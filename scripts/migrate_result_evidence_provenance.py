"""Add explicit managed-evidence provenance to pre-provenance Result records.

This one-off migration is non-destructive. It is only for Result records
written by Barcarolle before evidence source and availability policy became
explicit. It must not be used to relabel third-party Result records as
Barcarolle-managed evidence. The current evidence fields change both Result ID
and digest. Derived FeatureSnapshots, SelectorInputs, Selections, fitted
Selectors, CellSets, matrices, and metrics that bind old identities must be
rebuilt separately.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
from typing import Any, Mapping, cast

from barcarolle.records import (
    CheckOutcomeValue,
    InvalidOwner,
    ResultCacheIdentity,
    ResultRecord,
    ResultScoreableState,
    WorkspaceTerminalStatus,
    canonical_digest,
    canonical_json,
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

_IDENTITY_FIELDS = frozenset(
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
        "model_resolution_scope_ended_at",
        "model_resolution_scope_id",
        "model_resolution_scope_started_at",
        "model_snapshot_id",
        "network_policy_digest",
        "prompt_digest",
        "repository_id",
        "repository_instruction_digest",
        "requested_model_id",
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


def migrate_result_evidence_provenance(
    results_path: Path,
    output_path: Path,
) -> tuple[ResultRecord, ...]:
    source = results_path.resolve()
    output = output_path.resolve()
    if source == output:
        raise ValueError("output_path must differ from results_path")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    rows = _read_old_results(source)
    migrated = tuple(_migrate_result(row) for row in rows)
    ensure_unique_result_ids(migrated)
    write_jsonl_records(output, migrated)
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
                        "Result record is not the supported pre-provenance schema"
                    )
                _require_digest(row, "result_digest", "old Result")
                rows.append(row)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                raise ValueError(f"{path}: line {line_number}: {exc}") from exc
    return tuple(rows)


def _migrate_result(old_result: Mapping[str, Any]) -> ResultRecord:
    old_identity = _mapping(old_result["cache_identity"], "cache_identity")
    if set(old_identity) != _IDENTITY_FIELDS:
        raise ValueError("cache_identity is not the supported current schema")
    _require_digest(old_identity, "identity_digest", "cache identity")
    identity = ResultCacheIdentity(**dict(old_identity))
    available_at = _string(
        old_result["result_available_at"],
        "result_available_at",
    )
    result = ResultRecord(
        result_id="",
        result_digest="",
        cache_identity=identity,
        agent_id=_string(old_result["agent_id"], "agent_id"),
        task_id=_string(old_result["task_id"], "task_id"),
        check_id=_string(old_result["check_id"], "check_id"),
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
        failure_label=_optional_string(
            old_result["failure_label"],
            "failure_label",
        ),
        cost=dict(_mapping(old_result["cost"], "cost")),
        scoring_config_digest=_string(
            old_result["scoring_config_digest"],
            "scoring_config_digest",
        ),
        pricing_version=_string(
            old_result["pricing_version"],
            "pricing_version",
        ),
        usage=dict(_mapping(old_result["usage"], "usage")),
        latency=dict(_mapping(old_result["latency"], "latency")),
        diff_digest=_string(old_result["diff_digest"], "diff_digest"),
        verifier_metadata_digest=_string(
            old_result["verifier_metadata_digest"],
            "verifier_metadata_digest",
        ),
        started_at=_string(old_result["started_at"], "started_at"),
        finished_at=_string(old_result["finished_at"], "finished_at"),
        evidence_source_kind="barcarolle_managed",
        evidence_source_manifest_digest=None,
        evidence_imported_at=None,
        source_result_available_at=available_at,
        availability_policy="managed_observation_v1",
        result_available_at=available_at,
    )
    result = replace(result, result_id=compute_result_id(result))
    result = record_with_digest(result)
    validation = validate_result(result)
    if not validation.ok:
        raise ValueError(
            f"migrated Result {result.result_id} is invalid: "
            + ", ".join(validation.errors)
        )
    return result


def _require_digest(
    value: Mapping[str, Any],
    digest_field: str,
    label: str,
) -> None:
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    migrated = migrate_result_evidence_provenance(
        args.results,
        args.output,
    )
    print(f"migrated {len(migrated)} Result records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
