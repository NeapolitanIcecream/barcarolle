"""Concrete Selection algorithms and selector fitting helpers."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import isfinite
from random import Random
from typing import Mapping, Sequence

from barcarolle.records import (
    BenchmarkSelectionRecord,
    JSONValue,
    SelectorInput,
    SelectorRecord,
    TaskCheckRef,
    canonical_digest,
    record_with_digest,
    task_check_ref_key,
    validate_benchmark_selection,
    validate_selector,
)

from .inputs import _ensure_selector_input_valid
from .origin import _now


EXECUTABLE_SELECTOR_FAMILIES = frozenset({"coverage", "random", "recency", "rule_mixture"})
PLANNED_SELECTOR_FAMILIES = frozenset({"calibrated_weighting", "learned_mixture"})


@dataclass(frozen=True)
class SelectionConfig:
    selection_config_digest: str
    selector_id: str
    feature_snapshot_id: str
    eligibility_mode: str
    exposure_scope_digest: str | None = None


@dataclass(frozen=True)
class CoverageConfig:
    coverage_config_digest: str
    group_by_ref_key: Mapping[str, str]


def select_random(selector_input: SelectorInput, seed: int) -> BenchmarkSelectionRecord:
    _ensure_selector_input_valid(selector_input)
    refs = list(selector_input.eligible_task_check_refs)
    Random(seed).shuffle(refs)
    return _selection_from_refs(
        selector_input,
        refs[: _selection_count(selector_input)],
        selector_id="selector_random",
        feature_snapshot_id=selector_input.feature_snapshot_id,
        eligibility_mode="random",
        exposure_scope_digest=None,
    )


def select_recency(selector_input: SelectorInput) -> BenchmarkSelectionRecord:
    _ensure_selector_input_valid(selector_input)
    refs = tuple(reversed(selector_input.eligible_task_check_refs))
    return _selection_from_refs(
        selector_input,
        refs[: _selection_count(selector_input)],
        selector_id="selector_recency",
        feature_snapshot_id=selector_input.feature_snapshot_id,
        eligibility_mode="recency",
        exposure_scope_digest=None,
    )


def select_coverage(selector_input: SelectorInput, coverage_config: CoverageConfig) -> BenchmarkSelectionRecord:
    _ensure_selector_input_valid(selector_input)
    refs = _coverage_order(selector_input.eligible_task_check_refs, coverage_config)
    return _selection_from_refs(
        selector_input,
        refs[: _selection_count(selector_input)],
        selector_id="selector_coverage",
        feature_snapshot_id=selector_input.feature_snapshot_id,
        eligibility_mode="coverage",
        exposure_scope_digest=coverage_config.coverage_config_digest,
    )


def select_rule_mixture(
    selector_input: SelectorInput,
    selector_parameters: Mapping[str, JSONValue],
    selection_config: SelectionConfig,
) -> BenchmarkSelectionRecord:
    _ensure_selector_input_valid(selector_input)
    if selection_config.feature_snapshot_id != selector_input.feature_snapshot_id:
        raise ValueError("selection_config feature_snapshot_id must match selector_input")
    expert_weights, random_seed, group_by_ref_key = _rule_mixture_parameters(selector_parameters)
    scored = []
    refs = selector_input.eligible_task_check_refs
    total_weight = sum(expert_weights.values())
    coverage_config = CoverageConfig(canonical_digest(group_by_ref_key), group_by_ref_key)
    coverage_order = _coverage_order(refs, coverage_config)
    coverage_scores = {
        ref: (len(coverage_order) - rank) / max(1, len(coverage_order))
        for rank, ref in enumerate(coverage_order)
    }
    for index, ref in enumerate(refs):
        recency = (index + 1) / max(1, len(refs))
        randomish = int(canonical_digest((random_seed, task_check_ref_key(ref)))[:8], 16) / 0xFFFFFFFF
        score = (
            expert_weights.get("recency", 0.0) * recency
            + expert_weights.get("random", 0.0) * randomish
            + expert_weights.get("coverage", 0.0) * coverage_scores[ref]
        ) / total_weight
        scored.append((score, ref))
    ordered_refs = tuple(ref for _, ref in sorted(scored, key=lambda item: (-item[0], item[1].task_id, item[1].check_id)))
    return _selection_from_refs(
        selector_input,
        ordered_refs[: _selection_count(selector_input)],
        selector_id=selection_config.selector_id,
        feature_snapshot_id=selection_config.feature_snapshot_id,
        eligibility_mode=selection_config.eligibility_mode,
        exposure_scope_digest=selection_config.exposure_scope_digest,
    )


def select_with_selector(
    selector_input: SelectorInput,
    selector: SelectorRecord,
    selection_config: SelectionConfig,
) -> BenchmarkSelectionRecord:
    _ensure_selector_input_valid(selector_input)
    selector_validation = validate_selector(selector)
    if not selector_validation.ok:
        raise ValueError(f"selector is invalid: {', '.join(selector_validation.errors)}")
    if selection_config.selector_id != selector.selector_id:
        raise ValueError("selection_config selector_id must match selector")
    if selection_config.feature_snapshot_id != selector_input.feature_snapshot_id:
        raise ValueError("selection_config feature_snapshot_id must match selector_input")
    ensure_selector_executable(selector)
    if selector.selector_family == "random":
        seed = _random_parameters(selector.parameters)
        refs = list(selector_input.eligible_task_check_refs)
        Random(seed).shuffle(refs)
        return _selection_from_refs(
            selector_input,
            refs[: _selection_count(selector_input)],
            selector_id=selector.selector_id,
            feature_snapshot_id=selection_config.feature_snapshot_id,
            eligibility_mode=selection_config.eligibility_mode,
            exposure_scope_digest=selection_config.exposure_scope_digest,
        )
    if selector.selector_family == "coverage":
        group_by_ref_key = _coverage_parameters(selector.parameters)
        coverage_config = CoverageConfig(canonical_digest(group_by_ref_key), group_by_ref_key)
        refs = _coverage_order(selector_input.eligible_task_check_refs, coverage_config)
        return _selection_from_refs(
            selector_input,
            refs[: _selection_count(selector_input)],
            selector_id=selector.selector_id,
            feature_snapshot_id=selection_config.feature_snapshot_id,
            eligibility_mode=selection_config.eligibility_mode,
            exposure_scope_digest=selection_config.exposure_scope_digest,
        )
    if selector.selector_family == "rule_mixture":
        return select_rule_mixture(selector_input, selector.parameters, selection_config)
    if selector.selector_family == "recency":
        _recency_parameters(selector.parameters)
        refs = tuple(reversed(selector_input.eligible_task_check_refs))
        return _selection_from_refs(
            selector_input,
            refs[: _selection_count(selector_input)],
            selector_id=selector.selector_id,
            feature_snapshot_id=selection_config.feature_snapshot_id,
            eligibility_mode=selection_config.eligibility_mode,
            exposure_scope_digest=selection_config.exposure_scope_digest,
        )
    raise ValueError(f"unsupported selector family for selection: {selector.selector_family}")


def ensure_selector_family_executable(selector_family: str) -> None:
    if selector_family in PLANNED_SELECTOR_FAMILIES:
        raise NotImplementedError(f"{selector_family} selector is planned and not executable")
    if selector_family not in EXECUTABLE_SELECTOR_FAMILIES:
        raise ValueError(f"unsupported selector family: {selector_family}")


def ensure_selector_executable(selector: SelectorRecord) -> None:
    ensure_selector_family_executable(selector.selector_family)
    _validate_rule_parameters(selector.selector_family, selector.parameters)


def _selector_record(
    selector_family: str,
    selector_version: str,
    training_source_digests: tuple[str, ...],
    allowed_feature_classes: tuple[str, ...],
    parameters: Mapping[str, JSONValue],
) -> SelectorRecord:
    _validate_rule_parameters(selector_family, parameters)
    config_digest = canonical_digest(
        {"selector_family": selector_family, "parameters": parameters}
    )
    selector = SelectorRecord(
        selector_id=f"selector_{canonical_digest((selector_family, selector_version, training_source_digests, config_digest))}",
        selector_family=selector_family,
        selector_version=selector_version,
        training_source_digests=training_source_digests,
        allowed_feature_classes=allowed_feature_classes,
        parameters=parameters,
        config_digest=config_digest,
        created_at=_now(),
    )
    validation = validate_selector(selector)
    if not validation.ok:
        raise ValueError(f"selector is invalid: {', '.join(validation.errors)}")
    return selector


def _selection_from_refs(
    selector_input: SelectorInput,
    refs: Sequence[TaskCheckRef],
    *,
    selector_id: str,
    feature_snapshot_id: str,
    eligibility_mode: str,
    exposure_scope_digest: str | None,
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
    if feature_snapshot_id != selector_input.feature_snapshot_id:
        raise ValueError("feature_snapshot_id must match selector_input")
    weights = {task_check_ref_key(ref): 1.0 for ref in selected_refs}
    selection = BenchmarkSelectionRecord(
        selection_id=f"selection_{canonical_digest((selector_input.selector_input_digest, selector_id, tuple(task_check_ref_key(ref) for ref in selected_refs)))}",
        task_pool_id=selector_input.task_pool_id,
        task_pool_digest=selector_input.task_pool_digest or "",
        origin_id=selector_input.origin_id,
        selector_id=selector_id,
        selected_task_check_refs=selected_refs,
        selected_weights=weights,
        budget_digest=selector_input.budget_digest,
        selection_input_digest=selector_input.selector_input_digest,
        feature_snapshot_id=feature_snapshot_id,
        eligibility_mode=eligibility_mode,
        exposure_state="frozen",
        exposed_at=None,
        exposure_scope_digest=exposure_scope_digest,
        created_at=_now(),
        selection_digest="",
    )
    selection = record_with_digest(selection)
    validation = validate_benchmark_selection(selection)
    if not validation.ok:
        raise ValueError(f"benchmark selection is invalid: {', '.join(validation.errors)}")
    return selection


def _selection_count(selector_input: SelectorInput) -> int:
    _ensure_selector_input_valid(selector_input)
    if selector_input.selection_budget_limit is None:
        raise ValueError("selector_input selection_budget_limit is required")
    limit = selector_input.selection_budget_limit
    return max(1, min(limit, len(selector_input.eligible_task_check_refs)))


def _coverage_order(refs: Sequence[TaskCheckRef], coverage_config: CoverageConfig) -> tuple[TaskCheckRef, ...]:
    grouped: dict[str, deque[TaskCheckRef]] = {}
    for ref in refs:
        group = coverage_config.group_by_ref_key.get(task_check_ref_key(ref), ref.check_id)
        grouped.setdefault(group, deque()).append(ref)
    active_groups = deque(sorted(grouped))
    ordered: list[TaskCheckRef] = []
    while active_groups:
        group = active_groups.popleft()
        ordered.append(grouped[group].popleft())
        if grouped[group]:
            active_groups.append(group)
    return tuple(ordered)


def _normalized_nonnegative_weight(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    try:
        normalized = float(value)
    except OverflowError:
        return None
    return normalized if isfinite(normalized) and normalized >= 0.0 else None


def _validate_rule_parameters(
    selector_family: str,
    parameters: Mapping[str, JSONValue],
) -> None:
    if selector_family == "recency":
        _recency_parameters(parameters)
    elif selector_family == "random":
        _random_parameters(parameters)
    elif selector_family == "coverage":
        _coverage_parameters(parameters)
    elif selector_family == "rule_mixture":
        _rule_mixture_parameters(parameters)


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
        raise ValueError(f"unsupported rule-mixture experts: {', '.join(unsupported_experts)}")
    expert_weights: dict[str, float] = {}
    for name, weight in raw_weights.items():
        normalized_weight = _normalized_nonnegative_weight(weight)
        if normalized_weight is None:
            raise ValueError("expert_weights must be finite nonnegative numbers")
        expert_weights[name] = normalized_weight
    total_weight = sum(expert_weights.values())
    if not isfinite(total_weight) or total_weight <= 0.0:
        raise ValueError("expert_weights must include a positive coverage, random, or recency weight")
    random_seed = parameters["random_seed"]
    if isinstance(random_seed, bool) or not isinstance(random_seed, int):
        raise ValueError("rule_mixture random_seed must be an integer")
    groups = _string_mapping(parameters["group_by_ref_key"], "rule_mixture group_by_ref_key")
    return expert_weights, random_seed, groups


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
    return dict(value)
