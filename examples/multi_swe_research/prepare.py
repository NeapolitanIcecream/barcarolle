#!/usr/bin/env python3
"""Prepare the fixed Multi-SWE public panel and projected Task times."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
from typing import Any, Callable, Iterable, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, format_utc_timestamp  # noqa: E402


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "contract.json"
CONTRACT_SCHEMA = "barcarolle_multi_swe_research_contract_v1"
PANEL_SCHEMA = "barcarolle_multi_swe_public_panel_v1"
TIME_SCHEMA = "barcarolle_multi_swe_task_time_projection_v1"
CONTENT_SCHEMA = "barcarolle_multi_swe_task_content_projection_v1"
CONTENT_MANIFEST_SCHEMA = "barcarolle_multi_swe_task_content_manifest_v1"
EMBEDDING_MANIFEST_SCHEMA = "barcarolle_multi_swe_embedding_manifest_v1"
SELECTOR_SUMMARY_SCHEMA = "barcarolle_multi_swe_selector_study_summary_v1"
HINDSIGHT_SUMMARY_SCHEMA = "barcarolle_multi_swe_hindsight_summary_v1"
_TASK_ID = re.compile(
    r"(?P<owner>[A-Za-z0-9_.-]+)__(?P<repo>[A-Za-z0-9_.-]+)-(?P<number>[1-9][0-9]*)\Z"
)


def load_contract(path: Path = DEFAULT_CONTRACT) -> Mapping[str, Any]:
    payload = _load_mapping(path)
    if payload.get("schema_version") != CONTRACT_SCHEMA:
        raise ValueError("Multi-SWE contract schema is unsupported")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "contract_digest"}
    )
    if payload.get("contract_digest") != expected:
        raise ValueError("Multi-SWE contract digest does not match")

    dataset = _mapping(payload, "dataset")
    paths = _string_sequence(dataset, "paths")
    if len(paths) != 39 or len(set(paths)) != len(paths):
        raise ValueError("dataset path allowlist must contain 39 unique paths")
    if _line_digest(paths) != _required_string(dataset, "path_list_sha256"):
        raise ValueError("dataset path allowlist digest does not match")

    results = _mapping(payload, "results")
    configurations = _string_sequence(results, "configurations")
    if len(configurations) != 36 or len(set(configurations)) != len(configurations):
        raise ValueError("result allowlist must contain 36 unique configurations")
    if _line_digest(configurations) != _required_string(
        results, "configuration_list_sha256"
    ):
        raise ValueError("result configuration allowlist digest does not match")

    languages = _mapping_sequence(results, "languages")
    result_directories = tuple(
        _required_string(language, "result_directory") for language in languages
    )
    if len(result_directories) != 7 or len(set(result_directories)) != 7:
        raise ValueError("result language contract must contain seven unique entries")
    return payload


def normalize_public_panel(
    contract: Mapping[str, Any],
    experiments_root: Path,
) -> tuple[Mapping[str, Any], tuple[Mapping[str, object], ...], tuple[Mapping[str, str], ...]]:
    """Validate and normalize the exact 36-vector public result panel."""
    results = _mapping(contract, "results")
    configurations = _string_sequence(results, "configurations")
    language_specs = _mapping_sequence(results, "languages")
    split = _required_string(results, "split")
    expected_total = _required_int(_mapping(contract, "dataset"), "task_count")

    task_languages: dict[str, str] = {}
    expected_language_ids: dict[str, frozenset[str]] = {}
    result_file_records: list[Mapping[str, str]] = []
    outcome_rows: list[Mapping[str, object]] = []
    summaries: list[Mapping[str, object]] = []
    vectors: dict[str, frozenset[str]] = {}
    warnings: list[Mapping[str, object]] = []

    for configuration in configurations:
        configuration_terminal: dict[str, str] = {}
        configuration_resolved: set[str] = set()
        for language in language_specs:
            result_directory = _required_string(language, "result_directory")
            path = (
                experiments_root
                / "evaluation"
                / result_directory
                / split
                / configuration
                / "results"
                / "results.json"
            )
            metadata_path = path.parents[1] / "metadata.yaml"
            if not _metadata_is_verified(metadata_path):
                raise ValueError(f"result metadata is not verified: {metadata_path}")
            payload = _load_mapping(path)
            completed = _unique_string_set(payload, "completed_ids", path)
            empty = _unique_string_set(payload, "empty_error_patch_ids", path)
            incomplete = _unique_string_set(payload, "incomplete_ids", path)
            resolved = _unique_string_set(payload, "resolved", path)
            _require_disjoint_partitions(
                {
                    "completed": completed,
                    "empty_error_patch": empty,
                    "incomplete": incomplete,
                },
                path,
            )
            if not resolved <= completed:
                raise ValueError(f"resolved IDs are not completed IDs: {path}")
            language_ids = completed | empty | incomplete
            expected_count = _required_int(language, "task_count")
            if len(language_ids) != expected_count:
                raise ValueError(
                    f"result denominator mismatch for {result_directory}: {path}"
                )
            if _line_digest(language_ids) != _required_string(
                language, "task_id_line_digest"
            ):
                raise ValueError(
                    f"result Task identity mismatch for {result_directory}: {path}"
                )
            prior_ids = expected_language_ids.setdefault(
                result_directory, frozenset(language_ids)
            )
            if prior_ids != language_ids:
                raise ValueError(
                    f"result denominator changed for {result_directory}: {path}"
                )
            for instance_id in language_ids:
                prior_language = task_languages.setdefault(
                    instance_id, result_directory
                )
                if prior_language != result_directory:
                    raise ValueError(
                        f"Task occurs in multiple result languages: {instance_id}"
                    )
                terminal = (
                    "completed"
                    if instance_id in completed
                    else (
                        "empty_error_patch"
                        if instance_id in empty
                        else "incomplete"
                    )
                )
                configuration_terminal[instance_id] = terminal
            configuration_resolved.update(resolved)

            scalar_total = payload.get("total_instances")
            if scalar_total != len(language_ids):
                warnings.append(
                    {
                        "configuration_id": configuration,
                        "language": result_directory,
                        "warning": "scalar_total_instances_mismatch",
                        "reported": scalar_total,
                        "terminal_partition_count": len(language_ids),
                    }
                )
            relative_path = path.relative_to(experiments_root).as_posix()
            result_file_records.append(
                {
                    "path": relative_path,
                    "sha256": _file_sha256(path),
                }
            )

        universe = frozenset(configuration_terminal)
        if len(universe) != expected_total:
            raise ValueError(
                f"configuration does not cover {expected_total} Tasks: {configuration}"
            )
        vectors[configuration] = frozenset(configuration_resolved)
        harness, model = _configuration_parts(configuration)
        summaries.append(
            {
                "configuration_id": configuration,
                "harness_family": harness,
                "model_family": model,
                "resolved_count": len(configuration_resolved),
                "pass_rate": len(configuration_resolved) / expected_total,
                "resolved_id_line_digest": _line_digest(configuration_resolved),
                "terminal_state_counts": {
                    state: tuple(configuration_terminal.values()).count(state)
                    for state in ("completed", "empty_error_patch", "incomplete")
                },
            }
        )
        outcome_rows.extend(
            {
                "configuration_id": configuration,
                "instance_id": instance_id,
                "language": task_languages[instance_id],
                "resolved": instance_id in configuration_resolved,
                "terminal_state": configuration_terminal[instance_id],
            }
            for instance_id in sorted(universe)
        )

    universe = frozenset(task_languages)
    dataset = _mapping(contract, "dataset")
    if _line_digest(universe) != _required_string(dataset, "task_id_line_digest"):
        raise ValueError("normalized panel Task universe does not match the contract")
    if len(set(vectors.values())) != len(vectors):
        raise ValueError("public panel contains duplicate binary outcome vectors")

    disagreement_rates = _pairwise_disagreement_rates(vectors, len(universe))
    task_rows = tuple(
        {
            "instance_id": instance_id,
            "language": task_languages[instance_id],
            "repository": _task_identity(instance_id)[0],
        }
        for instance_id in sorted(universe)
    )
    resolved_rows = tuple(row for row in outcome_rows if bool(row["resolved"]))
    panel: dict[str, Any] = {
        "schema_version": PANEL_SCHEMA,
        "study_id": contract.get("study_id"),
        "contract_digest": contract.get("contract_digest"),
        "task_count": len(universe),
        "task_id_line_digest": _line_digest(universe),
        "configuration_count": len(configurations),
        "result_file_count": len(result_file_records),
        "result_file_manifest_digest": canonical_digest(
            tuple(sorted(result_file_records, key=lambda row: row["path"]))
        ),
        "task_universe_digest": canonical_digest(task_rows),
        "resolved_cell_count": len(resolved_rows),
        "resolved_outcome_digest": canonical_digest(resolved_rows),
        "configurations": tuple(summaries),
        "pairwise_disagreement": {
            "minimum": min(disagreement_rates),
            "median": statistics.median(disagreement_rates),
            "maximum": max(disagreement_rates),
        },
        "source_warnings": tuple(
            sorted(
                warnings,
                key=lambda row: (
                    str(row["configuration_id"]),
                    str(row["language"]),
                ),
            )
        ),
        "claim_boundary": (
            "Official terminal partitions are normalized counterfactual "
            "development evidence, not independently replayed Barcarolle Results."
        ),
        "resource_use": {"paid_api_calls": 0},
    }
    panel["panel_digest"] = canonical_digest(panel)
    return panel, tuple(outcome_rows), task_rows


def write_public_panel(
    panel: Mapping[str, Any],
    outcomes: Sequence[Mapping[str, object]],
    tasks: Sequence[Mapping[str, str]],
    output_dir: Path,
) -> None:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite panel output: {output_dir}")
    output_dir.mkdir(parents=True)
    _write_json(output_dir / "panel-summary.json", panel)
    _write_jsonl(output_dir / "task-universe.jsonl", tasks)
    _write_jsonl(output_dir / "outcomes.jsonl", outcomes)
    _write_jsonl(
        output_dir / "resolved-outcomes.jsonl",
        tuple(row for row in outcomes if bool(row["resolved"])),
    )


def project_task_times(
    contract: Mapping[str, Any],
    tasks: Sequence[Mapping[str, str]],
    observed_at: str,
    *,
    query: Callable[[str], Mapping[str, Any]] | None = None,
    batch_size: int = 80,
) -> tuple[Mapping[str, Any], tuple[Mapping[str, object], ...]]:
    """Project immutable GitHub pull-request creation times for the Task universe."""
    parsed_observed_at = _canonical_utc(observed_at)
    if batch_size < 1:
        raise ValueError("GraphQL batch size must be positive")
    query_graphql = query or _query_github_graphql
    grouped: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for task in tasks:
        instance_id = _required_string(task, "instance_id")
        repository, number = _task_identity(instance_id)
        if task.get("repository") != repository:
            raise ValueError(f"Task repository projection changed: {instance_id}")
        grouped[repository].append((instance_id, number))

    rows: list[Mapping[str, object]] = []
    for repository in sorted(grouped):
        owner, name = repository.split("/", 1)
        entries = sorted(grouped[repository])
        for start in range(0, len(entries), batch_size):
            chunk = entries[start : start + batch_size]
            graphql, aliases = _graphql_query(owner, name, chunk)
            response = query_graphql(graphql)
            data = _mapping(response, "data")
            repository_payload = data.get("repository")
            if not isinstance(repository_payload, Mapping):
                raise ValueError(f"GitHub repository is unavailable: {repository}")
            for alias, (instance_id, number) in aliases.items():
                pull_request = repository_payload.get(alias)
                if not isinstance(pull_request, Mapping):
                    raise ValueError(f"GitHub pull request is unavailable: {instance_id}")
                created_at = _canonical_utc(
                    _required_string(pull_request, "createdAt")
                )
                rows.append(
                    {
                        "instance_id": instance_id,
                        "repository": repository,
                        "pull_request_number": number,
                        "created_at": created_at,
                        "evidence": _required_string(
                            _mapping(contract, "time_projection"), "evidence"
                        ),
                        "observed_at": parsed_observed_at,
                    }
                )

    ordered = tuple(sorted(rows, key=lambda row: str(row["instance_id"])))
    _validate_time_rows(contract, tasks, ordered)
    created = tuple(str(row["created_at"]) for row in ordered)
    summary: dict[str, Any] = {
        "schema_version": TIME_SCHEMA,
        "study_id": contract.get("study_id"),
        "contract_digest": contract.get("contract_digest"),
        "task_count": len(ordered),
        "task_id_line_digest": _line_digest(
            str(row["instance_id"]) for row in ordered
        ),
        "minimum_created_at": min(created),
        "maximum_created_at": max(created),
        "observed_at": parsed_observed_at,
        "evidence": _required_string(
            _mapping(contract, "time_projection"), "evidence"
        ),
        "projection_digest": canonical_digest(ordered),
        "claim_boundary": (
            "GitHub pull-request createdAt is projected metadata for "
            "source-time-safe counterfactual research, not native dataset time."
        ),
        "resource_use": {"paid_api_calls": 0, "github_graphql_queries": None},
    }
    summary["summary_digest"] = canonical_digest(summary)
    return summary, ordered


def write_time_projection(
    summary: Mapping[str, Any],
    rows: Sequence[Mapping[str, object]],
    output_dir: Path,
) -> None:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite time output: {output_dir}")
    output_dir.mkdir(parents=True)
    _write_json(output_dir / "task-times-summary.json", summary)
    _write_jsonl(output_dir / "task-times.jsonl", rows)


def project_task_content(
    contract: Mapping[str, Any],
    tasks: Sequence[Mapping[str, str]],
    dataset_root: Path,
) -> tuple[Mapping[str, Any], tuple[Mapping[str, object], ...]]:
    """Verify the pinned dataset checkout and retain only public issue text."""
    source_manifest = _git_source_manifest(contract, dataset_root)
    expected_tasks = {
        _required_string(task, "instance_id"): task for task in tasks
    }
    if len(expected_tasks) != len(tasks):
        raise ValueError("Task universe contains duplicate Task IDs")

    projected: dict[str, Mapping[str, object]] = {}
    for source in source_manifest:
        source_path = dataset_root / _required_string(source, "path")
        with source_path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                payload = json.loads(line)
                if not isinstance(payload, Mapping):
                    raise ValueError(
                        f"dataset row must be an object: {source_path}:{line_number}"
                    )
                instance_id = _required_string(payload, "instance_id")
                task = expected_tasks.get(instance_id)
                if task is None:
                    raise ValueError(
                        f"dataset source refers outside Task universe: {instance_id}"
                    )
                if instance_id in projected:
                    raise ValueError(f"duplicate dataset Task: {instance_id}")
                repository, _ = _task_identity(instance_id)
                if task.get("repository") != repository:
                    raise ValueError(
                        f"dataset Task repository changed: {instance_id}"
                    )
                text, issue_count, has_content = _project_issue_text(payload)
                projected[instance_id] = {
                    "instance_id": instance_id,
                    "repository": repository,
                    "language": _required_string(task, "language"),
                    "issue_count": issue_count,
                    "has_content": has_content,
                    "text": text,
                }

    if set(projected) != set(expected_tasks):
        missing = sorted(set(expected_tasks) - set(projected))
        raise ValueError(
            f"dataset source does not exactly cover Task universe: {missing[:3]}"
        )
    rows = tuple(projected[instance_id] for instance_id in sorted(projected))
    repository_counts: dict[str, list[bool]] = defaultdict(list)
    for row in rows:
        repository_counts[str(row["repository"])].append(bool(row["has_content"]))
    summary: dict[str, Any] = {
        "schema_version": CONTENT_SCHEMA,
        "study_id": contract.get("study_id"),
        "contract_digest": contract.get("contract_digest"),
        "dataset_revision": _required_string(
            _mapping(contract, "dataset"), "revision"
        ),
        "task_count": len(rows),
        "task_id_line_digest": _line_digest(
            str(row["instance_id"]) for row in rows
        ),
        "source_file_count": len(source_manifest),
        "source_bytes": sum(_required_int(row, "size") for row in source_manifest),
        "source_manifest": source_manifest,
        "source_manifest_digest": canonical_digest(source_manifest),
        "task_text_digest": canonical_digest(
            tuple((row["instance_id"], row["text"]) for row in rows)
        ),
        "projection_digest": canonical_digest(rows),
        "nonempty_task_count": sum(bool(row["has_content"]) for row in rows),
        "nonempty_fraction": (
            sum(bool(row["has_content"]) for row in rows) / len(rows)
        ),
        "repository_coverage": {
            repository: {
                "task_count": len(values),
                "nonempty_task_count": sum(values),
                "nonempty_fraction": sum(values) / len(values),
            }
            for repository, values in sorted(repository_counts.items())
        },
        "excluded_fields": (
            "pull-request title/body, patches, tests, test results, hints, "
            "and Agent outcomes"
        ),
        "resource_use": {
            "paid_api_calls": 0,
            "embedding_api_calls": 0,
        },
    }
    summary["summary_digest"] = canonical_digest(summary)
    return summary, rows


def write_content_projection(
    summary: Mapping[str, Any],
    rows: Sequence[Mapping[str, object]],
    output_dir: Path,
) -> None:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite content output: {output_dir}")
    output_dir.mkdir(parents=True)
    _write_json(output_dir / "task-content-summary.json", summary)
    _write_jsonl(output_dir / "task-content.jsonl", rows)


def validate_evidence(
    contract: Mapping[str, Any],
    evidence_root: Path,
) -> Mapping[str, object]:
    """Validate the small committed panel indexes and projected-time sidecar."""
    panel = _load_mapping(evidence_root / "panel-summary.json")
    if panel.get("schema_version") != PANEL_SCHEMA:
        raise ValueError("committed panel schema is unsupported")
    if panel.get("contract_digest") != contract.get("contract_digest"):
        raise ValueError("committed panel contract identity changed")
    expected_panel_digest = canonical_digest(
        {key: value for key, value in panel.items() if key != "panel_digest"}
    )
    if panel.get("panel_digest") != expected_panel_digest:
        raise ValueError("committed panel digest does not match")

    tasks = _load_jsonl(evidence_root / "task-universe.jsonl")
    if len(tasks) != panel.get("task_count"):
        raise ValueError("committed Task universe count changed")
    if canonical_digest(tasks) != panel.get("task_universe_digest"):
        raise ValueError("committed Task universe digest changed")
    dataset = _mapping(contract, "dataset")
    if _line_digest(row["instance_id"] for row in tasks) != _required_string(
        dataset, "task_id_line_digest"
    ):
        raise ValueError("committed Task universe identity changed")

    resolved = _load_jsonl_mappings(evidence_root / "resolved-outcomes.jsonl")
    if len(resolved) != panel.get("resolved_cell_count"):
        raise ValueError("committed resolved outcome count changed")
    if canonical_digest(resolved) != panel.get("resolved_outcome_digest"):
        raise ValueError("committed resolved outcome digest changed")
    configurations = set(
        _string_sequence(_mapping(contract, "results"), "configurations")
    )
    task_ids = {row["instance_id"] for row in tasks}
    seen_cells: set[tuple[str, str]] = set()
    for row in resolved:
        configuration = _required_string(row, "configuration_id")
        instance_id = _required_string(row, "instance_id")
        if configuration not in configurations or instance_id not in task_ids:
            raise ValueError("committed resolved outcome references unknown identity")
        if row.get("resolved") is not True:
            raise ValueError("sparse committed outcome must be resolved")
        cell = (configuration, instance_id)
        if cell in seen_cells:
            raise ValueError("committed resolved outcome cell is duplicated")
        seen_cells.add(cell)

    time_summary = _load_mapping(evidence_root / "task-times-summary.json")
    if time_summary.get("schema_version") != TIME_SCHEMA:
        raise ValueError("committed time projection schema is unsupported")
    if time_summary.get("contract_digest") != contract.get("contract_digest"):
        raise ValueError("committed time projection contract identity changed")
    expected_time_digest = canonical_digest(
        {
            key: value
            for key, value in time_summary.items()
            if key != "summary_digest"
        }
    )
    if time_summary.get("summary_digest") != expected_time_digest:
        raise ValueError("committed time projection summary digest does not match")
    time_rows = _load_jsonl_mappings(evidence_root / "task-times.jsonl")
    _validate_time_rows(contract, tasks, time_rows)
    if canonical_digest(time_rows) != time_summary.get("projection_digest"):
        raise ValueError("committed time projection rows changed")
    origin_supply = _origin_supply(contract, tasks, time_rows)

    content = _load_mapping(evidence_root / "task-content-manifest.json")
    if content.get("schema_version") != CONTENT_MANIFEST_SCHEMA:
        raise ValueError("committed content manifest schema is unsupported")
    if content.get("contract_digest") != contract.get("contract_digest"):
        raise ValueError("committed content manifest contract identity changed")
    expected_content_digest = canonical_digest(
        {
            key: value
            for key, value in content.items()
            if key != "content_manifest_digest"
        }
    )
    if content.get("content_manifest_digest") != expected_content_digest:
        raise ValueError("committed content manifest digest does not match")
    if (
        content.get("task_count") != len(tasks)
        or content.get("task_id_line_digest")
        != _required_string(dataset, "task_id_line_digest")
        or content.get("source_file_count") != len(
            _string_sequence(dataset, "paths")
        )
        or content.get("source_bytes")
        != _required_int(dataset, "declared_path_bytes")
    ):
        raise ValueError("committed content manifest source identity changed")

    embedding = _validated_self_digested_summary(
        evidence_root / "embedding-manifest.json",
        schema=EMBEDDING_MANIFEST_SCHEMA,
        digest_key="embedding_manifest_digest",
    )
    if embedding.get("content_manifest_digest") != content.get(
        "content_manifest_digest"
    ):
        raise ValueError("committed embedding manifest content identity changed")

    selector_summary = _validated_self_digested_summary(
        evidence_root / "selector-study-summary.json",
        schema=SELECTOR_SUMMARY_SCHEMA,
        digest_key="selector_study_summary_digest",
    )
    selector_identities = _mapping(selector_summary, "identities")
    if (
        selector_identities.get("content_manifest_digest")
        != content.get("content_manifest_digest")
        or selector_identities.get("embedding_manifest_digest")
        != embedding.get("embedding_manifest_digest")
    ):
        raise ValueError("committed Selector summary identity changed")

    hindsight_summary = _validated_self_digested_summary(
        evidence_root / "hindsight-summary.json",
        schema=HINDSIGHT_SUMMARY_SCHEMA,
        digest_key="hindsight_summary_digest",
    )
    hindsight_identities = _mapping(hindsight_summary, "identities")
    if hindsight_identities.get("outcome_results_digest") != (
        selector_identities.get("outcome_results_digest")
    ):
        raise ValueError("committed hindsight summary identity changed")

    return {
        "schema_version": "barcarolle_multi_swe_evidence_validation_v1",
        "contract_digest": contract.get("contract_digest"),
        "panel_digest": panel.get("panel_digest"),
        "time_projection_digest": time_summary.get("projection_digest"),
        "content_manifest_digest": content.get("content_manifest_digest"),
        "task_text_digest": content.get("task_text_digest"),
        "embedding_manifest_digest": embedding.get(
            "embedding_manifest_digest"
        ),
        "selector_study_summary_digest": selector_summary.get(
            "selector_study_summary_digest"
        ),
        "hindsight_summary_digest": hindsight_summary.get(
            "hindsight_summary_digest"
        ),
        "task_count": len(tasks),
        "configuration_count": len(configurations),
        "resolved_cell_count": len(resolved),
        "origin_supply": origin_supply,
        "paid_api_calls": 0,
    }


def _validated_self_digested_summary(
    path: Path,
    *,
    schema: str,
    digest_key: str,
) -> Mapping[str, Any]:
    payload = _load_mapping(path)
    if payload.get("schema_version") != schema:
        raise ValueError(f"committed summary schema is unsupported: {path.name}")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != digest_key}
    )
    if payload.get(digest_key) != expected:
        raise ValueError(f"committed summary digest does not match: {path.name}")
    return payload


def _origin_supply(
    contract: Mapping[str, Any],
    tasks: Sequence[Mapping[str, str]],
    time_rows: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, object], ...]:
    times = {
        _required_string(row, "instance_id"): _canonical_utc(
            _required_string(row, "created_at")
        )
        for row in time_rows
    }
    repository_tasks: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for task in tasks:
        instance_id = _required_string(task, "instance_id")
        repository_tasks[_required_string(task, "repository")].append(
            (times[instance_id], instance_id)
        )

    protocol = _mapping(contract, "research_protocol")
    schedules = _mapping_sequence(protocol, "origin_schedules")
    summaries = []
    for schedule in schedules:
        minimum_history = _required_int(
            schedule, "minimum_initial_history_tasks"
        )
        future_block = _required_int(schedule, "future_block_tasks")
        if minimum_history < 1 or future_block < 1:
            raise ValueError("Origin schedule values must be positive")
        origins: list[Mapping[str, str]] = []
        repository_origin_counts: dict[str, int] = {}
        for repository, unsorted_tasks in repository_tasks.items():
            ordered = sorted(unsorted_tasks)
            task_count = len(ordered)
            if task_count < minimum_history + future_block:
                repository_origin_counts[repository] = 0
                continue
            initial_history = minimum_history + (
                (task_count - minimum_history) % future_block
            )
            repository_origins = []
            for future_start in range(
                initial_history, task_count, future_block
            ):
                repository_origins.append(
                    {
                        "repository": repository,
                        "cutoff": ordered[future_start - 1][0],
                        "future_end": ordered[
                            future_start + future_block - 1
                        ][0],
                    }
                )
            repository_origin_counts[repository] = len(repository_origins)
            origins.extend(repository_origins)

        origins.sort(
            key=lambda origin: (
                origin["repository"],
                origin["cutoff"],
                origin["future_end"],
            )
        )
        training_rows = []
        for target in origins:
            eligible = tuple(
                origin
                for origin in origins
                if origin["repository"] != target["repository"]
                and origin["future_end"] <= target["cutoff"]
            )
            training_rows.append(
                (
                    target["repository"],
                    target["cutoff"],
                    target["future_end"],
                    len(eligible),
                    len({origin["repository"] for origin in eligible}),
                )
            )
        training_origin_counts = [row[3] for row in training_rows]
        training_repository_counts = [row[4] for row in training_rows]
        nonzero_counts = [
            count for count in repository_origin_counts.values() if count > 0
        ]
        total = len(origins)
        summaries.append(
            {
                "minimum_initial_history_tasks": minimum_history,
                "future_block_tasks": future_block,
                "origin_count": total,
                "wide_repository_count": len(nonzero_counts),
                "deep_repository_count": sum(
                    count >= 5 for count in repository_origin_counts.values()
                ),
                "largest_repository_origin_share": (
                    max(nonzero_counts) / total if nonzero_counts else None
                ),
                "source_time_training": {
                    "definition": (
                        "Non-target Origins whose final future Task created_at "
                        "is no later than the final target-history Task."
                    ),
                    "median_origin_count": statistics.median(
                        training_origin_counts
                    ),
                    "median_repository_count": statistics.median(
                        training_repository_counts
                    ),
                    "targets_without_training_origin": sum(
                        count == 0 for count in training_origin_counts
                    ),
                    "targets_with_fewer_than_three_training_repositories": sum(
                        count < 3 for count in training_repository_counts
                    ),
                    "per_origin_counts_digest": canonical_digest(
                        tuple(training_rows)
                    ),
                },
            }
        )
    return tuple(summaries)


def _validate_time_rows(
    contract: Mapping[str, Any],
    tasks: Sequence[Mapping[str, str]],
    rows: Sequence[Mapping[str, object]],
) -> None:
    expected = {_required_string(task, "instance_id") for task in tasks}
    observed = [_required_string(row, "instance_id") for row in rows]
    if len(observed) != len(set(observed)):
        raise ValueError("time projection contains duplicate Task IDs")
    if set(observed) != expected:
        raise ValueError("time projection does not exactly cover the Task universe")
    dataset = _mapping(contract, "dataset")
    if _line_digest(observed) != _required_string(dataset, "task_id_line_digest"):
        raise ValueError("time projection Task identity does not match the contract")
    for row in rows:
        instance_id = _required_string(row, "instance_id")
        repository, number = _task_identity(instance_id)
        if row.get("repository") != repository:
            raise ValueError(f"time projection repository changed: {instance_id}")
        if row.get("pull_request_number") != number:
            raise ValueError(f"time projection PR number changed: {instance_id}")
        _canonical_utc(_required_string(row, "created_at"))
        _canonical_utc(_required_string(row, "observed_at"))


def _graphql_query(
    owner: str,
    name: str,
    entries: Sequence[tuple[str, int]],
) -> tuple[str, Mapping[str, tuple[str, int]]]:
    aliases = {
        f"p{index}": entry for index, entry in enumerate(entries)
    }
    fields = " ".join(
        f"{alias}: pullRequest(number: {number}) {{ createdAt }}"
        for alias, (_, number) in aliases.items()
    )
    graphql = (
        "query { repository("
        f"owner: {json.dumps(owner)}, name: {json.dumps(name)}"
        f") {{ {fields} }} }}"
    )
    return graphql, aliases


def _query_github_graphql(graphql: str) -> Mapping[str, Any]:
    process = subprocess.run(
        ("gh", "api", "graphql", "-f", f"query={graphql}"),
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        message = process.stderr.strip() or "GitHub GraphQL query failed"
        raise RuntimeError(message)
    payload = json.loads(process.stdout)
    if not isinstance(payload, Mapping):
        raise ValueError("GitHub GraphQL response must be an object")
    if payload.get("errors"):
        raise RuntimeError(f"GitHub GraphQL returned errors: {payload['errors']}")
    return payload


def _task_identity(instance_id: str) -> tuple[str, int]:
    match = _TASK_ID.fullmatch(instance_id)
    if match is None:
        raise ValueError(f"unsupported Multi-SWE Task identity: {instance_id}")
    return (
        f"{match.group('owner')}/{match.group('repo')}",
        int(match.group("number")),
    )


def _configuration_parts(configuration: str) -> tuple[str, str]:
    parts = configuration.split("_", 2)
    if len(parts) != 3 or not parts[1] or not parts[2]:
        raise ValueError(f"unsupported result configuration: {configuration}")
    return parts[1], parts[2]


def _require_disjoint_partitions(
    partitions: Mapping[str, frozenset[str]],
    path: Path,
) -> None:
    names = tuple(partitions)
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            overlap = partitions[left] & partitions[right]
            if overlap:
                raise ValueError(
                    f"terminal partitions overlap in {path}: {left}/{right}"
                )


def _unique_string_set(
    payload: Mapping[str, Any],
    key: str,
    path: Path,
) -> frozenset[str]:
    value = payload.get(key)
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise ValueError(f"{key} must be a string list: {path}")
    if len(value) != len(set(value)):
        raise ValueError(f"{key} contains duplicate IDs: {path}")
    return frozenset(value)


def _metadata_is_verified(path: Path) -> bool:
    if not path.is_file():
        raise FileNotFoundError(path)
    values = [
        line.split(":", 1)[1].strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("verified:")
    ]
    return values == ["true"]


def _pairwise_disagreement_rates(
    vectors: Mapping[str, frozenset[str]],
    denominator: int,
) -> tuple[float, ...]:
    names = tuple(sorted(vectors))
    rates = []
    for left_index, left in enumerate(names):
        for right in names[left_index + 1 :]:
            rates.append(len(vectors[left] ^ vectors[right]) / denominator)
    if not rates:
        raise ValueError("at least two outcome vectors are required")
    return tuple(rates)


def _canonical_utc(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"timestamp is invalid: {value}") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"timestamp is timezone-naive: {value}")
    return format_utc_timestamp(parsed.astimezone(UTC))


def _line_digest(values: Iterable[str]) -> str:
    payload = "".join(f"{value}\n" for value in sorted(values))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_source_manifest(
    contract: Mapping[str, Any],
    dataset_root: Path,
) -> tuple[Mapping[str, object], ...]:
    dataset = _mapping(contract, "dataset")
    expected_revision = _required_string(dataset, "revision")
    revision = _run_git(dataset_root, "rev-parse", "HEAD").strip()
    if revision != expected_revision:
        raise ValueError("dataset checkout revision does not match contract")
    lfs_output = _run_git(dataset_root, "lfs", "ls-files", "-l")
    lfs_oids = {}
    for line in lfs_output.splitlines():
        parts = line.split(maxsplit=2)
        if len(parts) == 3 and parts[1] in {"-", "*"}:
            lfs_oids[parts[2]] = parts[0]

    manifest = []
    total_bytes = 0
    for relative in _string_sequence(dataset, "paths"):
        source = dataset_root / relative
        if not source.is_file():
            raise FileNotFoundError(source)
        tree = _run_git(dataset_root, "ls-tree", "HEAD", "--", relative).strip()
        prefix, separator, observed_path = tree.partition("\t")
        fields = prefix.split()
        if (
            not separator
            or observed_path != relative
            or len(fields) != 3
            or fields[1] != "blob"
        ):
            raise ValueError(f"dataset Git identity is unavailable: {relative}")
        git_blob_oid = fields[2]
        size = source.stat().st_size
        digest = _file_sha256(source)
        lfs_oid = lfs_oids.get(relative)
        if lfs_oid is not None:
            if digest != lfs_oid:
                raise ValueError(f"dataset LFS identity changed: {relative}")
            storage = "git_lfs_sha256"
        else:
            worktree_blob = _run_git(
                dataset_root, "hash-object", "--", relative
            ).strip()
            if worktree_blob != git_blob_oid:
                raise ValueError(f"dataset Git blob changed: {relative}")
            storage = "git_blob"
        total_bytes += size
        manifest.append(
            {
                "path": relative,
                "size": size,
                "sha256": digest,
                "git_blob_oid": git_blob_oid,
                "lfs_oid": lfs_oid,
                "storage": storage,
            }
        )
    if total_bytes != _required_int(dataset, "declared_path_bytes"):
        raise ValueError("dataset source byte count does not match contract")
    return tuple(manifest)


def _run_git(root: Path, *arguments: str) -> str:
    process = subprocess.run(
        ("git", "-C", str(root), *arguments),
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        message = process.stderr.strip() or "Git source verification failed"
        raise RuntimeError(message)
    return process.stdout


def _project_issue_text(
    payload: Mapping[str, Any],
) -> tuple[str, int, bool]:
    value = payload.get("resolved_issues")
    if not isinstance(value, list) or any(
        not isinstance(item, Mapping) for item in value
    ):
        raise ValueError("resolved_issues must be an object list")
    issues = []
    has_content = False
    for issue in value:
        number = issue.get("number")
        title = issue.get("title")
        body = issue.get("body")
        if (
            isinstance(number, bool)
            or not isinstance(number, int)
            or number <= 0
            or not isinstance(title, str)
            or not isinstance(body, str)
        ):
            raise ValueError("resolved issue projection is malformed")
        has_content = has_content or bool(title.strip() or body.strip())
        issues.append((number, title, body))
    ordered = sorted(issues)
    text = "\n\n---\n\n".join(
        f"Issue #{number}\n{title}\n\n{body}"
        for number, title, body in ordered
    )
    return text, len(ordered), has_content


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON document must be an object: {path}")
    return payload


def _mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return value


def _mapping_sequence(
    payload: Mapping[str, Any],
    key: str,
) -> tuple[Mapping[str, Any], ...]:
    value = payload.get(key)
    if not isinstance(value, list) or any(not isinstance(item, Mapping) for item in value):
        raise ValueError(f"{key} must be an object list")
    return tuple(value)


def _string_sequence(payload: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise ValueError(f"{key} must be a string list")
    return tuple(value)


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a nonempty string")
    return value


def _required_int(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.write_text(
        "".join(
            json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def _load_jsonl(path: Path) -> tuple[Mapping[str, str], ...]:
    rows = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        payload = json.loads(line)
        if not isinstance(payload, Mapping):
            raise ValueError(f"JSONL row {line_number} must be an object")
        rows.append(
            {
                "instance_id": _required_string(payload, "instance_id"),
                "language": _required_string(payload, "language"),
                "repository": _required_string(payload, "repository"),
            }
        )
    return tuple(rows)


def _load_jsonl_mappings(path: Path) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        payload = json.loads(line)
        if not isinstance(payload, Mapping):
            raise ValueError(f"JSONL row {line_number} must be an object")
        rows.append(payload)
    return tuple(rows)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    panel = subparsers.add_parser("panel", help="normalize the public result panel")
    panel.add_argument("--experiments-root", type=Path, required=True)
    panel.add_argument("--output", type=Path, required=True)

    times = subparsers.add_parser(
        "project-times",
        help="project GitHub pull-request createdAt values",
    )
    times.add_argument("--task-universe", type=Path, required=True)
    times.add_argument("--observed-at", required=True)
    times.add_argument("--output", type=Path, required=True)
    times.add_argument("--batch-size", type=int, default=80)

    evidence = subparsers.add_parser(
        "verify-evidence",
        help="verify committed sparse panel and Task-time evidence",
    )
    evidence.add_argument("--evidence-root", type=Path, default=HERE / "evidence")

    content = subparsers.add_parser(
        "project-content",
        help="verify pinned source bytes and project public issue text",
    )
    content.add_argument("--dataset-root", type=Path, required=True)
    content.add_argument("--task-universe", type=Path, required=True)
    content.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    contract = load_contract(arguments.contract)
    if arguments.command == "panel":
        if arguments.output.exists():
            raise FileExistsError(
                f"refusing to overwrite panel output: {arguments.output}"
            )
        panel, outcomes, tasks = normalize_public_panel(
            contract, arguments.experiments_root
        )
        write_public_panel(panel, outcomes, tasks, arguments.output)
        print(json.dumps(panel, indent=2, sort_keys=True))
        return 0
    if arguments.command == "project-times":
        if arguments.output.exists():
            raise FileExistsError(
                f"refusing to overwrite time output: {arguments.output}"
            )
        tasks = _load_jsonl(arguments.task_universe)
        summary, rows = project_task_times(
            contract,
            tasks,
            arguments.observed_at,
            batch_size=arguments.batch_size,
        )
        query_count = sum(
            (count + arguments.batch_size - 1) // arguments.batch_size
            for count in _repository_counts(tasks).values()
        )
        summary = {
            **summary,
            "resource_use": {
                "paid_api_calls": 0,
                "github_graphql_queries": query_count,
            },
        }
        summary = {
            **summary,
            "summary_digest": canonical_digest(
                {key: value for key, value in summary.items() if key != "summary_digest"}
            ),
        }
        write_time_projection(summary, rows, arguments.output)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    if arguments.command == "verify-evidence":
        report = validate_evidence(contract, arguments.evidence_root)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if arguments.command == "project-content":
        if arguments.output.exists():
            raise FileExistsError(
                f"refusing to overwrite content output: {arguments.output}"
            )
        tasks = _load_jsonl(arguments.task_universe)
        summary, rows = project_task_content(
            contract,
            tasks,
            arguments.dataset_root,
        )
        write_content_projection(summary, rows, arguments.output)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    raise AssertionError(arguments.command)


def _repository_counts(
    tasks: Sequence[Mapping[str, str]],
) -> Mapping[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for task in tasks:
        counts[_required_string(task, "repository")] += 1
    return counts


if __name__ == "__main__":
    raise SystemExit(main())
