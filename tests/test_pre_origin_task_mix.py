from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import canonical_digest  # noqa: E402
from examples.pre_origin_task_mix.study import (  # noqa: E402
    CommitProjection,
    TaskProjection,
    _load_commit_index,
    build_origins,
    compact_result,
    decide,
    future_horizon_span_days,
    git_counts,
    git_vocabulary,
    load_plan,
    module_for_path,
    modules_from_patch,
    smoothed_distribution,
    summarize_rows,
    task_module_mass,
    verify_result,
    verify_summary,
)


PLAN_PATH = (
    REPOSITORY_ROOT
    / "examples"
    / "pre_origin_task_mix"
    / "plan.json"
)


def _task(index: int, repository_id: str = "example/repository") -> TaskProjection:
    return TaskProjection(
        instance_id=f"task-{index:03d}",
        repository_id=repository_id,
        source_time=datetime(2020, 1, 1, tzinfo=UTC) + timedelta(days=index),
        base_commit=f"{index:040x}",
        modules=(f"src/module-{index % 3}",),
    )


def _passing_horizon(repository_count: int) -> dict[str, Any]:
    return {
        "repository_count": repository_count,
        "contrasts": {
            control_id: {
                "macro_repository": -0.1,
                "favorable_repository_count": repository_count,
                "repository_count": repository_count,
            }
            for control_id in (
                "task_full_history",
                "task_trailing_h",
                "git_full_touch",
                "git_trailing_90d_touch",
                "uniform",
            )
        },
    }


def test_frozen_plan_digest_is_valid() -> None:
    plan = load_plan(PLAN_PATH)

    assert plan["candidate"]["algorithm_id"] == "THY-001R-A"
    assert plan["audit_revision"]["original_plan_digest"] == (
        "10b4fcb22d7c1fa3adf5e3b04fa50bd9fd1272d9f2bc507585997bae03188459"
    )


def test_plan_rejects_contract_change_without_new_digest(tmp_path: Path) -> None:
    payload = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    payload["candidate"]["half_life_days"] = 90
    changed = tmp_path / "plan.json"
    changed.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="digest"):
        load_plan(changed)


def test_module_projection_excludes_test_vendor_and_lock_paths() -> None:
    module_plan = load_plan(PLAN_PATH)["module_projection"]

    assert module_for_path("src/parser/token.py", module_plan) == "src/parser"
    assert module_for_path("README.md", module_plan) == "ROOT"
    assert module_for_path("tests/parser/test_token.py", module_plan) is None
    assert module_for_path("vendor/parser/token.py", module_plan) is None
    assert module_for_path("src/parser/package-lock.json", module_plan) is None


def test_patch_projection_retains_both_rename_sides_without_tests() -> None:
    module_plan = load_plan(PLAN_PATH)["module_projection"]
    patch = "\n".join(
        (
            "diff --git a/src/old/parser.py b/lib/new/parser.py",
            "similarity index 100%",
            "rename from src/old/parser.py",
            "rename to lib/new/parser.py",
            "diff --git a/tests/test_parser.py b/tests/test_parser.py",
        )
    )

    assert modules_from_patch(patch, module_plan) == ("lib/new", "src/old")


def test_origins_use_non_overlapping_h10_blocks_with_nested_h5() -> None:
    plan = load_plan(PLAN_PATH)
    origins = build_origins(
        tuple(_task(index) for index in range(42)),
        plan["rolling_origin"],
    )["example/repository"]

    assert tuple(len(origin.history) for origin in origins) == (22, 32)
    assert all(origin.future_h5 == origin.future_h10[:5] for origin in origins)
    assert set(task.instance_id for task in origins[0].future_h10).isdisjoint(
        task.instance_id for task in origins[1].future_h10
    )


def test_future_unseen_modules_collapse_to_other_without_losing_mass() -> None:
    task = TaskProjection(
        instance_id="future",
        repository_id="example/repository",
        source_time=datetime(2020, 1, 1, tzinfo=UTC),
        base_commit="a" * 40,
        modules=("known", "new-a", "new-b"),
    )

    mass = task_module_mass(
        task,
        ("known", "OTHER"),
        unseen_label="OTHER",
    )

    assert mass == pytest.approx({"known": 1 / 3, "OTHER": 2 / 3})


def test_git_pressure_applies_fixed_decay_and_clamps_clock_anomaly() -> None:
    cutoff = datetime(2022, 1, 1, tzinfo=UTC)
    commits = (
        CommitProjection(
            "a" * 40,
            cutoff,
            ("module-a", "module-b"),
        ),
        CommitProjection(
            "b" * 40,
            cutoff - timedelta(days=365.25),
            ("module-a",),
        ),
        CommitProjection(
            "c" * 40,
            cutoff + timedelta(days=1),
            ("module-b",),
        ),
    )

    counts, anomaly_count = git_counts(
        commits,
        cutoff=cutoff,
        half_life_days=365.25,
    )

    assert anomaly_count == 1
    assert counts == pytest.approx({"module-a": 1.0, "module-b": 1.5})


def test_candidate_vocabulary_uses_only_cutoff_safe_git_modules() -> None:
    module_plan = load_plan(PLAN_PATH)["module_projection"]
    commits = (
        CommitProjection(
            "a" * 40,
            datetime(2022, 1, 1, tzinfo=UTC),
            ("src/git-visible",),
        ),
    )

    vocabulary = git_vocabulary(
        commits,
        module_plan=module_plan,
        unseen_label="OTHER",
    )

    assert vocabulary == ("OTHER", "ROOT", "src/git-visible")
    assert "src/patch-only" not in vocabulary


def test_future_horizon_span_starts_at_origin_cutoff() -> None:
    cutoff = datetime(2022, 1, 1, tzinfo=UTC)
    future = (
        TaskProjection(
            instance_id="future-1",
            repository_id="example/repository",
            source_time=cutoff + timedelta(days=2),
            base_commit="a" * 40,
            modules=("src/module",),
        ),
        TaskProjection(
            instance_id="future-2",
            repository_id="example/repository",
            source_time=cutoff + timedelta(days=5),
            base_commit="b" * 40,
            modules=("src/module",),
        ),
    )

    assert future_horizon_span_days(cutoff, future) == pytest.approx(5.0)


def test_additive_smoothing_preserves_probability_mass() -> None:
    probabilities = smoothed_distribution(
        {"module-a": 1.0},
        ("module-a", "OTHER"),
        smoothing=0.5,
    )

    assert probabilities == pytest.approx({"module-a": 0.75, "OTHER": 0.25})
    assert sum(probabilities.values()) == pytest.approx(1.0)


def test_gate_passes_only_when_both_sources_and_horizons_pass() -> None:
    summaries = {
        "multi_swe_bench": {
            "horizons": {
                "5": _passing_horizon(11),
                "10": _passing_horizon(11),
            }
        },
        "swe_bench_full": {
            "horizons": {
                "5": _passing_horizon(10),
                "10": _passing_horizon(10),
            }
        },
    }

    decision = decide(summaries, admission_failures=())

    assert decision["status"] == "pass"
    assert decision["agent_outcome_replay_authorized"] is True


def test_one_failed_h10_task_baseline_retires_candidate() -> None:
    full_h10 = _passing_horizon(10)
    full_h10["contrasts"]["task_trailing_h"]["macro_repository"] = 0.01
    summaries = {
        "multi_swe_bench": {
            "horizons": {
                "5": _passing_horizon(11),
                "10": _passing_horizon(11),
            }
        },
        "swe_bench_full": {
            "horizons": {
                "5": _passing_horizon(10),
                "10": full_h10,
            }
        },
    }

    decision = decide(summaries, admission_failures=())

    assert decision["status"] == "retire"
    assert decision["agent_outcome_replay_authorized"] is False


def test_missing_repository_is_data_blocker_not_algorithm_failure() -> None:
    decision = decide(
        {},
        admission_failures=(
            {
                "source_id": "multi_swe_bench",
                "repository_id": "cli/cli",
                "reason": "repository_cache_missing",
            },
        ),
    )

    assert decision["status"] == "data_blocked"


def test_git_projection_uses_names_not_blob_contents(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    subprocess.run(("git", "init", str(repository)), check=True, capture_output=True)
    subprocess.run(
        ("git", "-C", str(repository), "config", "user.name", "Test"),
        check=True,
    )
    subprocess.run(
        ("git", "-C", str(repository), "config", "user.email", "test@example.com"),
        check=True,
    )
    source = repository / "src" / "parser"
    source.mkdir(parents=True)
    (source / "token.py").write_text("TOKEN = 1\n", encoding="utf-8")
    subprocess.run(("git", "-C", str(repository), "add", "."), check=True)
    subprocess.run(
        ("git", "-C", str(repository), "commit", "-m", "initial"),
        check=True,
        capture_output=True,
    )
    (source / "token.py").write_text("TOKEN = 2\n", encoding="utf-8")
    subprocess.run(("git", "-C", str(repository), "commit", "-am", "change"), check=True)
    commit_id = subprocess.run(
        ("git", "-C", str(repository), "rev-parse", "HEAD"),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    index = _load_commit_index(
        repository,
        (commit_id,),
        load_plan(PLAN_PATH)["module_projection"],
    )

    assert index[commit_id].modules == ("src/parser",)


def test_result_verification_survives_json_sequence_round_trip() -> None:
    plan = load_plan(PLAN_PATH)
    rows = []
    for source in plan["sources"]:
        for repository_id in source["repositories"]:
            for horizon in (5, 10):
                rows.append(
                    {
                        "source_id": source["source_id"],
                        "repository_id": repository_id,
                        "origin_id": f"{repository_id}:origin-001",
                        "horizon": horizon,
                        "future_calendar_span_days": 1.0,
                        "future_other_mass": 0.0,
                        "losses": {
                            "candidate": 0.1,
                            "task_full_history": 0.2,
                            "task_trailing_h": 0.2,
                            "git_full_touch": 0.2,
                            "git_trailing_90d_touch": 0.2,
                            "uniform": 0.2,
                        },
                    }
                )
    expected_by_source = {
        source["source_id"]: tuple(source["repositories"])
        for source in plan["sources"]
    }
    summaries = summarize_rows(
        rows,
        expected_by_source=expected_by_source,
        bootstrap_seed=plan["metrics"]["bootstrap_seed"],
    )
    result = {
        "schema_version": "barcarolle_pre_origin_task_mix_results_v1",
        "study_id": plan["study_id"],
        "plan_digest": plan["plan_digest"],
        "origin_rows": tuple(rows),
        "origin_rows_digest": canonical_digest(tuple(rows)),
        "source_summaries": summaries,
        "admission_failures": (),
        "decision": decide(summaries, admission_failures=()),
    }
    result["result_digest"] = canonical_digest(result)
    round_tripped = json.loads(json.dumps(result))

    verify_result(round_tripped, plan)


def test_summary_verification_binds_compact_projection_to_raw_result() -> None:
    plan = load_plan(PLAN_PATH)
    rows = []
    for source in plan["sources"]:
        for repository_id in source["repositories"]:
            for horizon in (5, 10):
                rows.append(
                    {
                        "source_id": source["source_id"],
                        "repository_id": repository_id,
                        "origin_id": f"{repository_id}:origin-001",
                        "horizon": horizon,
                        "future_calendar_span_days": 1.0,
                        "future_other_mass": 0.0,
                        "losses": {
                            predictor_id: 0.1
                            for predictor_id in (
                                "candidate",
                                "task_full_history",
                                "task_trailing_h",
                                "git_full_touch",
                                "git_trailing_90d_touch",
                                "uniform",
                            )
                        },
                    }
                )
    expected_by_source = {
        source["source_id"]: tuple(source["repositories"])
        for source in plan["sources"]
    }
    summaries = summarize_rows(
        rows,
        expected_by_source=expected_by_source,
        bootstrap_seed=plan["metrics"]["bootstrap_seed"],
    )
    result = {
        "schema_version": "barcarolle_pre_origin_task_mix_results_v1",
        "study_id": plan["study_id"],
        "plan_digest": plan["plan_digest"],
        "origin_rows": tuple(rows),
        "origin_rows_digest": canonical_digest(tuple(rows)),
        "source_summaries": summaries,
        "admission_failures": (),
        "decision": decide(summaries, admission_failures=()),
    }
    result["result_digest"] = canonical_digest(result)
    summary = dict(compact_result(result, plan))
    summary["resource_use"] = {"paid_api_calls": 1}
    summary["summary_digest"] = canonical_digest(
        {key: value for key, value in summary.items() if key != "summary_digest"}
    )

    with pytest.raises(ValueError, match="raw result"):
        verify_summary(summary, plan, result=result)
