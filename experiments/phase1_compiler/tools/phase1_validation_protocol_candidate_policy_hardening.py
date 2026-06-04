from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "phase1_validation_protocol_candidate_policy_hardening.yaml"
SCHEMA_VERSION = "barcarolle.phase1_validation_protocol_candidate_policy_hardening.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_validation_protocol_candidate_policy_hardening_output.v1"

PROHIBITED_CLAIM_PATTERNS = [
    "proves predictive validity",
    "established predictive validity",
    "authorizes paid",
    "paid validation authorized",
    "validated predictive benchmark compiler",
    "model-only superiority",
]


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


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(repo_path(path))
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected validation protocol hardening config schema_version")
    config["_path"] = str(repo_path(path))
    return config


def input_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["inputs"][key])


def optional_input_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["optional_inputs"][key])


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


def doc_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["docs"][key])


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


def digest_file(path: str | Path) -> str | None:
    resolved = repo_path(path)
    if not resolved.exists():
        return None
    return "sha256:" + hashlib.sha256(resolved.read_bytes()).hexdigest()


def command_result(args: list[str], *, timeout: int = 120) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return {"args": args, "returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {"args": args, "returncode": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
    return {"args": args, "returncode": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}


def command_stdout(args: list[str], *, timeout: int = 120) -> str:
    result = command_result(args, timeout=timeout)
    return result["stdout"] if result["returncode"] == 0 else result["stderr"]


def git_tracked(path: str | Path) -> bool:
    result = command_result(["git", "ls-files", "--error-unmatch", rel(path)])
    return result["returncode"] == 0


def round_float(value: float | int | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    if not rows:
        return ["_None._"]
    lines = [
        "| " + " | ".join(label for _, label in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(markdown_value(row.get(key, "")) for key, _ in columns) + " |")
    return lines


def markdown_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return "`" + json.dumps(value, sort_keys=True) + "`"
    return str(value)


def boundary_flags(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "new_paid_acut_cells_run": False,
        "new_paid_llm_calls_run": False,
        "external_reviewer_calls_run": False,
        "public_citation_browsing_run": False,
        "paid_calls_allowed_by_config": bool(config.get("paid_calls_allowed")),
        "external_review_allowed_by_config": bool(config.get("external_review_allowed")),
        "public_citation_browsing_allowed_by_config": bool(config.get("public_citation_browsing_allowed")),
        "score_tables_changed": False,
        "selected_task_ids_or_split_labels_changed": False,
        "predictive_validity_state": "not_established",
        "paid_validation_authorization": False,
    }


def artifact_availability(paths: dict[str, Any]) -> dict[str, dict[str, Any]]:
    availability: dict[str, dict[str, Any]] = {}
    for key, raw_path in sorted(paths.items()):
        resolved = repo_path(raw_path)
        availability[key] = {
            "path": rel(resolved),
            "exists": resolved.exists(),
            "tracked": git_tracked(resolved) if resolved.exists() else False,
            "size_bytes": resolved.stat().st_size if resolved.exists() else None,
            "digest": digest_file(resolved),
        }
    return availability


def load_m3_decision(config: dict[str, Any]) -> dict[str, Any]:
    decision = read_json(input_path(config, "m3_decision"))
    if decision.get("decision_label") != "proposal_evidence_package_complete":
        raise ValueError("M3 decision label is not proposal_evidence_package_complete")
    return decision


def m3_snapshot(config: dict[str, Any]) -> dict[str, Any]:
    decision = load_m3_decision(config)
    envelope = read_json(input_path(config, "m3_baseline_envelope"))
    fallback = read_json(input_path(config, "m3_fallback_share"))
    random_distribution = read_json(input_path(config, "m3_random_baseline_distribution"))
    overall = next(row for row in envelope["rows"] if row["group_type"] == "overall")
    random_overall = next(row for row in random_distribution["group_distributions"] if row["group_type"] == "overall")
    adapter_rows = [row for row in envelope["rows"] if row["group_type"] == "adapter"]
    repo_rows = [row for row in envelope["rows"] if row["group_type"] == "repo"]
    window_rows = [row for row in envelope["rows"] if row["group_type"] == "window"]
    return {
        "m3_decision_label": decision["decision_label"],
        "candidate_policy_object": decision["overall_candidate_vs_best_baseline"]["candidate_policy_object"]
        if "candidate_policy_object" in decision["overall_candidate_vs_best_baseline"]
        else config["settings"]["candidate_policy_id"],
        "overall_candidate_mae": overall["candidate"]["MAE"],
        "overall_best_baseline_id": overall["best_baseline"]["baseline_id"],
        "overall_best_baseline_mae": overall["best_baseline"]["MAE"],
        "overall_delta_vs_best_baseline_mae": overall["candidate_delta_vs_best_baseline_MAE"],
        "overall_candidate_catastrophic_miss_rate": overall["candidate"]["catastrophic_miss_rate"],
        "overall_best_baseline_catastrophic_miss_rate": overall["best_baseline"]["catastrophic_miss_rate"],
        "random_seed_count": random_distribution["seed_count"],
        "random_candidate_beats_or_ties_share_percent": random_overall["candidate_MAE_percentile"]["beats_random_share"],
        "fallback_share_overall": fallback["fallback_share_overall"],
        "fallback_share_by_repo": fallback["fallback_share_by_repo"],
        "fallback_selected_count_by_repo": fallback["fallback_selected_count_by_repo"],
        "adapter_rows": adapter_rows,
        "repo_rows": repo_rows,
        "window_rows": window_rows,
    }


def write_process_report(
    config: dict[str, Any],
    current_step: str,
    completed: list[str],
    notes: list[str] | None = None,
) -> None:
    lines = [
        "# Phase 1 Validation Protocol Candidate Policy Hardening Process",
        "",
        f"Current step: `{current_step}`.",
        "",
        "Completed artifacts:",
    ]
    lines.extend([f"- `{item}`" for item in completed] or ["- None yet."])
    lines.extend(
        [
            "",
            "Boundary:",
            "",
            "- New paid ACUT solver cells run: `false`.",
            "- New paid LLM calls run: `false`.",
            "- External reviewer calls run: `false`.",
            "- Public citation browsing run: `false`.",
            "- Score tables, selected task IDs, and split labels changed: `false`.",
            "- Predictive-validity state: `not_established`.",
            "- Paid-validation authorization: `false`.",
            "- Later M5 or M6 runbook drafted: `false`.",
        ]
    )
    if notes:
        lines.extend(["", "Notes:"])
        lines.extend(f"- {note}" for note in notes)
    write_text(report_path(config, "process"), "\n".join(lines))


def build_preflight(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    m3_decision = load_m3_decision(config)
    required = artifact_availability(config["inputs"])
    optional = artifact_availability(config.get("optional_inputs", {}))
    diff_check = command_result(["git", "diff", "--check"])
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "preflight",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "branch": command_stdout(["git", "branch", "--show-current"]),
        "head": command_stdout(["git", "rev-parse", "HEAD"]),
        "worktree_status_short_untracked_all": [
            line for line in command_stdout(["git", "status", "--short", "--untracked-files=all"]).splitlines() if line.strip()
        ],
        "git_diff_check": {"returncode": diff_check["returncode"], "stdout": diff_check["stdout"], "stderr": diff_check["stderr"]},
        "m3_stop_label": m3_decision["decision_label"],
        "m3_stop_label_confirmed": m3_decision["decision_label"] == "proposal_evidence_package_complete",
        "boundary": boundary_flags(config),
        "required_input_availability": required,
        "optional_planning_input_availability": optional,
        "missing_required_inputs": [item["path"] for item in required.values() if not item["exists"]],
        "artifact_plan": {
            "add_tooling": True,
            "reason": "M4 has many structured JSON and Markdown outputs; a narrow deterministic renderer reduces drift between reports and closeout JSON.",
            "tool_scope": [
                "load existing M2/M3 JSON artifacts",
                "render structured M4 JSON and Markdown",
                "check required decisions exist",
                "check prohibited current-claim phrases are absent from generated Markdown",
            ],
        },
        "permission_lock": {
            "paid_acut_cells": False,
            "paid_llm_calls": False,
            "external_reviewer_calls": False,
            "public_citation_browsing": False,
            "score_table_edits": False,
            "selected_task_edits": False,
            "split_label_edits": False,
        },
    }
    if payload["missing_required_inputs"]:
        raise FileNotFoundError(f"missing required inputs: {payload['missing_required_inputs']}")
    write_json(output_path(config, "preflight"), payload)
    write_process_report(
        config,
        "Step 0 - Preflight And Scope Lock",
        [rel(output_path(config, "preflight")), rel(report_path(config, "process"))],
        [
            "M3 stop label is proposal_evidence_package_complete.",
            "A narrow renderer will be used for auditability; it is limited to existing artifacts and explicit protocol decisions.",
        ],
    )
    return payload


def build_claim_modes(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    snapshot = m3_snapshot(config)
    modes = [
        {
            "mode": "true_future_holdout",
            "claim_allowed": "Predictive-validity evidence for the named scope only if every frozen gate passes.",
            "claim_not_allowed": "Cannot generalize beyond named repos, adapters, task supply, source reservoirs, and release schema.",
            "must_freeze_before_outcomes": [
                "target repos",
                "future cutoff",
                "task supply and certification rules",
                "feature extraction",
                "source-quality overlays",
                "candidate policy",
                "baselines and random seeds",
                "adapter estimand",
                "invalid-cell rules",
                "support thresholds",
                "joint success gate",
            ],
            "freeze_artifact": "benchmark release manifest plus protocol freeze JSON committed before future outcomes are collected or joined",
            "paid_discussion_after_m4": "not by M4 alone; requires later user decision and budget boundary",
        },
        {
            "mode": "preregistered_rolling_origin",
            "claim_allowed": "Predictive-validity evidence for preregistered cutoffs only when candidate, baselines, seeds, estimand, invalid-cell handling, support thresholds, and gate are frozen before outcomes are joined.",
            "claim_not_allowed": "Cannot use cutoffs chosen after seeing joined outcomes; cannot hide failed cutoffs in a pooled-only summary.",
            "must_freeze_before_outcomes": [
                "rolling-origin cutoffs",
                "candidate policy",
                "baseline registry",
                "seeds",
                "adapter estimand",
                "invalid and non-scoreable rules",
                "success gate",
                "support thresholds",
            ],
            "freeze_artifact": "rolling-origin preregistration manifest with outcome-blind digest and seed list",
            "paid_discussion_after_m4": "not by M4 alone; M4 only defines what the future preregistration must contain",
        },
        {
            "mode": "pseudo_future_replay",
            "claim_allowed": "Traction, debugging, and protocol stress-testing.",
            "claim_not_allowed": "Cannot carry the north-star validity claim because outcomes or outcome-derived design choices may already be visible.",
            "must_freeze_before_outcomes": [
                "replay selection manifest",
                "joined-score provenance",
                "known-outcome caveat",
            ],
            "freeze_artifact": "retrospective replay manifest and traction-only report",
            "paid_discussion_after_m4": "no; replay can motivate no-paid hardening only",
        },
        {
            "mode": "current_m3_retrospective_evidence",
            "claim_allowed": "Proposal traction: candidate MAE was 0.209 versus 0.2149 for the best simple aggregate baseline, with visible limitations.",
            "claim_not_allowed": "Cannot be treated as current predictive-validity evidence or as a paid-readiness result.",
            "must_freeze_before_outcomes": [
                "already frozen candidate policy",
                "retrospective score-join manifest",
                "M3 evidence package",
            ],
            "freeze_artifact": "phase1_proposal_evidence_package_decision.json and M3 supporting reports",
            "paid_discussion_after_m4": "no; M3 remains traction-only under this hardening package",
        },
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "claim_modes",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "north_star": "future target-repo ACUT performance predicted by a repo-specific benchmark release",
        "m3_interpretation": {
            "mode": "current_m3_retrospective_evidence",
            "label": "traction_only",
            "candidate_mae": snapshot["overall_candidate_mae"],
            "best_simple_baseline_id": snapshot["overall_best_baseline_id"],
            "best_simple_baseline_mae": snapshot["overall_best_baseline_mae"],
            "delta": snapshot["overall_delta_vs_best_baseline_mae"],
        },
        "study_modes": modes,
        "boundary": boundary_flags(config),
    }
    write_json(output_path(config, "claim_modes"), payload)
    write_claim_modes_report(config, payload)
    write_process_report(
        config,
        "Step 1 - Study Modes And Claim Boundary",
        [rel(output_path(config, "claim_modes")), rel(report_path(config, "claim_modes"))],
        ["Pseudo-future replay and current M3 evidence are restricted to traction and debugging."],
    )
    return payload


def write_claim_modes_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = [
        {
            "mode": mode["mode"],
            "claim_allowed": mode["claim_allowed"],
            "claim_not_allowed": mode["claim_not_allowed"],
            "freeze_artifact": mode["freeze_artifact"],
        }
        for mode in payload["study_modes"]
    ]
    lines = [
        "# Validation Protocol Claim Modes",
        "",
        "What happened: M4 separates future validation modes from retrospective replay.",
        "",
        "Why it matters: the same numeric table can support different claims depending on when the policy, baselines, seeds, and outcomes were frozen.",
        "",
        *markdown_table(rows, [("mode", "Mode"), ("claim_allowed", "Can claim"), ("claim_not_allowed", "Cannot claim"), ("freeze_artifact", "Freeze artifact")]),
        "",
        "M3 interpretation:",
        f"- Label: `{payload['m3_interpretation']['label']}`.",
        f"- Candidate MAE: `{payload['m3_interpretation']['candidate_mae']}`.",
        f"- Best simple baseline: `{payload['m3_interpretation']['best_simple_baseline_id']}` at MAE `{payload['m3_interpretation']['best_simple_baseline_mae']}`.",
        f"- Delta: `{payload['m3_interpretation']['delta']}`.",
        "",
        "Boundary:",
        "- Pseudo-future replay supports traction and debugging only.",
        "- The north-star claim remains future work.",
        "- Paid-validation authorization remains `false`.",
    ]
    assert_no_prohibited_claims(lines)
    write_text(report_path(config, "claim_modes"), "\n".join(lines))


def build_candidate_policy(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    policy_spec = read_json(input_path(config, "policy_spec"))
    fallback = read_json(input_path(config, "m3_fallback_share"))
    source = read_json(input_path(config, "m3_source_supply_status"))
    settings = config["settings"]
    per_repo_cap = float(settings["fallback_share_max_per_repo"])
    overall_cap = float(settings["fallback_share_max_overall"])
    current_passes = (
        float(fallback["fallback_share_overall"]) <= overall_cap
        and all(float(value) <= per_repo_cap for value in fallback["fallback_share_by_repo"].values())
    )
    pseudocode = [
        "Input: certified candidate task rows for each target repo plus allowed solver-visible feature fields.",
        "Reject rows missing release eligibility, source-quality status, statement digest, or leakage-risk status.",
        "For each repo, derive supported feature dimensions from the frozen policy feature list and source-quality overlays.",
        "If repo has at least budget_per_repo eligible tasks and enough supported feature coverage, select budget_per_repo tasks that maximize unweighted coarse feature coverage.",
        "Score candidate sets without task-level outcome weights; each selected task contributes equally within its repo budget.",
        "Break ties by sha256(seed, repo, task_id, feature_vector) with the frozen deterministic seed.",
        "If feature support is insufficient, route the repo to the labeled insufficient_feature_support fallback.",
        "If eligible budget is insufficient, route the repo to the labeled insufficient_budget fallback.",
        "Mark every selected fallback slot with fallback_selected, fallback_design, fallback_reason, and source-quality overlay status.",
        "Write selected and excluded task IDs with reasons; do not change IDs after any score or future outcome is visible.",
    ]
    governance = {
        "fallback_threshold_rule": {
            "overall_max_share": overall_cap,
            "per_repo_max_share": per_repo_cap,
            "per_feature_rule": "No primary coverage-policy claim may rely on a feature dimension where all selected slots for a repo came from fallback.",
            "threshold_basis": "A six-task per-repo budget can tolerate at most one fallback slot in a repo and at most about one to two slots overall; larger fallback share changes the candidate object.",
        },
        "include_exclude_reporting_rule": "Always report all repos and a sensitivity excluding repos whose per-repo fallback share exceeds the cap. If any repo is excluded, the primary claim is narrowed to support-qualified repos.",
        "repair_or_narrowing_rule": "Repair feature support and rerun the frozen policy before future outcomes are joined, or narrow the claim to the composite selector with fallback-repo sensitivity.",
        "current_m3_candidate_passes_fallback_rule": current_passes,
        "current_m3_classification": "not_paid_ready_for_primary_coverage_policy_claim" if not current_passes else "fallback_rule_passes",
        "boltons_treatment": "claim_changing_because_fallback_share_is_6_of_6",
        "fallback_repos_only_diagnostic": "boltons/fallback-repo diagnostic is worse than temporal by MAE 0.0139 in M3",
    }
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "candidate_policy",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "policy_id": settings["candidate_policy_id"],
        "base_policy_id": settings["candidate_policy_manifest_id"],
        "allowed_inputs": policy_spec["allowed_inputs"],
        "forbidden_outcome_inputs": policy_spec["forbidden_inputs"],
        "budget_per_repo": int(settings["budget_per_repo"]),
        "coverage_features": policy_spec["coverage_features"],
        "tie_break_rule": policy_spec["seed_policy"],
        "supported_feature_check": {
            "minimum_budget_multiple": int(settings["future_min_candidate_pool_multiple"]),
            "check": "feature dimensions with insufficient distinct eligible values or missing overlays are unsupported for the primary coverage objective",
        },
        "fallback_routes": policy_spec["fallback_rules"],
        "source_quality_overlays": {
            "use_repaired_click_overlay": True,
            "source_repo_rows": source["repo_rows"],
            "rule": "source-quality failures block primary release inclusion; repaired overlays must carry provenance and digest fields",
        },
        "pseudocode": pseudocode,
        "policy_violations": [
            "using forbidden outcome, terminal-status, score, hidden-verifier, transcript, or pass-rate fields",
            "changing selected task IDs, split labels, feature values, thresholds, seeds, or fallback labels after outcomes are visible",
            "using an unlabeled fallback slot",
            "omitting source-quality or leakage-risk overlays",
            "claiming a coverage-policy result when fallback caps fail",
        ],
        "fallback_governance": governance,
        "current_m3_fallback": {
            "overall_share": fallback["fallback_share_overall"],
            "share_by_repo": fallback["fallback_share_by_repo"],
            "selected_count_by_repo": fallback["fallback_selected_count_by_repo"],
        },
        "selected_task_ids_changed": False,
        "boundary": boundary_flags(config),
    }
    write_json(output_path(config, "candidate_policy"), payload)
    write_candidate_policy_report(config, payload)
    write_process_report(
        config,
        "Step 2 - Candidate Policy And Fallback Governance",
        [rel(output_path(config, "candidate_policy")), rel(report_path(config, "candidate_policy"))],
        ["The current M3 selector fails the hardened fallback rule because boltons has fallback share 6/6."],
    )
    return payload


def write_candidate_policy_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    fallback_rows = [
        {"scope": "overall", "share": payload["current_m3_fallback"]["overall_share"], "cap": payload["fallback_governance"]["fallback_threshold_rule"]["overall_max_share"]},
        *[
            {"scope": f"repo:{repo}", "share": share, "cap": payload["fallback_governance"]["fallback_threshold_rule"]["per_repo_max_share"]}
            for repo, share in payload["current_m3_fallback"]["share_by_repo"].items()
        ],
    ]
    lines = [
        "# Candidate Policy And Fallback Governance",
        "",
        f"Policy object: `{payload['policy_id']}`.",
        "",
        "Pseudocode:",
        "",
        "```text",
        *payload["pseudocode"],
        "```",
        "",
        "Fallback thresholds:",
        "",
        *markdown_table(fallback_rows, [("scope", "Scope"), ("share", "M3 share"), ("cap", "Hard cap")]),
        "",
        f"Current M3 fallback classification: `{payload['fallback_governance']['current_m3_classification']}`.",
        "",
        "Governance:",
        f"- Include/exclude rule: {payload['fallback_governance']['include_exclude_reporting_rule']}",
        f"- Repair or narrowing rule: {payload['fallback_governance']['repair_or_narrowing_rule']}",
        f"- Boltons treatment: `{payload['fallback_governance']['boltons_treatment']}`.",
        f"- Diagnostic: {payload['fallback_governance']['fallback_repos_only_diagnostic']}.",
        "",
        "Policy violations:",
    ]
    lines.extend(f"- {item}" for item in payload["policy_violations"])
    lines.extend(
        [
            "",
            "Boundary:",
            "- Selected task IDs and split labels changed: `false`.",
            "- Paid-validation authorization remains `false`.",
        ]
    )
    assert_no_prohibited_claims(lines)
    write_text(report_path(config, "candidate_policy"), "\n".join(lines))


def build_baseline_registry(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    registry = [
        {
            "baseline_id": "temporal_recent_baseline",
            "purpose": "Strong recency comparator for future target-repo work.",
            "allowed_inputs": ["repo", "task_time", "eligibility", "budget_per_repo", "frozen_tie_break_value"],
            "forbidden_inputs": ["pass_rate", "terminal_status", "future outcome", "adapter score"],
            "budget_matching_rule": "same per-repo task budget as the candidate",
            "seed_or_tie_break_rule": "deterministic most-recent ordering, then frozen sha256 task-id tie break",
            "reporting_metric": "MAE and catastrophic miss rate by adapter first, then repo/window diagnostics",
            "required_slice_reporting": ["adapter", "repo", "window", "overall secondary"],
            "failure_modes": ["recency dominates source diversity", "ties chosen after seeing scores", "insufficient future tasks"],
        },
        {
            "baseline_id": "repo_unweighted_same_budget",
            "purpose": "Tests whether fixed per-repo budget alone explains performance.",
            "allowed_inputs": ["repo", "eligible task IDs", "budget_per_repo", "frozen tie break"],
            "forbidden_inputs": ["outcomes", "score rows", "hidden verifier outputs"],
            "budget_matching_rule": "exact same per-repo count as the candidate",
            "seed_or_tie_break_rule": "frozen deterministic sha256 order",
            "reporting_metric": "same as candidate",
            "required_slice_reporting": ["adapter", "repo", "window"],
            "failure_modes": ["candidate pool too small", "source-quality filters not matched"],
        },
        {
            "baseline_id": "repo_stratified_by_target_profile",
            "purpose": "Conservative simple stratified comparator and fallback reference.",
            "allowed_inputs": ["repo", "task target profile features", "eligibility", "budget_per_repo", "frozen tie break"],
            "forbidden_inputs": ["future outcomes", "adapter terminal status", "score-derived weights"],
            "budget_matching_rule": "same repo budget and same eligibility filters",
            "seed_or_tie_break_rule": "deterministic profile ordering, then frozen sha256 tie break",
            "reporting_metric": "same as candidate",
            "required_slice_reporting": ["adapter", "repo", "window", "fallback sensitivity"],
            "failure_modes": ["underidentified target profile", "strata with sparse support", "fallback overuse"],
        },
        {
            "baseline_id": "many_seed_random_same_budget",
            "purpose": "Distributional same-budget random check; avoids overreading a small seed sample.",
            "allowed_inputs": ["repo", "eligible task IDs", "budget_per_repo", "declared seed range"],
            "forbidden_inputs": ["outcomes", "score rows", "post-hoc seed choice"],
            "budget_matching_rule": "same per-repo budget for each random seed",
            "seed_or_tie_break_rule": "at least 1000 seeds frozen before outcomes are joined",
            "reporting_metric": "candidate percentile, beats-or-ties share, MAE distribution, catastrophic-miss distribution",
            "required_slice_reporting": ["adapter", "repo", "window", "overall secondary"],
            "failure_modes": ["too few seeds", "seed range changed after outcomes", "random pool not eligibility-matched"],
        },
        {
            "baseline_id": "coverage_only_same_budget",
            "purpose": "Optional feasible no-paid comparator isolating coarse coverage without target-profile weighting.",
            "allowed_inputs": ["coverage features", "repo", "eligibility", "budget_per_repo", "frozen tie break"],
            "forbidden_inputs": ["outcomes", "adapter scores", "future score joins"],
            "budget_matching_rule": "same per-repo budget and eligibility filters",
            "seed_or_tie_break_rule": "same deterministic seed as candidate or a separately frozen seed",
            "reporting_metric": "same as candidate",
            "required_slice_reporting": ["adapter", "repo", "window"],
            "failure_modes": ["not cleanly separable from current composite selector without a frozen implementation"],
            "status": "add_when_selector_can_be_frozen_outcome_blind",
        },
        {
            "baseline_id": "stricter_temporal_recent_same_eligibility",
            "purpose": "Optional stricter temporal variant with exactly matched eligibility and frozen tie-breaks.",
            "allowed_inputs": ["repo", "task_time", "same eligibility filters", "budget_per_repo"],
            "forbidden_inputs": ["outcomes", "score-derived exclusions"],
            "budget_matching_rule": "same per-repo budget, same eligibility, same source-quality overlays",
            "seed_or_tie_break_rule": "timestamp order, then frozen sha256 tie break",
            "reporting_metric": "same as candidate",
            "required_slice_reporting": ["adapter", "repo", "window"],
            "failure_modes": ["future history too sparse", "eligibility filter drift"],
            "status": "recommended_for_future_protocol_if_supply_supports_it",
        },
    ]
    deferred = [
        {
            "baseline_id": "external_or_general_benchmark_comparator",
            "decision": "deferred",
            "reason": "External/general candidates are untrusted until local certification, license status, source provenance, oracle source, and release schema fields are clean.",
        }
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "baseline_registry",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "mandatory_baseline_ids": [
            "temporal_recent_baseline",
            "repo_unweighted_same_budget",
            "repo_stratified_by_target_profile",
            "many_seed_random_same_budget",
        ],
        "registry": registry,
        "deferred_comparators": deferred,
        "temporal_recent_remains_serious_comparator": True,
        "random_baseline_seed_rule": "many_seed_not_five_seed",
        "boundary": boundary_flags(config),
    }
    write_json(output_path(config, "baseline_registry"), payload)
    write_baseline_registry_report(config, payload)
    write_process_report(
        config,
        "Step 3 - Baseline Registry",
        [rel(output_path(config, "baseline_registry")), rel(report_path(config, "baseline_registry"))],
        ["Temporal recent remains a mandatory comparator; external/general benchmarks are deferred until locally certified."],
    )
    return payload


def write_baseline_registry_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = [
        {
            "baseline_id": item["baseline_id"],
            "purpose": item["purpose"],
            "budget": item["budget_matching_rule"],
            "status": item.get("status", "mandatory"),
        }
        for item in payload["registry"]
    ]
    lines = [
        "# Baseline Registry",
        "",
        "Future validation must compare the candidate against the best eligible simple baseline, not only a weak random sample.",
        "",
        *markdown_table(rows, [("baseline_id", "Baseline"), ("purpose", "Purpose"), ("budget", "Budget matching"), ("status", "Status")]),
        "",
        "Deferred comparator:",
        f"- `{payload['deferred_comparators'][0]['baseline_id']}`: {payload['deferred_comparators'][0]['reason']}",
        "",
        "Boundary:",
        "- Random baseline must be many-seed with frozen seeds.",
        "- External/general candidates are untrusted until certified locally.",
        "- Paid-validation authorization remains `false`.",
    ]
    assert_no_prohibited_claims(lines)
    write_text(report_path(config, "baseline_registry"), "\n".join(lines))


def build_adapter_estimand(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    snapshot = m3_snapshot(config)
    adapter_rows = []
    margin = float(config["settings"]["future_primary_mae_margin"])
    tolerance = float(config["settings"]["adapter_non_inferiority_tolerance_mae"])
    for row in snapshot["adapter_rows"]:
        delta = float(row["candidate_delta_vs_best_baseline_MAE"])
        adapter_rows.append(
            {
                "adapter_id": row["group_id"],
                "candidate_mae": row["candidate"]["MAE"],
                "best_baseline_id": row["best_baseline"]["baseline_id"],
                "best_baseline_mae": row["best_baseline"]["MAE"],
                "delta_vs_best_baseline": row["candidate_delta_vs_best_baseline_MAE"],
                "passes_primary_margin": delta <= -margin,
                "passes_non_inferiority_tolerance": delta <= tolerance,
            }
        )
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "adapter_estimand",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "primary_estimand": "per_named_acut_configuration",
        "primary_claim_rule": "A claim for a named adapter requires that adapter to pass the joint gate. A cross-adapter claim requires every named adapter in scope to pass.",
        "pooled_metric_rule": "An equal-mixture pooled metric may be reported only as a preregistered secondary diagnostic; it cannot rescue a named-adapter failure.",
        "if_codex_fails_kilo_passes": "Report Kilo-specific support and Codex failure; do not make an adapter-general claim.",
        "if_kilo_fails_codex_passes": "Report Codex-specific support and Kilo failure; do not make an adapter-general claim.",
        "adapter_non_inferiority_rule": {
            "tolerance_mae": tolerance,
            "meaning": "For a broad cross-adapter claim, no named adapter may be worse than its best eligible simple baseline by more than this tolerance; primary support still requires the full margin.",
        },
        "primary_m5_table": "adapter-stratified baseline envelope with candidate, best baseline, MAE delta, catastrophic miss rate, fallback status, and support status by named ACUT configuration",
        "current_m3_adapter_interpretation": adapter_rows,
        "current_m3_cross_adapter_status": "fails_because_codex_does_not_pass_and_pooled_summary_is_secondary",
        "adapter_difference_boundary": "Codex and Kilo are ACUT-configuration evidence; do not collapse differences into a model-only finding unless harness differences have been ruled out.",
        "boundary": boundary_flags(config),
    }
    write_json(output_path(config, "adapter_estimand"), payload)
    write_adapter_estimand_report(config, payload)
    write_process_report(
        config,
        "Step 4 - Adapter Estimand And Reporting Rule",
        [rel(output_path(config, "adapter_estimand")), rel(report_path(config, "adapter_estimand"))],
        ["Adapter-level reporting is primary; pooled improvement cannot rescue a named-adapter failure."],
    )
    return payload


def write_adapter_estimand_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = [
        {
            "adapter": row["adapter_id"],
            "candidate_mae": row["candidate_mae"],
            "best_baseline": row["best_baseline_id"],
            "delta": row["delta_vs_best_baseline"],
            "primary_margin": row["passes_primary_margin"],
            "noninferiority": row["passes_non_inferiority_tolerance"],
        }
        for row in payload["current_m3_adapter_interpretation"]
    ]
    lines = [
        "# Adapter Estimand And Reporting Rule",
        "",
        f"Primary estimand: `{payload['primary_estimand']}`.",
        "",
        payload["primary_claim_rule"],
        "",
        payload["pooled_metric_rule"],
        "",
        *markdown_table(rows, [("adapter", "Adapter"), ("candidate_mae", "Candidate MAE"), ("best_baseline", "Best baseline"), ("delta", "Delta"), ("primary_margin", "Passes margin"), ("noninferiority", "Passes tolerance")]),
        "",
        f"M3 cross-adapter status: `{payload['current_m3_cross_adapter_status']}`.",
        "",
        "M5 primary table:",
        f"- {payload['primary_m5_table']}.",
        "",
        "Boundary:",
        f"- {payload['adapter_difference_boundary']}",
        "- Paid-validation authorization remains `false`.",
    ]
    assert_no_prohibited_claims(lines)
    write_text(report_path(config, "adapter_estimand"), "\n".join(lines))


def build_success_gate(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    snapshot = m3_snapshot(config)
    settings = config["settings"]
    margin = float(settings["future_primary_mae_margin"])
    miss_worsening = float(settings["catastrophic_miss_max_worsening"])
    random_min = float(settings["random_baseline_min_beats_share_percent"])
    invalid_rules = {
        "invalid_cell_definition": [
            "wrong task base commit or task statement",
            "hidden oracle exposed outside verifier workspace",
            "endpoint or accounting cannot be proven for a paid cell",
            "out-of-scope path edits not allowed by task policy",
            "score row cannot be tied to a frozen task, adapter, and verifier",
        ],
        "non_scoreable_definition": [
            "solver or verifier did not produce a scoreable pass/fail cell despite valid task setup",
            "environment failure outside the task outcome when retry policy is exhausted",
            "missing terminal status after the preregistered retry window",
        ],
        "policy_violation_definition": [
            "forbidden outcome input used in candidate or baseline selection",
            "selected task IDs, split labels, seeds, fallback labels, or thresholds changed after outcome visibility",
            "unlabeled fallback or untracked source-quality overlay",
        ],
        "primary_metric_handling": "Invalid benchmark-side cells are excluded only under frozen reasons and must be counted; non-scoreable ACUT cells are excluded from pass-rate denominators in primary metrics and treated as fail in sensitivity.",
        "sensitivity_required": "Repeat primary tables with non-scoreable cells treated as fail and with invalid cells either excluded or fail-coded by preregistered reason.",
        "max_invalid_share_overall": float(settings["invalid_cell_max_share_overall"]),
        "max_non_scoreable_share_overall": float(settings["non_scoreable_max_share_overall"]),
        "max_non_scoreable_share_slice": float(settings["non_scoreable_max_share_slice"]),
        "policy_violations_allowed_for_primary_claims": 0,
    }
    catastrophic_rules = {
        "gap_threshold": float(settings["catastrophic_gap_threshold"]),
        "threshold_reason": "A 15 percentage point pass-rate gap is large enough to mark a benchmark estimate as materially misleading in the existing Phase 1 tables.",
        "candidate_must_not_worsen_rate_by_more_than": miss_worsening,
        "pass_fail_rule": "Candidate catastrophic-miss rate must be no higher than the best eligible simple baseline by more than the tolerance in every claimed adapter scope.",
    }
    adapter_pass = all(float(row["candidate_delta_vs_best_baseline_MAE"]) <= -margin for row in snapshot["adapter_rows"])
    repo_rows = snapshot["repo_rows"]
    repo_margin_pass_count = sum(1 for row in repo_rows if float(row["candidate_delta_vs_best_baseline_MAE"]) <= -margin)
    repo_worse_count = sum(1 for row in repo_rows if float(row["candidate_delta_vs_best_baseline_MAE"]) > 0)
    fallback_pass = (
        float(snapshot["fallback_share_overall"]) <= float(settings["fallback_share_max_overall"])
        and all(float(value) <= float(settings["fallback_share_max_per_repo"]) for value in snapshot["fallback_share_by_repo"].values())
    )
    gate_components = [
        {
            "component": "meaningful_mae_margin",
            "rule": f"candidate MAE must beat the best eligible simple baseline by at least {margin}",
            "m3_status": "fail",
            "m3_evidence": f"aggregate delta {snapshot['overall_delta_vs_best_baseline_mae']} is smaller than the required margin",
        },
        {
            "component": "many_seed_random_distribution",
            "rule": f"candidate must beat or tie at least {random_min}% of frozen random seeds on primary MAE",
            "m3_status": "fail",
            "m3_evidence": f"M3 beats-or-ties share is {snapshot['random_candidate_beats_or_ties_share_percent']}%",
        },
        {
            "component": "catastrophic_miss",
            "rule": catastrophic_rules["pass_fail_rule"],
            "m3_status": "pass_overall_only",
            "m3_evidence": f"overall miss rate {snapshot['overall_candidate_catastrophic_miss_rate']} vs baseline {snapshot['overall_best_baseline_catastrophic_miss_rate']}; slice checks remain fragile",
        },
        {
            "component": "adapter_estimand",
            "rule": "each claimed named adapter must pass; pooled summary is secondary",
            "m3_status": "pass" if adapter_pass else "fail",
            "m3_evidence": "Codex is worse than its best baseline while Kilo is better",
        },
        {
            "component": "repo_window_non_concentration",
            "rule": "improvements must not be concentrated in one favorable repo, adapter, or window",
            "m3_status": "fail",
            "m3_evidence": f"{repo_margin_pass_count} repos pass the margin and {repo_worse_count} repos are worse than their best baseline",
        },
        {
            "component": "fallback_governance",
            "rule": "fallback share must stay below overall and per-repo caps or the claim narrows",
            "m3_status": "pass" if fallback_pass else "fail",
            "m3_evidence": f"overall fallback share {snapshot['fallback_share_overall']}; boltons share {snapshot['fallback_share_by_repo'].get('boltons')}",
        },
        {
            "component": "invalid_non_scoreable_sensitivity",
            "rule": "sensitivity analysis must not reverse the conclusion and caps must hold",
            "m3_status": "unresolved_for_future_claim",
            "m3_evidence": "M3 reports non-scoreable counts, but the future sensitivity gate was not frozen before these retrospective outcomes",
        },
        {
            "component": "candidate_policy_compliance",
            "rule": "zero policy violations and no forbidden outcome inputs",
            "m3_status": "partial_pass",
            "m3_evidence": "outcome-blindness audit exists, but fallback governance fails for the primary coverage-policy claim",
        },
        {
            "component": "source_endpoint_accounting",
            "rule": "source-quality, endpoint, cost, latency, and artifact hygiene checks must pass",
            "m3_status": "pass_for_existing_no_paid_artifacts",
            "m3_evidence": "M3 made no paid calls and did not change score tables; future paid cells would need a fresh endpoint/accounting audit",
        },
        {
            "component": "support_thresholds",
            "rule": "minimum repos, tasks, adapters, windows, fallback, source, and invalid-cell thresholds must hold for the intended claim",
            "m3_status": "fail_for_primary_future_claim",
            "m3_evidence": "current evidence is retrospective, sparse, and fallback-composite",
        },
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "success_gate",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "gate_type": "joint_all_required",
        "invalid_non_scoreable_rules": invalid_rules,
        "catastrophic_miss_rules": catastrophic_rules,
        "joint_gate_components": gate_components,
        "current_m3_gate_result": {
            "passes_future_gate": False,
            "classification": "diagnostic_traction_candidate_not_paid_ready",
            "paid_validation_authorization": False,
            "usable_as_proposal_traction": True,
            "main_failures": [
                "aggregate MAE edge below future margin",
                "Codex adapter failure",
                "fallback caps fail because boltons is 6/6 fallback",
                "repo improvements concentrated and click/boltons are worse than temporal",
                "random beats-or-ties share below 95%",
                "current study mode is retrospective replay",
            ],
        },
        "boundary": boundary_flags(config),
    }
    write_json(output_path(config, "success_gate"), payload)
    write_success_gate_report(config, payload)
    write_process_report(
        config,
        "Steps 5-6 - Invalid Cells, Catastrophic Misses, And Joint Success Gate",
        [rel(output_path(config, "success_gate")), rel(report_path(config, "success_gate"))],
        ["Loose margin-or-majority logic is replaced by a joint all-required gate."],
    )
    return payload


def write_success_gate_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = [
        {
            "component": item["component"],
            "rule": item["rule"],
            "m3_status": item["m3_status"],
            "m3_evidence": item["m3_evidence"],
        }
        for item in payload["joint_gate_components"]
    ]
    lines = [
        "# Joint Success Gate",
        "",
        f"Gate type: `{payload['gate_type']}`.",
        "",
        *markdown_table(rows, [("component", "Component"), ("rule", "Rule"), ("m3_status", "M3 diagnostic"), ("m3_evidence", "Evidence")]),
        "",
        "Invalid/non-scoreable rules:",
        f"- Invalid max share overall: `{payload['invalid_non_scoreable_rules']['max_invalid_share_overall']}`.",
        f"- Non-scoreable max share overall: `{payload['invalid_non_scoreable_rules']['max_non_scoreable_share_overall']}`.",
        f"- Non-scoreable max share per slice: `{payload['invalid_non_scoreable_rules']['max_non_scoreable_share_slice']}`.",
        f"- Policy violations allowed for primary claims: `{payload['invalid_non_scoreable_rules']['policy_violations_allowed_for_primary_claims']}`.",
        "",
        "Catastrophic miss:",
        f"- Gap threshold: `{payload['catastrophic_miss_rules']['gap_threshold']}`.",
        f"- Worsening tolerance: `{payload['catastrophic_miss_rules']['candidate_must_not_worsen_rate_by_more_than']}`.",
        "",
        "M3 diagnostic result:",
        f"- Passes future gate: `{payload['current_m3_gate_result']['passes_future_gate']}`.",
        f"- Classification: `{payload['current_m3_gate_result']['classification']}`.",
        f"- Paid-validation authorization: `{payload['current_m3_gate_result']['paid_validation_authorization']}`.",
    ]
    assert_no_prohibited_claims(lines)
    write_text(report_path(config, "success_gate"), "\n".join(lines))


def build_support_thresholds(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    settings = config["settings"]
    thresholds = [
        {
            "threshold": "minimum_repos",
            "value": {
                "narrow_target_repo_claim": int(settings["future_min_repos_narrow_claim"]),
                "broader_method_claim": int(settings["future_min_repos_broad_claim"]),
            },
            "supports": "Narrow multi-repo validation if at least three repos pass; broader method claims need more independent repos.",
            "blocks_if_not_met": "Primary predictive-validity claim for the intended scope.",
        },
        {
            "threshold": "future_tasks_per_repo",
            "value": int(settings["future_min_tasks_per_repo"]),
            "supports": "Enough H_future support to estimate future target-repo performance beyond six selected tasks.",
            "blocks_if_not_met": "Primary claim for a repo with sparse future outcomes.",
        },
        {
            "threshold": "candidate_pool_support",
            "value": f"at least {settings['future_min_candidate_pool_multiple']}x selected budget per repo after source-quality filters",
            "supports": "Outcome-blind selection with meaningful alternatives.",
            "blocks_if_not_met": "Coverage-policy claim for that repo; route to repair or narrowing.",
        },
        {
            "threshold": "named_acut_configurations",
            "value": int(settings["future_min_named_acut_configs_cross_adapter"]),
            "supports": "Cross-adapter claim if every named configuration passes.",
            "blocks_if_not_met": "Adapter-general wording; one adapter can support only adapter-specific wording.",
        },
        {
            "threshold": "rolling_origin_cutoffs",
            "value": int(settings["future_min_rolling_cutoffs"]),
            "supports": "Rolling-origin claim with temporal replication.",
            "blocks_if_not_met": "Rolling-origin claim; true-future holdout may still proceed if separately frozen.",
        },
        {
            "threshold": "fallback_share",
            "value": {
                "overall_max": float(settings["fallback_share_max_overall"]),
                "per_repo_max": float(settings["fallback_share_max_per_repo"]),
            },
            "supports": "Primary coverage-policy claim without composite-selector caveat.",
            "blocks_if_not_met": "Primary coverage-policy wording; report composite selector or repair support.",
        },
        {
            "threshold": "invalid_non_scoreable_share",
            "value": {
                "invalid_overall_max": float(settings["invalid_cell_max_share_overall"]),
                "non_scoreable_overall_max": float(settings["non_scoreable_max_share_overall"]),
                "non_scoreable_slice_max": float(settings["non_scoreable_max_share_slice"]),
            },
            "supports": "Stable primary metrics and sensitivity analysis.",
            "blocks_if_not_met": "Primary claim unless rerun/repair is preregistered and completed.",
        },
        {
            "threshold": "independent_source_reservoirs",
            "value": int(settings["future_min_source_reservoirs_per_repo"]),
            "supports": "Source-mix claim and reduced single-reservoir overfitting risk.",
            "blocks_if_not_met": "Source-quality or source-diversity claim for affected repo.",
        },
        {
            "threshold": "source_quality_certification_fields",
            "value": "provenance digest, license status, oracle-source type, leakage check, environment status, statement digest",
            "supports": "Release auditability and hidden-oracle protection.",
            "blocks_if_not_met": "Release inclusion for the affected task.",
        },
    ]
    scenarios = [
        {
            "scenario": "minimal_three_repo_named_adapter",
            "status": "can support narrow claims only if every gate passes",
            "user_budget_decision_required": True,
        },
        {
            "scenario": "five_repo_broader_method",
            "status": "stronger but outside current M4 authorization",
            "user_budget_decision_required": True,
        },
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "support_thresholds",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "thresholds": thresholds,
        "scenario_notes": scenarios,
        "current_m3_status": {
            "blocks_primary_predictive_validity_claim": True,
            "reasons": ["retrospective replay", "fallback caps fail", "adapter/repo support is fragile"],
        },
        "boundary": boundary_flags(config),
    }
    write_json(output_path(config, "support_thresholds"), payload)
    write_support_thresholds_report(config, payload)
    write_process_report(
        config,
        "Step 7 - Quantitative Support Thresholds",
        [rel(output_path(config, "support_thresholds")), rel(report_path(config, "support_thresholds"))],
        ["Thresholds define claim support and blockers without setting a user-owned budget ceiling."],
    )
    return payload


def write_support_thresholds_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = [
        {
            "threshold": item["threshold"],
            "value": item["value"],
            "supports": item["supports"],
            "blocks": item["blocks_if_not_met"],
        }
        for item in payload["thresholds"]
    ]
    lines = [
        "# Quantitative Support Thresholds",
        "",
        *markdown_table(rows, [("threshold", "Threshold"), ("value", "Value"), ("supports", "Supports"), ("blocks", "Blocks if not met")]),
        "",
        "Current M3 status:",
        f"- Blocks primary future claim: `{payload['current_m3_status']['blocks_primary_predictive_validity_claim']}`.",
        "- Reasons:",
    ]
    lines.extend(f"  - {reason}" for reason in payload["current_m3_status"]["reasons"])
    lines.extend(
        [
            "",
            "Boundary:",
            "- Staffing, duration, and any paid budget ceiling remain user-owned decisions.",
            "- Paid-validation authorization remains `false`.",
        ]
    )
    assert_no_prohibited_claims(lines)
    write_text(report_path(config, "support_thresholds"), "\n".join(lines))


def build_release_schema(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    fields = [
        ("release_id", "unique release identifier", "reproducibility"),
        ("freeze_commit", "git commit containing frozen protocol and release manifests", "outcome blindness"),
        ("target_repo", "repository under test", "future validation support"),
        ("base_commit", "task base commit", "reproducibility"),
        ("task_id", "stable task identifier", "reproducibility"),
        ("task_source", "issue, PR, commit, regression, synthetic, manual, or external adapter source", "source quality"),
        ("source_reservoir", "specific reservoir label", "source quality"),
        ("source_license_status", "license and redistribution status", "source quality"),
        ("provenance_digest", "digest of sanitized provenance record", "artifact hygiene"),
        ("task_statement_path", "solver-visible statement path", "reproducibility"),
        ("solver_visible_context_path", "allowed context path", "hidden-oracle protection"),
        ("oracle_source", "real changed tests, generated/synthetic oracle, or manual oracle", "source quality"),
        ("oracle_path_or_digest", "hidden oracle path in verifier workspace or digest only", "hidden-oracle protection"),
        ("hidden_verifier_path_or_digest", "verifier reference without committing private material", "hidden-oracle protection"),
        ("environment_setup", "setup commands and dependency lock reference", "reproducibility"),
        ("dependency_lock", "lockfile or digest", "reproducibility"),
        ("certification_status", "certified, rejected, or repair-needed", "source quality"),
        ("leakage_check_status", "oracle and statement leakage gate", "hidden-oracle protection"),
        ("source_quality_gate", "source sufficiency and context status", "source quality"),
        ("candidate_policy_id", "selection policy identifier", "outcome blindness"),
        ("selected_status", "selected or not selected", "future validation support"),
        ("fallback_label", "fallback selected flag and design", "future validation support"),
        ("fallback_reason", "why fallback was used", "future validation support"),
        ("split_label", "B_eval, H_future, or other frozen split", "outcome blindness"),
        ("time_cutoff", "cutoff used for future or rolling-origin mode", "outcome blindness"),
        ("feature_values", "frozen feature vector", "future validation support"),
        ("tie_break_value", "frozen deterministic tie-break value", "outcome blindness"),
        ("acut_adapter_id", "named ACUT configuration", "adapter accounting"),
        ("endpoint_compliance_status", "LLM_BASE_URL and LLM_API_KEY compliance for paid cells", "adapter accounting"),
        ("cost_latency_accounting", "cost, latency, and retry accounting", "adapter accounting"),
        ("terminal_status", "terminal status category", "adapter accounting"),
        ("score_row_digest", "digest of sanitized score row", "future validation support"),
        ("sanitized_artifact_manifest", "committed manifest of allowed artifacts", "artifact hygiene"),
        ("raw_artifact_storage_policy", "ignored location for raw prompts, transcripts, workspaces, diffs, and verifier material", "artifact hygiene"),
        ("ignored_path_confirmation", "confirmation raw paths are ignored", "artifact hygiene"),
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "release_schema",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "fields": [
            {"field": field, "description": description, "claim_function": claim_function}
            for field, description, claim_function in fields
        ],
        "external_candidate_rule": "external candidates are untrusted until locally certified with source, license, oracle, environment, leakage, and provenance fields",
        "oracle_source_rule": "generated or synthetic oracles must be labeled separately from real changed tests",
        "raw_artifact_rule": "raw prompts, raw completions, ACUT transcripts, workspaces, raw diffs, and hidden verifier material are stored only under ignored paths",
        "boundary": boundary_flags(config),
    }
    write_json(output_path(config, "release_schema"), payload)
    write_release_schema_report(config, payload)
    write_process_report(
        config,
        "Step 8 - Release Artifact Schema",
        [rel(output_path(config, "release_schema")), rel(report_path(config, "release_schema"))],
        ["Release fields are tied to claim functions and raw artifact hygiene."],
    )
    return payload


def write_release_schema_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = payload["fields"]
    lines = [
        "# Benchmark Release Artifact Schema",
        "",
        *markdown_table(rows, [("field", "Field"), ("description", "Description"), ("claim_function", "Claim function")]),
        "",
        "Rules:",
        f"- {payload['external_candidate_rule']}.",
        f"- {payload['oracle_source_rule']}.",
        f"- {payload['raw_artifact_rule']}.",
        "- Paid-validation authorization remains `false`.",
    ]
    assert_no_prohibited_claims(lines)
    write_text(report_path(config, "release_schema"), "\n".join(lines))


def build_power_budget_note(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    snapshot = m3_snapshot(config)
    settings = config["settings"]
    historical_cells = int(settings["historical_pilot_completed_cells"])
    historical_cost = float(settings["historical_pilot_cost_usd"])
    cost_per_cell = historical_cost / historical_cells
    margin = float(settings["future_primary_mae_margin"])
    scenarios = [
        {
            "scenario": "three_repos_two_adapters_twenty_tasks",
            "rough_cells": 3 * 2 * 20,
            "historical_cost_proxy_usd": round_float(3 * 2 * 20 * cost_per_cell, 2),
            "claim_scope": "narrow three-repo follow-up if all gates pass",
        },
        {
            "scenario": "three_repos_two_adapters_two_cutoffs_twenty_tasks",
            "rough_cells": 3 * 2 * 2 * 20,
            "historical_cost_proxy_usd": round_float(3 * 2 * 2 * 20 * cost_per_cell, 2),
            "claim_scope": "rolling-origin stress test; overlapping task reuse could change real cost",
        },
        {
            "scenario": "five_repos_two_adapters_twenty_tasks",
            "rough_cells": 5 * 2 * 20,
            "historical_cost_proxy_usd": round_float(5 * 2 * 20 * cost_per_cell, 2),
            "claim_scope": "broader method support if supply and gates pass",
        },
        {
            "scenario": "five_repos_two_adapters_two_cutoffs_twenty_tasks",
            "rough_cells": 5 * 2 * 2 * 20,
            "historical_cost_proxy_usd": round_float(5 * 2 * 2 * 20 * cost_per_cell, 2),
            "claim_scope": "stronger rolling-origin support; not a current ask",
        },
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "power_budget_note",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "future_effect_size_to_be_persuasive_mae_margin": margin,
        "m3_edge": {
            "candidate_delta_vs_best_baseline_mae": snapshot["overall_delta_vs_best_baseline_mae"],
            "absolute_edge": abs(float(snapshot["overall_delta_vs_best_baseline_mae"])),
            "share_of_future_margin": round_float(abs(float(snapshot["overall_delta_vs_best_baseline_mae"])) / margin),
            "interpretation": "below the future margin and not enough by itself for paid-readiness",
        },
        "historical_context": {
            "completed_cells": historical_cells,
            "cost_usd": historical_cost,
            "cost_per_cell_usd": round_float(cost_per_cell, 4),
            "can_imply": "rough order-of-magnitude context for scenario sizing",
            "cannot_imply": "a budget ceiling, future model pricing, future task duration, staffing, or approval to spend",
        },
        "rough_scenarios": scenarios,
        "user_owned_decisions": [
            "staffing",
            "duration",
            "budget ceiling",
            "whether a future run is exploratory or claim-bearing",
            "approval artifact format",
        ],
        "paid_validation_authorization": False,
        "boundary": boundary_flags(config),
    }
    write_json(output_path(config, "power_budget_note"), payload)
    write_power_budget_report(config, payload)
    write_process_report(
        config,
        "Step 10 - Power And Budget Note",
        [rel(output_path(config, "power_budget_note")), rel(report_path(config, "power_budget_note"))],
        ["The note gives scenario math without setting a budget ceiling or authorizing spending."],
    )
    return payload


def write_power_budget_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = payload["rough_scenarios"]
    lines = [
        "# No-Paid Power And Budget Note",
        "",
        f"Persuasive future MAE margin: `{payload['future_effect_size_to_be_persuasive_mae_margin']}`.",
        "",
        "M3 comparison:",
        f"- Delta vs best simple baseline: `{payload['m3_edge']['candidate_delta_vs_best_baseline_mae']}`.",
        f"- Share of future margin: `{payload['m3_edge']['share_of_future_margin']}`.",
        f"- Interpretation: {payload['m3_edge']['interpretation']}.",
        "",
        "Historical cost context:",
        f"- Completed cells: `{payload['historical_context']['completed_cells']}`.",
        f"- Cost: `${payload['historical_context']['cost_usd']}`.",
        f"- Cost per cell proxy: `${payload['historical_context']['cost_per_cell_usd']}`.",
        "",
        *markdown_table(rows, [("scenario", "Scenario"), ("rough_cells", "Rough cells"), ("historical_cost_proxy_usd", "Historical cost proxy USD"), ("claim_scope", "Scope")]),
        "",
        "Boundary:",
        "- These scenarios are not a budget ceiling.",
        "- Staffing, duration, and spending decisions remain user-owned.",
        "- Paid-validation authorization remains `false`.",
    ]
    assert_no_prohibited_claims(lines)
    write_text(report_path(config, "power_budget_note"), "\n".join(lines))


def build_summary_doc(config_path: str | Path = DEFAULT_CONFIG) -> None:
    config = load_config(config_path)
    claim_modes = read_json(output_path(config, "claim_modes"))
    candidate_policy = read_json(output_path(config, "candidate_policy"))
    baseline_registry = read_json(output_path(config, "baseline_registry"))
    adapter_estimand = read_json(output_path(config, "adapter_estimand"))
    success_gate = read_json(output_path(config, "success_gate"))
    support_thresholds = read_json(output_path(config, "support_thresholds"))
    release_schema = read_json(output_path(config, "release_schema"))
    power_budget = read_json(output_path(config, "power_budget_note"))
    decision_rows = [
        {"item": "Study mode", "decision": "True-future or preregistered rolling-origin can support future validity claims only if all gates are frozen and pass; pseudo-future replay is traction/debugging only."},
        {"item": "Candidate object", "decision": candidate_policy["policy_id"]},
        {"item": "Fallback", "decision": candidate_policy["fallback_governance"]["current_m3_classification"]},
        {"item": "Adapter estimand", "decision": adapter_estimand["primary_estimand"]},
        {"item": "Success gate", "decision": success_gate["gate_type"]},
        {"item": "M3 readiness", "decision": success_gate["current_m3_gate_result"]["classification"]},
        {"item": "Power/budget", "decision": "scenario note only; budget ceiling is user-owned"},
    ]
    figure_steps = [
        "task supply",
        "certification",
        "frozen candidate policy",
        "benchmark release",
        "future ACUT run",
        "score join",
        "baseline comparison",
        "claim gate",
    ]
    freeze_points = [
        "task supply and cutoffs",
        "feature extraction",
        "candidate policy",
        "baselines and seeds",
        "adapter estimand",
        "invalid-cell rules",
        "support thresholds",
        "joint success gate",
    ]
    lines = [
        "# Phase 1 Validation Protocol And Candidate Policy Hardening",
        "",
        "Status: M4 hardening summary, 2026-06-01.",
        "",
        "This document summarizes the M4 no-paid protocol hardening package. It is proposal-facing input for M5, not the reviewer-ready proposal report and not a spending approval.",
        "",
        "## One-Page Decision Summary",
        "",
        *markdown_table(decision_rows, [("item", "Item"), ("decision", "Decision")]),
        "",
        "## Study-Mode Claim Table",
        "",
        *markdown_table(
            [
                {
                    "mode": item["mode"],
                    "can_claim": item["claim_allowed"],
                    "cannot_claim": item["claim_not_allowed"],
                    "freeze_artifact": item["freeze_artifact"],
                }
                for item in claim_modes["study_modes"]
            ],
            [("mode", "Mode"), ("can_claim", "Can claim"), ("cannot_claim", "Cannot claim"), ("freeze_artifact", "Freeze artifact")],
        ),
        "",
        "## Candidate Policy And Fallback",
        "",
        f"Candidate policy: `{candidate_policy['policy_id']}`.",
        "",
        f"Fallback cap: overall <= `{candidate_policy['fallback_governance']['fallback_threshold_rule']['overall_max_share']}`, per repo <= `{candidate_policy['fallback_governance']['fallback_threshold_rule']['per_repo_max_share']}`.",
        "",
        f"Current M3 fallback result: `{candidate_policy['fallback_governance']['current_m3_classification']}` because boltons has fallback share `1.0`.",
        "",
        "## Baseline Registry",
        "",
        "Mandatory future baselines:",
    ]
    lines.extend(f"- `{baseline_id}`" for baseline_id in baseline_registry["mandatory_baseline_ids"])
    lines.extend(
        [
            "",
            "Optional/deferred:",
            "- `coverage_only_same_budget`: add when the selector is frozen outcome-blind.",
            "- `stricter_temporal_recent_same_eligibility`: recommended if supply supports it.",
            "- External/general benchmark comparator: deferred until local certification and licensing are clean.",
            "",
            "## Adapter Estimand",
            "",
            adapter_estimand["primary_claim_rule"],
            "",
            adapter_estimand["pooled_metric_rule"],
            "",
            f"Current M3 cross-adapter status: `{adapter_estimand['current_m3_cross_adapter_status']}`.",
            "",
            "## Joint Gate",
            "",
            f"Gate type: `{success_gate['gate_type']}`.",
            "",
            "M3 does not pass the future gate. Main failures:",
        ]
    )
    lines.extend(f"- {item}" for item in success_gate["current_m3_gate_result"]["main_failures"])
    lines.extend(
        [
            "",
            "## Support Thresholds",
            "",
            *markdown_table(
                [
                    {"threshold": item["threshold"], "value": item["value"], "blocks": item["blocks_if_not_met"]}
                    for item in support_thresholds["thresholds"]
                ],
                [("threshold", "Threshold"), ("value", "Value"), ("blocks", "Blocks if not met")],
            ),
            "",
            "## Release Schema Pointer",
            "",
            f"The full schema is in `{rel(output_path(config, 'release_schema'))}` and `{rel(report_path(config, 'release_schema'))}`. It contains `{len(release_schema['fields'])}` fields tied to reproducibility, source quality, outcome blindness, hidden-oracle protection, adapter accounting, future validation support, and artifact hygiene.",
            "",
            "## Validation-Design Figure Spec",
            "",
            "Flow:",
            "",
            "```text",
            " -> ".join(figure_steps),
            "```",
            "",
            "Freeze points:",
        ]
    )
    lines.extend(f"- {item}" for item in freeze_points)
    lines.extend(
        [
            "",
            "The figure should visually separate true-future and preregistered rolling-origin validation from pseudo-future replay. M5 may render it, but M4 only freezes the spec.",
            "",
            "## Power And Budget Note",
            "",
            f"Future persuasive MAE margin: `{power_budget['future_effect_size_to_be_persuasive_mae_margin']}`.",
            f"M3 aggregate edge: `{power_budget['m3_edge']['absolute_edge']}`, or `{power_budget['m3_edge']['share_of_future_margin']}` of the future margin.",
            "",
            "Scenario math is in the power/budget report. It does not set a budget ceiling; staffing, duration, and spending decisions remain user-owned.",
            "",
            "## Readiness Classification",
            "",
            "`validation_protocol_hardened_candidate_not_paid_ready`.",
            "",
            "M5 can proceed to report integration from this summary. M6 or any budget-bearing discussion still needs user decisions on artifact format, staffing/duration, owner categories, and a conditional budget ceiling.",
        ]
    )
    assert_no_prohibited_claims(lines)
    write_text(doc_path(config, "summary"), "\n".join(lines))


def build_decision(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    if not output_path(config, "claim_modes").exists():
        build_claim_modes(config_path)
    if not output_path(config, "candidate_policy").exists():
        build_candidate_policy(config_path)
    if not output_path(config, "baseline_registry").exists():
        build_baseline_registry(config_path)
    if not output_path(config, "adapter_estimand").exists():
        build_adapter_estimand(config_path)
    if not output_path(config, "success_gate").exists():
        build_success_gate(config_path)
    if not output_path(config, "support_thresholds").exists():
        build_support_thresholds(config_path)
    if not output_path(config, "release_schema").exists():
        build_release_schema(config_path)
    if not output_path(config, "power_budget_note").exists():
        build_power_budget_note(config_path)
    build_summary_doc(config_path)

    success_gate = read_json(output_path(config, "success_gate"))
    support_thresholds = read_json(output_path(config, "support_thresholds"))
    candidate_policy = read_json(output_path(config, "candidate_policy"))
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "decision",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "stop_label": "validation_protocol_hardened_candidate_not_paid_ready",
        "what_happened": "M4 converted the M3 evidence package into explicit validation and candidate-policy rules.",
        "why_it_matters": "M5 can revise the proposal around clear claim boundaries, support thresholds, fallback treatment, and joint gate logic.",
        "m4_owned_placeholders": {
            "study_mode_claim_boundary": "filled",
            "candidate_policy_pseudocode": "filled",
            "fallback_share_threshold": "filled_current_candidate_fails",
            "adapter_estimand": "filled",
            "invalid_cell_and_catastrophic_miss_rules": "filled",
            "joint_success_gate": "filled",
            "support_thresholds": "filled",
            "release_artifact_schema": "filled",
            "validation_design_figure_spec": "filled",
            "power_budget_note": "filled_without_budget_ceiling",
        },
        "current_m3_candidate_passes_hardened_no_paid_readiness_gate": False,
        "current_m3_candidate_classification": success_gate["current_m3_gate_result"]["classification"],
        "fallback_classification": candidate_policy["fallback_governance"]["current_m3_classification"],
        "paid_validation_authorization": False,
        "predictive_validity_state": "not_established",
        "user_decisions_needed_before_M5": False,
        "user_decisions_needed_before_M6_or_budget_bearing_discussion": True,
        "next_recommended_action_category": "M5 reviewer-ready proposal report integration using the M4 summary and artifacts",
        "completion_criteria": {
            "study_mode_claim_boundary": True,
            "candidate_policy_and_fallback_governance": True,
            "adapter_estimand": True,
            "baseline_registry": True,
            "invalid_non_scoreable_catastrophic_rules": True,
            "joint_gate": True,
            "support_thresholds": True,
            "release_schema": True,
            "power_budget_note": True,
            "summary_doc": True,
            "process_sync_pending_manual_docs_update": False,
        },
        "support_threshold_current_status": support_thresholds["current_m3_status"],
        "boundary": boundary_flags(config),
    }
    write_json(output_path(config, "decision"), payload)
    write_decision_report(config, payload)
    write_process_report(
        config,
        "Step 12 - Verification And Closeout",
        [
            rel(output_path(config, "decision")),
            rel(report_path(config, "decision")),
            rel(doc_path(config, "summary")),
        ],
        [
            "All M4-owned protocol placeholders are filled or explicitly narrowed.",
            "The current M3 candidate is classified as not paid-ready under the hardened gate.",
        ],
    )
    return payload


def write_decision_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = [{"placeholder": key, "status": value} for key, value in payload["m4_owned_placeholders"].items()]
    lines = [
        "# Validation Protocol Candidate Policy Hardening Decision",
        "",
        f"Stop label: `{payload['stop_label']}`.",
        "",
        f"What happened: {payload['what_happened']}",
        "",
        f"Why it matters: {payload['why_it_matters']}",
        "",
        "M4-owned placeholder status:",
        "",
        *markdown_table(rows, [("placeholder", "Placeholder"), ("status", "Status")]),
        "",
        "Closeout:",
        f"- Current M3 candidate passes hardened no-paid readiness gate: `{payload['current_m3_candidate_passes_hardened_no_paid_readiness_gate']}`.",
        f"- Current M3 candidate classification: `{payload['current_m3_candidate_classification']}`.",
        f"- Fallback classification: `{payload['fallback_classification']}`.",
        f"- Paid-validation authorization: `{payload['paid_validation_authorization']}`.",
        f"- Predictive-validity state: `{payload['predictive_validity_state']}`.",
        f"- User decisions needed before M5: `{payload['user_decisions_needed_before_M5']}`.",
        f"- User decisions needed before M6 or budget-bearing discussion: `{payload['user_decisions_needed_before_M6_or_budget_bearing_discussion']}`.",
        f"- Next recommended action category: {payload['next_recommended_action_category']}.",
    ]
    assert_no_prohibited_claims(lines)
    write_text(report_path(config, "decision"), "\n".join(lines))


def assert_no_prohibited_claims(lines: list[str]) -> None:
    text = "\n".join(lines).lower()
    hits = [pattern for pattern in PROHIBITED_CLAIM_PATTERNS if pattern in text]
    if hits:
        raise AssertionError(f"prohibited current-claim phrase in generated markdown: {hits}")


def assert_generated_markdown_clean(config: dict[str, Any]) -> None:
    paths = [doc_path(config, "summary"), *[report_path(config, key) for key in config["reports"]]]
    hits: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for pattern in PROHIBITED_CLAIM_PATTERNS:
            if pattern in text:
                hits.append(f"{rel(path)}: {pattern}")
    if hits:
        raise AssertionError("prohibited current-claim phrases found: " + "; ".join(hits))


def build_all(config_path: str | Path = DEFAULT_CONFIG) -> None:
    build_preflight(config_path)
    build_claim_modes(config_path)
    build_candidate_policy(config_path)
    build_baseline_registry(config_path)
    build_adapter_estimand(config_path)
    build_success_gate(config_path)
    build_support_thresholds(config_path)
    build_release_schema(config_path)
    build_power_budget_note(config_path)
    build_decision(config_path)
    assert_generated_markdown_clean(load_config(config_path))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Phase 1 validation protocol and candidate-policy hardening artifacts.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument(
        "--step",
        choices=[
            "preflight",
            "claim_modes",
            "candidate_policy",
            "baseline_registry",
            "adapter_estimand",
            "success_gate",
            "support_thresholds",
            "release_schema",
            "power_budget_note",
            "decision",
            "all",
        ],
        default="all",
    )
    args = parser.parse_args()
    step_map: dict[str, Callable[[str | Path], Any]] = {
        "preflight": build_preflight,
        "claim_modes": build_claim_modes,
        "candidate_policy": build_candidate_policy,
        "baseline_registry": build_baseline_registry,
        "adapter_estimand": build_adapter_estimand,
        "success_gate": build_success_gate,
        "support_thresholds": build_support_thresholds,
        "release_schema": build_release_schema,
        "power_budget_note": build_power_budget_note,
        "decision": build_decision,
        "all": build_all,
    }
    result = step_map[args.step](args.config)
    if result is not None:
        print(json.dumps({"step": args.step, "completed": True}, sort_keys=True))


if __name__ == "__main__":
    main()
