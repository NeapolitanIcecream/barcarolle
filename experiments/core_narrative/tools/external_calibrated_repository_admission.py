#!/usr/bin/env python3
"""Phase 0 admission scan for external-calibrated repository benchmark v1."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import requests

from _common import ToolError, emit_json, fail, iso_now, write_json


TOOL = "external_calibrated_repository_admission"
SCHEMA_VERSION = "external-calibrated-repo-benchmark.repository-admission.v1"
PROTOCOL_ID = "external-calibrated-repo-benchmark-v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
RESULTS_ROOT = REPO_ROOT / "experiments/core_narrative/results"
REPORTS_ROOT = REPO_ROOT / "experiments/core_narrative/reports"
DEFAULT_OUTPUT = RESULTS_ROOT / "repository_admission/external_calibrated_phase0_admission_20260515.json"
DEFAULT_REPORT = REPORTS_ROOT / "00_repository_admission.md"
DEFAULT_SMOKE_SUMMARY = RESULTS_ROOT / "repository_admission/swebench_gold_smoke_summary_20260515.json"
DEFAULT_B_ADMISSION_SUMMARY = RESULTS_ROOT / "task_admission/sympy_b_admission_summary_v2.json"

HF_DATASET_SERVER = "https://datasets-server.huggingface.co"
HF_API = "https://huggingface.co/api/datasets"
HF_PAGE_SIZE = 100

T0 = dt.datetime(2026, 5, 14, 23, 59, 59, tzinfo=dt.timezone.utc)
RECENT_WINDOW_START = dt.datetime(2025, 5, 15, 0, 0, 0, tzinfo=dt.timezone.utc)
EXTENDED_WINDOW_START = dt.datetime(2024, 5, 15, 0, 0, 0, tzinfo=dt.timezone.utc)

DATASETS = {
    "swebench_verified": {
        "dataset": "SWE-bench/SWE-bench_Verified",
        "split": "test",
        "role": "primary_external_anchor",
    },
    "swebench_full": {
        "dataset": "SWE-bench/SWE-bench",
        "split": "test",
        "role": "fallback_external_anchor",
    },
}

REPOSITORIES = {
    "sympy": {
        "repo_id": "sympy/sympy",
        "path": REPO_ROOT / "experiments/core_narrative/external_repos/sympy",
        "source_prefixes": ("sympy/",),
        "test_prefixes": ("sympy/",),
        "recommendation_priority": 1,
    },
    "django": {
        "repo_id": "django/django",
        "path": REPO_ROOT / "experiments/core_narrative/external_repos/django",
        "source_prefixes": ("django/",),
        "test_prefixes": ("tests/",),
        "recommendation_priority": 2,
    },
    "sphinx": {
        "repo_id": "sphinx-doc/sphinx",
        "path": REPO_ROOT / "experiments/core_narrative/external_repos/sphinx",
        "source_prefixes": ("sphinx/",),
        "test_prefixes": ("tests/",),
        "recommendation_priority": 3,
    },
}

LOW_SIGNAL_SUBJECT_FRAGMENTS = (
    "release",
    "changelog",
    "pre-commit",
    "precommit",
    "codespell",
    "ruff",
    "mypy",
    "pyright",
    "format",
    "documentation",
    "docs:",
    "dependency",
    "dependencies",
    "workflow",
    "ci",
    "bump",
    "merge branch",
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Structured JSON output.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Markdown report output.")
    parser.add_argument(
        "--repo",
        action="append",
        choices=sorted(REPOSITORIES),
        help="Limit scan to one or more candidate repositories.",
    )
    parser.add_argument(
        "--skip-hf",
        action="store_true",
        help="Do not fetch Hugging Face rows; useful for local parser-only checks.",
    )
    parser.add_argument(
        "--external-summary-cache",
        help="Reuse external_dataset_sources from a prior admission JSON to avoid repeated Hugging Face row fetches.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def digest_parts(*parts: str) -> str:
    return sha256_text("\n".join(parts))


def run_command(command: Sequence[str], *, cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def run_git(repo_path: Path, *args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return run_command(["git", *args], cwd=repo_path, timeout=timeout)


def require_git(repo_path: Path, *args: str, timeout: int = 120) -> str:
    completed = run_git(repo_path, *args, timeout=timeout)
    if completed.returncode != 0:
        raise ToolError("git command failed", repo=repo_relative(repo_path), args=list(args), stderr=completed.stderr[-600:])
    return completed.stdout.strip()


def parse_git_datetime(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def hf_get_json(endpoint: str, *, params: Mapping[str, Any] | None = None, timeout: int = 45) -> dict[str, Any]:
    try:
        response = requests.get(endpoint, params=dict(params or {}), timeout=timeout)
    except requests.RequestException as exc:
        raise ToolError("failed to fetch Hugging Face metadata", endpoint=endpoint, cause=str(exc)) from exc
    if response.status_code != 200:
        raise ToolError(
            "Hugging Face metadata request failed",
            endpoint=endpoint,
            status_code=response.status_code,
            body=response.text[:500],
        )
    data = response.json()
    if not isinstance(data, dict):
        raise ToolError("Hugging Face response was not an object", endpoint=endpoint)
    return data


def dataset_api_metadata(dataset: str) -> dict[str, Any]:
    data = hf_get_json(f"{HF_API}/{dataset}")
    return {
        "dataset": dataset,
        "sha": data.get("sha"),
        "last_modified": data.get("lastModified"),
        "private": data.get("private"),
        "gated": data.get("gated"),
        "disabled": data.get("disabled"),
    }


def split_row_count(size_payload: Mapping[str, Any], *, dataset: str, split: str) -> int:
    size = size_payload.get("size") if isinstance(size_payload.get("size"), Mapping) else {}
    splits = size.get("splits") if isinstance(size.get("splits"), list) else []
    for row in splits:
        if not isinstance(row, Mapping):
            continue
        if row.get("dataset") == dataset and row.get("config") == "default" and row.get("split") == split:
            value = row.get("num_rows")
            if isinstance(value, int):
                return value
    raise ToolError("dataset split row count was unavailable", dataset=dataset, split=split)


def fetch_dataset_rows(dataset: str, *, split: str) -> list[dict[str, Any]]:
    size_payload = hf_get_json(f"{HF_DATASET_SERVER}/size", params={"dataset": dataset})
    total = split_row_count(size_payload, dataset=dataset, split=split)
    rows: list[dict[str, Any]] = []
    for offset in range(0, total, HF_PAGE_SIZE):
        payload = hf_get_json(
            f"{HF_DATASET_SERVER}/rows",
            params={
                "dataset": dataset,
                "config": "default",
                "split": split,
                "offset": offset,
                "length": min(HF_PAGE_SIZE, total - offset),
            },
            timeout=60,
        )
        page_rows = payload.get("rows")
        if not isinstance(page_rows, list):
            raise ToolError("dataset rows payload was missing rows", dataset=dataset, offset=offset)
        for item in page_rows:
            if isinstance(item, Mapping) and isinstance(item.get("row"), Mapping):
                rows.append(dict(item["row"]))
    if len(rows) != total:
        raise ToolError("fetched dataset row count mismatch", dataset=dataset, expected=total, actual=len(rows))
    return rows


def patch_paths(patch_text: object) -> list[str]:
    if not isinstance(patch_text, str):
        return []
    paths: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3]
                if path.startswith("b/"):
                    paths.append(path[2:])
        elif line.startswith("+++ b/"):
            paths.append(line[len("+++ b/") :])
    return sorted(set(path for path in paths if path and path != "/dev/null"))


def external_family(repo_id: str, row: Mapping[str, Any]) -> str:
    text = " ".join(
        [
            str(row.get("instance_id", "")),
            str(row.get("problem_statement", ""))[:1200],
            " ".join(patch_paths(row.get("patch"))),
            " ".join(patch_paths(row.get("test_patch"))),
        ]
    ).lower()
    if repo_id == "sympy/sympy":
        if any(token in text for token in ("assum", "predicate", "ask.py", "refine")):
            return "assumptions/predicates"
        if any(token in text for token in ("matrix", "matrices")):
            return "matrices/linear algebra"
        if any(token in text for token in ("polys", "numberfield", "diophantine", "ntheory", "prime")):
            return "polys/number theory"
        if any(token in text for token in ("integral", "calculus", "solve", "ode", "series", "limit")):
            return "calculus/integration/solving"
        if any(token in text for token in ("printing", "parser", "latex", "codegen", "pretty")):
            return "printing/parsing/syntax"
        if any(token in text for token in ("simplify", "canonical", "rewrite", "expand", "trig", "factor")):
            return "expression simplification/canonicalization"
        return "core/mixed"
    if repo_id == "django/django":
        if any(token in text for token in ("model", "queryset", "orm", "migration")):
            return "models/orm/migrations"
        if any(token in text for token in ("admin", "form", "widget")):
            return "admin/forms/widgets"
        if any(token in text for token in ("url", "view", "request", "response")):
            return "urls/views/http"
        if any(token in text for token in ("template", "translation", "locale")):
            return "templates/i18n"
        return "core/mixed"
    if repo_id == "sphinx-doc/sphinx":
        if any(token in text for token in ("builder", "html", "latex", "toctree")):
            return "builders/output"
        if any(token in text for token in ("domain", "directive", "role", "autodoc")):
            return "domains/directives/autodoc"
        if any(token in text for token in ("parser", "rst", "docutils")):
            return "parsing/docutils"
        if any(token in text for token in ("config", "extension")):
            return "config/extensions"
        return "core/mixed"
    return "core/mixed"


def redacted_external_task(row: Mapping[str, Any], repo_id: str) -> dict[str, Any]:
    instance_id = str(row.get("instance_id", ""))
    problem = str(row.get("problem_statement", ""))
    base_commit = str(row.get("base_commit", ""))
    return {
        "instance_id_digest": digest_parts(repo_id, instance_id),
        "base_commit_digest": digest_parts(repo_id, base_commit) if base_commit else None,
        "problem_statement_digest": sha256_text(problem) if problem else None,
        "family": external_family(repo_id, row),
        "patch_file_count": len(patch_paths(row.get("patch"))),
        "test_patch_file_count": len(patch_paths(row.get("test_patch"))),
    }


def summarize_external_dataset(dataset_key: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    spec = DATASETS[dataset_key]
    repo_counts: Counter[str] = Counter(str(row.get("repo", "")) for row in rows if row.get("repo"))
    repo_summaries: dict[str, Any] = {}
    for repo_slug, repo_spec in REPOSITORIES.items():
        repo_id = str(repo_spec["repo_id"])
        repo_rows = [row for row in rows if row.get("repo") == repo_id]
        families = Counter(external_family(repo_id, row) for row in repo_rows)
        repo_summaries[repo_slug] = {
            "repo_id": repo_id,
            "task_count": len(repo_rows),
            "family_counts": dict(sorted(families.items())),
            "sample_task_digests": [redacted_external_task(row, repo_id) for row in repo_rows[:10]],
        }
    return {
        "dataset": spec["dataset"],
        "split": spec["split"],
        "role": spec["role"],
        "total_rows": len(rows),
        "repo_counts": dict(sorted(repo_counts.items())),
        "candidate_repo_summaries": repo_summaries,
    }


def is_source_file(repo_slug: str, file_path: str) -> bool:
    spec = REPOSITORIES[repo_slug]
    if not file_path.endswith(".py"):
        return False
    if not any(file_path.startswith(prefix) for prefix in spec["source_prefixes"]):
        return False
    return not is_test_file(repo_slug, file_path)


def is_test_file(repo_slug: str, file_path: str) -> bool:
    if not file_path.endswith(".py"):
        return False
    if repo_slug == "sympy":
        return file_path.startswith("sympy/") and "/tests/" in file_path
    spec = REPOSITORIES[repo_slug]
    return any(file_path.startswith(prefix) for prefix in spec["test_prefixes"])


def is_docs_or_meta(file_path: str) -> bool:
    lowered = file_path.lower()
    return (
        lowered.startswith(("docs/", "doc/", ".github/", "requirements/", "changelog", "changes/", "news/"))
        or lowered in {"readme.md", "changelog.md", "pyproject.toml", "tox.ini", "uv.lock", "setup.cfg"}
        or lowered.endswith((".md", ".rst", ".txt", ".yml", ".yaml", ".toml", ".ini"))
    )


def candidate_surface(repo_slug: str, files: Sequence[str]) -> str:
    has_source = any(is_source_file(repo_slug, path) for path in files)
    has_tests = any(is_test_file(repo_slug, path) for path in files)
    if has_source and has_tests:
        return "source_and_tests"
    if has_source:
        return "source_without_tests"
    if has_tests:
        return "tests_without_source"
    if files and all(is_docs_or_meta(path) for path in files):
        return "docs_or_meta_only"
    return "other"


def task_design_surface(surface: str) -> bool:
    return surface in {"source_and_tests", "source_without_tests"}


def subject_is_low_signal(subject: str) -> bool:
    lowered = subject.lower()
    return any(fragment in lowered for fragment in LOW_SIGNAL_SUBJECT_FRAGMENTS)


def classify_candidate_family(repo_slug: str, subject: str, files: Sequence[str]) -> str:
    text = " ".join([subject, *files]).lower()
    if repo_slug == "sympy":
        if "assum" in text or "predicate" in text or "refine" in text:
            return "assumptions/predicates"
        if "matrices" in text or "matrix" in text:
            return "matrices/linear algebra"
        if "polys" in text or "ntheory" in text or "number" in text:
            return "polys/number theory"
        if "integral" in text or "solve" in text or "ode" in text or "calculus" in text or "series" in text:
            return "calculus/integration/solving"
        if "printing" in text or "parsing" in text or "latex" in text or "pretty" in text:
            return "printing/parsing/syntax"
        if "simplify" in text or "expand" in text or "factor" in text or "rewrite" in text:
            return "expression simplification/canonicalization"
        return "core/mixed"
    if repo_slug == "django":
        if "models" in text or "query" in text or "orm" in text or "migration" in text:
            return "models/orm/migrations"
        if "admin" in text or "form" in text or "widget" in text:
            return "admin/forms/widgets"
        if "url" in text or "views" in text or "request" in text or "response" in text:
            return "urls/views/http"
        if "template" in text or "locale" in text or "translation" in text:
            return "templates/i18n"
        return "core/mixed"
    if repo_slug == "sphinx":
        if "builder" in text or "html" in text or "latex" in text or "toctree" in text:
            return "builders/output"
        if "domain" in text or "directive" in text or "autodoc" in text or "role" in text:
            return "domains/directives/autodoc"
        if "parser" in text or "docutils" in text or "rst" in text:
            return "parsing/docutils"
        if "config" in text or "extension" in text:
            return "config/extensions"
        return "core/mixed"
    return "core/mixed"


def changed_files(repo_path: Path, commit: str) -> list[str]:
    completed = run_git(repo_path, "diff-tree", "--no-commit-id", "--name-only", "-r", commit, timeout=60)
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def commit_rows(repo_path: Path, *, since: dt.datetime, until: dt.datetime) -> list[dict[str, str]]:
    completed = run_git(
        repo_path,
        "log",
        "--no-merges",
        f"--since={since.isoformat()}",
        f"--until={until.isoformat()}",
        "--format=%H%x00%cI%x00%s",
        timeout=180,
    )
    if completed.returncode != 0:
        raise ToolError("failed to scan git history", repo=repo_relative(repo_path), stderr=completed.stderr[-600:])
    rows: list[dict[str, str]] = []
    for line in completed.stdout.splitlines():
        parts = line.split("\x00", 2)
        if len(parts) == 3:
            rows.append({"commit": parts[0], "committed_at": parts[1], "subject": parts[2]})
    return rows


def commit_rows_with_files(repo_path: Path, *, since: dt.datetime, until: dt.datetime) -> list[dict[str, Any]]:
    completed = run_git(
        repo_path,
        "log",
        "--no-merges",
        f"--since={since.isoformat()}",
        f"--until={until.isoformat()}",
        "--format=%x1e%H%x00%cI%x00%s",
        "--name-only",
        timeout=240,
    )
    if completed.returncode != 0:
        raise ToolError("failed to scan git history with files", repo=repo_relative(repo_path), stderr=completed.stderr[-600:])
    rows: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    # str.splitlines treats ASCII record separator (\x1e) as a line break.
    # Split only on LF so the commit marker remains attached to header lines.
    for raw_line in completed.stdout.split("\n"):
        if raw_line.startswith("\x1e"):
            if current is not None:
                rows.append(current)
            parts = raw_line[1:].split("\x00", 2)
            if len(parts) != 3:
                current = None
                continue
            current = {"commit": parts[0], "committed_at": parts[1], "subject": parts[2], "files": []}
            continue
        if current is not None:
            path = raw_line.strip()
            if path:
                current["files"].append(path)
    if current is not None:
        rows.append(current)
    return rows


def summarize_candidate_window(repo_slug: str, repo_path: Path, *, since: dt.datetime, until: dt.datetime) -> dict[str, Any]:
    rows = commit_rows_with_files(repo_path, since=since, until=until)
    surfaces: Counter[str] = Counter()
    families: Counter[str] = Counter()
    direct_candidates: list[dict[str, Any]] = []
    design_candidates: list[dict[str, Any]] = []
    low_signal_count = 0
    for row in rows:
        files = list(row.get("files", []))
        surface = candidate_surface(repo_slug, files)
        low_signal = subject_is_low_signal(row["subject"])
        if low_signal:
            low_signal_count += 1
        surfaces[surface] += 1
        if low_signal or not task_design_surface(surface):
            continue
        family = classify_candidate_family(repo_slug, row["subject"], files)
        families[family] += 1
        item = {
            "source_anchor_digest": digest_parts(repo_slug, row["commit"]),
            "committed_at": row["committed_at"],
            "family": family,
            "surface": surface,
            "changed_file_count": len(files),
            "changed_python_file_count": sum(1 for path in files if path.endswith(".py")),
            "subject_digest": sha256_text(row["subject"]),
        }
        design_candidates.append(item)
        if surface == "source_and_tests":
            direct_candidates.append(item)
    return {
        "window_start": since.date().isoformat(),
        "window_end": until.date().isoformat(),
        "non_merge_commit_count": len(rows),
        "surface_counts": dict(sorted(surfaces.items())),
        "low_signal_subject_count": low_signal_count,
        "source_and_tests_candidate_count": len(direct_candidates),
        "task_design_candidate_count": len(design_candidates),
        "family_counts": dict(sorted(families.items())),
        "family_count": len(families),
        "sample_candidate_digests": design_candidates[:10],
    }


def repo_metadata(repo_slug: str, repo_path: Path) -> dict[str, Any]:
    head = require_git(repo_path, "rev-parse", "HEAD")
    head_date = require_git(repo_path, "log", "-1", "--format=%cI")
    origin = run_git(repo_path, "remote", "get-url", "origin")
    return {
        "path": repo_relative(repo_path),
        "head_digest": digest_parts(repo_slug, head),
        "head_committed_at": head_date,
        "origin": origin.stdout.strip() if origin.returncode == 0 else None,
    }


def discover_test_surface(repo_path: Path) -> dict[str, Any]:
    return {
        "pyproject_exists": (repo_path / "pyproject.toml").exists(),
        "tests_dir_exists": (repo_path / "tests").exists(),
        "tox_ini_exists": (repo_path / "tox.ini").exists(),
        "requirements_dev_exists": (repo_path / "requirements-dev.txt").exists(),
    }


def command_available(command: str) -> bool:
    return shutil.which(command) is not None


def docker_available() -> bool:
    if not command_available("docker"):
        return False
    completed = run_command(["docker", "ps"], timeout=30)
    return completed.returncode == 0


def swebench_module_available() -> bool:
    completed = run_command([sys.executable, "-c", "import swebench"], timeout=30)
    return completed.returncode == 0


def repo_phase0_summary(
    repo_slug: str,
    *,
    external_summaries: Mapping[str, Any],
    docker_ok: bool,
    swebench_ok: bool,
    smoke_summary: Mapping[str, Any] | None,
    b_admission_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    spec = REPOSITORIES[repo_slug]
    repo_id = str(spec["repo_id"])
    repo_path = Path(spec["path"])
    if not (repo_path / ".git").exists():
        return {
            "repo_slug": repo_slug,
            "repo_id": repo_id,
            "recommendation": "reject",
            "blockers": ["repository_checkout_missing"],
            "path": repo_relative(repo_path),
        }

    verified = (
        external_summaries.get("swebench_verified", {})
        .get("candidate_repo_summaries", {})
        .get(repo_slug, {})
    )
    full = (
        external_summaries.get("swebench_full", {})
        .get("candidate_repo_summaries", {})
        .get(repo_slug, {})
    )
    windows = {
        "recent_12m": summarize_candidate_window(repo_slug, repo_path, since=RECENT_WINDOW_START, until=T0),
        "extended_24m": summarize_candidate_window(repo_slug, repo_path, since=EXTENDED_WINDOW_START, until=T0),
    }
    recent = windows["recent_12m"]
    external_verified_count = int(verified.get("task_count", 0) or 0)
    external_full_count = int(full.get("task_count", 0) or 0)
    task_design_count = int(recent.get("task_design_candidate_count", 0) or 0)
    direct_count = int(recent.get("source_and_tests_candidate_count", 0) or 0)
    family_count = int(recent.get("family_count", 0) or 0)
    metadata_ready = external_verified_count >= 30 and task_design_count >= 40 and family_count >= 4
    direct_oracle_supply_ready = direct_count >= 20
    b_summary_applies = repo_slug == "sympy" and isinstance(b_admission_summary, Mapping)
    b_primary_count = int(b_admission_summary.get("primary_task_count", 0) or 0) if b_summary_applies else 0
    b_reserve_count = int(b_admission_summary.get("reserve_task_count", 0) or 0) if b_summary_applies else 0
    b_accepted_count = int(b_admission_summary.get("accepted_count", 0) or 0) if b_summary_applies else 0
    b_candidate_count = int(b_admission_summary.get("candidate_count", 0) or 0) if b_summary_applies else 0
    b_reference_rate = b_admission_summary.get("reference_patch_pass_rate") if b_summary_applies else None
    b_noop_rate = b_admission_summary.get("noop_fail_rate") if b_summary_applies else None
    primary_tasks = b_admission_summary.get("primary_tasks", []) if b_summary_applies else []
    primary_reference_rate = None
    primary_noop_rate = None
    if isinstance(primary_tasks, list) and primary_tasks:
        primary_reference_rate = sum(
            1 for task in primary_tasks if isinstance(task, Mapping) and task.get("reference_patch_passes") is True
        ) / len(primary_tasks)
        primary_noop_rate = sum(
            1 for task in primary_tasks if isinstance(task, Mapping) and task.get("no_op_fails") is True
        ) / len(primary_tasks)
    blockers: list[str] = []
    if external_verified_count < 30:
        blockers.append("verified_external_task_count_below_30")
    if task_design_count < 40:
        blockers.append("recent_task_design_candidate_count_below_40")
    if family_count < 4:
        blockers.append("recent_task_design_family_count_below_4")
    if not direct_oracle_supply_ready:
        blockers.append("recent_source_and_tests_direct_oracle_count_below_20")
    if not swebench_ok:
        blockers.append("official_swebench_python_harness_not_installed")
    if not docker_ok:
        blockers.append("docker_not_available_for_external_eval_smoke")
    smoke_applies = (
        isinstance(smoke_summary, Mapping)
        and smoke_summary.get("repo") == repo_id
        and smoke_summary.get("benchmark_source") == "SWE-bench/SWE-bench_Verified"
    )
    smoke_pass = bool(smoke_applies and smoke_summary.get("pass") is True)
    smoke_sample_size = smoke_summary.get("total_instances_requested") if smoke_applies else 0
    smoke_resolved_count = int(smoke_summary.get("resolved_instances", 0) or 0) if smoke_applies else 0
    denominator_smoke_ready = smoke_pass and isinstance(smoke_sample_size, int) and smoke_sample_size >= 30 and smoke_resolved_count >= 30
    if denominator_smoke_ready:
        if b_primary_count >= 20:
            smoke_limitation = (
                f"A {smoke_sample_size}-instance gold smoke measured the usable external slice for Phase 1; "
                f"B primary is frozen, with full candidate-pool no-op fail rate {b_noop_rate}."
            )
        else:
            smoke_limitation = (
                f"A {smoke_sample_size}-instance gold smoke measured the usable external slice for Phase 1; "
                "B reference/no-op verifier evidence is still pending."
            )
        denominator_limitation = (
            f"Denominator-scale SWE-bench container smoke passed for {smoke_resolved_count} external task(s); "
            "after-infra-smoke E count is measured for this slice."
        )
    elif smoke_pass and isinstance(smoke_sample_size, int) and smoke_sample_size > 0:
        smoke_limitation = (
            f"A {smoke_sample_size}-instance gold smoke confirms harness plumbing only; "
            "it does not establish the usable E denominator."
        )
        denominator_limitation = "Denominator-scale SWE-bench container infra smoke has not run; after-infra-smoke counts remain unset."
    else:
        smoke_limitation = (
            "A passing gold smoke is not yet available for this repository; "
            "it does not establish the usable E denominator."
        )
        denominator_limitation = "Denominator-scale SWE-bench container infra smoke has not run; after-infra-smoke counts remain unset."
    recommendation = "backup"
    if not metadata_ready:
        recommendation = "reject"
    elif repo_slug == "sympy":
        if denominator_smoke_ready and b_primary_count >= 20:
            recommendation = (
                "primary_external_and_b_frozen_candidate_noop_gate_weak"
                if isinstance(b_noop_rate, (int, float)) and b_noop_rate < 0.9
                else "primary_external_and_b_frozen"
            )
        elif denominator_smoke_ready:
            recommendation = "primary_for_b_generation_pending_b_admission"
        else:
            recommendation = "primary_pending_infra_smoke"
    return {
        "repo_slug": repo_slug,
        "repo_id": repo_id,
        "external_benchmark_source": "SWE-bench Verified primary; SWE-bench Full fallback",
        "external_task_count_total": external_full_count,
        "external_task_count_verified": external_verified_count,
        "external_task_count_after_infra_smoke": smoke_resolved_count if denominator_smoke_ready else None,
        "external_task_family_sketch": verified.get("family_counts", {}),
        "external_eval_harness_available": bool(docker_ok and swebench_ok),
        "external_eval_smoke_pass_rate": 1.0 if smoke_pass else None,
        "external_eval_smoke_sample_size": smoke_sample_size,
        "external_eval_smoke_summary_path": repo_relative(DEFAULT_SMOKE_SUMMARY) if smoke_applies else None,
        "barcarolle_candidate_task_count": task_design_count,
        "barcarolle_direct_oracle_candidate_count": direct_count,
        "barcarolle_candidate_windows": windows,
        "barcarolle_admission_candidate_count": b_candidate_count if b_summary_applies else None,
        "barcarolle_admitted_candidate_count": b_accepted_count if b_summary_applies else None,
        "barcarolle_primary_b_task_count": b_primary_count if b_summary_applies else None,
        "barcarolle_reserve_b_task_count": b_reserve_count if b_summary_applies else None,
        "barcarolle_reference_smoke_pass_rate": b_reference_rate,
        "barcarolle_noop_fail_rate": b_noop_rate,
        "barcarolle_primary_reference_smoke_pass_rate": primary_reference_rate,
        "barcarolle_primary_noop_fail_rate": primary_noop_rate,
        "barcarolle_b_admission_summary_path": repo_relative(DEFAULT_B_ADMISSION_SUMMARY) if b_summary_applies else None,
        "test_runtime_median": None,
        "test_runtime_p90": None,
        "dependency_failure_rate": None,
        "network_dependency_risk": "low_for_smoked_external_slice" if denominator_smoke_ready else "medium_until_official_swebench_container_smoke_runs",
        "metadata": repo_metadata(repo_slug, repo_path),
        "test_surface": discover_test_surface(repo_path),
        "metadata_ready_for_infra_smoke": metadata_ready,
        "direct_oracle_supply_ready": direct_oracle_supply_ready,
        "recommendation": recommendation,
        "blockers": blockers,
        "limitations": [
            "This Phase 0 artifact freezes external dataset counts and local repository history supply only.",
            denominator_limitation,
            smoke_limitation,
            (
                f"Barcarolle B primary is frozen with {b_primary_count} task(s), but full candidate-pool no-op fail rate is {b_noop_rate}."
                if b_primary_count >= 20
                else "Barcarolle reference/no-op verifier pass rates require Phase 1 task construction and are not inferred from history supply."
            ),
            "External rows are summarized with digests and family labels; patch, test patch, problem statement, and raw commit values are not emitted.",
        ],
    }


def build_recommendation(repositories: Sequence[Mapping[str, Any]], *, smoke_summary: Mapping[str, Any] | None) -> dict[str, Any]:
    metadata_ready = [repo for repo in repositories if repo.get("metadata_ready_for_infra_smoke")]
    metadata_ready.sort(
        key=lambda repo: (
            int(REPOSITORIES.get(str(repo.get("repo_slug")), {}).get("recommendation_priority", 99)),
            -int(repo.get("external_task_count_verified", 0) or 0),
            -int(repo.get("barcarolle_candidate_task_count", 0) or 0),
        )
    )
    primary = metadata_ready[0].get("repo_slug") if metadata_ready else None
    sympy = next((repo for repo in repositories if repo.get("repo_slug") == "sympy"), {})
    smoke_pass = bool(isinstance(smoke_summary, Mapping) and smoke_summary.get("pass") is True)
    external_count_after_smoke = int(sympy.get("external_task_count_after_infra_smoke", 0) or 0)
    b_primary_count = int(sympy.get("barcarolle_primary_b_task_count", 0) or 0)
    b_noop_rate = sympy.get("barcarolle_noop_fail_rate")
    b_reference_rate = sympy.get("barcarolle_reference_smoke_pass_rate")
    remaining = []
    if b_primary_count < 20:
        remaining.append("barcarolle_reference_smoke_pass_rate and no-op fail rate require generated task candidates")
    elif not (isinstance(b_reference_rate, (int, float)) and b_reference_rate >= 0.9):
        remaining.append("barcarolle_reference_smoke_pass_rate is below 90% for evaluated candidates")
    elif not (isinstance(b_noop_rate, (int, float)) and b_noop_rate >= 0.9):
        remaining.append("barcarolle_noop_fail_rate is below 90% for evaluated candidates")
    else:
        remaining.append("barcarolle_primary_B_denominator_frozen")
    if external_count_after_smoke < 30:
        remaining.insert(0, "external_task_count_after_infra_smoke is not measured for the target E denominator")
    if not smoke_pass:
        remaining.insert(1, "external_eval_smoke_pass_rate is not measured")
    else:
        sample_size = smoke_summary.get("total_instances_requested") if isinstance(smoke_summary, Mapping) else None
        if external_count_after_smoke >= 30:
            remaining.insert(0, f"external_eval_smoke established {external_count_after_smoke} usable E task(s)")
        elif isinstance(sample_size, int) and sample_size > 0:
            remaining.insert(1, f"external_eval_smoke covers {sample_size} gold instance(s) only")
        else:
            remaining.insert(1, "external_eval_smoke covers a non-denominator gold sample only")
    phase0_status = (
        "external_and_b_primary_frozen_candidate_noop_gate_weak"
        if external_count_after_smoke >= 30 and b_primary_count >= 20 and isinstance(b_noop_rate, (int, float)) and b_noop_rate < 0.9
        else "external_and_b_primary_frozen"
        if external_count_after_smoke >= 30 and b_primary_count >= 20
        else "external_infra_smoke_completed_b_admission_pending"
        if external_count_after_smoke >= 30
        else "metadata_preflight_completed_infra_smoke_pending"
    )
    return {
        "phase0_status": phase0_status,
        "recommended_next_repo_for_infra_smoke": primary,
        "recommended_primary_repo_for_b_generation": primary if external_count_after_smoke >= 30 else None,
        "primary_repo_can_be_declared": bool(
            external_count_after_smoke >= 30
            and b_primary_count >= 20
            and isinstance(b_reference_rate, (int, float))
            and b_reference_rate >= 0.9
            and isinstance(b_noop_rate, (int, float))
            and b_noop_rate >= 0.9
        ),
        "why_not_final_admission": remaining,
        "sympy_metadata_ready_for_infra_smoke": sympy.get("metadata_ready_for_infra_smoke"),
        "basis": "Choose the first protocol-priority repo with >=30 Verified tasks, >=40 recent task-design candidates, and >=4 recent candidate families. Final admission requires official SWE-bench smoke plus B verifier gates or an explicit documented gate decision.",
    }


def load_smoke_summary() -> dict[str, Any] | None:
    if not DEFAULT_SMOKE_SUMMARY.exists():
        return None
    try:
        payload = json.loads(DEFAULT_SMOKE_SUMMARY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolError("failed to load SWE-bench smoke summary", path=repo_relative(DEFAULT_SMOKE_SUMMARY), cause=str(exc)) from exc
    if not isinstance(payload, dict):
        raise ToolError("SWE-bench smoke summary must be an object", path=repo_relative(DEFAULT_SMOKE_SUMMARY))
    return payload


def load_b_admission_summary() -> dict[str, Any] | None:
    if not DEFAULT_B_ADMISSION_SUMMARY.exists():
        return None
    try:
        payload = json.loads(DEFAULT_B_ADMISSION_SUMMARY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolError("failed to load B admission summary", path=repo_relative(DEFAULT_B_ADMISSION_SUMMARY), cause=str(exc)) from exc
    if not isinstance(payload, dict):
        raise ToolError("B admission summary must be an object", path=repo_relative(DEFAULT_B_ADMISSION_SUMMARY))
    return payload


def external_summaries_from_cache(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolError("failed to load external summary cache", path=repo_relative(path), cause=str(exc)) from exc
    external = payload.get("external_dataset_sources") if isinstance(payload, Mapping) else None
    if not isinstance(external, Mapping):
        raise ToolError("external summary cache is missing external_dataset_sources", path=repo_relative(path))
    missing = [key for key in DATASETS if key not in external]
    if missing:
        raise ToolError("external summary cache is missing required datasets", path=repo_relative(path), missing=missing)
    return dict(external)


def fetch_external_summaries(skip_hf: bool, *, cache_path: Path | None = None) -> dict[str, Any]:
    if cache_path is not None:
        return external_summaries_from_cache(cache_path)
    if skip_hf:
        return {
            key: {
                "dataset": spec["dataset"],
                "split": spec["split"],
                "role": spec["role"],
                "total_rows": None,
                "repo_counts": {},
                "candidate_repo_summaries": {
                    slug: {"repo_id": repo["repo_id"], "task_count": 0, "family_counts": {}, "sample_task_digests": []}
                    for slug, repo in REPOSITORIES.items()
                },
            }
            for key, spec in DATASETS.items()
        }
    summaries: dict[str, Any] = {}
    for key, spec in DATASETS.items():
        rows = fetch_dataset_rows(str(spec["dataset"]), split=str(spec["split"]))
        summary = summarize_external_dataset(key, rows)
        summary["dataset_metadata"] = dataset_api_metadata(str(spec["dataset"]))
        summaries[key] = summary
    return summaries


def build_payload(repo_slugs: Sequence[str], *, skip_hf: bool = False, external_summary_cache: Path | None = None) -> dict[str, Any]:
    external_summaries = fetch_external_summaries(skip_hf, cache_path=external_summary_cache)
    docker_ok = docker_available()
    swebench_ok = swebench_module_available()
    smoke_summary = load_smoke_summary()
    b_admission_summary = load_b_admission_summary()
    repositories = [
        repo_phase0_summary(
            slug,
            external_summaries=external_summaries,
            docker_ok=docker_ok,
            swebench_ok=swebench_ok,
            smoke_summary=smoke_summary,
            b_admission_summary=b_admission_summary,
        )
        for slug in repo_slugs
    ]
    recommendation = build_recommendation(repositories, smoke_summary=smoke_summary)
    if recommendation["phase0_status"] == "external_and_b_primary_frozen_candidate_noop_gate_weak":
        next_required_steps = [
            "Resolve the evaluated-candidate no-op fail-rate weakness before authorizing primary ACUT runs.",
            "Run a freeze integrity audit across E and B manifests.",
        ]
    elif recommendation["phase0_status"] == "external_and_b_primary_frozen":
        next_required_steps = [
            "Run a freeze integrity audit across E and B manifests before ACUT runs.",
            "Freeze ACUT profiles and execution manifests.",
        ]
    elif recommendation["phase0_status"] == "external_infra_smoke_completed_b_admission_pending":
        next_required_steps = [
            "Generate B candidates and run reference/no-op admission smokes before ACUT runs.",
            "Keep E results hidden from B task generation.",
        ]
    else:
        next_required_steps = [
            "Run a denominator-scale external infra smoke on the recommended repo before freezing E.",
            "Only after E task usability is known, generate B candidates and run reference/no-op admission smokes.",
        ]
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "protocol_id": PROTOCOL_ID,
        "status": recommendation["phase0_status"],
        "generated_at": iso_now(),
        "model_calls_made": 0,
        "external_dataset_sources": external_summaries,
        "local_infra": {
            "docker_available": docker_ok,
            "swebench_python_module_available": swebench_ok,
            "python_executable": sys.executable,
            "network_access_used_for_hf_metadata": not skip_hf,
            "codex_cli_version": codex_version(),
        },
        "swebench_gold_smoke": smoke_summary,
        "barcarolle_b_admission": b_admission_summary,
        "repositories": repositories,
        "recommendation": recommendation,
        "next_required_steps": next_required_steps,
    }


def codex_version() -> str | None:
    completed = run_command(["codex", "--version"], timeout=30) if command_available("codex") else None
    if completed is None or completed.returncode != 0:
        return None
    return completed.stdout.strip()


def render_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Phase 0 Repository Admission",
        "",
        f"Protocol: `{payload.get('protocol_id')}`",
        f"Status: `{payload.get('status')}`",
        f"Generated at: `{payload.get('generated_at')}`",
        "",
        "## External Dataset Snapshot",
        "",
        "| Dataset | Split | Total rows | Candidate repo counts | Revision |",
        "|---|---:|---:|---|---|",
    ]
    external = payload.get("external_dataset_sources") if isinstance(payload.get("external_dataset_sources"), Mapping) else {}
    for dataset_key in DATASETS:
        summary = external.get(dataset_key) if isinstance(external, Mapping) else None
        if not isinstance(summary, Mapping):
            continue
        metadata = summary.get("dataset_metadata") if isinstance(summary.get("dataset_metadata"), Mapping) else {}
        counts = []
        for repo_slug in REPOSITORIES:
            repo_summary = (
                summary.get("candidate_repo_summaries", {}).get(repo_slug, {})
                if isinstance(summary.get("candidate_repo_summaries"), Mapping)
                else {}
            )
            counts.append(f"`{repo_slug}`={repo_summary.get('task_count')}")
        lines.append(
            "| "
            f"`{summary.get('dataset')}` | "
            f"`{summary.get('split')}` | "
            f"{summary.get('total_rows')} | "
            f"{', '.join(counts)} | "
            f"`{metadata.get('sha')}` |"
        )
    lines.extend(
        [
            "",
            "## Candidate Repositories",
            "",
            "| Repo | Verified E | E after smoke | Full E | Recent B design | B primary | Ref pass | No-op fail | Recommendation | Blockers |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for repo in payload.get("repositories", []):
        if not isinstance(repo, Mapping):
            continue
        recent = (
            repo.get("barcarolle_candidate_windows", {}).get("recent_12m", {})
            if isinstance(repo.get("barcarolle_candidate_windows"), Mapping)
            else {}
        )
        blockers = ", ".join(str(item) for item in repo.get("blockers", [])) or "none"
        lines.append(
            "| "
            f"`{repo.get('repo_slug')}` | "
            f"{repo.get('external_task_count_verified')} | "
            f"{repo.get('external_task_count_after_infra_smoke')} | "
            f"{repo.get('external_task_count_total')} | "
            f"{repo.get('barcarolle_candidate_task_count')} | "
            f"{repo.get('barcarolle_primary_b_task_count')} | "
            f"{repo.get('barcarolle_reference_smoke_pass_rate')} | "
            f"{repo.get('barcarolle_noop_fail_rate')} | "
            f"`{repo.get('recommendation')}` | "
            f"{blockers} |"
        )
    infra = payload.get("local_infra") if isinstance(payload.get("local_infra"), Mapping) else {}
    recommendation = payload.get("recommendation") if isinstance(payload.get("recommendation"), Mapping) else {}
    lines.extend(
        [
            "",
            "## Local Infra",
            "",
            f"- Docker available: `{infra.get('docker_available')}`",
            f"- SWE-bench Python module available: `{infra.get('swebench_python_module_available')}`",
            f"- Codex CLI version: `{infra.get('codex_cli_version')}`",
            "",
        ]
    )
    smoke = payload.get("swebench_gold_smoke") if isinstance(payload.get("swebench_gold_smoke"), Mapping) else None
    if smoke is not None:
        raw_retained = smoke.get("raw_artifacts_retained")
        if raw_retained is None:
            redaction = smoke.get("redaction_policy") if isinstance(smoke.get("redaction_policy"), Mapping) else {}
            raw_retained = any(
                bool(redaction.get(key))
                for key in (
                    "raw_gold_patch_retained",
                    "raw_eval_script_retained",
                    "raw_test_output_retained",
                    "raw_instance_report_retained",
                )
            )
        lines.extend(
            [
                "## SWE-bench Gold Smoke",
                "",
                f"- Smoke id: `{smoke.get('smoke_id')}`",
                f"- Repo: `{smoke.get('repo')}`",
                f"- Instance ids: `{', '.join(str(item) for item in smoke.get('instance_ids', []))}`",
                f"- Completed/resolved/errors: `{smoke.get('completed_instances')}` / `{smoke.get('resolved_instances')}` / `{smoke.get('error_instances')}`",
                f"- Pass: `{smoke.get('pass')}`",
                f"- Raw gold patch/eval/test artifacts retained: `{raw_retained}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Recommendation",
            "",
            f"- Phase 0 status: `{recommendation.get('phase0_status')}`",
            f"- Next repo for infra smoke: `{recommendation.get('recommended_next_repo_for_infra_smoke')}`",
            f"- Primary repo for B generation: `{recommendation.get('recommended_primary_repo_for_b_generation')}`",
            f"- Final primary repo declared: `{recommendation.get('primary_repo_can_be_declared')}`",
            "",
            "## Boundary",
            "",
            "This artifact does not authorize ACUT runs. It keeps raw SWE-bench statements, patches, test patches, and commit SHAs out of the public artifact. If B admission is present, any remaining verifier-gate weakness must be resolved or explicitly accepted before primary execution.",
            "",
        ]
    )
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_slugs = args.repo or ["sympy", "django", "sphinx"]
    cache_path = Path(args.external_summary_cache) if args.external_summary_cache else None
    payload = build_payload(repo_slugs, skip_hf=bool(args.skip_hf), external_summary_cache=cache_path)
    output = Path(args.output)
    report = Path(args.report)
    write_json(output, payload)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(payload), encoding="utf-8")
    emit_json({**payload, "output_path": repo_relative(output), "report_path": repo_relative(report)})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
