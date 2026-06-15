from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_tuning_demo" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import target_repo_selection_gate as gate  # noqa: E402


def test_path_classification_separates_implementation_from_tests() -> None:
    assert gate.is_impl_path("src/pkg/core.py") is True
    assert gate.is_test_path("tests/test_core.py") is True
    assert gate.is_impl_path("tests/test_core.py") is False
    assert gate.is_impl_path("docs/conf.py") is False


def test_simulate_windows_requires_train_dev_and_future_counts() -> None:
    years = [2014] * 10 + [2016] * 6 + [2018] * 10 + [2020] * 6 + [2022] * 10

    windows = gate.simulate_windows(years)

    assert len(windows) >= 2
    assert all(window["train_count"] >= gate.MIN_WINDOW_TRAIN for window in windows)
    assert all(window["dev_count"] >= gate.MIN_WINDOW_DEV for window in windows)
    assert all(window["future_count"] >= gate.MIN_WINDOW_FUTURE for window in windows)


def test_projected_release_count_uses_observed_prior_before_source_projection() -> None:
    metrics = {"release_ready_before_certification_count": 100}

    assert gate.projected_release_count(metrics, {"known_release_eligible": 31}) == 31
    assert gate.projected_release_count(metrics, {"prior_probe_attempts": 10, "prior_probe_release_eligible": 4}) == 40
    assert gate.projected_release_count(metrics, {}) == 35


def test_new_prep_candidate_can_outrank_old_baseline_when_supply_is_stronger() -> None:
    new_repo = {
        "repo_id": "newlib",
        "repo_url": "https://example.invalid/newlib.git",
        "baseline": False,
        "checkout_status": "clean",
        "screen_label": "prep_candidate_certification_needed",
        "current_or_projected_release_eligible_count": 70,
        "release_ready_before_certification_count": 140,
        "verifier_environment_risk": "medium_needs_current_smoke_or_replay_probe",
    }
    old_repo = {
        "repo_id": "click",
        "repo_url": "https://github.com/pallets/click.git",
        "baseline": True,
        "checkout_status": "clean",
        "screen_label": "small_pilot_or_backup",
        "current_or_projected_release_eligible_count": 30,
        "release_ready_before_certification_count": 38,
        "verifier_environment_risk": "low_current_visible_smoke_passed",
    }

    primary, backup = gate.choose_recommendations([old_repo, new_repo])

    assert primary["repo_id"] == "newlib"
    assert backup["repo_id"] == "click"
