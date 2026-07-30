#!/usr/bin/env python3
"""Audit SWE-bench Full and conditionally replay frozen ALG-016U."""

from __future__ import annotations

# The explicit reproduction command supplies NumPy, SciPy, and PyArrow.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
import hashlib
import json
from math import fsum, isfinite
from pathlib import Path
import statistics
import sys
from typing import Any, Mapping, Sequence
from urllib.request import Request, urlopen


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    canonical_digest,
    canonical_json,
    parse_utc_timestamp,
)
from examples.multi_repository_study.public_replay import (  # noqa: E402
    RepositoryOrigin,
    TaskMetadata,
    build_repository_origins,
)
from examples.multi_swe_research.hindsight_diagnostic import (  # noqa: E402
    solve_exact_hindsight_subset,
)
from examples.multi_swe_research.suitability_audit import (  # noqa: E402
    _bootstrap_interval,
)
from examples.prequential_response_assembly.study import (  # noqa: E402
    shared_bocpd_forecast,
    solve_exact_l1_assembly,
)


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "plan.json"
DEFAULT_DATASET = (
    REPOSITORY_ROOT
    / "outputs"
    / "research"
    / "2026-07-28-external-benchmark-inventory"
    / "sources"
    / "swe_bench_full_test.parquet"
)
DEFAULT_RESULT_DIRECTORY = (
    REPOSITORY_ROOT
    / "outputs"
    / "research"
    / "2026-07-30-swe-bench-full-transfer"
    / "official-results"
)
DEFAULT_AUDIT_OUTPUT = (
    REPOSITORY_ROOT
    / "outputs"
    / "research"
    / "2026-07-30-swe-bench-full-transfer"
    / "suitability-result.json"
)
DEFAULT_TRANSFER_OUTPUT = (
    REPOSITORY_ROOT
    / "outputs"
    / "research"
    / "2026-07-30-swe-bench-full-transfer"
    / "alg-016u-result.json"
)
DEFAULT_SUMMARY = HERE / "evidence" / "summary.json"

PLAN_SCHEMA = "barcarolle_swe_bench_full_transfer_plan_v1"
AUDIT_SCHEMA = "barcarolle_swe_bench_full_suitability_result_v1"
TRANSFER_SCHEMA = "barcarolle_swe_bench_full_alg_016u_result_v1"
SUMMARY_SCHEMA = "barcarolle_swe_bench_full_transfer_summary_v1"

CURRENT_RESULT_FIELDS = frozenset(("no_generation", "no_logs", "resolved"))
LEGACY_RESULT_FIELDS = frozenset(
    (
        "applied",
        "generated",
        "install_fail",
        "no_apply",
        "no_generation",
        "reset_failed",
        "resolved",
        "test_errored",
        "test_timeout",
        "with_logs",
    )
)


def load_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    """Load the frozen self-digested contract and its bound prior evidence."""
    payload = dict(_load_mapping(path))
    digest = payload.pop("plan_digest", None)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("Full transfer plan schema is unsupported")
    if digest != canonical_digest(payload):
        raise ValueError("Full transfer plan digest does not match")
    payload["plan_digest"] = digest

    panel = _mapping(payload, "agent_panel")
    agents = _mapping_sequence(panel, "agents")
    if (
        _positive_integer(panel, "agent_count") != 11
        or len(agents) != 11
        or panel.get("panel_digest") != canonical_digest(agents)
    ):
        raise ValueError("Full transfer Agent panel changed")
    agent_ids = tuple(_required_string(row, "agent_id") for row in agents)
    submissions = tuple(_required_string(row, "submission") for row in agents)
    if len(agent_ids) != len(set(agent_ids)) or len(submissions) != len(
        set(submissions)
    ):
        raise ValueError("Full transfer Agent identities must be unique")

    frame = _mapping(payload, "frame")
    horizons = _mapping(frame, "horizons")
    if (
        _positive_integer(frame, "minimum_initial_history_tasks") != 20
        or _positive_integer(frame, "selection_budget_tasks") != 10
        or set(horizons) != {"5", "10"}
        or _positive_integer(_mapping(horizons, "5"), "expected_origin_count")
        != 408
        or _positive_integer(_mapping(horizons, "10"), "expected_origin_count")
        != 201
    ):
        raise ValueError("Full transfer rolling-Origin frame changed")

    algorithm = _mapping(payload, "conditional_algorithm")
    if algorithm.get("algorithm_id") != "ALG-016U":
        raise ValueError("Full transfer algorithm changed")
    authority = _mapping(payload, "authority")
    for key in (
        "paid_api_calls",
        "new_agent_outcome_calls",
        "sealed_swe_bench_verified_agent_reads",
        "core_schema_changes",
    ):
        if authority.get(key) != 0:
            raise ValueError("Full transfer authority changed")
    if authority.get("generator_development") is not False:
        raise ValueError("Full transfer Generator boundary changed")

    for binding in _mapping(payload, "bound_prior_artifacts").values():
        if not isinstance(binding, Mapping):
            raise ValueError("bound prior artifact must be an object")
        bound_path = REPOSITORY_ROOT / _required_string(binding, "path")
        if _file_sha256(bound_path) != _required_string(binding, "file_sha256"):
            raise ValueError(f"bound prior artifact changed: {bound_path}")
        logical = binding.get("logical_digest")
        if logical is not None:
            bound_payload = _load_mapping(bound_path)
            if logical not in bound_payload.values():
                raise ValueError(f"bound logical digest changed: {bound_path}")
    return payload


def normalize_official_result(
    task_denominator: Sequence[str],
    result_payload: Mapping[str, object],
    *,
    schema: str,
) -> tuple[Mapping[str, int], Mapping[str, int | str]]:
    """Map only ``resolved`` to pass under one exact official schema."""
    denominator = _unique_string_tuple(task_denominator, "Task denominator")
    denominator_set = set(denominator)
    expected = (
        CURRENT_RESULT_FIELDS
        if schema == "current"
        else LEGACY_RESULT_FIELDS
        if schema == "legacy"
        else None
    )
    if expected is None:
        raise ValueError("official result schema label is unsupported")
    if set(result_payload) != expected:
        raise ValueError("official result field set is unsupported")

    fields = {
        key: _unique_string_tuple(result_payload.get(key), key)
        for key in sorted(expected)
    }
    for key, task_ids in fields.items():
        if set(task_ids) - denominator_set:
            raise ValueError(f"{key} refers outside the Task denominator")
    if schema == "current":
        flattened = tuple(
            task_id for key in sorted(fields) for task_id in fields[key]
        )
        if len(flattened) != len(set(flattened)):
            raise ValueError("current official result categories overlap")

    resolved = set(fields["resolved"])
    listed = set().union(*(set(values) for values in fields.values()))
    outcomes = {task_id: int(task_id in resolved) for task_id in denominator}
    diagnostics: dict[str, int | str] = {
        "schema": schema,
        "resolved_count": len(resolved),
        "ordinary_unlisted_count": len(denominator_set - listed),
    }
    diagnostics.update(
        {f"{key}_count": len(values) for key, values in fields.items()}
    )
    return outcomes, diagnostics


def fetch_official_results(
    plan: Mapping[str, object],
    result_directory: Path = DEFAULT_RESULT_DIRECTORY,
) -> tuple[Mapping[str, object], ...]:
    """Fetch only the eleven result blobs allowed by the committed plan."""
    source = _mapping(plan, "source")
    revision = _required_string(source, "result_revision")
    result_directory.mkdir(parents=True, exist_ok=True)
    manifests = []
    for row in _mapping_sequence(_mapping(plan, "agent_panel"), "agents"):
        submission = _required_string(row, "submission")
        expected_blob = _required_string(row, "result_blob_sha")
        expected_size = _positive_integer(row, "result_size_bytes")
        path = result_directory / f"{submission}.json"
        if path.exists():
            raw = path.read_bytes()
        else:
            url = (
                "https://raw.githubusercontent.com/SWE-bench/experiments/"
                f"{revision}/evaluation/test/{submission}/results/results.json"
            )
            request = Request(url, headers={"User-Agent": "barcarolle-research"})
            with urlopen(request, timeout=60) as response:
                raw = response.read()
            if not raw:
                raise RuntimeError(f"official result download is empty: {submission}")
            path.write_bytes(raw)
        if len(raw) != expected_size or _git_blob_sha(raw) != expected_blob:
            raise ValueError(f"official result identity changed: {submission}")
        manifests.append(
            {
                "submission": submission,
                "path": str(path.relative_to(REPOSITORY_ROOT)),
                "result_blob_sha": expected_blob,
                "size_bytes": len(raw),
            }
        )
    return tuple(manifests)


def load_full_inputs(
    *,
    plan: Mapping[str, object],
    dataset_path: Path = DEFAULT_DATASET,
    result_directory: Path = DEFAULT_RESULT_DIRECTORY,
) -> tuple[
    tuple[TaskMetadata, ...],
    Mapping[str, Mapping[str, int]],
    Mapping[str, Mapping[str, int | str]],
    Mapping[str, Mapping[str, str]],
    Mapping[str, object],
]:
    """Load and identity-check the exact Full Task and checked Agent panel."""
    import pyarrow.parquet as parquet

    source = _mapping(plan, "source")
    if (
        _file_sha256(dataset_path) != _required_string(source, "dataset_sha256")
        or dataset_path.stat().st_size
        != _positive_integer(source, "dataset_size_bytes")
    ):
        raise ValueError("SWE-bench Full dataset identity changed")
    rows = tuple(
        parquet.read_table(
            dataset_path,
            columns=[
                "instance_id",
                "repo",
                "created_at",
                "problem_statement",
                "FAIL_TO_PASS",
                "PASS_TO_PASS",
            ],
        ).to_pylist()
    )
    if len(rows) != _positive_integer(source, "task_count"):
        raise ValueError("SWE-bench Full Task count changed")
    task_ids = tuple(sorted(_required_row_string(row, "instance_id") for row in rows))
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("SWE-bench Full instance IDs are not unique")
    if canonical_digest(task_ids) != _required_string(
        source,
        "task_denominator_digest",
    ):
        raise ValueError("SWE-bench Full Task denominator changed")
    check_projection = tuple(
        {
            key: row[key]
            for key in (
                "instance_id",
                "repo",
                "created_at",
                "FAIL_TO_PASS",
                "PASS_TO_PASS",
            )
        }
        for row in sorted(rows, key=lambda item: str(item["instance_id"]))
    )
    if canonical_digest(check_projection) != _required_string(
        source,
        "check_projection_digest",
    ):
        raise ValueError("SWE-bench Full Check projection changed")

    tasks = tuple(
        TaskMetadata(
            instance_id=_required_row_string(row, "instance_id"),
            repository_id=_required_row_string(row, "repo"),
            created_at=_required_row_string(row, "created_at"),
            difficulty="not-used",
            problem_statement=_required_row_string(row, "problem_statement"),
        )
        for row in rows
    )
    denominator = tuple(task.instance_id for task in tasks)
    outcomes = {}
    diagnostics = {}
    metadata = {}
    result_identities = []
    for agent in _mapping_sequence(_mapping(plan, "agent_panel"), "agents"):
        agent_id = _required_string(agent, "agent_id")
        submission = _required_string(agent, "submission")
        path = result_directory / f"{submission}.json"
        raw = path.read_bytes()
        if (
            len(raw) != _positive_integer(agent, "result_size_bytes")
            or _git_blob_sha(raw) != _required_string(agent, "result_blob_sha")
        ):
            raise ValueError(f"official result identity changed: {submission}")
        payload = json.loads(raw)
        if not isinstance(payload, Mapping):
            raise ValueError("official result must be an object")
        agent_outcomes, agent_diagnostics = normalize_official_result(
            denominator,
            payload,
            schema=_required_string(agent, "result_schema"),
        )
        outcomes[agent_id] = agent_outcomes
        diagnostics[agent_id] = agent_diagnostics
        metadata[agent_id] = {
            "agent_id": agent_id,
            "submission": submission,
            "mechanism_family": _required_string(agent, "mechanism_family"),
        }
        result_identities.append(
            {
                "agent_id": agent_id,
                "result_blob_sha": _required_string(agent, "result_blob_sha"),
            }
        )
    panel = _mapping(plan, "agent_panel")
    if len(outcomes) != _positive_integer(panel, "agent_count"):
        raise ValueError("normalized Full Agent panel changed")
    identities: dict[str, object] = {
        "dataset_sha256": _file_sha256(dataset_path),
        "task_denominator_digest": canonical_digest(task_ids),
        "check_projection_digest": canonical_digest(check_projection),
        "panel_digest": panel.get("panel_digest"),
        "result_identities": tuple(result_identities),
        "normalized_outcome_matrix_digest": canonical_digest(
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
        identities,
    )


def run_suitability_audit(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    outcome_diagnostics: Mapping[str, Mapping[str, int | str]],
    agent_metadata: Mapping[str, Mapping[str, str]],
    identities: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Run the frozen candidate-free H5/H10 suitability audit."""
    np, versions = _verified_runtime(plan)
    task_ids = tuple(task.instance_id for task in tasks)
    if any(set(outcomes) != set(task_ids) for outcomes in outcomes_by_agent.values()):
        raise ValueError("every Full Agent must cover the exact denominator")
    agent_ids = tuple(sorted(outcomes_by_agent))
    if set(agent_ids) != set(agent_metadata):
        raise ValueError("Full Agent metadata changed")
    response_patterns = {
        tuple(outcomes_by_agent[agent_id][task_id] for agent_id in agent_ids)
        for task_id in task_ids
    }

    horizon_results = {}
    for horizon in (5, 10):
        origins, repository_ids = _origins_for_horizon(tasks, plan, horizon)
        horizon_results[str(horizon)] = _run_suitability_horizon(
            np=np,
            horizon=horizon,
            repository_ids=repository_ids,
            origins_by_repository=origins,
            outcomes_by_agent=outcomes_by_agent,
            agent_ids=agent_ids,
            joint_response_pattern_count=len(response_patterns),
            plan=plan,
        )
    decision = build_suitability_decision(horizon_results)
    result: dict[str, Any] = {
        "schema_version": AUDIT_SCHEMA,
        "study_id": plan.get("study_id"),
        "epistemic_status": plan.get("epistemic_status"),
        "plan_digest": plan.get("plan_digest"),
        "identities": dict(identities),
        "agent_metadata": agent_metadata,
        "outcome_diagnostics": outcome_diagnostics,
        "horizons": horizon_results,
        "decision": decision,
        "implementation": {
            "implementation_file_sha256": _file_sha256(Path(__file__)),
            **versions,
        },
        "resource_use": {
            "paid_api_calls": 0,
            "new_agent_outcome_calls": 0,
            "sealed_swe_bench_verified_agent_reads": 0,
            "generator_development": False,
        },
        "claim_boundary": plan.get("claim_boundary"),
    }
    result["suitability_result_digest"] = canonical_digest(result)
    return result


def run_joint_block_order_null(
    *,
    np: Any,
    repository_ids: Sequence[str],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    horizon: int,
    draws: int,
    seed: int,
) -> Mapping[str, Any]:
    """Permute complete future blocks while preserving each joint block."""
    if horizon <= 0 or draws <= 0:
        raise ValueError("joint-block null inputs must be positive")
    agent_ids = tuple(sorted(outcomes_by_agent))
    sequences = {}
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
        initial = len(origins[0].history)
        tail = response[initial:]
        if len(tail) != horizon * len(origins):
            raise ValueError("joint-block null frame is not complete")
        sequences[repository_id] = {
            "prefix": response[:initial],
            "blocks": tail.reshape(len(origins), horizon, len(agent_ids)),
        }

    observed_full_rows = []
    observed_zero_rows = []
    observed_one_rows = []
    for repository_id in repository_ids:
        sequence = sequences[repository_id]
        full, zero, one = _sequence_control_losses(
            np=np,
            prefix=sequence["prefix"],
            blocks=sequence["blocks"],
        )
        observed_full_rows.append(full)
        observed_zero_rows.append(zero)
        observed_one_rows.append(one)
    observed_full = _mean(observed_full_rows)
    observed_zero = _mean(observed_zero_rows)
    observed_one = _mean(observed_one_rows)
    observed_best = min(observed_zero, observed_one)
    observed = observed_full - observed_best

    generator = np.random.Generator(np.random.PCG64(seed))
    null_values = []
    for _ in range(draws):
        repository_full = []
        for repository_id in repository_ids:
            sequence = sequences[repository_id]
            blocks = sequence["blocks"]
            permutation = generator.permutation(len(blocks))
            full, _, _ = _sequence_control_losses(
                np=np,
                prefix=sequence["prefix"],
                blocks=blocks[permutation],
            )
            repository_full.append(full)
        null_values.append(_mean(repository_full) - observed_best)
    ordered = tuple(sorted(null_values))
    as_good = sum(value <= observed + 1e-15 for value in null_values)
    return {
        "null_id": "joint_future_block_order_permutation",
        "horizon": horizon,
        "draws": draws,
        "seed": seed,
        "generator": "NumPy PCG64",
        "observed": observed,
        "observed_full_history_mae": observed_full,
        "observed_best_fixed_constant_mae": observed_best,
        "best_fixed_constant": (
            "always_zero" if observed_zero <= observed_one else "always_one"
        ),
        "null_mean": _mean(null_values),
        "null_interval_95": {
            "lower": _linear_quantile(ordered, 0.025),
            "upper": _linear_quantile(ordered, 0.975),
        },
        "one_sided_probability": (1 + as_good) / (draws + 1),
        "null_values_digest": canonical_digest(null_values),
        "null_values": tuple(null_values),
        "destroys": "order and adjacency between complete future blocks",
        "preserves": (
            "initial history, within-block order, joint Agent vectors, "
            "repository prevalence, and the future-block multiset"
        ),
    }


def build_suitability_decision(
    horizons: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    """Apply the frozen source gate without inspecting an algorithm result."""
    if set(horizons) != {"5", "10"}:
        raise ValueError("suitability decision requires H5 and H10")
    metrics = {
        horizon: (
            _mapping(row, "controls_source")
            if "controls_source" in row
            else row
        )
        for horizon, row in horizons.items()
    }
    resolution = all(
        _positive_integer(row, "repository_count") >= 8
        and _positive_integer(row, "origin_count") >= 100
        and _finite_number(
            row.get("largest_repository_origin_share"),
            "largest repository share",
        )
        < 0.5
        and _positive_integer(row, "joint_response_pattern_count") >= 10
        and 0.05
        < _finite_number(
            row.get("future_outcome_cell_density"),
            "future density",
        )
        < 0.95
        for row in metrics.values()
    )
    headroom = all(
        _finite_number(row.get("full_history_mae"), "full MAE")
        - _finite_number(row.get("oracle_mae"), "oracle MAE")
        >= 0.02 - 1e-15
        for row in metrics.values()
    )
    nontrivial = all(
        _finite_number(
            row.get("best_fixed_constant_mae"),
            "best fixed constant MAE",
        )
        - _finite_number(row.get("full_history_mae"), "full MAE")
        >= 0.02 - 1e-15
        and _finite_number(
            row.get("full_minus_best_fixed_constant_bootstrap_upper"),
            "bootstrap upper",
        )
        < 0.0
        for row in metrics.values()
    )
    chronology = (
        _finite_number(
            metrics["5"].get("joint_block_order_null_probability"),
            "H5 joint-block null probability",
        )
        <= 0.05
    )
    gates = {
        "resolution": resolution,
        "headroom": headroom,
        "nontrivial_prediction": nontrivial,
        "chronology": chronology,
    }
    authorized = all(gates.values())
    return {
        "gates": gates,
        "algorithm_execution_authorized": authorized,
        "terminal_state": (
            "source_suitable_for_conditional_alg_016u"
            if authorized
            else "suitability_gate_rejects_before_algorithm"
        ),
        "selector_nominated": False,
        "independent_confirmation": False,
    }


def select_alg_016u_origin_memberships(
    history: Any,
    *,
    horizon: int,
    budget: int,
    created_order: Sequence[tuple[str, str]],
) -> Mapping[int, Mapping[str, tuple[int, ...]]]:
    """Materialize frozen unseen-target memberships for one Origin."""
    import numpy as np

    values = np.asarray(history, dtype=np.float64)
    if (
        values.ndim != 2
        or values.shape[1] < 2
        or values.shape[0] != len(created_order)
        or budget <= 0
        or budget > len(values)
    ):
        raise ValueError("ALG-016U Origin inputs are invalid")
    result = {}
    for held_out in range(values.shape[1]):
        visible = tuple(
            index for index in range(values.shape[1]) if index != held_out
        )
        visible_history = values[:, list(visible)]
        forecast = shared_bocpd_forecast(visible_history, horizon=horizon)
        candidate = solve_exact_l1_assembly(
            visible_history,
            forecast.mixture,
            budget=budget,
            created_order=created_order,
        )
        stationary = solve_exact_l1_assembly(
            visible_history,
            visible_history.mean(axis=0),
            budget=budget,
            created_order=created_order,
        )
        result[held_out] = {
            "ALG-016U": candidate.indices,
            "unseen_full_response_assembly": stationary.indices,
            "ordinary_recency": tuple(range(len(values) - budget, len(values))),
        }
    return result


def run_alg_016u_transfer(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    identities: Mapping[str, object],
    audit_result: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Run unchanged ALG-016U only after the candidate-free source gate."""
    np, versions = _verified_runtime(plan)
    _validate_audit_result(audit_result, plan)
    if not bool(
        _mapping(audit_result, "decision").get(
            "algorithm_execution_authorized"
        )
    ):
        raise ValueError("suitability gate does not authorize ALG-016U")
    if _mapping(audit_result, "identities") != identities:
        raise ValueError("transfer inputs differ from suitability inputs")
    agent_ids = tuple(sorted(outcomes_by_agent))
    budget = _positive_integer(_mapping(plan, "frame"), "selection_budget_tasks")
    horizon_results = {}
    for horizon in (5, 10):
        origins, repository_ids = _origins_for_horizon(tasks, plan, horizon)
        rows = []
        for position, repository_id in enumerate(repository_ids, start=1):
            for origin in origins[repository_id]:
                history_ids = tuple(task.instance_id for task in origin.history)
                future_ids = tuple(task.instance_id for task in origin.future)
                history = np.asarray(
                    [
                        [
                            outcomes_by_agent[agent_id][task_id]
                            for agent_id in agent_ids
                        ]
                        for task_id in history_ids
                    ],
                    dtype=np.float64,
                )
                future = np.asarray(
                    [
                        [
                            outcomes_by_agent[agent_id][task_id]
                            for agent_id in agent_ids
                        ]
                        for task_id in future_ids
                    ],
                    dtype=np.float64,
                )
                created_order = tuple(
                    (task.created_at, task.instance_id) for task in origin.history
                )
                memberships = select_alg_016u_origin_memberships(
                    history,
                    horizon=horizon,
                    budget=budget,
                    created_order=created_order,
                )
                future_rates = future.mean(axis=0)
                for held_out, agent_id in enumerate(agent_ids):
                    selected = memberships[held_out]
                    losses = {
                        algorithm_id: float(
                            abs(
                                history[list(indices), held_out].mean()
                                - future_rates[held_out]
                            )
                        )
                        for algorithm_id, indices in selected.items()
                    }
                    losses["full_history"] = float(
                        abs(history[:, held_out].mean() - future_rates[held_out])
                    )
                    rows.append(
                        {
                            "repository_id": repository_id,
                            "origin_id": origin.origin_id,
                            "target_agent_id": agent_id,
                            "history_task_count": len(history_ids),
                            "future_task_count": len(future_ids),
                            "memberships": {
                                algorithm_id: tuple(
                                    history_ids[index] for index in indices
                                )
                                for algorithm_id, indices in selected.items()
                            },
                            "losses": losses,
                        }
                    )
            print(
                f"ALG-016U H{horizon} repository "
                f"{position}/{len(repository_ids)} {repository_id}",
                flush=True,
            )
        horizon_results[str(horizon)] = _summarize_transfer_horizon(
            rows=rows,
            repository_ids=repository_ids,
            agent_ids=agent_ids,
            audit_horizon=_mapping(
                _mapping(audit_result, "horizons"),
                str(horizon),
            ),
            plan=plan,
            horizon=horizon,
        )
    point_transfer = all(
        _finite_number(row.get("candidate_minus_full"), "candidate difference")
        < 0.0
        for row in horizon_results.values()
    )
    robust_transfer = point_transfer and all(
        bool(row.get("robust_transfer_gate_passed"))
        for row in horizon_results.values()
    )
    terminal_state = (
        "alg_016u_robust_transfer"
        if robust_transfer
        else "alg_016u_point_transfer_only"
        if point_transfer
        else "alg_016u_transfer_refuted"
    )
    result: dict[str, Any] = {
        "schema_version": TRANSFER_SCHEMA,
        "study_id": plan.get("study_id"),
        "epistemic_status": plan.get("epistemic_status"),
        "plan_digest": plan.get("plan_digest"),
        "suitability_result_digest": audit_result.get(
            "suitability_result_digest"
        ),
        "identities": dict(identities),
        "algorithm_id": "ALG-016U",
        "horizons": horizon_results,
        "decision": {
            "terminal_state": terminal_state,
            "point_transfer_gate_passed": point_transfer,
            "robust_transfer_gate_passed": robust_transfer,
            "production_promotion_allowed": False,
            "independent_confirmation": False,
        },
        "implementation": {
            "implementation_file_sha256": _file_sha256(Path(__file__)),
            **versions,
        },
        "resource_use": {
            "paid_api_calls": 0,
            "new_agent_outcome_calls": 0,
            "sealed_swe_bench_verified_agent_reads": 0,
            "generator_development": False,
        },
        "claim_boundary": plan.get("claim_boundary"),
    }
    result["transfer_result_digest"] = canonical_digest(result)
    return result


def build_compact_summary(
    *,
    plan: Mapping[str, object],
    audit_result: Mapping[str, object],
    audit_reproduction: Mapping[str, object],
    transfer_result: Mapping[str, object] | None = None,
    transfer_reproduction: Mapping[str, object] | None = None,
) -> Mapping[str, Any]:
    """Build committed evidence from two byte-identical executions."""
    _validate_audit_result(audit_result, plan)
    _validate_audit_result(audit_reproduction, plan)
    audit_identical = canonical_json(audit_result) == canonical_json(
        audit_reproduction
    )
    if not audit_identical:
        raise ValueError("suitability reproduction is not byte-identical")
    decision = _mapping(audit_result, "decision")
    authorized = bool(decision.get("algorithm_execution_authorized"))
    if authorized != (transfer_result is not None):
        raise ValueError("summary transfer evidence does not match source gate")

    compact_audit = {
        horizon: _compact_audit_horizon(_mapping(payload, "controls_source"))
        for horizon, payload in sorted(
            _mapping(audit_result, "horizons").items()
        )
    }
    transfer_payload = None
    transfer_identical = None
    if transfer_result is not None:
        if transfer_reproduction is None:
            raise ValueError("transfer reproduction is required")
        _validate_transfer_result(transfer_result, plan, audit_result)
        _validate_transfer_result(transfer_reproduction, plan, audit_result)
        transfer_identical = canonical_json(transfer_result) == canonical_json(
            transfer_reproduction
        )
        if not transfer_identical:
            raise ValueError("ALG-016U reproduction is not byte-identical")
        transfer_payload = {
            "result_digest": transfer_result.get("transfer_result_digest"),
            "byte_identical_second_run": transfer_identical,
            "decision": dict(_mapping(transfer_result, "decision")),
            "horizons": {
                horizon: _compact_transfer_horizon(payload)
                for horizon, payload in sorted(
                    _mapping(transfer_result, "horizons").items()
                )
            },
        }

    summary: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "study_id": plan.get("study_id"),
        "epistemic_status": plan.get("epistemic_status"),
        "identities": {
            "plan_digest": plan.get("plan_digest"),
            **dict(_mapping(audit_result, "identities")),
            "suitability_result_digest": audit_result.get(
                "suitability_result_digest"
            ),
        },
        "reproduction": {
            "suitability_byte_identical_second_run": audit_identical,
            "transfer_byte_identical_second_run": transfer_identical,
        },
        "suitability": {
            "horizons": compact_audit,
            "decision": dict(decision),
        },
        "transfer": transfer_payload,
        "resource_use": dict(_mapping(audit_result, "resource_use")),
        "claim_boundary": plan.get("claim_boundary"),
    }
    summary["summary_digest"] = canonical_digest(summary)
    return summary


def _run_suitability_horizon(
    *,
    np: Any,
    horizon: int,
    repository_ids: Sequence[str],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    agent_ids: Sequence[str],
    joint_response_pattern_count: int,
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    repository_rows = []
    agent_repository_rows: dict[str, list[Mapping[str, float]]] = {
        agent_id: [] for agent_id in agent_ids
    }
    oracle_rows = []
    future_positive_cells = 0
    future_cells = 0
    calendar_spans = []
    for position, repository_id in enumerate(repository_ids, start=1):
        full_losses = []
        zero_losses = []
        one_losses = []
        oracle_losses = []
        per_agent = {
            agent_id: {"full": [], "zero": [], "one": []}
            for agent_id in agent_ids
        }
        for origin in origins_by_repository[repository_id]:
            history_ids = tuple(task.instance_id for task in origin.history)
            future_ids = tuple(task.instance_id for task in origin.future)
            history = np.asarray(
                [
                    [
                        outcomes_by_agent[agent_id][task_id]
                        for agent_id in agent_ids
                    ]
                    for task_id in history_ids
                ],
                dtype=np.float64,
            )
            future = np.asarray(
                [
                    [
                        outcomes_by_agent[agent_id][task_id]
                        for agent_id in agent_ids
                    ]
                    for task_id in future_ids
                ],
                dtype=np.float64,
            )
            future_rates = future.mean(axis=0)
            full_by_agent = np.abs(history.mean(axis=0) - future_rates)
            zero_by_agent = future_rates
            one_by_agent = 1.0 - future_rates
            full_losses.append(float(full_by_agent.mean()))
            zero_losses.append(float(zero_by_agent.mean()))
            one_losses.append(float(one_by_agent.mean()))
            for index, agent_id in enumerate(agent_ids):
                per_agent[agent_id]["full"].append(float(full_by_agent[index]))
                per_agent[agent_id]["zero"].append(float(zero_by_agent[index]))
                per_agent[agent_id]["one"].append(float(one_by_agent[index]))
            selected, diagnostics = solve_exact_hindsight_subset(
                history_ids,
                future_ids,
                outcomes_by_agent,
                agent_ids,
                budget=_positive_integer(
                    _mapping(plan, "frame"),
                    "selection_budget_tasks",
                ),
            )
            selected_rates = np.asarray(
                [
                    [
                        outcomes_by_agent[agent_id][task_id]
                        for agent_id in agent_ids
                    ]
                    for task_id in selected
                ],
                dtype=np.float64,
            ).mean(axis=0)
            oracle_losses.append(
                float(np.abs(selected_rates - future_rates).mean())
            )
            oracle_rows.append(
                {
                    "repository_id": repository_id,
                    "origin_id": origin.origin_id,
                    "oracle_mae": oracle_losses[-1],
                    "response_pattern_count": diagnostics.get(
                        "response_pattern_count"
                    ),
                }
            )
            future_positive_cells += int(future.sum())
            future_cells += int(future.size)
            calendar_spans.append(
                (
                    parse_utc_timestamp(origin.future[-1].created_at)
                    - parse_utc_timestamp(origin.history[-1].created_at)
                ).total_seconds()
                / 86400.0
            )
        repository_rows.append(
            {
                "repository_id": repository_id,
                "origin_count": len(origins_by_repository[repository_id]),
                "full_history_mae": _mean(full_losses),
                "always_zero_mae": _mean(zero_losses),
                "always_one_mae": _mean(one_losses),
                "oracle_mae": _mean(oracle_losses),
            }
        )
        for agent_id in agent_ids:
            agent_repository_rows[agent_id].append(
                {
                    "full_history_mae": _mean(per_agent[agent_id]["full"]),
                    "always_zero_mae": _mean(per_agent[agent_id]["zero"]),
                    "always_one_mae": _mean(per_agent[agent_id]["one"]),
                }
            )
        print(
            f"suitability H{horizon} repository "
            f"{position}/{len(repository_ids)} {repository_id}",
            flush=True,
        )

    full = _mean([row["full_history_mae"] for row in repository_rows])
    zero = _mean([row["always_zero_mae"] for row in repository_rows])
    one = _mean([row["always_one_mae"] for row in repository_rows])
    oracle = _mean([row["oracle_mae"] for row in repository_rows])
    best_name = "always_zero" if zero <= one else "always_one"
    best = min(zero, one)
    constant_key = f"{best_name}_mae"
    differences = tuple(
        float(row["full_history_mae"]) - float(row[constant_key])
        for row in repository_rows
    )
    uncertainty = _mapping(_mapping(plan, "suitability_audit"), "uncertainty")
    bootstrap_seed = _positive_integer(
        uncertainty,
        "h5_seed" if horizon == 5 else "h10_seed",
    )
    bootstrap = _bootstrap_interval(
        differences,
        resamples=_positive_integer(
            uncertainty,
            "repository_bootstrap_resamples",
        ),
        seed=bootstrap_seed,
    )
    leave_one_repository_out = tuple(
        {
            "omitted_repository_id": repository_id,
            "full_minus_best_fixed_constant": _mean(
                [
                    value
                    for offset, value in enumerate(differences)
                    if offset != index
                ]
            ),
        }
        for index, repository_id in enumerate(repository_ids)
    )
    agent_rows = []
    for agent_id in agent_ids:
        rows = agent_repository_rows[agent_id]
        agent_full = _mean([row["full_history_mae"] for row in rows])
        agent_constant = _mean([row[constant_key] for row in rows])
        agent_rows.append(
            {
                "agent_id": agent_id,
                "full_history_mae": agent_full,
                f"{best_name}_mae": agent_constant,
                "full_minus_best_fixed_constant": agent_full - agent_constant,
            }
        )

    random_plan = _mapping(
        _mapping(plan, "suitability_audit"),
        "random",
    )
    random_result = _random_calibration(
        np=np,
        repository_ids=repository_ids,
        origins_by_repository=origins_by_repository,
        outcomes_by_agent=outcomes_by_agent,
        agent_ids=agent_ids,
        budget=_positive_integer(
            _mapping(plan, "frame"),
            "selection_budget_tasks",
        ),
        draws=_positive_integer(random_plan, "draws"),
        seed=_positive_integer(
            random_plan,
            "h5_seed" if horizon == 5 else "h10_seed",
        ),
    )
    null_plan = _mapping(
        _mapping(plan, "suitability_audit"),
        "joint_block_order_null",
    )
    temporal_null = run_joint_block_order_null(
        np=np,
        repository_ids=repository_ids,
        origins_by_repository=origins_by_repository,
        outcomes_by_agent=outcomes_by_agent,
        horizon=horizon,
        draws=_positive_integer(null_plan, "draws"),
        seed=_positive_integer(
            null_plan,
            "h5_seed" if horizon == 5 else "h10_seed",
        ),
    )
    if abs(float(temporal_null["observed"]) - (full - best)) > 1e-12:
        raise ValueError("joint-block null observed statistic changed")

    origin_count = sum(len(origins_by_repository[item]) for item in repository_ids)
    largest_share = max(
        len(origins_by_repository[item]) / origin_count for item in repository_ids
    )
    result: dict[str, Any] = {
        "frame": {
            "horizon": horizon,
            "repository_count": len(repository_ids),
            "origin_count": origin_count,
            "repository_ids": tuple(repository_ids),
            "largest_repository_origin_share": largest_share,
        },
        "prevalence": {
            "joint_response_pattern_count": joint_response_pattern_count,
            "future_outcome_cell_density": future_positive_cells / future_cells,
            "future_positive_cell_count": future_positive_cells,
            "future_cell_count": future_cells,
        },
        "controls": {
            "always_zero_mae": zero,
            "always_one_mae": one,
            "best_fixed_constant": best_name,
            "best_fixed_constant_mae": best,
            "full_history_mae": full,
            "random_mean_mae": full
            + _finite_number(
                random_result.get("mean_macro_repository_difference"),
                "random difference",
            ),
            "oracle_mae": oracle,
            "selection_headroom": full - oracle,
            "nontrivial_separation": best - full,
        },
        "uncertainty": {
            "contrast": "full_history_minus_best_fixed_constant",
            "observed": full - best,
            "repository_bootstrap_interval_95": {
                "lower": bootstrap["lower"],
                "upper": bootstrap["upper"],
            },
            "repository_bootstrap_values_digest": bootstrap["values_digest"],
            "leave_one_repository_out": leave_one_repository_out,
            "agent_rows": tuple(agent_rows),
        },
        "random_calibration": random_result,
        "joint_block_order_null": temporal_null,
        "calendar": {
            "cutoff_to_future_end_days": _distribution_summary(calendar_spans)
        },
        "repository_rows": tuple(repository_rows),
        "oracle_rows": tuple(oracle_rows),
    }
    result["controls_source"] = {
        "repository_count": len(repository_ids),
        "origin_count": origin_count,
        "largest_repository_origin_share": largest_share,
        "joint_response_pattern_count": joint_response_pattern_count,
        "future_outcome_cell_density": future_positive_cells / future_cells,
        "always_zero_mae": zero,
        "always_one_mae": one,
        "best_fixed_constant": best_name,
        "best_fixed_constant_mae": best,
        "full_history_mae": full,
        "random_mean_mae": result["controls"]["random_mean_mae"],
        "oracle_mae": oracle,
        "selection_headroom": full - oracle,
        "nontrivial_separation": best - full,
        "full_minus_best_fixed_constant_bootstrap_lower": bootstrap["lower"],
        "full_minus_best_fixed_constant_bootstrap_upper": bootstrap["upper"],
        "joint_block_order_null_probability": temporal_null[
            "one_sided_probability"
        ],
        "joint_block_order_null_observed": temporal_null["observed"],
        "joint_block_order_null_mean": temporal_null["null_mean"],
    }
    return result


def _random_calibration(
    *,
    np: Any,
    repository_ids: Sequence[str],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    agent_ids: Sequence[str],
    budget: int,
    draws: int,
    seed: int,
) -> Mapping[str, Any]:
    generator = np.random.Generator(np.random.PCG64(seed))
    macro_differences = np.zeros(draws, dtype=np.float64)
    batch_size = 512
    for repository_id in repository_ids:
        repository_differences = np.zeros(draws, dtype=np.float64)
        for origin in origins_by_repository[repository_id]:
            history = np.asarray(
                [
                    [
                        outcomes_by_agent[agent_id][task.instance_id]
                        for agent_id in agent_ids
                    ]
                    for task in origin.history
                ],
                dtype=np.float64,
            )
            future = np.asarray(
                [
                    [
                        outcomes_by_agent[agent_id][task.instance_id]
                        for agent_id in agent_ids
                    ]
                    for task in origin.future
                ],
                dtype=np.float64,
            )
            future_rate = future.mean(axis=0)
            baseline = float(np.abs(history.mean(axis=0) - future_rate).mean())
            for start in range(0, draws, batch_size):
                stop = min(start + batch_size, draws)
                keys = generator.random((stop - start, len(history)))
                indices = np.argpartition(keys, budget - 1, axis=1)[:, :budget]
                selected_rates = history[indices].mean(axis=1)
                losses = np.abs(selected_rates - future_rate).mean(axis=1)
                repository_differences[start:stop] += losses - baseline
        repository_differences /= len(origins_by_repository[repository_id])
        macro_differences += repository_differences
    macro_differences /= len(repository_ids)
    values = tuple(float(value) for value in macro_differences)
    ordered = tuple(sorted(values))
    standard_deviation = float(np.std(macro_differences))
    return {
        "draws": draws,
        "seed": seed,
        "generator": "NumPy PCG64 independent random keys per Origin and draw",
        "mean_macro_repository_difference": _mean(values),
        "population_standard_deviation": standard_deviation,
        "mean_monte_carlo_standard_error": standard_deviation / draws**0.5,
        "quantiles": {
            "0.025": _linear_quantile(ordered, 0.025),
            "0.5": _linear_quantile(ordered, 0.5),
            "0.975": _linear_quantile(ordered, 0.975),
        },
        "macro_differences_digest": canonical_digest(values),
        "macro_differences": values,
    }


def _sequence_control_losses(
    *,
    np: Any,
    prefix: Any,
    blocks: Any,
) -> tuple[float, float, float]:
    cumulative = prefix.sum(axis=0)
    history_count = len(prefix)
    full_losses = []
    zero_losses = []
    one_losses = []
    for block in blocks:
        future_rate = block.mean(axis=0)
        full_losses.append(
            float(np.abs(cumulative / history_count - future_rate).mean())
        )
        zero_losses.append(float(future_rate.mean()))
        one_losses.append(float((1.0 - future_rate).mean()))
        cumulative = cumulative + block.sum(axis=0)
        history_count += len(block)
    return (
        _mean(full_losses),
        _mean(zero_losses),
        _mean(one_losses),
    )


def _summarize_transfer_horizon(
    *,
    rows: Sequence[Mapping[str, Any]],
    repository_ids: Sequence[str],
    agent_ids: Sequence[str],
    audit_horizon: Mapping[str, Any],
    plan: Mapping[str, object],
    horizon: int,
) -> Mapping[str, Any]:
    algorithm_ids = (
        "ALG-016U",
        "full_history",
        "ordinary_recency",
        "unseen_full_response_assembly",
    )
    by_repository: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    by_agent: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_repository[_required_string(row, "repository_id")].append(row)
        by_agent[_required_string(row, "target_agent_id")].append(row)
    repository_rows = []
    for repository_id in repository_ids:
        source_rows = by_repository[repository_id]
        losses = {
            algorithm_id: _mean(
                [
                    _finite_number(
                        _mapping(row, "losses").get(algorithm_id),
                        f"{algorithm_id} loss",
                    )
                    for row in source_rows
                ]
            )
            for algorithm_id in algorithm_ids
        }
        repository_rows.append(
            {
                "repository_id": repository_id,
                **{f"{key}_mae": value for key, value in losses.items()},
                "candidate_minus_full": losses["ALG-016U"]
                - losses["full_history"],
                "candidate_minus_unseen_full_response_assembly": (
                    losses["ALG-016U"]
                    - losses["unseen_full_response_assembly"]
                ),
            }
        )
    macro = {
        algorithm_id: _mean(
            [row[f"{algorithm_id}_mae"] for row in repository_rows]
        )
        for algorithm_id in algorithm_ids
    }
    differences = tuple(
        float(row["candidate_minus_full"]) for row in repository_rows
    )
    uncertainty = _mapping(_mapping(plan, "suitability_audit"), "uncertainty")
    bootstrap = _bootstrap_interval(
        differences,
        resamples=_positive_integer(
            uncertainty,
            "repository_bootstrap_resamples",
        ),
        seed=_positive_integer(
            uncertainty,
            "h5_seed" if horizon == 5 else "h10_seed",
        ),
    )
    leave_one_repository_out = tuple(
        {
            "omitted_repository_id": repository_id,
            "candidate_minus_full": _mean(
                [
                    value
                    for offset, value in enumerate(differences)
                    if offset != index
                ]
            ),
        }
        for index, repository_id in enumerate(repository_ids)
    )
    target_agent_rows = []
    for agent_id in agent_ids:
        source_rows = by_agent[agent_id]
        repository_agent_differences = []
        for repository_id in repository_ids:
            repository_source = [
                row
                for row in source_rows
                if row["repository_id"] == repository_id
            ]
            repository_agent_differences.append(
                _mean(
                    [
                        _finite_number(
                            _mapping(row, "losses").get("ALG-016U"),
                            "candidate loss",
                        )
                        - _finite_number(
                            _mapping(row, "losses").get("full_history"),
                            "full loss",
                        )
                        for row in repository_source
                    ]
                )
            )
        target_agent_rows.append(
            {
                "target_agent_id": agent_id,
                "candidate_minus_full": _mean(repository_agent_differences),
            }
        )
    target_values = tuple(
        _finite_number(row.get("candidate_minus_full"), "target difference")
        for row in target_agent_rows
    )
    leave_one_target_out = tuple(
        {
            "omitted_target_agent_id": agent_id,
            "candidate_minus_full": _mean(
                [
                    value
                    for offset, value in enumerate(target_values)
                    if offset != index
                ]
            ),
        }
        for index, agent_id in enumerate(agent_ids)
    )
    candidate_difference = macro["ALG-016U"] - macro["full_history"]
    random_values = _number_tuple(
        _mapping(audit_horizon, "random_calibration").get(
            "macro_differences"
        ),
        "random macro differences",
    )
    better = sum(value > candidate_difference for value in random_values)
    equal = sum(value == candidate_difference for value in random_values)
    random_midrank = (better + 0.5 * equal) / len(random_values)
    candidate_minus_unseen = (
        macro["ALG-016U"] - macro["unseen_full_response_assembly"]
    )
    robust = (
        candidate_difference < 0.0
        and _finite_number(bootstrap.get("upper"), "bootstrap upper") < 0.0
        and sum(value < 0.0 for value in differences) >= 7
        and all(
            _finite_number(row.get("candidate_minus_full"), "LOO difference")
            < 0.0
            for row in leave_one_repository_out
        )
        and sum(value < 0.0 for value in target_values) >= 8
        and all(
            _finite_number(row.get("candidate_minus_full"), "Agent LOO difference")
            < 0.0
            for row in leave_one_target_out
        )
        and random_midrank >= 0.90
        and candidate_minus_unseen < 0.0
    )
    return {
        "horizon": horizon,
        "repository_count": len(repository_ids),
        "origin_count": sum(
            1
            for row in rows
            if row["target_agent_id"] == agent_ids[0]
        ),
        "target_agent_count": len(agent_ids),
        "mae": macro,
        "candidate_minus_full": candidate_difference,
        "candidate_minus_unseen_full_response_assembly": candidate_minus_unseen,
        "repository_bootstrap_interval_95": {
            "lower": bootstrap["lower"],
            "upper": bootstrap["upper"],
        },
        "favorable_repository_count": sum(value < 0.0 for value in differences),
        "leave_one_repository_out": leave_one_repository_out,
        "target_agent_rows": tuple(target_agent_rows),
        "favorable_target_agent_count": sum(value < 0.0 for value in target_values),
        "leave_one_target_agent_out": leave_one_target_out,
        "random_midrank": random_midrank,
        "practical_effect_at_least_0_005": candidate_difference <= -0.005,
        "robust_transfer_gate_passed": robust,
        "membership_rows_digest": canonical_digest(rows),
        "membership_rows": tuple(rows),
    }


def _origins_for_horizon(
    tasks: Sequence[TaskMetadata],
    plan: Mapping[str, object],
    horizon: int,
) -> tuple[Mapping[str, tuple[RepositoryOrigin, ...]], tuple[str, ...]]:
    frame = _mapping(plan, "frame")
    horizon_plan = _mapping(_mapping(frame, "horizons"), str(horizon))
    repository_ids = _unique_string_tuple(
        horizon_plan.get("repository_ids"),
        f"H{horizon} repository IDs",
    )
    all_origins = build_repository_origins(
        tasks,
        minimum_initial_history_tasks=_positive_integer(
            frame,
            "minimum_initial_history_tasks",
        ),
        future_block_tasks=horizon,
    )
    origins = {
        repository_id: all_origins[repository_id]
        for repository_id in repository_ids
    }
    expected_counts = _mapping(horizon_plan, "repository_origin_counts")
    actual_counts = {
        repository_id: len(origins[repository_id])
        for repository_id in repository_ids
    }
    if (
        actual_counts != expected_counts
        or sum(actual_counts.values())
        != _positive_integer(horizon_plan, "expected_origin_count")
    ):
        raise ValueError(f"H{horizon} Origin frame changed")
    return origins, repository_ids


def _verified_runtime(
    plan: Mapping[str, object],
) -> tuple[Any, Mapping[str, str]]:
    import numpy as np
    import pyarrow
    import scipy

    expected = _mapping(plan, "reproduction")
    versions = {
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "pyarrow_version": pyarrow.__version__,
    }
    if any(versions[key] != expected.get(key) for key in versions):
        raise ValueError(f"Full transfer runtime changed: {versions}")
    return np, versions


def _compact_audit_horizon(payload: Mapping[str, object]) -> Mapping[str, object]:
    return {
        key: payload.get(key)
        for key in (
            "repository_count",
            "origin_count",
            "largest_repository_origin_share",
            "joint_response_pattern_count",
            "future_outcome_cell_density",
            "always_zero_mae",
            "always_one_mae",
            "best_fixed_constant",
            "best_fixed_constant_mae",
            "full_history_mae",
            "random_mean_mae",
            "oracle_mae",
            "selection_headroom",
            "nontrivial_separation",
            "full_minus_best_fixed_constant_bootstrap_lower",
            "full_minus_best_fixed_constant_bootstrap_upper",
            "joint_block_order_null_probability",
            "joint_block_order_null_observed",
            "joint_block_order_null_mean",
        )
    }


def _compact_transfer_horizon(payload: object) -> Mapping[str, object]:
    row = _mapping_value(payload, "transfer horizon")
    return {
        key: row.get(key)
        for key in (
            "horizon",
            "repository_count",
            "origin_count",
            "target_agent_count",
            "mae",
            "candidate_minus_full",
            "candidate_minus_unseen_full_response_assembly",
            "repository_bootstrap_interval_95",
            "favorable_repository_count",
            "favorable_target_agent_count",
            "random_midrank",
            "practical_effect_at_least_0_005",
            "robust_transfer_gate_passed",
            "membership_rows_digest",
        )
    }


def _validate_audit_result(
    result: Mapping[str, object],
    plan: Mapping[str, object],
) -> None:
    payload = dict(result)
    digest = payload.pop("suitability_result_digest", None)
    if (
        payload.get("schema_version") != AUDIT_SCHEMA
        or payload.get("plan_digest") != plan.get("plan_digest")
        or digest != canonical_digest(payload)
    ):
        raise ValueError("Full suitability result is invalid")


def _validate_transfer_result(
    result: Mapping[str, object],
    plan: Mapping[str, object],
    audit_result: Mapping[str, object],
) -> None:
    payload = dict(result)
    digest = payload.pop("transfer_result_digest", None)
    if (
        payload.get("schema_version") != TRANSFER_SCHEMA
        or payload.get("plan_digest") != plan.get("plan_digest")
        or payload.get("suitability_result_digest")
        != audit_result.get("suitability_result_digest")
        or digest != canonical_digest(payload)
    ):
        raise ValueError("Full ALG-016U result is invalid")


def _load_result(path: Path, schema: str, digest_key: str) -> Mapping[str, Any]:
    payload = dict(_load_mapping(path))
    digest = payload.pop(digest_key, None)
    if payload.get("schema_version") != schema or digest != canonical_digest(payload):
        raise ValueError(f"result is invalid: {path}")
    payload[digest_key] = digest
    return payload


def _write_new_json(path: Path, payload: Mapping[str, object]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _distribution_summary(values: Sequence[float]) -> Mapping[str, float]:
    rows = tuple(values)
    if not rows:
        raise ValueError("distribution summary requires values")
    return {
        "minimum": min(rows),
        "median": statistics.median(rows),
        "maximum": max(rows),
    }


def _linear_quantile(ordered: Sequence[float], probability: float) -> float:
    if not ordered or not 0.0 <= probability <= 1.0:
        raise ValueError("quantile input is invalid")
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return float(ordered[lower] * (1.0 - weight) + ordered[upper] * weight)


def _mean(values: Sequence[float]) -> float:
    rows = tuple(values)
    if not rows:
        raise ValueError("mean requires values")
    return fsum(rows) / len(rows)


def _number_tuple(value: object, name: str) -> tuple[float, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or not value
    ):
        raise ValueError(f"{name} must be a nonempty number array")
    return tuple(_finite_number(item, name) for item in value)


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _required_row_string(row: Mapping[str, object], key: str) -> str:
    return _required_string(row, key)


def _required_string(value: Mapping[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a nonempty string")
    return item


def _integer(value: Mapping[str, object], key: str) -> int:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int):
        raise ValueError(f"{key} must be an integer")
    return item


def _positive_integer(value: Mapping[str, object], key: str) -> int:
    item = _integer(value, key)
    if item <= 0:
        raise ValueError(f"{key} must be positive")
    return item


def _mapping(value: Mapping[str, object], key: str) -> Mapping[str, Any]:
    return _mapping_value(value.get(key), key)


def _mapping_value(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _mapping_sequence(
    value: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, Any], ...]:
    item = value.get(key)
    if (
        not isinstance(item, Sequence)
        or isinstance(item, str)
        or any(not isinstance(row, Mapping) for row in item)
    ):
        raise ValueError(f"{key} must be an array of objects")
    return tuple(item)


def _unique_string_tuple(value: object, name: str) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{name} must be an array of nonempty strings")
    result = tuple(value)
    if len(result) != len(set(result)):
        raise ValueError(f"{name} contains duplicate IDs")
    return result


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON must contain an object: {path}")
    return payload


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser("fetch")
    fetch.add_argument("--result-dir", type=Path, default=DEFAULT_RESULT_DIRECTORY)

    audit = subparsers.add_parser("audit")
    audit.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    audit.add_argument("--result-dir", type=Path, default=DEFAULT_RESULT_DIRECTORY)
    audit.add_argument("--output", type=Path, required=True)

    transfer = subparsers.add_parser("transfer")
    transfer.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    transfer.add_argument("--result-dir", type=Path, default=DEFAULT_RESULT_DIRECTORY)
    transfer.add_argument("--audit", type=Path, required=True)
    transfer.add_argument("--output", type=Path, required=True)

    summary = subparsers.add_parser("summary")
    summary.add_argument("--audit", type=Path, required=True)
    summary.add_argument("--audit-reproduction", type=Path, required=True)
    summary.add_argument("--transfer", type=Path)
    summary.add_argument("--transfer-reproduction", type=Path)
    summary.add_argument("--output", type=Path, default=DEFAULT_SUMMARY)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--audit", type=Path)
    verify.add_argument("--transfer", type=Path)
    verify.add_argument("--summary", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    plan = load_plan(args.plan)
    if args.command == "fetch":
        manifests = fetch_official_results(plan, args.result_dir)
        print(json.dumps(manifests, sort_keys=True))
        return 0
    if args.command in {"audit", "transfer"}:
        (
            tasks,
            outcomes,
            diagnostics,
            metadata,
            identities,
        ) = load_full_inputs(
            plan=plan,
            dataset_path=args.dataset,
            result_directory=args.result_dir,
        )
        if args.command == "audit":
            result = run_suitability_audit(
                tasks,
                outcomes,
                diagnostics,
                metadata,
                identities,
                plan,
            )
        else:
            audit_result = _load_result(
                args.audit,
                AUDIT_SCHEMA,
                "suitability_result_digest",
            )
            result = run_alg_016u_transfer(
                tasks,
                outcomes,
                identities,
                audit_result,
                plan,
            )
        _write_new_json(args.output, result)
        print(json.dumps(result["decision"], sort_keys=True))
        return 0
    if args.command == "summary":
        audit_result = _load_result(
            args.audit,
            AUDIT_SCHEMA,
            "suitability_result_digest",
        )
        audit_reproduction = _load_result(
            args.audit_reproduction,
            AUDIT_SCHEMA,
            "suitability_result_digest",
        )
        transfer_result = (
            _load_result(args.transfer, TRANSFER_SCHEMA, "transfer_result_digest")
            if args.transfer
            else None
        )
        transfer_reproduction = (
            _load_result(
                args.transfer_reproduction,
                TRANSFER_SCHEMA,
                "transfer_result_digest",
            )
            if args.transfer_reproduction
            else None
        )
        summary = build_compact_summary(
            plan=plan,
            audit_result=audit_result,
            audit_reproduction=audit_reproduction,
            transfer_result=transfer_result,
            transfer_reproduction=transfer_reproduction,
        )
        _write_new_json(args.output, summary)
        print(json.dumps(summary, sort_keys=True))
        return 0
    if args.command == "verify":
        if args.audit:
            audit_result = _load_result(
                args.audit,
                AUDIT_SCHEMA,
                "suitability_result_digest",
            )
            _validate_audit_result(audit_result, plan)
        else:
            audit_result = None
        if args.transfer:
            if audit_result is None:
                raise ValueError("--transfer verification requires --audit")
            transfer_result = _load_result(
                args.transfer,
                TRANSFER_SCHEMA,
                "transfer_result_digest",
            )
            _validate_transfer_result(transfer_result, plan, audit_result)
        if args.summary:
            summary = _load_result(args.summary, SUMMARY_SCHEMA, "summary_digest")
            if _mapping(summary, "identities").get("plan_digest") != plan.get(
                "plan_digest"
            ):
                raise ValueError("summary plan binding changed")
        print(json.dumps({"verified": True, "plan_digest": plan["plan_digest"]}))
        return 0
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())
