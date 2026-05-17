#!/usr/bin/env python3
"""Run non-benchmark Codex route preflights for frozen external ACUT profiles."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import external_calibrated_repository_admission as repo_admission
from _common import ToolError, emit_json, fail, iso_now, load_manifest, slug, write_json


TOOL = "external_calibrated_route_preflight"
SCHEMA_VERSION = "external-calibrated-repo-benchmark.route-preflight.v1"
PROTOCOL_ID = repo_admission.PROTOCOL_ID
REPO_ROOT = repo_admission.REPO_ROOT
RESULTS_ROOT = repo_admission.RESULTS_ROOT
REPORTS_ROOT = repo_admission.REPORTS_ROOT
DEFAULT_ACUT_FREEZE = RESULTS_ROOT / "acut_profiles/external_calibrated_acut_freeze_20260516.json"
DEFAULT_OUTPUT = RESULTS_ROOT / "acut_profiles/external_calibrated_codex_route_preflight_20260516.json"
DEFAULT_REPORT = REPORTS_ROOT / "external_codex_route_preflight_report.md"
DEFAULT_PRIVATE_ROOT = REPO_ROOT / "experiments/core_narrative/large_artifacts/external_calibrated_route_preflight_20260516"
DEFAULT_WORKSPACE_ROOT = REPO_ROOT / "experiments/core_narrative/workspaces/external_calibrated_route_preflight_20260516"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acut-freeze", default=str(DEFAULT_ACUT_FREEZE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT))
    parser.add_argument("--workspace-root", default=str(DEFAULT_WORKSPACE_ROOT))
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--mode", choices=("dry-run", "live"), default="dry-run")
    parser.add_argument("--timeout-seconds", type=int, default=120)
    return parser.parse_args(list(argv) if argv is not None else None)


def repo_relative(path: Path) -> str:
    return repo_admission.repo_relative(path)


def toml_string(value: str) -> str:
    return json.dumps(value)


def route_specs_from_profiles(acut_freeze: Mapping[str, Any]) -> list[dict[str, str]]:
    profiles = acut_freeze.get("profiles") if isinstance(acut_freeze.get("profiles"), list) else []
    specs: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for profile in profiles:
        if not isinstance(profile, Mapping):
            continue
        params = profile.get("model_parameters") if isinstance(profile.get("model_parameters"), Mapping) else {}
        metadata = profile.get("metadata") if isinstance(profile.get("metadata"), Mapping) else {}
        model = str(profile.get("model", ""))
        effort = str(params.get("reasoning_effort", ""))
        verbosity = str(params.get("model_verbosity", "low"))
        key = (model, effort, verbosity)
        if not model or not effort or key in seen:
            continue
        seen.add(key)
        specs.append(
            {
                "route_id": f"{model}-{effort}-{verbosity}",
                "model": model,
                "reasoning_effort": effort,
                "model_verbosity": verbosity,
                "example_acut_id": str(profile.get("acut_id")),
                "example_slot": str(metadata.get("slot")),
            }
        )
    return specs


def build_codex_command(
    *,
    codex_bin: str,
    workspace: Path,
    model: str,
    reasoning_effort: str,
    model_verbosity: str,
    output_last_message: Path,
) -> list[str]:
    return [
        codex_bin,
        "-a",
        "never",
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--cd",
        str(workspace),
        "--model",
        model,
        "-c",
        f"model_reasoning_effort={toml_string(reasoning_effort)}",
        "-c",
        f"model_verbosity={toml_string(model_verbosity)}",
        "-o",
        str(output_last_message),
        "Return exactly ROUTE_OK for this non-benchmark route preflight. Do not inspect files or run shell commands.",
    ]


def run_route(spec: Mapping[str, str], *, args: argparse.Namespace) -> dict[str, Any]:
    route_slug = slug(str(spec["route_id"]))
    workspace = Path(args.workspace_root) / route_slug
    private_dir = Path(args.private_root) / route_slug
    workspace.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)
    output_last_message = private_dir / "last_message.txt"
    stdout_path = private_dir / "stdout.jsonl"
    stderr_path = private_dir / "stderr.txt"
    command = build_codex_command(
        codex_bin=args.codex_bin,
        workspace=workspace,
        model=str(spec["model"]),
        reasoning_effort=str(spec["reasoning_effort"]),
        model_verbosity=str(spec["model_verbosity"]),
        output_last_message=output_last_message,
    )
    if args.mode == "dry-run":
        return {
            **dict(spec),
            "status": "dry_run_ready",
            "model_call_made": False,
            "command": command,
            "workspace": repo_relative(workspace),
            "private_artifact_dir": repo_relative(private_dir),
        }
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=int(args.timeout_seconds),
            check=False,
        )
        timed_out = False
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    last_message = output_last_message.read_text(encoding="utf-8") if output_last_message.exists() else ""
    pass_flag = exit_code == 0 and "ROUTE_OK" in last_message
    return {
        **dict(spec),
        "status": "passed" if pass_flag else "failed",
        "model_call_made": True,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_seconds": round(time.monotonic() - started, 3),
        "last_message_digest": repo_admission.sha256_text(last_message),
        "stdout_digest": repo_admission.sha256_text(stdout),
        "stderr_digest": repo_admission.sha256_text(stderr),
        "last_message_contains_route_ok": "ROUTE_OK" in last_message,
        "workspace": repo_relative(workspace),
        "private_artifact_dir": repo_relative(private_dir),
    }


def build_payload(acut_freeze: Mapping[str, Any], route_results: Sequence[Mapping[str, Any]], *, mode: str) -> dict[str, Any]:
    blockers: list[str] = []
    if acut_freeze.get("status") != "acut_profiles_frozen":
        blockers.append("acut_profiles_not_frozen")
    if not route_results:
        blockers.append("no_route_specs")
    failed = [result for result in route_results if result.get("status") not in {"passed", "dry_run_ready"}]
    if failed:
        blockers.append("route_preflight_failed")
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "protocol_id": PROTOCOL_ID,
        "generated_at": iso_now(),
        "mode": mode,
        "model_calls_made": sum(1 for result in route_results if result.get("model_call_made") is True),
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "route_count": len(route_results),
        "routes": list(route_results),
        "next_required_steps": [
            "Run Phase 2 E attempts on the frozen matrix." if mode == "live" else "Run this preflight in live mode before Phase 2 E attempts."
        ],
    }


def render_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# External Codex Route Preflight",
        "",
        f"Protocol: `{payload.get('protocol_id')}`",
        f"Status: `{payload.get('status')}`",
        f"Mode: `{payload.get('mode')}`",
        f"Generated at: `{payload.get('generated_at')}`",
        f"Model calls made: `{payload.get('model_calls_made')}`",
        f"Blockers: `{payload.get('blockers')}`",
        "",
        "## Routes",
        "",
    ]
    for route in payload.get("routes", []):
        if not isinstance(route, Mapping):
            continue
        lines.append(
            f"- `{route.get('route_id')}` from `{route.get('example_slot')}`: `{route.get('status')}`"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This preflight uses synthetic non-benchmark prompts only. It does not run E or B tasks.",
            "",
        ]
    )
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    acut_freeze = load_manifest(args.acut_freeze)
    specs = route_specs_from_profiles(acut_freeze)
    route_results = [run_route(spec, args=args) for spec in specs]
    payload = build_payload(acut_freeze, route_results, mode=args.mode)
    output = Path(args.output)
    report = Path(args.report)
    write_json(output, payload)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(payload), encoding="utf-8")
    emit_json({**payload, "output_path": repo_relative(output), "report_path": repo_relative(report)})
    return 0 if payload.get("status") == "passed" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
