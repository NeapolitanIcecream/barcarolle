from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from phase1_future_holdout import parse_task_time, simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
PHASE0_TOOLS = PHASE0_ROOT / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))

import statement_quality  # noqa: E402


DEFAULT_CONFIG = ROOT / "configs" / "phase1_statement_hardened_holdout_preregistration.yaml"
RELEASE_ID = "statement_hardened_two_repo_holdout_20260525"
PAID_VALIDATION_PREFIX = "phase1_statement_hardened_paid_validation_20260525"
SOLUTION_EXPOSURE_TERMS = {
    "refactor",
    "rework",
    "rename",
    "wrapped",
    "move ",
    "changed implementation",
    "use raw strings",
    "according to review",
}
FORBIDDEN_PREVIEW_TERMS = {
    "diff --git": "raw_diff_in_statement_preview",
    "gold patch": "gold_patch_in_statement_preview",
    "hidden verifier": "hidden_verifier_in_statement_preview",
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


def rel(path: Path | str) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def config_path(raw: str | Path) -> Path:
    path = Path(str(raw))
    return path if path.is_absolute() else REPO_ROOT / path


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != "barcarolle.phase1_statement_hardened_holdout_preregistration.v1":
        raise ValueError("unexpected statement-hardened preregistration config schema_version")
    config["_path"] = str(path)
    return config


def artifact_path(config: dict[str, Any], key: str) -> Path:
    return config_path(str(config["source_artifacts"][key]))


def output_path(config: dict[str, Any], key: str) -> Path:
    return config_path(str(config["output_paths"][key]))


def stable_generated_at(config: dict[str, Any]) -> str:
    preflight = output_path(config, "preflight")
    if preflight.exists():
        return str(read_json(preflight).get("generated_at") or config.get("created_at") or "2026-05-25T00:00:00Z")
    return str(config.get("created_at") or "2026-05-25T00:00:00Z")


def digest_file(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def row_by_task(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["task_id"]): row for row in rows if row.get("task_id")}


def unique_sorted(values: list[str]) -> list[str]:
    return sorted(dict.fromkeys(str(value) for value in values if str(value)))


def source_kind(source_ref: str) -> str:
    return statement_quality.source_kind(source_ref)


def implementation_files_for(row: dict[str, Any]) -> list[str]:
    code_files = [str(path) for path in row.get("code_files", []) if statement_quality.is_implementation_path(str(path))]
    if code_files:
        return sorted(code_files)
    changed_files = [str(path) for path in row.get("changed_files", [])]
    return statement_quality.implementation_files(changed_files)


def test_files_for(row: dict[str, Any]) -> list[str]:
    changed_files = [str(path) for path in row.get("changed_files", [])]
    explicit = [str(path) for path in row.get("test_files", [])]
    return statement_quality.test_files(changed_files, explicit)


def certification_gate_summary(row: dict[str, Any]) -> dict[str, Any]:
    gates = row.get("clean_overlay_certification_gates") or row.get("local_certification_gates") or row.get("gates") or {}
    failed = sorted(str(key) for key, value in gates.items() if value != "pass")
    return {
        "all_pass": bool(gates) and not failed,
        "failed_gates": failed,
        "gate_count": len(gates),
        "gate_counts": dict(sorted(Counter(str(value) for value in gates.values()).items())),
    }


def change_size_bucket(row: dict[str, Any]) -> str:
    count = len(row.get("changed_files", []) or [])
    if count <= 2:
        return "small"
    if count <= 5:
        return "medium"
    return "large"


def split_eligibility(row: dict[str, Any]) -> list[str]:
    split = str(row.get("split") or "")
    if split in {"B_real", "B_eval"}:
        return ["B_eval"]
    if split in {"W_real", "H_future"}:
        return ["H_future"]
    return ["B_eval", "H_future"]


def verifier_command_metadata(repo_id: str, test_paths: list[str]) -> str:
    tests = " ".join(test_paths)
    if repo_id == "attrs":
        return (
            'uv run --project experiments/phase0_headroom --with "pytest>=7,<8" '
            f'--with "setuptools<81" --with "hypothesis<6" python -m pytest -q {tests}'
        )
    return f'uv run --project experiments/phase0_headroom --with "pytest>=7,<8" python -m pytest -q {tests}'


def problem_context_rationale(
    *,
    source_ref: str,
    context: dict[str, Any],
    quality: dict[str, Any],
) -> str:
    if source_kind(source_ref) != "pull_request":
        return ""
    text = statement_quality.normalize_text(f"{context.get('summary', '')} {context.get('body_summary', '')}")
    linked = statement_quality.linked_issue_refs(text)
    if linked:
        return f"PR context kept for manual review because it links public issue refs {', '.join(linked)}."
    if (
        context.get("classification") == "problem_context"
        and len(statement_quality.normalize_text(context.get("body_summary"))) >= 80
        and not quality.get("statement_probably_truncated")
    ):
        return "PR context kept for manual review because the sanitized body gives problem-context detail without hidden or target diff material."
    return ""


def severe_statement_risks(
    *,
    context: dict[str, Any],
    target_commit: str,
    quality: dict[str, Any],
    statement_text: str,
    source_context_status: str,
) -> list[str]:
    risks: list[str] = []
    if source_context_status != "non_leaky_problem_context":
        risks.append("public_problem_context_missing")
    if str(context.get("classification") or "") != "problem_context":
        risks.append("source_context_not_problem_context")
    if str(context.get("ref") or "").startswith("commit:"):
        risks.append("commit_context_not_allowed")
    if quality.get("statement_probably_truncated"):
        risks.append("statement_probably_truncated")
    if quality.get("statement_ends_mid_code_fence"):
        risks.append("statement_ends_mid_code_fence")
    if quality.get("empty_or_nearly_empty_body_summary"):
        risks.append("empty_or_nearly_empty_body_summary")
    if quality.get("statement_missing_public_problem_summary"):
        risks.append("statement_missing_public_problem_summary")
    if quality.get("statement_missing_editable_implementation_scope"):
        risks.append("statement_missing_editable_implementation_scope")
    lowered = statement_text.lower()
    for needle, reason in FORBIDDEN_PREVIEW_TERMS.items():
        if needle in lowered:
            risks.append(reason)
    if target_commit and target_commit in statement_text:
        risks.append("target_commit_in_statement_preview")
    return unique_sorted(risks)


def statement_preview_text(record: dict[str, Any]) -> str:
    lines = [
        f"Repair {record['repo_id']} behavior described by sanitized public context `{record['source_ref']}`.",
        f"Problem summary: {record['problem_summary']}.",
        f"Short public excerpt: {record['short_sanitized_public_excerpt']}",
        f"Editable implementation scope: {', '.join(record['implementation_files'])}.",
        f"Known non-editable test paths: {', '.join(record['test_files'])}.",
        f"Verifier command metadata: {record['verifier_command_metadata']}",
        "Preserve existing public behavior and do not edit tests, generated metadata, verifier files, or files outside the editable implementation scope.",
    ]
    return "\n".join(line for line in lines if line.strip())


def statement_quality_record(
    *,
    context: dict[str, Any],
    row: dict[str, Any],
    impl_files: list[str],
    tests: list[str],
) -> dict[str, Any]:
    source_ref = str(context.get("ref") or (row.get("allowed_context_refs") or [""])[0])
    flags = statement_quality.statement_quality_flags(
        source_ref=source_ref,
        title=str(context.get("summary") or row.get("subject") or ""),
        body_summary=str(context.get("body_summary") or ""),
        implementation_files=impl_files,
        test_files=tests,
    )
    rationale = problem_context_rationale(source_ref=source_ref, context=context, quality=flags)
    severe = severe_statement_risks(
        context=context,
        target_commit=str(row.get("target_commit") or ""),
        quality=flags,
        statement_text=f"{context.get('summary', '')} {context.get('body_summary', '')}",
        source_context_status=str(row.get("source_context_status") or ""),
    )
    if flags["statement_quality_gate"] == "pass":
        normalized_gate = "pass"
    elif rationale and not severe:
        normalized_gate = "manual_review_required"
    else:
        normalized_gate = "fail"
    return {
        "body_summary_hit_old_cap": flags["body_summary_hit_old_cap"],
        "body_summary_length": flags["body_summary_length"],
        "manual_review_rationale": rationale,
        "normalized_statement_quality_gate": normalized_gate,
        "raw_statement_quality_gate": flags["statement_quality_gate"],
        "risk_reasons": unique_sorted([str(reason) for reason in flags["risk_reasons"]] + severe),
        "severe_statement_quality_risks": severe,
        "statement_probably_truncated": flags["statement_probably_truncated"],
    }


def historical_paid_context_by_task(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    matrix = read_json(artifact_path(config, "task_outcome_matrix"))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cell in matrix.get("cells", []):
        if cell.get("task_id"):
            grouped[str(cell["task_id"])].append(cell)
    out: dict[str, dict[str, Any]] = {}
    for task_id, cells in grouped.items():
        scoreable = [cell for cell in cells if cell.get("scoreable_cell")]
        out[task_id] = {
            "historical_paid_cells_present": True,
            "planned_cell_count": len(cells),
            "policy_violation_count": sum(1 for cell in cells if cell.get("policy_violation") or cell.get("terminal_status") == "policy_violation"),
            "scoreable_cell_count": len(scoreable),
            "source_splits": unique_sorted([str(cell.get("split") or "") for cell in cells]),
            "terminal_status_counts": dict(sorted(Counter(str(cell.get("terminal_status") or "unknown") for cell in cells).items())),
            "used_for_selection": False,
        }
    return out


def candidate_record(
    *,
    repo_id: str,
    certified: dict[str, Any],
    context: dict[str, Any],
    historical_context: dict[str, Any] | None,
) -> dict[str, Any]:
    task_id = str(certified["task_id"])
    impl_files = implementation_files_for(certified)
    tests = test_files_for(certified)
    gate_summary = certification_gate_summary(certified)
    quality = statement_quality_record(context=context, row=certified, impl_files=impl_files, tests=tests)
    source_ref = str(context.get("ref") or (certified.get("allowed_context_refs") or [""])[0])
    source_status = str(certified.get("source_context_status") or "")
    public_excerpt = statement_quality.sanitize_public_body_summary(context.get("body_summary") or "", limit=360)
    record: dict[str, Any] = {
        "allowed_context_refs": [source_ref] if source_ref else [],
        "base_commit_present": bool(certified.get("base_commit")),
        "candidate_filter_status": certified.get("candidate_filter_status", ""),
        "certification_gate_summary": gate_summary,
        "change_size_bucket": change_size_bucket(certified),
        "changed_file_count": len(certified.get("changed_files", []) or []),
        "implementation_file_count": len(impl_files),
        "implementation_files": impl_files,
        "module_or_package": certified.get("module_or_package", []),
        "problem_context_manual_review_rationale": quality["manual_review_rationale"],
        "problem_summary": statement_quality.normalize_text(context.get("summary") or certified.get("subject") or ""),
        "repo_id": repo_id,
        "release_split_eligibility": split_eligibility(certified),
        "schema_version": "barcarolle.phase1.statement_hardened_candidate.v1",
        "selection_eligible_without_paid_outcome": False,
        "short_sanitized_public_excerpt": public_excerpt,
        "source_context_status": source_status,
        "source_kind": source_kind(source_ref),
        "source_ref": source_ref,
        "statement_quality_diagnostics": quality,
        "statement_quality_gate": quality["normalized_statement_quality_gate"],
        "statement_quality_risk_reasons": quality["risk_reasons"],
        "target_commit_present": bool(certified.get("target_commit")),
        "task_id": task_id,
        "task_time": certified.get("task_time"),
        "test_files": tests,
        "verifier_command_metadata": verifier_command_metadata(repo_id, tests),
    }
    record["preview_statement"] = statement_preview_text(record)
    record["statement_digest"] = digest_text(record["preview_statement"])
    record["historical_paid_context"] = historical_context or {
        "historical_paid_cells_present": False,
        "used_for_selection": False,
    }
    record["selection_eligible_without_paid_outcome"] = is_candidate_eligible(record)[0]
    return record


def load_repo_candidates(config: dict[str, Any], repo_id: str) -> list[dict[str, Any]]:
    certified = row_by_task(read_jsonl(artifact_path(config, f"{repo_id}_certified_tasks")))
    contexts = row_by_task(read_jsonl(artifact_path(config, f"{repo_id}_source_context")))
    paid_context = historical_paid_context_by_task(config)
    records = []
    for task_id in sorted(certified):
        row = certified[task_id]
        context = contexts.get(task_id) or row.get("sanitized_context") or {}
        records.append(
            candidate_record(
                repo_id=repo_id,
                certified=row,
                context=context,
                historical_context=paid_context.get(task_id),
            )
        )
    return records


def build_candidate_inventory(config: dict[str, Any]) -> dict[str, Any]:
    repos = [str(repo_id) for repo_id in config["selection"]["preferred_repos"]]
    candidates = [record for repo_id in repos for record in load_repo_candidates(config, repo_id)]
    by_repo = Counter(record["repo_id"] for record in candidates)
    by_repo_split: Counter[str] = Counter()
    by_repo_gate: Counter[str] = Counter()
    for record in candidates:
        by_repo_gate[f"{record['repo_id']}/{record['statement_quality_gate']}"] += 1
        for split in record["release_split_eligibility"]:
            by_repo_split[f"{record['repo_id']}/{split}"] += 1
    return {
        "candidates": candidates,
        "config": rel(config["_path"]),
        "generated_at": stable_generated_at(config),
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "predictive_validity_established": False,
        "schema_version": "barcarolle.phase1_statement_hardened_candidate_inventory.v1",
        "status": "computed",
        "summary": {
            "candidate_count": len(candidates),
            "eligible_without_paid_outcome_count": sum(1 for record in candidates if record["selection_eligible_without_paid_outcome"]),
            "historical_paid_context_task_count": sum(1 for record in candidates if record["historical_paid_context"]["historical_paid_cells_present"]),
            "repo_counts": dict(sorted(by_repo.items())),
            "repo_gate_counts": dict(sorted(by_repo_gate.items())),
            "repo_split_eligibility_counts": dict(sorted(by_repo_split.items())),
        },
    }


def is_candidate_eligible(record: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not record["certification_gate_summary"]["all_pass"]:
        reasons.extend(f"certification_gate_failed:{gate}" for gate in record["certification_gate_summary"]["failed_gates"])
    if record["source_context_status"] != "non_leaky_problem_context":
        reasons.append("public_source_context_required")
    if record["source_kind"] not in {"issue", "pull_request"}:
        reasons.append("public_issue_or_pr_context_required")
    if record["statement_quality_gate"] == "fail":
        reasons.extend(f"statement_quality_risk:{reason}" for reason in record["statement_quality_risk_reasons"])
    if record["statement_quality_gate"] == "manual_review_required" and not record["problem_context_manual_review_rationale"]:
        reasons.append("manual_review_rationale_required")
    if not record["implementation_files"]:
        reasons.append("editable_implementation_scope_empty")
    if any(statement_quality.is_test_path(path) for path in record["implementation_files"]):
        reasons.append("editable_scope_contains_tests")
    if any(path.endswith((".json", ".jsonl", ".yaml", ".yml")) for path in record["implementation_files"]):
        reasons.append("editable_scope_contains_generated_metadata")
    if record["source_kind"] == "pull_request" and not record["problem_context_manual_review_rationale"]:
        reasons.append("pr_context_requires_problem_rationale_or_linked_issue")
    return not reasons, unique_sorted(reasons)


def screen_candidate(record: dict[str, Any]) -> dict[str, Any]:
    eligible, reasons = is_candidate_eligible(record)
    return {
        "eligibility_reasons": reasons,
        "historical_paid_context_present": record["historical_paid_context"]["historical_paid_cells_present"],
        "paid_outcome_used_for_selection": False,
        "release_split_eligibility": record["release_split_eligibility"],
        "repo_id": record["repo_id"],
        "screen_status": "eligible" if eligible else "rejected",
        "statement_quality_gate": record["statement_quality_gate"],
        "task_id": record["task_id"],
        "task_time": record["task_time"],
    }


def sort_candidates_for_selection(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda row: (parse_task_time(str(row["task_time"])), str(row["task_id"])))


def select_release_candidates(
    eligible_records: list[dict[str, Any]],
    *,
    repos: list[str],
    splits: list[str],
    tasks_per_repo_split: int,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    selected: dict[str, list[str]] = {}
    missing: dict[str, list[str]] = {}
    by_id = {record["task_id"]: record for record in eligible_records}
    for repo_id in repos:
        repo_records = [record for record in eligible_records if record["repo_id"] == repo_id]
        used: set[str] = set()
        for split in splits:
            pool = [
                record
                for record in repo_records
                if split in record["release_split_eligibility"] and record["task_id"] not in used
            ]
            ordered = sort_candidates_for_selection(pool)
            choices = ordered[:tasks_per_repo_split] if split == "B_eval" else list(reversed(ordered))[:tasks_per_repo_split]
            choices = sorted(choices, key=lambda row: str(row["task_id"]))
            key = f"{repo_id}/{split}"
            selected[key] = [record["task_id"] for record in choices]
            used.update(selected[key])
            if len(selected[key]) < tasks_per_repo_split:
                missing[key] = [
                    f"needed {tasks_per_repo_split}, found {len(selected[key])} eligible tasks without using paid outcomes"
                ]
    # Keep static analyzers honest that selection uses only public/certification fields.
    for task_id in [task_id for task_ids in selected.values() for task_id in task_ids]:
        by_id[task_id]["historical_paid_context"]["used_for_selection"] = False
    return selected, missing


def build_candidate_screen(config: dict[str, Any], inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = inventory or build_candidate_inventory(config)
    screens = [screen_candidate(record) for record in inventory["candidates"]]
    eligible_ids = {row["task_id"] for row in screens if row["screen_status"] == "eligible"}
    eligible_records = [record for record in inventory["candidates"] if record["task_id"] in eligible_ids]
    repos = [str(repo_id) for repo_id in config["selection"]["preferred_repos"]]
    splits = [str(split) for split in config["selection"]["preferred_splits"]]
    tasks_per_repo_split = int(config["selection"]["tasks_per_repo_split"])
    selected, missing = select_release_candidates(
        eligible_records,
        repos=repos,
        splits=splits,
        tasks_per_repo_split=tasks_per_repo_split,
    )
    two_repo_feasible = not missing and len(repos) >= int(config["selection"]["minimum_repo_count"])
    attrs_keys = [f"attrs/{split}" for split in splits]
    attrs_only_feasible = all(len(selected.get(key, [])) >= tasks_per_repo_split for key in attrs_keys)
    reason_counts = Counter(reason for row in screens for reason in row["eligibility_reasons"])
    repo_split_counts = {
        f"{repo}/{split}": len(task_ids)
        for repo in repos
        for split in splits
        for task_ids in [selected.get(f"{repo}/{split}", [])]
    }
    return {
        "candidate_screens": screens,
        "config": rel(config["_path"]),
        "feasibility": {
            "attrs_only_statement_hardened_diagnostic_release": attrs_only_feasible,
            "missing_supply_by_repo_split": missing,
            "replacement_supply_needed": not two_repo_feasible,
            "two_repo_statement_hardened_release": two_repo_feasible,
        },
        "generated_at": stable_generated_at(config),
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "paid_outcome_used_for_selection": False,
        "predictive_validity_established": False,
        "schema_version": "barcarolle.phase1_statement_hardened_candidate_screen.v1",
        "selected_task_ids_by_repo_split": selected,
        "status": "computed",
        "summary": {
            "eligible_candidate_count": len(eligible_records),
            "preferred_two_repo_release_feasible": two_repo_feasible,
            "rejection_reason_counts": dict(sorted(reason_counts.items())),
            "selected_counts_by_repo_split": dict(sorted(repo_split_counts.items())),
            "total_candidate_count": len(screens),
        },
    }


def selected_ids_from_screen(screen: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for key in sorted(screen.get("selected_task_ids_by_repo_split", {})):
        ids.extend(str(task_id) for task_id in screen["selected_task_ids_by_repo_split"][key])
    return unique_sorted(ids)


def build_release_preview(
    config: dict[str, Any],
    inventory: dict[str, Any] | None = None,
    screen: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inventory = inventory or build_candidate_inventory(config)
    screen = screen or build_candidate_screen(config, inventory)
    selected = set(selected_ids_from_screen(screen))
    records = [record for record in inventory["candidates"] if record["task_id"] in selected]
    previews = []
    for record in sorted(records, key=lambda row: (row["repo_id"], row["task_id"])):
        previews.append(
            {
                "editable_implementation_scope": record["implementation_files"],
                "known_non_editable_test_paths": record["test_files"],
                "problem_summary": record["problem_summary"],
                "repo_id": record["repo_id"],
                "scoreable_result": False,
                "short_public_excerpt": record["short_sanitized_public_excerpt"],
                "source_ref": record["source_ref"],
                "statement_digest": record["statement_digest"],
                "statement_quality_diagnostics": record["statement_quality_diagnostics"],
                "task_id": record["task_id"],
                "verifier_command_metadata": record["verifier_command_metadata"],
                "visible_statement": record["preview_statement"],
            }
        )
    return {
        "config": rel(config["_path"]),
        "diagnostic_only": True,
        "generated_at": stable_generated_at(config),
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "paid_outcome_included": False,
        "predictive_validity_established": False,
        "previews": previews,
        "schema_version": "barcarolle.phase1_statement_hardened_release_preview.v1",
        "status": "computed",
        "summary": {
            "editable_scope_contains_tests": any(
                statement_quality.is_test_path(path)
                for preview in previews
                for path in preview["editable_implementation_scope"]
            ),
            "preview_count": len(previews),
            "scoreable_result_count": 0,
            "statements_cut_mid_code_or_sentence": sum(
                1
                for preview in previews
                if preview["statement_quality_diagnostics"]["statement_probably_truncated"]
            ),
        },
    }


def input_artifact_digests(config: dict[str, Any]) -> dict[str, str]:
    keys = [
        "attrs_h_future_evidence_status",
        "attrs_h_future_task_design_audit",
        "attrs_h_future_statement_sensitivity",
        "attrs_h_future_statement_preview",
        "task_outcome_matrix",
        "statement_quality_tool",
        "boltons_certified_tasks",
        "attrs_certified_tasks",
        "boltons_source_context",
        "attrs_source_context",
    ]
    return {rel(artifact_path(config, key)): digest_file(artifact_path(config, key)) for key in keys if artifact_path(config, key).exists()}


def build_release_manifest(
    config: dict[str, Any],
    inventory: dict[str, Any] | None = None,
    screen: dict[str, Any] | None = None,
    preview: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inventory = inventory or build_candidate_inventory(config)
    screen = screen or build_candidate_screen(config, inventory)
    preview = preview or build_release_preview(config, inventory, screen)
    if not screen["feasibility"]["two_repo_statement_hardened_release"]:
        raise ValueError("cannot freeze statement-hardened release because two-repo feasibility failed")
    selected_ids = set(selected_ids_from_screen(screen))
    selected_records = [record for record in inventory["candidates"] if record["task_id"] in selected_ids]
    adapters = [str(adapter) for adapter in config["selection"]["planned_adapters"]]
    return {
        "allowed_context_refs": {
            record["task_id"]: record["allowed_context_refs"]
            for record in sorted(selected_records, key=lambda row: row["task_id"])
        },
        "created_at": stable_generated_at(config),
        "editable_implementation_paths": {
            record["task_id"]: record["implementation_files"]
            for record in sorted(selected_records, key=lambda row: row["task_id"])
        },
        "historical_result_policy": {
            "old_paid_results_are_immutable_inputs": True,
            "old_results_are_not_corrected_or_repaired": True,
            "paid_outcomes_not_used_for_selection": True,
        },
        "input_artifact_digests": input_artifact_digests(config),
        "non_editable_test_paths": {
            record["task_id"]: record["test_files"]
            for record in sorted(selected_records, key=lambda row: row["task_id"])
        },
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "paid_validation_prefix_reserved": PAID_VALIDATION_PREFIX,
        "planned_adapters": adapters,
        "planned_cells": len(selected_records) * len(adapters),
        "predictive_validity_established": False,
        "release_id": RELEASE_ID,
        "schema_version": "barcarolle.phase1_statement_hardened_release_manifest.v1",
        "selected_repos": [str(repo) for repo in config["selection"]["preferred_repos"]],
        "selected_splits": [str(split) for split in config["selection"]["preferred_splits"]],
        "selected_task_ids": screen["selected_task_ids_by_repo_split"],
        "selection_rule": {
            "exclude_paid_outcome_from_selection": True,
            "repo_order": [str(repo) for repo in config["selection"]["preferred_repos"]],
            "split_order": [str(split) for split in config["selection"]["preferred_splits"]],
            "sort_key": ["task_time", "task_id"],
            "tasks_per_repo_split": int(config["selection"]["tasks_per_repo_split"]),
        },
        "statement_digests": {
            preview_row["task_id"]: f"sha256:{preview_row['statement_digest']}"
            for preview_row in preview["previews"]
        },
        "statement_quality_diagnostics": {
            record["task_id"]: record["statement_quality_diagnostics"]
            for record in sorted(selected_records, key=lambda row: row["task_id"])
        },
        "status": "frozen",
        "verifier_command_metadata": {
            record["task_id"]: record["verifier_command_metadata"]
            for record in sorted(selected_records, key=lambda row: row["task_id"])
        },
    }


def build_blocker(config: dict[str, Any], screen: dict[str, Any]) -> dict[str, Any]:
    return {
        "blocked_before_paid_validation": True,
        "generated_at": stable_generated_at(config),
        "missing_supply_by_repo_split": screen["feasibility"]["missing_supply_by_repo_split"],
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "predictive_validity_established": False,
        "recommendation": "Mine local replacement statement-hardened supply before any paid validation.",
        "schema_version": "barcarolle.phase1_statement_hardened_blocker.v1",
        "status": "replacement_supply_needed",
    }


def manifest_digest(manifest: dict[str, Any]) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return f"sha256:{digest_text(payload)}"


def build_preregistration(config: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "claims_allowed_after_future_paid_validation": [
            "statement_hardened_preflight_recorded",
            "statement_quality_gate_verified",
            "statement_hardened_release_frozen",
            "statement_hardened_preregistration_written",
            "paid_validation_gate_defined",
            "historical_paid_results_preserved",
        ],
        "claims_still_disallowed": [
            "predictive_validity_established",
            "production_benchmark_ranking",
            "attrs_h_future_paid_result_repaired",
            "old_two_repo_result_overwritten",
            "paid_validation_completed",
        ],
        "comparison_metrics": [
            "per_repo_split_pass_rate",
            "adapter_level_pass_rate",
            "absolute_gap_between_B_eval_and_H_future",
            "calibration_error_against_future_holdout",
        ],
        "cost_cap_proposal": {
            "requires_explicit_user_approval": True,
            "provider_cost_change_this_run_usd": 0,
            "future_runbook_must_set_cap_before_paid_calls": True,
        },
        "created_at": stable_generated_at(config),
        "decision_thresholds": {
            "minimum_scoreable_cells_for_claim": manifest["planned_cells"],
            "predictive_validity_claim_requires_future_paid_validation": True,
            "policy_violation_cells_non_scoreable": True,
        },
        "endpoint_rule": {
            "api_key_env": "LLM_API_KEY",
            "base_url_env": "LLM_BASE_URL",
            "no_provider_specific_fallback": True,
        },
        "historical_result_handling": "Old attrs H_future results are historical observations only. They are not corrected, repaired, rerun-equivalent, or merged into the new release score.",
        "manifest_digest": manifest_digest(manifest),
        "planned_adapters": manifest["planned_adapters"],
        "planned_paid_prefix": manifest["paid_validation_prefix_reserved"],
        "policy_violation_handling": "Policy violations are recorded as terminal status and excluded from scoreable pass-rate denominators.",
        "predictive_validity_established": False,
        "release_id": manifest["release_id"],
        "repos": manifest["selected_repos"],
        "research_question": "Does a statement-quality-gated two-repo Barcarolle release better support future target-repo predictive validation than the previous statement-risk-confounded attrs H_future pilot?",
        "schema_version": "barcarolle.phase1_statement_hardened_preregistration.v1",
        "scoreability_rules": {
            "hidden_verifier_only_in_verifier_workspace": True,
            "new_paid_validation_prefix_required": True,
            "old_paid_cells_not_merged": True,
            "tests_are_non_editable": True,
        },
        "splits": manifest["selected_splits"],
        "status": "written",
        "stop_conditions": [
            "missing LLM_BASE_URL or LLM_API_KEY in future paid worker shell",
            "any need to inspect hidden verifier material while editing statements",
            "any need to modify ACUT internals",
            "any attempt to rewrite historical score tables",
        ],
        "uncertainty_metrics": [
            "bootstrap_confidence_interval_by_task",
            "adapter_disagreement_rate",
            "policy_violation_rate",
        ],
    }


def build_validation_decision(config: dict[str, Any], manifest_exists: bool) -> dict[str, Any]:
    decision = (
        "ready_for_user_approved_paid_validation"
        if manifest_exists
        else "replacement_supply_needed_before_paid_validation"
    )
    next_runbook = (
        "docs/experiments/phase-1-statement-hardened-paid-validation-runbook.md"
        if manifest_exists
        else "docs/experiments/phase-1-statement-hardened-replacement-supply-runbook.md"
    )
    return {
        "generated_at": stable_generated_at(config),
        "next_runbook_path": next_runbook,
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "paid_validation_blocked_until_user_approval": True,
        "predictive_validity_established": False,
        "primary_decision": decision,
        "release_frozen": manifest_exists,
        "schema_version": "barcarolle.phase1_statement_hardened_validation_decision.v1",
        "status": "decided",
    }


def render_inventory_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Statement-Hardened Candidate Inventory",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "## Summary",
        "",
        f"- Candidates: `{payload['summary']['candidate_count']}`.",
        f"- Eligible without paid outcome: `{payload['summary']['eligible_without_paid_outcome_count']}`.",
        f"- Historical paid context present: `{payload['summary']['historical_paid_context_task_count']}`.",
        f"- Repo counts: `{payload['summary']['repo_counts']}`.",
        f"- Gate counts: `{payload['summary']['repo_gate_counts']}`.",
        "",
        "Historical paid outcomes are context only and are not used for eligibility.",
    ]
    return "\n".join(lines)


def render_screen_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Statement-Hardened Candidate Screen",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "## Feasibility",
        "",
        f"- Preferred two-repo release feasible: `{payload['feasibility']['two_repo_statement_hardened_release']}`.",
        f"- Attrs-only diagnostic release feasible: `{payload['feasibility']['attrs_only_statement_hardened_diagnostic_release']}`.",
        f"- Replacement supply needed: `{payload['feasibility']['replacement_supply_needed']}`.",
        f"- Missing supply: `{payload['feasibility']['missing_supply_by_repo_split']}`.",
        "",
        "## Selection Boundary",
        "",
        "- Paid outcome used for selection: `false`.",
        "- Paid validation is not recommended unless a frozen release manifest exists.",
        "",
        "## Counts",
        "",
        f"- Selected counts by repo/split: `{payload['summary']['selected_counts_by_repo_split']}`.",
        f"- Rejection reason counts: `{payload['summary']['rejection_reason_counts']}`.",
    ]
    return "\n".join(lines)


def render_preview_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Statement-Hardened Release Preview",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "These previews are solver-visible statement candidates only. They are not scoreable results.",
        "",
        "## Summary",
        "",
        f"- Preview count: `{payload['summary']['preview_count']}`.",
        f"- Scoreable result count: `{payload['summary']['scoreable_result_count']}`.",
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
                f"- Repo: `{row['repo_id']}`.",
                f"- Source ref: `{row['source_ref']}`.",
                f"- Problem summary: {row['problem_summary']}",
                f"- Short public excerpt: {row['short_public_excerpt']}",
                f"- Editable implementation scope: `{row['editable_implementation_scope']}`.",
                f"- Known non-editable test paths: `{row['known_non_editable_test_paths']}`.",
                f"- Statement digest: `{row['statement_digest']}`.",
                "",
            ]
        )
    return "\n".join(lines)


def render_preregistration_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Statement-Hardened Preregistration",
        "",
        f"Release: `{payload['release_id']}`.",
        f"Created: `{payload['created_at']}`.",
        "",
        "## Research Question",
        "",
        payload["research_question"],
        "",
        "## Paid Validation Gate",
        "",
        "- This preregistration does not authorize paid calls.",
        "- Future paid validation must use `LLM_BASE_URL` and `LLM_API_KEY` only.",
        f"- Future paid prefix: `{payload['planned_paid_prefix']}`.",
        "",
        "## Historical Result Handling",
        "",
        payload["historical_result_handling"],
        "",
        "## Claims Still Disallowed",
        "",
    ]
    lines.extend(f"- `{claim}`" for claim in payload["claims_still_disallowed"])
    return "\n".join(lines)


def render_decision_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Statement-Hardened Validation Decision",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Primary decision: `{payload['primary_decision']}`.",
            f"- Release frozen: `{payload['release_frozen']}`.",
            f"- Paid validation blocked until user approval: `{payload['paid_validation_blocked_until_user_approval']}`.",
            f"- Next runbook: `{payload['next_runbook_path']}`.",
            "- Predictive validity established: `false`.",
        ]
    )


def render_blocker_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Statement-Hardened Release Blocker",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Status: `{payload['status']}`.",
            f"- Missing supply: `{payload['missing_supply_by_repo_split']}`.",
            f"- Recommendation: {payload['recommendation']}",
            "- Predictive validity established: `false`.",
        ]
    )


def render_paid_validation_runbook(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Statement-Hardened Paid Validation Runbook",
            "",
            "Status: draft only, not executed.",
            "",
            "This runbook may be executed only after explicit user approval for paid validation.",
            "",
            "## Required Inputs",
            "",
            "- `experiments/phase1_compiler/results/phase1_statement_hardened_release_manifest.json`",
            "- `experiments/phase1_compiler/results/phase1_statement_hardened_preregistration.json`",
            "",
            "## Endpoint Rule",
            "",
            "Paid ACUT calls must use `LLM_BASE_URL` and `LLM_API_KEY`. Do not fall back to provider-specific variables or local subscription auth.",
            "",
            "## Prefix",
            "",
            f"Use a new result prefix derived from `{PAID_VALIDATION_PREFIX}`. Do not write into old `phase1_two_repo_future_holdout_*` prefixes.",
            "",
            "## Stop Conditions",
            "",
            "- Stop if endpoint variables are missing after sourcing `~/.zshrc`.",
            "- Stop if hidden verifier material would be needed to edit statements.",
            "- Stop if ACUT internals would need modification.",
            "- Stop if historical score tables would need rewriting.",
            "",
            "## Decision Link",
            "",
            f"Primary preregistration decision: `{decision['primary_decision']}`.",
        ]
    )


def render_replacement_supply_runbook(blocker: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Statement-Hardened Replacement Supply Runbook",
            "",
            "Status: draft only, local mining before paid validation.",
            "",
            "Mine additional public-context, statement-quality-gated replacement tasks for the missing repo/split supply before any paid ACUT run.",
            "",
            "## Missing Supply",
            "",
            f"`{blocker['missing_supply_by_repo_split']}`",
            "",
            "## Boundary",
            "",
            "Do not use paid outcomes, hidden verifier material, raw ACUT transcripts, or target diffs to choose or rewrite statements.",
        ]
    )


def write_inventory(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_candidate_inventory(config)
    write_json(output_path(config, "candidate_inventory"), payload)
    write_text(output_path(config, "candidate_inventory_report"), render_inventory_markdown(payload))
    return payload


def write_screen(config: dict[str, Any]) -> dict[str, Any]:
    inventory = build_candidate_inventory(config)
    payload = build_candidate_screen(config, inventory)
    write_json(output_path(config, "candidate_screen"), payload)
    write_text(output_path(config, "candidate_screen_report"), render_screen_markdown(payload))
    return payload


def write_preview(config: dict[str, Any]) -> dict[str, Any]:
    inventory = build_candidate_inventory(config)
    screen = build_candidate_screen(config, inventory)
    payload = build_release_preview(config, inventory, screen)
    write_json(output_path(config, "release_preview"), payload)
    write_text(output_path(config, "release_preview_report"), render_preview_markdown(payload))
    return payload


def write_manifest_or_blocker(config: dict[str, Any]) -> dict[str, Any]:
    inventory = build_candidate_inventory(config)
    screen = build_candidate_screen(config, inventory)
    if screen["feasibility"]["two_repo_statement_hardened_release"]:
        preview = build_release_preview(config, inventory, screen)
        manifest = build_release_manifest(config, inventory, screen, preview)
        write_json(output_path(config, "release_manifest"), manifest)
        return manifest
    blocker = build_blocker(config, screen)
    write_json(output_path(config, "blocker"), blocker)
    write_text(output_path(config, "blocker_report"), render_blocker_markdown(blocker))
    write_text(REPO_ROOT / "docs" / "experiments" / "phase-1-statement-hardened-replacement-supply-runbook.md", render_replacement_supply_runbook(blocker))
    return blocker


def write_preregistration(config: dict[str, Any]) -> dict[str, Any]:
    manifest_path = output_path(config, "release_manifest")
    if not manifest_path.exists():
        report = "# Phase 1 Statement-Hardened Preregistration\n\nNo preregistration was written because no release manifest was frozen.\n"
        write_text(output_path(config, "preregistration_report"), report)
        payload = {
            "created_at": stable_generated_at(config),
            "manifest_frozen": False,
            "paid_acut_calls_made": False,
            "paid_llm_calls_made": False,
            "predictive_validity_established": False,
            "schema_version": "barcarolle.phase1_statement_hardened_preregistration.v1",
            "status": "not_written_no_manifest",
        }
        write_json(output_path(config, "preregistration"), payload)
        return payload
    manifest = read_json(manifest_path)
    payload = build_preregistration(config, manifest)
    write_json(output_path(config, "preregistration"), payload)
    write_text(output_path(config, "preregistration_report"), render_preregistration_markdown(payload))
    return payload


def write_decision(config: dict[str, Any]) -> dict[str, Any]:
    manifest_exists = output_path(config, "release_manifest").exists()
    payload = build_validation_decision(config, manifest_exists)
    write_json(output_path(config, "validation_decision"), payload)
    write_text(output_path(config, "validation_decision_report"), render_decision_markdown(payload))
    if manifest_exists:
        write_text(REPO_ROOT / "docs" / "experiments" / "phase-1-statement-hardened-paid-validation-runbook.md", render_paid_validation_runbook(payload))
    else:
        blocker = read_json(output_path(config, "blocker")) if output_path(config, "blocker").exists() else {"missing_supply_by_repo_split": {}}
        write_text(REPO_ROOT / "docs" / "experiments" / "phase-1-statement-hardened-replacement-supply-runbook.md", render_replacement_supply_runbook(blocker))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Phase 1 statement-hardened preregistration artifacts.")
    parser.add_argument("mode", choices=["inventory", "screen", "preview", "freeze", "preregister", "decide", "all"])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    if args.mode in {"inventory", "all"}:
        write_inventory(config)
    if args.mode in {"screen", "all"}:
        write_screen(config)
    if args.mode in {"preview", "all"}:
        write_preview(config)
    if args.mode in {"freeze", "all"}:
        write_manifest_or_blocker(config)
    if args.mode in {"preregister", "all"}:
        write_preregistration(config)
    if args.mode in {"decide", "all"}:
        write_decision(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
