from __future__ import annotations

from collections import Counter
from itertools import combinations
import json
from pathlib import Path
import random
import sys
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import TaskRecord, canonical_digest, canonical_json  # noqa: E402
from examples.offline_selector_study import landscape  # noqa: E402
from examples.offline_selector_study import public_replay  # noqa: E402
from examples.offline_selector_study import study  # noqa: E402


def test_offline_study_amendments_form_a_zero_call_chain() -> None:
    plan = study.load_plan()
    amendment = study.load_amendment(study.DEFAULT_AMENDMENT, plan)
    correction = study.load_correction(
        study.DEFAULT_CORRECTION,
        plan,
        amendment,
    )
    replay_amendment = public_replay.load_replay_amendment(
        public_replay.DEFAULT_AMENDMENT,
        plan,
        correction,
    )

    assert plan["authority"]["new_paid_calls"] == 0
    assert amendment["claim_boundary"]["primary_terminal_state"].startswith(
        "invalid_or_insufficient_evidence"
    )
    assert (
        correction["previous_amendment_digest"]
        == amendment["amendment_digest"]
    )
    assert replay_amendment["previous_amendment_digest"] == (
        correction["amendment_digest"]
    )
    assert replay_amendment["authority"]["new_paid_calls"] == 0
    assert replay_amendment["authority"]["network_calls"] == 0


def test_chronological_blocks_keep_future_tasks_nonoverlapping() -> None:
    tasks = tuple(_task(index, "common") for index in range(7))

    blocks = study.chronological_blocks(
        tasks,
        initial_history_count=3,
        future_block_count=2,
    )

    assert tuple(len(history) for history, _ in blocks) == (3, 5)
    assert tuple(
        tuple(task.task_id for task in future) for _, future in blocks
    ) == (("task-3", "task-4"), ("task-5", "task-6"))


def test_coverage_selection_round_robins_declared_strata() -> None:
    tasks = (
        _task(0, "a"),
        _task(1, "a"),
        _task(2, "b"),
        _task(3, "b"),
        _task(4, "c"),
        _task(5, "c"),
    )

    selection = study.select_tasks(
        study.SelectorSpec("coverage", "coverage", {}),
        tasks,
        5,
    )

    assert selection.task_ids == (
        "task-0",
        "task-2",
        "task-4",
        "task-1",
        "task-3",
    )
    assert set(selection.weights.values()) == {1.0}


def test_stratified_selection_uses_trailing_mix_without_cap_activation() -> None:
    tasks = (
        _task(0, "a"),
        _task(1, "a"),
        _task(2, "a"),
        _task(3, "a"),
        _task(4, "b"),
        _task(5, "b"),
    )
    spec = study.SelectorSpec(
        "stratified",
        "stratified_forecast",
        {
            "alpha": 1.0,
            "trailing_ref_count": 4,
            "seed": 5,
            "weight_cap": 3.0,
        },
    )

    selection = study.select_tasks(spec, tasks, 4)

    assert selection.diagnostics["quota_by_stratum"] == {"a": 2, "b": 2}
    assert selection.diagnostics["capped_selected_fraction"] == 0.0
    assert set(selection.weights.values()) == {1.0}


def test_committed_offline_results_are_self_digested_and_non_core() -> None:
    results = json.loads(study.DEFAULT_RESULTS.read_text(encoding="utf-8"))
    digest = results.pop("study_results_digest")

    assert canonical_digest(results) == digest
    assert results["claim"]["core_rolling_origin"] == (
        "invalid_or_insufficient_evidence"
    )
    assert results["audit"]["per_task_outcomes_persisted"] is False
    assert results["authority"] == {"network_calls": 0, "new_paid_calls": 0}


def test_local_source_reproduces_committed_offline_results() -> None:
    if not study.DEFAULT_TASK_POOL.exists():
        pytest.skip("ignored source artifacts are not present")

    observed = study.run_study()
    committed = json.loads(study.DEFAULT_RESULTS.read_text(encoding="utf-8"))

    assert observed["study_results_digest"] == committed["study_results_digest"]


def test_committed_public_replay_results_are_self_digested() -> None:
    results = json.loads(
        public_replay.DEFAULT_OUTPUT.read_text(encoding="utf-8")
    )
    digest = results.pop("public_replay_results_digest")

    assert canonical_digest(results) == digest
    assert results["status"] == "public_counterfactual_replay_changes_algorithm_results"
    assert results["observed_at_negative_control"][
        "all_history_mature_counts_zero"
    ]
    assert results["observed_at_negative_control"][
        "all_future_mature_counts_zero"
    ]
    assert results["result_reuse_audit"][
        "exact_task_check_agent_cache_identity_match_count"
    ] == 150
    assert results["public_pipeline"]["origin_count"] == 12
    assert results["public_pipeline"]["selection_count"] == 72
    assert results["public_pipeline"]["result_matrix_count"] == 144
    assert results["transparent_diagnostic_comparison"][
        "selection_membership_mismatch_count"
    ] == 1


def test_local_source_reproduces_committed_public_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not study.DEFAULT_TASK_POOL.exists():
        pytest.skip("ignored source artifacts are not present")

    selection_count = 0
    original_select = public_replay.select_with_selector
    original_load_outcomes = public_replay.load_outcomes

    def tracked_select(*args: Any, **kwargs: Any) -> Any:
        nonlocal selection_count
        selection_count += 1
        return original_select(*args, **kwargs)

    def guarded_load_outcomes(*args: Any, **kwargs: Any) -> Any:
        assert selection_count == 72
        return original_load_outcomes(*args, **kwargs)

    monkeypatch.setattr(public_replay, "select_with_selector", tracked_select)
    monkeypatch.setattr(public_replay, "load_outcomes", guarded_load_outcomes)
    observed = public_replay.run_public_replay()
    committed = json.loads(
        public_replay.DEFAULT_OUTPUT.read_text(encoding="utf-8")
    )

    assert selection_count == 72
    assert observed["public_replay_results_digest"] == (
        committed["public_replay_results_digest"]
    )


def test_exact_random_loss_pmf_matches_small_exhaustive_space() -> None:
    history = ((0, 0), (0, 1), (1, 0), (1, 1))

    observed = landscape.exact_random_loss_pmf(
        history,
        (0.5, 0.5),
        selection_budget=2,
    )

    assert sum(observed.values()) == pytest.approx(1.0)
    assert observed == pytest.approx({0.0: 2 / 6, 0.25: 4 / 6})


def test_exact_random_loss_pmf_matches_deterministic_exhaustive_cases() -> None:
    rng = random.Random(20_260_727)

    for task_count in range(3, 9):
        for _ in range(8):
            history = tuple(
                (rng.randrange(2), rng.randrange(2)) for _ in range(task_count)
            )
            budget = rng.randrange(1, task_count + 1)
            future_rates = (rng.randrange(6) / 5.0, rng.randrange(6) / 5.0)
            exhaustive: Counter[float] = Counter()
            subsets = tuple(combinations(history, budget))
            for subset in subsets:
                selected_rates = (
                    sum(outcome[0] for outcome in subset) / budget,
                    sum(outcome[1] for outcome in subset) / budget,
                )
                loss = round(
                    (
                        abs(selected_rates[0] - future_rates[0])
                        + abs(selected_rates[1] - future_rates[1])
                    )
                    / 2.0,
                    12,
                )
                exhaustive[loss] += 1

            observed = landscape.exact_random_loss_pmf(
                history,
                future_rates,
                budget,
            )

            expected = {
                loss: count / len(subsets) for loss, count in exhaustive.items()
            }
            assert observed == pytest.approx(expected)


def test_density_frontier_improves_with_more_random_draws() -> None:
    pmf = {0.1: 0.1, 0.2: 0.4, 0.4: 0.5}

    best_of_one = landscape.expected_best_of(pmf, 1)
    best_of_ten = landscape.expected_best_of(pmf, 10)

    assert best_of_one == pytest.approx(0.29)
    assert best_of_ten < best_of_one
    assert landscape.elite_mean(pmf, 0.1) == pytest.approx(0.1)


def test_continuous_support_loss_separates_support_from_budget() -> None:
    full_square = ((0, 0), (0, 1), (1, 0), (1, 1))
    diagonal = ((0, 0), (1, 1))

    assert landscape.continuous_support_loss(full_square, (0.2, 0.8)) == 0.0
    assert landscape.continuous_support_loss(diagonal, (0.2, 0.8)) == (
        pytest.approx(0.3)
    )


def test_selection_landscape_plan_is_self_digested() -> None:
    plan = landscape.load_landscape_plan()
    amendment = landscape.load_landscape_amendment(
        landscape.DEFAULT_AMENDMENT,
        plan,
    )

    assert plan["epistemic_status"] == "post_outcome_development"
    assert plan["research_contract"]["primary_baseline"] == (
        "all eligible historical Task and Check refs without Selection"
    )
    assert plan["resources"]["new_coding_agent_calls"] == 0
    assert amendment["correction"]["corrected_terminal_state"] == (
        "selection_landscape_measured_but_no_candidate_clears_promotion_gate"
    )
    assert amendment["authority"]["new_coding_agent_calls"] == 0


def test_committed_selection_landscape_is_self_digested() -> None:
    results = json.loads(landscape.DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    digest = results.pop("landscape_results_digest")

    assert canonical_digest(results) == digest
    assert results["authority"]["new_coding_agent_calls"] == 0
    assert results["authority"]["local_repeat_noise_views"] == 5_000
    assert results["status"] == (
        "selection_landscape_measured_but_no_candidate_clears_promotion_gate"
    )
    assert results["decision"]["promotion_allowed"] is False
    assert results["baseline"]["coverage_minus_full_history"][
        "macro_origin_mae_difference"
    ] == pytest.approx(-0.009956432456432449)
    planning = results["baseline"]["coverage_minus_full_history"][
        "prospective_planning"
    ]
    assert planning["origins_for_80_percent_power_at_practical_effect"] == 44
    assert planning["origins_for_80_percent_power_at_observed_effect"] == 178
    for agent_result in results["baseline"]["per_agent"].values():
        difference = agent_result["coverage_minus_full_history"][
            "macro_origin_mae_difference"
        ]
        assert -0.02 < difference < 0.0
    semantic_alignment = results["candidate_families"]["semantic_alignment_diagnostic"][
        "baseline_mean_future_centroid_cosine_distance"
    ]
    semantic_best = results["candidate_families"]["semantic_coreset"][0]
    assert (
        semantic_best["semantic_future_centroid_cosine_distance"]
        < semantic_alignment["coverage"]
    )
    assert (
        semantic_best["macro_origin_mae"]
        > results["baseline"]["coverage"]["macro_origin_mae"]
    )
    semantic_outcome = results["candidate_families"]["semantic_outcome_forecast"]
    assert semantic_outcome["status"] == "post_plan_exploratory_mechanism_probe"
    assert semantic_outcome["candidates"][0]["macro_origin_mae"] == pytest.approx(
        0.1875
    )
    fixed_seed = results["random_selection_landscape"]["fixed_seed_policy_sensitivity"]
    assert fixed_seed["seed_range"]["count"] == 100_000
    assert (
        abs(
            fixed_seed["difference_from_independent_exact"][
                "as_good_or_better_fraction"
            ]
        )
        < 0.001
    )
    oracle_density = results["random_selection_landscape"]["oracle_density"]
    assert oracle_density["discrete_oracle_macro_origin_mae"] == pytest.approx(
        0.0375
    )
    assert oracle_density["exact_oracle_probability"] < 1e-20
    density = oracle_density["probability_within_excess_mae"]
    assert density["0.02"] < density["0.05"] < density["0.1"] < 0.01
    origin_positions = results["random_selection_landscape"]["origin_rows"]
    assert sum(
        row["coverage_midrank_fraction_beats"] > 0.5 for row in origin_positions
    ) == 8
    assert tuple(
        row["origin_number"]
        for row in origin_positions
        if row["coverage_midrank_fraction_beats"] < 0.5
    ) == (6, 7, 8, 9)
    robustness = results["robustness"]
    block_rows = robustness["future_block_size"]["configurations"]
    assert block_rows["3"]["coverage_minus_full_history"][
        "macro_origin_mae_difference"
    ] > 0.0
    assert block_rows["4"]["coverage_minus_full_history"][
        "macro_origin_mae_difference"
    ] > 0.0
    assert all(
        not row["point_gate_cleared"] and not row["interval_gate_cleared"]
        for row in block_rows.values()
    )
    dependency = robustness["dependency_first_task_per_cluster"]
    assert dependency["cluster_recurrence"] == 0
    assert dependency["coverage_minus_full_history"][
        "macro_origin_mae_difference"
    ] == pytest.approx(-0.016697109156317218)
    assert not dependency["point_gate_cleared"]
    assert not dependency["interval_gate_cleared"]
    repeat_noise = robustness["repeat_noise"]
    repeat_contrast = repeat_noise["coverage_minus_full_history"]
    assert repeat_noise["replicated_task_count"] == 22
    assert repeat_noise["replicated_agent_task_count"] == 44
    assert repeat_contrast["mean"] == pytest.approx(-0.007087503020128019)
    assert repeat_contrast["fraction_below_zero"] == pytest.approx(0.883)
    assert repeat_contrast["fraction_at_most_minus_0_02"] == 0.0
    assert repeat_contrast["upper_97_5_percentile"] > 0.0
    nulls = results["null_controls"]
    assert "(b + 1) / (B + 1)" in nulls["p_value_rule"]
    assert nulls["unrestricted_outcome_permutation"][
        "coverage_minus_full_history"
    ]["one_sided_probability_at_most_observed"] == pytest.approx(
        1834 / 10001
    )


def test_local_source_reproduces_selection_landscape_outcome_sections() -> None:
    if (
        not study.DEFAULT_TASK_POOL.exists()
        or not landscape.DEFAULT_EMBEDDINGS.exists()
    ):
        pytest.skip("ignored source or embedding artifacts are not present")

    observed = landscape.run_landscape(null_resamples=50)
    normalized_observed = json.loads(canonical_json(observed))
    committed = json.loads(landscape.DEFAULT_OUTPUT.read_text(encoding="utf-8"))

    for section in (
        "baseline",
        "random_selection_landscape",
        "support",
        "robustness",
        "candidate_families",
        "decision",
    ):
        assert normalized_observed[section] == committed[section]


def _task(index: int, stratum: str) -> TaskRecord:
    timestamp = f"2020-01-{index + 1:02d}T00:00:00Z"
    return TaskRecord(
        task_id=f"task-{index}",
        repository_id="example/repository",
        base_commit=f"base-{index}",
        source_family="fixture",
        source_ref=f"source-{index}",
        source_resolved_at=timestamp,
        task_material_available_at=timestamp,
        task_text=f"Task {index}",
        solver_material_digest=f"solver-{index}",
        solver_material_refs=(),
        check_ids=(f"check-{index}",),
        dependency_cluster_id=f"cluster-{index}",
        sampling_stratum=stratum,
    )
