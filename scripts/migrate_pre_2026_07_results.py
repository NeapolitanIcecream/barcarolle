"""Migrate the pre-2026-07 Result JSONL cache to the current schema.

This is deliberately a one-off, non-destructive migration. It preserves paid
execution records for cache reuse; it does not migrate selections, matrices, or
metrics that reference the old result and identity digests.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from barcarolle.records import (
    CheckRecord,
    ResultCacheIdentity,
    ResultRecord,
    canonical_digest,
    load_jsonl_records,
    make_check_digest,
    record_with_digest,
    validate_check,
    validate_result,
    write_jsonl_records,
)


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
        "started_at",
        "task_id",
        "terminal_status",
        "usage",
        "usage_coverage",
        "verifier_metadata_digest",
    }
)

_OLD_IDENTITY_FIELDS = frozenset(
    {
        "adapter_digest",
        "agent_manifest_digest",
        "base_commit",
        "budget_digest",
        "check_id",
        "check_manifest_digest",
        "hardware_profile_digest",
        "harness_digest",
        "hidden_check_bundle_digest",
        "identity_digest",
        "model_snapshot_id",
        "network_policy_digest",
        "prompt_digest",
        "repository_id",
        "repository_instruction_digest",
        "retrieval_digest",
        "retry_policy_digest",
        "runtime_config_digest",
        "scoring_config_digest",
        "skills_digest",
        "solver_material_digest",
        "stochastic_settings_digest",
        "submodule_state_digest",
        "task_id",
        "tools_digest",
        "verifier_deps_digest",
        "verifier_image_digest",
        "workspace_config_digest",
    }
)


def migrate_result_cache(
    results_path: Path,
    checks_path: Path,
    output_path: Path,
) -> tuple[ResultRecord, ...]:
    """Write current-schema Result records without changing the source file."""
    source = results_path.resolve()
    output = output_path.resolve()
    if source == output:
        raise ValueError("output_path must differ from results_path")
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_path}")

    checks = tuple(load_jsonl_records(checks_path, CheckRecord))
    checks_by_id: dict[str, CheckRecord] = {}
    for check in checks:
        validation = validate_check(check)
        if not validation.ok:
            raise ValueError(f"invalid CheckRecord {check.check_id}: {', '.join(validation.errors)}")
        if check.check_id in checks_by_id:
            raise ValueError(f"duplicate CheckRecord: {check.check_id}")
        checks_by_id[check.check_id] = check

    old_rows = _read_old_rows(results_path)
    migrated = tuple(_migrate_result(row, checks_by_id) for row in old_rows)
    write_jsonl_records(output_path, migrated)
    return migrated


def _read_old_rows(path: Path) -> tuple[Mapping[str, Any], ...]:
    rows: list[Mapping[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, Mapping) or set(row) != _OLD_RESULT_FIELDS:
                raise ValueError(f"line {line_number} is not the supported pre-2026-07 Result schema")
            rows.append(row)
    return tuple(rows)


def _migrate_result(
    old_result: Mapping[str, Any],
    checks_by_id: Mapping[str, CheckRecord],
) -> ResultRecord:
    _require_digest(old_result, "result_digest", "old result")
    old_identity = _mapping(old_result["cache_identity"], "cache_identity")
    if set(old_identity) != _OLD_IDENTITY_FIELDS:
        raise ValueError("cache_identity is not the supported pre-2026-07 schema")
    _require_digest(old_identity, "identity_digest", "old cache identity")

    task_id = _string(old_result["task_id"], "task_id")
    check_id = _string(old_result["check_id"], "check_id")
    agent_id = _string(old_result["agent_id"], "agent_id")
    if old_identity["task_id"] != task_id or old_identity["check_id"] != check_id:
        raise ValueError("old cache identity does not match Result task/check")
    check = checks_by_id.get(check_id)
    if check is None:
        raise ValueError(f"missing CheckRecord for {check_id}")
    if check.task_id != task_id:
        raise ValueError(f"CheckRecord {check_id} does not match Result task")
    _require_old_check_binding(old_identity, check)

    identity = ResultCacheIdentity(
        task_id=task_id,
        check_id=check_id,
        repository_id=_string(old_identity["repository_id"], "repository_id"),
        base_commit=_string(old_identity["base_commit"], "base_commit"),
        submodule_state_digest=_string(old_identity["submodule_state_digest"], "submodule_state_digest"),
        solver_material_digest=_string(old_identity["solver_material_digest"], "solver_material_digest"),
        check_digest=make_check_digest(check),
        agent_manifest_digest=_string(old_identity["agent_manifest_digest"], "agent_manifest_digest"),
        model_snapshot_id=_string(old_identity["model_snapshot_id"], "model_snapshot_id"),
        harness_digest=_string(old_identity["harness_digest"], "harness_digest"),
        repository_instruction_digest=_string(
            old_identity["repository_instruction_digest"],
            "repository_instruction_digest",
        ),
        prompt_digest=_string(old_identity["prompt_digest"], "prompt_digest"),
        tools_digest=_string(old_identity["tools_digest"], "tools_digest"),
        retrieval_digest=_string(old_identity["retrieval_digest"], "retrieval_digest"),
        skills_digest=_string(old_identity["skills_digest"], "skills_digest"),
        network_policy_digest=_string(old_identity["network_policy_digest"], "network_policy_digest"),
        budget_digest=_string(old_identity["budget_digest"], "budget_digest"),
        retry_policy_digest=_string(old_identity["retry_policy_digest"], "retry_policy_digest"),
        stochastic_settings_digest=_string(
            old_identity["stochastic_settings_digest"],
            "stochastic_settings_digest",
        ),
        adapter_digest=_string(old_identity["adapter_digest"], "adapter_digest"),
        workspace_config_digest=_string(old_identity["workspace_config_digest"], "workspace_config_digest"),
        runtime_config_digest=_string(old_identity["runtime_config_digest"], "runtime_config_digest"),
        hardware_profile_digest=_optional_string(
            old_identity["hardware_profile_digest"],
            "hardware_profile_digest",
        ),
        identity_digest="",
    )
    identity = record_with_digest(identity)

    usage = dict(_mapping(old_result["usage"], "usage"))
    usage_coverage = _string(old_result["usage_coverage"], "usage_coverage")
    if usage_coverage in {"reported", "complete"} and not usage:
        usage_coverage = "unreported"
    cost = dict(_mapping(old_result["cost"], "cost"))
    if usage_coverage in {"unknown", "unreported"}:
        if cost.get("total_cost") not in {0, 0.0, None}:
            raise ValueError("cannot infer unknown total_cost from the old Result")
        cost["total_cost"] = None

    terminal_status = _string(old_result["terminal_status"], "terminal_status")
    failure_label = _optional_string(old_result["failure_label"], "failure_label")
    scoreable_state, outcome, invalid_owner = _normalize_old_result_state(
        terminal_status,
        _string(old_result["scoreable_state"], "scoreable_state"),
        _string(old_result["outcome"], "outcome"),
        _optional_string(old_result["invalid_owner"], "invalid_owner"),
        failure_label,
    )
    result = ResultRecord(
        result_id=_string(old_result["result_id"], "result_id"),
        result_digest="",
        cache_identity=identity,
        agent_id=agent_id,
        task_id=task_id,
        check_id=check_id,
        terminal_status=terminal_status,
        scoreable_state=scoreable_state,
        outcome=outcome,
        invalid_owner=invalid_owner,
        failure_label=failure_label,
        cost=cost,
        scoring_config_digest=_string(old_identity["scoring_config_digest"], "scoring_config_digest"),
        pricing_version=_string(old_result["pricing_version"], "pricing_version"),
        usage=usage,
        latency=dict(_mapping(old_result["latency"], "latency")),
        diff_digest=_string(old_result["diff_digest"], "diff_digest"),
        verifier_metadata_digest=_string(
            old_result["verifier_metadata_digest"],
            "verifier_metadata_digest",
        ),
        started_at=_string(old_result["started_at"], "started_at"),
        finished_at=_string(old_result["finished_at"], "finished_at"),
        result_available_at=_string(old_result["result_available_at"], "result_available_at"),
    )
    result = record_with_digest(result)
    validation = validate_result(result)
    if not validation.ok:
        raise ValueError(f"migrated Result {result.result_id} is invalid: {', '.join(validation.errors)}")
    return result


def _normalize_old_result_state(
    terminal_status: str,
    scoreable_state: str,
    outcome: str,
    old_invalid_owner: str | None,
    failure_label: str | None,
) -> tuple[str, str, str | None]:
    old_state = (terminal_status, scoreable_state, outcome, old_invalid_owner)
    if old_state == ("passed", "scoreable", "pass", None):
        return ("scoreable", "pass", None)
    if old_state == ("failed", "scoreable", "fail", None):
        return ("scoreable", "fail", None)
    if old_state == ("error", "scoreable", "fail", None) and failure_label == "agent_failed":
        return ("agent_invalid", "invalid", "agent")
    raise ValueError(
        "unsupported old result state; inspect benchmark ownership before migration"
    )


def _require_digest(value: Mapping[str, Any], digest_field: str, label: str) -> None:
    expected = value.get(digest_field)
    payload = {key: item for key, item in value.items() if key != digest_field}
    if not isinstance(expected, str) or expected != canonical_digest(payload):
        raise ValueError(f"{label} digest does not match its payload")


def _require_old_check_binding(identity: Mapping[str, Any], check: CheckRecord) -> None:
    expected = {
        "check_manifest_digest": check.check_manifest_digest,
        "hidden_check_bundle_digest": check.hidden_check_bundle_digest,
        "verifier_image_digest": check.verifier_image_digest,
        "verifier_deps_digest": check.verifier_deps_digest,
    }
    mismatched = [field for field, value in expected.items() if identity[field] != value]
    if mismatched:
        raise ValueError(f"old cache identity does not match CheckRecord: {', '.join(mismatched)}")


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{label} must be a string-keyed mapping")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _optional_string(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _string(value, label)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True, help="pre-2026-07 results.jsonl")
    parser.add_argument("--checks", type=Path, required=True, help="matching checks.jsonl")
    parser.add_argument("--output", type=Path, required=True, help="new, current-schema JSONL path")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    migrated = migrate_result_cache(args.results, args.checks, args.output)
    print(f"migrated {len(migrated)} Result records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
