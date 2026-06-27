from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_tuning_demo" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import phase2b_rolling_origin_tuning as phase2b  # noqa: E402
import tuning_artifacts as artifacts  # noqa: E402


def test_selected_window_is_time_ordered_and_disjoint() -> None:
    splits = phase2b.selected_window_task_ids()

    assert len(splits["train"]) == 10
    assert len(splits["dev"]) == 6
    assert len(splits["future"]) == 10
    assert not set(splits["train"]) & set(splits["dev"])
    assert not set(splits["train"]) & set(splits["future"])
    assert not set(splits["dev"]) & set(splits["future"])


def test_task_supply_audit_passes_only_single_time_ordered_window() -> None:
    payload = phase2b.task_supply_audit_payload()
    selected = [window for window in payload["candidate_windows"] if window["selected_for_protocol"]]

    assert payload["paid_cells_run"] == 0
    assert payload["readiness_decision"]["paid_tuning_allowed_after_protocol_freeze"] is True
    assert payload["readiness_decision"]["time_ordered_future_validation_feasible"] is True
    assert payload["readiness_decision"]["rolling_origin_multi_window_claim_feasible"] is False
    assert len(selected) == 1
    assert selected[0]["future_task_ids_revealed"] is False
    assert "future_task_ids" not in selected[0]
    assert selected[0]["baseline_headroom"]["dev"]["pass_rate"] <= 0.70
    assert selected[0]["baseline_headroom"]["future"]["pass_rate"] <= 0.70


def test_protocol_withholds_future_ids_before_artifact_freeze(monkeypatch) -> None:
    audit = phase2b.task_supply_audit_payload()

    def fake_read_json(path: Path):
        if path.name == "phase2b_task_supply_headroom_audit.json":
            return audit
        return phase2b.read_json(path)

    monkeypatch.setattr(phase2b, "read_json", fake_read_json)
    protocol = phase2b.phase2b_protocol_payload()
    window = protocol["selected_windows"][0]

    assert window["future_task_ids_withheld_until_artifact_freeze"] is True
    assert window["future_task_ids_sha256"].startswith("sha256:")
    assert "future_task_ids" not in window


def test_llm_candidate_artifact_requires_train_only_evidence() -> None:
    train = {"train_a", "train_b"}
    forbidden = {"dev_a", "future_a"}
    candidate = {
        "artifact_id_suffix": "api-semantics",
        "appendix_markdown": "When changing API behavior, inspect the existing implementation and adjacent public tests before editing. Keep the patch narrow and verify the documented edge cases before final answer.",
        "targeted_failure_labels": ["wrong_api_semantics"],
        "evidence_task_ids": ["train_a"],
        "expected_behavior_change": "More careful API semantics repair.",
        "rollback_plan": "Remove the appendix.",
    }

    artifact = phase2b.artifact_from_llm_candidate(candidate, 1, train, forbidden)

    artifacts.validate_artifact(artifact)
    assert artifact["holdout_derived"] is False
    assert artifact["evidence_task_ids"] == ["train_a"]


def test_llm_candidate_artifact_rejects_dev_or_future_ids() -> None:
    train = {"train_a"}
    forbidden = {"dev_a", "future_a"}
    candidate = {
        "artifact_id_suffix": "bad",
        "appendix_markdown": "This is long enough but mentions future_a, which is not allowed in a train-only candidate artifact.",
        "targeted_failure_labels": ["wrong_api_semantics"],
        "evidence_task_ids": ["train_a"],
        "expected_behavior_change": "Bad.",
        "rollback_plan": "Remove.",
    }

    try:
        phase2b.artifact_from_llm_candidate(candidate, 1, train, forbidden)
    except ValueError as exc:
        assert "non-train task ids" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected dev/future task id rejection")
