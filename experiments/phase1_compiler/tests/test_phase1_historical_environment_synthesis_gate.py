from __future__ import annotations

from pathlib import Path

import phase1_historical_environment_synthesis_gate as gate


def profile(**overrides: object) -> gate.EnvironmentProfile:
    values = {
        "profile_id": "py39_pytest_lt5_pythonpath",
        "python_version": "3.9",
        "dependency_constraints": ("pytest<5", "setuptools<58"),
        "exclude_newer_date": "2020-12-31",
        "install_mode": "pythonpath_only",
        "cwd_mode": "target_workspace",
        "pytest_mode": "explicit_test_files",
        "extra_env": (),
        "max_seconds": 120,
        "why_selected": "test profile",
    }
    values.update(overrides)
    return gate.EnvironmentProfile(**values)


def test_build_uv_command_uses_no_project_for_historical_profile() -> None:
    command = gate.build_uv_command(profile(), Path("/tmp/target"), ["tests/test_example.py"])

    assert command[:6] == ["uv", "run", "--no-project", "--isolated", "--managed-python", "--python"]
    assert "--project" not in command
    assert "experiments/phase1_compiler" not in " ".join(command)
    assert command[-1] == "tests/test_example.py"


def test_build_uv_command_adds_editable_only_for_editable_mode() -> None:
    editable = profile(profile_id="py310_pytest7_editable", install_mode="editable")
    pythonpath_only = profile(install_mode="pythonpath_only")

    editable_command = gate.build_uv_command(editable, Path("/tmp/target"), ["tests/test_x.py"])
    pythonpath_command = gate.build_uv_command(pythonpath_only, Path("/tmp/target"), ["tests/test_x.py"])

    assert "--with-editable" in editable_command
    assert "--with-editable" not in pythonpath_command


def test_infer_profile_candidates_caps_profiles_and_keeps_project_boundary() -> None:
    profiles = gate.infer_profile_candidates("attrs", "2016-01-02T00:00:00+00:00")

    assert len(profiles) <= 5
    assert profiles[0].profile_id == "py311_current_editable"
    for candidate in profiles:
        command = gate.build_uv_command(candidate, Path("/tmp/target"), ["tests/test_x.py"])
        assert "--no-project" in command
        assert "--project" not in command


def test_classify_reference_subgate_separates_failure_modes() -> None:
    cases = [
        (0, "", "", "reference_pass"),
        (1, "", "Failed to build wheel for attrs", "reference_install_failed"),
        (1, "", "ModuleNotFoundError: No module named 'hypothesis'", "reference_import_failed"),
        (2, "", "ERROR collecting tests/test_x.py", "reference_collect_failed"),
        (1, "E   AssertionError: expected 1", "", "reference_assert_failed"),
        (124, "", "command timed out", "reference_timeout"),
        (1, "", "No interpreter found for Python 3.7", "reference_environment_unavailable"),
        (1, "", "unexpected nonzero output", "reference_unknown_failed"),
    ]

    for returncode, stdout, stderr, expected in cases:
        assert gate.classify_reference_subgate(returncode, stdout, stderr) == expected


def test_sanitize_output_tail_redacts_repo_home_and_uv_cache_paths() -> None:
    text = (
        f"error in {gate.REPO_ROOT}/target/tests/test_x.py\n"
        f"cache {Path.home()}/.cache/uv/archive\n"
        f"home {Path.home()}/project\n"
    )

    sanitized = gate.sanitize_output_tail(text)

    assert str(gate.REPO_ROOT) not in sanitized
    assert str(Path.home()) not in sanitized
    assert "<repo>" in sanitized
    assert "<uv-cache>" in sanitized
