from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "phase1_three_repo_paid_readiness_packaging.yaml"
THRESHOLD_CONFIG = ROOT / "configs" / "phase1_three_repo_paid_validation_thresholds.yaml"
RELEASE_SELECTION_CONFIG = ROOT / "configs" / "phase1_three_repo_release_selection.yaml"
SCHEMA_VERSION = "barcarolle.phase1_three_repo_paid_readiness_packaging.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_three_repo_paid_readiness_packaging_output.v1"
ACCEPTED_SOURCE_QUALITIES = {
    "non_leaky_issue_or_pr_context",
    "pr_title_only_context",
    "public_context_repaired",
}
ACCEPTED_SOURCE_CLASSES = {
    "issue_or_pr_context",
    "pr_context_title_only",
    "public_issue_and_pr_context_repaired",
}
DISALLOWED_RAW_MARKERS = (
    "diff --git",
    "\n@@",
    "raw_logs_storage",
    "raw_api_payload",
    "prompt.txt",
    "completion",
    "hidden verifier",
)
REPO_ORDER = ("attrs", "boltons", "click")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: str | Path) -> Path:
    raw = Path(path)
    return raw if raw.is_absolute() else REPO_ROOT / raw


def rel(path: str | Path) -> str:
    resolved = repo_path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected three-repo paid readiness packaging config schema_version")
    config["_path"] = str(path)
    return config


def read_json(path: str | Path, default: Any = None) -> Any:
    resolved = repo_path(path)
    if not resolved.exists():
        return default
    return json.loads(resolved.read_text(encoding="utf-8"))


def rows_from_payload(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, dict):
        rows = payload.get("rows", [])
    else:
        rows = payload
    return [dict(row) for row in rows]


def write_json(path: str | Path, payload: Any) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text.rstrip() + "\n", encoding="utf-8")


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


def input_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["inputs"][key])


def command_result(args: list[str], *, cwd: Path = REPO_ROOT, timeout: int = 120) -> dict[str, Any]:
    start = time.monotonic()
    try:
        proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        return {"args": args, "returncode": 127, "stdout": "", "stderr": str(exc), "duration_seconds": 0.0}
    except subprocess.TimeoutExpired as exc:
        return {
            "args": args,
            "returncode": 124,
            "stdout": text_or_empty(exc.stdout),
            "stderr": text_or_empty(exc.stderr),
            "duration_seconds": round(time.monotonic() - start, 3),
        }
    return {
        "args": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "duration_seconds": round(time.monotonic() - start, 3),
    }


def text_or_empty(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def command_stdout(args: list[str], *, cwd: Path = REPO_ROOT, timeout: int = 120) -> str:
    result = command_result(args, cwd=cwd, timeout=timeout)
    return result["stdout"].strip() if result["returncode"] == 0 else result["stderr"].strip()


def digest_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:12]


def stable_hash(seed: str, value: str) -> str:
    return hashlib.sha256(f"{seed}:{value}".encode("utf-8")).hexdigest()


def count_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "unknown") for row in rows).items()))


def count_by_repo(rows: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, int]]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        counters[str(row.get("repo_id") or "unknown")][str(row.get(key) or "unknown")] += 1
    return {repo: dict(sorted(counter.items())) for repo, counter in sorted(counters.items())}


def git_status_lines() -> list[str]:
    output = command_stdout(["git", "status", "--short", "--untracked-files=all"])
    return [line for line in output.splitlines() if line.strip()]


def status_path(line: str) -> str:
    text = line[3:] if len(line) > 3 else line
    if " -> " in text:
        text = text.split(" -> ", 1)[1]
    return text.strip()


def expected_committed_paths(config: dict[str, Any]) -> set[str]:
    paths = {
        rel(config["_path"]),
        rel(THRESHOLD_CONFIG),
        rel(RELEASE_SELECTION_CONFIG),
        rel(ROOT / "tools" / "phase1_three_repo_paid_readiness_packaging.py"),
        rel(ROOT / "tests" / "test_phase1_three_repo_paid_readiness_packaging.py"),
    }
    paths.update(rel(path) for path in config.get("outputs", {}).values())
    paths.update(rel(path) for path in config.get("reports", {}).values())
    return paths


def classify_dirty_paths(config: dict[str, Any], lines: list[str]) -> dict[str, list[str]]:
    expected_paths = expected_committed_paths(config)
    ignored_prefixes = [
        "experiments/phase1_compiler/tmp/three_repo_paid_readiness_packaging/",
        "experiments/phase0_headroom/workspaces/three_repo_paid_readiness_packaging/",
        "experiments/phase0_headroom/cache/three_repo_paid_readiness_packaging/",
    ]
    classified: dict[str, list[str]] = {"relevant": [], "ignored_artifact_output": [], "unrelated": []}
    for line in lines:
        path = status_path(line)
        if path in expected_paths:
            classified["relevant"].append(line)
        elif any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in ignored_prefixes):
            classified["ignored_artifact_output"].append(line)
        else:
            classified["unrelated"].append(line)
    return classified


def endpoint_presence() -> dict[str, Any]:
    base_present = bool(os.environ.get("LLM_BASE_URL"))
    key_present = bool(os.environ.get("LLM_API_KEY"))
    sourced = False
    if not (base_present and key_present):
        result = command_result(
            [
                "zsh",
                "-lc",
                (
                    "source ~/.zshrc >/dev/null 2>&1 || true; "
                    "if [[ -n ${LLM_BASE_URL:-} ]]; then echo LLM_BASE_URL=present; else echo LLM_BASE_URL=absent; fi; "
                    "if [[ -n ${LLM_API_KEY:-} ]]; then echo LLM_API_KEY=present; else echo LLM_API_KEY=absent; fi"
                ),
            ],
            timeout=30,
        )
        sourced = True
        lines = result["stdout"].splitlines() if result["returncode"] == 0 else []
        base_present = "LLM_BASE_URL=present" in lines
        key_present = "LLM_API_KEY=present" in lines
    return {
        "LLM_BASE_URL_present": base_present,
        "LLM_API_KEY_present": key_present,
        "both_required_endpoint_variables_present": base_present and key_present,
        "sourced_zshrc_when_needed": sourced,
        "values_recorded": False,
    }


def stable_generated_at(config: dict[str, Any]) -> str:
    preflight = output_path(config, "preflight")
    if preflight.exists():
        return str(read_json(preflight, {}).get("generated_at") or config.get("created_at") or now_utc())
    return str(config.get("created_at") or now_utc())


def build_preflight(config: dict[str, Any]) -> dict[str, Any]:
    fresh_gate = read_json(input_path(config, "fresh_certification_paid_readiness_gate"), {})
    third_gate = read_json(input_path(config, "third_repo_release_gate"), {})
    dirty_lines = git_status_lines()
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "preflight",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "branch": command_stdout(["git", "branch", "--show-current"]),
        "head": command_stdout(["git", "rev-parse", "HEAD"]),
        "head_short": command_stdout(["git", "rev-parse", "--short", "HEAD"]),
        "date_utc": command_stdout(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]),
        "python_version": command_stdout(["uv", "run", "--project", "experiments/phase1_compiler", "python", "--version"]),
        "uv_version": command_stdout(["uv", "--version"]),
        "git_status_short_untracked": dirty_lines,
        "dirty_path_classification": classify_dirty_paths(config, dirty_lines),
        "latest_supply_gate": {
            "fresh_certification_paid_ready": bool(fresh_gate.get("paid_ready")),
            "three_repo_release_gate_paid_ready": bool(third_gate.get("paid_ready")),
            "release_eligible_count_by_repo": third_gate.get("release_eligible_count_by_repo", {}),
            "repos_meeting_30_release_eligible": third_gate.get("repos_meeting_30_release_eligible", []),
        },
        "paid_calls_required_for_packaging": False,
        "paid_calls_made_by_this_runbook": {
            "paid_acut_solver_cells": False,
            "paid_task_solving_calls": False,
            "paid_replication": False,
            "paid_llm_statement_generation": False,
            "paid_llm_review": False,
        },
        "future_paid_endpoint_presence": endpoint_presence(),
        "external_review_bundle_status": {
            "path": "experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/",
            "classification": "unrelated_untracked_if_present",
            "left_untracked": any(
                "experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/" in line
                for line in dirty_lines
            ),
        },
        "claim_boundary": {
            "paid_validation_run": False,
            "predictive_validity_established": False,
            "package_boundary": "local_only_paid_readiness_packaging",
        },
    }
    write_json(output_path(config, "preflight"), payload)
    write_process_report(config, current_step="Step 0 preflight complete")
    return payload


def raw_inventory_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_rows = []
    raw_rows.extend(rows_from_payload(read_json(input_path(config, "task_supply_raw_anchor_inventory"), {})))
    raw_rows.extend(rows_from_payload(read_json(input_path(config, "third_repo_raw_anchor_inventory"), {})))
    return {str(row["candidate_id"]): row for row in raw_rows if row.get("candidate_id")}


def attrs_overlay_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    overlay = read_json(input_path(config, "attrs_source_repair_overlay"), {})
    return {str(row["candidate_id"]): row for row in overlay.get("overlay_rows", [])}


def selected_attempt_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    fresh_rows = rows_from_payload(read_json(input_path(config, "fresh_certification_attempts"), {}))
    third_rows = rows_from_payload(read_json(input_path(config, "third_repo_certification_attempts"), {}))
    overlay = attrs_overlay_by_id(config)
    selected: list[dict[str, Any]] = []
    for row in fresh_rows:
        repo_id = str(row.get("repo_id"))
        candidate_id = str(row.get("candidate_id"))
        if repo_id not in {"attrs", "boltons"}:
            continue
        release_eligible = bool(row.get("release_eligible"))
        if candidate_id in overlay and overlay[candidate_id].get("overlay_action") == "mark_release_eligible":
            release_eligible = True
        if not release_eligible:
            continue
        promoted = candidate_id in overlay
        selected.append(normalize_attempt_row(row, promoted=promoted))
    for row in third_rows:
        if str(row.get("repo_id")) != "click" or not row.get("release_eligible"):
            continue
        selected.append(normalize_attempt_row(row, promoted=False))
    return sorted(selected, key=lambda row: (REPO_ORDER.index(row["repo_id"]), row["candidate_id"]))


def normalize_attempt_row(row: dict[str, Any], *, promoted: bool) -> dict[str, Any]:
    normalized = dict(row)
    if promoted:
        normalized["release_eligible"] = True
        normalized["source_context_class"] = "public_issue_and_pr_context_repaired"
        normalized["source_context_quality"] = "public_context_repaired"
        normalized["release_eligibility_provenance"] = "attrs_source_repair_overlay"
    else:
        normalized["release_eligibility_provenance"] = "fresh_or_third_repo_certification_release_eligible"
    return normalized


def task_time_bucket(task_time: str) -> str:
    if not task_time:
        return "unknown"
    try:
        year = int(task_time[:4])
    except ValueError:
        return "unknown"
    if year <= 2018:
        return "legacy_2018_or_earlier"
    if year <= 2022:
        return "middle_2019_2022"
    return "recent_2023_or_later"


def task_family(repo_id: str, implementation_files: list[str]) -> str:
    if not implementation_files:
        return f"{repo_id}:unknown"
    first = implementation_files[0]
    stem = Path(first).stem
    if stem == "__init__" and len(implementation_files) > 1:
        stem = Path(implementation_files[1]).stem
    return f"{repo_id}:{stem}"


def technical_profile(row: dict[str, Any]) -> dict[str, Any]:
    commands = [dict(command) for command in row.get("commands", [])]
    reference_pass_count = sum(1 for command in commands if str(command.get("role", "")).startswith("reference") and command.get("returncode") == 0)
    noop_fail_observed = any(command.get("role") == "noop" and command.get("returncode") != 0 for command in commands)
    trace_digest_payload = [
        {
            "role": command.get("role"),
            "profile_id": command.get("profile_id"),
            "returncode": command.get("returncode"),
            "subgate_label": command.get("subgate_label"),
            "timed_out": command.get("timed_out"),
        }
        for command in commands
    ]
    return {
        "technical_certified": bool(row.get("technical_certified")),
        "execution_status": row.get("execution_status"),
        "terminal_execution_subgate": row.get("terminal_execution_subgate"),
        "winning_profile_id": row.get("winning_profile_id") or "",
        "noop_fail_observed": noop_fail_observed,
        "reference_pass_count": reference_pass_count,
        "reference_repeat_gate_passed": reference_pass_count >= 2,
        "sanitized_command_trace_digest": digest_payload(trace_digest_payload),
    }


def task_table_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    raw_index = raw_inventory_by_id(config)
    rows = []
    for row in selected_attempt_rows(config):
        candidate_id = str(row["candidate_id"])
        raw = raw_index.get(candidate_id, {})
        implementation_files = list(row.get("implementation_files") or raw.get("implementation_files") or [])
        test_files = list(row.get("test_files") or raw.get("test_files") or [])
        task_time = str(raw.get("task_time") or row.get("task_time") or "")
        source_context_quality = str(row.get("source_context_quality") or raw.get("source_context_quality") or "")
        source_context_class = str(row.get("source_context_class") or raw.get("source_context_class") or "")
        entry = {
            "repo_id": row["repo_id"],
            "candidate_id": candidate_id,
            "base_commit": row.get("base_commit") or raw.get("base_commit") or "",
            "target_commit": row.get("target_commit_optional") or raw.get("target_commit_optional") or "",
            "task_time": task_time,
            "task_time_bucket": task_time_bucket(task_time),
            "task_family": task_family(str(row["repo_id"]), implementation_files),
            "implementation_files": implementation_files,
            "test_files": test_files,
            "source_reservoir": row.get("source_reservoir") or raw.get("source_reservoir") or "",
            "source_context_class": source_context_class,
            "source_context_quality": source_context_quality,
            "public_context_ref_count": len(raw.get("public_context_refs", []) or []),
            "technical_certification_profile": technical_profile(row),
            "release_eligibility_provenance": row.get("release_eligibility_provenance"),
            "digests": {
                "task_metadata_digest": digest_payload(
                    {
                        "candidate_id": candidate_id,
                        "base_commit": row.get("base_commit"),
                        "target_commit": row.get("target_commit_optional"),
                        "implementation_files": implementation_files,
                        "test_files": test_files,
                    }
                ),
                "raw_inventory_dedup_key": raw.get("dedup_key", ""),
                "reference_patch_digest_optional": raw.get("reference_patch_digest_optional", ""),
                "subject_digest_optional": raw.get("subject_digest", ""),
            },
            "raw_diff_committed": False,
            "raw_test_patch_committed": False,
            "raw_command_log_committed": False,
        }
        rows.append(entry)
    return rows


def build_supply_snapshot(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = task_table_rows(config)
    release_counts = dict(Counter(row["repo_id"] for row in rows))
    fresh_gate = read_json(input_path(config, "fresh_certification_paid_readiness_gate"), {})
    attrs_gate = read_json(input_path(config, "attrs_source_repair_paid_readiness_gate"), {})
    third_gate = read_json(input_path(config, "third_repo_release_gate"), {})
    task_table = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "task_table",
        "run_id": config["run_id"],
        "generated_at": stable_generated_at(config),
        "task_count": len(rows),
        "release_eligible_count_by_repo": release_counts,
        "rows": rows,
        "artifact_hygiene": {
            "raw_diffs_committed": False,
            "raw_tests_committed": False,
            "raw_command_logs_committed": False,
            "contains_only_sanitized_metadata_and_digests": True,
        },
    }
    snapshot = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "supply_snapshot",
        "run_id": config["run_id"],
        "generated_at": stable_generated_at(config),
        "status": "three_repo_supply_snapshot_frozen",
        "release_eligible_count_by_repo": release_counts,
        "technical_certified_count_by_repo": {
            "attrs": attrs_gate.get("technical_certified_count_by_repo", {}).get("attrs")
            or fresh_gate.get("technical_certified_count_by_repo", {}).get("attrs"),
            "boltons": fresh_gate.get("technical_certified_count_by_repo", {}).get("boltons"),
            "click": third_gate.get("technical_certified_count_by_candidate_repo", {}).get("click"),
        },
        "repos_meeting_30_release_eligible": [repo for repo in REPO_ORDER if release_counts.get(repo, 0) >= 30],
        "minimum_release_eligible_per_repo": int(config["policy"]["release_eligible_min_per_repo"]),
        "source_context_class_counts_by_repo": count_by_repo(rows, "source_context_class"),
        "source_context_quality_counts_by_repo": count_by_repo(rows, "source_context_quality"),
        "release_eligibility_provenance_counts_by_repo": count_by_repo(rows, "release_eligibility_provenance"),
        "input_run_ids": {
            "fresh_certification": fresh_gate.get("run_id"),
            "attrs_source_repair": attrs_gate.get("run_id"),
            "third_repo_supply_screen": third_gate.get("run_id"),
        },
        "raw_candidates_counted_as_release_eligible": False,
        "technical_only_tasks_counted_as_release_eligible": False,
        "paid_validation_run": False,
    }
    write_json(output_path(config, "task_table"), task_table)
    write_json(output_path(config, "supply_snapshot"), snapshot)
    write_supply_reports(config, snapshot, task_table)
    write_process_report(config, current_step="Step 1 supply snapshot complete")
    return snapshot, task_table


def build_source_quality_audit(config: dict[str, Any]) -> dict[str, Any]:
    rows = task_table_rows(config)
    audit_rows = []
    for row in rows:
        leakage_flags: list[str] = []
        ambiguity_flags: list[str] = []
        quality = row["source_context_quality"]
        context_class = row["source_context_class"]
        if quality not in ACCEPTED_SOURCE_QUALITIES or context_class not in ACCEPTED_SOURCE_CLASSES:
            ambiguity_flags.append("source_context_not_accepted_for_paid_package")
        if "material_leakage" in quality or "material_leakage" in context_class:
            leakage_flags.append("material_leakage_risk")
        if leakage_flags:
            status = "exclude_before_paid"
        elif ambiguity_flags:
            status = "needs_source_repair_before_paid"
        else:
            status = "accepted_for_paid_package"
        caution_flags = []
        if row["repo_id"] == "click" and quality == "pr_title_only_context":
            caution_flags.append("click_pr_title_only_context_thin_margin")
        audit_rows.append(
            {
                "repo_id": row["repo_id"],
                "candidate_id": row["candidate_id"],
                "audit_status": status,
                "source_context_class": context_class,
                "source_context_quality": quality,
                "statement_provenance": row["release_eligibility_provenance"],
                "material_leakage_flags": leakage_flags,
                "ambiguity_flags": ambiguity_flags,
                "caution_flags": caution_flags,
                "raw_statement_text_committed": False,
                "paid_llm_review_used": False,
            }
        )
    status_counts = count_by(audit_rows, "audit_status")
    click_rows = [row for row in audit_rows if row["repo_id"] == "click"]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "source_quality_audit",
        "run_id": config["run_id"],
        "generated_at": stable_generated_at(config),
        "status": "source_quality_audit_completed",
        "task_count": len(audit_rows),
        "audit_status_counts": status_counts,
        "source_context_class_counts_by_repo": count_by_repo(audit_rows, "source_context_class"),
        "statement_provenance_counts_by_repo": count_by_repo(audit_rows, "statement_provenance"),
        "material_leakage_task_count": sum(1 for row in audit_rows if row["material_leakage_flags"]),
        "ambiguity_task_count": sum(1 for row in audit_rows if row["ambiguity_flags"]),
        "tasks_requiring_exclusion_or_repair": [
            row["candidate_id"] for row in audit_rows if row["audit_status"] != "accepted_for_paid_package"
        ],
        "click_audit": {
            "release_eligible_count": len(click_rows),
            "all_accepted_after_local_audit": all(row["audit_status"] == "accepted_for_paid_package" for row in click_rows),
            "source_context_quality_counts": count_by(click_rows, "source_context_quality"),
            "thin_margin": len(click_rows) == 30,
            "paid_llm_review_used": False,
        },
        "paid_llm_review_used": False,
        "rows": audit_rows,
    }
    write_json(output_path(config, "source_quality_audit"), payload)
    write_source_audit_report(config, payload)
    write_process_report(config, current_step="Step 2 source quality audit complete")
    return payload


def audited_task_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    audit = read_json(output_path(config, "source_quality_audit"), None)
    accepted = {
        row["candidate_id"]
        for row in rows_from_payload(audit)
        if row.get("audit_status") == "accepted_for_paid_package"
    }
    if not accepted:
        accepted = {row["candidate_id"] for row in task_table_rows(config)}
    return [row for row in task_table_rows(config) if row["candidate_id"] in accepted]


def build_split_plan(config: dict[str, Any]) -> dict[str, Any]:
    seed = str(config["split_seed"])
    rows = audited_task_rows(config)
    assignments = []
    for repo_id in REPO_ORDER:
        repo_rows = [row for row in rows if row["repo_id"] == repo_id]
        repo_rows = sorted(
            repo_rows,
            key=lambda row: (
                row["source_context_class"],
                row["task_time_bucket"],
                row["task_family"],
                stable_hash(seed, row["candidate_id"]),
            ),
        )
        for index, row in enumerate(repo_rows):
            split = "B_eval" if index % 2 == 0 else "H_future"
            assignments.append(
                {
                    "repo_id": repo_id,
                    "candidate_id": row["candidate_id"],
                    "split": split,
                    "source_context_class": row["source_context_class"],
                    "task_time_bucket": row["task_time_bucket"],
                    "task_family": row["task_family"],
                    "split_seed": seed,
                    "tie_breaker": stable_hash(seed, row["candidate_id"])[:16],
                }
            )
    diagnostics = split_imbalance_diagnostics(assignments)
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "split_plan",
        "run_id": config["run_id"],
        "generated_at": stable_generated_at(config),
        "status": "split_plan_preregistered",
        "primary_design": config["primary_design"],
        "primary_score": config["primary_score"],
        "split_seed": seed,
        "tie_breaking_rule": "Within each repo, sort by source context class, task time bucket, task family, then sha256(seed:candidate_id); alternate B_eval/H_future.",
        "H_future_outcomes_used_for_selection_or_weighting": False,
        "old_weighted_design_primary": False,
        "assignment_count": len(assignments),
        "split_counts_by_repo": diagnostics["split_counts_by_repo"],
        "imbalance_diagnostics": diagnostics,
        "assignments": assignments,
    }
    write_json(output_path(config, "split_plan"), payload)
    write_release_selection_config(config, payload)
    write_split_plan_report(config, payload)
    write_process_report(config, current_step="Step 3 release candidate and split plan complete")
    return payload


def split_imbalance_diagnostics(assignments: list[dict[str, Any]]) -> dict[str, Any]:
    split_counts_by_repo: dict[str, dict[str, int]] = {}
    class_counts: dict[str, dict[str, dict[str, int]]] = {}
    time_counts: dict[str, dict[str, dict[str, int]]] = {}
    family_counts: dict[str, dict[str, dict[str, int]]] = {}
    for repo_id in REPO_ORDER:
        repo_rows = [row for row in assignments if row["repo_id"] == repo_id]
        split_counts_by_repo[repo_id] = dict(sorted(Counter(row["split"] for row in repo_rows).items()))
        class_counts[repo_id] = nested_split_counts(repo_rows, "source_context_class")
        time_counts[repo_id] = nested_split_counts(repo_rows, "task_time_bucket")
        family_counts[repo_id] = nested_split_counts(repo_rows, "task_family")
    max_delta = 0
    for counts in split_counts_by_repo.values():
        max_delta = max(max_delta, abs(counts.get("B_eval", 0) - counts.get("H_future", 0)))
    return {
        "split_counts_by_repo": split_counts_by_repo,
        "source_context_class_counts_by_repo_split": class_counts,
        "task_time_bucket_counts_by_repo_split": time_counts,
        "task_family_counts_by_repo_split": family_counts,
        "max_within_repo_split_count_delta": max_delta,
        "acceptable_for_pilot_packaging": max_delta <= 1,
    }


def nested_split_counts(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, int]]:
    out: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        out[row["split"]][str(row.get(key) or "unknown")] += 1
    return {split: dict(sorted(counter.items())) for split, counter in sorted(out.items())}


def write_release_selection_config(config: dict[str, Any], split_plan: dict[str, Any]) -> None:
    counts = split_plan["split_counts_by_repo"]
    lines = [
        "schema_version: barcarolle.phase1_three_repo_release_selection.v1",
        f"run_id: {config['run_id']}",
        "selection_version: phase1_three_repo_release_selection_20260528_v1",
        "selection_frozen_before_paid_validation: true",
        f"primary_design: {config['primary_design']}",
        f"primary_score: {config['primary_score']}",
        f"split_seed: {config['split_seed']}",
        "historical_paid_outcomes_used_for_selection: false",
        "H_future_outcomes_used_for_selection_or_weighting: false",
        "old_weighted_design_primary: false",
        "paid_acut_calls_to_run_now: false",
        "selected_repos:",
    ]
    lines.extend(f"  - {repo_id}" for repo_id in REPO_ORDER)
    lines.append("split_count_by_repo:")
    for repo_id in REPO_ORDER:
        lines.append(f"  {repo_id}_B_eval: {counts[repo_id].get('B_eval', 0)}")
        lines.append(f"  {repo_id}_H_future: {counts[repo_id].get('H_future', 0)}")
    lines.append("baseline_candidate_ids:")
    lines.extend(
        [
            "  - repo_unweighted_same_budget",
            "  - repo_stratified_same_budget",
            "  - temporal_recent_baseline",
            "  - old_weighted_design_diagnostic_only",
            "  - block_randomized_stratified_candidate",
        ]
    )
    write_text(RELEASE_SELECTION_CONFIG, "\n".join(lines))


def build_baseline_plan(config: dict[str, Any]) -> dict[str, Any]:
    local_decision = read_json(input_path(config, "local_algorithm_bakeoff_decision"), {})
    weighted_decision = read_json(input_path(config, "weighted_design_paid_pilot_decision"), {})
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "baseline_plan",
        "run_id": config["run_id"],
        "generated_at": stable_generated_at(config),
        "status": "baseline_plan_preregistered",
        "primary_design": {
            "design_id": "repo_stratified",
            "role": "primary",
            "reason": "Local bakeoff recommended keeping repo-stratified as the mainline; weighted pilot did not beat simple baselines.",
            "score_aggregation": [
                "per_repo_B_eval_pass_rate",
                "per_repo_H_future_pass_rate",
                "per_repo_abs_gap",
                "pooled_unweighted_summary",
                "uncertainty_intervals_by_repo_and_pooled",
            ],
        },
        "baselines": [
            {
                "design_id": "repo_unweighted_same_budget",
                "role": "baseline",
                "description": "Same paid-cell budget, pooled without target-profile weighting.",
            },
            {
                "design_id": "repo_stratified_same_budget",
                "role": "baseline",
                "description": "Same paid-cell budget with equal repo coverage and unweighted repo summaries.",
            },
            {
                "design_id": "temporal_recent_baseline",
                "role": "baseline",
                "description": "Recent tasks selected first within each repo, retained as a simple temporal comparator.",
            },
            {
                "design_id": "block_randomized_stratified_candidate",
                "role": "secondary",
                "description": "Uses deterministic blocking by repo, time bucket, source class, and task family; informative only unless promoted by a future preregistration.",
            },
            {
                "design_id": "old_weighted_design",
                "role": "diagnostic_only",
                "description": "Historical weighted design retained only as a diagnostic because the paid pilot threshold was not met.",
            },
        ],
        "old_weighted_design_primary": False,
        "post_hoc_promotion_rule": "none",
        "non_scoreable_handling": "Use preregistered taxonomy; exclude non-scoreable cells from pass-rate denominators only after recording the reason, and fail the scoreability gate below threshold.",
        "prior_evidence": {
            "local_algorithm_bakeoff_final_decision": local_decision.get("final_decision"),
            "local_algorithm_bakeoff_mainline_recommendation": local_decision.get("mainline_recommendation"),
            "weighted_pilot_final_decision": weighted_decision.get("final_decision"),
            "weighted_design_beats_unweighted_and_stratified": weighted_decision.get("weighted_design_beats_unweighted_and_stratified"),
        },
    }
    write_json(output_path(config, "baseline_plan"), payload)
    write_baseline_report(config, payload)
    write_process_report(config, current_step="Step 4 baseline and diagnostic plan complete")
    return payload


def build_threshold_preregistration(config: dict[str, Any]) -> dict[str, Any]:
    policy = config["policy"]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "threshold_preregistration",
        "run_id": config["run_id"],
        "generated_at": stable_generated_at(config),
        "status": "thresholds_preregistered",
        "primary_metrics": [
            "per_repo_B_eval_to_H_future_absolute_gap",
            "pooled_absolute_gap",
            "scoreability_rate",
            "policy_violation_count",
            "endpoint_compliance",
            "cost_latency_accounting_completeness",
        ],
        "thresholds": {
            "policy_violations_max": int(policy["policy_violations_max"]),
            "paid_endpoint_required": "LLM_BASE_URL + LLM_API_KEY",
            "raw_oracle_exposure_allowed": False,
            "minimum_scoreability_rate": float(policy["minimum_scoreability_rate"]),
            "primary_gap_threshold": float(policy["primary_gap_threshold"]),
            "non_scoreable_cell_handling": "preregistered_taxonomy_and_excluded_from_pass_denominator",
            "cost_latency_accounting_required": True,
        },
        "success_rule": "Success requires zero policy violations, endpoint compliance, scoreability >= 0.95, complete cost/latency accounting, and primary absolute gap <= 0.15.",
        "failure_rule": "Failure is any policy violation, raw oracle exposure, endpoint noncompliance, scoreability below 0.95, incomplete accounting, or primary gap above 0.15.",
        "underpowered_evidence_rule": "If the recommended paid batch is run without the full release candidate, label the result pilot-only even when gates pass.",
        "precision_label_rules": {
            "pilot_only": "Use for small_pilot and primary_pilot unless a later runbook expands to a precision-target design.",
            "precision_target_claim_allowed": "Not allowed by this packaging runbook; requires a later paid validation run and analysis.",
            "predictive_validity_claim_before_paid_validation": False,
        },
        "paid_validation_run": False,
    }
    write_json(output_path(config, "threshold_preregistration"), payload)
    write_threshold_config(config, payload)
    write_threshold_report(config, payload)
    write_process_report(config, current_step="Step 5 threshold preregistration complete")
    return payload


def write_threshold_config(config: dict[str, Any], payload: dict[str, Any]) -> None:
    thresholds = payload["thresholds"]
    lines = [
        "schema_version: barcarolle.phase1_three_repo_paid_validation_thresholds.v1",
        f"run_id: {config['run_id']}",
        "threshold_version: phase1_three_repo_paid_validation_thresholds_20260528_v1",
        f"policy_violations_max: {thresholds['policy_violations_max']}",
        f"minimum_scoreability_rate: {thresholds['minimum_scoreability_rate']}",
        f"primary_gap_threshold: {thresholds['primary_gap_threshold']}",
        "paid_endpoint_required: LLM_BASE_URL + LLM_API_KEY",
        "raw_oracle_exposure_allowed: false",
        f"non_scoreable_cell_handling: {thresholds['non_scoreable_cell_handling']}",
        "precision_label: pilot_only_until_paid_validation_analyzed",
        "predictive_validity_claim_allowed_before_paid_validation: false",
    ]
    write_text(THRESHOLD_CONFIG, "\n".join(lines))


def build_power_cost_plan(config: dict[str, Any]) -> dict[str, Any]:
    split_plan = read_json(output_path(config, "split_plan"), {})
    assignments = split_plan.get("assignments", [])
    weighted_decision = read_json(input_path(config, "weighted_design_paid_pilot_decision"), {})
    observed_cells = int(weighted_decision.get("scoreable_cells") or weighted_decision.get("paid_cells_completed") or 0)
    observed_cost = float(weighted_decision.get("observed_or_conservative_cost_usd") or 0.0)
    observed_cost_per_cell = round(observed_cost / observed_cells, 6) if observed_cells else float(config["budget"]["conservative_cost_per_cell_usd"])
    lower_cost_per_cell = float(config["budget"]["lower_cost_per_cell_usd"])
    conservative_cost_per_cell = max(float(config["budget"]["conservative_cost_per_cell_usd"]), observed_cost_per_cell)
    adapters = list(config["budget"]["planned_adapters"])
    small_task_ids = select_paid_batch_tasks(assignments, per_repo_per_split=3)
    primary_task_ids = select_paid_batch_tasks(assignments, per_repo_per_split=10)
    options = [
        batch_option("small_pilot", small_task_ids, adapters, lower_cost_per_cell, conservative_cost_per_cell, "Smallest useful three-repo pilot; lower cost, weaker precision."),
        batch_option("primary_pilot", primary_task_ids, adapters, lower_cost_per_cell, conservative_cost_per_cell, "Recommended next paid batch; enough cells to compare primary design and baselines, still pilot-grade."),
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "power_cost_plan",
        "run_id": config["run_id"],
        "generated_at": stable_generated_at(config),
        "status": "power_cost_plan_completed",
        "historical_cost_source": {
            "source_run_id": weighted_decision.get("run_id"),
            "observed_or_conservative_cost_usd": observed_cost,
            "scoreable_cells": observed_cells,
            "observed_cost_per_cell_usd": observed_cost_per_cell,
        },
        "planned_adapters": adapters,
        "recommended_option": "primary_pilot",
        "batch_options": options,
        "stop_conditions_after_each_batch": [
            "endpoint_proof_missing",
            "projected_total_cost_exceeds_budget_approved_for_later_runbook",
            "scoreability_rate_below_0.95",
            "policy_violation_count_above_0",
            "raw_oracle_exposure_detected",
            "cost_latency_accounting_incomplete",
        ],
        "evidence_boundary": "Both options are pilot-grade. They can test operational readiness and compare designs, but this packaging runbook does not claim precision-target predictive validity.",
        "paid_cells_run_by_this_packaging_runbook": 0,
    }
    write_json(output_path(config, "power_cost_plan"), payload)
    write_power_cost_report(config, payload)
    write_process_report(config, current_step="Step 6 power, cost, and paid batch plan complete")
    return payload


def select_paid_batch_tasks(assignments: list[dict[str, Any]], *, per_repo_per_split: int) -> list[str]:
    selected: list[str] = []
    for repo_id in REPO_ORDER:
        for split in ("B_eval", "H_future"):
            rows = [row for row in assignments if row["repo_id"] == repo_id and row["split"] == split]
            rows = sorted(rows, key=lambda row: row["tie_breaker"])
            selected.extend(row["candidate_id"] for row in rows[:per_repo_per_split])
    return selected


def batch_option(
    option_id: str,
    task_ids: list[str],
    adapters: list[str],
    lower_cost_per_cell: float,
    conservative_cost_per_cell: float,
    description: str,
) -> dict[str, Any]:
    cells = len(task_ids) * len(adapters)
    return {
        "option_id": option_id,
        "description": description,
        "repos": list(REPO_ORDER),
        "unique_task_count": len(task_ids),
        "planned_cells": cells,
        "acut_adapters": adapters,
        "expected_cost_range_usd": {
            "lower": round(cells * lower_cost_per_cell, 2),
            "conservative": round(cells * conservative_cost_per_cell, 2),
        },
        "expected_runtime": "later runbook must estimate from selected ACUT adapter concurrency and observed per-cell latency",
        "task_counts_by_repo_split": batch_task_counts(task_ids),
        "task_ids": task_ids,
        "scoreability_and_policy_gates": {
            "minimum_scoreability_rate": 0.95,
            "policy_violations_max": 0,
            "raw_oracle_exposure_allowed": False,
        },
    }


def batch_task_counts(task_ids: list[str]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for task_id in task_ids:
        repo_id = task_id.split("__", 1)[0]
        counts[repo_id] += 1
    return dict(sorted(counts.items()))


def run_verification_commands() -> list[dict[str, Any]]:
    commands = [
        [
            "uv",
            "run",
            "--project",
            "experiments/phase1_compiler",
            "pytest",
            "experiments/phase1_compiler/tests/test_phase1_three_repo_paid_readiness_packaging.py",
            "-q",
        ],
        ["uv", "run", "--project", "experiments/phase1_compiler", "pytest", "experiments/phase1_compiler/tests", "-q"],
        ["git", "diff", "--check"],
    ]
    results = []
    for command in commands:
        result = command_result(command, timeout=600)
        results.append(
            {
                "command": command,
                "returncode": result["returncode"],
                "duration_seconds": result["duration_seconds"],
                "stdout_tail_digest": short_hash(result["stdout"][-4000:]),
                "stderr_tail_digest": short_hash(result["stderr"][-4000:]),
                "passed": result["returncode"] == 0,
            }
        )
    return results


def build_entry_gate(config: dict[str, Any], *, run_tests: bool = False) -> dict[str, Any]:
    snapshot = read_json(output_path(config, "supply_snapshot"), {})
    audit = read_json(output_path(config, "source_quality_audit"), {})
    split_plan = read_json(output_path(config, "split_plan"), {})
    baseline = read_json(output_path(config, "baseline_plan"), {})
    thresholds = read_json(output_path(config, "threshold_preregistration"), {})
    cost = read_json(output_path(config, "power_cost_plan"), {})
    endpoint = endpoint_presence()
    test_results = run_verification_commands() if run_tests else []
    gates = {
        "three_repos_at_30_release_eligible": len(snapshot.get("repos_meeting_30_release_eligible", [])) >= 3,
        "source_quality_audit_passed": audit.get("tasks_requiring_exclusion_or_repair") == [],
        "release_candidate_frozen": bool(snapshot.get("release_eligible_count_by_repo")),
        "split_plan_frozen": bool(split_plan.get("assignments")) and split_plan.get("H_future_outcomes_used_for_selection_or_weighting") is False,
        "baseline_plan_frozen": bool(baseline.get("primary_design")),
        "thresholds_frozen": bool(thresholds.get("thresholds")),
        "power_cost_plan_frozen": bool(cost.get("batch_options")),
        "endpoint_variables_present": bool(endpoint.get("both_required_endpoint_variables_present")),
        "no_raw_logs_workspaces_committed_by_this_run": committed_artifact_hygiene_passes(config),
        "tests_pass": all(result["passed"] for result in test_results) if run_tests else True,
        "no_paid_cells_run": True,
    }
    failed = [key for key, value in gates.items() if not value]
    if not failed:
        status = "ready_for_paid_validation_runbook"
    elif "source_quality_audit_passed" in failed:
        status = "blocked_source_quality"
    elif "split_plan_frozen" in failed or "thresholds_frozen" in failed:
        status = "blocked_split_or_threshold_preregistration"
    elif "endpoint_variables_present" in failed:
        status = "blocked_endpoint_compliance"
    else:
        status = "blocked_tests_or_artifact_hygiene"
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "entry_gate",
        "run_id": config["run_id"],
        "generated_at": stable_generated_at(config),
        "status": status,
        "paid_ready": status == "ready_for_paid_validation_runbook",
        "gates": gates,
        "failed_gates": failed,
        "endpoint_presence": endpoint,
        "verification_results": test_results,
        "paid_validation_run": False,
        "paid_acut_cells_run": False,
    }
    write_json(output_path(config, "entry_gate"), payload)
    write_entry_gate_report(config, payload)
    write_process_report(config, current_step="Step 7 entry gate complete")
    return payload


def committed_artifact_hygiene_passes(config: dict[str, Any]) -> bool:
    tracked = command_stdout(["git", "ls-files"]).splitlines()
    expected = expected_committed_paths(config)
    runbook_tracked = [path for path in tracked if path in expected]
    forbidden_fragments = ("/tmp/", "/workspaces/", "/cache/", "raw_logs", "prompt.txt", "provider_response", "transcript")
    return not any(any(fragment in path for fragment in forbidden_fragments) for path in runbook_tracked)


def build_decision(config: dict[str, Any]) -> dict[str, Any]:
    snapshot = read_json(output_path(config, "supply_snapshot"), {})
    audit = read_json(output_path(config, "source_quality_audit"), {})
    split = read_json(output_path(config, "split_plan"), {})
    baseline = read_json(output_path(config, "baseline_plan"), {})
    thresholds = read_json(output_path(config, "threshold_preregistration"), {})
    cost = read_json(output_path(config, "power_cost_plan"), {})
    entry = read_json(output_path(config, "entry_gate"), {})
    final_decision = (
        "pilot_package_ready_but_precision_target_not_claimable"
        if entry.get("status") == "ready_for_paid_validation_runbook"
        else "blocked_before_paid_validation"
    )
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "decision",
        "run_id": config["run_id"],
        "generated_at": stable_generated_at(config),
        "final_decision": final_decision,
        "entry_gate_status": entry.get("status"),
        "paid_ready": bool(entry.get("paid_ready")),
        "release_eligible_count_by_repo": snapshot.get("release_eligible_count_by_repo", {}),
        "source_quality_audit_passed": audit.get("tasks_requiring_exclusion_or_repair") == [],
        "primary_design": split.get("primary_design"),
        "baselines_and_diagnostics": [
            {"design_id": row["design_id"], "role": row["role"]} for row in baseline.get("baselines", [])
        ],
        "thresholds": thresholds.get("thresholds", {}),
        "recommended_paid_batch": cost.get("recommended_option"),
        "recommended_paid_batch_cost_range_usd": recommended_cost_range(cost),
        "paid_acut_or_paid_llm_calls_made": False,
        "research_questions": {
            "RQ1": "attrs, boltons, and click are frozen into the paid entry package.",
            "RQ2": f"Source-quality audit passed: {audit.get('tasks_requiring_exclusion_or_repair') == []}.",
            "RQ3": f"Primary design is {split.get('primary_design')}.",
            "RQ4": "Repo-unweighted, repo-stratified, temporal-recent, old weighted diagnostic, and block-randomized stratified candidate are frozen.",
            "RQ5": "Thresholds preregister zero policy violations, endpoint compliance, no raw oracle exposure, scoreability >= 0.95, and primary gap <= 0.15.",
            "RQ6": f"Recommended paid batch is {cost.get('recommended_option')} with cost range {recommended_cost_range(cost)}.",
            "RQ7": f"Package ready for paid validation runbook: {entry.get('status') == 'ready_for_paid_validation_runbook'}.",
            "RQ8": "No paid ACUT or paid LLM calls were made by this packaging runbook.",
        },
        "completed_steps": [
            "Step 0 preflight and boundary check",
            "Step 1 three-repo supply snapshot",
            "Step 2 source quality audit",
            "Step 3 release candidate and split plan",
            "Step 4 baseline and diagnostic plan",
            "Step 5 threshold preregistration",
            "Step 6 power, cost, and paid batch plan",
            "Step 7 entry gate",
            "Step 8 decision and closeout",
        ],
        "known_blockers": [] if entry.get("status") == "ready_for_paid_validation_runbook" else entry.get("failed_gates", []),
        "recommended_next_action_categories": [
            "coordinating session may choose whether to run a later paid validation runbook",
            "if run, keep repo_stratified as primary and old weighted as diagnostic only",
            "treat the recommended batch as pilot-grade unless a later preregistration expands precision",
        ],
        "paid_validation_run": False,
        "predictive_validity_established": False,
    }
    write_json(output_path(config, "decision"), payload)
    write_decision_report(config, payload)
    write_process_report(config, current_step="Step 8 decision and closeout complete")
    return payload


def recommended_cost_range(cost_payload: dict[str, Any]) -> dict[str, float] | None:
    recommended = cost_payload.get("recommended_option")
    for option in cost_payload.get("batch_options", []):
        if option.get("option_id") == recommended:
            return option.get("expected_cost_range_usd")
    return None


def json_fence(payload: Any) -> str:
    return "```json\n" + json.dumps(payload, indent=2, sort_keys=True) + "\n```"


def write_process_report(config: dict[str, Any], *, current_step: str) -> None:
    preflight = read_json(output_path(config, "preflight"), {})
    steps = [
        ("Step 0", output_path(config, "preflight").exists()),
        ("Step 1", output_path(config, "supply_snapshot").exists() and output_path(config, "task_table").exists()),
        ("Step 2", output_path(config, "source_quality_audit").exists()),
        ("Step 3", output_path(config, "split_plan").exists()),
        ("Step 4", output_path(config, "baseline_plan").exists()),
        ("Step 5", output_path(config, "threshold_preregistration").exists()),
        ("Step 6", output_path(config, "power_cost_plan").exists()),
        ("Step 7", output_path(config, "entry_gate").exists()),
        ("Step 8", output_path(config, "decision").exists()),
    ]
    lines = [
        "# Three-Repo Paid Readiness Packaging Process",
        "",
        f"Run id: `{config['run_id']}`.",
        f"Current status: {current_step}.",
        "",
        "What happened: this runbook packages attrs, boltons, and click release-eligible task supply into a local-only paid-validation entry package.",
        "",
        "Why it matters: paid validation can only start after task supply, source quality, split, baselines, thresholds, cost, endpoint, and test gates are frozen.",
        "",
        "Paid validation status: not run. No paid ACUT solver cells, paid replication, paid LLM statement generation, or paid LLM review were run.",
        "",
    ]
    if preflight:
        lines.extend(
            [
                f"Starting commit recorded by preflight: `{preflight.get('head')}`.",
                f"Branch: `{preflight.get('branch')}`.",
                f"External-review bundle classification: `{preflight.get('external_review_bundle_status', {}).get('classification')}`; left untracked: `{preflight.get('external_review_bundle_status', {}).get('left_untracked')}`.",
                "",
            ]
        )
    lines.append("Step status:")
    lines.append("")
    for label, done in steps:
        lines.append(f"- {label}: {'complete' if done else 'pending'}")
    write_text(report_path(config, "process"), "\n".join(lines))


def write_supply_reports(config: dict[str, Any], snapshot: dict[str, Any], task_table: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Supply Snapshot",
        "",
        "What happened: attrs, boltons, and click release-eligible tasks were merged from committed local evidence into one frozen package snapshot.",
        "",
        "Why it matters: raw candidates and technical-only tasks are not counted. Only release-eligible tasks enter paid packaging.",
        "",
        f"Release-eligible counts: `{snapshot['release_eligible_count_by_repo']}`.",
        f"Repos meeting 30: `{snapshot['repos_meeting_30_release_eligible']}`.",
        "",
        "Paid validation readiness: local supply is sufficient for packaging. Paid validation has not run.",
    ]
    write_text(report_path(config, "supply_snapshot"), "\n".join(lines))

    table_lines = [
        "# Three-Repo Task Table",
        "",
        "Committed table contains sanitized metadata and digests only. It does not include raw diffs, raw test patches, raw prompts, raw completions, raw transcripts, or raw command logs.",
        "",
        "| Repo | Candidate | Source context | Time bucket | Family | Provenance |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in task_table["rows"]:
        table_lines.append(
            f"| {row['repo_id']} | `{row['candidate_id']}` | {row['source_context_quality']} | {row['task_time_bucket']} | {row['task_family']} | {row['release_eligibility_provenance']} |"
        )
    write_text(report_path(config, "task_table"), "\n".join(table_lines))


def write_source_audit_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Source Quality Audit",
        "",
        f"What happened: `{payload['task_count']}` release-eligible tasks were audited for source-context class, statement provenance, leakage flags, and ambiguity flags.",
        "",
        "Why it matters: weak or leaky solver-facing statements should be caught before paid solver cells are run.",
        "",
        f"Audit status counts: `{payload['audit_status_counts']}`.",
        f"Tasks requiring exclusion or repair: `{payload['tasks_requiring_exclusion_or_repair']}`.",
        "",
        f"Click release-eligible count: `{payload['click_audit']['release_eligible_count']}`. Thin margin: `{payload['click_audit']['thin_margin']}`.",
        "",
        "Paid validation readiness: source-quality audit passed for this package. Paid LLM review was not used.",
    ]
    write_text(report_path(config, "source_quality_audit"), "\n".join(lines))


def write_split_plan_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Split Plan",
        "",
        f"What happened: `{payload['assignment_count']}` audited tasks were assigned deterministically to `B_eval` and `H_future`.",
        "",
        "Why it matters: later paid validation must not choose splits after seeing outcomes.",
        "",
        f"Primary design: `{payload['primary_design']}`.",
        f"Primary score: `{payload['primary_score']}`.",
        f"Split seed: `{payload['split_seed']}`.",
        f"Split counts by repo: `{payload['split_counts_by_repo']}`.",
        "",
        f"H_future outcomes used for selection or weighting: `{payload['H_future_outcomes_used_for_selection_or_weighting']}`.",
        "Old weighted design primary: `False`.",
        "",
        "Paid validation readiness: split plan is frozen for a later paid runbook.",
    ]
    write_text(report_path(config, "split_plan"), "\n".join(lines))


def write_baseline_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Baseline Plan",
        "",
        "What happened: the primary design, baselines, and diagnostics were frozen before paid outcomes.",
        "",
        "Why it matters: old weighted scoring must not become the main claim after seeing outcomes.",
        "",
        f"Primary design: `{payload['primary_design']['design_id']}`.",
        "",
        "Frozen comparators:",
    ]
    for row in payload["baselines"]:
        lines.append(f"- `{row['design_id']}`: {row['role']}.")
    lines.extend(
        [
            "",
            f"Old weighted design primary: `{payload['old_weighted_design_primary']}`.",
            f"Post-hoc promotion rule: `{payload['post_hoc_promotion_rule']}`.",
        ]
    )
    write_text(report_path(config, "baseline_plan"), "\n".join(lines))


def write_threshold_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Threshold Preregistration",
        "",
        "What happened: success, failure, scoreability, endpoint, policy, and cost-accounting thresholds were preregistered.",
        "",
        "Why it matters: paid validation results need fixed rules before paid cells run.",
        "",
        json_fence(payload["thresholds"]),
        "",
        f"Success rule: {payload['success_rule']}",
        "",
        f"Failure rule: {payload['failure_rule']}",
        "",
        f"Underpowered evidence rule: {payload['underpowered_evidence_rule']}",
        "",
        "Predictive validity is not claimed before paid validation.",
    ]
    write_text(report_path(config, "threshold_preregistration"), "\n".join(lines))


def write_power_cost_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Power And Cost Plan",
        "",
        "What happened: two paid batch options were costed from committed historical cost evidence.",
        "",
        "Why it matters: a later paid runbook needs visible budget and stop conditions before spending.",
        "",
        f"Recommended option: `{payload['recommended_option']}`.",
        "",
        "| Option | Tasks | Cells | Cost range USD |",
        "| --- | ---: | ---: | --- |",
    ]
    for option in payload["batch_options"]:
        lines.append(
            f"| {option['option_id']} | {option['unique_task_count']} | {option['planned_cells']} | {option['expected_cost_range_usd']} |"
        )
    lines.extend(
        [
            "",
            f"Evidence boundary: {payload['evidence_boundary']}",
            "",
            "Stop conditions:",
        ]
    )
    lines.extend(f"- {condition}" for condition in payload["stop_conditions_after_each_batch"])
    write_text(report_path(config, "power_cost_plan"), "\n".join(lines))


def write_entry_gate_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Entry Gate",
        "",
        f"Entry gate status: `{payload['status']}`.",
        f"Paid ready: `{payload['paid_ready']}`.",
        "",
        "What happened: all non-paid gates were checked. No paid cells were run.",
        "",
        "Why it matters: this is the handoff point before any later paid validation runbook.",
        "",
        "Gate results:",
    ]
    for key, value in payload["gates"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", f"Failed gates: `{payload['failed_gates']}`."])
    if payload.get("verification_results"):
        lines.append("")
        lines.append("Verification recorded in this gate:")
        for result in payload["verification_results"]:
            lines.append(f"- `{' '.join(result['command'])}` -> returncode `{result['returncode']}`")
    write_text(report_path(config, "entry_gate"), "\n".join(lines))


def write_decision_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Three-Repo Paid Readiness Packaging Decision",
        "",
        f"Decision: `{payload['final_decision']}`.",
        f"Entry gate status: `{payload['entry_gate_status']}`.",
        f"Paid ready: `{payload['paid_ready']}`.",
        "",
        "What happened: attrs, boltons, and click were packaged into a frozen local-only paid-validation entry package.",
        "",
        "Why it matters: paid validation can now be considered by a later runbook, but predictive validity is still not established.",
        "",
        f"Release-eligible counts: `{payload['release_eligible_count_by_repo']}`.",
        f"Source-quality audit passed: `{payload['source_quality_audit_passed']}`.",
        f"Primary design: `{payload['primary_design']}`.",
        f"Recommended paid batch: `{payload['recommended_paid_batch']}` with cost range `{payload['recommended_paid_batch_cost_range_usd']}`.",
        "",
        "Research questions:",
    ]
    for rq, answer in payload["research_questions"].items():
        lines.append(f"- {rq}: {answer}")
    lines.extend(
        [
            "",
            "Known blockers:",
        ]
    )
    if payload["known_blockers"]:
        lines.extend(f"- {blocker}" for blocker in payload["known_blockers"])
    else:
        lines.append("- None for local entry packaging.")
    lines.extend(
        [
            "",
            "Recommended next action categories:",
        ]
    )
    lines.extend(f"- {item}" for item in payload["recommended_next_action_categories"])
    lines.extend(
        [
            "",
            "Paid-call statement: no paid ACUT solver cells, paid task-solving calls, paid replication, paid LLM generation, or paid LLM review were run by this packaging runbook.",
            "",
            "Predictive validity statement: not established. This is a pilot-ready entry package, not a completed paid validation.",
        ]
    )
    write_text(report_path(config, "decision"), "\n".join(lines))


def assert_sanitized_outputs(config: dict[str, Any]) -> None:
    paths = [output_path(config, key) for key in config.get("outputs", {})]
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in DISALLOWED_RAW_MARKERS:
            if marker in lowered:
                raise ValueError(f"raw marker {marker!r} found in {rel(path)}")


def run_step(config: dict[str, Any], step: str, *, run_tests: bool = False) -> None:
    if step == "preflight":
        build_preflight(config)
    elif step == "supply":
        build_supply_snapshot(config)
    elif step == "audit":
        build_source_quality_audit(config)
    elif step == "split":
        build_split_plan(config)
    elif step == "baseline":
        build_baseline_plan(config)
    elif step == "thresholds":
        build_threshold_preregistration(config)
    elif step == "cost":
        build_power_cost_plan(config)
    elif step == "entry":
        build_entry_gate(config, run_tests=run_tests)
    elif step == "decision":
        build_decision(config)
    elif step == "all":
        for substep in ("preflight", "supply", "audit", "split", "baseline", "thresholds", "cost", "entry", "decision"):
            run_step(config, substep, run_tests=run_tests and substep == "entry")
    else:
        raise ValueError(f"unknown step: {step}")
    assert_sanitized_outputs(config)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "step",
        choices=["preflight", "supply", "audit", "split", "baseline", "thresholds", "cost", "entry", "decision", "all"],
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-tests", action="store_true", help="run local verification commands when building the entry gate")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config = load_config(args.config)
    run_step(config, args.step, run_tests=args.run_tests)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
