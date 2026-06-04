from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
DEFAULT_CONFIG = ROOT / "configs" / "phase1_retrospective_validation_and_clean_supply.yaml"
SCOREABLE_TERMINAL_STATUSES = {"verified_pass", "verified_fail"}
NON_SCOREABLE_TERMINAL_STATUSES = {"invalid_output", "policy_violation", "timeout", "harness_error", "acut_harness_error"}


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != "barcarolle.phase1_retrospective_validation_and_clean_supply.v1":
        raise ValueError("unexpected retrospective validation config schema_version")
    config["_path"] = str(path)
    return config


def artifact_path(config: dict[str, Any], key: str) -> Path:
    raw = config["source_artifacts"][key]
    path = Path(str(raw))
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def repo_from_task_id(task_id: str) -> str:
    return task_id.split("__", 1)[0] if "__" in task_id else "unknown"


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def score_table_path(prefix: str) -> Path:
    return PHASE0_ROOT / "results" / f"{prefix}_score_table.csv"


def validate_evidence_level(evidence_level: str) -> None:
    if evidence_level != "outcome_seen_retrospective_locked":
        raise ValueError("outcome-seen rows may only be analyzed under retrospective evidence level")


def prefix_roles(primary_prefixes: dict[str, list[str]], diagnostic_prefixes: list[str]) -> dict[str, str]:
    roles = {}
    for prefixes in primary_prefixes.values():
        for prefix in prefixes:
            roles[prefix] = "primary_retrospective"
    for prefix in diagnostic_prefixes:
        roles[prefix] = "diagnostic_dev"
    return roles


def primary_eligible_rows(
    rows: list[dict[str, str]],
    *,
    primary_repos: set[str],
    excluded_repos: set[str],
    diagnostic_only_repos: set[str],
) -> list[dict[str, str]]:
    filtered = []
    for row in rows:
        repo_id = repo_from_task_id(row["task_id"])
        if repo_id in excluded_repos or repo_id in diagnostic_only_repos:
            continue
        if repo_id not in primary_repos:
            continue
        filtered.append(row)
    return filtered


def load_primary_rows(config: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    primary_prefixes = config["retrospective_track"]["primary_result_prefixes"]
    excluded_repos = set(config["retrospective_track"].get("excluded_target_repos", []))
    diagnostic_only_repos = set(config["retrospective_track"].get("diagnostic_only_repos", []))
    for repo_id, prefixes in primary_prefixes.items():
        for prefix in prefixes:
            source_path = score_table_path(prefix)
            for row in read_csv(source_path):
                row = dict(row)
                row["source_result_prefix"] = prefix
                row["source_score_table"] = rel(source_path)
                row_repo_id = repo_from_task_id(row["task_id"])
                if row_repo_id != repo_id:
                    continue
                if row_repo_id in excluded_repos or row_repo_id in diagnostic_only_repos:
                    continue
                rows.append(row)
    return rows


def split_rate(rows: list[dict[str, str]]) -> dict[str, Any]:
    scoreable = [row for row in rows if boolish(row.get("scoreable_cell")) and row.get("terminal_status") in SCOREABLE_TERMINAL_STATUSES]
    passes = [row for row in scoreable if row.get("terminal_status") == "verified_pass"]
    policy = [row for row in rows if row.get("terminal_status") == "policy_violation"]
    return {
        "cell_count": len(rows),
        "scoreable_cell_count": len(scoreable),
        "non_scoreable_count": len(rows) - len(scoreable),
        "policy_violation_count": len(policy),
        "pass_count": len(passes),
        "pass_rate": round(len(passes) / len(scoreable), 6) if scoreable else None,
    }


def repo_adapter_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    by_split = {split: split_rate([row for row in rows if row.get("split") == split]) for split in ["B_real", "W_real"]}
    b_rate = by_split["B_real"]["pass_rate"]
    w_rate = by_split["W_real"]["pass_rate"]
    absolute_error = None if b_rate is None or w_rate is None else round(abs(float(b_rate) - float(w_rate)), 6)
    return {
        **by_split,
        "absolute_error": absolute_error,
    }


def metrics_payload(plan: dict[str, Any], rows: list[dict[str, str]], cost_summary: dict[str, Any]) -> dict[str, Any]:
    repo_adapter_errors: dict[str, Any] = {}
    errors = []
    for repo_id in sorted({repo_from_task_id(row["task_id"]) for row in rows}):
        repo_rows = [row for row in rows if repo_from_task_id(row["task_id"]) == repo_id]
        repo_adapter_errors[repo_id] = {}
        for adapter_id in sorted({row.get("adapter_id", "") for row in repo_rows}):
            adapter_rows = [row for row in repo_rows if row.get("adapter_id") == adapter_id]
            metrics = repo_adapter_metrics(adapter_rows)
            repo_adapter_errors[repo_id][adapter_id] = metrics
            if metrics["absolute_error"] is not None:
                errors.append(float(metrics["absolute_error"]))
    policy_violations = sum(1 for row in rows if row.get("terminal_status") == "policy_violation")
    scoreable = sum(1 for row in rows if boolish(row.get("scoreable_cell")) and row.get("terminal_status") in SCOREABLE_TERMINAL_STATUSES)
    warnings = []
    if scoreable < 24:
        warnings.append("retrospective_sample_underpowered_for_predictive_validity")
    return {
        "schema_version": "barcarolle.phase1.retrospective_validation_metrics.v1",
        "generated_at": now_utc(),
        "evidence_level": "outcome_seen_retrospective_locked",
        "clean_future_holdout": False,
        "predictive_validity_established": False,
        "included_repos": plan.get("included_repos", []),
        "included_task_ids": plan.get("included_task_ids", []),
        "included_row_count": len(rows),
        "scoreable_cell_count": scoreable,
        "policy_violation_count": policy_violations,
        "repo_adapter_errors": repo_adapter_errors,
        "pooled_mae": round(sum(errors) / len(errors), 6) if errors else None,
        "warnings": warnings,
        "cost_summary": cost_summary,
    }


def build_plan(config: dict[str, Any]) -> dict[str, Any]:
    evidence_level = config["evidence_levels"]["primary_retrospective"]
    validate_evidence_level(evidence_level)
    rows = load_primary_rows(config)
    included_task_ids = sorted({row["task_id"] for row in rows})
    primary_prefixes = {
        repo_id: list(prefixes)
        for repo_id, prefixes in config["retrospective_track"]["primary_result_prefixes"].items()
    }
    return {
        "schema_version": "barcarolle.phase1.retrospective_validation_plan.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "evidence_level": evidence_level,
        "clean_future_holdout": False,
        "predictive_validity_established": False,
        "included_repos": sorted(primary_prefixes),
        "included_task_ids": included_task_ids,
        "included_task_count": len(included_task_ids),
        "included_row_count": len(rows),
        "primary_prefixes": primary_prefixes,
        "diagnostic_prefixes": config["retrospective_track"].get("diagnostic_result_prefixes", []),
        "excluded_target_repos": config["retrospective_track"].get("excluded_target_repos", []),
        "diagnostic_only_repos": config["retrospective_track"].get("diagnostic_only_repos", []),
        "inclusion_rule": config["retrospective_track"]["inclusion_rule"],
        "rows_by_prefix": dict(Counter(row["source_result_prefix"] for row in rows)),
        "rows_by_repo": dict(Counter(repo_from_task_id(row["task_id"]) for row in rows)),
    }


def plan_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Retrospective Validation Plan",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Evidence level: `{payload['evidence_level']}`.",
        "- Clean future holdout: `false`.",
        "- Predictive validity established: `false`.",
        f"- Included repos: `{', '.join(payload['included_repos'])}`.",
        f"- Included tasks: `{payload['included_task_count']}`.",
        f"- Included rows: `{payload['included_row_count']}`.",
        "",
        "## Included Task IDs",
        "",
    ]
    lines.extend(f"- `{task_id}`" for task_id in payload["included_task_ids"])
    return "\n".join(lines)


def metrics_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Retrospective Validation Metrics",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Evidence level: `{payload['evidence_level']}`.",
        "- Clean future holdout: `false`.",
        "- Predictive validity established: `false`.",
        f"- Pooled MAE: `{payload['pooled_mae']}`.",
        f"- Scoreable cells: `{payload['scoreable_cell_count']}`.",
        f"- Policy violations: `{payload['policy_violation_count']}`.",
        "",
        "| Repo | Adapter | B_real pass rate | W_real pass rate | Absolute error |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for repo_id, adapter_metrics in payload["repo_adapter_errors"].items():
        for adapter_id, metrics in adapter_metrics.items():
            lines.append(
                f"| `{repo_id}` | `{adapter_id}` | {metrics['B_real']['pass_rate']} | "
                f"{metrics['W_real']['pass_rate']} | {metrics['absolute_error']} |"
            )
    if payload["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- `{warning}`" for warning in payload["warnings"])
    return "\n".join(lines)


def load_release_splits(path: Path) -> dict[str, str]:
    release = read_json(path)
    mapping = {}
    for split, task_ids in release.get("splits", {}).items():
        for task_id in task_ids:
            mapping[str(task_id)] = split
    return mapping


def load_outcome_seen_task_ids(config: dict[str, Any]) -> set[str]:
    scorecard = read_json(artifact_path(config, "workspace_scorecard"))
    return {str(cell["task_id"]) for cell in scorecard.get("cells", []) if cell.get("task_id")}


def file_risk(changed_files: list[str]) -> tuple[bool, bool]:
    code_files = [path for path in changed_files if path.startswith("boltons/") and path.endswith(".py")]
    test_files = [path for path in changed_files if path.startswith("tests/")]
    project_or_docs = [
        path
        for path in changed_files
        if path.startswith("docs/") or path.startswith(".github/") or path in {".travis.yml", "appveyor.yml", "tox.ini"}
    ]
    project_or_docs_only = bool(project_or_docs) and not code_files
    project_heavy = len(project_or_docs) >= 3
    return project_or_docs_only, project_heavy


def source_context_status(row: dict[str, Any]) -> str:
    refs = [str(ref) for ref in row.get("allowed_context_refs", [])]
    if row.get("statement_review_status") != "reviewed":
        return "not_reviewed"
    if any(ref.startswith(("issue:", "pr:", "manual:", "customer:")) for ref in refs):
        return "non_leaky_problem_context"
    if any(ref.startswith("commit:") for ref in refs):
        return "commit_message_only"
    return "missing"


def review_candidate(
    row: dict[str, Any],
    *,
    split: str,
    hardened_status: str,
    outcome_seen: bool,
) -> dict[str, Any]:
    gates = row.get("gates", {})
    changed_files = [str(path) for path in row.get("changed_files", [])]
    project_or_docs_only, project_heavy = file_risk(changed_files)
    source_status = source_context_status(row)
    oracle_alignment = "aligned" if all(gates.get(gate) == "pass" for gate in ["oracle_extractable", "no_op_fail", "reference_pass", "known_bad_fail", "flakiness_check"]) else "rejected"
    solution_exposure = "none_detected" if gates.get("solution_leakage_review") == "pass" else "solution_exposure_risk"
    blockers = []
    if outcome_seen:
        blockers.append("previous_acut_outcome_seen")
    if source_status != "non_leaky_problem_context":
        blockers.append(source_status)
    if oracle_alignment != "aligned":
        blockers.append("oracle_alignment_rejected")
    if solution_exposure != "none_detected":
        blockers.append("solution_exposure_risk")
    if project_or_docs_only:
        blockers.append("project_or_docs_only_work")
    if hardened_status not in {"manual_review_required", "benchmark_grade_candidate"}:
        blockers.append(f"hardened_status:{hardened_status}")

    decision = "promote_to_clean_benchmark_candidate"
    if blockers:
        decision = "reject_for_clean_holdout"
    elif project_heavy or "docs_or_config_change_present" in row.get("manual_review_reasons", []):
        if str(row.get("subject", "")).lower().startswith("tox gh action"):
            decision = "keep_manual_review_required"
            blockers.append("scope_context_project_heavy_or_ambiguous")
    return {
        "task_id": row["task_id"],
        "split": split,
        "module_or_package": row.get("module_or_package", []),
        "task_time": row.get("task_time"),
        "current_hardened_status": hardened_status,
        "manual_review_reasons": row.get("manual_review_reasons", []),
        "outcome_seen": outcome_seen,
        "source_context_status": source_status,
        "oracle_alignment_status": oracle_alignment,
        "solution_exposure_risk": solution_exposure,
        "project_or_docs_only_risk": project_or_docs_only,
        "project_or_config_heavy_risk": project_heavy,
        "promotion_decision": decision,
        "promotion_blockers": blockers,
    }


def build_clean_supply_review(config: dict[str, Any]) -> dict[str, Any]:
    candidate_ids = [str(task_id) for task_id in config["clean_supply_track"]["candidate_task_ids"]]
    certified_rows = {str(row["task_id"]): row for row in read_jsonl(artifact_path(config, "boltons_certified_tasks"))}
    split_map = load_release_splits(artifact_path(config, "boltons_release"))
    overlay = read_json(artifact_path(config, "hardening_overlay"))
    hardened = {str(row["task_id"]): str(row.get("hardened_status")) for row in overlay.get("tasks", [])}
    outcome_seen = load_outcome_seen_task_ids(config)
    reviews = []
    for task_id in candidate_ids:
        row = certified_rows[task_id]
        reviews.append(
            review_candidate(
                row,
                split=split_map.get(task_id, "unknown"),
                hardened_status=hardened.get(task_id, "unknown"),
                outcome_seen=task_id in outcome_seen,
            )
        )
    promoted = [item for item in reviews if item["promotion_decision"] == "promote_to_clean_benchmark_candidate"]
    promoted_by_split = {
        split: [item["task_id"] for item in promoted if item["split"] == split]
        for split in ["B_real", "W_real"]
    }
    minimum = config["clean_supply_track"]["minimum_clean_split"]
    ready = (
        len(promoted_by_split["B_real"]) >= int(minimum["b_eval_tasks"])
        and len(promoted_by_split["W_real"]) >= int(minimum["h_future_tasks"])
    )
    return {
        "schema_version": "barcarolle.phase1.clean_supply_extension_review.v1",
        "generated_at": now_utc(),
        "candidate_source": config["clean_supply_track"]["candidate_source"],
        "candidate_task_ids": candidate_ids,
        "reviews": reviews,
        "promoted_task_ids": [item["task_id"] for item in promoted],
        "promoted_by_split": promoted_by_split,
        "clean_supply_extension_ready": ready,
        "minimum_clean_split": minimum,
        "predictive_validity_established": False,
    }


def clean_supply_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Clean Supply Extension Review",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Clean supply extension ready: `{str(payload['clean_supply_extension_ready']).lower()}`.",
        f"- Promoted task ids: `{', '.join(payload['promoted_task_ids']) if payload['promoted_task_ids'] else 'none'}`.",
        "- Predictive validity established: `false`.",
        "",
        "| Task | Split | Outcome seen | Decision | Blockers |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in payload["reviews"]:
        blockers = ", ".join(item["promotion_blockers"]) if item["promotion_blockers"] else ""
        lines.append(
            f"| `{item['task_id']}` | `{item['split']}` | `{str(item['outcome_seen']).lower()}` | "
            f"`{item['promotion_decision']}` | {blockers} |"
        )
    return "\n".join(lines)


def build_decision(config: dict[str, Any]) -> dict[str, Any]:
    metrics = read_json(ROOT / "results" / "phase1_retrospective_validation_metrics.json")
    review = read_json(ROOT / "results" / "phase1_clean_supply_extension_review.json")
    cost = read_json(artifact_path(config, "cost_reconciliation")).get("totals", {})
    clean_ready = bool(review["clean_supply_extension_ready"])
    label = (
        "retrospective_validation_complete_clean_supply_ready"
        if clean_ready
        else "retrospective_validation_complete_clean_supply_still_blocked"
    )
    next_runbook = (
        "run_preregistered_clean_future_holdout_paid_validation"
        if clean_ready
        else "mine_additional_clean_outcome_unseen_supply"
    )
    return {
        "schema_version": "barcarolle.phase1.retrospective_validation_decision.v1",
        "generated_at": now_utc(),
        "primary_decision_label": label,
        "retrospective_evidence_level": "outcome_seen_retrospective_locked",
        "included_retrospective_repos": metrics["included_repos"],
        "included_retrospective_task_ids": metrics["included_task_ids"],
        "retrospective_b_to_w_error_metrics": {
            "pooled_mae": metrics["pooled_mae"],
            "repo_adapter_errors": metrics["repo_adapter_errors"],
            "warnings": metrics["warnings"],
        },
        "clean_supply_promoted_task_ids": review["promoted_task_ids"],
        "clean_supply_promoted_by_split": review["promoted_by_split"],
        "clean_supply_extension_ready": clean_ready,
        "optional_paid_clean_validation_ran": False,
        "scoreable_cells": None,
        "policy_violation_count": metrics["policy_violation_count"],
        "cost_summary": cost,
        "predictive_validity_established": False,
        "production_ranking_status": "not_produced",
        "recommended_next_runbook": next_runbook,
        "allowed_claims": [
            "retrospective_locked_validation_complete",
            "outcome_seen_retrospective_estimator_sanity_check",
            "same_endpoint_model_different_cli_harnesses",
            "existing_scorecard_baseline_comparison",
            "strict_clean_future_holdout_still_blocked",
            "insufficient_evidence_for_predictive_validation",
            "observed_or_conservative_cost_accounting",
        ],
        "disallowed_claims": [
            "predictive_validity_established",
            "clean_future_holdout_validity_from_outcome_seen_tasks",
            "production_benchmark_ranking",
            "pure_harness_effect",
            "contamination_proof_evaluation_if_model_snapshot_unknown",
            "validation_grade_humanize_if_commit_fallback_only",
        ],
    }


def decision_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Retrospective Validation Decision",
        "",
        f"Primary decision: `{payload['primary_decision_label']}`.",
        "",
        f"- Retrospective evidence level: `{payload['retrospective_evidence_level']}`.",
        f"- Included repos: `{', '.join(payload['included_retrospective_repos'])}`.",
        f"- Retrospective pooled MAE: `{payload['retrospective_b_to_w_error_metrics']['pooled_mae']}`.",
        f"- Clean supply ready: `{str(payload['clean_supply_extension_ready']).lower()}`.",
        f"- Promoted clean task ids: `{', '.join(payload['clean_supply_promoted_task_ids']) if payload['clean_supply_promoted_task_ids'] else 'none'}`.",
        f"- Optional paid clean validation ran: `{str(payload['optional_paid_clean_validation_ran']).lower()}`.",
        f"- Predictive validity established: `{str(payload['predictive_validity_established']).lower()}`.",
        f"- Recommended next runbook: `{payload['recommended_next_runbook']}`.",
    ]
    return "\n".join(lines)


def run_plan(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    payload = build_plan(config)
    write_json(ROOT / "results" / "phase1_retrospective_validation_plan.json", payload)
    write_text(ROOT / "reports" / "phase1_retrospective_validation_plan.md", plan_report(payload))
    return payload


def run_score(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    plan_path = ROOT / "results" / "phase1_retrospective_validation_plan.json"
    plan = read_json(plan_path) if plan_path.exists() else build_plan(config)
    rows = load_primary_rows(config)
    cost = read_json(artifact_path(config, "cost_reconciliation")).get("totals", {})
    payload = metrics_payload(plan, rows, cost)
    write_json(ROOT / "results" / "phase1_retrospective_validation_metrics.json", payload)
    write_text(ROOT / "reports" / "phase1_retrospective_validation_metrics.md", metrics_report(payload))
    return payload


def run_review_clean_supply(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    payload = build_clean_supply_review(config)
    write_json(ROOT / "results" / "phase1_clean_supply_extension_review.json", payload)
    write_text(ROOT / "reports" / "phase1_clean_supply_extension_review.md", clean_supply_report(payload))
    return payload


def run_decide(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    payload = build_decision(config)
    write_json(ROOT / "results" / "phase1_retrospective_validation_decision.json", payload)
    write_text(ROOT / "reports" / "phase1_retrospective_validation_decision.md", decision_report(payload))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1 retrospective validation and clean-supply helper.")
    parser.add_argument("command", choices=["plan", "score", "review-clean-supply", "decide"])
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()
    runners = {
        "plan": run_plan,
        "score": run_score,
        "review-clean-supply": run_review_clean_supply,
        "decide": run_decide,
    }
    payload = runners[args.command](args)
    print(json.dumps({"status": payload.get("primary_decision_label") or "ok"}, sort_keys=True))


if __name__ == "__main__":
    main()
