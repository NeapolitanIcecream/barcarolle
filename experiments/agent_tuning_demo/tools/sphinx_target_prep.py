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
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "experiments" / "agent_tuning_demo" / "config" / "sphinx_target_profile.json"
RESULTS = ROOT / "experiments" / "agent_tuning_demo" / "results"
REPORTS = ROOT / "experiments" / "agent_tuning_demo" / "reports"

SCHEMA_VERSION = "barcarolle.agent_tuning_demo.sphinx_target_prep.v1"
HISTORY_SCAN_CAP = 5000
SCRATCH = ROOT / "experiments" / "phase0_headroom" / "tmp" / "sphinx_target_prep"
CURRENT_DATE = datetime(2026, 6, 17, tzinfo=timezone.utc)


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
    parser.add_argument("command", choices=["setup-smoke", "replay-preflight"])
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    if args.command == "setup-smoke":
        payload = run_setup_smoke()
        print(json.dumps({"status": payload["targeted_verifier_time_class"], "pass_count": payload["smoke_pass_count"]}, sort_keys=True))
    elif args.command == "replay-preflight":
        payload = run_replay_preflight(limit=args.limit)
        print(json.dumps({"pass_count": payload["pass_count"], "sample_size": payload["sample_size"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
