from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, cast

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.generator_calibrated_exposure.study import (  # noqa: E402
    brier_loss,
    calibrated_exposure_distribution,
    canonical_task_id,
    decide,
    load_commit_index,
    load_plan,
    module_for_repository_path,
    modules_from_patch,
    probability_distribution,
    reachable_exposure_commit_ids,
    summarize_rows,
    verify_result,
)
from examples.pre_origin_task_mix.study import TaskProjection  # noqa: E402

PLAN_PATH = (
    REPOSITORY_ROOT
    / "examples"
    / "generator_calibrated_exposure"
    / "plan.json"
)


def test_frozen_plan_and_implementation_digests_are_valid() -> None:
    plan = cast(dict[str, Any], load_plan(PLAN_PATH))

    assert plan["candidate"]["algorithm_id"] == "THY-002"
    assert plan["source"]["canonical_repository_count"] == 40
    assert plan["source"]["canonical_task_count"] == 5365


def test_plan_rejects_formula_change_without_new_digest(tmp_path: Path) -> None:
    payload = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    payload["candidate"]["prior_task_shape"] = 1.0
    changed = tmp_path / "plan.json"
    changed.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="digest"):
        load_plan(changed)


def _task(
    instance_id: str,
    module: str,
    *,
    days: int = 0,
) -> TaskProjection:
    return TaskProjection(
        instance_id=instance_id,
        repository_id="example/repository",
        source_time=datetime(2020, 1, 1, tzinfo=UTC) + timedelta(days=days),
        base_commit=instance_id[0] * 40,
        modules=(module,),
    )


def _row(
    repository_id: str,
    horizon: int,
    candidate: float,
    *,
    origin: int = 1,
) -> dict[str, object]:
    return {
        "repository_id": repository_id,
        "origin_id": f"{repository_id}:origin-{origin:03d}",
        "horizon": horizon,
        "future_calendar_span_days": 10.0,
        "future_other_mass": 0.0,
        "losses": {
            "candidate": candidate,
            "task_full_history": 0.3,
            "git_recent_touch": 0.4,
            "yield_only": 0.5,
            "task_trailing_h": 0.6,
            "uniform": 0.7,
        },
    }


def test_canonical_task_identity_survives_repository_aliases() -> None:
    expected = "saveourtool/diktat#pr-1008"

    assert canonical_task_id(
        repository_id="saveourtool/diktat",
        source_instance_id="analysis-dev__diktat-1008",
        pull_request_url="https://github.com/saveourtool/diktat/pull/1008",
    ) == expected
    assert canonical_task_id(
        repository_id="saveourtool/diktat",
        source_instance_id="cqfn__diktat-1008",
        pull_request_url="https://github.com/saveourtool/diktat/pull/1008",
    ) == expected


def test_canonical_task_identity_rejects_non_github_pr_url() -> None:
    with pytest.raises(ValueError, match="pull-request URL"):
        canonical_task_id(
            repository_id="example/repository",
            source_instance_id="task-1",
            pull_request_url="https://example.com/pull/1",
        )


def test_canonical_task_identity_rejects_source_alias_mismatch() -> None:
    with pytest.raises(ValueError, match="source lineage"):
        canonical_task_id(
            repository_id="example/repository",
            source_instance_id="task-1",
            pull_request_url="https://github.com/other/repository/pull/1",
            source_alias="example/repository",
        )


def test_dimensionally_pooled_prior_is_finite_for_cold_start() -> None:
    probabilities, diagnostics = calibrated_exposure_distribution(
        task_counts={"a": 4.0, "b": 0.0},
        historical_exposure={"a": 8.0, "b": 0.0},
        recent_exposure={"a": 1.0, "b": 1.0},
        vocabulary=("a", "b"),
        prior_task_shape=0.5,
    )

    assert diagnostics["repository_task_per_touch_rate"] == pytest.approx(0.5)
    assert diagnostics["prior_exposure_mass"] == pytest.approx(1.0)
    assert probabilities["a"] == pytest.approx(0.5)
    assert probabilities["b"] == pytest.approx(0.5)
    assert sum(probabilities.values()) == pytest.approx(1.0)


def test_shrinkage_reports_task_mass_without_observed_git_exposure() -> None:
    probabilities, diagnostics = calibrated_exposure_distribution(
        task_counts={"observed": 4.0, "projected_only": 1.0},
        historical_exposure={"observed": 8.0, "projected_only": 0.0},
        recent_exposure={"observed": 1.0, "projected_only": 1.0},
        vocabulary=("observed", "projected_only"),
        prior_task_shape=0.5,
    )

    assert sum(probabilities.values()) == pytest.approx(1.0)
    assert diagnostics[
        "task_positive_zero_historical_exposure_module_count"
    ] == 1.0
    assert diagnostics["task_mass_on_zero_historical_exposure_modules"] == 1.0


def test_reachable_exposure_walk_survives_out_of_order_commit_clocks(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    subprocess.run(
        ("git", "init", "-q", "-b", "main", str(repository)),
        check=True,
    )
    subprocess.run(
        ("git", "-C", str(repository), "config", "user.email", "test@example.com"),
        check=True,
    )
    subprocess.run(
        ("git", "-C", str(repository), "config", "user.name", "Test"),
        check=True,
    )

    commits = []
    for index, timestamp in enumerate(
        (
            "2019-01-01T00:00:00+00:00",
            "2022-01-01T00:00:00+00:00",
            "2020-01-01T00:00:00+00:00",
            "2023-01-01T00:00:00+00:00",
        )
    ):
        (repository / "value.txt").write_text(str(index), encoding="utf-8")
        subprocess.run(
            ("git", "-C", str(repository), "add", "value.txt"),
            check=True,
        )
        environment = {
            **os.environ,
            "GIT_AUTHOR_DATE": timestamp,
            "GIT_COMMITTER_DATE": timestamp,
        }
        subprocess.run(
            ("git", "-C", str(repository), "commit", "-q", "-m", f"commit-{index}"),
            check=True,
            env=environment,
        )
        commits.append(
            subprocess.run(
                ("git", "-C", str(repository), "rev-parse", "HEAD"),
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )

    observed = reachable_exposure_commit_ids(
        repository,
        origin_commit=commits[-1],
        observation_start=datetime(2021, 1, 1, tzinfo=UTC),
    )

    assert set(observed) == {commits[1], commits[3]}

    non_ascii_path = repository / "a" / "模块" / "file.py"
    non_ascii_path.parent.mkdir(parents=True)
    non_ascii_path.write_text("value", encoding="utf-8")
    subprocess.run(
        ("git", "-C", str(repository), "add", "a/模块/file.py"),
        check=True,
    )
    environment = {
        **os.environ,
        "GIT_AUTHOR_DATE": "2024-01-01T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2024-01-01T00:00:00+00:00",
    }
    subprocess.run(
        ("git", "-C", str(repository), "commit", "-q", "-m", "non-ascii"),
        check=True,
        env=environment,
    )
    non_ascii_commit = subprocess.run(
        ("git", "-C", str(repository), "rev-parse", "HEAD"),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    commit_index = load_commit_index(
        repository,
        (commits[3], non_ascii_commit),
        {
            "depth": 2,
            "root_label": "ROOT",
            "unseen_label": "OTHER",
            "excluded_components": ("tests",),
            "excluded_file_names": ("package-lock.json",),
        },
    )

    assert commit_index[non_ascii_commit].modules == ("a/模块",)
    assert commit_index[commits[3]].modules == ("ROOT",)


def test_module_projection_preserves_real_top_level_a_and_b_directories() -> None:
    module_plan = {
        "depth": 2,
        "root_label": "ROOT",
        "unseen_label": "OTHER",
        "excluded_components": ("tests",),
        "excluded_file_names": ("package-lock.json",),
    }

    assert module_for_repository_path("a/package/file.py", module_plan) == (
        "a/package"
    )
    assert module_for_repository_path("b/package/file.py", module_plan) == (
        "b/package"
    )
    assert modules_from_patch(
        "diff --git a/b/package/file.py b/b/package/file.py",
        module_plan,
    ) == ("b/package",)
    assert modules_from_patch(
        "diff --git a/a/package/file with spaces.py "
        "b/a/package/file with spaces.py",
        module_plan,
    ) == ("a/package",)


def test_calibration_changes_equal_recent_exposure_by_historical_yield() -> None:
    probabilities, _ = calibrated_exposure_distribution(
        task_counts={"high": 8.0, "low": 1.0},
        historical_exposure={"high": 8.0, "low": 8.0},
        recent_exposure={"high": 2.0, "low": 2.0},
        vocabulary=("high", "low"),
        prior_task_shape=0.5,
    )

    assert probabilities["high"] > probabilities["low"]


def test_constant_yield_reduces_to_recent_git_distribution() -> None:
    candidate, _ = calibrated_exposure_distribution(
        task_counts={"a": 2.0, "b": 4.0},
        historical_exposure={"a": 4.0, "b": 8.0},
        recent_exposure={"a": 1.0, "b": 3.0},
        vocabulary=("a", "b"),
        prior_task_shape=0.5,
    )
    git_only = probability_distribution(
        {"a": 1.0, "b": 3.0},
        ("a", "b"),
    )

    assert candidate == pytest.approx(git_only)


def test_brier_loss_supports_fractional_multimodule_labels_without_epsilon() -> None:
    future = (
        TaskProjection(
            instance_id="future",
            repository_id="example/repository",
            source_time=datetime(2020, 1, 1, tzinfo=UTC),
            base_commit="f" * 40,
            modules=("a", "b"),
        ),
    )

    loss = brier_loss(
        future,
        {"a": 1.0, "b": 0.0, "OTHER": 0.0},
        ("a", "b", "OTHER"),
        unseen_label="OTHER",
    )

    assert loss == pytest.approx(0.5)


def test_repository_first_summary_does_not_origin_weight() -> None:
    rows = [
        _row("many/origins", horizon, 0.1, origin=index)
        for horizon in (5, 10)
        for index in range(1, 101)
    ]
    rows.extend(
        (
            _row("one/origin", 5, 0.5),
            _row("one/origin", 10, 0.5),
        )
    )

    summary = summarize_rows(
        rows,
        expected_repositories=("many/origins", "one/origin"),
        expected_origin_counts={"many/origins": 100, "one/origin": 1},
        bootstrap_seed=7,
    )

    typed_summary = cast(dict[str, Any], summary)
    assert typed_summary["horizons"]["5"]["macro_losses"][
        "candidate"
    ] == pytest.approx(0.3)


def test_summary_rejects_duplicate_or_incomplete_origin_pairs() -> None:
    complete_pair = (
        _row("repo/one", 5, 0.1),
        _row("repo/one", 10, 0.1),
    )
    with pytest.raises(ValueError, match="duplicate"):
        summarize_rows(
            (*complete_pair, complete_pair[0]),
            expected_repositories=("repo/one",),
            expected_origin_counts={"repo/one": 1},
            bootstrap_seed=7,
        )
    with pytest.raises(ValueError, match="incomplete"):
        summarize_rows(
            complete_pair[:1],
            expected_repositories=("repo/one",),
            expected_origin_counts={"repo/one": 1},
            bootstrap_seed=7,
        )


def test_summary_rejects_dropped_complete_origin_pair() -> None:
    with pytest.raises(ValueError, match="Origin rows changed"):
        summarize_rows(
            (
                _row("repo/one", 5, 0.1),
                _row("repo/one", 10, 0.1),
            ),
            expected_repositories=("repo/one",),
            expected_origin_counts={"repo/one": 2},
            bootstrap_seed=7,
        )


def test_summary_rejects_unknown_repository_and_horizon() -> None:
    with pytest.raises(ValueError, match="unexpected repository"):
        summarize_rows(
            (
                _row("repo/two", 5, 0.1),
                _row("repo/two", 10, 0.1),
            ),
            expected_repositories=("repo/one",),
            expected_origin_counts={"repo/one": 1},
            bootstrap_seed=7,
        )
    with pytest.raises(ValueError, match="future horizon"):
        summarize_rows(
            (_row("repo/one", 7, 0.1),),
            expected_repositories=("repo/one",),
            expected_origin_counts={"repo/one": 1},
            bootstrap_seed=7,
        )


def test_gate_requires_both_horizons_and_mechanistic_controls() -> None:
    rows = []
    repositories = tuple(f"repo/{index}" for index in range(5))
    for repository_id in repositories:
        rows.extend(
            (
                _row(repository_id, 5, 0.1),
                _row(repository_id, 10, 0.1),
            )
        )
    summary = summarize_rows(
        rows,
        expected_repositories=repositories,
        expected_origin_counts={repository_id: 1 for repository_id in repositories},
        bootstrap_seed=7,
    )

    decision = decide(
        summary,
        expected_repository_count=5,
        admission_failures=(),
    )

    assert decision["status"] == "pass"
    assert decision["agent_outcome_replay_authorized"] is False


def test_verifier_rejects_study_or_resource_boundary_tampering() -> None:
    plan = cast(dict[str, Any], load_plan(PLAN_PATH))
    resource_use = {
        "paid_api_calls": 0,
        "embedding_calls": 0,
        "agent_outcomes_opened": 0,
        "sealed_holdout_opened": 0,
    }
    with pytest.raises(ValueError, match="study identity"):
        verify_result(
            {
                "schema_version": "barcarolle_generator_calibrated_exposure_results_v1",
                "plan_digest": plan["plan_digest"],
                "study_id": "changed-study",
                "resource_use": resource_use,
            },
            plan,
        )
    with pytest.raises(ValueError, match="resource boundary"):
        verify_result(
            {
                "schema_version": "barcarolle_generator_calibrated_exposure_results_v1",
                "plan_digest": plan["plan_digest"],
                "study_id": plan["study_id"],
                "resource_use": {**resource_use, "agent_outcomes_opened": 1},
            },
            plan,
        )


def test_admission_failure_is_data_blocked_not_algorithm_failure() -> None:
    decision = decide(
        {"horizons": {}},
        expected_repository_count=40,
        admission_failures=(
            {
                "repository_id": "example/repository",
                "reason": "repository_cache_missing",
            },
        ),
    )

    assert decision["status"] == "data_blocked"
