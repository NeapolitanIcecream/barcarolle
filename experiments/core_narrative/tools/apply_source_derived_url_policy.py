#!/usr/bin/env python3
"""Policy helper for source-derived URL-only candidate patch artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail


TOOL = "apply_source_derived_url_policy"
POLICY_VERSION = "source-derived-url-only-v1"


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and value > 0


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def source_derived_url_only(findings: Mapping[str, Any], attribution: Mapping[str, Any]) -> bool:
    """Return true when all unsafe findings are full URLs copied from source diff lines."""
    if findings.get("unsafe") is not True:
        return False

    reason_counts = _mapping(findings.get("reason_counts"))
    if set(reason_counts) != {"full_url"} or not _positive_int(reason_counts.get("full_url")):
        return False

    non_url_reason_counts = _mapping(attribution.get("non_url_reason_counts"))
    if any(_positive_int(value) for value in non_url_reason_counts.values()):
        return False

    return (
        attribution.get("all_full_urls_source_derived") is True
        and attribution.get("all_unsafe_reasons_source_derived") is True
        and int(attribution.get("model_generated_full_url_count") or 0) == 0
        and int(attribution.get("ambiguous_full_url_count") or 0) == 0
    )


def candidate_patch_policy(findings: Mapping[str, Any], attribution: Mapping[str, Any]) -> dict[str, Any]:
    """Classify candidate patch artifact handling for primary workspace replay."""
    if findings.get("unsafe") is not True:
        return {
            "policy_version": POLICY_VERSION,
            "decision": "safe_public_patch",
            "allow_private_verifier_replay": False,
            "blocks_primary_scoring": False,
            "public_artifact_policy": "write_raw_candidate_patch",
            "primary_status_if_blocked": None,
            "reason": "no_unsafe_candidate_patch_content",
        }

    if source_derived_url_only(findings, attribution):
        return {
            "policy_version": POLICY_VERSION,
            "decision": "allow_private_replay_source_derived_url_only",
            "allow_private_verifier_replay": True,
            "blocks_primary_scoring": False,
            "public_artifact_policy": "write_redacted_preview_only",
            "primary_status_if_blocked": None,
            "reason": "candidate_patch_full_urls_are_source_context_or_removed_lines_only",
        }

    return {
        "policy_version": POLICY_VERSION,
        "decision": "reject_true_or_ambiguous_unsafe",
        "allow_private_verifier_replay": False,
        "blocks_primary_scoring": True,
        "public_artifact_policy": "write_redacted_preview_only",
        "primary_status_if_blocked": "unsafe_or_scope_violation",
        "reason": "candidate_patch_contains_model_generated_or_ambiguous_unsafe_content",
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON object with unsafe_content and unsafe_content_attribution.")
    parser.add_argument("--output", help="Optional policy decision JSON output.")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ToolError("input root must be a JSON object", path=args.input)
        findings = _mapping(payload.get("unsafe_content"))
        attribution = _mapping(payload.get("unsafe_content_attribution"))
        decision = {
            "tool": TOOL,
            "policy": candidate_patch_policy(findings, attribution),
        }
        emit_json(decision, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
