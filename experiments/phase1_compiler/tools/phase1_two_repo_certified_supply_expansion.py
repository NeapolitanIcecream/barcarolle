from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shlex
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
from phase1_future_holdout import parse_task_time  # noqa: E402


RUN_ID = "phase1_two_repo_supply_expansion_20260526"
SCHEMA_VERSION = "barcarolle.phase1_two_repo_certified_supply_expansion.v1"
RUNBOOK = "docs/experiments/phase-1-two-repo-certified-supply-expansion-runbook.md"
RUNBOOK_DATE = "2026-05-26"
TARGET_REPOS = ["attrs", "boltons"]
NAMESPACE = "supply_expansion_20260526"
MINIMUM_TARGET_PER_REPO = 30
STRETCH_TARGET_PER_REPO = 50
RAW_CANDIDATE_FLOOR_PER_REPO = 50
RAW_CANDIDATE_SOFT_CAP_PER_REPO = 160
LOCAL_CERTIFICATION_ATTEMPT_SOFT_CAP_PER_REPO = 96
EXISTING_BAKEOFF_ELIGIBLE_COUNTS = {"attrs": 10, "boltons": 12}

REPO_CONFIGS = {
    "attrs": {
        "repo_url": "https://github.com/python-attrs/attrs.git",
        "local_repo": "experiments/phase0_headroom/external_repos/attrs",
        "command_template": (
            "uv run --project experiments/phase0_headroom "
            "--with \"pytest>=7,<8\" --with \"setuptools<81\" --with \"hypothesis<6\" "
            "python -m pytest -q {test_files}"
        ),
    },
    "boltons": {
        "repo_url": "https://github.com/mahmoud/boltons.git",
        "local_repo": "experiments/phase0_headroom/external_repos/boltons",
        "command_template": (
            "uv run --project experiments/phase0_headroom "
            "--with \"pytest>=8,<9\" --with \"setuptools<81\" "
            "python -m pytest -q {test_files}"
        ),
    },
}

OUTPUTS = {
    "config": "experiments/phase1_compiler/configs/phase1_two_repo_certified_supply_expansion.yaml",
    "preflight": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_preflight.json",
    "existing_inventory": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_existing_inventory.json",
    "duplicate_and_leakage_index": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_duplicate_and_leakage_index.json",
    "mining_plan": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_mining_plan.json",
    "raw_candidates": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_raw_candidates.json",
    "source_contexts": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_source_contexts.json",
    "certification_attempts": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_certification_attempts.json",
    "statement_packets": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_statement_packets.json",
    "statement_generation_review": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_statement_generation_review.json",
    "eligibility_audit": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_eligibility_audit.json",
    "expanded_supply": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_expanded_supply.json",
    "split_support": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_split_support.json",
    "local_bakeoff_rerun": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_local_bakeoff_rerun.json",
    "contingency_screen": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_contingency_screen.json",
    "decision": "experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_decision.json",
}

REPORTS = {
    "process": "experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_process.md",
    "existing_inventory": "experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_existing_inventory.md",
    "mining_plan": "experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_mining_plan.md",
    "raw_candidates": "experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_raw_candidates.md",
    "source_contexts": "experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_source_contexts.md",
    "certification_attempts": "experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_certification_attempts.md",
    "statement_packets": "experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_statement_generation_review.md",
    "eligibility_audit": "experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_eligibility_audit.md",
    "expanded_supply": "experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_expanded_supply.md",
    "split_support": "experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_split_support.md",
    "local_bakeoff_rerun": "experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_local_bakeoff_rerun.md",
    "contingency_screen": "experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_contingency_screen.md",
    "decision": "experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_decision.md",
}

REQUIRED_INPUTS = [
    "AGENTS.md",
    "docs/architecture/system-design.md",
    "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_decision.json",
    "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_paid_readiness_gate.json",
    "experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_task_audit.json",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_candidate_inventory.json",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_release_candidates.json",
    "experiments/phase1_compiler/results/phase1_pre_paid_replication_target_profiles.json",
    "experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_score_table.csv",
    "experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py",
    "experiments/phase1_compiler/tools/phase1_diff_assisted_codex_loop_statement_regeneration.py",
    "experiments/phase1_compiler/tools/phase1_local_algorithm_bakeoff.py",
    "experiments/phase1_compiler/tools/phase1_pre_paid_replication_compiler_readiness.py",
    "experiments/phase0_headroom/tools/repo_history_pilot.py",
    "experiments/phase0_headroom/tools/statement_quality.py",
    "experiments/phase0_headroom/external_repos/attrs",
    "experiments/phase0_headroom/external_repos/boltons",
]

REQUIRED_CERTIFICATION_GATES = [
    "checkout",
    "oracle_extractable",
    "no_op_fail",
    "reference_pass",
    "known_bad_fail",
    "flakiness_check",
    "scope_clarity_review",
    "cost_boundedness",
    "taxonomy_labelability",
    "solution_leakage_review",
    "statement_quality_review",
]

DISALLOWED_CLAIMS = [
    "predictive_validity_established",
    "paid_replication_completed",
    "new_paid_acut_cells_run",
    "H_future_used_as_target_profile",
    "hidden_oracle_informed_selection",
    "raw_transcript_informed_selection",
    "local_subscription_llm_used_under_endpoint_rule",
    "post_hoc_algorithm_claimed_as_preregistered_paid_design",
    "followup_runbook_written_by_worker",
]

PROCESS_STEPS = [
    (0, "Preflight And Execution Ledger", "preflight"),
    (1, "Existing Supply Inventory", "existing_inventory"),
    (2, "Mining Plan And Stop Rules", "mining_plan"),
    (3, "Mine Raw Historical Candidates", "raw_candidates"),
    (4, "Enrich Public Source Context", "source_contexts"),
    (5, "Local Certification Replay", "certification_attempts"),
    (6, "Prepare Statement Generation Packets", "statement_packets"),
    (7, "Optional Endpoint Statement Generation And Review Loop", "statement_generation_review"),
    (8, "Eligibility Audit And Expanded Supply Freeze", "expanded_supply"),
    (9, "Split Support And Target-Profile Diagnostics", "split_support"),
    (10, "Local Bakeoff Rerun On Expanded Supply", "local_bakeoff_rerun"),
    (11, "New Repository Contingency Screen", "contingency_screen"),
    (12, "Final Decision And Closeout", "decision"),
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def path_from_repo(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def rel(path: str | Path) -> str:
    resolved = path_from_repo(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def output_path(key: str) -> Path:
    return path_from_repo(OUTPUTS[key])


def report_path(key: str) -> Path:
    return path_from_repo(REPORTS[key])


def phase0_candidate_path(repo_id: str, suffix: str) -> Path:
    return PHASE0_ROOT / "candidate_sources" / f"{repo_id}_{NAMESPACE}_{suffix}.jsonl"


def phase0_certified_path(repo_id: str, suffix: str) -> Path:
    return PHASE0_ROOT / "certified_tasks" / f"{repo_id}_{NAMESPACE}_{suffix}.jsonl"


def read_json(path: str | Path, default: Any = None) -> Any:
    resolved = path_from_repo(path)
    if not resolved.exists():
        return default
    return json.loads(resolved.read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    resolved = path_from_repo(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    resolved = path_from_repo(path)
    if not resolved.exists():
        return []
    return [json.loads(line) for line in resolved.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    resolved = path_from_repo(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def read_csv(path: str | Path) -> list[dict[str, str]]:
    resolved = path_from_repo(path)
    if not resolved.exists():
        return []
    with resolved.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_text(path: str | Path, text: str) -> None:
    resolved = path_from_repo(path)
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


def digest_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def short_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def command_result(args: list[str], cwd: Path = REPO_ROOT, timeout: int = 120) -> dict[str, Any]:
    started = time.monotonic()
    try:
        proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {
            "args": args,
            "returncode": 124 if isinstance(exc, subprocess.TimeoutExpired) else 127,
            "stdout": getattr(exc, "stdout", "") or "",
            "stderr": str(exc),
            "duration_seconds": round(time.monotonic() - started, 3),
        }
    return {
        "args": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "duration_seconds": round(time.monotonic() - started, 3),
    }


def command_stdout(args: list[str], cwd: Path = REPO_ROOT, timeout: int = 120) -> str:
    result = command_result(args, cwd, timeout)
    return result["stdout"] if result["returncode"] == 0 else result["stderr"]


def git_lines(repo: Path, args: list[str], timeout: int = 120) -> list[str]:
    result = command_result(["git", *args], repo, timeout=timeout)
    if result["returncode"] != 0:
        raise RuntimeError(result["stderr"])
    return result["stdout"].splitlines()


def repo_path(repo_id: str) -> Path:
    return path_from_repo(REPO_CONFIGS[repo_id]["local_repo"])


def pilot_config(repo_id: str) -> repo_history_pilot.PilotConfig:
    config = REPO_CONFIGS[repo_id]
    return repo_history_pilot.PilotConfig(
        repo_id=repo_id,
        repo_url=str(config["repo_url"]),
        local_repo=path_from_repo(str(config["local_repo"])),
        command_template=str(config["command_template"]),
        certification_attempts=LOCAL_CERTIFICATION_ATTEMPT_SOFT_CAP_PER_REPO,
        pilot_certified_min=MINIMUM_TARGET_PER_REPO,
        benchmark_grade_min=STRETCH_TARGET_PER_REPO,
        result_prefix=f"{repo_id}_{NAMESPACE}",
        claim_scope="two_repo_supply_expansion_local_only",
    )


def unique_preserve(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def repo_from_task_id(task_id: str) -> str:
    return task_id.split("__", 1)[0] if "__" in task_id else "unknown"


def is_target_repo_row(row: dict[str, Any]) -> bool:
    repo_id = str(row.get("repo_id") or repo_from_task_id(str(row.get("task_id", ""))))
    return repo_id in TARGET_REPOS


def task_id_from_row(row: dict[str, Any]) -> str:
    return str(row.get("task_id") or row.get("original_task_id") or "")


def implementation_files(row: dict[str, Any]) -> list[str]:
    changed = [str(path) for path in row.get("changed_files", [])]
    explicit = [str(path) for path in row.get("code_files", []) or row.get("implementation_files", [])]
    return sorted(set(explicit or statement_quality.implementation_files(changed)))


def test_files(row: dict[str, Any]) -> list[str]:
    changed = [str(path) for path in row.get("changed_files", [])]
    explicit = [str(path) for path in row.get("test_files", [])]
    return sorted(set(explicit or statement_quality.test_files(changed)))


def module_or_package(row: dict[str, Any]) -> list[str]:
    modules = row.get("module_or_package")
    if isinstance(modules, str):
        return [modules] if modules else []
    if isinstance(modules, list):
        return [str(item) for item in modules if item]
    return repo_history_pilot.module_names(implementation_files(row))


def source_kind_from_ref(ref: str) -> str:
    return statement_quality.source_kind(ref)


def first_failing_gate(gates: dict[str, str]) -> str:
    for gate in REQUIRED_CERTIFICATION_GATES:
        if gates.get(gate) != "pass":
            return gate
    return ""


def all_required_gates_pass(gates: dict[str, str]) -> bool:
    return not first_failing_gate(gates)


def stable_candidate_id(repo_id: str, index: int) -> str:
    return f"{repo_id}__{NAMESPACE}__{index:03d}"


def load_task_commit_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for path in list((PHASE0_ROOT / "candidate_sources").glob("*.jsonl")) + list((PHASE0_ROOT / "certified_tasks").glob("*.jsonl")):
        for row in read_jsonl(path):
            task_id = task_id_from_row(row)
            target = str(row.get("target_commit") or "")
            if task_id and target:
                index[task_id] = target
            original = str(row.get("original_task_id") or "")
            if original and target:
                index[original] = target
    return index


def load_seen_indexes() -> dict[str, Any]:
    task_commit_index = load_task_commit_index()
    seen_task_ids: set[str] = set()
    seen_target_commits: set[str] = set()
    score_tables: list[str] = []
    for score_table in sorted((PHASE0_ROOT / "results").glob("*score_table.csv")) + sorted((ROOT / "results").glob("*score_table.csv")):
        rows = read_csv(score_table)
        if not rows:
            continue
        score_tables.append(rel(score_table))
        for row in rows:
            task_id = str(row.get("task_id") or "")
            target_commit = str(row.get("target_commit") or "")
            if task_id:
                seen_task_ids.add(task_id)
            if target_commit:
                seen_target_commits.add(target_commit)
            elif task_id and task_id in task_commit_index:
                seen_target_commits.add(task_commit_index[task_id])
    scorecard = read_json(ROOT / "results" / "phase1_workspace_scorecard.json", default={}) or {}
    for cell in scorecard.get("cells", []):
        task_id = str(cell.get("task_id") or "")
        if task_id:
            seen_task_ids.add(task_id)
            if task_id in task_commit_index:
                seen_target_commits.add(task_commit_index[task_id])
    return {
        "seen_task_ids": sorted(seen_task_ids),
        "seen_target_commits": sorted(seen_target_commits),
        "paid_outcome_seen_task_ids": sorted(seen_task_ids),
        "paid_outcome_seen_target_commits": sorted(seen_target_commits),
        "score_tables_scanned": score_tables,
        "task_commit_index_count": len(task_commit_index),
        "hidden_oracle_sensitive_artifacts_excluded": True,
        "raw_transcripts_excluded": True,
        "raw_prompts_and_completions_excluded": True,
    }


def existing_target_commits() -> set[str]:
    return set(load_task_commit_index().values())


def load_pre_paid_inventory_rows() -> dict[str, dict[str, Any]]:
    payload = read_json(ROOT / "results" / "phase1_pre_paid_replication_candidate_inventory.json", default={}) or {}
    return {str(row.get("task_id")): row for row in payload.get("rows", []) if row.get("task_id")}


def load_bakeoff_task_rows() -> dict[str, dict[str, Any]]:
    payload = read_json(ROOT / "results" / "phase1_local_algorithm_bakeoff_task_audit.json", default={}) or {}
    return {str(row.get("task_id")): row for row in payload.get("rows", []) if row.get("task_id")}


def load_release_split_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for release in sorted((PHASE0_ROOT / "releases").glob("*.json")):
        payload = read_json(release, default={}) or {}
        for split, task_ids in (payload.get("splits") or {}).items():
            for task_id in task_ids or []:
                index[str(task_id)] = str(split)
        for row in payload.get("tasks", []) or []:
            task_id = str(row.get("task_id") or "")
            if task_id and row.get("split"):
                index[task_id] = str(row["split"])
    return index


def build_config() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "runbook": RUNBOOK,
        "runbook_date": RUNBOOK_DATE,
        "status": "configured",
        "target_repos": TARGET_REPOS,
        "namespace": NAMESPACE,
        "minimum_target_per_repo": MINIMUM_TARGET_PER_REPO,
        "stretch_target_per_repo": STRETCH_TARGET_PER_REPO,
        "starting_supply_counts": EXISTING_BAKEOFF_ELIGIBLE_COUNTS,
        "mining": {
            "raw_candidate_floor_per_repo": RAW_CANDIDATE_FLOOR_PER_REPO,
            "raw_candidate_soft_cap_per_repo": RAW_CANDIDATE_SOFT_CAP_PER_REPO,
            "local_certification_attempt_soft_cap_per_repo": LOCAL_CERTIFICATION_ATTEMPT_SOFT_CAP_PER_REPO,
            "scan_since": "2010-01-01",
            "prefer_broad_chronological_coverage": True,
        },
        "repos": REPO_CONFIGS,
        "guardrails": {
            "paid_acut_calls": "disabled",
            "paid_task_solving_calls": "disabled",
            "paid_replication": "disabled",
            "paid_llm_statement_generation": "later_gated_by_LLM_BASE_URL_and_LLM_API_KEY",
            "hidden_oracle_material_used_for_selection": False,
            "raw_acut_transcripts_used_for_selection": False,
            "mutate_canonical_historical_files": False,
            "write_followup_runbook": False,
        },
        "outputs": OUTPUTS,
        "reports": REPORTS,
    }


def preflight() -> dict[str, Any]:
    config = build_config()
    write_simple_yaml(OUTPUTS["config"], config)
    branch = command_stdout(["git", "branch", "--show-current"])
    head = command_stdout(["git", "rev-parse", "HEAD"])
    git_status = command_stdout(["git", "status", "--short"])
    python_version = sys.version.split()[0]
    uv_version = command_stdout(["uv", "--version"])
    decision = read_json(ROOT / "results" / "phase1_local_algorithm_bakeoff_decision.json", default={}) or {}
    gate = read_json(ROOT / "results" / "phase1_local_algorithm_bakeoff_paid_readiness_gate.json", default={}) or {}
    required = [
        {"path": path, "present": path_from_repo(path).exists(), "kind": "directory" if path_from_repo(path).is_dir() else "file"}
        for path in REQUIRED_INPUTS
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "status": "preflight_completed",
        "runbook": RUNBOOK,
        "branch": branch,
        "head": head,
        "python_version": python_version,
        "uv_version": uv_version,
        "git_status_short": git_status.splitlines(),
        "working_tree_already_contains_unrelated_changes": bool(git_status.strip()),
        "required_inputs": required,
        "missing_required_inputs": [row["path"] for row in required if not row["present"]],
        "latest_local_bakeoff_decision": {
            "final_decision": decision.get("final_decision"),
            "mainline_recommendation": decision.get("mainline_recommendation"),
            "smallest_local_blocker": decision.get("smallest_local_blocker"),
        },
        "latest_paid_readiness_gate": {
            "status": gate.get("status"),
            "eligible_supply_by_repo": gate.get("eligible_supply_by_repo"),
            "gates": gate.get("gates"),
            "candidate_algorithm_if_ready": gate.get("candidate_algorithm_if_ready"),
        },
        "starting_supply_counts_match_runbook": gate.get("eligible_supply_by_repo") == EXISTING_BAKEOFF_ELIGIBLE_COUNTS,
        "paid_acut_calls": "disabled",
        "paid_task_solving_calls": "disabled",
        "paid_replication": "disabled",
        "paid_llm_statement_generation": "later_gated_by_endpoint_variables",
        "endpoint_variables_present_initially": {
            "LLM_BASE_URL": bool(os.environ.get("LLM_BASE_URL")),
            "LLM_API_KEY": bool(os.environ.get("LLM_API_KEY")),
        },
        "claims": ["paid_replication_not_run"],
        "disallowed_claims_made": [],
    }
    write_json(OUTPUTS["preflight"], payload)
    write_process_report()
    return payload


def aggregate_existing_rows() -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    artifact_paths = list((PHASE0_ROOT / "candidate_sources").glob("*.jsonl")) + list((PHASE0_ROOT / "certified_tasks").glob("*.jsonl"))
    for path in sorted(artifact_paths):
        for row in read_jsonl(path):
            if not is_target_repo_row(row):
                continue
            task_id = task_id_from_row(row)
            if not task_id:
                continue
            repo_id = str(row.get("repo_id") or repo_from_task_id(task_id))
            entry = tasks.setdefault(
                task_id,
                {
                    "repo_id": repo_id,
                    "task_id": task_id,
                    "source_artifacts": [],
                    "source_kinds": [],
                    "rows_seen": 0,
                },
            )
            entry["rows_seen"] += 1
            entry["source_artifacts"].append(rel(path))
            entry["source_kinds"].append(path.parent.name)
            for key in [
                "base_commit",
                "target_commit",
                "task_time",
                "subject",
                "status",
                "candidate_filter_status",
                "promotion_decision",
                "source_context_status",
                "statement_review_status",
                "split",
                "first_failing_gate",
                "raw_certification_status",
            ]:
                if row.get(key) not in (None, "", []):
                    entry[key] = row[key]
            for key in ["changed_files", "code_files", "implementation_files", "test_files", "module_or_package", "promotion_blockers"]:
                if row.get(key):
                    entry[key] = row[key]
            for key in ["gates", "local_certification_gates", "clean_overlay_certification_gates"]:
                if row.get(key):
                    entry[key] = row[key]
            if row.get("solver_facing_statement"):
                entry["solver_facing_statement"] = row["solver_facing_statement"]
            if row.get("sanitized_context"):
                entry["sanitized_context"] = row["sanitized_context"]
    for path in sorted((PHASE0_ROOT / "candidate_sources").glob("*source_context*.jsonl")):
        for row in read_jsonl(path):
            if not is_target_repo_row(row):
                continue
            task_id = task_id_from_row(row)
            if not task_id or task_id not in tasks:
                continue
            tasks[task_id]["source_context"] = row
            tasks[task_id]["source_artifacts"].append(rel(path))
            if row.get("ref"):
                tasks[task_id]["source_ref"] = row["ref"]
    return tasks


def certification_summary_for(row: dict[str, Any]) -> dict[str, Any]:
    gates = dict(row.get("clean_overlay_certification_gates") or row.get("local_certification_gates") or row.get("gates") or {})
    if row.get("status") == "certified" or row.get("promotion_decision") == "promote_to_clean_benchmark_candidate":
        for gate in [
            "checkout",
            "oracle_extractable",
            "no_op_fail",
            "reference_pass",
            "known_bad_fail",
            "flakiness_check",
            "scope_clarity_review",
            "cost_boundedness",
            "taxonomy_labelability",
        ]:
            gates.setdefault(gate, "pass")
    context = row.get("source_context") or row.get("sanitized_context") or {}
    if context.get("classification") == "problem_context" and not str(context.get("ref", "")).startswith("commit:"):
        gates.setdefault("solution_leakage_review", "pass")
    quality = row.get("statement_quality") or {}
    if quality.get("statement_quality_gate") == "pass":
        gates.setdefault("statement_quality_review", "pass")
    return {
        "gates": gates,
        "first_failing_gate": first_failing_gate(gates) or str(row.get("first_failing_gate") or ""),
        "all_required_gates_pass": all_required_gates_pass(gates),
    }


def existing_inventory() -> dict[str, Any]:
    tasks = aggregate_existing_rows()
    pre_paid = load_pre_paid_inventory_rows()
    bakeoff_rows = load_bakeoff_task_rows()
    split_index = load_release_split_index()
    seen = load_seen_indexes()
    seen_task_ids = set(seen["paid_outcome_seen_task_ids"])
    seen_target_commits = set(seen["paid_outcome_seen_target_commits"])
    rows: list[dict[str, Any]] = []
    for task_id, row in sorted(tasks.items(), key=lambda item: (item[1].get("repo_id", ""), item[1].get("task_time", ""), item[0])):
        repo_id = str(row["repo_id"])
        target = str(row.get("target_commit") or "")
        context = row.get("source_context") or row.get("sanitized_context") or {}
        source_ref = str(row.get("source_ref") or context.get("ref") or "")
        source_kind = source_kind_from_ref(source_ref)
        statement = str(row.get("solver_facing_statement") or context.get("summary") or row.get("subject") or "")
        pre = pre_paid.get(task_id, {})
        bakeoff = bakeoff_rows.get(task_id, {})
        cert = certification_summary_for(row)
        outcome_seen = task_id in seen_task_ids or bool(target and target in seen_target_commits)
        certified_like = (
            row.get("status") == "certified"
            or row.get("promotion_decision") == "promote_to_clean_benchmark_candidate"
            or cert["all_required_gates_pass"]
            or str(pre.get("raw_certification_status")) == "certified"
        )
        source_status = str(row.get("source_context_status") or pre.get("source_kind") or ("missing" if not source_ref else "present"))
        eligible_without_paid = bool(
            certified_like
            and not outcome_seen
            and source_ref
            and not source_ref.startswith("commit:")
            and not row.get("promotion_blockers")
        )
        reason: list[str] = []
        if not certified_like:
            reason.append("not_certified_or_required_gates_missing")
        if outcome_seen:
            reason.append("historical_paid_outcome_or_target_commit_seen")
        if not source_ref:
            reason.append("source_context_missing")
        elif source_ref.startswith("commit:"):
            reason.append("commit_message_only_source")
        if row.get("promotion_blockers"):
            reason.extend(str(item) for item in row.get("promotion_blockers", []))
        rows.append(
            {
                "repo_id": repo_id,
                "task_id": task_id,
                "base_commit_present": bool(row.get("base_commit")),
                "target_commit_present": bool(target),
                "target_commit": target,
                "task_time": row.get("task_time"),
                "source_kind": source_kind,
                "source_context_status": source_status,
                "statement_quality_gate": pre.get("statement_quality_status") or (row.get("statement_quality") or {}).get("statement_quality_gate") or "unknown",
                "certification_gate_summary": cert,
                "release_split_eligibility": {
                    "historical_release_split": split_index.get(task_id),
                    "pre_paid_eligible_for_target_profile": pre.get("eligible_for_target_profile"),
                    "pre_paid_eligible_for_next_release": pre.get("eligible_for_next_release"),
                    "local_bakeoff_membership": bool(bakeoff),
                },
                "historical_paid_cells_present": bool(bakeoff) or task_id in seen_task_ids,
                "outcome_seen_status": "outcome_seen" if outcome_seen else "outcome_unseen",
                "eligible_without_paid_outcome": eligible_without_paid,
                "eligibility_explanation": "eligible_without_paid_outcome" if eligible_without_paid else ";".join(unique_preserve(reason)) or "diagnostic_only",
                "changed_file_count": len(row.get("changed_files") or []),
                "implementation_file_count": len(implementation_files(row)),
                "test_file_count": len(test_files(row)),
                "module_or_package": module_or_package(row),
                "statement_digest": digest_text(statement) if statement else "",
            }
        )
    summary = {
        "task_count": len(rows),
        "by_repo": dict(sorted(Counter(row["repo_id"] for row in rows).items())),
        "eligible_without_paid_outcome_by_repo": dict(
            sorted(Counter(row["repo_id"] for row in rows if row["eligible_without_paid_outcome"]).items())
        ),
        "historical_paid_cells_by_repo": dict(sorted(Counter(row["repo_id"] for row in rows if row["historical_paid_cells_present"]).items())),
        "starting_bakeoff_paid_readiness_supply_by_repo": EXISTING_BAKEOFF_ELIGIBLE_COUNTS,
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "status": "existing_supply_inventory_completed",
        "summary": summary,
        "rows": rows,
    }
    duplicate = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "status": "duplicate_and_leakage_index_completed",
        **seen,
    }
    write_json(OUTPUTS["existing_inventory"], payload)
    write_json(OUTPUTS["duplicate_and_leakage_index"], duplicate)
    write_text(REPORTS["existing_inventory"], existing_inventory_report(payload, duplicate))
    write_process_report()
    return payload


def mining_plan() -> dict[str, Any]:
    inventory = read_json(OUTPUTS["existing_inventory"], default={}) or existing_inventory()
    repo_windows = {}
    for repo_id in TARGET_REPOS:
        repo = repo_path(repo_id)
        dates = git_lines(repo, ["log", "--since=2010-01-01", "--format=%ad", "--date=iso-strict"], timeout=120)
        candidate_modules = Counter(
            module
            for row in inventory.get("rows", [])
            if row.get("repo_id") == repo_id
            for module in row.get("module_or_package", []) or ["unknown"]
        )
        repo_windows[repo_id] = {
            "history_window_start": min(dates) if dates else None,
            "history_window_end": max(dates) if dates else None,
            "existing_module_coverage": dict(candidate_modules.most_common(20)),
            "scan_policy": "scan chronologically since 2010 and retain broad module/time coverage up to the raw soft cap",
        }
    quotas = {}
    for repo_id in TARGET_REPOS:
        current = int(EXISTING_BAKEOFF_ELIGIBLE_COUNTS.get(repo_id, 0))
        quotas[repo_id] = {
            "current_eligible": current,
            "minimum_new_certified_needed": max(0, MINIMUM_TARGET_PER_REPO - current),
            "stretch_new_certified_needed": max(0, STRETCH_TARGET_PER_REPO - current),
            "raw_candidate_floor": RAW_CANDIDATE_FLOOR_PER_REPO,
            "raw_candidate_soft_cap": RAW_CANDIDATE_SOFT_CAP_PER_REPO,
            "local_certification_attempt_soft_cap": LOCAL_CERTIFICATION_ATTEMPT_SOFT_CAP_PER_REPO,
        }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "status": "raw_candidate_mining_plan_completed",
        "quotas": quotas,
        "repository_history_windows": repo_windows,
        "candidate_priorities": [
            "prefer behavior/API bugfixes over refactors",
            "prefer non-leaky issue or PR context",
            "prefer target commits with local tests that expose behavior",
            "prefer bounded implementation scope",
            "prefer tasks not outcome-seen in any score table",
        ],
        "candidate_avoidance_rules": [
            "docs-only",
            "project-config-heavy",
            "formatting-only",
            "dependency-only",
            "ambiguous project maintenance",
            "public context states exact solution patch",
        ],
        "hard_stop_rules": [
            "history scan reaches anchor cap",
            "source enrichment finds no additional non-leaky problem context",
            "certification attempts reach cap or plausible candidates are exhausted",
            "dominant failure modes are reported",
        ],
        "new_repository_selection": "contingency_only",
        "claims": ["existing_supply_inventory_completed"],
    }
    write_json(OUTPUTS["mining_plan"], payload)
    write_text(REPORTS["mining_plan"], mining_plan_report(payload))
    write_process_report()
    return payload


def candidate_filter_status(subject: str, paths: list[str], added: int, deleted: int) -> dict[str, Any]:
    code_files, tests = repo_history_pilot.classify_paths(paths)
    modules = repo_history_pilot.module_names(code_files)
    decision = repo_history_pilot.candidate_filter_decision(
        subject=subject,
        changed_files=paths,
        code_files=code_files,
        added=added,
        deleted=deleted,
        modules=modules,
    )
    reject_reasons = list(decision["reject_reasons"])
    if not tests:
        reject_reasons.append("no_changed_test_file")
    selected = bool(tests) and decision["candidate_filter_status"] != "rejected"
    return {
        "selected": selected,
        "code_files": code_files,
        "test_files": tests,
        "modules": modules,
        "candidate_filter_status": decision["candidate_filter_status"],
        "reject_reasons": reject_reasons,
        "manual_review_reasons": decision["manual_review_reasons"],
    }


def git_numstat(repo: Path, commit: str) -> tuple[int, int]:
    added = 0
    deleted = 0
    for line in git_lines(repo, ["show", "--format=", "--numstat", commit], timeout=120):
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        try:
            added += int(parts[0])
            deleted += int(parts[1])
        except ValueError:
            continue
    return added, deleted


def git_diff_digest(repo: Path, base: str, target: str) -> str:
    result = command_result(["git", "diff", "--binary", base, target], repo, timeout=120)
    return digest_text(result["stdout"] if result["returncode"] == 0 else result["stderr"])


def mine_raw_repo(repo_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    repo = repo_path(repo_id)
    existing_commits = existing_target_commits()
    seen = load_seen_indexes()
    outcome_seen_commits = set(seen["paid_outcome_seen_target_commits"])
    raw = subprocess.check_output(
        ["git", "log", "--since=2010-01-01", "--reverse", "--format=%x1e%H%x09%P%x09%ad%x09%s", "--date=iso-strict", "--name-only"],
        cwd=repo,
        text=True,
        errors="replace",
    )
    rows: list[dict[str, Any]] = []
    anchors_scanned = 0
    plausible_seen = 0
    for chunk in raw.split("\x1e"):
        lines = [line for line in chunk.splitlines() if line.strip()]
        if not lines:
            continue
        meta = lines[0].split("\t", 3)
        if len(meta) != 4:
            continue
        commit, parents, task_time, subject = meta
        parent = parents.split()[0] if parents.split() else ""
        if not parent:
            continue
        anchors_scanned += 1
        paths = lines[1:]
        added, deleted = git_numstat(repo, commit)
        decision = candidate_filter_status(subject, paths, added, deleted)
        if not decision["selected"]:
            continue
        plausible_seen += 1
        duplicate_target = commit in existing_commits
        outcome_seen = commit in outcome_seen_commits
        status = "excluded_duplicate_or_outcome_seen" if duplicate_target or outcome_seen else "selected_for_source_context"
        candidate_id = stable_candidate_id(repo_id, plausible_seen)
        row = {
            "schema_version": "barcarolle.phase1.two_repo_supply_raw_candidate.v1",
            "repo_id": repo_id,
            "candidate_id": candidate_id,
            "task_id": candidate_id,
            "target_commit": commit,
            "base_commit": parent,
            "task_time": task_time,
            "changed_files": paths,
            "implementation_files": decision["code_files"],
            "code_files": decision["code_files"],
            "test_files": decision["test_files"],
            "candidate_oracle_source": decision["test_files"],
            "change_size_bucket": repo_history_pilot.change_size_bucket(added + deleted),
            "module_or_package": decision["modules"],
            "commit_subject_summary": " ".join(subject.split())[:200],
            "subject": subject,
            "candidate_source_refs": [f"commit:{commit}"],
            "candidate_source_kind": "git_commit",
            "public_context_available": "unknown_pending_enrichment",
            "diff_digest": git_diff_digest(repo, parent, commit),
            "diff_size_summary": {
                "changed_file_count": len(paths),
                "implementation_file_count": len(decision["code_files"]),
                "test_file_count": len(decision["test_files"]),
                "changed_lines_added": added,
                "changed_lines_deleted": deleted,
            },
            "candidate_filter_status": decision["candidate_filter_status"],
            "manual_review_reasons": decision["manual_review_reasons"],
            "promotion_exclusion_reasons": [
                reason
                for reason, present in {
                    "duplicate_existing_target_commit": duplicate_target,
                    "previous_acut_target_commit_seen": outcome_seen,
                }.items()
                if present
            ],
            "outcome_seen_status": "outcome_seen" if outcome_seen else "outcome_unseen",
            "raw_candidate_status": status,
        }
        rows.append(row)
        selected_new = sum(1 for item in rows if item["raw_candidate_status"] == "selected_for_source_context")
        if len(rows) >= RAW_CANDIDATE_SOFT_CAP_PER_REPO and selected_new >= RAW_CANDIDATE_FLOOR_PER_REPO:
            break
    summary = {
        "repo_id": repo_id,
        "anchors_scanned": anchors_scanned,
        "raw_candidate_count": len(rows),
        "selected_for_source_context_count": sum(1 for row in rows if row["raw_candidate_status"] == "selected_for_source_context"),
        "duplicate_or_outcome_seen_count": sum(1 for row in rows if row["raw_candidate_status"] == "excluded_duplicate_or_outcome_seen"),
        "raw_candidate_floor_met": len(rows) >= RAW_CANDIDATE_FLOOR_PER_REPO,
        "soft_cap": RAW_CANDIDATE_SOFT_CAP_PER_REPO,
    }
    return rows, summary


def raw_candidates() -> dict[str, Any]:
    if not output_path("mining_plan").exists():
        mining_plan()
    by_repo: dict[str, Any] = {}
    all_rows: list[dict[str, Any]] = []
    for repo_id in TARGET_REPOS:
        rows, summary = mine_raw_repo(repo_id)
        write_jsonl(phase0_candidate_path(repo_id, "candidates"), rows)
        by_repo[repo_id] = summary
        all_rows.extend(rows)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "status": "raw_candidate_mining_completed",
        "summary_by_repo": by_repo,
        "raw_candidate_count": len(all_rows),
        "raw_candidate_floor_per_repo": RAW_CANDIDATE_FLOOR_PER_REPO,
        "raw_candidate_soft_cap_per_repo": RAW_CANDIDATE_SOFT_CAP_PER_REPO,
        "rows": all_rows,
        "claims": ["raw_candidate_mining_completed"],
        "paid_acut_calls_made": False,
        "paid_task_solving_calls_made": False,
    }
    write_json(OUTPUTS["raw_candidates"], payload)
    write_text(REPORTS["raw_candidates"], raw_candidates_report(payload))
    write_process_report()
    return payload


def issue_numbers_from_text(text: str) -> list[int]:
    numbers: list[int] = []
    for match in __import__("re").finditer(r"(?:fixes?|closes?|resolves?)\s+#(\d+)|#(\d+)|\bissue\s+(\d+)", text, flags=__import__("re").IGNORECASE):
        raw = match.group(1) or match.group(2) or match.group(3)
        if raw:
            numbers.append(int(raw))
    return list(dict.fromkeys(numbers))


def issue_lookup(repo_id: str, number: int) -> dict[str, Any] | None:
    owner_repo = REPO_CONFIGS[repo_id]["repo_url"].removeprefix("https://github.com/").removesuffix(".git")
    proc = command_result(
        ["gh", "api", f"repos/{owner_repo}/issues/{number}", "--jq", "{number,title,body:(.body // \"\"),state,is_pull_request:(.pull_request != null)}"],
        REPO_ROOT,
        timeout=30,
    )
    if proc["returncode"] != 0:
        return None
    try:
        payload = json.loads(proc["stdout"])
    except json.JSONDecodeError:
        return None
    if payload.get("is_pull_request"):
        return None
    title = " ".join(str(payload.get("title") or "").split())
    if not title:
        return None
    return {
        "ref": f"issue:{number}",
        "classification": "problem_context",
        "summary": title,
        "body_summary": statement_quality.sanitize_public_body_summary(payload.get("body")),
        "state": payload.get("state"),
    }


def context_has_solution_exposure(context: dict[str, Any]) -> bool:
    summary = str(context.get("summary") or "").lower()
    body = str(context.get("body_summary") or "").lower()
    terms = ["rework", "refactor", "rename", "move ", "wrapped ", "revert ", "polish", "use ", "replace "]
    if summary.startswith(("fix ", "fixed ", "don't ", "dont ", "add ")):
        return any(term in body for term in terms)
    return any(term in f"{summary} {body}" for term in terms[:7])


def supply_statement_quality_gate(quality: dict[str, Any], context: dict[str, Any]) -> str:
    """Apply this runbook's softer source screen without the old PR/240-char penalties."""
    title = " ".join(str(context.get("summary") or context.get("title_or_summary") or "").split())
    risk_reasons = set(str(reason) for reason in quality.get("risk_reasons", []))
    hard_reasons = risk_reasons - {
        "body_summary_hit_old_240_char_cap",
        "pr_context_source",
        "pr_context_without_linked_issue",
        "statement_probably_truncated",
    }
    if "statement_ends_mid_code_fence" in risk_reasons:
        return "material_risk"
    if "empty_or_nearly_empty_body_summary" in risk_reasons and len(title) < 24:
        return "material_risk"
    if "statement_missing_public_problem_summary" in risk_reasons and len(title) < 24:
        return "material_risk"
    if any(reason.endswith("_under_specified") for reason in risk_reasons):
        return "material_risk"
    if "statement_missing_editable_implementation_scope" in hard_reasons:
        return "material_risk"
    return "pass"


def selected_context_for_candidate(repo_id: str, candidate: dict[str, Any]) -> dict[str, Any]:
    cfg = pilot_config(repo_id)
    pr_refs = repo_history_pilot.github_pr_refs(cfg, str(candidate["target_commit"]))
    issue_refs: list[dict[str, Any]] = []
    for ref in pr_refs:
        linked_text = f"{ref.get('summary', '')} {ref.get('body_summary', '')}"
        for number in issue_numbers_from_text(linked_text):
            issue = issue_lookup(repo_id, number)
            if issue:
                issue_refs.append(issue)
    refs = issue_refs or pr_refs
    if not refs:
        refs = [repo_history_pilot.commit_context_ref(cfg, candidate)]
    context = dict(refs[0])
    context["repo_id"] = repo_id
    context["task_id"] = candidate["task_id"]
    context["target_commit"] = candidate["target_commit"]
    return context


def normalize_source_context(repo_id: str, candidate: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    source_ref = str(context.get("ref") or "")
    source_kind = source_kind_from_ref(source_ref)
    title = " ".join(str(context.get("summary") or candidate.get("subject") or "").split())
    body = statement_quality.sanitize_public_body_summary(context.get("body_summary"))
    normalized_for_quality = {
        "ref": source_ref,
        "classification": context.get("classification") or ("problem_context" if source_kind in {"issue", "pull_request"} else "diagnostic_only_context"),
        "summary": title,
        "body_summary": body,
    }
    quality = statement_quality.statement_quality_for_context(normalized_for_quality, candidate)
    supply_quality = supply_statement_quality_gate(quality, normalized_for_quality)
    leakage_risks: list[str] = []
    if context_has_solution_exposure(normalized_for_quality):
        leakage_risks.append("solution_exposure_risk")
    if source_ref.startswith("commit:"):
        status = "commit_message_only_source"
        confidence = "low"
    elif leakage_risks:
        status = "diff_assisted_statement_needed"
        confidence = "medium"
    elif supply_quality == "material_risk":
        status = "diff_assisted_statement_needed"
        confidence = "medium"
    else:
        status = "non_leaky_problem_context"
        confidence = "high" if source_ref.startswith("issue:") else "medium"
    digest = digest_text(f"{source_ref}\n{title}\n{body}")
    return {
        "schema_version": "barcarolle.phase1.two_repo_supply_source_context.v1",
        "repo_id": repo_id,
        "task_id": candidate["task_id"],
        "target_commit": candidate["target_commit"],
        "source_ref": source_ref,
        "ref": source_ref,
        "source_kind": source_kind,
        "classification": normalized_for_quality["classification"],
        "title_or_summary": title,
        "summary": title,
        "body_summary": body,
        "linked_issue_refs": [f"issue:{number}" for number in issue_numbers_from_text(f"{title} {body}")],
        "linked_pr_refs": [source_ref] if source_ref.startswith("pr:") else [],
        "problem_context_confidence": confidence,
        "source_context_status": status,
        "source_leakage_risks": leakage_risks,
        "statement_quality": quality,
        "supply_statement_quality_gate": supply_quality,
        "source_context_digest": digest,
    }


def source_contexts() -> dict[str, Any]:
    if not output_path("raw_candidates").exists():
        raw_candidates()
    by_repo: dict[str, Any] = {}
    all_rows: list[dict[str, Any]] = []
    for repo_id in TARGET_REPOS:
        contexts: list[dict[str, Any]] = []
        candidates = read_jsonl(phase0_candidate_path(repo_id, "candidates"))
        for candidate in candidates:
            if candidate.get("raw_candidate_status") != "selected_for_source_context":
                continue
            context = selected_context_for_candidate(repo_id, candidate)
            contexts.append(normalize_source_context(repo_id, candidate, context))
        write_jsonl(phase0_candidate_path(repo_id, "source_context"), contexts)
        status_counts = Counter(row["source_context_status"] for row in contexts)
        by_repo[repo_id] = {
            "candidate_count": len(candidates),
            "source_context_count": len(contexts),
            "source_context_status_counts": dict(sorted(status_counts.items())),
            "source_context_failure_modes": {
                key: value
                for key, value in sorted(status_counts.items())
                if key not in {"non_leaky_problem_context", "diff_assisted_statement_needed"}
            },
        }
        all_rows.extend(contexts)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "status": "source_context_enrichment_completed",
        "summary_by_repo": by_repo,
        "source_context_count": len(all_rows),
        "rows": all_rows,
        "claims": ["source_context_enrichment_completed"],
        "raw_api_responses_committed": False,
    }
    write_json(OUTPUTS["source_contexts"], payload)
    write_text(REPORTS["source_contexts"], source_contexts_report(payload))
    write_process_report()
    return payload


def context_by_task(repo_id: str) -> dict[str, dict[str, Any]]:
    return {str(row["task_id"]): row for row in read_jsonl(phase0_candidate_path(repo_id, "source_context"))}


def statement_for_candidate(repo_id: str, candidate: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    allowed = [context["source_ref"]] if not str(context.get("source_ref", "")).startswith("commit:") else []
    module = ", ".join(candidate.get("module_or_package") or [])
    title = str(context.get("title_or_summary") or candidate.get("subject") or "Repair the described behavior")
    body = str(context.get("body_summary") or "")
    public_context = f"{title}. {body}".strip()
    statement = (
        f"Repair the {repo_id} behavior described by the selected public context. "
        f"Public context summary: {public_context} "
        f"Focus on the {module or 'affected'} implementation area and preserve existing public behavior. "
        "Do not edit tests, generated metadata, or benchmark artifacts."
    )
    quality_gate = (context.get("statement_quality") or {}).get("statement_quality_gate")
    supply_quality = context.get("supply_statement_quality_gate") or quality_gate
    reviewed = context.get("source_context_status") == "non_leaky_problem_context" and supply_quality != "material_risk"
    return {
        "schema_version": "barcarolle.repo_history_statement.v1",
        "task_id": candidate["task_id"],
        "repo_id": repo_id,
        "base_commit": candidate["base_commit"],
        "target_commit": candidate["target_commit"],
        "solver_facing_statement": statement_quality.sanitize_public_body_summary(statement, limit=2200),
        "scope_boundaries": f"Modify only implementation files needed for this {repo_id} behavior; do not edit tests or generated metadata.",
        "allowed_context_refs": allowed,
        "excluded_context_refs": [] if allowed else [context.get("source_ref", "")],
        "oracle_refs": candidate["test_files"],
        "harness_test_command": REPO_CONFIGS[repo_id]["command_template"],
        "statement_quality": context.get("statement_quality", {}),
        "statement_review_status": "reviewed" if reviewed else "diff_assisted_statement_needed",
        "source_context_status": context.get("source_context_status"),
    }


def prioritize_candidates(repo_id: str) -> list[dict[str, Any]]:
    contexts = context_by_task(repo_id)
    candidates = [row for row in read_jsonl(phase0_candidate_path(repo_id, "candidates")) if row.get("raw_candidate_status") == "selected_for_source_context"]

    def key(row: dict[str, Any]) -> tuple[int, int, str, str]:
        context = contexts.get(str(row["task_id"]), {})
        context_rank = {"non_leaky_problem_context": 0, "diff_assisted_statement_needed": 1, "commit_message_only_source": 2}.get(
            str(context.get("source_context_status")), 3
        )
        filter_rank = 0 if row.get("candidate_filter_status") == "accepted" else 1
        return (context_rank, filter_rank, str(row.get("task_time")), str(row.get("task_id")))

    return sorted(candidates, key=key)[:LOCAL_CERTIFICATION_ATTEMPT_SOFT_CAP_PER_REPO]


def review_certification_row(row: dict[str, Any], context: dict[str, Any], seen: dict[str, Any]) -> dict[str, Any]:
    target = str(row.get("target_commit") or "")
    blockers: list[str] = []
    if row.get("status") != "certified":
        blockers.append(f"local_certification_gate_failed:{row.get('first_failing_gate') or 'unknown'}")
    if target in set(seen["paid_outcome_seen_target_commits"]):
        blockers.append("previous_acut_target_commit_seen")
    if context.get("source_context_status") != "non_leaky_problem_context":
        blockers.append(str(context.get("source_context_status") or "source_context_missing"))
    supply_quality = context.get("supply_statement_quality_gate") or (context.get("statement_quality") or {}).get("statement_quality_gate")
    if supply_quality == "material_risk":
        blockers.append("statement_quality_risk")
    blockers.extend(str(reason) for reason in context.get("source_leakage_risks", []))
    gates = dict(row.get("gates") or {})
    gates["statement_quality_review"] = "pass" if "statement_quality_risk" not in blockers else "fail"
    if "solution_exposure_risk" in blockers:
        gates["solution_leakage_review"] = "fail"
    else:
        gates.setdefault("solution_leakage_review", "pass" if context.get("source_context_status") == "non_leaky_problem_context" else "fail")
    decision = "locally_certified_statement_ready" if not blockers and all_required_gates_pass(gates) else "not_promoted"
    if row.get("status") == "certified" and context.get("source_context_status") == "diff_assisted_statement_needed":
        decision = "needs_endpoint_statement_generation_review"
    row = dict(row)
    row.update(
        {
            "source_context_status": context.get("source_context_status"),
            "source_ref": context.get("source_ref"),
            "statement_quality": context.get("statement_quality"),
            "reviewed_required_gates": gates,
            "review_first_failing_gate": first_failing_gate(gates),
            "promotion_decision": decision,
            "promotion_blockers": unique_preserve(blockers),
            "promotion_rationale": "local_certification_and_non_leaky_public_context" if decision == "locally_certified_statement_ready" else "",
            "paid_acut_calls_made": False,
            "paid_task_solving_calls_made": False,
        }
    )
    return row


def certification_attempts() -> dict[str, Any]:
    if not output_path("source_contexts").exists():
        source_contexts()
    seen = load_seen_indexes()
    all_rows: list[dict[str, Any]] = []
    by_repo: dict[str, Any] = {}
    for repo_id in TARGET_REPOS:
        cfg = pilot_config(repo_id)
        contexts = context_by_task(repo_id)
        statements: list[dict[str, Any]] = []
        attempts: list[dict[str, Any]] = []
        for candidate in prioritize_candidates(repo_id):
            context = contexts.get(str(candidate["task_id"]))
            if not context:
                continue
            statement = statement_for_candidate(repo_id, candidate, context)
            statements.append(statement)
            result = repo_history_pilot.certify_candidate(REPO_ROOT, PHASE0_ROOT, cfg, candidate, statement)
            attempts.append(review_certification_row(result, context, seen))
        write_jsonl(phase0_certified_path(repo_id, "review_records"), attempts)
        write_jsonl(phase0_certified_path(repo_id, "task_statements"), statements)
        status_counts = Counter(row.get("status", "unknown") for row in attempts)
        decision_counts = Counter(row.get("promotion_decision", "unknown") for row in attempts)
        first_gate_counts = Counter(row.get("review_first_failing_gate") or row.get("first_failing_gate") or "none" for row in attempts)
        by_repo[repo_id] = {
            "attempt_count": len(attempts),
            "local_certification_status_counts": dict(sorted(status_counts.items())),
            "promotion_decision_counts": dict(sorted(decision_counts.items())),
            "first_failing_gate_counts": dict(sorted(first_gate_counts.items())),
            "ready_count": decision_counts.get("locally_certified_statement_ready", 0),
            "needs_endpoint_statement_generation_review_count": decision_counts.get("needs_endpoint_statement_generation_review", 0),
        }
        all_rows.extend(attempts)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "status": "local_certification_replay_completed",
        "summary_by_repo": by_repo,
        "rows": all_rows,
        "claims": ["local_certification_replay_completed", "paid_replication_not_run"],
        "paid_acut_calls_made": False,
        "paid_task_solving_calls_made": False,
    }
    write_json(OUTPUTS["certification_attempts"], payload)
    write_text(REPORTS["certification_attempts"], certification_attempts_report(payload))
    write_process_report()
    return payload


def bounded_diff_summary(candidate: dict[str, Any]) -> dict[str, Any]:
    summary = dict(candidate.get("diff_size_summary") or {})
    summary["diff_digest"] = candidate.get("diff_digest")
    summary["changed_files_preview"] = list(candidate.get("changed_files") or [])[:12]
    return summary


def statement_packets() -> dict[str, Any]:
    if not output_path("certification_attempts").exists():
        certification_attempts()
    attempts_payload = read_json(OUTPUTS["certification_attempts"], default={}) or {}
    candidates_by_task = {
        str(row["task_id"]): row
        for repo_id in TARGET_REPOS
        for row in read_jsonl(phase0_candidate_path(repo_id, "candidates"))
    }
    contexts_by_task = {
        str(row["task_id"]): row
        for repo_id in TARGET_REPOS
        for row in read_jsonl(phase0_candidate_path(repo_id, "source_context"))
    }
    packets: list[dict[str, Any]] = []
    for attempt in attempts_payload.get("rows", []):
        if attempt.get("status") != "certified" and attempt.get("first_failing_gate") not in {"ambiguity_review", "solution_leakage_review"}:
            continue
        task_id = str(attempt["task_id"])
        candidate = candidates_by_task.get(task_id, {})
        context = contexts_by_task.get(task_id, {})
        packet = {
            "schema_version": "barcarolle.phase1.two_repo_statement_packet.v1",
            "repo_id": attempt.get("repo_id"),
            "task_id": task_id,
            "target_commit": attempt.get("target_commit"),
            "public_issue_or_pr_summary": context.get("title_or_summary"),
            "linked_public_context_summaries": {
                "source_ref": context.get("source_ref"),
                "source_kind": context.get("source_kind"),
                "body_summary": context.get("body_summary"),
            },
            "base_behavior_summary": "base behavior fails the target commit changed tests during no-op replay" if attempt.get("status") == "certified" else "not locally certified",
            "expected_behavior_summary": "target behavior passes the target commit changed tests during reference replay" if attempt.get("status") == "certified" else "requires certification repair",
            "bounded_diff_summary": bounded_diff_summary(candidate),
            "changed_file_categories": {
                "implementation_files": candidate.get("implementation_files", []),
                "test_files": candidate.get("test_files", []),
            },
            "implementation_scope_hints": candidate.get("module_or_package", []),
            "test_behavior_summary": f"Oracle extracted from changed test files: {', '.join(candidate.get('test_files', []))}",
            "explicit_leakage_constraints": [
                "do not include target commit id",
                "do not include patch text",
                "do not include hidden verifier content",
                "do not mention exact solution algorithm unless public context already states it",
            ],
            "statement_generation_requirement": "not_needed_public_context_accepted"
            if attempt.get("promotion_decision") == "locally_certified_statement_ready"
            else "endpoint_generation_or_review_needed",
            "diff_assisted_generation_allowed_only_after_leakage_review": True,
        }
        packets.append(packet)
    by_repo = defaultdict(Counter)
    for packet in packets:
        by_repo[str(packet["repo_id"])][str(packet["statement_generation_requirement"])] += 1
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "status": "statement_generation_packets_prepared",
        "packet_count": len(packets),
        "summary_by_repo": {repo: dict(sorted(counter.items())) for repo, counter in sorted(by_repo.items())},
        "packets": packets,
        "claims": ["statement_generation_packets_prepared"],
        "raw_prompts_committed": False,
        "raw_completions_committed": False,
    }
    write_json(OUTPUTS["statement_packets"], payload)
    write_text(REPORTS["statement_packets"], statement_packets_report(payload))
    write_process_report()
    return payload


def statement_generation_review() -> dict[str, Any]:
    if not output_path("statement_packets").exists():
        statement_packets()
    packets = read_json(OUTPUTS["statement_packets"], default={}) or {}
    attempts = read_json(OUTPUTS["certification_attempts"], default={}) or {}
    ready_by_repo = {
        repo_id: int((attempts.get("summary_by_repo", {}).get(repo_id, {}) or {}).get("ready_count", 0))
        for repo_id in TARGET_REPOS
    }
    needed_by_repo = {
        repo_id: max(0, MINIMUM_TARGET_PER_REPO - EXISTING_BAKEOFF_ELIGIBLE_COUNTS[repo_id] - ready_by_repo.get(repo_id, 0))
        for repo_id in TARGET_REPOS
    }
    endpoint_needed = any(value > 0 for value in needed_by_repo.values()) and any(
        packet.get("statement_generation_requirement") == "endpoint_generation_or_review_needed" for packet in packets.get("packets", [])
    )
    env_present = bool(os.environ.get("LLM_BASE_URL")) and bool(os.environ.get("LLM_API_KEY"))
    if endpoint_needed:
        status = "statement_generation_blocked_by_endpoint_policy"
        blocker = (
            "endpoint variables are missing"
            if not env_present
            else "no approved generator/reviewer wrapper in this runbook execution proves paid LLM calls use only LLM_BASE_URL and LLM_API_KEY"
        )
        write_text(
            ROOT / "reports" / "phase1_two_repo_supply_expansion_statement_generation_blocker.md",
            "\n".join(
                [
                    "# Statement Generation Endpoint Blocker",
                    "",
                    f"Generated: `{now_utc()}`.",
                    "",
                    f"Status: `{status}`.",
                    f"Blocker: `{blocker}`.",
                    "",
                    "No paid LLM statement-generation calls were made.",
                    "No deterministic substitute is presented as the endpoint generator/reviewer loop.",
                ]
            ),
        )
    else:
        status = "endpoint_statement_generation_review_not_run_not_needed"
        blocker = ""
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "status": status,
        "endpoint_needed_to_reach_minimum": endpoint_needed,
        "minimum_deficit_after_statement_ready_tasks": needed_by_repo,
        "LLM_BASE_URL_present": bool(os.environ.get("LLM_BASE_URL")),
        "LLM_API_KEY_present": bool(os.environ.get("LLM_API_KEY")),
        "endpoint_rule_satisfied_if_paid_llm_used": False if endpoint_needed else None,
        "blocker": blocker,
        "new_paid_llm_statement_calls_made": False,
        "raw_prompts_committed": False,
        "raw_completions_committed": False,
        "claims": [status] if endpoint_needed else ["endpoint_statement_generation_review_completed"],
    }
    write_json(OUTPUTS["statement_generation_review"], payload)
    write_process_report()
    return payload


def promoted_attempts() -> list[dict[str, Any]]:
    attempts = read_json(OUTPUTS["certification_attempts"], default={}) or {}
    seen = set(load_seen_indexes()["paid_outcome_seen_target_commits"])
    promoted = []
    for row in attempts.get("rows", []):
        if row.get("promotion_decision") != "locally_certified_statement_ready":
            continue
        if str(row.get("target_commit") or "") in seen:
            continue
        promoted.append(row)
    return promoted


def eligibility_and_freeze() -> dict[str, Any]:
    if not output_path("statement_generation_review").exists():
        statement_generation_review()
    contexts_by_task = {
        str(row["task_id"]): row
        for repo_id in TARGET_REPOS
        for row in read_jsonl(phase0_candidate_path(repo_id, "source_context"))
    }
    promoted = promoted_attempts()
    statements_by_repo: dict[str, list[dict[str, Any]]] = {repo_id: [] for repo_id in TARGET_REPOS}
    promoted_by_repo: dict[str, list[dict[str, Any]]] = {repo_id: [] for repo_id in TARGET_REPOS}
    audit_rows: list[dict[str, Any]] = []
    for row in promoted:
        repo_id = str(row["repo_id"])
        context = contexts_by_task.get(str(row["task_id"]), {})
        statement = {
            "schema_version": "barcarolle.repo_history_statement.v1",
            "task_id": row["task_id"],
            "repo_id": repo_id,
            "base_commit": row.get("base_commit"),
            "target_commit": row.get("target_commit"),
            "solver_facing_statement": row.get("solver_facing_statement"),
            "scope_boundaries": row.get("scope_boundaries"),
            "allowed_context_refs": row.get("allowed_context_refs", []),
            "excluded_context_refs": row.get("excluded_context_refs", []),
            "oracle_refs": row.get("oracle_refs", []),
            "harness_test_command": row.get("harness_test_command"),
            "statement_quality": row.get("statement_quality"),
            "statement_review_status": row.get("statement_review_status"),
            "source_context_status": row.get("source_context_status"),
        }
        frozen = {
            **row,
            "schema_version": "barcarolle.phase1.two_repo_supply_certified_task.v1",
            "leakage_review_status": "pass",
            "statement_digest": digest_text(str(row.get("solver_facing_statement") or "")),
            "promotion_reason": "new local certification plus non-leaky public context",
            "source_ref": context.get("source_ref"),
            "source_kind": context.get("source_kind"),
        }
        promoted_by_repo[repo_id].append(frozen)
        statements_by_repo[repo_id].append(statement)
        audit_rows.append(
            {
                "repo_id": repo_id,
                "task_id": row["task_id"],
                "task_time": row.get("task_time"),
                "source_ref": context.get("source_ref"),
                "source_context_status": row.get("source_context_status"),
                "statement_digest": frozen["statement_digest"],
                "certification_gate_summary": {
                    "gates": row.get("reviewed_required_gates"),
                    "first_failing_gate": row.get("review_first_failing_gate"),
                },
                "leakage_review_status": "pass",
                "outcome_seen_status": "outcome_unseen",
                "release_eligible": True,
                "promotion_reason": frozen["promotion_reason"],
            }
        )
    for repo_id in TARGET_REPOS:
        write_jsonl(phase0_certified_path(repo_id, "certified_tasks"), promoted_by_repo[repo_id])
        write_jsonl(phase0_certified_path(repo_id, "task_statements"), statements_by_repo[repo_id])
    counts = {}
    for repo_id in TARGET_REPOS:
        existing = EXISTING_BAKEOFF_ELIGIBLE_COUNTS[repo_id]
        new = len(promoted_by_repo[repo_id])
        counts[repo_id] = {
            "existing_eligible": existing,
            "new_eligible": new,
            "total_eligible": existing + new,
            "minimum_target_met": existing + new >= MINIMUM_TARGET_PER_REPO,
            "stretch_target_met": existing + new >= STRETCH_TARGET_PER_REPO,
        }
    audit_payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "status": "eligibility_audit_completed",
        "rows": audit_rows,
        "counts_by_repo": counts,
        "no_outcome_seen_target_commit_promoted": True,
    }
    expanded = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "status": "expanded_certified_supply_created",
        "expanded_supply_status": "expanded_supply_reaches_minimum"
        if all(row["minimum_target_met"] for row in counts.values())
        else "expanded_supply_below_minimum",
        "counts_by_repo": counts,
        "promoted_task_ids_by_repo": {repo_id: [row["task_id"] for row in rows] for repo_id, rows in promoted_by_repo.items()},
        "promoted_tasks": audit_rows,
        "phase0_artifacts": {
            repo_id: {
                "certified_tasks": rel(phase0_certified_path(repo_id, "certified_tasks")),
                "review_records": rel(phase0_certified_path(repo_id, "review_records")),
                "task_statements": rel(phase0_certified_path(repo_id, "task_statements")),
            }
            for repo_id in TARGET_REPOS
        },
        "claims": [
            "expanded_certified_supply_created",
            "expanded_supply_reaches_minimum" if all(row["minimum_target_met"] for row in counts.values()) else "expanded_supply_below_minimum",
        ],
    }
    write_json(OUTPUTS["eligibility_audit"], audit_payload)
    write_json(OUTPUTS["expanded_supply"], expanded)
    write_text(REPORTS["eligibility_audit"], eligibility_audit_report(audit_payload))
    write_text(REPORTS["expanded_supply"], expanded_supply_report(expanded))
    write_process_report()
    return expanded


def split_support() -> dict[str, Any]:
    if not output_path("expanded_supply").exists():
        eligibility_and_freeze()
    expanded = read_json(OUTPUTS["expanded_supply"], default={}) or {}
    promoted_tasks = expanded.get("promoted_tasks", [])
    inventory = read_json(OUTPUTS["existing_inventory"], default={}) or {}
    existing_rows = [row for row in inventory.get("rows", []) if row.get("task_id") in load_bakeoff_task_rows()]
    rows = [*existing_rows, *promoted_tasks]
    by_repo: dict[str, Any] = {}
    for repo_id in TARGET_REPOS:
        repo_rows = [row for row in rows if row.get("repo_id") == repo_id]
        years = Counter(str(row.get("task_time", ""))[:4] or "unknown" for row in repo_rows)
        modules = Counter(
            module
            for row in repo_rows
            for module in (row.get("module_or_package") or row.get("implementation_scope_hints") or ["unknown"])
        )
        sorted_rows = sorted(repo_rows, key=lambda row: (str(row.get("task_time") or ""), str(row.get("task_id") or "")))
        midpoint = len(sorted_rows) // 2
        b_eval = sorted_rows[:midpoint]
        h_future = sorted_rows[midpoint:]
        by_repo[repo_id] = {
            "per_repo_count": len(repo_rows),
            "chronological_coverage_by_year": dict(sorted(years.items())),
            "module_package_coverage": dict(modules.most_common(20)),
            "source_kind_mix": dict(sorted(Counter(row.get("source_kind", "unknown") for row in repo_rows).items())),
            "eligible_chronological_split_options": {
                "B_eval_count": len(b_eval),
                "H_future_count": len(h_future),
                "B_eval_task_ids_preview": [row.get("task_id") for row in b_eval[:10]],
                "H_future_task_ids_preview": [row.get("task_id") for row in h_future[:10]],
            },
            "pseudo_future_window_count": len(years),
            "minimum_per_window_support": min(years.values()) if years else 0,
        }
    minimum_counts_met = all((expanded.get("counts_by_repo", {}).get(repo_id, {}) or {}).get("minimum_target_met") for repo_id in TARGET_REPOS)
    paid_outcome_counts = Counter(row["repo_id"] for row in existing_rows if row.get("historical_paid_cells_present"))
    local_bakeoff_meaningful = minimum_counts_met and all(paid_outcome_counts.get(repo_id, 0) >= MINIMUM_TARGET_PER_REPO for repo_id in TARGET_REPOS)
    blocker = "" if local_bakeoff_meaningful else "expanded supply does not add paid local outcomes, so B_eval/H_future gap metrics remain limited to the previous 10 attrs and 12 boltons outcome-seen tasks"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "status": "split_support_completed",
        "by_repo": by_repo,
        "minimum_counts_met": minimum_counts_met,
        "paid_outcome_counts_by_repo": dict(sorted(paid_outcome_counts.items())),
        "H_future_used_as_target_profile": False,
        "local_bakeoff_rerun_meaningful": local_bakeoff_meaningful,
        "local_bakeoff_rerun_blocker": blocker,
        "claims": ["expanded_supply_reaches_minimum" if minimum_counts_met else "expanded_supply_below_minimum"],
    }
    write_json(OUTPUTS["split_support"], payload)
    write_text(REPORTS["split_support"], split_support_report(payload))
    write_process_report()
    return payload


def local_bakeoff_rerun() -> dict[str, Any]:
    if not output_path("split_support").exists():
        split_support()
    support = read_json(OUTPUTS["split_support"], default={}) or {}
    if not support.get("local_bakeoff_rerun_meaningful"):
        payload = {
            "schema_version": SCHEMA_VERSION,
            "run_id": RUN_ID,
            "generated_at": now_utc(),
            "status": "local_bakeoff_rerun_skipped",
            "reason": support.get("local_bakeoff_rerun_blocker"),
            "paid_replication_not_run": True,
            "local_bakeoff_rerun_completed": False,
        }
    else:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "run_id": RUN_ID,
            "generated_at": now_utc(),
            "status": "local_bakeoff_rerun_blocked",
            "reason": "rerun requires a separate local outcome matrix over the expanded inventory; no paid replication or paid task solving was authorized in this runbook",
            "paid_replication_not_run": True,
            "local_bakeoff_rerun_completed": False,
        }
    write_json(OUTPUTS["local_bakeoff_rerun"], payload)
    write_text(REPORTS["local_bakeoff_rerun"], local_bakeoff_report(payload))
    write_process_report()
    return payload


def contingency_screen() -> dict[str, Any]:
    if not output_path("expanded_supply").exists():
        eligibility_and_freeze()
    expanded = read_json(OUTPUTS["expanded_supply"], default={}) or {}
    below_minimum = [
        repo_id
        for repo_id, counts in (expanded.get("counts_by_repo") or {}).items()
        if not counts.get("minimum_target_met")
    ]
    candidates = [
        {
            "repo_id": "toolz",
            "history_depth": "high",
            "issue_pr_quality": "moderate",
            "test_suite_stability": "high",
            "dependency_environment_complexity": "low",
            "api_task_diversity": "high",
            "likely_non_leaky_source_availability": "moderate",
            "estimated_certified_supply": "medium",
            "maintenance_timeline_coverage": "broad",
        },
        {
            "repo_id": "humanize",
            "history_depth": "high",
            "issue_pr_quality": "moderate",
            "test_suite_stability": "medium",
            "dependency_environment_complexity": "medium",
            "api_task_diversity": "medium",
            "likely_non_leaky_source_availability": "moderate",
            "estimated_certified_supply": "medium",
            "maintenance_timeline_coverage": "broad",
        },
        {
            "repo_id": "itsdangerous",
            "history_depth": "medium",
            "issue_pr_quality": "moderate",
            "test_suite_stability": "high",
            "dependency_environment_complexity": "low",
            "api_task_diversity": "low",
            "likely_non_leaky_source_availability": "moderate",
            "estimated_certified_supply": "low",
            "maintenance_timeline_coverage": "medium",
        },
        {
            "repo_id": "rich",
            "history_depth": "high",
            "issue_pr_quality": "high",
            "test_suite_stability": "medium",
            "dependency_environment_complexity": "medium_high",
            "api_task_diversity": "high",
            "likely_non_leaky_source_availability": "high",
            "estimated_certified_supply": "high",
            "maintenance_timeline_coverage": "broad",
        },
        {
            "repo_id": "requests",
            "history_depth": "high",
            "issue_pr_quality": "high",
            "test_suite_stability": "medium",
            "dependency_environment_complexity": "medium_high",
            "api_task_diversity": "medium",
            "likely_non_leaky_source_availability": "high",
            "estimated_certified_supply": "medium",
            "maintenance_timeline_coverage": "broad",
        },
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "status": "contingency_screen_completed" if below_minimum else "contingency_screen_skipped_minimum_reached",
        "triggered_by_repos_below_minimum": below_minimum,
        "screened_repositories": candidates if below_minimum else [],
        "recommendation_category": "consider_third_repo_in_coordinating_session" if below_minimum else "keep_two_repo_path",
        "paid_acut_calls_made": False,
        "followup_runbook_written_by_worker": False,
    }
    write_json(OUTPUTS["contingency_screen"], payload)
    write_text(REPORTS["contingency_screen"], contingency_report(payload))
    write_process_report()
    return payload


def final_decision() -> dict[str, Any]:
    if not output_path("contingency_screen").exists():
        contingency_screen()
    expanded = read_json(OUTPUTS["expanded_supply"], default={}) or {}
    support = read_json(OUTPUTS["split_support"], default={}) or split_support()
    statement_review = read_json(OUTPUTS["statement_generation_review"], default={}) or {}
    counts = expanded.get("counts_by_repo", {})
    attrs_met = bool((counts.get("attrs") or {}).get("minimum_target_met"))
    boltons_met = bool((counts.get("boltons") or {}).get("minimum_target_met"))
    if attrs_met and boltons_met and support.get("local_bakeoff_rerun_meaningful"):
        decision = "expanded_supply_ready_for_local_bakeoff"
    elif attrs_met and boltons_met:
        decision = "keep_stratified_mainline_more_local_supply_needed"
    elif read_json(OUTPUTS["contingency_screen"], default={}).get("triggered_by_repos_below_minimum"):
        decision = "existing_repos_supply_exhausted_screen_new_repo"
    else:
        decision = "blocked_with_precise_reason"
    boundary_checks = {
        "new_paid_acut_calls_made": False,
        "new_paid_task_solving_calls_made": False,
        "new_paid_llm_statement_calls_made": False,
        "endpoint_rule_satisfied_if_paid_llm_used": statement_review.get("endpoint_rule_satisfied_if_paid_llm_used"),
        "raw_artifacts_committed": False,
        "followup_runbook_written_by_worker": False,
        "disallowed_claims_made": [],
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "decision": decision,
        "status": "two_repo_supply_expansion_completed",
        "answers": {
            "RQ1_attrs_reached_30": attrs_met,
            "RQ2_boltons_reached_30": boltons_met,
            "RQ3_depletion_gate_if_not": depletion_summary(counts, read_json(OUTPUTS["certification_attempts"], default={}) or {}),
            "RQ4_statement_generation_review": {
                "ran": False,
                "status": statement_review.get("status"),
                "endpoint_compliant": statement_review.get("endpoint_rule_satisfied_if_paid_llm_used"),
                "reason": statement_review.get("blocker") or "not needed for statement-ready promoted tasks",
            },
            "RQ5_expanded_local_supply_sufficient_for_stable_local_bakeoff": bool(support.get("local_bakeoff_rerun_meaningful")),
            "RQ6_any_design_beat_simple_stratified": False,
            "RQ7_readiness": "keep mining/screening locally" if decision != "expanded_supply_ready_for_local_bakeoff" else "ready for local bakeoff planning, not paid replication",
        },
        "counts_by_repo": counts,
        "boundary_checks": boundary_checks,
        "claims": [
            "two_repo_supply_expansion_completed",
            "paid_replication_not_run",
            expanded.get("expanded_supply_status", "expanded_supply_below_minimum"),
        ],
    }
    write_json(OUTPUTS["decision"], payload)
    write_text(REPORTS["decision"], decision_report(payload))
    write_process_report()
    return payload


def depletion_summary(counts: dict[str, Any], attempts: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for repo_id in TARGET_REPOS:
        if (counts.get(repo_id) or {}).get("minimum_target_met"):
            out[repo_id] = "minimum reached"
            continue
        summary = (attempts.get("summary_by_repo") or {}).get(repo_id, {})
        failure_counts = summary.get("first_failing_gate_counts") or {}
        dominant = max(failure_counts.items(), key=lambda item: item[1])[0] if failure_counts else "raw_or_context_supply"
        out[repo_id] = f"below minimum; dominant observed gate: {dominant}"
    return out


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    if not rows:
        return ["_None._"]
    lines = ["| " + " | ".join(label for _, label in columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return lines


def existing_inventory_report(payload: dict[str, Any], duplicate: dict[str, Any]) -> str:
    rows = [
        {"repo_id": repo, **counts}
        for repo, counts in sorted(
            {
                repo_id: {
                    "tasks": sum(1 for row in payload["rows"] if row["repo_id"] == repo_id),
                    "eligible_without_paid_outcome": sum(1 for row in payload["rows"] if row["repo_id"] == repo_id and row["eligible_without_paid_outcome"]),
                    "paid_cells": sum(1 for row in payload["rows"] if row["repo_id"] == repo_id and row["historical_paid_cells_present"]),
                }
                for repo_id in TARGET_REPOS
            }.items()
        )
    ]
    return "\n".join(
        [
            "# Two-Repo Existing Supply Inventory",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            *markdown_table(rows, [("repo_id", "Repo"), ("tasks", "Tasks"), ("eligible_without_paid_outcome", "Eligible without paid outcome"), ("paid_cells", "Historical paid cells")]),
            "",
            f"Seen task ids indexed: `{len(duplicate['seen_task_ids'])}`.",
            f"Seen target commits indexed: `{len(duplicate['seen_target_commits'])}`.",
            "Hidden oracle material, raw transcripts, raw prompts, and raw completions were excluded.",
        ]
    )


def mining_plan_report(payload: dict[str, Any]) -> str:
    rows = [{"repo_id": repo, **quota} for repo, quota in sorted(payload["quotas"].items())]
    return "\n".join(
        [
            "# Two-Repo Supply Mining Plan",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            *markdown_table(
                rows,
                [
                    ("repo_id", "Repo"),
                    ("current_eligible", "Current"),
                    ("minimum_new_certified_needed", "Min New"),
                    ("stretch_new_certified_needed", "Stretch New"),
                    ("raw_candidate_floor", "Raw Floor"),
                    ("local_certification_attempt_soft_cap", "Cert Cap"),
                ],
            ),
            "",
            "New repository selection remains contingency-only.",
        ]
    )


def raw_candidates_report(payload: dict[str, Any]) -> str:
    rows = [{"repo_id": repo, **summary} for repo, summary in sorted(payload["summary_by_repo"].items())]
    return "\n".join(
        [
            "# Two-Repo Raw Candidates",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            *markdown_table(
                rows,
                [
                    ("repo_id", "Repo"),
                    ("anchors_scanned", "Anchors"),
                    ("raw_candidate_count", "Raw Candidates"),
                    ("selected_for_source_context_count", "Selected"),
                    ("duplicate_or_outcome_seen_count", "Duplicate/Seen"),
                    ("raw_candidate_floor_met", "Floor Met"),
                ],
            ),
            "",
            "Only diff digests and bounded size summaries were committed.",
        ]
    )


def source_contexts_report(payload: dict[str, Any]) -> str:
    rows = []
    for repo, summary in sorted(payload["summary_by_repo"].items()):
        row = {"repo_id": repo, "source_context_count": summary["source_context_count"]}
        row.update(summary["source_context_status_counts"])
        rows.append(row)
    return "\n".join(
        [
            "# Two-Repo Source Contexts",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            *markdown_table(
                rows,
                [
                    ("repo_id", "Repo"),
                    ("source_context_count", "Contexts"),
                    ("non_leaky_problem_context", "Non-Leaky"),
                    ("diff_assisted_statement_needed", "Diff Assisted"),
                    ("commit_message_only_source", "Commit Only"),
                ],
            ),
            "",
            "Raw GitHub API responses were not committed.",
        ]
    )


def certification_attempts_report(payload: dict[str, Any]) -> str:
    rows = [{"repo_id": repo, **summary} for repo, summary in sorted(payload["summary_by_repo"].items())]
    return "\n".join(
        [
            "# Two-Repo Certification Attempts",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            *markdown_table(
                rows,
                [
                    ("repo_id", "Repo"),
                    ("attempt_count", "Attempts"),
                    ("ready_count", "Ready"),
                    ("needs_endpoint_statement_generation_review_count", "Needs Endpoint"),
                ],
            ),
            "",
            "Certification was local only. Paid ACUT task-solving calls were not run.",
        ]
    )


def statement_packets_report(payload: dict[str, Any]) -> str:
    rows = [{"repo_id": repo, **summary} for repo, summary in sorted(payload["summary_by_repo"].items())]
    return "\n".join(
        [
            "# Two-Repo Statement Packets",
            "",
            f"Generated: `{payload['generated_at']}`.",
            f"Packets: `{payload['packet_count']}`.",
            "",
            *markdown_table(
                rows,
                [
                    ("repo_id", "Repo"),
                    ("not_needed_public_context_accepted", "Accepted Public Context"),
                    ("endpoint_generation_or_review_needed", "Endpoint Needed"),
                ],
            ),
            "",
            "Diff-assisted generation is allowed only if a final statement passes leakage review.",
        ]
    )


def eligibility_audit_report(payload: dict[str, Any]) -> str:
    rows = [{"repo_id": repo, **counts} for repo, counts in sorted(payload["counts_by_repo"].items())]
    return "\n".join(
        [
            "# Two-Repo Eligibility Audit",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            *markdown_table(
                rows,
                [
                    ("repo_id", "Repo"),
                    ("existing_eligible", "Existing"),
                    ("new_eligible", "New"),
                    ("total_eligible", "Total"),
                    ("minimum_target_met", "Minimum Met"),
                ],
            ),
            "",
            "No outcome-seen target commit was promoted as new supply.",
        ]
    )


def expanded_supply_report(payload: dict[str, Any]) -> str:
    rows = [{"repo_id": repo, **counts} for repo, counts in sorted(payload["counts_by_repo"].items())]
    return "\n".join(
        [
            "# Two-Repo Expanded Supply",
            "",
            f"Generated: `{payload['generated_at']}`.",
            f"Status: `{payload['expanded_supply_status']}`.",
            "",
            *markdown_table(
                rows,
                [
                    ("repo_id", "Repo"),
                    ("existing_eligible", "Existing"),
                    ("new_eligible", "New"),
                    ("total_eligible", "Total"),
                    ("minimum_target_met", "Minimum Met"),
                    ("stretch_target_met", "Stretch Met"),
                ],
            ),
        ]
    )


def split_support_report(payload: dict[str, Any]) -> str:
    rows = []
    for repo, summary in sorted(payload["by_repo"].items()):
        rows.append(
            {
                "repo_id": repo,
                "per_repo_count": summary["per_repo_count"],
                "pseudo_future_window_count": summary["pseudo_future_window_count"],
                "minimum_per_window_support": summary["minimum_per_window_support"],
                "B_eval_count": summary["eligible_chronological_split_options"]["B_eval_count"],
                "H_future_count": summary["eligible_chronological_split_options"]["H_future_count"],
            }
        )
    return "\n".join(
        [
            "# Two-Repo Split Support",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            *markdown_table(
                rows,
                [
                    ("repo_id", "Repo"),
                    ("per_repo_count", "Count"),
                    ("pseudo_future_window_count", "Windows"),
                    ("minimum_per_window_support", "Min Window"),
                    ("B_eval_count", "B Eval"),
                    ("H_future_count", "H Future"),
                ],
            ),
            "",
            f"Local bakeoff rerun meaningful: `{str(payload['local_bakeoff_rerun_meaningful']).lower()}`.",
            f"Blocker: `{payload.get('local_bakeoff_rerun_blocker') or 'none'}`.",
            "H_future was kept as a validation holdout concept, not a target profile.",
        ]
    )


def local_bakeoff_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Two-Repo Local Bakeoff Rerun",
            "",
            f"Generated: `{payload['generated_at']}`.",
            f"Status: `{payload['status']}`.",
            f"Reason: `{payload['reason']}`.",
            "Paid replication was not run.",
        ]
    )


def contingency_report(payload: dict[str, Any]) -> str:
    rows = payload.get("screened_repositories", [])
    return "\n".join(
        [
            "# Two-Repo Contingency Repository Screen",
            "",
            f"Generated: `{payload['generated_at']}`.",
            f"Status: `{payload['status']}`.",
            f"Triggered by repos below minimum: `{', '.join(payload['triggered_by_repos_below_minimum']) or 'none'}`.",
            "",
            *markdown_table(
                rows,
                [
                    ("repo_id", "Repo"),
                    ("history_depth", "History"),
                    ("issue_pr_quality", "Issue/PR"),
                    ("test_suite_stability", "Tests"),
                    ("dependency_environment_complexity", "Deps"),
                    ("estimated_certified_supply", "Supply"),
                ],
            ),
            "",
            "This is a contingency memo only. No follow-up runbook was drafted.",
        ]
    )


def decision_report(payload: dict[str, Any]) -> str:
    answers = payload["answers"]
    return "\n".join(
        [
            "# Two-Repo Supply Expansion Decision",
            "",
            f"Generated: `{payload['generated_at']}`.",
            f"Decision: `{payload['decision']}`.",
            "",
            f"- RQ1 attrs reached 30: `{str(answers['RQ1_attrs_reached_30']).lower()}`.",
            f"- RQ2 boltons reached 30: `{str(answers['RQ2_boltons_reached_30']).lower()}`.",
            f"- RQ3 depletion: `{answers['RQ3_depletion_gate_if_not']}`.",
            f"- RQ4 statement generation: `{answers['RQ4_statement_generation_review']}`.",
            f"- RQ5 stable local bakeoff supply: `{str(answers['RQ5_expanded_local_supply_sufficient_for_stable_local_bakeoff']).lower()}`.",
            f"- RQ6 design beat stratified: `{str(answers['RQ6_any_design_beat_simple_stratified']).lower()}`.",
            f"- RQ7 readiness: `{answers['RQ7_readiness']}`.",
            "",
            "Boundary checks:",
            f"- New paid ACUT calls made: `{str(payload['boundary_checks']['new_paid_acut_calls_made']).lower()}`.",
            f"- New paid task-solving calls made: `{str(payload['boundary_checks']['new_paid_task_solving_calls_made']).lower()}`.",
            f"- New paid LLM statement calls made: `{str(payload['boundary_checks']['new_paid_llm_statement_calls_made']).lower()}`.",
            f"- Raw artifacts committed: `{str(payload['boundary_checks']['raw_artifacts_committed']).lower()}`.",
            f"- Follow-up runbook written by worker: `{str(payload['boundary_checks']['followup_runbook_written_by_worker']).lower()}`.",
        ]
    )


def write_process_report() -> None:
    lines = [
        "# Phase 1 Two-Repo Supply Expansion Process",
        "",
        f"Run id: `{RUN_ID}`.",
        f"Updated: `{now_utc()}`.",
        "",
        "## Boundary Rules",
        "",
        "- Barcarolle provides clean workspaces, captures diffs, enforces benchmark policy, and verifies separately; it does not reimplement ACUT internals.",
        "- Paid ACUT task-solving and paid replication are disabled for this runbook.",
        "- Paid statement generation, if needed, must use `LLM_BASE_URL` and `LLM_API_KEY`; no local subscription fallback is allowed.",
        "- Hidden oracle material, raw prompts, raw completions, raw ACUT transcripts, solver workspaces, verifier workspaces, and raw diffs are not committed.",
        "- No follow-up runbook is drafted by this worker.",
        "",
        "## Step Ledger",
        "",
    ]
    for number, title, output_key in PROCESS_STEPS:
        path = output_path(output_key) if output_key in OUTPUTS else None
        done = path.exists() if path else False
        status = "done" if done else "pending"
        lines.append(f"- Step {number}: {title} - `{status}`.")
    lines.extend(
        [
            "",
            "## Disallowed Claims",
            "",
            "Not claimed: " + ", ".join(f"`{claim}`" for claim in DISALLOWED_CLAIMS) + ".",
        ]
    )
    write_text(REPORTS["process"], "\n".join(lines))


def run_steps(names: list[str]) -> None:
    mapping = {
        "preflight": preflight,
        "inventory": existing_inventory,
        "mining-plan": mining_plan,
        "raw-candidates": raw_candidates,
        "source-contexts": source_contexts,
        "certification": certification_attempts,
        "statement-packets": statement_packets,
        "statement-review": statement_generation_review,
        "freeze": eligibility_and_freeze,
        "split-support": split_support,
        "local-bakeoff": local_bakeoff_rerun,
        "contingency": contingency_screen,
        "decision": final_decision,
    }
    ordered = [
        "preflight",
        "inventory",
        "mining-plan",
        "raw-candidates",
        "source-contexts",
        "certification",
        "statement-packets",
        "statement-review",
        "freeze",
        "split-support",
        "local-bakeoff",
        "contingency",
        "decision",
    ]
    targets = ordered if names == ["all"] else names
    for name in targets:
        if name not in mapping:
            raise SystemExit(f"unknown step: {name}")
        mapping[name]()


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute the Phase 1 two-repo certified supply expansion runbook.")
    parser.add_argument("steps", nargs="+", help="Step name(s), or all")
    args = parser.parse_args()
    run_steps(args.steps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
