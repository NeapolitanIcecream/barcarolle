from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
DEFAULT_CONFIG = ROOT / "configs" / "phase1_clean_supply_breal_extension.yaml"

HARD_REJECT_BLOCKERS = {
    "previous_acut_outcome_seen",
    "non_leaky_problem_context_missing",
    "oracle_alignment_not_aligned",
    "project_or_docs_only_change",
    "solution_exposure_risk",
    "commit_message_only_source",
}


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
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


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
    if config.get("schema_version") != "barcarolle.phase1_clean_supply_breal_extension.v1":
        raise ValueError("unexpected clean supply B_real extension config schema_version")
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


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def repo_from_task_id(task_id: str) -> str:
    return task_id.split("__", 1)[0] if "__" in task_id else "unknown"


def unique_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def split_map_from_release(config: dict[str, Any]) -> dict[str, str]:
    release = read_json(artifact_path(config, "boltons_release"))
    split_map: dict[str, str] = {}
    for split, task_ids in release.get("splits", {}).items():
        for task_id in task_ids:
            split_map[str(task_id)] = str(split)
    for task in release.get("tasks", []):
        if task.get("task_id") and task.get("split"):
            split_map[str(task["task_id"])] = str(task["split"])
    return split_map


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


def by_task(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["task_id"]): row for row in rows if row.get("task_id")}


def load_task_evidence(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    candidates = by_task(read_jsonl(artifact_path(config, "boltons_certified_tasks")))
    candidate_sources = by_task(read_jsonl(PHASE0_ROOT / "candidate_sources" / "boltons_candidates.jsonl"))
    statements = by_task(read_jsonl(artifact_path(config, "boltons_task_statements")))
    reviews = by_task(read_jsonl(artifact_path(config, "boltons_review_records")))
    source_context = by_task(read_jsonl(PHASE0_ROOT / "candidate_sources" / "boltons_source_context.jsonl"))
    hardening = by_task(read_json(artifact_path(config, "hardening_overlay")).get("tasks", []))
    clean_supply_review_path = artifact_path(config, "clean_supply_review")
    clean_supply_reviews = by_task(read_json(clean_supply_review_path).get("reviews", [])) if clean_supply_review_path.exists() else {}
    split_map = split_map_from_release(config)

    task_ids = (
        set(candidates)
        | set(candidate_sources)
        | set(statements)
        | set(reviews)
        | set(source_context)
        | set(hardening)
        | set(clean_supply_reviews)
    )
    evidence: dict[str, dict[str, Any]] = {}
    for task_id in sorted(task_ids):
        row: dict[str, Any] = {"task_id": task_id, "repo_id": repo_from_task_id(task_id)}
        for source in [candidate_sources, candidates, statements, reviews]:
            row.update(source.get(task_id, {}))
        if task_id in hardening:
            row["hardening"] = hardening[task_id]
        if task_id in clean_supply_reviews:
            row["prior_clean_supply_review"] = clean_supply_reviews[task_id]
        if task_id in source_context:
            row["source_context"] = source_context[task_id]
        row["split"] = split_map.get(task_id, row.get("split", "unknown"))
        evidence[task_id] = row
    return evidence


def source_context_status(row: dict[str, Any]) -> str:
    refs = [str(ref) for ref in row.get("allowed_context_refs", [])]
    if refs and all(ref.startswith(("pr:", "issue:", "manual:", "customer:")) for ref in refs):
        return "non_leaky_problem_context"
    if refs and all(ref.startswith("commit:") for ref in refs):
        return "commit_message_only_source"
    return "non_leaky_problem_context_missing"


def project_or_config_heavy(row: dict[str, Any]) -> bool:
    changed_files = [str(path) for path in row.get("changed_files", [])]
    project_files = [
        path
        for path in changed_files
        if path.startswith(".github/")
        or path in {"appveyor.yml", ".travis.yml", "tox.ini", "pyproject.toml", "setup.py", "setup.cfg"}
        or path.endswith((".rst", ".md", ".txt"))
    ]
    subject = str(row.get("subject") or "").lower()
    return len(project_files) >= 3 or "tox" in subject or "gh action" in subject or "github action" in subject


def project_or_docs_only(row: dict[str, Any]) -> bool:
    return not row.get("code_files") and bool(row.get("changed_files"))


def scope_clarity_status(row: dict[str, Any]) -> str:
    context = row.get("source_context") or {}
    summary = str(context.get("summary") or row.get("subject") or "").lower()
    body_summary = str(context.get("body_summary") or "").strip()
    if project_or_config_heavy(row) and (not body_summary or "tox" in summary or "gh action" in summary):
        return "ambiguous_project_heavy_context"
    return "clear_behavior_scope"


def solution_exposure_status(row: dict[str, Any]) -> str:
    hardening = row.get("hardening") or {}
    reject_reasons = {str(reason) for reason in hardening.get("hardened_reject_reasons", [])}
    if "solution_exposure_risk" in reject_reasons:
        return "solution_exposure_risk"
    return "none_detected"


def oracle_alignment_status(row: dict[str, Any]) -> str:
    prior_review = row.get("prior_clean_supply_review") or {}
    if prior_review.get("oracle_alignment_status") == "aligned":
        return "aligned"
    hardening = row.get("hardening") or {}
    status = hardening.get("oracle_alignment_status")
    if status == "aligned":
        return "aligned"
    if status == "manual_review_required":
        return "manual_review_required"
    return str(status or "missing_oracle_alignment")


def review_candidate_row(row: dict[str, Any], *, outcome_seen_task_ids: set[str]) -> dict[str, Any]:
    task_id = str(row["task_id"])
    reviewed = {
        "task_id": task_id,
        "split": row.get("split", "unknown"),
        "task_time": row.get("task_time"),
        "module_or_package": row.get("module_or_package", []),
        "subject": row.get("subject"),
        "allowed_context_refs": row.get("allowed_context_refs", []),
        "source_context_status": source_context_status(row),
        "oracle_alignment_status": oracle_alignment_status(row),
        "solution_exposure_risk": solution_exposure_status(row),
        "project_or_docs_only_risk": project_or_docs_only(row),
        "project_or_config_heavy_risk": project_or_config_heavy(row),
        "scope_clarity_status": scope_clarity_status(row),
        "outcome_seen": task_id in outcome_seen_task_ids,
        "candidate_filter_status": row.get("candidate_filter_status"),
        "current_hardened_status": (row.get("hardening") or {}).get("hardened_status"),
        "manual_review_reasons": row.get("manual_review_reasons", []),
        "changed_files": row.get("changed_files", []),
        "changed_line_total": int(row.get("changed_lines_added") or 0) + int(row.get("changed_lines_deleted") or 0),
    }
    reviewed.update(promotion_decision(reviewed))
    return reviewed


def promotion_decision(row: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if boolish(row.get("outcome_seen")):
        blockers.append("previous_acut_outcome_seen")
    source_status = str(row.get("source_context_status") or "")
    if source_status == "commit_message_only_source":
        blockers.append("commit_message_only_source")
    elif source_status not in {"non_leaky_problem_context", "non_leaky_context_found"}:
        blockers.append("non_leaky_problem_context_missing")
    if row.get("oracle_alignment_status") != "aligned":
        blockers.append("oracle_alignment_not_aligned")
    if str(row.get("solution_exposure_risk") or "").lower() not in {"", "none", "none_detected", "false"}:
        blockers.append("solution_exposure_risk")
    if boolish(row.get("project_or_docs_only_risk")):
        blockers.append("project_or_docs_only_change")
    if boolish(row.get("project_or_config_heavy_risk")) or row.get("scope_clarity_status") != "clear_behavior_scope":
        blockers.append("scope_context_project_heavy_or_ambiguous")

    blockers = unique_preserve(blockers)
    if any(blocker in HARD_REJECT_BLOCKERS for blocker in blockers):
        decision = "reject_for_clean_holdout"
    elif blockers:
        decision = "keep_manual_review_required"
    else:
        decision = "promote_to_clean_benchmark_candidate"
    return {"promotion_decision": decision, "promotion_blockers": blockers}


def overlay_payload(
    *,
    prior_promoted: dict[str, list[str]],
    new_promoted: list[dict[str, Any]],
    minimum: dict[str, int],
) -> dict[str, Any]:
    promoted_by_split = {split: unique_preserve(list(task_ids)) for split, task_ids in prior_promoted.items()}
    for row in new_promoted:
        split = str(row.get("split") or "")
        task_id = str(row.get("task_id") or "")
        if not split or not task_id:
            continue
        promoted_by_split.setdefault(split, [])
        promoted_by_split[split] = unique_preserve(promoted_by_split[split] + [task_id])
    for split in minimum:
        promoted_by_split.setdefault(split, [])
    clean_supply_ready = all(len(promoted_by_split.get(split, [])) >= int(required) for split, required in minimum.items())
    return {
        "schema_version": "barcarolle.phase1.clean_supply_breal_extension_overlay.v1",
        "generated_at": now_utc(),
        "evidence_level": "clean_supply_candidate_overlay",
        "promoted_by_split": promoted_by_split,
        "promoted_task_ids": unique_preserve([task_id for ids in promoted_by_split.values() for task_id in ids]),
        "newly_promoted_task_ids": unique_preserve([str(row["task_id"]) for row in new_promoted if row.get("task_id")]),
        "minimum_clean_split": minimum,
        "clean_supply_ready": clean_supply_ready,
        "predictive_validity_established": False,
    }


def target_minimum(config: dict[str, Any]) -> dict[str, int]:
    raw = config["target"]["minimum_clean_split"]
    return {str(split): int(count) for split, count in raw.items()}


def existing_promoted(config: dict[str, Any]) -> dict[str, list[str]]:
    raw = config["target"].get("existing_promoted_clean_supply", {})
    return {str(split): [str(task_id) for task_id in task_ids] for split, task_ids in raw.items()}


def candidate_task_ids(config: dict[str, Any]) -> list[str]:
    target = [str(task_id) for task_id in config["candidate_priority"].get("deep_review_first", [])]
    target.extend(str(task_id) for task_id in config["candidate_priority"].get("repair_only_if_non_leaky", []))
    for task_ids in existing_promoted(config).values():
        target.extend(task_ids)
    return unique_preserve(target)


def audit_payload(config: dict[str, Any]) -> dict[str, Any]:
    evidence = load_task_evidence(config)
    outcome_seen = load_outcome_seen_task_ids(config)
    reviews = []
    for task_id in candidate_task_ids(config):
        if task_id in evidence:
            reviews.append(review_candidate_row(evidence[task_id], outcome_seen_task_ids=outcome_seen))
    promoted = existing_promoted(config)
    by_decision = Counter(row["promotion_decision"] for row in reviews)
    return {
        "schema_version": "barcarolle.phase1.clean_supply_breal_candidate_audit.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "repo_id": config["target"]["repo_id"],
        "paid_llm_calls_made": False,
        "paid_acut_calls_made": False,
        "current_promoted_by_split": promoted,
        "minimum_clean_split": target_minimum(config),
        "current_clean_supply_ready": overlay_payload(prior_promoted=promoted, new_promoted=[], minimum=target_minimum(config))[
            "clean_supply_ready"
        ],
        "candidate_reviews": reviews,
        "candidate_count": len(reviews),
        "candidate_decision_counts": dict(by_decision),
        "recommended_action": "review_boltons_014_first",
        "predictive_validity_established": False,
    }


def audit_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Clean Supply B_real Candidate Audit",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Repo: `{payload['repo_id']}`.",
        f"- Paid LLM calls made: `{str(payload['paid_llm_calls_made']).lower()}`.",
        f"- Paid ACUT calls made: `{str(payload['paid_acut_calls_made']).lower()}`.",
        f"- Current clean supply ready: `{str(payload['current_clean_supply_ready']).lower()}`.",
        f"- Predictive validity established: `false`.",
        "",
        "| Task | Split | Decision | Blockers |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["candidate_reviews"]:
        blockers = ", ".join(row.get("promotion_blockers", [])) or "none"
        lines.append(f"| `{row['task_id']}` | `{row.get('split')}` | `{row['promotion_decision']}` | `{blockers}` |")
    lines.extend(["", f"Recommended action: `{payload['recommended_action']}`."])
    return "\n".join(lines)


def run_audit_candidates(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    payload = audit_payload(config)
    write_json(result_path("phase1_clean_supply_breal_candidate_audit.json"), payload)
    write_text(report_path("phase1_clean_supply_breal_candidate_audit.md"), audit_report(payload))
    return payload


def review_014_payload(config: dict[str, Any]) -> dict[str, Any]:
    evidence = load_task_evidence(config)
    outcome_seen = load_outcome_seen_task_ids(config)
    task_id = str(config["primary_candidate"]["task_id"])
    if task_id not in evidence:
        raise KeyError(f"missing primary candidate evidence: {task_id}")
    review = review_candidate_row(evidence[task_id], outcome_seen_task_ids=outcome_seen)
    source_context = evidence[task_id].get("source_context") or {}
    return {
        "schema_version": "barcarolle.phase1.clean_supply_boltons_014_review.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "paid_llm_calls_made": False,
        "paid_acut_calls_made": False,
        "task_id": task_id,
        "review": review,
        "sanitized_public_context": {
            "allowed_context_refs": review.get("allowed_context_refs", []),
            "summary": source_context.get("summary"),
            "body_summary_available": bool(str(source_context.get("body_summary") or "").strip()),
        },
        "promotion_decision": review["promotion_decision"],
        "promotion_blockers": review["promotion_blockers"],
        "predictive_validity_established": False,
    }


def review_014_report(payload: dict[str, Any]) -> str:
    review = payload["review"]
    blockers = ", ".join(payload["promotion_blockers"]) or "none"
    return "\n".join(
        [
            "# Phase 1 Boltons 014 Clean Supply Review",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Task: `{payload['task_id']}`.",
            f"- Decision: `{payload['promotion_decision']}`.",
            f"- Blockers: `{blockers}`.",
            f"- Public context summary: `{payload['sanitized_public_context'].get('summary')}`.",
            f"- Public body summary available: `{str(payload['sanitized_public_context'].get('body_summary_available')).lower()}`.",
            f"- Project/config heavy risk: `{str(review.get('project_or_config_heavy_risk')).lower()}`.",
            f"- Scope clarity: `{review.get('scope_clarity_status')}`.",
            f"- Predictive validity established: `false`.",
            "",
            "The public context for this candidate is infrastructure-oriented, while the behavior signal would require inferring from the patch and tests. The task is therefore not promoted into clean holdout supply.",
        ]
    )


def run_review_014(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    payload = review_014_payload(config)
    write_json(result_path("phase1_clean_supply_boltons_014_review.json"), payload)
    write_text(report_path("phase1_clean_supply_boltons_014_review.md"), review_014_report(payload))
    return payload


def mine_extension_payload(config: dict[str, Any]) -> dict[str, Any]:
    evidence = load_task_evidence(config)
    outcome_seen = load_outcome_seen_task_ids(config)
    repair_task_ids = [str(task_id) for task_id in config["candidate_priority"].get("repair_only_if_non_leaky", [])]
    reviews = []
    source_rows = []
    review_rows = []
    for task_id in repair_task_ids:
        if task_id not in evidence:
            continue
        review = review_candidate_row(evidence[task_id], outcome_seen_task_ids=outcome_seen)
        review["extension_action"] = (
            "promote_to_clean_overlay"
            if review["promotion_decision"] == "promote_to_clean_benchmark_candidate"
            else "reject_for_extension_overlay"
        )
        reviews.append(review)
        source_rows.append(
            {
                "schema_version": "barcarolle.phase1.clean_supply_breal_extension_candidate_source.v1",
                "task_id": task_id,
                "repo_id": config["target"]["repo_id"],
                "split": review.get("split"),
                "source_context_status": review.get("source_context_status"),
                "promotion_decision": review["promotion_decision"],
                "promotion_blockers": review["promotion_blockers"],
            }
        )
        review_rows.append(
            {
                "schema_version": "barcarolle.phase1.clean_supply_breal_extension_review.v1",
                "task_id": task_id,
                "split": review.get("split"),
                "promotion_decision": review["promotion_decision"],
                "promotion_blockers": review["promotion_blockers"],
                "extension_action": review["extension_action"],
            }
        )

    source_path = PHASE0_ROOT / "candidate_sources" / "boltons_clean_supply_breal_extension_candidates.jsonl"
    review_path = PHASE0_ROOT / "certified_tasks" / "boltons_clean_supply_breal_extension_reviews.jsonl"
    write_jsonl(source_path, source_rows)
    write_jsonl(review_path, review_rows)
    promoted = [row for row in reviews if row["promotion_decision"] == "promote_to_clean_benchmark_candidate"]
    return {
        "schema_version": "barcarolle.phase1.clean_supply_breal_extension_mining.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "paid_llm_calls_made": False,
        "paid_acut_calls_made": False,
        "extension_candidate_source": rel(source_path),
        "extension_review_records": rel(review_path),
        "candidate_reviews": reviews,
        "promoted_extension_task_ids": [row["task_id"] for row in promoted],
        "promoted_extension_count": len(promoted),
        "predictive_validity_established": False,
    }


def mining_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Clean Supply B_real Extension Mining",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Paid LLM calls made: `{str(payload['paid_llm_calls_made']).lower()}`.",
        f"- Paid ACUT calls made: `{str(payload['paid_acut_calls_made']).lower()}`.",
        f"- Promoted extension tasks: `{payload['promoted_extension_count']}`.",
        f"- Predictive validity established: `false`.",
        "",
        "| Task | Decision | Blockers |",
        "| --- | --- | --- |",
    ]
    for row in payload["candidate_reviews"]:
        blockers = ", ".join(row.get("promotion_blockers", [])) or "none"
        lines.append(f"| `{row['task_id']}` | `{row['promotion_decision']}` | `{blockers}` |")
    return "\n".join(lines)


def run_mine_extension(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    payload = mine_extension_payload(config)
    write_json(result_path("phase1_clean_supply_breal_extension_mining.json"), payload)
    write_text(report_path("phase1_clean_supply_breal_extension_mining.md"), mining_report(payload))
    return payload


def load_new_promoted_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    review_path = result_path("phase1_clean_supply_boltons_014_review.json")
    if review_path.exists():
        review = read_json(review_path).get("review", {})
        if review.get("promotion_decision") == "promote_to_clean_benchmark_candidate":
            rows.append({"task_id": review["task_id"], "split": review["split"]})
    mining_path = result_path("phase1_clean_supply_breal_extension_mining.json")
    if mining_path.exists():
        for review in read_json(mining_path).get("candidate_reviews", []):
            if review.get("promotion_decision") == "promote_to_clean_benchmark_candidate":
                rows.append({"task_id": review["task_id"], "split": review["split"]})
    return rows


def run_build_overlay(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    payload = overlay_payload(
        prior_promoted=existing_promoted(config),
        new_promoted=load_new_promoted_rows(),
        minimum=target_minimum(config),
    )
    payload["config"] = rel(config["_path"])
    payload["repo_id"] = config["target"]["repo_id"]
    payload["paid_llm_calls_made"] = False
    payload["paid_acut_calls_made"] = False
    write_json(result_path("phase1_clean_supply_breal_extension_overlay.json"), payload)
    write_text(report_path("phase1_clean_supply_breal_extension_overlay.md"), overlay_report(payload))
    return payload


def overlay_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Clean Supply B_real Extension Overlay",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Repo: `{payload.get('repo_id')}`.",
        f"- Clean supply ready: `{str(payload['clean_supply_ready']).lower()}`.",
        f"- Newly promoted tasks: `{len(payload['newly_promoted_task_ids'])}`.",
        f"- Predictive validity established: `false`.",
        "",
        "| Split | Promoted task count | Task IDs |",
        "| --- | ---: | --- |",
    ]
    for split, task_ids in payload["promoted_by_split"].items():
        lines.append(f"| `{split}` | {len(task_ids)} | {', '.join(f'`{task_id}`' for task_id in task_ids)} |")
    return "\n".join(lines)


def decision_payload(config: dict[str, Any]) -> dict[str, Any]:
    overlay_path = result_path("phase1_clean_supply_breal_extension_overlay.json")
    if not overlay_path.exists():
        raise FileNotFoundError(overlay_path)
    overlay = read_json(overlay_path)
    review_014 = read_json(result_path("phase1_clean_supply_boltons_014_review.json")) if result_path("phase1_clean_supply_boltons_014_review.json").exists() else {}
    mining = read_json(result_path("phase1_clean_supply_breal_extension_mining.json")) if result_path("phase1_clean_supply_breal_extension_mining.json").exists() else {}
    if overlay["clean_supply_ready"]:
        label = "clean_supply_ready_for_preregistered_validation"
        next_runbook = "run_preregistered_clean_future_holdout_validation"
    elif not mining and review_014.get("promotion_decision") != "promote_to_clean_benchmark_candidate":
        label = "clean_supply_needs_extension_mining"
        next_runbook = "mine_additional_clean_outcome_unseen_supply"
    else:
        label = "clean_supply_breal_extension_still_blocked"
        next_runbook = "continue_mining_clean_outcome_unseen_supply"
    return {
        "schema_version": "barcarolle.phase1.clean_supply_breal_extension_decision.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "paid_llm_calls_made": False,
        "paid_acut_calls_made": False,
        "repo_id": config["target"]["repo_id"],
        "primary_decision_label": label,
        "recommended_next_runbook": next_runbook,
        "clean_supply_ready": overlay["clean_supply_ready"],
        "clean_supply_promoted_by_split": overlay["promoted_by_split"],
        "newly_promoted_task_ids": overlay["newly_promoted_task_ids"],
        "boltons_014_decision": review_014.get("promotion_decision"),
        "boltons_014_blockers": review_014.get("promotion_blockers", []),
        "mining_promoted_extension_task_ids": mining.get("promoted_extension_task_ids", []),
        "strict_future_holdout_supply_status": "ready" if overlay["clean_supply_ready"] else "blocked",
        "predictive_validity_established": False,
        "allowed_claims": [
            "clean_supply_breal_extension_audited",
            "clean_supply_overlay_created",
            "strict_clean_future_holdout_still_blocked"
            if not overlay["clean_supply_ready"]
            else "clean_supply_ready_for_preregistered_validation",
            "insufficient_evidence_for_predictive_validity",
        ],
        "disallowed_claims": [
            "predictive_validity_established",
            "clean_future_holdout_validated_without_paid_holdout_run",
            "production_benchmark_ranking",
            "promotion_of_solution_leaky_or_project_heavy_tasks",
        ],
    }


def decision_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Clean Supply B_real Extension Decision",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Primary decision: `{payload['primary_decision_label']}`.",
            f"- Recommended next runbook: `{payload['recommended_next_runbook']}`.",
            f"- Clean supply ready: `{str(payload['clean_supply_ready']).lower()}`.",
            f"- Newly promoted tasks: `{len(payload['newly_promoted_task_ids'])}`.",
            f"- Boltons 014 decision: `{payload.get('boltons_014_decision')}`.",
            f"- Mining promoted extension tasks: `{len(payload.get('mining_promoted_extension_task_ids', []))}`.",
            f"- Paid LLM calls made: `{str(payload['paid_llm_calls_made']).lower()}`.",
            f"- Paid ACUT calls made: `{str(payload['paid_acut_calls_made']).lower()}`.",
            f"- Predictive validity established: `false`.",
            "",
            "The overlay does not promote outcome-seen, solution-leaky, or project-heavy ambiguous tasks. It therefore remains a local supply decision, not a validation result.",
        ]
    )


def run_decide(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    payload = decision_payload(config)
    write_json(result_path("phase1_clean_supply_breal_extension_decision.json"), payload)
    write_text(report_path("phase1_clean_supply_breal_extension_decision.md"), decision_report(payload))
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 1 clean B_real supply extension artifacts.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ["audit-candidates", "review-014", "mine-extension", "build-overlay", "decide"]:
        subparsers.add_parser(command)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    commands = {
        "audit-candidates": run_audit_candidates,
        "review-014": run_review_014,
        "mine-extension": run_mine_extension,
        "build-overlay": run_build_overlay,
        "decide": run_decide,
    }
    payload = commands[args.command](args)
    print(json.dumps({"status": "ok", "command": args.command, "primary_decision_label": payload.get("primary_decision_label")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
