from __future__ import annotations

import phase1_source_certification_hardening as hardening


def test_commit_message_fallback_source_is_diagnostic_only() -> None:
    config = hardening.default_hardening_config()
    task = {"task_id": "humanize__hist__002", "repo_id": "humanize", "status": "certified"}
    context = {"source_kind": "commit_message_fallback", "ref": "commit:abc123", "classification": "problem_context"}

    row = hardening.source_overlay_row(task, context, config)

    assert row["phase1_source_tier"] == "diagnostic_only_source"
    assert row["benchmark_grade_eligible"] is False
    assert row["reason"] == "commit_message_fallback_only"


def test_commit_message_fallback_for_replacement_repo_is_diagnostic_only() -> None:
    config = hardening.default_hardening_config()
    task = {"task_id": "boltons__hist__002", "repo_id": "boltons", "status": "certified"}
    context = {"source_kind": "commit_message_fallback", "ref": "commit:abc123", "classification": "diagnostic_only_context"}

    row = hardening.source_overlay_row(task, context, config)

    assert row["phase1_source_tier"] == "diagnostic_only_source"
    assert row["benchmark_grade_eligible"] is False


def test_issue_or_pr_problem_context_can_be_benchmark_grade_source() -> None:
    config = hardening.default_hardening_config()
    task = {"task_id": "toolz__hist__001", "repo_id": "toolz", "status": "certified"}
    context = {
        "source_items": [
            {
                "kind": "issue",
                "leakage_class": "problem_context",
                "solver_usable": True,
                "source_id": "issue:397",
            }
        ]
    }

    row = hardening.source_overlay_row(task, context, config)

    assert row["phase1_source_tier"] == "benchmark_grade_source"
    assert row["benchmark_grade_eligible"] is True
    assert row["source_kind"] == "issue"


def test_oracle_alignment_flags_statement_repo_mismatch() -> None:
    task = {
        "repo_id": "itsdangerous",
        "task_id": "itsdangerous__hist__010",
        "status": "certified",
        "gates": {"no_op_fail": "pass", "reference_pass": "pass"},
        "solver_facing_statement": "Repair the humanize behavior described by the selected public context summary.",
        "subject": "access sha1 lazily",
        "changed_files": ["src/itsdangerous/signer.py", "tests/test_itsdangerous/test_serializer.py"],
        "code_files": ["src/itsdangerous/signer.py"],
        "test_files": ["tests/test_itsdangerous/test_serializer.py"],
    }

    row = hardening.oracle_alignment_row(task, "benchmark_grade_source")

    assert row["oracle_alignment_status"] == "manual_review_required"
    assert "statement_source_mismatch" in row["risk_flags"]


def test_candidate_filter_rejects_maintenance_project_file_churn() -> None:
    config = hardening.default_hardening_config()
    task = {
        "task_id": "itsdangerous__hist__009",
        "subject": "update project files",
        "changed_lines_added": 467,
        "changed_lines_deleted": 350,
        "changed_files": [".github/workflows/tests.yaml", "pyproject.toml", "src/itsdangerous/timed.py"],
        "code_files": ["src/itsdangerous/timed.py"],
    }

    row = hardening.candidate_filter_row(task, config)

    assert row["candidate_filter_status"] == "rejected"
    assert "reject_subject_term:update project files" in row["reject_reasons"]
    assert "changed_lines_over:250" in row["reject_reasons"]


def test_current_humanize_certified_tasks_remain_diagnostic_only() -> None:
    payload = hardening.build_all_payloads(use_github=False, run_environment_probes=False, generated_at="2026-05-22T00:00:00+00:00")
    humanize_summary = payload["source_overlay"]["repo_summary"]["humanize"]
    toolz_summary = payload["source_overlay"]["repo_summary"]["toolz"]

    assert humanize_summary["certified_count"] == 12
    assert humanize_summary["source_tier_counts"]["diagnostic_only_source"] == 16
    assert humanize_summary["benchmark_grade_eligible_count"] == 0
    assert toolz_summary["benchmark_grade_eligible_count"] == 6


def test_humanize_hardened_repair_falls_back_to_diagnostic_commit_context_without_github() -> None:
    rows, summary = hardening.build_humanize_hardened_sources(use_github=False, generated_at="2026-05-22T00:00:00+00:00")

    assert len(rows) == 12
    assert summary["decision_counts"]["diagnostic_only_commit_fallback"] == 11
    assert summary["decision_counts"]["manual_review_required"] == 1
    assert summary["repaired_to_problem_context_count"] == 0
    assert summary["humanize_decision"] == "humanize_source_blocker_confirmed_operational_pilot_only"


def test_primary_decision_reports_certification_bug_when_statement_mismatch_exists() -> None:
    label = hardening.choose_primary_decision(
        humanize_repaired_count=0,
        source_overlay={"repo_summary": {}},
        oracle_audit={"summary": {"risk_flag_counts": {"statement_source_mismatch": 11}}},
        environment_diagnosis={"summary": {"supported_decisions": ["environment_synthesis_mismatch"]}},
        hardened_overlay={"repo_summary": {}},
    )

    assert label == "certification_implementation_bug_found"


def test_primary_decision_replaces_third_repo_when_oracle_weakness_remains_after_template_repair() -> None:
    label = hardening.choose_primary_decision(
        humanize_repaired_count=0,
        source_overlay={"repo_summary": {}},
        oracle_audit={"summary": {"risk_flag_counts": {"statement_source_mismatch": 0}}},
        environment_diagnosis={"summary": {"supported_decisions": ["oracle_weakness"]}},
        hardened_overlay={"repo_summary": {"itsdangerous": {"benchmark_grade_candidate_count": 0}, "toolz": {"benchmark_grade_candidate_count": 6}}},
    )

    assert label == "replace_third_repo_before_paid_acut"


def test_selected_replacement_repo_is_active_and_itsdangerous_is_replaced() -> None:
    selection = {
        "active_selection": {
            "repo_id": "boltons",
            "selection_status": "selected_local_pilot",
            "replacement_for": "itsdangerous",
        }
    }

    assert hardening.repo_ids_for_hardening(selection) == ("toolz", "humanize", "boltons")
    assert hardening.replaced_repo_summary(selection) == {"itsdangerous": {"replacement_status": "replaced_by_boltons"}}


def test_selected_replacement_repo_appears_in_empty_source_overlay_summary(monkeypatch) -> None:
    monkeypatch.setattr(hardening, "load_repo_rows", lambda repo_id, include_near=True: [])
    monkeypatch.setattr(hardening, "load_contexts", lambda repo_id: {})

    payload = hardening.build_source_provenance_overlay(
        hardening.default_hardening_config(),
        "2026-05-22T00:00:00+00:00",
        repo_ids=("toolz", "humanize", "boltons"),
    )

    assert set(payload["repo_summary"]) == {"toolz", "humanize", "boltons"}
    assert payload["predictive_validity_established"] is False
