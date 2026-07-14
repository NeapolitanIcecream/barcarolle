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

from .algorithms import ensure_selector_executable
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
        selected_rates = _pass_rates(selected_matrix, selection.selected_weights)
        future_rates = _pass_rates(future_matrix)
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
    mae = _mean_absolute_error(selected_rates, future_rates)
    coverage = _coverage(future_matrix)
    invalid_rate = _invalid_rate(future_matrix)
    metric_values = (
        ("future_pass_rate_mae", mae),
        ("future_coverage", coverage),
        ("future_invalid_rate", invalid_rate),
        ("pairwise_gap_mae", _pairwise_gap_mae(selected_rates, future_rates)),
        ("rank_agreement", _rank_agreement(selected_rates, future_rates)),
        ("recommendation_regret", _recommendation_regret(selected_rates, future_rates)),
    )
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
            completeness_state=future_matrix.scoreable_state,
            abstention_reason=future_matrix.abstention_reason,
        )
        for metric_name, metric_value in metric_values
    )


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
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise ValueError("MAE values must be finite numbers between 0 and 1")
            try:
                normalized = float(value)
            except OverflowError as exc:
                raise ValueError("MAE values must be finite numbers between 0 and 1") from exc
            if not isfinite(normalized) or not 0.0 <= normalized <= 1.0:
                raise ValueError("MAE values must be finite numbers between 0 and 1")
            totals[selector_id].append(normalized)
    means = {
        selector_id: fsum(values) / len(values)
        for selector_id, values in totals.items()
    }
    best_selector_id = min(means, key=lambda selector_id: (means[selector_id], selector_id))
    return selector_by_id[best_selector_id]


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
    return None


def _pass_rates(matrix: ResultMatrix, weights: Mapping[str, float] | None = None) -> Mapping[str, float]:
    rates: dict[str, float] = {}
    for agent_id in matrix.agent_ids:
        cells = [cell for cell in matrix.cells if cell.agent_id == agent_id and cell.cell_state == "result"]
        if not cells:
            rates[agent_id] = 0.0
            continue
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
        rates[agent_id] = 0.0 if weighted_total == 0.0 else weighted_passed / weighted_total
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
