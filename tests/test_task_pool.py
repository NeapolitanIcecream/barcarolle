from dataclasses import replace
import json
from pathlib import Path
import hashlib
import subprocess
import sys
from typing import Any

import pytest

import barcarolle.task_pool as task_pool_module
from barcarolle.records import (
    CheckRecord,
    RuntimeConfig,
    SourceEventRecord,
    TaskPoolRecord,
    TaskRecord,
    WorkspaceConfig,
    canonical_digest,
    format_utc_timestamp,
    make_source_event_id,
    make_check_digest,
    parse_utc_timestamp,
    record_with_digest,
    write_jsonl_records,
)
from barcarolle.task_pool import (
    CertificationConfig,
    CertificationResult,
    ImportConfig,
    TaskCandidate,
    TaskSourceConfig,
    TimeRange,
    build_check_candidate,
    certify_task_candidate,
    filter_history_candidates,
    freeze_task_pool,
    import_task_candidates,
    load_validated_task_pool_bundle,
    summarize_task_pool,
)
from barcarolle.workspace import (
    CapturedDiff,
    WorkspaceRunContext,
    bind_check_material,
    bind_repository_source,
    check_execution_binding_digest,
)
from barcarolle.verification import (
    VERIFICATION_ADAPTER_DIGEST,
    CheckOutcome,
    hidden_material_digest,
)


@pytest.fixture(scope="module")
def accepted_result(tmp_path_factory: pytest.TempPathFactory) -> CertificationResult:
    candidate, workspace_config, runtime_config, reference_patch, run_context = (
        _executable_candidate(tmp_path_factory.mktemp("accepted-task"))
    )
    result = certify_task_candidate(
        candidate,
        CertificationConfig(),
        workspace_config,
        runtime_config,
        reference_patch,
        run_context,
    )
    assert result.accepted
    return result


def test_filter_history_candidates_records_exclusions_and_defaults_repository() -> None:
    batch = filter_history_candidates(
        "repo-url",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(
            source_family="issue",
            source_events=(
                _candidate_payload(
                    source_ref="issue-1", source_resolved_at="2026-01-10T00:00:00Z"
                ),
                _candidate_payload(
                    source_ref="issue-2",
                    source_resolved_at="2026-02-10T00:00:00Z",
                    task_material_available_at="2026-02-11T00:00:00Z",
                    check_material_available_at="2026-02-12T00:00:00Z",
                ),
            ),
        ),
    )

    assert len(batch.candidates) == 1
    assert batch.candidates[0].repository_id == "repo"
    assert batch.candidates[0].source_ref == "issue-1"
    assert len(batch.excluded_source_events) == 1
    assert batch.excluded_source_events[0].rejection_reasons == (
        "outside_source_time_range",
    )


def test_filter_history_candidates_preserves_unmatured_event_as_censored() -> None:
    batch = filter_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(
            source_family="issue",
            source_events=(
                _candidate_payload(
                    check_material_available_at=None,
                ),
            ),
        ),
    )

    assert batch.candidates == ()
    assert len(batch.excluded_source_events) == 1
    event = batch.excluded_source_events[0]
    assert event.task_material_available_at == "2026-01-11T00:00:00Z"
    assert event.check_material_available_at is None
    assert event.label_mature_at is None
    assert event.rejection_reasons == ("check_material_unavailable",)


def test_time_range_compares_timezone_offsets_as_instants() -> None:
    time_range = TimeRange("2026-01-01T10:00:00Z", "2026-01-01T12:00:00Z")

    assert time_range.contains("2026-01-01T06:00:00-05:00")
    assert not time_range.contains("2026-01-01T05:00:00-10:00")


def test_time_range_rejects_timezone_naive_boundaries() -> None:
    with pytest.raises(ValueError, match="timezone offset"):
        TimeRange("2026-01-01T10:00:00", "2026-01-01T12:00:00Z").contains(
            "2026-01-01T11:00:00Z"
        )


def test_import_task_candidates_loads_json_and_applies_import_family(
    tmp_path: Path,
) -> None:
    source = tmp_path / "pool.json"
    payload = _candidate_payload()
    del payload["source_family"]
    source.write_text(json.dumps({"candidates": [payload]}), encoding="utf-8")

    candidates = import_task_candidates(
        source,
        ImportConfig(source_family="user_import"),
    ).candidates

    assert len(candidates) == 1
    assert candidates[0].source_family == "user_import"


@pytest.mark.parametrize(
    "field_name",
    (
        "source_ref",
        "candidate_id",
        "task_text",
        "dependency_cluster_id",
        "sampling_stratum",
    ),
)
def test_filter_history_candidates_rejects_nonstring_identity_fields(
    field_name: str,
) -> None:
    payload = _candidate_payload()
    payload[field_name] = 7

    with pytest.raises(ValueError, match=rf"{field_name} must be a string"):
        filter_history_candidates(
            "repo",
            TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
            TaskSourceConfig(source_family="issue", source_events=(payload,)),
        )


@pytest.mark.parametrize(
    ("field_name", "value", "error"),
    (
        (
            "solver_material_refs",
            ("README.md", 7),
            "solver_material_refs must be a sequence of strings",
        ),
        (
            "resource_limits",
            (("timeout_seconds", 30),),
            "resource_limits must be a mapping",
        ),
        (
            "resource_limits",
            {7: 30},
            "resource_limits keys must be strings",
        ),
    ),
)
def test_filter_history_candidates_rejects_noncanonical_container_fields(
    field_name: str,
    value: object,
    error: str,
) -> None:
    payload = _candidate_payload()
    payload[field_name] = value

    with pytest.raises(ValueError, match=error):
        filter_history_candidates(
            "repo",
            TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
            TaskSourceConfig(source_family="issue", source_events=(payload,)),
        )


def test_filter_history_candidates_does_not_coerce_excluded_event_labels() -> None:
    payload = _candidate_payload(
        source_resolved_at="2026-02-10T00:00:00Z",
        dependency_cluster_id=7,
    )

    with pytest.raises(ValueError, match="dependency_cluster_id must be a string"):
        filter_history_candidates(
            "repo",
            TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
            TaskSourceConfig(source_family="issue", source_events=(payload,)),
        )


def test_build_check_candidate_binds_check_to_stable_task_id() -> None:
    candidate = filter_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(source_family="issue", source_events=(_candidate_payload(),)),
    ).candidates[0]
    check = build_check_candidate(candidate)

    assert check.task_id.startswith("task_")
    assert check.check_id.startswith("check_")
    assert check.hidden_check_bundle_digest == candidate.hidden_check_bundle_digest


def test_build_check_candidate_keeps_logical_id_but_versions_hidden_material() -> None:
    candidate = filter_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(source_family="issue", source_events=(_candidate_payload(),)),
    ).candidates[0]

    original = build_check_candidate(candidate)
    changed = build_check_candidate(
        replace(candidate, hidden_check_bundle_digest="other-hidden-bundle")
    )

    assert changed.check_id == original.check_id
    assert make_check_digest(changed) != make_check_digest(original)


@pytest.mark.parametrize("value", (True, 1.0, 0, -1, "1", None))
def test_certification_config_requires_a_positive_integer(value: object) -> None:
    config_type: Any = CertificationConfig

    with pytest.raises(ValueError, match="repeat_count must be a positive integer"):
        config_type(repeat_count=value)


@pytest.mark.parametrize(
    ("config_name", "changes", "expected_error"),
    (
        (
            "workspace_config",
            {"workspace_config_id": 7},
            "workspace_config is invalid: "
            "WorkspaceConfig.workspace_config_id must be a string",
        ),
        (
            "runtime_config",
            {"runtime_config_id": 7},
            "runtime_config is invalid: "
            "RuntimeConfig.runtime_config_id must be a string",
        ),
    ),
)
def test_certify_task_candidate_validates_configs_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    config_name: str,
    changes: dict[str, object],
    expected_error: str,
) -> None:
    candidate, workspace_config, runtime_config, reference_patch, run_context = (
        _executable_candidate(tmp_path)
    )
    if config_name == "workspace_config":
        workspace_config = replace(workspace_config, **changes)
    else:
        runtime_config = replace(runtime_config, **changes)

    def unexpected_check(*args: object, **kwargs: object) -> CheckOutcome:
        raise AssertionError("config validation must precede Check execution")

    monkeypatch.setattr(task_pool_module, "_run_task_check", unexpected_check)

    with pytest.raises(ValueError, match=expected_error):
        certify_task_candidate(
            candidate,
            CertificationConfig(),
            workspace_config,
            runtime_config,
            reference_patch,
            run_context,
        )


def test_certify_task_candidate_requires_base_fail_and_reference_patch_pass(
    tmp_path: Path,
) -> None:
    workspace_log = tmp_path / "workspaces.txt"
    clean, workspace_config, runtime_config, reference_patch, run_context = (
        _executable_candidate(tmp_path, workspace_log=workspace_log)
    )
    dirty = replace(clean, solver_material_refs=("missing.txt",))

    accepted = certify_task_candidate(
        clean,
        CertificationConfig(repeat_count=2),
        workspace_config,
        runtime_config,
        reference_patch,
        run_context,
    )
    rejected = certify_task_candidate(
        dirty,
        CertificationConfig(),
        workspace_config,
        runtime_config,
        reference_patch,
        run_context,
    )

    assert accepted.accepted
    assert accepted.task is not None
    assert accepted.check is not None
    assert [item["outcome"] for item in accepted.evidence["base_check"]] == [
        "fail",
        "fail",
    ]
    assert [item["outcome"] for item in accepted.evidence["reference_patch_check"]] == [
        "pass",
        "pass",
    ]
    assert accepted.evidence["workspace_config_digest"] == canonical_digest(
        workspace_config
    )
    assert accepted.evidence["runtime_config_digest"] == canonical_digest(
        runtime_config
    )
    assert accepted.evidence["check_execution_binding_digest"] == (
        check_execution_binding_digest(accepted.check, run_context)
    )
    assert (
        accepted.evidence["verification_adapter_digest"] == VERIFICATION_ADAPTER_DIGEST
    )
    checked_workspaces = tuple(
        Path(value) for value in workspace_log.read_text(encoding="utf-8").splitlines()
    )
    assert len(checked_workspaces) == 4
    assert len(set(checked_workspaces)) == 4
    assert not any(path.exists() for path in checked_workspaces)
    assert not rejected.accepted
    assert any(
        "invalid_solver_material" in reason for reason in rejected.rejection_reasons
    )


def test_certification_repeats_base_and_quarantines_a_flaky_transition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate, workspace_config, runtime_config, reference_patch, run_context = (
        _executable_candidate(tmp_path)
    )
    outcomes = iter(
        (
            CheckOutcome("fail", "check_failed", 1, False, 0.1, ""),
            CheckOutcome("pass", None, 0, False, 0.1, ""),
            CheckOutcome("pass", None, 0, False, 0.1, ""),
        )
    )
    monkeypatch.setattr(
        task_pool_module,
        "_run_task_check",
        lambda *args, **kwargs: next(outcomes),
    )

    result = certify_task_candidate(
        candidate,
        CertificationConfig(repeat_count=2),
        workspace_config,
        runtime_config,
        reference_patch,
        run_context,
    )

    assert not result.accepted
    assert tuple(item["outcome"] for item in result.evidence["base_check"]) == (
        "fail",
        "pass",
    )
    assert tuple(
        item["outcome"] for item in result.evidence["reference_patch_check"]
    ) == ("pass",)
    assert any(
        reason.startswith("base check attempt 2 must fail; observed pass")
        for reason in result.rejection_reasons
    )


def test_certify_task_candidate_rejects_check_that_passes_at_base(
    tmp_path: Path,
) -> None:
    candidate, workspace_config, runtime_config, reference_patch, run_context = (
        _executable_candidate(tmp_path, expected_content="broken\n")
    )

    result = certify_task_candidate(
        candidate,
        CertificationConfig(),
        workspace_config,
        runtime_config,
        reference_patch,
        run_context,
    )

    assert not result.accepted
    assert "base check attempt 1 must fail; observed pass" in result.rejection_reasons
    assert result.task is None
    assert result.check is None


def test_certify_task_candidate_rejects_reference_patch_that_does_not_pass(
    tmp_path: Path,
) -> None:
    candidate, workspace_config, runtime_config, _, run_context = _executable_candidate(
        tmp_path
    )
    patch_text = (
        "diff --git a/value.txt b/value.txt\n"
        "--- a/value.txt\n"
        "+++ b/value.txt\n"
        "@@ -1 +1 @@\n"
        "-broken\n"
        "+still-broken\n"
    )
    reference_patch = CapturedDiff(
        patch_text, hashlib.sha256(patch_text.encode("utf-8")).hexdigest()
    )

    result = certify_task_candidate(
        candidate,
        CertificationConfig(),
        workspace_config,
        runtime_config,
        reference_patch,
        run_context,
    )

    assert not result.accepted
    assert any(
        reason.startswith("reference patch check attempt 1 must pass; observed fail")
        for reason in result.rejection_reasons
    )
    assert result.evidence["base_check"][0]["outcome"] == "fail"
    assert result.evidence["reference_patch_check"][0]["outcome"] == "fail"


def test_certify_task_candidate_rejects_empty_task_text(tmp_path: Path) -> None:
    executable, workspace_config, runtime_config, reference_patch, run_context = (
        _executable_candidate(tmp_path)
    )
    candidate = replace(executable, task_text="")

    result = certify_task_candidate(
        candidate,
        CertificationConfig(),
        workspace_config,
        runtime_config,
        reference_patch,
        run_context,
    )

    assert not result.accepted
    assert "task_text must not be empty" in result.rejection_reasons


def test_certify_task_candidate_reports_missing_repository_binding(
    tmp_path: Path,
) -> None:
    candidate, workspace_config, runtime_config, reference_patch, _ = (
        _executable_candidate(tmp_path)
    )

    with pytest.raises(RuntimeError, match="missing_repository_source"):
        certify_task_candidate(
            candidate,
            CertificationConfig(),
            workspace_config,
            runtime_config,
            reference_patch,
            WorkspaceRunContext(),
        )


@pytest.mark.parametrize(
    "failure_label",
    (
        "verifier_workspace_error",
        "verification_error",
        "diff_replay_launch_error",
        "missing_git_checkout",
        "check_launch_error",
        "check_invalid",
    ),
)
def test_certify_task_candidate_stops_on_validation_infrastructure_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_label: str,
) -> None:
    candidate, workspace_config, runtime_config, reference_patch, run_context = (
        _executable_candidate(tmp_path)
    )
    monkeypatch.setattr(
        task_pool_module,
        "_run_task_check",
        lambda *args, **kwargs: CheckOutcome(
            "invalid", failure_label, None, False, 0.0, ""
        ),
    )

    with pytest.raises(RuntimeError, match=failure_label):
        certify_task_candidate(
            candidate,
            CertificationConfig(),
            workspace_config,
            runtime_config,
            reference_patch,
            run_context,
        )


@pytest.mark.parametrize(
    "boundary",
    ("evidence_serialization", "source_event_finalization", "task_pool_freeze"),
)
def test_certification_decision_requires_exact_boolean_at_public_boundaries(
    accepted_result: CertificationResult,
    boundary: str,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None
    malformed = replace(accepted, accepted=1)  # type: ignore[arg-type]

    with pytest.raises(
        ValueError,
        match="certification result accepted must be a boolean",
    ):
        if boundary == "evidence_serialization":
            task_pool_module.certification_evidence_records((malformed,))
            return
        if boundary == "source_event_finalization":
            batch = filter_history_candidates(
                "repo",
                TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
                TaskSourceConfig(
                    source_family="issue",
                    source_events=(
                        _candidate_payload(candidate_id=accepted.candidate_id),
                    ),
                ),
            )
            task_pool_module.finalize_source_event_records(batch, (malformed,))
            return
        freeze_task_pool(
            (accepted.task,),
            (accepted.check,),
            (malformed,),
            _accepted_source_events(accepted),
            {
                "repository_id": "repo",
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "certification_evidence_ref": "certification-evidence.jsonl",
                "source_event_records_ref": "source-events.jsonl",
                "generator_config_digest": "generator",
                "certification_config_digest": canonical_digest(CertificationConfig()),
                "created_at": "2026-01-31T00:00:00Z",
            },
        )


def test_freeze_task_pool_records_digests_rejections_and_summary(
    accepted_result: CertificationResult,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None

    task_pool = freeze_task_pool(
        [accepted.task],
        [accepted.check],
        (accepted,),
        _accepted_source_events(accepted),
        {
            "repository_id": "repo",
            "task_records_ref": "tasks.jsonl",
            "check_records_ref": "checks.jsonl",
            "certification_evidence_ref": "certification-evidence.jsonl",
            "source_event_records_ref": "source-events.jsonl",
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


@pytest.mark.parametrize(
    ("field", "message"),
    (
        ("repository_id", "metadata fields must be strings: repository_id"),
        ("task_records_ref", "metadata fields must be strings: task_records_ref"),
        ("check_records_ref", "metadata fields must be strings: check_records_ref"),
        (
            "certification_evidence_ref",
            "metadata fields must be strings: certification_evidence_ref",
        ),
        (
            "source_event_records_ref",
            "metadata fields must be strings: source_event_records_ref",
        ),
        (
            "generator_config_digest",
            "metadata fields must be strings: generator_config_digest",
        ),
        (
            "certification_config_digest",
            "metadata fields must be strings: certification_config_digest",
        ),
        ("created_at", "metadata fields must be strings: created_at"),
        ("task_pool_id", "task_pool_id must be a string"),
    ),
)
def test_freeze_task_pool_rejects_nonstring_metadata(
    accepted_result: CertificationResult,
    field: str,
    message: str,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None
    metadata: dict[str, object] = {
        "repository_id": "repo",
        "task_records_ref": "tasks.jsonl",
        "check_records_ref": "checks.jsonl",
        "certification_evidence_ref": "certification-evidence.jsonl",
        "source_event_records_ref": "source-events.jsonl",
        "generator_config_digest": "generator",
        "certification_config_digest": canonical_digest(CertificationConfig()),
        "created_at": "2026-01-31T00:00:00Z",
    }
    metadata[field] = 7

    with pytest.raises(ValueError, match=message):
        freeze_task_pool(
            (accepted.task,),
            (accepted.check,),
            (accepted,),
            _accepted_source_events(accepted),
            metadata,
        )


def test_freeze_task_pool_rejects_accepted_event_outside_source_window(
    accepted_result: CertificationResult,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None

    with pytest.raises(
        ValueError, match="accepted source event is outside source window"
    ):
        freeze_task_pool(
            (accepted.task,),
            (accepted.check,),
            (accepted,),
            _accepted_source_events(accepted),
            {
                "repository_id": "repo",
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "certification_evidence_ref": "certification-evidence.jsonl",
                "source_event_records_ref": "source-events.jsonl",
                "generator_config_digest": "generator",
                "certification_config_digest": canonical_digest(CertificationConfig()),
                "created_at": "2026-02-03T00:00:00Z",
                "source_window_start": "2026-02-01T00:00:00Z",
                "source_window_end": "2026-02-02T00:00:00Z",
            },
        )


def test_freeze_task_pool_rejects_source_window_after_observation(
    accepted_result: CertificationResult,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None

    with pytest.raises(ValueError, match="source window ends after created_at"):
        freeze_task_pool(
            (accepted.task,),
            (accepted.check,),
            (accepted,),
            _accepted_source_events(accepted),
            {
                "repository_id": "repo",
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "certification_evidence_ref": "certification-evidence.jsonl",
                "source_event_records_ref": "source-events.jsonl",
                "generator_config_digest": "generator",
                "certification_config_digest": canonical_digest(CertificationConfig()),
                "created_at": "2026-01-31T00:00:00Z",
                "source_window_start": "2026-01-01T00:00:00Z",
                "source_window_end": "2026-02-01T00:00:00Z",
            },
        )


def test_source_window_error_contract_preserves_boundary_and_event_order(
    accepted_result: CertificationResult,
) -> None:
    task_pool, _, _, _ = _accepted_evidence_fixture(accepted_result)
    (event,) = _accepted_source_events(accepted_result)
    valid_pool = replace(
        task_pool,
        source_window_start="2026-01-01T00:00:00.000000Z",
        source_window_end="2026-01-20T00:00:00.000000Z",
    )

    assert task_pool_module._source_window_errors(task_pool, (event,)) == ()
    assert task_pool_module._source_window_errors(valid_pool, (event,)) == ()
    assert task_pool_module._source_window_errors(
        replace(valid_pool, source_window_end=None),
        (event,),
    ) == ("Task Pool source window requires string start and end",)
    assert task_pool_module._source_window_errors(
        replace(valid_pool, source_window_start="not-a-time"),
        (event,),
    ) == ("Task Pool source window timestamps are invalid",)
    assert task_pool_module._source_window_errors(
        replace(valid_pool, source_window_start="2026-01-01T00:00:00Z"),
        (event,),
    ) == ("Task Pool source window timestamps are not canonical UTC",)
    assert task_pool_module._source_window_errors(
        replace(
            valid_pool,
            source_window_start="2026-01-21T00:00:00.000000Z",
        ),
        (event,),
    ) == ("Task Pool source window start is after end",)
    assert task_pool_module._source_window_errors(
        replace(
            valid_pool,
            source_window_end="2026-02-01T00:00:00.000000Z",
        ),
        (event,),
    ) == ("Task Pool source window ends after created_at",)

    outside = replace(event, source_resolved_at="2025-12-31T00:00:00Z")
    assert task_pool_module._source_window_errors(valid_pool, (outside,)) == (
        "accepted source event is outside source window",
        f"source event {event.source_event_id} outside source window lacks exclusion reason",
    )
    excluded_outside = replace(
        outside,
        disposition="excluded",
        rejection_reasons=("outside_source_time_range",),
    )
    assert task_pool_module._source_window_errors(valid_pool, (excluded_outside,)) == ()
    marked_inside = replace(
        event,
        rejection_reasons=("outside_source_time_range",),
    )
    assert task_pool_module._source_window_errors(valid_pool, (marked_inside,)) == (
        f"source event {event.source_event_id} inside source window has outside-range reason",
    )


def test_certification_result_ingestion_characterizes_frozen_pairs(
    accepted_result: CertificationResult,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None

    assert task_pool_module._validated_certification_results(
        (accepted.task,),
        (accepted.check,),
        (accepted,),
    ) == (accepted,)

    duplicate_pair = replace(accepted, candidate_id="other-candidate")
    with pytest.raises(ValueError, match="duplicate Task/Check evidence"):
        task_pool_module._validated_certification_results(
            (accepted.task,),
            (accepted.check,),
            (accepted, duplicate_pair),
        )

    drifted_task = replace(accepted.task, sampling_stratum="different-stratum")
    drifted_result = replace(accepted, task=drifted_task)
    with pytest.raises(ValueError, match="task digest does not match frozen task"):
        task_pool_module._validated_certification_results(
            (accepted.task,),
            (accepted.check,),
            (drifted_result,),
        )


@pytest.mark.parametrize("location", ("record", "attempt"))
def test_task_pool_validation_rejects_unknown_certification_evidence_keys(
    accepted_result: CertificationResult,
    location: str,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None
    source_events = _accepted_source_events(accepted)
    task_pool = freeze_task_pool(
        (accepted.task,),
        (accepted.check,),
        (accepted,),
        source_events,
        {
            "repository_id": "repo",
            "task_records_ref": "tasks.jsonl",
            "check_records_ref": "checks.jsonl",
            "certification_evidence_ref": "certification-evidence.jsonl",
            "source_event_records_ref": "source-events.jsonl",
            "generator_config_digest": "generator",
            "certification_config_digest": canonical_digest(CertificationConfig()),
            "created_at": "2026-01-31T00:00:00Z",
        },
    )
    evidence = dict(task_pool_module.certification_evidence_records((accepted,))[0])
    if location == "record":
        evidence["legacy_field"] = "legacy"
        expected = "certification evidence record 0 has unknown keys: legacy_field"
    else:
        attempts = list(evidence["base_check"])
        attempts[0] = {**attempts[0], "legacy_field": "legacy"}
        evidence["base_check"] = tuple(attempts)
        expected = (
            "certification evidence record 0 base_check attempt 0 has unknown keys: "
            "legacy_field"
        )
    evidence_records = (evidence,)
    task_pool = record_with_digest(
        replace(
            task_pool,
            certification_evidence_digest=canonical_digest(evidence_records),
            task_pool_digest="",
        )
    )

    validation = task_pool_module.validate_task_pool_artifacts(
        task_pool,
        (accepted.task,),
        (accepted.check,),
        evidence_records,
        source_events,
    )

    assert expected in validation.errors


def test_task_pool_validation_returns_errors_for_non_object_certification_evidence(
    accepted_result: CertificationResult,
) -> None:
    task_pool, tasks, checks, _ = _accepted_evidence_fixture(accepted_result)
    malformed_evidence = (7,)
    task_pool = record_with_digest(
        replace(
            task_pool,
            certification_evidence_digest=canonical_digest(malformed_evidence),
            task_pool_digest="",
        )
    )

    validation = task_pool_module.validate_task_pool_artifacts(
        task_pool,
        tasks,
        checks,
        malformed_evidence,  # type: ignore[arg-type]
        _accepted_source_events(accepted_result),
    )

    assert "certification evidence record 0 must be an object" in validation.errors


@pytest.mark.parametrize(
    ("case", "expected_error"),
    (
        (
            "accepted_reasons",
            "accepted certification evidence must not have rejection reasons",
        ),
        ("base_outcome", "accepted certification base checks must fail"),
        (
            "reference_outcome",
            "accepted certification reference patch checks must pass",
        ),
        (
            "reference_timed_out",
            "timed_out attempts must have invalid outcome",
        ),
        (
            "reference_failure_label",
            "passing attempts must not have a failure_label",
        ),
        (
            "base_missing_failure_label",
            "non-passing attempts must have a non-empty failure_label",
        ),
        (
            "repeat_count",
            "accepted certification base checks must match repeat_count",
        ),
        (
            "adapter",
            "verification_adapter_digest is not supported",
        ),
        (
            "task_digest",
            "certification evidence does not exactly cover accepted Task/Check records",
        ),
    ),
)
def test_certification_evidence_validation_characterizes_accepted_contract(
    accepted_result: CertificationResult,
    case: str,
    expected_error: str,
) -> None:
    task_pool, tasks, checks, record = _accepted_evidence_fixture(accepted_result)
    if case == "accepted_reasons":
        record["rejection_reasons"] = ("unexpected reason",)
    elif case == "base_outcome":
        attempts = [dict(attempt) for attempt in record["base_check"]]
        attempts[0]["outcome"] = "pass"
        record["base_check"] = tuple(attempts)
    elif case == "reference_outcome":
        attempts = [dict(attempt) for attempt in record["reference_patch_check"]]
        attempts[0]["outcome"] = "fail"
        record["reference_patch_check"] = tuple(attempts)
    elif case == "reference_timed_out":
        attempts = [dict(attempt) for attempt in record["reference_patch_check"]]
        attempts[0]["timed_out"] = True
        record["reference_patch_check"] = tuple(attempts)
    elif case == "reference_failure_label":
        attempts = [dict(attempt) for attempt in record["reference_patch_check"]]
        attempts[0]["failure_label"] = "timeout"
        record["reference_patch_check"] = tuple(attempts)
    elif case == "base_missing_failure_label":
        attempts = [dict(attempt) for attempt in record["base_check"]]
        attempts[0]["failure_label"] = None
        record["base_check"] = tuple(attempts)
    elif case == "repeat_count":
        record["repeat_count"] = 2
        task_pool = replace(
            task_pool,
            certification_config_digest=canonical_digest(
                CertificationConfig(repeat_count=2)
            ),
        )
    elif case == "adapter":
        record["verification_adapter_digest"] = "unsupported-adapter"
    elif case == "task_digest":
        record["task_digest"] = "different-task"
    else:  # pragma: no cover - parameter list is closed above
        raise AssertionError(f"unsupported test case: {case}")

    errors = task_pool_module._certification_evidence_errors(
        task_pool,
        tasks,
        checks,
        (record,),
    )

    assert any(expected_error in error for error in errors)


@pytest.mark.parametrize(
    ("case", "expected_errors"),
    (
        ("malformed_record", ("is missing:",)),
        ("non_boolean_accepted", ("accepted must be boolean",)),
        (
            "duplicate_accepted",
            (
                "certification evidence contains duplicate candidate_id values",
                "certification evidence contains duplicate accepted Task/Check records",
            ),
        ),
        (
            "config_digest_mismatch",
            (
                "certification evidence repeat_count does not match "
                "certification_config_digest",
            ),
        ),
    ),
)
def test_certification_evidence_validation_characterizes_record_set_contract(
    accepted_result: CertificationResult,
    case: str,
    expected_errors: tuple[str, ...],
) -> None:
    task_pool, tasks, checks, record = _accepted_evidence_fixture(accepted_result)
    assert (
        task_pool_module._certification_evidence_errors(
            task_pool,
            tasks,
            checks,
            (record,),
        )
        == ()
    )

    if case == "malformed_record":
        evidence = ({},)
    elif case == "non_boolean_accepted":
        record["accepted"] = "yes"
        evidence = (record,)
    elif case == "duplicate_accepted":
        evidence = (record, dict(record))
    elif case == "config_digest_mismatch":
        record["repeat_count"] = 2
        evidence = (record,)
    else:  # pragma: no cover - parameter list is closed above
        raise AssertionError(f"unsupported test case: {case}")

    errors = task_pool_module._certification_evidence_errors(
        task_pool,
        tasks,
        checks,
        evidence,
    )

    assert all(
        any(expected_error in error for error in errors)
        for expected_error in expected_errors
    )


def test_certification_evidence_validation_characterizes_rejected_contract(
    accepted_result: CertificationResult,
) -> None:
    task_pool, tasks, checks, accepted_record = _accepted_evidence_fixture(
        accepted_result
    )
    rejection_reason = "base check attempt 1 expected fail but observed pass"
    rejected_record = {
        **accepted_record,
        "candidate_id": "candidate-rejected",
        "accepted": False,
        "rejection_reasons": (rejection_reason,),
    }
    task_pool = replace(
        task_pool,
        rejected_candidate_ids=("candidate-rejected",),
        rejection_summary_digest=canonical_digest(
            {"rejected_count": 1, "reasons": {rejection_reason: 1}}
        ),
    )
    evidence = tuple(
        sorted(
            (accepted_record, rejected_record),
            key=lambda record: str(record["candidate_id"]),
        )
    )

    errors = task_pool_module._certification_evidence_errors(
        task_pool,
        tasks,
        checks,
        evidence,
    )

    assert errors == ()
    ordering_errors = task_pool_module._certification_evidence_errors(
        task_pool,
        tasks,
        checks,
        tuple(reversed(evidence)),
    )
    assert (
        "certification evidence records must be ordered by candidate_id"
        in ordering_errors
    )
    for field in ("workspace_config_digest", "runtime_config_digest"):
        mixed_context = tuple(
            {**record, field: f"different-{field}"}
            if record["candidate_id"] == "candidate-rejected"
            else record
            for record in evidence
        )
        context_errors = task_pool_module._certification_evidence_errors(
            task_pool,
            tasks,
            checks,
            mixed_context,
        )
        assert (
            f"certification evidence contains multiple {field} values" in context_errors
        )
    rejected_record["rejection_reasons"] = ()
    errors = task_pool_module._certification_evidence_errors(
        task_pool,
        tasks,
        checks,
        (accepted_record, rejected_record),
    )
    assert "rejected certification evidence must include rejection reasons" in errors


def test_source_event_validation_characterizes_cross_record_contract(
    accepted_result: CertificationResult,
) -> None:
    task_pool, tasks, checks, accepted_evidence = _accepted_evidence_fixture(
        accepted_result
    )
    source_events = _accepted_source_events(accepted_result)
    assert (
        task_pool_module._source_event_errors(
            task_pool,
            tasks,
            checks,
            (accepted_evidence,),
            source_events,
        )
        == ()
    )

    event = source_events[0]
    wrong_repository = record_with_digest(
        replace(
            event,
            repository_id="other-repository",
            source_event_id=make_source_event_id(
                "other-repository",
                event.source_family,
                event.source_ref,
            ),
            source_event_digest="",
        )
    )
    repository_errors = task_pool_module._source_event_errors(
        task_pool,
        tasks,
        checks,
        (accepted_evidence,),
        (wrong_repository,),
    )
    assert any(
        "repository_id does not match Task Pool" in error for error in repository_errors
    )

    future_timestamp = replace(event, source_resolved_at="2030-01-01T00:00:00Z")
    timestamp_errors = task_pool_module._source_event_errors(
        task_pool,
        tasks,
        checks,
        (accepted_evidence,),
        (future_timestamp,),
    )
    assert any(
        "source_resolved_at is after Task Pool created_at" in error
        for error in timestamp_errors
    )

    missing_evidence_errors = task_pool_module._source_event_errors(
        task_pool,
        tasks,
        checks,
        (),
        source_events,
    )
    assert any(
        "references missing certification evidence" in error
        for error in missing_evidence_errors
    )

    material_drift = record_with_digest(
        replace(event, sampling_stratum="changed-stratum", source_event_digest="")
    )
    material_errors = task_pool_module._source_event_errors(
        task_pool,
        tasks,
        checks,
        (accepted_evidence,),
        (material_drift,),
    )
    assert (
        "accepted source event does not match frozen Task/Check material"
        in material_errors
    )

    rejection_reason = "base check did not fail"
    rejected_candidate_id = "candidate-rejected"
    rejected_evidence = {
        **accepted_evidence,
        "candidate_id": rejected_candidate_id,
        "accepted": False,
        "rejection_reasons": (rejection_reason,),
    }
    rejected_ref = "source-rejected"
    rejected_event = record_with_digest(
        replace(
            event,
            source_event_id=make_source_event_id(
                event.repository_id,
                event.source_family,
                rejected_ref,
            ),
            source_ref=rejected_ref,
            candidate_id=rejected_candidate_id,
            task_id=None,
            check_id=None,
            disposition="certification_rejected",
            rejection_stage="certification",
            rejection_reasons=("different reason",),
            source_event_digest="",
        )
    )
    rejected_pool = replace(
        task_pool,
        rejected_candidate_ids=(rejected_candidate_id,),
    )
    rejection_errors = task_pool_module._source_event_errors(
        rejected_pool,
        tasks,
        checks,
        (accepted_evidence, rejected_evidence),
        tuple(
            sorted(
                (*source_events, rejected_event), key=lambda item: item.source_event_id
            )
        ),
    )
    assert (
        "source event rejection reasons do not match certification evidence"
        in rejection_errors
    )

    extra_evidence = {
        **accepted_evidence,
        "candidate_id": "unrepresented-candidate",
    }
    coverage_errors = task_pool_module._source_event_errors(
        task_pool,
        tasks,
        checks,
        (accepted_evidence, extra_evidence),
        source_events,
    )
    assert (
        "source event records must exactly cover certification candidates"
        in coverage_errors
    )


def test_task_pool_validation_rejects_duplicate_source_event_candidate_ids(
    accepted_result: CertificationResult,
) -> None:
    task_pool, tasks, checks, accepted_evidence = _accepted_evidence_fixture(
        accepted_result
    )
    (accepted_event,) = _accepted_source_events(accepted_result)
    candidate_id = "candidate-rejected"
    rejection_reason = "base check did not fail"
    rejected_evidence = {
        **accepted_evidence,
        "candidate_id": candidate_id,
        "accepted": False,
        "rejection_reasons": (rejection_reason,),
    }

    def rejected_event(source_ref: str) -> SourceEventRecord:
        return record_with_digest(
            replace(
                accepted_event,
                source_event_id=make_source_event_id(
                    accepted_event.repository_id,
                    accepted_event.source_family,
                    source_ref,
                ),
                source_ref=source_ref,
                candidate_id=candidate_id,
                task_id=None,
                check_id=None,
                disposition="certification_rejected",
                rejection_stage="certification",
                rejection_reasons=(rejection_reason,),
                source_event_digest="",
            )
        )

    evidence = tuple(
        sorted(
            (accepted_evidence, rejected_evidence),
            key=lambda record: str(record["candidate_id"]),
        )
    )
    source_events = tuple(
        sorted(
            (
                accepted_event,
                rejected_event("source-rejected-a"),
                rejected_event("source-rejected-b"),
            ),
            key=lambda event: event.source_event_id,
        )
    )
    task_pool = record_with_digest(
        replace(
            task_pool,
            rejected_candidate_ids=(candidate_id,),
            rejection_summary_digest=canonical_digest(
                {"rejected_count": 1, "reasons": {rejection_reason: 1}}
            ),
            certification_evidence_digest=canonical_digest(evidence),
            source_event_records_digest=canonical_digest(source_events),
            task_pool_digest="",
        )
    )

    validation = task_pool_module.validate_task_pool_artifacts(
        task_pool,
        tasks,
        checks,
        evidence,
        source_events,
    )

    assert not validation.ok
    assert (
        "source event records contain duplicate candidate_id values"
        in validation.errors
    )


def test_task_pool_validation_rejects_scalar_evidence_reasons_without_raising(
    accepted_result: CertificationResult,
) -> None:
    task_pool, tasks, checks, accepted_evidence = _accepted_evidence_fixture(
        accepted_result
    )
    accepted_evidence["rejection_reasons"] = 7
    evidence = (accepted_evidence,)
    task_pool = record_with_digest(
        replace(
            task_pool,
            certification_evidence_digest=canonical_digest(evidence),
            task_pool_digest="",
        )
    )

    validation = task_pool_module.validate_task_pool_artifacts(
        task_pool,
        tasks,
        checks,
        evidence,
        _accepted_source_events(accepted_result),
    )

    assert not validation.ok
    assert any(
        "rejection_reasons must be a sequence of non-empty strings" in error
        for error in validation.errors
    )


def test_load_validated_task_pool_bundle_rejects_member_drift(
    tmp_path: Path,
    accepted_result: CertificationResult,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None
    evidence = task_pool_module.certification_evidence_records((accepted,))
    task_pool = freeze_task_pool(
        (accepted.task,),
        (accepted.check,),
        (accepted,),
        _accepted_source_events(accepted),
        {
            "repository_id": "repo",
            "task_records_ref": "bundle/tasks.jsonl",
            "check_records_ref": "bundle/checks.jsonl",
            "certification_evidence_ref": "bundle/certification-evidence.jsonl",
            "source_event_records_ref": "bundle/source-events.jsonl",
            "generator_config_digest": "generator",
            "certification_config_digest": canonical_digest(CertificationConfig()),
            "created_at": "2026-01-31T00:00:00Z",
        },
    )
    write_jsonl_records(tmp_path / task_pool.task_records_ref, (accepted.task,))
    write_jsonl_records(tmp_path / task_pool.check_records_ref, (accepted.check,))
    write_jsonl_records(tmp_path / task_pool.certification_evidence_ref, evidence)
    write_jsonl_records(
        tmp_path / task_pool.source_event_records_ref,
        _accepted_source_events(accepted),
    )

    bundle = load_validated_task_pool_bundle(task_pool, tmp_path)

    assert bundle.task_pool == task_pool
    assert bundle.tasks == (accepted.task,)
    assert bundle.checks_by_id == {accepted.check.check_id: accepted.check}

    drifted_task = replace(accepted.task, source_ref="changed-with-same-task-id")
    write_jsonl_records(tmp_path / task_pool.task_records_ref, (drifted_task,))

    with pytest.raises(ValueError, match="task records digest does not match"):
        load_validated_task_pool_bundle(task_pool, tmp_path)


@pytest.mark.parametrize(
    ("field", "error"),
    (
        (
            "generator_config_digest",
            "TaskPoolRecord.generator_config_digest must be a string",
        ),
        ("created_at", "TaskPoolRecord.created_at must be a string"),
        (
            "rejected_candidate_ids",
            "TaskPoolRecord.rejected_candidate_ids must be an array",
        ),
    ),
)
def test_task_pool_artifact_validation_rejects_non_reloadable_record_shape(
    accepted_result: CertificationResult,
    field: str,
    error: str,
) -> None:
    task_pool, tasks, checks, evidence = _accepted_evidence_fixture(accepted_result)
    malformed = record_with_digest(
        replace(
            task_pool,
            **{field: 7},
            task_pool_digest="",
        )
    )

    validation = task_pool_module.validate_task_pool_artifacts(
        malformed,
        tasks,
        checks,
        (evidence,),
        _accepted_source_events(accepted_result),
    )

    assert error in validation.errors


def test_task_pool_artifact_validation_rejects_non_reloadable_member_shape(
    accepted_result: CertificationResult,
) -> None:
    task_pool, tasks, checks, evidence = _accepted_evidence_fixture(accepted_result)
    malformed_tasks = (
        replace(tasks[0], check_ids=7),  # type: ignore[arg-type]
    )

    validation = task_pool_module.validate_task_pool_artifacts(
        task_pool,
        malformed_tasks,
        checks,
        (evidence,),
        _accepted_source_events(accepted_result),
    )

    assert "TaskRecord.check_ids must be an array" in validation.errors[0]


def test_load_validated_task_pool_bundle_rejects_task_pool_digest_drift(
    tmp_path: Path,
    accepted_result: CertificationResult,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None
    evidence = task_pool_module.certification_evidence_records((accepted,))
    task_pool = freeze_task_pool(
        (accepted.task,),
        (accepted.check,),
        (accepted,),
        _accepted_source_events(accepted),
        {
            "repository_id": "repo",
            "task_records_ref": "bundle/tasks.jsonl",
            "check_records_ref": "bundle/checks.jsonl",
            "certification_evidence_ref": "bundle/certification-evidence.jsonl",
            "source_event_records_ref": "bundle/source-events.jsonl",
            "generator_config_digest": "generator",
            "certification_config_digest": canonical_digest(CertificationConfig()),
            "created_at": "2026-01-31T00:00:00Z",
        },
    )
    write_jsonl_records(tmp_path / task_pool.task_records_ref, (accepted.task,))
    write_jsonl_records(tmp_path / task_pool.check_records_ref, (accepted.check,))
    write_jsonl_records(tmp_path / task_pool.certification_evidence_ref, evidence)
    write_jsonl_records(
        tmp_path / task_pool.source_event_records_ref,
        _accepted_source_events(accepted),
    )
    drifted_pool = replace(task_pool, generator_config_digest="changed")

    with pytest.raises(ValueError, match="task_pool_digest does not match"):
        load_validated_task_pool_bundle(drifted_pool, tmp_path)


def test_load_validated_task_pool_bundle_rejects_source_event_drift(
    tmp_path: Path,
    accepted_result: CertificationResult,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None
    evidence = task_pool_module.certification_evidence_records((accepted,))
    source_events = _accepted_source_events(accepted)
    task_pool = freeze_task_pool(
        (accepted.task,),
        (accepted.check,),
        (accepted,),
        source_events,
        {
            "repository_id": "repo",
            "task_records_ref": "bundle/tasks.jsonl",
            "check_records_ref": "bundle/checks.jsonl",
            "certification_evidence_ref": "bundle/certification-evidence.jsonl",
            "source_event_records_ref": "bundle/source-events.jsonl",
            "generator_config_digest": "generator",
            "certification_config_digest": canonical_digest(CertificationConfig()),
            "created_at": "2026-01-31T00:00:00Z",
        },
    )
    write_jsonl_records(tmp_path / task_pool.task_records_ref, (accepted.task,))
    write_jsonl_records(tmp_path / task_pool.check_records_ref, (accepted.check,))
    write_jsonl_records(tmp_path / task_pool.certification_evidence_ref, evidence)
    write_jsonl_records(
        tmp_path / task_pool.source_event_records_ref,
        (
            record_with_digest(
                replace(
                    source_events[0],
                    dependency_cluster_id="changed",
                    source_event_digest="",
                )
            ),
        ),
    )

    with pytest.raises(ValueError, match="source event records digest does not match"):
        load_validated_task_pool_bundle(task_pool, tmp_path)


def test_publish_task_pool_bundle_is_immutable_and_failure_atomic(
    tmp_path: Path,
    accepted_result: CertificationResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _published_bundle_fixture(
        accepted_result,
        bundle_key="first",
        created_at="2026-01-31T00:00:00Z",
    )
    target = task_pool_module.publish_task_pool_bundle(first, tmp_path)
    manifest_before = (target / "task-pool.jsonl").read_bytes()

    conflicting = _published_bundle_fixture(
        accepted_result,
        bundle_key="first",
        created_at="2026-02-01T00:00:00Z",
    )
    with pytest.raises(ValueError, match="different manifest"):
        task_pool_module.publish_task_pool_bundle(conflicting, tmp_path)

    assert (target / "task-pool.jsonl").read_bytes() == manifest_before
    assert load_validated_task_pool_bundle(first.task_pool, tmp_path) == first

    second = _published_bundle_fixture(
        accepted_result,
        bundle_key="second",
        created_at="2026-02-02T00:00:00Z",
    )
    original_write = task_pool_module.write_jsonl_records

    def fail_during_publish(path, records):
        if path.name == "checks.jsonl":
            raise OSError("injected publish failure")
        return original_write(path, records)

    monkeypatch.setattr(task_pool_module, "write_jsonl_records", fail_during_publish)

    with pytest.raises(OSError, match="injected publish failure"):
        task_pool_module.publish_task_pool_bundle(second, tmp_path)

    assert not (tmp_path / "task-pools" / "second").exists()
    assert load_validated_task_pool_bundle(first.task_pool, tmp_path) == first


def test_publish_task_pool_bundle_fsyncs_members_and_publication_directory(
    tmp_path: Path,
    accepted_result: CertificationResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _published_bundle_fixture(
        accepted_result,
        bundle_key="durable",
        created_at="2026-02-03T00:00:00Z",
    )
    file_calls: list[Path] = []
    directory_calls: list[Path] = []
    original_fsync_file = task_pool_module._fsync_file
    original_fsync_directory = task_pool_module._fsync_directory

    def track_file(path: Path) -> None:
        file_calls.append(path)
        original_fsync_file(path)

    def track_directory(path: Path) -> None:
        directory_calls.append(path)
        original_fsync_directory(path)

    monkeypatch.setattr(task_pool_module, "_fsync_file", track_file)
    monkeypatch.setattr(task_pool_module, "_fsync_directory", track_directory)

    target = task_pool_module.publish_task_pool_bundle(bundle, tmp_path)

    assert {path.name for path in file_calls} == {
        "task-pool.jsonl",
        "tasks.jsonl",
        "checks.jsonl",
        "certification-evidence.jsonl",
        "source-events.jsonl",
    }
    assert len({path.parent for path in file_calls}) == 1
    assert directory_calls[0] == file_calls[0].parent
    assert directory_calls[-1] == target.parent
    assert load_validated_task_pool_bundle(bundle.task_pool, tmp_path) == bundle


def test_freeze_task_pool_rejects_broken_task_check_linkage(
    accepted_result: CertificationResult,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None

    with pytest.raises(ValueError, match="references missing checks"):
        freeze_task_pool(
            [accepted.task],
            [],
            (accepted,),
            _accepted_source_events(accepted),
            {
                "repository_id": "repo",
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "certification_evidence_ref": "certification-evidence.jsonl",
                "source_event_records_ref": "source-events.jsonl",
                "generator_config_digest": "generator",
                "certification_config_digest": canonical_digest(CertificationConfig()),
                "created_at": "2026-01-31T00:00:00Z",
            },
        )


def test_freeze_task_pool_rejects_missing_required_metadata(
    accepted_result: CertificationResult,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None

    with pytest.raises(ValueError, match="metadata is missing required fields"):
        freeze_task_pool(
            [accepted.task],
            [accepted.check],
            (accepted,),
            _accepted_source_events(accepted),
            {
                "repository_id": "repo",
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "certification_evidence_ref": "certification-evidence.jsonl",
                "created_at": "2026-01-31T00:00:00Z",
            },
        )


def test_freeze_task_pool_rejects_missing_accepted_certification_result(
    accepted_result: CertificationResult,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None

    with pytest.raises(
        ValueError,
        match="accepted certification results must exactly cover",
    ):
        freeze_task_pool(
            [accepted.task],
            [accepted.check],
            (),
            _accepted_source_events(accepted),
            {
                "repository_id": "repo",
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "certification_evidence_ref": "certification-evidence.jsonl",
                "source_event_records_ref": "source-events.jsonl",
                "generator_config_digest": "generator",
                "certification_config_digest": canonical_digest(CertificationConfig()),
                "created_at": "2026-01-31T00:00:00Z",
            },
        )


def test_freeze_task_pool_rejects_unbound_accepted_certification_result(
    accepted_result: CertificationResult,
) -> None:
    accepted = accepted_result
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
            (bad_result,),
            _accepted_source_events(accepted),
            {
                "repository_id": "repo",
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "certification_evidence_ref": "certification-evidence.jsonl",
                "source_event_records_ref": "source-events.jsonl",
                "generator_config_digest": "generator",
                "certification_config_digest": canonical_digest(CertificationConfig()),
                "created_at": "2026-01-31T00:00:00Z",
            },
        )


def test_freeze_task_pool_revalidates_solver_material_digest(
    accepted_result: CertificationResult,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None
    bad_task = type(accepted.task)(
        **{
            **accepted.task.__dict__,
            "solver_material_refs": ("other.txt",),
        }
    )

    with pytest.raises(ValueError, match="failed validation"):
        freeze_task_pool(
            [bad_task],
            [accepted.check],
            (accepted,),
            _accepted_source_events(accepted),
            {
                "repository_id": "repo",
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "certification_evidence_ref": "certification-evidence.jsonl",
                "source_event_records_ref": "source-events.jsonl",
                "generator_config_digest": "generator",
                "certification_config_digest": canonical_digest(CertificationConfig()),
                "created_at": "2026-01-31T00:00:00Z",
            },
        )


def test_freeze_task_pool_rejects_repository_mismatch(
    accepted_result: CertificationResult,
) -> None:
    accepted = accepted_result
    assert accepted.task is not None
    assert accepted.check is not None

    with pytest.raises(ValueError, match="repository_id does not match"):
        freeze_task_pool(
            [accepted.task],
            [accepted.check],
            (accepted,),
            _accepted_source_events(accepted),
            {
                "repository_id": "other-repo",
                "task_records_ref": "tasks.jsonl",
                "check_records_ref": "checks.jsonl",
                "certification_evidence_ref": "certification-evidence.jsonl",
                "source_event_records_ref": "source-events.jsonl",
                "generator_config_digest": "generator",
                "certification_config_digest": canonical_digest(CertificationConfig()),
                "created_at": "2026-01-31T00:00:00Z",
            },
        )


def _published_bundle_fixture(
    accepted: CertificationResult,
    *,
    bundle_key: str,
    created_at: str,
):
    assert accepted.task is not None
    assert accepted.check is not None
    evidence = task_pool_module.certification_evidence_records((accepted,))
    bundle_dir = Path("task-pools") / bundle_key
    task_pool = freeze_task_pool(
        (accepted.task,),
        (accepted.check,),
        (accepted,),
        _accepted_source_events(accepted),
        {
            "repository_id": "repo",
            "task_records_ref": (bundle_dir / "tasks.jsonl").as_posix(),
            "check_records_ref": (bundle_dir / "checks.jsonl").as_posix(),
            "certification_evidence_ref": (
                bundle_dir / "certification-evidence.jsonl"
            ).as_posix(),
            "source_event_records_ref": (bundle_dir / "source-events.jsonl").as_posix(),
            "generator_config_digest": "generator",
            "certification_config_digest": canonical_digest(CertificationConfig()),
            "created_at": created_at,
        },
    )
    return task_pool_module.validated_task_pool_bundle(
        task_pool,
        (accepted.task,),
        (accepted.check,),
        evidence,
        _accepted_source_events(accepted),
    )


def _accepted_evidence_fixture(
    accepted: CertificationResult,
) -> tuple[
    TaskPoolRecord,
    tuple[TaskRecord, ...],
    tuple[CheckRecord, ...],
    dict[str, Any],
]:
    assert accepted.task is not None
    assert accepted.check is not None
    tasks = (accepted.task,)
    checks = (accepted.check,)
    task_pool = freeze_task_pool(
        tasks,
        checks,
        (accepted,),
        _accepted_source_events(accepted),
        {
            "repository_id": "repo",
            "task_records_ref": "tasks.jsonl",
            "check_records_ref": "checks.jsonl",
            "certification_evidence_ref": "certification-evidence.jsonl",
            "source_event_records_ref": "source-events.jsonl",
            "generator_config_digest": "generator",
            "certification_config_digest": canonical_digest(CertificationConfig()),
            "created_at": "2026-01-31T00:00:00Z",
        },
    )
    (evidence,) = task_pool_module.certification_evidence_records((accepted,))
    return task_pool, tasks, checks, dict(evidence)


def _accepted_source_events(
    *results: CertificationResult,
) -> tuple[SourceEventRecord, ...]:
    records = []
    for result in results:
        assert result.accepted
        assert result.task is not None
        assert result.check is not None
        task = result.task
        check = result.check
        label_mature_at = format_utc_timestamp(
            max(
                parse_utc_timestamp(task.task_material_available_at),
                parse_utc_timestamp(check.check_material_available_at),
            )
        )
        records.append(
            record_with_digest(
                SourceEventRecord(
                    source_event_id=make_source_event_id(
                        task.repository_id,
                        task.source_family,
                        task.source_ref,
                    ),
                    repository_id=task.repository_id,
                    source_family=task.source_family,
                    source_ref=task.source_ref,
                    source_resolved_at=task.source_resolved_at,
                    task_material_available_at=task.task_material_available_at,
                    check_material_available_at=check.check_material_available_at,
                    label_mature_at=label_mature_at,
                    candidate_id=result.candidate_id,
                    task_id=task.task_id,
                    check_id=check.check_id,
                    disposition="accepted",
                    rejection_stage=None,
                    rejection_reasons=(),
                    dependency_cluster_id=task.dependency_cluster_id,
                    sampling_stratum=task.sampling_stratum,
                    source_event_digest="",
                )
            )
        )
    return tuple(sorted(records, key=lambda record: record.source_event_id))


def _executable_candidate(
    tmp_path: Path,
    *,
    expected_content: str = "fixed\n",
    workspace_log: Path | None = None,
) -> tuple[
    TaskCandidate,
    WorkspaceConfig,
    RuntimeConfig,
    CapturedDiff,
    WorkspaceRunContext,
]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "Tests")
    (repo / "value.txt").write_text("broken\n", encoding="utf-8")
    _git(repo, "add", "value.txt")
    _git(repo, "commit", "--quiet", "-m", "base")
    base_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()

    hidden = tmp_path / "private-check.txt"
    hidden.write_text("private check material\n", encoding="utf-8")
    log_statement = ""
    if workspace_log is not None:
        log_statement = (
            f"log_path = Path({str(workspace_log)!r}); "
            "log_path.write_text((log_path.read_text(encoding='utf-8') if log_path.exists() else '') + "
            "str(Path.cwd()) + '\\n', encoding='utf-8'); "
        )
    check_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; "
        f"{log_statement}"
        f"content_ok = Path('value.txt').read_text(encoding='utf-8') == {expected_content!r}; "
        "private_ok = Path('.barcarolle/check_bundle').read_text(encoding='utf-8') == "
        "'private check material\\n'; "
        "raise SystemExit(0 if content_ok and private_ok else 1)",
    )
    payload = _candidate_payload(
        base_commit=base_commit,
        solver_material_refs=(),
        check_manifest_digest=canonical_digest({"check_command": check_command}),
        hidden_check_bundle_digest=hidden_material_digest(hidden),
    )
    candidate = filter_history_candidates(
        "repo",
        TimeRange("2026-01-01T00:00:00Z", "2026-01-31T23:59:59Z"),
        TaskSourceConfig(source_family="issue", source_events=(payload,)),
    ).candidates[0]
    workspace_config = WorkspaceConfig(
        workspace_config_id="workspace",
        repository_checkout_config_digest=canonical_digest(
            {"repository_path": str(repo)}
        ),
        submodule_state_digest="submodules",
        base_image_digest="image",
        dependency_lock_digest="deps",
    )
    runtime_config = RuntimeConfig(
        "runtime", "budget", "retry", "deterministic", 5, None
    )
    check = build_check_candidate(candidate)
    run_context = bind_repository_source(WorkspaceRunContext(), workspace_config, repo)
    run_context = bind_check_material(run_context, check, check_command, hidden)

    patch_text = (
        "diff --git a/value.txt b/value.txt\n"
        "--- a/value.txt\n"
        "+++ b/value.txt\n"
        "@@ -1 +1 @@\n"
        "-broken\n"
        "+fixed\n"
    )
    reference_patch = CapturedDiff(
        diff_text=patch_text,
        diff_digest=hashlib.sha256(patch_text.encode("utf-8")).hexdigest(),
    )
    return candidate, workspace_config, runtime_config, reference_patch, run_context


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
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
        "task_text": "Fix the parser\n\nThe parser should accept quoted values.",
        "solver_material_refs": ("README.md", "src/parser.py"),
        "dependency_cluster_id": "dependency-cluster-1",
        "sampling_stratum": "stratum-1",
        "check_manifest_digest": "check-manifest",
        "hidden_check_bundle_digest": "hidden-bundle",
        "resource_limits": {"timeout_seconds": 30},
        "oracle_source": "private_tests",
        "check_type": "pytest",
    }
    payload.update(overrides)
    return payload
