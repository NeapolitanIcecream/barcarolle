#!/usr/bin/env python3
"""Freeze and run the outcome-free THY-002S-A Selection front gate."""

from __future__ import annotations

# NumPy is required only by replay commands.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from math import fsum, isfinite
import os
from pathlib import Path
import random
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.generator_calibrated_exposure import study as thy2  # noqa: E402
from examples.pre_origin_task_mix import study as common  # noqa: E402


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "plan.json"
DEFAULT_OUTPUT = (
    REPOSITORY_ROOT
    / "outputs"
    / "research"
    / "2026-07-29-generator-calibrated-selection"
    / "task-space-results.json"
)
DEFAULT_REPOSITORY_CACHE = (
    REPOSITORY_ROOT
    / "outputs"
    / "research"
    / "2026-07-29-pre-origin-task-mix"
    / "repositories"
)
DEFAULT_SUMMARY = HERE / "evidence" / "task-space-summary.json"

PLAN_SCHEMA = "barcarolle_generator_calibrated_selection_plan_v1"
RESULT_SCHEMA = "barcarolle_generator_calibrated_selection_task_space_v1"
SUMMARY_SCHEMA = "barcarolle_generator_calibrated_selection_summary_v1"
PREDICTOR_IDS = (
    "forecast",
    "task_full_history",
    "git_recent_touch",
    "yield_only",
    "selection_candidate",
    "selection_stationary",
    "selection_recency",
)
SELECTION_IDS = (
    "candidate",
    "stationary",
    "recency",
)


@dataclass(frozen=True)
class OriginRuntime:
    repository_id: str
    origin_id: str
    history: tuple[common.TaskProjection, ...]
    future_h5: tuple[common.TaskProjection, ...]
    future_h10: tuple[common.TaskProjection, ...]
    vocabulary: tuple[str, ...]


def load_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    """Load the digest-bound, outcome-free THY-002S-A contract."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("THY-002S plan schema is unsupported")
    digest = payload.get("plan_digest")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "plan_digest"}
    )
    if digest != expected:
        raise ValueError("THY-002S plan digest does not match")
    if tuple(payload.get("predictors", ())) != PREDICTOR_IDS:
        raise ValueError("THY-002S predictors changed")
    for item in _mapping_sequence(payload, "implementation"):
        _verify_sha256(
            REPOSITORY_ROOT / _required_string(item, "path"),
            _required_string(item, "sha256"),
        )
    upstream = _mapping(payload, "upstream_thy_002")
    upstream_plan_path = REPOSITORY_ROOT / _required_string(upstream, "plan")
    _verify_sha256(
        upstream_plan_path,
        _required_string(upstream, "plan_file_sha256"),
    )
    upstream_plan = thy2.load_plan(upstream_plan_path)
    if upstream_plan.get("plan_digest") != upstream.get("plan_digest"):
        raise ValueError("THY-002S upstream plan changed")
    upstream_summary_path = REPOSITORY_ROOT / _required_string(upstream, "summary")
    _verify_sha256(
        upstream_summary_path,
        _required_string(upstream, "summary_file_sha256"),
    )
    upstream_summary = _load_mapping(upstream_summary_path)
    summary_payload = dict(upstream_summary)
    summary_digest = summary_payload.pop("summary_digest", None)
    if (
        canonical_digest(summary_payload) != summary_digest
        or upstream_summary.get("result_digest") != upstream.get("result_digest")
        or upstream_summary.get("summary_digest") != upstream.get("summary_digest")
        or _mapping(upstream_summary, "decision").get("status") != "pass"
    ):
        raise ValueError("THY-002S upstream pass identity changed")
    return payload


def task_distribution(
    tasks: Sequence[common.TaskProjection],
    vocabulary: Sequence[str],
    *,
    unseen_label: str,
) -> Mapping[str, float]:
    """Return the equal-Task empirical module distribution."""
    if not tasks:
        raise ValueError("Task distribution requires at least one Task")
    counts = common.task_counts(
        tasks,
        vocabulary,
        unseen_label=unseen_label,
    )
    return {label: counts.get(label, 0.0) / len(tasks) for label in vocabulary}


def select_brier_projection(
    history: Sequence[common.TaskProjection],
    target: Mapping[str, float],
    vocabulary: Sequence[str],
    *,
    unseen_label: str,
    budget: int,
    tie_domain: str,
) -> tuple[tuple[common.TaskProjection, ...], Mapping[str, object]]:
    """Greedily match k*p, then reach a deterministic 1-swap local optimum."""
    labels = tuple(vocabulary)
    if (
        budget <= 0
        or len(history) < budget
        or not labels
        or len(labels) != len(set(labels))
    ):
        raise ValueError("Brier projection inputs are invalid")
    if set(target) != set(labels):
        raise ValueError("Brier projection target vocabulary changed")
    if any(not isfinite(value) or value < 0.0 for value in target.values()):
        raise ValueError("Brier projection target is invalid")
    if abs(fsum(target.values()) - 1.0) > 1e-12:
        raise ValueError("Brier projection target does not sum to one")

    ordered = tuple(
        sorted(
            history,
            key=lambda task: (
                _tie_key(tie_domain, task.instance_id),
                task.instance_id,
            ),
        )
    )
    if len({task.instance_id for task in ordered}) != len(ordered):
        raise ValueError("Brier projection history contains duplicate Tasks")
    vectors = {
        task.instance_id: common.task_module_mass(
            task,
            labels,
            unseen_label=unseen_label,
        )
        for task in ordered
    }
    target_counts = {label: budget * target[label] for label in labels}
    current = {label: 0.0 for label in labels}
    selected: list[common.TaskProjection] = []
    selected_ids: set[str] = set()

    for _ in range(budget):
        choices = []
        for task in ordered:
            if task.instance_id in selected_ids:
                continue
            vector = vectors[task.instance_id]
            score = fsum(
                (current[label] + vector.get(label, 0.0) - target_counts[label]) ** 2
                for label in labels
            )
            choices.append(
                (
                    score,
                    _tie_key(tie_domain, task.instance_id),
                    task.instance_id,
                    task,
                )
            )
        _, _, _, chosen = min(
            choices,
            key=lambda item: (item[0], item[1], item[2]),
        )
        selected.append(chosen)
        selected_ids.add(chosen.instance_id)
        for label, value in vectors[chosen.instance_id].items():
            current[label] += value

    greedy_objective = _selection_objective(
        current,
        target_counts,
        labels,
    )
    swap_count = 0
    while True:
        current_objective = _selection_objective(
            current,
            target_counts,
            labels,
        )
        best: (
            tuple[
                float,
                str,
                common.TaskProjection,
                common.TaskProjection,
                Mapping[str, float],
            ]
            | None
        ) = None
        unselected = tuple(
            task for task in ordered if task.instance_id not in selected_ids
        )
        for outgoing in selected:
            outgoing_vector = vectors[outgoing.instance_id]
            for incoming in unselected:
                incoming_vector = vectors[incoming.instance_id]
                candidate_counts = {
                    label: (
                        current[label]
                        - outgoing_vector.get(label, 0.0)
                        + incoming_vector.get(label, 0.0)
                    )
                    for label in labels
                }
                objective = _selection_objective(
                    candidate_counts,
                    target_counts,
                    labels,
                )
                if objective >= current_objective:
                    continue
                candidate_ids = tuple(
                    sorted(
                        (selected_ids - {outgoing.instance_id}) | {incoming.instance_id}
                    )
                )
                tie = canonical_digest(candidate_ids)
                item = (
                    objective,
                    tie,
                    outgoing,
                    incoming,
                    candidate_counts,
                )
                if best is None or item[:2] < best[:2]:
                    best = item
        if best is None:
            break
        _, _, outgoing, incoming, current = best
        selected.remove(outgoing)
        selected.append(incoming)
        selected_ids.remove(outgoing.instance_id)
        selected_ids.add(incoming.instance_id)
        swap_count += 1

    result = tuple(sorted(selected, key=lambda task: task.instance_id))
    support = {
        label
        for label in labels
        if any(vectors[task.instance_id].get(label, 0.0) > 0.0 for task in history)
    }
    cold_labels = tuple(
        label for label in labels if label not in support and target[label] > 0.0
    )
    diagnostics: dict[str, object] = {
        "budget": budget,
        "greedy_objective": greedy_objective / (budget * budget),
        "final_objective": _selection_objective(
            current,
            target_counts,
            labels,
        )
        / (budget * budget),
        "swap_count": swap_count,
        "cold_support_mass": fsum(target[label] for label in cold_labels),
        "cold_support_module_count": len(cold_labels),
        "cold_support_brier_lower_bound": fsum(
            target[label] ** 2 for label in cold_labels
        ),
        "selection_digest": canonical_digest(
            tuple(task.instance_id for task in result)
        ),
    }
    if not any(target[label] > 0.0 for label in support):
        raise ValueError("forecast has no historical Task support")
    return result, diagnostics


def _selection_objective(
    counts: Mapping[str, float],
    target_counts: Mapping[str, float],
    vocabulary: Sequence[str],
) -> float:
    return fsum(
        (counts.get(label, 0.0) - target_counts[label]) ** 2 for label in vocabulary
    )


def _tie_key(domain: str, task_id: str) -> str:
    return hashlib.sha256(f"{domain}\0{task_id}".encode()).hexdigest()


def load_tasks(
    plan: Mapping[str, object],
) -> tuple[tuple[common.TaskProjection, ...], Mapping[str, object]]:
    """Load the exact 11-repository Multi-SWE task frame without outcomes."""
    source = _mapping(plan, "source")
    import_contract_path = REPOSITORY_ROOT / _required_string(source, "import_contract")
    _verify_sha256(
        import_contract_path,
        _required_string(source, "import_contract_sha256"),
    )
    import_contract = _load_mapping(import_contract_path)
    contract_payload = dict(import_contract)
    contract_digest = contract_payload.pop("contract_digest", None)
    if canonical_digest(
        contract_payload
    ) != contract_digest or contract_digest != source.get("import_contract_digest"):
        raise ValueError("THY-002S source import contract changed")
    module_plan = _mapping(plan, "module_projection")
    universe_path = REPOSITORY_ROOT / _required_string(source, "task_universe")
    times_path = REPOSITORY_ROOT / _required_string(source, "task_times")
    source_tree = REPOSITORY_ROOT / _required_string(source, "source_tree")
    _verify_sha256(
        universe_path,
        _required_string(source, "task_universe_sha256"),
    )
    _verify_sha256(
        times_path,
        _required_string(source, "task_times_sha256"),
    )
    if _git(source_tree, "rev-parse", "HEAD").strip() != _required_string(
        source,
        "source_revision",
    ):
        raise ValueError("Multi-SWE source revision changed")

    repository_specs = _mapping_sequence(source, "repositories")
    repositories = {
        _required_string(item, "repository_id"): item for item in repository_specs
    }
    universe = {}
    for row in _load_json_lines(universe_path):
        repository_id = _required_string(row, "repository")
        if repository_id in repositories:
            instance_id = _required_string(row, "instance_id")
            if instance_id in universe:
                raise ValueError("duplicate Multi-SWE Task universe identity")
            universe[instance_id] = repository_id
    times = {}
    for row in _load_json_lines(times_path):
        instance_id = _required_string(row, "instance_id")
        if instance_id not in universe:
            continue
        if instance_id in times:
            raise ValueError("duplicate Multi-SWE Task time identity")
        times[instance_id] = _parse_utc(_required_string(row, "created_at"))
    if set(times) != set(universe):
        raise ValueError("Multi-SWE projected times changed")

    by_repository: dict[str, set[str]] = defaultdict(set)
    for instance_id, repository_id in universe.items():
        by_repository[repository_id].add(instance_id)
    projections = {}
    selected_files = []
    for repository_id, spec in repositories.items():
        relative_path = _required_string(spec, "source_path")
        source_path = source_tree / relative_path
        _verify_sha256(
            source_path,
            _required_string(spec, "source_sha256"),
        )
        if source_path.stat().st_size != _positive_integer(
            spec,
            "source_size_bytes",
        ):
            raise ValueError(f"Multi-SWE source size changed: {repository_id}")
        selected_files.append(
            {
                "repository_id": repository_id,
                "path": relative_path,
                "sha256": _sha256_file(source_path),
            }
        )
        wanted = by_repository[repository_id]
        for row in _load_json_lines(source_path):
            instance_id = _required_string(row, "instance_id")
            if instance_id not in wanted:
                continue
            if instance_id in projections:
                raise ValueError("duplicate Multi-SWE source Task identity")
            base = _mapping(row, "base")
            projections[instance_id] = common.TaskProjection(
                instance_id=instance_id,
                repository_id=repository_id,
                source_time=times[instance_id],
                base_commit=_required_string(base, "sha"),
                modules=thy2.modules_from_patch(
                    _required_string(row, "fix_patch"),
                    module_plan,
                ),
            )
    if set(projections) != set(universe):
        raise ValueError("Multi-SWE source rows are incomplete")
    tasks = tuple(
        sorted(
            projections.values(),
            key=lambda task: (
                task.repository_id.casefold(),
                task.source_time,
                task.instance_id,
            ),
        )
    )
    expected_count = _positive_integer(source, "task_count")
    if len(tasks) != expected_count:
        raise ValueError("Multi-SWE selected Task count changed")
    observed_counts: dict[str, int] = defaultdict(int)
    for task in tasks:
        observed_counts[task.repository_id] += 1
    if any(
        observed_counts[repository_id] != _positive_integer(spec, "expected_task_count")
        for repository_id, spec in repositories.items()
    ):
        raise ValueError("Multi-SWE repository Task counts changed")
    manifest: dict[str, object] = {
        "source_id": _required_string(source, "source_id"),
        "source_revision": _required_string(source, "source_revision"),
        "task_count": len(tasks),
        "repository_count": len(repositories),
        "task_universe_sha256": _sha256_file(universe_path),
        "task_times_sha256": _sha256_file(times_path),
        "selected_source_files": tuple(selected_files),
        "task_projection_digest": _task_projection_digest(tasks),
        "time_semantics": "projected GitHub pull-request createdAt",
        "label_semantics": "retrospective reference-fix patch modules",
    }
    manifest["source_manifest_digest"] = canonical_digest(manifest)
    return tasks, manifest


def run_task_space(
    plan: Mapping[str, object],
    repository_cache: Path,
) -> Mapping[str, Any]:
    """Materialize memberships and run the outcome-free source-alignment gate."""
    tasks, source_manifest = load_tasks(plan)
    source = _mapping(plan, "source")
    rolling = _mapping(plan, "rolling_origin")
    module_plan = _mapping(plan, "module_projection")
    candidate = _mapping(plan, "forecast")
    selector = _mapping(plan, "selector")
    budget = _positive_integer(selector, "budget_tasks")
    unseen_label = _required_string(module_plan, "unseen_label")
    origins_by_repository = common.build_origins(tasks, rolling)
    tasks_by_repository: dict[str, list[common.TaskProjection]] = defaultdict(list)
    for task in tasks:
        tasks_by_repository[task.repository_id].append(task)

    rows: list[Mapping[str, object]] = []
    membership_rows: list[Mapping[str, object]] = []
    runtimes: list[OriginRuntime] = []
    repository_manifests: list[Mapping[str, object]] = []
    admission_failures: list[Mapping[str, str]] = []
    for repository in _mapping_sequence(source, "repositories"):
        repository_id = _required_string(repository, "repository_id")
        origins = origins_by_repository.get(repository_id, ())
        expected_origin_count = _positive_integer(
            repository,
            "expected_origin_count",
        )
        local_repository = common.repository_path(repository_cache, repository_id)
        if len(origins) != expected_origin_count:
            admission_failures.append(
                {
                    "repository_id": repository_id,
                    "reason": (
                        "origin_count_changed:"
                        f"expected={expected_origin_count},observed={len(origins)}"
                    ),
                }
            )
            continue
        if not local_repository.is_dir():
            admission_failures.append(
                {
                    "repository_id": repository_id,
                    "reason": "repository_cache_missing",
                }
            )
            continue
        try:
            repository_rows = evaluate_repository(
                repository=repository,
                tasks=tuple(tasks_by_repository[repository_id]),
                origins=origins,
                local_repository=local_repository,
                module_plan=module_plan,
                half_life_days=_positive_number(
                    candidate,
                    "recent_half_life_days",
                ),
                prior_task_shape=_positive_number(
                    candidate,
                    "prior_task_shape",
                ),
                unseen_label=unseen_label,
                budget=budget,
                tie_domain=_required_string(selector, "tie_domain"),
            )
        except (OSError, subprocess.CalledProcessError, ValueError) as error:
            admission_failures.append(
                {
                    "repository_id": repository_id,
                    "reason": f"{type(error).__name__}: {error}",
                }
            )
            continue
        repo_rows, repo_memberships, repo_runtimes, manifest = repository_rows
        rows.extend(repo_rows)
        membership_rows.extend(repo_memberships)
        runtimes.extend(repo_runtimes)
        repository_manifests.append(manifest)

    repository_ids = tuple(
        _required_string(repository, "repository_id")
        for repository in _mapping_sequence(source, "repositories")
    )
    summary = summarize_rows(
        rows,
        expected_repositories=repository_ids,
        bootstrap_seed=_positive_integer(
            _mapping(plan, "task_space_gate"),
            "bootstrap_seed",
        ),
    )
    random_plan = _mapping(plan, "random_landscape")
    if admission_failures:
        random_raw = {
            "status": "not_run_due_source_admission",
            "membership_digest": canonical_digest(()),
            "draws": _positive_integer(random_plan, "draws"),
            "seed": _positive_integer(random_plan, "seed"),
            "chunk_size": _positive_integer(random_plan, "chunk_size"),
            "numpy_version": _required_string(
                random_plan,
                "numpy_version",
            ),
            "horizons": {"5": (), "10": ()},
        }
        random_summary = summarize_random(random_raw)
    else:
        random_raw = random_task_mix_calibration(
            runtimes,
            repository_ids=repository_ids,
            budget=budget,
            draws=_positive_integer(random_plan, "draws"),
            seed=_positive_integer(random_plan, "seed"),
            chunk_size=_positive_integer(random_plan, "chunk_size"),
            numpy_version=_required_string(
                random_plan,
                "numpy_version",
            ),
            unseen_label=unseen_label,
        )
        random_summary = bind_candidate_random_position(
            summarize_random(random_raw),
            task_space_summary=summary,
            random_raw=random_raw,
        )
    decision = decide_task_space(
        summary,
        random_summary=random_summary,
        expected_repository_count=len(repository_ids),
        admission_failures=admission_failures,
    )
    ordered_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                str(row["repository_id"]).casefold(),
                str(row["origin_id"]),
                _positive_integer(row, "horizon"),
            ),
        )
    )
    ordered_memberships = tuple(
        sorted(
            membership_rows,
            key=lambda row: (
                str(row["repository_id"]).casefold(),
                str(row["origin_id"]),
            ),
        )
    )
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "upstream_result_digest": _mapping(plan, "upstream_thy_002").get(
            "result_digest"
        ),
        "source_manifest": source_manifest,
        "repository_manifests": tuple(
            sorted(
                repository_manifests,
                key=lambda item: str(item["repository_id"]).casefold(),
            )
        ),
        "admission_failures": tuple(
            sorted(admission_failures, key=lambda item: item["repository_id"])
        ),
        "origin_rows": ordered_rows,
        "origin_rows_digest": canonical_digest(ordered_rows),
        "memberships": ordered_memberships,
        "memberships_digest": canonical_digest(ordered_memberships),
        "task_space_summary": summary,
        "random_landscape_raw": random_raw,
        "random_landscape_summary": random_summary,
        "decision": decision,
        "resource_use": {
            "paid_api_calls": 0,
            "embedding_calls": 0,
            "agent_outcomes_opened": 0,
            "sealed_holdout_opened": 0,
        },
        "claim_boundary": (
            "This front gate uses projected Task times, retrospective patch "
            "modules, and cutoff-safe Git state. It freezes memberships before "
            "any THY-002S Agent-outcome join and cannot establish response "
            "prediction or a production Selector."
        ),
    }
    result["result_digest"] = canonical_digest(result)
    return result


def evaluate_repository(
    *,
    repository: Mapping[str, object],
    tasks: Sequence[common.TaskProjection],
    origins: Sequence[common.OriginProjection],
    local_repository: Path,
    module_plan: Mapping[str, object],
    half_life_days: float,
    prior_task_shape: float,
    unseen_label: str,
    budget: int,
    tie_domain: str,
) -> tuple[
    tuple[Mapping[str, object], ...],
    tuple[Mapping[str, object], ...],
    tuple[OriginRuntime, ...],
    Mapping[str, object],
]:
    """Evaluate one repository without opening Agent outcomes."""
    repository_id = _required_string(repository, "repository_id")
    observed_head = _git(local_repository, "rev-parse", "HEAD").strip()
    if observed_head != _required_string(repository, "head_commit"):
        raise ValueError(f"pinned repository HEAD changed: {repository_id}")
    observation_start = min(task.source_time for task in tasks)
    origin_commits = {}
    for origin in origins:
        commit_id = _git(
            local_repository,
            "rev-list",
            "--first-parent",
            "--max-count=1",
            f"--before={_format_utc(origin.cutoff)}",
            "HEAD",
        ).strip()
        if not commit_id:
            raise ValueError(f"no Origin commit: {origin.origin_id}")
        origin_commits[origin.origin_id] = commit_id

    commit_sets = {}
    union_commits: set[str] = set()
    for origin in origins:
        commit_ids = thy2.reachable_exposure_commit_ids(
            local_repository,
            origin_commit=origin_commits[origin.origin_id],
            observation_start=observation_start,
        )
        if not commit_ids:
            raise ValueError(f"no exposure commits: {origin.origin_id}")
        commit_sets[origin.origin_id] = commit_ids
        union_commits.update(commit_ids)
    commit_index = thy2.load_commit_index(
        local_repository,
        union_commits,
        module_plan,
    )

    rows = []
    memberships = []
    runtimes = []
    origin_inputs = []
    for origin in origins:
        commits = tuple(
            commit_index[commit_id] for commit_id in commit_sets[origin.origin_id]
        )
        vocabulary = tuple(
            sorted(
                {
                    _required_string(module_plan, "root_label"),
                    unseen_label,
                    *(module for task in origin.history for module in task.modules),
                    *(module for commit in commits for module in commit.modules),
                }
            )
        )
        historical_exposure, future_dated = thy2.exposure_counts(
            commits,
            observation_start=observation_start,
            cutoff=origin.cutoff,
            half_life_days=None,
        )
        recent_exposure, recent_future_dated = thy2.exposure_counts(
            commits,
            observation_start=observation_start,
            cutoff=origin.cutoff,
            half_life_days=half_life_days,
        )
        if future_dated != recent_future_dated:
            raise AssertionError("Git anomaly counts disagree")
        history_counts = common.task_counts(
            origin.history,
            vocabulary,
            unseen_label=unseen_label,
        )
        forecast, forecast_diagnostics = thy2.calibrated_exposure_distribution(
            task_counts=history_counts,
            historical_exposure=historical_exposure,
            recent_exposure=recent_exposure,
            vocabulary=vocabulary,
            prior_task_shape=prior_task_shape,
        )
        full_distribution = thy2.probability_distribution(
            history_counts,
            vocabulary,
        )
        git_distribution = thy2.probability_distribution(
            recent_exposure,
            vocabulary,
        )
        yield_distribution = thy2.probability_distribution(
            {
                label: (history_counts.get(label, 0.0) + prior_task_shape)
                / (
                    historical_exposure.get(label, 0.0)
                    + forecast_diagnostics["prior_exposure_mass"]
                )
                for label in vocabulary
            },
            vocabulary,
        )
        candidate_selection, candidate_diagnostics = select_brier_projection(
            origin.history,
            forecast,
            vocabulary,
            unseen_label=unseen_label,
            budget=budget,
            tie_domain=f"{tie_domain}\0{repository_id}",
        )
        stationary_selection, stationary_diagnostics = select_brier_projection(
            origin.history,
            full_distribution,
            vocabulary,
            unseen_label=unseen_label,
            budget=budget,
            tie_domain=f"{tie_domain}/stationary\0{repository_id}",
        )
        recency_selection = tuple(origin.history[-budget:])
        selection_distributions = {
            "selection_candidate": task_distribution(
                candidate_selection,
                vocabulary,
                unseen_label=unseen_label,
            ),
            "selection_stationary": task_distribution(
                stationary_selection,
                vocabulary,
                unseen_label=unseen_label,
            ),
            "selection_recency": task_distribution(
                recency_selection,
                vocabulary,
                unseen_label=unseen_label,
            ),
        }
        predictor_probabilities = {
            "forecast": forecast,
            "task_full_history": full_distribution,
            "git_recent_touch": git_distribution,
            "yield_only": yield_distribution,
            **selection_distributions,
        }
        for horizon, future in ((5, origin.future_h5), (10, origin.future_h10)):
            losses = {
                predictor_id: thy2.brier_loss(
                    future,
                    probabilities,
                    vocabulary,
                    unseen_label=unseen_label,
                )
                for predictor_id, probabilities in predictor_probabilities.items()
            }
            rows.append(
                {
                    "repository_id": repository_id,
                    "origin_id": origin.origin_id,
                    "origin_cutoff": _format_utc(origin.cutoff),
                    "horizon": horizon,
                    "history_task_count": len(origin.history),
                    "future_task_count": len(future),
                    "vocabulary_size": len(vocabulary),
                    "losses": losses,
                }
            )
        membership = {
            "repository_id": repository_id,
            "origin_id": origin.origin_id,
            "origin_cutoff": _format_utc(origin.cutoff),
            "history_task_ids": tuple(task.instance_id for task in origin.history),
            "future_h5_task_ids": tuple(task.instance_id for task in origin.future_h5),
            "future_h10_task_ids": tuple(
                task.instance_id for task in origin.future_h10
            ),
            "candidate_task_ids": tuple(
                task.instance_id for task in candidate_selection
            ),
            "stationary_task_ids": tuple(
                task.instance_id for task in stationary_selection
            ),
            "recency_task_ids": tuple(task.instance_id for task in recency_selection),
            "candidate_diagnostics": candidate_diagnostics,
            "stationary_diagnostics": stationary_diagnostics,
            "forecast_diagnostics": forecast_diagnostics,
            "vocabulary_digest": canonical_digest(vocabulary),
        }
        membership["membership_digest"] = canonical_digest(membership)
        memberships.append(membership)
        runtimes.append(
            OriginRuntime(
                repository_id=repository_id,
                origin_id=origin.origin_id,
                history=tuple(origin.history),
                future_h5=tuple(origin.future_h5),
                future_h10=tuple(origin.future_h10),
                vocabulary=vocabulary,
            )
        )
        origin_inputs.append(
            {
                "origin_id": origin.origin_id,
                "origin_commit": origin_commits[origin.origin_id],
                "reachable_commit_digest": canonical_digest(
                    commit_sets[origin.origin_id]
                ),
                "membership_digest": membership["membership_digest"],
            }
        )

    manifest: dict[str, object] = {
        "repository_id": repository_id,
        "repository_head": observed_head,
        "source_head_ref": _required_string(repository, "head_ref"),
        "task_count": len(tasks),
        "origin_count": len(origins),
        "observation_start": _format_utc(observation_start),
        "origin_input_digest": canonical_digest(tuple(origin_inputs)),
        "commit_projection_digest": canonical_digest(
            tuple(
                (
                    commit.commit_id,
                    _format_utc(commit.committed_at),
                    commit.modules,
                )
                for commit in sorted(
                    commit_index.values(),
                    key=lambda item: item.commit_id,
                )
            )
        ),
    }
    manifest["repository_manifest_digest"] = canonical_digest(manifest)
    return (
        tuple(rows),
        tuple(memberships),
        tuple(runtimes),
        manifest,
    )


def summarize_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    expected_repositories: Sequence[str],
    bootstrap_seed: int,
) -> Mapping[str, object]:
    """Aggregate Task-mix loss at repository level."""
    repositories = tuple(expected_repositories)
    grouped: dict[tuple[int, str], list[Mapping[str, object]]] = defaultdict(list)
    seen: set[tuple[str, str, int]] = set()
    for row in rows:
        repository_id = _required_string(row, "repository_id")
        origin_id = _required_string(row, "origin_id")
        horizon = _positive_integer(row, "horizon")
        key = (repository_id, origin_id, horizon)
        if repository_id not in repositories or horizon not in (5, 10) or key in seen:
            raise ValueError("THY-002S Task-space row identity changed")
        seen.add(key)
        grouped[(horizon, repository_id)].append(row)
    origin_pairs: dict[tuple[str, str], set[int]] = defaultdict(set)
    for repository_id, origin_id, horizon in seen:
        origin_pairs[(repository_id, origin_id)].add(horizon)
    if any(horizons != {5, 10} for horizons in origin_pairs.values()):
        raise ValueError("THY-002S H5/H10 pairs are incomplete")

    horizons = {}
    for horizon in (5, 10):
        repository_rows = []
        for repository_id in repositories:
            origin_rows = grouped.get((horizon, repository_id), ())
            if not origin_rows:
                continue
            losses = {
                predictor_id: fsum(
                    _number(_mapping(row, "losses"), predictor_id)
                    for row in origin_rows
                )
                / len(origin_rows)
                for predictor_id in PREDICTOR_IDS
            }
            repository_rows.append(
                {
                    "repository_id": repository_id,
                    "origin_count": len(origin_rows),
                    "losses": losses,
                    "contrasts": {
                        "forecast_full": (
                            losses["forecast"] - losses["task_full_history"]
                        ),
                        "forecast_git": (
                            losses["forecast"] - losses["git_recent_touch"]
                        ),
                        "forecast_yield": (losses["forecast"] - losses["yield_only"]),
                        "selection_full": (
                            losses["selection_candidate"] - losses["task_full_history"]
                        ),
                        "selection_stationary": (
                            losses["selection_candidate"]
                            - losses["selection_stationary"]
                        ),
                        "selection_recency": (
                            losses["selection_candidate"] - losses["selection_recency"]
                        ),
                    },
                }
            )
        macro_losses = {
            predictor_id: (
                fsum(
                    _number(_mapping(row, "losses"), predictor_id)
                    for row in repository_rows
                )
                / len(repository_rows)
                if repository_rows
                else None
            )
            for predictor_id in PREDICTOR_IDS
        }
        contrasts = {}
        for contrast_id in (
            "forecast_full",
            "forecast_git",
            "forecast_yield",
            "selection_full",
            "selection_stationary",
            "selection_recency",
        ):
            values = tuple(
                _number(_mapping(row, "contrasts"), contrast_id)
                for row in repository_rows
            )
            contrasts[contrast_id] = {
                "macro_repository": (fsum(values) / len(values) if values else None),
                "favorable_repository_count": sum(value < 0.0 for value in values),
                "repository_count": len(values),
                "bootstrap_95_interval": (
                    _bootstrap_interval(
                        values,
                        draws=20000,
                        seed=_seed(bootstrap_seed, horizon, contrast_id),
                    )
                    if values
                    else None
                ),
                "leave_one_repository_out": (
                    tuple(
                        (fsum(values) - value) / (len(values) - 1) for value in values
                    )
                    if len(values) > 1
                    else ()
                ),
            }
        horizons[str(horizon)] = {
            "repository_count": len(repository_rows),
            "origin_count": sum(
                _positive_integer(row, "origin_count") for row in repository_rows
            ),
            "macro_losses": macro_losses,
            "contrasts": contrasts,
            "repositories": tuple(repository_rows),
        }
    return {
        "expected_repository_count": len(repositories),
        "horizons": horizons,
    }


def random_task_mix_calibration(
    runtimes: Sequence[OriginRuntime],
    *,
    repository_ids: Sequence[str],
    budget: int,
    draws: int,
    seed: int,
    chunk_size: int,
    numpy_version: str,
    unseen_label: str,
) -> Mapping[str, object]:
    """Place the deterministic subset in the uniform budget-10 landscape."""
    import numpy as np

    if np.__version__ != numpy_version:
        raise ValueError(
            f"NumPy version changed: expected {numpy_version}, got {np.__version__}"
        )
    if not runtimes:
        return {
            "membership_digest": canonical_digest(()),
            "draws": draws,
            "seed": seed,
            "chunk_size": chunk_size,
            "numpy_version": np.__version__,
            "horizons": {"5": (), "10": ()},
        }
    generator = np.random.default_rng(seed)
    repository_draws = {
        horizon: {
            repository_id: np.zeros(draws, dtype=np.float64)
            for repository_id in repository_ids
        }
        for horizon in (5, 10)
    }
    origin_counts: dict[str, int] = defaultdict(int)
    membership_hash = hashlib.sha256()
    for runtime in sorted(
        runtimes,
        key=lambda item: (item.repository_id.casefold(), item.origin_id),
    ):
        origin_counts[runtime.repository_id] += 1
        history = runtime.history
        vocabulary = runtime.vocabulary
        matrix = np.asarray(
            [
                [
                    common.task_module_mass(
                        task,
                        vocabulary,
                        unseen_label=unseen_label,
                    ).get(label, 0.0)
                    for label in vocabulary
                ]
                for task in history
            ],
            dtype=np.float64,
        )
        targets = {
            5: np.asarray(
                [
                    task_distribution(
                        runtime.future_h5,
                        vocabulary,
                        unseen_label=unseen_label,
                    )[label]
                    for label in vocabulary
                ],
                dtype=np.float64,
            ),
            10: np.asarray(
                [
                    task_distribution(
                        runtime.future_h10,
                        vocabulary,
                        unseen_label=unseen_label,
                    )[label]
                    for label in vocabulary
                ],
                dtype=np.float64,
            ),
        }
        full_distribution = matrix.mean(axis=0)
        full_losses = {
            horizon: float(((full_distribution - target) ** 2).sum())
            for horizon, target in targets.items()
        }
        membership_hash.update(runtime.repository_id.encode())
        membership_hash.update(b"\0")
        membership_hash.update(runtime.origin_id.encode())
        membership_hash.update(b"\0")
        membership_hash.update(
            canonical_digest(tuple(task.instance_id for task in history)).encode()
        )
        membership_hash.update(b"\0")
        for offset in range(0, draws, chunk_size):
            chunk = min(chunk_size, draws - offset)
            keys = generator.random((chunk, len(history)))
            chosen = np.argpartition(keys, budget - 1, axis=1)[:, :budget]
            chosen = np.sort(chosen, axis=1).astype("<i4", copy=False)
            membership_hash.update(chosen.tobytes())
            selected = matrix[chosen].mean(axis=1)
            for horizon, target in targets.items():
                losses = ((selected - target) ** 2).sum(axis=1)
                repository_draws[horizon][runtime.repository_id][
                    offset : offset + chunk
                ] += losses - full_losses[horizon]
    for horizon in (5, 10):
        for repository_id in repository_ids:
            repository_draws[horizon][repository_id] /= origin_counts[repository_id]
    return {
        "membership_digest": membership_hash.hexdigest(),
        "draws": draws,
        "seed": seed,
        "chunk_size": chunk_size,
        "numpy_version": np.__version__,
        "horizons": {
            str(horizon): tuple(
                np.mean(
                    np.stack(
                        [
                            repository_draws[horizon][repository_id]
                            for repository_id in repository_ids
                        ],
                        axis=0,
                    ),
                    axis=0,
                ).tolist()
            )
            for horizon in (5, 10)
        },
    }


def summarize_random(
    random_raw: Mapping[str, object],
) -> Mapping[str, object]:
    """Summarize committed global random draws without losing their raw parent."""
    horizons = {}
    for horizon in ("5", "10"):
        values = tuple(
            float(value)
            for value in _sequence(
                _mapping(random_raw, "horizons").get(horizon),
                f"random H{horizon}",
                allow_empty=True,
            )
        )
        if not values:
            horizons[horizon] = None
            continue
        ordered = tuple(sorted(values))
        horizons[horizon] = {
            "draw_count": len(values),
            "mean_macro_repository_difference": fsum(values) / len(values),
            "standard_deviation": (
                (
                    fsum((value - fsum(values) / len(values)) ** 2 for value in values)
                    / (len(values) - 1)
                )
                ** 0.5
                if len(values) > 1
                else 0.0
            ),
            "quantiles": {
                "0.10": ordered[int(0.10 * len(ordered))],
                "0.25": ordered[int(0.25 * len(ordered))],
                "0.50": ordered[int(0.50 * len(ordered))],
                "0.75": ordered[int(0.75 * len(ordered))],
                "0.90": ordered[int(0.90 * len(ordered))],
            },
        }
    return {
        "membership_digest": random_raw.get("membership_digest"),
        "draws": random_raw.get("draws"),
        "seed": random_raw.get("seed"),
        "chunk_size": random_raw.get("chunk_size"),
        "numpy_version": random_raw.get("numpy_version"),
        "horizons": horizons,
    }


def decide_task_space(
    summary: Mapping[str, object],
    *,
    random_summary: Mapping[str, object],
    expected_repository_count: int,
    admission_failures: Sequence[Mapping[str, str]],
) -> Mapping[str, object]:
    """Apply the frozen THY-002S-A source-alignment and mapping gate."""
    if admission_failures:
        return {
            "status": "data_blocked",
            "task_space_gate_passed": False,
            "outcome_executor_amendment_authorized": False,
            "gates": {"complete_source_admission": False},
        }
    horizons = _mapping(summary, "horizons")
    h5 = _mapping(horizons, "5")
    h10 = _mapping(horizons, "10")
    complete = (
        h5.get("repository_count") == expected_repository_count
        and h10.get("repository_count") == expected_repository_count
    )

    def contrast(
        item: Mapping[str, object],
        contrast_id: str,
    ) -> Mapping[str, Any]:
        return _mapping(_mapping(item, "contrasts"), contrast_id)

    def upper_below_zero(item: Mapping[str, object]) -> bool:
        interval = item.get("bootstrap_95_interval")
        return (
            isinstance(interval, Sequence)
            and not isinstance(interval, str)
            and len(interval) == 2
            and float(interval[1]) < 0.0
        )

    h5_forecast = contrast(h5, "forecast_full")
    h10_forecast = contrast(h10, "forecast_full")
    h5_selection = contrast(h5, "selection_full")
    h10_selection = contrast(h10, "selection_full")
    h5_random = _number(
        _mapping(_mapping(random_summary, "horizons"), "5"),
        "candidate_better_than_random_midrank",
    )
    h10_random = _number(
        _mapping(_mapping(random_summary, "horizons"), "10"),
        "candidate_better_than_random_midrank",
    )

    gates = {
        "complete_source_admission": complete,
        "h5_forecast_alignment": (
            _number(h5_forecast, "macro_repository") < 0.0
            and upper_below_zero(h5_forecast)
            and _positive_integer(
                h5_forecast,
                "favorable_repository_count",
                allow_zero=True,
            )
            >= 7
            and all(
                _number(contrast(h5, control), "macro_repository") < 0.0
                for control in ("forecast_git", "forecast_yield")
            )
        ),
        "h10_forecast_alignment": (
            _number(h10_forecast, "macro_repository") < 0.0
            and _positive_integer(
                h10_forecast,
                "favorable_repository_count",
                allow_zero=True,
            )
            >= 6
            and all(
                _number(contrast(h10, control), "macro_repository") < 0.0
                for control in ("forecast_git", "forecast_yield")
            )
        ),
        "h5_mapping_alignment": (
            _number(h5_selection, "macro_repository") < 0.0
            and upper_below_zero(h5_selection)
            and _positive_integer(
                h5_selection,
                "favorable_repository_count",
                allow_zero=True,
            )
            >= 7
            and all(
                value < 0.0
                for value in _sequence(
                    h5_selection.get("leave_one_repository_out"),
                    "H5 leave-one-repository",
                )
            )
            and _number(
                contrast(h5, "selection_stationary"),
                "macro_repository",
            )
            < 0.0
            and h5_random >= 0.90
        ),
        "h10_mapping_alignment": (
            _number(h10_selection, "macro_repository") < 0.0
            and _positive_integer(
                h10_selection,
                "favorable_repository_count",
                allow_zero=True,
            )
            >= 6
            and _number(
                contrast(h10, "selection_stationary"),
                "macro_repository",
            )
            < 0.0
            and h10_random >= 0.50
        ),
    }
    passed = all(gates.values())
    return {
        "status": "pass" if passed else "retire_mapping",
        "task_space_gate_passed": passed,
        "outcome_executor_amendment_authorized": passed,
        "gates": gates,
    }


def bind_candidate_random_position(
    random_summary: Mapping[str, object],
    *,
    task_space_summary: Mapping[str, object],
    random_raw: Mapping[str, object],
) -> Mapping[str, object]:
    """Add the frozen candidate's midrank position to random summaries."""
    result = dict(random_summary)
    horizons = dict(_mapping(result, "horizons"))
    raw_horizons = _mapping(random_raw, "horizons")
    task_horizons = _mapping(task_space_summary, "horizons")
    for horizon in ("5", "10"):
        item = dict(_mapping(horizons, horizon))
        values = tuple(
            float(value)
            for value in _sequence(
                raw_horizons.get(horizon),
                f"random H{horizon}",
            )
        )
        candidate = _number(
            _mapping(
                _mapping(_mapping(task_horizons, horizon), "contrasts"),
                "selection_full",
            ),
            "macro_repository",
        )
        better = sum(value > candidate for value in values)
        tied = sum(value == candidate for value in values)
        item["candidate_macro_repository_difference"] = candidate
        item["candidate_better_than_random_midrank"] = (better + 0.5 * tied) / len(
            values
        )
        item["random_as_good_or_better_rate"] = (
            sum(value <= candidate for value in values) - 0.5 * tied
        ) / len(values)
        horizons[horizon] = item
    result["horizons"] = horizons
    return result


def compact_result(
    result: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, object]:
    """Create the committed, outcome-free projection."""
    verify_result(result, plan)
    compact: dict[str, object] = {
        "schema_version": SUMMARY_SCHEMA,
        "study_id": result.get("study_id"),
        "plan_digest": result.get("plan_digest"),
        "result_digest": result.get("result_digest"),
        "origin_rows_digest": result.get("origin_rows_digest"),
        "memberships_digest": result.get("memberships_digest"),
        "source_manifest": result.get("source_manifest"),
        "repository_manifests": result.get("repository_manifests"),
        "admission_failures": result.get("admission_failures"),
        "task_space_summary": result.get("task_space_summary"),
        "random_landscape_summary": result.get("random_landscape_summary"),
        "decision": result.get("decision"),
        "resource_use": result.get("resource_use"),
        "claim_boundary": result.get("claim_boundary"),
    }
    compact["summary_digest"] = canonical_digest(compact)
    return compact


def verify_result(
    result: Mapping[str, object],
    plan: Mapping[str, object],
) -> None:
    """Replay row, random, decision, membership, and resource identities."""
    if result.get("schema_version") != RESULT_SCHEMA:
        raise ValueError("THY-002S result schema is unsupported")
    if (
        result.get("study_id") != plan.get("study_id")
        or result.get("plan_digest") != plan.get("plan_digest")
        or result.get("upstream_result_digest")
        != _mapping(plan, "upstream_thy_002").get("result_digest")
    ):
        raise ValueError("THY-002S result does not bind the plan")
    payload = dict(result)
    digest = payload.pop("result_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("THY-002S result digest does not match")
    rows = _mapping_sequence(result, "origin_rows")
    memberships = _mapping_sequence(result, "memberships")
    if result.get("origin_rows_digest") != canonical_digest(tuple(rows)):
        raise ValueError("THY-002S Origin rows digest changed")
    if result.get("memberships_digest") != canonical_digest(tuple(memberships)):
        raise ValueError("THY-002S memberships digest changed")
    source = _mapping(plan, "source")
    expected_tasks, expected_source_manifest = load_tasks(plan)
    if canonical_digest(result.get("source_manifest")) != canonical_digest(
        expected_source_manifest
    ):
        raise ValueError("THY-002S source projection does not replay")
    expected_origins = common.build_origins(
        expected_tasks,
        _mapping(plan, "rolling_origin"),
    )
    failures = tuple(
        {
            "repository_id": _required_string(item, "repository_id"),
            "reason": _required_string(item, "reason"),
        }
        for item in _mapping_sequence(result, "admission_failures")
    )
    failed_repository_ids = {item["repository_id"] for item in failures}
    if len(failed_repository_ids) != len(failures):
        raise ValueError("THY-002S duplicate admission failure")
    _verify_source_manifests(result, source)
    _verify_membership_rows(
        rows,
        memberships,
        source=source,
        selector=_mapping(plan, "selector"),
        rolling=_mapping(plan, "rolling_origin"),
        failed_repository_ids=failed_repository_ids,
        expected_origins=expected_origins,
    )
    repository_ids = tuple(
        _required_string(item, "repository_id")
        for item in _mapping_sequence(source, "repositories")
    )
    expected_summary = summarize_rows(
        rows,
        expected_repositories=repository_ids,
        bootstrap_seed=_positive_integer(
            _mapping(plan, "task_space_gate"),
            "bootstrap_seed",
        ),
    )
    if canonical_digest(result.get("task_space_summary")) != canonical_digest(
        expected_summary
    ):
        raise ValueError("THY-002S Task-space summary does not replay")
    random_raw = _mapping(result, "random_landscape_raw")
    random_plan = _mapping(plan, "random_landscape")
    expected_random_identity = {
        "draws": _positive_integer(random_plan, "draws"),
        "seed": _positive_integer(random_plan, "seed"),
        "chunk_size": _positive_integer(random_plan, "chunk_size"),
        "numpy_version": _required_string(random_plan, "numpy_version"),
    }
    if any(
        random_raw.get(key) != value for key, value in expected_random_identity.items()
    ):
        raise ValueError("THY-002S random calibration identity changed")
    if failures:
        if random_raw.get("status") != "not_run_due_source_admission":
            raise ValueError("THY-002S failed admission still ran random calibration")
        expected_random = summarize_random(random_raw)
    else:
        if "status" in random_raw:
            raise ValueError("THY-002S admitted source skipped random calibration")
        expected_random = bind_candidate_random_position(
            summarize_random(random_raw),
            task_space_summary=expected_summary,
            random_raw=random_raw,
        )
    if canonical_digest(result.get("random_landscape_summary")) != canonical_digest(
        expected_random
    ):
        raise ValueError("THY-002S random summary does not replay")
    expected_decision = decide_task_space(
        expected_summary,
        random_summary=expected_random,
        expected_repository_count=len(repository_ids),
        admission_failures=failures,
    )
    if result.get("decision") != expected_decision:
        raise ValueError("THY-002S decision does not replay")
    expected_resource = {
        key: _positive_integer(
            _mapping(plan, "resource_budget"),
            key,
            allow_zero=True,
        )
        for key in (
            "paid_api_calls",
            "embedding_calls",
            "agent_outcomes_opened",
            "sealed_holdout_opened",
        )
    }
    if _mapping(result, "resource_use") != expected_resource:
        raise ValueError("THY-002S resource boundary changed")


def _verify_source_manifests(
    result: Mapping[str, object],
    source: Mapping[str, object],
) -> None:
    manifest = _mapping(result, "source_manifest")
    manifest_payload = dict(manifest)
    manifest_digest = manifest_payload.pop("source_manifest_digest", None)
    if canonical_digest(manifest_payload) != manifest_digest:
        raise ValueError("THY-002S source manifest digest changed")
    expected_identity = {
        "source_id": _required_string(source, "source_id"),
        "source_revision": _required_string(source, "source_revision"),
        "task_count": _positive_integer(source, "task_count"),
        "repository_count": _positive_integer(source, "repository_count"),
        "task_universe_sha256": _required_string(
            source,
            "task_universe_sha256",
        ),
        "task_times_sha256": _required_string(source, "task_times_sha256"),
    }
    if any(manifest.get(key) != value for key, value in expected_identity.items()):
        raise ValueError("THY-002S source manifest identity changed")

    repository_spec_rows = _mapping_sequence(source, "repositories")
    repository_specs = {
        _required_string(item, "repository_id"): item for item in repository_spec_rows
    }
    selected_file_rows = _mapping_sequence(manifest, "selected_source_files")
    selected_files = {
        _required_string(item, "repository_id"): item for item in selected_file_rows
    }
    if (
        len(repository_specs) != len(repository_spec_rows)
        or len(selected_files) != len(selected_file_rows)
        or set(selected_files) != set(repository_specs)
    ):
        raise ValueError("THY-002S selected source file frame changed")
    for repository_id, spec in repository_specs.items():
        selected = selected_files[repository_id]
        if selected.get("path") != spec.get("source_path") or selected.get(
            "sha256"
        ) != spec.get("source_sha256"):
            raise ValueError("THY-002S selected source file identity changed")

    repository_manifest_rows = _mapping_sequence(
        result,
        "repository_manifests",
    )
    failure_rows = _mapping_sequence(result, "admission_failures")
    repository_manifests = {
        _required_string(item, "repository_id"): item
        for item in repository_manifest_rows
    }
    failure_ids = {_required_string(item, "repository_id") for item in failure_rows}
    if (
        len(repository_manifests) != len(repository_manifest_rows)
        or len(failure_ids) != len(failure_rows)
        or set(repository_manifests) | failure_ids != set(repository_specs)
    ):
        raise ValueError("THY-002S repository admission frame changed")
    if set(repository_manifests) & failure_ids:
        raise ValueError("THY-002S repository is both admitted and failed")
    for repository_id, item in repository_manifests.items():
        payload = dict(item)
        digest = payload.pop("repository_manifest_digest", None)
        if canonical_digest(payload) != digest:
            raise ValueError("THY-002S repository manifest digest changed")
        spec = repository_specs[repository_id]
        expected = {
            "repository_head": _required_string(spec, "head_commit"),
            "source_head_ref": _required_string(spec, "head_ref"),
            "task_count": _positive_integer(spec, "expected_task_count"),
            "origin_count": _positive_integer(spec, "expected_origin_count"),
        }
        if any(item.get(key) != value for key, value in expected.items()):
            raise ValueError("THY-002S repository manifest identity changed")


def _verify_membership_rows(
    rows: Sequence[Mapping[str, object]],
    memberships: Sequence[Mapping[str, object]],
    *,
    source: Mapping[str, object],
    selector: Mapping[str, object],
    rolling: Mapping[str, object],
    failed_repository_ids: set[str],
    expected_origins: Mapping[
        str,
        Sequence[common.OriginProjection],
    ]
    | None = None,
) -> None:
    budget = _positive_integer(selector, "budget_tasks")
    h5_size = _positive_integer(rolling, "primary_future_tasks")
    h10_size = _positive_integer(rolling, "sensitivity_future_tasks")
    repository_specs = {
        _required_string(item, "repository_id"): item
        for item in _mapping_sequence(source, "repositories")
    }
    expected_membership_keys = {
        (repository_id, f"{repository_id}:origin-{index:03d}")
        for repository_id, spec in repository_specs.items()
        for index in range(
            1,
            _positive_integer(spec, "expected_origin_count") + 1,
        )
    }
    expected_origin_by_key = (
        {
            (repository_id, origin.origin_id): origin
            for repository_id, origins in expected_origins.items()
            for origin in origins
        }
        if expected_origins is not None
        else {}
    )
    if expected_origins is not None and (
        set(expected_origin_by_key) != expected_membership_keys
    ):
        raise ValueError("THY-002S source Origin frame changed")
    membership_by_key = {}
    for membership in memberships:
        repository_id = _required_string(membership, "repository_id")
        origin_id = _required_string(membership, "origin_id")
        key = (repository_id, origin_id)
        if key in membership_by_key:
            raise ValueError("THY-002S duplicate membership")
        membership_by_key[key] = membership
        payload = dict(membership)
        digest = payload.pop("membership_digest", None)
        if canonical_digest(payload) != digest:
            raise ValueError("THY-002S membership digest changed")

        history = _string_sequence(membership, "history_task_ids")
        future_h5 = _string_sequence(membership, "future_h5_task_ids")
        future_h10 = _string_sequence(membership, "future_h10_task_ids")
        candidate = _string_sequence(membership, "candidate_task_ids")
        stationary = _string_sequence(membership, "stationary_task_ids")
        recency = _string_sequence(membership, "recency_task_ids")
        if (
            len(history) < budget
            or len(future_h5) != h5_size
            or len(future_h10) != h10_size
            or future_h10[:h5_size] != future_h5
            or len(set(history)) != len(history)
            or len(set(future_h10)) != len(future_h10)
            or set(history) & set(future_h10)
        ):
            raise ValueError("THY-002S Origin membership changed")
        if expected_origins is not None:
            expected_origin = expected_origin_by_key.get(key)
            if expected_origin is None or (
                membership.get("origin_cutoff") != _format_utc(expected_origin.cutoff)
                or history
                != tuple(task.instance_id for task in expected_origin.history)
                or future_h5
                != tuple(task.instance_id for task in expected_origin.future_h5)
                or future_h10
                != tuple(task.instance_id for task in expected_origin.future_h10)
            ):
                raise ValueError("THY-002S source Origin membership changed")
        for label, selected in (
            ("candidate", candidate),
            ("stationary", stationary),
            ("recency", recency),
        ):
            if (
                len(selected) != budget
                or len(set(selected)) != budget
                or not set(selected).issubset(history)
            ):
                raise ValueError(f"THY-002S {label} membership changed")
        if recency != history[-budget:]:
            raise ValueError("THY-002S recency control changed")
        for label, selected in (
            ("candidate", candidate),
            ("stationary", stationary),
        ):
            diagnostics = _mapping(membership, f"{label}_diagnostics")
            if diagnostics.get("budget") != budget or diagnostics.get(
                "selection_digest"
            ) != canonical_digest(tuple(selected)):
                raise ValueError(f"THY-002S {label} diagnostics changed")

    expected_for_admitted = {
        key for key in expected_membership_keys if key[0] not in failed_repository_ids
    }
    if set(membership_by_key) != expected_for_admitted:
        raise ValueError("THY-002S expected Origin memberships changed")

    row_keys = set()
    for row in rows:
        repository_id = _required_string(row, "repository_id")
        origin_id = _required_string(row, "origin_id")
        horizon = _positive_integer(row, "horizon")
        key = (repository_id, origin_id, horizon)
        if key in row_keys or (repository_id, origin_id) not in membership_by_key:
            raise ValueError("THY-002S row membership identity changed")
        row_keys.add(key)
        membership = membership_by_key[(repository_id, origin_id)]
        future = (
            _string_sequence(membership, "future_h5_task_ids")
            if horizon == 5
            else _string_sequence(membership, "future_h10_task_ids")
        )
        if (
            horizon not in (5, 10)
            or row.get("origin_cutoff") != membership.get("origin_cutoff")
            or row.get("history_task_count")
            != len(_string_sequence(membership, "history_task_ids"))
            or row.get("future_task_count") != len(future)
            or set(_mapping(row, "losses")) != set(PREDICTOR_IDS)
        ):
            raise ValueError("THY-002S row semantics changed")
    expected_row_keys = {
        (*key, horizon) for key in membership_by_key for horizon in (5, 10)
    }
    if row_keys != expected_row_keys:
        raise ValueError("THY-002S membership rows are incomplete")


def verify_summary(
    summary: Mapping[str, object],
    plan: Mapping[str, object],
    *,
    result: Mapping[str, object],
) -> None:
    if summary.get("schema_version") != SUMMARY_SCHEMA:
        raise ValueError("THY-002S summary schema is unsupported")
    payload = dict(summary)
    digest = payload.pop("summary_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("THY-002S summary digest changed")
    if canonical_digest(summary) != canonical_digest(compact_result(result, plan)):
        raise ValueError("THY-002S summary does not match its raw result")


def _bootstrap_interval(
    values: Sequence[float],
    *,
    draws: int,
    seed: int,
) -> tuple[float, float]:
    generator = random.Random(seed)
    count = len(values)
    means = sorted(
        fsum(values[generator.randrange(count)] for _ in range(count)) / count
        for _ in range(draws)
    )
    return means[int(0.025 * draws)], means[min(draws - 1, int(0.975 * draws))]


def _seed(base: int, horizon: int, label: str) -> int:
    payload = f"{horizon}\0{label}".encode()
    return base + int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def _task_projection_digest(
    tasks: Sequence[common.TaskProjection],
) -> str:
    return canonical_digest(
        tuple(
            {
                "instance_id": task.instance_id,
                "repository_id": task.repository_id,
                "source_time": _format_utc(task.source_time),
                "base_commit": task.base_commit,
                "modules": task.modules,
            }
            for task in tasks
        )
    )


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp lacks a zone: {value}")
    return parsed.astimezone(UTC)


def _format_utc(value: datetime) -> str:
    return (
        value.astimezone(UTC)
        .isoformat(timespec="microseconds")
        .replace(
            "+00:00",
            "Z",
        )
    )


def _git(repository: Path, *arguments: str) -> str:
    environment = dict(os.environ)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    completed = subprocess.run(
        ("git", "-C", str(repository), *arguments),
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return completed.stdout


def _load_json_lines(path: Path) -> Iterable[Mapping[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSON line {line_number}: {path}") from error
            if not isinstance(row, Mapping):
                raise ValueError(f"JSON line is not an object: {path}")
            yield row


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_sha256(path: Path, expected: str) -> None:
    if _sha256_file(path) != expected:
        raise ValueError(f"file SHA-256 changed: {path}")


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON object required: {path}")
    return payload


def _mapping(payload: Mapping[str, object], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return value


def _mapping_sequence(
    payload: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, Any], ...]:
    values = _sequence(payload.get(key), key)
    if any(not isinstance(item, Mapping) for item in values):
        raise ValueError(f"{key} must contain objects")
    return tuple(item for item in values if isinstance(item, Mapping))


def _string_sequence(
    payload: Mapping[str, object],
    key: str,
) -> tuple[str, ...]:
    values = _sequence(payload.get(key), key)
    if any(not isinstance(item, str) or not item for item in values):
        raise ValueError(f"{key} must contain nonempty strings")
    return tuple(item for item in values if isinstance(item, str))


def _sequence(
    value: object,
    label: str,
    *,
    allow_empty: bool = False,
) -> tuple[Any, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError(f"{label} must be a sequence")
    result = tuple(value)
    if not result and not allow_empty:
        raise ValueError(f"{label} must not be empty")
    return result


def _required_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a nonempty string")
    return value


def _positive_integer(
    payload: Mapping[str, object],
    key: str,
    *,
    allow_zero: bool = False,
) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    if value < 0 if allow_zero else value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def _positive_number(payload: Mapping[str, object], key: str) -> float:
    value = _number(payload, key)
    if value <= 0.0:
        raise ValueError(f"{key} must be positive")
    return value


def _number(payload: Mapping[str, object], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be numeric")
    result = float(value)
    if not (-float("inf") < result < float("inf")):
        raise ValueError(f"{key} must be finite")
    return result


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run-task-space")
    run_parser.add_argument(
        "--repository-cache",
        type=Path,
        default=DEFAULT_REPOSITORY_CACHE,
    )
    run_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--result", type=Path, default=DEFAULT_OUTPUT)
    verify_parser.add_argument("--summary", type=Path)

    compact_parser = subparsers.add_parser("compact")
    compact_parser.add_argument("--result", type=Path, default=DEFAULT_OUTPUT)
    compact_parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)

    arguments = parser.parse_args(argv)
    plan = load_plan(arguments.plan)
    if arguments.command == "run-task-space":
        result = run_task_space(plan, arguments.repository_cache)
        _write_json(arguments.output, result)
        print(canonical_json(result["decision"]))
    elif arguments.command == "verify":
        result = _load_mapping(arguments.result)
        verify_result(result, plan)
        if arguments.summary:
            verify_summary(
                _load_mapping(arguments.summary),
                plan,
                result=result,
            )
        print("verified")
    elif arguments.command == "compact":
        result = _load_mapping(arguments.result)
        summary = compact_result(result, plan)
        _write_json(arguments.summary, summary)
        print(canonical_json(summary["decision"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
