"""Selection evaluation matrices, metrics, and metric-based selector choice."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import fsum, isfinite, sqrt
from random import Random
from statistics import pstdev
from typing import Mapping, Sequence

from barcarolle.records import (
    BenchmarkSelectionRecord,
    CheckRecord,
    EvaluationCellSet,
    FeatureSnapshotRecord,
    MetricRecord,
    ResultCellRef,
    ResultRecord,
    ResultMatrix,
    RollingOriginRecord,
    SelectorInput,
    SelectorRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    agent_record_from_cache_identity,
    cache_identity_task_check_mismatches,
    canonical_digest,
    matrix_denominator_error,
    parse_utc_timestamp,
    record_with_digest,
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
from barcarolle.result_store import result_matrix_evidence_errors

from .algorithms import (
    _coverage_parameters,
    _random_parameters,
    _rule_mixture_parameters,
    _selector_record,
    _simplex_weight_points,
    ensure_selection_replay,
    ensure_selector_executable,
)
from .features import ensure_feature_snapshot_task_metadata_provenance
from .inputs import ensure_selector_input_result_evidence
from .origin import _now, validate_rolling_origin_against_records


_METRIC_PROTOCOL_VERSION = 1
_AGGREGATE_METRIC_NAMES = (
    "future_pass_rate_mae",
    "future_coverage",
    "future_invalid_rate",
    "pairwise_gap_mae",
    "rank_agreement",
    "recommendation_regret",
)
METRIC_CONFIG_DIGEST = canonical_digest(
    {
        "metric_protocol_version": _METRIC_PROTOCOL_VERSION,
        "aggregate_metric_names": _AGGREGATE_METRIC_NAMES,
        "aggregation_level": "all_agents",
    }
)


@dataclass(frozen=True)
class SafeSwitchConfig:
    prior_strength: float = 2.0
    minimum_origins: int = 4
    improvement_margin: float = 0.0
    uncertainty_multiplier: float = 1.0

    def __post_init__(self) -> None:
        for name in (
            "prior_strength",
            "improvement_margin",
            "uncertainty_multiplier",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise ValueError(f"{name} must be a finite nonnegative number")
            try:
                normalized = float(value)
            except OverflowError as exc:
                raise ValueError(f"{name} must be a finite nonnegative number") from exc
            if not isfinite(normalized) or normalized < 0:
                raise ValueError(f"{name} must be a finite nonnegative number")
            object.__setattr__(self, name, normalized)
        if (
            isinstance(self.minimum_origins, bool)
            or not isinstance(self.minimum_origins, int)
            or self.minimum_origins < 2
        ):
            raise ValueError("minimum_origins must be an integer of at least 2")


@dataclass(frozen=True)
class EWMASwitchConfig:
    half_life_origins: float = 2.0
    safe_switch: SafeSwitchConfig = SafeSwitchConfig()

    def __post_init__(self) -> None:
        value = self.half_life_origins
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError("half_life_origins must be a finite positive number")
        try:
            normalized = float(value)
        except OverflowError as exc:
            raise ValueError(
                "half_life_origins must be a finite positive number"
            ) from exc
        if not isfinite(normalized) or normalized <= 0:
            raise ValueError("half_life_origins must be a finite positive number")
        if not isinstance(self.safe_switch, SafeSwitchConfig):
            raise ValueError("safe_switch must be a SafeSwitchConfig")
        object.__setattr__(self, "half_life_origins", normalized)


@dataclass(frozen=True)
class SimplexChoiceConfig:
    minimum_origins: int = 4

    def __post_init__(self) -> None:
        if (
            isinstance(self.minimum_origins, bool)
            or not isinstance(self.minimum_origins, int)
            or self.minimum_origins < 2
        ):
            raise ValueError("minimum_origins must be an integer of at least 2")


@dataclass(frozen=True)
class _PairedSelectionEvidence:
    by_id: Mapping[str, BenchmarkSelectionRecord]
    by_origin: Mapping[str, Mapping[str, BenchmarkSelectionRecord]]


@dataclass(frozen=True)
class _PairedMetricEvidence:
    by_selection_id: Mapping[str, MetricRecord]
    join_policy_digests: frozenset[str]
    denominator_policy_digests: frozenset[str]
    completeness_by_origin: Mapping[str, frozenset[str]]


def evaluate_selection(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    evaluation_cells: EvaluationCellSet,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
) -> Sequence[MetricRecord]:
    record_error = _record_validation_error(
        selection, origin, evaluation_cells, selected_matrix, future_matrix
    )
    if record_error:
        return (
            _metric_record(
                selection,
                origin,
                evaluation_cells,
                selected_matrix,
                future_matrix,
                metric_scope="aggregate",
                metric_name="selection_evaluation_invalid",
                metric_value=0.0,
                completeness_state="invalid",
                abstention_reason=record_error,
            ),
        )
    alignment_error = _matrix_alignment_error(
        selection, origin, evaluation_cells, selected_matrix, future_matrix
    )
    if alignment_error:
        return (
            _metric_record(
                selection,
                origin,
                evaluation_cells,
                selected_matrix,
                future_matrix,
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


_SELECTOR_MAE_SUMMARY_PROTOCOL = {
    "protocol_version": "paired_selector_mae_summary_v1",
    "future_weight": "distinct_scoreable_task_check_refs",
    "paired_difference": "selector_a_minus_selector_b",
    "uncertainty_protocol": "paired_origin_block_percentile_bootstrap_v1",
    "uncertainty_confidence_level": 0.95,
    "uncertainty_minimum_blocks": 8,
    "uncertainty_resamples": 10_000,
    "uncertainty_seed": 20_260_722,
}


def summarize_selector_mae(
    registered_selectors: Sequence[SelectorRecord],
    selections: Sequence[BenchmarkSelectionRecord],
    mae_metrics: Sequence[MetricRecord],
    future_matrices: Sequence[ResultMatrix],
) -> Mapping[str, object]:
    """Summarize paired rolling-origin MAE under the frozen protocol."""
    selectors_by_id: dict[str, SelectorRecord] = {}
    for selector in registered_selectors:
        validation = validate_selector(selector)
        if not validation.ok:
            raise ValueError(
                f"registered selector is invalid: {', '.join(validation.errors)}"
            )
        ensure_selector_executable(selector)
        if selector.selector_id in selectors_by_id:
            raise ValueError("registered selector IDs must be unique")
        selectors_by_id[selector.selector_id] = selector
    if not selectors_by_id:
        raise ValueError("registered_selectors must not be empty")

    mae_rows = _paired_mae_by_origin(
        {
            selector_id: selector.selector_digest
            for selector_id, selector in selectors_by_id.items()
        },
        selections,
        mae_metrics,
        future_matrices,
    )
    if not mae_rows:
        raise ValueError("selector MAE summary requires at least one origin")
    origin_ids = tuple(sorted({selection.origin_id for selection in selections}))
    if len(origin_ids) != len(mae_rows):
        raise ValueError("paired MAE rows do not match selection origins")
    future_counts = _future_scoreable_counts_by_origin(selections, future_matrices)
    weights = tuple(future_counts[origin_id] for origin_id in origin_ids)

    values_by_selector = {
        selector_id: tuple(row[selector_id] for row in mae_rows)
        for selector_id in sorted(selectors_by_id)
    }
    selector_rows = tuple(
        {
            "selector_id": selector_id,
            "macro_origin_mae": _mean(values),
            "future_task_count_weighted_mae": _weighted_mean(values, weights),
            "origin_block_interval_95": _origin_block_interval(values),
        }
        for selector_id, values in values_by_selector.items()
    )
    pair_rows = tuple(
        _paired_selector_summary(
            selector_a_id,
            selector_b_id,
            values_by_selector[selector_a_id],
            values_by_selector[selector_b_id],
            weights,
        )
        for selector_a_id, selector_b_id in combinations(values_by_selector, 2)
    )
    seed_banks = _stochastic_seed_bank_summaries(
        selectors_by_id,
        values_by_selector,
    )
    origin_rows = tuple(
        {
            "origin_id": origin_id,
            "future_scoreable_task_check_count": future_counts[origin_id],
            "mae_by_selector": dict(sorted(mae_row.items())),
        }
        for origin_id, mae_row in zip(origin_ids, mae_rows, strict=True)
    )
    return {
        **_SELECTOR_MAE_SUMMARY_PROTOCOL,
        "protocol_digest": canonical_digest(_SELECTOR_MAE_SUMMARY_PROTOCOL),
        "evidence_digest": canonical_digest(
            {
                "selector_digests": tuple(
                    sorted(
                        selector.selector_digest
                        for selector in selectors_by_id.values()
                    )
                ),
                "selection_digests": tuple(
                    sorted(selection.selection_digest for selection in selections)
                ),
                "metric_digests": tuple(
                    sorted(metric.metric_digest for metric in mae_metrics)
                ),
                "future_matrix_digests": tuple(
                    sorted(matrix.matrix_digest for matrix in future_matrices)
                ),
            }
        ),
        "origin_count": len(origin_ids),
        "future_scoreable_task_check_count": sum(weights),
        "origins": origin_rows,
        "selectors": selector_rows,
        "paired_differences": pair_rows,
        "seed_banks": seed_banks,
    }


def _future_scoreable_counts_by_origin(
    selections: Sequence[BenchmarkSelectionRecord],
    future_matrices: Sequence[ResultMatrix],
) -> Mapping[str, int]:
    origin_by_selection = {
        selection.selection_id: selection.origin_id for selection in selections
    }
    counts_by_origin: dict[str, set[int]] = {}
    for matrix in future_matrices:
        origin_id = origin_by_selection.get(matrix.selection_id)
        if origin_id is None:
            raise ValueError(
                f"future matrix has no matching selection: {matrix.selection_id}"
            )
        scoreable_refs = {
            (cell.task_id, cell.check_id)
            for cell in matrix.cells
            if cell.cell_state == "result"
        }
        counts_by_origin.setdefault(origin_id, set()).add(len(scoreable_refs))
    counts: dict[str, int] = {}
    for origin_id in sorted(set(origin_by_selection.values())):
        observed = counts_by_origin.get(origin_id, set())
        if len(observed) != 1:
            raise ValueError(
                f"origin {origin_id} must have one future scoreable task count"
            )
        count = next(iter(observed))
        if count < 1:
            raise ValueError(
                f"origin {origin_id} must have scoreable future Task/Check refs"
            )
        counts[origin_id] = count
    return counts


def _paired_selector_summary(
    selector_a_id: str,
    selector_b_id: str,
    selector_a_values: Sequence[float],
    selector_b_values: Sequence[float],
    weights: Sequence[int],
) -> Mapping[str, object]:
    differences = tuple(
        value_a - value_b
        for value_a, value_b in zip(
            selector_a_values,
            selector_b_values,
            strict=True,
        )
    )
    return {
        "selector_a_id": selector_a_id,
        "selector_b_id": selector_b_id,
        "difference_direction": "selector_a_minus_selector_b",
        "macro_origin_mae_difference": _mean(differences),
        "future_task_count_weighted_mae_difference": _weighted_mean(
            differences,
            weights,
        ),
        "origin_block_interval_95": _origin_block_interval(differences),
    }


def _stochastic_seed_bank_summaries(
    selectors_by_id: Mapping[str, SelectorRecord],
    values_by_selector: Mapping[str, Sequence[float]],
) -> tuple[Mapping[str, object], ...]:
    grouped: dict[str, list[tuple[int, str, SelectorRecord]]] = {}
    for selector_id, selector in selectors_by_id.items():
        signature = _stochastic_selector_signature(selector)
        if signature is None:
            continue
        group_digest, seed = signature
        grouped.setdefault(group_digest, []).append((seed, selector_id, selector))

    summaries: list[Mapping[str, object]] = []
    for group_digest, variants in sorted(grouped.items()):
        if len(variants) < 2:
            continue
        ordered = tuple(sorted(variants))
        seeds = tuple(seed for seed, _, _ in ordered)
        if len(seeds) != len(set(seeds)):
            raise ValueError("stochastic seed-bank variants must use unique seeds")
        selector_ids = tuple(selector_id for _, selector_id, _ in ordered)
        macro_values = tuple(
            _mean(values_by_selector[selector_id]) for selector_id in selector_ids
        )
        summaries.append(
            {
                "seed_bank_id": f"seed_bank_{group_digest}",
                "selector_family": ordered[0][2].selector_family,
                "selector_ids": selector_ids,
                "seeds": seeds,
                "macro_origin_mae_mean": _mean(macro_values),
                "macro_origin_mae_population_stddev": pstdev(macro_values),
            }
        )
    return tuple(summaries)


def _stochastic_selector_signature(
    selector: SelectorRecord,
) -> tuple[str, int] | None:
    seed_field = {
        "random": "seed",
        "rule_mixture": "random_seed",
        "stratified_forecast": "seed",
    }.get(selector.selector_family)
    if seed_field is None:
        return None
    parameters = dict(selector.parameters)
    seed = parameters.pop(seed_field)
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError(f"{selector.selector_family} seed must be an integer")
    return (
        canonical_digest(
            {
                "selector_family": selector.selector_family,
                "selector_version": selector.selector_version,
                "training_source_digests": selector.training_source_digests,
                "allowed_feature_classes": selector.allowed_feature_classes,
                "non_seed_parameters": parameters,
            }
        ),
        seed,
    )


def _origin_block_interval(values: Sequence[float]) -> Mapping[str, object]:
    block_count = len(values)
    base = {
        "protocol": _SELECTOR_MAE_SUMMARY_PROTOCOL["uncertainty_protocol"],
        "confidence_level": _SELECTOR_MAE_SUMMARY_PROTOCOL[
            "uncertainty_confidence_level"
        ],
        "block_count": block_count,
    }
    minimum_blocks = int(_SELECTOR_MAE_SUMMARY_PROTOCOL["uncertainty_minimum_blocks"])
    if block_count < minimum_blocks:
        return {
            **base,
            "status": "insufficient_origin_blocks",
            "lower": None,
            "upper": None,
        }
    resamples = int(_SELECTOR_MAE_SUMMARY_PROTOCOL["uncertainty_resamples"])
    seed = int(_SELECTOR_MAE_SUMMARY_PROTOCOL["uncertainty_seed"])
    random = Random(seed)
    bootstrap_values = sorted(
        fsum(values[random.randrange(block_count)] for _ in range(block_count))
        / block_count
        for _ in range(resamples)
    )
    return {
        **base,
        "status": "available",
        "resamples": resamples,
        "seed": seed,
        "lower": _linear_percentile(bootstrap_values, 0.025),
        "upper": _linear_percentile(bootstrap_values, 0.975),
    }


def _linear_percentile(values: Sequence[float], quantile: float) -> float:
    position = (len(values) - 1) * quantile
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(values) - 1)
    fraction = position - lower_index
    return values[lower_index] + (values[upper_index] - values[lower_index]) * fraction


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires at least one value")
    return fsum(values) / len(values)


def _weighted_mean(values: Sequence[float], weights: Sequence[int]) -> float:
    if len(values) != len(weights):
        raise ValueError("values and weights must have the same length")
    total_weight = sum(weights)
    if total_weight < 1:
        raise ValueError("weighted mean requires positive total weight")
    return (
        fsum(value * weight for value, weight in zip(values, weights, strict=True))
        / total_weight
    )


def _choose_selector_by_mean_mae(
    registered_selectors: Sequence[SelectorRecord],
    mae_by_origin: Sequence[Mapping[str, float]],
    fallback_selector_id: str,
) -> SelectorRecord:
    selector_by_id, normalized_rows = _validated_selector_choice_inputs(
        registered_selectors,
        mae_by_origin,
        fallback_selector_id,
    )
    if not normalized_rows:
        return selector_by_id[fallback_selector_id]
    means = {
        selector_id: _mean(tuple(row[selector_id] for row in normalized_rows))
        for selector_id in selector_by_id
    }
    best_selector_id = min(
        means, key=lambda selector_id: (means[selector_id], selector_id)
    )
    return selector_by_id[best_selector_id]


def _validated_selector_choice_inputs(
    registered_selectors: Sequence[SelectorRecord],
    mae_by_origin: Sequence[Mapping[str, float]],
    fallback_selector_id: str,
) -> tuple[Mapping[str, SelectorRecord], tuple[Mapping[str, float], ...]]:
    selector_by_id = _validated_selector_registry(
        registered_selectors,
        fallback_selector_id,
    )
    expected_selector_ids = set(selector_by_id)
    return selector_by_id, tuple(
        _normalized_selector_mae_row(row, expected_selector_ids)
        for row in mae_by_origin
    )


def _validated_selector_registry(
    registered_selectors: Sequence[SelectorRecord],
    fallback_selector_id: str,
) -> Mapping[str, SelectorRecord]:
    if not registered_selectors:
        raise ValueError("registered_selectors must not be empty")
    for selector in registered_selectors:
        validation = validate_selector(selector)
        if not validation.ok:
            raise ValueError(
                f"registered selector is invalid: {', '.join(validation.errors)}"
            )
        ensure_selector_executable(selector)
    selector_ids = [selector.selector_id for selector in registered_selectors]
    if len(selector_ids) != len(set(selector_ids)):
        raise ValueError("registered selector IDs must be unique")
    selector_by_id = {
        selector.selector_id: selector for selector in registered_selectors
    }
    if fallback_selector_id not in selector_by_id:
        raise ValueError("fallback_selector_id is not registered")
    return selector_by_id


def _normalized_selector_mae_row(
    row: Mapping[str, float],
    expected_selector_ids: set[str],
) -> Mapping[str, float]:
    if not isinstance(row, Mapping):
        raise ValueError("each MAE row must map selector IDs to MAE values")
    row_selector_ids = set(row)
    if row_selector_ids != expected_selector_ids:
        missing = sorted(expected_selector_ids - row_selector_ids)
        extra = sorted(row_selector_ids - expected_selector_ids, key=str)
        details = [f"missing {', '.join(missing)}"] if missing else []
        if extra:
            details.append(f"unknown {', '.join(map(str, extra))}")
        raise ValueError(
            f"each MAE row must cover every registered selector: {'; '.join(details)}"
        )
    return {selector_id: _normalized_mae(value) for selector_id, value in row.items()}


def _choose_selector_by_safe_switch(
    registered_selectors: Sequence[SelectorRecord],
    mae_by_origin: Sequence[Mapping[str, float]],
    fallback_selector_id: str,
    config: SafeSwitchConfig,
) -> SelectorRecord:
    selector_by_id, normalized_rows = _validated_selector_choice_inputs(
        registered_selectors,
        mae_by_origin,
        fallback_selector_id,
    )
    fallback = selector_by_id[fallback_selector_id]
    if len(normalized_rows) < config.minimum_origins:
        return fallback

    origin_count = len(normalized_rows)
    qualified: list[tuple[float, float, str]] = []
    for selector_id in selector_by_id:
        if selector_id == fallback_selector_id:
            continue
        improvements = tuple(
            row[fallback_selector_id] - row[selector_id] for row in normalized_rows
        )
        shrunk_mean = fsum(improvements) / (origin_count + config.prior_strength)
        standard_error = _sample_standard_error(improvements)
        conservative_improvement = (
            shrunk_mean - config.uncertainty_multiplier * standard_error
        )
        if conservative_improvement > config.improvement_margin:
            qualified.append((conservative_improvement, shrunk_mean, selector_id))
    if not qualified:
        return fallback
    _, _, chosen_selector_id = min(
        qualified,
        key=lambda candidate: (-candidate[0], -candidate[1], candidate[2]),
    )
    return selector_by_id[chosen_selector_id]


def _sample_standard_error(values: Sequence[float]) -> float:
    mean = _mean(values)
    sample_variance = fsum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return sqrt(sample_variance / len(values))


def _choose_selector_by_ewma_guard(
    registered_selectors: Sequence[SelectorRecord],
    mae_by_origin: Sequence[Mapping[str, float]],
    fallback_selector_id: str,
    config: EWMASwitchConfig,
) -> SelectorRecord:
    selector_by_id, normalized_rows = _validated_selector_choice_inputs(
        registered_selectors,
        mae_by_origin,
        fallback_selector_id,
    )
    fallback = selector_by_id[fallback_selector_id]
    if len(normalized_rows) < config.safe_switch.minimum_origins:
        return fallback

    means = {
        selector_id: _ewma(tuple(row[selector_id] for row in normalized_rows), config)
        for selector_id in selector_by_id
    }
    candidate_id = min(
        means,
        key=lambda selector_id: (means[selector_id], selector_id),
    )
    if candidate_id == fallback_selector_id:
        return fallback

    candidate = selector_by_id[candidate_id]
    guarded_rows = tuple(
        {
            fallback_selector_id: row[fallback_selector_id],
            candidate_id: row[candidate_id],
        }
        for row in normalized_rows
    )
    return _choose_selector_by_safe_switch(
        (fallback, candidate),
        guarded_rows,
        fallback_selector_id,
        config.safe_switch,
    )


def _ewma(values: Sequence[float], config: EWMASwitchConfig) -> float:
    newest_index = len(values) - 1
    weights = tuple(
        0.5 ** ((newest_index - index) / config.half_life_origins)
        for index in range(len(values))
    )
    return fsum(
        value * weight for value, weight in zip(values, weights, strict=True)
    ) / fsum(weights)


def _choose_rule_mixture_by_one_se(
    registered_selectors: Sequence[SelectorRecord],
    mae_by_origin: Sequence[Mapping[str, float]],
    config: SimplexChoiceConfig,
) -> SelectorRecord:
    point_by_selector_id, equal = _validated_rule_mixture_grid(registered_selectors)
    selector_by_id, normalized_rows = _validated_selector_choice_inputs(
        registered_selectors,
        mae_by_origin,
        equal.selector_id,
    )
    if len(normalized_rows) < config.minimum_origins:
        return equal
    losses_by_selector = {
        selector_id: tuple(row[selector_id] for row in normalized_rows)
        for selector_id in selector_by_id
    }
    means = {
        selector_id: _mean(losses) for selector_id, losses in losses_by_selector.items()
    }
    best_selector_id = min(
        means, key=lambda selector_id: (means[selector_id], selector_id)
    )
    one_se_limit = means[best_selector_id] + _sample_standard_error(
        losses_by_selector[best_selector_id]
    )
    eligible_ids = tuple(
        selector_id
        for selector_id in selector_by_id
        if means[selector_id] <= one_se_limit
    )
    chosen_id = min(
        eligible_ids,
        key=lambda selector_id: (
            _distance_from_equal(point_by_selector_id[selector_id]),
            means[selector_id],
            selector_id,
        ),
    )
    return selector_by_id[chosen_id]


def _validated_rule_mixture_grid(
    selectors: Sequence[SelectorRecord],
) -> tuple[Mapping[str, tuple[float, float, float]], SelectorRecord]:
    expected_points = set(_simplex_weight_points())
    if len(selectors) != len(expected_points):
        raise ValueError(
            "rule mixture choice requires a complete ten-point simplex grid"
        )
    selector_ids = [selector.selector_id for selector in selectors]
    if len(selector_ids) != len(set(selector_ids)):
        raise ValueError("simplex-grid Selector IDs must be unique")

    selector_by_point: dict[tuple[float, float, float], SelectorRecord] = {}
    behavior_signatures: set[str] = set()
    for selector in selectors:
        validation = validate_selector(selector)
        if not validation.ok:
            raise ValueError(
                f"simplex-grid selector is invalid: {', '.join(validation.errors)}"
            )
        ensure_selector_executable(selector)
        if selector.selector_family != "rule_mixture":
            raise ValueError("simplex grid must contain only rule_mixture selectors")
        weights, random_seed, groups = _rule_mixture_parameters(selector.parameters)
        point = _normalized_simplex_point(weights)
        if point not in expected_points or point in selector_by_point:
            raise ValueError(
                "rule mixture choice requires a complete ten-point simplex grid"
            )
        selector_by_point[point] = selector
        behavior_signatures.add(
            canonical_digest(
                {
                    "selector_version": selector.selector_version,
                    "training_source_digests": selector.training_source_digests,
                    "allowed_feature_classes": selector.allowed_feature_classes,
                    "random_seed": random_seed,
                    "group_by_ref_key": groups,
                }
            )
        )
    if set(selector_by_point) != expected_points:
        raise ValueError(
            "rule mixture choice requires a complete ten-point simplex grid"
        )
    if len(behavior_signatures) != 1:
        raise ValueError(
            "simplex-grid selectors must share the same non-weight behavior"
        )
    equal_point = (1 / 3, 1 / 3, 1 / 3)
    return (
        {selector.selector_id: point for point, selector in selector_by_point.items()},
        selector_by_point[equal_point],
    )


def _normalized_simplex_point(
    weights: Mapping[str, float],
) -> tuple[float, float, float]:
    families = ("coverage", "random", "recency")
    total = fsum(weights.get(family, 0.0) for family in families)
    normalized = tuple(weights.get(family, 0.0) / total for family in families)
    units = tuple(round(value * 3) for value in normalized)
    if sum(units) != 3 or any(
        abs(value * 3 - unit) > 1e-12
        for value, unit in zip(normalized, units, strict=True)
    ):
        raise ValueError("rule mixture weights must lie on the thirds simplex grid")
    return tuple(unit / 3 for unit in units)  # type: ignore[return-value]


def _distance_from_equal(point: tuple[float, float, float]) -> float:
    return fsum((weight - 1 / 3) ** 2 for weight in point)


def choose_selector_from_metrics(
    registered_selectors: Sequence[SelectorRecord],
    selections: Sequence[BenchmarkSelectionRecord],
    mae_metrics: Sequence[MetricRecord],
    future_matrices: Sequence[ResultMatrix],
    fallback_selector_id: str,
) -> SelectorRecord:
    fallback = _choose_selector_by_mean_mae(
        registered_selectors,
        (),
        fallback_selector_id,
    )
    mae_by_origin = _paired_mae_by_origin(
        {
            selector.selector_id: selector.selector_digest
            for selector in registered_selectors
        },
        selections,
        mae_metrics,
        future_matrices,
    )
    if not mae_by_origin:
        return fallback
    return _choose_selector_by_mean_mae(
        registered_selectors,
        mae_by_origin,
        fallback_selector_id,
    )


def choose_selector_with_safe_switch(
    registered_selectors: Sequence[SelectorRecord],
    selections: Sequence[BenchmarkSelectionRecord],
    mae_metrics: Sequence[MetricRecord],
    future_matrices: Sequence[ResultMatrix],
    fallback_selector_id: str,
    *,
    config: SafeSwitchConfig = SafeSwitchConfig(),
) -> SelectorRecord:
    """Choose an expert only when paired history clears a conservative gate."""
    mae_by_origin = _paired_mae_by_origin(
        {
            selector.selector_id: selector.selector_digest
            for selector in registered_selectors
        },
        selections,
        mae_metrics,
        future_matrices,
    )
    return _choose_selector_by_safe_switch(
        registered_selectors,
        mae_by_origin,
        fallback_selector_id,
        config,
    )


def choose_selector_with_ewma_guard(
    registered_selectors: Sequence[SelectorRecord],
    selections: Sequence[BenchmarkSelectionRecord],
    mae_metrics: Sequence[MetricRecord],
    future_matrices: Sequence[ResultMatrix],
    training_origins: Sequence[RollingOriginRecord],
    deployment_origin: RollingOriginRecord,
    fallback_selector_id: str,
    *,
    config: EWMASwitchConfig = EWMASwitchConfig(),
) -> SelectorRecord:
    """Rank by recent paired MAE, then require full-history safe-switch evidence."""
    mae_by_origin = _paired_mae_by_origin_mapping(
        {
            selector.selector_id: selector.selector_digest
            for selector in registered_selectors
        },
        selections,
        mae_metrics,
        future_matrices,
    )
    ordered_rows = _chronological_mae_rows(
        training_origins,
        deployment_origin,
        selections,
        mae_by_origin,
    )
    return _choose_selector_by_ewma_guard(
        registered_selectors,
        ordered_rows,
        fallback_selector_id,
        config,
    )


def choose_rule_mixture_from_grid(
    registered_selectors: Sequence[SelectorRecord],
    selections: Sequence[BenchmarkSelectionRecord],
    mae_metrics: Sequence[MetricRecord],
    future_matrices: Sequence[ResultMatrix],
    *,
    config: SimplexChoiceConfig = SimplexChoiceConfig(),
) -> SelectorRecord:
    """Choose a measured grid point, preferring equal weights within one SE."""
    mae_by_origin = _paired_mae_by_origin(
        {
            selector.selector_id: selector.selector_digest
            for selector in registered_selectors
        },
        selections,
        mae_metrics,
        future_matrices,
    )
    return _choose_rule_mixture_by_one_se(
        registered_selectors,
        mae_by_origin,
        config,
    )


_RULE_MIXTURE_TRAINER_PROTOCOL = "rule_mixture_future_pass_rate_mae_v1"


def train_selector(
    selector_family: str,
    *,
    deployment_origin: RollingOriginRecord,
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    training_origins: Sequence[RollingOriginRecord],
    feature_snapshots: Sequence[FeatureSnapshotRecord],
    selector_inputs: Sequence[SelectorInput],
    expert_selectors: Sequence[SelectorRecord],
    selections: Sequence[BenchmarkSelectionRecord],
    result_matrices: Sequence[ResultMatrix],
    metrics: Sequence[MetricRecord],
    pre_origin_results: Sequence[ResultRecord],
    training_results: Sequence[ResultRecord],
) -> SelectorRecord:
    """Fit the one learned Selector family from replayable rolling-origin evidence."""
    if selector_family != "rule_mixture":
        raise ValueError(
            "train_selector currently supports only the rule_mixture family"
        )
    experts = _validated_rule_mixture_experts(expert_selectors)
    origins_by_id = _validated_training_origins(deployment_origin, training_origins)
    snapshots_by_origin, inputs_by_origin = _validated_training_inputs(
        origins_by_id,
        feature_snapshots,
        selector_inputs,
    )
    _validate_training_task_pool_evidence(
        deployment_origin,
        origins_by_id,
        snapshots_by_origin,
        task_pool,
        tasks,
        checks,
    )
    _validate_training_pre_origin_results(
        origins_by_id,
        snapshots_by_origin,
        inputs_by_origin,
        pre_origin_results,
    )
    selections_by_id, selections_by_origin = _validated_training_selections(
        origins_by_id,
        snapshots_by_origin,
        inputs_by_origin,
        experts,
        selections,
    )
    matrices_by_selection = _validated_training_matrices(
        origins_by_id,
        inputs_by_origin,
        selections_by_id,
        result_matrices,
    )
    mae_by_origin = _validated_training_metrics(
        selections_by_id,
        selections_by_origin,
        matrices_by_selection,
        metrics,
    )
    _validate_training_results(
        deployment_origin,
        matrices_by_selection,
        training_results,
    )
    _validate_training_result_agent_identities(
        inputs_by_origin,
        training_results,
    )
    _validate_training_result_task_check_identities(
        (*pre_origin_results, *training_results),
        tasks,
        checks,
    )

    ordered_families = ("coverage", "random", "recency")
    expert_weights = {
        family: 1.0
        - fsum(row[experts[family].selector_id] for row in mae_by_origin)
        / len(mae_by_origin)
        for family in ordered_families
    }
    if all(weight == 0.0 for weight in expert_weights.values()):
        expert_weights = {family: 1.0 for family in ordered_families}

    ordered_origins = tuple(
        sorted(
            training_origins,
            key=lambda origin: (
                parse_utc_timestamp(origin.as_of_cutoff),
                origin.origin_id,
            ),
        )
    )
    training_source_digests = (
        canonical_digest(
            {
                "trainer_protocol": _RULE_MIXTURE_TRAINER_PROTOCOL,
                "selector_family": selector_family,
                "deployment_origin_digest": deployment_origin.origin_digest,
            }
        ),
        canonical_digest(
            {
                "training_origins": tuple(
                    origin.origin_digest for origin in ordered_origins
                )
            }
        ),
        canonical_digest(
            {
                "feature_snapshots": tuple(
                    snapshots_by_origin[origin.origin_id].feature_snapshot_digest
                    for origin in ordered_origins
                )
            }
        ),
        canonical_digest(
            {
                "selector_inputs": tuple(
                    inputs_by_origin[origin.origin_id].selector_input_digest
                    for origin in ordered_origins
                )
            }
        ),
        canonical_digest(
            {
                "expert_selectors": tuple(
                    experts[family].selector_digest for family in ordered_families
                )
            }
        ),
        canonical_digest(
            {
                "selections": tuple(
                    sorted(selection.selection_digest for selection in selections)
                )
            }
        ),
        canonical_digest(
            {
                "result_matrices": tuple(
                    sorted(matrix.matrix_digest for matrix in result_matrices)
                )
            }
        ),
        canonical_digest(
            {"metrics": tuple(sorted(metric.metric_digest for metric in metrics))}
        ),
        canonical_digest(
            {
                "pre_origin_results": tuple(
                    sorted(
                        (result.result_id, result.result_digest)
                        for result in pre_origin_results
                    )
                )
            }
        ),
        canonical_digest(
            {
                "training_results": tuple(
                    sorted(
                        (result.result_id, result.result_digest)
                        for result in training_results
                    )
                )
            }
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
            "group_by_ref_key": dict(
                _coverage_parameters(experts["coverage"].parameters)
            ),
        },
    )


def _validated_training_origins(
    deployment_origin: RollingOriginRecord,
    training_origins: Sequence[RollingOriginRecord],
) -> Mapping[str, RollingOriginRecord]:
    _ensure_deployment_origin_valid(deployment_origin)
    if not training_origins:
        raise ValueError("training_origins must not be empty")
    deployment_origin_time = parse_utc_timestamp(deployment_origin.origin_time)
    deployment_cutoff = parse_utc_timestamp(deployment_origin.as_of_cutoff)
    origins_by_id: dict[str, RollingOriginRecord] = {}
    comparable_policy: tuple[object, ...] | None = None
    for origin in training_origins:
        validation = validate_rolling_origin(origin)
        if not validation.ok:
            raise ValueError(
                f"training origin is invalid: {', '.join(validation.errors)}"
            )
        if origin.origin_id in origins_by_id:
            raise ValueError(f"duplicate training origin ID: {origin.origin_id}")
        if (
            origin.task_pool_id != deployment_origin.task_pool_id
            or origin.task_pool_digest != deployment_origin.task_pool_digest
        ):
            raise ValueError("training origins must use the deployment task pool")
        if not origin.future_holdout_known:
            raise ValueError("training origins must know their future holdout")
        if parse_utc_timestamp(origin.origin_time) >= deployment_origin_time:
            raise ValueError("training origins must precede the deployment origin")
        if parse_utc_timestamp(origin.as_of_cutoff) >= deployment_cutoff:
            raise ValueError("training origin cutoffs must precede deployment cutoff")
        if parse_utc_timestamp(origin.label_maturity_cutoff) > deployment_cutoff:
            raise ValueError(
                "training label-maturity cutoffs must not exceed the deployment cutoff"
            )
        policy = (
            origin.as_of_cutoff_rule,
            origin.eligibility_mode,
            origin.holdout_overlap_policy,
            origin.allowed_dependency_cluster_ids,
            origin.future_cohort_time_basis,
            origin.maturity_lag_seconds,
        )
        if comparable_policy is None:
            comparable_policy = policy
        elif policy != comparable_policy:
            raise ValueError("training origins must use one comparable policy")
        origins_by_id[origin.origin_id] = origin
    return origins_by_id


def _ensure_deployment_origin_valid(deployment_origin: RollingOriginRecord) -> None:
    deployment_validation = validate_rolling_origin(deployment_origin)
    if not deployment_validation.ok:
        raise ValueError(
            "deployment origin is invalid: " + ", ".join(deployment_validation.errors)
        )


def _validate_training_task_pool_evidence(
    deployment_origin: RollingOriginRecord,
    origins_by_id: Mapping[str, RollingOriginRecord],
    snapshots_by_origin: Mapping[str, FeatureSnapshotRecord],
    task_pool: TaskPoolRecord,
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
) -> None:
    task_records = tuple(tasks)
    if (
        deployment_origin.task_pool_id != task_pool.task_pool_id
        or deployment_origin.task_pool_digest != task_pool.task_pool_digest
        or tuple(task.task_id for task in task_records) != task_pool.task_ids
        or canonical_digest(task_records) != task_pool.task_records_digest
    ):
        raise ValueError("training Task records do not match the frozen Task Pool")
    if set(checks) != set(task_pool.check_ids):
        raise ValueError("training Check records do not match the frozen Task Pool")
    check_records = tuple(checks[check_id] for check_id in task_pool.check_ids)
    if canonical_digest(check_records) != task_pool.check_records_digest:
        raise ValueError("training Check records do not match the frozen Task Pool")

    for origin in (deployment_origin, *origins_by_id.values()):
        validation = validate_rolling_origin_against_records(
            origin,
            task_pool,
            task_records,
            checks,
        )
        if not validation.ok:
            raise ValueError(
                f"training origin {origin.origin_id} does not match frozen "
                f"Task Pool records: {', '.join(validation.errors)}"
            )
    for origin_id, snapshot in snapshots_by_origin.items():
        ensure_feature_snapshot_task_metadata_provenance(
            snapshot,
            origins_by_id[origin_id],
            task_pool,
            task_records,
        )


def _validated_training_inputs(
    origins_by_id: Mapping[str, RollingOriginRecord],
    feature_snapshots: Sequence[FeatureSnapshotRecord],
    selector_inputs: Sequence[SelectorInput],
) -> tuple[
    Mapping[str, FeatureSnapshotRecord],
    Mapping[str, SelectorInput],
]:
    snapshots_by_origin = _validated_training_snapshots(feature_snapshots)
    inputs_by_origin = _validated_selector_inputs(
        origins_by_id,
        snapshots_by_origin,
        selector_inputs,
    )
    expected_origin_ids = set(origins_by_id)
    if set(snapshots_by_origin) != expected_origin_ids:
        raise ValueError("feature snapshots must exactly cover training origins")
    if set(inputs_by_origin) != expected_origin_ids:
        raise ValueError("selector inputs must exactly cover training origins")
    return snapshots_by_origin, inputs_by_origin


def _validated_training_snapshots(
    feature_snapshots: Sequence[FeatureSnapshotRecord],
) -> Mapping[str, FeatureSnapshotRecord]:
    snapshots_by_origin: dict[str, FeatureSnapshotRecord] = {}
    snapshot_ids: set[str] = set()
    for snapshot in feature_snapshots:
        validation = validate_feature_snapshot(snapshot)
        if not validation.ok:
            raise ValueError(
                f"training feature snapshot is invalid: {', '.join(validation.errors)}"
            )
        if snapshot.feature_snapshot_id in snapshot_ids:
            raise ValueError(
                f"duplicate feature snapshot ID: {snapshot.feature_snapshot_id}"
            )
        if snapshot.origin_id in snapshots_by_origin:
            raise ValueError(
                f"duplicate feature snapshot for origin: {snapshot.origin_id}"
            )
        snapshot_ids.add(snapshot.feature_snapshot_id)
        snapshots_by_origin[snapshot.origin_id] = snapshot
    return snapshots_by_origin


def _validated_selector_inputs(
    origins_by_id: Mapping[str, RollingOriginRecord],
    snapshots_by_origin: Mapping[str, FeatureSnapshotRecord],
    selector_inputs: Sequence[SelectorInput],
) -> Mapping[str, SelectorInput]:
    inputs_by_origin: dict[str, SelectorInput] = {}
    input_ids: set[str] = set()
    agent_bindings: tuple[tuple[str, str], ...] | None = None
    budget_digest: str | None = None
    feature_config_digest: str | None = None
    for selector_input in selector_inputs:
        validation = validate_selector_input(selector_input)
        if not validation.ok:
            raise ValueError(
                f"training selector input is invalid: {', '.join(validation.errors)}"
            )
        if selector_input.selector_input_id in input_ids:
            raise ValueError(
                f"duplicate selector input ID: {selector_input.selector_input_id}"
            )
        if selector_input.origin_id in inputs_by_origin:
            raise ValueError(
                f"duplicate selector input for origin: {selector_input.origin_id}"
            )
        origin = origins_by_id.get(selector_input.origin_id)
        if origin is None:
            raise ValueError(
                f"selector input has no training origin: {selector_input.origin_id}"
            )
        snapshot = snapshots_by_origin.get(selector_input.origin_id)
        if snapshot is None:
            raise ValueError(
                f"selector input has no feature snapshot: {selector_input.origin_id}"
            )
        _validate_training_input_links(selector_input, origin, snapshot)
        current_agent_bindings = tuple(
            zip(
                selector_input.agent_ids,
                selector_input.agent_record_digests,
                strict=True,
            )
        )
        if agent_bindings is None:
            agent_bindings = current_agent_bindings
        elif current_agent_bindings != agent_bindings:
            raise ValueError("training selector inputs must use one Agent identity set")
        if budget_digest is None:
            budget_digest = selector_input.budget_digest
        elif selector_input.budget_digest != budget_digest:
            raise ValueError("training selector inputs must use one budget")
        if feature_config_digest is None:
            feature_config_digest = snapshot.feature_config_digest
        elif snapshot.feature_config_digest != feature_config_digest:
            raise ValueError("training snapshots must use one feature configuration")
        input_ids.add(selector_input.selector_input_id)
        inputs_by_origin[selector_input.origin_id] = selector_input
    return inputs_by_origin


def _validate_training_input_links(
    selector_input: SelectorInput,
    origin: RollingOriginRecord,
    snapshot: FeatureSnapshotRecord,
) -> None:
    if (
        selector_input.task_pool_id != origin.task_pool_id
        or selector_input.task_pool_digest != origin.task_pool_digest
    ):
        raise ValueError("selector input task pool does not match its origin")
    if selector_input.eligible_task_check_refs != origin.history_task_check_refs:
        raise ValueError("selector input does not cover its exact origin history")
    if selector_input.origin_as_of_cutoff != origin.as_of_cutoff:
        raise ValueError("selector input cutoff does not match its origin")
    if selector_input.eligibility_mode != origin.eligibility_mode:
        raise ValueError("selector input eligibility mode does not match its origin")
    if selector_input.feature_snapshot_id != snapshot.feature_snapshot_id:
        raise ValueError("selector input does not bind its feature snapshot")
    if selector_input.feature_records_digest != snapshot.feature_records_digest:
        raise ValueError("selector input does not bind snapshot feature records")
    if selector_input.leakage_policy_digest != snapshot.leakage_policy_digest:
        raise ValueError("selector input leakage policy does not match its snapshot")
    if selector_input.feature_snapshot_lint_status != snapshot.leakage_lint_status:
        raise ValueError("selector input lint status does not match its snapshot")


def _validate_training_pre_origin_results(
    origins_by_id: Mapping[str, RollingOriginRecord],
    snapshots_by_origin: Mapping[str, FeatureSnapshotRecord],
    inputs_by_origin: Mapping[str, SelectorInput],
    pre_origin_results: Sequence[ResultRecord],
) -> None:
    result_by_binding: dict[tuple[str, str], ResultRecord] = {}
    for result in pre_origin_results:
        validation = validate_result(result)
        if not validation.ok:
            raise ValueError(
                f"pre-origin training result is invalid: {', '.join(validation.errors)}"
            )
        binding = (result.result_id, result.result_digest)
        if binding in result_by_binding:
            raise ValueError(f"duplicate pre-origin result binding: {result.result_id}")
        result_by_binding[binding] = result

    referenced_bindings: set[tuple[str, str]] = set()
    for origin_id, selector_input in inputs_by_origin.items():
        bindings = tuple(
            zip(
                selector_input.pre_origin_result_ids,
                selector_input.pre_origin_result_digests,
                strict=True,
            )
        )
        ensure_selector_input_result_evidence(
            selector_input,
            origins_by_id[origin_id],
            snapshots_by_origin[origin_id],
            pre_origin_results,
        )
        referenced_bindings.update(bindings)
    if set(result_by_binding) != referenced_bindings:
        raise ValueError(
            "pre_origin_results must exactly match selector input bindings"
        )


def _validated_training_selections(
    origins_by_id: Mapping[str, RollingOriginRecord],
    snapshots_by_origin: Mapping[str, FeatureSnapshotRecord],
    inputs_by_origin: Mapping[str, SelectorInput],
    experts: Mapping[str, SelectorRecord],
    selections: Sequence[BenchmarkSelectionRecord],
) -> tuple[
    Mapping[str, BenchmarkSelectionRecord],
    Mapping[str, Mapping[str, BenchmarkSelectionRecord]],
]:
    expert_by_id = {selector.selector_id: selector for selector in experts.values()}
    selections_by_id: dict[str, BenchmarkSelectionRecord] = {}
    selections_by_origin: dict[str, dict[str, BenchmarkSelectionRecord]] = {}
    for selection in selections:
        validation = validate_benchmark_selection(selection)
        if not validation.ok:
            raise ValueError(
                f"training selection is invalid: {', '.join(validation.errors)}"
            )
        if selection.selection_id in selections_by_id:
            raise ValueError(f"duplicate selection ID: {selection.selection_id}")
        origin = origins_by_id.get(selection.origin_id)
        if origin is None:
            raise ValueError(f"selection has no training origin: {selection.origin_id}")
        expert = expert_by_id.get(selection.selector_id)
        if expert is None:
            raise ValueError(
                f"selection uses unregistered expert: {selection.selector_id}"
            )
        if selection.selector_digest != expert.selector_digest:
            raise ValueError("selection selector digest does not match its expert")
        selector_input = inputs_by_origin[selection.origin_id]
        snapshot = snapshots_by_origin[selection.origin_id]
        if (
            selection.task_pool_id != origin.task_pool_id
            or selection.task_pool_digest != origin.task_pool_digest
            or selection.selection_input_digest != selector_input.selector_input_digest
            or selection.feature_snapshot_id != snapshot.feature_snapshot_id
            or selection.budget_digest != selector_input.budget_digest
            or selection.eligibility_mode != origin.eligibility_mode
        ):
            raise ValueError("selection provenance does not match its training input")
        ensure_selection_replay(selector_input, snapshot, expert, selection)
        origin_selections = selections_by_origin.setdefault(selection.origin_id, {})
        if selection.selector_id in origin_selections:
            raise ValueError(
                "duplicate selection for origin and expert: "
                f"{selection.origin_id}, {selection.selector_id}"
            )
        selections_by_id[selection.selection_id] = selection
        origin_selections[selection.selector_id] = selection

    expected_selector_ids = set(expert_by_id)
    for origin_id in origins_by_id:
        actual_selector_ids = set(selections_by_origin.get(origin_id, {}))
        if actual_selector_ids != expected_selector_ids:
            missing = sorted(expected_selector_ids - actual_selector_ids)
            extra = sorted(actual_selector_ids - expected_selector_ids)
            details = []
            if missing:
                details.append("missing " + ", ".join(missing))
            if extra:
                details.append("unknown " + ", ".join(extra))
            raise ValueError(
                f"origin {origin_id} must cover every expert: {'; '.join(details)}"
            )
    return selections_by_id, selections_by_origin


def _validated_training_matrices(
    origins_by_id: Mapping[str, RollingOriginRecord],
    inputs_by_origin: Mapping[str, SelectorInput],
    selections_by_id: Mapping[str, BenchmarkSelectionRecord],
    result_matrices: Sequence[ResultMatrix],
) -> Mapping[str, tuple[ResultMatrix, ResultMatrix]]:
    matrices_by_selection = _indexed_training_matrices(
        origins_by_id,
        inputs_by_origin,
        selections_by_id,
        result_matrices,
    )
    paired = _paired_training_matrices(matrices_by_selection, selections_by_id)
    _validate_training_future_evidence(paired, selections_by_id)
    return paired


def _indexed_training_matrices(
    origins_by_id: Mapping[str, RollingOriginRecord],
    inputs_by_origin: Mapping[str, SelectorInput],
    selections_by_id: Mapping[str, BenchmarkSelectionRecord],
    result_matrices: Sequence[ResultMatrix],
) -> dict[str, dict[str, ResultMatrix]]:
    matrices_by_selection: dict[str, dict[str, ResultMatrix]] = {}
    matrix_ids: set[str] = set()
    join_policy_digest: str | None = None
    denominator_policy_digest: str | None = None
    for matrix in result_matrices:
        validation = validate_result_matrix(matrix)
        if not validation.ok:
            raise ValueError(
                f"training result matrix is invalid: {', '.join(validation.errors)}"
            )
        if matrix.matrix_id in matrix_ids:
            raise ValueError(f"duplicate result matrix ID: {matrix.matrix_id}")
        selection = selections_by_id.get(matrix.selection_id)
        if selection is None:
            raise ValueError(
                f"result matrix has no training selection: {matrix.selection_id}"
            )
        origin = origins_by_id[selection.origin_id]
        selector_input = inputs_by_origin[selection.origin_id]
        _validate_training_matrix_provenance(
            matrix,
            selection,
            origin,
            selector_input,
        )
        if join_policy_digest is None:
            join_policy_digest = matrix.join_policy_digest
        elif matrix.join_policy_digest != join_policy_digest:
            raise ValueError("training matrices must use one join policy")
        if denominator_policy_digest is None:
            denominator_policy_digest = matrix.denominator_policy_digest
        elif matrix.denominator_policy_digest != denominator_policy_digest:
            raise ValueError("training matrices must use one denominator policy")
        roles = matrices_by_selection.setdefault(matrix.selection_id, {})
        if matrix.matrix_role in roles:
            raise ValueError(
                f"duplicate {matrix.matrix_role} matrix for {matrix.selection_id}"
            )
        roles[matrix.matrix_role] = matrix
        matrix_ids.add(matrix.matrix_id)
    return matrices_by_selection


def _validate_training_matrix_provenance(
    matrix: ResultMatrix,
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    selector_input: SelectorInput,
) -> None:
    if matrix.origin_id != selection.origin_id:
        raise ValueError("result matrix origin does not match its selection")
    if matrix.agent_ids != selector_input.agent_ids:
        raise ValueError("result matrix Agent set does not match selector input")
    expected_refs = (
        selection.selected_task_check_refs
        if matrix.matrix_role == "selected"
        else origin.future_holdout_task_check_refs
    )
    if matrix.task_check_refs != expected_refs:
        raise ValueError(
            f"{matrix.matrix_role} matrix denominator does not match provenance"
        )
    if error := matrix_denominator_error(matrix):
        raise ValueError(f"training result matrix is not scoreable: {error}")


def _paired_training_matrices(
    matrices_by_selection: Mapping[str, Mapping[str, ResultMatrix]],
    selections_by_id: Mapping[str, BenchmarkSelectionRecord],
) -> dict[str, tuple[ResultMatrix, ResultMatrix]]:
    paired: dict[str, tuple[ResultMatrix, ResultMatrix]] = {}
    for selection_id in selections_by_id:
        roles = matrices_by_selection.get(selection_id, {})
        if set(roles) != {"selected", "future_holdout"}:
            raise ValueError(
                f"selection {selection_id} must have selected and future matrices"
            )
        paired[selection_id] = (roles["selected"], roles["future_holdout"])
    return paired


def _validate_training_future_evidence(
    paired: Mapping[str, tuple[ResultMatrix, ResultMatrix]],
    selections_by_id: Mapping[str, BenchmarkSelectionRecord],
) -> None:
    future_evidence_by_origin: dict[str, str] = {}
    for selection_id, (_, future_matrix) in paired.items():
        origin_id = selections_by_id[selection_id].origin_id
        evidence_digest = _future_result_evidence_digest(future_matrix)
        existing = future_evidence_by_origin.setdefault(origin_id, evidence_digest)
        if existing != evidence_digest:
            raise ValueError(
                f"future matrices for origin {origin_id} must use the same Result evidence"
            )


def _validated_training_metrics(
    selections_by_id: Mapping[str, BenchmarkSelectionRecord],
    selections_by_origin: Mapping[str, Mapping[str, BenchmarkSelectionRecord]],
    matrices_by_selection: Mapping[str, tuple[ResultMatrix, ResultMatrix]],
    metrics: Sequence[MetricRecord],
) -> tuple[Mapping[str, float], ...]:
    metrics_by_selection, completeness_by_origin = _indexed_training_metrics(
        selections_by_id,
        matrices_by_selection,
        metrics,
    )
    _validate_training_metric_coverage(metrics_by_selection, selections_by_id)
    _validate_training_metric_completeness(completeness_by_origin)
    return _training_mae_rows(
        selections_by_origin,
        metrics_by_selection,
    )


def _indexed_training_metrics(
    selections_by_id: Mapping[str, BenchmarkSelectionRecord],
    matrices_by_selection: Mapping[str, tuple[ResultMatrix, ResultMatrix]],
    metrics: Sequence[MetricRecord],
) -> tuple[dict[str, MetricRecord], dict[str, set[str]]]:
    _ensure_supported_metric_protocols(metrics, label="training metric")
    metrics_by_selection: dict[str, MetricRecord] = {}
    metric_ids: set[str] = set()
    completeness_by_origin: dict[str, set[str]] = {}
    for metric in metrics:
        validation = validate_metric(metric)
        if not validation.ok:
            raise ValueError(
                f"training metric is invalid: {', '.join(validation.errors)}"
            )
        if metric.metric_id in metric_ids:
            raise ValueError(f"duplicate metric ID: {metric.metric_id}")
        if metric.selection_id in metrics_by_selection:
            raise ValueError(
                f"duplicate training metric for selection: {metric.selection_id}"
            )
        selection = selections_by_id.get(metric.selection_id)
        if selection is None:
            raise ValueError(f"metric has no training selection: {metric.selection_id}")
        selected_matrix, future_matrix = matrices_by_selection[metric.selection_id]
        _validate_training_metric_provenance(
            metric,
            selection,
            selected_matrix,
            future_matrix,
        )
        _validate_training_metric_value(
            metric,
            selection,
            selected_matrix,
            future_matrix,
        )
        metrics_by_selection[metric.selection_id] = metric
        metric_ids.add(metric.metric_id)
        completeness_by_origin.setdefault(metric.origin_id, set()).add(
            metric.completeness_state
        )
    return metrics_by_selection, completeness_by_origin


def _validate_training_metric_provenance(
    metric: MetricRecord,
    selection: BenchmarkSelectionRecord,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
) -> None:
    if (
        metric.origin_id != selection.origin_id
        or metric.selected_matrix_digest != selected_matrix.matrix_digest
        or metric.future_matrix_digest != future_matrix.matrix_digest
        or metric.join_policy_digest != selected_matrix.join_policy_digest
        or metric.denominator_policy_digest != selected_matrix.denominator_policy_digest
        or metric.budget_digest != selection.budget_digest
    ):
        raise ValueError("metric provenance does not match its training matrices")


def _validate_training_metric_value(
    metric: MetricRecord,
    selection: BenchmarkSelectionRecord,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
) -> None:
    if (
        metric.metric_name != "future_pass_rate_mae"
        or metric.metric_scope != "aggregate"
        or metric.aggregation_level != "all_agents"
    ):
        raise ValueError("training metrics must be aggregate future_pass_rate_mae")
    expected_completeness = _combined_completeness_state(selected_matrix, future_matrix)
    if metric.completeness_state != expected_completeness:
        raise ValueError("metric completeness does not match its matrices")
    expected_value = compute_selection_metric_values(
        selection, selected_matrix, future_matrix
    )["future_pass_rate_mae"]
    if metric.metric_value != expected_value:
        raise ValueError("metric value does not recompute from its matrices")


def _validate_training_metric_coverage(
    metrics_by_selection: Mapping[str, MetricRecord],
    selections_by_id: Mapping[str, BenchmarkSelectionRecord],
) -> None:

    if set(metrics_by_selection) != set(selections_by_id):
        missing = sorted(set(selections_by_id) - set(metrics_by_selection))
        extra = sorted(set(metrics_by_selection) - set(selections_by_id))
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unknown " + ", ".join(extra))
        raise ValueError(
            "metrics must exactly cover training selections: " + "; ".join(details)
        )


def _validate_training_metric_completeness(
    completeness_by_origin: Mapping[str, set[str]],
) -> None:
    for origin_id, states in completeness_by_origin.items():
        if len(states) != 1:
            raise ValueError(
                f"metrics for origin {origin_id} must have one completeness state"
            )


def _training_mae_rows(
    selections_by_origin: Mapping[str, Mapping[str, BenchmarkSelectionRecord]],
    metrics_by_selection: Mapping[str, MetricRecord],
) -> tuple[Mapping[str, float], ...]:
    return tuple(
        {
            selector_id: _normalized_mae(
                metrics_by_selection[selection.selection_id].metric_value
            )
            for selector_id, selection in selections_by_origin[origin_id].items()
        }
        for origin_id in sorted(selections_by_origin)
    )


def _validate_training_results(
    deployment_origin: RollingOriginRecord,
    matrices_by_selection: Mapping[str, tuple[ResultMatrix, ResultMatrix]],
    training_results: Sequence[ResultRecord],
) -> None:
    result_by_binding = _indexed_training_results(training_results)
    bound_pairs = _validated_matrix_result_bindings(
        matrices_by_selection,
        result_by_binding,
    )
    _validate_training_result_coverage(result_by_binding, bound_pairs)
    _validate_training_matrix_result_states(
        matrices_by_selection,
        training_results,
    )
    _validate_training_result_availability(deployment_origin, training_results)


def _validate_training_result_agent_identities(
    inputs_by_origin: Mapping[str, SelectorInput],
    training_results: Sequence[ResultRecord],
) -> None:
    selector_input = next(iter(inputs_by_origin.values()))
    frozen_agent_digests = dict(
        zip(
            selector_input.agent_ids,
            selector_input.agent_record_digests,
            strict=True,
        )
    )
    if any(
        result.agent_id not in frozen_agent_digests
        or canonical_digest(
            agent_record_from_cache_identity(
                result.agent_id,
                result.cache_identity,
            )
        )
        != frozen_agent_digests[result.agent_id]
        for result in training_results
    ):
        raise ValueError("training Results do not match frozen Agent identities")


def _validate_training_result_task_check_identities(
    results: Sequence[ResultRecord],
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
) -> None:
    task_by_id = {task.task_id: task for task in tasks}
    for result in results:
        task = task_by_id.get(result.task_id)
        check = checks.get(result.check_id)
        if (
            task is None
            or check is None
            or check.task_id != task.task_id
            or check.check_id not in task.check_ids
            or cache_identity_task_check_mismatches(
                result.cache_identity,
                task,
                check,
            )
        ):
            raise ValueError("training Results do not match frozen Task/Check records")


def _indexed_training_results(
    training_results: Sequence[ResultRecord],
) -> Mapping[tuple[str, str], ResultRecord]:
    result_by_binding: dict[tuple[str, str], ResultRecord] = {}
    for result in training_results:
        validation = validate_result(result)
        if not validation.ok:
            raise ValueError(
                f"training result is invalid: {', '.join(validation.errors)}"
            )
        binding = (result.result_id, result.result_digest)
        if binding in result_by_binding:
            raise ValueError(f"duplicate training result binding: {result.result_id}")
        result_by_binding[binding] = result
    return result_by_binding


def _validated_matrix_result_bindings(
    matrices_by_selection: Mapping[str, tuple[ResultMatrix, ResultMatrix]],
    result_by_binding: Mapping[tuple[str, str], ResultRecord],
) -> set[tuple[str, str]]:
    bound_pairs: set[tuple[str, str]] = set()
    cell_bindings: dict[tuple[str, str, str, str], tuple[object, ...]] = {}
    for matrices in matrices_by_selection.values():
        for matrix in matrices:
            for cell in matrix.cells:
                if cell.result_id is None and cell.result_digest is None:
                    continue
                binding = _validated_training_result_binding(cell, result_by_binding)
                cell_key = (
                    cell.agent_id,
                    cell.task_id,
                    cell.check_id,
                    cell.required_identity_digest,
                )
                cell_binding = (
                    cell.result_id,
                    cell.result_digest,
                    cell.outcome,
                )
                existing = cell_bindings.setdefault(cell_key, cell_binding)
                if existing != cell_binding:
                    raise ValueError(
                        "training matrices bind conflicting Results for one cell"
                    )
                bound_pairs.add(binding)
    return bound_pairs


def _validate_training_matrix_result_states(
    matrices_by_selection: Mapping[str, tuple[ResultMatrix, ResultMatrix]],
    training_results: Sequence[ResultRecord],
) -> None:
    for matrices in matrices_by_selection.values():
        for matrix in matrices:
            evidence_errors = result_matrix_evidence_errors(matrix, training_results)
            if evidence_errors:
                raise ValueError("; ".join(evidence_errors))


def _validated_training_result_binding(
    cell: ResultCellRef,
    result_by_binding: Mapping[tuple[str, str], ResultRecord],
) -> tuple[str, str]:
    if cell.result_id is None or cell.result_digest is None:
        raise ValueError("result matrix has an incomplete Result binding")
    binding = (cell.result_id, cell.result_digest)
    result = result_by_binding.get(binding)
    if result is None:
        raise ValueError(
            "result matrix binding is missing from training_results: " + cell.result_id
        )
    if result_cell_record_mismatches(cell, result):
        raise ValueError("training Result does not match its matrix cell identity")
    return binding


def _validate_training_result_coverage(
    result_by_binding: Mapping[tuple[str, str], ResultRecord],
    bound_pairs: set[tuple[str, str]],
) -> None:
    if set(result_by_binding) != bound_pairs:
        extra = sorted(set(result_by_binding) - bound_pairs)
        raise ValueError(
            "training_results must exactly match matrix bindings"
            + (f": extra {extra}" if extra else "")
        )


def _validate_training_result_availability(
    deployment_origin: RollingOriginRecord,
    training_results: Sequence[ResultRecord],
) -> None:
    if deployment_origin.eligibility_mode == "strict_prospective":
        deployment_cutoff = parse_utc_timestamp(deployment_origin.as_of_cutoff)
        late = sorted(
            result.result_id
            for result in training_results
            if parse_utc_timestamp(result.result_available_at) >= deployment_cutoff
        )
        if late:
            raise ValueError(
                "strict-prospective training Results must be available strictly "
                "before deployment cutoff: " + ", ".join(late)
            )


def _validated_rule_mixture_experts(
    expert_selectors: Sequence[SelectorRecord],
) -> Mapping[str, SelectorRecord]:
    expected_families = {"coverage", "random", "recency"}
    families = [selector.selector_family for selector in expert_selectors]
    if (
        len(expert_selectors) != len(expected_families)
        or set(families) != expected_families
    ):
        raise ValueError(
            "expert_selectors must contain exactly one coverage, random, and recency selector"
        )
    selector_ids = [selector.selector_id for selector in expert_selectors]
    if len(selector_ids) != len(set(selector_ids)):
        raise ValueError("expert selector IDs must be unique")
    for selector in expert_selectors:
        validation = validate_selector(selector)
        if not validation.ok:
            raise ValueError(
                f"expert selector is invalid: {', '.join(validation.errors)}"
            )
        ensure_selector_executable(selector)
    return {selector.selector_family: selector for selector in expert_selectors}


def _paired_mae_by_origin(
    registered_selector_digests: Mapping[str, str],
    selections: Sequence[BenchmarkSelectionRecord],
    mae_metrics: Sequence[MetricRecord],
    future_matrices: Sequence[ResultMatrix],
) -> tuple[Mapping[str, float], ...]:
    by_origin = _paired_mae_by_origin_mapping(
        registered_selector_digests,
        selections,
        mae_metrics,
        future_matrices,
    )
    return tuple(by_origin[origin_id] for origin_id in sorted(by_origin))


def _paired_mae_by_origin_mapping(
    registered_selector_digests: Mapping[str, str],
    selections: Sequence[BenchmarkSelectionRecord],
    mae_metrics: Sequence[MetricRecord],
    future_matrices: Sequence[ResultMatrix],
) -> Mapping[str, Mapping[str, float]]:
    if not selections and not mae_metrics and not future_matrices:
        return {}
    if not selections or not mae_metrics or not future_matrices:
        raise ValueError(
            "selections, MAE metrics, and future matrices must all be provided"
        )

    selection_evidence = _validated_paired_selections(
        registered_selector_digests,
        selections,
    )
    metric_evidence = _validated_paired_metrics(
        selection_evidence.by_id,
        mae_metrics,
    )
    _validate_paired_future_matrices(
        selection_evidence.by_id,
        metric_evidence.by_selection_id,
        future_matrices,
    )
    _validate_paired_metric_comparability(metric_evidence)

    return {
        origin_id: {
            selector_id: _normalized_mae(
                metric_evidence.by_selection_id[selection.selection_id].metric_value
            )
            for selector_id, selection in selection_evidence.by_origin[
                origin_id
            ].items()
        }
        for origin_id in selection_evidence.by_origin
    }


def _chronological_mae_rows(
    training_origins: Sequence[RollingOriginRecord],
    deployment_origin: RollingOriginRecord,
    selections: Sequence[BenchmarkSelectionRecord],
    mae_by_origin: Mapping[str, Mapping[str, float]],
) -> tuple[Mapping[str, float], ...]:
    if not training_origins:
        _ensure_deployment_origin_valid(deployment_origin)
        if mae_by_origin:
            raise ValueError("origins must exactly cover paired MAE origins")
        return ()
    origins_by_id = _validated_training_origins(
        deployment_origin,
        training_origins,
    )
    if set(origins_by_id) != set(mae_by_origin):
        raise ValueError("origins must exactly cover paired MAE origins")

    selection_by_origin: dict[str, BenchmarkSelectionRecord] = {}
    for selection in selections:
        selection_by_origin.setdefault(selection.origin_id, selection)
    for origin_id, origin in origins_by_id.items():
        selection = selection_by_origin[origin_id]
        if (origin.task_pool_id, origin.task_pool_digest) != (
            selection.task_pool_id,
            selection.task_pool_digest,
        ):
            raise ValueError("origin Task Pool does not match paired selections")

    chronological = sorted(
        origins_by_id.values(),
        key=lambda origin: parse_utc_timestamp(origin.as_of_cutoff),
    )
    cutoffs = tuple(
        parse_utc_timestamp(origin.as_of_cutoff) for origin in chronological
    )
    if len(cutoffs) != len(set(cutoffs)):
        raise ValueError("paired MAE origins must have unique as-of cutoffs")
    return tuple(mae_by_origin[origin.origin_id] for origin in chronological)


def _validated_paired_selections(
    registered_selector_digests: Mapping[str, str],
    selections: Sequence[BenchmarkSelectionRecord],
) -> _PairedSelectionEvidence:
    selections_by_id: dict[str, BenchmarkSelectionRecord] = {}
    selections_by_origin: dict[str, dict[str, BenchmarkSelectionRecord]] = {}
    selection_input_by_origin: dict[str, str] = {}
    task_pool_identities: set[tuple[str, str]] = set()
    budget_digests: set[str] = set()
    for selection in selections:
        validation = validate_benchmark_selection(selection)
        if not validation.ok:
            raise ValueError(f"selection is invalid: {', '.join(validation.errors)}")
        if selection.selector_id not in registered_selector_digests:
            raise ValueError(
                f"selection uses unregistered selector: {selection.selector_id}"
            )
        if (
            selection.selector_digest
            != registered_selector_digests[selection.selector_id]
        ):
            raise ValueError("selection selector digest does not match registration")
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
        missing_selector_ids = sorted(
            set(registered_selector_digests) - set(origin_selections)
        )
        if missing_selector_ids:
            raise ValueError(
                f"origin {origin_id} is missing registered selectors: {', '.join(missing_selector_ids)}"
            )
    return _PairedSelectionEvidence(selections_by_id, selections_by_origin)


def _validated_paired_metrics(
    selections_by_id: Mapping[str, BenchmarkSelectionRecord],
    mae_metrics: Sequence[MetricRecord],
) -> _PairedMetricEvidence:
    _ensure_supported_metric_protocols(mae_metrics, label="metric")
    metrics_by_selection_id: dict[str, MetricRecord] = {}
    metric_ids: set[str] = set()
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
        if (
            metric.metric_scope != "aggregate"
            or metric.aggregation_level != "all_agents"
        ):
            raise ValueError("future_pass_rate_mae metrics must aggregate all agents")
        if metric.completeness_state not in {"complete", "complete_with_exclusions"}:
            raise ValueError("future_pass_rate_mae metrics must be complete")
        metrics_by_selection_id[metric.selection_id] = metric
        metric_ids.add(metric.metric_id)
        join_policy_digests.add(metric.join_policy_digest)
        denominator_policy_digests.add(metric.denominator_policy_digest)
        completeness_by_origin.setdefault(metric.origin_id, set()).add(
            metric.completeness_state
        )

    missing_metric_selection_ids = sorted(
        set(selections_by_id) - set(metrics_by_selection_id)
    )
    if missing_metric_selection_ids:
        raise ValueError(
            "selections are missing MAE metrics: "
            + ", ".join(missing_metric_selection_ids)
        )
    return _PairedMetricEvidence(
        by_selection_id=metrics_by_selection_id,
        join_policy_digests=frozenset(join_policy_digests),
        denominator_policy_digests=frozenset(denominator_policy_digests),
        completeness_by_origin={
            origin_id: frozenset(states)
            for origin_id, states in completeness_by_origin.items()
        },
    )


def _ensure_supported_metric_protocols(
    metrics: Sequence[MetricRecord],
    *,
    label: str,
) -> None:
    if any(metric.metric_config_digest != METRIC_CONFIG_DIGEST for metric in metrics):
        raise ValueError(f"{label} uses an unsupported metric protocol")


def _validate_paired_future_matrices(
    selections_by_id: Mapping[str, BenchmarkSelectionRecord],
    metrics_by_selection_id: Mapping[str, MetricRecord],
    future_matrices: Sequence[ResultMatrix],
) -> None:
    future_matrices_by_selection_id: dict[str, ResultMatrix] = {}
    future_evidence_by_origin: dict[str, str] = {}
    for matrix in future_matrices:
        validation = validate_result_matrix(matrix)
        if not validation.ok:
            raise ValueError(
                f"future matrix is invalid: {', '.join(validation.errors)}"
            )
        if matrix.matrix_role != "future_holdout":
            raise ValueError("future matrices must have the future_holdout role")
        if error := matrix_denominator_error(matrix):
            raise ValueError(f"future matrix is not scoreable: {error}")
        if matrix.selection_id in future_matrices_by_selection_id:
            raise ValueError(
                f"duplicate future matrix for selection: {matrix.selection_id}"
            )
        selection = selections_by_id.get(matrix.selection_id)
        if selection is None:
            raise ValueError(
                f"future matrix has no matching selection: {matrix.selection_id}"
            )
        metric = metrics_by_selection_id[matrix.selection_id]
        if matrix.origin_id != selection.origin_id:
            raise ValueError("future matrix origin does not match its selection")
        if matrix.matrix_digest != metric.future_matrix_digest:
            raise ValueError("future matrix digest does not match its MAE metric")
        if matrix.join_policy_digest != metric.join_policy_digest:
            raise ValueError("future matrix join policy does not match its MAE metric")
        if matrix.denominator_policy_digest != metric.denominator_policy_digest:
            raise ValueError(
                "future matrix denominator policy does not match its MAE metric"
            )
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


def _validate_paired_metric_comparability(
    evidence: _PairedMetricEvidence,
) -> None:
    if len(evidence.join_policy_digests) != 1:
        raise ValueError("metrics must use one join policy")
    if len(evidence.denominator_policy_digests) != 1:
        raise ValueError("metrics must use one denominator policy")
    for origin_id, completeness_states in evidence.completeness_by_origin.items():
        if len(completeness_states) != 1:
            raise ValueError(
                f"metrics for origin {origin_id} must have one completeness state"
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
    provenance_error = _matrix_provenance_error(
        selection,
        origin,
        evaluation_cells,
        selected_matrix,
        future_matrix,
    )
    if provenance_error is not None:
        return provenance_error
    future_refs, denominator_error = _matrix_denominator_alignment(
        selection,
        origin,
        evaluation_cells,
        selected_matrix,
        future_matrix,
    )
    if denominator_error is not None:
        return denominator_error
    if not _matrix_cells_match_cell_set(
        selected_matrix, evaluation_cells, selection.selected_task_check_refs
    ):
        return "selected_matrix_cell_identity_mismatch"
    if not _matrix_cells_match_cell_set(future_matrix, evaluation_cells, future_refs):
        return "future_matrix_cell_identity_mismatch"
    return None


def _matrix_provenance_error(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    evaluation_cells: EvaluationCellSet,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
) -> str | None:
    if (
        selection.origin_id != origin.origin_id
        or evaluation_cells.origin_id != origin.origin_id
    ):
        return "origin_mismatch"
    if selection.eligibility_mode != origin.eligibility_mode:
        return "selection_eligibility_mode_mismatch"
    if evaluation_cells.selection_id != selection.selection_id:
        return "evaluation_cell_selection_mismatch"
    if (
        selected_matrix.matrix_role != "selected"
        or future_matrix.matrix_role != "future_holdout"
    ):
        return "matrix_role_mismatch"
    if (
        selected_matrix.origin_id != origin.origin_id
        or future_matrix.origin_id != origin.origin_id
    ):
        return "matrix_origin_mismatch"
    if (
        selected_matrix.selection_id != selection.selection_id
        or future_matrix.selection_id != selection.selection_id
    ):
        return "matrix_selection_mismatch"
    if selected_matrix.agent_ids != future_matrix.agent_ids:
        return "agent_set_mismatch"
    if selected_matrix.join_policy_digest != future_matrix.join_policy_digest:
        return "join_policy_mismatch"
    if (
        selected_matrix.denominator_policy_digest
        != future_matrix.denominator_policy_digest
    ):
        return "denominator_policy_mismatch"
    return None


def _matrix_denominator_alignment(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    evaluation_cells: EvaluationCellSet,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
) -> tuple[tuple[TaskCheckRef, ...], str | None]:
    if selected_matrix.task_check_refs != selection.selected_task_check_refs:
        return (), "selected_denominator_mismatch"
    if evaluation_cells.selected_task_check_refs != selection.selected_task_check_refs:
        return (), "evaluation_selected_denominator_mismatch"
    if origin.eligibility_mode == "strict_prospective":
        if evaluation_cells.future_task_pool_digest == origin.task_pool_digest:
            return (), "prospective_future_task_pool_mismatch"
        future_refs = evaluation_cells.future_task_check_refs
    else:
        if (
            evaluation_cells.future_task_pool_id != origin.task_pool_id
            or evaluation_cells.future_task_pool_digest != origin.task_pool_digest
        ):
            return (), "evaluation_future_task_pool_mismatch"
        if evaluation_cells.future_task_check_refs != (
            origin.future_holdout_task_check_refs
        ):
            return (), "evaluation_future_denominator_mismatch"
        if evaluation_cells.future_censored_task_check_refs != (
            origin.future_censored_task_check_refs
        ):
            return (), "evaluation_future_censoring_mismatch"
        future_refs = origin.future_holdout_task_check_refs
    if future_matrix.task_check_refs != future_refs:
        return (), "future_denominator_mismatch"
    return future_refs, None


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
    if (
        selection.task_pool_id != origin.task_pool_id
        or selection.task_pool_digest != origin.task_pool_digest
    ):
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


def _matrix_completeness_error(
    selected_matrix: ResultMatrix, future_matrix: ResultMatrix
) -> str | None:
    for matrix in (selected_matrix, future_matrix):
        if error := matrix_denominator_error(matrix):
            return error
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


def _pass_rates(
    matrix: ResultMatrix, weights: Mapping[str, float] | None = None
) -> Mapping[str, float]:
    rates: dict[str, float] = {}
    for agent_id in matrix.agent_ids:
        cells = [
            cell
            for cell in matrix.cells
            if cell.agent_id == agent_id and cell.cell_state == "result"
        ]
        if not cells:
            raise ValueError("result matrix has an empty Agent denominator")
        if any(cell.outcome not in {"pass", "fail", "invalid"} for cell in cells):
            raise ValueError(
                "result matrix cells must carry outcomes for metric computation"
            )
        if weights is None:
            passed = sum(1 for cell in cells if cell.outcome == "pass")
            rates[agent_id] = passed / len(cells)
            continue
        weighted_total = 0.0
        weighted_passed = 0.0
        for cell in cells:
            weight = weights.get(
                task_check_ref_key(TaskCheckRef(cell.task_id, cell.check_id))
            )
            if weight is None:
                raise ValueError("selected matrix cells must have selection weights")
            weighted_total += weight
            if cell.outcome == "pass":
                weighted_passed += weight
        if weighted_total == 0.0:
            raise ValueError("selected matrix has an empty weighted denominator")
        rates[agent_id] = weighted_passed / weighted_total
    return rates


def _mean_absolute_error(
    selected_rates: Mapping[str, float], future_rates: Mapping[str, float]
) -> float:
    agent_ids = sorted(set(selected_rates) & set(future_rates))
    if not agent_ids:
        return 0.0
    return sum(
        abs(selected_rates[agent_id] - future_rates[agent_id]) for agent_id in agent_ids
    ) / len(agent_ids)


def _pairwise_gap_mae(
    selected_rates: Mapping[str, float], future_rates: Mapping[str, float]
) -> float:
    agent_pairs = tuple(
        combinations(sorted(set(selected_rates) & set(future_rates)), 2)
    )
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


def _rank_agreement(
    selected_rates: Mapping[str, float], future_rates: Mapping[str, float]
) -> float:
    agent_pairs = tuple(
        combinations(sorted(set(selected_rates) & set(future_rates)), 2)
    )
    if not agent_pairs:
        return 1.0
    agreements = sum(
        _sign(selected_rates[left] - selected_rates[right])
        == _sign(future_rates[left] - future_rates[right])
        for left, right in agent_pairs
    )
    return agreements / len(agent_pairs)


def _recommendation_regret(
    selected_rates: Mapping[str, float], future_rates: Mapping[str, float]
) -> float:
    agent_ids = sorted(set(selected_rates) & set(future_rates))
    if not agent_ids:
        return 0.0
    recommended_agent = min(
        agent_ids, key=lambda agent_id: (-selected_rates[agent_id], agent_id)
    )
    return (
        max(future_rates[agent_id] for agent_id in agent_ids)
        - future_rates[recommended_agent]
    )


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
        if cell.cell_state in {"missing", "excluded"}
        or (cell.cell_state == "result" and cell.outcome == "invalid")
    )
    return invalid / len(matrix.cells)


def _metric_record(
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    evaluation_cells: EvaluationCellSet,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
    *,
    metric_scope: str,
    metric_name: str,
    metric_value: float,
    completeness_state: str,
    abstention_reason: str | None,
) -> MetricRecord:
    metric = MetricRecord(
        metric_id=f"metric_{canonical_digest((origin.origin_id, selection.selection_id, evaluation_cells.cell_set_digest, selected_matrix.matrix_digest, future_matrix.matrix_digest, selected_matrix.join_policy_digest, selected_matrix.denominator_policy_digest, metric_scope, metric_name, METRIC_CONFIG_DIGEST, selection.budget_digest, None, 'all_agents'))}",
        origin_id=origin.origin_id,
        selection_id=selection.selection_id,
        evaluation_cell_set_digest=evaluation_cells.cell_set_digest,
        selected_matrix_digest=selected_matrix.matrix_digest,
        future_matrix_digest=future_matrix.matrix_digest,
        join_policy_digest=selected_matrix.join_policy_digest,
        metric_config_digest=METRIC_CONFIG_DIGEST,
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
