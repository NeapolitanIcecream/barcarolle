#!/usr/bin/env python3
"""Prepare a clean task workspace from a local target repository checkout."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from _common import ToolError, emit_json, fail, git, iso_now, load_manifest, require_keys, require_mapping, write_json


TOOL = "prepare_workspace"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Clone a local target repository into a task workspace, check out the "
            "task base commit, and write an ACUT-visible task package."
        )
    )
    parser.add_argument("--task", required=True, help="Task manifest JSON/YAML path.")
    parser.add_argument("--source-repo", required=True, help="Local target repository checkout to clone.")
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

        ensure_git_repo(source_repo, "source repo")
        remove_existing_workspace(workspace, force=args.force)

        clone = git("clone", "--no-hardlinks", str(source_repo), str(workspace))
        if clone.returncode != 0:
            raise ToolError("git clone failed", stderr=clone.stderr.strip())

        checkout = git("checkout", "--detach", base_commit, cwd=workspace)
        if checkout.returncode != 0:
            raise ToolError(
                "failed to check out task base commit",
                base_commit=base_commit,
                stderr=checkout.stderr.strip(),
            )

        metadata_path, statement_path, warnings = write_task_package(task, task_path, workspace)
        payload = {
            "tool": TOOL,
            "status": "prepared",
            "task_id": task["task_id"],
            "repo_slug": task["repo_slug"],
            "split": task["split"],
            "workspace": str(workspace),
            "base_commit": base_commit,
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
