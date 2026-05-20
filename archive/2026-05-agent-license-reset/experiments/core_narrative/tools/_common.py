#!/usr/bin/env python3
"""Shared helpers for the core narrative experiment CLIs."""

from __future__ import annotations

import datetime as _dt
import ast
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


def parse_yaml_scalar(value: str) -> Any:
    if value in {"", "null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if value in {"[]", "{}", "''", '""'}:
        return [] if value == "[]" else {} if value == "{}" else ""
    if value[0:1] in {"'", '"'} and value[-1:] == value[0]:
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value[1:-1]
    if re.fullmatch(r"[-+]?\d+", value):
        return int(value)
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\.\d+)", value):
        return float(value)
    return value


def significant_yaml_line(lines: list[str], index: int) -> tuple[int, str] | None:
    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if stripped and not stripped.startswith("#"):
            return len(raw) - len(raw.lstrip(" ")), raw.lstrip(" ").rstrip()
        index += 1
    return None


def split_yaml_key_value(content: str) -> tuple[str, str]:
    if ":" not in content:
        raise ToolError("failed to parse YAML manifest line", line=content)
    key, value = content.split(":", 1)
    key = key.strip()
    if not key:
        raise ToolError("failed to parse YAML manifest line", line=content)
    return key, value.strip()


def collect_yaml_block_scalar(lines: list[str], index: int, parent_indent: int, style: str) -> tuple[str, int]:
    block_lines: list[str] = []
    while index < len(lines):
        raw = lines[index].rstrip()
        stripped = raw.strip()
        if stripped and not stripped.startswith("#"):
            indent = len(raw) - len(raw.lstrip(" "))
            if indent <= parent_indent:
                break
        block_indent = parent_indent + 2
        block_lines.append(raw[block_indent:] if len(raw) >= block_indent else "")
        index += 1
    if style.startswith("|"):
        return "\n".join(block_lines), index
    paragraphs: list[str] = []
    current: list[str] = []
    for line in block_lines:
        if line.strip():
            current.append(line.strip())
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    return "\n".join(paragraphs), index


def parse_yaml_value(lines: list[str], index: int, indent: int, value: str) -> tuple[Any, int]:
    if value in {">", ">-", "|", "|-"}:
        return collect_yaml_block_scalar(lines, index, indent, value)
    if value:
        scalar = parse_yaml_scalar(value)
        if isinstance(scalar, str):
            continuation: list[str] = [scalar]
            while index < len(lines):
                raw = lines[index]
                stripped = raw.strip()
                if not stripped or stripped.startswith("#"):
                    break
                line_indent = len(raw) - len(raw.lstrip(" "))
                content = raw.lstrip(" ").rstrip()
                if line_indent <= indent or content.startswith("- ") or ":" in content:
                    break
                continuation.append(content.strip())
                index += 1
            scalar = " ".join(continuation)
        return scalar, index
    next_line = significant_yaml_line(lines, index)
    if next_line is None or next_line[0] < indent:
        return {}, index
    if next_line[0] == indent and not next_line[1].startswith("- "):
        return {}, index
    return parse_yaml_block(lines, index, next_line[0])


def parse_yaml_list(lines: list[str], index: int, indent: int) -> tuple[list[Any], int]:
    values: list[Any] = []
    while index < len(lines):
        next_line = significant_yaml_line(lines, index)
        if next_line is None:
            return values, len(lines)
        line_indent, content = next_line
        if line_indent < indent or not content.startswith("- "):
            return values, index
        if line_indent > indent:
            raise ToolError("unexpected YAML indentation", line=content)
        index += 1
        item = content[2:].strip()
        if not item:
            next_item_line = significant_yaml_line(lines, index)
            if next_item_line is None or next_item_line[0] <= indent:
                values.append(None)
            else:
                parsed, index = parse_yaml_block(lines, index, next_item_line[0])
                values.append(parsed)
        elif ":" in item and not item.startswith(("http://", "https://")):
            key, raw_value = split_yaml_key_value(item)
            parsed_value, index = parse_yaml_value(lines, index, line_indent, raw_value)
            item_data: dict[str, Any] = {key: parsed_value}
            next_item_line = significant_yaml_line(lines, index)
            if next_item_line is not None and next_item_line[0] > indent:
                nested, index = parse_yaml_block(lines, index, next_item_line[0])
                if not isinstance(nested, dict):
                    raise ToolError("YAML list item continuation must be an object", line=item)
                item_data.update(nested)
            values.append(item_data)
        else:
            scalar = parse_yaml_scalar(item)
            if isinstance(scalar, str):
                continuation: list[str] = [scalar]
                while index < len(lines):
                    raw = lines[index]
                    stripped = raw.strip()
                    if not stripped or stripped.startswith("#"):
                        break
                    continuation_indent = len(raw) - len(raw.lstrip(" "))
                    content = raw.lstrip(" ").rstrip()
                    if continuation_indent <= line_indent or content.startswith("- ") or ":" in content:
                        break
                    continuation.append(content.strip())
                    index += 1
                scalar = " ".join(continuation)
            values.append(scalar)
    return values, index


def parse_yaml_dict(lines: list[str], index: int, indent: int) -> tuple[dict[str, Any], int]:
    values: dict[str, Any] = {}
    while index < len(lines):
        next_line = significant_yaml_line(lines, index)
        if next_line is None:
            return values, len(lines)
        line_indent, content = next_line
        if line_indent < indent or content.startswith("- "):
            return values, index
        if line_indent > indent:
            raise ToolError("unexpected YAML indentation", line=content)
        key, raw_value = split_yaml_key_value(content)
        index += 1
        values[key], index = parse_yaml_value(lines, index, indent, raw_value)
    return values, index


def parse_yaml_block(lines: list[str], index: int, indent: int) -> tuple[Any, int]:
    next_line = significant_yaml_line(lines, index)
    if next_line is None:
        return {}, len(lines)
    if next_line[0] < indent:
        return {}, index
    if next_line[0] != indent:
        raise ToolError("unexpected YAML indentation", line=next_line[1])
    if next_line[1].startswith("- "):
        return parse_yaml_list(lines, index, indent)
    return parse_yaml_dict(lines, index, indent)


def load_yaml_manifest(text: str) -> Any:
    lines = text.splitlines()
    first = significant_yaml_line(lines, 0)
    if first is None:
        return {}
    data, next_index = parse_yaml_block(lines, 0, first[0])
    trailing = significant_yaml_line(lines, next_index)
    if trailing is not None:
        raise ToolError("failed to parse complete YAML manifest", line=trailing[1])
    return data


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
            except ImportError:
                data = load_yaml_manifest(text)
            else:
                data = yaml.safe_load(text)
        else:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                try:
                    import yaml  # type: ignore[import-not-found]
                except ImportError:
                    data = load_yaml_manifest(text)
                else:
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
