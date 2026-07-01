"""Concrete Selection algorithms and selector fitting helpers."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Mapping, Sequence

from barcarolle.records import (
    BenchmarkSelectionRecord,
    RollingOriginRecord,
    SelectorInput,
    SelectorRecord,
    TaskCheckRef,
    canonical_digest,
    record_with_digest,
    task_check_ref_key,
    validate_benchmark_selection,
    validate_selector,
)

from .inputs import _ensure_selector_input_valid, _validated_training_selector_inputs
from .origin import _now


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


@dataclass(frozen=True)
class FitConfig:
    fit_config_digest: str
    selector_family: str = "learned_mixture"


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
    expert_weights: Mapping[str, float],
    selection_config: SelectionConfig,
) -> BenchmarkSelectionRecord:
    _ensure_selector_input_valid(selector_input)
    if selection_config.feature_snapshot_id != selector_input.feature_snapshot_id:
        raise ValueError("selection_config feature_snapshot_id must match selector_input")
    scored = []
    total_weight = sum(max(0.0, weight) for weight in expert_weights.values()) or 1.0
    refs = selector_input.eligible_task_check_refs
    for index, ref in enumerate(refs):
        recency = (index + 1) / max(1, len(refs))
        randomish = int(canonical_digest((selection_config.selection_config_digest, task_check_ref_key(ref)))[:8], 16) / 0xFFFFFFFF
        score = (
            expert_weights.get("recency", 0.0) * recency
            + expert_weights.get("random", 0.0) * randomish
            + expert_weights.get("coverage", 0.0)
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


def fit_learned_mixture(
    training_origins: Sequence[RollingOriginRecord],
    training_selector_inputs: Mapping[str, SelectorInput],
    baseline_selectors: Sequence[SelectorRecord],
    fit_config: FitConfig,
) -> SelectorRecord:
    ordered_inputs = _validated_training_selector_inputs(training_origins, training_selector_inputs)
    source_digests = (
        fit_config.fit_config_digest,
        canonical_digest(tuple(origin.origin_id for origin in training_origins)),
        canonical_digest(tuple(selector_input.selector_input_digest for selector_input in ordered_inputs)),
        canonical_digest(tuple(selector.config_digest for selector in baseline_selectors)),
    )
    return _selector_record(
        selector_family=fit_config.selector_family,
        selector_version="1",
        training_source_digests=source_digests,
        allowed_feature_classes=("task_metadata", "pre_origin_result"),
        config_digest=canonical_digest(source_digests),
    )


def fit_calibrated_weighting(
    training_origins: Sequence[RollingOriginRecord],
    training_selector_inputs: Mapping[str, SelectorInput],
    selection_config: SelectionConfig,
) -> SelectorRecord:
    ordered_inputs = _validated_training_selector_inputs(training_origins, training_selector_inputs)
    source_digests = (
        selection_config.selection_config_digest,
        canonical_digest(tuple(origin.origin_id for origin in training_origins)),
        canonical_digest(tuple(selector_input.selector_input_digest for selector_input in ordered_inputs)),
    )
    return _selector_record(
        selector_family="calibrated_weighting",
        selector_version="1",
        training_source_digests=source_digests,
        allowed_feature_classes=("task_metadata", "pre_origin_result"),
        config_digest=canonical_digest(source_digests),
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
    if selector.selector_family == "random":
        refs = list(selector_input.eligible_task_check_refs)
        Random(int(canonical_digest(selection_config.selection_config_digest)[:8], 16)).shuffle(refs)
        return _selection_from_refs(
            selector_input,
            refs[: _selection_count(selector_input)],
            selector_id=selector.selector_id,
            feature_snapshot_id=selection_config.feature_snapshot_id,
            eligibility_mode=selection_config.eligibility_mode,
            exposure_scope_digest=selection_config.exposure_scope_digest,
        )
    if selector.selector_family == "coverage":
        refs = _coverage_order(selector_input.eligible_task_check_refs, CoverageConfig(selection_config.selection_config_digest, {}))
        return _selection_from_refs(
            selector_input,
            refs[: _selection_count(selector_input)],
            selector_id=selector.selector_id,
            feature_snapshot_id=selection_config.feature_snapshot_id,
            eligibility_mode=selection_config.eligibility_mode,
            exposure_scope_digest=selection_config.exposure_scope_digest,
        )
    if selector.selector_family == "rule_mixture":
        return select_rule_mixture(selector_input, {"recency": 1.0, "coverage": 1.0}, selection_config)
    if selector.selector_family == "recency":
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


def _selector_record(
    selector_family: str,
    selector_version: str,
    training_source_digests: tuple[str, ...],
    allowed_feature_classes: tuple[str, ...],
    config_digest: str,
) -> SelectorRecord:
    selector = SelectorRecord(
        selector_id=f"selector_{canonical_digest((selector_family, selector_version, config_digest))}",
        selector_family=selector_family,
        selector_version=selector_version,
        training_source_digests=training_source_digests,
        allowed_feature_classes=allowed_feature_classes,
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
    grouped: dict[str, list[TaskCheckRef]] = {}
    for ref in refs:
        group = coverage_config.group_by_ref_key.get(task_check_ref_key(ref), ref.check_id)
        grouped.setdefault(group, []).append(ref)
    ordered: list[TaskCheckRef] = []
    while any(grouped.values()):
        for group in sorted(grouped):
            if grouped[group]:
                ordered.append(grouped[group].pop(0))
    return tuple(ordered)
