from __future__ import annotations

import json

import source_adapter_followup as followup


def test_linked_issue_numbers_extracts_hash_and_url_forms() -> None:
    text = "Implements #397 and fixes https://github.com/pytoolz/toolz/issues/602"

    assert followup.linked_issue_numbers(text) == [397, 602]


def test_commit_diff_is_solution_revealing() -> None:
    assert followup.classify_source_item("commit_diff", "adds a method", is_commit_diff=True) == "solution_revealing"


def test_statement_for_compose_repr_excludes_forbidden_identifiers() -> None:
    task = {
        "task_id": "toolz__hist__001",
        "base_commit": "base",
        "target_commit": "e221dc5fc5be90e9819453bba9ee621ea9193759",
        "test_files": ["toolz/tests/test_functoolz.py"],
    }
    context = {
        "source_context_status": "non_leaky_context_found",
        "source_items": [
            {"source_id": "issue:397", "solver_usable": True},
            {"source_id": "commit:e221dc5", "solver_usable": False},
        ],
    }

    statement = followup.build_statement(task, context)

    assert statement is not None
    assert "github.com" not in statement["solver_facing_statement"]
    assert "e221dc5" not in statement["solver_facing_statement"]
    assert not followup.statement_has_forbidden_text(statement["solver_facing_statement"], task)


def test_review_promotes_only_non_leaky_statement() -> None:
    task = {
        "task_id": "toolz__hist__016",
        "target_commit": "5a7e078c941c990dcaca53ac6920e5d5c0b1475f",
    }
    statement = {
        "solver_facing_statement": "Prevent partition_all from silently returning internal padding values.",
        "allowed_context_refs": ["issue:602"],
    }

    review = followup.review_statement(task, {"source_context_status": "non_leaky_context_found"}, statement)

    assert review["status_after_review"] == "certified"
    assert review["solution_leakage_review"] == "pass"


def test_release_status_requires_six_certified_tasks() -> None:
    certified = [
        {
            "task_id": f"task_{index}",
            "task_time": f"2020-01-0{index}T00:00:00+00:00",
            "module_or_package": ["functoolz"],
            "task_type_proxy": "feature_or_api_extension",
        }
        for index in range(1, 7)
    ]

    release, task_rows = followup.release_rows(certified, [])

    assert release["release_status"] == "benchmark_grade_candidate"
    assert release["certified_task_count"] == 6
    assert len(task_rows) == 6


def test_load_repair_targets_reuses_promoted_certified_tasks(tmp_path) -> None:
    certified_dir = tmp_path / "experiments" / "phase0_headroom" / "certified_tasks"
    certified_dir.mkdir(parents=True)
    (certified_dir / "toolz_near_certified_tasks.jsonl").write_text("", encoding="utf-8")
    rows = [
        {
            "task_id": f"task_{index}",
            "source_adapter_followup": {"source_adapter_version": followup.SOURCE_ADAPTER_VERSION},
        }
        for index in range(6)
    ]
    (certified_dir / "toolz_certified_tasks.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    targets, diffs = followup.load_repair_targets(tmp_path)

    assert [target["task_id"] for target in targets] == [f"task_{index}" for index in range(6)]
    assert diffs


def test_task_status_payload_preserves_prior_near_certified_status() -> None:
    payload = followup.task_status_payload(
        {
            "task_id": "toolz__hist__001",
            "status": "certified",
            "first_failing_gate": "",
            "gates": {},
        },
        {
            "status_after_review": "certified",
            "first_failing_gate": "",
            "ambiguity_review": "pass",
            "solution_leakage_review": "pass",
            "scope_clarity_review": "pass",
            "cost_boundedness": "pass",
            "taxonomy_labelability": "pass",
        },
        {"task_id": "toolz__hist__001"},
    )

    assert payload["source_adapter_followup"]["prior_status"] == "near_certified"
    assert payload["source_adapter_followup"]["prior_first_failing_gate"] == "solution_leakage_review"
