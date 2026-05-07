#!/usr/bin/env python3
"""Regression self-check for ACUT workspace history leakage."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from _common import ToolError, emit_json, fail, git, write_json


TOOL = "check_workspace_leakage"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a synthetic Git repository, prepare a workspace at the base "
            "commit, and prove the target commit is absent from refs and the "
            "workspace object database."
        )
    )
    parser.add_argument("--work-dir", help="Optional directory for synthetic inputs; defaults to a temp dir.")
    parser.add_argument("--keep", action="store_true", help="Keep the synthetic work directory after the check.")
    parser.add_argument("--output", help="Optional path for the structured JSON summary.")
    return parser.parse_args()


def run_git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    result = git(*args, cwd=cwd)
    if result.returncode != 0:
        raise ToolError(
            "git command failed while building leakage self-check fixture",
            command=["git", *args],
            cwd=str(cwd),
            stderr=result.stderr.strip(),
        )
    return result


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_fixture(root: Path) -> tuple[Path, Path, Path, str, str]:
    source_repo = root / "source-repo"
    task_dir = root / "task"
    workspace = root / "workspace"
    source_repo.mkdir(parents=True)
    task_dir.mkdir(parents=True)

    run_git(["init"], cwd=source_repo)
    run_git(["config", "user.name", "Core Narrative Self Check"], cwd=source_repo)
    run_git(["config", "user.email", "core-narrative-self-check@example.invalid"], cwd=source_repo)

    write_text(source_repo / "story.txt", "base-visible content\n")
    run_git(["add", "story.txt"], cwd=source_repo)
    run_git(["commit", "--no-gpg-sign", "-m", "base commit"], cwd=source_repo)
    base_commit = run_git(["rev-parse", "HEAD"], cwd=source_repo).stdout.strip()

    write_text(source_repo / "story.txt", "base-visible content\nfuture-only solution\n")
    write_text(source_repo / "future_solution.txt", "target-only content\n")
    run_git(["add", "story.txt", "future_solution.txt"], cwd=source_repo)
    run_git(["commit", "--no-gpg-sign", "-m", "target commit"], cwd=source_repo)
    target_commit = run_git(["rev-parse", "HEAD"], cwd=source_repo).stdout.strip()

    write_text(task_dir / "statement.md", "Make the public behavior pass.\n")
    task = {
        "task_id": "fixture_repo__leakage__1",
        "repo_slug": "fixture_repo",
        "split": "rbench",
        "source": {
            "kind": "commit",
            "public_url": None,
            "anchor_id": "synthetic-target",
            "base_commit": base_commit,
            "target_commit": target_commit,
        },
        "task_family": "leakage_regression",
        "task_statement_path": "statement.md",
        "allowed_context": {
            "include_git_history_before_base": False,
            "include_issue_text": False,
            "include_pr_text": False,
            "include_reference_patch": False,
        },
    }
    task_path = task_dir / "task.json"
    write_json(task_path, task)
    return source_repo, task_path, workspace, base_commit, target_commit


def run_prepare_workspace(task_path: Path, source_repo: Path, workspace: Path) -> dict[str, Any]:
    tool_path = Path(__file__).with_name("prepare_workspace.py")
    completed = subprocess.run(
        [
            sys.executable,
            str(tool_path),
            "--task",
            str(task_path),
            "--source-repo",
            str(source_repo),
            "--workspace",
            str(workspace),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ToolError(
            "prepare_workspace.py failed during leakage self-check",
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ToolError("prepare_workspace.py did not emit JSON", stdout=completed.stdout) from exc
    if not isinstance(payload, dict):
        raise ToolError("prepare_workspace.py JSON output must be an object")
    return payload


def assert_target_absent(workspace: Path, target_commit: str) -> dict[str, Any]:
    show_ref = git("show-ref", cwd=workspace)
    if show_ref.returncode not in {0, 1}:
        raise ToolError("failed to inspect workspace refs", stderr=show_ref.stderr.strip())
    refs = show_ref.stdout.splitlines()
    refs_containing_target = [line for line in refs if target_commit in line]
    if refs_containing_target:
        raise ToolError(
            "target commit leaked through workspace refs",
            target_commit=target_commit,
            refs=refs_containing_target,
        )

    cat_file = git("cat-file", "-e", f"{target_commit}^{{commit}}", cwd=workspace)
    if cat_file.returncode == 0:
        raise ToolError(
            "target commit leaked into workspace object database",
            target_commit=target_commit,
        )

    rev_list = git("rev-list", "--all", cwd=workspace)
    if rev_list.returncode != 0:
        raise ToolError("failed to inspect workspace reachable commits", stderr=rev_list.stderr.strip())
    reachable_commits = rev_list.stdout.splitlines()
    if target_commit in reachable_commits:
        raise ToolError(
            "target commit is reachable from workspace history",
            target_commit=target_commit,
        )

    task_package = workspace / ".core_narrative" / "task.json"
    if not task_package.exists():
        raise ToolError("prepared task package is missing", path=str(task_package))
    package_text = task_package.read_text(encoding="utf-8")
    if target_commit in package_text:
        raise ToolError(
            "target commit leaked into ACUT-visible task package",
            target_commit=target_commit,
            task_package=str(task_package),
        )

    return {
        "ref_count": len(refs),
        "reachable_commit_count": len(reachable_commits),
        "target_absent_from_refs": True,
        "target_absent_from_object_database": True,
        "target_absent_from_task_package": True,
    }


def main() -> int:
    args = parse_args()
    root = Path(args.work_dir) if args.work_dir else Path(tempfile.mkdtemp(prefix="core-narrative-leakage-"))
    created_temp = args.work_dir is None

    try:
        if root.exists() and any(root.iterdir()):
            raise ToolError("self-check work directory must be empty", work_dir=str(root))
        root.mkdir(parents=True, exist_ok=True)
        source_repo, task_path, workspace, base_commit, target_commit = build_fixture(root)
        prepare_payload = run_prepare_workspace(task_path, source_repo, workspace)
        leakage = assert_target_absent(workspace, target_commit)
        payload = {
            "tool": TOOL,
            "status": "passed",
            "work_dir": str(root),
            "workspace": str(workspace),
            "base_commit": base_commit,
            "target_commit": target_commit,
            "prepare_status": prepare_payload.get("status"),
            "leakage": leakage,
        }
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)
    finally:
        if created_temp and not args.keep:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
