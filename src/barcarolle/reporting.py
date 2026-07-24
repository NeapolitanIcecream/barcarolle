"""Claim-safe reporting from existing Barcarolle records."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence, cast

from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    CheckRecord,
    EvaluationCellSet,
    FeatureSnapshotRecord,
    MetricRecord,
    ResultCellRef,
    ResultMatrix,
    ResultRecord,
    RollingOriginRecord,
    SelectorInput,
    SelectorRecord,
    SourceEventRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    agent_record_from_cache_identity,
    cache_identity_task_check_mismatches,
    canonical_digest,
    canonical_json,
    matrix_denominator_error,
    parse_utc_timestamp,
    result_cell_record_mismatches,
    task_check_ref_key,
    validate_benchmark_selection,
    validate_evaluation_cell_set,
    validate_feature_snapshot,
    validate_metric,
    validate_result,
    validate_result_matrix,
    validate_rolling_origin,
    validate_selector,
    validate_selector_input,
)
from barcarolle.result_store import (
    ambiguous_result_execution_keys,
    result_execution_digest,
    result_matrix_evidence_errors,
)
from barcarolle.selection.algorithms import (
    ensure_selection_replay,
    summarize_stratified_forecast,
)
from barcarolle.selection.evaluation import (
    METRIC_CONFIG_DIGEST,
    compute_selection_metric_values,
    summarize_selector_mae,
)
from barcarolle.selection.features import (
    _result_view_digest,
    ensure_feature_snapshot_task_metadata_provenance,
)
from barcarolle.selection.origin import (
    compare_arrival_and_label_time_cohorts,
    materialize_prospective_future_cohort,
    validate_rolling_origin_against_records,
)
from barcarolle.task_pool import (
    TaskPoolBundle,
    load_validated_task_pool_bundle,
)


_CLAIM_NAMES = (
    "task_pool_bundle_internal_consistency",
    "benchmark_selection_frozen",
    "cache_completeness",
    "selector_metrics",
    "agent_result_identity",
)


@dataclass(frozen=True)
class ReportSection:
    section_id: str
    heading: str
    summary: Mapping[str, Any]
    source_digests: Mapping[str, Any]
    artifact_paths: tuple[str, ...] = ()
    supported_claims: tuple[str, ...] = ()
    unsupported_claims: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ClaimConfig:
    requested_claims: tuple[str, ...] = _CLAIM_NAMES

    def __post_init__(self) -> None:
        claims = self.requested_claims
        if not isinstance(claims, tuple):
            raise ValueError("requested_claims must be a tuple")
        if any(type(claim) is not str or not claim.strip() for claim in claims):
            raise ValueError("requested_claims must contain non-empty strings")
        if len(claims) != len(set(claims)):
            raise ValueError("requested_claims must be unique")
        unsupported = tuple(claim for claim in claims if claim not in _CLAIM_NAMES)
        if unsupported:
            raise ValueError("unsupported requested claims: " + ", ".join(unsupported))
        requested = set(claims)
        object.__setattr__(
            self,
            "requested_claims",
            tuple(claim for claim in _CLAIM_NAMES if claim in requested),
        )

    @property
    def claim_config_digest(self) -> str:
        return canonical_digest({"requested_claims": self.requested_claims})


@dataclass(frozen=True)
class _SelectorProvenanceIndexes:
    origins: Mapping[str, RollingOriginRecord]
    snapshots: Mapping[str, FeatureSnapshotRecord]
    inputs: Mapping[str, SelectorInput]
    selectors: Mapping[str, SelectorRecord]
    results: Mapping[str, ResultRecord]
    agents: Mapping[str, AgentRecord]


@dataclass(frozen=True)
class _ResolvedSelectionProvenance:
    origin: RollingOriginRecord | None
    snapshot: FeatureSnapshotRecord | None
    selector_input: SelectorInput | None
    selector: SelectorRecord | None


def build_task_pool_report(
    task_pool: TaskPoolRecord,
    artifact_root: Path | None = None,
) -> ReportSection:
    validation_errors = _task_pool_validation_errors(task_pool, artifact_root)
    supported_claims = () if validation_errors else ("task_pool_counts",)
    limitations = tuple(validation_errors)
    source_event_summary = _task_pool_source_event_summary(task_pool, artifact_root)
    summary = {
        "task_pool_id": task_pool.task_pool_id,
        "repository_id": task_pool.repository_id,
        "task_count": len(task_pool.task_ids),
        "check_count": len(task_pool.check_ids),
        "rejected_candidate_count": len(task_pool.rejected_candidate_ids),
        "task_records_ref": task_pool.task_records_ref,
        "check_records_ref": task_pool.check_records_ref,
        "certification_evidence_ref": task_pool.certification_evidence_ref,
        "source_event_records_ref": task_pool.source_event_records_ref,
        "source_event_records_digest": task_pool.source_event_records_digest,
        "certification_evidence_digest": task_pool.certification_evidence_digest,
        "rejection_summary_digest": task_pool.rejection_summary_digest,
        "generation_provenance_ref": task_pool.generation_provenance_ref,
        "generation_provenance_digest": task_pool.generation_provenance_digest,
        "generator_config_digest": task_pool.generator_config_digest,
        "source_protocol_digest": task_pool.source_protocol_digest,
        "certification_config_digest": task_pool.certification_config_digest,
        "source_window_start": task_pool.source_window_start,
        "source_window_end": task_pool.source_window_end,
        **source_event_summary,
    }
    return ReportSection(
        section_id="task_pool",
        heading="Task Pool",
        summary=summary,
        source_digests={
            "task_pool_digest": task_pool.task_pool_digest,
            "task_records_digest": task_pool.task_records_digest,
            "check_records_digest": task_pool.check_records_digest,
            "source_event_records_digest": task_pool.source_event_records_digest,
            "generation_provenance_digest": (task_pool.generation_provenance_digest),
        },
        artifact_paths=_task_pool_artifact_paths((task_pool,), artifact_root),
        supported_claims=supported_claims,
        unsupported_claims=tuple(
            f"task_pool_counts: {error}" for error in validation_errors
        ),
        limitations=limitations,
    )


def build_result_report(
    results: Sequence[ResultRecord], agents: Sequence[AgentRecord]
) -> ReportSection:
    execution_results = _results_by_execution(results)
    limitations = _result_report_limitations(results, agents)
    pricing_view_count = _pricing_view_count(results)
    cache_identity_digests = tuple(
        sorted(result.cache_identity.identity_digest for result in results)
    )
    summary = {
        "result_count": len(execution_results),
        "execution_count": len(execution_results),
        "pricing_view_count": pricing_view_count,
        "result_record_count": len(results),
        "agent_count": len(agents),
        **_result_execution_summary(execution_results),
        **_result_cost_summary(results, execution_results),
        "latency": _result_latency_summary(execution_results),
        "pricing_versions": tuple(
            sorted({result.pricing_version for result in results})
        ),
        "result_evidence": _result_evidence_summary(results),
        "cache_coverage": {
            "result_count": len(execution_results),
            "pricing_view_count": pricing_view_count,
            "result_record_count": len(results),
            "unique_cache_identity_count": len(set(cache_identity_digests)),
        },
    }
    supported_claims = (
        ("agent_results_summary", "result_evidence_provenance_summary")
        if results and not limitations
        else ()
    )
    return ReportSection(
        section_id="agent_results",
        heading="Agent Results",
        summary=summary,
        source_digests={
            "result_digests": tuple(sorted(result.result_digest for result in results)),
            "cache_identity_digests": cache_identity_digests,
            "external_source_manifest_digests": tuple(
                sorted(
                    {
                        result.evidence_source_manifest_digest
                        for result in results
                        if result.evidence_source_manifest_digest is not None
                    }
                )
            ),
            "agent_manifest_digests": tuple(
                sorted(agent.agent_manifest_digest for agent in agents)
            ),
        },
        supported_claims=supported_claims,
        unsupported_claims=limitations,
        limitations=limitations,
    )


def _result_evidence_summary(
    results: Sequence[ResultRecord],
) -> Mapping[str, Any]:
    execution_digests_by_source: dict[str, set[str]] = {}
    execution_digests_by_policy: dict[str, set[str]] = {}
    for result in results:
        execution_digest = result_execution_digest(result)
        execution_digests_by_source.setdefault(
            result.evidence_source_kind,
            set(),
        ).add(execution_digest)
        execution_digests_by_policy.setdefault(
            result.availability_policy,
            set(),
        ).add(execution_digest)
    historical_count = len(
        execution_digests_by_policy.get(
            "producer_attested_historical_v1",
            set(),
        )
    )
    notes = []
    if historical_count:
        notes.append(
            "producer_attested_historical_v1 preserves producer-declared "
            "availability and is not a Barcarolle observation-time claim"
        )
    if execution_digests_by_policy.get("import_time_floor_v1"):
        notes.append(
            "import_time_floor_v1 makes external evidence available no earlier "
            "than its recorded import time"
        )
    return {
        "source_kind_record_counts": dict(
            sorted(Counter(result.evidence_source_kind for result in results).items())
        ),
        "source_kind_execution_counts": {
            source: len(digests)
            for source, digests in sorted(execution_digests_by_source.items())
        },
        "availability_policy_record_counts": dict(
            sorted(Counter(result.availability_policy for result in results).items())
        ),
        "availability_policy_execution_counts": {
            policy: len(digests)
            for policy, digests in sorted(execution_digests_by_policy.items())
        },
        "external_source_manifest_digests": tuple(
            sorted(
                {
                    result.evidence_source_manifest_digest
                    for result in results
                    if result.evidence_source_manifest_digest is not None
                }
            )
        ),
        "historical_attestation_execution_count": historical_count,
        "notes": tuple(notes),
    }


def _result_report_limitations(
    results: Sequence[ResultRecord],
    agents: Sequence[AgentRecord],
) -> tuple[str, ...]:
    limitations = (
        *_record_identity_errors(results, "result_id", "result"),
        *_record_identity_errors(agents, "agent_id", "Agent"),
        *_validation_errors("result", results, validate_result),
        *_result_agent_identity_errors(results, agents),
        *_result_measurement_errors(results),
        *_result_execution_conflict_errors(results),
        *_pricing_view_errors(results),
    )
    if not results:
        limitations = (*limitations, "result evidence is absent")
    return limitations


def _result_execution_conflict_errors(
    results: Sequence[ResultRecord],
) -> tuple[str, ...]:
    return tuple(
        "conflicting Result executions share cache identity "
        f"{cache_identity.identity_digest}"
        for _, _, _, cache_identity in sorted(
            ambiguous_result_execution_keys(results),
            key=lambda key: (
                key[0],
                key[1],
                key[2],
                key[3].identity_digest,
            ),
        )
    )


def _result_execution_summary(
    execution_results: Sequence[ResultRecord],
) -> Mapping[str, Any]:
    outcome_counts = Counter(result.outcome for result in execution_results)
    terminal_counts = Counter(result.terminal_status for result in execution_results)
    failure_label_counts = Counter(
        result.failure_label or "none" for result in execution_results
    )
    invalid_owner_counts = Counter(
        result.invalid_owner or "none" for result in execution_results
    )
    scoreable_state_counts = Counter(
        result.scoreable_state for result in execution_results
    )
    scoreable_count = sum(
        1 for result in execution_results if result.scoreable_state == "scoreable"
    )
    benchmark_invalid_results = tuple(
        result
        for result in execution_results
        if result.scoreable_state == "benchmark_invalid"
    )
    observed_task_checks = {
        (result.task_id, result.check_id) for result in execution_results
    }
    benchmark_invalid_task_checks = {
        (result.task_id, result.check_id) for result in benchmark_invalid_results
    }
    return {
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "terminal_status_counts": dict(sorted(terminal_counts.items())),
        "failure_label_counts": dict(sorted(failure_label_counts.items())),
        "invalid_owner_counts": dict(sorted(invalid_owner_counts.items())),
        "scoreable_state_counts": dict(sorted(scoreable_state_counts.items())),
        "scoreable_rate": scoreable_count / len(execution_results)
        if execution_results
        else 0.0,
        "benchmark_invalid": {
            "execution_count": len(benchmark_invalid_results),
            "execution_rate": (
                len(benchmark_invalid_results) / len(execution_results)
                if execution_results
                else None
            ),
            "affected_task_check_count": len(benchmark_invalid_task_checks),
            "observed_task_check_count": len(observed_task_checks),
            "affected_task_check_rate": (
                len(benchmark_invalid_task_checks) / len(observed_task_checks)
                if observed_task_checks
                else None
            ),
        },
    }


def _result_cost_summary(
    results: Sequence[ResultRecord],
    execution_results: Sequence[ResultRecord],
) -> Mapping[str, Any]:
    cost_by_scoring_config = _cost_by_scoring_config(results)
    single_cost_summary = (
        next(iter(cost_by_scoring_config.values()))
        if len(cost_by_scoring_config) == 1
        else None
    )
    total_cost = (
        single_cost_summary["total_cost"]
        if single_cost_summary is not None
        else (0.0 if not results else None)
    )
    cost_coverage = (
        _result_cost_coverage(execution_results)
        if single_cost_summary is not None or not results
        else {
            "measured_result_count": 0,
            "measured_zero_cost_count": 0,
            "unknown_result_count": len(execution_results),
            "reason": "multiple_scoring_configs",
        }
    )
    return {
        "total_cost": total_cost,
        "cost_coverage": cost_coverage,
        "cost_by_scoring_config": cost_by_scoring_config,
    }


def _pricing_view_count(results: Sequence[ResultRecord]) -> int:
    return len(
        {
            (result_execution_digest(result), result.scoring_config_digest)
            for result in results
        }
    )


def _results_by_execution(results: Sequence[ResultRecord]) -> tuple[ResultRecord, ...]:
    by_execution: dict[str, ResultRecord] = {}
    for result in results:
        by_execution.setdefault(result_execution_digest(result), result)
    return tuple(by_execution[digest] for digest in sorted(by_execution))


def _result_latency_summary(results: Sequence[ResultRecord]) -> Mapping[str, Any]:
    workspace_seconds = _latency_values(results, "workspace_seconds")
    agent_seconds = _latency_values(results, "agent_seconds")
    verification_seconds = _latency_values(results, "verification_seconds")
    phase_keys = (
        "solver_checkout_seconds",
        "verifier_checkout_seconds",
        "diff_replay_seconds",
        "cleanup_seconds",
    )
    phase_seconds = {key: _latency_values(results, key) for key in phase_keys}
    summary: dict[str, Any] = {
        "count": len(workspace_seconds),
        "total_workspace_seconds": sum(workspace_seconds),
        "mean_workspace_seconds": (
            sum(workspace_seconds) / len(workspace_seconds)
            if workspace_seconds
            else 0.0
        ),
        "agent_count": len(agent_seconds),
        "total_agent_seconds": sum(agent_seconds),
        "mean_agent_seconds": (
            sum(agent_seconds) / len(agent_seconds) if agent_seconds else 0.0
        ),
        "verification_count": len(verification_seconds),
        "total_verification_seconds": sum(verification_seconds),
        "mean_verification_seconds": (
            sum(verification_seconds) / len(verification_seconds)
            if verification_seconds
            else 0.0
        ),
    }
    if not any(phase_seconds.values()):
        return summary
    summary["phase_breakdown"] = {
        key: {
            "count": len(values),
            "total_seconds": sum(values),
            "mean_seconds": sum(values) / len(values) if values else None,
        }
        for key, values in phase_seconds.items()
    }
    complete_keys = (
        "workspace_seconds",
        "solver_checkout_seconds",
        "verifier_checkout_seconds",
        "cleanup_seconds",
    )
    complete_results = tuple(
        result
        for result in results
        if all(key in result.latency for key in complete_keys)
    )
    checkout_cleanup_seconds = sum(
        _number(result.latency["solver_checkout_seconds"])
        + _number(result.latency["verifier_checkout_seconds"])
        + _number(result.latency["cleanup_seconds"])
        for result in complete_results
    )
    workspace_cleanup_seconds = sum(
        _number(result.latency["workspace_seconds"])
        + _number(result.latency["cleanup_seconds"])
        for result in complete_results
    )
    summary["checkout_cleanup"] = {
        "count": len(complete_results),
        "total_seconds": checkout_cleanup_seconds,
        "share_of_workspace_plus_cleanup_seconds": (
            checkout_cleanup_seconds / workspace_cleanup_seconds
            if workspace_cleanup_seconds
            else None
        ),
    }
    return summary


def _latency_values(results: Sequence[ResultRecord], key: str) -> tuple[float, ...]:
    return tuple(
        _number(result.latency[key]) for result in results if key in result.latency
    )


def _result_cost_coverage(results: Sequence[ResultRecord]) -> Mapping[str, int]:
    measured = tuple(
        result for result in results if not _has_unknown_usage_or_cost(result)
    )
    return {
        "measured_result_count": len(measured),
        "measured_zero_cost_count": sum(
            1 for result in measured if _number(result.cost.get("total_cost")) == 0.0
        ),
        "unknown_result_count": len(results) - len(measured),
    }


def _cost_by_scoring_config(
    results: Sequence[ResultRecord],
) -> Mapping[str, Mapping[str, float | int | str | None]]:
    grouped: dict[str, dict[str, ResultRecord]] = {}
    for result in results:
        grouped.setdefault(result.scoring_config_digest, {}).setdefault(
            result_execution_digest(result), result
        )
    summaries: dict[str, Mapping[str, float | int | str | None]] = {}
    for scoring_digest in sorted(grouped):
        views = tuple(grouped[scoring_digest].values())
        measured = tuple(
            result for result in views if not _has_unknown_usage_or_cost(result)
        )
        pricing_versions = {result.pricing_version for result in views}
        summaries[scoring_digest] = {
            "execution_count": len(views),
            "measured_execution_count": len(measured),
            "pricing_version": next(iter(pricing_versions))
            if len(pricing_versions) == 1
            else None,
            "total_cost": (
                sum(_number(result.cost.get("total_cost")) for result in measured)
                if len(pricing_versions) == 1
                else None
            ),
            "unknown_execution_count": len(views) - len(measured),
        }
    return summaries


def _pricing_view_errors(results: Sequence[ResultRecord]) -> tuple[str, ...]:
    by_view: dict[tuple[str, str], ResultRecord] = {}
    errors: list[str] = []
    for result in results:
        key = (result_execution_digest(result), result.scoring_config_digest)
        existing = by_view.get(key)
        if existing is None:
            by_view[key] = result
            continue
        if (
            existing.cost != result.cost
            or existing.pricing_version != result.pricing_version
        ):
            errors.append(
                "conflicting pricing views for one execution and scoring configuration: "
                f"{existing.result_id}, {result.result_id}"
            )
    versions_by_scoring_config: dict[str, set[str]] = {}
    for result in results:
        versions_by_scoring_config.setdefault(result.scoring_config_digest, set()).add(
            result.pricing_version
        )
    errors.extend(
        f"scoring configuration {scoring_digest} has multiple pricing versions"
        for scoring_digest, versions in sorted(versions_by_scoring_config.items())
        if len(versions) > 1
    )
    return tuple(errors)


def build_selector_report(
    selections: Sequence[BenchmarkSelectionRecord],
    cell_sets: Sequence[EvaluationCellSet],
    result_matrices: Sequence[ResultMatrix],
    metrics: Sequence[MetricRecord],
    *,
    origins: Sequence[RollingOriginRecord] = (),
    feature_snapshots: Sequence[FeatureSnapshotRecord] = (),
    selector_inputs: Sequence[SelectorInput] = (),
    selectors: Sequence[SelectorRecord] = (),
    agents: Sequence[AgentRecord] = (),
    results: Sequence[ResultRecord] = (),
    task_pool: TaskPoolRecord | None = None,
    future_task_pools: Sequence[TaskPoolRecord] = (),
    artifact_root: Path | None = None,
) -> ReportSection:
    selection_errors = _validation_errors(
        "selection", selections, validate_benchmark_selection
    )
    cell_set_errors = _validation_errors(
        "cell_set", cell_sets, validate_evaluation_cell_set
    )
    matrix_errors = _validation_errors(
        "matrix", result_matrices, validate_result_matrix
    )
    metric_errors = _validation_errors("metric", metrics, validate_metric)
    trace_errors = _selector_trace_errors(
        selections, cell_sets, result_matrices, metrics
    )
    provenance_errors = _selector_provenance_errors(
        selections,
        cell_sets,
        result_matrices,
        origins,
        feature_snapshots,
        selector_inputs,
        selectors,
        agents,
        results,
        task_pool=task_pool,
        future_task_pools=future_task_pools,
        artifact_root=artifact_root,
    )
    future_timing_errors = _selection_future_timing_errors(
        selections, cell_sets, results
    )
    abstention_errors = _selector_abstention_errors(cell_sets, result_matrices, metrics)
    scoreability_errors = _matrix_scoreability_errors(result_matrices)
    metric_completeness_errors = _metric_completeness_errors(metrics)
    origin_ids = sorted(
        {selection.origin_id for selection in selections}
        | {metric.origin_id for metric in metrics}
    )
    origin_cohorts = _selector_origin_cohort_rows(
        task_pool,
        artifact_root,
        origins,
        cell_sets,
    )
    selection_rows = _selector_selection_rows(
        selections,
        cell_sets,
        result_matrices,
        metrics,
    )
    evidence_errors = (
        *selection_errors,
        *cell_set_errors,
        *matrix_errors,
        *metric_errors,
        *trace_errors,
        *provenance_errors,
        *future_timing_errors,
        *abstention_errors,
        *scoreability_errors,
        *metric_completeness_errors,
    )
    stratified_forecasts, stratified_forecast_errors = _selector_stratified_forecasts(
        selections,
        origins,
        feature_snapshots,
        selector_inputs,
        selectors,
        task_pool,
        artifact_root,
        inputs_valid=not evidence_errors,
    )
    mae_summary, mae_summary_errors = _selector_mae_summary(
        selectors,
        selections,
        metrics,
        result_matrices,
        inputs_valid=not evidence_errors,
    )
    limitations = (
        *evidence_errors,
        *stratified_forecast_errors,
        *mae_summary_errors,
    )
    has_selector_evidence = (
        bool(selections) and bool(cell_sets) and bool(result_matrices) and bool(metrics)
    )
    eligibility_modes = tuple(
        sorted({selection.eligibility_mode for selection in selections})
    )
    supported_claims = (
        tuple(f"{mode}_selector_performance_summary" for mode in eligibility_modes)
        if has_selector_evidence and not limitations
        else ()
    )
    if not has_selector_evidence:
        limitations = (
            *limitations,
            "selector performance evidence is absent or incomplete",
        )
    return ReportSection(
        section_id="selector_performance",
        heading="Selector Performance",
        summary={
            "selection_count": len(selections),
            "origin_ids": tuple(origin_ids),
            "origin_cohorts": origin_cohorts,
            "cell_set_count": len(cell_sets),
            "result_matrix_count": len(result_matrices),
            "metric_count": len(metrics),
            "eligibility_modes": eligibility_modes,
            "metrics_by_name": dict(
                sorted(Counter(metric.metric_name for metric in metrics).items())
            ),
            "stratified_forecasts": stratified_forecasts,
            "mae_summary": mae_summary,
            "selections": selection_rows,
        },
        source_digests={
            **_selector_source_digests(
                selections,
                cell_sets,
                result_matrices,
                metrics,
                origins,
                feature_snapshots,
                selector_inputs,
                selectors,
            ),
            "task_records_digest": (
                task_pool.task_records_digest if task_pool is not None else None
            ),
            "future_task_pool_digests": tuple(
                sorted(pool.task_pool_digest for pool in future_task_pools)
            ),
        },
        supported_claims=supported_claims,
        unsupported_claims=limitations,
        limitations=limitations,
    )


def _selector_origin_cohort_rows(
    task_pool: TaskPoolRecord | None,
    artifact_root: Path | None,
    origins: Sequence[RollingOriginRecord],
    cell_sets: Sequence[EvaluationCellSet],
) -> tuple[Mapping[str, Any], ...]:
    cohort_comparisons: dict[str, Mapping[str, Any]] = {}
    if task_pool is not None:
        try:
            bundle = load_validated_task_pool_bundle(
                task_pool,
                artifact_root or Path.cwd(),
            )
        except (KeyError, OSError, TypeError, ValueError):
            pass
        else:
            for origin in origins:
                if not origin.future_holdout_known:
                    continue
                try:
                    cohort_comparisons[origin.origin_id] = (
                        compare_arrival_and_label_time_cohorts(
                            origin,
                            bundle.tasks,
                            bundle.checks_by_id,
                        )
                    )
                except (KeyError, TypeError, ValueError):
                    continue
    realized_by_origin: dict[
        str, tuple[tuple[TaskCheckRef, ...], tuple[TaskCheckRef, ...]]
    ] = {}
    conflicting_origins: set[str] = set()
    for cell_set in cell_sets:
        if cell_set.origin_id in conflicting_origins:
            continue
        cohort = (
            cell_set.future_task_check_refs,
            cell_set.future_censored_task_check_refs,
        )
        existing = realized_by_origin.get(cell_set.origin_id)
        if existing is None:
            realized_by_origin[cell_set.origin_id] = cohort
        elif existing != cohort:
            realized_by_origin.pop(cell_set.origin_id, None)
            conflicting_origins.add(cell_set.origin_id)
    return tuple(
        _selector_origin_cohort_row(
            origin,
            cohort_comparisons.get(origin.origin_id, {}),
            realized_by_origin.get(origin.origin_id),
        )
        for origin in sorted(origins, key=lambda item: item.origin_id)
    )


def _selector_origin_cohort_row(
    origin: RollingOriginRecord,
    comparison: Mapping[str, Any],
    realized_cohort: tuple[tuple[TaskCheckRef, ...], tuple[TaskCheckRef, ...]] | None,
) -> Mapping[str, Any]:
    mature_refs, censored_refs = realized_cohort or (
        origin.future_holdout_task_check_refs,
        origin.future_censored_task_check_refs,
    )
    mature_count = len(mature_refs)
    censored_count = len(censored_refs)
    return {
        "origin_id": origin.origin_id,
        "future_cohort_time_basis": origin.future_cohort_time_basis,
        "maturity_lag_seconds": origin.maturity_lag_seconds,
        "label_maturity_cutoff": origin.label_maturity_cutoff,
        "history_mature_task_check_count": len(origin.history_task_check_refs),
        "history_censored_task_check_count": len(
            origin.history_censored_task_check_refs
        ),
        "mature_task_check_count": mature_count,
        "censored_task_check_count": censored_count,
        "mature_inclusion_rate": (
            mature_count / (mature_count + censored_count)
            if mature_count or censored_count
            else None
        ),
        **comparison,
    }


def _selector_selection_rows(
    selections: Sequence[BenchmarkSelectionRecord],
    cell_sets: Sequence[EvaluationCellSet],
    result_matrices: Sequence[ResultMatrix],
    metrics: Sequence[MetricRecord],
) -> tuple[Mapping[str, Any], ...]:
    cell_sets_by_selection = cast(
        Mapping[str, tuple[EvaluationCellSet, ...]],
        _group_by(cell_sets, "selection_id"),
    )
    matrices_by_selection = cast(
        Mapping[str, tuple[ResultMatrix, ...]],
        _group_by(result_matrices, "selection_id"),
    )
    metrics_by_selection = cast(
        Mapping[str, tuple[MetricRecord, ...]],
        _group_by(metrics, "selection_id"),
    )
    return tuple(
        _selector_selection_row(
            selection,
            cell_sets_by_selection.get(selection.selection_id, ()),
            matrices_by_selection.get(selection.selection_id, ()),
            metrics_by_selection.get(selection.selection_id, ()),
        )
        for selection in selections
    )


def _selector_selection_row(
    selection: BenchmarkSelectionRecord,
    cell_sets: Sequence[EvaluationCellSet],
    matrices: Sequence[ResultMatrix],
    metrics: Sequence[MetricRecord],
) -> Mapping[str, Any]:
    return {
        "selection_id": selection.selection_id,
        "origin_id": selection.origin_id,
        "selector_id": selection.selector_id,
        "budget_digest": selection.budget_digest,
        "selected_task_check_count": len(selection.selected_task_check_refs),
        "selected_task_check_refs": tuple(
            _ref_dict(ref) for ref in selection.selected_task_check_refs
        ),
        "selected_weights": dict(selection.selected_weights),
        "cell_set_digests": tuple(
            sorted(cell_set.cell_set_digest for cell_set in cell_sets)
        ),
        "cell_set_abstention_reasons": tuple(
            sorted(
                reason
                for cell_set in cell_sets
                if (reason := cell_set.abstention_reason)
            )
        ),
        "agent_ids": tuple(
            sorted({agent_id for matrix in matrices for agent_id in matrix.agent_ids})
        ),
        "matrices": tuple(
            _selector_matrix_row(matrix)
            for matrix in sorted(
                matrices,
                key=lambda item: (item.matrix_role, item.matrix_id),
            )
        ),
        "metrics": tuple(
            _selector_metric_row(metric)
            for metric in sorted(
                metrics,
                key=lambda item: (item.metric_name, item.metric_id),
            )
        ),
        "matrix_roles": tuple(sorted(matrix.matrix_role for matrix in matrices)),
        "matrix_scoreable_states": tuple(
            sorted(matrix.scoreable_state for matrix in matrices)
        ),
        "abstention_reasons": tuple(
            sorted(
                reason for matrix in matrices if (reason := matrix.abstention_reason)
            )
        ),
        "metric_names": tuple(sorted(metric.metric_name for metric in metrics)),
        "metric_digests": tuple(sorted(metric.metric_digest for metric in metrics)),
    }


def _selector_matrix_row(matrix: ResultMatrix) -> Mapping[str, Any]:
    return {
        "matrix_id": matrix.matrix_id,
        "matrix_role": matrix.matrix_role,
        "matrix_digest": matrix.matrix_digest,
        "agent_ids": matrix.agent_ids,
        "task_check_refs": tuple(_ref_dict(ref) for ref in matrix.task_check_refs),
        "join_policy_digest": matrix.join_policy_digest,
        "denominator_policy_digest": matrix.denominator_policy_digest,
        "scoreable_state": matrix.scoreable_state,
        "abstention_reason": matrix.abstention_reason,
        "cell_states": dict(
            sorted(Counter(cell.cell_state for cell in matrix.cells).items())
        ),
        "result_digests": tuple(
            sorted(cell.result_digest for cell in matrix.cells if cell.result_digest)
        ),
    }


def _selector_metric_row(metric: MetricRecord) -> Mapping[str, Any]:
    return {
        "metric_id": metric.metric_id,
        "metric_digest": metric.metric_digest,
        "metric_name": metric.metric_name,
        "metric_value": metric.metric_value,
        "metric_scope": metric.metric_scope,
        "agent_id": metric.agent_id,
        "agent_pair": metric.agent_pair,
        "aggregation_level": metric.aggregation_level,
        "stratum_ref": metric.stratum_ref,
        "budget_digest": metric.budget_digest,
        "evaluation_cell_set_digest": metric.evaluation_cell_set_digest,
        "selected_matrix_digest": metric.selected_matrix_digest,
        "future_matrix_digest": metric.future_matrix_digest,
        "join_policy_digest": metric.join_policy_digest,
        "denominator_policy_digest": metric.denominator_policy_digest,
        "completeness_state": metric.completeness_state,
        "abstention_reason": metric.abstention_reason,
    }


def _selector_stratified_forecasts(
    selections: Sequence[BenchmarkSelectionRecord],
    origins: Sequence[RollingOriginRecord],
    feature_snapshots: Sequence[FeatureSnapshotRecord],
    selector_inputs: Sequence[SelectorInput],
    selectors: Sequence[SelectorRecord],
    task_pool: TaskPoolRecord | None,
    artifact_root: Path | None,
    *,
    inputs_valid: bool,
) -> tuple[tuple[Mapping[str, Any], ...], tuple[str, ...]]:
    selector_by_id = {selector.selector_id: selector for selector in selectors}
    stratified_selections = _evaluated_stratified_selections(selections, selector_by_id)
    if not stratified_selections or not inputs_valid or task_pool is None:
        return (), ()
    try:
        task_by_id = _stratified_task_index(
            task_pool,
            artifact_root or Path.cwd(),
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        return (), (f"stratified forecast Task Pool cannot be validated: {exc}",)

    origin_by_id = {origin.origin_id: origin for origin in origins}
    snapshot_by_id = {
        snapshot.feature_snapshot_id: snapshot for snapshot in feature_snapshots
    }
    input_by_digest = {
        selector_input.selector_input_digest: selector_input
        for selector_input in selector_inputs
    }
    rows: list[Mapping[str, Any]] = []
    errors: list[str] = []
    for selection in sorted(
        stratified_selections,
        key=lambda item: (item.origin_id, item.selector_id, item.selection_id),
    ):
        try:
            row = _selector_stratified_forecast_row(
                selection,
                origin_by_id,
                snapshot_by_id,
                input_by_digest,
                selector_by_id,
                task_by_id,
            )
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(
                f"selection {selection.selection_id} stratified forecast is invalid: {exc}"
            )
            continue
        rows.append(row)
    return tuple(rows), tuple(errors)


def _evaluated_stratified_selections(
    selections: Sequence[BenchmarkSelectionRecord],
    selector_by_id: Mapping[str, SelectorRecord],
) -> tuple[BenchmarkSelectionRecord, ...]:
    return tuple(
        selection
        for selection in selections
        if selection.selector_id in selector_by_id
        and selector_by_id[selection.selector_id].selector_family
        == "stratified_forecast"
    )


def _stratified_task_index(
    task_pool: TaskPoolRecord,
    artifact_root: Path,
) -> Mapping[str, TaskRecord]:
    bundle = load_validated_task_pool_bundle(task_pool, artifact_root)
    return {task.task_id: task for task in bundle.tasks}


def _selector_stratified_forecast_row(
    selection: BenchmarkSelectionRecord,
    origin_by_id: Mapping[str, RollingOriginRecord],
    snapshot_by_id: Mapping[str, FeatureSnapshotRecord],
    input_by_digest: Mapping[str, SelectorInput],
    selector_by_id: Mapping[str, SelectorRecord],
    task_by_id: Mapping[str, TaskRecord],
) -> Mapping[str, Any]:
    origin = origin_by_id[selection.origin_id]
    future_strata = {
        task_check_ref_key(ref): task_by_id[ref.task_id].sampling_stratum
        for ref in origin.future_holdout_task_check_refs
    }
    summary = summarize_stratified_forecast(
        input_by_digest[selection.selection_input_digest],
        snapshot_by_id[selection.feature_snapshot_id],
        selector_by_id[selection.selector_id],
        selection,
        origin,
        future_strata,
    )
    return {
        "selection_id": selection.selection_id,
        "origin_id": selection.origin_id,
        "selector_id": selection.selector_id,
        **summary,
    }


def _selector_mae_summary(
    selectors: Sequence[SelectorRecord],
    selections: Sequence[BenchmarkSelectionRecord],
    metrics: Sequence[MetricRecord],
    result_matrices: Sequence[ResultMatrix],
    *,
    inputs_valid: bool,
) -> tuple[Mapping[str, object] | None, tuple[str, ...]]:
    evaluated_selector_ids = {selection.selector_id for selection in selections}
    evaluated_selectors = tuple(
        selector
        for selector in selectors
        if selector.selector_id in evaluated_selector_ids
    )
    if (
        not inputs_valid
        or not evaluated_selector_ids
        or {selector.selector_id for selector in evaluated_selectors}
        != evaluated_selector_ids
    ):
        return None, ()
    try:
        summary = summarize_selector_mae(
            evaluated_selectors,
            selections,
            tuple(
                metric
                for metric in metrics
                if metric.metric_name == "future_pass_rate_mae"
            ),
            tuple(
                matrix
                for matrix in result_matrices
                if matrix.matrix_role == "future_holdout"
            ),
        )
    except ValueError as exc:
        return None, (f"selector MAE summary is invalid: {exc}",)
    return summary, ()


def _selector_source_digests(
    selections: Sequence[BenchmarkSelectionRecord],
    cell_sets: Sequence[EvaluationCellSet],
    result_matrices: Sequence[ResultMatrix],
    metrics: Sequence[MetricRecord],
    origins: Sequence[RollingOriginRecord],
    feature_snapshots: Sequence[FeatureSnapshotRecord],
    selector_inputs: Sequence[SelectorInput],
    selectors: Sequence[SelectorRecord],
) -> Mapping[str, Any]:
    return {
        "selection_digests": tuple(
            sorted(selection.selection_digest for selection in selections)
        ),
        "cell_set_digests": tuple(
            sorted(cell_set.cell_set_digest for cell_set in cell_sets)
        ),
        "matrix_digests": tuple(
            sorted(matrix.matrix_digest for matrix in result_matrices)
        ),
        "metric_digests": tuple(sorted(metric.metric_digest for metric in metrics)),
        "origin_digests": tuple(sorted(origin.origin_digest for origin in origins)),
        "feature_snapshot_digests": tuple(
            sorted(
                snapshot.feature_snapshot_digest or "" for snapshot in feature_snapshots
            )
        ),
        "selector_input_digests": tuple(
            sorted(
                selector_input.selector_input_digest
                for selector_input in selector_inputs
            )
        ),
        "selector_digests": tuple(
            sorted(selector.selector_digest for selector in selectors)
        ),
    }


def build_claim_boundary(
    task_pool: TaskPoolRecord,
    selections: Sequence[BenchmarkSelectionRecord],
    cell_sets: Sequence[EvaluationCellSet],
    result_matrices: Sequence[ResultMatrix],
    metrics: Sequence[MetricRecord],
    claim_config: ClaimConfig,
    results: Sequence[ResultRecord] = (),
    artifact_root: Path | None = None,
    *,
    origins: Sequence[RollingOriginRecord] = (),
    feature_snapshots: Sequence[FeatureSnapshotRecord] = (),
    selector_inputs: Sequence[SelectorInput] = (),
    selectors: Sequence[SelectorRecord] = (),
    agents: Sequence[AgentRecord] = (),
    future_task_pools: Sequence[TaskPoolRecord] = (),
) -> ReportSection:
    supported: list[str] = []
    unsupported: list[str] = []
    requested = set(claim_config.requested_claims)
    if "task_pool_bundle_internal_consistency" in requested:
        _claim(
            supported,
            unsupported,
            "task_pool_bundle_internal_consistency",
            *_task_pool_bundle_internal_consistency_claim(task_pool, artifact_root),
        )
    if "benchmark_selection_frozen" in requested:
        _claim(
            supported,
            unsupported,
            "benchmark_selection_frozen",
            *_benchmark_selection_claim(task_pool, selections),
        )
    if "cache_completeness" in requested:
        _claim(
            supported,
            unsupported,
            "cache_completeness",
            *_cache_completeness_claim(result_matrices),
        )
    if "selector_metrics" in requested:
        provenance_errors = _selector_provenance_errors(
            selections,
            cell_sets,
            result_matrices,
            origins,
            feature_snapshots,
            selector_inputs,
            selectors,
            agents,
            results,
            task_pool=task_pool,
            future_task_pools=future_task_pools,
            artifact_root=artifact_root,
        )
        future_timing_errors = _selection_future_timing_errors(
            selections,
            cell_sets,
            results,
        )
        _claim(
            supported,
            unsupported,
            "selector_metrics",
            *_selector_metrics_claim(
                task_pool,
                selections,
                cell_sets,
                result_matrices,
                metrics,
                provenance_errors,
                future_timing_errors,
            ),
        )
    if "agent_result_identity" in requested:
        _claim(
            supported,
            unsupported,
            "agent_result_identity",
            *_agent_result_identity_claim(
                task_pool,
                result_matrices,
                results,
                agents,
                artifact_root,
                future_task_pools,
            ),
        )
    supported_tuple = tuple(supported)
    unsupported_tuple = tuple(unsupported)
    return ReportSection(
        section_id="claim_boundary",
        heading="Claim Boundary",
        summary={
            "claim_config_digest": claim_config.claim_config_digest,
            "requested_claims": claim_config.requested_claims,
            "supported_count": len(supported_tuple),
            "unsupported_count": len(unsupported_tuple),
            "abstention_count": sum(1 for metric in metrics if metric.abstention_reason)
            + sum(1 for matrix in result_matrices if matrix.abstention_reason),
            "selection_count": len(selections),
            "matrix_count": len(result_matrices),
            "metric_count": len(metrics),
            "selector_metric_eligibility_modes": tuple(
                sorted({selection.eligibility_mode for selection in selections})
            ),
        },
        source_digests={
            "task_pool_digest": task_pool.task_pool_digest,
            "future_task_pool_digests": tuple(
                sorted(pool.task_pool_digest for pool in future_task_pools)
            ),
            **_selector_source_digests(
                selections,
                cell_sets,
                result_matrices,
                metrics,
                origins,
                feature_snapshots,
                selector_inputs,
                selectors,
            ),
            "result_digests": tuple(sorted(result.result_digest for result in results)),
            "agent_manifest_digests": tuple(
                sorted(agent.agent_manifest_digest for agent in agents)
            ),
        },
        artifact_paths=_task_pool_artifact_paths(
            (task_pool, *future_task_pools),
            artifact_root,
        ),
        supported_claims=supported_tuple,
        unsupported_claims=unsupported_tuple,
        limitations=unsupported_tuple,
    )


def _task_pool_artifact_paths(
    task_pools: Sequence[TaskPoolRecord],
    artifact_root: Path | None,
) -> tuple[str, ...]:
    paths: list[str] = []
    for task_pool in task_pools:
        paths.extend(
            ref
            for ref in (
                task_pool.task_records_ref,
                task_pool.check_records_ref,
                task_pool.certification_evidence_ref,
                task_pool.source_event_records_ref,
                task_pool.generation_provenance_ref,
            )
            if ref is not None
        )
        paths.extend(_nested_generation_artifact_paths(task_pool, artifact_root))
    return tuple(paths)


def _nested_generation_artifact_paths(
    task_pool: TaskPoolRecord,
    artifact_root: Path | None,
) -> tuple[str, ...]:
    if task_pool.generation_provenance_ref is None:
        return ()
    try:
        bundle = load_validated_task_pool_bundle(
            task_pool,
            artifact_root or Path.cwd(),
        )
    except (KeyError, OSError, TypeError, ValueError):
        return ()
    provenance = bundle.generation_provenance
    if provenance is None:
        return ()
    frame_ref = (
        None
        if provenance.observed_frame is None
        else provenance.observed_frame.get("event_inventory_ref")
    )
    adapter_ref = provenance.outputs.get("adapter_evidence_ref")
    return tuple(
        ref for ref in (frame_ref, adapter_ref) if isinstance(ref, str) and ref
    )


def _task_pool_bundle_internal_consistency_claim(
    task_pool: TaskPoolRecord,
    artifact_root: Path | None,
) -> tuple[bool, str]:
    errors = _task_pool_validation_errors(task_pool, artifact_root)
    return not errors, "; ".join(errors)


def _benchmark_selection_claim(
    task_pool: TaskPoolRecord,
    selections: Sequence[BenchmarkSelectionRecord],
) -> tuple[bool, str]:
    validations = tuple(
        validate_benchmark_selection(selection) for selection in selections
    )
    identity_errors = _record_identity_errors(
        selections,
        "selection_id",
        "selection",
    )
    selections_valid = (
        all(validation.ok for validation in validations) and not identity_errors
    )
    selections_match_task_pool = all(
        selection.task_pool_id == task_pool.task_pool_id
        and selection.task_pool_digest == task_pool.task_pool_digest
        for selection in selections
    )
    errors = (
        *identity_errors,
        *_selection_claim_errors(validations, selections_match_task_pool),
    )
    return (
        bool(selections) and selections_valid and selections_match_task_pool,
        _claim_reason(
            "selection evidence is absent, invalid, or unbound from task pool",
            errors,
        ),
    )


def _cache_completeness_claim(
    result_matrices: Sequence[ResultMatrix],
) -> tuple[bool, str]:
    validations = tuple(validate_result_matrix(matrix) for matrix in result_matrices)
    identity_errors = _record_identity_errors(
        result_matrices,
        "matrix_id",
        "matrix",
    )
    matrices_valid = (
        all(validation.ok for validation in validations) and not identity_errors
    )
    scoreability_errors = _matrix_scoreability_errors(result_matrices)
    errors = (
        *identity_errors,
        *(error for validation in validations for error in validation.errors),
        *scoreability_errors,
    )
    return (
        bool(result_matrices) and matrices_valid and not scoreability_errors,
        _claim_reason(
            "result matrix evidence is absent, invalid, incomplete, or abstained",
            errors,
        ),
    )


def _selector_selection_claim_evidence(
    task_pool: TaskPoolRecord,
    selections: Sequence[BenchmarkSelectionRecord],
) -> tuple[bool, tuple[str, ...]]:
    validations = tuple(
        validate_benchmark_selection(selection) for selection in selections
    )
    identities_unique = not _record_identity_errors(
        selections,
        "selection_id",
        "selection",
    )
    matches_task_pool = all(
        selection.task_pool_id == task_pool.task_pool_id
        and selection.task_pool_digest == task_pool.task_pool_digest
        for selection in selections
    )
    return (
        all(validation.ok for validation in validations)
        and identities_unique
        and matches_task_pool,
        _selection_claim_errors(validations, matches_task_pool),
    )


def _selector_matrix_claim_evidence(
    result_matrices: Sequence[ResultMatrix],
) -> tuple[bool, tuple[str, ...]]:
    validations = tuple(validate_result_matrix(matrix) for matrix in result_matrices)
    identities_unique = not _record_identity_errors(
        result_matrices,
        "matrix_id",
        "matrix",
    )
    scoreability_errors = _matrix_scoreability_errors(result_matrices)
    errors = (
        *(error for validation in validations for error in validation.errors),
        *scoreability_errors,
    )
    return (
        all(validation.ok for validation in validations)
        and identities_unique
        and not scoreability_errors,
        errors,
    )


def _selector_metric_claim_evidence(
    metrics: Sequence[MetricRecord],
) -> tuple[bool, tuple[str, ...]]:
    validations = tuple(validate_metric(metric) for metric in metrics)
    abstained = any(metric.abstention_reason for metric in metrics)
    completeness_errors = _metric_completeness_errors(metrics)
    return (
        all(validation.ok for validation in validations)
        and not abstained
        and not completeness_errors,
        completeness_errors,
    )


def _selector_cell_set_claim_evidence(
    cell_sets: Sequence[EvaluationCellSet],
) -> tuple[bool, tuple[str, ...]]:
    validations = tuple(
        validate_evaluation_cell_set(cell_set) for cell_set in cell_sets
    )
    abstention_reasons = tuple(
        cell_set.abstention_reason
        for cell_set in cell_sets
        if cell_set.abstention_reason
    )
    errors = (
        *(error for validation in validations for error in validation.errors),
        *(f"evaluation cell set abstained: {reason}" for reason in abstention_reasons),
    )
    return (
        all(validation.ok for validation in validations) and not abstention_reasons,
        errors,
    )


def _selector_metrics_claim(
    task_pool: TaskPoolRecord,
    selections: Sequence[BenchmarkSelectionRecord],
    cell_sets: Sequence[EvaluationCellSet],
    result_matrices: Sequence[ResultMatrix],
    metrics: Sequence[MetricRecord],
    provenance_errors: Sequence[str],
    future_timing_errors: Sequence[str],
) -> tuple[bool, str]:
    selection_evidence_ok, selection_errors = _selector_selection_claim_evidence(
        task_pool,
        selections,
    )
    matrix_evidence_ok, matrix_errors = _selector_matrix_claim_evidence(result_matrices)
    metric_evidence_ok, metric_errors = _selector_metric_claim_evidence(metrics)
    cell_set_evidence_ok, cell_set_errors = _selector_cell_set_claim_evidence(cell_sets)
    trace_errors = _selector_trace_errors(
        selections, cell_sets, result_matrices, metrics
    )
    errors = (
        *trace_errors,
        *provenance_errors,
        *future_timing_errors,
        *selection_errors,
        *matrix_errors,
        *cell_set_errors,
        *metric_errors,
        *_selector_abstention_errors(cell_sets, result_matrices, metrics),
    )
    supported = (
        bool(metrics)
        and selection_evidence_ok
        and matrix_evidence_ok
        and metric_evidence_ok
        and cell_set_evidence_ok
        and not trace_errors
        and not provenance_errors
        and not future_timing_errors
    )
    return supported, _claim_reason(
        "metric evidence is absent, invalid, carries abstention reasons, or is not traceable",
        errors,
    )


def _agent_result_identity_claim(
    task_pool: TaskPoolRecord,
    result_matrices: Sequence[ResultMatrix],
    results: Sequence[ResultRecord],
    agents: Sequence[AgentRecord],
    artifact_root: Path | None,
    future_task_pools: Sequence[TaskPoolRecord],
) -> tuple[bool, str]:
    matrix_validations = tuple(
        validate_result_matrix(matrix) for matrix in result_matrices
    )
    matrix_identity_errors = _record_identity_errors(
        result_matrices,
        "matrix_id",
        "matrix",
    )
    matrices_valid = (
        all(validation.ok for validation in matrix_validations)
        and not matrix_identity_errors
    )
    identity_errors = (
        *matrix_identity_errors,
        *_record_identity_errors(results, "result_id", "result"),
        *_record_identity_errors(agents, "agent_id", "Agent"),
        *_result_execution_conflict_errors(results),
        *_result_agent_identity_errors(results, agents),
        *_result_identity_trace_errors(result_matrices, results),
        *_result_matrix_trace_errors(result_matrices, results),
        *_result_task_pool_identity_errors(
            (task_pool, *future_task_pools),
            results,
            artifact_root or Path.cwd(),
        ),
    )
    result_validations = tuple(validate_result(result) for result in results)
    results_valid = all(validation.ok for validation in result_validations)
    has_identity_evidence = bool(results) and any(
        _cell_binds_result(cell) for matrix in result_matrices for cell in matrix.cells
    )
    errors = (
        *identity_errors,
        *(error for validation in result_validations for error in validation.errors),
    )
    return (
        has_identity_evidence
        and matrices_valid
        and results_valid
        and not identity_errors,
        _claim_reason(
            "result identity evidence is absent, invalid, or not traceable",
            errors,
        ),
    )


def write_report(
    sections: Sequence[ReportSection],
    output_path: Path,
    artifact_root: Path | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    root = artifact_root or output_path.parent
    sanitized_sections = tuple(
        _sanitize_report_section(section, root) for section in sections
    )
    if output_path.suffix == ".json":
        output_path.write_text(
            canonical_json(
                tuple(_section_data(section) for section in sanitized_sections)
            )
            + "\n",
            encoding="utf-8",
        )
        return
    lines = ["# Barcarolle Report", ""]
    for section in sanitized_sections:
        lines.extend(
            [
                f"## {section.heading}",
                "",
                "### Summary",
                "",
                "```json",
                canonical_json(section.summary),
                "```",
                "",
                "### Source Digests",
                "",
                "```json",
                canonical_json(section.source_digests),
                "```",
                "",
            ]
        )
        if section.supported_claims:
            lines.extend(
                [
                    "### Supported Claims",
                    "",
                    *[f"- {claim}" for claim in section.supported_claims],
                    "",
                ]
            )
        if section.unsupported_claims:
            lines.extend(
                [
                    "### Unsupported Claims",
                    "",
                    *[f"- {claim}" for claim in section.unsupported_claims],
                    "",
                ]
            )
        if section.artifact_paths:
            lines.extend(
                [
                    "### Artifact Paths",
                    "",
                    *[f"- {artifact_path}" for artifact_path in section.artifact_paths],
                    "",
                ]
            )
        if section.limitations:
            lines.extend(
                [
                    "### Limitations",
                    "",
                    *[f"- {limitation}" for limitation in section.limitations],
                    "",
                ]
            )
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _sanitize_report_section(
    section: ReportSection, artifact_root: Path
) -> ReportSection:
    return replace(
        section,
        summary=_sanitize_artifact_refs(section.summary, artifact_root),
        artifact_paths=tuple(
            _sanitize_artifact_path(artifact_path, artifact_root)
            for artifact_path in section.artifact_paths
        ),
    )


def _sanitize_artifact_refs(value: Any, artifact_root: Path) -> Any:
    if isinstance(value, str):
        return _sanitize_artifact_path(value, artifact_root)
    if isinstance(value, Mapping):
        return {
            key: _sanitize_artifact_refs(item, artifact_root)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return tuple(_sanitize_artifact_refs(item, artifact_root) for item in value)
    if isinstance(value, list):
        return [_sanitize_artifact_refs(item, artifact_root) for item in value]
    return value


def _sanitize_artifact_path(artifact_path: str, artifact_root: Path) -> str:
    path = Path(artifact_path)
    if not path.is_absolute():
        return artifact_path
    try:
        return path.resolve().relative_to(artifact_root.resolve()).as_posix()
    except (OSError, ValueError):
        return path.name if path.name not in {"", ".", ".."} else "external-artifact"


def _section_data(section: ReportSection) -> Mapping[str, Any]:
    return {
        "section_id": section.section_id,
        "heading": section.heading,
        "summary": section.summary,
        "source_digests": section.source_digests,
        "artifact_paths": section.artifact_paths,
        "supported_claims": section.supported_claims,
        "unsupported_claims": section.unsupported_claims,
        "limitations": section.limitations,
    }


def _task_pool_validation_errors(
    task_pool: TaskPoolRecord,
    artifact_root: Path | None = None,
) -> tuple[str, ...]:
    errors: list[str] = []
    if task_pool.task_pool_digest != canonical_digest(
        task_pool, exclude_self_digest=True
    ):
        errors.append("task_pool_digest does not match canonical task pool")
    if not task_pool.task_ids:
        errors.append("task_ids are empty")
    if not task_pool.check_ids:
        errors.append("check_ids are empty")
    for field in (
        "task_records_ref",
        "check_records_ref",
        "certification_evidence_ref",
        "source_event_records_ref",
        "task_records_digest",
        "check_records_digest",
        "rejection_summary_digest",
        "source_event_records_digest",
        "certification_config_digest",
    ):
        if not getattr(task_pool, field):
            errors.append(f"{field} is missing")
    if not task_pool.certification_evidence_digest:
        errors.append("certification_evidence_digest is missing")
    errors.extend(_task_pool_artifact_errors(task_pool, artifact_root))
    return tuple(errors)


def _task_pool_source_event_summary(
    task_pool: TaskPoolRecord,
    artifact_root: Path | None,
) -> Mapping[str, Any]:
    try:
        bundle = load_validated_task_pool_bundle(
            task_pool,
            artifact_root or Path.cwd(),
        )
    except (KeyError, OSError, TypeError, ValueError):
        return {}
    delays = sorted(
        (
            parse_utc_timestamp(event.label_mature_at)
            - parse_utc_timestamp(event.task_material_available_at)
        ).total_seconds()
        for event in bundle.source_events
        if event.label_mature_at is not None
        and event.task_material_available_at is not None
    )
    delay_summary: Mapping[str, float | int] = {}
    if delays:
        middle = len(delays) // 2
        median = (
            delays[middle]
            if len(delays) % 2
            else (delays[middle - 1] + delays[middle]) / 2
        )
        delay_summary = {
            "count": len(delays),
            "min": delays[0],
            "median": median,
            "max": delays[-1],
        }
    return {
        "source_event_count": len(bundle.source_events),
        "source_event_dispositions": dict(
            sorted(Counter(event.disposition for event in bundle.source_events).items())
        ),
        "right_censored_source_event_count": sum(
            event.label_mature_at is None for event in bundle.source_events
        ),
        "label_delay_seconds": delay_summary,
        **_task_quality_summary(
            bundle.source_events,
            bundle.certification_evidence,
        ),
        **_task_pool_generation_summary(bundle),
    }


def _task_pool_generation_summary(bundle: TaskPoolBundle) -> Mapping[str, Any]:
    provenance = getattr(bundle, "generation_provenance", None)
    if provenance is None:
        return {
            "generation_evidence_state": "absent",
            "generation_authority_kind": None,
            "observed_frame_authority": None,
            "observed_frame_event_count": 0,
        }
    frame = provenance.observed_frame
    return {
        "generation_evidence_state": "bound",
        "generation_authority_kind": provenance.run.get("authority_kind"),
        "observed_frame_authority": (
            None if frame is None else frame.get("observation_authority")
        ),
        "observed_frame_event_count": len(getattr(bundle, "observed_frame_events", ())),
    }


def _task_quality_summary(
    source_events: Sequence[SourceEventRecord],
    certification_evidence: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    accepted_count = sum(
        record["accepted"] is True for record in certification_evidence
    )
    rejected_count = sum(
        record["accepted"] is False for record in certification_evidence
    )
    candidate_count = len(certification_evidence)
    rejected_events = tuple(
        event for event in source_events if event.disposition != "accepted"
    )
    rejection_stage_counts = Counter(
        event.rejection_stage
        for event in rejected_events
        if event.rejection_stage is not None
    )
    rejection_reason_counts = Counter(
        reason for event in rejected_events for reason in event.rejection_reasons
    )
    repeated = tuple(
        record for record in certification_evidence if record["repeat_count"] > 1
    )
    flaky_quarantined = tuple(
        record
        for record in repeated
        if record["accepted"] is False
        and _has_conflicting_certification_outcomes(record)
    )
    return {
        "certification_yield": {
            "candidate_count": candidate_count,
            "accepted_count": accepted_count,
            "rejected_count": rejected_count,
            "rate": accepted_count / candidate_count if candidate_count else None,
        },
        "pre_certification_excluded_count": sum(
            event.disposition == "excluded" for event in source_events
        ),
        "rejection_stage_counts": dict(sorted(rejection_stage_counts.items())),
        "rejection_reason_counts": dict(sorted(rejection_reason_counts.items())),
        "flaky_quarantine": {
            "count": len(flaky_quarantined),
            "configured_repeated_candidate_count": len(repeated),
            "rate": len(flaky_quarantined) / len(repeated) if repeated else None,
            "definition": (
                "rejected repeated certification with conflicting normalized "
                "outcomes on the base or reference-patch side"
            ),
        },
    }


def _has_conflicting_certification_outcomes(
    evidence: Mapping[str, Any],
) -> bool:
    for field_name in ("base_check", "reference_patch_check"):
        outcomes = tuple(attempt["outcome"] for attempt in evidence[field_name])
        if len(set(outcomes)) > 1:
            return True
    return False


def _task_pool_artifact_errors(
    task_pool: TaskPoolRecord,
    artifact_root: Path | None,
) -> tuple[str, ...]:
    root = artifact_root or Path.cwd()
    try:
        load_validated_task_pool_bundle(task_pool, root)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        return (str(exc),)
    return ()


def _validation_errors(
    label: str, records: Sequence[Any], validate: Any
) -> tuple[str, ...]:
    errors: list[str] = []
    for record in records:
        validation = validate(record)
        if not validation.ok:
            record_id = getattr(
                record, f"{label}_id", getattr(record, "result_id", "record")
            )
            errors.append(f"{label} {record_id}: {'; '.join(validation.errors)}")
    return tuple(errors)


def _record_identity_errors(
    records: Sequence[Any],
    field: str,
    label: str,
) -> tuple[str, ...]:
    seen: set[str] = set()
    errors: list[str] = []
    for record in records:
        identity = getattr(record, field)
        if identity in seen:
            errors.append(f"duplicate {label} identity: {identity}")
        seen.add(identity)
    return tuple(errors)


def _group_by(records: Sequence[Any], field: str) -> Mapping[str, tuple[Any, ...]]:
    grouped: dict[str, list[Any]] = {}
    for record in records:
        grouped.setdefault(getattr(record, field), []).append(record)
    return {key: tuple(value) for key, value in grouped.items()}


def _ref_dict(ref: Any) -> Mapping[str, str]:
    return {"task_id": ref.task_id, "check_id": ref.check_id}


def _claim(
    supported: list[str], unsupported: list[str], claim: str, ok: bool, reason: str
) -> None:
    if ok:
        supported.append(claim)
    else:
        unsupported.append(f"{claim}: {reason}")


def _claim_reason(default: str, errors: Sequence[str]) -> str:
    return "; ".join(errors) if errors else default


def _selector_trace_errors(
    selections: Sequence[BenchmarkSelectionRecord],
    cell_sets: Sequence[EvaluationCellSet],
    result_matrices: Sequence[ResultMatrix],
    metrics: Sequence[MetricRecord],
) -> tuple[str, ...]:
    identity_errors = (
        *_record_identity_errors(selections, "selection_id", "selection"),
        *_record_identity_errors(cell_sets, "cell_set_id", "cell_set"),
        *_record_identity_errors(result_matrices, "matrix_id", "matrix"),
        *_record_identity_errors(metrics, "metric_id", "metric"),
    )
    selection_by_id = {selection.selection_id: selection for selection in selections}
    cell_sets_by_selection = _group_by(cell_sets, "selection_id")
    matrices_by_selection = _group_by(result_matrices, "selection_id")
    metrics_by_selection = _group_by(metrics, "selection_id")
    matrix_by_digest = {matrix.matrix_digest: matrix for matrix in result_matrices}
    cell_set_by_digest = {cell_set.cell_set_digest: cell_set for cell_set in cell_sets}
    return (
        *identity_errors,
        *_cell_set_selection_trace_errors(cell_sets, selection_by_id),
        *_matrix_selection_trace_errors(result_matrices, selection_by_id),
        *_selection_evidence_trace_errors(
            selections,
            cell_sets_by_selection,
            matrices_by_selection,
            metrics_by_selection,
        ),
        *_metric_trace_errors(
            metrics,
            selection_by_id,
            cell_set_by_digest,
            matrix_by_digest,
        ),
    )


def _cell_set_selection_trace_errors(
    cell_sets: Sequence[EvaluationCellSet],
    selection_by_id: Mapping[str, BenchmarkSelectionRecord],
) -> tuple[str, ...]:
    errors: list[str] = []
    for cell_set in cell_sets:
        selection = selection_by_id.get(cell_set.selection_id)
        if selection is None:
            errors.append(
                f"cell_set {cell_set.cell_set_id} references missing selection {cell_set.selection_id}"
            )
            continue
        if cell_set.origin_id != selection.origin_id:
            errors.append(
                f"cell_set {cell_set.cell_set_id} origin does not match selection {selection.selection_id}"
            )
        if cell_set.selected_task_check_refs != selection.selected_task_check_refs:
            errors.append(
                f"cell_set {cell_set.cell_set_id} selected refs do not match selection {selection.selection_id}"
            )
    return tuple(errors)


def _matrix_selection_trace_errors(
    result_matrices: Sequence[ResultMatrix],
    selection_by_id: Mapping[str, BenchmarkSelectionRecord],
) -> tuple[str, ...]:
    errors: list[str] = []
    for matrix in result_matrices:
        selection = selection_by_id.get(matrix.selection_id)
        if selection is None:
            errors.append(
                f"matrix {matrix.matrix_id} references missing selection {matrix.selection_id}"
            )
            continue
        if matrix.origin_id != selection.origin_id:
            errors.append(
                f"matrix {matrix.matrix_id} origin does not match selection {selection.selection_id}"
            )
        if (
            matrix.matrix_role == "selected"
            and matrix.task_check_refs != selection.selected_task_check_refs
        ):
            errors.append(
                f"matrix {matrix.matrix_id} selected denominator does not match selection {selection.selection_id}"
            )
    return tuple(errors)


def _selection_evidence_trace_errors(
    selections: Sequence[BenchmarkSelectionRecord],
    cell_sets_by_selection: Mapping[str, tuple[Any, ...]],
    matrices_by_selection: Mapping[str, tuple[Any, ...]],
    metrics_by_selection: Mapping[str, tuple[Any, ...]],
) -> tuple[str, ...]:
    errors: list[str] = []
    for selection in selections:
        selection_cell_sets = cell_sets_by_selection.get(selection.selection_id, ())
        selection_matrices = matrices_by_selection.get(selection.selection_id, ())
        if not selection_cell_sets:
            errors.append(
                f"selection {selection.selection_id} has no evaluation cell set"
            )
        roles = Counter(matrix.matrix_role for matrix in selection_matrices)
        if roles.get("selected", 0) == 0:
            errors.append(
                f"selection {selection.selection_id} has no selected result matrix"
            )
        if roles.get("future_holdout", 0) == 0:
            errors.append(
                f"selection {selection.selection_id} has no future result matrix"
            )
        if not metrics_by_selection.get(selection.selection_id):
            errors.append(f"selection {selection.selection_id} has no metric evidence")
        agent_sets = {matrix.agent_ids for matrix in selection_matrices}
        if len(agent_sets) > 1:
            errors.append(
                f"selection {selection.selection_id} has mismatched matrix Agent sets"
            )
        for matrix in selection_matrices:
            for cell_set in selection_cell_sets:
                future_refs = cell_set.future_task_check_refs
                if (
                    matrix.matrix_role == "future_holdout"
                    and matrix.task_check_refs != future_refs
                ):
                    errors.append(
                        f"matrix {matrix.matrix_id} future denominator does not match cell set {cell_set.cell_set_id}"
                    )
    return tuple(errors)


def _metric_trace_errors(
    metrics: Sequence[MetricRecord],
    selection_by_id: Mapping[str, BenchmarkSelectionRecord],
    cell_set_by_digest: Mapping[str, EvaluationCellSet],
    matrix_by_digest: Mapping[str, ResultMatrix],
) -> tuple[str, ...]:
    errors: list[str] = []
    for metric in metrics:
        selection = selection_by_id.get(metric.selection_id)
        if selection is None:
            errors.append(
                f"metric {metric.metric_id} references missing selection {metric.selection_id}"
            )
            continue
        cell_set = cell_set_by_digest.get(metric.evaluation_cell_set_digest)
        selected_matrix = matrix_by_digest.get(metric.selected_matrix_digest)
        future_matrix = matrix_by_digest.get(metric.future_matrix_digest)
        errors.extend(
            _metric_evidence_trace_errors(
                metric,
                selection,
                cell_set,
                selected_matrix,
                future_matrix,
            )
        )
        if selected_matrix is None or future_matrix is None:
            continue
        errors.extend(
            _metric_value_trace_errors(
                metric,
                selection,
                selected_matrix,
                future_matrix,
            )
        )
    return tuple(errors)


def _metric_evidence_trace_errors(
    metric: MetricRecord,
    selection: BenchmarkSelectionRecord,
    cell_set: EvaluationCellSet | None,
    selected_matrix: ResultMatrix | None,
    future_matrix: ResultMatrix | None,
) -> tuple[str, ...]:
    errors: list[str] = []
    if metric.metric_config_digest != METRIC_CONFIG_DIGEST:
        errors.append(f"metric {metric.metric_id} uses an unsupported metric protocol")
    if cell_set is None:
        errors.append(
            f"metric {metric.metric_id} evaluation_cell_set_digest is not supplied"
        )
    if selected_matrix is None:
        errors.append(
            f"metric {metric.metric_id} selected_matrix_digest is not supplied"
        )
    if future_matrix is None:
        errors.append(f"metric {metric.metric_id} future_matrix_digest is not supplied")
    if cell_set is not None and (
        cell_set.selection_id != selection.selection_id
        or cell_set.origin_id != selection.origin_id
    ):
        errors.append(
            f"metric {metric.metric_id} cell set does not match selection {selection.selection_id}"
        )
    if selected_matrix is not None:
        errors.extend(
            _metric_matrix_trace_errors(
                metric,
                selection,
                selected_matrix,
                label="selected",
                expected_role="selected",
            )
        )
    if future_matrix is not None:
        errors.extend(
            _metric_matrix_trace_errors(
                metric,
                selection,
                future_matrix,
                label="future",
                expected_role="future_holdout",
            )
        )
    if (
        selected_matrix is not None
        and future_matrix is not None
        and selected_matrix.agent_ids != future_matrix.agent_ids
    ):
        errors.append(
            f"metric {metric.metric_id} selected/future Agent sets do not match"
        )
    if (
        cell_set is not None
        and selected_matrix is not None
        and not _matrix_cells_match_cell_set(selected_matrix, cell_set)
    ):
        errors.append(
            f"metric {metric.metric_id} selected matrix cells do not match evaluation cell set"
        )
    if (
        cell_set is not None
        and future_matrix is not None
        and not _matrix_cells_match_cell_set(future_matrix, cell_set)
    ):
        errors.append(
            f"metric {metric.metric_id} future matrix cells do not match evaluation cell set"
        )
    if metric.budget_digest != selection.budget_digest:
        errors.append(
            f"metric {metric.metric_id} budget digest does not match selection {selection.selection_id}"
        )
    if metric.origin_id != selection.origin_id:
        errors.append(
            f"metric {metric.metric_id} origin does not match selection {selection.selection_id}"
        )
    return tuple(errors)


def _metric_matrix_trace_errors(
    metric: MetricRecord,
    selection: BenchmarkSelectionRecord,
    matrix: ResultMatrix,
    *,
    label: str,
    expected_role: str,
) -> tuple[str, ...]:
    errors: list[str] = []
    if matrix.matrix_role != expected_role:
        errors.append(f"metric {metric.metric_id} {label} matrix has wrong role")
    if (
        matrix.selection_id != selection.selection_id
        or matrix.origin_id != selection.origin_id
    ):
        errors.append(
            f"metric {metric.metric_id} {label} matrix does not match selection {selection.selection_id}"
        )
    if matrix.join_policy_digest != metric.join_policy_digest:
        errors.append(
            f"metric {metric.metric_id} join policy does not match {label} matrix"
        )
    if matrix.denominator_policy_digest != metric.denominator_policy_digest:
        errors.append(
            f"metric {metric.metric_id} denominator policy does not match {label} matrix"
        )
    return tuple(errors)


def _metric_value_trace_errors(
    metric: MetricRecord,
    selection: BenchmarkSelectionRecord,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
) -> tuple[str, ...]:
    if (
        metric.metric_scope != "aggregate"
        or metric.aggregation_level != "all_agents"
        or metric.agent_id is not None
        or metric.agent_pair is not None
        or metric.stratum_ref is not None
    ):
        return (
            f"metric {metric.metric_id} is not a recomputable aggregate all-Agents metric",
        )
    try:
        expected_values = compute_selection_metric_values(
            selection,
            selected_matrix,
            future_matrix,
        )
    except (OverflowError, TypeError, ValueError, ZeroDivisionError) as exc:
        return (f"metric {metric.metric_id} cannot be recomputed: {exc}",)
    expected_value = expected_values.get(metric.metric_name)
    if expected_value is None:
        return (
            f"metric {metric.metric_id} has an unsupported metric name: {metric.metric_name}",
        )
    if metric.metric_value != expected_value:
        return (
            f"metric {metric.metric_id} value {metric.metric_value} does not match recomputed value {expected_value}",
        )
    return ()


def _selector_provenance_errors(
    selections: Sequence[BenchmarkSelectionRecord],
    cell_sets: Sequence[EvaluationCellSet],
    result_matrices: Sequence[ResultMatrix],
    origins: Sequence[RollingOriginRecord],
    feature_snapshots: Sequence[FeatureSnapshotRecord],
    selector_inputs: Sequence[SelectorInput],
    selectors: Sequence[SelectorRecord],
    agents: Sequence[AgentRecord],
    results: Sequence[ResultRecord],
    *,
    task_pool: TaskPoolRecord | None = None,
    future_task_pools: Sequence[TaskPoolRecord] = (),
    artifact_root: Path | None = None,
) -> tuple[str, ...]:
    if not selections:
        return ()
    errors: list[str] = []
    errors.extend(_validation_errors("origin", origins, validate_rolling_origin))
    errors.extend(
        _validation_errors(
            "feature_snapshot", feature_snapshots, validate_feature_snapshot
        )
    )
    errors.extend(
        _validation_errors("selector_input", selector_inputs, validate_selector_input)
    )
    errors.extend(_validation_errors("selector", selectors, validate_selector))

    indexes = _selector_provenance_indexes(
        origins,
        feature_snapshots,
        selector_inputs,
        selectors,
        results,
        agents,
        errors,
    )
    _append_required_selector_evidence_errors(
        errors,
        origins,
        feature_snapshots,
        selector_inputs,
        selectors,
        agents,
        results,
    )
    _append_origin_task_pool_errors(
        errors,
        task_pool,
        origins,
        feature_snapshots,
        artifact_root,
    )
    errors.extend(
        _prospective_future_task_pool_errors(
            selections,
            cell_sets,
            origins,
            task_pool,
            future_task_pools,
            artifact_root,
        )
    )

    _append_selection_provenance_errors(
        errors,
        selections,
        cast(
            Mapping[str, tuple[EvaluationCellSet, ...]],
            _group_by(cell_sets, "selection_id"),
        ),
        cast(
            Mapping[str, tuple[ResultMatrix, ...]],
            _group_by(result_matrices, "selection_id"),
        ),
        indexes,
    )

    errors.extend(_result_execution_conflict_errors(results))
    errors.extend(_result_identity_trace_errors(result_matrices, results))
    errors.extend(_result_matrix_trace_errors(result_matrices, results))
    if agents:
        errors.extend(_result_agent_identity_errors(results, agents))
    return tuple(errors)


def _selector_provenance_indexes(
    origins: Sequence[RollingOriginRecord],
    feature_snapshots: Sequence[FeatureSnapshotRecord],
    selector_inputs: Sequence[SelectorInput],
    selectors: Sequence[SelectorRecord],
    results: Sequence[ResultRecord],
    agents: Sequence[AgentRecord],
    errors: list[str],
) -> _SelectorProvenanceIndexes:
    origin_by_id = _unique_record_index(origins, "origin_id", "origin", errors)
    snapshot_by_id = _unique_record_index(
        feature_snapshots,
        "feature_snapshot_id",
        "feature_snapshot",
        errors,
    )
    input_by_digest = _unique_record_index(
        selector_inputs,
        "selector_input_digest",
        "selector_input digest",
        errors,
    )
    _unique_record_index(
        selector_inputs,
        "selector_input_id",
        "selector_input",
        errors,
    )
    selector_by_id = _unique_record_index(selectors, "selector_id", "selector", errors)
    result_by_id = _unique_record_index(results, "result_id", "result", errors)
    agent_by_id = _unique_record_index(agents, "agent_id", "Agent", errors)
    return _SelectorProvenanceIndexes(
        origins=cast(Mapping[str, RollingOriginRecord], origin_by_id),
        snapshots=cast(Mapping[str, FeatureSnapshotRecord], snapshot_by_id),
        inputs=cast(Mapping[str, SelectorInput], input_by_digest),
        selectors=cast(Mapping[str, SelectorRecord], selector_by_id),
        results=cast(Mapping[str, ResultRecord], result_by_id),
        agents=cast(Mapping[str, AgentRecord], agent_by_id),
    )


def _append_required_selector_evidence_errors(
    errors: list[str],
    origins: Sequence[RollingOriginRecord],
    feature_snapshots: Sequence[FeatureSnapshotRecord],
    selector_inputs: Sequence[SelectorInput],
    selectors: Sequence[SelectorRecord],
    agents: Sequence[AgentRecord],
    results: Sequence[ResultRecord],
) -> None:
    if not origins:
        errors.append("rolling-origin evidence is missing")
    if not feature_snapshots:
        errors.append("feature-snapshot evidence is missing")
    if not selector_inputs:
        errors.append("selector-input evidence is missing")
    if not selectors:
        errors.append("Selector evidence is missing")
    if not agents:
        errors.append("Agent evidence is missing")
    if not results:
        errors.append("Result evidence for selector matrices is missing")


def _append_origin_task_pool_errors(
    errors: list[str],
    task_pool: TaskPoolRecord | None,
    origins: Sequence[RollingOriginRecord],
    feature_snapshots: Sequence[FeatureSnapshotRecord],
    artifact_root: Path | None,
) -> None:
    if task_pool is None or not origins:
        return
    try:
        bundle = load_validated_task_pool_bundle(
            task_pool,
            artifact_root or Path.cwd(),
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        errors.append(f"rolling-origin Task Pool bundle cannot be validated: {exc}")
        return
    for origin in origins:
        validation = validate_rolling_origin_against_records(
            origin,
            task_pool,
            bundle.tasks,
            bundle.checks_by_id,
        )
        errors.extend(
            f"origin {origin.origin_id}: {error}" for error in validation.errors
        )
    origin_by_id = {origin.origin_id: origin for origin in origins}
    for snapshot in feature_snapshots:
        origin = origin_by_id.get(snapshot.origin_id)
        if origin is None:
            continue
        try:
            ensure_feature_snapshot_task_metadata_provenance(
                snapshot,
                origin,
                task_pool,
                bundle.tasks,
            )
        except (TypeError, ValueError) as exc:
            errors.append(f"feature snapshot {snapshot.feature_snapshot_id}: {exc}")


def _prospective_future_task_pool_errors(
    selections: Sequence[BenchmarkSelectionRecord],
    cell_sets: Sequence[EvaluationCellSet],
    origins: Sequence[RollingOriginRecord],
    task_pool: TaskPoolRecord | None,
    future_task_pools: Sequence[TaskPoolRecord],
    artifact_root: Path | None,
) -> tuple[str, ...]:
    strict_selections = tuple(
        selection
        for selection in selections
        if selection.eligibility_mode == "strict_prospective"
    )
    if not strict_selections:
        return ()
    if task_pool is None:
        return ("strict-prospective evaluation is missing its selection Task Pool",)
    root = artifact_root or Path.cwd()
    try:
        selection_bundle = load_validated_task_pool_bundle(task_pool, root)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        return (f"strict-prospective selection Task Pool cannot be validated: {exc}",)
    errors: list[str] = []
    origins_by_id = {origin.origin_id: origin for origin in origins}
    cell_sets_by_selection = _group_by(cell_sets, "selection_id")
    pools_by_identity, pool_errors = _future_task_pool_index(future_task_pools)
    errors.extend(pool_errors)
    bundle_by_identity: dict[tuple[str, str], TaskPoolBundle] = {}
    for selection in strict_selections:
        origin = origins_by_id.get(selection.origin_id)
        selection_cell_sets = cell_sets_by_selection.get(selection.selection_id, ())
        if origin is None or len(selection_cell_sets) != 1:
            continue
        cell_set = selection_cell_sets[0]
        identity = (
            cell_set.future_task_pool_id,
            cell_set.future_task_pool_digest,
        )
        future_pool = pools_by_identity.get(identity)
        if future_pool is None:
            errors.append(
                f"cell_set {cell_set.cell_set_id} references missing future Task Pool"
            )
            continue
        future_bundle = bundle_by_identity.get(identity)
        if future_bundle is None:
            try:
                future_bundle = load_validated_task_pool_bundle(future_pool, root)
            except (KeyError, OSError, TypeError, ValueError) as exc:
                errors.append(
                    f"future Task Pool {future_pool.task_pool_id} cannot be validated: {exc}"
                )
                continue
            bundle_by_identity[identity] = future_bundle
        errors.extend(
            _prospective_future_cohort_errors(
                selection,
                origin,
                cell_set,
                selection_bundle,
                future_bundle,
            )
        )
    return tuple(errors)


def _future_task_pool_index(
    future_task_pools: Sequence[TaskPoolRecord],
) -> tuple[dict[tuple[str, str], TaskPoolRecord], tuple[str, ...]]:
    pools_by_identity: dict[tuple[str, str], TaskPoolRecord] = {}
    errors: list[str] = []
    for pool in future_task_pools:
        identity = (pool.task_pool_id, pool.task_pool_digest)
        if identity in pools_by_identity:
            errors.append("future Task Pool evidence contains a duplicate identity")
        pools_by_identity[identity] = pool
    return pools_by_identity, tuple(errors)


def _prospective_future_cohort_errors(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    cell_set: EvaluationCellSet,
    selection_bundle: TaskPoolBundle,
    future_bundle: TaskPoolBundle,
) -> tuple[str, ...]:
    try:
        mature_refs, censored_refs = materialize_prospective_future_cohort(
            selection,
            origin,
            selection_bundle.task_pool,
            future_bundle.task_pool,
            selection_bundle.tasks,
            selection_bundle.checks_by_id,
            future_bundle.tasks,
            future_bundle.checks_by_id,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return (
            f"cell_set {cell_set.cell_set_id} future cohort cannot be replayed: {exc}",
        )
    errors: list[str] = []
    if cell_set.future_task_check_refs != mature_refs:
        errors.append(
            f"cell_set {cell_set.cell_set_id} mature future refs do not match later Task Pool"
        )
    if cell_set.future_censored_task_check_refs != censored_refs:
        errors.append(
            f"cell_set {cell_set.cell_set_id} censored future refs do not match later Task Pool"
        )
    return tuple(errors)


def _append_selection_provenance_errors(
    errors: list[str],
    selections: Sequence[BenchmarkSelectionRecord],
    cell_sets_by_selection: Mapping[str, tuple[EvaluationCellSet, ...]],
    matrices_by_selection: Mapping[str, tuple[ResultMatrix, ...]],
    indexes: _SelectorProvenanceIndexes,
) -> None:
    for selection in selections:
        resolved = _resolve_selection_provenance(errors, selection, indexes)
        cell_sets = cell_sets_by_selection.get(selection.selection_id, ())
        matrices = matrices_by_selection.get(selection.selection_id, ())
        _append_origin_selection_link_errors(
            errors,
            selection,
            resolved.origin,
            cell_sets,
            matrices,
        )
        _append_snapshot_selection_link_errors(
            errors,
            selection,
            resolved.snapshot,
            resolved.origin,
        )
        _append_selector_input_selection_errors(
            errors,
            selection,
            resolved,
            matrices,
            indexes,
        )
        if (
            resolved.selector_input is not None
            and resolved.snapshot is not None
            and resolved.selector is not None
        ):
            _append_selector_replay_errors(
                errors,
                selection,
                resolved.selector_input,
                resolved.snapshot,
                resolved.selector,
            )


def _resolve_selection_provenance(
    errors: list[str],
    selection: BenchmarkSelectionRecord,
    indexes: _SelectorProvenanceIndexes,
) -> _ResolvedSelectionProvenance:
    origin = indexes.origins.get(selection.origin_id)
    snapshot = indexes.snapshots.get(selection.feature_snapshot_id)
    selector_input = indexes.inputs.get(selection.selection_input_digest)
    selector = indexes.selectors.get(selection.selector_id)
    if origin is None:
        errors.append(
            f"selection {selection.selection_id} references missing origin {selection.origin_id}"
        )
    if snapshot is None:
        errors.append(
            "selection "
            f"{selection.selection_id} references missing feature snapshot "
            f"{selection.feature_snapshot_id}"
        )
    if selector_input is None:
        errors.append(
            "selection "
            f"{selection.selection_id} references missing selector input digest "
            f"{selection.selection_input_digest}"
        )
    if selector is None:
        errors.append(
            f"selection {selection.selection_id} references missing Selector {selection.selector_id}"
        )
    elif selector.selector_digest != selection.selector_digest:
        errors.append(
            f"selection {selection.selection_id} Selector digest does not match Selector record"
        )
    return _ResolvedSelectionProvenance(
        origin=origin,
        snapshot=snapshot,
        selector_input=selector_input,
        selector=selector,
    )


def _append_origin_selection_link_errors(
    errors: list[str],
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord | None,
    cell_sets: Sequence[EvaluationCellSet],
    matrices: Sequence[ResultMatrix],
) -> None:
    if origin is None:
        return
    if (
        origin.task_pool_id != selection.task_pool_id
        or origin.task_pool_digest != selection.task_pool_digest
    ):
        errors.append(
            f"selection {selection.selection_id} Task Pool does not match origin"
        )
    if origin.eligibility_mode != selection.eligibility_mode:
        errors.append(
            f"selection {selection.selection_id} eligibility mode does not match origin"
        )
    for cell_set in cell_sets:
        if origin.eligibility_mode == "counterfactual_replay" and (
            cell_set.future_task_check_refs != origin.future_holdout_task_check_refs
            or cell_set.future_censored_task_check_refs
            != origin.future_censored_task_check_refs
            or cell_set.future_task_pool_id != origin.task_pool_id
            or cell_set.future_task_pool_digest != origin.task_pool_digest
        ):
            errors.append(
                f"cell_set {cell_set.cell_set_id} future evidence does not match origin {origin.origin_id}"
            )
    expected_future_refs = origin.future_holdout_task_check_refs
    if origin.eligibility_mode == "strict_prospective" and len(cell_sets) == 1:
        expected_future_refs = cell_sets[0].future_task_check_refs
    for matrix in matrices:
        if (
            matrix.matrix_role == "future_holdout"
            and matrix.task_check_refs != expected_future_refs
        ):
            errors.append(
                f"matrix {matrix.matrix_id} future denominator does not match origin {origin.origin_id}"
            )


def _append_snapshot_selection_link_errors(
    errors: list[str],
    selection: BenchmarkSelectionRecord,
    snapshot: FeatureSnapshotRecord | None,
    origin: RollingOriginRecord | None,
) -> None:
    if snapshot is None:
        return
    if snapshot.leakage_lint_status != "passed":
        errors.append(
            f"feature snapshot {snapshot.feature_snapshot_id} did not persist passed leakage lint"
        )
    if origin is not None and snapshot.origin_id != origin.origin_id:
        errors.append(
            f"feature snapshot {snapshot.feature_snapshot_id} origin does not match selection"
        )


def _append_selector_input_selection_errors(
    errors: list[str],
    selection: BenchmarkSelectionRecord,
    resolved: _ResolvedSelectionProvenance,
    matrices: Sequence[ResultMatrix],
    indexes: _SelectorProvenanceIndexes,
) -> None:
    if resolved.selector_input is None:
        return
    _append_selector_input_link_errors(
        errors,
        selection,
        resolved.selector_input,
        resolved.origin,
        resolved.snapshot,
        resolved.selector,
        indexes.agents,
        indexes.results,
    )
    for matrix in matrices:
        if matrix.agent_ids != resolved.selector_input.agent_ids:
            errors.append(
                f"matrix {matrix.matrix_id} Agent set does not match selector input"
            )


def _append_selector_input_link_errors(
    errors: list[str],
    selection: BenchmarkSelectionRecord,
    selector_input: SelectorInput,
    origin: RollingOriginRecord | None,
    snapshot: FeatureSnapshotRecord | None,
    selector: SelectorRecord | None,
    agent_by_id: Mapping[str, AgentRecord],
    result_by_id: Mapping[str, ResultRecord],
) -> None:
    if selector_input.origin_id != selection.origin_id:
        errors.append(
            f"selector input {selector_input.selector_input_id} origin does not match selection"
        )
    if (
        selector_input.task_pool_id != selection.task_pool_id
        or selector_input.task_pool_digest != selection.task_pool_digest
    ):
        errors.append(
            f"selector input {selector_input.selector_input_id} Task Pool does not match selection"
        )
    if selector_input.feature_snapshot_id != selection.feature_snapshot_id:
        errors.append(
            f"selector input {selector_input.selector_input_id} feature snapshot does not match selection"
        )
    if selector_input.budget_digest != selection.budget_digest:
        errors.append(
            f"selector input {selector_input.selector_input_id} budget does not match selection"
        )
    if selector_input.eligibility_mode != selection.eligibility_mode:
        errors.append(
            f"selector input {selector_input.selector_input_id} eligibility mode does not match selection"
        )
    if any(
        ref not in selector_input.eligible_task_check_refs
        for ref in selection.selected_task_check_refs
    ):
        errors.append(
            f"selection {selection.selection_id} includes refs outside selector input eligibility"
        )
    if origin is not None:
        if selector_input.eligible_task_check_refs != origin.history_task_check_refs:
            errors.append(
                f"selector input {selector_input.selector_input_id} history refs do not match origin"
            )
        if selector_input.origin_as_of_cutoff != origin.as_of_cutoff:
            errors.append(
                f"selector input {selector_input.selector_input_id} cutoff does not match origin"
            )
    if snapshot is not None:
        if selector_input.feature_records_digest != snapshot.feature_records_digest:
            errors.append(
                f"selector input {selector_input.selector_input_id} feature digest does not match snapshot"
            )
        if selector_input.leakage_policy_digest != snapshot.leakage_policy_digest:
            errors.append(
                f"selector input {selector_input.selector_input_id} leakage policy does not match snapshot"
            )
        if selector_input.feature_snapshot_lint_status != snapshot.leakage_lint_status:
            errors.append(
                f"selector input {selector_input.selector_input_id} lint status does not match snapshot"
            )
    if set(agent_by_id) != set(selector_input.agent_ids):
        errors.append(
            f"selector input {selector_input.selector_input_id} Agent set does not match supplied Agents"
        )
    elif (
        tuple(
            canonical_digest(agent_by_id[agent_id])
            for agent_id in selector_input.agent_ids
        )
        != selector_input.agent_record_digests
    ):
        errors.append(
            f"selector input {selector_input.selector_input_id} Agent identities do not match supplied Agents"
        )

    pre_origin_results = _resolved_pre_origin_results(
        errors,
        selector_input,
        result_by_id,
    )
    _append_selector_input_result_view_errors(
        errors,
        selector_input,
        snapshot,
        selector,
        pre_origin_results,
    )


def _resolved_pre_origin_results(
    errors: list[str],
    selector_input: SelectorInput,
    result_by_id: Mapping[str, ResultRecord],
) -> tuple[ResultRecord, ...]:
    pre_origin_results: list[ResultRecord] = []
    eligible_keys = {
        (ref.task_id, ref.check_id) for ref in selector_input.eligible_task_check_refs
    }
    for result_id, result_digest in zip(
        selector_input.pre_origin_result_ids,
        selector_input.pre_origin_result_digests,
    ):
        result = result_by_id.get(result_id)
        if result is None:
            errors.append(
                f"selector input {selector_input.selector_input_id} references missing Result {result_id}"
            )
            continue
        if result.result_digest != result_digest:
            errors.append(
                f"selector input {selector_input.selector_input_id} Result digest does not match {result_id}"
            )
            continue
        pre_origin_results.append(result)
        if result.agent_id not in selector_input.agent_ids:
            errors.append(
                f"selector input {selector_input.selector_input_id} includes Result outside Agent set"
            )
        if (result.task_id, result.check_id) not in eligible_keys:
            errors.append(
                f"selector input {selector_input.selector_input_id} includes Result outside origin history"
            )
        if _timestamp_is_after(
            result.result_available_at,
            selector_input.origin_as_of_cutoff or "",
        ):
            errors.append(
                f"selector input {selector_input.selector_input_id} includes post-origin Result {result_id}"
            )
    return tuple(pre_origin_results)


def _append_selector_input_result_view_errors(
    errors: list[str],
    selector_input: SelectorInput,
    snapshot: FeatureSnapshotRecord | None,
    selector: SelectorRecord | None,
    pre_origin_results: Sequence[ResultRecord],
) -> None:
    if snapshot is None or len(pre_origin_results) != len(
        selector_input.pre_origin_result_ids
    ):
        return
    if snapshot.result_view_digest != _result_view_digest(pre_origin_results):
        errors.append(
            f"feature snapshot {snapshot.feature_snapshot_id} Result view does not match selector input"
        )
    if selector is not None:
        disallowed_classes = tuple(
            sorted(
                {
                    record.leakage_class
                    for record in snapshot.feature_records
                    if record.leakage_class not in selector.allowed_feature_classes
                }
            )
        )
        if disallowed_classes:
            errors.append(
                f"feature snapshot {snapshot.feature_snapshot_id} uses classes not allowed by Selector: "
                + ", ".join(disallowed_classes)
            )
    for record in snapshot.feature_records:
        if _timestamp_is_after(
            record.observed_at,
            selector_input.origin_as_of_cutoff or "",
        ):
            errors.append(
                f"feature snapshot {snapshot.feature_snapshot_id} contains post-origin feature {record.feature_id}"
            )


def _append_selector_replay_errors(
    errors: list[str],
    selection: BenchmarkSelectionRecord,
    selector_input: SelectorInput,
    snapshot: FeatureSnapshotRecord,
    selector: SelectorRecord,
) -> None:
    try:
        ensure_selection_replay(selector_input, snapshot, selector, selection)
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(
            f"selection {selection.selection_id} cannot replay deterministic Selector: {exc}"
        )


def _unique_record_index(
    records: Sequence[Any],
    field: str,
    label: str,
    errors: list[str],
) -> dict[str, Any]:
    indexed: dict[str, Any] = {}
    for record in records:
        key = getattr(record, field)
        if key in indexed:
            errors.append(f"duplicate {label} identity: {key}")
            continue
        indexed[key] = record
    return indexed


def _timestamp_is_after(left: str, right: str) -> bool:
    if not left or not right:
        return False
    try:
        return parse_utc_timestamp(left) > parse_utc_timestamp(right)
    except (TypeError, ValueError):
        return False


def _selection_future_timing_errors(
    selections: Sequence[BenchmarkSelectionRecord],
    cell_sets: Sequence[EvaluationCellSet],
    results: Sequence[ResultRecord],
) -> tuple[str, ...]:
    selection_by_id = {selection.selection_id: selection for selection in selections}
    result_by_id = {result.result_id: result for result in results}
    errors: list[str] = []
    checked: set[tuple[str, str]] = set()
    for cell_set in cell_sets:
        selection = selection_by_id.get(cell_set.selection_id)
        if selection is None or selection.eligibility_mode != "strict_prospective":
            continue
        future_keys = {
            (ref.task_id, ref.check_id) for ref in cell_set.future_task_check_refs
        }
        for cell in cell_set.cells:
            if (
                cell.result_id is None
                or (cell.task_id, cell.check_id) not in future_keys
                or (selection.selection_id, cell.result_id) in checked
            ):
                continue
            checked.add((selection.selection_id, cell.result_id))
            result = result_by_id.get(cell.result_id)
            if result is None:
                continue
            try:
                selection_time = parse_utc_timestamp(selection.created_at)
                result_time = parse_utc_timestamp(result.result_available_at)
            except (TypeError, ValueError):
                continue
            if result_time <= selection_time:
                errors.append(
                    f"selection {selection.selection_id} was created at or after "
                    f"future Result {result.result_id} became available"
                )
    return tuple(errors)


def _selector_abstention_errors(
    cell_sets: Sequence[EvaluationCellSet],
    result_matrices: Sequence[ResultMatrix],
    metrics: Sequence[MetricRecord],
) -> tuple[str, ...]:
    errors: list[str] = []
    errors.extend(
        f"cell_set {cell_set.cell_set_id} abstained: {cell_set.abstention_reason}"
        for cell_set in cell_sets
        if cell_set.abstention_reason
    )
    errors.extend(
        f"matrix {matrix.matrix_id} abstained: {matrix.abstention_reason}"
        for matrix in result_matrices
        if matrix.abstention_reason
    )
    errors.extend(
        f"metric {metric.metric_id} abstained: {metric.abstention_reason}"
        for metric in metrics
        if metric.abstention_reason
    )
    return tuple(errors)


def _matrix_scoreability_errors(
    result_matrices: Sequence[ResultMatrix],
) -> tuple[str, ...]:
    errors: list[str] = []
    for matrix in result_matrices:
        if matrix.scoreable_state not in {"complete", "complete_with_exclusions"}:
            errors.append(
                f"matrix {matrix.matrix_id} scoreable_state is {matrix.scoreable_state}"
            )
        if denominator_error := matrix_denominator_error(matrix):
            errors.append(
                f"matrix {matrix.matrix_id} denominator is unsafe: {denominator_error}"
            )
        non_result_counts = Counter(
            cell.cell_state
            for cell in matrix.cells
            if cell.cell_state not in {"result", "excluded"}
        )
        if non_result_counts:
            counts = ", ".join(
                f"{state}={count}" for state, count in sorted(non_result_counts.items())
            )
            errors.append(
                f"matrix {matrix.matrix_id} contains non-result cells: {counts}"
            )
    return tuple(errors)


def _metric_completeness_errors(metrics: Sequence[MetricRecord]) -> tuple[str, ...]:
    return tuple(
        f"metric {metric.metric_id} completeness_state is {metric.completeness_state}"
        for metric in metrics
        if metric.completeness_state not in {"complete", "complete_with_exclusions"}
    )


def _result_agent_identity_errors(
    results: Sequence[ResultRecord], agents: Sequence[AgentRecord]
) -> tuple[str, ...]:
    agent_by_id = {agent.agent_id: agent for agent in agents}
    errors: list[str] = []
    for result in results:
        agent = agent_by_id.get(result.agent_id)
        if agent is None:
            continue
        if (
            agent_record_from_cache_identity(result.agent_id, result.cache_identity)
            != agent
        ):
            errors.append(
                f"result {result.result_id} cache identity does not match Agent {agent.agent_id}"
            )
    unknown_agents = tuple(
        sorted({result.agent_id for result in results} - set(agent_by_id))
    )
    if unknown_agents:
        errors.append(f"results reference unknown Agents: {', '.join(unknown_agents)}")
    return tuple(errors)


def _result_measurement_errors(results: Sequence[ResultRecord]) -> tuple[str, ...]:
    errors: list[str] = []
    for result in results:
        if "total_cost" not in result.cost:
            errors.append(f"result {result.result_id} cost.total_cost is missing")
        elif result.cost["total_cost"] is None:
            pass
        elif not _is_number(result.cost["total_cost"]):
            errors.append(f"result {result.result_id} cost.total_cost is non-numeric")
        if "workspace_seconds" not in result.latency:
            errors.append(
                f"result {result.result_id} latency.workspace_seconds is missing"
            )
        elif not _is_number(result.latency["workspace_seconds"]):
            errors.append(
                f"result {result.result_id} latency.workspace_seconds is non-numeric"
            )
    return tuple(errors)


def _has_unknown_usage_or_cost(result: ResultRecord) -> bool:
    return result.cost.get("total_cost") is None


def _selection_claim_errors(
    selection_validations: Sequence[Any], selections_match_task_pool: bool
) -> tuple[str, ...]:
    errors = [
        error for validation in selection_validations for error in validation.errors
    ]
    if not selections_match_task_pool:
        errors.append("selection task_pool binding does not match report task_pool")
    return tuple(errors)


def _matrix_cells_match_cell_set(
    matrix: ResultMatrix, cell_set: EvaluationCellSet
) -> bool:
    expected_refs = (
        cell_set.selected_task_check_refs
        if matrix.matrix_role == "selected"
        else cell_set.future_task_check_refs
    )
    expected_ref_keys = {(ref.task_id, ref.check_id) for ref in expected_refs}
    expected = {
        (cell.agent_id, cell.task_id, cell.check_id): (
            cell.required_identity_digest,
            cell.result_id,
            cell.result_digest,
            cell.outcome,
        )
        for cell in cell_set.cells
        if (cell.task_id, cell.check_id) in expected_ref_keys
    }
    actual = {
        (cell.agent_id, cell.task_id, cell.check_id): (
            cell.required_identity_digest,
            cell.result_id,
            cell.result_digest,
            cell.outcome,
        )
        for cell in matrix.cells
    }
    return actual == expected


def _result_identity_trace_errors(
    result_matrices: Sequence[ResultMatrix], results: Sequence[ResultRecord]
) -> tuple[str, ...]:
    if not results:
        return ()
    result_by_digest = {result.result_digest: result for result in results}
    errors: list[str] = []
    for matrix in result_matrices:
        for cell in matrix.cells:
            if not _cell_binds_result(cell):
                continue
            if cell.result_digest is None:
                errors.append(
                    f"matrix {matrix.matrix_id} cell binds result_id without result_digest"
                )
                continue
            if cell.result_id is None:
                errors.append(
                    f"matrix {matrix.matrix_id} cell binds result_digest without result_id"
                )
                continue
            result = result_by_digest.get(cell.result_digest)
            if result is None:
                errors.append(
                    f"matrix {matrix.matrix_id} cell references missing result digest {cell.result_digest}"
                )
                continue
            mismatches = set(result_cell_record_mismatches(cell, result))
            if "result_id" in mismatches:
                errors.append(
                    f"matrix {matrix.matrix_id} cell result_id does not match result digest {cell.result_digest}"
                )
            if mismatches & {"agent_id", "task_id", "check_id"}:
                errors.append(
                    f"matrix {matrix.matrix_id} cell Agent/Task/Check does not match result {result.result_id}"
                )
            if "required_identity_digest" in mismatches:
                errors.append(
                    f"matrix {matrix.matrix_id} cell identity digest does not match result {result.result_id}"
                )
            if "outcome" in mismatches:
                errors.append(
                    f"matrix {matrix.matrix_id} cell outcome does not match result {result.result_id}"
                )
    return tuple(errors)


def _result_matrix_trace_errors(
    result_matrices: Sequence[ResultMatrix],
    results: Sequence[ResultRecord],
) -> tuple[str, ...]:
    return tuple(
        error
        for matrix in result_matrices
        for error in result_matrix_evidence_errors(matrix, results)
    )


def _result_task_pool_identity_errors(
    task_pools: Sequence[TaskPoolRecord],
    results: Sequence[ResultRecord],
    artifact_root: Path,
) -> tuple[str, ...]:
    if not results:
        return ()
    members_by_ref: dict[tuple[str, str], list[tuple[TaskRecord, CheckRecord]]] = {}
    for task_pool in task_pools:
        try:
            bundle = load_validated_task_pool_bundle(task_pool, artifact_root)
        except (KeyError, OSError, TypeError, ValueError) as exc:
            return (
                f"frozen Task Pool {task_pool.task_pool_id} is unavailable or invalid: {exc}",
            )
        tasks_by_id = {task.task_id: task for task in bundle.tasks}
        for check_id, check in bundle.checks_by_id.items():
            task = tasks_by_id.get(check.task_id)
            if task is not None:
                members_by_ref.setdefault((task.task_id, check_id), []).append(
                    (task, check)
                )
    errors: list[str] = []
    for result in results:
        candidates = members_by_ref.get((result.task_id, result.check_id), ())
        if not candidates:
            errors.append(
                f"result {result.result_id} is not a member of a supplied frozen Task Pool"
            )
            continue
        if not any(
            check.task_id == task.task_id
            and check.check_id in task.check_ids
            and not cache_identity_task_check_mismatches(
                result.cache_identity,
                task,
                check,
            )
            for task, check in candidates
        ):
            errors.append(
                f"result {result.result_id} identity does not match the frozen Task/Check"
            )
    return tuple(errors)


def _cell_binds_result(cell: ResultCellRef) -> bool:
    return cell.result_id is not None or cell.result_digest is not None


def _number(value: Any) -> float:
    return float(value) if _is_number(value) else 0.0


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)
