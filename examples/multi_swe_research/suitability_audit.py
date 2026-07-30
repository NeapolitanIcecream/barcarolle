#!/usr/bin/env python3
"""Run the frozen candidate-free Multi-SWE suitability audit."""

from __future__ import annotations

# NumPy is supplied by the explicit reproduction command.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
import hashlib
import json
from math import fsum, isclose, isfinite
from pathlib import Path
import random
import statistics
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    canonical_digest,
    canonical_json,
    format_utc_timestamp,
    parse_utc_timestamp,
)
from examples.multi_repository_study.public_replay import (  # noqa: E402
    RepositoryOrigin,
    TaskMetadata,
    build_repository_origins,
)
from examples.multi_swe_research.semantic_selector import (  # noqa: E402
    load_public_outcomes,
)


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "suitability-audit-plan.json"
DEFAULT_TASK_UNIVERSE = HERE / "evidence" / "task-universe.jsonl"
DEFAULT_TASK_TIMES = HERE / "evidence" / "task-times.jsonl"
DEFAULT_PANEL_SUMMARY = HERE / "evidence" / "panel-summary.json"
DEFAULT_RESOLVED_OUTCOMES = HERE / "evidence" / "resolved-outcomes.jsonl"
DEFAULT_OUTCOME_RESULTS = (
    REPOSITORY_ROOT
    / "outputs"
    / "research"
    / "2026-07-28-multi-swe-semantic-outcome-results.json"
)
DEFAULT_HINDSIGHT_RESULTS = (
    REPOSITORY_ROOT
    / "outputs"
    / "research"
    / "2026-07-28-multi-swe-hindsight-results.json"
)

PLAN_SCHEMA = "barcarolle_multi_swe_suitability_audit_plan_v1"
RESULT_SCHEMA = "barcarolle_multi_swe_suitability_audit_result_v1"
SUMMARY_SCHEMA = "barcarolle_multi_swe_suitability_audit_summary_v1"


def load_suitability_audit_plan(
    path: Path = DEFAULT_PLAN,
) -> Mapping[str, Any]:
    """Load and validate the frozen audit plan."""
    payload = dict(_load_mapping(path))
    digest = payload.pop("suitability_audit_plan_digest", None)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("suitability audit plan schema is unsupported")
    if digest != canonical_digest(payload):
        raise ValueError("suitability audit plan digest does not match")
    payload["suitability_audit_plan_digest"] = digest

    authority = _mapping(payload, "authority")
    if (
        authority.get("paid_api_calls") != 0
        or authority.get("sealed_swe_bench_holdout_agents_opened") != 0
        or authority.get("new_public_outcome_panels_opened") != 0
        or authority.get("generator_development") is not False
    ):
        raise ValueError("suitability audit authority changed")

    frame = _mapping(payload, "frame")
    horizon_rows = _mapping_sequence(frame, "horizons")
    if tuple(_positive_integer(row, "future_tasks") for row in horizon_rows) != (
        5,
        10,
    ):
        raise ValueError("suitability audit horizons changed")
    null = _mapping(payload, "temporal_null")
    uncertainty = _mapping(payload, "uncertainty")
    if (
        _positive_integer(null, "draws") != 2000
        or _finite_number(null.get("alpha"), "null alpha") != 0.05
        or _positive_integer(uncertainty, "repository_bootstrap_resamples")
        != 10000
    ):
        raise ValueError("suitability audit diagnostic size changed")
    return payload


def load_suitability_result(
    path: Path,
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Load a self-digested result bound to the frozen plan."""
    payload = dict(_load_mapping(path))
    digest = payload.pop("suitability_audit_result_digest", None)
    if payload.get("schema_version") != RESULT_SCHEMA:
        raise ValueError("suitability audit result schema is unsupported")
    if digest != canonical_digest(payload):
        raise ValueError("suitability audit result digest does not match")
    if payload.get("suitability_audit_plan_digest") != plan.get(
        "suitability_audit_plan_digest"
    ):
        raise ValueError("suitability audit result does not bind the plan")
    payload["suitability_audit_result_digest"] = digest
    return payload


def load_suitability_summary(
    path: Path,
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Load a committed compact summary bound to the frozen plan."""
    payload = dict(_load_mapping(path))
    digest = payload.pop("suitability_audit_summary_digest", None)
    if payload.get("schema_version") != SUMMARY_SCHEMA:
        raise ValueError("suitability audit summary schema is unsupported")
    if digest != canonical_digest(payload):
        raise ValueError("suitability audit summary digest does not match")
    if _mapping(payload, "identities").get(
        "suitability_audit_plan_digest"
    ) != plan.get("suitability_audit_plan_digest"):
        raise ValueError("suitability audit summary does not bind the plan")
    payload["suitability_audit_summary_digest"] = digest
    return payload


def load_task_metadata(
    task_universe_path: Path,
    task_times_path: Path,
    plan: Mapping[str, object],
) -> tuple[TaskMetadata, ...]:
    """Load the byte-bound Task universe and projected source times."""
    source = _mapping(plan, "source")
    _require_sha256(
        task_universe_path,
        _required_string(source, "task_universe_file_sha256"),
    )
    _require_sha256(
        task_times_path,
        _required_string(source, "task_times_file_sha256"),
    )
    universe = _load_jsonl(task_universe_path)
    times = _load_jsonl(task_times_path)
    if len(universe) != _positive_integer(source, "task_count"):
        raise ValueError("suitability Task count changed")

    universe_by_id: dict[str, Mapping[str, Any]] = {}
    for row in universe:
        task_id = _required_string(row, "instance_id")
        if task_id in universe_by_id:
            raise ValueError("suitability Task universe has duplicate IDs")
        universe_by_id[task_id] = row
    time_by_id: dict[str, Mapping[str, Any]] = {}
    for row in times:
        task_id = _required_string(row, "instance_id")
        if task_id in time_by_id:
            raise ValueError("suitability Task times have duplicate IDs")
        time_by_id[task_id] = row
    if set(universe_by_id) != set(time_by_id):
        raise ValueError("suitability Task universe and times differ")
    if canonical_digest(times) != source.get("task_time_projection_digest"):
        raise ValueError("suitability Task-time projection digest changed")

    tasks = []
    for task_id in sorted(universe_by_id):
        universe_row = universe_by_id[task_id]
        time_row = time_by_id[task_id]
        repository_id = _required_string(universe_row, "repository")
        if _required_string(time_row, "repository") != repository_id:
            raise ValueError("suitability Task repository changed")
        tasks.append(
            TaskMetadata(
                instance_id=task_id,
                repository_id=repository_id,
                created_at=format_utc_timestamp(
                    parse_utc_timestamp(
                        _required_string(time_row, "created_at")
                    )
                ),
                difficulty=_required_string(universe_row, "language"),
                problem_statement="source-projected Multi-SWE Task",
            )
        )
    return tuple(tasks)


def run_suitability_audit(
    tasks: Sequence[TaskMetadata],
    outcomes_by_configuration: Mapping[str, Mapping[str, int]],
    configuration_metadata: Sequence[Mapping[str, str]],
    outcome_diagnostics: Mapping[str, object],
    outcome_results: Mapping[str, object],
    hindsight_results: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Execute the frozen H5/H10 candidate-free audit."""
    import numpy as np

    source = _mapping(plan, "source")
    if (
        len(tasks) != _positive_integer(source, "task_count")
        or len(configuration_metadata)
        != _positive_integer(source, "configuration_count")
        or set(outcomes_by_configuration)
        != {
            _required_string(row, "configuration_id")
            for row in configuration_metadata
        }
    ):
        raise ValueError("suitability panel dimensions changed")

    configuration_ids = tuple(
        _required_string(row, "configuration_id")
        for row in configuration_metadata
    )
    metadata_by_configuration = {
        _required_string(row, "configuration_id"): row
        for row in configuration_metadata
    }
    frame = _mapping(plan, "frame")
    minimum_history = _positive_integer(
        frame,
        "minimum_initial_history_tasks",
    )
    budget = _positive_integer(frame, "selection_budget_tasks")
    origins_by_horizon = {
        _positive_integer(row, "future_tasks"): build_repository_origins(
            tasks,
            minimum_initial_history_tasks=minimum_history,
            future_block_tasks=_positive_integer(row, "future_tasks"),
        )
        for row in _mapping_sequence(frame, "horizons")
    }
    outcome_horizons = _mapping(outcome_results, "horizons")
    hindsight_horizons = _mapping(hindsight_results, "horizons")

    horizon_results = {}
    for horizon_row in _mapping_sequence(frame, "horizons"):
        horizon = _positive_integer(horizon_row, "future_tasks")
        outcome_horizon = _mapping(outcome_horizons, str(horizon))
        hindsight_horizon = _mapping(hindsight_horizons, str(horizon))
        repository_ids = _string_tuple(
            outcome_horizon.get("repository_ids"),
            f"H{horizon} repositories",
        )
        if repository_ids != _string_tuple(
            hindsight_horizon.get("repository_ids"),
            f"H{horizon} hindsight repositories",
        ):
            raise ValueError("suitability outcome and hindsight frames differ")
        origins_by_repository = origins_by_horizon[horizon]
        expected_origin_count = _positive_integer(horizon_row, "origin_count")
        if (
            len(repository_ids)
            != _positive_integer(horizon_row, "repository_count")
            or sum(
                len(origins_by_repository.get(repository_id, ()))
                for repository_id in repository_ids
            )
            != expected_origin_count
        ):
            raise ValueError("suitability Origin frame changed")

        horizon_results[str(horizon)] = _evaluate_horizon(
            np=np,
            horizon=horizon,
            budget=budget,
            repository_ids=repository_ids,
            origins_by_repository=origins_by_repository,
            outcomes_by_configuration=outcomes_by_configuration,
            configuration_ids=configuration_ids,
            metadata_by_configuration=metadata_by_configuration,
            outcome_horizon=outcome_horizon,
            hindsight_horizon=hindsight_horizon,
            plan=plan,
        )

    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "epistemic_status": plan.get("epistemic_status"),
        "suitability_audit_plan_digest": plan.get(
            "suitability_audit_plan_digest"
        ),
        "identities": {
            "panel_digest": outcome_diagnostics.get("panel_digest"),
            "resolved_outcome_digest": outcome_diagnostics.get(
                "resolved_outcome_digest"
            ),
            "task_time_projection_digest": source.get(
                "task_time_projection_digest"
            ),
            "outcome_results_digest": outcome_results.get(
                "outcome_results_digest"
            ),
            "hindsight_results_digest": hindsight_results.get(
                "hindsight_results_digest"
            ),
        },
        "task_count": len(tasks),
        "configuration_count": len(configuration_ids),
        "implementation": {
            "implementation_file_sha256": _file_sha256(
                Path(__file__).resolve()
            ),
            "python_version": sys.version.split()[0],
            "numpy_version": np.__version__,
        },
        "horizons": horizon_results,
        "decision": {
            "panel_status": "descriptive_only",
            "selector_nominated": False,
            "practical_main_region_nominated": False,
            "workload_relevance_resolved": False,
            "deployment_useful_margin_declared": False,
            "cross_source_extension": _cross_source_decision(horizon_results),
        },
        "resource_use": {
            "paid_api_calls": 0,
            "sealed_swe_bench_holdout_agents_opened": 0,
            "new_public_outcome_panels_opened": 0,
            "generator_development": False,
        },
        "claim_boundary": (
            "Opened public outcomes and projected Task times support a "
            "candidate-free source-time counterfactual diagnostic only. The "
            "result cannot nominate a Selector, practical workload region, "
            "strict-prospective claim, or failure cause."
        ),
    }
    result["suitability_audit_result_digest"] = canonical_digest(result)
    return result


def _evaluate_horizon(
    *,
    np: Any,
    horizon: int,
    budget: int,
    repository_ids: Sequence[str],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes_by_configuration: Mapping[str, Mapping[str, int]],
    configuration_ids: Sequence[str],
    metadata_by_configuration: Mapping[str, Mapping[str, str]],
    outcome_horizon: Mapping[str, object],
    hindsight_horizon: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    repository_rows = []
    panel_arrays: dict[str, Mapping[str, Any]] = {}
    for repository_id in repository_ids:
        origins = tuple(origins_by_repository.get(repository_id, ()))
        if not origins:
            raise ValueError("suitability repository has no Origin")
        ordered_tasks = (*origins[-1].history, *origins[-1].future)
        if len({task.instance_id for task in ordered_tasks}) != len(ordered_tasks):
            raise ValueError("suitability repository Task order is invalid")
        response = np.asarray(
            [
                [
                    outcomes_by_configuration[configuration_id][task.instance_id]
                    for configuration_id in configuration_ids
                ]
                for task in ordered_tasks
            ],
            dtype=np.float64,
        )
        starts = tuple(len(origin.history) for origin in origins)
        if any(
            tuple(task.instance_id for task in origin.future)
            != tuple(
                task.instance_id
                for task in ordered_tasks[start : start + horizon]
            )
            for origin, start in zip(origins, starts, strict=True)
        ):
            raise ValueError("suitability Origin membership changed")
        row = _observed_repository_row(
            np,
            repository_id,
            origins,
            response,
            starts,
            horizon,
            configuration_ids,
        )
        repository_rows.append(row)
        panel_arrays[repository_id] = {
            "response": response,
            "starts": starts,
        }

    control_names = (
        "always_zero_mae",
        "always_one_mae",
        "full_history_mae",
        "cached_expanding_median_mae",
    )
    controls = {
        name: _mean(
            tuple(_finite_number(row.get(name), name) for row in repository_rows)
        )
        for name in control_names
    }
    strongest_trivial_name = min(
        ("always_zero_mae", "always_one_mae"),
        key=lambda name: controls[name],
    )
    strongest_trivial = controls[strongest_trivial_name]
    full_history = controls["full_history_mae"]

    pooled = {
        name: _weighted_mean(
            tuple(
                (
                    _finite_number(row.get(name), name),
                    _positive_integer(row, "origin_count"),
                )
                for row in repository_rows
            )
        )
        for name in control_names
    }
    pooled_agent_origin_count = sum(
        _positive_integer(row, "agent_origin_count") for row in repository_rows
    )
    pooled_zero_blocks = sum(
        _positive_or_zero_integer(row, "all_zero_agent_origin_count")
        for row in repository_rows
    )
    pooled_one_blocks = sum(
        _positive_or_zero_integer(row, "all_one_agent_origin_count")
        for row in repository_rows
    )
    pooled_future_cells = sum(
        _positive_integer(row, "future_cell_count") for row in repository_rows
    )
    pooled_positive_future_cells = sum(
        _positive_or_zero_integer(row, "positive_future_cell_count")
        for row in repository_rows
    )

    oracle = _mapping(_mapping(hindsight_horizon, "exact_hindsight"), "wide")
    oracle_mae = _finite_number(
        oracle.get("macro_repository_loss"),
        "oracle MAE",
    )
    if not isclose(
        _finite_number(
            oracle.get("macro_repository_baseline_loss"),
            "oracle baseline",
        ),
        full_history,
        abs_tol=1e-12,
    ):
        raise ValueError("suitability oracle baseline changed")
    oracle_rows = {
        _required_string(row, "repository_id"): row
        for row in _mapping_sequence(oracle, "repository_rows")
    }
    if set(oracle_rows) != set(repository_ids):
        raise ValueError("suitability oracle repositories changed")

    random_row = _mapping(outcome_horizon, "random_calibration")
    random_difference = _finite_number(
        random_row.get("mean_macro_repository_difference"),
        "random mean difference",
    )
    random_quantiles = _mapping(random_row, "quantiles")
    random_control = {
        "draw_count": _positive_integer(random_row, "draw_count"),
        "seed": _positive_integer(random_row, "seed"),
        "generator": _required_string(random_row, "generator"),
        "mean_mae": full_history + random_difference,
        "mean_minus_full_history": random_difference,
        "mae_quantiles": {
            key: full_history
            + _finite_number(random_quantiles.get(key), f"random quantile {key}")
            for key in ("0.025", "0.5", "0.975")
        },
    }

    differences = tuple(
        _finite_number(row.get("full_minus_zero"), "full-minus-zero")
        for row in repository_rows
    )
    uncertainty_plan = _mapping(plan, "uncertainty")
    bootstrap = _bootstrap_interval(
        differences,
        resamples=_positive_integer(
            uncertainty_plan,
            "repository_bootstrap_resamples",
        ),
        seed=_positive_integer(
            uncertainty_plan,
            "repository_bootstrap_seed",
        )
        + horizon,
    )
    leave_one_out = tuple(
        {
            "omitted_repository_id": repository_id,
            "macro_repository_full_minus_zero": _mean(
                tuple(
                    value
                    for offset, value in enumerate(differences)
                    if offset != index
                )
            ),
        }
        for index, repository_id in enumerate(repository_ids)
    )
    null = _temporal_null(
        np=np,
        panel_arrays=panel_arrays,
        horizon=horizon,
        draws=_positive_integer(_mapping(plan, "temporal_null"), "draws"),
        seed=_positive_integer(_mapping(plan, "temporal_null"), "seed")
        + horizon,
    )
    if not isclose(_mean(differences), null["observed"], abs_tol=1e-12):
        raise ValueError("suitability observed and null statistics differ")

    configuration_rows = _configuration_rows(
        repository_rows,
        configuration_ids,
        metadata_by_configuration,
    )
    harness_rows = _group_configuration_rows(
        configuration_rows,
        "harness_family",
    )
    model_rows = _group_configuration_rows(
        configuration_rows,
        "model_family",
    )
    calendar_cutoff_to_end = tuple(
        value
        for row in repository_rows
        for value in _number_sequence(
            row.get("cutoff_to_future_end_days"),
            "cutoff-to-future-end days",
        )
    )
    calendar_future_width = tuple(
        value
        for row in repository_rows
        for value in _number_sequence(
            row.get("future_window_width_days"),
            "future window width days",
        )
    )

    alpha = _finite_number(
        _mapping(plan, "temporal_null").get("alpha"),
        "null alpha",
    )
    full_minus_zero = full_history - controls["always_zero_mae"]
    every_loo_negative = all(
        _finite_number(
            row["macro_repository_full_minus_zero"],
            "leave-one-repository-out difference",
        )
        < 0.0
        for row in leave_one_out
    )
    persistence_detected = (
        full_minus_zero < 0.0
        and _finite_number(bootstrap["upper"], "bootstrap upper") < 0.0
        and every_loo_negative
        and _finite_number(null["one_sided_probability"], "null probability")
        <= alpha
    )
    capacity_present = (
        oracle_mae < full_history and oracle_mae < strongest_trivial
    )
    full_dominated = strongest_trivial <= full_history
    if full_dominated:
        terminal_state = "unseen_estimator_full_dominated"
    elif capacity_present and persistence_detected:
        terminal_state = "history_persistence_detected_on_counterfactual_panel"
    elif capacity_present:
        terminal_state = "capacity_without_detected_history_persistence"
    else:
        terminal_state = "resolution_or_contract_limited"

    random_control["oracle_mae"] = oracle_mae
    random_control["selection_headroom"] = full_history - oracle_mae
    random_control["strongest_unseen_trivial"] = strongest_trivial_name
    random_control["trivial_separation_full"] = (
        strongest_trivial - full_history
    )
    random_control["trivial_relative_headroom"] = (
        strongest_trivial - oracle_mae
    )
    random_control["selection_capture"] = None

    for row in repository_rows:
        repository_id = _required_string(row, "repository_id")
        oracle_row = oracle_rows[repository_id]
        row["oracle_mae"] = _finite_number(
            oracle_row.get("mean_loss"),
            "repository oracle MAE",
        )
        row["selection_headroom"] = (
            _finite_number(row.get("full_history_mae"), "repository full MAE")
            - _finite_number(row.get("oracle_mae"), "repository oracle MAE")
        )

    return {
        "frame": {
            "future_tasks": horizon,
            "selection_budget_tasks": budget,
            "repository_ids": tuple(repository_ids),
            "repository_count": len(repository_ids),
            "origin_count": sum(
                _positive_integer(row, "origin_count")
                for row in repository_rows
            ),
            "origin_alignment": "end_aligned_complete_nonoverlapping",
            "primary_aggregation": "equal_repository",
            "secondary_aggregation": "pooled_origin",
            "task_time_status": "projected_pull_request_created_at",
            "result_availability_status": "not_historically_attested",
        },
        "prevalence": {
            "equal_repository_future_density": controls["always_zero_mae"],
            "pooled_future_density": (
                pooled_positive_future_cells / pooled_future_cells
            ),
            "pooled_agent_origin_count": pooled_agent_origin_count,
            "all_zero_agent_origin_count": pooled_zero_blocks,
            "all_zero_agent_origin_share": (
                pooled_zero_blocks / pooled_agent_origin_count
            ),
            "all_one_agent_origin_count": pooled_one_blocks,
            "all_one_agent_origin_share": (
                pooled_one_blocks / pooled_agent_origin_count
            ),
        },
        "controls": {
            "equal_repository": {
                **controls,
                **random_control,
            },
            "pooled_origin": pooled,
            "information_contract": {
                "always_zero_and_one": "unseen_target_estimator_diagnostic",
                "full_history": "target_history_no_selection_evidence",
                "cached_expanding_median": "cached_target_only",
                "random": "budget_matched_selection_calibration",
                "oracle": "future_open_capacity_diagnostic",
            },
        },
        "uncertainty": {
            "contrast": "full_history_minus_always_zero",
            "observed": full_minus_zero,
            "repository_bootstrap_interval_95": {
                "lower": bootstrap["lower"],
                "upper": bootstrap["upper"],
                "width": bootstrap["upper"] - bootstrap["lower"],
                "half_width": (
                    bootstrap["upper"] - bootstrap["lower"]
                )
                / 2.0,
            },
            "repository_bootstrap_resamples": bootstrap["resamples"],
            "repository_bootstrap_values_digest": bootstrap["values_digest"],
            "leave_one_repository_out": leave_one_out,
            "every_leave_one_repository_out_negative": every_loo_negative,
            "deployment_useful_margin": None,
            "configuration_rows": configuration_rows,
            "harness_rows": harness_rows,
            "model_rows": model_rows,
        },
        "calendar": {
            "cutoff_to_future_end_days": _distribution_summary(
                calendar_cutoff_to_end
            ),
            "future_window_width_days": _distribution_summary(
                calendar_future_width
            ),
            "interpretation": (
                "Task-count H is a research frame, not one deployment "
                "TimeRange."
            ),
        },
        "temporal_null": null,
        "repository_rows": tuple(repository_rows),
        "decision": {
            "terminal_state": terminal_state,
            "panel_status": "descriptive_only",
            "unseen_estimator_full_dominated": full_dominated,
            "budget_ten_capacity_present": capacity_present,
            "history_persistence_detected": persistence_detected,
            "selector_nominated": False,
            "practical_main_region_nominated": False,
        },
    }


def _observed_repository_row(
    np: Any,
    repository_id: str,
    origins: Sequence[RepositoryOrigin],
    response: Any,
    starts: Sequence[int],
    horizon: int,
    configuration_ids: Sequence[str],
) -> dict[str, Any]:
    cumulative = np.vstack(
        (
            np.zeros((1, response.shape[1]), dtype=np.float64),
            np.cumsum(response, axis=0),
        )
    )
    history_rates = np.asarray(
        [cumulative[start] / start for start in starts],
        dtype=np.float64,
    )
    future_rates = np.asarray(
        [
            (cumulative[start + horizon] - cumulative[start]) / horizon
            for start in starts
        ],
        dtype=np.float64,
    )
    climatology_rates = []
    for index in range(len(starts)):
        if index == 0:
            climatology_rates.append(history_rates[index])
        else:
            climatology_rates.append(
                np.median(future_rates[:index], axis=0)
            )
    climatology = np.asarray(climatology_rates, dtype=np.float64)

    zero_losses = future_rates
    one_losses = 1.0 - future_rates
    full_losses = np.abs(history_rates - future_rates)
    climatology_losses = np.abs(climatology - future_rates)
    origin_rows = []
    cutoff_to_end_days = []
    future_window_width_days = []
    for origin_index, origin in enumerate(origins):
        cutoff = parse_utc_timestamp(origin.history[-1].created_at)
        future_start = parse_utc_timestamp(origin.future[0].created_at)
        future_end = parse_utc_timestamp(origin.future[-1].created_at)
        cutoff_to_end = (future_end - cutoff).total_seconds() / 86400.0
        future_width = (future_end - future_start).total_seconds() / 86400.0
        cutoff_to_end_days.append(cutoff_to_end)
        future_window_width_days.append(future_width)
        origin_rows.append(
            {
                "origin_id": origin.origin_id,
                "history_task_count": len(origin.history),
                "future_task_count": len(origin.future),
                "always_zero_mae": float(np.mean(zero_losses[origin_index])),
                "always_one_mae": float(np.mean(one_losses[origin_index])),
                "full_history_mae": float(np.mean(full_losses[origin_index])),
                "cached_expanding_median_mae": float(
                    np.mean(climatology_losses[origin_index])
                ),
                "all_zero_configuration_count": int(
                    np.sum(future_rates[origin_index] == 0.0)
                ),
                "all_one_configuration_count": int(
                    np.sum(future_rates[origin_index] == 1.0)
                ),
                "cutoff_to_future_end_days": cutoff_to_end,
                "future_window_width_days": future_width,
            }
        )

    configuration_controls = {
        configuration_id: {
            "always_zero_mae": float(np.mean(zero_losses[:, index])),
            "always_one_mae": float(np.mean(one_losses[:, index])),
            "full_history_mae": float(np.mean(full_losses[:, index])),
            "cached_expanding_median_mae": float(
                np.mean(climatology_losses[:, index])
            ),
        }
        for index, configuration_id in enumerate(configuration_ids)
    }
    return {
        "repository_id": repository_id,
        "origin_count": len(origins),
        "agent_origin_count": len(origins) * len(configuration_ids),
        "future_cell_count": len(origins) * horizon * len(configuration_ids),
        "positive_future_cell_count": int(
            round(float(np.sum(future_rates)) * horizon)
        ),
        "all_zero_agent_origin_count": int(np.sum(future_rates == 0.0)),
        "all_one_agent_origin_count": int(np.sum(future_rates == 1.0)),
        "always_zero_mae": float(np.mean(zero_losses)),
        "always_one_mae": float(np.mean(one_losses)),
        "full_history_mae": float(np.mean(full_losses)),
        "cached_expanding_median_mae": float(
            np.mean(climatology_losses)
        ),
        "full_minus_zero": float(np.mean(full_losses - zero_losses)),
        "configuration_controls": configuration_controls,
        "cutoff_to_future_end_days": tuple(cutoff_to_end_days),
        "future_window_width_days": tuple(future_window_width_days),
        "origin_rows": tuple(origin_rows),
    }


def _temporal_null(
    *,
    np: Any,
    panel_arrays: Mapping[str, Mapping[str, Any]],
    horizon: int,
    draws: int,
    seed: int,
) -> Mapping[str, Any]:
    repository_ids = tuple(sorted(panel_arrays))
    observed = _mean(
        tuple(
            _full_minus_zero_for_response(
                np,
                panel_arrays[repository_id]["response"],
                panel_arrays[repository_id]["starts"],
                horizon,
            )
            for repository_id in repository_ids
        )
    )
    generator = random.Random(seed)
    null_values = []
    for _ in range(draws):
        repository_values = []
        for repository_id in repository_ids:
            response = panel_arrays[repository_id]["response"]
            offset = generator.randrange(int(response.shape[0]))
            shifted = np.roll(response, shift=offset, axis=0)
            repository_values.append(
                _full_minus_zero_for_response(
                    np,
                    shifted,
                    panel_arrays[repository_id]["starts"],
                    horizon,
                )
            )
        null_values.append(_mean(tuple(repository_values)))
    ordered = tuple(sorted(null_values))
    as_good_or_better = sum(value <= observed + 1e-15 for value in ordered)
    return {
        "statistic": "equal_repository_full_history_minus_always_zero",
        "observed": observed,
        "draws": draws,
        "seed": seed,
        "null_mean": _mean(ordered),
        "null_interval_95": {
            "lower": _quantile(ordered, 0.025),
            "upper": _quantile(ordered, 0.975),
        },
        "one_sided_probability": (as_good_or_better + 1) / (draws + 1),
        "null_values_digest": canonical_digest(tuple(null_values)),
        "construction": (
            "independent inclusive-zero within-repository circular shifts of "
            "complete joint configuration-response rows"
        ),
        "interpretation": (
            "Tests aggregate history persistence aligned to observed Task "
            "chronology; it does not test every possible pre-Origin feature."
        ),
    }


def _full_minus_zero_for_response(
    np: Any,
    response: Any,
    starts: Sequence[int],
    horizon: int,
) -> float:
    cumulative = np.vstack(
        (
            np.zeros((1, response.shape[1]), dtype=np.float64),
            np.cumsum(response, axis=0),
        )
    )
    differences = []
    for start in starts:
        history_rate = cumulative[start] / start
        future_rate = (
            cumulative[start + horizon] - cumulative[start]
        ) / horizon
        differences.append(float(np.mean(np.abs(history_rate - future_rate) - future_rate)))
    return _mean(tuple(differences))


def _configuration_rows(
    repository_rows: Sequence[Mapping[str, Any]],
    configuration_ids: Sequence[str],
    metadata_by_configuration: Mapping[str, Mapping[str, str]],
) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for configuration_id in configuration_ids:
        controls = tuple(
            _mapping(
                _mapping(row, "configuration_controls"),
                configuration_id,
            )
            for row in repository_rows
        )
        metadata = metadata_by_configuration[configuration_id]
        zero = _mean(
            tuple(
                _finite_number(row.get("always_zero_mae"), "configuration zero")
                for row in controls
            )
        )
        full = _mean(
            tuple(
                _finite_number(row.get("full_history_mae"), "configuration full")
                for row in controls
            )
        )
        rows.append(
            {
                "configuration_id": configuration_id,
                "harness_family": _required_string(
                    metadata,
                    "harness_family",
                ),
                "model_family": _required_string(metadata, "model_family"),
                "always_zero_mae": zero,
                "full_history_mae": full,
                "full_minus_zero": full - zero,
                "cached_expanding_median_mae": _mean(
                    tuple(
                        _finite_number(
                            row.get("cached_expanding_median_mae"),
                            "configuration climatology",
                        )
                        for row in controls
                    )
                ),
            }
        )
    return tuple(rows)


def _group_configuration_rows(
    rows: Sequence[Mapping[str, Any]],
    group_key: str,
) -> tuple[Mapping[str, Any], ...]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_required_string(row, group_key)].append(row)
    return tuple(
        {
            group_key: group_id,
            "configuration_count": len(group_rows),
            "mean_full_minus_zero": _mean(
                tuple(
                    _finite_number(row.get("full_minus_zero"), "group difference")
                    for row in group_rows
                )
            ),
            "favorable_configuration_count": sum(
                _finite_number(row.get("full_minus_zero"), "group difference")
                < 0.0
                for row in group_rows
            ),
        }
        for group_id, group_rows in sorted(grouped.items())
    )


def _bootstrap_interval(
    values: Sequence[float],
    *,
    resamples: int,
    seed: int,
) -> Mapping[str, Any]:
    rows = tuple(values)
    if len(rows) < 2:
        raise ValueError("repository bootstrap requires at least two rows")
    generator = random.Random(seed)
    draws = tuple(
        _mean(
            tuple(
                rows[generator.randrange(len(rows))]
                for _ in range(len(rows))
            )
        )
        for _ in range(resamples)
    )
    ordered = tuple(sorted(draws))
    return {
        "lower": _quantile(ordered, 0.025),
        "upper": _quantile(ordered, 0.975),
        "resamples": resamples,
        "seed": seed,
        "values_digest": canonical_digest(draws),
    }


def _distribution_summary(values: Sequence[float]) -> Mapping[str, float]:
    rows = tuple(values)
    if not rows:
        raise ValueError("distribution summary requires values")
    return {
        "minimum": min(rows),
        "median": statistics.median(rows),
        "maximum": max(rows),
    }


def _cross_source_decision(
    horizons: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    decisions = {
        horizon: _mapping(payload, "decision").get("terminal_state")
        for horizon, payload in sorted(horizons.items())
    }
    return {
        "status": "defer_until_pilot_interpretation",
        "horizon_terminal_states": decisions,
        "automatic_atlas_expansion": False,
        "swe_bench_full_status": "normalization_gated",
    }


def build_suitability_summary(
    result: Mapping[str, object],
    reproduction: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Build a compact committed summary from two identical raw runs."""
    _validate_in_memory_result(result, plan)
    _validate_in_memory_result(reproduction, plan)
    byte_identical = canonical_json(result) == canonical_json(reproduction)
    if not byte_identical:
        raise ValueError("suitability audit reproduction is not byte-identical")

    compact_horizons = {}
    for horizon, payload in sorted(_mapping(result, "horizons").items()):
        frame = _mapping(payload, "frame")
        prevalence = _mapping(payload, "prevalence")
        controls = _mapping(_mapping(payload, "controls"), "equal_repository")
        uncertainty = _mapping(payload, "uncertainty")
        interval = _mapping(uncertainty, "repository_bootstrap_interval_95")
        null = _mapping(payload, "temporal_null")
        calendar = _mapping(payload, "calendar")
        decision = _mapping(payload, "decision")
        configuration_rows = _mapping_sequence(uncertainty, "configuration_rows")
        compact_horizons[f"h{horizon}"] = {
            "repository_count": frame.get("repository_count"),
            "origin_count": frame.get("origin_count"),
            "future_tasks": frame.get("future_tasks"),
            "all_zero_agent_origin_share": prevalence.get(
                "all_zero_agent_origin_share"
            ),
            "all_one_agent_origin_share": prevalence.get(
                "all_one_agent_origin_share"
            ),
            "pooled_future_density": prevalence.get("pooled_future_density"),
            "equal_repository_future_density": prevalence.get(
                "equal_repository_future_density"
            ),
            "always_zero_mae": controls.get("always_zero_mae"),
            "always_one_mae": controls.get("always_one_mae"),
            "full_history_mae": controls.get("full_history_mae"),
            "cached_expanding_median_mae": controls.get(
                "cached_expanding_median_mae"
            ),
            "random_mean_mae": controls.get("mean_mae"),
            "oracle_mae": controls.get("oracle_mae"),
            "selection_headroom": controls.get("selection_headroom"),
            "trivial_separation_full": controls.get(
                "trivial_separation_full"
            ),
            "trivial_relative_headroom": controls.get(
                "trivial_relative_headroom"
            ),
            "full_minus_zero": uncertainty.get("observed"),
            "repository_bootstrap_interval_95": {
                "lower": interval.get("lower"),
                "upper": interval.get("upper"),
                "width": interval.get("width"),
                "half_width": interval.get("half_width"),
            },
            "leave_one_repository_out_all_negative": uncertainty.get(
                "every_leave_one_repository_out_negative"
            ),
            "configuration_directions_favorable": (
                f"{sum(_finite_number(row.get('full_minus_zero'), 'configuration difference') < 0.0 for row in configuration_rows)}/{len(configuration_rows)}"
            ),
            "temporal_null": {
                "observed": null.get("observed"),
                "null_mean": null.get("null_mean"),
                "null_interval_95": null.get("null_interval_95"),
                "one_sided_probability": null.get(
                    "one_sided_probability"
                ),
                "draws": null.get("draws"),
                "values_digest": null.get("null_values_digest"),
            },
            "calendar_cutoff_to_future_end_days": calendar.get(
                "cutoff_to_future_end_days"
            ),
            "terminal_state": decision.get("terminal_state"),
            "budget_ten_capacity_present": decision.get(
                "budget_ten_capacity_present"
            ),
            "history_persistence_detected": decision.get(
                "history_persistence_detected"
            ),
        }

    summary: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "study_id": result.get("study_id"),
        "epistemic_status": result.get("epistemic_status"),
        "identities": {
            "suitability_audit_plan_digest": plan.get(
                "suitability_audit_plan_digest"
            ),
            **dict(_mapping(result, "identities")),
            "suitability_audit_result_digest": result.get(
                "suitability_audit_result_digest"
            ),
        },
        "reproduction": {
            "byte_identical_second_run": byte_identical,
            "result_digest": result.get("suitability_audit_result_digest"),
        },
        "protocol": {
            "task_count": result.get("task_count"),
            "configuration_count": result.get("configuration_count"),
            "primary_metric": "future pass-rate MAE",
            "primary_aggregation": "equal repository",
            "origin_alignment": "end-aligned complete non-overlapping blocks",
            "information_contract": (
                "unseen-target estimator diagnostics and a separate "
                "cached-target climatology lane"
            ),
            "claim_boundary": result.get("claim_boundary"),
        },
        "implementation": dict(_mapping(result, "implementation")),
        "results": compact_horizons,
        "decision": dict(_mapping(result, "decision")),
        "resource_use": dict(_mapping(result, "resource_use")),
    }
    summary["suitability_audit_summary_digest"] = canonical_digest(summary)
    return summary


def _validate_in_memory_result(
    result: Mapping[str, object],
    plan: Mapping[str, object],
) -> None:
    payload = dict(result)
    digest = payload.pop("suitability_audit_result_digest", None)
    if (
        payload.get("schema_version") != RESULT_SCHEMA
        or digest != canonical_digest(payload)
        or payload.get("suitability_audit_plan_digest")
        != plan.get("suitability_audit_plan_digest")
    ):
        raise ValueError("in-memory suitability result is invalid")


def _load_bound_result(
    path: Path,
    plan: Mapping[str, object],
    *,
    sha_field: str,
    digest_field: str,
    schema: str,
) -> Mapping[str, Any]:
    source = _mapping(plan, "source")
    _require_sha256(path, _required_string(source, sha_field))
    payload = dict(_load_mapping(path))
    digest = payload.pop(digest_field, None)
    if payload.get("schema_version") != schema or digest != canonical_digest(payload):
        raise ValueError(f"bound result is invalid: {path}")
    if digest != source.get(digest_field):
        raise ValueError(f"bound result digest changed: {path}")
    payload[digest_field] = digest
    return payload


def _load_inputs(
    *,
    plan: Mapping[str, object],
    task_universe_path: Path,
    task_times_path: Path,
    panel_summary_path: Path,
    resolved_outcomes_path: Path,
    outcome_results_path: Path,
    hindsight_results_path: Path,
) -> tuple[
    tuple[TaskMetadata, ...],
    Mapping[str, Mapping[str, int]],
    tuple[Mapping[str, str], ...],
    Mapping[str, Any],
    Mapping[str, Any],
    Mapping[str, Any],
]:
    source = _mapping(plan, "source")
    _require_sha256(
        resolved_outcomes_path,
        _required_string(source, "resolved_outcomes_file_sha256"),
    )
    tasks = load_task_metadata(task_universe_path, task_times_path, plan)
    outcomes, configuration_metadata, diagnostics = load_public_outcomes(
        panel_summary_path,
        resolved_outcomes_path,
        tuple(task.instance_id for task in tasks),
        plan,
    )
    outcome_results = _load_bound_result(
        outcome_results_path,
        plan,
        sha_field="outcome_results_file_sha256",
        digest_field="outcome_results_digest",
        schema="barcarolle_multi_swe_semantic_outcome_results_v1",
    )
    hindsight_results = _load_bound_result(
        hindsight_results_path,
        plan,
        sha_field="hindsight_results_file_sha256",
        digest_field="hindsight_results_digest",
        schema="barcarolle_multi_swe_hindsight_results_v1",
    )
    return (
        tasks,
        outcomes,
        configuration_metadata,
        diagnostics,
        outcome_results,
        hindsight_results,
    )


def _write_payload(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _require_sha256(path: Path, expected: str) -> None:
    if _file_sha256(path) != expected:
        raise ValueError(f"file SHA-256 changed: {path}")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _load_jsonl(path: Path) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        payload = json.loads(line)
        if not isinstance(payload, Mapping):
            raise ValueError(f"expected JSON object at {path}:{line_number}")
        rows.append(payload)
    return tuple(rows)


def _mapping(payload: Mapping[str, object], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be a JSON object")
    return value


def _mapping_sequence(
    payload: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, Any], ...]:
    value = payload.get(key)
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or any(not isinstance(row, Mapping) for row in value)
    ):
        raise ValueError(f"{key} must contain JSON objects")
    return tuple(value)  # type: ignore[return-value]


def _required_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a nonempty string")
    return value


def _positive_integer(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{key} must be a positive integer")
    return value


def _positive_or_zero_integer(
    payload: Mapping[str, object],
    key: str,
) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{key} must be a nonnegative integer")
    return value


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _number_sequence(value: object, label: str) -> tuple[float, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
    ):
        raise ValueError(f"{label} must be a sequence")
    return tuple(_finite_number(item, label) for item in value)


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{label} must contain nonempty strings")
    result = tuple(value)
    if len(result) != len(set(result)):
        raise ValueError(f"{label} contains duplicates")
    return result  # type: ignore[return-value]


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires values")
    return fsum(values) / len(values)


def _weighted_mean(values: Sequence[tuple[float, int]]) -> float:
    total_weight = sum(weight for _, weight in values)
    if total_weight <= 0:
        raise ValueError("weighted mean requires positive weight")
    return fsum(value * weight for value, weight in values) / total_weight


def _quantile(values: Sequence[float], probability: float) -> float:
    if not values or probability < 0.0 or probability > 1.0:
        raise ValueError("quantile input is invalid")
    ordered = tuple(sorted(values))
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    run_parser.add_argument(
        "--task-universe",
        type=Path,
        default=DEFAULT_TASK_UNIVERSE,
    )
    run_parser.add_argument(
        "--task-times",
        type=Path,
        default=DEFAULT_TASK_TIMES,
    )
    run_parser.add_argument(
        "--panel-summary",
        type=Path,
        default=DEFAULT_PANEL_SUMMARY,
    )
    run_parser.add_argument(
        "--resolved-outcomes",
        type=Path,
        default=DEFAULT_RESOLVED_OUTCOMES,
    )
    run_parser.add_argument(
        "--outcome-results",
        type=Path,
        default=DEFAULT_OUTCOME_RESULTS,
    )
    run_parser.add_argument(
        "--hindsight-results",
        type=Path,
        default=DEFAULT_HINDSIGHT_RESULTS,
    )
    run_parser.add_argument("--output", type=Path, required=True)

    summary_parser = subparsers.add_parser("build-summary")
    summary_parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    summary_parser.add_argument("--results", type=Path, required=True)
    summary_parser.add_argument(
        "--reproduction-results",
        type=Path,
        required=True,
    )
    summary_parser.add_argument("--output", type=Path, required=True)

    verify_parser = subparsers.add_parser("verify-summary")
    verify_parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    verify_parser.add_argument("--results", type=Path, required=True)
    verify_parser.add_argument(
        "--reproduction-results",
        type=Path,
        required=True,
    )
    verify_parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    arguments = _parse_arguments()
    plan = load_suitability_audit_plan(arguments.plan)
    if arguments.command == "run":
        inputs = _load_inputs(
            plan=plan,
            task_universe_path=arguments.task_universe,
            task_times_path=arguments.task_times,
            panel_summary_path=arguments.panel_summary,
            resolved_outcomes_path=arguments.resolved_outcomes,
            outcome_results_path=arguments.outcome_results,
            hindsight_results_path=arguments.hindsight_results,
        )
        result = run_suitability_audit(*inputs, plan)
        _write_payload(arguments.output, result)
        return

    result = load_suitability_result(arguments.results, plan)
    reproduction = load_suitability_result(
        arguments.reproduction_results,
        plan,
    )
    expected = build_suitability_summary(result, reproduction, plan)
    if arguments.command == "build-summary":
        _write_payload(arguments.output, expected)
        return
    observed = load_suitability_summary(arguments.summary, plan)
    if canonical_json(observed) != canonical_json(expected):
        raise ValueError("committed suitability summary changed")


if __name__ == "__main__":
    main()
