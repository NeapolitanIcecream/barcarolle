#!/usr/bin/env python3
"""Shared helpers for the core narrative experiment CLIs."""

from __future__ import annotations

import datetime as _dt
import json
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable


class ToolError(Exception):
    """Expected CLI failure with structured error details."""

    def __init__(self, message: str, *, exit_code: int = 2, **details: Any) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.details = details


def iso_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z")


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip())
    return cleaned.strip("-") or "unnamed"


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise ToolError("manifest does not exist", path=str(manifest_path))

    text = manifest_path.read_text(encoding="utf-8")
    suffix = manifest_path.suffix.lower()
    try:
        if suffix == ".json":
            data = json.loads(text)
        elif suffix in {".yaml", ".yml"}:
            try:
                import yaml  # type: ignore[import-not-found]
            except ImportError as exc:
                raise ToolError(
                    "YAML manifests require PyYAML; install it or use JSON",
                    path=str(manifest_path),
                ) from exc
            data = yaml.safe_load(text)
        else:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                try:
                    import yaml  # type: ignore[import-not-found]
                except ImportError as exc:
                    raise ToolError(
                        "unknown manifest suffix and PyYAML is unavailable",
                        path=str(manifest_path),
                    ) from exc
                data = yaml.safe_load(text)
    except ToolError:
        raise
    except Exception as exc:
        raise ToolError(
            "failed to parse manifest",
            path=str(manifest_path),
            cause=str(exc),
        ) from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ToolError("manifest root must be an object", path=str(manifest_path))
    return data


def require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ToolError(f"{name} must be an object")
    return value


def require_keys(mapping: dict[str, Any], keys: Iterable[str], context: str) -> None:
    missing = [key for key in keys if key not in mapping]
    if missing:
        raise ToolError(
            f"{context} is missing required fields",
            missing=missing,
        )


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def emit_json(payload: dict[str, Any], output_path: str | Path | None = None) -> None:
    if output_path is not None:
        write_json(output_path, payload)
        payload = {**payload, "output_path": str(output_path)}
    print(json.dumps(payload, indent=2, sort_keys=True))


def command_from_args(command: list[str]) -> list[str]:
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise ToolError("command is required after --")
    return command


def split_command(command: str) -> list[str]:
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        raise ToolError("failed to parse command", command=command, cause=str(exc)) from exc
    if not parts:
        raise ToolError("command is empty")
    return parts


def run_to_artifacts(
    command: list[str],
    *,
    cwd: Path,
    timeout_seconds: int | None,
    stdout_path: Path,
    stderr_path: Path,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    try:
        with stdout_path.open("w", encoding="utf-8") as stdout_file:
            with stderr_path.open("w", encoding="utf-8") as stderr_file:
                completed = subprocess.run(
                    command,
                    cwd=str(cwd),
                    env=env,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
        return {
            "exit_code": completed.returncode,
            "timed_out": False,
            "duration_seconds": round(time.monotonic() - started, 3),
        }
    except FileNotFoundError as exc:
        raise ToolError(
            "command executable was not found",
            executable=command[0],
        ) from exc
    except subprocess.TimeoutExpired:
        return {
            "exit_code": None,
            "timed_out": True,
            "duration_seconds": round(time.monotonic() - started, 3),
        }


def run_capture(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=str(cwd) if cwd is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ToolError("command executable was not found", executable=command[0]) from exc


def git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return run_capture(["git", *args], cwd=cwd)


def fail(tool: str, exc: BaseException) -> int:
    if isinstance(exc, ToolError):
        payload: dict[str, Any] = {
            "tool": tool,
            "status": "error",
            "error": str(exc),
            "details": exc.details,
        }
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        return exc.exit_code

    payload = {
        "tool": tool,
        "status": "error",
        "error": str(exc),
        "details": {"exception_type": type(exc).__name__},
    }
    print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
    return 1
