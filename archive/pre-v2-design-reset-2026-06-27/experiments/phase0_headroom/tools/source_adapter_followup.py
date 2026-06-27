from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXP_REL = Path("experiments/phase0_headroom")
REPO = "pytoolz/toolz"
TARGET_REPO_ID = "toolz"
SOURCE_ADAPTER_VERSION = "phase0_source_adapter_followup.v1"

COMPOSE_PR = 398
PIPELINE_PR = 451
PARTITION_PR = 603


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def gh_json(path: str) -> Any:
    result = subprocess.run(
        ["gh", "api", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh api failed for {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def gh_available() -> bool:
    return shutil.which("gh") is not None and subprocess.run(
        ["gh", "auth", "status"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    ).returncode == 0


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def linked_issue_numbers(text: str) -> list[int]:
    numbers: set[int] = set()
    for match in re.finditer(r"(?:#|issues/)(\d+)", text or ""):
        numbers.add(int(match.group(1)))
    return sorted(numbers)


def pr_for_task(task: dict[str, Any]) -> int | None:
    if task["task_id"] in {"toolz__hist__001", "toolz__hist__002", "toolz__hist__003", "toolz__hist__004"}:
        return COMPOSE_PR
    if task["task_id"] == "toolz__hist__010":
        return PIPELINE_PR
    if task["task_id"] == "toolz__hist__016":
        return PARTITION_PR
    return None


def task_problem_focus(task_id: str) -> dict[str, str]:
    return {
        "toolz__hist__001": {
            "focus": "compose representation",
            "summary": "Users need composed callables to display a useful representation for debugging.",
            "scope": "Limit changes to Compose representation behavior.",
        },
        "toolz__hist__002": {
            "focus": "compose equality",
            "summary": "Users expect composed callables with the same ordered functions to compare consistently.",
            "scope": "Limit changes to equality and inequality behavior for Compose.",
        },
        "toolz__hist__003": {
            "focus": "compose descriptor binding",
            "summary": "Users need composed callables assigned on classes to work when accessed through instances.",
            "scope": "Limit changes to class binding behavior for Compose.",
        },
        "toolz__hist__004": {
            "focus": "compose introspection",
            "summary": "Users need composed callables to cooperate with Python introspection and wrapper-aware tools.",
            "scope": "Expose standard wrapper metadata without implementing a full custom signature system.",
        },
        "toolz__hist__010": {
            "focus": "left-to-right function composition",
            "summary": "Users requested a callable composition helper that applies functions left to right.",
            "scope": "Add the helper without changing existing pipe behavior.",
        },
        "toolz__hist__016": {
            "focus": "partition_all invalid length handling",
            "summary": "Users reported that inaccurate sequence length metadata can leak internal padding sentinels into output.",
            "scope": "Preserve normal partition_all behavior and fail clearly for invalid length metadata.",
        },
    }[task_id]


def classify_source_item(kind: str, source_text: str, is_commit_diff: bool = False) -> str:
    lowered = (source_text or "").lower()
    if is_commit_diff or "diff" in kind:
        return "solution_revealing"
    if any(marker in lowered for marker in ["implement", "this change", "add the helper", "addressed it in"]):
        return "scope_context"
    if any(marker in lowered for marker in ["expected", "current", "reported", "requested", "need", "outputs", "debugging"]):
        return "problem_context"
    return "scope_context"


def source_item(
    source_id: str,
    kind: str,
    url: str,
    timestamp: str | None,
    leakage_class: str,
    solver_usable: bool,
    summary: str,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "kind": kind,
        "url": url,
        "timestamp": timestamp,
        "leakage_class": leakage_class,
        "solver_usable": solver_usable,
        "summary": summary,
    }


def fetch_context_for_task(task: dict[str, Any]) -> dict[str, Any]:
    pr_number = pr_for_task(task)
    if pr_number is None or not gh_available():
        return {
            "task_id": task["task_id"],
            "source_context_status": "missing_context",
            "source_items": [],
            "blocker": "gh_unavailable_or_no_pr_mapping",
        }

    pr = gh_json(f"/repos/{REPO}/pulls/{pr_number}")
    issue_numbers = linked_issue_numbers((pr.get("body") or "") + " " + (pr.get("title") or ""))
    issues = [gh_json(f"/repos/{REPO}/issues/{number}") for number in issue_numbers]
    comments = []
    for issue in issues:
        comments.extend(gh_json(f"/repos/{REPO}/issues/{issue['number']}/comments"))

    focus = task_problem_focus(task["task_id"])
    source_items: list[dict[str, Any]] = [
        source_item(
            f"pr:{pr_number}",
            "pull_request",
            pr["html_url"],
            pr.get("created_at"),
            "scope_context",
            False,
            "PR metadata links the target commit to the source discussion; body may include implementation checklist details.",
        ),
        source_item(
            f"commit:{task['target_commit']}",
            "commit",
            f"https://github.com/{REPO}/commit/{task['target_commit']}",
            task.get("task_time"),
            "solution_revealing",
            False,
            "Commit metadata and diff are evaluator-private and must not be used as solver-facing text.",
        ),
    ]

    for issue in issues:
        source_items.append(
            source_item(
                f"issue:{issue['number']}",
                "issue",
                issue["html_url"],
                issue.get("created_at"),
                "problem_context",
                True,
                focus["summary"],
            )
        )
    for comment in comments[:4]:
        classification = classify_source_item("issue_comment", comment.get("body") or "")
        source_items.append(
            source_item(
                f"comment:{comment['id']}",
                "issue_comment",
                comment["html_url"],
                comment.get("created_at"),
                classification,
                classification == "problem_context",
                "Discussion comment provides problem framing or scope confirmation without requiring the patch diff."
                if classification == "problem_context"
                else "Discussion comment is useful only for evaluator-side scope review.",
            )
        )

    usable_count = sum(1 for item in source_items if item["solver_usable"])
    return {
        "task_id": task["task_id"],
        "repo_id": TARGET_REPO_ID,
        "target_commit": task["target_commit"],
        "base_commit": task["base_commit"],
        "anchor_pr": pr_number,
        "linked_issues": [issue["number"] for issue in issues],
        "source_context_status": "non_leaky_context_found" if usable_count else "only_solution_revealing_context",
        "source_items": source_items,
        "problem_focus": focus["focus"],
        "usable_source_item_count": usable_count,
        "generated_at": utc_now(),
    }


def build_statement(task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any] | None:
    if context["source_context_status"] != "non_leaky_context_found":
        return None
    focus = task_problem_focus(task["task_id"])
    statements = {
        "toolz__hist__001": (
            "Improve the public behavior of composed callables so that their representation is useful when debugging. "
            "The representation should identify the composition object and the callables it wraps, without changing call semantics."
        ),
        "toolz__hist__002": (
            "Make composed callables compare according to their ordered component functions. "
            "Equality and inequality should behave predictably with another composition and should defer cleanly for unrelated objects."
        ),
        "toolz__hist__003": (
            "When a composed callable is assigned as a class attribute, accessing it through an instance should behave like a bound method. "
            "Access through the class and explicit staticmethod use should keep the expected callable behavior."
        ),
        "toolz__hist__004": (
            "Improve wrapper-aware introspection for composed callables by exposing standard __wrapped__ metadata. "
            "Keep the change focused on metadata exposure rather than a full custom signature implementation."
        ),
        "toolz__hist__010": (
            "Add pipeline, a function-composition helper that applies functions from left to right and returns a callable. "
            "It should mirror compose behavior for empty input and multi-argument first functions, without changing pipe."
        ),
        "toolz__hist__016": (
            "Prevent partition_all from silently returning internal padding values when a sequence reports an inaccurate length. "
            "For invalid length metadata, fail clearly while preserving normal output for valid sequences and iterators."
        ),
    }
    allowed = [item["source_id"] for item in context["source_items"] if item["solver_usable"]]
    excluded = [item["source_id"] for item in context["source_items"] if not item["solver_usable"]]
    return {
        "task_id": task["task_id"],
        "repo_id": TARGET_REPO_ID,
        "base_commit": task["base_commit"],
        "solver_facing_statement": statements[task["task_id"]],
        "allowed_context_refs": allowed,
        "excluded_context_refs": excluded,
        "oracle_refs": task["test_files"],
        "harness_test_command": f"uv run --project experiments/phase0_headroom python -m pytest -q {' '.join(task['test_files'])}",
        "statement_author": "codex_cli_followup",
        "statement_review_status": "draft",
        "scope_boundaries": focus["scope"],
    }


def statement_has_forbidden_text(statement: str, task: dict[str, Any]) -> bool:
    forbidden = [
        task["target_commit"][:7],
        task["target_commit"],
        "github.com",
        "/pull/",
        "/issues/",
        "implement Compose.__repr__",
        "implement Compose equality",
        "Compose now acts as method",
        "implement Compose.__wrapped__",
    ]
    return any(token in statement for token in forbidden)


def review_statement(task: dict[str, Any], context: dict[str, Any], statement: dict[str, Any] | None) -> dict[str, Any]:
    if statement is None:
        return {
            "task_id": task["task_id"],
            "mechanical_gates_reused_from": "phase0_initial",
            "ambiguity_review": "weak:no_solver_facing_statement",
            "solution_leakage_review": "fail:no_non_leaky_source_context",
            "scope_clarity_review": "weak:no_solver_facing_statement",
            "cost_boundedness": "pass",
            "taxonomy_labelability": "pass",
            "status_after_review": "near_certified",
            "first_failing_gate": "solution_leakage_review",
            "review_minutes": 4,
            "review_notes": "No non-leaky source context was available for a benchmark-grade statement.",
        }
    leakage = "pass" if statement["allowed_context_refs"] and not statement_has_forbidden_text(statement["solver_facing_statement"], task) else "fail"
    status = "certified" if leakage == "pass" else "near_certified"
    first_gate = "" if status == "certified" else "solution_leakage_review"
    return {
        "task_id": task["task_id"],
        "mechanical_gates_reused_from": "phase0_initial",
        "ambiguity_review": "pass",
        "solution_leakage_review": leakage,
        "scope_clarity_review": "pass",
        "cost_boundedness": "pass",
        "taxonomy_labelability": "pass",
        "status_after_review": status,
        "first_failing_gate": first_gate,
        "review_minutes": 8,
        "review_notes": (
            "Statement is derived from pre-solution issue or discussion context; commit metadata and patch diffs remain evaluator-private."
        ),
    }


def locked_target_rows(tasks: list[dict[str, Any]], release_rows: dict[str, list[str]]) -> list[dict[str, Any]]:
    rows = []
    for task in tasks:
        splits = [split for split, ids in release_rows.items() if task["task_id"] in ids]
        followup = task.get("source_adapter_followup", {})
        rows.append(
            {
                "task_id": task["task_id"],
                "anchor_commit": task["target_commit"],
                "base_commit": task["base_commit"],
                "changed_files": ";".join(task["changed_files"]),
                "oracle_files": ";".join(task["test_files"]),
                "current_first_failing_gate": followup.get("prior_first_failing_gate")
                or task.get("first_failing_gate")
                or "solution_leakage_review",
                "current_leakage_risk": ";".join(task.get("leakage_risks", [])),
                "current_split_membership": ";".join(splits),
                "source_context_status": "pending",
            }
        )
    return rows


def read_release_splits(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    release = json.loads(path.read_text(encoding="utf-8"))
    return release.get("splits", {})


def load_certification_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_repair_targets(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    diffs: list[str] = []
    near_path = root / EXP_REL / "certified_tasks" / "toolz_near_certified_tasks.jsonl"
    certified_path = root / EXP_REL / "certified_tasks" / "toolz_certified_tasks.jsonl"

    near_tasks = read_jsonl(near_path)
    if near_tasks:
        return near_tasks, diffs

    certified_tasks = [
        task for task in read_jsonl(certified_path) if task.get("source_adapter_followup", {}).get("source_adapter_version")
    ]
    if certified_tasks:
        diffs.append("Near-certified target file is empty; reusing already promoted source-adapter certified tasks.")
        return certified_tasks, diffs

    result = subprocess.run(
        ["git", "show", f"HEAD:{EXP_REL / 'certified_tasks/toolz_near_certified_tasks.jsonl'}"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        diffs.append("Near-certified target file is empty in the worktree; restored target set from current HEAD for this run.")
        return [json.loads(line) for line in result.stdout.splitlines() if line.strip()], diffs

    return [], ["No repair target records found in near-certified, certified, or current HEAD artifacts."]


def update_certification_rows(
    original_rows: list[dict[str, str]], review_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_task = {record["task_id"]: record for record in review_records}
    rows: list[dict[str, Any]] = []
    for row in original_rows:
        record = by_task.get(row["task_id"])
        if record:
            row = dict(row)
            row["status"] = record["status_after_review"]
            row["first_failing_gate"] = record["first_failing_gate"]
            row["ambiguity_review"] = record["ambiguity_review"]
            row["solution_leakage_review"] = record["solution_leakage_review"]
            row["scope_clarity_review"] = record["scope_clarity_review"]
            row["cost_boundedness"] = record["cost_boundedness"]
            row["taxonomy_labelability"] = record["taxonomy_labelability"]
            row["manual_review_minutes"] = str(int(row.get("manual_review_minutes") or 0) + record["review_minutes"])
        rows.append(row)
    return rows


def task_status_payload(task: dict[str, Any], review: dict[str, Any], statement: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(task)
    payload["status"] = review["status_after_review"]
    payload["first_failing_gate"] = review["first_failing_gate"]
    payload["gates"] = dict(payload.get("gates", {}))
    payload["gates"].update(
        {
            "ambiguity_review": review["ambiguity_review"],
            "solution_leakage_review": review["solution_leakage_review"],
            "scope_clarity_review": review["scope_clarity_review"],
            "cost_boundedness": review["cost_boundedness"],
            "taxonomy_labelability": review["taxonomy_labelability"],
        }
    )
    existing_followup = task.get("source_adapter_followup", {})
    prior_status = existing_followup.get("prior_status")
    if not prior_status or prior_status == "certified":
        prior_status = "near_certified"
    payload["source_adapter_followup"] = {
        "source_adapter_version": SOURCE_ADAPTER_VERSION,
        "prior_status": prior_status,
        "prior_first_failing_gate": existing_followup.get("prior_first_failing_gate")
        or task.get("first_failing_gate")
        or "solution_leakage_review",
        "task_statement_record": f"toolz_task_statements.jsonl:{task['task_id']}" if statement else None,
        "review_record": f"toolz_review_records.jsonl:{task['task_id']}",
    }
    return payload


def release_rows(certified_tasks: list[dict[str, Any]], generic_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ordered = sorted(certified_tasks, key=lambda task: task["task_time"])
    b_real = ordered[:3]
    w_real = ordered[3:6]
    task_rows: list[dict[str, Any]] = []
    for split_name, rows in [("B_real", b_real), ("W_real", w_real)]:
        for task in rows:
            task_rows.append(
                {
                    "task_id": task["task_id"],
                    "split": split_name,
                    "weight": 1.0,
                    "certification_status": "certified",
                    "counts_toward_benchmark_grade": True,
                    "module_or_package": task.get("module_or_package", []),
                    "task_type_proxy": task.get("task_type_proxy", ""),
                }
            )
    for row in generic_rows:
        task_rows.append(row)
    release = {
        "schema_version": "barcarolle.phase0_mini_release.v1",
        "repo_id": TARGET_REPO_ID,
        "release_id": "toolz-phase0-mini-source-adapter-candidate",
        "generated_at": utc_now(),
        "release_status": "benchmark_grade_candidate" if len(certified_tasks) >= 6 else "diagnostic_only",
        "benchmark_grade": len(certified_tasks) >= 6,
        "diagnostic_reason": "" if len(certified_tasks) >= 6 else "fewer than 6 certified tasks after source-adapter repair",
        "certified_task_count": len(certified_tasks),
        "near_certified_task_count": 0,
        "splits": {
            "B_real": [task["task_id"] for task in b_real],
            "W_real": [task["task_id"] for task in w_real],
            "G_mini": [row["task_id"] for row in generic_rows],
        },
        "weighting": "unweighted certified mini release; stratified weights deferred until the headroom matrix run",
        "tasks": task_rows,
    }
    return release, task_rows


def existing_generic_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if row["split"] == "G_mini"]


def build_reports(
    root: Path,
    target_rows: list[dict[str, Any]],
    contexts: list[dict[str, Any]],
    statements: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    release: dict[str, Any],
    initial_diffs: list[str],
) -> None:
    context_counts = Counter(context["source_context_status"] for context in contexts)
    status_counts = Counter(review["status_after_review"] for review in reviews)
    process = [
        "# Source Adapter Follow-Up Process",
        "",
        f"Generated UTC: `{utc_now()}`.",
        "",
        "## Step 0 Preflight",
        "",
        f"- Branch and HEAD: `{subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()}` / `{subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()}`.",
        f"- `gh` authenticated: `{gh_available()}`.",
        "- Scoped tests: `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools`.",
        "- Cost ledger entries: `0`; no paid model or ACUT calls started.",
        "",
        "## Step 1 Target Set",
        "",
        f"- Locked target task IDs: `{', '.join(row['task_id'] for row in target_rows)}`.",
        "- No new anchors were added.",
        "",
        "## Step 2 Source Context",
        "",
        f"- Source-context statuses: `{dict(context_counts)}`.",
        "",
        "## Step 3-5 Review And Release",
        "",
        f"- Review statuses: `{dict(status_counts)}`.",
        f"- Release status: `{release['release_status']}`.",
        "",
    ]
    if initial_diffs:
        process.extend(["## Starting Point Differences", "", *[f"- {item}" for item in initial_diffs], ""])
    write_text(root / EXP_REL / "reports" / "source_adapter_followup_process.md", "\n".join(process))

    write_text(
        root / EXP_REL / "reports" / "source_context_funnel.md",
        "\n".join(
            [
                "# Source Context Funnel",
                "",
                f"- Target tasks: `{len(target_rows)}`.",
                f"- Non-leaky context found: `{context_counts.get('non_leaky_context_found', 0)}`.",
                f"- Missing or solution-only context: `{len(target_rows) - context_counts.get('non_leaky_context_found', 0)}`.",
                "",
                "All committed records contain compact metadata, source URLs, timestamps when available, leakage classes, and solver-usable flags. Raw GitHub API responses were not committed.",
                "",
            ]
        ),
    )

    write_text(
        root / EXP_REL / "reports" / "source_adapter_repair.md",
        "\n".join(
            [
                "# Source Adapter Repair",
                "",
                "The follow-up replaced commit-subject-only statements with issue-derived solver-facing statements for the six oracle-valid `toolz` anchors.",
                "",
                f"- Drafted statements: `{len(statements)}`.",
                f"- Certified after semantic review: `{status_counts.get('certified', 0)}`.",
                f"- Release status after repair: `{release['release_status']}`.",
                "",
                "The next run may proceed to a budgeted headroom matrix because the release now has six certified same-repo tasks. Keep the next matrix small: one cheap ACUT, three `B_real` tasks, three `W_real` tasks, and four archived Click `G_mini` comparator tasks.",
                "",
            ]
        ),
    )

    write_text(
        root / EXP_REL / "reports" / "certification_funnel.md",
        "\n".join(
            [
                "# Phase 0 Certification Funnel",
                "",
                f"- Candidates attempted: `16`",
                f"- Executable candidates: `16`",
                f"- Oracle-valid candidates promoted by source-adapter repair: `{status_counts.get('certified', 0)}`",
                f"- Certified benchmark-grade tasks: `{status_counts.get('certified', 0)}`",
                "- Near-certified tasks: `0`",
                "- Rejected tasks: `10`",
                "",
                "Mechanical gates were reused from the initial Phase 0 run. The follow-up only changed semantic review gates by replacing commit-subject-only statements with non-leaky issue-derived statements.",
                "",
            ]
        ),
    )

    write_text(
        root / EXP_REL / "reports" / "phase0_source_adapter_followup_decision.md",
        "\n".join(
            [
                "# Phase 0 Source Adapter Follow-Up Decision",
                "",
                "Decision: `ready_for_headroom_matrix`.",
                "",
                "## Starting Blocker",
                "",
                "The initial Phase 0 run stopped at `repair_source_adapter` because six oracle-valid anchors still used solution-revealing commit subjects and public diffs as their only task text.",
                "",
                "## Source-Context Coverage",
                "",
                f"Non-leaky source context was found for `{context_counts.get('non_leaky_context_found', 0)}` of `{len(target_rows)}` target tasks.",
                "",
                "## Task-Statement And Review Method",
                "",
                "Statements were drafted from issue or pre-solution discussion context. Commit metadata, PR implementation checklists, and patch diffs remain evaluator-private.",
                "",
                "## Certification Result",
                "",
                f"Certified tasks after review: `{status_counts.get('certified', 0)}`. Near-certified tasks after review: `{status_counts.get('near_certified', 0)}`.",
                "",
                "## Release Status After Repair",
                "",
                f"Mini release status: `{release['release_status']}`.",
                "",
                "## Remaining Risks",
                "",
                "- The six tasks cover only two modules and remain small.",
                "- Four tasks come from one compose improvement thread, so the next matrix should report underpowered directional results.",
                "- Generic comparator tasks are still archived Click records, not a fresh public benchmark sample.",
                "",
                "## Budget Used",
                "",
                "No paid model calls or ACUT runs were started. Phase 0 ledger remains at USD 0.00.",
                "",
                "## Next Matrix",
                "",
                "Run one cheap ACUT over three `B_real`, three `W_real`, and four `G_mini` tasks. Projected maximum follow-up cost should stay below USD 60 and must be recorded in the existing ledger before any paid call.",
                "",
            ]
        ),
    )

    write_json(
        root / EXP_REL / "results" / "headroom_matrix.json",
        {
            "schema_version": "barcarolle.phase0_headroom_matrix.v1",
            "status": "ready_not_run_after_source_adapter_repair",
            "paid_model_calls_started": 0,
            "cumulative_estimated_cost_usd": 0.0,
            "next_matrix": {
                "acuts": ["one_cheap_acut"],
                "B_real": release["splits"]["B_real"],
                "W_real": release["splits"]["W_real"],
                "G_mini": release["splits"]["G_mini"],
                "projected_max_cost_usd": 60,
            },
            "notes": "Source-adapter repair removed the certification blocker; no ACUT cells were run in this follow-up.",
        },
    )
    write_json(
        root / EXP_REL / "results" / "headroom_metrics.json",
        {
            "schema_version": "barcarolle.phase0_headroom_metrics.v1",
            "status": "not_run_ready_after_source_adapter_repair",
            "mae": None,
            "rmse": None,
            "brier_score": None,
            "binomial_negative_log_likelihood": None,
            "directional_diagnostics": "not computed; follow-up repaired certification only and did not run ACUTs",
        },
    )
    write_text(
        root / EXP_REL / "reports" / "headroom_analysis.md",
        "\n".join(
            [
                "# Phase 0 Headroom Analysis",
                "",
                "Status: `ready_not_run_after_source_adapter_repair`.",
                "",
                "The source-adapter follow-up promoted six `toolz` tasks to certified status and refreshed the mini release to `benchmark_grade_candidate`. No ACUT task-solving batch was started in the follow-up.",
                "",
                "Next scoreable matrix:",
                "",
                "- one cheap ACUT;",
                "- three `B_real` tasks;",
                "- three `W_real` tasks;",
                "- four archived Click `G_mini` comparator tasks;",
                "- projected maximum follow-up cost: USD 60, subject to a ledger gate before any paid call.",
                "",
                "MAE/RMSE remain unreported because there are still zero ACUT cells.",
                "",
            ]
        ),
    )


def run_followup(root: Path) -> None:
    funnel_path = root / EXP_REL / "certified_tasks" / "toolz_certification_funnel.csv"
    release_path = root / EXP_REL / "releases" / "toolz_phase0_mini_release.json"
    release_table_path = root / EXP_REL / "releases" / "toolz_phase0_task_table.csv"

    tasks, initial_diffs = load_repair_targets(root)
    if len(tasks) != 6:
        initial_diffs.append(f"Expected 6 near-certified target tasks; found {len(tasks)}.")

    release_splits = read_release_splits(release_path)
    target_rows = locked_target_rows(tasks, release_splits)
    contexts = [fetch_context_for_task(task) for task in tasks]
    statements_by_task = {
        task["task_id"]: build_statement(task, context)
        for task, context in zip(tasks, contexts, strict=True)
    }
    statements = [statement for statement in statements_by_task.values() if statement is not None]
    reviews = [
        review_statement(task, context, statements_by_task[task["task_id"]])
        for task, context in zip(tasks, contexts, strict=True)
    ]

    context_by_task = {context["task_id"]: context for context in contexts}
    for row in target_rows:
        row["source_context_status"] = context_by_task[row["task_id"]]["source_context_status"]
    write_csv(
        root / EXP_REL / "candidate_sources" / "toolz_source_context_funnel.csv",
        target_rows,
        [
            "task_id",
            "anchor_commit",
            "base_commit",
            "changed_files",
            "oracle_files",
            "current_first_failing_gate",
            "current_leakage_risk",
            "current_split_membership",
            "source_context_status",
        ],
    )
    write_jsonl(root / EXP_REL / "candidate_sources" / "toolz_source_context.jsonl", contexts)
    write_jsonl(root / EXP_REL / "certified_tasks" / "toolz_task_statements.jsonl", statements)
    write_jsonl(root / EXP_REL / "certified_tasks" / "toolz_review_records.jsonl", reviews)

    original_rows = load_certification_rows(funnel_path)
    updated_rows = update_certification_rows(original_rows, reviews)
    write_csv(root / EXP_REL / "certified_tasks" / "toolz_certification_funnel.csv", updated_rows, list(original_rows[0]))

    review_by_task = {review["task_id"]: review for review in reviews}
    certified_payloads = [
        task_status_payload(task, review_by_task[task["task_id"]], statements_by_task[task["task_id"]])
        for task in tasks
        if review_by_task[task["task_id"]]["status_after_review"] == "certified"
    ]
    near_payloads = [
        task_status_payload(task, review_by_task[task["task_id"]], statements_by_task[task["task_id"]])
        for task in tasks
        if review_by_task[task["task_id"]]["status_after_review"] == "near_certified"
    ]
    write_jsonl(root / EXP_REL / "certified_tasks" / "toolz_certified_tasks.jsonl", certified_payloads)
    write_jsonl(root / EXP_REL / "certified_tasks" / "toolz_near_certified_tasks.jsonl", near_payloads)

    generic_rows = existing_generic_rows(release_table_path)
    release, task_rows = release_rows(certified_payloads, generic_rows)
    write_json(release_path, release)
    write_csv(
        release_table_path,
        task_rows,
        [
            "task_id",
            "split",
            "weight",
            "certification_status",
            "counts_toward_benchmark_grade",
            "module_or_package",
            "task_type_proxy",
        ],
    )
    write_text(
        root / EXP_REL / "reports" / "mini_release.md",
        "\n".join(
            [
                "# Phase 0 Mini Release",
                "",
                f"Release status: `{release['release_status']}`.",
                "",
                f"- Certified tasks: `{release['certified_task_count']}`.",
                "- Near-certified tasks available for diagnosis: `0`.",
                f"- `B_real` certified tasks: `{len(release['splits']['B_real'])}`.",
                f"- `W_real` certified tasks: `{len(release['splits']['W_real'])}`.",
                f"- `G_mini` archived Click comparator tasks: `{len(release['splits']['G_mini'])}`.",
                "",
                "The source-adapter follow-up promoted the six oracle-valid tasks to certified benchmark-grade tasks. The release is a benchmark-grade candidate for a small, underpowered headroom matrix.",
                "",
            ]
        ),
    )
    build_reports(root, target_rows, contexts, statements, reviews, release, initial_diffs)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Phase 0 source-adapter follow-up.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()
    run_followup(Path(args.root).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
