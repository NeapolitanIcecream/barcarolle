"""Claim-safe reporting from existing Barcarolle records."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    CheckRecord,
    EvaluationCellSet,
    MetricRecord,
    ResultCellRef,
    ResultMatrix,
    ResultRecord,
    TaskPoolRecord,
    TaskRecord,
    canonical_digest,
    canonical_json,
    load_jsonl_records,
    validate_benchmark_selection,
    validate_evaluation_cell_set,
    validate_metric,
    validate_result,
    validate_result_matrix,
)
from barcarolle.selection.evaluation import compute_selection_metric_values
from barcarolle.task_pool import validate_task_pool_artifacts


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
    claim_config_digest: str
    requested_claims: tuple[str, ...] = (
        "task_pool_coverage",
        "benchmark_selection_frozen",
        "cache_completeness",
        "selector_metrics",
        "agent_result_identity",
    )
    require_complete_matrices: bool = True
    require_frozen_selections: bool = True
    require_valid_metrics: bool = True


def build_task_pool_report(
    task_pool: TaskPoolRecord,
    artifact_root: Path | None = None,
) -> ReportSection:
    validation_errors = _task_pool_validation_errors(task_pool, artifact_root)
    supported_claims = () if validation_errors else ("task_pool_counts",)
    limitations = tuple(validation_errors)
    summary = {
        "task_pool_id": task_pool.task_pool_id,
        "repository_id": task_pool.repository_id,
        "task_count": len(task_pool.task_ids),
        "check_count": len(task_pool.check_ids),
        "rejected_candidate_count": len(task_pool.rejected_candidate_ids),
        "task_records_ref": task_pool.task_records_ref,
        "check_records_ref": task_pool.check_records_ref,
        "certification_evidence_ref": task_pool.certification_evidence_ref,
        "certification_evidence_digest": task_pool.certification_evidence_digest,
        "rejection_summary_digest": task_pool.rejection_summary_digest,
        "generator_config_digest": task_pool.generator_config_digest,
        "certification_config_digest": task_pool.certification_config_digest,
    }
    return ReportSection(
        section_id="task_pool",
        heading="Task Pool",
        summary=summary,
        source_digests={
            "task_pool_digest": task_pool.task_pool_digest,
            "task_records_digest": task_pool.task_records_digest,
            "check_records_digest": task_pool.check_records_digest,
            "source_event_inventory_digest": task_pool.source_event_inventory_digest,
        },
        artifact_paths=(
            task_pool.task_records_ref,
            task_pool.check_records_ref,
            task_pool.certification_evidence_ref,
        ),
        supported_claims=supported_claims,
        unsupported_claims=tuple(f"task_pool_counts: {error}" for error in validation_errors),
        limitations=limitations,
    )


def build_result_report(results: Sequence[ResultRecord], agents: Sequence[AgentRecord]) -> ReportSection:
    result_errors = _validation_errors("result", results, validate_result)
    agent_identity_errors = _result_agent_identity_errors(results, agents)
    measurement_errors = _result_measurement_errors(results)
    outcome_counts = Counter(result.outcome for result in results)
    terminal_counts = Counter(result.terminal_status for result in results)
    failure_label_counts = Counter(result.failure_label or "none" for result in results)
    invalid_owner_counts = Counter(result.invalid_owner or "none" for result in results)
    scoreable_state_counts = Counter(result.scoreable_state for result in results)
    scoreable_count = sum(1 for result in results if result.scoreable_state == "scoreable")
    measured_cost_results = tuple(result for result in results if not _has_unknown_usage_or_cost(result))
    total_cost = sum(_number(result.cost.get("total_cost")) for result in measured_cost_results)
    latency_seconds = [_number(result.latency.get("workspace_seconds")) for result in results if result.latency.get("workspace_seconds") is not None]
    cache_identity_digests = tuple(sorted(result.cache_identity.identity_digest for result in results))
    result_agent_ids = {result.agent_id for result in results}
    known_agent_ids = {agent.agent_id for agent in agents}
    unknown_agents = tuple(sorted(result_agent_ids - known_agent_ids))
    limitations = (*result_errors, *agent_identity_errors, *measurement_errors)
    if unknown_agents:
        limitations = (*limitations, f"results reference unknown Agents: {', '.join(unknown_agents)}")
    if not results:
        limitations = (*limitations, "result evidence is absent")
    summary = {
        "result_count": len(results),
        "agent_count": len(agents),
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "terminal_status_counts": dict(sorted(terminal_counts.items())),
        "failure_label_counts": dict(sorted(failure_label_counts.items())),
        "invalid_owner_counts": dict(sorted(invalid_owner_counts.items())),
        "scoreable_state_counts": dict(sorted(scoreable_state_counts.items())),
        "scoreable_rate": scoreable_count / len(results) if results else 0.0,
        "total_cost": total_cost,
        "cost_coverage": {
            "measured_result_count": len(measured_cost_results),
            "measured_zero_cost_count": sum(1 for result in measured_cost_results if _number(result.cost.get("total_cost")) == 0.0),
            "unknown_result_count": len(results) - len(measured_cost_results),
        },
        "latency": {
            "count": len(latency_seconds),
            "total_workspace_seconds": sum(latency_seconds),
            "mean_workspace_seconds": sum(latency_seconds) / len(latency_seconds) if latency_seconds else 0.0,
        },
        "pricing_versions": tuple(sorted({result.pricing_version for result in results})),
        "cache_coverage": {
            "result_count": len(results),
            "unique_cache_identity_count": len(set(cache_identity_digests)),
        },
    }
    supported_claims = ("agent_results_summary",) if results and not limitations else ()
    return ReportSection(
        section_id="agent_results",
        heading="Agent Results",
        summary=summary,
        source_digests={
            "result_digests": tuple(sorted(result.result_digest for result in results)),
            "cache_identity_digests": cache_identity_digests,
            "agent_manifest_digests": tuple(sorted(agent.agent_manifest_digest for agent in agents)),
        },
        supported_claims=supported_claims,
        unsupported_claims=limitations,
        limitations=limitations,
    )


def build_selector_report(
    selections: Sequence[BenchmarkSelectionRecord],
    cell_sets: Sequence[EvaluationCellSet],
    result_matrices: Sequence[ResultMatrix],
    metrics: Sequence[MetricRecord],
) -> ReportSection:
    selection_errors = _validation_errors("selection", selections, validate_benchmark_selection)
    cell_set_errors = _validation_errors("cell_set", cell_sets, validate_evaluation_cell_set)
    matrix_errors = _validation_errors("matrix", result_matrices, validate_result_matrix)
    metric_errors = _validation_errors("metric", metrics, validate_metric)
    trace_errors = _selector_trace_errors(selections, cell_sets, result_matrices, metrics)
    abstention_errors = _selector_abstention_errors(cell_sets, result_matrices, metrics)
    scoreability_errors = _matrix_scoreability_errors(result_matrices)
    metric_completeness_errors = _metric_completeness_errors(metrics)
    exposure_errors = _selection_exposure_errors(selections)
    cell_sets_by_selection = _group_by(cell_sets, "selection_id")
    matrix_by_selection = _group_by(result_matrices, "selection_id")
    metrics_by_selection = _group_by(metrics, "selection_id")
    origins = sorted({selection.origin_id for selection in selections} | {metric.origin_id for metric in metrics})
    selection_rows = []
    for selection in selections:
        selection_cell_sets = cell_sets_by_selection.get(selection.selection_id, ())
        matrices = matrix_by_selection.get(selection.selection_id, ())
        selection_metrics = metrics_by_selection.get(selection.selection_id, ())
        matrix_rows = tuple(
            {
                "matrix_id": matrix.matrix_id,
                "matrix_role": matrix.matrix_role,
                "matrix_digest": matrix.matrix_digest,
                "agent_ids": matrix.agent_ids,
                "task_check_refs": tuple(_ref_dict(ref) for ref in matrix.task_check_refs),
                "join_policy_digest": matrix.join_policy_digest,
                "denominator_policy_digest": matrix.denominator_policy_digest,
                "scoreable_state": matrix.scoreable_state,
                "abstention_reason": matrix.abstention_reason,
                "cell_states": dict(sorted(Counter(cell.cell_state for cell in matrix.cells).items())),
                "result_digests": tuple(sorted(cell.result_digest for cell in matrix.cells if cell.result_digest)),
            }
            for matrix in sorted(matrices, key=lambda item: (item.matrix_role, item.matrix_id))
        )
        metric_rows = tuple(
            {
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
            for metric in sorted(selection_metrics, key=lambda item: (item.metric_name, item.metric_id))
        )
        selection_rows.append(
            {
                "selection_id": selection.selection_id,
                "origin_id": selection.origin_id,
                "selector_id": selection.selector_id,
                "budget_digest": selection.budget_digest,
                "exposure_state": selection.exposure_state,
                "selected_task_check_count": len(selection.selected_task_check_refs),
                "selected_task_check_refs": tuple(_ref_dict(ref) for ref in selection.selected_task_check_refs),
                "selected_weights": dict(selection.selected_weights),
                "cell_set_digests": tuple(sorted(cell_set.cell_set_digest for cell_set in selection_cell_sets)),
                "cell_set_abstention_reasons": tuple(sorted(reason for cell_set in selection_cell_sets if (reason := cell_set.abstention_reason))),
                "agent_ids": tuple(sorted({agent_id for matrix in matrices for agent_id in matrix.agent_ids})),
                "matrices": matrix_rows,
                "metrics": metric_rows,
                "matrix_roles": tuple(sorted(matrix.matrix_role for matrix in matrices)),
                "matrix_scoreable_states": tuple(sorted(matrix.scoreable_state for matrix in matrices)),
                "abstention_reasons": tuple(sorted(reason for matrix in matrices if (reason := matrix.abstention_reason))),
                "metric_names": tuple(sorted(metric.metric_name for metric in selection_metrics)),
                "metric_digests": tuple(sorted(metric.metric_digest for metric in selection_metrics)),
            }
        )
    limitations = (
        *selection_errors,
        *cell_set_errors,
        *matrix_errors,
        *metric_errors,
        *trace_errors,
        *abstention_errors,
        *scoreability_errors,
        *metric_completeness_errors,
        *exposure_errors,
    )
    has_selector_evidence = bool(selections) and bool(cell_sets) and bool(result_matrices) and bool(metrics)
    supported_claims = ("selector_performance_summary",) if has_selector_evidence and not limitations else ()
    if not has_selector_evidence:
        limitations = (*limitations, "selector performance evidence is absent or incomplete")
    return ReportSection(
        section_id="selector_performance",
        heading="Selector Performance",
        summary={
            "selection_count": len(selections),
            "origin_ids": tuple(origins),
            "cell_set_count": len(cell_sets),
            "result_matrix_count": len(result_matrices),
            "metric_count": len(metrics),
            "metrics_by_name": dict(sorted(Counter(metric.metric_name for metric in metrics).items())),
            "selections": tuple(selection_rows),
        },
        source_digests={
            "selection_digests": tuple(sorted(selection.selection_digest for selection in selections)),
            "cell_set_digests": tuple(sorted(cell_set.cell_set_digest for cell_set in cell_sets)),
            "matrix_digests": tuple(sorted(matrix.matrix_digest for matrix in result_matrices)),
            "metric_digests": tuple(sorted(metric.metric_digest for metric in metrics)),
        },
        supported_claims=supported_claims,
        unsupported_claims=limitations,
        limitations=limitations,
    )


def build_claim_boundary(
    task_pool: TaskPoolRecord,
    selections: Sequence[BenchmarkSelectionRecord],
    cell_sets: Sequence[EvaluationCellSet],
    result_matrices: Sequence[ResultMatrix],
    metrics: Sequence[MetricRecord],
    claim_config: ClaimConfig,
    results: Sequence[ResultRecord] = (),
    artifact_root: Path | None = None,
) -> ReportSection:
    supported: list[str] = []
    unsupported: list[str] = []
    task_pool_errors = _task_pool_validation_errors(task_pool, artifact_root)
    _claim(supported, unsupported, "task_pool_coverage", not task_pool_errors, "; ".join(task_pool_errors))
    selections_present = bool(selections)
    selection_validations = [validate_benchmark_selection(selection) for selection in selections]
    selections_valid = all(validation.ok for validation in selection_validations)
    selections_match_task_pool = all(
        selection.task_pool_id == task_pool.task_pool_id and selection.task_pool_digest == task_pool.task_pool_digest
        for selection in selections
    )
    frozen = all(selection.exposure_state == "frozen" for selection in selections)
    _claim(
        supported,
        unsupported,
        "benchmark_selection_frozen",
        selections_present
        and selections_valid
        and selections_match_task_pool
        and ((not claim_config.require_frozen_selections) or frozen),
        _claim_reason(
            "selection evidence is absent, invalid, unbound from task pool, or one or more selections are not frozen",
            _selection_claim_errors(selection_validations, selections_match_task_pool),
        ),
    )
    matrix_validations = [validate_result_matrix(matrix) for matrix in result_matrices]
    matrices_valid = all(validation.ok for validation in matrix_validations)
    matrix_scoreability_errors = _matrix_scoreability_errors(result_matrices)
    matrices_complete = not matrix_scoreability_errors
    _claim(
        supported,
        unsupported,
        "cache_completeness",
        bool(result_matrices) and matrices_valid and ((not claim_config.require_complete_matrices) or matrices_complete),
        _claim_reason(
            "result matrix evidence is absent, invalid, incomplete, or abstained",
            (*[error for validation in matrix_validations for error in validation.errors], *matrix_scoreability_errors),
        ),
    )
    metric_validations = [validate_metric(metric) for metric in metrics]
    metrics_valid = all(validation.ok for validation in metric_validations)
    metric_abstentions = [metric.abstention_reason for metric in metrics if metric.abstention_reason]
    metric_completeness_errors = _metric_completeness_errors(metrics)
    cell_set_validations = [validate_evaluation_cell_set(cell_set) for cell_set in cell_sets]
    cell_sets_valid = all(validation.ok for validation in cell_set_validations)
    cell_set_abstentions = [cell_set.abstention_reason for cell_set in cell_sets if cell_set.abstention_reason]
    trace_errors = _selector_trace_errors(selections, cell_sets, result_matrices, metrics)
    _claim(
        supported,
        unsupported,
        "selector_metrics",
        bool(metrics)
        and selections_valid
        and matrices_valid
        and matrices_complete
        and cell_sets_valid
        and selections_match_task_pool
        and ((not claim_config.require_frozen_selections) or frozen)
        and not trace_errors
        and not cell_set_abstentions
        and not metric_completeness_errors
        and ((not claim_config.require_valid_metrics) or (metrics_valid and not metric_abstentions)),
        _claim_reason(
            "metric evidence is absent, invalid, carries abstention reasons, or is not traceable",
            (
                *trace_errors,
                *_selection_claim_errors(selection_validations, selections_match_task_pool),
                *(("selection is not frozen",) if not frozen else ()),
                *[error for validation in matrix_validations for error in validation.errors],
                *matrix_scoreability_errors,
                *[error for validation in cell_set_validations for error in validation.errors],
                *[f"evaluation cell set abstained: {reason}" for reason in cell_set_abstentions],
                *metric_completeness_errors,
                *_selector_abstention_errors(cell_sets, result_matrices, metrics),
            ),
        ),
    )
    identity_errors = _result_identity_trace_errors(result_matrices, results)
    result_validations = [validate_result(result) for result in results]
    results_valid = all(validation.ok for validation in result_validations)
    has_identity_evidence = bool(results) and any(_cell_binds_result(cell) for matrix in result_matrices for cell in matrix.cells)
    _claim(
        supported,
        unsupported,
        "agent_result_identity",
        has_identity_evidence and matrices_valid and results_valid and not identity_errors,
        _claim_reason(
            "result identity evidence is absent, invalid, or not traceable",
            (*identity_errors, *[error for validation in result_validations for error in validation.errors]),
        ),
    )
    requested = set(claim_config.requested_claims)
    supported_tuple = tuple(claim for claim in supported if claim in requested)
    unsupported_tuple = tuple(claim for claim in unsupported if claim.split(":", 1)[0] in requested)
    return ReportSection(
        section_id="claim_boundary",
        heading="Claim Boundary",
        summary={
            "claim_config_digest": claim_config.claim_config_digest,
            "requested_claims": claim_config.requested_claims,
            "supported_count": len(supported_tuple),
            "unsupported_count": len(unsupported_tuple),
            "abstention_count": len(metric_abstentions) + sum(1 for matrix in result_matrices if matrix.abstention_reason),
            "selection_count": len(selections),
            "matrix_count": len(result_matrices),
            "metric_count": len(metrics),
        },
        source_digests={
            "task_pool_digest": task_pool.task_pool_digest,
            "selection_digests": tuple(sorted(selection.selection_digest for selection in selections)),
            "cell_set_digests": tuple(sorted(cell_set.cell_set_digest for cell_set in cell_sets)),
            "matrix_digests": tuple(sorted(matrix.matrix_digest for matrix in result_matrices)),
            "metric_digests": tuple(sorted(metric.metric_digest for metric in metrics)),
            "result_digests": tuple(sorted(result.result_digest for result in results)),
        },
        artifact_paths=(
            task_pool.task_records_ref,
            task_pool.check_records_ref,
            task_pool.certification_evidence_ref,
        ),
        supported_claims=supported_tuple,
        unsupported_claims=unsupported_tuple,
        limitations=unsupported_tuple,
    )


def write_report(sections: Sequence[ReportSection], output_path: Path, artifact_root: Path | None = None) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    root = artifact_root or output_path.parent
    sanitized_sections = tuple(_sanitize_report_section(section, root) for section in sections)
    if output_path.suffix == ".json":
        output_path.write_text(canonical_json(tuple(_section_data(section) for section in sanitized_sections)) + "\n", encoding="utf-8")
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
            lines.extend(["### Supported Claims", "", *[f"- {claim}" for claim in section.supported_claims], ""])
        if section.unsupported_claims:
            lines.extend(["### Unsupported Claims", "", *[f"- {claim}" for claim in section.unsupported_claims], ""])
        if section.artifact_paths:
            lines.extend(["### Artifact Paths", "", *[f"- {artifact_path}" for artifact_path in section.artifact_paths], ""])
        if section.limitations:
            lines.extend(["### Limitations", "", *[f"- {limitation}" for limitation in section.limitations], ""])
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _sanitize_report_section(section: ReportSection, artifact_root: Path) -> ReportSection:
    return replace(
        section,
        summary=_sanitize_artifact_refs(section.summary, artifact_root),
        artifact_paths=tuple(_sanitize_artifact_path(artifact_path, artifact_root) for artifact_path in section.artifact_paths),
    )


def _sanitize_artifact_refs(value: Any, artifact_root: Path) -> Any:
    if isinstance(value, str):
        return _sanitize_artifact_path(value, artifact_root)
    if isinstance(value, Mapping):
        return {key: _sanitize_artifact_refs(item, artifact_root) for key, item in value.items()}
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
    if task_pool.task_pool_digest != canonical_digest(task_pool, exclude_self_digest=True):
        errors.append("task_pool_digest does not match canonical task pool")
    if not task_pool.task_ids:
        errors.append("task_ids are empty")
    if not task_pool.check_ids:
        errors.append("check_ids are empty")
    for field in (
        "task_records_ref",
        "check_records_ref",
        "certification_evidence_ref",
        "task_records_digest",
        "check_records_digest",
        "rejection_summary_digest",
        "source_event_inventory_digest",
        "generator_config_digest",
        "certification_config_digest",
    ):
        if not getattr(task_pool, field):
            errors.append(f"{field} is missing")
    if not task_pool.certification_evidence_digest:
        errors.append("certification_evidence_digest is missing")
    errors.extend(_task_pool_artifact_errors(task_pool, artifact_root))
    return tuple(errors)


def _task_pool_artifact_errors(
    task_pool: TaskPoolRecord,
    artifact_root: Path | None,
) -> tuple[str, ...]:
    errors: list[str] = []
    root = artifact_root or Path.cwd()
    tasks = _load_task_pool_records(
        task_pool.task_records_ref,
        root,
        TaskRecord,
        "task records",
        errors,
    )
    checks = _load_task_pool_records(
        task_pool.check_records_ref,
        root,
        CheckRecord,
        "check records",
        errors,
    )
    evidence = _load_certification_evidence(
        task_pool.certification_evidence_ref,
        root,
        errors,
    )

    if tasks is not None and checks is not None and evidence is not None:
        validation = validate_task_pool_artifacts(
            task_pool,
            tasks,
            checks,
            evidence,
        )
        errors.extend(validation.errors)
    return tuple(errors)


def _load_task_pool_records(
    ref: str,
    root: Path,
    record_type: type,
    label: str,
    errors: list[str],
) -> tuple[Any, ...] | None:
    if not ref:
        return None
    try:
        return tuple(load_jsonl_records(_artifact_ref_path(ref, root), record_type))
    except (KeyError, OSError, TypeError, ValueError):
        errors.append(f"{label} are unavailable or invalid")
        return None


def _load_certification_evidence(
    ref: str,
    root: Path,
    errors: list[str],
) -> tuple[Mapping[str, Any], ...] | None:
    if not ref:
        return None
    try:
        records: list[Mapping[str, Any]] = []
        with _artifact_ref_path(ref, root).open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                value = json.loads(line, parse_constant=_reject_json_constant)
                if not isinstance(value, Mapping):
                    raise ValueError("certification evidence must contain objects")
                records.append(value)
        return tuple(records)
    except (OSError, TypeError, ValueError):
        errors.append("certification evidence is unavailable or invalid")
        return None


def _artifact_ref_path(ref: str, root: Path) -> Path:
    normalized = ref[5:] if ref.startswith("path:") else ref
    path = Path(normalized)
    return path if path.is_absolute() else root / path


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _validation_errors(label: str, records: Sequence[Any], validate: Any) -> tuple[str, ...]:
    errors: list[str] = []
    for record in records:
        validation = validate(record)
        if not validation.ok:
            record_id = getattr(record, f"{label}_id", getattr(record, "result_id", "record"))
            errors.append(f"{label} {record_id}: {'; '.join(validation.errors)}")
    return tuple(errors)


def _group_by(records: Sequence[Any], field: str) -> Mapping[str, tuple[Any, ...]]:
    grouped: dict[str, list[Any]] = {}
    for record in records:
        grouped.setdefault(getattr(record, field), []).append(record)
    return {key: tuple(value) for key, value in grouped.items()}


def _ref_dict(ref: Any) -> Mapping[str, str]:
    return {"task_id": ref.task_id, "check_id": ref.check_id}


def _claim(supported: list[str], unsupported: list[str], claim: str, ok: bool, reason: str) -> None:
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
    errors: list[str] = []
    selection_by_id = {selection.selection_id: selection for selection in selections}
    cell_sets_by_selection = _group_by(cell_sets, "selection_id")
    matrices_by_selection = _group_by(result_matrices, "selection_id")
    metrics_by_selection = _group_by(metrics, "selection_id")
    matrix_by_digest = {matrix.matrix_digest: matrix for matrix in result_matrices}
    cell_set_by_digest = {cell_set.cell_set_digest: cell_set for cell_set in cell_sets}
    for cell_set in cell_sets:
        selection = selection_by_id.get(cell_set.selection_id)
        if selection is None:
            errors.append(f"cell_set {cell_set.cell_set_id} references missing selection {cell_set.selection_id}")
            continue
        if cell_set.origin_id != selection.origin_id:
            errors.append(f"cell_set {cell_set.cell_set_id} origin does not match selection {selection.selection_id}")
        if cell_set.selected_task_check_refs != selection.selected_task_check_refs:
            errors.append(f"cell_set {cell_set.cell_set_id} selected refs do not match selection {selection.selection_id}")
    for matrix in result_matrices:
        selection = selection_by_id.get(matrix.selection_id)
        if selection is None:
            errors.append(f"matrix {matrix.matrix_id} references missing selection {matrix.selection_id}")
            continue
        if matrix.origin_id != selection.origin_id:
            errors.append(f"matrix {matrix.matrix_id} origin does not match selection {selection.selection_id}")
        if matrix.matrix_role == "selected" and matrix.task_check_refs != selection.selected_task_check_refs:
            errors.append(f"matrix {matrix.matrix_id} selected denominator does not match selection {selection.selection_id}")
    for selection in selections:
        selection_cell_sets = cell_sets_by_selection.get(selection.selection_id, ())
        selection_matrices = matrices_by_selection.get(selection.selection_id, ())
        if not selection_cell_sets:
            errors.append(f"selection {selection.selection_id} has no evaluation cell set")
        roles = Counter(matrix.matrix_role for matrix in selection_matrices)
        if roles.get("selected", 0) == 0:
            errors.append(f"selection {selection.selection_id} has no selected result matrix")
        if roles.get("future_holdout", 0) == 0:
            errors.append(f"selection {selection.selection_id} has no future result matrix")
        if not metrics_by_selection.get(selection.selection_id):
            errors.append(f"selection {selection.selection_id} has no metric evidence")
        agent_sets = {matrix.agent_ids for matrix in selection_matrices}
        if len(agent_sets) > 1:
            errors.append(f"selection {selection.selection_id} has mismatched matrix Agent sets")
        for matrix in selection_matrices:
            for cell_set in selection_cell_sets:
                future_refs = cell_set.future_task_check_refs
                if matrix.matrix_role == "future_holdout" and matrix.task_check_refs != future_refs:
                    errors.append(f"matrix {matrix.matrix_id} future denominator does not match cell set {cell_set.cell_set_id}")
    for metric in metrics:
        selection = selection_by_id.get(metric.selection_id)
        if selection is None:
            errors.append(f"metric {metric.metric_id} references missing selection {metric.selection_id}")
            continue
        cell_set = cell_set_by_digest.get(metric.evaluation_cell_set_digest)
        selected_matrix = matrix_by_digest.get(metric.selected_matrix_digest)
        future_matrix = matrix_by_digest.get(metric.future_matrix_digest)
        if cell_set is None:
            errors.append(f"metric {metric.metric_id} evaluation_cell_set_digest is not supplied")
        if selected_matrix is None:
            errors.append(f"metric {metric.metric_id} selected_matrix_digest is not supplied")
        if future_matrix is None:
            errors.append(f"metric {metric.metric_id} future_matrix_digest is not supplied")
        if cell_set is not None and (cell_set.selection_id != selection.selection_id or cell_set.origin_id != selection.origin_id):
            errors.append(f"metric {metric.metric_id} cell set does not match selection {selection.selection_id}")
        if selected_matrix is not None:
            if selected_matrix.matrix_role != "selected":
                errors.append(f"metric {metric.metric_id} selected matrix has wrong role")
            if selected_matrix.selection_id != selection.selection_id or selected_matrix.origin_id != selection.origin_id:
                errors.append(f"metric {metric.metric_id} selected matrix does not match selection {selection.selection_id}")
            if selected_matrix.join_policy_digest != metric.join_policy_digest:
                errors.append(f"metric {metric.metric_id} join policy does not match selected matrix")
            if selected_matrix.denominator_policy_digest != metric.denominator_policy_digest:
                errors.append(f"metric {metric.metric_id} denominator policy does not match selected matrix")
        if future_matrix is not None:
            if future_matrix.matrix_role != "future_holdout":
                errors.append(f"metric {metric.metric_id} future matrix has wrong role")
            if future_matrix.selection_id != selection.selection_id or future_matrix.origin_id != selection.origin_id:
                errors.append(f"metric {metric.metric_id} future matrix does not match selection {selection.selection_id}")
            if future_matrix.join_policy_digest != metric.join_policy_digest:
                errors.append(f"metric {metric.metric_id} join policy does not match future matrix")
            if future_matrix.denominator_policy_digest != metric.denominator_policy_digest:
                errors.append(f"metric {metric.metric_id} denominator policy does not match future matrix")
        if selected_matrix is not None and future_matrix is not None and selected_matrix.agent_ids != future_matrix.agent_ids:
            errors.append(f"metric {metric.metric_id} selected/future Agent sets do not match")
        if cell_set is not None and selected_matrix is not None and not _matrix_cells_match_cell_set(selected_matrix, cell_set):
            errors.append(f"metric {metric.metric_id} selected matrix cells do not match evaluation cell set")
        if cell_set is not None and future_matrix is not None and not _matrix_cells_match_cell_set(future_matrix, cell_set):
            errors.append(f"metric {metric.metric_id} future matrix cells do not match evaluation cell set")
        if metric.budget_digest != selection.budget_digest:
            errors.append(f"metric {metric.metric_id} budget digest does not match selection {selection.selection_id}")
        if metric.origin_id != selection.origin_id:
            errors.append(f"metric {metric.metric_id} origin does not match selection {selection.selection_id}")
        if selected_matrix is None or future_matrix is None:
            continue
        if (
            metric.metric_scope != "aggregate"
            or metric.aggregation_level != "all_agents"
            or metric.agent_id is not None
            or metric.agent_pair is not None
            or metric.stratum_ref is not None
        ):
            errors.append(f"metric {metric.metric_id} is not a recomputable aggregate all-Agents metric")
            continue
        try:
            expected_values = compute_selection_metric_values(
                selection,
                selected_matrix,
                future_matrix,
            )
        except (OverflowError, TypeError, ValueError, ZeroDivisionError) as exc:
            errors.append(f"metric {metric.metric_id} cannot be recomputed: {exc}")
            continue
        expected_value = expected_values.get(metric.metric_name)
        if expected_value is None:
            errors.append(f"metric {metric.metric_id} has an unsupported metric name: {metric.metric_name}")
        elif metric.metric_value != expected_value:
            errors.append(
                f"metric {metric.metric_id} value {metric.metric_value} does not match recomputed value {expected_value}"
            )
    return tuple(errors)


def _selector_abstention_errors(
    cell_sets: Sequence[EvaluationCellSet],
    result_matrices: Sequence[ResultMatrix],
    metrics: Sequence[MetricRecord],
) -> tuple[str, ...]:
    errors: list[str] = []
    errors.extend(f"cell_set {cell_set.cell_set_id} abstained: {cell_set.abstention_reason}" for cell_set in cell_sets if cell_set.abstention_reason)
    errors.extend(f"matrix {matrix.matrix_id} abstained: {matrix.abstention_reason}" for matrix in result_matrices if matrix.abstention_reason)
    errors.extend(f"metric {metric.metric_id} abstained: {metric.abstention_reason}" for metric in metrics if metric.abstention_reason)
    return tuple(errors)


def _matrix_scoreability_errors(result_matrices: Sequence[ResultMatrix]) -> tuple[str, ...]:
    errors: list[str] = []
    for matrix in result_matrices:
        if matrix.scoreable_state != "complete":
            errors.append(f"matrix {matrix.matrix_id} scoreable_state is {matrix.scoreable_state}")
        non_result_counts = Counter(cell.cell_state for cell in matrix.cells if cell.cell_state != "result")
        if non_result_counts:
            counts = ", ".join(f"{state}={count}" for state, count in sorted(non_result_counts.items()))
            errors.append(f"matrix {matrix.matrix_id} contains non-result cells: {counts}")
    return tuple(errors)


def _metric_completeness_errors(metrics: Sequence[MetricRecord]) -> tuple[str, ...]:
    return tuple(
        f"metric {metric.metric_id} completeness_state is {metric.completeness_state}"
        for metric in metrics
        if metric.completeness_state != "complete"
    )


def _selection_exposure_errors(selections: Sequence[BenchmarkSelectionRecord]) -> tuple[str, ...]:
    return tuple(
        f"selection {selection.selection_id} exposure_state is {selection.exposure_state}"
        for selection in selections
        if selection.exposure_state != "frozen"
    )


def _result_agent_identity_errors(results: Sequence[ResultRecord], agents: Sequence[AgentRecord]) -> tuple[str, ...]:
    agent_by_id = {agent.agent_id: agent for agent in agents}
    errors: list[str] = []
    for result in results:
        agent = agent_by_id.get(result.agent_id)
        if agent is None:
            continue
        identity = result.cache_identity
        if (
            identity.agent_manifest_digest != agent.agent_manifest_digest
            or identity.model_snapshot_id != agent.model_snapshot_id
            or identity.harness_digest != agent.harness_digest
            or identity.repository_instruction_digest != agent.repository_instruction_digest
            or identity.prompt_digest != agent.prompt_digest
            or identity.tools_digest != agent.tools_digest
            or identity.retrieval_digest != agent.retrieval_digest
            or identity.skills_digest != agent.skills_digest
            or identity.network_policy_digest != agent.network_policy_digest
            or identity.adapter_digest != agent.adapter_digest
        ):
            errors.append(f"result {result.result_id} cache identity does not match Agent {agent.agent_id}")
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
            errors.append(f"result {result.result_id} latency.workspace_seconds is missing")
        elif not _is_number(result.latency["workspace_seconds"]):
            errors.append(f"result {result.result_id} latency.workspace_seconds is non-numeric")
    return tuple(errors)


def _has_unknown_usage_or_cost(result: ResultRecord) -> bool:
    return result.cost.get("total_cost") is None


def _selection_claim_errors(selection_validations: Sequence[Any], selections_match_task_pool: bool) -> tuple[str, ...]:
    errors = [error for validation in selection_validations for error in validation.errors]
    if not selections_match_task_pool:
        errors.append("selection task_pool binding does not match report task_pool")
    return tuple(errors)


def _matrix_cells_match_cell_set(matrix: ResultMatrix, cell_set: EvaluationCellSet) -> bool:
    expected_refs = cell_set.selected_task_check_refs if matrix.matrix_role == "selected" else cell_set.future_task_check_refs
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


def _result_identity_trace_errors(result_matrices: Sequence[ResultMatrix], results: Sequence[ResultRecord]) -> tuple[str, ...]:
    if not results:
        return ()
    result_by_digest = {result.result_digest: result for result in results}
    errors: list[str] = []
    for matrix in result_matrices:
        for cell in matrix.cells:
            if not _cell_binds_result(cell):
                continue
            if cell.result_digest is None:
                errors.append(f"matrix {matrix.matrix_id} cell binds result_id without result_digest")
                continue
            if cell.result_id is None:
                errors.append(f"matrix {matrix.matrix_id} cell binds result_digest without result_id")
                continue
            result = result_by_digest.get(cell.result_digest)
            if result is None:
                errors.append(f"matrix {matrix.matrix_id} cell references missing result digest {cell.result_digest}")
                continue
            if result.result_id != cell.result_id:
                errors.append(f"matrix {matrix.matrix_id} cell result_id does not match result digest {cell.result_digest}")
            if result.agent_id != cell.agent_id or result.task_id != cell.task_id or result.check_id != cell.check_id:
                errors.append(f"matrix {matrix.matrix_id} cell Agent/Task/Check does not match result {result.result_id}")
            if result.cache_identity.identity_digest != cell.required_identity_digest:
                errors.append(f"matrix {matrix.matrix_id} cell identity digest does not match result {result.result_id}")
    return tuple(errors)


def _cell_binds_result(cell: ResultCellRef) -> bool:
    return cell.result_id is not None or cell.result_digest is not None


def _number(value: Any) -> float:
    return float(value) if _is_number(value) else 0.0


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)
