from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXP_REL = Path("experiments/phase0_headroom")
ARCHIVE_REL = Path("archive/2026-05-agent-license-reset")
PRIMARY_REPO_ID = "toolz"
PRIMARY_REPO_URL = "https://github.com/pytoolz/toolz.git"
PRIMARY_REPO_LOCAL = EXP_REL / "external_repos" / PRIMARY_REPO_ID
WORKSPACE_REL = EXP_REL / "workspaces"
RAW_REL = EXP_REL / "results" / "raw"
HISTORY_SINCE = "2016-01-01"
EXECUTABLE_SINCE = "2018-01-01"
CERTIFICATION_LIMIT = 16
CERTIFICATION_TIMEOUT_SECONDS = 60


@dataclass
class CommandResult:
    command: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False


def run_command(
    command: list[str],
    cwd: Path,
    timeout: int = 120,
    input_bytes: bytes | None = None,
    env: dict[str, str] | None = None,
) -> CommandResult:
    start = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=env,
            check=False,
        )
        duration = time.monotonic() - start
        return CommandResult(
            command=command,
            cwd=str(cwd),
            returncode=completed.returncode,
            stdout=completed.stdout.decode("utf-8", errors="replace"),
            stderr=completed.stderr.decode("utf-8", errors="replace"),
            duration_seconds=duration,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - start
        stdout = exc.stdout.decode("utf-8", errors="replace") if exc.stdout else ""
        stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
        return CommandResult(
            command=command,
            cwd=str(cwd),
            returncode=124,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
            timed_out=True,
        )


def require_success(result: CommandResult) -> str:
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(result.command)}\n"
            f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )
    return result.stdout


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_text(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def append_process(root: Path, title: str, lines: list[str]) -> None:
    path = root / EXP_REL / "reports" / "process.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    block = [f"\n## {title}", "", f"Timestamp: `{stamp}`.", ""]
    block.extend(lines)
    block.append("")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(block))


def debug_artifact(root: Path, name: str, payload: dict[str, Any]) -> Path:
    path = root / EXP_REL / "results" / f"{name}-debug.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        **payload,
    }
    write_json(path, payload)
    return path


def python_command(root: Path) -> list[str]:
    uv = shutil.which("uv")
    if uv:
        return [uv, "run", "--project", str(root / EXP_REL), "python"]
    return ["python3"]


def python_command_display(root: Path) -> str:
    return " ".join(python_command(root)).replace(str(root) + "/", "")


def ensure_layout(root: Path) -> None:
    for rel in [
        "configs",
        "candidate_sources",
        "target_profiles",
        "certified_tasks",
        "releases",
        "results",
        "reports",
        "tools",
    ]:
        (root / EXP_REL / rel).mkdir(parents=True, exist_ok=True)
    for rel in [
        "external_repos",
        "workspaces",
        "cache",
        "large_artifacts",
        "results/raw",
    ]:
        (root / EXP_REL / rel).mkdir(parents=True, exist_ok=True)


def read_cumulative_cost(ledger_path: Path) -> float:
    if not ledger_path.exists() or ledger_path.stat().st_size == 0:
        return 0.0
    cumulative = 0.0
    with ledger_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            cumulative = float(record.get("cumulative_estimated_cost_usd", cumulative))
    return cumulative


def current_branch(root: Path) -> str:
    return require_success(run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], root)).strip()


def current_head(root: Path) -> str:
    return require_success(run_command(["git", "rev-parse", "HEAD"], root)).strip()


def initialize_preflight(root: Path) -> None:
    ensure_layout(root)
    ledger = root / EXP_REL / "results" / "cost_ledger.jsonl"
    if not ledger.exists():
        write_text(ledger, "")

    process = root / EXP_REL / "reports" / "process.md"
    write_text(
        process,
        "# Phase 0 Headroom Process Log\n\n"
        "This log is generated by `experiments/phase0_headroom/tools/phase0_driver.py`.\n",
    )

    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    ignore_checks = {
        "workspaces": "experiments/phase0_headroom/workspaces/" in gitignore,
        "external_repos": "experiments/phase0_headroom/external_repos/" in gitignore,
        "cache": "experiments/phase0_headroom/cache/" in gitignore,
        "large_artifacts": "experiments/phase0_headroom/large_artifacts/" in gitignore,
        "raw_results": "experiments/phase0_headroom/results/raw/" in gitignore,
    }
    active_core = require_success(run_command(["git", "ls-files", "experiments/core_narrative"], root)).strip()
    archive_files = require_success(
        run_command(["find", str(ARCHIVE_REL / "experiments/core_narrative"), "-maxdepth", "3", "-type", "f"], root)
    ).splitlines()
    disk = require_success(run_command(["df", "-h", "."], root)).strip()
    shell = os.environ.get("SHELL", "")

    report = [
        "# Phase 0 Preflight",
        "",
        f"- Branch: `{current_branch(root)}`",
        f"- HEAD: `{current_head(root)}`",
        f"- Generated UTC: `{datetime.now(timezone.utc).replace(microsecond=0).isoformat()}`",
        f"- Shell: `{shell}`",
        f"- Python: `{platform.python_version()}` at `{sys.executable}`",
        f"- Phase 0 Python command: `{python_command_display(root)}`",
        "- Disk:",
        "",
        "```text",
        disk,
        "```",
        "",
        "## Ignore Checks",
        "",
    ]
    for name, passed in ignore_checks.items():
        report.append(f"- `{name}`: {'pass' if passed else 'fail'}")
    report.extend(
        [
            "",
            "## Archive Reuse Inventory",
            "",
            f"- Archived core-narrative files seen at max depth 3: `{len(archive_files)}`",
            "- Active `experiments/core_narrative` tracked files: `0`"
            if not active_core
            else f"- Active `experiments/core_narrative` tracked files: `{active_core}`",
            "- Reuse policy: reference archived Click manifests, release metadata, verifier discipline, and score taxonomy; do not copy raw outputs.",
            "",
            "## Budget",
            "",
            f"- Ledger path: `{EXP_REL / 'results/cost_ledger.jsonl'}`",
            f"- Cumulative estimated LLM API spend: `${read_cumulative_cost(ledger):.2f}`",
            "- Paid model calls during this run: `0`",
            "",
            "Acceptance: process log exists, budget ledger exists, no paid model call has been made, ignored raw paths are configured, and active `experiments/core_narrative` remains absent from tracked files.",
            "",
        ]
    )
    write_text(root / EXP_REL / "reports" / "preflight.md", "\n".join(report))
    append_process(
        root,
        "Step 0 Preflight",
        [
            f"- Branch `{current_branch(root)}`, HEAD `{current_head(root)}`.",
            f"- Cost ledger exists at `{EXP_REL / 'results/cost_ledger.jsonl'}` with cumulative estimated spend `${read_cumulative_cost(ledger):.2f}`.",
            "- No paid model calls were made.",
            "- Next acceptance gate: budget and execution configs.",
        ],
    )


def write_budget_configs(root: Path) -> None:
    budget_yaml = """max_total_usd: 200
soft_stop_usd: 160
stop_and_ask_usd: 180
reserve_usd: 20
paid_agent_runs_max_usd: 120
optional_llm_review_max_usd: 40
reporting_llm_max_usd: 20
require_ledger_before_paid_call: true
allow_parallel_paid_workers: false
ledger_path: experiments/phase0_headroom/results/cost_ledger.jsonl
"""
    execution_yaml = f"""tooling_manager: uv
phase0_project: experiments/phase0_headroom/pyproject.toml
python_command: {json.dumps(python_command_display(root))}
workspace_root: experiments/phase0_headroom/workspaces
external_repos_root: experiments/phase0_headroom/external_repos
raw_artifacts_root: experiments/phase0_headroom/results/raw
cache_root: experiments/phase0_headroom/cache
large_artifacts_root: experiments/phase0_headroom/large_artifacts
default_timeout_seconds: 120
certification_timeout_seconds: {CERTIFICATION_TIMEOUT_SECONDS}
allow_paid_model_calls_by_default: false
require_budget_projection_before_paid_batch: true
primary_python: {sys.executable}
primary_shell: {os.environ.get("SHELL", "")}
"""
    write_text(root / EXP_REL / "configs" / "budget.yaml", budget_yaml)
    write_text(root / EXP_REL / "configs" / "execution.yaml", execution_yaml)
    report = """# Phase 0 Budget Plan

The hard LLM API cap is USD 200. The soft stop is USD 160, and USD 180 is the
stop-and-ask threshold. This run uses `uv`-managed deterministic repository
mining and local test execution only; no paid model call is approved by default.

Before any paid batch, the worker must read
`experiments/phase0_headroom/results/cost_ledger.jsonl`, compute cumulative
estimated spend, write the projected batch cost into the process log, and verify
that the cumulative projected spend remains below the applicable threshold.

For this execution, cumulative estimated spend remains USD 0.00 because no
external model call was made.
"""
    write_text(root / EXP_REL / "reports" / "budget_plan.md", report)
    append_process(
        root,
        "Step 1 Budget And Execution Config",
        [
            "- Wrote `configs/budget.yaml` and `configs/execution.yaml`.",
            "- Wrote `reports/budget_plan.md`.",
            "- Next acceptance gate: repository selection must use buildability, task supply, and service-risk evidence.",
        ],
    )


def clone_or_update_primary(root: Path) -> dict[str, Any]:
    repo = root / PRIMARY_REPO_LOCAL
    if not repo.exists():
        result = run_command(["git", "clone", PRIMARY_REPO_URL, str(repo)], root, timeout=300)
        if result.returncode != 0:
            debug_artifact(
                root,
                "repository-clone",
                {"repo_id": PRIMARY_REPO_ID, "command": result.command, "stdout": result.stdout, "stderr": result.stderr},
            )
            raise RuntimeError("failed to clone primary repository")
    else:
        result = run_command(["git", "fetch", "--prune", "--tags", "origin"], repo, timeout=300)
        if result.returncode != 0:
            debug_artifact(
                root,
                "repository-fetch",
                {"repo_id": PRIMARY_REPO_ID, "command": result.command, "stdout": result.stdout, "stderr": result.stderr},
            )
    head = require_success(run_command(["git", "rev-parse", "HEAD"], repo)).strip()
    remote = require_success(run_command(["git", "remote", "get-url", "origin"], repo)).strip()
    return {"local_path": str(PRIMARY_REPO_LOCAL), "head": head, "remote": remote}


def is_code_file(path: str) -> bool:
    return path.startswith("toolz/") and path.endswith(".py") and "/tests/" not in path


def is_test_file(path: str) -> bool:
    return path.endswith(".py") and "/tests/" in path


def module_name(path: str) -> str:
    parts = path.split("/")
    if len(parts) < 2:
        return "root"
    if parts[1] == "sandbox":
        return "sandbox"
    return parts[1].removesuffix(".py")


def task_type_proxy(subject: str, files: list[str]) -> str:
    lower = subject.lower()
    if any(token in lower for token in ["fix", "bug", "error", "raise", "handle", "revert", "invalid"]):
        return "bug_or_behavior_fix"
    if any(token in lower for token in ["add", "implement", "support", "write", "new"]):
        return "feature_or_api_extension"
    if any(token in lower for token in ["refactor", "modernize", "cleanup", "clean up", "drop", "remove", "pyupgrade"]):
        return "maintenance_refactor"
    if all(path.startswith((".github/", "doc/", "docs/")) for path in files):
        return "docs_or_ci"
    if "test" in lower:
        return "test_infrastructure"
    return "behavior_or_maintenance"


def size_bucket(added: int, deleted: int) -> str:
    total = added + deleted
    if total <= 20:
        return "xs_0_20"
    if total <= 80:
        return "s_21_80"
    if total <= 200:
        return "m_81_200"
    return "l_201_plus"


def first_parent(repo: Path, sha: str) -> str | None:
    parts = require_success(run_command(["git", "rev-list", "--parents", "-n", "1", sha], repo)).split()
    if len(parts) != 2:
        return None
    return parts[1]


def commit_files(repo: Path, sha: str) -> list[str]:
    out = require_success(run_command(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha], repo))
    return [line.strip() for line in out.splitlines() if line.strip()]


def commit_numstat(repo: Path, parent: str, sha: str) -> tuple[int, int]:
    out = require_success(run_command(["git", "diff", "--numstat", parent, sha], repo))
    added = 0
    deleted = 0
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        if parts[0].isdigit():
            added += int(parts[0])
        if parts[1].isdigit():
            deleted += int(parts[1])
    return added, deleted


def extract_history_anchors(root: Path) -> list[dict[str, Any]]:
    repo = root / PRIMARY_REPO_LOCAL
    hashes = require_success(
        run_command(["git", "log", "--reverse", "--no-merges", f"--since={HISTORY_SINCE}", "--format=%H"], repo)
    ).splitlines()
    anchors: list[dict[str, Any]] = []
    for sha in hashes:
        parent = first_parent(repo, sha)
        if not parent:
            continue
        files = commit_files(repo, sha)
        code_files = [path for path in files if is_code_file(path)]
        test_files = [path for path in files if is_test_file(path)]
        if not code_files or not test_files:
            continue
        added, deleted = commit_numstat(repo, parent, sha)
        subject = require_success(run_command(["git", "show", "-s", "--format=%s", sha], repo)).strip()
        date = require_success(run_command(["git", "show", "-s", "--format=%aI", sha], repo)).strip()
        modules = sorted({module_name(path) for path in code_files})
        anchors.append(
            {
                "anchor_id": f"commit:{sha}",
                "repo_id": PRIMARY_REPO_ID,
                "repo_url": PRIMARY_REPO_URL,
                "source_type": "git_commit",
                "base_commit": parent,
                "target_commit": sha,
                "task_time": date,
                "subject": subject,
                "changed_files": files,
                "code_files": code_files,
                "test_files": test_files,
                "changed_file_count": len(files),
                "code_file_count": len(code_files),
                "test_file_count": len(test_files),
                "changed_lines_added": added,
                "changed_lines_deleted": deleted,
                "changed_lines_total": added + deleted,
                "change_size_bucket": size_bucket(added, deleted),
                "module_or_package": modules,
                "task_type_proxy": task_type_proxy(subject, files),
                "dependency_radius_proxy": len(modules),
                "issue_or_pr_text_length": len(subject),
                "labels": ["missing:not_fetched"],
                "api_surface_touched": modules,
                "runtime_or_platform_constraints": "python_version_or_introspection"
                if any(token in subject.lower() for token in ["python", "signature", "inspect"])
                else "local_pure_python",
                "source_text_pointers": [
                    f"https://github.com/pytoolz/toolz/commit/{sha}",
                    f"git show --stat {sha}",
                ],
                "candidate_oracle_source": test_files,
                "leakage_risks": [
                    "commit_subject_may_describe_solution",
                    "reference_patch_available_in_public_git_history",
                ],
                "taxonomy_draft": {
                    "module": modules,
                    "task_type_proxy": task_type_proxy(subject, files),
                    "change_size_bucket": size_bucket(added, deleted),
                    "oracle_type": "changed_tests_from_commit",
                },
            }
        )
    return anchors


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def split_early_late(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    sorted_rows = sorted(rows, key=lambda row: parse_iso(row["task_time"]))
    mid = len(sorted_rows) // 2
    cutoff = sorted_rows[mid]["task_time"] if sorted_rows else ""
    return sorted_rows[:mid], sorted_rows[mid:], cutoff


def distribution(rows: list[dict[str, Any]], field: str) -> dict[str, float]:
    counter: Counter[str] = Counter()
    for row in rows:
        value = row[field]
        if isinstance(value, list):
            for item in value:
                counter[str(item)] += 1
        else:
            counter[str(value)] += 1
    total = sum(counter.values()) or 1
    return {key: count / total for key, count in sorted(counter.items())}


def count_candidates_since(anchors: list[dict[str, Any]], since: str) -> int:
    cutoff = datetime.fromisoformat(f"{since}T00:00:00+00:00")
    return sum(1 for row in anchors if parse_iso(row["task_time"]) >= cutoff)


def write_repository_selection(root: Path, anchors: list[dict[str, Any]], clone_info: dict[str, Any]) -> None:
    repo = root / PRIMARY_REPO_LOCAL
    smoke = run_command(
        [*python_command(root), "-m", "pytest", "toolz/tests", "-q", "--ignore=toolz/tests/test_package.py"],
        repo,
        timeout=90,
        env={**os.environ, "PYTHONPATH": str(repo)},
    )
    smoke_tail = (smoke.stdout + smoke.stderr).strip().splitlines()[-3:]
    anchor_count = len(anchors)
    executable_anchor_estimate = count_candidates_since(anchors, EXECUTABLE_SINCE)
    py_version = platform.python_version()
    shortlist = [
        {
            "repo_id": "click_archive_smoke",
            "url": "archive/2026-05-agent-license-reset/experiments/core_narrative/tasks/click",
            "language": "Python",
            "package_manager": "archived manifests",
            "default_test_command": "verifier/run.sh per archived task",
            "install_command": "not applicable for active primary selection",
            "median_test_runtime_estimate_seconds": 60,
            "external_service_risk": "low",
            "candidate_anchor_estimate": 14,
            "why_selected_or_rejected": "selected as smoke and generic comparator only; not used as primary target because runbook keeps archived Click material out of active target selection.",
        },
        {
            "repo_id": PRIMARY_REPO_ID,
            "url": PRIMARY_REPO_URL,
            "language": "Python",
            "package_manager": "setuptools/pyproject",
            "default_test_command": f"PYTHONPATH=. {python_command_display(root)} -m pytest <changed test files> -q",
            "install_command": "phase0 tooling dependencies are resolved by uv; target repo editable install is not required for changed-test certification probe",
            "median_test_runtime_estimate_seconds": 1,
            "external_service_risk": "low",
            "candidate_anchor_estimate": anchor_count,
            "why_selected_or_rejected": f"selected primary: supports local Python {py_version}, has {anchor_count} code-plus-test history anchors since {HISTORY_SINCE}, and smoke command exited {smoke.returncode}.",
        },
        {
            "repo_id": "humanize",
            "url": "https://github.com/python-humanize/humanize.git",
            "language": "Python",
            "package_manager": "hatch/pyproject",
            "default_test_command": "python -m pytest",
            "install_command": "uv-managed Python >=3.10 plus test extras",
            "median_test_runtime_estimate_seconds": 5,
            "external_service_risk": "low",
            "candidate_anchor_estimate": "117 path-touching commits observed; code-plus-test count not fully certified",
            "why_selected_or_rejected": "backup only: observed supply is promising, but switching primary after toolz passed the local buildability and supply gates would expand Phase 0 scope.",
        },
        {
            "repo_id": "itsdangerous",
            "url": "https://github.com/pallets/itsdangerous.git",
            "language": "Python",
            "package_manager": "pyproject",
            "default_test_command": "python -m pytest",
            "install_command": "python -m pip install -e .[test]",
            "median_test_runtime_estimate_seconds": 5,
            "external_service_risk": "low",
            "candidate_anchor_estimate": "medium",
            "why_selected_or_rejected": "rejected for Phase 0 primary because task surface is smaller than toolz and overlaps Pallets/Click archive style.",
        },
        {
            "repo_id": "boltons",
            "url": "https://github.com/mahmoud/boltons.git",
            "language": "Python",
            "package_manager": "setuptools",
            "default_test_command": "python -m pytest",
            "install_command": "python -m pip install -e .",
            "median_test_runtime_estimate_seconds": 20,
            "external_service_risk": "low",
            "candidate_anchor_estimate": "medium",
            "why_selected_or_rejected": "backup candidate; broader utility surface but less immediately probed in this run.",
        },
        {
            "repo_id": "attrs",
            "url": "https://github.com/python-attrs/attrs.git",
            "language": "Python",
            "package_manager": "hatch/pyproject",
            "default_test_command": "python -m pytest",
            "install_command": "python -m pip install -e .[tests]",
            "median_test_runtime_estimate_seconds": 60,
            "external_service_risk": "low",
            "candidate_anchor_estimate": "high",
            "why_selected_or_rejected": "rejected for Phase 0 primary because the test/dependency matrix is broader than needed for the smallest evidence chain.",
        },
        {
            "repo_id": "rich",
            "url": "https://github.com/Textualize/rich.git",
            "language": "Python",
            "package_manager": "poetry/uv style pyproject",
            "default_test_command": "python -m pytest",
            "install_command": "project-specific dependency install",
            "median_test_runtime_estimate_seconds": 120,
            "external_service_risk": "medium",
            "candidate_anchor_estimate": "high",
            "why_selected_or_rejected": "rejected for Phase 0 primary because terminal rendering snapshots and dependency breadth increase oracle flakiness risk.",
        },
        {
            "repo_id": "requests",
            "url": "https://github.com/psf/requests.git",
            "language": "Python",
            "package_manager": "setuptools/pyproject",
            "default_test_command": "python -m pytest",
            "install_command": "python -m pip install -e .[socks]",
            "median_test_runtime_estimate_seconds": 120,
            "external_service_risk": "medium",
            "candidate_anchor_estimate": "high",
            "why_selected_or_rejected": "rejected for Phase 0 primary because HTTP integration history risks external-service assumptions.",
        },
    ]
    yaml_lines = ["repositories:"]
    for item in shortlist:
        yaml_lines.append(f"  - repo_id: {item['repo_id']}")
        for key, value in item.items():
            if key == "repo_id":
                continue
            yaml_lines.append(f"    {key}: {json.dumps(value)}")
    write_text(root / EXP_REL / "configs" / "repositories.yaml", "\n".join(yaml_lines) + "\n")
    rows = [
        "# Phase 0 Repository Selection",
        "",
        f"Primary selected repository: `{PRIMARY_REPO_ID}`.",
        "",
        "Selection used deterministic local evidence: reachable clone, Python compatibility, no external service requirement, changed-test smoke execution, and code-plus-test anchor count.",
        "",
        "## Primary Probe",
        "",
        f"- Local path: `{clone_info['local_path']}`",
        f"- Remote: `{clone_info['remote']}`",
        f"- HEAD: `{clone_info['head']}`",
        f"- Smoke command: `PYTHONPATH=. {python_command_display(root)} -m pytest toolz/tests -q --ignore=toolz/tests/test_package.py`",
        f"- Smoke exit code: `{smoke.returncode}`",
        f"- Smoke tail: `{' | '.join(smoke_tail)}`",
        f"- Code-plus-test history anchors since {HISTORY_SINCE}: `{anchor_count}`",
        f"- Code-plus-test anchors since {EXECUTABLE_SINCE}: `{executable_anchor_estimate}`",
        "",
        "## Shortlist",
        "",
        "| repo_id | selected role | local-risk note | candidate supply |",
        "|---|---|---|---:|",
    ]
    for item in shortlist:
        role = "primary" if item["repo_id"] == PRIMARY_REPO_ID else ("smoke" if item["repo_id"] == "click_archive_smoke" else "rejected_or_backup")
        rows.append(
            f"| `{item['repo_id']}` | {role} | {item['external_service_risk']}: {item['why_selected_or_rejected']} | {item['candidate_anchor_estimate']} |"
        )
    rows.extend(
        [
            "",
            "Acceptance: the primary target has deterministic local commands, low external-service risk, and enough mined anchors to attempt the 12-20 executable candidate target without model calls.",
            "",
        ]
    )
    write_text(root / EXP_REL / "reports" / "repository_selection.md", "\n".join(rows))
    append_process(
        root,
        "Step 2 Repository Selection",
        [
            f"- Selected `{PRIMARY_REPO_ID}` as primary and archived Click as smoke/generic comparator.",
            f"- Primary anchor estimate: `{anchor_count}` code-plus-test commits since `{HISTORY_SINCE}`.",
            f"- Smoke command exit code: `{smoke.returncode}`.",
            "- Next acceptance gate: target profile and distribution mismatch.",
        ],
    )


def click_generic_rows(root: Path) -> list[dict[str, Any]]:
    metadata = root / ARCHIVE_REL / "experiments/core_narrative/releases/click_r0_20260510/release_metadata.json"
    data = json.loads(metadata.read_text(encoding="utf-8"))
    rows = []
    for task in data.get("tasks", []):
        changed = task.get("source", {}).get("changed_files", [])
        modules = sorted({Path(path).stem for path in changed if path.endswith(".py") and "test" not in Path(path).stem})
        test_files = [path for path in changed if "test" in Path(path).stem]
        family = " ".join(task.get("task_family_tags", [])) or task.get("task_family", "")
        rows.append(
            {
                "task_id": task.get("task_id"),
                "module_or_package": modules or ["missing"],
                "task_type_proxy": task_type_proxy(family, changed),
                "changed_file_count": len(changed),
                "test_file_count": len(test_files),
                "change_size_bucket": "missing:numstat_not_in_archive",
                "source_type": task.get("source", {}).get("kind", "archive"),
                "task_family": family,
            }
        )
    return rows


def top_distribution_entry(dist: dict[str, float]) -> tuple[str, float]:
    if not dist:
        return "missing", 0.0
    return max(dist.items(), key=lambda item: item[1])


def write_profile_and_mismatch(root: Path, anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    early, late, cutoff = split_early_late(anchors)
    profile = {
        "repo_id": PRIMARY_REPO_ID,
        "repo_url": PRIMARY_REPO_URL,
        "history_since": HISTORY_SINCE,
        "cutoff": cutoff,
        "anchor_count": len(anchors),
        "early_count": len(early),
        "late_count": len(late),
        "feature_definitions": {
            "module_or_package": "Python module touched by changed production files.",
            "task_type_proxy": "Keyword proxy from commit subject and changed-file shape.",
            "changed_file_count": "Total files changed by the commit.",
            "change_size_bucket": "Bucketed added plus deleted lines from git numstat.",
            "test_file_count": "Changed Python test files under */tests/.",
            "dependency_radius_proxy": "Count of production modules touched.",
            "issue_or_pr_text_length": "Commit subject length; PR and issue body text not fetched in Phase 0.",
            "api_surface_touched": "Production modules touched.",
            "runtime_or_platform_constraints": "Keyword proxy for Python version/introspection vs pure local execution.",
        },
        "missing_data_labels": {
            "labels": "missing:not_fetched because the deterministic pass did not call GitHub issue or PR APIs.",
            "generic_change_size_bucket": "missing:numstat_not_in_archive for archived Click release metadata.",
        },
        "overall_distributions": {
            "module_or_package": distribution(anchors, "module_or_package"),
            "task_type_proxy": distribution(anchors, "task_type_proxy"),
            "change_size_bucket": distribution(anchors, "change_size_bucket"),
            "runtime_or_platform_constraints": distribution(anchors, "runtime_or_platform_constraints"),
        },
        "early_distributions": {
            "module_or_package": distribution(early, "module_or_package"),
            "task_type_proxy": distribution(early, "task_type_proxy"),
            "change_size_bucket": distribution(early, "change_size_bucket"),
        },
        "late_distributions": {
            "module_or_package": distribution(late, "module_or_package"),
            "task_type_proxy": distribution(late, "task_type_proxy"),
            "change_size_bucket": distribution(late, "change_size_bucket"),
        },
    }
    write_json(root / EXP_REL / "target_profiles" / f"{PRIMARY_REPO_ID}_target_profile.json", profile)

    generic = click_generic_rows(root)
    write_json(root / EXP_REL / "target_profiles" / "click_archive_generic_profile.json", {"rows": generic})

    mismatch_rows: list[dict[str, Any]] = []
    for feature in ["module_or_package", "task_type_proxy", "test_file_count", "changed_file_count", "change_size_bucket"]:
        target_dist = distribution(anchors, feature)
        generic_dist = distribution(generic, feature)
        keys = sorted(set(target_dist) | set(generic_dist))
        for key in keys:
            target_fraction = target_dist.get(key, 0.0)
            generic_fraction = generic_dist.get(key, 0.0)
            gap = abs(target_fraction - generic_fraction)
            if gap >= 0.15:
                mismatch_rows.append(
                    {
                        "feature_family": feature,
                        "feature_value": key,
                        "target_fraction": f"{target_fraction:.3f}",
                        "generic_fraction": f"{generic_fraction:.3f}",
                        "absolute_gap": f"{gap:.3f}",
                        "interpretation": "material_at_phase0_scope",
                    }
                )
    write_csv(
        root / EXP_REL / "results" / f"{PRIMARY_REPO_ID}_distribution_mismatch.csv",
        mismatch_rows,
        ["feature_family", "feature_value", "target_fraction", "generic_fraction", "absolute_gap", "interpretation"],
    )
    target_top_module, target_top_module_fraction = top_distribution_entry(distribution(anchors, "module_or_package"))
    generic_top_module, generic_top_module_fraction = top_distribution_entry(distribution(generic, "module_or_package"))
    report = [
        "# Phase 0 Distribution Mismatch",
        "",
        f"Primary target: `{PRIMARY_REPO_ID}`. Generic comparator: archived Click R0 metadata.",
        "",
        f"- Target anchors: `{len(anchors)}`.",
        f"- Early window count: `{len(early)}`.",
        f"- Late window count: `{len(late)}`.",
        f"- Cutoff used for early/late split: `{cutoff}`.",
        f"- Target top module: `{target_top_module}` at `{target_top_module_fraction:.1%}` of module touches.",
        f"- Generic Click top module: `{generic_top_module}` at `{generic_top_module_fraction:.1%}` of module touches.",
        f"- Mismatch rows with absolute gap >= 0.15: `{len(mismatch_rows)}`.",
        "",
        "The strongest Phase 0 mismatch is that `toolz` history is concentrated in functional-utility modules and includes maintenance/refactor/introspection work, while the archived Click comparator is a curated behavior-verifier mix centered on command-line option, prompt, and testing behavior. This is enough to treat a generic Click-like task mix as a weak estimator for `toolz` future work at this scope.",
        "",
        "Missing-data labels are explicit in the target profile. Issue and PR body text was not fetched in this deterministic pass.",
        "",
    ]
    write_text(root / EXP_REL / "reports" / "distribution_mismatch.md", "\n".join(report))
    append_process(
        root,
        "Step 3 Target Profile And Distribution Mismatch",
        [
            f"- Wrote `{EXP_REL / 'candidate_sources/toolz_history_anchors.jsonl'}` with `{len(anchors)}` anchors.",
            f"- Wrote target profile and `{len(mismatch_rows)}` mismatch rows.",
            "- Next acceptance gate: candidate supply and executable reconstruction.",
        ],
    )
    return mismatch_rows


def select_certification_candidates(anchors: list[dict[str, Any]], limit: int = CERTIFICATION_LIMIT) -> list[dict[str, Any]]:
    cutoff = datetime.fromisoformat(f"{EXECUTABLE_SINCE}T00:00:00+00:00")
    rows = [row for row in anchors if parse_iso(row["task_time"]) >= cutoff]
    rows = sorted(rows, key=lambda row: parse_iso(row["task_time"]))
    if len(rows) <= limit:
        selected = rows
    else:
        selected = []
        for index in range(limit):
            position = round(index * (len(rows) - 1) / (limit - 1))
            selected.append(rows[position])
    for index, row in enumerate(selected, start=1):
        row["task_id"] = f"toolz__hist__{index:03d}"
    return selected


def remove_worktree(repo: Path, path: Path) -> None:
    run_command(["git", "worktree", "remove", "--force", str(path)], repo, timeout=60)
    if path.exists():
        shutil.rmtree(path)
    run_command(["git", "worktree", "prune"], repo, timeout=60)


def add_worktree(repo: Path, path: Path, commit: str) -> CommandResult:
    remove_worktree(repo, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return run_command(["git", "worktree", "add", "--detach", str(path), commit], repo, timeout=120)


def command_tail(text: str, limit: int = 1200) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def review_gates(candidate: dict[str, Any]) -> dict[str, str]:
    subject = candidate["subject"].lower()
    gates = {
        "ambiguity_review": "pass" if len(candidate["subject"]) >= 12 and "nothing of substance" not in subject else "weak",
        "solution_leakage_review": "weak:commit_subject_and_public_diff_may_expose_solution",
        "scope_clarity_review": "pass" if candidate["changed_file_count"] <= 5 else "weak:multi_file_scope",
        "cost_boundedness": "pass",
        "taxonomy_labelability": "pass" if candidate["module_or_package"] and candidate["task_type_proxy"] else "weak",
    }
    return gates


def first_failing_gate(gates: dict[str, str]) -> str:
    order = [
        "checkout",
        "oracle_extractable",
        "no_op_fail",
        "reference_pass",
        "known_bad_fail",
        "flakiness_check",
        "ambiguity_review",
        "solution_leakage_review",
        "scope_clarity_review",
        "cost_boundedness",
        "taxonomy_labelability",
    ]
    for key in order:
        value = gates.get(key, "")
        if value.startswith("fail"):
            return key
    for key in order:
        value = gates.get(key, "")
        if value.startswith("weak"):
            return key
    return ""


def status_from_gates(gates: dict[str, str]) -> str:
    required = ["checkout", "oracle_extractable"]
    if any(gates.get(key, "").startswith("fail") for key in required):
        return "rejected"
    if gates.get("no_op_fail") != "pass" or gates.get("reference_pass") != "pass" or gates.get("known_bad_fail") != "pass":
        return "rejected"
    if gates.get("flakiness_check") != "pass":
        return "rejected"
    review_values = [
        gates.get("ambiguity_review", ""),
        gates.get("solution_leakage_review", ""),
        gates.get("scope_clarity_review", ""),
        gates.get("cost_boundedness", ""),
        gates.get("taxonomy_labelability", ""),
    ]
    if any(value.startswith("weak") for value in review_values):
        return "near_certified"
    if all(value == "pass" for value in review_values):
        return "certified"
    return "oracle_valid"


def certify_candidate(root: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    repo = root / PRIMARY_REPO_LOCAL
    raw_dir = root / RAW_REL / "certification"
    raw_dir.mkdir(parents=True, exist_ok=True)
    task_id = candidate["task_id"]
    base_ws = root / WORKSPACE_REL / "certification" / f"{task_id}_base"
    ref_ws = root / WORKSPACE_REL / "certification" / f"{task_id}_reference"
    gates: dict[str, str] = {}
    commands: list[dict[str, Any]] = []

    checkout = add_worktree(repo, base_ws, candidate["base_commit"])
    commands.append({"role": "checkout_base", "returncode": checkout.returncode, "stderr_tail": command_tail(checkout.stderr)})
    if checkout.returncode != 0:
        gates["checkout"] = "fail:base_worktree"
        debug_artifact(root, f"{task_id}-checkout", {"candidate": candidate, "result": checkout.__dict__})
        return {**candidate, "status": "rejected", "gates": gates, "first_failing_gate": "checkout", "commands": commands}
    gates["checkout"] = "pass"

    test_files = candidate["test_files"]
    patch = run_command(["git", "diff", candidate["base_commit"], candidate["target_commit"], "--", *test_files], repo)
    if patch.returncode != 0 or not patch.stdout.strip():
        gates["oracle_extractable"] = "fail:empty_or_unavailable_test_patch"
        debug_artifact(root, f"{task_id}-oracle", {"candidate": candidate, "result": patch.__dict__})
        remove_worktree(repo, base_ws)
        return {**candidate, "status": "rejected", "gates": gates, "first_failing_gate": "oracle_extractable", "commands": commands}
    apply_result = run_command(["git", "apply", "--index", "-"], base_ws, input_bytes=patch.stdout.encode("utf-8"))
    commands.append({"role": "apply_test_patch", "returncode": apply_result.returncode, "stderr_tail": command_tail(apply_result.stderr)})
    if apply_result.returncode != 0:
        gates["oracle_extractable"] = "fail:test_patch_apply"
        debug_artifact(root, f"{task_id}-oracle-apply", {"candidate": candidate, "result": apply_result.__dict__})
        remove_worktree(repo, base_ws)
        return {**candidate, "status": "rejected", "gates": gates, "first_failing_gate": "oracle_extractable", "commands": commands}
    gates["oracle_extractable"] = "pass"

    env_base = {**os.environ, "PYTHONPATH": str(base_ws)}
    noop = run_command(
        [*python_command(root), "-m", "pytest", "-q", *test_files],
        base_ws,
        timeout=CERTIFICATION_TIMEOUT_SECONDS,
        env=env_base,
    )
    write_text(raw_dir / f"{task_id}_noop.txt", noop.stdout + "\n" + noop.stderr)
    commands.append(
        {
            "role": "noop_test_patch_on_base",
            "returncode": noop.returncode,
            "duration_seconds": round(noop.duration_seconds, 3),
            "timed_out": noop.timed_out,
            "stdout_tail": command_tail(noop.stdout + noop.stderr),
        }
    )
    gates["no_op_fail"] = "pass" if noop.returncode != 0 and not noop.timed_out else "fail:no_op_passed_or_timed_out"
    gates["known_bad_fail"] = gates["no_op_fail"]
    remove_worktree(repo, base_ws)

    ref_checkout = add_worktree(repo, ref_ws, candidate["target_commit"])
    commands.append({"role": "checkout_reference", "returncode": ref_checkout.returncode, "stderr_tail": command_tail(ref_checkout.stderr)})
    if ref_checkout.returncode != 0:
        gates["reference_pass"] = "fail:reference_worktree"
        debug_artifact(root, f"{task_id}-reference-checkout", {"candidate": candidate, "result": ref_checkout.__dict__})
        return {**candidate, "status": "rejected", "gates": gates, "first_failing_gate": "reference_pass", "commands": commands}
    env_ref = {**os.environ, "PYTHONPATH": str(ref_ws)}
    ref_runs = []
    for run_index in [1, 2]:
        ref = run_command(
            [*python_command(root), "-m", "pytest", "-q", *test_files],
            ref_ws,
            timeout=CERTIFICATION_TIMEOUT_SECONDS,
            env=env_ref,
        )
        write_text(raw_dir / f"{task_id}_reference_{run_index}.txt", ref.stdout + "\n" + ref.stderr)
        ref_runs.append(ref)
        commands.append(
            {
                "role": f"reference_run_{run_index}",
                "returncode": ref.returncode,
                "duration_seconds": round(ref.duration_seconds, 3),
                "timed_out": ref.timed_out,
                "stdout_tail": command_tail(ref.stdout + ref.stderr),
            }
        )
    remove_worktree(repo, ref_ws)
    gates["reference_pass"] = "pass" if ref_runs[0].returncode == 0 and not ref_runs[0].timed_out else "fail:reference_failed"
    gates["flakiness_check"] = (
        "pass"
        if all(result.returncode == 0 and not result.timed_out for result in ref_runs)
        else "fail:reference_rerun_failed_or_timed_out"
    )
    gates.update(review_gates(candidate))
    status = status_from_gates(gates)
    first_gate = first_failing_gate(gates)
    return {
        **candidate,
        "status": status,
        "gates": gates,
        "first_failing_gate": first_gate,
        "manual_review_minutes": 0,
        "runtime_seconds_estimate": round(sum(command.get("duration_seconds", 0.0) for command in commands), 3),
        "commands": commands,
    }


def write_candidate_supply(root: Path, anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = select_certification_candidates(anchors)
    candidates = []
    for row in selected:
        candidates.append(
            {
                "task_id": row["task_id"],
                "repo_id": row["repo_id"],
                "source_type": row["source_type"],
                "base_commit": row["base_commit"],
                "target_commit": row["target_commit"],
                "task_time": row["task_time"],
                "changed_files": row["changed_files"],
                "source_text_pointers": row["source_text_pointers"],
                "candidate_oracle_source": row["candidate_oracle_source"],
                "leakage_risks": row["leakage_risks"],
                "taxonomy_draft": row["taxonomy_draft"],
                "problem_statement_source": "commit_subject_only",
                "problem_statement_draft": row["subject"],
                "status": "candidate",
            }
        )
    write_jsonl(root / EXP_REL / "candidate_sources" / f"{PRIMARY_REPO_ID}_candidates.jsonl", candidates)
    write_jsonl(root / EXP_REL / "candidate_sources" / f"{PRIMARY_REPO_ID}_history_anchors.jsonl", anchors)

    certified = []
    for candidate in selected:
        certified.append(certify_candidate(root, candidate))

    status_counts = Counter(row["status"] for row in certified)
    supply_rows = []
    for status in ["candidate", "executable", "oracle_valid", "certified", "near_certified", "rejected"]:
        if status == "candidate":
            count = len(candidates)
        elif status == "executable":
            count = sum(row["gates"].get("checkout") == "pass" and row["gates"].get("oracle_extractable") == "pass" for row in certified)
        elif status == "oracle_valid":
            count = sum(
                row["gates"].get("no_op_fail") == "pass"
                and row["gates"].get("reference_pass") == "pass"
                and row["gates"].get("known_bad_fail") == "pass"
                for row in certified
            )
        else:
            count = status_counts.get(status, 0)
        supply_rows.append({"stage": status, "count": count})
    write_csv(root / EXP_REL / "candidate_sources" / f"{PRIMARY_REPO_ID}_supply_funnel.csv", supply_rows, ["stage", "count"])
    return certified


def write_certification_outputs(root: Path, certified: list[dict[str, Any]]) -> None:
    funnel_rows = []
    for row in certified:
        gates = row["gates"]
        funnel_rows.append(
            {
                "task_id": row["task_id"],
                "status": row["status"],
                "first_failing_gate": row.get("first_failing_gate", ""),
                "checkout": gates.get("checkout", ""),
                "oracle_extractable": gates.get("oracle_extractable", ""),
                "no_op_fail": gates.get("no_op_fail", ""),
                "reference_pass": gates.get("reference_pass", ""),
                "known_bad_fail": gates.get("known_bad_fail", ""),
                "flakiness_check": gates.get("flakiness_check", ""),
                "ambiguity_review": gates.get("ambiguity_review", ""),
                "solution_leakage_review": gates.get("solution_leakage_review", ""),
                "scope_clarity_review": gates.get("scope_clarity_review", ""),
                "cost_boundedness": gates.get("cost_boundedness", ""),
                "taxonomy_labelability": gates.get("taxonomy_labelability", ""),
                "manual_review_minutes": row.get("manual_review_minutes", 0),
                "runtime_seconds_estimate": row.get("runtime_seconds_estimate", 0),
            }
        )
    write_csv(
        root / EXP_REL / "certified_tasks" / f"{PRIMARY_REPO_ID}_certification_funnel.csv",
        funnel_rows,
        [
            "task_id",
            "status",
            "first_failing_gate",
            "checkout",
            "oracle_extractable",
            "no_op_fail",
            "reference_pass",
            "known_bad_fail",
            "flakiness_check",
            "ambiguity_review",
            "solution_leakage_review",
            "scope_clarity_review",
            "cost_boundedness",
            "taxonomy_labelability",
            "manual_review_minutes",
            "runtime_seconds_estimate",
        ],
    )
    certified_rows = [row for row in certified if row["status"] == "certified"]
    near_rows = [row for row in certified if row["status"] == "near_certified"]
    write_jsonl(root / EXP_REL / "certified_tasks" / f"{PRIMARY_REPO_ID}_certified_tasks.jsonl", certified_rows)
    write_jsonl(root / EXP_REL / "certified_tasks" / f"{PRIMARY_REPO_ID}_near_certified_tasks.jsonl", near_rows)

    status_counts = Counter(row["status"] for row in certified)
    oracle_valid = sum(
        row["gates"].get("no_op_fail") == "pass"
        and row["gates"].get("reference_pass") == "pass"
        and row["gates"].get("known_bad_fail") == "pass"
        for row in certified
    )
    executable = sum(row["gates"].get("checkout") == "pass" and row["gates"].get("oracle_extractable") == "pass" for row in certified)
    report = [
        "# Phase 0 Certification Funnel",
        "",
        f"- Candidates attempted: `{len(certified)}`",
        f"- Executable candidates: `{executable}`",
        f"- Oracle-valid candidates: `{oracle_valid}`",
        f"- Certified benchmark-grade tasks: `{len(certified_rows)}`",
        f"- Near-certified tasks: `{len(near_rows)}`",
        f"- Rejected tasks: `{status_counts.get('rejected', 0)}`",
        "- Manual review minutes: `0` in this deterministic pass.",
        "",
        "All near-certified tasks passed the mechanical oracle gates but retain weak leakage review because the only generated statement is the commit subject and the public reference patch is part of the same Git history. They are separated from certified tasks and do not count toward a benchmark-grade release.",
        "",
        "Raw pytest tails are stored under ignored `experiments/phase0_headroom/results/raw/certification/` and referenced by task id.",
        "",
    ]
    write_text(root / EXP_REL / "reports" / "certification_funnel.md", "\n".join(report))
    append_process(
        root,
        "Steps 4-5 Candidate Supply And Certification",
        [
            f"- Attempted `{len(certified)}` candidates.",
            f"- Executable `{executable}`, oracle-valid `{oracle_valid}`, certified `{len(certified_rows)}`, near-certified `{len(near_rows)}`.",
            "- Next acceptance gate: mini release assembly with diagnostic label if certified yield remains below 6.",
        ],
    )


def choose_split_tasks(rows: list[dict[str, Any]], split: str, count: int) -> list[dict[str, Any]]:
    sorted_rows = sorted(rows, key=lambda row: parse_iso(row["task_time"]))
    if split == "B_real":
        return sorted_rows[:count]
    if split == "W_real":
        return sorted_rows[-count:]
    return []


def write_mini_release(root: Path, certified: list[dict[str, Any]]) -> None:
    certified_rows = [row for row in certified if row["status"] == "certified"]
    near_rows = [row for row in certified if row["status"] == "near_certified"]
    b_rows = choose_split_tasks(near_rows if len(certified_rows) < 6 else certified_rows, "B_real", 4)
    w_rows = choose_split_tasks(near_rows if len(certified_rows) < 6 else certified_rows, "W_real", 4)
    generic = click_generic_rows(root)[:4]
    release_status = "benchmark_grade" if len(certified_rows) >= 6 else "diagnostic_only"
    tasks = []
    for split_name, rows in [("B_real", b_rows), ("W_real", w_rows)]:
        for row in rows:
            tasks.append(
                {
                    "task_id": row["task_id"],
                    "split": split_name,
                    "weight": 1.0,
                    "certification_status": row["status"],
                    "counts_toward_benchmark_grade": row["status"] == "certified",
                    "module_or_package": row["module_or_package"],
                    "task_type_proxy": row["task_type_proxy"],
                }
            )
    for row in generic:
        tasks.append(
            {
                "task_id": row["task_id"],
                "split": "G_mini",
                "weight": 1.0,
                "certification_status": "archived_click_release_metadata",
                "counts_toward_benchmark_grade": False,
                "module_or_package": row["module_or_package"],
                "task_type_proxy": row["task_type_proxy"],
            }
        )
    release = {
        "schema_version": "barcarolle.phase0_mini_release.v1",
        "repo_id": PRIMARY_REPO_ID,
        "release_id": f"{PRIMARY_REPO_ID}-phase0-mini-diagnostic",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "release_status": release_status,
        "benchmark_grade": release_status == "benchmark_grade",
        "diagnostic_reason": ""
        if release_status == "benchmark_grade"
        else "fewer than 6 certified tasks; near-certified tasks are listed for diagnosis only",
        "certified_task_count": len(certified_rows),
        "near_certified_task_count": len(near_rows),
        "splits": {
            "B_real": [row["task_id"] for row in b_rows],
            "W_real": [row["task_id"] for row in w_rows],
            "G_mini": [row["task_id"] for row in generic],
        },
        "weighting": "unweighted; no benchmark-grade stratified weights because certified yield is below threshold",
        "tasks": tasks,
    }
    write_json(root / EXP_REL / "releases" / f"{PRIMARY_REPO_ID}_phase0_mini_release.json", release)
    write_csv(
        root / EXP_REL / "releases" / f"{PRIMARY_REPO_ID}_phase0_task_table.csv",
        tasks,
        [
            "task_id",
            "split",
            "weight",
            "certification_status",
            "counts_toward_benchmark_grade",
            "module_or_package",
            "task_type_proxy",
        ],
    )
    report = [
        "# Phase 0 Mini Release",
        "",
        f"Release status: `{release_status}`.",
        "",
        f"- Certified tasks: `{len(certified_rows)}`.",
        f"- Near-certified tasks available for diagnosis: `{len(near_rows)}`.",
        f"- `B_real` diagnostic tasks: `{len(b_rows)}`.",
        f"- `W_real` diagnostic tasks: `{len(w_rows)}`.",
        f"- `G_mini` archived Click comparator tasks: `{len(generic)}`.",
        "",
        "Because the release has fewer than 6 certified tasks, it is not benchmark-grade. Near-certified tasks are visible in the task table but are excluded from benchmark-grade counts.",
        "",
    ]
    write_text(root / EXP_REL / "reports" / "mini_release.md", "\n".join(report))
    append_process(
        root,
        "Step 6 Mini Release Assembly",
        [
            f"- Wrote `{release_status}` release manifest.",
            f"- Certified task count `{len(certified_rows)}`; near-certified diagnostic count `{len(near_rows)}`.",
            "- Next acceptance gate: headroom analysis must either run a budgeted matrix or state the precise blocker.",
        ],
    )


def write_headroom_and_decision(root: Path, certified: list[dict[str, Any]], mismatch_rows: list[dict[str, Any]]) -> None:
    certified_rows = [row for row in certified if row["status"] == "certified"]
    near_rows = [row for row in certified if row["status"] == "near_certified"]
    matrix = {
        "schema_version": "barcarolle.phase0_headroom_matrix.v1",
        "status": "blocked",
        "blocker": "mini release is diagnostic only because certified task count is below 6",
        "paid_model_calls_started": 0,
        "cumulative_estimated_cost_usd": read_cumulative_cost(root / EXP_REL / "results" / "cost_ledger.jsonl"),
        "requested_comparisons": ["G_mini -> W_real", "B_real -> W_real", "G_mini + B_real -> W_real"],
        "missing_cells": [
            "B_real and W_real have near-certified diagnostic tasks only",
            "no ACUT task-solving runs were started",
            "G_mini uses archived Click metadata and has no current same-protocol ACUT cells",
        ],
    }
    metrics = {
        "schema_version": "barcarolle.phase0_headroom_metrics.v1",
        "status": "underpowered_blocked",
        "mae": None,
        "rmse": None,
        "brier_score": None,
        "binomial_negative_log_likelihood": None,
        "directional_diagnostics": "not computed; certification blocker must be repaired before spending ACUT budget",
    }
    write_json(root / EXP_REL / "results" / "headroom_matrix.json", matrix)
    write_json(root / EXP_REL / "results" / "headroom_metrics.json", metrics)
    headroom_report = [
        "# Phase 0 Headroom Analysis",
        "",
        "Status: `blocked_underpowered`.",
        "",
        "No paid task-solving batch was started. The budget gate was satisfied with cumulative estimated cost USD 0.00, but the mini release is diagnostic only. Running ACUTs on near-certified tasks would spend budget without producing benchmark-grade predictive evidence.",
        "",
        "Missing comparison cells:",
        "",
        "- `B_real -> W_real`: blocked because both splits contain near-certified diagnostic tasks only.",
        "- `G_mini -> W_real`: blocked because archived Click comparator tasks do not share a current ACUT run protocol with the diagnostic `toolz` tasks.",
        "- `G_mini + B_real -> W_real`: blocked by both missing inputs above.",
        "",
        "MAE/RMSE are not reported because the matrix has zero scoreable ACUT cells.",
        "",
    ]
    write_text(root / EXP_REL / "reports" / "headroom_analysis.md", "\n".join(headroom_report))

    decision = "repair_source_adapter"
    memo = [
        "# Phase 0 Decision Memo",
        "",
        f"Decision: `{decision}`.",
        "",
        "## Scope",
        "",
        f"- Smoke/generic comparator: archived Click R0 metadata.",
        f"- Primary target repo: `{PRIMARY_REPO_ID}`.",
        "- Paid LLM API spend: `USD 0.00`.",
        f"- Ledger path: `{EXP_REL / 'results/cost_ledger.jsonl'}`.",
        "",
        "## Evidence",
        "",
        f"- Distribution mismatch rows with absolute gap >= 0.15: `{len(mismatch_rows)}`.",
        f"- Certification attempted tasks: `{len(certified)}`.",
        f"- Certified benchmark-grade tasks: `{len(certified_rows)}`.",
        f"- Near-certified diagnostic tasks: `{len(near_rows)}`.",
        "- Mini release status: `diagnostic_only`.",
        "- Headroom matrix: `blocked_underpowered`; no ACUT runs started.",
        "",
        "## Interpretation",
        "",
        "The target-profile and supply layers are viable enough to keep the restart alive: `toolz` yields many code-plus-test anchors and several candidates can be mechanically replayed through no-op/reference gates. The certification layer is the blocker. Deterministic commit-subject tasks do not provide sufficient non-leaky, scope-reviewed problem statements, so they cannot be counted as benchmark-grade tasks.",
        "",
        "## Threats To Validity",
        "",
        "- One primary target repository only.",
        "- Generic comparator is archived Click metadata, not a fresh public benchmark sample.",
        "- Issue and PR body text were not fetched, so ambiguity and leakage reviews are intentionally weak.",
        "- No ACUT task-solving runs were performed.",
        "",
        "## Next Smallest Useful Experiment",
        "",
        "Build a source adapter that fetches PR or issue text and produces non-leaky candidate statements for the existing oracle-valid `toolz` anchors. Re-run certification until at least 6 tasks are certified, then run one cheap ACUT across 4 `B_real`, 4 `W_real`, and 4 `G_mini` tasks under the same ledger gate.",
        "",
    ]
    write_text(root / EXP_REL / "reports" / "phase0_decision_memo.md", "\n".join(memo))
    append_process(
        root,
        "Steps 7-8 Headroom Analysis And Decision",
        [
            "- Did not start paid model calls.",
            "- Wrote blocked headroom matrix and decision memo.",
            f"- Decision: `{decision}`.",
            "- Next acceptance gate: commit hygiene and completion audit.",
        ],
    )


def write_raw_artifact_manifest(root: Path) -> None:
    raw_root = root / RAW_REL
    files = sorted(path for path in raw_root.rglob("*") if path.is_file())
    raw_entries = []
    for path in files:
        raw_entries.append(
            {
                "path": str(path.relative_to(root)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "producer": "phase0_driver.py certification pytest probe",
            }
        )
    external_repos = []
    for repo_id in [PRIMARY_REPO_ID, "humanize"]:
        repo_path = root / EXP_REL / "external_repos" / repo_id
        if not (repo_path / ".git").exists():
            continue
        head = run_command(["git", "rev-parse", "HEAD"], repo_path)
        remote = run_command(["git", "remote", "get-url", "origin"], repo_path)
        external_repos.append(
            {
                "repo_id": repo_id,
                "path": str(repo_path.relative_to(root)),
                "head": head.stdout.strip() if head.returncode == 0 else "unknown",
                "remote": remote.stdout.strip() if remote.returncode == 0 else "unknown",
                "tracked_in_git": False,
            }
        )
    manifest = {
        "schema_version": "barcarolle.phase0_raw_artifact_manifest.v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "raw_root": str(RAW_REL),
        "raw_files": raw_entries,
        "external_repositories": external_repos,
        "git_policy": "raw files and external repositories are ignored; this manifest is the committed reference.",
    }
    write_json(root / EXP_REL / "results" / "raw_artifact_manifest.json", manifest)


def run_all(root: Path) -> None:
    initialize_preflight(root)
    write_budget_configs(root)
    clone_info = clone_or_update_primary(root)
    anchors = extract_history_anchors(root)
    write_repository_selection(root, anchors, clone_info)
    mismatch_rows = write_profile_and_mismatch(root, anchors)
    certified = write_candidate_supply(root, anchors)
    write_certification_outputs(root, certified)
    write_mini_release(root, certified)
    write_headroom_and_decision(root, certified, mismatch_rows)
    write_raw_artifact_manifest(root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Phase 0 headroom experiment driver.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        run_all(root)
    except Exception as exc:
        debug_artifact(root, "phase0-driver-failure", {"error": str(exc)})
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
