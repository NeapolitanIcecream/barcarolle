import json
from pathlib import Path

import pytest

from barcarolle.records import canonical_digest
from barcarolle.task_pool import (
    CertificationConfig,
    CertificationResult,
    CheckConfig,
    ImportConfig,
    StatementConfig,
    TaskSourceConfig,
    TimeRange,
    build_check_candidate,
    build_task_statement,
    certify_task_candidate,
    freeze_task_pool,
    generate_history_candidates,
    import_task_pool,
    summarize_task_pool,
)


def test_generate_history_candidates_filters_by_time_range_and_defaults_repository() -> None:
    candidates = generate_history_candidates(
        "repo-url",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(
            source_family="issue",
            source_events=(
                _candidate_payload(source_ref="issue-1", source_resolved_at="2026-01-10T00:00:00Z"),
                _candidate_payload(source_ref="issue-2", source_resolved_at="2026-02-10T00:00:00Z"),
            ),
        ),
    )

    assert len(candidates) == 1
    assert candidates[0].repository_id == "repo"
    assert candidates[0].source_ref == "issue-1"


def test_time_range_compares_timezone_offsets_as_instants() -> None:
    time_range = TimeRange("2026-01-01T10:00:00Z", "2026-01-01T12:00:00Z")

    assert time_range.contains("2026-01-01T06:00:00-05:00")
    assert not time_range.contains("2026-01-01T05:00:00-10:00")


def test_import_task_pool_loads_json_and_applies_import_family(tmp_path: Path) -> None:
    source = tmp_path / "pool.json"
    payload = _candidate_payload()
    del payload["source_family"]
    source.write_text(json.dumps({"candidates": [payload]}), encoding="utf-8")

    candidates = import_task_pool(source, ImportConfig(source_family="user_import"))

    assert len(candidates) == 1
    assert candidates[0].source_family == "user_import"


def test_build_task_statement_uses_only_configured_solver_visible_material() -> None:
    candidate = generate_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(source_family="issue", source_events=(_candidate_payload(),)),
    )[0]

    statement = build_task_statement(candidate, StatementConfig(material_keys=("title",), separator="\n"))

    assert statement == "Fix the parser"
    assert "Hidden" not in statement


def test_build_check_candidate_binds_check_to_stable_task_id() -> None:
    candidate = generate_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(source_family="issue", source_events=(_candidate_payload(),)),
    )[0]
    check = build_check_candidate(candidate, _check_config())

    assert check.task_id.startswith("task_")
    assert check.check_id.startswith("check_")
    assert check.hidden_check_bundle_digest == candidate.hidden_check_bundle_digest


def test_certify_task_candidate_accepts_clean_candidate_and_rejects_hidden_solver_refs() -> None:
    clean = generate_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(source_family="issue", source_events=(_candidate_payload(),)),
    )[0]
    dirty = generate_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(
            source_family="issue",
            source_events=(_candidate_payload(solver_material_refs=("README.md", "hidden/oracle.txt")),),
        ),
    )[0]

    accepted = certify_task_candidate(clean, CertificationConfig())
    rejected = certify_task_candidate(dirty, CertificationConfig())

    assert accepted.accepted
    assert accepted.task is not None
    assert accepted.check is not None
    assert not rejected.accepted
    assert any("hidden check" in reason for reason in rejected.rejection_reasons)


def test_certify_task_candidate_rejects_missing_required_certification_evidence() -> None:
    candidate = generate_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(
            source_family="issue",
            source_events=(_candidate_payload(certification_evidence={"checkout_valid": True}),),
        ),
    )[0]

    result = certify_task_candidate(candidate, CertificationConfig())

    assert not result.accepted
    assert "certification evidence failed: check_executable" in result.rejection_reasons
    assert result.task is None
    assert result.check is None


def test_solver_visible_statement_rejects_hidden_or_oracle_text() -> None:
    candidate = generate_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(
            source_family="issue",
            source_events=(
                _candidate_payload(statement_material={"title": "Use the hidden oracle answer", "body": "Fix it"}),
            ),
        ),
    )[0]

    with pytest.raises(ValueError, match="hidden or oracle material"):
        build_task_statement(candidate, StatementConfig())

    result = certify_task_candidate(candidate, CertificationConfig())

    assert not result.accepted
    assert "solver-visible task statement contains hidden or oracle material" in result.rejection_reasons


def test_freeze_task_pool_records_digests_rejections_and_summary() -> None:
    candidate = generate_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(source_family="issue", source_events=(_candidate_payload(),)),
    )[0]
    accepted = certify_task_candidate(candidate, CertificationConfig())
    assert accepted.task is not None
    assert accepted.check is not None

    task_pool = freeze_task_pool(
        [accepted.task],
        [accepted.check],
        [],
        {
            "repository_id": "repo",
            "accepted_certification_results": (accepted,),
            "task_records_ref": "tasks.jsonl",
            "check_records_ref": "checks.jsonl",
            "source_event_inventory_digest": "source-events",
            "generator_config_digest": "generator",
            "certification_config_digest": canonical_digest(CertificationConfig()),
            "created_at": "2026-01-31T00:00:00Z",
        },
    )
    summary = summarize_task_pool(task_pool)

    assert task_pool.task_pool_id.startswith("task_pool_")
    assert task_pool.task_pool_digest
    assert task_pool.task_ids == (accepted.task.task_id,)
    assert summary["task_count"] == 1
    assert summary["rejected_count"] == 0


def test_freeze_task_pool_rejects_broken_task_check_linkage() -> None:
    candidate = generate_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(source_family="issue", source_events=(_candidate_payload(),)),
    )[0]
    accepted = certify_task_candidate(candidate, CertificationConfig())
    assert accepted.task is not None
    assert accepted.check is not None

    with pytest.raises(ValueError, match="references missing checks"):
        freeze_task_pool(
            [accepted.task],
            [],
            [],
            {
                "repository_id": "repo",
                "accepted_certification_results": (accepted,),
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "source_event_inventory_digest": "source-events",
                "generator_config_digest": "generator",
                "certification_config_digest": canonical_digest(CertificationConfig()),
                "created_at": "2026-01-31T00:00:00Z",
            },
        )


def test_freeze_task_pool_rejects_missing_required_metadata() -> None:
    candidate = generate_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(source_family="issue", source_events=(_candidate_payload(),)),
    )[0]
    accepted = certify_task_candidate(candidate, CertificationConfig())
    assert accepted.task is not None
    assert accepted.check is not None

    with pytest.raises(ValueError, match="metadata is missing required fields"):
        freeze_task_pool(
            [accepted.task],
            [accepted.check],
            [],
            {
                "repository_id": "repo",
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "created_at": "2026-01-31T00:00:00Z",
            },
        )


def test_freeze_task_pool_rejects_missing_accepted_certification_result() -> None:
    candidate = generate_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(source_family="issue", source_events=(_candidate_payload(),)),
    )[0]
    accepted = certify_task_candidate(candidate, CertificationConfig())
    assert accepted.task is not None
    assert accepted.check is not None

    with pytest.raises(ValueError, match="accepted_certification_results must align"):
        freeze_task_pool(
            [accepted.task],
            [accepted.check],
            [],
            {
                "repository_id": "repo",
                "accepted_certification_results": (),
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "source_event_inventory_digest": "source-events",
                "generator_config_digest": "generator",
                "certification_config_digest": canonical_digest(CertificationConfig()),
                "created_at": "2026-01-31T00:00:00Z",
            },
        )


def test_freeze_task_pool_rejects_unbound_accepted_certification_result() -> None:
    candidate = generate_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(source_family="issue", source_events=(_candidate_payload(),)),
    )[0]
    accepted = certify_task_candidate(candidate, CertificationConfig())
    assert accepted.task is not None
    assert accepted.check is not None
    bad_result = CertificationResult(
        candidate_id="other",
        accepted=True,
        task=accepted.task,
        check=accepted.check,
        rejection_reasons=(),
        evidence=accepted.evidence,
        evidence_digest="arbitrary-digest",
    )

    with pytest.raises(ValueError, match="evidence digest does not match"):
        freeze_task_pool(
            [accepted.task],
            [accepted.check],
            [],
            {
                "repository_id": "repo",
                "accepted_certification_results": (bad_result,),
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "source_event_inventory_digest": "source-events",
                "generator_config_digest": "generator",
                "certification_config_digest": canonical_digest(CertificationConfig()),
                "created_at": "2026-01-31T00:00:00Z",
            },
        )


def test_freeze_task_pool_revalidates_hidden_solver_material() -> None:
    candidate = generate_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(source_family="issue", source_events=(_candidate_payload(),)),
    )[0]
    accepted = certify_task_candidate(candidate, CertificationConfig())
    assert accepted.task is not None
    assert accepted.check is not None
    bad_task = type(accepted.task)(
        **{
            **accepted.task.__dict__,
            "solver_material_refs": ("hidden/oracle.txt",),
        }
    )

    with pytest.raises(ValueError, match="failed validation"):
        freeze_task_pool(
            [bad_task],
            [accepted.check],
            [],
            {
                "repository_id": "repo",
                "accepted_certification_results": (accepted,),
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "source_event_inventory_digest": "source-events",
                "generator_config_digest": "generator",
                "certification_config_digest": canonical_digest(CertificationConfig()),
                "created_at": "2026-01-31T00:00:00Z",
            },
        )


def test_freeze_task_pool_rejects_repository_mismatch() -> None:
    candidate = generate_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(source_family="issue", source_events=(_candidate_payload(),)),
    )[0]
    accepted = certify_task_candidate(candidate, CertificationConfig())
    assert accepted.task is not None
    assert accepted.check is not None

    with pytest.raises(ValueError, match="repository_id does not match"):
        freeze_task_pool(
            [accepted.task],
            [accepted.check],
            [],
            {
                "repository_id": "other-repo",
                "accepted_certification_results": (accepted,),
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "source_event_inventory_digest": "source-events",
                "generator_config_digest": "generator",
                "certification_config_digest": canonical_digest(CertificationConfig()),
                "created_at": "2026-01-31T00:00:00Z",
            },
        )


def _check_config() -> CheckConfig:
    return CheckConfig(
        check_type="pytest",
        verifier_image_digest="image",
        verifier_deps_digest="deps",
        resource_limits={"timeout_seconds": 30},
        oracle_source="private_tests",
    )


def _candidate_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "repository_id": "repo",
        "base_commit": "abc123",
        "source_family": "issue",
        "source_ref": "issue-1",
        "source_resolved_at": "2026-01-10T00:00:00Z",
        "task_material_available_at": "2026-01-11T00:00:00Z",
        "check_material_available_at": "2026-01-12T00:00:00Z",
        "solver_material_refs": ("README.md", "src/parser.py"),
        "solver_material_digest": "solver-material",
        "cluster_id": "cluster-1",
        "statement_material": {
            "title": "Fix the parser",
            "body": "The parser should accept quoted values.",
            "hidden": "Hidden oracle detail",
        },
        "check_manifest_digest": "check-manifest",
        "hidden_check_bundle_digest": "hidden-bundle",
        "verifier_image_digest": "image",
        "verifier_deps_digest": "deps",
        "resource_limits": {"timeout_seconds": 30},
        "oracle_source": "private_tests",
        "check_type": "pytest",
        "certification_evidence": {
            "checkout_valid": True,
            "dependencies_restored": True,
            "check_executable": True,
            "oracle_stable": True,
            "solver_visible_boundary": True,
            "hidden_material_separated": True,
            "statement_clear": True,
        },
    }
    payload.update(overrides)
    return payload
