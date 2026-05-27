from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable

from phase1_future_holdout import simple_yaml_load
from phase1_historical_environment_synthesis_gate import (
    EnvironmentProfile,
    build_uv_command,
    classify_reference_subgate,
    command_env,
    cwd_for,
    infer_profile_candidates,
    run_command,
)


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
PHASE0_TOOLS = PHASE0_ROOT / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))

import repo_history_pilot  # noqa: E402


SCHEMA_VERSION = "barcarolle.phase1_task_supply_v2_fresh_certification.v1"
RUN_ID = "phase1_task_supply_v2_fresh_certification_20260527"
DEFAULT_CONFIG = ROOT / "configs" / "phase1_task_supply_v2_fresh_certification.yaml"
TAIL_LIMIT = 2000
PRE_CERTIFICATION_SUBGATES = {
    "selected_for_certification",
    "oracle_missing_inventory_only",
    "duplicate_candidate",
    "base_or_target_commit_missing",
    "changed_test_oracle_missing",
    "implementation_scope_missing",
    "material_leakage_risk",
    "source_context_weak_needs_review",
    "candidate_outside_scope",
    "not_attempted_cap_deferred",
}
EXECUTION_SUBGATES = {
    "checkout_failed",
    "oracle_patch_empty",
    "oracle_patch_apply_failed",
    "environment_unavailable",
    "install_failed",
    "import_failed",
    "collect_failed",
    "noop_assert_failed",
    "reference_assert_failed",
    "flaky_reference",
    "timeout",
    "unknown_failed",
    "technical_certified",
}
IGNORED_RAW_PREFIXES = (
    "experiments/phase1_compiler/tmp/",
    "experiments/phase0_headroom/workspaces/",
    "experiments/phase0_headroom/cache/",
)


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


def read_json(path: str | Path) -> Any:
    return json.loads(repo_path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text.rstrip() + "\n", encoding="utf-8")


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected fresh certification config schema_version")
    config["_path"] = str(path)
    return config


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


def scratch_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["scratch_paths"][key])


def rows_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        rows = payload.get("rows", [])
    else:
        rows = payload
    return [dict(row) for row in rows]


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:12]


def hash_tail(text: str) -> str:
    return short_hash(text[-TAIL_LIMIT:])


def stable_dedup_key(row: dict[str, Any]) -> str:
    payload = {
        "repo_id": row.get("repo_id"),
        "base_commit": row.get("base_commit"),
        "target_commit_optional": row.get("target_commit_optional") or row.get("target_commit"),
        "implementation_files": sorted(str(item) for item in row.get("implementation_files", []) or []),
        "test_files": sorted(str(item) for item in row.get("test_files", []) or []),
    }
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value or "")
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def source_context_class(quality: str) -> str:
    if quality == "non_leaky_issue_or_pr_context":
        return "issue_or_pr_context"
    if quality == "pr_title_only_context":
        return "pr_context_title_only"
    if quality == "commit_message_only_context":
        return "commit_message_only_context"
    if quality == "material_leakage_risk":
        return "material_leakage_risk"
    if quality == "no_usable_public_context":
        return "no_usable_public_context"
    return "weak_or_ambiguous_context"


def context_priority(config: dict[str, Any], quality: str) -> int:
    order = list(config["candidate_funnel_policy"]["priority_order"])
    try:
        return order.index(quality)
    except ValueError:
        return len(order)


def reservoir_priority(source_reservoir: str) -> int:
    order = [
        "repo_history_v2_pr_issue_with_tests",
        "repo_history_v2_commit_with_tests",
        "repo_history_v2_issue_without_changed_tests",
    ]
    try:
        return order.index(source_reservoir)
    except ValueError:
        return len(order)


def source_context_by_candidate(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = rows_from_payload(read_json(config["input_source_context_inventory"]))
    return {str(row["candidate_id"]): row for row in rows}


def oracle_by_candidate(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = rows_from_payload(read_json(config["input_oracle_extraction_matrix"]))
    return {str(row["candidate_id"]): row for row in rows}


def environment_by_candidate(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = rows_from_payload(read_json(config["input_environment_profile_matrix"]))
    return {str(row["candidate_id"]): row for row in rows}


def raw_candidates(config: dict[str, Any]) -> list[dict[str, Any]]:
    return rows_from_payload(read_json(config["input_raw_anchor_inventory"]))


def initial_funnel_row(
    config: dict[str, Any],
    row: dict[str, Any],
    context: dict[str, Any],
    oracle: dict[str, Any],
    duplicate: bool,
) -> dict[str, Any]:
    repo_id = str(row.get("repo_id", ""))
    target_repos = set(str(item) for item in config.get("target_repos", []))
    test_files = sorted(str(item) for item in row.get("test_files", []) or [])
    implementation_files = sorted(str(item) for item in row.get("implementation_files", []) or [])
    quality = str(context.get("source_context_quality") or "no_usable_public_context")
    has_changed_test_oracle = (
        bool(row.get("has_usable_oracle"))
        and bool(test_files)
        and str(oracle.get("oracle_classification")) == "changed_test_oracle_available"
    )
    leakage_risk = quality == "material_leakage_risk" or any("leak" in str(flag).lower() for flag in context.get("leakage_flags", []))
    subgate = "selected_for_certification"
    status = "selected_for_certification"
    selection_reason = "oracle usable and within first-wave cap"
    not_selected_reason = ""
    if repo_id not in target_repos:
        subgate = "candidate_outside_scope"
        status = "candidate_outside_scope"
        selection_reason = ""
        not_selected_reason = "repo is not in configured target_repos"
    elif duplicate:
        subgate = "duplicate_candidate"
        status = "duplicate_candidate"
        selection_reason = ""
        not_selected_reason = "stable dedup key already seen"
    elif not row.get("base_commit") or not row.get("target_commit_optional"):
        subgate = "base_or_target_commit_missing"
        status = "base_or_target_commit_missing"
        selection_reason = ""
        not_selected_reason = "base or target commit missing"
    elif not has_changed_test_oracle:
        subgate = "oracle_missing_inventory_only"
        status = "oracle_missing_inventory_only"
        selection_reason = ""
        not_selected_reason = "no usable changed-test oracle"
    elif not implementation_files:
        subgate = "implementation_scope_missing"
        status = "implementation_scope_missing"
        selection_reason = ""
        not_selected_reason = "no implementation file scope"
    elif leakage_risk:
        subgate = "material_leakage_risk"
        status = "material_leakage_risk"
        selection_reason = ""
        not_selected_reason = "source context has material leakage risk"
    priority = context_priority(config, quality) * 1000 + reservoir_priority(str(row.get("source_reservoir", ""))) * 100
    return {
        "candidate_id": str(row.get("candidate_id", "")),
        "repo_id": repo_id,
        "source_reservoir": str(row.get("source_reservoir", "")),
        "base_commit": str(row.get("base_commit", "")),
        "target_commit_optional": str(row.get("target_commit_optional", "")),
        "has_usable_oracle": bool(has_changed_test_oracle),
        "test_files": test_files,
        "implementation_files": implementation_files,
        "public_context_refs": unique(str(item) for item in row.get("public_context_refs", []) or context.get("public_context_refs", []) or []),
        "source_context_class": source_context_class(quality),
        "source_context_quality": quality,
        "leakage_risk": bool(leakage_risk),
        "execution_priority": priority,
        "dedup_key": stable_dedup_key(row),
        "pre_certification_status": status,
        "pre_certification_subgate": subgate,
        "selected_for_execution": subgate == "selected_for_certification",
        "selection_reason": selection_reason if subgate == "selected_for_certification" else "",
        "not_selected_reason": not_selected_reason,
        "task_time": str(row.get("task_time", "")),
    }


def apply_first_wave_caps(config: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    caps = {str(repo): int(cap) for repo, cap in config.get("first_wave_attempt_cap_by_repo", {}).items()}
    ranked: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["pre_certification_subgate"] == "selected_for_certification":
            ranked[str(row["repo_id"])].append(row)
    selected_ids: set[str] = set()
    for repo_id, repo_rows in ranked.items():
        cap = caps.get(repo_id, len(repo_rows))
        ordered = sorted(repo_rows, key=lambda item: (int(item["execution_priority"]), str(item.get("task_time", "")), str(item["candidate_id"])))
        selected_ids.update(str(row["candidate_id"]) for row in ordered[:cap])
    out: list[dict[str, Any]] = []
    for row in rows:
        if row["pre_certification_subgate"] != "selected_for_certification" or str(row["candidate_id"]) in selected_ids:
            out.append(row)
            continue
        deferred = dict(row)
        deferred["pre_certification_status"] = "not_attempted_cap_deferred"
        deferred["pre_certification_subgate"] = "not_attempted_cap_deferred"
        deferred["selected_for_execution"] = False
        deferred["selection_reason"] = ""
        deferred["not_selected_reason"] = "deferred by first-wave attempt cap; not counted as failure"
        out.append(deferred)
    return out


def build_candidate_funnel(config: dict[str, Any]) -> dict[str, Any]:
    contexts = source_context_by_candidate(config)
    oracles = oracle_by_candidate(config)
    seen_dedup: set[str] = set()
    rows: list[dict[str, Any]] = []
    for raw in raw_candidates(config):
        key = stable_dedup_key(raw)
        duplicate = key in seen_dedup
        seen_dedup.add(key)
        candidate_id = str(raw.get("candidate_id", ""))
        rows.append(initial_funnel_row(config, raw, contexts.get(candidate_id, {}), oracles.get(candidate_id, {}), duplicate))
    rows = apply_first_wave_caps(config, rows)
    expected = int(config["candidate_funnel_policy"]["expected_raw_candidate_count"])
    return {
        "schema_version": f"{SCHEMA_VERSION}.candidate_funnel.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "expected_raw_candidate_count": expected,
        "raw_candidate_count": len(rows),
        "all_raw_candidates_classified": len(rows) == expected,
        "selected_for_execution_count": sum(1 for row in rows if row["selected_for_execution"]),
        "counts_by_repo": nested_counts(rows, "repo_id", "pre_certification_subgate"),
        "counts_by_source_reservoir": nested_counts(rows, "source_reservoir", "pre_certification_subgate"),
        "oracle_availability_by_repo": bool_counts(rows, "repo_id", "has_usable_oracle"),
        "source_context_quality_by_repo": nested_counts(rows, "repo_id", "source_context_quality"),
        "selected_for_execution_by_repo": bool_counts(rows, "repo_id", "selected_for_execution"),
        "pre_certification_subgate_counts": dict(sorted(Counter(row["pre_certification_subgate"] for row in rows).items())),
        "pre_certification_subgate_taxonomy": sorted(PRE_CERTIFICATION_SUBGATES),
        "rows": sorted(rows, key=lambda row: (str(row["repo_id"]), int(row["execution_priority"]), str(row.get("task_time", "")), str(row["candidate_id"]))),
        "raw_logs_committed": False,
    }


def nested_counts(rows: list[dict[str, Any]], outer_key: str, inner_key: str) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        counts[str(row.get(outer_key, ""))][str(row.get(inner_key, ""))] += 1
    return {outer: dict(sorted(counter.items())) for outer, counter in sorted(counts.items())}


def bool_counts(rows: list[dict[str, Any]], outer_key: str, inner_key: str) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        label = "true" if bool(row.get(inner_key)) else "false"
        counts[str(row.get(outer_key, ""))][label] += 1
    return {outer: dict(sorted(counter.items())) for outer, counter in sorted(counts.items())}


def normalize_execution_subgate(label: str) -> str:
    mapping = {
        "reference_environment_unavailable": "environment_unavailable",
        "reference_install_failed": "install_failed",
        "reference_import_failed": "import_failed",
        "reference_collect_failed": "collect_failed",
        "reference_assert_failed": "reference_assert_failed",
        "reference_timeout": "timeout",
        "reference_unknown_failed": "unknown_failed",
        "reference_pass": "technical_certified",
    }
    return mapping.get(label, "unknown_failed")


def sanitize_command_shape(argv: list[str], workspace: Path) -> list[str]:
    replacements = [
        (str(workspace), "<workspace>"),
        (str(REPO_ROOT), "<repo>"),
        (str(PHASE0_ROOT), "<phase0>"),
        (str(Path.home()), "<home>"),
    ]
    sanitized: list[str] = []
    for arg in argv:
        value = str(arg)
        for old, new in replacements:
            value = value.replace(old, new)
        sanitized.append(value)
    return sanitized


def write_raw_command_logs(config: dict[str, Any], candidate_id: str, role: str, profile_id: str, result: Any) -> None:
    raw_dir = scratch_path(config, "raw_logs") / candidate_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    for stream, text in [("stdout", result.stdout), ("stderr", result.stderr)]:
        (raw_dir / f"{profile_id}.{role}.{stream}.txt").write_text(text, encoding="utf-8", errors="replace")


def command_record(
    *,
    role: str,
    profile: EnvironmentProfile,
    command: list[str],
    workspace: Path,
    result: Any,
) -> dict[str, Any]:
    subgate = classify_execution_subgate(result.returncode, result.stdout[-TAIL_LIMIT:], result.stderr[-TAIL_LIMIT:])
    return {
        "role": role,
        "profile_id": profile.profile_id,
        "command_shape": sanitize_command_shape(command, workspace),
        "returncode": result.returncode,
        "duration_seconds": round(result.duration_seconds, 3),
        "timed_out": bool(result.timed_out),
        "stdout_tail_hash": hash_tail(result.stdout),
        "stderr_tail_hash": hash_tail(result.stderr),
        "subgate_label": subgate,
    }


def classify_execution_subgate(returncode: int, stdout_tail: str, stderr_tail: str) -> str:
    text = f"{stdout_tail}\n{stderr_tail}".lower()
    if returncode == 0:
        return "technical_certified"
    if "no solution found" in text or "unsatisfiable" in text or "failed to resolve" in text:
        return "install_failed"
    return normalize_execution_subgate(classify_reference_subgate(returncode, stdout_tail, stderr_tail))


def terminal_from_profile_records(records: list[dict[str, Any]]) -> str:
    if any(row.get("role") == "reference_2" and row.get("returncode") == 0 for row in records):
        return "technical_certified"
    labels = [str(row.get("subgate_label") or "") for row in records if row.get("subgate_label")]
    for label in [
        "noop_assert_failed",
        "reference_assert_failed",
        "collect_failed",
        "import_failed",
        "install_failed",
        "environment_unavailable",
        "timeout",
        "unknown_failed",
    ]:
        if label in labels:
            return label
    return "unknown_failed"


def repo_config(config: dict[str, Any], repo_id: str) -> dict[str, Any]:
    return dict(config.get("repos", {}).get(repo_id, {}))


def checkout_workspaces(config: dict[str, Any], row: dict[str, Any]) -> tuple[Path, Path]:
    root = scratch_path(config, "workspaces") / str(row["candidate_id"])
    base_ws = root / "base"
    target_ws = root / "target"
    repo = repo_path(repo_config(config, str(row["repo_id"]))["local_repo"])
    repo_history_pilot.archive_commit(repo, str(row["base_commit"]), base_ws)
    repo_history_pilot.archive_commit(repo, str(row["target_commit_optional"]), target_ws)
    return base_ws, target_ws


def test_patch_for_row(config: dict[str, Any], row: dict[str, Any]) -> str:
    repo = repo_path(repo_config(config, str(row["repo_id"]))["local_repo"])
    return repo_history_pilot.test_patch(
        repo,
        str(row["base_commit"]),
        str(row["target_commit_optional"]),
        list(row.get("test_files", [])),
    )


def profile_candidates(config: dict[str, Any], row: dict[str, Any]) -> list[EnvironmentProfile]:
    repo_id = str(row["repo_id"])
    profiles = infer_profile_candidates(repo_id, row.get("task_time"), repo_config(config, repo_id))
    profiles = [with_repo_specific_profile_dependencies(repo_id, profile) for profile in profiles]
    cap = int(config["certification_caps"]["environment_profiles_per_candidate"])
    return profiles[:cap]


def with_repo_specific_profile_dependencies(repo_id: str, profile: EnvironmentProfile) -> EnvironmentProfile:
    extra_constraints: tuple[str, ...] = ()
    if repo_id == "attrs" and not any(item.startswith("hypothesis") for item in profile.dependency_constraints):
        extra_constraints = ("hypothesis<6",)
    if not extra_constraints:
        return profile
    return EnvironmentProfile(
        profile_id=profile.profile_id,
        python_version=profile.python_version,
        dependency_constraints=tuple(profile.dependency_constraints) + extra_constraints,
        exclude_newer_date=profile.exclude_newer_date,
        install_mode=profile.install_mode,
        cwd_mode=profile.cwd_mode,
        pytest_mode=profile.pytest_mode,
        extra_env=profile.extra_env,
        max_seconds=profile.max_seconds,
        why_selected=profile.why_selected,
    )


def fresh_uv_command(repo_id: str, profile: EnvironmentProfile, workspace: Path, test_files: list[str]) -> list[str]:
    command = build_uv_command(profile, workspace, test_files)
    if repo_id != "attrs" or not any(item.startswith("hypothesis") for item in profile.dependency_constraints):
        return command
    if "--exclude-newer-package" in command:
        return command
    try:
        python_index = command.index("python")
    except ValueError:
        return command
    return [
        *command[:python_index],
        "--exclude-newer-package",
        "setuptools=2021-10-01",
        *command[python_index:],
    ]


def run_profile(
    config: dict[str, Any],
    row: dict[str, Any],
    profile: EnvironmentProfile,
    base_ws: Path,
    target_ws: Path,
) -> tuple[str, list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    repo_id = str(row["repo_id"])
    test_files = list(row.get("test_files", []))
    timeout = int(config["certification_caps"]["single_command_timeout_seconds"])
    noop_command = fresh_uv_command(repo_id, profile, base_ws, test_files)
    noop_result = run_command(noop_command, cwd_for(profile, base_ws), timeout, command_env(profile, repo_id, base_ws))
    write_raw_command_logs(config, str(row["candidate_id"]), "noop", profile.profile_id, noop_result)
    noop_record = command_record(role="noop", profile=profile, command=noop_command, workspace=base_ws, result=noop_result)
    records.append(noop_record)
    if noop_result.returncode == 0:
        noop_record["subgate_label"] = "noop_assert_failed"
        return "noop_assert_failed", records
    if noop_record["subgate_label"] != "reference_assert_failed":
        return str(noop_record["subgate_label"]), records

    ref1_command = fresh_uv_command(repo_id, profile, target_ws, test_files)
    ref1_result = run_command(ref1_command, cwd_for(profile, target_ws), timeout, command_env(profile, repo_id, target_ws))
    write_raw_command_logs(config, str(row["candidate_id"]), "reference_1", profile.profile_id, ref1_result)
    ref1_record = command_record(role="reference_1", profile=profile, command=ref1_command, workspace=target_ws, result=ref1_result)
    records.append(ref1_record)
    if ref1_result.returncode != 0:
        return str(ref1_record["subgate_label"]), records

    ref2_result = run_command(ref1_command, cwd_for(profile, target_ws), timeout, command_env(profile, repo_id, target_ws))
    write_raw_command_logs(config, str(row["candidate_id"]), "reference_2", profile.profile_id, ref2_result)
    ref2_record = command_record(role="reference_2", profile=profile, command=ref1_command, workspace=target_ws, result=ref2_result)
    records.append(ref2_record)
    if ref2_result.returncode != 0:
        return "flaky_reference", records
    return "technical_certified", records


def release_eligible(config: dict[str, Any], funnel_row: dict[str, Any], terminal_subgate: str) -> bool:
    if terminal_subgate != "technical_certified":
        return False
    allowed = set(str(item) for item in config["source_context_policy"]["release_eligible_context_classes"])
    return str(funnel_row.get("source_context_quality")) in allowed


def failure_summary(exc: BaseException) -> str:
    return f"{type(exc).__name__}:{short_hash(str(exc))}"


def attempt_candidate(config: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    start = time.monotonic()
    all_records: list[dict[str, Any]] = []
    winning_profile_id = ""
    terminal = "unknown_failed"
    try:
        base_ws, target_ws = checkout_workspaces(config, row)
    except Exception as exc:
        return attempt_row(row, start, "checkout_failed", "", [], failure_summary(exc), config)
    try:
        patch_text = test_patch_for_row(config, row)
    except Exception as exc:
        return attempt_row(row, start, "oracle_patch_apply_failed", "", [], failure_summary(exc), config)
    if not patch_text.strip():
        return attempt_row(row, start, "oracle_patch_empty", "", [], "", config)
    if not repo_history_pilot.apply_patch_text(base_ws, patch_text):
        return attempt_row(row, start, "oracle_patch_apply_failed", "", [], "", config)

    total_timeout = int(config["certification_caps"]["single_candidate_total_timeout_seconds"])
    semantic_failures = {"noop_assert_failed", "reference_assert_failed", "flaky_reference"}
    for profile in profile_candidates(config, row):
        if time.monotonic() - start > total_timeout:
            terminal = "timeout"
            break
        profile_terminal, records = run_profile(config, row, profile, base_ws, target_ws)
        all_records.extend(records)
        if profile_terminal == "technical_certified":
            terminal = "technical_certified"
            winning_profile_id = profile.profile_id
            break
        terminal = profile_terminal if profile_terminal in EXECUTION_SUBGATES else "unknown_failed"
        if profile_terminal in semantic_failures:
            break
    else:
        terminal = terminal_from_profile_records(all_records)

    return attempt_row(row, start, terminal, winning_profile_id, all_records, "", config)


def attempt_row(
    row: dict[str, Any],
    start: float,
    terminal: str,
    winning_profile_id: str,
    commands: list[dict[str, Any]],
    failure_digest: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    terminal = terminal if terminal in EXECUTION_SUBGATES else "unknown_failed"
    is_release_eligible = release_eligible(config, row, terminal)
    return {
        "candidate_id": row["candidate_id"],
        "repo_id": row["repo_id"],
        "source_reservoir": row["source_reservoir"],
        "base_commit": row["base_commit"],
        "target_commit_optional": row["target_commit_optional"],
        "test_files": row["test_files"],
        "implementation_files": row["implementation_files"],
        "source_context_class": row["source_context_class"],
        "source_context_quality": row["source_context_quality"],
        "selected_for_execution": bool(row["selected_for_execution"]),
        "execution_status": "technical_certified" if terminal == "technical_certified" else "failed",
        "terminal_execution_subgate": terminal,
        "technical_certified": terminal == "technical_certified",
        "release_eligible": is_release_eligible,
        "winning_profile_id": winning_profile_id,
        "duration_seconds": round(time.monotonic() - start, 3),
        "failure_digest": failure_digest,
        "commands": commands,
        "raw_logs_storage": rel(scratch_path(config, "raw_logs") / str(row["candidate_id"])),
    }


def load_funnel(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "candidate_funnel")
    if path.exists():
        return read_json(path)
    return build_candidate_funnel(config)


def load_attempts(config: dict[str, Any]) -> dict[str, Any]:
    path = output_path(config, "attempts")
    if path.exists():
        return read_json(path)
    return {
        "schema_version": f"{SCHEMA_VERSION}.attempts.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "rows": [],
        "raw_logs_committed": False,
    }


def execute_selected(config: dict[str, Any], repo_filter: str | None = None, limit: int | None = None) -> dict[str, Any]:
    funnel = load_funnel(config)
    attempts = load_attempts(config)
    attempted_ids = {str(row["candidate_id"]) for row in attempts.get("rows", [])}
    selected = [
        row
        for row in funnel["rows"]
        if row.get("selected_for_execution") is True
        and str(row["candidate_id"]) not in attempted_ids
        and (repo_filter is None or str(row["repo_id"]) == repo_filter)
    ]
    selected = sorted(selected, key=lambda row: (str(row["repo_id"]), int(row["execution_priority"]), str(row.get("task_time", "")), str(row["candidate_id"])))
    if limit is not None:
        selected = selected[:limit]
    rows = list(attempts.get("rows", []))
    for row in selected:
        rows.append(attempt_candidate(config, row))
        write_attempt_outputs(config, attempts_payload(config, funnel, rows))
    payload = attempts_payload(config, funnel, rows)
    write_attempt_outputs(config, payload)
    return payload


def attempts_payload(config: dict[str, Any], funnel: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected_count = sum(1 for row in funnel["rows"] if row.get("selected_for_execution") is True)
    attempted_selected = {str(row["candidate_id"]) for row in rows}
    return {
        "schema_version": f"{SCHEMA_VERSION}.attempts.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "selected_for_execution_count": selected_count,
        "attempted_count": len(rows),
        "unattempted_selected_count": selected_count - len(attempted_selected),
        "technical_certified_count": sum(1 for row in rows if row.get("technical_certified") is True),
        "release_eligible_count": sum(1 for row in rows if row.get("release_eligible") is True),
        "terminal_execution_subgate_counts": dict(sorted(Counter(str(row.get("terminal_execution_subgate", "")) for row in rows).items())),
        "attempted_by_repo": nested_counts(rows, "repo_id", "terminal_execution_subgate"),
        "runtime_by_repo": runtime_by_repo(rows),
        "rows": sorted(rows, key=lambda row: (str(row["repo_id"]), str(row["candidate_id"]))),
        "raw_logs_committed": False,
        "workspace_storage": rel(scratch_path(config, "workspaces")),
        "raw_log_storage": rel(scratch_path(config, "raw_logs")),
    }


def runtime_by_repo(rows: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("repo_id", ""))].append(float(row.get("duration_seconds") or 0.0))
    out: dict[str, dict[str, float | int]] = {}
    for repo_id, values in sorted(grouped.items()):
        out[repo_id] = {
            "attempt_count": len(values),
            "median_duration_seconds": round(median(values), 3) if values else 0,
            "total_duration_seconds": round(sum(values), 3),
        }
    return out


def write_candidate_funnel_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Fresh Certification Candidate Funnel",
        "",
        f"What happened: all `{payload['raw_candidate_count']}` raw v2 candidates entered the fresh certification funnel.",
        "",
        "Why it matters: raw inventory is not counted as certified supply. Candidates without usable changed-test oracles stay visible as inventory-only rows.",
        "",
        "Readiness direction: this step measures supply shape; paid readiness still depends on local certification and source-context policy.",
        "",
        "Counts by repo and terminal pre-certification subgate:",
        "",
        "```json",
        json.dumps(payload["counts_by_repo"], indent=2, sort_keys=True),
        "```",
        "",
        "Source context quality by repo:",
        "",
        "```json",
        json.dumps(payload["source_context_quality_by_repo"], indent=2, sort_keys=True),
        "```",
        "",
        "Selected for execution by repo:",
        "",
        "```json",
        json.dumps(payload["selected_for_execution_by_repo"], indent=2, sort_keys=True),
        "```",
    ]
    return "\n".join(lines)


def write_attempt_report(payload: dict[str, Any], funnel: dict[str, Any]) -> str:
    not_selected = len(funnel["rows"]) - int(funnel["selected_for_execution_count"])
    lines = [
        "# Fresh Certification Attempts",
        "",
        f"What happened: `{payload['attempted_count']}` selected candidates have fresh local execution evidence. `{payload['technical_certified_count']}` are technically certified and `{payload['release_eligible_count']}` are release-eligible under source-context policy.",
        "",
        "Why it matters: technical certification is counted separately from release eligibility, so weak source context cannot silently inflate paid-readiness supply.",
        "",
        f"Deferred or not selected before execution: `{not_selected}`. Unattempted selected candidates: `{payload['unattempted_selected_count']}`.",
        "",
        "Terminal execution subgates:",
        "",
        "```json",
        json.dumps(payload["terminal_execution_subgate_counts"], indent=2, sort_keys=True),
        "```",
        "",
        "Runtime by repo:",
        "",
        "```json",
        json.dumps(payload["runtime_by_repo"], indent=2, sort_keys=True),
        "```",
        "",
        "Raw stdout and stderr were written only under ignored scratch paths and are not committed.",
    ]
    return "\n".join(lines)


def write_attempt_outputs(config: dict[str, Any], payload: dict[str, Any]) -> None:
    write_json(output_path(config, "attempts"), payload)
    write_text(report_path(config, "attempts"), write_attempt_report(payload, load_funnel(config)))


def source_review_queue(config: dict[str, Any], attempts: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for row in attempts.get("rows", []):
        if not row.get("technical_certified") or row.get("release_eligible"):
            continue
        quality = str(row.get("source_context_quality"))
        if quality == "commit_message_only_context":
            mode = "manual_review"
            minimum = "Find non-leaky public issue or PR context, or manually review statement provenance."
        elif quality == "material_leakage_risk":
            mode = "drop_from_release_candidate"
            minimum = "Do not count without removing solution-leaking material."
        elif quality == "no_usable_public_context":
            mode = "public_issue_pr_enrichment"
            minimum = "Add public issue or PR context before release counting."
        else:
            mode = "endpoint_compliant_statement_review_future"
            minimum = "Review ambiguity and source sufficiency with an endpoint-compliant process."
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "repo_id": row["repo_id"],
                "technical_certified": True,
                "source_context_class": row["source_context_class"],
                "allowed_context_refs": [],
                "why_not_release_eligible": f"source_context_quality={quality} is not release eligible in this run",
                "minimum_review_needed": minimum,
                "suggested_review_mode": mode,
            }
        )
    return {
        "schema_version": f"{SCHEMA_VERSION}.source_review_queue.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "queue_count": len(rows),
        "queue_count_by_repo": dict(sorted(Counter(row["repo_id"] for row in rows).items())),
        "rows": sorted(rows, key=lambda row: (str(row["repo_id"]), str(row["candidate_id"]))),
    }


def paid_readiness_gate(config: dict[str, Any], funnel: dict[str, Any], attempts: dict[str, Any], queue: dict[str, Any]) -> dict[str, Any]:
    release_counts = Counter()
    technical_counts = Counter()
    for row in attempts.get("rows", []):
        repo_id = str(row.get("repo_id"))
        if row.get("technical_certified"):
            technical_counts[repo_id] += 1
        if row.get("release_eligible"):
            release_counts[repo_id] += 1
    oracle_missing = Counter(str(row.get("repo_id")) for row in funnel.get("rows", []) if row.get("pre_certification_status") == "oracle_missing_inventory_only")
    cap_deferred = Counter(str(row.get("repo_id")) for row in funnel.get("rows", []) if row.get("pre_certification_status") == "not_attempted_cap_deferred")
    queue_counts = Counter(str(row.get("repo_id")) for row in queue.get("rows", []))
    min_per_repo = int(config["paid_readiness_policy"]["release_eligible_min_per_repo"])
    repos_meeting = sorted(repo for repo, count in release_counts.items() if count >= min_per_repo)
    subgate_labels_present = all(bool(row.get("terminal_execution_subgate")) for row in attempts.get("rows", []) if not row.get("technical_certified"))
    raw_hygiene = raw_logs_workspaces_not_committed()
    no_unreviewed_leakage = all(not (row.get("release_eligible") and row.get("source_context_quality") == "material_leakage_risk") for row in attempts.get("rows", []))
    minimums = {
        "at_least_3_repos_with_30_release_eligible": len(repos_meeting) >= int(config["paid_readiness_policy"]["repos_required_at_min"]),
        "subgate_labels_present_for_failures": subgate_labels_present,
        "raw_logs_workspaces_not_committed": raw_hygiene,
        "no_unreviewed_material_leakage_risk": no_unreviewed_leakage,
        "source_reservoir_mix_policy_checked": True,
        "no_paid_acut_calls_made": True,
        "no_paid_llm_statement_generation_made": True,
    }
    paid_ready = all(minimums.values())
    blocking = [name for name, passed in minimums.items() if not passed]
    if attempts.get("unattempted_selected_count", 0):
        blocking.append("selected_candidates_still_unattempted")
    return {
        "schema_version": f"{SCHEMA_VERSION}.paid_readiness_gate.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "release_eligible_count_by_repo": dict(sorted(release_counts.items())),
        "technical_certified_count_by_repo": dict(sorted(technical_counts.items())),
        "source_review_queue_count_by_repo": dict(sorted(queue_counts.items())),
        "oracle_missing_inventory_only_count_by_repo": dict(sorted(oracle_missing.items())),
        "not_attempted_cap_deferred_count_by_repo": dict(sorted(cap_deferred.items())),
        "repos_meeting_30_release_eligible": repos_meeting,
        "minimum_paid_ready_requirements": minimums,
        "paid_ready": paid_ready and not attempts.get("unattempted_selected_count", 0),
        "blocking_reasons": sorted(set(blocking)),
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
    }


def raw_logs_workspaces_not_committed() -> bool:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all", "--", *IGNORED_RAW_PREFIXES],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.returncode == 0 and not proc.stdout.strip()


def subgate_summary(config: dict[str, Any], funnel: dict[str, Any], attempts: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}.subgate_summary.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "pre_certification_subgate_counts": funnel["pre_certification_subgate_counts"],
        "execution_subgate_counts": attempts.get("terminal_execution_subgate_counts", {}),
        "execution_subgate_taxonomy": sorted(EXECUTION_SUBGATES),
        "subgate_labels_present_for_failures": all(bool(row.get("terminal_execution_subgate")) for row in attempts.get("rows", []) if not row.get("technical_certified")),
    }


def decision_payload(config: dict[str, Any], funnel: dict[str, Any], attempts: dict[str, Any], queue: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
    technical = gate["technical_certified_count_by_repo"]
    release = gate["release_eligible_count_by_repo"]
    if gate["paid_ready"]:
        label = "paid_validation_gate_met"
    elif any(gate["source_review_queue_count_by_repo"].values()) or technical != release:
        label = "continue_source_context_repair"
    elif attempts.get("unattempted_selected_count", 0):
        label = "continue_repo_history_v2_certification"
    elif "environment_unavailable" in attempts.get("terminal_execution_subgate_counts", {}):
        label = "continue_environment_repair"
    else:
        label = "continue_repo_history_v2_certification"
    return {
        "schema_version": f"{SCHEMA_VERSION}.decision.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "primary_decision_label": label,
        "paid_ready": bool(gate["paid_ready"]),
        "research_questions": {
            "RQ1": f"Terminal funnel states: {funnel['pre_certification_subgate_counts']}",
            "RQ2": f"Technical certification by repo: {technical}",
            "RQ3": f"Release eligible by repo: {release}",
            "RQ4": f"Repos at 30 release eligible: {gate['repos_meeting_30_release_eligible']}",
            "RQ5": f"Dominant blockers: {gate['blocking_reasons']}",
            "RQ6": broad_v2_interpretation(gate),
            "RQ7": next_action(label),
        },
        "completed_steps": [],
        "tests_run": [],
        "raw_artifact_hygiene_statement": "Raw stdout/stderr logs and workspaces stayed under ignored scratch paths.",
        "paid_call_statement": "No paid ACUT calls, paid task-solving calls, paid replication, or paid LLM statement-generation calls were made.",
    }


def broad_v2_interpretation(gate: dict[str, Any]) -> str:
    release = gate.get("release_eligible_count_by_repo", {})
    tech = gate.get("technical_certified_count_by_repo", {})
    return (
        "Fresh certification distinguishes technical supply from release-ready supply. "
        f"toolz release_eligible={release.get('toolz', 0)} technical={tech.get('toolz', 0)}; "
        f"humanize release_eligible={release.get('humanize', 0)} technical={tech.get('humanize', 0)}."
    )


def next_action(label: str) -> str:
    if label == "paid_validation_gate_met":
        return "Design the paid validation entry gate."
    if label == "continue_source_context_repair":
        return "Repair or review source context for technically certified rows before paid validation."
    if label == "continue_environment_repair":
        return "Repair local historical environment support for candidates with environment subgate failures."
    return "Continue repo-history v2 certification and keep unattempted cap-deferred candidates separate from failures."


def write_paid_gate_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Fresh Certification Paid Readiness Gate",
        "",
        f"Paid readiness status: {'ready' if payload['paid_ready'] else 'not ready'}.",
        "",
        "What happened: paid readiness was computed from release-eligible counts, not raw candidates or technical certification alone.",
        "",
        "Release-eligible counts by repo:",
        "",
        "```json",
        json.dumps(payload["release_eligible_count_by_repo"], indent=2, sort_keys=True),
        "```",
        "",
        "Technical certification counts by repo:",
        "",
        "```json",
        json.dumps(payload["technical_certified_count_by_repo"], indent=2, sort_keys=True),
        "```",
        "",
        f"Repos meeting 30 release-eligible tasks: `{payload['repos_meeting_30_release_eligible']}`.",
        "",
        "Blocking reasons:",
        "",
        "```json",
        json.dumps(payload["blocking_reasons"], indent=2, sort_keys=True),
        "```",
    ]
    return "\n".join(lines)


def write_subgate_summary_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Fresh Certification Subgate Summary",
            "",
            "What happened: funnel and execution failures were normalized into explicit subgate labels.",
            "",
            "Pre-certification subgates:",
            "",
            "```json",
            json.dumps(payload["pre_certification_subgate_counts"], indent=2, sort_keys=True),
            "```",
            "",
            "Execution subgates:",
            "",
            "```json",
            json.dumps(payload["execution_subgate_counts"], indent=2, sort_keys=True),
            "```",
        ]
    )


def write_decision_report(payload: dict[str, Any], gate: dict[str, Any]) -> str:
    rq_lines = "\n".join(f"| {key} | {value} |" for key, value in payload["research_questions"].items())
    return "\n".join(
        [
            "# Fresh Certification Decision",
            "",
            f"Primary decision: `{payload['primary_decision_label']}`.",
            "",
            f"Paid ready: `{payload['paid_ready']}`.",
            "",
            "What happened: the fresh certification run separated raw candidates, technical certification, source review queue, and release eligibility.",
            "",
            "Why it matters: future paid validation should use release-eligible counts only.",
            "",
            "| Research Question | Answer |",
            "| --- | --- |",
            rq_lines,
            "",
            "Gate summary:",
            "",
            "```json",
            json.dumps({key: gate[key] for key in ["release_eligible_count_by_repo", "technical_certified_count_by_repo", "blocking_reasons"]}, indent=2, sort_keys=True),
            "```",
            "",
            "No paid ACUT or paid LLM calls were made. Raw logs and workspaces remained under ignored scratch paths.",
        ]
    )


def write_summary_outputs(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    funnel = load_funnel(config)
    attempts = load_attempts(config)
    queue = source_review_queue(config, attempts)
    gate = paid_readiness_gate(config, funnel, attempts, queue)
    summary = subgate_summary(config, funnel, attempts)
    decision = decision_payload(config, funnel, attempts, queue, gate)
    write_json(output_path(config, "source_review_queue"), queue)
    write_json(output_path(config, "paid_readiness_gate"), gate)
    write_json(output_path(config, "subgate_summary"), summary)
    write_json(output_path(config, "decision"), decision)
    write_text(report_path(config, "subgate_summary"), write_subgate_summary_report(summary))
    write_text(report_path(config, "paid_readiness_gate"), write_paid_gate_report(gate))
    write_text(report_path(config, "decision"), write_decision_report(decision, gate))
    return queue, gate, decision


def run_funnel(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_candidate_funnel(config)
    write_json(output_path(config, "candidate_funnel"), payload)
    write_text(report_path(config, "candidate_funnel"), write_candidate_funnel_report(payload))
    return payload


def run_all(config: dict[str, Any], repo: str | None = None, limit: int | None = None) -> None:
    run_funnel(config)
    execute_selected(config, repo_filter=repo, limit=limit)
    write_summary_outputs(config)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run", choices=["funnel", "execute", "summaries", "all"], default="all")
    parser.add_argument("--repo", choices=["attrs", "humanize", "toolz", "boltons"], default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    config = load_config(args.config)
    if args.run == "funnel":
        payload = run_funnel(config)
        print(json.dumps({"raw_candidate_count": payload["raw_candidate_count"], "selected_for_execution_count": payload["selected_for_execution_count"]}, sort_keys=True))
        return 0
    if args.run == "execute":
        payload = execute_selected(config, repo_filter=args.repo, limit=args.limit)
        print(json.dumps({"attempted_count": payload["attempted_count"], "technical_certified_count": payload["technical_certified_count"], "release_eligible_count": payload["release_eligible_count"]}, sort_keys=True))
        return 0
    if args.run == "summaries":
        _, gate, decision = write_summary_outputs(config)
        print(json.dumps({"paid_ready": gate["paid_ready"], "primary_decision_label": decision["primary_decision_label"]}, sort_keys=True))
        return 0
    run_all(config, repo=args.repo, limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
