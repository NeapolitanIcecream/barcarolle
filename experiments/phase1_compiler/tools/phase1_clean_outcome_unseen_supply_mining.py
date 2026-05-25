from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase1_future_holdout import parse_task_time, select_cutoff_for_repo, simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
PHASE0_TOOLS = PHASE0_ROOT / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))

import repo_history_pilot  # noqa: E402
import statement_quality  # noqa: E402

DEFAULT_CONFIG = ROOT / "configs" / "phase1_clean_outcome_unseen_supply_mining.yaml"
SECOND_REPO_CONFIG = ROOT / "configs" / "phase1_second_repo_clean_outcome_unseen_supply.yaml"

CORE_CERTIFICATION_GATES = [
    "checkout",
    "oracle_extractable",
    "no_op_fail",
    "reference_pass",
    "known_bad_fail",
    "flakiness_check",
    "scope_clarity_review",
    "cost_boundedness",
    "taxonomy_labelability",
]
PROJECT_CONFIG_FILES = {
    ".travis.yml",
    "appveyor.yml",
    "tox.ini",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "noxfile.py",
    "conftest.py",
}
REPO_OWNER = {
    "attrs": "python-attrs/attrs",
    "boltons": "mahmoud/boltons",
}
SOLUTION_EXPOSURE_SUMMARY_TERMS = [
    "rework",
    "refactor",
    "rename",
    "move ",
    "wrapped ",
    "revert ",
    "polish",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path | str) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != "barcarolle.phase1_clean_outcome_unseen_supply_mining.v1":
        raise ValueError("unexpected clean outcome-unseen supply mining config schema_version")
    config["_path"] = str(path)
    return config


def load_second_repo_config(path: Path = SECOND_REPO_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != "barcarolle.phase1_second_repo_clean_outcome_unseen_supply.v1":
        raise ValueError("unexpected second repo clean supply config schema_version")
    config["_path"] = str(path)
    return config


def artifact_path(config: dict[str, Any], key: str) -> Path:
    raw = config["source_artifacts"][key]
    path = Path(str(raw))
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def result_path(name: str) -> Path:
    return ROOT / "results" / name


def report_path(name: str) -> Path:
    return ROOT / "reports" / name


def configured_output_path(config: dict[str, Any], key: str) -> Path:
    raw = config["output_paths"][key]
    path = Path(str(raw))
    return path if path.is_absolute() else REPO_ROOT / path


def phase0_candidate_path(repo_id: str, suffix: str) -> Path:
    return PHASE0_ROOT / "candidate_sources" / f"{repo_id}_clean_outcome_unseen_supply_{suffix}.jsonl"


def phase0_certified_path(repo_id: str, suffix: str) -> Path:
    return PHASE0_ROOT / "certified_tasks" / f"{repo_id}_clean_outcome_unseen_supply_{suffix}.jsonl"


def second_repo_prefix(config: dict[str, Any], repo_id: str) -> str:
    return str(config["candidate_repos"][repo_id]["candidate_source_prefix"])


def second_repo_candidate_path(config: dict[str, Any], repo_id: str, suffix: str) -> Path:
    return PHASE0_ROOT / "candidate_sources" / f"{second_repo_prefix(config, repo_id)}_{suffix}.jsonl"


def second_repo_certified_path(config: dict[str, Any], repo_id: str, suffix: str) -> Path:
    return PHASE0_ROOT / "certified_tasks" / f"{second_repo_prefix(config, repo_id)}_{suffix}.jsonl"


def repo_from_task_id(task_id: str) -> str:
    return task_id.split("__", 1)[0] if "__" in task_id else "unknown"


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def unique_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def extension_task_id(repo_id: str, *, existing_task_ids: set[str]) -> str:
    index = 1
    while True:
        candidate = f"{repo_id}__clean_ext__{index:03d}"
        if candidate not in existing_task_ids:
            return candidate
        index += 1


def existing_task_ids() -> set[str]:
    ids: set[str] = set()
    for path in list((PHASE0_ROOT / "candidate_sources").glob("*.jsonl")) + list((PHASE0_ROOT / "certified_tasks").glob("*.jsonl")):
        for row in read_jsonl(path):
            if row.get("task_id"):
                ids.add(str(row["task_id"]))
            if row.get("original_task_id"):
                ids.add(str(row["original_task_id"]))
    for path in (ROOT / "results").glob("phase1_*supply*overlay.json"):
        try:
            payload = read_json(path)
        except json.JSONDecodeError:
            continue
        for task_id in payload.get("promoted_task_ids", []):
            ids.add(str(task_id))
        for row in payload.get("promoted_tasks", []):
            if row.get("task_id"):
                ids.add(str(row["task_id"]))
    return ids


def load_outcome_seen_task_ids(config: dict[str, Any]) -> set[str]:
    task_ids: set[str] = set()
    scorecard_path = artifact_path(config, "workspace_scorecard")
    if scorecard_path.exists():
        scorecard = read_json(scorecard_path)
        task_ids.update(str(cell["task_id"]) for cell in scorecard.get("cells", []) if cell.get("task_id"))
    for score_table in (PHASE0_ROOT / "results").glob("*_score_table.csv"):
        for row in read_csv(score_table):
            if row.get("task_id"):
                task_ids.add(str(row["task_id"]))
    return task_ids


def task_commit_index() -> dict[str, str]:
    index: dict[str, str] = {}
    paths = list((PHASE0_ROOT / "candidate_sources").glob("*.jsonl")) + list((PHASE0_ROOT / "certified_tasks").glob("*.jsonl"))
    for path in paths:
        for row in read_jsonl(path):
            if row.get("task_id") and row.get("target_commit"):
                index[str(row["task_id"])] = str(row["target_commit"])
            if row.get("original_task_id") and row.get("target_commit"):
                index[str(row["original_task_id"])] = str(row["target_commit"])
    return index


def load_outcome_seen_target_commits(config: dict[str, Any]) -> set[str]:
    seen_task_ids = load_outcome_seen_task_ids(config)
    commit_by_task = task_commit_index()
    commits = {commit_by_task[task_id] for task_id in seen_task_ids if task_id in commit_by_task}
    for score_table in (PHASE0_ROOT / "results").glob("*_score_table.csv"):
        for row in read_csv(score_table):
            if row.get("target_commit"):
                commits.add(str(row["target_commit"]))
    return commits


def row_by_task(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["task_id"]): row for row in rows if row.get("task_id")}


def load_repo_rows(repo_id: str) -> dict[str, dict[str, Any]]:
    candidates = row_by_task(read_jsonl(PHASE0_ROOT / "candidate_sources" / f"{repo_id}_candidates.jsonl"))
    certified = row_by_task(read_jsonl(PHASE0_ROOT / "certified_tasks" / f"{repo_id}_certified_tasks.jsonl"))
    near = row_by_task(read_jsonl(PHASE0_ROOT / "certified_tasks" / f"{repo_id}_near_certified_tasks.jsonl"))
    statements = row_by_task(read_jsonl(PHASE0_ROOT / "certified_tasks" / f"{repo_id}_task_statements.jsonl"))
    contexts = row_by_task(read_jsonl(PHASE0_ROOT / "candidate_sources" / f"{repo_id}_source_context.jsonl"))
    hardening_rows = row_by_task(read_json(ROOT / "results" / "phase1_hardened_certification_overlay.json").get("tasks", []))

    ids = set(candidates) | set(certified) | set(near) | set(statements) | set(contexts) | set(hardening_rows)
    rows: dict[str, dict[str, Any]] = {}
    for task_id in sorted(ids):
        row: dict[str, Any] = {"task_id": task_id, "repo_id": repo_id}
        row.update(candidates.get(task_id, {}))
        row.update(near.get(task_id, {}))
        row.update(certified.get(task_id, {}))
        if task_id in statements:
            row["statement"] = statements[task_id]
        if task_id in contexts:
            row["source_context"] = contexts[task_id]
        if task_id in hardening_rows:
            row["hardening"] = hardening_rows[task_id]
            row["hardened_reject_reasons"] = hardening_rows[task_id].get("hardened_reject_reasons", [])
        rows[task_id] = row
    return rows


def prior_promoted_tasks(config: dict[str, Any]) -> list[dict[str, Any]]:
    overlay = read_json(Path(REPO_ROOT / config["target"]["prior_clean_supply_overlay"]))
    rows_by_repo = {repo_id: load_repo_rows(repo_id) for repo_id in {repo_from_task_id(task_id) for ids in overlay["promoted_by_split"].values() for task_id in ids}}
    tasks: list[dict[str, Any]] = []
    for split, task_ids in overlay["promoted_by_split"].items():
        for task_id in task_ids:
            repo_id = repo_from_task_id(str(task_id))
            source = rows_by_repo.get(repo_id, {}).get(str(task_id), {})
            tasks.append(
                {
                    "task_id": str(task_id),
                    "original_task_id": str(task_id),
                    "repo_id": repo_id,
                    "split": str(split),
                    "task_time": source.get("task_time"),
                    "target_commit": source.get("target_commit"),
                    "module_or_package": source.get("module_or_package", []),
                    "original_hardening_status": (source.get("hardening") or {}).get("hardened_status"),
                    "original_hardening_reject_reasons": (source.get("hardening") or {}).get("hardened_reject_reasons", []),
                    "source": "prior_clean_supply_overlay",
                    "clean_overlay_promotion_decision": "prior_promoted_clean_supply",
                }
            )
    return tasks


def issue_numbers_from_subject(subject: str) -> list[int]:
    numbers: list[int] = []
    for match in re.finditer(r"(?:fixes?|closes?|resolves?)\s+#(\d+)|#(\d+)", subject, flags=re.IGNORECASE):
        raw = match.group(1) or match.group(2)
        if raw:
            numbers.append(int(raw))
    return list(dict.fromkeys(numbers))


def issue_numbers_from_text(text: str) -> list[int]:
    numbers = issue_numbers_from_subject(text)
    for match in re.finditer(r"\bissue\s+(\d+)", text, flags=re.IGNORECASE):
        numbers.append(int(match.group(1)))
    return list(dict.fromkeys(numbers))


def run_gh_issue_lookup(repo_id: str, number: int) -> dict[str, Any] | None:
    owner_repo = REPO_OWNER.get(repo_id)
    if not owner_repo:
        return None
    proc = subprocess.run(
        ["gh", "api", f"repos/{owner_repo}/issues/{number}", "--jq", "{number,title,body:(.body // \"\"),state}"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        return None
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    title = " ".join(str(payload.get("title") or "").split())
    body = statement_quality.sanitize_public_body_summary(payload.get("body"))
    if not title:
        return None
    return {
        "ref": f"issue:{number}",
        "classification": "problem_context",
        "summary": title,
        "body_summary": body,
        "state": payload.get("state"),
    }


def run_gh_issue_only_lookup(repo_id: str, number: int) -> dict[str, Any] | None:
    owner_repo = REPO_OWNER.get(repo_id)
    if not owner_repo:
        return None
    proc = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{owner_repo}/issues/{number}",
            "--jq",
            "{number,title,body:(.body // \"\"),state,is_pull_request:(.pull_request != null)}",
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        return None
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    if payload.get("is_pull_request"):
        return None
    title = " ".join(str(payload.get("title") or "").split())
    body = statement_quality.sanitize_public_body_summary(payload.get("body"))
    if not title:
        return None
    return {
        "ref": f"issue:{number}",
        "classification": "problem_context",
        "summary": title,
        "body_summary": body,
        "state": payload.get("state"),
    }


def context_for_candidate(row: dict[str, Any]) -> dict[str, Any]:
    source_context = row.get("source_context") or {}
    if source_context.get("classification") == "problem_context" and not str(source_context.get("ref", "")).startswith("commit:"):
        return {
            "ref": source_context.get("ref"),
            "classification": "problem_context",
            "summary": source_context.get("summary"),
            "body_summary": source_context.get("body_summary", ""),
        }
    statement = row.get("statement") or {}
    allowed = [str(ref) for ref in statement.get("allowed_context_refs", []) or row.get("allowed_context_refs", [])]
    if allowed:
        return {
            "ref": allowed[0],
            "classification": "problem_context",
            "summary": row.get("subject"),
            "body_summary": "",
        }
    for number in issue_numbers_from_subject(str(row.get("subject") or "")):
        context = run_gh_issue_lookup(str(row.get("repo_id") or repo_from_task_id(str(row.get("task_id", "")))), number)
        if context:
            return context
    return {
        "ref": f"commit:{row.get('target_commit', '')}",
        "classification": "diagnostic_only_context",
        "summary": row.get("subject") or "commit-message fallback",
        "body_summary": "",
    }


def project_or_config_heavy(row: dict[str, Any]) -> bool:
    paths = [str(path) for path in row.get("changed_files", [])]
    project_paths = [
        path
        for path in paths
        if path in PROJECT_CONFIG_FILES or path.startswith((".github/", "docs/", "requirements/")) or path.endswith((".rst", ".md"))
    ]
    subject = str(row.get("subject") or "").lower()
    return len(project_paths) >= 3 or "tox" in subject or "gh action" in subject or "github action" in subject


def project_or_docs_only(row: dict[str, Any]) -> bool:
    return bool(row.get("changed_files")) and not bool(row.get("code_files"))


def first_failed_core_gate(row: dict[str, Any]) -> str:
    gates = row.get("gates") or {}
    for gate in CORE_CERTIFICATION_GATES:
        if gates.get(gate) != "pass":
            return gate
    return ""


def split_for_candidate(row: dict[str, Any], config: dict[str, Any]) -> str:
    cutoff_hint = parse_task_time(str(config["mining"]["prefer_candidates_before_task_time"]))
    task_time = parse_task_time(str(row["task_time"]))
    return "B_real" if task_time < cutoff_hint else "W_real"


def source_status_from_context(context: dict[str, Any]) -> str:
    ref = str(context.get("ref") or "")
    if context.get("classification") != "problem_context":
        return "commit_message_only_source" if ref.startswith("commit:") else "non_leaky_problem_context_missing"
    if ref.startswith(("issue:", "pr:", "issue_comment:", "pr_comment:", "manual:", "customer:")):
        return "non_leaky_problem_context"
    return "commit_message_only_source" if ref.startswith("commit:") else "non_leaky_problem_context_missing"


def review_candidate(
    row: dict[str, Any],
    *,
    extension_task_id: str,
    context: dict[str, Any],
    outcome_seen_task_ids: set[str],
    outcome_seen_target_commits: set[str],
) -> dict[str, Any]:
    blockers: list[str] = []
    task_id = str(row["task_id"])
    target_commit = str(row.get("target_commit") or "")
    if task_id in outcome_seen_task_ids:
        blockers.append("previous_acut_outcome_seen")
    if target_commit and target_commit in outcome_seen_target_commits:
        blockers.append("previous_acut_target_commit_seen")
    source_status = source_status_from_context(context)
    if source_status == "commit_message_only_source":
        blockers.append("commit_message_only_source")
    elif source_status != "non_leaky_problem_context":
        blockers.append("non_leaky_problem_context_missing")
    quality = statement_quality.statement_quality_for_context(context, row)
    if quality["statement_quality_gate"] == "material_risk":
        blockers.append("statement_quality_risk")
    reject_reasons = set(str(reason) for reason in row.get("hardened_reject_reasons", []))
    if "solution_exposure_risk" in reject_reasons:
        blockers.append("solution_exposure_risk")
    if project_or_docs_only(row):
        blockers.append("project_or_docs_only_change")
    if project_or_config_heavy(row):
        blockers.append("scope_context_project_heavy_or_ambiguous")
    failed_core_gate = first_failed_core_gate(row)
    if failed_core_gate:
        blockers.append(f"local_certification_gate_failed:{failed_core_gate}")
    if row.get("candidate_filter_status") == "rejected":
        blockers.append("candidate_filter_rejected")

    blockers = unique_preserve(blockers)
    hard_reject = [
        blocker
        for blocker in blockers
        if blocker != "scope_context_project_heavy_or_ambiguous"
    ]
    if hard_reject:
        decision = "reject_for_clean_holdout"
    elif blockers:
        decision = "keep_manual_review_required"
    else:
        decision = "promote_to_clean_benchmark_candidate"
    clean_gates = dict(row.get("gates", {}))
    if source_status == "non_leaky_problem_context" and "scope_context_project_heavy_or_ambiguous" not in blockers:
        clean_gates["ambiguity_review"] = "pass"
    if source_status == "non_leaky_problem_context" and "solution_exposure_risk" not in blockers:
        clean_gates["solution_leakage_review"] = "pass"
    if quality["statement_quality_gate"] == "material_risk":
        clean_gates["ambiguity_review"] = "fail"
    clean_first_failing_gate = ""
    for gate, status in clean_gates.items():
        if status != "pass":
            clean_first_failing_gate = gate
            break
    return {
        "schema_version": "barcarolle.phase1.clean_outcome_unseen_supply_review.v1",
        "task_id": extension_task_id,
        "original_task_id": task_id,
        "repo_id": row.get("repo_id") or repo_from_task_id(task_id),
        "split": row.get("split", "unknown"),
        "task_time": row.get("task_time"),
        "base_commit": row.get("base_commit"),
        "target_commit": target_commit,
        "subject": row.get("subject"),
        "module_or_package": row.get("module_or_package", []),
        "changed_files": row.get("changed_files", []),
        "test_files": row.get("test_files", []),
        "original_hardening_status": (row.get("hardening") or {}).get("hardened_status"),
        "original_hardening_reject_reasons": sorted(reject_reasons),
        "source_context_status": source_status,
        "allowed_context_refs": [context["ref"]] if source_status == "non_leaky_problem_context" else [],
        "sanitized_context": context,
        "statement_quality": quality,
        "local_certification_gates": row.get("gates", {}),
        "clean_overlay_certification_gates": clean_gates,
        "clean_overlay_first_failing_gate": clean_first_failing_gate,
        "local_command_records": row.get("commands", []),
        "promotion_decision": decision,
        "promotion_blockers": blockers,
        "promotion_rationale": "source_context_repaired_with_sanitized_public_issue" if decision == "promote_to_clean_benchmark_candidate" else "",
        "predictive_validity_established": False,
    }


def second_repo_pilot_config(config: dict[str, Any], repo_id: str) -> repo_history_pilot.PilotConfig:
    repo = config["candidate_repos"][repo_id]
    local_repo = Path(str(repo["local_repo"]))
    if not local_repo.is_absolute():
        local_repo = REPO_ROOT / local_repo
    return repo_history_pilot.PilotConfig(
        repo_id=repo_id,
        repo_url=str(repo["repo_url"]),
        local_repo=local_repo,
        command_template=str(repo["test_environment"]["command_template"]),
        certification_attempts=int(config["mining"]["max_certification_attempts"]),
        pilot_certified_min=int(config["minimum_clean_split"]["B_eval"]) + int(config["minimum_clean_split"]["H_future"]),
        benchmark_grade_min=int(config["preferred_clean_split"]["B_eval"]) + int(config["preferred_clean_split"]["H_future"]),
        result_prefix=f"phase1_second_repo_clean_supply_{repo_id}",
        claim_scope=str(config["claim_scope"]),
    )


def second_repo_order(config: dict[str, Any]) -> list[str]:
    return [str(config["primary_candidate_repo"]), *[str(repo_id) for repo_id in config.get("fallback_candidate_repos", [])]]


def source_context_rows_for_candidates(
    pilot_config: repo_history_pilot.PilotConfig,
    candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    statement_by_task: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        pr_refs = repo_history_pilot.github_pr_refs(pilot_config, str(candidate["target_commit"]))
        issue_refs: list[dict[str, Any]] = []
        for ref in pr_refs:
            text = f"{ref.get('summary', '')} {ref.get('body_summary', '')}"
            for number in issue_numbers_from_text(text):
                issue_ref = run_gh_issue_only_lookup(pilot_config.repo_id, number)
                if issue_ref:
                    issue_refs.append(issue_ref)
        refs = issue_refs or pr_refs
        if not refs:
            refs = [repo_history_pilot.commit_context_ref(pilot_config, candidate)]
        for ref in refs:
            ref = dict(ref)
            ref["schema_version"] = "barcarolle.phase1.second_repo_clean_supply_source_context.v1"
            ref["repo_id"] = pilot_config.repo_id
            ref["task_id"] = candidate["task_id"]
            ref["target_commit"] = candidate["target_commit"]
            ref["statement_quality"] = statement_quality.statement_quality_for_context(ref, candidate)
            rows.append(ref)
        allowed_refs = repo_history_pilot.allowed_context_refs(refs)
        quality = statement_quality.statement_quality_for_context(refs[0], candidate)
        statement_by_task[str(candidate["task_id"])] = {
            "schema_version": "barcarolle.repo_history_statement.v1",
            "task_id": candidate["task_id"],
            "repo_id": pilot_config.repo_id,
            "base_commit": candidate["base_commit"],
            "target_commit": candidate["target_commit"],
            "solver_facing_statement": repo_history_pilot.solver_statement(candidate, refs),
            "scope_boundaries": (
                f"Modify only implementation files needed for this {pilot_config.repo_id} behavior; "
                "do not edit tests or generated metadata."
            ),
            "allowed_context_refs": allowed_refs,
            "excluded_context_refs": [ref["ref"] for ref in refs if ref["classification"] != "problem_context"],
            "oracle_refs": candidate["test_files"],
            "harness_test_command": pilot_config.command_template,
            "statement_quality": quality,
            "statement_review_status": "reviewed" if allowed_refs else "near_certified_context_missing",
            "source_context_status": "non_leaky_context_found" if allowed_refs else "no_non_leaky_source_context",
        }
        if quality["statement_quality_gate"] == "material_risk":
            statement_by_task[str(candidate["task_id"])]["statement_review_status"] = "statement_quality_risk"
    return rows, statement_by_task


def selected_context_for_task(contexts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in contexts:
        grouped.setdefault(str(row.get("task_id")), []).append(row)
    selected: dict[str, dict[str, Any]] = {}
    for task_id, rows in grouped.items():
        problem = [row for row in rows if row.get("classification") == "problem_context"]
        selected[task_id] = problem[0] if problem else rows[0]
    return selected


def context_has_solution_exposure(context: dict[str, Any]) -> bool:
    summary = str(context.get("summary") or "").lower()
    body = str(context.get("body_summary") or "").lower()
    if summary.startswith(("fix ", "fixed ", "don't ", "dont ", "add ")):
        return any(term in body for term in SOLUTION_EXPOSURE_SUMMARY_TERMS)
    combined = f"{summary} {body}"
    return any(term in combined for term in SOLUTION_EXPOSURE_SUMMARY_TERMS)


def review_second_repo_candidate(
    row: dict[str, Any],
    *,
    context: dict[str, Any],
    outcome_seen_task_ids: set[str],
    outcome_seen_target_commits: set[str],
) -> dict[str, Any]:
    task_id = str(row["task_id"])
    target_commit = str(row.get("target_commit") or "")
    blockers: list[str] = []
    if task_id in outcome_seen_task_ids:
        blockers.append("previous_acut_outcome_seen")
    if target_commit and target_commit in outcome_seen_target_commits:
        blockers.append("previous_acut_target_commit_seen")
    source_status = source_status_from_context(context)
    if source_status == "commit_message_only_source":
        blockers.append("commit_message_only_source")
    elif source_status != "non_leaky_problem_context":
        blockers.append("non_leaky_problem_context_missing")
    quality = statement_quality.statement_quality_for_context(context, row)
    if quality["statement_quality_gate"] == "material_risk":
        blockers.append("statement_quality_risk")
    if row.get("status") != "certified":
        first_gate = str(row.get("first_failing_gate") or "unknown")
        blockers.append(f"local_certification_gate_failed:{first_gate}")
    if project_or_docs_only(row):
        blockers.append("project_or_docs_only_change")
    if project_or_config_heavy(row):
        blockers.append("scope_context_project_heavy_or_ambiguous")
    if context_has_solution_exposure(context):
        blockers.append("solution_exposure_risk")

    blockers = unique_preserve(blockers)
    decision = "promote_to_clean_benchmark_candidate" if not blockers else "reject_for_clean_holdout"
    gates = dict(row.get("gates", {}))
    if source_status == "non_leaky_problem_context" and "scope_context_project_heavy_or_ambiguous" not in blockers:
        gates["ambiguity_review"] = "pass"
    if source_status == "non_leaky_problem_context" and "solution_exposure_risk" not in blockers:
        gates["solution_leakage_review"] = "pass"
    if quality["statement_quality_gate"] == "material_risk":
        gates["ambiguity_review"] = "fail"
    clean_first_failing_gate = ""
    for gate, status in gates.items():
        if status != "pass":
            clean_first_failing_gate = gate
            break
    return {
        "schema_version": "barcarolle.phase1.second_repo_clean_supply_review.v1",
        "task_id": task_id,
        "repo_id": row.get("repo_id"),
        "split": row.get("split", "candidate"),
        "task_time": row.get("task_time"),
        "base_commit": row.get("base_commit"),
        "target_commit": target_commit,
        "target_commit_unseen": target_commit not in outcome_seen_target_commits,
        "subject": row.get("subject"),
        "module_or_package": row.get("module_or_package", []),
        "changed_files": row.get("changed_files", []),
        "test_files": row.get("test_files", []),
        "candidate_filter_status": row.get("candidate_filter_status"),
        "source_context_status": source_status,
        "allowed_context_refs": [context["ref"]] if source_status == "non_leaky_problem_context" else [],
        "sanitized_context": context,
        "statement_quality": quality,
        "original_local_certification_status": row.get("status"),
        "local_certification_gates": row.get("gates", {}),
        "clean_overlay_certification_gates": gates,
        "clean_overlay_first_failing_gate": clean_first_failing_gate,
        "local_command_records": row.get("commands", []),
        "promotion_decision": decision,
        "promotion_blockers": blockers,
        "promotion_rationale": "local_certification_and_non_leaky_public_context" if decision == "promote_to_clean_benchmark_candidate" else "",
        "predictive_validity_established": False,
    }


def cutoff_feasibility_for_tasks(config: dict[str, Any], tasks: list[dict[str, Any]]) -> dict[str, Any]:
    minimum = config["target"]["required_future_holdout_minimum"]
    future_config = simple_yaml_load(artifact_path(config, "future_holdout_config"))
    embargo_gap_days = int(future_config["cutoff_policy"]["embargo_gap_days"])
    by_repo: dict[str, list[dict[str, Any]]] = {}
    for row in tasks:
        if row.get("task_time"):
            by_repo.setdefault(str(row["repo_id"]), []).append(row)
    plans = {}
    for repo_id, rows in by_repo.items():
        plans[repo_id] = select_cutoff_for_repo(
            repo_id,
            rows,
            embargo_gap_days=embargo_gap_days,
            preferred_b=int(future_config["clean_split_minimums"]["preferred_b_eval_tasks_per_repo"]),
            preferred_h=int(future_config["clean_split_minimums"]["preferred_h_future_tasks_per_repo"]),
            minimum_b=int(minimum["b_eval_tasks_per_repo"]),
            minimum_h=int(minimum["h_future_tasks_per_repo"]),
            model_snapshot_date=None,
            model_snapshot_status="unknown",
        )
    return plans


def first_filter_counts(anchors: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("status") or "unknown") for row in anchors)
    candidate_filter_counts = Counter(str(row.get("candidate_filter_status") or "unknown") for row in anchors)
    reject_counts: Counter[str] = Counter()
    for row in anchors:
        reject_counts.update(str(reason) for reason in row.get("reject_reasons", []) if reason)
    return {
        "anchor_status_counts": dict(sorted(status_counts.items())),
        "candidate_filter_status_counts": dict(sorted(candidate_filter_counts.items())),
        "reject_reason_counts": dict(sorted(reject_counts.items())),
    }


def second_repo_inventory_payload(
    config: dict[str, Any],
    *,
    repo_id: str,
    anchors: list[dict[str, Any]] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    contexts: list[dict[str, Any]] | None = None,
    reviews: list[dict[str, Any]] | None = None,
    certification_rows: list[dict[str, Any]] | None = None,
    prior_inventory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidates = candidates if candidates is not None else read_jsonl(second_repo_candidate_path(config, repo_id, "candidates"))
    contexts = contexts if contexts is not None else read_jsonl(second_repo_candidate_path(config, repo_id, "source_context"))
    reviews = reviews or []
    certification_rows = certification_rows or []
    if anchors is None:
        anchors_scanned = int((prior_inventory or {}).get("anchors_scanned") or 0)
        filter_counts = (prior_inventory or {}).get("first_filter_counts") or first_filter_counts([])
    else:
        anchors_scanned = len(anchors)
        filter_counts = first_filter_counts(anchors)
    context_status_counts = Counter(source_status_from_context(row) for row in contexts)
    promotion_counts = Counter(row.get("promotion_decision", "not_reviewed") for row in reviews)
    blocker_counts: Counter[str] = Counter()
    for row in reviews:
        blocker_counts.update(row.get("promotion_blockers", []))
    certification_counts = Counter(row.get("status", "not_attempted") for row in certification_rows)
    promoted = [row for row in reviews if row.get("promotion_decision") == "promote_to_clean_benchmark_candidate"]
    return {
        "schema_version": "barcarolle.phase1.second_repo_clean_supply_candidate_inventory.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "repo_id": repo_id,
        "repo_url": config["candidate_repos"][repo_id]["repo_url"],
        "local_repo": config["candidate_repos"][repo_id]["local_repo"],
        "anchors_scanned": anchors_scanned,
        "max_history_anchors": int(config["mining"]["max_history_anchors"]),
        "candidate_count": len(candidates),
        "source_context_count": len(contexts),
        "first_filter_counts": filter_counts,
        "source_context_status_counts": dict(sorted(context_status_counts.items())),
        "local_certification_attempt_count": len(certification_rows),
        "local_certification_status_counts": dict(sorted(certification_counts.items())),
        "promotion_decision_counts": dict(sorted(promotion_counts.items())),
        "promotion_blocker_counts": dict(sorted(blocker_counts.items())),
        "promoted_task_ids": [str(row["task_id"]) for row in promoted],
        "paid_llm_calls_made": False,
        "paid_acut_calls_made": False,
        "predictive_validity_established": False,
    }


def second_repo_inventory_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Second-Repo Clean Supply Candidate Inventory",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Repo: `{payload['repo_id']}`.",
            f"- Anchors scanned: `{payload['anchors_scanned']}`.",
            f"- Candidate count: `{payload['candidate_count']}`.",
            f"- Source context rows: `{payload['source_context_count']}`.",
            f"- Certification attempts: `{payload['local_certification_attempt_count']}`.",
            f"- Promoted candidates: `{len(payload['promoted_task_ids'])}`.",
            f"- Paid LLM calls made: `{str(payload['paid_llm_calls_made']).lower()}`.",
            f"- Paid ACUT calls made: `{str(payload['paid_acut_calls_made']).lower()}`.",
            f"- Predictive validity established: `false`.",
            "",
            f"- First filter counts: `{payload['first_filter_counts']}`.",
            f"- Source context status counts: `{payload['source_context_status_counts']}`.",
            f"- Local certification status counts: `{payload['local_certification_status_counts']}`.",
            f"- Promotion blocker counts: `{payload['promotion_blocker_counts']}`.",
        ]
    )


def statement_from_clean_context(
    pilot_config: repo_history_pilot.PilotConfig,
    candidate: dict[str, Any],
    contexts: list[dict[str, Any]],
) -> dict[str, Any]:
    refs = [row for row in contexts if row.get("task_id") == candidate.get("task_id")]
    if not refs:
        refs = [repo_history_pilot.commit_context_ref(pilot_config, candidate)]
    allowed_refs = repo_history_pilot.allowed_context_refs(refs)
    quality = statement_quality.statement_quality_for_context(refs[0], candidate)
    statement = {
        "schema_version": "barcarolle.repo_history_statement.v1",
        "task_id": candidate["task_id"],
        "repo_id": pilot_config.repo_id,
        "base_commit": candidate["base_commit"],
        "target_commit": candidate["target_commit"],
        "solver_facing_statement": repo_history_pilot.solver_statement(candidate, refs),
        "scope_boundaries": (
            f"Modify only implementation files needed for this {pilot_config.repo_id} behavior; "
            "do not edit tests or generated metadata."
        ),
        "allowed_context_refs": allowed_refs,
        "excluded_context_refs": [ref["ref"] for ref in refs if ref["classification"] != "problem_context"],
        "oracle_refs": candidate["test_files"],
        "harness_test_command": pilot_config.command_template,
        "statement_quality": quality,
        "statement_review_status": "reviewed" if allowed_refs else "near_certified_context_missing",
        "source_context_status": "non_leaky_context_found" if allowed_refs else "no_non_leaky_source_context",
    }
    if quality["statement_quality_gate"] == "material_risk":
        statement["statement_review_status"] = "statement_quality_risk"
    return statement


def second_repo_review_payload(config: dict[str, Any], *, repo_id: str, reviews: list[dict[str, Any]]) -> dict[str, Any]:
    promoted = [row for row in reviews if row.get("promotion_decision") == "promote_to_clean_benchmark_candidate"]
    rejected_counts: Counter[str] = Counter()
    for row in reviews:
        if row.get("promotion_decision") != "promote_to_clean_benchmark_candidate":
            rejected_counts.update(row.get("promotion_blockers", []) or ["not_promoted"])
    return {
        "schema_version": "barcarolle.phase1.second_repo_clean_supply_review.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "repo_id": repo_id,
        "paid_llm_calls_made": False,
        "paid_acut_calls_made": False,
        "promoted_task_ids": [str(row["task_id"]) for row in promoted],
        "promoted_reviews": promoted,
        "review_records": reviews,
        "rejected_counts": dict(sorted(rejected_counts.items())),
        "predictive_validity_established": False,
    }


def second_repo_review_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Second-Repo Clean Supply Review",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Repo: `{payload['repo_id']}`.",
        f"- Promoted task count: `{len(payload['promoted_task_ids'])}`.",
        f"- Paid LLM calls made: `{str(payload['paid_llm_calls_made']).lower()}`.",
        f"- Paid ACUT calls made: `{str(payload['paid_acut_calls_made']).lower()}`.",
        f"- Predictive validity established: `false`.",
        "",
        "| Task | Status | Decision | Blockers |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["review_records"]:
        blockers = ", ".join(row.get("promotion_blockers", [])) or "none"
        lines.append(
            f"| `{row['task_id']}` | `{row.get('original_local_certification_status')}` | "
            f"`{row['promotion_decision']}` | `{blockers}` |"
        )
    return "\n".join(lines)


def second_repo_overlay_payload(config: dict[str, Any], *, repo_id: str, promoted_reviews: list[dict[str, Any]]) -> dict[str, Any]:
    preferred = config["preferred_clean_split"]
    minimum = config["minimum_clean_split"]
    plan = select_cutoff_for_repo(
        repo_id,
        promoted_reviews,
        embargo_gap_days=int(config["mining"]["embargo_gap_days"]),
        preferred_b=int(preferred["B_eval"]),
        preferred_h=int(preferred["H_future"]),
        minimum_b=int(minimum["B_eval"]),
        minimum_h=int(minimum["H_future"]),
        model_snapshot_date=None,
        model_snapshot_status="unknown",
    )
    b_eval_ids = plan.get("b_eval_task_ids", [])
    h_future_ids = plan.get("h_future_task_ids", [])
    selected_ids = set(b_eval_ids) | set(h_future_ids)
    selected_tasks = []
    for row in promoted_reviews:
        row = dict(row)
        if row["task_id"] in b_eval_ids:
            row["selected_split"] = "B_eval"
        elif row["task_id"] in h_future_ids:
            row["selected_split"] = "H_future"
        else:
            row["selected_split"] = "reserve_clean_supply"
        selected_tasks.append(row)
    return {
        "schema_version": "barcarolle.phase1.second_repo_clean_supply_overlay.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "evidence_level": "clean_supply_overlay_sidecar",
        "selected_repo_id": repo_id,
        "promoted_task_ids": [str(row["task_id"]) for row in promoted_reviews],
        "selected_task_ids": unique_preserve([*b_eval_ids, *h_future_ids]),
        "selected_b_eval_task_ids": b_eval_ids,
        "selected_h_future_task_ids": h_future_ids,
        "reserve_clean_task_ids": [str(row["task_id"]) for row in promoted_reviews if str(row["task_id"]) not in selected_ids],
        "promoted_tasks": selected_tasks,
        "minimum_clean_split": minimum,
        "preferred_clean_split": preferred,
        "cutoff_feasibility": plan,
        "clean_supply_ready": bool(plan.get("clean_validation_ready")),
        "paid_llm_calls_made": False,
        "paid_acut_calls_made": False,
        "predictive_validity_established": False,
    }


def second_repo_overlay_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Second-Repo Clean Supply Overlay",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Evidence level: `{payload['evidence_level']}`.",
            f"- Selected repo: `{payload['selected_repo_id']}`.",
            f"- Clean supply ready: `{str(payload['clean_supply_ready']).lower()}`.",
            f"- B_eval tasks: `{', '.join(payload['selected_b_eval_task_ids']) if payload['selected_b_eval_task_ids'] else 'none'}`.",
            f"- H_future tasks: `{', '.join(payload['selected_h_future_task_ids']) if payload['selected_h_future_task_ids'] else 'none'}`.",
            f"- Reserve clean tasks: `{', '.join(payload['reserve_clean_task_ids']) if payload['reserve_clean_task_ids'] else 'none'}`.",
            f"- Paid LLM calls made: `{str(payload['paid_llm_calls_made']).lower()}`.",
            f"- Paid ACUT calls made: `{str(payload['paid_acut_calls_made']).lower()}`.",
            f"- Predictive validity established: `false`.",
            "",
            f"- T_compile_end: `{payload['cutoff_feasibility'].get('T_compile_end')}`.",
            f"- T_holdout_start: `{payload['cutoff_feasibility'].get('T_holdout_start')}`.",
            f"- Validation size: `{payload['cutoff_feasibility'].get('validation_size')}`.",
        ]
    )


def overlay_payload(
    *,
    prior_promoted_tasks: list[dict[str, Any]],
    promoted_reviews: list[dict[str, Any]],
    minimum_clean_split: dict[str, int],
    cutoff_feasibility: dict[str, Any],
) -> dict[str, Any]:
    promoted_tasks = [dict(task) for task in prior_promoted_tasks]
    promoted_tasks.extend(dict(row) for row in promoted_reviews if row.get("promotion_decision") == "promote_to_clean_benchmark_candidate")
    promoted_by_repo: dict[str, list[str]] = {}
    promoted_by_split: dict[str, list[str]] = {split: [] for split in minimum_clean_split}
    for row in promoted_tasks:
        repo_id = str(row.get("repo_id") or repo_from_task_id(str(row["task_id"])))
        split = str(row.get("split") or "unknown")
        task_id = str(row["task_id"])
        promoted_by_repo.setdefault(repo_id, [])
        promoted_by_repo[repo_id] = unique_preserve(promoted_by_repo[repo_id] + [task_id])
        promoted_by_split.setdefault(split, [])
        promoted_by_split[split] = unique_preserve(promoted_by_split[split] + [task_id])
    split_ready = all(len(promoted_by_split.get(split, [])) >= int(count) for split, count in minimum_clean_split.items())
    cutoff_ready = any(bool(plan.get("clean_validation_ready")) for plan in cutoff_feasibility.values())
    return {
        "schema_version": "barcarolle.phase1.clean_outcome_unseen_supply_overlay.v1",
        "generated_at": now_utc(),
        "evidence_level": "clean_supply_overlay_sidecar",
        "promoted_by_repo": promoted_by_repo,
        "promoted_by_split": promoted_by_split,
        "promoted_task_ids": unique_preserve([str(row["task_id"]) for row in promoted_tasks]),
        "newly_promoted_task_ids": unique_preserve(
            [str(row["task_id"]) for row in promoted_reviews if row.get("promotion_decision") == "promote_to_clean_benchmark_candidate"]
        ),
        "promoted_tasks": promoted_tasks,
        "minimum_clean_split": minimum_clean_split,
        "cutoff_feasibility": cutoff_feasibility,
        "clean_supply_ready": split_ready and cutoff_ready,
        "predictive_validity_established": False,
    }


def mine_repo(config: dict[str, Any], repo_id: str) -> dict[str, Any]:
    repo_rows = load_repo_rows(repo_id)
    seen_ids = load_outcome_seen_task_ids(config)
    seen_commits = load_outcome_seen_target_commits(config)
    prior_ids = {task["original_task_id"] for task in prior_promoted_tasks(config)}
    existing_ids = {task_id for task_id in existing_task_ids() if "__clean_ext__" not in task_id}
    reviews: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    contexts: list[dict[str, Any]] = []
    for original_task_id, row in sorted(repo_rows.items(), key=lambda item: (str(item[1].get("task_time")), item[0])):
        if original_task_id in prior_ids:
            continue
        if not row.get("target_commit") or not row.get("task_time"):
            continue
        row = dict(row)
        row["split"] = split_for_candidate(row, config)
        ext_id = extension_task_id(repo_id, existing_task_ids=existing_ids)
        existing_ids.add(ext_id)
        context = context_for_candidate(row)
        review = review_candidate(
            row,
            extension_task_id=ext_id,
            context=context,
            outcome_seen_task_ids=seen_ids,
            outcome_seen_target_commits=seen_commits,
        )
        reviews.append(review)
        candidates.append(
            {
                "schema_version": "barcarolle.phase1.clean_outcome_unseen_supply_candidate.v1",
                "task_id": ext_id,
                "original_task_id": original_task_id,
                "repo_id": repo_id,
                "split": row["split"],
                "task_time": row.get("task_time"),
                "base_commit": row.get("base_commit"),
                "target_commit": row.get("target_commit"),
                "subject": row.get("subject"),
                "candidate_filter_status": row.get("candidate_filter_status"),
                "promotion_decision": review["promotion_decision"],
                "promotion_blockers": review["promotion_blockers"],
            }
        )
        contexts.append(
            {
                "schema_version": "barcarolle.phase1.clean_outcome_unseen_supply_source_context.v1",
                "task_id": ext_id,
                "original_task_id": original_task_id,
                "repo_id": repo_id,
                **context,
            }
        )
    promoted = [row for row in reviews if row["promotion_decision"] == "promote_to_clean_benchmark_candidate"]
    write_jsonl(phase0_candidate_path(repo_id, "candidates"), candidates)
    write_jsonl(phase0_candidate_path(repo_id, "source_context"), contexts)
    write_jsonl(phase0_certified_path(repo_id, "certified_tasks"), promoted)
    write_jsonl(phase0_certified_path(repo_id, "review_records"), reviews)
    return inventory_payload(config, {repo_id: reviews})


def load_extension_reviews() -> dict[str, list[dict[str, Any]]]:
    reviews: dict[str, list[dict[str, Any]]] = {}
    for path in (PHASE0_ROOT / "certified_tasks").glob("*_clean_outcome_unseen_supply_review_records.jsonl"):
        repo_id = path.name.split("_clean_outcome_unseen_supply_", 1)[0]
        reviews[repo_id] = read_jsonl(path)
    return reviews


def inventory_payload(config: dict[str, Any], reviews_by_repo: dict[str, list[dict[str, Any]]] | None = None) -> dict[str, Any]:
    reviews_by_repo = reviews_by_repo or load_extension_reviews()
    repo_summary = {}
    recommended_path = "mine_boltons_first"
    for repo_id, reviews in sorted(reviews_by_repo.items()):
        counts = Counter(row["promotion_decision"] for row in reviews)
        blocker_counts: Counter[str] = Counter()
        for row in reviews:
            blocker_counts.update(row.get("promotion_blockers", []))
        promoted = [row for row in reviews if row["promotion_decision"] == "promote_to_clean_benchmark_candidate"]
        repo_summary[repo_id] = {
            "reviewed_candidate_count": len(reviews),
            "promoted_candidate_count": len(promoted),
            "promotion_decision_counts": dict(sorted(counts.items())),
            "blocker_counts": dict(sorted(blocker_counts.items())),
            "promoted_task_ids": [row["task_id"] for row in promoted],
        }
        if repo_id == config["target"]["primary_repo"] and promoted:
            recommended_path = "build_overlay_with_boltons_supply"
    return {
        "schema_version": "barcarolle.phase1.clean_outcome_unseen_supply_candidate_inventory.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "paid_llm_calls_made": False,
        "paid_acut_calls_made": False,
        "repo_summary": repo_summary,
        "recommended_path": recommended_path,
        "predictive_validity_established": False,
    }


def inventory_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Clean Outcome-Unseen Supply Candidate Inventory",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Recommended path: `{payload['recommended_path']}`.",
        f"- Paid LLM calls made: `{str(payload['paid_llm_calls_made']).lower()}`.",
        f"- Paid ACUT calls made: `{str(payload['paid_acut_calls_made']).lower()}`.",
        f"- Predictive validity established: `false`.",
        "",
        "| Repo | Reviewed | Promoted | Decision counts |",
        "| --- | ---: | ---: | --- |",
    ]
    for repo_id, summary in payload["repo_summary"].items():
        lines.append(
            f"| `{repo_id}` | {summary['reviewed_candidate_count']} | {summary['promoted_candidate_count']} | "
            f"`{summary['promotion_decision_counts']}` |"
        )
    return "\n".join(lines)


def review_payload(config: dict[str, Any]) -> dict[str, Any]:
    reviews_by_repo = load_extension_reviews()
    prior = prior_promoted_tasks(config)
    promoted_reviews = [row for rows in reviews_by_repo.values() for row in rows if row["promotion_decision"] == "promote_to_clean_benchmark_candidate"]
    plans = cutoff_feasibility_for_tasks(config, [*prior, *promoted_reviews])
    rejected_counts: Counter[str] = Counter()
    for rows in reviews_by_repo.values():
        for row in rows:
            if row["promotion_decision"] != "promote_to_clean_benchmark_candidate":
                rejected_counts.update(row.get("promotion_blockers", []) or ["not_promoted"])
    promoted_by_repo: dict[str, list[str]] = {}
    for row in promoted_reviews:
        promoted_by_repo.setdefault(str(row["repo_id"]), []).append(str(row["task_id"]))
    return {
        "schema_version": "barcarolle.phase1.clean_outcome_unseen_supply_review.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "paid_llm_calls_made": False,
        "paid_acut_calls_made": False,
        "promoted_by_repo": promoted_by_repo,
        "promoted_reviews": promoted_reviews,
        "review_records": [row for rows in reviews_by_repo.values() for row in rows],
        "rejected_counts": dict(sorted(rejected_counts.items())),
        "cutoff_feasibility": plans,
        "predictive_validity_established": False,
    }


def review_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Clean Outcome-Unseen Supply Review",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Promoted task count: `{sum(len(ids) for ids in payload['promoted_by_repo'].values())}`.",
        f"- Paid LLM calls made: `{str(payload['paid_llm_calls_made']).lower()}`.",
        f"- Paid ACUT calls made: `{str(payload['paid_acut_calls_made']).lower()}`.",
        f"- Predictive validity established: `false`.",
        "",
        "| Task | Original task | Repo | Decision | Blockers |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["review_records"]:
        blockers = ", ".join(row.get("promotion_blockers", [])) or "none"
        lines.append(
            f"| `{row['task_id']}` | `{row.get('original_task_id')}` | `{row.get('repo_id')}` | "
            f"`{row['promotion_decision']}` | `{blockers}` |"
        )
    return "\n".join(lines)


def build_overlay(config: dict[str, Any]) -> dict[str, Any]:
    review = read_json(result_path("phase1_clean_outcome_unseen_supply_review.json")) if result_path("phase1_clean_outcome_unseen_supply_review.json").exists() else review_payload(config)
    prior = prior_promoted_tasks(config)
    promoted = review["promoted_reviews"]
    plans = cutoff_feasibility_for_tasks(config, [*prior, *promoted])
    payload = overlay_payload(
        prior_promoted_tasks=prior,
        promoted_reviews=promoted,
        minimum_clean_split={split: int(count) for split, count in config["target"]["minimum_clean_split"].items()},
        cutoff_feasibility=plans,
    )
    payload["config"] = rel(config["_path"])
    payload["paid_llm_calls_made"] = False
    payload["paid_acut_calls_made"] = False
    return payload


def overlay_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Clean Outcome-Unseen Supply Overlay",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Evidence level: `{payload['evidence_level']}`.",
        f"- Clean supply ready: `{str(payload['clean_supply_ready']).lower()}`.",
        f"- Newly promoted tasks: `{len(payload['newly_promoted_task_ids'])}`.",
        f"- Paid LLM calls made: `{str(payload.get('paid_llm_calls_made', False)).lower()}`.",
        f"- Paid ACUT calls made: `{str(payload.get('paid_acut_calls_made', False)).lower()}`.",
        f"- Predictive validity established: `false`.",
        "",
        "| Split | Task IDs |",
        "| --- | --- |",
    ]
    for split, task_ids in payload["promoted_by_split"].items():
        lines.append(f"| `{split}` | {', '.join(f'`{task_id}`' for task_id in task_ids)} |")
    return "\n".join(lines)


def decision_payload(config: dict[str, Any]) -> dict[str, Any]:
    overlay = read_json(result_path("phase1_clean_outcome_unseen_supply_overlay.json"))
    prereg_path = result_path("phase1_future_holdout_preregistration.json")
    future_decision_path = result_path("phase1_future_holdout_decision.json")
    prereg = read_json(prereg_path) if prereg_path.exists() else {}
    future_decision = read_json(future_decision_path) if future_decision_path.exists() else {}
    boltons_ready = (
        overlay["clean_supply_ready"]
        and "boltons" in overlay.get("promoted_by_repo", {})
        and prereg.get("status") == "frozen"
        and "boltons" in prereg.get("selected_repos", [])
    )
    backup_ready_repos = [
        repo_id
        for repo_id in prereg.get("selected_repos", [])
        if repo_id != config["target"]["primary_repo"] and overlay["cutoff_feasibility"].get(repo_id, {}).get("clean_validation_ready")
    ]
    if boltons_ready:
        label = "boltons_clean_supply_ready_for_preregistered_validation"
        next_runbook = "run_preregistered_clean_future_holdout_paid_validation"
    elif backup_ready_repos:
        label = "backup_repo_clean_supply_ready_for_preregistered_validation"
        next_runbook = "run_preregistered_clean_future_holdout_paid_validation"
    elif overlay.get("clean_supply_ready") and prereg.get("status") != "frozen":
        label = "clean_supply_mining_tooling_blocked"
        next_runbook = "repair_clean_supply_mining_tooling"
    else:
        label = "clean_supply_continued_mining_still_blocked"
        next_runbook = "continue_mining_clean_outcome_unseen_supply_with_additional_backup_repo"
    return {
        "schema_version": "barcarolle.phase1.clean_outcome_unseen_supply_decision.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "paid_llm_calls_made": False,
        "paid_acut_calls_made": False,
        "primary_decision_label": label,
        "recommended_next_runbook": next_runbook,
        "promoted_by_repo": overlay.get("promoted_by_repo", {}),
        "promoted_by_split": overlay.get("promoted_by_split", {}),
        "newly_promoted_task_ids": overlay.get("newly_promoted_task_ids", []),
        "cutoff_feasibility": overlay.get("cutoff_feasibility", {}),
        "future_holdout_preregistration_status": prereg.get("status"),
        "future_holdout_selected_repos": prereg.get("selected_repos", []),
        "future_holdout_decision_label": future_decision.get("primary_decision_label"),
        "clean_supply_ready": overlay.get("clean_supply_ready"),
        "predictive_validity_established": False,
        "allowed_claims": [
            "clean_outcome_unseen_supply_mining_completed",
            "clean_supply_overlay_created",
            "boltons_clean_supply_ready_for_preregistered_validation" if boltons_ready else "strict_clean_future_holdout_still_blocked",
            "insufficient_evidence_for_predictive_validity",
        ],
        "disallowed_claims": [
            "predictive_validity_established",
            "clean_future_holdout_validated_without_paid_holdout_run",
            "production_benchmark_ranking",
            "promotion_of_solution_leaky_or_project_heavy_tasks",
            "contamination_proof_evaluation_if_model_snapshot_unknown",
        ],
    }


def decision_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Clean Outcome-Unseen Supply Mining Decision",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Primary decision: `{payload['primary_decision_label']}`.",
            f"- Recommended next runbook: `{payload['recommended_next_runbook']}`.",
            f"- Clean supply ready: `{str(payload['clean_supply_ready']).lower()}`.",
            f"- Future-holdout preregistration status: `{payload.get('future_holdout_preregistration_status')}`.",
            f"- Selected future-holdout repos: `{', '.join(payload.get('future_holdout_selected_repos', [])) if payload.get('future_holdout_selected_repos') else 'none'}`.",
            f"- Newly promoted tasks: `{', '.join(payload.get('newly_promoted_task_ids', [])) if payload.get('newly_promoted_task_ids') else 'none'}`.",
            f"- Paid LLM calls made: `{str(payload['paid_llm_calls_made']).lower()}`.",
            f"- Paid ACUT calls made: `{str(payload['paid_acut_calls_made']).lower()}`.",
            f"- Predictive validity established: `false`.",
        ]
    )


def run_audit_state(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    decision = read_json(artifact_path(config, "current_breal_extension_decision"))
    overlay = read_json(artifact_path(config, "current_breal_extension_overlay"))
    payload = {
        "schema_version": "barcarolle.phase1.clean_outcome_unseen_supply_state_audit.v1",
        "generated_at": now_utc(),
        "previous_decision": decision.get("primary_decision_label"),
        "previous_clean_supply_ready": overlay.get("clean_supply_ready"),
        "previous_promoted_by_split": overlay.get("promoted_by_split"),
        "outcome_seen_task_count": len(load_outcome_seen_task_ids(config)),
        "outcome_seen_target_commit_count": len(load_outcome_seen_target_commits(config)),
        "paid_llm_calls_made": False,
        "paid_acut_calls_made": False,
        "predictive_validity_established": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def run_mine_boltons(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    payload = mine_repo(config, config["target"]["primary_repo"])
    write_json(result_path("phase1_clean_outcome_unseen_supply_candidate_inventory.json"), payload)
    write_text(report_path("phase1_clean_outcome_unseen_supply_candidate_inventory.md"), inventory_report(payload))
    return payload


def run_mine_backup(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    reviews = {}
    for repo_id in config["target"].get("backup_repos", []):
        local_repo = artifact_path(config, f"{repo_id}_local_repo")
        if not local_repo.exists():
            write_jsonl(phase0_candidate_path(repo_id, "candidates"), [])
            write_jsonl(phase0_candidate_path(repo_id, "source_context"), [])
            write_jsonl(phase0_certified_path(repo_id, "certified_tasks"), [])
            write_jsonl(
                phase0_certified_path(repo_id, "review_records"),
                [
                    {
                        "schema_version": "barcarolle.phase1.clean_outcome_unseen_supply_review.v1",
                        "repo_id": repo_id,
                        "promotion_decision": "reject_for_clean_holdout",
                        "promotion_blockers": ["backup_repo_not_cloned"],
                        "predictive_validity_established": False,
                    }
                ],
            )
            reviews[repo_id] = read_jsonl(phase0_certified_path(repo_id, "review_records"))
            continue
        reviews[repo_id] = mine_repo(config, repo_id)["repo_summary"].get(repo_id, {})
    payload = inventory_payload(config)
    write_json(result_path("phase1_clean_outcome_unseen_supply_candidate_inventory.json"), payload)
    write_text(report_path("phase1_clean_outcome_unseen_supply_candidate_inventory.md"), inventory_report(payload))
    return payload


def run_review_candidates(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    inventory = inventory_payload(config)
    review = review_payload(config)
    write_json(result_path("phase1_clean_outcome_unseen_supply_candidate_inventory.json"), inventory)
    write_text(report_path("phase1_clean_outcome_unseen_supply_candidate_inventory.md"), inventory_report(inventory))
    write_json(result_path("phase1_clean_outcome_unseen_supply_review.json"), review)
    write_text(report_path("phase1_clean_outcome_unseen_supply_review.md"), review_report(review))
    return review


def run_build_overlay(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    payload = build_overlay(config)
    write_json(result_path("phase1_clean_outcome_unseen_supply_overlay.json"), payload)
    write_text(report_path("phase1_clean_outcome_unseen_supply_overlay.md"), overlay_report(payload))
    return payload


def run_decide(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    payload = decision_payload(config)
    write_json(result_path("phase1_clean_outcome_unseen_supply_decision.json"), payload)
    write_text(report_path("phase1_clean_outcome_unseen_supply_decision.md"), decision_report(payload))
    return payload


def resolve_second_repo_id(config: dict[str, Any], requested: str | None) -> str:
    repo_id = requested or str(config["primary_candidate_repo"])
    if repo_id not in config["candidate_repos"]:
        raise ValueError(f"unknown candidate repo: {repo_id}")
    return repo_id


def run_mine_second_repo(args: argparse.Namespace) -> dict[str, Any]:
    config = load_second_repo_config(Path(args.config))
    repo_id = resolve_second_repo_id(config, args.repo_id)
    pilot_config = second_repo_pilot_config(config, repo_id)
    if not pilot_config.local_repo.exists():
        raise FileNotFoundError(f"local repo missing: {pilot_config.local_repo}")
    anchors, candidates = repo_history_pilot.mining_rows(
        REPO_ROOT,
        pilot_config,
        max_anchors=int(config["mining"]["max_history_anchors"]),
    )
    contexts, _statements = source_context_rows_for_candidates(pilot_config, candidates)
    write_jsonl(second_repo_candidate_path(config, repo_id, "candidates"), candidates)
    write_jsonl(second_repo_candidate_path(config, repo_id, "source_context"), contexts)
    payload = second_repo_inventory_payload(config, repo_id=repo_id, anchors=anchors, candidates=candidates, contexts=contexts)
    write_json(configured_output_path(config, "candidate_inventory"), payload)
    write_text(configured_output_path(config, "candidate_inventory_report"), second_repo_inventory_report(payload))
    return payload


def run_certify_second_repo(args: argparse.Namespace) -> dict[str, Any]:
    config = load_second_repo_config(Path(args.config))
    repo_id = resolve_second_repo_id(config, args.repo_id)
    pilot_config = second_repo_pilot_config(config, repo_id)
    candidates = read_jsonl(second_repo_candidate_path(config, repo_id, "candidates"))
    contexts = read_jsonl(second_repo_candidate_path(config, repo_id, "source_context"))
    inventory_path = configured_output_path(config, "candidate_inventory")
    prior_inventory = read_json(inventory_path) if inventory_path.exists() else None
    selected_context = selected_context_for_task(contexts)
    certification_rows: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    seen_ids = load_outcome_seen_task_ids(
        {
            "source_artifacts": {
                "workspace_scorecard": "experiments/phase1_compiler/results/phase1_workspace_scorecard.json",
            }
        }
    )
    seen_commits = load_outcome_seen_target_commits(
        {
            "source_artifacts": {
                "workspace_scorecard": "experiments/phase1_compiler/results/phase1_workspace_scorecard.json",
            }
        }
    )
    for candidate in candidates[: int(config["mining"]["max_certification_attempts"])]:
        statement = statement_from_clean_context(pilot_config, candidate, contexts)
        certified_row = repo_history_pilot.certify_candidate(REPO_ROOT, PHASE0_ROOT, pilot_config, candidate, statement)
        certification_rows.append(certified_row)
        reviews.append(
            review_second_repo_candidate(
                certified_row,
                context=selected_context.get(str(candidate["task_id"]), {}),
                outcome_seen_task_ids=seen_ids,
                outcome_seen_target_commits=seen_commits,
            )
        )
    promoted = [row for row in reviews if row.get("promotion_decision") == "promote_to_clean_benchmark_candidate"]
    write_jsonl(second_repo_certified_path(config, repo_id, "certified_tasks"), promoted)
    write_jsonl(second_repo_certified_path(config, repo_id, "review_records"), reviews)
    inventory = second_repo_inventory_payload(
        config,
        repo_id=repo_id,
        candidates=candidates,
        contexts=contexts,
        reviews=reviews,
        certification_rows=certification_rows,
        prior_inventory=prior_inventory,
    )
    review = second_repo_review_payload(config, repo_id=repo_id, reviews=reviews)
    write_json(configured_output_path(config, "candidate_inventory"), inventory)
    write_text(configured_output_path(config, "candidate_inventory_report"), second_repo_inventory_report(inventory))
    write_json(configured_output_path(config, "review"), review)
    write_text(configured_output_path(config, "review_report"), second_repo_review_report(review))
    return review


def run_build_second_repo_overlay(args: argparse.Namespace) -> dict[str, Any]:
    config = load_second_repo_config(Path(args.config))
    repo_id = resolve_second_repo_id(config, args.repo_id)
    review = read_json(configured_output_path(config, "review"))
    payload = second_repo_overlay_payload(config, repo_id=repo_id, promoted_reviews=review.get("promoted_reviews", []))
    write_json(configured_output_path(config, "overlay"), payload)
    write_text(configured_output_path(config, "overlay_report"), second_repo_overlay_report(payload))
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Continue clean outcome-unseen supply mining for Phase 1.")
    parser.add_argument(
        "command",
        choices=[
            "audit-state",
            "mine-boltons",
            "review-candidates",
            "mine-backup",
            "build-overlay",
            "decide",
            "mine-second-repo",
            "certify-second-repo",
            "build-second-repo-overlay",
        ],
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--repo-id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runners = {
        "audit-state": run_audit_state,
        "mine-boltons": run_mine_boltons,
        "review-candidates": run_review_candidates,
        "mine-backup": run_mine_backup,
        "build-overlay": run_build_overlay,
        "decide": run_decide,
        "mine-second-repo": run_mine_second_repo,
        "certify-second-repo": run_certify_second_repo,
        "build-second-repo-overlay": run_build_second_repo_overlay,
    }
    payload = runners[args.command](args)
    if args.command != "audit-state":
        print(
            json.dumps(
                {
                    "status": "ok",
                    "command": args.command,
                    "primary_decision_label": payload.get("primary_decision_label"),
                    "clean_supply_ready": payload.get("clean_supply_ready"),
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
