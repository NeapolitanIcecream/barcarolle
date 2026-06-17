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
CONFIG = ROOT / "experiments" / "agent_tuning_demo" / "config" / "sphinx_target_profile.json"
RESULTS = ROOT / "experiments" / "agent_tuning_demo" / "results"
REPORTS = ROOT / "experiments" / "agent_tuning_demo" / "reports"

SCHEMA_VERSION = "barcarolle.agent_tuning_demo.sphinx_target_prep.v1"
HISTORY_SCAN_CAP = 5000
SCRATCH = ROOT / "experiments" / "phase0_headroom" / "tmp" / "sphinx_target_prep"
CURRENT_DATE = datetime(2026, 6, 17, tzinfo=timezone.utc)
DEFAULT_HISTORY_SIZES = [40, 60, 80]
DEFAULT_SELECTED_BENCHMARK_SIZE = 20
DEFAULT_FUTURE_HOLDOUT_SIZE = 20
DEFAULT_ORIGIN_STRIDE = 20
DEFAULT_BASELINE_AGENT_COUNT = 4

CERTIFIED_MANIFEST_FIELDS = [
    "task_id",
    "target_commit",
    "base_commit",
    "task_time",
    "time_bucket",
    "module_family",
    "changed_implementation_files",
    "changed_test_files",
    "pytest_entry_files",
    "winning_verifier_profile",
    "verifier_duration_seconds",
    "source_certification_provenance",
    "evidence_digest",
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


def repo_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def repo_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


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


def git_stdout(repo: Path, args: list[str], timeout: int = 120) -> str:
    result = run_command(["git", *args], repo, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


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


def current_profile(profile: dict[str, Any]) -> dict[str, Any]:
    return dict(profile["dependency_setup_policy"]["current_smoke_profile"])


def historical_profiles(profile: dict[str, Any], task_time: str) -> list[dict[str, Any]]:
    task_date = parse_datetime(task_time).date().isoformat()
    exclude_date = exclude_newer_date(task_time)
    raw_profiles: list[dict[str, Any]] = []
    if exclude_date >= "2025-11-01":
        raw_profiles.append(current_profile(profile))
    raw_profiles.extend(
        dict(raw)
        for raw in profile["dependency_setup_policy"]["historical_verifier_profiles"]
        if str(raw["active_from"]) <= task_date
    )
    raw_profiles.sort(key=lambda raw: str(raw.get("active_from") or "9999-12-31"), reverse=True)
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_profiles:
        profile_id = str(raw["profile_id"])
        if profile_id in seen:
            continue
        seen.add(profile_id)
        out.append({**raw, "exclude_newer_date": exclude_date})
    return out[:3]


def uv_pytest_command(env_profile: dict[str, Any], test_files: list[str]) -> list[str]:
    command = [
        "uv",
        "run",
        "--no-project",
        "--isolated",
        "--managed-python",
        "--python",
        str(env_profile["python_version"]),
        "--exclude-newer",
        str(env_profile["exclude_newer_date"]),
    ]
    for constraint in env_profile["dependency_constraints"]:
        command.extend(["--with", str(constraint)])
    command.extend(["--", "python", "-m", "pytest", *test_files, "-q"])
    return command


def command_shape(command: list[str]) -> list[str]:
    shaped: list[str] = []
    skip_next = False
    for index, item in enumerate(command):
        if skip_next:
            skip_next = False
            continue
        if item == "--with" and index + 1 < len(command):
            shaped.extend(["--with", command[index + 1] if command[index + 1] != "." else "."])
            skip_next = True
        elif item.startswith("tests/"):
            if not shaped or shaped[-1] != "<targeted_test_paths>":
                shaped.append("<targeted_test_paths>")
        else:
            shaped.append(item)
    return shaped


def classify_speed(rows: list[dict[str, Any]]) -> str:
    completed = [float(row["duration_seconds"]) for row in rows if row.get("duration_seconds") is not None]
    passed = [row for row in rows if row.get("status") == "passed"]
    if not completed:
        return "not_measured"
    if len(passed) != len(completed):
        return "risky_or_unusable_partial_failure"
    worst = max(completed)
    if worst < 60:
        return "ideal_under_60s"
    if worst < 180:
        return "acceptable_under_180s"
    if worst < 600:
        return "risky_180s_to_600s"
    return "unusable_over_600s"


def is_test_path(path: str) -> bool:
    lower = path.lower()
    return lower.endswith((".py", ".pyi")) and (
        lower.startswith("tests/")
        or re.search(r"(^|/)test_[^/]*\.pyi?$", lower) is not None
        or re.search(r"(^|/)[^/]*_test\.pyi?$", lower) is not None
    )


def is_pytest_entry_path(path: str) -> bool:
    lower = path.lower()
    if not lower.endswith((".py", ".pyi")) or not lower.startswith("tests/"):
        return False
    if lower.startswith("tests/roots/") or lower.startswith("tests/js/"):
        return False
    name = Path(lower).name
    return name.startswith("test_") or name.endswith("_test.py") or name.endswith("_test.pyi")


def is_impl_path(path: str) -> bool:
    lower = path.lower()
    if not lower.endswith((".py", ".pyi")) or is_test_path(path):
        return False
    return lower.startswith("sphinx/")


def public_refs_from_subject(subject: str) -> list[str]:
    return list(dict.fromkeys(f"pr_or_issue:{match.group(1)}" for match in re.finditer(r"#(\d+)", subject or "")))


def module_family(paths: list[str]) -> str:
    for path in paths:
        if path.startswith("sphinx/util/") or path.startswith("tests/test_util/"):
            return "util"
        if path.startswith("sphinx/ext/") or path.startswith("tests/test_ext_") or path.startswith("tests/test_extensions/"):
            return "extensions"
        if path.startswith("sphinx/domains/") or path.startswith("tests/test_domains/"):
            return "domains"
        if path.startswith("sphinx/builders/") or path.startswith("tests/test_builders/"):
            return "builders"
        if path.startswith("sphinx/directives/") or path.startswith("tests/test_directives/"):
            return "directives"
        if path.startswith("sphinx/environment/") or path.startswith("tests/test_environment/"):
            return "environment"
        if path.startswith("sphinx/config") or path.startswith("tests/test_config/"):
            return "config"
    return "core_or_other"


def time_bucket(year: int) -> str:
    if year < 2022:
        return "pre_2022"
    if year < 2024:
        return "2022_2023"
    return "2024_plus"


def risk_label(row: dict[str, Any]) -> str:
    tests = list(row.get("test_files") or [])
    impl = list(row.get("implementation_files") or [])
    if any("test_js" in path or path.startswith("tests/js/") for path in tests):
        return "skip_javascript_or_browser_test"
    if any("linkcheck" in path or "graphviz" in path for path in tests):
        return "risky_optional_external_tool"
    if len(tests) > 4:
        return "wide_changed_test_oracle"
    if len(impl) > 8:
        return "large_implementation_surface"
    return "normal"


def parse_git_history(repo: Path) -> tuple[list[dict[str, Any]], bool]:
    result = run_command(
        [
            "git",
            "log",
            "--since=2010-01-01",
            f"--max-count={HISTORY_SCAN_CAP}",
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
        implementation_files = [path for path in changed if is_impl_path(path)]
        test_files = [path for path in changed if is_test_path(path)]
        public_refs = public_refs_from_subject(subject)
        row = {
            "commit": commit,
            "parent": parents.split()[0] if parents.split() else "",
            "task_time": task_time,
            "task_year": parse_datetime(task_time).year,
            "subject": subject,
            "public_source_context_reference": ", ".join(public_refs),
            "public_refs": public_refs,
            "changed_files": changed,
            "implementation_files": implementation_files,
            "test_files": test_files,
            "pytest_files": [path for path in test_files if is_pytest_entry_path(path)],
            "module_family": module_family([*implementation_files, *test_files]),
                "expected_targeted_verifier_command": "python -m pytest <changed_tests> -q",
        }
        row["preliminary_risk_label"] = risk_label(row)
        row["time_bucket"] = time_bucket(int(row["task_year"]))
        rows.append(row)
    return rows, len(rows) >= HISTORY_SCAN_CAP


def candidate_rows(repo: Path) -> list[dict[str, Any]]:
    rows, _capped = parse_git_history(repo)
    candidates = [
        row
        for row in rows
        if row["parent"]
        and row["implementation_files"]
        and row["test_files"]
        and row["pytest_files"]
        and row["public_refs"]
        and row["preliminary_risk_label"] in {"normal", "wide_changed_test_oracle", "large_implementation_surface"}
    ]
    out: list[dict[str, Any]] = []
    for index, row in enumerate(sorted(candidates, key=lambda item: item["task_time"])):
        out.append(
            {
                "task_id": f"sphinx__hist__{index + 1:04d}",
                "base_commit": row["parent"],
            "target_commit": row["commit"],
            **row,
        }
        )
    return out


def spread_sample(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0 or not rows:
        return []
    ordered = sorted(rows, key=lambda row: (row.get("task_time") or "", row.get("module_family") or ""))
    if len(ordered) <= limit:
        return ordered
    if limit == 1:
        return [ordered[len(ordered) // 2]]
    step = (len(ordered) - 1) / (limit - 1)
    return [ordered[round(index * step)] for index in range(limit)]


def preflight_sample(rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    eligible = [row for row in rows if row["preliminary_risk_label"] == "normal"]
    by_bucket: dict[str, list[dict[str, Any]]] = {"pre_2022": [], "2022_2023": [], "2024_plus": []}
    for row in eligible:
        year = int(row["task_year"])
        if year < 2022:
            by_bucket["pre_2022"].append(row)
        elif year < 2024:
            by_bucket["2022_2023"].append(row)
        else:
            by_bucket["2024_plus"].append(row)
    selected: list[dict[str, Any]] = []
    families: set[str] = set()
    for bucket in ("pre_2022", "2022_2023", "2024_plus"):
        for row in spread_sample(by_bucket[bucket], min(2, max(1, limit - len(selected)))):
            if row["module_family"] in families and len(families) < 3:
                continue
            selected.append(row)
            families.add(str(row["module_family"]))
            if len(selected) >= limit:
                return selected
    if len(selected) < limit:
        used = {row["task_id"] for row in selected}
        selected.extend(row for row in spread_sample(eligible, limit * 2) if row["task_id"] not in used)
    return selected[:limit]


def inventory_sample(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if len(rows) <= limit:
        return rows
    out: list[dict[str, Any]] = []
    for bucket in ("pre_2022", "2022_2023", "2024_plus"):
        bucket_rows = [row for row in rows if row["time_bucket"] == bucket]
        out.extend(spread_sample(bucket_rows, max(1, limit // 3)))
    if len(out) < limit:
        used = {row["task_id"] for row in out}
        out.extend(row for row in spread_sample(rows, limit * 2) if row["task_id"] not in used)
    return sorted(out[:limit], key=lambda row: row["task_time"])


def certification_sample(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    eligible = [
        row
        for row in rows
        if row["preliminary_risk_label"] in {"normal", "wide_changed_test_oracle", "large_implementation_surface"}
    ]
    selected: list[dict[str, Any]] = []
    per_bucket = max(1, limit // 3)
    for bucket in ("pre_2022", "2022_2023", "2024_plus"):
        bucket_rows = [row for row in eligible if row["time_bucket"] == bucket and row["preliminary_risk_label"] == "normal"]
        selected.extend(spread_sample(bucket_rows, per_bucket))
    if len(selected) < limit:
        used = {row["task_id"] for row in selected}
        fill = [row for row in eligible if row["task_id"] not in used]
        selected.extend(spread_sample(fill, limit - len(selected)))
    return sorted(selected[:limit], key=lambda row: row["task_time"])


def command_record(role: str, profile: dict[str, Any], command: list[str], result: CommandResult) -> dict[str, Any]:
    return {
        "role": role,
        "profile_id": profile["profile_id"],
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
    if "no tests ran" in combined or result.returncode == 5:
        return "no_tests_selected"
    if result.returncode == 1:
        return "target_test_failure"
    return "unknown_failed"


def cleanup_worktree(repo: Path, worktree: Path) -> None:
    result = run_command(["git", "worktree", "remove", "--force", str(worktree)], repo, timeout=120)
    if result.returncode != 0 and worktree.exists():
        shutil.rmtree(worktree)


def add_worktree(repo: Path, worktree: Path, commit: str) -> CommandResult:
    if worktree.exists():
        shutil.rmtree(worktree)
    worktree.parent.mkdir(parents=True, exist_ok=True)
    return run_command(["git", "worktree", "add", "--detach", str(worktree), commit], repo, timeout=180)


def inject_target_tests(source_repo: Path, base_worktree: Path, target_commit: str, test_files: list[str]) -> CommandResult:
    return run_command(["git", "checkout", target_commit, "--", *test_files], base_worktree, timeout=120)


def replay_candidate(profile: dict[str, Any], repo: Path, row: dict[str, Any], *, scratch_root: Path) -> dict[str, Any]:
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
        missing = [path for path in row["test_files"] if not (target_worktree / path).exists()]
        if missing:
            return {
                **replay_base_row(row),
                "terminal_status": "failed",
                "failure_label": "changed_test_oracle_missing",
                "missing_test_paths": missing,
                "commands": commands,
            }
        inject = inject_target_tests(repo, base_worktree, row["target_commit"], row["test_files"])
        if inject.returncode != 0:
            return replay_failure(row, "hidden_verifier_injection_failed", inject, commands)
        for env_profile in historical_profiles(profile, row["task_time"]):
            command = uv_pytest_command(env_profile, row["pytest_files"])
            target_result = run_command(command, target_worktree, timeout=int(env_profile.get("max_seconds") or 180))
            commands.append(command_record("reference_target", env_profile, command, target_result))
            if target_result.returncode != 0:
                continue
            base_result = run_command(command, base_worktree, timeout=int(env_profile.get("max_seconds") or 180))
            commands.append(command_record("base_with_injected_tests", env_profile, command, base_result))
            if base_result.returncode == 0:
                return {
                    **replay_base_row(row),
                    "terminal_status": "failed",
                    "failure_label": "base_passed_changed_tests_not_meaningful",
                    "winning_profile_id": env_profile["profile_id"],
                    "verifier_duration_seconds": target_result.duration_seconds + base_result.duration_seconds,
                    "commands": commands,
                }
            return {
                **replay_base_row(row),
                "terminal_status": "passed",
                "failure_label": "",
                "winning_profile_id": env_profile["profile_id"],
                "verifier_duration_seconds": target_result.duration_seconds + base_result.duration_seconds,
                "commands": commands,
            }
        terminal = commands[-1]["subgate_label"] if commands else "reference_replay_not_attempted"
        return {
            **replay_base_row(row),
            "terminal_status": "failed",
            "failure_label": f"reference_{terminal}",
            "winning_profile_id": "",
            "verifier_duration_seconds": sum(float(command.get("duration_seconds") or 0.0) for command in commands),
            "commands": commands,
        }
    finally:
        cleanup_worktree(repo, base_worktree)
        cleanup_worktree(repo, target_worktree)


def replay_failure(row: dict[str, Any], label: str, result: CommandResult, commands: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        **replay_base_row(row),
        "terminal_status": "failed",
        "failure_label": label,
        "duration_seconds": result.duration_seconds,
        "stdout_tail_hash": digest_text(result.stdout[-1000:]),
        "stderr_tail_hash": digest_text(result.stderr[-1000:]),
        "commands": commands,
    }


def replay_base_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": row["task_id"],
        "target_commit": row["target_commit"],
        "base_commit": row["base_commit"],
        "task_time": row["task_time"],
        "module_family": row["module_family"],
        "changed_implementation_files": row["implementation_files"],
        "changed_test_files": row["test_files"],
        "pytest_entry_files": row["pytest_files"],
        "public_source_context_reference": row["public_source_context_reference"],
        "preliminary_risk_label": row["preliminary_risk_label"],
    }


def run_replay_preflight(limit: int = 5) -> dict[str, Any]:
    profile = read_json(CONFIG)
    repo = repo_path(profile["ignored_local_checkout_path"])
    rows = candidate_rows(repo)
    sampled = preflight_sample(rows, limit)
    results = [replay_candidate(profile, repo, row, scratch_root=SCRATCH / "preflight") for row in sampled]
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.replay_preflight.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repo_id": profile["repo_id"],
        "candidate_pool_size": len(rows),
        "sample_size": len(results),
        "pass_count": sum(1 for row in results if row.get("terminal_status") == "passed"),
        "dominant_failure_labels": failure_counts(results),
        "version_aware_policy": profile["dependency_setup_policy"]["historical_policy"],
        "profiles_tried_policy": "date-compatible historical profiles only; include the current profile only for near-current tasks; stop on first reference pass",
        "raw_output_committed": False,
        "results": results,
    }
    write_json(RESULTS / "sphinx_replay_preflight.json", payload)
    write_text(REPORTS / "sphinx_verifier_pinning_preflight_zh.md", preflight_report(payload))
    return payload


def inventory_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": row["task_id"],
        "commit": row["target_commit"],
        "parent_base_commit": row["base_commit"],
        "task_time": row["task_time"],
        "time_bucket": row["time_bucket"],
        "changed_implementation_files": row["implementation_files"],
        "changed_test_files": row["test_files"],
        "pytest_entry_files": row["pytest_files"],
        "module_family": row["module_family"],
        "public_source_context_reference": row["public_source_context_reference"],
        "preliminary_risk_label": row["preliminary_risk_label"],
        "expected_targeted_verifier_command": row["expected_targeted_verifier_command"],
    }


def run_candidate_inventory(limit: int = 180) -> dict[str, Any]:
    profile = read_json(CONFIG)
    repo = repo_path(profile["ignored_local_checkout_path"])
    rows = inventory_sample(candidate_rows(repo), limit)
    records = [inventory_record(row) for row in rows]
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.candidate_inventory.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repo_id": profile["repo_id"],
        "inventory_limit": limit,
        "candidate_count": len(records),
        "time_bucket_distribution": counted(row["time_bucket"] for row in records),
        "module_family_distribution": counted(row["module_family"] for row in records),
        "risk_distribution": counted(row["preliminary_risk_label"] for row in records),
        "rows": records,
    }
    write_json(RESULTS / "sphinx_candidate_inventory.json", payload)
    write_csv(
        RESULTS / "sphinx_candidate_inventory.csv",
        [csv_inventory_row(row) for row in records],
        [
            "task_id",
            "commit",
            "parent_base_commit",
            "task_time",
            "time_bucket",
            "module_family",
            "preliminary_risk_label",
            "changed_implementation_files",
            "changed_test_files",
            "pytest_entry_files",
            "public_source_context_reference",
            "expected_targeted_verifier_command",
        ],
    )
    write_text(REPORTS / "sphinx_candidate_inventory_zh.md", inventory_report(payload))
    return payload


def csv_inventory_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "changed_implementation_files": ";".join(row["changed_implementation_files"]),
        "changed_test_files": ";".join(row["changed_test_files"]),
        "pytest_entry_files": ";".join(row["pytest_entry_files"]),
    }


def run_certification_wave(limit: int = 24) -> dict[str, Any]:
    profile = read_json(CONFIG)
    repo = repo_path(profile["ignored_local_checkout_path"])
    inventory = inventory_sample(candidate_rows(repo), 180)
    sampled = certification_sample(inventory, limit)
    results = [replay_candidate(profile, repo, row, scratch_root=SCRATCH / "certification_wave") for row in sampled]
    flat_rows = [certification_csv_row(row) for row in results]
    durations = [float(row["verifier_duration_seconds"]) for row in flat_rows if row.get("verifier_duration_seconds") not in {"", None}]
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.certification_wave.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repo_id": profile["repo_id"],
        "sample_size": len(results),
        "pass_count": sum(1 for row in results if row.get("terminal_status") == "passed"),
        "conversion_rate": round(sum(1 for row in results if row.get("terminal_status") == "passed") / len(results), 4) if results else 0.0,
        "dominant_failure_labels": failure_counts(results),
        "time_bucket_distribution": counted(row["time_bucket"] for row in flat_rows),
        "module_family_distribution": counted(row["module_family"] for row in flat_rows),
        "verifier_duration_summary": duration_summary(durations),
        "raw_output_committed": False,
        "sample_policy": "24 deterministic spread-sample candidates across pre_2022, 2022_2023, and 2024_plus where available; normal-risk rows preferred before wider risk labels.",
        "rows": results,
        "flat_rows": flat_rows,
    }
    write_json(RESULTS / "sphinx_certification_wave.json", payload)
    write_csv(
        RESULTS / "sphinx_certification_wave.csv",
        flat_rows,
        [
            "task_id",
            "target_commit",
            "base_commit",
            "task_time",
            "time_bucket",
            "module_family",
            "terminal_status",
            "failure_label",
            "winning_profile_id",
            "base_workspace_prepared",
            "changed_tests_reconstructed",
            "hidden_verifier_injection_works",
            "base_reference_behavior_meaningful",
            "verifier_duration_seconds",
            "changed_implementation_files",
            "changed_test_files",
            "pytest_entry_files",
        ],
    )
    write_text(REPORTS / "sphinx_certification_wave_zh.md", certification_report(payload))
    return payload


def certification_csv_row(row: dict[str, Any]) -> dict[str, Any]:
    failure = str(row.get("failure_label") or "")
    return {
        "task_id": row["task_id"],
        "target_commit": row["target_commit"],
        "base_commit": row["base_commit"],
        "task_time": row["task_time"],
        "time_bucket": time_bucket(parse_datetime(row["task_time"]).year),
        "module_family": row["module_family"],
        "terminal_status": row["terminal_status"],
        "failure_label": failure,
        "winning_profile_id": row.get("winning_profile_id", ""),
        "base_workspace_prepared": failure not in {"base_worktree_failed", "target_worktree_failed"},
        "changed_tests_reconstructed": failure != "changed_test_oracle_missing",
        "hidden_verifier_injection_works": failure not in {
            "base_worktree_failed",
            "target_worktree_failed",
            "changed_test_oracle_missing",
            "hidden_verifier_injection_failed",
        },
        "base_reference_behavior_meaningful": row.get("terminal_status") == "passed",
        "verifier_duration_seconds": round(float(row.get("verifier_duration_seconds") or row.get("duration_seconds") or 0.0), 3),
        "changed_implementation_files": ";".join(row.get("changed_implementation_files") or []),
        "changed_test_files": ";".join(row.get("changed_test_files") or []),
        "pytest_entry_files": ";".join(row.get("pytest_entry_files") or []),
    }


def counted(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


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


def inventory_report(payload: dict[str, Any]) -> str:
    return f"""# Sphinx candidate inventory

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结果

本轮写出 bounded inventory `{payload['candidate_count']}` 条；上限 `{payload['inventory_limit']}`。这些条目均有实现文件、changed-test oracle、pytest entry 文件、base commit、target commit 和公开 issue/PR 引用。

- time buckets: `{payload['time_bucket_distribution']}`
- module families: `{payload['module_family_distribution']}`
- preliminary risks: `{payload['risk_distribution']}`

该 inventory 是 certification wave 和 rolling-origin feasibility 的 no-paid 输入，不是完整 Sphinx 历史挖掘。
"""


def certification_report(payload: dict[str, Any]) -> str:
    table = markdown_table(
        [
            {
                "task": row["task_id"],
                "bucket": row["time_bucket"],
                "family": row["module_family"],
                "status": row["terminal_status"],
                "label": row["failure_label"],
                "profile": row["winning_profile_id"],
                "seconds": row["verifier_duration_seconds"],
            }
            for row in payload["flat_rows"]
        ],
        [("Task", "task"), ("Bucket", "bucket"), ("Family", "family"), ("Status", "status"), ("Label", "label"), ("Profile", "profile"), ("Seconds", "seconds")],
    )
    return f"""# Sphinx certification wave

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

bounded no-paid certification/replay wave 为 `{payload['pass_count']}/{payload['sample_size']}` 通过，conversion rate `{payload['conversion_rate']}`。

## 覆盖

- time buckets: `{payload['time_bucket_distribution']}`
- module families: `{payload['module_family_distribution']}`
- sample policy: {payload['sample_policy']}

## Verifier speed

`{payload['verifier_duration_summary']}`

## Failure labels

`{payload['dominant_failure_labels']}`

## Rows

{table}

## Artifact hygiene

只提交 sanitized CSV/JSON/report。未提交 raw stdout/stderr、solver workspace、verifier workspace、prompt、completion 或 transcript。
"""


def run_rolling_origin_policy() -> dict[str, Any]:
    inventory = read_json(RESULTS / "sphinx_candidate_inventory.json")
    wave = read_json(RESULTS / "sphinx_certification_wave.json")
    payload = build_rolling_origin_policy(inventory, wave)
    write_json(RESULTS / "sphinx_rolling_origin_policy.json", payload)
    write_text(REPORTS / "sphinx_rolling_origin_policy_zh.md", rolling_origin_report(payload))
    return payload


def build_rolling_origin_policy(inventory: dict[str, Any], wave: dict[str, Any]) -> dict[str, Any]:
    conversion = float(wave.get("conversion_rate") or 0.0)
    projected_certified = round(int(inventory.get("candidate_count") or 0) * conversion)
    min_train = 40
    selection_count = 20
    future_count = 20
    stride = 20
    baseline_agent_count = 4
    windows = []
    origin = min_train
    while origin + selection_count + future_count <= projected_certified:
        windows.append(
            {
                "origin_id": f"origin_{origin}",
                "origin_task_index": origin,
                "historical_train_count": origin,
                "selected_benchmark_count": selection_count,
                "future_validation_count": future_count,
                "overlap_with_previous_selected_tasks": 0,
                "prediction_target": "selected benchmark pass rate",
                "actual_target": "later/future task pass rate",
                "mae_formula": "abs(predicted_selected_pass_rate - actual_future_pass_rate)",
                "tuning_uplift_error_formula": "abs(predicted_after_minus_before_uplift - actual_future_after_minus_before_uplift)",
                "expected_paid_baseline_discovery_cells": (selection_count + future_count) * baseline_agent_count,
                "expected_paid_tuning_before_after_cells": future_count * 2,
            }
        )
        origin += stride
    return {
        "schema_version": f"{SCHEMA_VERSION}.rolling_origin_policy.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repo_id": "sphinx",
        "evidence_inputs": {
            "candidate_inventory": "experiments/agent_tuning_demo/results/sphinx_candidate_inventory.json",
            "certification_wave": "experiments/agent_tuning_demo/results/sphinx_certification_wave.json",
            "certification_sample_size": wave.get("sample_size"),
            "certification_pass_count": wave.get("pass_count"),
            "certification_conversion_rate": wave.get("conversion_rate"),
            "inventory_candidate_count": inventory.get("candidate_count"),
            "projected_certified_count_from_wave": projected_certified,
        },
        "primary_policy": {
            "policy_id": "fixed_task_count_40_20_20_stride20",
            "ordering": "task_time ascending over certification-expanded Sphinx task manifest",
            "minimum_tasks_per_segment": {
                "historical_train": min_train,
                "selected_benchmark": selection_count,
                "future_validation": future_count,
            },
            "stride": stride,
            "overlap_policy": "no overlap between selected benchmark and future validation within a window; historical train is cumulative",
            "windows": windows,
            "window_count": len(windows),
        },
        "paid_cell_estimates": {
            "agent_count_for_baseline_discovery": baseline_agent_count,
            "baseline_discovery_cells_per_window": (selection_count + future_count) * baseline_agent_count,
            "selected_only_baseline_cells_per_window": selection_count * baseline_agent_count,
            "future_only_baseline_cells_per_window": future_count * baseline_agent_count,
            "baseline_discovery_cells_total_for_policy": sum(window["expected_paid_baseline_discovery_cells"] for window in windows),
            "tuning_before_after_cells_per_window": future_count * 2,
            "tuning_before_after_cells_total_for_policy": sum(window["expected_paid_tuning_before_after_cells"] for window in windows),
            "authorization": "not_authorized_by_this_no_paid_gate",
        },
        "feasibility": {
            "at_least_two_windows_projected": len(windows) >= 2,
            "verifier_speed_summary": wave.get("verifier_duration_summary", {}),
            "dominant_failure_labels": wave.get("dominant_failure_labels", {}),
            "unsupported_until_followup": [
                "Windows are projected from a 24-row certification wave, not frozen certified task manifests.",
                "Paid baseline discovery and before/after tuning require a separate preregistered paid runbook.",
            ],
        },
    }


def rolling_origin_report(payload: dict[str, Any]) -> str:
    policy = payload["primary_policy"]
    cells = payload["paid_cell_estimates"]
    table = markdown_table(
        [
            {
                "origin": window["origin_id"],
                "train": window["historical_train_count"],
                "selected": window["selected_benchmark_count"],
                "future": window["future_validation_count"],
                "baseline_cells": window["expected_paid_baseline_discovery_cells"],
                "tuning_cells": window["expected_paid_tuning_before_after_cells"],
            }
            for window in policy["windows"]
        ],
        [("Origin", "origin"), ("Train", "train"), ("Selected", "selected"), ("Future", "future"), ("Baseline cells", "baseline_cells"), ("Tuning cells", "tuning_cells")],
    )
    return f"""# Sphinx rolling-origin policy

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

主策略：`{policy['policy_id']}`。基于 certification wave 的 projected certified count 为 `{payload['evidence_inputs']['projected_certified_count_from_wave']}`，可支持 `{policy['window_count']}` 个 projected rolling-origin windows。

## Policy

- ordering: {policy['ordering']}
- minimum segments: `{policy['minimum_tasks_per_segment']}`
- stride: `{policy['stride']}`
- overlap: {policy['overlap_policy']}

{table}

## Metrics

每个 window 计算 selected benchmark predicted pass rate 与 later/future actual pass rate 的 MAE：`abs(predicted_selected_pass_rate - actual_future_pass_rate)`。

若未来执行 paid tuning，再用 future segment 计算 before/after uplift error：`abs(predicted_after_minus_before_uplift - actual_future_after_minus_before_uplift)`。

## Paid Cell Estimate

- baseline discovery: `{cells['baseline_discovery_cells_per_window']}` cells/window, `{cells['baseline_discovery_cells_total_for_policy']}` cells for the projected policy.
- selected-only component: `{cells['selected_only_baseline_cells_per_window']}` cells/window; future-only component: `{cells['future_only_baseline_cells_per_window']}` cells/window.
- before/after tuning: `{cells['tuning_before_after_cells_per_window']}` cells/window, `{cells['tuning_before_after_cells_total_for_policy']}` cells for the projected policy.
- authorization: `{cells['authorization']}`.

## Unsupported

{chr(10).join(f"- {item}" for item in payload['feasibility']['unsupported_until_followup'])}
"""


def build_rolling_origin_protocol_v2() -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}.rolling_origin_protocol.v2",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repo_id": "sphinx",
        "supersedes": {
            "artifact": "experiments/agent_tuning_demo/results/sphinx_rolling_origin_policy.json",
            "reason": "The earlier feasibility artifact used train/selected/future as three disjoint segments and carried selected-only baseline cell accounting.",
        },
        "field_definitions": {
            "history_pool_before_origin": "All eligible certified Sphinx tasks whose task ordering position is before the origin.",
            "selected_benchmark_from_history": "A selector/compiler-chosen subset of history_pool_before_origin; the future holdout is not an input.",
            "future_holdout_after_origin": "The next task-time ordered certified task window after the origin, used only after selection for scoring.",
            "origin_stride": "The number of certified task positions between consecutive origins.",
            "selected_benchmark_size": "The number of history-pool tasks the future preregistered selector may choose for a window.",
            "future_holdout_size": "The number of post-origin certified tasks used as the pseudo-future target for a window.",
        },
        "default_window_parameters": {
            "task_ordering": "task_time ascending, stable tie-break by task_id",
            "origin_history_sizes": DEFAULT_HISTORY_SIZES,
            "origin_stride": DEFAULT_ORIGIN_STRIDE,
            "selected_benchmark_size": DEFAULT_SELECTED_BENCHMARK_SIZE,
            "future_holdout_size": DEFAULT_FUTURE_HOLDOUT_SIZE,
        },
        "selector_leakage_rules": {
            "selector_inputs_allowed": [
                "history_pool_before_origin task IDs",
                "history_pool_before_origin solver-visible metadata",
                "history_pool_before_origin task statements and allowed context when the next runbook preregisters those fields",
            ],
            "selector_inputs_forbidden": [
                "future_holdout_after_origin task IDs",
                "future_holdout_after_origin labels",
                "future_holdout_after_origin Agent outcomes",
                "private oracle material",
                "verifier-only evidence beyond sanitized certification status needed to establish eligibility",
            ],
            "future_holdout_task_ids_allowed_before_selection": False,
            "selected_task_constraint": "selected_benchmark_from_history must be a subset of history_pool_before_origin and must not be picked from post-origin tasks.",
        },
        "score_join_rules": {
            "baseline_discovery": "After selection is frozen, join Agent outcomes for selected benchmark tasks and future holdout tasks under the same verifier policy.",
            "hidden_oracle_boundary": "Private oracle material is injected only in verifier workspaces, never into selector inputs or solver workspaces.",
            "failure_policy": "Timeout, harness error, invalid output, and no meaningful change remain failed user-visible attempts unless the next preregistration explicitly narrows a scoreable denominator.",
            "reuse_policy": "A task-Agent result may be reused across windows only after it has been legitimately run for a previous selected or future set; future holdout identity cannot be used to choose earlier selected tasks.",
        },
        "metric_formulas": {
            "pass_rate_prediction_error": "For origin o and Agent a: abs(mean(score[a,t] for t in selected_benchmark_from_history[o]) - mean(score[a,t] for t in future_holdout_after_origin[o])).",
            "mae_across_origins": "Mean pass_rate_prediction_error over preregistered origins and Agents with complete selected/future outcome joins.",
            "tuning_uplift_prediction_error": "For later paid tuning only: abs((mean(after-before on selected_benchmark_from_history[o])) - (mean(after-before on future_holdout_after_origin[o]))).",
        },
        "selector_status": "not_chosen_in_this_runbook",
        "no_paid_boundary": "This protocol artifact authorizes no paid Agent cells, paid LLM calls, tuner calls, baseline discovery, or before/after tuning experiments.",
    }


def run_rolling_origin_protocol_v2() -> dict[str, Any]:
    payload = build_rolling_origin_protocol_v2()
    write_json(RESULTS / "sphinx_rolling_origin_protocol_v2.json", payload)
    write_text(REPORTS / "sphinx_rolling_origin_protocol_v2_zh.md", rolling_origin_protocol_v2_report(payload))
    return payload


def rolling_origin_protocol_v2_report(payload: dict[str, Any]) -> str:
    fields = "\n".join(f"- `{key}`: {value}" for key, value in payload["field_definitions"].items())
    forbidden = "\n".join(f"- {item}" for item in payload["selector_leakage_rules"]["selector_inputs_forbidden"])
    metrics = "\n".join(f"- `{key}`: {value}" for key, value in payload["metric_formulas"].items())
    defaults = payload["default_window_parameters"]
    return f"""# Sphinx rolling-origin protocol v2

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

本 artifact 修正 rolling-origin 协议：每个 origin 的 selected benchmark 必须从 `history_pool_before_origin` 中选择；`future_holdout_after_origin` 是选择完成之后才用于评分的伪未来窗口，不是 selector/compiler 的输入。

旧 artifact `{payload['supersedes']['artifact']}` 的问题：{payload['supersedes']['reason']}

## 字段定义

{fields}

## 默认窗口参数

- task ordering: `{defaults['task_ordering']}`
- origin history sizes: `{defaults['origin_history_sizes']}`
- origin stride: `{defaults['origin_stride']}`
- selected benchmark size: `{defaults['selected_benchmark_size']}`
- future holdout size: `{defaults['future_holdout_size']}`

## 泄漏规则

selector 可以使用历史池内的 solver-visible 信息。禁止输入：

{forbidden}

`future_holdout_after_origin` 的 task IDs/outcomes 不得影响 selector/compiler。

## Score Join

{payload['score_join_rules']['baseline_discovery']} {payload['score_join_rules']['hidden_oracle_boundary']} {payload['score_join_rules']['failure_policy']}

## Metrics

{metrics}

## 边界

本文件不选择最终 selector algorithm，也不授权任何付费执行。
"""


def split_path_field(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if value in {"", None}:
        return []
    return [part for part in str(value).split(";") if part]


def inventory_record_to_replay_row(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": record["task_id"],
        "target_commit": record["commit"],
        "base_commit": record["parent_base_commit"],
        "task_time": record["task_time"],
        "module_family": record["module_family"],
        "implementation_files": split_path_field(record.get("changed_implementation_files")),
        "test_files": split_path_field(record.get("changed_test_files")),
        "pytest_files": split_path_field(record.get("pytest_entry_files")),
        "public_source_context_reference": record.get("public_source_context_reference", ""),
        "preliminary_risk_label": record.get("preliminary_risk_label", "normal"),
    }


def certification_manifest_row(
    flat_row: dict[str, Any],
    inventory_by_id: dict[str, dict[str, Any]],
    provenance: str,
) -> dict[str, Any]:
    inventory_row = inventory_by_id.get(str(flat_row["task_id"]), {})
    row = {
        "task_id": flat_row["task_id"],
        "target_commit": flat_row["target_commit"],
        "base_commit": flat_row["base_commit"],
        "task_time": flat_row["task_time"],
        "time_bucket": flat_row.get("time_bucket") or time_bucket(parse_datetime(flat_row["task_time"]).year),
        "module_family": flat_row.get("module_family") or inventory_row.get("module_family", ""),
        "changed_implementation_files": ";".join(
            split_path_field(flat_row.get("changed_implementation_files")) or split_path_field(inventory_row.get("changed_implementation_files"))
        ),
        "changed_test_files": ";".join(split_path_field(flat_row.get("changed_test_files")) or split_path_field(inventory_row.get("changed_test_files"))),
        "pytest_entry_files": ";".join(split_path_field(flat_row.get("pytest_entry_files")) or split_path_field(inventory_row.get("pytest_entry_files"))),
        "winning_verifier_profile": flat_row.get("winning_profile_id") or flat_row.get("winning_verifier_profile", ""),
        "verifier_duration_seconds": round(float(flat_row.get("verifier_duration_seconds") or 0.0), 3),
        "source_certification_provenance": provenance,
    }
    digest_material = {key: row[key] for key in row if key != "evidence_digest"}
    row["evidence_digest"] = digest_text(json.dumps(digest_material, ensure_ascii=False, sort_keys=True))
    return row


def certified_manifest_sort_key(row: dict[str, Any]) -> tuple[datetime, str]:
    return (parse_datetime(row["task_time"]), str(row["task_id"]))


def repairable_failure_profile(labels: dict[str, int]) -> bool:
    if not labels:
        return False
    repairable = {
        "reference_dependency_mismatch_or_install_failed",
        "reference_import_failed",
        "reference_collection_failed",
    }
    return set(labels).issubset(repairable)


def run_certification_expanded_manifest(
    *,
    preferred_threshold: int = 100,
    minimum_threshold: int = 80,
    stop_window: int = 30,
) -> dict[str, Any]:
    profile = read_json(CONFIG)
    repo = repo_path(profile["ignored_local_checkout_path"])
    inventory = read_json(RESULTS / "sphinx_candidate_inventory.json")
    wave = read_json(RESULTS / "sphinx_certification_wave.json")
    inventory_rows = sorted(inventory.get("rows", []), key=lambda row: (row.get("task_time", ""), row.get("task_id", "")))
    inventory_by_id = {str(row["task_id"]): row for row in inventory_rows}
    prior_flat_rows = list(wave.get("flat_rows") or [])
    attempted_ids = {str(row["task_id"]) for row in prior_flat_rows}
    certified_by_id: dict[str, dict[str, Any]] = {}
    for flat_row in prior_flat_rows:
        if flat_row.get("terminal_status") == "passed":
            certified_by_id[str(flat_row["task_id"])] = certification_manifest_row(
                flat_row,
                inventory_by_id,
                "sphinx_certification_wave",
            )

    additional_flat_rows: list[dict[str, Any]] = []
    stop_reason = "preferred_threshold_reached" if len(certified_by_id) >= preferred_threshold else "inventory_exhausted"
    for inventory_row in inventory_rows:
        if len(certified_by_id) >= preferred_threshold:
            stop_reason = "preferred_threshold_reached"
            break
        task_id = str(inventory_row["task_id"])
        if task_id in attempted_ids:
            continue
        result = replay_candidate(profile, repo, inventory_record_to_replay_row(inventory_row), scratch_root=SCRATCH / "certification_expanded")
        flat_row = certification_csv_row(result)
        additional_flat_rows.append(flat_row)
        attempted_ids.add(task_id)
        if flat_row.get("terminal_status") == "passed":
            certified_by_id[task_id] = certification_manifest_row(
                flat_row,
                inventory_by_id,
                "sphinx_certification_expansion",
            )
        recent = additional_flat_rows[-stop_window:]
        if len(recent) == stop_window:
            recent_passes = sum(1 for row in recent if row.get("terminal_status") == "passed")
            recent_rate = recent_passes / stop_window
            recent_labels = failure_counts(recent)
            if recent_rate < 0.30 and not repairable_failure_profile(recent_labels):
                stop_reason = "recent_conversion_below_0_30_and_not_clearly_repairable"
                break

    tasks = sorted(certified_by_id.values(), key=certified_manifest_sort_key)
    threshold_state = "preferred_met" if len(tasks) >= preferred_threshold else "minimum_met" if len(tasks) >= minimum_threshold else "below_minimum"
    durations = [float(row["verifier_duration_seconds"]) for row in tasks]
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.certification_expanded_manifest.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repo_id": profile["repo_id"],
        "source_inputs": {
            "candidate_inventory": "experiments/agent_tuning_demo/results/sphinx_candidate_inventory.json",
            "certification_wave": "experiments/agent_tuning_demo/results/sphinx_certification_wave.json",
        },
        "thresholds": {
            "preferred_certified_tasks": preferred_threshold,
            "minimum_certified_tasks": minimum_threshold,
            "preferred_policy": "origins at history sizes 40/60/80 with future_holdout_size=20",
            "minimum_policy": "origins at history sizes 40/60 with future_holdout_size=20",
        },
        "certified_task_count": len(tasks),
        "threshold_state": threshold_state,
        "stop_reason": stop_reason,
        "attempt_accounting": {
            "prior_wave_attempt_count": len(prior_flat_rows),
            "prior_wave_pass_count": sum(1 for row in prior_flat_rows if row.get("terminal_status") == "passed"),
            "additional_attempt_count": len(additional_flat_rows),
            "additional_pass_count": sum(1 for row in additional_flat_rows if row.get("terminal_status") == "passed"),
            "additional_failure_labels": failure_counts(additional_flat_rows),
            "total_attempt_count": len(prior_flat_rows) + len(additional_flat_rows),
            "total_pass_count": len(tasks),
        },
        "time_bucket_distribution": counted(row["time_bucket"] for row in tasks),
        "module_family_distribution": counted(row["module_family"] for row in tasks),
        "verifier_duration_summary": duration_summary(durations),
        "raw_output_committed": False,
        "tasks": tasks,
    }
    write_json(RESULTS / "sphinx_certification_expanded_manifest.json", payload)
    write_csv(RESULTS / "sphinx_certification_expanded_manifest.csv", tasks, CERTIFIED_MANIFEST_FIELDS)
    write_text(REPORTS / "sphinx_certification_expanded_manifest_zh.md", certification_expanded_manifest_report(payload))
    return payload


def certification_expanded_manifest_report(payload: dict[str, Any]) -> str:
    rows = [
        {
            "task": row["task_id"],
            "bucket": row["time_bucket"],
            "family": row["module_family"],
            "profile": row["winning_verifier_profile"],
            "seconds": row["verifier_duration_seconds"],
            "provenance": row["source_certification_provenance"],
        }
        for row in payload["tasks"]
    ]
    table = markdown_table(
        rows,
        [("Task", "task"), ("Bucket", "bucket"), ("Family", "family"), ("Profile", "profile"), ("Seconds", "seconds"), ("Provenance", "provenance")],
    )
    return f"""# Sphinx certification-expanded manifest

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

exact certified task manifest 包含 `{payload['certified_task_count']}` 个 Sphinx tasks；threshold state: `{payload['threshold_state']}`；stop reason: `{payload['stop_reason']}`。

## 输入与扩展

- candidate inventory: `{payload['source_inputs']['candidate_inventory']}`
- existing certification wave: `{payload['source_inputs']['certification_wave']}`
- prior wave attempts/pass: `{payload['attempt_accounting']['prior_wave_attempt_count']}` / `{payload['attempt_accounting']['prior_wave_pass_count']}`
- additional no-paid attempts/pass: `{payload['attempt_accounting']['additional_attempt_count']}` / `{payload['attempt_accounting']['additional_pass_count']}`
- additional failure labels: `{payload['attempt_accounting']['additional_failure_labels']}`

## 覆盖

- time buckets: `{payload['time_bucket_distribution']}`
- module families: `{payload['module_family_distribution']}`
- verifier duration: `{payload['verifier_duration_summary']}`

## Certified rows

{table}

## Artifact hygiene

manifest 只保留 sanitized task metadata、profile、duration、provenance 和 evidence digest；未提交 raw stdout/stderr、solver workspace、verifier workspace、prompt、completion 或 transcript。
"""


def build_window_manifest_from_tasks(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(tasks, key=certified_manifest_sort_key)
    windows = []
    for origin_size in DEFAULT_HISTORY_SIZES:
        if origin_size + DEFAULT_FUTURE_HOLDOUT_SIZE > len(ordered):
            continue
        history = ordered[:origin_size]
        future = ordered[origin_size : origin_size + DEFAULT_FUTURE_HOLDOUT_SIZE]
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
                    "selection_size": DEFAULT_SELECTED_BENCHMARK_SIZE,
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
    threshold_state = "preferred_policy_supported" if len(windows) >= 3 else "minimum_policy_supported" if len(windows) >= 2 else "below_minimum_policy"
    return {
        "schema_version": f"{SCHEMA_VERSION}.rolling_origin_window_manifest.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repo_id": "sphinx",
        "source_manifest": "experiments/agent_tuning_demo/results/sphinx_certification_expanded_manifest.json",
        "certified_task_count": len(ordered),
        "window_threshold_state": threshold_state,
        "preferred_policy_minimum_certified_tasks": 100,
        "minimum_policy_minimum_certified_tasks": 80,
        "task_ordering": "certified tasks by task_time ascending, stable tie-break by task_id",
        "origin_stride": DEFAULT_ORIGIN_STRIDE,
        "selected_benchmark_size": DEFAULT_SELECTED_BENCHMARK_SIZE,
        "future_holdout_size": DEFAULT_FUTURE_HOLDOUT_SIZE,
        "windows": windows,
        "window_count": len(windows),
        "selector_status": "not_chosen_in_this_runbook",
        "selector_leakage_rule": "Future holdout IDs/outcomes are withheld from selector/compiler until after selected_benchmark_from_history is frozen.",
    }


def run_rolling_origin_window_manifest() -> dict[str, Any]:
    manifest = read_json(RESULTS / "sphinx_certification_expanded_manifest.json")
    payload = build_window_manifest_from_tasks(list(manifest.get("tasks") or []))
    write_json(RESULTS / "sphinx_rolling_origin_window_manifest.json", payload)
    write_text(REPORTS / "sphinx_rolling_origin_window_manifest_zh.md", rolling_origin_window_manifest_report(payload))
    return payload


def rolling_origin_window_manifest_report(payload: dict[str, Any]) -> str:
    table = markdown_table(
        [
            {
                "origin": window["origin_id"],
                "history": window["history_pool_before_origin"]["task_count"],
                "selected": window["selected_benchmark_from_history"]["selection_size"],
                "future": window["future_holdout_after_origin"]["task_count"],
                "first_future": (window["future_holdout_after_origin"]["task_ids"] or [""])[0],
                "last_future": (window["future_holdout_after_origin"]["task_ids"] or [""])[-1],
            }
            for window in payload["windows"]
        ],
        [("Origin", "origin"), ("History pool", "history"), ("Selected size", "selected"), ("Future holdout", "future"), ("First future", "first_future"), ("Last future", "last_future")],
    )
    return f"""# Sphinx corrected rolling-origin window manifest

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

certified task count `{payload['certified_task_count']}` supports `{payload['window_count']}` corrected windows；state: `{payload['window_threshold_state']}`。

Preferred policy requires `{payload['preferred_policy_minimum_certified_tasks']}` certified tasks for origins `40/60/80`; minimum acceptable policy requires `{payload['minimum_policy_minimum_certified_tasks']}` certified tasks for origins `40/60`。当前 manifest 只有 `{payload['certified_task_count']}` tasks，因此不伪造 smaller windows。

## 规则

- ordering: `{payload['task_ordering']}`
- origin stride: `{payload['origin_stride']}`
- selected benchmark size: `{payload['selected_benchmark_size']}`
- future holdout size: `{payload['future_holdout_size']}`
- selector status: `{payload['selector_status']}`

{payload['selector_leakage_rule']}

## Windows

{table}

每个 JSON window 都列出 exact `history_pool_before_origin.task_ids` 和 exact `future_holdout_after_origin.task_ids`。本轮不选择 selected task IDs。
"""


def choose_for_min_unique(pool: list[str], already_selected: set[str], future_ids: set[str], size: int) -> set[str]:
    chosen: list[str] = []
    for group in (
        [task_id for task_id in pool if task_id in already_selected],
        [task_id for task_id in pool if task_id in future_ids and task_id not in already_selected],
        [task_id for task_id in pool if task_id not in future_ids and task_id not in already_selected],
    ):
        for task_id in group:
            if task_id not in chosen:
                chosen.append(task_id)
            if len(chosen) >= size:
                return set(chosen)
    return set(chosen)


def choose_for_max_unique(pool: list[str], already_selected: set[str], future_ids: set[str], size: int) -> set[str]:
    chosen: list[str] = []
    for group in (
        [task_id for task_id in pool if task_id not in future_ids and task_id not in already_selected],
        [task_id for task_id in pool if task_id not in already_selected],
        [task_id for task_id in pool if task_id in already_selected],
    ):
        for task_id in group:
            if task_id not in chosen:
                chosen.append(task_id)
            if len(chosen) >= size:
                return set(chosen)
    return set(chosen)


def selected_unique_bounds(windows: list[dict[str, Any]], future_ids: set[str]) -> tuple[int, int, int, int]:
    min_selected: set[str] = set()
    max_selected: set[str] = set()
    for window in windows:
        pool = list(window["selected_benchmark_from_history"]["allowed_task_ids"])
        size = int(window["selected_benchmark_from_history"]["selection_size"])
        min_selected.update(choose_for_min_unique(pool, min_selected, future_ids, size))
        max_selected.update(choose_for_max_unique(pool, max_selected, future_ids, size))
    return len(min_selected), len(max_selected), len(min_selected | future_ids), len(max_selected | future_ids)


def build_paid_cell_accounting(window_manifest: dict[str, Any], *, agent_count: int = DEFAULT_BASELINE_AGENT_COUNT) -> dict[str, Any]:
    windows = list(window_manifest.get("windows") or [])
    per_window = []
    future_ids: set[str] = set()
    for window in windows:
        selected_size = int(window["selected_benchmark_from_history"]["selection_size"])
        future_size = int(window["future_holdout_after_origin"]["task_count"])
        future_ids.update(window["future_holdout_after_origin"]["task_ids"])
        per_window.append(
            {
                "origin_id": window["origin_id"],
                "selected_benchmark_size": selected_size,
                "future_holdout_size": future_size,
                "agent_count_for_baseline_discovery": agent_count,
                "selected_benchmark_cells": selected_size * agent_count,
                "future_holdout_cells": future_size * agent_count,
                "naive_baseline_discovery_cells": (selected_size + future_size) * agent_count,
                "later_before_after_tuning_cells_full_formula": f"({selected_size} selected + {future_size} future) * 2 variants = {(selected_size + future_size) * 2}",
                "later_before_after_tuning_cells_selected_first_gate": selected_size * 2,
            }
        )
    min_selected, max_selected, min_total_unique, max_total_unique = selected_unique_bounds(windows, future_ids)
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.paid_cell_accounting.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repo_id": "sphinx",
        "source_window_manifest": "experiments/agent_tuning_demo/results/sphinx_rolling_origin_window_manifest.json",
        "agent_count_for_baseline_discovery": agent_count,
        "window_count": len(windows),
        "per_window": per_window,
        "total_naive_baseline_discovery_cells": sum(row["naive_baseline_discovery_cells"] for row in per_window),
        "total_naive_selected_benchmark_cells": sum(row["selected_benchmark_cells"] for row in per_window),
        "total_naive_future_holdout_cells": sum(row["future_holdout_cells"] for row in per_window),
        "deduplicated_unique_task_agent_cells": {
            "known_future_holdout_unique_task_count": len(future_ids),
            "known_future_holdout_unique_cells": len(future_ids) * agent_count,
            "selected_unique_task_count_range_depends_on_next_selector": [min_selected, max_selected],
            "selected_plus_future_unique_task_count_range_depends_on_next_selector": [min_total_unique, max_total_unique],
            "selected_plus_future_unique_cells_range_depends_on_next_selector": [min_total_unique * agent_count, max_total_unique * agent_count],
            "exact_selected_dedup_cells_status": "unknown_until_next_preregistration_selector_freezes_selected_task_ids",
        },
        "later_before_after_tuning_cells": {
            "full_selected_plus_future_formula_per_window": "(20 selected + 20 future) * 2 variants = 80 cells/window when using the default window sizes",
            "selected_first_gate_formula_per_window": "20 selected * 2 variants = 40 cells/window before any future gate",
            "authorization": "future_plan_only_not_authorized_by_this_no_paid_run",
        },
        "known_now": [
            "exact window count",
            "exact future holdout task IDs",
            "naive selected+future baseline-discovery cells per window",
            "known future-holdout deduplicated cells",
        ],
        "depends_on_next_preregistration_selector": [
            "exact selected benchmark task IDs",
            "exact selected benchmark deduplicated cells",
            "exact selected+future deduplicated cells across windows",
        ],
        "authorization": "not_authorized_by_this_no_paid_run",
    }
    return payload


def run_paid_cell_accounting() -> dict[str, Any]:
    window_manifest = read_json(RESULTS / "sphinx_rolling_origin_window_manifest.json")
    payload = build_paid_cell_accounting(window_manifest)
    write_json(RESULTS / "sphinx_paid_cell_accounting.json", payload)
    write_text(REPORTS / "sphinx_paid_cell_accounting_zh.md", paid_cell_accounting_report(payload))
    return payload


def paid_cell_accounting_report(payload: dict[str, Any]) -> str:
    table = markdown_table(
        [
            {
                "origin": row["origin_id"],
                "selected": row["selected_benchmark_cells"],
                "future": row["future_holdout_cells"],
                "naive": row["naive_baseline_discovery_cells"],
                "tuning_full": row["later_before_after_tuning_cells_full_formula"],
            }
            for row in payload["per_window"]
        ],
        [("Origin", "origin"), ("Selected cells", "selected"), ("Future cells", "future"), ("Naive baseline", "naive"), ("Later tuning formula", "tuning_full")],
    )
    dedup = payload["deduplicated_unique_task_agent_cells"]
    return f"""# Sphinx paid-cell accounting

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

baseline discovery 使用 `{payload['agent_count_for_baseline_discovery']}` Agents。默认 window 下 naive baseline discovery 是 `(20 selected + 20 future) * 4 = 160` cells/window，不再使用旧的 ambiguous `80 cells/window` 作为总数。

## Per-window accounting

{table}

Total naive baseline discovery cells: `{payload['total_naive_baseline_discovery_cells']}`。

## Deduplication

- known future holdout unique task-Agent cells: `{dedup['known_future_holdout_unique_cells']}`
- selected unique task count range depends on next selector: `{dedup['selected_unique_task_count_range_depends_on_next_selector']}`
- selected+future unique task-Agent cells range depends on next selector: `{dedup['selected_plus_future_unique_cells_range_depends_on_next_selector']}`
- exact selected dedup status: `{dedup['exact_selected_dedup_cells_status']}`

## Later before/after tuning

- full formula: `{payload['later_before_after_tuning_cells']['full_selected_plus_future_formula_per_window']}`
- selected-first gate formula: `{payload['later_before_after_tuning_cells']['selected_first_gate_formula_per_window']}`
- authorization: `{payload['later_before_after_tuning_cells']['authorization']}`

本 artifact 只做 accounting reconciliation，不授权 paid baseline discovery 或 tuning。
"""


def build_closeout(
    manifest: dict[str, Any],
    window_manifest: dict[str, Any],
    accounting: dict[str, Any],
    *,
    agent_tests_status: str,
    agent_tests_summary: str,
    git_diff_check_status: str,
    hygiene_scan_status: str,
    hygiene_scan_hits: list[str],
) -> dict[str, Any]:
    minimum_ready = int(manifest.get("certified_task_count") or 0) >= 80 and int(window_manifest.get("window_count") or 0) >= 2
    verification_ready = agent_tests_status == "passed" and git_diff_check_status == "passed" and hygiene_scan_status in {"passed", "explained_non_artifact_hit"}
    terminal_state = "sphinx_protocol_manifest_ready_for_paid_preregistration" if minimum_ready and verification_ready else "sphinx_manifest_needs_bounded_repair"
    return {
        "schema_version": f"{SCHEMA_VERSION}.protocol_manifest_freeze_closeout.v1",
        "generated_at": iso_now(),
        "terminal_state": terminal_state,
        "repo_id": "sphinx",
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "summary": {
            "corrected_protocol_written": True,
            "certified_task_count": manifest.get("certified_task_count"),
            "manifest_threshold_state": manifest.get("threshold_state"),
            "window_count": window_manifest.get("window_count"),
            "window_threshold_state": window_manifest.get("window_threshold_state"),
            "baseline_discovery_cells_per_default_window": (DEFAULT_SELECTED_BENCHMARK_SIZE + DEFAULT_FUTURE_HOLDOUT_SIZE) * DEFAULT_BASELINE_AGENT_COUNT,
            "total_naive_baseline_discovery_cells": accounting.get("total_naive_baseline_discovery_cells"),
        },
        "canonical_outputs": {
            "rolling_origin_protocol_v2": "experiments/agent_tuning_demo/results/sphinx_rolling_origin_protocol_v2.json",
            "certification_expanded_manifest": "experiments/agent_tuning_demo/results/sphinx_certification_expanded_manifest.json",
            "rolling_origin_window_manifest": "experiments/agent_tuning_demo/results/sphinx_rolling_origin_window_manifest.json",
            "paid_cell_accounting": "experiments/agent_tuning_demo/results/sphinx_paid_cell_accounting.json",
            "closeout": "experiments/agent_tuning_demo/results/sphinx_protocol_manifest_freeze_closeout.json",
        },
        "remaining_boundary": [
            "No paid Agent cells, paid LLM calls, tuner/proposer calls, baseline discovery, or before/after tuning experiments were run.",
            "The next preregistration runbook still needs to freeze the selector, Agents, endpoint proof, budget/timeouts, score-join details, and success criteria before any paid execution.",
            "This run did not write the paid-baseline-preregistration runbook.",
        ],
        "verification": {
            "agent_tuning_tests": {
                "command": "uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q",
                "status": agent_tests_status,
                "summary": agent_tests_summary,
            },
            "git_diff_check": {
                "command": "git diff --check",
                "status": git_diff_check_status,
            },
            "hygiene_scan": {
                "command": "git ls-files experiments/agent_tuning_demo experiments/demo_common experiments/phase0_headroom/target_profiles PROCESS.md | rg '(\\.venv|\\.pytest_cache|\\.DS_Store|__pycache__|\\.pyc$|raw|transcript|workspace|secret|prompt|completion)' || true",
                "status": hygiene_scan_status,
                "hits": hygiene_scan_hits,
                "explanation": "Any listed tracked hit was reviewed and is not a committed raw prompt/completion/transcript, secret, solver/verifier workspace, cache, or large raw artifact.",
            },
        },
    }


def run_closeout(
    *,
    agent_tests_status: str,
    agent_tests_summary: str,
    git_diff_check_status: str,
    hygiene_scan_status: str,
    hygiene_scan_hits: list[str],
) -> dict[str, Any]:
    manifest = read_json(RESULTS / "sphinx_certification_expanded_manifest.json")
    window_manifest = read_json(RESULTS / "sphinx_rolling_origin_window_manifest.json")
    accounting = read_json(RESULTS / "sphinx_paid_cell_accounting.json")
    payload = build_closeout(
        manifest,
        window_manifest,
        accounting,
        agent_tests_status=agent_tests_status,
        agent_tests_summary=agent_tests_summary,
        git_diff_check_status=git_diff_check_status,
        hygiene_scan_status=hygiene_scan_status,
        hygiene_scan_hits=hygiene_scan_hits,
    )
    write_json(RESULTS / "sphinx_protocol_manifest_freeze_closeout.json", payload)
    write_text(REPORTS / "sphinx_protocol_manifest_freeze_closeout_zh.md", closeout_report(payload))
    return payload


def closeout_report(payload: dict[str, Any]) -> str:
    outputs = "\n".join(f"- `{path}`" for path in payload["canonical_outputs"].values())
    boundaries = "\n".join(f"- {item}" for item in payload["remaining_boundary"])
    verification = payload["verification"]
    return f"""# Sphinx protocol and manifest freeze closeout

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

终态：`{payload['terminal_state']}`。

- corrected protocol written: `{payload['summary']['corrected_protocol_written']}`
- certified task count: `{payload['summary']['certified_task_count']}` (`{payload['summary']['manifest_threshold_state']}`)
- corrected window count: `{payload['summary']['window_count']}` (`{payload['summary']['window_threshold_state']}`)
- baseline discovery cells/default window: `{payload['summary']['baseline_discovery_cells_per_default_window']}`
- total naive baseline discovery cells: `{payload['summary']['total_naive_baseline_discovery_cells']}`

## Canonical outputs

{outputs}

## Boundary

{boundaries}

## Verification

- tests: `{verification['agent_tuning_tests']['status']}` / `{verification['agent_tuning_tests']['summary']}`
- git diff check: `{verification['git_diff_check']['status']}`
- hygiene scan: `{verification['hygiene_scan']['status']}` / hits: `{verification['hygiene_scan']['hits']}`
"""


def failure_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        label = str(row.get("failure_label") or "")
        if label:
            counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def preflight_report(payload: dict[str, Any]) -> str:
    table = markdown_table(
        [
            {
                "task": row["task_id"],
                "time": row["task_time"][:10],
                "family": row["module_family"],
                "status": row["terminal_status"],
                "label": row.get("failure_label", ""),
                "profile": row.get("winning_profile_id", ""),
                "seconds": round(float(row.get("verifier_duration_seconds") or row.get("duration_seconds") or 0.0), 3),
            }
            for row in payload["results"]
        ],
        [("Task", "task"), ("Date", "time"), ("Family", "family"), ("Status", "status"), ("Label", "label"), ("Profile", "profile"), ("Seconds", "seconds")],
    )
    return f"""# Sphinx version-aware verifier preflight

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

小样本 replay preflight 为 `{payload['pass_count']}/{payload['sample_size']}` 通过。该结果只回答 version-aware verifier 是否能工作，不是完整 certification wave。

## Verifier pinning policy

{payload['version_aware_policy']}

Profile 尝试边界：{payload['profiles_tried_policy']}。

## Preflight 结果

{table}

Dominant failure labels: `{payload['dominant_failure_labels']}`。

## 边界

本步骤只提交 sanitized command metadata、duration、subgate label 和输出尾部 hash；未提交 raw stdout/stderr、worktree、prompt、completion 或 transcript。
"""


def run_setup_smoke() -> dict[str, Any]:
    profile = read_json(CONFIG)
    repo = repo_path(profile["ignored_local_checkout_path"])
    env_profile = current_profile(profile)
    rows: list[dict[str, Any]] = []
    for smoke in profile["visible_smoke_commands"]:
        paths = [str(path) for path in smoke["paths"]]
        missing = [path for path in paths if not (repo / path).exists()]
        if missing:
            rows.append(
                {
                    "label": smoke["label"],
                    "paths": paths,
                    "status": "not_run_missing_paths",
                    "missing_paths": missing,
                    "profile_id": env_profile["profile_id"],
                }
            )
            continue
        command = uv_pytest_command(env_profile, paths)
        result = run_command(command, repo, timeout=240)
        rows.append(
            {
                "command_shape": command_shape(command),
                "duration_seconds": result.duration_seconds,
                "label": smoke["label"],
                "path_count": len(paths),
                "profile_id": env_profile["profile_id"],
                "returncode": result.returncode,
                "status": "passed" if result.returncode == 0 else "failed",
                "stderr_line_count": len(result.stderr.splitlines()),
                "stderr_tail_hash": digest_text(result.stderr[-1000:]),
                "stdout_line_count": len(result.stdout.splitlines()),
                "stdout_tail_hash": digest_text(result.stdout[-1000:]),
                "timed_out": result.timed_out,
            }
        )
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.setup_smoke.v1",
        "generated_at": iso_now(),
        "paid_agent_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "repo_id": profile["repo_id"],
        "repo_url": profile["repo_url"],
        "local_checkout": repo_rel(repo),
        "head_commit": git_stdout(repo, ["rev-parse", "HEAD"]),
        "head_time": git_stdout(repo, ["log", "-1", "--format=%cI"]),
        "head_subject": git_stdout(repo, ["log", "-1", "--format=%s"]),
        "profile_id": env_profile["profile_id"],
        "smoke_results": rows,
        "smoke_count": len(rows),
        "smoke_pass_count": sum(1 for row in rows if row.get("status") == "passed"),
        "targeted_verifier_time_class": classify_speed(rows),
        "raw_output_committed": False,
    }
    write_json(RESULTS / "sphinx_setup_smoke.json", payload)
    write_text(REPORTS / "sphinx_setup_smoke_zh.md", setup_smoke_report(payload))
    return payload


def setup_smoke_report(payload: dict[str, Any]) -> str:
    rows = payload["smoke_results"]
    table = markdown_table(
        [
            {
                "label": row.get("label"),
                "status": row.get("status"),
                "duration": row.get("duration_seconds", ""),
                "returncode": row.get("returncode", ""),
                "profile": row.get("profile_id", ""),
            }
            for row in rows
        ],
        [("Shard", "label"), ("Status", "status"), ("Seconds", "duration"), ("RC", "returncode"), ("Profile", "profile")],
    )
    head_subject = str(payload["head_subject"]).replace("`", "'")
    return f"""# Sphinx target profile and setup smoke

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

当前 Sphinx checkout 的小型 targeted smoke 为 `{payload['smoke_pass_count']}/{payload['smoke_count']}` 通过，targeted verifier 时间等级为 `{payload['targeted_verifier_time_class']}`。

## Checkout

- repo: `{payload['repo_id']}`
- path: `{payload['local_checkout']}`
- HEAD: `{payload['head_commit'][:12]}` / `{payload['head_time']}`
- subject: `{head_subject}`

## Smoke 结果

{table}

## 记录边界

命令记录只保留 command shape、duration、return code、行数和尾部 hash；未提交 raw stdout/stderr、solver workspace、verifier workspace、prompt、completion 或 transcript。
"""


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    lines = ["| " + " | ".join(label for label, _key in columns) + " |", "| " + " | ".join("---" for _label, _key in columns) + " |"]
    for row in rows:
        values = [str(row.get(key, "")).replace("|", "\\|") for _label, key in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "setup-smoke",
            "replay-preflight",
            "candidate-inventory",
            "certification-wave",
            "rolling-policy",
            "rolling-protocol-v2",
            "certification-expanded-manifest",
            "window-manifest",
            "paid-cell-accounting",
            "closeout",
        ],
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--preferred-threshold", type=int, default=100)
    parser.add_argument("--minimum-threshold", type=int, default=80)
    parser.add_argument("--agent-tests-status", default="not_run")
    parser.add_argument("--agent-tests-summary", default="")
    parser.add_argument("--git-diff-check-status", default="not_run")
    parser.add_argument("--hygiene-scan-status", default="not_run")
    parser.add_argument("--hygiene-scan-hit", action="append", default=[])
    args = parser.parse_args()
    if args.command == "setup-smoke":
        payload = run_setup_smoke()
        print(json.dumps({"status": payload["targeted_verifier_time_class"], "pass_count": payload["smoke_pass_count"]}, sort_keys=True))
    elif args.command == "replay-preflight":
        payload = run_replay_preflight(limit=args.limit or 5)
        print(json.dumps({"pass_count": payload["pass_count"], "sample_size": payload["sample_size"]}, sort_keys=True))
    elif args.command == "candidate-inventory":
        payload = run_candidate_inventory(limit=args.limit or 180)
        print(json.dumps({"candidate_count": payload["candidate_count"]}, sort_keys=True))
    elif args.command == "certification-wave":
        payload = run_certification_wave(limit=args.limit or 24)
        print(json.dumps({"pass_count": payload["pass_count"], "sample_size": payload["sample_size"]}, sort_keys=True))
    elif args.command == "rolling-policy":
        payload = run_rolling_origin_policy()
        print(json.dumps({"window_count": payload["primary_policy"]["window_count"]}, sort_keys=True))
    elif args.command == "rolling-protocol-v2":
        payload = run_rolling_origin_protocol_v2()
        print(json.dumps({"schema_version": payload["schema_version"]}, sort_keys=True))
    elif args.command == "certification-expanded-manifest":
        payload = run_certification_expanded_manifest(
            preferred_threshold=args.preferred_threshold,
            minimum_threshold=args.minimum_threshold,
        )
        print(json.dumps({"certified_task_count": payload["certified_task_count"], "threshold_state": payload["threshold_state"]}, sort_keys=True))
    elif args.command == "window-manifest":
        payload = run_rolling_origin_window_manifest()
        print(json.dumps({"window_count": payload["window_count"], "state": payload["window_threshold_state"]}, sort_keys=True))
    elif args.command == "paid-cell-accounting":
        payload = run_paid_cell_accounting()
        print(json.dumps({"total_naive_baseline_discovery_cells": payload["total_naive_baseline_discovery_cells"]}, sort_keys=True))
    elif args.command == "closeout":
        payload = run_closeout(
            agent_tests_status=args.agent_tests_status,
            agent_tests_summary=args.agent_tests_summary,
            git_diff_check_status=args.git_diff_check_status,
            hygiene_scan_status=args.hygiene_scan_status,
            hygiene_scan_hits=args.hygiene_scan_hit,
        )
        print(json.dumps({"terminal_state": payload["terminal_state"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
