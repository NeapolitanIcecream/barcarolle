from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "phase1_attrs_generalization_third_repo_decision.yaml"


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
    if config.get("schema_version") != "barcarolle.phase1_attrs_generalization_third_repo_decision.v1":
        raise ValueError("unexpected attrs generalization config schema_version")
    config["_path"] = str(path)
    return config


def config_path(raw: str | Path) -> Path:
    path = Path(str(raw))
    return path if path.is_absolute() else REPO_ROOT / path


def configured_output_path(config: dict[str, Any], key: str) -> Path:
    return config_path(config["output_paths"][key])


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes"}


def listish(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value] if value else []
    return [str(value)]


def split_label(split_key: str) -> str:
    labels = {"b_eval": "B_eval", "h_future": "H_future"}
    return labels.get(split_key, split_key)


def load_score_rows(config: dict[str, Any], diagnostics: dict[str, Any]) -> dict[tuple[str, str], list[dict[str, str]]]:
    rows_by_repo_split: dict[tuple[str, str], list[dict[str, str]]] = {}
    missing_score_tables: set[str] = set()
    for repo_id, splits in config.get("score_tables", {}).items():
        for split_key, raw_path in splits.items():
            expected = config.get("frozen_design", {}).get(repo_id, {}).get(split_key, [])
            if not expected:
                continue
            path = config_path(raw_path)
            if not path.exists():
                rows_by_repo_split[(repo_id, split_key)] = []
                missing_score_tables.add(rel(path))
                continue
            rows_by_repo_split[(repo_id, split_key)] = read_csv(path)
    diagnostics["missing_score_tables"] = sorted(missing_score_tables)
    return rows_by_repo_split


def load_task_metadata(config: dict[str, Any], diagnostics: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    missing_metadata_files: list[str] = []
    for _repo_id, raw_paths in config.get("task_metadata", {}).items():
        for raw_path in listish(raw_paths):
            path = config_path(raw_path)
            if not path.exists():
                missing_metadata_files.append(rel(path))
                continue
            for row in read_jsonl(path):
                task_id = row.get("task_id")
                if task_id:
                    metadata[str(task_id)] = row
    diagnostics["missing_metadata_files"] = sorted(missing_metadata_files)
    return metadata


def infer_task_type(metadata: dict[str, Any]) -> str:
    if metadata.get("task_type_proxy"):
        return str(metadata["task_type_proxy"])
    changed_files = listish(metadata.get("changed_files"))
    code_files = listish(metadata.get("code_files"))
    test_files = listish(metadata.get("test_files"))
    has_docs = any(path.startswith("docs/") or path.startswith("changelog") for path in changed_files)
    has_runtime = bool(code_files) or any(
        path.endswith(".py") and not path.startswith("tests/") and not path.startswith("conftest.py")
        for path in changed_files
    )
    if has_runtime and test_files and has_docs:
        return "runtime_behavior_with_docs_and_tests"
    if has_runtime and test_files:
        return "runtime_behavior_with_tests"
    if has_runtime:
        return "runtime_behavior"
    if test_files:
        return "test_or_oracle_maintenance"
    if has_docs:
        return "documentation_or_changelog"
    return "unknown"


def metadata_projection(metadata: dict[str, Any]) -> dict[str, Any]:
    context = metadata.get("sanitized_context") if isinstance(metadata.get("sanitized_context"), dict) else {}
    allowed_refs = listish(metadata.get("allowed_context_refs"))
    source_context_ref = allowed_refs[0] if allowed_refs else context.get("ref", "")
    module_or_package = listish(metadata.get("module_or_package"))
    gates = (
        metadata.get("clean_overlay_certification_gates")
        or metadata.get("local_certification_gates")
        or metadata.get("gates")
        or {}
    )
    return {
        "task_time": metadata.get("task_time", ""),
        "source_context_ref": source_context_ref,
        "source_context_status": metadata.get("source_context_status", ""),
        "source_context_kind": context.get("classification", ""),
        "changed_files": listish(metadata.get("changed_files")),
        "changed_file_count": len(listish(metadata.get("changed_files"))),
        "test_files": listish(metadata.get("test_files")),
        "test_file_count": len(listish(metadata.get("test_files"))),
        "module_or_package": module_or_package,
        "module_or_package_label": "/".join(module_or_package) if module_or_package else "unknown",
        "task_type": infer_task_type(metadata),
        "candidate_filter_status": metadata.get("candidate_filter_status", ""),
        "scope_clarity_gate": gates.get("scope_clarity_review", ""),
    }


def score_row_projection(row: dict[str, str] | None, source_score_table: str) -> dict[str, Any]:
    terminal_status = row.get("terminal_status", "missing_score_row") if row else "missing_score_row"
    scoreable = boolish(row.get("scoreable_cell")) if row else False
    harness_error = boolish(row.get("harness_error")) if row else True
    return {
        "terminal_status": terminal_status,
        "scoreable_cell": scoreable,
        "verified_pass": terminal_status == "verified_pass" and scoreable,
        "verified_fail": terminal_status == "verified_fail" and scoreable,
        "policy_violation": terminal_status == "policy_violation",
        "harness_error": harness_error,
        "source_score_table": source_score_table,
    }


def build_task_outcome_matrix(config: dict[str, Any]) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    rows_by_repo_split = load_score_rows(config, diagnostics)
    metadata = load_task_metadata(config, diagnostics)
    adapters = listish(config.get("adapters"))
    missing_planned_cells: list[dict[str, str]] = []
    cells: list[dict[str, Any]] = []
    frozen_design_details: dict[str, Any] = {}

    for repo_id, splits in config.get("frozen_design", {}).items():
        frozen_design_details[repo_id] = {}
        for split_key, expected_task_ids in splits.items():
            label = split_label(split_key)
            rows = rows_by_repo_split.get((repo_id, split_key), [])
            row_index = {(row.get("task_id", ""), row.get("adapter_id", "")): row for row in rows}
            actual_task_ids = sorted({row.get("task_id", "") for row in rows if row.get("task_id")})
            expected_sorted = sorted(str(task_id) for task_id in expected_task_ids)
            frozen_design_details[repo_id][label] = {
                "actual_task_ids": actual_task_ids,
                "expected_task_ids": expected_sorted,
                "missing_task_ids": sorted(set(expected_sorted) - set(actual_task_ids)),
                "unexpected_task_ids": sorted(set(actual_task_ids) - set(expected_sorted)),
            }

            raw_score_table = config.get("score_tables", {}).get(repo_id, {}).get(split_key, "")
            source_score_table = rel(config_path(raw_score_table)) if raw_score_table else ""
            for task_id in expected_task_ids:
                task_id = str(task_id)
                for adapter_id in adapters:
                    row = row_index.get((task_id, adapter_id))
                    if row is None:
                        missing_planned_cells.append(
                            {"adapter_id": adapter_id, "repo_id": repo_id, "split": label, "task_id": task_id}
                        )
                    cell = {
                        "repo_id": repo_id,
                        "split": label,
                        "selected_split_from_frozen_design": label,
                        "task_id": task_id,
                        "adapter_id": adapter_id,
                        **score_row_projection(row, source_score_table),
                        **metadata_projection(metadata.get(task_id, {})),
                    }
                    cells.append(cell)

    summary = summarize_cells(cells)
    diagnostics["missing_planned_cells"] = missing_planned_cells
    frozen_status = "matched"
    for repo_splits in frozen_design_details.values():
        for detail in repo_splits.values():
            if detail["missing_task_ids"] or detail["unexpected_task_ids"]:
                frozen_status = "mismatched"
    if missing_planned_cells or diagnostics["missing_score_tables"]:
        status = "invalid"
    else:
        status = "valid"

    return {
        "schema_version": "barcarolle.phase1.two_repo_task_outcome_matrix.v1",
        "generated_at": now_utc(),
        "status": status,
        "config": rel(config.get("_path", DEFAULT_CONFIG)),
        "cells": cells,
        "summary": summary,
        "frozen_design_match": {"status": frozen_status, "details": frozen_design_details},
        "diagnostics": diagnostics,
        "sanitization": {
            "raw_verifier_logs_included": False,
            "raw_patches_included": False,
            "raw_prompts_or_completions_included": False,
            "raw_acut_transcripts_included": False,
        },
        "predictive_validity_established": False,
        "production_ranking_status": "not_produced",
    }


def summarize_cells(cells: list[dict[str, Any]]) -> dict[str, Any]:
    by_repo_split: dict[str, dict[str, Any]] = {}
    by_adapter_split: dict[str, dict[str, Any]] = {}
    for key_name, keys, target in (
        ("repo_split", ("repo_id", "split"), by_repo_split),
        ("adapter_split", ("adapter_id", "split"), by_adapter_split),
    ):
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for cell in cells:
            grouped[(cell[keys[0]], cell[keys[1]])].append(cell)
        for key, group in grouped.items():
            target["/".join(key)] = summarize_group(group)

    return {
        "planned_cell_count": len(cells),
        "scoreable_cell_count": sum(1 for cell in cells if cell["scoreable_cell"]),
        "verified_pass_count": sum(1 for cell in cells if cell["verified_pass"]),
        "verified_fail_count": sum(1 for cell in cells if cell["verified_fail"]),
        "policy_violation_count": sum(1 for cell in cells if cell["policy_violation"]),
        "harness_error_count": sum(1 for cell in cells if cell["harness_error"]),
        "non_scoreable_count": sum(1 for cell in cells if not cell["scoreable_cell"]),
        "terminal_status_counts": dict(sorted(Counter(cell["terminal_status"] for cell in cells).items())),
        "by_repo_split": by_repo_split,
        "by_adapter_split": by_adapter_split,
    }


def summarize_group(cells: list[dict[str, Any]]) -> dict[str, Any]:
    scoreable = [cell for cell in cells if cell["scoreable_cell"]]
    pass_count = sum(1 for cell in scoreable if cell["verified_pass"])
    return {
        "planned_cell_count": len(cells),
        "scoreable_cell_count": len(scoreable),
        "verified_pass_count": pass_count,
        "verified_fail_count": sum(1 for cell in scoreable if cell["verified_fail"]),
        "policy_violation_count": sum(1 for cell in cells if cell["policy_violation"]),
        "pass_rate": round(pass_count / len(scoreable), 6) if scoreable else None,
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def cells_for(cells: list[dict[str, Any]], *, repo_id: str, split: str) -> list[dict[str, Any]]:
    return [cell for cell in cells if cell["repo_id"] == repo_id and cell["split"] == split]


def group_cells(cells: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cell in cells:
        value = cell.get(field)
        if isinstance(value, list):
            key = "/".join(str(item) for item in value) if value else "unknown"
        elif value in {"", None}:
            key = "unknown"
        else:
            key = str(value)
        grouped[key].append(cell)
    return {key: summarize_group(group) for key, group in sorted(grouped.items())}


def task_time_month(cell: dict[str, Any]) -> str:
    raw = str(cell.get("task_time") or "")
    return raw[:7] if len(raw) >= 7 else "unknown"


def context_ref_kind(cell: dict[str, Any]) -> str:
    ref = str(cell.get("source_context_ref") or "")
    if ref.startswith("issue:"):
        return "issue"
    if ref.startswith("pr:"):
        return "pull_request"
    return "unknown"


def attrs_h_future_task_patterns(cells: list[dict[str, Any]]) -> dict[str, Any]:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cell in cells:
        by_task[cell["task_id"]].append(cell)

    failed_on_both: list[str] = []
    passed_one_failed_one: list[str] = []
    policy_violation_tasks: list[str] = []
    task_outcomes: dict[str, dict[str, Any]] = {}
    for task_id, task_cells in sorted(by_task.items()):
        scoreable = [cell for cell in task_cells if cell["scoreable_cell"]]
        statuses_by_adapter = {cell["adapter_id"]: cell["terminal_status"] for cell in task_cells}
        pass_count = sum(1 for cell in scoreable if cell["verified_pass"])
        fail_count = sum(1 for cell in scoreable if cell["verified_fail"])
        policy_count = sum(1 for cell in task_cells if cell["policy_violation"])
        if len(scoreable) == 2 and fail_count == 2:
            failed_on_both.append(task_id)
        if pass_count and fail_count:
            passed_one_failed_one.append(task_id)
        if policy_count:
            policy_violation_tasks.append(task_id)
        task_outcomes[task_id] = {
            "statuses_by_adapter": statuses_by_adapter,
            "scoreable_cell_count": len(scoreable),
            "verified_pass_count": pass_count,
            "verified_fail_count": fail_count,
            "policy_violation_count": policy_count,
        }

    return {
        "failed_on_both_scoreable_adapters": failed_on_both,
        "passed_one_failed_one": passed_one_failed_one,
        "policy_violation_tasks": policy_violation_tasks,
        "task_outcomes": task_outcomes,
    }


def build_attrs_h_future_failure_taxonomy(
    config: dict[str, Any], matrix_payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    if matrix_payload is None:
        matrix_path = configured_output_path(config, "task_outcome_matrix")
        matrix_payload = load_json(matrix_path) if matrix_path.exists() else build_task_outcome_matrix(config)
    cells = matrix_payload["cells"]

    comparison_groups = {
        "attrs_b_eval": summarize_group(cells_for(cells, repo_id="attrs", split="B_eval")),
        "attrs_h_future": summarize_group(cells_for(cells, repo_id="attrs", split="H_future")),
        "boltons_b_eval": summarize_group(cells_for(cells, repo_id="boltons", split="B_eval")),
        "boltons_h_future": summarize_group(cells_for(cells, repo_id="boltons", split="H_future")),
    }
    attrs_h = cells_for(cells, repo_id="attrs", split="H_future")
    for cell in attrs_h:
        cell["task_time_month"] = task_time_month(cell)
        cell["source_context_ref_kind"] = context_ref_kind(cell)
        cell["policy_boundary"] = "policy_violation" if cell["policy_violation"] else "scoreable_outcome"

    concentrations = {
        "by_module_or_package": group_cells(attrs_h, "module_or_package_label"),
        "by_task_type": group_cells(attrs_h, "task_type"),
        "by_source_context_kind": group_cells(attrs_h, "source_context_kind"),
        "by_source_context_ref_kind": group_cells(attrs_h, "source_context_ref_kind"),
        "by_changed_file_count": group_cells(attrs_h, "changed_file_count"),
        "by_test_file_count": group_cells(attrs_h, "test_file_count"),
        "by_adapter": group_cells(attrs_h, "adapter_id"),
        "by_time_window": group_cells(attrs_h, "task_time_month"),
        "by_scope_clarity": group_cells(attrs_h, "scope_clarity_gate"),
        "by_policy_boundary": group_cells(attrs_h, "policy_boundary"),
    }
    patterns = attrs_h_future_task_patterns(attrs_h)

    return {
        "schema_version": "barcarolle.phase1.attrs_h_future_failure_taxonomy.v1",
        "generated_at": now_utc(),
        "status": "computed",
        "config": rel(config.get("_path", DEFAULT_CONFIG)),
        "source_matrix": rel(configured_output_path(config, "task_outcome_matrix"))
        if config.get("output_paths")
        else "",
        "comparison_groups": comparison_groups,
        "attrs_h_future": comparison_groups["attrs_h_future"],
        "attrs_h_future_concentrations": concentrations,
        "attrs_h_future_task_patterns": patterns,
        "observed_outcomes": {
            "all_four_attrs_h_future_tasks_have_at_least_one_non_pass_outcome": True,
            "codex_attrs_h_future_scoreable_pass_rate": concentrations["by_adapter"]["codex_workspace"]["pass_rate"],
            "kilo_attrs_h_future_scoreable_pass_rate": concentrations["by_adapter"]["kilo_workspace"]["pass_rate"],
            "policy_violation_cell": {
                "adapter_id": "kilo_workspace",
                "split": "H_future",
                "task_id": "attrs__hist__027",
                "terminal_status": "policy_violation",
                "scoreable_cell": False,
            },
        },
        "interpretation": {
            "breadth": "The attrs H_future collapse is broad across the four planned tasks, not a one-task artifact.",
            "adapter": "Both adapters contributed scoreable failures; Codex failed all four attrs H_future tasks, while Kilo failed two of three scoreable attrs H_future cells and had one non-scoreable policy violation.",
            "scope": "The confirmed policy violation is a benchmark boundary failure for one cell, but the scoreable collapse remains after excluding it.",
            "task_family_shift": "A task-family or time-window shift is plausible because attrs H_future moved later and touched _make, _next_gen, and _funcs, but the metadata is not strong enough to claim this as root cause.",
            "paid_validation": "The taxonomy does not justify more paid validation inside this runbook; it points to local uncertainty and baseline analysis before any spending decision.",
        },
        "main_findings": {
            "breadth": "broad_multi_task_collapse",
            "adapter_pattern": "both_adapters_with_codex_worse",
            "policy_boundary": "one_confirmed_policy_violation_not_scoreable",
            "benchmark_scope_problem": "one_cell_boundary_failure_not_full_collapse_explanation",
            "task_family_shift": "plausible_not_proven",
            "next_step": "local_uncertainty_and_baseline_analysis_before_more_paid_validation",
        },
        "sanitization": matrix_payload.get("sanitization", {}),
        "predictive_validity_established": False,
        "production_ranking_status": "not_produced",
    }


def attrs_h_future_failure_taxonomy_report(payload: dict[str, Any]) -> str:
    attrs_h = payload["attrs_h_future"]
    patterns = payload["attrs_h_future_task_patterns"]
    lines = [
        "# Phase 1 Attrs H_future Failure Taxonomy",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "## Observed Outcomes",
        "",
        f"- Attrs H_future scoreable pass rate: `{attrs_h['verified_pass_count']}/{attrs_h['scoreable_cell_count']}` = `{attrs_h['pass_rate']:.6f}`.",
        f"- Attrs H_future verified fails: `{attrs_h['verified_fail_count']}`.",
        f"- Attrs H_future policy violations: `{attrs_h['policy_violation_count']}`.",
        f"- Failed on both scoreable adapters: `{', '.join(patterns['failed_on_both_scoreable_adapters'])}`.",
        f"- Passed on one adapter and failed on one adapter: `{', '.join(patterns['passed_one_failed_one'])}`.",
        f"- Policy violation task: `{', '.join(patterns['policy_violation_tasks'])}`.",
        "",
        "## Concentration Checks",
        "",
        "| Check | Result |",
        "|---|---|",
    ]
    for label, groups in payload["attrs_h_future_concentrations"].items():
        rendered = ", ".join(
            f"{key}: {row['verified_pass_count']}/{row['scoreable_cell_count']} pass, {row['policy_violation_count']} policy"
            for key, row in groups.items()
        )
        lines.append(f"| `{label}` | {rendered} |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Breadth: attrs H_future failure is broad, not tied to one task.",
            "- Adapter pattern: both adapters have scoreable failures; Codex is worse on attrs H_future.",
            "- Benchmark scope: the `attrs__hist__027` / `kilo_workspace` policy violation is real, but it is only one non-scoreable cell and does not explain the six verified fails.",
            "- Task-family shift: plausible but not proven from the safe metadata. Change size, test count, source context status, and scope clarity do not isolate a single obvious stratum.",
            "- Spending implication: this taxonomy supports more local analysis before any paid validation decision.",
            "",
            "## Claim Boundary",
            "",
            "This report does not claim root cause, pure harness effect, repaired policy violation, predictive validity, or production ranking.",
        ]
    )
    return "\n".join(lines)


def scoreable_rate(cells: list[dict[str, Any]]) -> dict[str, Any]:
    scoreable = [cell for cell in cells if cell["scoreable_cell"]]
    pass_count = sum(1 for cell in scoreable if cell["verified_pass"])
    return {
        "pass_count": pass_count,
        "scoreable_cell_count": len(scoreable),
        "pass_rate": round(pass_count / len(scoreable), 6) if scoreable else None,
    }


def wilson_interval(pass_count: int, n: int, confidence_level: float = 0.95) -> dict[str, Any]:
    if n == 0:
        return {
            "confidence_level": confidence_level,
            "interval_method": "wilson",
            "lower": None,
            "upper": None,
        }
    z = 1.959963984540054
    phat = pass_count / n
    denominator = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denominator
    half_width = z * ((phat * (1 - phat) + z * z / (4 * n)) / n) ** 0.5 / denominator
    return {
        "confidence_level": confidence_level,
        "interval_method": "wilson",
        "lower": round(max(0.0, center - half_width), 6),
        "upper": round(min(1.0, center + half_width), 6),
    }


def interval_for_cells(cells: list[dict[str, Any]]) -> dict[str, Any]:
    rate = scoreable_rate(cells)
    return {
        **rate,
        **wilson_interval(rate["pass_count"], rate["scoreable_cell_count"]),
    }


def absolute_error(predicted: float | None, actual: float | None) -> float | None:
    if predicted is None or actual is None:
        return None
    return round(abs(predicted - actual), 6)


def mean_absolute_error(errors: list[float | None]) -> float | None:
    values = [error for error in errors if error is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def build_two_repo_uncertainty_and_baselines(
    config: dict[str, Any], matrix_payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    if matrix_payload is None:
        matrix_path = configured_output_path(config, "task_outcome_matrix")
        matrix_payload = load_json(matrix_path) if matrix_path.exists() else build_task_outcome_matrix(config)
    cells = matrix_payload["cells"]
    repos = list(config.get("selected_repos", [])) or sorted({cell["repo_id"] for cell in cells})
    adapters = listish(config.get("adapters"))

    pooled_b = [cell for cell in cells if cell["split"] == "B_eval"]
    pooled_h = [cell for cell in cells if cell["split"] == "H_future"]
    intervals = {
        "pooled_b_eval": interval_for_cells(pooled_b),
        "pooled_h_future": interval_for_cells(pooled_h),
    }
    for repo_id in repos:
        intervals[f"{repo_id}_b_eval"] = interval_for_cells(cells_for(cells, repo_id=repo_id, split="B_eval"))
        intervals[f"{repo_id}_h_future"] = interval_for_cells(cells_for(cells, repo_id=repo_id, split="H_future"))
    for adapter_id in adapters:
        intervals[f"{adapter_id}_b_eval"] = interval_for_cells(
            [cell for cell in cells if cell["adapter_id"] == adapter_id and cell["split"] == "B_eval"]
        )
        intervals[f"{adapter_id}_h_future"] = interval_for_cells(
            [cell for cell in cells if cell["adapter_id"] == adapter_id and cell["split"] == "H_future"]
        )

    pooled_b_rate = intervals["pooled_b_eval"]["pass_rate"]
    pooled_h_rate = intervals["pooled_h_future"]["pass_rate"]
    repo_errors: dict[str, Any] = {}
    for repo_id in repos:
        predicted = intervals[f"{repo_id}_b_eval"]["pass_rate"]
        actual = intervals[f"{repo_id}_h_future"]["pass_rate"]
        repo_errors[repo_id] = {
            "predicted_pass_rate": predicted,
            "actual_pass_rate": actual,
            "absolute_error": absolute_error(predicted, actual),
        }

    adapter_errors: dict[str, Any] = {}
    for adapter_id in adapters:
        predicted = intervals[f"{adapter_id}_b_eval"]["pass_rate"]
        actual = intervals[f"{adapter_id}_h_future"]["pass_rate"]
        adapter_errors[adapter_id] = {
            "predicted_pass_rate": predicted,
            "actual_pass_rate": actual,
            "absolute_error": absolute_error(predicted, actual),
        }

    repo_adapter_errors: dict[str, dict[str, Any]] = {}
    unweighted_to_repo_adapter_errors: dict[str, Any] = {}
    for repo_id in repos:
        repo_adapter_errors[repo_id] = {}
        for adapter_id in adapters:
            b_cells = [
                cell
                for cell in cells
                if cell["repo_id"] == repo_id and cell["adapter_id"] == adapter_id and cell["split"] == "B_eval"
            ]
            h_cells = [
                cell
                for cell in cells
                if cell["repo_id"] == repo_id and cell["adapter_id"] == adapter_id and cell["split"] == "H_future"
            ]
            b_rate = scoreable_rate(b_cells)["pass_rate"]
            h_rate = scoreable_rate(h_cells)["pass_rate"]
            repo_adapter_errors[repo_id][adapter_id] = {
                "predicted_pass_rate": b_rate,
                "actual_pass_rate": h_rate,
                "absolute_error": absolute_error(b_rate, h_rate),
            }
            key = f"{repo_id}/{adapter_id}"
            unweighted_to_repo_adapter_errors[key] = {
                "predicted_pass_rate": pooled_b_rate,
                "actual_pass_rate": h_rate,
                "absolute_error": absolute_error(pooled_b_rate, h_rate),
            }

    decision_path = config.get("source_decisions", {}).get("two_repo_future_holdout")
    decision = load_json(config_path(decision_path)) if decision_path else {}
    preregistered_mae = decision.get(
        "pooled_mae",
        mean_absolute_error(
            [
                adapter_result["absolute_error"]
                for repo_result in repo_adapter_errors.values()
                for adapter_result in repo_result.values()
            ]
        ),
    )

    return {
        "schema_version": "barcarolle.phase1.two_repo_uncertainty_and_baselines.v1",
        "generated_at": now_utc(),
        "status": "computed",
        "config": rel(config.get("_path", DEFAULT_CONFIG)),
        "source_matrix": rel(configured_output_path(config, "task_outcome_matrix"))
        if config.get("output_paths")
        else "",
        "intervals": intervals,
        "baseline_errors": {
            "pooled_b_eval_to_pooled_h_future": {
                "predicted_pass_rate": pooled_b_rate,
                "actual_pass_rate": pooled_h_rate,
                "absolute_error": absolute_error(pooled_b_rate, pooled_h_rate),
            },
            "repo_specific_b_eval_to_same_repo_h_future": {
                "by_repo": repo_errors,
                "mean_absolute_error": mean_absolute_error([row["absolute_error"] for row in repo_errors.values()]),
            },
            "adapter_specific_b_eval_to_same_adapter_h_future": {
                "by_adapter": adapter_errors,
                "mean_absolute_error": mean_absolute_error([row["absolute_error"] for row in adapter_errors.values()]),
            },
            "unweighted_all_b_eval_predictor_to_h_future_repo_adapter_cells": {
                "by_repo_adapter": unweighted_to_repo_adapter_errors,
                "mean_absolute_error": mean_absolute_error(
                    [row["absolute_error"] for row in unweighted_to_repo_adapter_errors.values()]
                ),
            },
            "preregistered_repo_adapter_b_eval_to_same_repo_adapter_h_future": {
                "by_repo_adapter": repo_adapter_errors,
                "mean_absolute_error": mean_absolute_error(
                    [
                        adapter_result["absolute_error"]
                        for repo_result in repo_adapter_errors.values()
                        for adapter_result in repo_result.values()
                    ]
                ),
            },
        },
        "preserved_preregistered_two_repo_result": {
            "pooled_mae": round(float(preregistered_mae), 6),
            "policy_violation_count": matrix_payload["summary"]["policy_violation_count"],
            "predictive_validity_established": False,
        },
        "policy_violation_count": matrix_payload["summary"]["policy_violation_count"],
        "non_scoreable_count": matrix_payload["summary"]["non_scoreable_count"],
        "conclusion": {
            "pilot_status": "negative_and_underpowered",
            "rationale": [
                "Point estimates are negative for predictive validity because B_eval materially overpredicts pooled H_future and attrs H_future.",
                "The sample is underpowered: only two repos and 15 H_future scoreable cells, with Wilson intervals that remain wide.",
                "The confirmed policy violation prevents a clean positive validation claim and remains non-scoreable.",
            ],
        },
        "predictive_validity_established": False,
        "production_ranking_status": "not_produced",
    }


def two_repo_uncertainty_and_baselines_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Two-Repo Uncertainty And Baselines",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "## Wilson Intervals",
        "",
        "| Group | Pass/scoreable | Pass rate | Wilson 95% interval |",
        "|---|---:|---:|---:|",
    ]
    for key, row in payload["intervals"].items():
        interval = f"[{row['lower']:.6f}, {row['upper']:.6f}]" if row["lower"] is not None else "n/a"
        lines.append(
            f"| `{key}` | `{row['pass_count']}/{row['scoreable_cell_count']}` | `{row['pass_rate']:.6f}` | `{interval}` |"
        )

    errors = payload["baseline_errors"]
    lines.extend(
        [
            "",
            "## Baseline Errors",
            "",
            f"- Pooled B_eval to pooled H_future absolute error: `{errors['pooled_b_eval_to_pooled_h_future']['absolute_error']}`.",
            f"- Repo-specific B_eval to same-repo H_future MAE: `{errors['repo_specific_b_eval_to_same_repo_h_future']['mean_absolute_error']}`.",
            f"- Adapter-specific B_eval to same-adapter H_future MAE: `{errors['adapter_specific_b_eval_to_same_adapter_h_future']['mean_absolute_error']}`.",
            f"- Unweighted all-B_eval predictor to H_future repo/adapter MAE: `{errors['unweighted_all_b_eval_predictor_to_h_future_repo_adapter_cells']['mean_absolute_error']}`.",
            f"- Preserved preregistered pooled MAE: `{payload['preserved_preregistered_two_repo_result']['pooled_mae']}`.",
            "",
            "## Interpretation",
            "",
            "The pilot is both negative and underpowered. The point estimates do not",
            "support predictive validity: pooled B_eval overpredicts pooled H_future,",
            "and attrs B_eval badly overpredicts attrs H_future. At the same time, the",
            "sample has only two repos and 15 H_future scoreable cells, so the Wilson",
            "intervals remain wide. The policy violation remains non-scoreable and",
            "predictive validity remains `false`.",
        ]
    )
    return "\n".join(lines)


def task_outcome_matrix_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Phase 1 Two-Repo Task Outcome Matrix",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "## Summary",
        "",
        f"- Status: `{payload['status']}`.",
        f"- Planned cells: `{summary['planned_cell_count']}`.",
        f"- Scoreable cells: `{summary['scoreable_cell_count']}`.",
        f"- Verified pass cells: `{summary['verified_pass_count']}`.",
        f"- Verified fail cells: `{summary['verified_fail_count']}`.",
        f"- Policy violations: `{summary['policy_violation_count']}`.",
        f"- Frozen design match: `{payload['frozen_design_match']['status']}`.",
        f"- Predictive validity established: `{payload['predictive_validity_established']}`.",
        "",
        "Policy violations remain non-scoreable. The single policy violation is expected to be",
        "`attrs__hist__027` / `kilo_workspace` in `H_future`.",
        "",
        "## Repo And Split Outcomes",
        "",
        "| Repo/split | Planned | Scoreable | Pass | Fail | Policy violations | Pass rate |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key, row in sorted(summary["by_repo_split"].items()):
        pass_rate = "n/a" if row["pass_rate"] is None else f"{row['pass_rate']:.6f}"
        lines.append(
            f"| `{key}` | `{row['planned_cell_count']}` | `{row['scoreable_cell_count']}` | "
            f"`{row['verified_pass_count']}` | `{row['verified_fail_count']}` | "
            f"`{row['policy_violation_count']}` | `{pass_rate}` |"
        )

    lines.extend(
        [
            "",
            "## Cell Matrix",
            "",
            "| Repo | Split | Adapter | Task | Status | Scoreable | Module | Changed | Tests | Context |",
            "|---|---|---|---|---|---:|---|---:|---:|---|",
        ]
    )
    for cell in payload["cells"]:
        lines.append(
            f"| `{cell['repo_id']}` | `{cell['split']}` | `{cell['adapter_id']}` | "
            f"`{cell['task_id']}` | `{cell['terminal_status']}` | `{cell['scoreable_cell']}` | "
            f"`{cell['module_or_package_label']}` | `{cell['changed_file_count']}` | "
            f"`{cell['test_file_count']}` | `{cell['source_context_ref']}` |"
        )

    lines.extend(
        [
            "",
            "## Sanitization",
            "",
            "This artifact includes score-table statuses and safe task metadata only. It",
            "does not include raw verifier logs, hidden test material, raw patches,",
            "prompts, completions, or ACUT transcripts.",
        ]
    )
    return "\n".join(lines)


def build_matrix_command(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    payload = build_task_outcome_matrix(config)
    write_json(configured_output_path(config, "task_outcome_matrix"), payload)
    write_text(configured_output_path(config, "task_outcome_matrix_report"), task_outcome_matrix_report(payload))
    print(json.dumps({"status": payload["status"], "summary": payload["summary"]}, indent=2, sort_keys=True))


def taxonomy_command(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    payload = build_attrs_h_future_failure_taxonomy(config)
    write_json(configured_output_path(config, "failure_taxonomy"), payload)
    write_text(configured_output_path(config, "failure_taxonomy_report"), attrs_h_future_failure_taxonomy_report(payload))
    print(
        json.dumps(
            {
                "status": payload["status"],
                "attrs_h_future": payload["attrs_h_future"],
                "main_findings": payload["main_findings"],
            },
            indent=2,
            sort_keys=True,
        )
    )


def uncertainty_command(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    payload = build_two_repo_uncertainty_and_baselines(config)
    write_json(configured_output_path(config, "uncertainty_and_baselines"), payload)
    write_text(
        configured_output_path(config, "uncertainty_and_baselines_report"),
        two_repo_uncertainty_and_baselines_report(payload),
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "conclusion": payload["conclusion"],
                "preserved_preregistered_two_repo_result": payload["preserved_preregistered_two_repo_result"],
            },
            indent=2,
            sort_keys=True,
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 1 attrs generalization local analysis")
    subparsers = parser.add_subparsers(dest="command", required=True)

    matrix = subparsers.add_parser("build-matrix", help="Build the two-repo task outcome matrix")
    matrix.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    matrix.set_defaults(func=build_matrix_command)

    taxonomy = subparsers.add_parser("build-taxonomy", help="Build the attrs H_future failure taxonomy")
    taxonomy.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    taxonomy.set_defaults(func=taxonomy_command)

    uncertainty = subparsers.add_parser("build-uncertainty", help="Build uncertainty and baseline error analysis")
    uncertainty.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    uncertainty.set_defaults(func=uncertainty_command)

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
