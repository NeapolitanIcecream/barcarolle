import json
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

import barcarolle.reporting as reporting_module
from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    CheckRecord,
    EvaluationCellSet,
    MetricRecord,
    ResultCacheIdentity,
    ResultCellRef,
    ResultMatrix,
    ResultRecord,
    RollingOriginRecord,
    SelectorInput,
    SourceEventRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    canonical_digest,
    canonical_json,
    load_jsonl_records,
    make_check_digest,
    make_feature_snapshot_id,
    make_result_id,
    make_source_event_id,
    make_solver_material_digest,
    record_with_digest,
    write_jsonl_records,
)
from barcarolle.reporting import (
    ClaimConfig,
    ReportSection,
    build_claim_boundary,
    build_result_report,
    build_selector_report,
    build_task_pool_report,
    write_report,
)
from barcarolle.result_store import ResultJoinConfig, result_execution_digest
from barcarolle.selection import (
    FeatureConfig,
    RollingOriginPolicy,
    build_feature_snapshot,
    build_rolling_origin,
    build_rule_selector,
)
from barcarolle.selection.evaluation import METRIC_CONFIG_DIGEST
from barcarolle.task_pool import (
    GENERATION_PROVENANCE_SCHEMA_VERSION,
    GenerationProvenanceManifest,
    ObservedFrameEventRecord,
    TimeRange,
)
from barcarolle.verification import VERIFICATION_ADAPTER_DIGEST


def test_claim_config_digest_is_derived_from_claim_behavior() -> None:
    config = ClaimConfig()
    same = ClaimConfig()
    narrowed = ClaimConfig(requested_claims=("agent_result_identity",))

    assert config.claim_config_digest == same.claim_config_digest
    assert narrowed.claim_config_digest != config.claim_config_digest


def test_claim_config_rejects_malformed_claim_controls() -> None:
    with pytest.raises(ValueError, match="requested_claims must be a tuple"):
        ClaimConfig(requested_claims="selector_metrics")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="requested_claims must be unique"):
        ClaimConfig(requested_claims=("selector_metrics", "selector_metrics"))
    with pytest.raises(ValueError, match="unsupported requested claims: unknown"):
        ClaimConfig(requested_claims=("unknown",))
    with pytest.raises(
        ValueError,
        match="unsupported requested claims: task_pool_coverage",
    ):
        ClaimConfig(requested_claims=("task_pool_coverage",))


def test_claim_config_does_not_expose_claim_weakening_controls() -> None:
    with pytest.raises(TypeError, match="require_complete_matrices"):
        ClaimConfig(require_complete_matrices=False)  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="require_valid_metrics"):
        ClaimConfig(require_valid_metrics=False)  # type: ignore[call-arg]


def test_claim_config_canonicalizes_requested_claim_order() -> None:
    reordered = ClaimConfig(
        requested_claims=(
            "agent_result_identity",
            "task_pool_bundle_internal_consistency",
        )
    )
    canonical = ClaimConfig(
        requested_claims=(
            "task_pool_bundle_internal_consistency",
            "agent_result_identity",
        )
    )

    assert reordered.requested_claims == canonical.requested_claims
    assert reordered.claim_config_digest == canonical.claim_config_digest


def test_task_pool_and_result_reports_summarize_existing_records(tmp_path) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    result_pass = _result(
        outcome="pass", terminal_status="passed", total_cost=1.25, workspace_seconds=3.0
    )
    result_fail = _result(
        result_id="result-fail",
        outcome="fail",
        terminal_status="failed",
        total_cost=0.75,
        workspace_seconds=5.0,
    )

    task_section = build_task_pool_report(task_pool, artifact_root=tmp_path)
    result_section = build_result_report((result_pass, result_fail), (_agent(),))

    assert task_section.summary["task_count"] == 1
    assert task_section.summary["check_count"] == 1
    assert task_section.summary["source_event_count"] == 1
    assert task_section.summary["right_censored_source_event_count"] == 0
    assert task_section.summary["source_event_dispositions"] == {"accepted": 1}
    assert task_section.summary["certification_yield"] == {
        "candidate_count": 1,
        "accepted_count": 1,
        "rejected_count": 0,
        "rate": 1.0,
    }
    assert task_section.summary["pre_certification_excluded_count"] == 0
    assert task_section.summary["rejection_stage_counts"] == {}
    assert task_section.summary["rejection_reason_counts"] == {}
    assert task_section.summary["flaky_quarantine"]["count"] == 0
    assert task_section.source_digests["task_pool_digest"] == task_pool.task_pool_digest
    assert task_section.artifact_paths == (
        "tasks.jsonl",
        "checks.jsonl",
        "certification-evidence.jsonl",
        "source-events.jsonl",
    )
    assert task_section.unsupported_claims == ()
    assert result_section.summary["outcome_counts"] == {"fail": 1, "pass": 1}
    assert result_section.summary["scoreable_state_counts"] == {"scoreable": 2}
    assert result_section.summary["failure_label_counts"] == {"none": 2}
    assert result_section.summary["invalid_owner_counts"] == {"none": 2}
    assert result_section.summary["benchmark_invalid"] == {
        "execution_count": 0,
        "execution_rate": 0.0,
        "affected_task_check_count": 0,
        "observed_task_check_count": 1,
        "affected_task_check_rate": 0.0,
    }
    assert result_section.summary["total_cost"] == 2.0
    assert result_section.summary["latency"]["mean_workspace_seconds"] == 4.0
    assert result_section.summary["latency"]["agent_count"] == 0
    assert result_section.summary["latency"]["verification_count"] == 0
    assert result_pass.result_digest in result_section.source_digests["result_digests"]


def test_generated_task_pool_reports_enumerate_nested_provenance_artifacts(
    tmp_path,
) -> None:
    task_pool = _generated_task_pool_with_artifacts(tmp_path)

    task_section = build_task_pool_report(task_pool, artifact_root=tmp_path)
    claim_section = build_claim_boundary(
        task_pool,
        (),
        (),
        (),
        (),
        ClaimConfig(
            requested_claims=("task_pool_bundle_internal_consistency",),
        ),
        artifact_root=tmp_path,
    )

    expected_paths = (
        "tasks.jsonl",
        "checks.jsonl",
        "certification-evidence.jsonl",
        "source-events.jsonl",
        "generation-provenance.jsonl",
        "observed-frame-events.jsonl",
        "adapter-evidence.jsonl",
    )
    assert task_section.artifact_paths == expected_paths
    assert claim_section.artifact_paths == expected_paths
    assert claim_section.supported_claims == ("task_pool_bundle_internal_consistency",)


def test_result_report_rejects_duplicate_result_and_agent_identities() -> None:
    result = _result()
    agent = _agent()

    section = build_result_report((result, result), (agent, agent))

    assert section.supported_claims == ()
    assert f"duplicate result identity: {result.result_id}" in section.limitations
    assert f"duplicate Agent identity: {agent.agent_id}" in section.limitations


def test_result_report_rejects_conflicting_executions_for_one_cache_identity() -> None:
    result = _result()
    conflicting = _redigest_result(
        result,
        terminal_status="failed",
        outcome="fail",
    )

    section = build_result_report((result, conflicting), (_agent(),))

    assert section.supported_claims == ()
    assert (
        "conflicting Result executions share cache identity "
        f"{result.cache_identity.identity_digest}"
    ) in section.limitations


def test_task_pool_report_tracks_yield_rejections_and_flaky_quarantine(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def event(disposition, stage, reasons):
        return SimpleNamespace(
            disposition=disposition,
            rejection_stage=stage,
            rejection_reasons=reasons,
            task_material_available_at="2026-01-01T00:00:00Z",
            label_mature_at="2026-01-01T00:00:00Z",
        )

    def attempt(outcome):
        return {"outcome": outcome}

    bundle = SimpleNamespace(
        source_events=(
            event("accepted", None, ()),
            event("certification_rejected", "certification", ("flaky",)),
            event("certification_rejected", "certification", ("bad_patch",)),
            event("excluded", "candidate_filter", ("out_of_range",)),
        ),
        certification_evidence=(
            {
                "accepted": True,
                "repeat_count": 2,
                "base_check": (attempt("fail"), attempt("fail")),
                "reference_patch_check": (attempt("pass"), attempt("pass")),
            },
            {
                "accepted": False,
                "repeat_count": 2,
                "base_check": (attempt("fail"), attempt("pass")),
                "reference_patch_check": (attempt("pass"),),
            },
            {
                "accepted": False,
                "repeat_count": 2,
                "base_check": (attempt("fail"),),
                "reference_patch_check": (attempt("fail"),),
            },
        ),
    )
    monkeypatch.setattr(
        reporting_module,
        "load_validated_task_pool_bundle",
        lambda *_args: bundle,
    )

    section = build_task_pool_report(_task_pool(), artifact_root=tmp_path)

    assert section.summary["certification_yield"] == {
        "candidate_count": 3,
        "accepted_count": 1,
        "rejected_count": 2,
        "rate": 1 / 3,
    }
    assert section.summary["pre_certification_excluded_count"] == 1
    assert section.summary["rejection_stage_counts"] == {
        "candidate_filter": 1,
        "certification": 2,
    }
    assert section.summary["rejection_reason_counts"] == {
        "bad_patch": 1,
        "flaky": 1,
        "out_of_range": 1,
    }
    assert section.summary["flaky_quarantine"] == {
        "count": 1,
        "configured_repeated_candidate_count": 3,
        "rate": 1 / 3,
        "definition": (
            "rejected repeated certification with conflicting normalized "
            "outcomes on the base or reference-patch side"
        ),
    }


def test_result_report_tracks_later_benchmark_invalid_rate_by_execution() -> None:
    passed = _result(result_id="passed")
    benchmark_invalid = _redigest_result(
        _result(result_id="benchmark-invalid"),
        terminal_status="invalid",
        scoreable_state="benchmark_invalid",
        outcome="invalid",
        invalid_owner="benchmark",
        failure_label="check_launch_failed",
    )
    repriced = _redigest_result(
        benchmark_invalid,
        cost={"total_cost": 0.25},
        scoring_config_digest="scoring-v2",
        pricing_version="test-v2",
    )

    section = build_result_report((passed, benchmark_invalid, repriced), (_agent(),))

    assert section.summary["execution_count"] == 2
    assert section.summary["benchmark_invalid"] == {
        "execution_count": 1,
        "execution_rate": 0.5,
        "affected_task_check_count": 1,
        "observed_task_check_count": 1,
        "affected_task_check_rate": 1.0,
    }


def test_result_report_summarizes_monotonic_phase_latency() -> None:
    result = _redigest_result(
        _result(workspace_seconds=5.0),
        latency={
            "workspace_seconds": 5.0,
            "agent_seconds": 3.0,
            "verification_seconds": 1.0,
            "solver_checkout_seconds": 0.5,
            "verifier_checkout_seconds": 0.5,
            "diff_replay_seconds": 0.25,
            "cleanup_seconds": 0.25,
        },
    )

    section = build_result_report((result,), (_agent(),))

    assert section.summary["latency"] == {
        "count": 1,
        "total_workspace_seconds": 5.0,
        "mean_workspace_seconds": 5.0,
        "agent_count": 1,
        "total_agent_seconds": 3.0,
        "mean_agent_seconds": 3.0,
        "verification_count": 1,
        "total_verification_seconds": 1.0,
        "mean_verification_seconds": 1.0,
        "phase_breakdown": {
            "solver_checkout_seconds": {
                "count": 1,
                "total_seconds": 0.5,
                "mean_seconds": 0.5,
            },
            "verifier_checkout_seconds": {
                "count": 1,
                "total_seconds": 0.5,
                "mean_seconds": 0.5,
            },
            "diff_replay_seconds": {
                "count": 1,
                "total_seconds": 0.25,
                "mean_seconds": 0.25,
            },
            "cleanup_seconds": {
                "count": 1,
                "total_seconds": 0.25,
                "mean_seconds": 0.25,
            },
        },
        "checkout_cleanup": {
            "count": 1,
            "total_seconds": 1.25,
            "share_of_workspace_plus_cleanup_seconds": 1.25 / 5.25,
        },
    }


def test_result_report_does_not_fill_missing_historical_phases_with_zero() -> None:
    legacy = _result(result_id="legacy", workspace_seconds=7.0)
    current = _redigest_result(
        _result(result_id="current", workspace_seconds=5.0),
        latency={
            "workspace_seconds": 5.0,
            "agent_seconds": 3.0,
            "verification_seconds": 1.0,
            "solver_checkout_seconds": 0.5,
            "verifier_checkout_seconds": 0.5,
            "diff_replay_seconds": 0.25,
            "cleanup_seconds": 0.25,
        },
    )

    latency = build_result_report((legacy, current), (_agent(),)).summary["latency"]

    assert latency["count"] == 2
    assert latency["phase_breakdown"]["solver_checkout_seconds"]["count"] == 1
    assert latency["checkout_cleanup"]["count"] == 1


def test_result_report_rejects_agent_identity_drift() -> None:
    result = _result_with_wrong_agent_identity(_result())

    section = build_result_report((result,), (_agent(),))

    assert section.supported_claims == ()
    assert any(
        "cache identity does not match Agent" in claim
        for claim in section.unsupported_claims
    )


def test_result_report_does_not_support_empty_evidence() -> None:
    section = build_result_report((), ())

    assert section.supported_claims == ()
    assert "result evidence is absent" in section.unsupported_claims
    assert section.summary["benchmark_invalid"]["execution_rate"] is None
    assert section.summary["benchmark_invalid"]["affected_task_check_rate"] is None


def test_result_report_rejects_non_numeric_cost_and_latency() -> None:
    result = _redigest_result(
        _result(),
        cost={"total_cost": "12.5"},
        latency={"workspace_seconds": "7"},
    )

    section = build_result_report((result,), (_agent(),))

    assert section.supported_claims == ()
    assert any(
        "cost.total_cost is non-numeric" in claim
        for claim in section.unsupported_claims
    )
    assert any(
        "latency.workspace_seconds is non-numeric" in claim
        for claim in section.unsupported_claims
    )


def test_result_report_distinguishes_unknown_cost_from_measured_zero() -> None:
    measured_zero = _result(result_id="result-zero", total_cost=0.0)
    unknown_identity = record_with_digest(
        replace(
            _identity(),
            stochastic_settings_digest="unknown-observation-slot",
            identity_digest="",
        )
    )
    unknown = _redigest_result(
        _result(result_id="result-unknown", total_cost=None),
        cache_identity=unknown_identity,
        usage={},
    )

    section = build_result_report((measured_zero, unknown), (_agent(),))

    assert section.summary["total_cost"] == 0.0
    assert section.summary["cost_coverage"] == {
        "measured_result_count": 1,
        "measured_zero_cost_count": 1,
        "unknown_result_count": 1,
    }
    assert "usage_coverage" not in section.summary
    assert section.unsupported_claims == ()


def test_result_report_separates_pricing_views_from_executions() -> None:
    original = _result(total_cost=0.5, workspace_seconds=2.0)
    repriced = _redigest_result(
        original,
        cost={"total_cost": 0.75},
        scoring_config_digest="scoring-repriced",
        pricing_version="test-repriced",
    )
    assert result_execution_digest(original) == result_execution_digest(repriced)

    section = build_result_report((original, repriced), (_agent(),))

    assert section.summary["result_count"] == 1
    assert section.summary["execution_count"] == 1
    assert section.summary["pricing_view_count"] == 2
    assert section.summary["result_record_count"] == 2
    assert section.summary["outcome_counts"] == {"pass": 1}
    assert section.summary["latency"]["count"] == 1
    assert section.summary["total_cost"] is None
    assert section.summary["cost_by_scoring_config"] == {
        "scoring": {
            "execution_count": 1,
            "measured_execution_count": 1,
            "pricing_version": "test",
            "total_cost": 0.5,
            "unknown_execution_count": 0,
        },
        "scoring-repriced": {
            "execution_count": 1,
            "measured_execution_count": 1,
            "pricing_version": "test-repriced",
            "total_cost": 0.75,
            "unknown_execution_count": 0,
        },
    }


def test_result_report_rejects_conflicting_duplicate_pricing_view() -> None:
    original = _result(total_cost=0.5)
    conflicting = record_with_digest(
        replace(
            original,
            result_id="result-conflicting-copy",
            result_digest="",
            cost={"total_cost": 0.75},
        )
    )

    section = build_result_report((original, conflicting), (_agent(),))

    assert section.summary["execution_count"] == 1
    assert section.summary["pricing_view_count"] == 1
    assert section.summary["result_record_count"] == 2
    assert any(
        "conflicting pricing views" in error for error in section.unsupported_claims
    )


def test_result_report_rejects_multiple_pricing_versions_for_one_scoring_digest() -> (
    None
):
    first = _result(total_cost=0.5)
    second_identity = record_with_digest(
        replace(
            first.cache_identity,
            task_id="other-task",
            identity_digest="",
        )
    )
    second = _redigest_result(
        first,
        cache_identity=second_identity,
        task_id="other-task",
        pricing_version="other-pricing-version",
        cost={"total_cost": 0.75},
    )
    assert result_execution_digest(first) != result_execution_digest(second)

    section = build_result_report((first, second), (_agent(),))

    assert section.summary["execution_count"] == 2
    assert section.summary["cost_by_scoring_config"]["scoring"] == {
        "execution_count": 2,
        "measured_execution_count": 2,
        "pricing_version": None,
        "total_cost": None,
        "unknown_execution_count": 0,
    }
    assert any(
        "multiple pricing versions" in error for error in section.unsupported_claims
    )


def test_selector_report_preserves_matrix_cell_set_and_metric_traceability() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)

    section = build_selector_report(
        (selection,), (cell_set,), (selected_matrix, future_matrix), (metric,)
    )

    assert section.supported_claims == ()
    assert "rolling-origin evidence is missing" in section.unsupported_claims
    assert section.summary["selection_count"] == 1
    assert section.summary["selections"][0]["matrix_roles"] == (
        "future_holdout",
        "selected",
    )
    assert section.summary["selections"][0]["agent_ids"] == ("agent",)
    assert section.summary["selections"][0]["cell_set_digests"] == (
        cell_set.cell_set_digest,
    )
    assert (
        section.summary["selections"][0]["matrices"][0]["matrix_digest"]
        == future_matrix.matrix_digest
    )
    assert (
        section.summary["selections"][0]["matrices"][1]["matrix_digest"]
        == selected_matrix.matrix_digest
    )
    assert section.summary["selections"][0]["metrics"][0]["metric_value"] == 0.0
    assert (
        section.summary["selections"][0]["metrics"][0]["selected_matrix_digest"]
        == selected_matrix.matrix_digest
    )
    assert (
        section.summary["selections"][0]["metrics"][0]["future_matrix_digest"]
        == future_matrix.matrix_digest
    )
    assert metric.metric_digest in section.source_digests["metric_digests"]
    assert selected_matrix.matrix_digest in section.source_digests["matrix_digests"]
    assert cell_set.cell_set_digest in section.source_digests["cell_set_digests"]


def test_selector_report_withholds_mae_summary_without_complete_provenance() -> None:
    task_pool = _task_pool()
    result = _result()
    selector = build_rule_selector("recency")
    selection = record_with_digest(
        replace(
            _selection(task_pool),
            selector_id=selector.selector_id,
            selector_digest=selector.selector_digest,
            selection_digest="",
        )
    )
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)

    section = build_selector_report(
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (metric,),
        selectors=(selector,),
    )

    assert section.summary["mae_summary"] is None
    assert "rolling-origin evidence is missing" in section.unsupported_claims


def test_selector_report_preserves_common_task_check_exclusion_but_requires_provenance() -> (
    None
):
    selection, cell_set, selected_matrix, future_matrix, metric = (
        _selector_report_evidence_with_task_exclusion(partial=False)
    )

    section = build_selector_report(
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (metric,),
    )

    assert section.supported_claims == ()
    assert "rolling-origin evidence is missing" in section.unsupported_claims
    assert not any(
        "agent_specific_invalid_exclusion" in claim
        for claim in section.unsupported_claims
    )


def test_selector_report_rejects_partial_agent_exclusion() -> None:
    selection, cell_set, selected_matrix, future_matrix, metric = (
        _selector_report_evidence_with_task_exclusion(partial=True)
    )

    section = build_selector_report(
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (metric,),
    )

    assert section.supported_claims == ()
    assert any(
        "agent_specific_invalid_exclusion" in claim
        for claim in section.unsupported_claims
    )


def test_selector_report_rejects_metric_without_selection_budget_binding() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = record_with_digest(
        replace(
            _metric(selection, cell_set, selected_matrix, future_matrix),
            budget_digest=None,
            metric_digest="",
        )
    )

    section = build_selector_report(
        (selection,), (cell_set,), (selected_matrix, future_matrix), (metric,)
    )

    assert any(
        "budget digest does not match" in claim for claim in section.unsupported_claims
    )


def test_selector_report_rejects_an_unknown_metric_protocol() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = record_with_digest(
        replace(
            _metric(selection, cell_set, selected_matrix, future_matrix),
            metric_config_digest="unknown-metric-protocol",
            metric_digest="",
        )
    )

    section = build_selector_report(
        (selection,), (cell_set,), (selected_matrix, future_matrix), (metric,)
    )

    assert any(
        "unsupported metric protocol" in error for error in section.unsupported_claims
    )


def test_selector_report_does_not_support_empty_evidence() -> None:
    section = build_selector_report((), (), (), ())

    assert section.supported_claims == ()
    assert (
        "selector performance evidence is absent or incomplete"
        in section.unsupported_claims
    )


def test_selector_input_link_treats_supplied_agent_records_as_an_unordered_set() -> (
    None
):
    selection = _selection(_task_pool())
    agents = {
        "agent-b": replace(_agent(), agent_id="agent-b"),
        "agent-a": replace(_agent(), agent_id="agent-a"),
    }
    selector_input = SelectorInput(
        selector_input_id="selector-input",
        origin_id=selection.origin_id,
        task_pool_id=selection.task_pool_id,
        feature_snapshot_id=selection.feature_snapshot_id,
        agent_ids=("agent-a", "agent-b"),
        agent_record_digests=tuple(
            canonical_digest(agents[agent_id]) for agent_id in ("agent-a", "agent-b")
        ),
        eligible_task_check_refs=selection.selected_task_check_refs,
        pre_origin_result_ids=(),
        pre_origin_result_digests=(),
        budget_digest=selection.budget_digest,
        leakage_policy_digest="leakage-policy",
        selector_input_digest="selector-input-digest",
        task_pool_digest=selection.task_pool_digest,
        selection_budget_limit=1,
        feature_records_digest="feature-records",
        feature_snapshot_lint_status="passed",
        origin_as_of_cutoff="2026-01-05T00:00:00Z",
        origin_history_refs_digest=canonical_digest(selection.selected_task_check_refs),
        eligibility_mode=selection.eligibility_mode,
    )
    errors: list[str] = []

    reporting_module._append_selector_input_link_errors(
        errors,
        selection,
        selector_input,
        None,
        None,
        None,
        agents,
        {},
    )

    assert errors == []

    drifted_agents = {
        **agents,
        "agent-a": replace(agents["agent-a"], harness_digest="changed-harness"),
    }
    reporting_module._append_selector_input_link_errors(
        errors,
        selection,
        selector_input,
        None,
        None,
        None,
        drifted_agents,
        {},
    )
    assert errors == [
        "selector input selector-input Agent identities do not match supplied Agents"
    ]


def test_selector_report_preserves_and_rejects_cell_set_abstention() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = record_with_digest(
        replace(
            _cell_set(selection, result.cache_identity.identity_digest, result),
            abstention_reason="missing_required_results",
            cell_set_digest="",
        )
    )
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)

    section = build_selector_report(
        (selection,), (cell_set,), (selected_matrix, future_matrix), (metric,)
    )
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (metric,),
        ClaimConfig(),
        results=(result,),
    )

    assert section.supported_claims == ()
    assert section.summary["selections"][0]["cell_set_abstention_reasons"] == (
        "missing_required_results",
    )
    assert any(
        "cell_set cell-set abstained" in claim for claim in section.unsupported_claims
    )
    assert any(
        claim.startswith("selector_metrics:")
        for claim in claim_section.unsupported_claims
    )


def test_selector_report_rejects_strict_selection_created_after_future_result() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool, eligibility_mode="strict_prospective")
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)

    section = build_selector_report(
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (metric,),
        results=(result,),
    )

    assert section.supported_claims == ()
    assert any(
        f"selection selection was created at or after future Result {result.result_id} became available"
        in claim
        for claim in section.unsupported_claims
    )


def test_prospective_future_task_pool_error_contract_is_ordered_and_lazy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_pool = _task_pool()
    result = _result()
    base_selection = _selection(task_pool, eligibility_mode="strict_prospective")
    selections = tuple(
        record_with_digest(
            replace(
                base_selection,
                selection_id=f"selection-{suffix}",
                origin_id=f"origin-{suffix}",
                selection_digest="",
            )
        )
        for suffix in ("mismatch", "replay-error", "missing")
    )
    future_pool = record_with_digest(
        replace(task_pool, task_pool_id="future-pool", task_pool_digest="")
    )
    unused_pool = record_with_digest(
        replace(task_pool, task_pool_id="unused-pool", task_pool_digest="")
    )
    cell_sets = tuple(
        record_with_digest(
            replace(
                _cell_set_variant(
                    selection,
                    result.cache_identity.identity_digest,
                    result,
                    f"cell-set-{suffix}",
                ),
                future_task_pool_id=(
                    "missing-pool" if suffix == "missing" else future_pool.task_pool_id
                ),
                future_task_pool_digest=(
                    "missing-digest"
                    if suffix == "missing"
                    else future_pool.task_pool_digest
                ),
                cell_set_digest="",
            )
        )
        for selection, suffix in zip(
            selections,
            ("mismatch", "replay-error", "missing"),
            strict=True,
        )
    )
    base_origin = RollingOriginRecord(
        origin_id="origin-mismatch",
        task_pool_id=task_pool.task_pool_id,
        task_pool_digest=task_pool.task_pool_digest,
        origin_time="2026-01-05T00:00:00Z",
        policy_digest="policy",
        history_task_check_refs=(),
        history_censored_task_check_refs=(),
        future_holdout_task_check_refs=(),
        future_censored_task_check_refs=(),
        as_of_cutoff="2026-01-05T00:00:00Z",
        eligibility_mode="strict_prospective",
        holdout_overlap_policy="allow_cluster_overlap",
        as_of_cutoff_rule="origin_time",
        history_window_start=None,
        future_window_start="2026-01-06T00:00:00Z",
        future_window_end="2026-01-10T00:00:00Z",
        future_cohort_time_basis="task_material_available_at",
        maturity_lag_seconds=0,
        label_maturity_cutoff="2026-01-10T00:00:00Z",
        future_holdout_known=False,
        allowed_dependency_cluster_ids=(),
        origin_digest="origin-digest",
    )
    origins = tuple(
        replace(base_origin, origin_id=f"origin-{suffix}")
        for suffix in ("mismatch", "replay-error", "missing")
    )
    selection_bundle = SimpleNamespace(
        task_pool=task_pool,
        tasks=(),
        checks_by_id={},
    )
    future_bundle = SimpleNamespace(
        task_pool=future_pool,
        tasks=(),
        checks_by_id={},
    )
    load_calls: list[str] = []

    def fake_load_bundle(pool, _root):
        load_calls.append(pool.task_pool_id)
        return selection_bundle if pool is task_pool else future_bundle

    def fake_materialize(selection, *_args):
        if selection.selection_id == "selection-replay-error":
            raise ValueError("unreplayable")
        return (
            (TaskCheckRef("later-task", "later-check"),),
            (TaskCheckRef("censored-task", "censored-check"),),
        )

    monkeypatch.setattr(
        reporting_module,
        "load_validated_task_pool_bundle",
        fake_load_bundle,
    )
    monkeypatch.setattr(
        reporting_module,
        "materialize_prospective_future_cohort",
        fake_materialize,
    )

    errors = reporting_module._prospective_future_task_pool_errors(
        selections,
        cell_sets,
        origins,
        task_pool,
        (future_pool, future_pool, unused_pool),
        None,
    )

    assert errors == (
        "future Task Pool evidence contains a duplicate identity",
        "cell_set cell-set-mismatch mature future refs do not match later Task Pool",
        "cell_set cell-set-mismatch censored future refs do not match later Task Pool",
        "cell_set cell-set-replay-error future cohort cannot be replayed: unreplayable",
        "cell_set cell-set-missing references missing future Task Pool",
    )
    assert load_calls == [task_pool.task_pool_id, future_pool.task_pool_id]


def test_selector_and_claim_reports_reject_incomplete_matrix_without_abstention() -> (
    None
):
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    missing_cell = ResultCellRef(
        agent_id="agent",
        task_id="task",
        check_id="check",
        required_identity_digest=result.cache_identity.identity_digest,
        result_id=None,
        result_digest=None,
        cell_state="missing",
        exclusion_reason=None,
        outcome=None,
    )
    incomplete_selected_matrix = record_with_digest(
        replace(
            selected_matrix,
            cells=(missing_cell,),
            scoreable_state="incomplete",
            matrix_digest="",
        )
    )
    metric = _metric(selection, cell_set, incomplete_selected_matrix, future_matrix)

    selector_section = build_selector_report(
        (selection,),
        (cell_set,),
        (incomplete_selected_matrix, future_matrix),
        (metric,),
    )
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (incomplete_selected_matrix, future_matrix),
        (metric,),
        ClaimConfig(),
        results=(result,),
    )

    assert selector_section.supported_claims == ()
    assert any(
        "scoreable_state is incomplete" in claim
        for claim in selector_section.unsupported_claims
    )
    assert any(
        "contains non-result cells: missing=1" in claim
        for claim in selector_section.unsupported_claims
    )
    assert any(
        claim.startswith("selector_metrics:")
        for claim in claim_section.unsupported_claims
    )


def test_selector_and_claim_reports_reject_incomplete_metric_without_abstention() -> (
    None
):
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)
    incomplete_metric = record_with_digest(
        replace(metric, completeness_state="incomplete", metric_digest="")
    )

    selector_section = build_selector_report(
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (incomplete_metric,),
    )
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (incomplete_metric,),
        ClaimConfig(),
        results=(result,),
    )

    assert selector_section.supported_claims == ()
    assert any(
        "completeness_state is incomplete" in claim
        for claim in selector_section.unsupported_claims
    )
    assert any(
        claim.startswith("selector_metrics:")
        for claim in claim_section.unsupported_claims
    )


def test_selector_and_claim_reports_reject_recomputed_metric_value_mismatch() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)
    fabricated_metric = record_with_digest(
        replace(metric, metric_value=0.5, metric_digest="")
    )

    selector_section = build_selector_report(
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (fabricated_metric,),
    )
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (fabricated_metric,),
        ClaimConfig(),
        results=(result,),
    )

    assert any(
        "does not match recomputed value" in claim
        for claim in selector_section.unsupported_claims
    )
    assert any(
        "does not match recomputed value" in claim
        for claim in claim_section.unsupported_claims
    )


def test_selector_and_claim_reports_require_metrics_for_each_selection() -> None:
    task_pool = _task_pool()
    result = _result()
    first_selection = _selection(task_pool)
    second_selection = _selection_variant(
        task_pool,
        selection_id="selection-without-metric",
        origin_id="origin-without-metric",
    )
    first_cell_set = _cell_set(
        first_selection, result.cache_identity.identity_digest, result
    )
    second_cell_set = _cell_set_variant(
        second_selection,
        result.cache_identity.identity_digest,
        result,
        cell_set_id="cell-set-without-metric",
    )
    first_selected_matrix = _matrix(first_selection, first_cell_set, role="selected")
    first_future_matrix = _matrix(
        first_selection, first_cell_set, role="future_holdout"
    )
    second_selected_matrix = _matrix_variant(
        second_selection,
        second_cell_set,
        role="selected",
        matrix_id="matrix-selected-without-metric",
    )
    second_future_matrix = _matrix_variant(
        second_selection,
        second_cell_set,
        role="future_holdout",
        matrix_id="matrix-future-without-metric",
    )
    first_metric = _metric(
        first_selection, first_cell_set, first_selected_matrix, first_future_matrix
    )

    selector_section = build_selector_report(
        (first_selection, second_selection),
        (first_cell_set, second_cell_set),
        (
            first_selected_matrix,
            first_future_matrix,
            second_selected_matrix,
            second_future_matrix,
        ),
        (first_metric,),
    )
    claim_section = build_claim_boundary(
        task_pool,
        (first_selection, second_selection),
        (first_cell_set, second_cell_set),
        (
            first_selected_matrix,
            first_future_matrix,
            second_selected_matrix,
            second_future_matrix,
        ),
        (first_metric,),
        ClaimConfig(),
        results=(result,),
    )

    assert selector_section.supported_claims == ()
    assert any(
        "selection selection-without-metric has no metric evidence" in claim
        for claim in selector_section.unsupported_claims
    )
    assert any(
        claim.startswith("selector_metrics:")
        for claim in claim_section.unsupported_claims
    )


def test_selector_and_claim_reports_reject_unlinked_metric_evidence() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)
    broken_metric = record_with_digest(
        replace(metric, selected_matrix_digest="missing-matrix", metric_digest="")
    )

    selector_section = build_selector_report(
        (selection,), (cell_set,), (selected_matrix, future_matrix), (broken_metric,)
    )
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (broken_metric,),
        ClaimConfig(),
        results=(result,),
    )

    assert any(
        "selected_matrix_digest is not supplied" in claim
        for claim in selector_section.unsupported_claims
    )
    assert any(
        claim.startswith("selector_metrics:")
        for claim in claim_section.unsupported_claims
    )


def test_selector_and_claim_reports_reject_metric_origin_drift() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)
    drift_metric = record_with_digest(
        replace(metric, origin_id="other-origin", metric_digest="")
    )

    selector_section = build_selector_report(
        (selection,), (cell_set,), (selected_matrix, future_matrix), (drift_metric,)
    )
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (drift_metric,),
        ClaimConfig(),
        results=(result,),
    )

    assert any(
        "origin does not match selection" in claim
        for claim in selector_section.unsupported_claims
    )
    assert any(
        claim.startswith("selector_metrics:")
        for claim in claim_section.unsupported_claims
    )


def test_selector_and_claim_reports_reject_matrix_cell_identity_mismatch() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    bad_cell = replace(
        selected_matrix.cells[0], required_identity_digest="different-identity"
    )
    bad_selected_matrix = record_with_digest(
        replace(selected_matrix, cells=(bad_cell,), matrix_digest="")
    )
    metric = _metric(selection, cell_set, bad_selected_matrix, future_matrix)

    selector_section = build_selector_report(
        (selection,), (cell_set,), (bad_selected_matrix, future_matrix), (metric,)
    )
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (bad_selected_matrix, future_matrix),
        (metric,),
        ClaimConfig(),
        results=(result,),
    )

    assert any(
        "selected matrix cells do not match" in claim
        for claim in selector_section.unsupported_claims
    )
    assert any(
        claim.startswith("selector_metrics:")
        for claim in claim_section.unsupported_claims
    )


def test_selector_and_claim_reports_reject_matrix_result_binding_mismatch() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    bad_cell = replace(
        selected_matrix.cells[0], result_digest="different-result-digest"
    )
    bad_selected_matrix = record_with_digest(
        replace(selected_matrix, cells=(bad_cell,), matrix_digest="")
    )
    metric = _metric(selection, cell_set, bad_selected_matrix, future_matrix)

    selector_section = build_selector_report(
        (selection,), (cell_set,), (bad_selected_matrix, future_matrix), (metric,)
    )
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (bad_selected_matrix, future_matrix),
        (metric,),
        ClaimConfig(),
        results=(result,),
    )

    assert any(
        "selected matrix cells do not match" in claim
        for claim in selector_section.unsupported_claims
    )
    assert any(
        claim.startswith("selector_metrics:")
        for claim in claim_section.unsupported_claims
    )


def test_claim_boundary_separates_supported_and_unsupported_claims(tmp_path) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    missing_matrix = _matrix(
        selection,
        cell_set,
        role="selected",
        cell_state="missing",
        abstention_reason="missing_required_results",
    )
    mismatched_result = record_with_digest(
        ResultRecord(
            **{
                **result.__dict__,
                "result_id": "result-mismatch",
                "result_digest": "",
            }
        )
    )
    metric = _metric(
        selection,
        cell_set,
        missing_matrix,
        missing_matrix,
        abstention_reason="missing_required_results",
    )

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (missing_matrix,),
        (metric,),
        ClaimConfig(),
        results=(mismatched_result,),
        artifact_root=tmp_path,
    )

    assert "task_pool_bundle_internal_consistency" in section.supported_claims
    assert "benchmark_selection_frozen" in section.supported_claims
    assert any(
        claim.startswith("cache_completeness:") for claim in section.unsupported_claims
    )
    assert any(
        claim.startswith("selector_metrics:") for claim in section.unsupported_claims
    )


def test_claim_boundary_rejects_duplicate_frozen_selection_identity(tmp_path) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    selection = _selection(task_pool)

    section = build_claim_boundary(
        task_pool,
        (selection, selection),
        (),
        (),
        (),
        ClaimConfig(requested_claims=("benchmark_selection_frozen",)),
        artifact_root=tmp_path,
    )

    assert section.supported_claims == ()
    assert any(
        f"duplicate selection identity: {selection.selection_id}" in claim
        for claim in section.unsupported_claims
    )


def test_claim_boundary_rejects_duplicate_matrix_identity_for_cache_claim() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    matrix = _matrix(selection, cell_set, role="selected")

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (matrix, matrix),
        (),
        ClaimConfig(requested_claims=("cache_completeness",)),
    )

    assert section.supported_claims == ()
    assert any(
        f"duplicate matrix identity: {matrix.matrix_id}" in claim
        for claim in section.unsupported_claims
    )


@pytest.mark.parametrize("duplicate_kind", ("result", "Agent"))
def test_claim_boundary_rejects_duplicate_agent_result_identity_evidence(
    tmp_path,
    duplicate_kind: str,
) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    result = _result()
    agent = _agent()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    matrix = _matrix(selection, cell_set, role="selected")
    results = (result, result) if duplicate_kind == "result" else (result,)
    agents = (agent, agent) if duplicate_kind == "Agent" else (agent,)

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (matrix,),
        (),
        ClaimConfig(requested_claims=("agent_result_identity",)),
        results=results,
        agents=agents,
        artifact_root=tmp_path,
    )

    assert section.supported_claims == ()
    identity = result.result_id if duplicate_kind == "result" else agent.agent_id
    assert any(
        f"duplicate {duplicate_kind} identity: {identity}" in claim
        for claim in section.unsupported_claims
    )


def test_selector_report_rejects_duplicate_evidence_identities() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)

    section = build_selector_report(
        (selection, selection),
        (cell_set, cell_set),
        (selected_matrix, selected_matrix, future_matrix),
        (metric, metric),
    )

    assert {
        f"duplicate selection identity: {selection.selection_id}",
        f"duplicate cell_set identity: {cell_set.cell_set_id}",
        f"duplicate matrix identity: {selected_matrix.matrix_id}",
        f"duplicate metric identity: {metric.metric_id}",
    }.issubset(section.limitations)


def test_claim_boundary_rejects_selector_metrics_when_matrices_abstain() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(
        selection,
        cell_set,
        role="selected",
        abstention_reason="missing_required_results",
    )
    future_matrix = _matrix(
        selection,
        cell_set,
        role="future_holdout",
        abstention_reason="missing_required_results",
    )
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (metric,),
        ClaimConfig(),
        results=(result,),
    )

    assert any(
        claim.startswith("selector_metrics:") for claim in section.unsupported_claims
    )


def test_claim_boundary_rejects_strict_selection_created_after_future_result() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool, eligibility_mode="strict_prospective")
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (metric,),
        ClaimConfig(),
        results=(result,),
    )

    assert any(
        f"future Result {result.result_id} became available" in claim
        for claim in section.unsupported_claims
    )


def test_claim_boundary_rejects_invalid_or_unbound_frozen_selection() -> None:
    task_pool = _task_pool()
    selection = _selection(task_pool)
    tampered_selection = replace(selection, selection_digest="not-canonical")
    wrong_pool_selection = record_with_digest(
        replace(selection, task_pool_digest="other-pool", selection_digest="")
    )

    tampered_section = build_claim_boundary(
        task_pool, (tampered_selection,), (), (), (), ClaimConfig(), results=()
    )
    wrong_pool_section = build_claim_boundary(
        task_pool,
        (wrong_pool_selection,),
        (),
        (),
        (),
        ClaimConfig(),
        results=(),
    )

    assert any(
        claim.startswith("benchmark_selection_frozen:")
        for claim in tampered_section.unsupported_claims
    )
    assert any("task_pool" in claim for claim in wrong_pool_section.unsupported_claims)


def test_claim_boundary_rejects_invalid_matrix_evidence_for_selector_metrics() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    invalid_matrix = replace(selected_matrix, matrix_digest="not-canonical")
    metric = _metric(selection, cell_set, invalid_matrix, future_matrix)

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (invalid_matrix, future_matrix),
        (metric,),
        ClaimConfig(),
        results=(result,),
    )

    assert any(
        claim.startswith("selector_metrics:") for claim in section.unsupported_claims
    )


def test_claim_boundary_detects_result_identity_drift() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    matrix = _matrix(selection, cell_set, role="selected")
    wrong_id_cell = ResultCellRef(
        "agent",
        "task",
        "check",
        result.cache_identity.identity_digest,
        "stale-result-id",
        result.result_digest,
        "result",
        None,
        result.outcome,
    )
    drift_matrix = record_with_digest(
        replace(matrix, cells=(wrong_id_cell,), matrix_digest="")
    )

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (drift_matrix,),
        (),
        ClaimConfig(requested_claims=("agent_result_identity",)),
        results=(result,),
    )

    assert any(
        claim.startswith("agent_result_identity:")
        for claim in section.unsupported_claims
    )


def test_claim_boundary_detects_result_outcome_drift(tmp_path) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    drifted_cell = replace(cell_set.cells[0], outcome="fail")
    drifted_cell_set = record_with_digest(
        replace(cell_set, cells=(drifted_cell,), cell_set_digest="")
    )
    drifted_matrix = _matrix(selection, drifted_cell_set, role="selected")

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (drifted_cell_set,),
        (drifted_matrix,),
        (),
        ClaimConfig(requested_claims=("agent_result_identity",)),
        results=(result,),
        artifact_root=tmp_path,
    )

    assert section.supported_claims == ()
    assert any(
        "outcome does not match" in claim for claim in section.unsupported_claims
    )


def test_claim_boundary_rejects_exclusion_without_invalid_result(tmp_path) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    excluded_cell = replace(
        cell_set.cells[0],
        cell_state="excluded",
        exclusion_reason="unjustified_exclusion",
    )
    excluded_cell_set = record_with_digest(
        replace(cell_set, cells=(excluded_cell,), cell_set_digest="")
    )
    excluded_matrix = record_with_digest(
        replace(
            _matrix(selection, excluded_cell_set, role="selected"),
            scoreable_state="complete_with_exclusions",
            matrix_digest="",
        )
    )

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (excluded_cell_set,),
        (excluded_matrix,),
        (),
        ClaimConfig(requested_claims=("agent_result_identity",)),
        results=(result,),
        artifact_root=tmp_path,
    )

    assert section.supported_claims == ()
    assert any(
        "does not follow Result evidence" in claim
        for claim in section.unsupported_claims
    )


def test_claim_boundary_binds_result_identity_to_frozen_task_pool(
    tmp_path,
) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(
        selection,
        result.cache_identity.identity_digest,
        result,
    )
    matrix = _matrix(selection, cell_set, role="selected")

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (matrix,),
        (),
        ClaimConfig(requested_claims=("agent_result_identity",)),
        results=(result,),
        agents=(_agent(),),
        artifact_root=tmp_path,
    )

    assert section.supported_claims == ("agent_result_identity",)
    assert section.unsupported_claims == ()
    assert section.source_digests["agent_manifest_digests"] == ("agent-manifest",)
    assert task_pool.source_event_records_ref in section.artifact_paths

    drifted_identity = record_with_digest(
        replace(result.cache_identity, base_commit="b" * 40, identity_digest="")
    )
    drifted_result = _redigest_result(
        result,
        cache_identity=drifted_identity,
    )
    drifted_cell_set = _cell_set(
        selection,
        drifted_identity.identity_digest,
        drifted_result,
    )
    drifted_matrix = _matrix(selection, drifted_cell_set, role="selected")

    drifted_section = build_claim_boundary(
        task_pool,
        (selection,),
        (drifted_cell_set,),
        (drifted_matrix,),
        (),
        ClaimConfig(requested_claims=("agent_result_identity",)),
        results=(drifted_result,),
        agents=(_agent(),),
        artifact_root=tmp_path,
    )

    assert drifted_section.supported_claims == ()
    assert any(
        "identity does not match the frozen Task/Check" in claim
        for claim in drifted_section.unsupported_claims
    )


@pytest.mark.parametrize(
    ("agent_evidence", "expected_reason"),
    (
        ("missing", "results reference unknown Agents: agent"),
        ("drifted", "cache identity does not match Agent agent"),
    ),
)
def test_claim_boundary_requires_matching_agent_evidence(
    tmp_path,
    agent_evidence: str,
    expected_reason: str,
) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    matrix = _matrix(selection, cell_set, role="selected")
    agents = (
        ()
        if agent_evidence == "missing"
        else (replace(_agent(), prompt_digest="drifted-prompt"),)
    )

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (matrix,),
        (),
        ClaimConfig(requested_claims=("agent_result_identity",)),
        results=(result,),
        agents=agents,
        artifact_root=tmp_path,
    )

    assert section.supported_claims == ()
    assert any(expected_reason in claim for claim in section.unsupported_claims)


def test_claim_boundary_rejects_ambiguous_result_executions(tmp_path) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    result = _result()
    conflicting = _redigest_result(
        result,
        terminal_status="failed",
        outcome="fail",
    )
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    matrix = _matrix(selection, cell_set, role="selected")

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (matrix,),
        (),
        ClaimConfig(requested_claims=("agent_result_identity",)),
        results=(result, conflicting),
        agents=(_agent(),),
        artifact_root=tmp_path,
    )

    assert section.supported_claims == ()
    assert any(
        "conflicting Result executions share cache identity" in reason
        for reason in section.unsupported_claims
    )


def test_claim_boundary_traces_result_bindings_on_excluded_cells() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    result_matrix = _matrix(selection, cell_set, role="selected")
    excluded_cell = ResultCellRef(
        agent_id="other-agent",
        task_id="task",
        check_id="check",
        required_identity_digest="other-identity",
        result_id="stale-result-id",
        result_digest="stale-result-digest",
        cell_state="excluded",
        exclusion_reason="task_check_infrastructure_failure:check_launch_error:stale",
        outcome="invalid",
    )
    drift_matrix = record_with_digest(
        replace(
            result_matrix,
            agent_ids=("agent", "other-agent"),
            cells=(result_matrix.cells[0], excluded_cell),
            scoreable_state="complete_with_exclusions",
            matrix_digest="",
        )
    )

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (drift_matrix,),
        (),
        ClaimConfig(requested_claims=("agent_result_identity",)),
        results=(result,),
    )

    assert section.supported_claims == ()
    assert any(
        "missing result digest stale-result-digest" in claim
        for claim in section.unsupported_claims
    )


def test_claim_boundary_rejects_identity_claim_from_invalid_matrix_or_result() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    matrix = _matrix(selection, cell_set, role="selected")
    invalid_matrix = replace(matrix, matrix_digest="not-canonical")
    invalid_result = replace(result, result_digest="not-canonical")

    matrix_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (invalid_matrix,),
        (),
        ClaimConfig(requested_claims=("agent_result_identity",)),
        results=(result,),
    )
    result_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (matrix,),
        (),
        ClaimConfig(requested_claims=("agent_result_identity",)),
        results=(invalid_result,),
    )

    assert any(
        claim.startswith("agent_result_identity:")
        for claim in matrix_section.unsupported_claims
    )
    assert any(
        claim.startswith("agent_result_identity:")
        for claim in result_section.unsupported_claims
    )


def test_task_pool_report_rejects_missing_audit_fields() -> None:
    bad_pool = record_with_digest(
        replace(_task_pool(), task_records_ref="", task_pool_digest="")
    )

    section = build_task_pool_report(bad_pool)
    claim_section = build_claim_boundary(
        bad_pool, (), (), (), (), ClaimConfig(), results=()
    )

    assert any(
        "task_records_ref is missing" in claim for claim in section.unsupported_claims
    )
    assert any(
        claim.startswith("task_pool_bundle_internal_consistency:")
        for claim in claim_section.unsupported_claims
    )


@pytest.mark.parametrize(
    ("filename", "error"),
    (
        ("tasks.jsonl", "task records are unavailable"),
        ("checks.jsonl", "check records are unavailable"),
        (
            "certification-evidence.jsonl",
            "certification evidence is unavailable",
        ),
    ),
)
def test_task_pool_claims_require_referenced_artifacts(
    tmp_path,
    filename: str,
    error: str,
) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    (tmp_path / filename).unlink()

    section = build_task_pool_report(task_pool, artifact_root=tmp_path)
    claim_section = build_claim_boundary(
        task_pool,
        (),
        (),
        (),
        (),
        ClaimConfig(),
        artifact_root=tmp_path,
    )

    assert any(error in claim for claim in section.unsupported_claims)
    assert any(error in claim for claim in claim_section.unsupported_claims)


@pytest.mark.parametrize(
    ("filename", "missing_field", "error"),
    (
        ("tasks.jsonl", "task_id", "task records are unavailable or invalid"),
        ("checks.jsonl", "check_id", "check records are unavailable or invalid"),
    ),
)
def test_task_pool_claims_treat_missing_artifact_fields_as_unsupported(
    tmp_path,
    filename: str,
    missing_field: str,
    error: str,
) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    path = tmp_path / filename
    record = json.loads(path.read_text(encoding="utf-8"))
    record.pop(missing_field)
    path.write_text(f"{canonical_json(record)}\n", encoding="utf-8")

    section = build_task_pool_report(task_pool, artifact_root=tmp_path)
    claim_section = build_claim_boundary(
        task_pool,
        (),
        (),
        (),
        (),
        ClaimConfig(),
        artifact_root=tmp_path,
    )

    assert any(error in claim for claim in section.unsupported_claims)
    assert any(error in claim for claim in claim_section.unsupported_claims)


@pytest.mark.parametrize(
    ("filename", "field", "value", "record_type", "digest_field", "error"),
    (
        (
            "tasks.jsonl",
            "task_text",
            "",
            TaskRecord,
            "task_records_digest",
            "task_text must not be empty",
        ),
        (
            "checks.jsonl",
            "resource_limits",
            {"timeout_seconds": None},
            CheckRecord,
            "check_records_digest",
            "check check failed validation: resource_limits values must be bounded",
        ),
    ),
)
def test_task_pool_claims_reject_semantically_invalid_task_and_check_records(
    tmp_path,
    filename: str,
    field: str,
    value: object,
    record_type: type,
    digest_field: str,
    error: str,
) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    path = tmp_path / filename
    record = json.loads(path.read_text(encoding="utf-8"))
    record[field] = value
    path.write_text(f"{canonical_json(record)}\n", encoding="utf-8")
    records = tuple(load_jsonl_records(path, record_type))
    task_pool = record_with_digest(
        replace(
            task_pool,
            **{digest_field: canonical_digest(records), "task_pool_digest": ""},
        )
    )

    section = build_task_pool_report(task_pool, artifact_root=tmp_path)
    claim_section = build_claim_boundary(
        task_pool,
        (),
        (),
        (),
        (),
        ClaimConfig(),
        artifact_root=tmp_path,
    )

    assert any(error in claim for claim in section.unsupported_claims)
    assert any(error in claim for claim in claim_section.unsupported_claims)


def test_task_pool_claims_require_evidence_for_every_accepted_task_check(
    tmp_path,
) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    evidence: tuple[object, ...] = ()
    write_jsonl_records(tmp_path / "certification-evidence.jsonl", evidence)
    task_pool = record_with_digest(
        replace(
            task_pool,
            certification_evidence_digest=canonical_digest(evidence),
            task_pool_digest="",
        )
    )

    section = build_task_pool_report(task_pool, artifact_root=tmp_path)

    assert any(
        "certification evidence does not exactly cover accepted Task/Check records"
        in claim
        for claim in section.unsupported_claims
    )


def test_task_pool_claims_require_evidence_for_every_rejected_candidate(
    tmp_path,
) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    task_pool = record_with_digest(
        replace(
            task_pool,
            rejected_candidate_ids=("rejected-candidate",),
            rejection_summary_digest=canonical_digest(
                {"rejected_count": 1, "reasons": {"check failed": 1}}
            ),
            task_pool_digest="",
        )
    )

    section = build_task_pool_report(task_pool, artifact_root=tmp_path)

    assert any(
        "certification evidence does not exactly cover rejected candidates" in claim
        for claim in section.unsupported_claims
    )


def test_task_pool_claims_require_base_fail_reference_patch_pass_evidence(
    tmp_path,
) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    path = tmp_path / "certification-evidence.jsonl"
    evidence = json.loads(path.read_text(encoding="utf-8"))
    evidence["base_check"][0]["outcome"] = "pass"
    evidence["base_check"][0]["failure_label"] = None
    records = (evidence,)
    write_jsonl_records(path, records)
    task_pool = record_with_digest(
        replace(
            task_pool,
            certification_evidence_digest=canonical_digest(records),
            task_pool_digest="",
        )
    )

    section = build_task_pool_report(task_pool, artifact_root=tmp_path)

    assert any(
        "accepted certification base checks must fail" in claim
        for claim in section.unsupported_claims
    )


@pytest.mark.parametrize(
    ("filename", "error"),
    (
        ("tasks.jsonl", "task records digest does not match"),
        ("checks.jsonl", "check records digest does not match"),
        (
            "certification-evidence.jsonl",
            "certification evidence digest does not match",
        ),
    ),
)
def test_task_pool_claims_reject_artifact_digest_drift(
    tmp_path,
    filename: str,
    error: str,
) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    path = tmp_path / filename
    record = json.loads(path.read_text(encoding="utf-8"))
    changed_field = {
        "tasks.jsonl": "dependency_cluster_id",
        "checks.jsonl": "oracle_source",
        "certification-evidence.jsonl": "candidate_id",
    }[filename]
    record[changed_field] = "changed"
    path.write_text(f"{canonical_json(record)}\n", encoding="utf-8")

    section = build_task_pool_report(task_pool, artifact_root=tmp_path)
    claim_section = build_claim_boundary(
        task_pool,
        (),
        (),
        (),
        (),
        ClaimConfig(),
        artifact_root=tmp_path,
    )

    assert any(error in claim for claim in section.unsupported_claims)
    assert any(error in claim for claim in claim_section.unsupported_claims)


def test_selector_reporting_replays_task_metadata_against_task_pool(tmp_path) -> None:
    task_pool = _task_pool_with_artifacts(tmp_path)
    (task,) = load_jsonl_records(tmp_path / "tasks.jsonl", TaskRecord)
    (check,) = load_jsonl_records(tmp_path / "checks.jsonl", CheckRecord)
    origin = build_rolling_origin(
        task_pool,
        (task,),
        {check.check_id: check},
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-05T00:00:00Z", "2026-01-10T00:00:00Z"),
        RollingOriginPolicy(
            "origin_time",
            "counterfactual_replay",
            "allow_cluster_overlap",
            True,
        ),
    )
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (task,),
        {check.check_id: check},
        (),
        FeatureConfig(("task_stratum",)),
    )
    drifted_records = (replace(snapshot.feature_records[0], value="drifted-stratum"),)
    drifted_snapshot = replace(
        snapshot,
        feature_snapshot_id="",
        feature_records=drifted_records,
        feature_records_digest=canonical_digest(drifted_records),
        feature_snapshot_digest="",
    )
    drifted_snapshot = replace(
        drifted_snapshot,
        feature_snapshot_id=make_feature_snapshot_id(drifted_snapshot),
    )
    drifted_snapshot = record_with_digest(drifted_snapshot)
    errors: list[str] = []

    reporting_module._append_origin_task_pool_errors(
        errors,
        task_pool,
        (origin,),
        (drifted_snapshot,),
        tmp_path,
    )

    assert len(errors) == 1
    assert "task_stratum feature does not match frozen Task record" in errors[0]


def test_claim_boundary_does_not_support_claims_without_evidence() -> None:
    section = build_claim_boundary(
        _task_pool(),
        (),
        (),
        (),
        (),
        ClaimConfig(),
        results=(),
    )

    assert any(
        claim.startswith("task_pool_bundle_internal_consistency:")
        for claim in section.unsupported_claims
    )
    assert any(
        claim.startswith("benchmark_selection_frozen:")
        for claim in section.unsupported_claims
    )
    assert any(
        claim.startswith("cache_completeness:") for claim in section.unsupported_claims
    )
    assert any(
        claim.startswith("selector_metrics:") for claim in section.unsupported_claims
    )
    assert any(
        claim.startswith("agent_result_identity:")
        for claim in section.unsupported_claims
    )


def test_write_report_writes_markdown_and_json_summaries(tmp_path) -> None:
    section = build_task_pool_report(_task_pool())
    markdown_path = tmp_path / "report.md"
    json_path = tmp_path / "report.json"

    write_report((section,), markdown_path)
    write_report((section,), json_path)

    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert "# Barcarolle Report" in markdown
    assert "task_pool_digest" in markdown
    assert "tasks.jsonl" in markdown
    assert payload[0]["section_id"] == "task_pool"
    assert payload[0]["artifact_paths"] == [
        "tasks.jsonl",
        "checks.jsonl",
        "certification-evidence.jsonl",
        "source-events.jsonl",
    ]


def test_write_report_sanitizes_local_absolute_artifact_paths(tmp_path) -> None:
    artifact = tmp_path / "runs" / "workspace-run" / "stdout.txt"
    section = ReportSection(
        section_id="artifacts",
        heading="Artifacts",
        summary={
            "task_records_ref": str(artifact),
            "nested": {"refs": (str(artifact),)},
        },
        source_digests={"artifact_digest": "digest"},
        artifact_paths=(str(artifact),),
    )
    markdown_path = tmp_path / "report.md"
    json_path = tmp_path / "report.json"

    write_report((section,), markdown_path)
    write_report((section,), json_path)

    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert str(tmp_path) not in markdown
    assert "/Users/" not in markdown
    assert "/home/" not in markdown
    assert "runs/workspace-run/stdout.txt" in markdown
    assert payload[0]["summary"]["task_records_ref"] == "runs/workspace-run/stdout.txt"
    assert payload[0]["summary"]["nested"]["refs"] == ["runs/workspace-run/stdout.txt"]
    assert payload[0]["artifact_paths"] == ["runs/workspace-run/stdout.txt"]


@pytest.mark.parametrize(
    ("artifact_path", "safe_ref"),
    (
        ("/tmp/barcarolle-user/workspaces/run/stdout.txt", "stdout.txt"),
        ("/private/var/folders/ab/private-run/verifier/stderr.txt", "stderr.txt"),
    ),
)
def test_write_report_hides_external_absolute_artifact_directories(
    tmp_path,
    artifact_path: str,
    safe_ref: str,
) -> None:
    section = ReportSection(
        section_id="artifacts",
        heading="Artifacts",
        summary={"artifact_ref": artifact_path},
        source_digests={"artifact_digest": "digest"},
        artifact_paths=(artifact_path,),
    )
    markdown_path = tmp_path / "report.md"
    json_path = tmp_path / "report.json"

    write_report((section,), markdown_path, artifact_root=tmp_path / "artifacts")
    write_report((section,), json_path, artifact_root=tmp_path / "artifacts")

    markdown = markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert artifact_path not in markdown
    assert payload[0]["summary"]["artifact_ref"] == safe_ref
    assert payload[0]["artifact_paths"] == [safe_ref]


def _task_pool() -> TaskPoolRecord:
    record = TaskPoolRecord(
        task_pool_id="task-pool",
        task_pool_digest="",
        repository_id="repo",
        task_ids=("task",),
        check_ids=("check",),
        task_records_ref="tasks.jsonl",
        task_records_digest="task-records",
        check_records_ref="checks.jsonl",
        check_records_digest="check-records",
        certification_evidence_ref="certification-evidence.jsonl",
        source_event_records_ref="source-events.jsonl",
        source_event_records_digest="source-events",
        rejected_candidate_ids=("rejected",),
        rejection_summary_digest="rejection-summary",
        certification_evidence_digest="certification-evidence",
        generation_provenance_ref=None,
        generation_provenance_digest=None,
        generator_config_digest=None,
        source_protocol_digest=None,
        certification_config_digest="certification",
        created_at="2026-01-01T00:00:00Z",
    )
    return record_with_digest(record)


def _task_pool_with_artifacts(root) -> TaskPoolRecord:
    task_text = "Fix the issue."
    solver_material_refs = ("README.md",)
    task = TaskRecord(
        task_id="task",
        repository_id="repo",
        base_commit="a" * 40,
        source_family="issue",
        source_ref="issue-1",
        source_resolved_at="2026-01-01T00:00:00Z",
        task_material_available_at="2026-01-01T00:00:00Z",
        task_text=task_text,
        solver_material_digest=make_solver_material_digest(
            task_text, solver_material_refs
        ),
        solver_material_refs=solver_material_refs,
        check_ids=("check",),
        dependency_cluster_id="dependency-cluster",
        sampling_stratum="stratum",
    )
    check = CheckRecord(
        check_id="check",
        task_id="task",
        check_type="pytest",
        check_manifest_digest="check-manifest",
        hidden_check_bundle_digest="hidden-bundle",
        resource_limits={"timeout_seconds": 5},
        oracle_source="private-tests",
        check_material_available_at="2026-01-01T00:00:00Z",
    )
    evidence = (
        {
            "candidate_id": "candidate",
            "accepted": True,
            "rejection_reasons": (),
            "repeat_count": 1,
            "base_check": (
                {
                    "outcome": "fail",
                    "failure_label": "check_failed",
                    "timed_out": False,
                    "duration_seconds": 0.1,
                    "evidence_excerpt": "",
                },
            ),
            "reference_patch_check": (
                {
                    "outcome": "pass",
                    "failure_label": None,
                    "timed_out": False,
                    "duration_seconds": 0.1,
                    "evidence_excerpt": "",
                },
            ),
            "reference_patch_digest": "0" * 64,
            "task_digest": canonical_digest(task),
            "check_digest": canonical_digest(check),
            "workspace_config_digest": canonical_digest({"workspace": "fixture"}),
            "runtime_config_digest": canonical_digest({"runtime": "fixture"}),
            "check_execution_binding_digest": canonical_digest({"check": "fixture"}),
            "verification_adapter_digest": VERIFICATION_ADAPTER_DIGEST,
        },
    )
    write_jsonl_records(root / "tasks.jsonl", (task,))
    write_jsonl_records(root / "checks.jsonl", (check,))
    write_jsonl_records(root / "certification-evidence.jsonl", evidence)
    source_events = (
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
                label_mature_at="2026-01-01T00:00:00.000000Z",
                candidate_id="candidate",
                task_id=task.task_id,
                check_id=check.check_id,
                disposition="accepted",
                rejection_stage=None,
                rejection_reasons=(),
                dependency_cluster_id=task.dependency_cluster_id,
                sampling_stratum=task.sampling_stratum,
                source_event_digest="",
            )
        ),
    )
    write_jsonl_records(root / "source-events.jsonl", source_events)
    return record_with_digest(
        TaskPoolRecord(
            task_pool_id="task-pool",
            task_pool_digest="",
            repository_id="repo",
            task_ids=(task.task_id,),
            check_ids=(check.check_id,),
            task_records_ref="tasks.jsonl",
            task_records_digest=canonical_digest((task,)),
            check_records_ref="checks.jsonl",
            check_records_digest=canonical_digest((check,)),
            certification_evidence_ref="certification-evidence.jsonl",
            source_event_records_ref="source-events.jsonl",
            source_event_records_digest=canonical_digest(source_events),
            rejected_candidate_ids=(),
            rejection_summary_digest=canonical_digest(
                {"rejected_count": 0, "reasons": {}}
            ),
            certification_evidence_digest=canonical_digest(evidence),
            generation_provenance_ref=None,
            generation_provenance_digest=None,
            generator_config_digest=None,
            source_protocol_digest=None,
            certification_config_digest=canonical_digest({"repeat_count": 1}),
            created_at="2026-01-01T00:00:00Z",
        )
    )


def _generated_task_pool_with_artifacts(root) -> TaskPoolRecord:
    task_pool = _task_pool_with_artifacts(root)
    source_events = tuple(
        load_jsonl_records(root / "source-events.jsonl", SourceEventRecord)
    )
    observed_at = "2026-01-01T00:00:00.000000Z"
    frame_events = tuple(
        record_with_digest(
            ObservedFrameEventRecord(
                source_event_id=event.source_event_id,
                repository_id=event.repository_id,
                source_family=event.source_family,
                source_ref=event.source_ref,
                observed_at=observed_at,
                frame_event_digest="",
            )
        )
        for event in source_events
    )
    behavior = {
        "generator_family": "fixture",
        "adapter_version": "1",
        "implementation_digest": "fixture-implementation",
        "behavior_config": {"strategy": "stable"},
    }
    protocol = {
        "source_kind": "issue",
        "target_definition": "all fixture issues in the declared window",
        "query_semantics": {"state": "resolved"},
        "sampling_policy": {"mode": "all"},
        "deduplication_policy": {"key": "source_ref"},
    }
    protocol_digest = canonical_digest(protocol)
    frame = {
        "frame_id": "fixture-frame",
        "source_protocol_digest": protocol_digest,
        "source_revision": "fixture-revision",
        "window_start": observed_at,
        "window_end": observed_at,
        "event_inventory_ref": "observed-frame-events.jsonl",
        "event_inventory_digest": canonical_digest(frame_events),
        "observation_authority": "source_authoritative",
        "observation_receipt_digest": "fixture-receipt",
        "known_blind_spots": [],
        "coverage_mode": "one_source_event_per_frame_unit_v1",
    }
    run = {
        "run_id": "fixture-run",
        "producer_id": "fixture-producer",
        "authority_kind": "barcarolle_managed",
        "authority_digest": "fixture-authority",
        "started_at": observed_at,
        "finished_at": observed_at,
        "input_snapshot_digest": "fixture-input",
    }
    adapter_evidence = {"schema_version": "fixture_v1", "count": 1}
    outputs = {
        "prepared_candidate_records_digest": "fixture-candidates",
        "adapter_evidence_ref": "adapter-evidence.jsonl",
        "adapter_evidence_digest": canonical_digest(adapter_evidence),
        "task_records_digest": task_pool.task_records_digest,
        "check_records_digest": task_pool.check_records_digest,
        "source_event_records_digest": task_pool.source_event_records_digest,
        "certification_evidence_digest": task_pool.certification_evidence_digest,
    }
    manifest = record_with_digest(
        GenerationProvenanceManifest(
            schema_version=GENERATION_PROVENANCE_SCHEMA_VERSION,
            generator_behavior=behavior,
            generator_behavior_digest=canonical_digest(behavior),
            source_protocol=protocol,
            source_protocol_digest=protocol_digest,
            observed_frame=frame,
            observed_frame_digest=canonical_digest(frame),
            run=run,
            run_digest=canonical_digest(run),
            outputs=outputs,
            outputs_digest=canonical_digest(outputs),
            manifest_digest="",
        )
    )
    write_jsonl_records(root / "observed-frame-events.jsonl", frame_events)
    write_jsonl_records(root / "adapter-evidence.jsonl", (adapter_evidence,))
    write_jsonl_records(root / "generation-provenance.jsonl", (manifest,))
    return record_with_digest(
        replace(
            task_pool,
            generation_provenance_ref="generation-provenance.jsonl",
            generation_provenance_digest=manifest.manifest_digest,
            generator_config_digest=manifest.generator_behavior_digest,
            source_protocol_digest=manifest.source_protocol_digest,
            source_window_start=observed_at,
            source_window_end=observed_at,
            task_pool_digest="",
        )
    )


def _agent() -> AgentRecord:
    return AgentRecord(
        agent_id="agent",
        agent_manifest_digest="agent-manifest",
        requested_model_id="model",
        model_snapshot_id="model",
        model_resolution_scope_id=None,
        model_resolution_scope_started_at=None,
        model_resolution_scope_ended_at=None,
        harness_digest="harness",
        repository_instruction_digest="instructions",
        prompt_digest="prompt",
        tools_digest="tools",
        retrieval_digest="retrieval",
        skills_digest="skills",
        network_policy_digest="network",
        adapter_digest="adapter",
    )


def _identity() -> ResultCacheIdentity:
    check = CheckRecord(
        check_id="check",
        task_id="task",
        check_type="pytest",
        check_manifest_digest="check-manifest",
        hidden_check_bundle_digest="hidden-bundle",
        resource_limits={"timeout_seconds": 5},
        oracle_source="private-tests",
        check_material_available_at="2026-01-01T00:00:00Z",
    )
    identity = ResultCacheIdentity(
        task_id="task",
        check_id="check",
        repository_id="repo",
        base_commit="a" * 40,
        submodule_state_digest="submodules",
        solver_material_digest=make_solver_material_digest(
            "Fix the issue.",
            ("README.md",),
        ),
        check_digest=make_check_digest(check),
        agent_manifest_digest="agent-manifest",
        requested_model_id="model",
        model_snapshot_id="model",
        model_resolution_scope_id=None,
        model_resolution_scope_started_at=None,
        model_resolution_scope_ended_at=None,
        harness_digest="harness",
        repository_instruction_digest="instructions",
        prompt_digest="prompt",
        tools_digest="tools",
        retrieval_digest="retrieval",
        skills_digest="skills",
        network_policy_digest="network",
        budget_digest="budget",
        retry_policy_digest="retry",
        stochastic_settings_digest="stochastic",
        adapter_digest="adapter",
        workspace_config_digest="workspace",
        runtime_config_digest="runtime",
        hardware_profile_digest=None,
        identity_digest="",
    )
    return record_with_digest(identity)


def _result(
    result_id: str = "result",
    outcome: str = "pass",
    terminal_status: str = "passed",
    total_cost: float | None = 0.5,
    workspace_seconds: float = 2.0,
) -> ResultRecord:
    result = ResultRecord(
        result_id="",
        result_digest="",
        cache_identity=_identity(),
        agent_id="agent",
        task_id="task",
        check_id="check",
        terminal_status=terminal_status,
        scoreable_state="scoreable",
        outcome=outcome,
        invalid_owner=None,
        failure_label=None,
        cost={"total_cost": total_cost},
        scoring_config_digest="scoring",
        pricing_version="test",
        usage={"total_tokens": 10},
        latency={"workspace_seconds": workspace_seconds},
        diff_digest="diff",
        verifier_metadata_digest=f"verifier:{result_id}",
        started_at="2026-01-04T00:00:00Z",
        finished_at="2026-01-04T00:00:01Z",
        evidence_source_kind="barcarolle_managed",
        evidence_source_manifest_digest=None,
        evidence_imported_at=None,
        source_result_available_at="2026-01-04T00:00:02Z",
        availability_policy="managed_observation_v1",
        result_available_at="2026-01-04T00:00:02Z",
    )
    return record_with_digest(replace(result, result_id=make_result_id(result)))


def _redigest_result(
    result: ResultRecord,
    **changes: object,
) -> ResultRecord:
    draft = replace(
        result,
        result_id="",
        result_digest="",
        **changes,
    )
    return record_with_digest(replace(draft, result_id=make_result_id(draft)))


def _result_with_wrong_agent_identity(result: ResultRecord) -> ResultRecord:
    cache_identity = record_with_digest(
        replace(
            result.cache_identity,
            agent_manifest_digest="other-agent-manifest",
            identity_digest="",
        )
    )
    return _redigest_result(result, cache_identity=cache_identity)


def _selection(
    task_pool: TaskPoolRecord,
    *,
    eligibility_mode: str = "counterfactual_replay",
    created_at: str = "2026-01-05T00:00:00Z",
) -> BenchmarkSelectionRecord:
    ref = TaskCheckRef("task", "check")
    selection = BenchmarkSelectionRecord(
        selection_id="selection",
        task_pool_id=task_pool.task_pool_id,
        task_pool_digest=task_pool.task_pool_digest,
        origin_id="origin",
        selector_id="selector",
        selector_digest="selector-digest",
        selected_task_check_refs=(ref,),
        selected_weights={canonical_digest(ref): 1.0},
        budget_digest="budget",
        selection_input_digest="selector-input",
        feature_snapshot_id="feature-snapshot",
        eligibility_mode=eligibility_mode,
        created_at=created_at,
        selection_digest="",
    )
    return record_with_digest(selection)


def _selection_variant(
    task_pool: TaskPoolRecord, selection_id: str, origin_id: str
) -> BenchmarkSelectionRecord:
    return record_with_digest(
        replace(
            _selection(task_pool),
            selection_id=selection_id,
            origin_id=origin_id,
            selection_digest="",
        )
    )


def _cell_set(
    selection: BenchmarkSelectionRecord, identity_digest: str, result: ResultRecord
) -> EvaluationCellSet:
    ref = selection.selected_task_check_refs[0]
    cell_set = EvaluationCellSet(
        cell_set_id="cell-set",
        origin_id=selection.origin_id,
        selection_id=selection.selection_id,
        selected_task_check_refs=(ref,),
        future_task_check_refs=(ref,),
        future_censored_task_check_refs=(),
        future_task_pool_id=selection.task_pool_id,
        future_task_pool_digest=selection.task_pool_digest,
        cells=(
            ResultCellRef(
                "agent",
                ref.task_id,
                ref.check_id,
                identity_digest,
                result.result_id,
                result.result_digest,
                "result",
                None,
                result.outcome,
            ),
        ),
        abstention_reason=None,
        cell_set_digest="",
    )
    return record_with_digest(cell_set)


def _cell_set_variant(
    selection: BenchmarkSelectionRecord,
    identity_digest: str,
    result: ResultRecord,
    cell_set_id: str,
) -> EvaluationCellSet:
    return record_with_digest(
        replace(
            _cell_set(selection, identity_digest, result),
            cell_set_id=cell_set_id,
            cell_set_digest="",
        )
    )


def _matrix(
    selection: BenchmarkSelectionRecord,
    cell_set: EvaluationCellSet,
    role: str,
    cell_state: str = "result",
    abstention_reason: str | None = None,
) -> ResultMatrix:
    join_config = ResultJoinConfig()
    cell = cell_set.cells[0]
    if cell_state == "missing":
        cell = ResultCellRef(
            cell.agent_id,
            cell.task_id,
            cell.check_id,
            cell.required_identity_digest,
            None,
            None,
            "missing",
            None,
            None,
        )
    matrix = ResultMatrix(
        matrix_id=f"matrix-{role}",
        matrix_role=role,
        origin_id=selection.origin_id,
        selection_id=selection.selection_id,
        agent_ids=("agent",),
        task_check_refs=selection.selected_task_check_refs,
        cells=(cell,),
        join_policy_digest=join_config.join_policy_digest,
        denominator_policy_digest=join_config.denominator_policy_digest,
        abstention_reason=abstention_reason,
        scoreable_state="abstained" if abstention_reason else "complete",
        matrix_digest="",
    )
    return record_with_digest(matrix)


def _matrix_variant(
    selection: BenchmarkSelectionRecord,
    cell_set: EvaluationCellSet,
    role: str,
    matrix_id: str,
) -> ResultMatrix:
    return record_with_digest(
        replace(
            _matrix(selection, cell_set, role), matrix_id=matrix_id, matrix_digest=""
        )
    )


def _metric(
    selection: BenchmarkSelectionRecord,
    cell_set: EvaluationCellSet,
    selected_matrix: ResultMatrix,
    future_matrix: ResultMatrix,
    abstention_reason: str | None = None,
) -> MetricRecord:
    metric = MetricRecord(
        metric_id="metric",
        origin_id=selection.origin_id,
        selection_id=selection.selection_id,
        evaluation_cell_set_digest=cell_set.cell_set_digest,
        selected_matrix_digest=selected_matrix.matrix_digest,
        future_matrix_digest=future_matrix.matrix_digest,
        join_policy_digest=selected_matrix.join_policy_digest,
        metric_config_digest=METRIC_CONFIG_DIGEST,
        metric_scope="aggregate",
        agent_id=None,
        agent_pair=None,
        aggregation_level="all_agents",
        budget_digest="budget",
        stratum_ref=None,
        metric_name="future_pass_rate_mae",
        metric_value=0.0,
        denominator_policy_digest=selected_matrix.denominator_policy_digest,
        completeness_state="abstained" if abstention_reason else "complete",
        abstention_reason=abstention_reason,
        computed_at="2026-01-05T00:00:00Z",
        metric_digest="",
    )
    return record_with_digest(metric)


def _selector_report_evidence_with_task_exclusion(*, partial: bool):
    kept_ref = TaskCheckRef("task", "check")
    excluded_ref = TaskCheckRef("excluded-task", "excluded-check")
    future_ref = TaskCheckRef("future-task", "future-check")
    selection = record_with_digest(
        replace(
            _selection(_task_pool()),
            selected_task_check_refs=(kept_ref, excluded_ref),
            selected_weights={
                canonical_digest(kept_ref): 1.0,
                canonical_digest(excluded_ref): 1.0,
            },
            selection_digest="",
        )
    )
    agents = ("agent", "other-agent")
    cells: list[ResultCellRef] = []
    for agent_id in agents:
        cells.append(
            ResultCellRef(
                agent_id,
                kept_ref.task_id,
                kept_ref.check_id,
                f"{agent_id}-kept-identity",
                f"{agent_id}-kept-result",
                f"{agent_id}-kept-digest",
                "result",
                None,
                "pass",
            )
        )
        excluded_for_agent = not partial or agent_id == "agent"
        cells.append(
            ResultCellRef(
                agent_id,
                excluded_ref.task_id,
                excluded_ref.check_id,
                f"{agent_id}-excluded-identity",
                f"{agent_id}-excluded-result",
                f"{agent_id}-excluded-digest",
                "excluded" if excluded_for_agent else "result",
                "task_check_infrastructure_failure" if excluded_for_agent else None,
                "invalid" if excluded_for_agent else "pass",
            )
        )
        cells.append(
            ResultCellRef(
                agent_id,
                future_ref.task_id,
                future_ref.check_id,
                f"{agent_id}-future-identity",
                f"{agent_id}-future-result",
                f"{agent_id}-future-digest",
                "result",
                None,
                "pass",
            )
        )
    cell_set = record_with_digest(
        EvaluationCellSet(
            cell_set_id="cell-set-with-exclusion",
            origin_id=selection.origin_id,
            selection_id=selection.selection_id,
            selected_task_check_refs=(kept_ref, excluded_ref),
            future_task_check_refs=(future_ref,),
            future_censored_task_check_refs=(),
            future_task_pool_id=selection.task_pool_id,
            future_task_pool_digest=selection.task_pool_digest,
            cells=tuple(cells),
            abstention_reason=None,
            cell_set_digest="",
        )
    )
    selected_refs = {
        (kept_ref.task_id, kept_ref.check_id),
        (excluded_ref.task_id, excluded_ref.check_id),
    }
    selected_matrix = record_with_digest(
        ResultMatrix(
            matrix_id="matrix-selected-with-exclusion",
            matrix_role="selected",
            origin_id=selection.origin_id,
            selection_id=selection.selection_id,
            agent_ids=agents,
            task_check_refs=(kept_ref, excluded_ref),
            cells=tuple(
                cell for cell in cells if (cell.task_id, cell.check_id) in selected_refs
            ),
            join_policy_digest="join",
            denominator_policy_digest="denominator",
            abstention_reason=None,
            scoreable_state="complete_with_exclusions",
            matrix_digest="",
        )
    )
    future_matrix = record_with_digest(
        ResultMatrix(
            matrix_id="matrix-future-with-exclusion",
            matrix_role="future_holdout",
            origin_id=selection.origin_id,
            selection_id=selection.selection_id,
            agent_ids=agents,
            task_check_refs=(future_ref,),
            cells=tuple(
                cell
                for cell in cells
                if (cell.task_id, cell.check_id)
                == (future_ref.task_id, future_ref.check_id)
            ),
            join_policy_digest="join",
            denominator_policy_digest="denominator",
            abstention_reason=None,
            scoreable_state="complete",
            matrix_digest="",
        )
    )
    metric = record_with_digest(
        replace(
            _metric(selection, cell_set, selected_matrix, future_matrix),
            completeness_state="complete_with_exclusions",
            metric_digest="",
        )
    )
    return selection, cell_set, selected_matrix, future_matrix, metric
