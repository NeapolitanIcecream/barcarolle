#!/usr/bin/env python3
"""Replicate the frozen joint-Markov Selection on a sealed Agent panel."""

from __future__ import annotations

# The extraction environment owns the optional parquet dependency.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    canonical_digest,
    canonical_json,
    parse_utc_timestamp,
)
from examples.multi_repository_study.aggregate import (  # noqa: E402
    ContrastRow,
    summarize_contrasts,
)
from examples.multi_repository_study.development import (  # noqa: E402
    select_outcome_match,
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
    official_binary_outcomes,
)
from examples.multi_repository_study.theory import (  # noqa: E402
    fit_repository_equal_markov,
    forecast_joint_markov,
    load_theory_plan,
)


HERE = Path(__file__).resolve().parent
DEFAULT_EXTENSION_PLAN = HERE / "agent-panel-extension-plan.json"
DEFAULT_SCHEMA_AMENDMENT = HERE / "agent-panel-schema-amendment.json"
DEFAULT_PUBLIC_PLAN = HERE / "public-panel-plan.json"
DEFAULT_THEORY_PLAN = HERE / "theory-plan.json"
DEFAULT_THEORY_RESULTS = HERE / "theory-results.json"
DEFAULT_PORTFOLIO = HERE / "portfolio.json"
DEFAULT_OUTPUT = HERE / "agent-panel-replication-results.json"


def load_agent_panel_extension_plan(
    path: Path = DEFAULT_EXTENSION_PLAN,
) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Agent panel extension plan must be an object")
    if payload.get("schema_version") != "barcarolle_agent_panel_extension_plan_v1":
        raise ValueError("Agent panel extension plan schema is unsupported")
    digest = payload.get("agent_panel_extension_plan_digest")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "agent_panel_extension_plan_digest"
        }
    )
    if digest != expected:
        raise ValueError("Agent panel extension plan digest does not match")
    return payload


def load_agent_panel_schema_amendment(
    path: Path = DEFAULT_SCHEMA_AMENDMENT,
) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Agent panel schema amendment must be an object")
    if payload.get("schema_version") != "barcarolle_agent_panel_schema_amendment_v1":
        raise ValueError("Agent panel schema amendment is unsupported")
    digest = payload.get("agent_panel_schema_amendment_digest")
    expected = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "agent_panel_schema_amendment_digest"
        }
    )
    if digest != expected:
        raise ValueError("Agent panel schema amendment digest does not match")
    return payload


def load_allocated_outcomes(
    result_dir: Path,
    plan: Mapping[str, object],
    task_ids: Sequence[str],
    *,
    allocation_key: str,
    schema_amendment: Mapping[str, object] | None = None,
) -> tuple[Mapping[str, Mapping[str, int]], Mapping[str, Mapping[str, int]]]:
    if allocation_key not in {"development_allocation", "holdout_allocation"}:
        raise ValueError("unsupported Agent allocation")
    amendment = (
        load_agent_panel_schema_amendment()
        if schema_amendment is None
        else schema_amendment
    )
    if amendment.get("agent_panel_extension_plan_digest") != plan.get(
        "agent_panel_extension_plan_digest"
    ):
        raise ValueError("schema amendment does not bind the extension plan")
    legacy_fields = _string_tuple(
        amendment.get("legacy_schema_fields"),
        "legacy schema fields",
    )
    legacy_blob_shas = {
        _required_string(row, "result_blob_sha")
        for row in _mapping_sequence(amendment, "affected_result_blobs")
    }
    outcomes = {}
    diagnostics = {}
    for agent in _mapping_sequence(plan, allocation_key):
        agent_id = _required_string(agent, "agent_id")
        submission = _required_string(agent, "submission")
        path = result_dir / f"{submission}.json"
        raw = path.read_bytes()
        if _git_blob_sha(raw) != _required_string(agent, "result_blob_sha"):
            raise ValueError(f"Agent result blob does not match plan: {submission}")
        payload = json.loads(raw)
        if not isinstance(payload, Mapping):
            raise ValueError("Agent result must be a JSON object")
        result_blob_sha = _required_string(agent, "result_blob_sha")
        if result_blob_sha in legacy_blob_shas:
            agent_outcomes, agent_diagnostics = legacy_official_binary_outcomes(
                task_ids,
                payload,
                legacy_fields=legacy_fields,
            )
        else:
            agent_outcomes, agent_diagnostics = official_binary_outcomes(
                task_ids,
                payload,
            )
        outcomes[agent_id] = agent_outcomes
        diagnostics[agent_id] = agent_diagnostics
    return dict(sorted(outcomes.items())), dict(sorted(diagnostics.items()))


def legacy_official_binary_outcomes(
    task_denominator: Sequence[str],
    result_payload: Mapping[str, object],
    *,
    legacy_fields: Sequence[str],
) -> tuple[Mapping[str, int], Mapping[str, int]]:
    expected_fields = set(
        _string_tuple(legacy_fields, "legacy result fields")
    )
    if set(result_payload) != expected_fields:
        raise ValueError("legacy official result fields are unsupported")
    denominator = _string_tuple(task_denominator, "Task denominator")
    denominator_set = set(denominator)
    values = {
        field: _task_id_set(result_payload.get(field), field)
        for field in sorted(expected_fields)
    }
    if any(task_ids - denominator_set for task_ids in values.values()):
        raise ValueError("legacy official result refers outside the Task denominator")
    outcomes = {
        task_id: int(task_id in values["resolved"]) for task_id in denominator
    }
    diagnostics = {
        f"{field}_count": len(task_ids)
        for field, task_ids in sorted(values.items())
    }
    diagnostics["ordinary_unlisted_count"] = len(
        denominator_set - set().union(*values.values())
    )
    return outcomes, diagnostics


def materialize_frozen_joint_markov(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    theory_plan: Mapping[str, object],
) -> tuple[
    Mapping[str, tuple[str, ...]],
    Mapping[str, tuple[RepositoryOrigin, ...]],
]:
    rolling = _mapping(theory_plan, "rolling_origin")
    origins_by_repository = build_repository_origins(
        tasks,
        minimum_initial_history_tasks=_positive_integer(
            rolling,
            "minimum_initial_history_tasks",
        ),
        future_block_tasks=_positive_integer(rolling, "future_block_tasks"),
    )
    budget = _positive_integer(rolling, "selection_budget_tasks")
    outer = _mapping(theory_plan, "outer_evaluation")
    repository_ids = _string_tuple(
        outer.get("repository_ids"),
        "outer repository IDs",
    )
    tasks_by_repository: dict[str, list[TaskMetadata]] = defaultdict(list)
    for task in tasks:
        tasks_by_repository[task.repository_id].append(task)
    for repository_tasks in tasks_by_repository.values():
        repository_tasks.sort(key=lambda task: (task.created_at, task.instance_id))

    constants = _mapping(theory_plan, "fixed_algorithm_constants")
    cell_prior_mass = _number(
        constants.get("training_transition_dirichlet_cell_mass"),
        "training transition cell mass",
    )
    local_prior_strength = _number(
        constants.get("target_local_transition_prior_total_mass_per_row"),
        "target local transition prior strength",
    )
    horizon = _positive_integer(constants, "markov_forecast_steps")

    memberships = {}
    for outer_repository_id in repository_ids:
        training_repository_ids = tuple(
            repository_id
            for repository_id in repository_ids
            if repository_id != outer_repository_id
        )
        transition = fit_repository_equal_markov(
            training_repository_ids,
            tasks_by_repository,
            outcomes_by_agent,
            cell_prior_mass=cell_prior_mass,
        )
        for origin in origins_by_repository[outer_repository_id]:
            forecast = forecast_joint_markov(
                origin.history,
                outcomes_by_agent,
                transition,
                horizon=horizon,
                local_prior_strength=local_prior_strength,
                include_local_transitions=True,
            )
            memberships[origin.origin_id] = select_outcome_match(
                origin.history,
                outcomes_by_agent,
                forecast,
                budget=budget,
            )
    return dict(sorted(memberships.items())), origins_by_repository


def run_panel_replication(
    tasks: Sequence[TaskMetadata],
    original_outcomes: Mapping[str, Mapping[str, int]],
    development_outcomes: Mapping[str, Mapping[str, int]],
    development_diagnostics: Mapping[str, Mapping[str, int]],
    extension_plan: Mapping[str, object],
    theory_plan: Mapping[str, object],
    theory_results: Mapping[str, object],
    portfolio: Mapping[str, object],
) -> Mapping[str, Any]:
    task_ids = tuple(task.instance_id for task in tasks)
    if (
        not task_ids
        or len(task_ids) != len(set(task_ids))
        or any(set(outcomes) != set(task_ids) for outcomes in original_outcomes.values())
        or any(
            set(outcomes) != set(task_ids)
            for outcomes in development_outcomes.values()
        )
    ):
        raise ValueError("Agent panel must cover the exact Task denominator")
    if _mapping(extension_plan, "source").get("revision") != _mapping(
        load_public_panel_plan(),
        "public_result_source",
    ).get("revision"):
        raise ValueError("Agent panel extension does not bind the public source")
    if extension_plan.get("existing_opened_development_panel") is None:
        raise ValueError("Agent panel extension lacks the opened panel")
    if set(original_outcomes) != {
        _required_string(row, "agent_id")
        for row in _mapping_sequence(
            extension_plan,
            "existing_opened_development_panel",
        )
    }:
        raise ValueError("opened Agent panel does not match the extension plan")

    memberships, origins_by_repository = materialize_frozen_joint_markov(
        tasks,
        original_outcomes,
        theory_plan,
    )
    expected_membership_digest = _required_string(
        _mapping(theory_results, "selection_membership_digests"),
        "joint_markov_match",
    )
    membership_digest = canonical_digest(tuple(sorted(memberships.items())))
    if membership_digest != expected_membership_digest:
        raise ValueError("joint Markov memberships do not match frozen results")

    outer = _mapping(theory_plan, "outer_evaluation")
    repository_ids = _string_tuple(
        outer.get("repository_ids"),
        "outer repository IDs",
    )
    deep_repository_ids = _string_tuple(
        outer.get("deep_repository_ids"),
        "deep repository IDs",
    )
    cluster_by_repository = {
        _required_string(row, "repository_id"): _required_string(
            row,
            "repository_cluster_id",
        )
        for row in _mapping_sequence(portfolio, "repositories")
    }
    aggregation = _mapping(_mapping(theory_plan, "diagnostics"), "aggregation")
    bootstrap_seed = _integer(aggregation, "bootstrap_seed")
    bootstrap_resamples = _positive_integer(
        aggregation,
        "bootstrap_resamples",
    )

    panel_rows = []
    rows_by_agent: dict[str, list[ContrastRow]] = {
        agent_id: [] for agent_id in development_outcomes
    }
    for repository_id in repository_ids:
        for origin in origins_by_repository[repository_id]:
            history_ids = tuple(task.instance_id for task in origin.history)
            future_ids = tuple(task.instance_id for task in origin.future)
            selected_ids = memberships[origin.origin_id]
            panel_rows.append(
                ContrastRow(
                    "joint_markov_match",
                    "wide",
                    repository_id,
                    cluster_by_repository[repository_id],
                    origin.origin_id,
                    future_pass_rate_mae(
                        selected_ids,
                        future_ids,
                        development_outcomes,
                    )
                    - future_pass_rate_mae(
                        history_ids,
                        future_ids,
                        development_outcomes,
                    ),
                )
            )
            for agent_id, outcomes in development_outcomes.items():
                rows_by_agent[agent_id].append(
                    ContrastRow(
                        "joint_markov_match",
                        "wide",
                        repository_id,
                        cluster_by_repository[repository_id],
                        origin.origin_id,
                        future_pass_rate_mae(
                            selected_ids,
                            future_ids,
                            {agent_id: outcomes},
                        )
                        - future_pass_rate_mae(
                            history_ids,
                            future_ids,
                            {agent_id: outcomes},
                        ),
                    )
                )

    summaries = {
        portfolio_name: _summary_for_repositories(
            panel_rows,
            selected_repositories,
            portfolio_name,
            bootstrap_seed,
            bootstrap_resamples,
        )
        for portfolio_name, selected_repositories in (
            ("wide", set(repository_ids)),
            ("deep", set(deep_repository_ids)),
        )
    }
    per_agent = {
        agent_id: {
            portfolio_name: _summary_for_repositories(
                rows,
                selected_repositories,
                portfolio_name,
                bootstrap_seed,
                bootstrap_resamples,
            )
            for portfolio_name, selected_repositories in (
                ("wide", set(repository_ids)),
                ("deep", set(deep_repository_ids)),
            )
        }
        for agent_id, rows in rows_by_agent.items()
    }
    availability = retrospective_availability_audit(
        tasks,
        origins_by_repository,
        repository_ids,
    )
    result: dict[str, Any] = {
        "schema_version": "barcarolle_agent_panel_replication_results_v1",
        "study_id": extension_plan.get("study_id"),
        "epistemic_status": "one_shot_project_sealed_agent_replication",
        "agent_panel_extension_plan_digest": extension_plan.get(
            "agent_panel_extension_plan_digest"
        ),
        "theory_plan_digest": theory_plan.get("theory_plan_digest"),
        "theory_results_digest": theory_results.get("theory_results_digest"),
        "portfolio_digest": portfolio.get("portfolio_digest"),
        "task_count": len(tasks),
        "original_agent_count": len(original_outcomes),
        "replication_agent_count": len(development_outcomes),
        "origin_counts": {
            repository_id: len(origins_by_repository[repository_id])
            for repository_id in repository_ids
        },
        "agent_outcome_diagnostics": dict(sorted(development_diagnostics.items())),
        "selection_membership_digest": membership_digest,
        "summaries": summaries,
        "per_agent_summaries": per_agent,
        "retrospective_fit_availability": availability,
        "decision": {
            "candidate_status": "remains_retired_after_adversarial_audit",
            "reactivation_allowed": False,
            "development_panel_may_now_open": True,
        },
        "claim_boundary": (
            "The per-Task outcomes were project-sealed before the allocation "
            "plan. The frozen Selection was nevertheless fitted retrospectively "
            "with later-created Tasks from other repositories, and the result "
            "cannot reactivate or promote the retired candidate."
        ),
    }
    result["agent_panel_replication_results_digest"] = canonical_digest(result)
    return result


def retrospective_availability_audit(
    tasks: Sequence[TaskMetadata],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    repository_ids: Sequence[str],
) -> Mapping[str, Any]:
    tasks_by_repository: dict[str, list[TaskMetadata]] = defaultdict(list)
    for task in tasks:
        tasks_by_repository[task.repository_id].append(task)
    total_uses = 0
    later_uses = 0
    origins_with_later = 0
    by_target = {}
    for target_repository_id in repository_ids:
        target_total = 0
        target_later = 0
        target_origins_with_later = 0
        for origin in origins_by_repository[target_repository_id]:
            cutoff = parse_utc_timestamp(origin.history[-1].created_at)
            origin_later = 0
            for training_repository_id in repository_ids:
                if training_repository_id == target_repository_id:
                    continue
                for task in tasks_by_repository[training_repository_id]:
                    target_total += 1
                    if parse_utc_timestamp(task.created_at) > cutoff:
                        target_later += 1
                        origin_later += 1
            if origin_later:
                target_origins_with_later += 1
        total_uses += target_total
        later_uses += target_later
        origins_with_later += target_origins_with_later
        by_target[target_repository_id] = {
            "training_task_uses": target_total,
            "later_created_training_task_uses": target_later,
            "later_created_rate": (
                target_later / target_total if target_total else None
            ),
            "origins_with_later_created_training_tasks": target_origins_with_later,
        }
    if not total_uses:
        raise ValueError("availability audit has no cross-repository task uses")
    return {
        "training_task_uses": total_uses,
        "later_created_training_task_uses": later_uses,
        "later_created_rate": later_uses / total_uses,
        "origins_with_later_created_training_tasks": origins_with_later,
        "origin_count": sum(
            len(origins_by_repository[repository_id])
            for repository_id in repository_ids
        ),
        "by_target_repository": by_target,
    }


def _summary_for_repositories(
    rows: Sequence[ContrastRow],
    selected_repositories: set[str],
    portfolio_name: str,
    bootstrap_seed: int,
    bootstrap_resamples: int,
) -> Mapping[str, Any]:
    return summarize_contrasts(
        tuple(
            ContrastRow(
                row.selector_id,
                portfolio_name,
                row.repository_id,
                row.repository_cluster_id,
                row.origin_id,
                row.difference,
            )
            for row in rows
            if row.repository_id in selected_repositories
        ),
        bootstrap_seed=bootstrap_seed,
        bootstrap_resamples=bootstrap_resamples,
    )


def _load_theory_results(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("theory results must be an object")
    digest = payload.get("theory_results_digest")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "theory_results_digest"}
    )
    if digest != expected:
        raise ValueError("theory results digest does not match")
    return payload


def _git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()


def _task_id_set(value: object, field: str) -> set[str]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{field} must contain nonempty Task IDs")
    items = tuple(value)
    if len(items) != len(set(items)):
        raise ValueError(f"{field} must not contain duplicate Task IDs")
    return set(items)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _mapping(value: Mapping[str, object], key: str) -> Mapping[str, object]:
    item = value.get(key)
    if not isinstance(item, Mapping):
        raise ValueError(f"{key} must be an object")
    return item


def _mapping_sequence(
    value: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, object], ...]:
    item = value.get(key)
    if (
        not isinstance(item, Sequence)
        or isinstance(item, str)
        or any(not isinstance(row, Mapping) for row in item)
    ):
        raise ValueError(f"{key} must be an array of objects")
    return tuple(item)


def _required_string(value: Mapping[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a nonempty string")
    return item


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{name} must contain nonempty strings")
    result = tuple(value)
    if not result or len(result) != len(set(result)):
        raise ValueError(f"{name} must be nonempty and unique")
    return result


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    return float(value)


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


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--extension-plan", type=Path, default=DEFAULT_EXTENSION_PLAN)
    parser.add_argument("--public-plan", type=Path, default=DEFAULT_PUBLIC_PLAN)
    parser.add_argument("--theory-plan", type=Path, default=DEFAULT_THEORY_PLAN)
    parser.add_argument(
        "--theory-results",
        type=Path,
        default=DEFAULT_THEORY_RESULTS,
    )
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    extension_plan = load_agent_panel_extension_plan(args.extension_plan)
    public_plan = load_public_panel_plan(args.public_plan)
    theory_plan = load_theory_plan(args.theory_plan)
    theory_results = _load_theory_results(args.theory_results)
    portfolio = load_portfolio(args.portfolio)
    public_source = _mapping(public_plan, "task_source")
    if _file_sha256(args.dataset) != _required_string(
        public_source,
        "dataset_sha256",
    ):
        raise RuntimeError("dataset digest does not match the public plan")
    tasks = load_dataset_tasks(args.dataset)
    task_ids = tuple(task.instance_id for task in tasks)
    original_outcomes, _ = load_public_outcomes(
        args.result_dir,
        public_plan,
        task_ids,
    )
    development_outcomes, development_diagnostics = load_allocated_outcomes(
        args.result_dir,
        extension_plan,
        task_ids,
        allocation_key="development_allocation",
    )
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite replication: {args.output}")
    result = run_panel_replication(
        tasks,
        original_outcomes,
        development_outcomes,
        development_diagnostics,
        extension_plan,
        theory_plan,
        theory_results,
        portfolio,
    )
    args.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "agent_panel_replication_results_digest": result[
                    "agent_panel_replication_results_digest"
                ],
                "wide_macro_repository_difference": result["summaries"]["wide"][
                    "macro_repository_difference"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
