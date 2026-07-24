"""Migrate Result records that predate explicit model-resolution scope.

The source schema used ``model_snapshot_id`` for both immutable snapshots and
moving aliases. This one-off migration makes no immutability claim: it treats
that value as the requested model and binds every Result to one caller-declared
campaign scope. It assigns current Result identities, so derived
FeatureSnapshots, SelectorInputs, Selections, fitted Selectors, CellSets,
matrices, and metrics must be rebuilt. The source file is never modified.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
from typing import Any, Mapping, Sequence, cast

from barcarolle.records import (
    CheckOutcomeValue,
    InvalidOwner,
    ResultCacheIdentity,
    ResultRecord,
    ResultScoreableState,
    WorkspaceTerminalStatus,
    canonical_digest,
    canonical_json,
    parse_utc_timestamp,
    record_with_digest,
    validate_result,
    write_jsonl_records,
)
from barcarolle.result_store import compute_result_id, ensure_unique_result_ids


_OLD_RESULT_FIELDS = frozenset(
    {
        "agent_id",
        "cache_identity",
        "check_id",
        "cost",
        "diff_digest",
        "failure_label",
        "finished_at",
        "invalid_owner",
        "latency",
        "outcome",
        "pricing_version",
        "result_available_at",
        "result_digest",
        "result_id",
        "scoreable_state",
        "scoring_config_digest",
        "started_at",
        "task_id",
        "terminal_status",
        "usage",
        "verifier_metadata_digest",
    }
)

_OLD_IDENTITY_FIELDS = frozenset(
    {
        "adapter_digest",
        "agent_manifest_digest",
        "base_commit",
        "budget_digest",
        "check_digest",
        "check_id",
        "hardware_profile_digest",
        "harness_digest",
        "identity_digest",
        "model_snapshot_id",
        "network_policy_digest",
        "prompt_digest",
        "repository_id",
        "repository_instruction_digest",
        "retrieval_digest",
        "retry_policy_digest",
        "runtime_config_digest",
        "skills_digest",
        "solver_material_digest",
        "stochastic_settings_digest",
        "submodule_state_digest",
        "task_id",
        "tools_digest",
        "workspace_config_digest",
    }
)


def migrate_unscoped_model_results(
    results_path: Path,
    output_path: Path,
    *,
    model_scope_id: str,
    model_scope_started_at: str,
    model_scope_ended_at: str,
) -> tuple[ResultRecord, ...]:
    source = results_path.resolve()
    output = output_path.resolve()
    if source == output:
        raise ValueError("output_path must differ from results_path")
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_path}")

    rows = _read_old_results(results_path)
    _validate_declared_scope(
        rows,
        model_scope_id=model_scope_id,
        model_scope_started_at=model_scope_started_at,
        model_scope_ended_at=model_scope_ended_at,
    )
    migrated = tuple(
        _migrate_result(
            row,
            model_scope_id=model_scope_id,
            model_scope_started_at=model_scope_started_at,
            model_scope_ended_at=model_scope_ended_at,
        )
        for row in rows
    )
    ensure_unique_result_ids(migrated)
    write_jsonl_records(output_path, migrated)
    return migrated


def _read_old_results(path: Path) -> tuple[Mapping[str, Any], ...]:
    rows: list[Mapping[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            payload = line[:-1] if line.endswith("\n") else line
            try:
                if not payload:
                    raise ValueError("blank JSONL records are not allowed")
                row = json.loads(payload, parse_constant=_reject_json_constant)
                if not isinstance(row, Mapping):
                    raise TypeError("Result record must be a JSON object")
                if canonical_json(row) != payload:
                    raise ValueError("Result record is not canonical JSON")
                if set(row) != _OLD_RESULT_FIELDS:
                    raise ValueError(
                        "Result record is not the supported unscoped-model schema"
                    )
                _require_digest(row, "result_digest", "old Result")
                rows.append(row)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                raise ValueError(f"{path}: line {line_number}: {exc}") from exc
    return tuple(rows)


def _validate_declared_scope(
    rows: Sequence[Mapping[str, Any]],
    *,
    model_scope_id: str,
    model_scope_started_at: str,
    model_scope_ended_at: str,
) -> None:
    if not model_scope_id:
        raise ValueError("model_scope_id must be a nonempty string")
    try:
        scope_started_at = parse_utc_timestamp(model_scope_started_at)
        scope_ended_at = parse_utc_timestamp(model_scope_ended_at)
    except ValueError as exc:
        raise ValueError("model scope timestamps must be valid ISO datetimes") from exc
    if scope_started_at >= scope_ended_at:
        raise ValueError("model scope must have positive duration")
    for row in rows:
        started_at = parse_utc_timestamp(_string(row["started_at"], "started_at"))
        finished_at = parse_utc_timestamp(_string(row["finished_at"], "finished_at"))
        if started_at < scope_started_at or finished_at > scope_ended_at:
            raise ValueError("model scope does not contain every Result execution")


def _migrate_result(
    old_result: Mapping[str, Any],
    *,
    model_scope_id: str,
    model_scope_started_at: str,
    model_scope_ended_at: str,
) -> ResultRecord:
    old_identity = _mapping(old_result["cache_identity"], "cache_identity")
    if set(old_identity) != _OLD_IDENTITY_FIELDS:
        raise ValueError("cache_identity is not the supported unscoped-model schema")
    _require_digest(old_identity, "identity_digest", "old cache identity")

    task_id = _string(old_result["task_id"], "task_id")
    check_id = _string(old_result["check_id"], "check_id")
    if old_identity["task_id"] != task_id or old_identity["check_id"] != check_id:
        raise ValueError("old cache identity does not match Result task/check")
    requested_model_id = _string(old_identity["model_snapshot_id"], "model_snapshot_id")

    identity = record_with_digest(
        ResultCacheIdentity(
            task_id=task_id,
            check_id=check_id,
            repository_id=_string(old_identity["repository_id"], "repository_id"),
            base_commit=_string(old_identity["base_commit"], "base_commit"),
            submodule_state_digest=_string(
                old_identity["submodule_state_digest"], "submodule_state_digest"
            ),
            solver_material_digest=_string(
                old_identity["solver_material_digest"], "solver_material_digest"
            ),
            check_digest=_string(old_identity["check_digest"], "check_digest"),
            agent_manifest_digest=_string(
                old_identity["agent_manifest_digest"], "agent_manifest_digest"
            ),
            requested_model_id=requested_model_id,
            model_snapshot_id=None,
            model_resolution_scope_id=model_scope_id,
            model_resolution_scope_started_at=model_scope_started_at,
            model_resolution_scope_ended_at=model_scope_ended_at,
            harness_digest=_string(old_identity["harness_digest"], "harness_digest"),
            repository_instruction_digest=_string(
                old_identity["repository_instruction_digest"],
                "repository_instruction_digest",
            ),
            prompt_digest=_string(old_identity["prompt_digest"], "prompt_digest"),
            tools_digest=_string(old_identity["tools_digest"], "tools_digest"),
            retrieval_digest=_string(
                old_identity["retrieval_digest"], "retrieval_digest"
            ),
            skills_digest=_string(old_identity["skills_digest"], "skills_digest"),
            network_policy_digest=_string(
                old_identity["network_policy_digest"], "network_policy_digest"
            ),
            budget_digest=_string(old_identity["budget_digest"], "budget_digest"),
            retry_policy_digest=_string(
                old_identity["retry_policy_digest"], "retry_policy_digest"
            ),
            stochastic_settings_digest=_string(
                old_identity["stochastic_settings_digest"],
                "stochastic_settings_digest",
            ),
            adapter_digest=_string(old_identity["adapter_digest"], "adapter_digest"),
            workspace_config_digest=_string(
                old_identity["workspace_config_digest"], "workspace_config_digest"
            ),
            runtime_config_digest=_string(
                old_identity["runtime_config_digest"], "runtime_config_digest"
            ),
            hardware_profile_digest=_optional_string(
                old_identity["hardware_profile_digest"], "hardware_profile_digest"
            ),
            identity_digest="",
        )
    )
    result = ResultRecord(
        result_id="",
        result_digest="",
        cache_identity=identity,
        agent_id=_string(old_result["agent_id"], "agent_id"),
        task_id=task_id,
        check_id=check_id,
        terminal_status=cast(
            WorkspaceTerminalStatus,
            _string(old_result["terminal_status"], "terminal_status"),
        ),
        scoreable_state=cast(
            ResultScoreableState,
            _string(old_result["scoreable_state"], "scoreable_state"),
        ),
        outcome=cast(
            CheckOutcomeValue,
            _string(old_result["outcome"], "outcome"),
        ),
        invalid_owner=cast(
            InvalidOwner | None,
            _optional_string(old_result["invalid_owner"], "invalid_owner"),
        ),
        failure_label=_optional_string(old_result["failure_label"], "failure_label"),
        cost=dict(_mapping(old_result["cost"], "cost")),
        scoring_config_digest=_string(
            old_result["scoring_config_digest"], "scoring_config_digest"
        ),
        pricing_version=_string(old_result["pricing_version"], "pricing_version"),
        usage=dict(_mapping(old_result["usage"], "usage")),
        latency=dict(_mapping(old_result["latency"], "latency")),
        diff_digest=_string(old_result["diff_digest"], "diff_digest"),
        verifier_metadata_digest=_string(
            old_result["verifier_metadata_digest"], "verifier_metadata_digest"
        ),
        started_at=_string(old_result["started_at"], "started_at"),
        finished_at=_string(old_result["finished_at"], "finished_at"),
        evidence_source_kind="barcarolle_managed",
        evidence_source_manifest_digest=None,
        evidence_imported_at=None,
        source_result_available_at=_string(
            old_result["result_available_at"], "result_available_at"
        ),
        availability_policy="managed_observation_v1",
        result_available_at=_string(
            old_result["result_available_at"], "result_available_at"
        ),
    )
    result = replace(result, result_id=compute_result_id(result))
    result = record_with_digest(result)
    validation = validate_result(result)
    if not validation.ok:
        raise ValueError(f"migrated Result is invalid: {', '.join(validation.errors)}")
    return result


def _require_digest(value: Mapping[str, Any], digest_field: str, label: str) -> None:
    expected = value.get(digest_field)
    payload = {key: item for key, item in value.items() if key != digest_field}
    if not isinstance(expected, str) or expected != canonical_digest(payload):
        raise ValueError(f"{label} digest does not match its payload")


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{label} must be a string-keyed mapping")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _optional_string(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _string(value, label)


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-scope-id", required=True)
    parser.add_argument("--model-scope-started-at", required=True)
    parser.add_argument("--model-scope-ended-at", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    migrated = migrate_unscoped_model_results(
        args.results,
        args.output,
        model_scope_id=args.model_scope_id,
        model_scope_started_at=args.model_scope_started_at,
        model_scope_ended_at=args.model_scope_ended_at,
    )
    print(f"migrated {len(migrated)} Result records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
