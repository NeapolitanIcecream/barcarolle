from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_tuning_demo" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import sphinx_target_prep as prep  # noqa: E402


def test_uv_pytest_command_stays_outside_barcarolle_project() -> None:
    profile = {
        "python_version": "3.14",
        "exclude_newer_date": "2026-06-17",
        "dependency_constraints": [".", "pytest>=9,<10"],
    }

    command = prep.uv_pytest_command(profile, ["tests/test_util/test_util.py"])

    assert command[:4] == ["uv", "run", "--no-project", "--isolated"]
    assert "--project" not in command
    assert command[-2:] == ["tests/test_util/test_util.py", "-q"]


def test_command_shape_redacts_targeted_test_paths() -> None:
    command = [
        "uv",
        "run",
        "--no-project",
        "--with",
        ".",
        "--",
        "python",
        "-m",
        "pytest",
        "tests/test_a.py",
        "tests/test_b.py",
        "-q",
    ]

    shaped = prep.command_shape(command)

    assert shaped.count("<targeted_test_paths>") == 1
    assert "tests/test_a.py" not in shaped
    assert "tests/test_b.py" not in shaped


def test_classify_speed_uses_target_prep_thresholds() -> None:
    assert prep.classify_speed([]) == "not_measured"
    assert prep.classify_speed([{"status": "passed", "duration_seconds": 59.9}]) == "ideal_under_60s"
    assert prep.classify_speed([{"status": "passed", "duration_seconds": 179.9}]) == "acceptable_under_180s"
    assert prep.classify_speed([{"status": "passed", "duration_seconds": 599.9}]) == "risky_180s_to_600s"
    assert prep.classify_speed([{"status": "passed", "duration_seconds": 600}]) == "unusable_over_600s"
    assert prep.classify_speed([{"status": "failed", "duration_seconds": 1.0}]) == "risky_or_unusable_partial_failure"


def test_setup_report_escapes_backticks_in_subject() -> None:
    payload = {
        "generated_at": "2026-06-17T00:00:00+00:00",
        "smoke_results": [],
        "smoke_pass_count": 0,
        "smoke_count": 0,
        "targeted_verifier_time_class": "not_measured",
        "repo_id": "sphinx",
        "local_checkout": "experiments/phase0_headroom/external_repos/sphinx",
        "head_commit": "a" * 40,
        "head_time": "2026-06-17T00:00:00+00:00",
        "head_subject": "Document `graphviz` requirement",
    }

    report = prep.setup_smoke_report(payload)

    assert "Document 'graphviz' requirement" in report
