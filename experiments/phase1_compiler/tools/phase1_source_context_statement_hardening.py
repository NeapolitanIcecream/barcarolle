from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "phase1_source_context_statement_hardening.yaml"
SCHEMA_VERSION = "barcarolle.phase1_source_context_statement_hardening.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_source_context_statement_hardening_output.v1"
RUN_ID = "phase1_source_context_statement_hardening_20260528"
REPO_ORDER = ("attrs", "boltons", "click")
RELEVANT_REPOS = set(REPO_ORDER)
FORBIDDEN_RAW_MARKERS = (
    "diff --git",
    "\n@@",
    "raw_api_payload",
    "raw_completion",
    "hidden verifier",
    "verified_pass",
    "verified_fail",
)
HEX40_RE = re.compile(r"\b[0-9a-f]{40}\b")

ALLOWED_SOURCE_CONTEXT_TYPE_BUCKETS = {
    "issue_or_pr",
    "public_docs_or_changelog",
    "reviewed_diff_assisted",
    "commit_message_only",
    "title_only",
    "unknown",
}
ALLOWED_SOURCE_QUALITY_BUCKETS = {"clean", "minor_risk", "diagnostic_only", "blocked"}
ALLOWED_STATEMENT_SPECIFICITY_BUCKETS = {"specific", "acceptable", "thin", "missing"}
ALLOWED_CONTEXT_LENGTH_BUCKETS = {"short", "medium", "long", "unknown"}
ALLOWED_EDITABLE_SCOPE_BUCKETS = {"single_module", "multi_module", "project_wide", "unknown"}
ALLOWED_RISK_BUCKETS = {"low", "minor_risk", "high", "blocked", "unknown"}
ALLOWED_CERTIFICATION_RISK_BUCKETS = {
    "technical_certified_release_eligible",
    "technical_certified_source_review_needed",
    "not_technical_certified",
    "unknown",
}
ALLOWED_REVIEW_VERDICTS = {
    "promote_release_eligible",
    "keep_release_eligible",
    "keep_diagnostic_only",
    "reject_solution_exposure_risk",
    "reject_ambiguous_scope",
    "reject_missing_public_problem_context",
    "reject_certification_inconsistent",
}


TITLE_ONLY_PUBLIC_SUMMARIES: dict[str, str] = {
    "attrs__v2__056": "The public PR title only says repr output should be fixed, without enough behavior detail to define the exact representation contract.",
    "click__third__045": "Shell completion should expose the --help option where users expect completion candidates.",
    "click__third__050": "The BOOL parameter type should accept on and off strings in addition to existing boolean spellings.",
    "click__third__091": "Progress bars should avoid rendering so frequently that output becomes noisy or inefficient.",
    "click__third__109": "A bad parameter default should produce a clearer error when a multi-value parameter receives a single default.",
    "click__third__166": "shell_completion.add_completion_class should have the documented return value and type behavior.",
    "click__third__197": "Choice option metavars should be formatted correctly when show_choices is disabled.",
    "click__third__198": "Default values should stay hidden when show_default is false.",
    "click__third__199": "Help metadata generation and rendering should be separated so extra help items render consistently.",
    "click__third__200": "CliRunner results should preserve the observed mix of stdout and stderr streams.",
    "click__third__201": "Environment variable hints should appear in relevant parameter error messages.",
    "click__third__202": "Callbacks registered for CLI execution should be closed correctly when the CLI exits.",
    "click__third__203": "Progress bars should support being hidden without disrupting surrounding termui behavior.",
    "click__third__204": "Overriding a Parameter by name should produce a UserWarning.",
    "click__third__205": "Flag values supplied through envvar handling should be set correctly.",
    "click__third__206": "Choice failures should have a dedicated failure path that preserves useful error behavior.",
    "click__third__207": "Help shown because no_args_is_help is enabled should exit with status 2 instead of 0.",
    "click__third__208": "Contexts created during shell completion should be closed after completion handling.",
    "click__third__213": "Deprecated Parameter and Command objects should support customizable deprecation messages.",
    "click__third__214": "Generated help options configured through help_option_names should preserve the right eager behavior.",
    "click__third__216": "CliRunner should expose a default catch_exceptions parameter for invocation behavior.",
    "click__third__217": "flag_value should only be set for options that are actually flags.",
    "click__third__220": "Choice token normalization should cover more choice values and work with generic typing.",
    "click__third__234": "Zsh shell completion should handle completion values containing colons.",
    "click__third__238": "Fish shell completion should handle quoted or escaped parameter values.",
    "click__third__250": "Optional flag values should be interpreted correctly for option parsing.",
    "click__third__271": "Readline prompts on Linux should handle backspace and line wrapping correctly.",
    "click__third__274": "Fish completion output should handle multiline help strings correctly.",
    "click__third__275": "Unknown command handling should provide a NoSuchCommand error with suggestions for misspelled commands.",
    "click__third__278": "FuncParamType failures should preserve the ValueError message in Click's failure output.",
    "click__third__288": "Shell completion output should use Unix line endings for compatibility with Windows consumers.",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: str | Path) -> Path:
    raw = Path(str(path))
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
        raise ValueError("unexpected source context hardening config schema_version")
    config["_path"] = str(path)
    return config


def input_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["inputs"][key])


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


def external_repo_path(config: dict[str, Any], repo_id: str) -> Path:
    return repo_path(config["external_repos"].get(repo_id, ""))


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


def digest_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def digest_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def count_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "unknown") for row in rows).items()))


def count_by_repo(rows: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, int]]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        counters[str(row.get("repo") or "unknown")][str(row.get(key) or "unknown")] += 1
    return {repo: dict(sorted(counter.items())) for repo, counter in sorted(counters.items())}


def count_repos(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("repo") or "unknown") for row in rows).items()))


def sorted_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (REPO_ORDER.index(row["repo"]) if row.get("repo") in REPO_ORDER else 99, str(row.get("task_id"))))


def source_context_type_bucket(source_context_type: str) -> str:
    if source_context_type in {"issue_or_pr_context", "public_issue_and_pr_context_repaired"}:
        return "issue_or_pr"
    if source_context_type == "pr_context_title_only":
        return "title_only"
    if source_context_type == "commit_message_only_context":
        return "commit_message_only"
    return "unknown"


def editable_scope_bucket(files: list[str]) -> str:
    if not files:
        return "unknown"
    if len(files) == 1:
        return "single_module"
    if len(files) <= 3:
        return "multi_module"
    return "project_wide"


def context_length_bucket(length: int | None) -> str:
    if length is None or length <= 0:
        return "unknown"
    if length < 120:
        return "short"
    if length < 500:
        return "medium"
    return "long"


def statement_specificity_bucket(row: dict[str, Any]) -> str:
    source_type = row.get("source_context_type") or row.get("source_context_class") or ""
    source_quality = row.get("source_context_quality") or ""
    if source_quality == "public_context_repaired":
        return "specific"
    if source_type == "issue_or_pr_context":
        return "acceptable"
    if source_type == "pr_context_title_only":
        return "thin"
    if source_type == "commit_message_only_context":
        return "missing"
    return "missing"


def source_quality_bucket(row: dict[str, Any]) -> str:
    quality = row.get("source_context_quality") or ""
    source_type = row.get("source_context_type") or row.get("source_context_class") or ""
    if quality in {"non_leaky_issue_or_pr_context", "public_context_repaired"}:
        return "clean"
    if source_type == "pr_context_title_only" or quality == "pr_title_only_context":
        return "minor_risk"
    if source_type == "commit_message_only_context" or quality == "commit_message_only_context":
        return "blocked"
    return "diagnostic_only"


def ambiguity_risk_bucket(row: dict[str, Any]) -> str:
    source_type = row.get("source_context_type") or row.get("source_context_class") or ""
    if row.get("task_id") == "attrs__v2__056":
        return "high"
    if source_type == "pr_context_title_only":
        return "minor_risk"
    if source_type == "commit_message_only_context":
        return "blocked"
    return "low"


def leakage_risk_bucket(row: dict[str, Any]) -> str:
    source_type = row.get("source_context_type") or row.get("source_context_class") or ""
    if source_type == "commit_message_only_context":
        return "high"
    if source_type == "pr_context_title_only":
        return "minor_risk"
    return "low"


def certification_risk_bucket(row: dict[str, Any]) -> str:
    if row.get("technical_certified") is not True:
        return "not_technical_certified"
    if row.get("release_eligible_before") is True:
        return "technical_certified_release_eligible"
    return "technical_certified_source_review_needed"


def material_leakage_risk(row: dict[str, Any]) -> str:
    return "minor_risk" if row.get("commit_message_only_context") else "none_detected"


def coarse_task_family(repo_id: str, files: list[str], fallback: str = "") -> str:
    if fallback:
        return fallback
    if not files:
        return f"{repo_id}:unknown"
    first = files[0].replace("\\", "/")
    parts = [part for part in first.split("/") if part not in {"src", repo_id}]
    if not parts:
        return f"{repo_id}:unknown"
    return f"{repo_id}:{parts[0].removesuffix('.py')}"


def git_public_subject(config: dict[str, Any], repo_id: str, commit: str | None) -> str:
    if not commit:
        return ""
    repo_dir = external_repo_path(config, repo_id)
    if not repo_dir.exists():
        return ""
    try:
        output = subprocess.check_output(
            ["git", "show", "-s", "--format=%s", commit],
            cwd=repo_dir,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return " ".join(output.split())


def sanitized_public_summary(config: dict[str, Any], row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    task_id = str(row["task_id"])
    curated = TITLE_ONLY_PUBLIC_SUMMARIES.get(task_id)
    raw_subject = ""
    if not curated:
        raw_subject = git_public_subject(config, str(row["repo"]), row.get("target_commit_optional") or row.get("target_commit"))
        if raw_subject:
            curated = f"Public commit or PR title says: {raw_subject}"
    if not curated:
        curated = "No non-leaky public problem summary is available from committed metadata."
    return curated, {
        "summary_digest": digest_text(curated),
        "raw_subject_digest_optional": digest_text(raw_subject) if raw_subject else "",
        "raw_subject_committed": False,
        "target_commit_exposed": False,
    }


def load_paid_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    return rows_from_payload(read_json(input_path(config, "paid_task_table")))


def split_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    payload = read_json(input_path(config, "paid_split_plan"), {})
    return {str(row["candidate_id"]): row for row in payload.get("assignments", [])}


def source_audit_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    payload = read_json(input_path(config, "paid_source_quality_audit"), {})
    return {str(row["candidate_id"]): row for row in payload.get("rows", [])}


def fresh_attempts_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    payload = read_json(input_path(config, "fresh_certification_attempts"), {})
    return {str(row["candidate_id"]): row for row in payload.get("rows", [])}


def third_attempts_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    payload = read_json(input_path(config, "third_repo_certification_attempts"), {})
    return {str(row["candidate_id"]): row for row in payload.get("rows", [])}


def relevant_queue_rows(config: dict[str, Any], paid_ids: set[str]) -> list[dict[str, Any]]:
    queue_payload = read_json(input_path(config, "fresh_source_review_queue"), {})
    attempts = fresh_attempts_by_id(config)
    rows: list[dict[str, Any]] = []
    for queue_row in queue_payload.get("rows", []):
        repo_id = str(queue_row.get("repo_id") or "")
        task_id = str(queue_row.get("candidate_id") or "")
        if repo_id not in {"attrs", "boltons"}:
            continue
        if task_id in paid_ids:
            continue
        attempt = attempts.get(task_id, {})
        merged = {**attempt, **queue_row}
        merged["_inventory_role"] = "source_review_queue"
        rows.append(merged)

    for task_id, attempt in third_attempts_by_id(config).items():
        if task_id in paid_ids:
            continue
        if attempt.get("repo_id") != "click":
            continue
        if attempt.get("technical_certified") is not True or attempt.get("release_eligible") is True:
            continue
        if attempt.get("source_context_class") != "commit_message_only_context":
            continue
        merged = dict(attempt)
        merged["_inventory_role"] = "source_review_queue"
        rows.append(merged)
    return rows


def inventory_row_from_paid(config: dict[str, Any], paid_row: dict[str, Any]) -> dict[str, Any]:
    task_id = str(paid_row["candidate_id"])
    repo_id = str(paid_row["repo_id"])
    split = split_by_id(config).get(task_id, {})
    audit = source_audit_by_id(config).get(task_id, {})
    impl_files = list(paid_row.get("implementation_files") or [])
    source_type = str(paid_row.get("source_context_class") or audit.get("source_context_class") or "unknown")
    source_quality = str(paid_row.get("source_context_quality") or audit.get("source_context_quality") or "unknown")
    technical_profile = paid_row.get("technical_certification_profile") or {}
    title_only = source_type == "pr_context_title_only" or source_quality == "pr_title_only_context"
    commit_only = source_type == "commit_message_only_context" or source_quality == "commit_message_only_context"
    row = {
        "task_id": task_id,
        "repo": repo_id,
        "source_reservoir": paid_row.get("source_reservoir", "unknown"),
        "inventory_role": "paid_package",
        "split_label": split.get("split", ""),
        "release_eligible_before": True,
        "technical_certified": bool(technical_profile.get("technical_certified")),
        "statement_source": audit.get("statement_provenance") or paid_row.get("release_eligibility_provenance", "unknown"),
        "source_context_type": source_type,
        "source_context_quality": source_quality,
        "title_only_context": title_only,
        "commit_message_only_context": commit_only,
        "public_issue_or_pr_context": source_type in {"issue_or_pr_context", "pr_context_title_only", "public_issue_and_pr_context_repaired"},
        "public_context_ref_count": paid_row.get("public_context_ref_count", 0),
        "implementation_files": impl_files,
        "test_files": list(paid_row.get("test_files") or []),
        "raw_statement_text_committed": bool(audit.get("raw_statement_text_committed", False)),
        "raw_diff_committed": bool(paid_row.get("raw_diff_committed", False)),
        "target_commit_exposed": False,
        "task_time_bucket": paid_row.get("task_time_bucket", "unknown"),
        "coarse_task_family": coarse_task_family(repo_id, impl_files, str(paid_row.get("task_family") or "")),
    }
    row.update(
        {
            "material_leakage_risk": material_leakage_risk(row),
            "statement_specificity_bucket": statement_specificity_bucket(row),
            "statement_length_bucket": "unknown",
            "editable_scope_bucket": editable_scope_bucket(impl_files),
            "ambiguity_risk_bucket": ambiguity_risk_bucket(row),
            "leakage_risk_bucket": leakage_risk_bucket(row),
            "certification_risk_bucket": certification_risk_bucket(row),
        }
    )
    return row


def inventory_row_from_queue(queue_row: dict[str, Any]) -> dict[str, Any]:
    task_id = str(queue_row["candidate_id"])
    repo_id = str(queue_row["repo_id"])
    impl_files = list(queue_row.get("implementation_files") or [])
    source_type = str(queue_row.get("source_context_class") or "commit_message_only_context")
    source_quality = str(queue_row.get("source_context_quality") or source_type)
    row = {
        "task_id": task_id,
        "repo": repo_id,
        "source_reservoir": queue_row.get("source_reservoir", "unknown"),
        "inventory_role": queue_row.get("_inventory_role", "source_review_queue"),
        "split_label": "",
        "release_eligible_before": False,
        "technical_certified": bool(queue_row.get("technical_certified")),
        "statement_source": "source_review_queue",
        "source_context_type": source_type,
        "source_context_quality": source_quality,
        "title_only_context": source_type == "pr_context_title_only" or source_quality == "pr_title_only_context",
        "commit_message_only_context": source_type == "commit_message_only_context" or source_quality == "commit_message_only_context",
        "public_issue_or_pr_context": source_type in {"issue_or_pr_context", "pr_context_title_only", "public_issue_and_pr_context_repaired"},
        "public_context_ref_count": len(queue_row.get("allowed_context_refs") or queue_row.get("public_context_refs") or []),
        "implementation_files": impl_files,
        "test_files": list(queue_row.get("test_files") or []),
        "raw_statement_text_committed": False,
        "raw_diff_committed": False,
        "target_commit_exposed": False,
        "task_time_bucket": "unknown",
        "coarse_task_family": coarse_task_family(repo_id, impl_files),
    }
    row.update(
        {
            "material_leakage_risk": material_leakage_risk(row),
            "statement_specificity_bucket": statement_specificity_bucket(row),
            "statement_length_bucket": "unknown",
            "editable_scope_bucket": editable_scope_bucket(impl_files),
            "ambiguity_risk_bucket": ambiguity_risk_bucket(row),
            "leakage_risk_bucket": leakage_risk_bucket(row),
            "certification_risk_bucket": certification_risk_bucket(row),
        }
    )
    return row


def build_inventory(config: dict[str, Any]) -> dict[str, Any]:
    paid_rows = load_paid_rows(config)
    paid_ids = {str(row["candidate_id"]) for row in paid_rows}
    inventory_rows = [inventory_row_from_paid(config, row) for row in paid_rows]
    inventory_rows.extend(inventory_row_from_queue(row) for row in relevant_queue_rows(config, paid_ids))
    inventory_rows = sorted_rows(inventory_rows)
    release_eligible_rows = [row for row in inventory_rows if row["release_eligible_before"]]
    technical_rows = [row for row in inventory_rows if row["technical_certified"]]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "inventory",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": config.get("created_at", now_utc()),
        "scope": "attrs_boltons_click_paid_package_plus_relevant_source_review_queue",
        "task_count": len(inventory_rows),
        "paid_package_task_count": len(paid_rows),
        "source_review_queue_task_count": len(inventory_rows) - len(paid_rows),
        "release_eligible_before_count": len(release_eligible_rows),
        "technical_certified_count": len(technical_rows),
        "release_eligible_before_count_by_repo": count_repos(release_eligible_rows),
        "technical_certified_count_by_repo": count_repos(technical_rows),
        "source_context_quality_counts_by_repo": count_by_repo(inventory_rows, "source_context_quality"),
        "source_context_type_counts_by_repo": count_by_repo(inventory_rows, "source_context_type"),
        "source_quality_bucket_counts_by_repo": count_by_repo([{**row, "source_quality_bucket": source_quality_bucket(row)} for row in inventory_rows], "source_quality_bucket"),
        "title_only_context_count": sum(1 for row in inventory_rows if row["title_only_context"]),
        "commit_message_only_context_count": sum(1 for row in inventory_rows if row["commit_message_only_context"]),
        "diagnostic_outcome_joined": False,
        "outcome_labels_used_for_promotion": False,
        "raw_hidden_oracle_material_committed": False,
        "rows": inventory_rows,
    }
    return payload


def write_inventory_report(config: dict[str, Any], inventory: dict[str, Any]) -> None:
    lines = [
        "# Source Context Statement Hardening Inventory",
        "",
        "## What Happened",
        "",
        f"The inventory covers {inventory['paid_package_task_count']} frozen paid-package tasks and "
        f"{inventory['source_review_queue_task_count']} directly relevant source-review queue tasks for attrs, boltons, and click.",
        "",
        f"Release-eligible before this overlay: {inventory['release_eligible_before_count']}. "
        f"Technical-certified rows in scope: {inventory['technical_certified_count']}. These counts are separate.",
        "",
        f"Title-only context rows: {inventory['title_only_context_count']}. "
        f"Commit-message-only context rows: {inventory['commit_message_only_context_count']}.",
        "",
        "## Why It Matters",
        "",
        "Title-only and commit-message-only source context can make a task look usable while still leaving the solver with a weak problem statement. The inventory makes that risk explicit before any future split design consumes the pool.",
        "",
        "## Counts By Repo And Source Quality",
        "",
    ]
    for repo in REPO_ORDER:
        counts = inventory["source_context_quality_counts_by_repo"].get(repo, {})
        lines.append(f"- {repo}: {counts}")
    lines.extend(
        [
            "",
            "## Action This Suggests",
            "",
            "Build a deterministic repair queue from title-only and commit-message-only rows. Keep completed paid outcomes out of repair priority and promotion decisions.",
            "",
            "## Hygiene",
            "",
            "- Diagnostic paid outcomes were not joined into the inventory rows.",
            "- Raw hidden oracle material committed: false.",
            "- Raw target diffs committed: false.",
        ]
    )
    write_text(report_path(config, "inventory"), "\n".join(lines))


def repair_labels_for_inventory_row(row: dict[str, Any]) -> list[str]:
    if row.get("title_only_context"):
        return ["needs_public_context_repair", "needs_statement_specificity_review", "needs_leakage_review", "needs_scope_review"]
    if row.get("commit_message_only_context"):
        return ["needs_public_context_repair", "needs_diff_assisted_statement_review", "needs_leakage_review", "needs_scope_review"]
    if row.get("source_context_quality") == "public_context_repaired":
        return ["no_repair_needed"]
    return ["no_repair_needed"]


def build_repair_queue(config: dict[str, Any], inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = inventory or read_json(output_path(config, "inventory"), build_inventory(config))
    queue_rows: list[dict[str, Any]] = []
    for row in inventory["rows"]:
        labels = repair_labels_for_inventory_row(row)
        if labels == ["no_repair_needed"] and row.get("source_context_quality") != "public_context_repaired":
            continue
        priority = 0
        if row.get("inventory_role") == "paid_package":
            priority += 100
        if row.get("title_only_context"):
            priority += 50
        if row.get("commit_message_only_context"):
            priority += 25
        queue_rows.append(
            {
                "task_id": row["task_id"],
                "repo": row["repo"],
                "inventory_role": row["inventory_role"],
                "release_eligible_before": row["release_eligible_before"],
                "technical_certified": row["technical_certified"],
                "source_context_type": row["source_context_type"],
                "source_context_quality": row["source_context_quality"],
                "primary_queue_label": labels[0],
                "queue_labels": labels,
                "stable_priority": -priority,
                "repair_priority_reason": (
                    "paid_package_title_only" if row.get("title_only_context") and row.get("inventory_role") == "paid_package"
                    else "technical_certified_commit_message_only"
                    if row.get("commit_message_only_context")
                    else "preexisting_public_context_repair"
                ),
                "paid_outcome_used_for_priority": False,
                "repair_blocker_if_not_repaired": "missing_public_problem_context" if row.get("commit_message_only_context") else "",
            }
        )
    queue_rows.sort(key=lambda row: (row["stable_priority"], REPO_ORDER.index(row["repo"]) if row["repo"] in REPO_ORDER else 99, row["task_id"]))
    for index, row in enumerate(queue_rows, start=1):
        row["stable_order"] = index
        row.pop("stable_priority", None)
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "repair_queue",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": config.get("created_at", now_utc()),
        "queue_count": len(queue_rows),
        "queue_count_by_repo": count_repos(queue_rows),
        "primary_queue_label_counts": count_by(queue_rows, "primary_queue_label"),
        "policy": {
            "release_eligible_separate_from_technical_certified": True,
            "commit_message_only_requires_promoted_review": True,
            "title_only_requires_review": True,
            "outcome_labels_can_promote_or_demote": False,
            "H_future_outcomes_can_promote_or_demote": False,
            "adapter_pass_fail_labels_can_promote_or_demote": False,
            "diff_assisted_repair_requires_review": True,
        },
        "thresholds": config.get("thresholds", {}),
        "rows": queue_rows,
    }
    return payload


def attrs_repair_packets_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    payload = read_json(input_path(config, "attrs_source_repair_statement_packets"), {})
    return {str(row["candidate_id"]): row for row in payload.get("statement_packets", [])}


def build_statement_packets(config: dict[str, Any], inventory: dict[str, Any] | None = None, queue: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = inventory or read_json(output_path(config, "inventory"), build_inventory(config))
    queue = queue or read_json(output_path(config, "repair_queue"), build_repair_queue(config, inventory))
    inventory_by_id = {row["task_id"]: row for row in inventory["rows"]}
    attrs_packets = attrs_repair_packets_by_id(config)
    packets: list[dict[str, Any]] = []
    for queue_row in queue["rows"]:
        row = inventory_by_id[queue_row["task_id"]]
        public_summary, summary_meta = sanitized_public_summary(config, row)
        source_refs = [f"public_context_ref_count:{row.get('public_context_ref_count', 0)}"]
        if row["task_id"] in attrs_packets:
            packet = attrs_packets[row["task_id"]]
            problem_summary = packet.get("statement_summary", {}).get("problem_summary", public_summary)
            expected_behavior = packet.get("statement_summary", {}).get("expected_behavior", "")
            public_summary = f"{problem_summary} {expected_behavior}".strip()
            source_refs = [packet.get("primary_ref", ""), *packet.get("secondary_refs", [])]
            repair_mode = "preexisting_public_context_repair"
            packet_status = "ready_for_review"
            blocked_reason = ""
        elif row.get("commit_message_only_context"):
            repair_mode = "blocked_missing_public_problem_context"
            packet_status = "blocked"
            blocked_reason = "missing_public_problem_context"
        else:
            repair_mode = "public_title_context_review"
            packet_status = "ready_for_review"
            blocked_reason = ""
        solver_summary = (
            "No solver-visible repaired statement is approved because public problem context is missing."
            if packet_status == "blocked"
            else public_summary
        )
        packet_row = {
            "task_id": row["task_id"],
            "repo": row["repo"],
            "inventory_role": row["inventory_role"],
            "repair_mode": repair_mode,
            "packet_status": packet_status,
            "solver_visible_problem_summary": solver_summary,
            "allowed_public_context_summary": public_summary if packet_status != "blocked" else "",
            "editable_scope_summary": f"Editable implementation scope bucket: {row['editable_scope_bucket']}; implementation paths: {', '.join(row.get('implementation_files') or ['unknown'])}.",
            "non_solver_visible_review_notes": (
                "Commit-message-only context remains excluded unless a separate non-leaky public problem statement is reviewed."
                if row.get("commit_message_only_context")
                else "Title-only context remains at least minor risk unless review records a specific, non-leaky problem statement."
                if row.get("title_only_context")
                else "Preexisting public context repair imported from the attrs source repair overlay."
            ),
            "source_references_or_digests": [ref for ref in source_refs if ref],
            "source_summary_digest": summary_meta["summary_digest"],
            "raw_subject_digest_optional": summary_meta["raw_subject_digest_optional"],
            "leakage_review_required": True,
            "ambiguity_review_required": True,
            "scope_review_required": True,
            "diff_assisted": False,
            "raw_public_api_response_committed": False,
            "raw_prompt_or_completion_committed": False,
            "target_commit_exposed": False,
            "blocked_reason": blocked_reason,
        }
        packets.append(packet_row)
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "statement_packets",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": config.get("created_at", now_utc()),
        "packet_count": len(packets),
        "packet_status_counts": count_by(packets, "packet_status"),
        "repair_mode_counts": count_by(packets, "repair_mode"),
        "paid_llm_calls_made": 0,
        "raw_public_api_responses_committed": False,
        "raw_prompts_or_completions_committed": False,
        "rows": sorted_rows(packets),
    }
    return payload


def review_packet(packet: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    if packet["packet_status"] == "blocked":
        verdict = "reject_missing_public_problem_context"
        release_after = False
        source_quality_after = "blocked"
        specificity_after = "missing"
        leakage_after = "high"
        ambiguity_after = "blocked"
        scope_after = row.get("editable_scope_bucket", "unknown")
        reasons = ["No non-leaky public issue or PR problem context is available in committed metadata."]
    elif row["task_id"] == "attrs__v2__056":
        verdict = "reject_ambiguous_scope"
        release_after = False
        source_quality_after = "diagnostic_only"
        specificity_after = "thin"
        leakage_after = "minor_risk"
        ambiguity_after = "high"
        scope_after = row.get("editable_scope_bucket", "unknown")
        reasons = ["The only public title says reprs should be fixed; that is too thin to define the user-visible representation contract."]
    elif row.get("title_only_context"):
        verdict = "keep_release_eligible" if row.get("release_eligible_before") else "keep_diagnostic_only"
        release_after = bool(row.get("release_eligible_before"))
        source_quality_after = "minor_risk"
        specificity_after = "acceptable"
        leakage_after = "minor_risk"
        ambiguity_after = "minor_risk"
        scope_after = row.get("editable_scope_bucket", "unknown")
        reasons = ["The public title summary plus implementation scope gives a bounded problem statement, but title-only provenance remains minor risk."]
    else:
        verdict = "keep_release_eligible" if row.get("release_eligible_before") else "promote_release_eligible"
        release_after = True
        source_quality_after = "clean"
        specificity_after = "specific"
        leakage_after = "low"
        ambiguity_after = "low"
        scope_after = row.get("editable_scope_bucket", "unknown")
        reasons = ["A prior public-context repair already recorded a non-leaky solver-visible problem summary and review."]
    return {
        "task_id": row["task_id"],
        "repo": row["repo"],
        "review_verdict": verdict,
        "release_eligible_before": row.get("release_eligible_before"),
        "release_eligible_after_overlay": release_after,
        "source_quality_before": row.get("source_context_quality"),
        "source_quality_after_overlay": source_quality_after,
        "statement_specificity_after_overlay": specificity_after,
        "leakage_risk_after_overlay": leakage_after,
        "ambiguity_risk_after_overlay": ambiguity_after,
        "scope_clarity_after_overlay": scope_after,
        "review_reasons": reasons,
        "paid_outcome_used_for_verdict": False,
        "exposes_target_commit": False,
        "exposes_patch_or_raw_tests": False,
        "exposes_hidden_oracle_text": False,
        "contains_implementation_recipe": False,
    }


def build_review_records(config: dict[str, Any], inventory: dict[str, Any] | None = None, packets: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = inventory or read_json(output_path(config, "inventory"), build_inventory(config))
    packets = packets or read_json(output_path(config, "statement_packets"), build_statement_packets(config, inventory))
    inventory_by_id = {row["task_id"]: row for row in inventory["rows"]}
    records = [review_packet(packet, inventory_by_id[packet["task_id"]]) for packet in packets["rows"]]
    records = sorted_rows(records)
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "review_records",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": config.get("created_at", now_utc()),
        "review_count": len(records),
        "review_verdict_counts": count_by(records, "review_verdict"),
        "paid_llm_review_calls_made": 0,
        "paid_outcomes_used_for_verdicts": False,
        "rows": records,
    }
    return payload


def build_overlay(config: dict[str, Any], inventory: dict[str, Any] | None = None, reviews: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = inventory or read_json(output_path(config, "inventory"), build_inventory(config))
    reviews = reviews or read_json(output_path(config, "review_records"), build_review_records(config, inventory))
    review_by_id = {row["task_id"]: row for row in reviews["rows"]}
    overlay_rows: list[dict[str, Any]] = []
    for row in inventory["rows"]:
        review = review_by_id.get(row["task_id"])
        if review:
            release_after = review["release_eligible_after_overlay"]
            quality_after = review["source_quality_after_overlay"]
            specificity_after = review["statement_specificity_after_overlay"]
            leakage_after = review["leakage_risk_after_overlay"]
            ambiguity_after = review["ambiguity_risk_after_overlay"]
            verdict = review["review_verdict"]
            exclusion_reason = "" if release_after else {
                "reject_ambiguous_scope": "ambiguous_scope",
                "reject_missing_public_problem_context": "missing_public_problem_context",
                "reject_solution_exposure_risk": "solution_exposure_risk",
                "reject_certification_inconsistent": "certification_inconsistent",
            }.get(verdict, "statement_too_thin")
        else:
            release_after = bool(row["release_eligible_before"])
            quality_after = source_quality_bucket(row)
            specificity_after = row["statement_specificity_bucket"]
            leakage_after = row["leakage_risk_bucket"]
            ambiguity_after = row["ambiguity_risk_bucket"]
            verdict = "not_reviewed_no_repair_needed"
            exclusion_reason = "" if release_after else "not_release_eligible_before_overlay"
        overlay_rows.append(
            {
                "task_id": row["task_id"],
                "repo": row["repo"],
                "inventory_role": row["inventory_role"],
                "review_verdict": verdict,
                "release_eligible_before": row["release_eligible_before"],
                "release_eligible_after_overlay": release_after,
                "source_quality_bucket_before": source_quality_bucket(row),
                "source_quality_bucket_after_overlay": quality_after,
                "statement_specificity_bucket_after_overlay": specificity_after,
                "leakage_risk_bucket_after_overlay": leakage_after,
                "ambiguity_risk_bucket_after_overlay": ambiguity_after,
                "scope_bucket_after_overlay": row["editable_scope_bucket"],
                "exclusion_reason": exclusion_reason,
            }
        )
    before = [row for row in overlay_rows if row["release_eligible_before"]]
    after = [row for row in overlay_rows if row["release_eligible_after_overlay"]]
    changed = [
        row
        for row in overlay_rows
        if row["release_eligible_before"] != row["release_eligible_after_overlay"]
        or row["source_quality_bucket_before"] != row["source_quality_bucket_after_overlay"]
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "overlay",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": config.get("created_at", now_utc()),
        "overlay_row_count": len(overlay_rows),
        "release_eligible_before_count_by_repo": count_repos(before),
        "release_eligible_after_count_by_repo": count_repos(after),
        "release_eligible_changed_count": sum(1 for row in overlay_rows if row["release_eligible_before"] != row["release_eligible_after_overlay"]),
        "source_quality_changed_count": sum(1 for row in overlay_rows if row["source_quality_bucket_before"] != row["source_quality_bucket_after_overlay"]),
        "changed_task_ids": [row["task_id"] for row in sorted_rows(changed)],
        "completed_paid_result_changed": False,
        "historical_paid_task_list_changed": False,
        "rows": sorted_rows(overlay_rows),
    }
    return payload


def write_repair_review_report(config: dict[str, Any], queue: dict[str, Any], packets: dict[str, Any], reviews: dict[str, Any], overlay: dict[str, Any]) -> None:
    lines = [
        "# Source Context Repair Review",
        "",
        "## What Happened",
        "",
        f"The repair queue has {queue['queue_count']} rows. Statement packets were written for {packets['packet_count']} rows; "
        f"{packets['packet_status_counts'].get('blocked', 0)} packets are blocked because public problem context is missing.",
        "",
        f"Review verdicts: {reviews['review_verdict_counts']}.",
        "",
        "Release-eligible counts before and after the overlay:",
    ]
    for repo in REPO_ORDER:
        before = overlay["release_eligible_before_count_by_repo"].get(repo, 0)
        after = overlay["release_eligible_after_count_by_repo"].get(repo, 0)
        lines.append(f"- {repo}: {before} before, {after} after")
    lines.extend(
        [
            "",
            "## Why It Matters",
            "",
            "The overlay repairs the accounting weakness without rewriting the completed paid pilot. Click remains usable only with minor title-only risk, while one attrs title-only task is excluded from future split-design eligibility for ambiguous scope.",
            "",
            "## Action This Suggests",
            "",
            "Use the overlay for future no-paid split design. Do not use the completed paid outcomes to promote or demote tasks.",
            "",
            "## Hygiene",
            "",
            "- Paid LLM review calls made: 0.",
            "- Raw public API responses committed: false.",
            "- Raw prompts or completions committed: false.",
            "- Completed paid decision changed: false.",
        ]
    )
    write_text(report_path(config, "repair_review"), "\n".join(lines))


def build_split_feature_table(config: dict[str, Any], inventory: dict[str, Any] | None = None, overlay: dict[str, Any] | None = None, packets: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = inventory or read_json(output_path(config, "inventory"), build_inventory(config))
    overlay = overlay or read_json(output_path(config, "overlay"), build_overlay(config, inventory))
    packets = packets or read_json(output_path(config, "statement_packets"), build_statement_packets(config, inventory))
    overlay_by_id = {row["task_id"]: row for row in overlay["rows"]}
    packet_by_id = {row["task_id"]: row for row in packets["rows"]}
    feature_rows: list[dict[str, Any]] = []
    for row in inventory["rows"]:
        overlay_row = overlay_by_id[row["task_id"]]
        packet = packet_by_id.get(row["task_id"], {})
        summary = packet.get("allowed_public_context_summary") or ""
        feature = {
            "task_id": row["task_id"],
            "repo": row["repo"],
            "release_eligible_for_split_design": overlay_row["release_eligible_after_overlay"],
            "source_context_type_bucket": source_context_type_bucket(row["source_context_type"]),
            "source_quality_bucket": overlay_row["source_quality_bucket_after_overlay"],
            "statement_specificity_bucket": overlay_row["statement_specificity_bucket_after_overlay"],
            "context_length_bucket": context_length_bucket(len(summary) if summary else None),
            "editable_scope_bucket": overlay_row["scope_bucket_after_overlay"],
            "ambiguity_risk_bucket": overlay_row["ambiguity_risk_bucket_after_overlay"],
            "leakage_risk_bucket": overlay_row["leakage_risk_bucket_after_overlay"],
            "certification_risk_bucket": row["certification_risk_bucket"],
            "coarse_task_family": row["coarse_task_family"],
            "time_bucket": row.get("task_time_bucket", "unknown"),
            "rare_or_unknown_feature_flag": (
                overlay_row["scope_bucket_after_overlay"] == "project_wide"
                or overlay_row["statement_specificity_bucket_after_overlay"] in {"missing", "thin"}
                or source_context_type_bucket(row["source_context_type"]) in {"unknown", "commit_message_only"}
            ),
            "exclusion_reason": overlay_row["exclusion_reason"],
        }
        feature_rows.append(feature)
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "split_feature_table",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": config.get("created_at", now_utc()),
        "feature_row_count": len(feature_rows),
        "eligible_for_split_design_count": sum(1 for row in feature_rows if row["release_eligible_for_split_design"]),
        "eligible_for_split_design_count_by_repo": count_repos([row for row in feature_rows if row["release_eligible_for_split_design"]]),
        "source_quality_bucket_counts_by_repo": count_by_repo(feature_rows, "source_quality_bucket"),
        "rare_or_unknown_feature_count": sum(1 for row in feature_rows if row["rare_or_unknown_feature_flag"]),
        "raw_text_fields_committed": False,
        "rows": sorted_rows(feature_rows),
    }
    return payload


def write_split_features_report(config: dict[str, Any], features: dict[str, Any]) -> None:
    lines = [
        "# Source Quality Split Feature Table",
        "",
        "## What Happened",
        "",
        f"The split feature table has {features['feature_row_count']} rows and "
        f"{features['eligible_for_split_design_count']} rows eligible for future split design after overlay.",
        "",
        "Eligible counts by repo:",
    ]
    for repo in REPO_ORDER:
        count = features["eligible_for_split_design_count_by_repo"].get(repo, 0)
        lines.append(f"- {repo}: {count}")
    lines.extend(
        [
            "",
            "## Why It Matters",
            "",
            "Future split redesign can use coarse, auditable buckets instead of raw statement text or high-cardinality public context.",
            "",
            "## Action This Suggests",
            "",
            "The fields ready for blocked split design are repo, source context type, source quality, statement specificity, context length, editable scope, leakage risk, ambiguity risk, certification risk, task family, and time bucket.",
            "",
            "Weak fields remain explicit: click title-only tasks carry minor risk, and commit-message-only queue tasks are blocked from split-design eligibility.",
        ]
    )
    write_text(report_path(config, "split_features"), "\n".join(lines))


def build_readiness_gate(config: dict[str, Any], inventory: dict[str, Any] | None = None, overlay: dict[str, Any] | None = None, features: dict[str, Any] | None = None, reviews: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = inventory or read_json(output_path(config, "inventory"), build_inventory(config))
    overlay = overlay or read_json(output_path(config, "overlay"), build_overlay(config, inventory))
    features = features or read_json(output_path(config, "split_feature_table"), build_split_feature_table(config, inventory, overlay))
    reviews = reviews or read_json(output_path(config, "review_records"), build_review_records(config, inventory))
    min_per_repo = int(config.get("policy", {}).get("release_eligible_min_per_repo", 30))
    eligible_by_repo = {repo: features["eligible_for_split_design_count_by_repo"].get(repo, 0) for repo in REPO_ORDER}
    gates = {
        "no_unresolved_solution_exposure_risk": not any(row["review_verdict"] == "reject_solution_exposure_risk" for row in reviews["rows"]),
        "release_eligible_and_technical_certified_counts_separate": inventory["release_eligible_before_count"] != inventory["technical_certified_count"],
        "eligible_tasks_not_blocked": not any(row["release_eligible_for_split_design"] and row["source_quality_bucket"] == "blocked" for row in features["rows"]),
        "title_only_and_commit_message_only_reviewed_or_excluded": all(
            row["source_context_type_bucket"] not in {"title_only", "commit_message_only"}
            or row["release_eligible_for_split_design"]
            or row["exclusion_reason"]
            for row in features["rows"]
        ),
        "feature_table_covers_three_repos": all(repo in eligible_by_repo for repo in REPO_ORDER),
        "each_repo_has_minimum_eligible_after_overlay": all(count >= min_per_repo for count in eligible_by_repo.values()),
        "paid_calls_made_by_this_run_zero": True,
        "completed_paid_decision_unchanged": True,
    }
    ready = all(gates.values())
    minor_risk = any(row["release_eligible_for_split_design"] and row["source_quality_bucket"] == "minor_risk" for row in features["rows"])
    if ready and minor_risk:
        decision_label = "source_context_ready_with_minor_risk"
    elif ready:
        decision_label = "source_context_ready_for_blocked_split_design"
    elif not gates["each_repo_has_minimum_eligible_after_overlay"]:
        decision_label = "needs_more_public_context_repair_before_split_design"
    else:
        decision_label = "blocked_missing_public_context_or_review"
    return {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "readiness_gate",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": config.get("created_at", now_utc()),
        "ready_for_blocked_split_design": ready,
        "decision_label": decision_label,
        "gates": gates,
        "failed_gates": [key for key, value in gates.items() if not value],
        "eligible_by_repo_after_overlay": eligible_by_repo,
        "paid_calls_made_by_this_run": 0,
        "completed_paid_decision_changed": False,
        "predictive_validity_established": False,
        "smallest_remaining_blocker": "click_title_only_minor_risk" if minor_risk else "",
        "recommended_next_action_category": "blocked_split_redesign" if ready else "additional_public_context_repair",
    }


def write_readiness_report(config: dict[str, Any], readiness: dict[str, Any]) -> None:
    lines = [
        "# Source Context Statement Hardening Readiness Gate",
        "",
        "## What Happened",
        "",
        f"Gate decision: `{readiness['decision_label']}`. Ready for blocked split design: {str(readiness['ready_for_blocked_split_design']).lower()}.",
        "",
        "Eligible counts after overlay:",
    ]
    for repo, count in readiness["eligible_by_repo_after_overlay"].items():
        lines.append(f"- {repo}: {count}")
    lines.extend(
        [
            "",
            "## Why It Matters",
            "",
            "The gate checks the benchmark-side policy before any future split redesign. It confirms that paid outcomes did not choose promotions and that completed paid decisions remain frozen.",
            "",
            "## Action This Suggests",
            "",
            f"Recommended next action category: `{readiness['recommended_next_action_category']}`.",
            f"Smallest remaining blocker: `{readiness['smallest_remaining_blocker'] or 'none'}`.",
        ]
    )
    write_text(report_path(config, "readiness_gate"), "\n".join(lines))


def build_decision(config: dict[str, Any], inventory: dict[str, Any] | None = None, overlay: dict[str, Any] | None = None, features: dict[str, Any] | None = None, readiness: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = inventory or read_json(output_path(config, "inventory"), build_inventory(config))
    overlay = overlay or read_json(output_path(config, "overlay"), build_overlay(config, inventory))
    features = features or read_json(output_path(config, "split_feature_table"), build_split_feature_table(config, inventory, overlay))
    readiness = readiness or read_json(output_path(config, "readiness_gate"), build_readiness_gate(config, inventory, overlay, features))
    thin_by_repo = defaultdict(int)
    minor_by_repo = defaultdict(int)
    blocked_by_repo = defaultdict(int)
    for row in features["rows"]:
        if row["statement_specificity_bucket"] in {"thin", "missing"}:
            thin_by_repo[row["repo"]] += 1
        if row["source_quality_bucket"] == "minor_risk" and row["release_eligible_for_split_design"]:
            minor_by_repo[row["repo"]] += 1
        if row["source_quality_bucket"] == "blocked":
            blocked_by_repo[row["repo"]] += 1
    changed_release = overlay["release_eligible_changed_count"]
    changed_quality = overlay["source_quality_changed_count"]
    return {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "decision",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": config.get("created_at", now_utc()),
        "decision_label": readiness["decision_label"],
        "ready_for_blocked_split_design": readiness["ready_for_blocked_split_design"],
        "research_questions": {
            "RQ1_changed_source_quality_or_release_eligibility": {
                "release_eligibility_changed_count": changed_release,
                "source_quality_changed_count": changed_quality,
                "changed_task_ids": overlay["changed_task_ids"],
            },
            "RQ2_repos_with_thin_source_context_or_statement_risk": {
                "thin_or_missing_specificity_by_repo": dict(sorted(thin_by_repo.items())),
                "eligible_minor_risk_by_repo": dict(sorted(minor_by_repo.items())),
                "blocked_queue_rows_by_repo": dict(sorted(blocked_by_repo.items())),
            },
            "RQ3_ready_as_input_to_no_paid_blocked_split_redesign": readiness["ready_for_blocked_split_design"],
            "RQ4_paid_calls_made": 0,
            "RQ5_completed_paid_result_changed": False,
            "RQ6_smallest_remaining_blocker": readiness["smallest_remaining_blocker"],
            "RQ7_next_action_category": readiness["recommended_next_action_category"],
        },
        "predictive_validity_established": False,
        "completed_paid_pilot_decision_changed": False,
        "completed_paid_task_list_changed": False,
        "paid_llm_calls_made": 0,
        "paid_acut_solver_cells_made": 0,
        "raw_artifact_hygiene": {
            "raw_prompts_committed": False,
            "raw_completions_committed": False,
            "raw_acut_transcripts_committed": False,
            "raw_target_diffs_committed": False,
            "raw_test_patches_committed": False,
            "raw_public_api_responses_committed": False,
        },
        "recommended_next_action_category": readiness["recommended_next_action_category"],
        "smallest_remaining_blocker": readiness["smallest_remaining_blocker"],
    }


def write_decision_report(config: dict[str, Any], decision: dict[str, Any]) -> None:
    rq = decision["research_questions"]
    lines = [
        "# Source Context Statement Hardening Decision",
        "",
        "## What Happened",
        "",
        f"Decision label: `{decision['decision_label']}`.",
        f"Ready for blocked split redesign: {str(decision['ready_for_blocked_split_design']).lower()}.",
        "",
        f"RQ1: {rq['RQ1_changed_source_quality_or_release_eligibility']['release_eligibility_changed_count']} tasks changed release eligibility for future split design, and {rq['RQ1_changed_source_quality_or_release_eligibility']['source_quality_changed_count']} changed source-quality bucket.",
        f"RQ2: Thin or missing specificity by repo: {rq['RQ2_repos_with_thin_source_context_or_statement_risk']['thin_or_missing_specificity_by_repo']}. Eligible minor risk by repo: {rq['RQ2_repos_with_thin_source_context_or_statement_risk']['eligible_minor_risk_by_repo']}.",
        f"RQ3: attrs/boltons/click ready as input to no-paid blocked split redesign: {str(rq['RQ3_ready_as_input_to_no_paid_blocked_split_redesign']).lower()}.",
        f"RQ4: Paid calls made by this run: {rq['RQ4_paid_calls_made']}.",
        f"RQ5: Completed paid result changed: {str(rq['RQ5_completed_paid_result_changed']).lower()}.",
        f"RQ6: Smallest remaining blocker: `{rq['RQ6_smallest_remaining_blocker'] or 'none'}`.",
        f"RQ7: Recommended next action category: `{rq['RQ7_next_action_category']}`.",
        "",
        "## Why It Matters",
        "",
        "The pool now has an explicit overlay that separates technical certification from release eligibility and records the risk from title-only or commit-message-only context. Predictive validity is still not established.",
        "",
        "## Action This Suggests",
        "",
        "Proceed only to the recommended action category. Do not draft a follow-up runbook in this run.",
        "",
        "## Hygiene",
        "",
        "- Paid LLM calls made: 0.",
        "- Paid ACUT solver cells made: 0.",
        "- Completed paid decision changed: false.",
        "- Predictive validity established: false.",
        "- Raw prompts, completions, ACUT transcripts, target diffs, test patches, and public API responses committed: false.",
    ]
    write_text(report_path(config, "decision"), "\n".join(lines))


def assert_no_forbidden_raw_markers(payload: Any) -> None:
    encoded = json.dumps(payload, sort_keys=True)
    for marker in FORBIDDEN_RAW_MARKERS:
        if marker in encoded:
            raise ValueError(f"forbidden raw marker found in output: {marker!r}")
    for match in HEX40_RE.findall(encoded):
        raise ValueError(f"raw 40-char hash found in source-context hardening output: {match}")


def run_inventory(config: dict[str, Any]) -> dict[str, Any]:
    inventory = build_inventory(config)
    assert_no_forbidden_raw_markers(inventory)
    write_json(output_path(config, "inventory"), inventory)
    write_inventory_report(config, inventory)
    return inventory


def run_queue(config: dict[str, Any]) -> dict[str, Any]:
    inventory = read_json(output_path(config, "inventory"), build_inventory(config))
    queue = build_repair_queue(config, inventory)
    assert_no_forbidden_raw_markers(queue)
    write_json(output_path(config, "repair_queue"), queue)
    return queue


def run_packets(config: dict[str, Any]) -> dict[str, Any]:
    inventory = read_json(output_path(config, "inventory"), build_inventory(config))
    queue = read_json(output_path(config, "repair_queue"), build_repair_queue(config, inventory))
    packets = build_statement_packets(config, inventory, queue)
    assert_no_forbidden_raw_markers(packets)
    write_json(output_path(config, "statement_packets"), packets)
    return packets


def run_review(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    inventory = read_json(output_path(config, "inventory"), build_inventory(config))
    queue = read_json(output_path(config, "repair_queue"), build_repair_queue(config, inventory))
    packets = read_json(output_path(config, "statement_packets"), build_statement_packets(config, inventory, queue))
    reviews = build_review_records(config, inventory, packets)
    overlay = build_overlay(config, inventory, reviews)
    assert_no_forbidden_raw_markers(reviews)
    assert_no_forbidden_raw_markers(overlay)
    write_json(output_path(config, "review_records"), reviews)
    write_json(output_path(config, "overlay"), overlay)
    write_repair_review_report(config, queue, packets, reviews, overlay)
    return reviews, overlay


def run_features(config: dict[str, Any]) -> dict[str, Any]:
    inventory = read_json(output_path(config, "inventory"), build_inventory(config))
    overlay = read_json(output_path(config, "overlay"), build_overlay(config, inventory))
    packets = read_json(output_path(config, "statement_packets"), build_statement_packets(config, inventory))
    features = build_split_feature_table(config, inventory, overlay, packets)
    assert_no_forbidden_raw_markers(features)
    write_json(output_path(config, "split_feature_table"), features)
    write_split_features_report(config, features)
    return features


def run_readiness(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    inventory = read_json(output_path(config, "inventory"), build_inventory(config))
    overlay = read_json(output_path(config, "overlay"), build_overlay(config, inventory))
    features = read_json(output_path(config, "split_feature_table"), build_split_feature_table(config, inventory, overlay))
    reviews = read_json(output_path(config, "review_records"), build_review_records(config, inventory))
    readiness = build_readiness_gate(config, inventory, overlay, features, reviews)
    decision = build_decision(config, inventory, overlay, features, readiness)
    assert_no_forbidden_raw_markers(readiness)
    assert_no_forbidden_raw_markers(decision)
    write_json(output_path(config, "readiness_gate"), readiness)
    write_json(output_path(config, "decision"), decision)
    write_readiness_report(config, readiness)
    write_decision_report(config, decision)
    return readiness, decision


def run_all(config: dict[str, Any]) -> None:
    run_inventory(config)
    run_queue(config)
    run_packets(config)
    run_review(config)
    run_features(config)
    run_readiness(config)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--step",
        choices=["inventory", "queue", "packets", "review", "features", "readiness", "all"],
        default="all",
    )
    args = parser.parse_args(argv)
    config = load_config(args.config)
    if args.step == "inventory":
        run_inventory(config)
    elif args.step == "queue":
        run_queue(config)
    elif args.step == "packets":
        run_packets(config)
    elif args.step == "review":
        run_review(config)
    elif args.step == "features":
        run_features(config)
    elif args.step == "readiness":
        run_readiness(config)
    else:
        run_all(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
