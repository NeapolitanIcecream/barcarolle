#!/usr/bin/env python3
"""Run the frozen SWE-bench Verified candidate-free suitability audit."""

from __future__ import annotations

# The explicit reproduction command supplies NumPy, SciPy, and PyArrow.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
import hashlib
import json
from math import fsum, isfinite
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.multi_repository_study.panel_extension import (  # noqa: E402
    load_agent_panel_extension_plan,
    load_agent_panel_schema_amendment,
    load_allocated_outcomes,
)
from examples.multi_repository_study.public_replay import (  # noqa: E402
    RepositoryOrigin,
    TaskMetadata,
    build_repository_origins,
    future_pass_rate_mae,
    load_dataset_tasks,
    load_portfolio,
    load_public_outcomes,
    load_public_panel_plan,
    random_calibration,
)
from examples.multi_swe_research.hindsight_diagnostic import (  # noqa: E402
    solve_exact_hindsight_subset,
)
from examples.multi_swe_research.suitability_audit import (  # noqa: E402
    _bootstrap_interval,
    _distribution_summary,
    _observed_repository_row,
    _temporal_null,
)


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "suitability-audit-plan.json"
DEFAULT_DATASET = (
    REPOSITORY_ROOT
    / "outputs"
    / "user-journeys"
    / "2026-07-17-swe-bench-verified-pylint-pilot"
    / "source"
    / "swe-bench-verified-test-91aa3ed.parquet"
)
DEFAULT_RESULT_DIRECTORY = (
    REPOSITORY_ROOT
    / "outputs"
    / "research"
    / "2026-07-28-public-multi-repository"
    / "official-results"
)
DEFAULT_PUBLIC_PLAN = HERE / "public-panel-plan.json"
DEFAULT_PORTFOLIO = HERE / "portfolio.json"
DEFAULT_EXTENSION_PLAN = HERE / "agent-panel-extension-plan.json"
DEFAULT_SCHEMA_AMENDMENT = HERE / "agent-panel-schema-amendment.json"
DEFAULT_MULTI_SWE_SUMMARY = (
    REPOSITORY_ROOT
    / "examples"
    / "multi_swe_research"
    / "evidence"
    / "suitability-audit-summary.json"
)

PLAN_SCHEMA = "barcarolle_verified_suitability_audit_plan_v1"
RESULT_SCHEMA = "barcarolle_verified_suitability_audit_result_v1"
SUMMARY_SCHEMA = "barcarolle_verified_suitability_audit_summary_v1"


def load_verified_suitability_plan(
    path: Path = DEFAULT_PLAN,
) -> Mapping[str, Any]:
    """Load the self-digested frozen plan and enforce its authority."""
    payload = dict(_load_mapping(path))
    digest = payload.pop("suitability_audit_plan_digest", None)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("Verified suitability plan schema is unsupported")
    if digest != canonical_digest(payload):
        raise ValueError("Verified suitability plan digest does not match")
    payload["suitability_audit_plan_digest"] = digest

    authority = _mapping(payload, "authority")
    if authority != {
        "paid_api_calls": 0,
        "sealed_swe_bench_holdout_agents_opened": 0,
        "new_public_outcome_panels_opened": 0,
        "generator_development": False,
        "implementation_scope": (
            "one direct SWE-bench Verified experiment module reusing "
            "existing loaders and statistical helpers, focused tests, "
            "ignored raw results, a compact self-digested summary, and "
            "claim-boundary documentation"
        ),
    }:
        raise ValueError("Verified suitability authority changed")

    frame = _mapping(payload, "frame")
    random_plan = _mapping(payload, "random_calibration")
    uncertainty = _mapping(payload, "uncertainty")
    null = _mapping(payload, "temporal_null")
    if (
        _positive_integer(frame, "repository_count") != 7
        or _positive_integer(frame, "expected_origin_count") != 68
        or _positive_integer(frame, "minimum_initial_history_tasks") != 15
        or _positive_integer(frame, "future_tasks") != 5
        or _positive_integer(frame, "selection_budget_tasks") != 10
        or _positive_integer(random_plan, "draws") != 20000
        or _positive_integer(
            uncertainty,
            "repository_bootstrap_resamples",
        )
        != 10000
        or _positive_integer(null, "draws") != 2000
        or _finite_number(null.get("alpha"), "temporal-null alpha") != 0.05
    ):
        raise ValueError("Verified suitability diagnostic contract changed")
    return payload


def load_verified_suitability_result(
    path: Path,
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Load a self-digested raw result bound to the frozen plan."""
    payload = dict(_load_mapping(path))
    digest = payload.pop("suitability_audit_result_digest", None)
    if (
        payload.get("schema_version") != RESULT_SCHEMA
        or digest != canonical_digest(payload)
        or payload.get("suitability_audit_plan_digest")
        != plan.get("suitability_audit_plan_digest")
    ):
        raise ValueError("Verified suitability result is invalid")
    payload["suitability_audit_result_digest"] = digest
    return payload


def load_verified_suitability_summary(
    path: Path,
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Load the committed compact summary."""
    payload = dict(_load_mapping(path))
    digest = payload.pop("suitability_audit_summary_digest", None)
    identities = _mapping(payload, "identities")
    if (
        payload.get("schema_version") != SUMMARY_SCHEMA
        or digest != canonical_digest(payload)
        or identities.get("suitability_audit_plan_digest")
        != plan.get("suitability_audit_plan_digest")
    ):
        raise ValueError("Verified suitability summary is invalid")
    payload["suitability_audit_summary_digest"] = digest
    return payload


def load_verified_inputs(
    *,
    plan: Mapping[str, object],
    dataset_path: Path = DEFAULT_DATASET,
    result_directory: Path = DEFAULT_RESULT_DIRECTORY,
) -> tuple[
    tuple[TaskMetadata, ...],
    Mapping[str, Mapping[str, int]],
    Mapping[str, Mapping[str, int]],
    Mapping[str, Mapping[str, str]],
    Mapping[str, Any],
]:
    """Load only the eleven already-opened Agent outcomes."""
    _require_sha256(
        dataset_path,
        _required_string(_mapping(plan, "source"), "dataset_sha256"),
    )
    bound = _mapping(plan, "bound_manifests")
    _require_bound_manifest(
        DEFAULT_PUBLIC_PLAN,
        _mapping(bound, "public_panel_plan"),
    )
    _require_bound_manifest(
        DEFAULT_PORTFOLIO,
        _mapping(bound, "portfolio"),
    )
    _require_bound_manifest(
        DEFAULT_EXTENSION_PLAN,
        _mapping(bound, "agent_panel_extension_plan"),
    )
    _require_bound_manifest(
        DEFAULT_SCHEMA_AMENDMENT,
        _mapping(bound, "agent_panel_schema_amendment"),
    )

    public_plan = load_public_panel_plan(DEFAULT_PUBLIC_PLAN)
    portfolio = load_portfolio(DEFAULT_PORTFOLIO)
    extension = load_agent_panel_extension_plan(DEFAULT_EXTENSION_PLAN)
    amendment = load_agent_panel_schema_amendment(DEFAULT_SCHEMA_AMENDMENT)
    _require_logical_digest(
        public_plan,
        "public_panel_plan_digest",
        _mapping(bound, "public_panel_plan"),
    )
    _require_logical_digest(
        portfolio,
        "portfolio_digest",
        _mapping(bound, "portfolio"),
    )
    _require_logical_digest(
        extension,
        "agent_panel_extension_plan_digest",
        _mapping(bound, "agent_panel_extension_plan"),
    )
    _require_logical_digest(
        amendment,
        "agent_panel_schema_amendment_digest",
        _mapping(bound, "agent_panel_schema_amendment"),
    )
    _require_multi_swe_summary_identity(
        DEFAULT_MULTI_SWE_SUMMARY,
        _mapping(bound, "multi_swe_pilot_summary"),
    )

    tasks = load_dataset_tasks(dataset_path)
    source = _mapping(plan, "source")
    if len(tasks) != _positive_integer(source, "task_count"):
        raise ValueError("Verified Task denominator changed")
    task_ids = tuple(task.instance_id for task in tasks)
    original_outcomes, original_diagnostics = load_public_outcomes(
        result_directory,
        public_plan,
        task_ids,
    )
    development_outcomes, development_diagnostics = load_allocated_outcomes(
        result_directory,
        extension,
        task_ids,
        allocation_key="development_allocation",
        schema_amendment=amendment,
    )
    if set(original_outcomes) & set(development_outcomes):
        raise ValueError("opened Agent allocations overlap")
    outcomes = {
        **original_outcomes,
        **development_outcomes,
    }
    panel = _mapping(plan, "agent_panel")
    if len(outcomes) != _positive_integer(panel, "opened_agent_count"):
        raise ValueError("opened Agent count changed")

    metadata: dict[str, Mapping[str, str]] = {}
    for row in _mapping_sequence(public_plan, "agent_panel"):
        agent_id = _required_string(row, "agent_id")
        metadata[agent_id] = {
            "agent_id": agent_id,
            "allocation": "existing_opened_development_panel",
            "mechanism_family": "preexisting_public_panel",
            "model_label": "not_frozen_for_this_diagnostic",
        }
    for row in _mapping_sequence(extension, "development_allocation"):
        agent_id = _required_string(row, "agent_id")
        metadata[agent_id] = {
            "agent_id": agent_id,
            "allocation": "development_allocation",
            "mechanism_family": _required_string(
                row,
                "mechanism_family",
            ),
            "model_label": _required_string(row, "model_label"),
        }
    if set(metadata) != set(outcomes):
        raise ValueError("opened Agent metadata changed")

    diagnostics = {
        **original_diagnostics,
        **development_diagnostics,
    }
    input_identities = {
        "dataset_sha256": _file_sha256(dataset_path),
        "public_panel_plan_digest": public_plan.get(
            "public_panel_plan_digest"
        ),
        "portfolio_digest": portfolio.get("portfolio_digest"),
        "agent_panel_extension_plan_digest": extension.get(
            "agent_panel_extension_plan_digest"
        ),
        "agent_panel_schema_amendment_digest": amendment.get(
            "agent_panel_schema_amendment_digest"
        ),
        "opened_agent_ids": tuple(sorted(outcomes)),
        "opened_outcome_matrix_digest": canonical_digest(
            {
                agent_id: outcomes[agent_id]
                for agent_id in sorted(outcomes)
            }
        ),
    }
    return (
        tasks,
        dict(sorted(outcomes.items())),
        dict(sorted(diagnostics.items())),
        dict(sorted(metadata.items())),
        input_identities,
    )


def run_verified_suitability_audit(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    outcome_diagnostics: Mapping[str, Mapping[str, int]],
    agent_metadata: Mapping[str, Mapping[str, str]],
    input_identities: Mapping[str, Any],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Execute the frozen H5 candidate-free source-transfer audit."""
    import numpy as np
    import pyarrow
    import scipy

    reproduction = _mapping(plan, "reproduction")
    if (
        np.__version__ != _required_string(reproduction, "numpy_version")
        or scipy.__version__
        != _required_string(reproduction, "scipy_version")
        or pyarrow.__version__
        != _required_string(reproduction, "pyarrow_version")
        or sys.version.split()[0]
        != _required_string(reproduction, "python_version")
    ):
        raise ValueError("Verified suitability runtime changed")

    agent_ids = tuple(sorted(outcomes_by_agent))
    if set(agent_ids) != set(agent_metadata):
        raise ValueError("Verified Agent panel metadata differs")
    frame = _mapping(plan, "frame")
    repository_ids = _string_tuple(
        frame.get("repository_ids"),
        "repository IDs",
    )
    origins_by_repository = build_repository_origins(
        tasks,
        minimum_initial_history_tasks=_positive_integer(
            frame,
            "minimum_initial_history_tasks",
        ),
        future_block_tasks=_positive_integer(frame, "future_tasks"),
    )
    origins_by_repository = {
        repository_id: origins_by_repository[repository_id]
        for repository_id in repository_ids
    }
    origin_count = sum(map(len, origins_by_repository.values()))
    if (
        len(origins_by_repository)
        != _positive_integer(frame, "repository_count")
        or origin_count != _positive_integer(frame, "expected_origin_count")
    ):
        raise ValueError("Verified Origin frame changed")

    observed, panel_arrays = _evaluate_observed(
        np=np,
        repository_ids=repository_ids,
        origins_by_repository=origins_by_repository,
        outcomes_by_agent=outcomes_by_agent,
        agent_ids=agent_ids,
        horizon=_positive_integer(frame, "future_tasks"),
    )
    controls = _aggregate_controls(observed)
    full_history = controls["full_history_mae"]
    zero = controls["always_zero_mae"]

    random_plan = _mapping(plan, "random_calibration")
    random_result = random_calibration(
        repository_ids,
        origins_by_repository,
        outcomes_by_agent,
        budget=_positive_integer(frame, "selection_budget_tasks"),
        draws=_positive_integer(random_plan, "draws"),
        seed=_positive_integer(random_plan, "seed"),
        observed_summaries={},
    )
    random_mean_difference = _finite_number(
        random_result.get("mean_macro_repository_difference"),
        "random mean difference",
    )
    random_quantiles = _mapping(random_result, "quantiles")

    oracle_rows = _exact_oracle_rows(
        repository_ids=repository_ids,
        origins_by_repository=origins_by_repository,
        outcomes_by_agent=outcomes_by_agent,
        agent_ids=agent_ids,
        budget=_positive_integer(frame, "selection_budget_tasks"),
    )
    oracle_mae = _mean(
        tuple(
            _finite_number(row.get("oracle_mae"), "repository oracle MAE")
            for row in oracle_rows
        )
    )
    observed_by_repository = {
        _required_string(row, "repository_id"): row for row in observed
    }
    for row in oracle_rows:
        repository_id = _required_string(row, "repository_id")
        observed_row = observed_by_repository[repository_id]
        observed_row["oracle_mae"] = row["oracle_mae"]
        observed_row["selection_headroom"] = (
            _finite_number(
                observed_row.get("full_history_mae"),
                "repository full-history MAE",
            )
            - _finite_number(row.get("oracle_mae"), "repository oracle MAE")
        )

    differences = tuple(
        _finite_number(row.get("full_minus_zero"), "full-minus-zero")
        for row in observed
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
        ),
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
    every_loo_negative = all(
        _finite_number(
            row.get("macro_repository_full_minus_zero"),
            "leave-one-repository-out difference",
        )
        < 0.0
        for row in leave_one_out
    )
    null_plan = _mapping(plan, "temporal_null")
    temporal_null = _temporal_null(
        np=np,
        panel_arrays=panel_arrays,
        horizon=_positive_integer(frame, "future_tasks"),
        draws=_positive_integer(null_plan, "draws"),
        seed=_positive_integer(null_plan, "seed"),
    )
    observed_difference = full_history - zero
    if abs(observed_difference - temporal_null["observed"]) > 1e-12:
        raise ValueError("observed and temporal-null statistics differ")

    capacity_present = oracle_mae < full_history
    persistence_detected = (
        capacity_present
        and observed_difference < 0.0
        and _finite_number(bootstrap.get("upper"), "bootstrap upper") < 0.0
        and every_loo_negative
        and _finite_number(
            temporal_null.get("one_sided_probability"),
            "temporal-null probability",
        )
        <= _finite_number(null_plan.get("alpha"), "temporal-null alpha")
    )
    if zero <= full_history:
        terminal_state = "unseen_estimator_full_dominated"
    elif persistence_detected:
        terminal_state = "history_persistence_detected_on_counterfactual_panel"
    elif capacity_present:
        terminal_state = "capacity_without_detected_history_persistence"
    else:
        terminal_state = "resolution_or_contract_limited"

    pooled = _pooled_controls(observed)
    future_cells = sum(
        _positive_integer(row, "future_cell_count") for row in observed
    )
    positive_cells = sum(
        _nonnegative_integer(row, "positive_future_cell_count")
        for row in observed
    )
    agent_origin_count = sum(
        _positive_integer(row, "agent_origin_count") for row in observed
    )
    all_zero_blocks = sum(
        _nonnegative_integer(row, "all_zero_agent_origin_count")
        for row in observed
    )
    all_one_blocks = sum(
        _nonnegative_integer(row, "all_one_agent_origin_count")
        for row in observed
    )
    agent_rows = _agent_rows(observed, agent_ids, agent_metadata)
    calendar_values = tuple(
        value
        for row in observed
        for value in _number_tuple(
            row.get("cutoff_to_future_end_days"),
            "cutoff-to-future-end days",
        )
    )

    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "epistemic_status": plan.get("epistemic_status"),
        "suitability_audit_plan_digest": plan.get(
            "suitability_audit_plan_digest"
        ),
        "identities": dict(input_identities),
        "frame": {
            "task_count": len(tasks),
            "agent_count": len(agent_ids),
            "repository_ids": repository_ids,
            "repository_count": len(repository_ids),
            "origin_count": origin_count,
            "future_tasks": _positive_integer(frame, "future_tasks"),
            "selection_budget_tasks": _positive_integer(
                frame,
                "selection_budget_tasks",
            ),
            "origin_alignment": "end_aligned_complete_nonoverlapping",
            "primary_aggregation": "equal_repository",
            "task_time_status": "projected_issue_created_at",
            "result_availability_status": "not_historically_attested",
        },
        "prevalence": {
            "equal_repository_future_density": zero,
            "pooled_future_density": positive_cells / future_cells,
            "all_zero_agent_origin_count": all_zero_blocks,
            "all_zero_agent_origin_share": (
                all_zero_blocks / agent_origin_count
            ),
            "all_one_agent_origin_count": all_one_blocks,
            "all_one_agent_origin_share": (
                all_one_blocks / agent_origin_count
            ),
        },
        "controls": {
            "equal_repository": {
                **controls,
                "random_mean_mae": full_history + random_mean_difference,
                "random_mean_minus_full": random_mean_difference,
                "random_mae_quantiles": {
                    key: full_history
                    + _finite_number(
                        random_quantiles.get(key),
                        f"random quantile {key}",
                    )
                    for key in ("0.025", "0.5", "0.975")
                },
                "oracle_mae": oracle_mae,
                "selection_headroom": full_history - oracle_mae,
                "trivial_separation_full": zero - full_history,
                "trivial_relative_headroom": zero - oracle_mae,
            },
            "pooled_origin": pooled,
            "random_calibration": random_result,
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
            "observed": observed_difference,
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
            "agent_rows": agent_rows,
        },
        "temporal_null": temporal_null,
        "calendar": {
            "cutoff_to_future_end_days": _distribution_summary(
                calendar_values
            ),
            "interpretation": (
                "Task-count H5 is a research frame, not one deployment "
                "TimeRange."
            ),
        },
        "repository_rows": tuple(observed),
        "oracle_rows": oracle_rows,
        "outcome_diagnostics": outcome_diagnostics,
        "decision": {
            "terminal_state": terminal_state,
            "panel_status": (
                "exploratory_counterfactual_development_boundary"
                if persistence_detected
                else "descriptive_only"
            ),
            "budget_ten_capacity_present": capacity_present,
            "history_persistence_detected": persistence_detected,
            "selector_nominated": False,
            "production_claim_allowed": False,
            "workload_relevance_resolved": False,
            "next_route": (
                "stage_c_theory_driven_algorithm_research"
                if persistence_detected
                else "stop_atlas_and_normalize_or_acquire"
            ),
        },
        "implementation": {
            "implementation_file_sha256": _file_sha256(
                Path(__file__).resolve()
            ),
            "python_version": sys.version.split()[0],
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
            "pyarrow_version": pyarrow.__version__,
        },
        "resource_use": {
            "paid_api_calls": 0,
            "sealed_swe_bench_holdout_agents_opened": 0,
            "new_public_outcome_panels_opened": 0,
            "generator_development": False,
        },
        "claim_boundary": _required_string(
            _mapping(plan, "research_contract"),
            "claim_boundary",
        ),
    }
    result["suitability_audit_result_digest"] = canonical_digest(result)
    return result


def build_verified_suitability_summary(
    result: Mapping[str, object],
    reproduction: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Build the compact committed evidence summary."""
    _validate_in_memory_result(result, plan)
    _validate_in_memory_result(reproduction, plan)
    byte_identical = canonical_json(result) == canonical_json(reproduction)
    if not byte_identical:
        raise ValueError("Verified suitability reproduction differs")

    frame = _mapping(result, "frame")
    prevalence = _mapping(result, "prevalence")
    controls = _mapping(_mapping(result, "controls"), "equal_repository")
    uncertainty = _mapping(result, "uncertainty")
    interval = _mapping(uncertainty, "repository_bootstrap_interval_95")
    null = _mapping(result, "temporal_null")
    calendar = _mapping(result, "calendar")
    decision = _mapping(result, "decision")
    agent_rows = _mapping_sequence(uncertainty, "agent_rows")
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
            "task_count": frame.get("task_count"),
            "agent_count": frame.get("agent_count"),
            "repository_count": frame.get("repository_count"),
            "origin_count": frame.get("origin_count"),
            "future_tasks": frame.get("future_tasks"),
            "selection_budget_tasks": frame.get("selection_budget_tasks"),
            "primary_metric": "future pass-rate MAE",
            "primary_aggregation": "equal repository",
            "claim_boundary": result.get("claim_boundary"),
        },
        "results": {
            "equal_repository_future_density": prevalence.get(
                "equal_repository_future_density"
            ),
            "pooled_future_density": prevalence.get(
                "pooled_future_density"
            ),
            "all_zero_agent_origin_share": prevalence.get(
                "all_zero_agent_origin_share"
            ),
            "all_one_agent_origin_share": prevalence.get(
                "all_one_agent_origin_share"
            ),
            "always_zero_mae": controls.get("always_zero_mae"),
            "always_one_mae": controls.get("always_one_mae"),
            "full_history_mae": controls.get("full_history_mae"),
            "cached_expanding_median_mae": controls.get(
                "cached_expanding_median_mae"
            ),
            "random_mean_mae": controls.get("random_mean_mae"),
            "oracle_mae": controls.get("oracle_mae"),
            "selection_headroom": controls.get("selection_headroom"),
            "trivial_separation_full": controls.get(
                "trivial_separation_full"
            ),
            "trivial_relative_headroom": controls.get(
                "trivial_relative_headroom"
            ),
            "full_minus_zero": uncertainty.get("observed"),
            "repository_bootstrap_interval_95": dict(interval),
            "leave_one_repository_out_all_negative": uncertainty.get(
                "every_leave_one_repository_out_negative"
            ),
            "agent_directions_favorable": (
                f"{sum(_finite_number(row.get('full_minus_zero'), 'Agent difference') < 0.0 for row in agent_rows)}/{len(agent_rows)}"
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
        },
        "decision": dict(decision),
        "implementation": dict(_mapping(result, "implementation")),
        "resource_use": dict(_mapping(result, "resource_use")),
    }
    summary["suitability_audit_summary_digest"] = canonical_digest(summary)
    return summary


def _evaluate_observed(
    *,
    np: Any,
    repository_ids: Sequence[str],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    agent_ids: Sequence[str],
    horizon: int,
) -> tuple[
    tuple[dict[str, Any], ...],
    Mapping[str, Mapping[str, Any]],
]:
    rows = []
    panel_arrays = {}
    for repository_id in repository_ids:
        origins = tuple(origins_by_repository[repository_id])
        ordered_tasks = (*origins[-1].history, *origins[-1].future)
        response = np.asarray(
            [
                [
                    outcomes_by_agent[agent_id][task.instance_id]
                    for agent_id in agent_ids
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
            raise ValueError("Verified Origin membership changed")
        rows.append(
            _observed_repository_row(
                np,
                repository_id,
                origins,
                response,
                starts,
                horizon,
                agent_ids,
            )
        )
        panel_arrays[repository_id] = {
            "response": response,
            "starts": starts,
        }
    return tuple(rows), panel_arrays


def _aggregate_controls(
    repository_rows: Sequence[Mapping[str, Any]],
) -> Mapping[str, float]:
    names = (
        "always_zero_mae",
        "always_one_mae",
        "full_history_mae",
        "cached_expanding_median_mae",
    )
    return {
        name: _mean(
            tuple(
                _finite_number(row.get(name), f"repository {name}")
                for row in repository_rows
            )
        )
        for name in names
    }


def _pooled_controls(
    repository_rows: Sequence[Mapping[str, Any]],
) -> Mapping[str, float]:
    names = (
        "always_zero_mae",
        "always_one_mae",
        "full_history_mae",
        "cached_expanding_median_mae",
    )
    result = {}
    total_origins = sum(
        _positive_integer(row, "origin_count") for row in repository_rows
    )
    for name in names:
        result[name] = (
            fsum(
                _finite_number(row.get(name), f"repository {name}")
                * _positive_integer(row, "origin_count")
                for row in repository_rows
            )
            / total_origins
        )
    return result


def _exact_oracle_rows(
    *,
    repository_ids: Sequence[str],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    agent_ids: Sequence[str],
    budget: int,
) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for repository_id in repository_ids:
        losses = []
        pattern_counts = []
        max_objective_error = 0.0
        for origin in origins_by_repository[repository_id]:
            selected, diagnostics = solve_exact_hindsight_subset(
                tuple(task.instance_id for task in origin.history),
                tuple(task.instance_id for task in origin.future),
                outcomes_by_agent,
                agent_ids,
                budget=budget,
            )
            losses.append(
                future_pass_rate_mae(
                    selected,
                    tuple(task.instance_id for task in origin.future),
                    outcomes_by_agent,
                )
            )
            pattern_counts.append(
                _positive_integer(diagnostics, "response_pattern_count")
            )
            max_objective_error = max(
                max_objective_error,
                _finite_number(
                    diagnostics.get("objective_error"),
                    "oracle objective error",
                ),
            )
        rows.append(
            {
                "repository_id": repository_id,
                "origin_count": len(losses),
                "oracle_mae": _mean(tuple(losses)),
                "minimum_response_pattern_count": min(pattern_counts),
                "maximum_response_pattern_count": max(pattern_counts),
                "maximum_objective_error": max_objective_error,
                "all_solver_runs_certified": True,
            }
        )
    return tuple(rows)


def _agent_rows(
    repository_rows: Sequence[Mapping[str, Any]],
    agent_ids: Sequence[str],
    metadata: Mapping[str, Mapping[str, str]],
) -> tuple[Mapping[str, Any], ...]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in repository_rows:
        controls = _mapping(row, "configuration_controls")
        for agent_id in agent_ids:
            grouped[agent_id].append(_mapping(controls, agent_id))
    result = []
    for agent_id in agent_ids:
        rows = grouped[agent_id]
        zero = _mean(
            tuple(
                _finite_number(row.get("always_zero_mae"), "Agent zero MAE")
                for row in rows
            )
        )
        full = _mean(
            tuple(
                _finite_number(row.get("full_history_mae"), "Agent full MAE")
                for row in rows
            )
        )
        result.append(
            {
                **dict(metadata[agent_id]),
                "always_zero_mae": zero,
                "full_history_mae": full,
                "full_minus_zero": full - zero,
                "cached_expanding_median_mae": _mean(
                    tuple(
                        _finite_number(
                            row.get("cached_expanding_median_mae"),
                            "Agent cached climatology MAE",
                        )
                        for row in rows
                    )
                ),
            }
        )
    return tuple(result)


def _require_bound_manifest(
    path: Path,
    manifest: Mapping[str, object],
) -> None:
    _require_sha256(path, _required_string(manifest, "file_sha256"))


def _require_logical_digest(
    payload: Mapping[str, object],
    field: str,
    manifest: Mapping[str, object],
) -> None:
    if payload.get(field) != manifest.get("logical_digest"):
        raise ValueError(f"bound manifest logical digest changed: {field}")


def _require_multi_swe_summary_identity(
    path: Path,
    manifest: Mapping[str, object],
) -> None:
    payload = _load_mapping(path)
    digest = payload.get("suitability_audit_summary_digest")
    unsigned = {
        key: value
        for key, value in payload.items()
        if key != "suitability_audit_summary_digest"
    }
    if (
        digest != canonical_digest(unsigned)
        or digest != manifest.get("logical_digest")
    ):
        raise ValueError("bound Multi-SWE summary changed")


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
        raise ValueError("in-memory Verified suitability result is invalid")


def _write_payload(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _require_sha256(path: Path, expected: str) -> None:
    if _file_sha256(path) != expected:
        raise ValueError(f"file SHA-256 changed: {path}")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def _mapping(
    payload: Mapping[str, object],
    key: str,
) -> Mapping[str, Any]:
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
        raise ValueError(f"{key} must be an array of objects")
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


def _nonnegative_integer(
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


def _number_tuple(value: object, label: str) -> tuple[float, ...]:
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


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    run_parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    run_parser.add_argument(
        "--result-directory",
        type=Path,
        default=DEFAULT_RESULT_DIRECTORY,
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
    plan = load_verified_suitability_plan(arguments.plan)
    if arguments.command == "run":
        inputs = load_verified_inputs(
            plan=plan,
            dataset_path=arguments.dataset,
            result_directory=arguments.result_directory,
        )
        result = run_verified_suitability_audit(*inputs, plan)
        _write_payload(arguments.output, result)
        return

    result = load_verified_suitability_result(arguments.results, plan)
    reproduction = load_verified_suitability_result(
        arguments.reproduction_results,
        plan,
    )
    expected = build_verified_suitability_summary(
        result,
        reproduction,
        plan,
    )
    if arguments.command == "build-summary":
        _write_payload(arguments.output, expected)
        return
    observed = load_verified_suitability_summary(arguments.summary, plan)
    if canonical_json(observed) != canonical_json(expected):
        raise ValueError("committed Verified suitability summary changed")


if __name__ == "__main__":
    main()
