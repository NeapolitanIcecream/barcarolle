#!/usr/bin/env python3
"""Measure the offline Selector landscape without new Agent executions."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
import json
import math
from math import comb
from pathlib import Path
import random
import sys
from typing import Any, cast


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import TaskRecord, canonical_digest, canonical_json
from examples.offline_selector_study import study


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "landscape-plan.json"
DEFAULT_AMENDMENT = HERE / "landscape-amendment-1.json"
DEFAULT_OUTPUT = HERE / "landscape-results.json"
DEFAULT_EMBEDDINGS = (
    study.REPOSITORY_ROOT
    / "outputs/research/2026-07-27-selection-landscape"
    / "task-text-embeddings.json"
)
BOOTSTRAP_SEED = 20_260_727
BOOTSTRAP_RESAMPLES = 10_000
FIXED_SEED_AUDIT_COUNT = 100_000
_ROUND_DIGITS = 12
_Z_80 = 0.8416212335729143
_Z_975 = 1.959963984540054


@dataclass(frozen=True)
class OriginView:
    origin_number: int
    history_task_ids: tuple[str, ...]
    future_task_ids: tuple[str, ...]
    coverage_task_ids: tuple[str, ...]
    recency_task_ids: tuple[str, ...]
    history_strata: tuple[str, ...]


@dataclass(frozen=True)
class MetricValues:
    future_pass_rate_mae: float
    pairwise_gap_mae: float
    rank_agreement: float
    recommendation_regret: float


@dataclass(frozen=True)
class EmbeddingData:
    model: str
    usage: Mapping[str, object]
    dimensions: int
    task_ids: tuple[str, ...]
    vectors: tuple[tuple[float, ...], ...]
    artifact_sha256: str


def load_landscape_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("landscape plan must be a JSON object")
    if payload.get("schema_version") != "barcarolle_selection_landscape_plan_v1":
        raise ValueError("landscape plan schema is not supported")
    digest = payload.get("landscape_plan_digest")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "landscape_plan_digest"}
    )
    if digest != expected:
        raise ValueError("landscape plan digest does not match its content")
    return payload


def load_landscape_amendment(
    path: Path,
    plan: Mapping[str, Any],
) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("landscape amendment must be a JSON object")
    if payload.get("schema_version") != "barcarolle_selection_landscape_amendment_v1":
        raise ValueError("landscape amendment schema is not supported")
    digest = payload.get("landscape_amendment_digest")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "landscape_amendment_digest"
        }
    )
    if digest != expected:
        raise ValueError("landscape amendment digest does not match its content")
    if payload.get("study_id") != plan.get("study_id"):
        raise ValueError("landscape amendment does not bind the study")
    if payload.get("previous_landscape_plan_digest") != plan.get(
        "landscape_plan_digest"
    ):
        raise ValueError("landscape amendment does not bind the plan")
    return payload


def exact_random_loss_pmf(
    history_outcomes: Sequence[tuple[int, int]],
    future_rates: tuple[float, float],
    selection_budget: int,
) -> Mapping[float, float]:
    """Return the exact loss PMF for a uniform fixed-size Task subset."""
    if selection_budget <= 0 or selection_budget > len(history_outcomes):
        raise ValueError("selection budget must fit the history")
    categories = ((0, 0), (0, 1), (1, 0), (1, 1))
    counts = Counter(history_outcomes)
    denominator = comb(len(history_outcomes), selection_budget)
    pmf: dict[float, float] = defaultdict(float)
    for selected_counts in _bounded_compositions(
        tuple(counts[category] for category in categories),
        selection_budget,
    ):
        ways = math.prod(
            comb(counts[category], selected_count)
            for category, selected_count in zip(
                categories,
                selected_counts,
                strict=True,
            )
        )
        selected_rates = tuple(
            sum(
                selected_count * category[agent_index]
                for selected_count, category in zip(
                    selected_counts,
                    categories,
                    strict=True,
                )
            )
            / selection_budget
            for agent_index in range(2)
        )
        loss = _rounded(_mean_absolute_error(selected_rates, future_rates))
        pmf[loss] += ways / denominator
    if not math.isclose(sum(pmf.values()), 1.0, abs_tol=1e-12):
        raise ValueError("exact random loss PMF does not normalize")
    return dict(sorted(pmf.items()))


def _bounded_compositions(
    capacities: tuple[int, ...],
    total: int,
) -> Iterable[tuple[int, ...]]:
    def visit(
        index: int, remaining: int, prefix: tuple[int, ...]
    ) -> Iterable[tuple[int, ...]]:
        if index == len(capacities) - 1:
            if 0 <= remaining <= capacities[index]:
                yield (*prefix, remaining)
            return
        for value in range(min(capacities[index], remaining) + 1):
            yield from visit(index + 1, remaining - value, (*prefix, value))

    return visit(0, total, ())


def convolve_macro_pmfs(
    origin_pmfs: Sequence[Mapping[float, float]],
) -> Mapping[float, float]:
    if not origin_pmfs:
        raise ValueError("at least one Origin PMF is required")
    total_pmf: dict[float, float] = {0.0: 1.0}
    for origin_pmf in origin_pmfs:
        combined: dict[float, float] = defaultdict(float)
        for left, left_probability in total_pmf.items():
            for right, right_probability in origin_pmf.items():
                combined[_rounded(left + right)] += left_probability * right_probability
        total_pmf = combined
    macro_pmf: dict[float, float] = defaultdict(float)
    for total_loss, probability in total_pmf.items():
        macro_pmf[_rounded(total_loss / len(origin_pmfs))] += probability
    if not math.isclose(sum(macro_pmf.values()), 1.0, abs_tol=1e-10):
        raise ValueError("macro random loss PMF does not normalize")
    return dict(sorted(macro_pmf.items()))


def distribution_quantile(pmf: Mapping[float, float], probability: float) -> float:
    if not 0.0 <= probability <= 1.0 or not pmf:
        raise ValueError("quantile probability and PMF must be valid")
    cumulative = 0.0
    for value, mass in sorted(pmf.items()):
        cumulative += mass
        if cumulative >= probability - 1e-15:
            return value
    return max(pmf)


def elite_mean(pmf: Mapping[float, float], fraction: float) -> float:
    if not 0.0 < fraction <= 1.0:
        raise ValueError("elite fraction must be in (0, 1]")
    remaining = fraction
    total = 0.0
    for value, probability in sorted(pmf.items()):
        taken = min(remaining, probability)
        total += value * taken
        remaining -= taken
        if remaining <= 1e-15:
            break
    if remaining > 1e-10:
        raise ValueError("PMF has insufficient mass")
    return total / fraction


def expected_best_of(pmf: Mapping[float, float], draw_count: int) -> float:
    if draw_count <= 0:
        raise ValueError("draw count must be positive")
    values = sorted(pmf)
    result = 0.0
    for index, value in enumerate(values):
        at_least = sum(pmf[item] for item in values[index:])
        greater = sum(pmf[item] for item in values[index + 1 :])
        result += value * (at_least**draw_count - greater**draw_count)
    return result


def continuous_support_loss(
    available_outcomes: Sequence[tuple[int, int]],
    future_rates: tuple[float, float],
) -> float:
    """L1/Agent distance from the future rate to the historical outcome hull."""
    points = sorted(set(available_outcomes))
    if not points:
        raise ValueError("support requires at least one historical outcome")
    hull = _convex_hull(tuple((float(x), float(y)) for x, y in points))
    target = future_rates
    if len(hull) == 1:
        return _mean_absolute_error(hull[0], target)
    if len(hull) == 2:
        return _segment_l1_loss(target, hull[0], hull[1])
    if _inside_convex_polygon(target, hull):
        return 0.0
    edges = tuple(zip(hull, (*hull[1:], hull[0]), strict=True))
    return min(_segment_l1_loss(target, start, end) for start, end in edges)


def _convex_hull(
    points: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    if len(points) <= 1:
        return points

    def cross(
        origin: tuple[float, float],
        left: tuple[float, float],
        right: tuple[float, float],
    ) -> float:
        return (left[0] - origin[0]) * (right[1] - origin[1]) - (
            left[1] - origin[1]
        ) * (right[0] - origin[0])

    lower: list[tuple[float, float]] = []
    for point in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0.0:
            lower.pop()
        lower.append(point)
    upper: list[tuple[float, float]] = []
    for point in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0.0:
            upper.pop()
        upper.append(point)
    return tuple(lower[:-1] + upper[:-1])


def _inside_convex_polygon(
    point: tuple[float, float],
    polygon: Sequence[tuple[float, float]],
) -> bool:
    signs = []
    for start, end in zip(polygon, (*polygon[1:], polygon[0]), strict=True):
        cross = (end[0] - start[0]) * (point[1] - start[1]) - (end[1] - start[1]) * (
            point[0] - start[0]
        )
        if not math.isclose(cross, 0.0, abs_tol=1e-12):
            signs.append(cross > 0.0)
    return not signs or all(sign == signs[0] for sign in signs)


def _segment_l1_loss(
    target: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    candidates = {0.0, 1.0}
    for index in range(2):
        delta = end[index] - start[index]
        if not math.isclose(delta, 0.0):
            candidates.add((target[index] - start[index]) / delta)
    return min(
        _mean_absolute_error(
            (
                start[0] + max(0.0, min(1.0, value)) * (end[0] - start[0]),
                start[1] + max(0.0, min(1.0, value)) * (end[1] - start[1]),
            ),
            target,
        )
        for value in candidates
    )


def run_landscape(
    *,
    landscape_plan_path: Path = DEFAULT_PLAN,
    landscape_amendment_path: Path = DEFAULT_AMENDMENT,
    embedding_path: Path = DEFAULT_EMBEDDINGS,
    null_resamples: int | None = None,
) -> Mapping[str, object]:
    landscape_plan = load_landscape_plan(landscape_plan_path)
    landscape_amendment = load_landscape_amendment(
        landscape_amendment_path,
        landscape_plan,
    )
    source_plan = study.load_plan()
    amendment = study.load_amendment(study.DEFAULT_AMENDMENT, source_plan)
    correction = study.load_correction(
        study.DEFAULT_CORRECTION,
        source_plan,
        amendment,
    )
    paths = study.StudyPaths()
    metadata = study.load_metadata(paths, source_plan, correction)
    design = study.build_design(metadata, source_plan)
    outcomes = study.load_outcomes(paths, source_plan, metadata)
    if (
        landscape_plan["design"]["source_study_plan_digest"]
        != (source_plan["study_plan_digest"])
    ):
        raise ValueError("landscape plan does not bind the source study")
    agent_keys = tuple(cast(Sequence[str], source_plan["source_bindings"]["agents"]))
    if len(agent_keys) != 2:
        raise ValueError("exact landscape study requires the frozen two-Agent panel")
    selection_budget = int(
        source_plan["rolling_origin"]["selection_budget_task_checks"]
    )
    practical_margin = float(
        landscape_plan["research_contract"]["minimum_practical_improvement"]
    )
    views = _origin_views(design)
    outcome_by_task = _joint_outcome_by_task(metadata, outcomes, agent_keys)

    baseline = _baseline_analysis(
        views,
        outcome_by_task,
        agent_keys,
        practical_margin,
    )
    coverage_summary = cast(Mapping[str, float], baseline["coverage"])
    full_history_summary = cast(Mapping[str, float], baseline["full_history"])
    random_landscape = _random_landscape(
        views,
        outcome_by_task,
        selection_budget,
        cast(Sequence[float], landscape_plan["design"]["elite_fractions"]),
        cast(
            Sequence[int],
            landscape_plan["design"]["best_of_random_draw_counts"],
        ),
        coverage_summary["macro_origin_mae"],
    )
    support = _support_analysis(
        views,
        outcome_by_task,
        selection_budget,
    )
    configured_resamples = int(landscape_plan["design"]["null_resamples"])
    nulls = _null_analysis(
        views,
        outcome_by_task,
        metadata,
        selection_budget,
        null_resamples=(
            configured_resamples if null_resamples is None else null_resamples
        ),
        seed=int(landscape_plan["design"]["null_seed"]),
    )
    embedding_data = load_embeddings(embedding_path, metadata)
    candidates = _candidate_analysis(
        views,
        outcome_by_task,
        agent_keys,
        embedding_data,
    )
    robustness = _baseline_robustness(
        metadata,
        source_plan,
        outcomes,
        outcome_by_task,
        agent_keys,
        selection_budget,
        practical_margin,
    )
    best_candidate = cast(Mapping[str, object], candidates["best_fixed_candidate"])
    repeat_robustness = cast(Mapping[str, object], robustness["repeat_noise"])
    full_mae = full_history_summary["macro_origin_mae"]
    best_mae = cast(float, best_candidate["macro_origin_mae"])
    candidate_meets_point_gate = best_mae - full_mae <= -practical_margin

    result: dict[str, object] = {
        "schema_version": "barcarolle_selection_landscape_results_v1",
        "study_id": landscape_plan["study_id"],
        "status": (
            "development_candidate_identified"
            if candidate_meets_point_gate
            else landscape_amendment["correction"]["corrected_terminal_state"]
        ),
        "landscape_plan_digest": landscape_plan["landscape_plan_digest"],
        "landscape_amendment_digest": landscape_amendment["landscape_amendment_digest"],
        "source_study_plan_digest": source_plan["study_plan_digest"],
        "authority": {
            "new_coding_agent_calls": 0,
            "embedding_calls": 1,
            "embedding_input_tokens": embedding_data.usage.get("prompt_tokens"),
            "embedding_monetary_cost_usd": None,
            "embedding_monetary_cost_status": "provider_response_did_not_expose_cost",
            "local_null_resamples": nulls["resample_count"],
            "local_repeat_noise_views": repeat_robustness["resamples"],
        },
        "claim": {
            "established": (
                "The exact same-budget random selection landscape, full-history "
                "baseline, support bounds, null controls, repeat/dependency/"
                "horizon robustness, and three candidate families plus one "
                "post-plan hybrid probe are measured for the frozen "
                "development scenario."
            ),
            "not_established": (
                "No explored candidate demonstrates a 0.02 improvement over "
                "full history; no result is confirmatory or establishes transfer "
                "to an unseen Agent."
            ),
        },
        "embedding_manifest": {
            "model": embedding_data.model,
            "task_count": len(embedding_data.task_ids),
            "dimensions": embedding_data.dimensions,
            "usage": embedding_data.usage,
            "artifact_sha256": embedding_data.artifact_sha256,
            "input_digest": canonical_digest(
                tuple(
                    {
                        "task_id": task.task_id,
                        "task_text": task.task_text,
                    }
                    for task in metadata.ordered_tasks
                )
            ),
            "raw_artifact_committed": False,
        },
        "baseline": baseline,
        "random_selection_landscape": random_landscape,
        "support": support,
        "null_controls": nulls,
        "robustness": robustness,
        "candidate_families": candidates,
        "decision": {
            "primary_baseline": "full_history",
            "minimum_practical_improvement": practical_margin,
            "best_fixed_candidate": best_candidate,
            "candidate_meets_point_gate": candidate_meets_point_gate,
            "promotion_allowed": False,
            "reason": (
                "The development source was already opened, the full-history "
                "contrast is inconclusive, and no explored rule clears the "
                "practical improvement gate."
            ),
        },
    }
    result["landscape_results_digest"] = canonical_digest(result)
    return result


def _origin_views(design: study.DiagnosticDesign) -> tuple[OriginView, ...]:
    return tuple(
        OriginView(
            origin.origin_number,
            tuple(task.task_id for task in origin.history),
            tuple(task.task_id for task in origin.future),
            origin.selections["coverage"].task_ids,
            origin.selections["recency"].task_ids,
            tuple(task.sampling_stratum for task in origin.history),
        )
        for origin in design.origins
    )


def _joint_outcome_by_task(
    metadata: study.Metadata,
    outcomes: study.Outcomes,
    agent_keys: Sequence[str],
) -> Mapping[str, tuple[int, int]]:
    return {
        task.task_id: (
            outcomes.base[agent_keys[0]][task.task_id],
            outcomes.base[agent_keys[1]][task.task_id],
        )
        for task in metadata.ordered_tasks
    }


def _rates(
    task_ids: Sequence[str],
    outcome_by_task: Mapping[str, tuple[int, int]],
) -> tuple[float, float]:
    if not task_ids:
        raise ValueError("rate requires at least one Task")
    return (
        sum(outcome_by_task[task_id][0] for task_id in task_ids) / len(task_ids),
        sum(outcome_by_task[task_id][1] for task_id in task_ids) / len(task_ids),
    )


def _metric_values(
    selected_task_ids: Sequence[str],
    future_task_ids: Sequence[str],
    outcome_by_task: Mapping[str, tuple[int, int]],
    agent_keys: Sequence[str],
) -> MetricValues:
    return _metrics_from_rates(
        _rates(selected_task_ids, outcome_by_task),
        _rates(future_task_ids, outcome_by_task),
        agent_keys,
    )


def _metrics_from_rates(
    selected_rates: tuple[float, float],
    future_rates: tuple[float, float],
    agent_keys: Sequence[str],
) -> MetricValues:
    selected_gap = selected_rates[0] - selected_rates[1]
    future_gap = future_rates[0] - future_rates[1]
    recommended = min(
        range(2),
        key=lambda index: (-selected_rates[index], agent_keys[index]),
    )
    return MetricValues(
        _mean_absolute_error(selected_rates, future_rates),
        abs(selected_gap - future_gap),
        float(_sign(selected_gap) == _sign(future_gap)),
        max(future_rates) - future_rates[recommended],
    )


def _baseline_analysis(
    views: Sequence[OriginView],
    outcome_by_task: Mapping[str, tuple[int, int]],
    agent_keys: Sequence[str],
    practical_margin: float,
) -> Mapping[str, object]:
    by_name = {
        "full_history": tuple(
            _metric_values(
                view.history_task_ids,
                view.future_task_ids,
                outcome_by_task,
                agent_keys,
            )
            for view in views
        ),
        "coverage": tuple(
            _metric_values(
                view.coverage_task_ids,
                view.future_task_ids,
                outcome_by_task,
                agent_keys,
            )
            for view in views
        ),
        "recency": tuple(
            _metric_values(
                view.recency_task_ids,
                view.future_task_ids,
                outcome_by_task,
                agent_keys,
            )
            for view in views
        ),
    }
    result: dict[str, object] = {
        name: _metric_summary(metrics) for name, metrics in by_name.items()
    }
    coverage_minus_full = tuple(
        coverage.future_pass_rate_mae - full.future_pass_rate_mae
        for coverage, full in zip(
            by_name["coverage"],
            by_name["full_history"],
            strict=True,
        )
    )
    contrast = dict(_paired_contrast(coverage_minus_full))
    contrast["prospective_planning"] = _prospective_origin_planning(
        coverage_minus_full,
        practical_margin,
    )
    result["coverage_minus_full_history"] = contrast
    result["per_agent"] = _per_agent_baseline_analysis(
        views,
        outcome_by_task,
        agent_keys,
    )
    result["mean_history_task_count"] = sum(
        len(view.history_task_ids) for view in views
    ) / len(views)
    result["selection_fraction_of_mean_history"] = 10.0 / float(
        result["mean_history_task_count"]
    )
    return result


def _per_agent_baseline_analysis(
    views: Sequence[OriginView],
    outcome_by_task: Mapping[str, tuple[int, int]],
    agent_keys: Sequence[str],
) -> Mapping[str, object]:
    result: dict[str, object] = {}
    for agent_index, agent_key in enumerate(agent_keys):
        coverage_losses = []
        full_history_losses = []
        for view in views:
            future_rate = sum(
                outcome_by_task[task_id][agent_index]
                for task_id in view.future_task_ids
            ) / len(view.future_task_ids)
            coverage_rate = sum(
                outcome_by_task[task_id][agent_index]
                for task_id in view.coverage_task_ids
            ) / len(view.coverage_task_ids)
            full_history_rate = sum(
                outcome_by_task[task_id][agent_index]
                for task_id in view.history_task_ids
            ) / len(view.history_task_ids)
            coverage_losses.append(abs(coverage_rate - future_rate))
            full_history_losses.append(abs(full_history_rate - future_rate))
        result[agent_key] = {
            "coverage_macro_origin_mae": sum(coverage_losses) / len(coverage_losses),
            "full_history_macro_origin_mae": (
                sum(full_history_losses) / len(full_history_losses)
            ),
            "coverage_minus_full_history": _paired_contrast(
                tuple(
                    coverage - full
                    for coverage, full in zip(
                        coverage_losses,
                        full_history_losses,
                        strict=True,
                    )
                )
            ),
        }
    return result


def _baseline_robustness(
    metadata: study.Metadata,
    source_plan: Mapping[str, Any],
    outcomes: study.Outcomes,
    outcome_by_task: Mapping[str, tuple[int, int]],
    agent_keys: Sequence[str],
    selection_budget: int,
    practical_margin: float,
) -> Mapping[str, object]:
    specs = study.selector_specs(source_plan)
    block_rows = {}
    for block_size, initial_history_count in (
        (3, 15),
        (4, 15),
        (5, 15),
        (6, 15),
        (8, 11),
    ):
        design = _coverage_design(
            metadata.ordered_tasks,
            specs,
            initial_history_count,
            block_size,
            selection_budget,
        )
        block_rows[str(block_size)] = {
            "initial_history_task_count": initial_history_count,
            **_primary_baseline_row(
                _origin_views(design),
                outcome_by_task,
                practical_margin,
            ),
        }

    first_by_cluster: dict[str, TaskRecord] = {}
    for task in metadata.ordered_tasks:
        first_by_cluster.setdefault(task.dependency_cluster_id, task)
    independent_tasks = tuple(first_by_cluster.values())
    independent_design = _coverage_design(
        independent_tasks,
        specs,
        14,
        5,
        selection_budget,
    )
    return {
        "status": "post_plan_adversarial_sensitivity",
        "future_block_size": {
            "configurations": block_rows,
            "interpretation": (
                "The coverage-minus-full-history direction changes across "
                "reasonable future-block sizes; no configuration clears both "
                "promotion gates."
            ),
        },
        "dependency_first_task_per_cluster": {
            "task_count": len(independent_tasks),
            "cluster_recurrence": 0,
            "initial_history_task_count": 14,
            "future_block_task_count": 5,
            **_primary_baseline_row(
                _origin_views(independent_design),
                outcome_by_task,
                practical_margin,
            ),
            "interpretation": (
                "Removing repeated dependency clusters strengthens the point "
                "gain but reduces the evidence units and still misses both "
                "promotion gates."
            ),
        },
        "repeat_noise": _repeat_noise_primary_sensitivity(
            metadata,
            views=_origin_views(
                _coverage_design(
                    metadata.ordered_tasks,
                    specs,
                    15,
                    5,
                    selection_budget,
                )
            ),
            outcomes=outcomes,
            agent_keys=agent_keys,
            source_plan=source_plan,
        ),
    }


def _coverage_design(
    tasks: Sequence[TaskRecord],
    specs: Mapping[str, study.SelectorSpec],
    initial_history_count: int,
    future_block_count: int,
    selection_budget: int,
) -> study.DiagnosticDesign:
    blocks = study.chronological_blocks(
        tasks,
        initial_history_count=initial_history_count,
        future_block_count=future_block_count,
    )
    origins = tuple(
        study.DiagnosticOrigin(
            index,
            history,
            future,
            {
                name: study.select_tasks(specs[name], history, selection_budget)
                for name in ("coverage", "recency")
            },
        )
        for index, (history, future) in enumerate(blocks, start=1)
    )
    return study.DiagnosticDesign(
        origins,
        specs,
        canonical_digest(
            {
                "task_ids": tuple(task.task_id for task in tasks),
                "initial_history_task_count": initial_history_count,
                "future_block_task_count": future_block_count,
                "selection_budget": selection_budget,
            }
        ),
    )


def _primary_baseline_row(
    views: Sequence[OriginView],
    outcome_by_task: Mapping[str, tuple[int, int]],
    practical_margin: float,
) -> Mapping[str, object]:
    coverage_losses = tuple(
        _mean_absolute_error(
            _rates(view.coverage_task_ids, outcome_by_task),
            _rates(view.future_task_ids, outcome_by_task),
        )
        for view in views
    )
    full_history_losses = tuple(
        _mean_absolute_error(
            _rates(view.history_task_ids, outcome_by_task),
            _rates(view.future_task_ids, outcome_by_task),
        )
        for view in views
    )
    differences = tuple(
        coverage - full
        for coverage, full in zip(
            coverage_losses,
            full_history_losses,
            strict=True,
        )
    )
    contrast = _paired_contrast(differences)
    interval = cast(
        Mapping[str, object],
        contrast["origin_block_interval_95"],
    )
    difference = cast(float, contrast["macro_origin_mae_difference"])
    return {
        "origin_count": len(views),
        "coverage_macro_origin_mae": sum(coverage_losses) / len(coverage_losses),
        "full_history_macro_origin_mae": (
            sum(full_history_losses) / len(full_history_losses)
        ),
        "coverage_minus_full_history": contrast,
        "point_gate_cleared": difference <= -practical_margin,
        "interval_gate_cleared": (
            interval["status"] == "available"
            and cast(float, interval["upper"]) < 0.0
        ),
    }


def _repeat_noise_primary_sensitivity(
    metadata: study.Metadata,
    *,
    views: Sequence[OriginView],
    outcomes: study.Outcomes,
    agent_keys: Sequence[str],
    source_plan: Mapping[str, Any],
) -> Mapping[str, object]:
    sensitivity = cast(
        Mapping[str, Any],
        source_plan["sensitivity_analyses"],
    )
    configuration = cast(
        Mapping[str, Any],
        sensitivity["repeat_noise_views"],
    )
    resamples = int(configuration["resamples"])
    seed = int(configuration["seed"])
    rng = random.Random(seed)
    differences = []
    for _ in range(resamples):
        sampled_by_agent = {
            agent_key: {
                task_id: (
                    rng.choice(replicates)
                    if len(replicates) > 1
                    else outcomes.base[agent_key][task_id]
                )
                for task_id, replicates in outcomes.scoreable_replicates[
                    agent_key
                ].items()
            }
            for agent_key in agent_keys
        }
        sampled_outcomes = {
            task.task_id: (
                sampled_by_agent[agent_keys[0]][task.task_id],
                sampled_by_agent[agent_keys[1]][task.task_id],
            )
            for task in metadata.ordered_tasks
        }
        origin_differences = []
        for view in views:
            future_rates = _rates(view.future_task_ids, sampled_outcomes)
            origin_differences.append(
                _mean_absolute_error(
                    _rates(view.coverage_task_ids, sampled_outcomes),
                    future_rates,
                )
                - _mean_absolute_error(
                    _rates(view.history_task_ids, sampled_outcomes),
                    future_rates,
                )
            )
        differences.append(sum(origin_differences) / len(origin_differences))
    ordered = sorted(differences)
    repeated_tasks = {
        task_id
        for tasks in outcomes.scoreable_replicates.values()
        for task_id, replicates in tasks.items()
        if len(replicates) > 1
    }
    return {
        "status": "preselected_repeat_view_conditional_sensitivity",
        "resamples": resamples,
        "seed": seed,
        "replicated_task_count": len(repeated_tasks),
        "replicated_agent_task_count": sum(
            len(replicates) > 1
            for tasks in outcomes.scoreable_replicates.values()
            for replicates in tasks.values()
        ),
        "coverage_minus_full_history": {
            "mean": sum(ordered) / len(ordered),
            "lower_2_5_percentile": _empirical_quantile(ordered, 0.025),
            "median": _empirical_quantile(ordered, 0.5),
            "upper_97_5_percentile": _empirical_quantile(ordered, 0.975),
            "fraction_below_zero": (
                sum(value < 0.0 for value in ordered) / len(ordered)
            ),
            "fraction_at_most_minus_0_02": (
                sum(value <= -0.02 for value in ordered) / len(ordered)
            ),
            "minimum": ordered[0],
            "maximum": ordered[-1],
        },
        "interpretation": (
            "This reuses the source plan's preselected repeat views and is "
            "conditional sensitivity, not an independent sampling interval."
        ),
    }


def _metric_summary(values: Sequence[MetricValues]) -> Mapping[str, float]:
    return {
        field: sum(getattr(value, field) for value in values) / len(values)
        for field in (
            "future_pass_rate_mae",
            "pairwise_gap_mae",
            "rank_agreement",
            "recommendation_regret",
        )
    } | {
        "macro_origin_mae": sum(value.future_pass_rate_mae for value in values)
        / len(values)
    }


def _random_landscape(
    views: Sequence[OriginView],
    outcome_by_task: Mapping[str, tuple[int, int]],
    selection_budget: int,
    elite_fractions: Sequence[float],
    draw_counts: Sequence[int],
    coverage_macro_mae: float,
) -> Mapping[str, object]:
    origin_pmfs = []
    origin_rows = []
    for view in views:
        future_rates = _rates(view.future_task_ids, outcome_by_task)
        pmf = exact_random_loss_pmf(
            tuple(outcome_by_task[task_id] for task_id in view.history_task_ids),
            future_rates,
            selection_budget,
        )
        coverage_loss = _mean_absolute_error(
            _rates(view.coverage_task_ids, outcome_by_task),
            future_rates,
        )
        origin_strictly_better = sum(
            probability
            for loss, probability in pmf.items()
            if loss < coverage_loss - 1e-12
        )
        origin_equal = sum(
            probability
            for loss, probability in pmf.items()
            if math.isclose(loss, coverage_loss, abs_tol=1e-12)
        )
        origin_pmfs.append(pmf)
        origin_rows.append(
            {
                "origin_number": view.origin_number,
                "expected_mae": _pmf_mean(pmf),
                "median_mae": distribution_quantile(pmf, 0.5),
                "best_mae": min(pmf),
                "distinct_loss_count": len(pmf),
                "coverage_mae": coverage_loss,
                "random_strictly_better_probability": origin_strictly_better,
                "random_equal_probability": origin_equal,
                "coverage_midrank_fraction_beats": (
                    1.0 - origin_strictly_better - 0.5 * origin_equal
                ),
            }
        )
    macro_pmf = convolve_macro_pmfs(origin_pmfs)
    strictly_better = sum(
        probability
        for loss, probability in macro_pmf.items()
        if loss < coverage_macro_mae - 1e-12
    )
    equal = sum(
        probability
        for loss, probability in macro_pmf.items()
        if math.isclose(loss, coverage_macro_mae, abs_tol=1e-12)
    )
    as_good_or_better = strictly_better + equal
    discrete_oracle_mae = min(macro_pmf)
    fixed_seed_sensitivity = _fixed_seed_random_policy_sensitivity(
        views,
        outcome_by_task,
        selection_budget,
        coverage_macro_mae,
        seed_count=FIXED_SEED_AUDIT_COUNT,
    )
    return {
        "reference": "uniform independent ten-Task subset at each Origin",
        "macro_origin_expected_mae": _pmf_mean(macro_pmf),
        "macro_origin_standard_deviation": _pmf_standard_deviation(macro_pmf),
        "quantiles": {
            str(probability): distribution_quantile(macro_pmf, probability)
            for probability in (
                0.001,
                0.01,
                0.05,
                0.1,
                0.25,
                0.5,
                0.75,
                0.9,
                0.95,
                0.99,
            )
        },
        "coverage_position": {
            "coverage_macro_origin_mae": coverage_macro_mae,
            "random_strictly_better_probability": strictly_better,
            "random_equal_probability": equal,
            "random_as_good_or_better_probability": as_good_or_better,
            "midrank_fraction_coverage_beats": (1.0 - strictly_better - 0.5 * equal),
            "equivalent_random_draws": (
                1.0 / as_good_or_better if as_good_or_better > 0.0 else None
            ),
        },
        "elite_mean_mae": {
            str(fraction): elite_mean(macro_pmf, fraction)
            for fraction in elite_fractions
        },
        "expected_best_of_random_mae": {
            str(draw_count): expected_best_of(macro_pmf, draw_count)
            for draw_count in draw_counts
        },
        "oracle_density": {
            "discrete_oracle_macro_origin_mae": discrete_oracle_mae,
            "exact_oracle_probability": macro_pmf[discrete_oracle_mae],
            "probability_within_excess_mae": {
                str(excess): sum(
                    probability
                    for loss, probability in macro_pmf.items()
                    if loss <= discrete_oracle_mae + excess + 1e-12
                )
                for excess in (0.01, 0.02, 0.05, 0.1)
            },
            "interpretation": (
                "The oracle opens future outcomes and is a density endpoint, "
                "not a deployable random-search target."
            ),
        },
        "fixed_seed_policy_sensitivity": {
            **fixed_seed_sensitivity,
            "difference_from_independent_exact": {
                "expected_mae": (
                    cast(float, fixed_seed_sensitivity["macro_origin_mean_mae"])
                    - _pmf_mean(macro_pmf)
                ),
                "as_good_or_better_fraction": (
                    cast(
                        float,
                        fixed_seed_sensitivity[
                            "fraction_as_good_or_better_than_coverage"
                        ],
                    )
                    - as_good_or_better
                ),
            },
        },
        "origin_rows": tuple(origin_rows),
    }


def _fixed_seed_random_policy_sensitivity(
    views: Sequence[OriginView],
    outcome_by_task: Mapping[str, tuple[int, int]],
    selection_budget: int,
    coverage_macro_mae: float,
    *,
    seed_count: int,
) -> Mapping[str, object]:
    """Audit the cross-Origin coupling of the example's fixed-seed policy."""
    if seed_count <= 0:
        raise ValueError("fixed-seed audit count must be positive")
    future_rates = tuple(
        _rates(view.future_task_ids, outcome_by_task) for view in views
    )
    macro_losses = []
    for seed in range(seed_count):
        origin_losses = []
        for view, future in zip(views, future_rates, strict=True):
            shuffled = list(view.history_task_ids)
            random.Random(seed).shuffle(shuffled)
            selected_rates = _rates(shuffled[:selection_budget], outcome_by_task)
            origin_losses.append(_mean_absolute_error(selected_rates, future))
        macro_losses.append(sum(origin_losses) / len(origin_losses))
    ordered = sorted(macro_losses)
    strictly_better = (
        sum(loss < coverage_macro_mae - 1e-12 for loss in ordered) / seed_count
    )
    equal = (
        sum(math.isclose(loss, coverage_macro_mae, abs_tol=1e-12) for loss in ordered)
        / seed_count
    )
    return {
        "status": "post_plan_adversarial_sensitivity",
        "reference": (
            "Current example policy: reinitialize the same integer seed and "
            "shuffle each growing Origin history."
        ),
        "seed_range": {"first": 0, "last": seed_count - 1, "count": seed_count},
        "macro_origin_mean_mae": sum(ordered) / seed_count,
        "quantiles": {
            str(probability): _empirical_quantile(ordered, probability)
            for probability in (0.01, 0.05, 0.1, 0.5)
        },
        "fraction_strictly_better_than_coverage": strictly_better,
        "fraction_equal_to_coverage": equal,
        "fraction_as_good_or_better_than_coverage": strictly_better + equal,
        "midrank_fraction_coverage_beats": 1.0 - strictly_better - 0.5 * equal,
        "minimum_mae": ordered[0],
        "maximum_mae": ordered[-1],
    }


def _support_analysis(
    views: Sequence[OriginView],
    outcome_by_task: Mapping[str, tuple[int, int]],
    selection_budget: int,
) -> Mapping[str, object]:
    rows = []
    for view in views:
        history = tuple(outcome_by_task[item] for item in view.history_task_ids)
        future_rates = _rates(view.future_task_ids, outcome_by_task)
        pmf = exact_random_loss_pmf(history, future_rates, selection_budget)
        rows.append(
            {
                "origin_number": view.origin_number,
                "continuous_support_mae": continuous_support_loss(
                    history,
                    future_rates,
                ),
                "discrete_ten_task_oracle_mae": min(pmf),
            }
        )
    return {
        "continuous_support_macro_origin_mae": sum(
            row["continuous_support_mae"] for row in rows
        )
        / len(rows),
        "discrete_ten_task_oracle_macro_origin_mae": sum(
            row["discrete_ten_task_oracle_mae"] for row in rows
        )
        / len(rows),
        "origins_with_zero_continuous_support_loss": sum(
            math.isclose(row["continuous_support_mae"], 0.0, abs_tol=1e-12)
            for row in rows
        ),
        "origins_with_zero_discrete_oracle_loss": sum(
            math.isclose(
                row["discrete_ten_task_oracle_mae"],
                0.0,
                abs_tol=1e-12,
            )
            for row in rows
        ),
        "origin_rows": tuple(rows),
        "interpretation": (
            "Support and discrete oracle rows open future outcomes and measure "
            "representability only, not pre-origin learnability."
        ),
    }


def _null_analysis(
    views: Sequence[OriginView],
    observed_outcomes: Mapping[str, tuple[int, int]],
    metadata: study.Metadata,
    selection_budget: int,
    *,
    null_resamples: int,
    seed: int,
) -> Mapping[str, object]:
    task_ids = tuple(task.task_id for task in metadata.ordered_tasks)
    observed_values = tuple(observed_outcomes[task_id] for task_id in task_ids)
    observed = _landscape_contrasts(
        views,
        observed_outcomes,
        selection_budget,
    )
    rng = random.Random(seed)
    unrestricted = []
    for _ in range(null_resamples):
        permuted = list(observed_values)
        rng.shuffle(permuted)
        unrestricted.append(
            _landscape_contrasts(
                views,
                dict(zip(task_ids, permuted, strict=True)),
                selection_budget,
            )
        )
    by_stratum: dict[str, list[int]] = defaultdict(list)
    for index, task in enumerate(metadata.ordered_tasks):
        by_stratum[task.sampling_stratum].append(index)
    stratum_preserving = []
    for _ in range(null_resamples):
        permuted = list(observed_values)
        for indices in by_stratum.values():
            group = [permuted[index] for index in indices]
            rng.shuffle(group)
            for index, value in zip(indices, group, strict=True):
                permuted[index] = value
        stratum_preserving.append(
            _landscape_contrasts(
                views,
                dict(zip(task_ids, permuted, strict=True)),
                selection_budget,
            )
        )
    circular = tuple(
        _landscape_contrasts(
            views,
            dict(
                zip(
                    task_ids,
                    (*observed_values[offset:], *observed_values[:offset]),
                    strict=True,
                )
            ),
            selection_budget,
        )
        for offset in range(1, len(task_ids))
    )
    return {
        "resample_count": null_resamples,
        "seed": seed,
        "observed": observed,
        "unrestricted_outcome_permutation": _null_summary(
            observed,
            unrestricted,
            plus_one=True,
        ),
        "sampling_stratum_preserving_outcome_permutation": _null_summary(
            observed,
            stratum_preserving,
            plus_one=True,
        ),
        "exact_nonzero_circular_shifts": _null_summary(
            observed,
            circular,
            plus_one=True,
        ),
        "interpretation": (
            "These controls test accidental alignment of the frozen Task "
            "metadata and outcome sequence. They do not create new Origins."
        ),
        "p_value_rule": (
            "Use (b + 1) / (B + 1), including the observed arrangement, for "
            "finite Monte Carlo and nonzero-shift randomization distributions."
        ),
    }


def _landscape_contrasts(
    views: Sequence[OriginView],
    outcome_by_task: Mapping[str, tuple[int, int]],
    selection_budget: int,
) -> Mapping[str, float]:
    coverage_losses = []
    full_losses = []
    random_expected_losses = []
    for view in views:
        future_rates = _rates(view.future_task_ids, outcome_by_task)
        coverage_losses.append(
            _mean_absolute_error(
                _rates(view.coverage_task_ids, outcome_by_task),
                future_rates,
            )
        )
        full_losses.append(
            _mean_absolute_error(
                _rates(view.history_task_ids, outcome_by_task),
                future_rates,
            )
        )
        pmf = exact_random_loss_pmf(
            tuple(outcome_by_task[item] for item in view.history_task_ids),
            future_rates,
            selection_budget,
        )
        random_expected_losses.append(_pmf_mean(pmf))
    coverage = sum(coverage_losses) / len(views)
    return {
        "coverage_minus_full_history": (coverage - sum(full_losses) / len(views)),
        "coverage_minus_exact_random_expectation": (
            coverage - sum(random_expected_losses) / len(views)
        ),
    }


def _null_summary(
    observed: Mapping[str, float],
    values: Sequence[Mapping[str, float]],
    *,
    plus_one: bool = False,
) -> Mapping[str, object]:
    result: dict[str, object] = {}
    for name, observed_value in observed.items():
        ordered = sorted(value[name] for value in values)
        count = sum(value <= observed_value + 1e-15 for value in ordered)
        numerator = count + int(plus_one)
        denominator = len(ordered) + int(plus_one)
        result[name] = {
            "observed": observed_value,
            "null_mean": sum(ordered) / len(ordered),
            "null_interval_95": {
                "lower": _empirical_quantile(ordered, 0.025),
                "upper": _empirical_quantile(ordered, 0.975),
            },
            "one_sided_probability_at_most_observed": numerator / denominator,
        }
    return result


def load_embeddings(
    path: Path,
    metadata: study.Metadata,
) -> EmbeddingData:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "barcarolle_task_text_embeddings_v1":
        raise ValueError("embedding artifact schema is not supported")
    items = payload.get("items")
    if not isinstance(items, list):
        raise ValueError("embedding artifact is missing items")
    task_ids = tuple(task.task_id for task in metadata.ordered_tasks)
    observed_ids = tuple(item.get("task_id") for item in items)
    if observed_ids != task_ids:
        raise ValueError("embedding artifact does not match Task order")
    vectors = tuple(
        _normalized_vector(cast(Sequence[float], item["embedding"])) for item in items
    )
    dimensions = int(payload["dimensions"])
    if not vectors or any(len(vector) != dimensions for vector in vectors):
        raise ValueError("embedding dimensions are inconsistent")
    return EmbeddingData(
        str(payload["model"]),
        cast(Mapping[str, object], payload.get("usage", {})),
        dimensions,
        task_ids,
        vectors,
        _sha256(path),
    )


def _candidate_analysis(
    views: Sequence[OriginView],
    outcome_by_task: Mapping[str, tuple[int, int]],
    agent_keys: Sequence[str],
    embeddings: EmbeddingData,
) -> Mapping[str, object]:
    outcome_rows = _outcome_forecast_candidates(
        views,
        outcome_by_task,
        agent_keys,
    )
    semantic_rows, semantic_alignment = _semantic_candidates(
        views,
        outcome_by_task,
        agent_keys,
        embeddings,
    )
    semantic_outcome_rows = _semantic_outcome_forecast_candidates(
        views,
        outcome_by_task,
        agent_keys,
        embeddings,
    )
    difficulty_rows = _difficulty_candidates(
        views,
        outcome_by_task,
        agent_keys,
    )
    candidates = (
        *outcome_rows,
        *semantic_rows,
        *semantic_outcome_rows,
        *difficulty_rows,
    )
    best = min(candidates, key=_candidate_sort_key)
    return {
        "outcome_forecast_matching": outcome_rows,
        "semantic_coreset": semantic_rows,
        "semantic_alignment_diagnostic": semantic_alignment,
        "semantic_outcome_forecast": {
            "status": "post_plan_exploratory_mechanism_probe",
            "candidates": semantic_outcome_rows,
        },
        "difficulty_information": difficulty_rows,
        "best_fixed_candidate": best,
        "promotion_status": "none",
        "retired_or_reopening_conditions": {
            "outcome_forecast_matching": (
                "Reopen with a new reference-Agent panel or a predeclared "
                "change-point mechanism; do not tune more windows here."
            ),
            "semantic_coreset": (
                "Reopen on a second Task source or with more independent "
                "Origins; current fixed semantic rules do not beat coverage."
            ),
            "semantic_outcome_forecast": (
                "Reopen on a new Agent panel and Task source; do not tune more "
                "similarity windows, neighbor counts, or temperatures here."
            ),
            "difficulty_information": (
                "Reopen with at least several reference Agents so historical "
                "difficulty is not restricted to 0, 0.5, and 1."
            ),
        },
    }


def _outcome_forecast_candidates(
    views: Sequence[OriginView],
    outcome_by_task: Mapping[str, tuple[int, int]],
    agent_keys: Sequence[str],
) -> tuple[Mapping[str, object], ...]:
    specs: tuple[tuple[str, float], ...] = (
        ("full_mean", 0.0),
        *(
            (f"recent_{window}", float(window))
            for window in (5, 10, 15, 20, 25, 30, 40)
        ),
        *(
            (f"ewma_half_life_{half_life}", float(half_life))
            for half_life in (2, 3, 5, 8, 10, 15, 20)
        ),
        *(
            (f"linear_window_{window}", float(window))
            for window in (10, 15, 20, 25, 30, 40)
        ),
    )
    rows = []
    for name, parameter in specs:
        values = []
        for view in views:
            history = tuple(outcome_by_task[item] for item in view.history_task_ids)
            target = _outcome_forecast(history, name, parameter)
            selected_rates = _nearest_feasible_rates(history, target, 10)
            values.append(
                _metrics_from_rates(
                    selected_rates,
                    _rates(view.future_task_ids, outcome_by_task),
                    agent_keys,
                )
            )
        rows.append(_candidate_row("outcome_forecast_matching", name, values))
    return tuple(sorted(rows, key=_candidate_sort_key))


def _outcome_forecast(
    history: Sequence[tuple[int, int]],
    name: str,
    parameter: float,
) -> tuple[float, float]:
    if name == "full_mean":
        return (
            sum(value[0] for value in history) / len(history),
            sum(value[1] for value in history) / len(history),
        )
    if name.startswith("recent_"):
        window = min(int(parameter), len(history))
        recent = history[-window:]
        return (
            sum(value[0] for value in recent) / len(recent),
            sum(value[1] for value in recent) / len(recent),
        )
    if name.startswith("ewma_"):
        weights = tuple(
            0.5 ** ((len(history) - 1 - index) / parameter)
            for index in range(len(history))
        )
        total = sum(weights)
        return (
            sum(
                weight * value[0]
                for weight, value in zip(weights, history, strict=True)
            )
            / total,
            sum(
                weight * value[1]
                for weight, value in zip(weights, history, strict=True)
            )
            / total,
        )
    window = min(int(parameter), len(history))
    recent = history[-window:]
    x_values = tuple(range(len(history) - window, len(history)))
    x_mean = sum(x_values) / len(x_values)
    denominator = sum((value - x_mean) ** 2 for value in x_values)
    future_x = tuple(range(len(history), len(history) + 5))
    forecasts = []
    for agent_index in range(2):
        y_mean = sum(value[agent_index] for value in recent) / len(recent)
        slope = (
            sum(
                (x_value - x_mean) * (value[agent_index] - y_mean)
                for x_value, value in zip(x_values, recent, strict=True)
            )
            / denominator
            if denominator > 0.0
            else 0.0
        )
        forecast = sum(
            y_mean + slope * (x_value - x_mean) for x_value in future_x
        ) / len(future_x)
        forecasts.append(max(0.0, min(1.0, forecast)))
    return forecasts[0], forecasts[1]


def _nearest_feasible_rates(
    history: Sequence[tuple[int, int]],
    target: tuple[float, float],
    budget: int,
) -> tuple[float, float]:
    categories = ((0, 0), (0, 1), (1, 0), (1, 1))
    counts = Counter(history)
    candidates = []
    for selected_counts in _bounded_compositions(
        tuple(counts[category] for category in categories),
        budget,
    ):
        rates = tuple(
            sum(
                count * category[index]
                for count, category in zip(
                    selected_counts,
                    categories,
                    strict=True,
                )
            )
            / budget
            for index in range(2)
        )
        candidates.append(
            (
                _mean_absolute_error(rates, target),
                sum((rates[index] - target[index]) ** 2 for index in range(2)),
                selected_counts,
                rates,
            )
        )
    return min(candidates)[-1]


def _semantic_candidates(
    views: Sequence[OriginView],
    outcome_by_task: Mapping[str, tuple[int, int]],
    agent_keys: Sequence[str],
    embeddings: EmbeddingData,
) -> tuple[tuple[Mapping[str, object], ...], Mapping[str, object]]:
    index_by_task = {
        task_id: index for index, task_id in enumerate(embeddings.task_ids)
    }
    gram = tuple(
        tuple(
            sum(left * right for left, right in zip(vector, other, strict=True))
            for other in embeddings.vectors
        )
        for vector in embeddings.vectors
    )
    specs: tuple[tuple[str, int, float], ...] = (
        *(
            (f"centroid_recent_{window}", window, 0.0)
            for window in (10, 15, 20, 25, 30, 40)
        ),
        *(
            (f"facility_recent_{window}", window, 0.0)
            for window in (10, 15, 20, 25, 30, 40)
        ),
        *(
            (f"centroid_trend_{window}_alpha_{alpha}", window, alpha)
            for window in (5, 10, 15, 20)
            for alpha in (0.5, 1.0)
        ),
    )
    rows = []
    for name, configured_window, alpha in specs:
        values = []
        selection_digests = []
        semantic_distances = []
        for view in views:
            history = tuple(index_by_task[item] for item in view.history_task_ids)
            future = tuple(index_by_task[item] for item in view.future_task_ids)
            window = min(configured_window, len(history))
            recent = history[-window:]
            if name.startswith("facility"):
                selected = _facility_location(history, recent, gram, 10)
            else:
                target_similarities = _embedding_target_similarities(
                    name,
                    history,
                    recent,
                    gram,
                    alpha,
                )
                selected = _centroid_coreset(
                    history,
                    target_similarities,
                    gram,
                    10,
                )
            selected_ids = tuple(embeddings.task_ids[index] for index in selected)
            selection_digests.append(canonical_digest(selected_ids))
            semantic_distances.append(_centroid_cosine_distance(selected, future, gram))
            values.append(
                _metric_values(
                    selected_ids,
                    view.future_task_ids,
                    outcome_by_task,
                    agent_keys,
                )
            )
        row = dict(_candidate_row("semantic_coreset", name, values))
        row["selection_membership_digests"] = tuple(selection_digests)
        row["semantic_future_centroid_cosine_distance"] = sum(semantic_distances) / len(
            semantic_distances
        )
        rows.append(row)
    return (
        tuple(sorted(rows, key=_candidate_sort_key)),
        {
            "baseline_mean_future_centroid_cosine_distance": (
                _semantic_alignment_baselines(views, index_by_task, gram)
            ),
            "interpretation": (
                "Lower embedding-centroid distance is descriptive. It is not "
                "an outcome metric or a Selector promotion target."
            ),
        },
    )


def _semantic_alignment_baselines(
    views: Sequence[OriginView],
    index_by_task: Mapping[str, int],
    gram: Sequence[Sequence[float]],
) -> Mapping[str, float]:
    selections = {
        "full_history": lambda view: view.history_task_ids,
        "coverage": lambda view: view.coverage_task_ids,
        "recency": lambda view: view.recency_task_ids,
    }
    return {
        name: sum(
            _centroid_cosine_distance(
                tuple(index_by_task[item] for item in selection(view)),
                tuple(index_by_task[item] for item in view.future_task_ids),
                gram,
            )
            for view in views
        )
        / len(views)
        for name, selection in selections.items()
    }


def _centroid_cosine_distance(
    left: Sequence[int],
    right: Sequence[int],
    gram: Sequence[Sequence[float]],
) -> float:
    if not left or not right:
        raise ValueError("centroid distance requires nonempty sets")
    dot = sum(
        gram[left_index][right_index] for left_index in left for right_index in right
    )
    left_norm_square = sum(
        gram[left_index][other_index] for left_index in left for other_index in left
    )
    right_norm_square = sum(
        gram[right_index][other_index] for right_index in right for other_index in right
    )
    denominator = math.sqrt(left_norm_square * right_norm_square)
    if denominator <= 0.0:
        raise ValueError("embedding centroid must have positive norm")
    cosine = dot / denominator
    return 1.0 - max(-1.0, min(1.0, cosine))


def _semantic_outcome_forecast_candidates(
    views: Sequence[OriginView],
    outcome_by_task: Mapping[str, tuple[int, int]],
    agent_keys: Sequence[str],
    embeddings: EmbeddingData,
) -> tuple[Mapping[str, object], ...]:
    index_by_task = {
        task_id: index for index, task_id in enumerate(embeddings.task_ids)
    }
    gram = tuple(
        tuple(
            sum(left * right for left, right in zip(vector, other, strict=True))
            for other in embeddings.vectors
        )
        for vector in embeddings.vectors
    )
    specs: tuple[tuple[str, int, float], ...] = (
        *(
            (f"semantic_knn_w{window}_k{neighbor_count}", window, neighbor_count)
            for window in (5, 10, 15, 20)
            for neighbor_count in (5, 10, 20)
        ),
        *(
            (f"semantic_softmax_w{window}_b{beta:g}", window, beta)
            for window in (5, 10, 15, 20)
            for beta in (1.0, 5.0, 10.0, 20.0)
        ),
    )
    rows = []
    for name, window, parameter in specs:
        values = []
        for view in views:
            history_ids = view.history_task_ids
            recent_ids = history_ids[-min(window, len(history_ids)) :]
            similarities = tuple(
                (
                    sum(
                        gram[index_by_task[task_id]][index_by_task[recent_id]]
                        for recent_id in recent_ids
                    )
                    / len(recent_ids),
                    task_id,
                )
                for task_id in history_ids
            )
            if "knn" in name:
                neighbor_count = min(int(parameter), len(similarities))
                neighbors = tuple(
                    task_id
                    for _, task_id in sorted(similarities, reverse=True)[
                        :neighbor_count
                    ]
                )
                target_rates = _rates(neighbors, outcome_by_task)
            else:
                target_rates = _similarity_weighted_rates(
                    similarities,
                    outcome_by_task,
                    beta=parameter,
                )
            selected_rates = _nearest_feasible_rates(
                tuple(outcome_by_task[task_id] for task_id in history_ids),
                target_rates,
                10,
            )
            values.append(
                _metrics_from_rates(
                    selected_rates,
                    _rates(view.future_task_ids, outcome_by_task),
                    agent_keys,
                )
            )
        rows.append(_candidate_row("semantic_outcome_forecast", name, values))
    return tuple(sorted(rows, key=_candidate_sort_key))


def _similarity_weighted_rates(
    similarities: Sequence[tuple[float, str]],
    outcome_by_task: Mapping[str, tuple[int, int]],
    *,
    beta: float,
) -> tuple[float, float]:
    maximum = max(similarity for similarity, _ in similarities)
    weights = tuple(
        math.exp(beta * (similarity - maximum)) for similarity, _ in similarities
    )
    total = sum(weights)
    return (
        sum(
            weight * outcome_by_task[task_id][0]
            for weight, (_, task_id) in zip(weights, similarities, strict=True)
        )
        / total,
        sum(
            weight * outcome_by_task[task_id][1]
            for weight, (_, task_id) in zip(weights, similarities, strict=True)
        )
        / total,
    )


def _embedding_target_similarities(
    name: str,
    history: Sequence[int],
    recent: Sequence[int],
    gram: Sequence[Sequence[float]],
    alpha: float,
) -> tuple[float, ...]:
    recent_similarities = tuple(
        sum(gram[index][candidate] for index in recent) / len(recent)
        for candidate in range(len(gram))
    )
    if not name.startswith("centroid_trend"):
        return recent_similarities
    previous = history[-2 * len(recent) : -len(recent)]
    if not previous:
        previous = history[: len(recent)]
    previous_similarities = tuple(
        sum(gram[index][candidate] for index in previous) / len(previous)
        for candidate in range(len(gram))
    )
    return tuple(
        (1.0 + alpha) * recent_value - alpha * previous_value
        for recent_value, previous_value in zip(
            recent_similarities,
            previous_similarities,
            strict=True,
        )
    )


def _centroid_coreset(
    universe: Sequence[int],
    target_similarities: Sequence[float],
    gram: Sequence[Sequence[float]],
    budget: int,
) -> tuple[int, ...]:
    selected: list[int] = []
    for round_index in range(budget):
        selected.append(
            max(
                (item for item in universe if item not in selected),
                key=lambda item: (
                    target_similarities[item]
                    - (
                        sum(gram[item][other] for other in selected) / (round_index + 1)
                        if selected
                        else 0.0
                    ),
                    -item,
                ),
            )
        )

    def objective(items: Sequence[int]) -> float:
        return (
            sum(gram[left][right] for left in items for right in items)
            / (budget * budget)
            - 2.0 * sum(target_similarities[item] for item in items) / budget
        )

    current = objective(selected)
    for _ in range(20):
        replacement: tuple[int, int] | None = None
        best = current
        selected_set = set(selected)
        for position, _old in enumerate(selected):
            for new in universe:
                if new in selected_set:
                    continue
                candidate = selected.copy()
                candidate[position] = new
                value = objective(candidate)
                if value < best - 1e-12:
                    best = value
                    replacement = position, new
        if replacement is None:
            break
        selected[replacement[0]] = replacement[1]
        current = best
    return tuple(selected)


def _facility_location(
    universe: Sequence[int],
    target: Sequence[int],
    gram: Sequence[Sequence[float]],
    budget: int,
) -> tuple[int, ...]:
    selected: list[int] = []
    best_similarities = [-2.0] * len(target)
    for _ in range(budget):

        def gain(candidate: int) -> float:
            return sum(
                max(current, gram[target_item][candidate]) - current
                for current, target_item in zip(
                    best_similarities,
                    target,
                    strict=True,
                )
            )

        chosen = max(
            (item for item in universe if item not in selected),
            key=lambda item: (gain(item), -item),
        )
        selected.append(chosen)
        best_similarities = [
            max(current, gram[target_item][chosen])
            for current, target_item in zip(
                best_similarities,
                target,
                strict=True,
            )
        ]
    return tuple(selected)


def _difficulty_candidates(
    views: Sequence[OriginView],
    outcome_by_task: Mapping[str, tuple[int, int]],
    agent_keys: Sequence[str],
) -> tuple[Mapping[str, object], ...]:
    rows = []
    for name, recency_tie_break in (
        ("mid_range_recent_tie_break", True),
        ("mid_range_oldest_tie_break", False),
    ):
        values = []
        for view in views:
            position = {
                task_id: index for index, task_id in enumerate(view.history_task_ids)
            }
            selected = tuple(
                sorted(
                    view.history_task_ids,
                    key=lambda task_id: (
                        abs(sum(outcome_by_task[task_id]) / 2.0 - 0.5),
                        (
                            -position[task_id]
                            if recency_tie_break
                            else position[task_id]
                        ),
                        task_id,
                    ),
                )[:10]
            )
            values.append(
                _metric_values(
                    selected,
                    view.future_task_ids,
                    outcome_by_task,
                    agent_keys,
                )
            )
        rows.append(_candidate_row("difficulty_information", name, values))
    return tuple(sorted(rows, key=_candidate_sort_key))


def _candidate_row(
    family: str,
    candidate: str,
    values: Sequence[MetricValues],
) -> Mapping[str, object]:
    summary: dict[str, object] = dict(_metric_summary(values))
    summary.update(
        {
            "family": family,
            "candidate": candidate,
            "outer_eight_macro_origin_mae": sum(
                value.future_pass_rate_mae for value in values[4:]
            )
            / len(values[4:]),
        }
    )
    return summary


def _candidate_sort_key(row: Mapping[str, object]) -> tuple[float, str]:
    return cast(float, row["macro_origin_mae"]), str(row["candidate"])


def _paired_contrast(values: Sequence[float]) -> Mapping[str, object]:
    return {
        "macro_origin_mae_difference": sum(values) / len(values),
        "origin_block_interval_95": _bootstrap_interval(values),
        "origins_favoring_selector": sum(value < 0.0 for value in values),
        "origins_tied": sum(math.isclose(value, 0.0) for value in values),
        "origins_favoring_baseline": sum(value > 0.0 for value in values),
        "origin_differences": tuple(values),
    }


def _prospective_origin_planning(
    differences: Sequence[float],
    practical_margin: float,
) -> Mapping[str, object]:
    if len(differences) < 2 or practical_margin <= 0.0:
        raise ValueError("prospective planning requires two Origins and a margin")
    mean = sum(differences) / len(differences)
    sample_variance = sum((value - mean) ** 2 for value in differences) / (
        len(differences) - 1
    )
    sample_standard_deviation = math.sqrt(sample_variance)

    def power_count(effect: float) -> int | None:
        if math.isclose(effect, 0.0, abs_tol=1e-15):
            return None
        return math.ceil(
            ((_Z_975 + _Z_80) * sample_standard_deviation / abs(effect)) ** 2
        )

    return {
        "status": "normal_approximation_planning_only",
        "sample_standard_deviation": sample_standard_deviation,
        "origins_for_80_percent_power_at_observed_effect": power_count(mean),
        "origins_for_80_percent_power_at_practical_effect": power_count(
            practical_margin
        ),
        "origins_for_95_percent_half_width_at_practical_margin": math.ceil(
            (_Z_975 * sample_standard_deviation / practical_margin) ** 2
        ),
        "limitation": (
            "Assumes independent identically distributed Origin contrasts; "
            "current dependency recurrence violates that assumption."
        ),
    }


def _bootstrap_interval(values: Sequence[float]) -> Mapping[str, object]:
    if len(values) < 8:
        return {
            "status": "insufficient_origin_blocks",
            "block_count": len(values),
            "lower": None,
            "upper": None,
        }
    rng = random.Random(BOOTSTRAP_SEED)
    sampled = sorted(
        sum(rng.choice(values) for _ in values) / len(values)
        for _ in range(BOOTSTRAP_RESAMPLES)
    )
    return {
        "status": "available",
        "block_count": len(values),
        "resamples": BOOTSTRAP_RESAMPLES,
        "seed": BOOTSTRAP_SEED,
        "lower": _empirical_quantile(sampled, 0.025),
        "upper": _empirical_quantile(sampled, 0.975),
    }


def _pmf_mean(pmf: Mapping[float, float]) -> float:
    return sum(value * probability for value, probability in pmf.items())


def _pmf_standard_deviation(pmf: Mapping[float, float]) -> float:
    mean = _pmf_mean(pmf)
    return math.sqrt(
        sum((value - mean) ** 2 * probability for value, probability in pmf.items())
    )


def _empirical_quantile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile requires values")
    index = max(0, min(len(values) - 1, math.ceil(probability * len(values)) - 1))
    return values[index]


def _mean_absolute_error(
    left: Sequence[float],
    right: Sequence[float],
) -> float:
    return sum(
        abs(left_value - right_value)
        for left_value, right_value in zip(left, right, strict=True)
    ) / len(left)


def _normalized_vector(values: Sequence[float]) -> tuple[float, ...]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= 0.0:
        raise ValueError("embedding vector must have positive norm")
    return tuple(float(value) / norm for value in values)


def _sign(value: float) -> int:
    return (value > 0.0) - (value < 0.0)


def _rounded(value: float) -> float:
    return round(value, _ROUND_DIGITS)


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_results(path: Path, results: Mapping[str, object]) -> None:
    path.write_text(canonical_json(results) + "\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--amendment", type=Path, default=DEFAULT_AMENDMENT)
    parser.add_argument("--embeddings", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--null-resamples", type=int)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    results = run_landscape(
        landscape_plan_path=arguments.plan,
        landscape_amendment_path=arguments.amendment,
        embedding_path=arguments.embeddings,
        null_resamples=arguments.null_resamples,
    )
    write_results(arguments.output, results)
    print(canonical_json(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
