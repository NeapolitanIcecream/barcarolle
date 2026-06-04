from __future__ import annotations

import json

import pytest

import phase1_canonical_split_statement_repair as repair


def test_canonical_split_map_ignores_pass_fail_statuses() -> None:
    entry_gate = {
        "b_eval": {"selected_task_ids": ["boltons__hist__011"]},
        "h_future": {"selected_task_ids": ["boltons__clean_ext__017"]},
    }
    matrix = {
        "cells": [
            {
                "adapter_id": "codex_workspace",
                "repo_id": "boltons",
                "task_id": "boltons__clean_ext__017",
                "selected_split_from_frozen_design": "H_future",
                "split": "H_future",
                "terminal_status": "verified_fail",
                "verified_pass": False,
                "verified_fail": True,
                "policy_violation": False,
            },
            {
                "adapter_id": "kilo_workspace",
                "repo_id": "boltons",
                "task_id": "boltons__hist__011",
                "selected_split_from_frozen_design": "B_eval",
                "split": "B_eval",
                "terminal_status": "verified_pass",
                "verified_pass": True,
                "verified_fail": False,
                "policy_violation": False,
            },
        ]
    }

    payload = repair.build_canonical_split_map_payload(
        entry_gate=entry_gate,
        matrix=matrix,
        generated_at="2026-05-25T00:00:00Z",
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["task_to_split"]["boltons__clean_ext__017"]["repo_split"] == "boltons/H_future"
    assert payload["task_to_split"]["boltons__hist__011"]["repo_split"] == "boltons/B_eval"
    assert payload["historical_pass_fail_outcomes_used_for_selection"] is False
    assert "verified_pass" not in encoded
    assert "verified_fail" not in encoded


def test_canonical_split_map_rejects_matrix_split_mismatch() -> None:
    matrix = {
        "cells": [
            {
                "repo_id": "boltons",
                "task_id": "boltons__clean_ext__017",
                "selected_split_from_frozen_design": "B_eval",
                "terminal_status": "verified_pass",
            }
        ]
    }

    with pytest.raises(ValueError, match="matrix split mismatch"):
        repair.build_canonical_split_map_payload(
            entry_gate={},
            matrix=matrix,
            generated_at="2026-05-25T00:00:00Z",
        )


def test_inventory_row_needs_new_statement_unless_review_and_qa_pass() -> None:
    split_row = {
        "task_id": "boltons__hist__022",
        "repo_id": "boltons",
        "canonical_split": "H_future",
        "repo_split": "boltons/H_future",
    }
    certified = {
        "allowed_context_refs": ["pr:312"],
        "changed_files": ["boltons/iterutils.py", "tests/test_iterutils.py"],
        "code_files": ["boltons/iterutils.py"],
        "gates": {"checkout": "pass"},
        "module_or_package": ["iterutils"],
        "task_time": "2023-02-20T07:22:09+01:00",
        "test_files": ["tests/test_iterutils.py"],
    }
    context = {
        "body_summary": "Public problem context.",
        "classification": "problem_context",
        "ref": "pr:312",
        "summary": "add chunk_ranges function to iterutils",
    }

    missing = repair.canonical_inventory_row(
        split_row=split_row,
        certified=certified,
        context=context,
        existing_statement={"statement_digest": "sha256:abc"},
        existing_review={"status": "pass"},
        existing_qa={"status": "reject"},
    )
    reusable = repair.canonical_inventory_row(
        split_row=split_row,
        certified=certified,
        context=context,
        existing_statement={"statement_digest": "sha256:abc"},
        existing_review={"status": "pass"},
        existing_qa={"status": "pass"},
    )

    assert missing["needs_new_codex_loop_statement"] is True
    assert reusable["needs_new_codex_loop_statement"] is False


def test_run_script_uses_local_subscription_and_unsets_endpoint_vars() -> None:
    config = {
        "generation_review": {
            "workflow_dir": ".codex-workflows/test-canonical-workflow",
            "generator_tmux_session": "generator-session",
        },
        "policy": {
            "required_codex_model": "gpt-5.5",
            "required_reasoning_effort": "xhigh",
            "endpoint_env_vars_unset_for_generator_reviewer": [
                "LLM_BASE_URL",
                "LLM_API_KEY",
                "OPENAI_API_KEY",
                "OPENROUTER_API_KEY",
            ],
        },
    }

    script = repair.run_script_text("generator", config)

    assert "env -u LLM_BASE_URL -u LLM_API_KEY -u OPENAI_API_KEY -u OPENROUTER_API_KEY" in script
    assert "--ignore-user-config" not in script
    assert "model_provider" not in script
    assert "local Codex Subscription" in script


def test_packet_redaction_removes_public_context_hex_hashes() -> None:
    payload = {
        "public_context": {
            "body_excerpt": "See https://example.invalid/0123456789abcdef0123456789abcdef01234567/file.py",
        },
        "target_diff_digest": "sha256:" + ("a" * 64),
    }

    redacted = repair.redact_commit_hash_like_text(payload)

    assert "0123456789abcdef0123456789abcdef01234567" not in redacted["public_context"]["body_excerpt"]
    assert redacted["target_diff_digest"] == payload["target_diff_digest"]


def test_canonical_screen_uses_canonical_split_not_current_inventory_split() -> None:
    screen = {
        "task_id": "boltons__clean_ext__017",
        "repo_id": "boltons",
        "canonical_split": "H_future",
        "canonical_repo_split": "boltons/H_future",
        "current_inventory_split": "B_eval",
        "eligible_under_canonical_split_repair": True,
    }

    assert screen["canonical_repo_split"] == "boltons/H_future"
    assert screen["current_inventory_split"] != screen["canonical_split"]
