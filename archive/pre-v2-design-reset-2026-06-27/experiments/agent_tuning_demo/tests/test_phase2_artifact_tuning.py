from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_tuning_demo" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import phase2_artifact_tuning as phase2  # noqa: E402
import tuning_artifacts as artifacts  # noqa: E402


def test_action_artifacts_are_valid_and_distinct() -> None:
    variant_a = phase2.action_artifact("A")
    variant_b = phase2.action_artifact("B")

    artifacts.validate_artifact(variant_a)
    artifacts.validate_artifact(variant_b)
    assert variant_a["hash"] != variant_b["hash"]
    assert phase2.PUBLIC_TEST_COMMAND not in variant_a["files"][0]["content"]
    assert phase2.PUBLIC_TEST_COMMAND in variant_b["files"][0]["content"]


def test_protocol_keeps_holdout_ids_out_of_optimizer_visible_splits() -> None:
    payload = phase2.protocol_payload()

    assert payload["splits"]["selection_dev"] == phase2.SELECTION_DEV_TASKS
    assert "selection_train" in payload["splits"]
    assert payload["splits"]["holdout"]["task_ids_withheld_until_artifact_freeze"] is True
    assert "task_ids" not in payload["splits"]["holdout"]
    assert not set(payload["splits"]["selection_train"]) & set(phase2.SELECTION_DEV_TASKS)


def test_paired_summary_counts_net_wins_and_invalids() -> None:
    rows = [
        {"condition": "baseline", "task_id": "a", "terminal_status": "verified_fail", "scoreable_cell": True, "verified_pass": False, "estimated_cost_usd": "0.1", "latency_seconds": "1", "usage_observed": True},
        {"condition": "tuned", "task_id": "a", "terminal_status": "verified_pass", "scoreable_cell": True, "verified_pass": True, "estimated_cost_usd": "0.1", "latency_seconds": "2", "usage_observed": True},
        {"condition": "baseline", "task_id": "b", "terminal_status": "verified_pass", "scoreable_cell": True, "verified_pass": True, "estimated_cost_usd": "0.1", "latency_seconds": "3", "usage_observed": True},
        {"condition": "tuned", "task_id": "b", "terminal_status": "verified_fail", "scoreable_cell": True, "verified_pass": False, "estimated_cost_usd": "0.1", "latency_seconds": "4", "usage_observed": True},
        {"condition": "baseline", "task_id": "c", "terminal_status": "invalid_output", "scoreable_cell": False, "verified_pass": False, "estimated_cost_usd": "0.1", "latency_seconds": "5", "usage_observed": False},
        {"condition": "tuned", "task_id": "c", "terminal_status": "verified_fail", "scoreable_cell": True, "verified_pass": False, "estimated_cost_usd": "0.1", "latency_seconds": "6", "usage_observed": True},
    ]

    summary = phase2.paired_summary(rows)

    assert summary["paired_net_wins"] == 0
    assert summary["improved_task_ids"] == ["a"]
    assert summary["regressed_task_ids"] == ["b"]
    assert summary["conditions"]["baseline"]["invalid_or_unscoreable_cells"] == 1
    assert summary["conditions"]["tuned"]["invalid_or_unscoreable_cells"] == 0
    assert summary["non_regressing_gate"] is True


def test_artifact_from_text_rejects_holdout_derived_by_default() -> None:
    artifact = phase2.artifact_from_text("hello\n", "unit-candidate", "unit")
    artifacts.validate_artifact(artifact)
    artifact["holdout_derived"] = True
    artifact = artifacts.with_computed_hash(artifact)

    try:
        artifacts.validate_artifact(artifact)
    except artifacts.ArtifactValidationError as exc:
        assert "holdout-derived" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected holdout-derived artifact rejection")
