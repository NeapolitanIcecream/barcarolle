from __future__ import annotations

import pytest

import phase1_task_supply_v2_generator_bakeoff as bakeoff


def v1_row() -> dict[str, object]:
    return {
        "schema_version": "barcarolle.repo_history_candidate.v1",
        "task_id": "toolz__hist__001",
        "repo_id": "toolz",
        "repo_url": "https://github.com/pytoolz/toolz.git",
        "base_commit": "e052d819b2d8dcf50f0147b5659b9a530204d05f",
        "target_commit": "e221dc5fc5be90e9819453bba9ee621ea9193759",
        "task_time": "2018-05-16T21:43:35+02:00",
        "subject": "implement Compose.__repr__",
        "changed_files": ["toolz/functoolz.py", "toolz/tests/test_functoolz.py"],
        "code_files": ["toolz/functoolz.py"],
        "test_files": ["toolz/tests/test_functoolz.py"],
        "candidate_oracle_source": ["toolz/tests/test_functoolz.py"],
        "source_type": "git_commit",
        "status": "selected_for_certification",
    }


def test_v1_row_maps_to_valid_task_source_candidate_v2() -> None:
    candidate = bakeoff.v1_row_to_candidate(
        v1_row(),
        context={
            "repo_id": "toolz",
            "ref": "issue:397",
            "source_kind": "issue",
            "source_context_status": "non_leaky_context_found",
            "summary": "Compose representation is unclear.",
        },
    )

    assert candidate["schema_version"] == bakeoff.CANDIDATE_SCHEMA_VERSION
    assert candidate["source_reservoir"] == "repo_history_v1_commit_with_tests"
    assert candidate["oracle"]["fail_to_pass"] == ["toolz/tests/test_functoolz.py"]
    assert candidate["gold_patch_exposed_to_solver"] is False
    assert candidate["public_context_refs"] == ["issue:397"]


def test_validate_candidate_rejects_gold_patch_exposed_to_solver() -> None:
    candidate = bakeoff.v1_row_to_candidate(v1_row())
    candidate["gold_patch_exposed_to_solver"] = True

    with pytest.raises(ValueError, match="gold_patch_exposed_to_solver"):
        bakeoff.validate_candidate(candidate)


def test_validate_candidate_rejects_raw_artifact_outside_ignored_paths() -> None:
    candidate = bakeoff.v1_row_to_candidate(v1_row())
    candidate["raw_artifact_paths_uncommitted"] = ["experiments/phase1_compiler/results/raw.log"]

    with pytest.raises(ValueError, match="raw artifact path"):
        bakeoff.validate_candidate(candidate)


@pytest.mark.parametrize(
    ("subject", "expected"),
    [
        ("fix #123 by handling None", True),
        ("Resolve issue 42 in parser", True),
        ("refactor internals", False),
    ],
)
def test_is_linkable_subject_detects_issue_style_refs(subject: str, expected: bool) -> None:
    assert bakeoff.is_linkable_subject(subject) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("reference_install_failed", "install_failed"),
        ("reference_import_failed", "import_failed"),
        ("reference_collect_failed", "collect_failed"),
        ("reference_assert_failed", "reference_assert_failed"),
        ("reference_timeout", "timeout"),
        ("reference_environment_unavailable", "environment_unavailable"),
        ("reference_pass", "reference_pass"),
        ("unexpected", "unknown_failed"),
    ],
)
def test_normalize_subgate_label_uses_bakeoff_taxonomy(raw: str, expected: str) -> None:
    assert bakeoff.normalize_subgate_label(raw) == expected


def test_attempt_subgate_label_does_not_treat_old_reference_gate_failure_as_success() -> None:
    known = {"first_failing_gate": "reference_pass"}

    assert bakeoff.attempt_subgate_label({}, "certified") == "reference_pass"
    assert bakeoff.attempt_subgate_label(known, "near_certified") == "unknown_failed"
    assert (
        bakeoff.attempt_subgate_label(
            known,
            "near_certified",
            {"terminal_subgate_label": "reference_collect_failed"},
        )
        == "collect_failed"
    )


def test_classify_context_quality_keeps_commit_message_separate_from_issue_context() -> None:
    commit_only = bakeoff.v1_row_to_candidate(v1_row())
    issue_context = bakeoff.v1_row_to_candidate(
        v1_row(),
        context={"ref": "issue:397", "source_kind": "issue", "source_context_status": "non_leaky_context_found"},
    )

    assert bakeoff.classify_context_quality(commit_only) == "commit_message_only_context"
    assert bakeoff.classify_context_quality(issue_context) == "non_leaky_issue_or_pr_context"


def test_reservoir_for_commit_separates_changed_tests_from_missing_oracle_issue_candidates() -> None:
    with_tests = {"has_code": True, "has_tests": True, "linkable": False}
    linked_with_tests = {"has_code": True, "has_tests": True, "linkable": True}
    linked_without_tests = {"has_code": True, "has_tests": False, "linkable": True}

    assert bakeoff.reservoir_for_commit(with_tests) == "repo_history_v2_commit_with_tests"
    assert bakeoff.reservoir_for_commit(linked_with_tests) == "repo_history_v2_pr_issue_with_tests"
    assert bakeoff.reservoir_for_commit(linked_without_tests) == "repo_history_v2_issue_without_changed_tests"
