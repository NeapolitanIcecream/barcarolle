import json
from dataclasses import replace

import pytest

from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    EvaluationCellSet,
    MetricRecord,
    ResultCacheIdentity,
    ResultCellRef,
    ResultMatrix,
    ResultRecord,
    TaskCheckRef,
    TaskPoolRecord,
    canonical_digest,
    record_with_digest,
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


def test_task_pool_and_result_reports_summarize_existing_records() -> None:
    task_pool = _task_pool()
    result_pass = _result(outcome="pass", terminal_status="passed", total_cost=1.25, workspace_seconds=3.0)
    result_fail = _result(result_id="result-fail", outcome="fail", terminal_status="failed", total_cost=0.75, workspace_seconds=5.0)

    task_section = build_task_pool_report(task_pool)
    result_section = build_result_report((result_pass, result_fail), (_agent(),))

    assert task_section.summary["task_count"] == 1
    assert task_section.summary["check_count"] == 1
    assert task_section.source_digests["task_pool_digest"] == task_pool.task_pool_digest
    assert task_section.artifact_paths == ("tasks.jsonl", "checks.jsonl")
    assert task_section.unsupported_claims == ()
    assert result_section.summary["outcome_counts"] == {"fail": 1, "pass": 1}
    assert result_section.summary["scoreable_state_counts"] == {"scoreable": 2}
    assert result_section.summary["failure_label_counts"] == {"none": 2}
    assert result_section.summary["invalid_owner_counts"] == {"none": 2}
    assert result_section.summary["total_cost"] == 2.0
    assert result_section.summary["latency"]["mean_workspace_seconds"] == 4.0
    assert result_pass.result_digest in result_section.source_digests["result_digests"]


def test_result_report_rejects_agent_identity_drift() -> None:
    result = _result_with_wrong_agent_identity(_result())

    section = build_result_report((result,), (_agent(),))

    assert section.supported_claims == ()
    assert any("cache identity does not match Agent" in claim for claim in section.unsupported_claims)


def test_result_report_does_not_support_empty_evidence() -> None:
    section = build_result_report((), ())

    assert section.supported_claims == ()
    assert "result evidence is absent" in section.unsupported_claims


def test_result_report_rejects_non_numeric_cost_and_latency() -> None:
    result = record_with_digest(
        replace(
            _result(),
            cost={"total_cost": "12.5"},
            latency={"workspace_seconds": "7"},
            result_digest="",
        )
    )

    section = build_result_report((result,), (_agent(),))

    assert section.supported_claims == ()
    assert "result result cost.total_cost is non-numeric" in section.unsupported_claims
    assert "result result latency.workspace_seconds is non-numeric" in section.unsupported_claims


def test_result_report_distinguishes_unknown_cost_from_measured_zero() -> None:
    measured_zero = _result(result_id="result-zero", total_cost=0.0)
    unknown = record_with_digest(
        replace(
            _result(result_id="result-unknown", total_cost=None),
            usage={},
            usage_coverage="unknown",
            result_digest="",
        )
    )

    section = build_result_report((measured_zero, unknown), (_agent(),))

    assert section.summary["total_cost"] == 0.0
    assert section.summary["cost_coverage"] == {
        "measured_result_count": 1,
        "measured_zero_cost_count": 1,
        "unknown_result_count": 1,
    }
    assert section.summary["usage_coverage"] == {"reported": 1, "unknown": 1}
    assert section.unsupported_claims == ()


def test_selector_report_preserves_matrix_cell_set_and_metric_traceability() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)

    section = build_selector_report((selection,), (cell_set,), (selected_matrix, future_matrix), (metric,))

    assert section.unsupported_claims == ()
    assert section.summary["selection_count"] == 1
    assert section.summary["selections"][0]["matrix_roles"] == ("future_holdout", "selected")
    assert section.summary["selections"][0]["agent_ids"] == ("agent",)
    assert section.summary["selections"][0]["cell_set_digests"] == (cell_set.cell_set_digest,)
    assert section.summary["selections"][0]["matrices"][0]["matrix_digest"] == future_matrix.matrix_digest
    assert section.summary["selections"][0]["matrices"][1]["matrix_digest"] == selected_matrix.matrix_digest
    assert section.summary["selections"][0]["metrics"][0]["metric_value"] == 0.0
    assert section.summary["selections"][0]["metrics"][0]["selected_matrix_digest"] == selected_matrix.matrix_digest
    assert section.summary["selections"][0]["metrics"][0]["future_matrix_digest"] == future_matrix.matrix_digest
    assert metric.metric_digest in section.source_digests["metric_digests"]
    assert selected_matrix.matrix_digest in section.source_digests["matrix_digests"]
    assert cell_set.cell_set_digest in section.source_digests["cell_set_digests"]


def test_selector_report_rejects_metric_without_selection_budget_binding() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = record_with_digest(
        replace(_metric(selection, cell_set, selected_matrix, future_matrix), budget_digest=None, metric_digest="")
    )

    section = build_selector_report((selection,), (cell_set,), (selected_matrix, future_matrix), (metric,))

    assert any("budget digest does not match" in claim for claim in section.unsupported_claims)


def test_selector_report_does_not_support_empty_evidence() -> None:
    section = build_selector_report((), (), (), ())

    assert section.supported_claims == ()
    assert "selector performance evidence is absent or incomplete" in section.unsupported_claims


def test_selector_report_preserves_and_rejects_cell_set_abstention() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = record_with_digest(
        replace(_cell_set(selection, result.cache_identity.identity_digest, result), abstention_reason="missing_required_results", cell_set_digest="")
    )
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)

    section = build_selector_report((selection,), (cell_set,), (selected_matrix, future_matrix), (metric,))
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (metric,),
        ClaimConfig("claims"),
        results=(result,),
    )

    assert section.supported_claims == ()
    assert section.summary["selections"][0]["cell_set_abstention_reasons"] == ("missing_required_results",)
    assert any("cell_set cell-set abstained" in claim for claim in section.unsupported_claims)
    assert any(claim.startswith("selector_metrics:") for claim in claim_section.unsupported_claims)


def test_selector_report_rejects_unfrozen_selection_performance_support() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool, exposure_state="draft")
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)

    section = build_selector_report((selection,), (cell_set,), (selected_matrix, future_matrix), (metric,))

    assert section.supported_claims == ()
    assert any("selection selection exposure_state is draft" in claim for claim in section.unsupported_claims)


def test_selector_and_claim_reports_reject_incomplete_matrix_without_abstention() -> None:
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
        replace(selected_matrix, cells=(missing_cell,), scoreable_state="incomplete", matrix_digest="")
    )
    metric = _metric(selection, cell_set, incomplete_selected_matrix, future_matrix)

    selector_section = build_selector_report((selection,), (cell_set,), (incomplete_selected_matrix, future_matrix), (metric,))
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (incomplete_selected_matrix, future_matrix),
        (metric,),
        ClaimConfig("claims"),
        results=(result,),
    )

    assert selector_section.supported_claims == ()
    assert any("scoreable_state is incomplete" in claim for claim in selector_section.unsupported_claims)
    assert any("contains non-result cells: missing=1" in claim for claim in selector_section.unsupported_claims)
    assert any(claim.startswith("selector_metrics:") for claim in claim_section.unsupported_claims)


def test_selector_and_claim_reports_reject_incomplete_metric_without_abstention() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)
    incomplete_metric = record_with_digest(replace(metric, completeness_state="incomplete", metric_digest=""))

    selector_section = build_selector_report((selection,), (cell_set,), (selected_matrix, future_matrix), (incomplete_metric,))
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (incomplete_metric,),
        ClaimConfig("claims"),
        results=(result,),
    )

    assert selector_section.supported_claims == ()
    assert any("completeness_state is incomplete" in claim for claim in selector_section.unsupported_claims)
    assert any(claim.startswith("selector_metrics:") for claim in claim_section.unsupported_claims)


def test_selector_and_claim_reports_require_metrics_for_each_selection() -> None:
    task_pool = _task_pool()
    result = _result()
    first_selection = _selection(task_pool)
    second_selection = _selection_variant(task_pool, selection_id="selection-without-metric", origin_id="origin-without-metric")
    first_cell_set = _cell_set(first_selection, result.cache_identity.identity_digest, result)
    second_cell_set = _cell_set_variant(second_selection, result.cache_identity.identity_digest, result, cell_set_id="cell-set-without-metric")
    first_selected_matrix = _matrix(first_selection, first_cell_set, role="selected")
    first_future_matrix = _matrix(first_selection, first_cell_set, role="future_holdout")
    second_selected_matrix = _matrix_variant(second_selection, second_cell_set, role="selected", matrix_id="matrix-selected-without-metric")
    second_future_matrix = _matrix_variant(second_selection, second_cell_set, role="future_holdout", matrix_id="matrix-future-without-metric")
    first_metric = _metric(first_selection, first_cell_set, first_selected_matrix, first_future_matrix)

    selector_section = build_selector_report(
        (first_selection, second_selection),
        (first_cell_set, second_cell_set),
        (first_selected_matrix, first_future_matrix, second_selected_matrix, second_future_matrix),
        (first_metric,),
    )
    claim_section = build_claim_boundary(
        task_pool,
        (first_selection, second_selection),
        (first_cell_set, second_cell_set),
        (first_selected_matrix, first_future_matrix, second_selected_matrix, second_future_matrix),
        (first_metric,),
        ClaimConfig("claims"),
        results=(result,),
    )

    assert selector_section.supported_claims == ()
    assert any("selection selection-without-metric has no metric evidence" in claim for claim in selector_section.unsupported_claims)
    assert any(claim.startswith("selector_metrics:") for claim in claim_section.unsupported_claims)


def test_selector_and_claim_reports_reject_unlinked_metric_evidence() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)
    broken_metric = record_with_digest(replace(metric, selected_matrix_digest="missing-matrix", metric_digest=""))

    selector_section = build_selector_report((selection,), (cell_set,), (selected_matrix, future_matrix), (broken_metric,))
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (broken_metric,),
        ClaimConfig("claims"),
        results=(result,),
    )

    assert any("selected_matrix_digest is not supplied" in claim for claim in selector_section.unsupported_claims)
    assert any(claim.startswith("selector_metrics:") for claim in claim_section.unsupported_claims)


def test_selector_and_claim_reports_reject_metric_origin_drift() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)
    drift_metric = record_with_digest(replace(metric, origin_id="other-origin", metric_digest=""))

    selector_section = build_selector_report((selection,), (cell_set,), (selected_matrix, future_matrix), (drift_metric,))
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (drift_metric,),
        ClaimConfig("claims"),
        results=(result,),
    )

    assert any("origin does not match selection" in claim for claim in selector_section.unsupported_claims)
    assert any(claim.startswith("selector_metrics:") for claim in claim_section.unsupported_claims)


def test_selector_and_claim_reports_reject_matrix_cell_identity_mismatch() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    bad_cell = replace(selected_matrix.cells[0], required_identity_digest="different-identity")
    bad_selected_matrix = record_with_digest(replace(selected_matrix, cells=(bad_cell,), matrix_digest=""))
    metric = _metric(selection, cell_set, bad_selected_matrix, future_matrix)

    selector_section = build_selector_report((selection,), (cell_set,), (bad_selected_matrix, future_matrix), (metric,))
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (bad_selected_matrix, future_matrix),
        (metric,),
        ClaimConfig("claims"),
        results=(result,),
    )

    assert any("selected matrix cells do not match" in claim for claim in selector_section.unsupported_claims)
    assert any(claim.startswith("selector_metrics:") for claim in claim_section.unsupported_claims)


def test_selector_and_claim_reports_reject_matrix_result_binding_mismatch() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected")
    future_matrix = _matrix(selection, cell_set, role="future_holdout")
    bad_cell = replace(selected_matrix.cells[0], result_digest="different-result-digest")
    bad_selected_matrix = record_with_digest(replace(selected_matrix, cells=(bad_cell,), matrix_digest=""))
    metric = _metric(selection, cell_set, bad_selected_matrix, future_matrix)

    selector_section = build_selector_report((selection,), (cell_set,), (bad_selected_matrix, future_matrix), (metric,))
    claim_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (bad_selected_matrix, future_matrix),
        (metric,),
        ClaimConfig("claims"),
        results=(result,),
    )

    assert any("selected matrix cells do not match" in claim for claim in selector_section.unsupported_claims)
    assert any(claim.startswith("selector_metrics:") for claim in claim_section.unsupported_claims)


def test_claim_boundary_separates_supported_and_unsupported_claims() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool, exposure_state="draft")
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    missing_matrix = _matrix(selection, cell_set, role="selected", cell_state="missing", abstention_reason="missing_required_results")
    mismatched_result = record_with_digest(
        ResultRecord(
            **{
                **result.__dict__,
                "result_id": "result-mismatch",
                "result_digest": "",
            }
        )
    )
    metric = _metric(selection, cell_set, missing_matrix, missing_matrix, abstention_reason="missing_required_results")

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (missing_matrix,),
        (metric,),
        ClaimConfig("claims"),
        results=(mismatched_result,),
    )

    assert "task_pool_coverage" in section.supported_claims
    assert any(claim.startswith("benchmark_selection_frozen:") for claim in section.unsupported_claims)
    assert any(claim.startswith("cache_completeness:") for claim in section.unsupported_claims)
    assert any(claim.startswith("selector_metrics:") for claim in section.unsupported_claims)


def test_claim_boundary_rejects_selector_metrics_when_matrices_abstain() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool)
    cell_set = _cell_set(selection, result.cache_identity.identity_digest, result)
    selected_matrix = _matrix(selection, cell_set, role="selected", abstention_reason="missing_required_results")
    future_matrix = _matrix(selection, cell_set, role="future_holdout", abstention_reason="missing_required_results")
    metric = _metric(selection, cell_set, selected_matrix, future_matrix)

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        (metric,),
        ClaimConfig("claims"),
        results=(result,),
    )

    assert any(claim.startswith("selector_metrics:") for claim in section.unsupported_claims)


def test_claim_boundary_rejects_selector_metrics_for_unfrozen_selection() -> None:
    task_pool = _task_pool()
    result = _result()
    selection = _selection(task_pool, exposure_state="draft")
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
        ClaimConfig("claims"),
        results=(result,),
    )

    assert any(claim.startswith("selector_metrics:") for claim in section.unsupported_claims)


def test_claim_boundary_rejects_invalid_or_unbound_frozen_selection() -> None:
    task_pool = _task_pool()
    selection = _selection(task_pool)
    tampered_selection = replace(selection, selection_digest="not-canonical")
    wrong_pool_selection = record_with_digest(replace(selection, task_pool_digest="other-pool", selection_digest=""))

    tampered_section = build_claim_boundary(task_pool, (tampered_selection,), (), (), (), ClaimConfig("claims"), results=())
    wrong_pool_section = build_claim_boundary(task_pool, (wrong_pool_selection,), (), (), (), ClaimConfig("claims"), results=())

    assert any(claim.startswith("benchmark_selection_frozen:") for claim in tampered_section.unsupported_claims)
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
        ClaimConfig("claims"),
        results=(result,),
    )

    assert any(claim.startswith("selector_metrics:") for claim in section.unsupported_claims)


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
    drift_matrix = record_with_digest(replace(matrix, cells=(wrong_id_cell,), matrix_digest=""))

    section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (drift_matrix,),
        (),
        ClaimConfig("claims", requested_claims=("agent_result_identity",)),
        results=(result,),
    )

    assert any(claim.startswith("agent_result_identity:") for claim in section.unsupported_claims)


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
        ClaimConfig("claims", requested_claims=("agent_result_identity",)),
        results=(result,),
    )

    assert section.supported_claims == ()
    assert any("missing result digest stale-result-digest" in claim for claim in section.unsupported_claims)


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
        ClaimConfig("claims", requested_claims=("agent_result_identity",)),
        results=(result,),
    )
    result_section = build_claim_boundary(
        task_pool,
        (selection,),
        (cell_set,),
        (matrix,),
        (),
        ClaimConfig("claims", requested_claims=("agent_result_identity",)),
        results=(invalid_result,),
    )

    assert any(claim.startswith("agent_result_identity:") for claim in matrix_section.unsupported_claims)
    assert any(claim.startswith("agent_result_identity:") for claim in result_section.unsupported_claims)


def test_task_pool_report_rejects_missing_audit_fields() -> None:
    bad_pool = record_with_digest(replace(_task_pool(), task_records_ref="", task_pool_digest=""))

    section = build_task_pool_report(bad_pool)
    claim_section = build_claim_boundary(bad_pool, (), (), (), (), ClaimConfig("claims"), results=())

    assert any("task_records_ref is missing" in claim for claim in section.unsupported_claims)
    assert any(claim.startswith("task_pool_coverage:") for claim in claim_section.unsupported_claims)


def test_claim_boundary_does_not_support_claims_without_evidence() -> None:
    section = build_claim_boundary(
        _task_pool(),
        (),
        (),
        (),
        (),
        ClaimConfig("claims"),
        results=(),
    )

    assert "task_pool_coverage" in section.supported_claims
    assert any(claim.startswith("benchmark_selection_frozen:") for claim in section.unsupported_claims)
    assert any(claim.startswith("cache_completeness:") for claim in section.unsupported_claims)
    assert any(claim.startswith("selector_metrics:") for claim in section.unsupported_claims)
    assert any(claim.startswith("agent_result_identity:") for claim in section.unsupported_claims)


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
    assert payload[0]["artifact_paths"] == ["tasks.jsonl", "checks.jsonl"]


def test_write_report_sanitizes_local_absolute_artifact_paths(tmp_path) -> None:
    artifact = tmp_path / "runs" / "workspace-run" / "stdout.txt"
    section = ReportSection(
        section_id="artifacts",
        heading="Artifacts",
        summary={"task_records_ref": str(artifact), "nested": {"refs": (str(artifact),)}},
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
        rejected_candidate_ids=("rejected",),
        rejection_summary_digest="rejection-summary",
        certification_evidence_digest="certification-evidence",
        source_event_inventory_digest="source-events",
        generator_config_digest="generator",
        certification_config_digest="certification",
        created_at="2026-01-01T00:00:00Z",
    )
    return record_with_digest(record)


def _agent() -> AgentRecord:
    return AgentRecord(
        agent_id="agent",
        agent_manifest_digest="agent-manifest",
        model_snapshot_id="model",
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
    identity = ResultCacheIdentity(
        task_id="task",
        check_id="check",
        repository_id="repo",
        base_commit="commit",
        submodule_state_digest="submodules",
        solver_material_digest="solver",
        check_digest="check",
        agent_manifest_digest="agent-manifest",
        model_snapshot_id="model",
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
        result_id=result_id,
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
        usage_coverage="reported",
        latency={"workspace_seconds": workspace_seconds},
        diff_digest="diff",
        verifier_metadata_digest="verifier",
        started_at="2026-01-04T00:00:00Z",
        finished_at="2026-01-04T00:00:01Z",
        result_available_at="2026-01-04T00:00:02Z",
    )
    return record_with_digest(result)


def _result_with_wrong_agent_identity(result: ResultRecord) -> ResultRecord:
    cache_identity = record_with_digest(
        replace(
            result.cache_identity,
            agent_manifest_digest="other-agent-manifest",
            identity_digest="",
        )
    )
    return record_with_digest(replace(result, cache_identity=cache_identity, result_digest=""))


def _selection(task_pool: TaskPoolRecord, exposure_state: str = "frozen") -> BenchmarkSelectionRecord:
    ref = TaskCheckRef("task", "check")
    selection = BenchmarkSelectionRecord(
        selection_id="selection",
        task_pool_id=task_pool.task_pool_id,
        task_pool_digest=task_pool.task_pool_digest,
        origin_id="origin",
        selector_id="selector",
        selected_task_check_refs=(ref,),
        selected_weights={canonical_digest(ref): 1.0},
        budget_digest="budget",
        selection_input_digest="selector-input",
        feature_snapshot_id="feature-snapshot",
        eligibility_mode="strict_history",
        exposure_state=exposure_state,
        exposed_at=None,
        exposure_scope_digest=None,
        created_at="2026-01-05T00:00:00Z",
        selection_digest="",
    )
    return record_with_digest(selection)


def _selection_variant(task_pool: TaskPoolRecord, selection_id: str, origin_id: str) -> BenchmarkSelectionRecord:
    return record_with_digest(replace(_selection(task_pool), selection_id=selection_id, origin_id=origin_id, selection_digest=""))


def _cell_set(selection: BenchmarkSelectionRecord, identity_digest: str, result: ResultRecord) -> EvaluationCellSet:
    ref = selection.selected_task_check_refs[0]
    cell_set = EvaluationCellSet(
        cell_set_id="cell-set",
        origin_id=selection.origin_id,
        selection_id=selection.selection_id,
        selected_task_check_refs=(ref,),
        future_task_check_refs=(ref,),
        cells=(
            ResultCellRef("agent", ref.task_id, ref.check_id, identity_digest, result.result_id, result.result_digest, "result", None, result.outcome),
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
    return record_with_digest(replace(_cell_set(selection, identity_digest, result), cell_set_id=cell_set_id, cell_set_digest=""))


def _matrix(
    selection: BenchmarkSelectionRecord,
    cell_set: EvaluationCellSet,
    role: str,
    cell_state: str = "result",
    abstention_reason: str | None = None,
) -> ResultMatrix:
    cell = cell_set.cells[0]
    if cell_state == "missing":
        cell = ResultCellRef(cell.agent_id, cell.task_id, cell.check_id, cell.required_identity_digest, None, None, "missing", None, None)
    matrix = ResultMatrix(
        matrix_id=f"matrix-{role}",
        matrix_role=role,
        origin_id=selection.origin_id,
        selection_id=selection.selection_id,
        agent_ids=("agent",),
        task_check_refs=selection.selected_task_check_refs,
        cells=(cell,),
        join_policy_digest="join",
        denominator_policy_digest="denominator",
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
    return record_with_digest(replace(_matrix(selection, cell_set, role), matrix_id=matrix_id, matrix_digest=""))


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
        metric_config_digest="metric-config",
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
