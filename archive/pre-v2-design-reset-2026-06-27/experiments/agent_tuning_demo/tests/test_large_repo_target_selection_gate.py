from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_tuning_demo" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import large_repo_target_selection_gate as gate  # noqa: E402


def test_speed_class_uses_runbook_thresholds() -> None:
    assert gate.speed_class(59) == "ideal_under_60s"
    assert gate.speed_class(179) == "acceptable_under_180s"
    assert gate.speed_class(599) == "risky_180s_to_600s"
    assert gate.speed_class(600) == "avoid_over_600s"
    assert gate.speed_class(10, passed=False) == "environment_failed_or_unusable"


def test_classification_separates_large_heavy_from_balanced_candidate() -> None:
    balanced = {
        "estimated_release_eligible_volume": 120,
        "count_feasible_rolling_origin_windows": 3,
        "expected_evaluation_speed_class": "ideal_under_60s",
        "environment_risk": "low",
    }
    heavy = {
        "estimated_release_eligible_volume": 120,
        "count_feasible_rolling_origin_windows": 3,
        "expected_evaluation_speed_class": "environment_failed_or_unusable",
        "environment_risk": "high_compiled_extension_build",
    }
    fast_small = {
        "estimated_release_eligible_volume": 24,
        "count_feasible_rolling_origin_windows": 1,
        "expected_evaluation_speed_class": "ideal_under_60s",
        "environment_risk": "low",
    }

    assert gate.classify_candidate(balanced) == "balanced_strong_target_prep_candidate"
    assert gate.classify_candidate(heavy) == "large_but_heavy"
    assert gate.classify_candidate(fast_small) == "fast_but_underpowered"


def test_choose_recommendations_prefers_nonbaseline_balanced_target() -> None:
    baseline = {
        "repo_id": "attrs",
        "repo_url": "https://github.com/python-attrs/attrs.git",
        "track": "baseline",
        "checkout_status": "clean",
        "classification": "fast_but_underpowered",
        "expected_evaluation_speed_class": "ideal_under_60s",
        "estimated_release_eligible_volume": 31,
        "projected_certified_task_count_after_bounded_repair": 31,
        "changed_test_oracle_availability_count": 249,
    }
    candidate = {
        "repo_id": "sympy",
        "repo_url": "https://github.com/sympy/sympy.git",
        "track": "large_heavy",
        "checkout_status": "clean",
        "classification": "balanced_target_prep_candidate",
        "expected_evaluation_speed_class": "acceptable_under_180s",
        "estimated_release_eligible_volume": 70,
        "projected_certified_task_count_after_bounded_repair": 90,
        "changed_test_oracle_availability_count": 260,
    }

    primary, backup = gate.choose_recommendations([baseline, candidate])

    assert primary["repo_id"] == "sympy"
    assert backup["repo_id"] == "attrs"


def test_spread_sample_supports_single_sample() -> None:
    rows = [{"task_time": f"2020-01-0{index}T00:00:00Z", "value": index} for index in range(1, 6)]

    sampled = gate.spread_sample(rows, 1)

    assert sampled == [{"task_time": "2020-01-03T00:00:00Z", "value": 3}]


def test_projected_release_count_respects_prior_failed_probe() -> None:
    metrics = {
        "changed_test_oracle_availability_count": 100,
        "bounded_certification_sample": {"sample_size": 24, "pass_count": 24},
        "targeted_verifier_timing": {"pass_count": 1, "speed_class": "ideal_under_60s"},
        "environment_risk": "low",
    }

    assert gate.projected_release_count(metrics, {"prior_probe_attempts": 12, "prior_probe_release_eligible": 0}) == 0


def test_partial_probe_failure_is_not_fast_enough_for_balanced_classification() -> None:
    probes = [
        {"status": "passed", "duration_seconds": 1.0},
        {"status": "failed", "duration_seconds": 2.0},
    ]

    timing = gate.summarize_probe_timings(probes)

    assert timing["speed_class"] == "partial_probe_failure"
    assert gate.smoke_status(probes) == "partial_failed"
    assert (
        gate.classify_candidate(
            {
                "estimated_release_eligible_volume": 120,
                "count_feasible_rolling_origin_windows": 3,
                "expected_evaluation_speed_class": timing["speed_class"],
                "environment_risk": "low",
            }
        )
        == "capacity_promising_but_speed_unproven"
    )
