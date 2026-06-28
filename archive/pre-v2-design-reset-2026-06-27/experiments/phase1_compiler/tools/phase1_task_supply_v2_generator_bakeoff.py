from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
PHASE0_TOOLS = PHASE0_ROOT / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import repo_history_pilot  # noqa: E402
import statement_quality  # noqa: E402
from phase1_historical_environment_synthesis_gate import (  # noqa: E402
    build_uv_command,
    classify_reference_subgate,
    infer_profile_candidates,
)


RUN_ID = "phase1_task_supply_v2_generator_bakeoff_20260527"
SCHEMA_VERSION = "barcarolle.phase1_task_supply_v2_generator_bakeoff.v1"
CANDIDATE_SCHEMA_VERSION = "barcarolle.task_source_candidate.v2"
RESULT_SCHEMA_VERSION = "barcarolle.task_supply_bakeoff_result.v1"
RUNBOOK = "docs/experiments/phase-1-task-supply-v2-generator-bakeoff-runbook.md"
RUNBOOK_DATE = "2026-05-27"
CURRENT_DATE = "2026-05-27"
TARGET_REPOS = ["attrs", "boltons", "toolz", "humanize"]
SCAN_SINCE = "2010-01-01"
HISTORY_SCAN_CAP = 2000
RAW_CANDIDATE_CAP_PER_REPO = 300
LOCAL_CERTIFICATION_ATTEMPT_CAP_PER_REPO = 120
EXTERNAL_FEASIBILITY_ATTEMPT_CAP_PER_REPO = 60
ENVIRONMENT_PROFILES_PER_TASK = 4

REPO_CONFIGS: dict[str, dict[str, str]] = {
    "attrs": {
        "repo_url": "https://github.com/python-attrs/attrs.git",
        "local_repo": "experiments/phase0_headroom/external_repos/attrs",
        "language": "Python",
        "package_manager_hint": "uv/hatch/pyproject",
        "test_framework_hint": "pytest+hypothesis",
        "external_service_risk": "low",
    },
    "boltons": {
        "repo_url": "https://github.com/mahmoud/boltons.git",
        "local_repo": "experiments/phase0_headroom/external_repos/boltons",
        "language": "Python",
        "package_manager_hint": "setuptools/pyproject",
        "test_framework_hint": "pytest",
        "external_service_risk": "low",
    },
    "toolz": {
        "repo_url": "https://github.com/pytoolz/toolz.git",
        "local_repo": "experiments/phase0_headroom/external_repos/toolz",
        "language": "Python",
        "package_manager_hint": "setuptools/pyproject",
        "test_framework_hint": "pytest",
        "external_service_risk": "low",
    },
    "humanize": {
        "repo_url": "https://github.com/python-humanize/humanize.git",
        "local_repo": "experiments/phase0_headroom/external_repos/humanize",
        "language": "Python",
        "package_manager_hint": "hatch/pyproject",
        "test_framework_hint": "pytest",
        "external_service_risk": "low",
    },
}

ALLOWED_SOURCE_RESERVOIRS = {
    "repo_history_v1_commit_with_tests",
    "repo_history_v2_pr_issue_with_tests",
    "repo_history_v2_commit_with_tests",
    "repo_history_v2_issue_without_changed_tests",
    "external_swe_bench_plus_plus_feasibility",
    "external_swe_smith_feasibility",
    "external_swe_bench_live_feasibility",
    "manual_or_customer_future_direction",
    "synthetic_or_generated_oracle_future_direction",
}

REQUIRED_CANDIDATE_FIELDS = [
    "schema_version",
    "candidate_id",
    "repo_id",
    "repo_url",
    "language",
    "source_system",
    "source_system_version",
    "source_reservoir",
    "source_license",
    "upstream_task_id",
    "base_commit",
    "target_commit_optional",
    "task_time",
    "source_time",
    "problem_statement",
    "problem_statement_provenance",
    "public_context_refs",
    "oracle",
    "environment",
    "changed_files",
    "implementation_files",
    "test_files",
    "reference_patch_digest_optional",
    "gold_patch_available_to_barcarolle",
    "gold_patch_exposed_to_solver",
    "leakage_flags",
    "ambiguity_flags",
    "candidate_labels",
    "source_confidence",
    "raw_artifact_paths_uncommitted",
]

IGNORED_RAW_PREFIXES = (
    "experiments/phase1_compiler/tmp/",
    "experiments/phase0_headroom/workspaces/",
    "experiments/phase0_headroom/cache/",
    "experiments/phase0_headroom/external_repos/",
)

NORMALIZED_SUBGATES = {
    "checkout_failed",
    "install_failed",
    "import_failed",
    "collect_failed",
    "noop_assert_failed",
    "reference_assert_failed",
    "reference_pass",
    "flaky_reference",
    "timeout",
    "environment_unavailable",
    "unknown_failed",
}

OUTPUTS = {
    "config": "experiments/phase1_compiler/configs/phase1_task_supply_v2_generator_bakeoff.yaml",
    "preflight": "experiments/phase1_compiler/results/phase1_task_supply_v2_preflight.json",
    "schema": "experiments/phase1_compiler/results/phase1_task_supply_v2_schema.json",
    "current_supply_reproduction": "experiments/phase1_compiler/results/phase1_task_supply_v2_current_supply_reproduction.json",
    "repo_inventory": "experiments/phase1_compiler/results/phase1_task_supply_v2_repo_inventory.json",
    "raw_anchor_inventory": "experiments/phase1_compiler/results/phase1_task_supply_v2_raw_anchor_inventory.json",
    "source_context_inventory": "experiments/phase1_compiler/results/phase1_task_supply_v2_source_context_inventory.json",
    "environment_profile_matrix": "experiments/phase1_compiler/results/phase1_task_supply_v2_environment_profile_matrix.json",
    "oracle_extraction_matrix": "experiments/phase1_compiler/results/phase1_task_supply_v2_oracle_extraction_matrix.json",
    "certification_attempts": "experiments/phase1_compiler/results/phase1_task_supply_v2_certification_attempts.json",
    "external_feasibility": "experiments/phase1_compiler/results/phase1_task_supply_v2_external_feasibility.json",
    "source_bakeoff_decision": "experiments/phase1_compiler/results/phase1_task_supply_v2_source_bakeoff_decision.json",
    "future_directions": "experiments/phase1_compiler/results/phase1_task_supply_v2_future_directions.json",
    "paid_readiness_gate": "experiments/phase1_compiler/results/phase1_task_supply_v2_paid_readiness_gate.json",
}

REPORTS = {
    "process": "experiments/phase1_compiler/reports/phase1_task_supply_v2_process.md",
    "schema": "experiments/phase1_compiler/reports/phase1_task_supply_v2_schema.md",
    "current_supply_reproduction": "experiments/phase1_compiler/reports/phase1_task_supply_v2_current_supply_reproduction.md",
    "repo_inventory": "experiments/phase1_compiler/reports/phase1_task_supply_v2_repo_inventory.md",
    "raw_anchor_inventory": "experiments/phase1_compiler/reports/phase1_task_supply_v2_raw_anchor_inventory.md",
    "source_context_inventory": "experiments/phase1_compiler/reports/phase1_task_supply_v2_source_context_inventory.md",
    "environment_profile_matrix": "experiments/phase1_compiler/reports/phase1_task_supply_v2_environment_profile_matrix.md",
    "oracle_extraction_matrix": "experiments/phase1_compiler/reports/phase1_task_supply_v2_oracle_extraction_matrix.md",
    "certification_attempts": "experiments/phase1_compiler/reports/phase1_task_supply_v2_certification_attempts.md",
    "external_feasibility": "experiments/phase1_compiler/reports/phase1_task_supply_v2_external_feasibility.md",
    "source_bakeoff_decision": "experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md",
    "future_directions": "experiments/phase1_compiler/reports/phase1_task_supply_v2_future_directions.md",
    "paid_readiness_gate": "experiments/phase1_compiler/reports/phase1_task_supply_v2_paid_readiness_gate.md",
}

SCHEMA_OUTPUTS = {
    "candidate": "experiments/phase1_compiler/schemas/task_source_candidate_v2.schema.json",
    "bakeoff_result": "experiments/phase1_compiler/schemas/task_supply_bakeoff_result_v1.schema.json",
}

REQUIRED_INPUTS = [
    "AGENTS.md",
    "docs/architecture/system-design.md",
    "docs/restart/2026-05-20-restart-consensus.md",
    "docs/experiments/phase-1-two-repo-certified-supply-expansion-runbook.md",
    "docs/experiments/phase-1-reference-pass-failure-audit-runbook.md",
    "docs/experiments/phase-1-historical-environment-synthesis-and-third-repo-gate-runbook.md",
    "<local-downloads>/barcarolle-research-0519.md",
    "<local-downloads>/barcarolle-research-0526.md",
    "<local-downloads>/barcarolle-research-0526-1.md",
    "experiments/phase0_headroom/configs/repositories.yaml",
    "experiments/phase0_headroom/tools/repo_history_pilot.py",
    "experiments/phase0_headroom/tools/statement_quality.py",
    "experiments/phase0_headroom/tools/test_repo_history_pilot.py",
    "experiments/phase0_headroom/external_repos/attrs",
    "experiments/phase0_headroom/external_repos/boltons",
    "experiments/phase0_headroom/external_repos/toolz",
    "experiments/phase0_headroom/external_repos/humanize",
    "experiments/phase1_compiler/tools/phase1_two_repo_certified_supply_expansion.py",
    "experiments/phase1_compiler/tools/phase1_reference_pass_failure_audit.py",
    "experiments/phase1_compiler/tools/phase1_historical_environment_synthesis_gate.py",
    "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_decision.json",
    "experiments/phase1_compiler/results/phase1_reference_pass_failure_audit_decision.json",
    "experiments/phase1_compiler/results/phase1_historical_environment_synthesis_decision.json",
    "experiments/phase1_compiler/results/phase1_third_repo_environment_gate_screen.json",
]

FUTURE_DIRECTION_IDS = [
    "external_swe_bench_plus_plus_adapter",
    "external_swe_smith_adapter",
    "external_swe_bench_live_adapter",
    "generated_oracle_pipeline",
    "endpoint_statement_generator_reviewer",
    "docker_or_nix_environment_factory",
    "manual_or_customer_regression_source",
    "multi_language_supply",
]


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


def output_path(key: str) -> Path:
    return repo_path(OUTPUTS[key])


def report_path(key: str) -> Path:
    return repo_path(REPORTS[key])


def read_json(path: str | Path, default: Any = None) -> Any:
    resolved = repo_path(path)
    if not resolved.exists():
        return default
    return json.loads(resolved.read_text(encoding="utf-8"))


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    resolved = repo_path(path)
    if not resolved.exists():
        return []
    return [json.loads(line) for line in resolved.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: str | Path, payload: Any) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_simple_yaml(path: str | Path, payload: dict[str, Any]) -> None:
    def scalar(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        if isinstance(value, (int, float)):
            return str(value)
        text = str(value)
        if not text or any(ch in text for ch in ":#[]{}*&!,|>'\"%@`"):
            return json.dumps(text)
        return text

    def render(value: Any, indent: int = 0) -> list[str]:
        prefix = " " * indent
        if isinstance(value, dict):
            lines: list[str] = []
            for key, item in value.items():
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.extend(render(item, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: {scalar(item)}")
            return lines
        if isinstance(value, list):
            lines = []
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}-")
                    lines.extend(render(item, indent + 2))
                else:
                    lines.append(f"{prefix}- {scalar(item)}")
            return lines
        return [f"{prefix}{scalar(value)}"]

    write_text(path, "\n".join(render(payload)))


def command_result(args: list[str], cwd: Path = REPO_ROOT, timeout: int = 120) -> dict[str, Any]:
    start = time.monotonic()
    try:
        proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        return {"args": args, "returncode": 127, "stdout": "", "stderr": str(exc), "duration_seconds": 0.0}
    except subprocess.TimeoutExpired as exc:
        return {
            "args": args,
            "returncode": 124,
            "stdout": str(exc.stdout or ""),
            "stderr": str(exc.stderr or ""),
            "duration_seconds": round(time.monotonic() - start, 3),
        }
    return {
        "args": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "duration_seconds": round(time.monotonic() - start, 3),
    }


def command_stdout(args: list[str], cwd: Path = REPO_ROOT) -> str:
    result = command_result(args, cwd=cwd)
    return result["stdout"] if result["returncode"] == 0 else result["stderr"]


def git_lines(repo: Path, args: list[str], timeout: int = 120) -> list[str]:
    result = command_result(["git", *args], cwd=repo, timeout=timeout)
    if result["returncode"] != 0:
        raise RuntimeError(result["stderr"])
    return result["stdout"].splitlines()


def short_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def digest_payload(value: Any) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value or "")
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def repo_dir(repo_id: str) -> Path:
    return repo_path(REPO_CONFIGS[repo_id]["local_repo"])


def target_commit(row: dict[str, Any]) -> str:
    return str(row.get("target_commit_optional") or row.get("target_commit") or row.get("commit") or "")


def task_id(row: dict[str, Any]) -> str:
    return str(row.get("candidate_id") or row.get("task_id") or row.get("original_task_id") or "")


def is_linkable_subject(subject: str) -> bool:
    text = subject.lower()
    return bool(re.search(r"(?:fixe?s?|close[sd]?|resolve[sd]?|issue|pr|pull request)\s+#?\d+|#\d+", text))


def issue_refs_from_text(text: str) -> list[str]:
    return unique(f"issue:{match.group(1)}" for match in re.finditer(r"#(\d+)", text))


def detect_license(repo_id: str) -> str:
    candidates = ["LICENSE", "LICENSE.txt", "LICENCE", "LICENSE.md"]
    for name in candidates:
        path = repo_dir(repo_id) / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if "mit license" in text or "permission is hereby granted" in text:
            return "MIT"
        if "redistribution and use in source and binary forms" in text:
            return "BSD-style"
        if "apache license" in text:
            return "Apache-2.0"
        return "present_unknown"
    return "missing"


def implementation_files_from_row(row: dict[str, Any]) -> list[str]:
    explicit = row.get("code_files") or row.get("implementation_files") or []
    if explicit:
        return sorted(str(path) for path in explicit)
    changed = [str(path) for path in row.get("changed_files", [])]
    return statement_quality.implementation_files(changed)


def test_files_from_row(row: dict[str, Any]) -> list[str]:
    explicit = row.get("test_files") or row.get("candidate_oracle_source") or []
    if explicit:
        return sorted(str(path) for path in explicit)
    changed = [str(path) for path in row.get("changed_files", [])]
    return statement_quality.test_files(changed)


def module_names(row: dict[str, Any]) -> list[str]:
    modules = row.get("module_or_package")
    if isinstance(modules, str):
        return [modules] if modules else []
    if isinstance(modules, list):
        return [str(item) for item in modules if item]
    return repo_history_pilot.module_names(implementation_files_from_row(row))


def candidate_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://barcarolle.local/schemas/task_source_candidate_v2.schema.json",
        "title": "Barcarolle TaskSourceCandidate v2",
        "type": "object",
        "required": REQUIRED_CANDIDATE_FIELDS,
        "additionalProperties": True,
        "properties": {
            "schema_version": {"const": CANDIDATE_SCHEMA_VERSION},
            "candidate_id": {"type": "string", "minLength": 1},
            "repo_id": {"type": "string", "minLength": 1},
            "repo_url": {"type": "string", "minLength": 1},
            "language": {"type": "string", "minLength": 1},
            "source_reservoir": {"enum": sorted(ALLOWED_SOURCE_RESERVOIRS)},
            "base_commit": {"type": "string", "minLength": 7},
            "oracle": {
                "type": "object",
                "required": ["fail_to_pass", "pass_to_pass", "oracle_source"],
                "properties": {
                    "fail_to_pass": {"type": "array", "items": {"type": "string"}},
                    "pass_to_pass": {"type": "array", "items": {"type": "string"}},
                    "oracle_source": {"type": "string", "minLength": 1},
                },
            },
            "environment": {
                "type": "object",
                "required": ["kind", "profile_id", "command_shape", "dependency_time_policy"],
            },
            "gold_patch_exposed_to_solver": {"const": False},
            "raw_artifact_paths_uncommitted": {"type": "array", "items": {"type": "string"}},
        },
    }


def bakeoff_result_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://barcarolle.local/schemas/task_supply_bakeoff_result_v1.schema.json",
        "title": "Barcarolle Task Supply Bakeoff Result v1",
        "type": "object",
        "required": ["schema_version", "run_id", "generated_at", "status"],
        "properties": {
            "schema_version": {"const": RESULT_SCHEMA_VERSION},
            "run_id": {"type": "string"},
            "generated_at": {"type": "string"},
            "status": {"type": "string"},
        },
        "additionalProperties": True,
    }


def validate_candidate(row: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_CANDIDATE_FIELDS if field not in row]
    if missing:
        raise ValueError(f"candidate missing required fields: {', '.join(missing)}")
    if row["schema_version"] != CANDIDATE_SCHEMA_VERSION:
        raise ValueError(f"unexpected candidate schema_version: {row['schema_version']}")
    if row["source_reservoir"] not in ALLOWED_SOURCE_RESERVOIRS:
        raise ValueError(f"unsupported source_reservoir: {row['source_reservoir']}")
    if not str(row.get("candidate_id", "")).strip():
        raise ValueError("candidate_id is required")
    if len(str(row.get("base_commit", ""))) < 7:
        raise ValueError("base_commit must look like a git commit")
    oracle = row.get("oracle")
    if not isinstance(oracle, dict):
        raise ValueError("oracle must be an object")
    if not isinstance(oracle.get("fail_to_pass"), list) or not isinstance(oracle.get("pass_to_pass"), list):
        raise ValueError("oracle fail_to_pass and pass_to_pass must be lists")
    if not str(oracle.get("oracle_source", "")).strip():
        raise ValueError("oracle oracle_source is required")
    environment = row.get("environment")
    if not isinstance(environment, dict):
        raise ValueError("environment must be an object")
    for key in ["kind", "profile_id", "command_shape", "dependency_time_policy"]:
        if key not in environment:
            raise ValueError(f"environment missing {key}")
    if row.get("gold_patch_exposed_to_solver") is not False:
        raise ValueError("gold_patch_exposed_to_solver must be false")
    for key in ["public_context_refs", "changed_files", "implementation_files", "test_files", "leakage_flags", "ambiguity_flags", "candidate_labels", "raw_artifact_paths_uncommitted"]:
        if not isinstance(row.get(key), list):
            raise ValueError(f"{key} must be a list")
    for raw_path in row.get("raw_artifact_paths_uncommitted", []):
        if not str(raw_path).startswith(IGNORED_RAW_PREFIXES):
            raise ValueError(f"raw artifact path is not under an ignored scratch prefix: {raw_path}")
    return row


def source_context_rows() -> dict[tuple[str, str], dict[str, Any]]:
    contexts: dict[tuple[str, str], dict[str, Any]] = {}
    for path in sorted((PHASE0_ROOT / "candidate_sources").glob("*source_context*.jsonl")):
        for row in read_jsonl(path):
            repo_id = str(row.get("repo_id") or "").strip()
            keys = unique([str(row.get("target_commit") or ""), str(row.get("task_id") or ""), str(row.get("original_task_id") or "")])
            for key in keys:
                if repo_id and key:
                    contexts[(repo_id, key)] = {**row, "_artifact_path": rel(path)}
    return contexts


def context_for(row: dict[str, Any], contexts: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    repo_id = str(row.get("repo_id") or "")
    for key in [str(row.get("target_commit") or ""), str(row.get("target_commit_optional") or ""), task_id(row), str(row.get("original_task_id") or "")]:
        if key and (repo_id, key) in contexts:
            return contexts[(repo_id, key)]
    return {}


def source_refs_from_context(context: dict[str, Any], row: dict[str, Any]) -> list[str]:
    refs = []
    for key in ["source_ref", "ref"]:
        if context.get(key):
            refs.append(str(context[key]))
    for item in context.get("source_items", []) or []:
        if item.get("solver_usable") is True and item.get("source_id"):
            refs.append(str(item["source_id"]))
    for ref in context.get("linked_issue_refs", []) or context.get("linked_issues", []) or []:
        text = str(ref)
        refs.append(text if ":" in text else f"issue:{text}")
    refs.extend(str(item) for item in row.get("source_text_pointers", []) if item)
    if not refs and row.get("target_commit"):
        refs.append(f"commit:{row['target_commit']}")
    return unique(refs)


def classify_context_quality(candidate: dict[str, Any], context: dict[str, Any] | None = None) -> str:
    context = context or {}
    status = str(context.get("source_context_status") or context.get("classification") or "").lower()
    source_kind = str(context.get("source_kind") or statement_quality.source_kind(str(context.get("source_ref") or context.get("ref") or ""))).lower()
    refs = [str(ref) for ref in candidate.get("public_context_refs", [])]
    leakage_flags = [str(flag) for flag in candidate.get("leakage_flags", [])]
    if "leakage" in status or any("leak" in flag or "solution" in flag for flag in leakage_flags):
        return "material_leakage_risk"
    if "non_leaky" in status or status == "problem_context" or source_kind == "issue" or any(ref.startswith("issue:") for ref in refs):
        return "non_leaky_issue_or_pr_context"
    if source_kind in {"pull_request", "pr"} or any(ref.startswith("pr:") for ref in refs):
        return "pr_title_only_context"
    if any(ref.startswith("commit:") for ref in refs) or candidate.get("problem_statement_provenance") == "commit_subject_only":
        return "commit_message_only_context"
    if not refs:
        return "no_usable_public_context"
    return "material_ambiguity_risk"


def v1_row_to_candidate(
    row: dict[str, Any],
    *,
    source_artifact: str = "",
    source_reservoir: str = "repo_history_v1_commit_with_tests",
    context: dict[str, Any] | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    repo_id = str(row.get("repo_id") or "")
    context = context or {}
    target = str(row.get("target_commit") or row.get("commit") or "")
    subject = str(row.get("subject") or row.get("problem_statement_draft") or context.get("summary") or "")
    problem_statement = str(row.get("solver_facing_statement") or row.get("problem_statement_draft") or context.get("summary") or subject or "No public statement available.")
    public_context_refs = source_refs_from_context(context, row)
    tests = test_files_from_row(row)
    impl = implementation_files_from_row(row)
    changed = [str(path) for path in row.get("changed_files", [])]
    leakage_flags = unique([str(item) for item in row.get("leakage_risks", [])] + [str(item) for item in context.get("source_leakage_risks", [])])
    if problem_statement == subject and not context:
        provenance = "commit_subject_only"
    elif context:
        provenance = "public_source_context"
    else:
        provenance = str(row.get("problem_statement_source") or "existing_sanitized_statement")
    candidate = {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "candidate_id": candidate_id or str(row.get("task_id") or f"{repo_id}__v1__{short_digest(target or subject)}"),
        "repo_id": repo_id,
        "repo_url": str(row.get("repo_url") or REPO_CONFIGS.get(repo_id, {}).get("repo_url") or ""),
        "language": str(REPO_CONFIGS.get(repo_id, {}).get("language") or "Python"),
        "source_system": "repo_history_v1",
        "source_system_version": str(row.get("schema_version") or "barcarolle.repo_history_candidate.v1"),
        "source_reservoir": source_reservoir,
        "source_license": detect_license(repo_id) if repo_id in REPO_CONFIGS else "unknown",
        "upstream_task_id": str(row.get("task_id") or target or subject),
        "base_commit": str(row.get("base_commit") or row.get("parent") or ""),
        "target_commit_optional": target,
        "task_time": str(row.get("task_time") or row.get("source_time") or ""),
        "source_time": str(context.get("timestamp") or row.get("task_time") or ""),
        "problem_statement": problem_statement,
        "problem_statement_provenance": provenance,
        "public_context_refs": public_context_refs,
        "oracle": {
            "fail_to_pass": tests,
            "pass_to_pass": [],
            "oracle_source": "changed_tests_from_repo_history" if tests else "missing_oracle",
        },
        "environment": {
            "kind": "uv_pytest",
            "profile_id": "baseline_current_or_inferred",
            "command_shape": "uv run --no-project --isolated --managed-python python -m pytest -q <test_files>",
            "dependency_time_policy": "baseline_plus_historical_exclude_newer",
        },
        "changed_files": changed,
        "implementation_files": impl,
        "test_files": tests,
        "reference_patch_digest_optional": digest_payload({"target_commit": target, "test_files": tests}) if target and tests else "",
        "gold_patch_available_to_barcarolle": bool(target),
        "gold_patch_exposed_to_solver": False,
        "leakage_flags": leakage_flags,
        "ambiguity_flags": [] if problem_statement.strip() else ["missing_problem_statement"],
        "candidate_labels": unique([str(row.get("task_type_proxy") or "behavior_or_feature_or_bugfix"), *module_names(row)]),
        "source_confidence": "medium" if context else "low",
        "raw_artifact_paths_uncommitted": [],
        "sanitized_artifact_refs": [source_artifact] if source_artifact else [],
    }
    return validate_candidate(candidate)


def build_config() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "runbook": RUNBOOK,
        "runbook_date": RUNBOOK_DATE,
        "status": "configured",
        "target_repos": TARGET_REPOS,
        "caps": {
            "history_scan_since": SCAN_SINCE,
            "history_scan_cap_per_repo": HISTORY_SCAN_CAP,
            "raw_candidate_cap_per_repo_per_source_arm": RAW_CANDIDATE_CAP_PER_REPO,
            "local_certification_attempt_cap_per_repo_for_repo_history_v2": LOCAL_CERTIFICATION_ATTEMPT_CAP_PER_REPO,
            "local_certification_attempt_cap_per_repo_for_external_feasibility": EXTERNAL_FEASIBILITY_ATTEMPT_CAP_PER_REPO,
            "environment_profiles_per_task": ENVIRONMENT_PROFILES_PER_TASK,
            "single_command_timeout_seconds": 120,
            "single_task_total_certification_timeout_seconds": 600,
        },
        "budget": {
            "paid_acut_calls": "disabled",
            "paid_task_solving_calls": "disabled",
            "paid_replication": "disabled",
            "paid_llm_statement_generation": "disabled",
            "provider_cost_change": 0,
        },
        "repos": REPO_CONFIGS,
        "source_reservoirs": sorted(ALLOWED_SOURCE_RESERVOIRS),
        "outputs": OUTPUTS,
        "reports": REPORTS,
        "scratch_paths": {
            "tmp": "experiments/phase1_compiler/tmp/task_supply_v2_generator_bakeoff/",
            "workspaces": "experiments/phase0_headroom/workspaces/task_supply_v2_generator_bakeoff/",
            "cache": "experiments/phase0_headroom/cache/task_supply_v2_generator_bakeoff/",
            "external_repos": "experiments/phase0_headroom/external_repos/",
        },
    }


def preflight_payload(config: dict[str, Any]) -> dict[str, Any]:
    required = []
    for item in REQUIRED_INPUTS:
        path = repo_path(item)
        required.append(
            {
                "path": item,
                "present": path.exists(),
                "kind": "directory" if path.is_dir() else "file",
            }
        )
    repo_rows = []
    for repo_id in TARGET_REPOS:
        path = repo_dir(repo_id)
        repo_rows.append(
            {
                "repo_id": repo_id,
                "local_repo": rel(path),
                "present": path.exists(),
                "is_git_repo": (path / ".git").exists(),
            }
        )
    scratch_checks = []
    for raw in config["scratch_paths"].values():
        check = command_result(["git", "check-ignore", "-v", raw], cwd=REPO_ROOT)
        scratch_checks.append(
            {
                "path": raw,
                "ignored": check["returncode"] == 0,
                "git_check_ignore": check["stdout"] or check["stderr"],
            }
        )
    gh = command_result(["gh", "auth", "status"], cwd=REPO_ROOT)
    return {
        "schema_version": f"{SCHEMA_VERSION}.preflight.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "task_supply_v2_preflight_completed",
        "branch": command_stdout(["git", "branch", "--show-current"]),
        "head": command_stdout(["git", "rev-parse", "HEAD"]),
        "date": CURRENT_DATE,
        "python_version": sys.version.split()[0],
        "uv_version": command_stdout(["uv", "--version"]),
        "git_status_short": command_stdout(["git", "status", "--short"]).splitlines(),
        "gh_auth": {
            "checked": True,
            "authenticated": gh["returncode"] == 0,
            "summary": (gh["stdout"] or gh["stderr"]).splitlines()[:4],
        },
        "required_inputs": required,
        "missing_required_inputs": [row["path"] for row in required if not row["present"]],
        "target_repos": repo_rows,
        "scratch_paths": scratch_checks,
        "paid_acut_calls": "disabled",
        "paid_task_solving_calls": "disabled",
        "paid_replication": "disabled",
        "paid_llm_calls": "disabled",
        "raw_artifacts_committed": False,
        "hidden_oracle_material_used": False,
        "raw_acut_transcripts_used": False,
        "process_scope": "supply-layer bakeoff, not benchmark validation",
        "claims": ["task_supply_v2_preflight_completed", "no_paid_acut_calls_made", "no_paid_llm_statement_generation_made"],
    }


def candidate_artifact_paths(repo_id: str) -> list[Path]:
    return sorted((PHASE0_ROOT / "candidate_sources").glob(f"{repo_id}*candidates.jsonl"))


def source_context_artifact_paths(repo_id: str) -> list[Path]:
    return sorted((PHASE0_ROOT / "candidate_sources").glob(f"{repo_id}*source_context*.jsonl"))


def certification_artifact_paths(repo_id: str) -> list[Path]:
    return sorted((PHASE0_ROOT / "certified_tasks").glob(f"{repo_id}*.jsonl"))


def unique_rows_by_task(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("target_commit") or row.get("task_id") or row.get("original_task_id") or "")
        if not key:
            key = short_digest(json.dumps(row, sort_keys=True))
        out[key] = {**out.get(key, {}), **row}
    return out


def load_artifact_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        for row in read_jsonl(path):
            rows.append({**row, "_artifact_path": rel(path)})
    return rows


def current_supply_reproduction() -> dict[str, Any]:
    expansion_decision = read_json("experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_decision.json", default={}) or {}
    third_repo_screen = read_json("experiments/phase1_compiler/results/phase1_third_repo_environment_gate_screen.json", default={}) or {}
    rows = []
    for repo_id in TARGET_REPOS:
        candidate_rows = load_artifact_rows(candidate_artifact_paths(repo_id))
        source_rows = load_artifact_rows(source_context_artifact_paths(repo_id))
        cert_rows = load_artifact_rows(
            path
            for path in certification_artifact_paths(repo_id)
            if path.name.endswith("_certified_tasks.jsonl") and "near_certified" not in path.name
        )
        near_rows = load_artifact_rows(path for path in certification_artifact_paths(repo_id) if "near_certified" in path.name)
        review_rows = load_artifact_rows(path for path in certification_artifact_paths(repo_id) if "review_records" in path.name)
        first_failing = Counter(str(row.get("first_failing_gate") or row.get("review_first_failing_gate") or "unknown") for row in review_rows if row.get("first_failing_gate") or row.get("review_first_failing_gate"))
        context_quality = Counter()
        for context in source_rows:
            status = str(context.get("source_context_status") or context.get("classification") or "")
            if "non_leaky" in status or status == "problem_context":
                context_quality["public_issue_or_pr_context"] += 1
            elif "commit" in status or str(context.get("source_kind", "")).startswith("commit"):
                context_quality["commit_message_only"] += 1
            elif "risk" in status:
                context_quality["material_risk"] += 1
            else:
                context_quality["other_or_unknown"] += 1
        reference_failures = sum(count for gate, count in first_failing.items() if "reference" in gate or gate == "reference_pass")
        eligible_from_decision = None
        if repo_id in (expansion_decision.get("counts_by_repo") or {}):
            eligible_from_decision = expansion_decision["counts_by_repo"][repo_id].get("total_eligible")
        for screen in third_repo_screen.get("repo_screens", []):
            if screen.get("repo_id") == repo_id:
                eligible_from_decision = screen.get("certified_candidate_count")
        rows.append(
            {
                "repo_id": repo_id,
                "raw_candidate_rows": len(candidate_rows),
                "unique_raw_candidates": len(unique_rows_by_task(candidate_rows)),
                "source_context_rows": len(source_rows),
                "certified_rows": len(cert_rows),
                "near_certified_rows": len(near_rows),
                "review_rows": len(review_rows),
                "eligible_count_from_prior_decision": eligible_from_decision,
                "first_failing_gate_counts": dict(sorted(first_failing.items())),
                "commit_message_only_count": context_quality.get("commit_message_only", 0),
                "public_pr_or_issue_context_count": context_quality.get("public_issue_or_pr_context", 0),
                "reference_or_environment_failure_count": reference_failures,
                "candidate_artifacts": [rel(path) for path in candidate_artifact_paths(repo_id)],
                "source_context_artifacts": [rel(path) for path in source_context_artifact_paths(repo_id)],
                "certification_artifacts": [rel(path) for path in certification_artifact_paths(repo_id)],
            }
        )
    return {
        "schema_version": f"{SCHEMA_VERSION}.current_supply_reproduction.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "repo_history_v1_reproduction_completed",
        "basis": "committed local artifacts only; this is not new mining",
        "warning": "toolz and humanize old 16-candidate screens are narrow artifacts, not broad repo-supply conclusions",
        "rows": rows,
        "claims": ["repo_history_v1_reproduction_completed"],
        "paid_calls_made": False,
    }


def parse_git_log(repo: Path) -> list[dict[str, Any]]:
    raw = command_result(
        [
            "git",
            "log",
            f"--since={SCAN_SINCE}",
            f"--max-count={HISTORY_SCAN_CAP}",
            "--reverse",
            "--format=%x1e%H%x09%P%x09%ad%x09%s",
            "--date=iso-strict",
            "--name-only",
        ],
        cwd=repo,
        timeout=120,
    )
    if raw["returncode"] != 0:
        raise RuntimeError(raw["stderr"])
    commits: list[dict[str, Any]] = []
    for chunk in raw["stdout"].split("\x1e"):
        lines = [line for line in chunk.splitlines() if line.strip()]
        if not lines:
            continue
        meta = lines[0].split("\t", 3)
        if len(meta) != 4:
            continue
        commit, parents, commit_time, subject = meta
        paths = lines[1:]
        code_files, test_files = repo_history_pilot.classify_paths(paths)
        commits.append(
            {
                "commit": commit,
                "parent": parents.split()[0] if parents.split() else "",
                "task_time": commit_time,
                "subject": subject,
                "changed_files": paths,
                "code_files": code_files,
                "test_files": test_files,
                "has_code": bool(code_files),
                "has_tests": bool(test_files),
                "linkable": is_linkable_subject(subject),
            }
        )
    return commits


def repo_inventory() -> dict[str, Any]:
    rows = []
    for repo_id in TARGET_REPOS:
        path = repo_dir(repo_id)
        if not path.exists():
            rows.append({"repo_id": repo_id, "present": False, "blocker": "local_repo_missing"})
            continue
        try:
            commits = parse_git_log(path)
            default_branch = command_stdout(["git", "branch", "--show-current"], cwd=path) or command_stdout(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path)
            head = command_stdout(["git", "rev-parse", "HEAD"], cwd=path)
            visible_link_count = sum(1 for row in commits if row["linkable"])
            rows.append(
                {
                    "repo_id": repo_id,
                    "present": True,
                    "local_repo": rel(path),
                    "repo_url": REPO_CONFIGS[repo_id]["repo_url"],
                    "default_branch": default_branch,
                    "head": head,
                    "commit_count_since_2010_or_cap": len(commits),
                    "commit_count_with_implementation_changes": sum(1 for row in commits if row["has_code"]),
                    "commit_count_with_test_changes": sum(1 for row in commits if row["has_tests"]),
                    "commit_count_with_both_implementation_and_test_changes": sum(1 for row in commits if row["has_code"] and row["has_tests"]),
                    "visible_issue_or_pr_linkability_signal": {
                        "commit_subject_refs": visible_link_count,
                        "rate": round(visible_link_count / len(commits), 3) if commits else 0,
                    },
                    "test_framework_hints": REPO_CONFIGS[repo_id]["test_framework_hint"],
                    "package_manager_hints": REPO_CONFIGS[repo_id]["package_manager_hint"],
                    "known_external_service_risk": REPO_CONFIGS[repo_id]["external_service_risk"],
                    "source_license": detect_license(repo_id),
                    "worth_broad_mining_first": sum(1 for row in commits if row["has_code"] and (row["has_tests"] or row["linkable"])) >= 30,
                }
            )
        except Exception as exc:
            rows.append({"repo_id": repo_id, "present": True, "local_repo": rel(path), "blocker": str(exc)})
    return {
        "schema_version": f"{SCHEMA_VERSION}.repo_inventory.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "repo_inventory_completed",
        "history_scan_cap_per_repo": HISTORY_SCAN_CAP,
        "rows": rows,
        "claims": ["repo_inventory_completed"],
    }


def reservoir_for_commit(commit: dict[str, Any]) -> str:
    if commit["has_code"] and commit["has_tests"] and commit["linkable"]:
        return "repo_history_v2_pr_issue_with_tests"
    if commit["has_code"] and commit["has_tests"]:
        return "repo_history_v2_commit_with_tests"
    if commit["has_code"] and commit["linkable"]:
        return "repo_history_v2_issue_without_changed_tests"
    return ""


def broad_mining_candidates(contexts: dict[tuple[str, str], dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}
    for repo_id in TARGET_REPOS:
        path = repo_dir(repo_id)
        repo_candidates: list[dict[str, Any]] = []
        repo_summary = Counter()
        if not path.exists():
            summary[repo_id] = {"blocker": "local_repo_missing"}
            continue
        for commit in parse_git_log(path):
            reservoir = reservoir_for_commit(commit)
            if not reservoir:
                continue
            if not commit["parent"]:
                continue
            context = context_for({"repo_id": repo_id, "target_commit": commit["commit"]}, contexts)
            row = {
                "repo_id": repo_id,
                "repo_url": REPO_CONFIGS[repo_id]["repo_url"],
                "task_id": f"{repo_id}__v2__{len(repo_candidates) + 1:03d}",
                "base_commit": commit["parent"],
                "target_commit": commit["commit"],
                "task_time": commit["task_time"],
                "subject": commit["subject"],
                "changed_files": commit["changed_files"],
                "code_files": commit["code_files"],
                "test_files": commit["test_files"],
                "candidate_oracle_source": commit["test_files"],
                "source_type": "git_commit",
                "schema_version": "barcarolle.repo_history_v2_anchor.v1",
                "status": "selected_for_v2_bakeoff_inventory",
            }
            candidate = v1_row_to_candidate(
                row,
                source_artifact=rel(path),
                source_reservoir=reservoir,
                context=context,
                candidate_id=row["task_id"],
            )
            candidate["source_system"] = "repo_history_v2"
            candidate["source_system_version"] = "barcarolle.repo_history_v2_anchor.v1"
            candidate["candidate_labels"] = unique(
                [
                    *candidate["candidate_labels"],
                    "source_context_linkable" if commit["linkable"] else "source_context_commit_only",
                    "changed_tests_present" if commit["has_tests"] else "no_changed_tests",
                ]
            )
            candidate["dedup_key"] = digest_payload(
                {
                    "repo_id": repo_id,
                    "base_commit": candidate["base_commit"],
                    "target_commit": candidate["target_commit_optional"],
                    "problem_context_ref": candidate["public_context_refs"][:1],
                    "implementation_path_set": candidate["implementation_files"],
                    "oracle_path_set": candidate["test_files"],
                }
            )
            repo_candidates.append(validate_candidate(candidate))
            repo_summary[reservoir] += 1
            if len(repo_candidates) >= RAW_CANDIDATE_CAP_PER_REPO:
                break
        candidates.extend(repo_candidates)
        summary[repo_id] = {
            "raw_v2_candidate_count": len(repo_candidates),
            "reservoir_counts": dict(sorted(repo_summary.items())),
            "cap_hit": len(repo_candidates) >= RAW_CANDIDATE_CAP_PER_REPO,
        }
    return candidates, summary


def raw_anchor_inventory(candidates: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    rows = [
        {
            "candidate_id": row["candidate_id"],
            "repo_id": row["repo_id"],
            "source_reservoir": row["source_reservoir"],
            "base_commit": row["base_commit"],
            "target_commit_optional": row["target_commit_optional"],
            "task_time": row["task_time"],
            "public_context_refs": row["public_context_refs"][:3],
            "implementation_files": row["implementation_files"],
            "test_files": row["test_files"],
            "has_usable_oracle": bool(row["test_files"]),
            "dedup_key": row.get("dedup_key", ""),
        }
        for row in candidates
    ]
    return {
        "schema_version": f"{SCHEMA_VERSION}.raw_anchor_inventory.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "repo_history_v2_broad_mining_completed",
        "history_scan_cap_per_repo": HISTORY_SCAN_CAP,
        "raw_candidate_cap_per_repo": RAW_CANDIDATE_CAP_PER_REPO,
        "summary_by_repo": summary,
        "candidate_count": len(rows),
        "rows": rows,
        "claims": ["repo_history_v2_broad_mining_completed"],
        "raw_api_payloads_committed": False,
    }


def source_context_inventory(candidates: list[dict[str, Any]], contexts: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    rows = []
    counts_by_repo: dict[str, Counter[str]] = defaultdict(Counter)
    counts_by_reservoir: dict[str, Counter[str]] = defaultdict(Counter)
    for candidate in candidates:
        context = context_for(candidate, contexts)
        quality = classify_context_quality(candidate, context)
        counts_by_repo[candidate["repo_id"]][quality] += 1
        counts_by_reservoir[candidate["source_reservoir"]][quality] += 1
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "repo_id": candidate["repo_id"],
                "source_reservoir": candidate["source_reservoir"],
                "source_context_quality": quality,
                "problem_statement_provenance": candidate["problem_statement_provenance"],
                "public_context_refs": candidate["public_context_refs"],
                "leakage_flags": candidate["leakage_flags"],
                "ambiguity_flags": candidate["ambiguity_flags"],
            }
        )
    return {
        "schema_version": f"{SCHEMA_VERSION}.source_context_inventory.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "source_context_inventory_completed",
        "counts_by_repo": {repo: dict(sorted(counter.items())) for repo, counter in sorted(counts_by_repo.items())},
        "counts_by_source_reservoir": {repo: dict(sorted(counter.items())) for repo, counter in sorted(counts_by_reservoir.items())},
        "rows": rows,
        "claims": ["source_context_inventory_completed"],
    }


def normalize_subgate_label(raw: str) -> str:
    text = str(raw or "").lower()
    mapping = {
        "checkout": "checkout_failed",
        "checkout_failed": "checkout_failed",
        "install": "install_failed",
        "reference_install_failed": "install_failed",
        "import": "import_failed",
        "reference_import_failed": "import_failed",
        "collect": "collect_failed",
        "reference_collect_failed": "collect_failed",
        "noop": "noop_assert_failed",
        "no_op_fail": "noop_assert_failed",
        "reference_assert": "reference_assert_failed",
        "reference_assert_failed": "reference_assert_failed",
        "reference_pass": "reference_pass",
        "flaky": "flaky_reference",
        "timeout": "timeout",
        "reference_timeout": "timeout",
        "environment_unavailable": "environment_unavailable",
        "reference_environment_unavailable": "environment_unavailable",
    }
    for needle, label in mapping.items():
        if needle in text:
            return label
    return "unknown_failed"


def environment_profile_matrix(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    profile_counts = Counter()
    command_shapes = {}
    for candidate in candidates:
        profiles = infer_profile_candidates(candidate["repo_id"], candidate["task_time"], REPO_CONFIGS[candidate["repo_id"]])[:ENVIRONMENT_PROFILES_PER_TASK]
        profile_ids = [profile.profile_id for profile in profiles]
        for profile_id in profile_ids:
            profile_counts[profile_id] += 1
        first_command = build_uv_command(profiles[0], Path("<target_workspace>"), candidate["test_files"]) if profiles else []
        command_shapes[candidate["candidate_id"]] = [str(part) for part in first_command]
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "repo_id": candidate["repo_id"],
                "source_reservoir": candidate["source_reservoir"],
                "profile_ids": profile_ids,
                "profile_count": len(profile_ids),
                "baseline_profile_id": profile_ids[0] if profile_ids else "",
                "command_shape": " ".join(str(part) for part in first_command),
                "dependency_time_policy": "exclude_newer_relative_to_task_time",
                "raw_stdout_stderr_storage": "experiments/phase1_compiler/tmp/task_supply_v2_generator_bakeoff/",
            }
        )
    return {
        "schema_version": f"{SCHEMA_VERSION}.environment_profile_matrix.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "historical_environment_subgate_integration_completed",
        "profile_counts": dict(sorted(profile_counts.items())),
        "rows": rows,
        "subgate_labels": sorted(NORMALIZED_SUBGATES),
        "raw_logs_committed": False,
        "claims": ["historical_environment_subgate_integration_completed"],
    }


def oracle_extraction_matrix(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    counts = Counter()
    for candidate in candidates:
        if candidate["test_files"]:
            classification = "changed_test_oracle_available"
            oracle_source = "changed_tests_from_repo_history"
        elif candidate["source_reservoir"] == "repo_history_v2_issue_without_changed_tests":
            classification = "oracle_requires_generated_tests"
            oracle_source = "missing_oracle"
        else:
            classification = "oracle_missing"
            oracle_source = "missing_oracle"
        counts[classification] += 1
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "repo_id": candidate["repo_id"],
                "source_reservoir": candidate["source_reservoir"],
                "oracle_classification": classification,
                "oracle_source": oracle_source,
                "fail_to_pass": candidate["oracle"]["fail_to_pass"],
                "generated_oracle_promoted_to_eval": False,
                "recovered_existing_test_oracle": classification == "changed_test_oracle_available",
            }
        )
    return {
        "schema_version": f"{SCHEMA_VERSION}.oracle_extraction_matrix.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "oracle_extraction_inventory_completed",
        "oracle_classification_counts": dict(sorted(counts.items())),
        "rows": rows,
        "generated_oracle_tasks_promoted_to_eval_pool": False,
        "claims": ["oracle_extraction_inventory_completed"],
    }


def known_certification_index() -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for repo_id in TARGET_REPOS:
        for path in certification_artifact_paths(repo_id):
            if any(marker in path.name for marker in ["task_statements"]):
                continue
            for row in read_jsonl(path):
                target = str(row.get("target_commit") or "")
                tid = str(row.get("task_id") or row.get("original_task_id") or "")
                enriched = {**row, "_artifact_path": rel(path)}
                if target:
                    index[(repo_id, target)] = {**index.get((repo_id, target), {}), **enriched}
                if tid:
                    index[(repo_id, tid)] = {**index.get((repo_id, tid), {}), **enriched}
    attempts = read_json("experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_certification_attempts.json", default={}) or {}
    for row in attempts.get("rows", []):
        repo_id = str(row.get("repo_id") or "")
        target = str(row.get("target_commit") or "")
        tid = str(row.get("task_id") or row.get("original_task_id") or "")
        enriched = {**row, "_artifact_path": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_certification_attempts.json"}
        if repo_id and target:
            index[(repo_id, target)] = {**index.get((repo_id, target), {}), **enriched}
        if repo_id and tid:
            index[(repo_id, tid)] = {**index.get((repo_id, tid), {}), **enriched}
    return index


def historical_subgate_index() -> dict[tuple[str, str], dict[str, Any]]:
    replay = read_json("experiments/phase1_compiler/results/phase1_historical_environment_known_failure_replay_matrix.json", default={}) or {}
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in replay.get("rows", []):
        repo_id = str(row.get("repo_id") or "")
        target = str(row.get("target_commit") or "")
        tid = str(row.get("task_id") or "")
        value = {
            "terminal_subgate_label": str(row.get("terminal_subgate_label") or ""),
            "recovered_reference_pass": bool(row.get("recovered_reference_pass")),
            "profiles_tried": row.get("profiles_tried", []),
        }
        if repo_id and target:
            index[(repo_id, target)] = value
        if repo_id and tid:
            index[(repo_id, tid)] = value
    return index


def status_from_known(row: dict[str, Any]) -> str:
    if row.get("status") in {"certified", "near_certified", "rejected"}:
        return str(row["status"])
    if row.get("promotion_decision") == "promote_to_clean_benchmark_candidate":
        return "certified"
    if row.get("first_failing_gate"):
        return "near_certified" if row.get("oracle_extractable") == "pass" else "rejected"
    return "unknown"


def attempt_subgate_label(known: dict[str, Any], status: str, historical: dict[str, Any] | None = None) -> str:
    if status == "certified":
        return "reference_pass"
    historical = historical or {}
    terminal = str(historical.get("terminal_subgate_label") or "")
    if terminal:
        return normalize_subgate_label(terminal)
    raw = str(known.get("subgate_label") or known.get("terminal_subgate_label") or "")
    if raw:
        return normalize_subgate_label(raw)
    first_gate = str(known.get("first_failing_gate") or known.get("review_first_failing_gate") or "")
    if first_gate == "reference_pass" and status != "certified":
        return "unknown_failed"
    return normalize_subgate_label(first_gate or status)


def certification_attempts(candidates: list[dict[str, Any]], contexts: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    index = known_certification_index()
    historical_index = historical_subgate_index()
    rows = []
    summary: dict[str, Counter[str]] = defaultdict(Counter)
    subgates: dict[str, Counter[str]] = defaultdict(Counter)
    durations: dict[str, list[float]] = defaultdict(list)
    for candidate in candidates:
        known = index.get((candidate["repo_id"], candidate["target_commit_optional"])) or index.get((candidate["repo_id"], candidate["candidate_id"]))
        if not known:
            continue
        status = status_from_known(known)
        first_gate = str(known.get("first_failing_gate") or known.get("review_first_failing_gate") or "")
        historical = historical_index.get((candidate["repo_id"], candidate["target_commit_optional"])) or historical_index.get((candidate["repo_id"], candidate["candidate_id"])) or {}
        subgate = attempt_subgate_label(known, status, historical)
        command_durations = [float(cmd.get("duration_seconds", 0)) for cmd in known.get("commands", []) if isinstance(cmd, dict) and cmd.get("duration_seconds") is not None]
        if command_durations:
            durations[candidate["repo_id"]].extend(command_durations)
        quality = classify_context_quality(candidate, context_for(candidate, contexts))
        summary[candidate["repo_id"]][status] += 1
        subgates[candidate["repo_id"]][subgate] += 1
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "repo_id": candidate["repo_id"],
                "source_arm": "repo_history_v2_real" if candidate["source_system"] == "repo_history_v2" else "repo_history_v1_baseline",
                "source_reservoir": candidate["source_reservoir"],
                "attempt_basis": "matched_committed_local_certification_artifact",
                "status": status,
                "first_failing_gate": first_gate,
                "subgate_label": subgate,
                "historical_environment_terminal_subgate": historical.get("terminal_subgate_label", ""),
                "historical_environment_recovered_reference_pass": bool(historical.get("recovered_reference_pass")),
                "source_context_quality": quality,
                "oracle_source": candidate["oracle"]["oracle_source"],
                "module_or_package": module_names(candidate),
                "time_bucket": time_bucket(candidate["task_time"]),
                "artifact_ref": known.get("_artifact_path", ""),
            }
        )
    repo_summaries = []
    for repo_id in TARGET_REPOS:
        status_counts = summary[repo_id]
        attempt_count = sum(status_counts.values())
        certified_count = status_counts.get("certified", 0)
        near_count = status_counts.get("near_certified", 0)
        median_seconds = median(durations[repo_id])
        repo_summaries.append(
            {
                "repo_id": repo_id,
                "attempt_count": attempt_count,
                "certified_count": certified_count,
                "near_certified_count": near_count,
                "first_failing_gate_counts": dict(sorted(subgates[repo_id].items())),
                "subgate_counts": dict(sorted(subgates[repo_id].items())),
                "median_seconds_per_attempt": median_seconds,
                "wall_clock_per_certified": round((sum(durations[repo_id]) / certified_count), 3) if certified_count and durations[repo_id] else None,
            }
        )
    return {
        "schema_version": f"{SCHEMA_VERSION}.certification_attempts.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "local_certification_bakeoff_completed",
        "basis": "matched v2 candidates against committed local certification artifacts; no paid ACUT or LLM calls were made",
        "local_certification_attempt_cap_per_repo": LOCAL_CERTIFICATION_ATTEMPT_CAP_PER_REPO,
        "summary_by_repo": repo_summaries,
        "rows": rows,
        "raw_logs_committed": False,
        "claims": ["local_certification_bakeoff_completed"],
    }


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return round(ordered[middle], 3)
    return round((ordered[middle - 1] + ordered[middle]) / 2, 3)


def time_bucket(value: str) -> str:
    year = 0
    try:
        year = int(str(value)[:4])
    except ValueError:
        return "unknown"
    if year < 2016:
        return "pre_2016"
    if year < 2020:
        return "2016_2019"
    if year < 2024:
        return "2020_2023"
    return "2024_plus"


def external_feasibility() -> dict[str, Any]:
    rows = [
        {
            "source": "SWE-Bench++",
            "source_reservoir": "external_swe_bench_plus_plus_feasibility",
            "license_availability": "paper_available; code_or_dataset_artifact_not_confirmed_in_this_local_run",
            "public_artifact_availability": "paper_only_confirmed",
            "schema_mapping": "conceptually maps to PR base/target/oracle fields",
            "repo_overlap_with_targets": "unknown",
            "environment_oracle_fields_available": "described in paper; not locally inspected",
            "status": "blocked_by_missing_artifacts",
            "future_adapter_feasibility": "feasible_only_as_design_reference",
            "source_urls": ["https://arxiv.org/abs/2512.17419"],
        },
        {
            "source": "SWE-smith",
            "source_reservoir": "external_swe_smith_feasibility",
            "license_availability": "MIT license",
            "public_artifact_availability": "GitHub code and HuggingFace datasets are public",
            "schema_mapping": "task instances are SWE-bench-like and include repository/version/environment hooks",
            "repo_overlap_with_targets": "target-specific support not confirmed for attrs/boltons/toolz/humanize",
            "environment_oracle_fields_available": "Docker/Ubuntu execution environments and break-one-test filtering",
            "status": "blocked_by_runtime_cost",
            "future_adapter_feasibility": "feasible_for_future_adapter",
            "source_urls": ["https://github.com/SWE-bench/SWE-smith", "https://www.swebench.com/SWE-bench/reference/versioning/"],
        },
        {
            "source": "SWE-bench-Live",
            "source_reservoir": "external_swe_bench_live_feasibility",
            "license_availability": "MIT license",
            "public_artifact_availability": "GitHub code and HuggingFace datasets are public",
            "schema_mapping": "issue resolving tasks can map to public issue context, repo version, and test oracle fields",
            "repo_overlap_with_targets": "not established for this target-repo set",
            "environment_oracle_fields_available": "RepoLaunch/containerized evaluation is available but outside this local adapter",
            "status": "feasible_only_as_design_reference",
            "future_adapter_feasibility": "feasible_for_future_adapter",
            "source_urls": ["https://github.com/microsoft/SWE-bench-Live"],
        },
        {
            "source": "R2E-Gym / R2E-style",
            "source_reservoir": "external_swe_bench_live_feasibility",
            "license_availability": "Apache-2.0 license",
            "public_artifact_availability": "GitHub code and HuggingFace datasets are public",
            "schema_mapping": "environment objects can inform future generated-environment adapters",
            "repo_overlap_with_targets": "not established for this target-repo set",
            "environment_oracle_fields_available": "procedural environments and hybrid verifiers, not trusted Barcarolle certification by default",
            "status": "feasible_only_as_design_reference",
            "future_adapter_feasibility": "feasible_for_future_adapter",
            "source_urls": ["https://github.com/R2E-Gym/R2E-Gym"],
        },
    ]
    return {
        "schema_version": f"{SCHEMA_VERSION}.external_feasibility.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "external_source_feasibility_completed",
        "external_tasks_counted_as_certified_default_supply": False,
        "rows": rows,
        "claims": ["external_source_feasibility_completed"],
    }


def source_mixing_policy() -> dict[str, Any]:
    return {
        "per_repo_certified_candidates_min_before_paid_validation": 30,
        "minimum_source_reservoirs_per_repo_when_feasible": 2,
        "max_single_source_reservoir_share_unless_waived": 0.70,
        "max_commit_message_only_share_unless_manually_reviewed": 0.20,
        "max_synthetic_or_generated_oracle_share_until_predictive_evidence": 0.25,
        "external_tasks_must_be_recertified_locally": True,
        "policy_status": "draft_for_future_release_candidates_not_release_freeze",
    }


def future_directions_payload(external: dict[str, Any]) -> dict[str, Any]:
    status_by_source = {row["source"]: row["status"] for row in external["rows"]}
    rows = [
        {
            "direction_id": "external_swe_bench_plus_plus_adapter",
            "status": "blocked",
            "why_not_now": "Only paper-level feasibility was confirmed; local public adapter artifacts were not inspected.",
            "evidence_from_this_run": status_by_source.get("SWE-Bench++", "not_checked"),
            "minimum_next_artifact": "licensed schema sample plus repository overlap table",
            "main_risk": "missing or non-recertifiable artifacts",
            "recommended_priority": "later",
        },
        {
            "direction_id": "external_swe_smith_adapter",
            "status": "feasible_spike_completed",
            "why_not_now": "Docker/Ubuntu runtime is outside this local macOS-centered bakeoff and generated tasks must stay separate from eval supply.",
            "evidence_from_this_run": status_by_source.get("SWE-smith", "not_checked"),
            "minimum_next_artifact": "one target-repo profile mapping and local Barcarolle recertification plan",
            "main_risk": "synthetic oracle distribution shift and container cost",
            "recommended_priority": "next",
        },
        {
            "direction_id": "external_swe_bench_live_adapter",
            "status": "feasible_spike_completed",
            "why_not_now": "Repo overlap and local recertification were not established.",
            "evidence_from_this_run": status_by_source.get("SWE-bench-Live", "not_checked"),
            "minimum_next_artifact": "monthly split sample mapped into TaskSourceCandidate v2",
            "main_risk": "freshness and contamination policy complexity",
            "recommended_priority": "next",
        },
        {
            "direction_id": "generated_oracle_pipeline",
            "status": "deferred",
            "why_not_now": "This run separated missing-oracle issue/PR candidates from changed-test supply and did not promote generated oracle tasks.",
            "evidence_from_this_run": "repo_history_v2_issue_without_changed_tests candidates were inventoried as missing-oracle supply.",
            "minimum_next_artifact": "separate generated-oracle feasibility report with no eval-pool promotion",
            "main_risk": "synthetic tests leaking target behavior or changing predictive value",
            "recommended_priority": "later",
        },
        {
            "direction_id": "endpoint_statement_generator_reviewer",
            "status": "deferred",
            "why_not_now": "Paid LLM statement generation was disabled by this runbook.",
            "evidence_from_this_run": "commit-message-only and weak public context counts show where generation/review would be useful later.",
            "minimum_next_artifact": "endpoint-compliant wrapper proving LLM_BASE_URL and LLM_API_KEY usage",
            "main_risk": "raw prompt/completion leakage and endpoint-policy violations",
            "recommended_priority": "next",
        },
        {
            "direction_id": "docker_or_nix_environment_factory",
            "status": "deferred",
            "why_not_now": "Historical uv profiles were integrated first; full image factory was outside the local cap.",
            "evidence_from_this_run": "environment profile matrix records bounded uv profile shapes.",
            "minimum_next_artifact": "one repo-specific container profile with sanitized logs",
            "main_risk": "runtime cost and hard-to-audit environment drift",
            "recommended_priority": "later",
        },
        {
            "direction_id": "manual_or_customer_regression_source",
            "status": "deferred",
            "why_not_now": "No manual/customer source was provided in this run.",
            "evidence_from_this_run": "schema includes manual_or_customer_future_direction reservoir.",
            "minimum_next_artifact": "one sanitized candidate packet and provenance checklist",
            "main_risk": "license/provenance ambiguity",
            "recommended_priority": "park",
        },
        {
            "direction_id": "multi_language_supply",
            "status": "deferred",
            "why_not_now": "The target repos and local certification path were Python-only.",
            "evidence_from_this_run": "external systems show multi-language options, but local Barcarolle adapters were not built.",
            "minimum_next_artifact": "language-specific candidate schema extension and one local verifier profile",
            "main_risk": "environment fragmentation",
            "recommended_priority": "later",
        },
    ]
    return {
        "schema_version": f"{SCHEMA_VERSION}.future_directions.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "task_supply_future_directions_recorded",
        "rows": rows,
        "claims": ["task_supply_future_directions_recorded"],
    }


def paid_readiness_gate(certification: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    historical = read_json("experiments/phase1_compiler/results/phase1_historical_environment_synthesis_decision.json", default={}) or {}
    prior_counts = {row["repo_id"]: row.get("eligible_count_from_prior_decision") or row.get("certified_rows") for row in current["rows"]}
    projected = dict(prior_counts)
    if "attrs" in projected:
        projected["attrs"] = int(projected.get("attrs") or 0) + int(historical.get("confirmed_recovered_eligible_attrs") or 0)
    if "boltons" in projected:
        projected["boltons"] = int(projected.get("boltons") or 0) + int(historical.get("confirmed_recovered_eligible_boltons") or 0)
    repos_meeting_30 = sorted(repo for repo, count in projected.items() if int(count or 0) >= 30)
    ready = len(repos_meeting_30) >= 3
    return {
        "schema_version": f"{SCHEMA_VERSION}.paid_readiness_gate.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "paid_readiness_gate_completed",
        "paid_ready": ready,
        "reason": "requires at least 3 repos with >=30 certified candidates; local evidence currently meets this for fewer than 3 repos",
        "projected_certified_or_confirmed_eligible_by_repo": projected,
        "repos_meeting_30": repos_meeting_30,
        "minimum_gate": {
            "at_least_3_repos_with_30_certified": ready,
            "subgate_labels_present_for_failures": bool(certification.get("rows")),
            "raw_logs_workspaces_not_committed": True,
            "no_unreviewed_material_leakage_risk": False,
            "source_reservoir_mix_policy_drafted": True,
        },
        "missing": [
            "at least three repos with >=30 locally certified candidates",
            "fresh repo_history_v2 certification attempts for the broad mined pool",
            "manual or endpoint-compliant review of weak/commit-message-only statements",
        ],
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "claims": ["paid_readiness_gate_completed", "no_paid_acut_calls_made", "no_paid_llm_statement_generation_made"],
    }


def source_bakeoff_decision(
    current: dict[str, Any],
    raw_inventory: dict[str, Any],
    source_context: dict[str, Any],
    oracle: dict[str, Any],
    certification: dict[str, Any],
    external: dict[str, Any],
    paid_gate: dict[str, Any],
    future: dict[str, Any],
) -> dict[str, Any]:
    certified_by_repo = {row["repo_id"]: row["certified_count"] for row in certification["summary_by_repo"]}
    best_arm = {}
    for repo_id in TARGET_REPOS:
        v2_count = raw_inventory["summary_by_repo"].get(repo_id, {}).get("raw_v2_candidate_count", 0)
        if v2_count:
            best_arm[repo_id] = "repo_history_v2_real_for_candidate_discovery"
        else:
            best_arm[repo_id] = "repo_history_v1_baseline_only"
    dominant_failures = {
        "source_context": "commit-message-only remains common, especially where no linked issue/PR context was found",
        "oracle": "issue/PR candidates without changed tests are missing-oracle inventory only",
        "environment": "historical subgates improve diagnosis but do not yet lift three repos over the paid gate",
    }
    research_questions = {
        "RQ1": "Yes. Current v1 artifacts reproduce the bottleneck: attrs/toolz/humanize remain below 30, boltons reaches 31 only after adding confirmed historical-environment recoveries.",
        "RQ2": "Yes for raw candidate yield and source-reservoir visibility; not yet proven for certified yield because broad v2 candidates still need bounded certification execution.",
        "RQ3": "Dominant modes are source context quality, missing oracle for issue-only candidates, and environment/reference subgates.",
        "RQ4": f"Repos projected at >=30: {paid_gate['repos_meeting_30']}. The three-repo paid gate is not met.",
        "RQ5": "SWE-smith, SWE-bench-Live, and R2E-style systems are feasible design references or future adapters; none is adopted or counted as default certified supply.",
        "RQ6": "Paid validation, paid statement generation, benchmark release freeze, generated-oracle promotion, broad multi-language implementation, and ACUT harness work were not implemented and are tracked in the future-direction ledger.",
        "RQ7": "Continue internal repo-history v2 on selected repos, then run a bounded certification pass; use external-source adapters only as later spikes.",
    }
    return {
        "schema_version": f"{SCHEMA_VERSION}.source_bakeoff_decision.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "source_bakeoff_decision_completed",
        "primary_decision_label": "continue_internal_repo_history_v2",
        "plain_language_summary": "Broad local mining found more candidate anchors, but certified supply is still not paid-ready. The next useful move is to certify the v2 pool and repair weak source-context/oracle paths.",
        "repos_screened": TARGET_REPOS,
        "source_arms_compared": [
            "repo_history_v1_baseline",
            "repo_history_v2_real",
            "repo_history_v2_oracle_inventory",
            "external_source_feasibility",
            "hybrid_pool_diagnostic",
        ],
        "certified_count_by_repo_and_arm": certified_by_repo,
        "best_source_arm_by_repo": best_arm,
        "dominant_failure_modes": dominant_failures,
        "external_source_feasibility_summary": {row["source"]: row["status"] for row in external["rows"]},
        "future_directions_summary": {row["direction_id"]: row["status"] for row in future["rows"]},
        "paid_readiness_status": paid_gate["status"],
        "paid_ready": paid_gate["paid_ready"],
        "recommended_next_action_category": "continue_internal_generator_v2_on_selected_repos",
        "source_mixing_policy": source_mixing_policy(),
        "research_questions": research_questions,
        "verification": {},
        "claims": [
            "source_mixing_policy_drafted",
            "task_supply_future_directions_recorded",
            "paid_readiness_gate_completed",
            "no_paid_acut_calls_made",
            "no_paid_llm_statement_generation_made",
        ],
        "disallowed_claims_made": [],
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |")
    return "\n".join(lines)


def write_process_report(preflight: dict[str, Any]) -> None:
    rows = [
        ["0", "Preflight and ledger", "completed"],
        ["1", "TaskSourceCandidate v2 schema", "completed"],
        ["2", "Current supply baseline", "completed"],
        ["3", "Repo inventory", "completed"],
        ["4", "Broad repo-history v2 mining", "completed"],
        ["5", "Source context inventory", "completed"],
        ["6", "Environment profile and subgate integration", "completed"],
        ["7", "Oracle extraction inventory", "completed"],
        ["8", "Local certification bakeoff", "completed from committed local certification artifacts"],
        ["9", "External source feasibility", "completed as public metadata/design check"],
        ["10", "Source mixing policy", "drafted"],
        ["11", "Future direction ledger", "completed"],
        ["12", "Paid readiness gate", "completed"],
        ["13", "Decision and closeout", "completed"],
    ]
    text = f"""# Phase 1 Task Supply v2 Process

Generated at: {preflight['generated_at']}

This is a supply-layer bakeoff. It is not a benchmark validation run. It does not run paid ACUT cells, paid task-solving, paid replication, or paid LLM statement generation.

{markdown_table(['Step', 'Name', 'Status'], rows)}

Boundary checks:

- paid ACUT calls: disabled
- paid LLM calls: disabled
- raw artifacts committed: false
- hidden oracle material used: false
- raw ACUT transcripts used: false
"""
    write_text(report_path("process"), text)


def write_schema_report(schema_payload: dict[str, Any]) -> None:
    fields = [[field, "required"] for field in REQUIRED_CANDIDATE_FIELDS]
    text = f"""# TaskSourceCandidate v2 Schema

TaskSourceCandidate v2 is the normalized row shape for supply candidates. It keeps source provenance, public context, oracle status, environment profile, leakage flags, and solver-exposure policy in one JSON-serializable object.

{markdown_table(['Field', 'Status'], fields)}

The validator enforces required ids, base commits, allowed source reservoirs, oracle shape, environment shape, `gold_patch_exposed_to_solver == false`, and raw artifact paths under ignored scratch prefixes.

Allowed source reservoirs:

{chr(10).join(f'- {name}' for name in sorted(ALLOWED_SOURCE_RESERVOIRS))}
"""
    write_text(report_path("schema"), text)
    del schema_payload


def write_current_supply_report(payload: dict[str, Any]) -> None:
    rows = [
        [
            row["repo_id"],
            row["raw_candidate_rows"],
            row["source_context_rows"],
            row["certified_rows"],
            row["near_certified_rows"],
            row["eligible_count_from_prior_decision"],
            row["commit_message_only_count"],
            row["public_pr_or_issue_context_count"],
        ]
        for row in payload["rows"]
    ]
    text = f"""# Current Supply Reproduction

This baseline uses committed local artifacts only. It reproduces what the current repo-history v1 path already showed; it does not prove that toolz or humanize lack supply.

{markdown_table(['Repo', 'Raw Rows', 'Context Rows', 'Certified Rows', 'Near Rows', 'Prior Eligible', 'Commit-Only Context', 'Issue/PR Context'], rows)}

The old toolz/humanize 16-candidate screens are narrow artifacts, not broad repository conclusions.
"""
    write_text(report_path("current_supply_reproduction"), text)


def write_repo_inventory_report(payload: dict[str, Any]) -> None:
    rows = [
        [
            row["repo_id"],
            row.get("commit_count_since_2010_or_cap", 0),
            row.get("commit_count_with_implementation_changes", 0),
            row.get("commit_count_with_test_changes", 0),
            row.get("commit_count_with_both_implementation_and_test_changes", 0),
            row.get("visible_issue_or_pr_linkability_signal", {}).get("commit_subject_refs", 0),
            row.get("worth_broad_mining_first", False),
        ]
        for row in payload["rows"]
    ]
    text = f"""# Repo Inventory

The inventory checks whether the local target repositories have enough history to justify broader mining.

{markdown_table(['Repo', 'Commits', 'Impl', 'Tests', 'Impl+Tests', 'Subject Refs', 'Worth Broad Mining'], rows)}
"""
    write_text(report_path("repo_inventory"), text)


def write_raw_anchor_report(payload: dict[str, Any]) -> None:
    rows = [
        [
            repo_id,
            summary.get("raw_v2_candidate_count", 0),
            summary.get("reservoir_counts", {}),
            summary.get("cap_hit", False),
        ]
        for repo_id, summary in payload["summary_by_repo"].items()
    ]
    text = f"""# Raw Anchor Inventory

Repo-history v2 separates candidate discovery from oracle usability. A candidate with no changed tests is useful inventory, but it is not certified eval supply.

{markdown_table(['Repo', 'V2 Candidates', 'Reservoir Mix', 'Cap Hit'], rows)}
"""
    write_text(report_path("raw_anchor_inventory"), text)


def write_source_context_report(payload: dict[str, Any]) -> None:
    rows = [[repo, counts] for repo, counts in payload["counts_by_repo"].items()]
    text = f"""# Source Context Inventory

The source-context pass counts issue/PR-like context separately from commit-message-only context. Commit-message-only candidates do not silently count as high-quality issue supply.

{markdown_table(['Repo', 'Context Quality Counts'], rows)}
"""
    write_text(report_path("source_context_inventory"), text)


def write_environment_report(payload: dict[str, Any]) -> None:
    text = f"""# Environment Profile Matrix

The environment matrix records bounded uv profile shapes and normalized subgate labels. Raw stdout and stderr stay under ignored scratch paths.

Profile counts:

{json.dumps(payload['profile_counts'], indent=2, sort_keys=True)}

Subgate labels:

{', '.join(payload['subgate_labels'])}
"""
    write_text(report_path("environment_profile_matrix"), text)


def write_oracle_report(payload: dict[str, Any]) -> None:
    text = f"""# Oracle Extraction Matrix

Changed-test candidates and missing-oracle candidates are separated. Generated oracle tasks were not promoted to eval supply.

Oracle classification counts:

{json.dumps(payload['oracle_classification_counts'], indent=2, sort_keys=True)}
"""
    write_text(report_path("oracle_extraction_matrix"), text)


def write_certification_report(payload: dict[str, Any]) -> None:
    rows = [
        [
            row["repo_id"],
            row["attempt_count"],
            row["certified_count"],
            row["near_certified_count"],
            row["subgate_counts"],
            row["median_seconds_per_attempt"],
        ]
        for row in payload["summary_by_repo"]
    ]
    text = f"""# Certification Attempts

This bakeoff matched v2 candidates to committed local certification artifacts. It did not make paid calls and did not commit raw logs. The result is enough to identify supply gaps, but not enough to claim broad v2 certified yield.

{markdown_table(['Repo', 'Attempts', 'Certified', 'Near', 'Subgates', 'Median Seconds'], rows)}
"""
    write_text(report_path("certification_attempts"), text)


def write_external_report(payload: dict[str, Any]) -> None:
    rows = [[row["source"], row["status"], row["future_adapter_feasibility"], ", ".join(row["source_urls"])] for row in payload["rows"]]
    text = f"""# External Source Feasibility

External systems were inspected as untrusted future inputs. None is adopted as a default Barcarolle generator and none counts as certified supply in this run.

{markdown_table(['Source', 'Status', 'Future Feasibility', 'Sources'], rows)}
"""
    write_text(report_path("external_feasibility"), text)


def write_future_report(payload: dict[str, Any]) -> None:
    rows = [[row["direction_id"], row["status"], row["recommended_priority"], row["minimum_next_artifact"]] for row in payload["rows"]]
    text = f"""# Future Direction Ledger

Deferred work is recorded explicitly so that not implementing it in this run is not mistaken for permanently rejecting it.

{markdown_table(['Direction', 'Status', 'Priority', 'Minimum Next Artifact'], rows)}
"""
    write_text(report_path("future_directions"), text)


def write_paid_gate_report(payload: dict[str, Any]) -> None:
    text = f"""# Paid Readiness Gate

Paid readiness status: {'ready' if payload['paid_ready'] else 'not ready'}.

Reason: {payload['reason']}

Projected certified or confirmed eligible counts:

{json.dumps(payload['projected_certified_or_confirmed_eligible_by_repo'], indent=2, sort_keys=True)}

Missing:

{chr(10).join(f'- {item}' for item in payload['missing'])}
"""
    write_text(report_path("paid_readiness_gate"), text)


def write_decision_report(payload: dict[str, Any]) -> None:
    rq_rows = [[key, value] for key, value in payload["research_questions"].items()]
    text = f"""# Source Bakeoff Decision

Primary decision: {payload['primary_decision_label']}

{payload['plain_language_summary']}

Recommended next action: {payload['recommended_next_action_category']}

{markdown_table(['Research Question', 'Answer'], rq_rows)}

Source mixing policy:

{json.dumps(payload['source_mixing_policy'], indent=2, sort_keys=True)}
"""
    write_text(report_path("source_bakeoff_decision"), text)


def run_all() -> dict[str, Any]:
    config = build_config()
    write_simple_yaml(output_path("config"), config)
    preflight = preflight_payload(config)
    write_json(output_path("preflight"), preflight)
    write_process_report(preflight)

    schema_payload = {
        "schema_version": f"{SCHEMA_VERSION}.schema_bundle.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "task_source_candidate_schema_defined",
        "candidate_schema": candidate_schema(),
        "bakeoff_result_schema": bakeoff_result_schema(),
        "allowed_source_reservoirs": sorted(ALLOWED_SOURCE_RESERVOIRS),
        "claims": ["task_source_candidate_schema_defined"],
    }
    write_json(output_path("schema"), schema_payload)
    write_json(SCHEMA_OUTPUTS["candidate"], candidate_schema())
    write_json(SCHEMA_OUTPUTS["bakeoff_result"], bakeoff_result_schema())
    write_schema_report(schema_payload)

    current = current_supply_reproduction()
    write_json(output_path("current_supply_reproduction"), current)
    write_current_supply_report(current)

    repo_inv = repo_inventory()
    write_json(output_path("repo_inventory"), repo_inv)
    write_repo_inventory_report(repo_inv)

    contexts = source_context_rows()
    candidates, mining_summary = broad_mining_candidates(contexts)
    raw_inventory = raw_anchor_inventory(candidates, mining_summary)
    write_json(output_path("raw_anchor_inventory"), raw_inventory)
    write_raw_anchor_report(raw_inventory)

    source_context = source_context_inventory(candidates, contexts)
    write_json(output_path("source_context_inventory"), source_context)
    write_source_context_report(source_context)

    environment = environment_profile_matrix(candidates)
    write_json(output_path("environment_profile_matrix"), environment)
    write_environment_report(environment)

    oracle = oracle_extraction_matrix(candidates)
    write_json(output_path("oracle_extraction_matrix"), oracle)
    write_oracle_report(oracle)

    cert = certification_attempts(candidates, contexts)
    write_json(output_path("certification_attempts"), cert)
    write_certification_report(cert)

    external = external_feasibility()
    write_json(output_path("external_feasibility"), external)
    write_external_report(external)

    future = future_directions_payload(external)
    write_json(output_path("future_directions"), future)
    write_future_report(future)

    paid_gate = paid_readiness_gate(cert, current)
    write_json(output_path("paid_readiness_gate"), paid_gate)
    write_paid_gate_report(paid_gate)

    decision = source_bakeoff_decision(current, raw_inventory, source_context, oracle, cert, external, paid_gate, future)
    write_json(output_path("source_bakeoff_decision"), decision)
    write_decision_report(decision)
    return decision


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 1 Task Supply v2 generator bakeoff.")
    parser.add_argument("--run", choices=["all"], default="all")
    args = parser.parse_args()
    if args.run == "all":
        decision = run_all()
        print(json.dumps({"status": decision["status"], "primary_decision_label": decision["primary_decision_label"]}, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
