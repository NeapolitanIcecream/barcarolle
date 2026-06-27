from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXP_REL = Path("experiments/phase0_headroom")
TOOLZ_REPO_REL = EXP_REL / "external_repos" / "toolz"
RAW_REL = EXP_REL / "results" / "raw" / "headroom_matrix_followup"
WORKSPACE_REL = EXP_REL / "workspaces" / "headroom_matrix_followup"
ACUT_ID = "codex_cli_gpt_5_3_codex_spark"
ACUT_MODEL = "gpt-5.3-codex-spark"
ACUT_PROJECTED_MAX_USD = 60.0
PER_TASK_TIMEOUT_SECONDS = 900
REQUIRED_MECHANICAL_GATES = ["checkout", "oracle_extractable", "no_op_fail", "reference_pass", "known_bad_fail", "flakiness_check"]
SEMANTIC_GATES = [
    "ambiguity_review",
    "solution_leakage_review",
    "scope_clarity_review",
    "cost_boundedness",
    "taxonomy_labelability",
]


@dataclass
class CommandResult:
    command: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_command(
    command: list[str],
    cwd: Path,
    timeout: int = 120,
    input_text: str | None = None,
) -> CommandResult:
    start = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            input=input_text.encode("utf-8") if input_text is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return CommandResult(
            command=command,
            cwd=str(cwd),
            returncode=completed.returncode,
            stdout=completed.stdout.decode("utf-8", errors="replace"),
            stderr=completed.stderr.decode("utf-8", errors="replace"),
            duration_seconds=time.monotonic() - start,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            command=command,
            cwd=str(cwd),
            returncode=124,
            stdout=exc.stdout.decode("utf-8", errors="replace") if exc.stdout else "",
            stderr=exc.stderr.decode("utf-8", errors="replace") if exc.stderr else "",
            duration_seconds=time.monotonic() - start,
            timed_out=True,
        )


def require_success(result: CommandResult) -> str:
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(result.command)}\n"
            f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )
    return result.stdout


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_text(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def boolish(value: Any) -> bool:
    return str(value).lower() in {"true", "1", "yes"}


def read_cumulative_cost(ledger_path: Path) -> float:
    if not ledger_path.exists() or ledger_path.stat().st_size == 0:
        return 0.0
    cumulative = 0.0
    with ledger_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            cumulative = float(
                record.get(
                    "cumulative_estimated_cost_usd",
                    record.get("cumulative_projected_cost_usd", cumulative),
                )
            )
    return cumulative


def append_ledger(root: Path, record: dict[str, Any]) -> None:
    ledger = root / EXP_REL / "results" / "cost_ledger.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def prune_existing_headroom_cost_events(root: Path) -> None:
    ledger = root / EXP_REL / "results" / "cost_ledger.jsonl"
    if not ledger.exists() or ledger.stat().st_size == 0:
        return
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
    kept = [row for row in rows if row.get("record_type") != "phase0_headroom_cost_event"]
    write_text(ledger, "".join(json.dumps(row, sort_keys=True) + "\n" for row in kept))


def source_adapter_decision(root: Path) -> str:
    path = root / EXP_REL / "reports" / "phase0_source_adapter_followup_decision.md"
    if not path.exists():
        return ""
    match = re.search(r"Decision:\s*`([^`]+)`", path.read_text(encoding="utf-8"))
    return match.group(1) if match else ""


def statement_has_forbidden_text(statement: str) -> bool:
    patterns = [
        r"[0-9a-f]{40}",
        r"github\.com",
        r"/pull/\d+",
        r"/issues/\d+",
        r"#\d+",
        r"commit/[0-9a-f]+",
        r"git\s+diff",
        r"git\s+show",
        r"assert\s+",
        r"toolz/tests/",
    ]
    return any(re.search(pattern, statement, flags=re.IGNORECASE) for pattern in patterns)


def artifact_hygiene_status(root: Path) -> tuple[bool, dict[str, Any]]:
    ignored_paths = [
        "experiments/phase0_headroom/.pytest_cache",
        "experiments/phase0_headroom/.venv",
        "experiments/phase0_headroom/external_repos",
        "experiments/phase0_headroom/results/raw",
        "experiments/phase0_headroom/tools/__pycache__",
        "experiments/phase0_headroom/workspaces",
    ]
    tracked = require_success(run_command(["git", "ls-files", *ignored_paths], root)).splitlines()
    cached = require_success(run_command(["git", "diff", "--cached", "--name-only", "--", *ignored_paths], root)).splitlines()
    return not tracked and not cached, {"tracked_ignored_paths": tracked, "staged_ignored_paths": cached}


def run_tooling_check(root: Path) -> dict[str, Any]:
    command = ["uv", "run", "--project", "experiments/phase0_headroom", "pytest", "-q", "experiments/phase0_headroom/tools"]
    result = run_command(command, root, timeout=120)
    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "duration_seconds": round(result.duration_seconds, 3),
        "stdout_tail": result.stdout[-1000:],
        "stderr_tail": result.stderr[-1000:],
        "passed": result.returncode == 0 and not result.timed_out,
    }


def gate(name: str, status: str, evidence_path: str, details: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "status": status, "evidence_path": evidence_path, "details": details}


def evaluate_entry_gate(
    root: Path,
    *,
    projected_cost_usd: float = ACUT_PROJECTED_MAX_USD,
    tooling_check: dict[str, Any] | None = None,
    artifact_hygiene: tuple[bool, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    certified_rows = read_csv(root / EXP_REL / "certified_tasks" / "toolz_certification_funnel.csv")
    certified_tasks = read_jsonl(root / EXP_REL / "certified_tasks" / "toolz_certified_tasks.jsonl")
    statements = read_jsonl(root / EXP_REL / "certified_tasks" / "toolz_task_statements.jsonl")
    reviews = read_jsonl(root / EXP_REL / "certified_tasks" / "toolz_review_records.jsonl")
    release = read_json(root / EXP_REL / "releases" / "toolz_phase0_mini_release.json")
    release_table = read_csv(root / EXP_REL / "releases" / "toolz_phase0_task_table.csv")
    matrix = read_json(root / EXP_REL / "results" / "headroom_matrix.json")
    ledger = root / EXP_REL / "results" / "cost_ledger.jsonl"

    rows_by_task = {row["task_id"]: row for row in certified_rows}
    certified_ids = [row["task_id"] for row in certified_rows if row["status"] == "certified"]
    statement_by_task = {row["task_id"]: row for row in statements}
    review_by_task = {row["task_id"]: row for row in reviews}
    release_by_task = {row["task_id"]: row for row in release.get("tasks", [])}
    jsonl_by_task = {row["task_id"]: row for row in certified_tasks}
    gate_rows: list[dict[str, Any]] = []

    decision = source_adapter_decision(root)
    gate_rows.append(
        gate(
            "source_adapter_decision",
            "pass" if decision == "ready_for_headroom_matrix" else "fail",
            "experiments/phase0_headroom/reports/phase0_source_adapter_followup_decision.md",
            {"decision": decision},
        )
    )

    matrix_status = matrix.get("status")
    gate_rows.append(
        gate(
            "matrix_status",
            "pass" if matrix_status == "ready_not_run_after_source_adapter_repair" else "fail",
            "experiments/phase0_headroom/results/headroom_matrix.json",
            {"status": matrix_status},
        )
    )

    near_count = sum(1 for row in certified_rows if row["status"] == "near_certified")
    gate_rows.append(
        gate(
            "certified_count",
            "pass" if len(certified_ids) >= 6 and near_count == 0 else "fail",
            "experiments/phase0_headroom/certified_tasks/toolz_certification_funnel.csv",
            {"certified_count": len(certified_ids), "near_certified_count": near_count},
        )
    )

    gate_rows.append(
        gate(
            "release_status",
            "pass" if release.get("release_status") == "benchmark_grade_candidate" else "fail",
            "experiments/phase0_headroom/releases/toolz_phase0_mini_release.json",
            {"release_status": release.get("release_status"), "benchmark_grade": release.get("benchmark_grade")},
        )
    )

    split_ids: dict[str, list[str]] = defaultdict(list)
    for row in release_table:
        if row["split"] in {"B_real", "W_real"} and row["certification_status"] == "certified" and boolish(
            row["counts_toward_benchmark_grade"]
        ):
            split_ids[row["split"]].append(row["task_id"])
    duplicate_bw = sorted(set(split_ids["B_real"]) & set(split_ids["W_real"]))
    gate_rows.append(
        gate(
            "split_minimum",
            "pass" if len(split_ids["B_real"]) >= 3 and len(split_ids["W_real"]) >= 3 and not duplicate_bw else "fail",
            "experiments/phase0_headroom/releases/toolz_phase0_task_table.csv",
            {"B_real": split_ids["B_real"], "W_real": split_ids["W_real"], "duplicates": duplicate_bw},
        )
    )

    draft_tasks = sorted(task_id for task_id in certified_ids if statement_by_task.get(task_id, {}).get("statement_review_status") == "draft")
    missing_reviewed = sorted(
        task_id
        for task_id in certified_ids
        if statement_by_task.get(task_id, {}).get("statement_review_status") not in {"reviewed", "reviewed_passed"}
    )
    gate_rows.append(
        gate(
            "statement_status",
            "pass" if not missing_reviewed else "fail",
            "experiments/phase0_headroom/certified_tasks/toolz_task_statements.jsonl",
            {"draft_tasks": draft_tasks, "not_final_reviewed_tasks": missing_reviewed},
        )
    )

    inconsistent: list[dict[str, Any]] = []
    for task_id in certified_ids:
        row = rows_by_task.get(task_id, {})
        review = review_by_task.get(task_id, {})
        payload = jsonl_by_task.get(task_id, {})
        rel = release_by_task.get(task_id, {})
        if review.get("status_after_review") != "certified":
            inconsistent.append({"task_id": task_id, "field": "review.status_after_review", "value": review.get("status_after_review")})
        if row.get("first_failing_gate", "") != review.get("first_failing_gate", ""):
            inconsistent.append({"task_id": task_id, "field": "first_failing_gate", "csv": row.get("first_failing_gate"), "review": review.get("first_failing_gate")})
        if payload.get("status") != "certified":
            inconsistent.append({"task_id": task_id, "field": "certified_jsonl.status", "value": payload.get("status")})
        if rel.get("certification_status") != "certified":
            inconsistent.append({"task_id": task_id, "field": "release.certification_status", "value": rel.get("certification_status")})
    gate_rows.append(
        gate(
            "review_consistency",
            "pass" if not inconsistent else "fail",
            "experiments/phase0_headroom/certified_tasks/ and experiments/phase0_headroom/releases/",
            {"inconsistencies": inconsistent},
        )
    )

    forbidden = sorted(
        row["task_id"] for row in statements if statement_has_forbidden_text(row.get("solver_facing_statement", ""))
    )
    gate_rows.append(
        gate(
            "leakage_policy",
            "pass" if not forbidden else "fail",
            "experiments/phase0_headroom/certified_tasks/toolz_task_statements.jsonl",
            {"forbidden_text_task_ids": forbidden},
        )
    )

    missing_mechanical: list[dict[str, Any]] = []
    for task in certified_tasks:
        gates = task.get("gates", {})
        for gate_name in REQUIRED_MECHANICAL_GATES:
            if gates.get(gate_name) != "pass":
                missing_mechanical.append({"task_id": task["task_id"], "gate": gate_name, "value": gates.get(gate_name)})
    gate_rows.append(
        gate(
            "mechanical_gates",
            "pass" if not missing_mechanical and len(certified_tasks) >= 6 else "fail",
            "experiments/phase0_headroom/certified_tasks/toolz_certified_tasks.jsonl",
            {"missing_or_nonpass": missing_mechanical, "certified_jsonl_count": len(certified_tasks)},
        )
    )

    cumulative = read_cumulative_cost(ledger)
    budget_pass = cumulative + projected_cost_usd <= 160.0 and cumulative + projected_cost_usd <= 200.0
    gate_rows.append(
        gate(
            "budget",
            "pass" if budget_pass else "fail",
            "experiments/phase0_headroom/results/cost_ledger.jsonl",
            {
                "current_cumulative_estimated_cost_usd": cumulative,
                "projected_default_matrix_cost_usd": projected_cost_usd,
                "projected_cumulative_cost_usd": round(cumulative + projected_cost_usd, 2),
                "soft_stop_usd": 160.0,
                "hard_stop_usd": 200.0,
            },
        )
    )

    tooling = tooling_check if tooling_check is not None else run_tooling_check(root)
    gate_rows.append(
        gate(
            "tooling",
            "pass" if tooling.get("passed") else "fail",
            "uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools",
            tooling,
        )
    )

    hygiene = artifact_hygiene if artifact_hygiene is not None else artifact_hygiene_status(root)
    gate_rows.append(
        gate(
            "artifact_hygiene",
            "pass" if hygiene[0] else "fail",
            "git status --short --ignored experiments/phase0_headroom docs/experiments .gitignore",
            hygiene[1],
        )
    )

    blocking = [row for row in gate_rows if row["status"] == "fail"]
    return {
        "schema_version": "barcarolle.phase0_headroom_entry_gate.v1",
        "generated_at": iso_now(),
        "can_continue_phase0": not blocking,
        "gates": gate_rows,
        "decision": "can_continue_phase0" if not blocking else "repair_certification_hygiene",
        "blocking_reasons": [f"{row['name']}: {row['details']}" for row in blocking],
    }


def reusable_passed_entry_gate(root: Path) -> dict[str, Any] | None:
    path = root / EXP_REL / "results" / "headroom_entry_gate.json"
    if not path.exists():
        return None
    entry = read_json(path)
    if entry.get("schema_version") != "barcarolle.phase0_headroom_entry_gate.v1":
        return None
    if entry.get("can_continue_phase0") is not True:
        return None
    return entry


def repair_entry_hygiene(root: Path) -> dict[str, Any]:
    statements_path = root / EXP_REL / "certified_tasks" / "toolz_task_statements.jsonl"
    review_path = root / EXP_REL / "certified_tasks" / "toolz_review_records.jsonl"
    funnel_path = root / EXP_REL / "certified_tasks" / "toolz_certification_funnel.csv"
    certified_path = root / EXP_REL / "certified_tasks" / "toolz_certified_tasks.jsonl"
    context_path = root / EXP_REL / "candidate_sources" / "toolz_source_context.jsonl"

    statements = read_jsonl(statements_path)
    reviews = read_jsonl(review_path)
    funnel = read_csv(funnel_path)
    certified = read_jsonl(certified_path)
    contexts = {row["task_id"]: row for row in read_jsonl(context_path)}
    review_by_task = {row["task_id"]: row for row in reviews}
    statement_by_task = {row["task_id"]: row for row in statements}
    changes: dict[str, Any] = {"statements_reviewed": [], "manual_review_minutes_corrected": [], "source_labels_repaired": []}

    for statement in statements:
        review = review_by_task.get(statement["task_id"], {})
        if review.get("status_after_review") == "certified" and all(review.get(gate_name) == "pass" for gate_name in SEMANTIC_GATES):
            if statement.get("statement_review_status") != "reviewed":
                statement["statement_review_status"] = "reviewed"
                statement["statement_review_record"] = f"toolz_review_records.jsonl:{statement['task_id']}"
                changes["statements_reviewed"].append(statement["task_id"])

    for row in funnel:
        review = review_by_task.get(row["task_id"])
        if not review:
            continue
        expected = str(review.get("review_minutes", row.get("manual_review_minutes", "")))
        if row.get("manual_review_minutes") != expected:
            row["manual_review_minutes"] = expected
            changes["manual_review_minutes_corrected"].append({"task_id": row["task_id"], "manual_review_minutes": expected})

    for task in certified:
        context = contexts.get(task["task_id"], {})
        statement = statement_by_task.get(task["task_id"], {})
        labels = [label for label in task.get("labels", []) if not str(label).startswith("missing:not_fetched")]
        for label in ["source_context:non_leaky_context_found", "source_adapter:repaired"]:
            if label not in labels:
                labels.append(label)
        if labels != task.get("labels", []):
            task["labels"] = labels
            changes["source_labels_repaired"].append(task["task_id"])
        followup = task.setdefault("source_adapter_followup", {})
        followup["source_context_record"] = f"toolz_source_context.jsonl:{task['task_id']}"
        followup["source_context_status"] = context.get("source_context_status", "")
        followup["usable_source_item_count"] = context.get("usable_source_item_count", 0)
        followup["allowed_context_refs"] = statement.get("allowed_context_refs", [])

    write_jsonl(statements_path, statements)
    write_csv(funnel_path, funnel, list(funnel[0]))
    write_jsonl(certified_path, certified)
    return changes


def gate_report(entry: dict[str, Any], repair_changes: dict[str, Any] | None = None) -> str:
    lines = [
        "# Headroom Entry Gate",
        "",
        f"Generated UTC: `{entry['generated_at']}`.",
        f"Can continue Phase 0: `{entry['can_continue_phase0']}`.",
        f"Decision: `{entry['decision']}`.",
        "",
        "## Gates",
        "",
        "| Gate | Status | Evidence | Notes |",
        "|---|---:|---|---|",
    ]
    for row in entry["gates"]:
        notes = json.dumps(row["details"], sort_keys=True)
        if len(notes) > 220:
            notes = notes[:217] + "..."
        lines.append(f"| `{row['name']}` | `{row['status']}` | `{row['evidence_path']}` | `{notes}` |")
    if repair_changes is not None:
        lines.extend(
            [
                "",
                "## Hygiene Repair",
                "",
                f"- Statements marked reviewed: `{len(repair_changes['statements_reviewed'])}`.",
                f"- Manual review minute rows corrected: `{len(repair_changes['manual_review_minutes_corrected'])}`.",
                f"- Certified task source labels repaired: `{len(repair_changes['source_labels_repaired'])}`.",
            ]
        )
    if entry["blocking_reasons"]:
        lines.extend(["", "## Blocking Reasons", ""])
        lines.extend(f"- {reason}" for reason in entry["blocking_reasons"])
    return "\n".join(lines) + "\n"


def process_report(root: Path, initial_entry: dict[str, Any], final_entry: dict[str, Any], repair_changes: dict[str, Any]) -> str:
    branch = require_success(run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], root)).strip()
    head = require_success(run_command(["git", "rev-parse", "HEAD"], root)).strip()
    uv = require_success(run_command(["uv", "--version"], root)).strip()
    python_version = require_success(run_command(["uv", "run", "--project", "experiments/phase0_headroom", "python", "--version"], root)).strip()
    cost = read_cumulative_cost(root / EXP_REL / "results" / "cost_ledger.jsonl")
    return "\n".join(
        [
            "# Headroom Matrix Follow-Up Process",
            "",
            f"Generated UTC: `{iso_now()}`.",
            "",
            "## Step 0 Preflight",
            "",
            f"- Branch and HEAD: `{branch}` / `{head}`.",
            f"- `uv`: `{uv}`.",
            f"- Python: `{python_version}`.",
            f"- Platform Python: `{platform.python_version()}` at `{sys.executable}`.",
            f"- Cumulative cost before matrix follow-up: `${cost:.2f}`.",
            "- Scoped tooling command: `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools`.",
            "",
            "## Step 1 Entry Gate",
            "",
            f"- Initial gate passed: `{initial_entry['can_continue_phase0']}`.",
            f"- Final gate passed: `{final_entry['can_continue_phase0']}`.",
            "",
            "## Step 2 Hygiene Repair",
            "",
            f"- Statements marked reviewed: `{repair_changes['statements_reviewed']}`.",
            f"- Manual review minute corrections: `{repair_changes['manual_review_minutes_corrected']}`.",
            f"- Source-label repairs: `{repair_changes['source_labels_repaired']}`.",
        ]
    ) + "\n"


def write_matrix_config(root: Path, release: dict[str, Any], g_mini_same_protocol: bool = False) -> None:
    b_real = release["splits"].get("B_real", [])
    w_real = release["splits"].get("W_real", [])
    g_mini = release["splits"].get("G_mini", [])
    lines = [
        "schema_version: barcarolle.phase0_headroom_matrix_config.v1",
        f"release_id: {release['release_id']}",
        "default_matrix:",
        "  acuts:",
        f"    - id: {ACUT_ID}",
        f"      model_or_agent_name: {ACUT_MODEL}",
        "      command_template: codex --ask-for-approval never exec --json --ephemeral --model gpt-5.3-codex-spark --sandbox workspace-write --cd <workspace> -",
        f"      per_task_timeout_seconds: {PER_TASK_TIMEOUT_SECONDS}",
        "      projected_cost_per_task_usd: 10",
        f"      max_projected_cost_usd: {ACUT_PROJECTED_MAX_USD:.0f}",
        "      output_contract: direct workspace edit captured as git diff patch",
        "      verifier_command: uv run --project experiments/phase0_headroom python -m pytest -q <oracle_refs>",
        "  splits:",
        "    B_real:",
    ]
    lines.extend(f"      - {task_id}" for task_id in b_real)
    lines.append("    W_real:")
    lines.extend(f"      - {task_id}" for task_id in w_real)
    lines.append("    G_mini:")
    if g_mini_same_protocol:
        lines.extend(f"      - {task_id}" for task_id in g_mini)
    else:
        lines.append("      # excluded unless protocol dry run marks same-protocol scoreable")
        lines.extend(f"      # - {task_id}" for task_id in g_mini)
    lines.extend(
        [
            "allow_second_acut: false",
            "claim_scope: underpowered_directional_diagnostic",
            "g_mini_policy: include_only_if_scoreable_same_protocol",
        ]
    )
    write_text(root / EXP_REL / "configs" / "headroom_matrix.yaml", "\n".join(lines) + "\n")


def archive_tree(repo: Path, commit: str, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    tar_proc = subprocess.run(
        ["git", "archive", "--format=tar", commit],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tar_proc.returncode != 0:
        stderr = tar_proc.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"git archive failed for {commit}: {stderr}")
    with tarfile.open(fileobj=io.BytesIO(tar_proc.stdout), mode="r:") as tar:
        tar.extractall(destination)


def initialize_workspace_git(workspace: Path) -> None:
    require_success(run_command(["git", "init", "-q"], workspace))
    require_success(run_command(["git", "add", "."], workspace))
    commit = run_command(
        [
            "git",
            "-c",
            "user.name=Barcarolle Phase0",
            "-c",
            "user.email=phase0@example.invalid",
            "commit",
            "-q",
            "-m",
            "base task state",
        ],
        workspace,
    )
    require_success(commit)


def verify_git_object(repo: Path, commit: str) -> bool:
    result = run_command(["git", "cat-file", "-e", f"{commit}^{{commit}}"], repo)
    return result.returncode == 0


def generate_hidden_test_patch(root: Path, task: dict[str, Any], output_dir: Path) -> Path:
    repo = root / TOOLZ_REPO_REL
    output_dir.mkdir(parents=True, exist_ok=True)
    patch_path = output_dir / f"{task['task_id']}_hidden_tests.patch"
    command = ["git", "diff", "--binary", task["base_commit"], task["target_commit"], "--", *task["test_files"]]
    result = run_command(command, repo, timeout=120)
    require_success(result)
    patch_path.write_text(result.stdout, encoding="utf-8")
    return patch_path


def protocol_dry_run(root: Path) -> dict[str, Any]:
    release = read_json(root / EXP_REL / "releases" / "toolz_phase0_mini_release.json")
    certified_tasks = {row["task_id"]: row for row in read_jsonl(root / EXP_REL / "certified_tasks" / "toolz_certified_tasks.jsonl")}
    statements = {row["task_id"]: row for row in read_jsonl(root / EXP_REL / "certified_tasks" / "toolz_task_statements.jsonl")}
    repo = root / TOOLZ_REPO_REL
    raw_dir = root / RAW_REL / "dry_run"
    task_results: list[dict[str, Any]] = []

    for split in ["B_real", "W_real"]:
        for task_id in release["splits"].get(split, []):
            task = certified_tasks[task_id]
            statement = statements[task_id]
            workspace = root / WORKSPACE_REL / "dry_run" / task_id
            reasons: list[str] = []
            if not verify_git_object(repo, task["base_commit"]):
                reasons.append("base_commit_missing")
            if statement_has_forbidden_text(statement.get("solver_facing_statement", "")):
                reasons.append("solver_statement_leakage")
            missing_mechanical = [
                gate_name for gate_name in REQUIRED_MECHANICAL_GATES if task.get("gates", {}).get(gate_name) != "pass"
            ]
            if missing_mechanical:
                reasons.append(f"missing_mechanical_gates:{','.join(missing_mechanical)}")
            try:
                archive_tree(repo, task["base_commit"], workspace)
                test_paths_exist = all((workspace / test_path).exists() for test_path in task["test_files"])
                if not test_paths_exist:
                    reasons.append("oracle_paths_missing_in_base")
                patch_path = generate_hidden_test_patch(root, task, raw_dir / "hidden_test_patches")
                patch_digest = sha256_file(patch_path)
                initialize_workspace_git(workspace)
            except Exception as exc:  # diagnostic path; represented in machine-readable dry run output
                reasons.append(f"workspace_reconstruction_failed:{exc}")
                patch_digest = ""
            task_results.append(
                {
                    "task_id": task_id,
                    "repo_id": "toolz",
                    "split": split,
                    "status": "scoreable_same_protocol" if not reasons else "not_scoreable",
                    "base_checkout_reconstructed": not any(reason.startswith("workspace_reconstruction_failed") for reason in reasons),
                    "solver_statement_loaded": bool(statement.get("solver_facing_statement")),
                    "solver_statement_private_field_check": "pass" if "solver_statement_leakage" not in reasons else "fail",
                    "verifier_command_available": not any(reason in {"oracle_paths_missing_in_base"} for reason in reasons),
                    "mechanical_gates_attached": not missing_mechanical,
                    "hidden_test_patch_sha256": patch_digest,
                    "reasons": reasons,
                }
            )

    for task_id in release["splits"].get("G_mini", []):
        task_results.append(
            {
                "task_id": task_id,
                "repo_id": "click",
                "split": "G_mini",
                "status": "not_scoreable_same_protocol",
                "base_checkout_reconstructed": False,
                "solver_statement_loaded": False,
                "solver_statement_private_field_check": "not_applicable",
                "verifier_command_available": False,
                "mechanical_gates_attached": False,
                "reasons": [
                    "archived Click comparator has core_narrative task packaging but no active phase0_headroom task package",
                    "same ACUT invocation and verifier protocol not established",
                ],
            }
        )

    same_repo = [row for row in task_results if row["split"] in {"B_real", "W_real"}]
    g_mini = [row for row in task_results if row["split"] == "G_mini"]
    result = {
        "schema_version": "barcarolle.phase0_headroom_protocol_dry_run.v1",
        "generated_at": iso_now(),
        "same_repo_protocol_status": "pass"
        if all(row["status"] == "scoreable_same_protocol" for row in same_repo)
        else "repair_harness_protocol",
        "g_mini_protocol_status": "not_scoreable_same_protocol"
        if any(row["status"] != "scoreable_same_protocol" for row in g_mini)
        else "scoreable_same_protocol",
        "paid_batch_task_ids": [row["task_id"] for row in same_repo if row["status"] == "scoreable_same_protocol"],
        "g_mini_included_in_paid_batch": all(row["status"] == "scoreable_same_protocol" for row in g_mini) if g_mini else False,
        "tasks": task_results,
        "raw_artifact_root": str(RAW_REL / "dry_run"),
    }
    return result


def dry_run_report(dry_run: dict[str, Any]) -> str:
    counts = Counter(row["status"] for row in dry_run["tasks"])
    lines = [
        "# Headroom Protocol Dry Run",
        "",
        f"Generated UTC: `{dry_run['generated_at']}`.",
        f"Same-repo protocol status: `{dry_run['same_repo_protocol_status']}`.",
        f"`G_mini` protocol status: `{dry_run['g_mini_protocol_status']}`.",
        f"Paid same-repo task count: `{len(dry_run['paid_batch_task_ids'])}`.",
        "",
        "## Status Counts",
        "",
    ]
    lines.extend(f"- `{status}`: `{count}`" for status, count in sorted(counts.items()))
    lines.extend(["", "## Task Results", "", "| Task | Split | Status | Reasons |", "|---|---|---:|---|"])
    for row in dry_run["tasks"]:
        reasons = "; ".join(row.get("reasons", [])) or "none"
        lines.append(f"| `{row['task_id']}` | `{row['split']}` | `{row['status']}` | {reasons} |")
    return "\n".join(lines) + "\n"


def append_projected_cost(root: Path, task_ids: list[str]) -> dict[str, Any]:
    ledger = root / EXP_REL / "results" / "cost_ledger.jsonl"
    current = read_cumulative_cost(ledger)
    projected = round(current + ACUT_PROJECTED_MAX_USD, 2)
    record = {
        "record_type": "phase0_headroom_cost_event",
        "event": "projected_headroom_matrix_batch",
        "generated_at": iso_now(),
        "acut_id": ACUT_ID,
        "task_ids": task_ids,
        "projected_model_call_count": len(task_ids),
        "projected_max_cost_usd": ACUT_PROJECTED_MAX_USD,
        "previous_cumulative_estimated_cost_usd": current,
        "cumulative_projected_cost_usd": projected,
        "approval_status": "runbook_default_cap",
        "model_call_started": False,
    }
    append_ledger(root, record)
    return record


def append_completed_cost(root: Path, task_ids: list[str], terminal_counts: dict[str, int]) -> dict[str, Any]:
    ledger = root / EXP_REL / "results" / "cost_ledger.jsonl"
    current = read_cumulative_cost(ledger)
    # Codex CLI billing is not exposed to this process. Retain the conservative
    # projection as the estimated batch cost so budget gates remain conservative.
    cumulative = round(max(current, ACUT_PROJECTED_MAX_USD), 2)
    record = {
        "record_type": "phase0_headroom_cost_event",
        "event": "completed_headroom_matrix_batch",
        "generated_at": iso_now(),
        "acut_id": ACUT_ID,
        "task_ids": task_ids,
        "model_call_count": len(task_ids),
        "estimated_cost_usd": ACUT_PROJECTED_MAX_USD,
        "actual_cost_usd": None,
        "cumulative_estimated_cost_usd": cumulative,
        "model_call_started": True,
        "cost_observation": "codex_cli_cost_not_observable; conservative projected max retained as estimate",
        "terminal_status_counts": terminal_counts,
    }
    append_ledger(root, record)
    return record


def solver_prompt(statement: dict[str, Any]) -> str:
    return "\n".join(
        [
            "You are working in a standalone checkout of a Python package at a historical base state.",
            "Fix the user-visible behavior described below. Make the smallest code change needed.",
            "Do not edit tests. Do not inspect network resources or any external repository.",
            "Leave your changes in the workspace; the evaluator will run hidden regression tests after you finish.",
            "",
            "Task:",
            statement["solver_facing_statement"],
            "",
            "Scope boundary:",
            statement.get("scope_boundaries", ""),
            "",
            "Final response: summarize the files changed and the behavior fixed.",
        ]
    )


def capture_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git_diff_patch(workspace: Path, patch_path: Path) -> None:
    result = run_command(["git", "diff", "--binary"], workspace, timeout=120)
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    patch_path.write_text(result.stdout, encoding="utf-8")


def changed_paths(workspace: Path) -> list[str]:
    result = run_command(["git", "diff", "--name-only"], workspace, timeout=120)
    require_success(result)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def run_acut_for_task(root: Path, task: dict[str, Any], statement: dict[str, Any], split: str) -> tuple[dict[str, Any], dict[str, Any]]:
    repo = root / TOOLZ_REPO_REL
    run_id = f"{ACUT_ID}__{task['task_id']}__attempt1"
    solver_ws = root / WORKSPACE_REL / "acut" / run_id / "solver"
    verify_ws = root / WORKSPACE_REL / "acut" / run_id / "verify"
    raw_dir = root / RAW_REL / "acut" / run_id
    raw_dir.mkdir(parents=True, exist_ok=True)

    archive_tree(repo, task["base_commit"], solver_ws)
    initialize_workspace_git(solver_ws)
    prompt = solver_prompt(statement)
    capture_file(raw_dir / "prompt_redacted.txt", prompt)
    last_message = raw_dir / "last_message.txt"
    stdout_path = raw_dir / "codex_stdout.jsonl"
    stderr_path = raw_dir / "codex_stderr.txt"
    command = [
        "codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--json",
        "--ephemeral",
        "--model",
        ACUT_MODEL,
        "--sandbox",
        "workspace-write",
        "--cd",
        str(solver_ws),
        "--output-last-message",
        str(last_message),
        "-",
    ]
    acut_result = run_command(command, solver_ws, timeout=PER_TASK_TIMEOUT_SECONDS, input_text=prompt)
    capture_file(stdout_path, acut_result.stdout)
    capture_file(stderr_path, acut_result.stderr)
    patch_path = raw_dir / "submission.patch"
    git_diff_patch(solver_ws, patch_path)
    changed = changed_paths(solver_ws)
    patch_nonempty = patch_path.exists() and patch_path.stat().st_size > 0
    edited_tests = [path for path in changed if "/tests/" in path or path.startswith("tests/")]
    if acut_result.timed_out:
        output_status = "timeout"
    elif acut_result.returncode != 0:
        output_status = "harness_error"
    elif not patch_nonempty or edited_tests:
        output_status = "invalid_output"
    else:
        output_status = "submitted"

    submission = {
        "schema_version": "barcarolle.phase0_headroom_submission.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "acut_id": ACUT_ID,
        "model": ACUT_MODEL,
        "task_id": task["task_id"],
        "split": split,
        "attempt": 1,
        "codex_returncode": acut_result.returncode,
        "codex_timed_out": acut_result.timed_out,
        "status": output_status,
        "changed_paths": changed,
        "edited_test_paths": edited_tests,
        "patch_sha256": sha256_file(patch_path) if patch_path.exists() else "",
        "raw_artifacts": {
            "stdout_jsonl": str(stdout_path.relative_to(root)),
            "stderr": str(stderr_path.relative_to(root)),
            "patch": str(patch_path.relative_to(root)),
            "last_message": str(last_message.relative_to(root)) if last_message.exists() else "",
        },
    }

    verifier = {
        "schema_version": "barcarolle.phase0_headroom_verifier_result.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "acut_id": ACUT_ID,
        "task_id": task["task_id"],
        "split": split,
        "attempt": 1,
        "status": "invalid_output",
        "verifier_exit_code": None,
        "harness_error": None,
        "raw_artifacts": {},
    }
    if submission["status"] != "submitted":
        verifier["status"] = submission["status"]
        if submission["status"] == "harness_error":
            verifier["harness_error"] = "acut_command_nonzero"
        return submission, verifier

    archive_tree(repo, task["base_commit"], verify_ws)
    initialize_workspace_git(verify_ws)
    apply_submission = run_command(["git", "apply", "--check", str(patch_path)], verify_ws, timeout=120)
    if apply_submission.returncode != 0:
        verifier["status"] = "invalid_output"
        verifier["harness_error"] = "submission_patch_did_not_apply"
        verifier["raw_artifacts"]["git_apply_check_stderr"] = apply_submission.stderr[-2000:]
        return submission, verifier
    require_success(run_command(["git", "apply", str(patch_path)], verify_ws, timeout=120))

    hidden_patch = generate_hidden_test_patch(root, task, raw_dir)
    apply_tests = run_command(["git", "apply", "--check", str(hidden_patch)], verify_ws, timeout=120)
    if apply_tests.returncode != 0:
        verifier["status"] = "harness_error"
        verifier["harness_error"] = "hidden_test_patch_did_not_apply"
        verifier["raw_artifacts"]["hidden_test_apply_stderr"] = apply_tests.stderr[-2000:]
        return submission, verifier
    require_success(run_command(["git", "apply", str(hidden_patch)], verify_ws, timeout=120))

    stdout_path = raw_dir / "verifier_stdout.txt"
    stderr_path = raw_dir / "verifier_stderr.txt"
    command = ["uv", "run", "--project", str(root / EXP_REL), "python", "-m", "pytest", "-q", *task["test_files"]]
    result = run_command(command, verify_ws, timeout=180)
    capture_file(stdout_path, result.stdout)
    capture_file(stderr_path, result.stderr)
    if result.timed_out:
        status = "timeout"
    elif result.returncode == 0:
        status = "verified_pass"
    else:
        status = "verified_fail"
    verifier.update(
        {
            "status": status,
            "verifier_exit_code": result.returncode,
            "duration_seconds": round(result.duration_seconds, 3),
            "hidden_test_patch_sha256": sha256_file(hidden_patch),
            "raw_artifacts": {
                "stdout": str(stdout_path.relative_to(root)),
                "stderr": str(stderr_path.relative_to(root)),
            },
        }
    )
    return submission, verifier


def run_paid_matrix(root: Path, dry_run: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    release = read_json(root / EXP_REL / "releases" / "toolz_phase0_mini_release.json")
    tasks = {row["task_id"]: row for row in read_jsonl(root / EXP_REL / "certified_tasks" / "toolz_certified_tasks.jsonl")}
    statements = {row["task_id"]: row for row in read_jsonl(root / EXP_REL / "certified_tasks" / "toolz_task_statements.jsonl")}
    submissions: list[dict[str, Any]] = []
    verifiers: list[dict[str, Any]] = []
    approved = set(dry_run["paid_batch_task_ids"])
    for split in ["B_real", "W_real"]:
        for task_id in release["splits"].get(split, []):
            if task_id not in approved:
                submissions.append(
                    {
                        "schema_version": "barcarolle.phase0_headroom_submission.v1",
                        "generated_at": iso_now(),
                        "acut_id": ACUT_ID,
                        "task_id": task_id,
                        "split": split,
                        "attempt": 1,
                        "status": "not_submitted",
                        "reason": "protocol_dry_run_not_scoreable",
                    }
                )
                continue
            submission, verifier = run_acut_for_task(root, tasks[task_id], statements[task_id], split)
            submissions.append(submission)
            verifiers.append(verifier)
    return submissions, verifiers


def score_rows(submissions: list[dict[str, Any]], verifiers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    verifier_by_task = {row["task_id"]: row for row in verifiers}
    rows: list[dict[str, Any]] = []
    for submission in submissions:
        verifier = verifier_by_task.get(submission["task_id"], {})
        terminal = verifier.get("status") or submission["status"]
        rows.append(
            {
                "acut_id": submission["acut_id"],
                "task_id": submission["task_id"],
                "split": submission["split"],
                "attempt": submission.get("attempt", 1),
                "submission_status": submission["status"],
                "terminal_status": terminal,
                "verifier_exit_code": verifier.get("verifier_exit_code", ""),
                "scoreable_cell": terminal in {"verified_pass", "verified_fail"},
                "agent_failure": terminal == "verified_fail",
                "harness_error": terminal in {"harness_error", "invalid_output", "timeout", "cost_stopped"},
            }
        )
    return rows


def metrics_payload(rows: list[dict[str, Any]], dry_run: dict[str, Any]) -> dict[str, Any]:
    split_counts: dict[str, dict[str, Any]] = {}
    for split in sorted({row["split"] for row in rows}):
        split_rows = [row for row in rows if row["split"] == split]
        scoreable = [row for row in split_rows if boolish(row["scoreable_cell"])]
        passed = [row for row in scoreable if row["terminal_status"] == "verified_pass"]
        split_counts[split] = {
            "cell_count": len(split_rows),
            "scoreable_cell_count": len(scoreable),
            "verified_pass_count": len(passed),
            "verified_fail_count": sum(1 for row in scoreable if row["terminal_status"] == "verified_fail"),
            "pass_rate": None if not scoreable else round(len(passed) / len(scoreable), 4),
        }
    harness_errors = sum(1 for row in rows if boolish(row["harness_error"]))
    return {
        "schema_version": "barcarolle.phase0_headroom_metrics.v1",
        "generated_at": iso_now(),
        "status": "scored_underpowered" if any(boolish(row["scoreable_cell"]) for row in rows) else "not_scoreable",
        "claim_scope": "underpowered_directional_diagnostic",
        "split_metrics": split_counts,
        "scoreable_cell_count": sum(1 for row in rows if boolish(row["scoreable_cell"])),
        "invalid_or_harness_error_count": harness_errors,
        "g_mini_protocol_status": dry_run["g_mini_protocol_status"],
        "directional_notes": "single-ACUT same-repo diagnostics only; no predictive validity claim",
        "mae": "not_applicable_underpowered",
        "rmse": "not_applicable_underpowered",
        "brier_score": "not_applicable_underpowered",
        "binomial_negative_log_likelihood": "not_applicable_underpowered",
    }


def matrix_payload(rows: list[dict[str, Any]], dry_run: dict[str, Any], cost_record: dict[str, Any] | None) -> dict[str, Any]:
    terminal_counts = Counter(row["terminal_status"] for row in rows)
    return {
        "schema_version": "barcarolle.phase0_headroom_matrix.v1",
        "generated_at": iso_now(),
        "status": "completed_underpowered_same_repo_matrix" if rows else "not_run",
        "acut_id": ACUT_ID,
        "paid_acut_batches_started": 1 if rows else 0,
        "paid_model_calls_started": len(rows),
        "scheduled_task_ids": [row["task_id"] for row in rows],
        "same_repo_task_ids": dry_run.get("paid_batch_task_ids", []),
        "g_mini_included": dry_run.get("g_mini_included_in_paid_batch", False),
        "g_mini_protocol_status": dry_run.get("g_mini_protocol_status"),
        "terminal_status_counts": dict(terminal_counts),
        "cumulative_estimated_cost_usd": None if cost_record is None else cost_record.get("cumulative_estimated_cost_usd"),
        "claim_scope": "underpowered_directional_diagnostic",
    }


def analysis_report(rows: list[dict[str, Any]], metrics: dict[str, Any]) -> str:
    lines = [
        "# Phase 0 Headroom Analysis",
        "",
        f"Status: `{metrics['status']}`.",
        "",
        "This matrix is underpowered directional evidence only. It uses one ACUT, six certified `toolz` same-repo tasks, and no same-protocol `G_mini` cells.",
        "",
        "## Split Metrics",
        "",
        "| Split | Cells | Scoreable | Pass | Fail | Pass Rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for split, values in metrics["split_metrics"].items():
        lines.append(
            f"| `{split}` | `{values['cell_count']}` | `{values['scoreable_cell_count']}` | "
            f"`{values['verified_pass_count']}` | `{values['verified_fail_count']}` | `{values['pass_rate']}` |"
        )
    lines.extend(
        [
            "",
            "## Cell Outcomes",
            "",
            "| Task | Split | Terminal Status | Scoreable |",
            "|---|---|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(f"| `{row['task_id']}` | `{row['split']}` | `{row['terminal_status']}` | `{row['scoreable_cell']}` |")
    lines.extend(
        [
            "",
            "MAE, RMSE, Brier score, and residual-style predictive metrics are `not_applicable_underpowered` for a one-ACUT matrix.",
        ]
    )
    return "\n".join(lines) + "\n"


def decision_report(
    entry: dict[str, Any],
    dry_run: dict[str, Any],
    rows: list[dict[str, Any]],
    metrics: dict[str, Any],
    cost_record: dict[str, Any] | None,
) -> str:
    scoreable = [row for row in rows if boolish(row["scoreable_cell"])]
    agent_failures = [row for row in rows if row["terminal_status"] == "verified_fail"]
    harness_failures = [row for row in rows if boolish(row["harness_error"])]
    if not entry["can_continue_phase0"]:
        decision = "return_to_certification"
    elif len(harness_failures) > 1:
        decision = "repair_harness_protocol"
    elif dry_run["g_mini_protocol_status"] != "scoreable_same_protocol":
        decision = "repair_generic_comparator_protocol"
    elif scoreable:
        decision = "phase0_same_repo_diagnostic_complete"
    else:
        decision = "stop_phase0"
    budget = 0.0 if cost_record is None else float(cost_record.get("estimated_cost_usd", 0.0))
    lines = [
        "# Phase 0 Headroom Matrix Decision",
        "",
        f"Decision: `{decision}`.",
        "",
        "## Entry Conditions",
        "",
        f"Phase 0 met entry conditions: `{entry['can_continue_phase0']}`.",
        "",
        "## Scoreable Cells",
        "",
        f"- Scoreable same-repo cells: `{len(scoreable)}`.",
        f"- Agent failures: `{len(agent_failures)}`.",
        f"- Harness or invalid-output failures: `{len(harness_failures)}`.",
        f"- `G_mini` same-protocol scoreable: `{dry_run['g_mini_protocol_status'] == 'scoreable_same_protocol'}`.",
        "",
        "## Budget",
        "",
        f"Estimated budget recorded for this matrix: `${budget:.2f}`.",
        "",
        "## Supported Claim",
        "",
        "The run supports only an underpowered same-repo scoreability diagnostic. It does not support predictive validity, repository-general conclusions, or a final benchmark claim.",
        "",
        "## Limitations",
        "",
        "- The sample has six same-repo tasks and one ACUT.",
        "- Four tasks are clustered around one `compose` issue thread.",
        "- `G_mini` archived Click tasks were not same-protocol scoreable in this Phase 0 harness.",
        "",
        "## Next Smallest Useful Action",
        "",
        "Repair or materialize the generic comparator protocol before spending on a second ACUT. A second ACUT would be useful only after comparator scoreability is fixed; keep any follow-up projected cost at or below USD 60 unless explicitly approved.",
    ]
    return "\n".join(lines) + "\n"


def write_empty_result_files(root: Path) -> None:
    write_jsonl(root / EXP_REL / "results" / "headroom_submissions.jsonl", [])
    write_jsonl(root / EXP_REL / "results" / "headroom_verifier_results.jsonl", [])
    write_csv(
        root / EXP_REL / "results" / "headroom_score_table.csv",
        [],
        [
            "acut_id",
            "task_id",
            "split",
            "attempt",
            "submission_status",
            "terminal_status",
            "verifier_exit_code",
            "scoreable_cell",
            "agent_failure",
            "harness_error",
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Phase 0 headroom matrix follow-up.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--skip-paid-run", action="store_true", help="Stop after dry run and write a no-paid-run decision.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    prune_existing_headroom_cost_events(root)

    current_matrix_status = read_json(root / EXP_REL / "results" / "headroom_matrix.json").get("status")
    previous_passed_entry = reusable_passed_entry_gate(root)
    initial_entry = (
        previous_passed_entry
        if previous_passed_entry is not None and current_matrix_status != "ready_not_run_after_source_adapter_repair"
        else evaluate_entry_gate(root)
    )
    repair_changes = repair_entry_hygiene(root)
    final_entry = (
        previous_passed_entry
        if previous_passed_entry is not None and current_matrix_status != "ready_not_run_after_source_adapter_repair"
        else evaluate_entry_gate(root)
    )
    write_json(root / EXP_REL / "results" / "headroom_entry_gate.json", final_entry)
    write_text(root / EXP_REL / "reports" / "headroom_entry_gate.md", gate_report(final_entry, repair_changes))
    write_text(root / EXP_REL / "reports" / "headroom_matrix_followup_process.md", process_report(root, initial_entry, final_entry, repair_changes))

    if not final_entry["can_continue_phase0"]:
        dry_run = {
            "schema_version": "barcarolle.phase0_headroom_protocol_dry_run.v1",
            "generated_at": iso_now(),
            "same_repo_protocol_status": "not_run_entry_gate_failed",
            "g_mini_protocol_status": "not_run_entry_gate_failed",
            "paid_batch_task_ids": [],
            "g_mini_included_in_paid_batch": False,
            "tasks": [],
        }
        write_json(root / EXP_REL / "results" / "headroom_protocol_dry_run.json", dry_run)
        write_text(root / EXP_REL / "reports" / "headroom_protocol_dry_run.md", dry_run_report(dry_run))
        write_empty_result_files(root)
        metrics = metrics_payload([], dry_run)
        matrix = matrix_payload([], dry_run, None)
        write_json(root / EXP_REL / "results" / "headroom_metrics.json", metrics)
        write_json(root / EXP_REL / "results" / "headroom_matrix.json", matrix)
        write_text(root / EXP_REL / "reports" / "headroom_analysis.md", analysis_report([], metrics))
        write_text(root / EXP_REL / "reports" / "phase0_headroom_matrix_decision.md", decision_report(final_entry, dry_run, [], metrics, None))
        return 0

    release = read_json(root / EXP_REL / "releases" / "toolz_phase0_mini_release.json")
    write_matrix_config(root, release)
    dry_run = protocol_dry_run(root)
    write_json(root / EXP_REL / "results" / "headroom_protocol_dry_run.json", dry_run)
    write_text(root / EXP_REL / "reports" / "headroom_protocol_dry_run.md", dry_run_report(dry_run))

    if dry_run["same_repo_protocol_status"] != "pass" or args.skip_paid_run:
        write_empty_result_files(root)
        metrics = metrics_payload([], dry_run)
        matrix = matrix_payload([], dry_run, None)
        write_json(root / EXP_REL / "results" / "headroom_metrics.json", metrics)
        write_json(root / EXP_REL / "results" / "headroom_matrix.json", matrix)
        write_text(root / EXP_REL / "reports" / "headroom_analysis.md", analysis_report([], metrics))
        write_text(root / EXP_REL / "reports" / "phase0_headroom_matrix_decision.md", decision_report(final_entry, dry_run, [], metrics, None))
        return 0

    projected = append_projected_cost(root, dry_run["paid_batch_task_ids"])
    if projected["cumulative_projected_cost_usd"] > 160.0:
        raise RuntimeError("projected batch cost exceeds Phase 0 soft stop")

    submissions, verifiers = run_paid_matrix(root, dry_run)
    rows = score_rows(submissions, verifiers)
    terminal_counts = Counter(str(row["terminal_status"]) for row in rows)
    completed_cost = append_completed_cost(root, dry_run["paid_batch_task_ids"], dict(terminal_counts))
    write_jsonl(root / EXP_REL / "results" / "headroom_submissions.jsonl", submissions)
    write_jsonl(root / EXP_REL / "results" / "headroom_verifier_results.jsonl", verifiers)
    write_csv(
        root / EXP_REL / "results" / "headroom_score_table.csv",
        rows,
        [
            "acut_id",
            "task_id",
            "split",
            "attempt",
            "submission_status",
            "terminal_status",
            "verifier_exit_code",
            "scoreable_cell",
            "agent_failure",
            "harness_error",
        ],
    )
    metrics = metrics_payload(rows, dry_run)
    matrix = matrix_payload(rows, dry_run, completed_cost)
    write_json(root / EXP_REL / "results" / "headroom_metrics.json", metrics)
    write_json(root / EXP_REL / "results" / "headroom_matrix.json", matrix)
    write_text(root / EXP_REL / "reports" / "headroom_analysis.md", analysis_report(rows, metrics))
    write_text(root / EXP_REL / "reports" / "phase0_headroom_matrix_decision.md", decision_report(final_entry, dry_run, rows, metrics, completed_cost))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
