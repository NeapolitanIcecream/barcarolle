#!/usr/bin/env python3
"""Acquire and run the frozen outcome-free THY-003 Stage-A study."""

from __future__ import annotations

# DuckDB is required only by source-loading commands.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from fractions import Fraction
import hashlib
import importlib.metadata
import json
from math import fsum
import os
from pathlib import Path, PurePosixPath
import random
import re
import shlex
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence
import urllib.error
import urllib.parse
import urllib.request


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.generator_calibrated_exposure import study as thy2  # noqa: E402
from examples.pre_origin_task_mix import study as common  # noqa: E402


HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
DEFAULT_PLAN = HERE / "plan.json"
DEFAULT_ADDENDUM = HERE / "execution-addendum.json"
DEFAULT_EXECUTION_LOCK = HERE / "execution-lock.json"
PARENT_PLAN = REPOSITORY_ROOT / "examples/generator_calibrated_exposure/plan.json"
PARENT_RESULT = (
    REPOSITORY_ROOT
    / "outputs/research/2026-07-29-generator-calibrated-exposure"
    / "task-mix-results.json"
)
DEFAULT_REPOSITORY_CACHE = PARENT_RESULT.parent / "repositories"
DEFAULT_RAW_ROOT = (
    REPOSITORY_ROOT / "outputs/research/2026-07-29-dependency-lag-theory/raw-registry"
)
DEFAULT_REGISTRY_MANIFEST = DEFAULT_RAW_ROOT / "manifest.json"
DEFAULT_OUTPUT = (
    REPOSITORY_ROOT
    / "outputs/research/2026-07-29-dependency-lag-theory"
    / "stage-a-result.json"
)
DEFAULT_SUMMARY = HERE / "evidence/stage-a-summary.json"

PLAN_SCHEMA = "barcarolle_dependency_lag_theory_plan_v1"
ADDENDUM_SCHEMA = "barcarolle_dependency_lag_execution_addendum_v1"
EXECUTION_LOCK_SCHEMA = "barcarolle_dependency_lag_execution_lock_v1"
REGISTRY_MANIFEST_SCHEMA = "barcarolle_dependency_lag_registry_manifest_v1"
RESULT_SCHEMA = "barcarolle_dependency_lag_stage_a_result_v1"
SUMMARY_SCHEMA = "barcarolle_dependency_lag_stage_a_summary_v1"

LOCKFILES = (
    "npm-shrinkwrap.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
)
SCORING_FILES = frozenset(
    {
        "package.json",
        "package-lock.json",
        "npm-shrinkwrap.json",
        "pnpm-lock.yaml",
        "yarn.lock",
    }
)
SCOPES = ("production", "development")
LAG_CATEGORIES = (
    "current",
    "patch_lag",
    "minor_lag",
    "major_lag",
    "unknown",
)
PREDICTORS = (
    "candidate_continuous",
    "candidate_materialized",
    "task_full_history",
    "task_trailing_h",
    "lock_only_continuous",
    "lock_only_materialized",
)
STRICT_SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
PNPM_CONTEXT_VERSION = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:_.+|\(.+\))$"
)
YAML_ENTRY = re.compile(
    r"^(?P<indent> *)(?P<key>\"(?:[^\"\\]|\\.)*\"|'[^']*'|[^:]+):"
    r"(?P<value>.*)$"
)


@dataclass(frozen=True)
class DirectDependency:
    """One root direct declaration and its exact lock resolution, if any."""

    name: str
    scope: str
    specifier: str
    locked_version: str | None


@dataclass(frozen=True)
class DependencySnapshot:
    """The direct dependency projection of one repository commit."""

    commit_id: str
    lockfile: str | None
    dependencies: tuple[DirectDependency, ...]
    missing_reason: str | None = None

    @property
    def supported(self) -> bool:
        return self.missing_reason is None and bool(self.dependencies)


@dataclass(frozen=True)
class StateVector:
    """Exact ten-cell state; missing historical state is represented by None."""

    counts: tuple[int, ...]
    total: int

    def __post_init__(self) -> None:
        if len(self.counts) != 10 or self.total <= 0:
            raise ValueError("dependency-lag state shape is invalid")
        if any(value < 0 for value in self.counts) or sum(self.counts) != self.total:
            raise ValueError("dependency-lag state mass is invalid")

    def fractions(self) -> tuple[Fraction, ...]:
        return tuple(Fraction(value, self.total) for value in self.counts)


@dataclass(frozen=True)
class OriginFrame:
    """One parent-bound rolling Origin."""

    projection: common.OriginProjection
    origin_commit: str


@dataclass(frozen=True)
class SourceFrame:
    """The exact nine-repository Task and Origin frame."""

    tasks: tuple[common.TaskProjection, ...]
    origins: Mapping[str, tuple[OriginFrame, ...]]
    repositories: tuple[Mapping[str, Any], ...]
    source_manifest: Mapping[str, Any]


@dataclass(frozen=True)
class StatePoint:
    """One Task-time or Origin-time state input."""

    repository_id: str
    kind: str
    state_id: str
    cutoff: datetime
    commit_id: str | None
    snapshot: DependencySnapshot


@dataclass(frozen=True)
class SelectionProjection:
    """Outcome-free ranking material for one Origin."""

    selected_task_ids: tuple[str, ...]
    distances: Mapping[str, Fraction]


def load_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    """Load and verify the frozen scientific plan."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != PLAN_SCHEMA:
        raise ValueError("THY-003 plan schema is unsupported")
    digest = payload.get("plan_digest")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "plan_digest"}
    )
    if digest != expected:
        raise ValueError("THY-003 plan digest does not match")
    if (
        tuple(
            _mapping(payload, "information_set").get(
                "lockfiles_in_precedence_order", ()
            )
        )
        != LOCKFILES
    ):
        raise ValueError("THY-003 lockfile precedence changed")
    if (
        tuple(_mapping(payload, "state_projection").get("lag_categories", ()))
        != LAG_CATEGORIES
    ):
        raise ValueError("THY-003 lag categories changed")
    return payload


def load_addendum(
    path: Path = DEFAULT_ADDENDUM,
    *,
    plan: Mapping[str, object] | None = None,
) -> Mapping[str, Any]:
    """Load and verify the pre-execution ambiguity closure."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != ADDENDUM_SCHEMA:
        raise ValueError("THY-003 execution addendum schema is unsupported")
    digest = payload.get("addendum_digest")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "addendum_digest"}
    )
    if digest != expected:
        raise ValueError("THY-003 execution addendum digest does not match")
    if plan is not None and payload.get("parent_plan_digest") != plan.get(
        "plan_digest"
    ):
        raise ValueError("THY-003 execution addendum does not bind the plan")
    return payload


def load_execution_lock(
    path: Path = DEFAULT_EXECUTION_LOCK,
    *,
    plan: Mapping[str, object],
    addendum: Mapping[str, object],
) -> Mapping[str, Any]:
    """Verify the runner, dependency, repository, and registry freeze."""
    payload = _load_mapping(path)
    if payload.get("schema_version") != EXECUTION_LOCK_SCHEMA:
        raise ValueError("THY-003 execution lock schema is unsupported")
    digest = payload.get("execution_lock_digest")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "execution_lock_digest"}
    )
    if digest != expected:
        raise ValueError("THY-003 execution lock digest does not match")
    if payload.get("plan_digest") != plan.get("plan_digest") or payload.get(
        "addendum_digest"
    ) != addendum.get("addendum_digest"):
        raise ValueError("THY-003 execution lock parent identity changed")
    for item in _mapping_sequence(payload, "implementation"):
        relative = _required_string(item, "path")
        _verify_sha256(
            REPOSITORY_ROOT / relative,
            _required_string(item, "sha256"),
        )
    dependencies = _mapping(payload, "dependencies")
    python_version = ".".join(str(value) for value in sys.version_info[:3])
    if dependencies.get("python") != python_version:
        raise ValueError("THY-003 Python version changed")
    if dependencies.get("duckdb") != importlib.metadata.version("duckdb"):
        raise ValueError("THY-003 DuckDB version changed")
    return payload


def parse_strict_semver(value: object) -> tuple[int, int, int] | None:
    """Parse only stable canonical x.y.z versions."""
    if not isinstance(value, str):
        return None
    match = STRICT_SEMVER.fullmatch(value)
    if match is None:
        return None
    return tuple(int(field) for field in match.groups())  # type: ignore[return-value]


def normalize_pnpm_version(value: object) -> str | None:
    """Remove only a documented frozen peer-context suffix."""
    if not isinstance(value, str):
        return None
    if parse_strict_semver(value) is not None:
        return value
    match = PNPM_CONTEXT_VERSION.fullmatch(value)
    if match is None:
        return None
    return ".".join(match.groups())


def dependency_declarations(
    manifest: Mapping[str, object],
) -> tuple[tuple[str, str, str], ...]:
    """Read root production/dev declarations with production precedence."""
    result: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for field, scope in (
        ("dependencies", "production"),
        ("devDependencies", "development"),
    ):
        raw = manifest.get(field, {})
        if raw is None:
            raw = {}
        if not isinstance(raw, Mapping):
            raise ValueError(f"package.json {field} must be an object")
        for raw_name, raw_specifier in sorted(
            raw.items(), key=lambda item: str(item[0])
        ):
            if not isinstance(raw_name, str) or not raw_name:
                raise ValueError("package.json dependency name is invalid")
            if raw_name in seen:
                continue
            seen.add(raw_name)
            specifier = raw_specifier if isinstance(raw_specifier, str) else ""
            result.append((raw_name, scope, specifier))
    return tuple(result)


def locked_direct_versions(
    *,
    manifest: Mapping[str, object],
    lockfile: str,
    lock_bytes: bytes,
) -> tuple[DirectDependency, ...]:
    """Resolve the frozen direct dependency projection for one lockfile."""
    declarations = dependency_declarations(manifest)
    if not declarations:
        return ()
    if lockfile in {"npm-shrinkwrap.json", "package-lock.json"}:
        resolved = _npm_locked_versions(lock_bytes, declarations)
    elif lockfile == "pnpm-lock.yaml":
        resolved = _pnpm_locked_versions(lock_bytes, declarations)
    elif lockfile == "yarn.lock":
        resolved = _yarn_locked_versions(lock_bytes, declarations)
    else:
        raise ValueError(f"unsupported lockfile: {lockfile}")
    return tuple(
        DirectDependency(
            name=name,
            scope=scope,
            specifier=specifier,
            locked_version=resolved.get(name),
        )
        for name, scope, specifier in declarations
    )


def _npm_locked_versions(
    lock_bytes: bytes,
    declarations: Sequence[tuple[str, str, str]],
) -> Mapping[str, str | None]:
    try:
        payload = json.loads(lock_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("npm lockfile is malformed") from error
    if not isinstance(payload, Mapping):
        raise ValueError("npm lockfile root must be an object")
    raw_version = payload.get("lockfileVersion", 1)
    if isinstance(raw_version, str) and raw_version.isdigit():
        raw_version = int(raw_version)
    if raw_version not in (1, 2, 3):
        raise ValueError(f"npm lockfileVersion is unsupported: {raw_version}")
    result: dict[str, str | None] = {}
    if raw_version == 1:
        dependencies = payload.get("dependencies", {})
        if not isinstance(dependencies, Mapping):
            raise ValueError("npm v1 dependencies must be an object")
        for name, _, _ in declarations:
            entry = dependencies.get(name)
            value = entry.get("version") if isinstance(entry, Mapping) else None
            result[name] = value if parse_strict_semver(value) is not None else None
        return result
    packages = payload.get("packages", {})
    if not isinstance(packages, Mapping):
        raise ValueError("npm v2/v3 packages must be an object")
    for name, _, _ in declarations:
        entry = packages.get(f"node_modules/{name}")
        value = entry.get("version") if isinstance(entry, Mapping) else None
        link = entry.get("link") if isinstance(entry, Mapping) else None
        result[name] = (
            value
            if link is not True and parse_strict_semver(value) is not None
            else None
        )
    return result


def _yaml_scalar(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return ""
    if stripped.startswith('"') and stripped.endswith('"'):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError as error:
            raise ValueError("double-quoted YAML scalar is malformed") from error
        return parsed if isinstance(parsed, str) else ""
    if stripped.startswith("'") and stripped.endswith("'"):
        return stripped[1:-1].replace("''", "'")
    return stripped


def _pnpm_locked_versions(
    lock_bytes: bytes,
    declarations: Sequence[tuple[str, str, str]],
) -> Mapping[str, str | None]:
    """Parse only the root importer of pnpm 5.4/9 lockfiles."""
    try:
        lines = lock_bytes.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise ValueError("pnpm lockfile is not UTF-8") from error
    lock_version: str | None = None
    root_start: int | None = None
    in_importers = False
    for index, line in enumerate(lines):
        match = YAML_ENTRY.match(line)
        if match is None:
            continue
        indent = len(match.group("indent"))
        key = _yaml_scalar(match.group("key"))
        value = _yaml_scalar(match.group("value"))
        if indent == 0 and key == "lockfileVersion":
            lock_version = value
        if indent == 0:
            in_importers = key == "importers"
            continue
        if in_importers and indent == 2 and key == ".":
            root_start = index + 1
            break
    if lock_version not in {"5.4", "9.0"} or root_start is None:
        raise ValueError(f"pnpm lockfileVersion is unsupported: {lock_version}")

    sections: dict[str, dict[str, dict[str, str]]] = {
        "dependencies": {},
        "devDependencies": {},
    }
    specifiers: dict[str, str] = {}
    section: str | None = None
    package: str | None = None
    for line in lines[root_start:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = YAML_ENTRY.match(line)
        if match is None:
            continue
        indent = len(match.group("indent"))
        key = _yaml_scalar(match.group("key"))
        value = _yaml_scalar(match.group("value"))
        if indent <= 2:
            break
        if indent == 4:
            section = (
                key
                if key
                in {
                    "specifiers",
                    "dependencies",
                    "devDependencies",
                }
                else None
            )
            package = None
            continue
        if section == "specifiers" and indent == 6:
            specifiers[key] = value
            continue
        if section in sections and indent == 6:
            package = key
            sections[section][package] = {}
            if value:
                sections[section][package]["version"] = value
            continue
        if section in sections and indent == 8 and package is not None:
            if key in {"specifier", "version"}:
                sections[section][package][key] = value

    result: dict[str, str | None] = {}
    for name, scope, expected_specifier in declarations:
        field = "dependencies" if scope == "production" else "devDependencies"
        entry = sections[field].get(name, {})
        observed_specifier = entry.get("specifier", specifiers.get(name))
        if observed_specifier is not None and observed_specifier != expected_specifier:
            result[name] = None
            continue
        result[name] = normalize_pnpm_version(entry.get("version"))
    return result


def _yarn_header_selectors(header: str) -> tuple[str, ...]:
    raw = header.strip()
    if not raw:
        return ()
    parts = re.findall(r'"(?:[^"\\]|\\.)*"|\'[^\']*\'|[^,]+', raw)
    decoded = tuple(_yaml_scalar(part.strip()) for part in parts if part.strip())
    if len(decoded) == 1 and ", " in decoded[0]:
        return tuple(item.strip() for item in decoded[0].split(", "))
    return decoded


def _yarn_locked_versions(
    lock_bytes: bytes,
    declarations: Sequence[tuple[str, str, str]],
) -> Mapping[str, str | None]:
    """Parse top-level Yarn classic or Berry lock entries."""
    try:
        lines = lock_bytes.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise ValueError("Yarn lockfile is not UTF-8") from error
    berry = any(line == "__metadata:" for line in lines)
    selector_versions: dict[str, str | None] = {}
    selectors: tuple[str, ...] = ()
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith((" ", "\t")) and line.endswith(":"):
            selectors = _yarn_header_selectors(line[:-1])
            continue
        if not selectors:
            continue
        value: str | None = None
        if berry:
            match = re.match(r"^  version:\s*(.+?)\s*$", line)
            if match:
                value = _yaml_scalar(match.group(1))
        else:
            match = re.match(r'^  version\s+"([^"]+)"\s*$', line)
            if match:
                value = match.group(1)
        if value is None:
            continue
        normalized = value if parse_strict_semver(value) is not None else None
        for selector in selectors:
            selector_versions[selector] = normalized
        selectors = ()

    result: dict[str, str | None] = {}
    for name, _, specifier in declarations:
        candidates = (
            (f"{name}@npm:{specifier}", f"{name}@{specifier}")
            if berry
            else (f"{name}@{specifier}",)
        )
        result[name] = next(
            (
                selector_versions[candidate]
                for candidate in candidates
                if candidate in selector_versions
            ),
            None,
        )
    return result


def load_frame(
    plan: Mapping[str, object],
    addendum: Mapping[str, object],
) -> SourceFrame:
    """Load and bind the exact parent Task/Origin frame."""
    source = _mapping(plan, "source")
    parent_plan = thy2.load_plan(PARENT_PLAN)
    if parent_plan.get("plan_digest") != source.get("parent_plan_digest"):
        raise ValueError("THY-003 parent plan identity changed")
    parent_result = _load_mapping(PARENT_RESULT)
    thy2.verify_result(parent_result, parent_plan)
    if parent_result.get("result_digest") != source.get("parent_result_digest"):
        raise ValueError("THY-003 parent result identity changed")

    all_tasks, task_source_identity_digest = load_task_identities(parent_plan)
    if task_source_identity_digest != source.get("task_source_identity_digest"):
        raise ValueError("THY-003 Task source identity changed")
    repository_ids = _string_sequence(
        source.get("wide_repositories"),
        "THY-003 wide repositories",
    )
    tasks = tuple(
        task for task in all_tasks if task.repository_id in set(repository_ids)
    )
    frame_binding = _mapping(addendum, "source_frame")
    if len(tasks) != _positive_integer(frame_binding, "task_count"):
        raise ValueError("THY-003 Task frame count changed")
    task_projection = tuple(
        {
            "task_id": task.instance_id,
            "repository_id": task.repository_id,
            "source_time": _format_utc(task.source_time),
            "base_commit": task.base_commit,
        }
        for task in tasks
    )
    if canonical_digest(task_projection) != frame_binding.get("task_projection_digest"):
        raise ValueError("THY-003 Task frame projection changed")

    rolling = _mapping(plan, "rolling_origin")
    origins_by_repository = common.build_origins(tasks, rolling)
    parent_origin_rows: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in _mapping_sequence(parent_result, "origin_rows"):
        repository_id = _required_string(row, "repository_id")
        if repository_id not in repository_ids:
            continue
        key = (repository_id, _required_string(row, "origin_id"))
        prior = parent_origin_rows.get(key)
        stable = {
            field: row.get(field)
            for field in (
                "repository_id",
                "origin_id",
                "origin_commit",
                "origin_cutoff",
                "history_task_count",
            )
        }
        if prior is not None and any(
            prior.get(field) != value for field, value in stable.items()
        ):
            raise ValueError("THY-003 parent H5/H10 Origin rows disagree")
        parent_origin_rows[key] = stable

    bound_origins: dict[str, tuple[OriginFrame, ...]] = {}
    schedule_records = []
    task_frame_records = []
    for repository_id in repository_ids:
        bound = []
        for origin in origins_by_repository.get(repository_id, ()):
            key = (repository_id, origin.origin_id)
            row = parent_origin_rows.get(key)
            if row is None:
                raise ValueError(
                    f"THY-003 parent Origin is missing: {origin.origin_id}"
                )
            if row.get("origin_cutoff") != _format_utc(origin.cutoff) or row.get(
                "history_task_count"
            ) != len(origin.history):
                raise ValueError(f"THY-003 parent Origin changed: {origin.origin_id}")
            commit_id = _required_string(row, "origin_commit")
            bound.append(OriginFrame(projection=origin, origin_commit=commit_id))
            schedule_records.append(dict(row))
            task_frame_records.append(
                {
                    "repository_id": repository_id,
                    "origin_id": origin.origin_id,
                    "origin_cutoff": _format_utc(origin.cutoff),
                    "origin_commit": commit_id,
                    "history_task_ids": tuple(
                        task.instance_id for task in origin.history
                    ),
                    "future_h10_task_ids": tuple(
                        task.instance_id for task in origin.future_h10
                    ),
                }
            )
        bound_origins[repository_id] = tuple(bound)
    if len(task_frame_records) != _positive_integer(frame_binding, "origin_count"):
        raise ValueError("THY-003 Origin count changed")
    if canonical_digest(tuple(schedule_records)) != frame_binding.get(
        "origin_schedule_digest"
    ):
        raise ValueError("THY-003 Origin schedule changed")
    if canonical_digest(tuple(task_frame_records)) != frame_binding.get(
        "origin_task_frame_digest"
    ):
        raise ValueError("THY-003 Origin Task frame changed")

    parent_repositories = {
        _required_string(item, "repository_id"): item
        for item in _mapping_sequence(_mapping(parent_plan, "source"), "repositories")
    }
    repositories = tuple(parent_repositories[item] for item in repository_ids)
    source_manifest = {
        "source_id": source.get("source_id"),
        "dataset_revision": source.get("dataset_revision"),
        "parquet_sha256": source.get("parquet_sha256"),
        "task_source_identity_digest": source.get("task_source_identity_digest"),
        "parent_plan_digest": source.get("parent_plan_digest"),
        "parent_result_digest": source.get("parent_result_digest"),
        "task_count": len(tasks),
        "origin_count": len(task_frame_records),
        "task_projection_digest": canonical_digest(task_projection),
        "origin_schedule_digest": canonical_digest(tuple(schedule_records)),
        "origin_task_frame_digest": canonical_digest(tuple(task_frame_records)),
    }
    source_manifest["source_manifest_digest"] = canonical_digest(source_manifest)
    return SourceFrame(
        tasks=tasks,
        origins=bound_origins,
        repositories=repositories,
        source_manifest=source_manifest,
    )


def load_task_identities(
    parent_plan: Mapping[str, object],
) -> tuple[tuple[common.TaskProjection, ...], str]:
    """Load Task identity, time, and base commit without reading patch labels."""
    try:
        import duckdb
    except ImportError as error:
        raise RuntimeError(
            "DuckDB is required; run with `uv run --with duckdb`"
        ) from error

    source = _mapping(parent_plan, "source")
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
    if len(aliases) != _positive_integer(source, "source_alias_count"):
        raise ValueError("Rebench source alias count changed")
    if len(repositories) != _positive_integer(
        source,
        "canonical_repository_count",
    ):
        raise ValueError("Rebench repository count changed")

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
    observed_aliases = tuple(str(row[0]) for row in observed_frame_rows)
    if set(observed_aliases) != set(aliases):
        connection.close()
        raise ValueError("Rebench repositories passing the frame rule changed")
    rows = connection.execute(
        """
        SELECT
          repo,
          instance_id,
          base_commit,
          created_at,
          language,
          meta.pr_url
        FROM read_parquet(?)
        WHERE repo IN (SELECT unnest(?))
        ORDER BY lower(repo), created_at, instance_id
        """,
        [str(parquet_path), list(aliases)],
    ).fetchall()
    connection.close()

    projections: dict[str, common.TaskProjection] = {}
    visible_fingerprints: dict[str, tuple[str, str, str]] = {}
    source_lineage: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for (
        source_alias,
        source_instance_id,
        base_commit,
        created_at,
        language,
        pull_request_url,
    ) in rows:
        alias = str(source_alias)
        repository_id = alias_to_repository[alias]
        source_id = str(source_instance_id)
        canonical_id = thy2.canonical_task_id(
            repository_id=repository_id,
            source_instance_id=source_id,
            pull_request_url=(
                str(pull_request_url) if pull_request_url is not None else None
            ),
            source_alias=alias,
        )
        source_time = _parse_source_time(str(created_at))
        projection = common.TaskProjection(
            instance_id=canonical_id,
            repository_id=repository_id,
            source_time=source_time,
            base_commit=str(base_commit),
            modules=(),
        )
        fingerprint = (str(base_commit), str(created_at), str(language))
        prior = projections.get(canonical_id)
        if prior is not None and (
            prior != projection or visible_fingerprints[canonical_id] != fingerprint
        ):
            raise ValueError(
                f"canonical Task visible identity disagrees: {canonical_id}"
            )
        projections.setdefault(canonical_id, projection)
        visible_fingerprints.setdefault(canonical_id, fingerprint)
        source_lineage[canonical_id].append(
            {"source_alias": alias, "source_instance_id": source_id}
        )

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
    if len(rows) != _positive_integer(
        source,
        "selected_source_row_count",
    ) or len(tasks) != _positive_integer(source, "canonical_task_count"):
        raise ValueError("Rebench frozen frame count changed")
    observed_counts: dict[str, int] = defaultdict(int)
    for task in tasks:
        observed_counts[task.repository_id] += 1
    if any(
        observed_counts[_required_string(repository, "repository_id")]
        != _positive_integer(repository, "expected_task_count")
        for repository in repositories
    ):
        raise ValueError("Rebench repository Task counts changed")
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
    return tasks, canonical_digest(task_source_ids)


def _parse_source_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        raise ValueError(f"Rebench source timestamp unexpectedly has a zone: {value}")
    return parsed.replace(tzinfo=UTC)


def snapshot_commit(repository: Path, cutoff: datetime) -> str | None:
    """Return the latest first-parent commit selected by the frozen Git query."""
    output = _git(
        repository,
        "rev-list",
        "--first-parent",
        "--max-count=1",
        f"--before={_format_utc(cutoff)}",
        "HEAD",
    )
    return output.strip() or None


def read_dependency_snapshot(
    repository: Path,
    commit_id: str | None,
) -> DependencySnapshot:
    """Read package.json and the first-present lockfile at one commit."""
    if commit_id is None:
        return DependencySnapshot(
            commit_id="",
            lockfile=None,
            dependencies=(),
            missing_reason="no_snapshot_commit",
        )
    root_names = set(
        line
        for line in _git(repository, "ls-tree", "--name-only", commit_id).splitlines()
        if line
    )
    if "package.json" not in root_names:
        return DependencySnapshot(
            commit_id=commit_id,
            lockfile=None,
            dependencies=(),
            missing_reason="root_manifest_missing",
        )
    manifest_bytes = _git_bytes(repository, "show", f"{commit_id}:package.json")
    try:
        manifest = json.loads(manifest_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return DependencySnapshot(
            commit_id=commit_id,
            lockfile=None,
            dependencies=(),
            missing_reason="root_manifest_malformed",
        )
    if not isinstance(manifest, Mapping):
        return DependencySnapshot(
            commit_id=commit_id,
            lockfile=None,
            dependencies=(),
            missing_reason="root_manifest_not_object",
        )
    lockfile = next((name for name in LOCKFILES if name in root_names), None)
    if lockfile is None:
        return DependencySnapshot(
            commit_id=commit_id,
            lockfile=None,
            dependencies=(),
            missing_reason="supported_lockfile_missing",
        )
    lock_bytes = _git_bytes(repository, "show", f"{commit_id}:{lockfile}")
    try:
        dependencies = locked_direct_versions(
            manifest=manifest,
            lockfile=lockfile,
            lock_bytes=lock_bytes,
        )
    except ValueError as error:
        return DependencySnapshot(
            commit_id=commit_id,
            lockfile=lockfile,
            dependencies=(),
            missing_reason=f"lockfile_parse_error:{error}",
        )
    if not dependencies:
        return DependencySnapshot(
            commit_id=commit_id,
            lockfile=lockfile,
            dependencies=(),
            missing_reason="direct_dependencies_empty",
        )
    return DependencySnapshot(
        commit_id=commit_id,
        lockfile=lockfile,
        dependencies=dependencies,
    )


def scan_state_points(
    frame: SourceFrame,
    repository_cache: Path,
) -> tuple[tuple[StatePoint, ...], Mapping[str, Mapping[str, Any]]]:
    """Project every Task and Origin snapshot without registry or labels."""
    repository_specs = {
        _required_string(item, "repository_id"): item for item in frame.repositories
    }
    tasks_by_repository: dict[str, list[common.TaskProjection]] = defaultdict(list)
    for task in frame.tasks:
        tasks_by_repository[task.repository_id].append(task)
    scans = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(
                _scan_repository_state_points,
                repository_id=repository_id,
                repository_spec=repository_specs[repository_id],
                repository_cache=repository_cache,
                tasks=tuple(tasks_by_repository[repository_id]),
                origins=frame.origins[repository_id],
            ): repository_id
            for repository_id in repository_specs
        }
        for future in as_completed(futures):
            scans[futures[future]] = future.result()
    points = tuple(
        point for repository_id in repository_specs for point in scans[repository_id][0]
    )
    manifests = {
        repository_id: scans[repository_id][1] for repository_id in repository_specs
    }
    return points, manifests


def _scan_repository_state_points(
    *,
    repository_id: str,
    repository_spec: Mapping[str, object],
    repository_cache: Path,
    tasks: Sequence[common.TaskProjection],
    origins: Sequence[OriginFrame],
) -> tuple[tuple[StatePoint, ...], Mapping[str, Any]]:
    repository = common.repository_path(repository_cache, repository_id)
    if not repository.is_dir():
        raise ValueError(f"repository cache is missing: {repository_id}")
    expected_head = _required_string(repository_spec, "head_commit")
    observed_head = _git(repository, "rev-parse", "HEAD").strip()
    if observed_head != expected_head:
        raise ValueError(f"repository HEAD changed: {repository_id}")
    snapshot_cache: dict[str, DependencySnapshot] = {}

    def cached_snapshot(commit_id: str) -> DependencySnapshot:
        if commit_id not in snapshot_cache:
            snapshot_cache[commit_id] = read_dependency_snapshot(
                repository,
                commit_id,
            )
        return snapshot_cache[commit_id]

    points = []
    historical_missing = 0
    lockfile_counts: dict[str, int] = defaultdict(int)
    for task in tasks:
        commit_id = snapshot_commit(repository, task.source_time)
        snapshot = (
            cached_snapshot(commit_id)
            if commit_id is not None
            else read_dependency_snapshot(repository, None)
        )
        if not snapshot.supported:
            historical_missing += 1
        elif snapshot.lockfile is not None:
            lockfile_counts[snapshot.lockfile] += 1
        points.append(
            StatePoint(
                repository_id=repository_id,
                kind="task",
                state_id=task.instance_id,
                cutoff=task.source_time,
                commit_id=commit_id,
                snapshot=snapshot,
            )
        )
    origin_missing = 0
    origin_inputs = []
    for origin_frame in origins:
        origin = origin_frame.projection
        observed_commit = snapshot_commit(repository, origin.cutoff)
        if observed_commit != origin_frame.origin_commit:
            raise ValueError(f"Origin commit changed: {origin.origin_id}")
        snapshot = cached_snapshot(origin_frame.origin_commit)
        if not snapshot.supported:
            origin_missing += 1
        elif snapshot.lockfile is not None:
            lockfile_counts[snapshot.lockfile] += 1
        points.append(
            StatePoint(
                repository_id=repository_id,
                kind="origin",
                state_id=origin.origin_id,
                cutoff=origin.cutoff,
                commit_id=origin_frame.origin_commit,
                snapshot=snapshot,
            )
        )
        origin_inputs.append(
            {
                "origin_id": origin.origin_id,
                "origin_commit": origin_frame.origin_commit,
                "snapshot_digest": snapshot_digest(snapshot),
            }
        )
    manifest: dict[str, Any] = {
        "repository_id": repository_id,
        "repository_head": observed_head,
        "task_count": len(tasks),
        "origin_count": len(origins),
        "historical_missing_state_count": historical_missing,
        "origin_missing_state_count": origin_missing,
        "lockfile_state_counts": dict(sorted(lockfile_counts.items())),
        "origin_snapshot_digest": canonical_digest(tuple(origin_inputs)),
    }
    manifest["repository_scan_manifest_digest"] = canonical_digest(manifest)
    return tuple(points), manifest


def snapshot_digest(snapshot: DependencySnapshot) -> str:
    """Digest the complete candidate-visible snapshot projection."""
    return canonical_digest(
        {
            "commit_id": snapshot.commit_id,
            "lockfile": snapshot.lockfile,
            "missing_reason": snapshot.missing_reason,
            "dependencies": tuple(
                {
                    "name": item.name,
                    "scope": item.scope,
                    "specifier": item.specifier,
                    "locked_version": item.locked_version,
                }
                for item in snapshot.dependencies
            ),
        }
    )


def acquire_registry(
    packages: Sequence[str],
    raw_root: Path,
    *,
    workers: int = 8,
) -> Mapping[str, Any]:
    """Fetch each full npm packument once, retaining exact response bytes."""
    unique = tuple(sorted(set(packages), key=lambda item: (item.casefold(), item)))
    if not unique:
        raise ValueError("registry acquisition package set is empty")
    raw_root.mkdir(parents=True, exist_ok=True)
    response_root = raw_root / "responses"
    response_root.mkdir(parents=True, exist_ok=True)
    progress_path = raw_root / "acquisition-progress.json"
    prior_rows: dict[str, Mapping[str, Any]] = {}
    if progress_path.exists():
        progress = _load_mapping(progress_path)
        for row in _mapping_sequence(progress, "responses"):
            package = _required_string(row, "package")
            _verify_registry_response_row(row, raw_root)
            prior_rows[package] = row
    if set(prior_rows) - set(unique):
        raise ValueError("registry progress contains an unexpected package")

    rows: dict[str, Mapping[str, Any]] = dict(prior_rows)
    missing = tuple(package for package in unique if package not in rows)
    errors: list[str] = []
    if missing:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_fetch_packument, package, raw_root): package
                for package in missing
            }
            for future in as_completed(futures):
                package = futures[future]
                try:
                    rows[package] = future.result()
                except (OSError, urllib.error.URLError, ValueError) as error:
                    errors.append(f"{package}: {type(error).__name__}: {error}")
                _write_registry_progress(progress_path, rows)
    if errors:
        raise RuntimeError(
            "registry acquisition is externally blocked: " + "; ".join(sorted(errors))
        )
    ordered = tuple(rows[package] for package in unique)
    for row in ordered:
        _verify_registry_response_row(row, raw_root)
    manifest: dict[str, Any] = {
        "schema_version": REGISTRY_MANIFEST_SCHEMA,
        "registry": "https://registry.npmjs.org/",
        "request_accept": "application/json",
        "package_count": len(unique),
        "package_digest": canonical_digest(unique),
        "response_count": len(ordered),
        "response_bytes": sum(
            _positive_integer(row, "byte_count", allow_zero=True) for row in ordered
        ),
        "responses": ordered,
    }
    manifest["registry_manifest_digest"] = canonical_digest(manifest)
    _write_json(raw_root / "manifest.json", manifest)
    return manifest


def _fetch_packument(package: str, raw_root: Path) -> Mapping[str, Any]:
    encoded = urllib.parse.quote(package, safe="")
    url = f"https://registry.npmjs.org/{encoded}"
    attempts = []
    body = b""
    final_url = url
    status = 0
    queried_at = ""
    for attempt in range(1, 4):
        queried_at = _format_utc(datetime.now(UTC))
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "barcarolle-thy003-stage-a/1",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                status = int(response.status)
                final_url = response.geturl()
                body = response.read()
        except urllib.error.HTTPError as error:
            status = int(error.code)
            final_url = error.geturl()
            body = error.read()
        attempts.append(
            {
                "attempt": attempt,
                "queried_at": queried_at,
                "status": status,
            }
        )
        if status not in {429, 500, 502, 503, 504} or attempt == 3:
            break
        time.sleep(float(attempt))
    digest = hashlib.sha256(body).hexdigest()
    relative = PurePosixPath("responses") / (
        hashlib.sha256(package.encode("utf-8")).hexdigest() + ".bin"
    )
    target = raw_root / relative
    target.write_bytes(body)
    return {
        "package": package,
        "request_url": url,
        "response_url": final_url,
        "status": status,
        "queried_at": queried_at,
        "attempts": tuple(attempts),
        "path": relative.as_posix(),
        "byte_count": len(body),
        "sha256": digest,
    }


def _write_registry_progress(
    path: Path,
    rows: Mapping[str, Mapping[str, Any]],
) -> None:
    payload = {
        "schema_version": "barcarolle_dependency_lag_registry_progress_v1",
        "responses": tuple(
            rows[key] for key in sorted(rows, key=lambda item: (item.casefold(), item))
        ),
    }
    _write_json(path, payload)


def _verify_registry_response_row(
    row: Mapping[str, object],
    raw_root: Path,
) -> None:
    relative = PurePosixPath(_required_string(row, "path"))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("registry response path escapes raw root")
    path = raw_root.joinpath(*relative.parts)
    if not path.is_file():
        raise ValueError(f"registry response is missing: {path}")
    if path.stat().st_size != _positive_integer(row, "byte_count", allow_zero=True):
        raise ValueError("registry response byte count changed")
    _verify_sha256(path, _required_string(row, "sha256"))


def load_registry_manifest(
    path: Path,
    *,
    expected_digest: str | None = None,
) -> tuple[Mapping[str, Any], Mapping[str, Mapping[tuple[int, int, int], datetime]]]:
    """Reload-verify raw bytes and expose only version publication times."""
    manifest = _load_mapping(path)
    if manifest.get("schema_version") != REGISTRY_MANIFEST_SCHEMA:
        raise ValueError("THY-003 registry manifest schema is unsupported")
    payload = dict(manifest)
    digest = payload.pop("registry_manifest_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("THY-003 registry manifest digest does not match")
    if expected_digest is not None and digest != expected_digest:
        raise ValueError("THY-003 registry manifest does not bind execution lock")
    raw_root = path.parent
    packages: dict[str, Mapping[tuple[int, int, int], datetime]] = {}
    seen: set[str] = set()
    total_bytes = 0
    for row in _mapping_sequence(manifest, "responses"):
        package = _required_string(row, "package")
        if package in seen:
            raise ValueError("THY-003 registry package is duplicated")
        seen.add(package)
        _verify_registry_response_row(row, raw_root)
        relative = PurePosixPath(_required_string(row, "path"))
        body = raw_root.joinpath(*relative.parts).read_bytes()
        total_bytes += len(body)
        if row.get("status") != 200:
            packages[package] = {}
            continue
        try:
            packument = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"packument is malformed: {package}") from error
        if not isinstance(packument, Mapping) or packument.get("name") != package:
            raise ValueError(f"packument package identity changed: {package}")
        versions = packument.get("versions", {})
        times = packument.get("time", {})
        if not isinstance(versions, Mapping) or not isinstance(times, Mapping):
            raise ValueError(f"packument version/time maps are missing: {package}")
        projection: dict[tuple[int, int, int], datetime] = {}
        for raw_version in versions:
            version = parse_strict_semver(raw_version)
            raw_timestamp = times.get(raw_version)
            if version is None or not isinstance(raw_timestamp, str):
                continue
            try:
                published = _parse_registry_time(raw_timestamp)
            except ValueError:
                continue
            projection[version] = published
        packages[package] = projection
    if len(seen) != _positive_integer(manifest, "package_count"):
        raise ValueError("THY-003 registry package count changed")
    if len(seen) != _positive_integer(manifest, "response_count"):
        raise ValueError("THY-003 registry response count changed")
    if total_bytes != _positive_integer(manifest, "response_bytes", allow_zero=True):
        raise ValueError("THY-003 registry response total changed")
    if canonical_digest(
        tuple(sorted(seen, key=lambda item: (item.casefold(), item)))
    ) != manifest.get("package_digest"):
        raise ValueError("THY-003 registry package identity changed")
    return manifest, packages


def _parse_registry_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("registry publication time is timezone-naive")
    return parsed.astimezone(UTC)


def dependency_state(
    snapshot: DependencySnapshot,
    cutoff: datetime,
    registry: Mapping[str, Mapping[tuple[int, int, int], datetime]],
) -> tuple[StateVector | None, int]:
    """Compute registry-dated state and eligible-resolution cell count."""
    if not snapshot.supported:
        return None, 0
    counts = [0] * 10
    eligible_resolution_count = 0
    for dependency in snapshot.dependencies:
        category = "unknown"
        locked = parse_strict_semver(dependency.locked_version)
        publications = registry.get(dependency.name, {})
        if locked is not None:
            locked_time = publications.get(locked)
            if locked_time is not None and locked_time <= cutoff:
                eligible_resolution_count += 1
                eligible = tuple(
                    version
                    for version, published in publications.items()
                    if published <= cutoff
                )
                if eligible:
                    latest = max(eligible)
                    category = classify_lag(locked, latest)
        scope_index = SCOPES.index(dependency.scope)
        category_index = LAG_CATEGORIES.index(category)
        counts[(scope_index * len(LAG_CATEGORIES)) + category_index] += 1
    return StateVector(
        tuple(counts), len(snapshot.dependencies)
    ), eligible_resolution_count


def lock_only_state(snapshot: DependencySnapshot) -> StateVector | None:
    """Project exact lock resolutions to current and retain unknown."""
    if not snapshot.supported:
        return None
    counts = [0] * 10
    for dependency in snapshot.dependencies:
        category = (
            "current"
            if parse_strict_semver(dependency.locked_version) is not None
            else "unknown"
        )
        counts[
            (SCOPES.index(dependency.scope) * len(LAG_CATEGORIES))
            + LAG_CATEGORIES.index(category)
        ] += 1
    return StateVector(tuple(counts), len(snapshot.dependencies))


def classify_lag(
    locked: tuple[int, int, int],
    latest: tuple[int, int, int],
) -> str:
    """Apply the frozen exact lag taxonomy."""
    if locked == latest:
        return "current"
    if locked > latest:
        return "unknown"
    if locked[0] != latest[0]:
        return "major_lag"
    if locked[1] != latest[1]:
        return "minor_lag"
    return "patch_lag"


def state_distance(
    historical: StateVector | None,
    origin: StateVector,
) -> Fraction:
    """Compute exact half-L1; missing historical state is distance one."""
    if historical is None:
        return Fraction(1, 1)
    return (
        sum(
            (
                abs(left - right)
                for left, right in zip(
                    historical.fractions(),
                    origin.fractions(),
                    strict=True,
                )
            ),
            start=Fraction(0, 1),
        )
        / 2
    )


def select_nearest_regime(
    *,
    study_id: str,
    repository_id: str,
    origin_id: str,
    history_task_ids: Sequence[str],
    task_states: Mapping[str, StateVector | None],
    origin_state: StateVector,
    budget: int,
) -> SelectionProjection:
    """Rank only candidate-visible Task state and the frozen identity tie-break."""
    if budget <= 0 or len(history_task_ids) < budget:
        raise ValueError("THY-003 selection budget exceeds history")
    distances = {
        task_id: state_distance(task_states.get(task_id), origin_state)
        for task_id in history_task_ids
    }
    ordered = tuple(
        sorted(
            history_task_ids,
            key=lambda task_id: (
                distances[task_id],
                hashlib.sha256(
                    "\0".join((study_id, repository_id, origin_id, task_id)).encode(
                        "utf-8"
                    )
                ).hexdigest(),
            ),
        )
    )
    return SelectionProjection(
        selected_task_ids=ordered[:budget],
        distances=distances,
    )


def weighted_rate(
    task_ids: Sequence[str],
    labels: Mapping[str, int],
    distances: Mapping[str, Fraction],
) -> Fraction:
    """Compute the frozen max(0, 1-distance) historical forecast."""
    weights = tuple(max(Fraction(0, 1), 1 - distances[task_id]) for task_id in task_ids)
    total = sum(weights, start=Fraction(0, 1))
    if total == 0:
        return unweighted_rate(task_ids, labels)
    positive = sum(
        (
            weight * labels[task_id]
            for task_id, weight in zip(task_ids, weights, strict=True)
        ),
        start=Fraction(0, 1),
    )
    return positive / total


def unweighted_rate(
    task_ids: Sequence[str],
    labels: Mapping[str, int],
) -> Fraction:
    if not task_ids:
        raise ValueError("forecast Task set is empty")
    return Fraction(sum(labels[task_id] for task_id in task_ids), len(task_ids))


def binary_brier(labels: Sequence[int], forecast: Fraction | float) -> float:
    """Mean scalar binary Brier loss."""
    if not labels:
        raise ValueError("future labels are empty")
    probability = float(forecast)
    return fsum((probability - value) ** 2 for value in labels) / len(labels)


def build_state_index(
    points: Sequence[StatePoint],
    registry: Mapping[str, Mapping[tuple[int, int, int], datetime]],
) -> tuple[
    Mapping[str, StateVector | None],
    Mapping[str, StateVector | None],
    Mapping[str, StateVector | None],
    Mapping[str, StateVector | None],
    Mapping[str, Any],
]:
    """Build true and lock-only Task/Origin state maps plus admission evidence."""
    task_states: dict[str, StateVector | None] = {}
    origin_states: dict[str, StateVector | None] = {}
    task_lock_states: dict[str, StateVector | None] = {}
    origin_lock_states: dict[str, StateVector | None] = {}
    denominator = 0
    numerator = 0
    missing_tasks: dict[str, int] = defaultdict(int)
    missing_origins: dict[str, int] = defaultdict(int)
    origin_vectors: dict[str, set[tuple[Fraction, ...]]] = defaultdict(set)
    point_rows = []
    for point in points:
        state, resolved = dependency_state(point.snapshot, point.cutoff, registry)
        lock_state = lock_only_state(point.snapshot)
        denominator += len(point.snapshot.dependencies)
        numerator += resolved
        target = task_states if point.kind == "task" else origin_states
        lock_target = task_lock_states if point.kind == "task" else origin_lock_states
        if point.state_id in target:
            raise ValueError(f"duplicate THY-003 state point: {point.state_id}")
        target[point.state_id] = state
        lock_target[point.state_id] = lock_state
        if point.kind == "task" and state is None:
            missing_tasks[point.repository_id] += 1
        if point.kind == "origin":
            if state is None:
                missing_origins[point.repository_id] += 1
            else:
                origin_vectors[point.repository_id].add(state.fractions())
        point_rows.append(
            {
                "repository_id": point.repository_id,
                "kind": point.kind,
                "state_id": point.state_id,
                "cutoff": _format_utc(point.cutoff),
                "commit_id": point.commit_id,
                "snapshot_digest": snapshot_digest(point.snapshot),
                "state": state_record(state),
                "lock_only_state": state_record(lock_state),
                "declared_dependency_count": len(point.snapshot.dependencies),
                "eligible_resolution_count": resolved,
            }
        )
    coverage = Fraction(numerator, denominator) if denominator else Fraction(0, 1)
    summary = {
        "state_point_count": len(points),
        "coverage_numerator": numerator,
        "coverage_denominator": denominator,
        "coverage": float(coverage),
        "historical_missing_state_count": sum(missing_tasks.values()),
        "origin_missing_state_count": sum(missing_origins.values()),
        "historical_missing_by_repository": dict(sorted(missing_tasks.items())),
        "origin_missing_by_repository": dict(sorted(missing_origins.items())),
        "distinct_origin_state_count_by_repository": {
            repository_id: len(origin_vectors.get(repository_id, set()))
            for repository_id in sorted(
                {point.repository_id for point in points},
                key=lambda value: (value.casefold(), value),
            )
        },
        "state_point_digest": canonical_digest(tuple(point_rows)),
    }
    return (
        task_states,
        origin_states,
        task_lock_states,
        origin_lock_states,
        summary,
    )


def state_record(state: StateVector | None) -> Mapping[str, object] | None:
    if state is None:
        return None
    return {"counts": state.counts, "total": state.total}


def build_memberships(
    *,
    plan: Mapping[str, object],
    frame: SourceFrame,
    task_states: Mapping[str, StateVector | None],
    origin_states: Mapping[str, StateVector | None],
    task_lock_states: Mapping[str, StateVector | None],
    origin_lock_states: Mapping[str, StateVector | None],
) -> tuple[
    Mapping[str, Mapping[str, SelectionProjection]],
    Mapping[str, Mapping[str, SelectionProjection]],
    Mapping[str, Mapping[str, Mapping[int, SelectionProjection]]],
    str,
]:
    """Build true, lock-only, and all circular-donor memberships before labels."""
    study_id = _required_string(plan, "study_id")
    budget = _positive_integer(_mapping(plan, "candidate"), "selection_budget")
    true_memberships: dict[str, dict[str, SelectionProjection]] = {}
    lock_memberships: dict[str, dict[str, SelectionProjection]] = {}
    null_memberships: dict[str, dict[str, dict[int, SelectionProjection]]] = {}
    digest_rows = []
    for repository_id in _string_sequence(
        _mapping(plan, "source").get("wide_repositories"),
        "wide repositories",
    ):
        true_memberships[repository_id] = {}
        lock_memberships[repository_id] = {}
        null_memberships[repository_id] = {}
        repository_origins = frame.origins[repository_id]
        for origin_index, origin_frame in enumerate(repository_origins):
            origin = origin_frame.projection
            true_state = origin_states.get(origin.origin_id)
            lock_state = origin_lock_states.get(origin.origin_id)
            if true_state is None or lock_state is None:
                continue
            history_ids = tuple(task.instance_id for task in origin.history)
            true_selection = select_nearest_regime(
                study_id=study_id,
                repository_id=repository_id,
                origin_id=origin.origin_id,
                history_task_ids=history_ids,
                task_states=task_states,
                origin_state=true_state,
                budget=budget,
            )
            lock_selection = select_nearest_regime(
                study_id=study_id,
                repository_id=repository_id,
                origin_id=origin.origin_id,
                history_task_ids=history_ids,
                task_states=task_lock_states,
                origin_state=lock_state,
                budget=budget,
            )
            true_memberships[repository_id][origin.origin_id] = true_selection
            lock_memberships[repository_id][origin.origin_id] = lock_selection
            donors = {}
            for offset in range(1, len(repository_origins)):
                donor = repository_origins[
                    (origin_index + offset) % len(repository_origins)
                ].projection
                donor_state = origin_states.get(donor.origin_id)
                if donor_state is None:
                    continue
                donors[offset] = select_nearest_regime(
                    study_id=study_id,
                    repository_id=repository_id,
                    origin_id=origin.origin_id,
                    history_task_ids=history_ids,
                    task_states=task_states,
                    origin_state=donor_state,
                    budget=budget,
                )
            null_memberships[repository_id][origin.origin_id] = donors
            digest_rows.append(
                {
                    "repository_id": repository_id,
                    "origin_id": origin.origin_id,
                    "candidate_selected_task_ids": true_selection.selected_task_ids,
                    "candidate_distance_digest": fraction_mapping_digest(
                        true_selection.distances
                    ),
                    "lock_only_selected_task_ids": lock_selection.selected_task_ids,
                    "lock_only_distance_digest": fraction_mapping_digest(
                        lock_selection.distances
                    ),
                    "null_membership_digest": canonical_digest(
                        tuple(
                            {
                                "offset": offset,
                                "selected_task_ids": donors[offset].selected_task_ids,
                                "distance_digest": fraction_mapping_digest(
                                    donors[offset].distances
                                ),
                            }
                            for offset in sorted(donors)
                        )
                    ),
                }
            )
    return (
        true_memberships,
        lock_memberships,
        null_memberships,
        canonical_digest(tuple(digest_rows)),
    )


def fraction_mapping_digest(values: Mapping[str, Fraction]) -> str:
    return canonical_digest(
        tuple(
            {
                "task_id": task_id,
                "numerator": value.numerator,
                "denominator": value.denominator,
            }
            for task_id, value in sorted(values.items())
        )
    )


def load_scoring_labels(
    plan: Mapping[str, object],
    addendum: Mapping[str, object],
    frame: SourceFrame,
) -> Mapping[str, int]:
    """Load retrospective reference-patch labels after membership freeze."""
    try:
        import duckdb
    except ImportError as error:
        raise RuntimeError(
            "DuckDB is required; run with `uv run --with duckdb`"
        ) from error
    source = _mapping(plan, "source")
    parquet = REPOSITORY_ROOT / _required_string(source, "parquet")
    _verify_sha256(parquet, _required_string(source, "parquet_sha256"))
    repository_ids = _string_sequence(
        source.get("wide_repositories"),
        "wide repositories",
    )
    connection = duckdb.connect()
    rows = connection.execute(
        """
        SELECT repo, instance_id, created_at, patch, meta.pr_url
        FROM read_parquet(?)
        WHERE repo IN (SELECT unnest(?))
        ORDER BY repo, created_at, instance_id
        """,
        [str(parquet), list(repository_ids)],
    ).fetchall()
    connection.close()
    labels: dict[str, int] = {}
    feasibility_projection = []
    for repository_id in repository_ids:
        for (
            source_repository,
            source_instance_id,
            _,
            patch,
            pull_request_url,
        ) in rows:
            if str(source_repository) != repository_id:
                continue
            canonical_id = thy2.canonical_task_id(
                repository_id=repository_id,
                source_instance_id=str(source_instance_id),
                pull_request_url=(
                    str(pull_request_url) if pull_request_url is not None else None
                ),
                source_alias=repository_id,
            )
            label = int(patch_touches_root_dependency(str(patch)))
            prior = labels.get(canonical_id)
            if prior is not None and prior != label:
                raise ValueError(f"duplicate Task label disagrees: {canonical_id}")
            labels[canonical_id] = label
            feasibility_projection.append(
                [repository_id, str(source_instance_id), bool(label)]
            )
    expected_ids = {task.instance_id for task in frame.tasks}
    if set(labels) != expected_ids:
        raise ValueError("THY-003 scoring labels do not match Task frame")
    expected_digest = _mapping(addendum, "scoring_label").get("label_projection_digest")
    observed = hashlib.sha256(
        json.dumps(feasibility_projection, separators=(",", ":")).encode()
    ).hexdigest()
    if observed != expected_digest:
        raise ValueError("THY-003 scoring label projection changed")
    return labels


def patch_touches_root_dependency(patch: str) -> bool:
    """Project only root manifest/lock names from diff headers."""
    for line in patch.splitlines():
        if not line.startswith("diff --git "):
            continue
        for raw_path in _diff_header_paths(line):
            path = raw_path.removeprefix("a/").removeprefix("b/")
            pure = PurePosixPath(path)
            if len(pure.parts) == 1 and pure.name in SCORING_FILES:
                return True
    return False


def _diff_header_paths(line: str) -> tuple[str, str]:
    payload = line.removeprefix("diff --git ")
    if payload.startswith('"'):
        try:
            paths = tuple(shlex.split(payload))
        except ValueError as error:
            raise ValueError(
                "reference patch contains an invalid diff header"
            ) from error
        if len(paths) != 2:
            raise ValueError("quoted diff header does not contain two paths")
        return paths[0], paths[1]
    separator = " b/"
    if not payload.startswith("a/") or separator not in payload:
        raise ValueError("reference patch contains an unsupported diff header")
    old_path, new_suffix = payload.split(separator, maxsplit=1)
    return old_path, f"b/{new_suffix}"


def evaluate_origins(
    *,
    plan: Mapping[str, object],
    frame: SourceFrame,
    labels: Mapping[str, int],
    true_memberships: Mapping[str, Mapping[str, SelectionProjection]],
    lock_memberships: Mapping[str, Mapping[str, SelectionProjection]],
    null_memberships: Mapping[str, Mapping[str, Mapping[int, SelectionProjection]]],
) -> tuple[tuple[Mapping[str, Any], ...], Mapping[str, Mapping[int, float]]]:
    """Score frozen memberships and precompute each temporal-null offset."""
    rows = []
    null_offsets: dict[str, dict[int, float]] = {}
    for repository_id in _string_sequence(
        _mapping(plan, "source").get("wide_repositories"),
        "wide repositories",
    ):
        repository_rows: list[Mapping[str, Any]] = []
        repository_origins = frame.origins[repository_id]
        for origin_frame in repository_origins:
            origin = origin_frame.projection
            true_selection = true_memberships.get(repository_id, {}).get(
                origin.origin_id
            )
            lock_selection = lock_memberships.get(repository_id, {}).get(
                origin.origin_id
            )
            if true_selection is None or lock_selection is None:
                continue
            history_ids = tuple(task.instance_id for task in origin.history)
            predictions_base = {
                "candidate_continuous": weighted_rate(
                    history_ids,
                    labels,
                    true_selection.distances,
                ),
                "candidate_materialized": unweighted_rate(
                    true_selection.selected_task_ids,
                    labels,
                ),
                "task_full_history": unweighted_rate(history_ids, labels),
                "lock_only_continuous": weighted_rate(
                    history_ids,
                    labels,
                    lock_selection.distances,
                ),
                "lock_only_materialized": unweighted_rate(
                    lock_selection.selected_task_ids,
                    labels,
                ),
            }
            for horizon, future in (
                (5, origin.future_h5),
                (10, origin.future_h10),
            ):
                future_ids = tuple(task.instance_id for task in future)
                predictions = {
                    **predictions_base,
                    "task_trailing_h": unweighted_rate(
                        history_ids[-horizon:],
                        labels,
                    ),
                }
                future_labels = tuple(labels[task_id] for task_id in future_ids)
                losses = {
                    predictor: binary_brier(future_labels, predictions[predictor])
                    for predictor in PREDICTORS
                }
                row = {
                    "repository_id": repository_id,
                    "origin_id": origin.origin_id,
                    "origin_cutoff": _format_utc(origin.cutoff),
                    "origin_commit": origin_frame.origin_commit,
                    "horizon": horizon,
                    "history_task_count": len(history_ids),
                    "future_task_count": len(future_ids),
                    "future_calendar_span_days": common.future_horizon_span_days(
                        origin.cutoff,
                        future,
                    ),
                    "future_positive_rate": float(unweighted_rate(future_ids, labels)),
                    "forecasts": {
                        predictor: float(predictions[predictor])
                        for predictor in PREDICTORS
                    },
                    "losses": losses,
                    "candidate_selected_task_ids": true_selection.selected_task_ids,
                    "candidate_selected_digest": canonical_digest(
                        true_selection.selected_task_ids
                    ),
                    "candidate_distance_digest": fraction_mapping_digest(
                        true_selection.distances
                    ),
                    "lock_only_selected_task_ids": lock_selection.selected_task_ids,
                    "lock_only_selected_digest": canonical_digest(
                        lock_selection.selected_task_ids
                    ),
                    "lock_only_distance_digest": fraction_mapping_digest(
                        lock_selection.distances
                    ),
                    "history_task_digest": canonical_digest(history_ids),
                    "future_task_digest": canonical_digest(future_ids),
                }
                rows.append(row)
                repository_rows.append(row)

        offsets = {}
        for offset in range(1, len(repository_origins)):
            origin_contrasts = []
            for origin_frame in repository_origins:
                origin = origin_frame.projection
                selection = (
                    null_memberships.get(repository_id, {})
                    .get(origin.origin_id, {})
                    .get(offset)
                )
                if selection is None:
                    continue
                history_ids = tuple(task.instance_id for task in origin.history)
                future_ids = tuple(task.instance_id for task in origin.future_h5)
                forecast = unweighted_rate(selection.selected_task_ids, labels)
                full = unweighted_rate(history_ids, labels)
                future_labels = tuple(labels[task_id] for task_id in future_ids)
                origin_contrasts.append(
                    binary_brier(future_labels, forecast)
                    - binary_brier(future_labels, full)
                )
            if origin_contrasts:
                offsets[offset] = fsum(origin_contrasts) / len(origin_contrasts)
        null_offsets[repository_id] = offsets
    return (
        tuple(
            sorted(
                rows,
                key=lambda row: (
                    str(row["repository_id"]).casefold(),
                    str(row["origin_id"]),
                    int(row["horizon"]),
                ),
            )
        ),
        null_offsets,
    )


def summarize_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    wide_repositories: Sequence[str],
    deep_repositories: Sequence[str],
    bootstrap_seed: int,
) -> Mapping[str, Any]:
    """Aggregate Tasks→Origins→repositories and apply paired uncertainty."""
    repositories = tuple(wide_repositories)
    deep = tuple(deep_repositories)
    if len(repositories) != len(set(repositories)) or not set(deep).issubset(
        repositories
    ):
        raise ValueError("THY-003 wide/deep repository frame is invalid")
    grouped: dict[tuple[int, str], list[Mapping[str, object]]] = defaultdict(list)
    seen: set[tuple[str, str, int]] = set()
    origin_horizons: dict[tuple[str, str], set[int]] = defaultdict(set)
    for row in rows:
        repository_id = _required_string(row, "repository_id")
        origin_id = _required_string(row, "origin_id")
        horizon = _positive_integer(row, "horizon")
        key = (repository_id, origin_id, horizon)
        if repository_id not in repositories or key in seen or horizon not in (5, 10):
            raise ValueError("THY-003 Origin result identity is invalid")
        seen.add(key)
        origin_horizons[(repository_id, origin_id)].add(horizon)
        grouped[(horizon, repository_id)].append(row)
    if any(value != {5, 10} for value in origin_horizons.values()):
        raise ValueError("THY-003 Origin H5/H10 pairs are incomplete")

    bootstrap_matrix = _bootstrap_matrix(
        repository_count=len(repositories),
        draws=20000,
        seed=bootstrap_seed,
    )
    horizons = {}
    for horizon in (5, 10):
        repository_rows = []
        for repository_id in repositories:
            origin_rows = grouped.get((horizon, repository_id), ())
            if not origin_rows:
                continue
            losses = {
                predictor: fsum(
                    _number(_mapping(row, "losses"), predictor) for row in origin_rows
                )
                / len(origin_rows)
                for predictor in PREDICTORS
            }
            spans = sorted(
                _number(row, "future_calendar_span_days") for row in origin_rows
            )
            contrasts = {
                "continuous_vs_full": (
                    losses["candidate_continuous"] - losses["task_full_history"]
                ),
                "materialized_vs_full": (
                    losses["candidate_materialized"] - losses["task_full_history"]
                ),
                "materialized_vs_trailing": (
                    losses["candidate_materialized"] - losses["task_trailing_h"]
                ),
                "materialized_vs_lock_only": (
                    losses["candidate_materialized"] - losses["lock_only_materialized"]
                ),
                "materialized_vs_continuous": (
                    losses["candidate_materialized"] - losses["candidate_continuous"]
                ),
                "lock_only_continuous_vs_full": (
                    losses["lock_only_continuous"] - losses["task_full_history"]
                ),
            }
            repository_rows.append(
                {
                    "repository_id": repository_id,
                    "origin_count": len(origin_rows),
                    "losses": losses,
                    "contrasts": contrasts,
                    "future_calendar_span_days": {
                        "mean": fsum(spans) / len(spans),
                        "median": _median(spans),
                        "minimum": spans[0],
                        "maximum": spans[-1],
                    },
                }
            )
        if len(repository_rows) != len(repositories):
            raise ValueError(f"THY-003 H{horizon} repository frame is incomplete")
        macro_losses = {
            predictor: fsum(
                _number(_mapping(row, "losses"), predictor) for row in repository_rows
            )
            / len(repository_rows)
            for predictor in PREDICTORS
        }
        contrast_ids = tuple(_mapping(repository_rows[0], "contrasts").keys())
        macro_contrasts = {}
        for contrast_id in contrast_ids:
            values = tuple(
                _number(_mapping(row, "contrasts"), contrast_id)
                for row in repository_rows
            )
            draws = tuple(
                fsum(values[index] for index in sample) / len(sample)
                for sample in bootstrap_matrix
            )
            ordered_draws = sorted(draws)
            macro_contrasts[contrast_id] = {
                "macro_repository": fsum(values) / len(values),
                "favorable_repository_count": sum(value < 0.0 for value in values),
                "repository_count": len(values),
                "bootstrap_95_interval": (
                    ordered_draws[500],
                    ordered_draws[19500],
                ),
                "leave_one_repository_out": tuple(
                    {
                        "omitted_repository_id": repositories[omitted],
                        "contrast": fsum(
                            value
                            for index, value in enumerate(values)
                            if index != omitted
                        )
                        / (len(values) - 1),
                    }
                    for omitted in range(len(values))
                ),
            }
        deep_rows = tuple(
            row for row in repository_rows if row["repository_id"] in deep
        )
        deep_contrasts = {
            contrast_id: fsum(
                _number(_mapping(row, "contrasts"), contrast_id) for row in deep_rows
            )
            / len(deep_rows)
            for contrast_id in contrast_ids
        }
        horizons[str(horizon)] = {
            "repository_count": len(repository_rows),
            "origin_count": sum(
                _positive_integer(row, "origin_count") for row in repository_rows
            ),
            "macro_losses": macro_losses,
            "contrasts": macro_contrasts,
            "deep_repository_count": len(deep_rows),
            "deep_contrasts": deep_contrasts,
            "repositories": tuple(repository_rows),
        }
    return {
        "wide_repository_count": len(repositories),
        "deep_repository_count": len(deep),
        "bootstrap_draws": 20000,
        "bootstrap_seed": bootstrap_seed,
        "bootstrap_matrix_digest": canonical_digest(bootstrap_matrix),
        "horizons": horizons,
    }


def _bootstrap_matrix(
    *,
    repository_count: int,
    draws: int,
    seed: int,
) -> tuple[tuple[int, ...], ...]:
    generator = random.Random(seed)
    return tuple(
        tuple(generator.randrange(repository_count) for _ in range(repository_count))
        for _ in range(draws)
    )


def temporal_null_summary(
    offset_contrasts: Mapping[str, Mapping[int, float]],
    *,
    repositories: Sequence[str],
    true_contrast: float,
    seed: int,
) -> Mapping[str, Any]:
    """Run the frozen independent nonzero circular shift diagnostic."""
    ordered_repositories = tuple(repositories)
    if any(not offset_contrasts.get(repository_id) for repository_id in repositories):
        raise ValueError("THY-003 temporal-null offsets are incomplete")
    generator = random.Random(seed)
    draws = []
    chosen_rows = []
    for _ in range(20000):
        selected = []
        values = []
        for repository_id in ordered_repositories:
            offsets = offset_contrasts[repository_id]
            offset = generator.randrange(1, len(offsets) + 1)
            if offset not in offsets:
                raise ValueError("THY-003 temporal-null offset identities changed")
            selected.append(offset)
            values.append(offsets[offset])
        draws.append(fsum(values) / len(values))
        chosen_rows.append(tuple(selected))
    ordered = sorted(draws)
    return {
        "draw_count": len(draws),
        "seed": seed,
        "true_h5_materialized_vs_full": true_contrast,
        "as_good_or_better_count": sum(value <= true_contrast for value in draws),
        "as_good_or_better_rate": (
            sum(value <= true_contrast for value in draws) / len(draws)
        ),
        "null_contrast_quantiles": {
            "p025": ordered[500],
            "p50": ordered[10000],
            "p975": ordered[19500],
        },
        "offset_choice_digest": canonical_digest(tuple(chosen_rows)),
        "draw_digest": canonical_digest(tuple(draws)),
        "repository_offset_contrasts": tuple(
            {
                "repository_id": repository_id,
                "offsets": tuple(
                    {
                        "offset": offset,
                        "contrast": offset_contrasts[repository_id][offset],
                    }
                    for offset in sorted(offset_contrasts[repository_id])
                ),
            }
            for repository_id in ordered_repositories
        ),
    }


def decide(
    *,
    summary: Mapping[str, object],
    state_summary: Mapping[str, object],
    temporal_null: Mapping[str, object],
    raw_registry_verified: bool,
    expected_origin_count: int,
) -> Mapping[str, Any]:
    """Apply every frozen gate except the later byte-reproduction proof."""
    horizons = _mapping(summary, "horizons")
    h5 = _mapping(horizons, "5")
    h10 = _mapping(horizons, "10")

    def contrast(item: Mapping[str, object], key: str) -> Mapping[str, Any]:
        return _mapping(_mapping(item, "contrasts"), key)

    source_gates = {
        "complete_frame": (
            h5.get("origin_count") == expected_origin_count
            and h10.get("origin_count") == expected_origin_count
            and h5.get("repository_count") == 9
            and h10.get("repository_count") == 9
        ),
        "all_origins_supported": state_summary.get("origin_missing_state_count") == 0,
        "resolution_coverage_at_least_0_70": _number(
            state_summary,
            "coverage",
        )
        >= 0.70,
        "origin_state_variation": sum(
            int(value) >= 3
            for value in _mapping(
                state_summary,
                "distinct_origin_state_count_by_repository",
            ).values()
        )
        >= 6,
        "raw_registry_reload_verified": raw_registry_verified,
    }
    h5_continuous = contrast(h5, "continuous_vs_full")
    h5_materialized = contrast(h5, "materialized_vs_full")
    h10_continuous = contrast(h10, "continuous_vs_full")
    h10_materialized = contrast(h10, "materialized_vs_full")
    scientific_gates = {
        "h5_continuous_vs_full": (
            _number(h5_continuous, "macro_repository") < 0.0
            and _sequence_pair(h5_continuous, "bootstrap_95_interval")[1] < 0.0
            and _positive_integer(
                h5_continuous,
                "favorable_repository_count",
                allow_zero=True,
            )
            >= 6
        ),
        "h5_materialized_vs_full": (
            _number(h5_materialized, "macro_repository") < 0.0
            and _sequence_pair(h5_materialized, "bootstrap_95_interval")[1] < 0.0
            and _positive_integer(
                h5_materialized,
                "favorable_repository_count",
                allow_zero=True,
            )
            >= 6
        ),
        "h10_continuous_vs_full": (
            _number(h10_continuous, "macro_repository") < 0.0
            and _positive_integer(
                h10_continuous,
                "favorable_repository_count",
                allow_zero=True,
            )
            >= 6
        ),
        "h10_materialized_vs_full": (
            _number(h10_materialized, "macro_repository") < 0.0
            and _positive_integer(
                h10_materialized,
                "favorable_repository_count",
                allow_zero=True,
            )
            >= 6
        ),
        "deep_h5": all(
            _number(_mapping(h5, "deep_contrasts"), key) < 0.0
            for key in ("continuous_vs_full", "materialized_vs_full")
        ),
        "deep_h10": all(
            _number(_mapping(h10, "deep_contrasts"), key) < 0.0
            for key in ("continuous_vs_full", "materialized_vs_full")
        ),
        "h5_leave_one_repository_out": all(
            _number(item, "contrast") < 0.0
            for item in _mapping_sequence(
                h5_materialized,
                "leave_one_repository_out",
            )
        ),
        "materialization_tolerance": all(
            _number(
                contrast(item, "materialized_vs_continuous"),
                "macro_repository",
            )
            <= 0.005
            for item in (h5, h10)
        ),
        "materialized_beats_trailing_and_lock_only": all(
            _number(contrast(item, key), "macro_repository") < 0.0
            for item in (h5, h10)
            for key in ("materialized_vs_trailing", "materialized_vs_lock_only")
        ),
        "temporal_null": _number(
            temporal_null,
            "as_good_or_better_rate",
        )
        < 0.10,
    }
    source_passed = all(source_gates.values())
    stage_a_without_reproduction = source_passed and all(scientific_gates.values())
    if not source_passed:
        status = "retired_source_admission"
    elif stage_a_without_reproduction:
        status = "passed_pending_reproduction"
    else:
        status = "retired_stage_a"
    return {
        "status": status,
        "source_admission_passed_without_reproduction": source_passed,
        "stage_a_passed_without_reproduction": stage_a_without_reproduction,
        "agent_outcome_plan_authorized": False,
        "source_gates": source_gates,
        "scientific_gates": scientific_gates,
        "reproduction_gate": "pending_external_byte_comparison",
    }


def run_study(
    *,
    plan: Mapping[str, object],
    addendum: Mapping[str, object],
    execution_lock: Mapping[str, object],
    repository_cache: Path,
    registry_manifest_path: Path,
) -> Mapping[str, Any]:
    """Execute accepted Stage A entirely from frozen local responses."""
    frame = load_frame(plan, addendum)
    points, scan_manifests = scan_state_points(frame, repository_cache)
    registry_binding = _mapping(execution_lock, "registry_manifest")
    registry_manifest, registry = load_registry_manifest(
        registry_manifest_path,
        expected_digest=_required_string(registry_binding, "digest"),
    )
    (
        task_states,
        origin_states,
        task_lock_states,
        origin_lock_states,
        state_summary,
    ) = build_state_index(points, registry)
    (
        true_memberships,
        lock_memberships,
        null_memberships,
        membership_digest,
    ) = build_memberships(
        plan=plan,
        frame=frame,
        task_states=task_states,
        origin_states=origin_states,
        task_lock_states=task_lock_states,
        origin_lock_states=origin_lock_states,
    )

    # The scoring-only source is intentionally loaded after every accepted and
    # circular-null membership has been created and digested.
    labels = load_scoring_labels(plan, addendum, frame)
    rows, null_offsets = evaluate_origins(
        plan=plan,
        frame=frame,
        labels=labels,
        true_memberships=true_memberships,
        lock_memberships=lock_memberships,
        null_memberships=null_memberships,
    )
    repositories = _string_sequence(
        _mapping(plan, "source").get("wide_repositories"),
        "wide repositories",
    )
    deep = _string_sequence(
        _mapping(plan, "source").get("deep_repositories"),
        "deep repositories",
    )
    summary = summarize_rows(
        rows,
        wide_repositories=repositories,
        deep_repositories=deep,
        bootstrap_seed=20260729,
    )
    true_h5 = _number(
        _mapping(
            _mapping(
                _mapping(_mapping(summary, "horizons"), "5"),
                "contrasts",
            ),
            "materialized_vs_full",
        ),
        "macro_repository",
    )
    null_summary = temporal_null_summary(
        null_offsets,
        repositories=repositories,
        true_contrast=true_h5,
        seed=20260729,
    )
    decision = decide(
        summary=summary,
        state_summary=state_summary,
        temporal_null=null_summary,
        raw_registry_verified=True,
        expected_origin_count=_positive_integer(
            _mapping(plan, "rolling_origin"),
            "origin_count",
        ),
    )
    ordered_scan_manifests = tuple(
        scan_manifests[repository_id] for repository_id in repositories
    )
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "addendum_digest": addendum.get("addendum_digest"),
        "execution_lock_digest": execution_lock.get("execution_lock_digest"),
        "source_manifest": frame.source_manifest,
        "registry_manifest": {
            "digest": registry_manifest.get("registry_manifest_digest"),
            "package_count": registry_manifest.get("package_count"),
            "response_count": registry_manifest.get("response_count"),
            "response_bytes": registry_manifest.get("response_bytes"),
        },
        "repository_scan_manifests": ordered_scan_manifests,
        "state_summary": state_summary,
        "membership_digest": membership_digest,
        "scoring_label_digest": _mapping(addendum, "scoring_label").get(
            "label_projection_digest"
        ),
        "origin_rows": rows,
        "origin_rows_digest": canonical_digest(rows),
        "summary": summary,
        "temporal_null": null_summary,
        "decision_without_reproduction": decision,
        "resource_use": {
            "paid_api_calls": 0,
            "embedding_calls": 0,
            "coding_agent_calls": 0,
            "agent_outcomes_opened": 0,
            "sealed_holdout_opened": 0,
        },
        "claim_boundary": (
            "Outcome-free registry-retrospective projected counterfactual "
            "development evidence. Binary dependency-touch Brier is a "
            "mechanism diagnostic, not pass-rate MAE or Selector validity."
        ),
    }
    result["result_digest"] = canonical_digest(result)
    return result


def verify_result(
    result: Mapping[str, object],
    *,
    plan: Mapping[str, object],
    addendum: Mapping[str, object],
    execution_lock: Mapping[str, object],
    frame: SourceFrame,
) -> None:
    """Verify result identity, memberships, aggregation, null, and decision."""
    if result.get("schema_version") != RESULT_SCHEMA:
        raise ValueError("THY-003 result schema is unsupported")
    if (
        result.get("study_id") != plan.get("study_id")
        or result.get("plan_digest") != plan.get("plan_digest")
        or result.get("addendum_digest") != addendum.get("addendum_digest")
        or result.get("execution_lock_digest")
        != execution_lock.get("execution_lock_digest")
    ):
        raise ValueError("THY-003 result parent identity changed")
    payload = dict(result)
    digest = payload.pop("result_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("THY-003 result digest does not match")
    expected_resources = {
        key: _positive_integer(
            _mapping(plan, "resource_budget"),
            key,
            allow_zero=True,
        )
        for key in (
            "paid_api_calls",
            "embedding_calls",
            "coding_agent_calls",
            "agent_outcomes_opened",
            "sealed_holdout_opened",
        )
    }
    if _mapping(result, "resource_use") != expected_resources:
        raise ValueError("THY-003 result crossed the resource boundary")
    if canonical_digest(_mapping_sequence(result, "origin_rows")) != result.get(
        "origin_rows_digest"
    ):
        raise ValueError("THY-003 Origin row digest does not match")
    if canonical_digest(result.get("source_manifest")) != canonical_digest(
        frame.source_manifest
    ):
        raise ValueError("THY-003 result source frame changed")

    histories = {
        origin_frame.projection.origin_id: {
            task.instance_id for task in origin_frame.projection.history
        }
        for repository_origins in frame.origins.values()
        for origin_frame in repository_origins
    }
    expected_pairs = {
        (repository_id, origin_frame.projection.origin_id, horizon)
        for repository_id, repository_origins in frame.origins.items()
        for origin_frame in repository_origins
        for horizon in (5, 10)
    }
    observed_pairs = set()
    membership_rows = {}
    for row in _mapping_sequence(result, "origin_rows"):
        repository_id = _required_string(row, "repository_id")
        origin_id = _required_string(row, "origin_id")
        horizon = _positive_integer(row, "horizon")
        observed_pairs.add((repository_id, origin_id, horizon))
        for field in (
            "candidate_selected_task_ids",
            "lock_only_selected_task_ids",
        ):
            selected = _string_sequence(row.get(field), field)
            if len(selected) != 10 or not set(selected).issubset(histories[origin_id]):
                raise ValueError("THY-003 membership is invalid")
        membership_identity = {
            key: row.get(key)
            for key in (
                "candidate_selected_task_ids",
                "candidate_distance_digest",
                "lock_only_selected_task_ids",
                "lock_only_distance_digest",
            )
        }
        prior = membership_rows.get(origin_id)
        if prior is not None and prior != membership_identity:
            raise ValueError("THY-003 H5/H10 memberships disagree")
        membership_rows[origin_id] = membership_identity
    if observed_pairs != expected_pairs:
        raise ValueError("THY-003 Origin result frame changed")

    repositories = _string_sequence(
        _mapping(plan, "source").get("wide_repositories"),
        "wide repositories",
    )
    expected_summary = summarize_rows(
        _mapping_sequence(result, "origin_rows"),
        wide_repositories=repositories,
        deep_repositories=_string_sequence(
            _mapping(plan, "source").get("deep_repositories"),
            "deep repositories",
        ),
        bootstrap_seed=20260729,
    )
    if canonical_digest(result.get("summary")) != canonical_digest(expected_summary):
        raise ValueError("THY-003 result summary does not replay")
    null_payload = _mapping(result, "temporal_null")
    offsets = {
        _required_string(item, "repository_id"): {
            _positive_integer(offset, "offset"): _number(offset, "contrast")
            for offset in _mapping_sequence(item, "offsets")
        }
        for item in _mapping_sequence(
            null_payload,
            "repository_offset_contrasts",
        )
    }
    true_h5 = _number(
        _mapping(
            _mapping(
                _mapping(_mapping(expected_summary, "horizons"), "5"),
                "contrasts",
            ),
            "materialized_vs_full",
        ),
        "macro_repository",
    )
    expected_null = temporal_null_summary(
        offsets,
        repositories=repositories,
        true_contrast=true_h5,
        seed=20260729,
    )
    if canonical_digest(null_payload) != canonical_digest(expected_null):
        raise ValueError("THY-003 temporal null does not replay")
    expected_decision = decide(
        summary=expected_summary,
        state_summary=_mapping(result, "state_summary"),
        temporal_null=expected_null,
        raw_registry_verified=True,
        expected_origin_count=_positive_integer(
            _mapping(plan, "rolling_origin"),
            "origin_count",
        ),
    )
    if result.get("decision_without_reproduction") != expected_decision:
        raise ValueError("THY-003 decision does not replay")


def compact_reproduction(
    *,
    first_path: Path,
    second_path: Path,
    first: Mapping[str, object],
    second: Mapping[str, object],
    plan: Mapping[str, object],
    addendum: Mapping[str, object],
    execution_lock: Mapping[str, object],
    frame: SourceFrame,
) -> Mapping[str, Any]:
    """Bind two byte-identical offline executions into final Stage-A evidence."""
    verify_result(
        first,
        plan=plan,
        addendum=addendum,
        execution_lock=execution_lock,
        frame=frame,
    )
    verify_result(
        second,
        plan=plan,
        addendum=addendum,
        execution_lock=execution_lock,
        frame=frame,
    )
    first_bytes = first_path.read_bytes()
    second_bytes = second_path.read_bytes()
    byte_identical = first_bytes == second_bytes
    if not byte_identical:
        raise ValueError("THY-003 offline executions are not byte-identical")
    preliminary = _mapping(first, "decision_without_reproduction")
    source_passed = (
        preliminary.get("source_admission_passed_without_reproduction") is True
    )
    scientific_passed = preliminary.get("stage_a_passed_without_reproduction") is True
    if not source_passed:
        status = "retired_source_admission"
    elif not scientific_passed:
        status = "retired_stage_a"
    else:
        status = "passed_stage_a"
    final_decision = {
        **preliminary,
        "status": status,
        "reproduction_gate": True,
        "stage_a_passed": bool(source_passed and scientific_passed),
        "agent_outcome_plan_authorized": bool(source_passed and scientific_passed),
    }
    compact: dict[str, Any] = {
        "schema_version": SUMMARY_SCHEMA,
        "study_id": first.get("study_id"),
        "plan_digest": first.get("plan_digest"),
        "addendum_digest": first.get("addendum_digest"),
        "execution_lock_digest": first.get("execution_lock_digest"),
        "result_digest": first.get("result_digest"),
        "result_sha256": hashlib.sha256(first_bytes).hexdigest(),
        "byte_identical_execution_count": 2,
        "source_manifest": first.get("source_manifest"),
        "registry_manifest": first.get("registry_manifest"),
        "repository_scan_manifests": first.get("repository_scan_manifests"),
        "state_summary": first.get("state_summary"),
        "membership_digest": first.get("membership_digest"),
        "scoring_label_digest": first.get("scoring_label_digest"),
        "origin_rows_digest": first.get("origin_rows_digest"),
        "summary": first.get("summary"),
        "temporal_null": first.get("temporal_null"),
        "decision": final_decision,
        "resource_use": first.get("resource_use"),
        "claim_boundary": first.get("claim_boundary"),
    }
    compact["summary_digest"] = canonical_digest(compact)
    return compact


def discovery_payload(
    *,
    plan: Mapping[str, object],
    addendum: Mapping[str, object],
    repository_cache: Path,
) -> Mapping[str, Any]:
    """Scan candidate-visible state and list the one-time package acquisition."""
    frame = load_frame(plan, addendum)
    points, scan_manifests = scan_state_points(frame, repository_cache)
    packages = tuple(
        sorted(
            {
                dependency.name
                for point in points
                for dependency in point.snapshot.dependencies
            },
            key=lambda item: (item.casefold(), item),
        )
    )
    payload: dict[str, Any] = {
        "schema_version": "barcarolle_dependency_lag_discovery_v1",
        "study_id": plan.get("study_id"),
        "plan_digest": plan.get("plan_digest"),
        "addendum_digest": addendum.get("addendum_digest"),
        "source_manifest": frame.source_manifest,
        "state_point_count": len(points),
        "package_count": len(packages),
        "package_digest": canonical_digest(packages),
        "packages": packages,
        "repository_scan_manifests": tuple(
            scan_manifests[repository_id]
            for repository_id in _string_sequence(
                _mapping(plan, "source").get("wide_repositories"),
                "wide repositories",
            )
        ),
    }
    payload["discovery_digest"] = canonical_digest(payload)
    return payload


def _median(values: Sequence[float]) -> float:
    count = len(values)
    if count == 0:
        raise ValueError("median input is empty")
    middle = count // 2
    if count % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2


def _git(repository: Path, *arguments: str) -> str:
    completed = _run_process(
        ("git", "-C", str(repository), *arguments),
        text=True,
    )
    return str(completed.stdout)


def _git_bytes(repository: Path, *arguments: str) -> bytes:
    environment = dict(os.environ)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    last_error: subprocess.CalledProcessError | None = None
    for attempt in range(1, 4):
        try:
            completed = subprocess.run(
                ("git", "-C", str(repository), *arguments),
                check=True,
                capture_output=True,
                text=False,
                env=environment,
            )
            return completed.stdout
        except subprocess.CalledProcessError as error:
            last_error = error
            if attempt < 3:
                time.sleep(float(attempt))
    assert last_error is not None
    raise last_error


def _run_process(
    arguments: Sequence[str],
    *,
    text: bool,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    environment = dict(os.environ)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    return subprocess.run(
        tuple(arguments),
        check=True,
        capture_output=True,
        text=text,
        env=environment,
    )


def _format_utc(value: datetime) -> str:
    return (
        value.astimezone(UTC)
        .isoformat(timespec="microseconds")
        .replace(
            "+00:00",
            "Z",
        )
    )


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
    if any(not isinstance(item, str) or not item for item in items):
        raise ValueError(f"{label} contains an invalid string")
    if len(items) != len(set(items)):
        raise ValueError(f"{label} contains duplicates")
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


def _sequence_pair(
    payload: Mapping[str, object],
    key: str,
) -> tuple[float, float]:
    value = payload.get(key)
    if not isinstance(value, Sequence) or isinstance(value, str) or len(value) != 2:
        raise ValueError(f"{key} must be a numeric pair")
    return float(value[0]), float(value[1])


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--addendum", type=Path, default=DEFAULT_ADDENDUM)
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover")
    discover.add_argument(
        "--repository-cache",
        type=Path,
        default=DEFAULT_REPOSITORY_CACHE,
    )
    discover.add_argument("--output", type=Path)

    acquire = subparsers.add_parser("fetch-registry")
    acquire.add_argument(
        "--repository-cache",
        type=Path,
        default=DEFAULT_REPOSITORY_CACHE,
    )
    acquire.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    acquire.add_argument("--workers", type=int, default=8)

    run = subparsers.add_parser("run")
    run.add_argument(
        "--execution-lock",
        type=Path,
        default=DEFAULT_EXECUTION_LOCK,
    )
    run.add_argument(
        "--repository-cache",
        type=Path,
        default=DEFAULT_REPOSITORY_CACHE,
    )
    run.add_argument(
        "--registry-manifest",
        type=Path,
        default=DEFAULT_REGISTRY_MANIFEST,
    )
    run.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)

    verify = subparsers.add_parser("verify")
    verify.add_argument(
        "--execution-lock",
        type=Path,
        default=DEFAULT_EXECUTION_LOCK,
    )
    verify.add_argument(
        "--repository-cache",
        type=Path,
        default=DEFAULT_REPOSITORY_CACHE,
    )
    verify.add_argument(
        "--registry-manifest",
        type=Path,
        default=DEFAULT_REGISTRY_MANIFEST,
    )
    verify.add_argument("--result", type=Path, default=DEFAULT_OUTPUT)

    compact = subparsers.add_parser("compact")
    compact.add_argument(
        "--execution-lock",
        type=Path,
        default=DEFAULT_EXECUTION_LOCK,
    )
    compact.add_argument("--first", type=Path, required=True)
    compact.add_argument("--second", type=Path, required=True)
    compact.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)

    arguments = parser.parse_args(argv)
    plan = load_plan(arguments.plan)
    addendum = load_addendum(arguments.addendum, plan=plan)
    if arguments.command in {"discover", "fetch-registry"}:
        discovery = discovery_payload(
            plan=plan,
            addendum=addendum,
            repository_cache=arguments.repository_cache,
        )
        if arguments.command == "discover":
            if arguments.output is not None:
                _write_json(arguments.output, discovery)
            else:
                print(canonical_json(discovery))
            return 0
        manifest = acquire_registry(
            _string_sequence(discovery.get("packages"), "discovered packages"),
            arguments.raw_root,
            workers=arguments.workers,
        )
        print(
            canonical_json(
                {
                    "registry_manifest_digest": manifest.get(
                        "registry_manifest_digest"
                    ),
                    "package_count": manifest.get("package_count"),
                    "response_count": manifest.get("response_count"),
                    "response_bytes": manifest.get("response_bytes"),
                }
            )
        )
        return 0

    execution_lock = load_execution_lock(
        arguments.execution_lock,
        plan=plan,
        addendum=addendum,
    )
    frame = load_frame(plan, addendum)
    if arguments.command == "run":
        result = run_study(
            plan=plan,
            addendum=addendum,
            execution_lock=execution_lock,
            repository_cache=arguments.repository_cache,
            registry_manifest_path=arguments.registry_manifest,
        )
        verify_result(
            result,
            plan=plan,
            addendum=addendum,
            execution_lock=execution_lock,
            frame=frame,
        )
        _write_json(arguments.output, result)
        print(canonical_json(result["decision_without_reproduction"]))
        return 0
    if arguments.command == "verify":
        result = _load_mapping(arguments.result)
        verify_result(
            result,
            plan=plan,
            addendum=addendum,
            execution_lock=execution_lock,
            frame=frame,
        )
        replay = run_study(
            plan=plan,
            addendum=addendum,
            execution_lock=execution_lock,
            repository_cache=arguments.repository_cache,
            registry_manifest_path=arguments.registry_manifest,
        )
        verify_result(
            replay,
            plan=plan,
            addendum=addendum,
            execution_lock=execution_lock,
            frame=frame,
        )
        if canonical_digest(replay) != canonical_digest(result):
            raise ValueError(
                "THY-003 result does not reconstruct from frozen raw inputs"
            )
        print(_required_string(result, "result_digest"))
        return 0
    first = _load_mapping(arguments.first)
    second = _load_mapping(arguments.second)
    summary = compact_reproduction(
        first_path=arguments.first,
        second_path=arguments.second,
        first=first,
        second=second,
        plan=plan,
        addendum=addendum,
        execution_lock=execution_lock,
        frame=frame,
    )
    _write_json(arguments.summary, summary)
    print(canonical_json(summary["decision"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
