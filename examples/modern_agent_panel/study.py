#!/usr/bin/env python3
"""Refresh Barcarolle's public Agent research population."""

from __future__ import annotations

# The reproduction command supplies NumPy, SciPy, and PyArrow.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
import hashlib
import json
from math import fsum, isfinite
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence
from urllib.request import Request, urlopen


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.multi_repository_study.public_replay import (  # noqa: E402
    RepositoryOrigin,
    TaskMetadata,
    build_repository_origins,
)
from examples.swe_bench_full_development.diagnostic import (  # noqa: E402
    select_future_oracle_memberships,
)
from examples.swe_bench_full_transfer.study import (  # noqa: E402
    CURRENT_RESULT_FIELDS,
    LEGACY_RESULT_FIELDS,
    normalize_official_result,
)


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "plan.json"
DEFAULT_SUMMARY = HERE / "evidence" / "summary.json"
DEFAULT_OUTPUT_DIRECTORY = (
    REPOSITORY_ROOT / "outputs" / "research" / "2026-07-31-modern-agent-panel"
)
DEFAULT_RESULT_A = DEFAULT_OUTPUT_DIRECTORY / "result-a.json"
DEFAULT_RESULT_B = DEFAULT_OUTPUT_DIRECTORY / "result-b.json"

PLAN_SCHEMA = "barcarolle_modern_agent_panel_plan_v1"
RESULT_SCHEMA = "barcarolle_modern_agent_panel_result_v1"
SUMMARY_SCHEMA = "barcarolle_modern_agent_panel_summary_v1"


def load_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    """Load the frozen source and measurement contract."""
    payload = dict(_load_mapping(path))
    digest = payload.pop("plan_digest", None)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("modern Agent panel plan schema is unsupported")
    if digest != canonical_digest(payload):
        raise ValueError("modern Agent panel plan digest does not match")
    payload["plan_digest"] = digest

    authority = _mapping(payload, "authority")
    for key in (
        "paid_api_calls",
        "new_agent_runs",
        "sealed_verified_full_system_agents_opened",
        "selector_changes",
        "core_schema_changes",
    ):
        if authority.get(key) != 0:
            raise ValueError("modern Agent panel authority changed")
    if authority.get("generator_development") is not False:
        raise ValueError("modern Agent panel Generator boundary changed")

    frame = _mapping(payload, "frame")
    if (
        _positive_integer(frame, "minimum_initial_history_tasks") != 20
        or _positive_integer(frame, "selection_budget_tasks") != 10
        or frame.get("horizons") != [5, 10]
    ):
        raise ValueError("modern Agent panel frame changed")
    return payload


def select_fixed_harness_rows(
    leaderboard_payload: Mapping[str, object],
    *,
    leaderboard_name: str,
    folders: Sequence[str],
    version: str,
    task_ids: Sequence[str],
) -> tuple[Mapping[str, object], ...]:
    """Select exact complete same-harness rows without score filtering."""
    denominator = _unique_strings(task_ids, "Task denominator")
    denominator_set = set(denominator)
    folder_allowlist = _unique_strings(folders, "Agent folders")
    leaderboards = _mapping_sequence(leaderboard_payload, "leaderboards")
    matches = [row for row in leaderboards if row.get("name") == leaderboard_name]
    if len(matches) != 1:
        raise ValueError("leaderboard identity is ambiguous")
    results = _mapping_sequence(matches[0], "results")
    by_folder: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in results:
        folder = row.get("folder")
        if isinstance(folder, str) and folder:
            by_folder[folder].append(row)

    discovered_complete = set()
    selected = []
    for folder, rows in sorted(by_folder.items()):
        complete = []
        for row in rows:
            if row.get("mini-swe-agent_version") != version:
                continue
            details = row.get("per_instance_details")
            if not isinstance(details, Mapping):
                continue
            if set(details) != denominator_set:
                continue
            complete.append(row)
        if complete:
            discovered_complete.add(folder)
        if folder not in folder_allowlist:
            continue
        if len(complete) != 1:
            raise ValueError(f"expected one complete fixed-harness row: {folder}")
        selected.append(complete[0])

    if discovered_complete != set(folder_allowlist):
        raise ValueError("fixed-harness complete cohort changed")
    if len(selected) != len(folder_allowlist):
        raise ValueError("fixed-harness Agent count changed")
    return tuple(sorted(selected, key=lambda row: str(row["folder"])))


def normalize_fixed_harness_outcomes(
    rows: Sequence[Mapping[str, object]],
    task_ids: Sequence[str],
) -> tuple[
    Mapping[str, Mapping[str, int]],
    Mapping[str, Mapping[str, object]],
]:
    """Normalize leaderboard per-instance details to exact binary outcomes."""
    denominator = _unique_strings(task_ids, "Task denominator")
    denominator_set = set(denominator)
    outcomes = {}
    metadata = {}
    for row in rows:
        folder = _required_string(row, "folder")
        details = _mapping(row, "per_instance_details")
        if set(details) != denominator_set:
            raise ValueError(f"fixed-harness Task denominator changed: {folder}")
        normalized = {}
        for task_id in denominator:
            detail = details[task_id]
            if not isinstance(detail, Mapping):
                raise ValueError("per-instance detail must be an object")
            resolved = detail.get("resolved")
            if not isinstance(resolved, bool):
                raise ValueError("per-instance resolved must be boolean")
            normalized[task_id] = int(resolved)
        aggregate = row.get("resolved")
        if (
            isinstance(aggregate, bool)
            or not isinstance(aggregate, (int, float))
            or not isfinite(float(aggregate))
            or abs(float(aggregate) - 100.0 * _mean(normalized.values())) > 1e-9
        ):
            raise ValueError("leaderboard aggregate disagrees with outcomes")
        if folder in outcomes:
            raise ValueError("duplicate fixed-harness Agent identity")
        outcomes[folder] = normalized
        metadata[folder] = {
            "agent_id": folder,
            "name": _required_string(row, "name"),
            "date": _required_string(row, "date"),
            "mini_swe_agent_version": _required_string(
                row,
                "mini-swe-agent_version",
            ),
            "reported_pass_rate": float(aggregate) / 100.0,
        }
    return dict(sorted(outcomes.items())), dict(sorted(metadata.items()))


def fetch_sources(
    plan: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    """Fetch only the public source blobs frozen in the plan."""
    manifests = []
    primary = _mapping(plan, "primary_lane")
    source = _mapping(primary, "result_source")
    revision = _required_string(source, "revision")
    source_path = _required_string(source, "path")
    local_path = REPOSITORY_ROOT / _required_string(source, "local_path")
    url = (
        "https://raw.githubusercontent.com/"
        f"{_required_string(source, 'repository')}/{revision}/{source_path}"
    )
    raw = _fetch_exact(
        url,
        local_path,
        expected_size=_positive_integer(source, "size_bytes"),
        expected_sha256=_required_string(source, "sha256"),
        expected_git_blob=_required_string(source, "git_blob_sha"),
    )
    manifests.append(
        {
            "lane_id": primary.get("lane_id"),
            "path": str(local_path.relative_to(REPOSITORY_ROOT)),
            "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "git_blob_sha": _git_blob_sha(raw),
        }
    )

    secondary = _mapping(plan, "secondary_lane")
    result_source = _mapping(secondary, "result_source")
    result_revision = _required_string(result_source, "revision")
    result_repository = _required_string(result_source, "repository")
    result_directory = _required_string(result_source, "directory")
    local_directory = REPOSITORY_ROOT / _required_string(
        result_source, "local_directory"
    )
    for agent in _mapping_sequence(secondary, "agents"):
        submission = _required_string(agent, "submission")
        path = local_directory / f"{submission}.json"
        result_url = (
            "https://raw.githubusercontent.com/"
            f"{result_repository}/{result_revision}/{result_directory}/"
            f"{submission}/results/results.json"
        )
        result_raw = _fetch_exact(
            result_url,
            path,
            expected_size=_positive_integer(agent, "result_size_bytes"),
            expected_sha256=_required_string(agent, "result_sha256"),
            expected_git_blob=_required_string(agent, "result_blob_sha"),
        )
        manifests.append(
            {
                "lane_id": secondary.get("lane_id"),
                "agent_id": agent.get("agent_id"),
                "path": str(path.relative_to(REPOSITORY_ROOT)),
                "size_bytes": len(result_raw),
                "sha256": hashlib.sha256(result_raw).hexdigest(),
                "git_blob_sha": _git_blob_sha(result_raw),
            }
        )
    return tuple(manifests)


def load_inputs(
    plan: Mapping[str, object],
) -> tuple[
    tuple[
        str,
        tuple[TaskMetadata, ...],
        Mapping[str, Mapping[str, int]],
        Mapping[str, Mapping[str, object]],
        Mapping[str, object],
    ],
    ...,
]:
    """Load and normalize both exact public lanes."""
    primary = _mapping(plan, "primary_lane")
    primary_source = _mapping(primary, "task_source")
    primary_tasks = _load_tasks(
        REPOSITORY_ROOT / _required_string(primary_source, "local_path"),
        expected_sha256=_required_string(primary_source, "sha256"),
        expected_count=_positive_integer(primary_source, "task_count"),
    )
    primary_task_ids = tuple(task.instance_id for task in primary_tasks)
    leaderboard_source = _mapping(primary, "result_source")
    leaderboard_path = REPOSITORY_ROOT / _required_string(
        leaderboard_source, "local_path"
    )
    _require_file_identity(
        leaderboard_path,
        expected_size=_positive_integer(leaderboard_source, "size_bytes"),
        expected_sha256=_required_string(leaderboard_source, "sha256"),
        expected_git_blob=_required_string(
            leaderboard_source,
            "git_blob_sha",
        ),
    )
    leaderboard = _load_mapping(leaderboard_path)
    cohort = _mapping(primary, "cohort_rule")
    primary_rows = select_fixed_harness_rows(
        leaderboard,
        leaderboard_name=_required_string(
            leaderboard_source,
            "leaderboard_name",
        ),
        folders=_string_sequence(primary.get("folders"), "Agent folders"),
        version=_required_string(cohort, "mini_swe_agent_version"),
        task_ids=primary_task_ids,
    )
    primary_outcomes, primary_metadata = normalize_fixed_harness_outcomes(
        primary_rows,
        primary_task_ids,
    )
    if len(primary_outcomes) != _positive_integer(
        cohort,
        "expected_agent_count",
    ):
        raise ValueError("fixed-harness normalized Agent count changed")
    primary_identities = {
        "dataset_sha256": _file_sha256(
            REPOSITORY_ROOT / _required_string(primary_source, "local_path")
        ),
        "result_source_sha256": _file_sha256(leaderboard_path),
        "agent_ids": tuple(sorted(primary_outcomes)),
        "outcome_matrix_digest": canonical_digest(primary_outcomes),
    }

    secondary = _mapping(plan, "secondary_lane")
    secondary_source = _mapping(secondary, "task_source")
    secondary_tasks = _load_tasks(
        REPOSITORY_ROOT / _required_string(secondary_source, "local_path"),
        expected_sha256=_required_string(secondary_source, "sha256"),
        expected_count=_positive_integer(secondary_source, "task_count"),
    )
    secondary_task_ids = tuple(task.instance_id for task in secondary_tasks)
    result_source = _mapping(secondary, "result_source")
    local_directory = REPOSITORY_ROOT / _required_string(
        result_source, "local_directory"
    )
    secondary_outcomes = {}
    secondary_metadata = {}
    result_identities = []
    for agent in _mapping_sequence(secondary, "agents"):
        agent_id = _required_string(agent, "agent_id")
        submission = _required_string(agent, "submission")
        path = local_directory / f"{submission}.json"
        _require_file_identity(
            path,
            expected_size=_positive_integer(agent, "result_size_bytes"),
            expected_sha256=_required_string(agent, "result_sha256"),
            expected_git_blob=_required_string(agent, "result_blob_sha"),
        )
        payload = _load_mapping(path)
        fields = frozenset(payload)
        schema = (
            "current"
            if fields == CURRENT_RESULT_FIELDS
            else "legacy"
            if fields == LEGACY_RESULT_FIELDS
            else None
        )
        if schema is None:
            raise ValueError(f"unsupported Full result schema: {submission}")
        normalized, diagnostics = normalize_official_result(
            secondary_task_ids,
            payload,
            schema=schema,
        )
        secondary_outcomes[agent_id] = normalized
        secondary_metadata[agent_id] = {
            "agent_id": agent_id,
            "submission": submission,
            "model_label": _required_string(agent, "model_label"),
            "harness_label": _required_string(agent, "harness_label"),
            "attempts": _required_string(agent, "attempts"),
            "checked": agent.get("checked"),
            "normalization": diagnostics,
        }
        result_identities.append(
            {
                "agent_id": agent_id,
                "result_sha256": _file_sha256(path),
                "result_blob_sha": _git_blob_sha(path.read_bytes()),
            }
        )
    secondary_outcomes = dict(sorted(secondary_outcomes.items()))
    secondary_identities = {
        "dataset_sha256": _file_sha256(
            REPOSITORY_ROOT / _required_string(secondary_source, "local_path")
        ),
        "agent_ids": tuple(sorted(secondary_outcomes)),
        "result_identities": tuple(result_identities),
        "outcome_matrix_digest": canonical_digest(secondary_outcomes),
    }
    return (
        (
            _required_string(primary, "lane_id"),
            primary_tasks,
            primary_outcomes,
            primary_metadata,
            primary_identities,
        ),
        (
            _required_string(secondary, "lane_id"),
            secondary_tasks,
            secondary_outcomes,
            dict(sorted(secondary_metadata.items())),
            secondary_identities,
        ),
    )


def run_study(
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Run the frozen candidate-free direct-MAE diagnostics."""
    import numpy as np
    import pyarrow
    import scipy

    reproduction = _mapping(plan, "reproduction")
    if (
        sys.version.split()[0] != _required_string(reproduction, "python_version")
        or np.__version__ != _required_string(reproduction, "numpy_version")
        or scipy.__version__ != _required_string(reproduction, "scipy_version")
        or pyarrow.__version__ != _required_string(reproduction, "pyarrow_version")
    ):
        raise ValueError("modern Agent panel runtime changed")

    lane_results = {}
    for lane_offset, (
        lane_id,
        tasks,
        outcomes,
        metadata,
        identities,
    ) in enumerate(load_inputs(plan)):
        lane_results[lane_id] = _evaluate_lane(
            np=np,
            lane_id=lane_id,
            tasks=tasks,
            outcomes_by_agent=outcomes,
            metadata_by_agent=metadata,
            identities=identities,
            plan=plan,
            random_seed_offset=lane_offset * 1000,
        )

    primary_id = _required_string(_mapping(plan, "primary_lane"), "lane_id")
    primary = _mapping(lane_results, primary_id)
    horizon_rows = _mapping(primary, "horizons")
    ready = all(
        bool(_mapping(horizon_rows, str(horizon)).get("nontrivial_capacity"))
        for horizon in (5, 10)
    )
    reference_transport = all(
        _finite_number(
            _mapping(
                _mapping(horizon_rows, str(horizon)),
                "controls",
            ).get("reference_future_oracle_mae"),
            "reference Oracle MAE",
        )
        < _finite_number(
            _mapping(
                _mapping(horizon_rows, str(horizon)),
                "controls",
            ).get("full_history_mae"),
            "Full MAE",
        )
        for horizon in (5, 10)
    )
    terminal_state = (
        "modern_fixed_harness_panel_ready_for_outcome_open_algorithm_research"
        if ready
        else "modern_panel_trivial_or_capacity_limited"
    )
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "epistemic_status": plan.get("epistemic_status"),
        "lanes": lane_results,
        "decision": {
            "terminal_state": terminal_state,
            "primary_nontrivial_capacity_at_both_horizons": ready,
            "primary_reference_transport_at_both_horizons": (reference_transport),
            "selector_nominated": False,
            "production_promotion_allowed": False,
        },
        "implementation": {
            "study_file_sha256": _file_sha256(Path(__file__)),
        },
        "resource_use": {
            "paid_api_calls": 0,
            "new_agent_runs": 0,
            "sealed_verified_full_system_agents_opened": 0,
        },
        "claim_boundary": plan.get("claim_boundary"),
    }
    result["result_digest"] = canonical_digest(result)
    return result


def _evaluate_lane(
    *,
    np: Any,
    lane_id: str,
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    metadata_by_agent: Mapping[str, Mapping[str, object]],
    identities: Mapping[str, object],
    plan: Mapping[str, object],
    random_seed_offset: int,
) -> Mapping[str, Any]:
    agent_ids = tuple(sorted(outcomes_by_agent))
    task_ids = tuple(task.instance_id for task in tasks)
    if len(agent_ids) < 2 or set(metadata_by_agent) != set(agent_ids):
        raise ValueError("Agent panel metadata changed")
    if any(set(outcomes_by_agent[agent]) != set(task_ids) for agent in agent_ids):
        raise ValueError("Agent outcome denominator changed")

    tasks_by_repository: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        tasks_by_repository[task.repository_id].append(task.instance_id)
    per_agent_pass_rate = {
        agent_id: _mean(outcomes_by_agent[agent_id].values()) for agent_id in agent_ids
    }
    response_patterns = tuple(
        tuple(outcomes_by_agent[agent_id][task_id] for agent_id in agent_ids)
        for task_id in task_ids
    )
    pairwise_disagreements = []
    exact_duplicate_pairs = 0
    for left_index, left_agent in enumerate(agent_ids):
        for right_agent in agent_ids[left_index + 1 :]:
            disagreement = _mean(
                outcomes_by_agent[left_agent][task_id]
                != outcomes_by_agent[right_agent][task_id]
                for task_id in task_ids
            )
            pairwise_disagreements.append(disagreement)
            exact_duplicate_pairs += disagreement == 0.0
    repository_rates = []
    for repository_id, repository_task_ids in sorted(tasks_by_repository.items()):
        rates = {
            agent_id: _mean(
                outcomes_by_agent[agent_id][task_id] for task_id in repository_task_ids
            )
            for agent_id in agent_ids
        }
        repository_rates.append(
            {
                "repository_id": repository_id,
                "task_count": len(repository_task_ids),
                "panel_mean_pass_rate": _mean(rates.values()),
                "minimum_agent_pass_rate": min(rates.values()),
                "maximum_agent_pass_rate": max(rates.values()),
            }
        )

    frame = _mapping(plan, "frame")
    expected_by_lane = _mapping(_mapping(frame, "expected"), lane_id)
    horizons = {}
    for horizon in (5, 10):
        origins_all = build_repository_origins(
            tasks,
            minimum_initial_history_tasks=_positive_integer(
                frame,
                "minimum_initial_history_tasks",
            ),
            future_block_tasks=horizon,
        )
        origins_by_repository = {
            repository_id: origins
            for repository_id, origins in sorted(origins_all.items())
            if origins
        }
        expected = _mapping(expected_by_lane, str(horizon))
        if len(origins_by_repository) != _positive_integer(
            expected, "repository_count"
        ) or sum(map(len, origins_by_repository.values())) != _positive_integer(
            expected, "origin_count"
        ):
            raise ValueError(f"{lane_id} H{horizon} Origin frame changed")
        horizons[str(horizon)] = _evaluate_horizon(
            np=np,
            lane_id=lane_id,
            horizon=horizon,
            origins_by_repository=origins_by_repository,
            outcomes_by_agent=outcomes_by_agent,
            agent_ids=agent_ids,
            budget=_positive_integer(frame, "selection_budget_tasks"),
            random_draws=_positive_integer(
                _mapping(plan, "diagnostics"),
                "random_draws",
            ),
            random_seed=(
                _positive_integer(
                    _mapping(plan, "diagnostics"),
                    "random_seed",
                )
                + random_seed_offset
                + horizon
            ),
        )

    return {
        "lane_id": lane_id,
        "task_count": len(tasks),
        "agent_count": len(agent_ids),
        "identities": dict(identities),
        "pass_rates": {
            "panel_pooled": _mean(per_agent_pass_rate.values()),
            "minimum_agent": min(per_agent_pass_rate.values()),
            "maximum_agent": max(per_agent_pass_rate.values()),
            "by_agent": {
                agent_id: {
                    **dict(metadata_by_agent[agent_id]),
                    "pass_rate": per_agent_pass_rate[agent_id],
                }
                for agent_id in agent_ids
            },
            "by_repository": tuple(repository_rates),
        },
        "response_geometry": {
            "unique_response_pattern_count": len(set(response_patterns)),
            "unanimous_fail_task_share": _mean(
                sum(pattern) == 0 for pattern in response_patterns
            ),
            "unanimous_pass_task_share": _mean(
                sum(pattern) == len(agent_ids) for pattern in response_patterns
            ),
            "pairwise_disagreement": {
                "pair_count": len(pairwise_disagreements),
                "minimum": min(pairwise_disagreements),
                "mean": _mean(pairwise_disagreements),
                "maximum": max(pairwise_disagreements),
                "exact_duplicate_pair_count": exact_duplicate_pairs,
            },
        },
        "horizons": horizons,
    }


def _evaluate_horizon(
    *,
    np: Any,
    lane_id: str,
    horizon: int,
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    agent_ids: Sequence[str],
    budget: int,
    random_draws: int,
    random_seed: int,
) -> Mapping[str, Any]:
    algorithm_ids = (
        "always_zero",
        "always_one",
        "full_history",
        "reference_future_oracle",
        "target_future_oracle",
    )
    repository_losses: dict[str, dict[str, list[float]]] = {}
    agent_repository_losses: dict[
        tuple[str, str],
        dict[str, list[float]],
    ] = {}
    future_positive_cells = 0
    future_cells = 0
    all_zero_blocks = 0
    all_one_blocks = 0
    for position, (repository_id, origins) in enumerate(
        origins_by_repository.items(),
        start=1,
    ):
        repository_losses[repository_id] = {
            algorithm_id: [] for algorithm_id in algorithm_ids
        }
        for agent_id in agent_ids:
            agent_repository_losses[(agent_id, repository_id)] = {
                algorithm_id: [] for algorithm_id in algorithm_ids
            }
        for origin in origins:
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
            memberships = select_future_oracle_memberships(
                history,
                future,
                budget=budget,
                created_order=tuple(
                    (task.created_at, task.instance_id) for task in origin.history
                ),
            )
            future_rates = future.mean(axis=0)
            future_positive_cells += int(future.sum())
            future_cells += int(future.size)
            all_zero_blocks += int((future.sum(axis=0) == 0).sum())
            all_one_blocks += int((future.sum(axis=0) == len(origin.future)).sum())
            for held_out, agent_id in enumerate(agent_ids):
                losses = {
                    "always_zero": float(future_rates[held_out]),
                    "always_one": float(1.0 - future_rates[held_out]),
                    "full_history": float(
                        abs(history[:, held_out].mean() - future_rates[held_out])
                    ),
                }
                for oracle_id, indices in memberships[held_out].items():
                    losses[oracle_id] = float(
                        abs(
                            history[list(indices), held_out].mean()
                            - future_rates[held_out]
                        )
                    )
                for algorithm_id, loss in losses.items():
                    repository_losses[repository_id][algorithm_id].append(loss)
                    agent_repository_losses[(agent_id, repository_id)][
                        algorithm_id
                    ].append(loss)
        print(
            f"{lane_id} H{horizon} repository "
            f"{position}/{len(origins_by_repository)} {repository_id}",
            flush=True,
        )

    repository_rows = []
    for repository_id in origins_by_repository:
        mae = {
            algorithm_id: _mean(repository_losses[repository_id][algorithm_id])
            for algorithm_id in algorithm_ids
        }
        repository_rows.append(
            {
                "repository_id": repository_id,
                "origin_count": len(origins_by_repository[repository_id]),
                "mae": mae,
                "oracle_minus_full": {
                    oracle_id: mae[oracle_id] - mae["full_history"]
                    for oracle_id in (
                        "reference_future_oracle",
                        "target_future_oracle",
                    )
                },
            }
        )
    macro = {
        algorithm_id: _mean(
            _mapping(row, "mae")[algorithm_id] for row in repository_rows
        )
        for algorithm_id in algorithm_ids
    }
    agent_rows = []
    for agent_id in agent_ids:
        agent_macro = {
            algorithm_id: _mean(
                _mean(agent_repository_losses[(agent_id, repository_id)][algorithm_id])
                for repository_id in origins_by_repository
            )
            for algorithm_id in algorithm_ids
        }
        agent_rows.append(
            {
                "agent_id": agent_id,
                "mae": agent_macro,
                "oracle_minus_full": {
                    oracle_id: (agent_macro[oracle_id] - agent_macro["full_history"])
                    for oracle_id in (
                        "reference_future_oracle",
                        "target_future_oracle",
                    )
                },
            }
        )

    random = _random_calibration(
        np=np,
        origins_by_repository=origins_by_repository,
        outcomes_by_agent=outcomes_by_agent,
        agent_ids=agent_ids,
        budget=budget,
        draws=random_draws,
        seed=random_seed,
    )
    controls = {
        f"{algorithm_id}_mae": macro[algorithm_id] for algorithm_id in algorithm_ids
    }
    controls.update(
        {
            "random_mean_mae": (
                macro["full_history"]
                + _finite_number(
                    random.get("mean_macro_repository_difference"),
                    "random mean difference",
                )
            ),
            "reference_selection_headroom": (
                macro["full_history"] - macro["reference_future_oracle"]
            ),
            "target_selection_headroom": (
                macro["full_history"] - macro["target_future_oracle"]
            ),
        }
    )
    nontrivial_capacity = (
        macro["full_history"] < macro["always_zero"]
        and macro["full_history"] < macro["always_one"]
        and macro["target_future_oracle"] < macro["full_history"]
    )
    return {
        "frame": {
            "horizon": horizon,
            "repository_count": len(origins_by_repository),
            "origin_count": sum(map(len, origins_by_repository.values())),
            "repository_ids": tuple(origins_by_repository),
            "selection_budget_tasks": budget,
        },
        "prevalence": {
            "future_outcome_density": future_positive_cells / future_cells,
            "all_zero_agent_origin_share": (
                all_zero_blocks
                / (len(agent_ids) * sum(map(len, origins_by_repository.values())))
            ),
            "all_one_agent_origin_share": (
                all_one_blocks
                / (len(agent_ids) * sum(map(len, origins_by_repository.values())))
            ),
        },
        "controls": controls,
        "random_calibration": random,
        "repository_rows": tuple(repository_rows),
        "agent_rows": tuple(agent_rows),
        "oracle_directions": {
            oracle_id: {
                "favorable_repositories": sum(
                    _finite_number(
                        _mapping(row, "oracle_minus_full").get(oracle_id),
                        "repository Oracle difference",
                    )
                    < 0.0
                    for row in repository_rows
                ),
                "repository_count": len(repository_rows),
                "favorable_agents": sum(
                    _finite_number(
                        _mapping(row, "oracle_minus_full").get(oracle_id),
                        "Agent Oracle difference",
                    )
                    < 0.0
                    for row in agent_rows
                ),
                "agent_count": len(agent_rows),
            }
            for oracle_id in (
                "reference_future_oracle",
                "target_future_oracle",
            )
        },
        "nontrivial_capacity": nontrivial_capacity,
    }


def _random_calibration(
    *,
    np: Any,
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
    for repository_id, origins in origins_by_repository.items():
        repository_differences = np.zeros(draws, dtype=np.float64)
        for origin in origins:
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
            future_rate = np.asarray(
                [
                    [
                        outcomes_by_agent[agent_id][task.instance_id]
                        for agent_id in agent_ids
                    ]
                    for task in origin.future
                ],
                dtype=np.float64,
            ).mean(axis=0)
            baseline = float(np.abs(history.mean(axis=0) - future_rate).mean())
            for start in range(0, draws, batch_size):
                stop = min(start + batch_size, draws)
                keys = generator.random((stop - start, len(history)))
                indices = np.argpartition(
                    keys,
                    budget - 1,
                    axis=1,
                )[:, :budget]
                selected_rates = history[indices].mean(axis=1)
                losses = np.abs(selected_rates - future_rate).mean(axis=1)
                repository_differences[start:stop] += losses - baseline
        repository_differences /= len(origins)
        macro_differences += repository_differences
    macro_differences /= len(origins_by_repository)
    values = tuple(float(value) for value in macro_differences)
    ordered = tuple(sorted(values))
    standard_deviation = float(np.std(macro_differences))
    return {
        "draws": draws,
        "seed": seed,
        "mean_macro_repository_difference": _mean(values),
        "random_as_good_or_better_than_full_share": (
            sum(value <= 0.0 for value in values) / draws
        ),
        "population_standard_deviation": standard_deviation,
        "mean_monte_carlo_standard_error": standard_deviation / draws**0.5,
        "quantiles": {
            "0.025": _quantile(ordered, 0.025),
            "0.5": _quantile(ordered, 0.5),
            "0.975": _quantile(ordered, 0.975),
        },
        "macro_differences_digest": canonical_digest(values),
    }


def build_summary(
    result_a: Mapping[str, object],
    result_b: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Commit only identical compact evidence."""
    _validate_result(result_a, plan)
    _validate_result(result_b, plan)
    if canonical_json(result_a) != canonical_json(result_b):
        raise ValueError("modern Agent panel reproduction differs")
    summary: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "reproduction": {
            "byte_identical_second_run": True,
            "result_digest": result_a.get("result_digest"),
        },
        "lanes": dict(_mapping(result_a, "lanes")),
        "decision": dict(_mapping(result_a, "decision")),
        "implementation": dict(_mapping(result_a, "implementation")),
        "resource_use": dict(_mapping(result_a, "resource_use")),
        "claim_boundary": result_a.get("claim_boundary"),
    }
    summary["summary_digest"] = canonical_digest(summary)
    return summary


def _validate_result(
    result: Mapping[str, object],
    plan: Mapping[str, object],
) -> None:
    body = {key: value for key, value in result.items() if key != "result_digest"}
    if (
        result.get("schema_version") != RESULT_SCHEMA
        or result.get("plan_digest") != plan.get("plan_digest")
        or result.get("result_digest") != canonical_digest(body)
    ):
        raise ValueError("modern Agent panel result is invalid")


def validate_summary(
    summary: Mapping[str, object],
    plan: Mapping[str, object],
) -> None:
    body = {key: value for key, value in summary.items() if key != "summary_digest"}
    if (
        summary.get("schema_version") != SUMMARY_SCHEMA
        or summary.get("plan_digest") != plan.get("plan_digest")
        or summary.get("summary_digest") != canonical_digest(body)
        or _mapping(summary, "implementation").get("study_file_sha256")
        != _file_sha256(Path(__file__))
    ):
        raise ValueError("modern Agent panel summary is invalid")


def _fetch_exact(
    url: str,
    path: Path,
    *,
    expected_size: int,
    expected_sha256: str,
    expected_git_blob: str,
) -> bytes:
    if path.exists():
        raw = path.read_bytes()
    else:
        request = Request(url, headers={"User-Agent": "barcarolle-research"})
        with urlopen(request, timeout=120) as response:
            raw = response.read()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    _check_raw_identity(
        raw,
        expected_size=expected_size,
        expected_sha256=expected_sha256,
        expected_git_blob=expected_git_blob,
    )
    return raw


def _require_file_identity(
    path: Path,
    *,
    expected_size: int,
    expected_sha256: str,
    expected_git_blob: str,
) -> None:
    _check_raw_identity(
        path.read_bytes(),
        expected_size=expected_size,
        expected_sha256=expected_sha256,
        expected_git_blob=expected_git_blob,
    )


def _check_raw_identity(
    raw: bytes,
    *,
    expected_size: int,
    expected_sha256: str,
    expected_git_blob: str,
) -> None:
    if (
        len(raw) != expected_size
        or hashlib.sha256(raw).hexdigest() != expected_sha256
        or _git_blob_sha(raw) != expected_git_blob
    ):
        raise ValueError("public source identity changed")


def _load_tasks(
    path: Path,
    *,
    expected_sha256: str,
    expected_count: int,
) -> tuple[TaskMetadata, ...]:
    import pyarrow.parquet as parquet

    if _file_sha256(path) != expected_sha256:
        raise ValueError("Task source identity changed")
    rows = parquet.read_table(
        path,
        columns=[
            "instance_id",
            "repo",
            "created_at",
            "problem_statement",
        ],
    ).to_pylist()
    if len(rows) != expected_count:
        raise ValueError("Task count changed")
    tasks = tuple(
        TaskMetadata(
            instance_id=_required_string(row, "instance_id"),
            repository_id=_required_string(row, "repo"),
            created_at=_required_string(row, "created_at"),
            difficulty="not-used",
            problem_statement=_required_string(row, "problem_statement"),
        )
        for row in rows
    )
    if len({task.instance_id for task in tasks}) != len(tasks):
        raise ValueError("Task IDs are not unique")
    return tasks


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _mapping(
    payload: Mapping[str, object],
    key: str,
) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return value


def _mapping_sequence(
    payload: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, object], ...]:
    value = payload.get(key)
    if not isinstance(value, list) or any(
        not isinstance(row, Mapping) for row in value
    ):
        raise ValueError(f"{key} must be an array of objects")
    return tuple(value)


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


def _string_sequence(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return _unique_strings(value, label)


def _unique_strings(values: Sequence[object], label: str) -> tuple[str, ...]:
    result = tuple(values)
    if any(not isinstance(value, str) or not value for value in result):
        raise ValueError(f"{label} must contain nonempty strings")
    if len(result) != len(set(result)):
        raise ValueError(f"{label} must not contain duplicates")
    return result  # type: ignore[return-value]


def _finite_number(value: object, label: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(float(value))
    ):
        raise ValueError(f"{label} must be finite")
    return float(value)


def _mean(values: Sequence[float] | Any) -> float:
    rows = tuple(values)
    if not rows:
        raise ValueError("mean requires values")
    return fsum(float(value) for value in rows) / len(rows)


def _quantile(ordered: Sequence[float], probability: float) -> float:
    if not ordered or not 0.0 <= probability <= 1.0:
        raise ValueError("quantile inputs are invalid")
    index = probability * (len(ordered) - 1)
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content).hexdigest()


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser("fetch")
    fetch.add_argument("--plan", type=Path, default=DEFAULT_PLAN)

    run = subparsers.add_parser("run")
    run.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    run.add_argument("--output", type=Path, required=True)

    summary = subparsers.add_parser("summarize")
    summary.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    summary.add_argument("--result-a", type=Path, default=DEFAULT_RESULT_A)
    summary.add_argument("--result-b", type=Path, default=DEFAULT_RESULT_B)
    summary.add_argument("--output", type=Path, default=DEFAULT_SUMMARY)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    validate.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    plan = load_plan(args.plan)
    if args.command == "fetch":
        print(json.dumps(fetch_sources(plan), sort_keys=True))
    elif args.command == "run":
        _write_json(args.output, run_study(plan))
    elif args.command == "summarize":
        _write_json(
            args.output,
            build_summary(
                _load_mapping(args.result_a),
                _load_mapping(args.result_b),
                plan,
            ),
        )
    else:
        validate_summary(_load_mapping(args.summary), plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
