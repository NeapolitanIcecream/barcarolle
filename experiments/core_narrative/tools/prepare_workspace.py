#!/usr/bin/env python3
"""Prepare a clean task workspace from a local target repository checkout."""

from __future__ import annotations

import argparse
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

from _common import (
    ToolError,
    emit_json,
    fail,
    git,
    iso_now,
    load_manifest,
    require_keys,
    require_mapping,
    write_json,
)


TOOL = "prepare_workspace"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export the task base commit from a local target repository into a "
            "fresh synthetic Git workspace and write an ACUT-visible task package."
        )
    )
    parser.add_argument("--task", required=True, help="Task manifest JSON/YAML path.")
    parser.add_argument("--source-repo", required=True, help="Local target repository checkout to export from.")
    parser.add_argument("--workspace", required=True, help="Workspace path to create.")
    parser.add_argument("--force", action="store_true", help="Remove an existing workspace first.")
    parser.add_argument("--output", help="Optional path for the structured JSON summary.")
    return parser.parse_args()


def ensure_git_repo(path: Path, label: str) -> None:
    result = git("rev-parse", "--is-inside-work-tree", cwd=path)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise ToolError(f"{label} is not a git work tree", path=str(path), stderr=result.stderr.strip())


def remove_existing_workspace(path: Path, *, force: bool) -> None:
    if not path.exists():
        return
    if not force:
        raise ToolError("workspace already exists; pass --force to replace it", workspace=str(path))
    resolved = path.resolve()
    if resolved == Path("/") or resolved == Path.home():
        raise ToolError("refusing to remove unsafe workspace path", workspace=str(path))
    shutil.rmtree(path)


def ensure_commit_exists(source_repo: Path, commit: str, label: str) -> None:
    result = git("cat-file", "-e", f"{commit}^{{commit}}", cwd=source_repo)
    if result.returncode != 0:
        raise ToolError(
            f"{label} is not a commit in the source repository",
            commit=commit,
            stderr=result.stderr.strip(),
        )


def ensure_tar_member_safe(member: tarfile.TarInfo, destination: Path) -> None:
    destination_root = destination.resolve()
    target = (destination / member.name).resolve()
    try:
        target.relative_to(destination_root)
    except ValueError as exc:
        raise ToolError("git archive contains an unsafe path", path=member.name) from exc

    if member.islnk() or member.issym():
        link_base = destination if member.islnk() else (destination / member.name).parent
        link_target = (link_base / member.linkname).resolve()
        try:
            link_target.relative_to(destination_root)
        except ValueError as exc:
            link_type = "symlink" if member.issym() else "hardlink"
            raise ToolError(f"git archive contains an unsafe {link_type}", path=member.name, link=member.linkname) from exc


def extract_archive_safely(archive_path: Path, destination: Path) -> None:
    with tarfile.open(archive_path, "r") as archive:
        for member in archive.getmembers():
            ensure_tar_member_safe(member, destination)
        archive.extractall(destination)


def run_git_checked(args: list[str], *, cwd: Path, message: str) -> None:
    result = git(*args, cwd=cwd)
    if result.returncode != 0:
        raise ToolError(message, command=["git", *args], cwd=str(cwd), stderr=result.stderr.strip())


def create_base_only_workspace(source_repo: Path, workspace: Path, base_commit: str, target_commit: str | None) -> None:
    ensure_commit_exists(source_repo, base_commit, "base_commit")
    workspace.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="core-narrative-base-archive-") as temp_dir:
        archive_path = Path(temp_dir) / "base.tar"
        archive = git("archive", "--format=tar", "--output", str(archive_path), base_commit, cwd=source_repo)
        if archive.returncode != 0:
            raise ToolError(
                "failed to export base commit tree",
                base_commit=base_commit,
                stderr=archive.stderr.strip(),
            )
        extract_archive_safely(archive_path, workspace)

    run_git_checked(["init"], cwd=workspace, message="failed to initialize synthetic workspace git repo")
    run_git_checked(
        ["config", "user.name", "Core Narrative Workspace"],
        cwd=workspace,
        message="failed to configure workspace git user name",
    )
    run_git_checked(
        ["config", "user.email", "core-narrative-workspace@example.invalid"],
        cwd=workspace,
        message="failed to configure workspace git user email",
    )
    run_git_checked(["add", "--all"], cwd=workspace, message="failed to stage base workspace tree")
    run_git_checked(
        ["commit", "--no-gpg-sign", "--allow-empty", "-m", f"core narrative base tree {base_commit}"],
        cwd=workspace,
        message="failed to commit synthetic base workspace tree",
    )

    if target_commit:
        target_check = git("cat-file", "-e", f"{target_commit}^{{commit}}", cwd=workspace)
        if target_check.returncode == 0:
            raise ToolError("target commit is present in prepared workspace object database")


def write_task_package(task: dict[str, object], task_path: Path, workspace: Path) -> tuple[Path, Path | None, list[str]]:
    warnings: list[str] = []
    package_dir = workspace / ".core_narrative"
    package_dir.mkdir(parents=True, exist_ok=True)

    source = require_mapping(task.get("source"), "task.source")
    safe_source = {
        "kind": source.get("kind"),
        "public_url": source.get("public_url"),
        "base_commit": source.get("base_commit"),
    }
    safe_task = {
        "schema_version": "core-narrative.task-package.v1",
        "prepared_at": iso_now(),
        "task_id": task.get("task_id"),
        "repo_slug": task.get("repo_slug"),
        "split": task.get("split"),
        "task_family": task.get("task_family"),
        "source": safe_source,
        "allowed_context": task.get("allowed_context", {}),
        "workspace_history": {
            "mode": "base_tree_only_synthetic_git",
            "future_history_available": False,
        },
    }

    statement_path: Path | None = None
    manifest_statement = task.get("task_statement_path")
    if isinstance(manifest_statement, str) and manifest_statement:
        candidate = (task_path.parent / manifest_statement).resolve()
        if candidate.exists():
            statement_path = package_dir / "statement.md"
            shutil.copy2(candidate, statement_path)
            safe_task["task_statement_path"] = str(statement_path.relative_to(workspace))
        else:
            warnings.append(f"task statement was not found: {candidate}")
            safe_task["task_statement_path"] = None
    else:
        warnings.append("task_statement_path is empty or missing")
        safe_task["task_statement_path"] = None

    metadata_path = package_dir / "task.json"
    write_json(metadata_path, safe_task)
    return metadata_path, statement_path, warnings


def main() -> int:
    args = parse_args()
    try:
        task_path = Path(args.task)
        source_repo = Path(args.source_repo)
        workspace = Path(args.workspace)

        task = load_manifest(task_path)
        require_keys(task, ["task_id", "repo_slug", "split", "source", "task_family"], "task manifest")
        source = require_mapping(task.get("source"), "task.source")
        require_keys(source, ["base_commit"], "task.source")
        base_commit = str(source["base_commit"])
        raw_target_commit = source.get("target_commit")
        target_commit = str(raw_target_commit) if isinstance(raw_target_commit, str) and raw_target_commit else None

        ensure_git_repo(source_repo, "source repo")
        remove_existing_workspace(workspace, force=args.force)
        create_base_only_workspace(source_repo, workspace, base_commit, target_commit)

        metadata_path, statement_path, warnings = write_task_package(task, task_path, workspace)
        payload = {
            "tool": TOOL,
            "status": "prepared",
            "task_id": task["task_id"],
            "repo_slug": task["repo_slug"],
            "split": task["split"],
            "workspace": str(workspace),
            "base_commit": base_commit,
            "workspace_history_mode": "base_tree_only_synthetic_git",
            "target_commit_absence_checked": target_commit is not None,
            "task_package_path": str(metadata_path),
            "statement_path": str(statement_path) if statement_path is not None else None,
            "warnings": warnings,
        }
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
