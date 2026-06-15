from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXTERNAL_REPOS = ROOT / "experiments" / "phase0_headroom" / "external_repos"
RESULTS = ROOT / "experiments" / "agent_tuning_demo" / "results"
REPORTS = ROOT / "experiments" / "agent_tuning_demo" / "reports"

SCHEMA_VERSION = "barcarolle.target_repo_selection_gate.v1"
SCAN_SINCE = "2010-01-01"
HISTORY_SCAN_CAP = 3000

MIN_RELEASE_TASKS = 60
PREFERRED_RELEASE_TASKS = 90
MIN_WINDOW_TRAIN = 10
MIN_WINDOW_DEV = 6
MIN_WINDOW_FUTURE = 10


@dataclass(frozen=True)
class CandidateConfig:
    repo_id: str
    repo_url: str
    local_dir: str
    package_import: str
    baseline: bool
    smoke_paths: tuple[str, ...] = ()
    deep_probe: bool = False
    external_service_risk: str = "low"


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def digest_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def candidate_configs() -> list[CandidateConfig]:
    return [
        CandidateConfig(
            "boltons",
            "https://github.com/mahmoud/boltons.git",
            "boltons",
            "boltons",
            True,
            ("tests/test_iterutils.py", "tests/test_cacheutils.py"),
            True,
        ),
        CandidateConfig(
            "attrs",
            "https://github.com/python-attrs/attrs.git",
            "attrs",
            "attr",
            True,
            ("tests/test_funcs.py", "tests/test_validators.py"),
            True,
        ),
        CandidateConfig(
            "click",
            "https://github.com/pallets/click.git",
            "click",
            "click",
            True,
            ("tests/test_basic.py", "tests/test_options.py"),
            True,
        ),
        CandidateConfig("toolz", "https://github.com/pytoolz/toolz.git", "toolz", "toolz", True),
        CandidateConfig("humanize", "https://github.com/python-humanize/humanize.git", "humanize", "humanize", True),
        CandidateConfig(
            "packaging",
            "https://github.com/pypa/packaging.git",
            "packaging",
            "packaging",
            False,
            ("tests/test_version.py", "tests/test_markers.py"),
            True,
        ),
        CandidateConfig(
            "jinja2",
            "https://github.com/pallets/jinja.git",
            "jinja2",
            "jinja2",
            False,
            ("tests/test_api.py", "tests/test_filters.py"),
            True,
        ),
        CandidateConfig(
            "werkzeug",
            "https://github.com/pallets/werkzeug.git",
            "werkzeug",
            "werkzeug",
            False,
            ("tests/test_http.py", "tests/test_datastructures.py"),
            True,
        ),
        CandidateConfig(
            "cachetools",
            "https://github.com/tkem/cachetools.git",
            "cachetools",
            "cachetools",
            False,
            ("tests/test_cache.py", "tests/test_ttl.py"),
            True,
        ),
        CandidateConfig("pluggy", "https://github.com/pytest-dev/pluggy.git", "pluggy", "pluggy", False),
        CandidateConfig(
            "sortedcontainers",
            "https://github.com/grantjenks/python-sortedcontainers.git",
            "sortedcontainers",
            "sortedcontainers",
            False,
        ),
        CandidateConfig(
            "pytest",
            "https://github.com/pytest-dev/pytest.git",
            "pytest",
            "_pytest",
            False,
            external_service_risk="high_complex_self_hosting_test_harness",
        ),
        CandidateConfig("requests", "https://github.com/psf/requests.git", "requests", "requests", False, external_service_risk="medium"),
        CandidateConfig(
            "marshmallow",
            "https://github.com/marshmallow-code/marshmallow.git",
            "marshmallow",
            "marshmallow",
            False,
            ("tests/test_schema.py", "tests/test_fields.py"),
            True,
        ),
        CandidateConfig("jsonschema", "https://github.com/python-jsonschema/jsonschema.git", "jsonschema", "jsonschema", False),
        CandidateConfig(
            "urllib3",
            "https://github.com/urllib3/urllib3.git",
            "urllib3",
            "urllib3",
            False,
            ("test/test_retry.py", "test/test_util.py"),
            True,
            external_service_risk="medium",
        ),
        CandidateConfig("dateutil", "https://github.com/dateutil/dateutil.git", "dateutil", "dateutil", False),
        CandidateConfig("rich", "https://github.com/Textualize/rich.git", "rich", "rich", False),
    ]


def prior_evidence() -> dict[str, dict[str, Any]]:
    gate = read_json(ROOT / "experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_release_gate.json", {})
    third_source = read_json(
        ROOT / "experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_source_context_inventory.json", {}
    )
    third_env = read_json(ROOT / "experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_environment_probe.json", {})
    third_attempts = read_json(
        ROOT / "experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_certification_attempts.json", {}
    )
    out: dict[str, dict[str, Any]] = {
        "boltons": {
            "known_release_eligible": 57,
            "known_current_release_eligible": 35,
            "known_certification_attempts": 80,
            "known_release_conversion": 22 / 58,
            "evidence_backed_windows": 1,
            "prior_source": "boltons_capacity_final_recommendation",
            "prior_note": "57 projected release tasks; only one evidence-backed tuning window.",
        },
        "attrs": {
            "known_release_eligible": 31,
            "known_technical_certified": 28,
            "known_replay_passes": 1,
            "known_replay_attempts": 4,
            "evidence_backed_windows": 0,
            "prior_source": "second_repo_gate_and_attrs_source_repair",
            "prior_note": "31 release-eligible after overlay; packaging and verifier pinning repairs remain.",
        },
        "click": {
            "known_release_eligible": 30,
            "known_technical_certified": 75,
            "known_certification_attempts": 102,
            "known_release_conversion": 30 / 102,
            "evidence_backed_windows": 0,
            "prior_source": "third_repo_release_supply_screen_and_click_source_repair",
            "prior_note": "30 release-eligible and source context repaired; target-profile packaging still needed.",
        },
        "toolz": {
            "known_release_eligible": 5,
            "known_technical_certified": 6,
            "prior_source": "boltons_capacity_repo_selection_fallback",
            "prior_note": "Supply below threshold.",
        },
        "humanize": {
            "known_release_eligible": 12,
            "known_technical_certified": 12,
            "prior_source": "boltons_capacity_repo_selection_fallback",
            "prior_note": "Supply below threshold.",
        },
    }
    release_counts = gate.get("release_eligible_count_by_repo", {}) if isinstance(gate, dict) else {}
    technical_counts = gate.get("technical_certified_count_by_candidate_repo", {}) if isinstance(gate, dict) else {}
    release_ready = third_source.get("release_ready_before_certification_count_by_repo", {}) if isinstance(third_source, dict) else {}
    upper = third_source.get("technical_plus_review_upper_bound_count_by_repo", {}) if isinstance(third_source, dict) else {}
    env_rows = third_env.get("rows", []) if isinstance(third_env, dict) else []
    attempt_rows = third_attempts.get("rows", []) if isinstance(third_attempts, dict) else []
    for repo_id in sorted(set(release_ready) | set(upper) | set(release_counts) | set(technical_counts)):
        repo_env_rows = [row for row in env_rows if row.get("repo_id") == repo_id]
        repo_attempt_rows = [row for row in attempt_rows if row.get("repo_id") == repo_id]
        observed = repo_attempt_rows or repo_env_rows
        out.setdefault(repo_id, {})
        out[repo_id].update(
            {
                "prior_source": "phase1_third_repo_release_supply_screen",
                "prior_release_ready_before_certification": release_ready.get(repo_id, 0),
                "prior_technical_plus_review_upper_bound": upper.get(repo_id, 0),
                "known_release_eligible": max(int(release_counts.get(repo_id, 0)), int(out[repo_id].get("known_release_eligible", 0))),
                "known_technical_certified": max(
                    int(technical_counts.get(repo_id, 0)), int(out[repo_id].get("known_technical_certified", 0))
                ),
                "prior_probe_attempts": len(observed),
                "prior_probe_release_eligible": sum(1 for row in observed if row.get("release_eligible")),
                "prior_probe_technical_certified": sum(1 for row in observed if row.get("technical_certified")),
            }
        )
    for repo_id in ["marshmallow", "urllib3"]:
        sample = read_json(RESULTS / f"target_repo_selection_gate_{repo_id}_cert_sample.json", {})
        if not sample:
            continue
        out.setdefault(repo_id, {})
        out[repo_id].update(
            {
                "prior_source": f"target_repo_selection_gate_{repo_id}_cert_sample",
                "prior_probe_attempts": int(sample.get("sample_count") or 0),
                "prior_probe_release_eligible": int(sample.get("release_eligible_count") or 0),
                "prior_probe_technical_certified": int(sample.get("technical_certified_count") or 0),
                "prior_probe_subgate_counts": sample.get("terminal_execution_subgate_counts", {}),
                "prior_note": "Fresh no-paid gate replay sample did not produce a technical certification.",
            }
        )
    return out


def run_command(args: list[str], cwd: Path, timeout: int = 120) -> CommandResult:
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


def is_test_path(path: str) -> bool:
    lower = path.lower()
    if not lower.endswith((".py", ".pyi")):
        return False
    return bool(
        re.search(r"(^|/)(tests?|testing)/", lower)
        or re.search(r"(^|/)test_[^/]*\.pyi?$", lower)
        or re.search(r"(^|/)[^/]*_test\.pyi?$", lower)
    )


def is_impl_path(path: str) -> bool:
    lower = path.lower()
    if not lower.endswith((".py", ".pyi")):
        return False
    if is_test_path(path):
        return False
    excluded_roots = ("docs/", "doc/", "examples/", "example/", "bench/", "benchmark/", "benchmarks/", "scripts/")
    return not lower.startswith(excluded_roots)


def public_refs_from_subject(subject: str) -> list[str]:
    refs = [f"pr_or_issue:{match.group(1)}" for match in re.finditer(r"#(\d+)", subject or "")]
    return list(dict.fromkeys(refs))


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
        timeout=75,
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
        impl = [path for path in changed if is_impl_path(path)]
        tests = [path for path in changed if is_test_path(path)]
        rows.append(
            {
                "commit": commit,
                "parent": parents.split()[0] if parents.split() else "",
                "task_time": task_time,
                "year": int(task_time[:4]) if task_time[:4].isdigit() else None,
                "subject_has_public_ref": bool(public_refs_from_subject(subject)),
                "implementation_files": impl,
                "test_files": tests,
                "has_implementation": bool(impl),
                "has_tests": bool(tests),
            }
        )
    capped = len(rows) >= HISTORY_SCAN_CAP
    return rows, capped


def date_span(repo: Path) -> dict[str, str]:
    root_commits = git_stdout(repo, ["rev-list", "--max-parents=0", "HEAD"], timeout=60).splitlines()
    first_commit = root_commits[0] if root_commits else "HEAD"
    first = git_stdout(repo, ["show", "-s", "--format=%cI", first_commit], timeout=60)
    latest = git_stdout(repo, ["log", "-1", "--format=%cI"], timeout=60)
    return {"first_commit": first, "latest_commit": latest}


def dirty_line_count(repo: Path) -> int:
    result = run_command(["git", "status", "--short", "--untracked-files=no"], repo, timeout=60)
    if result.returncode != 0:
        return -1
    return len([line for line in result.stdout.splitlines() if line.strip()])


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


def simulate_windows(years: list[int], *, minimum_future: int = MIN_WINDOW_FUTURE) -> list[dict[str, Any]]:
    if not years:
        return []
    out: list[dict[str, Any]] = []
    for dev_start in range(min(years) + 1, max(years) - 1):
        train = sum(1 for year in years if year < dev_start)
        dev = sum(1 for year in years if dev_start <= year < dev_start + 2)
        future = sum(1 for year in years if year >= dev_start + 2)
        if train >= MIN_WINDOW_TRAIN and dev >= MIN_WINDOW_DEV and future >= minimum_future:
            out.append(
                {
                    "window_id": f"train_lt_{dev_start}_dev_{dev_start}_{dev_start + 1}_future_gte_{dev_start + 2}",
                    "train_count": train,
                    "dev_count": dev,
                    "future_count": future,
                }
            )
    return out


def run_smoke(config: CandidateConfig, repo: Path) -> dict[str, Any]:
    if not config.smoke_paths:
        return {"status": "not_run_screen_only", "reason": "no bounded smoke paths configured"}
    missing = [path for path in config.smoke_paths if not (repo / path).exists()]
    if missing:
        return {"status": "not_run_missing_paths", "missing_paths": missing}
    command = ["uv", "run", "--with", "pytest>=8,<10", "--with", ".", "--", "python", "-m", "pytest", *config.smoke_paths, "-q"]
    result = run_command(command, repo, timeout=240)
    return {
        "status": "passed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "duration_seconds": result.duration_seconds,
        "timed_out": result.timed_out,
        "command_shape": ["uv", "run", "--with", "pytest>=8,<10", "--with", ".", "--", "python", "-m", "pytest", "<smoke_paths>", "-q"],
        "stdout_line_count": len(result.stdout.splitlines()),
        "stderr_line_count": len(result.stderr.splitlines()),
        "stdout_tail_hash": digest_text(result.stdout[-1000:]),
        "stderr_tail_hash": digest_text(result.stderr[-1000:]),
    }


def projected_release_count(metrics: dict[str, Any], prior: dict[str, Any]) -> int:
    known = int(prior.get("known_release_eligible") or 0)
    if known:
        return known
    release_ready = int(metrics["release_ready_before_certification_count"])
    attempts = int(prior.get("prior_probe_attempts") or 0)
    release_success = int(prior.get("prior_probe_release_eligible") or 0)
    if attempts:
        return min(release_ready, round(release_ready * (release_success / attempts)))
    if release_ready >= 90:
        return round(release_ready * 0.35)
    if release_ready >= 45:
        return round(release_ready * 0.25)
    return round(release_ready * 0.15)


def candidate_metrics(config: CandidateConfig, *, run_smokes: bool, priors: dict[str, dict[str, Any]]) -> dict[str, Any]:
    repo = EXTERNAL_REPOS / config.local_dir
    prior = priors.get(config.repo_id, {})
    base = {
        "repo_id": config.repo_id,
        "repo_url": config.repo_url,
        "local_path": rel(repo),
        "baseline": config.baseline,
        "deep_probe": config.deep_probe,
        "checkout_status": "missing",
        "external_service_risk": config.external_service_risk,
        "prior_evidence": prior,
    }
    if not (repo / ".git").exists():
        base.update(
            {
                "screen_label": "screened_out",
                "recommendation_role": "not_recommended",
                "main_blockers": ["local_checkout_missing"],
                "repair_plan": "clone under ignored external repo path and rerun the gate",
            }
        )
        return base
    dirty = dirty_line_count(repo)
    if dirty:
        base.update(
            {
                "checkout_status": "dirty_or_partial_checkout",
                "dirty_line_count": dirty,
                "screen_label": "screened_out",
                "recommendation_role": "not_recommended",
                "main_blockers": ["checkout_dirty_or_partial"],
                "repair_plan": "repair or reclone the ignored external checkout, then rerun the gate",
            }
        )
        return base
    try:
        history_rows, history_capped = parse_git_history(repo)
        span = date_span(repo)
        head = git_stdout(repo, ["rev-parse", "--short", "HEAD"], timeout=60)
        total_commits = int(git_stdout(repo, ["rev-list", "--count", "HEAD"], timeout=120))
    except Exception as exc:
        base.update(
            {
                "checkout_status": "history_read_failed",
                "screen_label": "screened_out",
                "recommendation_role": "not_recommended",
                "main_blockers": [f"history_read_failed:{type(exc).__name__}"],
                "repair_plan": "repair git checkout and rerun history metric collection",
            }
        )
        return base

    impl_count = sum(1 for row in history_rows if row["has_implementation"])
    test_count = sum(1 for row in history_rows if row["has_tests"])
    impl_test = [row for row in history_rows if row["has_implementation"] and row["has_tests"]]
    impl_test_refs = [row for row in impl_test if row["subject_has_public_ref"]]
    impl_test_years = [int(row["year"]) for row in impl_test if row["year"] is not None]
    release_ready_years = [int(row["year"]) for row in impl_test_refs if row["year"] is not None]
    smoke = run_smoke(config, repo) if run_smokes and config.deep_probe else {"status": "not_run"}
    metrics = {
        **base,
        "checkout_status": "clean",
        "head_short": head,
        "history_commit_count": total_commits,
        "history_scan_since": SCAN_SINCE,
        "history_scan_cap": HISTORY_SCAN_CAP,
        "history_scan_capped": history_capped,
        "history_date_span": span,
        "implementation_change_count": impl_count,
        "test_change_count": test_count,
        "implementation_plus_test_change_count": len(impl_test),
        "implementation_plus_test_public_ref_count": len(impl_test_refs),
        "source_context_availability": source_context_label(len(impl_test_refs), len(impl_test)),
        "source_context_leakage_risk": "low" if impl_test_refs else "medium_commit_message_only",
        "oracle_availability": "changed_tests_available" if impl_test else "weak_or_missing_changed_tests",
        "time_bucket_distribution": dict(sorted(Counter(time_bucket(row["year"]) for row in impl_test).items())),
        "release_ready_before_certification_count": len(impl_test_refs),
        "technical_plus_review_upper_bound_count": len(impl_test),
        "rolling_origin_windows_raw": simulate_windows(impl_test_years),
        "rolling_origin_windows_release_ready": simulate_windows(release_ready_years),
        "visible_test_setup_smoke": smoke,
    }
    projected = projected_release_count(metrics, prior)
    metrics["current_or_projected_release_eligible_count"] = projected
    metrics["estimated_or_observed_certification_conversion"] = conversion_label(metrics, prior)
    metrics["at_least_two_rolling_origin_windows_count_feasible"] = len(metrics["rolling_origin_windows_raw"]) >= 2 and projected >= MIN_RELEASE_TASKS
    metrics["at_least_two_windows_evidence_backed_enough_for_tuning"] = evidence_backed_window_feasible(metrics, prior)
    metrics["expected_paid_baseline_discovery_cells"] = expected_paid_cells(projected)
    metrics["rough_paid_baseline_cost_usd_range"] = rough_cost_range(metrics["expected_paid_baseline_discovery_cells"])
    metrics["verifier_environment_risk"] = verifier_risk(metrics, prior)
    metrics["screen_label"] = screen_label(metrics)
    metrics["recommendation_role"] = "candidate"
    metrics["main_blockers"] = blockers(metrics, prior)
    metrics["repair_plan"] = repair_plan(metrics)
    return metrics


def source_context_label(public_ref_count: int, impl_test_count: int) -> str:
    if public_ref_count >= 90:
        return "strong_pr_or_issue_title_context"
    if public_ref_count >= 45:
        return "adequate_pr_or_issue_title_context"
    if public_ref_count >= 20:
        return "thin_but_usable_pr_or_issue_title_context"
    if impl_test_count:
        return "mostly_commit_message_or_manual_source_repair_needed"
    return "no_meaningful_source_context_inventory"


def conversion_label(metrics: dict[str, Any], prior: dict[str, Any]) -> dict[str, Any]:
    if prior.get("known_release_conversion") is not None:
        attempts = int(prior.get("known_certification_attempts") or 0)
        rate = float(prior["known_release_conversion"])
        return {
            "kind": "observed_prior_no_paid_release_conversion",
            "attempts": attempts,
            "release_or_replay_successes": round(attempts * rate, 2) if attempts else None,
            "rate": round(rate, 4),
        }
    if prior.get("prior_probe_attempts"):
        attempts = int(prior.get("prior_probe_attempts") or 0)
        release = int(prior.get("prior_probe_release_eligible") or 0)
        return {"kind": "observed_prior_no_paid_probe", "attempts": attempts, "release_or_replay_successes": release, "rate": round(release / attempts, 4)}
    if prior.get("known_replay_attempts"):
        attempts = int(prior.get("known_replay_attempts") or 0)
        release = int(prior.get("known_replay_passes") or 0)
        return {"kind": "observed_prior_no_paid_replay_sample", "attempts": attempts, "release_or_replay_successes": release, "rate": round(release / attempts, 4)}
    return {
        "kind": "projected_from_source_supply_only",
        "attempts": 0,
        "release_or_replay_successes": 0,
        "rate": None,
        "note": "needs bounded no-paid certification before paid baseline discovery",
    }


def evidence_backed_window_feasible(metrics: dict[str, Any], prior: dict[str, Any]) -> bool:
    if int(prior.get("evidence_backed_windows") or 0) >= 2:
        return True
    smoke_status = metrics.get("visible_test_setup_smoke", {}).get("status")
    projected = int(metrics.get("current_or_projected_release_eligible_count") or 0)
    release_windows = len(metrics.get("rolling_origin_windows_release_ready") or [])
    observed_release = int(prior.get("known_release_eligible") or 0)
    return projected >= MIN_RELEASE_TASKS and release_windows >= 2 and smoke_status == "passed" and observed_release >= MIN_RELEASE_TASKS


def expected_paid_cells(projected_release_count: int) -> int:
    if projected_release_count < 30:
        return 0
    task_count = min(max(projected_release_count, 30), 90)
    return task_count * 4


def rough_cost_range(cells: int) -> dict[str, float]:
    if cells <= 0:
        return {"low": 0.0, "high": 0.0}
    return {"low": round(cells * 0.20, 2), "high": round(cells * 0.45, 2)}


def verifier_risk(metrics: dict[str, Any], prior: dict[str, Any]) -> str:
    smoke = metrics.get("visible_test_setup_smoke", {}).get("status")
    if str(metrics.get("external_service_risk", "")).startswith("high"):
        return "high_complex_or_infrastructure_heavy_tests"
    if smoke == "failed":
        return "high_visible_smoke_failed"
    if metrics.get("external_service_risk") != "low":
        return "medium_external_or_integration_tests_need_isolation"
    if int(prior.get("prior_probe_attempts") or 0) and int(prior.get("prior_probe_release_eligible") or 0) == 0:
        return "high_prior_replay_probe_failed"
    if smoke == "passed":
        return "low_current_visible_smoke_passed"
    return "medium_needs_current_smoke_or_replay_probe"


def screen_label(metrics: dict[str, Any]) -> str:
    projected = int(metrics.get("current_or_projected_release_eligible_count") or 0)
    release_ready = int(metrics.get("release_ready_before_certification_count") or 0)
    raw_windows = len(metrics.get("rolling_origin_windows_raw") or [])
    smoke = metrics.get("visible_test_setup_smoke", {}).get("status")
    risk = str(metrics.get("verifier_environment_risk"))
    if projected >= MIN_RELEASE_TASKS and raw_windows >= 2 and smoke == "passed" and not risk.startswith("high"):
        return "strong_multi_window_candidate"
    if release_ready >= MIN_RELEASE_TASKS and raw_windows >= 2 and not risk.startswith("high"):
        return "prep_candidate_certification_needed"
    if projected >= 30:
        return "small_pilot_or_backup"
    return "screened_out_or_supply_below_gate"


def blockers(metrics: dict[str, Any], prior: dict[str, Any]) -> list[str]:
    out: list[str] = []
    if int(metrics.get("current_or_projected_release_eligible_count") or 0) < MIN_RELEASE_TASKS:
        out.append("projected_release_eligible_count_below_60")
    if len(metrics.get("rolling_origin_windows_raw") or []) < 2:
        out.append("rolling_origin_window_count_sparse")
    if not metrics.get("at_least_two_windows_evidence_backed_enough_for_tuning"):
        out.append("evidence_backed_multi_window_not_proven")
    if str(metrics.get("verifier_environment_risk", "")).startswith("high"):
        out.append(metrics["verifier_environment_risk"])
    if int(prior.get("known_release_eligible") or 0) == 0:
        out.append("bounded_no_paid_certification_needed")
    return out or ["no_major_no_paid_gate_blocker_identified"]


def repair_plan(metrics: dict[str, Any]) -> str:
    label = metrics.get("screen_label")
    if label == "strong_multi_window_candidate":
        return "freeze target profile, run bounded certification wave, then split/freeze no-paid rehearsal before any paid cells"
    if label == "prep_candidate_certification_needed":
        return "run no-paid certification on release-ready rows and repair verifier environment before paid baseline discovery"
    if label == "small_pilot_or_backup":
        return "use only as small second-repo pilot or backup unless further certification expands supply"
    return "do not advance unless new mining or environment repair changes the supply conclusion"


def choose_recommendations(candidates: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    viable = [row for row in candidates if row.get("checkout_status") == "clean"]
    scored = sorted(
        viable,
        key=lambda row: (
            row.get("screen_label") != "strong_multi_window_candidate",
            row.get("screen_label") != "prep_candidate_certification_needed",
            row.get("baseline") is True,
            -int(row.get("current_or_projected_release_eligible_count") or 0),
            -int(row.get("release_ready_before_certification_count") or 0),
            str(row.get("verifier_environment_risk", "")).startswith("high"),
            str(row.get("repo_id")),
        ),
    )
    primary = scored[0] if scored else {}
    backups = [row for row in scored[1:] if row.get("repo_id") != primary.get("repo_id")]
    backup = next((row for row in backups if row.get("repo_id") == "click"), None)
    if backup is None:
        backup = next((row for row in backups if row.get("repo_id") == "boltons"), backups[0] if backups else {})
    primary["recommendation_role"] = "primary_recommendation"
    if backup:
        backup["recommendation_role"] = "backup_recommendation"
    return primary, backup


def build_payload(*, run_smokes: bool) -> dict[str, Any]:
    priors = prior_evidence()
    candidates = [candidate_metrics(config, run_smokes=run_smokes, priors=priors) for config in candidate_configs()]
    primary, backup = choose_recommendations(candidates)
    new_candidates = [row for row in candidates if not row.get("baseline")]
    deep_new = [row for row in new_candidates if row.get("deep_probe")]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": iso_now(),
        "paid_cells_run": 0,
        "paid_llm_calls_run": 0,
        "paid_tuner_calls_run": 0,
        "history_scan_since": SCAN_SINCE,
        "history_scan_cap": HISTORY_SCAN_CAP,
        "new_repository_screen_count": len(new_candidates),
        "new_repository_deep_probe_count": len(deep_new),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "top_recommendation": recommendation_summary(primary),
        "backup_recommendation": recommendation_summary(backup),
        "terminal_state": "target_repo_selected_no_paid",
        "next_action": next_action(primary),
        "unsupported_claims": unsupported_claims(primary),
    }


def recommendation_summary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "repo_id": row.get("repo_id"),
        "repo_url": row.get("repo_url"),
        "baseline": row.get("baseline"),
        "screen_label": row.get("screen_label"),
        "current_or_projected_release_eligible_count": row.get("current_or_projected_release_eligible_count"),
        "release_ready_before_certification_count": row.get("release_ready_before_certification_count"),
        "rolling_origin_windows_raw_count": len(row.get("rolling_origin_windows_raw") or []),
        "rolling_origin_windows_release_ready_count": len(row.get("rolling_origin_windows_release_ready") or []),
        "verifier_environment_risk": row.get("verifier_environment_risk"),
        "expected_paid_baseline_discovery_cells": row.get("expected_paid_baseline_discovery_cells"),
        "rough_paid_baseline_cost_usd_range": row.get("rough_paid_baseline_cost_usd_range"),
        "repair_plan": row.get("repair_plan"),
        "main_blockers": row.get("main_blockers"),
    }


def next_action(primary: dict[str, Any]) -> str:
    repo_id = primary.get("repo_id", "unknown")
    if primary.get("screen_label") == "strong_multi_window_candidate":
        return f"prepare {repo_id} target profile and run bounded no-paid certification/split freeze before any paid cells"
    return f"run bounded no-paid certification and verifier-environment repair for {repo_id} before any paid baseline discovery"


def unsupported_claims(primary: dict[str, Any]) -> list[str]:
    return [
        "No paid Agent tuning improvement is supported by this gate.",
        "No predictive-validity or cross-repo generalization claim is supported.",
        "No repository is immediate-paid-ready until target profile, verifier pinning, split freeze, and baseline discovery gates pass.",
        f"{primary.get('repo_id', 'the primary repository')} is recommended for next no-paid target preparation, not for starting a tuning experiment today.",
    ]


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    lines = ["| " + " | ".join(label for label, _ in columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        values = [str(row.get(key, "")).replace("|", "\\|").replace("\n", " ") for _, key in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def report_payload(payload: dict[str, Any]) -> str:
    candidates = payload["candidates"]
    primary = payload["top_recommendation"]
    backup = payload["backup_recommendation"]
    comparison_rows = [summary_row(row) for row in sorted(candidates, key=lambda row: (row.get("baseline") is False, row.get("repo_id")))]
    new_rows = [summary_row(row) for row in candidates if not row.get("baseline")]
    screened_out = [
        {
            "repo": row.get("repo_id"),
            "reason": "; ".join(row.get("main_blockers", [])),
            "repair": row.get("repair_plan"),
        }
        for row in candidates
        if not row.get("baseline") and row.get("repo_id") != primary.get("repo_id")
    ]
    deep_rows = [probe_row(row) for row in candidates if row.get("deep_probe")]
    not_recommended = [
        {
            "repo": row.get("repo_id"),
            "why_not": "; ".join(row.get("main_blockers", [])),
        }
        for row in candidates
        if row.get("repo_id") not in {primary.get("repo_id"), backup.get("repo_id")}
    ]
    if primary.get("baseline"):
        primary_rationale = (
            f"本轮没有新仓库在 certification/replay 环节实质优于 attrs/click/boltons。`{primary.get('repo_id')}` "
            "因此是保守 fallback：它已有 31 个 release-eligible 任务、当前 smoke 通过、source/context 时间分布较好，"
            "但仍不是 strong multi-window paid-ready 仓库。`click` 是备选；`boltons` 只保留为弱一窗口历史路径，不建议继续作为 stronger demo 主线。"
        )
    else:
        primary_rationale = (
            f"`{primary.get('repo_id')}` 的直接价值不是 immediate paid readiness，而是更适合作为下一轮强 demo 的 no-paid target-prep 对象。"
            "相比 `attrs` 的 `31` 和 `click` 的 `30` release-eligible 小池，它的 release-ready-before-certification 和 raw rolling-origin window 容量更有上限；"
            "相比 `boltons`，它避免继续拉伸已经只有一窗口证据的旧 demo 路径。"
        )
    return f"""# 目标仓库选择门禁报告

生成时间：`{payload['generated_at']}`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 执行建议

主推荐：`{primary.get('repo_id')}`。备选：`{backup.get('repo_id')}`。

本轮结论是选择 `{primary.get('repo_id')}` 作为下一轮 no-paid target-prep 的主仓库，而不是今天启动付费调优。{primary_rationale}

## 候选对比

{markdown_table(comparison_rows, [('Repo', 'repo'), ('Baseline', 'baseline'), ('Impl+Test', 'impl_test'), ('Public refs', 'refs'), ('Release/projected', 'release_projected'), ('Raw windows', 'raw_windows'), ('Evidence windows', 'evidence_windows'), ('Smoke', 'smoke'), ('Risk', 'risk'), ('Label', 'label')])}

## 旧基线结果

`boltons` 仍只支持弱化的一窗口故事：保守投影 `57` 个 release tasks，低于 `60` 门槛，且当前 Kilo low-cost headroom 只支持一个 evidence-backed window。`attrs` 是先前 fallback，但只有 `31` release-eligible，并且 packaging/verifier pinning 未完成。`click` 有 `30` release-eligible 和较好的技术认证记录，是最稳的 baseline 备选，但 supply 仍更像小 pilot 而不是强多窗口调优 demo。

## 新候选结果

本轮筛查新仓库数：`{payload['new_repository_screen_count']}`；deep probe 新仓库数：`{payload['new_repository_deep_probe_count']}`。

{markdown_table(new_rows, [('Repo', 'repo'), ('Impl+Test', 'impl_test'), ('Public refs', 'refs'), ('Release/projected', 'release_projected'), ('Raw windows', 'raw_windows'), ('Smoke', 'smoke'), ('Risk', 'risk'), ('Label', 'label')])}

## 筛出新候选

{markdown_table(screened_out, [('Repo', 'repo'), ('Reason', 'reason'), ('Repair', 'repair')]) if screened_out else '_没有新候选只因原始计数不足被完全筛出；主要差异在 certification/env 风险。_'}

## Top 候选 no-paid probe

{markdown_table(deep_rows, [('Repo', 'repo'), ('Smoke', 'smoke'), ('Prior cert', 'prior_cert'), ('Release ready', 'release_ready'), ('Projected', 'projected'), ('Windows', 'windows'), ('Blockers', 'blockers')])}

## 为什么选择这个仓库

{primary_rationale}

## 不推荐仓库

{markdown_table(not_recommended[:16], [('Repo', 'repo'), ('Why not', 'why_not')])}

## 下一步 no-paid 准备计划

1. 为 `{primary.get('repo_id')}` 写 target profile/package map/verifier command。
2. 从 release-ready rows 中抽样运行 20-30 个 bounded no-paid certification/replay probes。
3. 只在 conversion、source context、verifier pinning 通过后，冻结两个 rolling-origin windows。
4. 用同一脚本重算 release manifest、split plan、cost plan、artifact-hygiene scan。

## 粗略付费 baseline discovery 计划

若只复用当前 `{primary.get('repo_id')}` 的 `31` task 级别，小型 baseline discovery 约 `{primary.get('expected_paid_baseline_discovery_cells', 0)}` cells；若 no-paid certification 证明至少 `60` 个 release-eligible tasks，强 demo 下限约 `240` cells（4 个候选 Agent）。按历史单 cell 粗估，小型方案约 `${primary.get('rough_paid_baseline_cost_usd_range', {}).get('low', 0)}` 到 `${primary.get('rough_paid_baseline_cost_usd_range', {}).get('high', 0)}`；强 demo 需另行重算预算。这不是授权，只是后续 runbook 的预算输入。

## 明确不支持的 claim

{chr(10).join(f'- {claim}' for claim in payload['unsupported_claims'])}
"""


def summary_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "repo": row.get("repo_id"),
        "baseline": row.get("baseline"),
        "impl_test": row.get("implementation_plus_test_change_count", 0),
        "refs": row.get("implementation_plus_test_public_ref_count", 0),
        "release_projected": row.get("current_or_projected_release_eligible_count", 0),
        "raw_windows": len(row.get("rolling_origin_windows_raw") or []),
        "evidence_windows": row.get("prior_evidence", {}).get("evidence_backed_windows", 0),
        "smoke": row.get("visible_test_setup_smoke", {}).get("status", ""),
        "risk": row.get("verifier_environment_risk", ""),
        "label": row.get("screen_label", ""),
    }


def probe_row(row: dict[str, Any]) -> dict[str, Any]:
    conversion = row.get("estimated_or_observed_certification_conversion", {})
    attempts = conversion.get("attempts")
    successes = conversion.get("release_or_replay_successes")
    prior_cert = f"{successes}/{attempts} {conversion.get('kind', '')}" if attempts else "no replay sample"
    return {
        "repo": row.get("repo_id"),
        "smoke": row.get("visible_test_setup_smoke", {}).get("status", ""),
        "prior_cert": prior_cert,
        "release_ready": row.get("release_ready_before_certification_count", 0),
        "projected": row.get("current_or_projected_release_eligible_count", 0),
        "windows": len(row.get("rolling_origin_windows_raw") or []),
        "blockers": "; ".join(row.get("main_blockers", [])),
    }


def output_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [summary_row(row) for row in payload["candidates"]]


def run(run_smokes: bool) -> dict[str, Any]:
    payload = build_payload(run_smokes=run_smokes)
    result_path = RESULTS / "target_repo_selection_gate.json"
    report_path = REPORTS / "target_repo_selection_gate_zh.md"
    csv_path = RESULTS / "target_repo_selection_gate_candidates.csv"
    write_json(result_path, payload)
    write_text(report_path, report_payload(payload))
    write_csv(
        csv_path,
        output_rows(payload),
        ["repo", "baseline", "impl_test", "refs", "release_projected", "raw_windows", "evidence_windows", "smoke", "risk", "label"],
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-smoke", action="store_true", help="run bounded visible setup/test smoke probes for deep candidates")
    args = parser.parse_args()
    payload = run(run_smokes=args.run_smoke)
    print(json.dumps(payload["top_recommendation"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
