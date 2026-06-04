from __future__ import annotations

import csv
import json
from pathlib import Path

import headroom_matrix_followup as followup


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def minimal_root(tmp_path: Path) -> Path:
    root = tmp_path
    base = root / "experiments" / "phase0_headroom"
    task_ids = [f"toolz__hist__00{index}" for index in range(1, 7)]
    (base / "reports").mkdir(parents=True)
    (base / "reports" / "phase0_source_adapter_followup_decision.md").write_text(
        "Decision: `ready_for_headroom_matrix`.\n",
        encoding="utf-8",
    )
    write_json(base / "results" / "headroom_matrix.json", {"status": "ready_not_run_after_source_adapter_repair"})
    (base / "results" / "cost_ledger.jsonl").write_text("", encoding="utf-8")
    write_json(
        base / "releases" / "toolz_phase0_mini_release.json",
        {
            "release_id": "toolz-phase0-mini-source-adapter-candidate",
            "release_status": "benchmark_grade_candidate",
            "benchmark_grade": True,
            "splits": {"B_real": task_ids[:3], "W_real": task_ids[3:], "G_mini": ["click__rbench__001"]},
            "tasks": [{"task_id": task_id, "certification_status": "certified"} for task_id in task_ids],
        },
    )
    write_csv(
        base / "releases" / "toolz_phase0_task_table.csv",
        [
            {
                "task_id": task_id,
                "split": "B_real" if index < 3 else "W_real",
                "weight": "1.0",
                "certification_status": "certified",
                "counts_toward_benchmark_grade": "True",
                "module_or_package": "['functoolz']",
                "task_type_proxy": "feature_or_api_extension",
            }
            for index, task_id in enumerate(task_ids)
        ],
        ["task_id", "split", "weight", "certification_status", "counts_toward_benchmark_grade", "module_or_package", "task_type_proxy"],
    )
    gate_values = {gate: "pass" for gate in [*followup.REQUIRED_MECHANICAL_GATES, *followup.SEMANTIC_GATES]}
    write_csv(
        base / "certified_tasks" / "toolz_certification_funnel.csv",
        [
            {
                "task_id": task_id,
                "status": "certified",
                "first_failing_gate": "",
                **gate_values,
                "manual_review_minutes": "48",
                "runtime_seconds_estimate": "0.1",
            }
            for task_id in task_ids
        ],
        [
            "task_id",
            "status",
            "first_failing_gate",
            *followup.REQUIRED_MECHANICAL_GATES,
            *followup.SEMANTIC_GATES,
            "manual_review_minutes",
            "runtime_seconds_estimate",
        ],
    )
    write_jsonl(
        base / "certified_tasks" / "toolz_task_statements.jsonl",
        [
            {
                "task_id": task_id,
                "statement_review_status": "draft",
                "solver_facing_statement": "Fix the public callable behavior without changing unrelated APIs.",
                "allowed_context_refs": ["issue:1"],
            }
            for task_id in task_ids
        ],
    )
    write_jsonl(
        base / "certified_tasks" / "toolz_review_records.jsonl",
        [
            {
                "task_id": task_id,
                "status_after_review": "certified",
                "first_failing_gate": "",
                "review_minutes": 8,
                **{gate: "pass" for gate in followup.SEMANTIC_GATES},
            }
            for task_id in task_ids
        ],
    )
    write_jsonl(
        base / "certified_tasks" / "toolz_certified_tasks.jsonl",
        [
            {
                "task_id": task_id,
                "status": "certified",
                "first_failing_gate": "",
                "labels": ["missing:not_fetched"],
                "gates": {gate: "pass" for gate in followup.REQUIRED_MECHANICAL_GATES},
            }
            for task_id in task_ids
        ],
    )
    write_jsonl(
        base / "candidate_sources" / "toolz_source_context.jsonl",
        [
            {"task_id": task_id, "source_context_status": "non_leaky_context_found", "usable_source_item_count": 1}
            for task_id in task_ids
        ],
    )
    return root


def test_entry_gate_blocks_draft_statements(tmp_path: Path) -> None:
    root = minimal_root(tmp_path)
    entry = followup.evaluate_entry_gate(
        root,
        tooling_check={"passed": True},
        artifact_hygiene=(True, {"tracked_ignored_paths": [], "staged_ignored_paths": []}),
    )

    status = {gate["name"]: gate["status"] for gate in entry["gates"]}
    assert status["statement_status"] == "fail"
    assert entry["can_continue_phase0"] is False


def test_hygiene_repair_marks_reviewed_and_resets_review_minutes(tmp_path: Path) -> None:
    root = minimal_root(tmp_path)

    changes = followup.repair_entry_hygiene(root)
    entry = followup.evaluate_entry_gate(
        root,
        tooling_check={"passed": True},
        artifact_hygiene=(True, {"tracked_ignored_paths": [], "staged_ignored_paths": []}),
    )

    statements = followup.read_jsonl(root / "experiments" / "phase0_headroom" / "certified_tasks" / "toolz_task_statements.jsonl")
    funnel = followup.read_csv(root / "experiments" / "phase0_headroom" / "certified_tasks" / "toolz_certification_funnel.csv")
    certified = followup.read_jsonl(root / "experiments" / "phase0_headroom" / "certified_tasks" / "toolz_certified_tasks.jsonl")
    assert all(row["statement_review_status"] == "reviewed" for row in statements)
    assert {row["manual_review_minutes"] for row in funnel} == {"8"}
    assert all("missing:not_fetched" not in row["labels"] for row in certified)
    assert len(changes["source_labels_repaired"]) == 6
    assert entry["can_continue_phase0"] is True


def test_protocol_dry_run_report_preserves_g_mini_blocker() -> None:
    dry_run = {
        "generated_at": "2026-05-20T00:00:00+00:00",
        "same_repo_protocol_status": "pass",
        "g_mini_protocol_status": "not_scoreable_same_protocol",
        "paid_batch_task_ids": ["toolz__hist__001"],
        "tasks": [
            {"task_id": "toolz__hist__001", "split": "B_real", "status": "scoreable_same_protocol", "reasons": []},
            {
                "task_id": "click__rbench__001",
                "split": "G_mini",
                "status": "not_scoreable_same_protocol",
                "reasons": ["archived protocol"],
            },
        ],
    }

    report = followup.dry_run_report(dry_run)

    assert "`G_mini` protocol status: `not_scoreable_same_protocol`." in report
    assert "archived protocol" in report


def test_decision_reports_generic_protocol_repair_when_g_mini_is_not_same_protocol() -> None:
    entry = {"can_continue_phase0": True}
    dry_run = {
        "g_mini_protocol_status": "not_scoreable_same_protocol",
    }
    rows = [
        {
            "task_id": "toolz__hist__001",
            "split": "B_real",
            "terminal_status": "verified_fail",
            "scoreable_cell": True,
            "harness_error": False,
        }
    ]
    metrics = followup.metrics_payload(rows, {"g_mini_protocol_status": "not_scoreable_same_protocol"})

    report = followup.decision_report(entry, dry_run, rows, metrics, {"estimated_cost_usd": 60.0})

    assert "Decision: `repair_generic_comparator_protocol`." in report
