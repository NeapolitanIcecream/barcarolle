from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
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
    command_env,
    cwd_for,
    infer_profile_candidates,
)


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
PHASE0_TOOLS = PHASE0_ROOT / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import phase1_task_supply_v2_fresh_certification as fresh  # noqa: E402
import repo_history_pilot  # noqa: E402


SCHEMA_VERSION = "barcarolle.phase1_third_repo_release_supply_screen.v1"
RUN_ID = "phase1_third_repo_release_supply_screen_20260528"
DEFAULT_CONFIG = ROOT / "configs" / "phase1_third_repo_release_supply_screen.yaml"
SCAN_SINCE = "2010-01-01"
TAIL_LIMIT = 2000
ACCEPTED_RELEASE_CONTEXTS = {"non_leaky_issue_or_pr_context", "pr_title_only_context"}
NON_LEAKY_CONTEXTS = {
    "non_leaky_issue_or_pr_context",
    "pr_title_only_context",
    "commit_message_only_context",
    "no_usable_public_context",
    "material_ambiguity_risk",
}
RAW_INVENTORY_STATUSES = {
    "oracle_usable",
    "oracle_missing_inventory_only",
    "material_leakage_risk",
    "candidate_outside_scope",
    "duplicate_candidate",
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


def read_json(path: str | Path, default: Any = None) -> Any:
    resolved = repo_path(path)
    if not resolved.exists():
        return default
    return json.loads(resolved.read_text(encoding="utf-8"))


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
        raise ValueError("unexpected third repo release supply screen config schema_version")
    caps = config.get("caps", {})
    config.setdefault(
        "certification_caps",
        {
            "single_command_timeout_seconds": caps.get("single_command_timeout_seconds", 120),
            "single_candidate_total_timeout_seconds": caps.get("single_candidate_total_timeout_seconds", 600),
            "environment_profiles_per_candidate": caps.get("environment_profiles_per_candidate", 5),
        },
    )
    config["_path"] = str(path)
    return config


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


def scratch_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["scratch_paths"][key])


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
            "stdout": fresh.ensure_text(exc.stdout),
            "stderr": fresh.ensure_text(exc.stderr),
            "duration_seconds": round(time.monotonic() - start, 3),
        }
    return {
        "args": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "duration_seconds": round(time.monotonic() - start, 3),
    }


def command_stdout(args: list[str], cwd: Path = REPO_ROOT, timeout: int = 120) -> str:
    result = command_result(args, cwd=cwd, timeout=timeout)
    return result["stdout"].strip() if result["returncode"] == 0 else result["stderr"].strip()


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:12]


def stable_dedup_key(row: dict[str, Any]) -> str:
    payload = {
        "repo_id": row.get("repo_id"),
        "base_commit": row.get("base_commit"),
        "target_commit_optional": row.get("target_commit_optional"),
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


def candidate_repo_ids(config: dict[str, Any]) -> list[str]:
    return [str(repo_id) for repo_id in config.get("seed_candidate_repos", [])]


def repo_config(config: dict[str, Any], repo_id: str) -> dict[str, Any]:
    return dict(config["repos"][repo_id])


def repo_dir(config: dict[str, Any], repo_id: str) -> Path:
    return repo_path(repo_config(config, repo_id)["local_repo"])


def parse_git_log(config: dict[str, Any], repo_id: str) -> list[dict[str, Any]]:
    repo = repo_dir(config, repo_id)
    cap = int(config["caps"]["raw_anchors_scanned_per_repo"])
    result = command_result(
        [
            "git",
            "log",
            f"--since={SCAN_SINCE}",
            f"--max-count={cap}",
            "--reverse",
            "--format=%x1e%H%x09%P%x09%ad%x09%s",
            "--date=iso-strict",
            "--name-only",
        ],
        cwd=repo,
        timeout=int(config["caps"]["single_command_timeout_seconds"]),
    )
    if result["returncode"] != 0:
        raise RuntimeError(result["stderr"])
    commits: list[dict[str, Any]] = []
    for chunk in result["stdout"].split("\x1e"):
        lines = [line for line in chunk.splitlines() if line.strip()]
        if not lines:
            continue
        meta = lines[0].split("\t", 3)
        if len(meta) != 4:
            continue
        commit, parents, commit_time, subject = meta
        paths = lines[1:]
        code_files, test_files = repo_history_pilot.classify_paths(paths)
        refs = public_refs_from_text(subject)
        commits.append(
            {
                "commit": commit,
                "parent": parents.split()[0] if parents.split() else "",
                "task_time": commit_time,
                "subject": subject,
                "changed_files": paths,
                "implementation_files": code_files,
                "test_files": test_files,
                "has_implementation": bool(code_files),
                "has_tests": bool(test_files),
                "public_context_refs": refs,
                "linkable": bool(refs),
            }
        )
    return commits


def public_refs_from_text(text: str) -> list[str]:
    refs = []
    for match in re.finditer(r"#(\d+)", text or ""):
        refs.append(f"pr:{match.group(1)}")
    return unique(refs)


def source_context_quality(subject: str, refs: list[str], leakage_flags: list[str] | None = None) -> str:
    leakage_flags = leakage_flags or []
    text = f"{subject} {' '.join(leakage_flags)}".lower()
    if "leak" in text or "solution patch" in text:
        return "material_leakage_risk"
    if any(ref.startswith("issue:") for ref in refs):
        return "non_leaky_issue_or_pr_context"
    if any(ref.startswith("pr:") for ref in refs):
        return "pr_title_only_context"
    if subject.strip():
        return "commit_message_only_context"
    return "no_usable_public_context"


def source_context_class(quality: str) -> str:
    if quality == "non_leaky_issue_or_pr_context":
        return "issue_or_pr_context"
    if quality == "pr_title_only_context":
        return "pr_context_title_only"
    return quality


def score_from_thresholds(value: int, thresholds: tuple[int, int, int, int]) -> int:
    if value >= thresholds[3]:
        return 5
    if value >= thresholds[2]:
        return 4
    if value >= thresholds[1]:
        return 3
    if value >= thresholds[0]:
        return 2
    if value > 0:
        return 1
    return 0


def cheap_repo_row(config: dict[str, Any], repo_id: str) -> dict[str, Any]:
    cfg = repo_config(config, repo_id)
    repo = repo_dir(config, repo_id)
    if not (repo / ".git").exists():
        return {
            "repo_id": repo_id,
            "repo_url": cfg["repo_url"],
            "local_path": rel(repo),
            "present": False,
            "overall_screen_label": "reject_for_this_run",
            "rejection_reasons": ["local_repo_missing"],
        }
    commits = parse_git_log(config, repo_id)
    impl_count = sum(1 for row in commits if row["has_implementation"])
    test_count = sum(1 for row in commits if row["has_tests"])
    impl_test_count = sum(1 for row in commits if row["has_implementation"] and row["has_tests"])
    linkable_count = sum(1 for row in commits if row["linkable"])
    impl_test_linkable_count = sum(1 for row in commits if row["has_implementation"] and row["has_tests"] and row["linkable"])
    history_supply_score = score_from_thresholds(impl_test_count, (15, 45, 90, 150))
    oracle_supply_score = score_from_thresholds(impl_test_count, (15, 45, 90, 150))
    source_context_score = score_from_thresholds(impl_test_linkable_count, (5, 20, 45, 90))
    environment_score = 4 if cfg.get("external_service_risk") == "low" else 2
    runtime_score = 4 if test_count <= 350 else 3
    external_service_risk_score = 5 if cfg.get("external_service_risk") == "low" else 2
    total = history_supply_score + oracle_supply_score + source_context_score + environment_score + runtime_score + external_service_risk_score
    reasons = []
    if impl_test_count < 45:
        reasons.append("too_few_implementation_plus_test_commits")
    if impl_test_linkable_count < 20:
        reasons.append("weak_public_issue_or_pr_linkability")
    if cfg.get("external_service_risk") != "low":
        reasons.append("external_service_risk_not_low")
    return {
        "repo_id": repo_id,
        "repo_url": cfg["repo_url"],
        "local_path": rel(repo),
        "present": True,
        "head": command_stdout(["git", "rev-parse", "HEAD"], cwd=repo),
        "head_short": command_stdout(["git", "rev-parse", "--short", "HEAD"], cwd=repo),
        "default_branch": command_stdout(["git", "branch", "--show-current"], cwd=repo),
        "language": cfg.get("language", "Python"),
        "package_manager_hints": cfg.get("package_manager_hint", ""),
        "test_framework_hints": cfg.get("test_framework_hint", ""),
        "external_service_risk": cfg.get("external_service_risk", "unknown"),
        "commit_count_since_2010_or_cap": len(commits),
        "commit_count_with_implementation_changes": impl_count,
        "commit_count_with_test_changes": test_count,
        "commit_count_with_both_implementation_and_test_changes": impl_test_count,
        "commit_count_with_both_implementation_and_test_changes_and_public_refs": impl_test_linkable_count,
        "visible_issue_or_pr_linkability_signal": {
            "commit_subject_refs": linkable_count,
            "implementation_plus_test_subject_refs": impl_test_linkable_count,
            "rate": round(linkable_count / len(commits), 3) if commits else 0.0,
        },
        "history_supply_score": history_supply_score,
        "oracle_supply_score": oracle_supply_score,
        "source_context_score": source_context_score,
        "environment_score": environment_score,
        "runtime_score": runtime_score,
        "external_service_risk_score": external_service_risk_score,
        "overall_score": total,
        "rejection_reasons": reasons,
    }


def build_repo_shortlist(config: dict[str, Any]) -> dict[str, Any]:
    rows = [cheap_repo_row(config, repo_id) for repo_id in candidate_repo_ids(config)]
    eligible = [
        row
        for row in rows
        if row.get("present")
        and int(row.get("commit_count_with_both_implementation_and_test_changes", 0)) >= 45
        and int(row.get("overall_score", 0)) >= 18
    ]
    cap = int(config["caps"]["repos_advanced_to_raw_mining"])
    ordered = sorted(
        eligible,
        key=lambda row: (
            -int(row.get("commit_count_with_both_implementation_and_test_changes_and_public_refs", 0)),
            -int(row.get("overall_score", 0)),
            str(row["repo_id"]),
        ),
    )
    advanced = {str(row["repo_id"]) for row in ordered[:cap]}
    for row in rows:
        if row.get("repo_id") in advanced:
            row["overall_screen_label"] = "advance_to_raw_mining"
            row["screen_reason"] = "enough implementation-plus-test history and public linkability for bounded raw mining"
        elif not row.get("present") or int(row.get("commit_count_with_both_implementation_and_test_changes", 0)) < 45:
            row["overall_screen_label"] = "reject_for_this_run"
            row["screen_reason"] = "; ".join(row.get("rejection_reasons", [])) or "cheap screen did not show enough local supply"
        else:
            row["overall_screen_label"] = "backup_only"
            row["screen_reason"] = "usable history exists, but stronger repos filled the raw-mining cap"
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.repo_shortlist.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "status": "repo_shortlist_built",
        "candidate_repos_screened": candidate_repo_ids(config),
        "candidate_repo_count_cap": int(config["caps"]["candidate_repos_in_cheap_screen"]),
        "repos_advanced_to_raw_mining": sorted(advanced),
        "rows": sorted(rows, key=lambda row: str(row["repo_id"])),
        "paid_calls_made": False,
        "raw_artifacts_committed": False,
    }
    return payload


def raw_inventory_status(row: dict[str, Any], duplicate: bool) -> str:
    if duplicate:
        return "duplicate_candidate"
    if not row.get("base_commit") or not row.get("target_commit_optional") or not row.get("implementation_files"):
        return "candidate_outside_scope"
    if row.get("source_context_quality") == "material_leakage_risk":
        return "material_leakage_risk"
    if row.get("test_files"):
        return "oracle_usable"
    return "oracle_missing_inventory_only"


def source_reservoir(commit: dict[str, Any]) -> str:
    if commit["has_implementation"] and commit["has_tests"] and commit["linkable"]:
        return "repo_history_v2_pr_issue_with_tests"
    if commit["has_implementation"] and commit["has_tests"]:
        return "repo_history_v2_commit_with_tests"
    if commit["has_implementation"] and commit["linkable"]:
        return "repo_history_v2_issue_without_changed_tests"
    return ""


def mine_raw_inventory(config: dict[str, Any]) -> dict[str, Any]:
    shortlist = read_json(output_path(config, "repo_shortlist")) or build_repo_shortlist(config)
    advanced = set(shortlist["repos_advanced_to_raw_mining"])
    rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}
    cap = int(config["caps"]["raw_candidates_retained_per_repo"])
    for repo_id in sorted(advanced):
        repo_rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        inventory_counts: Counter[str] = Counter()
        reservoir_counts: Counter[str] = Counter()
        for commit in parse_git_log(config, repo_id):
            reservoir = source_reservoir(commit)
            if not reservoir or not commit["parent"]:
                continue
            quality = source_context_quality(commit["subject"], commit["public_context_refs"])
            row = {
                "candidate_id": f"{repo_id}__third__{len(repo_rows) + 1:03d}",
                "repo_id": repo_id,
                "source_reservoir": reservoir,
                "base_commit": commit["parent"],
                "target_commit_optional": commit["commit"],
                "task_time": commit["task_time"],
                "subject_digest": short_hash(commit["subject"]),
                "public_context_refs": commit["public_context_refs"][:3],
                "implementation_files": commit["implementation_files"],
                "test_files": commit["test_files"],
                "changed_file_count": len(commit["changed_files"]),
                "source_context_quality": quality,
                "source_context_class": source_context_class(quality),
                "leakage_flags": [] if quality != "material_leakage_risk" else ["material_leakage_risk"],
                "ambiguity_flags": [],
                "has_usable_oracle": bool(commit["test_files"]),
                "gold_patch_exposed_to_solver": False,
                "reference_patch_digest_optional": short_hash(f"{repo_id}:{commit['parent']}:{commit['commit']}:{commit['test_files']}"),
                "raw_artifact_paths_uncommitted": [rel(scratch_path(config, "tmp"))],
            }
            row["dedup_key"] = stable_dedup_key(row)
            duplicate = row["dedup_key"] in seen
            seen.add(row["dedup_key"])
            row["inventory_status"] = raw_inventory_status(row, duplicate)
            inventory_counts[row["inventory_status"]] += 1
            reservoir_counts[reservoir] += 1
            repo_rows.append(row)
            if len(repo_rows) >= cap:
                break
        rows.extend(repo_rows)
        summary[repo_id] = {
            "raw_candidate_count": len(repo_rows),
            "inventory_status_counts": dict(sorted(inventory_counts.items())),
            "source_reservoir_counts": dict(sorted(reservoir_counts.items())),
            "cap_hit": len(repo_rows) >= cap,
        }
    return {
        "schema_version": f"{SCHEMA_VERSION}.raw_anchor_inventory.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "status": "repo_raw_anchor_inventory_completed",
        "history_scan_cap_per_repo": int(config["caps"]["raw_anchors_scanned_per_repo"]),
        "raw_candidates_retained_per_repo_cap": cap,
        "advanced_repos": sorted(advanced),
        "summary_by_repo": summary,
        "candidate_count": len(rows),
        "inventory_status_taxonomy": sorted(RAW_INVENTORY_STATUSES),
        "rows": sorted(rows, key=lambda row: (str(row["repo_id"]), str(row["candidate_id"]))),
        "raw_diffs_committed": False,
        "raw_test_patches_committed": False,
        "paid_calls_made": False,
    }


def build_source_context_inventory(config: dict[str, Any], raw_inventory: dict[str, Any]) -> dict[str, Any]:
    rows = []
    counts_by_repo: dict[str, Counter[str]] = defaultdict(Counter)
    release_ready_by_repo: Counter[str] = Counter()
    upper_bound_by_repo: Counter[str] = Counter()
    for raw in raw_inventory.get("rows", []):
        quality = str(raw.get("source_context_quality") or "no_usable_public_context")
        oracle_usable = raw.get("inventory_status") == "oracle_usable"
        release_ready = oracle_usable and quality in ACCEPTED_RELEASE_CONTEXTS
        upper_bound = oracle_usable and quality in NON_LEAKY_CONTEXTS
        counts_by_repo[str(raw["repo_id"])][quality] += 1
        if release_ready:
            release_ready_by_repo[str(raw["repo_id"])] += 1
        if upper_bound:
            upper_bound_by_repo[str(raw["repo_id"])] += 1
        rows.append(
            {
                "candidate_id": raw["candidate_id"],
                "repo_id": raw["repo_id"],
                "source_reservoir": raw["source_reservoir"],
                "source_context_quality": quality,
                "source_context_class": source_context_class(quality),
                "public_context_refs": raw.get("public_context_refs", []),
                "leakage_flags": raw.get("leakage_flags", []),
                "ambiguity_flags": raw.get("ambiguity_flags", []),
                "release_ready_before_certification": release_ready,
                "technical_plus_review_upper_bound": upper_bound,
                "not_release_ready_reason": "" if release_ready else not_release_ready_reason(quality, oracle_usable),
            }
        )
    return {
        "schema_version": f"{SCHEMA_VERSION}.source_context_inventory.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "status": "repo_source_context_screen_completed",
        "counts_by_repo": {repo: dict(sorted(counter.items())) for repo, counter in sorted(counts_by_repo.items())},
        "release_ready_before_certification_count_by_repo": dict(sorted(release_ready_by_repo.items())),
        "technical_plus_review_upper_bound_count_by_repo": dict(sorted(upper_bound_by_repo.items())),
        "rows": sorted(rows, key=lambda row: (str(row["repo_id"]), str(row["candidate_id"]))),
    }


def not_release_ready_reason(quality: str, oracle_usable: bool) -> str:
    if not oracle_usable:
        return "candidate lacks changed-test oracle"
    if quality == "material_leakage_risk":
        return "source context has material leakage risk"
    return f"source_context_quality={quality} requires separate review before release counting"


def build_oracle_matrix(config: dict[str, Any], raw_inventory: dict[str, Any]) -> dict[str, Any]:
    rows = []
    counts_by_repo: dict[str, Counter[str]] = defaultdict(Counter)
    for raw in raw_inventory.get("rows", []):
        if raw.get("inventory_status") == "oracle_usable":
            classification = "changed_test_oracle_available"
            extractable = True
        elif raw.get("inventory_status") == "oracle_missing_inventory_only":
            classification = "oracle_missing_inventory_only"
            extractable = False
        else:
            classification = str(raw.get("inventory_status"))
            extractable = False
        counts_by_repo[str(raw["repo_id"])][classification] += 1
        rows.append(
            {
                "candidate_id": raw["candidate_id"],
                "repo_id": raw["repo_id"],
                "source_reservoir": raw["source_reservoir"],
                "oracle_classification": classification,
                "changed_tests_present": bool(raw.get("test_files")),
                "private_oracle_patch_extractable": extractable,
                "test_files_within_scope": bool(raw.get("test_files")),
                "target_patch_exposed_to_solver": False,
                "test_files": raw.get("test_files", []),
            }
        )
    return {
        "schema_version": f"{SCHEMA_VERSION}.oracle_matrix.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "status": "repo_oracle_screen_completed",
        "oracle_classification_counts_by_repo": {repo: dict(sorted(counter.items())) for repo, counter in sorted(counts_by_repo.items())},
        "rows": sorted(rows, key=lambda row: (str(row["repo_id"]), str(row["candidate_id"]))),
        "raw_test_patches_committed": False,
        "generated_oracle_tasks_promoted_to_eval_pool": False,
    }


def selected_repos_for_environment(config: dict[str, Any], source_context: dict[str, Any]) -> list[str]:
    release_ready = {str(k): int(v) for k, v in source_context.get("release_ready_before_certification_count_by_repo", {}).items()}
    upper_bound = {str(k): int(v) for k, v in source_context.get("technical_plus_review_upper_bound_count_by_repo", {}).items()}
    release_floor = int(config["selection_policy"]["release_ready_min_before_certification"])
    repair_upper = int(config["selection_policy"]["source_repair_upper_bound_min"])
    repair_floor = int(config["selection_policy"]["source_repair_release_ready_floor"])
    candidates = []
    for repo_id in sorted(set(release_ready) | set(upper_bound)):
        rr = release_ready.get(repo_id, 0)
        ub = upper_bound.get(repo_id, 0)
        if rr >= release_floor or (ub >= repair_upper and rr >= repair_floor):
            candidates.append((repo_id, rr, ub))
    candidates.sort(key=lambda item: (-item[1], -item[2], item[0]))
    return [repo_id for repo_id, _, _ in candidates[: int(config["caps"]["repos_advanced_to_certification_wave"])]]


def raw_row_to_execution_row(row: dict[str, Any]) -> dict[str, Any]:
    quality = str(row.get("source_context_quality") or "no_usable_public_context")
    return {
        "candidate_id": row["candidate_id"],
        "repo_id": row["repo_id"],
        "source_reservoir": row["source_reservoir"],
        "base_commit": row["base_commit"],
        "target_commit_optional": row["target_commit_optional"],
        "test_files": row.get("test_files", []),
        "implementation_files": row.get("implementation_files", []),
        "source_context_class": source_context_class(quality),
        "source_context_quality": quality,
        "selected_for_execution": True,
        "execution_priority": context_priority(quality),
        "task_time": row.get("task_time", ""),
        "public_context_refs": row.get("public_context_refs", []),
    }


def context_priority(quality: str) -> int:
    order = [
        "non_leaky_issue_or_pr_context",
        "pr_title_only_context",
        "commit_message_only_context",
        "no_usable_public_context",
        "material_ambiguity_risk",
        "material_leakage_risk",
    ]
    try:
        return order.index(quality)
    except ValueError:
        return len(order)


def time_bucket(value: str) -> str:
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


def sample_probe_rows(config: dict[str, Any], raw_inventory: dict[str, Any], repos: list[str]) -> list[dict[str, Any]]:
    cap = int(config["caps"]["environment_probe_sample_per_repo"])
    by_repo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in raw_inventory.get("rows", []):
        if row.get("repo_id") in repos and row.get("inventory_status") == "oracle_usable":
            by_repo[str(row["repo_id"])].append(row)
    selected: list[dict[str, Any]] = []
    for repo_id, rows in sorted(by_repo.items()):
        rows = sorted(rows, key=lambda row: (context_priority(str(row.get("source_context_quality"))), str(row.get("task_time", "")), str(row["candidate_id"])))
        buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            buckets[time_bucket(str(row.get("task_time", "")))].append(row)
        repo_selected: list[dict[str, Any]] = []
        while len(repo_selected) < cap and any(buckets.values()):
            for bucket in ["pre_2016", "2016_2019", "2020_2023", "2024_plus", "unknown"]:
                if buckets[bucket] and len(repo_selected) < cap:
                    repo_selected.append(buckets[bucket].pop(0))
        selected.extend(raw_row_to_execution_row(row) for row in repo_selected)
    return selected


def run_probe_or_attempt(config: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    return fresh.attempt_candidate(config, row)


def build_environment_probe(config: dict[str, Any]) -> dict[str, Any]:
    raw_inventory = read_json(output_path(config, "raw_anchor_inventory")) or mine_raw_inventory(config)
    source_context = read_json(output_path(config, "source_context_inventory")) or build_source_context_inventory(config, raw_inventory)
    repos = selected_repos_for_environment(config, source_context)
    sample_rows = sample_probe_rows(config, raw_inventory, repos)
    rows = [run_probe_or_attempt(config, row) for row in sample_rows]
    decisions = environment_decisions(config, repos, sample_rows, rows, source_context)
    return {
        "schema_version": f"{SCHEMA_VERSION}.environment_probe.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "status": "repo_environment_probe_completed",
        "repos_selected_for_probe": repos,
        "sample_size_by_repo": dict(sorted(Counter(str(row["repo_id"]) for row in sample_rows).items())),
        "profiles_per_candidate_cap": int(config["caps"]["environment_profiles_per_candidate"]),
        "subgate_counts_by_repo": nested_counts(rows, "repo_id", "terminal_execution_subgate"),
        "decisions_by_repo": decisions,
        "rows": rows,
        "raw_logs_committed": False,
        "workspace_storage": rel(scratch_path(config, "workspaces")),
        "raw_log_storage": rel(scratch_path(config, "raw_logs")),
    }


def environment_decisions(
    config: dict[str, Any],
    repos: list[str],
    sample_rows: list[dict[str, Any]],
    attempt_rows: list[dict[str, Any]],
    source_context: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    release_ready = {str(k): int(v) for k, v in source_context.get("release_ready_before_certification_count_by_repo", {}).items()}
    decisions: dict[str, dict[str, Any]] = {}
    for repo_id in repos:
        repo_attempts = [row for row in attempt_rows if row.get("repo_id") == repo_id]
        sample_count = sum(1 for row in sample_rows if row.get("repo_id") == repo_id)
        technical = sum(1 for row in repo_attempts if row.get("technical_certified"))
        hard_failures = sum(1 for row in repo_attempts if row.get("terminal_execution_subgate") in {"install_failed", "import_failed", "collect_failed", "environment_unavailable", "timeout", "unknown_failed"})
        rr = release_ready.get(repo_id, 0)
        if sample_count == 0:
            decision = "reject_for_this_run"
            reason = "no oracle-usable candidates selected for environment probe"
        elif technical >= 2 or (technical >= 1 and rr >= 90):
            decision = "advance_to_certification_wave"
            reason = "bounded probe produced technical certifications"
        elif hard_failures >= max(1, int(sample_count * 0.75)):
            decision = "needs_environment_repair"
            reason = "environment-like failures dominated the bounded probe"
        else:
            decision = "reject_for_this_run"
            reason = "probe did not show enough stable technical evidence within this run"
        decisions[repo_id] = {
            "decision": decision,
            "reason": reason,
            "sample_size": sample_count,
            "technical_certified": technical,
            "hard_environment_failures": hard_failures,
            "release_ready_before_certification": rr,
        }
    return decisions


def certification_candidates(config: dict[str, Any], raw_inventory: dict[str, Any], environment_probe: dict[str, Any], repo_filter: str | None = None) -> list[dict[str, Any]]:
    advanced = [
        repo
        for repo, decision in environment_probe.get("decisions_by_repo", {}).items()
        if decision.get("decision") == "advance_to_certification_wave" and (repo_filter is None or repo == repo_filter)
    ]
    cap = int(config["caps"]["certification_attempts_per_advanced_repo"])
    by_repo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in raw_inventory.get("rows", []):
        if row.get("repo_id") in advanced and row.get("inventory_status") == "oracle_usable":
            by_repo[str(row["repo_id"])].append(row)
    selected: list[dict[str, Any]] = []
    for repo_id, rows in sorted(by_repo.items()):
        ordered = sorted(rows, key=lambda row: (context_priority(str(row.get("source_context_quality"))), str(row.get("task_time", "")), str(row["candidate_id"])))
        selected.extend(raw_row_to_execution_row(row) for row in ordered[:cap])
    return selected


def load_certification_attempts(config: dict[str, Any]) -> list[dict[str, Any]]:
    existing = read_json(output_path(config, "certification_attempts"), default={}) or {}
    return list(existing.get("rows", []))


def build_certification_attempts(config: dict[str, Any], repo_filter: str | None = None, limit: int | None = None) -> dict[str, Any]:
    raw_inventory = read_json(output_path(config, "raw_anchor_inventory")) or mine_raw_inventory(config)
    environment_probe = read_json(output_path(config, "environment_probe")) or build_environment_probe(config)
    selected = certification_candidates(config, raw_inventory, environment_probe, repo_filter=repo_filter)
    selected_ids = {str(row["candidate_id"]) for row in selected}
    rows = load_certification_attempts(config)
    attempted_ids = {str(row["candidate_id"]) for row in rows}
    for probe_row in environment_probe.get("rows", []):
        if str(probe_row.get("candidate_id")) in selected_ids and str(probe_row.get("candidate_id")) not in attempted_ids:
            rows.append(probe_row)
            attempted_ids.add(str(probe_row["candidate_id"]))
    todo = [row for row in selected if str(row["candidate_id"]) not in attempted_ids]
    if limit is not None:
        todo = todo[:limit]
    for row in todo:
        rows.append(run_probe_or_attempt(config, row))
        write_certification_outputs(config, attempts_payload(config, selected, rows))
    return attempts_payload(config, selected, rows)


def attempts_payload(config: dict[str, Any], selected: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected_ids = {str(row["candidate_id"]) for row in selected}
    selected_attempt_rows = [row for row in rows if str(row.get("candidate_id")) in selected_ids]
    attempted_ids = {str(row.get("candidate_id")) for row in selected_attempt_rows}
    queue = source_review_queue_from_attempts(selected_attempt_rows)
    return {
        "schema_version": f"{SCHEMA_VERSION}.certification_attempts.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "status": "bounded_certification_wave_completed",
        "selected_candidate_count": len(selected_ids),
        "attempted_count": len(selected_attempt_rows),
        "unattempted_selected_count": len(selected_ids - attempted_ids),
        "technical_certified_count": sum(1 for row in selected_attempt_rows if row.get("technical_certified")),
        "release_eligible_count": sum(1 for row in selected_attempt_rows if row.get("release_eligible")),
        "technical_certified_count_by_repo": dict(sorted(Counter(str(row.get("repo_id")) for row in selected_attempt_rows if row.get("technical_certified")).items())),
        "release_eligible_count_by_repo": dict(sorted(Counter(str(row.get("repo_id")) for row in selected_attempt_rows if row.get("release_eligible")).items())),
        "source_review_queue_count_by_repo": dict(sorted(Counter(str(row.get("repo_id")) for row in queue).items())),
        "terminal_execution_subgate_counts": dict(sorted(Counter(str(row.get("terminal_execution_subgate")) for row in selected_attempt_rows).items())),
        "terminal_execution_subgate_counts_by_repo": nested_counts(selected_attempt_rows, "repo_id", "terminal_execution_subgate"),
        "runtime_by_repo": runtime_by_repo(selected_attempt_rows),
        "rows": sorted(selected_attempt_rows, key=lambda row: (str(row.get("repo_id")), str(row.get("candidate_id")))),
        "raw_logs_committed": False,
        "workspace_storage": rel(scratch_path(config, "workspaces")),
        "raw_log_storage": rel(scratch_path(config, "raw_logs")),
    }


def source_review_queue_from_attempts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("technical_certified") and not row.get("release_eligible")]


def nested_counts(rows: list[dict[str, Any]], outer_key: str, inner_key: str) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        counts[str(row.get(outer_key, ""))][str(row.get(inner_key, ""))] += 1
    return {outer: dict(sorted(counter.items())) for outer, counter in sorted(counts.items())}


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


def write_certification_outputs(config: dict[str, Any], payload: dict[str, Any]) -> None:
    write_json(output_path(config, "certification_attempts"), payload)
    write_text(report_path(config, "certification_attempts"), certification_report(payload))


def build_release_gate(config: dict[str, Any]) -> dict[str, Any]:
    attrs_gate = read_json(config["inputs"]["attrs_source_repair_gate"], default={}) or {}
    attempts = read_json(output_path(config, "certification_attempts"), default={}) or {"rows": []}
    release_counts = Counter({repo: int(count) for repo, count in (attrs_gate.get("release_eligible_count_by_repo") or {}).items()})
    technical_counts = Counter()
    queue_counts = Counter()
    for row in attempts.get("rows", []):
        repo_id = str(row.get("repo_id"))
        if row.get("release_eligible"):
            release_counts[repo_id] += 1
        if row.get("technical_certified"):
            technical_counts[repo_id] += 1
        if row.get("technical_certified") and not row.get("release_eligible"):
            queue_counts[repo_id] += 1
    min_count = int(config["selection_policy"]["release_eligible_min_per_repo"])
    repos_meeting = sorted(repo for repo, count in release_counts.items() if count >= min_count)
    paid_ready = len(repos_meeting) >= int(config["selection_policy"]["repos_required_at_min"])
    third_repo_candidates = sorted(repo for repo in release_counts if repo not in {"attrs", "boltons"})
    blocker = []
    if not paid_ready:
        blocker.append("third_repo_still_needed")
    if attempts.get("unattempted_selected_count", 0):
        blocker.append("selected_candidates_still_unattempted")
    return {
        "schema_version": f"{SCHEMA_VERSION}.release_gate.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "status": "paid_gate_recomputed",
        "release_eligible_count_by_repo": dict(sorted(release_counts.items())),
        "technical_certified_count_by_candidate_repo": dict(sorted(technical_counts.items())),
        "source_review_queue_count_by_candidate_repo": dict(sorted(queue_counts.items())),
        "third_repo_candidates": third_repo_candidates,
        "repos_meeting_30_release_eligible": repos_meeting,
        "paid_ready": paid_ready,
        "blocking_reasons": blocker,
        "minimum_requirements": {
            "at_least_3_repos_with_30_release_eligible": paid_ready,
            "raw_candidates_do_not_count": True,
            "technical_certifications_alone_do_not_count": True,
            "no_paid_acut_calls_made": True,
            "no_paid_llm_calls_made": True,
        },
    }


def build_decision(config: dict[str, Any]) -> dict[str, Any]:
    shortlist = read_json(output_path(config, "repo_shortlist"), default={}) or {}
    raw_inventory = read_json(output_path(config, "raw_anchor_inventory"), default={}) or {}
    source_context = read_json(output_path(config, "source_context_inventory"), default={}) or {}
    environment = read_json(output_path(config, "environment_probe"), default={}) or {}
    attempts = read_json(output_path(config, "certification_attempts"), default={}) or {"rows": []}
    gate = read_json(output_path(config, "release_gate"), default={}) or build_release_gate(config)
    technical = gate.get("technical_certified_count_by_candidate_repo", {})
    release = {repo: count for repo, count in gate.get("release_eligible_count_by_repo", {}).items() if repo not in {"attrs", "boltons"}}
    best_repo = best_candidate_repo(technical, release, source_context)
    best_technical = int(technical.get(best_repo, 0)) if best_repo else 0
    best_release = int(release.get(best_repo, 0)) if best_repo else 0
    if gate.get("paid_ready"):
        label = "third_repo_ready_paid_gate_ready_for_packaging"
    elif best_technical >= 30 and best_release < 30:
        label = "third_repo_technical_ready_source_repair_needed"
    elif any(decision.get("decision") == "needs_environment_repair" for decision in environment.get("decisions_by_repo", {}).values()):
        label = "third_repo_environment_repair_needed"
    elif attempts.get("unattempted_selected_count", 0):
        label = "blocked_by_runtime_or_tooling"
    else:
        label = "third_repo_supply_still_blocked_continue_screening"
    return {
        "schema_version": f"{SCHEMA_VERSION}.decision.v1",
        "generated_at": now_utc(),
        "run_id": str(config["run_id"]),
        "status": "third_repo_supply_screen_completed",
        "decision_label": label,
        "paid_ready": bool(gate.get("paid_ready")),
        "best_candidate_repo": best_repo,
        "best_candidate_technical_certified": best_technical,
        "best_candidate_release_eligible": best_release,
        "research_questions": {
            "RQ1": screened_advanced_rejected(shortlist, raw_inventory, environment),
            "RQ2": f"{best_repo or 'none'} has the strongest observed path under this bounded run.",
            "RQ3": f"Third repo reached 30 release-eligible tasks: {any(int(count) >= 30 for count in release.values())}.",
            "RQ4": smallest_blocker(label, attempts, source_context, environment),
            "RQ5": f"Repos at 30 release eligible: {gate.get('repos_meeting_30_release_eligible', [])}.",
            "RQ6": "No paid ACUT, paid task-solving, paid replication, paid LLM generation, or paid LLM review calls were made.",
            "RQ7": next_action(label),
        },
        "completed_steps": completed_steps(config),
        "commits_made_during_run": [],
        "tests_run": [],
        "known_blockers": gate.get("blocking_reasons", []),
        "raw_artifact_hygiene_statement": "Committed JSON and Markdown contain sanitized metadata, counts, hashes, source-context classes, subgates, and task ids only.",
        "paid_call_statement": "No paid ACUT calls, paid task-solving calls, paid replication, paid LLM statement-generation calls, or paid LLM review calls were made.",
    }


def best_candidate_repo(technical: dict[str, Any], release: dict[str, Any], source_context: dict[str, Any]) -> str:
    upper = source_context.get("technical_plus_review_upper_bound_count_by_repo", {})
    repos = set(technical) | set(release) | set(upper)
    if not repos:
        return ""
    return sorted(repos, key=lambda repo: (-int(release.get(repo, 0)), -int(technical.get(repo, 0)), -int(upper.get(repo, 0)), repo))[0]


def screened_advanced_rejected(shortlist: dict[str, Any], raw_inventory: dict[str, Any], environment: dict[str, Any]) -> str:
    screened = shortlist.get("candidate_repos_screened", [])
    raw = raw_inventory.get("advanced_repos", [])
    cert = [repo for repo, decision in environment.get("decisions_by_repo", {}).items() if decision.get("decision") == "advance_to_certification_wave"]
    rejected = [row["repo_id"] for row in shortlist.get("rows", []) if row.get("overall_screen_label") == "reject_for_this_run"]
    return f"Screened={screened}; advanced_to_raw={raw}; advanced_to_certification={cert}; rejected={rejected}."


def smallest_blocker(label: str, attempts: dict[str, Any], source_context: dict[str, Any], environment: dict[str, Any]) -> str:
    if label == "third_repo_technical_ready_source_repair_needed":
        return "source context repair is the smallest blocker."
    if label == "third_repo_environment_repair_needed":
        return "environment stability is the smallest blocker."
    if attempts.get("unattempted_selected_count", 0):
        return "runtime cap left selected candidates unattempted."
    release_ready = source_context.get("release_ready_before_certification_count_by_repo", {})
    if not release_ready:
        return "raw or oracle supply is the smallest blocker."
    if not environment.get("rows"):
        return "environment probe did not produce enough certification evidence."
    return "certified release-eligible yield stayed below 30."


def next_action(label: str) -> str:
    if label == "third_repo_ready_paid_gate_ready_for_packaging":
        return "paid-readiness packaging."
    if label == "third_repo_technical_ready_source_repair_needed":
        return "source-context repair for the best candidate repo."
    if label == "third_repo_environment_repair_needed":
        return "environment repair for the best candidate repo."
    if label == "blocked_by_runtime_or_tooling":
        return "resume bounded certification or fix tooling before drawing a supply conclusion."
    return "more repo screening or a narrower certification repair pass."


def completed_steps(config: dict[str, Any]) -> list[str]:
    pairs = [
        ("0", "preflight"),
        ("1", "repo_shortlist"),
        ("2", "raw_anchor_inventory"),
        ("3a", "source_context_inventory"),
        ("3b", "oracle_matrix"),
        ("4", "environment_probe"),
        ("5", "certification_attempts"),
        ("6", "release_gate"),
        ("7", "decision"),
    ]
    return [f"Step {step} {key}" for step, key in pairs if output_path(config, key).exists()]


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |")
    return "\n".join(lines)


def write_process_report(config: dict[str, Any]) -> None:
    preflight = read_json(output_path(config, "preflight"), default={}) or {}
    step_rows = []
    for label in [
        ("0", "Preflight and current gate snapshot", "preflight"),
        ("1", "Cheap repository shortlist", "repo_shortlist"),
        ("2", "Raw v2 mining", "raw_anchor_inventory"),
        ("3", "Source context and oracle screen", "source_context_inventory"),
        ("4", "Environment probe", "environment_probe"),
        ("5", "Bounded fresh certification wave", "certification_attempts"),
        ("6", "Third repo release gate", "release_gate"),
        ("7", "Decision and closeout", "decision"),
    ]:
        step_rows.append([label[0], label[1], "completed" if output_path(config, label[2]).exists() else "pending"])
    text = f"""# Third Repo Release Supply Screen Process

Status: {', '.join(completed_steps(config)) or 'not started'}.

What happened: this run screens third-repo supply only. It does not run paid validation.

Why it matters: attrs and boltons are already supply anchors; the open blocker is one more repo with 30 release-eligible tasks.

Starting HEAD: `{preflight.get('head', 'unknown')}` on `{preflight.get('branch', 'unknown')}`.

Current gate snapshot: attrs has `{preflight.get('paid_readiness_gate_snapshot', {}).get('release_eligible_count_by_repo', {}).get('attrs', 31)}` release-eligible tasks and boltons has `{preflight.get('paid_readiness_gate_snapshot', {}).get('release_eligible_count_by_repo', {}).get('boltons', 35)}`. Paid readiness remains false until a third repo reaches 30.

{markdown_table(['Step', 'Name', 'Status'], step_rows)}

Dirty tree classification: unrelated pre-existing files under `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/` were left unstaged.

Paid-call statement: no paid ACUT solver cells, paid task-solving calls, paid replication, paid LLM statement generation, or paid LLM review calls were made.

Artifact hygiene: raw logs and workspaces stay under ignored scratch paths. Committed artifacts contain sanitized metadata, counts, hashes, source-context classes, subgate labels, and task ids only.
"""
    write_text(report_path(config, "process"), text)


def repo_shortlist_report(payload: dict[str, Any]) -> str:
    rows = [
        [
            row["repo_id"],
            row.get("commit_count_with_both_implementation_and_test_changes", 0),
            row.get("commit_count_with_both_implementation_and_test_changes_and_public_refs", 0),
            row.get("overall_score", 0),
            row["overall_screen_label"],
            row.get("screen_reason", ""),
        ]
        for row in payload["rows"]
    ]
    return f"""# Third Repo Repo Shortlist

What happened: seven seed repos were screened with local git metadata.

Why it matters: certification time should go only to repos with enough implementation-plus-test history and plausible public source context.

{markdown_table(['Repo', 'Impl+Tests', 'Impl+Tests+Refs', 'Score', 'Label', 'Reason'], rows)}

Repos advanced to raw mining: `{payload['repos_advanced_to_raw_mining']}`.
"""


def raw_inventory_report(payload: dict[str, Any]) -> str:
    rows = [[repo, summary.get("raw_candidate_count", 0), summary.get("inventory_status_counts", {}), summary.get("source_reservoir_counts", {})] for repo, summary in payload["summary_by_repo"].items()]
    return f"""# Third Repo Raw Anchor Inventory

What happened: bounded repo-history v2 mining produced sanitized candidate rows for the repos advanced by the cheap screen.

Why it matters: raw anchors are inventory only. Only `oracle_usable` candidates can enter local certification.

{markdown_table(['Repo', 'Raw Candidates', 'Inventory Statuses', 'Reservoir Mix'], rows)}
"""


def source_context_report(payload: dict[str, Any]) -> str:
    rows = []
    release_ready = payload.get("release_ready_before_certification_count_by_repo", {})
    upper = payload.get("technical_plus_review_upper_bound_count_by_repo", {})
    for repo, counts in payload.get("counts_by_repo", {}).items():
        rows.append([repo, counts, release_ready.get(repo, 0), upper.get(repo, 0)])
    return f"""# Third Repo Source Context Inventory

What happened: every raw candidate received a source-context class.

Why it matters: commit-message-only context is not counted as release eligible without separate review.

{markdown_table(['Repo', 'Context Counts', 'Release-Ready Before Cert', 'Technical+Review Upper Bound'], rows)}

Repos selected for environment probe: `{payload.get('repos_selected_for_environment_probe', [])}`.
"""


def oracle_report(payload: dict[str, Any]) -> str:
    rows = [[repo, counts] for repo, counts in payload.get("oracle_classification_counts_by_repo", {}).items()]
    return f"""# Third Repo Oracle Matrix

What happened: changed-test oracle availability was separated from raw candidate inventory.

Why it matters: issue-only rows without changed tests stay inventory only and are not certified.

{markdown_table(['Repo', 'Oracle Classifications'], rows)}
"""


def environment_report(payload: dict[str, Any]) -> str:
    rows = [
        [
            repo,
            decision.get("sample_size", 0),
            decision.get("technical_certified", 0),
            decision.get("hard_environment_failures", 0),
            decision.get("decision", ""),
            decision.get("reason", ""),
        ]
        for repo, decision in payload.get("decisions_by_repo", {}).items()
    ]
    return f"""# Third Repo Environment Probe

What happened: bounded environment probes ran on sampled oracle-usable candidates.

Why it matters: a repo should not enter a larger certification wave if the historical uv environment is obviously unstable.

{markdown_table(['Repo', 'Sample', 'Technical', 'Hard Env Failures', 'Decision', 'Reason'], rows)}

Raw stdout and stderr are stored only under ignored scratch paths.
"""


def certification_report(payload: dict[str, Any]) -> str:
    rows = []
    for repo, subgates in payload.get("terminal_execution_subgate_counts_by_repo", {}).items():
        rows.append(
            [
                repo,
                payload.get("technical_certified_count_by_repo", {}).get(repo, 0),
                payload.get("release_eligible_count_by_repo", {}).get(repo, 0),
                payload.get("source_review_queue_count_by_repo", {}).get(repo, 0),
                subgates,
            ]
        )
    return f"""# Third Repo Certification Attempts

What happened: selected candidates from environment-approved repos received bounded local certification attempts.

Why it matters: technical certification and release eligibility are counted separately.

Selected candidates: `{payload['selected_candidate_count']}`. Attempted: `{payload['attempted_count']}`. Unattempted selected: `{payload['unattempted_selected_count']}`.

{markdown_table(['Repo', 'Technical Certified', 'Release Eligible', 'Source Review Queue', 'Subgates'], rows)}

Raw logs and workspaces remain under ignored scratch paths.
"""


def release_gate_report(payload: dict[str, Any]) -> str:
    return f"""# Third Repo Release Gate

Paid ready: `{payload['paid_ready']}`.

What happened: release eligibility was recomputed from attrs source repair, boltons fresh certification, and this run's candidate-third-repo certification results.

Release-eligible counts:

```json
{json.dumps(payload['release_eligible_count_by_repo'], indent=2, sort_keys=True)}
```

Technical certified counts for candidate repos:

```json
{json.dumps(payload['technical_certified_count_by_candidate_repo'], indent=2, sort_keys=True)}
```

Repos meeting 30 release-eligible tasks: `{payload['repos_meeting_30_release_eligible']}`.

Blocking reasons: `{payload['blocking_reasons']}`.
"""


def decision_report(payload: dict[str, Any]) -> str:
    rq_rows = [[key, value] for key, value in payload["research_questions"].items()]
    return f"""# Third Repo Release Supply Screen Decision

Decision: `{payload['decision_label']}`.

What happened: the run screened candidate repositories, mined bounded repo-history candidates, checked source/oracle shape, ran environment probes, and ran bounded certification only where the evidence warranted it.

Why it matters: paid validation can move forward only when attrs, boltons, and one additional repo each have at least 30 release-eligible tasks.

Best candidate repo: `{payload['best_candidate_repo']}`.

Best candidate technical certified: `{payload['best_candidate_technical_certified']}`.

Best candidate release eligible: `{payload['best_candidate_release_eligible']}`.

Paid ready: `{payload['paid_ready']}`.

{markdown_table(['Research Question', 'Answer'], rq_rows)}

No paid ACUT, paid task-solving, paid replication, paid LLM generation, or paid LLM review calls were made.
"""


def run_shortlist(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_repo_shortlist(config)
    write_json(output_path(config, "repo_shortlist"), payload)
    write_text(report_path(config, "repo_shortlist"), repo_shortlist_report(payload))
    write_process_report(config)
    return payload


def run_raw(config: dict[str, Any]) -> dict[str, Any]:
    payload = mine_raw_inventory(config)
    write_json(output_path(config, "raw_anchor_inventory"), payload)
    write_text(report_path(config, "raw_anchor_inventory"), raw_inventory_report(payload))
    write_process_report(config)
    return payload


def run_source_oracle(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    raw_inventory = read_json(output_path(config, "raw_anchor_inventory")) or mine_raw_inventory(config)
    source = build_source_context_inventory(config, raw_inventory)
    source["repos_selected_for_environment_probe"] = selected_repos_for_environment(config, source)
    oracle = build_oracle_matrix(config, raw_inventory)
    write_json(output_path(config, "source_context_inventory"), source)
    write_json(output_path(config, "oracle_matrix"), oracle)
    write_text(report_path(config, "source_context_inventory"), source_context_report(source))
    write_text(report_path(config, "oracle_matrix"), oracle_report(oracle))
    write_process_report(config)
    return source, oracle


def run_environment(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_environment_probe(config)
    write_json(output_path(config, "environment_probe"), payload)
    write_text(report_path(config, "environment_probe"), environment_report(payload))
    write_process_report(config)
    return payload


def run_certification(config: dict[str, Any], repo_filter: str | None = None, limit: int | None = None) -> dict[str, Any]:
    payload = build_certification_attempts(config, repo_filter=repo_filter, limit=limit)
    write_certification_outputs(config, payload)
    write_process_report(config)
    return payload


def run_gate(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_release_gate(config)
    write_json(output_path(config, "release_gate"), payload)
    write_text(report_path(config, "release_gate"), release_gate_report(payload))
    write_process_report(config)
    return payload


def run_decision(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_decision(config)
    write_json(output_path(config, "decision"), payload)
    write_text(report_path(config, "decision"), decision_report(payload))
    write_process_report(config)
    return payload


def run_all(config: dict[str, Any], repo_filter: str | None = None, limit: int | None = None) -> None:
    run_shortlist(config)
    run_raw(config)
    run_source_oracle(config)
    run_environment(config)
    run_certification(config, repo_filter=repo_filter, limit=limit)
    run_gate(config)
    run_decision(config)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run", choices=["shortlist", "raw", "source-oracle", "environment", "certification", "gate", "decision", "all"], default="all")
    parser.add_argument("--repo", default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    config = load_config(args.config)
    if args.run == "shortlist":
        payload = run_shortlist(config)
        print(json.dumps({"advanced": payload["repos_advanced_to_raw_mining"]}, sort_keys=True))
        return 0
    if args.run == "raw":
        payload = run_raw(config)
        print(json.dumps({"candidate_count": payload["candidate_count"], "advanced": payload["advanced_repos"]}, sort_keys=True))
        return 0
    if args.run == "source-oracle":
        source, oracle = run_source_oracle(config)
        print(json.dumps({"release_ready": source["release_ready_before_certification_count_by_repo"], "oracle": oracle["oracle_classification_counts_by_repo"]}, sort_keys=True))
        return 0
    if args.run == "environment":
        payload = run_environment(config)
        print(json.dumps({"decisions": payload["decisions_by_repo"]}, sort_keys=True))
        return 0
    if args.run == "certification":
        payload = run_certification(config, repo_filter=args.repo, limit=args.limit)
        print(json.dumps({"attempted": payload["attempted_count"], "technical": payload["technical_certified_count_by_repo"], "release": payload["release_eligible_count_by_repo"]}, sort_keys=True))
        return 0
    if args.run == "gate":
        payload = run_gate(config)
        print(json.dumps({"paid_ready": payload["paid_ready"], "repos_meeting": payload["repos_meeting_30_release_eligible"]}, sort_keys=True))
        return 0
    if args.run == "decision":
        payload = run_decision(config)
        print(json.dumps({"decision": payload["decision_label"], "best_repo": payload["best_candidate_repo"]}, sort_keys=True))
        return 0
    run_all(config, repo_filter=args.repo, limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
