from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "phase1_attrs_h_future_statement_quality_audit.yaml"
OLD_BODY_SUMMARY_CAP = 240
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
    if source_ref.startswith("issue:"):
        return "issue"
    if source_ref.startswith("pr:"):
        return "pull_request"
    if source_ref.startswith("commit:"):
        return "commit"
    return "unknown"


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def short_excerpt(value: str, limit: int = 180) -> str:
    text = normalize_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def is_test_path(path: str) -> bool:
    return path.startswith("tests/") or path.startswith("test/") or "/tests/" in path or Path(path).name.startswith("test_")


def is_implementation_path(path: str) -> bool:
    if is_test_path(path):
        return False
    if path in {"conftest.py", "setup.py", "noxfile.py", "tox.ini", "pyproject.toml", "setup.cfg"}:
        return False
    if path.startswith("changelog.d/") or path.startswith("docs/") or path.startswith(".github/"):
        return False
    return path.endswith((".py", ".pyi"))


def implementation_files(changed_files: list[str]) -> list[str]:
    return sorted(path for path in changed_files if is_implementation_path(path))


def test_files(changed_files: list[str], explicit_test_files: list[str] | None = None) -> list[str]:
    if explicit_test_files:
        return sorted(str(path) for path in explicit_test_files)
    return sorted(path for path in changed_files if is_test_path(path))


def ends_mid_sentence(body_summary: str, *, hit_cap: bool) -> bool:
    text = body_summary.rstrip()
    if not text:
        return True
    if not hit_cap:
        return False
    if text[-1] in TERMINAL_PUNCTUATION or text.endswith("```"):
        return False
    if text[-1] in {":", ",", ";", "-", "("}:
        return True
    tail_words = re.findall(r"[A-Za-z_]+", text[-40:].lower())
    if tail_words and tail_words[-1] in {"a", "an", "the", "to", "be", "fr", "if", "or", "and"}:
        return True
    return True


def statement_quality_flags(
    *,
    source_ref: str,
    title: str,
    body_summary: str,
    implementation_files: list[str],
    test_files: list[str],
) -> dict[str, Any]:
    body = body_summary or ""
    hit_cap = len(body) >= OLD_BODY_SUMMARY_CAP
    mid_code_fence = body.count("```") % 2 == 1
    mid_sentence = ends_mid_sentence(body, hit_cap=hit_cap)
    nearly_empty = len(normalize_text(body)) < 20
    missing_problem_summary = not normalize_text(title) or nearly_empty
    missing_scope = not implementation_files
    pr_risk = source_ref.startswith("pr:")
    known_under_spec = KNOWN_UNDERSPECIFIED_REFS.get(source_ref)
    probably_truncated = bool(hit_cap and (mid_code_fence or mid_sentence))

    risk_reasons: list[str] = []
    if hit_cap:
        risk_reasons.append("body_summary_hit_old_240_char_cap")
    if mid_code_fence:
        risk_reasons.append("statement_ends_mid_code_fence")
    if probably_truncated:
        risk_reasons.append("statement_probably_truncated")
    if pr_risk:
        risk_reasons.append("pr_context_source")
    if known_under_spec:
        risk_reasons.append(known_under_spec)
    if nearly_empty:
        risk_reasons.append("empty_or_nearly_empty_body_summary")
    if missing_problem_summary:
        risk_reasons.append("statement_missing_public_problem_summary")
    if missing_scope:
        risk_reasons.append("statement_missing_editable_implementation_scope")

    material_risk = bool(probably_truncated or pr_risk or known_under_spec or nearly_empty or missing_problem_summary or missing_scope)
    return {
        "body_summary_hit_old_cap": hit_cap,
        "body_summary_length": len(body),
        "diagnostics": {
            "failure_signal": "statement_quality_risk_detected" if material_risk else "",
            "risk_flag_count": len(risk_reasons),
        },
        "empty_or_nearly_empty_body_summary": nearly_empty,
        "pr_context_risk": pr_risk,
        "risk_reasons": risk_reasons,
        "statement_ends_mid_code_fence": mid_code_fence,
        "statement_ends_mid_sentence": mid_sentence,
        "statement_missing_editable_implementation_scope": missing_scope,
        "statement_missing_public_problem_summary": missing_problem_summary,
        "statement_probably_truncated": probably_truncated,
        "statement_quality_gate": "material_risk" if material_risk else "pass",
        "statement_underspecified_risk": bool(material_risk and not probably_truncated),
    }


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


def task_evidence_label(row: dict[str, Any]) -> str:
    label = str(row["manual_audit_label"])
    if label == "questionable_pr_context_and_statement_quality_risk":
        return "exclude_in_sensitivity_view"
    if row["statement_quality_gate"] == "material_risk":
        return "questionable_clean_predictive_evidence"
    return "safe_clean_predictive_evidence"


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit attrs H_future statement quality using sanitized sidecars.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--write", action="store_true", help="write configured JSON and Markdown outputs")
    args = parser.parse_args(argv)
    payload = run_audit(args.config, write=args.write)
    if not args.write:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "computed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

