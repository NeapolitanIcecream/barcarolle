from dataclasses import replace
from datetime import UTC, datetime

import pytest

from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    CheckRecord,
    EvaluationCellSet,
    MetricRecord,
    ResultCacheIdentity,
    ResultCellRef,
    ResultMatrix,
    ResultRecord,
    SelectorRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    canonical_digest,
    make_check_digest,
    make_selector_input_id,
    make_solver_material_digest,
    record_with_digest,
    validate_benchmark_selection,
    validate_metric,
    validate_selector_input,
)
from barcarolle.selection import (
    FeatureConfig,
    LeakagePolicy,
    MetricConfig,
    RollingOriginPolicy,
    SelectionBudget,
    SelectionConfig,
    build_feature_snapshot,
    build_rolling_origin,
    build_selector_input,
    choose_selector_by_mean_mae,
    choose_selector_from_metrics,
    evaluate_selection,
    fit_rule_mixture_from_metrics,
    freeze_evaluation_selections,
    lint_feature_snapshot,
    select_recency,
    select_rule_mixture,
    select_with_selector,
    train_selector,
)
from barcarolle.task_pool import TimeRange


def test_build_rolling_origin_separates_history_and_future_without_outcomes() -> None:
    origin = build_rolling_origin(
        _task_pool(("task-old", "task-future"), ("check-old", "check-future")),
        (_task("task-old", "check-old", available_at="2026-01-02T00:00:00Z"), _task("task-future", "check-future", available_at="2026-01-07T00:00:00Z")),
        {
            "check-old": _check("check-old", "task-old", available_at="2026-01-02T00:00:00Z"),
            "check-future": _check("check-future", "task-future", available_at="2026-01-07T00:00:00Z"),
        },
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        _rolling_policy(future_holdout_known=True),
    )

    assert origin.history_task_check_refs == (TaskCheckRef("task-old", "check-old"),)
    assert origin.future_holdout_task_check_refs == (TaskCheckRef("task-future", "check-future"),)
    assert origin.as_of_cutoff == "2026-01-05T00:00:00.000000Z"


def test_build_rolling_origin_preserves_fractional_second_boundary() -> None:
    task_pool = _task_pool(("history", "future"), ("history-check", "future-check"))
    origin = build_rolling_origin(
        task_pool,
        (
            _task("history", "history-check", available_at="2026-01-05T00:00:00.250000Z"),
            _task("future", "future-check", available_at="2026-01-05T00:00:00.750000Z"),
        ),
        {
            "history-check": _check(
                "history-check",
                "history",
                available_at="2026-01-05T00:00:00.250000Z",
            ),
            "future-check": _check(
                "future-check",
                "future",
                available_at="2026-01-05T00:00:00.750000Z",
            ),
        },
        datetime(2026, 1, 5, 0, 0, 0, 500000, tzinfo=UTC),
        TimeRange("2026-01-05T00:00:00.500001Z", "2026-01-05T00:00:00.999999Z"),
        _rolling_policy(future_holdout_known=True),
    )

    assert origin.origin_time == "2026-01-05T00:00:00.500000Z"
    assert origin.as_of_cutoff == "2026-01-05T00:00:00.500000Z"
    assert origin.history_task_check_refs == (TaskCheckRef("history", "history-check"),)
    assert origin.future_holdout_task_check_refs == (TaskCheckRef("future", "future-check"),)


def test_build_rolling_origin_identity_changes_with_holdout() -> None:
    task_pool = _task_pool(("history", "future"), ("history-check", "future-check"))
    tasks = (
        _task("history", "history-check", available_at="2026-01-02T00:00:00Z"),
        _task("future", "future-check", available_at="2026-01-07T00:00:00Z"),
    )
    checks = {
        "history-check": _check("history-check", "history", available_at="2026-01-02T00:00:00Z"),
        "future-check": _check("future-check", "future", available_at="2026-01-07T00:00:00Z"),
    }
    short_holdout = build_rolling_origin(
        task_pool,
        tasks,
        checks,
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-06T23:59:59Z"),
        _rolling_policy(future_holdout_known=True),
    )
    shifted_empty_holdout = build_rolling_origin(
        task_pool,
        tasks,
        checks,
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-05T12:00:00Z", "2026-01-06T23:59:59Z"),
        _rolling_policy(future_holdout_known=True),
    )
    long_holdout = build_rolling_origin(
        task_pool,
        tasks,
        checks,
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        _rolling_policy(future_holdout_known=True),
    )

    assert short_holdout.future_holdout_task_check_refs == ()
    assert shifted_empty_holdout.future_holdout_task_check_refs == ()
    assert long_holdout.future_holdout_task_check_refs == (TaskCheckRef("future", "future-check"),)
    assert short_holdout.origin_id != shifted_empty_holdout.origin_id
    assert short_holdout.origin_id != long_holdout.origin_id


def test_recency_selection_is_chronological_and_input_order_independent() -> None:
    task_pool = _task_pool(("task-new", "task-old"), ("check-new", "check-old"))
    task_new = _task("task-new", "check-new", available_at="2026-01-04T00:00:00Z")
    task_old = _task("task-old", "check-old", available_at="2026-01-02T00:00:00Z")
    checks = {
        "check-new": _check("check-new", "task-new", available_at="2026-01-04T00:00:00Z"),
        "check-old": _check("check-old", "task-old", available_at="2026-01-02T00:00:00Z"),
    }
    origin_forward = build_rolling_origin(
        task_pool,
        (task_new, task_old),
        checks,
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        _rolling_policy(),
    )
    origin_reversed = build_rolling_origin(
        task_pool,
        (task_old, task_new),
        checks,
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        _rolling_policy(),
    )

    expected_refs = (TaskCheckRef("task-old", "check-old"), TaskCheckRef("task-new", "check-new"))
    assert origin_forward.history_task_check_refs == expected_refs
    assert origin_reversed.history_task_check_refs == expected_refs

    snapshot = build_feature_snapshot(
        origin_forward,
        task_pool,
        (task_new, task_old),
        checks,
        (),
        FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",)),
    )
    selector_input = build_selector_input(
        origin_forward,
        task_pool,
        snapshot,
        (),
        (_agent(),),
        SelectionBudget("budget", 1),
        LeakagePolicy("leakage", ("task_metadata",), origin_forward.as_of_cutoff),
    )

    selection = select_recency(selector_input)

    assert selection.selected_task_check_refs == (TaskCheckRef("task-new", "check-new"),)


def test_build_rolling_origin_enforces_cluster_policy() -> None:
    task_pool = _task_pool(("old", "recent", "wrong-cluster"), ("old-check", "recent-check", "wrong-check"))
    origin = build_rolling_origin(
        task_pool,
        (
            _task("old", "old-check", available_at="2026-01-02T00:00:00Z", cluster_id="allowed"),
            _task("recent", "recent-check", available_at="2026-01-04T12:00:00Z", cluster_id="allowed"),
            _task("wrong-cluster", "wrong-check", available_at="2026-01-02T00:00:00Z", cluster_id="blocked"),
        ),
        {
            "old-check": _check("old-check", "old", available_at="2026-01-02T00:00:00Z"),
            "recent-check": _check("recent-check", "recent", available_at="2026-01-04T12:00:00Z"),
            "wrong-check": _check("wrong-check", "wrong-cluster", available_at="2026-01-02T00:00:00Z"),
        },
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        _rolling_policy(allowed_cluster_ids=("allowed",)),
    )

    assert origin.history_task_check_refs == (
        TaskCheckRef("old", "old-check"),
        TaskCheckRef("recent", "recent-check"),
    )


def test_build_rolling_origin_rejects_cutoff_after_origin() -> None:
    with pytest.raises(ValueError, match="must not be after origin_time"):
        build_rolling_origin(
            _task_pool(("task",), ("check",)),
            (_task("task", "check", available_at="2026-01-06T00:00:00Z"),),
            {"check": _check("check", "task", available_at="2026-01-06T00:00:00Z")},
            datetime(2026, 1, 5, tzinfo=UTC),
            TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
            replace(_rolling_policy(), as_of_cutoff_rule="2026-01-10T00:00:00Z"),
        )


def test_build_rolling_origin_compares_timezone_offsets_as_instants() -> None:
    task_pool = _task_pool(("old", "after-origin"), ("old-check", "after-check"))
    origin = build_rolling_origin(
        task_pool,
        (
            _task("old", "old-check", available_at="2026-01-02T00:00:00Z"),
            _task("after-origin", "after-check", available_at="2026-01-04T20:00:00-05:00"),
        ),
        {
            "old-check": _check("old-check", "old", available_at="2026-01-02T00:00:00Z"),
            "after-check": _check("after-check", "after-origin", available_at="2026-01-04T20:00:00-05:00"),
        },
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-05T00:30:00Z", "2026-01-06T00:00:00Z"),
        _rolling_policy(future_holdout_known=True),
    )

    assert origin.history_task_check_refs == (TaskCheckRef("old", "old-check"),)
    assert origin.future_holdout_task_check_refs == (TaskCheckRef("after-origin", "after-check"),)


def test_build_selector_input_lints_features_and_rejects_future_results() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    feature_config = FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",))
    pre_origin_results = (_result(result_available_at="2026-01-04T00:00:00Z"),)
    snapshot = build_feature_snapshot(origin, task_pool, (_task("task-old", "check-old"),), {"check-old": _check("check-old", "task-old")}, pre_origin_results, feature_config)

    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        pre_origin_results,
        (_agent(),),
        SelectionBudget("budget", 1),
        LeakagePolicy("leakage", ("task_metadata",), origin.as_of_cutoff),
    )

    assert validate_selector_input(selector_input).ok
    assert selector_input.eligible_task_check_refs == origin.history_task_check_refs
    assert selector_input.feature_records_digest == snapshot.feature_records_digest
    assert selector_input.feature_snapshot_lint_status == "passed"

    with pytest.raises(ValueError, match="after the origin cutoff"):
        build_selector_input(
            origin,
            task_pool,
            snapshot,
            (_result(result_available_at="2026-01-06T00:00:00Z"),),
            (_agent(),),
            SelectionBudget("budget", 1),
            LeakagePolicy("leakage", ("task_metadata",), origin.as_of_cutoff),
        )


def test_build_selector_input_allows_metadata_only_cold_start() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (),
        FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",)),
    )

    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (),
        (_agent(),),
        SelectionBudget("budget", 1),
        LeakagePolicy("leakage", ("task_metadata",), origin.as_of_cutoff),
    )

    assert validate_selector_input(selector_input).ok
    assert selector_input.pre_origin_result_ids == ()
    assert selector_input.pre_origin_result_digests == ()
    assert selector_input.feature_records_digest == snapshot.feature_records_digest


def test_build_selector_input_rejects_timezone_offset_post_origin_result() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    feature_config = FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",))
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        feature_config,
    )

    with pytest.raises(ValueError, match="after the origin cutoff"):
        build_selector_input(
            origin,
            task_pool,
            snapshot,
            (_result(result_available_at="2026-01-04T20:00:00-05:00"),),
            (_agent(),),
            SelectionBudget("budget", 1),
            LeakagePolicy("leakage", ("task_metadata",), origin.as_of_cutoff),
        )


def test_build_feature_snapshot_rejects_result_finished_after_origin_as_instant() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = replace(
        _origin(task_pool),
        origin_time="2026-01-05T01:00:00Z",
        as_of_cutoff="2026-01-05T01:00:00Z",
    )
    valid_result = _result(result_available_at="2026-01-04T00:00:00Z")
    future_finished_result = record_with_digest(
        replace(
            valid_result,
            finished_at="2026-01-04T20:30:00-05:00",
            result_available_at="2026-01-05T00:30:00Z",
            result_digest="",
        )
    )

    with pytest.raises(ValueError, match="invalid ResultRecord"):
        build_feature_snapshot(
            origin,
            task_pool,
            (_task("task-old", "check-old"),),
            {"check-old": _check("check-old", "task-old")},
            (future_finished_result,),
            FeatureConfig("features", "leakage"),
        )


def test_build_selector_input_rejects_off_history_or_wrong_agent_results() -> None:
    task_pool = _task_pool(("task-old", "task-other"), ("check-old", "check-other"))
    origin = _origin(task_pool)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"), _task("task-other", "check-other")),
        {"check-old": _check("check-old", "task-old"), "check-other": _check("check-other", "task-other")},
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",)),
    )

    with pytest.raises(ValueError, match="outside origin history"):
        build_selector_input(
            origin,
            task_pool,
            snapshot,
            (_result(result_available_at="2026-01-04T00:00:00Z", task_id="task-other", check_id="check-other"),),
            (_agent(),),
            SelectionBudget("budget", 1),
            LeakagePolicy("leakage", ("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
        )

    with pytest.raises(ValueError, match="outside candidate Agent"):
        build_selector_input(
            origin,
            task_pool,
            snapshot,
            (_result(result_available_at="2026-01-04T00:00:00Z", agent_id="other-agent"),),
            (_agent(),),
            SelectionBudget("budget", 1),
            LeakagePolicy("leakage", ("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
        )


def test_build_selector_input_rejects_result_feature_provenance_mismatch() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (_result(result_available_at="2026-01-04T00:00:00Z", agent_id="other-agent"),),
        FeatureConfig("features", "leakage", ("pre_origin_result_count",), ("pre_origin_result",)),
    )

    with pytest.raises(ValueError, match="result provenance"):
        build_selector_input(
            origin,
            task_pool,
            snapshot,
            (_result(result_available_at="2026-01-04T00:00:00Z", agent_id="agent"),),
            (_agent("agent"),),
            SelectionBudget("budget", 1),
            LeakagePolicy("leakage", ("pre_origin_result",), origin.as_of_cutoff),
        )


def test_build_selector_input_rejects_invalid_result_records() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    valid_result = _result(result_available_at="2026-01-04T00:00:00Z")
    bad_digest_result = replace(valid_result, result_digest="not-the-canonical-digest")

    with pytest.raises(ValueError, match="invalid ResultRecord"):
        build_feature_snapshot(
            origin,
            task_pool,
            (_task("task-old", "check-old"),),
            {"check-old": _check("check-old", "task-old")},
            (bad_digest_result,),
            FeatureConfig("features", "leakage"),
        )

    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (valid_result,),
        FeatureConfig("features", "leakage"),
    )
    with pytest.raises(ValueError, match="invalid ResultRecord"):
        build_selector_input(
            origin,
            task_pool,
            snapshot,
            (_result_with_mismatched_identity(valid_result),),
            (_agent(),),
            SelectionBudget("budget", 1),
            LeakagePolicy("leakage", ("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
        )


def test_build_selector_input_rejects_stale_check_or_wrong_agent_identity() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    valid_result = _result(result_available_at="2026-01-04T00:00:00Z")

    with pytest.raises(ValueError, match="current Task/Check"):
        build_feature_snapshot(
            origin,
            task_pool,
            (_task("task-old", "check-old"),),
            {"check-old": _check("check-old", "task-old")},
            (_result_with_stale_check_identity(valid_result),),
            FeatureConfig("features", "leakage"),
        )

    wrong_agent_result = _result_with_wrong_agent_identity(valid_result)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (wrong_agent_result,),
        FeatureConfig("features", "leakage"),
    )
    with pytest.raises(ValueError, match="candidate Agent"):
        build_selector_input(
            origin,
            task_pool,
            snapshot,
            (wrong_agent_result,),
            (_agent(),),
            SelectionBudget("budget", 1),
            LeakagePolicy("leakage", ("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
        )


def test_lint_feature_snapshot_rejects_disallowed_leakage_class() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (_result(result_available_at="2026-01-04T00:00:00Z", agent_id="agent-a"),),
        FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",)),
    )

    result = lint_feature_snapshot(snapshot, LeakagePolicy("leakage", ("pre_origin_result",), origin.as_of_cutoff))

    assert not result.ok
    assert "feature leakage_class is not allowed" in result.errors
    assert snapshot.feature_records


def test_select_with_selector_freezes_common_refs_weights_and_task_pool_digest() -> None:
    task_pool = _task_pool(("task-old", "task-new"), ("check-old", "check-new"))
    origin = _origin(
        task_pool,
        refs=(TaskCheckRef("task-old", "check-old"), TaskCheckRef("task-new", "check-new")),
    )
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"), _task("task-new", "check-new")),
        {"check-old": _check("check-old", "task-old"), "check-new": _check("check-new", "task-new")},
        (_result(result_available_at="2026-01-04T00:00:00Z", agent_id="agent-a"),),
        FeatureConfig("features", "leakage"),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (_result(result_available_at="2026-01-04T00:00:00Z", agent_id="agent-a"),),
        (_agent("agent-a"), _agent("agent-b")),
        SelectionBudget("budget", 1),
        LeakagePolicy("leakage", ("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
    )
    selector = _selector("selector-recency", "recency")

    selection = select_with_selector(
        selector_input,
        selector,
        SelectionConfig("selection-config", selector.selector_id, snapshot.feature_snapshot_id, "strict_history"),
    )

    assert validate_benchmark_selection(selection).ok
    assert selection.task_pool_digest == task_pool.task_pool_digest
    assert selection.exposure_state == "frozen"
    assert selection.selected_task_check_refs == (TaskCheckRef("task-new", "check-new"),)
    assert set(selection.selected_weights) == {canonical_digest(TaskCheckRef("task-new", "check-new"))}


def test_rule_mixture_coverage_score_round_robins_across_groups() -> None:
    refs = (
        TaskCheckRef("task-a-1", "check-a-1"),
        TaskCheckRef("task-a-2", "check-a-2"),
        TaskCheckRef("task-b-1", "check-b-1"),
    )
    task_pool = _task_pool(
        tuple(ref.task_id for ref in refs),
        tuple(ref.check_id for ref in refs),
    )
    origin = _origin(task_pool, refs=refs)
    tasks = tuple(_task(ref.task_id, ref.check_id) for ref in refs)
    checks = {ref.check_id: _check(ref.check_id, ref.task_id) for ref in refs}
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        tasks,
        checks,
        (),
        FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",)),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (),
        (_agent(),),
        SelectionBudget("budget", 2),
        LeakagePolicy("leakage", ("task_metadata",), origin.as_of_cutoff),
    )
    parameters = {
        "expert_weights": {"coverage": 1.0},
        "random_seed": 7,
        "group_by_ref_key": {
            canonical_digest(refs[0]): "group-a",
            canonical_digest(refs[1]): "group-a",
            canonical_digest(refs[2]): "group-b",
        },
    }

    selection = select_rule_mixture(
        selector_input,
        parameters,
        SelectionConfig(
            "selection-config",
            "selector-rule-mixture",
            snapshot.feature_snapshot_id,
            "strict_history",
        ),
    )

    assert selection.selected_task_check_refs == (refs[0], refs[2])


@pytest.mark.parametrize(
    ("expert_weights", "error"),
    [
        ({"coverage": -1.0}, "finite nonnegative"),
        ({"coverage": float("inf")}, "finite nonnegative"),
        ({"coverage": 10**400}, "finite nonnegative"),
        ({"coverage": 1e308, "recency": 1e308}, "must include a positive"),
        ({"coverage": 1.0, "typo": 1.0}, "unsupported rule-mixture experts"),
    ],
)
def test_rule_mixture_rejects_invalid_expert_weights(
    expert_weights: dict[str, float],
    error: str,
) -> None:
    refs = (TaskCheckRef("task-a", "check-a"),)
    task_pool = _task_pool(("task-a",), ("check-a",))
    origin = _origin(task_pool, refs=refs)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-a", "check-a"),),
        {"check-a": _check("check-a", "task-a")},
        (),
        FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",)),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (),
        (_agent(),),
        SelectionBudget("budget", 1),
        LeakagePolicy("leakage", ("task_metadata",), origin.as_of_cutoff),
    )

    with pytest.raises(ValueError, match=error):
        select_rule_mixture(
            selector_input,
            {
                "expert_weights": expert_weights,
                "random_seed": 7,
                "group_by_ref_key": {},
            },
            SelectionConfig(
                "selection-config",
                "selector-rule-mixture",
                snapshot.feature_snapshot_id,
                "strict_history",
            ),
        )


def test_select_with_selector_replays_random_parameters_from_selector() -> None:
    refs = tuple(
        TaskCheckRef(f"task-{index}", f"check-{index}")
        for index in range(3)
    )
    task_pool = _task_pool(
        tuple(ref.task_id for ref in refs),
        tuple(ref.check_id for ref in refs),
    )
    origin = _origin(task_pool, refs=refs)
    tasks = tuple(_task(ref.task_id, ref.check_id) for ref in refs)
    checks = {ref.check_id: _check(ref.check_id, ref.task_id) for ref in refs}
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        tasks,
        checks,
        (),
        FeatureConfig("features", "leakage", ("task_count",), ("task_metadata",)),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (),
        (_agent(),),
        SelectionBudget("budget", 2),
        LeakagePolicy("leakage", ("task_metadata",), origin.as_of_cutoff),
    )
    selector = _selector("selector-random-v1", "random")

    first = select_with_selector(
        selector_input,
        selector,
        SelectionConfig("freeze-a", selector.selector_id, snapshot.feature_snapshot_id, "strict_history"),
    )
    second = select_with_selector(
        selector_input,
        selector,
        SelectionConfig("freeze-b", selector.selector_id, snapshot.feature_snapshot_id, "strict_history"),
    )
    mixture = select_rule_mixture(
        selector_input,
        {
            "expert_weights": {"random": 1.0},
            "random_seed": 7,
            "group_by_ref_key": {},
        },
        SelectionConfig(
            "freeze-mixture",
            "selector-rule-mixture",
            snapshot.feature_snapshot_id,
            "strict_history",
        ),
    )

    assert selector.parameters == {"seed": 7}
    assert first.selector_id == "selector-random-v1"
    assert first.selected_task_check_refs == second.selected_task_check_refs
    assert mixture.selected_task_check_refs == first.selected_task_check_refs


def test_select_with_selector_rejects_selector_or_feature_snapshot_mismatch() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        FeatureConfig("features", "leakage"),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        (_agent(),),
        SelectionBudget("budget", 1),
        LeakagePolicy("leakage", ("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
    )
    selector = _selector("selector-recency", "recency")

    with pytest.raises(ValueError, match="selector_id"):
        select_with_selector(
            selector_input,
            selector,
            SelectionConfig("selection-config", "other-selector", snapshot.feature_snapshot_id, "strict_history"),
        )

    with pytest.raises(ValueError, match="feature_snapshot_id"):
        select_with_selector(
            selector_input,
            selector,
            SelectionConfig("selection-config", selector.selector_id, "other-snapshot", "strict_history"),
        )


def test_select_with_selector_rejects_invalid_tampered_selector_input() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        FeatureConfig("features", "leakage"),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        (_agent(),),
        SelectionBudget("budget", 1),
        LeakagePolicy("leakage", ("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
    )
    tampered_input = record_with_digest(replace(selector_input, feature_snapshot_lint_status="failed", selector_input_digest=""))

    with pytest.raises(ValueError, match="selector input is invalid"):
        select_with_selector(
            tampered_input,
            _selector("selector-recency", "recency"),
            SelectionConfig("selection-config", "selector-recency", snapshot.feature_snapshot_id, "strict_history"),
        )


def test_select_with_selector_rejects_unsupported_selector_family() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        FeatureConfig("features", "leakage"),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        (_agent(),),
        SelectionBudget("budget", 1),
        LeakagePolicy("leakage", ("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
    )
    selector = _selector("selector-unsupported", "unsupported")

    with pytest.raises(ValueError, match="unsupported selector family"):
        select_with_selector(
            selector_input,
            selector,
            SelectionConfig("selection-config", selector.selector_id, snapshot.feature_snapshot_id, "strict_history"),
        )


def test_freeze_evaluation_selections_does_not_accept_future_results() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        FeatureConfig("features", "leakage"),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        (_agent(),),
        SelectionBudget("budget", 1),
        LeakagePolicy("leakage", ("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
    )
    selector = _selector("selector-recency", "recency")

    selections = freeze_evaluation_selections(
        selector,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (selector_input,),
        (_agent(),),
        TimeRange("2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z"),
        SelectionConfig("selection-config", selector.selector_id, snapshot.feature_snapshot_id, "strict_history"),
        _rolling_policy(),
    )

    assert len(selections) == 1
    assert validate_benchmark_selection(selections[0]).ok


def test_freeze_evaluation_selections_rejects_valid_input_with_future_ref() -> None:
    task_pool = _task_pool(("task-old", "future-task"), ("check-old", "future-check"))
    origin = _origin(task_pool)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"), _task("future-task", "future-check", available_at="2026-01-07T00:00:00Z")),
        {"check-old": _check("check-old", "task-old"), "future-check": _check("future-check", "future-task", available_at="2026-01-07T00:00:00Z")},
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        FeatureConfig("features", "leakage"),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        (_agent(),),
        SelectionBudget("budget", 1),
        LeakagePolicy("leakage", ("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
    )
    future_ref = TaskCheckRef("future-task", "future-check")
    future_ref_input = replace(
        selector_input,
        eligible_task_check_refs=(future_ref,),
        origin_history_refs_digest=canonical_digest((future_ref,)),
        selector_input_id="",
        selector_input_digest="",
    )
    future_ref_input = record_with_digest(replace(future_ref_input, selector_input_id=make_selector_input_id(future_ref_input)))

    with pytest.raises(ValueError, match="outside history window"):
        freeze_evaluation_selections(
            _selector("selector-recency", "recency"),
            task_pool,
            (_task("task-old", "check-old"), _task("future-task", "future-check", available_at="2026-01-07T00:00:00Z")),
            {"check-old": _check("check-old", "task-old"), "future-check": _check("future-check", "future-task", available_at="2026-01-07T00:00:00Z")},
            (future_ref_input,),
            (_agent(),),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z"),
            SelectionConfig("selection-config", "selector-recency", snapshot.feature_snapshot_id, "strict_history"),
            _rolling_policy(),
        )


def test_freeze_evaluation_selections_rejects_incomplete_history_denominator() -> None:
    refs = (
        TaskCheckRef("task-a", "check-a"),
        TaskCheckRef("task-b", "check-b"),
    )
    task_pool = _task_pool(
        tuple(ref.task_id for ref in refs),
        tuple(ref.check_id for ref in refs),
    )
    origin = _origin(task_pool, refs)
    tasks = (
        _task("task-a", "check-a"),
        _task("task-b", "check-b", available_at="2026-01-03T00:00:00Z"),
    )
    checks = {
        "check-a": _check("check-a", "task-a"),
        "check-b": _check(
            "check-b", "task-b", available_at="2026-01-03T00:00:00Z"
        ),
    }
    result = _result(
        result_available_at="2026-01-04T00:00:00Z",
        task_id="task-a",
        check_id="check-a",
    )
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        tasks,
        checks,
        (result,),
        FeatureConfig("features", "leakage"),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (result,),
        (_agent(),),
        SelectionBudget("budget", 1),
        LeakagePolicy(
            "leakage",
            ("task_metadata", "pre_origin_result"),
            origin.as_of_cutoff,
        ),
    )
    narrowed = replace(
        selector_input,
        eligible_task_check_refs=(refs[0],),
        origin_history_refs_digest=canonical_digest((refs[0],)),
        selector_input_id="",
        selector_input_digest="",
    )
    narrowed = record_with_digest(
        replace(narrowed, selector_input_id=make_selector_input_id(narrowed))
    )

    with pytest.raises(ValueError, match="complete chronological history"):
        freeze_evaluation_selections(
            _selector("selector-recency", "recency"),
            task_pool,
            tasks,
            checks,
            (narrowed,),
            (_agent(),),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z"),
            SelectionConfig(
                "selection-config",
                "selector-recency",
                snapshot.feature_snapshot_id,
                "strict_history",
            ),
            _rolling_policy(),
        )


def test_train_selector_persists_executable_rule_parameters() -> None:
    parameters = {"seed": 11}

    selector = train_selector(
        _task_pool(("task-old",), ("check-old",)),
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (),
        (_agent(),),
        TimeRange("2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z"),
        (),
        __import__("barcarolle.selection", fromlist=["SelectorTrainingConfig"]).SelectorTrainingConfig(
            "training",
            "random",
            parameters,
        ),
        _rolling_policy(),
        FeatureConfig("features", "leakage"),
    )

    assert selector.parameters == parameters
    assert selector.config_digest == canonical_digest(
        {"selector_family": "random", "parameters": parameters}
    )


def test_train_selector_rejects_unsupported_family() -> None:
    with pytest.raises(ValueError, match="unsupported selector family"):
        train_selector(
            _task_pool(("task-old",), ("check-old",)),
            (_task("task-old", "check-old"),),
            {"check-old": _check("check-old", "task-old")},
            (),
            (_agent(),),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z"),
            (),
            __import__("barcarolle.selection", fromlist=["SelectorTrainingConfig"]).SelectorTrainingConfig(
                "training",
                "unsupported",
            ),
            _rolling_policy(),
            FeatureConfig("features", "leakage"),
        )


def test_train_selector_rejects_post_origin_training_results() -> None:
    with pytest.raises(ValueError, match="after the origin cutoff"):
        train_selector(
            _task_pool(("task-old",), ("check-old",)),
            (_task("task-old", "check-old"),),
            {"check-old": _check("check-old", "task-old")},
            (_result(result_available_at="2026-01-06T00:00:00Z"),),
            (_agent(),),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z"),
            (),
            __import__("barcarolle.selection", fromlist=["SelectorTrainingConfig"]).SelectorTrainingConfig("training"),
            _rolling_policy(),
            FeatureConfig("features", "leakage"),
        )


def test_train_selector_rejects_wrong_agent_training_results() -> None:
    with pytest.raises(ValueError, match="outside candidate Agent"):
        train_selector(
            _task_pool(("task-old",), ("check-old",)),
            (_task("task-old", "check-old"),),
            {"check-old": _check("check-old", "task-old")},
            (_result(result_available_at="2026-01-04T00:00:00Z", agent_id="other-agent"),),
            (_agent("agent"),),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z"),
            (),
            __import__("barcarolle.selection", fromlist=["SelectorTrainingConfig"]).SelectorTrainingConfig("training"),
            _rolling_policy(),
            FeatureConfig("features", "leakage"),
        )


def test_train_selector_rejects_invalid_result_records() -> None:
    valid_result = _result(result_available_at="2026-01-04T00:00:00Z")
    for invalid_result in (
        replace(valid_result, result_digest="not-the-canonical-digest"),
        _result_with_mismatched_identity(valid_result),
    ):
        with pytest.raises(ValueError, match="invalid ResultRecord"):
            train_selector(
                _task_pool(("task-old",), ("check-old",)),
                (_task("task-old", "check-old"),),
                {"check-old": _check("check-old", "task-old")},
                (invalid_result,),
                (_agent(),),
                TimeRange("2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z"),
                (),
                __import__("barcarolle.selection", fromlist=["SelectorTrainingConfig"]).SelectorTrainingConfig("training"),
                _rolling_policy(),
                FeatureConfig("features", "leakage"),
            )


def test_train_selector_rejects_stale_check_or_wrong_agent_identity() -> None:
    valid_result = _result(result_available_at="2026-01-04T00:00:00Z")
    for invalid_result, message in (
        (_result_with_stale_check_identity(valid_result), "current Task/Check"),
        (_result_with_wrong_agent_identity(valid_result), "candidate Agent"),
    ):
        with pytest.raises(ValueError, match=message):
            train_selector(
                _task_pool(("task-old",), ("check-old",)),
                (_task("task-old", "check-old"),),
                {"check-old": _check("check-old", "task-old")},
                (invalid_result,),
                (_agent(),),
                TimeRange("2026-01-01T00:00:00Z", "2026-01-05T00:00:00Z"),
                (),
                __import__("barcarolle.selection", fromlist=["SelectorTrainingConfig"]).SelectorTrainingConfig("training"),
                _rolling_policy(),
                FeatureConfig("features", "leakage"),
            )


def test_choose_selector_by_mean_mae_averages_prepared_origin_rows() -> None:
    fallback = _selector("selector-fallback", "recency")
    selector_a = _selector("selector-a", "coverage")
    selector_b = _selector("selector-b", "random")
    rows = (
        {fallback.selector_id: 0.5, selector_a.selector_id: 0.2, selector_b.selector_id: 0.3},
        {fallback.selector_id: 0.4, selector_a.selector_id: 0.4, selector_b.selector_id: 0.5},
    )

    chosen = choose_selector_by_mean_mae(
        (fallback, selector_a, selector_b),
        rows,
        fallback.selector_id,
    )

    assert chosen == selector_a


def test_choose_selector_by_mean_mae_uses_fallback_only_without_history() -> None:
    fallback = _selector("selector-fallback", "recency")
    candidate = _selector("selector-candidate", "random")

    chosen = choose_selector_by_mean_mae(
        (fallback, candidate),
        (),
        fallback.selector_id,
    )

    assert chosen == fallback


def test_choose_selector_by_mean_mae_rejects_unpaired_rows() -> None:
    fallback = _selector("selector-fallback", "recency")
    candidate = _selector("selector-candidate", "coverage")

    with pytest.raises(ValueError, match="cover every registered selector"):
        choose_selector_by_mean_mae(
            (fallback, candidate),
            ({candidate.selector_id: 0.1},),
            fallback.selector_id,
        )


@pytest.mark.parametrize("value", (float("nan"), float("inf"), -0.1, 1.1, True))
def test_choose_selector_by_mean_mae_rejects_invalid_values(value: float) -> None:
    selector = _selector("selector", "recency")

    with pytest.raises(ValueError, match="between 0 and 1"):
        choose_selector_by_mean_mae(
            (selector,),
            ({selector.selector_id: value},),
            selector.selector_id,
        )


def test_choose_selector_by_mean_mae_rejects_invalid_registration() -> None:
    duplicate_a = _selector("duplicate", "recency")
    duplicate_b = _selector("duplicate", "random")

    with pytest.raises(ValueError, match="must be unique"):
        choose_selector_by_mean_mae((duplicate_a, duplicate_b), (), duplicate_a.selector_id)

    with pytest.raises(ValueError, match="fallback_selector_id is not registered"):
        choose_selector_by_mean_mae((_selector("selector", "recency"),), (), "missing")

    with pytest.raises(ValueError, match="unsupported selector family"):
        choose_selector_by_mean_mae(
            (_selector("selector-unsupported", "unsupported"),),
            (),
            "selector-unsupported",
        )

    invalid_random = replace(
        _selector("selector-random", "random"),
        parameters={},
        config_digest=canonical_digest(
            {"selector_family": "random", "parameters": {}}
        ),
    )
    with pytest.raises(ValueError, match="seed"):
        choose_selector_by_mean_mae(
            (invalid_random,),
            (),
            invalid_random.selector_id,
        )


def test_choose_selector_from_metrics_pairs_complete_origin_rows() -> None:
    selector_a = _selector("selector-a", "recency")
    selector_b = _selector("selector-b", "coverage")
    selections = (
        _selection_for_metric("origin-2", selector_b.selector_id),
        _selection_for_metric("origin-1", selector_a.selector_id),
        _selection_for_metric("origin-2", selector_a.selector_id),
        _selection_for_metric("origin-1", selector_b.selector_id),
    )
    values = {
        ("origin-1", selector_a.selector_id): 0.2,
        ("origin-1", selector_b.selector_id): 0.5,
        ("origin-2", selector_a.selector_id): 0.4,
        ("origin-2", selector_b.selector_id): 0.3,
    }
    metrics = tuple(
        _mae_metric(selection, values[(selection.origin_id, selection.selector_id)])
        for selection in reversed(selections)
    )

    chosen = choose_selector_from_metrics(
        (selector_b, selector_a),
        selections,
        metrics,
        _future_matrices(selections),
        selector_b.selector_id,
    )

    assert chosen == selector_a


def test_choose_selector_from_metrics_uses_fallback_without_prior_origins() -> None:
    fallback = _selector("selector-fallback", "recency")

    chosen = choose_selector_from_metrics(
        (fallback,),
        (),
        (),
        (),
        fallback.selector_id,
    )

    assert chosen == fallback


@pytest.mark.parametrize("missing", ("selections", "metrics", "matrices"))
def test_choose_selector_from_metrics_rejects_one_sided_evidence(missing: str) -> None:
    selector = _selector("selector", "recency")
    selection = _selection_for_metric("origin-1", selector.selector_id)
    metric = _mae_metric(selection, 0.2)
    future_matrix = _future_matrix_for_metric(selection)

    with pytest.raises(ValueError, match="must all be provided"):
        choose_selector_from_metrics(
            (selector,),
            () if missing == "selections" else (selection,),
            () if missing == "metrics" else (metric,),
            () if missing == "matrices" else (future_matrix,),
            selector.selector_id,
        )


def test_choose_selector_from_metrics_rejects_missing_selector_at_origin() -> None:
    selector_a = _selector("selector-a", "recency")
    selector_b = _selector("selector-b", "coverage")
    selection = _selection_for_metric("origin-1", selector_a.selector_id)

    with pytest.raises(ValueError, match="origin-1 is missing registered selectors: selector-b"):
        choose_selector_from_metrics(
            (selector_a, selector_b),
            (selection,),
            (_mae_metric(selection, 0.2),),
            (_future_matrix_for_metric(selection),),
            selector_a.selector_id,
        )


@pytest.mark.parametrize("duplicate", ("selection", "metric"))
def test_choose_selector_from_metrics_rejects_duplicates(duplicate: str) -> None:
    selector = _selector("selector", "recency")
    selection = _selection_for_metric("origin-1", selector.selector_id)
    metric = _mae_metric(selection, 0.2)
    selections = (selection, selection) if duplicate == "selection" else (selection,)
    metrics = (metric, metric) if duplicate == "metric" else (metric,)

    with pytest.raises(ValueError, match=f"duplicate {duplicate}"):
        choose_selector_from_metrics(
            (selector,),
            selections,
            metrics,
            (_future_matrix_for_metric(selection),),
            selector.selector_id,
        )


def test_choose_selector_from_metrics_rejects_incomparable_metrics() -> None:
    selector = _selector("selector", "recency")
    first = _selection_for_metric("origin-1", selector.selector_id)
    second = _selection_for_metric("origin-2", selector.selector_id)
    first_metric = _mae_metric(first, 0.2)
    second_metric = _mae_metric(second, 0.3)
    incompatible_cases = (
        (replace(second, budget_digest="other-budget", selection_digest=""), second_metric, "budget"),
        (second, replace(second_metric, metric_name="other-metric", metric_digest=""), "future_pass_rate_mae"),
        (second, replace(second_metric, metric_config_digest="other-config", metric_digest=""), "metric configuration"),
    )

    for changed_selection, changed_metric, message in incompatible_cases:
        changed_selection = record_with_digest(changed_selection)
        changed_metric = record_with_digest(changed_metric)
        with pytest.raises(ValueError, match=message):
            choose_selector_from_metrics(
                (selector,),
                (first, changed_selection),
                (first_metric, changed_metric),
                _future_matrices((first, changed_selection)),
                selector.selector_id,
            )


def test_choose_selector_from_metrics_requires_same_origin_input_and_task_pool() -> None:
    selector_a = _selector("selector-a", "recency")
    selector_b = _selector("selector-b", "coverage")
    first = _selection_for_metric("origin-1", selector_a.selector_id)
    mismatched_input = record_with_digest(
        replace(
            _selection_for_metric("origin-1", selector_b.selector_id),
            selection_input_digest="other-input",
            selection_digest="",
        )
    )
    with pytest.raises(ValueError, match="origin origin-1 must use one selection input"):
        choose_selector_from_metrics(
            (selector_a, selector_b),
            (first, mismatched_input),
            (_mae_metric(first, 0.2), _mae_metric(mismatched_input, 0.3)),
            _future_matrices((first, mismatched_input)),
            selector_a.selector_id,
        )

    second_origin = record_with_digest(
        replace(
            _selection_for_metric("origin-2", selector_a.selector_id),
            task_pool_id="other-task-pool",
            task_pool_digest="other-task-pool-digest",
            selection_digest="",
        )
    )
    with pytest.raises(ValueError, match="one task pool"):
        choose_selector_from_metrics(
            (selector_a,),
            (first, second_origin),
            (_mae_metric(first, 0.2), _mae_metric(second_origin, 0.3)),
            _future_matrices((first, second_origin)),
            selector_a.selector_id,
        )


def test_choose_selector_from_metrics_allows_completeness_to_differ_across_origins() -> None:
    selector = _selector("selector", "recency")
    first = _selection_for_metric("origin-1", selector.selector_id)
    second = _selection_for_metric("origin-2", selector.selector_id)
    second_metric = record_with_digest(
        replace(
            _mae_metric(second, 0.3),
            completeness_state="complete_with_exclusions",
            metric_digest="",
        )
    )

    chosen = choose_selector_from_metrics(
        (selector,),
        (first, second),
        (_mae_metric(first, 0.2), second_metric),
        _future_matrices((first, second)),
        selector.selector_id,
    )

    assert chosen == selector


def test_choose_selector_from_metrics_requires_one_completeness_state_within_origin() -> None:
    selector_a = _selector("selector-a", "recency")
    selector_b = _selector("selector-b", "coverage")
    first = _selection_for_metric("origin-1", selector_a.selector_id)
    second = _selection_for_metric("origin-1", selector_b.selector_id)
    second_metric = record_with_digest(
        replace(
            _mae_metric(second, 0.3),
            completeness_state="complete_with_exclusions",
            metric_digest="",
        )
    )

    with pytest.raises(ValueError, match="origin origin-1 must have one completeness state"):
        choose_selector_from_metrics(
            (selector_a, selector_b),
            (first, second),
            (_mae_metric(first, 0.2), second_metric),
            _future_matrices((first, second)),
            selector_a.selector_id,
        )


def test_choose_selector_from_metrics_requires_shared_future_result_evidence() -> None:
    selector_a = _selector("selector-a", "recency")
    selector_b = _selector("selector-b", "coverage")
    first = _selection_for_metric("origin-1", selector_a.selector_id)
    second = _selection_for_metric("origin-1", selector_b.selector_id)
    first_matrix = _future_matrix_for_metric(first)
    second_matrix = _future_matrix_for_metric(
        second,
        result_id="different-future-result",
        result_digest="different-future-result-digest",
    )

    with pytest.raises(ValueError, match="same Result evidence"):
        choose_selector_from_metrics(
            (selector_a, selector_b),
            (first, second),
            (
                _mae_metric(first, 0.2, first_matrix),
                _mae_metric(second, 0.3, second_matrix),
            ),
            (first_matrix, second_matrix),
            selector_a.selector_id,
        )


def test_fit_rule_mixture_from_metrics_learns_weights_and_inherits_parameters() -> None:
    coverage_parameters = {
        "group_by_ref_key": {"task-old::check-old": "group-a"},
    }
    coverage = replace(
        _selector("selector-coverage", "coverage"),
        allowed_feature_classes=("task_metadata",),
        parameters=coverage_parameters,
        config_digest=canonical_digest(
            {"selector_family": "coverage", "parameters": coverage_parameters}
        ),
    )
    random_parameters = {"seed": 41}
    random = replace(
        _selector("selector-random", "random"),
        parameters=random_parameters,
        config_digest=canonical_digest(
            {"selector_family": "random", "parameters": random_parameters}
        ),
    )
    recency = replace(
        _selector("selector-recency", "recency"),
        allowed_feature_classes=("pre_origin_result",),
    )
    experts = (random, recency, coverage)
    values = {
        ("origin-1", coverage.selector_id): 0.2,
        ("origin-2", coverage.selector_id): 0.4,
        ("origin-1", random.selector_id): 0.1,
        ("origin-2", random.selector_id): 0.3,
        ("origin-1", recency.selector_id): 0.6,
        ("origin-2", recency.selector_id): 0.8,
    }
    selections = tuple(
        _selection_for_metric(origin_id, selector.selector_id)
        for origin_id in ("origin-2", "origin-1")
        for selector in experts
    )
    metrics = tuple(
        _mae_metric(selection, values[(selection.origin_id, selection.selector_id)])
        for selection in reversed(selections)
    )

    fitted = fit_rule_mixture_from_metrics(
        experts,
        selections,
        metrics,
        _future_matrices(selections),
    )

    assert fitted.selector_family == "rule_mixture"
    assert fitted.selector_version == "1"
    assert fitted.allowed_feature_classes == ("pre_origin_result", "task_metadata")
    weights = fitted.parameters["expert_weights"]
    assert isinstance(weights, dict)
    assert weights == pytest.approx({"coverage": 0.7, "random": 0.8, "recency": 0.3})
    assert fitted.parameters["random_seed"] == 41
    assert fitted.parameters["group_by_ref_key"] == coverage_parameters["group_by_ref_key"]
    assert fitted.training_source_digests == (
        canonical_digest(
            {
                "expert_selectors": tuple(
                    canonical_digest(selector)
                    for selector in (coverage, random, recency)
                )
            }
        ),
        canonical_digest(
            {"selections": tuple(sorted(selection.selection_digest for selection in selections))}
        ),
        canonical_digest(
            {"mae_metrics": tuple(sorted(metric.metric_digest for metric in metrics))}
        ),
    )


def test_fit_rule_mixture_from_metrics_uses_equal_weights_when_all_experts_have_mae_one() -> None:
    experts = (
        _selector("selector-coverage", "coverage"),
        _selector("selector-random", "random"),
        _selector("selector-recency", "recency"),
    )
    selections = tuple(
        _selection_for_metric("origin-1", selector.selector_id) for selector in experts
    )
    metrics = tuple(_mae_metric(selection, 1.0) for selection in selections)

    fitted = fit_rule_mixture_from_metrics(
        experts,
        selections,
        metrics,
        _future_matrices(selections),
    )

    assert fitted.parameters["expert_weights"] == {
        "coverage": 1.0,
        "random": 1.0,
        "recency": 1.0,
    }


def test_fit_rule_mixture_from_metrics_requires_exact_experts_and_paired_evidence() -> None:
    coverage = _selector("selector-coverage", "coverage")
    random = _selector("selector-random", "random")
    recency = _selector("selector-recency", "recency")

    with pytest.raises(ValueError, match="exactly one coverage, random, and recency"):
        fit_rule_mixture_from_metrics((coverage, random, random), (), (), ())

    with pytest.raises(ValueError, match="paired MAE evidence is required"):
        fit_rule_mixture_from_metrics((coverage, random, recency), (), (), ())

    selections = (
        _selection_for_metric("origin-1", coverage.selector_id),
        _selection_for_metric("origin-1", random.selector_id),
    )
    metrics = tuple(_mae_metric(selection, 0.2) for selection in selections)
    with pytest.raises(ValueError, match="missing registered selectors: selector-recency"):
        fit_rule_mixture_from_metrics(
            (coverage, random, recency),
            selections,
            metrics,
            _future_matrices(selections),
        )

    complete_selections = tuple(
        _selection_for_metric("origin-1", selector.selector_id)
        for selector in (coverage, random, recency)
    )
    invalid_metrics = tuple(
        _mae_metric(selection, 1.1 if selection.selector_id == coverage.selector_id else 0.2)
        for selection in complete_selections
    )
    with pytest.raises(ValueError, match="between 0 and 1"):
        fit_rule_mixture_from_metrics(
            (coverage, random, recency),
            complete_selections,
            invalid_metrics,
            _future_matrices(complete_selections),
        )


def test_evaluate_selection_emits_invalid_metric_for_matrix_alignment_failure() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    selected_matrix = _matrix(origin, selection, cell_set, role="selected")
    future_matrix = _matrix(origin, selection, cell_set, role="selected")

    metrics = evaluate_selection(selection, origin, cell_set, selected_matrix, future_matrix, MetricConfig("metric-config"))

    assert len(metrics) == 1
    assert validate_metric(metrics[0]).ok
    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].abstention_reason == "matrix_role_mismatch"


def test_evaluate_selection_applies_selected_weights_to_pass_rate_mae() -> None:
    selected_refs = (TaskCheckRef("task-a", "check-a"), TaskCheckRef("task-b", "check-b"))
    future_refs = (TaskCheckRef("future-task", "future-check"),)
    task_pool = _task_pool(("task-a", "task-b", "future-task"), ("check-a", "check-b", "future-check"))
    origin = _origin(task_pool, refs=selected_refs)
    selection = record_with_digest(
        BenchmarkSelectionRecord(
            selection_id="weighted-selection",
            task_pool_id=task_pool.task_pool_id,
            task_pool_digest=task_pool.task_pool_digest,
            origin_id=origin.origin_id,
            selector_id="selector",
            selected_task_check_refs=selected_refs,
            selected_weights={canonical_digest(selected_refs[0]): 0.9, canonical_digest(selected_refs[1]): 0.1},
            budget_digest="budget",
            selection_input_digest="selector-input",
            feature_snapshot_id="feature-snapshot",
            eligibility_mode="strict_history",
            exposure_state="frozen",
            exposed_at=None,
            exposure_scope_digest=None,
            created_at="2026-01-05T00:00:00Z",
            selection_digest="",
        )
    )
    cells = (
        ResultCellRef("agent", "task-a", "check-a", "identity-a", "result-a", "digest-a", "result", None, "fail"),
        ResultCellRef("agent", "task-b", "check-b", "identity-b", "result-b", "digest-b", "result", None, "pass"),
        ResultCellRef("agent", "future-task", "future-check", "future-identity", "future-result", "future-digest", "result", None, "pass"),
    )
    cell_set = record_with_digest(
        EvaluationCellSet(
            cell_set_id="weighted-cells",
            origin_id=origin.origin_id,
            selection_id=selection.selection_id,
            selected_task_check_refs=selected_refs,
            future_task_check_refs=future_refs,
            cells=cells,
            abstention_reason=None,
            cell_set_digest="",
        )
    )
    selected_matrix = record_with_digest(
        ResultMatrix(
            matrix_id="weighted-selected",
            matrix_role="selected",
            origin_id=origin.origin_id,
            selection_id=selection.selection_id,
            agent_ids=("agent",),
            task_check_refs=selected_refs,
            cells=cells[:2],
            join_policy_digest="join",
            denominator_policy_digest="denominator",
            abstention_reason=None,
            scoreable_state="complete",
            matrix_digest="",
        )
    )
    future_matrix = record_with_digest(
        ResultMatrix(
            matrix_id="weighted-future",
            matrix_role="future_holdout",
            origin_id=origin.origin_id,
            selection_id=selection.selection_id,
            agent_ids=("agent",),
            task_check_refs=future_refs,
            cells=cells[2:],
            join_policy_digest="join",
            denominator_policy_digest="denominator",
            abstention_reason=None,
            scoreable_state="complete",
            matrix_digest="",
        )
    )

    metrics = evaluate_selection(selection, origin, cell_set, selected_matrix, future_matrix, MetricConfig("metric-config"))
    metrics_by_name = {metric.metric_name: metric.metric_value for metric in metrics}

    assert metrics[0].metric_name == "future_pass_rate_mae"
    assert metrics[0].metric_value == pytest.approx(0.9)
    assert metrics_by_name["pairwise_gap_mae"] == pytest.approx(0.0)
    assert metrics_by_name["rank_agreement"] == pytest.approx(1.0)
    assert metrics_by_name["recommendation_regret"] == pytest.approx(0.0)
    assert {metric.budget_digest for metric in metrics} == {selection.budget_digest}


def test_evaluate_selection_rejects_metric_budget_mismatch() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    selected_matrix = _matrix(origin, selection, cell_set, role="selected")
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")

    metrics = evaluate_selection(
        selection,
        origin,
        cell_set,
        selected_matrix,
        future_matrix,
        MetricConfig("metric-config", budget_digest="other-budget"),
    )

    assert len(metrics) == 1
    assert metrics[0].abstention_reason == "metric_budget_mismatch"
    assert metrics[0].budget_digest == selection.budget_digest


def test_evaluate_selection_emits_pairwise_rank_and_recommendation_metrics() -> None:
    selected_refs = (TaskCheckRef("selected-a", "check-selected-a"), TaskCheckRef("selected-b", "check-selected-b"))
    future_refs = (TaskCheckRef("future-a", "check-future-a"), TaskCheckRef("future-b", "check-future-b"))
    task_pool = _task_pool(
        tuple(ref.task_id for ref in selected_refs + future_refs),
        tuple(ref.check_id for ref in selected_refs + future_refs),
    )
    origin = replace(_origin(task_pool, refs=selected_refs), future_holdout_task_check_refs=future_refs)
    selection = record_with_digest(
        BenchmarkSelectionRecord(
            selection_id="selection-pairwise",
            task_pool_id=task_pool.task_pool_id,
            task_pool_digest=task_pool.task_pool_digest,
            origin_id=origin.origin_id,
            selector_id="selector",
            selected_task_check_refs=selected_refs,
            selected_weights={canonical_digest(ref): 1.0 for ref in selected_refs},
            budget_digest="budget",
            selection_input_digest="selector-input",
            feature_snapshot_id="feature-snapshot",
            eligibility_mode="strict_history",
            exposure_state="frozen",
            exposed_at=None,
            exposure_scope_digest=None,
            created_at="2026-01-05T00:00:00Z",
            selection_digest="",
        )
    )
    agent_ids = ("agent-a", "agent-b")
    outcomes = {
        ("agent-a", "selected-a"): "pass",
        ("agent-a", "selected-b"): "pass",
        ("agent-b", "selected-a"): "pass",
        ("agent-b", "selected-b"): "fail",
        ("agent-a", "future-a"): "fail",
        ("agent-a", "future-b"): "fail",
        ("agent-b", "future-a"): "pass",
        ("agent-b", "future-b"): "pass",
    }
    cells = tuple(
        ResultCellRef(
            agent_id,
            ref.task_id,
            ref.check_id,
            f"identity-{agent_id}-{ref.task_id}",
            f"result-{agent_id}-{ref.task_id}",
            f"digest-{agent_id}-{ref.task_id}",
            "result",
            None,
            outcomes[(agent_id, ref.task_id)],
        )
        for agent_id in agent_ids
        for ref in selected_refs + future_refs
    )
    cell_set = record_with_digest(
        EvaluationCellSet(
            cell_set_id="cell-set-pairwise",
            origin_id=origin.origin_id,
            selection_id=selection.selection_id,
            selected_task_check_refs=selected_refs,
            future_task_check_refs=future_refs,
            cells=cells,
            abstention_reason=None,
            cell_set_digest="",
        )
    )
    selected_matrix = record_with_digest(
        ResultMatrix(
            matrix_id="selected-pairwise",
            matrix_role="selected",
            origin_id=origin.origin_id,
            selection_id=selection.selection_id,
            agent_ids=agent_ids,
            task_check_refs=selected_refs,
            cells=tuple(cell for cell in cells if cell.task_id.startswith("selected-")),
            join_policy_digest="join",
            denominator_policy_digest="denominator",
            abstention_reason=None,
            scoreable_state="complete",
            matrix_digest="",
        )
    )
    future_matrix = record_with_digest(
        ResultMatrix(
            matrix_id="future-pairwise",
            matrix_role="future_holdout",
            origin_id=origin.origin_id,
            selection_id=selection.selection_id,
            agent_ids=agent_ids,
            task_check_refs=future_refs,
            cells=tuple(cell for cell in cells if cell.task_id.startswith("future-")),
            join_policy_digest="join",
            denominator_policy_digest="denominator",
            abstention_reason=None,
            scoreable_state="complete",
            matrix_digest="",
        )
    )

    metrics = evaluate_selection(selection, origin, cell_set, selected_matrix, future_matrix, MetricConfig("metric-config"))
    metrics_by_name = {metric.metric_name: metric.metric_value for metric in metrics}

    assert metrics_by_name["future_pass_rate_mae"] == pytest.approx(0.75)
    assert metrics_by_name["pairwise_gap_mae"] == pytest.approx(1.5)
    assert metrics_by_name["rank_agreement"] == pytest.approx(0.0)
    assert metrics_by_name["recommendation_regret"] == pytest.approx(1.0)
    assert metrics_by_name["future_coverage"] == pytest.approx(1.0)
    assert metrics_by_name["future_invalid_rate"] == pytest.approx(0.0)


def test_evaluate_selection_rejects_unfrozen_or_wrong_task_pool_selection() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    selected_matrix = _matrix(origin, selection, cell_set, role="selected")
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")
    unfrozen = record_with_digest(replace(selection, exposure_state="unexposed", selection_digest=""))

    metrics = evaluate_selection(unfrozen, origin, cell_set, selected_matrix, future_matrix, MetricConfig("metric-config"))

    assert metrics[0].abstention_reason == "selection_not_frozen"

    wrong_pool = record_with_digest(replace(selection, task_pool_digest="other-digest", selection_digest=""))
    metrics = evaluate_selection(wrong_pool, origin, cell_set, selected_matrix, future_matrix, MetricConfig("metric-config"))

    assert metrics[0].abstention_reason == "selection_task_pool_mismatch"


def test_build_selector_input_rejects_feature_snapshot_origin_or_feature_mismatch() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        FeatureConfig("features", "leakage", ("task_cluster",), ("task_metadata",)),
    )

    with pytest.raises(ValueError, match="origin_id"):
        build_selector_input(
            origin,
            task_pool,
            replace(snapshot, origin_id="other-origin"),
            (_result(result_available_at="2026-01-04T00:00:00Z"),),
            (_agent(),),
            SelectionBudget("budget", 1),
            LeakagePolicy("leakage", ("task_metadata",), origin.as_of_cutoff),
        )

    bad_record = replace(snapshot.feature_records[0], task_id="task-other")
    bad_snapshot = replace(
        snapshot,
        feature_records=(bad_record,),
        feature_record_ids=(bad_record.feature_id,),
        feature_records_digest=canonical_digest((bad_record,)),
    )
    with pytest.raises(ValueError, match="outside origin history"):
        build_selector_input(
            origin,
            task_pool,
            bad_snapshot,
            (_result(result_available_at="2026-01-04T00:00:00Z"),),
            (_agent(),),
            SelectionBudget("budget", 1),
            LeakagePolicy("leakage", ("task_metadata",), origin.as_of_cutoff),
        )


def test_evaluate_selection_rejects_denominator_mismatch_before_scoring() -> None:
    task_pool = _task_pool(("task-old", "task-other"), ("check-old", "check-other"))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    selected_matrix = _matrix(origin, selection, cell_set, role="selected")
    wrong_selected = record_with_digest(
        replace(
            selected_matrix,
            task_check_refs=(TaskCheckRef("task-other", "check-other"),),
            matrix_digest="",
        )
    )
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")

    metrics = evaluate_selection(selection, origin, cell_set, wrong_selected, future_matrix, MetricConfig("metric-config"))

    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].abstention_reason.startswith("selected_matrix_invalid:")


def test_evaluate_selection_abstains_on_missing_cells() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection, selected_state="missing")
    selected_matrix = _matrix(origin, selection, cell_set, role="selected", abstention_reason="missing_required_results")
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")

    metrics = evaluate_selection(selection, origin, cell_set, selected_matrix, future_matrix, MetricConfig("metric-config"))

    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].completeness_state == "abstained"
    assert metrics[0].abstention_reason == "missing_required_results"


@pytest.mark.parametrize("matrix_role", ("selected", "future_holdout"))
def test_evaluate_selection_abstains_when_exclusions_empty_agent_denominator(
    matrix_role: str,
) -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    cell_index = 0 if matrix_role == "selected" else 1
    excluded = replace(
        cell_set.cells[cell_index],
        result_id=None,
        result_digest=None,
        cell_state="excluded",
        exclusion_reason="agent_invalid",
        outcome="invalid",
    )
    cells = list(cell_set.cells)
    cells[cell_index] = excluded
    cell_set = record_with_digest(
        replace(cell_set, cells=tuple(cells), cell_set_digest="")
    )
    selected_matrix = _matrix(origin, selection, cell_set, role="selected")
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")
    target_matrix = selected_matrix if matrix_role == "selected" else future_matrix
    target_matrix = record_with_digest(
        replace(
            target_matrix,
            scoreable_state="complete_with_exclusions",
            matrix_digest="",
        )
    )
    if matrix_role == "selected":
        selected_matrix = target_matrix
    else:
        future_matrix = target_matrix

    metrics = evaluate_selection(
        selection,
        origin,
        cell_set,
        selected_matrix,
        future_matrix,
        MetricConfig("metric-config"),
    )

    assert len(metrics) == 1
    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].completeness_state == "abstained"
    assert metrics[0].abstention_reason == (
        f"{matrix_role}_empty_agent_denominator"
    )


def test_evaluate_selection_rejects_matrix_with_omitted_agent_denominator_cell() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    selected_matrix = record_with_digest(
        replace(
            _matrix(origin, selection, cell_set, role="selected"),
            agent_ids=("agent", "missing-agent"),
            matrix_digest="",
        )
    )
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")

    metrics = evaluate_selection(selection, origin, cell_set, selected_matrix, future_matrix, MetricConfig("metric-config"))

    assert len(metrics) == 1
    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].abstention_reason.startswith("selected_matrix_invalid:")


def test_evaluate_selection_metric_id_changes_with_matrix_evidence() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    selected_matrix = _matrix(origin, selection, cell_set, role="selected")
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")
    changed_future = record_with_digest(replace(future_matrix, matrix_id="future-matrix-rescore", matrix_digest=""))

    first = evaluate_selection(selection, origin, cell_set, selected_matrix, future_matrix, MetricConfig("metric-config"))
    second = evaluate_selection(selection, origin, cell_set, selected_matrix, changed_future, MetricConfig("metric-config"))

    assert first[0].metric_name == "future_pass_rate_mae"
    assert second[0].metric_name == "future_pass_rate_mae"
    assert first[0].metric_id != second[0].metric_id


def test_evaluate_selection_rejects_matrix_cell_identity_mismatch_with_cell_set() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    selected_matrix = _matrix(origin, selection, cell_set, role="selected")
    mismatched_cell = replace(selected_matrix.cells[0], required_identity_digest="different-identity")
    mismatched_matrix = record_with_digest(replace(selected_matrix, cells=(mismatched_cell,), matrix_digest=""))
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")

    metrics = evaluate_selection(selection, origin, cell_set, mismatched_matrix, future_matrix, MetricConfig("metric-config"))

    assert len(metrics) == 1
    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].abstention_reason == "selected_matrix_cell_identity_mismatch"


def test_evaluate_selection_rejects_matrix_result_binding_mismatch_with_cell_set() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    selected_matrix = _matrix(origin, selection, cell_set, role="selected")
    mismatched_cell = replace(selected_matrix.cells[0], result_id="different-result")
    mismatched_matrix = record_with_digest(replace(selected_matrix, cells=(mismatched_cell,), matrix_digest=""))
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")

    metrics = evaluate_selection(selection, origin, cell_set, mismatched_matrix, future_matrix, MetricConfig("metric-config"))

    assert len(metrics) == 1
    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].abstention_reason == "selected_matrix_cell_identity_mismatch"


def _origin(task_pool: TaskPoolRecord, refs: tuple[TaskCheckRef, ...] = (TaskCheckRef("task-old", "check-old"),)):
    return __import__("barcarolle.records", fromlist=["RollingOriginRecord"]).RollingOriginRecord(
        origin_id="origin",
        task_pool_id=task_pool.task_pool_id,
        task_pool_digest=task_pool.task_pool_digest,
        origin_time="2026-01-05T00:00:00Z",
        policy_digest="policy",
        history_task_check_refs=refs,
        future_holdout_task_check_refs=(TaskCheckRef("future-task", "future-check"),),
        as_of_cutoff="2026-01-05T00:00:00Z",
        cluster_constraints_digest="clusters",
        eligibility_mode="strict_history",
        holdout_overlap_policy="disjoint",
    )


def _selection(origin, task_pool: TaskPoolRecord):
    selection = __import__("barcarolle.records", fromlist=["BenchmarkSelectionRecord"]).BenchmarkSelectionRecord(
        selection_id="selection",
        task_pool_id=task_pool.task_pool_id,
        task_pool_digest=task_pool.task_pool_digest,
        origin_id=origin.origin_id,
        selector_id="selector",
        selected_task_check_refs=origin.history_task_check_refs,
        selected_weights={canonical_digest(origin.history_task_check_refs[0]): 1.0},
        budget_digest="budget",
        selection_input_digest="selector-input",
        feature_snapshot_id="feature-snapshot",
        eligibility_mode="strict_history",
        exposure_state="frozen",
        exposed_at=None,
        exposure_scope_digest=None,
        created_at="2026-01-05T00:00:00Z",
        selection_digest="",
    )
    return record_with_digest(selection)


def _selection_for_metric(
    origin_id: str,
    selector_id: str,
    *,
    budget_digest: str = "budget",
) -> BenchmarkSelectionRecord:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = replace(_origin(task_pool), origin_id=origin_id)
    selection = replace(
        _selection(origin, task_pool),
        selection_id=f"selection-{origin_id}-{selector_id}",
        selector_id=selector_id,
        budget_digest=budget_digest,
        selection_digest="",
    )
    return record_with_digest(selection)


def _mae_metric(
    selection: BenchmarkSelectionRecord,
    value: float,
    future_matrix: ResultMatrix | None = None,
) -> MetricRecord:
    future_matrix = future_matrix or _future_matrix_for_metric(selection)
    metric = MetricRecord(
        metric_id=f"metric-{selection.selection_id}",
        origin_id=selection.origin_id,
        selection_id=selection.selection_id,
        evaluation_cell_set_digest=f"cells-{selection.selection_id}",
        selected_matrix_digest=f"selected-{selection.selection_id}",
        future_matrix_digest=future_matrix.matrix_digest,
        join_policy_digest="join",
        metric_config_digest="metric-config",
        metric_scope="aggregate",
        agent_id=None,
        agent_pair=None,
        aggregation_level="all_agents",
        budget_digest=selection.budget_digest,
        stratum_ref=None,
        metric_name="future_pass_rate_mae",
        metric_value=value,
        denominator_policy_digest="denominator",
        completeness_state="complete",
        abstention_reason=None,
        computed_at="2026-01-10T00:00:00Z",
        metric_digest="",
    )
    return record_with_digest(metric)


def _future_matrix_for_metric(
    selection: BenchmarkSelectionRecord,
    *,
    result_id: str = "future-result",
    result_digest: str = "future-result-digest",
) -> ResultMatrix:
    ref = TaskCheckRef("future-task", "future-check")
    matrix = ResultMatrix(
        matrix_id=f"future-{selection.selection_id}",
        matrix_role="future_holdout",
        origin_id=selection.origin_id,
        selection_id=selection.selection_id,
        agent_ids=("agent",),
        task_check_refs=(ref,),
        cells=(
            ResultCellRef(
                "agent",
                ref.task_id,
                ref.check_id,
                "future-identity",
                result_id,
                result_digest,
                "result",
                None,
                "pass",
            ),
        ),
        join_policy_digest="join",
        denominator_policy_digest="denominator",
        abstention_reason=None,
        scoreable_state="complete",
        matrix_digest="",
    )
    return record_with_digest(matrix)


def _future_matrices(
    selections: tuple[BenchmarkSelectionRecord, ...],
) -> tuple[ResultMatrix, ...]:
    return tuple(_future_matrix_for_metric(selection) for selection in selections)


def _cell_set(origin, selection, selected_state: str = "result"):
    cell_set = EvaluationCellSet(
        cell_set_id="cell-set",
        origin_id=origin.origin_id,
        selection_id=selection.selection_id,
        selected_task_check_refs=origin.history_task_check_refs,
        future_task_check_refs=origin.future_holdout_task_check_refs,
        cells=(
            ResultCellRef("agent", "task-old", "check-old", "identity", "result" if selected_state == "result" else None, "digest" if selected_state == "result" else None, selected_state, None, "pass" if selected_state == "result" else None),
            ResultCellRef("agent", "future-task", "future-check", "future-identity", "future-result", "future-digest", "result", None, "pass"),
        ),
        abstention_reason=None,
        cell_set_digest="",
    )
    return record_with_digest(cell_set)


def _matrix(origin, selection, cell_set, role: str, abstention_reason: str | None = None):
    refs = origin.history_task_check_refs if role == "selected" else origin.future_holdout_task_check_refs
    matrix = ResultMatrix(
        matrix_id=f"matrix-{role}",
        matrix_role=role,
        origin_id=origin.origin_id,
        selection_id=selection.selection_id,
        agent_ids=("agent",),
        task_check_refs=refs,
        cells=tuple(cell for cell in cell_set.cells if (cell.task_id, cell.check_id) in {(ref.task_id, ref.check_id) for ref in refs}),
        join_policy_digest="join",
        denominator_policy_digest="denominator",
        abstention_reason=abstention_reason,
        scoreable_state="abstained" if abstention_reason else "complete",
        matrix_digest="",
    )
    return record_with_digest(matrix)


def _task_pool(task_ids: tuple[str, ...], check_ids: tuple[str, ...]) -> TaskPoolRecord:
    record = TaskPoolRecord(
        task_pool_id="task-pool",
        task_pool_digest="",
        repository_id="repo",
        task_ids=task_ids,
        check_ids=check_ids,
        task_records_ref="tasks.jsonl",
        task_records_digest="task-records",
        check_records_ref="checks.jsonl",
        check_records_digest="check-records",
        certification_evidence_ref="certification-evidence.jsonl",
        rejected_candidate_ids=(),
        rejection_summary_digest="rejections",
        certification_evidence_digest="evidence",
        source_event_inventory_digest="source-events",
        generator_config_digest="generator",
        certification_config_digest="certification",
        created_at="2026-01-01T00:00:00Z",
    )
    return record_with_digest(record)


def _task(
    task_id: str,
    check_id: str,
    available_at: str = "2026-01-02T00:00:00Z",
    cluster_id: str = "cluster",
) -> TaskRecord:
    task_text = f"Task {task_id}"
    solver_material_refs = ("README.md",)
    return TaskRecord(
        task_id=task_id,
        repository_id="repo",
        base_commit="commit",
        source_family="issue",
        source_ref=f"issue-{task_id}",
        source_resolved_at=available_at,
        task_material_available_at=available_at,
        task_text=task_text,
        solver_material_digest=make_solver_material_digest(task_text, solver_material_refs),
        solver_material_refs=solver_material_refs,
        check_ids=(check_id,),
        cluster_id=cluster_id,
    )


def _check(check_id: str, task_id: str, available_at: str = "2026-01-02T00:00:00Z") -> CheckRecord:
    return CheckRecord(
        check_id=check_id,
        task_id=task_id,
        check_type="pytest",
        check_manifest_digest=f"manifest-{check_id}",
        hidden_check_bundle_digest=f"bundle-{check_id}",
        resource_limits={"timeout_seconds": 5},
        oracle_source="private_tests",
        check_material_available_at=available_at,
    )


def _agent(agent_id: str = "agent") -> AgentRecord:
    return AgentRecord(
        agent_id=agent_id,
        agent_manifest_digest=f"manifest-{agent_id}",
        model_snapshot_id="model",
        harness_digest="harness",
        repository_instruction_digest="instructions",
        prompt_digest="prompt",
        tools_digest="tools",
        retrieval_digest="retrieval",
        skills_digest="skills",
        network_policy_digest="network",
        adapter_digest="adapter",
    )


def _selector(selector_id: str, family: str) -> SelectorRecord:
    parameters = {
        "recency": {},
        "random": {"seed": 7},
        "coverage": {"group_by_ref_key": {}},
        "rule_mixture": {
            "expert_weights": {"coverage": 1.0, "random": 0.0, "recency": 1.0},
            "random_seed": 7,
            "group_by_ref_key": {},
        },
    }.get(family, {})
    return SelectorRecord(
        selector_id=selector_id,
        selector_family=family,
        selector_version="1",
        training_source_digests=("training",),
        allowed_feature_classes=("task_metadata", "pre_origin_result"),
        parameters=parameters,
        config_digest=canonical_digest(
            {"selector_family": family, "parameters": parameters}
        ),
        created_at="2026-01-01T00:00:00Z",
    )


def _rolling_policy(
    future_holdout_known: bool = False,
    allowed_cluster_ids: tuple[str, ...] = (),
) -> RollingOriginPolicy:
    return RollingOriginPolicy(
        policy_digest="policy",
        as_of_cutoff_rule="origin_time",
        cluster_constraints_digest="clusters",
        eligibility_mode="strict_history",
        holdout_overlap_policy="disjoint",
        future_holdout_known=future_holdout_known,
        allowed_cluster_ids=allowed_cluster_ids,
    )


def _result(
    result_available_at: str,
    agent_id: str = "agent",
    task_id: str = "task-old",
    check_id: str = "check-old",
) -> ResultRecord:
    task_text = f"Task {task_id}"
    solver_material_refs = ("README.md",)
    identity = ResultCacheIdentity(
        task_id=task_id,
        check_id=check_id,
        repository_id="repo",
        base_commit="commit",
        submodule_state_digest="submodules",
        solver_material_digest=make_solver_material_digest(task_text, solver_material_refs),
        check_digest=make_check_digest(_check(check_id, task_id)),
        agent_manifest_digest=f"manifest-{agent_id}",
        model_snapshot_id="model",
        harness_digest="harness",
        repository_instruction_digest="instructions",
        prompt_digest="prompt",
        tools_digest="tools",
        retrieval_digest="retrieval",
        skills_digest="skills",
        network_policy_digest="network",
        budget_digest="budget",
        retry_policy_digest="retry",
        stochastic_settings_digest="stochastic",
        adapter_digest="adapter",
        workspace_config_digest="workspace",
        runtime_config_digest="runtime",
        hardware_profile_digest=None,
        identity_digest="",
    )
    identity = record_with_digest(identity)
    result = ResultRecord(
        result_id="result",
        result_digest="",
        cache_identity=identity,
        agent_id=agent_id,
        task_id=task_id,
        check_id=check_id,
        terminal_status="passed",
        scoreable_state="scoreable",
        outcome="pass",
        invalid_owner=None,
        failure_label=None,
        cost={"total_cost": 0.0},
        scoring_config_digest="scoring",
        pricing_version="test",
        usage={"total_tokens": 1},
        latency={"workspace_seconds": 1.0},
        diff_digest="diff",
        verifier_metadata_digest="verifier",
        started_at="2026-01-03T23:59:58Z",
        finished_at="2026-01-03T23:59:59Z",
        result_available_at=result_available_at,
    )
    return record_with_digest(result)


def _result_with_mismatched_identity(result: ResultRecord) -> ResultRecord:
    cache_identity = record_with_digest(
        replace(
            result.cache_identity,
            task_id=f"{result.task_id}-different",
            identity_digest="",
        )
    )
    return record_with_digest(replace(result, cache_identity=cache_identity, result_digest=""))


def _result_with_stale_check_identity(result: ResultRecord) -> ResultRecord:
    cache_identity = record_with_digest(
        replace(
            result.cache_identity,
            check_digest="stale-check",
            identity_digest="",
        )
    )
    return record_with_digest(replace(result, cache_identity=cache_identity, result_digest=""))
def _result_with_wrong_agent_identity(result: ResultRecord) -> ResultRecord:
    cache_identity = record_with_digest(
        replace(
            result.cache_identity,
            agent_manifest_digest="manifest-other-agent-version",
            identity_digest="",
        )
    )
    return record_with_digest(replace(result, cache_identity=cache_identity, result_digest=""))
