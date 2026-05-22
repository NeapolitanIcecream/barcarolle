from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
PHASE1_ROOT = REPO_ROOT / "experiments" / "phase1_compiler"
REPOS = ("toolz", "humanize", "itsdangerous")

SOURCE_TIERS = (
    "benchmark_grade_source",
    "manual_review_source",
    "diagnostic_only_source",
    "reject_source",
)
ORACLE_STATUSES = ("aligned", "manual_review_required", "diagnostic_only", "reject")
HARDENED_STATUSES = ("benchmark_grade_candidate", "manual_review_required", "diagnostic_only", "rejected")
GATE_ORDER = (
    "checkout",
    "oracle_extractable",
    "no_op_fail",
    "reference_pass",
    "known_bad_fail",
    "flakiness_check",
    "ambiguity_review",
    "solution_leakage_review",
    "scope_clarity_review",
    "cost_boundedness",
    "taxonomy_labelability",
)
PROJECT_OR_CONFIG_PREFIXES = (
    ".devcontainer/",
    ".github/",
    "ci/",
    "docs/",
    "requirements/",
)
PROJECT_OR_CONFIG_FILES = {
    ".editorconfig",
    ".flake8",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".readthedocs.yaml",
    "LICENSE.txt",
    "MANIFEST.in",
    "README.md",
    "README.rst",
    "CHANGES.rst",
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "tox.ini",
    "uv.lock",
}
SOURCE_QUALITY_WORDS = (
    "bug",
    "error",
    "fail",
    "failure",
    "expected",
    "observed",
    "reported",
    "should",
    "need",
    "needs",
    "allow",
    "support",
    "regression",
    "bad signature",
    "not defined",
    "could result",
)
SOLUTION_WORDS = (
    "removed",
    "ran ",
    "manual cleanup",
    "implemented",
    "changed to",
    "now it is",
    "this conditional checks",
    "use a dedicated library",
    "accessed lazily",
    "diff",
    "patch",
    "```",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ascii_safe(value: Any) -> str:
    return str(value or "").encode("ascii", errors="backslashreplace").decode("ascii")


def digest_text(text: str, length: int = 16) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:length]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: ascii_safe(row.get(field, "")) for field in fieldnames})


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return "null"
    text = str(value)
    if not text or any(ch in text for ch in ":#[]{}"):
        return json.dumps(text)
    return text


def render_yaml(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    lines: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(render_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {yaml_scalar(item)}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(render_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}- {yaml_scalar(item)}")
    else:
        lines.append(f"{prefix}{yaml_scalar(value)}")
    return lines


def default_hardening_config() -> dict[str, Any]:
    return {
        "schema_version": "barcarolle.phase1_source_certification_hardening_config.v1",
        "status": "configured",
        "claim_scope": "source_adapter_and_certification_hardening",
        "predictive_validity_established": False,
        "paid_acut_calls": "disabled",
        "paid_llm_calls": "disabled",
        "source_policy": {
            "benchmark_grade_allowed_source_kinds": [
                "issue",
                "pull_request",
                "issue_comment",
                "pr_body",
                "pr_comment",
                "manual_canary",
                "customer_regression",
            ],
            "diagnostic_only_source_kinds": ["commit_message_fallback", "commit_subject", "inferred_from_diff"],
            "reject_source_kinds": ["missing"],
        },
        "source_quality_gates": {
            "commit_message_fallback_max_for_benchmark_grade": 0,
            "issue_or_pr_context_required_for_benchmark_grade": True,
            "solution_exposure_risk_allowed_for_benchmark_grade": False,
        },
        "oracle_alignment_gates": {
            "no_op_fail": "required",
            "reference_pass_twice": "required",
            "hidden_tests_apply_to_base": "required",
            "changed_test_patch_nonempty": "required",
            "wide_test_risk_review": "required",
            "narrow_test_risk_review": "required",
        },
        "third_repo": {
            "preferred_repo_id": "itsdangerous",
            "min_certified_for_pilot": 4,
            "min_certified_for_benchmark_candidate": 6,
            "min_b_real": 2,
            "min_w_real": 2,
        },
        "candidate_filter_policy": {
            "reject_subject_terms": [
                "update dev dependencies",
                "update project files",
                "drop support",
                "remove deprecated",
                "deprecate",
                "typing",
                "lint",
                "format",
                "pre-commit",
            ],
            "reject_if_project_file_heavy": True,
            "reject_if_no_behavior_code_file": True,
            "reject_if_changed_lines_over": 250,
            "manual_review_if_cross_module_count_over": 3,
            "manual_review_if_docs_or_config_change_present": True,
        },
    }


def load_repo_rows(repo_id: str, include_near: bool = True) -> list[dict[str, Any]]:
    certified = read_jsonl(PHASE0_ROOT / "certified_tasks" / f"{repo_id}_certified_tasks.jsonl")
    near = read_jsonl(PHASE0_ROOT / "certified_tasks" / f"{repo_id}_near_certified_tasks.jsonl") if include_near else []
    rows = []
    for row in [*certified, *near]:
        copied = dict(row)
        copied["phase0_status"] = copied.get("status", "")
        rows.append(copied)
    return sorted(rows, key=lambda row: (str(row.get("repo_id", repo_id)), str(row.get("task_id", ""))))


def load_contexts(repo_id: str) -> dict[str, dict[str, Any]]:
    contexts = read_jsonl(PHASE0_ROOT / "candidate_sources" / f"{repo_id}_source_context.jsonl")
    by_task: dict[str, dict[str, Any]] = {}
    for context in contexts:
        task_id = str(context.get("task_id", ""))
        if not task_id:
            continue
        existing = by_task.get(task_id)
        if existing is None:
            by_task[task_id] = dict(context)
        elif existing.get("source_items") or not context.get("source_items"):
            continue
        else:
            by_task[task_id] = dict(context)
    return by_task


def load_statements(repo_id: str) -> dict[str, dict[str, Any]]:
    statements = read_jsonl(PHASE0_ROOT / "certified_tasks" / f"{repo_id}_task_statements.jsonl")
    return {str(row.get("task_id")): row for row in statements if row.get("task_id")}


def load_candidates(repo_id: str) -> list[dict[str, Any]]:
    return read_jsonl(PHASE0_ROOT / "candidate_sources" / f"{repo_id}_candidates.jsonl")


def source_kind_from_context(context: dict[str, Any]) -> tuple[str, str, bool]:
    if not context:
        return "missing", "", False
    explicit = str(context.get("source_kind") or "")
    if explicit:
        return explicit, str(context.get("ref") or ""), False
    for item in context.get("source_items", []):
        if item.get("solver_usable") and item.get("leakage_class") == "problem_context":
            return str(item.get("kind") or "missing"), str(item.get("source_id") or ""), False
    ref = str(context.get("ref") or "")
    if ref.startswith("pr:"):
        return "pull_request", ref, False
    if ref.startswith("issue:"):
        return "issue", ref, False
    if ref.startswith("comment:"):
        return "issue_comment", ref, False
    if ref.startswith("commit:"):
        return "commit_message_fallback", ref, False
    return "missing", ref, False


def context_has_solution_exposure(context: dict[str, Any]) -> bool:
    classification = str(context.get("classification") or "")
    if classification in {"solution_context", "mixed_context"}:
        return True
    for item in context.get("source_items", []):
        if item.get("solver_usable") and item.get("leakage_class") == "solution_revealing":
            return True
    if any(item.get("solver_usable") and item.get("leakage_class") == "problem_context" for item in context.get("source_items", [])):
        return False
    text_parts = [str(context.get("summary") or ""), str(context.get("body_summary") or "")]
    text_parts.extend(str(item.get("summary") or "") for item in context.get("source_items", []) if item.get("solver_usable"))
    text = " ".join(text_parts).lower()
    return any(word in text for word in SOLUTION_WORDS)


def context_is_release_or_changelog(context: dict[str, Any]) -> bool:
    ref = str(context.get("ref") or "").lower()
    source_kind = str(context.get("source_kind") or "").lower()
    return source_kind in {"release_notes", "changelog"} or "changelog" in ref or "changes" in ref


def source_overlay_row(task: dict[str, Any], context: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    source_kind, source_ref, _ = source_kind_from_context(context)
    source_policy = config["source_policy"]
    diagnostic = set(source_policy["diagnostic_only_source_kinds"])
    allowed = set(source_policy["benchmark_grade_allowed_source_kinds"])
    reject = set(source_policy["reject_source_kinds"])
    solution_exposure = context_has_solution_exposure(context)

    if source_kind in reject or not context:
        tier = "reject_source"
        reason = "missing_source_context"
    elif source_kind in diagnostic:
        tier = "diagnostic_only_source"
        reason = "commit_message_fallback_only" if source_kind == "commit_message_fallback" else f"diagnostic_source_kind:{source_kind}"
    elif context_is_release_or_changelog(context):
        tier = "manual_review_source"
        reason = "release_or_changelog_context_requires_manual_review"
    elif source_kind in allowed and not solution_exposure:
        tier = "benchmark_grade_source"
        reason = "non_leaky_problem_context"
    elif source_kind in allowed:
        tier = "manual_review_source"
        reason = "solution_exposure_or_mixed_context_requires_review"
    else:
        tier = "manual_review_source"
        reason = f"unrecognized_source_kind:{source_kind}"

    return {
        "task_id": str(task.get("task_id", "")),
        "repo_id": str(task.get("repo_id", "")),
        "target_commit": str(task.get("target_commit", "")),
        "phase0_status": str(task.get("phase0_status") or task.get("status") or ""),
        "source_kind": source_kind,
        "source_ref": source_ref,
        "phase1_source_tier": tier,
        "benchmark_grade_eligible": tier == "benchmark_grade_source",
        "reason": reason,
        "solution_exposure_risk": solution_exposure,
        "manual_review_required": tier == "manual_review_source",
    }


def build_source_provenance_overlay(config: dict[str, Any], generated_at: str) -> dict[str, Any]:
    tasks = []
    summary: dict[str, Any] = {}
    source_files = []
    for repo_id in REPOS:
        contexts = load_contexts(repo_id)
        rows = load_repo_rows(repo_id)
        source_files.extend(
            [
                rel(PHASE0_ROOT / "candidate_sources" / f"{repo_id}_source_context.jsonl"),
                rel(PHASE0_ROOT / "certified_tasks" / f"{repo_id}_certified_tasks.jsonl"),
                rel(PHASE0_ROOT / "certified_tasks" / f"{repo_id}_near_certified_tasks.jsonl"),
            ]
        )
        repo_rows = [source_overlay_row(row, contexts.get(str(row.get("task_id")), {}), config) for row in rows]
        tasks.extend(repo_rows)
        tier_counts = Counter(row["phase1_source_tier"] for row in repo_rows)
        status_counts = Counter(row["phase0_status"] for row in repo_rows)
        summary[repo_id] = {
            "task_count": len(repo_rows),
            "certified_count": status_counts["certified"],
            "near_certified_count": status_counts["near_certified"],
            "source_tier_counts": {tier: tier_counts.get(tier, 0) for tier in SOURCE_TIERS},
            "benchmark_grade_eligible_count": sum(1 for row in repo_rows if row["benchmark_grade_eligible"]),
        }
    tasks.sort(key=lambda row: (row["repo_id"], row["task_id"]))
    return {
        "schema_version": "barcarolle.phase1.source_provenance_overlay.v1",
        "generated_at": generated_at,
        "claim_scope": "source_provenance_overlay",
        "predictive_validity_established": False,
        "source_files": sorted(set(source_files)),
        "repo_summary": summary,
        "tasks": tasks,
    }


def run_command(command: list[str], cwd: Path, timeout: int = 45, env: dict[str, str] | None = None) -> dict[str, Any]:
    start = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        duration = time.monotonic() - start
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        return {
            "returncode": completed.returncode,
            "duration_seconds": round(duration, 3),
            "timed_out": False,
            "stdout_tail_hash": digest_text(stdout[-2000:], 12),
            "stderr_tail_hash": digest_text(stderr[-2000:], 12),
        }
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - start
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        return {
            "returncode": 124,
            "duration_seconds": round(duration, 3),
            "timed_out": True,
            "stdout_tail_hash": digest_text(str(stdout)[-2000:], 12),
            "stderr_tail_hash": digest_text(str(stderr)[-2000:], 12),
        }


def gh_authenticated() -> bool:
    if shutil.which("gh") is None:
        return False
    result = subprocess.run(["gh", "auth", "status"], cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    return result.returncode == 0


def fetch_commit_pull_requests(owner_repo: str, commit: str) -> list[dict[str, Any]]:
    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{owner_repo}/commits/{commit}/pulls",
            "-H",
            "Accept: application/vnd.github.groot-preview+json",
        ],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        return [{"lookup_status": "gh_api_error", "stderr_digest": digest_text(result.stderr, 12)}]
    try:
        pulls = json.loads(result.stdout)
    except json.JSONDecodeError:
        return [{"lookup_status": "gh_api_invalid_json"}]
    sanitized = []
    for pull in pulls[:3]:
        body = str(pull.get("body") or "")
        sanitized.append(
            {
                "lookup_status": "pull_request_metadata_found",
                "number": pull.get("number"),
                "title": ascii_safe(pull.get("title") or ""),
                "body_digest": digest_text(body),
                "body_length": len(body),
                "url": pull.get("html_url"),
                "body_excerpt": ascii_safe(" ".join(body.split())[:240]),
            }
        )
    return sanitized or [{"lookup_status": "no_pull_request"}]


def fetch_issue_or_pr_metadata(owner_repo: str, issue_number: str) -> dict[str, Any]:
    result = subprocess.run(
        ["gh", "api", f"repos/{owner_repo}/issues/{issue_number}"],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        return {"lookup_status": "gh_api_error", "stderr_digest": digest_text(result.stderr, 12)}
    try:
        item = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"lookup_status": "gh_api_invalid_json"}
    body = str(item.get("body") or "")
    return {
        "lookup_status": "issue_or_pr_metadata_found",
        "number": item.get("number"),
        "title": ascii_safe(item.get("title") or ""),
        "body_digest": digest_text(body),
        "body_length": len(body),
        "url": item.get("html_url"),
        "body_excerpt": ascii_safe(" ".join(body.split())[:240]),
        "source_kind": "pull_request" if item.get("pull_request") else "issue",
    }


def local_commit_message(repo_id: str, commit: str) -> tuple[str, str]:
    repo = PHASE0_ROOT / "external_repos" / repo_id
    if not repo.exists():
        return "", ""
    result = subprocess.run(
        ["git", "show", "-s", "--format=%s%n%b", commit],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        return "", ""
    lines = result.stdout.splitlines()
    subject = lines[0] if lines else ""
    body = "\n".join(lines[1:])
    return subject, body


def issue_refs_from_text(text: str) -> list[str]:
    refs = []
    for match in re.finditer(r"(?i)\b(?:fixes|closes|refs|references)\s+#(\d+)", text):
        refs.append(f"issue:{match.group(1)}")
    return sorted(set(refs))


def classify_source_text(title: str, body: str) -> str:
    combined = f"{title}\n{body}".lower()
    if not combined.strip():
        return "insufficient_context"
    has_problem = any(word in combined for word in SOURCE_QUALITY_WORDS)
    has_solution = any(word in combined for word in SOLUTION_WORDS)
    if has_problem and has_solution:
        return "mixed_context"
    if has_solution:
        return "solution_context"
    if has_problem:
        return "problem_context"
    return "insufficient_context"


def build_humanize_hardened_sources(use_github: bool, generated_at: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = load_repo_rows("humanize", include_near=False)
    original_contexts = load_contexts("humanize")
    github_enabled = use_github and gh_authenticated()
    hardened = []
    for task in rows:
        task_id = str(task["task_id"])
        commit = str(task["target_commit"])
        subject, body = local_commit_message("humanize", commit)
        original_context = original_contexts.get(task_id, {})
        issue_refs = issue_refs_from_text(f"{subject}\n{body}")
        candidates: list[dict[str, Any]] = []
        lookup_statuses: list[str] = []
        if github_enabled:
            for pull in fetch_commit_pull_requests("python-humanize/humanize", commit):
                lookup_statuses.append(str(pull.get("lookup_status") or "unknown"))
                if pull.get("lookup_status") == "pull_request_metadata_found":
                    classification = classify_source_text(str(pull.get("title") or ""), str(pull.get("body_excerpt") or ""))
                    candidates.append(
                        {
                            "source_kind": "pull_request",
                            "source_ref": f"pr:{pull.get('number')}",
                            "source_title": pull.get("title") or "",
                            "source_body_digest": pull.get("body_digest") or "",
                            "source_url": pull.get("url") or "",
                            "classification": classification,
                        }
                    )
                elif pull.get("lookup_status") not in {"no_pull_request"}:
                    candidates.append(
                        {
                            "source_kind": "missing",
                            "source_ref": "",
                            "source_title": "",
                            "source_body_digest": "",
                            "source_url": "",
                            "classification": str(pull.get("lookup_status")),
                        }
                    )
        for ref in issue_refs:
            issue_number = ref.split(":", 1)[1]
            issue_metadata: dict[str, Any] | None = None
            if github_enabled:
                issue_metadata = fetch_issue_or_pr_metadata("python-humanize/humanize", issue_number)
                lookup_statuses.append(str(issue_metadata.get("lookup_status") or "unknown"))
            if issue_metadata and issue_metadata.get("lookup_status") == "issue_or_pr_metadata_found":
                title = str(issue_metadata.get("title") or "")
                body_excerpt = str(issue_metadata.get("body_excerpt") or "")
                source_kind = str(issue_metadata.get("source_kind") or "issue")
                source_ref = ("pr:" if source_kind == "pull_request" else "issue:") + issue_number
                source_url = str(issue_metadata.get("url") or "")
                body_digest = str(issue_metadata.get("body_digest") or "")
                classification = classify_source_text(title, body_excerpt)
            else:
                title = ascii_safe(subject)
                source_kind = "issue"
                source_ref = ref
                source_url = f"https://github.com/python-humanize/humanize/issues/{issue_number}"
                body_digest = digest_text(body)
                classification = classify_source_text(subject, body)
            candidates.append(
                {
                    "source_kind": source_kind,
                    "source_ref": source_ref,
                    "source_title": ascii_safe(title),
                    "source_body_digest": body_digest,
                    "source_url": source_url,
                    "classification": classification,
                }
            )

        usable = [row for row in candidates if row["classification"] == "problem_context"]
        if usable:
            selected = usable[0]
            decision = "repaired_to_problem_context"
            manual_review_required = False
            leakage_risk = False
        elif candidates:
            selected = candidates[0]
            decision = "manual_review_required"
            manual_review_required = True
            leakage_risk = selected["classification"] in {"solution_context", "mixed_context"}
        elif original_context.get("source_kind") == "commit_message_fallback":
            selected = {
                "source_kind": "commit_message_fallback",
                "source_ref": f"commit:{commit}",
                "source_title": ascii_safe(subject or original_context.get("summary") or task.get("subject") or ""),
                "source_body_digest": digest_text(body),
                "source_url": f"https://github.com/python-humanize/humanize/commit/{commit}",
                "classification": "insufficient_context",
            }
            decision = "diagnostic_only_commit_fallback"
            manual_review_required = False
            leakage_risk = False
        else:
            selected = {
                "source_kind": "missing",
                "source_ref": "",
                "source_title": "",
                "source_body_digest": "",
                "source_url": "",
                "classification": "missing",
            }
            decision = "reject_missing_context"
            manual_review_required = False
            leakage_risk = False

        hardened.append(
            {
                "schema_version": "barcarolle.phase1.humanize_hardened_source_context.v1",
                "generated_at": generated_at,
                "task_id": task_id,
                "target_commit": commit,
                "source_kind": selected["source_kind"],
                "source_ref": selected["source_ref"],
                "source_title": ascii_safe(selected["source_title"]),
                "source_body_digest": selected["source_body_digest"],
                "source_url": selected["source_url"],
                "classification": selected["classification"],
                "leakage_risk": leakage_risk,
                "manual_review_required": manual_review_required,
                "hardened_decision": decision,
                "github_lookup_attempted": github_enabled,
                "github_lookup_status": ";".join(sorted(set(lookup_statuses))) if lookup_statuses else "not_attempted",
                "raw_github_response_committed": False,
            }
        )
    counts = Counter(row["hardened_decision"] for row in hardened)
    summary = {
        "schema_version": "barcarolle.phase1.humanize_source_hardening_summary.v1",
        "generated_at": generated_at,
        "github_lookup_attempted": github_enabled,
        "certified_task_count": len(rows),
        "decision_counts": dict(sorted(counts.items())),
        "repaired_to_problem_context_count": counts["repaired_to_problem_context"],
        "humanize_decision": "humanize_benchmark_candidate_overlay" if counts["repaired_to_problem_context"] >= 6 else "humanize_source_blocker_confirmed_operational_pilot_only",
        "no_raw_github_responses_committed": True,
        "no_paid_llm_calls_made": True,
    }
    return sorted(hardened, key=lambda row: row["task_id"]), summary


def total_changed_lines(task: dict[str, Any]) -> int:
    return int(task.get("changed_lines_total") or 0) or int(task.get("changed_lines_added") or 0) + int(task.get("changed_lines_deleted") or 0)


def is_project_or_config_path(path: str) -> bool:
    return path in PROJECT_OR_CONFIG_FILES or path.startswith(PROJECT_OR_CONFIG_PREFIXES)


def is_test_path(path: str) -> bool:
    name = Path(path).name
    return path.startswith("tests/") or path.startswith("test/") or "/tests/" in path or name.startswith("test_")


def is_behavior_code_path(path: str) -> bool:
    if not path.endswith(".py") or is_test_path(path):
        return False
    if is_project_or_config_path(path):
        return False
    return True


def subject_has_term(subject: str, terms: list[str]) -> str:
    lower = subject.lower()
    for term in terms:
        if term in lower:
            return term
    return ""


def candidate_filter_row(task: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    policy = config["candidate_filter_policy"]
    subject = str(task.get("subject") or "")
    changed_files = list(task.get("changed_files") or [])
    code_files = list(task.get("code_files") or [path for path in changed_files if is_behavior_code_path(str(path))])
    taxonomy = dict(task.get("taxonomy_draft") or {})
    modules = task.get("module_or_package") or taxonomy.get("module") or [Path(path).stem for path in code_files]
    module_count = len(set(modules))
    project_paths = [path for path in changed_files if is_project_or_config_path(str(path))]
    reject_reasons = []
    manual_review_reasons = []
    term = subject_has_term(subject, list(policy["reject_subject_terms"]))
    if term:
        reject_reasons.append(f"reject_subject_term:{term}")
    if policy["reject_if_project_file_heavy"] and project_paths and len(project_paths) >= max(2, len(code_files) + 1):
        reject_reasons.append("project_file_heavy")
    if policy["reject_if_no_behavior_code_file"] and not code_files:
        reject_reasons.append("no_behavior_code_file")
    changed_limit = int(policy["reject_if_changed_lines_over"])
    if total_changed_lines(task) > changed_limit:
        reject_reasons.append(f"changed_lines_over:{changed_limit}")
    if module_count > int(policy["manual_review_if_cross_module_count_over"]):
        manual_review_reasons.append(f"cross_module_count_over:{policy['manual_review_if_cross_module_count_over']}")
    if policy["manual_review_if_docs_or_config_change_present"] and project_paths:
        manual_review_reasons.append("docs_or_config_change_present")
    if reject_reasons:
        status = "rejected"
    elif manual_review_reasons:
        status = "manual_review_required"
    else:
        status = "accepted"
    return {
        "task_id": str(task.get("task_id", "")),
        "repo_id": str(task.get("repo_id", "")),
        "target_commit": str(task.get("target_commit", "")),
        "candidate_filter_status": status,
        "reject_reasons": reject_reasons,
        "manual_review_reasons": manual_review_reasons,
        "changed_line_count": total_changed_lines(task),
        "project_or_config_file_count": len(project_paths),
        "code_file_count": len(code_files),
    }


def build_candidate_filter_audit(config: dict[str, Any], generated_at: str) -> dict[str, Any]:
    rows = []
    summary: dict[str, Any] = {}
    for repo_id in REPOS:
        candidates = load_candidates(repo_id)
        repo_rows = [candidate_filter_row(row, config) for row in candidates]
        rows.extend(repo_rows)
        counts = Counter(row["candidate_filter_status"] for row in repo_rows)
        summary[repo_id] = {
            "candidate_count": len(repo_rows),
            "accepted_count": counts["accepted"],
            "manual_review_required_count": counts["manual_review_required"],
            "rejected_count": counts["rejected"],
            "remaining_after_filter_count": counts["accepted"] + counts["manual_review_required"],
            "top_reject_reasons": dict(Counter(reason for row in repo_rows for reason in row["reject_reasons"]).most_common(8)),
        }
    rows.sort(key=lambda row: (row["repo_id"], row["task_id"]))
    return {
        "schema_version": "barcarolle.phase1.candidate_filter_audit.v1",
        "generated_at": generated_at,
        "claim_scope": "candidate_selection_overlay",
        "predictive_validity_established": False,
        "policy": config["candidate_filter_policy"],
        "repo_summary": summary,
        "tasks": rows,
    }


def task_execution_passed(task: dict[str, Any]) -> bool:
    gates = dict(task.get("gates") or {})
    return bool(gates) and all(gates.get(gate) == "pass" for gate in GATE_ORDER)


def oracle_alignment_row(task: dict[str, Any], source_tier: str) -> dict[str, Any]:
    gates = dict(task.get("gates") or {})
    statement = str(task.get("solver_facing_statement") or "")
    repo_id = str(task.get("repo_id") or "")
    changed_files = [str(path) for path in task.get("changed_files") or []]
    code_files = [str(path) for path in task.get("code_files") or []]
    test_files = [str(path) for path in task.get("test_files") or []]
    modules = set(task.get("module_or_package") or [])
    subject = str(task.get("subject") or "").lower()
    risk_flags: list[str] = []

    if len(code_files) > 3 or len(changed_files) > 8 or total_changed_lines(task) > 250:
        risk_flags.append("wide_test_risk")
    if len(test_files) == 1 and (len(code_files) > 1 or len(modules) > 1):
        risk_flags.append("narrow_test_risk")
    if gates.get("no_op_fail") != "pass" or gates.get("known_bad_fail") == "fail":
        risk_flags.append("weak_oracle_risk")
    if len(modules) > 3:
        risk_flags.append("multi_issue_patch_risk")
        risk_flags.append("large_cross_module_change_risk")
    if any(term in subject for term in ("update", "deprecate", "remove deprecated", "drop support", "project files", "dev dependencies")):
        risk_flags.append("maintenance_or_dependency_update_risk")
    if repo_id != "humanize" and "humanize behavior" in statement.lower():
        risk_flags.append("statement_source_mismatch")
    if gates.get("reference_pass") == "fail":
        risk_flags.append("target_fails_hidden_tests")
    if any(is_project_or_config_path(path) for path in changed_files) and len([path for path in changed_files if is_project_or_config_path(path)]) >= len(code_files):
        risk_flags.append("test_edits_only_or_config_heavy_change")
    for module in modules:
        module_text = str(module).strip("_").lower()
        if module_text and module_text not in statement.lower() and repo_id != "toolz":
            risk_flags.append("reference_patch_requires_unmentioned_symbol")
            break

    if source_tier == "reject_source":
        status = "reject"
    elif source_tier == "diagnostic_only_source":
        status = "diagnostic_only"
    elif "weak_oracle_risk" in risk_flags or "target_fails_hidden_tests" in risk_flags:
        status = "reject"
    elif risk_flags:
        status = "manual_review_required"
    else:
        status = "aligned"
    return {
        "task_id": str(task.get("task_id", "")),
        "repo_id": repo_id,
        "phase0_status": str(task.get("phase0_status") or task.get("status") or ""),
        "source_tier": source_tier,
        "oracle_alignment_status": status,
        "risk_flags": sorted(set(risk_flags)),
        "weak_oracle_risk": "weak_oracle_risk" in risk_flags,
        "wide_test_risk": "wide_test_risk" in risk_flags,
        "narrow_test_risk": "narrow_test_risk" in risk_flags,
    }


def build_oracle_alignment_audit(source_overlay: dict[str, Any], generated_at: str) -> dict[str, Any]:
    source_by_task = {row["task_id"]: row for row in source_overlay["tasks"]}
    rows = []
    for repo_id in REPOS:
        statements = load_statements(repo_id)
        for task in load_repo_rows(repo_id):
            merged = dict(task)
            merged.update(statements.get(str(task.get("task_id")), {}))
            source_tier = source_by_task.get(str(task.get("task_id")), {}).get("phase1_source_tier", "reject_source")
            rows.append(oracle_alignment_row(merged, str(source_tier)))
    rows.sort(key=lambda row: (row["repo_id"], row["task_id"]))
    repo_summary = {}
    for repo_id in REPOS:
        repo_rows = [row for row in rows if row["repo_id"] == repo_id]
        status_counts = Counter(row["oracle_alignment_status"] for row in repo_rows)
        risk_counts = Counter(flag for row in repo_rows for flag in row["risk_flags"])
        repo_summary[repo_id] = {
            "task_count": len(repo_rows),
            "status_counts": {status: status_counts.get(status, 0) for status in ORACLE_STATUSES},
            "top_risk_flags": dict(risk_counts.most_common(8)),
        }
    return {
        "schema_version": "barcarolle.phase1.oracle_alignment_audit.v1",
        "generated_at": generated_at,
        "claim_scope": "oracle_alignment_audit",
        "predictive_validity_established": False,
        "summary": {
            "status_counts": dict(Counter(row["oracle_alignment_status"] for row in rows)),
            "risk_flag_counts": dict(Counter(flag for row in rows for flag in row["risk_flags"])),
        },
        "repo_summary": repo_summary,
        "tasks": rows,
    }


def failure_category(task: dict[str, Any]) -> str:
    gate = str(task.get("first_failing_gate") or "")
    if gate == "reference_pass":
        return "reference_pass_failure"
    if gate == "no_op_fail":
        return "no_op_fail_failure"
    if gate == "checkout":
        return "checkout_failure"
    if gate == "oracle_extractable":
        return "oracle_extract_failure"
    if gate in {"ambiguity_review", "solution_leakage_review", "scope_clarity_review"}:
        return "source_context_failure"
    if gate == "taxonomy_labelability":
        return "scope_or_taxonomy_failure"
    return "certified_or_unknown"


def environment_probe_variants(task: dict[str, Any], target_ws: Path) -> list[tuple[str, list[str]]]:
    test_paths = [str(target_ws / path) for path in task.get("test_files") or []]
    project = str(PHASE0_ROOT)
    return [
        (
            "configured_command",
            ["uv", "run", "--project", project, "--with", "pytest>=9", "--with", "setuptools<81", "python", "-m", "pytest", "-q", *test_paths],
        ),
        (
            "pytest_current_with_editable",
            [
                "uv",
                "run",
                "--project",
                project,
                "--with-editable",
                str(target_ws),
                "--with",
                "pytest>=9",
                "--with",
                "setuptools<81",
                "python",
                "-m",
                "pytest",
                "-q",
                *test_paths,
            ],
        ),
        (
            "pytest_legacy_7_with_editable",
            [
                "uv",
                "run",
                "--project",
                project,
                "--with-editable",
                str(target_ws),
                "--with",
                "pytest<8",
                "--with",
                "setuptools<81",
                "python",
                "-m",
                "pytest",
                "-q",
                *test_paths,
            ],
        ),
        (
            "pytest_legacy_6_with_editable",
            [
                "uv",
                "run",
                "--project",
                project,
                "--with-editable",
                str(target_ws),
                "--with",
                "pytest<7",
                "--with",
                "setuptools<81",
                "python",
                "-m",
                "pytest",
                "-q",
                *test_paths,
            ],
        ),
        (
            "repo_declared_test_extra_if_present",
            [
                "uv",
                "run",
                "--project",
                project,
                "--with-editable",
                str(target_ws),
                "--with",
                "pytest<8",
                "--with",
                "setuptools<81",
                "--with",
                "freezegun",
                "python",
                "-m",
                "pytest",
                "-q",
                *test_paths,
            ],
        ),
    ]


def run_environment_probes_for_task(task: dict[str, Any]) -> list[dict[str, Any]]:
    target_ws = PHASE0_ROOT / "workspaces" / "repo_history_pilot" / "itsdangerous" / str(task.get("task_id")) / "target"
    if not target_ws.exists():
        return [{"variant": "workspace_missing", "command_hash": "", "returncode": None, "duration_seconds": 0, "timed_out": False}]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(target_ws / "src")
    env["SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ITSDANGEROUS"] = "0.0.0"
    probe_rows = []
    for variant, command in environment_probe_variants(task, target_ws):
        record = run_command(command, REPO_ROOT, timeout=45, env=env)
        probe_rows.append(
            {
                "variant": variant,
                "command_hash": digest_text(json.dumps(command, sort_keys=True), 12),
                **record,
            }
        )
    return probe_rows


def build_environment_synthesis_diagnosis(generated_at: str, run_environment_probes: bool) -> dict[str, Any]:
    near = load_repo_rows("itsdangerous")
    near = [row for row in near if row.get("status") == "near_certified"]
    rows = []
    supported = set()
    for task in near:
        category = failure_category(task)
        target_ws = PHASE0_ROOT / "workspaces" / "repo_history_pilot" / "itsdangerous" / str(task.get("task_id")) / "target"
        missing_test_files = [path for path in task.get("test_files") or [] if not (target_ws / path).exists()]
        probes = run_environment_probes_for_task(task) if run_environment_probes and category == "reference_pass_failure" else []
        repaired_variant = next((probe["variant"] for probe in probes if probe.get("returncode") == 0), "")
        if category == "reference_pass_failure" and repaired_variant:
            environment_status = "repaired_environment_variant_found"
            supported.add("environment_synthesis_mismatch")
        elif category == "reference_pass_failure":
            environment_status = "reference_environment_unrepaired"
        elif category == "no_op_fail_failure":
            environment_status = "not_environment_failure"
            supported.add("oracle_weakness")
        else:
            environment_status = "not_environment_failure"
        if missing_test_files:
            supported.add("oracle_weakness")
        if subject_has_term(str(task.get("subject") or ""), default_hardening_config()["candidate_filter_policy"]["reject_subject_terms"]):
            supported.add("candidate_pool_bad")
        rows.append(
            {
                "task_id": str(task.get("task_id", "")),
                "repo_id": "itsdangerous",
                "first_failing_gate": str(task.get("first_failing_gate") or ""),
                "failure_category": category,
                "environment_status": environment_status,
                "repaired_variant": repaired_variant,
                "target_missing_test_files": missing_test_files,
                "probe_results": probes,
                "raw_command_output_committed": False,
            }
        )
    counts = Counter(row["failure_category"] for row in rows)
    status_counts = Counter(row["environment_status"] for row in rows)
    return {
        "schema_version": "barcarolle.phase1.environment_synthesis_diagnosis.v1",
        "generated_at": generated_at,
        "claim_scope": "environment_synthesis_diagnosis",
        "predictive_validity_established": False,
        "repo_id": "itsdangerous",
        "run_environment_probes": run_environment_probes,
        "summary": {
            "near_certified_count": len(rows),
            "failure_category_counts": dict(sorted(counts.items())),
            "environment_status_counts": dict(sorted(status_counts.items())),
            "supported_decisions": sorted(supported) or ["insufficient_repo_history_supply"],
        },
        "tasks": sorted(rows, key=lambda row: row["task_id"]),
    }


def build_hardened_certification_overlay(
    source_overlay: dict[str, Any],
    oracle_audit: dict[str, Any],
    candidate_filter_audit: dict[str, Any],
    environment_diagnosis: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    source_by_task = {row["task_id"]: row for row in source_overlay["tasks"]}
    oracle_by_task = {row["task_id"]: row for row in oracle_audit["tasks"]}
    filter_by_task = {row["task_id"]: row for row in candidate_filter_audit["tasks"]}
    environment_by_task = {row["task_id"]: row for row in environment_diagnosis["tasks"]}
    rows = []
    for repo_id in REPOS:
        for task in load_repo_rows(repo_id):
            task_id = str(task.get("task_id"))
            source = source_by_task.get(task_id, {})
            oracle = oracle_by_task.get(task_id, {})
            candidate = filter_by_task.get(task_id, {"candidate_filter_status": "accepted", "reject_reasons": [], "manual_review_reasons": []})
            environment = environment_by_task.get(task_id, {})
            execution_passed = task_execution_passed(task)
            source_tier = str(source.get("phase1_source_tier") or "reject_source")
            oracle_status = str(oracle.get("oracle_alignment_status") or "reject")
            candidate_status = str(candidate.get("candidate_filter_status") or "accepted")
            environment_status = str(environment.get("environment_status") or "clean")
            reject_reasons = []
            if not execution_passed:
                reject_reasons.append(f"execution_gate_failed:{task.get('first_failing_gate') or 'unknown'}")
            if source_tier == "reject_source":
                reject_reasons.append("source_reject")
            if source_tier == "diagnostic_only_source":
                reject_reasons.append("source_diagnostic_only")
            if oracle_status == "reject":
                reject_reasons.append("oracle_alignment_reject")
            if candidate_status == "rejected":
                reject_reasons.extend(candidate.get("reject_reasons") or ["candidate_filter_reject"])
            if source.get("solution_exposure_risk"):
                reject_reasons.append("solution_exposure_risk")

            if reject_reasons and "source_diagnostic_only" not in reject_reasons:
                hardened_status = "rejected"
            elif "source_diagnostic_only" in reject_reasons:
                hardened_status = "diagnostic_only"
            elif (
                execution_passed
                and source_tier == "benchmark_grade_source"
                and oracle_status == "aligned"
                and candidate_status == "accepted"
                and environment_status == "clean"
                and not source.get("solution_exposure_risk")
            ):
                hardened_status = "benchmark_grade_candidate"
            else:
                hardened_status = "manual_review_required"

            rows.append(
                {
                    "task_id": task_id,
                    "repo_id": repo_id,
                    "phase0_status": str(task.get("phase0_status") or task.get("status") or ""),
                    "execution_gate_status": "passed" if execution_passed else f"failed:{task.get('first_failing_gate') or 'unknown'}",
                    "source_tier": source_tier,
                    "oracle_alignment_status": oracle_status,
                    "candidate_filter_status": candidate_status,
                    "environment_status": environment_status,
                    "hardened_status": hardened_status,
                    "hardened_reject_reasons": sorted(set(reject_reasons)),
                }
            )
    rows.sort(key=lambda row: (row["repo_id"], row["task_id"]))
    repo_summary = {}
    for repo_id in REPOS:
        repo_rows = [row for row in rows if row["repo_id"] == repo_id]
        counts = Counter(row["hardened_status"] for row in repo_rows)
        repo_summary[repo_id] = {
            "task_count": len(repo_rows),
            "benchmark_grade_candidate_count": counts["benchmark_grade_candidate"],
            "manual_review_required_count": counts["manual_review_required"],
            "diagnostic_only_count": counts["diagnostic_only"],
            "rejected_count": counts["rejected"],
            "blocking_gates": dict(Counter(reason for row in repo_rows for reason in row["hardened_reject_reasons"]).most_common(8)),
        }
    return {
        "schema_version": "barcarolle.phase1.hardened_certification_overlay.v1",
        "generated_at": generated_at,
        "claim_scope": "certification_gate_hardening",
        "predictive_validity_established": False,
        "repo_summary": repo_summary,
        "tasks": rows,
    }


def build_hardening_plan(generated_at: str) -> dict[str, Any]:
    humanize_context = load_contexts("humanize")
    humanize_certified = load_repo_rows("humanize", include_near=False)
    its_certified = [row for row in load_repo_rows("itsdangerous") if row.get("status") == "certified"]
    its_near = [row for row in load_repo_rows("itsdangerous") if row.get("status") == "near_certified"]
    fallback_count = sum(1 for row in humanize_certified if humanize_context.get(str(row.get("task_id")), {}).get("source_kind") == "commit_message_fallback")
    return {
        "schema_version": "barcarolle.phase1.source_certification_hardening_plan.v1",
        "generated_at": generated_at,
        "claim_scope": "source_adapter_and_certification_hardening",
        "predictive_validity_established": False,
        "paid_acut_calls": "disabled",
        "paid_llm_calls": "disabled",
        "paid_acut_cells_scheduled": False,
        "paid_llm_calls_scheduled": False,
        "current_humanize_fallback_count": fallback_count,
        "current_itsdangerous_certified_count": len(its_certified),
        "current_itsdangerous_near_certified_count": len(its_near),
        "humanize": {
            "certified_count": len(humanize_certified),
            "commit_message_fallback_count": fallback_count,
            "decision_criteria": "benchmark-grade only if at least 6 certified tasks repair to non-leaky problem context",
            "commit_message_fallback_is_diagnostic_only": True,
        },
        "itsdangerous": {
            "certified_count": len(its_certified),
            "near_certified_count": len(its_near),
            "decision_criteria": "pilot repair requires at least 4 certified tasks with balanced B/W and no diagnostic-only source gate",
        },
        "hypotheses_to_test": [
            "source_adapter_too_weak",
            "candidate_selection_too_broad",
            "environment_synthesis_mismatch",
            "oracle_alignment_mismatch",
            "certification_implementation_bug",
        ],
        "expected_outputs": [
            "phase1_source_provenance_overlay",
            "humanize_hardened_source_context",
            "phase1_oracle_alignment_audit",
            "phase1_environment_synthesis_diagnosis",
            "phase1_candidate_filter_audit",
            "phase1_hardened_certification_overlay",
            "phase1_certification_hardening_decision",
        ],
        "stop_conditions": [
            "paid_acut_or_paid_llm_call_required",
            "raw_or_workspace_artifact_would_need_commit",
            "source_records_inconsistent_enough_to_mislead",
            "local_scoped_tests_unrepairable",
            "hardening_would_force_predictive_validity_claim",
        ],
    }


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


def runbook_starting_head() -> str:
    process = PHASE1_ROOT / "reports" / "phase1_source_certification_hardening_process.md"
    if process.exists():
        match = re.search(r"\|\s*HEAD\s*\|\s*`([a-f0-9]{40})`", process.read_text(encoding="utf-8"))
        if match:
            return match.group(1)
    return git_head()


def choose_primary_decision(
    humanize_repaired_count: int,
    source_overlay: dict[str, Any],
    oracle_audit: dict[str, Any],
    environment_diagnosis: dict[str, Any],
    hardened_overlay: dict[str, Any],
) -> str:
    risk_counts = oracle_audit.get("summary", {}).get("risk_flag_counts", {})
    supported = set(environment_diagnosis.get("summary", {}).get("supported_decisions", []))
    its_hardened = hardened_overlay.get("repo_summary", {}).get("itsdangerous", {})
    toolz_hardened = hardened_overlay.get("repo_summary", {}).get("toolz", {})
    if risk_counts.get("statement_source_mismatch", 0) > 0:
        return "certification_implementation_bug_found"
    if "environment_synthesis_mismatch" in supported:
        return "third_repo_environment_repair_needed"
    if "candidate_pool_bad" in supported:
        return "third_repo_candidate_pool_repair_needed"
    if "oracle_weakness" in supported:
        return "replace_third_repo_before_paid_acut"
    if humanize_repaired_count < 6 and its_hardened.get("benchmark_grade_candidate_count", 0) < 4:
        return "humanize_source_blocker_confirmed_third_repo_repair_needed"
    if toolz_hardened.get("benchmark_grade_candidate_count", 0) >= 6 and (
        humanize_repaired_count >= 6 or its_hardened.get("benchmark_grade_candidate_count", 0) >= 4
    ):
        return "source_certification_hardening_complete_ready_for_future_holdout_design"
    return "replace_third_repo_before_future_holdout"


def build_final_decision(payloads: dict[str, Any], generated_at: str) -> dict[str, Any]:
    humanize_summary = payloads["humanize_hardened_summary"]
    source_overlay = payloads["source_overlay"]
    oracle_audit = payloads["oracle_alignment_audit"]
    environment = payloads["environment_synthesis_diagnosis"]
    hardened = payloads["hardened_certification_overlay"]
    primary = choose_primary_decision(
        int(humanize_summary["repaired_to_problem_context_count"]),
        source_overlay,
        oracle_audit,
        environment,
        hardened,
    )
    supported = set(environment["summary"]["supported_decisions"])
    third_repo_decision = "third_repo_manual_review_required"
    if primary == "third_repo_environment_repair_needed":
        third_repo_decision = "repair_itsdangerous_environment"
    elif primary == "third_repo_candidate_pool_repair_needed":
        third_repo_decision = "repair_itsdangerous_candidate_filter_and_remine"
    elif primary == "replace_third_repo_before_paid_acut":
        third_repo_decision = "replace_third_repo_before_paid_acut"
    elif "environment_synthesis_mismatch" in supported and "candidate_pool_bad" in supported:
        third_repo_decision = "repair_itsdangerous_candidate_filter_and_remine"
    if primary == "replace_third_repo_before_paid_acut":
        third_repo_should_be_repaired_or_replaced = "replace_third_repo_before_paid_acut"
        recommended_next_runbook = "select_replacement_third_repo_and_locally_certify_without_paid_acut"
    elif primary in {"third_repo_environment_repair_needed", "third_repo_candidate_pool_repair_needed"}:
        third_repo_should_be_repaired_or_replaced = "repair_itsdangerous_before_paid_acut"
        recommended_next_runbook = "fix_itsdangerous_environment_or_candidate_filter_then_remine_certify_without_paid_acut"
    else:
        third_repo_should_be_repaired_or_replaced = "repair_or_replace_third_repo_before_paid_acut"
        recommended_next_runbook = "fix_itsdangerous_statement_template_environment_and_candidate_filter_then_remine_certify_without_paid_acut"
    return {
        "schema_version": "barcarolle.phase1.certification_hardening_decision.v1",
        "generated_at": generated_at,
        "starting_head": payloads["starting_head"],
        "final_head": payloads["final_head"],
        "primary_decision_label": primary,
        "predictive_validity_established": False,
        "tools_or_configs_added": [
            "experiments/phase1_compiler/configs/phase1_source_certification_hardening.yaml",
            "experiments/phase1_compiler/tools/phase1_source_certification_hardening.py",
            "experiments/phase1_compiler/tests/test_phase1_source_certification_hardening.py",
        ],
        "repos_analyzed": list(REPOS),
        "source_tier_counts": {
            repo: summary["source_tier_counts"] for repo, summary in source_overlay["repo_summary"].items()
        },
        "oracle_alignment_counts": {
            repo: summary["status_counts"] for repo, summary in oracle_audit["repo_summary"].items()
        },
        "environment_diagnosis_counts": environment["summary"]["failure_category_counts"],
        "hardened_certification_counts": {
            repo: {
                "benchmark_grade_candidate_count": summary["benchmark_grade_candidate_count"],
                "manual_review_required_count": summary["manual_review_required_count"],
                "diagnostic_only_count": summary["diagnostic_only_count"],
                "rejected_count": summary["rejected_count"],
            }
            for repo, summary in hardened["repo_summary"].items()
        },
        "humanize_decision": humanize_summary["humanize_decision"],
        "itsdangerous_decision": {
            "third_repo_decision": third_repo_decision,
            "supported_failure_modes": environment["summary"]["supported_decisions"],
            "certification_statement_template_bug": oracle_audit["summary"]["risk_flag_counts"].get("statement_source_mismatch", 0) > 0,
        },
        "third_repo_should_be_repaired_or_replaced": third_repo_should_be_repaired_or_replaced,
        "allowed_claims": [
            "source_adapter_hardening",
            "certification_gate_hardening",
            "source_provenance_overlay",
            "oracle_alignment_audit",
            "environment_synthesis_diagnosis",
            "third_repo_certification_diagnosis",
            "third_repo_local_pilot_grade_candidate",
            "third_repo_replacement_needed",
            "insufficient_evidence_for_predictive_validation",
        ],
        "disallowed_claims": [
            "predictive_validity_established",
            "future_holdout_predictive_validity",
            "production_benchmark_ranking",
            "pure_harness_effect",
            "humanize_benchmark_grade_if_commit_fallback_only",
            "third_repo_pilot_grade_if_unbalanced_or_under_certified",
        ],
        "recommended_next_runbook": recommended_next_runbook,
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
    }


def build_all_payloads(use_github: bool, run_environment_probes: bool, generated_at: str | None = None) -> dict[str, Any]:
    generated = generated_at or now_utc()
    config = default_hardening_config()
    plan = build_hardening_plan(generated)
    source_overlay = build_source_provenance_overlay(config, generated)
    humanize_rows, humanize_summary = build_humanize_hardened_sources(use_github=use_github, generated_at=generated)
    oracle_audit = build_oracle_alignment_audit(source_overlay, generated)
    environment = build_environment_synthesis_diagnosis(generated, run_environment_probes)
    candidate_filter = build_candidate_filter_audit(config, generated)
    hardened = build_hardened_certification_overlay(source_overlay, oracle_audit, candidate_filter, environment, generated)
    head = git_head()
    payloads = {
        "generated_at": generated,
        "starting_head": runbook_starting_head(),
        "final_head": head,
        "config": config,
        "plan": plan,
        "source_overlay": source_overlay,
        "humanize_hardened_rows": humanize_rows,
        "humanize_hardened_summary": humanize_summary,
        "oracle_alignment_audit": oracle_audit,
        "environment_synthesis_diagnosis": environment,
        "candidate_filter_audit": candidate_filter,
        "hardened_certification_overlay": hardened,
    }
    payloads["final_decision"] = build_final_decision(payloads, generated)
    return payloads


def table_counts(summary: dict[str, Any], keys: list[str]) -> list[str]:
    lines = ["| Repo | " + " | ".join(keys) + " |", "| --- | " + " | ".join("---:" for _ in keys) + " |"]
    for repo_id in REPOS:
        repo = summary.get(repo_id, {})
        lines.append("| `" + repo_id + "` | " + " | ".join(str(repo.get(key, 0)) for key in keys) + " |")
    return lines


def render_source_overlay_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Source Provenance Overlay",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "| Repo | Certified | Near-certified | Benchmark source | Manual source | Diagnostic source | Reject source |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for repo_id, summary in payload["repo_summary"].items():
        counts = summary["source_tier_counts"]
        lines.append(
            f"| `{repo_id}` | {summary['certified_count']} | {summary['near_certified_count']} | "
            f"{counts['benchmark_grade_source']} | {counts['manual_review_source']} | "
            f"{counts['diagnostic_only_source']} | {counts['reject_source']} |"
        )
    lines.extend(
        [
            "",
            "Humanize commit-message fallback remains diagnostic-only. Toolz remains eligible only where issue-derived problem context is present.",
        ]
    )
    return "\n".join(lines)


def render_humanize_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Humanize Source Hardening",
        "",
        f"Generated: `{summary['generated_at']}`.",
        "",
        f"- GitHub lookup attempted: `{str(summary['github_lookup_attempted']).lower()}`.",
        f"- Repaired to problem context: `{summary['repaired_to_problem_context_count']}`.",
        f"- Decision: `{summary['humanize_decision']}`.",
        "- Raw GitHub responses were not committed.",
        "- No paid LLM calls were made.",
        "",
        "| Hardened decision | Count |",
        "| --- | ---: |",
    ]
    for label, count in summary["decision_counts"].items():
        lines.append(f"| `{label}` | {count} |")
    return "\n".join(lines)


def render_oracle_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Oracle Alignment Audit",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "| Repo | Aligned | Manual review | Diagnostic-only | Reject | Top risk flags |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for repo_id, summary in payload["repo_summary"].items():
        counts = summary["status_counts"]
        top = ", ".join(f"{key}={value}" for key, value in summary["top_risk_flags"].items()) or "none"
        lines.append(
            f"| `{repo_id}` | {counts['aligned']} | {counts['manual_review_required']} | "
            f"{counts['diagnostic_only']} | {counts['reject']} | {top} |"
        )
    mismatch_count = payload["summary"]["risk_flag_counts"].get("statement_source_mismatch", 0)
    if mismatch_count:
        note = "Itsdangerous statements contain a repo-name mismatch that requires certification repair before benchmark use."
    else:
        note = "Itsdangerous statements no longer show a repo-name mismatch; remaining blockers are oracle, source-quality, or execution-gate risks."
    lines.extend(["", f"The audit distinguishes weak-oracle failures from wide and narrow oracle risks. {note}"])
    return "\n".join(lines)


def render_environment_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Environment Synthesis Diagnosis",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Environment probes run: `{str(payload['run_environment_probes']).lower()}`.",
        f"- Supported decisions: `{', '.join(payload['summary']['supported_decisions'])}`.",
        "- Raw command output was not committed; probe rows contain hashes, exit codes, and durations only.",
        "",
        "| Failure category | Count |",
        "| --- | ---: |",
    ]
    for label, count in payload["summary"]["failure_category_counts"].items():
        lines.append(f"| `{label}` | {count} |")
    lines.extend(["", "| Environment status | Count |", "| --- | ---: |"])
    for label, count in payload["summary"]["environment_status_counts"].items():
        lines.append(f"| `{label}` | {count} |")
    return "\n".join(lines)


def render_candidate_filter_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Candidate Filter Audit",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "| Repo | Candidates | Accepted | Manual review | Rejected | Remaining |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for repo_id, summary in payload["repo_summary"].items():
        lines.append(
            f"| `{repo_id}` | {summary['candidate_count']} | {summary['accepted_count']} | "
            f"{summary['manual_review_required_count']} | {summary['rejected_count']} | "
            f"{summary['remaining_after_filter_count']} |"
        )
    lines.append("")
    lines.append("Maintenance, dependency, deprecation, project-file, and oversized churn are flagged before certification.")
    return "\n".join(lines)


def render_hardened_overlay_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Hardened Certification Overlay",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "| Repo | Benchmark candidates | Manual review | Diagnostic-only | Rejected | Main blocking gates |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for repo_id, summary in payload["repo_summary"].items():
        blockers = ", ".join(f"{key}={value}" for key, value in summary["blocking_gates"].items()) or "none"
        lines.append(
            f"| `{repo_id}` | {summary['benchmark_grade_candidate_count']} | "
            f"{summary['manual_review_required_count']} | {summary['diagnostic_only_count']} | "
            f"{summary['rejected_count']} | {blockers} |"
        )
    lines.append("")
    lines.append("Benchmark-grade eligibility requires passing execution gates, benchmark-grade source, aligned oracle, clean environment, candidate-filter acceptance, and no solution exposure risk.")
    return "\n".join(lines)


def render_decision_report(payload: dict[str, Any]) -> str:
    its = payload["itsdangerous_decision"]
    lines = [
        "# Phase 1 Certification Hardening Decision",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"Primary decision: `{payload['primary_decision_label']}`.",
        "",
        "## Answers",
        "",
        f"- Humanize benchmark-grade after hardening: `no`; decision `{payload['humanize_decision']}` because certified tasks remain commit-message fallback unless repaired to non-leaky problem context.",
        f"- Itsdangerous failure mode: `{', '.join(its['supported_failure_modes'])}`.",
        f"- Third repo path: `{its['third_repo_decision']}`.",
        f"- Next runbook: `{payload['recommended_next_runbook']}`.",
        "",
        "The third-repo path must not proceed to paid ACUT scale-up unless local hardening yields enough benchmark-grade candidates. Current blockers are reported by the source, oracle, environment, and hardened-certification overlays.",
        "",
        "## Prohibited Claims",
        "",
    ]
    lines.extend(f"- `{claim}`" for claim in payload["disallowed_claims"])
    return "\n".join(lines)


def write_outputs(payloads: dict[str, Any]) -> None:
    config_path = PHASE1_ROOT / "configs" / "phase1_source_certification_hardening.yaml"
    write_text(config_path, "\n".join(render_yaml(payloads["config"])))
    write_json(PHASE1_ROOT / "results" / "phase1_source_certification_hardening_plan.json", payloads["plan"])
    write_json(PHASE1_ROOT / "results" / "phase1_source_provenance_overlay.json", payloads["source_overlay"])
    write_text(PHASE1_ROOT / "reports" / "phase1_source_provenance_overlay.md", render_source_overlay_report(payloads["source_overlay"]))
    write_jsonl(PHASE0_ROOT / "candidate_sources" / "humanize_hardened_source_context.jsonl", payloads["humanize_hardened_rows"])
    write_csv(
        PHASE0_ROOT / "candidate_sources" / "humanize_hardened_source_context_funnel.csv",
        payloads["humanize_hardened_rows"],
        [
            "task_id",
            "target_commit",
            "source_kind",
            "source_ref",
            "source_title",
            "source_body_digest",
            "source_url",
            "classification",
            "leakage_risk",
            "manual_review_required",
            "hardened_decision",
            "github_lookup_attempted",
            "github_lookup_status",
            "raw_github_response_committed",
        ],
    )
    write_text(PHASE1_ROOT / "reports" / "phase1_humanize_source_hardening.md", render_humanize_report(payloads["humanize_hardened_summary"]))
    write_json(PHASE1_ROOT / "results" / "phase1_oracle_alignment_audit.json", payloads["oracle_alignment_audit"])
    write_text(PHASE1_ROOT / "reports" / "phase1_oracle_alignment_audit.md", render_oracle_report(payloads["oracle_alignment_audit"]))
    write_json(PHASE1_ROOT / "results" / "phase1_environment_synthesis_diagnosis.json", payloads["environment_synthesis_diagnosis"])
    write_text(
        PHASE1_ROOT / "reports" / "phase1_environment_synthesis_diagnosis.md",
        render_environment_report(payloads["environment_synthesis_diagnosis"]),
    )
    write_json(PHASE1_ROOT / "results" / "phase1_candidate_filter_audit.json", payloads["candidate_filter_audit"])
    write_text(PHASE1_ROOT / "reports" / "phase1_candidate_filter_audit.md", render_candidate_filter_report(payloads["candidate_filter_audit"]))
    write_json(PHASE1_ROOT / "results" / "phase1_hardened_certification_overlay.json", payloads["hardened_certification_overlay"])
    write_text(
        PHASE1_ROOT / "reports" / "phase1_hardened_certification_overlay.md",
        render_hardened_overlay_report(payloads["hardened_certification_overlay"]),
    )
    write_json(PHASE1_ROOT / "results" / "phase1_certification_hardening_decision.json", payloads["final_decision"])
    write_text(PHASE1_ROOT / "reports" / "phase1_certification_hardening_decision.md", render_decision_report(payloads["final_decision"]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 1 source certification hardening overlays.")
    parser.add_argument("--skip-github", action="store_true", help="Skip GitHub metadata lookup for Humanize source repair.")
    parser.add_argument("--skip-environment-probes", action="store_true", help="Skip local Itsdangerous environment probes.")
    args = parser.parse_args()
    payloads = build_all_payloads(use_github=not args.skip_github, run_environment_probes=not args.skip_environment_probes)
    write_outputs(payloads)
    print(
        json.dumps(
            {
                "status": payloads["final_decision"]["primary_decision_label"],
                "humanize_decision": payloads["final_decision"]["humanize_decision"],
                "itsdangerous_decision": payloads["final_decision"]["itsdangerous_decision"]["third_repo_decision"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
