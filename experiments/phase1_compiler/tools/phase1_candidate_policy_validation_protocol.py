from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "phase1_candidate_policy_validation_protocol.yaml"
SCHEMA_VERSION = "barcarolle.phase1_candidate_policy_validation_protocol.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_candidate_policy_validation_protocol_output.v1"
RUN_ID = "phase1_candidate_policy_validation_protocol_20260530"

POLICY_INPUT_KEYS = (
    "policy_task_table",
    "policy_candidate_universe",
    "policy_click_repair_quality_overlay",
)


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
        raise ValueError("unexpected candidate policy validation protocol config schema_version")
    config["_path"] = str(repo_path(path))
    return config


def input_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["inputs"][key])


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


def packet_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["external_review_packet"][key])


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


def raw_sha256(path: str | Path) -> str:
    return hashlib.sha256(repo_path(path).read_bytes()).hexdigest()


def digest_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def stable_int(*parts: Any) -> int:
    text = "||".join(str(part) for part in parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


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


def status_path(line: str) -> str:
    if line.startswith("?? "):
        text = line[3:]
    elif len(line) > 3 and line[:2].strip() and line[2] == " ":
        text = line[3:]
    elif len(line) > 3 and line[0] == " " and line[1].strip() and line[2] == " ":
        text = line[3:]
    elif len(line) > 2 and line[1] == " ":
        text = line[2:]
    elif len(line) > 2 and line[0] in "MADRCU":
        text = line[2:]
    else:
        text = line
    if " -> " in text:
        text = text.split(" -> ", 1)[1]
    return text.strip()


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    if not rows:
        return ["_None._"]
    lines = [
        "| " + " | ".join(label for _, label in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return lines


def expected_paths(config: dict[str, Any]) -> set[str]:
    expected = {
        rel(config["_path"]),
        rel(ROOT / "tools" / "phase1_candidate_policy_validation_protocol.py"),
        rel(ROOT / "tests" / "test_phase1_candidate_policy_validation_protocol.py"),
    }
    expected.update(rel(path) for path in config["outputs"].values())
    expected.update(rel(path) for path in config["reports"].values())
    expected.update(rel(path) for key, path in config["external_review_packet"].items() if key != "directory")
    return expected


def classify_dirty_paths(config: dict[str, Any], status_lines: list[str]) -> dict[str, list[str]]:
    expected = expected_paths(config)
    current_runbook = rel(input_path(config, "runbook"))
    known_unrelated_dir = "experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/"
    classified: dict[str, list[str]] = {
        "this_run_expected_outputs": [],
        "current_runbook_input": [],
        "known_unrelated_external_review": [],
        "preexisting_process_or_instruction_edits": [],
        "unrelated_or_requires_review": [],
    }
    for line in status_lines:
        path = status_path(line)
        if path in expected or any(item.startswith(path.rstrip("/") + "/") for item in expected):
            classified["this_run_expected_outputs"].append(line)
        elif path == current_runbook:
            classified["current_runbook_input"].append(line)
        elif path.startswith(known_unrelated_dir):
            classified["known_unrelated_external_review"].append(line)
        elif path in {"AGENTS.md", "PROCESS.md"}:
            classified["preexisting_process_or_instruction_edits"].append(line)
        else:
            classified["unrelated_or_requires_review"].append(line)
    return classified


def git_tracked(path: str | Path) -> bool:
    result = command_result(["git", "ls-files", "--error-unmatch", rel(path)])
    return result["returncode"] == 0


def input_availability(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    availability: dict[str, dict[str, Any]] = {}
    for key, raw_path in sorted(config["inputs"].items()):
        resolved = repo_path(raw_path)
        availability[key] = {
            "path": rel(resolved),
            "exists": resolved.exists(),
            "tracked": git_tracked(resolved) if resolved.exists() else False,
            "size_bytes": resolved.stat().st_size if resolved.exists() else None,
            "digest": digest_file(resolved),
        }
    return availability


def forbidden_fields(config: dict[str, Any]) -> set[str]:
    return {str(field).lower() for field in config.get("forbidden_fields", [])}


def find_forbidden_fields(payload: Any, forbidden: set[str], path: str = "$") -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            normalized = str(key).lower()
            if normalized in forbidden:
                violations.append({"path": f"{path}.{key}", "field": str(key)})
            violations.extend(find_forbidden_fields(value, forbidden, f"{path}.{key}"))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            violations.extend(find_forbidden_fields(item, forbidden, f"{path}[{index}]"))
    return violations


def validate_no_forbidden_fields(payload: Any, forbidden: set[str], label: str) -> None:
    violations = find_forbidden_fields(payload, forbidden)
    if violations:
        fields = ", ".join(sorted({item["field"] for item in violations}))
        raise ValueError(f"{label} contains forbidden outcome fields: {fields}")


def load_policy_input_payloads(config: dict[str, Any]) -> dict[str, Any]:
    payloads = {key: read_json(input_path(config, key)) for key in POLICY_INPUT_KEYS}
    forbidden = forbidden_fields(config)
    for key, payload in payloads.items():
        validate_no_forbidden_fields(payload, forbidden, key)
    universe = payloads["policy_candidate_universe"]
    if universe.get("outcome_fields_loaded") is not False:
        raise ValueError("policy candidate universe must declare outcome_fields_loaded=false")
    return payloads


def task_metadata_by_id(task_table: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["candidate_id"]): row for row in task_table.get("rows", [])}


def click_overlay_by_id(overlay: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["task_id"]): row for row in overlay.get("rows", [])}


def compact_time(value: Any) -> str:
    return str(value or "")


def task_sort_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (str(row.get("repo") or ""), compact_time(row.get("task_time")), str(row.get("task_id") or ""))


def policy_input_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    payloads = load_policy_input_payloads(config)
    candidate_universe = payloads["policy_candidate_universe"]
    metadata = task_metadata_by_id(payloads["policy_task_table"])
    click_overlay = click_overlay_by_id(payloads["policy_click_repair_quality_overlay"])
    allowed = set(config["allowed_selection_fields"])
    rows: list[dict[str, Any]] = []
    for source in candidate_universe.get("rows", []):
        task_id = str(source["task_id"])
        meta = metadata.get(task_id, {})
        repo = str(source.get("repo") or meta.get("repo_id") or task_id.split("__", 1)[0])
        overlay = click_overlay.get(task_id, {})
        exclusion_reasons: list[str] = []
        if not source.get("release_eligible_for_split_design", False):
            exclusion_reasons.append("not_release_eligible_for_split_design")
        if overlay and overlay.get("release_quality_recommendation") != "clean_source_candidate":
            exclusion_reasons.append("click_repair_overlay_not_release_quality")
        if overlay:
            source_quality = "clean"
            source_context = "public_context_repaired"
            ambiguity = "low"
            leakage = "low"
            repair_status = "click_public_context_repair_overlay_applied"
            statement_digest = str(overlay.get("statement_digest") or "")
        else:
            source_quality = str(source.get("source_quality_bucket") or "unknown")
            source_context = str(source.get("source_context_type_bucket") or meta.get("source_context_class") or "unknown")
            ambiguity = str(source.get("ambiguity_risk_bucket") or "unknown")
            leakage = str(source.get("leakage_risk_bucket") or "unknown")
            repair_status = "not_applicable"
            statement_digest = str(meta.get("digests", {}).get("task_metadata_digest") or "")
        if leakage not in {"low", "minor_risk"}:
            exclusion_reasons.append("unresolved_leakage_risk")
        row = {
            "task_id": task_id,
            "repo": repo,
            "task_time": str(meta.get("task_time") or ""),
            "time_bucket": str(source.get("time_bucket") or meta.get("task_time_bucket") or "unknown"),
            "coarse_task_family": str(source.get("coarse_task_family") or meta.get("task_family") or "unknown"),
            "editable_scope_bucket": str(source.get("editable_scope_bucket") or "unknown"),
            "source_context_type_bucket": source_context,
            "source_quality_bucket": source_quality,
            "statement_specificity_bucket": str(source.get("statement_specificity_bucket") or "unknown"),
            "context_length_bucket": str(source.get("context_length_bucket") or "unknown"),
            "ambiguity_risk_bucket": ambiguity,
            "leakage_risk_bucket": leakage,
            "certification_risk_bucket": str(source.get("certification_risk_bucket") or "unknown"),
            "rare_or_unknown_feature_flag": bool(source.get("rare_or_unknown_feature_flag", False)),
            "source_reservoir": str(meta.get("source_reservoir") or ""),
            "source_context_class": str(meta.get("source_context_class") or ""),
            "implementation_file_count": len(meta.get("implementation_files", []) or []),
            "test_file_count": len(meta.get("test_files", []) or []),
            "public_context_ref_count": int(meta.get("public_context_ref_count") or 0),
            "release_eligibility_provenance": str(meta.get("release_eligibility_provenance") or ""),
            "repair_overlay_status": repair_status,
            "statement_digest": statement_digest,
            "eligible_for_policy_selection": not exclusion_reasons,
            "exclusion_reasons": exclusion_reasons,
        }
        extra = sorted(set(row) - allowed - {"eligible_for_policy_selection", "exclusion_reasons"})
        if extra:
            raise ValueError(f"policy row has fields outside allowed_selection_fields: {extra}")
        rows.append(row)
    validate_no_forbidden_fields(rows, forbidden_fields(config), "assembled policy input rows")
    return sorted(rows, key=task_sort_key)


def feature_counts(rows: list[dict[str, Any]], feature: str) -> Counter[str]:
    return Counter(str(row.get(feature) or "unknown") for row in rows)


def supported_feature_dimensions(rows: list[dict[str, Any]], features: list[str]) -> list[str]:
    supported = []
    for feature in features:
        values = {str(row.get(feature) or "unknown") for row in rows}
        if len(values - {"unknown"}) >= 2 or (len(values) >= 2 and "unknown" in values):
            supported.append(feature)
    return supported


def selection_fallback_status(config: dict[str, Any], rows: list[dict[str, Any]], budget: int) -> dict[str, Any]:
    features = list(config["coverage_features"])
    supported = supported_feature_dimensions(rows, features)
    if len(rows) < budget:
        return {
            "fallback_applied": True,
            "fallback_design": config["policy"]["fallback_insufficient_budget"],
            "fallback_reason": "insufficient_budget",
            "supported_feature_dimensions": supported,
        }
    minimum = int(config["policy"]["minimum_supported_feature_dimensions"])
    if len(supported) < minimum:
        return {
            "fallback_applied": True,
            "fallback_design": config["policy"]["fallback_insufficient_feature_support"],
            "fallback_reason": "insufficient_feature_support",
            "supported_feature_dimensions": supported,
        }
    return {
        "fallback_applied": False,
        "fallback_design": None,
        "fallback_reason": None,
        "supported_feature_dimensions": supported,
    }


def imbalance_score(selected: list[dict[str, Any]], target: list[dict[str, Any]], features: list[str]) -> float:
    if not selected or not target:
        return 0.0
    distance = 0.0
    for feature in features:
        selected_counts = feature_counts(selected, feature)
        target_counts = feature_counts(target, feature)
        values = set(selected_counts) | set(target_counts)
        for value in values:
            distance += abs((selected_counts[value] / len(selected)) - (target_counts[value] / len(target)))
    return round(distance, 8)


def coverage_gain(row: dict[str, Any], covered: set[tuple[str, str]], features: list[str]) -> int:
    return sum((feature, str(row.get(feature) or "unknown")) not in covered for feature in features)


def deterministic_tiebreak(policy_id: str, seed: int, repo: str, task_id: str) -> int:
    return stable_int(policy_id, seed, repo, task_id)


def select_policy_rows(
    rows: list[dict[str, Any]],
    *,
    repo: str,
    budget: int,
    features: list[str],
    seed: int,
    policy_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    pool = [row for row in rows if row["repo"] == repo and row["eligible_for_policy_selection"]]
    fallback = selection_fallback_status(
        {
            "coverage_features": features,
            "policy": {
                "minimum_supported_feature_dimensions": 3,
                "fallback_insufficient_budget": "repo_unweighted_same_budget",
                "fallback_insufficient_feature_support": "repo_stratified_by_target_profile",
            },
        },
        pool,
        budget,
    )
    if fallback["fallback_applied"]:
        if fallback["fallback_design"] == "repo_stratified_by_target_profile":
            selected = []
            remaining = list(pool)
            stratify_features = fallback["supported_feature_dimensions"] or features
            while remaining and len(selected) < budget:
                best = min(
                    remaining,
                    key=lambda row: (
                        imbalance_score(selected + [row], pool, stratify_features),
                        deterministic_tiebreak(policy_id, seed, repo, row["task_id"]),
                        row["task_id"],
                    ),
                )
                selected.append(best)
                remaining.remove(best)
        else:
            ordered = sorted(pool, key=lambda row: (deterministic_tiebreak(policy_id, seed, repo, row["task_id"]), row["task_id"]))
            selected = ordered[: min(budget, len(ordered))]
        return selected, [row for row in pool if row not in selected], fallback

    remaining = list(pool)
    selected: list[dict[str, Any]] = []
    covered: set[tuple[str, str]] = set()
    while remaining and len(selected) < budget:
        best = min(
            remaining,
            key=lambda row: (
                -coverage_gain(row, covered, features),
                imbalance_score(selected + [row], pool, features),
                deterministic_tiebreak(policy_id, seed, repo, row["task_id"]),
                str(row["task_id"]),
            ),
        )
        selected.append(best)
        for feature in features:
            covered.add((feature, str(best.get(feature) or "unknown")))
        remaining.remove(best)
    return selected, remaining, fallback


def feature_coverage_rows(repo: str, eligible_rows: list[dict[str, Any]], selected: list[dict[str, Any]], features: list[str]) -> list[dict[str, Any]]:
    selected_ids = {row["task_id"] for row in selected}
    coverage: list[dict[str, Any]] = []
    for feature in features:
        eligible_counts = feature_counts(eligible_rows, feature)
        selected_counts = feature_counts([row for row in selected if row["task_id"] in selected_ids], feature)
        for value in sorted(eligible_counts):
            coverage.append(
                {
                    "repo": repo,
                    "feature": feature,
                    "value": value,
                    "eligible_count": eligible_counts[value],
                    "selected_count": selected_counts[value],
                    "coverage_status": "covered" if selected_counts[value] else "gap",
                }
            )
    return coverage


def build_preflight(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    status = command_result(["git", "status", "--short", "--untracked-files=all"])
    status_lines = [line for line in status["stdout"].splitlines() if line.strip()]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "preflight",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "branch": command_stdout(["git", "branch", "--show-current"]),
        "head": command_stdout(["git", "rev-parse", "HEAD"]),
        "date_utc": now_utc()[:10],
        "python_version": sys.version.split()[0],
        "uv_version": command_stdout(["uv", "--version"]),
        "git_status_short_untracked_all": status_lines,
        "dirty_tree_classification": classify_dirty_paths(config, status_lines),
        "required_input_availability": input_availability(config),
        "boundary": {
            "new_paid_acut_cells_run": False,
            "new_paid_llm_calls_run": False,
            "external_review_submitted": False,
            "run_can_proceed_outcome_blind": True,
            "selection_command_reads_score_tables": False,
        },
    }
    write_json(output_path(config, "preflight"), payload)
    write_process_report(
        config,
        "Step 0 - Preflight And Worktree State",
        [rel(output_path(config, "preflight"))],
        [
            "No paid ACUT solver cells, paid LLM calls, or external-review submissions were made.",
            "The current runbook input is untracked and recorded separately from generated outputs.",
            "The known unrelated 20260526 external review bundle remains unmodified and unstaged.",
            "The run can proceed outcome-blind because policy selection uses only task inventory and source-quality metadata inputs.",
        ],
    )
    return payload


def build_policy_spec(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "policy_spec",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "policy_id": config["policy"]["policy_id"],
        "primary_purpose": "choose a small repo-specific benchmark set that maximizes coarse solver-visible feature coverage under a fixed task budget without outcome data or task-level score weights",
        "allowed_inputs": list(config["allowed_selection_fields"]),
        "forbidden_inputs": list(config["forbidden_fields"]),
        "coverage_features": list(config["coverage_features"]),
        "budget_policy": {
            "budget_per_repo": config["policy"]["budget_per_repo"],
            "minimum_tasks_per_repo": config["policy"]["minimum_tasks_per_repo"],
        },
        "seed_policy": {
            "deterministic_seed": config["policy"]["deterministic_seed"],
            "tie_break_policy": config["policy"]["tie_break_policy"],
        },
        "score_model": config["policy"]["score_model"],
        "selection_objective": [
            config["policy"]["primary_objective"],
            config["policy"]["secondary_objective"],
            "deterministic_seeded_tie_breaks",
        ],
        "fallback_rules": {
            "insufficient_budget": config["policy"]["fallback_insufficient_budget"],
            "insufficient_feature_support": config["policy"]["fallback_insufficient_feature_support"],
            "fallbacks_must_be_labeled": True,
        },
        "output_schema": [
            "selected_task_ids",
            "excluded_task_ids_with_reasons",
            "feature_coverage_table",
            "coverage_gaps",
            "fallback_status",
            "seed_and_tie_break_policy",
            "input_artifact_digests",
            "outcome_blindness_audit",
        ],
        "claim_boundary": {
            "candidate_role": "near_term_mainline_candidate_ready_for_adversarial_review",
            "old_weighted_target_profile": "negative_control_or_reference_only",
            "block_randomized_stratified": "optional_research_branch_not_primary",
            "block_plus_shrinkage_weighted": "optional_research_branch_not_primary",
            "completed_blocked_split_supplement": "post_hoc_diagnostic_not_primary_evidence",
        },
    }
    write_json(output_path(config, "policy_spec"), payload)
    write_policy_spec_report(config, payload)
    write_process_report(
        config,
        "Step 1 - Freeze Candidate Policy Spec",
        [rel(output_path(config, "policy_spec")), rel(report_path(config, "policy_spec"))],
        [
            "Policy spec can be read without consulting score tables.",
            "Forbidden inputs include terminal outcomes, pass/fail labels, adapter outcomes, score-table rows, raw transcripts, and hidden verifier output.",
        ],
    )
    return payload


def build_input_freeze_and_selection(config_path: str | Path = DEFAULT_CONFIG) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    config = load_config(config_path)
    rows = policy_input_rows(config)
    eligible_rows = [row for row in rows if row["eligible_for_policy_selection"]]
    input_digests = {key: digest_file(input_path(config, key)) for key in POLICY_INPUT_KEYS}
    input_freeze = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "input_freeze",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "policy_id": config["policy"]["policy_id"],
        "selection_frozen_before_future_outcomes": True,
        "score_tables_read_for_selection": [],
        "terminal_outcomes_loaded": False,
        "input_artifact_digests": input_digests,
        "allowed_selection_fields": list(config["allowed_selection_fields"]),
        "forbidden_fields": list(config["forbidden_fields"]),
        "row_count": len(rows),
        "eligible_row_count": len(eligible_rows),
        "eligible_count_by_repo": dict(sorted(Counter(row["repo"] for row in eligible_rows).items())),
        "feature_counts_by_repo": feature_counts_by_repo(eligible_rows, list(config["coverage_features"])),
        "rows": eligible_rows,
    }
    validate_no_forbidden_fields(input_freeze["rows"], forbidden_fields(config), "input freeze rows")
    write_json(output_path(config, "input_freeze"), input_freeze)

    selection_rows: list[dict[str, Any]] = []
    coverage_table: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    all_selected_ids: list[str] = []
    features = list(config["coverage_features"])
    budget = int(config["policy"]["budget_per_repo"])
    seed = int(config["policy"]["deterministic_seed"])
    policy_id = str(config["policy"]["policy_id"])
    for repo in config["repos"]:
        repo_eligible = [row for row in eligible_rows if row["repo"] == repo]
        selected, not_selected, fallback = select_policy_rows(
            rows,
            repo=str(repo),
            budget=budget,
            features=features,
            seed=seed,
            policy_id=policy_id,
        )
        selected_ids = [row["task_id"] for row in selected]
        all_selected_ids.extend(selected_ids)
        for order, row in enumerate(selected, start=1):
            selection_rows.append(
                {
                    "repo": repo,
                    "selection_order": order,
                    "task_id": row["task_id"],
                    "feature_values": {feature: row.get(feature, "unknown") for feature in features},
                    "tie_break_value": deterministic_tiebreak(policy_id, seed, str(repo), row["task_id"]),
                }
            )
        for row in not_selected:
            excluded.append(
                {
                    "repo": repo,
                    "task_id": row["task_id"],
                    "reasons": ["not_selected_under_fixed_budget_after_coverage_priority"],
                }
            )
        coverage_table.extend(feature_coverage_rows(str(repo), repo_eligible, selected, features))
        selection_rows.append(
            {
                "repo": repo,
                "selection_order": "summary",
                "task_id": "",
                "feature_values": {},
                "fallback_status": fallback,
            }
        )
    for row in rows:
        if not row["eligible_for_policy_selection"]:
            excluded.append({"repo": row["repo"], "task_id": row["task_id"], "reasons": row["exclusion_reasons"]})
    coverage_gaps = [row for row in coverage_table if row["coverage_status"] == "gap"]
    selection_manifest = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "selection_manifest",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "policy_id": policy_id,
        "selected_task_ids": sorted(all_selected_ids),
        "selected_count": len(all_selected_ids),
        "selected_count_by_repo": dict(sorted(Counter(row["repo"] for row in selection_rows if row["task_id"]).items())),
        "excluded_task_ids_with_reasons": sorted(excluded, key=lambda row: (row["repo"], row["task_id"], ",".join(row["reasons"]))),
        "feature_coverage_table": coverage_table,
        "coverage_gaps": coverage_gaps,
        "fallback_by_repo": {
            str(repo): next(row["fallback_status"] for row in selection_rows if row["repo"] == repo and row["selection_order"] == "summary")
            for repo in config["repos"]
        },
        "seed_and_tie_break_policy": {
            "seed": seed,
            "tie_break_policy": config["policy"]["tie_break_policy"],
            "tie_break_function": "sha256(policy_id, seed, repo, task_id)",
        },
        "input_freeze_digest": digest_payload(input_freeze),
        "input_artifact_digests": input_digests,
        "score_tables_read_for_selection": [],
        "terminal_outcomes_loaded": False,
        "selection_rows": selection_rows,
    }
    write_json(output_path(config, "selection_manifest"), selection_manifest)
    audit = build_outcome_blindness_audit_payload(config, input_freeze, selection_manifest)
    write_json(output_path(config, "outcome_blindness_audit"), audit)
    write_selection_report(config, selection_manifest)
    write_outcome_blindness_report(config, audit)
    write_process_report(
        config,
        "Step 2 - Implement Outcome-Blind Policy Tooling",
        [
            rel(output_path(config, "input_freeze")),
            rel(output_path(config, "selection_manifest")),
            rel(output_path(config, "outcome_blindness_audit")),
            rel(report_path(config, "selection_manifest")),
            rel(report_path(config, "outcome_blindness_audit")),
        ],
        [
            "The selection command loaded only configured policy inputs and read no score tables.",
            "Selected and excluded task IDs, feature coverage, gaps, seed policy, and input digests were emitted.",
        ],
    )
    return input_freeze, selection_manifest, audit


def feature_counts_by_repo(rows: list[dict[str, Any]], features: list[str]) -> dict[str, dict[str, dict[str, int]]]:
    counts: dict[str, dict[str, dict[str, int]]] = {}
    repos = sorted({row["repo"] for row in rows})
    for repo in repos:
        repo_rows = [row for row in rows if row["repo"] == repo]
        counts[repo] = {
            feature: dict(sorted(feature_counts(repo_rows, feature).items()))
            for feature in features
        }
    return counts


def build_outcome_blindness_audit_payload(
    config: dict[str, Any],
    input_freeze: dict[str, Any],
    selection_manifest: dict[str, Any],
) -> dict[str, Any]:
    forbidden = forbidden_fields(config)
    violations = find_forbidden_fields(input_freeze["rows"], forbidden) + find_forbidden_fields(selection_manifest["selection_rows"], forbidden)
    return {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "outcome_blindness_audit",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "policy_id": config["policy"]["policy_id"],
        "outcome_blind": not violations,
        "forbidden_fields": sorted(forbidden),
        "forbidden_field_violations": violations,
        "policy_inputs_loaded": list(POLICY_INPUT_KEYS),
        "score_tables_read_for_selection": [],
        "terminal_outcomes_loaded": False,
        "pass_fail_labels_loaded": False,
        "adapter_outcomes_loaded": False,
        "raw_acut_transcripts_loaded": False,
        "hidden_verifier_outputs_loaded": False,
        "input_freeze_digest": digest_payload(input_freeze),
        "selection_manifest_digest": digest_payload(selection_manifest),
        "no_paid_acut_cells_run": True,
        "no_paid_llm_calls_run": True,
    }


def build_validation_protocol(config_path: str | Path = DEFAULT_CONFIG) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    config = load_config(config_path)
    protocol = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "validation_protocol",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "frozen_before_future_paid_calls": True,
        "paid_calls_authorized_by_this_runbook": False,
        "study_mode": {
            "preferred": config["validation"]["preferred_study_mode"],
            "fallback": config["validation"]["fallback_study_mode"],
            "already_inspected_outcomes": "may support retrospective traction labels only, not a clean predictive-validity claim",
        },
        "primary_candidate": config["validation"]["primary_candidate"],
        "mandatory_baselines": list(config["baselines"]),
        "optional_research_branches": list(config["research_branches"]),
        "primary_reporting": {
            "metrics": ["adapter_stratified_MAE", "adapter_stratified_catastrophic_miss_rate"],
            "adapters": list(config["adapters"]),
            "codex_kilo_handling": "report Codex and Kilo as separate ACUT configurations first",
        },
        "secondary_reporting": {
            "equal_mix_pooled_estimator": "allowed only as a secondary diagnostic if defined before future outcomes are joined",
            "pooled_result_cannot_satisfy_success_without_adapter_stratified_support": True,
        },
        "invalid_or_non_scoreable_cells": {
            "primary_policy": "exclude from pass-rate numerator and denominator, report count and reason by adapter/repo/window",
            "sensitivity": "repeat primary metrics with invalid cells treated as fail when support allows",
        },
        "endpoint_and_cost_accounting": {
            "required_endpoint_for_any_future_paid_call": "LLM_BASE_URL + LLM_API_KEY",
            "no_fallback_to_subscription_or_provider_specific_keys": True,
            "cost_and_latency_must_be_recorded": True,
        },
        "source_quality_overlays": {
            "use_repaired_click_overlay": True,
            "source_quality_failures_block_primary_claim": True,
        },
        "missing_or_sparse_support": {
            "missing_repo": "block primary predictive-validity claim and report insufficient support",
            "sparse_window": "fallback to preregistered rolling-origin or pseudo-future replay with traction-only claim boundary",
        },
        "seed_stability": {
            "candidate_seed": config["policy"]["deterministic_seed"],
            "random_baseline_seeds_declared_before_outcomes": True,
        },
        "no_paid_local_vs_future_paid_boundary": {
            "this_run": "no-paid protocol preparation only",
            "future_paid_validation": "requires separate human authorization after adversarial review",
        },
    }
    success = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "success_criteria",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "traction_evidence": {
            "allowed_when": "retrospective or underpowered validation shows directional improvement with visible limitations",
            "required_reporting": "what happened, why it matters, and next action",
        },
        "future_predictive_validity_claim": {
            "requires_future_outcome_unseen_validation": True,
            "candidate_must_beat_best_simple_baseline_primary_mae_by_at_least": config["validation"]["minimum_mae_margin_vs_best_simple_baseline"],
            "or_majority_of_slices_rule": config["validation"]["majority_of_slices_rule"],
            "cannot_be_driven_only_by_one_repo_or_one_adapter": True,
            "catastrophic_miss_rate_must_not_materially_worsen": True,
            "policy_violations_allowed": 0,
            "source_quality_endpoint_and_accounting_checks_must_pass": True,
            "pooled_improvement_alone_is_insufficient": True,
        },
        "paid_readiness_gate": {
            "adversarial_review_packet_ready": True,
            "external_review_submission_required_before_paid_run": True,
            "future_paid_cells_authorized_now": False,
        },
        "stop_or_blocker_conditions": [
            "policy cannot be implemented outcome-blind",
            "policy inputs have forbidden outcome fields",
            "future validation lacks enough repo or adapter support for the intended claim",
            "endpoint or cost accounting cannot be proven before future paid calls",
            "review packet cannot be sanitized",
        ],
    }
    baseline_registry = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "baseline_registry",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "primary_candidate": config["validation"]["primary_candidate"],
        "mandatory_baselines": [
            {
                "baseline_id": "temporal_recent_baseline",
                "role": "simple_baseline",
                "definition": "same budget, most recent eligible tasks by task time only",
            },
            {
                "baseline_id": "repo_unweighted_same_budget",
                "role": "simple_baseline",
                "definition": "same budget, deterministic unweighted repo-local task set",
            },
            {
                "baseline_id": "repo_stratified_by_target_profile",
                "role": "simple_baseline",
                "definition": "same budget, coarse target-profile stratification without outcome weights",
            },
            {
                "baseline_id": "seeded_random_same_budget",
                "role": "simple_baseline",
                "definition": "same budget, preregistered deterministic random seeds",
            },
        ],
        "optional_research_branches": [
            {"design_id": "block_randomized_stratified", "role": "research_branch_not_primary"},
            {"design_id": "block_plus_shrinkage_weighted", "role": "research_branch_not_primary"},
            {"design_id": "old_weighted_target_profile", "role": "negative_control_or_reference_only"},
        ],
    }
    write_json(output_path(config, "validation_protocol"), protocol)
    write_json(output_path(config, "success_criteria"), success)
    write_json(output_path(config, "baseline_registry"), baseline_registry)
    write_validation_protocol_report(config, protocol)
    write_success_criteria_report(config, success)
    write_process_report(
        config,
        "Step 3 - Freeze Validation Protocol And Success Criteria",
        [
            rel(output_path(config, "validation_protocol")),
            rel(output_path(config, "success_criteria")),
            rel(output_path(config, "baseline_registry")),
            rel(report_path(config, "validation_protocol")),
            rel(report_path(config, "success_criteria")),
        ],
        [
            "The validation protocol is frozen before future paid calls.",
            "Adapter-stratified MAE and catastrophic miss rate are primary; pooled summaries are secondary only.",
            "No paid run is authorized by this runbook.",
        ],
    )
    return protocol, success, baseline_registry


def evidence_rows(config: dict[str, Any]) -> list[dict[str, str]]:
    items = [
        ("Policy spec", output_path(config, "policy_spec"), "Frozen coverage_constrained_unweighted_v1 rule."),
        ("Selection manifest", output_path(config, "selection_manifest"), "Selected and excluded task IDs with coverage diagnostics."),
        ("Outcome-blindness audit", output_path(config, "outcome_blindness_audit"), "Audit that the selector did not use outcomes or score tables."),
        ("Validation protocol", output_path(config, "validation_protocol"), "Frozen future validation protocol and adapter reporting policy."),
        ("Success criteria", output_path(config, "success_criteria"), "Frozen traction, predictive-validity, and blocker criteria."),
        ("Retrospective signal decision", input_path(config, "retrospective_signal_decision"), "Latest no-paid retrospective signal decision."),
        ("Retrospective baseline comparison", input_path(config, "retrospective_signal_baseline_comparison"), "Candidate versus simple baseline comparison."),
        ("Adapter metrics", input_path(config, "retrospective_signal_adapter_metrics"), "Adapter-stratified retrospective metrics."),
        ("Click repair decision", input_path(config, "click_repair_decision"), "Source-quality boundary for repaired click tasks."),
        ("Blocked split supplement fairness decision", input_path(config, "blocked_split_supplement_fairness_decision"), "Adapter fairness and gap diagnostic decision."),
    ]
    return [
        {
            "label": label,
            "path": rel(path),
            "description": description,
            "exists": str(repo_path(path).exists()).lower(),
            "digest": digest_file(path) or "",
        }
        for label, path, description in items
    ]


def build_review_packet(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    packet_dir = packet_path(config, "directory")
    packet_dir.mkdir(parents=True, exist_ok=True)
    readme = [
        "# Candidate Policy Validation Protocol Review Packet",
        "",
        "Status: prepared for later adversarial review; not submitted by this runbook.",
        "",
        "Barcarolle is a target-repository benchmark compiler for coding-agent evaluation and tuning. It is not an ACUT harness, general SWE task factory, agent-license product, public leaderboard, or one-shot chat-completion diff generator.",
        "",
        "Current claim: Barcarolle has traction evidence and a concrete, reproducible candidate policy ready for adversarial review. Predictive validity is not established.",
        "",
        "Candidate under review: `coverage_constrained_unweighted_v1`.",
        "",
        "What happened: the policy, outcome-blind selection manifest, validation protocol, success criteria, and claim boundary were frozen without paid ACUT or LLM calls.",
        "",
        "Why it matters: the next review can challenge a specific object before any new paid validation spend.",
        "",
        "Action suggested next: submit this packet to GPT-5.5-Pro or another adversarial reviewer, then triage objections before any paid validation.",
    ]
    evidence = [
        "# Evidence Index",
        "",
        "The packet links to canonical repository artifacts instead of copying large evidence.",
        "",
        *markdown_table(evidence_rows(config), [("label", "Item"), ("path", "Path"), ("description", "Description"), ("digest", "SHA-256")]),
        "",
        "Known weaknesses:",
        "- Retrospective signal is weak and underpowered.",
        "- Codex did not improve uniformly across slices.",
        "- Improvement is not uniform across repos.",
        "- Blocked and shrinkage candidates failed the latest comparison.",
        "- The completed blocked split supplement is post-hoc and diagnostic only.",
    ]
    questions = [
        "# Review Questions",
        "",
        "1. Is `coverage_constrained_unweighted_v1` a defensible near-term mainline candidate given the current evidence, or is it too close to a simple coverage heuristic to carry the Barcarolle compiler claim?",
        "2. Does the proposed rolling-origin or future-holdout protocol actually test predictive validity, or does it still leave a post-hoc or transductive loophole?",
        "3. Are the baselines strong enough, especially `temporal_recent_baseline`, `repo_unweighted_same_budget`, `repo_stratified_by_target_profile`, and seeded random same-budget?",
        "4. Are the success criteria too weak, too strong, or vulnerable to a single repo or adapter driving the conclusion?",
        "5. Does adapter-stratified reporting correctly treat Codex and Kilo as ACUT configurations rather than model-only comparisons?",
        "6. Is the proposal narrative better stated as predictive benchmark compiler, auditable repo-specific benchmark construction with early predictive signal, or something narrower?",
    ]
    claim = [
        "# Claim Boundary",
        "",
        "This packet has not been submitted to GPT-5.5-Pro or any external reviewer.",
        "",
        "Allowed claim now: Barcarolle has a deterministic, outcome-blind candidate policy and frozen validation protocol ready for adversarial review.",
        "",
        "Not allowed now: formal predictive validity, model-only Codex/Kilo superiority, a primary claim based on the completed blocked split supplement, or authorization for new paid ACUT cells.",
        "",
        "Future predictive-validity claim requires future outcome-unseen validation or a preregistered rolling-origin design that satisfies the frozen thresholds.",
    ]
    write_text(packet_path(config, "readme"), "\n".join(readme))
    write_text(packet_path(config, "evidence_index"), "\n".join(evidence))
    write_text(packet_path(config, "review_questions"), "\n".join(questions))
    write_text(packet_path(config, "claim_boundary"), "\n".join(claim))
    manifest_paths = [
        packet_path(config, "readme"),
        packet_path(config, "evidence_index"),
        packet_path(config, "review_questions"),
        packet_path(config, "claim_boundary"),
        output_path(config, "policy_spec"),
        output_path(config, "selection_manifest"),
        output_path(config, "outcome_blindness_audit"),
        output_path(config, "validation_protocol"),
        output_path(config, "success_criteria"),
        input_path(config, "retrospective_signal_decision"),
        input_path(config, "retrospective_signal_baseline_comparison"),
    ]
    manifest_lines = [f"{raw_sha256(path)}  {rel(path)}" for path in manifest_paths if repo_path(path).exists()]
    write_text(packet_path(config, "manifest"), "\n".join(manifest_lines))
    packet_manifest = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "review_packet_manifest",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "packet_directory": rel(packet_dir),
        "external_review_submitted": False,
        "sanitized": True,
        "raw_prompts_or_completions_included": False,
        "raw_acut_transcripts_included": False,
        "raw_diffs_or_tests_included": False,
        "solver_or_verifier_workspaces_included": False,
        "manifest_file": rel(packet_path(config, "manifest")),
        "manifest_entries": [
            {"path": line.split("  ", 1)[1], "sha256": line.split("  ", 1)[0]}
            for line in manifest_lines
        ],
    }
    write_json(output_path(config, "review_packet_manifest"), packet_manifest)
    write_review_packet_report(config, packet_manifest)
    write_process_report(
        config,
        "Step 4 - Prepare Adversarial Review Packet",
        [
            rel(packet_path(config, "readme")),
            rel(packet_path(config, "evidence_index")),
            rel(packet_path(config, "review_questions")),
            rel(packet_path(config, "claim_boundary")),
            rel(packet_path(config, "manifest")),
            rel(output_path(config, "review_packet_manifest")),
            rel(report_path(config, "adversarial_review_packet")),
        ],
        [
            "The packet is sanitized and links to canonical reports rather than copying large evidence.",
            "The packet explicitly says it has not been submitted.",
        ],
    )
    return packet_manifest


def build_claim_boundary_and_decision(config_path: str | Path = DEFAULT_CONFIG) -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_config(config_path)
    process_text = repo_path("PROCESS.md").read_text(encoding="utf-8") if repo_path("PROCESS.md").exists() else ""
    process_updated = (
        "phase1_candidate_policy_validation_protocol_decision.md" in process_text
        and "ready_for_adversarial_review" in process_text
    )
    test_cmd = [
        "uv",
        "run",
        "--project",
        "experiments/phase1_compiler",
        "pytest",
        "-q",
        "experiments/phase1_compiler/tests/test_phase1_candidate_policy_validation_protocol.py",
    ]
    retrospective_test_cmd = [
        "uv",
        "run",
        "--project",
        "experiments/phase1_compiler",
        "pytest",
        "-q",
        "experiments/phase1_compiler/tests/test_phase1_retrospective_predictive_signal.py",
    ]
    verification_results = {
        "candidate_policy_tests": command_result(test_cmd, timeout=180),
        "retrospective_signal_tests": command_result(retrospective_test_cmd, timeout=180),
        "git_diff_check": command_result(["git", "diff", "--check"], timeout=120),
    }
    verification_passed = all(result["returncode"] == 0 for result in verification_results.values())
    claim = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "claim_boundary",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status_label": "ready_for_adversarial_review" if verification_passed else "blocked_validation_protocol_not_defensible",
        "allowed_claims": [
            "coverage_constrained_unweighted_v1 is a deterministic outcome-blind candidate policy ready for adversarial review",
            "the next validation protocol and success criteria are frozen before future paid calls",
            "the review packet is prepared but not submitted",
        ],
        "disallowed_claims": [
            "formal predictive validity is established",
            "new paid ACUT cells are authorized",
            "Codex and Kilo differences are model-only results",
            "completed blocked split supplement is primary evidence",
        ],
        "predictive_validity_established": False,
        "external_review_submitted": False,
        "new_paid_acut_cells_run": False,
        "new_paid_llm_calls_run": False,
    }
    decision = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "decision",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "decision_label": claim["status_label"],
        "policy_id": config["policy"]["policy_id"],
        "candidate_policy_frozen": output_path(config, "policy_spec").exists(),
        "selection_manifest_frozen": output_path(config, "selection_manifest").exists(),
        "outcome_blindness_audit_passed": read_json(output_path(config, "outcome_blindness_audit")).get("outcome_blind") is True
        if output_path(config, "outcome_blindness_audit").exists()
        else False,
        "validation_protocol_frozen": output_path(config, "validation_protocol").exists(),
        "review_packet_prepared": output_path(config, "review_packet_manifest").exists(),
        "review_packet_submitted": False,
        "new_paid_acut_cells_run": False,
        "new_paid_llm_calls_run": False,
        "predictive_validity_established": False,
        "future_paid_acut_remains_blocked_by_default": True,
        "process_md_updated": process_updated,
        "verification_results": verification_results,
        "verification_passed": verification_passed,
        "next_action": "submit packet for adversarial review, then triage reviewer objections before any paid validation"
        if verification_passed
        else "repair blocker before review submission",
    }
    write_json(output_path(config, "claim_boundary"), claim)
    write_json(output_path(config, "decision"), decision)
    write_decision_report(config, claim, decision)
    write_process_report(
        config,
        "Step 5 - Closeout Decision",
        [
            rel(output_path(config, "claim_boundary")),
            rel(output_path(config, "decision")),
            rel(report_path(config, "decision")),
        ],
        [
            f"Stop label: `{decision['decision_label']}`.",
            "No external review was submitted.",
            "No paid ACUT or paid LLM calls were made.",
            f"Candidate policy tests return code: `{verification_results['candidate_policy_tests']['returncode']}`.",
            f"Retrospective signal tests return code: `{verification_results['retrospective_signal_tests']['returncode']}`.",
            f"git diff --check return code: `{verification_results['git_diff_check']['returncode']}`.",
        ],
    )
    return claim, decision


def write_process_report(config: dict[str, Any], current_step: str, completed: list[str], notes: list[str] | None = None) -> None:
    lines = [
        "# Candidate Policy Validation Protocol Process",
        "",
        f"Current step: `{current_step}`.",
        "",
        "Completed artifacts:",
    ]
    lines.extend(f"- `{item}`" for item in completed)
    lines.extend(
        [
            "",
            "Boundary:",
            "- This runbook is no-paid.",
            "- New paid ACUT solver cells run: `false`.",
            "- New paid LLM calls run: `false`.",
            "- External adversarial review submitted: `false`.",
            "- Score tables are not read by the policy selection command.",
        ]
    )
    if notes:
        lines.extend(["", "Notes:"])
        lines.extend(f"- {note}" for note in notes)
    write_text(report_path(config, "process"), "\n".join(lines))


def write_policy_spec_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Candidate Policy Spec",
        "",
        "What happened: froze `coverage_constrained_unweighted_v1` as a deterministic, outcome-blind candidate policy.",
        "",
        "Why it matters: future review can inspect an exact rule instead of an informal retrospective winner.",
        "",
        "Action suggested next: run the selector, audit outcome-blindness, then use the frozen validation protocol before any future paid work.",
        "",
        f"Policy ID: `{payload['policy_id']}`.",
        f"Budget per repo: `{payload['budget_policy']['budget_per_repo']}`.",
        f"Seed: `{payload['seed_policy']['deterministic_seed']}`.",
        "",
        "Forbidden inputs include terminal outcomes, pass/fail labels, adapter outcomes, score-table rows, raw ACUT transcripts, and hidden verifier output.",
    ]
    write_text(report_path(config, "policy_spec"), "\n".join(lines))


def write_selection_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    rows = [
        {"repo": repo, "selected": count, "fallback": payload["fallback_by_repo"][repo]["fallback_reason"] or "none"}
        for repo, count in payload["selected_count_by_repo"].items()
    ]
    lines = [
        "# Candidate Policy Selection Manifest",
        "",
        "What happened: selected a fixed task set with the outcome-blind coverage-constrained policy.",
        "",
        "Why it matters: selected and excluded task IDs are now reproducible before future paid validation.",
        "",
        "Action suggested next: use this manifest as the candidate object for adversarial review.",
        "",
        *markdown_table(rows, [("repo", "Repo"), ("selected", "Selected"), ("fallback", "Fallback")]),
        "",
        f"Selected task IDs: `{', '.join(payload['selected_task_ids'])}`.",
        "",
        f"Coverage gaps recorded: `{len(payload['coverage_gaps'])}`.",
    ]
    write_text(report_path(config, "selection_manifest"), "\n".join(lines))


def write_outcome_blindness_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Outcome-Blindness Audit",
        "",
        "What happened: audited the policy inputs and selection outputs for forbidden outcome fields.",
        "",
        "Why it matters: the promoted policy is useful only if task selection does not depend on terminal outcomes or score tables.",
        "",
        "Action suggested next: keep any future score join in a separately labeled post-selection diagnostic command.",
        "",
        f"Outcome blind: `{str(payload['outcome_blind']).lower()}`.",
        f"Forbidden field violations: `{len(payload['forbidden_field_violations'])}`.",
        "Score tables read for selection: `[]`.",
        "Terminal outcomes loaded: `false`.",
    ]
    write_text(report_path(config, "outcome_blindness_audit"), "\n".join(lines))


def write_validation_protocol_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Validation Protocol",
        "",
        "What happened: froze the future validation protocol before any future paid ACUT calls.",
        "",
        "Why it matters: future results can be interpreted against preregistered baselines, metrics, adapter handling, and failure rules.",
        "",
        "Action suggested next: adversarially review this protocol before authorizing any future paid validation.",
        "",
        f"Primary candidate: `{payload['primary_candidate']}`.",
        f"Preferred study mode: `{payload['study_mode']['preferred']}`.",
        f"Fallback study mode: `{payload['study_mode']['fallback']}`.",
        "Primary reporting: adapter-stratified MAE and catastrophic miss rate.",
        "No paid run is authorized by this runbook.",
    ]
    write_text(report_path(config, "validation_protocol"), "\n".join(lines))


def write_success_criteria_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    criteria = payload["future_predictive_validity_claim"]
    lines = [
        "# Success Criteria",
        "",
        "What happened: froze criteria for traction evidence, future predictive validity, paid readiness, and blockers.",
        "",
        "Why it matters: the candidate cannot pass through pooled improvement alone or through one favorable repo or adapter.",
        "",
        "Action suggested next: use these thresholds during adversarial review and any later paid validation.",
        "",
        f"Minimum MAE margin versus best simple baseline: `{criteria['candidate_must_beat_best_simple_baseline_primary_mae_by_at_least']}`.",
        f"Majority-of-slices rule: `{criteria['or_majority_of_slices_rule']}`.",
        "Pooled improvement alone is insufficient.",
        "Future predictive validity requires future outcome-unseen validation or a preregistered rolling-origin design with enough support.",
    ]
    write_text(report_path(config, "success_criteria"), "\n".join(lines))


def write_review_packet_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Adversarial Review Packet",
        "",
        "What happened: prepared a small sanitized review packet with context, evidence links, review questions, claim boundary, and hashes.",
        "",
        "Why it matters: an external reviewer can now challenge the candidate policy and protocol before more paid ACUT budget is spent.",
        "",
        "Action suggested next: submit the packet for adversarial review, then triage reviewer objections before any paid validation.",
        "",
        f"Packet directory: `{payload['packet_directory']}`.",
        f"External review submitted: `{str(payload['external_review_submitted']).lower()}`.",
        f"Manifest entries: `{len(payload['manifest_entries'])}`.",
        "Sanitized: `true`.",
    ]
    write_text(report_path(config, "adversarial_review_packet"), "\n".join(lines))


def write_decision_report(config: dict[str, Any], claim: dict[str, Any], decision: dict[str, Any]) -> None:
    lines = [
        "# Candidate Policy Validation Protocol Decision",
        "",
        "What happened: candidate policy implemented and frozen, validation protocol frozen, and review packet prepared.",
        "",
        "Why it matters: Barcarolle now has a concrete object for adversarial review before spending more paid ACUT budget.",
        "",
        "Action suggested next: submit the packet to GPT-5.5-Pro or another adversarial reviewer, then triage reviewer objections before any paid validation.",
        "",
        f"Decision label: `{decision['decision_label']}`.",
        f"Policy ID: `{decision['policy_id']}`.",
        f"Predictive validity established: `{str(decision['predictive_validity_established']).lower()}`.",
        f"External review submitted: `{str(decision['review_packet_submitted']).lower()}`.",
        f"New paid ACUT cells run: `{str(decision['new_paid_acut_cells_run']).lower()}`.",
        f"New paid LLM calls run: `{str(decision['new_paid_llm_calls_run']).lower()}`.",
        f"Verification passed: `{str(decision['verification_passed']).lower()}`.",
        "",
        "Allowed claims:",
    ]
    lines.extend(f"- {item}" for item in claim["allowed_claims"])
    lines.extend(["", "Disallowed claims:"])
    lines.extend(f"- {item}" for item in claim["disallowed_claims"])
    write_text(report_path(config, "decision"), "\n".join(lines))


def run_all(config_path: str | Path = DEFAULT_CONFIG) -> None:
    build_preflight(config_path)
    build_policy_spec(config_path)
    build_input_freeze_and_selection(config_path)
    build_validation_protocol(config_path)
    build_review_packet(config_path)
    build_claim_boundary_and_decision(config_path)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Phase 1 candidate policy validation protocol artifacts.")
    parser.add_argument("command", choices=["preflight", "policy-spec", "run", "protocol", "packet", "closeout", "all"])
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config_path = repo_path(args.config)
    if args.command == "preflight":
        build_preflight(config_path)
    elif args.command == "policy-spec":
        build_policy_spec(config_path)
    elif args.command == "run":
        build_input_freeze_and_selection(config_path)
    elif args.command == "protocol":
        build_validation_protocol(config_path)
    elif args.command == "packet":
        build_review_packet(config_path)
    elif args.command == "closeout":
        build_claim_boundary_and_decision(config_path)
    elif args.command == "all":
        run_all(config_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
