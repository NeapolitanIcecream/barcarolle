from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import sys

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import canonical_digest  # noqa: E402
from examples.multi_repository_study.public_replay import (  # noqa: E402
    RepositoryOrigin,
    TaskMetadata,
)
from examples.multi_repository_study.suitability_audit import (  # noqa: E402
    _evaluate_observed,
    load_verified_inputs,
    load_verified_suitability_plan,
)


def test_verified_suitability_plan_is_frozen_and_zero_authority() -> None:
    plan = dict(load_verified_suitability_plan())
    digest = plan.pop("suitability_audit_plan_digest")

    assert digest == canonical_digest(plan)
    assert plan["frame"] == {
        "repository_ids": [
            "astropy/astropy",
            "django/django",
            "matplotlib/matplotlib",
            "pydata/xarray",
            "scikit-learn/scikit-learn",
            "sphinx-doc/sphinx",
            "sympy/sympy",
        ],
        "repository_count": 7,
        "expected_origin_count": 68,
        "minimum_initial_history_tasks": 15,
        "future_tasks": 5,
        "selection_budget_tasks": 10,
        "origin_alignment": (
            "end-aligned complete non-overlapping future blocks using "
            "build_repository_origins"
        ),
        "ordering": "created_at then instance_id",
        "primary_aggregation": "equal repository",
        "secondary_aggregation": "pooled Origin mean, labeled separately",
    }
    assert plan["authority"]["paid_api_calls"] == 0
    assert plan["authority"]["sealed_swe_bench_holdout_agents_opened"] == 0


def test_verified_suitability_plan_rejects_diagnostic_drift(
    tmp_path: Path,
) -> None:
    plan = dict(load_verified_suitability_plan())
    plan["temporal_null"] = {
        **plan["temporal_null"],
        "draws": 20,
    }
    unsigned = {
        key: value
        for key, value in plan.items()
        if key != "suitability_audit_plan_digest"
    }
    plan["suitability_audit_plan_digest"] = canonical_digest(unsigned)
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(ValueError, match="diagnostic contract changed"):
        load_verified_suitability_plan(path)


def test_verified_inputs_load_only_opened_development_agents() -> None:
    pytest.importorskip("pyarrow")
    plan = load_verified_suitability_plan()
    source = plan["source"]
    if any(
        not (REPOSITORY_ROOT / source[key]).exists()
        for key in ("dataset_path", "result_directory")
    ):
        pytest.skip("ignored Verified source artifacts are not present")
    tasks, outcomes, diagnostics, metadata, identities = (
        load_verified_inputs(plan=plan)
    )

    assert len(tasks) == 500
    assert len(outcomes) == 11
    assert set(outcomes) == set(diagnostics) == set(metadata)
    assert identities["opened_agent_ids"] == tuple(sorted(outcomes))
    holdout_ids = {
        "rag-gpt35-20231010",
        "rag-swellama7b-20231010",
        "sweagent-gpt4-20240402",
        "sweagent-gpt4o-20240728",
        "sweagent-devstral-20250725",
        "openhands-kimi-k2-20250716",
    }
    assert not holdout_ids & set(outcomes)


def test_observed_verified_frame_preserves_agent_dimension() -> None:
    np = pytest.importorskip("numpy")
    tasks = _tasks(4)
    origins = (
        RepositoryOrigin("repo", "repo:o1", tasks[:2], tasks[2:3]),
        RepositoryOrigin("repo", "repo:o2", tasks[:3], tasks[3:4]),
    )
    outcomes = {
        "a": {
            "task-0": 0,
            "task-1": 0,
            "task-2": 1,
            "task-3": 1,
        },
        "b": {
            "task-0": 0,
            "task-1": 1,
            "task-2": 0,
            "task-3": 1,
        },
    }

    rows, arrays = _evaluate_observed(
        np=np,
        repository_ids=("repo",),
        origins_by_repository={"repo": origins},
        outcomes_by_agent=outcomes,
        agent_ids=("a", "b"),
        horizon=1,
    )

    assert len(rows) == 1
    assert rows[0]["agent_origin_count"] == 4
    assert arrays["repo"]["response"].shape == (4, 2)


def _tasks(count: int) -> tuple[TaskMetadata, ...]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return tuple(
        TaskMetadata(
            instance_id=f"task-{index}",
            repository_id="repo",
            created_at=(start + timedelta(days=index)).isoformat().replace(
                "+00:00",
                "Z",
            ),
            difficulty="fixture",
            problem_statement="fixture",
        )
        for index in range(count)
    )
