from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
if str(PHASE1_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE1_TOOLS))

import phase1_source_context_statement_hardening as hardening  # noqa: E402


HEX40_RE = re.compile(r"\b[0-9a-f]{40}\b")


def build_payloads() -> dict[str, dict[str, object]]:
    config = hardening.load_config()
    inventory = hardening.build_inventory(config)
    queue = hardening.build_repair_queue(config, inventory)
    packets = hardening.build_statement_packets(config, inventory, queue)
    reviews = hardening.build_review_records(config, inventory, packets)
    overlay = hardening.build_overlay(config, inventory, reviews)
    features = hardening.build_split_feature_table(config, inventory, overlay, packets)
    readiness = hardening.build_readiness_gate(config, inventory, overlay, features, reviews)
    return {
        "inventory": inventory,
        "queue": queue,
        "packets": packets,
        "reviews": reviews,
        "overlay": overlay,
        "features": features,
        "readiness": readiness,
    }


def test_inventory_counts_release_eligible_separately_from_technical_certified() -> None:
    inventory = hardening.build_inventory(hardening.load_config())

    assert inventory["paid_package_task_count"] == 96
    assert inventory["release_eligible_before_count"] == 96
    assert inventory["technical_certified_count"] == 153
    assert inventory["release_eligible_before_count_by_repo"] == {"attrs": 31, "boltons": 35, "click": 30}
    assert inventory["technical_certified_count_by_repo"] == {"attrs": 31, "boltons": 47, "click": 75}
    assert inventory["diagnostic_outcome_joined"] is False


def test_repair_queue_flags_title_and_commit_context_without_outcome_priority() -> None:
    payloads = build_payloads()
    queue = payloads["queue"]
    rows = queue["rows"]

    assert queue["queue_count"] == 91
    assert queue["policy"]["outcome_labels_can_promote_or_demote"] is False
    assert queue["policy"]["H_future_outcomes_can_promote_or_demote"] is False
    assert queue["policy"]["adapter_pass_fail_labels_can_promote_or_demote"] is False
    assert all(row["paid_outcome_used_for_priority"] is False for row in rows)
    assert all(
        "needs_statement_specificity_review" in row["queue_labels"]
        for row in rows
        if row["source_context_type"] == "pr_context_title_only"
    )
    assert all(
        "needs_diff_assisted_statement_review" in row["queue_labels"]
        for row in rows
        if row["source_context_type"] == "commit_message_only_context"
    )


def test_statement_packets_block_commit_message_only_without_guessing() -> None:
    payloads = build_payloads()
    packets = payloads["packets"]

    blocked = [row for row in packets["rows"] if row["repair_mode"] == "blocked_missing_public_problem_context"]
    assert len(blocked) == 57
    assert all(row["packet_status"] == "blocked" for row in blocked)
    assert all(row["allowed_public_context_summary"] == "" for row in blocked)
    assert all(row["blocked_reason"] == "missing_public_problem_context" for row in blocked)
    assert packets["paid_llm_calls_made"] == 0
    assert packets["raw_public_api_responses_committed"] is False


def test_review_overlay_does_not_promote_from_outcomes_and_keeps_paid_result_frozen() -> None:
    payloads = build_payloads()
    reviews = payloads["reviews"]
    overlay = payloads["overlay"]

    assert reviews["paid_outcomes_used_for_verdicts"] is False
    assert reviews["review_verdict_counts"] == {
        "keep_release_eligible": 33,
        "reject_ambiguous_scope": 1,
        "reject_missing_public_problem_context": 57,
    }
    assert overlay["release_eligible_before_count_by_repo"] == {"attrs": 31, "boltons": 35, "click": 30}
    assert overlay["release_eligible_after_count_by_repo"] == {"attrs": 30, "boltons": 35, "click": 30}
    assert overlay["release_eligible_changed_count"] == 1
    assert overlay["completed_paid_result_changed"] is False
    assert overlay["historical_paid_task_list_changed"] is False


def test_split_feature_table_uses_allowed_buckets_and_excludes_raw_text() -> None:
    features = build_payloads()["features"]

    assert features["eligible_for_split_design_count_by_repo"] == {"attrs": 30, "boltons": 35, "click": 30}
    assert features["raw_text_fields_committed"] is False
    encoded = json.dumps(features, sort_keys=True)
    assert not HEX40_RE.search(encoded)
    assert "solver_visible_problem_summary" not in encoded
    assert "allowed_public_context_summary" not in encoded
    assert "diff --git" not in encoded
    assert all(row["source_context_type_bucket"] in hardening.ALLOWED_SOURCE_CONTEXT_TYPE_BUCKETS for row in features["rows"])
    assert all(row["source_quality_bucket"] in hardening.ALLOWED_SOURCE_QUALITY_BUCKETS for row in features["rows"])
    assert all(row["statement_specificity_bucket"] in hardening.ALLOWED_STATEMENT_SPECIFICITY_BUCKETS for row in features["rows"])
    assert all(row["context_length_bucket"] in hardening.ALLOWED_CONTEXT_LENGTH_BUCKETS for row in features["rows"])
    assert all(row["editable_scope_bucket"] in hardening.ALLOWED_EDITABLE_SCOPE_BUCKETS for row in features["rows"])
    assert all(row["ambiguity_risk_bucket"] in hardening.ALLOWED_RISK_BUCKETS for row in features["rows"])
    assert all(row["leakage_risk_bucket"] in hardening.ALLOWED_RISK_BUCKETS for row in features["rows"])
    assert all(row["certification_risk_bucket"] in hardening.ALLOWED_CERTIFICATION_RISK_BUCKETS for row in features["rows"])


def test_readiness_gate_allows_reviewed_minor_risk_but_preserves_paid_boundary() -> None:
    readiness = build_payloads()["readiness"]

    assert readiness["decision_label"] == "source_context_ready_with_minor_risk"
    assert readiness["ready_for_blocked_split_design"] is True
    assert readiness["failed_gates"] == []
    assert readiness["paid_calls_made_by_this_run"] == 0
    assert readiness["completed_paid_decision_changed"] is False
    assert readiness["predictive_validity_established"] is False
    assert readiness["smallest_remaining_blocker"] == "click_title_only_minor_risk"
