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
        "run_policy": {"result_prefix": "test", "adapter_cleanup_grace_seconds": 30},
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


def test_demo_config_generates_doubled_timeout_adapter_commands() -> None:
    config = demo.load_config(demo.ROOT / demo.DEFAULT_CONFIG)
    candidates = [*config["agent_candidates"], config["fallback_candidate"]]

    for candidate in candidates:
        adapter = demo.adapter_config_for(config, candidate)
        assert candidate["timeout_seconds"] == 1800
        assert "--timeout 1800" in adapter.command_template
        assert adapter.timeout_seconds == 1860

    assert config["run_policy"]["adapter_cleanup_grace_seconds"] == 60
    assert config["run_policy"]["endpoint_proxy_upstream_timeout_seconds"] == 3600
    assert demo.run_policy_int(config, "verifier_timeout_seconds", demo.DEFAULT_VERIFIER_TIMEOUT_SECONDS) == 360


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


def test_selector_task_rows_create_deterministic_metadata_fallbacks() -> None:
    split = {
        "selection_tasks": ["task_old"],
        "holdout_tasks": ["task_future"],
        "smoke_tasks": [],
    }
    audit_rows = [
        {
            "task_id": "task_future",
            "source": "canonical_history",
            "task_time": "2023-01-01T00:00:00Z",
            "code_files": ["boltons/timeutils.py"],
            "test_files": ["tests/test_timeutils.py"],
            "gates_pass": True,
            "has_required_fields": True,
            "base_commit_present": True,
            "target_commit_present": True,
        },
        {
            "task_id": "task_old",
            "source": "supply",
            "task_time": "2020-01-01T00:00:00Z",
            "code_files": ["boltons/iterutils.py"],
            "test_files": ["tests/test_iterutils.py"],
            "gates_pass": True,
            "has_required_fields": True,
            "base_commit_present": True,
            "target_commit_present": True,
        },
    ]

    rows = demo.selector_task_rows_from_audit(audit_rows, split, "example/repo")

    old = rows[0]
    future = rows[1]
    assert old["task_id"] == "task_old"
    assert old["stage_role"] == "selection"
    assert old["module_bucket"] == "iterutils"
    assert old["test_bucket"] == "pytest_unit"
    assert old["change_size_proxy"] == "small"
    assert old["quality_score"] == 1.0
    assert "difficulty_bucket" in old["metadata_fallbacks"]
    assert future["stage_role"] == "holdout"
    assert future["is_final_later_task"] is True


def test_selector_visible_task_ids_masks_future_and_holdout_rows() -> None:
    rows = [
        {"task_id": "old_selection", "task_time": "2020-01-01T00:00:00Z", "stage_role": "selection"},
        {"task_id": "future_selection", "task_time": "2021-01-01T00:00:00Z", "stage_role": "selection"},
        {"task_id": "holdout", "task_time": "2020-01-02T00:00:00Z", "stage_role": "holdout"},
    ]

    visible = demo.selector_visible_task_ids(rows, "2020-06-01T00:00:00Z", {"selection"})

    assert visible == ["old_selection"]


def test_selector_outcome_policy_counts_solver_invalid_cells_as_fail() -> None:
    rows = demo.selector_outcome_rows_from_score_tables(
        {
            "selection": [
                {
                    "task_id": "task_1",
                    "agent_id": "agent_a",
                    "terminal_status": "acut_harness_error",
                    "scoreable_cell": "False",
                    "verified_pass": "False",
                    "failure_category": "exceeded budget or timeout",
                },
                {
                    "task_id": "task_2",
                    "agent_id": "agent_a",
                    "terminal_status": "invalid_output",
                    "scoreable_cell": "False",
                    "verified_pass": "False",
                    "failure_category": "no meaningful change",
                },
            ]
        }
    )

    assert [row["policy_valid_cell"] for row in rows] == [True, True]
    assert [row["policy_pass"] for row in rows] == [False, False]
    assert [row["policy_outcome_value"] for row in rows] == [0, 0]


def test_selector_random_selection_is_deterministic_for_fixed_seed() -> None:
    rows = [
        {
            "task_id": f"task_{index}",
            "quality_score": 1.0,
            "risk_flag": False,
            "flaky_flag": False,
        }
        for index in range(6)
    ]

    first = demo.select_uniform_random_same_budget(rows, k=3, seed=7)
    second = demo.select_uniform_random_same_budget(rows, k=3, seed=7)

    assert first == second
    assert len(first) == 3


def test_selector_stratified_random_preserves_source_recency_quota() -> None:
    rows = [
        {
            "task_id": f"a_{index}",
            "source": "a",
            "recency_bucket": "old",
            "module_bucket": f"m{index}",
            "quality_score": 1.0,
            "risk_flag": False,
            "flaky_flag": False,
            "task_time": f"2020-01-{index + 1:02d}T00:00:00Z",
        }
        for index in range(6)
    ] + [
        {
            "task_id": f"b_{index}",
            "source": "b",
            "recency_bucket": "new",
            "module_bucket": f"n{index}",
            "quality_score": 1.0,
            "risk_flag": False,
            "flaky_flag": False,
            "task_time": f"2021-01-{index + 1:02d}T00:00:00Z",
        }
        for index in range(4)
    ]

    selected = demo.select_stratified_random(rows, k=5, seed=11)

    assert sum(task_id.startswith("a_") for task_id in selected) == 3
    assert sum(task_id.startswith("b_") for task_id in selected) == 2


def test_rsq_selects_newest_task_within_each_source_recency_quota() -> None:
    rows = [
        {
            "task_id": "old_a",
            "source": "a",
            "recency_bucket": "legacy",
            "module_bucket": "m1",
            "quality_score": 1.0,
            "risk_flag": False,
            "flaky_flag": False,
            "task_time": "2020-01-01T00:00:00Z",
        },
        {
            "task_id": "new_a",
            "source": "a",
            "recency_bucket": "legacy",
            "module_bucket": "m2",
            "quality_score": 1.0,
            "risk_flag": False,
            "flaky_flag": False,
            "task_time": "2020-02-01T00:00:00Z",
        },
        {
            "task_id": "old_b",
            "source": "b",
            "recency_bucket": "middle",
            "module_bucket": "m3",
            "quality_score": 1.0,
            "risk_flag": False,
            "flaky_flag": False,
            "task_time": "2021-01-01T00:00:00Z",
        },
        {
            "task_id": "new_b",
            "source": "b",
            "recency_bucket": "middle",
            "module_bucket": "m4",
            "quality_score": 1.0,
            "risk_flag": False,
            "flaky_flag": False,
            "task_time": "2021-02-01T00:00:00Z",
        },
    ]

    selected = demo.select_rsq_recency_stratified_quota(rows, k=2)

    assert selected == ["new_a", "new_b"]


def test_hrd_hybrid_reports_representative_and_discriminative_split() -> None:
    rows = [
        {
            "task_id": f"task_{index}",
            "source": "source_a" if index < 6 else "source_b",
            "source_cluster": "source_a:cluster" if index < 6 else "source_b:cluster",
            "recency_bucket": "legacy" if index < 6 else "middle",
            "module_bucket": f"m{index}",
            "change_size_proxy": "medium" if index % 3 == 0 else "small",
            "quality_score": 1.0,
            "risk_flag": False,
            "flaky_flag": False,
            "task_time": f"2020-01-{index + 1:02d}T00:00:00Z",
        }
        for index in range(10)
    ]

    selection = demo.select_hrd_hybrid(rows, k=10, representative_fraction=0.7)

    assert len(selection["selected_task_ids"]) == 10
    assert selection["representative_count"] == 7
    assert selection["discriminative_count"] == 3
    assert selection["disagreement_source"] == "metadata_cluster_density_difficulty_proxy"


def test_hrd_metadata_scores_ignore_outcome_like_future_fields() -> None:
    rows = [
        {
            "task_id": "task_a",
            "source": "source_a",
            "source_cluster": "source_a:cluster",
            "recency_bucket": "legacy",
            "module_bucket": "m1",
            "change_size_proxy": "medium",
            "quality_score": 1.0,
            "risk_flag": False,
            "flaky_flag": False,
            "task_time": "2020-01-01T00:00:00Z",
            "future_pass_rate": 0.0,
        },
        {
            "task_id": "task_b",
            "source": "source_b",
            "source_cluster": "source_b:cluster",
            "recency_bucket": "middle",
            "module_bucket": "m2",
            "change_size_proxy": "small",
            "quality_score": 1.0,
            "risk_flag": False,
            "flaky_flag": False,
            "task_time": "2020-02-01T00:00:00Z",
            "future_pass_rate": 1.0,
        },
    ]
    changed_future = [{**row, "future_pass_rate": 1.0 - row["future_pass_rate"]} for row in rows]

    assert demo.metadata_disagreement_scores(rows) == demo.metadata_disagreement_scores(changed_future)
    assert demo.select_hrd_disagreement_only(rows, k=1)["selected_task_ids"] == demo.select_hrd_disagreement_only(changed_future, k=1)["selected_task_ids"]


def test_corrected_protocol_freezes_phase1_selection_without_score_join() -> None:
    payload = demo.corrected_protocol_payload()

    assert payload["status"] == "frozen_before_final_outcome_join"
    assert payload["final_selector_config"]["selector_id"] == "hrd_v2_70_30"
    assert payload["final_selector_config"]["k_per_repo"] == 6
    assert payload["final_selector_config"]["k_total"] == 18
    assert "phase1_retrospective_predictive_signal_score_join_manifest.json" not in " ".join(
        payload["input_artifacts_allowed_for_selector_scoring"]
    )
    assert any("score_join_manifest" in path for path in payload["outcome_artifacts_withheld_until_package4"])
    assert set(payload["forbidden_selector_score_fields"]).isdisjoint(payload["selector_score_input_fields"])
    assert payload["outcome_blind_audit"]["score_join_manifest_read_by_protocol_command"] is False


def test_corrected_phase1_hrd_selection_ignores_outcome_like_fields() -> None:
    window = demo.corrected_phase1_window()
    rows = demo.corrected_phase1_task_rows_from_window(
        window,
        demo.corrected_phase1_universe_rows(),
        demo.CORRECTED_FINAL_REPOS,
    )
    changed = [
        {
            **row,
            "pass_flag": index % 2 == 0,
            "future_pass_rate": 1.0 if index % 2 == 0 else 0.0,
            "terminal_status": "verified_pass" if index % 2 == 0 else "verified_fail",
        }
        for index, row in enumerate(rows)
    ]

    original = demo.corrected_select_hrd_by_repo(rows, demo.CORRECTED_FINAL_REPOS, 6, 0.7)
    mutated = demo.corrected_select_hrd_by_repo(changed, demo.CORRECTED_FINAL_REPOS, 6, 0.7)

    assert original["selected_task_ids"] == mutated["selected_task_ids"]


def test_bakeoff_feature_leakage_mask_forbids_outcome_fields_for_final() -> None:
    statuses = demo.bakeoff_feature_leakage_status_by_field()

    assert statuses["metadata_informativeness"] == "metadata_only"
    assert statuses["development_outcome_difficulty"] == "development_outcome_only"
    assert statuses["policy_outcome_value"] == "not_allowed_for_final"
    assert "development_outcome_difficulty" in demo.bakeoff_forbidden_final_feature_fields()
    assert "policy_outcome_value" not in demo.bakeoff_final_allowed_feature_fields()
    assert "metadata_informativeness" in demo.bakeoff_final_allowed_feature_fields()


def test_bakeoff_attach_scores_keeps_final_outcome_features_blank() -> None:
    feature_rows = [
        {
            "task_id": "task_1",
            "source_id": demo.BAKEOFF_FINAL_SOURCE_ID,
            "source_cluster": "repo:module",
            "source": "source",
            "change_size_proxy": "medium",
            "recency_bucket": "recent_2023_or_later",
            "development_outcome_difficulty": "",
            "development_outcome_disagreement": "",
            "feature_leakage_notes": "",
        },
        {
            "task_id": "task_2",
            "source_id": "phase1_blocked_split_heldout_development",
            "source_cluster": "repo:module",
            "source": "source",
            "change_size_proxy": "small",
            "recency_bucket": "recent_2023_or_later",
            "development_outcome_difficulty": "",
            "development_outcome_disagreement": "",
            "feature_leakage_notes": "",
        },
    ]
    outcome_rows = [
        {
            "source_id": "phase1_blocked_split_heldout_development",
            "task_id": "task_2",
            "stage": "selection",
            "policy_valid_cell": True,
            "policy_outcome_value": 1,
        },
        {
            "source_id": "phase1_blocked_split_heldout_development",
            "task_id": "task_2",
            "stage": "selection",
            "policy_valid_cell": True,
            "policy_outcome_value": 0,
        },
    ]

    rows = demo.bakeoff_attach_scores(feature_rows, outcome_rows)
    final = next(row for row in rows if row["source_id"] == demo.BAKEOFF_FINAL_SOURCE_ID)
    development = next(row for row in rows if row["source_id"] != demo.BAKEOFF_FINAL_SOURCE_ID)

    assert final["development_outcome_difficulty"] == ""
    assert final["development_outcome_disagreement"] == ""
    assert development["development_outcome_difficulty"] == 0.5
    assert development["development_outcome_disagreement"] == 1.0


def bakeoff_selector_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for repo in ["attrs", "boltons"]:
        for index in range(6):
            rows.append(
                {
                    "task_id": f"{repo}_task_{index}",
                    "repo": repo,
                    "stage_role": "selection",
                    "quality_score": 1.0,
                    "risk_flag": False,
                    "flaky_flag": False,
                    "source": "source_a" if index < 3 else "source_b",
                    "source_cluster": f"{repo}:m{index % 3}",
                    "module_bucket": f"m{index % 3}",
                    "path_bucket": repo,
                    "test_bucket": "pytest_unit",
                    "change_size_proxy": "medium" if index % 2 == 0 else "small",
                    "difficulty_bucket": "medium" if index % 2 == 0 else "small",
                    "recency_bucket": "recent_2023_or_later" if index >= 3 else "middle_2019_2022",
                    "task_time": f"2024-01-{index + 1:02d}T00:00:00Z",
                    "historical_difficulty": 0.5 if index % 2 == 0 else 0.25,
                    "metadata_informativeness": float(index) / 10.0,
                }
            )
    return rows


def bakeoff_selector_outcome_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    outcome_rows: list[dict[str, object]] = []
    for row in rows:
        index = int(str(row["task_id"]).rsplit("_", 1)[1])
        for agent_id, passed in {
            "codex_workspace": index % 3 == 0,
            "kilo_workspace": index % 2 == 0,
        }.items():
            outcome_rows.append(
                {
                    "stage": "selection",
                    "task_id": row["task_id"],
                    "agent_id": agent_id,
                    "terminal_status": "verified_pass" if passed else "verified_fail",
                    "policy_valid_cell": True,
                    "policy_outcome_value": 1 if passed else 0,
                }
            )
    return outcome_rows


def test_bakeoff_rsq_v2_is_deterministic() -> None:
    rows = bakeoff_selector_rows()

    first = demo.select_bakeoff_rsq_v2(rows, k=4)
    second = demo.select_bakeoff_rsq_v2(rows, k=4)

    assert first["selected_task_ids"] == second["selected_task_ids"]
    assert len(first["selected_task_ids"]) == 4
    assert all(item["reason"] for item in first["rationale"])


def test_bakeoff_flc_is_deterministic() -> None:
    rows = bakeoff_selector_rows()

    first = demo.select_bakeoff_flc(rows, k=4)
    second = demo.select_bakeoff_flc(rows, k=4)

    assert first["selected_task_ids"] == second["selected_task_ids"]
    assert len(first["rationale"]) == 4


def test_bakeoff_hrd_v3_uses_metadata_informativeness_name() -> None:
    rows = bakeoff_selector_rows()

    selection = demo.select_bakeoff_hrd_v3(rows, k=5, representative_fraction=0.6)

    assert selection["selected_count"] == 5
    assert selection["informativeness_source"] == "metadata_informativeness"
    assert selection["leakage_safe_historical_agent_disagreement_used"] is False


def test_bakeoff_cod_lite_reports_contrast_gain() -> None:
    rows = bakeoff_selector_rows()

    selection = demo.select_bakeoff_cod_lite(rows, k=4)

    assert selection["selected_count"] == 4
    assert all("contrast_gain" in item for item in selection["rationale"])


def test_bakeoff_ro_lsp_is_deterministic_for_fixed_weights() -> None:
    rows = bakeoff_selector_rows()

    first = demo.select_bakeoff_ro_lsp(rows, k=4)
    second = demo.select_bakeoff_ro_lsp(rows, k=4)

    assert first["selected_task_ids"] == second["selected_task_ids"]
    assert first["weights"] == demo.RO_LSP_DEFAULT_WEIGHTS


def test_bakeoff_saes_lite_records_sequential_trace() -> None:
    rows = bakeoff_selector_rows()
    outcomes = bakeoff_selector_outcome_rows(rows)

    selection = demo.select_bakeoff_saes_lite(rows, k=5, outcome_rows=outcomes, agent_ids=demo.BAKEOFF_AGENT_IDS)

    assert selection["selected_count"] == 5
    assert [step["step"] for step in selection["sequential_trace"]] == [
        "representative_seed_batch",
        "observe_seed_outcomes",
        "informative_second_batch",
    ]


def test_bakeoff_strong_random_is_deterministic_for_fixed_seed() -> None:
    rows = bakeoff_selector_rows()

    first = demo.select_bakeoff_strong_random(rows, k=5, seed=19, baseline_id="module_stratified_random")
    second = demo.select_bakeoff_strong_random(rows, k=5, seed=19, baseline_id="module_stratified_random")

    assert first["selected_task_ids"] == second["selected_task_ids"]


def selector_test_outcome_rows(agent_values: dict[str, list[int]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for agent_id, values in agent_values.items():
        for index, value in enumerate(values):
            rows.append(
                {
                    "stage": "selection",
                    "task_id": f"task_{index}",
                    "agent_id": agent_id,
                    "terminal_status": "verified_pass" if value else "verified_fail",
                    "policy_valid_cell": "True",
                    "policy_outcome_value": str(value),
                }
            )
    return rows


def test_decision_wrapper_recommends_when_top_agent_has_pass_rate_advantage() -> None:
    outcomes = selector_test_outcome_rows(
        {
            "agent_a": [1] * 10,
            "agent_b": [1] * 8 + [0, 0],
        }
    )

    decision = demo.decision_wrapper_for_selection(
        [f"task_{index}" for index in range(10)],
        ["agent_a", "agent_b"],
        outcomes,
        {"action_margin": 0.05, "min_common_valid_selected_tasks": 8, "bootstrap_iterations": 100, "confidence_level": 0.8},
    )

    assert decision["state"] == "recommend"
    assert decision["recommended_agent_id"] == "agent_a"
    assert decision["selection_recommendation"]["type"] == "recommend"
    assert decision["agent_rankings"][0]["agent_id"] == "agent_a"


def test_decision_wrapper_returns_top_tier_for_close_agents() -> None:
    outcomes = selector_test_outcome_rows(
        {
            "agent_a": [1] * 8 + [0, 0],
            "agent_b": [1] * 8 + [0, 0],
        }
    )

    decision = demo.decision_wrapper_for_selection(
        [f"task_{index}" for index in range(10)],
        ["agent_a", "agent_b"],
        outcomes,
        {"action_margin": 0.05, "min_common_valid_selected_tasks": 8, "bootstrap_iterations": 100, "confidence_level": 0.8},
    )

    assert decision["state"] == "top_tier"
    assert decision["recommended_agent_id"] is None
    assert decision["top_tier_agent_ids"] == ["agent_a", "agent_b"]
    assert "成本、速度、稳定性" in decision["selection_recommendation"]["guidance"]


def test_decision_wrapper_returns_insufficient_data_when_common_valid_is_low() -> None:
    outcomes = selector_test_outcome_rows(
        {
            "agent_a": [1, 1, 1, 1],
            "agent_b": [1, 0, 0, 0],
        }
    )

    decision = demo.decision_wrapper_for_selection(
        [f"task_{index}" for index in range(4)],
        ["agent_a", "agent_b"],
        outcomes,
        {"action_margin": 0.05, "min_common_valid_selected_tasks": 8, "bootstrap_iterations": 100, "confidence_level": 0.8},
    )

    assert decision["state"] == "insufficient_data"
    assert decision["reason"] == "insufficient_common_valid_selected_tasks"


def test_decision_wrapper_returns_insufficient_data_for_infrastructure_failure() -> None:
    outcomes = selector_test_outcome_rows(
        {
            "agent_a": [1] * 10,
            "agent_b": [1] * 8 + [0, 0],
        }
    )
    outcomes[0] = {
        **outcomes[0],
        "terminal_status": "harness_error",
        "policy_valid_cell": "False",
        "policy_outcome_value": "",
    }

    decision = demo.decision_wrapper_for_selection(
        [f"task_{index}" for index in range(10)],
        ["agent_a", "agent_b"],
        outcomes,
        {"action_margin": 0.05, "min_common_valid_selected_tasks": 8, "bootstrap_iterations": 100, "confidence_level": 0.8},
    )

    assert decision["state"] == "insufficient_data"
    assert decision["reason"] == "infrastructure_failure_in_selection_cells"


def test_decision_wrapper_v2_recommends_nine_of_ten_over_eight_of_ten_at_margin_boundary() -> None:
    outcomes = selector_test_outcome_rows(
        {
            "agent_a": [1] * 9 + [0],
            "agent_b": [1] * 8 + [0, 0],
        }
    )

    decision = demo.decision_wrapper_v2_for_selection(
        [f"task_{index}" for index in range(10)],
        ["agent_a", "agent_b"],
        outcomes,
        {
            "action_margin": 0.1,
            "min_common_valid": 8,
            "lcb_tolerance": 0.1,
            "tie_epsilon": 0.05,
            "bootstrap_iterations": 100,
            "confidence_level": 0.8,
        },
    )

    assert decision["state"] == "recommend"
    assert decision["recommended_agent_id"] == "agent_a"
    assert decision["selected_top_margin"] == 0.1


def test_decision_wrapper_v2_recommends_with_one_discordant_loss_but_overall_win() -> None:
    outcomes = selector_test_outcome_rows(
        {
            "agent_a": [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1],
            "agent_b": [0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1],
        }
    )

    decision = demo.decision_wrapper_v2_for_selection(
        [f"task_{index}" for index in range(12)],
        ["agent_a", "agent_b"],
        outcomes,
        {
            "action_margin": 0.05,
            "min_common_valid": 8,
            "lcb_tolerance": 0.1,
            "tie_epsilon": 0.05,
            "bootstrap_iterations": 100,
            "confidence_level": 0.8,
        },
    )

    assert decision["state"] == "recommend"
    assert decision["recommended_agent_id"] == "agent_a"
    assert decision["pair_stats"][0]["losses"] == 1


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
