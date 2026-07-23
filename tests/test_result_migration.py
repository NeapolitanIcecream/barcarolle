from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from barcarolle.records import (
    CheckRecord,
    ResultRecord,
    canonical_digest,
    canonical_json,
    load_jsonl_records,
    make_check_digest,
    validate_result,
)


def test_migrate_result_cache_preserves_execution_and_moves_pricing(
    tmp_path: Path,
) -> None:
    check = _check()
    old_result = _old_result(check)
    results_path = tmp_path / "results.v1.jsonl"
    checks_path = tmp_path / "checks.jsonl"
    output_path = tmp_path / "results.latest.jsonl"
    results_path.write_text(
        json.dumps(old_result, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_old_check(checks_path, check)

    completed = _run_migration(results_path, checks_path, output_path)
    loaded = load_jsonl_records(output_path, ResultRecord)

    assert completed.returncode == 0
    assert "migrated 1 Result records" in completed.stdout
    assert len(loaded) == 1
    result = loaded[0]
    assert validate_result(result).ok
    assert result.result_id == old_result["result_id"]
    assert result.scoring_config_digest == "scoring-v1"
    assert result.cache_identity.check_digest == make_check_digest(check)
    assert result.cache_identity.requested_model_id == "model"
    assert result.cache_identity.model_snapshot_id is None
    assert result.cache_identity.model_resolution_scope_id.startswith("legacy-result-")
    assert (
        result.cache_identity.identity_digest
        != old_result["cache_identity"]["identity_digest"]
    )
    assert result.cost["total_cost"] is None
    assert (
        results_path.read_text(encoding="utf-8")
        == json.dumps(old_result, sort_keys=True) + "\n"
    )


def test_migrate_result_cache_refuses_overwrite_and_corrupt_input(
    tmp_path: Path,
) -> None:
    check = _check()
    results_path = tmp_path / "results.v1.jsonl"
    checks_path = tmp_path / "checks.jsonl"
    output_path = tmp_path / "results.latest.jsonl"
    _write_old_check(checks_path, check)
    old_result = _old_result(check)
    old_result["result_digest"] = "corrupt"
    results_path.write_text(json.dumps(old_result) + "\n", encoding="utf-8")

    corrupt = _run_migration(results_path, checks_path, output_path)
    assert corrupt.returncode != 0
    assert "old result digest" in corrupt.stderr

    output_path.write_text("occupied\n", encoding="utf-8")
    occupied = _run_migration(results_path, checks_path, output_path)
    assert occupied.returncode != 0
    assert "refusing to overwrite" in occupied.stderr


def test_migrate_result_cache_normalizes_legacy_error_and_empty_complete_usage(
    tmp_path: Path,
) -> None:
    check = _check()
    old_result = _old_result(check)
    old_result.update(
        terminal_status="error",
        scoreable_state="scoreable",
        outcome="fail",
        invalid_owner=None,
        failure_label="agent_failed",
        usage_coverage="complete",
        usage={},
    )
    old_result.pop("result_digest")
    old_result["result_digest"] = canonical_digest(old_result)
    results_path = tmp_path / "results.v1.jsonl"
    checks_path = tmp_path / "checks.jsonl"
    output_path = tmp_path / "results.latest.jsonl"
    results_path.write_text(json.dumps(old_result) + "\n", encoding="utf-8")
    _write_old_check(checks_path, check)

    completed = _run_migration(results_path, checks_path, output_path)
    result = load_jsonl_records(output_path, ResultRecord)[0]

    assert completed.returncode == 0
    assert (
        result.terminal_status,
        result.scoreable_state,
        result.outcome,
        result.invalid_owner,
    ) == (
        "error",
        "agent_invalid",
        "invalid",
        "agent",
    )
    assert result.usage == {}
    assert result.cost["total_cost"] is None
    assert validate_result(result).ok


def test_migrate_result_cache_rejects_benchmark_owned_error(tmp_path: Path) -> None:
    check = _check()
    old_result = _old_result(check)
    old_result.update(
        terminal_status="error",
        scoreable_state="benchmark_invalid",
        outcome="invalid",
        invalid_owner="benchmark",
        failure_label="infrastructure_failed",
    )
    old_result.pop("result_digest")
    old_result["result_digest"] = canonical_digest(old_result)
    results_path = tmp_path / "results.v1.jsonl"
    checks_path = tmp_path / "checks.jsonl"
    output_path = tmp_path / "results.latest.jsonl"
    results_path.write_text(json.dumps(old_result) + "\n", encoding="utf-8")
    _write_old_check(checks_path, check)

    completed = _run_migration(results_path, checks_path, output_path)

    assert completed.returncode != 0
    assert "inspect benchmark ownership" in completed.stderr
    assert not output_path.exists()


def test_migrate_unscoped_model_results_preserves_source_and_limits_alias_reuse(
    tmp_path: Path,
) -> None:
    old_result = _unscoped_model_result(_check())
    results_path = tmp_path / "results.unscoped-model.jsonl"
    output_path = tmp_path / "results.latest.jsonl"
    source = f"{canonical_json(old_result)}\n"
    results_path.write_text(source, encoding="utf-8")

    completed = _run_model_identity_migration(results_path, output_path)
    result = load_jsonl_records(output_path, ResultRecord)[0]

    assert completed.returncode == 0
    assert result.cache_identity.requested_model_id == "model"
    assert result.cache_identity.model_snapshot_id is None
    assert result.cache_identity.model_resolution_scope_id == "historical-campaign"
    assert result.cache_identity.model_resolution_scope_started_at == (
        "2025-12-31T00:00:00Z"
    )
    assert result.cache_identity.model_resolution_scope_ended_at == (
        "2026-01-02T00:00:00Z"
    )
    assert validate_result(result).ok
    assert results_path.read_text(encoding="utf-8") == source


def test_migrate_unscoped_model_results_rejects_corrupt_input_and_overwrite(
    tmp_path: Path,
) -> None:
    old_result = _unscoped_model_result(_check())
    old_result["result_digest"] = "corrupt"
    results_path = tmp_path / "results.unscoped-model.jsonl"
    output_path = tmp_path / "results.latest.jsonl"
    results_path.write_text(f"{canonical_json(old_result)}\n", encoding="utf-8")

    corrupt = _run_model_identity_migration(results_path, output_path)
    assert corrupt.returncode != 0
    assert "old Result digest" in corrupt.stderr

    output_path.write_text("occupied\n", encoding="utf-8")
    occupied = _run_model_identity_migration(results_path, output_path)
    assert occupied.returncode != 0
    assert "refusing to overwrite" in occupied.stderr


def _run_migration(
    results_path: Path,
    checks_path: Path,
    output_path: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (
            sys.executable,
            "scripts/migrate_pre_2026_07_results.py",
            "--results",
            str(results_path),
            "--checks",
            str(checks_path),
            "--output",
            str(output_path),
        ),
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _run_model_identity_migration(
    results_path: Path,
    output_path: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (
            sys.executable,
            "scripts/migrate_unscoped_model_results.py",
            "--results",
            str(results_path),
            "--output",
            str(output_path),
            "--model-scope-id",
            "historical-campaign",
            "--model-scope-started-at",
            "2025-12-31T00:00:00Z",
            "--model-scope-ended-at",
            "2026-01-02T00:00:00Z",
        ),
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _check() -> CheckRecord:
    return CheckRecord(
        check_id="check",
        task_id="task",
        check_type="tests",
        check_manifest_digest="check-manifest",
        hidden_check_bundle_digest="hidden-bundle",
        resource_limits={"timeout_seconds": 30},
        oracle_source="private",
        check_material_available_at="2026-01-01T00:00:00Z",
    )


def _write_old_check(path: Path, check: CheckRecord) -> None:
    payload = {
        **check.__dict__,
        "certified_at": check.check_material_available_at,
        "verifier_image_digest": "verifier-image",
        "verifier_deps_digest": "verifier-deps",
    }
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _old_result(check: CheckRecord) -> dict[str, object]:
    identity: dict[str, object] = {
        "task_id": "task",
        "check_id": check.check_id,
        "repository_id": "repo",
        "base_commit": "commit",
        "submodule_state_digest": "submodules",
        "solver_material_digest": "solver-material",
        "check_manifest_digest": check.check_manifest_digest,
        "hidden_check_bundle_digest": check.hidden_check_bundle_digest,
        "verifier_image_digest": "verifier-image",
        "verifier_deps_digest": "verifier-deps",
        "agent_manifest_digest": "agent-manifest",
        "model_snapshot_id": "model",
        "harness_digest": "harness",
        "repository_instruction_digest": "instructions",
        "prompt_digest": "prompt",
        "tools_digest": "tools",
        "retrieval_digest": "retrieval",
        "skills_digest": "skills",
        "network_policy_digest": "network",
        "budget_digest": "budget",
        "retry_policy_digest": "retry",
        "stochastic_settings_digest": "stochastic",
        "adapter_digest": "adapter",
        "workspace_config_digest": "workspace",
        "runtime_config_digest": "runtime",
        "hardware_profile_digest": None,
        "scoring_config_digest": "scoring-v1",
    }
    identity["identity_digest"] = canonical_digest(identity)
    result: dict[str, object] = {
        "result_id": "result-paid-execution",
        "cache_identity": identity,
        "agent_id": "agent",
        "task_id": "task",
        "check_id": "check",
        "terminal_status": "passed",
        "scoreable_state": "scoreable",
        "outcome": "pass",
        "invalid_owner": None,
        "failure_label": None,
        "cost": {"total_cost": 0.0},
        "pricing_version": "usage-unpriced",
        "usage": {},
        "usage_coverage": "unknown",
        "latency": {"workspace_seconds": 10.0},
        "diff_digest": "diff",
        "verifier_metadata_digest": "verifier-metadata",
        "started_at": "2026-01-01T00:00:00Z",
        "finished_at": "2026-01-01T00:00:10Z",
        "result_available_at": "2026-01-01T00:00:10Z",
    }
    result["result_digest"] = canonical_digest(result)
    return result


def _unscoped_model_result(check: CheckRecord) -> dict[str, object]:
    result = _old_result(check)
    identity = dict(result["cache_identity"])
    scoring_config_digest = identity.pop("scoring_config_digest")
    for field in (
        "check_manifest_digest",
        "hidden_check_bundle_digest",
        "verifier_deps_digest",
        "verifier_image_digest",
    ):
        identity.pop(field)
    identity["check_digest"] = make_check_digest(check)
    identity.pop("identity_digest")
    identity["identity_digest"] = canonical_digest(identity)

    result["cache_identity"] = identity
    result["scoring_config_digest"] = scoring_config_digest
    result.pop("usage_coverage")
    result.pop("result_digest")
    result["result_digest"] = canonical_digest(result)
    return result
