#!/usr/bin/env python3
"""Run the boltons paired-MAE mechanism experiment one paid cell at a time."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    AgentRecord,
    BenchmarkSelectionRecord,
    CheckRecord,
    EvaluationCellSet,
    MetricRecord,
    ResultCellRef,
    ResultMatrix,
    RollingOriginRecord,
    RuntimeConfig,
    SelectorRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    WorkspaceConfig,
    canonical_digest,
    canonical_json,
    load_jsonl_records,
    record_with_digest,
    task_check_ref_key,
    validate_evaluation_cell_set,
    write_jsonl_records,
)
from barcarolle.result_store import (  # noqa: E402
    ResultCacheConfig,
    ResultJoinConfig,
    ResultQuery,
    ResultStore,
    ScoringConfig,
    build_result_record,
    build_result_matrix,
    compute_result_cache_identity,
    find_missing_results,
    load_results,
    resolve_result_cells,
    store_result,
)
from barcarolle.selection import (  # noqa: E402
    FeatureConfig,
    LeakagePolicy,
    MetricConfig,
    RollingOriginPolicy,
    SelectionBudget,
    SelectionConfig,
    build_feature_snapshot,
    build_rolling_origin,
    build_selector_input,
    evaluate_selection,
    fit_rule_mixture_from_metrics,
    select_with_selector,
)
from barcarolle.task_pool import TimeRange  # noqa: E402
from barcarolle.workspace import (  # noqa: E402
    WorkspaceArtifactConfig,
    bind_agent_harness,
    bind_check_material,
    bind_repository_source,
    run_agent_on_task_with_artifacts,
)
from examples.boltons_regression import run as fixture  # noqa: E402


HERE = Path(__file__).resolve().parent
HARNESS = (HERE.parent / "harnesses/codex-cli/run-agent.zsh").resolve()
DEFAULT_OUTPUT_DIR = Path(
    "outputs/user-journeys/2026-07-15-openai-paired-rolling-origin"
)
MODEL = "gpt-5.4-mini"
REASONING_EFFORTS = ("low", "high")
ORIGIN_ONE = "2026-07-01T00:00:00Z"
ORIGIN_TWO = "2026-07-05T00:00:00Z"
HISTORY_START = "2026-06-01T00:00:00Z"
HISTORY_END = "2026-07-07T00:00:00Z"
PRICING_VERSION = "openai-standard-api-gpt-5.4-mini-2026-07-15"
OFFICIAL_PRICING_SOURCE = "https://developers.openai.com/api/docs/models/gpt-5.4-mini"
OFFICIAL_RATES = {
    "uncached_input_tokens": 0.75 / 1_000_000,
    "cached_input_tokens": 0.075 / 1_000_000,
    "output_tokens": 4.50 / 1_000_000,
}
SCORING_CONFIG = ScoringConfig(PRICING_VERSION, OFFICIAL_RATES)
CACHE_CONFIG = ResultCacheConfig(require_valid_result=False)
JOIN_CONFIG = ResultJoinConfig(
    join_policy_digest="paired-exact-result-v1",
    denominator_policy_digest="all-required-agent-task-check-cells-v1",
)
FEATURE_CONFIG = FeatureConfig(
    feature_config_digest="boltons-metadata-only-v1",
    leakage_policy_digest="task-metadata-only-v1",
    feature_names=("task_count", "task_cluster"),
    allowed_leakage_classes=("task_metadata",),
)
BUDGET = SelectionBudget("two-task-checks-per-origin-v1", 2)
POLICY = RollingOriginPolicy(
    policy_digest="boltons-sequential-rolling-origin-v1",
    as_of_cutoff_rule="origin_time",
    cluster_constraints_digest="all-boltons-clusters-v1",
    eligibility_mode="strict_history",
    holdout_overlap_policy="disjoint",
    future_holdout_known=True,
)


@dataclass(frozen=True)
class ExperimentContext:
    output_dir: Path
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


def prepare(target_repo: Path, output_dir: Path) -> Mapping[str, object]:
    output_dir = output_dir.resolve()
    ledger_path = output_dir / "resource-ledger.json"
    if ledger_path.exists():
        ledger = _load_ledger(ledger_path)
        if ledger["calls"]:
            raise RuntimeError("prepare refuses to replace a started paid experiment")
    results_path = output_dir / "records/results.jsonl"
    if results_path.exists():
        results = load_results(ResultStore(results_path), ResultQuery())
        paid = tuple(
            result
            for result in results
            if result.agent_id != "scripted-known-good-boltons"
        )
        if paid:
            raise RuntimeError(
                "prepare refuses to replace existing paid Agent Results"
            )
    records_dir = output_dir / "records"
    if records_dir.exists():
        for path in records_dir.glob("paired-*.jsonl"):
            path.unlink()
    for path in (
        output_dir / "paired-metrics.json",
        output_dir / "paired-summary.json",
    ):
        path.unlink(missing_ok=True)
    summary = fixture.run(target_repo, output_dir)
    return {
        "stage": "prepared",
        "paid_call_count": 0,
        "task_count": summary["task_count"],
        "task_pool_id": summary["task_pool_id"],
        "next": "--canary or --next-cell",
    }


def freeze_origin_one(context: ExperimentContext) -> Mapping[str, object]:
    selectors_path = context.records_dir / "paired-baseline-selectors.jsonl"
    origin_path = context.records_dir / "paired-origin-one.jsonl"
    selections_path = context.records_dir / "paired-origin-one-selections.jsonl"
    origin_two_path = context.records_dir / "paired-origin-two.jsonl"
    selections_two_path = (
        context.records_dir / "paired-origin-two-baseline-selections.jsonl"
    )
    paths = (
        selectors_path,
        origin_path,
        selections_path,
        origin_two_path,
        selections_two_path,
    )
    if any(path.exists() for path in paths):
        if not all(path.exists() for path in paths):
            if _paid_result_count(context):
                raise RuntimeError("baseline selection freeze records are partial")
            for path in paths:
                path.unlink(missing_ok=True)
            return freeze_origin_one(context)
        selectors, origin, selections = _load_origin_one(context)
        origin_two, selections_two = _load_origin_two_baselines(context)
    else:
        selectors = _baseline_selectors(context.task_pool, context.tasks)
        origin = _build_origin(
            context, ORIGIN_ONE, TimeRange(ORIGIN_ONE, ORIGIN_TWO)
        )
        selections = _freeze_selections(context, origin, selectors)
        origin_two = _build_origin(
            context, ORIGIN_TWO, TimeRange(ORIGIN_TWO, HISTORY_END)
        )
        selections_two = _freeze_selections(context, origin_two, selectors)
        write_jsonl_records(selectors_path, selectors)
        write_jsonl_records(origin_path, (origin,))
        write_jsonl_records(selections_path, selections)
        write_jsonl_records(origin_two_path, (origin_two,))
        write_jsonl_records(selections_two_path, selections_two)
    required = _required_refs(context, origin, selections)
    return {
        "stage": "baseline_selections_frozen",
        "origin_id": origin.origin_id,
        "origin_two_id": origin_two.origin_id,
        "selector_ids": tuple(selector.selector_id for selector in selectors),
        "selection_ids": tuple(selection.selection_id for selection in selections),
        "origin_two_baseline_selection_ids": tuple(
            selection.selection_id for selection in selections_two
        ),
        "required_task_check_count": len(required),
        "paid_call_count": _paid_result_count(context),
        "next": "--canary or --next-cell",
    }


def run_next_cell(
    context: ExperimentContext, *, canary: bool
) -> Mapping[str, object]:
    _reconcile_ledger(context)
    freeze_origin_one(context)
    _, origin_one, origin_one_selections = _load_origin_one(context)
    if _origin_two_is_frozen(context):
        _, origin_two, origin_two_selections = _load_origin_two(context)
        refs = _required_refs(context, origin_two, origin_two_selections)
        stage = "origin_two"
    else:
        refs = _required_refs(context, origin_one, origin_one_selections)
        stage = "origin_one"
    missing = tuple(
        find_missing_results(
            refs,
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
        next_stage = "--evaluate" if stage == "origin_two" else "--fit-mixture"
        return {
            "stage": f"{stage}_cells_complete",
            "paid_call_count": _paid_result_count(context),
            "next": next_stage,
        }
    if canary and _paid_result_count(context):
        raise RuntimeError("the canary stage already has a paid Agent Result")
    cell = missing[0]
    result = _execute_cell(context, cell, require_scoreable=canary)
    return {
        "stage": f"{stage}_cell_recorded",
        "agent_id": result.agent_id,
        "model": result.cache_identity.model_snapshot_id,
        "task_id": result.task_id,
        "check_id": result.check_id,
        "terminal_status": result.terminal_status,
        "scoreable_state": result.scoreable_state,
        "outcome": result.outcome,
        "usage": _priced_usage(result.usage),
        "estimated_cost_usd": result.cost["total_cost"],
        "paid_call_count": _paid_result_count(context),
        "next": "--next-cell",
    }


def fit_mixture(context: ExperimentContext) -> Mapping[str, object]:
    _reconcile_ledger(context)
    selectors, origin_one, selections = _load_origin_one(context)
    refs = _required_refs(context, origin_one, selections)
    _require_no_missing(context, refs, "origin one")
    cell_sets, matrices, metrics = _load_or_score_origin(
        context, "origin-one", origin_one, selections
    )
    mae_metrics = tuple(
        metric
        for metric in metrics
        if metric.metric_name == "future_pass_rate_mae"
    )
    future_matrices = tuple(
        matrix for matrix in matrices if matrix.matrix_role == "future_holdout"
    )
    mixture_path = context.records_dir / "paired-mixture-selector.jsonl"
    if mixture_path.exists():
        (mixture,) = load_jsonl_records(mixture_path, SelectorRecord)
    else:
        mixture = fit_rule_mixture_from_metrics(
            selectors, selections, mae_metrics, future_matrices
        )
        write_jsonl_records(mixture_path, (mixture,))

    origin_two, baseline_selections_two = _load_origin_two_baselines(context)
    selections_two_path = context.records_dir / "paired-origin-two-selections.jsonl"
    if selections_two_path.exists():
        _, persisted_origin, selections_two = _load_origin_two(context)
        if persisted_origin != origin_two:
            raise RuntimeError("persisted origin-two records disagree")
    else:
        (mixture_selection,) = _freeze_selections(context, origin_two, (mixture,))
        selections_two = (*baseline_selections_two, mixture_selection)
        write_jsonl_records(selections_two_path, selections_two)

    return {
        "stage": "origin_two_frozen",
        "trained_on_origin_id": origin_one.origin_id,
        "mixture_selector_id": mixture.selector_id,
        "expert_weights": mixture.parameters["expert_weights"],
        "origin_two_id": origin_two.origin_id,
        "origin_two_selection_ids": tuple(
            selection.selection_id for selection in selections_two
        ),
        "origin_one_cell_set_digests": tuple(
            cell_set.cell_set_digest for cell_set in cell_sets
        ),
        "paid_call_count": _paid_result_count(context),
        "next": "--next-cell",
    }


def evaluate(context: ExperimentContext) -> Mapping[str, object]:
    _reconcile_ledger(context)
    selectors, origin_one, selections_one = _load_origin_one(context)
    mixture, origin_two, selections_two = _load_origin_two(context)
    refs = _required_refs(context, origin_two, selections_two)
    _require_no_missing(context, refs, "origin two")
    _, matrices_one, metrics_one = _load_or_score_origin(
        context, "origin-one", origin_one, selections_one
    )
    _, matrices_two, metrics_two = _load_or_score_origin(
        context, "origin-two", origin_two, selections_two
    )
    all_selectors = (*selectors, mixture)
    selector_family = {
        selector.selector_id: selector.selector_family for selector in all_selectors
    }
    selection_family = {
        selection.selection_id: selector_family[selection.selector_id]
        for selection in (*selections_one, *selections_two)
    }
    rows = tuple(
        {
            "origin_id": metric.origin_id,
            "selector_family": selection_family[metric.selection_id],
            "metric_name": metric.metric_name,
            "metric_value": metric.metric_value,
            "completeness_state": metric.completeness_state,
            "metric_digest": metric.metric_digest,
        }
        for metric in (*metrics_one, *metrics_two)
    )
    metrics_payload = {
        "schema_version": 1,
        "objective": "paired future pass-rate MAE",
        "origins": (
            {"origin_id": origin_one.origin_id, "origin_time": ORIGIN_ONE},
            {"origin_id": origin_two.origin_id, "origin_time": ORIGIN_TWO},
        ),
        "rows": rows,
        "rule_mixture": {
            "trained_only_on_origin_id": origin_one.origin_id,
            "evaluated_on_origin_id": origin_two.origin_id,
            "expert_weights": mixture.parameters["expert_weights"],
        },
    }
    _write_json(context.output_dir / "paired-metrics.json", metrics_payload)
    results = _paid_results(context)
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
        raise RuntimeError("paid Result Store contains duplicate execution identities")
    total_cost = sum(float(result.cost["total_cost"]) for result in results)
    summary = {
        "schema_version": 1,
        "stage": "complete",
        "task_pool_id": context.task_pool.task_pool_id,
        "agents": tuple(
            {
                "agent_id": agent.agent_id,
                "model": agent.model_snapshot_id,
                "reasoning_effort": _agent_effort(agent),
            }
            for agent in context.agents
        ),
        "paid_agent_result_count": len(results),
        "estimated_cost_usd": total_cost,
        "pricing_version": PRICING_VERSION,
        "pricing_source": OFFICIAL_PRICING_SOURCE,
        "origin_one_future_matrix_digests": tuple(
            matrix.matrix_digest
            for matrix in matrices_one
            if matrix.matrix_role == "future_holdout"
        ),
        "origin_two_future_matrix_digests": tuple(
            matrix.matrix_digest
            for matrix in matrices_two
            if matrix.matrix_role == "future_holdout"
        ),
        "predictive_validity_claim": {
            "supported": False,
            "reason": (
                "This five-task hand-authored fixture tests the rolling-origin, "
                "paired-MAE, and rule-mixture mechanism; it is not a representative "
                "sample of future repository work."
            ),
        },
        "metrics_path": str(context.output_dir / "paired-metrics.json"),
    }
    _write_json(context.output_dir / "paired-summary.json", summary)
    return summary


def build_context(
    target_repo: Path, output_dir: Path, ledger_path: Path | None = None
) -> ExperimentContext:
    output_dir = output_dir.resolve()
    records_dir = output_dir / "records"
    task_pool_path = records_dir / "task_pool.jsonl"
    if not task_pool_path.exists():
        raise RuntimeError("run --prepare-only before the paired experiment")
    (task_pool,) = load_jsonl_records(task_pool_path, TaskPoolRecord)
    tasks = tuple(load_jsonl_records(records_dir / "tasks.jsonl", TaskRecord))
    checks_tuple = tuple(
        load_jsonl_records(records_dir / "checks.jsonl", CheckRecord)
    )
    if canonical_digest(tasks) != task_pool.task_records_digest:
        raise RuntimeError("Task records do not match the prepared Task Pool")
    if canonical_digest(checks_tuple) != task_pool.check_records_digest:
        raise RuntimeError("Check records do not match the prepared Task Pool")

    workspace_config = _workspace_config()
    runtime_config = RuntimeConfig(
        runtime_config_id="boltons-codex-mini-paired-900s",
        budget_digest="codex-mini-paired-900s-default-network-retries-v1",
        retry_policy_digest="codex-default-network-retries-no-cell-retry",
        stochastic_settings_digest="reasoning-effort-bound-in-agent-identity",
        timeout_seconds=900,
        hardware_profile_digest=None,
    )
    agents, commands = _agents(
        output_dir,
        cli_version=_codex_cli_version(),
        endpoint_digest=_authorized_endpoint_digest(),
    )
    context = ExperimentContext(
        output_dir=output_dir,
        records_dir=records_dir,
        ledger_path=(ledger_path or output_dir / "resource-ledger.json").resolve(),
        task_pool=task_pool,
        tasks=tasks,
        checks={check.check_id: check for check in checks_tuple},
        agents=agents,
        commands=commands,
        workspace_config=workspace_config,
        runtime_config=runtime_config,
        result_store=ResultStore(records_dir / "results.jsonl"),
    )
    _bind_context(context, target_repo.resolve())
    return context


def _workspace_config() -> WorkspaceConfig:
    return WorkspaceConfig(
        workspace_config_id="boltons-pinned-current-schema",
        repository_checkout_config_digest=canonical_digest(
            {"repository": "boltons", "base_commit": fixture.PINNED_COMMIT}
        ),
        submodule_state_digest="submodules-none",
        base_image_digest=canonical_digest({"python": sys.version.split()[0]}),
        dependency_lock_digest=canonical_digest(
            {"pytest": "barcarolle-dev-lock"}
        ),
    )


def _agents(
    output_dir: Path,
    *,
    cli_version: str,
    endpoint_digest: str,
) -> tuple[tuple[AgentRecord, ...], Mapping[str, tuple[str, ...]]]:
    harness_text = HARNESS.read_text(encoding="utf-8")
    if "BARCAROLLE_CODEX_REASONING_EFFORT" not in harness_text:
        raise RuntimeError("Codex harness does not bind reasoning effort")
    usage_helper = HARNESS.parent / "extract-usage.py"
    harness_content_digest = canonical_digest(
        {
            "run_agent_sha256": hashlib.sha256(HARNESS.read_bytes()).hexdigest(),
            "extract_usage_sha256": hashlib.sha256(
                usage_helper.read_bytes()
            ).hexdigest(),
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
        agent_id = f"codex-{MODEL}-reasoning-{effort}"
        prompt_digest = canonical_digest(
            {
                "prompt": "boltons-task-md-codex-v1",
                "task_file": ".barcarolle/TASK.md",
                "repository_instruction_state": "none-at-pinned-commit",
                "execpolicy_rules_ignored": True,
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
        agent = AgentRecord(
            agent_id=agent_id,
            agent_manifest_digest=canonical_digest(
                {
                    "agent": "codex-cli",
                    "model": MODEL,
                    "reasoning_effort": effort,
                    "codex_cli_version": cli_version,
                    "harness_digest": harness_digest,
                    "harness_content_digest": harness_content_digest,
                    "prompt_digest": prompt_digest,
                    "provider_digest": provider_digest,
                    "multi_agent_disabled": True,
                }
            ),
            model_snapshot_id=MODEL,
            harness_digest=harness_digest,
            repository_instruction_digest=canonical_digest(
                {
                    "state": "none-at-pinned-commit",
                    "base_commit": fixture.PINNED_COMMIT,
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
            network_policy_digest=provider_digest,
            adapter_digest="barcarolle-worktree-diff-v2-python-cache-excluded",
        )
        agents.append(agent)
        commands[agent_id] = command
    return tuple(agents), commands


def _bind_context(context: ExperimentContext, target_repo: Path) -> None:
    _require_no_repository_instructions(target_repo)
    bind_repository_source(context.workspace_config, target_repo)
    task_by_id = {task.task_id: task for task in context.tasks}
    for check in context.checks.values():
        task = task_by_id[check.task_id]
        bind_check_material(
            check,
            fixture.CHECK_COMMAND,
            fixture._hidden_check_dir(task.source_ref),
        )
    for agent in context.agents:
        bind_agent_harness(agent, context.commands[agent.agent_id])


def _require_no_repository_instructions(target_repo: Path) -> None:
    completed = subprocess.run(
        (
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            fixture.PINNED_COMMIT,
        ),
        cwd=target_repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("could not inspect pinned repository instructions")
    if any(Path(name).name == "AGENTS.md" for name in completed.stdout.splitlines()):
        raise RuntimeError(
            "pinned repository contains AGENTS.md but Agent identity says none"
        )


def _baseline_selectors(
    task_pool: TaskPoolRecord, tasks: Sequence[TaskRecord]
) -> tuple[SelectorRecord, ...]:
    group_by_ref_key = {
        task_check_ref_key(TaskCheckRef(task.task_id, check_id)): task.cluster_id
        for task in tasks
        for check_id in task.check_ids
    }
    return (
        _selector(task_pool, "coverage", {"group_by_ref_key": group_by_ref_key}),
        _selector(task_pool, "random", {"seed": 5}),
        _selector(task_pool, "recency", {}),
    )


def _selector(
    task_pool: TaskPoolRecord, family: str, parameters: Mapping[str, object]
) -> SelectorRecord:
    config_digest = canonical_digest(
        {"selector_family": family, "parameters": parameters}
    )
    return SelectorRecord(
        selector_id=f"selector_{canonical_digest((task_pool.task_pool_digest, family, config_digest))}",
        selector_family=family,
        selector_version="1",
        training_source_digests=(
            task_pool.task_pool_digest,
            FEATURE_CONFIG.feature_config_digest,
        ),
        allowed_feature_classes=FEATURE_CONFIG.allowed_leakage_classes,
        parameters=parameters,
        config_digest=config_digest,
        created_at="2026-07-15T00:00:00Z",
    )


def _build_origin(
    context: ExperimentContext, origin_time: str, future_window: TimeRange
) -> RollingOriginRecord:
    from datetime import datetime

    return build_rolling_origin(
        context.task_pool,
        context.tasks,
        context.checks,
        datetime.fromisoformat(origin_time.replace("Z", "+00:00")),
        future_window,
        POLICY,
    )


def _freeze_selections(
    context: ExperimentContext,
    origin: RollingOriginRecord,
    selectors: Sequence[SelectorRecord],
) -> tuple[BenchmarkSelectionRecord, ...]:
    snapshot = build_feature_snapshot(
        origin,
        context.task_pool,
        context.tasks,
        context.checks,
        (),
        FEATURE_CONFIG,
    )
    selector_input = build_selector_input(
        origin,
        context.task_pool,
        snapshot,
        (),
        context.agents,
        BUDGET,
        LeakagePolicy(
            FEATURE_CONFIG.leakage_policy_digest,
            FEATURE_CONFIG.allowed_leakage_classes,
            origin.as_of_cutoff,
        ),
    )
    return tuple(
        select_with_selector(
            selector_input,
            selector,
            SelectionConfig(
                selection_config_digest=f"boltons-{selector.selector_family}-v1",
                selector_id=selector.selector_id,
                feature_snapshot_id=snapshot.feature_snapshot_id,
                eligibility_mode="strict_history",
            ),
        )
        for selector in selectors
    )


def _required_refs(
    context: ExperimentContext,
    origin: RollingOriginRecord,
    selections: Sequence[BenchmarkSelectionRecord],
) -> tuple[TaskCheckRef, ...]:
    keys = {
        (ref.task_id, ref.check_id)
        for selection in selections
        for ref in selection.selected_task_check_refs
    }
    keys.update(
        (ref.task_id, ref.check_id)
        for ref in origin.future_holdout_task_check_refs
    )
    return tuple(
        TaskCheckRef(task.task_id, check_id)
        for task in context.tasks
        for check_id in task.check_ids
        if (task.task_id, check_id) in keys
    )


def _execute_cell(
    context: ExperimentContext,
    cell: ResultCellRef,
    *,
    require_scoreable: bool,
):
    task = next(task for task in context.tasks if task.task_id == cell.task_id)
    check = context.checks[cell.check_id]
    agent = next(agent for agent in context.agents if agent.agent_id == cell.agent_id)
    command = context.commands[agent.agent_id]
    _assert_command_identity(agent, command)
    _ensure_credentials_available()
    ledger = _reconcile_ledger(context)
    _ensure_ledger_allows_call(ledger, context, task, check, agent)
    call_id = _start_ledger_call(
        context.ledger_path, ledger, task, check, agent
    )
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
            WorkspaceArtifactConfig(
                output_root=context.output_dir / "raw/agent-runs",
                preserve_solver_workspace_summary="on_failure",
                preserve_verifier_workspace_summary="on_failure",
            ),
        )
        workspace_run = workspace_result.run
        if workspace_result.artifacts is not None:
            artifact_manifest_ref = workspace_result.artifacts.manifest_ref
        result = build_result_record(
            task, check, agent, workspace_run, identity, SCORING_CONFIG
        )
        result = store_result(result, context.result_store)
        _fsync_file(context.result_store.path)
        usage = _priced_usage(result.usage)
        if result.cost["total_cost"] is None:
            raise RuntimeError("measured usage could not be priced")
        if require_scoreable and result.scoreable_state != "scoreable":
            raise RuntimeError("canary Result is not scoreable")
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


def _assert_command_identity(
    agent: AgentRecord, command: Sequence[str]
) -> None:
    effort = _agent_effort(agent)
    required = {
        f"BARCAROLLE_CODEX_MODEL={agent.model_snapshot_id}",
        f"BARCAROLLE_CODEX_REASONING_EFFORT={effort}",
    }
    if not required.issubset(command):
        raise RuntimeError("Agent command does not match model/effort identity")


def _agent_effort(agent: AgentRecord) -> str:
    for effort in REASONING_EFFORTS:
        if agent.agent_id.endswith(f"-{effort}"):
            return effort
    raise RuntimeError(f"unknown reasoning effort in Agent identity {agent.agent_id}")


def _priced_usage(usage: Mapping[str, object]) -> Mapping[str, int]:
    priced: dict[str, int] = {}
    for key in OFFICIAL_RATES:
        value = usage.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise RuntimeError(f"measured {key} is required before continuing")
        priced[key] = value
    input_tokens = usage.get("input_tokens")
    if input_tokens is not None:
        if (
            isinstance(input_tokens, bool)
            or not isinstance(input_tokens, int)
            or input_tokens < 0
        ):
            raise RuntimeError("measured input_tokens must be a nonnegative integer")
        if input_tokens != (
            priced["uncached_input_tokens"] + priced["cached_input_tokens"]
        ):
            raise RuntimeError(
                "measured input_tokens must equal cached plus uncached input"
            )
    return priced


def _load_or_score_origin(
    context: ExperimentContext,
    label: str,
    origin: RollingOriginRecord,
    selections: Sequence[BenchmarkSelectionRecord],
) -> tuple[
    tuple[EvaluationCellSet, ...],
    tuple[ResultMatrix, ...],
    tuple[MetricRecord, ...],
]:
    cell_path = context.records_dir / f"paired-{label}-cell-sets.jsonl"
    matrix_path = context.records_dir / f"paired-{label}-matrices.jsonl"
    metric_path = context.records_dir / f"paired-{label}-metrics.jsonl"
    if cell_path.exists() or matrix_path.exists() or metric_path.exists():
        if not (cell_path.exists() and matrix_path.exists() and metric_path.exists()):
            for path in (cell_path, matrix_path, metric_path):
                path.unlink(missing_ok=True)
        else:
            return (
                tuple(load_jsonl_records(cell_path, EvaluationCellSet)),
                tuple(load_jsonl_records(matrix_path, ResultMatrix)),
                tuple(load_jsonl_records(metric_path, MetricRecord)),
            )
    cell_sets: list[EvaluationCellSet] = []
    matrices: list[ResultMatrix] = []
    metrics: list[MetricRecord] = []
    for selection in selections:
        refs = tuple(
            dict.fromkeys(
                (*selection.selected_task_check_refs, *origin.future_holdout_task_check_refs)
            )
        )
        _require_no_missing(context, refs, label)
        cell_set = _prepare_cells_without_execution(
            context, selection, origin, refs
        )
        selected, future, selection_metrics = _score_without_side_effects(
            context, selection, origin, cell_set
        )
        cell_sets.append(cell_set)
        matrices.extend((selected, future))
        metrics.extend(selection_metrics)
    write_jsonl_records(cell_path, cell_sets)
    write_jsonl_records(matrix_path, matrices)
    write_jsonl_records(metric_path, metrics)
    return tuple(cell_sets), tuple(matrices), tuple(metrics)


def _prepare_cells_without_execution(
    context: ExperimentContext,
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    refs: Sequence[TaskCheckRef],
) -> EvaluationCellSet:
    cells = tuple(
        resolve_result_cells(
            refs,
            context.tasks,
            context.checks,
            context.agents,
            context.workspace_config,
            context.runtime_config,
            context.result_store,
            CACHE_CONFIG,
            SCORING_CONFIG,
        )
    )
    if any(cell.cell_state != "result" for cell in cells):
        raise RuntimeError("analysis stage cannot execute missing Agent cells")
    cell_set = EvaluationCellSet(
        cell_set_id=f"cell_set_{canonical_digest((selection.selection_digest, origin.origin_id, JOIN_CONFIG.join_policy_digest, tuple((ref.task_id, ref.check_id) for ref in refs), tuple(agent.agent_id for agent in context.agents)))}",
        origin_id=origin.origin_id,
        selection_id=selection.selection_id,
        selected_task_check_refs=selection.selected_task_check_refs,
        future_task_check_refs=origin.future_holdout_task_check_refs,
        cells=cells,
        abstention_reason=None,
        cell_set_digest="",
    )
    cell_set = record_with_digest(cell_set)
    validation = validate_evaluation_cell_set(cell_set)
    if not validation.ok:
        raise RuntimeError(
            "resolved analysis cells are invalid: " + ", ".join(validation.errors)
        )
    return cell_set


def _score_without_side_effects(
    context: ExperimentContext,
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    cell_set: EvaluationCellSet,
) -> tuple[ResultMatrix, ResultMatrix, tuple[MetricRecord, ...]]:
    result_ids = tuple(
        cell.result_id for cell in cell_set.cells if cell.result_id is not None
    )
    results = tuple(
        load_results(
            context.result_store,
            ResultQuery(
                result_ids=result_ids,
                scoring_config_digests=(SCORING_CONFIG.scoring_config_digest,),
            ),
        )
    )
    selected = build_result_matrix(
        cell_set,
        selection.selected_task_check_refs,
        context.tasks,
        context.checks,
        context.agents,
        results,
        "selected",
        JOIN_CONFIG,
    )
    future = build_result_matrix(
        cell_set,
        origin.future_holdout_task_check_refs,
        context.tasks,
        context.checks,
        context.agents,
        results,
        "future_holdout",
        JOIN_CONFIG,
    )
    metrics = tuple(
        evaluate_selection(
            selection,
            origin,
            cell_set,
            selected,
            future,
            MetricConfig("paired-pass-rate-mae-v1", BUDGET.budget_digest),
        )
    )
    return selected, future, metrics


def _require_no_missing(
    context: ExperimentContext, refs: Sequence[TaskCheckRef], label: str
) -> None:
    missing = find_missing_results(
        refs,
        context.tasks,
        context.checks,
        context.agents,
        context.workspace_config,
        context.runtime_config,
        context.result_store,
        CACHE_CONFIG,
    )
    if missing:
        raise RuntimeError(
            f"{label} still has {len(missing)} missing Agent/Task/Check cells"
        )
    bound = load_results(
        context.result_store,
        ResultQuery(
            agent_ids=tuple(agent.agent_id for agent in context.agents),
            scoring_config_digests=(SCORING_CONFIG.scoring_config_digest,),
        ),
    )
    for result in bound:
        _priced_usage(result.usage)
        if result.cost.get("total_cost") is None:
            raise RuntimeError("a paid Result has unknown estimated cost")


def _load_origin_one(
    context: ExperimentContext,
) -> tuple[
    tuple[SelectorRecord, ...],
    RollingOriginRecord,
    tuple[BenchmarkSelectionRecord, ...],
]:
    selectors = tuple(
        load_jsonl_records(
            context.records_dir / "paired-baseline-selectors.jsonl",
            SelectorRecord,
        )
    )
    origins = load_jsonl_records(
        context.records_dir / "paired-origin-one.jsonl", RollingOriginRecord
    )
    selections = tuple(
        load_jsonl_records(
            context.records_dir / "paired-origin-one-selections.jsonl",
            BenchmarkSelectionRecord,
        )
    )
    if len(selectors) != 3 or len(origins) != 1 or len(selections) != 3:
        raise RuntimeError("origin-one freeze records are incomplete")
    return selectors, origins[0], selections


def _origin_two_is_frozen(context: ExperimentContext) -> bool:
    paths = (
        context.records_dir / "paired-mixture-selector.jsonl",
        context.records_dir / "paired-origin-two-selections.jsonl",
    )
    present = tuple(path.exists() for path in paths)
    if any(present) and not all(present):
        raise RuntimeError("origin-two freeze records are partial")
    return all(present)


def _load_origin_two(
    context: ExperimentContext,
) -> tuple[
    SelectorRecord,
    RollingOriginRecord,
    tuple[BenchmarkSelectionRecord, ...],
]:
    if not _origin_two_is_frozen(context):
        raise RuntimeError("run --fit-mixture before origin-two work")
    (mixture,) = load_jsonl_records(
        context.records_dir / "paired-mixture-selector.jsonl", SelectorRecord
    )
    (origin,) = load_jsonl_records(
        context.records_dir / "paired-origin-two.jsonl", RollingOriginRecord
    )
    selections = tuple(
        load_jsonl_records(
            context.records_dir / "paired-origin-two-selections.jsonl",
            BenchmarkSelectionRecord,
        )
    )
    if len(selections) != 4:
        raise RuntimeError("origin-two must freeze three baselines and one mixture")
    return mixture, origin, selections


def _load_origin_two_baselines(
    context: ExperimentContext,
) -> tuple[RollingOriginRecord, tuple[BenchmarkSelectionRecord, ...]]:
    (origin,) = load_jsonl_records(
        context.records_dir / "paired-origin-two.jsonl", RollingOriginRecord
    )
    selections = tuple(
        load_jsonl_records(
            context.records_dir / "paired-origin-two-baseline-selections.jsonl",
            BenchmarkSelectionRecord,
        )
    )
    if len(selections) != 3:
        raise RuntimeError("origin-two baseline selections are incomplete")
    return origin, selections


def _paid_results(context: ExperimentContext):
    return tuple(
        load_results(
            context.result_store,
            ResultQuery(
                agent_ids=tuple(agent.agent_id for agent in context.agents),
                scoring_config_digests=(SCORING_CONFIG.scoring_config_digest,),
            ),
        )
    )


def _paid_result_count(context: ExperimentContext) -> int:
    return len(_paid_results(context))


def _ensure_credentials_available() -> None:
    if os.environ.get("OPENAI_BASE_URL") and os.environ.get("OPENAI_API_KEY"):
        return
    completed = subprocess.run(
        (
            "zsh",
            "-lc",
            "source \"$HOME/.zshrc\"; [[ -n \"$OPENAI_BASE_URL\" && -n \"$OPENAI_API_KEY\" ]]",
        ),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "OPENAI_BASE_URL and OPENAI_API_KEY are required for paid cells"
        )


def _authorized_endpoint_digest() -> str:
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not base_url:
        completed = subprocess.run(
            (
                "zsh",
                "-lc",
                "source \"$HOME/.zshrc\"; printf %s \"$OPENAI_BASE_URL\"",
            ),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if completed.returncode == 0:
            base_url = completed.stdout
    if not base_url:
        raise RuntimeError("OPENAI_BASE_URL is required to bind Agent identity")
    return canonical_digest({"openai_base_url": base_url.rstrip("/")})


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


def _load_ledger(path: Path) -> dict[str, object]:
    if not path.exists():
        raise RuntimeError(f"resource ledger is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("calls"), list):
        raise RuntimeError("resource ledger must contain a calls list")
    events = _load_ledger_events(_ledger_events_path(path))
    if events:
        value = _rebuild_ledger_snapshot(path, value, events)
    elif value["calls"]:
        raise RuntimeError("resource ledger snapshot has calls without an event log")
    return value


def _reconcile_ledger(context: ExperimentContext) -> dict[str, object]:
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
        not isinstance(call, dict) or call.get("state") != "completed"
        for call in calls
    ):
        raise RuntimeError("resource ledger contains a stopped paid cell")
    _ensure_historical_calls_scoreable(calls)
    return ledger


def _exact_result_for_call(context: ExperimentContext, call: Mapping[str, object]):
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
        raise RuntimeError("resource ledger reservation does not match this experiment")
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
    context: ExperimentContext,
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
) -> None:
    calls = ledger["calls"]
    limits = ledger.get("limits")
    authorization = ledger.get("authorization")
    if not isinstance(calls, list) or not isinstance(limits, dict):
        raise RuntimeError("resource ledger limits are missing")
    if not isinstance(authorization, dict):
        raise RuntimeError("resource ledger authorization is missing")
    required_credentials = authorization.get("credential_variables")
    if required_credentials != ["OPENAI_API_KEY", "OPENAI_BASE_URL"]:
        raise RuntimeError("resource ledger does not authorize the required endpoint")
    pricing = ledger.get("pricing")
    models = pricing.get("models") if isinstance(pricing, dict) else None
    model_pricing = models.get(MODEL) if isinstance(models, dict) else None
    expected_rates = {
        "input_usd_per_token": OFFICIAL_RATES["uncached_input_tokens"],
        "cached_input_usd_per_token": OFFICIAL_RATES["cached_input_tokens"],
        "output_usd_per_token": OFFICIAL_RATES["output_tokens"],
    }
    if not isinstance(model_pricing, dict) or any(
        model_pricing.get(key) != rate for key, rate in expected_rates.items()
    ):
        raise RuntimeError("resource ledger pricing does not match official rates")
    if any(
        isinstance(call, dict) and call.get("state") != "completed"
        for call in calls
    ):
        raise RuntimeError("resource ledger contains a stopped paid cell")
    _ensure_historical_calls_scoreable(calls)
    maximum_calls = limits.get("maximum_paid_calls")
    if not isinstance(maximum_calls, int) or len(calls) >= maximum_calls:
        raise RuntimeError("resource ledger paid-call limit is reached")
    remaining = ledger.get("remaining_usd")
    if (
        isinstance(remaining, bool)
        or not isinstance(remaining, int | float)
        or remaining <= 0
    ):
        raise RuntimeError("resource ledger has no remaining USD budget")
    key = (agent.agent_id, task.task_id, check.check_id)
    for call in calls:
        if not isinstance(call, dict):
            raise RuntimeError("resource ledger call entries must be objects")
        if (
            call.get("agent_id"),
            call.get("task_id"),
            call.get("check_id"),
        ) == key:
            raise RuntimeError("resource ledger forbids retrying an attempted cell")
    if _paid_result_count(context) != len(calls):
        raise RuntimeError("paid Result count and resource ledger call count differ")


def _ensure_historical_calls_scoreable(calls: Sequence[object]) -> None:
    for call in calls:
        if not isinstance(call, dict):
            raise RuntimeError("resource ledger call entries must be objects")
        if (
            call.get("state") == "completed"
            and call.get("scoreable_state") != "scoreable"
        ):
            raise RuntimeError(
                "a historical paid cell is not scoreable; expansion is stopped"
            )


def _start_ledger_call(
    path: Path,
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
        "call_id": call_id,
        "state": "started",
        "agent_id": agent.agent_id,
        "model": agent.model_snapshot_id,
        "reasoning_effort": _agent_effort(agent),
        "task_id": task.task_id,
        "check_id": check.check_id,
        "source_ref": task.source_ref,
        "retry": False,
    }
    _append_ledger_event(_ledger_events_path(path), event)
    _rebuild_ledger_snapshot(
        path,
        ledger,
        _load_ledger_events(_ledger_events_path(path)),
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
    call = next(
        (
            item
            for item in calls
            if isinstance(item, dict) and item.get("call_id") == call_id
        ),
        None,
    )
    if call is None:
        raise RuntimeError(f"resource ledger is missing {call_id}")
    event: dict[str, object] = {
        "event_type": "completion",
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
    _append_ledger_event(_ledger_events_path(path), event)
    _rebuild_ledger_snapshot(
        path,
        ledger,
        _load_ledger_events(_ledger_events_path(path)),
    )


def _ledger_events_path(snapshot_path: Path) -> Path:
    return snapshot_path.with_name(f"{snapshot_path.stem}-events.jsonl")


def _load_ledger_events(path: Path) -> tuple[dict[str, object], ...]:
    if not path.exists():
        return ()
    events: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = json.loads(line)
        if not isinstance(value, dict):
            raise RuntimeError("resource ledger events must be JSON objects")
        events.append(value)
    return tuple(events)


def _append_ledger_event(path: Path, event: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(event))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    _fsync_directory(path.parent)


def _rebuild_ledger_snapshot(
    path: Path,
    ledger: Mapping[str, object],
    events: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    calls: list[dict[str, object]] = []
    by_id: dict[str, dict[str, object]] = {}
    completed: set[str] = set()
    for event in events:
        event_type = event.get("event_type")
        call_id = event.get("call_id")
        if not isinstance(call_id, str):
            raise RuntimeError("resource ledger event call_id is required")
        if event_type == "reservation":
            if call_id in by_id:
                raise RuntimeError("resource ledger has a duplicate reservation")
            call = {
                key: value for key, value in event.items() if key != "event_type"
            }
            calls.append(call)
            by_id[call_id] = call
        elif event_type == "completion":
            call = by_id.get(call_id)
            if call is None or call_id in completed:
                raise RuntimeError("resource ledger completion has no reservation")
            call.update(
                {
                    key: value
                    for key, value in event.items()
                    if key not in {"event_type", "call_id"}
                }
            )
            completed.add(call_id)
        else:
            raise RuntimeError("resource ledger event_type is invalid")
    snapshot = dict(ledger)
    snapshot["calls"] = calls
    known_costs: list[float] = []
    for call in calls:
        estimated_cost = call.get("estimated_cost_usd")
        if isinstance(estimated_cost, int | float) and not isinstance(
            estimated_cost, bool
        ):
            known_costs.append(float(estimated_cost))
    authorization = snapshot.get("authorization")
    if not isinstance(authorization, dict):
        raise RuntimeError("resource ledger authorization is missing")
    budget = authorization.get("budget_usd")
    if isinstance(budget, bool) or not isinstance(budget, int | float):
        raise RuntimeError("resource ledger budget_usd must be numeric")
    snapshot["spent_usd"] = sum(known_costs)
    snapshot["remaining_usd"] = float(budget) - sum(known_costs)
    snapshot["updated_at"] = "2026-07-15"
    _write_json(path, snapshot)
    return snapshot


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(canonical_json(value))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    _fsync_directory(path.parent)


def _fsync_directory(path: Path) -> None:
    directory = os.open(path, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Stage the boltons paired-MAE mechanism experiment; paid modes run "
            "at most one Agent/Task/Check cell per invocation."
        )
    )
    parser.add_argument("--target-repo", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--ledger", type=Path)
    stage = parser.add_mutually_exclusive_group(required=True)
    stage.add_argument("--prepare-only", action="store_true")
    stage.add_argument("--freeze-origin-one", action="store_true")
    stage.add_argument("--canary", action="store_true")
    stage.add_argument("--next-cell", action="store_true")
    stage.add_argument("--fit-mixture", action="store_true")
    stage.add_argument("--evaluate", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.prepare_only:
        summary = prepare(args.target_repo, args.output_dir)
    else:
        context = build_context(args.target_repo, args.output_dir, args.ledger)
        if args.freeze_origin_one:
            summary = freeze_origin_one(context)
        elif args.canary:
            summary = run_next_cell(context, canary=True)
        elif args.next_cell:
            summary = run_next_cell(context, canary=False)
        elif args.fit_mixture:
            summary = fit_mixture(context)
        else:
            summary = evaluate(context)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
