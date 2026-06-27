from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
PHASE1_ROOT = REPO_ROOT / "experiments" / "phase1_compiler"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT))


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def gh_authenticated() -> bool:
    if shutil.which("gh") is None:
        return False
    result = subprocess.run(["gh", "auth", "status"], cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    return result.returncode == 0


def fetch_github_pr_metadata(task_rows: list[dict[str, Any]], *, enabled: bool) -> list[dict[str, Any]]:
    if not enabled:
        return []
    sanitized = []
    for row in task_rows:
        commit = row.get("target_commit")
        if not commit:
            continue
        result = subprocess.run(
            [
                "gh",
                "api",
                f"repos/python-humanize/humanize/commits/{commit}/pulls",
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
            sanitized.append(
                {
                    "task_id": row["task_id"],
                    "target_commit": commit,
                    "status": "gh_api_error",
                    "stderr_digest": digest_text(result.stderr),
                }
            )
            continue
        try:
            pulls = json.loads(result.stdout)
        except json.JSONDecodeError:
            sanitized.append({"task_id": row["task_id"], "target_commit": commit, "status": "gh_api_invalid_json"})
            continue
        if not pulls:
            sanitized.append({"task_id": row["task_id"], "target_commit": commit, "status": "no_pull_request"})
            continue
        compact = []
        for pr in pulls[:3]:
            body = pr.get("body") or ""
            compact.append(
                {
                    "number": pr.get("number"),
                    "title": pr.get("title"),
                    "html_url": pr.get("html_url"),
                    "body_digest": digest_text(body),
                    "body_length": len(body),
                    "state": pr.get("state"),
                    "merged_at": pr.get("merged_at"),
                }
            )
        sanitized.append(
            {
                "task_id": row["task_id"],
                "target_commit": commit,
                "status": "pull_request_metadata_found",
                "pull_requests": compact,
            }
        )
    return sanitized


def context_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["task_id"]: row for row in rows}


def statement_index(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {row["task_id"]: str(row.get("solver_facing_statement") or "") for row in rows}


def has_issue_or_pr_context(context: dict[str, Any]) -> bool:
    if context.get("source_kind") in {"issue", "pull_request", "issue_or_pr"}:
        return True
    for item in context.get("source_items", []):
        if item.get("kind") in {"issue", "pull_request"} and item.get("solver_usable"):
            return True
    return False


def task_exposes_solution(context: dict[str, Any], statement: str) -> bool:
    source_kind = str(context.get("source_kind") or "")
    summary = str(context.get("summary") or context.get("problem_focus") or "").strip()
    if source_kind == "commit_message_fallback":
        return True
    if summary and summary.lower() in statement.lower() and any(verb in summary.lower() for verb in ["add ", "fix", "support", "append", "import"]):
        return True
    return False


def summarize_repo(repo_id: str, certified: list[dict[str, Any]], contexts: list[dict[str, Any]], statements: list[dict[str, Any]]) -> dict[str, Any]:
    by_context = context_index(contexts)
    by_statement = statement_index(statements)
    rows = []
    for row in certified:
        task_id = row["task_id"]
        context = by_context.get(task_id, {})
        source_kind = str(context.get("source_kind") or "missing")
        issue_or_pr = has_issue_or_pr_context(context)
        fallback = source_kind == "commit_message_fallback" or (not issue_or_pr and str(context.get("ref", "")).startswith("commit:"))
        missing = not bool(context)
        exposes = task_exposes_solution(context, by_statement.get(task_id, ""))
        rows.append(
            {
                "task_id": task_id,
                "target_commit": row.get("target_commit"),
                "source_kind": source_kind,
                "issue_or_pr_derived": issue_or_pr,
                "commit_message_fallback_only": fallback and not issue_or_pr,
                "missing_source_context": missing,
                "solver_statement_solution_exposure_risk": exposes,
            }
        )
    counts = Counter()
    for row in rows:
        counts["issue_or_pr_derived"] += int(row["issue_or_pr_derived"])
        counts["commit_message_fallback_only"] += int(row["commit_message_fallback_only"])
        counts["missing_source_context"] += int(row["missing_source_context"])
        counts["solver_statement_solution_exposure_risk"] += int(row["solver_statement_solution_exposure_risk"])
    return {
        "repo_id": repo_id,
        "certified_task_count": len(certified),
        "tasks_with_issue_or_pr_source_context": counts["issue_or_pr_derived"],
        "tasks_with_commit_message_fallback_only": counts["commit_message_fallback_only"],
        "tasks_with_missing_source_context": counts["missing_source_context"],
        "tasks_whose_solver_statement_appears_to_expose_solution": counts["solver_statement_solution_exposure_risk"],
        "task_audit": rows,
    }


def build_audit_payload(use_github: bool = True) -> dict[str, Any]:
    toolz_certified = read_jsonl(PHASE0_ROOT / "certified_tasks" / "toolz_certified_tasks.jsonl")
    humanize_certified = read_jsonl(PHASE0_ROOT / "certified_tasks" / "humanize_certified_tasks.jsonl")
    toolz_context = read_jsonl(PHASE0_ROOT / "candidate_sources" / "toolz_source_context.jsonl")
    humanize_context = read_jsonl(PHASE0_ROOT / "candidate_sources" / "humanize_source_context.jsonl")
    toolz_statements = read_jsonl(PHASE0_ROOT / "certified_tasks" / "toolz_task_statements.jsonl")
    humanize_statements = read_jsonl(PHASE0_ROOT / "certified_tasks" / "humanize_task_statements.jsonl")
    github_enabled = use_github and gh_authenticated()
    github_metadata = fetch_github_pr_metadata(humanize_certified, enabled=github_enabled)
    non_fallback_pr_count = sum(1 for row in github_metadata if row.get("status") == "pull_request_metadata_found")

    repos = [
        summarize_repo("toolz", toolz_certified, toolz_context, toolz_statements),
        summarize_repo("humanize", humanize_certified, humanize_context, humanize_statements),
    ]
    humanize_status = (
        "humanize_source_provenance_hardened"
        if non_fallback_pr_count >= 6
        else "humanize_source_provenance_fallback_confirmed"
    )
    return {
        "schema_version": "barcarolle.phase1.source_provenance_audit.v1",
        "generated_at": now_utc(),
        "claim_scope": "source_provenance_audited",
        "predictive_validity_established": False,
        "source_files": [
            rel(PHASE0_ROOT / "candidate_sources" / "toolz_source_context.jsonl"),
            rel(PHASE0_ROOT / "candidate_sources" / "humanize_source_context.jsonl"),
            rel(PHASE0_ROOT / "certified_tasks" / "toolz_certified_tasks.jsonl"),
            rel(PHASE0_ROOT / "certified_tasks" / "humanize_certified_tasks.jsonl"),
        ],
        "github_metadata_attempted": github_enabled,
        "github_metadata": github_metadata,
        "github_pull_request_metadata_count": non_fallback_pr_count,
        "repos": repos,
        "humanize_source_provenance_status": humanize_status,
        "no_raw_github_responses_committed": True,
        "no_paid_llm_calls_made": True,
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Source Provenance Audit",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- GitHub metadata attempted: `{str(payload['github_metadata_attempted']).lower()}`.",
        f"- Humanize provenance status: `{payload['humanize_source_provenance_status']}`.",
        f"- Humanize PR metadata count: `{payload['github_pull_request_metadata_count']}`.",
        "- No raw GitHub responses were committed.",
        "- No paid LLM call was made.",
        "",
        "| Repo | Certified | Issue/PR context | Commit fallback only | Missing context | Statement exposure risk |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for repo in payload["repos"]:
        lines.append(
            f"| `{repo['repo_id']}` | {repo['certified_task_count']} | "
            f"{repo['tasks_with_issue_or_pr_source_context']} | "
            f"{repo['tasks_with_commit_message_fallback_only']} | "
            f"{repo['tasks_with_missing_source_context']} | "
            f"{repo['tasks_whose_solver_statement_appears_to_expose_solution']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Toolz remains issue-derived through the repaired source adapter. "
            "Humanize remains commit-message-fallback provenance unless GitHub commit-to-PR metadata supplies at least six non-fallback matches. "
            "This audit is sufficient for an operational pilot but not for validation-grade claims.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Phase 1 source provenance.")
    parser.add_argument("--no-github", action="store_true", help="Skip GitHub metadata lookup.")
    args = parser.parse_args()
    payload = build_audit_payload(use_github=not args.no_github)
    write_json(PHASE1_ROOT / "results" / "phase1_source_provenance_audit.json", payload)
    write_text(PHASE1_ROOT / "reports" / "phase1_source_provenance_audit.md", render_report(payload))
    print(json.dumps({"status": payload["humanize_source_provenance_status"], "github_pr_count": payload["github_pull_request_metadata_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
