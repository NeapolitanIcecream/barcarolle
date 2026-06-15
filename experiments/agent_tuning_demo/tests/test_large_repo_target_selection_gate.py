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
