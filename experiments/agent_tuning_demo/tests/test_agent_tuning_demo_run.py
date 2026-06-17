from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_tuning_demo" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import agent_tuning_demo_run as demo  # noqa: E402


def test_selected_history_benchmark_uses_only_pre_origin_history() -> None:
    rows_by_id = demo.task_rows_by_id("mypy")
    window = demo.selected_window("mypy", "origin_40")

    selected = demo.select_history_benchmark(window, rows_by_id)

    assert len(selected) == demo.SELECTED_SIZE
    assert set(selected).issubset(set(window["history_pool_before_origin"]["task_ids"]))
    assert not set(selected) & set(window["future_holdout_after_origin"]["task_ids"])


def test_preregistration_payload_withholds_future_ids_before_artifact_freeze() -> None:
    payload = demo.protocol_payload()
    window = payload["rolling_origin_window"]

    assert payload["status"] == "frozen_before_new_paid_result_inspection"
    assert window["future_holdout_task_ids_withheld_until_artifact_freeze"] is True
    assert window["future_holdout_task_ids_sha256"].startswith("sha256:")
    assert "future_holdout_task_ids" not in window
    assert set(window["train_feedback_task_ids"]).isdisjoint(window["dev_eval_task_ids"])


def test_package_for_mypy_keeps_test_data_non_editable_scope() -> None:
    row = demo.task_rows_by_id("mypy")["mypy__taskgen__2304"]

    package = demo.package_for(row, "selected_baseline")

    assert package.repo_id == "mypy"
    assert package.allowed_code_paths
    assert "test-data/unit/check-incremental.test" in package.test_paths
    assert all(not path.startswith("test-data/") for path in package.allowed_code_paths)
    assert "Do not edit tests" in package.solver_facing_statement


def test_ledger_row_records_required_cost_fields() -> None:
    row = {
        "run_id": "selected_baseline__baseline__kilo__task",
        "repository": "mypy",
        "origin_id": "origin_40",
        "task_id": "task",
        "candidate_id": "",
        "agent_id": demo.TARGET_AGENT_ID,
        "model": demo.TARGET_MODEL,
        "harness": demo.TARGET_HARNESS,
        "surface": "baseline_no_artifact",
        "endpoint_proof_status": "llm_endpoint_proxy_secret_isolated",
        "input_tokens": 10,
        "cached_input_tokens": 1,
        "output_tokens": 2,
        "usage_source": "adapter_output_usage_json",
        "estimated_cost_usd": 0.01,
        "cost_observation_kind": "observed_tokens_estimated_cost",
        "latency_seconds": 12.3,
        "terminal_status": "verified_pass",
        "result_artifact_path": "experiments/phase0_headroom/results/raw/example/submission.patch",
    }

    ledger = demo.ledger_row_from_score(row)

    assert ledger["call_id"] == row["run_id"]
    assert ledger["call_category"] == "solver Agent"
    assert ledger["repository"] == "mypy"
    assert ledger["observed_or_estimated_usd_cost"] == 0.01
    assert ledger["agent_model_harness_surface"]["surface"] == "baseline_no_artifact"
