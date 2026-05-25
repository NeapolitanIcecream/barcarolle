from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import phase1_diff_assisted_codex_loop_statement_regeneration as codexloop


def minimal_config(tmp_path: Path) -> dict:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init"], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test User"], check=True)
    (repo / "pkg").mkdir()
    (repo / "tests").mkdir()
    (repo / "pkg" / "core.py").write_text("def f(value):\n    return value\n", encoding="utf-8")
    (repo / "tests" / "test_core.py").write_text("def test_f():\n    assert True\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "base"], check=True, stdout=subprocess.DEVNULL)
    base = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    (repo / "pkg" / "core.py").write_text("def f(value):\n    return value + 1\n", encoding="utf-8")
    (repo / "tests" / "test_core.py").write_text("from pkg.core import f\n\ndef test_f():\n    assert f(1) == 2\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "target"], check=True, stdout=subprocess.DEVNULL)
    target = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    return {
        "external_repos": {"demo": str(repo)},
        "_base": base,
        "_target": target,
    }


def candidate_record() -> dict:
    return {
        "certification_gate_summary": {
            "all_pass": True,
            "failed_gates": [],
            "gate_count": 2,
            "gate_counts": {"pass": 2},
        },
        "historical_paid_context": {
            "terminal_status_counts": {"verified_pass": 1},
            "used_for_selection": False,
        },
        "implementation_files": ["pkg/core.py"],
        "module_or_package": ["core"],
        "repo_id": "demo",
        "source_ref": "issue:1",
        "statement_quality_diagnostics": {
            "body_summary_hit_old_cap": True,
            "statement_probably_truncated": True,
        },
        "statement_quality_gate": "fail",
        "statement_quality_risk_reasons": [
            "body_summary_hit_old_240_char_cap",
            "statement_probably_truncated",
        ],
        "task_id": "demo__001",
        "task_time": "2024-01-01T00:00:00+00:00",
        "test_files": ["tests/test_core.py"],
        "verifier_command_metadata": "pytest tests/test_core.py",
    }


def source_context() -> dict:
    return {
        "body_summary": "Calling f with a small integer returns the wrong public value.",
        "classification": "problem_context",
        "ref": "issue:1",
        "state": "closed",
        "summary": "f returns the wrong value",
    }


def packet(tmp_path: Path) -> dict:
    config = minimal_config(tmp_path)
    return codexloop.build_codex_loop_candidate_packet(
        config=config,
        candidate=candidate_record(),
        certified={
            "base_commit": config["_base"],
            "changed_files": ["pkg/core.py", "tests/test_core.py"],
            "target_commit": config["_target"],
        },
        source_context=source_context(),
    )


def test_codex_loop_packet_excludes_paid_outcomes_raw_diff_and_test_assertions(tmp_path: Path) -> None:
    built = packet(tmp_path)
    encoded = json.dumps(built, sort_keys=True)

    assert built["real_codex_loop_required"] is True
    assert built["deterministic_generation_allowed"] is False
    assert built["deterministic_review_allowed"] is False
    assert "historical_paid_context" not in encoded
    assert "verified_pass" not in encoded
    assert "diff --git" not in encoded
    assert "assert f(1) == 2" not in encoded
    assert "return value + 1" not in encoded
    assert built["target_diff_digest"].startswith("sha256:")
    assert built["test_diff_digest"].startswith("sha256:")


def test_packet_payload_validator_rejects_forbidden_status_text(tmp_path: Path) -> None:
    built = packet(tmp_path)
    built["public_context"]["body_excerpt"] = "This text leaks verified_fail from a paid run."
    payload = {"packets": [built]}

    with pytest.raises(ValueError, match="paid_terminal_status"):
        codexloop.validate_packet_payload(payload)


def test_corrected_tool_has_no_deterministic_generate_mode() -> None:
    assert "generate" not in codexloop.MODES


def test_run_script_uses_local_subscription_and_unsets_endpoint_vars(tmp_path: Path) -> None:
    config = {
        "generation_review": {
            "workflow_dir": ".codex-workflows/test-local-subscription-workflow",
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

    script = codexloop.run_script_text("generator", config)

    assert "env -u LLM_BASE_URL -u LLM_API_KEY -u OPENAI_API_KEY -u OPENROUTER_API_KEY" in script
    assert "--ignore-user-config" not in script
    assert "model_provider=\"barcarolle_llm\"" not in script
    assert "LLM_API_KEY was missing" not in script
    assert "local Codex Subscription" in script


def test_generated_statement_validation_rejects_deterministic_override_marker() -> None:
    statement = "Problem summary: public behavior.\nExpected behavior: public behavior should work."
    rows = [
        {
            "task_id": "demo__001",
            "statement": statement,
            "statement_digest": codexloop.statement_digest(statement),
            "generation_notes": "Used deterministic behavior override.",
            "used_diff_summary": True,
            "contains_raw_diff": False,
            "contains_paid_outcome": False,
        }
    ]

    with pytest.raises(ValueError, match="deterministic override"):
        codexloop.validate_generated_statement_rows(rows, packet_count=1)


def test_review_validation_requires_all_pass_booleans_for_pass_status() -> None:
    statement = "Problem summary: public behavior.\nExpected behavior: public behavior should work."
    generated = [
        {
            "task_id": "demo__001",
            "statement": statement,
            "statement_digest": codexloop.statement_digest(statement),
        }
    ]
    payload = {
        "reviews": [
            {
                "task_id": "demo__001",
                "status": "pass",
                "leakage_pass": True,
                "sufficiency_pass": False,
                "faithfulness_pass": True,
                "scope_pass": True,
                "formatting_pass": True,
                "reasons": ["too thin"],
                "required_revision": "",
                "statement_digest": codexloop.statement_digest(statement),
            }
        ]
    }

    with pytest.raises(ValueError, match="pass review has failing boolean"):
        codexloop.validate_review_payload(payload, generated)


def test_review_validation_allows_rubric_reference_to_hidden_verifier() -> None:
    statement = "Problem summary: public behavior.\nExpected behavior: public behavior should work."
    generated = [
        {
            "task_id": "demo__001",
            "statement": statement,
            "statement_digest": codexloop.statement_digest(statement),
        }
    ]
    payload = {
        "reviews": [
            {
                "task_id": "demo__001",
                "status": "pass",
                "leakage_pass": True,
                "sufficiency_pass": True,
                "faithfulness_pass": True,
                "scope_pass": True,
                "formatting_pass": True,
                "reasons": ["No hidden verifier content is present."],
                "required_revision": "",
                "statement_digest": codexloop.statement_digest(statement),
            }
        ]
    }

    codexloop.validate_review_payload(payload, generated)


def test_deterministic_qa_cannot_create_pass_without_reviewer_pass(tmp_path: Path) -> None:
    built = packet(tmp_path)
    statement = codexloop.dryrun.generated_statement_text(built)
    statement_row = {
        "task_id": built["task_id"],
        "statement": statement,
        "statement_digest": codexloop.statement_digest(statement),
    }
    review = {
        "task_id": built["task_id"],
        "status": "reject",
        "statement_digest": codexloop.statement_digest(statement),
    }

    qa = codexloop.deterministic_qa_row(built, statement_row, review)

    assert qa["status"] == "reject"
    assert "review_status:reject" in qa["reasons"]


def test_select_by_repo_split_reports_remaining_supply_holes() -> None:
    records = [
        {
            "eligible_after_codex_loop_regeneration": True,
            "release_split_eligibility": ["B_eval"],
            "repo_id": "demo",
            "task_id": "demo__001",
            "task_time": "2024-01-01T00:00:00+00:00",
        }
    ]

    selected = codexloop.select_by_repo_split(records, repos=["demo"], splits=["B_eval", "H_future"], per_split=1)

    assert selected["demo/B_eval"] == ["demo__001"]
    assert selected["demo/H_future"] == []
