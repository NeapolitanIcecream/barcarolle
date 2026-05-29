from __future__ import annotations

import argparse
import csv
import glob
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "phase1_blocked_split_paid_validation_design_review.yaml"
SCHEMA_VERSION = "barcarolle.phase1_blocked_split_paid_validation_design_review.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_blocked_split_paid_validation_design_review_output.v1"
RUN_ID = "phase1_blocked_split_paid_validation_design_review_20260529"


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
        raise ValueError("unexpected blocked split paid validation design review schema_version")
    config["_path"] = str(path)
    return config


def input_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["inputs"][key])


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


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


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with repo_path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for line in repo_path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def bool_from_csv(raw: Any) -> bool:
    return str(raw).strip().lower() == "true"


def repo_from_task_id(task_id: str) -> str:
    return task_id.split("__", 1)[0] if "__" in task_id else "unknown"


def adapters(config: dict[str, Any]) -> list[str]:
    return [str(adapter) for adapter in config["adapters"]]


def repos(config: dict[str, Any]) -> list[str]:
    return [str(repo) for repo in config["repos"]]


def splits(config: dict[str, Any]) -> list[str]:
    return [str(split) for split in config["splits"]]


def load_selected_candidates(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    selected = read_json(input_path(config, "blocked_split_selected_split"))
    candidates = {str(candidate["budget_id"]): candidate for candidate in selected["selected_candidates"]}
    required = {config["primary_budget_id"], config["secondary_budget_id"]}
    missing = required - set(candidates)
    if missing:
        raise ValueError(f"selected split missing budgets: {sorted(missing)}")
    return candidates


def selected_task_entries(config: dict[str, Any], candidate: dict[str, Any]) -> list[dict[str, str]]:
    entries = []
    for split in splits(config):
        for task_id in candidate[f"{split}_task_ids"]:
            entries.append(
                {
                    "task_id": str(task_id),
                    "repo": repo_from_task_id(str(task_id)),
                    "split": split,
                }
            )
    return sorted(entries, key=lambda row: (repos(config).index(row["repo"]), row["split"], row["task_id"]))


def load_score_table_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    manifest = read_json(input_path(config, "score_tables_manifest"))
    manifest_paths = [str(entry["score_table"]) for entry in manifest.get("entries", [])]
    glob_paths = [rel(path) for path in sorted(glob.glob(str(input_path(config, "score_tables_glob"))))]
    score_table_paths = sorted(set(manifest_paths) | set(glob_paths))
    rows = []
    for score_table in score_table_paths:
        resolved = repo_path(score_table)
        if not resolved.exists():
            raise FileNotFoundError(score_table)
        for row in read_csv(resolved):
            rows.append(
                {
                    "adapter_id": str(row["adapter_id"]),
                    "task_id": str(row["task_id"]),
                    "repo": repo_from_task_id(str(row["task_id"])),
                    "prior_paid_split": str(row.get("split") or ""),
                    "terminal_status": str(row.get("terminal_status") or ""),
                    "scoreable_cell": bool_from_csv(row.get("scoreable_cell")),
                    "submission_status": str(row.get("submission_status") or ""),
                    "result_prefix": resolved.name.removesuffix("_score_table.csv"),
                    "score_table": rel(resolved),
                }
            )
    return rows


def completed_cell_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    duplicates = []
    for row in rows:
        key = (str(row["task_id"]), str(row["adapter_id"]))
        if key in index:
            duplicates.append(key)
        index[key] = row
    if duplicates:
        raise ValueError(f"duplicate paid score-table cells: {duplicates[:5]}")
    return index


def empty_repo_split_adapter_counts(config: dict[str, Any]) -> dict[str, dict[str, dict[str, int]]]:
    return {
        repo: {split: {adapter: 0 for adapter in adapters(config)} for split in splits(config)}
        for repo in repos(config)
    }


def source_counts(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(cell["score_table"]) for cell in cells)
    result_prefix_by_path = {str(cell["score_table"]): str(cell["result_prefix"]) for cell in cells}
    return [
        {
            "score_table": path,
            "result_prefix": result_prefix_by_path[path],
            "known_cell_count": count,
        }
        for path, count in sorted(counts.items())
    ]


def summarize_candidate_overlap(
    config: dict[str, Any],
    candidate: dict[str, Any],
    completed: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    task_entries = selected_task_entries(config, candidate)
    selected_task_ids = [entry["task_id"] for entry in task_entries]
    selected_by_task = {entry["task_id"]: entry for entry in task_entries}
    known_cells = []
    missing_cells = []
    known_by_adapter: Counter[str] = Counter()
    missing_by_adapter: Counter[str] = Counter()
    known_by_repo_split_adapter = empty_repo_split_adapter_counts(config)
    missing_by_repo_split_adapter = empty_repo_split_adapter_counts(config)

    for entry in task_entries:
        for adapter in adapters(config):
            key = (entry["task_id"], adapter)
            row = completed.get(key)
            if row is None:
                cell = {
                    "task_id": entry["task_id"],
                    "repo": entry["repo"],
                    "split": entry["split"],
                    "adapter_id": adapter,
                }
                missing_cells.append(cell)
                missing_by_adapter[adapter] += 1
                missing_by_repo_split_adapter[entry["repo"]][entry["split"]][adapter] += 1
                continue
            cell = {
                "task_id": entry["task_id"],
                "repo": entry["repo"],
                "split": entry["split"],
                "adapter_id": adapter,
                "terminal_status": row["terminal_status"],
                "scoreable_cell": row["scoreable_cell"],
                "submission_status": row["submission_status"],
                "prior_paid_split": row["prior_paid_split"],
                "result_prefix": row["result_prefix"],
                "score_table": row["score_table"],
            }
            known_cells.append(cell)
            known_by_adapter[adapter] += 1
            known_by_repo_split_adapter[entry["repo"]][entry["split"]][adapter] += 1

    tasks_with_known = {cell["task_id"] for cell in known_cells}
    tasks_with_missing = {cell["task_id"] for cell in missing_cells}
    missing_tasks = [task_id for task_id in selected_task_ids if task_id not in tasks_with_known]
    known_tasks = [task_id for task_id in selected_task_ids if task_id in tasks_with_known]
    partial_tasks = sorted(tasks_with_known & tasks_with_missing)
    split_labels = {
        split: [entry["task_id"] for entry in task_entries if entry["split"] == split]
        for split in splits(config)
    }

    return {
        "design_id": str(candidate["design_id"]),
        "budget_id": str(candidate["budget_id"]),
        "selected_tasks": len(task_entries),
        "selected_task_ids": selected_task_ids,
        "split_labels": split_labels,
        "selected_cells": len(task_entries) * len(adapters(config)),
        "selected_cells_by_adapter": {adapter: len(task_entries) for adapter in adapters(config)},
        "known_cells": len(known_cells),
        "missing_cells": len(missing_cells),
        "known_cells_by_adapter": {adapter: known_by_adapter.get(adapter, 0) for adapter in adapters(config)},
        "missing_cells_by_adapter": {adapter: missing_by_adapter.get(adapter, 0) for adapter in adapters(config)},
        "known_tasks": len(known_tasks),
        "known_task_ids": known_tasks,
        "missing_tasks": len(missing_tasks),
        "missing_task_ids": missing_tasks,
        "tasks_requiring_any_new_paid_run": sorted(tasks_with_missing),
        "partial_task_ids": partial_tasks,
        "known_cells_by_repo_split_adapter": known_by_repo_split_adapter,
        "missing_cells_by_repo_split_adapter": missing_by_repo_split_adapter,
        "cells_safe_to_reuse": sorted(
            known_cells,
            key=lambda cell: (cell["repo"], cell["split"], cell["task_id"], cell["adapter_id"]),
        ),
        "cells_requiring_new_paid_run": sorted(
            missing_cells,
            key=lambda cell: (cell["repo"], cell["split"], cell["task_id"], cell["adapter_id"]),
        ),
        "reused_cell_score_table_sources": source_counts(known_cells),
        "missing_cell_manifest": sorted(
            missing_cells,
            key=lambda cell: (cell["repo"], cell["split"], cell["task_id"], cell["adapter_id"]),
        ),
        "no_missing_outcomes_imputed": True,
        "selected_split_by_task": selected_by_task,
    }


def build_overlap_payloads(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    completed = completed_cell_index(load_score_table_rows(config))
    candidates = load_selected_candidates(config)
    overlap_by_budget = {
        budget_id: summarize_candidate_overlap(config, candidate, completed)
        for budget_id, candidate in sorted(candidates.items())
    }
    overlap = {
        "artifact": "overlap_matrix",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "source_run_id": config["source_run_id"],
        "paid_validation_run_id": config["paid_validation_run_id"],
        "primary_budget_id": config["primary_budget_id"],
        "secondary_budget_id": config["secondary_budget_id"],
        "paid_calls_made_by_this_run": 0,
        "completed_paid_decision_changed": False,
        "selected_blocked_split_changed": False,
        "missing_outcomes_imputed": False,
        "splits": overlap_by_budget,
    }
    missing = {
        "artifact": "missing_cells",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": config["run_id"],
        "generated_at": overlap["generated_at"],
        "paid_calls_made_by_this_run": 0,
        "missing_outcomes_imputed": False,
        "split_missing_cells": {
            budget_id: {
                "design_id": summary["design_id"],
                "budget_id": budget_id,
                "missing_tasks": summary["missing_tasks"],
                "missing_task_ids": summary["missing_task_ids"],
                "missing_cells": summary["missing_cells"],
                "missing_cells_by_adapter": summary["missing_cells_by_adapter"],
                "missing_cells_by_repo_split_adapter": summary["missing_cells_by_repo_split_adapter"],
                "missing_cell_manifest": summary["missing_cell_manifest"],
            }
            for budget_id, summary in overlap_by_budget.items()
        },
    }
    return overlap, missing


def render_overlap_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Blocked Split Paid Outcome Overlap",
        "",
        "Status: `complete`.",
        "",
        "## What Happened",
        "",
        "The frozen blocked split was compared against committed three-repo paid score tables at the task/adapter-cell level.",
        "",
        "## Why It Matters",
        "",
        "Known outcomes cover only part of the selected blocked split. Missing outcomes are not imputed, so any complete selected score table needs new paid cells or a full rerun.",
        "",
        "## What Action It Suggests Next",
        "",
        "Use the exact missing-cell manifest to compare retrospective-only, missing-cell supplement, and full-rerun protocols.",
        "",
        "## Summary",
        "",
    ]
    for budget_id in (payload["primary_budget_id"], payload["secondary_budget_id"]):
        summary = payload["splits"][budget_id]
        lines.extend(
            [
                f"### `{budget_id}`",
                "",
                f"- Selected tasks: `{summary['selected_tasks']}`.",
                f"- Selected cells: `{summary['selected_cells']}`.",
                f"- Known tasks with at least one paid outcome: `{summary['known_tasks']}`.",
                f"- Tasks with no completed paid outcome: `{summary['missing_tasks']}`.",
                f"- Known cells by adapter: `{summary['known_cells_by_adapter']}`.",
                f"- Missing cells by adapter: `{summary['missing_cells_by_adapter']}`.",
                f"- Reused score-table sources: `{len(summary['reused_cell_score_table_sources'])}`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "No paid calls were made. Existing outcomes are used only for exploratory overlap accounting and provenance, not to alter the selected split or claim predictive validity.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_overlap_artifacts(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    overlap, missing = build_overlap_payloads(config)
    write_json(output_path(config, "overlap_matrix"), overlap)
    write_json(output_path(config, "missing_cells"), missing)
    write_text(report_path(config, "overlap_matrix"), render_overlap_report(overlap))
    return overlap, missing


def validate_claim_policy(config: dict[str, Any]) -> dict[str, Any]:
    policy = config["claim_policy"]
    checks = {
        "exploratory_status_explicit": policy.get("phase_status") == "exploratory",
        "post_hoc_allowed_only_for_exploration": (
            policy.get("post_hoc_design_allowed_for_exploration") is True
            and policy.get("formal_preregistration_claim_allowed") is False
        ),
        "predictive_validity_not_claimed": policy.get("predictive_validity_established") is False,
        "existing_outcomes_not_formal_preregistration": (
            policy.get("existing_outcomes_reusable_for_exploratory_accounting") is True
            and policy.get("existing_outcomes_reusable_for_formal_preregistration") is False
        ),
        "click_minor_risk_visible": policy.get("click_minor_risk_must_be_reported") is True,
        "adapter_reporting_first": policy.get("adapter_stratified_reporting_required") is True,
        "paid_outcomes_do_not_mutate_split": policy.get("use_paid_outcomes_to_alter_selected_split") is False,
        "provider_bill_exact_cost_guard_present": (
            policy.get("provider_billed_exact_cost_requires_actual_provider_billed_cost") is True
        ),
    }
    return {"valid": all(checks.values()), "checks": checks}


def build_protocol_options(config: dict[str, Any], overlap: dict[str, Any] | None = None) -> dict[str, Any]:
    overlap = overlap or read_json(output_path(config, "overlap_matrix"))
    policy_validation = validate_claim_policy(config)
    primary = overlap["splits"][config["primary_budget_id"]]
    secondary = overlap["splits"][config["secondary_budget_id"]]

    def adapter_counts(counts: dict[str, int], default: int = 0) -> dict[str, int]:
        return {adapter: int(counts.get(adapter, default)) for adapter in adapters(config)}

    options = [
        {
            "option_id": "A",
            "protocol_name": "retrospective_only_no_new_paid_cells",
            "target_budget_id": config["primary_budget_id"],
            "target_split_id": primary["design_id"],
            "new_paid_cell_count": 0,
            "new_paid_cell_count_by_adapter": {adapter: 0 for adapter in adapters(config)},
            "reused_cell_count": primary["known_cells"],
            "reused_cell_count_by_adapter": adapter_counts(primary["known_cells_by_adapter"]),
            "total_scoreable_cell_count_after_protocol": primary["known_cells"],
            "adapter_reporting_mode": "adapter_stratified_before_pooled",
            "claim_boundary": "retrospective_sanity_check_only",
            "pros": ["free", "fast", "uses only completed committed outcomes"],
            "cons": ["incomplete outcome coverage", "not new validation evidence"],
            "click_minor_risk_status": "visible_title_only_minor_risk",
            "provider_bill_status": "provider_billed_exact_cost_unavailable_without_actual_provider_billed_cost_usd",
            "recommendation_status": "not_recommended",
            "predictive_validity_claim_allowed": False,
        },
        {
            "option_id": "B",
            "protocol_name": "same_budget_missing_cell_supplement",
            "target_budget_id": config["primary_budget_id"],
            "target_split_id": primary["design_id"],
            "new_paid_cell_count": primary["missing_cells"],
            "new_paid_cell_count_by_adapter": adapter_counts(primary["missing_cells_by_adapter"]),
            "reused_cell_count": primary["known_cells"],
            "reused_cell_count_by_adapter": adapter_counts(primary["known_cells_by_adapter"]),
            "total_scoreable_cell_count_after_protocol": primary["selected_cells"],
            "adapter_reporting_mode": "adapter_stratified_before_pooled",
            "claim_boundary": "exploratory_supplemental_validation_for_post_hoc_blocked_split",
            "pros": ["cheaper than full rerun", "fills the selected same-budget score table"],
            "cons": ["mixes old and new outcomes", "still post-hoc and exploratory"],
            "click_minor_risk_status": "visible_title_only_minor_risk",
            "provider_bill_status": "provider_billed_exact_cost_unavailable_without_actual_provider_billed_cost_usd",
            "recommendation_status": "recommended",
            "predictive_validity_claim_allowed": False,
        },
        {
            "option_id": "C",
            "protocol_name": "same_budget_full_rerun",
            "target_budget_id": config["primary_budget_id"],
            "target_split_id": primary["design_id"],
            "new_paid_cell_count": primary["selected_cells"],
            "new_paid_cell_count_by_adapter": adapter_counts(primary["selected_cells_by_adapter"]),
            "reused_cell_count": 0,
            "reused_cell_count_by_adapter": {adapter: 0 for adapter in adapters(config)},
            "total_scoreable_cell_count_after_protocol": primary["selected_cells"],
            "adapter_reporting_mode": "adapter_stratified_before_pooled",
            "claim_boundary": "cleaner_exploratory_validation_after_blocked_split_freeze",
            "pros": ["one uniform run after design review"],
            "cons": ["higher cost than supplement", "still not formal pre-outcome design"],
            "click_minor_risk_status": "visible_title_only_minor_risk",
            "provider_bill_status": "provider_billed_exact_cost_unavailable_without_actual_provider_billed_cost_usd",
            "recommendation_status": "acceptable_secondary",
            "predictive_validity_claim_allowed": False,
        },
        {
            "option_id": "D",
            "protocol_name": "expanded_full_rerun",
            "target_budget_id": config["secondary_budget_id"],
            "target_split_id": secondary["design_id"],
            "new_paid_cell_count": secondary["selected_cells"],
            "new_paid_cell_count_by_adapter": adapter_counts(secondary["selected_cells_by_adapter"]),
            "reused_cell_count": 0,
            "reused_cell_count_by_adapter": {adapter: 0 for adapter in adapters(config)},
            "total_scoreable_cell_count_after_protocol": secondary["selected_cells"],
            "adapter_reporting_mode": "adapter_stratified_before_pooled",
            "claim_boundary": "higher_coverage_exploratory_validation_after_blocked_split_freeze",
            "pros": ["more tasks", "better mechanical precision"],
            "cons": ["highest projected spend", "click risk remains", "still post-hoc"],
            "click_minor_risk_status": "visible_title_only_minor_risk",
            "provider_bill_status": "provider_billed_exact_cost_unavailable_without_actual_provider_billed_cost_usd",
            "recommendation_status": "acceptable_secondary",
            "predictive_validity_claim_allowed": False,
        },
        {
            "option_id": "E",
            "protocol_name": "stop_for_source_repair_or_third_repo_replacement",
            "target_budget_id": None,
            "target_split_id": None,
            "new_paid_cell_count": 0,
            "new_paid_cell_count_by_adapter": {adapter: 0 for adapter in adapters(config)},
            "reused_cell_count": 0,
            "reused_cell_count_by_adapter": {adapter: 0 for adapter in adapters(config)},
            "total_scoreable_cell_count_after_protocol": 0,
            "adapter_reporting_mode": "not_applicable_until_paid_validation_resumes",
            "claim_boundary": "no_paid_validation_until_click_risk_or_repo_mix_changes",
            "pros": ["cleaner source-quality basis"],
            "cons": ["delays validation", "requires more local source repair or replacement work"],
            "click_minor_risk_status": "treated_as_blocker_for_this_option",
            "provider_bill_status": "not_applicable",
            "recommendation_status": "not_recommended",
            "predictive_validity_claim_allowed": False,
        },
    ]
    return {
        "artifact": "protocol_options",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "claim_policy_valid": policy_validation["valid"],
        "policy_checks": policy_validation["checks"],
        "selected_recommended_option_id": "B",
        "paid_calls_made_by_this_run": 0,
        "predictive_validity_established": False,
        "options": options,
    }


def render_protocol_options_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Blocked Split Validation Protocol Options",
        "",
        "Status: `complete`.",
        "",
        "## What Happened",
        "",
        "Five validation protocols were compared under the exploratory claim policy.",
        "",
        "## Why It Matters",
        "",
        "The selected protocol controls what Barcarolle can honestly claim from reused and future paid cells.",
        "",
        "## What Action It Suggests Next",
        "",
        f"Recommended option: `{payload['selected_recommended_option_id']}`.",
        "",
        "## Options",
        "",
    ]
    for option in payload["options"]:
        lines.extend(
            [
                f"### Option {option['option_id']}: `{option['protocol_name']}`",
                "",
                f"- New paid cells: `{option['new_paid_cell_count']}`.",
                f"- Reused cells: `{option['reused_cell_count']}`.",
                f"- Total scoreable cells after protocol: `{option['total_scoreable_cell_count_after_protocol']}`.",
                f"- Claim boundary: `{option['claim_boundary']}`.",
                f"- Recommendation status: `{option['recommendation_status']}`.",
                f"- Click status: `{option['click_minor_risk_status']}`.",
                "",
            ]
        )
    lines.extend(
        [
            "No option claims predictive validity. Adapter-level reporting remains required before pooled summaries.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_protocol_option_artifacts(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_protocol_options(config)
    write_json(output_path(config, "protocol_options"), payload)
    write_text(report_path(config, "protocol_options"), render_protocol_options_report(payload))
    return payload


def load_cost_baselines(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    projection = read_json(input_path(config, "blocked_split_cost_power_projection"))
    baselines = projection["adapter_baselines"]
    missing = set(adapters(config)) - set(baselines)
    if missing:
        raise ValueError(f"missing cost baselines for adapters: {sorted(missing)}")
    return baselines


def build_cost_projection(config: dict[str, Any], options: dict[str, Any] | None = None) -> dict[str, Any]:
    options = options or read_json(output_path(config, "protocol_options"))
    baselines = load_cost_baselines(config)
    blocked_projection = read_json(input_path(config, "blocked_split_cost_power_projection"))
    option_costs = []
    for option in options["options"]:
        by_adapter = {}
        for adapter in adapters(config):
            baseline = baselines[adapter]
            per_cell = float(baseline["estimated_cost_per_cell_usd"])
            new_count = int(option["new_paid_cell_count_by_adapter"].get(adapter, 0))
            reused_count = int(option["reused_cell_count_by_adapter"].get(adapter, 0))
            new_cost = round(per_cell * new_count, 6)
            historical_cost = round(per_cell * reused_count, 6)
            by_adapter[adapter] = {
                "adapter_id": adapter,
                "new_paid_cell_count": new_count,
                "reused_cell_count": reused_count,
                "estimated_cost_per_cell_usd": per_cell,
                "token_estimated_new_cost_usd": new_cost,
                "token_estimated_historical_reused_cost_usd": historical_cost,
                "token_estimated_total_historical_plus_new_cost_usd": round(new_cost + historical_cost, 6),
                "median_latency_seconds": baseline.get("median_latency_seconds"),
                "provider_billed_cost_status": baseline.get("provider_billed_cost_status"),
                "actual_provider_billed_cost_usd": baseline.get("actual_provider_billed_cost_usd"),
                "cost_basis": "token_estimated_from_committed_prior_cost_summary",
            }
        option_costs.append(
            {
                "option_id": option["option_id"],
                "protocol_name": option["protocol_name"],
                "target_budget_id": option["target_budget_id"],
                "new_paid_cell_count": option["new_paid_cell_count"],
                "reused_cell_count": option["reused_cell_count"],
                "cost_basis": "token_estimated_from_committed_cost_power_projection",
                "provider_billed_exact_cost_available": any(
                    item["actual_provider_billed_cost_usd"] is not None for item in by_adapter.values()
                ),
                "by_adapter": by_adapter,
                "total_token_estimated_new_cost_usd": round(
                    sum(item["token_estimated_new_cost_usd"] for item in by_adapter.values()), 6
                ),
                "total_token_estimated_historical_reused_cost_usd": round(
                    sum(item["token_estimated_historical_reused_cost_usd"] for item in by_adapter.values()), 6
                ),
                "total_token_estimated_historical_plus_new_cost_usd": round(
                    sum(item["token_estimated_total_historical_plus_new_cost_usd"] for item in by_adapter.values()), 6
                ),
            }
        )

    by_option = {option["option_id"]: option for option in option_costs}
    same_budget_expected = blocked_projection["budget_projections"][config["primary_budget_id"]][
        "total_token_estimated_cost_usd"
    ]
    expanded_expected = blocked_projection["budget_projections"][config["secondary_budget_id"]][
        "total_token_estimated_cost_usd"
    ]
    return {
        "artifact": "cost_projection",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "paid_calls_made_by_this_run": 0,
        "provider_billed_exact_cost_available": False,
        "actual_provider_billed_cost_usd": None,
        "cost_basis": "token_estimated_from_committed_cost_summaries_and_usage_ledger",
        "adapter_baseline_source": rel(input_path(config, "blocked_split_cost_power_projection")),
        "options": option_costs,
        "full_rerun_cost_reconciliation": {
            "same_budget_20_per_repo": {
                "blocked_split_projection_total_usd": same_budget_expected,
                "design_review_option_C_total_usd": by_option["C"]["total_token_estimated_new_cost_usd"],
                "difference_usd": round(by_option["C"]["total_token_estimated_new_cost_usd"] - same_budget_expected, 6),
            },
            "expanded_30_per_repo": {
                "blocked_split_projection_total_usd": expanded_expected,
                "design_review_option_D_total_usd": by_option["D"]["total_token_estimated_new_cost_usd"],
                "difference_usd": round(by_option["D"]["total_token_estimated_new_cost_usd"] - expanded_expected, 6),
            },
        },
    }


def render_cost_projection_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Blocked Split Validation Cost Projection",
        "",
        "Status: `complete`.",
        "",
        "## What Happened",
        "",
        "Projected cost and latency were computed from committed prior token-cost summaries and usage-ledger-derived baselines. No provider billing API was called.",
        "",
        "## Why It Matters",
        "",
        "The missing-cell supplement is cheaper than full rerun, but all cost numbers remain token-estimated rather than exact provider-billed cost.",
        "",
        "## What Action It Suggests Next",
        "",
        "If the coordinator authorizes paid work, use adapter-specific new-cell counts and keep provider-billed cost status explicit.",
        "",
        "## Options",
        "",
    ]
    for option in payload["options"]:
        lines.extend(
            [
                f"### Option {option['option_id']}: `{option['protocol_name']}`",
                "",
                f"- New paid cells: `{option['new_paid_cell_count']}`.",
                f"- Reused cells: `{option['reused_cell_count']}`.",
                f"- Token-estimated new cost: `${option['total_token_estimated_new_cost_usd']}`.",
                f"- Token-estimated historical reused cost: `${option['total_token_estimated_historical_reused_cost_usd']}`.",
                f"- Provider-billed exact cost available: `{option['provider_billed_exact_cost_available']}`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Reconciliation",
            "",
            f"- Same-budget full rerun difference from blocked projection: `${payload['full_rerun_cost_reconciliation']['same_budget_20_per_repo']['difference_usd']}`.",
            f"- Expanded full rerun difference from blocked projection: `${payload['full_rerun_cost_reconciliation']['expanded_30_per_repo']['difference_usd']}`.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_cost_projection_artifacts(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_cost_projection(config)
    write_json(output_path(config, "cost_projection"), payload)
    write_text(report_path(config, "cost_projection"), render_cost_projection_report(payload))
    return payload


def build_reuse_policy_and_ready_package(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    overlap = read_json(output_path(config, "overlap_matrix"))
    options = read_json(output_path(config, "protocol_options"))
    costs = read_json(output_path(config, "cost_projection"))
    recommended = next(option for option in options["options"] if option["recommendation_status"] == "recommended")
    primary = overlap["splits"][config["primary_budget_id"]]
    option_cost = next(option for option in costs["options"] if option["option_id"] == recommended["option_id"])
    full_rerun_cost = next(option for option in costs["options"] if option["option_id"] == "C")
    reuse_policy = {
        "artifact": "reuse_policy",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "selected_protocol_option": recommended["option_id"],
        "selected_protocol_name": recommended["protocol_name"],
        "existing_outcomes_reusable_for_exploratory_accounting": True,
        "existing_outcomes_reusable_for_formal_preregistration": False,
        "missing_outcomes_imputed": False,
        "reuse_requires_score_table_provenance": True,
        "adapter_reporting_mode": "adapter_stratified_before_pooled",
        "known_reusable_cell_count": primary["known_cells"],
        "missing_paid_cell_count": primary["missing_cells"],
        "known_reusable_cell_count_by_adapter": primary["known_cells_by_adapter"],
        "missing_paid_cell_count_by_adapter": primary["missing_cells_by_adapter"],
        "full_rerun_is_cleaner_but_more_expensive": True,
        "full_rerun_token_estimated_new_cost_usd": full_rerun_cost["total_token_estimated_new_cost_usd"],
        "supplement_token_estimated_new_cost_usd": option_cost["total_token_estimated_new_cost_usd"],
        "claim_boundary": recommended["claim_boundary"],
        "paid_calls_made_by_this_run": 0,
    }
    ready_package = {
        "artifact": "ready_package",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": config["run_id"],
        "generated_at": reuse_policy["generated_at"],
        "status": "ready",
        "selected_protocol_option": recommended["option_id"],
        "selected_protocol_name": recommended["protocol_name"],
        "selected_split_id": primary["design_id"],
        "selected_budget_id": config["primary_budget_id"],
        "selected_task_ids": primary["selected_task_ids"],
        "split_labels": primary["split_labels"],
        "adapters": adapters(config),
        "known_reusable_cells": primary["cells_safe_to_reuse"],
        "missing_paid_cells_to_run": primary["cells_requiring_new_paid_run"],
        "endpoint_requirement": {
            "required_env_vars": ["LLM_BASE_URL", "LLM_API_KEY"],
            "fallback_to_other_llm_auth_allowed": False,
        },
        "adapter_reporting_policy": {
            "adapter_stratified_reporting_required": True,
            "pooled_summary_primary_allowed": False,
            "paired_disagreement_reporting_required_when_shared_tasks": True,
        },
        "claim_boundary": {
            "phase_status": "exploratory",
            "formal_preregistration_claim_allowed": False,
            "predictive_validity_established": False,
            "existing_outcomes_reused_only_for_exploratory_evidence": True,
        },
        "click_minor_risk_caveat": {
            "status": "visible_title_only_minor_risk",
            "accepted_as_caveat_for_recommended_option": True,
        },
        "cost_projection": {
            "token_estimated_new_cost_usd": option_cost["total_token_estimated_new_cost_usd"],
            "by_adapter": {
                adapter: {
                    "new_paid_cell_count": option_cost["by_adapter"][adapter]["new_paid_cell_count"],
                    "token_estimated_new_cost_usd": option_cost["by_adapter"][adapter][
                        "token_estimated_new_cost_usd"
                    ],
                }
                for adapter in adapters(config)
            },
            "provider_billed_exact_cost_available": False,
        },
        "stop_conditions": [
            "LLM_BASE_URL or LLM_API_KEY is unavailable in the worker shell",
            "the selected split ID, task IDs, or split labels differ from this package",
            "score-table provenance for reused cells cannot be verified from committed files",
            "the execution would edit task statements, source eligibility, or completed paid decisions",
            "provider-billed exact cost is claimed without actual_provider_billed_cost_usd",
        ],
        "paid_calls_made_by_this_run": 0,
        "completed_paid_decision_changed": False,
        "selected_blocked_split_changed": False,
        "followup_runbook_written_by_worker": False,
    }
    return reuse_policy, ready_package


def write_reuse_package_artifacts(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    reuse_policy, ready_package = build_reuse_policy_and_ready_package(config)
    write_json(output_path(config, "reuse_policy"), reuse_policy)
    write_json(output_path(config, "ready_package"), ready_package)
    return reuse_policy, ready_package


def build_decision(config: dict[str, Any], *, tests_passed: bool) -> dict[str, Any]:
    overlap = read_json(output_path(config, "overlap_matrix"))
    options = read_json(output_path(config, "protocol_options"))
    costs = read_json(output_path(config, "cost_projection"))
    ready_package = read_json(output_path(config, "ready_package"))
    primary = overlap["splits"][config["primary_budget_id"]]
    recommended = next(option for option in options["options"] if option["recommendation_status"] == "recommended")
    recommended_cost = next(option for option in costs["options"] if option["option_id"] == recommended["option_id"])
    gates = {
        "claim_policy_written_and_exploratory_status_explicit": validate_claim_policy(config)["valid"],
        "selected_blocked_split_unchanged": ready_package["selected_blocked_split_changed"] is False,
        "overlap_and_missing_cell_manifests_exact": primary["missing_outcomes_imputed"] is False
        if "missing_outcomes_imputed" in primary
        else True,
        "recommended_option_has_clear_reusable_missing_cell_handling": (
            recommended["reused_cell_count"] == primary["known_cells"]
            and recommended["new_paid_cell_count"] == primary["missing_cells"]
        ),
        "adapter_level_reporting_required": ready_package["adapter_reporting_policy"][
            "adapter_stratified_reporting_required"
        ]
        is True,
        "click_minor_risk_caveat_explicit": ready_package["click_minor_risk_caveat"]["status"]
        == "visible_title_only_minor_risk",
        "cost_projection_adapter_stratified_and_token_estimated": all(
            "by_adapter" in option and option["cost_basis"].startswith("token_estimated")
            for option in costs["options"]
        ),
        "paid_calls_made_by_this_run_zero": ready_package["paid_calls_made_by_this_run"] == 0,
        "completed_paid_decision_changed_false": ready_package["completed_paid_decision_changed"] is False,
        "predictive_validity_established_false": ready_package["claim_boundary"][
            "predictive_validity_established"
        ]
        is False,
        "tests_and_diff_check_passed": tests_passed,
    }
    readiness = all(gates.values())
    payload = {
        "artifact": "decision",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "decision_label": "recommend_missing_cell_supplement_exploratory",
        "ready_for_later_paid_execution_runbook": readiness,
        "readiness_gates": gates,
        "failed_readiness_gates": [key for key, value in gates.items() if value is not True],
        "recommended_protocol_option": recommended["option_id"],
        "recommended_protocol_name": recommended["protocol_name"],
        "recommended_next_action_category": "exploratory_missing_cell_supplement_paid_execution",
        "known_reusable_cells": primary["known_cells"],
        "missing_new_paid_cells": primary["missing_cells"],
        "known_reusable_cells_by_adapter": primary["known_cells_by_adapter"],
        "missing_new_paid_cells_by_adapter": primary["missing_cells_by_adapter"],
        "estimated_new_paid_cost_by_adapter_usd": {
            adapter: recommended_cost["by_adapter"][adapter]["token_estimated_new_cost_usd"]
            for adapter in adapters(config)
        },
        "estimated_new_paid_cost_total_usd": recommended_cost["total_token_estimated_new_cost_usd"],
        "provider_billed_exact_cost_available": False,
        "click_minor_risk_status": "accepted_caveat_visible_title_only_minor_risk",
        "paid_calls_made_by_this_run": 0,
        "completed_paid_decision_changed": False,
        "selected_blocked_split_changed": False,
        "predictive_validity_established": False,
        "followup_runbook_written_by_worker": False,
        "research_questions": {
            "RQ1_paid_pass_fail_incomplete": (
                f"The primary selected split has {primary['known_tasks']}/{primary['selected_tasks']} tasks "
                f"with at least one completed paid outcome and {primary['missing_tasks']} tasks with none; "
                f"that leaves {primary['missing_cells']} missing task/adapter cells."
            ),
            "RQ2_post_hoc_design_acceptable": "Yes, for Phase 1 exploration only.",
            "RQ3_claim_boundary": recommended["claim_boundary"],
            "RQ4_recommended_protocol": recommended["protocol_name"],
            "RQ5_reuse_and_new_cells": {
                "reusable_cells": primary["known_cells"],
                "new_cells_needed": primary["missing_cells"],
            },
            "RQ6_estimated_new_paid_cost": {
                "by_adapter_usd": {
                    adapter: recommended_cost["by_adapter"][adapter]["token_estimated_new_cost_usd"]
                    for adapter in adapters(config)
                },
                "total_usd": recommended_cost["total_token_estimated_new_cost_usd"],
            },
            "RQ7_click_minor_risk": "Accepted caveat for exploratory supplement; not hidden.",
            "RQ8_paid_calls_made": 0,
            "RQ9_completed_decisions_or_split_labels_changed": {
                "completed_paid_decision_changed": False,
                "selected_blocked_split_changed": False,
            },
            "RQ10_next_action_category": "exploratory_missing_cell_supplement_paid_execution",
        },
    }
    return payload


def render_decision_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Blocked Split Paid Validation Design Review Decision",
            "",
            "Status: `complete`.",
            "",
            "## What Happened",
            "",
            f"Decision label: `{payload['decision_label']}`.",
            f"Recommended protocol option: `{payload['recommended_protocol_option']}` (`{payload['recommended_protocol_name']}`).",
            f"Reusable cells: `{payload['known_reusable_cells']}`. Missing new paid cells: `{payload['missing_new_paid_cells']}`.",
            f"Estimated new paid cost: `${payload['estimated_new_paid_cost_total_usd']}` token-estimated.",
            "",
            "## Why It Matters",
            "",
            "The blocked split can be validated honestly as exploratory supplemental evidence by reusing committed outcomes with provenance and running only missing cells. It still cannot be described as a formal preregistered predictive-validity experiment.",
            "",
            "## What Action It Suggests Next",
            "",
            f"Coordinator action category: `{payload['recommended_next_action_category']}`.",
            "",
            "## Boundary",
            "",
            f"- Paid calls made by this run: `{payload['paid_calls_made_by_this_run']}`.",
            f"- Completed paid decision changed: `{payload['completed_paid_decision_changed']}`.",
            f"- Selected blocked split changed: `{payload['selected_blocked_split_changed']}`.",
            f"- Predictive validity established: `{payload['predictive_validity_established']}`.",
            f"- Click minor risk status: `{payload['click_minor_risk_status']}`.",
            f"- Follow-up runbook written by worker: `{payload['followup_runbook_written_by_worker']}`.",
            "",
            "## Readiness",
            "",
            f"- Ready for later paid execution runbook: `{payload['ready_for_later_paid_execution_runbook']}`.",
            f"- Failed readiness gates: `{payload['failed_readiness_gates']}`.",
        ]
    ) + "\n"


def write_decision_artifacts(config: dict[str, Any], *, tests_passed: bool) -> dict[str, Any]:
    payload = build_decision(config, tests_passed=tests_passed)
    write_json(output_path(config, "decision"), payload)
    write_text(report_path(config, "decision"), render_decision_report(payload))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate blocked split paid validation design review artifacts.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--tests-passed", action="store_true")
    parser.add_argument(
        "command",
        choices=["overlap", "protocol-options", "cost", "ready-package", "decision", "all"],
    )
    args = parser.parse_args(argv)

    config = load_config(args.config)
    if args.command in {"overlap", "all"}:
        write_overlap_artifacts(config)
    if args.command in {"protocol-options", "all"}:
        write_protocol_option_artifacts(config)
    if args.command in {"cost", "all"}:
        write_cost_projection_artifacts(config)
    if args.command in {"ready-package", "all"}:
        write_reuse_package_artifacts(config)
    if args.command in {"decision", "all"}:
        write_decision_artifacts(config, tests_passed=args.tests_passed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
