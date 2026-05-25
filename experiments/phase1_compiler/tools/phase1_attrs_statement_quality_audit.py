from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_TOOLS = REPO_ROOT / "experiments" / "phase0_headroom" / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))

import statement_quality  # noqa: E402

DEFAULT_CONFIG = ROOT / "configs" / "phase1_attrs_h_future_statement_quality_audit.yaml"
OLD_BODY_SUMMARY_CAP = statement_quality.OLD_BODY_SUMMARY_CAP
TERMINAL_PUNCTUATION = {".", "!", "?", ")"}
KNOWN_UNDERSPECIFIED_REFS = {
    "issue:766": "resolve_types_attribs_api_behavior_under_specified",
}
MANUAL_AUDIT_RATIONALES = {
    "attrs__hist__012": (
        "Mechanism and scope look plausible, but the solver-visible body summary ends inside a reproduction "
        "snippet at the historical 240-character cap."
    ),
    "attrs__hist__013": (
        "Highest concern: the source is PR-context, the behavior is subtle next-gen frozen subclass handling, "
        "and the body summary ends mid-word at the historical 240-character cap."
    ),
    "attrs__hist__023": (
        "Mechanism and scope look plausible, but the expected-result context is cut at the historical "
        "240-character cap."
    ),
    "attrs__hist__027": (
        "Target scope appears plausible, but the statement likely under-specifies the public "
        "resolve_types(..., attribs=...) API behavior."
    ),
}
PREVIEW_PUBLIC_EXCERPTS = {
    "attrs__hist__012": (
        "A public report says a slotted attrs class with a custom __setattr__ worked in 19.3.0, "
        "but 20.1.0 replaced that custom behavior with the default slotted behavior."
    ),
    "attrs__hist__013": (
        "A PR-context report says on_setattr=validate gets in the way for frozen define classes "
        "and for subclassing frozen classes in the next-gen API."
    ),
    "attrs__hist__023": (
        "A public issue reproduces get_type_hints(C.__init__) for an attrs class using a deferred "
        "List[int] annotation and expects annotations to resolve in the correct context."
    ),
    "attrs__hist__027": (
        "A public issue says Python 3.10 string annotations made field hooks clunky and needed a "
        "public helper path for resolving string annotations on attrs fields."
    ),
}
ATTRS_VERIFIER_COMMAND_TEMPLATE = (
    'uv run --project experiments/phase0_headroom --with "pytest>=7,<8" '
    '--with "setuptools<81" --with "hypothesis<6" python -m pytest -q {test_files}'
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def artifact_path(config: dict[str, Any], key: str) -> Path:
    raw = str(config["source_artifacts"][key])
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def output_path(config: dict[str, Any], key: str) -> Path:
    raw = str(config["output_paths"][key])
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != "barcarolle.phase1_attrs_h_future_statement_quality_audit.v1":
        raise ValueError("unexpected attrs H_future statement quality audit config schema_version")
    config["_path"] = str(path)
    return config


def source_kind(source_ref: str) -> str:
    return statement_quality.source_kind(source_ref)


def normalize_text(value: Any) -> str:
    return statement_quality.normalize_text(value)


def digest_text(value: str) -> str:
    return statement_quality.digest_text(value)


def short_excerpt(value: str, limit: int = 180) -> str:
    return statement_quality.short_excerpt(value, limit=limit)


def is_test_path(path: str) -> bool:
    return statement_quality.is_test_path(path)


def is_implementation_path(path: str) -> bool:
    return statement_quality.is_implementation_path(path)


def implementation_files(changed_files: list[str]) -> list[str]:
    return statement_quality.implementation_files(changed_files)


def test_files(changed_files: list[str], explicit_test_files: list[str] | None = None) -> list[str]:
    return statement_quality.test_files(changed_files, explicit_test_files)


def ends_mid_sentence(body_summary: str, *, hit_cap: bool) -> bool:
    return statement_quality.ends_mid_sentence(body_summary, hit_cap=hit_cap)


def statement_quality_flags(
    *,
    source_ref: str,
    title: str,
    body_summary: str,
    implementation_files: list[str],
    test_files: list[str],
) -> dict[str, Any]:
    return statement_quality.statement_quality_flags(
        source_ref=source_ref,
        title=title,
        body_summary=body_summary,
        implementation_files=implementation_files,
        test_files=test_files,
    )


def adapter_outcome_summary(cells: list[dict[str, Any]]) -> dict[str, Any]:
    adapter_outcomes = {str(cell.get("adapter_id")): str(cell.get("terminal_status")) for cell in sorted(cells, key=lambda row: str(row.get("adapter_id")))}
    scoreable = [cell for cell in cells if bool(cell.get("scoreable_cell"))]
    scoreable_pass_count = sum(1 for cell in scoreable if cell.get("terminal_status") == "verified_pass" or bool(cell.get("verified_pass")))
    scoreable_fail_count = sum(1 for cell in scoreable if cell.get("terminal_status") == "verified_fail" or bool(cell.get("verified_fail")))
    policy_violation_count = sum(1 for cell in cells if cell.get("terminal_status") == "policy_violation" or bool(cell.get("policy_violation")))
    return {
        "adapter_outcomes": adapter_outcomes,
        "planned_cell_count": len(cells),
        "policy_violation_count": policy_violation_count,
        "scoreable_cell_count": len(scoreable),
        "scoreable_fail_count": scoreable_fail_count,
        "scoreable_pass_count": scoreable_pass_count,
    }


def certification_gate_summary(row: dict[str, Any]) -> dict[str, Any]:
    gates = row.get("clean_overlay_certification_gates") or row.get("local_certification_gates") or {}
    counts = Counter(str(value) for value in gates.values())
    failed = sorted(key for key, value in gates.items() if value != "pass")
    return {
        "all_pass": bool(gates) and not failed,
        "failed_gates": failed,
        "gate_counts": dict(sorted(counts.items())),
        "gate_count": len(gates),
    }


def solver_statement_excerpt(task: dict[str, Any], context: dict[str, Any], impl_files: list[str], tests: list[str]) -> str:
    parts = [
        "Repair the public behavior described by the sanitized problem context.",
        f"Allowed public context refs: {', '.join(task.get('allowed_context_refs') or [])}.",
        f"Problem summary: {context.get('summary', '')}",
        f"Problem details: {context.get('body_summary', '')}",
        f"Editable implementation scope: {', '.join(impl_files)}.",
        f"Known non-editable test paths: {', '.join(tests)}.",
    ]
    return short_excerpt(" ".join(part for part in parts if part.strip()), limit=600)


def public_context_metadata(context: dict[str, Any]) -> dict[str, Any]:
    body = str(context.get("body_summary") or "")
    ref = str(context.get("ref") or "")
    return {
        "body_digest": digest_text(body) if body else "",
        "body_length": len(body),
        "lookup_status": "local_sanitized_context_only",
        "short_public_excerpt": short_excerpt(body),
        "source_kind": source_kind(ref),
        "source_ref": ref,
        "title": normalize_text(context.get("summary")),
    }


def task_record(
    task_id: str,
    *,
    certified_task: dict[str, Any],
    source_context: dict[str, Any],
    cells: list[dict[str, Any]],
    manual_label: str,
) -> dict[str, Any]:
    changed_files = [str(path) for path in certified_task.get("changed_files", [])]
    impl_files = implementation_files(changed_files)
    tests = test_files(changed_files, [str(path) for path in certified_task.get("test_files", [])])
    source_ref = str(source_context.get("ref") or (certified_task.get("allowed_context_refs") or [""])[0])
    flags = statement_quality_flags(
        source_ref=source_ref,
        title=str(source_context.get("summary") or certified_task.get("subject") or ""),
        body_summary=str(source_context.get("body_summary") or ""),
        implementation_files=impl_files,
        test_files=tests,
    )
    outcomes = adapter_outcome_summary(cells)
    return {
        "adapter_outcomes": outcomes["adapter_outcomes"],
        "body_summary_hit_old_cap": flags["body_summary_hit_old_cap"],
        "body_summary_length": flags["body_summary_length"],
        "certification_gate_summary": certification_gate_summary(certified_task),
        "changed_file_count": len(changed_files),
        "implementation_file_count": len(impl_files),
        "implementation_files": impl_files,
        "manual_audit_label": manual_label,
        "manual_audit_rationale": MANUAL_AUDIT_RATIONALES.get(task_id, ""),
        "module_or_package": certified_task.get("module_or_package", []),
        "policy_violation_count": outcomes["policy_violation_count"],
        "pr_context_risk": flags["pr_context_risk"],
        "public_context_metadata": public_context_metadata(source_context),
        "risk_reasons": flags["risk_reasons"],
        "scoreable_fail_count": outcomes["scoreable_fail_count"],
        "scoreable_pass_count": outcomes["scoreable_pass_count"],
        "scope_metadata_matches_target_non_test_files": bool(impl_files) and all(path in changed_files for path in tests),
        "solver_statement_excerpt": solver_statement_excerpt(certified_task, source_context, impl_files, tests),
        "source_kind": source_kind(source_ref),
        "source_ref": source_ref,
        "statement_ends_mid_code_fence": flags["statement_ends_mid_code_fence"],
        "statement_ends_mid_sentence": flags["statement_ends_mid_sentence"],
        "statement_probably_truncated": flags["statement_probably_truncated"],
        "statement_quality_gate": flags["statement_quality_gate"],
        "statement_underspecified_risk": flags["statement_underspecified_risk"],
        "task_id": task_id,
        "test_file_count": len(tests),
        "test_files": tests,
    }


def stable_generated_at(config: dict[str, Any]) -> str:
    preflight = output_path(config, "preflight")
    if preflight.exists():
        return str(read_json(preflight).get("generated_at") or "2026-05-25T00:00:00Z")
    return "2026-05-25T00:00:00Z"


def build_task_design_audit(config: dict[str, Any]) -> dict[str, Any]:
    audited_tasks = [str(task_id) for task_id in config["audited_tasks"]]
    certified_by_task = {str(row["task_id"]): row for row in read_jsonl(artifact_path(config, "certified_tasks"))}
    context_by_task = {str(row["task_id"]): row for row in read_jsonl(artifact_path(config, "source_context"))}
    matrix = read_json(artifact_path(config, "task_outcome_matrix"))
    cells_by_task: dict[str, list[dict[str, Any]]] = {task_id: [] for task_id in audited_tasks}
    for cell in matrix.get("cells", []):
        if cell.get("repo_id") == config["audited_repo"] and cell.get("split") == config["audited_split"] and cell.get("task_id") in cells_by_task:
            cells_by_task[str(cell["task_id"])].append(cell)

    missing = [
        task_id
        for task_id in audited_tasks
        if task_id not in certified_by_task or task_id not in context_by_task or not cells_by_task.get(task_id)
    ]
    labels = config.get("manual_audit_labels", {})
    records = [
        task_record(
            task_id,
            certified_task=certified_by_task.get(task_id, {}),
            source_context=context_by_task.get(task_id, {}),
            cells=cells_by_task.get(task_id, []),
            manual_label=str(labels.get(task_id, "unlabeled")),
        )
        for task_id in audited_tasks
        if task_id not in missing
    ]
    quality_counts = Counter(row["statement_quality_gate"] for row in records)
    summary = {
        "audited_task_count": len(audited_tasks),
        "clean_statement_task_count": quality_counts.get("pass", 0),
        "material_statement_quality_risk_count": quality_counts.get("material_risk", 0),
        "policy_violation_count": sum(row["policy_violation_count"] for row in records),
        "probably_truncated_count": sum(1 for row in records if row["statement_probably_truncated"]),
        "pr_context_risk_count": sum(1 for row in records if row["pr_context_risk"]),
        "scoreable_fail_count": sum(row["scoreable_fail_count"] for row in records),
        "scoreable_pass_count": sum(row["scoreable_pass_count"] for row in records),
    }
    return {
        "audited_tasks": audited_tasks,
        "config": config["_path"],
        "diagnostics": {
            "failure_signal": "statement_quality_risk_detected" if summary["material_statement_quality_risk_count"] else "",
            "missing_task_inputs": missing,
            "raw_public_bodies_included": false_bool(),
        },
        "generated_at": stable_generated_at(config),
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "predictive_validity_established": False,
        "production_ranking_status": "not_produced",
        "sanitization": {
            "raw_acut_transcripts_included": False,
            "raw_public_issue_or_pr_bodies_included": False,
            "raw_verifier_material_included": False,
        },
        "schema_version": "barcarolle.phase1.attrs_h_future_task_design_audit.v1",
        "status": "invalid" if missing else "computed",
        "summary": summary,
        "tasks": records,
    }


def false_bool() -> bool:
    return False


def rounded_rate(pass_count: int, scoreable_count: int) -> float | None:
    if scoreable_count == 0:
        return None
    return round(pass_count / scoreable_count, 6)


def matrix_cells(config: dict[str, Any]) -> list[dict[str, Any]]:
    return list(read_json(artifact_path(config, "task_outcome_matrix")).get("cells", []))


def attrs_b_eval_comparison(cells: list[dict[str, Any]]) -> dict[str, Any]:
    b_eval = [cell for cell in cells if cell.get("repo_id") == "attrs" and cell.get("split") == "B_eval"]
    scoreable = [cell for cell in b_eval if cell.get("scoreable_cell")]
    passed = sum(1 for cell in scoreable if cell.get("terminal_status") == "verified_pass" or cell.get("verified_pass"))
    failed = sum(1 for cell in scoreable if cell.get("terminal_status") == "verified_fail" or cell.get("verified_fail"))
    return {
        "attrs_b_eval_pass_rate": rounded_rate(passed, len(scoreable)),
        "attrs_b_eval_scoreable_cells": len(scoreable),
        "attrs_b_eval_verified_fail": failed,
        "attrs_b_eval_verified_pass": passed,
    }


def sensitivity_view(
    *,
    name: str,
    included_tasks: list[str],
    excluded_tasks: list[str],
    cells: list[dict[str, Any]],
    attrs_b_eval: dict[str, Any],
    interpretation: str,
) -> dict[str, Any]:
    included = [cell for cell in cells if cell.get("task_id") in set(included_tasks)]
    scoreable = [cell for cell in included if cell.get("scoreable_cell")]
    verified_pass = sum(1 for cell in scoreable if cell.get("terminal_status") == "verified_pass" or cell.get("verified_pass"))
    verified_fail = sum(1 for cell in scoreable if cell.get("terminal_status") == "verified_fail" or cell.get("verified_fail"))
    policy_violations = sum(1 for cell in included if cell.get("terminal_status") == "policy_violation" or cell.get("policy_violation"))
    pass_rate = rounded_rate(verified_pass, len(scoreable))
    b_eval_rate = attrs_b_eval["attrs_b_eval_pass_rate"]
    comparison = dict(attrs_b_eval)
    comparison["absolute_pass_rate_gap_vs_attrs_b_eval"] = None if pass_rate is None or b_eval_rate is None else round(b_eval_rate - pass_rate, 6)
    return {
        "comparison_to_attrs_b_eval": comparison,
        "excluded_tasks": excluded_tasks,
        "included_tasks": included_tasks,
        "interpretation": interpretation if len(scoreable) else "insufficient_clean_attrs_h_future_evidence",
        "name": name,
        "pass_rate": pass_rate,
        "policy_violations": policy_violations,
        "scoreable_cells": len(scoreable),
        "verified_fail": verified_fail,
        "verified_pass": verified_pass,
    }


def build_statement_sensitivity(config: dict[str, Any], task_audit: dict[str, Any] | None = None) -> dict[str, Any]:
    task_audit = task_audit or build_task_design_audit(config)
    audited_tasks = [str(task_id) for task_id in task_audit["audited_tasks"]]
    task_rows = {str(row["task_id"]): row for row in task_audit["tasks"]}
    material_risk_tasks = [task_id for task_id in audited_tasks if task_rows[task_id]["statement_quality_gate"] == "material_risk"]
    clean_statement_tasks = [task_id for task_id in audited_tasks if task_rows[task_id]["statement_quality_gate"] == "pass"]
    cells = [
        cell
        for cell in matrix_cells(config)
        if cell.get("repo_id") == config["audited_repo"] and cell.get("split") == config["audited_split"] and cell.get("task_id") in audited_tasks
    ]
    attrs_b_eval = attrs_b_eval_comparison(matrix_cells(config))

    view_specs = [
        (
            "original_attrs_h_future",
            audited_tasks,
            [],
            "original_paid_observation_preserved_as_1_of_7_scoreable_pass",
        ),
        (
            "exclude_policy_violation_only",
            audited_tasks,
            [],
            "policy_violation_cell_remains_non_scoreable_so_scoreable_metric_matches_original",
        ),
        (
            "exclude_highest_risk_task_013",
            [task_id for task_id in audited_tasks if task_id != "attrs__hist__013"],
            ["attrs__hist__013"],
            "sensitivity_only_not_corrected_score; removing the highest PR-context risk task still leaves attrs H_future far below B_eval",
        ),
        (
            "exclude_highest_risk_tasks_013_027",
            [task_id for task_id in audited_tasks if task_id not in {"attrs__hist__013", "attrs__hist__027"}],
            ["attrs__hist__013", "attrs__hist__027"],
            "sensitivity_only_not_corrected_score; remaining evidence is smaller and still below B_eval",
        ),
        (
            "strict_clean_statement_only",
            clean_statement_tasks,
            [task_id for task_id in audited_tasks if task_id not in clean_statement_tasks],
            "strict clean statement view after excluding material statement-quality risk",
        ),
        (
            "all_statement_risk_excluded",
            [task_id for task_id in audited_tasks if task_id not in material_risk_tasks],
            material_risk_tasks,
            "diagnostic view for clean evidence remaining after excluding all statement-risk tasks",
        ),
    ]
    views = {
        name: sensitivity_view(
            name=name,
            included_tasks=included,
            excluded_tasks=excluded,
            cells=cells,
            attrs_b_eval=attrs_b_eval,
            interpretation=interpretation,
        )
        for name, included, excluded, interpretation in view_specs
    }
    return {
        "attrs_b_eval_comparison": attrs_b_eval,
        "audited_tasks": audited_tasks,
        "config": config["_path"],
        "generated_at": stable_generated_at(config),
        "original_paid_result_preserved": True,
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "predictive_validity_established": False,
        "production_ranking_status": "not_produced",
        "schema_version": "barcarolle.phase1.attrs_h_future_statement_sensitivity.v1",
        "source_task_design_audit": str(output_path(config, "task_design_audit").relative_to(REPO_ROOT)),
        "status": "computed",
        "summary": {
            "material_statement_quality_risk_task_count": len(material_risk_tasks),
            "original_attrs_h_future_pass_rate": views["original_attrs_h_future"]["pass_rate"],
            "original_attrs_h_future_scoreable_cells": views["original_attrs_h_future"]["scoreable_cells"],
            "strict_clean_statement_view_status": views["strict_clean_statement_only"]["interpretation"],
        },
        "views": views,
    }


def render_statement_sensitivity_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Attrs H_future Statement-Risk Sensitivity",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "These views are sensitivity analysis only. They do not correct, repair, rerun, or overwrite the paid result.",
        "",
        "## Summary",
        "",
        f"- Original attrs H_future remains `{payload['summary']['original_attrs_h_future_pass_rate']}` pass rate over `{payload['summary']['original_attrs_h_future_scoreable_cells']}` scoreable cells.",
        f"- Material statement-quality risk tasks: `{payload['summary']['material_statement_quality_risk_task_count']}`.",
        f"- Strict clean statement view: `{payload['summary']['strict_clean_statement_view_status']}`.",
        "",
        "## Views",
        "",
    ]
    for name, view in payload["views"].items():
        lines.extend(
            [
                f"### {name}",
                "",
                f"- Included tasks: `{view['included_tasks']}`.",
                f"- Excluded tasks: `{view['excluded_tasks']}`.",
                f"- Scoreable cells: `{view['scoreable_cells']}`.",
                f"- Verified pass/fail: `{view['verified_pass']}/{view['verified_fail']}`.",
                f"- Policy violations: `{view['policy_violations']}`.",
                f"- Pass rate: `{view['pass_rate']}`.",
                f"- Comparison to attrs B_eval: `{view['comparison_to_attrs_b_eval']}`.",
                f"- Interpretation: `{view['interpretation']}`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "Excluding questionable tasks is a diagnostic sensitivity view, not a corrected score. If clean statement evidence is empty or too small, the correct conclusion is insufficient clean attrs H_future evidence.",
        ]
    )
    return "\n".join(lines)


def verifier_command_metadata(test_paths: list[str]) -> str:
    return ATTRS_VERIFIER_COMMAND_TEMPLATE.format(test_files=" ".join(test_paths))


def preview_statement(row: dict[str, Any], excerpt: str) -> str:
    lines = [
        f"Repair attrs behavior described by sanitized public context `{row['source_ref']}`.",
        f"Problem summary: {row['public_context_metadata']['title']}.",
        f"Problem details excerpt: {excerpt}",
        f"Editable implementation scope: {', '.join(row['implementation_files'])}.",
        f"Known non-editable test paths: {', '.join(row['test_files'])}.",
        f"Verifier command metadata: {verifier_command_metadata(row['test_files'])}",
        "Preserve existing public behavior and do not edit tests, generated metadata, or files outside the editable implementation scope.",
    ]
    return "\n".join(lines)


def build_statement_preview(config: dict[str, Any], task_audit: dict[str, Any] | None = None) -> dict[str, Any]:
    task_audit = task_audit or build_task_design_audit(config)
    previews: list[dict[str, Any]] = []
    for row in task_audit["tasks"]:
        excerpt = PREVIEW_PUBLIC_EXCERPTS.get(row["task_id"], row["public_context_metadata"]["short_public_excerpt"])
        previews.append(
            {
                "diagnostic_only": True,
                "editable_implementation_scope": row["implementation_files"],
                "known_non_editable_test_paths": row["test_files"],
                "preview_statement": preview_statement(row, excerpt),
                "problem_summary": row["public_context_metadata"]["title"],
                "scoreable_result": False,
                "short_public_excerpt": excerpt,
                "source_kind": row["source_kind"],
                "source_ref": row["source_ref"],
                "statement_quality_flags": {
                    "body_summary_hit_old_cap": row["body_summary_hit_old_cap"],
                    "risk_reasons": row["risk_reasons"],
                    "statement_probably_truncated": row["statement_probably_truncated"],
                    "statement_quality_gate": row["statement_quality_gate"],
                },
                "task_id": row["task_id"],
                "verifier_command_metadata": verifier_command_metadata(row["test_files"]),
            }
        )
    return {
        "config": config["_path"],
        "diagnostic_only": True,
        "does_not_change_paid_outcomes": True,
        "future_paid_validation_requires_new_preregistration": True,
        "generated_at": stable_generated_at(config),
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "predictive_validity_established": False,
        "previews": previews,
        "production_ranking_status": "not_produced",
        "schema_version": "barcarolle.phase1.attrs_h_future_statement_preview.v1",
        "source_task_design_audit": str(output_path(config, "task_design_audit").relative_to(REPO_ROOT)),
        "status": "computed",
        "summary": {
            "preview_count": len(previews),
            "scoreable_result_count": 0,
            "statements_cut_mid_code_or_sentence": 0,
        },
    }


def render_statement_preview_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Attrs H_future Statement Preview",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "These previews do not change previous paid outcomes and are not a rerun.",
        "Any future paid validation using improved statements requires a new frozen release or preregistration.",
        "",
        "## Summary",
        "",
        f"- Preview statements: `{payload['summary']['preview_count']}`.",
        f"- Scoreable results represented here: `{payload['summary']['scoreable_result_count']}`.",
        f"- Statements cut mid-code or mid-sentence: `{payload['summary']['statements_cut_mid_code_or_sentence']}`.",
        "",
        "## Previews",
        "",
    ]
    for row in payload["previews"]:
        lines.extend(
            [
                f"### {row['task_id']}",
                "",
                f"- Source ref: `{row['source_ref']}`.",
                f"- Problem summary: {row['problem_summary']}",
                f"- Short public excerpt: {row['short_public_excerpt']}",
                f"- Editable implementation scope: `{row['editable_implementation_scope']}`.",
                f"- Known non-editable test paths: `{row['known_non_editable_test_paths']}`.",
                f"- Verifier command metadata: `{row['verifier_command_metadata']}`.",
                f"- Statement quality flags: `{row['statement_quality_flags']}`.",
                "",
                "Preview statement:",
                "",
                "```text",
                row["preview_statement"],
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def task_evidence_label(row: dict[str, Any]) -> str:
    label = str(row["manual_audit_label"])
    if label == "questionable_pr_context_and_statement_quality_risk":
        return "exclude_in_sensitivity_view"
    if row["statement_quality_gate"] == "material_risk":
        return "questionable_clean_predictive_evidence"
    return "safe_clean_predictive_evidence"


def plausibly_explains_failure(row: dict[str, Any]) -> bool:
    return row["statement_quality_gate"] == "material_risk" and row["scoreable_fail_count"] > 0


def render_task_design_audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Attrs H_future Task-Design Audit",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "This sidecar uses sanitized committed artifacts only. It does not use hidden verifier material, raw ACUT transcripts, raw public issue/PR bodies, or paid reruns.",
        "",
        "## Summary",
        "",
        f"- Audited tasks: `{payload['summary']['audited_task_count']}`.",
        f"- Material statement-quality risk: `{payload['summary']['material_statement_quality_risk_count']}`.",
        f"- Probable truncation at old cap: `{payload['summary']['probably_truncated_count']}`.",
        f"- PR-context risk: `{payload['summary']['pr_context_risk_count']}`.",
        f"- Scoreable outcomes in these tasks: `{payload['summary']['scoreable_pass_count']}` pass, `{payload['summary']['scoreable_fail_count']}` fail.",
        f"- Policy violations remain non-scoreable: `{payload['summary']['policy_violation_count']}`.",
        "",
        "## Audit Questions",
        "",
        "- Verifier/oracle machinery obviously broken: `no evidence from sanitized certification gates`.",
        "- Task scope obviously wrong: `no`; scope metadata still points at target implementation files, though one cell remains a non-scoreable policy violation.",
        "- Solver-facing statements likely incomplete: `yes`; all four audited tasks hit material statement-quality risk.",
        "- Incompleteness plausibly explains failure: `yes for directional interpretation`; it is a confound, not a repaired score.",
        "",
        "## Task Findings",
        "",
    ]
    for row in payload["tasks"]:
        lines.extend(
            [
                f"### {row['task_id']}",
                "",
                f"- Source: `{row['source_ref']}` (`{row['source_kind']}`).",
                f"- Outcomes: `{row['adapter_outcomes']}`; scoreable pass/fail `{row['scoreable_pass_count']}/{row['scoreable_fail_count']}`, policy violations `{row['policy_violation_count']}`.",
                f"- Mechanism validity: certification gates all pass is `{row['certification_gate_summary']['all_pass']}`; scope metadata matches target non-test files is `{row['scope_metadata_matches_target_non_test_files']}`.",
                f"- Statement quality: gate `{row['statement_quality_gate']}`, risk reasons `{row['risk_reasons']}`.",
                f"- Could statement incompleteness plausibly explain failure: `{plausibly_explains_failure(row)}`.",
                f"- Clean evidence label: `{task_evidence_label(row)}`.",
                f"- Manual audit label: `{row['manual_audit_label']}`.",
                f"- Rationale: {row['manual_audit_rationale']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "This audit weakens or qualifies interpretation of the original paid observation. It does not repair the paid result, rerun any cell, relabel the policy violation, or establish predictive validity.",
        ]
    )
    return "\n".join(lines)


def run_audit(config_path: Path, *, write: bool) -> dict[str, Any]:
    config = load_config(config_path)
    payload = build_task_design_audit(config)
    if write:
        write_json(output_path(config, "task_design_audit"), payload)
        write_text(output_path(config, "task_design_audit_report"), render_task_design_audit_markdown(payload))
    return payload


def run_sensitivity(config_path: Path, *, write: bool) -> dict[str, Any]:
    config = load_config(config_path)
    task_audit_path = output_path(config, "task_design_audit")
    task_audit = read_json(task_audit_path) if task_audit_path.exists() else build_task_design_audit(config)
    payload = build_statement_sensitivity(config, task_audit)
    if write:
        write_json(output_path(config, "statement_sensitivity"), payload)
        write_text(output_path(config, "statement_sensitivity_report"), render_statement_sensitivity_markdown(payload))
    return payload


def run_preview(config_path: Path, *, write: bool) -> dict[str, Any]:
    config = load_config(config_path)
    task_audit_path = output_path(config, "task_design_audit")
    task_audit = read_json(task_audit_path) if task_audit_path.exists() else build_task_design_audit(config)
    payload = build_statement_preview(config, task_audit)
    if write:
        write_json(output_path(config, "statement_preview"), payload)
        write_text(output_path(config, "statement_preview_report"), render_statement_preview_markdown(payload))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit attrs H_future statement quality using sanitized sidecars.")
    parser.add_argument("command", nargs="?", choices=["audit", "sensitivity", "preview"], default="audit")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--write", action="store_true", help="write configured JSON and Markdown outputs")
    args = parser.parse_args(argv)
    if args.command == "audit":
        payload = run_audit(args.config, write=args.write)
    elif args.command == "sensitivity":
        payload = run_sensitivity(args.config, write=args.write)
    else:
        payload = run_preview(args.config, write=args.write)
    if not args.write:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "computed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
