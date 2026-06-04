from __future__ import annotations

import json
from pathlib import Path

import phase0_driver


def test_task_type_proxy_classifies_behavior_fix() -> None:
    assert (
        phase0_driver.task_type_proxy(
            "Raise in partition_all when length is invalid",
            ["toolz/itertoolz.py", "toolz/tests/test_itertoolz.py"],
        )
        == "bug_or_behavior_fix"
    )


def test_task_type_proxy_classifies_feature_extension() -> None:
    assert (
        phase0_driver.task_type_proxy(
            "Implement Compose.__repr__",
            ["toolz/functoolz.py", "toolz/tests/test_functoolz.py"],
        )
        == "feature_or_api_extension"
    )


def test_status_is_near_certified_when_oracle_valid_but_leakage_is_weak() -> None:
    gates = {
        "checkout": "pass",
        "oracle_extractable": "pass",
        "no_op_fail": "pass",
        "reference_pass": "pass",
        "known_bad_fail": "pass",
        "flakiness_check": "pass",
        "ambiguity_review": "pass",
        "solution_leakage_review": "weak:commit_subject_and_public_diff_may_expose_solution",
        "scope_clarity_review": "pass",
        "cost_boundedness": "pass",
        "taxonomy_labelability": "pass",
    }

    assert phase0_driver.status_from_gates(gates) == "near_certified"
    assert phase0_driver.first_failing_gate(gates) == "solution_leakage_review"


def test_empty_cost_ledger_is_zero(tmp_path: Path) -> None:
    ledger = tmp_path / "cost_ledger.jsonl"
    ledger.write_text("", encoding="utf-8")

    assert phase0_driver.read_cumulative_cost(ledger) == 0.0


def test_debug_artifact_is_machine_readable(tmp_path: Path) -> None:
    artifact = phase0_driver.debug_artifact(
        tmp_path,
        "unit-failure",
        {"event": "simulated_failure", "returncode": 1},
    )

    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["event"] == "simulated_failure"
    assert payload["returncode"] == 1
    assert payload["generated_at"]
