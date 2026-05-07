#!/usr/bin/env python3
"""Materialize split-level Click task manifests into runner-ready task dirs."""

from __future__ import annotations

import argparse
import shutil
import shlex
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

from _common import ToolError, emit_json, load_manifest, require_keys


TOOL = "materialize_task_pack"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert reviewed split-level task manifests into per-task task.yaml, "
            "public statement, and verifier wrapper directories."
        )
    )
    parser.add_argument("--split-manifest", action="append", required=True, help="Reviewed split YAML path.")
    parser.add_argument(
        "--output-root",
        default="experiments/core_narrative/tasks",
        help="Root directory for materialized task packs.",
    )
    parser.add_argument(
        "--source-repo",
        help="Optional target repository checkout used to package hidden verifier test files from target commits.",
    )
    parser.add_argument("--force", action="store_true", help="Replace existing task directories.")
    parser.add_argument("--output", help="Optional path for the structured JSON summary.")
    return parser.parse_args()


def fail(exc: BaseException) -> int:
    if isinstance(exc, ToolError):
        emit_json({"tool": TOOL, "status": "error", "error": str(exc), "details": exc.details})
        return exc.exit_code
    emit_json({"tool": TOOL, "status": "error", "error": str(exc), "details": {"exception_type": type(exc).__name__}})
    return 1


def require_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ToolError(f"{name} must be a list")
    return value


def safe_remove(path: Path, root: Path) -> None:
    if not path.exists():
        return
    resolved = path.resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ToolError("refusing to remove path outside output root", path=str(path), root=str(root)) from exc
    shutil.rmtree(path)


def yaml_dump(path: Path, payload: dict[str, Any]) -> None:
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ToolError("materializing YAML task packs requires PyYAML") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")


def statement_text(task: dict[str, Any]) -> str:
    expected_area = "\n".join(f"- {item}" for item in task.get("expected_touched_area", []))
    guidance = task.get("visible_context_guidance", "")
    source = task.get("source", {})
    source_url = source.get("public_url") or "not recorded"
    return (
        f"# {task['task_id']}\n\n"
        "## Problem Statement\n\n"
        f"{task.get('problem_statement', '').strip()}\n\n"
        "## Public Source\n\n"
        f"- Kind: {source.get('kind', 'unknown')}\n"
        f"- Anchor: {source.get('anchor_id', 'unknown')}\n"
        f"- URL: {source_url}\n\n"
        "## Visible Context Guidance\n\n"
        f"{str(guidance).strip()}\n\n"
        "## Expected Touched Area\n\n"
        f"{expected_area or '- Not recorded'}\n"
    )


def verifier_script(command: str) -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "# Run from the prepared task workspace. The coordinator keeps this script outside ACUT-visible inputs.\n"
        "script_dir=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"\n"
        "hidden_dir=\"$script_dir/hidden\"\n"
        "if [ -d \"$hidden_dir\" ]; then\n"
        "  while IFS= read -r -d '' file; do\n"
        "    rel=\"${file#$hidden_dir/}\"\n"
        "    mkdir -p \"$(dirname \"$rel\")\"\n"
        "    cp \"$file\" \"$rel\"\n"
        "  done < <(find \"$hidden_dir\" -type f -print0)\n"
        "fi\n"
        f"exec {command}\n"
    )


def verifier_source_paths(command: str) -> list[str]:
    paths: list[str] = []
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        raise ToolError("failed to parse verifier command", command=command, cause=str(exc)) from exc
    for part in parts:
        path = part.split("::", 1)[0]
        if path.endswith(".py") and "/" in path and path not in paths:
            paths.append(path)
    return paths


def git_show_file(source_repo: Path, commit: str, file_path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{commit}:{file_path}"],
        cwd=source_repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def write_hidden_verifier_files(task: dict[str, Any], verifier_dir: Path, command: str, source_repo: Path | None) -> list[str]:
    if source_repo is None:
        return []
    source = task.get("source")
    if not isinstance(source, dict):
        raise ToolError("task.source must be an object", task_id=task.get("task_id"))
    target_commit = source.get("target_commit")
    if not isinstance(target_commit, str) or not target_commit:
        raise ToolError("task.source.target_commit is required to package hidden verifier files", task_id=task.get("task_id"))

    hidden_files: list[str] = []
    for file_path in verifier_source_paths(command):
        content = git_show_file(source_repo, target_commit, file_path)
        if content is None:
            continue
        hidden_path = verifier_dir / "hidden" / file_path
        hidden_path.parent.mkdir(parents=True, exist_ok=True)
        hidden_path.write_text(content, encoding="utf-8")
        hidden_files.append(file_path)
    return hidden_files


def materialize_task(
    task: dict[str, Any],
    *,
    split_name: str,
    split_manifest: Path,
    output_root: Path,
    force: bool,
    source_repo: Path | None,
) -> dict[str, Any]:
    require_keys(
        task,
        [
            "task_id",
            "repo_slug",
            "split",
            "source",
            "task_family",
            "allowed_context",
            "disallowed_context",
            "verifier",
            "expected",
            "leakage",
            "admission",
        ],
        "task",
    )
    task_id = str(task["task_id"])
    repo_slug = str(task["repo_slug"])
    split = str(task["split"]).lower()
    if split != split_name.lower():
        raise ToolError("task split does not match split manifest", task_id=task_id, task_split=split, manifest_split=split_name)

    task_dir = output_root / repo_slug / split / task_id
    if task_dir.exists():
        if not force:
            raise ToolError("task directory already exists; pass --force to replace it", task_dir=str(task_dir))
        safe_remove(task_dir, output_root)

    public_dir = task_dir / "public"
    verifier_dir = task_dir / "verifier"
    public_dir.mkdir(parents=True, exist_ok=True)
    verifier_dir.mkdir(parents=True, exist_ok=True)

    statement_path = public_dir / "statement.md"
    statement_path.write_text(statement_text(task), encoding="utf-8")

    verifier = task["verifier"]
    if not isinstance(verifier, dict):
        raise ToolError("task.verifier must be an object", task_id=task_id)
    require_keys(verifier, ["command", "timeout_seconds"], "task.verifier")
    run_path = verifier_dir / "run.sh"
    verifier_command = str(verifier["command"])
    hidden_files = write_hidden_verifier_files(task, verifier_dir, verifier_command, source_repo)
    run_path.write_text(verifier_script(verifier_command), encoding="utf-8")
    run_path.chmod(run_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    task_yaml = {
        "schema_version": "core-narrative.task.v1",
        "task_id": task_id,
        "repo_slug": repo_slug,
        "split": split,
        "source": task["source"],
        "task_family": task["task_family"],
        "task_statement_path": "public/statement.md",
        "allowed_context": task["allowed_context"],
        "disallowed_context": task["disallowed_context"],
        "verifier": {
            "command": "verifier/run.sh",
            "timeout_seconds": verifier["timeout_seconds"],
        },
        "expected": task["expected"],
        "leakage": task["leakage"],
        "admission": task["admission"],
        "metadata": {
            "materialized_from": str(split_manifest),
            "benchmark_split": task.get("benchmark_split"),
            "locked_target_repository": task.get("locked_target_repository"),
            "locked_target_commit": task.get("locked_target_commit"),
            "source_compare": task.get("source_compare"),
            "expected_touched_area": task.get("expected_touched_area", []),
            "visible_context_guidance": task.get("visible_context_guidance"),
            "risk_notes": task.get("risk_notes"),
        },
    }
    yaml_dump(task_dir / "task.yaml", task_yaml)
    return {
        "task_id": task_id,
        "split": split,
        "task_dir": str(task_dir),
        "task_manifest": str(task_dir / "task.yaml"),
        "statement": str(statement_path),
        "verifier": str(run_path),
        "hidden_verifier_files": hidden_files,
    }


def main() -> int:
    args = parse_args()
    try:
        output_root = Path(args.output_root)
        source_repo = Path(args.source_repo) if args.source_repo else None
        if source_repo is not None and not (source_repo / ".git").exists():
            raise ToolError("--source-repo must point at a git checkout", source_repo=str(source_repo))
        materialized: list[dict[str, Any]] = []
        for raw_path in args.split_manifest:
            split_manifest = Path(raw_path)
            data = load_manifest(split_manifest)
            require_keys(data, ["split", "repo_slug", "tasks"], "split manifest")
            tasks = require_list(data["tasks"], "split manifest tasks")
            expected_count = data.get("task_count")
            if expected_count is not None and int(expected_count) != len(tasks):
                raise ToolError(
                    "split manifest task_count does not match task list",
                    split_manifest=str(split_manifest),
                    task_count=expected_count,
                    actual=len(tasks),
                )
            for task in tasks:
                if not isinstance(task, dict):
                    raise ToolError("task entry must be an object", split_manifest=str(split_manifest))
                materialized.append(
                    materialize_task(
                        task,
                        split_name=str(data["split"]),
                        split_manifest=split_manifest,
                        output_root=output_root,
                        force=args.force,
                        source_repo=source_repo,
                    )
                )

        payload = {
            "tool": TOOL,
            "status": "materialized",
            "output_root": str(output_root),
            "task_count": len(materialized),
            "by_split": {
                split: sum(1 for item in materialized if item["split"] == split)
                for split in sorted({str(item["split"]) for item in materialized})
            },
            "hidden_verifier_file_count": sum(len(item["hidden_verifier_files"]) for item in materialized),
            "tasks": materialized,
        }
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(exc)


if __name__ == "__main__":
    sys.exit(main())
