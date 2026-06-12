from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_selection_demo" / "tools"
PHASE0_TOOLS = ROOT / "experiments" / "phase0_headroom" / "tools"
for path in [TOOLS, PHASE0_TOOLS]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import agent_selection_demo as demo  # noqa: E402
import workspace_acut_run as workspace  # noqa: E402


def test_split_counts_uses_minimum_when_pool_below_preferred() -> None:
    policy = {
        "minimum_selection_count": 20,
        "minimum_holdout_count": 10,
        "preferred_pool_size": 45,
        "preferred_selection_count": 30,
        "preferred_holdout_count": 15,
        "stronger_pool_size": 60,
        "stronger_selection_count": 40,
        "stronger_holdout_count": 20,
    }

    assert demo.split_counts(35, policy) == (20, 10)


def test_adapter_config_uses_candidate_model_and_proxy_proof() -> None:
    config = {
        "run_policy": {"result_prefix": "test"},
    }
    candidate = {
        "agent_id": "kilo_claude_sonnet_4_6",
        "harness": "kilo",
        "model": "claude-sonnet-4-6",
        "adapter_script": "experiments/phase0_headroom/tools/kilo_workspace_adapter.py",
        "timeout_seconds": 123,
        "completion_mode": "strict-final",
    }

    adapter = demo.adapter_config_for(config, candidate)

    assert adapter.adapter_id == "kilo_claude_sonnet_4_6"
    assert adapter.model_or_agent_name == "claude-sonnet-4-6"
    assert "--model claude-sonnet-4-6" in adapter.command_template
    assert "--completion-mode strict-final" in adapter.command_template
    assert adapter.endpoint_proof_status == "llm_endpoint_proxy_secret_isolated"


def test_summarize_stage_computes_cost_latency_and_failures() -> None:
    rows = [
        {
            "agent_id": "a",
            "reviewer_name": "Agent A",
            "harness": "codex",
            "model": "gpt-5.4",
            "scoreable_cell": True,
            "verified_pass": True,
            "estimated_cost_usd": 0.2,
            "latency_seconds": 10.0,
            "failure_category": "verified pass",
        },
        {
            "agent_id": "a",
            "reviewer_name": "Agent A",
            "harness": "codex",
            "model": "gpt-5.4",
            "scoreable_cell": True,
            "verified_pass": False,
            "estimated_cost_usd": 0.2,
            "latency_seconds": 20.0,
            "failure_category": "hidden verifier failure",
        },
    ]

    summary = demo.summarize_stage("selection", rows, expected_cells=2)

    assert summary["scoreable_cell_rate"] == 1.0
    assert summary["verified_solve_rate"] == 0.5
    assert summary["agent_metrics"]["a"]["cost_per_solved_task_usd"] == 0.4
    assert summary["agent_metrics"]["a"]["median_latency_seconds"] == 15.0
    assert summary["failure_category_counts"]["hidden verifier failure"] == 1


def test_failure_category_maps_policy_and_empty_diff() -> None:
    assert demo.failure_category({"status": "invalid_output"}, {}) == "no meaningful change"
    assert demo.failure_category({"status": "policy_violation", "harness_error": "submission_edited_tests"}, {}) == "edited tests when prohibited"
    assert demo.failure_category({"status": "harness_error", "harness_error": "captured_patch_did_not_apply"}, {}) == "patch did not apply"


def test_freeze_split_uses_unused_task_for_smoke(tmp_path: Path) -> None:
    packages = [
        workspace.TaskPackage(
            task_id=f"task_{index:02d}",
            repo_id="repo",
            split="",
            source_repo=tmp_path,
            base_commit="base",
            target_commit="target",
            solver_facing_statement="statement",
            verifier_command=["true"],
            metadata={"task_time": f"2020-01-{index + 1:02d}"},
        )
        for index in range(31)
    ]
    config = {
        "target_repo": {"repo_name": "example/repo"},
        "split_policy": {
            "minimum_selection_count": 20,
            "minimum_holdout_count": 10,
            "preferred_pool_size": 45,
            "preferred_selection_count": 30,
            "preferred_holdout_count": 15,
            "stronger_pool_size": 60,
            "stronger_selection_count": 40,
            "stronger_holdout_count": 20,
            "smoke_task_count": 1,
        },
    }

    split = demo.freeze_split(packages, config)

    assert len(split["selection_tasks"]) == 20
    assert len(split["holdout_tasks"]) == 10
    assert split["smoke_tasks"] == ["task_30"]
