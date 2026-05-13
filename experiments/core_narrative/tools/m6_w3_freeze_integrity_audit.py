#!/usr/bin/env python3
"""Audit the M6-W3 frozen denominator before any W3 primary execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, load_manifest, write_json


TOOL = "m6_w3_freeze_integrity_audit"
SCHEMA_VERSION = "core-narrative.m6-w3-freeze-integrity-audit.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]

PRIMARY_MANIFEST = REPO_ROOT / "experiments/core_narrative/configs/tasks/rwork_click_w3.yaml"
RESERVE_MANIFEST = REPO_ROOT / "experiments/core_narrative/configs/tasks/rwork_click_w3_reserve.yaml"
CANDIDATE_MANIFEST = REPO_ROOT / "experiments/core_narrative/configs/tasks/rwork_click_w3_candidates.yaml"
PROTOCOL = REPO_ROOT / "experiments/core_narrative/configs/m6_w3_protocol.yaml"
ADMISSION_SUMMARY = REPO_ROOT / "experiments/core_narrative/results/m6_w3_admission/admission_summary_20260513.json"
ADMISSION_SUMMARY_PUBLIC = REPO_ROOT / "experiments/core_narrative/results/m6_w3_admission_20260513.json"
ADMISSION_SHEETS = REPO_ROOT / "experiments/core_narrative/results/m6_w3_admission/admission_sheets.json"
MATERIALIZATION_SUMMARY = REPO_ROOT / "experiments/core_narrative/results/m6_w3_admission/materialization_summary.json"
ADMISSION_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-13_m6_w3_admission_report.md"
ADMISSION_COMPLETION_AUDIT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-13_m6_w3_admission_completion_audit.md"
ACUT_CONFIG = REPO_ROOT / "experiments/core_narrative/configs/acuts/cheap-click-rbench-calibrated-v1.yaml"
CONTEXT_MANIFEST = REPO_ROOT / "experiments/core_narrative/context_packs/click_rbench_calibrated_v1/manifest.json"
LEAKAGE_AUDIT = REPO_ROOT / "experiments/core_narrative/context_packs/click_rbench_calibrated_v1/leakage_audit.json"
LLM_ACCESS = REPO_ROOT / "experiments/core_narrative/configs/llm_access.yaml"

DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/m6_w3_freeze_integrity_audit_20260513.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-13_m6_w3_freeze_integrity_audit.md"

PRIOR_MANIFESTS = [
    REPO_ROOT / "experiments/core_narrative/configs/tasks/rbench_click.yaml",
    REPO_ROOT / "experiments/core_narrative/configs/tasks/rwork_click.yaml",
    REPO_ROOT / "experiments/core_narrative/configs/tasks/rwork_click_v2.yaml",
    REPO_ROOT / "experiments/core_narrative/configs/tasks/rwork_click_v2_reserve.yaml",
]
W3_RESULT_PATHS = [
    REPO_ROOT / "experiments/core_narrative/results/m6_w3_primary",
    REPO_ROOT / "experiments/core_narrative/results/m6_r3",
    REPO_ROOT / "experiments/core_narrative/results/acut_g",
    REPO_ROOT / "experiments/core_narrative/results/m6_acut_g",
]
REMOTE_ARTIFACTS = [
    PRIMARY_MANIFEST,
    RESERVE_MANIFEST,
    CANDIDATE_MANIFEST,
    PROTOCOL,
    ADMISSION_SUMMARY,
    ADMISSION_SUMMARY_PUBLIC,
    ADMISSION_SHEETS,
    MATERIALIZATION_SUMMARY,
    ADMISSION_REPORT,
    ADMISSION_COMPLETION_AUDIT,
    ACUT_CONFIG,
    CONTEXT_MANIFEST,
    LEAKAGE_AUDIT,
]
EXPECTED_ACUT_ORDER = [
    "cheap-generic-swe",
    "cheap-click-deep-specialist-v2",
    "cheap-click-rbench-calibrated-v1",
    "frontier-generic-swe",
]
EXPECTED_RUN_SEED = "m6-w3-primary-20260513-denominator-v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DIFF_MARKERS = (
    "diff --git",
    "\n@@",
    "\n--- a/",
    "\n+++ b/",
    "\nindex ",
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Audit JSON output path.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Markdown audit report path.")
    parser.add_argument("--remote-ref", help="Remote ref to compare with HEAD, default origin/<current-branch>.")
    parser.add_argument("--skip-remote-fetch", action="store_true", help="Do not fetch the remote ref before checking.")
    parser.add_argument("--skip-readiness-tests", action="store_true", help="Do not run readiness unit tests.")
    return parser.parse_args(list(argv) if argv is not None else None)


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def rel_paths(paths: Sequence[Path]) -> list[str]:
    return [repo_relative(path) for path in paths]


def nested_get(mapping: Mapping[str, Any], keys: Sequence[str]) -> Any:
    value: Any = mapping
    for key in keys:
        if not isinstance(value, Mapping):
            return None
        value = value.get(key)
    return value


def make_check(check_id: str, description: str, passed: bool, evidence: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": check_id,
        "description": description,
        "status": "passed" if passed else "failed",
        "evidence": dict(evidence),
    }


def overall_status(checks: Sequence[Mapping[str, Any]]) -> str:
    return "passed" if all(check.get("status") == "passed" for check in checks) else "failed"


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def manifest_tasks(manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    tasks = manifest.get("tasks")
    return [task for task in tasks if isinstance(task, Mapping)] if isinstance(tasks, list) else []


def task_candidate_id(task: Mapping[str, Any]) -> str | None:
    metadata = task.get("metadata") if isinstance(task.get("metadata"), Mapping) else {}
    candidate_id = metadata.get("candidate_id")
    return str(candidate_id) if candidate_id else None


def primary_sheet_evidence(tasks: Sequence[Mapping[str, Any]], sheets_by_candidate: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    missing_sheet_task_ids: list[str] = []
    invalid_smoke_task_ids: list[str] = []
    missing_digest_task_ids: list[str] = []
    missing_anchor_record_task_ids: list[str] = []
    reference_digest_mismatch_task_ids: list[str] = []
    accepted_count = 0

    for task in tasks:
        task_id = str(task.get("task_id", "unknown"))
        candidate_id = task_candidate_id(task)
        sheet = sheets_by_candidate.get(candidate_id or "")
        if not isinstance(sheet, Mapping):
            missing_sheet_task_ids.append(task_id)
            continue

        if sheet.get("admission_decision") == "accepted":
            accepted_count += 1
        noop = sheet.get("no_op_result") if isinstance(sheet.get("no_op_result"), Mapping) else {}
        reference = sheet.get("reference_result") if isinstance(sheet.get("reference_result"), Mapping) else {}
        if not (
            noop.get("status") == "failed"
            and noop.get("expected_no_op_fails") is True
            and reference.get("status") == "passed"
            and reference.get("oracle_status") == "reference_passed"
        ):
            invalid_smoke_task_ids.append(task_id)

        if not (
            is_sha256(sheet.get("statement_digest"))
            and is_sha256(sheet.get("reference_patch_digest"))
            and is_sha256(sheet.get("hidden_verifier_digest"))
        ):
            missing_digest_task_ids.append(task_id)

        source = task.get("source") if isinstance(task.get("source"), Mapping) else {}
        anchor_id = source.get("anchor_id")
        changed_file_anchor_set = sheet.get("changed_file_anchor_set")
        if not isinstance(anchor_id, str) or not isinstance(changed_file_anchor_set, list) or not changed_file_anchor_set:
            missing_anchor_record_task_ids.append(task_id)

        source_compare = task.get("source_compare") if isinstance(task.get("source_compare"), Mapping) else {}
        if source_compare.get("reference_patch_digest") != sheet.get("reference_patch_digest"):
            reference_digest_mismatch_task_ids.append(task_id)

    return {
        "task_count": len(tasks),
        "accepted_sheet_count": accepted_count,
        "missing_sheet_task_ids": missing_sheet_task_ids,
        "invalid_smoke_task_ids": invalid_smoke_task_ids,
        "missing_digest_task_ids": missing_digest_task_ids,
        "missing_anchor_record_task_ids": missing_anchor_record_task_ids,
        "reference_digest_mismatch_task_ids": reference_digest_mismatch_task_ids,
    }


def public_statement_findings(text: str, *, target_commit: str | None = None) -> list[str]:
    lowered = text.lower()
    findings: list[str] = []
    if any(marker in text for marker in DIFF_MARKERS):
        findings.append("implementation_diff")
    if target_commit and target_commit in text:
        findings.append("target_commit")
    if "target_commit" in lowered or "target commit" in lowered:
        findings.append("target_commit")
    if "reference patch" in lowered or "patch_sha256" in lowered or "reference_patch" in lowered:
        findings.append("reference_patch")
    if "hidden verifier" in lowered or "verifier/hidden" in lowered or "hidden/tests" in lowered:
        findings.append("hidden_verifier")
    if "w3 acut output" in lowered or "failed patch" in lowered or "near-miss score" in lowered:
        findings.append("acut_output")
    return sorted(set(findings))


def public_statement_evidence(tasks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    findings_by_task: dict[str, list[str]] = {}
    checked_paths: list[str] = []
    missing_paths: list[str] = []

    for task in tasks:
        task_id = str(task.get("task_id", "unknown"))
        statement_path = REPO_ROOT / "experiments/core_narrative/tasks/click/w3" / task_id / "public/statement.md"
        if not statement_path.exists():
            missing_paths.append(repo_relative(statement_path))
            findings_by_task[task_id] = ["missing_public_statement"]
            continue
        checked_paths.append(repo_relative(statement_path))
        source = task.get("source") if isinstance(task.get("source"), Mapping) else {}
        findings = public_statement_findings(statement_path.read_text(encoding="utf-8"), target_commit=source.get("target_commit"))
        if findings:
            findings_by_task[task_id] = findings

    return {
        "checked_paths": checked_paths,
        "missing_paths": missing_paths,
        "findings_by_task": findings_by_task,
    }


def collect_source_anchors(manifests: Sequence[Path]) -> dict[str, list[str]]:
    anchors: dict[str, list[str]] = {}
    for manifest_path in manifests:
        manifest = load_manifest(manifest_path)
        manifest_anchors: list[str] = []
        for task in manifest_tasks(manifest):
            source = task.get("source") if isinstance(task.get("source"), Mapping) else {}
            anchor_id = source.get("anchor_id")
            target_commit = source.get("target_commit")
            if isinstance(anchor_id, str):
                manifest_anchors.append(anchor_id)
            if isinstance(target_commit, str):
                manifest_anchors.append(f"commit:{target_commit}")
        anchors[repo_relative(manifest_path)] = sorted(set(manifest_anchors))
    return anchors


def disjoint_anchor_evidence(primary_tasks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    primary_anchors: set[str] = set()
    for task in primary_tasks:
        source = task.get("source") if isinstance(task.get("source"), Mapping) else {}
        anchor_id = source.get("anchor_id")
        target_commit = source.get("target_commit")
        if isinstance(anchor_id, str):
            primary_anchors.add(anchor_id)
        if isinstance(target_commit, str):
            primary_anchors.add(f"commit:{target_commit}")

    prior_by_manifest = collect_source_anchors(PRIOR_MANIFESTS)
    overlaps: dict[str, list[str]] = {}
    for manifest, anchors in prior_by_manifest.items():
        overlap = sorted(primary_anchors.intersection(anchors))
        if overlap:
            overlaps[manifest] = overlap
    return {
        "primary_anchor_count": len(primary_anchors),
        "prior_manifest_anchor_counts": {manifest: len(anchors) for manifest, anchors in prior_by_manifest.items()},
        "overlaps": overlaps,
    }


def context_pack_hash_check(acut: Mapping[str, Any], context_manifest: Mapping[str, Any]) -> dict[str, Any]:
    acut_pack_hash = nested_get(acut, ["metadata", "specialist_context", "context_pack", "pack_hash"])
    manifest_pack_hash = context_manifest.get("pack_hash")
    return make_check(
        "context.hash_match",
        "calibrated context pack hash matches the ACUT manifest hash",
        bool(acut_pack_hash and acut_pack_hash == manifest_pack_hash),
        {
            "acut_pack_hash": acut_pack_hash,
            "context_manifest_pack_hash": manifest_pack_hash,
            "acut_config": repo_relative(ACUT_CONFIG),
            "context_manifest": repo_relative(CONTEXT_MANIFEST),
        },
    )


def context_leakage_evidence(acut: Mapping[str, Any], context_manifest: Mapping[str, Any], leakage_audit: Mapping[str, Any]) -> dict[str, Any]:
    forbidden_context_flags = {
        "manifest.generation_timing.uses_w3_material": nested_get(context_manifest, ["generation_timing", "uses_w3_material"]),
        "manifest.generation_timing.uses_observed_m5_w2_acut_outputs": nested_get(context_manifest, ["generation_timing", "uses_observed_m5_w2_acut_outputs"]),
        "manifest.source_material_policy.w3_target_commits_used": nested_get(context_manifest, ["source_material_policy", "w3_target_commits_used"]),
        "manifest.source_material_policy.w3_reference_patches_used": nested_get(context_manifest, ["source_material_policy", "w3_reference_patches_used"]),
        "manifest.source_material_policy.w3_hidden_verifier_tests_used": nested_get(context_manifest, ["source_material_policy", "w3_hidden_verifier_tests_used"]),
        "manifest.source_material_policy.w3_acut_outputs_used": nested_get(context_manifest, ["source_material_policy", "w3_acut_outputs_used"]),
        "manifest.source_material_policy.acut_outputs_or_failed_patches_used": nested_get(context_manifest, ["source_material_policy", "acut_outputs_or_failed_patches_used"]),
        "manifest.leakage_guards.w3_target_commits_recorded": nested_get(context_manifest, ["leakage_guards", "w3_target_commits_recorded"]),
        "manifest.leakage_guards.w3_reference_diffs_recorded": nested_get(context_manifest, ["leakage_guards", "w3_reference_diffs_recorded"]),
        "manifest.leakage_guards.hidden_verifier_paths_recorded": nested_get(context_manifest, ["leakage_guards", "hidden_verifier_paths_recorded"]),
        "manifest.leakage_guards.w3_acut_outputs_recorded": nested_get(context_manifest, ["leakage_guards", "w3_acut_outputs_recorded"]),
        "manifest.leakage_guards.m5_w2_acut_outputs_recorded": nested_get(context_manifest, ["leakage_guards", "m5_w2_acut_outputs_recorded"]),
        "leakage.forbidden_sources_checked.w3_target_commits_used": nested_get(leakage_audit, ["forbidden_sources_checked", "w3_target_commits_used"]),
        "leakage.forbidden_sources_checked.w3_reference_patches_used": nested_get(leakage_audit, ["forbidden_sources_checked", "w3_reference_patches_used"]),
        "leakage.forbidden_sources_checked.w3_hidden_verifiers_used": nested_get(leakage_audit, ["forbidden_sources_checked", "w3_hidden_verifiers_used"]),
        "leakage.forbidden_sources_checked.w3_final_diffs_used": nested_get(leakage_audit, ["forbidden_sources_checked", "w3_final_diffs_used"]),
        "leakage.forbidden_sources_checked.w3_acut_outputs_used": nested_get(leakage_audit, ["forbidden_sources_checked", "w3_acut_outputs_used"]),
        "leakage.forbidden_sources_checked.m5_w2_acut_outputs_used_as_calibration": nested_get(
            leakage_audit,
            ["forbidden_sources_checked", "m5_w2_acut_outputs_used_as_calibration"],
        ),
        "acut.metadata.specialist_context.calibration_basis.w3_material_used": nested_get(
            acut,
            ["metadata", "specialist_context", "calibration_basis", "w3_material_used"],
        ),
        "acut.metadata.specialist_context.calibration_basis.w2_outputs_used_as_calibration": nested_get(
            acut,
            ["metadata", "specialist_context", "calibration_basis", "w2_outputs_used_as_calibration"],
        ),
    }
    return {
        "leakage_audit_status": leakage_audit.get("status"),
        "forbidden_true_flags": {key: value for key, value in forbidden_context_flags.items() if value is not False},
    }


def freeze_control_evidence(primary: Mapping[str, Any], reserve: Mapping[str, Any], summary: Mapping[str, Any], protocol: Mapping[str, Any]) -> dict[str, Any]:
    primary_freeze = primary.get("freeze") if isinstance(primary.get("freeze"), Mapping) else {}
    reserve_freeze = reserve.get("freeze") if isinstance(reserve.get("freeze"), Mapping) else {}
    summary_freeze = summary.get("freeze") if isinstance(summary.get("freeze"), Mapping) else {}
    protocol_denominator = protocol.get("w3_denominator") if isinstance(protocol.get("w3_denominator"), Mapping) else {}
    return {
        "primary_seed": primary_freeze.get("deterministic_run_seed"),
        "reserve_seed": reserve_freeze.get("deterministic_run_seed"),
        "summary_seed": summary_freeze.get("deterministic_run_seed"),
        "protocol_seed": protocol_denominator.get("deterministic_run_seed"),
        "primary_acut_order": primary_freeze.get("acut_run_order"),
        "reserve_acut_order": reserve_freeze.get("acut_run_order"),
        "summary_acut_order": summary_freeze.get("acut_run_order"),
        "protocol_acut_order": protocol_denominator.get("acut_run_order"),
        "primary_status_mapping_keys": sorted((primary_freeze.get("status_mapping") or {}).keys()),
        "protocol_status_mapping_keys": sorted((protocol_denominator.get("freeze_status_mapping") or {}).keys()),
        "primary_infra_policy": primary_freeze.get("infra_rerun_policy"),
        "protocol_infra_policy": protocol_denominator.get("infra_rerun_policy"),
    }


def freeze_controls_pass(evidence: Mapping[str, Any]) -> bool:
    seeds = [evidence.get("primary_seed"), evidence.get("reserve_seed"), evidence.get("summary_seed"), evidence.get("protocol_seed")]
    orders = [
        evidence.get("primary_acut_order"),
        evidence.get("reserve_acut_order"),
        evidence.get("summary_acut_order"),
        evidence.get("protocol_acut_order"),
    ]
    primary_policy = evidence.get("primary_infra_policy") if isinstance(evidence.get("primary_infra_policy"), Mapping) else {}
    protocol_policy = evidence.get("protocol_infra_policy") if isinstance(evidence.get("protocol_infra_policy"), Mapping) else {}
    return (
        all(seed == EXPECTED_RUN_SEED for seed in seeds)
        and all(order == EXPECTED_ACUT_ORDER for order in orders)
        and primary_policy.get("best_of_n_allowed") is False
        and primary_policy.get("acut_specific_retry_allowed") is False
        and protocol_policy.get("best_of_n_allowed") is False
        and protocol_policy.get("acut_specific_retry_allowed") is False
    )


def cost_ledger_evidence(llm_access: Mapping[str, Any]) -> dict[str, Any]:
    ledger_path_value = nested_get(llm_access, ["ledger", "path"])
    ledger_path = REPO_ROOT / str(ledger_path_value) if ledger_path_value else REPO_ROOT / "experiments/core_narrative/results/cost_ledger.jsonl"
    probe_path = ledger_path.parent / ".m6_w3_freeze_audit_write_probe.tmp"
    write_probe_passed = False
    error = None
    try:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        probe_path.write_text("ok\n", encoding="utf-8")
        write_probe_passed = probe_path.read_text(encoding="utf-8") == "ok\n"
    except OSError as exc:
        error = str(exc)
    finally:
        try:
            probe_path.unlink(missing_ok=True)
        except OSError:
            pass
    return {
        "ledger_path": repo_relative(ledger_path),
        "ledger_exists": ledger_path.exists(),
        "parent_writable_probe_passed": write_probe_passed,
        "required_before_acut_execution": nested_get(llm_access, ["ledger", "required_before_acut_execution"]),
        "error": error,
    }


def run_capture(command: Sequence[str], *, timeout: int = 120, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=str(REPO_ROOT),
        env=dict(env) if env is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def run_capture_bytes(command: Sequence[str], *, timeout: int = 120) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        list(command),
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def run_readiness_tests() -> dict[str, Any]:
    env = dict(os.environ)
    existing_pythonpath = env.get("PYTHONPATH")
    tools_path = repo_relative(REPO_ROOT / "experiments/core_narrative/tools")
    env["PYTHONPATH"] = tools_path if not existing_pythonpath else f"{tools_path}{os.pathsep}{existing_pythonpath}"
    command = [
        sys.executable,
        "-m",
        "unittest",
        "experiments/core_narrative/tools/test_workspace_mode_runner.py",
        "experiments/core_narrative/tools/test_apply_source_derived_url_policy.py",
    ]
    completed = run_capture(command, timeout=240, env=env)
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def git(*args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return run_capture(["git", *args], timeout=timeout)


def current_remote_ref() -> str:
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch.returncode != 0:
        raise ToolError("failed to determine current branch", stderr=branch.stderr[-500:])
    branch_name = branch.stdout.strip()
    if not branch_name or branch_name == "HEAD":
        raise ToolError("current checkout is detached; pass --remote-ref explicitly")
    return f"origin/{branch_name}"


def fetch_remote_ref(remote_ref: str) -> subprocess.CompletedProcess[str]:
    if "/" not in remote_ref:
        return git("fetch", "origin", remote_ref, timeout=180)
    remote, branch = remote_ref.split("/", 1)
    return git("fetch", remote, branch, timeout=180)


def remote_artifact_evidence(remote_ref: str, paths: Sequence[Path], *, fetch: bool) -> dict[str, Any]:
    fetch_result: dict[str, Any] | None = None
    if fetch:
        completed = fetch_remote_ref(remote_ref)
        fetch_result = {
            "exit_code": completed.returncode,
            "stdout_tail": completed.stdout[-1000:],
            "stderr_tail": completed.stderr[-1000:],
        }

    head = git("rev-parse", "HEAD")
    remote = git("rev-parse", remote_ref)
    missing_paths: list[str] = []
    content_mismatch_paths: list[str] = []
    checked_paths = rel_paths(paths)
    if remote.returncode == 0:
        for path in checked_paths:
            local_path = REPO_ROOT / path
            remote_content = run_capture_bytes(["git", "show", f"{remote_ref}:{path}"])
            if remote_content.returncode != 0:
                missing_paths.append(path)
            elif local_path.exists():
                local_digest = hashlib.sha256(local_path.read_bytes()).hexdigest()
                remote_digest = hashlib.sha256(remote_content.stdout).hexdigest()
                if local_digest != remote_digest:
                    content_mismatch_paths.append(path)

    return {
        "remote_ref": remote_ref,
        "fetch": fetch_result,
        "local_head": head.stdout.strip() if head.returncode == 0 else None,
        "remote_head": remote.stdout.strip() if remote.returncode == 0 else None,
        "head_exit_code": head.returncode,
        "remote_exit_code": remote.returncode,
        "same_commit": head.returncode == 0 and remote.returncode == 0 and head.stdout.strip() == remote.stdout.strip(),
        "checked_paths": checked_paths,
        "missing_paths": missing_paths,
        "content_mismatch_paths": content_mismatch_paths,
    }


def no_model_run_evidence(summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "admission_summary_flags": {
            "w3_primary_run": summary.get("w3_primary_run"),
            "r3_run": summary.get("r3_run"),
            "acut_g_run": summary.get("acut_g_run"),
            "model_calls_made": summary.get("model_calls_made"),
        },
        "forbidden_result_paths_existing": [repo_relative(path) for path in W3_RESULT_PATHS if path.exists()],
    }


def build_audit_payload(*, remote_ref: str, skip_remote_fetch: bool, skip_readiness_tests: bool) -> dict[str, Any]:
    primary = load_manifest(PRIMARY_MANIFEST)
    reserve = load_manifest(RESERVE_MANIFEST)
    summary = load_manifest(ADMISSION_SUMMARY)
    sheets_payload = load_manifest(ADMISSION_SHEETS)
    materialization = load_manifest(MATERIALIZATION_SUMMARY)
    protocol = load_manifest(PROTOCOL)
    acut = load_manifest(ACUT_CONFIG)
    context_manifest = load_manifest(CONTEXT_MANIFEST)
    leakage = load_manifest(LEAKAGE_AUDIT)
    llm_access = load_manifest(LLM_ACCESS)

    primary_tasks = manifest_tasks(primary)
    reserve_tasks = manifest_tasks(reserve)
    sheets = sheets_payload.get("sheets") if isinstance(sheets_payload.get("sheets"), list) else []
    sheets_by_candidate = {
        str(sheet.get("candidate_id")): sheet
        for sheet in sheets
        if isinstance(sheet, Mapping) and sheet.get("candidate_id")
    }

    checks: list[dict[str, Any]] = []
    checks.append(
        make_check(
            "freeze.primary_manifest",
            "rwork_click_w3.yaml exists and contains 20 primary tasks",
            PRIMARY_MANIFEST.exists() and primary.get("task_count") == 20 and len(primary_tasks) == 20,
            {
                "path": repo_relative(PRIMARY_MANIFEST),
                "exists": PRIMARY_MANIFEST.exists(),
                "manifest_task_count": primary.get("task_count"),
                "observed_task_count": len(primary_tasks),
                "status": primary.get("status"),
            },
        )
    )
    checks.append(
        make_check(
            "freeze.reserve_manifest",
            "rwork_click_w3_reserve.yaml exists and contains 5 reserve tasks",
            RESERVE_MANIFEST.exists() and reserve.get("task_count") == 5 and len(reserve_tasks) == 5,
            {
                "path": repo_relative(RESERVE_MANIFEST),
                "exists": RESERVE_MANIFEST.exists(),
                "manifest_task_count": reserve.get("task_count"),
                "observed_task_count": len(reserve_tasks),
                "status": reserve.get("status"),
            },
        )
    )
    checks.append(
        make_check(
            "admission.summary_counts",
            "admission_summary_20260513.json exists with expected candidate/admission counts",
            ADMISSION_SUMMARY.exists()
            and summary.get("candidate_count") == 40
            and summary.get("admitted_candidate_count") == 28
            and summary.get("primary_task_count") == 20
            and summary.get("reserve_task_count") == 5,
            {
                "path": repo_relative(ADMISSION_SUMMARY),
                "exists": ADMISSION_SUMMARY.exists(),
                "candidate_count": summary.get("candidate_count"),
                "admitted_candidate_count": summary.get("admitted_candidate_count"),
                "primary_task_count": summary.get("primary_task_count"),
                "reserve_task_count": summary.get("reserve_task_count"),
                "status": summary.get("status"),
            },
        )
    )

    sheet_evidence = primary_sheet_evidence(primary_tasks, sheets_by_candidate)
    checks.append(
        make_check(
            "admission.primary_sheet_coverage",
            "every primary task has an accepted admission sheet",
            not sheet_evidence["missing_sheet_task_ids"] and sheet_evidence["accepted_sheet_count"] == len(primary_tasks),
            sheet_evidence,
        )
    )
    checks.append(
        make_check(
            "admission.primary_smoke_records",
            "every primary task records no-op fail and reference patch pass",
            not sheet_evidence["invalid_smoke_task_ids"],
            {
                "invalid_smoke_task_ids": sheet_evidence["invalid_smoke_task_ids"],
                "checked_task_count": sheet_evidence["task_count"],
            },
        )
    )
    checks.append(
        make_check(
            "admission.primary_digest_records",
            "every primary task records statement, reference patch, and hidden verifier digests",
            not sheet_evidence["missing_digest_task_ids"] and not sheet_evidence["reference_digest_mismatch_task_ids"],
            {
                "missing_digest_task_ids": sheet_evidence["missing_digest_task_ids"],
                "reference_digest_mismatch_task_ids": sheet_evidence["reference_digest_mismatch_task_ids"],
                "checked_task_count": sheet_evidence["task_count"],
            },
        )
    )
    checks.append(
        make_check(
            "admission.primary_anchor_records",
            "every primary task records source anchor and changed-file anchors",
            not sheet_evidence["missing_anchor_record_task_ids"],
            {
                "missing_anchor_record_task_ids": sheet_evidence["missing_anchor_record_task_ids"],
                "checked_task_count": sheet_evidence["task_count"],
            },
        )
    )

    disjoint = disjoint_anchor_evidence(primary_tasks)
    checks.append(
        make_check(
            "denominator.disjoint_anchors",
            "W3 primary task anchors are disjoint from RBench, RWork-v1, W2 primary, and W2 reserve",
            not disjoint["overlaps"],
            disjoint,
        )
    )

    public_redaction = public_statement_evidence(primary_tasks)
    checks.append(
        make_check(
            "public.statement_redaction",
            "public statements contain no implementation diff, target commit, reference patch, hidden verifier, or ACUT output",
            not public_redaction["missing_paths"] and not public_redaction["findings_by_task"],
            public_redaction,
        )
    )

    checks.append(context_pack_hash_check(acut, context_manifest))

    leakage_evidence = context_leakage_evidence(acut, context_manifest, leakage)
    checks.append(
        make_check(
            "context.leakage_w3_false",
            "leakage audit and context pack record W3 material and M5-W2 ACUT outputs as unused",
            leakage_evidence["leakage_audit_status"] == "passed_for_protocol_prep" and not leakage_evidence["forbidden_true_flags"],
            leakage_evidence,
        )
    )

    protocol_denominator = protocol.get("w3_denominator") if isinstance(protocol.get("w3_denominator"), Mapping) else {}
    checks.append(
        make_check(
            "protocol.denominator_status",
            "m6_w3_protocol.yaml denominator status is synchronized to denominator_frozen_primary_not_run",
            protocol.get("status") == "protocol_synced_denominator_frozen_no_primary_run"
            and protocol_denominator.get("status") == "denominator_frozen_primary_not_run"
            and protocol_denominator.get("accepted_task_count") == 20
            and nested_get(protocol_denominator, ["metadata_sync", "task_reselection_performed"]) is False
            and nested_get(protocol_denominator, ["metadata_sync", "w3_primary_run_performed"]) is False,
            {
                "path": repo_relative(PROTOCOL),
                "protocol_status": protocol.get("status"),
                "w3_denominator_status": protocol_denominator.get("status"),
                "accepted_task_count": protocol_denominator.get("accepted_task_count"),
                "metadata_sync": protocol_denominator.get("metadata_sync"),
            },
        )
    )

    freeze_evidence = freeze_control_evidence(primary, reserve, summary, protocol)
    checks.append(
        make_check(
            "readiness.freeze_controls",
            "deterministic run seed, ACUT order, status mapping, no best-of-N, and no ACUT-specific retry are frozen",
            freeze_controls_pass(freeze_evidence),
            freeze_evidence,
        )
    )

    no_runs = no_model_run_evidence(summary)
    checks.append(
        make_check(
            "boundary.no_w3_r3_or_g_run",
            "W3 primary, R3, and ACUT G have not been run in this phase",
            no_runs["admission_summary_flags"] == {
                "w3_primary_run": False,
                "r3_run": False,
                "acut_g_run": False,
                "model_calls_made": 0,
            }
            and not no_runs["forbidden_result_paths_existing"],
            no_runs,
        )
    )

    ledger = cost_ledger_evidence(llm_access)
    checks.append(
        make_check(
            "readiness.cost_ledger_writable",
            "cost ledger path is writable before any live ACUT execution",
            ledger["ledger_exists"] is True
            and ledger["parent_writable_probe_passed"] is True
            and ledger["required_before_acut_execution"] is True,
            ledger,
        )
    )

    if skip_readiness_tests:
        readiness = {"skipped": True}
        readiness_passed = False
    else:
        readiness = run_readiness_tests()
        readiness_passed = readiness["exit_code"] == 0
    checks.append(
        make_check(
            "readiness.workspace_and_source_url_tests",
            "workspace-mode runner and source-derived URL-only policy tests pass",
            readiness_passed,
            readiness,
        )
    )

    remote = remote_artifact_evidence(remote_ref, REMOTE_ARTIFACTS, fetch=not skip_remote_fetch)
    checks.append(
        make_check(
            "remote.same_commit_artifacts",
            "remote branch at the same commit can access frozen protocol, manifests, admission artifacts, and context artifacts",
            remote["same_commit"] is True
            and not remote["missing_paths"]
            and not remote["content_mismatch_paths"]
            and (remote.get("fetch") is None or remote["fetch"]["exit_code"] == 0),
            remote,
        )
    )

    status = overall_status(checks)
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": status,
        "generated_at": iso_now(),
        "objective": "M6-W3 0-model freeze integrity audit before W3 primary execution",
        "model_calls_made": 0,
        "w3_primary_run": False,
        "r3_run": False,
        "acut_g_run": False,
        "artifact_paths": {
            "primary_manifest": repo_relative(PRIMARY_MANIFEST),
            "reserve_manifest": repo_relative(RESERVE_MANIFEST),
            "candidate_manifest": repo_relative(CANDIDATE_MANIFEST),
            "admission_summary": repo_relative(ADMISSION_SUMMARY),
            "admission_sheets": repo_relative(ADMISSION_SHEETS),
            "materialization_summary": repo_relative(MATERIALIZATION_SUMMARY),
            "protocol": repo_relative(PROTOCOL),
            "acut_config": repo_relative(ACUT_CONFIG),
            "context_manifest": repo_relative(CONTEXT_MANIFEST),
            "leakage_audit": repo_relative(LEAKAGE_AUDIT),
        },
        "counts": {
            "candidate_count": summary.get("candidate_count"),
            "admitted_candidate_count": summary.get("admitted_candidate_count"),
            "primary_task_count": len(primary_tasks),
            "reserve_task_count": len(reserve_tasks),
            "admission_sheet_count": len(sheets),
            "primary_family_counts": dict(sorted(Counter(str(task.get("task_family")) for task in primary_tasks).items())),
        },
        "checks": checks,
    }


def render_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# M6-W3 Freeze Integrity Audit",
        "",
        f"Status: `{payload.get('status')}`",
        f"Generated at: `{payload.get('generated_at')}`",
        "",
        "## Scope",
        "",
        "This is a 0-model audit before W3 primary execution. It verifies frozen W3 denominator artifacts, protocol synchronization, context-pack leakage boundaries, remote availability, and execution readiness.",
        "",
        "No W3 primary, R3, or ACUT G run is authorized or performed by this audit.",
        "",
        "## Counts",
        "",
    ]
    counts = payload.get("counts") if isinstance(payload.get("counts"), Mapping) else {}
    lines.extend(
        [
            f"- Candidate count: `{counts.get('candidate_count')}`",
            f"- Accepted candidate count: `{counts.get('admitted_candidate_count')}`",
            f"- Primary task count: `{counts.get('primary_task_count')}`",
            f"- Reserve task count: `{counts.get('reserve_task_count')}`",
            f"- Admission sheet count: `{counts.get('admission_sheet_count')}`",
            "",
            "## Checks",
            "",
            "| ID | Status | Evidence |",
            "|---|---|---|",
        ]
    )
    for check in payload.get("checks", []):
        if not isinstance(check, Mapping):
            continue
        evidence = json.dumps(check.get("evidence", {}), sort_keys=True)
        if len(evidence) > 500:
            evidence = evidence[:497] + "..."
        lines.append(f"| `{check.get('id')}` | `{check.get('status')}` | `{evidence}` |")
    lines.extend(
        [
            "",
            "## Output Boundary",
            "",
            "- This audit does not change the W3 denominator.",
            "- This audit does not run models.",
            "- If status is `passed`, W3 primary may be run as a separate step under the frozen seed, ACUT order, scoring map, and infra policy.",
            "",
        ]
    )
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    remote_ref = args.remote_ref or current_remote_ref()
    payload = build_audit_payload(
        remote_ref=remote_ref,
        skip_remote_fetch=args.skip_remote_fetch,
        skip_readiness_tests=args.skip_readiness_tests,
    )
    output_path = Path(args.output)
    report_path = Path(args.report)
    write_json(output_path, payload)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(payload), encoding="utf-8")
    emit_json({**payload, "output_path": repo_relative(output_path), "report_path": repo_relative(report_path)})
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
