#!/usr/bin/env python3
"""Localize a negative Full development result with future-open Oracles."""

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


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.multi_repository_study.public_replay import (  # noqa: E402
    TaskMetadata,
)
from examples.multi_swe_research.suitability_audit import (  # noqa: E402
    _bootstrap_interval,
)
from examples.prequential_response_assembly.study import (  # noqa: E402
    select_cached_scalar_indices,
    solve_exact_l1_assembly,
)
from examples.swe_bench_full_development.study import (  # noqa: E402
    CANDIDATE_IDS,
    MEMBERSHIP_DIGEST_KEY,
    MEMBERSHIP_SCHEMA,
    _load_artifact,
    _load_inputs,
    _mapping,
    _mapping_sequence,
    _origins_for_horizon,
    _required_string,
    _unique_string_tuple,
    _write_json,
    load_plan as load_development_plan,
)


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "diagnostic-plan.json"
DEFAULT_DEVELOPMENT_PLAN = HERE / "plan.json"
DEFAULT_MEMBERSHIP = (
    REPOSITORY_ROOT
    / "outputs"
    / "research"
    / "2026-07-30-swe-bench-full-development"
    / "memberships-a.json"
)
DEFAULT_OUTPUT_DIRECTORY = (
    REPOSITORY_ROOT
    / "outputs"
    / "research"
    / "2026-07-30-swe-bench-full-development"
)
DEFAULT_RESULT_A = DEFAULT_OUTPUT_DIRECTORY / "diagnostic-a.json"
DEFAULT_RESULT_B = DEFAULT_OUTPUT_DIRECTORY / "diagnostic-b.json"
DEFAULT_SUMMARY = HERE / "evidence" / "diagnostic-summary.json"

PLAN_SCHEMA = "barcarolle_swe_bench_full_diagnostic_plan_v1"
RESULT_SCHEMA = "barcarolle_swe_bench_full_diagnostic_result_v1"
SUMMARY_SCHEMA = "barcarolle_swe_bench_full_diagnostic_summary_v1"
PLAN_DIGEST_KEY = "diagnostic_plan_digest"
RESULT_DIGEST_KEY = "diagnostic_result_digest"
SUMMARY_DIGEST_KEY = "diagnostic_summary_digest"
ORACLE_IDS = ("reference_future_oracle", "target_future_oracle")


def load_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    """Load the post-result diagnostic contract."""
    payload = dict(_load_mapping(path))
    digest = payload.pop(PLAN_DIGEST_KEY, None)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("Full diagnostic plan schema is unsupported")
    if digest != canonical_digest(payload):
        raise ValueError("Full diagnostic plan digest does not match")
    payload[PLAN_DIGEST_KEY] = digest
    for binding in _mapping(payload, "bound_artifacts").values():
        if not isinstance(binding, Mapping):
            raise ValueError("bound diagnostic artifact must be an object")
        path_value = REPOSITORY_ROOT / _required_string(binding, "path")
        if _file_sha256(path_value) != _required_string(
            binding,
            "file_sha256",
        ):
            raise ValueError(f"bound diagnostic artifact changed: {path_value}")
        logical_key = binding.get("logical_digest_key")
        if logical_key is not None:
            bound = _load_mapping(path_value)
            if (
                not isinstance(logical_key, str)
                or bound.get(logical_key) != binding.get("logical_digest")
            ):
                raise ValueError(
                    f"bound diagnostic logical digest changed: {path_value}"
                )
    if _file_sha256(Path(__file__)) != _required_string(
        _mapping(payload, "implementation"),
        "diagnostic_file_sha256",
    ):
        raise ValueError("Full diagnostic implementation changed")
    authority = _mapping(payload, "authority")
    if any(
        authority.get(key) != 0
        for key in (
            "paid_api_calls",
            "new_agent_outcome_calls",
            "sealed_swe_bench_verified_agent_reads",
        )
    ):
        raise ValueError("Full diagnostic authority changed")
    return payload


def select_future_oracle_memberships(
    history: Any,
    future: Any,
    *,
    budget: int,
    created_order: Sequence[tuple[str, str]],
) -> Mapping[int, Mapping[str, tuple[int, ...]]]:
    """Materialize target-hidden and target-open future Oracles."""
    import numpy as np

    history_values = np.asarray(history, dtype=np.float64)
    future_values = np.asarray(future, dtype=np.float64)
    order = tuple(created_order)
    if (
        history_values.ndim != 2
        or future_values.ndim != 2
        or history_values.shape[1] != future_values.shape[1]
        or history_values.shape[1] < 2
        or history_values.shape[0] != len(order)
        or isinstance(budget, bool)
        or budget <= 0
        or budget > len(history_values)
        or not np.all((history_values == 0.0) | (history_values == 1.0))
        or not np.all((future_values == 0.0) | (future_values == 1.0))
    ):
        raise ValueError("future Oracle inputs are invalid")
    result = {}
    for held_out in range(history_values.shape[1]):
        visible = tuple(
            index
            for index in range(history_values.shape[1])
            if index != held_out
        )
        reference = solve_exact_l1_assembly(
            history_values[:, list(visible)],
            future_values[:, list(visible)].mean(axis=0),
            budget=budget,
            created_order=order,
        )
        target = select_cached_scalar_indices(
            tuple(int(value) for value in history_values[:, held_out]),
            float(future_values[:, held_out].mean()),
            budget=budget,
            created_order=order,
        )
        result[held_out] = {
            "reference_future_oracle": reference.indices,
            "target_future_oracle": target,
        }
    return result


def run_diagnostic(
    *,
    plan: Mapping[str, object],
    development_plan: Mapping[str, object],
    membership: Mapping[str, object],
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    identities: Mapping[str, object],
    source_plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Measure future-open signal and frozen-portfolio diversity."""
    import numpy as np

    if (
        plan.get("development_plan_digest")
        != development_plan.get("plan_digest")
        or membership.get("plan_digest") != development_plan.get("plan_digest")
        or canonical_digest(_mapping(membership, "input_identities"))
        != canonical_digest(identities)
    ):
        raise ValueError("Full diagnostic inputs changed")
    agent_ids = tuple(sorted(outcomes_by_agent))
    horizon_payloads = {}
    for horizon in (5, 10):
        origins_by_repository, repository_ids = _origins_for_horizon(
            tasks,
            source_plan,
            horizon,
        )
        rows = []
        for position, repository_id in enumerate(repository_ids, start=1):
            for origin in origins_by_repository[repository_id]:
                history_ids = tuple(
                    task.instance_id for task in origin.history
                )
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
                memberships = select_future_oracle_memberships(
                    history,
                    future,
                    budget=10,
                    created_order=tuple(
                        (task.created_at, task.instance_id)
                        for task in origin.history
                    ),
                )
                future_rates = future.mean(axis=0)
                for held_out, target_agent_id in enumerate(agent_ids):
                    losses = {
                        "full_history": float(
                            abs(
                                history[:, held_out].mean()
                                - future_rates[held_out]
                            )
                        )
                    }
                    for oracle_id, indices in memberships[held_out].items():
                        losses[oracle_id] = float(
                            abs(
                                history[list(indices), held_out].mean()
                                - future_rates[held_out]
                            )
                        )
                    rows.append(
                        {
                            "repository_id": repository_id,
                            "origin_id": origin.origin_id,
                            "target_agent_id": target_agent_id,
                            "losses": losses,
                        }
                    )
            print(
                f"diagnosed H{horizon} repository "
                f"{position}/{len(repository_ids)} {repository_id}",
                flush=True,
            )
        horizon_payloads[str(horizon)] = _summarize_oracles(
            rows,
            repository_ids=repository_ids,
            agent_ids=agent_ids,
            bootstrap_resamples=10000,
            bootstrap_seed=20260820 + horizon,
        )
        horizon_payloads[str(horizon)]["portfolio_diversity"] = (
            _membership_diversity(
                _mapping(
                    _mapping(membership, "horizons"),
                    str(horizon),
                )
            )
        )
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "diagnostic_plan_digest": plan.get("diagnostic_plan_digest"),
        "development_plan_digest": development_plan.get("plan_digest"),
        "membership_digest": membership.get("membership_digest"),
        "input_identities": dict(identities),
        "horizons": horizon_payloads,
        "decision": _localize(horizon_payloads),
        "resource_use": {
            "paid_api_calls": 0,
            "new_agent_outcome_calls": 0,
            "sealed_swe_bench_verified_agent_reads": 0,
        },
        "claim_boundary": plan.get("claim_boundary"),
    }
    result[RESULT_DIGEST_KEY] = canonical_digest(result)
    return result


def _summarize_oracles(
    rows: Sequence[Mapping[str, Any]],
    *,
    repository_ids: Sequence[str],
    agent_ids: Sequence[str],
    bootstrap_resamples: int,
    bootstrap_seed: int,
) -> dict[str, Any]:
    by_repository: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    by_agent_repository: dict[
        tuple[str, str],
        list[Mapping[str, Any]],
    ] = defaultdict(list)
    for row in rows:
        repository_id = _required_string(row, "repository_id")
        agent_id = _required_string(row, "target_agent_id")
        by_repository[repository_id].append(row)
        by_agent_repository[(agent_id, repository_id)].append(row)
    algorithm_ids = ("full_history", *ORACLE_IDS)
    repository_rows = []
    for repository_id in repository_ids:
        mae = {
            algorithm_id: _mean(
                tuple(
                    _number(
                        _mapping(row, "losses").get(algorithm_id),
                        f"{algorithm_id} loss",
                    )
                    for row in by_repository[repository_id]
                )
            )
            for algorithm_id in algorithm_ids
        }
        repository_rows.append(
            {
                "repository_id": repository_id,
                "mae": mae,
                "oracle_minus_full": {
                    oracle_id: mae[oracle_id] - mae["full_history"]
                    for oracle_id in ORACLE_IDS
                },
            }
        )
    macro = {
        algorithm_id: _mean(
            tuple(
                _number(
                    _mapping(row, "mae").get(algorithm_id),
                    f"{algorithm_id} repository MAE",
                )
                for row in repository_rows
            )
        )
        for algorithm_id in algorithm_ids
    }
    agent_rows = []
    for agent_id in agent_ids:
        repository_mae = {}
        for repository_id in repository_ids:
            source_rows = by_agent_repository[(agent_id, repository_id)]
            repository_mae[repository_id] = {
                algorithm_id: _mean(
                    tuple(
                        _number(
                            _mapping(row, "losses").get(algorithm_id),
                            f"{algorithm_id} loss",
                        )
                        for row in source_rows
                    )
                )
                for algorithm_id in algorithm_ids
            }
        agent_macro = {
            algorithm_id: _mean(
                tuple(
                    repository_mae[repository_id][algorithm_id]
                    for repository_id in repository_ids
                )
            )
            for algorithm_id in algorithm_ids
        }
        agent_rows.append(
            {
                "target_agent_id": agent_id,
                "oracle_minus_full": {
                    oracle_id: (
                        agent_macro[oracle_id] - agent_macro["full_history"]
                    )
                    for oracle_id in ORACLE_IDS
                },
            }
        )
    oracles = {}
    for oracle_id in ORACLE_IDS:
        repository_differences = tuple(
            _number(
                _mapping(row, "oracle_minus_full").get(oracle_id),
                f"{oracle_id} repository difference",
            )
            for row in repository_rows
        )
        agent_differences = tuple(
            _number(
                _mapping(row, "oracle_minus_full").get(oracle_id),
                f"{oracle_id} Agent difference",
            )
            for row in agent_rows
        )
        interval = _bootstrap_interval(
            repository_differences,
            resamples=bootstrap_resamples,
            seed=bootstrap_seed,
        )
        oracles[oracle_id] = {
            "mae": macro[oracle_id],
            "oracle_minus_full": macro[oracle_id] - macro["full_history"],
            "repository_bootstrap_interval_95": {
                "lower": interval["lower"],
                "upper": interval["upper"],
            },
            "favorable_repository_count": sum(
                value < 0.0 for value in repository_differences
            ),
            "favorable_target_agent_count": sum(
                value < 0.0 for value in agent_differences
            ),
        }
    return {
        "repository_count": len(repository_ids),
        "origin_count": len(rows) // len(agent_ids),
        "target_agent_count": len(agent_ids),
        "mae": macro,
        "oracles": oracles,
        "repository_rows": tuple(repository_rows),
        "target_agent_rows": tuple(agent_rows),
        "score_rows_digest": canonical_digest(rows),
    }


def _membership_diversity(
    membership_horizon: Mapping[str, Any],
) -> Mapping[str, Any]:
    rows = _mapping_sequence(membership_horizon, "rows")
    pairs = {}
    for left_index, left in enumerate(CANDIDATE_IDS):
        for right in CANDIDATE_IDS[left_index + 1 :]:
            exact = 0
            jaccard = []
            for row in rows:
                memberships = _mapping(row, "memberships")
                left_set = set(
                    _unique_string_tuple(
                        memberships.get(left),
                        f"{left} membership",
                    )
                )
                right_set = set(
                    _unique_string_tuple(
                        memberships.get(right),
                        f"{right} membership",
                    )
                )
                exact += left_set == right_set
                jaccard.append(
                    len(left_set & right_set) / len(left_set | right_set)
                )
            pairs[f"{left}__{right}"] = {
                "exact_membership_rate": exact / len(rows),
                "mean_jaccard": _mean(tuple(jaccard)),
            }
    return {
        "target_row_count": len(rows),
        "pairwise": pairs,
    }


def _localize(
    horizons: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    labels = {}
    for horizon, payload in sorted(horizons.items()):
        oracles = _mapping(payload, "oracles")
        reference = _number(
            _mapping(oracles, "reference_future_oracle").get(
                "oracle_minus_full"
            ),
            "reference Oracle difference",
        )
        target = _number(
            _mapping(oracles, "target_future_oracle").get("oracle_minus_full"),
            "target Oracle difference",
        )
        labels[horizon] = {
            "reference_agent_signal_can_beat_full": reference < 0.0,
            "history_pool_can_match_target_future_rate": target < 0.0,
            "interpretation": (
                "forecasting_or_materialization_is_the_primary_gap"
                if reference < 0.0
                else "cross_agent_transfer_is_the_primary_gap"
                if target < 0.0
                else "history_pool_capacity_is_the_primary_gap"
            ),
        }
    return {
        "by_horizon": labels,
        "candidate_ranking_changed": False,
        "selector_nominated": False,
        "production_promotion_allowed": False,
    }


def build_summary(
    result_a: Mapping[str, object],
    result_b: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, Any]:
    """Build committed evidence from identical diagnostic runs."""
    _validate_result(result_a, plan)
    _validate_result(result_b, plan)
    identical = canonical_json(result_a) == canonical_json(result_b)
    if not identical:
        raise ValueError("Full diagnostic reproduction is not identical")
    summary: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "study_id": plan.get("study_id"),
        "diagnostic_plan_digest": plan.get("diagnostic_plan_digest"),
        "development_plan_digest": result_a.get("development_plan_digest"),
        "membership_digest": result_a.get("membership_digest"),
        "input_identities": dict(_mapping(result_a, "input_identities")),
        "reproduction": {
            "byte_identical_second_run": True,
            "diagnostic_result_digest": result_a.get(
                "diagnostic_result_digest"
            ),
        },
        "horizons": dict(_mapping(result_a, "horizons")),
        "decision": dict(_mapping(result_a, "decision")),
        "resource_use": dict(_mapping(result_a, "resource_use")),
        "claim_boundary": plan.get("claim_boundary"),
    }
    summary[SUMMARY_DIGEST_KEY] = canonical_digest(summary)
    return summary


def _validate_result(
    result: Mapping[str, object],
    plan: Mapping[str, object],
) -> None:
    if result.get("schema_version") != RESULT_SCHEMA:
        raise ValueError("Full diagnostic result schema is unsupported")
    digest = result.get(RESULT_DIGEST_KEY)
    body = {
        key: value
        for key, value in result.items()
        if key != RESULT_DIGEST_KEY
    }
    if (
        digest != canonical_digest(body)
        or result.get("diagnostic_plan_digest")
        != plan.get("diagnostic_plan_digest")
    ):
        raise ValueError("Full diagnostic result binding changed")


def run_once(
    *,
    plan_path: Path,
    development_plan_path: Path,
    membership_path: Path,
    output: Path,
) -> None:
    plan = load_plan(plan_path)
    development_plan = load_development_plan(development_plan_path)
    source_plan, tasks, outcomes, identities, _ = _load_inputs(
        development_plan
    )
    membership = _load_artifact(
        membership_path,
        schema=MEMBERSHIP_SCHEMA,
        digest_key=MEMBERSHIP_DIGEST_KEY,
    )
    _write_json(
        output,
        run_diagnostic(
            plan=plan,
            development_plan=development_plan,
            membership=membership,
            tasks=tasks,
            outcomes_by_agent=outcomes,
            identities=identities,
            source_plan=source_plan,
        ),
    )


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _mean(values: Sequence[float]) -> float:
    rows = tuple(values)
    if not rows:
        raise ValueError("mean requires values")
    return fsum(rows) / len(rows)


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summary_command(args: argparse.Namespace) -> None:
    plan = load_plan(args.plan)
    result_a = _load_mapping(args.result_a)
    result_b = _load_mapping(args.result_b)
    _write_json(args.output, build_summary(result_a, result_b, plan))


def _validate_command(args: argparse.Namespace) -> None:
    plan = load_plan(args.plan)
    summary = _load_mapping(args.summary)
    if summary.get("schema_version") != SUMMARY_SCHEMA:
        raise ValueError("Full diagnostic summary schema is unsupported")
    digest = summary.get(SUMMARY_DIGEST_KEY)
    body = {
        key: value
        for key, value in summary.items()
        if key != SUMMARY_DIGEST_KEY
    }
    if (
        digest != canonical_digest(body)
        or summary.get("diagnostic_plan_digest")
        != plan.get("diagnostic_plan_digest")
    ):
        raise ValueError("Full diagnostic summary binding changed")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run")
    run.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    run.add_argument(
        "--development-plan",
        type=Path,
        default=DEFAULT_DEVELOPMENT_PLAN,
    )
    run.add_argument(
        "--membership",
        type=Path,
        default=DEFAULT_MEMBERSHIP,
    )
    run.add_argument("--output", type=Path, required=True)

    summary = subparsers.add_parser("summarize")
    summary.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    summary.add_argument("--result-a", type=Path, default=DEFAULT_RESULT_A)
    summary.add_argument("--result-b", type=Path, default=DEFAULT_RESULT_B)
    summary.add_argument("--output", type=Path, default=DEFAULT_SUMMARY)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    validate.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)

    args = parser.parse_args(argv)
    if args.command == "run":
        run_once(
            plan_path=args.plan,
            development_plan_path=args.development_plan,
            membership_path=args.membership,
            output=args.output,
        )
    elif args.command == "summarize":
        _summary_command(args)
    else:
        _validate_command(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
