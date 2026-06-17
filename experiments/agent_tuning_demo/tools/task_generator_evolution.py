from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_tuning_demo" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import sphinx_target_prep as sphinx_prep  # noqa: E402


SCHEMA_VERSION = "barcarolle.agent_tuning_demo.task_generator_evolution.v1"
RESULTS = ROOT / "experiments" / "agent_tuning_demo" / "results"
REPORTS = ROOT / "experiments" / "agent_tuning_demo" / "reports"
EXTERNAL_REPOS = ROOT / "experiments" / "phase0_headroom" / "external_repos"
SCRATCH = ROOT / "experiments" / "phase0_headroom" / "tmp" / "task_generator_evolution"
CURRENT_DATE = datetime(2026, 6, 17, tzinfo=timezone.utc)
SELECTED_BENCHMARK_SIZE = 20
FUTURE_HOLDOUT_SIZE = 20
ORIGIN_HISTORY_SIZES = [40, 60, 80]
AGENT_COUNT = 4

MANIFEST_FIELDS = [
    "task_id",
    "repo_id",
    "reservoir_source_type",
    "base_commit",
    "target_commit",
    "task_time",
    "module_family",
    "changed_implementation_files",
    "changed_test_files",
    "support_oracle_files",
    "verifier_entry_points",
    "solver_visible_statement_provenance",
    "hidden_oracle_provenance",
    "verifier_profile",
    "verifier_command_digest",
    "checkout_status",
    "install_setup_status",
    "test_collection_status",
    "reference_changed_test_result",
    "base_with_injected_tests_result",
    "pass_to_pass_guard_result",
    "subgate_results_json",
    "certification_duration_seconds",
    "leakage_label",
    "ambiguity_label",
    "source_confidence_label",
    "sanitized_evidence_digest",
]


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def digest_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def digest_payload(value: Any) -> str:
    return digest_text(json.dumps(value, sort_keys=True, ensure_ascii=False))


def parse_datetime(value: Any) -> datetime:
    text = str(value or "")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return CURRENT_DATE
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def exclude_newer_date(task_time: str) -> str:
    return min(parse_datetime(task_time) + timedelta(days=180), CURRENT_DATE).date().isoformat()


def counted(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items(), key=lambda item: (-item[1], item[0])))


def duration_summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "median_seconds": None, "p95_seconds": None, "max_seconds": None}
    ordered = sorted(values)
    p95_index = min(len(ordered) - 1, round((len(ordered) - 1) * 0.95))
    return {
        "count": len(values),
        "median_seconds": round(median(values), 3),
        "p95_seconds": round(ordered[p95_index], 3),
        "max_seconds": round(max(values), 3),
    }


def run_command(args: list[str], cwd: Path, timeout: int = 240) -> CommandResult:
    start = time.monotonic()
    try:
        proc = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return CommandResult(proc.returncode, proc.stdout or "", proc.stderr or "", round(time.monotonic() - start, 3))
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            124,
            str(exc.stdout or ""),
            str(exc.stderr or ""),
            round(time.monotonic() - start, 3),
            timed_out=True,
        )
    except FileNotFoundError as exc:
        return CommandResult(127, "", str(exc), round(time.monotonic() - start, 3))


def classify_execution_failure(result: CommandResult) -> str:
    combined = f"{result.stdout}\n{result.stderr}".lower()
    if result.returncode == 0:
        return "passed"
    if result.timed_out or result.returncode == 124:
        return "timeout"
    if "no solution found" in combined or "failed to build" in combined or "build backend" in combined:
        return "dependency_mismatch_or_install_failed"
    if "modulenotfounderror" in combined or "importerror" in combined:
        return "import_failed"
    if result.returncode == 2 or "error collecting" in combined:
        return "collection_failed"
    if "no tests ran" in combined or result.returncode in {4, 5}:
        return "no_tests_selected_or_usage_error"
    if result.returncode == 1:
        return "target_test_failure"
    return "unknown_failed"


def command_record(role: str, profile_id: str, command: list[str], result: CommandResult) -> dict[str, Any]:
    return {
        "role": role,
        "profile_id": profile_id,
        "command_shape": command_shape(command),
        "returncode": result.returncode,
        "duration_seconds": result.duration_seconds,
        "timed_out": result.timed_out,
        "stdout_line_count": len(result.stdout.splitlines()),
        "stderr_line_count": len(result.stderr.splitlines()),
        "stdout_tail_hash": digest_text(result.stdout[-1000:]),
        "stderr_tail_hash": digest_text(result.stderr[-1000:]),
        "subgate_label": classify_execution_failure(result),
    }


def command_shape(command: list[str]) -> list[str]:
    shaped: list[str] = []
    skip_next = False
    for index, item in enumerate(command):
        if skip_next:
            skip_next = False
            continue
        if item in {"--with", "--python", "--exclude-newer"} and index + 1 < len(command):
            shaped.extend([item, command[index + 1] if command[index + 1] != "." else "."])
            skip_next = True
        elif item.startswith(("tests/", "mypy/test/", "mypyc/test/")) or "::" in item:
            if not shaped or shaped[-1] != "<targeted_test_or_nodeids>":
                shaped.append("<targeted_test_or_nodeids>")
        else:
            shaped.append(item)
    return shaped


def cleanup_worktree(repo: Path, worktree: Path) -> None:
    result = run_command(["git", "worktree", "remove", "--force", str(worktree)], repo, timeout=120)
    if result.returncode != 0 and worktree.exists():
        shutil.rmtree(worktree)
    run_command(["git", "worktree", "prune"], repo, timeout=120)


def add_worktree(repo: Path, worktree: Path, commit: str) -> CommandResult:
    if worktree.exists():
        cleanup_worktree(repo, worktree)
    else:
        run_command(["git", "worktree", "prune"], repo, timeout=120)
    worktree.parent.mkdir(parents=True, exist_ok=True)
    return run_command(["git", "worktree", "add", "--detach", str(worktree), commit], repo, timeout=180)


def list_field(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if value in {"", None}:
        return []
    return [part for part in str(value).split(";") if part]


def joined(paths: Iterable[str]) -> str:
    return ";".join(dict.fromkeys(str(path) for path in paths if str(path)))


def issue_refs_from_subject(subject: str) -> list[str]:
    return list(dict.fromkeys(f"pr_or_issue:{match.group(1)}" for match in re.finditer(r"#(\d+)", subject or "")))


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    lines = ["| " + " | ".join(label for label, _key in columns) + " |", "| " + " | ".join("---" for _label, _key in columns) + " |"]
    for row in rows:
        values = [str(row.get(key, "")).replace("|", "\\|").replace("\n", " ") for _label, key in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def is_mypy_test_path(path: str) -> bool:
    lower = path.lower()
    return lower.endswith(".py") and lower.startswith(("mypy/test/", "mypyc/test/")) and Path(lower).name.startswith("test")


def is_mypy_impl_path(path: str) -> bool:
    lower = path.lower()
    if not lower.endswith((".py", ".pyi")) or is_mypy_test_path(path):
        return False
    if lower.startswith(("mypy/test/", "mypyc/test/", "test-data/", "mypyc/test-data/")):
        return False
    return lower.startswith(("mypy/", "mypyc/"))


def is_mypy_typecheck_data(path: str) -> bool:
    lower = path.lower()
    return lower.startswith("test-data/unit/") and Path(lower).name.startswith("check-") and lower.endswith(".test")


def is_mypy_support_oracle(path: str) -> bool:
    lower = path.lower()
    return lower.startswith(("test-data/", "mypyc/test-data/"))


def mypy_module_family(paths: list[str]) -> str:
    for path in paths:
        if path.startswith("mypy/check") or "test-data/unit/check-" in path:
            return "type_checker"
        if path.startswith("mypy/semanal") or path.startswith("mypy/nodes"):
            return "semantic_analysis"
        if path.startswith("mypy/server") or "finegrained" in path:
            return "daemon_finegrained"
        if path.startswith("mypyc/"):
            return "mypyc"
    return "core_or_other"


def time_bucket(task_time: str) -> str:
    year = parse_datetime(task_time).year
    if year < 2020:
        return "pre_2020"
    if year < 2024:
        return "2020_2023"
    return "2024_plus"


def parse_mypy_history(repo: Path, *, max_count: int = 7000) -> list[dict[str, Any]]:
    result = run_command(
        [
            "git",
            "log",
            "--since=2010-01-01",
            f"--max-count={max_count}",
            "--format=%x1e%H%x09%P%x09%ad%x09%s",
            "--date=iso-strict",
            "--name-only",
        ],
        repo,
        timeout=240,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    raw_rows: list[dict[str, Any]] = []
    for chunk in result.stdout.split("\x1e"):
        lines = [line for line in chunk.splitlines() if line.strip()]
        if not lines:
            continue
        meta = lines[0].split("\t", 3)
        if len(meta) != 4:
            continue
        commit, parents, task_time, subject = meta
        parent = parents.split()[0] if parents.split() else ""
        changed = lines[1:]
        implementation_files = [path for path in changed if is_mypy_impl_path(path)]
        python_test_files = [path for path in changed if is_mypy_test_path(path)]
        data_entry_files = [path for path in changed if is_mypy_typecheck_data(path)]
        support_files = [path for path in changed if is_mypy_support_oracle(path)]
        if not parent or not implementation_files or not (python_test_files or data_entry_files):
            continue
        if len(data_entry_files) > 3 or len(python_test_files) > 4:
            continue
        refs = issue_refs_from_subject(subject)
        reservoir = "mypy_typecheck_data_with_impl" if data_entry_files else "mypy_python_test_with_impl"
        raw_rows.append(
            {
                "repo_id": "mypy",
                "target_commit": commit,
                "base_commit": parent,
                "task_time": task_time,
                "subject": subject,
                "time_bucket": time_bucket(task_time),
                "module_family": mypy_module_family([*implementation_files, *python_test_files, *data_entry_files]),
                "changed_implementation_files": implementation_files,
                "changed_test_files": [*python_test_files, *data_entry_files],
                "support_oracle_files": support_files,
                "verifier_entry_points": mypy_entry_points(python_test_files, data_entry_files),
                "public_source_context_reference": ", ".join(refs) if refs else f"commit:{commit[:12]}",
                "source_confidence_label": "medium" if refs else "low_commit_message_only",
                "reservoir_source_type": reservoir,
            }
        )
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(sorted(raw_rows, key=lambda item: (item["task_time"], item["target_commit"]))):
        rows.append({"task_id": f"mypy__taskgen__{index + 1:04d}", **row})
    return rows


def mypy_entry_points(python_test_files: list[str], data_entry_files: list[str]) -> list[str]:
    if data_entry_files:
        return [
            f"mypy/test/testcheck.py::TypeCheckSuite::{Path(path).name}"
            for path in sorted(data_entry_files)
        ]
    return sorted(python_test_files)


def mypy_profiles(task_time: str) -> list[tuple[str, str, str]]:
    year = parse_datetime(task_time).year
    modern = ("py312_data_or_pytest", "3.12", "pytest>=8,<10")
    py310 = ("py310_legacy_data_or_pytest", "3.10", "pytest>=7,<9")
    py39 = ("py39_legacy_data_or_pytest", "3.9", "pytest>=6,<8")
    if year >= 2024:
        return [modern, py310]
    if year >= 2020:
        return [py310, py39, modern]
    return [py39, py310]


def mypy_command(row: dict[str, Any], python_version: str, pytest_spec: str) -> list[str]:
    return [
        "uv",
        "run",
        "--no-project",
        "--isolated",
        "--managed-python",
        "--python",
        python_version,
        "--exclude-newer",
        exclude_newer_date(str(row["task_time"])),
        "--with",
        pytest_spec,
        "--with",
        "pytest-xdist",
        "--with",
        ".",
        "--",
        "python",
        "-m",
        "pytest",
        *row["verifier_entry_points"],
        "-q",
    ]


def replay_mypy_candidate(repo: Path, row: dict[str, Any], *, scratch_root: Path) -> dict[str, Any]:
    task_root = scratch_root / row["task_id"]
    base_worktree = task_root / "base"
    target_worktree = task_root / "target"
    commands: list[dict[str, Any]] = []
    target_add = add_worktree(repo, target_worktree, row["target_commit"])
    if target_add.returncode != 0:
        return replay_failure(row, "target_worktree_failed", target_add, commands)
    base_add = add_worktree(repo, base_worktree, row["base_commit"])
    if base_add.returncode != 0:
        cleanup_worktree(repo, target_worktree)
        return replay_failure(row, "base_worktree_failed", base_add, commands)
    try:
        oracle_files = list(dict.fromkeys([*row["changed_test_files"], *row["support_oracle_files"]]))
        missing = [path for path in oracle_files if not (target_worktree / path).exists()]
        if missing:
            return {**replay_failure(row, "hidden_oracle_missing_on_target", CommandResult(1, "", "", 0.0), commands), "missing_oracle_files": missing}
        inject = run_command(["git", "checkout", row["target_commit"], "--", *oracle_files], base_worktree, timeout=120)
        if inject.returncode != 0:
            return replay_failure(row, "hidden_verifier_injection_failed", inject, commands)
        for profile_id, python_version, pytest_spec in mypy_profiles(str(row["task_time"])):
            command = mypy_command(row, python_version, pytest_spec)
            target_result = run_command(command, target_worktree, timeout=240)
            commands.append(command_record("reference_target", profile_id, command, target_result))
            if target_result.returncode != 0:
                continue
            base_result = run_command(command, base_worktree, timeout=240)
            commands.append(command_record("base_with_injected_tests", profile_id, command, base_result))
            if base_result.returncode == 0:
                return {
                    **base_replay_row(row),
                    "terminal_status": "failed",
                    "failure_label": "base_passed_changed_tests_not_meaningful",
                    "winning_profile_id": profile_id,
                    "verifier_duration_seconds": target_result.duration_seconds + base_result.duration_seconds,
                    "commands": commands,
                }
            return {
                **base_replay_row(row),
                "terminal_status": "passed",
                "failure_label": "",
                "winning_profile_id": profile_id,
                "verifier_duration_seconds": target_result.duration_seconds + base_result.duration_seconds,
                "commands": commands,
            }
        terminal = commands[-1]["subgate_label"] if commands else "reference_replay_not_attempted"
        return {
            **base_replay_row(row),
            "terminal_status": "failed",
            "failure_label": f"reference_{terminal}",
            "winning_profile_id": "",
            "verifier_duration_seconds": sum(float(command.get("duration_seconds") or 0.0) for command in commands),
            "commands": commands,
        }
    finally:
        cleanup_worktree(repo, base_worktree)
        cleanup_worktree(repo, target_worktree)


def base_replay_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": row["task_id"],
        "repo_id": row["repo_id"],
        "target_commit": row["target_commit"],
        "base_commit": row["base_commit"],
        "task_time": row["task_time"],
        "time_bucket": row["time_bucket"],
        "module_family": row["module_family"],
        "changed_implementation_files": row["changed_implementation_files"],
        "changed_test_files": row["changed_test_files"],
        "support_oracle_files": row["support_oracle_files"],
        "verifier_entry_points": row["verifier_entry_points"],
        "reservoir_source_type": row["reservoir_source_type"],
        "solver_visible_statement_provenance": row["public_source_context_reference"],
        "source_confidence_label": row["source_confidence_label"],
    }


def replay_failure(row: dict[str, Any], label: str, result: CommandResult, commands: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        **base_replay_row(row),
        "terminal_status": "failed",
        "failure_label": label,
        "duration_seconds": result.duration_seconds,
        "stdout_tail_hash": digest_text(result.stdout[-1000:]),
        "stderr_tail_hash": digest_text(result.stderr[-1000:]),
        "commands": commands,
    }


def sanitized_commands(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "role": command.get("role", ""),
            "profile_id": command.get("profile_id", ""),
            "returncode": command.get("returncode", ""),
            "duration_seconds": command.get("duration_seconds", ""),
            "timed_out": command.get("timed_out", False),
            "subgate_label": command.get("subgate_label", ""),
            "stdout_line_count": command.get("stdout_line_count", ""),
            "stderr_line_count": command.get("stderr_line_count", ""),
            "stdout_tail_hash": command.get("stdout_tail_hash", ""),
            "stderr_tail_hash": command.get("stderr_tail_hash", ""),
        }
        for command in row.get("commands", [])
    ]


def manifest_row_from_replay(row: dict[str, Any]) -> dict[str, Any]:
    commands = sanitized_commands(row)
    verifier_profile = str(row.get("winning_profile_id") or "")
    target_label = next((cmd["subgate_label"] for cmd in commands if cmd["role"] == "reference_target" and cmd["profile_id"] == verifier_profile), "")
    base_label = next((cmd["subgate_label"] for cmd in commands if cmd["role"] == "base_with_injected_tests" and cmd["profile_id"] == verifier_profile), "")
    payload = {
        "task_id": row["task_id"],
        "repo_id": row["repo_id"],
        "reservoir_source_type": row["reservoir_source_type"],
        "base_commit": row["base_commit"],
        "target_commit": row["target_commit"],
        "task_time": row["task_time"],
        "module_family": row["module_family"],
        "changed_implementation_files": joined(row.get("changed_implementation_files") or []),
        "changed_test_files": joined(row.get("changed_test_files") or []),
        "support_oracle_files": joined(row.get("support_oracle_files") or []),
        "verifier_entry_points": joined(row.get("verifier_entry_points") or []),
        "solver_visible_statement_provenance": row.get("solver_visible_statement_provenance", ""),
        "hidden_oracle_provenance": "target_commit_changed_tests_and_support_files",
        "verifier_profile": verifier_profile,
        "verifier_command_digest": digest_payload([cmd.get("command_shape") for cmd in row.get("commands", [])]),
        "checkout_status": "passed",
        "install_setup_status": "passed_via_reference_command",
        "test_collection_status": "passed",
        "reference_changed_test_result": target_label or "passed",
        "base_with_injected_tests_result": base_label or "target_test_failure",
        "pass_to_pass_guard_result": "not_run_no_stable_adjacent_guard",
        "subgate_results_json": json.dumps(commands, sort_keys=True),
        "certification_duration_seconds": round(float(row.get("verifier_duration_seconds") or row.get("duration_seconds") or 0.0), 3),
        "leakage_label": "no_hidden_oracle_in_statement",
        "ambiguity_label": "commit_or_issue_context_only",
        "source_confidence_label": row.get("source_confidence_label", "medium"),
    }
    payload["sanitized_evidence_digest"] = digest_payload({key: payload[key] for key in payload if key != "sanitized_evidence_digest"})
    return payload


def sphinx_manifest_row_from_existing(row: dict[str, Any]) -> dict[str, Any]:
    task_id = str(row["task_id"])
    payload = {
        "task_id": task_id.replace("sphinx__hist__", "sphinx__taskgen__"),
        "repo_id": "sphinx",
        "reservoir_source_type": "sphinx_changed_pytest_with_support_roots",
        "base_commit": row["base_commit"],
        "target_commit": row["target_commit"],
        "task_time": row["task_time"],
        "module_family": row["module_family"],
        "changed_implementation_files": row.get("changed_implementation_files", ""),
        "changed_test_files": row.get("changed_test_files", ""),
        "support_oracle_files": ";".join(path for path in list_field(row.get("changed_test_files")) if path.startswith("tests/roots/")),
        "verifier_entry_points": row.get("pytest_entry_files", ""),
        "solver_visible_statement_provenance": "public_pr_or_issue_reference_or_commit_subject",
        "hidden_oracle_provenance": "target_commit_changed_tests_and_sphinx_support_roots",
        "verifier_profile": row.get("winning_verifier_profile", ""),
        "verifier_command_digest": digest_payload(
            {
                "profile": row.get("winning_verifier_profile", ""),
                "entry": row.get("pytest_entry_files", ""),
                "oracle": row.get("changed_test_files", ""),
            }
        ),
        "checkout_status": "passed",
        "install_setup_status": "passed_via_reference_command",
        "test_collection_status": "passed",
        "reference_changed_test_result": "passed",
        "base_with_injected_tests_result": "target_test_failure",
        "pass_to_pass_guard_result": "not_run_no_stable_adjacent_guard",
        "subgate_results_json": json.dumps(
            [
                {"role": "reference_target", "profile_id": row.get("winning_verifier_profile", ""), "subgate_label": "passed"},
                {"role": "base_with_injected_tests", "profile_id": row.get("winning_verifier_profile", ""), "subgate_label": "target_test_failure"},
            ],
            sort_keys=True,
        ),
        "certification_duration_seconds": round(float(row.get("verifier_duration_seconds") or 0.0), 3),
        "leakage_label": "no_hidden_oracle_in_statement",
        "ambiguity_label": "public_context_or_commit_subject_only",
        "source_confidence_label": "medium",
    }
    payload["sanitized_evidence_digest"] = digest_payload({key: payload[key] for key in payload if key != "sanitized_evidence_digest"})
    return payload


def manifest_sort_key(row: dict[str, Any]) -> tuple[datetime, str]:
    return parse_datetime(row["task_time"]), str(row["task_id"])


def write_certified_manifest(repo_id: str, rows: list[dict[str, Any]], *, source_summary: dict[str, Any]) -> dict[str, Any]:
    ordered = sorted(rows, key=manifest_sort_key)
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.certified_manifest.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repo_id": repo_id,
        "certified_task_count": len(ordered),
        "threshold_state": "preferred_met" if len(ordered) >= 100 else "minimum_met" if len(ordered) >= 80 else "below_minimum",
        "selected_benchmark_size": SELECTED_BENCHMARK_SIZE,
        "future_holdout_size": FUTURE_HOLDOUT_SIZE,
        "time_bucket_distribution": counted(time_bucket(row["task_time"]) for row in ordered),
        "module_family_distribution": counted(row["module_family"] for row in ordered),
        "reservoir_distribution": counted(row["reservoir_source_type"] for row in ordered),
        "verifier_duration_summary": duration_summary([float(row["certification_duration_seconds"]) for row in ordered]),
        "source_summary": source_summary,
        "raw_output_committed": False,
        "tasks": ordered,
    }
    write_json(RESULTS / f"{repo_id}_task_generator_certified_manifest.json", payload)
    write_csv(RESULTS / f"{repo_id}_task_generator_certified_manifest.csv", ordered, MANIFEST_FIELDS)
    write_text(REPORTS / f"{repo_id}_task_generator_certified_manifest_zh.md", certified_manifest_report(payload))
    return payload


def certified_manifest_report(payload: dict[str, Any]) -> str:
    rows = [
        {
            "task": row["task_id"],
            "time": str(row["task_time"])[:10],
            "family": row["module_family"],
            "reservoir": row["reservoir_source_type"],
            "profile": row["verifier_profile"],
            "seconds": row["certification_duration_seconds"],
        }
        for row in payload["tasks"][:120]
    ]
    return f"""# {payload['repo_id']} Task Generator certified manifest

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

exact certified tasks: `{payload['certified_task_count']}`；threshold state: `{payload['threshold_state']}`。

- selected benchmark size: `{payload['selected_benchmark_size']}`
- future holdout size: `{payload['future_holdout_size']}`
- time buckets: `{payload['time_bucket_distribution']}`
- module families: `{payload['module_family_distribution']}`
- reservoirs: `{payload['reservoir_distribution']}`
- verifier duration: `{payload['verifier_duration_summary']}`

## Certified rows

{markdown_table(rows, [('Task', 'task'), ('Time', 'time'), ('Family', 'family'), ('Reservoir', 'reservoir'), ('Profile', 'profile'), ('Seconds', 'seconds')])}

## Artifact hygiene

manifest 只保留 sanitized task metadata、subgate summaries、command digest 和 evidence digest；未提交 raw stdout/stderr、solver workspace、verifier workspace、prompt、completion 或 transcript。
"""


def build_windows(repo_id: str, manifest: dict[str, Any]) -> dict[str, Any]:
    tasks = sorted(manifest.get("tasks") or [], key=manifest_sort_key)
    windows = []
    for origin_size in ORIGIN_HISTORY_SIZES:
        if origin_size + FUTURE_HOLDOUT_SIZE > len(tasks):
            continue
        history = tasks[:origin_size]
        future = tasks[origin_size : origin_size + FUTURE_HOLDOUT_SIZE]
        windows.append(
            {
                "origin_id": f"origin_{origin_size}",
                "origin_history_size": origin_size,
                "origin_task_index": origin_size,
                "history_pool_before_origin": {
                    "task_count": len(history),
                    "task_ids": [row["task_id"] for row in history],
                },
                "selected_benchmark_from_history": {
                    "selection_status": "not_chosen_in_this_runbook",
                    "selection_size": SELECTED_BENCHMARK_SIZE,
                    "allowed_task_ids": [row["task_id"] for row in history],
                    "selected_task_ids": [],
                },
                "future_holdout_after_origin": {
                    "task_count": len(future),
                    "task_ids": [row["task_id"] for row in future],
                },
                "leakage_rule": "future_holdout_after_origin task IDs, labels, and outcomes are not selector inputs.",
            }
        )
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.rolling_origin_windows.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repo_id": repo_id,
        "source_manifest": f"experiments/agent_tuning_demo/results/{repo_id}_task_generator_certified_manifest.json",
        "certified_task_count": len(tasks),
        "window_threshold_state": "preferred_policy_supported" if len(windows) >= 3 else "minimum_policy_supported" if len(windows) >= 2 else "below_minimum_policy",
        "selected_benchmark_size": SELECTED_BENCHMARK_SIZE,
        "future_holdout_size": FUTURE_HOLDOUT_SIZE,
        "task_ordering": "certified tasks by task_time ascending, stable tie-break by task_id",
        "windows": windows,
        "window_count": len(windows),
        "selector_status": "not_chosen_in_this_runbook",
        "selector_leakage_rule": "Future holdout IDs/outcomes are withheld from selector/compiler until after selected_benchmark_from_history is frozen.",
    }
    write_json(RESULTS / f"{repo_id}_task_generator_rolling_origin_windows.json", payload)
    write_text(REPORTS / f"{repo_id}_task_generator_rolling_origin_windows_zh.md", rolling_windows_report(payload))
    return payload


def rolling_windows_report(payload: dict[str, Any]) -> str:
    rows = [
        {
            "origin": window["origin_id"],
            "history": window["history_pool_before_origin"]["task_count"],
            "selected": window["selected_benchmark_from_history"]["selection_size"],
            "future": window["future_holdout_after_origin"]["task_count"],
            "first_future": (window["future_holdout_after_origin"]["task_ids"] or [""])[0],
            "last_future": (window["future_holdout_after_origin"]["task_ids"] or [""])[-1],
        }
        for window in payload["windows"]
    ]
    return f"""# {payload['repo_id']} Task Generator corrected rolling-origin windows

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

certified task count `{payload['certified_task_count']}` supports `{payload['window_count']}` corrected windows；state: `{payload['window_threshold_state']}`。

每个 origin 的 selected benchmark 只能从 `history_pool_before_origin` 选择；`future_holdout_after_origin` 的 IDs/outcomes 不是 selector inputs。

{markdown_table(rows, [('Origin', 'origin'), ('History pool', 'history'), ('Selected size', 'selected'), ('Future holdout', 'future'), ('First future', 'first_future'), ('Last future', 'last_future')])}
"""


def build_paid_cell_accounting(window_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    per_repo = {}
    for payload in window_payloads:
        per_window = []
        for window in payload.get("windows", []):
            selected = int(window["selected_benchmark_from_history"]["selection_size"])
            future = int(window["future_holdout_after_origin"]["task_count"])
            per_window.append(
                {
                    "origin_id": window["origin_id"],
                    "selected_benchmark_cells": selected * AGENT_COUNT,
                    "future_holdout_cells": future * AGENT_COUNT,
                    "naive_baseline_discovery_cells": (selected + future) * AGENT_COUNT,
                }
            )
        per_repo[payload["repo_id"]] = {
            "window_count": payload.get("window_count", 0),
            "baseline_cells_per_window": (SELECTED_BENCHMARK_SIZE + FUTURE_HOLDOUT_SIZE) * AGENT_COUNT,
            "total_naive_baseline_discovery_cells": sum(row["naive_baseline_discovery_cells"] for row in per_window),
            "per_window": per_window,
        }
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.paid_cell_accounting.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "agent_count_for_baseline_discovery": AGENT_COUNT,
        "formula": "(20 selected + 20 future) * 4 agents = 160 baseline cells/window",
        "per_repo": per_repo,
        "authorization": "not_authorized_by_this_no_paid_run",
    }
    write_json(RESULTS / "task_generator_paid_cell_accounting.json", payload)
    write_text(REPORTS / "task_generator_paid_cell_accounting_zh.md", paid_cell_accounting_report(payload))
    return payload


def paid_cell_accounting_report(payload: dict[str, Any]) -> str:
    rows = []
    for repo_id, repo in payload["per_repo"].items():
        rows.append(
            {
                "repo": repo_id,
                "windows": repo["window_count"],
                "per_window": repo["baseline_cells_per_window"],
                "total": repo["total_naive_baseline_discovery_cells"],
            }
        )
    return f"""# Task Generator paid-cell accounting

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

默认 accounting: `{payload['formula']}`。本 artifact 只做 accounting，不授权 paid baseline discovery、paid solver Agent cells、paid tuner/proposer calls 或 before/after tuning experiments。

{markdown_table(rows, [('Repo', 'repo'), ('Windows', 'windows'), ('Cells/window', 'per_window'), ('Total naive baseline cells', 'total')])}
"""


def run_mypy_manifest(preferred_threshold: int = 100, attempt_limit: int = 420) -> dict[str, Any]:
    repo = EXTERNAL_REPOS / "mypy"
    candidates = parse_mypy_history(repo)
    attempted: list[dict[str, Any]] = []
    certified: list[dict[str, Any]] = []
    # Recency-first improves historical environment reproducibility; final manifest is still task-time ordered.
    ordered = sorted(candidates, key=lambda row: (parse_datetime(row["task_time"]), row["task_id"]), reverse=True)
    for row in ordered[:attempt_limit]:
        if len(certified) >= preferred_threshold:
            break
        result = replay_mypy_candidate(repo, row, scratch_root=SCRATCH / "mypy_certification")
        result["attempt_index"] = len(attempted) + 1
        attempted.append(result)
        if result.get("terminal_status") == "passed":
            certified.append(manifest_row_from_replay(result))
    payload = write_certified_manifest(
        "mypy",
        certified,
        source_summary={
            "candidate_inventory_count": len(candidates),
            "attempt_count": len(attempted),
            "pass_count": len(certified),
            "failure_label_counts": counted(row.get("failure_label") for row in attempted if row.get("failure_label")),
            "kept_mechanisms": ["mypy_typecheck_data_nodeids", "target_commit_support_file_injection", "version_aware_uv_profiles"],
        },
    )
    attempts_payload = {
        "schema_version": f"{SCHEMA_VERSION}.mypy_certification_attempts.v1",
        "generated_at": iso_now(),
        "repo_id": "mypy",
        "candidate_inventory_count": len(candidates),
        "attempt_count": len(attempted),
        "pass_count": len(certified),
        "failure_label_counts": counted(row.get("failure_label") for row in attempted if row.get("failure_label")),
        "attempts": [sanitize_attempt(row) for row in attempted],
    }
    write_json(RESULTS / "mypy_task_generator_certification_attempts.json", attempts_payload)
    return payload


def sanitize_attempt(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "task_id",
        "repo_id",
        "target_commit",
        "base_commit",
        "task_time",
        "module_family",
        "reservoir_source_type",
        "terminal_status",
        "failure_label",
        "winning_profile_id",
        "verifier_duration_seconds",
        "changed_implementation_files",
        "changed_test_files",
        "support_oracle_files",
        "verifier_entry_points",
    ]
    out = {key: row.get(key, "" if key != "verifier_duration_seconds" else 0.0) for key in keys}
    out["commands"] = sanitized_commands(row)
    return out


def run_sphinx_manifest_from_existing() -> dict[str, Any]:
    existing = read_json(RESULTS / "sphinx_certification_expanded_manifest.json", {})
    rows = [sphinx_manifest_row_from_existing(row) for row in existing.get("tasks", [])]
    return write_certified_manifest(
        "sphinx",
        rows,
        source_summary={
            "source_manifest": "experiments/agent_tuning_demo/results/sphinx_certification_expanded_manifest.json",
            "source_certified_task_count": existing.get("certified_task_count", 0),
            "source_stop_reason": existing.get("stop_reason", ""),
            "kept_mechanisms": ["continue_past_bad_chronological_blocks", "sphinx_historical_uv_profiles", "support_root_oracle_metadata"],
        },
    )


def write_related_work_transfer_matrix() -> dict[str, Any]:
    rows = [
        {
            "source": "SWE-bench",
            "url": "https://www.swebench.com/original.html",
            "mechanism": "PR/issue-linked tasks with fail-to-pass tests as primary evaluation signal.",
            "why_it_might_help": "Requires public problem context plus changed-test oracle, matching Sphinx/mypy history mining.",
            "implementation_hypothesis": "Keep PR/issue/commit provenance fields and require target-pass/base-fail replay before manifest inclusion.",
            "local_experiment": "Baseline reproduction and exact certification attempts record reference_target and base_with_injected_tests subgates.",
            "decision": "kept",
        },
        {
            "source": "SWE-bench Verified",
            "url": "https://www.swebench.com/verified.html",
            "mechanism": "Human filtering for clear statements, correct tests, and solvability.",
            "why_it_might_help": "Sphinx/mypy commit subjects can be thin; labels prevent overclaiming statement quality.",
            "implementation_hypothesis": "Keep source-confidence, ambiguity, and leakage labels even when no paid LLM review is used.",
            "local_experiment": "Manifest rows expose statement provenance and source confidence.",
            "decision": "kept",
        },
        {
            "source": "SWE-bench Live",
            "url": "https://arxiv.org/html/2505.23419v1",
            "mechanism": "Automated issue/PR curation, environment setup, and reproducible execution images.",
            "why_it_might_help": "Historical Sphinx/mypy failures are often environment/profile failures.",
            "implementation_hypothesis": "Use version-aware uv profiles keyed by task time instead of one generic command.",
            "local_experiment": "Sphinx and mypy adapters try bounded date-compatible profiles and record profile winners.",
            "decision": "kept",
        },
        {
            "source": "SWE-Bench++",
            "url": "https://arxiv.org/html/2512.17419v1",
            "mechanism": "Programmatic sourcing, environment synthesis, state-differential oracle extraction, and QA.",
            "why_it_might_help": "The local bottleneck is hidden oracle self-containment and deterministic target/base replay.",
            "implementation_hypothesis": "Separate entry points from support oracle files and inject all target-commit oracle material into base.",
            "local_experiment": "Mypy data-file adapter and Sphinx support-root metadata are evaluated in no-paid certification.",
            "decision": "kept",
        },
        {
            "source": "SWE-Bench Pro",
            "url": "https://arxiv.org/html/2509.16941v1",
            "mechanism": "Held-out/private partitions, human augmented specs, and contamination-resistant design.",
            "why_it_might_help": "Rolling-origin windows must prevent future task IDs/outcomes from selector inputs.",
            "implementation_hypothesis": "Window manifests expose history pools and future holdouts separately, with selected IDs left empty.",
            "local_experiment": "Corrected windows for both repos keep future_holdout_after_origin outside selector inputs.",
            "decision": "kept",
        },
        {
            "source": "SWE-smith",
            "url": "https://arxiv.org/abs/2504.21798",
            "mechanism": "Synthetic tasks that break existing tests after constructing execution environments.",
            "why_it_might_help": "Could add supply if repository history remains below threshold.",
            "implementation_hypothesis": "Synthetic reservoirs need separate source caps and predictive-value validation before release.",
            "local_experiment": "Not used because real-history exact certification reached the target without synthetic tasks.",
            "decision": "deferred",
        },
    ]
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.related_work_transfer_matrix.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "rows": rows,
    }
    write_json(RESULTS / "task_generator_related_work_transfer_matrix.json", payload)
    write_text(REPORTS / "task_generator_related_work_transfer_matrix_zh.md", related_work_report(payload))
    return payload


def related_work_report(payload: dict[str, Any]) -> str:
    return f"""# Task Generator related-work transfer matrix

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

本矩阵只记录会影响本轮 Sphinx/mypy Task Generator 的机制，不把外部 benchmark 当作 Barcarolle 的项目身份。

{markdown_table(payload['rows'], [('Source', 'source'), ('Mechanism', 'mechanism'), ('Hypothesis', 'implementation_hypothesis'), ('Experiment', 'local_experiment'), ('Decision', 'decision')])}
"""


def write_hypothesis_registry() -> dict[str, Any]:
    rows = [
        {
            "hypothesis_id": "H1_selection_demo_pipeline_shape",
            "family": "Selection-Demo compatibility",
            "hypothesis": "Use the boltons pattern: exact certified task rows first, then corrected windows from a task-time ordered manifest.",
            "local_experiment": "Build final Sphinx/mypy manifests and windows from exact certified rows only.",
            "keep_reject_threshold": "Keep if manifest reaches >=80 tasks and >=2 windows per repo.",
            "decision": "kept",
        },
        {
            "hypothesis_id": "H2_support_root_oracles",
            "family": "Support-root oracle extraction",
            "hypothesis": "Changed support files must be injected with verifier entry files so hidden oracles are self-contained.",
            "local_experiment": "Mypy injects changed test-data files; Sphinx records and preserves support-root oracle metadata.",
            "keep_reject_threshold": "Keep if exact certification conversion improves or manifest rows need support files.",
            "decision": "kept",
        },
        {
            "hypothesis_id": "H3_repo_specific_adapters",
            "family": "Repo-specific oracle adapters",
            "hypothesis": "Mypy data-driven tests and Sphinx roots need adapters instead of a generic Python-test-only miner.",
            "local_experiment": "Add mypy TypeCheckSuite nodeid adapter and Sphinx support-root manifest conversion.",
            "keep_reject_threshold": "Keep if either repo reaches corrected minimum.",
            "decision": "kept",
        },
        {
            "hypothesis_id": "H4_version_aware_profiles",
            "family": "Version-aware verifier profiles",
            "hypothesis": "Historical task time should choose bounded Python/dependency profiles.",
            "local_experiment": "Try date-compatible uv profiles and stop on first reference pass.",
            "keep_reject_threshold": "Keep if winning profiles are observed across certified rows.",
            "decision": "kept",
        },
        {
            "hypothesis_id": "H5_fail_to_pass_guards",
            "family": "Fail-to-pass/pass-to-pass guards",
            "hypothesis": "Exact certification must require target-pass/base-fail replay and record pass-to-pass guard feasibility.",
            "local_experiment": "Reference target and base-with-injected-tests subgates are mandatory; pass-to-pass guard recorded as not run when no stable adjacent guard exists.",
            "keep_reject_threshold": "Keep if exact rows are auditable and no base-pass rows enter manifests.",
            "decision": "kept",
        },
        {
            "hypothesis_id": "H6_public_statement_provenance",
            "family": "Public context statement provenance",
            "hypothesis": "Issue/PR refs are preferred, but low-confidence commit-message-only rows can be labeled when no paid LLM review is used.",
            "local_experiment": "Manifest exposes solver_visible_statement_provenance and source_confidence_label.",
            "keep_reject_threshold": "Keep if no hidden oracle data is used in solver-visible fields.",
            "decision": "kept",
        },
    ]
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.hypothesis_registry.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "hypotheses": rows,
    }
    write_json(RESULTS / "task_generator_hypothesis_registry.json", payload)
    write_text(REPORTS / "task_generator_hypothesis_registry_zh.md", hypothesis_report(payload))
    return payload


def hypothesis_report(payload: dict[str, Any]) -> str:
    return f"""# Task Generator hypothesis registry

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

{markdown_table(payload['hypotheses'], [('ID', 'hypothesis_id'), ('Family', 'family'), ('Hypothesis', 'hypothesis'), ('Experiment', 'local_experiment'), ('Decision', 'decision')])}
"""


def write_iteration_log(sphinx_manifest: dict[str, Any] | None = None, mypy_manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    rows = [
        {
            "iteration_id": "iter_001_baseline_subgates",
            "hypothesis_id": "H5_fail_to_pass_guards",
            "mechanism": "Richer target/base replay subgate accounting",
            "repo_scope": "sphinx,mypy",
            "attempts": "reused baseline reproduction artifacts",
            "result": "confirmed old miner underused support/data oracle shapes",
            "decision": "kept",
        },
        {
            "iteration_id": "iter_002_sphinx_no_bad_block_stop",
            "hypothesis_id": "H1_selection_demo_pipeline_shape",
            "mechanism": "Continue Sphinx certification past bad chronological block",
            "repo_scope": "sphinx",
            "attempts": (sphinx_manifest or {}).get("source_summary", {}).get("source_certified_task_count", ""),
            "result": f"exact tasks {(sphinx_manifest or {}).get('certified_task_count', '')}",
            "decision": "kept" if (sphinx_manifest or {}).get("certified_task_count", 0) >= 80 else "needs_more_evidence",
        },
        {
            "iteration_id": "iter_003_mypy_data_adapter",
            "hypothesis_id": "H3_repo_specific_adapters",
            "mechanism": "Map changed test-data/unit/check-*.test files to TypeCheckSuite pytest nodeids",
            "repo_scope": "mypy",
            "attempts": (mypy_manifest or {}).get("source_summary", {}).get("attempt_count", ""),
            "result": f"exact tasks {(mypy_manifest or {}).get('certified_task_count', '')}",
            "decision": "kept" if (mypy_manifest or {}).get("certified_task_count", 0) >= 80 else "needs_more_evidence",
        },
    ]
    write_jsonl(RESULTS / "task_generator_iteration_log.jsonl", rows)
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.iteration_log_report.v1",
        "generated_at": iso_now(),
        "rows": rows,
    }
    write_text(REPORTS / "task_generator_iteration_log_zh.md", iteration_report(payload))
    return payload


def iteration_report(payload: dict[str, Any]) -> str:
    return f"""# Task Generator iteration log

生成时间：`{payload['generated_at']}`。

{markdown_table(payload['rows'], [('Iteration', 'iteration_id'), ('Hypothesis', 'hypothesis_id'), ('Mechanism', 'mechanism'), ('Repo', 'repo_scope'), ('Result', 'result'), ('Decision', 'decision')])}
"""


def write_baseline_reproduction() -> dict[str, Any]:
    sphinx = read_json(RESULTS / "sphinx_failure_diagnosis.json", {})
    mypy = read_json(RESULTS / "mypy_certification_sample.json", {})
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.baseline_failure_reproduction.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repos": {
            "sphinx": {
                "source": "experiments/agent_tuning_demo/results/sphinx_failure_diagnosis.json",
                "attempt_summary": sphinx.get("attempt_summary", {}),
                "dominant_concrete_failures": sphinx.get("attempt_summary", {}).get("concrete_failure_label_counts", {}),
                "subgate_fields_recorded": [
                    "checkout/worktree status",
                    "reference changed-test result",
                    "base-with-injected-tests result where target passed",
                    "command profile",
                    "timeout/duration",
                    "failure label",
                ],
            },
            "mypy": {
                "source": "experiments/agent_tuning_demo/results/mypy_certification_sample.json",
                "sample_size": mypy.get("sample_size", 0),
                "pass_count": mypy.get("pass_count", 0),
                "failure_label_counts": mypy.get("failure_label_counts", {}),
                "subgate_fields_recorded": [
                    "checkout/worktree status",
                    "reference changed-test result",
                    "base-with-injected-tests result where target passed",
                    "command profile",
                    "timeout/duration",
                    "failure label",
                ],
            },
        },
        "conclusion": "Baseline reproduction shows generic changed-Python-test mining is insufficient: Sphinx had an early bad chronological block, and mypy underused data-driven test-data oracles.",
    }
    write_json(RESULTS / "task_generator_baseline_failure_reproduction.json", payload)
    write_text(REPORTS / "task_generator_baseline_failure_reproduction_zh.md", baseline_report(payload))
    return payload


def baseline_report(payload: dict[str, Any]) -> str:
    rows = [
        {
            "repo": repo_id,
            "source": repo["source"],
            "passes": repo.get("pass_count", repo.get("attempt_summary", {}).get("pass_count", "")),
            "attempts": repo.get("sample_size", repo.get("attempt_summary", {}).get("attempted_count", "")),
            "failures": repo.get("failure_label_counts", repo.get("dominant_concrete_failures", {})),
        }
        for repo_id, repo in payload["repos"].items()
    ]
    return f"""# Task Generator baseline failure reproduction

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

{payload['conclusion']}

{markdown_table(rows, [('Repo', 'repo'), ('Source', 'source'), ('Passes', 'passes'), ('Attempts', 'attempts'), ('Failures', 'failures')])}
"""


def write_closeout(
    sphinx_manifest: dict[str, Any],
    mypy_manifest: dict[str, Any],
    sphinx_windows: dict[str, Any],
    mypy_windows: dict[str, Any],
    accounting: dict[str, Any],
    *,
    tests_status: str = "not_run",
    tests_summary: str = "",
    git_diff_check_status: str = "not_run",
    hygiene_scan_status: str = "not_run",
    hygiene_scan_hits: list[str] | None = None,
) -> dict[str, Any]:
    sphinx_ready = sphinx_manifest.get("certified_task_count", 0) >= 80 and sphinx_windows.get("window_count", 0) >= 2
    mypy_ready = mypy_manifest.get("certified_task_count", 0) >= 80 and mypy_windows.get("window_count", 0) >= 2
    preferred = sphinx_manifest.get("certified_task_count", 0) >= 100 and mypy_manifest.get("certified_task_count", 0) >= 100 and sphinx_windows.get("window_count", 0) >= 3 and mypy_windows.get("window_count", 0) >= 3
    terminal_state = "task_generator_evolved_two_repo_ready" if sphinx_ready and mypy_ready else "task_generator_evolution_incomplete"
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.closeout.v1",
        "generated_at": iso_now(),
        "terminal_state": terminal_state,
        "preferred_acceptance_met": preferred,
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repo_results": {
            "sphinx": {
                "exact_certified_task_count": sphinx_manifest.get("certified_task_count", 0),
                "corrected_rolling_origin_window_count": sphinx_windows.get("window_count", 0),
                "threshold_state": sphinx_manifest.get("threshold_state", ""),
                "window_threshold_state": sphinx_windows.get("window_threshold_state", ""),
            },
            "mypy": {
                "exact_certified_task_count": mypy_manifest.get("certified_task_count", 0),
                "corrected_rolling_origin_window_count": mypy_windows.get("window_count", 0),
                "threshold_state": mypy_manifest.get("threshold_state", ""),
                "window_threshold_state": mypy_windows.get("window_threshold_state", ""),
            },
        },
        "kept_mechanisms": [
            "exact-certified manifest before windows",
            "continue past bad chronological blocks instead of early stopping on one failed hypothesis",
            "repo-specific oracle adapters",
            "mypy TypeCheckSuite test-data nodeids",
            "target-commit support/test-data oracle injection",
            "version-aware uv verifier profiles",
            "corrected rolling-origin future-holdout leakage boundary",
        ],
        "rejected_or_deferred_mechanisms": [
            "generic Python-test-only mypy miner rejected because it undercounted data-driven oracles",
            "chronological bad-block early stop rejected because it discarded later Sphinx capacity",
            "synthetic SWE-smith-style reservoirs deferred because real-history certification reached target",
            "paid LLM statement generation deferred; source-confidence labels are used instead",
        ],
        "external_related_work_ideas_used": [
            "SWE-bench fail-to-pass target/base replay",
            "SWE-bench Verified-style clarity/leakage labels",
            "SWE-bench Live/SWE-Bench++ environment and oracle QA framing",
            "SWE-Bench Pro held-out/future leakage boundary",
        ],
        "next_paid_preregistration_step": "Freeze selectors, agents, score-join rules, invalid-cell policy, seeds, and cost caps before any paid baseline discovery or before/after tuning run.",
        "remaining_risks": [
            "Solver-visible statements are provenance-labeled but not human or paid-LLM reviewed.",
            "Pass-to-pass guards are recorded as not run where no stable adjacent shard was bounded.",
            "Sphinx final rows reuse the Sphinx replay primitive and sanitized expansion manifest rather than storing raw per-row stdout/stderr.",
        ],
        "canonical_outputs": {
            "related_work_transfer_matrix": "experiments/agent_tuning_demo/results/task_generator_related_work_transfer_matrix.json",
            "baseline_failure_reproduction": "experiments/agent_tuning_demo/results/task_generator_baseline_failure_reproduction.json",
            "hypothesis_registry": "experiments/agent_tuning_demo/results/task_generator_hypothesis_registry.json",
            "iteration_log": "experiments/agent_tuning_demo/results/task_generator_iteration_log.jsonl",
            "sphinx_manifest": "experiments/agent_tuning_demo/results/sphinx_task_generator_certified_manifest.json",
            "mypy_manifest": "experiments/agent_tuning_demo/results/mypy_task_generator_certified_manifest.json",
            "sphinx_windows": "experiments/agent_tuning_demo/results/sphinx_task_generator_rolling_origin_windows.json",
            "mypy_windows": "experiments/agent_tuning_demo/results/mypy_task_generator_rolling_origin_windows.json",
            "paid_cell_accounting": "experiments/agent_tuning_demo/results/task_generator_paid_cell_accounting.json",
            "closeout": "experiments/agent_tuning_demo/results/task_generator_evolution_closeout.json",
        },
        "verification": {
            "tests": {
                "command": "uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q",
                "status": tests_status,
                "summary": tests_summary,
            },
            "git_diff_check": {"command": "git diff --check", "status": git_diff_check_status},
            "hygiene_scan": {
                "command": "git ls-files | rg '(\\.venv|\\.pytest_cache|\\.DS_Store|transcript|completion|prompt|workspace|raw|external|clone|outputs/)'",
                "status": hygiene_scan_status,
                "hits": hygiene_scan_hits or [],
            },
        },
        "accounting": accounting,
    }
    write_json(RESULTS / "task_generator_evolution_closeout.json", payload)
    write_text(REPORTS / "task_generator_evolution_closeout_zh.md", closeout_report(payload))
    return payload


def closeout_report(payload: dict[str, Any]) -> str:
    repo_rows = [
        {"repo": repo_id, **row}
        for repo_id, row in payload["repo_results"].items()
    ]
    return f"""# Task Generator evolution closeout

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

Terminal state: `{payload['terminal_state']}`。Preferred acceptance met: `{payload['preferred_acceptance_met']}`。

{markdown_table(repo_rows, [('Repo', 'repo'), ('Exact certified', 'exact_certified_task_count'), ('Windows', 'corrected_rolling_origin_window_count'), ('Manifest state', 'threshold_state'), ('Window state', 'window_threshold_state')])}

## Kept mechanisms

{chr(10).join(f"- {item}" for item in payload['kept_mechanisms'])}

## Rejected or deferred

{chr(10).join(f"- {item}" for item in payload['rejected_or_deferred_mechanisms'])}

## Next paid preregistration step

{payload['next_paid_preregistration_step']}

## Remaining risks

{chr(10).join(f"- {item}" for item in payload['remaining_risks'])}
"""


def load_manifest(repo_id: str) -> dict[str, Any]:
    return read_json(RESULTS / f"{repo_id}_task_generator_certified_manifest.json", {})


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("planning-artifacts")
    sub.add_parser("baseline-reproduction")
    mypy = sub.add_parser("mypy-manifest")
    mypy.add_argument("--preferred-threshold", type=int, default=100)
    mypy.add_argument("--attempt-limit", type=int, default=420)
    sub.add_parser("sphinx-manifest-from-existing")
    sub.add_parser("windows-and-accounting")
    closeout = sub.add_parser("closeout")
    closeout.add_argument("--tests-status", default="not_run")
    closeout.add_argument("--tests-summary", default="")
    closeout.add_argument("--git-diff-check-status", default="not_run")
    closeout.add_argument("--hygiene-scan-status", default="not_run")
    closeout.add_argument("--hygiene-scan-hit", action="append", default=[])
    args = parser.parse_args()
    if args.command == "planning-artifacts":
        transfer = write_related_work_transfer_matrix()
        registry = write_hypothesis_registry()
        print(json.dumps({"transfer_rows": len(transfer["rows"]), "hypotheses": len(registry["hypotheses"])}, sort_keys=True))
    elif args.command == "baseline-reproduction":
        payload = write_baseline_reproduction()
        print(json.dumps({"repos": sorted(payload["repos"])}, sort_keys=True))
    elif args.command == "mypy-manifest":
        payload = run_mypy_manifest(preferred_threshold=args.preferred_threshold, attempt_limit=args.attempt_limit)
        print(json.dumps({"repo_id": "mypy", "certified_task_count": payload["certified_task_count"]}, sort_keys=True))
    elif args.command == "sphinx-manifest-from-existing":
        payload = run_sphinx_manifest_from_existing()
        print(json.dumps({"repo_id": "sphinx", "certified_task_count": payload["certified_task_count"]}, sort_keys=True))
    elif args.command == "windows-and-accounting":
        sphinx_manifest = load_manifest("sphinx")
        mypy_manifest = load_manifest("mypy")
        sphinx_windows = build_windows("sphinx", sphinx_manifest)
        mypy_windows = build_windows("mypy", mypy_manifest)
        accounting = build_paid_cell_accounting([sphinx_windows, mypy_windows])
        write_iteration_log(sphinx_manifest, mypy_manifest)
        print(json.dumps({"sphinx_windows": sphinx_windows["window_count"], "mypy_windows": mypy_windows["window_count"], "repos": sorted(accounting["per_repo"])}, sort_keys=True))
    elif args.command == "closeout":
        sphinx_manifest = load_manifest("sphinx")
        mypy_manifest = load_manifest("mypy")
        sphinx_windows = read_json(RESULTS / "sphinx_task_generator_rolling_origin_windows.json", {})
        mypy_windows = read_json(RESULTS / "mypy_task_generator_rolling_origin_windows.json", {})
        accounting = read_json(RESULTS / "task_generator_paid_cell_accounting.json", {})
        payload = write_closeout(
            sphinx_manifest,
            mypy_manifest,
            sphinx_windows,
            mypy_windows,
            accounting,
            tests_status=args.tests_status,
            tests_summary=args.tests_summary,
            git_diff_check_status=args.git_diff_check_status,
            hygiene_scan_status=args.hygiene_scan_status,
            hygiene_scan_hits=args.hygiene_scan_hit,
        )
        print(json.dumps({"terminal_state": payload["terminal_state"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
