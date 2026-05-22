from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
DEFAULT_CONFIG = ROOT / "configs" / "phase1_future_holdout_validation.yaml"
TWO_REPO_CONFIG = ROOT / "configs" / "phase1_two_repo_future_holdout_validation.yaml"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path | str) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def parse_scalar(value: str) -> Any:
    text = value.strip().strip("'\"")
    if text == "":
        return ""
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False
    if text.lower() in {"null", "none"}:
        return None
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def simple_yaml_load(path: Path) -> dict[str, Any]:
    rows: list[tuple[int, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        rows.append((len(raw) - len(raw.lstrip(" ")), raw.strip()))

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(rows):
            return {}, index
        is_list = rows[index][0] == indent and rows[index][1].startswith("- ")
        if is_list:
            items = []
            while index < len(rows) and rows[index][0] == indent and rows[index][1].startswith("- "):
                items.append(parse_scalar(rows[index][1][2:]))
                index += 1
            return items, index

        mapping: dict[str, Any] = {}
        while index < len(rows):
            row_indent, text = rows[index]
            if row_indent < indent:
                break
            if row_indent > indent:
                raise ValueError(f"unsupported YAML indentation near: {text}")
            if ":" not in text:
                raise ValueError(f"unsupported YAML line: {text}")
            key, raw_value = text.split(":", 1)
            index += 1
            if raw_value.strip():
                mapping[key] = parse_scalar(raw_value)
                continue
            if index >= len(rows) or rows[index][0] <= row_indent:
                mapping[key] = {}
                continue
            mapping[key], index = parse_block(index, rows[index][0])
        return mapping, index

    parsed, final_index = parse_block(0, 0)
    if final_index != len(rows):
        raise ValueError(f"unparsed YAML content in {path}")
    if not isinstance(parsed, dict):
        raise ValueError(f"expected mapping YAML root in {path}")
    return parsed


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != "barcarolle.phase1_future_holdout_validation.v1":
        raise ValueError("unexpected future holdout config schema_version")
    config["_path"] = str(path)
    return config


def load_two_repo_config(path: Path = TWO_REPO_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != "barcarolle.phase1_two_repo_future_holdout_validation.v1":
        raise ValueError("unexpected two repo future holdout config schema_version")
    config["_path"] = str(path)
    return config


def artifact_path(config: dict[str, Any], key: str) -> Path:
    raw = config["source_artifacts"][key]
    path = Path(str(raw))
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def config_path(raw: str | Path) -> Path:
    path = Path(str(raw))
    return path if path.is_absolute() else REPO_ROOT / path


def configured_output_path(config: dict[str, Any], key: str) -> Path:
    return config_path(config["output_paths"][key])


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
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_task_time(raw: str) -> datetime:
    value = raw.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"task_time must include timezone: {raw}")
    return parsed


def sort_clean_tasks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (parse_task_time(str(row["task_time"])), str(row["task_id"])))


def repo_from_task_id(task_id: str) -> str:
    if "__" in task_id:
        return task_id.split("__", 1)[0]
    return "unknown"


@dataclass(frozen=True)
class ClassifiedTask:
    row: dict[str, Any]
    clean_eligible: bool
    exclusion_reasons: list[str]


def classify_task(
    row: dict[str, Any],
    *,
    benchmark_grade_task_ids: set[str],
    outcome_seen_task_ids: set[str],
    diagnostic_only_repos: set[str],
    excluded_target_repos: set[str],
) -> ClassifiedTask:
    task_id = str(row.get("task_id") or "")
    repo_id = str(row.get("repo_id") or repo_from_task_id(task_id))
    reasons = []
    clean_overlay_promoted = (
        row.get("clean_supply_evidence_level") == "clean_supply_overlay_sidecar"
        and row.get("clean_overlay_promotion_decision")
        in {"promote_to_clean_benchmark_candidate", "prior_promoted_clean_supply"}
        and row.get("target_commit_unseen", True) is not False
    )
    if repo_id in excluded_target_repos:
        reasons.append("generic_comparator")
    if repo_id in diagnostic_only_repos:
        reasons.append("diagnostic_only_source_provenance")
    if task_id not in benchmark_grade_task_ids and not clean_overlay_promoted:
        reasons.append("not_benchmark_grade_or_hardening_rejected")
    if row.get("target_commit_unseen", True) is False:
        reasons.append("previous_acut_target_commit_seen")
    if task_id in outcome_seen_task_ids:
        reasons.append("previous_acut_outcome_seen")
    if not row.get("task_time"):
        reasons.append("missing_task_time")
    return ClassifiedTask(row=row, clean_eligible=not reasons, exclusion_reasons=reasons)


def load_benchmark_grade_task_ids(config: dict[str, Any]) -> set[str]:
    overlay = read_json(artifact_path(config, "hardening_overlay"))
    return {
        str(row["task_id"])
        for row in overlay.get("tasks", [])
        if row.get("hardened_status") == "benchmark_grade_candidate"
    }


def load_candidate_tasks(config: dict[str, Any]) -> list[dict[str, Any]]:
    repos = list(config["eligible_repos"].get("primary", [])) + list(config["eligible_repos"].get("diagnostic_only", []))
    rows: list[dict[str, Any]] = []
    for repo_id in repos:
        key = f"{repo_id}_certified_tasks"
        if key not in config["source_artifacts"]:
            continue
        for row in read_jsonl(artifact_path(config, key)):
            row = dict(row)
            row.setdefault("repo_id", repo_id)
            rows.append(row)
    rows.extend(load_clean_supply_overlay_tasks(config))
    return rows


def clean_supply_overlay_paths(config: dict[str, Any]) -> list[Path]:
    raw = config.get("clean_supply_overlays", [])
    if isinstance(raw, str):
        raw = [raw]
    paths = []
    for item in raw:
        path = Path(str(item))
        paths.append(path if path.is_absolute() else REPO_ROOT / path)
    return paths


def overlay_candidate_tasks(payload: dict[str, Any], *, source_path: str) -> list[dict[str, Any]]:
    if payload.get("evidence_level") != "clean_supply_overlay_sidecar":
        return []
    rows: list[dict[str, Any]] = []
    for row in payload.get("promoted_tasks", []):
        if not row.get("task_id") or not row.get("repo_id") or not row.get("task_time"):
            continue
        decision = row.get("promotion_decision") or row.get("clean_overlay_promotion_decision")
        rows.append(
            {
                "task_id": str(row["task_id"]),
                "repo_id": str(row["repo_id"]),
                "task_time": row["task_time"],
                "status": "certified",
                "module_or_package": row.get("module_or_package", []),
                "task_type_proxy": row.get("task_type_proxy", "behavior_or_feature_or_bugfix"),
                "clean_supply_evidence_level": "clean_supply_overlay_sidecar",
                "clean_overlay_promotion_decision": decision,
                "clean_supply_overlay_source": source_path,
                "original_hardening_status": row.get("original_hardening_status"),
                "target_commit_unseen": row.get("target_commit_unseen", True),
            }
        )
    return rows


def load_clean_supply_overlay_tasks(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in clean_supply_overlay_paths(config):
        if path.exists():
            rows.extend(overlay_candidate_tasks(read_json(path), source_path=rel(path)))
    return rows


def load_outcome_seen_task_ids(config: dict[str, Any]) -> set[str]:
    task_ids: set[str] = set()
    scorecard_path = artifact_path(config, "workspace_scorecard")
    if scorecard_path.exists():
        scorecard = read_json(scorecard_path)
        task_ids.update(str(cell["task_id"]) for cell in scorecard.get("cells", []) if cell.get("task_id"))
    for score_table in (PHASE0_ROOT / "results").glob("*_score_table.csv"):
        for row in read_csv(score_table):
            task_id = row.get("task_id")
            if task_id:
                task_ids.add(str(task_id))
    return task_ids


def model_snapshot_status_and_date(config: dict[str, Any]) -> tuple[str, datetime | None]:
    raw_date = (config.get("model_design") or {}).get("model_snapshot_date")
    if raw_date:
        return "known", parse_task_time(str(raw_date))
    return "unknown", None


def select_cutoff_for_repo(
    repo_id: str,
    clean_tasks: list[dict[str, Any]],
    *,
    embargo_gap_days: int,
    preferred_b: int,
    preferred_h: int,
    minimum_b: int,
    minimum_h: int,
    model_snapshot_date: datetime | None,
    model_snapshot_status: str,
) -> dict[str, Any]:
    tasks = sort_clean_tasks(clean_tasks)

    def try_counts(label: str, b_count: int, h_count: int) -> dict[str, Any] | None:
        for candidate in tasks:
            compile_end = parse_task_time(str(candidate["task_time"]))
            holdout_start = compile_end + timedelta(days=embargo_gap_days)
            b_candidates = [row for row in tasks if parse_task_time(str(row["task_time"])) <= compile_end]
            h_candidates = [row for row in tasks if parse_task_time(str(row["task_time"])) >= holdout_start]
            if model_snapshot_status == "known" and model_snapshot_date is not None:
                h_candidates = [row for row in h_candidates if parse_task_time(str(row["task_time"])) > model_snapshot_date]
            if len(b_candidates) >= b_count and len(h_candidates) >= h_count:
                b_eval = b_candidates[-b_count:]
                h_future = h_candidates[:h_count]
                return {
                    "repo_id": repo_id,
                    "T_compile_end": compile_end.isoformat(),
                    "T_holdout_start": holdout_start.isoformat(),
                    "b_eval_task_ids": [str(row["task_id"]) for row in b_eval],
                    "h_future_task_ids": [str(row["task_id"]) for row in h_future],
                    "clean_validation_ready": True,
                    "validation_size": label,
                    "clean_task_count": len(tasks),
                    "blockers": [],
                }
        return None

    preferred = try_counts("preferred", preferred_b, preferred_h)
    if preferred is not None:
        return preferred
    minimum = try_counts("minimum", minimum_b, minimum_h)
    if minimum is not None:
        return minimum
    blockers = ["insufficient_clean_outcome_unseen_supply"]
    if model_snapshot_status == "known" and model_snapshot_date is not None:
        blockers.append("future_holdout_model_date_supply_blocked")
    return {
        "repo_id": repo_id,
        "T_compile_end": None,
        "T_holdout_start": None,
        "b_eval_task_ids": [],
        "h_future_task_ids": [],
        "clean_validation_ready": False,
        "validation_size": "blocked",
        "clean_task_count": len(tasks),
        "blockers": blockers,
    }


def build_supply(config: dict[str, Any]) -> dict[str, Any]:
    benchmark_grade_task_ids = load_benchmark_grade_task_ids(config)
    outcome_seen_task_ids = load_outcome_seen_task_ids(config)
    diagnostic_only_repos = set(config["eligible_repos"].get("diagnostic_only", []))
    excluded_target_repos = set(config["eligible_repos"].get("excluded_target_holdout", []))
    primary_repos = set(config["eligible_repos"].get("primary", []))
    minimums = config["clean_split_minimums"]
    embargo_gap_days = int(config["cutoff_policy"]["embargo_gap_days"])
    model_snapshot_status, model_snapshot_date = model_snapshot_status_and_date(config)

    classified_by_repo: dict[str, list[ClassifiedTask]] = {}
    for row in load_candidate_tasks(config):
        repo_id = str(row.get("repo_id") or repo_from_task_id(str(row.get("task_id", ""))))
        classified = classify_task(
            row,
            benchmark_grade_task_ids=benchmark_grade_task_ids,
            outcome_seen_task_ids=outcome_seen_task_ids,
            diagnostic_only_repos=diagnostic_only_repos,
            excluded_target_repos=excluded_target_repos,
        )
        classified_by_repo.setdefault(repo_id, []).append(classified)

    repo_summary: dict[str, Any] = {}
    repo_plans: dict[str, Any] = {}
    selected_repos: list[str] = []
    for repo_id in sorted(classified_by_repo):
        rows = classified_by_repo[repo_id]
        clean_rows = [item.row for item in rows if item.clean_eligible and repo_id in primary_repos]
        reason_counts: Counter[str] = Counter()
        for item in rows:
            reason_counts.update(item.exclusion_reasons)
        plan = select_cutoff_for_repo(
            repo_id,
            clean_rows,
            embargo_gap_days=embargo_gap_days,
            preferred_b=int(minimums["preferred_b_eval_tasks_per_repo"]),
            preferred_h=int(minimums["preferred_h_future_tasks_per_repo"]),
            minimum_b=int(minimums["minimum_b_eval_tasks_per_repo"]),
            minimum_h=int(minimums["minimum_h_future_tasks_per_repo"]),
            model_snapshot_date=model_snapshot_date,
            model_snapshot_status=model_snapshot_status,
        )
        repo_plans[repo_id] = plan
        if plan["clean_validation_ready"]:
            selected_repos.append(repo_id)
        repo_summary[repo_id] = {
            "certified_task_count": len(rows),
            "benchmark_grade_candidate_count": sum(
                1 for item in rows if str(item.row.get("task_id")) in benchmark_grade_task_ids
            ),
            "previous_acut_outcome_seen_count": sum(
                1 for item in rows if str(item.row.get("task_id")) in outcome_seen_task_ids
            ),
            "clean_outcome_unseen_count": len(clean_rows),
            "missing_task_time_count": reason_counts.get("missing_task_time", 0),
            "exclusion_reason_counts": dict(sorted(reason_counts.items())),
            "clean_task_ids": [str(row["task_id"]) for row in sort_clean_tasks(clean_rows)],
            "clean_task_source_counts": dict(
                sorted(Counter(str(row.get("clean_supply_evidence_level") or "hardening_overlay") for row in clean_rows).items())
            ),
            "clean_tasks": [
                {
                    "task_id": str(row["task_id"]),
                    "source": str(row.get("clean_supply_evidence_level") or "hardening_overlay"),
                    "clean_supply_overlay_source": row.get("clean_supply_overlay_source"),
                    "original_hardening_status": row.get("original_hardening_status"),
                }
                for row in sort_clean_tasks(clean_rows)
            ],
            "minimum_clean_split_ready": plan["clean_validation_ready"],
        }

    blockers = [] if selected_repos else ["no_repo_has_minimum_clean_outcome_unseen_supply"]
    return {
        "schema_version": "barcarolle.phase1.future_holdout_clean_supply.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "cutoff_primary_axis": "repo_task_time",
        "embargo_gap_days": embargo_gap_days,
        "model_snapshot_status": model_snapshot_status,
        "model_snapshot_date": None if model_snapshot_date is None else model_snapshot_date.isoformat(),
        "selected_repos": selected_repos,
        "clean_supply_ready": bool(selected_repos),
        "repo_summary": repo_summary,
        "repo_plans": repo_plans,
        "blockers": blockers,
        "outcome_seen_task_count": len(outcome_seen_task_ids),
        "predictive_validity_established": False,
    }


def clean_supply_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Future Holdout Clean Supply",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Clean supply ready: `{str(payload['clean_supply_ready']).lower()}`.",
        f"- Selected repos: `{', '.join(payload['selected_repos']) if payload['selected_repos'] else 'none'}`.",
        f"- Model snapshot status: `{payload['model_snapshot_status']}`.",
        f"- Predictive validity established: `false`.",
        "",
        "| Repo | Certified | Benchmark-grade | Outcome-seen | Clean outcome-unseen | Minimum split ready |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for repo_id, summary in payload["repo_summary"].items():
        lines.append(
            f"| `{repo_id}` | {summary['certified_task_count']} | {summary['benchmark_grade_candidate_count']} | "
            f"{summary['previous_acut_outcome_seen_count']} | {summary['clean_outcome_unseen_count']} | "
            f"`{str(summary['minimum_clean_split_ready']).lower()}` |"
        )
    lines.extend(["", "## Blockers", ""])
    if payload["blockers"]:
        lines.extend(f"- `{item}`" for item in payload["blockers"])
    else:
        lines.append("- None.")
    return "\n".join(lines)


def cutoff_plan_payload(
    *,
    repo_plans: dict[str, Any],
    embargo_gap_days: int,
    model_snapshot_status: str,
    model_snapshot_date: str | None = None,
) -> dict[str, Any]:
    selected_repos = sorted(repo_id for repo_id, plan in repo_plans.items() if plan.get("clean_validation_ready"))
    return {
        "schema_version": "barcarolle.phase1.future_holdout_cutoff_plan.v1",
        "generated_at": now_utc(),
        "cutoff_primary_axis": "repo_task_time",
        "embargo_gap_days": embargo_gap_days,
        "model_snapshot_status": model_snapshot_status,
        "model_snapshot_date": model_snapshot_date,
        "selected_repos": selected_repos,
        "repo_plans": repo_plans,
        "repo_time_holdout_not_contamination_proof": model_snapshot_status == "unknown",
        "predictive_validity_established": False,
    }


def build_cutoff_plan(config: dict[str, Any]) -> dict[str, Any]:
    supply = build_supply(config)
    return cutoff_plan_payload(
        repo_plans=supply["repo_plans"],
        embargo_gap_days=int(config["cutoff_policy"]["embargo_gap_days"]),
        model_snapshot_status=supply["model_snapshot_status"],
        model_snapshot_date=supply["model_snapshot_date"],
    )


def cutoff_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Future Holdout Cutoff Plan",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Selected repos: `{', '.join(payload['selected_repos']) if payload['selected_repos'] else 'none'}`.",
        f"- Repo-time holdout not contamination-proof: `{str(payload['repo_time_holdout_not_contamination_proof']).lower()}`.",
        "",
        "| Repo | Ready | Size | T_compile_end | T_holdout_start | B_eval | H_future |",
        "| --- | --- | --- | --- | --- | ---: | ---: |",
    ]
    for repo_id, plan in payload["repo_plans"].items():
        lines.append(
            f"| `{repo_id}` | `{str(plan['clean_validation_ready']).lower()}` | `{plan['validation_size']}` | "
            f"`{plan['T_compile_end']}` | `{plan['T_holdout_start']}` | "
            f"{len(plan['b_eval_task_ids'])} | {len(plan['h_future_task_ids'])} |"
        )
    return "\n".join(lines)


def build_preregistration(config: dict[str, Any]) -> dict[str, Any]:
    plan_path = ROOT / "results" / "phase1_future_holdout_cutoff_plan.json"
    plan = read_json(plan_path) if plan_path.exists() else build_cutoff_plan(config)
    selected_repos = plan["selected_repos"]
    b_eval = []
    h_future = []
    for repo_id in selected_repos:
        repo_plan = plan["repo_plans"][repo_id]
        b_eval.extend(repo_plan["b_eval_task_ids"])
        h_future.extend(repo_plan["h_future_task_ids"])
    return {
        "schema_version": "barcarolle.phase1.future_holdout_preregistration.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "status": "frozen" if selected_repos else "blocked_no_clean_supply",
        "selected_repos": selected_repos,
        "repo_cutoffs": {repo_id: plan["repo_plans"][repo_id] for repo_id in selected_repos},
        "splits": {"b_eval": b_eval, "h_future": h_future},
        "adapters": config["adapters"]["ids"],
        "model_name": config["model_design"]["preferred_model"],
        "endpoint_rule": config["endpoint_rule"],
        "budget": config["budget"],
        "retry_policy": "single_attempt_per_adapter_per_task",
        "scoreability_policy": {
            "scoreable_terminal_statuses": ["verified_pass", "verified_fail"],
            "policy_violations_max": config["acceptance"]["policy_violations_max"],
            "non_scoreable_cells_max_per_split": config["acceptance"]["non_scoreable_cells_max_per_split"],
        },
        "predictor": {
            "primary": "adapter_level_unweighted_b_eval_pass_rate",
            "weighted_predictor": "diagnostic_only_when_strata_underpowered",
        },
        "baselines": ["Repo_unweighted", "Repo_stratified", "Historical_sidecar"],
        "metrics": [
            "MAE",
            "absolute_error_per_adapter",
            "scoreable_cell_counts",
            "policy_violation_counts",
            "non_scoreable_cell_counts",
            "cost_summary",
        ],
        "claim_thresholds": {
            "min_target_repos": config["acceptance"]["predictive_validity_claim_min_repos"],
            "min_holdout_scoreable_cells": config["acceptance"]["predictive_validity_claim_min_holdout_scoreable_cells"],
            "policy_violations_max": config["acceptance"]["policy_violations_max"],
            "must_beat_unweighted_baseline": True,
        },
        "holdout_tuning_forbidden": True,
        "predictive_validity_established": False,
    }


def preregistration_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Future Holdout Preregistration",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Status: `{payload['status']}`.",
            f"- Selected repos: `{', '.join(payload['selected_repos']) if payload['selected_repos'] else 'none'}`.",
            f"- B_eval tasks: `{len(payload['splits']['b_eval'])}`.",
            f"- H_future tasks: `{len(payload['splits']['h_future'])}`.",
            "- Holdout tuning forbidden: `true`.",
            "- Predictive validity established: `false`.",
        ]
    )


def build_two_repo_clean_supply(config: dict[str, Any]) -> dict[str, Any]:
    repos = [str(repo_id) for repo_id in config["repos"]]
    adapters = [str(adapter_id) for adapter_id in config["adapters"]["ids"]]
    boltons_cfg = config["existing_paid_evidence"]["boltons"]
    boltons_decision = read_json(config_path(boltons_cfg["decision"]))
    second_overlay = read_json(config_path(config["second_repo_clean_supply_overlay"]))
    second_repo_id = str(second_overlay["selected_repo_id"])
    second_b_eval_tasks = [str(task_id) for task_id in second_overlay.get("selected_b_eval_task_ids", [])]
    second_h_future_tasks = [str(task_id) for task_id in second_overlay.get("selected_h_future_task_ids", [])]
    planned_b_eval_cells = len(second_b_eval_tasks) * len(adapters)
    planned_h_future_cells = len(second_h_future_tasks) * len(adapters)
    existing_h_future_cells = int(boltons_decision.get("h_future_scoreable_cells") or boltons_cfg.get("h_future_scoreable_cells") or 0)
    existing_b_eval_cells = int(boltons_decision.get("b_eval_scoreable_cells") or boltons_cfg.get("b_eval_scoreable_cells") or 0)
    total_planned_h_future_capacity = existing_h_future_cells + planned_h_future_cells
    selected_repos = ["boltons", second_repo_id] if "boltons" in repos and second_repo_id in repos else repos
    blockers: list[str] = []
    if second_overlay.get("clean_supply_ready") is not True:
        blockers.append("second_repo_clean_supply_below_minimum")
    if len(selected_repos) < int(config["acceptance"]["min_target_repos"]):
        blockers.append("two_repo_min_target_repos_not_met")
    if total_planned_h_future_capacity < int(config["acceptance"]["min_holdout_scoreable_cells"]):
        blockers.append("min_holdout_scoreable_cells_not_met_if_second_repo_scoreable")
    if int(boltons_decision.get("policy_violation_count") or 0) > int(config["acceptance"]["policy_violations_max"]):
        blockers.append("existing_paid_policy_violation_count_exceeds_gate")
    return {
        "schema_version": "barcarolle.phase1.two_repo_future_holdout_clean_supply.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "selected_repos": selected_repos,
        "clean_supply_ready": not blockers,
        "existing_paid_evidence": {
            "boltons": {
                "decision": rel(config_path(boltons_cfg["decision"])),
                "primary_decision_label": boltons_decision.get("primary_decision_label"),
                "b_eval_prefix": boltons_cfg["b_eval_prefix"],
                "h_future_prefix": boltons_cfg["h_future_prefix"],
                "b_eval_scoreable_cells": existing_b_eval_cells,
                "h_future_scoreable_cells": existing_h_future_cells,
                "policy_violation_count": int(boltons_decision.get("policy_violation_count") or 0),
                "predictive_validity_established": bool(boltons_decision.get("predictive_validity_established")),
            }
        },
        "second_repo_clean_supply": {
            "repo_id": second_repo_id,
            "overlay": rel(config_path(config["second_repo_clean_supply_overlay"])),
            "clean_supply_ready": bool(second_overlay.get("clean_supply_ready")),
            "selected_b_eval_task_ids": second_b_eval_tasks,
            "selected_h_future_task_ids": second_h_future_tasks,
            "validation_size": second_overlay.get("cutoff_feasibility", {}).get("validation_size"),
            "T_compile_end": second_overlay.get("cutoff_feasibility", {}).get("T_compile_end"),
            "T_holdout_start": second_overlay.get("cutoff_feasibility", {}).get("T_holdout_start"),
        },
        "second_repo_planned_paid_prefixes": config["second_repo_planned_paid_prefixes"],
        "adapters": adapters,
        "planned_second_repo_b_eval_cells": planned_b_eval_cells,
        "planned_second_repo_h_future_cells": planned_h_future_cells,
        "total_h_future_scoreable_capacity_if_second_repo_scoreable": total_planned_h_future_capacity,
        "acceptance": config["acceptance"],
        "blockers": blockers,
        "paid_second_repo_acut_calls_made": False,
        "paid_acut_calls_made": False,
        "predictive_validity_established": False,
    }


def two_repo_preregistration_payload(config: dict[str, Any], clean_supply: dict[str, Any]) -> dict[str, Any]:
    status = "frozen" if clean_supply["clean_supply_ready"] else "blocked_clean_supply"
    return {
        "schema_version": "barcarolle.phase1.two_repo_future_holdout_preregistration.v1",
        "generated_at": now_utc(),
        "config": rel(config["_path"]),
        "status": status,
        "selected_repos": clean_supply["selected_repos"],
        "existing_paid_evidence": clean_supply["existing_paid_evidence"],
        "second_repo_planned_paid_prefixes": clean_supply["second_repo_planned_paid_prefixes"],
        "planned_second_repo_tasks": {
            "b_eval": clean_supply["second_repo_clean_supply"]["selected_b_eval_task_ids"],
            "h_future": clean_supply["second_repo_clean_supply"]["selected_h_future_task_ids"],
        },
        "planned_second_repo_cells": {
            "b_eval": clean_supply["planned_second_repo_b_eval_cells"],
            "h_future": clean_supply["planned_second_repo_h_future_cells"],
        },
        "total_h_future_scoreable_capacity_if_second_repo_scoreable": clean_supply[
            "total_h_future_scoreable_capacity_if_second_repo_scoreable"
        ],
        "acceptance": config["acceptance"],
        "adapters": clean_supply["adapters"],
        "holdout_tuning_forbidden": True,
        "paid_second_repo_acut_calls_made": False,
        "paid_acut_calls_made": False,
        "blockers": clean_supply["blockers"],
        "recommended_next_runbook": (
            "run_two_repo_preregistered_clean_future_holdout_paid_validation"
            if status == "frozen"
            else "expand_clean_supply_sources_or_add_manual_canaries"
        ),
        "predictive_validity_established": False,
    }


def two_repo_preregistration_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Two-Repo Future Holdout Preregistration",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Status: `{payload['status']}`.",
            f"- Selected repos: `{', '.join(payload['selected_repos'])}`.",
            f"- Planned second-repo B_eval tasks: `{', '.join(payload['planned_second_repo_tasks']['b_eval'])}`.",
            f"- Planned second-repo H_future tasks: `{', '.join(payload['planned_second_repo_tasks']['h_future'])}`.",
            f"- Existing Boltons H_future scoreable cells: `{payload['existing_paid_evidence']['boltons']['h_future_scoreable_cells']}`.",
            f"- Planned second-repo H_future cells: `{payload['planned_second_repo_cells']['h_future']}`.",
            f"- Total H_future capacity if second repo is scoreable: `{payload['total_h_future_scoreable_capacity_if_second_repo_scoreable']}`.",
            f"- Paid second-repo ACUT calls made: `{str(payload['paid_second_repo_acut_calls_made']).lower()}`.",
            f"- Holdout tuning forbidden: `{str(payload['holdout_tuning_forbidden']).lower()}`.",
            f"- Predictive validity established: `false`.",
            f"- Recommended next runbook: `{payload['recommended_next_runbook']}`.",
        ]
    )


def prefix_score_table(prefix: str) -> Path:
    return PHASE0_ROOT / "results" / f"{prefix}_score_table.csv"


def summarize_score_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    scoreable = [row for row in rows if str(row.get("scoreable_cell")).lower() == "true"]
    passes = [row for row in scoreable if row.get("terminal_status") == "verified_pass"]
    policy_violations = [row for row in rows if row.get("terminal_status") == "policy_violation"]
    by_adapter: dict[str, Any] = {}
    for adapter_id in sorted({row.get("adapter_id", "") for row in rows}):
        adapter_rows = [row for row in rows if row.get("adapter_id") == adapter_id]
        adapter_scoreable = [row for row in adapter_rows if str(row.get("scoreable_cell")).lower() == "true"]
        adapter_passes = [row for row in adapter_scoreable if row.get("terminal_status") == "verified_pass"]
        by_adapter[adapter_id] = {
            "cell_count": len(adapter_rows),
            "scoreable_cell_count": len(adapter_scoreable),
            "pass_count": len(adapter_passes),
            "pass_rate": round(len(adapter_passes) / len(adapter_scoreable), 6) if adapter_scoreable else None,
        }
    return {
        "cell_count": len(rows),
        "scoreable_cell_count": len(scoreable),
        "pass_count": len(passes),
        "pass_rate": round(len(passes) / len(scoreable), 6) if scoreable else None,
        "policy_violation_count": len(policy_violations),
        "non_scoreable_count": len(rows) - len(scoreable),
        "by_adapter": by_adapter,
    }


def paid_validation_decision_outcome(
    config: dict[str, Any],
    supply: dict[str, Any],
    *,
    b_summary: dict[str, Any],
    h_summary: dict[str, Any],
    policy_violation_count: int,
) -> dict[str, Any]:
    acceptance = config["acceptance"]
    selected_repos = list(supply.get("selected_repos", []))
    max_policy_violations = int(acceptance["policy_violations_max"])
    max_non_scoreable = int(acceptance["non_scoreable_cells_max_per_split"])
    min_repos = int(acceptance["predictive_validity_claim_min_repos"])
    min_holdout_scoreable = int(acceptance["predictive_validity_claim_min_holdout_scoreable_cells"])
    blockers: list[str] = []

    if policy_violation_count > max_policy_violations:
        blockers.append("policy_violation_count_exceeds_acceptance_gate")
        return {
            "primary_decision_label": "future_holdout_validation_blocked_policy_or_cost",
            "blockers": blockers,
            "recommended_next_runbook": "repair_workspace_acut_scoreability_or_cost_accounting",
            "predictive_validity_established": False,
        }

    if int(b_summary["non_scoreable_count"]) > max_non_scoreable or int(h_summary["non_scoreable_count"]) > max_non_scoreable:
        blockers.append("non_scoreable_cells_exceed_acceptance_gate")
        return {
            "primary_decision_label": "future_holdout_validation_blocked_non_scoreable_cells",
            "blockers": blockers,
            "recommended_next_runbook": "repair_workspace_acut_scoreability_or_cost_accounting",
            "predictive_validity_established": False,
        }

    if len(selected_repos) < min_repos:
        blockers.append("predictive_validity_min_target_repos_not_met")
    if int(h_summary["scoreable_cell_count"]) < min_holdout_scoreable:
        blockers.append("predictive_validity_min_holdout_scoreable_cells_not_met")
    if blockers:
        label = (
            "boltons_clean_future_holdout_pilot_complete_insufficient_sample"
            if selected_repos == ["boltons"]
            else "clean_future_holdout_pilot_complete_insufficient_sample"
        )
        return {
            "primary_decision_label": label,
            "blockers": blockers,
            "recommended_next_runbook": "mine_second_repo_clean_outcome_unseen_supply_for_two_repo_validation",
            "predictive_validity_established": False,
        }

    return {
        "primary_decision_label": "ready_for_phase1_predictive_validation_scaleup",
        "blockers": [],
        "recommended_next_runbook": "preregister_second_repo_clean_future_holdout_validation",
        "predictive_validity_established": False,
    }


def task_ids_from_supply(supply: dict[str, Any], split_name: str) -> list[str]:
    key = f"{split_name}_task_ids"
    task_ids: list[str] = []
    for repo_id in supply.get("selected_repos", []):
        plan = supply.get("repo_plans", {}).get(repo_id, {})
        task_ids.extend(str(task_id) for task_id in plan.get(key, []))
    return task_ids


def prefix_observed_or_conservative_cost(prefix: str) -> float:
    path = PHASE0_ROOT / "results" / f"{prefix}_cost_summary.json"
    if not path.exists():
        return 0.0
    summary = read_json(path)
    if "observed_or_conservative_estimated_cost_usd" in summary:
        return float(summary.get("observed_or_conservative_estimated_cost_usd") or 0.0)
    return float(summary.get("estimated_cost_usd") or 0.0)


def build_score_and_decision(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    supply_path = ROOT / "results" / "phase1_future_holdout_clean_supply.json"
    supply = read_json(supply_path) if supply_path.exists() else build_supply(config)
    cost = read_json(artifact_path(config, "cost_reconciliation")).get("totals", {})
    b_prefix = config["result_prefixes"]["b_eval"]
    h_prefix = config["result_prefixes"]["h_future"]
    b_path = prefix_score_table(b_prefix)
    h_path = prefix_score_table(h_prefix)

    if not supply["clean_supply_ready"]:
        metrics = {
            "schema_version": "barcarolle.phase1.future_holdout_prediction_metrics.v1",
            "generated_at": now_utc(),
            "status": "not_run_clean_supply_blocked",
            "b_eval": None,
            "h_future": None,
            "mae": None,
            "policy_violation_count": 0,
            "cost_summary": cost,
            "predictive_validity_established": False,
        }
        decision = {
            "schema_version": "barcarolle.phase1.future_holdout_decision.v1",
            "generated_at": now_utc(),
            "primary_decision_label": "future_holdout_supply_blocked",
            "paid_acut_calls_made": False,
            "selected_repos": [],
            "cutoff_primary_axis": "repo_task_time",
            "blockers": supply["blockers"],
            "b_eval_task_ids": [],
            "h_future_task_ids": [],
            "b_eval_scoreable_cells": 0,
            "h_future_scoreable_cells": 0,
            "policy_violation_count": 0,
            "observed_or_conservative_estimated_cost_usd": cost.get("observed_or_conservative_estimated_cost_usd"),
            "incremental_observed_or_conservative_estimated_cost_usd": 0.0,
            "predictive_validity_established": False,
            "production_ranking_status": "not_produced",
            "recommended_next_runbook": "mine_and_certify_fresh_outcome_unseen_tasks_for_future_holdout",
            "allowed_claims": [
                "future_holdout_design_preregistered",
                "repo_time_cutoff_policy_defined",
                "outcome_unseen_task_supply_audited",
                "future_holdout_supply_blocked",
                "insufficient_evidence_for_predictive_validation",
            ],
            "disallowed_claims": [
                "predictive_validity_established",
                "production_benchmark_ranking",
                "pure_harness_effect",
                "contamination_proof_evaluation_if_model_snapshot_unknown",
                "future_holdout_validity_if_holdout_used_for_tuning",
                "validation_grade_humanize_if_commit_fallback_only",
            ],
        }
        return metrics, decision

    if not b_path.exists() or not h_path.exists():
        b_eval_task_ids = []
        h_future_task_ids = []
        for repo_id in supply["selected_repos"]:
            plan = supply["repo_plans"].get(repo_id, {})
            b_eval_task_ids.extend(plan.get("b_eval_task_ids", []))
            h_future_task_ids.extend(plan.get("h_future_task_ids", []))
        metrics = {
            "schema_version": "barcarolle.phase1.future_holdout_prediction_metrics.v1",
            "generated_at": now_utc(),
            "status": "not_run_paid_validation_deferred",
            "b_eval": None,
            "h_future": None,
            "mae": None,
            "policy_violation_count": 0,
            "cost_summary": cost,
            "predictive_validity_established": False,
        }
        decision = {
            "schema_version": "barcarolle.phase1.future_holdout_decision.v1",
            "generated_at": now_utc(),
            "primary_decision_label": "future_holdout_design_frozen_ready_for_paid_validation",
            "paid_acut_calls_made": False,
            "selected_repos": supply["selected_repos"],
            "cutoff_primary_axis": "repo_task_time",
            "blockers": [],
            "b_eval_task_ids": b_eval_task_ids,
            "h_future_task_ids": h_future_task_ids,
            "b_eval_scoreable_cells": 0,
            "h_future_scoreable_cells": 0,
            "policy_violation_count": 0,
            "incremental_observed_or_conservative_estimated_cost_usd": 0.0,
            "predictive_validity_established": False,
            "production_ranking_status": "not_produced",
            "recommended_next_runbook": "run_preregistered_clean_future_holdout_paid_validation",
        }
        return metrics, decision

    b_summary = summarize_score_rows(read_csv(b_path))
    h_summary = summarize_score_rows(read_csv(h_path))
    adapter_errors = {}
    for adapter_id, b_adapter in b_summary["by_adapter"].items():
        h_adapter = h_summary["by_adapter"].get(adapter_id, {})
        if b_adapter.get("pass_rate") is None or h_adapter.get("pass_rate") is None:
            adapter_errors[adapter_id] = None
        else:
            adapter_errors[adapter_id] = abs(float(b_adapter["pass_rate"]) - float(h_adapter["pass_rate"]))
    errors = [value for value in adapter_errors.values() if value is not None]
    metrics = {
        "schema_version": "barcarolle.phase1.future_holdout_prediction_metrics.v1",
        "generated_at": now_utc(),
        "status": "computed",
        "b_eval": b_summary,
        "h_future": h_summary,
        "absolute_error_per_adapter": adapter_errors,
        "mae": round(sum(errors) / len(errors), 6) if errors else None,
        "policy_violation_count": b_summary["policy_violation_count"] + h_summary["policy_violation_count"],
        "cost_summary": cost,
        "predictive_validity_established": False,
    }
    outcome = paid_validation_decision_outcome(
        config,
        supply,
        b_summary=b_summary,
        h_summary=h_summary,
        policy_violation_count=metrics["policy_violation_count"],
    )
    incremental_cost = round(prefix_observed_or_conservative_cost(b_prefix) + prefix_observed_or_conservative_cost(h_prefix), 8)
    decision = {
        "schema_version": "barcarolle.phase1.future_holdout_decision.v1",
        "generated_at": now_utc(),
        "primary_decision_label": outcome["primary_decision_label"],
        "paid_acut_calls_made": True,
        "selected_repos": supply["selected_repos"],
        "cutoff_primary_axis": "repo_task_time",
        "blockers": outcome["blockers"],
        "b_eval_task_ids": task_ids_from_supply(supply, "b_eval"),
        "h_future_task_ids": task_ids_from_supply(supply, "h_future"),
        "b_eval_scoreable_cells": b_summary["scoreable_cell_count"],
        "h_future_scoreable_cells": h_summary["scoreable_cell_count"],
        "policy_violation_count": metrics["policy_violation_count"],
        "observed_or_conservative_estimated_cost_usd": cost.get("observed_or_conservative_estimated_cost_usd"),
        "incremental_observed_or_conservative_estimated_cost_usd": incremental_cost,
        "predictive_validity_established": outcome["predictive_validity_established"],
        "production_ranking_status": "not_produced",
        "recommended_next_runbook": outcome["recommended_next_runbook"],
        "allowed_claims": [
            "preregistered_clean_future_holdout_paid_validation_run",
            "boltons_clean_future_holdout_pilot_complete",
            "workspace_acut_future_holdout_cells_scoreable",
            "same_endpoint_model_different_cli_harnesses",
            "observed_or_conservative_cost_accounting",
            "insufficient_evidence_for_predictive_validation",
            "ready_for_second_repo_clean_supply_scaleup",
        ],
        "disallowed_claims": [
            "predictive_validity_established_without_acceptance_thresholds",
            "production_benchmark_ranking",
            "pure_harness_effect",
            "contamination_proof_evaluation_if_model_snapshot_unknown",
            "clean_future_holdout_validated_without_paid_holdout_run",
        ],
    }
    return metrics, decision


def prediction_metrics_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Future Holdout Prediction Metrics",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Status: `{payload['status']}`.",
            f"- B_eval score data: `{payload['b_eval']}`.",
            f"- H_future score data: `{payload['h_future']}`.",
            f"- MAE: `{payload['mae']}`.",
            f"- Policy violations: `{payload['policy_violation_count']}`.",
            f"- Observed-or-conservative cost USD: `{(payload.get('cost_summary') or {}).get('observed_or_conservative_estimated_cost_usd')}`.",
            "- Predictive validity established: `false`.",
        ]
    )


def decision_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Future Holdout Decision",
        "",
        f"Primary decision: `{payload['primary_decision_label']}`.",
        "",
        f"- Paid ACUT calls made: `{str(payload.get('paid_acut_calls_made', False)).lower()}`.",
        f"- Selected repos: `{', '.join(payload.get('selected_repos', [])) if payload.get('selected_repos') else 'none'}`.",
        f"- Cutoff primary axis: `{payload.get('cutoff_primary_axis', 'repo_task_time')}`.",
        f"- B_eval tasks: `{', '.join(payload.get('b_eval_task_ids', [])) if payload.get('b_eval_task_ids') else 'none'}`.",
        f"- H_future tasks: `{', '.join(payload.get('h_future_task_ids', [])) if payload.get('h_future_task_ids') else 'none'}`.",
        f"- B_eval scoreable cells: `{payload.get('b_eval_scoreable_cells', 0)}`.",
        f"- H_future scoreable cells: `{payload.get('h_future_scoreable_cells', 0)}`.",
        f"- Policy violations: `{payload.get('policy_violation_count', 0)}`.",
        f"- Observed-or-conservative cost USD: `{payload.get('observed_or_conservative_estimated_cost_usd')}`.",
        f"- Incremental observed-or-conservative cost USD: `{payload.get('incremental_observed_or_conservative_estimated_cost_usd')}`.",
        f"- Predictive validity established: `{str(payload['predictive_validity_established']).lower()}`.",
        f"- Production ranking: `{payload.get('production_ranking_status', 'not_produced')}`.",
        f"- Recommended next runbook: `{payload['recommended_next_runbook']}`.",
    ]
    if payload.get("blockers"):
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{item}`" for item in payload["blockers"])
    return "\n".join(lines)


def run_audit_supply(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    payload = build_supply(config)
    write_json(ROOT / "results" / "phase1_future_holdout_clean_supply.json", payload)
    write_text(ROOT / "reports" / "phase1_future_holdout_clean_supply.md", clean_supply_report(payload))
    return payload


def run_design_cutoff(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    payload = build_cutoff_plan(config)
    write_json(ROOT / "results" / "phase1_future_holdout_cutoff_plan.json", payload)
    write_text(ROOT / "reports" / "phase1_future_holdout_cutoff_plan.md", cutoff_report(payload))
    return payload


def run_preregister(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    payload = build_preregistration(config)
    write_json(ROOT / "results" / "phase1_future_holdout_preregistration.json", payload)
    write_text(ROOT / "reports" / "phase1_future_holdout_preregistration.md", preregistration_report(payload))
    return payload


def run_score(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(Path(args.config))
    metrics, decision = build_score_and_decision(config)
    write_json(ROOT / "results" / "phase1_future_holdout_prediction_metrics.json", metrics)
    write_text(ROOT / "reports" / "phase1_future_holdout_prediction_metrics.md", prediction_metrics_report(metrics))
    write_json(ROOT / "results" / "phase1_future_holdout_decision.json", decision)
    write_text(ROOT / "reports" / "phase1_future_holdout_decision.md", decision_report(decision))
    return decision


def run_two_repo_preregister(args: argparse.Namespace) -> dict[str, Any]:
    config = load_two_repo_config(Path(args.config))
    clean_supply = build_two_repo_clean_supply(config)
    preregistration = two_repo_preregistration_payload(config, clean_supply)
    write_json(configured_output_path(config, "clean_supply"), clean_supply)
    write_json(configured_output_path(config, "preregistration"), preregistration)
    write_text(configured_output_path(config, "preregistration_report"), two_repo_preregistration_report(preregistration))
    return preregistration


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1 future-holdout design and scoring helper.")
    parser.add_argument("command", choices=["audit-supply", "design-cutoff", "preregister", "score", "two-repo-preregister"])
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()
    runners = {
        "audit-supply": run_audit_supply,
        "design-cutoff": run_design_cutoff,
        "preregister": run_preregister,
        "score": run_score,
        "two-repo-preregister": run_two_repo_preregister,
    }
    payload = runners[args.command](args)
    print(json.dumps({"status": payload.get("primary_decision_label") or payload.get("status") or "ok"}, sort_keys=True))


if __name__ == "__main__":
    main()
