#!/usr/bin/env python3
"""No-model smoke for Click specialist context-pack prompt injection."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, fail, load_manifest


TOOL = "smoke_click_specialist_context_pack"
PACK_ID = "click_specialist_context_pack_v1"
PACK_MARKER = "CLICK_SPECIALIST_CONTEXT_PACK_V1"
PACK_HASH = "dfb271ad174531a7dd2f00da4cd0486193d87ce33349380982150889ecf84e48"
SECTION_IDS = [
    "repo_map",
    "docs_map",
    "symbol_index",
    "convention_playbook",
    "deterministic_retrieval_policy",
]
ACUTS = [
    ("frontier-generic-swe", False),
    ("frontier-click-specialist", True),
    ("cheap-generic-swe", False),
    ("cheap-click-specialist", True),
]
FORBIDDEN_ARTIFACT_PATTERNS = [
    ("full_url", re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.-]*://\S+")),
    ("ip_address", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("bearer_token", re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]+")),
    ("resolved_secret_assignment", re.compile(r"(?i)\b(api[_-]?key|token|secret)\s*[:=]\s*['\"][^'\"]+['\"]")),
    ("hidden_verifier_path", re.compile(r"verifier/hidden|hidden/tests")),
    ("pilot_output_path", re.compile(r"experiments/core_narrative/results/(raw|normalized)/pilot_")),
]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Experiment repository root.")
    parser.add_argument(
        "--raw-dir",
        default="experiments/core_narrative/results/raw/click_specialist_context_pack_smoke",
        help="Raw smoke artifact directory.",
    )
    parser.add_argument(
        "--normalized-output",
        default="experiments/core_narrative/results/normalized/click_specialist_context_pack_smoke.json",
        help="Normalized smoke summary JSON path.",
    )
    parser.add_argument("--codex-bin", default="codex", help="Codex CLI executable for dry-run catalog generation.")
    return parser.parse_args(list(argv))


def stable_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")


def run_command(command: Sequence[str], *, cwd: Path, env: Mapping[str, str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            cwd=str(cwd),
            env=dict(env),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ToolError("command executable was not found", executable=command[0]) from exc


def build_workspace(root: Path) -> Path:
    workspace = root / "workspace"
    workspace.mkdir(parents=True)
    completed = run_command(["git", "init"], cwd=workspace, env=os.environ)
    if completed.returncode != 0:
        raise ToolError("failed to initialize smoke workspace", stderr=completed.stderr.strip())
    package_dir = workspace / ".core_narrative"
    package_dir.mkdir()
    (package_dir / "statement.md").write_text(
        "No-model context-pack injection smoke. Do not generate or apply a patch.\n",
        encoding="utf-8",
    )
    task = {
        "task_id": "click_specialist_context_pack_smoke",
        "repo_slug": "pallets_click",
        "split": "smoke",
        "task_family": "no_model_context_injection",
        "source": {
            "kind": "synthetic_no_model_smoke",
            "anchor_id": "click-specialist-context-pack",
            "base_commit": "8bd8b4a074c55c03b6eb5666edc44a9c43df38a2",
        },
        "task_statement_path": ".core_narrative/statement.md",
        "allowed_context": {
            "include_git_history_before_base": False,
            "include_issue_text": False,
            "include_pr_text": False,
            "include_reference_patch": False,
        },
        "workspace_history": {
            "future_commits_available": False,
            "target_patch_available": False,
        },
    }
    write_json(package_dir / "task.json", task)
    return workspace


def acut_path(repo_root: Path, acut_id: str) -> Path:
    return repo_root / "experiments" / "core_narrative" / "configs" / "acuts" / f"{acut_id}.yaml"


def validate_manifest_side(repo_root: Path, acut_id: str, expected_injection: bool) -> dict[str, Any]:
    manifest = load_manifest(acut_path(repo_root, acut_id))
    metadata = manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {}
    specialist = metadata.get("specialist_context") if isinstance(metadata.get("specialist_context"), dict) else {}
    context_pack = specialist.get("context_pack")
    return {
        "acut_id": acut_id,
        "expected_injection": expected_injection,
        "manifest_allows_click_context": specialist.get("click_task_agnostic_context_allowed") is True,
        "manifest_declares_context_pack": isinstance(context_pack, dict),
        "manifest_pack_id": context_pack.get("pack_id") if isinstance(context_pack, dict) else None,
        "manifest_pack_hash": context_pack.get("pack_hash") if isinstance(context_pack, dict) else None,
    }


def validate_summary(summary: Mapping[str, Any], acut_id: str, expected_injection: bool) -> dict[str, Any]:
    context = summary.get("specialist_context_pack")
    if not isinstance(context, dict):
        raise ToolError("dry-run summary is missing specialist_context_pack", acut_id=acut_id)
    prompt = summary.get("prompt")
    if not isinstance(prompt, dict):
        raise ToolError("dry-run summary is missing prompt evidence", acut_id=acut_id)
    prompt_checks = context.get("prompt_checks") if isinstance(context.get("prompt_checks"), dict) else {}
    provider_override = summary.get("provider_override") if isinstance(summary.get("provider_override"), dict) else {}
    codex_exec = summary.get("codex_exec") if isinstance(summary.get("codex_exec"), dict) else {}

    failures: list[str] = []
    if summary.get("model_call_made") is not False:
        failures.append("model_call_made must be false")
    if codex_exec.get("executed") is not False:
        failures.append("codex exec must not execute in dry-run smoke")
    if prompt.get("content_recorded") is not False:
        failures.append("prompt content must not be recorded")
    if prompt.get("full_urls_redacted") is not True:
        failures.append("prompt full_urls_redacted must be true")
    if provider_override.get("endpoint_value_recorded") is not False:
        failures.append("endpoint value must not be recorded")
    if provider_override.get("credential_value_recorded") is not False:
        failures.append("credential value must not be recorded")

    if expected_injection:
        if context.get("enabled") is not True:
            failures.append("specialist context should be enabled")
        if context.get("pack_id") != PACK_ID:
            failures.append("pack id mismatch")
        if context.get("pack_hash") != PACK_HASH:
            failures.append("pack hash mismatch")
        if prompt_checks.get("marker_present") is not True:
            failures.append("pack marker missing from prompt")
        if prompt_checks.get("pack_hash_present") is not True:
            failures.append("pack hash missing from prompt")
        sections = prompt_checks.get("section_ids_present")
        if not isinstance(sections, dict):
            failures.append("section id evidence missing")
        else:
            for section_id in SECTION_IDS:
                if sections.get(section_id) is not True:
                    failures.append(f"section id missing from prompt: {section_id}")
        if prompt_checks.get("all_expected_sections_present") is not True:
            failures.append("not all expected sections are present")
    else:
        if context.get("enabled") is not False:
            failures.append("generic context should be disabled")
        if prompt_checks.get("marker_present") is not False:
            failures.append("generic prompt must not contain pack marker")
        if prompt_checks.get("pack_hash_present") is not False:
            failures.append("generic prompt must not contain pack hash")
        if context.get("section_ids"):
            failures.append("generic prompt must not report context section ids")

    return {
        "acut_id": acut_id,
        "expected_injection": expected_injection,
        "passed": not failures,
        "failures": failures,
        "summary_status": summary.get("status"),
        "model_call_made": summary.get("model_call_made"),
        "prompt_sha256": prompt.get("sha256"),
        "prompt_char_count": prompt.get("char_count"),
        "context_enabled": context.get("enabled"),
        "marker_present": prompt_checks.get("marker_present"),
        "pack_id": context.get("pack_id"),
        "pack_hash": context.get("pack_hash"),
        "pack_hash_present": prompt_checks.get("pack_hash_present"),
        "section_ids": context.get("section_ids", []),
        "section_ids_present": prompt_checks.get("section_ids_present", {}),
        "context_prompt_char_count": context.get("context_prompt_char_count"),
        "context_prompt_sha256": context.get("context_prompt_sha256"),
        "endpoint_value_recorded": provider_override.get("endpoint_value_recorded"),
        "credential_value_recorded": provider_override.get("credential_value_recorded"),
        "prompt_content_recorded": prompt.get("content_recorded"),
        "codex_exec_executed": codex_exec.get("executed"),
    }


def scan_artifacts(paths: Sequence[Path]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    scanned = 0
    for root in paths:
        if root.is_file():
            candidates = [root]
        else:
            candidates = sorted(path for path in root.rglob("*") if path.is_file())
        for path in candidates:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            scanned += 1
            for reason, pattern in FORBIDDEN_ARTIFACT_PATTERNS:
                matches = pattern.findall(text)
                if matches:
                    findings.append({"path": str(path), "reason": reason, "count": len(matches)})
    return {
        "status": "passed" if not findings else "failed",
        "scanned_file_count": scanned,
        "findings": findings,
        "record_credential_values": False,
        "record_bearer_tokens": False,
        "record_full_urls": False,
        "record_hostnames": False,
        "record_ip_addresses": False,
    }


def run(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    raw_dir = repo_root / args.raw_dir
    normalized_output = repo_root / args.normalized_output
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix="click-specialist-context-pack-smoke-"))
    env = dict(os.environ)
    env.setdefault("PYTHONPYCACHEPREFIX", "/tmp/barcarolle-pycache")

    try:
        workspace = build_workspace(temp_root)
        tool_path = repo_root / "experiments" / "core_narrative" / "tools" / "codex_cli_patch_command.py"
        manifest_checks = []
        results = []
        raw_artifact_paths = []
        for acut_id, expected_injection in ACUTS:
            manifest_checks.append(validate_manifest_side(repo_root, acut_id, expected_injection))
            acut_raw_dir = raw_dir / acut_id
            acut_raw_dir.mkdir(parents=True, exist_ok=True)
            summary_path = acut_raw_dir / "dry_run_summary.json"
            command = [
                sys.executable,
                str(tool_path),
                "--workspace",
                str(workspace),
                "--acut",
                str(acut_path(repo_root, acut_id)),
                "--artifact-dir",
                str(acut_raw_dir),
                "--summary-output",
                str(summary_path),
                "--codex-bin",
                args.codex_bin,
                "--dry-run",
            ]
            completed = run_command(command, cwd=repo_root, env=env)
            (acut_raw_dir / "command.stdout.txt").write_text(completed.stdout, encoding="utf-8")
            (acut_raw_dir / "command.stderr.txt").write_text(completed.stderr, encoding="utf-8")
            raw_artifact_paths.extend(
                [
                    str(summary_path),
                    str(acut_raw_dir / "command.stdout.txt"),
                    str(acut_raw_dir / "command.stderr.txt"),
                ]
            )
            if completed.returncode != 0:
                raise ToolError(
                    "codex CLI context-pack dry-run failed",
                    acut_id=acut_id,
                    exit_code=completed.returncode,
                    stderr=completed.stderr.strip(),
                )
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            evidence = validate_summary(summary, acut_id, expected_injection)
            evidence["raw_summary_path"] = str(summary_path)
            results.append(evidence)

        leakage_guard = scan_artifacts(
            [
                repo_root / "experiments" / "core_narrative" / "context_packs" / "click_specialist",
                raw_dir,
            ]
        )
        write_json(raw_dir / "leakage_guard.json", leakage_guard)
        raw_artifact_paths.append(str(raw_dir / "leakage_guard.json"))

        failures = [failure for result in results for failure in result["failures"]]
        if leakage_guard["status"] != "passed":
            failures.append("leakage guard scan failed")
        manifest_failures = [
            item["acut_id"]
            for item in manifest_checks
            if item["manifest_declares_context_pack"] is not item["expected_injection"]
        ]
        if manifest_failures:
            failures.append(f"manifest side context-pack mismatch: {', '.join(manifest_failures)}")

        payload = {
            "schema_version": "core-narrative.click-specialist-context-pack-smoke.v1",
            "tool": TOOL,
            "status": "passed" if not failures else "failed",
            "pack_id": PACK_ID,
            "marker": PACK_MARKER,
            "pack_hash": PACK_HASH,
            "model_call_made": False,
            "acut_adapter_invoked": False,
            "acut_attempt_started": False,
            "retry_started": False,
            "second_attempt_started": False,
            "specialist_live_run_started": False,
            "broad_execution_started": False,
            "large_batch_started": False,
            "ledger_appended": False,
            "raw_dir": str(raw_dir),
            "raw_artifacts": raw_artifact_paths,
            "manifest_checks": manifest_checks,
            "acut_results": results,
            "leakage_guard": leakage_guard,
            "failures": failures,
        }
        write_json(normalized_output, payload)
        print(stable_json(payload), end="")
        return 0 if not failures else 2
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def main() -> int:
    try:
        return run(sys.argv[1:])
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
