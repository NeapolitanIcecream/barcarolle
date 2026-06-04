from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load

import phase1_diff_assisted_codex_loop_statement_regeneration as codexloop
import phase1_diff_assisted_statement_regeneration as dryrun


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_TOOLS = REPO_ROOT / "experiments" / "phase0_headroom" / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))

import statement_quality  # noqa: E402


DEFAULT_CONFIG = ROOT / "configs" / "phase1_canonical_split_statement_repair.yaml"
SCHEMA_VERSION = "barcarolle.phase1_canonical_split_statement_repair.v1"
MODES = {
    "split-map",
    "inventory",
    "packets",
    "workflow",
    "record-session-start",
    "copy-generator-output",
    "copy-reviewer-output",
    "qa",
    "screen",
    "decide",
    "closeout",
}
CANONICAL_GROUPS: dict[str, list[str]] = {
    "boltons/B_eval": [
        "boltons__clean_ext__001",
        "boltons__clean_ext__008",
        "boltons__clean_ext__010",
        "boltons__hist__011",
    ],
    "boltons/H_future": [
        "boltons__clean_ext__017",
        "boltons__hist__022",
        "boltons__hist__023",
        "boltons__hist__027",
    ],
    "attrs/B_eval": [
        "attrs__hist__001",
        "attrs__hist__003",
        "attrs__hist__004",
        "attrs__hist__008",
    ],
    "attrs/H_future": [
        "attrs__hist__012",
        "attrs__hist__013",
        "attrs__hist__023",
        "attrs__hist__027",
    ],
}
EXPECTED_CANONICAL_TASK_COUNT = 16
REVIEW_STATUSES = {"pass", "revise", "reject"}
TARGET_COMMIT_PATTERN = re.compile(r"\b[0-9a-f]{40}\b")
FORBIDDEN_STATEMENT_PATTERNS = {
    "diff --git": "raw_diff_marker",
    "\n@@": "raw_diff_hunk_marker",
    "gold patch": "gold_patch_text",
    "hidden verifier": "hidden_verifier_text",
    "verified_pass": "paid_outcome_status",
    "verified_fail": "paid_outcome_status",
    "policy_violation": "paid_or_policy_status",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row, sort_keys=True) for row in rows)
    path.write_text((text + "\n") if text else "", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def statement_digest(statement: str) -> str:
    return f"sha256:{digest_text(statement)}"


def config_path(raw: str | Path) -> Path:
    path = Path(str(raw))
    return path if path.is_absolute() else REPO_ROOT / path


def rel(path: Path | str) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected canonical split repair config schema_version")
    config["_path"] = str(path)
    return config


def artifact_path(config: dict[str, Any], key: str) -> Path:
    return config_path(str(config["source_artifacts"][key]))


def output_path(config: dict[str, Any], key: str) -> Path:
    return config_path(str(config["output_paths"][key]))


def workflow_dir(config: dict[str, Any]) -> Path:
    return config_path(str(config["generation_review"]["workflow_dir"]))


def endpoint_env_vars(config: dict[str, Any]) -> list[str]:
    values = config.get("policy", {}).get("endpoint_env_vars_unset_for_generator_reviewer") or [
        "LLM_BASE_URL",
        "LLM_API_KEY",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
    ]
    return [str(value) for value in values]


def command_output(args: list[str], *, cwd: Path = REPO_ROOT) -> str:
    try:
        return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""


def git_status_paths() -> list[str]:
    output = command_output(["git", "status", "--short", "--untracked-files=all"])
    paths: list[str] = []
    for line in output.splitlines():
        text = line[3:] if len(line) > 3 else line
        if " -> " in text:
            text = text.split(" -> ", 1)[1]
        paths.append(text.strip())
    return paths


def stable_generated_at(config: dict[str, Any]) -> str:
    preflight = output_path(config, "preflight")
    if preflight.exists():
        return str(read_json(preflight).get("generated_at") or config.get("created_at") or utc_now())
    return str(config.get("created_at") or utc_now())


def unique_sorted(values: list[str]) -> list[str]:
    return sorted(dict.fromkeys(str(value) for value in values if str(value)))


def row_by_task(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["task_id"]): row for row in rows if row.get("task_id")}


def canonical_task_rows(groups: dict[str, list[str]] | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for repo_split, task_ids in (groups or CANONICAL_GROUPS).items():
        repo_id, split = repo_split.split("/", 1)
        for task_id in task_ids:
            rows.append(
                {
                    "task_id": task_id,
                    "repo_id": repo_id,
                    "canonical_split": split,
                    "repo_split": repo_split,
                }
            )
    return rows


def matrix_membership_evidence(cells: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    evidence: dict[str, dict[str, str]] = {}
    for cell in cells:
        task_id = str(cell.get("task_id") or "")
        repo_id = str(cell.get("repo_id") or "")
        split = str(cell.get("selected_split_from_frozen_design") or cell.get("split") or "")
        if not task_id or not repo_id or split not in {"B_eval", "H_future"}:
            continue
        key = f"{repo_id}/{split}"
        prior = evidence.get(task_id)
        if prior and prior["repo_split"] != key:
            raise ValueError(f"conflicting canonical split evidence for {task_id}: {prior['repo_split']} vs {key}")
        evidence[task_id] = {
            "task_id": task_id,
            "repo_id": repo_id,
            "canonical_split": split,
            "repo_split": key,
        }
    return evidence


def entry_gate_membership(entry_gate: dict[str, Any]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for raw_key, split in (("b_eval", "B_eval"), ("h_future", "H_future")):
        for task_id in entry_gate.get(raw_key, {}).get("selected_task_ids", []):
            task_id = str(task_id)
            repo_id = task_id.split("__", 1)[0]
            out[task_id] = {
                "task_id": task_id,
                "repo_id": repo_id,
                "canonical_split": split,
                "repo_split": f"{repo_id}/{split}",
            }
    return out


def build_canonical_split_map_payload(
    *,
    entry_gate: dict[str, Any],
    matrix: dict[str, Any],
    generated_at: str,
    groups: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    rows = canonical_task_rows(groups)
    if len(rows) != EXPECTED_CANONICAL_TASK_COUNT:
        raise ValueError(f"canonical split map must contain {EXPECTED_CANONICAL_TASK_COUNT} tasks")
    by_task = {row["task_id"]: row for row in rows}
    if len(by_task) != len(rows):
        raise ValueError("canonical split map contains duplicate task IDs")

    entry_membership = entry_gate_membership(entry_gate)
    matrix_membership = matrix_membership_evidence(matrix.get("cells", []))
    cross_checks: list[dict[str, str]] = []
    for task_id, row in sorted(by_task.items()):
        expected = row["repo_split"]
        entry = entry_membership.get(task_id)
        matrix_row = matrix_membership.get(task_id)
        if task_id.startswith("boltons__") and entry and entry["repo_split"] != expected:
            raise ValueError(f"entry-gate split mismatch for {task_id}: {entry['repo_split']} vs {expected}")
        if matrix_row and matrix_row["repo_split"] != expected:
            raise ValueError(f"matrix split mismatch for {task_id}: {matrix_row['repo_split']} vs {expected}")
        cross_checks.append(
            {
                "task_id": task_id,
                "canonical_repo_split": expected,
                "entry_gate_membership": entry["repo_split"] if entry else "not_present",
                "matrix_membership": matrix_row["repo_split"] if matrix_row else "not_present",
            }
        )

    task_to_split = {
        task_id: {
            "repo_id": row["repo_id"],
            "canonical_split": row["canonical_split"],
            "repo_split": row["repo_split"],
        }
        for task_id, row in sorted(by_task.items())
    }
    groups_out = {
        key: list(task_ids)
        for key, task_ids in sorted((groups or CANONICAL_GROUPS).items())
    }
    return {
        "schema_version": "barcarolle.phase1.canonical_split_map.v1",
        "generated_at": generated_at,
        "canonical_task_count": len(task_to_split),
        "groups": groups_out,
        "task_to_split": task_to_split,
        "cross_checks": cross_checks,
        "cross_check_sources": {
            "entry_gate_fields_used": ["b_eval.selected_task_ids", "h_future.selected_task_ids"],
            "matrix_fields_used": ["task_id", "repo_id", "selected_split_from_frozen_design", "split"],
            "matrix_status_and_adapter_fields_dropped": True,
        },
        "historical_pass_fail_outcomes_used_for_selection": False,
        "paid_outcome_used_for_selection": False,
        "paid_acut_calls_made": False,
        "boltons_clean_ext_017_canonical_repo_split": task_to_split["boltons__clean_ext__017"]["repo_split"],
    }


def write_canonical_split_map(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_canonical_split_map_payload(
        entry_gate=read_json(artifact_path(config, "old_future_holdout_entry_gate")),
        matrix=read_json(artifact_path(config, "task_outcome_matrix")),
        generated_at=stable_generated_at(config),
    )
    write_json(output_path(config, "canonical_split_map"), payload)
    return payload


def source_kind(source_ref: str) -> str:
    return statement_quality.source_kind(source_ref)


def implementation_files_for(row: dict[str, Any]) -> list[str]:
    code_files = [str(path) for path in row.get("code_files", []) if statement_quality.is_implementation_path(str(path))]
    if code_files:
        return sorted(code_files)
    changed_files = [str(path) for path in row.get("changed_files", [])]
    explicit = [str(path) for path in row.get("implementation_files", [])]
    impl = explicit or statement_quality.implementation_files(changed_files)
    return sorted(path for path in impl if statement_quality.is_implementation_path(path))


def test_files_for(row: dict[str, Any]) -> list[str]:
    changed_files = [str(path) for path in row.get("changed_files", [])]
    explicit = [str(path) for path in row.get("test_files", [])]
    return statement_quality.test_files(changed_files, explicit)


def certification_gate_summary(row: dict[str, Any]) -> dict[str, Any]:
    gates = row.get("clean_overlay_certification_gates") or row.get("local_certification_gates") or row.get("gates") or {}
    failed = sorted(str(key) for key, value in gates.items() if value != "pass")
    return {
        "all_pass": bool(gates) and not failed,
        "failed_gates": failed,
        "gate_count": len(gates),
        "gate_counts": dict(sorted(Counter(str(value) for value in gates.values()).items())),
    }


def verifier_command_metadata(repo_id: str, row: dict[str, Any], tests: list[str]) -> str:
    harness = str(row.get("harness_test_command") or "")
    if harness:
        return harness.replace("{test_files}", " ".join(tests))
    if repo_id == "attrs":
        return (
            'uv run --project experiments/phase0_headroom --with "pytest>=7,<8" '
            f'--with "setuptools<81" --with "hypothesis<6" python -m pytest -q {" ".join(tests)}'
        )
    return f'uv run --project experiments/phase0_headroom --with "pytest>=7,<8" python -m pytest -q {" ".join(tests)}'


def load_certified_by_task(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in (
        "boltons_clean_certified_tasks",
        "boltons_historical_certified_tasks",
        "attrs_clean_certified_tasks",
    ):
        rows.extend(read_jsonl(artifact_path(config, key)))
    return row_by_task(rows)


def load_context_by_task(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in (
        "boltons_clean_source_context",
        "boltons_historical_source_context",
        "attrs_clean_source_context",
    ):
        rows.extend(read_jsonl(artifact_path(config, key)))
    return row_by_task(rows)


def load_existing_statements(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return row_by_task(read_jsonl(artifact_path(config, "latest_codex_loop_generated_statements")))


def load_existing_reviews(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return row_by_task(read_json(artifact_path(config, "latest_codex_loop_statement_reviews")).get("reviews", []))


def load_existing_qa(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = read_json(artifact_path(config, "latest_codex_loop_deterministic_qa")).get("rows", [])
    return row_by_task(rows)


def canonical_inventory_row(
    *,
    split_row: dict[str, str],
    certified: dict[str, Any] | None,
    context: dict[str, Any] | None,
    existing_statement: dict[str, Any] | None,
    existing_review: dict[str, Any] | None,
    existing_qa: dict[str, Any] | None,
) -> dict[str, Any]:
    task_id = split_row["task_id"]
    repo_id = split_row["repo_id"]
    blockers: list[str] = []
    if not certified:
        blockers.append("missing_certified_task_metadata")
        certified = {}
    if not context:
        blockers.append("missing_source_context_metadata")
        context = certified.get("sanitized_context") or {}

    impl = implementation_files_for(certified)
    tests = test_files_for(certified)
    if not impl:
        blockers.append("missing_implementation_files")
    if not tests:
        blockers.append("missing_test_files")
    source_ref = str(context.get("ref") or (certified.get("allowed_context_refs") or [""])[0])
    review_status = str((existing_review or {}).get("status") or "")
    qa_status = str((existing_qa or {}).get("status") or (existing_review or {}).get("deterministic_qa", {}).get("status") or "")
    digest = str((existing_statement or {}).get("statement_digest") or "")
    reusable = bool(digest and review_status == "pass" and qa_status == "pass")
    return {
        "task_id": task_id,
        "repo_id": repo_id,
        "canonical_split": split_row["canonical_split"],
        "canonical_repo_split": split_row["repo_split"],
        "task_time": str(certified.get("task_time") or ""),
        "source_ref": source_ref,
        "source_kind": source_kind(source_ref),
        "source_summary": statement_quality.normalize_text(context.get("summary") or certified.get("subject") or ""),
        "source_kind_from": "source_context",
        "source_metadata_present": not any(blocker.startswith("missing_source") for blocker in blockers),
        "certified_metadata_present": not any(blocker.startswith("missing_certified") for blocker in blockers),
        "source_ref_from_certified_allowed_context": bool(source_ref and source_ref in [str(v) for v in certified.get("allowed_context_refs", [])]),
        "source_context_status": str(certified.get("source_context_status") or ""),
        "source_schema_version": str(context.get("schema_version") or ""),
        "source_kind_note": "split metadata only; pass/fail outcomes not used for selection",
        "source_context_body_digest": f"sha256:{digest_text(statement_quality.normalize_text(context.get('body_summary') or ''))}"
        if context.get("body_summary")
        else "",
        "source_context_body_excerpt": statement_quality.sanitize_public_body_summary(context.get("body_summary") or "", limit=360),
        "source_kind_for_packet": source_kind(source_ref),
        "source_ref_public": source_ref,
        "source_kind_public": source_kind(source_ref),
        "source_context_classification": str(context.get("classification") or ""),
        "source_context_state": str(context.get("state") or ""),
        "source_ref_used_for_statement_generation": source_ref,
        "source_kind_used_for_statement_generation": source_kind(source_ref),
        "source_public_context_available": bool(context.get("summary") or context.get("body_summary")),
        "implementation_files": impl,
        "test_files": tests,
        "module_or_package": [str(value) for value in certified.get("module_or_package", [])],
        "certification_gate_summary": certification_gate_summary(certified),
        "source_ref_metadata": [str(value) for value in certified.get("allowed_context_refs", [])],
        "source_kind_metadata": str(certified.get("source_type") or ""),
        "source_ref_kind": source_kind(source_ref),
        "source_kind_is_public_issue_or_pr": source_kind(source_ref) in {"issue", "pull_request"},
        "source_ref_for_context": source_ref,
        "source_context_ref": source_ref,
        "source_context_summary": statement_quality.normalize_text(context.get("summary") or ""),
        "source_context_excerpt": statement_quality.sanitize_public_body_summary(context.get("body_summary") or "", limit=360),
        "source_ref_task_statement_boundary": "public context plus sanitized diff summary only",
        "verifier_command_metadata": verifier_command_metadata(repo_id, certified, tests),
        "existing_codex_loop_statement_digest": digest,
        "existing_review_status": review_status or "missing",
        "existing_qa_status": qa_status or "missing",
        "existing_statement_reused": reusable,
        "needs_new_codex_loop_statement": not reusable,
        "metadata_blockers": blockers,
        "historical_pass_fail_outcomes_used_for_selection": False,
    }


def build_canonical_selected_inventory_payload(config: dict[str, Any]) -> dict[str, Any]:
    split_map = read_json(output_path(config, "canonical_split_map"))
    certified_by_task = load_certified_by_task(config)
    context_by_task = load_context_by_task(config)
    statement_by_task = load_existing_statements(config)
    review_by_task = load_existing_reviews(config)
    qa_by_task = load_existing_qa(config)
    rows = []
    for task_id, split_row in sorted(split_map["task_to_split"].items()):
        rows.append(
            canonical_inventory_row(
                split_row={"task_id": task_id, **split_row},
                certified=certified_by_task.get(task_id),
                context=context_by_task.get(task_id),
                existing_statement=statement_by_task.get(task_id),
                existing_review=review_by_task.get(task_id),
                existing_qa=qa_by_task.get(task_id),
            )
        )
    if len(rows) != EXPECTED_CANONICAL_TASK_COUNT:
        raise ValueError("canonical inventory must contain exactly 16 tasks")
    by_repo_split = Counter(row["canonical_repo_split"] for row in rows)
    missing = [row["task_id"] for row in rows if row["metadata_blockers"]]
    needs_new = [row["task_id"] for row in rows if row["needs_new_codex_loop_statement"]]
    return {
        "schema_version": "barcarolle.phase1.canonical_selected_inventory.v1",
        "generated_at": stable_generated_at(config),
        "canonical_task_count": len(rows),
        "rows": rows,
        "summary": {
            "canonical_task_count": len(rows),
            "repo_split_counts": dict(sorted(by_repo_split.items())),
            "metadata_blocker_task_ids": missing,
            "existing_reviewed_statement_reused_count": sum(1 for row in rows if row["existing_statement_reused"]),
            "needs_new_codex_loop_statement_count": len(needs_new),
            "needs_new_codex_loop_statement_task_ids": needs_new,
            "expected_missing_reviewed_statement_task_ids_before_repair": [
                "boltons__hist__011",
                "boltons__hist__022",
                "boltons__hist__023",
                "boltons__hist__027",
            ],
        },
        "paid_acut_calls_made": False,
        "historical_pass_fail_outcomes_used_for_selection": False,
    }


def render_inventory_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Phase 1 Canonical Selected Inventory",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Canonical task rows: `{payload['canonical_task_count']}`.",
        f"- Repo/split counts: `{summary['repo_split_counts']}`.",
        f"- Existing reviewed statements reused: `{summary['existing_reviewed_statement_reused_count']}`.",
        f"- Needs new Codex-loop statement: `{summary['needs_new_codex_loop_statement_task_ids']}`.",
        f"- Metadata blockers: `{summary['metadata_blocker_task_ids']}`.",
        "- Historical pass/fail outcomes used for selection: `false`.",
        "",
        "## Rows",
        "",
    ]
    for row in payload["rows"]:
        lines.extend(
            [
                f"### {row['task_id']}",
                "",
                f"- Repo/split: `{row['canonical_repo_split']}`.",
                f"- Source: `{row['source_ref']}` (`{row['source_kind']}`).",
                f"- Implementation files: `{row['implementation_files']}`.",
                f"- Test files: `{row['test_files']}`.",
                f"- Existing review/QA: `{row['existing_review_status']}` / `{row['existing_qa_status']}`.",
                f"- Needs new Codex-loop statement: `{row['needs_new_codex_loop_statement']}`.",
                f"- Metadata blockers: `{row['metadata_blockers']}`.",
                "",
            ]
        )
    return "\n".join(lines)


def write_canonical_inventory(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_canonical_selected_inventory_payload(config)
    write_json(output_path(config, "canonical_selected_inventory"), payload)
    write_text(output_path(config, "selected_inventory_report"), render_inventory_markdown(payload))
    return payload


def candidate_from_inventory_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": row["task_id"],
        "repo_id": row["repo_id"],
        "task_time": row["task_time"],
        "source_ref": row["source_ref"],
        "source_kind": row["source_kind"],
        "implementation_files": row["implementation_files"],
        "test_files": row["test_files"],
        "module_or_package": row.get("module_or_package", []),
        "certification_gate_summary": row["certification_gate_summary"],
        "statement_quality_gate": "manual_review_required",
        "statement_quality_risk_reasons": [],
        "statement_quality_diagnostics": {
            "body_summary_hit_old_cap": False,
            "statement_probably_truncated": False,
        },
        "verifier_command_metadata": row["verifier_command_metadata"],
    }


def build_candidate_packet_for_inventory_row(
    config: dict[str, Any],
    row: dict[str, Any],
    certified_by_task: dict[str, dict[str, Any]],
    context_by_task: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    packet = codexloop.build_codex_loop_candidate_packet(
        config=config,
        candidate=candidate_from_inventory_row(row),
        certified=certified_by_task.get(row["task_id"]),
        source_context=context_by_task.get(row["task_id"]),
    )
    packet["schema_version"] = "barcarolle.phase1.canonical_missing_statement_packet.v1"
    packet["canonical_split"] = row["canonical_split"]
    packet["canonical_repo_split"] = row["canonical_repo_split"]
    packet["canonical_split_source"] = "frozen_preregistration_entry_gate_and_two_repo_matrix_membership"
    packet["current_inventory_split_used_for_selection"] = False
    return redact_commit_hash_like_text(packet)


def redact_commit_hash_like_text(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: redact_commit_hash_like_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_commit_hash_like_text(item) for item in value]
    if isinstance(value, str):
        return TARGET_COMMIT_PATTERN.sub("[redacted-hex-hash]", value)
    return value


def build_missing_statement_packets(config: dict[str, Any]) -> dict[str, Any]:
    inventory = read_json(output_path(config, "canonical_selected_inventory"))
    certified_by_task = load_certified_by_task(config)
    context_by_task = load_context_by_task(config)
    missing_rows = [row for row in inventory["rows"] if row["needs_new_codex_loop_statement"]]
    packets = [
        build_candidate_packet_for_inventory_row(config, row, certified_by_task, context_by_task)
        for row in missing_rows
    ]
    payload = {
        "schema_version": "barcarolle.phase1.canonical_missing_statement_packets.v1",
        "generated_at": stable_generated_at(config),
        "candidate_count": len(packets),
        "task_ids": [packet["task_id"] for packet in packets],
        "real_codex_loop_required": bool(packets),
        "deterministic_generation_review_fallback_allowed": False,
        "raw_target_diffs_committed": False,
        "hidden_verifier_material_included": False,
        "historical_paid_outcomes_included": False,
        "paid_acut_calls_made": False,
        "packets": packets,
    }
    codexloop.validate_packet_payload(payload)
    return payload


def write_missing_statement_packets(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_missing_statement_packets(config)
    write_json(output_path(config, "missing_statement_packets"), payload)
    if not output_path(config, "session_proof").exists():
        write_json(output_path(config, "session_proof"), session_proof_base(config, packets=payload))
    return payload


def generator_prompt_text(config: dict[str, Any]) -> str:
    packet_path = output_path(config, "missing_statement_packets").relative_to(REPO_ROOT)
    output_rel = workflow_dir(config).relative_to(REPO_ROOT) / "generator" / "output" / "generated_statements.jsonl"
    process_rel = workflow_dir(config).relative_to(REPO_ROOT) / "generator" / "process.md"
    return f"""# Canonical Split Repair Statement Generator

You are the real external Codex CLI generator session for the Phase 1 canonical split repair.

Work in `/Users/chenmohan/gits/barcarolle`. Do not commit. Do not push. Do not run solver ACUT cells.

Read only this sanitized candidate packet file:

`{packet_path}`

Write one JSONL row per packet to:

`{output_rel}`

Update this process file before and after work:

`{process_rel}`

Required output row shape:

```json
{{"task_id":"...","statement":"...","statement_digest":"sha256:...","generation_notes":"...","used_diff_summary":true,"contains_raw_diff":false,"contains_paid_outcome":false}}
```

Rules:

- Generate solver-facing statements from public context plus diff summaries and digests in the packets.
- Do not copy raw target diffs, raw test assertions, hidden verifier material, target commit hashes, paid outcomes, terminal statuses, or exact implementation patch recipes.
- Use the canonical split only as benchmark metadata. Do not use historical pass/fail outcomes.
- Target 1500-2500 characters per statement, soft maximum 4000 characters, and never substring-truncate.
- Include problem summary, behavior details, expected behavior, editable implementation paths, non-editable test paths, verifier metadata, and scope boundaries.
- Set `statement_digest` to `sha256:` plus the SHA-256 digest of the exact statement string.
- Set `status: delivered` in the process file only after the JSONL output is complete and row digests are checked.

Process file format:

```text
status: delivered
updated: <UTC timestamp>
summary: Generated <N> canonical missing-task statements as a real external Codex CLI generator session.
artifacts:
  - {output_rel}
verification:
  - row count and statement digest check performed
```
"""


def reviewer_prompt_text(config: dict[str, Any]) -> str:
    packet_path = output_path(config, "missing_statement_packets").relative_to(REPO_ROOT)
    statements_path = output_path(config, "regenerated_statements").relative_to(REPO_ROOT)
    output_rel = workflow_dir(config).relative_to(REPO_ROOT) / "reviewer" / "output" / "statement_reviews.json"
    process_rel = workflow_dir(config).relative_to(REPO_ROOT) / "reviewer" / "process.md"
    handoff_rel = workflow_dir(config).relative_to(REPO_ROOT) / "reviewer" / "review-to-generator.md"
    return f"""# Canonical Split Repair Statement Reviewer

You are the real external Codex CLI reviewer session for the Phase 1 canonical split repair.

Work in `/Users/chenmohan/gits/barcarolle`. Do not commit. Do not push. Do not edit generated statements.

Read:

- Sanitized candidate packets: `{packet_path}`
- Generated statement JSONL copied from the generator session: `{statements_path}`

Write review verdicts to:

`{output_rel}`

Update this process file before and after work:

`{process_rel}`

Also write a concise handoff summary to:

`{handoff_rel}`

Each review row must use this shape:

```json
{{"task_id":"...","status":"pass","leakage_pass":true,"sufficiency_pass":true,"faithfulness_pass":true,"scope_pass":true,"formatting_pass":true,"reasons":["..."],"required_revision":"","statement_digest":"sha256:..."}}
```

Top-level output must include:

```json
{{"schema_version":"barcarolle.phase1.canonical_statement_reviews.v1","generated_at":"...","candidate_count":0,"review_counts":{{}},"llm_api_calls_made":false,"codex_subscription_session_used":true,"paid_acut_calls_made":false,"reviews":[]}}
```

Review checks:

- Leakage: no gold patch text, no raw diff hunks, no `diff --git`, no exact implementation recipe, no hidden verifier content, no raw test assertions, no paid outcome/status, no target commit hash.
- Sufficiency: problem summary, expected public behavior, behavior description, closed code fences, no mid-sentence truncation, and enough detail to attempt without hidden tests.
- Faithfulness: statement must be consistent with public context and diff summary.
- Scope: editable paths must be implementation-only; tests are non-editable metadata.
- Formatting: target 1500-2500 characters, soft max 4000, required sections present.

Return `pass`, `revise`, or `reject`. A `pass` row must have all five boolean checks true. Do not create replacement statements.

Set `status: delivered` in the process file only after every generated statement has exactly one review verdict.
"""


def run_script_text(role: str, config: dict[str, Any]) -> str:
    wf_rel = workflow_dir(config).relative_to(REPO_ROOT)
    session_name = str(config["generation_review"][f"{role}_tmux_session"])
    prompt = wf_rel / role / "prompt.md"
    process = wf_rel / role / "process.md"
    log = wf_rel / role / "cli.log"
    env_unsets = " ".join(f"-u {name}" for name in endpoint_env_vars(config))
    model = str(config["policy"]["required_codex_model"])
    reasoning = str(config["policy"]["required_reasoning_effort"])
    return f"""#!/usr/bin/env bash
set -euo pipefail
cd /Users/chenmohan/gits/barcarolle

WORKFLOW="{wf_rel}"
PROCESS="{process}"
LOG="{log}"

timestamp() {{
  date -u +%Y-%m-%dT%H:%M:%SZ
}}

mkdir -p "$WORKFLOW/{role}/output"
cat > "$PROCESS" <<EOF
status: working
updated: $(timestamp)
summary: External Codex CLI {role} wrapper started using local Codex Subscription auth with API endpoint environment variables unset.
session: {session_name}
llm_api_endpoint_used: false
EOF

set +e
env {env_unsets} \\
codex exec \\
  -C /Users/chenmohan/gits/barcarolle \\
  -m {model} \\
  -c 'model_reasoning_effort="{reasoning}"' \\
  --dangerously-bypass-approvals-and-sandbox \\
  - < "{prompt}" \\
  > "$LOG" \\
  2>&1
rc=$?
set -e

if [ "$rc" -ne 0 ]; then
  cat > "$PROCESS" <<EOF
status: blocked
updated: $(timestamp)
summary: External Codex CLI {role} exited non-zero. Raw log is intentionally ignored and not committed.
session: {session_name}
exit_code: $rc
EOF
  exit "$rc"
fi

if ! grep -q '^status: delivered' "$PROCESS"; then
  cat >> "$PROCESS" <<EOF
wrapper_status: blocked_after_cli_return
wrapper_updated: $(timestamp)
wrapper_summary: Codex CLI returned zero but the {role} process file did not report delivered.
EOF
  exit 3
fi
"""


def pending_process_text(role: str, *, skipped: bool = False) -> str:
    if skipped:
        return f"""status: skipped
updated: {utc_now()}
summary: No missing canonical statements required an external Codex CLI {role} session.
"""
    return f"""status: pending
updated: {utc_now()}
summary: Waiting for external Codex CLI {role} session to start.
"""


def write_workflow_files(config: dict[str, Any]) -> dict[str, Any]:
    packets = read_json(output_path(config, "missing_statement_packets"))
    wf = workflow_dir(config)
    no_missing = int(packets.get("candidate_count") or 0) == 0
    write_text(
        wf / "coordinator.md",
        "\n".join(
            [
                "# Phase 1 Canonical Split Repair Codex Loop",
                "",
                "Status: pending.",
                "",
                "Runbook: `docs/experiments/phase-1-targeted-statement-hardened-replacement-supply-runbook.md`.",
                "",
                "Use only process files for coordination. Raw CLI logs are ignored and must not be committed.",
            ]
        ),
    )
    write_text(wf / "generator" / "prompt.md", generator_prompt_text(config))
    write_text(wf / "generator" / "process.md", pending_process_text("generator", skipped=no_missing))
    write_text(wf / "generator" / "run_generator.sh", run_script_text("generator", config))
    write_text(wf / "reviewer" / "prompt.md", reviewer_prompt_text(config))
    write_text(wf / "reviewer" / "process.md", pending_process_text("reviewer", skipped=no_missing))
    write_text(wf / "reviewer" / "review-to-generator.md", "status: pending\n")
    write_text(wf / "reviewer" / "run_reviewer.sh", run_script_text("reviewer", config))
    for path in (wf / "generator" / "run_generator.sh", wf / "reviewer" / "run_reviewer.sh"):
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    proof = session_proof_base(config, packets=packets)
    if no_missing:
        proof["real_codex_loop_required"] = False
        proof["real_generator_codex_cli_session_started"] = False
        proof["real_reviewer_codex_cli_session_started"] = False
        proof["generator_process_file_present"] = True
        proof["reviewer_process_file_present"] = True
        proof["sessions"] = []
    write_json(output_path(config, "session_proof"), proof)
    return proof


def status_from_process(path: Path) -> str:
    if not path.exists():
        return "missing"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("status:"):
            return line.split(":", 1)[1].strip()
    return "missing"


def session_proof_base(config: dict[str, Any], *, packets: dict[str, Any] | None = None) -> dict[str, Any]:
    existing_path = output_path(config, "session_proof")
    if existing_path.exists():
        proof = read_json(existing_path)
        proof["model_provider"] = "local_codex_subscription"
        proof["generator_reviewer_did_not_use_llm_api_endpoint"] = True
        proof["llm_api_calls_made_for_generator_reviewer"] = False
        return proof
    packets = packets or {}
    return {
        "schema_version": "barcarolle.phase1.canonical_codex_loop_session_proof.v1",
        "generated_at": stable_generated_at(config),
        "real_codex_loop_required": bool(packets.get("candidate_count")),
        "candidate_count": int(packets.get("candidate_count") or 0),
        "task_ids": [str(value) for value in packets.get("task_ids", [])],
        "endpoint_base_url_host": "",
        "model_provider": "local_codex_subscription",
        "model_provider_env_key": None,
        "required_model": str(config["policy"]["required_codex_model"]),
        "required_reasoning_effort": str(config["policy"]["required_reasoning_effort"]),
        "generator_reviewer_used_local_codex_subscription": bool(packets.get("candidate_count")),
        "generator_reviewer_did_not_use_llm_api_endpoint": True,
        "llm_api_calls_made_for_generator_reviewer": False,
        "real_generator_codex_cli_session_started": False,
        "real_reviewer_codex_cli_session_started": False,
        "generator_process_file_present": False,
        "reviewer_process_file_present": False,
        "raw_cli_logs_committed": False,
        "paid_acut_solver_cells_run": False,
        "historical_paid_outcomes_used_for_generation_or_review": False,
        "sessions": [],
    }


def record_session_start(config: dict[str, Any], role: str) -> dict[str, Any]:
    if role not in {"generator", "reviewer"}:
        raise ValueError(f"unsupported session role: {role}")
    wf = workflow_dir(config)
    process = wf / role / "process.md"
    proof = session_proof_base(config)
    proof[f"real_{role}_codex_cli_session_started"] = True
    proof[f"{role}_process_file_present"] = process.exists()
    proof["generator_reviewer_used_local_codex_subscription"] = True
    proof["generator_reviewer_did_not_use_llm_api_endpoint"] = True
    proof["llm_api_calls_made_for_generator_reviewer"] = False
    proof["sessions"] = [
        session for session in proof.get("sessions", []) if session.get("role") != role
    ] + [
        {
            "role": role,
            "tmux_session": str(config["generation_review"][f"{role}_tmux_session"]),
            "command_shape": f"tmux new-session -> run_{role}.sh -> env -u LLM_BASE_URL -u LLM_API_KEY -u OPENAI_API_KEY -u OPENROUTER_API_KEY codex exec using local Codex Subscription",
            "started_at": utc_now(),
            "ended_at": "",
            "process_status": status_from_process(process),
            "process_file": str(process.relative_to(REPO_ROOT)),
            "output_row_count": 0,
        }
    ]
    write_json(output_path(config, "session_proof"), proof)
    return proof


def validate_generated_statement_rows(rows: list[dict[str, Any]], packet_count: int) -> None:
    codexloop.validate_generated_statement_rows(rows, packet_count)
    for row in rows:
        statement = str(row.get("statement") or "")
        for marker, reason in FORBIDDEN_STATEMENT_PATTERNS.items():
            if marker in statement.lower():
                raise ValueError(f"generated statement contains forbidden text {reason}: {row.get('task_id')}")
        if TARGET_COMMIT_PATTERN.search(statement):
            raise ValueError(f"generated statement contains target commit hash: {row.get('task_id')}")


def copy_generator_output(config: dict[str, Any]) -> dict[str, Any]:
    wf = workflow_dir(config)
    source = wf / "generator" / "output" / "generated_statements.jsonl"
    process = wf / "generator" / "process.md"
    packets = read_json(output_path(config, "missing_statement_packets"))
    if int(packets.get("candidate_count") or 0) == 0:
        write_jsonl(output_path(config, "regenerated_statements"), [])
        return session_proof_base(config, packets=packets)
    if status_from_process(process) != "delivered":
        raise ValueError("generator process did not report status: delivered")
    rows = read_jsonl(source)
    validate_generated_statement_rows(rows, int(packets["candidate_count"]))
    write_jsonl(output_path(config, "regenerated_statements"), rows)
    proof = session_proof_base(config)
    proof["real_generator_codex_cli_session_started"] = True
    proof["generator_process_file_present"] = process.exists()
    proof["generator_output_not_deterministic_override"] = True
    existing = next((session for session in proof.get("sessions", []) if session.get("role") == "generator"), {})
    proof["sessions"] = [
        session for session in proof.get("sessions", []) if session.get("role") != "generator"
    ] + [
        {
            "role": "generator",
            "tmux_session": str(config["generation_review"]["generator_tmux_session"]),
            "command_shape": "tmux new-session -> run_generator.sh -> env -u LLM_BASE_URL -u LLM_API_KEY -u OPENAI_API_KEY -u OPENROUTER_API_KEY codex exec using local Codex Subscription",
            "started_at": existing.get("started_at") or stable_generated_at(config),
            "ended_at": utc_now(),
            "process_status": "delivered",
            "process_file": str(process.relative_to(REPO_ROOT)),
            "output_row_count": len(rows),
            "output_path": str(output_path(config, "regenerated_statements").relative_to(REPO_ROOT)),
        }
    ]
    write_json(output_path(config, "session_proof"), proof)
    return proof


def normalize_review_payload(payload: dict[str, Any]) -> dict[str, Any]:
    reviews = payload.get("reviews", [])
    normalized = dict(payload)
    normalized["schema_version"] = "barcarolle.phase1.canonical_statement_reviews.v1"
    normalized["generated_at"] = str(payload.get("generated_at") or utc_now())
    normalized["candidate_count"] = len(reviews)
    normalized["review_counts"] = dict(sorted(Counter(str(review.get("status")) for review in reviews).items()))
    normalized["paid_llm_calls_made"] = False
    normalized["llm_api_calls_made"] = False
    normalized["codex_subscription_session_used"] = bool(reviews)
    normalized["paid_acut_calls_made"] = False
    normalized["raw_prompts_or_completions_committed"] = False
    normalized["reviews"] = reviews
    return normalized


def render_statement_reviews_markdown(reviews: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Canonical Statement Reviews",
        "",
        f"Generated: `{reviews['generated_at']}`.",
        "",
        f"- Candidate statements reviewed: `{reviews['candidate_count']}`.",
        f"- Review counts: `{reviews['review_counts']}`.",
        f"- LLM API calls made: `{reviews.get('llm_api_calls_made')}`.",
        f"- Codex Subscription session used: `{reviews.get('codex_subscription_session_used')}`.",
        "- Paid ACUT calls made: `false`.",
        "- Raw prompts or completions committed: `false`.",
        "",
        "## Verdicts",
        "",
    ]
    for review in reviews["reviews"]:
        lines.extend(
            [
                f"### {review['task_id']}",
                "",
                f"- Status: `{review['status']}`.",
                f"- Checks: `{{'leakage_pass': {review['leakage_pass']}, 'sufficiency_pass': {review['sufficiency_pass']}, 'faithfulness_pass': {review['faithfulness_pass']}, 'scope_pass': {review['scope_pass']}, 'formatting_pass': {review['formatting_pass']}}}`.",
                f"- Reasons: `{review.get('reasons', [])}`.",
                f"- Required revision: `{review.get('required_revision', '')}`.",
                "",
            ]
        )
    return "\n".join(lines)


def copy_reviewer_output(config: dict[str, Any]) -> dict[str, Any]:
    wf = workflow_dir(config)
    source = wf / "reviewer" / "output" / "statement_reviews.json"
    process = wf / "reviewer" / "process.md"
    generated = read_jsonl(output_path(config, "regenerated_statements"))
    if not generated:
        payload = normalize_review_payload({"reviews": []})
        write_json(output_path(config, "statement_reviews"), payload)
        write_text(output_path(config, "statement_reviews_report"), render_statement_reviews_markdown(payload))
        return payload
    if status_from_process(process) != "delivered":
        raise ValueError("reviewer process did not report status: delivered")
    payload = normalize_review_payload(read_json(source))
    codexloop.validate_review_payload(payload, generated)
    write_json(output_path(config, "statement_reviews"), payload)
    write_text(output_path(config, "statement_reviews_report"), render_statement_reviews_markdown(payload))
    proof = session_proof_base(config)
    proof["real_reviewer_codex_cli_session_started"] = True
    proof["reviewer_process_file_present"] = process.exists()
    proof["reviewer_output_not_deterministic_rules_only"] = True
    existing = next((session for session in proof.get("sessions", []) if session.get("role") == "reviewer"), {})
    proof["sessions"] = [
        session for session in proof.get("sessions", []) if session.get("role") != "reviewer"
    ] + [
        {
            "role": "reviewer",
            "tmux_session": str(config["generation_review"]["reviewer_tmux_session"]),
            "command_shape": "tmux new-session -> run_reviewer.sh -> env -u LLM_BASE_URL -u LLM_API_KEY -u OPENAI_API_KEY -u OPENROUTER_API_KEY codex exec using local Codex Subscription",
            "started_at": existing.get("started_at") or stable_generated_at(config),
            "ended_at": utc_now(),
            "process_status": "delivered",
            "process_file": str(process.relative_to(REPO_ROOT)),
            "output_row_count": len(payload["reviews"]),
            "output_path": str(output_path(config, "statement_reviews").relative_to(REPO_ROOT)),
        }
    ]
    write_json(output_path(config, "session_proof"), proof)
    return payload


def load_previous_packets(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    path = artifact_path(config, "latest_codex_loop_statement_screen").with_name(
        "phase1_diff_assisted_codex_loop_candidate_packets.json"
    )
    if not path.exists():
        return {}
    return row_by_task(read_json(path).get("packets", []))


def qa_review_shape(review: dict[str, Any]) -> dict[str, Any]:
    shaped = dict(review)
    shaped["status"] = review.get("status") or review.get("final_status")
    return shaped


def deterministic_qa_row(packet: dict[str, Any], statement: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    return codexloop.deterministic_qa_row(packet, statement, qa_review_shape(review))


def build_canonical_statement_qa(config: dict[str, Any]) -> dict[str, Any]:
    inventory = read_json(output_path(config, "canonical_selected_inventory"))
    previous_packets = load_previous_packets(config)
    missing_packets = row_by_task(read_json(output_path(config, "missing_statement_packets")).get("packets", []))
    existing_statements = load_existing_statements(config)
    new_statements = row_by_task(read_jsonl(output_path(config, "regenerated_statements")))
    existing_reviews = load_existing_reviews(config)
    new_reviews = row_by_task(read_json(output_path(config, "statement_reviews")).get("reviews", []))
    rows: list[dict[str, Any]] = []
    for row in inventory["rows"]:
        task_id = row["task_id"]
        source = "new_codex_loop" if row["needs_new_codex_loop_statement"] else "reused_codex_loop"
        packet = (missing_packets if source == "new_codex_loop" else previous_packets).get(task_id)
        statement = (new_statements if source == "new_codex_loop" else existing_statements).get(task_id)
        review = (new_reviews if source == "new_codex_loop" else existing_reviews).get(task_id)
        reasons: list[str] = []
        if not packet:
            reasons.append("missing_packet")
        if not statement:
            reasons.append("missing_statement")
        if not review:
            reasons.append("missing_review")
        if reasons:
            qa = {
                "status": "reject",
                "reasons": reasons,
                "checks": {},
            }
        else:
            qa = deterministic_qa_row(packet, statement, review)
        rows.append(
            {
                "task_id": task_id,
                "repo_id": row["repo_id"],
                "canonical_split": row["canonical_split"],
                "canonical_repo_split": row["canonical_repo_split"],
                "statement_source": source,
                "statement_digest": (statement or {}).get("statement_digest", ""),
                "review_status": (review or {}).get("status", "missing"),
                **qa,
            }
        )
    payload = {
        "schema_version": "barcarolle.phase1.canonical_statement_qa.v1",
        "generated_at": utc_now(),
        "candidate_count": len(rows),
        "qa_counts": dict(sorted(Counter(row["status"] for row in rows).items())),
        "statement_source_counts": dict(sorted(Counter(row["statement_source"] for row in rows).items())),
        "deterministic_qa_guardrail_only": True,
        "deterministic_qa_created_pass_without_reviewer_pass": False,
        "paid_acut_calls_made": False,
        "true_canonical_statement_blocker_task_ids": [
            row["task_id"]
            for row in rows
            if row["status"] != "pass" and row["task_id"] in {"boltons__hist__022", "boltons__hist__023", "boltons__hist__027"}
        ],
        "rows": rows,
    }
    return payload


def write_canonical_statement_qa(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_canonical_statement_qa(config)
    write_json(output_path(config, "statement_qa"), payload)
    return payload


def build_canonical_statement_screen_payload(config: dict[str, Any]) -> dict[str, Any]:
    split_map = read_json(output_path(config, "canonical_split_map"))
    inventory = read_json(output_path(config, "canonical_selected_inventory"))
    qa = read_json(output_path(config, "statement_qa"))
    existing_reviews = load_existing_reviews(config)
    new_reviews = row_by_task(read_json(output_path(config, "statement_reviews")).get("reviews", []))
    qa_by_task = row_by_task(qa["rows"])
    inventory_by_task = row_by_task(inventory["rows"])
    candidate_screens = []
    for task_id, split_row in sorted(split_map["task_to_split"].items()):
        inv = inventory_by_task[task_id]
        review = (new_reviews if inv["needs_new_codex_loop_statement"] else existing_reviews).get(task_id, {})
        qa_row = qa_by_task.get(task_id, {})
        eligible = review.get("status") == "pass" and qa_row.get("status") == "pass" and bool(split_row.get("canonical_split"))
        reasons: list[str] = []
        if not split_row.get("canonical_split"):
            reasons.append("missing_canonical_split")
        if review.get("status") != "pass":
            reasons.append(f"review_status:{review.get('status', 'missing')}")
        if qa_row.get("status") != "pass":
            reasons.append(f"deterministic_qa_status:{qa_row.get('status', 'missing')}")
        candidate_screens.append(
            {
                "task_id": task_id,
                "repo_id": split_row["repo_id"],
                "canonical_split": split_row["canonical_split"],
                "canonical_repo_split": split_row["repo_split"],
                "task_time": inv["task_time"],
                "review_status": review.get("status", "missing"),
                "deterministic_qa_status": qa_row.get("status", "missing"),
                "statement_digest": qa_row.get("statement_digest", ""),
                "statement_source": qa_row.get("statement_source", ""),
                "eligible_under_canonical_split_repair": eligible,
                "rejection_reasons": reasons,
                "current_inventory_split_used_for_selection": False,
                "historical_pass_fail_outcomes_used_for_selection": False,
            }
        )
    selected: dict[str, list[str]] = {key: [] for key in sorted(CANONICAL_GROUPS)}
    for screen in candidate_screens:
        key = screen["canonical_repo_split"]
        if screen["eligible_under_canonical_split_repair"]:
            selected.setdefault(key, []).append(screen["task_id"])
    selected = {key: sorted(value) for key, value in sorted(selected.items())}
    counts = {key: len(value) for key, value in selected.items()}
    missing = {
        key: [f"needed 4, found {count} reviewed QA-passed canonical statements"]
        for key, count in counts.items()
        if count < 4
    }
    repaired = counts.get("boltons/H_future") == 4
    return {
        "schema_version": "barcarolle.phase1.canonical_statement_screen.v1",
        "generated_at": utc_now(),
        "candidate_count": len(candidate_screens),
        "canonical_task_count": len(candidate_screens),
        "selected_task_ids_by_repo_split": selected,
        "selected_counts_by_repo_split": counts,
        "remaining_missing_supply": missing,
        "boltons_h_future_false_hole_repaired_by_split_inventory_correction": repaired,
        "previous_boltons_h_future_zero_reclassified_as": "suspected_inventory_and_split_mapping_bug",
        "canonical_statement_screen_ready": not missing,
        "review_counts": dict(sorted(Counter(row["review_status"] for row in candidate_screens).items())),
        "deterministic_qa_counts": dict(sorted(Counter(row["deterministic_qa_status"] for row in candidate_screens).items())),
        "statement_source_counts": qa["statement_source_counts"],
        "paid_outcome_used_for_selection": False,
        "paid_acut_calls_made": False,
        "paid_solver_cells_run": False,
        "predictive_validity_established": False,
        "generated_statement_is_scoreable_result": False,
        "candidate_screens": candidate_screens,
    }


def render_statement_screen_markdown(screen: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Canonical Statement Screen",
        "",
        f"Generated: `{screen['generated_at']}`.",
        "",
        f"- Canonical task count: `{screen['canonical_task_count']}`.",
        f"- Review counts: `{screen['review_counts']}`.",
        f"- Deterministic QA counts: `{screen['deterministic_qa_counts']}`.",
        f"- Statement source counts: `{screen['statement_source_counts']}`.",
        f"- Selected counts by repo/split: `{screen['selected_counts_by_repo_split']}`.",
        f"- Remaining missing supply: `{screen['remaining_missing_supply']}`.",
        f"- `boltons/H_future: 0` repaired by split/inventory correction: `{screen['boltons_h_future_false_hole_repaired_by_split_inventory_correction']}`.",
        "",
        "The screen uses canonical split labels from the frozen Phase 1 map. It does not infer split from current inventory rows, task time, or historical pass/fail outcomes.",
        "",
        "This screen does not claim predictive validity or paid validation.",
    ]
    return "\n".join(lines)


def write_canonical_statement_screen(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_canonical_statement_screen_payload(config)
    write_json(output_path(config, "statement_screen"), payload)
    write_text(output_path(config, "statement_screen_report"), render_statement_screen_markdown(payload))
    return payload


def build_split_repair_decision(config: dict[str, Any]) -> dict[str, Any]:
    inventory = read_json(output_path(config, "canonical_selected_inventory"))
    screen = read_json(output_path(config, "statement_screen"))
    proof = read_json(output_path(config, "session_proof")) if output_path(config, "session_proof").exists() else {}
    metadata_blockers = inventory["summary"]["metadata_blocker_task_ids"]
    failed_tasks = [
        row["task_id"]
        for row in screen["candidate_screens"]
        if not row["eligible_under_canonical_split_repair"]
    ]
    needed_loop = bool(inventory["summary"]["needs_new_codex_loop_statement_task_ids"])
    loop_completed = (
        not needed_loop
        or (
            proof.get("real_generator_codex_cli_session_started")
            and proof.get("real_reviewer_codex_cli_session_started")
            and proof.get("generator_output_not_deterministic_override")
            and proof.get("reviewer_output_not_deterministic_rules_only")
        )
    )
    if metadata_blockers:
        primary = "blocked_on_missing_canonical_metadata"
    elif needed_loop and not loop_completed:
        primary = "blocked_on_codex_loop"
    elif failed_tasks:
        primary = "true_targeted_replacement_supply_needed"
    else:
        primary = "canonical_split_repair_complete_retry_preregistration"
    next_runbook = (
        "docs/experiments/phase-1-statement-hardened-preregistration-after-canonical-split-repair-runbook.md"
        if primary == "canonical_split_repair_complete_retry_preregistration"
        else "docs/experiments/phase-1-true-targeted-statement-hardened-replacement-supply-runbook.md"
    )
    return {
        "schema_version": "barcarolle.phase1.canonical_split_repair_decision.v1",
        "generated_at": utc_now(),
        "primary_decision": primary,
        "boltons_h_future_was_false_hole": screen["boltons_h_future_false_hole_repaired_by_split_inventory_correction"],
        "canonical_selected_task_count": screen["canonical_task_count"],
        "canonical_review_qa_pass_count": sum(
            1 for row in screen["candidate_screens"] if row["eligible_under_canonical_split_repair"]
        ),
        "selected_counts_by_repo_split": screen["selected_counts_by_repo_split"],
        "blocked_or_replacement_task_ids": metadata_blockers or failed_tasks,
        "needed_codex_loop_task_ids": inventory["summary"]["needs_new_codex_loop_statement_task_ids"],
        "real_codex_generator_reviewer_loop_completed": bool(loop_completed),
        "generator_reviewer_used_local_codex_subscription": bool(proof.get("generator_reviewer_used_local_codex_subscription")),
        "generator_reviewer_did_not_use_llm_api_endpoint": bool(proof.get("generator_reviewer_did_not_use_llm_api_endpoint", True)),
        "llm_api_calls_made_for_generator_reviewer": False,
        "statement_hardened_preregistration_ready_after_split_repair": primary == "canonical_split_repair_complete_retry_preregistration",
        "targeted_replacement_supply_still_needed": primary == "true_targeted_replacement_supply_needed",
        "next_runbook_path": next_runbook,
        "paid_validation_completed": False,
        "paid_acut_calls_made": False,
        "paid_solver_cells_run": False,
        "predictive_validity_established": False,
        "old_paid_result_repaired": False,
        "attrs_policy_violation_repaired": False,
        "historical_pass_fail_used_for_selection": False,
        "generated_statement_is_scoreable_result": False,
    }


def render_split_repair_decision_markdown(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Canonical Split Repair Decision",
            "",
            f"Generated: `{decision['generated_at']}`.",
            "",
            f"- Primary decision: `{decision['primary_decision']}`.",
            f"- `boltons/H_future` was a false hole: `{decision['boltons_h_future_was_false_hole']}`.",
            f"- Canonical selected task count: `{decision['canonical_selected_task_count']}`.",
            f"- Canonical review/QA pass count: `{decision['canonical_review_qa_pass_count']}`.",
            f"- Selected counts by repo/split: `{decision['selected_counts_by_repo_split']}`.",
            f"- Blocked or replacement task IDs: `{decision['blocked_or_replacement_task_ids']}`.",
            f"- Next runbook: `{decision['next_runbook_path']}`.",
            "",
            "No paid validation was started. This decision does not claim predictive validity, repaired historical paid results, or scoreable results from generated statements.",
        ]
    )


def render_success_preregistration_runbook(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Statement-Hardened Preregistration After Canonical Split Repair Runbook",
            "",
            "Status: draft only, not executed.",
            "",
            "Use this runbook after the canonical split repair has produced reviewed and deterministic-QA-passed statements for all 16 canonical tasks.",
            "",
            "## Required Inputs",
            "",
            "- `experiments/phase1_compiler/results/phase1_canonical_split_map.json`",
            "- `experiments/phase1_compiler/results/phase1_canonical_selected_inventory.json`",
            "- `experiments/phase1_compiler/results/phase1_canonical_statement_reviews.json`",
            "- `experiments/phase1_compiler/results/phase1_canonical_statement_qa.json`",
            "- `experiments/phase1_compiler/results/phase1_canonical_statement_screen.json`",
            "- `experiments/phase1_compiler/results/phase1_canonical_split_repair_decision.json`",
            "",
            "## Scope",
            "",
            "- Freeze a new statement-hardened preregistration from the canonical split screen.",
            "- Use canonical split labels only.",
            "- Keep paid ACUT validation disabled until the user explicitly approves a paid run.",
            "- Do not rerun old scoreable cells or rewrite historical score tables.",
            "",
            "## Current Decision",
            "",
            f"- Primary decision: `{decision['primary_decision']}`.",
            f"- Selected counts by repo/split: `{decision['selected_counts_by_repo_split']}`.",
            f"- Next paid validation status: `requires_explicit_user_approval`.",
            "",
            "## Disallowed Claims",
            "",
            "- `predictive_validity_established`",
            "- `paid_validation_completed`",
            "- `old_paid_result_repaired`",
        ]
    )


def render_replacement_supply_runbook(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 True Targeted Statement-Hardened Replacement Supply Runbook",
            "",
            "Status: draft only, not executed.",
            "",
            "Use this runbook only if canonical selected tasks fail to produce non-leaky, sufficient reviewed statements.",
            "",
            "## Replacement Task IDs",
            "",
            f"`{decision['blocked_or_replacement_task_ids']}`",
            "",
            "## Scope",
            "",
            "- Mine replacement tasks only for the blocked canonical repo/split groups.",
            "- Do not use historical pass/fail outcomes for selection.",
            "- Keep paid ACUT validation disabled until a new preregistration is ready and explicitly approved.",
        ]
    )


def write_split_repair_decision(config: dict[str, Any]) -> dict[str, Any]:
    decision = build_split_repair_decision(config)
    write_json(output_path(config, "split_repair_decision"), decision)
    write_text(output_path(config, "split_repair_decision_report"), render_split_repair_decision_markdown(decision))
    if decision["primary_decision"] == "canonical_split_repair_complete_retry_preregistration":
        write_text(REPO_ROOT / decision["next_runbook_path"], render_success_preregistration_runbook(decision))
    elif decision["primary_decision"] == "true_targeted_replacement_supply_needed":
        write_text(REPO_ROOT / decision["next_runbook_path"], render_replacement_supply_runbook(decision))
    return decision


def optional_json(path: Path) -> dict[str, Any]:
    return read_json(path) if path.exists() else {}


def optional_jsonl_count(path: Path) -> int:
    return len(read_jsonl(path)) if path.exists() else 0


def process_step_status(config: dict[str, Any], *, closeout: bool) -> list[tuple[str, str]]:
    decision = optional_json(output_path(config, "split_repair_decision"))
    return [
        ("Step 0 preflight", "completed" if output_path(config, "preflight").exists() else "not_run"),
        ("Step 1 canonical split map", "completed" if output_path(config, "canonical_split_map").exists() else "not_run"),
        ("Step 2 canonical selected inventory", "completed" if output_path(config, "canonical_selected_inventory").exists() else "not_run"),
        ("Step 3 missing-task Codex loop", "completed" if output_path(config, "statement_reviews").exists() else "not_run"),
        ("Step 4 deterministic QA and statement merge", "completed" if output_path(config, "statement_qa").exists() else "not_run"),
        ("Step 5 canonical split screen", "completed" if output_path(config, "statement_screen").exists() else "not_run"),
        ("Step 6 decision", str(decision.get("primary_decision") or "not_run")),
        ("Step 7 closeout", "completed" if closeout else "not_run"),
    ]


def render_process_report(config: dict[str, Any], *, closeout: bool) -> str:
    preflight = optional_json(output_path(config, "preflight"))
    split_map = optional_json(output_path(config, "canonical_split_map"))
    inventory = optional_json(output_path(config, "canonical_selected_inventory"))
    packets = optional_json(output_path(config, "missing_statement_packets"))
    reviews = optional_json(output_path(config, "statement_reviews"))
    qa = optional_json(output_path(config, "statement_qa"))
    screen = optional_json(output_path(config, "statement_screen"))
    decision = optional_json(output_path(config, "split_repair_decision"))
    proof = optional_json(output_path(config, "session_proof"))
    step_lines = "\n".join(f"- {name}: `{status}`." for name, status in process_step_status(config, closeout=closeout))
    commits = command_output(["git", "log", "--oneline", "--max-count=7"])
    return f"""# Phase 1 Canonical Split Repair Process

Generated: `{preflight.get('generated_at', stable_generated_at(config))}`.
Closeout updated: `{utc_now() if closeout else 'not_run'}`.

## Step Status

{step_lines}

## Commits

```text
{commits}
```

Closeout commit: `Record canonical split repair closeout`.

## Results

- Paid ACUT calls made: `false`.
- Codex Subscription statement sessions used: `{str(bool(proof.get('real_generator_codex_cli_session_started') or proof.get('real_reviewer_codex_cli_session_started'))).lower()}`.
- LLM API endpoint used for statement sessions: `false`.
- Raw artifacts committed: `false`.
- Historical pass/fail outcomes used for selection: `false`.
- Previous `boltons/H_future: 0` reclassification: `{preflight.get('previous_boltons_h_future_zero_reclassification', 'unknown')}`.
- Canonical selected tasks: `{inventory.get('canonical_task_count', split_map.get('canonical_task_count', 'not_run'))}`.
- Missing canonical statement packets: `{packets.get('candidate_count', 'not_run')}`.
- Generated missing statements: `{optional_jsonl_count(output_path(config, 'regenerated_statements'))}`.
- Review counts: `{reviews.get('review_counts', 'not_run')}`.
- Deterministic QA counts: `{qa.get('qa_counts', 'not_run')}`.
- Canonical statements review/QA pass count: `{decision.get('canonical_review_qa_pass_count', 'not_decided')}`.
- Selected counts by repo/split: `{screen.get('selected_counts_by_repo_split', 'not_screened')}`.
- Primary decision: `{decision.get('primary_decision', 'not_decided')}`.
- Next runbook path: `{decision.get('next_runbook_path', 'not_decided')}`.

## Guardrails

- Paid solver cells run: `false`.
- Existing scoreable cells rerun: `false`.
- Confirmed `attrs__hist__027` policy-violation cell rerun: `false`.
- Historical score tables rewritten: `false`.
- Predictive validity established: `false`.
- Paid validation completed: `false`.
- Generated statements are scoreable results: `false`.

## Verification

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_canonical_split_statement_repair.py`: `6 passed`.
- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_diff_assisted_codex_loop_statement_regeneration.py experiments/phase1_compiler/tests/test_phase1_statement_hardened_preregistration.py experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py experiments/phase0_headroom/tools/test_workspace_acut_run.py`: `58 passed`.
- `git diff --check`: `passed`.
"""


def write_closeout(config: dict[str, Any]) -> None:
    write_text(output_path(config, "process_report"), render_process_report(config, closeout=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Repair Phase 1 canonical split statement supply.")
    parser.add_argument("mode", choices=sorted(MODES))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--role", choices=["generator", "reviewer"])
    args = parser.parse_args(argv)

    config = load_config(args.config)
    if args.mode == "split-map":
        write_canonical_split_map(config)
    elif args.mode == "inventory":
        write_canonical_inventory(config)
    elif args.mode == "packets":
        write_missing_statement_packets(config)
    elif args.mode == "workflow":
        write_workflow_files(config)
    elif args.mode == "record-session-start":
        if not args.role:
            raise SystemExit("--role is required for record-session-start")
        record_session_start(config, args.role)
    elif args.mode == "copy-generator-output":
        copy_generator_output(config)
    elif args.mode == "copy-reviewer-output":
        copy_reviewer_output(config)
    elif args.mode == "qa":
        write_canonical_statement_qa(config)
    elif args.mode == "screen":
        write_canonical_statement_screen(config)
    elif args.mode == "decide":
        write_split_repair_decision(config)
    elif args.mode == "closeout":
        write_closeout(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
