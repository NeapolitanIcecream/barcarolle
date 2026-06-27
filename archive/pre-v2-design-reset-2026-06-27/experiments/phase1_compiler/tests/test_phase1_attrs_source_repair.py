from __future__ import annotations

import json
import re

import phase1_attrs_source_repair as repair


TARGET_IDS = ["attrs__v2__218", "attrs__v2__231", "attrs__v2__237"]


def test_preflight_finds_exact_attrs_source_review_tasks() -> None:
    config = repair.load_config()

    payload = repair.preflight_payload(config)

    assert payload["target_task_ids"] == TARGET_IDS
    assert payload["all_target_tasks_found"] is True
    assert payload["all_targets_technical_certified"] is True
    assert payload["all_targets_release_ineligible_due_to_source_context"] is True
    assert all(row["source_context_quality"] == "commit_message_only_context" for row in payload["task_statuses"])
    assert payload["paid_calls"]["paid_acut_solver_cells_run"] is False


def test_candidate_packets_are_sanitized_but_traceable() -> None:
    config = repair.load_config()

    payload = repair.build_candidate_packets(config)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["packet_count"] == 3
    assert payload["candidate_ids"] == TARGET_IDS
    assert "diff --git" not in encoded
    assert "\n@@" not in encoded
    assert "hidden verifier" not in encoded.lower()
    assert all(packet["target_commit"] for packet in payload["packets"])
    assert all(packet["diff_summaries"]["implementation_diff_digest"].startswith("sha256:") for packet in payload["packets"])
    assert all(packet["diff_summaries"]["test_diff_digest"].startswith("sha256:") for packet in payload["packets"])


def test_public_context_accepts_all_three_tasks_without_llm_generation() -> None:
    config = repair.load_config()
    packets = repair.build_candidate_packets(config)

    payload = repair.build_public_context_review(config, packets)

    assert payload["accepted_public_context_count"] == 3
    assert payload["diff_assisted_statement_repair_needed"] is False
    assert {row["verdict"] for row in payload["reviews"]} == {"accepted_public_context"}
    assert all(row["leakage_flags"] == [] for row in payload["reviews"])
    assert all(row["ambiguity_flags"] == [] for row in payload["reviews"])


def test_statement_packets_do_not_expose_target_hashes_or_raw_diffs() -> None:
    config = repair.load_config()
    packets = repair.build_candidate_packets(config)
    context = repair.build_public_context_review(config, packets)

    payload = repair.build_statement_packets(config, packets, context)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["statement_packet_count"] == 3
    assert payload["diff_assisted_generation_status"] == "skipped_public_context_sufficient"
    assert payload["paid_llm_calls_made"] is False
    assert "diff --git" not in encoded
    assert "\n@@" not in encoded
    assert not re.search(r"\b[0-9a-f]{40}\b", encoded)
    assert all(packet["raw_statement_text_committed"] is False for packet in payload["statement_packets"])


def test_overlay_promotes_attrs_to_31_release_eligible_but_paid_gate_stays_false() -> None:
    config = repair.load_config()
    packets = repair.build_candidate_packets(config)
    context = repair.build_public_context_review(config, packets)
    statement_payload = repair.build_statement_packets(config, packets, context)
    review_payload = repair.build_review_records(config, statement_payload)

    overlay = repair.build_release_overlay(config, review_payload)
    gate = repair.build_paid_readiness_gate(config, overlay)

    assert overlay["promoted_task_count"] == 3
    assert overlay["attrs_release_eligible_count_before_overlay"] == 28
    assert overlay["attrs_release_eligible_count_after_overlay"] == 31
    assert overlay["attrs_reached_30_release_eligible"] is True
    assert gate["paid_ready"] is False
    assert gate["repos_meeting_30_release_eligible"] == ["attrs", "boltons"]
    assert gate["blocking_reasons"] == ["third_repo_still_needed"]
