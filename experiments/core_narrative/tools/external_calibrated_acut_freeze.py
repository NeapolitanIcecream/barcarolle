#!/usr/bin/env python3
"""Freeze external-calibrated Codex CLI ACUT profiles and run matrices."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import external_calibrated_repository_admission as repo_admission
from _common import ToolError, emit_json, fail, iso_now, load_manifest, write_json


TOOL = "external_calibrated_acut_freeze"
SCHEMA_VERSION = "external-calibrated-repo-benchmark.acut-freeze.v1"
PROFILE_SCHEMA_VERSION = "core-narrative.acut.v1"
MATRIX_SCHEMA_VERSION = "external-calibrated-repo-benchmark.acut-execution-matrix.v1"
PROTOCOL_ID = repo_admission.PROTOCOL_ID
REPO_ROOT = repo_admission.REPO_ROOT
CONFIG_ROOT = REPO_ROOT / "experiments/core_narrative/configs"
RESULTS_ROOT = repo_admission.RESULTS_ROOT
REPORTS_ROOT = repo_admission.REPORTS_ROOT

DEFAULT_PROTOCOL = CONFIG_ROOT / "external_calibrated_benchmark_20260515.yaml"
DEFAULT_E_CONFIG = CONFIG_ROOT / "external/swebench_sympy_e_v1.yaml"
DEFAULT_B_PRIMARY = CONFIG_ROOT / "tasks/sympy_barcarolle_b_v2.yaml"
DEFAULT_PROFILE_DIR = CONFIG_ROOT / "acuts/external_calibrated_sympy"
DEFAULT_MATRIX = CONFIG_ROOT / "external/sympy_external_acut_execution_matrix_v1.yaml"
DEFAULT_OUTPUT = RESULTS_ROOT / "acut_profiles/external_calibrated_acut_freeze_20260516.json"
DEFAULT_REPORT = REPORTS_ROOT / "external_acut_freeze_report.md"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", default=str(DEFAULT_PROTOCOL))
    parser.add_argument("--e-config", default=str(DEFAULT_E_CONFIG))
    parser.add_argument("--b-primary", default=str(DEFAULT_B_PRIMARY))
    parser.add_argument("--profile-dir", default=str(DEFAULT_PROFILE_DIR))
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    return parser.parse_args(list(argv) if argv is not None else None)


def repo_relative(path: Path) -> str:
    return repo_admission.repo_relative(path)


def run_command(command: Sequence[str], *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout, check=False)


def codex_cli_version() -> str | None:
    completed = run_command(["codex", "--version"])
    return completed.stdout.strip() if completed.returncode == 0 else None


def bundled_model_slugs() -> set[str]:
    completed = run_command(["codex", "debug", "models", "--bundled"], timeout=60)
    if completed.returncode != 0:
        return set()
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return set()
    models = payload.get("models") if isinstance(payload, Mapping) else None
    if not isinstance(models, list):
        return set()
    return {str(item.get("slug")) for item in models if isinstance(item, Mapping) and item.get("slug")}


def agent_profile_text(profile: str) -> str:
    if profile == "rich":
        return "\n".join(
            [
                "You are working in SymPy as a repository-level coding agent.",
                "Prefer local evidence: inspect the failing behavior, adjacent tests, relevant symbolic domains, and minimal implementation paths.",
                "Preserve public APIs and mathematical semantics. Add or adjust targeted tests when the task statement implies a regression.",
                "Do not use hidden verifier files, reference patches, SWE-bench gold material, ACUT outputs, or network resources.",
                "",
            ]
        )
    return "\n".join(
        [
            "You are a concise software-engineering agent.",
            "Use the public task statement and local repository evidence only.",
            "Make the smallest correct patch and verify it with targeted tests.",
            "Do not use hidden verifier files, reference patches, SWE-bench gold material, ACUT outputs, or network resources.",
            "",
        ]
    )


def acut_specs() -> list[dict[str, str]]:
    return [
        {
            "slot": "A0",
            "acut_id": "external-sympy-a0-gpt54-medium-concise",
            "display_name": "A0 Codex GPT-5.4 Medium Concise",
            "model": "gpt-5.4",
            "reasoning_effort": "medium",
            "agents_md_profile": "concise",
            "model_tier": "frontier",
            "purpose": "Default realistic Codex CLI baseline.",
        },
        {
            "slot": "A1",
            "acut_id": "external-sympy-a1-gpt54-low-concise",
            "display_name": "A1 Codex GPT-5.4 Low Concise",
            "model": "gpt-5.4",
            "reasoning_effort": "low",
            "agents_md_profile": "concise",
            "model_tier": "frontier",
            "purpose": "Low reasoning-effort contrast.",
        },
        {
            "slot": "A2",
            "acut_id": "external-sympy-a2-gpt54-high-concise",
            "display_name": "A2 Codex GPT-5.4 High Concise",
            "model": "gpt-5.4",
            "reasoning_effort": "high",
            "agents_md_profile": "concise",
            "model_tier": "frontier",
            "purpose": "High reasoning-effort contrast.",
        },
        {
            "slot": "A3",
            "acut_id": "external-sympy-a3-gpt55-high-concise",
            "display_name": "A3 Codex GPT-5.5 High Concise",
            "model": "gpt-5.5",
            "reasoning_effort": "high",
            "agents_md_profile": "concise",
            "model_tier": "strongest_available",
            "purpose": "Strong-model upper-bound contrast.",
        },
        {
            "slot": "A4",
            "acut_id": "external-sympy-a4-gpt54mini-high-concise",
            "display_name": "A4 Codex GPT-5.4 Mini High Concise",
            "model": "gpt-5.4-mini",
            "reasoning_effort": "high",
            "agents_md_profile": "concise",
            "model_tier": "cheap",
            "purpose": "Low-cost model contrast.",
        },
        {
            "slot": "A5",
            "acut_id": "external-sympy-a5-gpt54-high-rich-agents",
            "display_name": "A5 Codex GPT-5.4 High Rich AGENTS",
            "model": "gpt-5.4",
            "reasoning_effort": "high",
            "agents_md_profile": "rich",
            "model_tier": "frontier",
            "purpose": "Task-agnostic SymPy AGENTS.md guidance contrast.",
        },
    ]


def profile_path(profile_dir: Path, acut_id: str) -> Path:
    return profile_dir / f"{acut_id}.yaml"


def agents_path(profile_dir: Path, profile: str) -> Path:
    return profile_dir / "agents" / f"{profile}.md"


def build_profile(
    spec: Mapping[str, str],
    *,
    frozen_at: str,
    codex_version: str | None,
    model_available: bool,
    profile_dir: Path,
) -> dict[str, Any]:
    agents_text = agent_profile_text(spec["agents_md_profile"])
    agents_digest = repo_admission.sha256_text(agents_text)
    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "manifest_version": "external-calibrated-sympy-v1",
        "acut_id": spec["acut_id"],
        "display_name": spec["display_name"],
        "purpose": spec["purpose"],
        "frozen": True,
        "provider": "openai",
        "model": spec["model"],
        "model_parameters": {
            "reasoning_effort": spec["reasoning_effort"],
            "model_verbosity": "low",
            "reasoning_summary": "auto",
        },
        "prompt_policy_digest": f"sha256:{repo_admission.sha256_text(spec['acut_id'] + ':' + agents_digest)}",
        "prompt_policy_reference": repo_relative(agents_path(profile_dir, spec["agents_md_profile"])),
        "tool_permissions": {
            "filesystem": "workspace-write",
            "network": "disabled",
            "allowed_tools": ["filesystem:read", "filesystem:write", "shell", "code_edit", "git:status", "git:diff", "git:show"],
            "custom_localization_or_retrieval_tool_allowed": False,
        },
        "retrieval_context_strategy": {
            "strategy_id": "external-sympy-local-evidence-v1",
            "allowed_sources": ["public_task_statement", "local_filesystem", "targeted_tests", "bounded_symbol_search"],
            "forbidden_sources": [
                "SWE-bench gold patches",
                "SWE-bench test patches",
                "SWE-bench problem statements outside the task prompt",
                "B reference patches",
                "B hidden verifiers",
                "ACUT outputs",
                "network resources",
            ],
        },
        "runtime_budget": {
            "timeout_seconds": 3600,
            "max_turns": 18,
            "max_shell_commands": 55,
            "max_test_commands": 10,
            "retry_policy": {"primary_attempts": 1, "retries_allowed": False, "best_of_n": False},
        },
        "network_policy": {"mode": "disabled", "allowed_hosts": []},
        "execution_mode": "codex_cli_non_interactive_fresh_workspace",
        "adapter_or_harness_basis": "workspace_mode_runner.py + codex_cli_patch_command.py + apply_and_verify.py",
        "frozen_at": frozen_at,
        "operator": "codex-external-calibrated-coordinator",
        "notes": "Frozen for external-calibrated SymPy SWE-bench/B benchmark validation; no model calls made during profile freeze.",
        "metadata": {
            "slot": spec["slot"],
            "protocol_id": PROTOCOL_ID,
            "model_tier": spec["model_tier"],
            "agents_md_profile": spec["agents_md_profile"],
            "agents_md_digest": agents_digest,
            "codex_cli_version_observed": codex_version,
            "model_availability_checked_via": "codex debug models --bundled",
            "model_available_in_bundled_catalog": model_available,
            "primary_attempts_per_task": 1,
            "manual_steering_allowed": False,
            "network_access_allowed": False,
            "custom_tooling_as_primary_intervention": False,
        },
    }


def yaml_dump(path: Path, payload: Mapping[str, Any]) -> None:
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ToolError("PyYAML is required to write YAML artifacts") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(dict(payload), sort_keys=False, allow_unicode=False), encoding="utf-8")


def extract_e_tasks(e_config: Mapping[str, Any]) -> list[dict[str, Any]]:
    tasks = e_config.get("tasks") if isinstance(e_config.get("tasks"), list) else []
    return [
        {
            "task_id": str(task.get("instance_id")),
            "ordinal": int(task.get("ordinal", index)),
            "family": task.get("family_if_available"),
        }
        for index, task in enumerate(tasks, start=1)
        if isinstance(task, Mapping) and task.get("smoke_status") == "gold_resolved"
    ]


def extract_b_tasks(b_primary: Mapping[str, Any]) -> list[dict[str, Any]]:
    tasks = b_primary.get("tasks") if isinstance(b_primary.get("tasks"), list) else []
    return [
        {
            "task_id": str(task.get("task_id")),
            "ordinal": int(task.get("ordinal", index)),
            "family": task.get("family"),
            "difficulty": task.get("difficulty"),
        }
        for index, task in enumerate(tasks, start=1)
        if isinstance(task, Mapping)
    ]


def run_cells(acuts: Sequence[Mapping[str, Any]], tasks: Sequence[Mapping[str, Any]], *, phase: str) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for acut in acuts:
        for task in tasks:
            run_id = f"external_calibrated_sympy_{phase}_{acut['slot'].lower()}_{task['ordinal']:03d}_attempt1"
            cells.append(
                {
                    "run_id": run_id,
                    "phase": phase,
                    "acut_slot": acut["slot"],
                    "acut_id": acut["acut_id"],
                    "task_id": task["task_id"],
                    "task_ordinal": task["ordinal"],
                    "attempt": 1,
                    "network_policy": "disabled",
                    "status": "not_started",
                }
            )
    return cells


def build_payload(
    protocol: Mapping[str, Any],
    e_config: Mapping[str, Any],
    b_primary: Mapping[str, Any],
    *,
    codex_version_override: str | None = None,
    available_models_override: set[str] | None = None,
) -> dict[str, Any]:
    frozen_at = iso_now()
    codex_version = codex_version_override if codex_version_override is not None else codex_cli_version()
    available_models = available_models_override if available_models_override is not None else bundled_model_slugs()
    specs = acut_specs()
    e_tasks = extract_e_tasks(e_config)
    b_tasks = extract_b_tasks(b_primary)
    profile_dir = DEFAULT_PROFILE_DIR
    profiles = [
        build_profile(
            spec,
            frozen_at=frozen_at,
            codex_version=codex_version,
            model_available=spec["model"] in available_models,
            profile_dir=profile_dir,
        )
        for spec in specs
    ]
    e_cells = run_cells(specs, e_tasks, phase="e")
    b_cells = run_cells(specs, b_tasks, phase="b")
    blockers: list[str] = []
    if protocol.get("status") not in {
        "phase1_e_and_b_primary_frozen_acut_profiles_pending",
        "phase2_e_acut_profiles_frozen_route_preflight_pending",
    }:
        blockers.append("protocol_not_ready_for_acut_profile_freeze")
    if len(e_tasks) < 30:
        blockers.append("e_task_count_below_minimum")
    if len(b_tasks) < 20:
        blockers.append("b_primary_task_count_below_minimum")
    missing_models = [spec["model"] for spec in specs if spec["model"] not in available_models]
    if missing_models:
        blockers.append("required_models_missing_from_bundled_catalog")
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "protocol_id": PROTOCOL_ID,
        "generated_at": frozen_at,
        "model_calls_made": 0,
        "status": "acut_profiles_frozen" if not blockers else "blocked",
        "blockers": blockers,
        "codex_cli_version": codex_version,
        "available_model_slugs": sorted(available_models),
        "acut_count": len(profiles),
        "profiles": profiles,
        "e_task_count": len(e_tasks),
        "b_primary_task_count": len(b_tasks),
        "phase2_e_cell_count": len(e_cells),
        "phase3_b_cell_count": len(b_cells),
        "phase2_e_cells": e_cells,
        "phase3_b_cells": b_cells,
        "execution_controls": {
            "primary_attempts_per_task": 1,
            "best_of_n": False,
            "manual_steering": False,
            "network_access": "disabled",
            "run_b_before_e_spread_gate": False,
        },
        "next_required_steps": [
            "Run a live Codex route/preflight check without consuming benchmark tasks.",
            "Run Phase 2 E attempts only after the preflight passes.",
        ],
    }


def write_profiles_and_agents(payload: Mapping[str, Any], profile_dir: Path) -> list[str]:
    written: list[str] = []
    for profile_name in ("concise", "rich"):
        path = agents_path(profile_dir, profile_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(agent_profile_text(profile_name), encoding="utf-8")
        written.append(repo_relative(path))
    for profile in payload.get("profiles", []):
        if not isinstance(profile, Mapping):
            continue
        path = profile_path(profile_dir, str(profile.get("acut_id")))
        yaml_dump(path, profile)
        written.append(repo_relative(path))
    return written


def render_matrix(payload: Mapping[str, Any], profile_dir: Path) -> dict[str, Any]:
    return {
        "schema_version": MATRIX_SCHEMA_VERSION,
        "protocol_id": payload.get("protocol_id"),
        "status": payload.get("status"),
        "generated_at": payload.get("generated_at"),
        "profile_dir": repo_relative(profile_dir),
        "acut_ids": [profile.get("acut_id") for profile in payload.get("profiles", []) if isinstance(profile, Mapping)],
        "phase2_e_cell_count": payload.get("phase2_e_cell_count"),
        "phase3_b_cell_count": payload.get("phase3_b_cell_count"),
        "execution_controls": payload.get("execution_controls"),
        "phase2_e_cells": payload.get("phase2_e_cells"),
        "phase3_b_cells": payload.get("phase3_b_cells"),
    }


def render_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# External ACUT Freeze",
        "",
        f"Protocol: `{payload.get('protocol_id')}`",
        f"Status: `{payload.get('status')}`",
        f"Generated at: `{payload.get('generated_at')}`",
        f"Model calls made: `{payload.get('model_calls_made')}`",
        "",
        "## Matrix",
        "",
        f"- ACUTs: `{payload.get('acut_count')}`",
        f"- E tasks / cells: `{payload.get('e_task_count')}` / `{payload.get('phase2_e_cell_count')}`",
        f"- B primary tasks / cells: `{payload.get('b_primary_task_count')}` / `{payload.get('phase3_b_cell_count')}`",
        f"- Blockers: `{payload.get('blockers')}`",
        "",
        "## ACUTs",
        "",
    ]
    for profile in payload.get("profiles", []):
        if not isinstance(profile, Mapping):
            continue
        params = profile.get("model_parameters") if isinstance(profile.get("model_parameters"), Mapping) else {}
        metadata = profile.get("metadata") if isinstance(profile.get("metadata"), Mapping) else {}
        lines.append(
            f"- `{metadata.get('slot')}` `{profile.get('acut_id')}`: model `{profile.get('model')}`, "
            f"reasoning `{params.get('reasoning_effort')}`, AGENTS `{metadata.get('agents_md_profile')}`"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This freezes ACUT profiles and not-started run cells only. It does not execute model attempts.",
            "",
        ]
    )
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    protocol = load_manifest(args.protocol)
    e_config = load_manifest(args.e_config)
    b_primary = load_manifest(args.b_primary)
    payload = build_payload(protocol, e_config, b_primary)
    profile_dir = Path(args.profile_dir)
    written_paths = write_profiles_and_agents(payload, profile_dir)
    matrix_path = Path(args.matrix)
    yaml_dump(matrix_path, render_matrix(payload, profile_dir))
    payload["profile_paths"] = written_paths
    payload["matrix_path"] = repo_relative(matrix_path)
    output = Path(args.output)
    report = Path(args.report)
    write_json(output, payload)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(payload), encoding="utf-8")
    emit_json({**payload, "output_path": repo_relative(output), "report_path": repo_relative(report)})
    return 0 if payload.get("status") == "acut_profiles_frozen" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
