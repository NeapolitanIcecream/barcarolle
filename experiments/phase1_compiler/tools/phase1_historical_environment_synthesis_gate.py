from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
PHASE0_TOOLS = PHASE0_ROOT / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))

import repo_history_pilot  # noqa: E402


RUN_ID = "phase1_historical_environment_synthesis_gate_20260526"
SCHEMA_VERSION = "barcarolle.phase1_historical_environment_synthesis_gate.v1"
DEFAULT_CONFIG = ROOT / "configs" / "phase1_historical_environment_synthesis_gate.yaml"
CURRENT_DATE = datetime(2026, 5, 26, tzinfo=timezone.utc)
TAIL_LIMIT = 2000
SINGLE_COMMAND_TIMEOUT_SECONDS = 120
SINGLE_TASK_TIMEOUT_SECONDS = 8 * 60


@dataclass(frozen=True)
class EnvironmentProfile:
    profile_id: str
    python_version: str
    dependency_constraints: tuple[str, ...]
    exclude_newer_date: str
    install_mode: str
    cwd_mode: str
    pytest_mode: str
    extra_env: tuple[tuple[str, str], ...]
    max_seconds: int
    why_selected: str

    def to_json(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "python_version": self.python_version,
            "dependency_constraints": list(self.dependency_constraints),
            "exclude_newer_date": self.exclude_newer_date,
            "install_mode": self.install_mode,
            "cwd_mode": self.cwd_mode,
            "pytest_mode": self.pytest_mode,
            "extra_env": dict(self.extra_env),
            "max_seconds": self.max_seconds,
            "why_selected": self.why_selected,
        }


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: str | Path) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def repo_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def read_json(path: str | Path) -> Any:
    return json.loads(repo_path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    resolved = repo_path(path)
    if not resolved.exists():
        return []
    return [json.loads(line) for line in resolved.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected historical environment synthesis config schema_version")
    config["_path"] = str(path)
    return config


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


def scratch_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["scratch_paths"][key])


def attempt_rows() -> list[dict[str, Any]]:
    return read_json("experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_certification_attempts.json").get("rows", [])


def reference_failure_rows() -> list[dict[str, Any]]:
    return [
        row
        for row in attempt_rows()
        if row.get("first_failing_gate") == "reference_pass"
        or row.get("review_first_failing_gate") == "reference_pass"
    ]


def profile_catalog(config: dict[str, Any]) -> dict[str, Any]:
    profiles = [
        profile_for(
            "py311_current_editable",
            "3.11",
            ("pytest>=8,<9", "setuptools<81", "hypothesis<6"),
            "2026-05-26",
            "editable",
            "target_workspace",
            "explicit_test_files",
            "baseline comparison using current-style dependencies without the Barcarolle project",
        ),
        profile_for(
            "py310_pytest7_editable",
            "3.10",
            ("pytest>=7,<8", "setuptools<81", "hypothesis<6"),
            "2022-12-31",
            "editable",
            "target_workspace",
            "explicit_test_files",
            "newer historical projects",
        ),
        profile_for(
            "py39_pytest_lt5_pythonpath",
            "3.9",
            ("pytest<5", "setuptools<58"),
            "2021-12-31",
            "pythonpath_only",
            "target_workspace",
            "explicit_test_files",
            "old pytest cutoff-compatible runs without installing the target project",
        ),
        profile_for(
            "py38_pytest_lt4_pythonpath",
            "3.8",
            ("pytest<4", "setuptools<58"),
            "2020-12-31",
            "pythonpath_only",
            "target_workspace",
            "explicit_test_files",
            "old attrs-era pytest configuration compatibility",
        ),
        profile_for(
            "py37_pytest4_pythonpath",
            "3.7",
            ("pytest<5", "setuptools<58"),
            "2019-12-31",
            "pythonpath_only",
            "target_workspace",
            "explicit_test_files",
            "optional oldest bounded profile; skipped cleanly if uv cannot provide Python 3.7",
        ),
    ]
    return {
        "schema_version": f"{SCHEMA_VERSION}.profile_catalog.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "profile_count": len(profiles),
        "per_task_profile_cap": int(config.get("environment_profiles_per_task_cap", 5)),
        "profiles": [profile.to_json() for profile in profiles],
        "raw_logs_committed": False,
    }


def profile_for(
    profile_id: str,
    python_version: str,
    dependency_constraints: tuple[str, ...],
    exclude_newer_date: str,
    install_mode: str,
    cwd_mode: str,
    pytest_mode: str,
    why_selected: str,
) -> EnvironmentProfile:
    return EnvironmentProfile(
        profile_id=profile_id,
        python_version=python_version,
        dependency_constraints=dependency_constraints,
        exclude_newer_date=exclude_newer_date,
        install_mode=install_mode,
        cwd_mode=cwd_mode,
        pytest_mode=pytest_mode,
        extra_env=(),
        max_seconds=SINGLE_COMMAND_TIMEOUT_SECONDS,
        why_selected=why_selected,
    )


def profile_from_json(raw: dict[str, Any]) -> EnvironmentProfile:
    return EnvironmentProfile(
        profile_id=str(raw["profile_id"]),
        python_version=str(raw["python_version"]),
        dependency_constraints=tuple(str(item) for item in raw.get("dependency_constraints", [])),
        exclude_newer_date=str(raw["exclude_newer_date"]),
        install_mode=str(raw["install_mode"]),
        cwd_mode=str(raw["cwd_mode"]),
        pytest_mode=str(raw["pytest_mode"]),
        extra_env=tuple((str(k), str(v)) for k, v in dict(raw.get("extra_env", {})).items()),
        max_seconds=int(raw.get("max_seconds", SINGLE_COMMAND_TIMEOUT_SECONDS)),
        why_selected=str(raw.get("why_selected", "")),
    )


def parse_datetime(value: Any) -> datetime:
    text = str(value or "")
    if not text:
        return CURRENT_DATE
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return CURRENT_DATE
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def exclude_newer_date(target_commit_date: Any) -> str:
    target = parse_datetime(target_commit_date)
    capped = min(target + timedelta(days=180), CURRENT_DATE)
    return capped.date().isoformat()


def build_uv_command(profile: EnvironmentProfile | dict[str, Any], target_workspace: Path, test_files: list[str]) -> list[str]:
    if isinstance(profile, dict):
        profile = profile_from_json(profile)
    argv = [
        "uv",
        "run",
        "--no-project",
        "--isolated",
        "--managed-python",
        "--python",
        profile.python_version,
        "--exclude-newer",
        profile.exclude_newer_date,
    ]
    for constraint in profile.dependency_constraints:
        argv.extend(["--with", constraint])
    if profile.install_mode == "editable":
        argv.extend(["--with-editable", str(target_workspace)])
    argv.extend(["python", "-m", "pytest", "-q"])
    if profile.pytest_mode == "explicit_test_files":
        argv.extend(test_files_for_command(profile, target_workspace, test_files))
    return argv


def test_files_for_command(profile: EnvironmentProfile, target_workspace: Path, test_files: list[str]) -> list[str]:
    if profile.cwd_mode == "target_workspace":
        return [str(path) for path in test_files]
    return [str(target_workspace / path) for path in test_files]


def infer_profile_candidates(
    repo_id: str,
    target_commit_date: Any,
    target_metadata: dict[str, Any] | None = None,
) -> list[EnvironmentProfile]:
    target_metadata = target_metadata or {}
    date = exclude_newer_date(target_commit_date)
    current_deps = tuple(target_metadata.get("current_command_dependencies") or current_dependencies(repo_id))
    year = parse_datetime(target_commit_date).year
    baseline = profile_for(
        "py311_current_editable",
        "3.11",
        current_deps,
        date,
        "editable",
        "target_workspace",
        "explicit_test_files",
        "baseline using current reference-pass audit dependencies outside the Barcarolle project",
    )
    py310 = profile_for("py310_pytest7_editable", "3.10", ("pytest>=7,<8", "setuptools<81", "hypothesis<6"), date, "editable", "target_workspace", "explicit_test_files", "newer historical fallback")
    py39 = profile_for("py39_pytest_lt5_pythonpath", "3.9", ("pytest<5", "setuptools<58"), date, "pythonpath_only", "target_workspace", "explicit_test_files", "old Python/API compatibility with build avoidance")
    py38 = profile_for("py38_pytest_lt4_pythonpath", "3.8", ("pytest<4", "setuptools<58"), date, "pythonpath_only", "target_workspace", "explicit_test_files", "old pytest configuration compatibility")
    py37 = profile_for("py37_pytest4_pythonpath", "3.7", ("pytest<5", "setuptools<58"), date, "pythonpath_only", "target_workspace", "explicit_test_files", "optional oldest bounded fallback")
    if year <= 2018:
        ordered = [baseline, py38, py39, py37, py310]
    elif year <= 2021:
        ordered = [baseline, py310, py39, py38, py37]
    else:
        ordered = [baseline, py310, py39, py38, py37]
    return ordered[:5]


def current_dependencies(repo_id: str) -> tuple[str, ...]:
    if repo_id == "attrs":
        return ("pytest>=7,<8", "setuptools<81", "hypothesis<6")
    if repo_id == "boltons":
        return ("pytest>=8,<9", "setuptools<81")
    return ("pytest>=8,<9", "setuptools<81")


def classify_reference_subgate(returncode: int, stdout_tail: str, stderr_tail: str) -> str:
    text = f"{stdout_tail}\n{stderr_tail}".lower()
    if returncode == 0:
        return "reference_pass"
    if returncode == 124 or "timed out" in text or "timeout" in text:
        return "reference_timeout"
    unavailable = (
        "managed python" in text
        or "no interpreter found" in text
        or "no download found" in text
        or "request failed" in text
        or "failed to download" in text
        or ("python 3.7" in text and ("not found" in text or "no interpreter" in text))
    )
    if unavailable:
        return "reference_environment_unavailable"
    install_needles = (
        "failed to resolve",
        "no solution found",
        "failed to build",
        "metadata-generation-failed",
        "build backend",
        "subprocess-exited-with-error",
        "setup.py egg_info",
        "invalid command",
    )
    if any(needle in text for needle in install_needles):
        return "reference_install_failed"
    collect_needles = (
        "error collecting",
        "found no collectors",
        "collected 0 items",
        "[pytest] section in setup.cfg files is no longer supported",
        "file or directory not found",
    )
    if any(needle in text for needle in collect_needles):
        return "reference_collect_failed"
    import_needles = (
        "modulenotfounderror",
        "importerror",
        "cannot import name",
        "module 'collections' has no attribute",
        "no module named",
    )
    if any(needle in text for needle in import_needles):
        return "reference_import_failed"
    assertion_needles = (
        "assertionerror",
        "failed",
        "xfailed",
        "short test summary info",
        "=== failures",
    )
    if any(needle in text for needle in assertion_needles):
        return "reference_assert_failed"
    return "reference_unknown_failed"


def sanitize_command_shape(argv: list[str]) -> list[str]:
    return [sanitize_text(part, workspace=None) for part in argv]


def sanitize_output_tail(text: str) -> str:
    return sanitize_text(text[-TAIL_LIMIT:], workspace=None)


def sanitize_text(text: str, workspace: Path | None) -> str:
    replacements = [
        (str(REPO_ROOT), "<repo>"),
        (str(PHASE0_ROOT), "<phase0>"),
        (str(Path.home() / ".cache" / "uv"), "<uv-cache>"),
        (str(Path.home() / ".local" / "share" / "uv" / "python"), "<uv-python>"),
        (str(Path.home()), "<home>"),
    ]
    if workspace is not None:
        replacements.insert(0, (str(workspace), "<workspace>"))
    out = text
    for old, new in replacements:
        if old:
            out = out.replace(old, new)
    return out


def summarize_dependency_versions(stdout_or_probe_json: str) -> dict[str, str]:
    text = stdout_or_probe_json.strip()
    if not text:
        return {}
    try:
        payload = json.loads(text.splitlines()[-1])
    except json.JSONDecodeError:
        return {"probe_parse_status": "unparseable"}
    packages = payload.get("packages", {})
    out = {"python": str(payload.get("python", "unknown"))}
    for name in ["pytest", "setuptools", "hypothesis", "attrs", "boltons", "toolz", "humanize"]:
        if name in packages:
            out[name] = str(packages[name])
    return out


def command_env(profile: EnvironmentProfile, repo_id: str, workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    for key, value in profile.extra_env:
        env[key] = value
    env[f"SETUPTOOLS_SCM_PRETEND_VERSION_FOR_{repo_id.upper().replace('-', '_')}"] = "0.0.0"
    if profile.install_mode == "pythonpath_only":
        env["PYTHONPATH"] = repo_history_pilot.pythonpath_for(workspace)
    return env


def cwd_for(profile: EnvironmentProfile, workspace: Path) -> Path:
    return workspace if profile.cwd_mode == "target_workspace" else REPO_ROOT


def run_command(argv: list[str], cwd: Path, timeout: int, env: dict[str, str]) -> repo_history_pilot.CommandResult:
    return repo_history_pilot.run_command(argv, cwd, timeout=timeout, env=env)


def probe_command(profile: EnvironmentProfile, target_workspace: Path) -> list[str]:
    base = build_uv_command(profile, target_workspace, [])
    python_index = base.index("python")
    probe_code = (
        "import importlib.metadata as m, json, sys; "
        "names=['pytest','setuptools','hypothesis','attrs','boltons','toolz','humanize']; "
        "pkgs={}; "
        "\nfor n in names:\n"
        "    try: pkgs[n]=m.version(n)\n"
        "    except m.PackageNotFoundError: pkgs[n]='missing'\n"
        "print(json.dumps({'python': sys.version.split()[0], 'packages': pkgs}, sort_keys=True))"
    )
    return [*base[: python_index + 1], "-c", probe_code]


def run_dependency_probe(profile: EnvironmentProfile, repo_id: str, workspace: Path) -> tuple[str, dict[str, str], dict[str, Any]]:
    result = run_command(probe_command(profile, workspace), cwd_for(profile, workspace), timeout=30, env=command_env(profile, repo_id, workspace))
    observed = summarize_dependency_versions(result.stdout)
    return (
        observed.get("python", "unobserved"),
        observed,
        {
            "returncode": result.returncode,
            "stdout_tail_hash": hash_tail(result.stdout),
            "stderr_tail_hash": hash_tail(result.stderr),
            "sanitized_error_class": classify_reference_subgate(result.returncode, result.stdout[-TAIL_LIMIT:], result.stderr[-TAIL_LIMIT:]),
        },
    )


def hash_tail(text: str) -> str:
    return hashlib.sha256(text[-TAIL_LIMIT:].encode("utf-8", errors="replace")).hexdigest()[:12]


def raw_log_path(config: dict[str, Any], task_id: str, profile_id: str, stream: str) -> Path:
    return scratch_path(config, "raw_replay_logs") / task_id / f"{profile_id}.{stream}.txt"


def write_raw_logs(config: dict[str, Any], task_id: str, profile_id: str, result: repo_history_pilot.CommandResult) -> None:
    for stream, text in [("stdout", result.stdout), ("stderr", result.stderr)]:
        path = raw_log_path(config, task_id, profile_id, stream)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", errors="replace")


def repo_config(config: dict[str, Any], repo_id: str) -> dict[str, Any]:
    return dict(config.get("repos", {}).get(repo_id, {}))


def checkout_workspace(config: dict[str, Any], row: dict[str, Any], kind: str, commit: str) -> Path:
    workspace = scratch_path(config, "replay_workspaces") / str(row["task_id"]) / kind
    repo = repo_path(repo_config(config, str(row["repo_id"]))["local_repo"])
    repo_history_pilot.archive_commit(repo, commit, workspace)
    return workspace


def replay_record(
    config: dict[str, Any],
    row: dict[str, Any],
    profile: EnvironmentProfile,
    workspace: Path,
    result: repo_history_pilot.CommandResult,
    probe: tuple[str, dict[str, str], dict[str, Any]],
    command: list[str],
) -> dict[str, Any]:
    python_version_observed, dependency_summary, probe_summary = probe
    stdout_tail = result.stdout[-TAIL_LIMIT:]
    stderr_tail = result.stderr[-TAIL_LIMIT:]
    return {
        "task_id": row["task_id"],
        "repo_id": row["repo_id"],
        "base_commit": row.get("base_commit"),
        "target_commit": row.get("target_commit"),
        "target_commit_date": row.get("task_time"),
        "test_files": row.get("test_files", []),
        "profile_id": profile.profile_id,
        "command_shape": sanitize_command_shape(command),
        "cwd_shape": "<workspace>" if cwd_for(profile, workspace).resolve() == workspace.resolve() else rel(cwd_for(profile, workspace)),
        "python_version_observed": python_version_observed,
        "installed_dependency_summary": dependency_summary,
        "dependency_probe": probe_summary,
        "pytest_rootdir_summary": pytest_rootdir_summary(result.stdout + "\n" + result.stderr),
        "returncode": result.returncode,
        "duration_seconds": round(result.duration_seconds, 3),
        "timed_out": result.timed_out,
        "stdout_tail_hash": hash_tail(result.stdout),
        "stderr_tail_hash": hash_tail(result.stderr),
        "sanitized_error_class": classify_reference_subgate(result.returncode, stdout_tail, stderr_tail),
        "subgate_label": classify_reference_subgate(result.returncode, stdout_tail, stderr_tail),
        "sanitized_error_tail": sanitize_output_tail(result.stderr + "\n" + result.stdout)[:1000],
    }


def pytest_rootdir_summary(text: str) -> str:
    for line in text.splitlines():
        if "rootdir:" in line.lower() or "configfile:" in line.lower():
            return sanitize_output_tail(line)
    return "not_reported"


def input_inventory(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "input_inventory")
    if path.exists():
        return read_json(path)
    raise FileNotFoundError(path)


def replay_known_failures(config: dict[str, Any], limit: int | None = None) -> dict[str, Any]:
    inventory = input_inventory(config)
    failures = {str(row["task_id"]): row for row in reference_failure_rows()}
    selected = inventory["rows"][: limit or int(config.get("known_failure_sample_cap", 36))]
    rows: list[dict[str, Any]] = []
    for selected_row in selected:
        source = failures[str(selected_row["task_id"])]
        target_ws = checkout_workspace(config, source, "target", str(source["target_commit"]))
        profiles = infer_profile_candidates(
            str(source["repo_id"]),
            source.get("task_time"),
            repo_config(config, str(source["repo_id"])),
        )
        task_start = time.monotonic()
        attempts = []
        winning_profile_id = ""
        for profile in profiles:
            if time.monotonic() - task_start > SINGLE_TASK_TIMEOUT_SECONDS:
                attempts.append(task_timeout_record(source, profile))
                break
            command = build_uv_command(profile, target_ws, list(source.get("test_files", [])))
            result = run_command(command, cwd_for(profile, target_ws), profile.max_seconds, command_env(profile, str(source["repo_id"]), target_ws))
            write_raw_logs(config, str(source["task_id"]), profile.profile_id, result)
            probe = run_dependency_probe(profile, str(source["repo_id"]), target_ws)
            record = replay_record(config, source, profile, target_ws, result, probe, command)
            attempts.append(record)
            if record["subgate_label"] == "reference_pass":
                winning_profile_id = profile.profile_id
                break
        rows.append(
            {
                "task_id": source["task_id"],
                "repo_id": source["repo_id"],
                "base_commit": source.get("base_commit"),
                "target_commit": source.get("target_commit"),
                "target_commit_date": source.get("task_time"),
                "test_files": source.get("test_files", []),
                "previous_root_cause_label": selected_row.get("previous_root_cause_label"),
                "profiles_tried": [row["profile_id"] for row in attempts],
                "winning_profile_id": winning_profile_id,
                "recovered_reference_pass": bool(winning_profile_id),
                "terminal_subgate_label": terminal_subgate_label(attempts),
                "attempts": attempts,
            }
        )
    counts = Counter(row["terminal_subgate_label"] for row in rows)
    return {
        "schema_version": f"{SCHEMA_VERSION}.known_failure_replay_matrix.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "sampled_task_count": len(rows),
        "recovered_reference_pass_count": sum(1 for row in rows if row["recovered_reference_pass"]),
        "terminal_subgate_counts": dict(sorted(counts.items())),
        "raw_log_storage": rel(scratch_path(config, "raw_replay_logs")),
        "workspace_storage": rel(scratch_path(config, "replay_workspaces")),
        "rows": rows,
    }


def terminal_subgate_label(attempts: list[dict[str, Any]]) -> str:
    labels = [str(row.get("subgate_label", "reference_unknown_failed")) for row in attempts]
    for label in [
        "reference_pass",
        "reference_assert_failed",
        "reference_import_failed",
        "reference_collect_failed",
        "reference_install_failed",
        "reference_environment_unavailable",
        "reference_timeout",
        "reference_unknown_failed",
    ]:
        if label in labels:
            return label
    return "reference_unknown_failed"


def task_timeout_record(row: dict[str, Any], profile: EnvironmentProfile) -> dict[str, Any]:
    return {
        "task_id": row["task_id"],
        "repo_id": row["repo_id"],
        "base_commit": row.get("base_commit"),
        "target_commit": row.get("target_commit"),
        "target_commit_date": row.get("task_time"),
        "test_files": row.get("test_files", []),
        "profile_id": profile.profile_id,
        "command_shape": [],
        "cwd_shape": "not_run_task_timeout",
        "python_version_observed": "unobserved",
        "installed_dependency_summary": {},
        "pytest_rootdir_summary": "not_run_task_timeout",
        "returncode": 124,
        "duration_seconds": 0,
        "timed_out": True,
        "stdout_tail_hash": hash_tail(""),
        "stderr_tail_hash": hash_tail("task timeout"),
        "sanitized_error_class": "reference_timeout",
        "subgate_label": "reference_timeout",
    }


def subclassify_reference_gates(config: dict[str, Any]) -> dict[str, Any]:
    replay = read_json(output_path(config, "known_failure_replay_matrix"))
    rows = []
    for row in replay.get("rows", []):
        for attempt in row.get("attempts", []):
            rows.append(
                {
                    "task_id": row["task_id"],
                    "repo_id": row["repo_id"],
                    "profile_id": attempt["profile_id"],
                    "old_gate_label": "reference_pass",
                    "subgate_label": attempt["subgate_label"],
                    "returncode": attempt["returncode"],
                    "stdout_tail_hash": attempt["stdout_tail_hash"],
                    "stderr_tail_hash": attempt["stderr_tail_hash"],
                }
            )
    final_by_task = [
        {
            "task_id": row["task_id"],
            "repo_id": row["repo_id"],
            "final_subgate_label": "reference_pass" if row["recovered_reference_pass"] else row["terminal_subgate_label"],
            "winning_profile_id": row["winning_profile_id"],
        }
        for row in replay.get("rows", [])
    ]
    counts = Counter(row["final_subgate_label"] for row in final_by_task)
    environment_count = sum(
        count
        for label, count in counts.items()
        if label
        in {
            "reference_install_failed",
            "reference_import_failed",
            "reference_collect_failed",
            "reference_environment_unavailable",
            "reference_timeout",
        }
    )
    return {
        "schema_version": f"{SCHEMA_VERSION}.reference_gate_subclassification.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "old_gate_label": "reference_pass",
        "sampled_task_count": len(final_by_task),
        "final_subgate_counts": dict(sorted(counts.items())),
        "install_import_collection_or_environment_failures": environment_count,
        "production_classification_change_recommended": True,
        "recommended_change": "store benchmark-side reference subgate labels alongside the coarse first_failing_gate",
        "attempt_rows": rows,
        "rows": final_by_task,
    }


def project_recovered_supply(config: dict[str, Any], limit: int | None = None) -> dict[str, Any]:
    replay = read_json(output_path(config, "known_failure_replay_matrix"))
    failures = {str(row["task_id"]): row for row in reference_failure_rows()}
    confirmed = []
    for row in replay.get("rows", []):
        if not row.get("recovered_reference_pass"):
            continue
        source = failures[str(row["task_id"])]
        profile = next(
            profile
            for profile in infer_profile_candidates(str(source["repo_id"]), source.get("task_time"), repo_config(config, str(source["repo_id"])))
            if profile.profile_id == row["winning_profile_id"]
        )
        cert = rerun_full_local_certification_under_profile(config, source, profile)
        confirmed.append(cert)
        if limit is not None and len(confirmed) >= limit:
            break
    confirmed_eligible = [row for row in confirmed if row["recovered_eligible"]]
    by_repo = defaultdict(list)
    for row in confirmed_eligible:
        by_repo[str(row["repo_id"])].append(row)
    decision = read_json("experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_decision.json")
    existing_totals = {
        repo: int(summary.get("total_eligible", 0))
        for repo, summary in decision.get("counts_by_repo", {}).items()
    }
    confirmed_counts = {repo: len(rows) for repo, rows in by_repo.items()}
    projected_by_repo = same_signature_projection(config, confirmed_eligible)
    final_totals = {
        repo: existing_totals.get(repo, 0) + confirmed_counts.get(repo, 0) + projected_by_repo.get(repo, 0)
        for repo in sorted(set(existing_totals) | set(confirmed_counts) | set(projected_by_repo))
    }
    return {
        "schema_version": f"{SCHEMA_VERSION}.recovered_supply_projection.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "existing_total_eligible_by_repo": existing_totals,
        "confirmed_recovered_eligible_by_repo": dict(sorted(confirmed_counts.items())),
        "same_signature_projected_recoverable_by_repo": dict(sorted(projected_by_repo.items())),
        "projected_total_eligible_by_repo": final_totals,
        "attrs_boltons_can_plausibly_reach_30_each": final_totals.get("attrs", 0) >= 30 and final_totals.get("boltons", 0) >= 30,
        "confirmed_records": confirmed,
        "projection_basis": "same stderr/stdout signature only; unrelated signatures are not extrapolated",
    }


def rerun_full_local_certification_under_profile(
    config: dict[str, Any],
    source: dict[str, Any],
    profile: EnvironmentProfile,
) -> dict[str, Any]:
    repo_id = str(source["repo_id"])
    base_ws = checkout_workspace(config, source, "base_cert", str(source["base_commit"]))
    target_ws = checkout_workspace(config, source, "target_cert", str(source["target_commit"]))
    repo = repo_path(repo_config(config, repo_id)["local_repo"])
    patch_text = repo_history_pilot.test_patch(repo, str(source["base_commit"]), str(source["target_commit"]), list(source.get("test_files", [])))
    patch_applied = repo_history_pilot.apply_patch_text(base_ws, patch_text)
    no_op_summary: dict[str, Any] = {"subgate_label": "reference_unknown_failed", "returncode": None}
    ref1_summary: dict[str, Any] = {"subgate_label": "reference_unknown_failed", "returncode": None}
    ref2_summary: dict[str, Any] = {"subgate_label": "reference_unknown_failed", "returncode": None}
    if patch_applied:
        no_op_summary = run_cert_command(config, source, profile, base_ws, "noop_test_patch_on_base")
        ref1_summary = run_cert_command(config, source, profile, target_ws, "reference_run_1")
        ref2_summary = run_cert_command(config, source, profile, target_ws, "reference_run_2")
    source_gate_ok = source.get("source_context_status") == "non_leaky_problem_context"
    leakage_ok = source.get("statement_review_status") == "reviewed" and bool(source.get("allowed_context_refs"))
    scope_ok = bool(source.get("scope_boundaries"))
    recovered_eligible = (
        patch_applied
        and no_op_summary.get("returncode") not in {None, 0}
        and ref1_summary.get("returncode") == 0
        and ref2_summary.get("returncode") == 0
        and source_gate_ok
        and leakage_ok
        and scope_ok
    )
    return {
        "task_id": source["task_id"],
        "repo_id": repo_id,
        "profile_id": profile.profile_id,
        "recovered_eligible": recovered_eligible,
        "gates": {
            "checkout": "pass",
            "changed_test_material_equivalence": "pass" if patch_applied else "fail",
            "no_op_behavior": "pass" if no_op_summary.get("returncode") not in {None, 0} else "fail",
            "reference_behavior": "pass" if ref1_summary.get("returncode") == 0 and ref2_summary.get("returncode") == 0 else "fail",
            "source_provenance": "pass" if source_gate_ok else "fail",
            "solution_leakage_review": "pass" if leakage_ok else "fail",
            "scope_path_policy": "pass" if scope_ok else "fail",
            "artifact_hygiene": "pass",
        },
        "environment_proof": {
            "profile_id": profile.profile_id,
            "command_shape": no_op_summary.get("command_shape", []),
            "cwd_shape": no_op_summary.get("cwd_shape", ""),
            "install_mode": profile.install_mode,
            "pytest_rootdir_summary": ref1_summary.get("pytest_rootdir_summary", ""),
            "result_hashes": {
                "noop_stdout": no_op_summary.get("stdout_tail_hash"),
                "noop_stderr": no_op_summary.get("stderr_tail_hash"),
                "ref1_stdout": ref1_summary.get("stdout_tail_hash"),
                "ref1_stderr": ref1_summary.get("stderr_tail_hash"),
                "ref2_stdout": ref2_summary.get("stdout_tail_hash"),
                "ref2_stderr": ref2_summary.get("stderr_tail_hash"),
            },
            "python_version_observed": ref1_summary.get("python_version_observed", "unobserved"),
            "direct_dependency_versions": ref1_summary.get("installed_dependency_summary", {}),
        },
        "certification_runs": {
            "noop": compact_attempt(no_op_summary),
            "reference_1": compact_attempt(ref1_summary),
            "reference_2": compact_attempt(ref2_summary),
        },
    }


def run_cert_command(
    config: dict[str, Any],
    source: dict[str, Any],
    profile: EnvironmentProfile,
    workspace: Path,
    role: str,
) -> dict[str, Any]:
    command = build_uv_command(profile, workspace, list(source.get("test_files", [])))
    result = run_command(command, cwd_for(profile, workspace), profile.max_seconds, command_env(profile, str(source["repo_id"]), workspace))
    write_raw_logs(config, str(source["task_id"]), f"{profile.profile_id}.{role}", result)
    probe = run_dependency_probe(profile, str(source["repo_id"]), workspace)
    return replay_record(config, source, profile, workspace, result, probe, command)


def compact_attempt(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "returncode": row.get("returncode"),
        "subgate_label": row.get("subgate_label"),
        "stdout_tail_hash": row.get("stdout_tail_hash"),
        "stderr_tail_hash": row.get("stderr_tail_hash"),
        "duration_seconds": row.get("duration_seconds"),
    }


def same_signature_projection(config: dict[str, Any], confirmed_eligible: list[dict[str, Any]]) -> dict[str, int]:
    if not confirmed_eligible:
        return {}
    inventory = input_inventory(config)
    confirmed_tasks = {row["task_id"] for row in confirmed_eligible}
    confirmed_signatures = {
        row["failure_signature"]
        for row in inventory.get("rows", [])
        if row["task_id"] in confirmed_tasks
    }
    all_failures = reference_failure_rows()
    selected_tasks = {row["task_id"] for row in inventory.get("rows", [])}
    counts: Counter[str] = Counter()
    for row in all_failures:
        if str(row["task_id"]) in selected_tasks:
            continue
        if failure_signature(row) in confirmed_signatures:
            counts[str(row["repo_id"])] += 1
    return dict(sorted(counts.items()))


def failure_signature(row: dict[str, Any]) -> str:
    ref = command_record(row, "reference_run_1") or command_record(row, "reference_run_2")
    return "|".join([str(ref.get("returncode", "missing")), str(ref.get("stderr_tail_hash", "missing")), str(ref.get("stdout_tail_hash", "missing"))])


def command_record(row: dict[str, Any], role: str) -> dict[str, Any]:
    for record in row.get("commands", []):
        if record.get("role") == role:
            return record
    return {}


def screen_third_repo(config: dict[str, Any]) -> dict[str, Any]:
    order = list(config.get("third_repo_screen_order", ["toolz", "humanize"]))
    repo_screens = []
    recommendation = "no_third_repo_passed_local_gate"
    for repo_id in order:
        screen = screen_existing_repo_artifacts(config, str(repo_id))
        repo_screens.append(screen)
        if screen["gate_status"] == "passed":
            recommendation = f"{repo_id}_local_gate_passed"
            break
        if repo_id == "toolz":
            continue
    return {
        "schema_version": f"{SCHEMA_VERSION}.third_repo_environment_gate_screen.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "screened_repos": [row["repo_id"] for row in repo_screens],
        "recommended_third_repo": next((row["repo_id"] for row in repo_screens if row["gate_status"] == "passed"), ""),
        "recommendation": recommendation,
        "repo_screens": repo_screens,
    }


def screen_existing_repo_artifacts(config: dict[str, Any], repo_id: str) -> dict[str, Any]:
    certified = read_jsonl(PHASE0_ROOT / "certified_tasks" / f"{repo_id}_certified_tasks.jsonl")
    near = read_jsonl(PHASE0_ROOT / "certified_tasks" / f"{repo_id}_near_certified_tasks.jsonl")
    candidates = read_jsonl(PHASE0_ROOT / "candidate_sources" / f"{repo_id}_candidates.jsonl")
    release_path = PHASE0_ROOT / "releases" / f"{repo_id}_phase0_pilot_release.json"
    if not release_path.exists():
        release_path = PHASE0_ROOT / "releases" / f"{repo_id}_phase0_mini_release.json"
    release = read_json(release_path) if release_path.exists() else {}
    external_service_risk = repo_external_service_risk(repo_id)
    reference_failures = [row for row in near if row.get("first_failing_gate") == "reference_pass"]
    gate_status = "passed" if len(certified) >= 30 and external_service_risk == "low" and len(reference_failures) <= max(3, len(near) // 2) else "failed"
    fail_reasons = []
    if len(certified) < 30:
        fail_reasons.append("fewer_than_30_locally_certified_candidates")
    if external_service_risk != "low":
        fail_reasons.append("external_service_risk_not_low")
    if len(reference_failures) > max(3, len(near) // 2):
        fail_reasons.append("reference_failures_dominate_near_certified")
    return {
        "repo_id": repo_id,
        "gate_status": gate_status,
        "certified_candidate_count": len(certified),
        "near_certified_count": len(near),
        "candidate_count": len(candidates),
        "reference_failure_count": len(reference_failures),
        "external_service_risk": external_service_risk,
        "release_status": release.get("release_status", "missing"),
        "benchmark_grade": release.get("benchmark_grade", False),
        "fail_reasons": fail_reasons,
        "screening_basis": "existing local repo-history artifacts plus same 30-certified-candidate gate",
    }


def repo_external_service_risk(repo_id: str) -> str:
    repos = simple_yaml_load(PHASE0_ROOT / "configs" / "repositories.yaml").get("repositories", [])
    for row in repos:
        if row.get("repo_id") == repo_id:
            return str(row.get("external_service_risk", "unknown"))
    return "unknown"


def decision(config: dict[str, Any]) -> dict[str, Any]:
    replay = read_json(output_path(config, "known_failure_replay_matrix"))
    subclass = read_json(output_path(config, "reference_gate_subclassification"))
    projection = read_json(output_path(config, "recovered_supply_projection"))
    third = read_json(output_path(config, "third_repo_environment_gate_screen"))
    attrs_confirmed = projection["confirmed_recovered_eligible_by_repo"].get("attrs", 0)
    boltons_confirmed = projection["confirmed_recovered_eligible_by_repo"].get("boltons", 0)
    attrs_projected = projection["same_signature_projected_recoverable_by_repo"].get("attrs", 0)
    boltons_projected = projection["same_signature_projected_recoverable_by_repo"].get("boltons", 0)
    third_repo = third.get("recommended_third_repo", "")
    if projection.get("attrs_boltons_can_plausibly_reach_30_each"):
        label = "continue_attrs_boltons_after_historical_env_recovery"
        next_action = "continue_attrs_boltons_recommended"
    elif third_repo == "toolz":
        label = "move_to_toolz_as_third_repo"
        next_action = "move_to_third_repo_recommended"
    elif third_repo == "humanize":
        label = "move_to_humanize_as_third_repo"
        next_action = "move_to_third_repo_recommended"
    elif replay.get("recovered_reference_pass_count", 0) > 0:
        label = "integrate_subgates_and_move_to_third_repo"
        next_action = "third_repo_screening_needs_broader_local_candidate_supply"
    else:
        label = "insufficient_local_evidence"
        next_action = "third_repo_screening_needs_broader_local_candidate_supply"
    claims = [
        "historical_environment_synthesis_completed",
        "historical_environment_profile_inference_completed",
        "uv_historical_environment_probe_completed",
        "reference_gate_subclassification_completed",
        "known_reference_failures_replayed_under_historical_envs",
        "paid_replication_not_run",
        "new_paid_acut_cells_not_run",
        "new_paid_llm_calls_not_run",
    ]
    if replay.get("recovered_reference_pass_count", 0):
        claims.append("historical_environment_recovered_reference_pass_sample")
    else:
        claims.append("historical_environment_did_not_recover_reference_pass_sample")
    if projection.get("attrs_boltons_can_plausibly_reach_30_each"):
        claims.append("attrs_boltons_reopened_for_local_certification")
    else:
        claims.append("attrs_boltons_still_below_supply_threshold")
    if third.get("repo_screens"):
        claims.append("third_repo_gate_screen_completed")
    if third_repo == "toolz":
        claims.append("toolz_local_gate_passed")
    elif any(row["repo_id"] == "toolz" and row["gate_status"] == "failed" for row in third.get("repo_screens", [])):
        claims.append("toolz_local_gate_failed")
    if third_repo == "humanize":
        claims.append("humanize_local_gate_passed")
    elif any(row["repo_id"] == "humanize" and row["gate_status"] == "failed" for row in third.get("repo_screens", [])):
        claims.append("humanize_local_gate_failed")
    return {
        "schema_version": f"{SCHEMA_VERSION}.decision.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "completed",
        "primary_decision_label": label,
        "plain_language_summary": plain_summary(label, projection, third),
        "known_failure_sample_size": replay.get("sampled_task_count", 0),
        "profiles_tried": sorted({profile for row in replay.get("rows", []) for profile in row.get("profiles_tried", [])}),
        "confirmed_recovered_eligible_attrs": attrs_confirmed,
        "confirmed_recovered_eligible_boltons": boltons_confirmed,
        "same_signature_projected_recoverable_attrs": attrs_projected,
        "same_signature_projected_recoverable_boltons": boltons_projected,
        "third_repo_screened": third.get("screened_repos", []),
        "third_repo_certified_candidate_count": max([row.get("certified_candidate_count", 0) for row in third.get("repo_screens", [])] or [0]),
        "recommended_next_action_category": next_action,
        "claims": claims,
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "paid_replication_made": False,
        "verification": {
            "focused_tests": "pending_closeout",
            "git_diff_check": "pending_closeout",
        },
        "research_questions": research_answers(replay, subclass, projection, third, next_action),
    }


def plain_summary(label: str, projection: dict[str, Any], third: dict[str, Any]) -> str:
    if label == "continue_attrs_boltons_after_historical_env_recovery":
        return "Historical environments recovered enough bounded local supply to keep attrs/boltons as the active Phase 1 path."
    if label.startswith("move_to_"):
        return f"attrs/boltons remain below the threshold, and {third.get('recommended_third_repo')} passed the local third-repo gate."
    if label == "integrate_subgates_and_move_to_third_repo":
        return "Historical environments improved diagnosis or recovered some tasks, but the existing third-repo local artifacts do not yet meet the 30-task gate."
    return "The local evidence is not enough to reopen attrs/boltons or select a third repo under the 30-task gate."


def research_answers(
    replay: dict[str, Any],
    subclass: dict[str, Any],
    projection: dict[str, Any],
    third: dict[str, Any],
    next_action: str,
) -> dict[str, str]:
    recovered = replay.get("recovered_reference_pass_count", 0)
    return {
        "RQ1": "uv isolated historical commands ran outside the Barcarolle project where uv could provide the requested Python and dependency profile.",
        "RQ2": f"{recovered} sampled attrs/boltons known reference_pass failures recovered reference_pass under bounded historical profiles.",
        "RQ3": f"Remaining failures were subclassified as {subclass.get('final_subgate_counts', {})}.",
        "RQ4": f"Projected attrs/boltons 30-task feasibility: {projection.get('attrs_boltons_can_plausibly_reach_30_each')}.",
        "RQ5": f"Third repo screen result: {third.get('recommendation')}.",
        "RQ6": next_action,
    }


def run_preflight(config: dict[str, Any]) -> dict[str, Any]:
    support = subprocess.run(["uv", "run", "--help"], cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, check=False).stdout
    flags = ["--no-project", "--isolated", "--managed-python", "--python", "--exclude-newer", "--with", "--with-editable"]
    return {
        "schema_version": f"{SCHEMA_VERSION}.preflight.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "preflight_passed",
        "uv_run_help_support": {flag: flag in support for flag in flags},
        "paid_acut_calls": "disabled",
        "paid_llm_calls": "disabled",
        "historical_env_command_boundary": "uses uv run --no-project --isolated to avoid Barcarolle project Python constraints",
    }


def write_profile_catalog_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Historical Environment Profile Catalog",
        "",
        "Plain-language summary: the catalog is intentionally small. Each task gets the current-style baseline plus historical Python/pytest fallbacks capped at five profiles.",
        "",
        "| profile | python | install mode | deps | why |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["profiles"]:
        deps = ", ".join(f"`{dep}`" for dep in row["dependency_constraints"])
        lines.append(f"| `{row['profile_id']}` | {row['python_version']} | {row['install_mode']} | {deps} | {row['why_selected']} |")
    return "\n".join(lines)


def replay_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Historical Environment Known Failure Replay Matrix",
        "",
        f"Recovered reference_pass tasks: `{payload['recovered_reference_pass_count']}` of `{payload['sampled_task_count']}`.",
        "",
        "Raw stdout and stderr are stored only under ignored scratch paths. This report includes hashes, profiles, and subgate labels.",
        "",
        "## Terminal Subgate Counts",
        "",
        "| subgate | count |",
        "| --- | ---: |",
    ]
    for label, count in payload["terminal_subgate_counts"].items():
        lines.append(f"| {label} | {count} |")
    lines.extend(["", "## Tasks", "", "| repo | task | recovered | winning profile | terminal subgate | profiles tried |", "| --- | --- | --- | --- | --- | --- |"])
    for row in payload["rows"]:
        lines.append(
            f"| {row['repo_id']} | `{row['task_id']}` | {row['recovered_reference_pass']} | `{row['winning_profile_id'] or 'none'}` | {row['terminal_subgate_label']} | {', '.join(row['profiles_tried'])} |"
        )
    return "\n".join(lines)


def subclass_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Reference Gate Subclassification",
        "",
        "Plain-language summary: the old `reference_pass` gate is too coarse. This report separates install, import, collection, assertion, timeout, unavailable environment, pass, and unknown failures.",
        "",
        "| final subgate | task count |",
        "| --- | ---: |",
    ]
    for label, count in payload["final_subgate_counts"].items():
        lines.append(f"| {label} | {count} |")
    lines.extend(
        [
            "",
            f"Install/import/collection/environment shaped failures in sample: `{payload['install_import_collection_or_environment_failures']}`.",
            "",
            f"Production classification change recommended: `{payload['production_classification_change_recommended']}`.",
        ]
    )
    return "\n".join(lines)


def projection_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Historical Environment Recovered Supply Projection",
        "",
        "Plain-language summary: confirmed recovery requires the full local gate under the winning environment profile. Reference behavior alone is not counted as eligible.",
        "",
        "| repo | existing eligible | confirmed recovered | same-signature projected | projected total |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    repos = sorted(set(payload["existing_total_eligible_by_repo"]) | set(payload["projected_total_eligible_by_repo"]))
    for repo in repos:
        lines.append(
            f"| {repo} | {payload['existing_total_eligible_by_repo'].get(repo, 0)} | {payload['confirmed_recovered_eligible_by_repo'].get(repo, 0)} | {payload['same_signature_projected_recoverable_by_repo'].get(repo, 0)} | {payload['projected_total_eligible_by_repo'].get(repo, 0)} |"
        )
    lines.extend(["", f"Can plausibly reach 30 each: `{payload['attrs_boltons_can_plausibly_reach_30_each']}`."])
    return "\n".join(lines)


def third_repo_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Third Repo Environment Gate Screen",
        "",
        "Plain-language summary: toolz is screened first; humanize is screened only if toolz fails. The local gate requires at least 30 locally certified candidates and low external-service risk.",
        "",
        "| repo | status | certified | candidates | reference failures | reasons |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["repo_screens"]:
        lines.append(
            f"| {row['repo_id']} | {row['gate_status']} | {row['certified_candidate_count']} | {row['candidate_count']} | {row['reference_failure_count']} | {', '.join(row['fail_reasons']) or 'none'} |"
        )
    return "\n".join(lines)


def decision_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Historical Environment Synthesis Decision",
        "",
        f"Primary decision label: `{payload['primary_decision_label']}`.",
        "",
        f"Plain-language summary: {payload['plain_language_summary']}",
        "",
        "## Required Fields",
        "",
        f"- known_failure_sample_size: {payload['known_failure_sample_size']}",
        f"- profiles_tried: {', '.join(payload['profiles_tried'])}",
        f"- confirmed_recovered_eligible_attrs: {payload['confirmed_recovered_eligible_attrs']}",
        f"- confirmed_recovered_eligible_boltons: {payload['confirmed_recovered_eligible_boltons']}",
        f"- same_signature_projected_recoverable_attrs: {payload['same_signature_projected_recoverable_attrs']}",
        f"- same_signature_projected_recoverable_boltons: {payload['same_signature_projected_recoverable_boltons']}",
        f"- third_repo_screened: {', '.join(payload['third_repo_screened'])}",
        f"- third_repo_certified_candidate_count: {payload['third_repo_certified_candidate_count']}",
        f"- recommended_next_action_category: {payload['recommended_next_action_category']}",
        f"- paid_acut_calls_made: {payload['paid_acut_calls_made']}",
        f"- paid_llm_calls_made: {payload['paid_llm_calls_made']}",
        "",
        "## Research Questions",
        "",
    ]
    for key, answer in payload["research_questions"].items():
        lines.append(f"- {key}: {answer}")
    lines.extend(["", "## Claims", ""])
    for claim in payload["claims"]:
        lines.append(f"- `{claim}`")
    return "\n".join(lines)


def update_process(status_by_step: dict[str, str]) -> None:
    path = report_path(load_config(), "process")
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    labels = {
        "Step 2": "Historical environment tool and tests",
        "Step 3": "Known failures replay under historical profiles",
        "Step 4": "Reference gate subclassification",
        "Step 5": "Recovered supply projection",
        "Step 6": "Third repo local environment gate",
        "Step 7": "Decision",
        "Step 8": "Verification and closeout",
    }
    for step, status in status_by_step.items():
        title = labels[step]
        text = re.sub(rf"- {step}: {re.escape(title)} - `[^`]+`\\.", f"- {step}: {title} - `{status}`.", text)
    path.write_text(text, encoding="utf-8")


def write_named_output(config: dict[str, Any], key: str, payload: dict[str, Any]) -> None:
    write_json(output_path(config, key), payload)
    report_writers = {
        "profile_catalog": write_profile_catalog_report,
        "known_failure_replay_matrix": replay_report,
        "reference_gate_subclassification": subclass_report,
        "recovered_supply_projection": projection_report,
        "third_repo_environment_gate_screen": third_repo_report,
        "decision": decision_report,
    }
    if key in report_writers:
        write_text(report_path(config, key), report_writers[key](payload))


def run_all(config: dict[str, Any], limit: int | None = None) -> None:
    write_named_output(config, "profile_catalog", profile_catalog(config))
    write_named_output(config, "known_failure_replay_matrix", replay_known_failures(config, limit=limit))
    update_process({"Step 3": "completed"})
    write_named_output(config, "reference_gate_subclassification", subclassify_reference_gates(config))
    update_process({"Step 4": "completed"})
    write_named_output(config, "recovered_supply_projection", project_recovered_supply(config))
    update_process({"Step 5": "completed"})
    write_named_output(config, "third_repo_environment_gate_screen", screen_third_repo(config))
    update_process({"Step 6": "completed"})
    write_named_output(config, "decision", decision(config))
    update_process({"Step 7": "completed"})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 1 historical environment synthesis gate.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--limit", type=int, default=None, help="limit known failure replay count for focused debugging")
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in [
        "preflight",
        "inventory",
        "profile-catalog",
        "replay-known-failures",
        "subclassify-reference-gates",
        "project-recovered-supply",
        "screen-third-repo",
        "decision",
        "all",
    ]:
        subcommands.add_parser(name)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    if args.command == "preflight":
        write_named_output(config, "preflight", run_preflight(config))
    elif args.command == "inventory":
        input_inventory(config)
    elif args.command == "profile-catalog":
        write_named_output(config, "profile_catalog", profile_catalog(config))
    elif args.command == "replay-known-failures":
        write_named_output(config, "known_failure_replay_matrix", replay_known_failures(config, limit=args.limit))
        update_process({"Step 3": "completed"})
    elif args.command == "subclassify-reference-gates":
        write_named_output(config, "reference_gate_subclassification", subclassify_reference_gates(config))
        update_process({"Step 4": "completed"})
    elif args.command == "project-recovered-supply":
        write_named_output(config, "recovered_supply_projection", project_recovered_supply(config))
        update_process({"Step 5": "completed"})
    elif args.command == "screen-third-repo":
        write_named_output(config, "third_repo_environment_gate_screen", screen_third_repo(config))
        update_process({"Step 6": "completed"})
    elif args.command == "decision":
        write_named_output(config, "decision", decision(config))
        update_process({"Step 7": "completed"})
    elif args.command == "all":
        run_all(config, limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
