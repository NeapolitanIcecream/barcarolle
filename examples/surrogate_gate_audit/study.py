#!/usr/bin/env python3
"""Replay proxy-gated candidates against the actual pass-rate MAE outcome."""

from __future__ import annotations

# NumPy is supplied by the explicit reproduction command.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
from math import fsum
from numbers import Real
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.generator_calibrated_selection.study import (  # noqa: E402
    load_plan as load_thy_002s_plan,
    verify_result as verify_thy_002s_result,
)
from examples.multi_repository_study.public_replay import (  # noqa: E402
    RepositoryOrigin,
    TaskMetadata,
    build_repository_origins,
)
from examples.multi_swe_research.response_composition import (  # noqa: E402
    _build_composition_data,
    _global_prior,
    leave_one_configuration_difficulty,
    load_response_composition_plan,
)
from examples.multi_swe_research.response_signal import (  # noqa: E402
    StudyData,
    _load_bound_study,
    fit_response_contrast_projection,
    load_response_signal_plan,
    ols_next_block_mean,
    transform_response_projection,
)
from examples.multi_swe_research.semantic_selector import (  # noqa: E402
    _random_outcome_calibration,
    load_embedding_manifest,
    load_task_space_results,
)


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "plan.json"
DEFAULT_AMENDMENT = HERE / "plan-amendment-1.json"
DEFAULT_PROVENANCE_AMENDMENT = HERE / "plan-amendment-2.json"
PLAN_SCHEMA = "barcarolle_surrogate_gate_audit_plan_v1"
AMENDMENT_SCHEMA = "barcarolle_surrogate_gate_audit_amendment_v1"
PROVENANCE_AMENDMENT_SCHEMA = (
    "barcarolle_surrogate_gate_audit_provenance_amendment_v1"
)
RESULT_SCHEMA = "barcarolle_surrogate_gate_audit_results_v1"
SUMMARY_SCHEMA = "barcarolle_surrogate_gate_audit_summary_v1"
NUMPY_VERSION = "2.5.1"
ALGORITHM_TERMINAL_STATES = frozenset(
    {
        "primary_mae_rejects",
        "primary_mae_supports_but_complete_gate_is_under_specified",
        "would_pass_frozen_outcome_gate",
    }
)


@dataclass(frozen=True)
class AuditInputs:
    plan: Mapping[str, Any]
    selector_plan: Mapping[str, Any]
    data: StudyData
    configuration_metadata: tuple[Mapping[str, str], ...]
    outcome_maps: Mapping[str, Mapping[str, int]]
    alg_007_task_space: Mapping[str, Any]
    thy_002s_result: Mapping[str, Any]


def load_audit_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    """Load the digest-bound post-decision audit contract."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("surrogate-gate audit plan schema is unsupported")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "plan_digest"}
    )
    if payload.get("plan_digest") != expected:
        raise ValueError("surrogate-gate audit plan digest does not match")
    resources = _mapping(payload, "resource_boundary")
    for key in (
        "paid_api_calls",
        "new_agent_outcome_calls",
        "sealed_holdout_reads",
    ):
        if resources.get(key) != 0:
            raise ValueError("surrogate-gate audit resource boundary changed")
    amendment = load_audit_amendment(DEFAULT_AMENDMENT, plan=payload)
    provenance_amendment = load_audit_provenance_amendment(
        DEFAULT_PROVENANCE_AMENDMENT,
        plan=payload,
        prior_amendment=amendment,
    )
    for item in _mapping_sequence(payload, "bound_files"):
        path_value = REPOSITORY_ROOT / _required_string(item, "path")
        expected_sha = _required_string(item, "sha256")
        if item.get("path") == "examples/surrogate_gate_audit/study.py":
            if amendment.get("parent_implementation_sha256") != expected_sha:
                raise ValueError("audit amendment does not bind parent executor")
            amended_sha = _required_string(
                amendment,
                "amended_implementation_sha256",
            )
            if (
                provenance_amendment.get(
                    "parent_amended_implementation_sha256"
                )
                != amended_sha
            ):
                raise ValueError(
                    "provenance amendment does not bind amended executor"
                )
            expected_sha = _required_string(
                provenance_amendment,
                "amended_implementation_sha256",
            )
        if _sha256_file(path_value) != expected_sha:
            raise ValueError(f"bound file changed: {path_value}")
    result = dict(payload)
    logical_bindings = dict(_mapping(payload, "logical_bindings"))
    corrections = _mapping(
        provenance_amendment,
        "corrected_logical_bindings",
    )
    for key, value in corrections.items():
        if key not in logical_bindings or not isinstance(value, str) or not value:
            raise ValueError("provenance amendment logical correction changed")
        logical_bindings[key] = value
    result["logical_bindings"] = logical_bindings
    result["active_amendment_digests"] = (
        amendment.get("amendment_digest"),
        provenance_amendment.get("amendment_digest"),
    )
    return result


def load_audit_amendment(
    path: Path = DEFAULT_AMENDMENT,
    *,
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    payload = _load_mapping(path)
    if payload.get("schema_version") != AMENDMENT_SCHEMA:
        raise ValueError("surrogate-gate audit amendment schema is unsupported")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "amendment_digest"}
    )
    if payload.get("amendment_digest") != expected:
        raise ValueError("surrogate-gate audit amendment digest does not match")
    if (
        payload.get("parent_plan_digest") != plan.get("plan_digest")
        or payload.get("status") != "pre_selection_input_adapter_correction"
    ):
        raise ValueError("surrogate-gate audit amendment binding changed")
    resources = _mapping(payload, "evidence_access_before_amendment")
    if any(
        resources.get(key) != 0
        for key in (
            "selection_memberships_materialized",
            "paid_api_calls",
            "sealed_holdout_reads",
        )
    ):
        raise ValueError("surrogate-gate audit amendment scope changed")
    return payload


def load_audit_provenance_amendment(
    path: Path = DEFAULT_PROVENANCE_AMENDMENT,
    *,
    plan: Mapping[str, object],
    prior_amendment: Mapping[str, object],
) -> Mapping[str, Any]:
    """Load the post-replay provenance-only correction."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != PROVENANCE_AMENDMENT_SCHEMA:
        raise ValueError(
            "surrogate-gate provenance amendment schema is unsupported"
        )
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "amendment_digest"}
    )
    if payload.get("amendment_digest") != expected:
        raise ValueError(
            "surrogate-gate provenance amendment digest does not match"
        )
    if (
        payload.get("parent_plan_digest") != plan.get("plan_digest")
        or payload.get("prior_amendment_digest")
        != prior_amendment.get("amendment_digest")
        or payload.get("status")
        != "post_replay_provenance_contract_correction"
    ):
        raise ValueError("surrogate-gate provenance amendment binding changed")
    corrections = _mapping(payload, "corrected_logical_bindings")
    if set(corrections) != {
        "response_signal_amendment_digest",
        "alg_007_task_space_result_digest",
    }:
        raise ValueError("surrogate-gate logical correction scope changed")
    resources = _mapping(payload, "evidence_access_before_amendment")
    if (
        resources.get("accepted_replays_completed") != 2
        or resources.get("opened_development_outcomes_read") is not True
        or any(
            resources.get(key) != 0
            for key in (
                "paid_api_calls",
                "new_agent_outcome_calls",
                "sealed_holdout_reads",
            )
        )
    ):
        raise ValueError("surrogate-gate provenance amendment scope changed")
    return payload


def select_mean_matching_indices(
    coordinates: Any,
    target: Any,
    *,
    budget: int,
    swap_pass_limit: int,
    tolerance: float = 1e-15,
) -> tuple[int, ...]:
    """Apply the frozen greedy mean-match plus best improving swaps."""
    import numpy as np

    values = np.asarray(coordinates, dtype=np.float64)
    target_values = np.asarray(target, dtype=np.float64)
    if (
        values.ndim != 2
        or target_values.shape != (values.shape[1],)
        or isinstance(budget, bool)
        or budget <= 0
        or budget > len(values)
        or isinstance(swap_pass_limit, bool)
        or swap_pass_limit < 0
        or tolerance <= 0.0
    ):
        raise ValueError("mean-matching selection inputs are invalid")
    selected: list[int] = []
    selected_sum = np.zeros(values.shape[1], dtype=np.float64)
    all_indices = np.arange(len(values))
    for count in range(1, budget + 1):
        available = np.asarray(
            [index for index in all_indices if int(index) not in selected],
            dtype=np.int64,
        )
        means = (selected_sum[None, :] + values[available]) / count
        objectives = np.square(means - target_values).sum(axis=1)
        chosen = int(available[int(np.argmin(objectives))])
        selected.append(chosen)
        selected_sum += values[chosen]

    def objective(candidate_sum: Any) -> float:
        return float(
            np.square(candidate_sum / budget - target_values).sum()
        )

    current = objective(selected_sum)
    for _ in range(swap_pass_limit):
        selected_set = set(selected)
        available = np.asarray(
            [index for index in all_indices if int(index) not in selected_set],
            dtype=np.int64,
        )
        best: tuple[float, int, int] | None = None
        for selected_position, old_index in enumerate(selected):
            candidate_sums = (
                selected_sum[None, :]
                - values[old_index][None, :]
                + values[available]
            )
            objectives = np.square(
                candidate_sums / budget - target_values
            ).sum(axis=1)
            improving = np.flatnonzero(objectives < current - tolerance)
            if not len(improving):
                continue
            best_relative = int(improving[int(np.argmin(objectives[improving]))])
            minimum = float(objectives[best_relative])
            incoming = int(available[best_relative])
            candidate = (minimum, selected_position, incoming)
            if best is None or candidate < best:
                best = candidate
        if best is None:
            break
        _, selected_position, incoming = best
        outgoing = selected[selected_position]
        selected_sum += values[incoming] - values[outgoing]
        selected[selected_position] = incoming
        current = objective(selected_sum)
    return tuple(sorted(selected))


def select_discrete_composition_indices(
    solved_counts: Sequence[int],
    forecast: float,
    *,
    budget: int,
    maximum_count: int,
    created_order: Sequence[tuple[str, str]],
) -> tuple[int, ...]:
    """Select a lexicographically tied exact discrete response composition."""
    if (
        not solved_counts
        or len(solved_counts) != len(created_order)
        or isinstance(budget, bool)
        or budget <= 0
        or budget > len(solved_counts)
        or isinstance(maximum_count, bool)
        or maximum_count <= 0
        or not 0.0 <= forecast <= 1.0
        or any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            or value > maximum_count
            for value in solved_counts
        )
    ):
        raise ValueError("discrete composition inputs are invalid")
    capacities = tuple(
        sum(value == count for value in solved_counts)
        for count in range(maximum_count + 1)
    )
    suffix = _suffix_reachability(capacities, budget)
    feasible_totals = tuple(
        total
        for total in range(maximum_count * budget + 1)
        if (suffix[0][budget] >> total) & 1
    )
    if not feasible_totals:
        raise ValueError("discrete composition has no feasible total")

    candidates = []
    for total in feasible_totals:
        count_vector = _lexicographic_count_vector(
            capacities,
            suffix,
            budget=budget,
            total=total,
        )
        objective = abs(total / (maximum_count * budget) - forecast)
        candidates.append((objective, count_vector, total))
    _, count_vector, _ = min(candidates)

    selected = []
    for solved_count, wanted in enumerate(count_vector):
        if not wanted:
            continue
        cell = [
            index
            for index, value in enumerate(solved_counts)
            if value == solved_count
        ]
        cell.sort(key=lambda index: created_order[index], reverse=True)
        selected.extend(cell[:wanted])
    if len(selected) != budget:
        raise ValueError("discrete composition did not fill the budget")
    return tuple(sorted(selected))


def _suffix_reachability(
    capacities: Sequence[int],
    budget: int,
) -> tuple[tuple[int, ...], ...]:
    suffix = [[0] * (budget + 1) for _ in range(len(capacities) + 1)]
    suffix[-1][0] = 1
    for count in range(len(capacities) - 1, -1, -1):
        for used in range(budget + 1):
            bits = 0
            for take in range(min(capacities[count], used) + 1):
                bits |= suffix[count + 1][used - take] << (take * count)
            suffix[count][used] = bits
    return tuple(tuple(row) for row in suffix)


def _lexicographic_count_vector(
    capacities: Sequence[int],
    suffix: Sequence[Sequence[int]],
    *,
    budget: int,
    total: int,
) -> tuple[int, ...]:
    remaining_budget = budget
    remaining_total = total
    result = []
    for count, capacity in enumerate(capacities):
        chosen = None
        for take in range(min(capacity, remaining_budget) + 1):
            suffix_budget = remaining_budget - take
            suffix_total = remaining_total - take * count
            if (
                suffix_total >= 0
                and (suffix[count + 1][suffix_budget] >> suffix_total) & 1
            ):
                chosen = take
                break
        if chosen is None:
            raise ValueError("discrete composition reconstruction failed")
        result.append(chosen)
        remaining_budget -= chosen
        remaining_total -= chosen * count
    if remaining_budget or remaining_total:
        raise ValueError("discrete composition reconstruction is incomplete")
    return tuple(result)


def run_audit(
    plan_path: Path = DEFAULT_PLAN,
) -> Mapping[str, Any]:
    """Run all three minimum decisive pass-rate MAE replays."""
    import numpy as np

    if np.__version__ != NUMPY_VERSION:
        raise ValueError(
            f"NumPy version changed: expected {NUMPY_VERSION}, got {np.__version__}"
        )
    inputs = _load_inputs(load_audit_plan(plan_path))
    results = {
        "ALG-013": _run_alg_013(inputs),
        "ALG-014": _run_alg_014(inputs),
        "THY-002S": _run_thy_002s(inputs),
    }
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": inputs.plan.get("study_id"),
        "plan_digest": inputs.plan.get("plan_digest"),
        "active_amendment_digests": inputs.plan.get(
            "active_amendment_digests"
        ),
        "epistemic_status": "post_decision_opened_development_outcome_audit",
        "algorithms": results,
        "resource_use": {
            "paid_api_calls": 0,
            "new_agent_outcome_calls": 0,
            "sealed_holdout_reads": 0,
            "already_open_public_outcome_artifacts_read": 2,
        },
        "claim_boundary": _required_string(inputs.plan, "claim_boundary"),
    }
    result["result_digest"] = canonical_digest(result)
    return result


def _load_inputs(plan: Mapping[str, Any]) -> AuditInputs:
    source = _mapping(plan, "source_paths")
    (
        selector_plan,
        response_signal_plan,
        response_signal_amendment,
        data,
        outcome_diagnostics,
        _,
    ) = _load_bound_study(
        task_content_path=_bound_path(source, "task_content"),
        task_time_path=_bound_path(source, "task_times"),
        embedding_path=_bound_path(source, "embeddings"),
        panel_path=_bound_path(source, "panel_summary"),
        resolved_path=_bound_path(source, "resolved_outcomes"),
        plan_path=_bound_path(source, "response_signal_plan"),
        amendment_path=_bound_path(source, "response_signal_amendment"),
    )
    panel = _load_mapping(_bound_path(source, "panel_summary"))
    configuration_metadata = tuple(
        {
            "configuration_id": _required_string(item, "configuration_id"),
            "model_family": _required_string(item, "model_family"),
            "harness_family": _required_string(item, "harness_family"),
        }
        for item in _mapping_sequence(panel, "configurations")
    )
    if tuple(
        item["configuration_id"] for item in configuration_metadata
    ) != data.configuration_ids:
        raise ValueError("configuration metadata order changed")
    outcome_maps = {
        configuration_id: {
            task_id: int(data.outcomes[task_index, configuration_index])
            for task_index, task_id in enumerate(data.task_ids)
        }
        for configuration_index, configuration_id in enumerate(
            data.configuration_ids
        )
    }
    embedding_manifest = load_embedding_manifest()
    alg_007 = load_task_space_results(
        _bound_path(source, "alg_007_task_space"),
        selector_plan,
        embedding_manifest,
    )
    thy_plan = load_thy_002s_plan(_bound_path(source, "thy_002s_plan"))
    thy_result = _load_mapping(_bound_path(source, "thy_002s_result"))
    verify_thy_002s_result(thy_result, thy_plan)
    if _mapping(thy_result, "decision").get("status") != "retire_mapping":
        raise ValueError("original THY-002S decision changed")
    response_composition_plan = load_response_composition_plan(
        _bound_path(source, "response_composition_plan")
    )
    _validate_logical_bindings(
        plan,
        selector_plan=selector_plan,
        response_signal_plan=response_signal_plan,
        response_signal_amendment=response_signal_amendment,
        response_composition_plan=response_composition_plan,
        outcome_diagnostics=outcome_diagnostics,
        alg_007=alg_007,
        thy_plan=thy_plan,
        thy_result=thy_result,
    )
    return AuditInputs(
        plan=plan,
        selector_plan=selector_plan,
        data=data,
        configuration_metadata=configuration_metadata,
        outcome_maps=outcome_maps,
        alg_007_task_space=alg_007,
        thy_002s_result=thy_result,
    )


def _validate_logical_bindings(
    plan: Mapping[str, object],
    *,
    selector_plan: Mapping[str, object],
    response_signal_plan: Mapping[str, object],
    response_signal_amendment: Mapping[str, object],
    response_composition_plan: Mapping[str, object],
    outcome_diagnostics: Mapping[str, object],
    alg_007: Mapping[str, object],
    thy_plan: Mapping[str, object],
    thy_result: Mapping[str, object],
) -> None:
    contract = _load_mapping(
        REPOSITORY_ROOT / "examples/multi_swe_research/contract.json"
    )
    actual = {
        "selector_plan_digest": selector_plan.get("selector_plan_digest"),
        "import_contract_digest": contract.get("contract_digest"),
        "panel_digest": outcome_diagnostics.get("panel_digest"),
        "resolved_outcome_digest": outcome_diagnostics.get(
            "resolved_outcome_digest"
        ),
        "response_signal_plan_digest": response_signal_plan.get(
            "response_signal_plan_digest"
        ),
        "response_signal_amendment_digest": response_signal_amendment.get(
            "amendment_digest"
        ),
        "response_composition_plan_digest": response_composition_plan.get(
            "response_composition_plan_digest"
        ),
        "thy_002s_plan_digest": thy_plan.get("plan_digest"),
        "thy_002s_result_digest": thy_result.get("result_digest"),
        "thy_002s_memberships_digest": thy_result.get("memberships_digest"),
        "thy_002s_random_membership_digest": _mapping(
            thy_result,
            "random_landscape_raw",
        ).get("membership_digest"),
        "alg_007_task_space_result_digest": alg_007.get(
            "task_space_results_digest"
        ),
    }
    expected = _mapping(plan, "logical_bindings")
    if set(expected) != set(actual):
        raise ValueError("surrogate-gate logical binding set changed")
    mismatches = tuple(
        key for key in sorted(actual) if expected.get(key) != actual[key]
    )
    if mismatches:
        raise ValueError(
            "surrogate-gate logical binding mismatch: "
            + ", ".join(mismatches)
        )


def _run_alg_013(inputs: AuditInputs) -> Mapping[str, Any]:
    original_plan = load_response_signal_plan(
        _bound_path(_mapping(inputs.plan, "source_paths"), "response_signal_plan")
    )
    selector_plan = inputs.selector_plan
    rolling = _mapping(selector_plan, "rolling_origin")
    budget = int(rolling["selection_budget_tasks"])
    tolerance = float(_mapping(original_plan, "diagnostics")["numerical_tolerance"])
    horizon_results = {}
    membership_digests = {}
    for horizon in (5, 10):
        origins, repository_ids, deep_ids = _horizon_frame(
            inputs.data.tasks,
            selector_plan,
            horizon,
        )
        alg_007 = _alg_007_memberships(
            inputs.alg_007_task_space,
            horizon,
            repository_ids,
        )
        rows = []
        membership_rows = []
        for repository_id in repository_ids:
            for origin in origins[repository_id]:
                history_indices = tuple(
                    inputs.data.task_index[task.instance_id]
                    for task in origin.history
                )
                future_indices = tuple(
                    inputs.data.task_index[task.instance_id]
                    for task in origin.future
                )
                cutoff = max(task.created_at for task in origin.history)
                projection = fit_response_contrast_projection(
                    inputs.data,
                    target_repository_id=repository_id,
                    cutoff=cutoff,
                    tolerance=tolerance,
                )
                projected = transform_response_projection(
                    inputs.data.embeddings[list(history_indices)],
                    projection,
                )
                raw_forecast = ols_next_block_mean(
                    inputs.data.embeddings[list(history_indices)],
                    horizon=horizon,
                )
                raw_selected_positions = select_mean_matching_indices(
                    inputs.data.embeddings[list(history_indices)],
                    raw_forecast,
                    budget=budget,
                    swap_pass_limit=20,
                )
                raw_selected = tuple(
                    history_indices[position] for position in raw_selected_positions
                )
                for held_out in range(len(inputs.data.configuration_ids)):
                    keep = tuple(
                        position
                        for position, configuration_index in enumerate(
                            projection.configuration_indices
                        )
                        if configuration_index != held_out
                    )
                    if not keep:
                        raise ValueError("ALG-013 held-out projection is empty")
                    coordinates = projected[:, keep]
                    forecast = ols_next_block_mean(
                        coordinates,
                        horizon=horizon,
                    )
                    selected_positions = select_mean_matching_indices(
                        coordinates,
                        forecast,
                        budget=budget,
                        swap_pass_limit=20,
                    )
                    selected = tuple(
                        history_indices[position] for position in selected_positions
                    )
                    full_target = coordinates.mean(axis=0)
                    full_rcp_positions = select_mean_matching_indices(
                        coordinates,
                        full_target,
                        budget=budget,
                        swap_pass_limit=20,
                    )
                    recent_target = coordinates[-horizon:].mean(axis=0)
                    recent_rcp_positions = select_mean_matching_indices(
                        coordinates,
                        recent_target,
                        budget=budget,
                        swap_pass_limit=20,
                    )
                    alg_007_indices = tuple(
                        inputs.data.task_index[task_id]
                        for task_id in alg_007[origin.origin_id]
                    )
                    row = _loss_row(
                        inputs,
                        repository_id=repository_id,
                        origin=origin,
                        held_out=held_out,
                        candidate=selected,
                        full=history_indices,
                        controls={
                            "rcp_full_centroid": tuple(
                                history_indices[position]
                                for position in full_rcp_positions
                            ),
                            "rcp_recent_centroid": tuple(
                                history_indices[position]
                                for position in recent_rcp_positions
                            ),
                            "raw_embedding_ols": raw_selected,
                            "alg_007": alg_007_indices,
                            "ordinary_recency": history_indices[-budget:],
                        },
                        future=future_indices,
                    )
                    rows.append(row)
                    membership_rows.append(
                        (
                            inputs.data.configuration_ids[held_out],
                            origin.origin_id,
                            tuple(
                                inputs.data.task_ids[index] for index in selected
                            ),
                        )
                    )
        summary = _summarize_rows(
            rows,
            repository_ids,
            deep_ids,
            inputs.configuration_metadata,
            inputs.selector_plan,
        )
        random_report = _random_outcome_calibration(
            origins,
            repository_ids,
            inputs.outcome_maps,
            inputs.data.configuration_ids,
            budget=budget,
            draws=20000,
            seed=20260728,
            candidate_difference=float(summary["wide"]["difference"]),
        )
        summary["random_calibration"] = random_report
        summary["repository_bootstrap_interval_95"] = _repository_bootstrap(
            rows,
            repository_ids,
            resamples=10000,
            seed=20260728,
        )
        horizon_results[str(horizon)] = summary
        membership_digests[str(horizon)] = canonical_digest(
            tuple(sorted(membership_rows))
        )
    decision = _primary_decision(
        horizon_results,
        h5_limit=-0.010,
        h5_repository_minimum=10,
        h10_repository_minimum=8,
    )
    return {
        "original_plan_digest": original_plan.get(
            "response_signal_plan_digest"
        ),
        "original_gate_decision_preserved": (
            "response_representation_signal_rejected"
        ),
        "membership_digests": membership_digests,
        "horizons": horizon_results,
        "primary_mae_decision": decision,
        "terminal_state": _primary_terminal_state(decision),
        "complete_original_stage_c_status": (
            "not_reconstructable_without_post_hoc_defaults"
        ),
        "under_specified_items": (
            "random coupling across held-out configurations",
            "model/harness/language and double-holdout rematerialization",
            "selection temporal-null construction",
        ),
    }


def _run_alg_014(inputs: AuditInputs) -> Mapping[str, Any]:
    import numpy as np

    original_plan = load_response_composition_plan(
        _bound_path(
            _mapping(inputs.plan, "source_paths"),
            "response_composition_plan",
        )
    )
    composition_data = _build_composition_data(
        inputs.data.tasks,
        inputs.outcome_maps,
        inputs.data.configuration_ids,
    )
    difficulty = leave_one_configuration_difficulty(composition_data.outcomes)
    integer_counts = (
        composition_data.outcomes.sum(axis=1, keepdims=True)
        - composition_data.outcomes
    ).astype(np.int64)
    selector_plan = inputs.selector_plan
    budget = int(_mapping(selector_plan, "rolling_origin")["selection_budget_tasks"])
    horizon_results = {}
    membership_digests = {}
    for horizon in (5, 10):
        origins, repository_ids, deep_ids = _horizon_frame(
            inputs.data.tasks,
            selector_plan,
            horizon,
        )
        alg_007 = _alg_007_memberships(
            inputs.alg_007_task_space,
            horizon,
            repository_ids,
        )
        rows = []
        stage_b_rows = []
        membership_rows = []
        static_rows = []
        for repository_id in repository_ids:
            full_loss_sum = np.zeros(
                len(inputs.data.configuration_ids),
                dtype=np.float64,
            )
            recent_loss_sum = np.zeros_like(full_loss_sum)
            earlier_origin_count = 0
            for origin in origins[repository_id]:
                history_indices = tuple(
                    inputs.data.task_index[task.instance_id]
                    for task in origin.history
                )
                future_indices = tuple(
                    inputs.data.task_index[task.instance_id]
                    for task in origin.future
                )
                history_difficulty = difficulty[list(history_indices)]
                future_difficulty = difficulty[list(future_indices)]
                cutoff = max(task.created_at for task in origin.history)
                prior = _global_prior(
                    composition_data,
                    difficulty,
                    target_repository_id=repository_id,
                    cutoff=cutoff,
                )
                (
                    forecast,
                    local,
                    full_difficulty,
                    recent_difficulty,
                ) = _composition_forecast_only(
                    history_difficulty,
                    horizon=horizon,
                    earlier_full_loss_sum=full_loss_sum,
                    earlier_recent_loss_sum=recent_loss_sum,
                    earlier_origin_count=earlier_origin_count,
                    global_prior=prior,
                )
                future_difficulty_mean = future_difficulty.mean(axis=0)
                stage_b_rows.append(
                    {
                        "repository_id": repository_id,
                        "origin_id": origin.origin_id,
                        "difference": float(
                            (
                                np.abs(forecast - future_difficulty_mean)
                                - np.abs(
                                    full_difficulty - future_difficulty_mean
                                )
                            ).mean()
                        ),
                    }
                )
                created_order = tuple(
                    (task.created_at, task.instance_id) for task in origin.history
                )
                for held_out in range(len(inputs.data.configuration_ids)):
                    counts = tuple(
                        int(integer_counts[index, held_out])
                        for index in history_indices
                    )
                    selected_positions = select_discrete_composition_indices(
                        counts,
                        float(forecast[held_out]),
                        budget=budget,
                        maximum_count=len(inputs.data.configuration_ids) - 1,
                        created_order=created_order,
                    )
                    static_positions = select_discrete_composition_indices(
                        counts,
                        float(full_difficulty[held_out]),
                        budget=budget,
                        maximum_count=len(inputs.data.configuration_ids) - 1,
                        created_order=created_order,
                    )
                    selected = tuple(
                        history_indices[position] for position in selected_positions
                    )
                    static_selected = tuple(
                        history_indices[position] for position in static_positions
                    )
                    alg_007_indices = tuple(
                        inputs.data.task_index[task_id]
                        for task_id in alg_007[origin.origin_id]
                    )
                    rows.append(
                        _loss_row(
                            inputs,
                            repository_id=repository_id,
                            origin=origin,
                            held_out=held_out,
                            candidate=selected,
                            full=history_indices,
                            controls={
                                "static_composition": static_selected,
                                "ordinary_recency": history_indices[-budget:],
                                "alg_007": alg_007_indices,
                            },
                            future=future_indices,
                        )
                    )
                    membership_rows.append(
                        (
                            inputs.data.configuration_ids[held_out],
                            origin.origin_id,
                            tuple(
                                inputs.data.task_ids[index] for index in selected
                            ),
                        )
                    )
                    static_rows.append(
                        (
                            inputs.data.configuration_ids[held_out],
                            origin.origin_id,
                            tuple(
                                inputs.data.task_ids[index]
                                for index in static_selected
                            ),
                        )
                    )
                full_loss_sum += np.abs(
                    full_difficulty - future_difficulty_mean
                )
                recent_loss_sum += np.abs(
                    recent_difficulty - future_difficulty_mean
                )
                earlier_origin_count += 1
        summary = _summarize_rows(
            rows,
            repository_ids,
            deep_ids,
            inputs.configuration_metadata,
            inputs.selector_plan,
        )
        summary["stage_b_proxy_difference"] = _repository_first_difference(
            stage_b_rows,
            repository_ids,
        )
        summary["random_calibration"] = _random_outcome_calibration(
            origins,
            repository_ids,
            inputs.outcome_maps,
            inputs.data.configuration_ids,
            budget=budget,
            draws=20000,
            seed=20260728,
            candidate_difference=float(summary["wide"]["difference"]),
        )
        summary["repository_bootstrap_interval_95"] = _repository_bootstrap(
            rows,
            repository_ids,
            resamples=10000,
            seed=20260728,
        )
        horizon_results[str(horizon)] = summary
        membership_digests[str(horizon)] = {
            "candidate": canonical_digest(tuple(sorted(membership_rows))),
            "static_composition": canonical_digest(tuple(sorted(static_rows))),
        }
    decision = _primary_decision(
        horizon_results,
        h5_limit=-0.010,
        h5_repository_minimum=10,
        h10_repository_minimum=8,
    )
    return {
        "original_plan_digest": original_plan.get(
            "response_composition_plan_digest"
        ),
        "original_gate_decision_preserved": "target_future_increment_rejected",
        "membership_digests": membership_digests,
        "horizons": horizon_results,
        "primary_mae_decision": decision,
        "terminal_state": _primary_terminal_state(decision),
        "complete_original_stage_c_status": (
            "not_reconstructable_without_post_hoc_defaults"
        ),
        "under_specified_items": (
            "random coupling across held-out configurations",
            "group-holdout rematerialization",
            "selection temporal-null construction",
        ),
    }


def _composition_forecast_only(
    history: Any,
    *,
    horizon: int,
    earlier_full_loss_sum: Any,
    earlier_recent_loss_sum: Any,
    earlier_origin_count: int,
    global_prior: Any,
) -> tuple[Any, Any, Any, Any]:
    """Materialize ALG-014 without accepting the current future cohort."""
    import numpy as np

    values = np.asarray(history, dtype=np.float64)
    full_loss = np.asarray(earlier_full_loss_sum, dtype=np.float64)
    recent_loss = np.asarray(earlier_recent_loss_sum, dtype=np.float64)
    prior = np.asarray(global_prior, dtype=np.float64)
    if (
        values.ndim != 2
        or values.shape[0] < horizon
        or full_loss.shape != (values.shape[1],)
        or recent_loss.shape != full_loss.shape
        or prior.shape != full_loss.shape
        or earlier_origin_count < 0
    ):
        raise ValueError("composition forecast-only inputs are invalid")
    full = values.mean(axis=0)
    recent = values[-horizon:].mean(axis=0)
    choose_recent = (
        recent_loss < full_loss
        if earlier_origin_count
        else np.zeros(values.shape[1], dtype=bool)
    )
    local = np.where(choose_recent, recent, full)
    local_mass = np.where(
        choose_recent,
        float(horizon),
        float(len(values)),
    )
    forecast = (local_mass * local + prior) / (local_mass + 1.0)
    return forecast, local, full, recent


def _run_thy_002s(inputs: AuditInputs) -> Mapping[str, Any]:
    memberships = tuple(
        _mapping(item, "candidate_diagnostics") and item
        for item in _mapping_sequence(inputs.thy_002s_result, "memberships")
    )
    repository_ids = tuple(
        sorted({_required_string(item, "repository_id") for item in memberships})
    )
    if len(repository_ids) != 11 or len(memberships) != 107:
        raise ValueError("THY-002S audit frame changed")
    rows_by_horizon: dict[int, list[Mapping[str, object]]] = {5: [], 10: []}
    validated_rows = []
    for item in memberships:
        repository_id = _required_string(item, "repository_id")
        origin_id = _required_string(item, "origin_id")
        history_ids = _string_tuple(item.get("history_task_ids"), "history Tasks")
        candidate_ids = _string_tuple(
            item.get("candidate_task_ids"),
            "candidate Tasks",
        )
        stationary_ids = _string_tuple(
            item.get("stationary_task_ids"),
            "stationary Tasks",
        )
        recency_ids = _string_tuple(
            item.get("recency_task_ids"),
            "recency Tasks",
        )
        future_h5 = _string_tuple(item.get("future_h5_task_ids"), "H5 future")
        future_h10 = _string_tuple(item.get("future_h10_task_ids"), "H10 future")
        if (
            len(candidate_ids) != 10
            or len(stationary_ids) != 10
            or len(recency_ids) != 10
            or not set(candidate_ids) <= set(history_ids)
            or not set(stationary_ids) <= set(history_ids)
            or not set(recency_ids) <= set(history_ids)
            or future_h10[:5] != future_h5
            or set(history_ids) & set(future_h10)
        ):
            raise ValueError("THY-002S membership boundary changed")
        index_rows = {
            "candidate": tuple(inputs.data.task_index[item] for item in candidate_ids),
            "stationary": tuple(
                inputs.data.task_index[item] for item in stationary_ids
            ),
            "recency": tuple(inputs.data.task_index[item] for item in recency_ids),
            "full": tuple(inputs.data.task_index[item] for item in history_ids),
        }
        for horizon, future_ids in ((5, future_h5), (10, future_h10)):
            future = tuple(inputs.data.task_index[item] for item in future_ids)
            for held_out in range(len(inputs.data.configuration_ids)):
                rows_by_horizon[horizon].append(
                    _loss_row(
                        inputs,
                        repository_id=repository_id,
                        origin=_synthetic_origin(origin_id, repository_id),
                        held_out=held_out,
                        candidate=index_rows["candidate"],
                        full=index_rows["full"],
                        controls={
                            "stationary_coreset": index_rows["stationary"],
                            "ordinary_recency": index_rows["recency"],
                        },
                        future=future,
                    )
                )
        validated_rows.append(
            (
                repository_id,
                origin_id,
                history_ids,
                candidate_ids,
                stationary_ids,
                recency_ids,
                future_h5,
                future_h10,
            )
        )
    if canonical_digest(tuple(validated_rows)) == canonical_digest(()):
        raise ValueError("THY-002S membership validation is empty")
    horizon_results = {}
    for horizon in (5, 10):
        deep_ids = _deep_repository_ids(inputs.selector_plan, horizon)
        summary = _summarize_rows(
            rows_by_horizon[horizon],
            repository_ids,
            deep_ids,
            inputs.configuration_metadata,
            inputs.selector_plan,
        )
        summary["repository_bootstrap_interval_95"] = _repository_bootstrap(
            rows_by_horizon[horizon],
            repository_ids,
            resamples=20000,
            seed=2026072904,
        )
        horizon_results[str(horizon)] = summary
    random_reports = _thy_random_calibration(
        inputs,
        memberships,
        repository_ids,
        candidate_differences={
            horizon: float(horizon_results[str(horizon)]["wide"]["difference"])
            for horizon in (5, 10)
        },
    )
    for horizon in (5, 10):
        horizon_results[str(horizon)]["random_calibration"] = random_reports[
            str(horizon)
        ]
    gate = _thy_outcome_gate(horizon_results)
    return {
        "original_plan_digest": inputs.thy_002s_result.get("plan_digest"),
        "original_decision_preserved": "retire_mapping",
        "original_outcome_executor_authorized": False,
        "parent_memberships_digest": inputs.thy_002s_result.get(
            "memberships_digest"
        ),
        "horizons": horizon_results,
        "would_pass_frozen_outcome_gate": gate,
        "frozen_outcome_gate_decision": (
            "would_nominate_for_independent_confirmation"
            if gate["all_requirements_met"]
            else "fails_frozen_outcome_gate"
        ),
        "terminal_state": (
            "would_pass_frozen_outcome_gate"
            if gate["all_requirements_met"]
            else "primary_mae_rejects"
        ),
    }


def _synthetic_origin(
    origin_id: str,
    repository_id: str,
) -> RepositoryOrigin:
    return RepositoryOrigin(
        repository_id=repository_id,
        origin_id=origin_id,
        history=(),
        future=(),
    )


def _thy_random_calibration(
    inputs: AuditInputs,
    memberships: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
    *,
    candidate_differences: Mapping[int, float],
) -> Mapping[str, Any]:
    import numpy as np

    draws = 20000
    chunk_size = 500
    generator = np.random.default_rng(2026072902)
    repository_draws = {
        horizon: {
            repository_id: np.zeros(
                (draws, len(inputs.data.configuration_ids)),
                dtype=np.float64,
            )
            for repository_id in repository_ids
        }
        for horizon in (5, 10)
    }
    origin_counts: dict[str, int] = defaultdict(int)
    membership_hash = hashlib.sha256()
    for item in sorted(
        memberships,
        key=lambda value: (
            _required_string(value, "repository_id").casefold(),
            _required_string(value, "origin_id"),
        ),
    ):
        repository_id = _required_string(item, "repository_id")
        origin_id = _required_string(item, "origin_id")
        history_ids = _string_tuple(item.get("history_task_ids"), "history Tasks")
        history_indices = tuple(
            inputs.data.task_index[task_id] for task_id in history_ids
        )
        history = inputs.data.outcomes[list(history_indices)]
        futures = {
            horizon: inputs.data.outcomes[
                [
                    inputs.data.task_index[task_id]
                    for task_id in _string_tuple(
                        item.get(f"future_h{horizon}_task_ids"),
                        f"H{horizon} future",
                    )
                ]
            ].mean(axis=0)
            for horizon in (5, 10)
        }
        full = history.mean(axis=0)
        full_losses = {
            horizon: np.abs(full - future)
            for horizon, future in futures.items()
        }
        origin_counts[repository_id] += 1
        membership_hash.update(repository_id.encode())
        membership_hash.update(b"\0")
        membership_hash.update(origin_id.encode())
        membership_hash.update(b"\0")
        membership_hash.update(canonical_digest(history_ids).encode())
        membership_hash.update(b"\0")
        for offset in range(0, draws, chunk_size):
            chunk = min(chunk_size, draws - offset)
            keys = generator.random((chunk, len(history)))
            selected = np.argpartition(keys, 9, axis=1)[:, :10]
            selected = np.sort(selected, axis=1).astype("<i4", copy=False)
            membership_hash.update(selected.tobytes())
            selected_rates = history[selected].mean(axis=1)
            for horizon, future in futures.items():
                losses = np.abs(selected_rates - future)
                repository_draws[horizon][repository_id][
                    offset : offset + chunk
                ] += losses - full_losses[horizon]
    expected_digest = _mapping(
        inputs.thy_002s_result,
        "random_landscape_raw",
    ).get("membership_digest")
    if membership_hash.hexdigest() != expected_digest:
        raise ValueError("THY-002S random membership digest changed")
    reports = {}
    for horizon in (5, 10):
        for repository_id in repository_ids:
            repository_draws[horizon][repository_id] /= origin_counts[
                repository_id
            ]
        macro = np.mean(
            np.stack(
                [
                    repository_draws[horizon][repository_id].mean(axis=1)
                    for repository_id in repository_ids
                ]
            ),
            axis=0,
        )
        candidate = candidate_differences[horizon]
        greater = int(np.sum(macro > candidate))
        equal = int(np.sum(macro == candidate))
        reports[str(horizon)] = {
            "draws": draws,
            "seed": 2026072902,
            "chunk_size": chunk_size,
            "membership_digest": membership_hash.hexdigest(),
            "candidate_better_than_random_midrank": (
                greater + 0.5 * equal
            )
            / draws,
            "random_as_good_or_better_rate": float(
                (np.sum(macro < candidate) + 0.5 * equal) / draws
            ),
            "mean_difference": float(macro.mean()),
            "quantiles": {
                "0.025": float(np.quantile(macro, 0.025)),
                "0.5": float(np.quantile(macro, 0.5)),
                "0.975": float(np.quantile(macro, 0.975)),
            },
        }
    return reports


def _thy_outcome_gate(
    horizons: Mapping[str, Mapping[str, object]],
) -> Mapping[str, Any]:
    h5 = _mapping(horizons, "5")
    h10 = _mapping(horizons, "10")
    h5_wide = _mapping(h5, "wide")
    h10_wide = _mapping(h10, "wide")
    h5_views = _mapping(h5, "group_directions")
    h10_views = _mapping(h10, "group_directions")
    h5_requirements = {
        "candidate_minus_full_at_most_minus_0_005": (
            float(h5_wide["difference"]) <= -0.005
        ),
        "repository_bootstrap_upper_below_zero": (
            float(
                _mapping(h5, "repository_bootstrap_interval_95")["upper"]
            )
            < 0.0
        ),
        "at_least_7_favorable_repositories": (
            int(h5_wide["favorable_repository_count"]) >= 7
        ),
        "every_leave_one_repository_out_below_zero": all(
            float(item["difference"]) < 0.0
            for item in _mapping_sequence(h5_wide, "leave_one_repository_out")
        ),
        "random_midrank_at_least_0_90": (
            float(
                _mapping(h5, "random_calibration")[
                    "candidate_better_than_random_midrank"
                ]
            )
            >= 0.90
        ),
        "candidate_beats_stationary_coreset": (
            float(_mapping(h5, "control_differences")["stationary_coreset"])
            < 0.0
        ),
        "at_least_24_favorable_configurations": (
            int(_mapping(h5_views, "configuration")["favorable_count"]) >= 24
        ),
        "at_least_8_favorable_models": (
            int(_mapping(h5_views, "model")["favorable_count"]) >= 8
        ),
        "at_least_2_favorable_harnesses": (
            int(_mapping(h5_views, "harness")["favorable_count"]) >= 2
        ),
    }
    h10_requirements = {
        "candidate_minus_full_below_zero": float(h10_wide["difference"]) < 0.0,
        "at_least_6_favorable_repositories": (
            int(h10_wide["favorable_repository_count"]) >= 6
        ),
        "random_midrank_at_least_0_50": (
            float(
                _mapping(h10, "random_calibration")[
                    "candidate_better_than_random_midrank"
                ]
            )
            >= 0.50
        ),
        "at_least_19_favorable_configurations": (
            int(_mapping(h10_views, "configuration")["favorable_count"]) >= 19
        ),
    }
    return {
        "h5": h5_requirements,
        "h10": h10_requirements,
        "all_requirements_met": all(h5_requirements.values())
        and all(h10_requirements.values()),
    }


def _loss_row(
    inputs: AuditInputs,
    *,
    repository_id: str,
    origin: RepositoryOrigin,
    held_out: int,
    candidate: Sequence[int],
    full: Sequence[int],
    controls: Mapping[str, Sequence[int]],
    future: Sequence[int],
) -> Mapping[str, object]:
    if (
        len(candidate) != 10
        or len(candidate) != len(set(candidate))
        or not candidate
        or not full
        or not future
    ):
        raise ValueError("pass-rate MAE row membership is invalid")
    outcomes = inputs.data.outcomes[:, held_out]
    future_rate = float(outcomes[list(future)].mean())

    def loss(indices: Sequence[int]) -> float:
        return abs(float(outcomes[list(indices)].mean()) - future_rate)

    candidate_loss = loss(candidate)
    full_loss = loss(full)
    return {
        "repository_id": repository_id,
        "origin_id": origin.origin_id,
        "configuration_id": inputs.data.configuration_ids[held_out],
        "candidate_loss": candidate_loss,
        "full_loss": full_loss,
        "difference": candidate_loss - full_loss,
        "control_losses": {
            key: loss(indices) for key, indices in sorted(controls.items())
        },
    }


def _summarize_rows(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
    deep_repository_ids: Sequence[str],
    configuration_metadata: Sequence[Mapping[str, str]],
    selector_plan: Mapping[str, object],
) -> dict[str, Any]:
    wide = _repository_summary(rows, repository_ids)
    deep = _repository_summary(rows, deep_repository_ids)
    control_ids = tuple(
        sorted(
            _mapping(rows[0], "control_losses")
        )
    )
    control_differences = {
        control_id: _control_difference(rows, repository_ids, control_id)
        for control_id in control_ids
    }
    metadata = {
        _required_string(item, "configuration_id"): item
        for item in configuration_metadata
    }
    configuration_groups = {
        configuration_id: (configuration_id,)
        for configuration_id in sorted(metadata)
    }
    model_groups: dict[str, list[str]] = defaultdict(list)
    harness_groups: dict[str, list[str]] = defaultdict(list)
    for configuration_id, item in metadata.items():
        model_groups[_required_string(item, "model_family")].append(
            configuration_id
        )
        harness_groups[_required_string(item, "harness_family")].append(
            configuration_id
        )
    group_directions = {
        "configuration": _group_direction_summary(
            rows,
            repository_ids,
            configuration_groups,
        ),
        "model": _group_direction_summary(
            rows,
            repository_ids,
            {
                key: tuple(sorted(value))
                for key, value in sorted(model_groups.items())
            },
        ),
        "harness": _group_direction_summary(
            rows,
            repository_ids,
            {
                key: tuple(sorted(value))
                for key, value in sorted(harness_groups.items())
            },
        ),
        "language": _language_direction_summary(
            wide,
            selector_plan,
        ),
    }
    return {
        "wide": wide,
        "deep": deep,
        "control_differences": control_differences,
        "group_directions": group_directions,
    }


def _repository_summary(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    by_repository: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    allowed = set(repository_ids)
    for row in rows:
        repository_id = _required_string(row, "repository_id")
        if repository_id in allowed:
            by_repository[repository_id].append(row)
    if set(by_repository) != allowed:
        raise ValueError("repository summary does not cover its frame")
    repository_rows = []
    for repository_id in repository_ids:
        values = by_repository[repository_id]
        repository_rows.append(
            {
                "repository_id": repository_id,
                "cell_count": len(values),
                "candidate_loss": _mean(
                    tuple(
                        _number(item.get("candidate_loss"), "candidate loss")
                        for item in values
                    )
                ),
                "full_loss": _mean(
                    tuple(
                        _number(item.get("full_loss"), "full loss")
                        for item in values
                    )
                ),
                "difference": _mean(
                    tuple(
                        _number(item.get("difference"), "difference")
                        for item in values
                    )
                ),
            }
        )
    differences = tuple(float(item["difference"]) for item in repository_rows)
    return {
        "repository_count": len(repository_rows),
        "cell_count": sum(int(item["cell_count"]) for item in repository_rows),
        "candidate_loss": _mean(
            tuple(float(item["candidate_loss"]) for item in repository_rows)
        ),
        "full_loss": _mean(
            tuple(float(item["full_loss"]) for item in repository_rows)
        ),
        "difference": _mean(differences),
        "favorable_repository_count": sum(value < 0.0 for value in differences),
        "repository_rows": tuple(repository_rows),
        "leave_one_repository_out": tuple(
            {
                "omitted_repository_id": repository_rows[index][
                    "repository_id"
                ],
                "difference": _mean(
                    differences[:index] + differences[index + 1 :]
                ),
            }
            for index in range(len(repository_rows))
        ),
    }


def _control_difference(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
    control_id: str,
) -> float:
    by_repository: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        repository_id = _required_string(row, "repository_id")
        if repository_id not in repository_ids:
            continue
        control_loss = _number(
            _mapping(row, "control_losses").get(control_id),
            f"{control_id} loss",
        )
        by_repository[repository_id].append(
            _number(row.get("candidate_loss"), "candidate loss") - control_loss
        )
    return _mean(
        tuple(
            _mean(tuple(by_repository[repository_id]))
            for repository_id in repository_ids
        )
    )


def _group_direction_summary(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
    groups: Mapping[str, Sequence[str]],
) -> Mapping[str, Any]:
    values = {}
    for group_id, configuration_ids in groups.items():
        selected = [
            row
            for row in rows
            if row.get("configuration_id") in configuration_ids
        ]
        values[group_id] = float(
            _repository_summary(selected, repository_ids)["difference"]
        )
    return {
        "group_count": len(values),
        "favorable_count": sum(value < 0.0 for value in values.values()),
        "differences": values,
        "interpretation": (
            "post-selection direction only; not group-holdout rematerialization"
        ),
    }


def _language_direction_summary(
    wide: Mapping[str, object],
    selector_plan: Mapping[str, object],
) -> Mapping[str, Any]:
    language_by_repository = {
        _required_string(item, "repository_id"): _required_string(item, "language")
        for item in _mapping_sequence(selector_plan, "lineage_and_language")
    }
    values: dict[str, list[float]] = defaultdict(list)
    for row in _mapping_sequence(wide, "repository_rows"):
        repository_id = _required_string(row, "repository_id")
        values[language_by_repository[repository_id]].append(
            _number(row.get("difference"), "repository difference")
        )
    directions = {
        language: _mean(tuple(items))
        for language, items in sorted(values.items())
    }
    return {
        "group_count": len(directions),
        "favorable_count": sum(value < 0.0 for value in directions.values()),
        "differences": directions,
        "interpretation": (
            "post-selection direction only; not language-holdout rematerialization"
        ),
    }


def _repository_bootstrap(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
    *,
    resamples: int,
    seed: int,
) -> Mapping[str, Any]:
    import numpy as np

    summary = _repository_summary(rows, repository_ids)
    values = np.asarray(
        [
            _number(item.get("difference"), "repository difference")
            for item in _mapping_sequence(summary, "repository_rows")
        ],
        dtype=np.float64,
    )
    generator = np.random.default_rng(seed)
    samples = values[
        generator.integers(0, len(values), size=(resamples, len(values)))
    ].mean(axis=1)
    return {
        "resamples": resamples,
        "seed": seed,
        "quantile_method": "NumPy 2.5.1 default linear",
        "lower": float(np.quantile(samples, 0.025)),
        "upper": float(np.quantile(samples, 0.975)),
    }


def _repository_first_difference(
    rows: Sequence[Mapping[str, object]],
    repository_ids: Sequence[str],
) -> float:
    by_repository: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        by_repository[_required_string(row, "repository_id")].append(
            _number(row.get("difference"), "proxy difference")
        )
    return _mean(
        tuple(
            _mean(tuple(by_repository[repository_id]))
            for repository_id in repository_ids
        )
    )


def _primary_decision(
    horizons: Mapping[str, Mapping[str, object]],
    *,
    h5_limit: float,
    h5_repository_minimum: int,
    h10_repository_minimum: int,
) -> Mapping[str, Any]:
    h5 = _mapping(_mapping(horizons, "5"), "wide")
    h10 = _mapping(_mapping(horizons, "10"), "wide")
    requirements = {
        "h5_difference_at_most_limit": float(h5["difference"]) <= h5_limit,
        "h5_repository_count": (
            int(h5["favorable_repository_count"]) >= h5_repository_minimum
        ),
        "h5_every_leave_one_repository_out": all(
            float(item["difference"]) < 0.0
            for item in _mapping_sequence(h5, "leave_one_repository_out")
        ),
        "h5_deep_negative": (
            float(_mapping(_mapping(horizons, "5"), "deep")["difference"]) < 0.0
        ),
        "h10_negative": float(h10["difference"]) < 0.0,
        "h10_repository_count": (
            int(h10["favorable_repository_count"]) >= h10_repository_minimum
        ),
        "h10_deep_negative": (
            float(_mapping(_mapping(horizons, "10"), "deep")["difference"]) < 0.0
        ),
    }
    return {
        "requirements": requirements,
        "all_primary_requirements_met": all(requirements.values()),
        "decision": (
            "primary_mae_passes"
            if all(requirements.values())
            else "primary_mae_rejects"
        ),
    }


def _primary_terminal_state(
    decision: Mapping[str, object],
) -> str:
    return (
        "primary_mae_supports_but_complete_gate_is_under_specified"
        if decision.get("all_primary_requirements_met") is True
        else "primary_mae_rejects"
    )


def _horizon_frame(
    tasks: Sequence[TaskMetadata],
    selector_plan: Mapping[str, object],
    horizon: int,
) -> tuple[
    Mapping[str, tuple[RepositoryOrigin, ...]],
    tuple[str, ...],
    tuple[str, ...],
]:
    rolling = _mapping(selector_plan, "rolling_origin")
    origins = build_repository_origins(
        tasks,
        minimum_initial_history_tasks=int(
            rolling["minimum_initial_history_tasks"]
        ),
        future_block_tasks=horizon,
    )
    repository_ids = (
        _string_tuple(rolling.get("primary_repository_ids"), "H5 repositories")
        if horizon == 5
        else _string_tuple(
            rolling.get("sensitivity_common_repository_ids"),
            "H10 repositories",
        )
    )
    return origins, repository_ids, _deep_repository_ids(selector_plan, horizon)


def _deep_repository_ids(
    selector_plan: Mapping[str, object],
    horizon: int,
) -> tuple[str, ...]:
    rolling = _mapping(selector_plan, "rolling_origin")
    return (
        _string_tuple(
            rolling.get("primary_deep_repository_ids"),
            "H5 deep repositories",
        )
        if horizon == 5
        else _string_tuple(
            rolling.get("sensitivity_deep_repository_ids"),
            "H10 deep repositories",
        )
    )


def _alg_007_memberships(
    task_space: Mapping[str, object],
    horizon: int,
    repository_ids: Sequence[str],
) -> Mapping[str, tuple[str, ...]]:
    horizon_payload = _mapping(_mapping(task_space, "horizons"), str(horizon))
    if _string_tuple(
        horizon_payload.get("repository_ids"),
        "ALG-007 repositories",
    ) != tuple(repository_ids):
        raise ValueError("ALG-007 repository frame changed")
    memberships = _mapping(
        _mapping(horizon_payload, "memberships"),
        "alg_007_centroid_recent_15",
    )
    return {
        origin_id: _string_tuple(value, "ALG-007 membership")
        for origin_id, value in memberships.items()
    }


def compact_result(result: Mapping[str, object]) -> Mapping[str, Any]:
    """Remove raw group vectors while retaining every decision input."""
    verify_result(result)
    compact = json.loads(canonical_json(result))
    algorithms = _mapping(compact, "algorithms")
    for algorithm in algorithms.values():
        if not isinstance(algorithm, Mapping):
            raise ValueError("algorithm result is invalid")
        horizons = _mapping(algorithm, "horizons")
        for horizon in horizons.values():
            if not isinstance(horizon, dict):
                raise ValueError("horizon result is invalid")
            for frame in ("wide", "deep"):
                summary = horizon.get(frame)
                if isinstance(summary, dict):
                    summary.pop("repository_rows", None)
                    summary.pop("leave_one_repository_out", None)
            groups = horizon.get("group_directions")
            if isinstance(groups, dict):
                for group in groups.values():
                    if isinstance(group, dict):
                        group.pop("differences", None)
    compact["schema_version"] = SUMMARY_SCHEMA
    compact.pop("result_digest", None)
    compact["parent_result_digest"] = result.get("result_digest")
    compact["summary_digest"] = canonical_digest(compact)
    return compact


def verify_result(result: Mapping[str, object]) -> None:
    """Verify the result's own identity and resource boundary."""
    if result.get("schema_version") != RESULT_SCHEMA:
        raise ValueError("surrogate-gate audit result schema is unsupported")
    payload = dict(result)
    digest = payload.pop("result_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("surrogate-gate audit result digest does not match")
    resources = _mapping(result, "resource_use")
    for key in (
        "paid_api_calls",
        "new_agent_outcome_calls",
        "sealed_holdout_reads",
    ):
        if resources.get(key) != 0:
            raise ValueError("surrogate-gate audit result exceeds resources")
    algorithms = _mapping(result, "algorithms")
    if set(algorithms) != {"ALG-013", "ALG-014", "THY-002S"}:
        raise ValueError("surrogate-gate audit algorithm set changed")
    if any(
        not isinstance(algorithm, Mapping)
        or algorithm.get("terminal_state") not in ALGORITHM_TERMINAL_STATES
        for algorithm in algorithms.values()
    ):
        raise ValueError("surrogate-gate audit terminal state changed")
    amendments = result.get("active_amendment_digests")
    if (
        not isinstance(amendments, Sequence)
        or isinstance(amendments, (str, bytes))
        or len(amendments) != 2
        or any(not isinstance(item, str) or not item for item in amendments)
    ):
        raise ValueError("surrogate-gate amendment chain changed")


def _bound_path(
    mapping: Mapping[str, object],
    key: str,
) -> Path:
    return REPOSITORY_ROOT / _required_string(mapping, key)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _mapping(
    payload: Mapping[str, object],
    key: str,
) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be a mapping")
    return value


def _mapping_sequence(
    payload: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, Any], ...]:
    value = payload.get(key)
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or any(not isinstance(item, Mapping) for item in value)
    ):
        raise ValueError(f"{key} must be a mapping sequence")
    return tuple(value)


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{label} must be a nonempty string sequence")
    result = tuple(value)
    if len(result) != len(set(result)):
        raise ValueError(f"{label} must not contain duplicates")
    return result


def _required_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a nonempty string")
    return value


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be numeric")
    normalized = float(value)
    if not -float("inf") < normalized < float("inf"):
        raise ValueError(f"{label} must be finite")
    return normalized


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires at least one value")
    return fsum(values) / len(values)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path)
    arguments = parser.parse_args(argv)
    if arguments.output.exists():
        raise ValueError(f"refusing to overwrite output: {arguments.output}")
    if arguments.summary is not None and arguments.summary.exists():
        raise ValueError(f"refusing to overwrite summary: {arguments.summary}")
    result = run_audit(arguments.plan)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    summary = compact_result(result)
    if arguments.summary is not None:
        arguments.summary.parent.mkdir(parents=True, exist_ok=True)
        arguments.summary.write_text(
            canonical_json(summary) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
