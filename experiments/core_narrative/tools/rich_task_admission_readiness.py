#!/usr/bin/env python3
"""Build Rich task-admission readiness evidence for the 2026-05-14 C/R/W* line."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, write_json
from repository_local_benchmark_admission import classify_family


TOOL = "rich_task_admission_readiness"
SCHEMA_VERSION = "core-narrative.rich-task-admission-readiness.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPO = REPO_ROOT / "experiments/core_narrative/external_repos/rich"
DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/rich_task_admission_readiness_20260514.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-14_rich_task_admission_readiness.md"

T0 = dt.datetime(2026, 5, 14, 23, 59, 59, tzinfo=dt.timezone.utc)
C_SCAN_START = dt.datetime(2025, 5, 14, 0, 0, 0, tzinfo=dt.timezone.utc)
C_END = dt.datetime(2025, 11, 13, 23, 59, 59, tzinfo=dt.timezone.utc)
R_START = dt.datetime(2025, 11, 14, 0, 0, 0, tzinfo=dt.timezone.utc)
R_END = dt.datetime(2026, 2, 13, 23, 59, 59, tzinfo=dt.timezone.utc)
W_STAR_START = dt.datetime(2026, 2, 14, 0, 0, 0, tzinfo=dt.timezone.utc)

PRIMARY_TARGET = 20
RESERVE_TARGET = 5
CANDIDATE_POOL_TARGET = 40

TEST_DEF_RE = re.compile(r"^\+\s*(?:async\s+)?def\s+(test_[A-Za-z0-9_]+)\s*\(")
TEST_HUNK_RE = re.compile(r"^@@.*@@\s*(?:async\s+)?def\s+(test_[A-Za-z0-9_]+)\s*\(")
SKIP_SUBJECT_RE = re.compile(
    r"(?i)(release|docs?:|documentation|pre-commit|precommit|ruff|lint|format guidelines|typing|"
    r"mypy|pyright|dependency|dependencies|changelog|workflow|ci|publish|revert)"
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(DEFAULT_REPO), help="Local Rich checkout.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Structured JSON output.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Markdown report output.")
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


def parse_git_datetime(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def window_for_date(value: str) -> str:
    when = parse_git_datetime(value)
    if C_SCAN_START <= when <= C_END:
        return "C"
    if R_START <= when <= R_END:
        return "R"
    if W_STAR_START <= when <= T0:
        return "W_star"
    if when < C_SCAN_START:
        return "older_C_not_scanned"
    if when > T0:
        return "future"
    return "gap"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def source_anchor_digest(commit: str) -> str:
    return sha256_text(f"rich\n{commit}")


def changed_file_set_digest(files: Sequence[str]) -> str:
    return sha256_text("\n".join(sorted(files)))


def changed_files(repo_path: Path, commit: str) -> list[str]:
    completed = run_git(repo_path, "diff-tree", "--no-commit-id", "--name-only", "-r", commit)
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def first_parent(repo_path: Path, commit: str) -> str | None:
    completed = run_git(repo_path, "rev-list", "--parents", "-n", "1", commit)
    if completed.returncode != 0:
        return None
    parts = completed.stdout.strip().split()
    return parts[1] if len(parts) >= 2 else None


def rich_source_files(files: Sequence[str]) -> list[str]:
    return [path for path in files if path.endswith(".py") and path.startswith("rich/")]


def rich_test_files(files: Sequence[str]) -> list[str]:
    return [path for path in files if path.endswith(".py") and path.startswith("tests/")]


def candidate_surface(files: Sequence[str]) -> str:
    has_source = bool(rich_source_files(files))
    has_tests = bool(rich_test_files(files))
    if has_source and has_tests:
        return "source_and_tests"
    if has_source:
        return "source_without_tests"
    if has_tests:
        return "tests_without_source"
    return "other"


def extract_test_nodes_from_diff(diff_text: str, test_file: str) -> list[str]:
    nodes: list[str] = []
    for line in diff_text.splitlines():
        match = TEST_DEF_RE.match(line) or TEST_HUNK_RE.match(line)
        if not match:
            continue
        node = f"{test_file}::{match.group(1)}"
        if node not in nodes:
            nodes.append(node)
    return nodes


def extract_test_nodes(repo_path: Path, base: str, target: str, test_files: Sequence[str]) -> list[str]:
    nodes: list[str] = []
    for test_file in test_files:
        completed = run_git(repo_path, "diff", "--unified=0", base, target, "--", test_file)
        if completed.returncode != 0:
            continue
        for node in extract_test_nodes_from_diff(completed.stdout, test_file):
            if node not in nodes:
                nodes.append(node)
    return nodes


def oracle_requirement(surface: str, *, test_node_count: int) -> str:
    if surface == "source_without_tests":
        return "golden_oracle_required"
    if surface == "source_and_tests" and test_node_count > 0:
        return "direct_reference_tests_available"
    if surface == "source_and_tests":
        return "direct_tests_without_extractable_nodes"
    return "not_task_design_candidate"


def candidate_from_commit(repo_path: Path, commit: str, committed_at: str, subject: str) -> dict[str, Any] | None:
    window = window_for_date(committed_at)
    if window not in {"C", "R", "W_star"} or SKIP_SUBJECT_RE.search(subject):
        return None
    files = changed_files(repo_path, commit)
    surface = candidate_surface(files)
    if surface not in {"source_and_tests", "source_without_tests"}:
        return None
    source_files = rich_source_files(files)
    test_files = rich_test_files(files)
    parent = first_parent(repo_path, commit)
    test_nodes: list[str] = []
    if parent is not None and test_files:
        test_nodes = extract_test_nodes(repo_path, parent, commit, test_files)
    requirement = oracle_requirement(surface, test_node_count=len(test_nodes))
    family = classify_family("rich", subject, files)
    return {
        "commit": commit,
        "base_commit": parent,
        "committed_at": committed_at,
        "subject": subject,
        "window": window,
        "family": family,
        "surface": surface,
        "source_files": source_files,
        "test_files": test_files,
        "test_nodes": test_nodes,
        "verifier_command": ".venv/bin/python -m pytest -q " + " ".join(test_nodes) if test_nodes else "",
        "source_file_count": len(source_files),
        "test_file_count": len(test_files),
        "test_node_count": len(test_nodes),
        "changed_file_set_digest": changed_file_set_digest(source_files + test_files),
        "oracle_requirement": requirement,
        "direct_smoke_ready": requirement == "direct_reference_tests_available",
    }


def commit_rows(repo_path: Path) -> list[dict[str, str]]:
    completed = run_git(
        repo_path,
        "log",
        "--no-merges",
        f"--since={C_SCAN_START.isoformat()}",
        f"--until={T0.isoformat()}",
        "--format=%H%x00%cI%x00%s",
        timeout=180,
    )
    if completed.returncode != 0:
        raise ToolError("failed to scan Rich git history", stderr=completed.stderr[-500:])
    rows: list[dict[str, str]] = []
    for line in completed.stdout.splitlines():
        parts = line.split("\x00", 2)
        if len(parts) == 3:
            rows.append({"commit": parts[0], "committed_at": parts[1], "subject": parts[2]})
    return rows


def discover_candidates(repo_path: Path) -> list[dict[str, Any]]:
    rows = commit_rows(repo_path)
    candidates: list[dict[str, Any]] = []
    seen_subjects: set[str] = set()
    for row in rows:
        subject_key = re.sub(r"\s*\(#\d+\)\s*$", "", row["subject"]).lower()
        if subject_key in seen_subjects:
            continue
        candidate = candidate_from_commit(repo_path, row["commit"], row["committed_at"], row["subject"])
        if candidate is None:
            continue
        seen_subjects.add(subject_key)
        candidates.append(candidate)
    return candidates


def public_candidate_row(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_anchor_digest": source_anchor_digest(str(candidate["commit"])),
        "committed_at": candidate["committed_at"],
        "window": candidate["window"],
        "family": candidate["family"],
        "surface": candidate["surface"],
        "source_file_count": candidate["source_file_count"],
        "test_file_count": candidate["test_file_count"],
        "test_node_count": candidate["test_node_count"],
        "changed_file_set_digest": candidate["changed_file_set_digest"],
        "subject_digest": sha256_text(str(candidate["subject"])),
        "oracle_requirement": candidate["oracle_requirement"],
        "direct_smoke_ready": bool(candidate["direct_smoke_ready"]),
    }


def summarize_window(candidates: Sequence[Mapping[str, Any]], window: str) -> dict[str, Any]:
    rows = [candidate for candidate in candidates if candidate.get("window") == window]
    surfaces = Counter(str(row.get("surface")) for row in rows)
    families = Counter(str(row.get("family")) for row in rows)
    direct_ready = [row for row in rows if row.get("direct_smoke_ready")]
    source_only = [row for row in rows if row.get("oracle_requirement") == "golden_oracle_required"]
    direct_without_nodes = [row for row in rows if row.get("oracle_requirement") == "direct_tests_without_extractable_nodes"]
    design_count = len(rows)
    return {
        "window": window,
        "task_design_candidate_count": design_count,
        "surface_counts": dict(sorted(surfaces.items())),
        "family_counts": dict(sorted(families.items())),
        "family_count": len(families),
        "direct_smoke_ready_count": len(direct_ready),
        "source_only_golden_oracle_required_count": len(source_only),
        "direct_tests_without_extractable_nodes_count": len(direct_without_nodes),
        "sample_candidate_digests": [public_candidate_row(row) for row in rows[:10]],
        "denominator_readiness": {
            "primary_target": PRIMARY_TARGET,
            "reserve_target": RESERVE_TARGET,
            "candidate_pool_target": CANDIDATE_POOL_TARGET,
            "can_form_20_primary_from_design_candidates": design_count >= PRIMARY_TARGET,
            "can_form_20_primary_plus_5_reserve_from_design_candidates": design_count >= PRIMARY_TARGET + RESERVE_TARGET,
            "can_form_40_candidate_pool": design_count >= CANDIDATE_POOL_TARGET,
            "can_form_20_primary_from_direct_smoke_ready_candidates": len(direct_ready) >= PRIMARY_TARGET,
            "golden_oracle_needed_for_20_primary": max(0, PRIMARY_TARGET - len(direct_ready)),
            "golden_oracle_needed_for_20_primary_plus_5_reserve": max(0, PRIMARY_TARGET + RESERVE_TARGET - len(direct_ready)),
            "candidate_pool_gap_to_40": max(0, CANDIDATE_POOL_TARGET - design_count),
        },
    }


def repo_metadata(repo_path: Path) -> dict[str, Any]:
    head = run_git(repo_path, "rev-parse", "HEAD")
    head_date = run_git(repo_path, "log", "-1", "--format=%cI")
    if head.returncode != 0:
        raise ToolError("failed to read Rich HEAD", stderr=head.stderr[-500:])
    return {
        "path": repo_relative(repo_path),
        "head_digest": source_anchor_digest(head.stdout.strip()),
        "head_committed_at": head_date.stdout.strip() if head_date.returncode == 0 else None,
    }


def build_payload(repo_path: Path) -> dict[str, Any]:
    if not (repo_path / ".git").exists():
        raise ToolError("Rich checkout is missing", repo_path=str(repo_path))
    candidates = discover_candidates(repo_path)
    windows = {window: summarize_window(candidates, window) for window in ["C", "R", "W_star"]}
    w_star = windows["W_star"]
    r_window = windows["R"]
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": "rich_task_admission_readiness_completed",
        "generated_at": iso_now(),
        "model_calls_made": 0,
        "repo_slug": "rich",
        "repository": "Textualize/rich",
        "metadata": repo_metadata(repo_path),
        "time_split": {
            "T0": "2026-05-14",
            "C_scanned": {"start": C_SCAN_START.date().isoformat(), "end": C_END.date().isoformat()},
            "R": {"start": R_START.date().isoformat(), "end": R_END.date().isoformat()},
            "W_star": {"start": W_STAR_START.date().isoformat(), "end": T0.date().isoformat()},
        },
        "windows": windows,
        "primary_runs_authorized": False,
        "readiness_verdict": {
            "r_has_20_primary_design_supply": r_window["denominator_readiness"]["can_form_20_primary_from_design_candidates"],
            "r_has_40_candidate_pool": r_window["denominator_readiness"]["can_form_40_candidate_pool"],
            "w_star_has_20_primary_design_supply": w_star["denominator_readiness"]["can_form_20_primary_from_design_candidates"],
            "w_star_has_20_primary_plus_5_reserve_design_supply": w_star["denominator_readiness"][
                "can_form_20_primary_plus_5_reserve_from_design_candidates"
            ],
            "w_star_has_40_candidate_pool": w_star["denominator_readiness"]["can_form_40_candidate_pool"],
            "w_star_direct_smoke_ready_count": w_star["direct_smoke_ready_count"],
            "w_star_golden_oracle_needed_for_20_primary": w_star["denominator_readiness"]["golden_oracle_needed_for_20_primary"],
            "w_star_golden_oracle_needed_for_20_primary_plus_5_reserve": w_star["denominator_readiness"][
                "golden_oracle_needed_for_20_primary_plus_5_reserve"
            ],
        },
        "claim_boundary": [
            "This is task-admission readiness, not task admission.",
            "No no-op verifier smoke or reference-patch smoke has run.",
            "Source-only candidates require Golden-Oracle verifier construction before admission.",
            "Primary R/W* model attempts remain unauthorized.",
            "Candidate rows publish digests instead of raw target commits.",
        ],
        "next_required_step": "Construct and smoke Rich hidden verifiers, prioritizing W* source-only candidates until at least 20 primary and 5 reserve tasks pass no-op/reference admission.",
    }


def render_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Rich Task-Admission Readiness",
        "",
        f"Status: `{payload.get('status')}`",
        f"Generated at: `{payload.get('generated_at')}`",
        "",
        "## Scan Boundary",
        "",
        "- This scan deduplicates commits by normalized subject before counting task-design rows.",
        "- Direct smoke-ready requires source changes, test changes, and extractable pytest nodes from the target diff.",
        "- Source-only rows remain task-design candidates, but require Golden-Oracle verifier construction before admission.",
        "- C is scanned only from `2025-05-14` to `2025-11-13`; older C can still be used if calibration supply is thin.",
        "",
        "## Summary",
        "",
        "| Window | Design candidates | Direct smoke-ready | Source-only needing Golden-Oracle | Direct tests without nodes | Families | 40-pool gap |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    windows = payload.get("windows") if isinstance(payload.get("windows"), Mapping) else {}
    for window in ["C", "R", "W_star"]:
        summary = windows.get(window) if isinstance(windows.get(window), Mapping) else {}
        readiness = summary.get("denominator_readiness") if isinstance(summary.get("denominator_readiness"), Mapping) else {}
        lines.append(
            f"| `{window}` | "
            f"{summary.get('task_design_candidate_count')} | "
            f"{summary.get('direct_smoke_ready_count')} | "
            f"{summary.get('source_only_golden_oracle_required_count')} | "
            f"{summary.get('direct_tests_without_extractable_nodes_count')} | "
            f"{summary.get('family_count')} | "
            f"{readiness.get('candidate_pool_gap_to_40')} |"
        )
    verdict = payload.get("readiness_verdict") if isinstance(payload.get("readiness_verdict"), Mapping) else {}
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"- R has 20-primary design supply: `{verdict.get('r_has_20_primary_design_supply')}`",
            f"- R has 40-candidate pool supply: `{verdict.get('r_has_40_candidate_pool')}`",
            f"- W* has 20-primary design supply: `{verdict.get('w_star_has_20_primary_design_supply')}`",
            f"- W* has 20-primary plus 5-reserve design supply: `{verdict.get('w_star_has_20_primary_plus_5_reserve_design_supply')}`",
            f"- W* has 40-candidate pool supply: `{verdict.get('w_star_has_40_candidate_pool')}`",
            f"- W* direct smoke-ready candidates: `{verdict.get('w_star_direct_smoke_ready_count')}`",
            f"- W* Golden-Oracle candidates needed for 20 primary: `{verdict.get('w_star_golden_oracle_needed_for_20_primary')}`",
            f"- W* Golden-Oracle candidates needed for 20 primary + 5 reserve: `{verdict.get('w_star_golden_oracle_needed_for_20_primary_plus_5_reserve')}`",
            "",
            "Primary R/W* model attempts remain unauthorized. This readiness scan does not run no-op/reference smoke.",
            "",
        ]
    )
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    output = Path(args.output)
    report = Path(args.report)
    payload = build_payload(Path(args.repo).resolve())
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
