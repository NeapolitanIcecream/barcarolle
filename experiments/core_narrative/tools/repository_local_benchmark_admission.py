#!/usr/bin/env python3
"""Scan candidate repositories for the Barcarolle repository-local benchmark line."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, write_json


TOOL = "repository_local_benchmark_admission"
SCHEMA_VERSION = "core-narrative.repository-local-admission.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
T0 = dt.datetime(2026, 5, 14, 23, 59, 59, tzinfo=dt.timezone.utc)
CUTOFF_C_END = dt.datetime(2025, 11, 13, 23, 59, 59, tzinfo=dt.timezone.utc)
R_START = dt.datetime(2025, 11, 14, 0, 0, 0, tzinfo=dt.timezone.utc)
R_END = dt.datetime(2026, 2, 13, 23, 59, 59, tzinfo=dt.timezone.utc)
W_STAR_START = dt.datetime(2026, 2, 14, 0, 0, 0, tzinfo=dt.timezone.utc)
EXTENDED_R_START = dt.datetime(2025, 5, 14, 0, 0, 0, tzinfo=dt.timezone.utc)

DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/repository_local_benchmark_admission_20260514.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-14_repository_local_benchmark_admission.md"

REPOSITORIES = {
    "click": {
        "repo_slug": "click",
        "repository": "pallets/click",
        "path": REPO_ROOT / "experiments/core_narrative/external_repos/click",
        "language": "python",
        "test_command": "python -m pytest -q",
        "source_prefixes": ("src/click/", "click/"),
        "test_prefixes": ("tests/",),
        "role": "primary_evidence_candidate",
    },
    "rich": {
        "repo_slug": "rich",
        "repository": "Textualize/rich",
        "path": REPO_ROOT / "experiments/core_narrative/external_repos/rich",
        "language": "python",
        "test_command": "python -m pytest -q",
        "source_prefixes": ("rich/",),
        "test_prefixes": ("tests/",),
        "role": "replication_candidate",
    },
    "black": {
        "repo_slug": "black",
        "repository": "psf/black",
        "path": REPO_ROOT / "experiments/core_narrative/external_repos/black",
        "language": "python",
        "test_command": "python -m pytest -q",
        "source_prefixes": ("src/black/", "src/blib2to3/", "black/", "blib2to3/"),
        "test_prefixes": ("tests/",),
        "role": "replication_fallback_candidate",
    },
}

SKIP_SUBJECT_FRAGMENTS = (
    "release",
    "changelog",
    "pre-commit",
    "precommit",
    "codespell",
    "ruff",
    "mypy",
    "pyright",
    "format guidelines",
    "documentation",
    "docs:",
    "dependency",
    "dependencies",
    "update dev",
    "workflow",
    "ci",
    "publish",
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Structured JSON output.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Markdown report output.")
    parser.add_argument("--repo", action="append", choices=sorted(REPOSITORIES), help="Limit scan to one or more repos.")
    return parser.parse_args(list(argv) if argv is not None else None)


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def run_git(repo_path: Path, *args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def require_git(repo_path: Path, *args: str, timeout: int = 120) -> str:
    completed = run_git(repo_path, *args, timeout=timeout)
    if completed.returncode != 0:
        raise ToolError("git command failed", repo=str(repo_path), args=list(args), stderr=completed.stderr[-500:])
    return completed.stdout.strip()


def parse_git_datetime(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def window_for_date(value: str) -> str:
    when = parse_git_datetime(value)
    if when <= CUTOFF_C_END:
        return "C"
    if R_START <= when <= R_END:
        return "R"
    if W_STAR_START <= when <= T0:
        return "W_star"
    if when > T0:
        return "future"
    return "gap"


def anchor_digest(repo_slug: str, commit: str) -> str:
    return hashlib.sha256(f"{repo_slug}\n{commit}".encode("utf-8")).hexdigest()


def is_source_file(repo_slug: str, file_path: str) -> bool:
    spec = REPOSITORIES[repo_slug]
    return file_path.endswith(".py") and any(file_path.startswith(prefix) for prefix in spec["source_prefixes"])


def is_test_file(repo_slug: str, file_path: str) -> bool:
    spec = REPOSITORIES[repo_slug]
    return file_path.endswith(".py") and any(file_path.startswith(prefix) for prefix in spec["test_prefixes"])


def is_docs_or_meta(file_path: str) -> bool:
    return (
        file_path.startswith(("docs/", ".github/", "requirements/", "changelog", "changes/", "news/"))
        or file_path.lower() in {"readme.md", "changelog.md", "pyproject.toml", "tox.ini", "uv.lock"}
        or file_path.endswith((".md", ".rst", ".txt", ".yml", ".yaml", ".toml"))
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
    return any(fragment in lowered for fragment in SKIP_SUBJECT_FRAGMENTS)


def classify_family(repo_slug: str, subject: str, files: Sequence[str]) -> str:
    text = " ".join([subject, *files]).lower()
    if repo_slug == "click":
        if "clirunner" in text or "testing.py" in text or "stderr" in text or "stdout" in text:
            return "CliRunner/testing/input-output isolation"
        if "choice" in text or "datetime" in text or "types.py" in text or "paramtype" in text or "normaliz" in text:
            return "type conversion/parameter normalization"
        if "prompt" in text or "termui" in text or "pager" in text or "echo" in text or "color" in text:
            return "prompt/termui/output rendering"
        if "default" in text or "envvar" in text or "flag" in text or "option" in text or "help" in text:
            return "option/default/envvar/flag semantics"
        return "parser/mixed integration"
    if repo_slug == "rich":
        if "progress" in text or "live" in text or "status" in text:
            return "progress/live/status rendering"
        if "console" in text or "terminal" in text or "ansi" in text or "color" in text:
            return "console/rendering"
        if "markup" in text or "text.py" in text or "emoji" in text:
            return "markup/text/emoji"
        if "table" in text or "panel" in text or "layout" in text or "columns" in text:
            return "table/panel/layout"
        if "traceback" in text or "logging" in text or "inspect" in text:
            return "traceback/logging/inspect"
        return "parser/mixed integration"
    if repo_slug == "black":
        if "format" in text or "fmt" in text or "linegen" in text or "bracket" in text:
            return "formatting behavior"
        if "parser" in text or "grammar" in text or "blib2to3" in text or "ast" in text:
            return "parser/AST"
        if "mode" in text or "config" in text or "preview" in text or "pyproject" in text:
            return "mode/config semantics"
        if "cache" in text or "filesystem" in text or "files.py" in text:
            return "cache/filesystem"
        if "cli" in text or "click" in text or "__main__" in text:
            return "CLI/integration"
        return "fixtures/mixed integration"
    return "mixed"


def changed_files(repo_path: Path, commit: str) -> list[str]:
    completed = run_git(repo_path, "diff-tree", "--no-commit-id", "--name-only", "-r", commit)
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
        raise ToolError("failed to scan git history", repo=str(repo_path), stderr=completed.stderr[-500:])
    rows: list[dict[str, str]] = []
    for line in completed.stdout.splitlines():
        parts = line.split("\x00", 2)
        if len(parts) == 3:
            rows.append({"commit": parts[0], "committed_at": parts[1], "subject": parts[2]})
    return rows


def summarize_window(repo_slug: str, repo_path: Path, *, since: dt.datetime, until: dt.datetime) -> dict[str, Any]:
    rows = commit_rows(repo_path, since=since, until=until)
    surfaces: Counter[str] = Counter()
    families: Counter[str] = Counter()
    design_families: Counter[str] = Counter()
    low_signal_count = 0
    candidates: list[dict[str, Any]] = []
    design_candidates: list[dict[str, Any]] = []
    for row in rows:
        files = changed_files(repo_path, row["commit"])
        surface = candidate_surface(repo_slug, files)
        low_signal = subject_is_low_signal(row["subject"])
        if low_signal:
            low_signal_count += 1
        surfaces[surface] += 1
        if surface == "source_and_tests" and not low_signal:
            family = classify_family(repo_slug, row["subject"], files)
            families[family] += 1
            candidates.append(
                {
                    "source_anchor_digest": anchor_digest(repo_slug, row["commit"]),
                    "committed_at": row["committed_at"],
                    "family": family,
                    "surface": surface,
                    "changed_file_count": len(files),
                    "changed_python_file_count": sum(1 for path in files if path.endswith(".py")),
                    "subject_digest": hashlib.sha256(row["subject"].encode("utf-8")).hexdigest(),
                }
            )
        if task_design_surface(surface) and not low_signal:
            family = classify_family(repo_slug, row["subject"], files)
            design_families[family] += 1
            design_candidates.append(
                {
                    "source_anchor_digest": anchor_digest(repo_slug, row["commit"]),
                    "committed_at": row["committed_at"],
                    "family": family,
                    "surface": surface,
                    "changed_file_count": len(files),
                    "changed_python_file_count": sum(1 for path in files if path.endswith(".py")),
                    "subject_digest": hashlib.sha256(row["subject"].encode("utf-8")).hexdigest(),
                }
            )
    return {
        "window_start": since.date().isoformat(),
        "window_end": until.date().isoformat(),
        "non_merge_commit_count": len(rows),
        "surface_counts": dict(sorted(surfaces.items())),
        "low_signal_subject_count": low_signal_count,
        "oracle_direct_candidate_count": len(candidates),
        "candidate_count": len(candidates),
        "candidate_family_counts": dict(sorted(families.items())),
        "family_count": len(families),
        "sample_candidate_digests": candidates[:10],
        "task_design_candidate_count": len(design_candidates),
        "task_design_family_counts": dict(sorted(design_families.items())),
        "task_design_family_count": len(design_families),
        "sample_task_design_candidate_digests": design_candidates[:10],
    }


def repo_metadata(repo_slug: str, repo_path: Path) -> dict[str, Any]:
    head = require_git(repo_path, "rev-parse", "HEAD")
    head_date = require_git(repo_path, "log", "-1", "--format=%cI")
    tags = run_git(repo_path, "tag", "--sort=-creatordate")
    top_tags = [line.strip() for line in tags.stdout.splitlines()[:5] if line.strip()] if tags.returncode == 0 else []
    return {
        "path": repo_relative(repo_path),
        "head_digest": anchor_digest(repo_slug, head),
        "head_committed_at": head_date,
        "tag_sample": top_tags,
    }


def discover_test_surface(repo_path: Path) -> dict[str, Any]:
    return {
        "pyproject_exists": (repo_path / "pyproject.toml").exists(),
        "tests_dir_exists": (repo_path / "tests").exists(),
        "tox_ini_exists": (repo_path / "tox.ini").exists(),
        "noxfile_exists": (repo_path / "noxfile.py").exists(),
    }


def repo_admission_summary(repo_slug: str) -> dict[str, Any]:
    spec = REPOSITORIES[repo_slug]
    repo_path = Path(spec["path"])
    if not (repo_path / ".git").exists():
        raise ToolError("repository checkout is missing", repo_slug=repo_slug, path=str(repo_path))
    windows = {
        "C": summarize_window(repo_slug, repo_path, since=dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc), until=CUTOFF_C_END),
        "R": summarize_window(repo_slug, repo_path, since=R_START, until=R_END),
        "W_star": summarize_window(repo_slug, repo_path, since=W_STAR_START, until=T0),
    }
    extended_r = summarize_window(repo_slug, repo_path, since=EXTENDED_R_START, until=R_END)
    strict_r_ready = windows["R"]["task_design_candidate_count"] >= 20
    extended_r_ready = extended_r["task_design_candidate_count"] >= 20
    w_ready = windows["W_star"]["task_design_candidate_count"] >= 20
    family_ready = max(windows["W_star"]["task_design_family_count"], extended_r["task_design_family_count"]) >= 4
    repo_ready = w_ready and (strict_r_ready or extended_r_ready) and family_ready
    blockers = []
    if not w_ready:
        blockers.append("w_star_task_design_candidate_count_below_20")
    if not (strict_r_ready or extended_r_ready):
        blockers.append("r_task_design_candidate_count_below_20_even_with_allowed_earlier_extension")
    if not family_ready:
        blockers.append("task_design_family_count_below_4")
    if not windows["R"]["task_design_candidate_count"] >= 20 and extended_r_ready:
        blockers.append("strict_r_window_needs_allowed_earlier_extension")
    return {
        "repo_slug": repo_slug,
        "repository": spec["repository"],
        "role": spec["role"],
        "language": spec["language"],
        "test_command": spec["test_command"],
        "metadata": repo_metadata(repo_slug, repo_path),
        "test_surface": discover_test_surface(repo_path),
        "windows": windows,
        "extended_R": extended_r,
        "admission_ready": repo_ready,
        "strict_R_ready": strict_r_ready,
        "extended_R_ready": extended_r_ready,
        "W_star_ready": w_ready,
        "family_ready": family_ready,
        "blockers": blockers,
        "limitations": [
            "This is repository admission, not task admission; no hidden verifier smoke has run.",
            "oracle_direct_candidate_count requires source and test changes in the same commit.",
            "task_design_candidate_count also includes source-only changes that would require Golden-Oracle verifier construction.",
            "Candidate counts exclude low-signal subjects, but they are not accepted tasks.",
            "Source anchors are digested to avoid publishing W* target commits in this planning artifact.",
        ],
    }


def recommend_repositories(repos: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_slug = {str(repo.get("repo_slug")): repo for repo in repos}
    primary = "click" if by_slug.get("click", {}).get("admission_ready") else None
    ready_candidates = [repo for repo in repos if repo.get("admission_ready")]
    ready_candidates.sort(
        key=lambda repo: (
            repo.get("repo_slug") == "click",
            int(repo.get("windows", {}).get("W_star", {}).get("task_design_candidate_count", 0)),
            int(repo.get("extended_R", {}).get("task_design_candidate_count", 0)),
            int(repo.get("windows", {}).get("W_star", {}).get("task_design_family_count", 0)),
        ),
        reverse=True,
    )
    replication_candidates = [repo for repo in repos if repo.get("repo_slug") != "click" and repo.get("admission_ready")]
    replication_candidates.sort(
        key=lambda repo: (
            int(repo.get("windows", {}).get("W_star", {}).get("task_design_candidate_count", 0)),
            int(repo.get("extended_R", {}).get("task_design_candidate_count", 0)),
            int(repo.get("windows", {}).get("W_star", {}).get("task_design_family_count", 0)),
        ),
        reverse=True,
    )
    replication = replication_candidates[0]["repo_slug"] if replication_candidates else None
    fallback = None
    if replication != "black" and by_slug.get("black", {}).get("admission_ready"):
        fallback = "black"
    return {
        "primary_repo": primary,
        "recommended_execution_repo": ready_candidates[0]["repo_slug"] if ready_candidates else None,
        "replication_repo": replication,
        "fallback_replication_repo": fallback,
        "basis": "Click remains the historical evidence repo, but the new C/R/W* execution repo must pass the 20-task W* design-supply gate. If Click is blocked, choose the ready repo with the strongest W* and extended-R task-design counts.",
    }


def build_payload(repo_slugs: Sequence[str]) -> dict[str, Any]:
    repositories = [repo_admission_summary(slug) for slug in repo_slugs]
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": "repository_admission_completed",
        "generated_at": iso_now(),
        "model_calls_made": 0,
        "objective": "Barcarolle repository-local benchmark admission for C/R/W* experiment line",
        "time_split": {
            "T0": "2026-05-14",
            "C": {"end": "2025-11-13", "role": "calibration_only"},
            "R": {"start": "2025-11-14", "end": "2026-02-13", "role": "repository_benchmark_selection"},
            "W_star": {"start": "2026-02-14", "end": "2026-05-14", "role": "criterion_work_set"},
            "allowed_extension": "C and R may extend earlier if task supply is thin; W* must not borrow earlier work.",
            "extended_R_scan": {"start": "2025-05-14", "end": "2026-02-13"},
        },
        "repositories": repositories,
        "recommendation": recommend_repositories(repositories),
        "next_required_step": "Run task admission for the recommended ready execution repo; do not use ACUT outputs or W* results to modify R.",
    }


def render_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Repository-Local Benchmark Admission",
        "",
        f"Status: `{payload.get('status')}`",
        f"Generated at: `{payload.get('generated_at')}`",
        "",
        "## Split",
        "",
        "- T0: `2026-05-14`",
        "- C/calibration: `<= 2025-11-13`",
        "- R/repository benchmark: `2025-11-14` to `2026-02-13`",
        "- W*/criterion work set: `2026-02-14` to `2026-05-14`",
        "- If task supply is thin, only C/R may extend earlier; W* must stay recent.",
        "",
        "## Repository Summary",
        "",
        "| Repo | Ready | Strict R design | Extended R design | W* design | W* direct oracle | W* families | Notes |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for repo in payload.get("repositories", []):
        if not isinstance(repo, Mapping):
            continue
        blockers = ", ".join(repo.get("blockers", [])) or "none"
        lines.append(
            "| "
            f"`{repo.get('repo_slug')}` | "
            f"`{repo.get('admission_ready')}` | "
            f"{repo.get('windows', {}).get('R', {}).get('task_design_candidate_count')} | "
            f"{repo.get('extended_R', {}).get('task_design_candidate_count')} | "
            f"{repo.get('windows', {}).get('W_star', {}).get('task_design_candidate_count')} | "
            f"{repo.get('windows', {}).get('W_star', {}).get('oracle_direct_candidate_count')} | "
            f"{repo.get('windows', {}).get('W_star', {}).get('task_design_family_count')} | "
            f"{blockers} |"
        )
    recommendation = payload.get("recommendation") if isinstance(payload.get("recommendation"), Mapping) else {}
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            f"- Primary repo: `{recommendation.get('primary_repo')}`",
            f"- Recommended execution repo: `{recommendation.get('recommended_execution_repo')}`",
            f"- Replication repo: `{recommendation.get('replication_repo')}`",
            f"- Fallback replication repo: `{recommendation.get('fallback_replication_repo')}`",
            "",
            "## Boundary",
            "",
            "This scan does not admit tasks and does not run models. It checks whether repositories have enough history to justify task admission under the C/R/W* design, separating direct oracle candidates from source-only task-design candidates.",
            "",
        ]
    )
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_slugs = args.repo or ["click", "rich", "black"]
    payload = build_payload(repo_slugs)
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
