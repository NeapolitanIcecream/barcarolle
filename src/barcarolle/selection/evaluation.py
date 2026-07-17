"""Selection evaluation matrices, metrics, and metric-based selector choice."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import fsum, isfinite
from typing import Mapping, Sequence

from barcarolle.records import (
    BenchmarkSelectionRecord,
    EvaluationCellSet,
    MetricRecord,
    ResultMatrix,
    RollingOriginRecord,
    SelectorRecord,
    TaskCheckRef,
    canonical_digest,
    record_with_digest,
    task_check_ref_key,
    validate_benchmark_selection,
    validate_evaluation_cell_set,
    validate_metric,
    validate_result_matrix,
    validate_selector,
)

from .algorithms import (
    _coverage_parameters,
    _random_parameters,
    _selector_record,
    ensure_selector_executable,
)
from .origin import _now


@dataclass(frozen=True)
class MetricConfig:
    metric_config_digest: str
    budget_digest: str | None = None


def evaluate_selection(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    evaluation_cells: EvaluationCellSet,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
    metric_config: MetricConfig,
) -> Sequence[MetricRecord]:
    record_error = _record_validation_error(selection, origin, evaluation_cells, selected_matrix, future_matrix)
    if not record_error and metric_config.budget_digest not in {None, selection.budget_digest}:
        record_error = "metric_budget_mismatch"
    if record_error:
        return (
            _metric_record(
                selection,
                origin,
                evaluation_cells,
                selected_matrix,
                future_matrix,
                metric_config,
                metric_scope="aggregate",
                metric_name="selection_evaluation_invalid",
                metric_value=0.0,
                completeness_state="invalid",
                abstention_reason=record_error,
            ),
        )
    alignment_error = _matrix_alignment_error(selection, origin, evaluation_cells, selected_matrix, future_matrix)
    if alignment_error:
        return (
            _metric_record(
                selection,
                origin,
                evaluation_cells,
                selected_matrix,
                future_matrix,
                metric_config,
                metric_scope="aggregate",
                metric_name="selection_evaluation_invalid",
                metric_value=0.0,
                completeness_state="invalid",
                abstention_reason=alignment_error,
            ),
        )
    completeness_error = _matrix_completeness_error(selected_matrix, future_matrix)
    if completeness_error:
        return (
            _metric_record(
                selection,
                origin,
                evaluation_cells,
                selected_matrix,
                future_matrix,
                metric_config,
                metric_scope="aggregate",
                metric_name="selection_evaluation_invalid",
                metric_value=0.0,
                completeness_state="abstained",
                abstention_reason=completeness_error,
            ),
        )
    try:
        metric_values = compute_selection_metric_values(
            selection,
            selected_matrix,
            future_matrix,
        )
    except ValueError as exc:
        return (
            _metric_record(
                selection,
                origin,
                evaluation_cells,
                selected_matrix,
                future_matrix,
                metric_config,
                metric_scope="aggregate",
                metric_name="selection_evaluation_invalid",
                metric_value=0.0,
                completeness_state="invalid",
                abstention_reason=str(exc),
            ),
        )
    completeness_state = _combined_completeness_state(selected_matrix, future_matrix)
    return tuple(
        _metric_record(
            selection,
            origin,
            evaluation_cells,
            selected_matrix,
            future_matrix,
            metric_config,
            metric_scope="aggregate",
            metric_name=metric_name,
            metric_value=metric_value,
            completeness_state=completeness_state,
            abstention_reason=future_matrix.abstention_reason,
        )
        for metric_name, metric_value in metric_values.items()
    )


def compute_selection_metric_values(
    selection: BenchmarkSelectionRecord,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
) -> Mapping[str, float]:
    """Derive every current aggregate metric from supplied Result matrices."""
    selected_rates = _pass_rates(selected_matrix, selection.selected_weights)
    future_rates = _pass_rates(future_matrix)
    return {
        "future_pass_rate_mae": _mean_absolute_error(selected_rates, future_rates),
        "future_coverage": _coverage(future_matrix),
        "future_invalid_rate": _invalid_rate(future_matrix),
        "pairwise_gap_mae": _pairwise_gap_mae(selected_rates, future_rates),
        "rank_agreement": _rank_agreement(selected_rates, future_rates),
        "recommendation_regret": _recommendation_regret(selected_rates, future_rates),
    }


def choose_selector_by_mean_mae(
    registered_selectors: Sequence[SelectorRecord],
    mae_by_origin: Sequence[Mapping[str, float]],
    fallback_selector_id: str,
) -> SelectorRecord:
    if not registered_selectors:
        raise ValueError("registered_selectors must not be empty")
    for selector in registered_selectors:
        validation = validate_selector(selector)
        if not validation.ok:
            raise ValueError(f"registered selector is invalid: {', '.join(validation.errors)}")
        ensure_selector_executable(selector)
    selector_ids = [selector.selector_id for selector in registered_selectors]
    if len(selector_ids) != len(set(selector_ids)):
        raise ValueError("registered selector IDs must be unique")
    selector_by_id = {selector.selector_id: selector for selector in registered_selectors}
    if fallback_selector_id not in selector_by_id:
        raise ValueError("fallback_selector_id is not registered")
    if not mae_by_origin:
        return selector_by_id[fallback_selector_id]
    expected_selector_ids = set(selector_by_id)
    totals = {selector_id: [] for selector_id in selector_by_id}
    for row in mae_by_origin:
        if not isinstance(row, Mapping):
            raise ValueError("each MAE row must map selector IDs to MAE values")
        row_selector_ids = set(row)
        if row_selector_ids != expected_selector_ids:
            missing = sorted(expected_selector_ids - row_selector_ids)
            extra = sorted(row_selector_ids - expected_selector_ids)
            details = []
            if missing:
                details.append(f"missing {', '.join(missing)}")
            if extra:
                details.append(f"unknown {', '.join(map(str, sorted(extra, key=str)))}")
            raise ValueError(f"each MAE row must cover every registered selector: {'; '.join(details)}")
        for selector_id, value in row.items():
            totals[selector_id].append(_normalized_mae(value))
    means = {
        selector_id: fsum(values) / len(values)
        for selector_id, values in totals.items()
    }
    best_selector_id = min(means, key=lambda selector_id: (means[selector_id], selector_id))
    return selector_by_id[best_selector_id]


def choose_selector_from_metrics(
    registered_selectors: Sequence[SelectorRecord],
    selections: Sequence[BenchmarkSelectionRecord],
    mae_metrics: Sequence[MetricRecord],
    future_matrices: Sequence[ResultMatrix],
    fallback_selector_id: str,
) -> SelectorRecord:
    fallback = choose_selector_by_mean_mae(
        registered_selectors,
        (),
        fallback_selector_id,
    )
    mae_by_origin = _paired_mae_by_origin(
        {selector.selector_id for selector in registered_selectors},
        selections,
        mae_metrics,
        future_matrices,
    )
    if not mae_by_origin:
        return fallback
    return choose_selector_by_mean_mae(
        registered_selectors,
        mae_by_origin,
        fallback_selector_id,
    )


def fit_rule_mixture_from_metrics(
    expert_selectors: Sequence[SelectorRecord],
    selections: Sequence[BenchmarkSelectionRecord],
    mae_metrics: Sequence[MetricRecord],
    future_matrices: Sequence[ResultMatrix],
) -> SelectorRecord:
    experts = _validated_rule_mixture_experts(expert_selectors)
    mae_by_origin = _paired_mae_by_origin(
        {selector.selector_id for selector in expert_selectors},
        selections,
        mae_metrics,
        future_matrices,
    )
    if not mae_by_origin:
        raise ValueError("paired MAE evidence is required to fit a rule mixture")

    ordered_families = ("coverage", "random", "recency")
    expert_weights = {
        family: 1.0
        - fsum(row[experts[family].selector_id] for row in mae_by_origin) / len(mae_by_origin)
        for family in ordered_families
    }
    if all(weight == 0.0 for weight in expert_weights.values()):
        expert_weights = {family: 1.0 for family in ordered_families}

    training_source_digests = (
        canonical_digest(
            {
                "expert_selectors": tuple(
                    canonical_digest(experts[family]) for family in ordered_families
                )
            }
        ),
        canonical_digest(
            {"selections": tuple(sorted(selection.selection_digest for selection in selections))}
        ),
        canonical_digest(
            {"mae_metrics": tuple(sorted(metric.metric_digest for metric in mae_metrics))}
        ),
    )
    allowed_feature_classes = tuple(
        sorted(
            {
                feature_class
                for selector in expert_selectors
                for feature_class in selector.allowed_feature_classes
            }
        )
    )
    return _selector_record(
        selector_family="rule_mixture",
        selector_version="1",
        training_source_digests=training_source_digests,
        allowed_feature_classes=allowed_feature_classes,
        parameters={
            "expert_weights": expert_weights,
            "random_seed": _random_parameters(experts["random"].parameters),
            "group_by_ref_key": dict(_coverage_parameters(experts["coverage"].parameters)),
        },
    )


def _validated_rule_mixture_experts(
    expert_selectors: Sequence[SelectorRecord],
) -> Mapping[str, SelectorRecord]:
    expected_families = {"coverage", "random", "recency"}
    families = [selector.selector_family for selector in expert_selectors]
    if len(expert_selectors) != len(expected_families) or set(families) != expected_families:
        raise ValueError(
            "expert_selectors must contain exactly one coverage, random, and recency selector"
        )
    selector_ids = [selector.selector_id for selector in expert_selectors]
    if len(selector_ids) != len(set(selector_ids)):
        raise ValueError("expert selector IDs must be unique")
    for selector in expert_selectors:
        validation = validate_selector(selector)
        if not validation.ok:
            raise ValueError(f"expert selector is invalid: {', '.join(validation.errors)}")
        ensure_selector_executable(selector)
    return {selector.selector_family: selector for selector in expert_selectors}


def _paired_mae_by_origin(
    registered_selector_ids: set[str],
    selections: Sequence[BenchmarkSelectionRecord],
    mae_metrics: Sequence[MetricRecord],
    future_matrices: Sequence[ResultMatrix],
) -> tuple[Mapping[str, float], ...]:
    if not selections and not mae_metrics and not future_matrices:
        return ()
    if not selections or not mae_metrics or not future_matrices:
        raise ValueError(
            "selections, MAE metrics, and future matrices must all be provided"
        )

    selections_by_id: dict[str, BenchmarkSelectionRecord] = {}
    selections_by_origin: dict[str, dict[str, BenchmarkSelectionRecord]] = {}
    selection_input_by_origin: dict[str, str] = {}
    task_pool_identities: set[tuple[str, str]] = set()
    budget_digests: set[str] = set()
    for selection in selections:
        validation = validate_benchmark_selection(selection)
        if not validation.ok:
            raise ValueError(f"selection is invalid: {', '.join(validation.errors)}")
        if selection.exposure_state != "frozen":
            raise ValueError("selections must be frozen")
        if selection.selector_id not in registered_selector_ids:
            raise ValueError(f"selection uses unregistered selector: {selection.selector_id}")
        if selection.selection_id in selections_by_id:
            raise ValueError(f"duplicate selection ID: {selection.selection_id}")
        selection_input_digest = selection_input_by_origin.setdefault(
            selection.origin_id,
            selection.selection_input_digest,
        )
        if selection.selection_input_digest != selection_input_digest:
            raise ValueError(
                f"selections for origin {selection.origin_id} must use one selection input"
            )
        origin_selections = selections_by_origin.setdefault(selection.origin_id, {})
        if selection.selector_id in origin_selections:
            raise ValueError(
                f"duplicate selection for origin {selection.origin_id} and selector {selection.selector_id}"
            )
        selections_by_id[selection.selection_id] = selection
        origin_selections[selection.selector_id] = selection
        task_pool_identities.add((selection.task_pool_id, selection.task_pool_digest))
        budget_digests.add(selection.budget_digest)

    if len(task_pool_identities) != 1:
        raise ValueError("selections must use one task pool")
    if len(budget_digests) != 1:
        raise ValueError("selections must use one budget")
    for origin_id, origin_selections in selections_by_origin.items():
        missing_selector_ids = sorted(registered_selector_ids - set(origin_selections))
        if missing_selector_ids:
            raise ValueError(
                f"origin {origin_id} is missing registered selectors: {', '.join(missing_selector_ids)}"
            )

    metrics_by_selection_id: dict[str, MetricRecord] = {}
    metric_ids: set[str] = set()
    metric_config_digests: set[str] = set()
    join_policy_digests: set[str] = set()
    denominator_policy_digests: set[str] = set()
    completeness_by_origin: dict[str, set[str]] = {}
    for metric in mae_metrics:
        validation = validate_metric(metric)
        if not validation.ok:
            raise ValueError(f"metric is invalid: {', '.join(validation.errors)}")
        if metric.metric_id in metric_ids:
            raise ValueError(f"duplicate metric ID: {metric.metric_id}")
        if metric.selection_id in metrics_by_selection_id:
            raise ValueError(f"duplicate metric for selection: {metric.selection_id}")
        selection = selections_by_id.get(metric.selection_id)
        if selection is None:
            raise ValueError(f"metric has no matching selection: {metric.selection_id}")
        if metric.origin_id != selection.origin_id:
            raise ValueError("metric origin does not match its selection")
        if metric.budget_digest != selection.budget_digest:
            raise ValueError("metric budget does not match its selection budget")
        if metric.metric_name != "future_pass_rate_mae":
            raise ValueError("metrics must be future_pass_rate_mae")
        if metric.metric_scope != "aggregate" or metric.aggregation_level != "all_agents":
            raise ValueError("future_pass_rate_mae metrics must aggregate all agents")
        if metric.completeness_state not in {"complete", "complete_with_exclusions"}:
            raise ValueError("future_pass_rate_mae metrics must be complete")
        metrics_by_selection_id[metric.selection_id] = metric
        metric_ids.add(metric.metric_id)
        metric_config_digests.add(metric.metric_config_digest)
        join_policy_digests.add(metric.join_policy_digest)
        denominator_policy_digests.add(metric.denominator_policy_digest)
        completeness_by_origin.setdefault(metric.origin_id, set()).add(
            metric.completeness_state
        )

    missing_metric_selection_ids = sorted(set(selections_by_id) - set(metrics_by_selection_id))
    if missing_metric_selection_ids:
        raise ValueError(
            "selections are missing MAE metrics: " + ", ".join(missing_metric_selection_ids)
        )

    future_matrices_by_selection_id: dict[str, ResultMatrix] = {}
    future_evidence_by_origin: dict[str, str] = {}
    for matrix in future_matrices:
        validation = validate_result_matrix(matrix)
        if not validation.ok:
            raise ValueError(f"future matrix is invalid: {', '.join(validation.errors)}")
        if matrix.matrix_role != "future_holdout":
            raise ValueError("future matrices must have the future_holdout role")
        if matrix.selection_id in future_matrices_by_selection_id:
            raise ValueError(f"duplicate future matrix for selection: {matrix.selection_id}")
        selection = selections_by_id.get(matrix.selection_id)
        if selection is None:
            raise ValueError(f"future matrix has no matching selection: {matrix.selection_id}")
        metric = metrics_by_selection_id[matrix.selection_id]
        if matrix.origin_id != selection.origin_id:
            raise ValueError("future matrix origin does not match its selection")
        if matrix.matrix_digest != metric.future_matrix_digest:
            raise ValueError("future matrix digest does not match its MAE metric")
        if matrix.join_policy_digest != metric.join_policy_digest:
            raise ValueError("future matrix join policy does not match its MAE metric")
        if matrix.denominator_policy_digest != metric.denominator_policy_digest:
            raise ValueError("future matrix denominator policy does not match its MAE metric")
        evidence_digest = _future_result_evidence_digest(matrix)
        prior_evidence_digest = future_evidence_by_origin.setdefault(
            matrix.origin_id,
            evidence_digest,
        )
        if prior_evidence_digest != evidence_digest:
            raise ValueError(
                f"future matrices for origin {matrix.origin_id} must use the same Result evidence"
            )
        future_matrices_by_selection_id[matrix.selection_id] = matrix

    missing_future_matrix_selection_ids = sorted(
        set(selections_by_id) - set(future_matrices_by_selection_id)
    )
    if missing_future_matrix_selection_ids:
        raise ValueError(
            "selections are missing future matrices: "
            + ", ".join(missing_future_matrix_selection_ids)
        )
    if len(metric_config_digests) != 1:
        raise ValueError("metrics must use one metric configuration")
    if len(join_policy_digests) != 1:
        raise ValueError("metrics must use one join policy")
    if len(denominator_policy_digests) != 1:
        raise ValueError("metrics must use one denominator policy")
    for origin_id, completeness_states in completeness_by_origin.items():
        if len(completeness_states) != 1:
            raise ValueError(f"metrics for origin {origin_id} must have one completeness state")

    return tuple(
        {
            selector_id: _normalized_mae(
                metrics_by_selection_id[selection.selection_id].metric_value
            )
            for selector_id, selection in selections_by_origin[origin_id].items()
        }
        for origin_id in sorted(selections_by_origin)
    )


def _normalized_mae(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("MAE values must be finite numbers between 0 and 1")
    try:
        normalized = float(value)
    except OverflowError as exc:
        raise ValueError("MAE values must be finite numbers between 0 and 1") from exc
    if not isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise ValueError("MAE values must be finite numbers between 0 and 1")
    return normalized


def _future_result_evidence_digest(matrix: ResultMatrix) -> str:
    return canonical_digest(
        {
            "agent_ids": matrix.agent_ids,
            "task_check_refs": matrix.task_check_refs,
            "cells": matrix.cells,
            "scoreable_state": matrix.scoreable_state,
            "abstention_reason": matrix.abstention_reason,
        }
    )


def _matrix_alignment_error(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    evaluation_cells: EvaluationCellSet,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
) -> str | None:
    if selection.origin_id != origin.origin_id or evaluation_cells.origin_id != origin.origin_id:
        return "origin_mismatch"
    if evaluation_cells.selection_id != selection.selection_id:
        return "evaluation_cell_selection_mismatch"
    if selected_matrix.matrix_role != "selected" or future_matrix.matrix_role != "future_holdout":
        return "matrix_role_mismatch"
    if selected_matrix.origin_id != origin.origin_id or future_matrix.origin_id != origin.origin_id:
        return "matrix_origin_mismatch"
    if selected_matrix.selection_id != selection.selection_id or future_matrix.selection_id != selection.selection_id:
        return "matrix_selection_mismatch"
    if selected_matrix.agent_ids != future_matrix.agent_ids:
        return "agent_set_mismatch"
    if selected_matrix.join_policy_digest != future_matrix.join_policy_digest:
        return "join_policy_mismatch"
    if selected_matrix.denominator_policy_digest != future_matrix.denominator_policy_digest:
        return "denominator_policy_mismatch"
    if selected_matrix.task_check_refs != selection.selected_task_check_refs:
        return "selected_denominator_mismatch"
    if evaluation_cells.selected_task_check_refs != selection.selected_task_check_refs:
        return "evaluation_selected_denominator_mismatch"
    if future_matrix.task_check_refs != origin.future_holdout_task_check_refs:
        return "future_denominator_mismatch"
    if evaluation_cells.future_task_check_refs != origin.future_holdout_task_check_refs:
        return "evaluation_future_denominator_mismatch"
    if not _matrix_cells_match_cell_set(selected_matrix, evaluation_cells, selection.selected_task_check_refs):
        return "selected_matrix_cell_identity_mismatch"
    if not _matrix_cells_match_cell_set(future_matrix, evaluation_cells, origin.future_holdout_task_check_refs):
        return "future_matrix_cell_identity_mismatch"
    return None


def _matrix_cells_match_cell_set(
    matrix: ResultMatrix,
    evaluation_cells: EvaluationCellSet,
    refs: Sequence[TaskCheckRef],
) -> bool:
    allowed_refs = {(ref.task_id, ref.check_id) for ref in refs}
    expected = {
        (cell.agent_id, cell.task_id, cell.check_id): (
            cell.required_identity_digest,
            cell.result_id,
            cell.result_digest,
            cell.outcome,
        )
        for cell in evaluation_cells.cells
        if (cell.task_id, cell.check_id) in allowed_refs
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


def _record_validation_error(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    evaluation_cells: EvaluationCellSet,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
) -> str | None:
    selection_validation = validate_benchmark_selection(selection)
    if not selection_validation.ok:
        return f"selection_invalid:{'; '.join(selection_validation.errors)}"
    if selection.exposure_state != "frozen":
        return "selection_not_frozen"
    if selection.task_pool_id != origin.task_pool_id or selection.task_pool_digest != origin.task_pool_digest:
        return "selection_task_pool_mismatch"
    validations = (
        ("evaluation_cell_set", validate_evaluation_cell_set(evaluation_cells)),
        ("selected_matrix", validate_result_matrix(selected_matrix)),
        ("future_matrix", validate_result_matrix(future_matrix)),
    )
    for label, validation in validations:
        if not validation.ok:
            return f"{label}_invalid:{'; '.join(validation.errors)}"
    return None


def _matrix_completeness_error(selected_matrix: ResultMatrix, future_matrix: ResultMatrix) -> str | None:
    if selected_matrix.abstention_reason or future_matrix.abstention_reason:
        return selected_matrix.abstention_reason or future_matrix.abstention_reason
    if any(cell.cell_state == "missing" for cell in selected_matrix.cells + future_matrix.cells):
        return "missing_required_results"
    for matrix in (selected_matrix, future_matrix):
        agents_with_results = {
            cell.agent_id for cell in matrix.cells if cell.cell_state == "result"
        }
        if any(agent_id not in agents_with_results for agent_id in matrix.agent_ids):
            return f"{matrix.matrix_role}_empty_agent_denominator"
    return None


def _combined_completeness_state(
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
) -> str:
    if "complete_with_exclusions" in {
        selected_matrix.scoreable_state,
        future_matrix.scoreable_state,
    }:
        return "complete_with_exclusions"
    return "complete"


def _pass_rates(matrix: ResultMatrix, weights: Mapping[str, float] | None = None) -> Mapping[str, float]:
    rates: dict[str, float] = {}
    for agent_id in matrix.agent_ids:
        cells = [cell for cell in matrix.cells if cell.agent_id == agent_id and cell.cell_state == "result"]
        if not cells:
            raise ValueError("result matrix has an empty Agent denominator")
        if any(cell.outcome not in {"pass", "fail", "invalid"} for cell in cells):
            raise ValueError("result matrix cells must carry outcomes for metric computation")
        if weights is None:
            passed = sum(1 for cell in cells if cell.outcome == "pass")
            rates[agent_id] = passed / len(cells)
            continue
        weighted_total = 0.0
        weighted_passed = 0.0
        for cell in cells:
            weight = weights.get(task_check_ref_key(TaskCheckRef(cell.task_id, cell.check_id)))
            if weight is None:
                raise ValueError("selected matrix cells must have selection weights")
            weighted_total += weight
            if cell.outcome == "pass":
                weighted_passed += weight
        if weighted_total == 0.0:
            raise ValueError("selected matrix has an empty weighted denominator")
        rates[agent_id] = weighted_passed / weighted_total
    return rates


def _mean_absolute_error(selected_rates: Mapping[str, float], future_rates: Mapping[str, float]) -> float:
    agent_ids = sorted(set(selected_rates) & set(future_rates))
    if not agent_ids:
        return 0.0
    return sum(abs(selected_rates[agent_id] - future_rates[agent_id]) for agent_id in agent_ids) / len(agent_ids)


def _pairwise_gap_mae(selected_rates: Mapping[str, float], future_rates: Mapping[str, float]) -> float:
    agent_pairs = tuple(combinations(sorted(set(selected_rates) & set(future_rates)), 2))
    if not agent_pairs:
        return 0.0
    errors = (
        abs(
            (selected_rates[left] - selected_rates[right])
            - (future_rates[left] - future_rates[right])
        )
        for left, right in agent_pairs
    )
    return fsum(errors) / len(agent_pairs)


def _rank_agreement(selected_rates: Mapping[str, float], future_rates: Mapping[str, float]) -> float:
    agent_pairs = tuple(combinations(sorted(set(selected_rates) & set(future_rates)), 2))
    if not agent_pairs:
        return 1.0
    agreements = sum(
        _sign(selected_rates[left] - selected_rates[right])
        == _sign(future_rates[left] - future_rates[right])
        for left, right in agent_pairs
    )
    return agreements / len(agent_pairs)


def _recommendation_regret(selected_rates: Mapping[str, float], future_rates: Mapping[str, float]) -> float:
    agent_ids = sorted(set(selected_rates) & set(future_rates))
    if not agent_ids:
        return 0.0
    recommended_agent = min(agent_ids, key=lambda agent_id: (-selected_rates[agent_id], agent_id))
    return max(future_rates[agent_id] for agent_id in agent_ids) - future_rates[recommended_agent]


def _sign(value: float) -> int:
    return (value > 0.0) - (value < 0.0)


def _coverage(matrix: ResultMatrix) -> float:
    if not matrix.cells:
        return 0.0
    covered = sum(1 for cell in matrix.cells if cell.cell_state == "result")
    return covered / len(matrix.cells)


def _invalid_rate(matrix: ResultMatrix) -> float:
    if not matrix.cells:
        return 0.0
    invalid = sum(
        1
        for cell in matrix.cells
        if cell.cell_state in {"missing", "excluded"} or (cell.cell_state == "result" and cell.outcome == "invalid")
    )
    return invalid / len(matrix.cells)


def _metric_record(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    evaluation_cells: EvaluationCellSet,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
    metric_config: MetricConfig,
    *,
    metric_scope: str,
    metric_name: str,
    metric_value: float,
    completeness_state: str,
    abstention_reason: str | None,
) -> MetricRecord:
    metric = MetricRecord(
        metric_id=f"metric_{canonical_digest((origin.origin_id, selection.selection_id, evaluation_cells.cell_set_digest, selected_matrix.matrix_digest, future_matrix.matrix_digest, selected_matrix.join_policy_digest, selected_matrix.denominator_policy_digest, metric_scope, metric_name, metric_config.metric_config_digest, selection.budget_digest, None, 'all_agents'))}",
        origin_id=origin.origin_id,
        selection_id=selection.selection_id,
        evaluation_cell_set_digest=evaluation_cells.cell_set_digest,
        selected_matrix_digest=selected_matrix.matrix_digest,
        future_matrix_digest=future_matrix.matrix_digest,
        join_policy_digest=selected_matrix.join_policy_digest,
        metric_config_digest=metric_config.metric_config_digest,
        metric_scope=metric_scope,
        agent_id=None,
        agent_pair=None,
        aggregation_level="all_agents",
        budget_digest=selection.budget_digest,
        stratum_ref=None,
        metric_name=metric_name,
        metric_value=metric_value,
        denominator_policy_digest=selected_matrix.denominator_policy_digest,
        completeness_state=completeness_state,
        abstention_reason=abstention_reason,
        computed_at=_now(),
        metric_digest="",
    )
    metric = record_with_digest(metric)
    validation = validate_metric(metric)
    if not validation.ok:
        raise ValueError(f"metric is invalid: {', '.join(validation.errors)}")
    return metric
