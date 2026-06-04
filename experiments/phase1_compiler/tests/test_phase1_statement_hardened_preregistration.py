from __future__ import annotations

import copy

import phase1_statement_hardened_preregistration as prereg


def base_record() -> dict:
    record = {
        "allowed_context_refs": ["issue:123"],
        "certification_gate_summary": {
            "all_pass": True,
            "failed_gates": [],
            "gate_count": 3,
            "gate_counts": {"pass": 3},
        },
        "historical_paid_context": {"historical_paid_cells_present": False, "used_for_selection": False},
        "implementation_files": ["pkg/core.py"],
        "problem_context_manual_review_rationale": "",
        "release_split_eligibility": ["B_eval", "H_future"],
        "repo_id": "demo",
        "source_context_status": "non_leaky_problem_context",
        "source_kind": "issue",
        "source_ref": "issue:123",
        "statement_quality_gate": "pass",
        "statement_quality_risk_reasons": [],
        "task_id": "demo__001",
        "task_time": "2024-01-01T00:00:00+00:00",
        "test_files": ["tests/test_core.py"],
    }
    return record


def test_old_cap_truncation_is_rejected_from_selection() -> None:
    context = {
        "classification": "problem_context",
        "ref": "issue:123",
        "summary": "Broken public behavior",
        "body_summary": ("Reproduce with: ```python\nassert broken(" + ("x" * 260))[:240],
    }
    quality = prereg.statement_quality_record(
        context=context,
        row={"source_context_status": "non_leaky_problem_context", "target_commit": "abc"},
        impl_files=["pkg/core.py"],
        tests=["tests/test_core.py"],
    )
    record = base_record()
    record["statement_quality_gate"] = quality["normalized_statement_quality_gate"]
    record["statement_quality_risk_reasons"] = quality["risk_reasons"]

    eligible, reasons = prereg.is_candidate_eligible(record)

    assert eligible is False
    assert "statement_quality_risk:statement_probably_truncated" in reasons


def test_implementation_scope_excludes_tests_and_generated_metadata() -> None:
    row = {
        "changed_files": [
            "pkg/core.py",
            "tests/test_core.py",
            "docs/generated.json",
            "pyproject.toml",
        ],
        "test_files": ["tests/test_core.py"],
    }

    assert prereg.implementation_files_for(row) == ["pkg/core.py"]


def test_statement_digest_changes_when_visible_text_changes() -> None:
    left = prereg.digest_text("Problem summary: old behavior")
    right = prereg.digest_text("Problem summary: new behavior")

    assert left != right


def test_paid_outcome_fields_do_not_affect_selection() -> None:
    records = []
    for index in range(1, 5):
        record = base_record()
        record["task_id"] = f"demo__{index:03d}"
        record["task_time"] = f"2024-01-0{index}T00:00:00+00:00"
        record["historical_paid_context"] = {
            "historical_paid_cells_present": True,
            "terminal_status_counts": {"verified_pass": index},
            "used_for_selection": False,
        }
        records.append(record)
    flipped = copy.deepcopy(records)
    for record in flipped:
        record["historical_paid_context"]["terminal_status_counts"] = {"verified_fail": 99}

    selected_a, _ = prereg.select_release_candidates(
        records,
        repos=["demo"],
        splits=["B_eval"],
        tasks_per_repo_split=2,
    )
    selected_b, _ = prereg.select_release_candidates(
        flipped,
        repos=["demo"],
        splits=["B_eval"],
        tasks_per_repo_split=2,
    )

    assert selected_a == selected_b == {"demo/B_eval": ["demo__001", "demo__002"]}


def test_pr_context_requires_problem_rationale_or_linked_issue() -> None:
    record = base_record()
    record["source_kind"] = "pull_request"
    record["source_ref"] = "pr:456"

    eligible, reasons = prereg.is_candidate_eligible(record)

    assert eligible is False
    assert "pr_context_requires_problem_rationale_or_linked_issue" in reasons


def test_pr_context_with_linked_issue_gets_manual_review_rationale() -> None:
    context = {
        "classification": "problem_context",
        "ref": "pr:456",
        "summary": "Fixes #123",
        "body_summary": "This public PR points to the user-visible bug tracked in issue #123.",
    }

    rationale = prereg.problem_context_rationale(
        source_ref="pr:456",
        context=context,
        quality={"statement_probably_truncated": False},
    )

    assert "issue:123" in rationale


def test_strict_gates_produce_blocker_when_release_is_underfilled() -> None:
    config = {
        "_path": "config.yaml",
        "created_at": "2026-05-25T00:00:00Z",
        "output_paths": {"preflight": "missing.json"},
        "selection": {
            "minimum_repo_count": 2,
            "planned_adapters": ["codex_workspace", "kilo_workspace"],
            "preferred_repos": ["demo", "other"],
            "preferred_splits": ["B_eval", "H_future"],
            "tasks_per_repo_split": 2,
        },
    }
    inventory = {"candidates": [base_record()]}

    screen = prereg.build_candidate_screen(config, inventory)
    blocker = prereg.build_blocker(config, screen)

    assert screen["feasibility"]["two_repo_statement_hardened_release"] is False
    assert blocker["status"] == "replacement_supply_needed"
    assert blocker["predictive_validity_established"] is False
