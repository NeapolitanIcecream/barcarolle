"""Concrete Selection algorithms and selector fitting helpers."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, replace
from math import copysign, floor, fsum, isfinite, nextafter
from random import Random
from typing import Mapping, Sequence

from barcarolle.records import (
    BenchmarkSelectionRecord,
    FeatureSnapshotRecord,
    JSONValue,
    RollingOriginRecord,
    SelectorInput,
    SelectorRecord,
    TaskCheckRef,
    canonical_digest,
    make_selector_id,
    record_with_digest,
    task_check_ref_key,
    validate_benchmark_selection,
    validate_feature_snapshot,
    validate_rolling_origin,
    validate_selector,
)

from .inputs import _ensure_selector_input_valid
from .origin import _instant_gt, _now


EXECUTABLE_SELECTOR_FAMILIES = frozenset(
    {"coverage", "random", "recency", "rule_mixture", "stratified_forecast"}
)
FIXED_RULE_SELECTOR_FAMILIES = frozenset(
    {"coverage", "random", "recency", "stratified_forecast"}
)
_RULE_MIXTURE_SIMPLEX_FAMILIES = ("coverage", "random", "recency")
_RULE_MIXTURE_SIMPLEX_DENOMINATOR = 3
_RULE_MIXTURE_SIMPLEX_PROTOCOL = "rule_mixture_simplex_grid_v1"
_SELECTION_REPLAY_FIELDS = (
    "selection_id",
    "task_pool_id",
    "task_pool_digest",
    "origin_id",
    "selector_id",
    "selector_digest",
    "selected_task_check_refs",
    "selected_weights",
    "budget_digest",
    "selection_input_digest",
    "feature_snapshot_id",
    "eligibility_mode",
)


@dataclass(frozen=True)
class _StratifiedForecastPlan:
    selected_refs: tuple[TaskCheckRef, ...]
    selected_weights: Mapping[str, float]
    forecast_proportions: Mapping[str, float]
    quotas: Mapping[str, int]
    stratum_by_ref: Mapping[TaskCheckRef, str]
    uncapped_weight_by_stratum: Mapping[str, float]


def build_rule_selector(
    selector_family: str,
    parameters: Mapping[str, JSONValue] | None = None,
    *,
    allowed_feature_classes: tuple[str, ...] = (
        "task_metadata",
        "pre_origin_result",
    ),
) -> SelectorRecord:
    if selector_family not in FIXED_RULE_SELECTOR_FAMILIES:
        raise ValueError(f"unsupported fixed rule selector family: {selector_family}")
    return _selector_record(
        selector_family=selector_family,
        selector_version="1",
        training_source_digests=(),
        allowed_feature_classes=allowed_feature_classes,
        parameters=dict(parameters or {}),
    )


def build_rule_mixture_grid(
    *,
    random_seed: int,
    group_by_ref_key: Mapping[str, str],
    allowed_feature_classes: tuple[str, ...] = (
        "task_metadata",
        "pre_origin_result",
    ),
) -> tuple[SelectorRecord, ...]:
    """Build the fixed ten-point simplex grid used by ALG-003."""
    normalized_seed = _random_parameters({"seed": random_seed})
    normalized_groups = dict(
        _coverage_parameters({"group_by_ref_key": dict(group_by_ref_key)})
    )
    grid_digest = canonical_digest(
        {
            "protocol": _RULE_MIXTURE_SIMPLEX_PROTOCOL,
            "simplex_denominator": _RULE_MIXTURE_SIMPLEX_DENOMINATOR,
            "random_seed": normalized_seed,
            "group_by_ref_key": normalized_groups,
        }
    )
    return tuple(
        _selector_record(
            selector_family="rule_mixture",
            selector_version="simplex-grid-v1",
            training_source_digests=(grid_digest,),
            allowed_feature_classes=allowed_feature_classes,
            parameters={
                "expert_weights": dict(
                    zip(_RULE_MIXTURE_SIMPLEX_FAMILIES, point, strict=True)
                ),
                "random_seed": normalized_seed,
                "group_by_ref_key": normalized_groups,
            },
        )
        for point in _simplex_weight_points()
    )


def _simplex_weight_points() -> tuple[tuple[float, float, float], ...]:
    denominator = _RULE_MIXTURE_SIMPLEX_DENOMINATOR
    return tuple(
        (
            coverage_units / denominator,
            random_units / denominator,
            (denominator - coverage_units - random_units) / denominator,
        )
        for coverage_units in range(denominator + 1)
        for random_units in range(denominator - coverage_units + 1)
    )


def _rule_mixture_order(
    refs: Sequence[TaskCheckRef],
    selector_parameters: Mapping[str, JSONValue],
) -> tuple[TaskCheckRef, ...]:
    expert_weights, random_seed, group_by_ref_key = _rule_mixture_parameters(
        selector_parameters
    )
    scored = []
    total_weight = fsum(expert_weights.values())
    coverage_order = _coverage_order(refs, group_by_ref_key)
    coverage_scores = {
        ref: (len(coverage_order) - rank) / max(1, len(coverage_order))
        for rank, ref in enumerate(coverage_order)
    }
    random_order = _random_order(refs, random_seed)
    random_scores = {
        ref: (len(random_order) - rank) / max(1, len(random_order))
        for rank, ref in enumerate(random_order)
    }
    for index, ref in enumerate(refs):
        recency = (index + 1) / max(1, len(refs))
        score = (
            expert_weights.get("recency", 0.0) * recency
            + expert_weights.get("random", 0.0) * random_scores[ref]
            + expert_weights.get("coverage", 0.0) * coverage_scores[ref]
        ) / total_weight
        scored.append((score, ref))
    return tuple(
        ref
        for _, ref in sorted(
            scored, key=lambda item: (-item[0], item[1].task_id, item[1].check_id)
        )
    )


def select_with_selector(
    selector_input: SelectorInput,
    feature_snapshot: FeatureSnapshotRecord,
    selector: SelectorRecord,
) -> BenchmarkSelectionRecord:
    _ensure_selector_input_valid(selector_input)
    selector_validation = validate_selector(selector)
    if not selector_validation.ok:
        raise ValueError(
            f"selector is invalid: {', '.join(selector_validation.errors)}"
        )
    ensure_selector_executable(selector)
    _ensure_feature_snapshot_matches_selector_input(
        selector_input, feature_snapshot, selector
    )
    if selector.selector_family == "random":
        seed = _random_parameters(selector.parameters)
        refs = _random_order(selector_input.eligible_task_check_refs, seed)
        return _selection_from_refs(
            selector_input,
            refs[: _selection_count(selector_input)],
            selector_id=selector.selector_id,
            selector_digest=selector.selector_digest,
        )
    if selector.selector_family == "coverage":
        group_by_ref_key = _coverage_parameters(selector.parameters)
        refs = _coverage_order(
            selector_input.eligible_task_check_refs, group_by_ref_key
        )
        return _selection_from_refs(
            selector_input,
            refs[: _selection_count(selector_input)],
            selector_id=selector.selector_id,
            selector_digest=selector.selector_digest,
        )
    if selector.selector_family == "rule_mixture":
        refs = _rule_mixture_order(
            selector_input.eligible_task_check_refs, selector.parameters
        )
        return _selection_from_refs(
            selector_input,
            refs[: _selection_count(selector_input)],
            selector_id=selector.selector_id,
            selector_digest=selector.selector_digest,
        )
    if selector.selector_family == "stratified_forecast":
        plan = _stratified_forecast_plan(
            selector_input.eligible_task_check_refs,
            feature_snapshot,
            selector.parameters,
            _selection_count(selector_input),
        )
        return _selection_from_refs(
            selector_input,
            plan.selected_refs,
            selector_id=selector.selector_id,
            selector_digest=selector.selector_digest,
            selected_weights=plan.selected_weights,
        )
    if selector.selector_family == "recency":
        _recency_parameters(selector.parameters)
        refs = tuple(reversed(selector_input.eligible_task_check_refs))
        return _selection_from_refs(
            selector_input,
            refs[: _selection_count(selector_input)],
            selector_id=selector.selector_id,
            selector_digest=selector.selector_digest,
        )
    raise ValueError(
        f"unsupported selector family for selection: {selector.selector_family}"
    )


def ensure_selection_replay(
    selector_input: SelectorInput,
    feature_snapshot: FeatureSnapshotRecord,
    selector: SelectorRecord,
    selection: BenchmarkSelectionRecord,
) -> None:
    selection_validation = validate_benchmark_selection(selection)
    if not selection_validation.ok:
        raise ValueError(
            "selection is invalid: " + ", ".join(selection_validation.errors)
        )
    replayed = select_with_selector(selector_input, feature_snapshot, selector)
    mismatched = tuple(
        field_name
        for field_name in _SELECTION_REPLAY_FIELDS
        if getattr(selection, field_name) != getattr(replayed, field_name)
    )
    if mismatched:
        raise ValueError(
            "selection does not replay deterministically: " + ", ".join(mismatched)
        )


def _ensure_feature_snapshot_matches_selector_input(
    selector_input: SelectorInput,
    feature_snapshot: FeatureSnapshotRecord,
    selector: SelectorRecord,
) -> None:
    snapshot_validation = validate_feature_snapshot(feature_snapshot)
    if not snapshot_validation.ok:
        raise ValueError(
            "feature snapshot is invalid: " + ", ".join(snapshot_validation.errors)
        )
    if feature_snapshot.feature_snapshot_id != selector_input.feature_snapshot_id:
        raise ValueError("feature snapshot does not match selector input")
    if feature_snapshot.origin_id != selector_input.origin_id:
        raise ValueError("feature snapshot origin does not match selector input")
    if feature_snapshot.feature_records_digest != selector_input.feature_records_digest:
        raise ValueError("feature snapshot records do not match selector input")
    if feature_snapshot.leakage_policy_digest != selector_input.leakage_policy_digest:
        raise ValueError(
            "feature snapshot leakage policy does not match selector input"
        )
    if (
        feature_snapshot.leakage_lint_status
        != selector_input.feature_snapshot_lint_status
    ):
        raise ValueError("feature snapshot lint status does not match selector input")
    cutoff = selector_input.origin_as_of_cutoff or ""
    if any(
        _instant_gt(record.observed_at, cutoff)
        for record in feature_snapshot.feature_records
    ):
        raise ValueError("feature snapshot contains post-origin features")
    disallowed_classes = tuple(
        sorted(
            {
                record.leakage_class
                for record in feature_snapshot.feature_records
                if record.leakage_class not in selector.allowed_feature_classes
            }
        )
    )
    if disallowed_classes:
        raise ValueError(
            "feature classes not allowed by selector: " + ", ".join(disallowed_classes)
        )


def ensure_selector_family_executable(selector_family: str) -> None:
    if selector_family not in EXECUTABLE_SELECTOR_FAMILIES:
        raise ValueError(f"unsupported selector family: {selector_family}")


def ensure_selector_executable(selector: SelectorRecord) -> None:
    ensure_selector_family_executable(selector.selector_family)
    normalized_parameters = _normalized_rule_parameters(
        selector.selector_family, selector.parameters
    )
    if canonical_digest(selector.parameters) != canonical_digest(normalized_parameters):
        raise ValueError(
            f"{selector.selector_family} selector parameters must be canonical"
        )


def _selector_record(
    selector_family: str,
    selector_version: str,
    training_source_digests: tuple[str, ...],
    allowed_feature_classes: tuple[str, ...],
    parameters: Mapping[str, JSONValue],
) -> SelectorRecord:
    normalized_parameters = _normalized_rule_parameters(selector_family, parameters)
    if any(not isinstance(value, str) for value in allowed_feature_classes):
        raise ValueError("allowed_feature_classes must contain strings")
    normalized_feature_classes = tuple(sorted(set(allowed_feature_classes)))
    config_digest = canonical_digest(
        {"selector_family": selector_family, "parameters": normalized_parameters}
    )
    selector = SelectorRecord(
        selector_id="",
        selector_family=selector_family,
        selector_version=selector_version,
        training_source_digests=training_source_digests,
        allowed_feature_classes=normalized_feature_classes,
        parameters=normalized_parameters,
        config_digest=config_digest,
        created_at=_now(),
        selector_digest="",
    )
    selector = replace(selector, selector_id=make_selector_id(selector))
    selector = record_with_digest(selector)
    validation = validate_selector(selector)
    if not validation.ok:
        raise ValueError(f"selector is invalid: {', '.join(validation.errors)}")
    return selector


def _selection_from_refs(
    selector_input: SelectorInput,
    refs: Sequence[TaskCheckRef],
    *,
    selector_id: str,
    selector_digest: str,
    selected_weights: Mapping[str, float] | None = None,
) -> BenchmarkSelectionRecord:
    _ensure_selector_input_valid(selector_input)
    selected_refs = tuple(refs)
    if not selected_refs:
        raise ValueError("selection must include at least one Task/Check ref")
    eligible_refs = set(selector_input.eligible_task_check_refs)
    if any(ref not in eligible_refs for ref in selected_refs):
        raise ValueError("selection includes refs outside selector_input eligibility")
    if len(selected_refs) > _selection_count(selector_input):
        raise ValueError("selection exceeds selector_input budget")
    weights = (
        {task_check_ref_key(ref): 1.0 for ref in selected_refs}
        if selected_weights is None
        else dict(selected_weights)
    )
    selection = BenchmarkSelectionRecord(
        selection_id=f"selection_{canonical_digest((selector_input.selector_input_digest, selector_id, tuple(task_check_ref_key(ref) for ref in selected_refs)))}",
        task_pool_id=selector_input.task_pool_id,
        task_pool_digest=selector_input.task_pool_digest or "",
        origin_id=selector_input.origin_id,
        selector_id=selector_id,
        selector_digest=selector_digest,
        selected_task_check_refs=selected_refs,
        selected_weights=weights,
        budget_digest=selector_input.budget_digest,
        selection_input_digest=selector_input.selector_input_digest,
        feature_snapshot_id=selector_input.feature_snapshot_id,
        eligibility_mode=selector_input.eligibility_mode or "",
        created_at=_now(),
        selection_digest="",
    )
    selection = record_with_digest(selection)
    validation = validate_benchmark_selection(selection)
    if not validation.ok:
        raise ValueError(
            f"benchmark selection is invalid: {', '.join(validation.errors)}"
        )
    return selection


def _selection_count(selector_input: SelectorInput) -> int:
    _ensure_selector_input_valid(selector_input)
    if selector_input.selection_budget_limit is None:
        raise ValueError("selector_input selection_budget_limit is required")
    limit = selector_input.selection_budget_limit
    return max(1, min(limit, len(selector_input.eligible_task_check_refs)))


def _coverage_order(
    refs: Sequence[TaskCheckRef], group_by_ref_key: Mapping[str, str]
) -> tuple[TaskCheckRef, ...]:
    grouped: dict[str, deque[TaskCheckRef]] = {}
    for ref in refs:
        group = group_by_ref_key.get(task_check_ref_key(ref), ref.check_id)
        grouped.setdefault(group, deque()).append(ref)
    active_groups = deque(sorted(grouped))
    ordered: list[TaskCheckRef] = []
    while active_groups:
        group = active_groups.popleft()
        ordered.append(grouped[group].popleft())
        if grouped[group]:
            active_groups.append(group)
    return tuple(ordered)


def _random_order(refs: Sequence[TaskCheckRef], seed: int) -> tuple[TaskCheckRef, ...]:
    ordered = list(refs)
    Random(seed).shuffle(ordered)
    return tuple(ordered)


def _stratified_forecast_plan(
    refs: Sequence[TaskCheckRef],
    feature_snapshot: FeatureSnapshotRecord,
    parameters: Mapping[str, JSONValue],
    selection_count: int,
) -> _StratifiedForecastPlan:
    alpha, trailing_ref_count, seed, weight_cap = _stratified_forecast_parameters(
        parameters
    )
    stratum_by_ref = _task_strata(refs, feature_snapshot)
    strata = tuple(sorted(set(stratum_by_ref.values())))
    trailing_refs = tuple(refs)[-min(trailing_ref_count, len(refs)) :]
    trailing_counts = Counter(stratum_by_ref[ref] for ref in trailing_refs)
    denominator = len(trailing_refs) + alpha * len(strata)
    forecast = {
        stratum: (trailing_counts[stratum] + alpha) / denominator for stratum in strata
    }
    refs_by_stratum = {
        stratum: tuple(ref for ref in refs if stratum_by_ref[ref] == stratum)
        for stratum in strata
    }
    quotas = _capacity_constrained_largest_remainder(
        selection_count,
        forecast,
        {
            stratum: len(stratum_refs)
            for stratum, stratum_refs in refs_by_stratum.items()
        },
    )
    selected_refs = tuple(
        ref
        for stratum in strata
        for ref in sorted(
            refs_by_stratum[stratum],
            key=lambda item: (
                canonical_digest((seed, task_check_ref_key(item))),
                task_check_ref_key(item),
            ),
        )[: quotas[stratum]]
    )
    selected_share = {
        stratum: quotas[stratum] / selection_count
        for stratum in strata
        if quotas[stratum]
    }
    uncapped_weights = {
        stratum: forecast[stratum] / selected_share[stratum]
        for stratum in selected_share
    }
    selected_weights = {
        task_check_ref_key(ref): (
            1.0
            if weight_cap is None
            else min(weight_cap, uncapped_weights[stratum_by_ref[ref]])
        )
        for ref in selected_refs
    }
    return _StratifiedForecastPlan(
        selected_refs,
        selected_weights,
        forecast,
        quotas,
        stratum_by_ref,
        uncapped_weights,
    )


def _task_strata(
    refs: Sequence[TaskCheckRef], snapshot: FeatureSnapshotRecord
) -> Mapping[TaskCheckRef, str]:
    eligible_refs = set(refs)
    stratum_by_ref: dict[TaskCheckRef, str] = {}
    for record in snapshot.feature_records:
        if record.feature_name != "task_stratum":
            continue
        ref = TaskCheckRef(record.task_id or "", record.check_id or "")
        if (
            record.feature_scope != "task"
            or record.leakage_class != "task_metadata"
            or ref not in eligible_refs
            or not isinstance(record.value, str)
            or not record.value.strip()
            or ref in stratum_by_ref
        ):
            raise ValueError(
                "stratified_forecast requires exactly one task_stratum feature "
                "for every eligible Task/Check ref"
            )
        stratum_by_ref[ref] = record.value
    if set(stratum_by_ref) != eligible_refs:
        raise ValueError(
            "stratified_forecast requires exactly one task_stratum feature "
            "for every eligible Task/Check ref"
        )
    return stratum_by_ref


def _capacity_constrained_largest_remainder(
    target_count: int,
    proportions: Mapping[str, float],
    capacities: Mapping[str, int],
) -> Mapping[str, int]:
    exact = {
        stratum: target_count * proportion
        for stratum, proportion in proportions.items()
    }
    quotas = {
        stratum: min(capacities[stratum], floor(exact[stratum]))
        for stratum in proportions
    }
    while sum(quotas.values()) < target_count:
        available = tuple(
            stratum for stratum in proportions if quotas[stratum] < capacities[stratum]
        )
        if not available:
            raise ValueError("stratified quota allocation exceeds available refs")
        stratum = min(
            available,
            key=lambda item: (
                -(exact[item] - quotas[item]),
                -proportions[item],
                item,
            ),
        )
        quotas[stratum] += 1
    return quotas


def summarize_stratified_forecast(
    selector_input: SelectorInput,
    feature_snapshot: FeatureSnapshotRecord,
    selector: SelectorRecord,
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    future_stratum_by_ref_key: Mapping[str, str],
) -> Mapping[str, object]:
    """Return replay-checked composition diagnostics without opening outcomes."""
    plan, future_keys, weight_cap = _validated_stratified_summary_inputs(
        selector_input,
        feature_snapshot,
        selector,
        selection,
        origin,
        future_stratum_by_ref_key,
    )
    future_proportions = _stratum_proportions(
        tuple(future_stratum_by_ref_key[key] for key in future_keys)
    )
    selected_proportions = _stratum_proportions(
        tuple(plan.stratum_by_ref[ref] for ref in selection.selected_task_check_refs)
    )
    weighted_proportions = _weighted_stratum_proportions(selection, plan)
    weights = tuple(selection.selected_weights.values())
    effective_sample_size = _effective_sample_size(weights)
    return {
        "protocol_version": "stratified_forecast_diagnostics_v1",
        "forecast_proportions": dict(plan.forecast_proportions),
        "future_proportions": future_proportions,
        "quota_by_stratum": dict(plan.quotas),
        "forecast_proportion_tv_error": _proportion_tv_error(
            plan.forecast_proportions, future_proportions
        ),
        "unweighted_selected_proportion_tv_error": _proportion_tv_error(
            selected_proportions, future_proportions
        ),
        "post_stratified_proportion_tv_error": _proportion_tv_error(
            weighted_proportions, future_proportions
        ),
        "effective_sample_size": effective_sample_size,
        "effective_sample_fraction": effective_sample_size / len(weights),
        "maximum_selected_weight": max(weights),
        "configured_weight_cap": weight_cap,
        "capped_selected_fraction": _capped_selected_fraction(plan, weight_cap),
    }


def _validated_stratified_summary_inputs(
    selector_input: SelectorInput,
    feature_snapshot: FeatureSnapshotRecord,
    selector: SelectorRecord,
    selection: BenchmarkSelectionRecord,
    origin: RollingOriginRecord,
    future_stratum_by_ref_key: Mapping[str, str],
) -> tuple[_StratifiedForecastPlan, tuple[str, ...], float | None]:
    origin_validation = validate_rolling_origin(origin)
    if not origin_validation.ok:
        raise ValueError(f"origin is invalid: {', '.join(origin_validation.errors)}")
    if (
        origin.origin_id != selector_input.origin_id
        or origin.history_task_check_refs != selector_input.eligible_task_check_refs
    ):
        raise ValueError("origin does not match stratified selector input")
    if selector.selector_family != "stratified_forecast":
        raise ValueError("stratified forecast summary requires its selector family")
    ensure_selection_replay(selector_input, feature_snapshot, selector, selection)

    future_keys = tuple(
        task_check_ref_key(ref) for ref in origin.future_holdout_task_check_refs
    )
    if not future_keys:
        raise ValueError("stratified forecast summary requires future refs")
    if set(future_stratum_by_ref_key) != set(future_keys) or any(
        not isinstance(value, str) or not value.strip()
        for value in future_stratum_by_ref_key.values()
    ):
        raise ValueError("future strata must exactly cover future Task/Check refs")

    plan = _stratified_forecast_plan(
        selector_input.eligible_task_check_refs,
        feature_snapshot,
        selector.parameters,
        len(selection.selected_task_check_refs),
    )
    _, _, _, weight_cap = _stratified_forecast_parameters(selector.parameters)
    return plan, future_keys, weight_cap


def _stratum_proportions(strata: Sequence[str]) -> Mapping[str, float]:
    counts = Counter(strata)
    return {stratum: count / len(strata) for stratum, count in sorted(counts.items())}


def _weighted_stratum_proportions(
    selection: BenchmarkSelectionRecord,
    plan: _StratifiedForecastPlan,
) -> Mapping[str, float]:
    weighted_totals: dict[str, float] = {}
    for ref in selection.selected_task_check_refs:
        stratum = plan.stratum_by_ref[ref]
        weighted_totals[stratum] = (
            weighted_totals.get(stratum, 0.0)
            + selection.selected_weights[task_check_ref_key(ref)]
        )
    total_weight = fsum(weighted_totals.values())
    weighted_proportions = {
        stratum: weight / total_weight
        for stratum, weight in sorted(weighted_totals.items())
    }
    return weighted_proportions


def _effective_sample_size(weights: Sequence[float]) -> float:
    return fsum(weights) ** 2 / fsum(weight * weight for weight in weights)


def _capped_selected_fraction(
    plan: _StratifiedForecastPlan,
    weight_cap: float | None,
) -> float:
    if weight_cap is None:
        return 0.0
    capped_count = sum(
        plan.quotas[stratum]
        for stratum, uncapped in plan.uncapped_weight_by_stratum.items()
        if uncapped > weight_cap
    )
    return capped_count / len(plan.selected_refs)


def _proportion_tv_error(
    first: Mapping[str, float], second: Mapping[str, float]
) -> float:
    return 0.5 * fsum(
        abs(first.get(stratum, 0.0) - second.get(stratum, 0.0))
        for stratum in set(first) | set(second)
    )


def _normalized_nonnegative_weight(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    try:
        normalized = float(value)
    except OverflowError:
        return None
    return normalized if isfinite(normalized) and normalized >= 0.0 else None


def _normalized_rule_parameters(
    selector_family: str,
    parameters: Mapping[str, JSONValue],
) -> dict[str, JSONValue]:
    if selector_family == "recency":
        _recency_parameters(parameters)
        return {}
    if selector_family == "random":
        return {"seed": _random_parameters(parameters)}
    if selector_family == "coverage":
        groups = _coverage_parameters(parameters)
        return {
            "group_by_ref_key": {key: groups[key] for key in sorted(groups)},
        }
    if selector_family == "rule_mixture":
        weights, seed, groups = _rule_mixture_parameters(parameters)
        return {
            "expert_weights": _normalized_rule_mixture_weights(weights),
            "random_seed": seed,
            "group_by_ref_key": {key: groups[key] for key in sorted(groups)},
        }
    if selector_family == "stratified_forecast":
        alpha, trailing_ref_count, seed, weight_cap = _stratified_forecast_parameters(
            parameters
        )
        return {
            "dirichlet_alpha": alpha,
            "trailing_ref_count": trailing_ref_count,
            "seed": seed,
            "weight_cap": weight_cap,
        }
    raise ValueError(f"unsupported selector family: {selector_family}")


def _normalized_rule_mixture_weights(
    weights: Mapping[str, float],
) -> dict[str, float]:
    ordered = [weights.get(family, 0.0) for family in _RULE_MIXTURE_SIMPLEX_FAMILIES]
    if set(weights) == set(_RULE_MIXTURE_SIMPLEX_FAMILIES) and fsum(ordered) == 1.0:
        return dict(zip(_RULE_MIXTURE_SIMPLEX_FAMILIES, map(abs, ordered), strict=True))
    total_weight = fsum(ordered)
    normalized = [weight / total_weight for weight in ordered]
    correction_index = max(range(len(normalized)), key=normalized.__getitem__)
    normalized[correction_index] = 0.0
    normalized[correction_index] = 1.0 - fsum(normalized)
    normalized_total = fsum(normalized)
    if normalized_total != 1.0:
        normalized[correction_index] = nextafter(
            normalized[correction_index],
            copysign(float("inf"), 1.0 - normalized_total),
        )
    return dict(zip(_RULE_MIXTURE_SIMPLEX_FAMILIES, map(abs, normalized), strict=True))


def _recency_parameters(parameters: Mapping[str, JSONValue]) -> None:
    if parameters:
        raise ValueError("recency selector parameters must be empty")


def _random_parameters(parameters: Mapping[str, JSONValue]) -> int:
    _require_parameter_keys(parameters, {"seed"}, "random")
    seed = parameters["seed"]
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("random selector seed must be an integer")
    return seed


def _coverage_parameters(parameters: Mapping[str, JSONValue]) -> Mapping[str, str]:
    _require_parameter_keys(parameters, {"group_by_ref_key"}, "coverage")
    return _string_mapping(parameters["group_by_ref_key"], "coverage group_by_ref_key")


def _rule_mixture_parameters(
    parameters: Mapping[str, JSONValue],
) -> tuple[Mapping[str, float], int, Mapping[str, str]]:
    _require_parameter_keys(
        parameters,
        {"expert_weights", "random_seed", "group_by_ref_key"},
        "rule_mixture",
    )
    raw_weights = parameters["expert_weights"]
    if not isinstance(raw_weights, Mapping):
        raise ValueError("rule_mixture expert_weights must be a mapping")
    if any(not isinstance(name, str) for name in raw_weights):
        raise ValueError("rule_mixture expert_weights keys must be strings")
    supported_experts = {"coverage", "random", "recency"}
    unsupported_experts = sorted(set(raw_weights) - supported_experts)
    if unsupported_experts:
        raise ValueError(
            f"unsupported rule-mixture experts: {', '.join(unsupported_experts)}"
        )
    expert_weights: dict[str, float] = {}
    for name, weight in raw_weights.items():
        normalized_weight = _normalized_nonnegative_weight(weight)
        if normalized_weight is None:
            raise ValueError("expert_weights must be finite nonnegative numbers")
        expert_weights[name] = normalized_weight
    total_weight = sum(expert_weights.values())
    if not isfinite(total_weight) or total_weight <= 0.0:
        raise ValueError(
            "expert_weights must include a positive coverage, random, or recency weight"
        )
    random_seed = parameters["random_seed"]
    if isinstance(random_seed, bool) or not isinstance(random_seed, int):
        raise ValueError("rule_mixture random_seed must be an integer")
    groups = _string_mapping(
        parameters["group_by_ref_key"], "rule_mixture group_by_ref_key"
    )
    return expert_weights, random_seed, groups


def _stratified_forecast_parameters(
    parameters: Mapping[str, JSONValue],
) -> tuple[float, int, int, float | None]:
    _require_parameter_keys(
        parameters,
        {"dirichlet_alpha", "trailing_ref_count", "seed", "weight_cap"},
        "stratified_forecast",
    )
    alpha = _normalized_nonnegative_weight(parameters["dirichlet_alpha"])
    if alpha is None or alpha <= 0.0:
        raise ValueError("stratified_forecast dirichlet_alpha must be positive")
    trailing_ref_count = parameters["trailing_ref_count"]
    if (
        isinstance(trailing_ref_count, bool)
        or not isinstance(trailing_ref_count, int)
        or trailing_ref_count <= 0
    ):
        raise ValueError(
            "stratified_forecast trailing_ref_count must be a positive integer"
        )
    seed = parameters["seed"]
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("stratified_forecast seed must be an integer")
    raw_weight_cap = parameters["weight_cap"]
    weight_cap = (
        None
        if raw_weight_cap is None
        else _normalized_nonnegative_weight(raw_weight_cap)
    )
    if raw_weight_cap is not None and (weight_cap is None or weight_cap < 1.0):
        raise ValueError(
            "stratified_forecast weight_cap must be null or a finite number at least one"
        )
    return alpha, trailing_ref_count, seed, weight_cap


def _require_parameter_keys(
    parameters: Mapping[str, JSONValue],
    expected: set[str],
    selector_family: str,
) -> None:
    if set(parameters) != expected:
        raise ValueError(
            f"{selector_family} selector parameters must contain exactly: {', '.join(sorted(expected)) or 'no keys'}"
        )


def _string_mapping(value: JSONValue, label: str) -> Mapping[str, str]:
    if not isinstance(value, Mapping) or any(
        not isinstance(key, str) or not isinstance(item, str)
        for key, item in value.items()
    ):
        raise ValueError(f"{label} must map strings to strings")
    return {
        key: item
        for key, item in value.items()
        if isinstance(key, str) and isinstance(item, str)
    }
