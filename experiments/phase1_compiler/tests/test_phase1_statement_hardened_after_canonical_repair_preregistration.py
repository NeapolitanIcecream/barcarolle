from __future__ import annotations

import copy

import pytest

import phase1_statement_hardened_after_canonical_repair_preregistration as prereg


def statement_row(task_id: str, statement: str) -> dict:
    return {
        "contains_paid_outcome": False,
        "contains_raw_diff": False,
        "statement": statement,
        "statement_digest": prereg.statement_digest(statement),
        "task_id": task_id,
    }


def base_inventory_record() -> dict:
    return {
        "allowed_public_context_refs": ["issue:1"],
        "canonical_repo_split": "boltons/H_future",
        "canonical_screen_eligible": True,
        "canonical_split": "H_future",
        "current_inventory_split": "B_eval",
        "current_inventory_split_used_for_selection": False,
        "deterministic_qa_status": "pass",
        "digest_mismatch_sources": [],
        "editable_implementation_paths": ["boltons/iterutils.py"],
        "forbidden_statement_reasons": [],
        "full_visible_statement": "Task: implement public iterable behavior without leaking tests.",
        "historical_pass_fail_outcomes_used_for_selection": False,
        "implementation_scope_reasons": [],
        "non_editable_test_paths": ["tests/test_iterutils.py"],
        "repo_id": "boltons",
        "review_status": "pass",
        "source_ref": "issue:1",
        "statement_contains_paid_outcome_flag": False,
        "statement_contains_raw_diff_flag": False,
        "statement_digest": prereg.statement_digest("Task: implement public iterable behavior without leaking tests."),
        "statement_digest_matches_text": True,
        "statement_source": "canonical_regenerated",
        "task_id": "boltons__clean_ext__017",
        "task_time": "2024-01-01T00:00:00Z",
        "verifier_command_metadata": "pytest tests/test_iterutils.py",
    }


def minimal_split_map(groups: dict[str, list[str]] | None = None) -> dict:
    groups = groups or prereg.EXPECTED_CANONICAL_GROUPS
    task_to_split = {}
    for repo_split, task_ids in groups.items():
        repo_id, split = repo_split.split("/", 1)
        for task_id in task_ids:
            task_to_split[task_id] = {
                "canonical_split": split,
                "repo_id": repo_id,
                "repo_split": repo_split,
            }
    return {"task_to_split": task_to_split}


def test_canonical_split_labels_override_current_inventory_split() -> None:
    task_id = "boltons__clean_ext__017"
    split_map = minimal_split_map()
    canonical_inventory = {
        "rows": [
            {
                "implementation_files": ["boltons/timeutils.py"],
                "source_ref": "issue:319",
                "source_ref_metadata": ["issue:319"],
                "task_id": task_id,
                "test_files": ["tests/test_timeutils.py"],
            }
        ]
    }
    canonical_screen = {
        "candidate_screens": [
            {
                "eligible_under_canonical_split_repair": True,
                "statement_digest": prereg.statement_digest("Task: fix daterange month stepping."),
                "statement_source": "diff_assisted_codex_loop",
                "task_id": task_id,
            }
        ]
    }
    current_inventory = {"candidates": [{"release_split_eligibility": ["B_eval"], "task_id": task_id}]}
    statements = {task_id: statement_row(task_id, "Task: fix daterange month stepping.")}
    reviews = {task_id: {"status": "pass", "statement_digest": statements[task_id]["statement_digest"]}}
    qa = {task_id: {"status": "pass", "statement_digest": statements[task_id]["statement_digest"]}}

    rows = prereg.build_inventory_rows(
        split_map={"task_to_split": {task_id: split_map["task_to_split"][task_id], **{
            other: split_map["task_to_split"][other]
            for other in prereg.expected_task_ids()
            if other != task_id
        }}},
        canonical_inventory={
            "rows": canonical_inventory["rows"]
            + [
                {
                    "implementation_files": ["pkg/core.py"],
                    "source_ref": "issue:1",
                    "task_id": other,
                    "test_files": ["tests/test_core.py"],
                }
                for other in prereg.expected_task_ids()
                if other != task_id
            ]
        },
        canonical_screen={
            "candidate_screens": canonical_screen["candidate_screens"]
            + [
                {
                    "eligible_under_canonical_split_repair": True,
                    "statement_digest": prereg.statement_digest(f"Task: {other}"),
                    "task_id": other,
                }
                for other in prereg.expected_task_ids()
                if other != task_id
            ]
        },
        statement_rows={
            **statements,
            **{other: statement_row(other, f"Task: {other}") for other in prereg.expected_task_ids() if other != task_id},
        },
        review_rows={
            **reviews,
            **{
                other: {"status": "pass", "statement_digest": prereg.statement_digest(f"Task: {other}")}
                for other in prereg.expected_task_ids()
                if other != task_id
            },
        },
        qa_rows={
            **qa,
            **{
                other: {"status": "pass", "statement_digest": prereg.statement_digest(f"Task: {other}")}
                for other in prereg.expected_task_ids()
                if other != task_id
            },
        },
        current_inventory=current_inventory,
    )
    row = next(row for row in rows if row["task_id"] == task_id)

    assert row["canonical_repo_split"] == "boltons/H_future"
    assert row["current_inventory_split"] == "B_eval"
    assert row["current_inventory_split_used_for_selection"] is False


def test_all_16_canonical_tasks_are_required() -> None:
    broken = copy.deepcopy(prereg.EXPECTED_CANONICAL_GROUPS)
    broken["attrs/B_eval"] = broken["attrs/B_eval"][:-1]

    with pytest.raises(ValueError, match="missing"):
        prereg.validate_canonical_split_map(minimal_split_map(broken))


def test_boltons_clean_ext_017_must_be_h_future() -> None:
    broken = copy.deepcopy(prereg.EXPECTED_CANONICAL_GROUPS)
    broken["boltons/H_future"].remove("boltons__clean_ext__017")
    broken["boltons/B_eval"].append("boltons__clean_ext__017")

    with pytest.raises(ValueError, match="canonical split labels mismatch"):
        prereg.validate_canonical_split_map(minimal_split_map(broken))


def test_old_240_character_cap_is_not_rejection_reason_for_reviewed_generated_statement() -> None:
    record = base_inventory_record()
    record["source_context_excerpt"] = "x" * 240

    screen = prereg.screen_inventory_record(record)

    assert screen["eligible_under_canonical_split_repair"] is True
    assert screen["rejection_reasons"] == []


def test_statement_digest_must_match_statement_text() -> None:
    with pytest.raises(ValueError, match="statement digest mismatch"):
        prereg.merge_statement_rows(
            [
                {
                    "statement": "Problem summary: current text",
                    "statement_digest": prereg.statement_digest("Problem summary: different text"),
                    "task_id": "demo__001",
                }
            ],
            [],
        )


@pytest.mark.parametrize(
    ("review_status", "qa_status", "expected_reason"),
    [
        ("reject", "pass", "review_status_not_pass"),
        ("pass", "reject", "deterministic_qa_status_not_pass"),
    ],
)
def test_review_pass_plus_qa_pass_are_both_required(
    review_status: str,
    qa_status: str,
    expected_reason: str,
) -> None:
    record = base_inventory_record()
    record["review_status"] = review_status
    record["deterministic_qa_status"] = qa_status

    screen = prereg.screen_inventory_record(record)

    assert screen["eligible_under_canonical_split_repair"] is False
    assert expected_reason in screen["rejection_reasons"]


def test_paid_outcomes_do_not_affect_selection() -> None:
    config = {
        "_path": "config.yaml",
        "created_at": "2026-05-25T00:00:00Z",
        "output_paths": {"preflight": "missing.json"},
    }
    records = []
    for repo_split, task_ids in prereg.EXPECTED_CANONICAL_GROUPS.items():
        repo_id, split = repo_split.split("/", 1)
        for task_id in task_ids:
            row = base_inventory_record()
            row["canonical_repo_split"] = repo_split
            row["canonical_split"] = split
            row["repo_id"] = repo_id
            row["task_id"] = task_id
            row["historical_paid_context"] = {"terminal_status_counts": {"verified_pass": 2}}
            records.append(row)
    flipped = copy.deepcopy(records)
    for row in flipped:
        row["historical_paid_context"] = {"terminal_status_counts": {"verified_fail": 99}}

    left = prereg.build_screen_payload(config, {"rows": records})
    right = prereg.build_screen_payload(config, {"rows": flipped})

    assert left["selected_task_ids_by_repo_split"] == right["selected_task_ids_by_repo_split"]
    assert left["paid_outcome_used_for_selection"] is False


def test_tool_does_not_create_followup_runbook_files(tmp_path) -> None:
    config = {
        "_path": str(tmp_path / "config.yaml"),
        "created_at": "2026-05-25T00:00:00Z",
        "output_paths": {
            "blocker": str(tmp_path / "blocker.json"),
            "blocker_report": str(tmp_path / "blocker.md"),
            "preflight": str(tmp_path / "missing-preflight.json"),
            "preregistration": str(tmp_path / "preregistration.json"),
            "release_manifest": str(tmp_path / "manifest.json"),
            "validation_decision": str(tmp_path / "decision.json"),
            "validation_decision_report": str(tmp_path / "decision.md"),
        },
    }
    prereg.write_json(
        prereg.output_path(config, "release_manifest"),
        {
            "schema_version": prereg.RELEASE_MANIFEST_SCHEMA,
            "status": "frozen",
        },
    )
    prereg.write_json(
        prereg.output_path(config, "preregistration"),
        {
            "schema_version": prereg.PREREGISTRATION_SCHEMA,
            "status": "written",
        },
    )

    prereg.write_decision(config)

    assert not (tmp_path / "docs" / "experiments" / "phase-1-statement-hardened-paid-validation-runbook.md").exists()
    assert not (tmp_path / "docs" / "experiments" / "phase-1-statement-hardened-replacement-supply-runbook.md").exists()
