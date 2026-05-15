#!/usr/bin/env python3
"""Preregister and audit the reduced Rich-W20 repository-local protocol."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from _common import ToolError, emit_json, iso_now, load_manifest, write_json


TOOL = "repository_local_rich_w20_protocol_readiness"
SCHEMA_VERSION = "core-narrative.repository-local-rich-w20-readiness.v1"
PROTOCOL_ID = "repository-local-rich-w20-v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
RESULTS_ROOT = REPO_ROOT / "experiments/core_narrative/results"
DEFAULT_OUTPUT = RESULTS_ROOT / "repository_local_rich_w20_protocol_readiness_20260515.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-15_repository_local_rich_w20_protocol_readiness.md"

W_DIRECT = (RESULTS_ROOT / "rich_direct_smoke_batch_20260514.json",)
W_SOURCE_GLOB = "rich_source_oracle_pilot*_20260514.json"
W_REPLACEMENT = (
    RESULTS_ROOT / "rich_replacement_oracle_pilot_20260514.json",
    RESULTS_ROOT / "rich_replacement_oracle_pilot_zerospan_20260514.json",
    RESULTS_ROOT / "rich_replacement_oracle_pilot_vs16_20260514.json",
)
W_DIRECT_WITHOUT_NODES = (RESULTS_ROOT / "rich_direct_without_nodes_oracle_pilot_20260514.json",)
R_DIRECT = (RESULTS_ROOT / "rich_r_direct_smoke_batch_20260515.json",)
R_SOURCE_GLOB = "rich_r_source_oracle_pilot*_20260515.json"
ACUTS = (
    ("A0", "generic_baseline", "cheap-generic-swe"),
    ("A1", "same_token_inert_control", "cheap-rich-inert-control-v1"),
    ("A3", "repository_calibrated_playbook", "cheap-rich-c-calibrated-v1"),
    ("A4", "code_understanding_localization", "cheap-rich-localization-tool-v1"),
)
FORBIDDEN_PUBLIC_KEYS = {
    "base_commit",
    "target_commit",
    "commit",
    "subject",
    "raw_subject",
    "reference_patch",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    return parser.parse_args(list(argv) if argv is not None else None)


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ToolError("required Rich evidence artifact is missing", path=repo_relative(path)) from exc
    except json.JSONDecodeError as exc:
        raise ToolError("required Rich evidence artifact is not valid JSON", path=repo_relative(path)) from exc
    if not isinstance(payload, dict):
        raise ToolError("required Rich evidence artifact has unexpected shape", path=repo_relative(path))
    return payload


def private_task_pack_path(private_artifact_root: object) -> Path | None:
    if not isinstance(private_artifact_root, str) or not private_artifact_root:
        return None
    path = REPO_ROOT / private_artifact_root / "candidate_task_pack/task.json"
    return path if path.exists() else None


def private_task_pack_summary(private_artifact_root: object) -> dict[str, Any]:
    path = private_task_pack_path(private_artifact_root)
    if path is None:
        return {
            "task_pack_present": False,
            "task_pack_path": None,
            "task_pack_task_id": None,
            "leakage_reviewed": False,
            "expected_no_op_fails": None,
            "expected_reference_passes": None,
        }
    task = load_json(path)
    leakage = task.get("leakage") if isinstance(task.get("leakage"), Mapping) else {}
    expected = task.get("expected") if isinstance(task.get("expected"), Mapping) else {}
    return {
        "task_pack_present": True,
        "task_pack_path": repo_relative(path),
        "task_pack_task_id": task.get("task_id") if isinstance(task.get("task_id"), str) else None,
        "leakage_reviewed": leakage.get("reviewed") is True,
        "expected_no_op_fails": expected.get("no_op_fails") is True,
        "expected_reference_passes": expected.get("reference_passes") is True,
    }


def public_records(path: Path) -> list[Mapping[str, Any]]:
    payload = load_json(path)
    records = payload.get("results")
    if isinstance(records, list):
        return [record for record in records if isinstance(record, Mapping)]
    return [payload]


def accepted_from_artifacts(paths: Iterable[Path]) -> list[tuple[Path, Mapping[str, Any]]]:
    accepted: list[tuple[Path, Mapping[str, Any]]] = []
    for path in paths:
        for record in public_records(path):
            if record.get("admission_decision") == "accepted":
                accepted.append((path, record))
    return accepted


def no_op_passed_admission(record: Mapping[str, Any]) -> bool:
    result = record.get("no_op_result") if isinstance(record.get("no_op_result"), Mapping) else {}
    return result.get("status") == "failed" and result.get("verifier_exit_code") == 1


def reference_passed_admission(record: Mapping[str, Any]) -> bool:
    result = record.get("reference_result") if isinstance(record.get("reference_result"), Mapping) else {}
    return result.get("status") == "passed" and result.get("verifier_exit_code") == 0


def redacted_task_record(
    *,
    split: str,
    slot: int,
    source_path: Path,
    record: Mapping[str, Any],
) -> dict[str, Any]:
    private_summary = private_task_pack_summary(record.get("private_artifact_root"))
    item = {
        "protocol_task_id": f"rich__{split.lower()}__{slot:03d}",
        "split": split,
        "source_artifact": repo_relative(source_path),
        "source_record_index": record.get("batch_candidate_index"),
        "admission_decision": record.get("admission_decision"),
        "surface": record.get("surface"),
        "family": record.get("family"),
        "tool": record.get("tool"),
        "statement_digest": record.get("statement_digest"),
        "subject_digest": record.get("subject_digest"),
        "hidden_verifier_digest": record.get("hidden_verifier_digest"),
        "reference_patch_digest": record.get("reference_patch_digest"),
        "changed_file_set_digest": record.get("changed_file_set_digest"),
        "source_anchor_digest": record.get("source_anchor_digest"),
        "no_op_status": (record.get("no_op_result") or {}).get("status")
        if isinstance(record.get("no_op_result"), Mapping)
        else None,
        "no_op_exit_code": (record.get("no_op_result") or {}).get("verifier_exit_code")
        if isinstance(record.get("no_op_result"), Mapping)
        else None,
        "reference_status": (record.get("reference_result") or {}).get("status")
        if isinstance(record.get("reference_result"), Mapping)
        else None,
        "reference_exit_code": (record.get("reference_result") or {}).get("verifier_exit_code")
        if isinstance(record.get("reference_result"), Mapping)
        else None,
        "private_artifact_root": record.get("private_artifact_root"),
        **private_summary,
        "pre_primary_checks": {
            "no_op_fails": no_op_passed_admission(record),
            "reference_passes": reference_passed_admission(record),
            "hidden_verifier_digest_recorded": isinstance(record.get("hidden_verifier_digest"), str),
            "statement_digest_recorded": isinstance(record.get("statement_digest"), str),
            "public_statement_digest_recorded": isinstance(record.get("statement_digest"), str),
            "leakage_reviewed": private_summary["leakage_reviewed"],
        },
    }
    assert_no_forbidden_public_keys(item)
    return item


def assert_no_forbidden_public_keys(value: object, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in FORBIDDEN_PUBLIC_KEYS:
                raise ToolError("readiness artifact would expose a forbidden raw field", path=f"{path}.{key}")
            assert_no_forbidden_public_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_no_forbidden_public_keys(item, f"{path}[{index}]")


def ordered_w_star_records() -> list[dict[str, Any]]:
    paths = [*W_DIRECT, *sorted(RESULTS_ROOT.glob(W_SOURCE_GLOB)), *W_REPLACEMENT, *W_DIRECT_WITHOUT_NODES]
    accepted = accepted_from_artifacts(paths)
    return [
        redacted_task_record(split="W_star", slot=index, source_path=path, record=record)
        for index, (path, record) in enumerate(accepted, start=1)
    ]


def ordered_r_records() -> list[dict[str, Any]]:
    paths = [*R_DIRECT, *sorted(RESULTS_ROOT.glob(R_SOURCE_GLOB))]
    accepted = accepted_from_artifacts(paths)
    return [
        redacted_task_record(split="R", slot=index, source_path=path, record=record)
        for index, (path, record) in enumerate(accepted, start=1)
    ]


def all_primary_checks_pass(records: Sequence[Mapping[str, Any]]) -> bool:
    for record in records:
        checks = record.get("pre_primary_checks") if isinstance(record.get("pre_primary_checks"), Mapping) else {}
        if not all(checks.get(key) is True for key in ("no_op_fails", "reference_passes", "hidden_verifier_digest_recorded", "statement_digest_recorded", "leakage_reviewed")):
            return False
    return True


def acut_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for slot, role, acut_id in ACUTS:
        path = REPO_ROOT / "experiments/core_narrative/configs/acuts" / f"{acut_id}.yaml"
        manifest = load_manifest(path)
        model = manifest.get("model")
        if not isinstance(model, str) or model.startswith("openai/") or model == "gpt-5.5":
            raise ToolError("ACUT model route is not compatible with the 2026-05-15 endpoint switch", acut_id=acut_id, model=model)
        rows.append(
            {
                "slot": slot,
                "role": role,
                "acut_id": acut_id,
                "manifest": repo_relative(path),
                "model": model,
                "provider": manifest.get("provider"),
            }
        )
    return rows


def build_payload() -> dict[str, Any]:
    w_records = ordered_w_star_records()
    r_records = ordered_r_records()
    if len(w_records) != 20:
        raise ToolError("Rich-W20 requires exactly 20 W* primary tasks", observed=len(w_records))
    if len(r_records) < 20:
        raise ToolError("Rich-W20 requires at least 20 R tasks", observed=len(r_records))
    r_primary = r_records[:20]
    r_reserve = r_records[20:]
    primary_records = [*w_records, *r_primary]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "protocol_id": PROTOCOL_ID,
        "generated_at": iso_now(),
        "status": "preregistered_reduced_protocol_primary_not_run",
        "parent_protocol": "repository-local-benchmark-20260514",
        "original_0514_status": "completed_blocked_before_primary_runs_under_frozen_protocol",
        "original_0514_blocker": {
            "decision": "w_star_primary_reached_but_reserve_and_pool_gates_failed",
            "accepted_w_star_primary": 20,
            "target_primary_plus_reserve": 25,
            "maximum_possible_w_star_admissions_under_current_scan": 23,
            "reserve_gap": 2,
            "candidate_pool_gap": 17,
        },
        "revision_boundary": {
            "type": "preregistered_reduced_scale_decision_validity_pilot",
            "does_not_satisfy_original_reserve_gate": True,
            "does_not_satisfy_original_40_candidate_pool_gate": True,
            "does_not_rewrite_0514_terminal_block": True,
        },
        "repository": {"repo_slug": "rich"},
        "model_route_policy": {
            "provider_prefix_removed": True,
            "active_cheap_route": "gpt-5.4-mini",
            "active_frontier_route": "gpt-5.4",
            "unavailable_models": ["gpt-5.5"],
        },
        "runner_concurrency_requirement": {
            "required_min_workers": 4,
            "implemented_default_max_workers": 4,
            "runners": [
                "experiments/core_narrative/tools/codex_nfl_workspace_runner.py",
                "experiments/core_narrative/tools/codex_nfl_experiment_runner.py",
            ],
            "cli_flag": "--max-workers",
            "diagnostic_field": "concurrency.max_workers",
            "result_order": "input_cell_order",
            "status": "satisfied_for_batch_runners",
        },
        "denominators": {
            "W_star": {
                "target_primary_tasks": 20,
                "primary_task_count": len(w_records),
                "reserve_required": False,
                "candidate_pool_required": False,
                "primary_tasks": w_records,
            },
            "R": {
                "target_primary_tasks": 20,
                "accepted_task_count": len(r_records),
                "primary_task_count": len(r_primary),
                "reserve_task_count": len(r_reserve),
                "primary_tasks": r_primary,
                "reserve_tasks": r_reserve,
            },
        },
        "acuts": acut_rows(),
        "run_controls": {
            "primary_attempts_per_acut_task": 1,
            "best_of_n": False,
            "acut_specific_retry": False,
            "fresh_workspace_replay": True,
            "hidden_verifier": True,
            "deterministic_run_order": "W_star then R records in readiness order; ACUT order A0,A1,A3,A4",
            "status_mapping": "workspace-mode fixed denominator semantics",
        },
        "pre_primary_checks": {
            "primary_task_count": len(primary_records),
            "no_op_fails_all_primary_tasks": all(
                record["pre_primary_checks"]["no_op_fails"] for record in primary_records
            ),
            "reference_passes_all_primary_tasks": all(
                record["pre_primary_checks"]["reference_passes"] for record in primary_records
            ),
            "hidden_verifier_digest_recorded_all_primary_tasks": all(
                record["pre_primary_checks"]["hidden_verifier_digest_recorded"] for record in primary_records
            ),
            "public_statement_digest_recorded_all_primary_tasks": all(
                record["pre_primary_checks"]["public_statement_digest_recorded"] for record in primary_records
            ),
            "leakage_reviewed_all_primary_tasks": all(
                record["pre_primary_checks"]["leakage_reviewed"] for record in primary_records
            ),
            "all_primary_checks_pass": all_primary_checks_pass(primary_records),
        },
        "success_criteria": {
            "A4_vs_A0_w_star_min_delta_tasks": 4,
            "r_selected_vs_A0_w_star_min_delta_tasks": 3,
            "r_selected_within_tasks_of_w_star_best": [1, 2],
            "inert_control_guard": "A1 must not be selected as winner unless W* also supports it.",
        },
        "analysis_plan": [
            "Compute R_score and W_star_score per ACUT.",
            "Compute paired deltas against A0.",
            "Run inert control check.",
            "Identify R-selected ACUT, W*-best ACUT, and selection regret.",
            "Report family-level score and failure breakdown.",
        ],
        "primary_runs_authorized": False,
        "remaining_before_primary_attempts": [
            "Record reduced-protocol owner start decision.",
            "Run live API/cost-ledger preflight under bare model routes.",
            "Execute primary attempts; this readiness artifact contains no ACUT primary result.",
        ],
        "privacy": {
            "commit_values_recorded": False,
            "subject_text_recorded": False,
            "reference_patches_recorded": False,
            "private_artifact_roots_recorded": True,
            "public_records_are_digest_only": True,
        },
    }
    assert_no_forbidden_public_keys(payload)
    return payload


def report_markdown(payload: Mapping[str, Any]) -> str:
    w = payload["denominators"]["W_star"]  # type: ignore[index]
    r = payload["denominators"]["R"]  # type: ignore[index]
    checks = payload["pre_primary_checks"]  # type: ignore[index]
    return "\n".join(
        [
            "# Repository-Local Rich-W20 Protocol Readiness",
            "",
            f"Status: `{payload['status']}`",
            f"Protocol: `{payload['protocol_id']}`",
            "",
            "## Boundary",
            "",
            "The 0514 frozen protocol remains terminally blocked before primary runs. This artifact preregisters a reduced-scale Rich-W20 decision-validity pilot; it does not claim to satisfy the original 5-reserve or 40-candidate-pool gates.",
            "",
            "## Denominators",
            "",
            f"- W*: `{w['primary_task_count']}` primary tasks; reserve required: `{str(w['reserve_required']).lower()}`.",
            f"- R: `{r['primary_task_count']}` primary tasks; `{r['reserve_task_count']}` accepted reserve tasks retained.",
            "- ACUTs: A0 generic, A1 inert, A3 repository-calibrated, A4 localization.",
            "",
            "## Pre-Primary Checks",
            "",
            f"- No-op fails all primary tasks: `{str(checks['no_op_fails_all_primary_tasks']).lower()}`",
            f"- Reference passes all primary tasks: `{str(checks['reference_passes_all_primary_tasks']).lower()}`",
            f"- Hidden verifier digest recorded: `{str(checks['hidden_verifier_digest_recorded_all_primary_tasks']).lower()}`",
            f"- Public statement digest recorded: `{str(checks['public_statement_digest_recorded_all_primary_tasks']).lower()}`",
            f"- Leakage reviewed: `{str(checks['leakage_reviewed_all_primary_tasks']).lower()}`",
            "",
            "## Current Blockers",
            "",
            "- Primary ACUT attempts are still not run in this artifact.",
            "- A reduced-protocol owner start decision and live API/cost preflight must be recorded before primary attempts.",
            "",
            "## Privacy",
            "",
            "The readiness JSON records digests and private artifact roots only. Raw commits, raw subjects, reference patch bodies, and hidden verifier files remain outside committed public artifacts.",
            "",
        ]
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload()
    output = Path(args.output)
    report = Path(args.report)
    write_json(output, payload)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(report_markdown(payload), encoding="utf-8")
    emit_json(
        {
            "tool": TOOL,
            "status": payload["status"],
            "protocol_id": PROTOCOL_ID,
            "output": repo_relative(output),
            "report": repo_relative(report),
            "w_star_primary_task_count": payload["denominators"]["W_star"]["primary_task_count"],
            "r_primary_task_count": payload["denominators"]["R"]["primary_task_count"],
            "r_reserve_task_count": payload["denominators"]["R"]["reserve_task_count"],
            "primary_runs_authorized": payload["primary_runs_authorized"],
        },
        None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
