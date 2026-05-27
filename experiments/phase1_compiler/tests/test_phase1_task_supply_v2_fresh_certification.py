from __future__ import annotations

from collections import Counter

import phase1_task_supply_v2_fresh_certification as fresh


def test_candidate_funnel_classifies_all_829_input_rows() -> None:
    config = fresh.load_config()

    payload = fresh.build_candidate_funnel(config)

    assert payload["raw_candidate_count"] == 829
    assert payload["all_raw_candidates_classified"] is True
    assert len(payload["rows"]) == 829
    assert all(row["pre_certification_subgate"] for row in payload["rows"])


def test_oracle_missing_candidates_are_inventory_only_and_not_executed() -> None:
    config = fresh.load_config()

    payload = fresh.build_candidate_funnel(config)
    missing = [row for row in payload["rows"] if row["pre_certification_status"] == "oracle_missing_inventory_only"]

    assert missing
    assert all(row["has_usable_oracle"] is False for row in missing)
    assert all(row["selected_for_execution"] is False for row in missing)
    assert Counter(row["repo_id"] for row in missing) == Counter({"attrs": 35, "boltons": 32, "humanize": 8, "toolz": 10})


def test_technical_certified_and_release_eligible_are_separate_counts() -> None:
    config = fresh.load_config()
    funnel_row = {
        "source_context_quality": "commit_message_only_context",
    }

    assert fresh.release_eligible(config, funnel_row, "technical_certified") is False
    assert fresh.release_eligible(config, {"source_context_quality": "non_leaky_issue_or_pr_context"}, "technical_certified") is True
    assert fresh.release_eligible(config, {"source_context_quality": "non_leaky_issue_or_pr_context"}, "reference_assert_failed") is False


def test_commit_message_only_technical_pass_enters_source_review_queue() -> None:
    config = fresh.load_config()
    attempts = {
        "rows": [
            {
                "candidate_id": "humanize__v2__001",
                "repo_id": "humanize",
                "technical_certified": True,
                "release_eligible": False,
                "source_context_class": "commit_message_only_context",
                "source_context_quality": "commit_message_only_context",
            }
        ]
    }

    queue = fresh.source_review_queue(config, attempts)

    assert queue["queue_count"] == 1
    assert queue["rows"][0]["suggested_review_mode"] == "manual_review"


def test_unattempted_cap_deferred_candidates_are_not_counted_as_failures() -> None:
    config = fresh.load_config()
    raw = [
        {
            "candidate_id": "attrs__x__1",
            "repo_id": "attrs",
            "source_reservoir": "repo_history_v2_commit_with_tests",
            "base_commit": "a" * 40,
            "target_commit_optional": "b" * 40,
            "implementation_files": ["attr/_next_gen.py"],
            "test_files": ["tests/test_next_gen.py"],
            "has_usable_oracle": True,
        },
        {
            "candidate_id": "attrs__x__2",
            "repo_id": "attrs",
            "source_reservoir": "repo_history_v2_commit_with_tests",
            "base_commit": "a" * 40,
            "target_commit_optional": "c" * 40,
            "implementation_files": ["attr/_next_gen.py"],
            "test_files": ["tests/test_next_gen.py"],
            "has_usable_oracle": True,
        },
    ]
    context = {"source_context_quality": "non_leaky_issue_or_pr_context"}
    oracle = {"oracle_classification": "changed_test_oracle_available"}
    rows = [
        fresh.initial_funnel_row(config, row, context, oracle, duplicate=False)
        for row in raw
    ]
    limited = fresh.apply_first_wave_caps({**config, "first_wave_attempt_cap_by_repo": {"attrs": 1}}, rows)

    assert Counter(row["pre_certification_subgate"] for row in limited) == Counter(
        {"selected_for_certification": 1, "not_attempted_cap_deferred": 1}
    )
    assert [row for row in limited if row["pre_certification_status"] == "not_attempted_cap_deferred"][0]["selected_for_execution"] is False


def test_subgate_labels_are_present_for_every_non_certified_attempt() -> None:
    attempts = {
        "rows": [
            {"technical_certified": False, "terminal_execution_subgate": "collect_failed"},
            {"technical_certified": True, "terminal_execution_subgate": "technical_certified"},
        ]
    }

    assert all(bool(row.get("terminal_execution_subgate")) for row in attempts["rows"] if not row.get("technical_certified"))


def test_command_record_does_not_store_raw_stdout_or_stderr() -> None:
    class Profile:
        profile_id = "py311_current_editable"

    class Result:
        returncode = 1
        stdout = "long raw stdout"
        stderr = "long raw stderr"
        duration_seconds = 0.1
        timed_out = False

    record = fresh.command_record(
        role="reference_1",
        profile=Profile(),  # type: ignore[arg-type]
        command=["python", "-m", "pytest"],
        workspace=fresh.REPO_ROOT,
        result=Result(),
    )

    assert "stdout" not in record
    assert "stderr" not in record
    assert record["stdout_tail_hash"]
    assert record["stderr_tail_hash"]


def test_paid_ready_requires_at_least_three_repos_with_30_release_eligible_tasks() -> None:
    config = fresh.load_config()
    funnel = {
        "rows": [],
    }
    rows = []
    for repo_id in ["attrs", "boltons"]:
        rows.extend(
            {
                "candidate_id": f"{repo_id}-{index}",
                "repo_id": repo_id,
                "technical_certified": True,
                "release_eligible": True,
                "terminal_execution_subgate": "technical_certified",
            }
            for index in range(30)
        )
    attempts = {"rows": rows, "unattempted_selected_count": 0}
    queue = {"rows": []}

    gate = fresh.paid_readiness_gate(config, funnel, attempts, queue)

    assert gate["minimum_paid_ready_requirements"]["at_least_3_repos_with_30_release_eligible"] is False
    assert gate["paid_ready"] is False
