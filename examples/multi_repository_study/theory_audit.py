#!/usr/bin/env python3
"""Adversarially audit the frozen joint-Markov development nomination."""

from __future__ import annotations

# The extraction environment owns the optional parquet dependency.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
import hashlib
import json
from math import fsum, isfinite, sqrt
from pathlib import Path
import random
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
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
)
from examples.multi_repository_study.theory import (  # noqa: E402
    fit_repository_equal_markov,
    forecast_joint_markov,
    load_theory_plan,
)


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "theory-audit-plan.json"
DEFAULT_THEORY_PLAN = HERE / "theory-plan.json"
DEFAULT_THEORY_RESULTS = HERE / "theory-results.json"
DEFAULT_PUBLIC_PLAN = HERE / "public-panel-plan.json"
DEFAULT_PORTFOLIO = HERE / "portfolio.json"
DEFAULT_OUTPUT = HERE / "theory-audit-results.json"


def load_audit_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("theory audit plan must be an object")
    if payload.get("schema_version") != "barcarolle_theory_selector_audit_plan_v1":
        raise ValueError("theory audit plan schema is unsupported")
    digest = payload.get("audit_plan_digest")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "audit_plan_digest"}
    )
    if digest != expected:
        raise ValueError("theory audit plan digest does not match")
    return payload


def permute_joint_outcomes(
    tasks_by_repository: Mapping[str, Sequence[TaskMetadata]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    generator: random.Random,
) -> Mapping[str, Mapping[str, int]]:
    agent_ids = tuple(sorted(outcomes_by_agent))
    if not agent_ids:
        raise ValueError("joint permutation requires Agents")
    permuted = {agent_id: {} for agent_id in agent_ids}
    for repository_id in sorted(tasks_by_repository):
        tasks = tasks_by_repository[repository_id]
        if not tasks:
            raise ValueError("joint permutation repository is empty")
        vectors = [
            tuple(
                _binary_outcome(
                    outcomes_by_agent[agent_id].get(task.instance_id),
                    agent_id,
                    task.instance_id,
                )
                for agent_id in agent_ids
            )
            for task in tasks
        ]
        generator.shuffle(vectors)
        for task, vector in zip(tasks, vectors, strict=True):
            for index, agent_id in enumerate(agent_ids):
                permuted[agent_id][task.instance_id] = vector[index]
    return permuted


def run_leave_one_agent_out(
    repository_ids: Sequence[str],
    deep_repository_ids: Sequence[str],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    tasks_by_repository: Mapping[str, Sequence[TaskMetadata]],
    cluster_by_repository: Mapping[str, str],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    *,
    cell_prior_mass: float,
    local_prior_strength: float,
    horizon: int,
    budget: int,
    bootstrap_seed: int,
    bootstrap_resamples: int,
) -> Mapping[str, Any]:
    agent_ids = tuple(sorted(outcomes_by_agent))
    if len(agent_ids) < 2:
        raise ValueError("leave-one-Agent-out requires at least two Agents")
    summaries = {}
    membership_digests = {}
    for held_out_agent_id in agent_ids:
        reference_outcomes = {
            agent_id: outcomes_by_agent[agent_id]
            for agent_id in agent_ids
            if agent_id != held_out_agent_id
        }
        held_out_outcomes = {
            held_out_agent_id: outcomes_by_agent[held_out_agent_id]
        }
        rows = []
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
                reference_outcomes,
                cell_prior_mass=cell_prior_mass,
            )
            for origin in origins_by_repository[outer_repository_id]:
                forecast = forecast_joint_markov(
                    origin.history,
                    reference_outcomes,
                    transition,
                    horizon=horizon,
                    local_prior_strength=local_prior_strength,
                    include_local_transitions=True,
                )
                selected = select_outcome_match(
                    origin.history,
                    reference_outcomes,
                    forecast,
                    budget=budget,
                )
                history_ids = tuple(task.instance_id for task in origin.history)
                future_ids = tuple(task.instance_id for task in origin.future)
                rows.append(
                    ContrastRow(
                        selector_id=f"joint_markov_without_{held_out_agent_id}",
                        portfolio="wide",
                        repository_id=outer_repository_id,
                        repository_cluster_id=cluster_by_repository[
                            outer_repository_id
                        ],
                        origin_id=origin.origin_id,
                        difference=(
                            future_pass_rate_mae(
                                selected,
                                future_ids,
                                held_out_outcomes,
                            )
                            - future_pass_rate_mae(
                                history_ids,
                                future_ids,
                                held_out_outcomes,
                            )
                        ),
                    )
                )
                memberships[origin.origin_id] = selected
        summaries[held_out_agent_id] = {
            portfolio_name: summarize_contrasts(
                tuple(
                    _with_portfolio(row, portfolio_name)
                    for row in rows
                    if row.repository_id in selected_repositories
                ),
                bootstrap_seed=bootstrap_seed,
                bootstrap_resamples=bootstrap_resamples,
            )
            for portfolio_name, selected_repositories in (
                ("wide", set(repository_ids)),
                ("deep", set(deep_repository_ids)),
            )
        }
        membership_digests[held_out_agent_id] = canonical_digest(
            tuple(sorted(memberships.items()))
        )
    wide_differences = tuple(
        float(summary["wide"]["macro_repository_difference"])
        for summary in summaries.values()
    )
    deep_differences = tuple(
        float(summary["deep"]["macro_repository_difference"])
        for summary in summaries.values()
    )
    return {
        "by_held_out_agent": summaries,
        "selection_membership_digests": membership_digests,
        "wide_macro_over_held_out_agents": _mean(wide_differences),
        "wide_favorable_held_out_agent_count": sum(
            value < 0.0 for value in wide_differences
        ),
        "deep_macro_over_held_out_agents": _mean(deep_differences),
        "deep_favorable_held_out_agent_count": sum(
            value < 0.0 for value in deep_differences
        ),
    }


def run_temporal_null(
    repository_ids: Sequence[str],
    origins_by_repository: Mapping[str, Sequence[RepositoryOrigin]],
    tasks_by_repository: Mapping[str, Sequence[TaskMetadata]],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    *,
    cell_prior_mass: float,
    local_prior_strength: float,
    horizon: int,
    budget: int,
    permutations: int,
    seed: int,
    observed_difference: float,
) -> Mapping[str, Any]:
    if permutations <= 0:
        raise ValueError("temporal null requires permutations")
    generator = random.Random(seed)
    statistics = []
    for _ in range(permutations):
        permuted = permute_joint_outcomes(
            tasks_by_repository,
            outcomes_by_agent,
            generator,
        )
        repository_differences = []
        for outer_repository_id in repository_ids:
            training_repository_ids = tuple(
                repository_id
                for repository_id in repository_ids
                if repository_id != outer_repository_id
            )
            transition = fit_repository_equal_markov(
                training_repository_ids,
                tasks_by_repository,
                permuted,
                cell_prior_mass=cell_prior_mass,
            )
            origin_differences = []
            for origin in origins_by_repository[outer_repository_id]:
                forecast = forecast_joint_markov(
                    origin.history,
                    permuted,
                    transition,
                    horizon=horizon,
                    local_prior_strength=local_prior_strength,
                    include_local_transitions=True,
                )
                selected = select_outcome_match(
                    origin.history,
                    permuted,
                    forecast,
                    budget=budget,
                )
                history_ids = tuple(task.instance_id for task in origin.history)
                future_ids = tuple(task.instance_id for task in origin.future)
                origin_differences.append(
                    future_pass_rate_mae(selected, future_ids, permuted)
                    - future_pass_rate_mae(history_ids, future_ids, permuted)
                )
            repository_differences.append(_mean(tuple(origin_differences)))
        statistics.append(_mean(tuple(repository_differences)))
    ordered = sorted(statistics)
    rate = sum(value <= observed_difference for value in ordered) / permutations
    mean = _mean(tuple(ordered))
    standard_deviation = sqrt(
        _mean(tuple((value - mean) ** 2 for value in ordered))
    )
    return {
        "permutations": permutations,
        "seed": seed,
        "observed_wide_macro_repository_difference": observed_difference,
        "as_good_or_better_rate": rate,
        "null_mean": mean,
        "null_population_standard_deviation": standard_deviation,
        "monte_carlo_standard_error_at_observed_rate": sqrt(
            rate * (1.0 - rate) / permutations
        ),
        "quantiles": {
            "0.025": _empirical_quantile(ordered, 0.025),
            "0.5": _empirical_quantile(ordered, 0.5),
            "0.975": _empirical_quantile(ordered, 0.975),
        },
        "minimum": ordered[0],
        "maximum": ordered[-1],
        "null_statistics_digest": canonical_digest(tuple(statistics)),
    }


def audit_decision(
    temporal_null_rate: float,
    held_out_wide_macro: float,
    held_out_favorable_count: int,
) -> str:
    if not 0.0 <= temporal_null_rate <= 1.0:
        raise ValueError("temporal null rate must be in [0, 1]")
    if temporal_null_rate >= 0.10:
        return "retire_candidate_after_adversarial_audit"
    if held_out_wide_macro < 0.0 and held_out_favorable_count >= 2:
        return "retain_candidate_for_independent_agent_validation"
    return "retain_only_as_panel_conditional_candidate"


def run_audit(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    audit_plan: Mapping[str, object],
    theory_plan: Mapping[str, object],
    public_plan: Mapping[str, object],
    portfolio: Mapping[str, object],
) -> Mapping[str, Any]:
    source = _mapping(audit_plan, "source_results")
    if source.get("theory_plan_digest") != theory_plan.get("theory_plan_digest"):
        raise ValueError("audit plan does not bind the theory plan")
    rolling = _mapping(theory_plan, "rolling_origin")
    origins_by_repository = build_repository_origins(
        tasks,
        minimum_initial_history_tasks=_positive_integer(
            rolling,
            "minimum_initial_history_tasks",
        ),
        future_block_tasks=_positive_integer(rolling, "future_block_tasks"),
    )
    outer = _mapping(theory_plan, "outer_evaluation")
    repository_ids = _unique_strings(
        outer.get("repository_ids"),
        "outer repositories",
    )
    deep_repository_ids = _unique_strings(
        outer.get("deep_repository_ids"),
        "deep repositories",
    )
    tasks_by_repository: dict[str, list[TaskMetadata]] = defaultdict(list)
    for task in tasks:
        tasks_by_repository[task.repository_id].append(task)
    for repository_tasks in tasks_by_repository.values():
        repository_tasks.sort(key=lambda task: (task.created_at, task.instance_id))
    cluster_by_repository = {
        _required_string(row, "repository_id"): _required_string(
            row,
            "repository_cluster_id",
        )
        for row in _mapping_sequence(portfolio, "repositories")
    }
    if any(
        repository_id not in cluster_by_repository
        or not origins_by_repository.get(repository_id)
        for repository_id in repository_ids
    ):
        raise ValueError("audit repositories require lineage and Origins")
    agent_outcome = _mapping(audit_plan, "leave_one_agent_out")
    aggregation = _mapping(_mapping(theory_plan, "diagnostics"), "aggregation")
    held_out = run_leave_one_agent_out(
        repository_ids,
        deep_repository_ids,
        origins_by_repository,
        tasks_by_repository,
        cluster_by_repository,
        outcomes_by_agent,
        cell_prior_mass=_finite_number(
            agent_outcome.get("training_transition_dirichlet_cell_mass"),
            "held-out transition cell mass",
        ),
        local_prior_strength=_finite_number(
            agent_outcome.get("target_local_transition_prior_total_mass_per_row"),
            "held-out local prior strength",
        ),
        horizon=_positive_integer(agent_outcome, "horizon"),
        budget=_positive_integer(agent_outcome, "selection_budget_tasks"),
        bootstrap_seed=_integer(aggregation, "bootstrap_seed"),
        bootstrap_resamples=_positive_integer(
            aggregation,
            "bootstrap_resamples",
        ),
    )
    theory_constants = _mapping(theory_plan, "fixed_algorithm_constants")
    temporal_config = _mapping(audit_plan, "temporal_null")
    temporal = run_temporal_null(
        repository_ids,
        origins_by_repository,
        tasks_by_repository,
        outcomes_by_agent,
        cell_prior_mass=_finite_number(
            theory_constants.get("training_transition_dirichlet_cell_mass"),
            "transition cell mass",
        ),
        local_prior_strength=_finite_number(
            theory_constants.get(
                "target_local_transition_prior_total_mass_per_row"
            ),
            "local prior strength",
        ),
        horizon=_positive_integer(theory_constants, "markov_forecast_steps"),
        budget=_positive_integer(rolling, "selection_budget_tasks"),
        permutations=_positive_integer(temporal_config, "permutations"),
        seed=_integer(temporal_config, "seed"),
        observed_difference=_finite_number(
            source.get("observed_wide_macro_repository_difference"),
            "observed difference",
        ),
    )
    decision = audit_decision(
        float(temporal["as_good_or_better_rate"]),
        float(held_out["wide_macro_over_held_out_agents"]),
        int(held_out["wide_favorable_held_out_agent_count"]),
    )
    result: dict[str, Any] = {
        "schema_version": "barcarolle_theory_selector_audit_results_v1",
        "study_id": audit_plan.get("study_id"),
        "epistemic_status": audit_plan.get("epistemic_status"),
        "audit_plan_digest": audit_plan.get("audit_plan_digest"),
        "theory_plan_digest": theory_plan.get("theory_plan_digest"),
        "theory_results_digest": source.get("theory_results_digest"),
        "portfolio_digest": portfolio.get("portfolio_digest"),
        "public_panel_plan_digest": public_plan.get("public_panel_plan_digest"),
        "task_count": len(tasks),
        "agent_count": len(outcomes_by_agent),
        "origin_counts": {
            repository_id: len(origins_by_repository[repository_id])
            for repository_id in repository_ids
        },
        "leave_one_agent_out": held_out,
        "temporal_null": temporal,
        "decision": {
            "status": decision,
            "independent_validation_candidate": (
                "joint_markov_match"
                if decision == "retain_candidate_for_independent_agent_validation"
                else None
            ),
            "production_promotion_allowed": False,
        },
        "claim_boundary": (
            "This post-nomination audit reuses opened outcomes. It can retire "
            "or narrow the candidate and prioritize an independent Agent test; "
            "it cannot provide independent confirmation."
        ),
    }
    result["audit_results_digest"] = canonical_digest(result)
    return result


def _with_portfolio(row: ContrastRow, portfolio: str) -> ContrastRow:
    return ContrastRow(
        selector_id=row.selector_id,
        portfolio=portfolio,
        repository_id=row.repository_id,
        repository_cluster_id=row.repository_cluster_id,
        origin_id=row.origin_id,
        difference=row.difference,
    )


def _binary_outcome(value: object, agent_id: str, task_id: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1):
        raise ValueError(f"invalid binary outcome for {agent_id}/{task_id}")
    return value


def _empirical_quantile(values: Sequence[float], probability: float) -> float:
    if not values or not 0.0 <= probability <= 1.0:
        raise ValueError("empirical quantile input is invalid")
    return values[round(probability * (len(values) - 1))]


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires values")
    return fsum(values) / len(values)


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    normalized = float(value)
    if not isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    return normalized


def _unique_strings(value: object, name: str) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{name} must be nonempty strings")
    normalized = tuple(value)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{name} must be unique")
    return normalized


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


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_bound_result(
    path: Path,
    *,
    digest_field: str,
    expected_digest: object,
) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must be an object")
    digest = payload.pop(digest_field, None)
    if canonical_digest(payload) != digest or digest != expected_digest:
        raise ValueError(f"{path.name} does not match the audit plan")
    return payload


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--theory-plan", type=Path, default=DEFAULT_THEORY_PLAN)
    parser.add_argument(
        "--theory-results",
        type=Path,
        default=DEFAULT_THEORY_RESULTS,
    )
    parser.add_argument("--public-plan", type=Path, default=DEFAULT_PUBLIC_PLAN)
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    audit_plan = load_audit_plan(args.plan)
    theory_plan = load_theory_plan(args.theory_plan)
    public_plan = load_public_panel_plan(args.public_plan)
    portfolio = load_portfolio(args.portfolio)
    public_source = _mapping(public_plan, "task_source")
    if _file_sha256(args.dataset) != _required_string(
        public_source,
        "dataset_sha256",
    ):
        raise RuntimeError("dataset digest does not match public plan")
    source = _mapping(audit_plan, "source_results")
    _load_bound_result(
        args.theory_results,
        digest_field="theory_results_digest",
        expected_digest=source.get("theory_results_digest"),
    )
    tasks = load_dataset_tasks(args.dataset)
    outcomes, _ = load_public_outcomes(
        args.result_dir,
        public_plan,
        tuple(task.instance_id for task in tasks),
    )
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite theory audit: {args.output}")
    result = run_audit(
        tasks,
        outcomes,
        audit_plan,
        theory_plan,
        public_plan,
        portfolio,
    )
    args.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "audit_results_digest": result["audit_results_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
