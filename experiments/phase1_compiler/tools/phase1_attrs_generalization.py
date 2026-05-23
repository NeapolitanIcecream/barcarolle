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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 1 attrs generalization local analysis")
    subparsers = parser.add_subparsers(dest="command", required=True)

    matrix = subparsers.add_parser("build-matrix", help="Build the two-repo task outcome matrix")
    matrix.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    matrix.set_defaults(func=build_matrix_command)

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
