#!/usr/bin/env python3
"""Freeze the external SymPy SWE-bench task slice after a redacted gold smoke."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import external_calibrated_repository_admission as admission
import external_calibrated_swebench_smoke as smoke
from _common import ToolError, emit_json, fail, iso_now, write_json


TOOL = "external_calibrated_e_freeze"
SCHEMA_VERSION = "external-calibrated-repo-benchmark.e-freeze.v1"
PROTOCOL_ID = admission.PROTOCOL_ID
REPO_ROOT = admission.REPO_ROOT
DEFAULT_SMOKE = admission.RESULTS_ROOT / "repository_admission/swebench_gold_smoke_summary_20260515.json"
DEFAULT_CONFIG = REPO_ROOT / "experiments/core_narrative/configs/external/swebench_sympy_e_v1.yaml"
DEFAULT_RESULT = REPO_ROOT / "experiments/core_narrative/results/external/e_task_smoke.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/external_e_task_freeze_report.md"
DEFAULT_TARGET_SIZE = 48
DEFAULT_MIN_SIZE = 30


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-summary", default=str(DEFAULT_SMOKE), help="Redacted SWE-bench smoke summary JSON.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Frozen E task slice YAML output.")
    parser.add_argument("--result", default=str(DEFAULT_RESULT), help="Machine-readable E smoke/freeze JSON output.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Markdown E freeze report output.")
    parser.add_argument("--target-size", type=int, default=DEFAULT_TARGET_SIZE, help="Preferred E denominator size.")
    parser.add_argument("--min-size", type=int, default=DEFAULT_MIN_SIZE, help="Minimum E denominator size.")
    return parser.parse_args(list(argv) if argv is not None else None)


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolError("failed to load JSON artifact", path=admission.repo_relative(path), cause=str(exc)) from exc
    if not isinstance(payload, dict):
        raise ToolError("JSON artifact root must be an object", path=admission.repo_relative(path))
    return payload


def freeze_decision(smoke_summary: Mapping[str, Any], *, target_size: int, min_size: int) -> dict[str, Any]:
    resolved_count = int(smoke_summary.get("resolved_instances", 0) or 0)
    completed_count = int(smoke_summary.get("completed_instances", 0) or 0)
    requested_count = int(smoke_summary.get("total_instances_requested", 0) or 0)
    error_count = int(smoke_summary.get("error_instances", 0) or 0)
    pass_flag = smoke_summary.get("pass") is True
    blockers: list[str] = []
    if not pass_flag:
        blockers.append("gold_smoke_not_passing")
    if resolved_count < min_size:
        blockers.append("resolved_external_task_count_below_min_size")
    if requested_count < min_size:
        blockers.append("requested_external_task_count_below_min_size")
    if error_count:
        blockers.append("gold_smoke_has_error_instances")
    status = "frozen_target_size" if pass_flag and resolved_count >= target_size and not blockers else "not_frozen"
    if status != "frozen_target_size" and pass_flag and resolved_count >= min_size and not error_count:
        status = "frozen_reduced_min_size"
    return {
        "status": status,
        "freeze_allowed": status in {"frozen_target_size", "frozen_reduced_min_size"},
        "target_size": target_size,
        "min_size": min_size,
        "requested_count": requested_count,
        "completed_count": completed_count,
        "resolved_count": resolved_count,
        "error_count": error_count,
        "blockers": blockers,
    }


def row_by_instance_id(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row.get("instance_id")): row for row in rows if row.get("instance_id")}


def e_task_table(
    rows: Sequence[Mapping[str, Any]],
    smoke_summary: Mapping[str, Any],
    *,
    repo_id: str,
) -> list[dict[str, Any]]:
    by_id = row_by_instance_id(rows)
    completed = set(smoke.report_id_list(smoke_summary, "completed_ids"))
    resolved = set(smoke.report_id_list(smoke_summary, "resolved_ids"))
    unresolved = set(smoke.report_id_list(smoke_summary, "unresolved_ids"))
    errors = set(smoke.report_id_list(smoke_summary, "error_ids"))
    empty = set(smoke.report_id_list(smoke_summary, "empty_patch_ids"))
    tasks: list[dict[str, Any]] = []
    for instance_id in smoke_summary.get("instance_ids", []):
        if not isinstance(instance_id, str):
            continue
        row = by_id.get(instance_id, {})
        if instance_id in errors:
            status = "infra_or_harness_error"
        elif instance_id in empty:
            status = "empty_gold_patch"
        elif instance_id in unresolved:
            status = "gold_unresolved"
        elif instance_id in resolved:
            status = "gold_resolved"
        elif instance_id in completed:
            status = "completed_without_resolved_status"
        else:
            status = "not_completed"
        problem = str(row.get("problem_statement", ""))
        base_commit = str(row.get("base_commit", ""))
        tasks.append(
            {
                "external_task_id": instance_id,
                "repo": repo_id,
                "benchmark_source": smoke_summary.get("benchmark_source"),
                "split": smoke_summary.get("split"),
                "instance_id": instance_id,
                "instance_id_digest": admission.digest_parts(repo_id, instance_id),
                "base_commit_digest": admission.digest_parts(repo_id, base_commit) if base_commit else None,
                "problem_statement_digest": admission.sha256_text(problem) if problem else None,
                "family_if_available": admission.external_family(repo_id, row) if row else None,
                "smoke_status": status,
                "exclusion_reason": None if status == "gold_resolved" else status,
            }
        )
    return tasks


def build_payload(smoke_summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], *, target_size: int, min_size: int) -> dict[str, Any]:
    repo_id = str(smoke_summary.get("repo") or "sympy/sympy")
    decision = freeze_decision(smoke_summary, target_size=target_size, min_size=min_size)
    tasks = e_task_table(rows, smoke_summary, repo_id=repo_id)
    included = [task for task in tasks if task.get("smoke_status") == "gold_resolved"]
    families = Counter(str(task.get("family_if_available")) for task in included if task.get("family_if_available"))
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "protocol_id": PROTOCOL_ID,
        "generated_at": iso_now(),
        "model_calls_made": 0,
        "status": decision["status"],
        "freeze_allowed": decision["freeze_allowed"],
        "external_anchor": {
            "dataset": smoke_summary.get("benchmark_source"),
            "split": smoke_summary.get("split"),
            "repo": repo_id,
            "dataset_metadata": smoke_summary.get("dataset_metadata"),
            "selection_rule": smoke_summary.get("selection_rule"),
            "smoke_id": smoke_summary.get("smoke_id"),
        },
        "gate": decision,
        "task_count": len(included),
        "task_ids": [str(task["instance_id"]) for task in included],
        "family_counts": dict(sorted(families.items())),
        "task_table": tasks,
        "raw_material_policy": {
            "raw_problem_statements_emitted": False,
            "raw_patches_emitted": False,
            "raw_test_patches_emitted": False,
            "raw_base_commits_emitted": False,
            "note": "The plan's base_commit field is represented by base_commit_digest to avoid leaking E anchors into B-generation context.",
        },
        "next_required_steps": [
            "Only proceed to B generation after this artifact is frozen and before any E ACUT result is inspected.",
            "Generate and smoke B candidate tasks with no-op fail and reference-patch pass evidence.",
        ],
    }


def yaml_quote(value: Any) -> str:
    if value is None:
        return "null"
    text = str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_config(payload: Mapping[str, Any]) -> str:
    anchor = payload.get("external_anchor") if isinstance(payload.get("external_anchor"), Mapping) else {}
    gate = payload.get("gate") if isinstance(payload.get("gate"), Mapping) else {}
    lines = [
        "schema_version: external-calibrated-repo-benchmark.e-slice.v1",
        f"protocol_id: {yaml_quote(payload.get('protocol_id'))}",
        f"status: {yaml_quote(payload.get('status'))}",
        f"frozen_at: {yaml_quote(payload.get('generated_at'))}",
        f"freeze_allowed: {str(bool(payload.get('freeze_allowed'))).lower()}",
        "external_anchor:",
        f"  dataset: {yaml_quote(anchor.get('dataset'))}",
        f"  split: {yaml_quote(anchor.get('split'))}",
        f"  repo: {yaml_quote(anchor.get('repo'))}",
        f"  smoke_id: {yaml_quote(anchor.get('smoke_id'))}",
        "gate:",
        f"  target_size: {gate.get('target_size')}",
        f"  min_size: {gate.get('min_size')}",
        f"  requested_count: {gate.get('requested_count')}",
        f"  resolved_count: {gate.get('resolved_count')}",
        f"  error_count: {gate.get('error_count')}",
        "task_selection:",
        "  source: deterministic redacted SWE-bench gold smoke",
        "  replacement_after_freeze: false",
        "  selected_using_acut_outputs: false",
        "  selected_using_e_results: false",
        "raw_material_policy:",
        "  raw_problem_statements_emitted: false",
        "  raw_patches_emitted: false",
        "  raw_test_patches_emitted: false",
        "  raw_base_commits_emitted: false",
        "tasks:",
    ]
    for index, task in enumerate(payload.get("task_table", []), start=1):
        if not isinstance(task, Mapping):
            continue
        lines.extend(
            [
                f"  - ordinal: {index}",
                f"    instance_id: {yaml_quote(task.get('instance_id'))}",
                f"    instance_id_digest: {yaml_quote(task.get('instance_id_digest'))}",
                f"    base_commit_digest: {yaml_quote(task.get('base_commit_digest'))}",
                f"    problem_statement_digest: {yaml_quote(task.get('problem_statement_digest'))}",
                f"    family_if_available: {yaml_quote(task.get('family_if_available'))}",
                f"    smoke_status: {yaml_quote(task.get('smoke_status'))}",
                f"    exclusion_reason: {yaml_quote(task.get('exclusion_reason'))}",
            ]
        )
    return "\n".join(lines) + "\n"


def render_report(payload: Mapping[str, Any]) -> str:
    anchor = payload.get("external_anchor") if isinstance(payload.get("external_anchor"), Mapping) else {}
    gate = payload.get("gate") if isinstance(payload.get("gate"), Mapping) else {}
    lines = [
        "# External E Task Freeze",
        "",
        f"Protocol: `{payload.get('protocol_id')}`",
        f"Status: `{payload.get('status')}`",
        f"Generated at: `{payload.get('generated_at')}`",
        "",
        "## Anchor",
        "",
        f"- Dataset: `{anchor.get('dataset')}` / `{anchor.get('split')}`",
        f"- Repository: `{anchor.get('repo')}`",
        f"- Smoke id: `{anchor.get('smoke_id')}`",
        "",
        "## Gate",
        "",
        f"- Target/min size: `{gate.get('target_size')}` / `{gate.get('min_size')}`",
        f"- Requested/completed/resolved/errors: `{gate.get('requested_count')}` / `{gate.get('completed_count')}` / `{gate.get('resolved_count')}` / `{gate.get('error_count')}`",
        f"- Freeze allowed: `{payload.get('freeze_allowed')}`",
        f"- Blockers: `{gate.get('blockers')}`",
        "",
        "## Family Sketch",
        "",
    ]
    families = payload.get("family_counts") if isinstance(payload.get("family_counts"), Mapping) else {}
    for family, count in families.items():
        lines.append(f"- `{family}`: `{count}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This artifact records instance ids and digests only. It does not emit raw SWE-bench problem statements, gold patches, test patches, or base commits.",
            "",
        ]
    )
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    smoke_summary = load_json_object(Path(args.smoke_summary))
    rows = smoke.load_dataset_rows(str(smoke_summary.get("benchmark_source")), split=str(smoke_summary.get("split")))
    payload = build_payload(smoke_summary, rows, target_size=args.target_size, min_size=args.min_size)
    write_json(Path(args.result), payload)
    config_path = Path(args.config)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(render_config(payload), encoding="utf-8")
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(payload), encoding="utf-8")
    emit_json(
        {
            **payload,
            "config_path": admission.repo_relative(config_path),
            "result_path": admission.repo_relative(Path(args.result)),
            "report_path": admission.repo_relative(report_path),
        }
    )
    return 0 if payload["freeze_allowed"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
