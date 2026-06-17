from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "experiments" / "agent_tuning_demo" / "config" / "sphinx_target_profile.json"
RESULTS = ROOT / "experiments" / "agent_tuning_demo" / "results"
REPORTS = ROOT / "experiments" / "agent_tuning_demo" / "reports"

SCHEMA_VERSION = "barcarolle.agent_tuning_demo.sphinx_target_prep.v1"


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


def current_profile(profile: dict[str, Any]) -> dict[str, Any]:
    return dict(profile["dependency_setup_policy"]["current_smoke_profile"])


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
    parser.add_argument("command", choices=["setup-smoke"])
    args = parser.parse_args()
    if args.command == "setup-smoke":
        payload = run_setup_smoke()
        print(json.dumps({"status": payload["targeted_verifier_time_class"], "pass_count": payload["smoke_pass_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
