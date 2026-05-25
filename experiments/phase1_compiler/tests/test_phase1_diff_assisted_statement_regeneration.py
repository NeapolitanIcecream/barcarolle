from __future__ import annotations

import json
import subprocess
from pathlib import Path

import phase1_diff_assisted_statement_regeneration as diffregen


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
    (repo / "tests" / "test_core.py").write_text("def test_f():\n    assert f(1) == 2\n", encoding="utf-8")
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


def test_candidate_packet_excludes_raw_diff_text_and_test_assertions_by_default(tmp_path: Path) -> None:
    config = minimal_config(tmp_path)
    certified = {
        "base_commit": config["_base"],
        "changed_files": ["pkg/core.py", "tests/test_core.py"],
        "target_commit": config["_target"],
    }
    source_context = {
        "body_summary": "Calling f with a small integer returns the wrong public value.",
        "classification": "problem_context",
        "ref": "issue:1",
        "state": "closed",
        "summary": "f returns the wrong value",
    }

    packet = diffregen.build_candidate_packet(
        config=config,
        candidate=candidate_record(),
        certified=certified,
        source_context=source_context,
    )

    encoded = json.dumps(packet, sort_keys=True)
    assert "diff --git" not in encoded
    assert "assert f(1) == 2" not in encoded
    assert "return value + 1" not in encoded
    assert packet["target_diff_digest"].startswith("sha256:")
    assert packet["test_diff_digest"].startswith("sha256:")


def test_candidate_packet_separates_public_context_diff_summary_and_scope_metadata(tmp_path: Path) -> None:
    config = minimal_config(tmp_path)
    certified = {
        "base_commit": config["_base"],
        "changed_files": ["pkg/core.py", "tests/test_core.py"],
        "target_commit": config["_target"],
    }
    source_context = {
        "body_summary": "Public issue body",
        "classification": "problem_context",
        "ref": "issue:1",
        "state": "closed",
        "summary": "Public issue title",
    }

    packet = diffregen.build_candidate_packet(
        config=config,
        candidate=candidate_record(),
        certified=certified,
        source_context=source_context,
    )

    assert packet["public_context"]["title"] == "Public issue title"
    assert packet["diff_summary"]["implementation_files_changed"] == ["pkg/core.py"]
    assert packet["scope_metadata"]["editable_paths"] == ["pkg/core.py"]
    assert packet["scope_metadata"]["non_editable_test_paths"] == ["tests/test_core.py"]


def test_old_240_character_truncation_is_recoverable_packet_metadata() -> None:
    config = {"external_repos": {"demo": ""}}
    certified = {"changed_files": ["pkg/core.py", "tests/test_core.py"]}
    source_context = {
        "body_summary": "x" * 240,
        "classification": "problem_context",
        "ref": "issue:1",
        "summary": "Public issue title",
    }

    packet = diffregen.build_candidate_packet(
        config=config,
        candidate=candidate_record(),
        certified=certified,
        source_context=source_context,
    )

    assert packet["old_statement_quality"]["body_summary_hit_old_cap"] is True
    assert packet["old_statement_quality"]["old_truncation_treated_as_recoverable_renderer_defect"] is True


def test_generator_prompt_omits_paid_outcomes_hidden_fields_and_raw_statuses(tmp_path: Path) -> None:
    config = minimal_config(tmp_path)
    certified = {
        "base_commit": config["_base"],
        "changed_files": ["pkg/core.py", "tests/test_core.py"],
        "target_commit": config["_target"],
    }
    packet = diffregen.build_candidate_packet(
        config=config,
        candidate=candidate_record(),
        certified=certified,
        source_context={
            "body_summary": "Public issue body",
            "classification": "problem_context",
            "ref": "issue:1",
            "summary": "Public issue title",
        },
    )
    packet["historical_paid_context"] = {"terminal_status": "verified_pass"}
    packet["hidden_verifier"] = "private oracle details"
    packet["raw_diff"] = "diff --git a/pkg/core.py b/pkg/core.py"

    prompt = diffregen.build_statement_generator_prompt(packet)

    assert "historical_paid_context" not in prompt
    assert "verified_pass" not in prompt
    assert "private oracle details" not in prompt
    assert "diff --git" not in prompt
    assert "statement_generator" in prompt


def test_reviewer_prompt_uses_machine_readable_review_schema(tmp_path: Path) -> None:
    config = minimal_config(tmp_path)
    packet = diffregen.build_candidate_packet(
        config=config,
        candidate=candidate_record(),
        certified={
            "base_commit": config["_base"],
            "changed_files": ["pkg/core.py", "tests/test_core.py"],
            "target_commit": config["_target"],
        },
        source_context={
            "body_summary": "Public issue body",
            "classification": "problem_context",
            "ref": "issue:1",
            "summary": "Public issue title",
        },
    )

    prompt = diffregen.build_statement_reviewer_prompt(packet, "Problem summary: public behavior is wrong.")

    assert '"status_values": [' in prompt
    assert '"pass"' in prompt
    assert '"revise"' in prompt
    assert '"reject"' in prompt
    assert "statement_reviewer" in prompt


def test_revision_prompt_sanitizes_reviewer_feedback(tmp_path: Path) -> None:
    config = minimal_config(tmp_path)
    packet = diffregen.build_candidate_packet(
        config=config,
        candidate=candidate_record(),
        certified={
            "base_commit": config["_base"],
            "changed_files": ["pkg/core.py", "tests/test_core.py"],
            "target_commit": config["_target"],
        },
        source_context={
            "body_summary": "Public issue body",
            "classification": "problem_context",
            "ref": "issue:1",
            "summary": "Public issue title",
        },
    )

    prompt = diffregen.build_statement_revision_prompt(
        packet,
        "Problem summary: public behavior is wrong.",
        {"status": "revise", "terminal_status": "verified_fail", "reasons": ["add expected behavior"]},
    )

    assert "verified_fail" not in prompt
    assert "add expected behavior" in prompt
    assert "statement_revision" in prompt
