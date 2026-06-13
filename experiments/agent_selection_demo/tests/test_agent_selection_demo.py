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
    assert "--timeout 123" in adapter.command_template
    assert "--completion-mode strict-final" in adapter.command_template
    assert adapter.timeout_seconds == 153
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
            "usage_observed": True,
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
            "usage_observed": False,
        },
    ]

    summary = demo.summarize_stage("selection", rows, expected_cells=2)

    assert summary["scoreable_cell_rate"] == 1.0
    assert summary["usage_observed_rate"] == 0.5
    assert summary["verified_solve_rate"] == 0.5
    assert summary["agent_metrics"]["a"]["cost_per_solved_task_usd"] == 0.4
    assert summary["agent_metrics"]["a"]["usage_observed_rate"] == 0.5
    assert summary["agent_metrics"]["a"]["cost_observation_kind"] == "mixed_observed_and_missing_usage_estimate"
    assert summary["agent_metrics"]["a"]["median_latency_seconds"] == 15.0
    assert summary["failure_category_counts"]["hidden verifier failure"] == 1


def test_score_rows_preserve_cost_observation_fields() -> None:
    submissions = [
        {
            "run_id": "run_1",
            "adapter_id": "codex",
            "harness_name": "codex",
            "model_or_agent_name": "gpt-5.4",
            "task_id": "task_1",
            "status": "submitted",
            "latency_seconds": 12.0,
            "patch_sha256": "abc123",
        }
    ]
    verifiers = [{"run_id": "run_1", "status": "verified_pass"}]
    cost_rows = [
        {
            "run_id": "run_1",
            "reviewer_name": "Codex",
            "estimated_cost_usd": 0.25,
            "usage_observed": True,
            "cost_observation_kind": "observed_tokens",
            "usage_source": "adapter_output_usage_json",
            "billed_cost_usd": None,
        }
    ]

    rows = demo.score_rows("selection", submissions, verifiers, cost_rows)

    assert rows[0]["cost_observation_kind"] == "observed_tokens"
    assert rows[0]["usage_source"] == "adapter_output_usage_json"
    assert rows[0]["billed_cost_usd"] is None


def test_normalize_cost_row_backfills_missing_usage_and_billing_metadata() -> None:
    missing_usage = demo.normalize_cost_row({"run_id": "a", "usage_observed": False, "estimated_cost_usd": 0.5})
    billed = demo.normalize_cost_row({"run_id": "b", "usage_observed": True, "estimated_cost_usd": 0.2, "billed_cost_usd": 0.19})

    assert missing_usage["cost_observation_kind"] == "missing_usage_conservative_estimate"
    assert missing_usage["usage_source"] == "missing_adapter_usage"
    assert missing_usage["billed_cost_usd"] is None
    assert billed["cost_observation_kind"] == "billed_cost"
    assert billed["usage_source"] == "provider_billing_export"
    assert billed["billed_cost_usd"] == 0.19


def test_extract_usage_from_kilo_step_finish_events() -> None:
    text = "\n".join(
        [
            '{"type":"step_finish","part":{"tokens":{"input":100,"output":20,"reasoning":5,"cache":{"read":30,"write":0}}}}',
            '{"type":"step_finish","part":{"tokens":{"input":40,"output":10,"reasoning":0,"cache":{"read":60}}}}',
        ]
    )

    usage = demo.extract_usage_from_text(text)

    assert usage == {
        "input_tokens": 230,
        "cached_input_tokens": 90,
        "output_tokens": 35,
        "usage_source_schema": "kilo_step_finish_tokens",
    }


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


def test_top2_repeat_stage_uses_frozen_holdout_tasks() -> None:
    split = {
        "selection_tasks": ["selection_1"],
        "holdout_tasks": ["holdout_1", "holdout_2"],
        "smoke_tasks": ["smoke_1"],
    }

    assert demo.stage_task_ids(split, demo.TOP2_REPEAT_STAGE) == ["holdout_1", "holdout_2"]


def test_top2_repeat_default_agents_are_frozen_pair() -> None:
    config = {
        "agent_candidates": [
            {"agent_id": "codex_gpt_5_4"},
            {"agent_id": "kilo_gpt_5_4"},
            {"agent_id": "kilo_gpt_5_4_mini"},
            {"agent_id": "kilo_claude_sonnet_4_6"},
        ]
    }

    assert demo.selected_agent_ids_for_stage(config, demo.TOP2_REPEAT_STAGE) == demo.TOP2_REPEAT_AGENT_IDS
    assert demo.selected_agent_ids_for_stage(config, "selection") == [
        "codex_gpt_5_4",
        "kilo_gpt_5_4",
        "kilo_gpt_5_4_mini",
        "kilo_claude_sonnet_4_6",
    ]
    assert demo.selected_agent_ids_for_stage(config, demo.TOP2_REPEAT_STAGE, ["kilo_gpt_5_4"]) == ["kilo_gpt_5_4"]


def test_stop_on_unscoreable_guard_only_stops_for_infra_status() -> None:
    assert demo.should_stop_after_cell("acut_harness_error", stop_on_unscoreable=True) is True
    assert demo.should_stop_after_cell("verified_fail", stop_on_unscoreable=True) is False
    assert demo.should_stop_after_cell("acut_harness_error", stop_on_unscoreable=False) is False


def test_recommend_skips_cost_when_usage_coverage_is_inconclusive(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(demo, "RESULTS_REL", tmp_path / "results")
    monkeypatch.setattr(demo, "REPORTS_REL", tmp_path / "reports")
    demo.write_json(
        demo.stage_paths("selection")["metrics"],
        {
            "agent_metrics": {
                "codex": {
                    "reviewer_name": "Codex",
                    "verified_solve_rate": 0.75,
                    "failure_counts": {"hidden verifier failure": 5, "verified pass": 15},
                    "cost_per_solved_task_usd": 0.34,
                    "median_latency_seconds": 100.0,
                    "usage_observed_rate": 1.0,
                },
                "kilo": {
                    "reviewer_name": "Kilo",
                    "verified_solve_rate": 0.75,
                    "failure_counts": {"hidden verifier failure": 5, "verified pass": 15},
                    "cost_per_solved_task_usd": 0.67,
                    "median_latency_seconds": 50.0,
                    "usage_observed_rate": 0.0,
                },
            }
        },
    )

    payload = demo.recommend({"run_policy": {"cost_usage_observed_rate_min": 0.95}})

    assert payload["cost_comparison"]["status"] == "cost_inconclusive_usage_coverage"
    assert payload["primary_quality_recommendation"]["agent_id"] == "kilo"
    assert payload["production_value_status"] == "cost_inconclusive_fallback_to_primary_quality"
    assert payload["recommended_agent_id_for_holdout"] == "kilo"


def test_tuning_feedback_summary_aggregates_sanitized_rows(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(demo, "RESULTS_REL", tmp_path / "results")
    monkeypatch.setattr(demo, "REPORTS_REL", tmp_path / "reports")
    rows = [
        {
            "stage": "selection",
            "agent_id": "codex",
            "reviewer_name": "Codex",
            "harness": "codex",
            "model": "gpt-5.4",
            "task_id": "task_shared",
            "terminal_status": "verified_fail",
            "scoreable_cell": True,
            "verified_pass": False,
            "failure_category": "hidden verifier failure",
            "latency_seconds": 12.0,
            "estimated_cost_usd": 0.2,
            "usage_observed": True,
            "cost_observation_kind": "observed_tokens_estimated_cost",
            "usage_source": "adapter_output_usage_json",
            "billed_cost_usd": None,
            "patch_sha256": "abc",
        },
        {
            "stage": "selection",
            "agent_id": "kilo",
            "reviewer_name": "Kilo",
            "harness": "kilo",
            "model": "gpt-5.4",
            "task_id": "task_shared",
            "terminal_status": "acut_harness_error",
            "scoreable_cell": False,
            "verified_pass": False,
            "failure_category": "exceeded budget or timeout",
            "latency_seconds": 900.0,
            "estimated_cost_usd": 0.5,
            "usage_observed": False,
            "cost_observation_kind": "missing_usage_conservative_estimate",
            "usage_source": "missing_adapter_usage",
            "billed_cost_usd": None,
            "patch_sha256": "def",
        },
    ]
    demo.write_csv(demo.stage_paths("selection")["score"], rows, demo.STAGE_SCORE_FIELDNAMES)
    demo.write_json(
        demo.result_path("top2_repeatability_check.json"),
        {
            "interpretation": "blocked_infrastructure",
            "stability_rows": [
                {
                    "task_id": "task_unstable",
                    "codex_original": "F",
                    "codex_repeat": "P",
                    "codex_changed": True,
                    "kilo_original": "P",
                    "kilo_repeat": "M",
                    "kilo_changed": "",
                    "relationship_repeat": "P/M",
                }
            ],
            "infrastructure_or_policy_rows": [
                {
                    "agent_id": "kilo",
                    "task_id": "task_shared",
                    "terminal_status": "acut_harness_error",
                    "failure_category": "exceeded budget or timeout",
                    "latency_seconds": "900.0",
                }
            ],
        },
    )

    payload = demo.build_tuning_feedback_summary(["selection"])
    rendered = demo.render_tuning_feedback_summary(payload)

    kilo = next(row for row in payload["agent_rows"] if row["agent_id"] == "kilo")
    assert kilo["infra_or_unscoreable_count"] == 1
    assert kilo["usage_observed_rate"] == 0.0
    assert payload["shared_failures"][0]["task_id"] == "task_shared"
    assert payload["unstable_tasks"][0]["task_id"] == "task_unstable"
    assert "不声称任何 Agent 已经经过 tuning" in rendered
    assert "raw prompts" in rendered


def test_predictive_validity_score_join_support_deduplicates_selection_rows() -> None:
    joined = [
        {
            "window_id": "w1",
            "repo": "boltons",
            "adapter_id": "codex_workspace",
            "split": "B_eval",
            "task_id": "task_1",
            "scoreable_cell": True,
            "pass_flag": True,
        },
        {
            "window_id": "w1",
            "repo": "boltons",
            "adapter_id": "codex_workspace",
            "split": "B_eval",
            "task_id": "task_1",
            "scoreable_cell": True,
            "pass_flag": True,
        },
        {
            "window_id": "w1",
            "repo": "boltons",
            "adapter_id": "codex_workspace",
            "split": "H_future",
            "task_id": "task_2",
            "scoreable_cell": False,
            "pass_flag": False,
        },
    ]

    support = demo.deduplicated_scoreable_support(joined)

    b_eval = next(row for row in support if row["stage"] == "B_eval")
    h_future = next(row for row in support if row["stage"] == "H_future")
    assert b_eval["task_count"] == 1
    assert b_eval["scoreable_cells"] == 1
    assert b_eval["pass_count"] == 1
    assert h_future["non_scoreable_cells"] == 1


def test_predictive_validity_metrics_handle_missing_cells_and_mae() -> None:
    rows = [
        {
            "selection_pass_rate": 0.75,
            "future_pass_rate": 0.5,
            "selection_scoreable_count": 4,
            "future_scoreable_count": 4,
            "missing_or_non_scoreable_count": 0,
        },
        {
            "selection_pass_rate": 0.25,
            "future_pass_rate": 0.5,
            "selection_scoreable_count": 4,
            "future_scoreable_count": 4,
            "missing_or_non_scoreable_count": 0,
        },
        {
            "selection_pass_rate": None,
            "future_pass_rate": 0.5,
            "selection_scoreable_count": 0,
            "future_scoreable_count": 4,
            "missing_or_non_scoreable_count": 2,
        },
    ]

    summary = demo.summarize_prediction_rows(rows, threshold=0.2)

    assert summary["slice_count"] == 2
    assert summary["MAE"] == 0.25
    assert summary["RMSE"] == 0.25
    assert summary["mean_signed_error"] == 0.0
    assert summary["catastrophic_miss_rate"] == 1.0
    assert summary["missing_or_non_scoreable_count"] == 2


def test_predictive_validity_baseline_comparison_uses_best_simple_envelope() -> None:
    protocol = {
        "baselines": {
            "simple": ["temporal_recent_baseline", "repo_unweighted_same_budget"],
            "candidate_selectors": ["coverage_constrained_unweighted"],
        }
    }
    summaries = {
        "temporal_recent_baseline": {"MAE": 0.2, "catastrophic_miss_rate": 0.5, "slice_count": 4},
        "repo_unweighted_same_budget": {"MAE": 0.15, "catastrophic_miss_rate": 0.25, "slice_count": 4},
        "coverage_constrained_unweighted": {"MAE": 0.1, "catastrophic_miss_rate": 0.25, "slice_count": 4},
        "completed_blocked_split_supplement": {"MAE": 0.05, "catastrophic_miss_rate": 0.0, "slice_count": 2},
    }

    comparison = demo.baseline_comparison_from_summaries(summaries, protocol)

    assert comparison["best_simple_baseline"]["design_id"] == "repo_unweighted_same_budget"
    assert comparison["best_barcarolle_candidate"]["design_id"] == "coverage_constrained_unweighted"
    assert comparison["candidate_beats_best_simple_baseline"] is True
    assert comparison["candidate_minus_best_simple_MAE"] == -0.05
    assert comparison["best_diagnostic_candidate"]["design_id"] == "completed_blocked_split_supplement"


def test_predictive_validity_recommendation_regret_uses_frozen_recommendation() -> None:
    rows = [
        {
            "window_id": "demo",
            "repo": "boltons",
            "design_id": "demo_selection_set",
            "agent_id": "codex",
            "selection_pass_rate": 0.8,
            "future_pass_rate": 0.2,
            "recommended_agent_id": "codex",
        },
        {
            "window_id": "demo",
            "repo": "boltons",
            "design_id": "demo_selection_set",
            "agent_id": "kilo",
            "selection_pass_rate": 0.7,
            "future_pass_rate": 0.9,
            "recommended_agent_id": "codex",
        },
    ]

    summary = demo.summarize_rank_and_regret(rows)

    assert summary["rank_agreement"]["groups_evaluated"] == 1
    assert summary["rank_agreement"]["top_rank_agreement_rate"] == 0.0
    assert summary["recommendation_regret"]["mean_regret"] == 0.7
    assert summary["recommendation_regret"]["rows"][0]["selection_rule"] == "frozen_recommendation"
