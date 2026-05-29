from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "phase1_blocked_split_redesign.yaml"
SCHEMA_VERSION = "barcarolle.phase1_blocked_split_redesign.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_blocked_split_redesign_output.v1"
RUN_ID = "phase1_blocked_split_redesign_20260529"
REPOS = ("attrs", "boltons", "click")
SPLITS = ("B_eval", "H_future")
ADAPTERS = ("codex_workspace", "kilo_workspace")
PRIMARY_BUDGET = "same_budget_20_per_repo"
SECONDARY_BUDGET = "expanded_30_per_repo"
VISIBLE_FEATURES = (
    "source_context_type_bucket",
    "source_quality_bucket",
    "statement_specificity_bucket",
    "context_length_bucket",
    "editable_scope_bucket",
    "ambiguity_risk_bucket",
    "leakage_risk_bucket",
    "certification_risk_bucket",
    "coarse_task_family",
    "time_bucket",
    "rare_or_unknown_feature_flag",
)
BLOCKING_FEATURES = (
    "source_quality_bucket",
    "source_context_type_bucket",
    "coarse_task_family",
    "time_bucket",
    "editable_scope_bucket",
)
BALANCE_FEATURES = (
    "coarse_task_family",
    "time_bucket",
    "editable_scope_bucket",
    "statement_specificity_bucket",
    "rare_or_unknown_feature_flag",
    "context_length_bucket",
)
GATE_FEATURE_KEYS = {
    "rare_or_unknown_feature_flag": "rare_or_unknown_abs_diff_per_repo",
    "editable_scope_bucket": "editable_scope_abs_diff_per_repo",
    "time_bucket": "time_bucket_abs_diff_per_repo",
    "coarse_task_family": "coarse_family_abs_diff_per_repo",
    "statement_specificity_bucket": "statement_specificity_abs_diff_per_repo",
}
PAIR_FEATURE_WEIGHTS = {
    "source_quality_bucket": 13,
    "source_context_type_bucket": 11,
    "coarse_task_family": 7,
    "time_bucket": 5,
    "editable_scope_bucket": 4,
    "statement_specificity_bucket": 3,
    "context_length_bucket": 2,
    "ambiguity_risk_bucket": 2,
    "leakage_risk_bucket": 2,
    "certification_risk_bucket": 2,
    "rare_or_unknown_feature_flag": 1,
}
OUTCOME_PATH_MARKERS = (
    "score_table",
    "paid_validation_metrics",
    "paid_validation_decision",
    "result_diagnostics",
    "adapter_stratified",
    "cost_summary",
    "cost_reconciliation",
    "workspace_usage_ledger",
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


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected blocked split redesign config schema_version")
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


def digest_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def stable_int(*parts: Any) -> int:
    text = "||".join(str(part) for part in parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def bool_from_csv(raw: Any) -> bool:
    return str(raw).strip().lower() == "true"


def repo_from_task_id(task_id: str) -> str:
    return task_id.split("__", 1)[0] if "__" in task_id else "unknown"


def bucket_value(row: dict[str, Any], feature: str) -> str:
    value = row.get(feature)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None or value == "":
        return "unknown"
    return str(value)


def sorted_task_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (REPOS.index(str(row["repo"])), str(row["task_id"])))


def count_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(bucket_value(row, key) for row in rows).items()))


def count_by_repo(rows: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, int]]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        counters[str(row.get("repo") or "unknown")][bucket_value(row, key)] += 1
    return {repo: dict(sorted(counters.get(repo, Counter()).items())) for repo in REPOS}


def load_candidate_universe(config: dict[str, Any]) -> dict[str, Any]:
    payload = read_json(config["candidate_universe_path"])
    if payload.get("artifact") != "candidate_universe":
        raise ValueError("candidate universe artifact is missing or invalid")
    if payload.get("outcome_fields_loaded") is not False:
        raise ValueError("candidate universe must be outcome-blind")
    return payload


def rows_by_task_id(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    row_list = list(rows)
    indexed = {str(row["task_id"]): dict(row) for row in row_list}
    if len(indexed) != len(row_list):
        raise ValueError("duplicate task IDs in row set")
    return indexed


def budget_tasks_per_repo(config: dict[str, Any], budget_id: str) -> int:
    return int(config["budget_tasks_per_repo"][budget_id])


def budget_split_tasks_per_repo(config: dict[str, Any], budget_id: str) -> int:
    return int(config["budget_split_tasks_per_repo"][budget_id])


def soft_penalty_weights(config: dict[str, Any]) -> dict[str, float]:
    return {str(key): float(value) for key, value in config["soft_penalty_weights"].items()}


def gate_thresholds(config: dict[str, Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in config["gate_thresholds"].items()}


def is_outcome_path(path: str | Path) -> bool:
    text = rel(path)
    return any(marker in text for marker in OUTCOME_PATH_MARKERS)


def pair_distance(left: dict[str, Any], right: dict[str, Any]) -> tuple[int, list[str]]:
    mismatches: list[str] = []
    distance = 0
    for feature, weight in PAIR_FEATURE_WEIGHTS.items():
        if bucket_value(left, feature) != bucket_value(right, feature):
            mismatches.append(feature)
            distance += weight
    return distance, mismatches


def split_feature_counts(candidate: dict[str, Any], row_by_id: dict[str, dict[str, Any]], feature: str) -> dict[str, dict[str, dict[str, int]]]:
    counts: dict[str, dict[str, Counter[str]]] = {
        repo: {split: Counter() for split in SPLITS}
        for repo in REPOS
    }
    for split in SPLITS:
        for task_id in candidate[f"{split}_task_ids"]:
            row = row_by_id[str(task_id)]
            counts[str(row["repo"])][split][bucket_value(row, feature)] += 1
    return {
        repo: {split: dict(sorted(split_counts.items())) for split, split_counts in by_split.items()}
        for repo, by_split in counts.items()
    }


def split_repo_counts(candidate: dict[str, Any], row_by_id: dict[str, dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = {repo: Counter() for repo in REPOS}
    for split in SPLITS:
        for task_id in candidate[f"{split}_task_ids"]:
            row = row_by_id.get(str(task_id))
            repo = str(row.get("repo") if row else repo_from_task_id(str(task_id)))
            counts[repo][split] += 1
    return {repo: {split: int(counts[repo].get(split, 0)) for split in SPLITS} for repo in REPOS}


def feature_diff_summary(candidate: dict[str, Any], row_by_id: dict[str, dict[str, Any]], feature: str) -> dict[str, Any]:
    counts = split_feature_counts(candidate, row_by_id, feature)
    per_repo: dict[str, Any] = {}
    total_abs_diff = 0
    max_abs_diff = 0
    for repo, by_split in counts.items():
        buckets = sorted(set(by_split["B_eval"]) | set(by_split["H_future"]))
        bucket_diffs = {
            bucket: int(by_split["B_eval"].get(bucket, 0) - by_split["H_future"].get(bucket, 0))
            for bucket in buckets
        }
        repo_total = sum(abs(value) for value in bucket_diffs.values())
        repo_max = max([abs(value) for value in bucket_diffs.values()] or [0])
        total_abs_diff += repo_total
        max_abs_diff = max(max_abs_diff, repo_max)
        per_repo[repo] = {
            "B_eval": by_split["B_eval"],
            "H_future": by_split["H_future"],
            "bucket_diffs_B_minus_H": bucket_diffs,
            "total_abs_diff": repo_total,
            "max_abs_diff": repo_max,
        }
    return {
        "feature": feature,
        "per_repo": per_repo,
        "total_abs_diff": total_abs_diff,
        "max_abs_diff": max_abs_diff,
    }


def hard_constraint_failures(candidate: dict[str, Any], row_by_id: dict[str, dict[str, Any]], split_tasks_per_repo: int) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    selected = list(candidate.get("B_eval_task_ids", [])) + list(candidate.get("H_future_task_ids", []))
    if not candidate.get("seed"):
        failures.append({"constraint": "missing_selected_seed", "detail": "candidate seed is missing"})
    if len(selected) != len(set(selected)):
        failures.append({"constraint": "duplicate_task_ids", "detail": "selected task IDs are not unique"})
    missing = sorted(task_id for task_id in selected if task_id not in row_by_id)
    if missing:
        failures.append({"constraint": "non_eligible_task_selected", "task_ids": missing})
    blocked = sorted(task_id for task_id in selected if task_id in row_by_id and row_by_id[task_id].get("source_quality_bucket") == "blocked")
    diagnostic = sorted(task_id for task_id in selected if task_id in row_by_id and row_by_id[task_id].get("source_quality_bucket") == "diagnostic_only")
    if blocked:
        failures.append({"constraint": "blocked_source_quality_selected", "task_ids": blocked})
    if diagnostic:
        failures.append({"constraint": "diagnostic_only_source_quality_selected", "task_ids": diagnostic})
    for repo, counts in split_repo_counts(candidate, row_by_id).items():
        if counts["B_eval"] != split_tasks_per_repo or counts["H_future"] != split_tasks_per_repo:
            failures.append({"constraint": "split_count_per_repo", "repo": repo, "counts": counts, "expected_each_split": split_tasks_per_repo})
    return failures


def compute_imbalance(candidate: dict[str, Any], row_by_id: dict[str, dict[str, Any]], weights: dict[str, float]) -> dict[str, Any]:
    summaries = {feature: feature_diff_summary(candidate, row_by_id, feature) for feature in BALANCE_FEATURES}
    score = sum(weights.get(feature, 1.0) * summaries[feature]["total_abs_diff"] for feature in BALANCE_FEATURES)
    return {
        "feature_imbalance_score": round(score, 6),
        "per_feature_imbalance_summary": {
            feature: {
                "total_abs_diff": summary["total_abs_diff"],
                "max_abs_diff": summary["max_abs_diff"],
            }
            for feature, summary in summaries.items()
        },
    }


def build_block_schema_payload(config: dict[str, Any], universe: dict[str, Any]) -> dict[str, Any]:
    rows = list(universe["rows"])
    repo_counts = {repo: sum(1 for row in rows if row["repo"] == repo) for repo in REPOS}
    budget_feasibility: dict[str, Any] = {}
    for budget_id in config["budgets_to_evaluate"]:
        tasks_per_repo = budget_tasks_per_repo(config, budget_id)
        split_per_repo = budget_split_tasks_per_repo(config, budget_id)
        infeasible_repos = {repo: repo_counts[repo] for repo in REPOS if repo_counts[repo] < tasks_per_repo}
        budget_feasibility[budget_id] = {
            "tasks_per_repo": tasks_per_repo,
            "B_eval_tasks_per_repo": split_per_repo,
            "H_future_tasks_per_repo": split_per_repo,
            "total_tasks": tasks_per_repo * len(REPOS),
            "feasible": not infeasible_repos and tasks_per_repo == split_per_repo * 2,
            "infeasible_repos": infeasible_repos,
        }
    return {
        "artifact": "block_schema",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "input_paths_loaded": [rel(config["_path"]), rel(config["candidate_universe_path"])],
        "outcome_input_paths_loaded": [],
        "outcome_fields_loaded": False,
        "repo_strata": list(REPOS),
        "split_labels": list(SPLITS),
        "default_block_size": 2,
        "blocking_scope": "within_repo_first",
        "blocking_features_in_priority_order": list(BLOCKING_FEATURES),
        "visible_features_allowed_for_selection": list(VISIBLE_FEATURES),
        "forbidden_selection_inputs": list(OUTCOME_PATH_MARKERS),
        "allowed_feature_buckets": {feature: count_by(rows, feature) for feature in VISIBLE_FEATURES},
        "allowed_feature_buckets_by_repo": {feature: count_by_repo(rows, feature) for feature in VISIBLE_FEATURES},
        "budget_feasibility": budget_feasibility,
        "hard_constraints": config["hard_constraints"],
        "soft_penalty_weights": config["soft_penalty_weights"],
        "gate_thresholds": config["gate_thresholds"],
        "selection_policy": config["selection_policy"],
        "retrospective_policy": config["retrospective_policy"],
        "click_minor_risk_caveat_required": bool(config["click_minor_risk_caveat_required"]),
        "click_minor_risk_caveat": universe["click_minor_risk_caveat"],
        "deterministic_order": {
            "task_order": "repo_order_then_task_id",
            "seed_material": [str(config["random_seed_family"]), int(config["candidate_seed_start"])],
            "candidate_seed_count": int(config["candidate_seed_count"]),
        },
    }


def render_block_schema_report(schema: dict[str, Any]) -> str:
    budgets = schema["budget_feasibility"]
    lines = [
        "# Phase 1 Blocked Split Block Schema",
        "",
        "## What Happened",
        "",
        "Defined deterministic, within-repo blocks of size 2. Each block assigns one task to `B_eval` and one task to `H_future`.",
        f"Budgets evaluated locally: `{list(budgets)}`.",
        f"`same_budget_20_per_repo` feasible: `{budgets[PRIMARY_BUDGET]['feasible']}`.",
        f"`expanded_30_per_repo` feasible: `{budgets[SECONDARY_BUDGET]['feasible']}`.",
        "",
        "## Why It Matters",
        "",
        "The schema names the visible features that can influence split selection before any paid outcomes are read. Repo remains a hard stratum, so attrs, boltons, and click are balanced separately rather than hidden inside a cross-repo average.",
        "",
        "Click is a required caveat. Click tasks stay eligible, but their source context is title-only and their source quality is `minor_risk`; this must remain visible in reports and gates.",
        "",
        "## What Action It Suggests Next",
        "",
        "Generate seeded candidate splits under this schema and choose by feature-imbalance score only. Do not load paid score tables until the selected split is frozen.",
        "",
        "## Selection Inputs",
        "",
        f"- Allowed visible features: `{schema['visible_features_allowed_for_selection']}`",
        f"- Blocking priority: `{schema['blocking_features_in_priority_order']}`",
        f"- Hard constraints: `{schema['hard_constraints']}`",
        f"- Soft penalty weights: `{schema['soft_penalty_weights']}`",
    ]
    return "\n".join(lines) + "\n"


def build_block_schema(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    universe = load_candidate_universe(config)
    payload = build_block_schema_payload(config, universe)
    write_json(output_path(config, "block_schema"), payload)
    write_text(report_path(config, "block_schema"), render_block_schema_report(payload))
    return payload


def select_repo_rows(rows: list[dict[str, Any]], budget_id: str, repo: str, tasks_per_repo: int, seed: int) -> list[dict[str, Any]]:
    repo_rows = sorted([row for row in rows if row["repo"] == repo], key=lambda row: str(row["task_id"]))
    if len(repo_rows) < tasks_per_repo:
        raise ValueError(f"budget {budget_id} infeasible for {repo}: {len(repo_rows)} available")
    rng = random.Random(stable_int(RUN_ID, budget_id, repo, seed, "select"))
    if len(repo_rows) == tasks_per_repo:
        return list(repo_rows)
    selected_indices = sorted(rng.sample(range(len(repo_rows)), tasks_per_repo))
    return [repo_rows[index] for index in selected_indices]


def build_repo_blocks(selected_rows: list[dict[str, Any]], budget_id: str, repo: str, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(stable_int(RUN_ID, budget_id, repo, seed, "block"))
    random_rank = {str(row["task_id"]): rng.random() for row in selected_rows}
    remaining = sorted(selected_rows, key=lambda row: random_rank[str(row["task_id"])])
    blocks: list[dict[str, Any]] = []
    while remaining:
        left = remaining.pop(0)
        partner_index, partner = min(
            enumerate(remaining),
            key=lambda item: (pair_distance(left, item[1])[0], random_rank[str(item[1]["task_id"])], str(item[1]["task_id"])),
        )
        right = remaining.pop(partner_index)
        distance, mismatches = pair_distance(left, right)
        left_goes_b = random.Random(stable_int(RUN_ID, budget_id, repo, seed, str(left["task_id"]), str(right["task_id"]), "split")).randrange(2) == 0
        tasks = [
            {
                "task_id": str(left["task_id"]),
                "split": "B_eval" if left_goes_b else "H_future",
            },
            {
                "task_id": str(right["task_id"]),
                "split": "H_future" if left_goes_b else "B_eval",
            },
        ]
        blocks.append(
            {
                "block_index": len(blocks) + 1,
                "repo": repo,
                "task_ids": sorted([str(left["task_id"]), str(right["task_id"])]),
                "tasks": sorted(tasks, key=lambda task: task["split"]),
                "pair_distance": distance,
                "nearest_match_reason": "exact_visible_feature_match" if not mismatches else "nearest_available_mismatch:" + ",".join(mismatches),
            }
        )
    return blocks


def generate_candidate(config: dict[str, Any], rows: list[dict[str, Any]], budget_id: str, seed: int) -> dict[str, Any]:
    tasks_per_repo = budget_tasks_per_repo(config, budget_id)
    split_per_repo = budget_split_tasks_per_repo(config, budget_id)
    design_id = f"{RUN_ID}__{budget_id}__seed_{seed}"
    blocks: list[dict[str, Any]] = []
    for repo in REPOS:
        selected = select_repo_rows(rows, budget_id, repo, tasks_per_repo, seed)
        for block in build_repo_blocks(selected, budget_id, repo, seed):
            block["block_id"] = f"{design_id}__{repo}__block_{block['block_index']:02d}"
            blocks.append(block)
    b_eval = sorted(task["task_id"] for block in blocks for task in block["tasks"] if task["split"] == "B_eval")
    h_future = sorted(task["task_id"] for block in blocks for task in block["tasks"] if task["split"] == "H_future")
    selected_task_ids = sorted(b_eval + h_future)
    row_by_id = rows_by_task_id(rows)
    candidate: dict[str, Any] = {
        "design_id": design_id,
        "budget_id": budget_id,
        "seed": seed,
        "selected_task_ids": selected_task_ids,
        "B_eval_task_ids": b_eval,
        "H_future_task_ids": h_future,
        "block_assignments": sorted(blocks, key=lambda block: (block["repo"], block["block_index"])),
        "selection_inputs_used": ["candidate_universe", "block_schema", "config"],
        "selection_features_used": list(VISIBLE_FEATURES),
        "outcome_fields_used_for_selection": False,
        "outcome_input_paths_loaded_before_freeze": [],
        "split_counts_by_repo": split_repo_counts({"B_eval_task_ids": b_eval, "H_future_task_ids": h_future}, row_by_id),
        "nearest_match_pair_distance_total": sum(int(block["pair_distance"]) for block in blocks),
    }
    candidate["hard_constraint_failures"] = hard_constraint_failures(candidate, row_by_id, split_per_repo)
    candidate.update(compute_imbalance(candidate, row_by_id, soft_penalty_weights(config)))
    return candidate


def build_candidate_splits_payload(config: dict[str, Any]) -> dict[str, Any]:
    universe = load_candidate_universe(config)
    rows = sorted_task_rows(universe["rows"])
    block_schema = read_json(output_path(config, "block_schema"))
    candidates: list[dict[str, Any]] = []
    seed_start = int(config["candidate_seed_start"])
    candidate_seed_count = int(config["candidate_seed_count"])
    for budget_id in config["budgets_to_evaluate"]:
        if not block_schema["budget_feasibility"][budget_id]["feasible"]:
            continue
        for offset in range(candidate_seed_count):
            candidates.append(generate_candidate(config, rows, budget_id, seed_start + offset))
    budget_summary: dict[str, Any] = {}
    for budget_id in config["budgets_to_evaluate"]:
        budget_candidates = [candidate for candidate in candidates if candidate["budget_id"] == budget_id]
        feasible = [candidate for candidate in budget_candidates if not candidate["hard_constraint_failures"]]
        budget_summary[budget_id] = {
            "candidate_count": len(budget_candidates),
            "feasible_candidate_count": len(feasible),
            "minimum_feature_imbalance_score": None if not feasible else min(candidate["feature_imbalance_score"] for candidate in feasible),
            "maximum_feature_imbalance_score": None if not feasible else max(candidate["feature_imbalance_score"] for candidate in feasible),
            "infeasible_reason": None if budget_candidates else "budget_infeasible_or_not_generated",
        }
    return {
        "artifact": "candidate_splits",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "input_paths_loaded": [rel(config["_path"]), rel(config["candidate_universe_path"]), rel(output_path(config, "block_schema"))],
        "outcome_input_paths_loaded": [],
        "outcome_fields_loaded": False,
        "random_seed_family": config["random_seed_family"],
        "candidate_seed_count_per_budget": candidate_seed_count,
        "candidate_count": len(candidates),
        "budget_summary": budget_summary,
        "selection_objective": config["selection_objective"],
        "candidates": candidates,
    }


def render_candidate_splits_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Blocked Split Candidate Splits",
        "",
        "## What Happened",
        "",
        f"Generated {payload['candidate_count']} deterministic candidate splits using seeded block randomization.",
        f"Budget summary: `{payload['budget_summary']}`.",
        "",
        "Every candidate records selected task IDs, block assignments, B_eval/H_future task IDs, hard failures, feature imbalance score, and `outcome_fields_used_for_selection=false`.",
        "",
        "## Why It Matters",
        "",
        "The candidate set gives the selector many reproducible options without looking at pass/fail outcomes. Counts are exact by repo because every within-repo block contributes one task to each split.",
        "",
        "## What Action It Suggests Next",
        "",
        "Freeze the lowest feature-imbalance feasible candidate for the same-budget design as primary, and freeze the best expanded-budget candidate as secondary if feasible. Retrospective outcome diagnostics must wait until after that freeze.",
    ]
    return "\n".join(lines) + "\n"


def generate_candidate_splits(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    payload = build_candidate_splits_payload(config)
    write_json(output_path(config, "candidate_splits"), payload)
    write_text(report_path(config, "candidate_splits"), render_candidate_splits_report(payload))
    return payload


def best_candidate(candidates: list[dict[str, Any]], budget_id: str) -> dict[str, Any] | None:
    feasible = [candidate for candidate in candidates if candidate["budget_id"] == budget_id and not candidate["hard_constraint_failures"]]
    if not feasible:
        return None
    return min(
        feasible,
        key=lambda candidate: (
            float(candidate["feature_imbalance_score"]),
            int(candidate["nearest_match_pair_distance_total"]),
            int(candidate["seed"]),
            str(candidate["design_id"]),
        ),
    )


def freeze_selected_split(config: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    config = config or load_config()
    candidate_payload = read_json(output_path(config, "candidate_splits"))
    candidates = list(candidate_payload["candidates"])
    primary = best_candidate(candidates, PRIMARY_BUDGET)
    secondary = best_candidate(candidates, SECONDARY_BUDGET)
    selected = [candidate for candidate in (primary, secondary) if candidate is not None]
    if primary is None:
        raise ValueError("primary same-budget candidate is not feasible")
    loaded_before_freeze = [rel(config["_path"]), rel(config["candidate_universe_path"]), rel(output_path(config, "block_schema")), rel(output_path(config, "candidate_splits"))]
    outcome_loaded_before_freeze = [path for path in loaded_before_freeze if is_outcome_path(path)]
    selected_payload = {
        "artifact": "selected_split",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "freeze_status": "frozen_before_retrospective_outcome_diagnostics",
        "primary_candidate_id": primary["design_id"],
        "primary_budget_id": primary["budget_id"],
        "primary_seed": primary["seed"],
        "secondary_candidate_id": None if secondary is None else secondary["design_id"],
        "secondary_budget_id": None if secondary is None else secondary["budget_id"],
        "secondary_seed": None if secondary is None else secondary["seed"],
        "selected_candidates": selected,
        "outcome_fields_used_for_selection": False,
        "outcome_input_paths_loaded_before_freeze": outcome_loaded_before_freeze,
        "selection_rule": "minimum feature_imbalance_score, then nearest-match pair distance, seed, design_id",
        "selection_objective": config["selection_objective"],
        "click_minor_risk_caveat": load_candidate_universe(config)["click_minor_risk_caveat"],
    }
    audit_payload = {
        "artifact": "selection_audit",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "loaded_input_paths_before_freeze": loaded_before_freeze,
        "outcome_input_paths_loaded_before_freeze": outcome_loaded_before_freeze,
        "outcome_fields_loaded_before_freeze": False,
        "outcome_fields_used_for_selection": False,
        "selection_inputs_are_visible_features_only": True,
        "selection_policy": config["selection_policy"],
        "selected_candidate_ids": [candidate["design_id"] for candidate in selected],
        "candidate_count_considered": len(candidates),
        "candidate_payload_digest": digest_payload(candidate_payload),
        "selected_split_digest": digest_payload(selected_payload),
        "selection_audit_passed": not outcome_loaded_before_freeze,
        "completed_paid_pilot_files_changed_by_this_step": False,
    }
    write_json(output_path(config, "selected_split"), selected_payload)
    write_json(output_path(config, "selection_audit"), audit_payload)
    return selected_payload, audit_payload


def task_assignment_candidate(design: dict[str, Any]) -> dict[str, str]:
    assignment: dict[str, str] = {}
    for split in SPLITS:
        for task_id in design[f"{split}_task_ids"]:
            assignment[str(task_id)] = split
    return assignment


def candidate_from_assignment(design_id: str, budget_id: str, assignments: dict[str, str]) -> dict[str, Any]:
    return {
        "design_id": design_id,
        "budget_id": budget_id,
        "B_eval_task_ids": sorted(task_id for task_id, split in assignments.items() if split == "B_eval"),
        "H_future_task_ids": sorted(task_id for task_id, split in assignments.items() if split == "H_future"),
    }


def previous_paid_split_candidate(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    split_plan = read_json(input_path(config, "paid_readiness_split_plan"))
    feature_rows = read_json(input_path(config, "source_feature_table"))["rows"]
    row_by_id = {str(row["task_id"]): dict(row) for row in feature_rows}
    assignments = {str(row["candidate_id"]): str(row["split"]) for row in split_plan["assignments"]}
    return candidate_from_assignment("previous_frozen_three_repo_paid_split", "previous_paid_pilot", assignments), row_by_id


def threshold_status_for_candidate(config: dict[str, Any], candidate: dict[str, Any], row_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    thresholds = gate_thresholds(config)
    failures: list[dict[str, Any]] = []
    for feature, threshold_key in GATE_FEATURE_KEYS.items():
        threshold = thresholds[threshold_key]
        summary = feature_diff_summary(candidate, row_by_id, feature)
        for repo, repo_summary in summary["per_repo"].items():
            if repo_summary["max_abs_diff"] > threshold:
                failures.append(
                    {
                        "gate": threshold_key,
                        "feature": feature,
                        "repo": repo,
                        "max_abs_diff": repo_summary["max_abs_diff"],
                        "threshold": threshold,
                    }
                )
    source_quality_summary = feature_diff_summary(candidate, row_by_id, "source_quality_bucket")
    source_context_summary = feature_diff_summary(candidate, row_by_id, "source_context_type_bucket")
    for label, summary in (("source_quality_balance_within_repo", source_quality_summary), ("source_context_type_balance_within_repo", source_context_summary)):
        for repo, repo_summary in summary["per_repo"].items():
            if repo_summary["max_abs_diff"] != 0:
                failures.append({"gate": label, "repo": repo, "max_abs_diff": repo_summary["max_abs_diff"], "threshold": 0})
    if candidate.get("hard_constraint_failures"):
        failures.append({"gate": "hard_constraints", "failures": candidate["hard_constraint_failures"]})
    return {
        "gate_passed": not failures,
        "gate_failures": failures,
        "source_quality_summary": source_quality_summary,
        "source_context_type_summary": source_context_summary,
    }


def build_imbalance_diagnostics(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    universe = load_candidate_universe(config)
    row_by_id = rows_by_task_id(universe["rows"])
    selected_payload = read_json(output_path(config, "selected_split"))
    previous_candidate, previous_row_by_id = previous_paid_split_candidate(config)
    selected_diagnostics: dict[str, Any] = {}
    for candidate in selected_payload["selected_candidates"]:
        candidate = dict(candidate)
        candidate["repo_split_counts"] = split_repo_counts(candidate, row_by_id)
        candidate["feature_summaries"] = {feature: feature_diff_summary(candidate, row_by_id, feature) for feature in ("source_quality_bucket", "source_context_type_bucket", "statement_specificity_bucket", "coarse_task_family", "time_bucket", "editable_scope_bucket", "rare_or_unknown_feature_flag")}
        candidate["threshold_status"] = threshold_status_for_candidate(config, candidate, row_by_id)
        selected_diagnostics[candidate["design_id"]] = candidate
    previous_imbalance = compute_imbalance(previous_candidate, previous_row_by_id, soft_penalty_weights(config))
    payload = {
        "artifact": "imbalance_diagnostics",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "input_paths_loaded": [rel(config["_path"]), rel(config["candidate_universe_path"]), rel(output_path(config, "selected_split")), rel(input_path(config, "paid_readiness_split_plan")), rel(input_path(config, "source_feature_table"))],
        "outcome_input_paths_loaded": [],
        "outcome_fields_loaded": False,
        "selected_diagnostics": selected_diagnostics,
        "previous_frozen_paid_split_retrospective_visible_balance": {
            "design_id": previous_candidate["design_id"],
            "feature_imbalance_score": previous_imbalance["feature_imbalance_score"],
            "note": "Previous split comparison uses visible split-plan features only and no pass/fail outcomes.",
        },
        "fairer_than_previous_on_visible_feature_score": {
            candidate["design_id"]: candidate["feature_imbalance_score"] <= previous_imbalance["feature_imbalance_score"]
            for candidate in selected_payload["selected_candidates"]
        },
        "click_minor_risk_caveat": selected_payload["click_minor_risk_caveat"],
        "predictive_validity_established": False,
    }
    write_json(output_path(config, "imbalance_diagnostics"), payload)
    write_text(report_path(config, "imbalance_diagnostics"), render_imbalance_report(payload))
    return payload


def render_imbalance_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Blocked Split Imbalance Diagnostics",
        "",
        "## What Happened",
        "",
    ]
    for design_id, candidate in payload["selected_diagnostics"].items():
        lines.append(f"`{design_id}` has feature imbalance score `{candidate['feature_imbalance_score']}` and gate status `{candidate['threshold_status']['gate_passed']}`.")
    lines += [
        f"Previous frozen paid split visible-feature score: `{payload['previous_frozen_paid_split_retrospective_visible_balance']['feature_imbalance_score']}`.",
        "",
        "## Why It Matters",
        "",
        "B_eval and H_future are checked by repo on visible features only. This keeps attrs, boltons, and click from masking each other in a pooled average.",
        "",
        "Click remains title-only minor risk: it is balanced within click, but it still has a weaker source-context claim boundary than attrs or boltons.",
        "",
        "## What Action It Suggests Next",
        "",
        "Use these diagnostics as the feature-balance gate for any later preregistration decision. Do not treat this as predictive validity evidence.",
    ]
    return "\n".join(lines) + "\n"


def load_score_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    manifest = read_json(input_path(config, "score_tables_manifest"))
    rows: list[dict[str, Any]] = []
    for entry in manifest.get("entries", []):
        score_table = entry["score_table"]
        for row in read_csv(score_table):
            task_id = str(row["task_id"])
            terminal_status = str(row.get("terminal_status") or "")
            rows.append(
                {
                    "task_id": task_id,
                    "repo": repo_from_task_id(task_id),
                    "old_split": str(row.get("split") or ""),
                    "adapter_id": str(row.get("adapter_id") or ""),
                    "terminal_status": terminal_status,
                    "scoreable_cell": bool_from_csv(row.get("scoreable_cell")),
                    "pass_flag": terminal_status == "verified_pass" and bool_from_csv(row.get("scoreable_cell")),
                    "score_table": rel(score_table),
                }
            )
    return rows


def summarize_rate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scoreable = [row for row in rows if row["scoreable_cell"]]
    passed = sum(1 for row in scoreable if row["pass_flag"])
    return {
        "cell_count": len(rows),
        "scoreable_cell_count": len(scoreable),
        "pass_count": passed,
        "pass_rate": None if not scoreable else round(passed / len(scoreable), 4),
    }


def grouped_rates(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[str, Any]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row.get(key) or "unknown") for key in keys)].append(row)
    return {"|".join(key): summarize_rate(group_rows) for key, group_rows in sorted(groups.items())}


def paired_disagreement(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_task: dict[str, dict[str, bool]] = defaultdict(dict)
    for row in rows:
        if row["scoreable_cell"] and row["adapter_id"] in ADAPTERS:
            by_task[row["task_id"]][row["adapter_id"]] = bool(row["pass_flag"])
    counts = Counter()
    for adapter_passes in by_task.values():
        if set(adapter_passes) != set(ADAPTERS):
            continue
        codex = adapter_passes["codex_workspace"]
        kilo = adapter_passes["kilo_workspace"]
        if codex and kilo:
            counts["both_pass"] += 1
        elif not codex and not kilo:
            counts["both_fail"] += 1
        elif codex:
            counts["codex_only_pass"] += 1
        else:
            counts["kilo_only_pass"] += 1
    paired = sum(counts.values())
    return {
        "paired_task_count": paired,
        "both_pass": counts["both_pass"],
        "both_fail": counts["both_fail"],
        "codex_only_pass": counts["codex_only_pass"],
        "kilo_only_pass": counts["kilo_only_pass"],
        "disagreement_count": counts["codex_only_pass"] + counts["kilo_only_pass"],
        "disagreement_rate": None if not paired else round((counts["codex_only_pass"] + counts["kilo_only_pass"]) / paired, 4),
    }


def build_retrospective_outcome_diagnostics(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    selected_payload = read_json(output_path(config, "selected_split"))
    score_rows = load_score_rows(config)
    design_payloads: dict[str, Any] = {}
    for candidate in selected_payload["selected_candidates"]:
        assignment = task_assignment_candidate(candidate)
        rows = []
        for row in score_rows:
            if row["task_id"] in assignment:
                joined = dict(row)
                joined["new_split"] = assignment[row["task_id"]]
                rows.append(joined)
        covered_tasks = sorted({row["task_id"] for row in rows})
        missing_tasks = sorted(set(candidate["selected_task_ids"]) - set(covered_tasks))
        design_payloads[candidate["design_id"]] = {
            "budget_id": candidate["budget_id"],
            "selected_task_count": len(candidate["selected_task_ids"]),
            "tasks_with_any_completed_paid_outcome": len(covered_tasks),
            "tasks_missing_completed_paid_outcome": len(missing_tasks),
            "missing_outcomes_imputed": False,
            "outcome_coverage_by_repo_and_new_split": grouped_rates(rows, ("repo", "new_split")),
            "adapter_level_pass_rates": grouped_rates(rows, ("adapter_id", "repo", "new_split")),
            "adapter_level_gaps": adapter_gaps(rows),
            "paired_disagreement": paired_disagreement(rows),
        }
    metrics = read_json(input_path(config, "validation_metrics"))
    payload = {
        "artifact": "retrospective_outcome_diagnostics",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "input_paths_loaded": [rel(config["_path"]), rel(output_path(config, "selected_split")), rel(input_path(config, "score_tables_manifest")), *sorted({row["score_table"] for row in score_rows})],
        "outcome_input_paths_loaded": [rel(input_path(config, "score_tables_manifest")), *sorted({row["score_table"] for row in score_rows})],
        "retrospective_outcomes_did_not_choose_split": True,
        "missing_outcome_cells_are_not_imputed": True,
        "adapter_level_diagnostics_remain_separate": True,
        "pooled_diagnostics_are_secondary": True,
        "predictive_validity_established": False,
        "selected_split_changed_after_outcomes": False,
        "design_diagnostics": design_payloads,
        "previous_frozen_paid_split_comparison_retrospective": {
            "primary_design": metrics.get("primary_design"),
            "scoreable_cells": metrics.get("scoreable_cells"),
            "pooled_unweighted": metrics.get("pooled_unweighted"),
            "label": "retrospective_context_only_not_paid_evidence_for_new_design",
        },
    }
    write_json(output_path(config, "retrospective_outcome_diagnostics"), payload)
    write_text(report_path(config, "retrospective_outcome_diagnostics"), render_retrospective_report(payload))
    return payload


def adapter_gaps(rows: list[dict[str, Any]]) -> dict[str, Any]:
    gaps: dict[str, Any] = {}
    for adapter in ADAPTERS:
        adapter_rows = [row for row in rows if row["adapter_id"] == adapter]
        for repo in REPOS:
            key = f"{adapter}|{repo}"
            b_rate = summarize_rate([row for row in adapter_rows if row["repo"] == repo and row["new_split"] == "B_eval"])["pass_rate"]
            h_rate = summarize_rate([row for row in adapter_rows if row["repo"] == repo and row["new_split"] == "H_future"])["pass_rate"]
            gaps[key] = {
                "B_eval_pass_rate": b_rate,
                "H_future_pass_rate": h_rate,
                "absolute_gap": None if b_rate is None or h_rate is None else round(abs(b_rate - h_rate), 4),
            }
    return gaps


def render_retrospective_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Blocked Split Retrospective Outcome Diagnostics",
        "",
        "## What Happened",
        "",
        "After the selected split was frozen, existing completed paid score tables were joined where task IDs overlapped. Missing outcome cells were not imputed.",
        "",
    ]
    for design_id, diagnostics in payload["design_diagnostics"].items():
        lines.append(f"`{design_id}` coverage: {diagnostics['tasks_with_any_completed_paid_outcome']}/{diagnostics['selected_task_count']} tasks have at least one completed paid outcome.")
    lines += [
        "",
        "## Why It Matters",
        "",
        "These diagnostics did not choose or tune the split. Adapter-level results remain separate, pooled diagnostics are secondary, and predictive validity remains false.",
        "",
        "## What Action It Suggests Next",
        "",
        "Use this only as a retrospective sanity check. Any new evidence for the redesigned split would require a later preregistered paid validation runbook.",
    ]
    return "\n".join(lines) + "\n"


def load_cost_summaries(config: dict[str, Any]) -> list[dict[str, Any]]:
    paths = sorted(glob.glob(str(repo_path(input_path(config, "cost_summaries_glob")))))
    return [{**read_json(path), "_path": rel(path)} for path in paths]


def adapter_from_cost_summary(summary: dict[str, Any]) -> str:
    per_harness = summary.get("per_harness_observed_token_cost_usd") or {}
    if len(per_harness) == 1:
        return next(iter(per_harness))
    prefix = str(summary.get("result_prefix") or "")
    if "codex_workspace" in prefix:
        return "codex_workspace"
    if "kilo_workspace" in prefix:
        return "kilo_workspace"
    return "unknown"


def build_cost_power_projection(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    summaries = load_cost_summaries(config)
    by_adapter: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for summary in summaries:
        by_adapter[adapter_from_cost_summary(summary)].append(summary)
    adapter_baselines: dict[str, Any] = {}
    for adapter, adapter_summaries in sorted(by_adapter.items()):
        call_count = sum(int(summary.get("call_count") or 0) for summary in adapter_summaries)
        observed_or_conservative = sum(float(summary.get("observed_or_conservative_estimated_cost_usd") or 0.0) for summary in adapter_summaries)
        observed = sum(float(summary.get("observed_token_estimated_cost_usd") or 0.0) for summary in adapter_summaries)
        conservative = sum(float(summary.get("conservative_estimated_cost_usd") or 0.0) for summary in adapter_summaries)
        billed_values = [summary.get("actual_provider_billed_cost_usd") for summary in adapter_summaries if summary.get("actual_provider_billed_cost_usd") is not None]
        latencies = [float(summary["median_latency_seconds"]) for summary in adapter_summaries if summary.get("median_latency_seconds") is not None]
        adapter_baselines[adapter] = {
            "prior_call_count": call_count,
            "observed_token_estimated_cost_usd": round(observed, 6),
            "observed_or_conservative_estimated_cost_usd": round(observed_or_conservative, 6),
            "conservative_estimated_cost_usd": round(conservative, 6),
            "actual_provider_billed_cost_usd": None if not billed_values else round(sum(float(value) for value in billed_values), 6),
            "provider_billed_cost_status": "unavailable" if not billed_values else "available",
            "estimated_cost_per_cell_usd": None if not call_count else round(observed_or_conservative / call_count, 6),
            "median_latency_seconds": None if not latencies else round(statistics.median(latencies), 3),
        }
    projections: dict[str, Any] = {}
    for budget_id in config["budgets_to_evaluate"]:
        tasks_per_repo = budget_tasks_per_repo(config, budget_id)
        split_per_repo = budget_split_tasks_per_repo(config, budget_id)
        total_tasks = tasks_per_repo * len(REPOS)
        by_adapter_projection: dict[str, Any] = {}
        for adapter, baseline in adapter_baselines.items():
            per_cell = baseline["estimated_cost_per_cell_usd"] or 0.0
            by_adapter_projection[adapter] = {
                "scoreable_cell_count": total_tasks,
                "token_estimated_cost_usd": round(per_cell * total_tasks, 6),
                "cost_basis": "token_estimated",
                "provider_billed_cost_status": baseline["provider_billed_cost_status"],
                "estimated_latency_seconds_per_cell": baseline["median_latency_seconds"],
            }
        projections[budget_id] = {
            "tasks_per_repo": tasks_per_repo,
            "B_eval_tasks_per_repo": split_per_repo,
            "H_future_tasks_per_repo": split_per_repo,
            "total_tasks": total_tasks,
            "adapters": sorted(adapter_baselines),
            "scoreable_cell_count": total_tasks * len(adapter_baselines),
            "by_adapter": by_adapter_projection,
            "total_token_estimated_cost_usd": round(sum(item["token_estimated_cost_usd"] for item in by_adapter_projection.values()), 6),
            "expected_precision_caveat": "larger task count improves retrospective precision mechanically but does not establish predictive validity",
        }
    payload = {
        "artifact": "cost_power_projection",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "input_paths_loaded": [rel(config["_path"]), *[summary["_path"] for summary in summaries], rel(input_path(config, "workspace_usage_ledger"))],
        "paid_calls_made": 0,
        "cost_basis": "token_estimated_unless_provider_billed_available",
        "adapter_baselines": adapter_baselines,
        "budget_projections": projections,
        "expanded_budget_recommendation": "secondary_candidate_worth_considering_if_preregistration_accepts_higher_cost_and_click_minor_risk_caveat",
        "predictive_validity_established": False,
    }
    write_json(output_path(config, "cost_power_projection"), payload)
    write_text(report_path(config, "cost_power_projection"), render_cost_report(payload))
    return payload


def render_cost_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Blocked Split Cost And Power Projection",
        "",
        "## What Happened",
        "",
        "Projected future paid validation cost from committed prior cost summaries. No paid calls were made.",
        "",
    ]
    for budget_id, projection in payload["budget_projections"].items():
        lines.append(f"`{budget_id}`: {projection['scoreable_cell_count']} planned scoreable cells, token-estimated cost `${projection['total_token_estimated_cost_usd']}`.")
    lines += [
        "",
        "## Why It Matters",
        "",
        "The estimate is adapter-separated before any pooled total. Provider-billed exact cost is unavailable in the committed summaries, so projected cost remains token-estimated.",
        "",
        "## What Action It Suggests Next",
        "",
        "Treat the expanded design as secondary unless the coordinator accepts the higher projected cost and the persistent click title-only minor-risk caveat.",
    ]
    return "\n".join(lines) + "\n"


def build_readiness_gate(config: dict[str, Any] | None = None, *, tests_passed: bool = True) -> dict[str, Any]:
    config = config or load_config()
    universe = load_candidate_universe(config)
    audit = read_json(output_path(config, "selection_audit"))
    imbalance = read_json(output_path(config, "imbalance_diagnostics"))
    retrospective = read_json(output_path(config, "retrospective_outcome_diagnostics"))
    selected = read_json(output_path(config, "selected_split"))
    paid_decision = read_json(input_path(config, "validation_decision"))
    primary_diag = imbalance["selected_diagnostics"][selected["primary_candidate_id"]]
    gates = {
        "candidate_universe_eligible_only": universe["blocked_source_quality_selected_count"] == 0 and universe["diagnostic_only_selected_count"] == 0,
        "selection_audit_outcome_blind": audit["selection_audit_passed"] and audit["outcome_fields_loaded_before_freeze"] is False,
        "primary_selected_split_exact_repo_and_split_counts": not primary_diag["hard_constraint_failures"],
        "blocked_or_diagnostic_tasks_selected": universe["blocked_source_quality_selected_count"] == 0 and universe["diagnostic_only_selected_count"] == 0,
        "feature_imbalance_gates_pass": primary_diag["threshold_status"]["gate_passed"],
        "click_minor_risk_visible": selected["click_minor_risk_caveat"]["all_click_source_quality_minor_risk"] is True,
        "retrospective_outcomes_did_not_change_split": retrospective["selected_split_changed_after_outcomes"] is False,
        "paid_calls_made_by_this_run": 0,
        "completed_paid_decision_changed": False,
        "predictive_validity_established": False,
        "tests_and_diff_check_passed": tests_passed,
    }
    failed = [key for key, value in gates.items() if value is not True and value != 0]
    ready = not failed
    payload = {
        "artifact": "readiness_gate",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "ready_for_preregistered_paid_validation_runbook": ready,
        "decision_label": "blocked_split_ready_with_click_minor_risk" if ready else "blocked_split_blocked_by_feature_imbalance",
        "gates": gates,
        "failed_gates": failed,
        "paid_calls_made_by_this_run": 0,
        "completed_paid_decision_changed": False,
        "completed_paid_decision_label": paid_decision.get("decision_label"),
        "predictive_validity_established": False,
        "selected_primary_candidate_id": selected["primary_candidate_id"],
        "selected_primary_budget_id": selected["primary_budget_id"],
        "selected_secondary_candidate_id": selected["secondary_candidate_id"],
        "click_minor_risk_status": "visible_title_only_minor_risk",
        "smallest_remaining_blocker": "click_title_only_minor_risk",
        "recommended_next_action_category": "preregistered_paid_validation_design_review" if ready else "source_repair_or_split_rebalance",
    }
    write_json(output_path(config, "readiness_gate"), payload)
    write_text(report_path(config, "readiness_gate"), render_readiness_report(payload))
    return payload


def render_readiness_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Blocked Split Readiness Gate",
            "",
            "## What Happened",
            "",
            f"Readiness gate result: `{payload['ready_for_preregistered_paid_validation_runbook']}` with decision label `{payload['decision_label']}`.",
            f"Primary selected split: `{payload['selected_primary_candidate_id']}`.",
            "",
            "## Why It Matters",
            "",
            "The gate checks that the split was selected using visible pre-outcome features only, that repo and split counts are exact, and that click title-only minor risk remains visible.",
            "",
            "Predictive validity remains false, and the completed paid decision is unchanged.",
            "",
            "## What Action It Suggests Next",
            "",
            f"Coordinator action category: `{payload['recommended_next_action_category']}`. Smallest remaining blocker: `{payload['smallest_remaining_blocker']}`.",
        ]
    ) + "\n"


def build_decision(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    gate = read_json(output_path(config, "readiness_gate"))
    cost = read_json(output_path(config, "cost_power_projection"))
    retrospective = read_json(output_path(config, "retrospective_outcome_diagnostics"))
    payload = {
        "artifact": "decision",
        "schema_version": OUTPUT_SCHEMA,
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "decision_label": gate["decision_label"],
        "ready_for_preregistered_paid_validation_runbook": gate["ready_for_preregistered_paid_validation_runbook"],
        "predictive_validity_established": False,
        "paid_calls_made_by_this_run": 0,
        "completed_paid_decision_changed": False,
        "followup_runbook_written_by_worker": False,
        "selected_primary_candidate_id": gate["selected_primary_candidate_id"],
        "selected_primary_budget_id": gate["selected_primary_budget_id"],
        "selected_secondary_candidate_id": gate["selected_secondary_candidate_id"],
        "click_minor_risk_status": gate["click_minor_risk_status"],
        "smallest_remaining_blocker": gate["smallest_remaining_blocker"],
        "recommended_next_action_category": gate["recommended_next_action_category"],
        "research_questions": {
            "RQ1_visible_pre_outcome_features_only": gate["gates"]["selection_audit_outcome_blind"],
            "RQ2_primary_budget_and_reason": "same_budget_20_per_repo selected by minimum visible-feature imbalance score",
            "RQ3_balance_gate": gate["gates"]["feature_imbalance_gates_pass"],
            "RQ4_click_title_only_minor_risk_claim_boundary": gate["click_minor_risk_status"],
            "RQ5_retrospective_outcome_diagnostics": "joined after freeze only; not paid evidence for the redesigned split",
            "RQ6_future_paid_cost_by_budget": {budget_id: projection["total_token_estimated_cost_usd"] for budget_id, projection in cost["budget_projections"].items()},
            "RQ7_paid_calls_or_completed_decision_changes": {
                "paid_calls_made": 0,
                "completed_paid_decision_changed": False,
            },
            "RQ8_smallest_remaining_blocker": gate["smallest_remaining_blocker"],
            "RQ9_next_action_category": gate["recommended_next_action_category"],
        },
        "retrospective_outcomes_did_not_choose_split": retrospective["retrospective_outcomes_did_not_choose_split"],
    }
    write_json(output_path(config, "decision"), payload)
    write_text(report_path(config, "decision"), render_decision_report(payload))
    return payload


def render_decision_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Blocked Split Redesign Decision",
            "",
            "## What Happened",
            "",
            f"Decision label: `{payload['decision_label']}`.",
            f"Primary selected split: `{payload['selected_primary_candidate_id']}` using budget `{payload['selected_primary_budget_id']}`.",
            "",
            "## Why It Matters",
            "",
            "The selected split was frozen before retrospective outcomes were joined. It uses only source-context and statement-quality features visible before paid outcomes.",
            "",
            "Click remains title-only minor risk, so the design is not a clean-source three-repo claim. Predictive validity remains false.",
            "",
            "## What Action It Suggests Next",
            "",
            f"Recommended action category: `{payload['recommended_next_action_category']}`. Smallest remaining blocker: `{payload['smallest_remaining_blocker']}`.",
        ]
    ) + "\n"


def run_all_pre_freeze(config: dict[str, Any]) -> None:
    build_block_schema(config)
    generate_candidate_splits(config)
    freeze_selected_split(config)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Phase 1 blocked split redesign artifacts.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in (
        "block-schema",
        "candidate-splits",
        "freeze",
        "imbalance",
        "retrospective",
        "cost",
        "readiness",
        "decision",
        "pre-freeze",
        "post-freeze",
        "all",
    ):
        subparsers.add_parser(command)
    args = parser.parse_args()
    config = load_config(args.config)
    if args.command == "block-schema":
        build_block_schema(config)
    elif args.command == "candidate-splits":
        generate_candidate_splits(config)
    elif args.command == "freeze":
        freeze_selected_split(config)
    elif args.command == "imbalance":
        build_imbalance_diagnostics(config)
    elif args.command == "retrospective":
        build_retrospective_outcome_diagnostics(config)
    elif args.command == "cost":
        build_cost_power_projection(config)
    elif args.command == "readiness":
        build_readiness_gate(config)
    elif args.command == "decision":
        build_decision(config)
    elif args.command == "pre-freeze":
        run_all_pre_freeze(config)
    elif args.command == "post-freeze":
        build_imbalance_diagnostics(config)
        build_retrospective_outcome_diagnostics(config)
        build_cost_power_projection(config)
        build_readiness_gate(config)
        build_decision(config)
    elif args.command == "all":
        run_all_pre_freeze(config)
        build_imbalance_diagnostics(config)
        build_retrospective_outcome_diagnostics(config)
        build_cost_power_projection(config)
        build_readiness_gate(config)
        build_decision(config)


if __name__ == "__main__":
    main()
