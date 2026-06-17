from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXTERNAL_REPOS = ROOT / "experiments" / "phase0_headroom" / "external_repos"
SCRATCH = ROOT / "experiments" / "phase0_headroom" / "tmp" / "target_repair_selection_loop"
RESULTS = ROOT / "experiments" / "agent_tuning_demo" / "results"
REPORTS = ROOT / "experiments" / "agent_tuning_demo" / "reports"

SCHEMA_VERSION = "barcarolle.agent_tuning_demo.target_repair_selection_loop.v1"
CURRENT_DATE = datetime(2026, 6, 17, tzinfo=timezone.utc)
MINIMUM_CERTIFIED_TASKS = 80
PREFERRED_CERTIFIED_TASKS = 100
SELECTED_BENCHMARK_SIZE = 20
FUTURE_HOLDOUT_SIZE = 20
AGENT_COUNT = 4


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


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def digest_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


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


def git_stdout(repo: Path, args: list[str], timeout: int = 240) -> str:
    result = run_command(["git", *args], repo, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def is_mypy_test_path(path: str) -> bool:
    lower = path.lower()
    if not lower.endswith(".py"):
        return False
    return lower.startswith(("mypy/test/", "mypyc/test/")) and Path(lower).name.startswith("test")


def is_mypy_impl_path(path: str) -> bool:
    lower = path.lower()
    if not lower.endswith(".py") or is_mypy_test_path(path):
        return False
    return lower.startswith(("mypy/", "mypyc/"))


def public_refs_from_subject(subject: str) -> list[str]:
    return list(dict.fromkeys(f"pr_or_issue:{match.group(1)}" for match in re.finditer(r"#(\d+)", subject or "")))


def risk_label(implementation_files: list[str], test_files: list[str]) -> str:
    if len(test_files) > 4:
        return "wide_changed_test_oracle"
    if len(implementation_files) > 8:
        return "large_implementation_surface"
    return "normal"


def mypy_module_family(paths: list[str]) -> str:
    for path in paths:
        if path.startswith("mypy/check"):
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


def parse_mypy_history(repo: Path, *, max_count: int = 5000) -> list[dict[str, Any]]:
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
        timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    rows: list[dict[str, Any]] = []
    for chunk in result.stdout.split("\x1e"):
        lines = [line for line in chunk.splitlines() if line.strip()]
        if not lines:
            continue
        meta = lines[0].split("\t", 3)
        if len(meta) != 4:
            continue
        commit, parents, task_time, subject = meta
        changed = lines[1:]
        implementation_files = [path for path in changed if is_mypy_impl_path(path)]
        pytest_files = [path for path in changed if is_mypy_test_path(path)]
        refs = public_refs_from_subject(subject)
        if not parents.split() or not implementation_files or not pytest_files or not refs:
            continue
        rows.append(
            {
                "repo_id": "mypy",
                "task_id": f"mypy__hist__{len(rows) + 1:04d}",
                "target_commit": commit,
                "base_commit": parents.split()[0],
                "task_time": task_time,
                "time_bucket": time_bucket(task_time),
                "module_family": mypy_module_family([*implementation_files, *pytest_files]),
                "changed_implementation_files": implementation_files,
                "changed_test_files": pytest_files,
                "pytest_entry_files": pytest_files,
                "public_source_context_reference": ", ".join(refs),
                "preliminary_risk_label": risk_label(implementation_files, pytest_files),
            }
        )
    return rows


def spread_sample(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0 or not rows:
        return []
    ordered = sorted(rows, key=lambda row: (row["task_time"], row["task_id"]))
    if len(ordered) <= limit:
        return ordered
    if limit == 1:
        return [ordered[len(ordered) // 2]]
    step = (len(ordered) - 1) / (limit - 1)
    return [ordered[round(index * step)] for index in range(limit)]


def command_shape(command: list[str]) -> list[str]:
    shaped: list[str] = []
    skip_next = False
    for index, item in enumerate(command):
        if skip_next:
            skip_next = False
            continue
        if item in {"--with", "--python", "--exclude-newer"} and index + 1 < len(command):
            shaped.extend([item, command[index + 1] if item != "--with" or command[index + 1] != "." else "."])
            skip_next = True
        elif item.startswith(("mypy/test/", "mypyc/test/")):
            if not shaped or shaped[-1] != "<targeted_test_paths>":
                shaped.append("<targeted_test_paths>")
        else:
            shaped.append(item)
    return shaped


def mypy_pytest_command(row: dict[str, Any], python_version: str, pytest_spec: str) -> list[str]:
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
        *row["pytest_entry_files"],
        "-q",
    ]


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


def replay_failure(row: dict[str, Any], label: str, result: CommandResult, commands: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        **{key: row[key] for key in ["repo_id", "task_id", "target_commit", "base_commit", "task_time", "time_bucket", "module_family"]},
        "terminal_status": "failed",
        "failure_label": label,
        "preliminary_risk_label": row["preliminary_risk_label"],
        "changed_implementation_files": row["changed_implementation_files"],
        "changed_test_files": row["changed_test_files"],
        "pytest_entry_files": row["pytest_entry_files"],
        "duration_seconds": result.duration_seconds,
        "stdout_tail_hash": digest_text(result.stdout[-1000:]),
        "stderr_tail_hash": digest_text(result.stderr[-1000:]),
        "commands": commands,
    }


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
        missing = [path for path in row["pytest_entry_files"] if not (target_worktree / path).exists()]
        if missing:
            return {
                **replay_failure(row, "changed_test_oracle_missing", CommandResult(1, "", "", 0.0), commands),
                "missing_test_paths": missing,
            }
        inject = run_command(["git", "checkout", row["target_commit"], "--", *row["changed_test_files"]], base_worktree, timeout=120)
        if inject.returncode != 0:
            return replay_failure(row, "hidden_verifier_injection_failed", inject, commands)
        for profile_id, python_version, pytest_spec in (
            ("py312_editable", "3.12", "pytest>=8,<10"),
            ("py310_legacy_editable", "3.10", "pytest>=7,<9"),
        ):
            command = mypy_pytest_command(row, python_version, pytest_spec)
            target_result = run_command(command, target_worktree, timeout=180)
            commands.append(command_record("reference_target", profile_id, command, target_result))
            if target_result.returncode != 0:
                continue
            base_result = run_command(command, base_worktree, timeout=180)
            commands.append(command_record("base_with_injected_tests", profile_id, command, base_result))
            if base_result.returncode == 0:
                return {
                    **replay_failure(row, "base_passed_changed_tests_not_meaningful", base_result, commands),
                    "winning_profile_id": profile_id,
                    "verifier_duration_seconds": target_result.duration_seconds + base_result.duration_seconds,
                }
            return {
                **{key: row[key] for key in ["repo_id", "task_id", "target_commit", "base_commit", "task_time", "time_bucket", "module_family"]},
                "terminal_status": "passed",
                "failure_label": "",
                "winning_profile_id": profile_id,
                "preliminary_risk_label": row["preliminary_risk_label"],
                "changed_implementation_files": row["changed_implementation_files"],
                "changed_test_files": row["changed_test_files"],
                "pytest_entry_files": row["pytest_entry_files"],
                "verifier_duration_seconds": target_result.duration_seconds + base_result.duration_seconds,
                "commands": commands,
            }
        terminal = commands[-1]["subgate_label"] if commands else "reference_replay_not_attempted"
        return {
            **replay_failure(row, f"reference_{terminal}", CommandResult(1, "", "", 0.0), commands),
            "verifier_duration_seconds": sum(float(command.get("duration_seconds") or 0.0) for command in commands),
        }
    finally:
        cleanup_worktree(repo, base_worktree)
        cleanup_worktree(repo, target_worktree)


def counted(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def duration_summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "median_seconds": None, "p95_seconds": None, "max_seconds": None}
    ordered = sorted(values)
    p95_index = min(len(ordered) - 1, round((len(ordered) - 1) * 0.95))
    return {
        "count": len(ordered),
        "median_seconds": round(median(ordered), 3),
        "p95_seconds": round(ordered[p95_index], 3),
        "max_seconds": round(max(ordered), 3),
    }


def run_mypy_current_smoke() -> dict[str, Any]:
    repo = EXTERNAL_REPOS / "mypy"
    command = [
        "uv",
        "run",
        "--no-project",
        "--with",
        "pytest>=8,<10",
        "--with",
        "pytest-xdist",
        "--with",
        ".",
        "--",
        "python",
        "-m",
        "pytest",
        "mypy/test/testapi.py",
        "-q",
    ]
    result = run_command(command, repo, timeout=240)
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.mypy_current_smoke.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repo_id": "mypy",
        "status": "passed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "duration_seconds": result.duration_seconds,
        "timed_out": result.timed_out,
        "command_shape": command_shape(command),
        "stdout_line_count": len(result.stdout.splitlines()),
        "stderr_line_count": len(result.stderr.splitlines()),
        "stdout_tail_hash": digest_text(result.stdout[-1000:]),
        "stderr_tail_hash": digest_text(result.stderr[-1000:]),
    }
    write_json(RESULTS / "mypy_current_smoke.json", payload)
    return payload


def run_mypy_certification_sample(limit: int) -> dict[str, Any]:
    repo = EXTERNAL_REPOS / "mypy"
    inventory = parse_mypy_history(repo)
    eligible = [row for row in inventory if row["preliminary_risk_label"] == "normal"]
    sampled = spread_sample(eligible, limit)
    results = [replay_mypy_candidate(repo, row, scratch_root=SCRATCH / "mypy_certification_sample") for row in sampled]
    durations = [float(row.get("verifier_duration_seconds") or 0.0) for row in results if row.get("terminal_status") == "passed"]
    pass_count = sum(1 for row in results if row.get("terminal_status") == "passed")
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.mypy_certification_sample.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repo_id": "mypy",
        "candidate_inventory_count": len(inventory),
        "eligible_normal_risk_count": len(eligible),
        "sample_size": len(results),
        "pass_count": pass_count,
        "conversion_rate": round(pass_count / len(results), 4) if results else 0.0,
        "failure_label_counts": counted(row.get("failure_label") for row in results if row.get("failure_label")),
        "time_bucket_distribution": counted(row["time_bucket"] for row in results),
        "module_family_distribution": counted(row["module_family"] for row in results),
        "verifier_duration_summary": duration_summary(durations),
        "stop_decision": (
            "reject_mypy_conversion_below_0_30"
            if len(results) >= 24 and (pass_count / len(results) if results else 0.0) < 0.30
            else "continue_if_needed"
        ),
        "raw_output_committed": False,
        "rows": [sanitize_certification_row(row) for row in results],
    }
    write_json(RESULTS / "mypy_certification_sample.json", payload)
    write_text(REPORTS / "mypy_certification_sample_zh.md", mypy_certification_sample_report(payload))
    return payload


def sanitize_certification_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": row.get("task_id", ""),
        "target_commit": row.get("target_commit", ""),
        "base_commit": row.get("base_commit", ""),
        "task_time": row.get("task_time", ""),
        "time_bucket": row.get("time_bucket", ""),
        "module_family": row.get("module_family", ""),
        "preliminary_risk_label": row.get("preliminary_risk_label", ""),
        "terminal_status": row.get("terminal_status", ""),
        "failure_label": row.get("failure_label", ""),
        "winning_profile_id": row.get("winning_profile_id", ""),
        "verifier_duration_seconds": round(float(row.get("verifier_duration_seconds") or row.get("duration_seconds") or 0.0), 3),
        "changed_implementation_files": row.get("changed_implementation_files") or [],
        "changed_test_files": row.get("changed_test_files") or [],
        "pytest_entry_files": row.get("pytest_entry_files") or [],
        "commands": [
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
        ],
    }


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    lines = ["| " + " | ".join(label for label, _key in columns) + " |", "| " + " | ".join("---" for _label, _key in columns) + " |"]
    for row in rows:
        values = [str(row.get(key, "")).replace("|", "\\|").replace("\n", " ") for _label, key in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def mypy_certification_sample_report(payload: dict[str, Any]) -> str:
    rows = [
        {
            "task": row["task_id"],
            "time": str(row["task_time"])[:10],
            "family": row["module_family"],
            "status": row["terminal_status"],
            "failure": row["failure_label"],
            "profile": row["winning_profile_id"],
            "seconds": row["verifier_duration_seconds"],
        }
        for row in payload["rows"]
    ]
    return f"""# Mypy certification sample

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

exact certification sample: `{payload['pass_count']}/{payload['sample_size']}`；conversion `{payload['conversion_rate']}`；decision `{payload['stop_decision']}`。

- candidate inventory count: `{payload['candidate_inventory_count']}`
- normal-risk eligible count: `{payload['eligible_normal_risk_count']}`
- failure labels: `{payload['failure_label_counts']}`
- verifier duration: `{payload['verifier_duration_summary']}`

## Rows

{markdown_table(rows, [('Task', 'task'), ('Time', 'time'), ('Family', 'family'), ('Status', 'status'), ('Failure', 'failure'), ('Profile', 'profile'), ('Seconds', 'seconds')])}

## Artifact hygiene

本 artifact 只保存 sanitized command metadata 和 tail hashes；未提交 raw stdout/stderr、workspaces、prompts、completions、transcripts 或 secrets。
"""


def run_candidate_decisions() -> dict[str, Any]:
    large_gate = read_json(RESULTS / "large_repo_target_selection_gate.json", {})
    target_gate = read_json(RESULTS / "target_repo_selection_gate.json", {})
    sphinx = read_json(RESULTS / "sphinx_failure_diagnosis.json", {})
    mypy_sample = read_json(RESULTS / "mypy_certification_sample.json", {})
    mypy_smoke = read_json(RESULTS / "mypy_current_smoke.json", {})
    large_by_id = {row.get("repo_id"): row for row in large_gate.get("candidate_metrics", [])}
    target_by_id = {row.get("repo_id"): row for row in target_gate.get("candidates", [])}
    decisions = []
    for repo_id in ["sphinx", "mypy", "black", "starlette", "attrs", "click", "django", "pandas", "scikit-learn", "packaging", "marshmallow", "urllib3", "pytest"]:
        row = build_candidate_decision(repo_id, large_by_id.get(repo_id, {}), target_by_id.get(repo_id, {}), sphinx, mypy_sample, mypy_smoke)
        decisions.append(row)
    ready = [row for row in decisions if row["decision_label"] == "ready_for_paid_baseline_preregistration"]
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.candidate_decisions.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "terminal_state": "target_ready_for_paid_baseline_preregistration" if ready else "candidate_loop_no_ready_target",
        "selected_target_repository": ready[0]["repo_id"] if ready else None,
        "decisions": decisions,
    }
    write_json(RESULTS / "target_repair_selection_candidate_decisions.json", payload)
    write_csv(RESULTS / "target_repair_selection_candidate_decisions.csv", decisions, list(decisions[0].keys()))
    write_text(REPORTS / "target_repair_selection_candidate_decisions_zh.md", candidate_decisions_report(payload))
    return payload


def build_candidate_decision(
    repo_id: str,
    large: dict[str, Any],
    target: dict[str, Any],
    sphinx: dict[str, Any],
    mypy_sample: dict[str, Any],
    mypy_smoke: dict[str, Any],
) -> dict[str, Any]:
    if repo_id == "sphinx":
        return {
            "repo_id": repo_id,
            "exact_certified_task_count": 16,
            "corrected_window_count": 0,
            "setup_smoke": "passed_prior",
            "verifier_speed_summary": "median 9.502s, p95 20.469s on certified rows",
            "decision_label": "rejected",
            "primary_reason": sphinx.get("decision", {}).get("sphinx_decision", "sphinx_manifest_needs_bounded_repair"),
            "bounded_repair_attempted": False,
            "paid_cells_used": 0,
        }
    if repo_id == "mypy":
        exact = int(mypy_sample.get("pass_count") or 0)
        conversion = float(mypy_sample.get("conversion_rate") or 0.0)
        return {
            "repo_id": repo_id,
            "exact_certified_task_count": exact,
            "corrected_window_count": 0,
            "setup_smoke": mypy_smoke.get("status", "not_run"),
            "verifier_speed_summary": f"current smoke {mypy_smoke.get('duration_seconds')}s; cert sample {mypy_sample.get('verifier_duration_summary', {})}",
            "decision_label": "rejected" if mypy_sample.get("stop_decision") == "reject_mypy_conversion_below_0_30" else "needs_more_no_paid_certification",
            "primary_reason": f"exact certification sample conversion {conversion}; corrected threshold requires 80 exact tasks",
            "bounded_repair_attempted": False,
            "paid_cells_used": 0,
        }
    baseline_source_ids = {"attrs", "click", "packaging", "marshmallow", "urllib3", "pytest"}
    source = target if repo_id in baseline_source_ids and target else large or target
    projected = int(source.get("projected_certified_task_count_after_bounded_repair") or source.get("current_or_projected_release_eligible_count") or 0)
    speed = source.get("targeted_verifier_timing") or source.get("visible_test_setup_smoke") or {}
    blockers = source.get("main_blockers") or []
    classification = source.get("classification") or source.get("screen_label") or "screened_out"
    if projected < MINIMUM_CERTIFIED_TASKS:
        reason = f"projected/existing supply {projected} below corrected exact minimum {MINIMUM_CERTIFIED_TASKS}"
    elif classification in {"large_but_heavy", "screened_out"}:
        reason = f"classified {classification}; setup/replay blocker not bounded enough for this loop"
    else:
        reason = f"classified {classification}; exact certification not available from current method"
    return {
        "repo_id": repo_id,
        "exact_certified_task_count": 0,
        "corrected_window_count": 0,
        "setup_smoke": speed.get("speed_class") or speed.get("status") or "not_run",
        "verifier_speed_summary": json.dumps(speed, sort_keys=True),
        "decision_label": "rejected",
        "primary_reason": reason if not blockers else f"{reason}; blockers: {'; '.join(str(item) for item in blockers)}",
        "bounded_repair_attempted": False,
        "paid_cells_used": 0,
    }


def candidate_decisions_report(payload: dict[str, Any]) -> str:
    return f"""# Target repair selection candidate decisions

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

Candidate-loop terminal state: `{payload['terminal_state']}`。Selected target: `{payload['selected_target_repository']}`。

## Decisions

{markdown_table(payload['decisions'], [('Repo', 'repo_id'), ('Exact certified', 'exact_certified_task_count'), ('Windows', 'corrected_window_count'), ('Smoke', 'setup_smoke'), ('Decision', 'decision_label'), ('Reason', 'primary_reason')])}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("mypy-current-smoke")
    sample = sub.add_parser("mypy-certification-sample")
    sample.add_argument("--limit", type=int, default=24)
    sub.add_parser("candidate-decisions")
    args = parser.parse_args()
    if args.command == "mypy-current-smoke":
        payload = run_mypy_current_smoke()
        print(json.dumps({"status": payload["status"], "duration_seconds": payload["duration_seconds"]}, sort_keys=True))
    elif args.command == "mypy-certification-sample":
        payload = run_mypy_certification_sample(limit=args.limit)
        print(json.dumps({"pass_count": payload["pass_count"], "sample_size": payload["sample_size"], "decision": payload["stop_decision"]}, sort_keys=True))
    elif args.command == "candidate-decisions":
        payload = run_candidate_decisions()
        print(json.dumps({"terminal_state": payload["terminal_state"], "selected": payload["selected_target_repository"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
