from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_TOOLS = REPO_ROOT / "experiments" / "phase0_headroom" / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))

import statement_quality  # noqa: E402


DEFAULT_CONFIG = ROOT / "configs" / "phase1_statement_hardened_after_canonical_repair_preregistration.yaml"
SCHEMA_VERSION = "barcarolle.phase1_statement_hardened_after_canonical_repair_preregistration.v1"
RELEASE_MANIFEST_SCHEMA = "barcarolle.phase1.statement_hardened_after_canonical_repair_release_manifest.v1"
PREREGISTRATION_SCHEMA = "barcarolle.phase1.statement_hardened_after_canonical_repair_preregistration.v1"
EXPECTED_CANONICAL_GROUPS: dict[str, list[str]] = {
    "attrs/B_eval": [
        "attrs__hist__001",
        "attrs__hist__003",
        "attrs__hist__004",
        "attrs__hist__008",
    ],
    "attrs/H_future": [
        "attrs__hist__012",
        "attrs__hist__013",
        "attrs__hist__023",
        "attrs__hist__027",
    ],
    "boltons/B_eval": [
        "boltons__clean_ext__001",
        "boltons__clean_ext__008",
        "boltons__clean_ext__010",
        "boltons__hist__011",
    ],
    "boltons/H_future": [
        "boltons__clean_ext__017",
        "boltons__hist__022",
        "boltons__hist__023",
        "boltons__hist__027",
    ],
}
EXPECTED_TASK_COUNT = 16
FORBIDDEN_STATEMENT_PATTERNS: dict[str, str] = {
    "diff --git": "raw_diff_marker",
    "\n@@": "raw_diff_hunk_marker",
    "gold patch": "gold_patch_text",
    "hidden verifier": "hidden_verifier_text",
    "verified_pass": "paid_outcome_status_text",
    "verified_fail": "paid_outcome_status_text",
    "policy_violation": "policy_status_text",
}
RAW_TEST_ASSERTION_RE = re.compile(r"\bassert\s+")
TARGET_COMMIT_RE = re.compile(r"\b[0-9a-f]{40}\b")


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


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def statement_digest(statement: str) -> str:
    return f"sha256:{digest_text(statement)}"


def digest_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def config_path(raw: str | Path) -> Path:
    path = Path(str(raw))
    return path if path.is_absolute() else REPO_ROOT / path


def rel(path: Path | str) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected after-canonical-repair preregistration config schema_version")
    config["_path"] = str(path)
    return config


def artifact_path(config: dict[str, Any], key: str) -> Path:
    return config_path(str(config["source_artifacts"][key]))


def output_path(config: dict[str, Any], key: str) -> Path:
    return config_path(str(config["output_paths"][key]))


def generated_at(config: dict[str, Any]) -> str:
    preflight = output_path(config, "preflight")
    if preflight.exists():
        return str(read_json(preflight).get("generated_at") or config.get("created_at") or "")
    return str(config.get("created_at") or "")


def row_by_task(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["task_id"]): row for row in rows if row.get("task_id")}


def unique_sorted(values: list[str]) -> list[str]:
    return sorted(dict.fromkeys(str(value) for value in values if str(value)))


def expected_task_ids() -> list[str]:
    task_ids: list[str] = []
    for repo_split in sorted(EXPECTED_CANONICAL_GROUPS):
        task_ids.extend(EXPECTED_CANONICAL_GROUPS[repo_split])
    return task_ids


def validate_canonical_split_map(split_map: dict[str, Any]) -> list[dict[str, str]]:
    task_to_split = split_map.get("task_to_split") or {}
    actual_task_ids = set(str(task_id) for task_id in task_to_split)
    expected_ids = set(expected_task_ids())
    missing = sorted(expected_ids - actual_task_ids)
    extra = sorted(actual_task_ids - expected_ids)
    if missing or extra:
        raise ValueError(f"canonical split map task mismatch: missing={missing}, extra={extra}")
    if len(actual_task_ids) != EXPECTED_TASK_COUNT:
        raise ValueError(f"canonical split map must contain {EXPECTED_TASK_COUNT} tasks")

    rows: list[dict[str, str]] = []
    actual_groups: dict[str, list[str]] = defaultdict(list)
    for task_id, split_row in sorted(task_to_split.items()):
        repo_id = str(split_row.get("repo_id") or task_id.split("__", 1)[0])
        canonical_split = str(split_row.get("canonical_split") or "")
        repo_split = str(split_row.get("repo_split") or f"{repo_id}/{canonical_split}")
        actual_groups[repo_split].append(str(task_id))
        rows.append(
            {
                "canonical_repo_split": repo_split,
                "canonical_split": canonical_split,
                "repo_id": repo_id,
                "task_id": str(task_id),
            }
        )

    normalized = {key: sorted(values) for key, values in actual_groups.items()}
    expected = {key: sorted(values) for key, values in EXPECTED_CANONICAL_GROUPS.items()}
    if normalized != expected:
        raise ValueError(f"canonical split labels mismatch: expected={expected}, actual={normalized}")
    if normalized["boltons/H_future"].count("boltons__clean_ext__017") != 1:
        raise ValueError("boltons__clean_ext__017 must be canonical boltons/H_future")
    return rows


def merge_statement_rows(
    diff_assisted_rows: list[dict[str, Any]],
    canonical_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for source_name, rows in (
        ("diff_assisted_codex_loop", diff_assisted_rows),
        ("canonical_regenerated", canonical_rows),
    ):
        for row in rows:
            task_id = str(row.get("task_id") or "")
            statement = str(row.get("statement") or "")
            provided_digest = str(row.get("statement_digest") or "")
            if not task_id:
                continue
            calculated = statement_digest(statement)
            if provided_digest != calculated:
                raise ValueError(f"statement digest mismatch for {task_id}: {provided_digest} != {calculated}")
            merged[task_id] = {
                **row,
                "statement": statement,
                "statement_digest": calculated,
                "statement_source": source_name,
            }
    return merged


def merge_review_rows(
    diff_assisted_reviews: list[dict[str, Any]],
    canonical_reviews: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for source_name, rows in (
        ("diff_assisted_codex_loop_review", diff_assisted_reviews),
        ("canonical_review", canonical_reviews),
    ):
        for row in rows:
            task_id = str(row.get("task_id") or "")
            if task_id:
                merged[task_id] = {**row, "review_source": source_name}
    return merged


def current_inventory_split_by_task(current_inventory: dict[str, Any] | None) -> dict[str, str]:
    if not current_inventory:
        return {}
    out: dict[str, str] = {}
    for row in current_inventory.get("candidates", []):
        task_id = str(row.get("task_id") or "")
        eligibilities = [str(value) for value in row.get("release_split_eligibility", [])]
        if task_id and len(eligibilities) == 1:
            out[task_id] = eligibilities[0]
    return out


def allowed_refs_from_inventory(row: dict[str, Any]) -> list[str]:
    refs = [str(value) for value in row.get("source_ref_metadata", [])]
    if row.get("source_ref"):
        refs.append(str(row["source_ref"]))
    return unique_sorted(refs)


def forbidden_statement_reasons(statement: str) -> list[str]:
    lowered = statement.lower()
    reasons = [reason for needle, reason in FORBIDDEN_STATEMENT_PATTERNS.items() if needle in lowered]
    if TARGET_COMMIT_RE.search(statement):
        reasons.append("target_commit_hash")
    if RAW_TEST_ASSERTION_RE.search(statement):
        reasons.append("raw_test_assertion")
    return unique_sorted(reasons)


def scope_reasons(implementation_files: list[str], test_files: list[str]) -> list[str]:
    reasons: list[str] = []
    if not implementation_files:
        reasons.append("missing_editable_implementation_paths")
    if not test_files:
        reasons.append("missing_non_editable_test_paths")
    if any(statement_quality.is_test_path(path) for path in implementation_files):
        reasons.append("editable_scope_contains_test_path")
    if set(implementation_files) & set(test_files):
        reasons.append("editable_scope_overlaps_non_editable_tests")
    return unique_sorted(reasons)


def build_inventory_rows(
    *,
    split_map: dict[str, Any],
    canonical_inventory: dict[str, Any],
    canonical_screen: dict[str, Any],
    statement_rows: dict[str, dict[str, Any]],
    review_rows: dict[str, dict[str, Any]],
    qa_rows: dict[str, dict[str, Any]],
    current_inventory: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    split_rows = validate_canonical_split_map(split_map)
    inventory_by_task = row_by_task(canonical_inventory.get("rows", []))
    screen_by_task = row_by_task(canonical_screen.get("candidate_screens", []))
    current_split_by_task = current_inventory_split_by_task(current_inventory)

    rows: list[dict[str, Any]] = []
    for split_row in split_rows:
        task_id = split_row["task_id"]
        inventory = inventory_by_task.get(task_id)
        statement = statement_rows.get(task_id)
        review = review_rows.get(task_id)
        qa = qa_rows.get(task_id)
        screen = screen_by_task.get(task_id)
        if not inventory:
            raise ValueError(f"missing canonical inventory row for {task_id}")
        if not statement:
            raise ValueError(f"missing full statement text for {task_id}")
        if not review:
            raise ValueError(f"missing review row for {task_id}")
        if not qa:
            raise ValueError(f"missing deterministic QA row for {task_id}")
        if not screen:
            raise ValueError(f"missing canonical screen row for {task_id}")

        statement_text = str(statement["statement"])
        digest = statement_digest(statement_text)
        digest_sources = {
            "generated_statement": str(statement.get("statement_digest") or ""),
            "review": str(review.get("statement_digest") or ""),
            "qa": str(qa.get("statement_digest") or ""),
            "canonical_screen": str(screen.get("statement_digest") or ""),
        }
        digest_mismatches = sorted(key for key, value in digest_sources.items() if value and value != digest)
        implementation_files = [str(path) for path in inventory.get("implementation_files", [])]
        test_files = [str(path) for path in inventory.get("test_files", [])]
        rows.append(
            {
                "allowed_public_context_refs": allowed_refs_from_inventory(inventory),
                "canonical_repo_split": split_row["canonical_repo_split"],
                "canonical_screen_eligible": bool(screen.get("eligible_under_canonical_split_repair")),
                "canonical_split": split_row["canonical_split"],
                "current_inventory_split": current_split_by_task.get(task_id, ""),
                "current_inventory_split_used_for_selection": False,
                "deterministic_qa_status": str(qa.get("status") or ""),
                "digest_mismatch_sources": digest_mismatches,
                "editable_implementation_paths": implementation_files,
                "forbidden_statement_reasons": forbidden_statement_reasons(statement_text),
                "full_visible_statement": statement_text,
                "historical_pass_fail_outcomes_used_for_selection": False,
                "implementation_scope_reasons": scope_reasons(implementation_files, test_files),
                "non_editable_test_paths": test_files,
                "repo_id": split_row["repo_id"],
                "review_status": str(review.get("status") or screen.get("review_status") or ""),
                "source_ref": str(inventory.get("source_ref") or ""),
                "statement_contains_paid_outcome_flag": bool(statement.get("contains_paid_outcome")),
                "statement_contains_raw_diff_flag": bool(statement.get("contains_raw_diff")),
                "statement_digest": digest,
                "statement_digest_matches_text": not digest_mismatches,
                "statement_generation_notes": str(statement.get("generation_notes") or ""),
                "statement_source": str(screen.get("statement_source") or statement.get("statement_source") or ""),
                "task_id": task_id,
                "task_time": str(inventory.get("task_time") or ""),
                "verifier_command_metadata": str(inventory.get("verifier_command_metadata") or ""),
            }
        )
    return sorted(rows, key=lambda row: (row["repo_id"], row["canonical_split"], row["task_id"]))


def build_inventory_payload(config: dict[str, Any]) -> dict[str, Any]:
    statement_rows = merge_statement_rows(
        read_jsonl(artifact_path(config, "diff_assisted_codex_loop_generated_statements")),
        read_jsonl(artifact_path(config, "canonical_regenerated_statements")),
    )
    diff_reviews = read_json(artifact_path(config, "diff_assisted_codex_loop_statement_reviews")).get("reviews", [])
    canonical_reviews = read_json(artifact_path(config, "canonical_statement_reviews")).get("reviews", [])
    review_rows = merge_review_rows(diff_reviews, canonical_reviews)
    qa_rows = row_by_task(read_json(artifact_path(config, "canonical_statement_qa")).get("rows", []))
    current_inventory_path = artifact_path(config, "current_statement_hardened_inventory")
    current_inventory = read_json(current_inventory_path) if current_inventory_path.exists() else None
    rows = build_inventory_rows(
        split_map=read_json(artifact_path(config, "canonical_split_map")),
        canonical_inventory=read_json(artifact_path(config, "canonical_selected_inventory")),
        canonical_screen=read_json(artifact_path(config, "canonical_statement_screen")),
        statement_rows=statement_rows,
        review_rows=review_rows,
        qa_rows=qa_rows,
        current_inventory=current_inventory,
    )
    counts = Counter(row["canonical_repo_split"] for row in rows)
    return {
        "config": rel(config["_path"]),
        "generated_at": generated_at(config),
        "historical_pass_fail_outcomes_used_for_selection": False,
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "rows": rows,
        "schema_version": "barcarolle.phase1.statement_hardened_after_canonical_repair_inventory.v1",
        "summary": {
            "canonical_task_count": len(rows),
            "current_inventory_split_used_for_selection": False,
            "repo_split_counts": dict(sorted(counts.items())),
            "statement_source_counts": dict(sorted(Counter(row["statement_source"] for row in rows).items())),
        },
    }


def screen_inventory_record(record: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if record.get("review_status") != "pass":
        reasons.append("review_status_not_pass")
    if record.get("deterministic_qa_status") != "pass":
        reasons.append("deterministic_qa_status_not_pass")
    if not record.get("canonical_screen_eligible"):
        reasons.append("canonical_screen_not_eligible")
    if not record.get("statement_digest_matches_text"):
        reasons.append("statement_digest_mismatch")
    if record.get("statement_contains_raw_diff_flag"):
        reasons.append("statement_row_contains_raw_diff_flag")
    if record.get("statement_contains_paid_outcome_flag"):
        reasons.append("statement_row_contains_paid_outcome_flag")
    reasons.extend(str(reason) for reason in record.get("forbidden_statement_reasons", []))
    reasons.extend(str(reason) for reason in record.get("implementation_scope_reasons", []))
    reasons = unique_sorted(reasons)
    return {
        "canonical_repo_split": record["canonical_repo_split"],
        "canonical_split": record["canonical_split"],
        "current_inventory_split": record.get("current_inventory_split", ""),
        "current_inventory_split_used_for_selection": False,
        "deterministic_qa_status": record["deterministic_qa_status"],
        "eligible_under_canonical_split_repair": not reasons,
        "historical_pass_fail_outcomes_used_for_selection": False,
        "rejection_reasons": reasons,
        "repo_id": record["repo_id"],
        "review_status": record["review_status"],
        "statement_digest": record["statement_digest"],
        "statement_source": record["statement_source"],
        "task_id": record["task_id"],
        "task_time": record["task_time"],
    }


def build_screen_payload(config: dict[str, Any], inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = inventory or build_inventory_payload(config)
    screens = [screen_inventory_record(record) for record in inventory["rows"]]
    selected: dict[str, list[str]] = {key: [] for key in sorted(EXPECTED_CANONICAL_GROUPS)}
    for row in screens:
        if row["eligible_under_canonical_split_repair"]:
            selected[row["canonical_repo_split"]].append(row["task_id"])
    selected = {key: sorted(values) for key, values in selected.items()}
    missing = {
        key: sorted(set(EXPECTED_CANONICAL_GROUPS[key]) - set(selected.get(key, [])))
        for key in sorted(EXPECTED_CANONICAL_GROUPS)
        if sorted(set(EXPECTED_CANONICAL_GROUPS[key]) - set(selected.get(key, [])))
    }
    selected_counts = {key: len(values) for key, values in selected.items()}
    return {
        "candidate_count": len(screens),
        "canonical_statement_inputs_verified": not missing and all(row["eligible_under_canonical_split_repair"] for row in screens),
        "canonical_task_count": EXPECTED_TASK_COUNT,
        "candidate_screens": screens,
        "current_inventory_split_used_for_selection": False,
        "deterministic_qa_counts": dict(sorted(Counter(row["deterministic_qa_status"] for row in screens).items())),
        "generated_at": generated_at(config),
        "historical_pass_fail_outcomes_used_for_selection": False,
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "paid_outcome_used_for_selection": False,
        "predictive_validity_established": False,
        "remaining_missing_supply": missing,
        "review_counts": dict(sorted(Counter(row["review_status"] for row in screens).items())),
        "schema_version": "barcarolle.phase1.statement_hardened_after_canonical_repair_screen.v1",
        "selected_counts_by_repo_split": selected_counts,
        "selected_task_ids_by_repo_split": selected,
    }


def selected_records(inventory: dict[str, Any], screen: dict[str, Any]) -> list[dict[str, Any]]:
    selected_ids = {
        task_id
        for values in screen["selected_task_ids_by_repo_split"].values()
        for task_id in values
    }
    return [row for row in inventory["rows"] if row["task_id"] in selected_ids]


def input_artifact_digests(config: dict[str, Any]) -> dict[str, str]:
    digests = {
        rel(Path(config["_path"])): digest_file(config_path(config["_path"])),
        rel(Path(__file__)): digest_file(Path(__file__)),
    }
    for key, raw in sorted(config.get("source_artifacts", {}).items()):
        path = config_path(str(raw))
        if path.exists():
            digests[rel(path)] = digest_file(path)
    return digests


def build_release_preview_payload(
    config: dict[str, Any],
    inventory: dict[str, Any] | None = None,
    screen: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inventory = inventory or build_inventory_payload(config)
    screen = screen or build_screen_payload(config, inventory)
    if screen["remaining_missing_supply"]:
        raise ValueError("cannot write release preview while canonical statement inputs are missing")
    rows = []
    for record in selected_records(inventory, screen):
        rows.append(
            {
                "allowed_public_context_refs": record["allowed_public_context_refs"],
                "canonical_repo_split": record["canonical_repo_split"],
                "editable_implementation_paths": record["editable_implementation_paths"],
                "generated_statement_is_scoreable_result": False,
                "non_editable_test_paths": record["non_editable_test_paths"],
                "repo_id": record["repo_id"],
                "source_ref": record["source_ref"],
                "statement_digest": record["statement_digest"],
                "statement_source": record["statement_source"],
                "task_id": record["task_id"],
                "visible_statement": record["full_visible_statement"],
            }
        )
    return {
        "generated_at": generated_at(config),
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "predictive_validity_established": False,
        "previews": sorted(rows, key=lambda row: (row["repo_id"], row["canonical_repo_split"], row["task_id"])),
        "schema_version": "barcarolle.phase1.statement_hardened_after_canonical_repair_release_preview.v1",
        "status": "computed",
        "summary": {
            "generated_statements_are_solver_visible_task_statements": True,
            "preview_count": len(rows),
            "scoreable_result_count": 0,
        },
    }


def planned_adapters(config: dict[str, Any]) -> list[str]:
    return [str(adapter) for adapter in config["selection"]["planned_adapters"]]


def build_release_manifest_payload(
    config: dict[str, Any],
    inventory: dict[str, Any] | None = None,
    screen: dict[str, Any] | None = None,
    preview: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inventory = inventory or build_inventory_payload(config)
    screen = screen or build_screen_payload(config, inventory)
    preview = preview or build_release_preview_payload(config, inventory, screen)
    if not screen["canonical_statement_inputs_verified"]:
        raise ValueError("cannot freeze manifest until canonical statement inputs are verified")
    records = sorted(selected_records(inventory, screen), key=lambda row: row["task_id"])
    adapters = planned_adapters(config)
    return {
        "allowed_public_context_refs": {row["task_id"]: row["allowed_public_context_refs"] for row in records},
        "canonical_selected_task_ids_by_repo_split": screen["selected_task_ids_by_repo_split"],
        "created_at": generated_at(config),
        "editable_implementation_paths": {row["task_id"]: row["editable_implementation_paths"] for row in records},
        "historical_result_policy": {
            "old_two_repo_paid_results_preserved_as_historical_observations": True,
            "old_paid_results_are_not_corrected_or_repaired": True,
            "old_paid_results_not_merged_into_new_release_score": True,
            "paid_outcomes_used_for_selection": False,
        },
        "input_artifact_digests": input_artifact_digests(config),
        "non_editable_test_paths": {row["task_id"]: row["non_editable_test_paths"] for row in records},
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "paid_validation_prefix_reserved": str(config["paid_validation_prefix_reserved"]),
        "paid_validation_prefix_reserved_for_future_run_only": True,
        "planned_adapters": adapters,
        "planned_cells": len(records) * len(adapters),
        "planned_cells_policy": {
            "derived_from_selected_task_count_times_planned_adapters": True,
            "selected_task_count": len(records),
        },
        "predictive_validity_established": False,
        "release_id": str(config["release_id"]),
        "schema_version": RELEASE_MANIFEST_SCHEMA,
        "scoreability_policy": {
            "generated_statement_is_scoreable_result": False,
            "hidden_oracle_material_only_in_verifier_workspace": True,
            "scoreable_acut_runs_must_use_workspace_adapter": True,
            "tests_are_non_editable": True,
        },
        "statement_digests": {row["task_id"]: row["statement_digest"] for row in records},
        "status": "frozen",
    }


def manifest_digest(manifest: dict[str, Any]) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return f"sha256:{digest_text(payload)}"


def build_preregistration_payload(config: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "canonical_split_policy": {
            "canonical_split_labels_source": "phase1_canonical_split_map and phase1_canonical_statement_screen",
            "current_inventory_split_used_for_selection": False,
            "historical_pass_fail_outcomes_used_for_selection": False,
        },
        "claims_allowed": [
            "canonical_statement_hardened_preflight_recorded",
            "canonical_statement_inputs_verified",
            "statement_hardened_release_manifest_frozen",
            "statement_hardened_preregistration_written",
            "paid_validation_gate_defined",
            "historical_paid_results_preserved",
            "future_paid_validation_requires_user_approval",
        ],
        "claims_disallowed": [
            "predictive_validity_established",
            "production_benchmark_ranking",
            "paid_validation_completed",
            "old_paid_result_repaired",
            "attrs_policy_violation_repaired",
            "generated_statement_is_scoreable_result",
            "hidden_oracle_informed_statement_rewrite",
            "next_runbook_written_by_worker",
        ],
        "cost_cap_placeholder": {
            "future_runbook_must_set_cap_before_paid_calls": True,
            "provider_cost_change_this_run_usd": 0,
            "requires_explicit_user_approval": True,
        },
        "created_at": generated_at(config),
        "endpoint_rule_for_future_paid_validation": {
            "api_key_env": "LLM_API_KEY",
            "base_url_env": "LLM_BASE_URL",
            "no_openai_api_key_fallback": True,
            "no_provider_specific_fallback": True,
        },
        "explicit_non_claims": {
            "attrs__hist__027_old_policy_violation_repaired_by_this_preregistration": False,
            "future_paid_validation_requires_explicit_user_approval_and_separate_runbook": True,
            "old_paid_results_repaired_or_overwritten": False,
            "paid_validation_has_not_started": True,
            "predictive_validity_has_not_been_established": True,
        },
        "historical_result_handling": "Old two-repo paid results remain immutable historical observations. They motivate this repair but are not corrected, rerun-equivalent, or merged into the new release score.",
        "manifest_digest": manifest_digest(manifest),
        "planned_adapters": manifest["planned_adapters"],
        "planned_metrics": [
            "per_repo_split_scoreable_pass_rate",
            "adapter_level_scoreable_pass_rate",
            "B_eval_to_H_future_gap",
            "policy_violation_rate",
            "cost_and_latency_by_adapter",
        ],
        "planned_paid_validation_prefix": manifest["paid_validation_prefix_reserved"],
        "policy_violation_handling": "Future policy-violation cells are terminal non-scoreable outcomes and do not repair old attrs__hist__027 policy status.",
        "predictive_validity_established": False,
        "release_id": manifest["release_id"],
        "research_question": "Can a canonical-split, statement-hardened two-repo release support a future paid validation of target-repository predictive behavior without reusing the old statement-risk-confounded score tables?",
        "schema_version": PREREGISTRATION_SCHEMA,
        "scoreability_rules": manifest["scoreability_policy"],
        "statement_quality_gate": {
            "deterministic_qa_status_required": "pass",
            "forbidden_material_disallowed": [
                "raw diff hunks",
                "target commit hashes",
                "hidden verifier markers",
                "paid outcome text",
                "raw test assertions",
            ],
            "review_status_required": "pass",
            "statement_digest_must_match_text": True,
        },
        "status": "written",
        "stop_conditions": [
            "missing full statement text",
            "review or deterministic QA status below pass",
            "statement digest mismatch",
            "statement leakage or unsafe editable scope",
            "need for paid ACUT call, paid LLM call, or Codex generator/reviewer session",
            "need to modify ACUT internals or rewrite old score tables",
        ],
        "task_inclusion_rule": {
            "canonical_selected_task_ids_by_repo_split": manifest["canonical_selected_task_ids_by_repo_split"],
            "selected_task_count": manifest["planned_cells_policy"]["selected_task_count"],
        },
        "uncertainty_metrics": [
            "Wilson interval by repo split",
            "bootstrap confidence interval by task",
            "adapter disagreement rate",
        ],
    }


def build_validation_decision_payload(
    config: dict[str, Any],
    *,
    manifest: dict[str, Any] | None,
    preregistration: dict[str, Any] | None,
    blocked_task_ids: list[str] | None = None,
    blocker_reasons: list[str] | None = None,
) -> dict[str, Any]:
    blocked_task_ids = blocked_task_ids or []
    blocker_reasons = blocker_reasons or []
    release_frozen = bool(manifest and manifest.get("status") == "frozen")
    prereg_written = bool(preregistration and preregistration.get("status") == "written")
    if release_frozen and prereg_written:
        primary = "ready_for_user_approved_paid_validation"
    elif blocked_task_ids:
        primary = "blocked_on_canonical_statement_inputs"
    elif blocker_reasons:
        primary = "blocked_on_policy_or_scope"
    else:
        primary = "blocked_on_tooling"
    return {
        "blocked_task_ids": blocked_task_ids,
        "blocker_reasons": blocker_reasons,
        "followup_runbook_written_by_worker": False,
        "generated_at": generated_at(config),
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "paid_validation_blocked_until_user_approval": True,
        "predictive_validity_established": False,
        "preregistration_written": prereg_written,
        "primary_decision": primary,
        "recommended_next_action": "ask user whether to authorize paid validation runbook"
        if primary == "ready_for_user_approved_paid_validation"
        else "repair the recorded blocker before paid validation",
        "release_frozen": release_frozen,
        "schema_version": "barcarolle.phase1.statement_hardened_after_canonical_repair_validation_decision.v1",
        "suggested_followup_runbook_path": "docs/experiments/phase-1-statement-hardened-paid-validation-runbook.md",
    }


def build_blocker_payload(config: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    blocked = decision["primary_decision"] != "ready_for_user_approved_paid_validation"
    return {
        "blocked": blocked,
        "blocked_task_ids": decision["blocked_task_ids"],
        "blocker_reasons": decision["blocker_reasons"],
        "followup_runbook_written_by_worker": False,
        "generated_at": generated_at(config),
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "primary_decision": decision["primary_decision"],
        "schema_version": "barcarolle.phase1.statement_hardened_after_canonical_repair_blocker.v1",
        "status": "blocked" if blocked else "not_blocked",
    }


def render_inventory_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Statement-Hardened After Canonical Repair Inventory",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "## Summary",
        "",
        f"- Canonical task count: `{payload['summary']['canonical_task_count']}`.",
        f"- Repo/split counts: `{payload['summary']['repo_split_counts']}`.",
        f"- Statement source counts: `{payload['summary']['statement_source_counts']}`.",
        "- Historical pass/fail outcomes used for selection: `false`.",
        "- Current inventory split used for selection: `false`.",
        "",
        "## Tasks",
        "",
    ]
    for row in payload["rows"]:
        lines.extend(
            [
                f"### {row['task_id']}",
                "",
                f"- Canonical repo/split: `{row['canonical_repo_split']}`.",
                f"- Current inventory split: `{row['current_inventory_split']}`.",
                f"- Statement digest: `{row['statement_digest']}`.",
                f"- Review status: `{row['review_status']}`.",
                f"- Deterministic QA status: `{row['deterministic_qa_status']}`.",
                f"- Editable implementation paths: `{row['editable_implementation_paths']}`.",
                f"- Non-editable test paths: `{row['non_editable_test_paths']}`.",
                "",
            ]
        )
    return "\n".join(lines)


def render_screen_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Statement-Hardened After Canonical Repair Screen",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Canonical statement inputs verified: `{payload['canonical_statement_inputs_verified']}`.",
            f"- Selected counts by repo/split: `{payload['selected_counts_by_repo_split']}`.",
            f"- Remaining missing supply: `{payload['remaining_missing_supply']}`.",
            f"- Review counts: `{payload['review_counts']}`.",
            f"- Deterministic QA counts: `{payload['deterministic_qa_counts']}`.",
            "- Historical pass/fail outcomes used for selection: `false`.",
            "- Current inventory split used for selection: `false`.",
            "- Paid outcome used for selection: `false`.",
        ]
    )


def render_release_preview_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Statement-Hardened After Canonical Repair Release Preview",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "These generated statements are solver-visible task statements. They are not scoreable results.",
        "",
        f"- Preview count: `{payload['summary']['preview_count']}`.",
        f"- Scoreable result count: `{payload['summary']['scoreable_result_count']}`.",
        "",
    ]
    for row in payload["previews"]:
        lines.extend(
            [
                f"## {row['task_id']}",
                "",
                f"- Canonical repo/split: `{row['canonical_repo_split']}`.",
                f"- Statement digest: `{row['statement_digest']}`.",
                "",
                "```text",
                row["visible_statement"],
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def render_manifest_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Statement-Hardened After Canonical Repair Release Manifest",
            "",
            f"Release ID: `{payload['release_id']}`.",
            f"Created: `{payload['created_at']}`.",
            f"Status: `{payload['status']}`.",
            "",
            f"- Planned adapters: `{payload['planned_adapters']}`.",
            f"- Planned cells: `{payload['planned_cells']}`.",
            f"- Paid validation prefix reserved: `{payload['paid_validation_prefix_reserved']}`.",
            "- Paid validation executed: `false`.",
            "- Predictive validity established: `false`.",
            "- Old paid results are historical immutable context only.",
        ]
    )


def render_preregistration_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Statement-Hardened After Canonical Repair Preregistration",
        "",
        f"Release ID: `{payload['release_id']}`.",
        f"Created: `{payload['created_at']}`.",
        "",
        "## Research Question",
        "",
        payload["research_question"],
        "",
        "## Gate",
        "",
        "- Paid validation has not started.",
        "- Predictive validity has not been established.",
        "- Old paid results are not repaired or overwritten.",
        "- `attrs__hist__027` old policy violation is not repaired by this local preregistration.",
        "- Future paid validation requires explicit user approval and a separate runbook.",
        "- Future paid validation must use `LLM_BASE_URL` and `LLM_API_KEY`.",
        "",
        "## Claims Disallowed",
        "",
    ]
    lines.extend(f"- `{claim}`" for claim in payload["claims_disallowed"])
    return "\n".join(lines)


def render_decision_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Statement-Hardened After Canonical Repair Validation Decision",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Primary decision: `{payload['primary_decision']}`.",
            f"- Release frozen: `{payload['release_frozen']}`.",
            f"- Preregistration written: `{payload['preregistration_written']}`.",
            f"- Paid validation blocked until user approval: `{payload['paid_validation_blocked_until_user_approval']}`.",
            f"- Recommended next action: `{payload['recommended_next_action']}`.",
            f"- Suggested follow-up runbook path: `{payload['suggested_followup_runbook_path']}`.",
            f"- Follow-up runbook written by worker: `{payload['followup_runbook_written_by_worker']}`.",
            "- Predictive validity established: `false`.",
        ]
    )


def render_blocker_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Statement-Hardened After Canonical Repair Blocker",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Status: `{payload['status']}`.",
            f"- Primary decision: `{payload['primary_decision']}`.",
            f"- Blocked task IDs: `{payload['blocked_task_ids']}`.",
            f"- Blocker reasons: `{payload['blocker_reasons']}`.",
            f"- Follow-up runbook written by worker: `{payload['followup_runbook_written_by_worker']}`.",
        ]
    )


def write_inventory_and_screen(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    inventory = build_inventory_payload(config)
    screen = build_screen_payload(config, inventory)
    write_json(output_path(config, "inventory"), inventory)
    write_text(output_path(config, "inventory_report"), render_inventory_markdown(inventory))
    write_json(output_path(config, "screen"), screen)
    write_text(output_path(config, "screen_report"), render_screen_markdown(screen))
    return inventory, screen


def write_preview_and_manifest(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    inventory = build_inventory_payload(config)
    screen = build_screen_payload(config, inventory)
    preview = build_release_preview_payload(config, inventory, screen)
    manifest = build_release_manifest_payload(config, inventory, screen, preview)
    write_json(output_path(config, "release_preview"), preview)
    write_text(output_path(config, "release_preview_report"), render_release_preview_markdown(preview))
    write_json(output_path(config, "release_manifest"), manifest)
    write_text(output_path(config, "release_manifest_report"), render_manifest_markdown(manifest))
    return preview, manifest


def write_preregistration(config: dict[str, Any]) -> dict[str, Any]:
    manifest = read_json(output_path(config, "release_manifest"))
    payload = build_preregistration_payload(config, manifest)
    write_json(output_path(config, "preregistration"), payload)
    write_text(output_path(config, "preregistration_report"), render_preregistration_markdown(payload))
    return payload


def write_decision(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_path = output_path(config, "release_manifest")
    prereg_path = output_path(config, "preregistration")
    manifest = read_json(manifest_path) if manifest_path.exists() else None
    preregistration = read_json(prereg_path) if prereg_path.exists() else None
    decision = build_validation_decision_payload(config, manifest=manifest, preregistration=preregistration)
    blocker = build_blocker_payload(config, decision)
    write_json(output_path(config, "validation_decision"), decision)
    write_text(output_path(config, "validation_decision_report"), render_decision_markdown(decision))
    write_json(output_path(config, "blocker"), blocker)
    write_text(output_path(config, "blocker_report"), render_blocker_markdown(blocker))
    return decision, blocker


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Freeze statement-hardened preregistration artifacts after canonical split repair."
    )
    parser.add_argument(
        "mode",
        choices=["inventory-screen", "preview-manifest", "preregister", "decide", "all"],
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))
    if args.mode in {"inventory-screen", "all"}:
        write_inventory_and_screen(config)
    if args.mode in {"preview-manifest", "all"}:
        write_preview_and_manifest(config)
    if args.mode in {"preregister", "all"}:
        write_preregistration(config)
    if args.mode in {"decide", "all"}:
        write_decision(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
