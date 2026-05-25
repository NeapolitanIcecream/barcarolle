from __future__ import annotations

from pathlib import Path

import phase1_attrs_statement_quality_audit as audit


REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG = REPO_ROOT / "experiments" / "phase1_compiler" / "configs" / "phase1_attrs_h_future_statement_quality_audit.yaml"


def capped_summary(text: str) -> str:
    return (text + " " + ("x" * 240))[:240]


def test_old_cap_summary_ending_inside_code_fence_is_truncation_risk() -> None:
    body = capped_summary("Reproduce with: ```python import attr class C: def __setattr__(self, key, value):")

    flags = audit.statement_quality_flags(
        source_ref="issue:680",
        title="slots class overrides custom setattr",
        body_summary=body,
        implementation_files=["src/attr/_make.py"],
        test_files=["tests/test_setattr.py"],
    )

    assert flags["body_summary_hit_old_cap"] is True
    assert flags["statement_ends_mid_code_fence"] is True
    assert flags["statement_probably_truncated"] is True
    assert flags["statement_quality_gate"] == "material_risk"


def test_short_complete_issue_summary_is_not_flagged_as_truncated() -> None:
    flags = audit.statement_quality_flags(
        source_ref="issue:319",
        title="date_range handles December steps incorrectly",
        body_summary="Minimal reproduction: date_range should include the expected December year boundary.",
        implementation_files=["boltons/timeutils.py"],
        test_files=["tests/test_timeutils.py"],
    )

    assert flags["body_summary_hit_old_cap"] is False
    assert flags["statement_probably_truncated"] is False
    assert flags["statement_underspecified_risk"] is False
    assert flags["statement_quality_gate"] == "pass"


def test_pr_context_task_gets_pr_context_risk() -> None:
    flags = audit.statement_quality_flags(
        source_ref="pr:687",
        title="NG: make frozen classes comfortably subclassable",
        body_summary=capped_summary("This fixes an inconvenience in frozen subclass handling."),
        implementation_files=["src/attr/_next_gen.py"],
        test_files=["tests/test_next_gen.py"],
    )

    assert flags["pr_context_risk"] is True
    assert "pr_context_source" in flags["risk_reasons"]
    assert flags["statement_quality_gate"] == "material_risk"


def test_policy_violation_is_not_treated_as_scoreable_fail() -> None:
    outcomes = audit.adapter_outcome_summary(
        [
            {
                "adapter_id": "codex_workspace",
                "terminal_status": "verified_fail",
                "scoreable_cell": True,
                "verified_pass": False,
            },
            {
                "adapter_id": "kilo_workspace",
                "terminal_status": "policy_violation",
                "scoreable_cell": False,
                "verified_pass": False,
            },
        ]
    )

    assert outcomes["scoreable_pass_count"] == 0
    assert outcomes["scoreable_fail_count"] == 1
    assert outcomes["policy_violation_count"] == 1
    assert outcomes["adapter_outcomes"]["kilo_workspace"] == "policy_violation"


def test_severe_statement_risk_is_machine_readable() -> None:
    flags = audit.statement_quality_flags(
        source_ref="issue:593",
        title="Deferred type annotations are evaluated in the wrong execution context",
        body_summary=capped_summary("Expected result: ``` {'return': <class 'NoneType"),
        implementation_files=["src/attr/_make.py"],
        test_files=["tests/test_annotations.py"],
    )

    assert flags["statement_quality_gate"] == "material_risk"
    assert flags["diagnostics"]["risk_flag_count"] >= 2
    assert flags["diagnostics"]["failure_signal"] == "statement_quality_risk_detected"


def test_sensitivity_preserves_original_attrs_h_future_metric() -> None:
    config = audit.load_config(CONFIG)
    task_audit = audit.build_task_design_audit(config)

    sensitivity = audit.build_statement_sensitivity(config, task_audit)

    original = sensitivity["views"]["original_attrs_h_future"]
    assert original["scoreable_cells"] == 7
    assert original["verified_pass"] == 1
    assert original["verified_fail"] == 6
    assert original["policy_violations"] == 1
    assert original["pass_rate"] == 0.142857
    assert original["comparison_to_attrs_b_eval"]["attrs_b_eval_pass_rate"] == 0.875


def test_sensitivity_reports_insufficient_clean_attrs_h_future_evidence() -> None:
    config = audit.load_config(CONFIG)
    task_audit = audit.build_task_design_audit(config)

    sensitivity = audit.build_statement_sensitivity(config, task_audit)

    strict = sensitivity["views"]["strict_clean_statement_only"]
    assert strict["included_tasks"] == []
    assert strict["scoreable_cells"] == 0
    assert strict["pass_rate"] is None
    assert strict["interpretation"] == "insufficient_clean_attrs_h_future_evidence"
