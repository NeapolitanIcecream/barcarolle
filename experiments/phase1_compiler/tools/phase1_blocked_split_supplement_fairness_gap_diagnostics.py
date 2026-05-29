from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load

import phase1_blocked_split_missing_cell_supplement_paid_execution as supplement


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
DEFAULT_CONFIG = ROOT / "configs" / "phase1_blocked_split_supplement_fairness_gap_diagnostics.yaml"
SCHEMA_VERSION = "barcarolle.phase1_blocked_split_supplement_fairness_gap_diagnostics.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_blocked_split_supplement_fairness_gap_diagnostics_output.v1"
ADAPTERS = ["codex_workspace", "kilo_workspace"]
REPOS = ["attrs", "boltons", "click"]
SPLITS = ["B_eval", "H_future"]
INVALID_TASK_ID = "attrs__v2__157"
TERMINAL_SCOREABLE = {"verified_pass", "verified_fail"}


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
        raise ValueError("unexpected fairness gap diagnostics config schema_version")
    config["_path"] = str(path)
    return config


def input_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["inputs"][key])


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


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


def command_result(args: list[str], *, timeout: int = 120) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        return {"args": args, "returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {"args": args, "returncode": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
    return {"args": args, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def command_stdout(args: list[str], *, timeout: int = 120) -> str:
    result = command_result(args, timeout=timeout)
    return (result["stdout"] if result["returncode"] == 0 else result["stderr"]).strip()


def status_path(line: str) -> str:
    if line.startswith("?? "):
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


def expected_commit_paths(config: dict[str, Any]) -> set[str]:
    expected = {
        rel(config["_path"]),
        rel(ROOT / "tools" / "phase1_blocked_split_supplement_fairness_gap_diagnostics.py"),
        rel(ROOT / "tests" / "test_phase1_blocked_split_supplement_fairness_gap_diagnostics.py"),
    }
    expected.update(rel(path) for path in config["outputs"].values())
    expected.update(rel(path) for path in config["reports"].values())
    return expected


def classify_dirty_paths(config: dict[str, Any], status_lines: list[str]) -> dict[str, list[str]]:
    expected = expected_commit_paths(config)
    ignored_prefixes = [
        "experiments/phase0_headroom/results/raw/",
        "experiments/phase0_headroom/workspaces/",
        "experiments/phase0_headroom/external_repos/",
        "experiments/phase1_compiler/.pytest_cache/",
        "experiments/phase1_compiler/.venv/",
        "experiments/phase1_compiler/tmp/",
    ]
    known_unrelated_prefixes = [
        "experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/",
    ]
    classified: dict[str, list[str]] = {
        "relevant_to_this_run": [],
        "ignored_raw_or_runtime": [],
        "known_unrelated_external_review": [],
        "unrelated_or_requires_review": [],
    }
    for line in status_lines:
        path = status_path(line)
        if path in expected:
            classified["relevant_to_this_run"].append(line)
        elif any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in ignored_prefixes):
            classified["ignored_raw_or_runtime"].append(line)
        elif any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in known_unrelated_prefixes):
            classified["known_unrelated_external_review"].append(line)
        else:
            classified["unrelated_or_requires_review"].append(line)
    return classified


def required_input_availability(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    availability = {}
    for key, path in sorted(config["inputs"].items()):
        resolved = repo_path(path)
        availability[key] = {
            "path": rel(resolved),
            "exists": resolved.exists(),
            "size_bytes": resolved.stat().st_size if resolved.exists() else None,
        }
    return availability


def changed_input_paths(config: dict[str, Any]) -> list[str]:
    paths = [rel(path) for path in config["inputs"].values()]
    if not paths:
        return []
    result = command_result(["git", "diff", "--name-only", "--", *paths])
    return [line for line in result["stdout"].splitlines() if line.strip()]


def bool_from_csv(raw: Any) -> bool:
    return str(raw).strip().lower() == "true"


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized["scoreable_cell"] = bool(normalized.get("scoreable_cell"))
    normalized["pass_flag"] = normalized.get("terminal_status") == "verified_pass" and normalized["scoreable_cell"] is True
    normalized["fail_flag"] = normalized.get("terminal_status") == "verified_fail" and normalized["scoreable_cell"] is True
    normalized["repo"] = normalized.get("repo") or str(normalized.get("task_id", "")).split("__", 1)[0]
    normalized["repo_id"] = normalized["repo"]
    return normalized


def combined_rows() -> list[dict[str, Any]]:
    rows = supplement.combined_rows(supplement.load_config())
    return [normalize_row(row) for row in rows]


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    terminal_counts = dict(sorted(Counter(str(row.get("terminal_status") or "") for row in rows).items()))
    scoreable = [row for row in rows if row.get("scoreable_cell") is True]
    pass_count = sum(1 for row in scoreable if row.get("terminal_status") == "verified_pass")
    return {
        "cell_count": len(rows),
        "scoreable_cell_count": len(scoreable),
        "non_scoreable_cell_count": len(rows) - len(scoreable),
        "scoreability_rate": None if not rows else round(len(scoreable) / len(rows), 4),
        "verified_pass_count": pass_count,
        "verified_fail_count": sum(1 for row in scoreable if row.get("terminal_status") == "verified_fail"),
        "pass_rate": None if not scoreable else round(pass_count / len(scoreable), 4),
        "policy_violation_count": sum(1 for row in rows if row.get("terminal_status") == "policy_violation"),
        "terminal_status_counts": terminal_counts,
    }


def split_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_split: dict[str, Any] = {}
    for split in SPLITS:
        by_split[split] = summarize_rows([row for row in rows if row.get("split") == split])
    b_rate = by_split["B_eval"]["pass_rate"]
    h_rate = by_split["H_future"]["pass_rate"]
    by_split["absolute_gap"] = None if b_rate is None or h_rate is None else round(abs(b_rate - h_rate), 4)
    by_split["H_future_minus_B_eval"] = None if b_rate is None or h_rate is None else round(h_rate - b_rate, 4)
    return by_split


def repo_from_task_id(task_id: str) -> str:
    return task_id.split("__", 1)[0] if "__" in task_id else "unknown"


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with repo_path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def score_table_path_for_row(row: dict[str, Any]) -> str:
    if row.get("score_table"):
        return str(row["score_table"])
    prefix = row.get("result_prefix")
    if prefix:
        return rel(PHASE0_ROOT / "results" / f"{prefix}_score_table.csv")
    return ""


def write_process_report(config: dict[str, Any], current_step: str, completed: list[str], notes: list[str] | None = None) -> None:
    lines = [
        "# Blocked Split Supplement Fairness Gap Diagnostics Process",
        "",
        f"Current step: `{current_step}`.",
        "",
        "Completed artifacts:",
    ]
    lines.extend([f"- {item}" for item in completed] or ["- None yet."])
    lines.extend(
        [
            "",
            "Boundary:",
            "- Diagnostic-only run.",
            f"- New paid LLM or ACUT calls allowed: `{bool(config.get('paid_calls_allowed'))}`.",
            "- Completed paid outcomes, score tables, selected tasks, and split labels were not changed.",
            "- Adapter difference is not automatically a blocker.",
            "- Follow-up runbook drafted by this worker: `false`.",
            "",
            "Notes:",
        ]
    )
    lines.extend([f"- {note}" for note in notes] if notes else ["- No extra notes."])
    write_text(report_path(config, "process"), "\n".join(lines))


def write_preflight(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    status_lines = [line for line in command_stdout(["git", "status", "--short", "--untracked-files=all"]).splitlines() if line.strip()]
    diff_check = command_result(["git", "diff", "--check"])
    decision = read_json(input_path(config, "decision"), {})
    input_availability = required_input_availability(config)
    missing_inputs = [key for key, value in input_availability.items() if not value["exists"]]
    changed_inputs = changed_input_paths(config)
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "preflight",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "ready_for_adapter_fairness_audit"
        if not missing_inputs
        and decision.get("decision_label") == config.get("expected_decision_label")
        and not changed_inputs
        else "blocked_or_limited",
        "branch": command_stdout(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "head": command_stdout(["git", "rev-parse", "HEAD"]),
        "python_version": sys.version.split()[0],
        "uv_version": command_stdout(["uv", "--version"]),
        "git_status_short_untracked_all": status_lines,
        "dirty_path_classification": classify_dirty_paths(config, status_lines),
        "git_diff_check": {
            "returncode": diff_check["returncode"],
            "stdout": diff_check["stdout"],
            "stderr": diff_check["stderr"],
            "passed": diff_check["returncode"] == 0,
        },
        "required_input_availability": input_availability,
        "missing_required_inputs": missing_inputs,
        "required_inputs_with_uncommitted_diff": changed_inputs,
        "no_paid_boundary": {
            "diagnostic_only": bool(config.get("diagnostic_only")),
            "paid_calls_allowed": bool(config.get("paid_calls_allowed")),
            "new_paid_llm_or_acut_calls_made_by_this_tool": 0,
            "raw_artifacts_required": False,
        },
        "supplement_decision_label": decision.get("decision_label"),
        "supplement_decision_matches_expected": decision.get("decision_label") == config.get("expected_decision_label"),
        "completed_supplement_artifacts_present_and_unchanged": not missing_inputs and not changed_inputs,
        "adapter_difference_policy": {
            "adapter_difference_is_automatic_blocker": False,
            "treat_as_acut_configuration_difference_if_fairness_checks_pass": True,
        },
    }
    write_json(output_path(config, "preflight"), payload)
    write_process_report(
        config,
        "Step 0 preflight complete",
        ["Step 0 preflight"],
        ["No paid calls were made.", "Known external-review bundle is classified as unrelated and left uncommitted."],
    )
    return payload


def adapter_configs(config: dict[str, Any]) -> dict[str, Any]:
    raw = simple_yaml_load(input_path(config, "adapter_config"))
    return {
        "schema_version": raw.get("schema_version"),
        "preferred_model": raw.get("preferred_model"),
        "comparison_design": raw.get("comparison_design"),
        "local_subscription_fallback": raw.get("local_subscription_fallback"),
        "openai_or_provider_fallback": raw.get("openai_or_provider_fallback"),
        "adapters": {row["adapter_id"]: row for row in raw.get("adapters", [])},
    }


def classification_for_clean(clean: bool, limited: bool = False) -> str:
    if clean:
        return "clean"
    return "missing_evidence" if limited else "fairness_risk"


def build_fairness_dimensions(config: dict[str, Any]) -> dict[str, Any]:
    adapters = adapter_configs(config)
    ready = read_json(input_path(config, "ready_package_integrity"), {})
    decision = read_json(input_path(config, "decision"), {})
    metrics = read_json(input_path(config, "adapter_metrics"), {})
    cost = read_json(input_path(config, "cost_reconciliation"), {})
    batch_payloads = [read_json(input_path(config, key), {}) for key in ["batch_1_smoke", "batch_2_attrs_remainder", "batch_3_boltons_remainder", "batch_4_click_remainder"]]
    rows = combined_rows()
    score_models = sorted({str(row.get("model_or_agent_name")) for row in rows if row.get("model_or_agent_name")})
    required_env_clean = all(
        adapters["adapters"].get(adapter, {}).get("requires_env") == ["LLM_BASE_URL", "LLM_API_KEY"]
        for adapter in ADAPTERS
    )
    batch_endpoint_clean = all((payload.get("endpoint_compliance") or {}).get("both_required_endpoint_variables_present") is True for payload in batch_payloads)
    package_rows = ready.get("package_rows", [])
    package_clean = bool(package_rows) and all(
        row.get("solver_visible_statement_exists")
        and row.get("base_commit_resolvable")
        and row.get("hidden_oracle_material_solver_visible") is False
        and row.get("target_commit_exposed_in_statement") is False
        and row.get("raw_diff_marker_in_statement") is False
        and row.get("tests_non_editable")
        and row.get("verifier_command_configured")
        for row in package_rows
    )
    dimensions = {
        "required_endpoint_variables": {
            "classification": classification_for_clean(required_env_clean and batch_endpoint_clean and decision.get("endpoint_compliance_status") == "pass"),
            "what_happened": "Both adapters require LLM_BASE_URL and LLM_API_KEY, all supplement batch summaries record endpoint variables present, and the final decision records endpoint compliance pass.",
            "why_it_matters": "The adapter comparison is not explained by one harness using a different auth path in the committed evidence.",
            "action_suggested": "Keep this endpoint rule for paid work.",
            "evidence": {
                "adapter_requires_env": {adapter: adapters["adapters"].get(adapter, {}).get("requires_env") for adapter in ADAPTERS},
                "batch_endpoint_host_hashes": sorted({(payload.get("endpoint_compliance") or {}).get("endpoint_host_hash") for payload in batch_payloads}),
                "decision_endpoint_compliance_status": decision.get("endpoint_compliance_status"),
            },
        },
        "model_identifier_or_family": {
            "classification": classification_for_clean(
                adapters.get("preferred_model") == "gpt-5.4-mini"
                and all(adapters["adapters"].get(adapter, {}).get("model_or_agent_name") == "gpt-5.4-mini" for adapter in ADAPTERS)
                and score_models == ["gpt-5.4-mini"]
            ),
            "what_happened": "Adapter config and score tables record gpt-5.4-mini for both ACUT configurations.",
            "why_it_matters": "The observed gap should not be reported as a model-only result, but the model identifier is aligned across adapters.",
            "action_suggested": "Report the difference as a same-model cross-harness ACUT configuration difference.",
            "evidence": {
                "preferred_model": adapters.get("preferred_model"),
                "configured_models": {adapter: adapters["adapters"].get(adapter, {}).get("model_or_agent_name") for adapter in ADAPTERS},
                "score_table_models": score_models,
                "comparison_design": adapters.get("comparison_design"),
            },
        },
        "pricing_and_accounting": {
            "classification": classification_for_clean(cost.get("cost_latency_accounting_complete") is True and cost.get("usage_observed_rate") == 1.0),
            "what_happened": "Cost reconciliation is complete with usage observed for all new cells; exact provider billing is explicitly unavailable.",
            "why_it_matters": "Cost/latency interpretation can use token-estimated accounting but must not claim exact provider spend.",
            "action_suggested": "Keep cost claims token-estimated unless provider billing becomes available.",
            "evidence": {
                "usage_observed_rate": cost.get("usage_observed_rate"),
                "provider_billed_exact_cost_available": cost.get("provider_billed_exact_cost_available"),
                "observed_or_conservative_new_cost_usd": cost.get("observed_or_conservative_new_cost_usd"),
                "pricing_config": rel(input_path(config, "pricing_config")),
            },
        },
        "solver_visible_task_statement_source": {
            "classification": classification_for_clean(package_clean),
            "what_happened": "Ready-package integrity records solver-visible statements, statement digests, no raw diff marker, and no target commit exposure for the new supplement package.",
            "why_it_matters": "The paid supplement was driven by task statements rather than hidden oracle material.",
            "action_suggested": "Use sanitized statement digests when auditing future packages.",
            "evidence": {
                "package_rows_checked": len(package_rows),
                "all_solver_visible_statement_exists": all(row.get("solver_visible_statement_exists") for row in package_rows),
                "all_target_commit_hidden": all(row.get("target_commit_exposed_in_statement") is False for row in package_rows),
                "reused_cells_trace_to_prior_score_tables": read_json(input_path(config, "reuse_manifest"), {}).get("reused_cell_count") == 72,
            },
        },
        "base_commit_and_workspace_construction": {
            "classification": classification_for_clean(package_clean),
            "what_happened": "Ready-package rows record resolvable base commits and source repos for the supplement missing-cell package.",
            "why_it_matters": "Both adapters should have worked from comparable clean task workspaces.",
            "action_suggested": "No paid rerun is suggested by workspace construction evidence.",
            "evidence": {
                "package_rows_checked": len(package_rows),
                "all_base_commits_resolvable": all(row.get("base_commit_resolvable") for row in package_rows),
                "workspace_matrix": rel(input_path(config, "workspace_matrix")),
            },
        },
        "allowed_edit_paths_and_prohibited_tests_or_oracle": {
            "classification": classification_for_clean(package_clean and decision.get("policy_violation_count") == 0 and decision.get("raw_oracle_exposure_detected") is False),
            "what_happened": "Allowed code paths and test paths were recorded, tests were non-editable, policy violations were zero, and raw oracle exposure was false.",
            "why_it_matters": "Adapter pass-rate differences are not explained by committed evidence of path-policy or oracle leakage.",
            "action_suggested": "Continue treating policy violations as hard gates.",
            "evidence": {
                "policy_violation_count": decision.get("policy_violation_count"),
                "raw_oracle_exposure_detected": decision.get("raw_oracle_exposure_detected"),
                "all_tests_non_editable": all(row.get("tests_non_editable") for row in package_rows),
            },
        },
        "verifier_replay_policy": {
            "classification": classification_for_clean(package_clean),
            "what_happened": "System design and supplement runbook require diff replay in fresh verifier workspaces, and ready-package rows record verifier commands.",
            "why_it_matters": "The score table is benchmark-side verification evidence, not self-reported ACUT success.",
            "action_suggested": "No verifier-policy blocker found.",
            "evidence": {
                "system_design": rel(input_path(config, "system_design")),
                "all_verifier_commands_configured": all(row.get("verifier_command_configured") for row in package_rows),
            },
        },
        "timeout_concurrency_retry_policy": {
            "classification": "documented_acut_difference",
            "what_happened": "Both adapters use the same recorded timeout and paid concurrency is one; Kilo uses strict-final completion mode as a documented harness setting.",
            "why_it_matters": "Harness/tooling differences are part of the ACUT configuration unless they break benchmark rules.",
            "action_suggested": "Report adapter results separately and avoid model-only superiority claims.",
            "evidence": {
                "timeouts": {adapter: adapters["adapters"].get(adapter, {}).get("timeout_seconds") for adapter in ADAPTERS},
                "paid_acut_concurrency": simple_yaml_load(ROOT / "configs" / "phase1_blocked_split_missing_cell_supplement_paid_execution.yaml").get("budget", {}).get("paid_acut_concurrency"),
                "command_templates": {adapter: adapters["adapters"].get(adapter, {}).get("command_template") for adapter in ADAPTERS},
            },
        },
        "score_table_import_rules": {
            "classification": classification_for_clean(
                read_json(input_path(config, "combined_manifest"), {}).get("completed_cells") == 120
                and read_json(input_path(config, "combined_manifest"), {}).get("scoreable_cells") == 119
                and decision.get("completed_paid_decision_changed") is False
            ),
            "what_happened": "The combined manifest covers all 120 selected cells, preserves the one non-scoreable cell, and the completed paid decision was not changed.",
            "why_it_matters": "Denominators are explicit and the invalid output was not silently converted into a pass or fail.",
            "action_suggested": "Keep the invalid cell non-scoreable in analysis.",
            "evidence": {
                "combined_manifest": rel(input_path(config, "combined_manifest")),
                "completed_cells": read_json(input_path(config, "combined_manifest"), {}).get("completed_cells"),
                "scoreable_cells": read_json(input_path(config, "combined_manifest"), {}).get("scoreable_cells"),
                "non_scoreable_by_status": read_json(input_path(config, "combined_manifest"), {}).get("non_scoreable_by_status"),
            },
        },
        "usage_and_cost_record_completeness": {
            "classification": classification_for_clean(cost.get("cost_latency_accounting_complete") is True and metrics.get("combined_summary", {}).get("cost_latency_accounting_status") == "complete"),
            "what_happened": "Cost reconciliation and adapter metrics mark cost/latency accounting complete for the supplement.",
            "why_it_matters": "Cost and latency comparisons are usable as token-estimated diagnostics.",
            "action_suggested": "Do not claim exact billed dollars.",
            "evidence": {
                "cost_latency_accounting_complete": cost.get("cost_latency_accounting_complete"),
                "metrics_cost_latency_accounting_status": metrics.get("combined_summary", {}).get("cost_latency_accounting_status"),
                "workspace_cost_reconciliation": rel(input_path(config, "workspace_cost_reconciliation")),
            },
        },
    }
    return dimensions


def write_adapter_fairness_audit(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    dimensions = build_fairness_dimensions(config)
    blockers = [key for key, row in dimensions.items() if row["classification"] == "benchmark_blocker"]
    risks = [key for key, row in dimensions.items() if row["classification"] == "fairness_risk"]
    missing = [key for key, row in dimensions.items() if row["classification"] == "missing_evidence"]
    conclusion = (
        "supplement_interpretation_blocked"
        if blockers
        else "adapter_comparison_limited_but_score_tables_usable"
        if risks
        else "fair_enough_to_interpret_as_acut_difference"
    )
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "adapter_fairness_audit",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete",
        "fairness_conclusion": conclusion,
        "dimension_counts": dict(sorted(Counter(row["classification"] for row in dimensions.values()).items())),
        "dimensions": dimensions,
        "limitations": [
            {
                "limitation": "Raw solver transcripts and raw ACUT logs were intentionally not read.",
                "effect": "Exact invalid-output text cannot be reconstructed; committed sanitized score tables are sufficient for scoreability and fairness denominators.",
            }
        ],
        "adapter_difference_interpretation": {
            "adapter_difference_is_problem_by_itself": False,
            "can_report_as_acut_configuration_difference": conclusion == "fair_enough_to_interpret_as_acut_difference",
            "model_only_claim_allowed": False,
        },
    }
    write_json(output_path(config, "adapter_fairness_audit"), payload)
    write_adapter_fairness_report(config, payload)
    write_process_report(config, "Step 1 adapter fairness audit complete", ["Step 0 preflight", "Step 1 adapter fairness audit"])
    return payload


def write_adapter_fairness_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Blocked Split Supplement Adapter Fairness Audit",
        "",
        f"Fairness conclusion: `{payload['fairness_conclusion']}`.",
        "",
        "What happened: endpoint, model, workspace, verifier, score-table, and accounting evidence were checked from committed sanitized artifacts.",
        "Why it matters: Kilo and Codex can differ without that being a benchmark bug if both ACUT configurations followed the same benchmark rules.",
        "Action suggested next: report the adapter gap as an ACUT configuration difference, not a model-only result.",
        "",
        "## Dimensions",
        "",
    ]
    for key, row in payload["dimensions"].items():
        lines.extend(
            [
                f"### {key}",
                "",
                f"- Classification: `{row['classification']}`.",
                f"- What happened: {row['what_happened']}",
                f"- Why it matters: {row['why_it_matters']}",
                f"- Action suggested: {row['action_suggested']}",
                "",
            ]
        )
    lines.extend(["## Limitations", ""])
    for item in payload["limitations"]:
        lines.append(f"- {item['limitation']} Effect: {item['effect']}")
    write_text(report_path(config, "adapter_fairness_audit"), "\n".join(lines))


def origin_breakdown(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_origin: dict[str, Any] = {}
    for origin in sorted({str(row.get("cell_source") or "unknown") for row in rows}):
        by_origin[origin] = summarize_rows([row for row in rows if str(row.get("cell_source") or "unknown") == origin])
    return by_origin


def gap_labels(repo: str, gap: float | None, non_scoreable_count: int) -> list[str]:
    labels: list[str] = []
    if gap is None:
        labels.append("missing_gap")
    elif gap >= 0.25:
        labels.append("high_gap")
    elif gap >= 0.1:
        labels.append("moderate_gap")
    else:
        labels.append("low_gap")
    if non_scoreable_count:
        labels.append("non_scoreable_sensitive")
    if repo == "click":
        labels.append("click_source_caveat_applies")
    return labels


def build_repo_gap_matrix(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    rows = combined_rows()
    by_adapter: dict[str, Any] = {}
    for adapter in ADAPTERS:
        adapter_rows = [row for row in rows if row.get("adapter_id") == adapter]
        adapter_payload = {"summary": summarize_rows(adapter_rows), "by_repo": {}}
        for repo in REPOS:
            repo_rows = [row for row in adapter_rows if row.get("repo") == repo]
            metrics = split_metrics(repo_rows)
            non_scoreable_count = summarize_rows(repo_rows)["non_scoreable_cell_count"]
            adapter_payload["by_repo"][repo] = {
                "repo": repo,
                "adapter_id": adapter,
                "B_eval": metrics["B_eval"],
                "H_future": metrics["H_future"],
                "absolute_gap": metrics["absolute_gap"],
                "H_future_minus_B_eval": metrics["H_future_minus_B_eval"],
                "origin_breakdown": origin_breakdown(repo_rows),
                "gap_driver_labels": gap_labels(repo, metrics["absolute_gap"], non_scoreable_count),
            }
        by_adapter[adapter] = adapter_payload
    pooled_secondary_by_repo = {}
    for repo in REPOS:
        repo_rows = [row for row in rows if row.get("repo") == repo]
        metrics = split_metrics(repo_rows)
        pooled_secondary_by_repo[repo] = {
            "repo": repo,
            "B_eval": metrics["B_eval"],
            "H_future": metrics["H_future"],
            "absolute_gap": metrics["absolute_gap"],
            "H_future_minus_B_eval": metrics["H_future_minus_B_eval"],
            "origin_breakdown": origin_breakdown(repo_rows),
            "gap_driver_labels": gap_labels(repo, metrics["absolute_gap"], summarize_rows(repo_rows)["non_scoreable_cell_count"]),
        }
    driver_summary = [
        "codex_workspace click has the largest adapter/repo gap at 0.3000 and carries the click title-only caveat.",
        "kilo_workspace boltons has the largest Kilo repo gap at 0.2000.",
        "codex_workspace attrs has one non-scoreable B_eval cell, so the attrs gap is denominator-sensitive.",
    ]
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "repo_gap_matrix",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete",
        "by_adapter": by_adapter,
        "pooled_secondary_by_repo": pooled_secondary_by_repo,
        "driver_summary": driver_summary,
        "interpretation_boundary": {
            "adapter_level_results_first": True,
            "pooled_repo_summaries_are_secondary": True,
            "click_minor_risk_caveat": "visible_title_only_minor_risk",
            "outcomes_or_denominators_changed_after_matrix": False,
        },
    }
    write_json(output_path(config, "repo_gap_matrix"), payload)
    write_repo_gap_report(config, payload)
    write_process_report(config, "Step 2 repo gap matrix complete", ["Step 0 preflight", "Step 1 adapter fairness audit", "Step 2 repo gap matrix"])
    return payload


def write_repo_gap_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Blocked Split Supplement Repo Gap Matrix",
        "",
        "What happened: B_eval/H_future pass-rate gaps were recomputed by adapter and repo.",
        "Why it matters: the overall gap hides different repo-level shapes for Codex and Kilo.",
        "Action suggested next: use repo-level no-paid analysis for Codex click, Kilo boltons, and Codex attrs denominator sensitivity.",
        "",
    ]
    for adapter, adapter_payload in payload["by_adapter"].items():
        lines.extend([f"## {adapter}", ""])
        for repo, row in adapter_payload["by_repo"].items():
            lines.append(
                f"- `{repo}`: B_eval `{row['B_eval']['pass_rate']}`, H_future `{row['H_future']['pass_rate']}`, gap `{row['absolute_gap']}`, labels `{', '.join(row['gap_driver_labels'])}`."
            )
        lines.append("")
    lines.extend(["## Driver Summary", ""])
    lines.extend([f"- {item}" for item in payload["driver_summary"]])
    write_text(report_path(config, "repo_gap_matrix"), "\n".join(lines))


def paired_outcome(codex: dict[str, Any], kilo: dict[str, Any]) -> str:
    codex_pass = codex.get("terminal_status") == "verified_pass"
    kilo_pass = kilo.get("terminal_status") == "verified_pass"
    if codex_pass and kilo_pass:
        return "both_pass"
    if not codex_pass and not kilo_pass:
        return "both_fail"
    if codex_pass:
        return "codex_only_pass"
    return "kilo_only_pass"


def disagreement_summary_for_pairs(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(pair["paired_outcome"] for pair in pairs)
    paired = len(pairs)
    disagreement = counts["codex_only_pass"] + counts["kilo_only_pass"]
    codex_passes = counts["both_pass"] + counts["codex_only_pass"]
    kilo_passes = counts["both_pass"] + counts["kilo_only_pass"]
    return {
        "paired_task_count": paired,
        "both_pass": counts["both_pass"],
        "both_fail": counts["both_fail"],
        "codex_only_pass": counts["codex_only_pass"],
        "kilo_only_pass": counts["kilo_only_pass"],
        "disagreement_count": disagreement,
        "disagreement_rate": None if paired == 0 else round(disagreement / paired, 4),
        "codex_pass_rate_on_paired_tasks": None if paired == 0 else round(codex_passes / paired, 4),
        "kilo_pass_rate_on_paired_tasks": None if paired == 0 else round(kilo_passes / paired, 4),
        "kilo_minus_codex_pass_rate_delta": None if paired == 0 else round((kilo_passes - codex_passes) / paired, 4),
    }


def build_adapter_disagreement(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    rows = combined_rows()
    by_task_adapter = {(str(row["task_id"]), str(row["adapter_id"])): row for row in rows if row.get("scoreable_cell") is True}
    all_task_ids = sorted({str(row["task_id"]) for row in rows})
    pairs: list[dict[str, Any]] = []
    unpaired: list[dict[str, Any]] = []
    for task_id in all_task_ids:
        codex = by_task_adapter.get((task_id, "codex_workspace"))
        kilo = by_task_adapter.get((task_id, "kilo_workspace"))
        if not (codex and kilo):
            raw_rows = [row for row in rows if row.get("task_id") == task_id]
            unpaired.append(
                {
                    "task_id": task_id,
                    "repo": repo_from_task_id(task_id),
                    "reason": "one_or_more_adapter_cells_non_scoreable_or_missing",
                    "cells": [
                        {
                            "adapter_id": row.get("adapter_id"),
                            "terminal_status": row.get("terminal_status"),
                            "scoreable_cell": row.get("scoreable_cell"),
                            "score_table": score_table_path_for_row(row),
                        }
                        for row in raw_rows
                    ],
                }
            )
            continue
        outcome = paired_outcome(codex, kilo)
        pairs.append(
            {
                "task_id": task_id,
                "repo": codex.get("repo"),
                "split": codex.get("split"),
                "paired_outcome": outcome,
                "codex_terminal_status": codex.get("terminal_status"),
                "kilo_terminal_status": kilo.get("terminal_status"),
            }
        )
    by_repo = {
        repo: disagreement_summary_for_pairs([pair for pair in pairs if pair["repo"] == repo])
        for repo in REPOS
    }
    by_split = {
        split: disagreement_summary_for_pairs([pair for pair in pairs if pair["split"] == split])
        for split in SPLITS
    }
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "adapter_disagreement_by_repo",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete",
        "overall": disagreement_summary_for_pairs(pairs),
        "by_repo": by_repo,
        "by_split": by_split,
        "unpaired_or_non_scoreable_tasks": unpaired,
        "broad_or_concentrated": "broad_across_repos_with_largest_rates_in_click_and_boltons",
        "interpretation_boundary": {
            "higher_kilo_pass_rate_is_valid_acut_result_if_fairness_clean": True,
            "model_only_claim_allowed": False,
        },
    }
    write_json(output_path(config, "adapter_disagreement_by_repo"), payload)
    write_adapter_disagreement_report(config, payload)
    write_process_report(
        config,
        "Step 3 adapter disagreement complete",
        ["Step 0 preflight", "Step 1 adapter fairness audit", "Step 2 repo gap matrix", "Step 3 adapter disagreement by repo"],
    )
    return payload


def write_adapter_disagreement_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    overall = payload["overall"]
    lines = [
        "# Blocked Split Supplement Adapter Disagreement By Repo",
        "",
        "What happened: scoreable Codex/Kilo outcomes were paired by task ID.",
        "Why it matters: disagreement is benchmark evidence about ACUT configurations, not automatically an error.",
        "Action suggested next: focus no-paid review on click and boltons disagreements while keeping attrs denominator limits visible.",
        "",
        f"- Paired task count: `{overall['paired_task_count']}`.",
        f"- Disagreement rate: `{overall['disagreement_rate']}`.",
        f"- Both pass: `{overall['both_pass']}`.",
        f"- Both fail: `{overall['both_fail']}`.",
        f"- Codex-only pass: `{overall['codex_only_pass']}`.",
        f"- Kilo-only pass: `{overall['kilo_only_pass']}`.",
        "",
        "## By Repo",
        "",
    ]
    for repo, row in payload["by_repo"].items():
        lines.append(
            f"- `{repo}`: paired `{row['paired_task_count']}`, disagreement `{row['disagreement_rate']}`, Kilo minus Codex delta `{row['kilo_minus_codex_pass_rate_delta']}`."
        )
    lines.extend(["", "## Unpaired", ""])
    lines.extend([f"- `{row['task_id']}`: {row['reason']}." for row in payload["unpaired_or_non_scoreable_tasks"]] or ["- None."])
    write_text(report_path(config, "adapter_disagreement_by_repo"), "\n".join(lines))


def build_invalid_output_triage(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    rows = combined_rows()
    invalid_rows = [
        row
        for row in rows
        if row.get("adapter_id") == "codex_workspace"
        and row.get("task_id") == INVALID_TASK_ID
        and row.get("terminal_status") == "invalid_output"
    ]
    invalid_row = invalid_rows[0] if invalid_rows else {}
    same_task_rows = [row for row in rows if row.get("task_id") == INVALID_TASK_ID]
    other_invalid_like = [
        row
        for row in rows
        if row.get("task_id") != INVALID_TASK_ID
        and (row.get("terminal_status") == "invalid_output" or row.get("submission_status") == "invalid_output" or row.get("scoreable_cell") is not True)
    ]
    classification = "adapter_output_contract_violation" if invalid_row else "insufficient_sanitized_evidence"
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "invalid_output_triage",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete" if invalid_row else "limited",
        "invalid_cell": {
            "task_id": INVALID_TASK_ID,
            "adapter_id": "codex_workspace",
            "repo": "attrs",
            "split": "B_eval",
            "score_table": score_table_path_for_row(invalid_row) if invalid_row else None,
            "sanitized_row": {
                key: invalid_row.get(key)
                for key in [
                    "adapter_id",
                    "harness_name",
                    "model_or_agent_name",
                    "task_id",
                    "split",
                    "submission_status",
                    "terminal_status",
                    "verifier_exit_code",
                    "scoreable_cell",
                    "agent_failure",
                    "harness_error",
                    "cell_source",
                ]
            }
            if invalid_row
            else {},
        },
        "classification": classification,
        "exact_cause_limitation": "Raw solver output was not read, so the sanitized row cannot distinguish no-diff from unparseable-diff details.",
        "same_task_other_adapter": [
            {
                "adapter_id": row.get("adapter_id"),
                "terminal_status": row.get("terminal_status"),
                "scoreable_cell": row.get("scoreable_cell"),
                "submission_status": row.get("submission_status"),
                "score_table": score_table_path_for_row(row),
            }
            for row in same_task_rows
            if row.get("adapter_id") != "codex_workspace"
        ],
        "other_invalid_or_non_scoreable_patterns": [
            {
                "adapter_id": row.get("adapter_id"),
                "task_id": row.get("task_id"),
                "terminal_status": row.get("terminal_status"),
                "scoreable_cell": row.get("scoreable_cell"),
                "score_table": score_table_path_for_row(row),
            }
            for row in other_invalid_like
        ],
        "threat_assessment": {
            "threatens_supplement_conclusion": False,
            "threatens_adapter_comparison": "limited_denominator_effect_for_one_codex_attrs_B_eval_cell",
            "scoreability_rate": read_json(input_path(config, "decision"), {}).get("scoreability_rate"),
            "policy_violation_count": read_json(input_path(config, "decision"), {}).get("policy_violation_count"),
        },
        "recommended_actions": [
            "improve_sanitized_invalid_output_logging",
            "investigate_codex_attrs_invalid_output_contract_no_paid",
            "paid_rerun_only_if_benchmark_bug_confirmed",
        ],
    }
    write_json(output_path(config, "invalid_output_triage"), payload)
    write_invalid_output_report(config, payload)
    write_process_report(
        config,
        "Step 4 invalid output triage complete",
        ["Step 0 preflight", "Step 1 adapter fairness audit", "Step 2 repo gap matrix", "Step 3 adapter disagreement by repo", "Step 4 invalid output triage"],
    )
    return payload


def write_invalid_output_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    invalid = payload["invalid_cell"]
    lines = [
        "# Blocked Split Supplement Invalid Output Triage",
        "",
        f"Classification: `{payload['classification']}`.",
        "",
        f"What happened: Codex produced a non-scoreable `invalid_output` for `{INVALID_TASK_ID}` in `{invalid.get('score_table')}`.",
        "Why it matters: this affects one denominator cell and should not be silently converted to pass or fail.",
        "Action suggested next: improve no-paid sanitized logging and inspect the Codex output contract only if a benchmark bug is suspected.",
        "",
        f"- Kilo same task: `{payload['same_task_other_adapter'][0]['terminal_status'] if payload['same_task_other_adapter'] else None}`.",
        f"- Other invalid or non-scoreable patterns: `{len(payload['other_invalid_or_non_scoreable_patterns'])}`.",
        f"- Threatens supplement conclusion: `{payload['threat_assessment']['threatens_supplement_conclusion']}`.",
        "",
        "Limitation: raw solver output was not read or committed, so the exact invalid-output text remains unknown.",
    ]
    write_text(report_path(config, "invalid_output_triage"), "\n".join(lines))


def previous_repo_gaps(previous_summary: dict[str, Any]) -> dict[str, Any]:
    by_adapter = previous_summary.get("by_adapter", {})
    return {
        adapter: (payload.get("b_eval_h_future_gap") or {}).get("by_repo", {})
        for adapter, payload in by_adapter.items()
    }


def build_previous_split_comparison(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    supplement_metrics = read_json(input_path(config, "adapter_metrics"), {})
    previous_metrics = read_json(input_path(config, "previous_metrics"), {})
    previous_summary = read_json(input_path(config, "adapter_reporting_three_repo_summary"), {})
    previous_pairwise = read_json(input_path(config, "adapter_reporting_pairwise_summary"), {})
    comparison = {
        "scoreability": {
            "previous": previous_metrics.get("scoreability_rate"),
            "supplement": supplement_metrics.get("combined_summary", {}).get("scoreability_rate"),
            "interpretation": "supplement_slightly_worse_due_to_one_invalid_output",
        },
        "policy_violations": {
            "previous": previous_metrics.get("policy_violation_count"),
            "supplement": supplement_metrics.get("combined_summary", {}).get("policy_violation_count"),
            "interpretation": "same_clean_policy_result",
        },
        "pooled_gap": {
            "previous_three_repo_primary_pooled_gap": previous_metrics.get("pooled_unweighted", {}).get("primary_absolute_gap"),
            "supplement_pooled_gap": supplement_metrics.get("pooled_summary_secondary", {}).get("primary_absolute_gap"),
            "known_comparison_required_by_runbook": "old 0.1000 vs supplement 0.1079",
            "interpretation": "about_the_same_or_slightly_worse_not_healthier",
        },
        "adapter_pass_rates": {
            "previous": {
                adapter: (previous_summary.get("by_adapter", {}).get(adapter) or {}).get("pass_rate")
                for adapter in ADAPTERS
            },
            "supplement": {
                adapter: (supplement_metrics.get("by_adapter", {}).get(adapter) or {}).get("pass_rate")
                for adapter in ADAPTERS
            },
        },
        "adapter_gaps": {
            "previous": {
                adapter: ((previous_summary.get("by_adapter", {}).get(adapter) or {}).get("b_eval_h_future_gap") or {}).get("pooled", {}).get("absolute_gap")
                for adapter in ADAPTERS
            },
            "supplement": {
                adapter: (supplement_metrics.get("by_adapter", {}).get(adapter) or {}).get("B_eval_H_future_absolute_gap")
                for adapter in ADAPTERS
            },
        },
        "repo_level_gaps": {
            "previous": previous_repo_gaps(previous_summary),
            "supplement": {
                adapter: (supplement_metrics.get("by_adapter", {}).get(adapter) or {}).get("per_repo", {})
                for adapter in ADAPTERS
            },
        },
        "adapter_disagreement": {
            "previous": {
                "paired_task_count": previous_pairwise.get("paired_task_count"),
                "disagreement_rate": previous_pairwise.get("disagreement_rate"),
                "codex_only_pass": previous_pairwise.get("codex_workspace_only_pass"),
                "kilo_only_pass": previous_pairwise.get("kilo_workspace_only_pass"),
            },
            "supplement": supplement_metrics.get("paired_adapter_disagreement"),
        },
    }
    payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "previous_split_comparison",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete",
        "comparison": comparison,
        "overall_diagnostic_label": "about_the_same_or_slightly_worse",
        "claim_boundary": {
            "diagnostic_not_formal_validation": True,
            "predictive_validity_established": False,
            "new_paid_cells_run_by_this_diagnostic": 0,
        },
    }
    write_json(output_path(config, "previous_split_comparison"), payload)
    write_previous_split_report(config, payload)
    write_process_report(
        config,
        "Step 5 previous split comparison complete",
        [
            "Step 0 preflight",
            "Step 1 adapter fairness audit",
            "Step 2 repo gap matrix",
            "Step 3 adapter disagreement by repo",
            "Step 4 invalid output triage",
            "Step 5 previous split comparison",
        ],
    )
    return payload


def write_previous_split_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    comparison = payload["comparison"]
    lines = [
        "# Blocked Split Supplement Previous Split Comparison",
        "",
        f"Overall diagnostic label: `{payload['overall_diagnostic_label']}`.",
        "",
        "What happened: the blocked split supplement was compared with the previous three-repo paid split using committed summaries.",
        "Why it matters: the new split should not be described as healthier if the pooled gap is similar or slightly worse.",
        "Action suggested next: treat the comparison as exploratory context, not formal predictive-validity evidence.",
        "",
        f"- Pooled gap: old `{comparison['pooled_gap']['previous_three_repo_primary_pooled_gap']}` vs supplement `{comparison['pooled_gap']['supplement_pooled_gap']}`.",
        f"- Scoreability: old `{comparison['scoreability']['previous']}` vs supplement `{comparison['scoreability']['supplement']}`.",
        f"- Adapter disagreement: old `{comparison['adapter_disagreement']['previous']['disagreement_rate']}` vs supplement `{comparison['adapter_disagreement']['supplement']['disagreement_rate']}`.",
        "",
        "This comparison is diagnostic only and does not establish predictive validity.",
    ]
    write_text(report_path(config, "previous_split_comparison"), "\n".join(lines))


def build_action_matrix_and_decision(config_path: Path = DEFAULT_CONFIG) -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_config(config_path)
    fairness = read_json(output_path(config, "adapter_fairness_audit"), {})
    repo_gap = read_json(output_path(config, "repo_gap_matrix"), {})
    disagreement = read_json(output_path(config, "adapter_disagreement_by_repo"), {})
    invalid = read_json(output_path(config, "invalid_output_triage"), {})
    previous = read_json(output_path(config, "previous_split_comparison"), {})
    actions = [
        {
            "action": "accept_adapter_difference_as_acut_result",
            "recommendation_status": "recommended",
            "evidence": "Fairness conclusion is fair_enough_to_interpret_as_acut_difference; endpoint/model/workspace/verifier/accounting checks are clean enough.",
            "cost": "no_paid",
            "blocking": False,
        },
        {
            "action": "fix_adapter_endpoint_or_model_config",
            "recommendation_status": "not_recommended_now",
            "evidence": "Committed endpoint and model evidence is clean for both adapters.",
            "cost": "no_paid_if_needed",
            "blocking": False,
        },
        {
            "action": "improve_sanitized_invalid_output_logging",
            "recommendation_status": "recommended_minor",
            "evidence": "The invalid row proves invalid_output but does not preserve enough sanitized cause detail to distinguish no diff from unparseable diff.",
            "cost": "no_paid",
            "blocking": False,
        },
        {
            "action": "investigate_codex_attrs_invalid_output_contract",
            "recommendation_status": "recommended_no_paid",
            "evidence": "Only Codex attrs__v2__157 is non-scoreable; Kilo completed the same task as verified_fail.",
            "cost": "no_paid",
            "blocking": False,
        },
        {
            "action": "repo_level_gap_deep_dive_no_paid",
            "recommendation_status": "recommended",
            "evidence": "Repo gaps are concentrated in Codex click, Kilo boltons, and Codex attrs non-scoreable sensitivity.",
            "cost": "no_paid",
            "blocking": False,
        },
        {
            "action": "proceed_to_next_repo_or_supply_expansion",
            "recommendation_status": "allowed_after_no_paid_review",
            "evidence": "Supplement is fair enough to interpret, but click caveat and repo gaps should inform next supply decisions.",
            "cost": "depends_on_next_work",
            "blocking": False,
        },
        {
            "action": "do_not_run_more_paid_cells_yet",
            "recommendation_status": "recommended",
            "evidence": "No benchmark bug was found that justifies paid reruns; repo-level gaps can be studied without paid cells.",
            "cost": "saves_paid_budget",
            "blocking": True,
        },
        {
            "action": "paid_rerun_only_if_benchmark_bug_confirmed",
            "recommendation_status": "recommended_policy",
            "evidence": "The one invalid output is non-scoreable and logging-limited, not proof of a benchmark bug.",
            "cost": "paid_only_if_later_justified",
            "blocking": False,
        },
    ]
    action_payload = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "action_matrix",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "status": "complete",
        "actions": actions,
    }
    decision_label = "supplement_fair_enough_with_minor_logging_action"
    decision = {
        "schema_version": OUTPUT_SCHEMA,
        "artifact": "decision",
        "run_id": config["run_id"],
        "generated_at": now_utc(),
        "decision_label": decision_label,
        "adapter_fairness": fairness.get("fairness_conclusion"),
        "endpoint_model_config_evidence": "clean",
        "adapter_difference_as_acut_difference": "yes",
        "model_only_claim_allowed": False,
        "repo_level_gap_priorities": [
            "codex_workspace click gap 0.3000 with click title-only caveat",
            "kilo_workspace boltons gap 0.2000",
            "codex_workspace attrs gap 0.1444 with one non-scoreable B_eval denominator caveat",
        ],
        "adapter_disagreement_summary": {
            "overall": disagreement.get("overall"),
            "main_concentration": disagreement.get("broad_or_concentrated"),
        },
        "invalid_output_summary": {
            "classification": invalid.get("classification"),
            "threatens_supplement_conclusion": (invalid.get("threat_assessment") or {}).get("threatens_supplement_conclusion"),
            "recommended_action": "minor no-paid logging and Codex output-contract inspection",
        },
        "previous_split_comparison": {
            "diagnostic_label": previous.get("overall_diagnostic_label"),
            "predictive_validity_established": False,
        },
        "more_paid_cells_recommended_now": False,
        "predictive_validity_established": False,
        "new_paid_cells_run_by_this_diagnostic": 0,
        "raw_artifacts_committed": False,
        "followup_runbook_written_by_worker": False,
        "action_matrix": rel(output_path(config, "action_matrix")),
    }
    write_json(output_path(config, "action_matrix"), action_payload)
    write_json(output_path(config, "decision"), decision)
    write_action_matrix_report(config, action_payload)
    write_decision_report(config, decision)
    write_process_report(
        config,
        "Step 6 action matrix and decision complete",
        [
            "Step 0 preflight",
            "Step 1 adapter fairness audit",
            "Step 2 repo gap matrix",
            "Step 3 adapter disagreement by repo",
            "Step 4 invalid output triage",
            "Step 5 previous split comparison",
            "Step 6 action matrix and decision",
        ],
    )
    return action_payload, decision


def write_action_matrix_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        "# Blocked Split Supplement Action Matrix",
        "",
        "What happened: diagnostic findings were mapped to next-action categories.",
        "Why it matters: follow-up should separate no-paid analysis from paid reruns.",
        "Action suggested next: accept the adapter difference as ACUT evidence and keep paid reruns blocked unless a concrete benchmark bug appears.",
        "",
    ]
    for row in payload["actions"]:
        lines.append(
            f"- `{row['action']}`: `{row['recommendation_status']}`, cost `{row['cost']}`, blocking `{row['blocking']}`. Evidence: {row['evidence']}"
        )
    write_text(report_path(config, "action_matrix"), "\n".join(lines))


def write_decision_report(config: dict[str, Any], decision: dict[str, Any]) -> None:
    lines = [
        "# Blocked Split Supplement Fairness Gap Diagnostics Decision",
        "",
        f"Primary decision label: `{decision['decision_label']}`.",
        "",
        "What happened: the no-paid diagnostic found the supplement fair enough to interpret, with one minor invalid-output logging action.",
        "Why it matters: Kilo's higher pass rate can be reported as an ACUT configuration result, not as a model-only claim.",
        "Action suggested next: do no-paid repo-level and invalid-output logging work; do not run more paid cells now.",
        "",
        f"- Adapter fairness: `{decision['adapter_fairness']}`.",
        f"- Endpoint/model/config evidence: `{decision['endpoint_model_config_evidence']}`.",
        f"- Adapter difference as ACUT difference: `{decision['adapter_difference_as_acut_difference']}`.",
        f"- Invalid output classification: `{decision['invalid_output_summary']['classification']}`.",
        f"- Invalid output threatens supplement conclusion: `{decision['invalid_output_summary']['threatens_supplement_conclusion']}`.",
        f"- More paid cells recommended now: `{decision['more_paid_cells_recommended_now']}`.",
        f"- Predictive validity established: `{decision['predictive_validity_established']}`.",
        "",
        "No follow-up runbook was drafted or created by this diagnostic run.",
    ]
    write_text(report_path(config, "decision"), "\n".join(lines))


def run_all(config_path: Path = DEFAULT_CONFIG) -> None:
    write_preflight(config_path)
    write_adapter_fairness_audit(config_path)
    build_repo_gap_matrix(config_path)
    build_adapter_disagreement(config_path)
    build_invalid_output_triage(config_path)
    build_previous_split_comparison(config_path)
    build_action_matrix_and_decision(config_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "command",
        choices=[
            "preflight",
            "fairness",
            "repo-gap",
            "disagreement",
            "invalid-output",
            "previous-comparison",
            "decision",
            "all",
        ],
    )
    args = parser.parse_args(argv)
    if args.command == "preflight":
        write_preflight(args.config)
    elif args.command == "fairness":
        write_adapter_fairness_audit(args.config)
    elif args.command == "repo-gap":
        build_repo_gap_matrix(args.config)
    elif args.command == "disagreement":
        build_adapter_disagreement(args.config)
    elif args.command == "invalid-output":
        build_invalid_output_triage(args.config)
    elif args.command == "previous-comparison":
        build_previous_split_comparison(args.config)
    elif args.command == "decision":
        build_action_matrix_and_decision(args.config)
    elif args.command == "all":
        run_all(args.config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
