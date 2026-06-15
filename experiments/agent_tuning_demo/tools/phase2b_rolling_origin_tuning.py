from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tuning_artifacts import ARTIFACT_SCHEMA_VERSION, materialize_artifact, validate_artifact, with_computed_hash


ROOT = Path(__file__).resolve().parents[3]
PHASE0_TOOLS = ROOT / "experiments" / "phase0_headroom" / "tools"
for path in [ROOT, PHASE0_TOOLS]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from experiments.demo_common import costs as demo_costs  # noqa: E402
from experiments.demo_common import workspace_inputs  # noqa: E402
import selection_snapshot  # noqa: E402
import workspace_acut_run as workspace  # noqa: E402


DEMO_REL = Path("experiments/agent_tuning_demo")
RESULTS = ROOT / DEMO_REL / "results"
REPORTS = ROOT / DEMO_REL / "reports"
CANDIDATE_DIR = RESULTS / "phase2b_candidate_artifacts"
CHOSEN_DIR = RESULTS / "phase2b_chosen_artifact"
RAW_PROPOSER_ROOT = ROOT / "experiments" / "phase0_headroom" / "results" / "raw" / "agent_tuning_demo_phase2b" / "proposer"
PHASE2B_RESULT_PREFIX = "agent_tuning_demo_phase2b"

MODEL = "gpt-5.4-mini"
TARGET_AGENT_ID = "kilo_gpt_5_4_mini"
TARGET_AGENT_NAME = "Kilo + GPT low-cost"
TARGET_SURFACE = "repo_AGENTS_md"
TARGET_ARTIFACT_TYPE = "agents_md_appendix"
TARGET_ARTIFACT_PATH = "AGENTS.md"
TARGET_REPO = "mahmoud/boltons"
TARGET_REPO_ID = "boltons"
SELECTED_WINDOW_ID = "boltons_time_ordered_w1_train2015_2018_dev2019_2020_future2022_2023"

MAX_PROPOSER_CALLS = 8
MAX_CANDIDATES = 2
MAX_REFLECTION_ITERATIONS = 2
AGENT_PAID_CELLS_MAX = 72
TOTAL_COST_SOFT_CAP_USD = 8.0
SCOREABLE_STATUSES = {"verified_pass", "verified_fail"}

PHASE2B_SCORE_FIELDS = [
    "window_id",
    "stage",
    "condition",
    "candidate_id",
    "agent_id",
    "reviewer_name",
    "harness",
    "model",
    "task_id",
    "terminal_status",
    "scoreable_cell",
    "verified_pass",
    "failure_category",
    "latency_seconds",
    "estimated_cost_usd",
    "usage_observed",
    "cost_observation_kind",
    "usage_source",
    "artifact_hash",
    "patch_sha256",
]


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    if not rows:
        return ["_No rows._"]
    lines = [
        "| " + " | ".join(label for label, _key in columns) + " |",
        "| " + " | ".join("---" for _label, _key in columns) + " |",
    ]
    for row in rows:
        values = [str(row.get(key, "")) for _label, key in columns]
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in values) + " |")
    return lines


def bool_from_cell(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def load_task_table() -> list[dict[str, str]]:
    rows = selection_snapshot.selector_task_table_rows()
    return [row for row in rows if row["target_repo"] == TARGET_REPO]


def ordered_tasks_by_role(role: str) -> list[str]:
    rows = [row for row in load_task_table() if row["stage_role"] == role]
    return [row["task_id"] for row in sorted(rows, key=lambda row: (row["task_time"], row["task_id"]))]


def selected_window_task_ids() -> dict[str, list[str]]:
    selection = ordered_tasks_by_role("selection")
    holdout = ordered_tasks_by_role("holdout")
    return {
        "train": selection[:10],
        "dev": selection[10:16],
        "bridge_excluded": selection[16:],
        "future": holdout,
    }


def score_rows_for_target() -> list[dict[str, str]]:
    rows = selection_snapshot.selection_score_rows() + selection_snapshot.holdout_score_rows()
    return [row for row in rows if row["agent_id"] == TARGET_AGENT_ID]


def score_by_task() -> dict[str, dict[str, str]]:
    return {row["task_id"]: row for row in score_rows_for_target()}


def failure_label(row: dict[str, str] | None) -> str:
    if not row:
        return "missing_baseline_outcome"
    status = row.get("terminal_status", "")
    failure = row.get("failure_category", "")
    if bool_from_cell(row.get("verified_pass")):
        return "verified_pass"
    if status == "acut_harness_error" or "timeout" in failure or "exceeded budget" in failure:
        return "timeout_or_context_exhaustion"
    if status == "invalid_output" or "no meaningful change" in failure:
        return "invalid_or_no_diff"
    if "edited tests" in failure:
        return "overbroad_patch"
    if "hidden verifier failure" in failure:
        return "wrong_api_semantics"
    return "unknown_failure"


def outcome_metrics(task_ids: list[str]) -> dict[str, Any]:
    scores = score_by_task()
    rows = [scores.get(task_id) for task_id in task_ids]
    present = [row for row in rows if row is not None]
    scoreable = [row for row in present if row and row.get("terminal_status") in SCOREABLE_STATUSES]
    pass_count = sum(1 for row in scoreable if bool_from_cell(row.get("verified_pass")))
    label_counts: dict[str, int] = {}
    for row in present:
        label = failure_label(row)
        label_counts[label] = label_counts.get(label, 0) + 1
    return {
        "task_count": len(task_ids),
        "baseline_rows_present": len(present),
        "scoreable_count": len(scoreable),
        "invalid_or_unscoreable_count": len(present) - len(scoreable),
        "verified_pass_count": pass_count,
        "pass_rate": None if not scoreable else round(pass_count / len(scoreable), 4),
        "label_counts": label_counts,
        "missing_task_ids": [task_id for task_id, row in zip(task_ids, rows) if row is None],
    }


def time_range_for(task_ids: list[str]) -> dict[str, str | None]:
    task_rows = {row["task_id"]: row for row in load_task_table()}
    times = [task_rows[task_id]["task_time"] for task_id in task_ids if task_id in task_rows]
    return {"start": min(times) if times else None, "end": max(times) if times else None}


def build_window(train_count: int, dev_count: int, *, selected: bool, reason: str) -> dict[str, Any]:
    selection = ordered_tasks_by_role("selection")
    holdout = ordered_tasks_by_role("holdout")
    train_ids = selection[:train_count]
    dev_ids = selection[train_count : train_count + dev_count]
    bridge_ids = selection[train_count + dev_count :]
    future_ids = holdout
    train_metrics = outcome_metrics(train_ids)
    dev_metrics = outcome_metrics(dev_ids)
    future_metrics = outcome_metrics(future_ids)
    future_hash = sha256_text("\n".join(future_ids))
    headroom_pass = (
        dev_metrics["pass_rate"] is not None
        and 0.20 <= dev_metrics["pass_rate"] <= 0.70
        and future_metrics["pass_rate"] is not None
        and 0.20 <= future_metrics["pass_rate"] <= 0.70
    )
    recurring_failures = sum(
        count
        for label, count in train_metrics["label_counts"].items()
        if label not in {"verified_pass", "missing_baseline_outcome"}
    )
    return {
        "window_id": SELECTED_WINDOW_ID if selected else f"boltons_time_ordered_train{train_count}_dev{dev_count}_future_holdout",
        "target_repo": TARGET_REPO,
        "target_agent_id": TARGET_AGENT_ID,
        "mode": "single_time_ordered_future_validation",
        "selected_for_protocol": selected,
        "selection_reason": reason,
        "task_counts": {
            "train": len(train_ids),
            "dev": len(dev_ids),
            "future": len(future_ids),
            "bridge_excluded": len(bridge_ids),
        },
        "time_ranges": {
            "train": time_range_for(train_ids),
            "dev": time_range_for(dev_ids),
            "future": time_range_for(future_ids),
        },
        "train_task_ids": train_ids,
        "dev_task_ids": dev_ids,
        "bridge_excluded_task_ids": bridge_ids,
        "future_task_ids_revealed": False,
        "future_task_ids_sha256": future_hash,
        "baseline_headroom": {
            "train": train_metrics,
            "dev": dev_metrics,
            "future": future_metrics,
            "target_range": [0.20, 0.70],
            "headroom_pass": headroom_pass,
        },
        "recurring_failure_labels": train_metrics["label_counts"],
        "recurring_failure_count": recurring_failures,
        "estimated_paid_cells": {
            "fresh_dev_baseline": len(dev_ids),
            "dev_tuned_candidates": len(dev_ids) * MAX_CANDIDATES,
            "fresh_future_baseline_if_dev_gate_passes": len(future_ids),
            "future_tuned_if_dev_gate_passes": len(future_ids),
            "total_if_future_runs": len(dev_ids) * (1 + MAX_CANDIDATES) + len(future_ids) * 2,
        },
        "infrastructure_risk": "moderate: Kilo low-cost had 2 unscoreable Selection cells, but Holdout coverage was 10/10 scoreable.",
        "hidden_oracle_leakage_risk": "controlled: proposer input is train-only; future IDs are hashed until artifact freeze.",
    }


def inventory_summary() -> dict[str, Any]:
    selection_inventory = selection_snapshot.predictive_validity_window_inventory()
    phase1_metrics = read_json(ROOT / "experiments" / "phase1_compiler" / "results" / "phase1_three_repo_paid_validation_metrics.json")
    boltons_selection = outcome_metrics(ordered_tasks_by_role("selection"))
    boltons_holdout = outcome_metrics(ordered_tasks_by_role("holdout"))
    return {
        "selection_snapshot_boltons_kilo_low_cost": {
            "selection_task_count": boltons_selection["task_count"],
            "selection_baseline_pass_rate": boltons_selection["pass_rate"],
            "selection_scoreable_count": boltons_selection["scoreable_count"],
            "holdout_task_count": boltons_holdout["task_count"],
            "holdout_baseline_pass_rate": boltons_holdout["pass_rate"],
            "holdout_scoreable_count": boltons_holdout["scoreable_count"],
            "usable_for_phase2b_default_path": True,
        },
        "phase1_candidate_repos": selection_inventory.get("candidate_repos", {}),
        "phase1_three_repo_paid_metrics": {
            repo: {
                "B_eval_pass_rate": data["B_eval"]["pass_rate"],
                "H_future_pass_rate": data["H_future"]["pass_rate"],
                "scoreability_rate": data["B_eval"]["scoreability_rate"],
            }
            for repo, data in phase1_metrics.get("per_repo", {}).items()
        },
        "attrs_click_selection_decision": (
            "Do not select attrs/click for the default Phase 2b paid path: current Agent Tuning tooling "
            "and Kilo AGENTS.md action preflight are prepared for the frozen boltons package map, "
            "while attrs/click need packaging and injection-runner repair before paid artifact tuning."
        ),
    }


def claim_reframe_payload() -> dict[str, Any]:
    return {
        "schema_version": "barcarolle.agent_tuning_demo.phase2b_claim_reframe.v1",
        "generated_at": iso_now(),
        "phase2a_relabel": {
            "terminal_state": "phase2_success_no_holdout_regression",
            "action_level_preflight_success": True,
            "end_to_end_artifact_validation_pilot": True,
            "selection_dev_matrix": "1/4 -> 1/4",
            "holdout_matrix": "5/6 -> 5/6",
            "selection_dev_paired_net_wins": 0,
            "holdout_paired_net_wins": 0,
            "tuned_improvement_proven": False,
            "real_reflection_lm_tuner_used": False,
            "proposer_used": "gepa_optimize_anything_custom_local_proposer",
        },
        "phase2b_success_criteria": {
            "time_ordered_or_rolling_origin_validation_required": True,
            "llm_driven_artifact_proposer_required": True,
            "deterministic_local_template_counts_as_real_tuner": False,
            "selection_dev_gate": {
                "paired_net_wins": "> 0",
                "invalid_or_unscoreable_tuned": "<= baseline",
                "cost_per_task": "<= baseline * 1.50 unless explicitly justified",
            },
            "future_green": "aggregate future paired net wins > 0 and no material regression",
            "future_yellow": "aggregate future paired net wins == 0 with no material regression and improved behavior labels",
            "future_red": "aggregate future paired net wins < 0 or materially worse invalid/timeout behavior",
        },
        "supported_claims_if_successful": [
            "A narrow, repo-local Kilo AGENTS.md appendix can be proposed from past boltons failures by an LLM-driven proposer.",
            "Under one or more frozen time-ordered windows, selected artifacts can be evaluated before/after under fixed Agent and verifier conditions.",
            "If future paired net wins are positive, Phase 2b supports demo-level artifact-tuning improvement for this target slice.",
        ],
        "unsupported_claims_even_if_successful": [
            "statistical significance",
            "cross-repo generalization",
            "model fine-tuning",
            "full opaque-Agent tuning",
            "production-ready Agent tuning system",
            "public leaderboard ranking",
            "predictive validity beyond the frozen task windows",
        ],
    }


def write_claim_reframe() -> None:
    payload = claim_reframe_payload()
    write_json(RESULTS / "phase2b_claim_and_phase2a_reframe.json", payload)
    lines = [
        "# Agent Tuning Phase 2b claim and Phase 2a reframe",
        "",
        f"Generated at: `{payload['generated_at']}`.",
        "",
        "## Phase 2a reframe",
        "",
        "Phase 2a is recorded as an action-level injection and before/after validation pilot. It did not prove tuned improvement: Selection-dev stayed `1/4 -> 1/4`, Holdout stayed `5/6 -> 5/6`, and paired net wins were `0` on both splits.",
        "",
        "Phase 2a also did not run a real LLM-driven tuner. It used GEPA `optimize_anything` with a custom deterministic local proposer and no reflection LM. A deterministic local template or local proposer must not be presented as a real LLM-driven artifact tuner.",
        "",
        "## Frozen Phase 2b gates",
        "",
        "- Use rolling-origin or time-ordered future validation.",
        "- Use an LLM-driven artifact proposer; otherwise stop or label the run as non-LLM control.",
        "- Require positive Selection-dev paired net wins before future validation.",
        "- Require future non-regression at minimum; positive paired net wins are preferred.",
        "- Track cost, latency, invalid/unscoreable cells, and failure-label shifts.",
        "",
        "## Supported if successful",
        "",
        *[f"- {claim}" for claim in payload["supported_claims_if_successful"]],
        "",
        "## Still unsupported",
        "",
        *[f"- {claim}" for claim in payload["unsupported_claims_even_if_successful"]],
        "",
    ]
    write_text(REPORTS / "phase2b_claim_and_phase2a_reframe_zh.md", "\n".join(lines))


def task_supply_audit_payload() -> dict[str, Any]:
    windows = [
        build_window(10, 6, selected=True, reason="best single-window default path: dev pass rate is inside target range and future Holdout pass rate is 6/10"),
        build_window(12, 4, selected=False, reason="rejected: dev baseline is above the preferred headroom range"),
        build_window(16, 4, selected=False, reason="rejected: dev baseline is saturated after excluding an unscoreable row"),
    ]
    selected_windows = [window for window in windows if window["selected_for_protocol"]]
    selected = selected_windows[0]
    rolling_origin_feasible = len(
        [
            window
            for window in windows
            if window["baseline_headroom"]["headroom_pass"] and window["recurring_failure_count"] >= 3
        ]
    ) >= 2
    readiness = bool(
        selected["baseline_headroom"]["headroom_pass"]
        and selected["recurring_failure_count"] >= 3
        and selected["estimated_paid_cells"]["total_if_future_runs"] <= AGENT_PAID_CELLS_MAX
    )
    return {
        "schema_version": "barcarolle.agent_tuning_demo.phase2b_task_supply_headroom_audit.v1",
        "generated_at": iso_now(),
        "paid_cells_run": 0,
        "inventory": inventory_summary(),
        "candidate_windows": windows,
        "readiness_decision": {
            "status": "pass_time_ordered_single_window" if readiness else "blocked",
            "paid_tuning_allowed_after_protocol_freeze": readiness,
            "rolling_origin_multi_window_claim_feasible": rolling_origin_feasible,
            "time_ordered_future_validation_feasible": readiness,
            "recommended_window_id": selected["window_id"] if readiness else None,
            "recommended_agent": TARGET_AGENT_ID if readiness else None,
            "recommended_surface": TARGET_SURFACE if readiness else None,
            "limitation": (
                "Current Kilo low-cost boltons supply supports one strong time-ordered future-validation window, "
                "not a two-window rolling-origin claim. Later middle slices are saturated or too sparse."
            ),
        },
    }


def write_task_supply_audit() -> None:
    payload = task_supply_audit_payload()
    write_json(RESULTS / "phase2b_task_supply_headroom_audit.json", payload)
    write_json(RESULTS / "phase2b_candidate_windows.json", {"generated_at": payload["generated_at"], "candidate_windows": payload["candidate_windows"]})
    rows = [
        {
            "Window": window["window_id"],
            "Selected": window["selected_for_protocol"],
            "Train": window["task_counts"]["train"],
            "Dev": window["task_counts"]["dev"],
            "Future": window["task_counts"]["future"],
            "Dev pass": window["baseline_headroom"]["dev"]["pass_rate"],
            "Future pass": window["baseline_headroom"]["future"]["pass_rate"],
            "Cells": window["estimated_paid_cells"]["total_if_future_runs"],
            "Decision": window["selection_reason"],
        }
        for window in payload["candidate_windows"]
    ]
    decision = payload["readiness_decision"]
    lines = [
        "# Agent Tuning Phase 2b task-supply and headroom audit",
        "",
        f"Generated at: `{payload['generated_at']}`.",
        "",
        "Paid cells run in this package: `0`.",
        "",
        f"Readiness decision: `{decision['status']}`.",
        f"Recommended Agent/surface: `{decision['recommended_agent']}` / `{decision['recommended_surface']}`.",
        f"Rolling-origin multi-window claim feasible now: `{decision['rolling_origin_multi_window_claim_feasible']}`.",
        f"Time-ordered future validation feasible now: `{decision['time_ordered_future_validation_feasible']}`.",
        "",
        "## Candidate windows",
        "",
        *markdown_table(rows, [("Window", "Window"), ("Selected", "Selected"), ("Train", "Train"), ("Dev", "Dev"), ("Future", "Future"), ("Dev pass", "Dev pass"), ("Future pass", "Future pass"), ("Paid cells", "Cells"), ("Decision", "Decision")]),
        "",
        "Future task IDs are not listed here; only counts, time ranges, and SHA-256 digests are committed before artifact freeze.",
        "",
        "## Inventory notes",
        "",
        "- `mahmoud/boltons` with Kilo low-cost has 20 Selection rows and 10 Holdout rows; Holdout baseline headroom is `6/10`.",
        "- `python-attrs/attrs` and `click` have Phase 1 task supply and generic adapter evidence, but they are not selected for this paid path because the Phase 2 artifact-injection runner and Kilo AGENTS.md action preflight are prepared for the boltons package map.",
        f"- Limitation: {decision['limitation']}",
        "",
    ]
    write_text(REPORTS / "phase2b_task_supply_headroom_audit_zh.md", "\n".join(lines))


def phase2b_protocol_payload() -> dict[str, Any]:
    audit = read_json(RESULTS / "phase2b_task_supply_headroom_audit.json")
    if not audit["readiness_decision"]["paid_tuning_allowed_after_protocol_freeze"]:
        raise RuntimeError("task-supply/headroom audit did not pass")
    selected = next(window for window in audit["candidate_windows"] if window["selected_for_protocol"])
    planned_dev_cells = selected["task_counts"]["dev"] * (1 + MAX_CANDIDATES)
    planned_future_cells = selected["task_counts"]["future"] * 2
    return {
        "schema_version": "barcarolle.agent_tuning_demo.phase2b_protocol.v1",
        "generated_at": iso_now(),
        "status": "frozen_before_llm_proposer_or_paid_agent_cells",
        "selected_windows": [
            {
                "window_id": selected["window_id"],
                "mode": selected["mode"],
                "target_repo": selected["target_repo"],
                "train_task_ids": selected["train_task_ids"],
                "dev_task_ids": selected["dev_task_ids"],
                "future_task_count": selected["task_counts"]["future"],
                "future_task_ids_sha256": selected["future_task_ids_sha256"],
                "future_task_ids_withheld_until_artifact_freeze": True,
                "bridge_excluded_task_count": selected["task_counts"]["bridge_excluded"],
                "baseline_headroom": selected["baseline_headroom"],
            }
        ],
        "target_agent": {
            "agent_id": TARGET_AGENT_ID,
            "reviewer_name": TARGET_AGENT_NAME,
            "harness": "kilo",
            "model": MODEL,
        },
        "artifact_surface": {
            "surface": TARGET_SURFACE,
            "artifact_type": TARGET_ARTIFACT_TYPE,
            "workspace_path": TARGET_ARTIFACT_PATH,
            "reason": "Kilo AGENTS.md action-level preflight already passed in Phase 2 and remains the most reliable deployable surface.",
        },
        "proposer": {
            "primary": "GEPA-shaped reflective LLM proposer",
            "fallback": "Phoenix-style LLM rule proposer",
            "non_llm_local_template_allowed_as_tuning_result": False,
            "max_proposer_calls": MAX_PROPOSER_CALLS,
            "max_candidates_per_window": MAX_CANDIDATES,
            "max_reflection_iterations_per_window": MAX_REFLECTION_ITERATIONS,
            "proposer_input_visibility": "train failure labels and sanitized train summaries only",
        },
        "paid_caps": {
            "llm_proposer_calls_max": MAX_PROPOSER_CALLS,
            "agent_paid_cells_max": AGENT_PAID_CELLS_MAX,
            "total_estimated_cost_soft_cap_usd": TOTAL_COST_SOFT_CAP_USD,
            "planned_agent_cells": {
                "dev": planned_dev_cells,
                "future_if_dev_gate_passes": planned_future_cells,
                "total_if_future_runs": planned_dev_cells + planned_future_cells,
            },
        },
        "success_gates": {
            "selection_dev_gate": {
                "paired_net_wins": "> 0",
                "invalid_or_unscoreable_tuned": "<= baseline",
                "cost_per_task": "<= baseline * 1.50 unless explicitly justified",
            },
            "future_gate_green": "aggregate_future_paired_net_wins > 0 and no window has material regression",
            "future_gate_yellow": "aggregate_future_paired_net_wins == 0, no material regression, and behavior/failure labels improve",
            "future_gate_red": "aggregate_future_paired_net_wins < 0 or tuned invalid/timeout materially worse",
        },
        "leakage_controls": {
            "proposer_sees_train_only": True,
            "dev_scores_select_artifact": True,
            "future_tasks_logs_outcomes_hidden_until_artifact_hash_freeze": True,
            "candidate_artifact_may_contain_future_derived_content": False,
            "candidate_records_require_holdout_derived_false": True,
            "raw_prompts_completions_stored_only_under_ignored_paths": True,
        },
        "claim_boundary": {
            "min_windows_for_rolling_origin_claim": 2,
            "selected_window_count": 1,
            "rolling_origin_claim_allowed": False,
            "time_ordered_future_demo_claim_allowed_if_gates_pass": True,
        },
        "stop_conditions": [
            "Stop before LLM proposer if LLM_BASE_URL or LLM_API_KEY is missing after sourcing ~/.zshrc.",
            "Stop or label as non-LLM control if no LLM proposal/reflection step runs.",
            "Stop before future validation if no dev candidate has positive paired net wins.",
            "Stop if paid-cell or cost caps would be exceeded.",
            "Stop if any candidate contains dev/future task IDs or future-derived content.",
        ],
    }


def write_protocol() -> None:
    payload = phase2b_protocol_payload()
    write_json(RESULTS / "phase2b_protocol.json", payload)
    window = payload["selected_windows"][0]
    lines = [
        "# Agent Tuning Phase 2b protocol",
        "",
        f"Generated at: `{payload['generated_at']}`.",
        "",
        f"Status: `{payload['status']}`.",
        "",
        "## Frozen route",
        "",
        f"- Proposer: `{payload['proposer']['primary']}`",
        f"- Target Agent: `{TARGET_AGENT_NAME}` (`{TARGET_AGENT_ID}`)",
        f"- Artifact surface: Kilo repo `{TARGET_ARTIFACT_PATH}` appendix",
        f"- Window: `{window['window_id']}`",
        f"- Train/dev/future counts: `{len(window['train_task_ids'])}` / `{len(window['dev_task_ids'])}` / `{window['future_task_count']}`",
        f"- Future task IDs withheld: `{window['future_task_ids_withheld_until_artifact_freeze']}`",
        "",
        "## Paid caps",
        "",
        f"- LLM proposer calls max: `{MAX_PROPOSER_CALLS}`",
        f"- Agent paid cells max: `{AGENT_PAID_CELLS_MAX}`",
        f"- Planned cells if future runs: `{payload['paid_caps']['planned_agent_cells']['total_if_future_runs']}`",
        f"- Soft cost cap: `${TOTAL_COST_SOFT_CAP_USD}`",
        "",
        "## Gates",
        "",
        "- Dev requires positive paired net wins before future validation.",
        "- Future green requires positive aggregate paired net wins and no material regression.",
        "- A single selected window can support only a time-ordered demo claim, not a multi-window rolling-origin claim.",
        "",
        "## Stop conditions",
        "",
        *[f"- {condition}" for condition in payload["stop_conditions"]],
        "",
    ]
    write_text(REPORTS / "phase2b_protocol_zh.md", "\n".join(lines))


def protocol_or_raise() -> dict[str, Any]:
    path = RESULTS / "phase2b_protocol.json"
    if not path.exists():
        raise RuntimeError("phase2b_protocol.json is required")
    payload = read_json(path)
    if payload.get("status") != "frozen_before_llm_proposer_or_paid_agent_cells":
        raise RuntimeError("phase2b protocol is not frozen")
    return payload


def require_endpoint_env() -> None:
    missing = [name for name in ["LLM_BASE_URL", "LLM_API_KEY"] if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"missing endpoint env: {', '.join(missing)}")


def train_evidence_rows() -> list[dict[str, Any]]:
    protocol = protocol_or_raise()
    train_ids = set(protocol["selected_windows"][0]["train_task_ids"])
    forbidden = set(protocol["selected_windows"][0]["dev_task_ids"]) | set(selected_window_task_ids()["future"])
    score_lookup = score_by_task()
    packages = workspace_inputs.package_map(selection_snapshot.selection_config())
    rows = []
    for task_id in protocol["selected_windows"][0]["train_task_ids"]:
        if task_id in forbidden:
            raise RuntimeError("train evidence overlaps dev/future")
        score = score_lookup[task_id]
        package = packages[task_id]
        rows.append(
            {
                "task_id": task_id,
                "failure_label": failure_label(score),
                "terminal_status": score["terminal_status"],
                "verified_pass": bool_from_cell(score["verified_pass"]),
                "failure_category": score["failure_category"],
                "task_summary": package.solver_facing_statement[:700],
                "editable_paths": package.allowed_code_paths,
                "public_test_paths": package.test_paths,
                "patch_sha256": score["patch_sha256"],
                "visible_to_proposer": True,
                "holdout_derived": False,
            }
        )
    if {row["task_id"] for row in rows} != train_ids:
        raise RuntimeError("train evidence row mismatch")
    return rows


def proposer_prompt(evidence: list[dict[str, Any]]) -> str:
    failure_rows = [row for row in evidence if row["failure_label"] != "verified_pass"]
    label_counts: dict[str, int] = {}
    for row in evidence:
        label_counts[row["failure_label"]] = label_counts.get(row["failure_label"], 0) + 1
    payload = {
        "objective": "Propose up to two concise Kilo AGENTS.md appendices for future boltons repair tasks.",
        "hard_constraints": [
            "Use only the train evidence in this JSON.",
            "Do not mention dev, holdout, future, hidden verifier, or any task ID not present in train evidence.",
            "Do not include raw prompts, raw completions, hidden tests, exact patches, or solution code.",
            "The appendix must be general repair guidance, not task-specific instructions.",
            "Return JSON only with a top-level candidates array.",
        ],
        "output_schema": {
            "candidates": [
                {
                    "artifact_id_suffix": "short-kebab-case",
                    "title": "short title",
                    "appendix_markdown": "the AGENTS.md appendix text to append",
                    "targeted_failure_labels": ["wrong_api_semantics"],
                    "evidence_task_ids": ["train task ids only"],
                    "expected_behavior_change": "one sentence",
                    "rollback_plan": "one sentence",
                }
            ]
        },
        "label_counts": label_counts,
        "train_failure_evidence": failure_rows,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def post_chat_completion(messages: list[dict[str, str]], raw_dir: Path, call_index: int) -> str:
    require_endpoint_env()
    base_url = os.environ["LLM_BASE_URL"].rstrip("/")
    url = f"{base_url}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }
    request_path = raw_dir / f"request_{call_index}.json"
    response_path = raw_dir / f"response_{call_index}.json"
    request_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {os.environ['LLM_API_KEY']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            response_text = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="replace")
        response_path.write_text(error_text, encoding="utf-8")
        raise RuntimeError(f"LLM proposer HTTP {exc.code}: {error_text[:500]}") from exc
    response_path.write_text(response_text, encoding="utf-8")
    parsed = json.loads(response_text)
    content = parsed["choices"][0]["message"].get("content") or ""
    (raw_dir / f"completion_text_{call_index}.txt").write_text(content, encoding="utf-8")
    (raw_dir / f"metadata_{call_index}.json").write_text(
        json.dumps(
            {
                "duration_seconds": round(time.monotonic() - started, 3),
                "usage": parsed.get("usage"),
                "model": parsed.get("model"),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return content


def extract_json_payload(text: str) -> dict[str, Any]:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found in proposer completion")
    return json.loads(text[start : end + 1])


def artifact_from_llm_candidate(candidate: dict[str, Any], index: int, train_ids: set[str], forbidden_ids: set[str]) -> dict[str, Any]:
    suffix = re.sub(r"[^a-z0-9-]+", "-", str(candidate.get("artifact_id_suffix") or f"candidate-{index}").lower()).strip("-")
    if not suffix:
        suffix = f"candidate-{index}"
    content = str(candidate.get("appendix_markdown") or "").strip()
    if len(content) < 80:
        raise ValueError("candidate appendix_markdown is too short")
    evidence_task_ids = [str(task_id) for task_id in candidate.get("evidence_task_ids") or []]
    if not evidence_task_ids:
        raise ValueError("candidate is missing evidence_task_ids")
    if not set(evidence_task_ids).issubset(train_ids):
        raise ValueError("candidate evidence_task_ids are not train-only")
    serialized = json.dumps(candidate, ensure_ascii=False)
    forbidden_hits = sorted(task_id for task_id in forbidden_ids if task_id in serialized or task_id in content)
    if forbidden_hits:
        raise ValueError(f"candidate contains non-train task ids: {forbidden_hits[:3]}")
    artifact = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "artifact_id": f"phase2b-llm-{suffix}",
        "artifact_type": TARGET_ARTIFACT_TYPE,
        "target_agent": "kilo_workspace",
        "changed_files": [TARGET_ARTIFACT_PATH],
        "files": [
            {
                "workspace_relative_path": TARGET_ARTIFACT_PATH,
                "content": content + "\n",
                "write_mode": "append",
            }
        ],
        "hash": "",
        "intended_effect": str(candidate.get("expected_behavior_change") or "Improve Kilo repair behavior on recurring train failure labels."),
        "rollback_plan": str(candidate.get("rollback_plan") or "Remove the AGENTS.md appendix or discard the solver workspace."),
        "optimizer_source": "phase2b_llm_gepa_shaped_reflective_proposer",
        "visible_to_optimizer": True,
        "holdout_derived": False,
        "targeted_failure_labels": [str(label) for label in candidate.get("targeted_failure_labels") or []],
        "evidence_task_ids": evidence_task_ids,
        "expected_behavior_change": str(candidate.get("expected_behavior_change") or ""),
    }
    artifact = with_computed_hash(artifact)
    validate_artifact(artifact)
    return artifact


def run_llm_proposer() -> dict[str, Any]:
    protocol = protocol_or_raise()
    evidence = train_evidence_rows()
    train_ids = {row["task_id"] for row in evidence}
    forbidden_ids = set(protocol["selected_windows"][0]["dev_task_ids"]) | set(selected_window_task_ids()["future"])
    raw_dir = RAW_PROPOSER_ROOT / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_dir.mkdir(parents=True, exist_ok=True)
    prompt = proposer_prompt(evidence)
    (raw_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    system = (
        "You are a careful coding-agent artifact proposer. Return JSON only. "
        "Use only the provided train evidence. Do not use future or holdout information."
    )
    calls = 0
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    completion = post_chat_completion(messages, raw_dir, 1)
    calls += 1
    try:
        parsed = extract_json_payload(completion)
    except Exception:
        repair = (
            "The previous answer was not valid JSON matching the requested schema. "
            "Return only a JSON object with a candidates array. Do not add commentary.\n\n"
            f"Previous answer:\n{completion[:4000]}"
        )
        completion = post_chat_completion(messages + [{"role": "assistant", "content": completion}, {"role": "user", "content": repair}], raw_dir, 2)
        calls += 1
        parsed = extract_json_payload(completion)
    initial_candidates = parsed.get("candidates") if isinstance(parsed.get("candidates"), list) else []
    reflection_prompt = json.dumps(
        {
            "task": "Reflect on the initial candidates and return revised JSON candidates.",
            "reflection_criteria": [
                "Keep evidence_task_ids train-only.",
                "Prefer guidance that generalizes across recurring wrong_api_semantics and timeout_or_context_exhaustion labels.",
                "Avoid overfitting to one module name if a broader repair discipline would be safer.",
                "Keep the appendix concise and deployable as AGENTS.md text.",
                "Return JSON only with the same candidates schema.",
            ],
            "label_counts": outcome_metrics(protocol["selected_windows"][0]["train_task_ids"])["label_counts"],
            "initial_candidates": initial_candidates,
        },
        indent=2,
        ensure_ascii=False,
    )
    try:
        reflection_completion = post_chat_completion(
            messages
            + [
                {"role": "assistant", "content": completion},
                {"role": "user", "content": reflection_prompt},
            ],
            raw_dir,
            calls + 1,
        )
        calls += 1
        reflected = extract_json_payload(reflection_completion)
        if reflected.get("candidates"):
            parsed = reflected
            reflection_used = True
        else:
            reflection_used = False
    except Exception as exc:
        (raw_dir / "reflection_error.txt").write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        reflection_used = False
    candidates = parsed.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise RuntimeError("LLM proposer returned no candidates")
    artifacts = []
    for index, candidate in enumerate(candidates[:MAX_CANDIDATES], start=1):
        if not isinstance(candidate, dict):
            continue
        artifacts.append(artifact_from_llm_candidate(candidate, index, train_ids, forbidden_ids))
    if not artifacts:
        raise RuntimeError("LLM proposer returned no valid candidates")
    return {
        "raw_dir": raw_dir,
        "proposer_calls": calls,
        "train_evidence_count": len(evidence),
        "label_counts": outcome_metrics(protocol["selected_windows"][0]["train_task_ids"])["label_counts"],
        "candidate_artifacts": artifacts[:MAX_CANDIDATES],
        "reflection_used": reflection_used,
    }


def write_proposer_integration() -> None:
    try:
        result = run_llm_proposer()
        status = "llm_proposer_complete"
        error = None
        artifacts = result["candidate_artifacts"]
        raw_dir = result["raw_dir"]
        proposer_calls = result["proposer_calls"]
        label_counts = result["label_counts"]
        train_evidence_count = result["train_evidence_count"]
        reflection_used = result["reflection_used"]
    except Exception as exc:
        status = "llm_proposer_blocked"
        error = f"{type(exc).__name__}: {exc}"
        artifacts = []
        raw_dir = None
        proposer_calls = 0
        label_counts = {}
        train_evidence_count = 0
        reflection_used = False
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    for artifact in artifacts:
        write_json(CANDIDATE_DIR / f"{artifact['artifact_id']}.json", artifact)
        write_text(CANDIDATE_DIR / f"{artifact['artifact_id']}.md", artifact["files"][0]["content"])
    candidate_payload = {
        "schema_version": "barcarolle.agent_tuning_demo.phase2b_candidate_artifacts.v1",
        "generated_at": iso_now(),
        "status": status,
        "proposer": "phase2b_llm_gepa_shaped_reflective_proposer",
        "candidate_count": len(artifacts),
        "candidate_artifacts": artifacts,
        "holdout_derived_candidates_rejected": True,
    }
    integration_payload = {
        "schema_version": "barcarolle.agent_tuning_demo.phase2b_proposer_integration.v1",
        "generated_at": candidate_payload["generated_at"],
        "status": status,
        "error": error,
        "llm_proposer_used": status == "llm_proposer_complete",
        "proposer_calls": proposer_calls,
        "reflection_iterations_used": 1 if reflection_used else 0,
        "proposer_calls_cap": MAX_PROPOSER_CALLS,
        "raw_prompt_completion_path_ignored": None if raw_dir is None else display_path(raw_dir),
        "raw_prompt_completion_committed": False,
        "endpoint_rule": "LLM_BASE_URL plus LLM_API_KEY; no fallback auth",
        "train_evidence_count": train_evidence_count,
        "label_counts": label_counts,
        "candidate_hashes": [artifact["hash"] for artifact in artifacts],
        "future_or_dev_task_ids_in_proposer_input": False,
    }
    write_json(RESULTS / "phase2b_candidate_artifacts.json", candidate_payload)
    write_json(RESULTS / "phase2b_proposer_integration.json", integration_payload)
    rows = [
        {
            "Candidate": artifact["artifact_id"],
            "Hash": artifact["hash"][:24],
            "Labels": ",".join(artifact.get("targeted_failure_labels") or []),
            "Evidence": len(artifact.get("evidence_task_ids") or []),
            "Chars": len(artifact["files"][0]["content"]),
        }
        for artifact in artifacts
    ]
    lines = [
        "# Agent Tuning Phase 2b proposer integration",
        "",
        f"Generated at: `{integration_payload['generated_at']}`.",
        "",
        f"Status: `{status}`.",
        f"LLM proposer used: `{integration_payload['llm_proposer_used']}`.",
        f"Proposer calls: `{proposer_calls}` / `{MAX_PROPOSER_CALLS}`.",
        f"Reflection iterations used: `{integration_payload['reflection_iterations_used']}`.",
        "- Raw prompt/completion content is stored only under ignored `experiments/phase0_headroom/results/raw/...` paths.",
        "",
        "## Candidates",
        "",
        *markdown_table(rows, [("Candidate", "Candidate"), ("Hash", "Hash"), ("Labels", "Labels"), ("Evidence tasks", "Evidence"), ("Chars", "Chars")]),
        "",
    ]
    if error:
        lines.extend(["## Blocker", "", error, ""])
    write_text(REPORTS / "phase2b_proposer_integration_zh.md", "\n".join(lines))


def load_candidate_artifacts() -> list[dict[str, Any]]:
    payload = read_json(RESULTS / "phase2b_candidate_artifacts.json")
    artifacts = payload.get("candidate_artifacts") or []
    for artifact in artifacts:
        validate_artifact(artifact)
    return artifacts


def run_workspace_cell_with_artifact(
    package: workspace.TaskPackage,
    adapter: workspace.AdapterConfig,
    run_id: str,
    stage: str,
    condition: str,
    artifact: dict[str, Any] | None,
) -> workspace.CellResult:
    exp = ROOT / "experiments" / "phase0_headroom"
    namespace = workspace.artifact_namespace(f"{PHASE2B_RESULT_PREFIX}_{stage}_{condition}", adapter.adapter_id)
    raw_dir = exp / workspace.RAW_REL / namespace / run_id
    workspace_root = exp / workspace.WORKSPACE_REL / namespace / run_id
    solver_workspace = workspace_root / "solver"
    verifier_workspace = workspace_root / "verifier"
    workspace.archive_tree(package.source_repo, package.base_commit, solver_workspace)
    injection_record = None
    if artifact is not None:
        injection_record = materialize_artifact(solver_workspace, artifact, run_id=run_id, surface=TARGET_SURFACE)
    workspace.initialize_workspace_git(solver_workspace)
    statement_file = workspace.write_statement_file(solver_workspace, package)
    raw_dir.mkdir(parents=True, exist_ok=True)

    command = workspace.render_command(
        adapter.command_template,
        workspace=solver_workspace,
        statement_file=statement_file,
        task_id=package.task_id,
        run_id=run_id,
        raw_dir=raw_dir,
        timeout_seconds=adapter.timeout_seconds,
    )
    start = time.monotonic()
    acut = workspace.run_command(command, solver_workspace, timeout=adapter.timeout_seconds, env=os.environ.copy())
    latency = round(time.monotonic() - start, 3)
    stdout_path = raw_dir / "acut_stdout.txt"
    stderr_path = raw_dir / "acut_stderr.txt"
    stdout_path.write_text(acut.stdout, encoding="utf-8")
    stderr_path.write_text(acut.stderr, encoding="utf-8")
    patch_text = workspace.capture_diff(solver_workspace)
    patch_path = raw_dir / "submission.patch"
    patch_path.write_text(patch_text, encoding="utf-8")
    patch_sha = workspace.sha256_file(patch_path)
    base_submission = {
        "schema_version": "barcarolle.workspace_acut_submission.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "adapter_id": adapter.adapter_id,
        "acut_id": adapter.acut_id,
        "harness_name": adapter.harness_name,
        "model_or_agent_name": adapter.model_or_agent_name,
        "command_template_source": adapter.command_template_source,
        "endpoint_proof_status": adapter.endpoint_proof_status,
        "task_id": package.task_id,
        "repo_id": package.repo_id,
        "split": stage,
        "patch_source": "git_diff_after_workspace_run",
        "patch_sha256": patch_sha,
        "latency_seconds": latency,
        "adapter_timed_out": acut.timed_out,
        "raw_artifacts": {
            "stdout": str(stdout_path.relative_to(exp)),
            "stderr": str(stderr_path.relative_to(exp)),
            "patch": str(patch_path.relative_to(exp)),
        },
        "task_package_metadata": workspace.package_submission_metadata(package),
        "phase2b_condition": condition,
        "phase2b_artifact_hash": None if artifact is None else artifact["hash"],
        "phase2b_injection_record": injection_record,
    }
    verifier = {
        "schema_version": "barcarolle.workspace_acut_verifier.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "adapter_id": adapter.adapter_id,
        "acut_id": adapter.acut_id,
        "harness_name": adapter.harness_name,
        "model_or_agent_name": adapter.model_or_agent_name,
        "command_template_source": adapter.command_template_source,
        "endpoint_proof_status": adapter.endpoint_proof_status,
        "task_id": package.task_id,
        "repo_id": package.repo_id,
        "split": stage,
        "fresh_workspace": False,
        "status": "invalid_output",
        "verifier_exit_code": None,
        "harness_error": None,
        "phase2b_condition": condition,
        "phase2b_artifact_hash": None if artifact is None else artifact["hash"],
    }
    if acut.returncode != 0:
        submission = {**base_submission, "status": "acut_harness_error", "acut_exit_code": acut.returncode}
        verifier.update({"status": "acut_harness_error", "harness_error": "acut_command_failed", "acut_exit_code": acut.returncode, "adapter_timed_out": acut.timed_out})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)
    if not patch_text.strip():
        submission = {**base_submission, "status": "invalid_output", "acut_exit_code": acut.returncode}
        verifier.update({"status": "invalid_output", "harness_error": "empty_workspace_diff"})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)

    changed = workspace.changed_paths(solver_workspace)
    submission = {**base_submission, "status": "submitted", "acut_exit_code": acut.returncode, "changed_paths": changed}
    violation, violating_paths = workspace.policy_violation(changed, package)
    if violation:
        verifier.update({"status": "policy_violation", "harness_error": violation, "changed_paths": violating_paths})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)

    workspace.archive_tree(package.source_repo, package.base_commit, verifier_workspace)
    workspace.initialize_workspace_git(verifier_workspace)
    applied, apply_error = workspace.apply_patch(verifier_workspace, patch_path)
    if not applied:
        verifier.update({"status": "harness_error", "harness_error": "captured_patch_did_not_apply", "patch_apply_error_tail": apply_error})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)
    injected, inject_error = workspace.inject_hidden_oracle(ROOT, package, verifier_workspace, raw_dir)
    if not injected:
        verifier.update({"status": "harness_error", "harness_error": inject_error})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)

    verify_stdout = raw_dir / "verifier_stdout.txt"
    verify_stderr = raw_dir / "verifier_stderr.txt"
    verify = workspace.run_command(package.verifier_command, verifier_workspace, timeout=package.timeout_seconds, env=workspace.verifier_env_for(package, verifier_workspace))
    verify_stdout.write_text(verify.stdout, encoding="utf-8")
    verify_stderr.write_text(verify.stderr, encoding="utf-8")
    verifier.update(
        {
            "status": "timeout" if verify.timed_out else "verified_pass" if verify.returncode == 0 else "verified_fail",
            "verifier_exit_code": verify.returncode,
            "duration_seconds": round(verify.duration_seconds, 3),
            "fresh_workspace": True,
            "raw_artifacts": {
                "stdout": str(verify_stdout.relative_to(exp)),
                "stderr": str(verify_stderr.relative_to(exp)),
            },
        }
    )
    return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)


def score_row_for_result(
    result: workspace.CellResult,
    candidate_config: dict[str, Any],
    config: dict[str, Any],
    stage: str,
    condition: str,
    candidate_id: str,
    artifact_hash: str | None,
) -> dict[str, Any]:
    usage = demo_costs.usage_from_submission(result.submission)
    usage_observed, estimated_cost, _token_counts = demo_costs.estimate_cost(usage, candidate_config["model"], config)
    cost_meta = demo_costs.cost_observation_metadata(usage_observed)
    terminal = result.verifier.get("status") or result.submission.get("status")
    return {
        "window_id": SELECTED_WINDOW_ID,
        "stage": stage,
        "condition": condition,
        "candidate_id": candidate_id,
        "agent_id": candidate_config["agent_id"],
        "reviewer_name": candidate_config["reviewer_name"],
        "harness": candidate_config["harness"],
        "model": candidate_config["model"],
        "task_id": result.submission["task_id"],
        "terminal_status": terminal,
        "scoreable_cell": terminal in SCOREABLE_STATUSES,
        "verified_pass": terminal == "verified_pass",
        "failure_category": demo_costs.failure_category(result.verifier, result.submission),
        "latency_seconds": result.submission.get("latency_seconds", ""),
        "estimated_cost_usd": estimated_cost,
        "usage_observed": usage_observed,
        "cost_observation_kind": cost_meta["cost_observation_kind"],
        "usage_source": cost_meta["usage_source"],
        "artifact_hash": artifact_hash or "",
        "patch_sha256": result.submission.get("patch_sha256", ""),
    }


def condition_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scoreable = [row for row in rows if bool_from_cell(row.get("scoreable_cell"))]
    invalid = [row for row in rows if not bool_from_cell(row.get("scoreable_cell"))]
    costs = [float(row.get("estimated_cost_usd") or 0.0) for row in rows]
    latencies = [float(row.get("latency_seconds") or 0.0) for row in rows if row.get("latency_seconds") not in {"", None}]
    return {
        "cells": len(rows),
        "scoreable_cells": len(scoreable),
        "invalid_or_unscoreable_cells": len(invalid),
        "verified_pass_count": sum(1 for row in scoreable if bool_from_cell(row.get("verified_pass"))),
        "pass_rate": None if not scoreable else round(sum(1 for row in scoreable if bool_from_cell(row.get("verified_pass"))) / len(scoreable), 4),
        "estimated_cost_usd": round(sum(costs), 8),
        "median_latency_seconds": None if not latencies else sorted(latencies)[len(latencies) // 2],
    }


def paired_summary(rows: list[dict[str, Any]], tuned_condition: str) -> dict[str, Any]:
    baseline_rows = [row for row in rows if row["condition"] == "baseline"]
    tuned_rows = [row for row in rows if row["condition"] == tuned_condition]
    baseline = {row["task_id"]: row for row in baseline_rows}
    tuned = {row["task_id"]: row for row in tuned_rows}
    common_ids = sorted(set(baseline) & set(tuned))
    improved = [task_id for task_id in common_ids if bool_from_cell(tuned[task_id]["verified_pass"]) and not bool_from_cell(baseline[task_id]["verified_pass"])]
    regressed = [task_id for task_id in common_ids if bool_from_cell(baseline[task_id]["verified_pass"]) and not bool_from_cell(tuned[task_id]["verified_pass"])]
    matrix = [
        {
            "task_id": task_id,
            "baseline_status": baseline[task_id]["terminal_status"],
            "baseline_pass": bool_from_cell(baseline[task_id]["verified_pass"]),
            "tuned_status": tuned[task_id]["terminal_status"],
            "tuned_pass": bool_from_cell(tuned[task_id]["verified_pass"]),
        }
        for task_id in common_ids
    ]
    baseline_metrics = condition_metrics(baseline_rows)
    tuned_metrics = condition_metrics(tuned_rows)
    baseline_cost_per_task = baseline_metrics["estimated_cost_usd"] / baseline_metrics["cells"] if baseline_metrics["cells"] else None
    tuned_cost_per_task = tuned_metrics["estimated_cost_usd"] / tuned_metrics["cells"] if tuned_metrics["cells"] else None
    cost_ratio = None if not baseline_cost_per_task or tuned_cost_per_task is None else round(tuned_cost_per_task / baseline_cost_per_task, 4)
    paired_net_wins = len(improved) - len(regressed)
    return {
        "candidate_condition": tuned_condition,
        "paired_task_count": len(common_ids),
        "improved_task_ids": improved,
        "regressed_task_ids": regressed,
        "paired_net_wins": paired_net_wins,
        "matrix": matrix,
        "conditions": {"baseline": baseline_metrics, "tuned": tuned_metrics},
        "cost_ratio_vs_baseline_per_task": cost_ratio,
        "dev_gate_pass": bool(
            paired_net_wins > 0
            and tuned_metrics["invalid_or_unscoreable_cells"] <= baseline_metrics["invalid_or_unscoreable_cells"]
            and (cost_ratio is None or cost_ratio <= 1.5)
        ),
    }


def run_eval_stage(stage: str) -> dict[str, Any]:
    require_endpoint_env()
    protocol = protocol_or_raise()
    config = selection_snapshot.selection_config()
    candidate_config = workspace_inputs.candidate_by_id(config)[TARGET_AGENT_ID]
    adapter = workspace_inputs.adapter_config_for(config, candidate_config, command_template_source="agent_tuning_demo_selection_snapshot")
    packages = workspace_inputs.package_map(config)
    artifacts = load_candidate_artifacts()
    if not artifacts:
        raise RuntimeError("no candidate artifacts available")
    if stage == "dev_eval":
        task_ids = protocol["selected_windows"][0]["dev_task_ids"]
        conditions: list[tuple[str, str, dict[str, Any] | None]] = [("baseline", "", None)]
        conditions.extend((f"tuned_candidate_{idx}", artifact["artifact_id"], artifact) for idx, artifact in enumerate(artifacts, start=1))
        output_csv = RESULTS / "phase2b_dev_eval.csv"
    elif stage == "future_validation":
        chosen = read_json(RESULTS / "phase2b_chosen_artifact.json")
        task_ids = chosen["future_task_ids_revealed_after_freeze"]
        artifact = read_json(CHOSEN_DIR / "artifact.json")
        validate_artifact(artifact)
        conditions = [("baseline", "", None), ("tuned", artifact["artifact_id"], artifact)]
        output_csv = RESULTS / "phase2b_future_validation.csv"
    else:
        raise ValueError(f"unknown stage: {stage}")

    rows = read_csv_rows(output_csv)
    seen = {(row["condition"], row["task_id"]) for row in rows}
    for condition, candidate_id, artifact in conditions:
        for task_id in task_ids:
            if (condition, task_id) in seen:
                continue
            package = replace(packages[task_id], split=stage)
            run_id = f"phase2b_{stage}__{condition}__{TARGET_AGENT_ID}__{task_id}"
            result = run_workspace_cell_with_artifact(package, adapter, run_id, stage, condition, artifact)
            row = score_row_for_result(
                result,
                candidate_config,
                config,
                stage,
                condition,
                candidate_id,
                None if artifact is None else artifact["hash"],
            )
            rows.append(row)
            seen.add((condition, task_id))
            write_csv(output_csv, rows, PHASE2B_SCORE_FIELDS)
    write_csv(output_csv, rows, PHASE2B_SCORE_FIELDS)
    return summarize_stage(stage, rows, artifacts)


def summarize_stage(stage: str, rows: list[dict[str, Any]], artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    if stage == "dev_eval":
        candidate_summaries = []
        for idx, artifact in enumerate(artifacts, start=1):
            condition = f"tuned_candidate_{idx}"
            summary = paired_summary(rows, condition)
            summary["artifact_id"] = artifact["artifact_id"]
            summary["artifact_hash"] = artifact["hash"]
            candidate_summaries.append(summary)
        passing = [summary for summary in candidate_summaries if summary["dev_gate_pass"]]
        chosen = sorted(passing, key=lambda item: (-item["paired_net_wins"], item["conditions"]["tuned"]["invalid_or_unscoreable_cells"], item["cost_ratio_vs_baseline_per_task"] or 999))[0] if passing else None
        payload = {
            "schema_version": "barcarolle.agent_tuning_demo.phase2b_dev_eval_summary.v1",
            "generated_at": iso_now(),
            "stage": stage,
            "window_id": SELECTED_WINDOW_ID,
            "paid_cells": len(rows),
            "estimated_cost_usd": round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in rows), 8),
            "candidate_summaries": candidate_summaries,
            "future_gate_decision": "run_future_validation" if chosen else "stop_dev_gate_not_positive",
            "chosen_artifact_hash": None if not chosen else chosen["artifact_hash"],
            "chosen_candidate_condition": None if not chosen else chosen["candidate_condition"],
        }
        write_json(RESULTS / "phase2b_dev_eval_summary.json", payload)
        if chosen:
            write_chosen_artifact(chosen, artifacts)
        write_dev_report(payload)
        return payload
    summary = paired_summary(rows, "tuned")
    payload = {
        "schema_version": "barcarolle.agent_tuning_demo.phase2b_future_validation_summary.v1",
        "generated_at": iso_now(),
        "stage": stage,
        "window_id": SELECTED_WINDOW_ID,
        "status": "complete",
        "paid_cells": len(rows),
        "estimated_cost_usd": round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in rows), 8),
        "paired": summary,
    }
    write_json(RESULTS / "phase2b_future_validation_summary.json", payload)
    write_future_report(payload)
    return payload


def write_chosen_artifact(chosen_summary: dict[str, Any], artifacts: list[dict[str, Any]]) -> None:
    artifact = next(artifact for artifact in artifacts if artifact["hash"] == chosen_summary["artifact_hash"])
    validate_artifact(artifact)
    CHOSEN_DIR.mkdir(parents=True, exist_ok=True)
    write_json(CHOSEN_DIR / "artifact.json", artifact)
    write_text(CHOSEN_DIR / "AGENTS_appendix.md", artifact["files"][0]["content"])
    future_ids = selected_window_task_ids()["future"]
    payload = {
        "schema_version": "barcarolle.agent_tuning_demo.phase2b_chosen_artifact.v1",
        "generated_at": iso_now(),
        "status": "frozen_future_gate_passed",
        "window_id": SELECTED_WINDOW_ID,
        "artifact_id": artifact["artifact_id"],
        "artifact_hash": artifact["hash"],
        "artifact_path": display_path(CHOSEN_DIR / "artifact.json"),
        "appendix_path": display_path(CHOSEN_DIR / "AGENTS_appendix.md"),
        "dev_summary": chosen_summary,
        "future_task_ids_revealed_after_freeze": future_ids,
        "future_task_ids_revealed_after_artifact_hash": artifact["hash"],
        "gate_to_run_future": True,
        "leakage_audit": {
            "holdout_derived": artifact["holdout_derived"],
            "visible_to_optimizer": artifact["visible_to_optimizer"],
            "future_task_ids_used_before_freeze": False,
        },
    }
    write_json(RESULTS / "phase2b_chosen_artifact.json", payload)


def write_dev_report(payload: dict[str, Any]) -> None:
    rows = [
        {
            "Candidate": summary["candidate_condition"],
            "Pass": summary["conditions"]["tuned"]["verified_pass_count"],
            "Scoreable": summary["conditions"]["tuned"]["scoreable_cells"],
            "Invalid": summary["conditions"]["tuned"]["invalid_or_unscoreable_cells"],
            "Net wins": summary["paired_net_wins"],
            "Cost ratio": summary["cost_ratio_vs_baseline_per_task"],
            "Gate": summary["dev_gate_pass"],
        }
        for summary in payload["candidate_summaries"]
    ]
    lines = [
        "# Agent Tuning Phase 2b dev evaluation",
        "",
        f"Generated at: `{payload['generated_at']}`.",
        "",
        f"- Paid cells: `{payload['paid_cells']}`",
        f"- Estimated cost: `${payload['estimated_cost_usd']}`",
        f"- Future gate decision: `{payload['future_gate_decision']}`",
        f"- Chosen artifact hash: `{payload['chosen_artifact_hash']}`",
        "",
        "## Candidate results",
        "",
        *markdown_table(rows, [("Candidate", "Candidate"), ("Pass", "Pass"), ("Scoreable", "Scoreable"), ("Invalid", "Invalid"), ("Net wins", "Net wins"), ("Cost ratio", "Cost ratio"), ("Gate", "Gate")]),
        "",
    ]
    for summary in payload["candidate_summaries"]:
        lines.extend(
            [
                f"## Pair matrix: {summary['candidate_condition']}",
                "",
                *markdown_table(summary["matrix"], [("Task", "task_id"), ("Baseline", "baseline_status"), ("Baseline pass", "baseline_pass"), ("Tuned", "tuned_status"), ("Tuned pass", "tuned_pass")]),
                "",
            ]
        )
    write_text(REPORTS / "phase2b_dev_eval_zh.md", "\n".join(lines))


def write_future_report(payload: dict[str, Any]) -> None:
    paired = payload.get("paired") or {}
    rows = [
        {
            "Condition": condition,
            "Pass": data["verified_pass_count"],
            "Scoreable": data["scoreable_cells"],
            "Invalid": data["invalid_or_unscoreable_cells"],
            "Cost": data["estimated_cost_usd"],
            "Latency": data["median_latency_seconds"],
        }
        for condition, data in paired.get("conditions", {}).items()
    ]
    lines = [
        "# Agent Tuning Phase 2b future validation",
        "",
        f"Generated at: `{payload['generated_at']}`.",
        "",
        f"Status: `{payload.get('status')}`.",
        f"- Paid cells: `{payload.get('paid_cells', 0)}`",
        f"- Estimated cost: `${payload.get('estimated_cost_usd', 0)}`",
        f"- Paired net wins: `{paired.get('paired_net_wins')}`",
        "",
        *markdown_table(rows, [("Condition", "Condition"), ("Pass", "Pass"), ("Scoreable", "Scoreable"), ("Invalid", "Invalid"), ("Cost", "Cost"), ("Median latency", "Latency")]),
        "",
        "## Pair matrix",
        "",
        *markdown_table(paired.get("matrix", []), [("Task", "task_id"), ("Baseline", "baseline_status"), ("Baseline pass", "baseline_pass"), ("Tuned", "tuned_status"), ("Tuned pass", "tuned_pass")]),
        "",
    ]
    write_text(REPORTS / "phase2b_future_validation_zh.md", "\n".join(lines))


def run_dev_eval() -> None:
    proposer = read_json(RESULTS / "phase2b_proposer_integration.json")
    if proposer.get("status") != "llm_proposer_complete":
        payload = {
            "schema_version": "barcarolle.agent_tuning_demo.phase2b_dev_eval_summary.v1",
            "generated_at": iso_now(),
            "stage": "dev_eval",
            "window_id": SELECTED_WINDOW_ID,
            "paid_cells": 0,
            "estimated_cost_usd": 0.0,
            "candidate_summaries": [],
            "future_gate_decision": "stop_llm_proposer_blocked",
            "chosen_artifact_hash": None,
        }
        write_csv(RESULTS / "phase2b_dev_eval.csv", [], PHASE2B_SCORE_FIELDS)
        write_json(RESULTS / "phase2b_dev_eval_summary.json", payload)
        write_dev_report(payload)
        return
    run_eval_stage("dev_eval")


def run_future_validation() -> None:
    dev = read_json(RESULTS / "phase2b_dev_eval_summary.json")
    if dev.get("future_gate_decision") != "run_future_validation":
        payload = {
            "schema_version": "barcarolle.agent_tuning_demo.phase2b_future_validation_summary.v1",
            "generated_at": iso_now(),
            "stage": "future_validation",
            "window_id": SELECTED_WINDOW_ID,
            "status": "skipped_dev_gate_not_positive",
            "skip_reason": dev.get("future_gate_decision"),
            "paid_cells": 0,
            "estimated_cost_usd": 0.0,
            "paired": None,
        }
        write_csv(RESULTS / "phase2b_future_validation.csv", [], PHASE2B_SCORE_FIELDS)
        write_json(RESULTS / "phase2b_future_validation_summary.json", payload)
        write_future_report(payload)
        return
    run_eval_stage("future_validation")


def final_closeout_payload() -> dict[str, Any]:
    claim = read_json(RESULTS / "phase2b_claim_and_phase2a_reframe.json")
    audit = read_json(RESULTS / "phase2b_task_supply_headroom_audit.json")
    protocol = read_json(RESULTS / "phase2b_protocol.json") if (RESULTS / "phase2b_protocol.json").exists() else None
    proposer = read_json(RESULTS / "phase2b_proposer_integration.json") if (RESULTS / "phase2b_proposer_integration.json").exists() else None
    dev = read_json(RESULTS / "phase2b_dev_eval_summary.json") if (RESULTS / "phase2b_dev_eval_summary.json").exists() else None
    future = read_json(RESULTS / "phase2b_future_validation_summary.json") if (RESULTS / "phase2b_future_validation_summary.json").exists() else None
    terminal = "phase2b_task_supply_blocked"
    if audit["readiness_decision"]["paid_tuning_allowed_after_protocol_freeze"]:
        terminal = "phase2b_llm_proposer_blocked"
    if proposer and proposer.get("status") == "llm_proposer_complete":
        terminal = "phase2b_dev_negative"
    if future and future.get("status") == "complete":
        net = future["paired"]["paired_net_wins"]
        terminal = "phase2b_success_future_improved" if net > 0 else "phase2b_yellow_non_regression" if net == 0 else "phase2b_dev_negative"
    paid_cells = 0
    estimated_cost = 0.0
    for payload in [dev, future]:
        if payload:
            paid_cells += int(payload.get("paid_cells") or 0)
            estimated_cost += float(payload.get("estimated_cost_usd") or 0.0)
    selected = audit["candidate_windows"][0]
    return {
        "schema_version": "barcarolle.agent_tuning_demo.phase2b_closeout.v1",
        "generated_at": iso_now(),
        "terminal_state": terminal,
        "phase2a_relabel_correct": claim["phase2a_relabel"]["tuned_improvement_proven"] is False,
        "rolling_origin_windows": [
            {
                "window_id": selected["window_id"],
                "mode": selected["mode"],
                "train_count": selected["task_counts"]["train"],
                "dev_count": selected["task_counts"]["dev"],
                "future_count": selected["task_counts"]["future"],
                "dev_baseline_headroom": selected["baseline_headroom"]["dev"]["pass_rate"],
                "future_baseline_headroom": selected["baseline_headroom"]["future"]["pass_rate"],
            }
        ],
        "target_agent": TARGET_AGENT_ID,
        "artifact_surface": TARGET_SURFACE,
        "llm_proposer": None if not proposer else proposer.get("proposer_calls"),
        "llm_proposer_status": None if not proposer else proposer.get("status"),
        "paid_agent_cells": paid_cells,
        "estimated_cost_usd": round(estimated_cost, 8),
        "dev": dev,
        "future": future,
        "protocol": protocol,
        "supported_claims": supported_claims(terminal),
        "unsupported_claims": unsupported_claims(),
        "canonical_artifacts": [
            "experiments/agent_tuning_demo/reports/phase2b_agent_tuning_demo_report_zh.md",
            "experiments/agent_tuning_demo/reports/phase2b_closeout_zh.md",
            "experiments/agent_tuning_demo/results/phase2b_closeout.json",
        ],
    }


def supported_claims(terminal: str) -> list[str]:
    base = [
        "Phase 2a is correctly relabeled as an action-level artifact-validation pilot, not tuned improvement.",
        "The current boltons/Kilo-low-cost supply supports one no-paid-gated time-ordered future-validation window.",
    ]
    if terminal in {"phase2b_dev_negative", "phase2b_yellow_non_regression", "phase2b_success_future_improved"}:
        base.append("A real LLM-driven proposer produced deployable Kilo AGENTS.md candidate artifacts from train-only evidence.")
    if terminal == "phase2b_success_future_improved":
        base.append("The frozen selected artifact produced positive paired net wins on later future tasks in this demo slice.")
    if terminal == "phase2b_yellow_non_regression":
        base.append("The frozen selected artifact did not regress on future tasks, but did not improve paired net wins.")
    return base


def unsupported_claims() -> list[str]:
    return [
        "multi-window rolling-origin improvement",
        "statistical significance",
        "cross-repo generalization",
        "model fine-tuning",
        "full opaque-Agent tuning",
        "production-ready Agent tuning",
        "predictive validity beyond this frozen task window",
    ]


def write_final_reports() -> None:
    payload = final_closeout_payload()
    write_json(RESULTS / "phase2b_closeout.json", payload)
    dev_rows = []
    dev_cost_rows = []
    if payload["dev"]:
        dev_rows = [
            {
                "Candidate": summary["candidate_condition"],
                "Pass": summary["conditions"]["tuned"]["verified_pass_count"],
                "Scoreable": summary["conditions"]["tuned"]["scoreable_cells"],
                "Net wins": summary["paired_net_wins"],
                "Gate": summary["dev_gate_pass"],
            }
            for summary in payload["dev"].get("candidate_summaries", [])
        ]
        dev_cost_rows = [
            {
                "Candidate": summary["candidate_condition"],
                "Baseline cost": summary["conditions"]["baseline"]["estimated_cost_usd"],
                "Tuned cost": summary["conditions"]["tuned"]["estimated_cost_usd"],
                "Cost ratio": summary["cost_ratio_vs_baseline_per_task"],
                "Baseline latency": summary["conditions"]["baseline"]["median_latency_seconds"],
                "Tuned latency": summary["conditions"]["tuned"]["median_latency_seconds"],
                "Invalid baseline/tuned": f"{summary['conditions']['baseline']['invalid_or_unscoreable_cells']}/{summary['conditions']['tuned']['invalid_or_unscoreable_cells']}",
            }
            for summary in payload["dev"].get("candidate_summaries", [])
        ]
    future_pair = payload["future"].get("paired") if payload.get("future") else None
    report_lines = [
        "# Agent Tuning Demo Phase 2b report",
        "",
        f"Generated at: `{payload['generated_at']}`.",
        "",
        "## Why Phase 2a was not enough",
        "",
        "Phase 2a proved action-level artifact injection and an end-to-end before/after validation loop, but it did not prove tuning improvement. Selection-dev stayed `1/4 -> 1/4`, Holdout stayed `5/6 -> 5/6`, paired net wins were `0` on both splits, and the proposer was a deterministic local GEPA-shaped proposer with no reflection LM.",
        "",
        "## Result",
        "",
        f"- Terminal state: `{payload['terminal_state']}`",
        f"- Phase 2a relabeled correctly: `{payload['phase2a_relabel_correct']}`",
        f"- Target Agent/surface: `{payload['target_agent']}` / `{payload['artifact_surface']}`",
        f"- LLM proposer status/calls: `{payload['llm_proposer_status']}` / `{payload['llm_proposer']}`",
        f"- Paid Agent cells: `{payload['paid_agent_cells']}`",
        f"- Estimated cost: `${payload['estimated_cost_usd']}`",
        "",
        "## Rolling-origin design and task supply",
        "",
        *markdown_table(payload["rolling_origin_windows"], [("Window", "window_id"), ("Mode", "mode"), ("Train", "train_count"), ("Dev", "dev_count"), ("Future", "future_count"), ("Dev baseline", "dev_baseline_headroom"), ("Future baseline", "future_baseline_headroom")]),
        "",
        "Current supply supports one strong time-ordered future-validation window, not a two-window rolling-origin claim. Future task IDs stayed hidden because no artifact passed the dev gate.",
        "",
        "## Target Agent and artifact surface",
        "",
        f"The frozen target was `{TARGET_AGENT_ID}` through Kilo with one repo-local `{TARGET_ARTIFACT_PATH}` appendix. The surface was chosen because Kilo `AGENTS.md` action-level preflight passed in Phase 2.",
        "",
        "## LLM proposer and artifacts",
        "",
        f"The proposer used `{payload['llm_proposer']}` LLM calls, including one reflection/revision iteration. It produced two candidate `AGENTS.md` appendices from train-only evidence; raw prompt and completion content stayed under ignored raw paths.",
        "",
        "## Dev matrix",
        "",
        *markdown_table(dev_rows, [("Candidate", "Candidate"), ("Pass", "Pass"), ("Scoreable", "Scoreable"), ("Net wins", "Net wins"), ("Gate", "Gate")]),
        "",
        "Both candidates were non-regressing on dev but failed the preregistered improvement gate because paired net wins were `0` rather than positive.",
        "",
        "## Future matrix",
        "",
    ]
    if future_pair:
        report_lines.extend(markdown_table(future_pair["matrix"], [("Task", "task_id"), ("Baseline", "baseline_status"), ("Baseline pass", "baseline_pass"), ("Tuned", "tuned_status"), ("Tuned pass", "tuned_pass")]))
    else:
        report_lines.append("_Future validation was not run._")
    report_lines.extend(
        [
            "",
            "## Cost, latency, and invalid runs",
            "",
            *markdown_table(dev_cost_rows, [("Candidate", "Candidate"), ("Baseline cost", "Baseline cost"), ("Tuned cost", "Tuned cost"), ("Cost ratio", "Cost ratio"), ("Baseline latency", "Baseline latency"), ("Tuned latency", "Tuned latency"), ("Invalid baseline/tuned", "Invalid baseline/tuned")]),
            "",
            "No tuned candidate increased invalid or unscoreable dev cells. Candidate 1 cost was `1.0843x` baseline per task; candidate 2 cost was `0.9211x` baseline per task.",
            "",
            "## Case studies",
            "",
            "- Improved task: none observed on dev.",
            "- Unchanged task: `boltons__clean_ext__001` passed under baseline and both tuned candidates.",
            "- Remaining failure: `boltons__hist__006` and `boltons__supply_expansion_20260526__107` failed under baseline and both tuned candidates.",
            "- Regression: none observed on dev.",
            "",
            "## Behavior and failure-label changes",
            "",
            "No terminal-status or failure-label shift was observed on dev: both candidates reproduced the baseline pass/fail matrix exactly.",
            "",
            "## Supported claims",
            "",
            *[f"- {claim}" for claim in payload["supported_claims"]],
            "",
            "## Unsupported claims",
            "",
            *[f"- {claim}" for claim in payload["unsupported_claims"]],
            "",
            "## Recommended next work",
            "",
            "- Add a second prepared repo or more Kilo-low-cost boltons rows before claiming multi-window rolling-origin improvement.",
            "- Keep the LLM-proposer path, but add stronger train failure summaries if dev remains negative.",
            "- Do not spend future-validation cells unless the frozen dev gate remains positive.",
            "",
        ]
    )
    write_text(REPORTS / "phase2b_agent_tuning_demo_report_zh.md", "\n".join(report_lines))
    closeout_lines = [
        "# Agent Tuning Phase 2b closeout",
        "",
        f"Terminal state: `{payload['terminal_state']}`.",
        "",
        f"- Phase 2a relabeled correctly: `{payload['phase2a_relabel_correct']}`.",
        f"- Window counts: train/dev/future `{payload['rolling_origin_windows'][0]['train_count']}` / `{payload['rolling_origin_windows'][0]['dev_count']}` / `{payload['rolling_origin_windows'][0]['future_count']}`.",
        f"- Target Agent/surface: `{payload['target_agent']}` / `{payload['artifact_surface']}`.",
        f"- LLM proposer status/calls: `{payload['llm_proposer_status']}` / `{payload['llm_proposer']}`.",
        f"- Paid Agent cells/cost: `{payload['paid_agent_cells']}` / `${payload['estimated_cost_usd']}`.",
        f"- Future status: `{None if not payload['future'] else payload['future'].get('status')}`.",
        "",
        "See `phase2b_closeout.json` for full matrices, costs, claims, and canonical artifact links.",
        "",
    ]
    write_text(REPORTS / "phase2b_closeout_zh.md", "\n".join(closeout_lines))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Agent Tuning Demo Phase 2b helpers.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in [
        "claim-reframe",
        "task-supply-audit",
        "protocol",
        "proposer",
        "dev-eval",
        "future-validation",
        "final",
    ]:
        sub.add_parser(name)
    args = parser.parse_args(argv)
    if args.command == "claim-reframe":
        write_claim_reframe()
    elif args.command == "task-supply-audit":
        write_task_supply_audit()
    elif args.command == "protocol":
        write_protocol()
    elif args.command == "proposer":
        write_proposer_integration()
    elif args.command == "dev-eval":
        run_dev_eval()
    elif args.command == "future-validation":
        run_future_validation()
    elif args.command == "final":
        write_final_reports()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
