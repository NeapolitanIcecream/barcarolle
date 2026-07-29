#!/usr/bin/env python3
"""Run the frozen THY-001R counterfactual Task-mix kill test."""

from __future__ import annotations

# DuckDB is required only by the explicit run command.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json
from math import fsum, log
import os
from pathlib import Path, PurePosixPath
import random
import shlex
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "plan.json"
DEFAULT_OUTPUT = (
    REPOSITORY_ROOT
    / "outputs"
    / "research"
    / "2026-07-29-pre-origin-task-mix"
    / "task-mix-results.json"
)
DEFAULT_REPOSITORY_CACHE = DEFAULT_OUTPUT.parent / "repositories"
DEFAULT_SUMMARY = HERE / "evidence" / "task-mix-summary.json"

PLAN_SCHEMA = "barcarolle_pre_origin_task_mix_plan_v1"
RESULT_SCHEMA = "barcarolle_pre_origin_task_mix_results_v1"
SUMMARY_SCHEMA = "barcarolle_pre_origin_task_mix_summary_v1"
MARKER = "@@@BARCAROLLE_COMMIT@@@"
CONTROL_IDS = (
    "task_full_history",
    "task_trailing_h",
    "git_full_touch",
    "git_trailing_90d_touch",
    "uniform",
)


@dataclass(frozen=True)
class TaskProjection:
    instance_id: str
    repository_id: str
    source_time: datetime
    base_commit: str
    modules: tuple[str, ...]


@dataclass(frozen=True)
class OriginProjection:
    repository_id: str
    origin_id: str
    cutoff: datetime
    history: tuple[TaskProjection, ...]
    future_h5: tuple[TaskProjection, ...]
    future_h10: tuple[TaskProjection, ...]


@dataclass(frozen=True)
class CommitProjection:
    commit_id: str
    committed_at: datetime
    modules: tuple[str, ...]


def load_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    """Load and validate the frozen research plan."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("Task-mix plan schema is unsupported")
    digest = payload.get("plan_digest")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "plan_digest"}
    )
    if digest != expected:
        raise ValueError("Task-mix plan digest does not match")
    source_ids = tuple(
        _required_string(source, "source_id")
        for source in _mapping_sequence(payload, "sources")
    )
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Task-mix source IDs must be unique")
    if tuple(payload.get("controls", ())) != CONTROL_IDS:
        raise ValueError("Task-mix controls changed")
    return payload


def module_for_path(
    path: str,
    module_plan: Mapping[str, object],
) -> str | None:
    """Map one repository path to the fixed portable module vocabulary."""
    normalized = path.removeprefix("a/").removeprefix("b/").strip("/")
    if not normalized or normalized == "dev/null":
        return None
    pure = PurePosixPath(normalized)
    parts = pure.parts
    if not parts or any(part in {".", ".."} for part in parts):
        return None
    excluded_components = {
        item.casefold()
        for item in _string_sequence(
            module_plan.get("excluded_components"),
            "excluded components",
        )
    }
    if any(part.casefold() in excluded_components for part in parts):
        return None
    excluded_names = set(
        _string_sequence(
            module_plan.get("excluded_file_names"),
            "excluded file names",
        )
    )
    if parts[-1] in excluded_names:
        return None
    parent_parts = parts[:-1]
    if not parent_parts:
        return _required_string(module_plan, "root_label")
    depth = _positive_integer(module_plan, "depth")
    return "/".join(parent_parts[:depth])


def modules_from_patch(
    patch: str,
    module_plan: Mapping[str, object],
) -> tuple[str, ...]:
    """Project reference-patch paths into retrospective scoring labels."""
    modules: set[str] = set()
    for line in patch.splitlines():
        if not line.startswith("diff --git "):
            continue
        try:
            fields = shlex.split(line)
        except ValueError as error:
            raise ValueError("reference patch contains an invalid diff header") from error
        if len(fields) < 4:
            raise ValueError("reference patch contains a short diff header")
        for raw_path in fields[2:4]:
            module = module_for_path(raw_path, module_plan)
            if module is not None:
                modules.add(module)
    if not modules:
        modules.add(_required_string(module_plan, "unseen_label"))
    return tuple(sorted(modules))


def build_origins(
    tasks: Sequence[TaskProjection],
    rolling: Mapping[str, object],
) -> Mapping[str, tuple[OriginProjection, ...]]:
    """Build nested H5/H10 views from non-overlapping ten-Task blocks."""
    minimum_history = _positive_integer(
        rolling,
        "minimum_initial_history_tasks",
    )
    block_size = _positive_integer(rolling, "future_block_tasks")
    primary_size = _positive_integer(rolling, "primary_future_tasks")
    sensitivity_size = _positive_integer(
        rolling,
        "sensitivity_future_tasks",
    )
    if primary_size > block_size or sensitivity_size != block_size:
        raise ValueError("Task-mix horizons changed")
    by_repository: dict[str, list[TaskProjection]] = defaultdict(list)
    seen: set[str] = set()
    for task in tasks:
        if task.instance_id in seen:
            raise ValueError(f"duplicate Task projection: {task.instance_id}")
        seen.add(task.instance_id)
        by_repository[task.repository_id].append(task)

    result: dict[str, tuple[OriginProjection, ...]] = {}
    for repository_id, repository_tasks in sorted(by_repository.items()):
        ordered = tuple(
            sorted(
                repository_tasks,
                key=lambda item: (item.source_time, item.instance_id),
            )
        )
        if len(ordered) < minimum_history + block_size:
            continue
        initial_history = minimum_history + (
            (len(ordered) - minimum_history) % block_size
        )
        origins = []
        for offset, start in enumerate(
            range(initial_history, len(ordered), block_size),
            start=1,
        ):
            future = ordered[start : start + block_size]
            if len(future) != block_size:
                raise ValueError("Task-mix block is incomplete")
            history = ordered[:start]
            origins.append(
                OriginProjection(
                    repository_id=repository_id,
                    origin_id=f"{repository_id}:origin-{offset:03d}",
                    cutoff=history[-1].source_time,
                    history=history,
                    future_h5=future[:primary_size],
                    future_h10=future,
                )
            )
        result[repository_id] = tuple(origins)
    return result


def smoothed_distribution(
    counts: Mapping[str, float],
    vocabulary: Sequence[str],
    *,
    smoothing: float,
) -> Mapping[str, float]:
    """Normalize nonnegative module mass with fixed additive smoothing."""
    labels = tuple(vocabulary)
    if (
        not labels
        or len(labels) != len(set(labels))
        or smoothing <= 0.0
        or any(value < 0.0 for value in counts.values())
    ):
        raise ValueError("module distribution inputs are invalid")
    denominator = fsum(counts.get(label, 0.0) for label in labels) + (
        smoothing * len(labels)
    )
    return {
        label: (counts.get(label, 0.0) + smoothing) / denominator
        for label in labels
    }


def task_module_mass(
    task: TaskProjection,
    vocabulary: Sequence[str],
    *,
    unseen_label: str,
) -> Mapping[str, float]:
    """Map one potentially multi-module Task into an Origin vocabulary."""
    vocabulary_set = set(vocabulary)
    if unseen_label not in vocabulary_set or not task.modules:
        raise ValueError("Task module vocabulary is invalid")
    mass: dict[str, float] = defaultdict(float)
    weight = 1.0 / len(task.modules)
    for module in task.modules:
        mass[module if module in vocabulary_set else unseen_label] += weight
    return dict(mass)


def task_counts(
    tasks: Sequence[TaskProjection],
    vocabulary: Sequence[str],
    *,
    unseen_label: str,
) -> Mapping[str, float]:
    """Aggregate unit-weight Task module distributions."""
    counts: dict[str, float] = defaultdict(float)
    for task in tasks:
        for module, weight in task_module_mass(
            task,
            vocabulary,
            unseen_label=unseen_label,
        ).items():
            counts[module] += weight
    return dict(counts)


def git_counts(
    commits: Iterable[CommitProjection],
    *,
    cutoff: datetime,
    half_life_days: float | None,
    trailing_days: float | None = None,
) -> tuple[Mapping[str, float], int]:
    """Aggregate commit-level module touches under one frozen time kernel."""
    counts: dict[str, float] = defaultdict(float)
    future_dated = 0
    for commit in commits:
        age = cutoff - commit.committed_at
        if age.total_seconds() < 0:
            future_dated += 1
            age = timedelta(0)
        if trailing_days is not None and age > timedelta(days=trailing_days):
            continue
        weight = (
            1.0
            if half_life_days is None
            else 2.0 ** (-age.total_seconds() / (half_life_days * 86400.0))
        )
        if not commit.modules:
            continue
        module_weight = weight / len(commit.modules)
        for module in commit.modules:
            counts[module] += module_weight
    return dict(counts), future_dated


def git_vocabulary(
    commits: Iterable[CommitProjection],
    *,
    module_plan: Mapping[str, object],
    unseen_label: str,
) -> tuple[str, ...]:
    """Build the candidate vocabulary without retrospective Task labels."""
    return tuple(
        sorted(
            {
                _required_string(module_plan, "root_label"),
                unseen_label,
                *(module for commit in commits for module in commit.modules),
            }
        )
    )


def future_horizon_span_days(
    cutoff: datetime,
    future: Sequence[TaskProjection],
) -> float:
    """Measure the future horizon from the Origin cutoff to its last Task."""
    if not future:
        raise ValueError("future Task cohort must not be empty")
    span = future[-1].source_time - cutoff
    if span.total_seconds() < 0:
        raise ValueError("future Task cohort precedes its Origin cutoff")
    return span.total_seconds() / 86400.0


def future_loss(
    future: Sequence[TaskProjection],
    probabilities: Mapping[str, float],
    vocabulary: Sequence[str],
    *,
    unseen_label: str,
) -> float:
    """Compute mean future-Task cross-entropy."""
    if not future:
        raise ValueError("future Task cohort must not be empty")
    values = []
    for task in future:
        mass = task_module_mass(
            task,
            vocabulary,
            unseen_label=unseen_label,
        )
        values.append(-fsum(weight * log(probabilities[label]) for label, weight in mass.items()))
    return fsum(values) / len(values)


def future_total_variation(
    future: Sequence[TaskProjection],
    probabilities: Mapping[str, float],
    vocabulary: Sequence[str],
    *,
    unseen_label: str,
) -> float:
    """Compare a forecast with the empirical future Task-module mix."""
    empirical_counts = task_counts(
        future,
        vocabulary,
        unseen_label=unseen_label,
    )
    denominator = float(len(future))
    return 0.5 * fsum(
        abs(probabilities[label] - empirical_counts.get(label, 0.0) / denominator)
        for label in vocabulary
    )


def prepare_repositories(
    plan: Mapping[str, object],
    repository_cache: Path,
) -> tuple[Mapping[str, object], ...]:
    """Clone the exact planned repositories into an ignored blobless cache."""
    repository_cache.mkdir(parents=True, exist_ok=True)
    manifests = []
    for repository_id in _planned_repositories(plan):
        target = repository_path(repository_cache, repository_id)
        if not target.exists():
            _run_process(
                (
                    "git",
                    "clone",
                    "--bare",
                    "--filter=blob:none",
                    "--single-branch",
                    "--no-tags",
                    f"https://github.com/{repository_id}.git",
                    str(target),
                )
            )
        head = _git(target, "rev-parse", "HEAD").strip()
        symbolic_head = _git(target, "symbolic-ref", "HEAD").strip()
        remote = _git(target, "remote", "get-url", "origin").strip()
        manifests.append(
            {
                "repository_id": repository_id,
                "head_commit": head,
                "head_ref": symbolic_head,
                "remote_url": remote,
            }
        )
    return tuple(manifests)


def repository_path(repository_cache: Path, repository_id: str) -> Path:
    """Return the stable local bare-repository path."""
    return repository_cache / f"{repository_id.replace('/', '__')}.git"


def run_study(
    plan: Mapping[str, object],
    repository_cache: Path,
) -> Mapping[str, Any]:
    """Run the frozen source projections and composition comparisons."""
    source_specs = {
        _required_string(source, "source_id"): source
        for source in _mapping_sequence(plan, "sources")
    }
    module_plan = _mapping(plan, "module_projection")
    rolling = _mapping(plan, "rolling_origin")
    candidate = _mapping(plan, "candidate")
    smoothing = _positive_number(candidate, "smoothing_per_module")
    half_life_days = _positive_number(candidate, "half_life_days")
    unseen_label = _required_string(module_plan, "unseen_label")

    task_sets, source_manifests = load_task_sets(plan)
    all_rows: list[Mapping[str, object]] = []
    repository_manifests: list[Mapping[str, object]] = []
    admission_failures: list[Mapping[str, str]] = []

    for source_id, source in source_specs.items():
        tasks = task_sets[source_id]
        origins_by_repository = build_origins(tasks, rolling)
        expected_repositories = _string_sequence(
            source.get("repositories"),
            f"{source_id} repositories",
        )
        for repository_id in expected_repositories:
            origins = origins_by_repository.get(repository_id, ())
            if not origins:
                admission_failures.append(
                    {
                        "source_id": source_id,
                        "repository_id": repository_id,
                        "reason": "no_complete_origin",
                    }
                )
                continue
            local_repository = repository_path(repository_cache, repository_id)
            if not local_repository.is_dir():
                admission_failures.append(
                    {
                        "source_id": source_id,
                        "repository_id": repository_id,
                        "reason": "repository_cache_missing",
                    }
                )
                continue
            try:
                rows, manifest = evaluate_repository(
                    source_id=source_id,
                    repository_id=repository_id,
                    origins=origins,
                    local_repository=local_repository,
                    module_plan=module_plan,
                    smoothing=smoothing,
                    half_life_days=half_life_days,
                    unseen_label=unseen_label,
                )
            except (OSError, subprocess.CalledProcessError, ValueError) as error:
                admission_failures.append(
                    {
                        "source_id": source_id,
                        "repository_id": repository_id,
                        "reason": f"{type(error).__name__}: {error}",
                    }
                )
                continue
            all_rows.extend(rows)
            repository_manifests.append(manifest)

    expected_by_source = {
        source_id: tuple(
            _string_sequence(
                source.get("repositories"),
                f"{source_id} repositories",
            )
        )
        for source_id, source in source_specs.items()
    }
    summaries = summarize_rows(
        all_rows,
        expected_by_source=expected_by_source,
        bootstrap_seed=_positive_integer(_mapping(plan, "metrics"), "bootstrap_seed"),
    )
    decision = decide(
        summaries,
        admission_failures=admission_failures,
    )
    ordered_rows = tuple(
        sorted(
            all_rows,
            key=lambda row: (
                str(row["source_id"]),
                str(row["repository_id"]),
                str(row["origin_id"]),
                _positive_integer(row, "horizon"),
            ),
        )
    )
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "source_manifests": source_manifests,
        "repository_manifests": tuple(
            sorted(
                repository_manifests,
                key=lambda item: (
                    str(item["source_id"]),
                    str(item["repository_id"]),
                ),
            )
        ),
        "admission_failures": tuple(
            sorted(
                admission_failures,
                key=lambda item: (
                    item["source_id"],
                    item["repository_id"],
                ),
            )
        ),
        "origin_rows": ordered_rows,
        "origin_rows_digest": canonical_digest(ordered_rows),
        "source_summaries": summaries,
        "decision": decision,
        "resource_use": {
            "paid_api_calls": 0,
            "embedding_calls": 0,
            "agent_outcomes_opened": 0,
            "sealed_holdout_opened": 0,
        },
        "claim_boundary": (
            "Retrospective patch labels and declared PR times support only "
            "generator-conditional counterfactual development. They do not "
            "establish native Task arrival, strict prospective validity, or "
            "external confirmation."
        ),
    }
    result["result_digest"] = canonical_digest(result)
    return result


def load_task_sets(
    plan: Mapping[str, object],
) -> tuple[Mapping[str, tuple[TaskProjection, ...]], tuple[Mapping[str, object], ...]]:
    """Load the exact source-specific Task frames without Agent outcomes."""
    task_sets: dict[str, tuple[TaskProjection, ...]] = {}
    manifests = []
    module_plan = _mapping(plan, "module_projection")
    for source in _mapping_sequence(plan, "sources"):
        source_id = _required_string(source, "source_id")
        if source_id == "multi_swe_bench":
            tasks, manifest = _load_multi_swe_tasks(source, module_plan)
        elif source_id == "swe_bench_full":
            tasks, manifest = _load_swe_bench_full_tasks(source, module_plan)
        else:
            raise ValueError(f"unsupported Task-mix source: {source_id}")
        expected_repositories = set(
            _string_sequence(
                source.get("repositories"),
                f"{source_id} repositories",
            )
        )
        observed_repositories = {task.repository_id for task in tasks}
        if observed_repositories != expected_repositories:
            raise ValueError(f"{source_id} Task frame repositories changed")
        task_sets[source_id] = tasks
        manifests.append(manifest)
    return task_sets, tuple(manifests)


def _load_multi_swe_tasks(
    source: Mapping[str, object],
    module_plan: Mapping[str, object],
) -> tuple[tuple[TaskProjection, ...], Mapping[str, object]]:
    universe_path = REPOSITORY_ROOT / _required_string(source, "task_universe")
    times_path = REPOSITORY_ROOT / _required_string(source, "task_times")
    source_tree = REPOSITORY_ROOT / _required_string(source, "source_tree")
    repositories = set(
        _string_sequence(source.get("repositories"), "Multi-SWE repositories")
    )

    universe: dict[str, str] = {}
    for row in _load_json_lines(universe_path):
        repository_id = _required_string(row, "repository")
        if repository_id in repositories:
            instance_id = _required_string(row, "instance_id")
            universe[instance_id] = repository_id
    times = {
        _required_string(row, "instance_id"): _parse_utc(
            _required_string(row, "created_at")
        )
        for row in _load_json_lines(times_path)
        if _required_string(row, "instance_id") in universe
    }
    if set(times) != set(universe):
        raise ValueError("Multi-SWE time projection is incomplete")

    by_repository: dict[str, set[str]] = defaultdict(set)
    for instance_id, repository_id in universe.items():
        by_repository[repository_id].add(instance_id)
    projected: dict[str, TaskProjection] = {}
    selected_files = []
    for repository_id in sorted(repositories):
        expected_name = f"{repository_id.replace('/', '__')}_dataset.jsonl"
        matches = tuple(source_tree.rglob(expected_name))
        if len(matches) != 1:
            raise ValueError(f"Multi-SWE source file is ambiguous: {repository_id}")
        source_path = matches[0]
        selected_files.append(
            {
                "repository_id": repository_id,
                "path": str(source_path.relative_to(source_tree)),
                "sha256": _sha256_file(source_path),
            }
        )
        wanted = by_repository[repository_id]
        for row in _load_json_lines(source_path):
            instance_id = _required_string(row, "instance_id")
            if instance_id not in wanted:
                continue
            base = _mapping(row, "base")
            projected[instance_id] = TaskProjection(
                instance_id=instance_id,
                repository_id=repository_id,
                source_time=times[instance_id],
                base_commit=_required_string(base, "sha"),
                modules=modules_from_patch(
                    _required_string(row, "fix_patch"),
                    module_plan,
                ),
            )
    if set(projected) != set(universe):
        raise ValueError("Multi-SWE source rows are incomplete")
    tasks = tuple(
        sorted(
            projected.values(),
            key=lambda item: (
                item.repository_id,
                item.source_time,
                item.instance_id,
            ),
        )
    )
    source_head = _git(source_tree, "rev-parse", "HEAD").strip()
    manifest = {
        "source_id": "multi_swe_bench",
        "task_count": len(tasks),
        "repository_count": len(repositories),
        "source_revision": source_head,
        "task_universe_sha256": _sha256_file(universe_path),
        "task_times_sha256": _sha256_file(times_path),
        "selected_source_files": tuple(selected_files),
        "task_projection_digest": _task_projection_digest(tasks),
        "time_semantics": "projected_pull_request_created_at",
        "label_semantics": "retrospective_reference_fix_patch_paths",
    }
    manifest["source_manifest_digest"] = canonical_digest(manifest)
    return tasks, manifest


def _load_swe_bench_full_tasks(
    source: Mapping[str, object],
    module_plan: Mapping[str, object],
) -> tuple[tuple[TaskProjection, ...], Mapping[str, object]]:
    try:
        import duckdb
    except ImportError as error:
        raise RuntimeError(
            "DuckDB is required; run the study with `uv run --with duckdb`"
        ) from error

    parquet_path = REPOSITORY_ROOT / _required_string(source, "parquet")
    verified_path = REPOSITORY_ROOT / _required_string(
        source,
        "primary_frame_exclusion_source",
    )
    _verify_sha256(
        parquet_path,
        _required_string(source, "parquet_sha256"),
    )
    _verify_sha256(
        verified_path,
        _required_string(source, "primary_frame_exclusion_sha256"),
    )
    connection = duckdb.connect()
    full_rows = connection.execute(
        """
        SELECT repo, instance_id, base_commit, patch, created_at
        FROM read_parquet(?)
        ORDER BY repo, created_at, instance_id
        """,
        [str(parquet_path)],
    ).fetchall()
    verified_ids = {
        str(row[0])
        for row in connection.execute(
            "SELECT instance_id FROM read_parquet(?)",
            [str(verified_path)],
        ).fetchall()
    }
    connection.close()

    repositories = set(
        _string_sequence(source.get("repositories"), "SWE-bench repositories")
    )
    tasks = []
    excluded_count = 0
    for repository_id, instance_id, base_commit, patch, created_at in full_rows:
        if str(instance_id) in verified_ids:
            excluded_count += 1
            continue
        if str(repository_id) not in repositories:
            continue
        tasks.append(
            TaskProjection(
                instance_id=str(instance_id),
                repository_id=str(repository_id),
                source_time=_parse_utc(str(created_at)),
                base_commit=str(base_commit),
                modules=modules_from_patch(str(patch), module_plan),
            )
        )
    ordered = tuple(
        sorted(
            tasks,
            key=lambda item: (
                item.repository_id,
                item.source_time,
                item.instance_id,
            ),
        )
    )
    manifest = {
        "source_id": "swe_bench_full",
        "task_count": len(ordered),
        "repository_count": len(repositories),
        "full_parquet_sha256": _sha256_file(parquet_path),
        "verified_exclusion_sha256": _sha256_file(verified_path),
        "verified_task_ids_excluded": excluded_count,
        "task_projection_digest": _task_projection_digest(ordered),
        "time_semantics": "pull_request_created_at",
        "label_semantics": "retrospective_gold_fix_patch_paths",
        "source_relationship": (
            "SWE-bench Full minus the exact SWE-bench Verified Task IDs; "
            "same Generator family, not independent confirmation"
        ),
    }
    manifest["source_manifest_digest"] = canonical_digest(manifest)
    return ordered, manifest


def evaluate_repository(
    *,
    source_id: str,
    repository_id: str,
    origins: Sequence[OriginProjection],
    local_repository: Path,
    module_plan: Mapping[str, object],
    smoothing: float,
    half_life_days: float,
    unseen_label: str,
) -> tuple[tuple[Mapping[str, object], ...], Mapping[str, object]]:
    """Evaluate all frozen Origins for one repository."""
    head = _git(local_repository, "rev-parse", "HEAD").strip()
    head_ref = _git(local_repository, "symbolic-ref", "HEAD").strip()
    origin_commits: dict[str, str] = {}
    for origin in origins:
        cutoff = origin.cutoff.astimezone(UTC).isoformat().replace("+00:00", "Z")
        commit_id = _git(
            local_repository,
            "rev-list",
            "--first-parent",
            "--max-count=1",
            f"--before={cutoff}",
            "HEAD",
        ).strip()
        if not commit_id:
            raise ValueError(f"no default-branch Origin commit for {origin.origin_id}")
        origin_commits[origin.origin_id] = commit_id

    commit_sets: dict[str, tuple[str, ...]] = {}
    union_commits: set[str] = set()
    for origin in origins:
        commit_ids = tuple(
            line
            for line in _git(
                local_repository,
                "rev-list",
                "--no-merges",
                "--min-parents=1",
                origin_commits[origin.origin_id],
            ).splitlines()
            if line
        )
        commit_sets[origin.origin_id] = commit_ids
        union_commits.update(commit_ids)
    commit_index = _load_commit_index(
        local_repository,
        union_commits,
        module_plan,
    )

    rows = []
    origin_input_rows = []
    for origin in origins:
        commits = tuple(
            commit_index[commit_id]
            for commit_id in commit_sets[origin.origin_id]
        )
        vocabulary = git_vocabulary(
            commits,
            module_plan=module_plan,
            unseen_label=unseen_label,
        )
        candidate_counts, future_dated = git_counts(
            commits,
            cutoff=origin.cutoff,
            half_life_days=half_life_days,
        )
        full_git_counts, _ = git_counts(
            commits,
            cutoff=origin.cutoff,
            half_life_days=None,
        )
        trailing_git_counts, _ = git_counts(
            commits,
            cutoff=origin.cutoff,
            half_life_days=None,
            trailing_days=90.0,
        )
        for horizon, future in (
            (5, origin.future_h5),
            (10, origin.future_h10),
        ):
            predictor_counts = {
                "candidate": candidate_counts,
                "task_full_history": task_counts(
                    origin.history,
                    vocabulary,
                    unseen_label=unseen_label,
                ),
                "task_trailing_h": task_counts(
                    origin.history[-horizon:],
                    vocabulary,
                    unseen_label=unseen_label,
                ),
                "git_full_touch": full_git_counts,
                "git_trailing_90d_touch": trailing_git_counts,
                "uniform": {},
            }
            losses = {}
            total_variations = {}
            for predictor_id, counts in predictor_counts.items():
                probabilities = smoothed_distribution(
                    counts,
                    vocabulary,
                    smoothing=smoothing,
                )
                losses[predictor_id] = future_loss(
                    future,
                    probabilities,
                    vocabulary,
                    unseen_label=unseen_label,
                )
                total_variations[predictor_id] = future_total_variation(
                    future,
                    probabilities,
                    vocabulary,
                    unseen_label=unseen_label,
                )
            rows.append(
                {
                    "source_id": source_id,
                    "repository_id": repository_id,
                    "origin_id": origin.origin_id,
                    "origin_cutoff": _format_utc(origin.cutoff),
                    "origin_commit": origin_commits[origin.origin_id],
                    "horizon": horizon,
                    "history_task_count": len(origin.history),
                    "future_task_count": len(future),
                    "future_calendar_span_days": future_horizon_span_days(
                        origin.cutoff,
                        future,
                    ),
                    "vocabulary_size": len(vocabulary),
                    "future_other_mass": fsum(
                        task_module_mass(
                            task,
                            vocabulary,
                            unseen_label=unseen_label,
                        ).get(unseen_label, 0.0)
                        for task in future
                    )
                    / len(future),
                    "future_dated_reachable_commit_count": future_dated,
                    "losses": losses,
                    "total_variations": total_variations,
                }
            )
        origin_input_rows.append(
            {
                "origin_id": origin.origin_id,
                "origin_cutoff": _format_utc(origin.cutoff),
                "origin_commit": origin_commits[origin.origin_id],
                "history_task_ids": tuple(task.instance_id for task in origin.history),
                "future_task_ids": tuple(
                    task.instance_id for task in origin.future_h10
                ),
                "reachable_commit_digest": canonical_digest(
                    commit_sets[origin.origin_id]
                ),
            }
        )
    manifest: dict[str, Any] = {
        "source_id": source_id,
        "repository_id": repository_id,
        "repository_head": head,
        "repository_head_ref": head_ref,
        "origin_count": len(origins),
        "origin_input_digest": canonical_digest(tuple(origin_input_rows)),
        "commit_projection_digest": canonical_digest(
            tuple(
                (
                    item.commit_id,
                    _format_utc(item.committed_at),
                    item.modules,
                )
                for item in sorted(
                    commit_index.values(),
                    key=lambda item: item.commit_id,
                )
            )
        ),
    }
    manifest["repository_manifest_digest"] = canonical_digest(manifest)
    return tuple(rows), manifest


def _load_commit_index(
    repository: Path,
    commit_ids: Iterable[str],
    module_plan: Mapping[str, object],
) -> Mapping[str, CommitProjection]:
    ordered_ids = tuple(sorted(set(commit_ids)))
    if not ordered_ids:
        raise ValueError("repository Origin has no eligible commit history")
    output = _git(
        repository,
        "show",
        "--stdin",
        "--no-walk=unsorted",
        f"--format={MARKER}%H%x09%ct",
        "--name-only",
        "--no-renames",
        input_text="\n".join(ordered_ids) + "\n",
    )
    index: dict[str, CommitProjection] = {}
    current_id: str | None = None
    current_time: datetime | None = None
    paths: list[str] = []

    def flush() -> None:
        if current_id is None or current_time is None:
            return
        modules = {
            module
            for path in paths
            if (module := module_for_path(path, module_plan)) is not None
        }
        index[current_id] = CommitProjection(
            commit_id=current_id,
            committed_at=current_time,
            modules=tuple(sorted(modules)),
        )

    for line in output.splitlines():
        if line.startswith(MARKER):
            flush()
            payload = line.removeprefix(MARKER)
            fields = payload.split("\t")
            if len(fields) != 2:
                raise ValueError("Git commit marker is malformed")
            current_id = fields[0]
            current_time = datetime.fromtimestamp(int(fields[1]), tz=UTC)
            paths = []
        elif line and current_id is not None:
            paths.append(line)
    flush()
    missing = set(ordered_ids) - set(index)
    if missing:
        raise ValueError(f"Git commit projection missed {len(missing)} objects")
    return index


def summarize_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    expected_by_source: Mapping[str, Sequence[str]],
    bootstrap_seed: int,
) -> Mapping[str, Any]:
    """Aggregate Origin rows to repository-first source summaries."""
    by_source_horizon_repository: dict[
        tuple[str, int, str],
        list[Mapping[str, object]],
    ] = defaultdict(list)
    for row in rows:
        by_source_horizon_repository[
            (
                _required_string(row, "source_id"),
                _positive_integer(row, "horizon"),
                _required_string(row, "repository_id"),
            )
        ].append(row)

    result: dict[str, Any] = {}
    for source_id, expected_repositories in expected_by_source.items():
        horizons: dict[str, Any] = {}
        for horizon in (5, 10):
            repository_rows = []
            for repository_id in expected_repositories:
                origin_rows = by_source_horizon_repository.get(
                    (source_id, horizon, repository_id),
                    (),
                )
                if not origin_rows:
                    continue
                predictor_losses = {
                    predictor_id: fsum(
                        _number(_mapping(row, "losses"), predictor_id)
                        for row in origin_rows
                    )
                    / len(origin_rows)
                    for predictor_id in ("candidate", *CONTROL_IDS)
                }
                repository_rows.append(
                    {
                        "repository_id": repository_id,
                        "origin_count": len(origin_rows),
                        "losses": predictor_losses,
                        "contrasts": {
                            control_id: (
                                predictor_losses["candidate"]
                                - predictor_losses[control_id]
                            )
                            for control_id in CONTROL_IDS
                        },
                        "mean_future_calendar_span_days": fsum(
                            _number(row, "future_calendar_span_days")
                            for row in origin_rows
                        )
                        / len(origin_rows),
                        "mean_future_other_mass": fsum(
                            _number(row, "future_other_mass") for row in origin_rows
                        )
                        / len(origin_rows),
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
                for predictor_id in ("candidate", *CONTROL_IDS)
            }
            contrasts = {}
            for control_id in CONTROL_IDS:
                values = tuple(
                    _number(_mapping(row, "contrasts"), control_id)
                    for row in repository_rows
                )
                contrasts[control_id] = {
                    "macro_repository": fsum(values) / len(values)
                    if values
                    else None,
                    "favorable_repository_count": sum(value < 0.0 for value in values),
                    "repository_count": len(values),
                    "bootstrap_95_interval": _bootstrap_interval(
                        values,
                        draws=20000,
                        seed=_control_seed(bootstrap_seed, source_id, horizon, control_id),
                    )
                    if values
                    else None,
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
        result[source_id] = {
            "expected_repository_count": len(tuple(expected_repositories)),
            "horizons": horizons,
        }
    return result


def decide(
    summaries: Mapping[str, object],
    *,
    admission_failures: Sequence[Mapping[str, str]],
) -> Mapping[str, object]:
    """Apply the exact preregistered pass-or-retire gate."""
    if admission_failures:
        return {
            "status": "data_blocked",
            "task_mix_gate_passed": False,
            "agent_outcome_replay_authorized": False,
            "gates": {
                "complete_source_admission": False,
            },
        }

    multi = _mapping(summaries, "multi_swe_bench")
    full = _mapping(summaries, "swe_bench_full")
    multi_h5 = _mapping(_mapping(multi, "horizons"), "5")
    multi_h10 = _mapping(_mapping(multi, "horizons"), "10")
    full_h5 = _mapping(_mapping(full, "horizons"), "5")
    full_h10 = _mapping(_mapping(full, "horizons"), "10")

    complete_source_admission = (
        multi_h5.get("repository_count") == 11
        and full_h5.get("repository_count") == 10
        and multi_h10.get("repository_count") == 11
        and full_h10.get("repository_count") == 10
    )
    multi_h5_contrasts = _mapping(multi_h5, "contrasts")
    full_h5_contrasts = _mapping(full_h5, "contrasts")
    primary_source_h5 = (
        complete_source_admission
        and all(
            _number(_mapping(multi_h5_contrasts, control_id), "macro_repository")
            < 0.0
            for control_id in CONTROL_IDS
        )
        and _positive_integer(
            _mapping(multi_h5_contrasts, "task_full_history"),
            "favorable_repository_count",
            allow_zero=True,
        )
        >= 7
    )
    transfer_source_h5 = (
        complete_source_admission
        and all(
            _number(_mapping(full_h5_contrasts, control_id), "macro_repository")
            < 0.0
            for control_id in ("task_full_history", "task_trailing_h")
        )
        and _positive_integer(
            _mapping(full_h5_contrasts, "task_full_history"),
            "favorable_repository_count",
            allow_zero=True,
        )
        >= 6
    )
    h10_sensitivity = complete_source_admission and all(
        _number(
            _mapping(_mapping(summary, "contrasts"), control_id),
            "macro_repository",
        )
        < 0.0
        for summary in (multi_h10, full_h10)
        for control_id in ("task_full_history", "task_trailing_h")
    )
    passed = primary_source_h5 and transfer_source_h5 and h10_sensitivity
    return {
        "status": "pass" if passed else "retire",
        "task_mix_gate_passed": passed,
        "agent_outcome_replay_authorized": passed,
        "gates": {
            "complete_source_admission": complete_source_admission,
            "primary_source_h5": primary_source_h5,
            "same_family_robustness_h5": transfer_source_h5,
            "h10_sensitivity": h10_sensitivity,
        },
    }


def compact_result(
    result: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, object]:
    """Build the small committed evidence projection."""
    verify_result(result, plan)
    compact: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "study_id": result.get("study_id"),
        "plan_digest": result.get("plan_digest"),
        "result_digest": result.get("result_digest"),
        "origin_rows_digest": result.get("origin_rows_digest"),
        "source_manifests": result.get("source_manifests"),
        "repository_manifests": result.get("repository_manifests"),
        "admission_failures": result.get("admission_failures"),
        "source_summaries": result.get("source_summaries"),
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
    """Verify result identity and mechanically recompute summaries and gates."""
    if result.get("schema_version") != RESULT_SCHEMA:
        raise ValueError("Task-mix result schema is unsupported")
    if result.get("plan_digest") != plan.get("plan_digest"):
        raise ValueError("Task-mix result does not bind the plan")
    payload = dict(result)
    digest = payload.pop("result_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("Task-mix result digest does not match")
    rows = _mapping_sequence(result, "origin_rows")
    if result.get("origin_rows_digest") != canonical_digest(tuple(rows)):
        raise ValueError("Task-mix Origin rows digest does not match")
    expected_by_source = {
        _required_string(source, "source_id"): _string_sequence(
            source.get("repositories"),
            "planned repositories",
        )
        for source in _mapping_sequence(plan, "sources")
    }
    expected_summaries = summarize_rows(
        rows,
        expected_by_source=expected_by_source,
        bootstrap_seed=_positive_integer(_mapping(plan, "metrics"), "bootstrap_seed"),
    )
    if canonical_digest(result.get("source_summaries")) != canonical_digest(
        expected_summaries
    ):
        raise ValueError("Task-mix source summaries do not replay")
    failures = tuple(
        {
            key: str(value)
            for key, value in _mapping(item, "admission failure").items()
        }
        for item in _mapping_sequence(result, "admission_failures")
    )
    if result.get("decision") != decide(
        expected_summaries,
        admission_failures=failures,
    ):
        raise ValueError("Task-mix decision does not replay")


def verify_summary(
    summary: Mapping[str, object],
    plan: Mapping[str, object],
    *,
    result: Mapping[str, object] | None = None,
) -> None:
    """Verify the compact committed evidence projection."""
    if summary.get("schema_version") != SUMMARY_SCHEMA:
        raise ValueError("Task-mix summary schema is unsupported")
    if summary.get("plan_digest") != plan.get("plan_digest"):
        raise ValueError("Task-mix summary does not bind the plan")
    payload = dict(summary)
    digest = payload.pop("summary_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("Task-mix summary digest does not match")
    if result is not None and canonical_digest(summary) != canonical_digest(
        compact_result(result, plan)
    ):
        raise ValueError("Task-mix summary does not match the raw result")


def _bootstrap_interval(
    values: Sequence[float],
    *,
    draws: int,
    seed: int,
) -> tuple[float, float]:
    if not values or draws <= 0:
        raise ValueError("bootstrap inputs are invalid")
    generator = random.Random(seed)
    count = len(values)
    means = sorted(
        fsum(values[generator.randrange(count)] for _ in range(count)) / count
        for _ in range(draws)
    )
    lower = means[int(0.025 * draws)]
    upper = means[min(draws - 1, int(0.975 * draws))]
    return (lower, upper)


def _control_seed(
    base_seed: int,
    source_id: str,
    horizon: int,
    control_id: str,
) -> int:
    payload = f"{source_id}\0{horizon}\0{control_id}".encode()
    return base_seed + int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def _task_projection_digest(tasks: Sequence[TaskProjection]) -> str:
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


def _planned_repositories(plan: Mapping[str, object]) -> tuple[str, ...]:
    repositories = {
        repository_id
        for source in _mapping_sequence(plan, "sources")
        for repository_id in _string_sequence(
            source.get("repositories"),
            "planned repositories",
        )
    }
    return tuple(sorted(repositories))


def _git(
    repository: Path,
    *arguments: str,
    input_text: str | None = None,
) -> str:
    return _run_process(
        ("git", "-C", str(repository), *arguments),
        input_text=input_text,
    )


def _run_process(
    arguments: Sequence[str],
    *,
    input_text: str | None = None,
) -> str:
    environment = dict(os.environ)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    completed = subprocess.run(
        tuple(arguments),
        input=input_text,
        text=True,
        check=True,
        capture_output=True,
        env=environment,
    )
    return completed.stdout


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"invalid timestamp: {value}") from error
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp lacks timezone: {value}")
    return parsed.astimezone(UTC)


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace(
        "+00:00",
        "Z",
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_sha256(path: Path, expected: str) -> None:
    observed = _sha256_file(path)
    if observed != expected:
        raise ValueError(f"source SHA-256 changed: {path}")


def _load_json_lines(path: Path) -> Iterable[Mapping[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid JSONL at {path}:{line_number}"
                ) from error
            if not isinstance(payload, Mapping):
                raise ValueError(f"JSONL row is not an object: {path}:{line_number}")
            yield payload


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON file must contain an object: {path}")
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
) -> tuple[Mapping[str, Any], ...]:
    value = payload.get(key)
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError(f"{key} must be a sequence")
    rows = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"{key} entries must be objects")
        rows.append(item)
    return tuple(rows)


def _required_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a nonempty string")
    return value


def _string_sequence(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError(f"{label} must be a string sequence")
    items = tuple(value)
    if (
        not items
        or any(not isinstance(item, str) or not item for item in items)
        or len(items) != len(set(items))
    ):
        raise ValueError(f"{label} must contain unique nonempty strings")
    return items  # type: ignore[return-value]


def _positive_integer(
    payload: Mapping[str, object],
    key: str,
    *,
    allow_zero: bool = False,
) -> int:
    value = payload.get(key)
    minimum = 0 if allow_zero else 1
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{key} must be an integer >= {minimum}")
    return value


def _number(payload: Mapping[str, object], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _positive_number(payload: Mapping[str, object], key: str) -> float:
    value = _number(payload, key)
    if value <= 0.0:
        raise ValueError(f"{key} must be positive")
    return value


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare-repositories")
    prepare_parser.add_argument(
        "--repository-cache",
        type=Path,
        default=DEFAULT_REPOSITORY_CACHE,
    )

    run_parser = subparsers.add_parser("run")
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
    if arguments.command == "prepare-repositories":
        manifests = prepare_repositories(plan, arguments.repository_cache)
        print(canonical_json({"repositories": manifests}))
    elif arguments.command == "run":
        result = run_study(plan, arguments.repository_cache)
        _write_json(arguments.output, result)
        print(canonical_json(result["decision"]))
    elif arguments.command == "verify":
        result = _load_mapping(arguments.result)
        verify_result(result, plan)
        if arguments.summary is not None:
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
    else:
        raise AssertionError("unreachable Task-mix command")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
