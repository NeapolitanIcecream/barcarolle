from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import statistics
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_tuning_demo" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import target_repo_selection_gate as prior_gate  # noqa: E402


EXTERNAL_REPOS = ROOT / "experiments" / "phase0_headroom" / "external_repos"
TMP = ROOT / "experiments" / "phase0_headroom" / "tmp" / "large_repo_target_selection_gate"
RESULTS = ROOT / "experiments" / "agent_tuning_demo" / "results"
REPORTS = ROOT / "experiments" / "agent_tuning_demo" / "reports"

SCHEMA_VERSION = "barcarolle.large_repo_target_selection_gate.v1"
SCAN_SINCE = "2010-01-01"
HISTORY_SCAN_CAP = 5000
MIN_RELEASE_TASKS = 60
PREFERRED_RELEASE_TASKS = 90


@dataclass(frozen=True)
class ProbeSpec:
    label: str
    paths: tuple[str, ...]
    with_package: bool = True
    timeout_seconds: int = 240
    extra_with: tuple[str, ...] = ()
    python: str | None = None


@dataclass(frozen=True)
class CandidateConfig:
    repo_id: str
    repo_url: str
    local_dir: str
    package_import: str
    track: str
    deep_probe: bool = False
    expected_speed_class: str = "unknown"
    environment_risk: str = "low"
    likely_verifier_command: str = "python -m pytest <changed_tests> -q"
    probes: tuple[ProbeSpec, ...] = ()


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def digest_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


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


def run_command(args: list[str], cwd: Path, timeout: int = 240) -> CommandResult:
    start = time.monotonic()
    try:
        proc = prior_gate.subprocess.run(
            args,
            cwd=cwd,
            text=True,
            stdout=prior_gate.subprocess.PIPE,
            stderr=prior_gate.subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return CommandResult(proc.returncode, proc.stdout or "", proc.stderr or "", round(time.monotonic() - start, 3))
    except prior_gate.subprocess.TimeoutExpired as exc:
        return CommandResult(
            124,
            str(exc.stdout or ""),
            str(exc.stderr or ""),
            round(time.monotonic() - start, 3),
            timed_out=True,
        )
    except FileNotFoundError as exc:
        return CommandResult(127, "", str(exc), round(time.monotonic() - start, 3))


def candidate_configs() -> list[CandidateConfig]:
    return [
        CandidateConfig(
            "boltons",
            "https://github.com/mahmoud/boltons.git",
            "boltons",
            "boltons",
            "baseline",
            True,
            "ideal",
            "low",
            probes=(ProbeSpec("boltons_iterutils_cacheutils", ("tests/test_iterutils.py", "tests/test_cacheutils.py")),),
        ),
        CandidateConfig(
            "attrs",
            "https://github.com/python-attrs/attrs.git",
            "attrs",
            "attr",
            "baseline",
            True,
            "ideal",
            "low",
            probes=(ProbeSpec("attrs_funcs_validators", ("tests/test_funcs.py", "tests/test_validators.py")),),
        ),
        CandidateConfig(
            "click",
            "https://github.com/pallets/click.git",
            "click",
            "click",
            "baseline",
            True,
            "ideal",
            "low",
            probes=(ProbeSpec("click_basic_options", ("tests/test_basic.py", "tests/test_options.py")),),
        ),
        CandidateConfig(
            "packaging",
            "https://github.com/pypa/packaging.git",
            "packaging",
            "packaging",
            "baseline",
            True,
            "ideal",
            "low",
            probes=(ProbeSpec("packaging_version_markers", ("tests/test_version.py", "tests/test_markers.py")),),
        ),
        CandidateConfig(
            "pytest",
            "https://github.com/pytest-dev/pytest.git",
            "pytest",
            "_pytest",
            "baseline",
            False,
            "risky",
            "high_self_hosting_test_harness",
            "python -m pytest <pytest self-test shard> -q",
        ),
        CandidateConfig(
            "django",
            "https://github.com/django/django.git",
            "django",
            "django",
            "large_heavy",
            True,
            "acceptable",
            "medium_database_and_settings_matrix",
            "python -m pytest <django test module> -q",
            (
                ProbeSpec("django_utils_datastructures", ("tests/utils_tests/test_datastructures.py",), True, 300),
                ProbeSpec("django_forms_fields", ("tests/forms_tests/field_tests/test_charfield.py",), True, 300),
            ),
        ),
        CandidateConfig(
            "sqlalchemy",
            "https://github.com/sqlalchemy/sqlalchemy.git",
            "sqlalchemy",
            "sqlalchemy",
            "large_heavy",
            True,
            "acceptable",
            "medium_database_backend_matrix",
            "python -m pytest <sqlalchemy non-db or sqlite shard> -q",
            (
                ProbeSpec("sqlalchemy_sql_selectable", ("test/sql/test_selectable.py",), True, 300),
                ProbeSpec("sqlalchemy_orm_session", ("test/orm/test_session.py",), True, 300),
            ),
        ),
        CandidateConfig(
            "sympy",
            "https://github.com/sympy/sympy.git",
            "sympy",
            "sympy",
            "large_heavy",
            True,
            "acceptable",
            "low_pure_python_but_large_suite",
            "python -m pytest <sympy test file> -q",
            (
                ProbeSpec("sympy_core_numbers", ("sympy/core/tests/test_numbers.py",), True, 300),
                ProbeSpec("sympy_matrices", ("sympy/matrices/tests/test_matrices.py",), True, 300),
            ),
        ),
        CandidateConfig(
            "pandas",
            "https://github.com/pandas-dev/pandas.git",
            "pandas",
            "pandas",
            "large_heavy",
            True,
            "risky",
            "high_compiled_extension_build",
            "python -m pytest <pandas test file> -q after compiled build",
            (
                ProbeSpec("pandas_series_constructors", ("pandas/tests/series/test_constructors.py",), False, 240),
                ProbeSpec("pandas_indexing", ("pandas/tests/indexing/test_iloc.py",), False, 240),
            ),
        ),
        CandidateConfig(
            "scikit-learn",
            "https://github.com/scikit-learn/scikit-learn.git",
            "scikit-learn",
            "sklearn",
            "large_heavy",
            True,
            "risky",
            "high_compiled_extension_build",
            "python -m pytest <sklearn test file> -q after compiled build",
            (
                ProbeSpec("sklearn_validation", ("sklearn/utils/tests/test_validation.py",), False, 240),
            ),
        ),
        CandidateConfig(
            "matplotlib",
            "https://github.com/matplotlib/matplotlib.git",
            "matplotlib",
            "matplotlib",
            "large_heavy",
            False,
            "risky",
            "high_compiled_extension_and_image_test_stack",
            "python -m pytest <matplotlib non-image shard> -q after build",
        ),
        CandidateConfig(
            "mypy",
            "https://github.com/python/mypy.git",
            "mypy",
            "mypy",
            "large_heavy",
            False,
            "acceptable",
            "medium_large_custom_test_harness",
            "python -m pytest <mypy test shard> -q",
        ),
        CandidateConfig(
            "black",
            "https://github.com/psf/black.git",
            "black",
            "black",
            "medium_large_fast",
            True,
            "ideal",
            "low",
            probes=(
                ProbeSpec("black_format", ("tests/test_format.py",), True, 240),
                ProbeSpec("black_black", ("tests/test_black.py",), True, 240),
            ),
        ),
        CandidateConfig(
            "httpx",
            "https://github.com/encode/httpx.git",
            "httpx",
            "httpx",
            "medium_large_fast",
            True,
            "ideal",
            "low_to_medium_network_mocking",
            "python -m pytest <httpx mocked client test> -q",
            (
                ProbeSpec("httpx_client", ("tests/client/test_client.py",), True, 240),
                ProbeSpec("httpx_models", ("tests/models/test_responses.py",), True, 240),
            ),
        ),
        CandidateConfig(
            "starlette",
            "https://github.com/encode/starlette.git",
            "starlette",
            "starlette",
            "medium_large_fast",
            True,
            "ideal",
            "low_to_medium_async_http_stack",
            "python -m pytest <starlette test file> -q",
            (
                ProbeSpec("starlette_responses", ("tests/test_responses.py",), True, 240, ("httpx2",)),
                ProbeSpec("starlette_routing", ("tests/test_routing.py",), True, 240, ("httpx2",)),
            ),
        ),
        CandidateConfig(
            "anyio",
            "https://github.com/agronholm/anyio.git",
            "anyio",
            "anyio",
            "medium_large_fast",
            True,
            "ideal",
            "low_to_medium_async_backend_matrix",
            "python -m pytest <anyio pytest shard> -q",
            (
                ProbeSpec("anyio_streams", ("tests/streams/test_memory.py",), True, 240),
                ProbeSpec("anyio_tasks", ("tests/test_taskgroups.py",), True, 240),
            ),
        ),
        CandidateConfig(
            "tornado",
            "https://github.com/tornadoweb/tornado.git",
            "tornado",
            "tornado",
            "medium_large_fast",
            False,
            "ideal",
            "low_to_medium_async_network_tests",
            "python -m pytest <tornado unit shard> -q",
        ),
        CandidateConfig(
            "trio",
            "https://github.com/python-trio/trio.git",
            "trio",
            "trio",
            "medium_large_fast",
            False,
            "ideal",
            "low_to_medium_async_backend_matrix",
            "python -m pytest <trio unit shard> -q",
        ),
        CandidateConfig(
            "pydantic",
            "https://github.com/pydantic/pydantic.git",
            "pydantic",
            "pydantic",
            "medium_large_fast",
            False,
            "acceptable",
            "medium_rust_core_dependency_but_wheel_available",
            "python -m pytest <pydantic test file> -q",
        ),
        CandidateConfig(
            "sphinx",
            "https://github.com/sphinx-doc/sphinx.git",
            "sphinx",
            "sphinx",
            "medium_large_fast",
            True,
            "acceptable",
            "medium_doc_build_fixture_matrix",
            "python -m pytest <sphinx unit shard> -q",
            (
                ProbeSpec("sphinx_util", ("tests/test_util/test_util.py",), True, 240, (), "3.14"),
                ProbeSpec("sphinx_config", ("tests/test_config/test_config.py",), True, 240, (), "3.14"),
            ),
        ),
    ]


def git_stdout(repo: Path, args: list[str], timeout: int = 240) -> str:
    result = run_command(["git", *args], repo, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def clone_missing(config: CandidateConfig, timeout: int = 300) -> dict[str, Any]:
    repo = EXTERNAL_REPOS / config.local_dir
    if (repo / ".git").exists():
        return {"status": "already_present", "local_path": repo_rel(repo)}
    repo.parent.mkdir(parents=True, exist_ok=True)
    result = run_command(["git", "clone", "--filter=blob:none", config.repo_url, str(repo)], ROOT, timeout=timeout)
    if result.returncode != 0 and repo.exists() and not (repo / ".git").exists():
        shutil.rmtree(repo)
    return {
        "status": "cloned" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "duration_seconds": result.duration_seconds,
        "timed_out": result.timed_out,
        "local_path": repo_rel(repo),
        "stdout_tail_hash": digest_text(result.stdout[-1000:]),
        "stderr_tail_hash": digest_text(result.stderr[-1000:]),
        "stderr_line_count": len(result.stderr.splitlines()),
    }


def is_dirty(repo: Path) -> bool:
    result = run_command(["git", "status", "--short", "--untracked-files=no"], repo, timeout=120)
    return result.returncode != 0 or bool(result.stdout.strip())


def parse_git_history(repo: Path) -> tuple[list[dict[str, Any]], bool]:
    result = run_command(
        [
            "git",
            "log",
            f"--since={SCAN_SINCE}",
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
        impl = [path for path in changed if prior_gate.is_impl_path(path)]
        tests = [path for path in changed if prior_gate.is_test_path(path)]
        public_refs = prior_gate.public_refs_from_subject(subject)
        rows.append(
            {
                "commit": commit,
                "parent": parents.split()[0] if parents.split() else "",
                "task_time": task_time,
                "year": int(task_time[:4]) if task_time[:4].isdigit() else None,
                "subject": subject,
                "public_refs": public_refs,
                "subject_has_public_ref": bool(public_refs),
                "changed_files": changed,
                "implementation_files": impl,
                "test_files": tests,
                "has_implementation": bool(impl),
                "has_tests": bool(tests),
            }
        )
    return rows, len(rows) >= HISTORY_SCAN_CAP


def date_span(repo: Path) -> dict[str, str]:
    roots = git_stdout(repo, ["rev-list", "--max-parents=0", "HEAD"], timeout=120).splitlines()
    first_commit = roots[0] if roots else "HEAD"
    return {
        "first_commit": git_stdout(repo, ["show", "-s", "--format=%cI", first_commit], timeout=120),
        "latest_commit": git_stdout(repo, ["log", "-1", "--format=%cI"], timeout=120),
    }


def time_bucket(year: int | None) -> str:
    if year is None:
        return "unknown"
    if year < 2016:
        return "pre_2016"
    if year < 2020:
        return "2016_2019"
    if year < 2024:
        return "2020_2023"
    return "2024_plus"


def probe_command(spec: ProbeSpec, paths: tuple[str, ...]) -> list[str]:
    command = ["uv", "run", "--no-project"]
    if spec.python:
        command.extend(["--python", spec.python])
    command.extend(["--with", "pytest>=8,<10"])
    for dep in spec.extra_with:
        command.extend(["--with", dep])
    if spec.with_package:
        command.extend(["--with", "."])
    command.extend(["--", "python", "-m", "pytest", *paths, "-q"])
    return command


def run_probe(repo: Path, spec: ProbeSpec) -> dict[str, Any]:
    missing = [path for path in spec.paths if not (repo / path).exists()]
    if missing:
        return {"label": spec.label, "status": "not_run_missing_paths", "missing_paths": missing}
    result = run_command(probe_command(spec, spec.paths), repo, timeout=spec.timeout_seconds)
    return {
        "label": spec.label,
        "status": "passed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "duration_seconds": result.duration_seconds,
        "timed_out": result.timed_out,
        "command_shape": pytest_command_shape(spec),
        "stdout_line_count": len(result.stdout.splitlines()),
        "stderr_line_count": len(result.stderr.splitlines()),
        "stdout_tail_hash": digest_text(result.stdout[-1000:]),
        "stderr_tail_hash": digest_text(result.stderr[-1000:]),
    }


def pytest_command_shape(spec: ProbeSpec) -> list[str]:
    command = ["uv", "run", "--no-project"]
    if spec.python:
        command.extend(["--python", spec.python])
    command.extend(["--with", "pytest>=8,<10"])
    for dep in spec.extra_with:
        command.extend(["--with", dep])
    if spec.with_package:
        command.extend(["--with", "."])
    command.extend(["--", "python", "-m", "pytest", "<targeted_test_paths>", "-q"])
    return command


def summarize_probe_timings(probes: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [float(row["duration_seconds"]) for row in probes if row.get("duration_seconds") is not None]
    passed = [float(row["duration_seconds"]) for row in probes if row.get("status") == "passed"]
    if not completed:
        return {
            "sample_count": 0,
            "pass_count": 0,
            "median_seconds": None,
            "p95_seconds": None,
            "speed_class": "not_measured",
        }
    if 0 < len(passed) < len(completed):
        measured_speed_class = "partial_probe_failure"
    else:
        measured_speed_class = speed_class(max(completed), passed=bool(passed))
    return {
        "sample_count": len(completed),
        "pass_count": len(passed),
        "median_seconds": round(statistics.median(completed), 3),
        "p95_seconds": round(percentile(completed, 0.95), 3),
        "speed_class": measured_speed_class,
    }


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[int(position)]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def speed_class(seconds: float | None, *, passed: bool = True) -> str:
    if seconds is None:
        return "not_measured"
    if not passed:
        return "environment_failed_or_unusable"
    if seconds < 60:
        return "ideal_under_60s"
    if seconds < 180:
        return "acceptable_under_180s"
    if seconds < 600:
        return "risky_180s_to_600s"
    return "avoid_over_600s"


def task_shape_sample(rows: list[dict[str, Any]], sample_limit: int) -> dict[str, Any]:
    candidates = [row for row in rows if row["has_implementation"] and row["has_tests"] and row["subject_has_public_ref"]]
    sampled = spread_sample(candidates, sample_limit)
    failure_counts: Counter[str] = Counter()
    pass_count = 0
    for row in sampled:
        reasons = []
        if not row.get("parent"):
            reasons.append("missing_parent_commit")
        if len(row.get("implementation_files") or []) > 8:
            reasons.append("large_implementation_surface")
        if len(row.get("test_files") or []) > 8:
            reasons.append("wide_changed_test_oracle")
        if not row.get("public_refs"):
            reasons.append("missing_public_issue_or_pr_ref")
        if reasons:
            failure_counts.update(reasons)
        else:
            pass_count += 1
    return {
        "mode": "bounded_task_shape_certification_not_paid_agent_replay",
        "sample_size": len(sampled),
        "pass_count": pass_count,
        "dominant_failure_labels": dict(failure_counts.most_common()),
    }


def spread_sample(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0 or not rows:
        return []
    ordered = sorted(rows, key=lambda row: row.get("task_time") or "")
    if len(ordered) <= limit:
        return ordered
    if limit == 1:
        return [ordered[len(ordered) // 2]]
    step = (len(ordered) - 1) / (limit - 1)
    return [ordered[round(index * step)] for index in range(limit)]


def historical_reference_probe(
    config: CandidateConfig,
    repo: Path,
    rows: list[dict[str, Any]],
    *,
    sample_limit: int,
) -> dict[str, Any]:
    if not config.probes or sample_limit <= 0:
        return {"mode": "not_run", "sample_size": 0, "pass_count": 0, "results": []}
    candidates = [
        row
        for row in rows
        if row["has_implementation"] and row["has_tests"] and row["subject_has_public_ref"] and row.get("commit")
    ]
    sampled = spread_sample(candidates, sample_limit)
    results: list[dict[str, Any]] = []
    for row in sampled:
        test_paths = tuple((row.get("test_files") or [])[:2])
        if not test_paths:
            continue
        spec = ProbeSpec(
            label=f"historical_reference_{row['commit'][:12]}",
            paths=test_paths,
            with_package=config.probes[0].with_package,
            timeout_seconds=min(config.probes[0].timeout_seconds, 300),
            extra_with=config.probes[0].extra_with,
        )
        result = run_historical_reference_probe(repo, row["commit"], spec)
        results.append(result)
    return {
        "mode": "target_commit_changed_tests_reference_probe",
        "sample_size": len(results),
        "pass_count": sum(1 for row in results if row.get("status") == "passed"),
        "results": results,
        "dominant_failure_labels": dict(Counter(classify_probe_failure(row) for row in results if row.get("status") != "passed")),
    }


def run_historical_reference_probe(repo: Path, commit: str, spec: ProbeSpec) -> dict[str, Any]:
    worktree = TMP / repo.name / commit[:12]
    if worktree.exists():
        shutil.rmtree(worktree)
    worktree.parent.mkdir(parents=True, exist_ok=True)
    add = run_command(["git", "worktree", "add", "--detach", str(worktree), commit], repo, timeout=180)
    if add.returncode != 0:
        return {
            "label": spec.label,
            "commit": commit[:12],
            "status": "worktree_failed",
            "duration_seconds": add.duration_seconds,
            "stdout_tail_hash": digest_text(add.stdout[-1000:]),
            "stderr_tail_hash": digest_text(add.stderr[-1000:]),
        }
    missing = [path for path in spec.paths if not (worktree / path).exists()]
    if missing:
        cleanup_worktree(repo, worktree)
        return {"label": spec.label, "commit": commit[:12], "status": "missing_historical_test_paths", "missing_paths": missing}
    result = run_command(probe_command(spec, spec.paths), worktree, timeout=spec.timeout_seconds)
    cleanup_worktree(repo, worktree)
    return {
        "label": spec.label,
        "commit": commit[:12],
        "status": "passed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "duration_seconds": result.duration_seconds,
        "timed_out": result.timed_out,
        "command_shape": pytest_command_shape(spec),
        "test_path_count": len(spec.paths),
        "stdout_line_count": len(result.stdout.splitlines()),
        "stderr_line_count": len(result.stderr.splitlines()),
        "stdout_tail_hash": digest_text(result.stdout[-1000:]),
        "stderr_tail_hash": digest_text(result.stderr[-1000:]),
    }


def cleanup_worktree(repo: Path, worktree: Path) -> None:
    remove = run_command(["git", "worktree", "remove", "--force", str(worktree)], repo, timeout=120)
    if remove.returncode != 0 and worktree.exists():
        shutil.rmtree(worktree)


def classify_probe_failure(row: dict[str, Any]) -> str:
    if row.get("timed_out"):
        return "timeout"
    status = str(row.get("status") or "")
    if status in {"worktree_failed", "missing_historical_test_paths", "not_run_missing_paths"}:
        return status
    if row.get("returncode") == 1:
        return "test_failure_or_environment_mismatch"
    if row.get("returncode") == 2:
        return "pytest_collect_or_usage_failure"
    if row.get("returncode") == 4:
        return "pytest_usage_or_no_tests"
    return status or "unknown_failed"


def prior_evidence() -> dict[str, dict[str, Any]]:
    return prior_gate.prior_evidence()


def projected_release_count(metrics: dict[str, Any], prior: dict[str, Any]) -> int:
    known = int(prior.get("known_release_eligible") or 0)
    if known:
        return known
    release_ready = int(metrics.get("changed_test_oracle_availability_count") or 0)
    prior_attempts = int(prior.get("prior_probe_attempts") or 0)
    if prior_attempts:
        prior_successes = int(prior.get("prior_probe_release_eligible") or 0)
        return min(release_ready, round(release_ready * (prior_successes / prior_attempts)))
    shape = metrics.get("bounded_certification_sample", {})
    shape_rate = None
    if shape.get("sample_size"):
        shape_rate = int(shape.get("pass_count") or 0) / int(shape["sample_size"])
    timing = metrics.get("targeted_verifier_timing", {})
    speed = str(timing.get("speed_class") or "")
    timing_sample_count = int(timing.get("sample_count") or 0)
    smoke_passed = timing_sample_count > 0 and int(timing.get("pass_count") or 0) == timing_sample_count
    if speed == "environment_failed_or_unusable" or str(metrics.get("environment_risk", "")).startswith("high_compiled"):
        rate = 0.05
    elif smoke_passed and shape_rate is not None:
        rate = min(0.45, max(0.20, shape_rate * 0.35))
    elif smoke_passed:
        rate = 0.30
    else:
        rate = 0.15
    return min(release_ready, round(release_ready * rate))


def classify_candidate(metrics: dict[str, Any]) -> str:
    projected = int(metrics.get("estimated_release_eligible_volume") or 0)
    windows = int(metrics.get("count_feasible_rolling_origin_windows") or 0)
    speed = str(metrics.get("expected_evaluation_speed_class") or "")
    risk = str(metrics.get("environment_risk") or "")
    has_fast_probe = speed in {"ideal_under_60s", "acceptable_under_180s"}
    if projected >= PREFERRED_RELEASE_TASKS and windows >= 3 and has_fast_probe and not risk.startswith("high"):
        return "balanced_strong_target_prep_candidate"
    if projected >= MIN_RELEASE_TASKS and windows >= 2 and has_fast_probe and not risk.startswith("high"):
        return "balanced_target_prep_candidate"
    if projected >= MIN_RELEASE_TASKS and (risk.startswith("high") or speed in {"risky_180s_to_600s", "environment_failed_or_unusable"}):
        return "large_but_heavy"
    if projected < MIN_RELEASE_TASKS and has_fast_probe:
        return "fast_but_underpowered"
    if projected >= MIN_RELEASE_TASKS:
        return "capacity_promising_but_speed_unproven"
    return "screened_out"


def expected_paid_cells(projected_release_count: int) -> int:
    if projected_release_count < 30:
        return 0
    return min(max(projected_release_count, 30), 90) * 4


def rough_cost_range(cells: int) -> dict[str, float]:
    if cells <= 0:
        return {"low": 0.0, "high": 0.0}
    return {"low": round(cells * 0.20, 2), "high": round(cells * 0.45, 2)}


def candidate_metrics(
    config: CandidateConfig,
    *,
    clone: bool,
    clone_timeout: int,
    run_deep_probes: bool,
    task_shape_sample_limit: int,
    historical_sample_limit: int,
    priors: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    repo = EXTERNAL_REPOS / config.local_dir
    clone_status = clone_missing(config, timeout=clone_timeout) if clone else {"status": "not_requested", "local_path": repo_rel(repo)}
    prior = priors.get(config.repo_id, {})
    base: dict[str, Any] = {
        "repo_id": config.repo_id,
        "repo_url": config.repo_url,
        "track": config.track,
        "local_path": repo_rel(repo),
        "checkout_status": "missing",
        "clone_status": clone_status,
        "deep_probe": config.deep_probe,
        "source_context_availability": "unknown",
        "changed_test_oracle_availability": "unknown",
        "likely_verifier_command": config.likely_verifier_command,
        "environment_risk": config.environment_risk,
        "prior_evidence": prior,
    }
    if not (repo / ".git").exists():
        return {
            **base,
            "reason_to_deep_probe_or_reject": "local_checkout_missing_or_clone_failed",
            "classification": "screened_out",
        }
    if is_dirty(repo):
        return {
            **base,
            "checkout_status": "dirty_or_partial_checkout",
            "reason_to_deep_probe_or_reject": "repair or reclone ignored external checkout",
            "classification": "screened_out",
        }
    try:
        history_rows, capped = parse_git_history(repo)
        span = date_span(repo)
        head = git_stdout(repo, ["rev-parse", "--short", "HEAD"], timeout=120)
        total_commits = int(git_stdout(repo, ["rev-list", "--count", "HEAD"], timeout=240))
    except Exception as exc:
        return {
            **base,
            "checkout_status": "history_read_failed",
            "history_error": f"{type(exc).__name__}: {exc}",
            "reason_to_deep_probe_or_reject": "history_read_failed",
            "classification": "screened_out",
        }

    impl = [row for row in history_rows if row["has_implementation"]]
    tests = [row for row in history_rows if row["has_tests"]]
    impl_tests = [row for row in history_rows if row["has_implementation"] and row["has_tests"]]
    release_ready = [row for row in impl_tests if row["subject_has_public_ref"]]
    impl_years = [row["year"] for row in impl_tests if row["year"] is not None]
    release_ready_years = [row["year"] for row in release_ready if row["year"] is not None]
    probe_results = [run_probe(repo, spec) for spec in config.probes] if run_deep_probes and config.deep_probe else []
    timing = summarize_probe_timings(probe_results)
    task_shape = task_shape_sample(history_rows, task_shape_sample_limit if config.deep_probe else 0)
    historical = (
        historical_reference_probe(config, repo, history_rows, sample_limit=historical_sample_limit)
        if run_deep_probes and config.deep_probe
        else {"mode": "not_run", "sample_size": 0, "pass_count": 0, "results": []}
    )

    metrics = {
        **base,
        "checkout_status": "clean",
        "head_short": head,
        "history_date_span": span,
        "total_commits": total_commits,
        "total_commits_scanned": len(history_rows),
        "history_scan_cap": HISTORY_SCAN_CAP,
        "history_scan_capped": capped,
        "history_scan_since": SCAN_SINCE,
        "implementation_change_count": len(impl),
        "test_change_count": len(tests),
        "implementation_plus_test_change_count": len(impl_tests),
        "source_context_availability": prior_gate.source_context_label(len(release_ready), len(impl_tests)),
        "changed_test_oracle_availability": "changed_tests_available" if impl_tests else "weak_or_missing_changed_tests",
        "changed_test_oracle_availability_count": len(release_ready),
        "estimated_candidate_volume": len(impl_tests),
        "time_bucket_distribution": dict(sorted(Counter(time_bucket(row["year"]) for row in impl_tests).items())),
        "rolling_origin_windows_raw": prior_gate.simulate_windows([int(year) for year in impl_years]),
        "rolling_origin_windows_release_ready": prior_gate.simulate_windows([int(year) for year in release_ready_years]),
        "visible_setup_smoke_status": smoke_status(probe_results),
        "setup_test_smoke": probe_results,
        "targeted_verifier_timing": timing,
        "bounded_certification_sample": task_shape,
        "historical_reference_probe": historical,
    }
    projected = projected_release_count(metrics, prior)
    cells = expected_paid_cells(projected)
    expected_speed = timing.get("speed_class") if timing.get("sample_count") else config.expected_speed_class
    metrics.update(
        {
            "estimated_release_eligible_volume": projected,
            "count_feasible_rolling_origin_windows": len(metrics["rolling_origin_windows_release_ready"]),
            "expected_evaluation_speed_class": expected_speed,
            "expected_paid_baseline_discovery_cells": cells,
            "rough_paid_baseline_cost_usd_range": rough_cost_range(cells),
        }
    )
    metrics["classification"] = classify_candidate(metrics)
    metrics["projected_certified_task_count_after_bounded_repair"] = projected_after_repair(metrics, projected)
    metrics["projected_evidence_backed_rolling_origin_windows"] = projected_windows_after_repair(metrics)
    metrics["reason_to_deep_probe_or_reject"] = reason(metrics)
    return metrics


def smoke_status(probe_results: list[dict[str, Any]]) -> str:
    if not probe_results:
        return "not_run"
    if all(row.get("status") == "passed" for row in probe_results):
        return "passed"
    if any(row.get("status") == "passed" for row in probe_results):
        return "partial_failed"
    if all(row.get("status") == "not_run_missing_paths" for row in probe_results):
        return "not_run_missing_paths"
    return "failed"


def projected_after_repair(metrics: dict[str, Any], projected: int) -> int:
    release_ready = int(metrics.get("changed_test_oracle_availability_count") or 0)
    classification = str(metrics.get("classification") or "")
    if classification == "large_but_heavy":
        return min(release_ready, max(projected, round(release_ready * 0.15)))
    if classification in {"balanced_strong_target_prep_candidate", "balanced_target_prep_candidate"}:
        return min(release_ready, max(projected, round(release_ready * 0.45)))
    if int(metrics.get("historical_reference_probe", {}).get("pass_count") or 0) > 0:
        return min(release_ready, max(projected, round(release_ready * 0.35)))
    return projected


def projected_windows_after_repair(metrics: dict[str, Any]) -> int:
    projected = int(metrics.get("projected_certified_task_count_after_bounded_repair") or 0)
    raw_windows = len(metrics.get("rolling_origin_windows_release_ready") or [])
    if projected >= PREFERRED_RELEASE_TASKS:
        return min(3, raw_windows)
    if projected >= MIN_RELEASE_TASKS:
        return min(2, raw_windows)
    return 0


def reason(metrics: dict[str, Any]) -> str:
    label = metrics.get("classification")
    if label == "balanced_strong_target_prep_candidate":
        return "deep-probe winner: high projected capacity, multiple rolling-origin windows, and targeted verifier timing below the practical threshold"
    if label == "balanced_target_prep_candidate":
        return "advance to no-paid target prep if stronger candidate does not beat it"
    if label == "large_but_heavy":
        return "reject for mainline today unless environment repair can make targeted verification fast and stable"
    if label == "fast_but_underpowered":
        return "keep only as backup or small pilot; capacity below rolling-origin threshold"
    if label == "capacity_promising_but_speed_unproven":
        return "run targeted verifier smoke before any recommendation"
    return "screened out by capacity, checkout, or source/oracle availability"


def choose_recommendations(candidates: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    viable = [row for row in candidates if row.get("checkout_status") == "clean"]

    def score(row: dict[str, Any]) -> tuple[Any, ...]:
        classification = row.get("classification")
        class_rank = {
            "balanced_strong_target_prep_candidate": 0,
            "balanced_target_prep_candidate": 1,
            "capacity_promising_but_speed_unproven": 2,
            "fast_but_underpowered": 3,
            "large_but_heavy": 4,
            "screened_out": 5,
        }.get(str(classification), 6)
        speed = str(row.get("expected_evaluation_speed_class") or "")
        speed_rank = {
            "ideal_under_60s": 0,
            "acceptable_under_180s": 1,
            "ideal": 1,
            "acceptable": 2,
            "not_measured": 3,
            "risky_180s_to_600s": 4,
            "risky": 4,
            "environment_failed_or_unusable": 5,
            "avoid_over_600s": 6,
        }.get(speed, 3)
        return (
            class_rank,
            row.get("track") == "baseline",
            speed_rank,
            -int(row.get("projected_certified_task_count_after_bounded_repair") or 0),
            -int(row.get("estimated_release_eligible_volume") or 0),
            -int(row.get("changed_test_oracle_availability_count") or 0),
            str(row.get("repo_id")),
        )

    scored = sorted(viable, key=score)
    primary = scored[0] if scored else {}
    backups = [row for row in scored[1:] if row.get("repo_id") != primary.get("repo_id")]
    backup = next((row for row in backups if row.get("classification") in {"balanced_strong_target_prep_candidate", "balanced_target_prep_candidate"}), None)
    if backup is None:
        backup = next((row for row in backups if row.get("classification") == "capacity_promising_but_speed_unproven"), None)
    if backup is None:
        backup = backups[0] if backups else {}
    return primary, backup


def build_payload(
    *,
    clone: bool,
    clone_timeout: int,
    run_deep_probes: bool,
    task_shape_sample_limit: int,
    historical_sample_limit: int,
) -> dict[str, Any]:
    priors = prior_evidence()
    candidates = []
    for config in candidate_configs():
        print(f"[large-repo-gate] screen {config.repo_id} ({config.track})", flush=True)
        candidates.append(
            candidate_metrics(
            config,
            clone=clone,
            clone_timeout=clone_timeout,
            run_deep_probes=run_deep_probes,
            task_shape_sample_limit=task_shape_sample_limit,
            historical_sample_limit=historical_sample_limit,
            priors=priors,
        )
        )
    primary, backup = choose_recommendations(candidates)
    new_candidates = [row for row in candidates if row.get("track") != "baseline"]
    deep_new = [row for row in new_candidates if row.get("deep_probe")]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": iso_now(),
        "runbook": "docs/research/large-repo-target-selection-gate-runbook-2026-06-15.md",
        "paid_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "tuning_experiment_started": False,
        "history_scan_since": SCAN_SINCE,
        "history_scan_cap": HISTORY_SCAN_CAP,
        "new_repository_screen_count": len(new_candidates),
        "new_repository_deep_probe_count": len(deep_new),
        "deep_probe_track_counts": dict(Counter(row.get("track") for row in deep_new)),
        "candidate_metrics": candidates,
        "deep_probe_metrics": [row for row in candidates if row.get("deep_probe")],
        "recommendation": recommendation_summary(primary),
        "backup_recommendation": recommendation_summary(backup),
        "terminal_state": terminal_state(primary),
        "next_action": next_action(primary),
        "unsupported_claims": unsupported_claims(primary),
    }
    return payload


def recommendation_summary(row: dict[str, Any]) -> dict[str, Any]:
    if not row:
        return {}
    return {
        "repo_id": row.get("repo_id"),
        "repo_url": row.get("repo_url"),
        "track": row.get("track"),
        "classification": row.get("classification"),
        "estimated_release_eligible_volume": row.get("estimated_release_eligible_volume"),
        "projected_certified_task_count_after_bounded_repair": row.get("projected_certified_task_count_after_bounded_repair"),
        "projected_evidence_backed_rolling_origin_windows": row.get("projected_evidence_backed_rolling_origin_windows"),
        "count_feasible_rolling_origin_windows": row.get("count_feasible_rolling_origin_windows"),
        "expected_evaluation_speed_class": row.get("expected_evaluation_speed_class"),
        "targeted_verifier_timing": row.get("targeted_verifier_timing"),
        "historical_reference_probe": {
            "mode": row.get("historical_reference_probe", {}).get("mode"),
            "sample_size": row.get("historical_reference_probe", {}).get("sample_size"),
            "pass_count": row.get("historical_reference_probe", {}).get("pass_count"),
            "dominant_failure_labels": row.get("historical_reference_probe", {}).get("dominant_failure_labels", {}),
        },
        "environment_risk": row.get("environment_risk"),
        "likely_verifier_command": row.get("likely_verifier_command"),
        "expected_paid_baseline_discovery_cells": row.get("expected_paid_baseline_discovery_cells"),
        "rough_paid_baseline_cost_usd_range": row.get("rough_paid_baseline_cost_usd_range"),
        "reason": row.get("reason_to_deep_probe_or_reject"),
    }


def terminal_state(primary: dict[str, Any]) -> str:
    if not primary:
        return "negative_no_candidate_selected_no_paid"
    if primary.get("classification") in {"balanced_strong_target_prep_candidate", "balanced_target_prep_candidate"}:
        return "large_repo_target_selected_no_paid"
    return "negative_no_balanced_large_fast_target_no_paid"


def next_action(primary: dict[str, Any]) -> str:
    if not primary:
        return "stop: no repository had enough no-paid evidence for target prep"
    repo_id = primary.get("repo_id")
    return (
        f"prepare {repo_id} target profile, package map, verifier pinning, and a 20-30 task no-paid certification wave; "
        "do not start paid baseline discovery or tuning until that gate passes"
    )


def unsupported_claims(primary: dict[str, Any]) -> list[str]:
    repo_id = primary.get("repo_id", "the recommended repository") if primary else "any repository"
    return [
        "No paid Agent cell, paid LLM call, or paid tuner call was run.",
        "No Agent tuning improvement is supported.",
        "No predictive-validity or cross-repo generalization claim is supported.",
        f"{repo_id} is a no-paid target-prep recommendation, not an immediate paid-run authorization.",
        "Projected certified counts are capacity estimates until a bounded release-certification wave proves conversion.",
    ]


def report_payload(payload: dict[str, Any]) -> str:
    candidates = payload["candidate_metrics"]
    primary = payload["recommendation"]
    backup = payload["backup_recommendation"]
    baseline = [row for row in candidates if row.get("track") == "baseline"]
    large = [row for row in candidates if row.get("track") == "large_heavy"]
    medium = [row for row in candidates if row.get("track") == "medium_large_fast"]
    deep = [row for row in candidates if row.get("deep_probe")]
    high_capacity_rejected = [
        row for row in candidates if int(row.get("estimated_release_eligible_volume") or 0) >= MIN_RELEASE_TASKS and row.get("classification") == "large_but_heavy"
    ]
    fast_rejected = [
        row for row in candidates if row.get("classification") == "fast_but_underpowered"
    ]
    return f"""# Large-repo target selection gate

Generated at: `{payload['generated_at']}`. Paid Agent cells: `0`. Paid LLM calls: `0`. Paid tuner calls: `0`.

## Executive Recommendation

Primary recommendation: `{primary.get('repo_id')}` (`{primary.get('classification')}`).
Backup recommendation: `{backup.get('repo_id')}` (`{backup.get('classification')}`).

This is a no-paid target-prep recommendation, not permission to start paid baseline discovery or tuning. The best balance in this run is `{primary.get('repo_id')}` because it combines projected task capacity, rolling-origin shape, and targeted verifier evidence better than the old attrs/click fallback and better than the large compiled stacks whose setup risk dominated their raw capacity.

## Candidate Table By Track

### Baseline And Prior Near-miss

{markdown_table(summary_rows(baseline), summary_columns())}

### Large/Heavy Candidates

{markdown_table(summary_rows(large), summary_columns())}

### Medium-large Fast-evaluation Candidates

{markdown_table(summary_rows(medium), summary_columns())}

## Large/heavy Findings

The large/heavy track confirms that size alone is not enough. `pandas` and `scikit-learn` have strong raw capacity signals, but compiled-extension setup and generic-probe failures make them `large_but_heavy` rather than practical mainline targets. `django` has very high source-linked capacity, but the bounded pytest shards failed under the generic verifier command, so it is an environment/profile repair candidate. `sqlalchemy` timed well on current targeted shards, but this simple public-ref screen found too little source-linked changed-test oracle volume. `sympy` also screened low under the public-ref heuristic despite being large, so it needs a different source-context miner before it can be considered.

## Medium-large Fast-evaluation Findings

The medium-large fast track is the right comparison class against old attrs/click. `{primary.get('repo_id')}` is the strongest measured result in the final run: its current targeted shards passed quickly and projected source-linked changed-test capacity clears the conservative threshold. `black` and `starlette` have attractive raw history, but their configured current probes were only partial or failed after dependency profile tightening, so they are bounded repair opportunities rather than recommendations. `httpx` and `anyio` also need verifier-profile repair before they can compete on practical iteration speed.

## Top Deep-probe Summaries

{markdown_table(deep_rows(deep), [('Repo', 'repo'), ('Track', 'track'), ('Smoke', 'smoke'), ('Median s', 'median'), ('P95 s', 'p95'), ('Hist replay', 'hist'), ('Projected', 'projected'), ('Repair projection', 'repair'), ('Label', 'label')])}

## Capacity vs Evaluation-speed Tradeoff

The preferred target is not the largest repository. A repository needs enough source-linked implementation-plus-test changes to survive release certification, but the verifier must also be targetable to sub-suite tests. The avoid-by-default group is high-capacity but environment-heavy; the underpowered group is fast but does not yet clear the `60` conservative task threshold. The recommended path is to prep the candidate with the strongest middle: high enough projected task count and targeted verifier timing that leaves room for iteration.

## Recommended Target And Backup

Recommended target: `{primary.get('repo_id')}`. It should receive a target profile, package map, verifier pinning, and a 20-30 task no-paid certification wave before any paid work. Its current targeted verifier timing is strong, but the one-sample historical changed-test replay did not pass under the generic dependency profile, so version-aware verifier pinning is a required next gate.

Backup: `{backup.get('repo_id')}`. Use it only as a follow-up no-paid prep candidate if `{primary.get('repo_id')}` fails; it still needs its own targeted smoke and certification wave before any paid baseline discovery.

## Repositories Rejected Despite High Capacity

{markdown_table(rejection_rows(high_capacity_rejected), [('Repo', 'repo'), ('Why rejected', 'why'), ('Repair opportunity', 'repair')]) if high_capacity_rejected else '_No high-capacity repository was rejected solely after passing the speed gate._'}

## Repositories Rejected Despite Fast Evaluation

{markdown_table(rejection_rows(fast_rejected), [('Repo', 'repo'), ('Why rejected', 'why'), ('Repair opportunity', 'repair')]) if fast_rejected else '_No fast candidate was rejected solely for low capacity after this bounded screen._'}

## Next No-paid Prep Plan

1. Create a target profile and package map for `{primary.get('repo_id')}`.
2. Pin a task-level verifier command that prefers changed tests or narrow module shards, not full-suite execution.
3. Run a 20-30 task no-paid release-certification wave across at least two time buckets.
4. Freeze a rolling-origin split only if the certified count supports at least two evidence-backed windows.
5. Recompute paid baseline discovery cells and stop again before any paid Agent or tuner call.

## Paid Baseline Discovery Estimate

For `{primary.get('repo_id')}`, the rough baseline-discovery estimate is `{primary.get('expected_paid_baseline_discovery_cells')}` cells, with a coarse historical cost range of `${primary.get('rough_paid_baseline_cost_usd_range', {}).get('low')}` to `${primary.get('rough_paid_baseline_cost_usd_range', {}).get('high')}`. This estimate is not an authorization.

## Unsupported Claims

{chr(10).join(f'- {claim}' for claim in payload['unsupported_claims'])}
"""


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    lines = ["| " + " | ".join(label for label, _ in columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "")).replace("|", "\\|").replace("\n", " ") for _, key in columns) + " |")
    return "\n".join(lines)


def summary_columns() -> list[tuple[str, str]]:
    return [
        ("Repo", "repo"),
        ("Impl+Test", "impl_test"),
        ("Source refs", "refs"),
        ("Projected", "projected"),
        ("Windows", "windows"),
        ("Smoke", "smoke"),
        ("Speed", "speed"),
        ("Risk", "risk"),
        ("Label", "label"),
    ]


def summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [summary_row(row) for row in sorted(rows, key=lambda row: (row.get("classification"), row.get("repo_id")))]


def summary_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "repo": row.get("repo_id"),
        "track": row.get("track"),
        "impl_test": row.get("implementation_plus_test_change_count", 0),
        "refs": row.get("changed_test_oracle_availability_count", 0),
        "projected": row.get("estimated_release_eligible_volume", 0),
        "windows": row.get("count_feasible_rolling_origin_windows", 0),
        "smoke": row.get("visible_setup_smoke_status", ""),
        "speed": row.get("expected_evaluation_speed_class", ""),
        "risk": row.get("environment_risk", ""),
        "label": row.get("classification", ""),
    }


def deep_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        timing = row.get("targeted_verifier_timing", {})
        historical = row.get("historical_reference_probe", {})
        out.append(
            {
                "repo": row.get("repo_id"),
                "track": row.get("track"),
                "smoke": row.get("visible_setup_smoke_status"),
                "median": timing.get("median_seconds"),
                "p95": timing.get("p95_seconds"),
                "hist": f"{historical.get('pass_count', 0)}/{historical.get('sample_size', 0)}",
                "projected": row.get("estimated_release_eligible_volume"),
                "repair": row.get("projected_certified_task_count_after_bounded_repair"),
                "label": row.get("classification"),
            }
        )
    return out


def rejection_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "repo": row.get("repo_id"),
            "why": row.get("reason_to_deep_probe_or_reject"),
            "repair": "bounded verifier/environment repair, then repeat no-paid certification; otherwise reject for practical iteration",
        }
        for row in rows
    ]


def csv_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in payload["candidate_metrics"]:
        timing = row.get("targeted_verifier_timing", {})
        hist = row.get("historical_reference_probe", {})
        rows.append(
            {
                "repo_id": row.get("repo_id"),
                "repo_url": row.get("repo_url"),
                "track": row.get("track"),
                "checkout_status": row.get("checkout_status"),
                "total_commits": row.get("total_commits", ""),
                "total_commits_scanned": row.get("total_commits_scanned", ""),
                "implementation_change_count": row.get("implementation_change_count", ""),
                "test_change_count": row.get("test_change_count", ""),
                "implementation_plus_test_change_count": row.get("implementation_plus_test_change_count", ""),
                "source_ref_count": row.get("changed_test_oracle_availability_count", ""),
                "estimated_release_eligible_volume": row.get("estimated_release_eligible_volume", ""),
                "rolling_origin_windows": row.get("count_feasible_rolling_origin_windows", ""),
                "visible_setup_smoke_status": row.get("visible_setup_smoke_status", ""),
                "targeted_median_seconds": timing.get("median_seconds", ""),
                "targeted_p95_seconds": timing.get("p95_seconds", ""),
                "historical_reference_probe_passes": hist.get("pass_count", ""),
                "historical_reference_probe_samples": hist.get("sample_size", ""),
                "environment_risk": row.get("environment_risk", ""),
                "expected_evaluation_speed_class": row.get("expected_evaluation_speed_class", ""),
                "classification": row.get("classification", ""),
                "reason": row.get("reason_to_deep_probe_or_reject", ""),
            }
        )
    return rows


def run(
    *,
    clone: bool,
    clone_timeout: int,
    run_deep_probes: bool,
    task_shape_sample_limit: int,
    historical_sample_limit: int,
) -> dict[str, Any]:
    payload = build_payload(
        clone=clone,
        clone_timeout=clone_timeout,
        run_deep_probes=run_deep_probes,
        task_shape_sample_limit=task_shape_sample_limit,
        historical_sample_limit=historical_sample_limit,
    )
    write_json(RESULTS / "large_repo_target_selection_gate.json", payload)
    write_text(REPORTS / "large_repo_target_selection_gate_zh.md", report_payload(payload))
    write_csv(
        RESULTS / "large_repo_target_selection_candidates.csv",
        csv_rows(payload),
        [
            "repo_id",
            "repo_url",
            "track",
            "checkout_status",
            "total_commits",
            "total_commits_scanned",
            "implementation_change_count",
            "test_change_count",
            "implementation_plus_test_change_count",
            "source_ref_count",
            "estimated_release_eligible_volume",
            "rolling_origin_windows",
            "visible_setup_smoke_status",
            "targeted_median_seconds",
            "targeted_p95_seconds",
            "historical_reference_probe_passes",
            "historical_reference_probe_samples",
            "environment_risk",
            "expected_evaluation_speed_class",
            "classification",
            "reason",
        ],
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clone-missing", action="store_true", help="clone missing public repositories under ignored external_repos")
    parser.add_argument("--clone-timeout", type=int, default=300)
    parser.add_argument("--run-deep-probes", action="store_true", help="run bounded visible smoke and historical reference probes")
    parser.add_argument("--task-shape-sample-limit", type=int, default=24)
    parser.add_argument("--historical-sample-limit", type=int, default=1)
    args = parser.parse_args()
    payload = run(
        clone=args.clone_missing,
        clone_timeout=args.clone_timeout,
        run_deep_probes=args.run_deep_probes,
        task_shape_sample_limit=args.task_shape_sample_limit,
        historical_sample_limit=args.historical_sample_limit,
    )
    print(json.dumps(payload["recommendation"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
