#!/usr/bin/env python3
"""Audit frozen E/B manifests before external-calibrated ACUT execution."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import external_calibrated_repository_admission as repo_admission
from _common import ToolError, emit_json, fail, git, iso_now, load_manifest, write_json


TOOL = "external_calibrated_freeze_integrity_audit"
SCHEMA_VERSION = "external-calibrated-repo-benchmark.freeze-integrity-audit.v1"
PROTOCOL_ID = repo_admission.PROTOCOL_ID
REPO_ROOT = repo_admission.REPO_ROOT
RESULTS_ROOT = repo_admission.RESULTS_ROOT
REPORTS_ROOT = repo_admission.REPORTS_ROOT

DEFAULT_PROTOCOL = REPO_ROOT / "experiments/core_narrative/configs/external_calibrated_benchmark_20260515.yaml"
DEFAULT_REPOSITORY_ADMISSION = RESULTS_ROOT / "repository_admission/external_calibrated_phase0_admission_20260515.json"
DEFAULT_E_CONFIG = REPO_ROOT / "experiments/core_narrative/configs/external/swebench_sympy_e_v1.yaml"
DEFAULT_E_RESULT = RESULTS_ROOT / "external/e_task_smoke.json"
DEFAULT_B_PRIMARY = REPO_ROOT / "experiments/core_narrative/configs/tasks/sympy_barcarolle_b_v2.yaml"
DEFAULT_B_RESERVE = REPO_ROOT / "experiments/core_narrative/configs/tasks/sympy_barcarolle_b_v2_reserve.yaml"
DEFAULT_B_SUMMARY = RESULTS_ROOT / "task_admission/sympy_b_admission_summary_v2.json"
DEFAULT_OUTPUT = RESULTS_ROOT / "audits/external_calibrated_freeze_integrity_audit_20260516.json"
DEFAULT_REPORT = REPORTS_ROOT / "external_calibrated_freeze_integrity_audit.md"

PUBLIC_RAW_ARTIFACT_ROOTS = (
    RESULTS_ROOT / "repository_admission",
    RESULTS_ROOT / "external",
)
RAW_ARTIFACT_NAME_RE = re.compile(r"(patch\.diff|eval\.sh|test_output\.txt|run_instance\.log|report\.json)$")
RAW_VALUE_FRAGMENTS = (
    "diff --git",
    "reference_source.patch",
    "hidden_tests.py",
    "run_instance.log",
    "test_output.txt",
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", default=str(DEFAULT_PROTOCOL), help="Protocol manifest YAML.")
    parser.add_argument("--repository-admission", default=str(DEFAULT_REPOSITORY_ADMISSION), help="Repository admission JSON.")
    parser.add_argument("--e-config", default=str(DEFAULT_E_CONFIG), help="Frozen E YAML.")
    parser.add_argument("--e-result", default=str(DEFAULT_E_RESULT), help="Frozen E result JSON.")
    parser.add_argument("--b-primary", default=str(DEFAULT_B_PRIMARY), help="Frozen primary B YAML.")
    parser.add_argument("--b-reserve", default=str(DEFAULT_B_RESERVE), help="Frozen reserve B YAML.")
    parser.add_argument("--b-summary", default=str(DEFAULT_B_SUMMARY), help="B task admission summary JSON.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Structured audit JSON output.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Markdown report output.")
    return parser.parse_args(list(argv) if argv is not None else None)


def repo_relative(path: Path) -> str:
    return repo_admission.repo_relative(path)


def task_list(manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    tasks = manifest.get("tasks")
    return [task for task in tasks if isinstance(task, Mapping)] if isinstance(tasks, list) else []


def true_rate(items: Sequence[Mapping[str, Any]], key: str) -> float | None:
    if not items:
        return None
    return sum(1 for item in items if item.get(key) is True) / len(items)


def append_if(condition: bool, target: list[str], value: str) -> None:
    if condition:
        target.append(value)


def audit_e_freeze(e_config: Mapping[str, Any], e_result: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    tasks = task_list(e_config)
    task_table = e_result.get("task_table") if isinstance(e_result.get("task_table"), list) else []
    result_task_count = int(e_result.get("task_count", 0) or 0)
    raw_policy = e_result.get("raw_material_policy") if isinstance(e_result.get("raw_material_policy"), Mapping) else {}

    append_if(e_config.get("status") != "frozen_target_size", blockers, "e_config_status_not_frozen_target_size")
    append_if(e_config.get("freeze_allowed") is not True, blockers, "e_config_freeze_not_allowed")
    append_if(e_result.get("status") != "frozen_target_size", blockers, "e_result_status_not_frozen_target_size")
    append_if(e_result.get("freeze_allowed") is not True, blockers, "e_result_freeze_not_allowed")
    append_if(result_task_count < 30, blockers, "e_result_task_count_below_minimum")
    append_if(len(tasks) != result_task_count, blockers, "e_config_task_count_mismatch")
    append_if(
        any(isinstance(task, Mapping) and task.get("smoke_status") != "gold_resolved" for task in tasks),
        blockers,
        "e_config_contains_non_resolved_task",
    )
    append_if(
        any(isinstance(task, Mapping) and task.get("smoke_status") != "gold_resolved" for task in task_table),
        blockers,
        "e_result_contains_non_resolved_task",
    )
    for key in (
        "raw_problem_statements_emitted",
        "raw_patches_emitted",
        "raw_test_patches_emitted",
        "raw_base_commits_emitted",
    ):
        append_if(raw_policy.get(key) is not False, blockers, f"e_raw_policy_{key}_not_false")
    if result_task_count > 48:
        warnings.append("e_result_task_count_exceeds_planned_target_size")
    return {
        "status": "pass" if not blockers else "fail",
        "task_count": result_task_count,
        "blockers": blockers,
        "warnings": warnings,
    }


def audit_b_split(
    manifest: Mapping[str, Any],
    *,
    expected_status: str,
    expected_count: int,
    label: str,
) -> dict[str, Any]:
    blockers: list[str] = []
    tasks = task_list(manifest)
    declared_count = int(manifest.get("task_count", 0) or 0)
    reference_rate = true_rate(tasks, "reference_patch_passes")
    noop_rate = true_rate(tasks, "no_op_fails")
    append_if(manifest.get("status") != expected_status, blockers, f"{label}_status_mismatch")
    append_if(declared_count != expected_count, blockers, f"{label}_declared_count_mismatch")
    append_if(len(tasks) != expected_count, blockers, f"{label}_task_count_mismatch")
    append_if(reference_rate != 1.0, blockers, f"{label}_reference_patch_pass_rate_below_1")
    append_if(noop_rate != 1.0, blockers, f"{label}_noop_fail_rate_below_1")
    return {
        "status": "pass" if not blockers else "fail",
        "declared_task_count": declared_count,
        "task_count": len(tasks),
        "reference_patch_pass_rate": reference_rate,
        "noop_fail_rate": noop_rate,
        "blockers": blockers,
    }


def audit_b_freeze(
    primary: Mapping[str, Any],
    reserve: Mapping[str, Any],
    summary: Mapping[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    candidate_count = int(summary.get("candidate_count", 0) or 0)
    accepted_count = int(summary.get("accepted_count", 0) or 0)
    primary_count = int(summary.get("primary_task_count", 0) or 0)
    reserve_count = int(summary.get("reserve_task_count", 0) or 0)
    reference_rate = summary.get("reference_patch_pass_rate")
    noop_rate = summary.get("noop_fail_rate")
    primary_audit = audit_b_split(
        primary,
        expected_status="admitted_frozen",
        expected_count=primary_count,
        label="primary",
    )
    reserve_audit = audit_b_split(
        reserve,
        expected_status="reserve_admitted_frozen",
        expected_count=reserve_count,
        label="reserve",
    )
    blockers.extend(primary_audit["blockers"])
    blockers.extend(reserve_audit["blockers"])

    append_if(candidate_count < 40, blockers, "b_candidate_count_below_40")
    append_if(accepted_count < candidate_count, blockers, "b_accepted_count_below_generated_candidate_count")
    append_if(primary_count < 20, blockers, "b_summary_primary_count_below_20")
    append_if(reserve_count < 1, warnings, "b_summary_has_no_reserve_tasks")
    append_if(not isinstance(reference_rate, (int, float)) or reference_rate < 0.9, blockers, "b_reference_patch_pass_rate_below_90_percent")
    if not isinstance(noop_rate, (int, float)):
        blockers.append("b_noop_fail_rate_missing")
    elif noop_rate < 0.9:
        blockers.append("b_noop_fail_rate_below_90_percent")

    return {
        "status": "pass" if not blockers else "fail",
        "candidate_count": candidate_count,
        "accepted_count": accepted_count,
        "primary_task_count": primary_count,
        "reserve_task_count": reserve_count,
        "reference_patch_pass_rate": reference_rate,
        "noop_fail_rate": noop_rate,
        "primary": primary_audit,
        "reserve": reserve_audit,
        "blockers": blockers,
        "warnings": warnings,
    }


def iter_string_values(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, Mapping):
        for key, child in value.items():
            yield from iter_string_values(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_string_values(child, f"{path}[{index}]")


def raw_value_findings(named_payloads: Mapping[str, Mapping[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for artifact, payload in named_payloads.items():
        for path, value in iter_string_values(payload):
            for fragment in RAW_VALUE_FRAGMENTS:
                if fragment in value:
                    findings.append({"artifact": artifact, "path": path, "fragment": fragment})
    return findings


def scan_raw_artifact_paths(roots: Sequence[Path]) -> list[str]:
    findings: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and RAW_ARTIFACT_NAME_RE.search(path.name):
                findings.append(repo_relative(path))
    return sorted(findings)


def git_ignored(path: Path) -> bool:
    completed = git("check-ignore", "-q", str(path), cwd=REPO_ROOT)
    return completed.returncode == 0


def audit_protocol(protocol: Mapping[str, Any], repo_payload: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    not_authorized = protocol.get("not_authorized_until_next_gate")
    if not isinstance(not_authorized, list):
        blockers.append("protocol_missing_not_authorized_until_next_gate")
    else:
        for item in ("run_ACUT_on_E", "run_ACUT_on_B", "use_E_gold_or_hidden_material_in_B_generation"):
            append_if(item not in not_authorized, blockers, f"protocol_missing_block_{item}")
    status = str(protocol.get("status", ""))
    append_if("e_and_b_primary_frozen" not in status, blockers, "protocol_status_not_e_and_b_frozen")
    append_if(
        repo_payload.get("status") not in {
            "external_and_b_primary_frozen",
            "external_and_b_primary_frozen_candidate_noop_gate_weak",
        },
        blockers,
        "repository_admission_status_mismatch",
    )
    return {"status": "pass" if not blockers else "fail", "blockers": blockers, "warnings": warnings}


def build_payload(
    *,
    protocol: Mapping[str, Any],
    repository_admission: Mapping[str, Any],
    e_config: Mapping[str, Any],
    e_result: Mapping[str, Any],
    b_primary: Mapping[str, Any],
    b_reserve: Mapping[str, Any],
    b_summary: Mapping[str, Any],
    public_raw_artifact_paths: Sequence[str],
    ignored_private_paths: Mapping[str, bool],
) -> dict[str, Any]:
    protocol_audit = audit_protocol(protocol, repository_admission)
    e_audit = audit_e_freeze(e_config, e_result)
    b_audit = audit_b_freeze(b_primary, b_reserve, b_summary)
    raw_value_leaks = raw_value_findings(
        {
            "e_config": e_config,
            "e_result": e_result,
            "b_primary": b_primary,
            "b_reserve": b_reserve,
            "b_summary": b_summary,
        }
    )
    redaction_blockers: list[str] = []
    append_if(bool(public_raw_artifact_paths), redaction_blockers, "public_raw_artifact_files_present")
    append_if(bool(raw_value_leaks), redaction_blockers, "public_manifest_raw_value_leaks_present")
    for label, ignored in ignored_private_paths.items():
        append_if(not ignored, redaction_blockers, f"private_path_not_gitignored:{label}")

    blockers = (
        protocol_audit["blockers"]
        + e_audit["blockers"]
        + b_audit["blockers"]
        + redaction_blockers
    )
    warnings = protocol_audit["warnings"] + e_audit["warnings"] + b_audit["warnings"]
    candidate_noop_weak = (
        "b_evaluated_candidate_noop_fail_rate_below_90_percent" in warnings
        or "b_noop_fail_rate_below_90_percent" in blockers
    )
    freeze_integrity_passed = not blockers
    acut_authorized = freeze_integrity_passed and not candidate_noop_weak
    status = (
        "failed"
        if blockers
        else "passed"
        if acut_authorized
        else "passed_acut_blocked_candidate_noop_gate_weak"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "protocol_id": PROTOCOL_ID,
        "generated_at": iso_now(),
        "model_calls_made": 0,
        "status": status,
        "freeze_integrity_passed": freeze_integrity_passed,
        "acut_authorized": acut_authorized,
        "candidate_noop_gate_weak": candidate_noop_weak,
        "blockers": blockers,
        "warnings": warnings,
        "protocol_audit": protocol_audit,
        "e_audit": e_audit,
        "b_audit": b_audit,
        "redaction_audit": {
            "status": "pass" if not redaction_blockers else "fail",
            "public_raw_artifact_paths": list(public_raw_artifact_paths),
            "raw_value_leaks": raw_value_leaks,
            "ignored_private_paths": dict(ignored_private_paths),
            "blockers": redaction_blockers,
        },
        "next_required_steps": [
            "Resolve or explicitly accept the evaluated-candidate no-op fail-rate weakness before primary ACUT runs.",
            "Freeze ACUT profiles and execution manifests after the no-op gate decision.",
        ]
        if candidate_noop_weak
        else [
            "Freeze ACUT profiles and execution manifests.",
            "Run one primary ACUT attempt per frozen task with network disabled.",
        ],
    }


def render_report(payload: Mapping[str, Any]) -> str:
    b_audit = payload.get("b_audit") if isinstance(payload.get("b_audit"), Mapping) else {}
    e_audit = payload.get("e_audit") if isinstance(payload.get("e_audit"), Mapping) else {}
    redaction = payload.get("redaction_audit") if isinstance(payload.get("redaction_audit"), Mapping) else {}
    acut_authorized = payload.get("acut_authorized") is True
    boundary = (
        "This audit clears the E/B freeze integrity gate. ACUT execution still requires frozen ACUT profiles and execution manifests under the protocol."
        if acut_authorized
        else "This audit does not authorize ACUT execution while `acut_authorized` is false. Resolve the reported blockers before primary execution."
    )
    lines = [
        "# External Freeze Integrity Audit",
        "",
        f"Protocol: `{payload.get('protocol_id')}`",
        f"Status: `{payload.get('status')}`",
        f"Generated at: `{payload.get('generated_at')}`",
        f"Freeze integrity passed: `{payload.get('freeze_integrity_passed')}`",
        f"ACUT authorized: `{payload.get('acut_authorized')}`",
        "",
        "## E Freeze",
        "",
        f"- Status: `{e_audit.get('status')}`",
        f"- Task count: `{e_audit.get('task_count')}`",
        f"- Blockers: `{e_audit.get('blockers')}`",
        "",
        "## B Freeze",
        "",
        f"- Status: `{b_audit.get('status')}`",
        f"- Candidates/accepted/primary/reserve: `{b_audit.get('candidate_count')}` / `{b_audit.get('accepted_count')}` / `{b_audit.get('primary_task_count')}` / `{b_audit.get('reserve_task_count')}`",
        f"- Evaluated candidate reference/no-op rates: `{b_audit.get('reference_patch_pass_rate')}` / `{b_audit.get('noop_fail_rate')}`",
        f"- Warnings: `{b_audit.get('warnings')}`",
        "",
        "## Redaction",
        "",
        f"- Status: `{redaction.get('status')}`",
        f"- Public raw artifact files: `{redaction.get('public_raw_artifact_paths')}`",
        f"- Raw value leaks: `{redaction.get('raw_value_leaks')}`",
        "",
        "## Boundary",
        "",
        boundary,
        "",
    ]
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    protocol = load_manifest(args.protocol)
    repository_admission = load_manifest(args.repository_admission)
    e_config = load_manifest(args.e_config)
    e_result = load_manifest(args.e_result)
    b_primary = load_manifest(args.b_primary)
    b_reserve = load_manifest(args.b_reserve)
    b_summary = load_manifest(args.b_summary)
    private_paths = {
        "b_private_artifact_root": Path(str(b_summary.get("private_artifact_root", ""))),
        "b_workspace_root": Path(str(b_summary.get("workspace_root", ""))),
    }
    ignored_private_paths = {
        label: git_ignored((REPO_ROOT / path) if not path.is_absolute() else path)
        for label, path in private_paths.items()
        if str(path)
    }
    payload = build_payload(
        protocol=protocol,
        repository_admission=repository_admission,
        e_config=e_config,
        e_result=e_result,
        b_primary=b_primary,
        b_reserve=b_reserve,
        b_summary=b_summary,
        public_raw_artifact_paths=scan_raw_artifact_paths(PUBLIC_RAW_ARTIFACT_ROOTS),
        ignored_private_paths=ignored_private_paths,
    )
    output = Path(args.output)
    report = Path(args.report)
    write_json(output, payload)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(payload), encoding="utf-8")
    emit_json({**payload, "output_path": repo_relative(output), "report_path": repo_relative(report)})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
