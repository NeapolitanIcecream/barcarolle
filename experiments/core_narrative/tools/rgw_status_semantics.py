#!/usr/bin/env python3
"""Shared RGW-full-workspace-v1 status and denominator semantics."""

from __future__ import annotations

from typing import Any, Mapping


WORKSPACE_MODE_STATUSES = {
    "verified_pass",
    "verified_fail",
    "no_diff",
    "timeout",
    "unsafe_or_scope_violation",
    "patch_apply_error",
    "verifier_infra_error",
    "base_tree_mismatch",
    "candidate_patch_extraction_error",
    "acut_command_error",
}

PRIMARY_PASS_STATUSES = {"verified_pass"}
INFRASTRUCTURE_STATUSES = {
    "verifier_infra_error",
    "base_tree_mismatch",
    "candidate_patch_extraction_error",
}
TRIAGE_PAUSED_STATUSES = {"patch_apply_error"}
ACUT_ZERO_STATUSES = {
    "verified_fail",
    "no_diff",
    "unsafe_or_scope_violation",
    "acut_command_error",
}


def timeout_owner(payload: Mapping[str, Any]) -> str | None:
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), Mapping) else {}
    owner = payload.get("timeout_owner") or metadata.get("timeout_owner")
    if isinstance(owner, str) and owner:
        return owner
    verification = payload.get("verification") if isinstance(payload.get("verification"), Mapping) else {}
    owner = verification.get("timeout_owner")
    return str(owner) if isinstance(owner, str) and owner else None


def classify_status(status: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return the primary scoring action for a workspace-mode status."""
    payload = payload or {}
    owner = timeout_owner(payload)
    if status in PRIMARY_PASS_STATUSES:
        return {
            "category": "primary_pass",
            "primary_pass": True,
            "score_action": "fixed_denominator_one",
            "score_value": 1,
            "requires_rerun_or_exclusion": False,
            "triage_paused": False,
            "timeout_owner": owner,
        }
    if status == "timeout":
        if owner == "acut":
            return {
                "category": "acut_failure_zero",
                "primary_pass": False,
                "score_action": "fixed_denominator_zero",
                "score_value": 0,
                "requires_rerun_or_exclusion": False,
                "triage_paused": False,
                "timeout_owner": owner,
            }
        return {
            "category": "infrastructure",
            "primary_pass": False,
            "score_action": "rerun_or_global_exclusion_required",
            "score_value": None,
            "requires_rerun_or_exclusion": True,
            "triage_paused": False,
            "timeout_owner": owner,
        }
    if status in ACUT_ZERO_STATUSES:
        return {
            "category": "acut_failure_zero",
            "primary_pass": False,
            "score_action": "fixed_denominator_zero",
            "score_value": 0,
            "requires_rerun_or_exclusion": False,
            "triage_paused": False,
            "timeout_owner": owner,
        }
    if status in INFRASTRUCTURE_STATUSES:
        return {
            "category": "infrastructure",
            "primary_pass": False,
            "score_action": "rerun_or_global_exclusion_required",
            "score_value": None,
            "requires_rerun_or_exclusion": True,
            "triage_paused": False,
            "timeout_owner": owner,
        }
    if status in TRIAGE_PAUSED_STATUSES:
        return {
            "category": "triage_paused",
            "primary_pass": False,
            "score_action": "triage_paused_before_primary_scoring",
            "score_value": None,
            "requires_rerun_or_exclusion": False,
            "triage_paused": True,
            "timeout_owner": owner,
        }
    return {
        "category": "unknown_status",
        "primary_pass": False,
        "score_action": "invalid_for_primary_scoring",
        "score_value": None,
        "requires_rerun_or_exclusion": True,
        "triage_paused": False,
        "timeout_owner": owner,
    }


def score_value(status: str, payload: Mapping[str, Any] | None = None) -> int | None:
    value = classify_status(status, payload).get("score_value")
    return value if isinstance(value, int) else None
