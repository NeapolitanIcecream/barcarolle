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
from examples.multi_swe_research.suitability_audit import (  # noqa: E402
    _full_minus_zero_for_response,
    _observed_repository_row,
    _temporal_null,
    load_suitability_audit_plan,
    load_task_metadata,
)

EXAMPLE_ROOT = REPOSITORY_ROOT / "examples" / "multi_swe_research"


def test_suitability_plan_is_self_digested_and_zero_authority() -> None:
    plan = dict(load_suitability_audit_plan())
    digest = plan.pop("suitability_audit_plan_digest")

    assert digest == canonical_digest(plan)
    assert plan["research_contract"]["primary_metric"].startswith(
        "future pass-rate"
    )
    assert plan["authority"] == {
        "paid_api_calls": 0,
        "sealed_swe_bench_holdout_agents_opened": 0,
        "new_public_outcome_panels_opened": 0,
        "generator_development": False,
        "implementation_scope": (
            "one direct Multi-SWE experiment module, focused tests, ignored "
            "raw results, a compact self-digested summary, and claim-boundary "
            "documentation"
        ),
    }


def test_suitability_plan_rejects_resigned_diagnostic_drift(
    tmp_path: Path,
) -> None:
    plan = dict(load_suitability_audit_plan())
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

    with pytest.raises(
        ValueError,
        match="diagnostic size changed",
    ):
        load_suitability_audit_plan(path)


def test_committed_suitability_source_identity_loads() -> None:
    plan = load_suitability_audit_plan()
    tasks = load_task_metadata(
        EXAMPLE_ROOT / "evidence" / "task-universe.jsonl",
        EXAMPLE_ROOT / "evidence" / "task-times.jsonl",
        plan,
    )

    assert len(tasks) == 1632
    assert len({task.instance_id for task in tasks}) == 1632
    assert len({task.repository_id for task in tasks}) == 39


def test_observed_controls_keep_cached_climatology_separate() -> None:
    np = pytest.importorskip("numpy")
    tasks = _tasks(4)
    origins = (
        RepositoryOrigin("repo", "repo:o1", tasks[:2], tasks[2:3]),
        RepositoryOrigin("repo", "repo:o2", tasks[:3], tasks[3:4]),
    )
    response = np.asarray(
        (
            (0, 0),
            (0, 1),
            (1, 0),
            (1, 1),
        ),
        dtype=np.float64,
    )

    row = _observed_repository_row(
        np,
        "repo",
        origins,
        response,
        (2, 3),
        1,
        ("a", "b"),
    )

    first = row["origin_rows"][0]
    assert first["cached_expanding_median_mae"] == pytest.approx(
        first["full_history_mae"]
    )
    assert row["all_zero_agent_origin_count"] == 1
    assert row["all_one_agent_origin_count"] == 3
    assert row["future_cell_count"] == 4
    assert row["positive_future_cell_count"] == 3


def test_joint_response_circular_null_is_deterministic() -> None:
    np = pytest.importorskip("numpy")
    response = np.asarray(
        (
            (0, 0),
            (0, 1),
            (1, 0),
            (1, 1),
        ),
        dtype=np.float64,
    )
    panels = {
        "first": {"response": response, "starts": (2, 3)},
        "second": {"response": response[::-1].copy(), "starts": (2, 3)},
    }

    first = _temporal_null(
        np=np,
        panel_arrays=panels,
        horizon=1,
        draws=20,
        seed=17,
    )
    second = _temporal_null(
        np=np,
        panel_arrays=panels,
        horizon=1,
        draws=20,
        seed=17,
    )

    assert first == second
    assert 0.0 < first["one_sided_probability"] <= 1.0
    expected = sum(
        _full_minus_zero_for_response(
            np,
            panel["response"],
            panel["starts"],
            1,
        )
        for panel in panels.values()
    ) / 2
    assert first["observed"] == pytest.approx(expected)


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
