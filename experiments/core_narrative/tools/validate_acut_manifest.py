#!/usr/bin/env python3
"""Dependency-light validation for core narrative ACUT manifests."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from typing import Any

from _common import ToolError, emit_json, fail, load_manifest


TOOL = "validate_acut_manifest"
ACUT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
ALLOWED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "manifest_version",
    "acut_id",
    "display_name",
    "purpose",
    "frozen",
    "provider",
    "model",
    "model_parameters",
    "prompt_policy_digest",
    "prompt_policy_reference",
    "tool_permissions",
    "retrieval_context_strategy",
    "runtime_budget",
    "network_policy",
    "execution_mode",
    "adapter_or_harness_basis",
    "frozen_at",
    "operator",
    "score_fields",
    "notes",
    "metadata",
}
REQUIRED_STRING_FIELDS = [
    "acut_id",
    "provider",
    "model",
    "prompt_policy_digest",
    "frozen_at",
    "operator",
]
OPTIONAL_OBJECT_FIELDS = [
    "model_parameters",
    "tool_permissions",
    "retrieval_context_strategy",
    "runtime_budget",
    "network_policy",
    "execution_mode",
    "adapter_or_harness_basis",
    "score_fields",
    "metadata",
]
OPTIONAL_STRING_FIELDS = [
    "manifest_version",
    "display_name",
    "purpose",
    "prompt_policy_reference",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate ACUT manifests against the dependency-light canonical "
            "contract used by the core narrative experiment."
        )
    )
    parser.add_argument("paths", nargs="*", help="ACUT manifest files or directories to scan recursively.")
    parser.add_argument("--self-check", action="store_true", help="Validate a built-in canonical ACUT fixture.")
    parser.add_argument("--output", help="Optional path for the structured JSON validation summary.")
    return parser.parse_args()


def iter_manifest_paths(paths: list[str]) -> list[Path]:
    manifest_paths: list[Path] = []
    suffixes = {".json", ".yaml", ".yml"}
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            manifest_paths.extend(
                sorted(
                    candidate
                    for candidate in path.rglob("*")
                    if candidate.is_file() and candidate.suffix.lower() in suffixes
                )
            )
        elif path.is_file():
            manifest_paths.append(path)
        else:
            raise ToolError("manifest path does not exist", path=str(path))
    return manifest_paths


def expect_non_empty_string(data: dict[str, Any], field: str, errors: list[str]) -> None:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty string")


def validate_date_time(value: Any, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        return
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append("frozen_at must be an ISO-8601 date-time string")
        return
    if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
        errors.append("frozen_at must include a timezone offset")


def validate_data(data: dict[str, Any], path_label: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    unknown_fields = sorted(set(data) - ALLOWED_TOP_LEVEL_FIELDS)
    if unknown_fields:
        errors.append(f"unknown top-level fields: {', '.join(unknown_fields)}")

    schema_version = data.get("schema_version")
    if schema_version is not None and schema_version != "core-narrative.acut.v1":
        errors.append("schema_version must be core-narrative.acut.v1 when present")

    for field in REQUIRED_STRING_FIELDS:
        expect_non_empty_string(data, field, errors)

    acut_id = data.get("acut_id")
    if isinstance(acut_id, str) and not ACUT_ID_PATTERN.fullmatch(acut_id):
        errors.append("acut_id must match ^[a-z0-9][a-z0-9_-]*$")

    validate_date_time(data.get("frozen_at"), errors)

    frozen = data.get("frozen")
    if frozen is not None and not isinstance(frozen, bool):
        errors.append("frozen must be a boolean when present")

    for field in OPTIONAL_OBJECT_FIELDS:
        value = data.get(field)
        if value is not None and not isinstance(value, dict):
            errors.append(f"{field} must be an object when present")

    for field in OPTIONAL_STRING_FIELDS:
        value = data.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field} must be a string when present")

    if data.get("prompt_policy_reference") == "":
        warnings.append("prompt_policy_reference is present but empty")

    return {
        "path": path_label,
        "acut_id": data.get("acut_id"),
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def validate_manifest(path: Path) -> dict[str, Any]:
    return validate_data(load_manifest(path), str(path))


def validate_self_check_fixture() -> dict[str, Any]:
    fixture = {
        "schema_version": "core-narrative.acut.v1",
        "acut_id": "fixture-acut",
        "provider": "openai",
        "model": "gpt-5.5",
        "prompt_policy_digest": "sha256:fixture",
        "frozen_at": "2026-04-28T00:00:00Z",
        "operator": "schema-toolsmith",
        "model_parameters": {"reasoning_effort": "medium"},
        "tool_permissions": {"filesystem": "workspace-write"},
        "retrieval_context_strategy": {"strategy_id": "fixture"},
        "runtime_budget": {"wall_clock_minutes": 30},
        "network_policy": {"default": "denied"},
        "execution_mode": {"type": "non_interactive_codex_cli"},
        "adapter_or_harness_basis": {"adapter_id": "fixture"},
        "metadata": {},
    }
    return validate_data(fixture, "<self-check:canonical-acut>")


def main() -> int:
    args = parse_args()
    try:
        manifest_paths = iter_manifest_paths(args.paths) if args.paths else []
        if not manifest_paths and not args.self_check:
            raise ToolError("no ACUT manifests found")

        results = [validate_manifest(path) for path in manifest_paths]
        if args.self_check:
            results.append(validate_self_check_fixture())
        invalid = [result for result in results if not result["valid"]]
        payload = {
            "tool": TOOL,
            "status": "failed" if invalid else "passed",
            "manifest_count": len(results),
            "valid_count": len(results) - len(invalid),
            "invalid_count": len(invalid),
            "results": results,
        }
        emit_json(payload, args.output)
        return 1 if invalid else 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
