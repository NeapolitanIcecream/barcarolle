#!/usr/bin/env python3
"""Run the frozen THY-002 generator-calibrated module-exposure test."""

from __future__ import annotations

# DuckDB is required only by source-loading run commands.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
import hashlib
import json
from math import fsum
import os
from pathlib import Path
from pathlib import PurePosixPath
import random
import re
import shlex
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.pre_origin_task_mix import study as common  # noqa: E402


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "plan.json"
DEFAULT_OUTPUT = (
    REPOSITORY_ROOT
    / "outputs"
    / "research"
    / "2026-07-29-generator-calibrated-exposure"
    / "task-mix-results.json"
)
DEFAULT_REPOSITORY_CACHE = DEFAULT_OUTPUT.parent / "repositories"
DEFAULT_SUMMARY = HERE / "evidence" / "task-mix-summary.json"

PLAN_SCHEMA = "barcarolle_generator_calibrated_exposure_plan_v1"
RESULT_SCHEMA = "barcarolle_generator_calibrated_exposure_results_v1"
SUMMARY_SCHEMA = "barcarolle_generator_calibrated_exposure_summary_v1"
PREDICTOR_IDS = (
    "candidate",
    "task_full_history",
    "git_recent_touch",
    "yield_only",
    "task_trailing_h",
    "uniform",
)
CONTROL_IDS = PREDICTOR_IDS[1:]
PR_URL = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repository>[^/]+)/pull/"
    r"(?P<number>[0-9]+)/?$",
    re.IGNORECASE,
)
COMMIT_MARKER = "@@@BARCAROLLE_THY2_COMMIT@@@"


def load_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    """Load and verify the complete frozen THY-002 contract."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("THY-002 plan schema is unsupported")
    digest = payload.get("plan_digest")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "plan_digest"}
    )
    if digest != expected:
        raise ValueError("THY-002 plan digest does not match")
    if tuple(payload.get("predictors", ())) != PREDICTOR_IDS:
        raise ValueError("THY-002 predictors changed")
    repositories = _mapping_sequence(_mapping(payload, "source"), "repositories")
    repository_ids = tuple(
        _required_string(repository, "repository_id")
        for repository in repositories
    )
    if len(repository_ids) != len(set(repository_ids)):
        raise ValueError("THY-002 canonical repositories are not unique")
    aliases = tuple(
        alias
        for repository in repositories
        for alias in _string_sequence(repository.get("source_aliases"), "source aliases")
    )
    if len(aliases) != len(set(aliases)):
        raise ValueError("THY-002 source aliases overlap")
    for item in _mapping_sequence(payload, "implementation"):
        relative_path = _required_string(item, "path")
        _verify_sha256(
            REPOSITORY_ROOT / relative_path,
            _required_string(item, "sha256"),
        )
    return payload


def canonical_task_id(
    *,
    repository_id: str,
    source_instance_id: str,
    pull_request_url: str | None,
    source_alias: str | None = None,
) -> str:
    """Derive one stable identity across source-slug repository renames."""
    if pull_request_url:
        match = PR_URL.fullmatch(pull_request_url)
        if match is None:
            raise ValueError(f"unsupported pull-request URL: {pull_request_url}")
        pull_request_repository = (
            f"{match.group('owner')}/{match.group('repository')}"
        )
        if (
            source_alias is not None
            and pull_request_repository.casefold()
            not in {source_alias.casefold(), repository_id.casefold()}
        ):
            raise ValueError(
                "pull-request repository disagrees with source lineage: "
                f"{pull_request_repository} not in "
                f"({source_alias}, {repository_id})"
            )
        return f"{repository_id}#pr-{match.group('number')}"
    return source_instance_id


def probability_distribution(
    counts: Mapping[str, float],
    vocabulary: Sequence[str],
) -> Mapping[str, float]:
    """Normalize finite nonnegative mass without adding an arbitrary epsilon."""
    labels = tuple(vocabulary)
    if not labels or len(labels) != len(set(labels)):
        raise ValueError("probability vocabulary is invalid")
    if any(value < 0.0 for value in counts.values()):
        raise ValueError("probability mass must be nonnegative")
    total = fsum(counts.get(label, 0.0) for label in labels)
    if total <= 0.0:
        raise ValueError("probability mass is zero")
    return {label: counts.get(label, 0.0) / total for label in labels}


def calibrated_exposure_distribution(
    *,
    task_counts: Mapping[str, float],
    historical_exposure: Mapping[str, float],
    recent_exposure: Mapping[str, float],
    vocabulary: Sequence[str],
    prior_task_shape: float,
) -> tuple[Mapping[str, float], Mapping[str, float]]:
    """Apply fixed repository-scale empirical Task-per-touch shrinkage."""
    if prior_task_shape <= 0.0:
        raise ValueError("prior task shape must be positive")
    total_tasks = fsum(task_counts.get(label, 0.0) for label in vocabulary)
    total_exposure = fsum(
        historical_exposure.get(label, 0.0) for label in vocabulary
    )
    if total_tasks <= 0.0 or total_exposure <= 0.0:
        raise ValueError("calibration history has no Task or Git exposure")
    repository_rate = total_tasks / total_exposure
    prior_exposure = prior_task_shape / repository_rate
    yields = {
        label: (
            task_counts.get(label, 0.0) + prior_task_shape
        )
        / (historical_exposure.get(label, 0.0) + prior_exposure)
        for label in vocabulary
    }
    scores = {
        label: recent_exposure.get(label, 0.0) * yields[label]
        for label in vocabulary
    }
    probabilities = probability_distribution(scores, vocabulary)
    diagnostics = {
        "repository_task_per_touch_rate": repository_rate,
        "prior_exposure_mass": prior_exposure,
        "recent_exposure_mass": fsum(recent_exposure.values()),
        "historical_exposure_mass": total_exposure,
        "task_positive_zero_historical_exposure_module_count": float(
            sum(
                task_counts.get(label, 0.0) > 0.0
                and historical_exposure.get(label, 0.0) == 0.0
                for label in vocabulary
            )
        ),
        "task_mass_on_zero_historical_exposure_modules": fsum(
            task_counts.get(label, 0.0)
            for label in vocabulary
            if historical_exposure.get(label, 0.0) == 0.0
        ),
    }
    return probabilities, diagnostics


def brier_loss(
    future: Sequence[common.TaskProjection],
    probabilities: Mapping[str, float],
    vocabulary: Sequence[str],
    *,
    unseen_label: str,
) -> float:
    """Compute the mean quadratic proper score for fractional Task labels."""
    if not future:
        raise ValueError("future Task cohort must not be empty")
    values = []
    for task in future:
        target = common.task_module_mass(
            task,
            vocabulary,
            unseen_label=unseen_label,
        )
        values.append(
            fsum(
                (probabilities[label] - target.get(label, 0.0)) ** 2
                for label in vocabulary
            )
        )
    return fsum(values) / len(values)


def exposure_counts(
    commits: Iterable[common.CommitProjection],
    *,
    observation_start: datetime,
    cutoff: datetime,
    half_life_days: float | None,
) -> tuple[Mapping[str, float], int]:
    """Count eligible touches inside the fixed source observation window."""
    eligible = tuple(
        commit
        for commit in commits
        if commit.committed_at >= observation_start
    )
    return common.git_counts(
        eligible,
        cutoff=cutoff,
        half_life_days=half_life_days,
    )


def module_for_repository_path(
    path: str,
    module_plan: Mapping[str, object],
) -> str | None:
    """Map one path already relative to the repository root."""
    normalized = path.strip("/")
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
    """Project diff paths after removing exactly one a/ or b/ side prefix."""
    modules: set[str] = set()
    for line in patch.splitlines():
        if not line.startswith("diff --git "):
            continue
        for side, raw_path in zip(("a/", "b/"), _diff_header_paths(line), strict=True):
            if not raw_path.startswith(side):
                raise ValueError("reference patch path has the wrong diff-side prefix")
            module = module_for_repository_path(raw_path[2:], module_plan)
            if module is not None:
                modules.add(module)
    if not modules:
        modules.add(_required_string(module_plan, "unseen_label"))
    return tuple(sorted(modules))


def _diff_header_paths(line: str) -> tuple[str, str]:
    payload = line.removeprefix("diff --git ")
    if payload.startswith('"'):
        try:
            paths = tuple(shlex.split(payload))
        except ValueError as error:
            raise ValueError("reference patch contains an invalid diff header") from error
        if len(paths) != 2:
            raise ValueError("quoted diff header does not contain two paths")
        return paths[0], paths[1]
    separator = " b/"
    if not payload.startswith("a/") or separator not in payload:
        raise ValueError("reference patch contains an unsupported diff header")
    old_path, new_suffix = payload.split(separator, maxsplit=1)
    return old_path, f"b/{new_suffix}"


def load_commit_index(
    repository: Path,
    commit_ids: Iterable[str],
    module_plan: Mapping[str, object],
) -> Mapping[str, common.CommitProjection]:
    """Project Git --name-only paths without treating a/ or b/ as diff sides."""
    ordered_ids = tuple(sorted(set(commit_ids)))
    if not ordered_ids:
        raise ValueError("repository Origin has no eligible commit history")
    output = _run_process(
        (
            "git",
            "-C",
            str(repository),
            "show",
            "--stdin",
            "--no-walk=unsorted",
            f"--format={COMMIT_MARKER}%H%x09%ct",
            "--name-only",
            "--no-renames",
            "-z",
        ),
        input_text="\n".join(ordered_ids) + "\n",
    )
    index: dict[str, common.CommitProjection] = {}
    current_id: str | None = None
    current_time: datetime | None = None
    paths: list[str] = []
    first_path_after_header = False

    def flush() -> None:
        if current_id is None or current_time is None:
            return
        modules = {
            module
            for path in paths
            if (
                module := module_for_repository_path(path, module_plan)
            )
            is not None
        }
        index[current_id] = common.CommitProjection(
            commit_id=current_id,
            committed_at=current_time,
            modules=tuple(sorted(modules)),
        )

    for token in output.split("\0"):
        if token.startswith(COMMIT_MARKER):
            flush()
            fields = token.removeprefix(COMMIT_MARKER).split("\t")
            if len(fields) != 2:
                raise ValueError("Git commit marker is malformed")
            current_id = fields[0]
            current_time = datetime.fromtimestamp(int(fields[1]), tz=UTC)
            paths = []
            first_path_after_header = True
            continue
        if current_id is None:
            if token:
                raise ValueError("Git path appeared before a commit marker")
            continue
        path = token
        if first_path_after_header:
            if not path.startswith("\n"):
                raise ValueError("Git commit header lacks its NUL path separator")
            path = path[1:]
            first_path_after_header = False
        if path:
            paths.append(path)
    flush()
    missing = set(ordered_ids) - set(index)
    if missing:
        raise ValueError(f"Git commit projection missed {len(missing)} objects")
    return index


def reachable_exposure_commit_ids(
    repository: Path,
    *,
    origin_commit: str,
    observation_start: datetime,
) -> tuple[str, ...]:
    """Enumerate the full reachable DAG before filtering commit timestamps."""
    since = _format_utc(observation_start)
    return tuple(
        line
        for line in _git(
            repository,
            "rev-list",
            "--no-merges",
            "--min-parents=1",
            f"--since-as-filter={since}",
            origin_commit,
        ).splitlines()
        if line
    )


def prepare_repositories(
    plan: Mapping[str, object],
    repository_cache: Path,
) -> tuple[Mapping[str, object], ...]:
    """Materialize every pinned canonical repository without replacement."""
    repository_cache.mkdir(parents=True, exist_ok=True)
    repositories = _mapping_sequence(_mapping(plan, "source"), "repositories")
    workers = _positive_integer(
        _mapping(plan, "resource_budget"),
        "repository_prepare_concurrency",
    )
    with ThreadPoolExecutor(max_workers=workers) as executor:
        manifests = tuple(
            executor.map(
                lambda repository: _prepare_repository(
                    repository,
                    repository_cache,
                ),
                repositories,
            )
        )
    return tuple(
        sorted(manifests, key=lambda item: str(item["repository_id"]).casefold())
    )


def _prepare_repository(
    repository: Mapping[str, object],
    repository_cache: Path,
) -> Mapping[str, object]:
    repository_id = _required_string(repository, "repository_id")
    remote_url = _required_string(repository, "remote_url")
    head_ref = _required_string(repository, "head_ref")
    head_commit = _required_string(repository, "head_commit")
    branch = head_ref.removeprefix("refs/heads/")
    if not branch or branch == head_ref:
        raise ValueError(f"repository head ref is not a branch: {repository_id}")
    target = common.repository_path(repository_cache, repository_id)
    if not target.exists():
        _run_process(
            (
                "git",
                "clone",
                "--bare",
                "--filter=blob:none",
                "--single-branch",
                "--no-tags",
                "--branch",
                branch,
                remote_url,
                str(target),
            )
        )
    observed_remote = _git(target, "remote", "get-url", "origin").strip()
    if observed_remote != remote_url:
        raise ValueError(f"repository remote changed: {repository_id}")
    try:
        _git(target, "cat-file", "-e", f"{head_commit}^{{commit}}")
    except subprocess.CalledProcessError:
        _run_process(("git", "-C", str(target), "fetch", "origin", head_commit))
        _git(target, "cat-file", "-e", f"{head_commit}^{{commit}}")
    frozen_ref = "refs/heads/barcarolle-frozen"
    _git(target, "update-ref", frozen_ref, head_commit)
    _git(target, "symbolic-ref", "HEAD", frozen_ref)
    _git(target, "fsck", "--connectivity-only")
    return {
        "repository_id": repository_id,
        "remote_url": observed_remote,
        "source_head_ref": head_ref,
        "frozen_head_commit": _git(target, "rev-parse", "HEAD").strip(),
    }


def load_tasks(
    plan: Mapping[str, object],
) -> tuple[
    tuple[common.TaskProjection, ...],
    Mapping[str, object],
    Mapping[str, tuple[Mapping[str, str], ...]],
]:
    """Load only the pinned Rebench frame and deduplicate canonical PRs."""
    try:
        import duckdb
    except ImportError as error:
        raise RuntimeError(
            "DuckDB is required; run with `uv run --with duckdb`"
        ) from error

    source = _mapping(plan, "source")
    module_plan = _mapping(plan, "module_projection")
    parquet_path = REPOSITORY_ROOT / _required_string(source, "parquet")
    if parquet_path.stat().st_size != _positive_integer(
        source,
        "parquet_size_bytes",
    ):
        raise ValueError("Rebench parquet size changed")
    _verify_sha256(parquet_path, _required_string(source, "parquet_sha256"))
    repositories = _mapping_sequence(source, "repositories")
    alias_to_repository = {
        alias: _required_string(repository, "repository_id")
        for repository in repositories
        for alias in _string_sequence(repository.get("source_aliases"), "source aliases")
    }
    aliases = tuple(sorted(alias_to_repository))
    expected_alias_count = _positive_integer(source, "source_alias_count")
    expected_repository_count = _positive_integer(
        source,
        "canonical_repository_count",
    )
    if len(aliases) != expected_alias_count:
        raise ValueError("Rebench frozen source-alias count changed")
    if len(repositories) != expected_repository_count:
        raise ValueError("Rebench frozen canonical-repository count changed")
    connection = duckdb.connect()
    minimum_source_rows = _positive_integer(source, "frame_minimum_source_rows")
    observed_frame_rows = connection.execute(
        """
        SELECT repo, count(*) AS source_row_count
        FROM read_parquet(?)
        GROUP BY repo
        HAVING count(*) >= ?
        ORDER BY lower(repo), repo
        """,
        [str(parquet_path), minimum_source_rows],
    ).fetchall()
    observed_frame_aliases = tuple(str(row[0]) for row in observed_frame_rows)
    if set(observed_frame_aliases) != set(aliases):
        raise ValueError("Rebench repositories passing the frame rule changed")
    rows = connection.execute(
        """
        SELECT
          repo,
          instance_id,
          base_commit,
          created_at,
          language,
          patch,
          meta.pr_url
        FROM read_parquet(?)
        WHERE repo IN (SELECT unnest(?))
        ORDER BY lower(repo), created_at, instance_id
        """,
        [str(parquet_path), list(aliases)],
    ).fetchall()
    connection.close()

    projections: dict[str, tuple[common.TaskProjection, str]] = {}
    source_lineage: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    duplicate_fingerprints: dict[str, tuple[str, str, str, str]] = {}
    duplicate_rows = 0
    for (
        source_alias,
        source_instance_id,
        base_commit,
        created_at,
        language,
        patch,
        pull_request_url,
    ) in rows:
        alias = str(source_alias)
        repository_id = alias_to_repository[alias]
        source_id = str(source_instance_id)
        canonical_id = canonical_task_id(
            repository_id=repository_id,
            source_instance_id=source_id,
            pull_request_url=(
                str(pull_request_url) if pull_request_url is not None else None
            ),
            source_alias=alias,
        )
        source_time = _parse_naive_utc(str(created_at))
        patch_text = str(patch)
        fingerprint = (
            str(base_commit),
            str(created_at),
            str(language),
            hashlib.sha256(patch_text.encode()).hexdigest(),
        )
        projection = common.TaskProjection(
            instance_id=canonical_id,
            repository_id=repository_id,
            source_time=source_time,
            base_commit=str(base_commit),
            modules=modules_from_patch(patch_text, module_plan),
        )
        prior = projections.get(canonical_id)
        if prior is not None:
            if (
                prior[0] != projection
                or duplicate_fingerprints[canonical_id] != fingerprint
            ):
                raise ValueError(f"canonical Task duplicate disagrees: {canonical_id}")
            duplicate_rows += 1
            source_lineage[canonical_id].append(
                {"source_alias": alias, "source_instance_id": source_id}
            )
            continue
        projections[canonical_id] = (projection, source_id)
        duplicate_fingerprints[canonical_id] = fingerprint
        source_lineage[canonical_id].append(
            {"source_alias": alias, "source_instance_id": source_id}
        )

    tasks = tuple(
        sorted(
            (projection for projection, _ in projections.values()),
            key=lambda task: (
                task.repository_id.casefold(),
                task.source_time,
                task.instance_id,
            ),
        )
    )
    expected_rows = _positive_integer(source, "selected_source_row_count")
    expected_tasks = _positive_integer(source, "canonical_task_count")
    if len(rows) != expected_rows or len(tasks) != expected_tasks:
        raise ValueError("Rebench frozen frame count changed")
    observed_repositories = {task.repository_id for task in tasks}
    expected_repositories = {
        _required_string(repository, "repository_id")
        for repository in repositories
    }
    if observed_repositories != expected_repositories:
        raise ValueError("Rebench frozen repository frame changed")
    observed_task_counts = Counter(task.repository_id for task in tasks)
    expected_task_counts = {
        _required_string(repository, "repository_id"): _positive_integer(
            repository,
            "expected_task_count",
        )
        for repository in repositories
    }
    if observed_task_counts != expected_task_counts:
        raise ValueError("Rebench frozen repository Task counts changed")
    task_source_ids = {
        task_id: tuple(
            sorted(
                lineage,
                key=lambda item: (
                    item["source_alias"].casefold(),
                    item["source_instance_id"],
                ),
            )
        )
        for task_id, lineage in sorted(source_lineage.items())
    }
    manifest: dict[str, Any] = {
        "source_id": _required_string(source, "source_id"),
        "dataset_revision": _required_string(source, "dataset_revision"),
        "parquet_sha256": _sha256_file(parquet_path),
        "selected_source_row_count": len(rows),
        "canonical_task_count": len(tasks),
        "canonical_duplicate_row_count": duplicate_rows,
        "repository_count": len(observed_repositories),
        "frame_minimum_source_rows": minimum_source_rows,
        "source_alias_count": len(observed_frame_aliases),
        "source_alias_digest": canonical_digest(observed_frame_aliases),
        "task_projection_digest": _task_projection_digest(tasks),
        "task_source_identity_digest": canonical_digest(task_source_ids),
        "time_semantics": "timezone-naive source time assumed UTC for counterfactual development",
        "label_semantics": "retrospective reference-fix patch paths",
    }
    manifest["source_manifest_digest"] = canonical_digest(manifest)
    return tasks, manifest, task_source_ids


def run_study(
    plan: Mapping[str, object],
    repository_cache: Path,
) -> Mapping[str, Any]:
    """Run the frozen outcome-free THY-002 Task-mix comparison."""
    tasks, source_manifest, task_source_ids = load_tasks(plan)
    source = _mapping(plan, "source")
    module_plan = _mapping(plan, "module_projection")
    rolling = _mapping(plan, "rolling_origin")
    candidate = _mapping(plan, "candidate")
    unseen_label = _required_string(module_plan, "unseen_label")
    half_life_days = _positive_number(candidate, "recent_half_life_days")
    prior_task_shape = _positive_number(candidate, "prior_task_shape")
    origins_by_repository = common.build_origins(tasks, rolling)
    tasks_by_repository: dict[str, list[common.TaskProjection]] = defaultdict(list)
    for task in tasks:
        tasks_by_repository[task.repository_id].append(task)

    all_rows: list[Mapping[str, object]] = []
    repository_manifests: list[Mapping[str, object]] = []
    admission_failures: list[Mapping[str, str]] = []
    for repository in _mapping_sequence(source, "repositories"):
        repository_id = _required_string(repository, "repository_id")
        origins = origins_by_repository.get(repository_id, ())
        local_repository = common.repository_path(repository_cache, repository_id)
        if not origins:
            admission_failures.append(
                {
                    "repository_id": repository_id,
                    "reason": "no_complete_origin",
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
            rows, manifest = evaluate_repository(
                repository=repository,
                tasks=tuple(tasks_by_repository[repository_id]),
                origins=origins,
                local_repository=local_repository,
                module_plan=module_plan,
                half_life_days=half_life_days,
                prior_task_shape=prior_task_shape,
                unseen_label=unseen_label,
            )
        except (OSError, subprocess.CalledProcessError, ValueError) as error:
            admission_failures.append(
                {
                    "repository_id": repository_id,
                    "reason": f"{type(error).__name__}: {error}",
                }
            )
            continue
        all_rows.extend(rows)
        repository_manifests.append(manifest)

    expected_repositories = tuple(
        _required_string(repository, "repository_id")
        for repository in _mapping_sequence(source, "repositories")
    )
    summaries = summarize_rows(
        all_rows,
        expected_repositories=expected_repositories,
        expected_origin_counts=_expected_origin_counts(plan),
        bootstrap_seed=_positive_integer(_mapping(plan, "metrics"), "bootstrap_seed"),
    )
    decision = decide(
        summaries,
        expected_repository_count=len(expected_repositories),
        admission_failures=admission_failures,
    )
    ordered_rows = tuple(
        sorted(
            all_rows,
            key=lambda row: (
                str(row["repository_id"]).casefold(),
                str(row["origin_id"]),
                _positive_integer(row, "horizon"),
            ),
        )
    )
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "source_manifest": source_manifest,
        "repository_manifests": tuple(
            sorted(
                repository_manifests,
                key=lambda item: str(item["repository_id"]).casefold(),
            )
        ),
        "task_source_identity_digest": canonical_digest(task_source_ids),
        "admission_failures": tuple(
            sorted(admission_failures, key=lambda item: item["repository_id"])
        ),
        "origin_rows": ordered_rows,
        "origin_rows_digest": canonical_digest(ordered_rows),
        "source_summary": summaries,
        "decision": decision,
        "resource_use": {
            "paid_api_calls": 0,
            "embedding_calls": 0,
            "agent_outcomes_opened": 0,
            "sealed_holdout_opened": 0,
        },
        "claim_boundary": (
            "SWE-rebench V2 is a separate automated Generator family. "
            "Timezone-naive source times are assumed UTC and reference patches "
            "supply retrospective Task attributes, so this is outcome-free, "
            "generator-conditional counterfactual development evidence only."
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
) -> tuple[tuple[Mapping[str, object], ...], Mapping[str, object]]:
    """Evaluate every frozen Origin for one canonical repository."""
    repository_id = _required_string(repository, "repository_id")
    expected_head = _required_string(repository, "head_commit")
    observed_head = _git(local_repository, "rev-parse", "HEAD").strip()
    if observed_head != expected_head:
        raise ValueError(f"pinned repository HEAD changed: {repository_id}")
    observation_start = min(task.source_time for task in tasks)
    origin_commits = {}
    for origin in origins:
        cutoff = _format_utc(origin.cutoff)
        commit_id = _git(
            local_repository,
            "rev-list",
            "--first-parent",
            "--max-count=1",
            f"--before={cutoff}",
            "HEAD",
        ).strip()
        if not commit_id:
            raise ValueError(f"no Origin commit: {origin.origin_id}")
        origin_commits[origin.origin_id] = commit_id

    commit_sets: dict[str, tuple[str, ...]] = {}
    union_commits: set[str] = set()
    for origin in origins:
        commit_ids = reachable_exposure_commit_ids(
            local_repository,
            origin_commit=origin_commits[origin.origin_id],
            observation_start=observation_start,
        )
        if not commit_ids:
            raise ValueError(f"no exposure commits: {origin.origin_id}")
        commit_sets[origin.origin_id] = commit_ids
        union_commits.update(commit_ids)
    commit_index = load_commit_index(
        local_repository,
        union_commits,
        module_plan,
    )

    rows = []
    origin_inputs = []
    for origin in origins:
        commits = tuple(
            commit_index[commit_id]
            for commit_id in commit_sets[origin.origin_id]
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
        historical_counts, future_dated = exposure_counts(
            commits,
            observation_start=observation_start,
            cutoff=origin.cutoff,
            half_life_days=None,
        )
        recent_counts, recent_future_dated = exposure_counts(
            commits,
            observation_start=observation_start,
            cutoff=origin.cutoff,
            half_life_days=half_life_days,
        )
        if future_dated != recent_future_dated:
            raise AssertionError("Git anomaly counts disagree")
        history_task_counts = common.task_counts(
            origin.history,
            vocabulary,
            unseen_label=unseen_label,
        )
        candidate_probabilities, diagnostics = calibrated_exposure_distribution(
            task_counts=history_task_counts,
            historical_exposure=historical_counts,
            recent_exposure=recent_counts,
            vocabulary=vocabulary,
            prior_task_shape=prior_task_shape,
        )
        yield_probabilities = probability_distribution(
            {
                label: (
                    history_task_counts.get(label, 0.0) + prior_task_shape
                )
                / (
                    historical_counts.get(label, 0.0)
                    + diagnostics["prior_exposure_mass"]
                )
                for label in vocabulary
            },
            vocabulary,
        )
        for horizon, future in ((5, origin.future_h5), (10, origin.future_h10)):
            predictor_probabilities = {
                "candidate": candidate_probabilities,
                "task_full_history": probability_distribution(
                    history_task_counts,
                    vocabulary,
                ),
                "git_recent_touch": probability_distribution(
                    recent_counts,
                    vocabulary,
                ),
                "yield_only": yield_probabilities,
                "task_trailing_h": probability_distribution(
                    common.task_counts(
                        origin.history[-horizon:],
                        vocabulary,
                        unseen_label=unseen_label,
                    ),
                    vocabulary,
                ),
                "uniform": {
                    label: 1.0 / len(vocabulary) for label in vocabulary
                },
            }
            losses = {
                predictor_id: brier_loss(
                    future,
                    probabilities,
                    vocabulary,
                    unseen_label=unseen_label,
                )
                for predictor_id, probabilities in predictor_probabilities.items()
            }
            total_variations = {
                predictor_id: common.future_total_variation(
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
                    "origin_commit": origin_commits[origin.origin_id],
                    "horizon": horizon,
                    "history_task_count": len(origin.history),
                    "future_task_count": len(future),
                    "future_calendar_span_days": common.future_horizon_span_days(
                        origin.cutoff,
                        future,
                    ),
                    "vocabulary_size": len(vocabulary),
                    "future_other_mass": fsum(
                        common.task_module_mass(
                            task,
                            vocabulary,
                            unseen_label=unseen_label,
                        ).get(unseen_label, 0.0)
                        for task in future
                    )
                    / len(future),
                    "future_dated_reachable_commit_count": future_dated,
                    "candidate_diagnostics": diagnostics,
                    "losses": losses,
                    "total_variations": total_variations,
                }
            )
        origin_inputs.append(
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

    base_presence = _git_object_presence(
        local_repository,
        tuple(task.base_commit for task in tasks),
    )
    manifest: dict[str, Any] = {
        "repository_id": repository_id,
        "repository_head": observed_head,
        "source_head_ref": _required_string(repository, "head_ref"),
        "task_count": len(tasks),
        "origin_count": len(origins),
        "observation_start": _format_utc(observation_start),
        "base_commit_present_count": sum(base_presence.values()),
        "base_commit_missing_count": sum(not present for present in base_presence.values()),
        "base_commit_presence_digest": canonical_digest(base_presence),
        "origin_input_digest": canonical_digest(tuple(origin_inputs)),
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


def _expected_origin_counts(
    plan: Mapping[str, object],
) -> Mapping[str, int]:
    rolling = _mapping(plan, "rolling_origin")
    minimum_history = _positive_integer(
        rolling,
        "minimum_initial_history_tasks",
    )
    block_size = _positive_integer(rolling, "future_block_tasks")
    result = {}
    for repository in _mapping_sequence(_mapping(plan, "source"), "repositories"):
        repository_id = _required_string(repository, "repository_id")
        task_count = _positive_integer(repository, "expected_task_count")
        origin_count = (task_count - minimum_history) // block_size
        if origin_count <= 0:
            raise ValueError(f"repository has no expected Origin: {repository_id}")
        result[repository_id] = origin_count
    return result


def summarize_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    expected_repositories: Sequence[str],
    expected_origin_counts: Mapping[str, int],
    bootstrap_seed: int,
) -> Mapping[str, object]:
    """Aggregate Origin losses to equal-weight repository evidence units."""
    repositories = tuple(expected_repositories)
    if not repositories or len(repositories) != len(set(repositories)):
        raise ValueError("expected repositories must be nonempty and unique")
    expected_repository_set = set(repositories)
    if set(expected_origin_counts) != expected_repository_set or any(
        count <= 0 for count in expected_origin_counts.values()
    ):
        raise ValueError("expected Origin counts do not match repositories")
    observed_keys: set[tuple[str, str, int]] = set()
    origin_horizons: dict[tuple[str, str], set[int]] = defaultdict(set)
    grouped: dict[tuple[int, str], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        repository_id = _required_string(row, "repository_id")
        if repository_id not in expected_repository_set:
            raise ValueError(f"unexpected repository row: {repository_id}")
        origin_id = _required_string(row, "origin_id")
        horizon = _positive_integer(row, "horizon")
        if horizon not in (5, 10):
            raise ValueError(f"unexpected future horizon: {horizon}")
        row_key = (repository_id, origin_id, horizon)
        if row_key in observed_keys:
            raise ValueError(f"duplicate Origin-horizon row: {row_key}")
        observed_keys.add(row_key)
        origin_horizons[(repository_id, origin_id)].add(horizon)
        grouped[
            (
                horizon,
                repository_id,
            )
        ].append(row)
    incomplete = tuple(
        key
        for key, horizons in sorted(origin_horizons.items())
        if horizons != {5, 10}
    )
    if incomplete:
        raise ValueError(f"incomplete H5/H10 Origin pairs: {incomplete}")
    observed_origins: dict[str, set[str]] = defaultdict(set)
    for repository_id, origin_id in origin_horizons:
        observed_origins[repository_id].add(origin_id)
    for repository_id, origin_ids in observed_origins.items():
        expected_ids = {
            f"{repository_id}:origin-{index:03d}"
            for index in range(1, expected_origin_counts[repository_id] + 1)
        }
        if origin_ids != expected_ids:
            raise ValueError(
                f"Origin rows changed for {repository_id}: "
                f"expected {len(expected_ids)}, observed {len(origin_ids)}"
            )

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
                        control_id: losses["candidate"] - losses[control_id]
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
            for predictor_id in PREDICTOR_IDS
        }
        contrasts = {}
        for control_id in CONTROL_IDS:
            values = tuple(
                _number(_mapping(row, "contrasts"), control_id)
                for row in repository_rows
            )
            contrasts[control_id] = {
                "macro_repository": (
                    fsum(values) / len(values) if values else None
                ),
                "favorable_repository_count": sum(value < 0.0 for value in values),
                "repository_count": len(values),
                "bootstrap_95_interval": (
                    _bootstrap_interval(
                        values,
                        draws=20000,
                        seed=_control_seed(bootstrap_seed, horizon, control_id),
                    )
                    if values
                    else None
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


def decide(
    summary: Mapping[str, object],
    *,
    expected_repository_count: int,
    admission_failures: Sequence[Mapping[str, str]],
) -> Mapping[str, object]:
    """Apply the frozen task-mix pass-or-retire decision."""
    if admission_failures:
        return {
            "status": "data_blocked",
            "task_mix_gate_passed": False,
            "agent_outcome_replay_authorized": False,
            "gates": {"complete_source_admission": False},
        }
    horizons = _mapping(summary, "horizons")
    h5 = _mapping(horizons, "5")
    h10 = _mapping(horizons, "10")
    complete = (
        h5.get("repository_count") == expected_repository_count
        and h10.get("repository_count") == expected_repository_count
    )
    required_favorable = (3 * expected_repository_count + 4) // 5

    def horizon_gate(item: Mapping[str, object]) -> bool:
        contrasts = _mapping(item, "contrasts")
        full = _mapping(contrasts, "task_full_history")

        def statistically_better(control_id: str) -> bool:
            contrast = _mapping(contrasts, control_id)
            interval = contrast.get("bootstrap_95_interval")
            return (
                isinstance(interval, Sequence)
                and not isinstance(interval, str)
                and len(interval) == 2
                and _number(contrast, "macro_repository") < 0.0
                and float(interval[1]) < 0.0
            )

        return (
            statistically_better("task_full_history")
            and _positive_integer(
                full,
                "favorable_repository_count",
                allow_zero=True,
            )
            >= required_favorable
            and all(
                statistically_better(control_id)
                for control_id in ("git_recent_touch", "yield_only")
            )
        )

    h5_gate = complete and horizon_gate(h5)
    h10_gate = complete and horizon_gate(h10)
    passed = h5_gate and h10_gate
    return {
        "status": "pass" if passed else "retire",
        "task_mix_gate_passed": passed,
        "agent_outcome_replay_authorized": False,
        "gates": {
            "complete_source_admission": complete,
            "h5_generator_calibration": h5_gate,
            "h10_generator_calibration": h10_gate,
        },
    }


def compact_result(
    result: Mapping[str, object],
    plan: Mapping[str, object],
) -> Mapping[str, object]:
    """Create the small committed projection after raw verification."""
    verify_result(result, plan)
    compact: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "study_id": result.get("study_id"),
        "plan_digest": result.get("plan_digest"),
        "result_digest": result.get("result_digest"),
        "origin_rows_digest": result.get("origin_rows_digest"),
        "source_manifest": result.get("source_manifest"),
        "repository_manifests": result.get("repository_manifests"),
        "admission_failures": result.get("admission_failures"),
        "source_summary": result.get("source_summary"),
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
    """Replay raw summary and decision identities."""
    if result.get("schema_version") != RESULT_SCHEMA:
        raise ValueError("THY-002 result schema is unsupported")
    if result.get("plan_digest") != plan.get("plan_digest"):
        raise ValueError("THY-002 result does not bind the plan")
    if result.get("study_id") != plan.get("study_id"):
        raise ValueError("THY-002 result study identity changed")
    budget = _mapping(plan, "resource_budget")
    expected_resource_use = {
        key: _positive_integer(budget, key, allow_zero=True)
        for key in (
            "paid_api_calls",
            "embedding_calls",
            "agent_outcomes_opened",
            "sealed_holdout_opened",
        )
    }
    if _mapping(result, "resource_use") != expected_resource_use:
        raise ValueError("THY-002 result crossed the frozen resource boundary")
    payload = dict(result)
    digest = payload.pop("result_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("THY-002 result digest does not match")
    source = _mapping(plan, "source")
    source_manifest = _mapping(result, "source_manifest")
    source_manifest_payload = dict(source_manifest)
    source_manifest_digest = source_manifest_payload.pop(
        "source_manifest_digest",
        None,
    )
    if canonical_digest(source_manifest_payload) != source_manifest_digest:
        raise ValueError("THY-002 source manifest digest does not match")
    aliases = tuple(
        sorted(
            (
                alias
                for repository in _mapping_sequence(source, "repositories")
                for alias in _string_sequence(
                    repository.get("source_aliases"),
                    "source aliases",
                )
            ),
            key=lambda alias: (alias.casefold(), alias),
        )
    )
    expected_source_manifest = {
        "source_id": _required_string(source, "source_id"),
        "dataset_revision": _required_string(source, "dataset_revision"),
        "parquet_sha256": _required_string(source, "parquet_sha256"),
        "selected_source_row_count": _positive_integer(
            source,
            "selected_source_row_count",
        ),
        "canonical_task_count": _positive_integer(
            source,
            "canonical_task_count",
        ),
        "repository_count": _positive_integer(
            source,
            "canonical_repository_count",
        ),
        "frame_minimum_source_rows": _positive_integer(
            source,
            "frame_minimum_source_rows",
        ),
        "source_alias_count": _positive_integer(source, "source_alias_count"),
        "source_alias_digest": canonical_digest(aliases),
    }
    if any(
        source_manifest.get(key) != value
        for key, value in expected_source_manifest.items()
    ):
        raise ValueError("THY-002 source manifest changed from the plan")
    if result.get("task_source_identity_digest") != source_manifest.get(
        "task_source_identity_digest"
    ):
        raise ValueError("THY-002 Task source identity digest changed")

    planned_repositories = {
        _required_string(repository, "repository_id"): repository
        for repository in _mapping_sequence(source, "repositories")
    }
    expected_origin_counts = _expected_origin_counts(plan)
    repository_manifest_ids: set[str] = set()
    for manifest in _mapping_sequence(result, "repository_manifests"):
        manifest_payload = dict(manifest)
        manifest_digest = manifest_payload.pop(
            "repository_manifest_digest",
            None,
        )
        if canonical_digest(manifest_payload) != manifest_digest:
            raise ValueError("THY-002 repository manifest digest does not match")
        repository_id = _required_string(manifest, "repository_id")
        if (
            repository_id not in planned_repositories
            or repository_id in repository_manifest_ids
        ):
            raise ValueError("THY-002 repository manifest identity changed")
        repository_manifest_ids.add(repository_id)
        repository_plan = planned_repositories[repository_id]
        if (
            manifest.get("repository_head")
            != repository_plan.get("head_commit")
            or manifest.get("source_head_ref")
            != repository_plan.get("head_ref")
            or manifest.get("task_count")
            != repository_plan.get("expected_task_count")
            or manifest.get("origin_count")
            != expected_origin_counts[repository_id]
        ):
            raise ValueError("THY-002 repository manifest changed from the plan")

    failures = tuple(
        {
            "repository_id": _required_string(
                _mapping(item, "admission failure"),
                "repository_id",
            ),
            "reason": _required_string(
                _mapping(item, "admission failure"),
                "reason",
            ),
        }
        for item in _mapping_sequence(result, "admission_failures")
    )
    failure_ids = {item["repository_id"] for item in failures}
    if (
        len(failure_ids) != len(failures)
        or failure_ids & repository_manifest_ids
        or failure_ids | repository_manifest_ids != set(planned_repositories)
    ):
        raise ValueError("THY-002 repository admission partition changed")
    rows = _mapping_sequence(result, "origin_rows")
    if result.get("origin_rows_digest") != canonical_digest(tuple(rows)):
        raise ValueError("THY-002 Origin rows digest does not match")
    row_repository_ids = {
        _required_string(row, "repository_id") for row in rows
    }
    if row_repository_ids != repository_manifest_ids:
        raise ValueError("THY-002 Origin rows do not match admitted repositories")
    repositories = tuple(
        _required_string(repository, "repository_id")
        for repository in _mapping_sequence(source, "repositories")
    )
    expected_summary = summarize_rows(
        rows,
        expected_repositories=repositories,
        expected_origin_counts=expected_origin_counts,
        bootstrap_seed=_positive_integer(_mapping(plan, "metrics"), "bootstrap_seed"),
    )
    if canonical_digest(result.get("source_summary")) != canonical_digest(
        expected_summary
    ):
        raise ValueError("THY-002 source summary does not replay")
    expected_decision = decide(
        expected_summary,
        expected_repository_count=len(repositories),
        admission_failures=failures,
    )
    if result.get("decision") != expected_decision:
        raise ValueError("THY-002 decision does not replay")


def verify_summary(
    summary: Mapping[str, object],
    plan: Mapping[str, object],
    *,
    result: Mapping[str, object],
) -> None:
    """Bind the compact artifact to its exact raw parent."""
    if summary.get("schema_version") != SUMMARY_SCHEMA:
        raise ValueError("THY-002 summary schema is unsupported")
    payload = dict(summary)
    digest = payload.pop("summary_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("THY-002 summary digest does not match")
    if canonical_digest(summary) != canonical_digest(compact_result(result, plan)):
        raise ValueError("THY-002 summary does not match the raw result")


def _git_object_presence(
    repository: Path,
    object_ids: Sequence[str],
) -> Mapping[str, bool]:
    unique = tuple(sorted(set(object_ids)))
    output = _run_process(
        (
            "git",
            "-C",
            str(repository),
            "cat-file",
            "--batch-check=%(objectname) %(objecttype)",
        ),
        input_text="\n".join(unique) + "\n",
        check=False,
    )
    present = {}
    for object_id, line in zip(unique, output.splitlines(), strict=True):
        fields = line.split()
        present[object_id] = len(fields) == 2 and fields[1] == "commit"
    return present


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


def _control_seed(base_seed: int, horizon: int, control_id: str) -> int:
    payload = f"{horizon}\0{control_id}".encode()
    return base_seed + int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


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


def _parse_naive_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        raise ValueError(f"Rebench source timestamp unexpectedly has a zone: {value}")
    return parsed.replace(tzinfo=UTC)


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace(
        "+00:00",
        "Z",
    )


def _git(repository: Path, *arguments: str) -> str:
    return _run_process(("git", "-C", str(repository), *arguments))


def _run_process(
    arguments: Sequence[str],
    *,
    input_text: str | None = None,
    check: bool = True,
) -> str:
    environment = dict(os.environ)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    completed = subprocess.run(
        tuple(arguments),
        input=input_text,
        text=True,
        check=check,
        capture_output=True,
        env=environment,
    )
    return completed.stdout


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
        raise ValueError(f"JSON file must contain an object: {path}")
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
    value = payload.get(key)
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError(f"{key} must be a sequence")
    rows = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"{key} entries must be objects")
        rows.append(item)
    return tuple(rows)


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
        print(
            canonical_json(
                {
                    "repositories": prepare_repositories(
                        plan,
                        arguments.repository_cache,
                    )
                }
            )
        )
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
        raise AssertionError("unreachable THY-002 command")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
