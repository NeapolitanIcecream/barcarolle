from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Mapping

import pytest

import barcarolle.selection.evaluation as evaluation_module
from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    CheckRecord,
    EvaluationCellSet,
    FeatureRecord,
    FeatureSnapshotRecord,
    MetricRecord,
    ResultCacheIdentity,
    ResultCellRef,
    ResultMatrix,
    ResultRecord,
    RollingOriginRecord,
    SelectorInput,
    SelectorRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    canonical_digest,
    make_check_digest,
    make_feature_snapshot_id,
    make_rolling_origin_id,
    make_rolling_origin_policy_digest,
    make_result_id,
    make_selector_id,
    make_selector_input_id,
    make_solver_material_digest,
    parse_utc_timestamp,
    record_with_digest,
    validate_benchmark_selection,
    validate_metric,
    validate_rolling_origin,
    validate_selector,
    validate_selector_input,
)
from barcarolle.result_store import ResultJoinConfig
from barcarolle.selection import (
    FeatureConfig,
    EWMASwitchConfig,
    LeakagePolicy,
    RollingOriginPolicy,
    SafeSwitchConfig,
    SelectionBudget,
    SimplexChoiceConfig,
    build_feature_snapshot,
    build_rule_mixture_grid,
    build_rule_selector,
    build_rolling_origin,
    build_selector_input,
    choose_rule_mixture_from_grid,
    choose_selector_from_metrics,
    choose_selector_with_ewma_guard,
    choose_selector_with_safe_switch,
    compare_arrival_and_label_time_cohorts,
    ensure_selector_executable,
    ensure_selector_input_result_evidence,
    ensure_feature_snapshot_task_metadata_provenance,
    evaluate_selection,
    lint_feature_snapshot,
    materialize_prospective_future_cohort,
    select_with_selector,
    summarize_stratified_forecast,
    summarize_selector_mae,
    train_selector,
)
from barcarolle.selection.evaluation import (
    _choose_rule_mixture_by_one_se,
    _choose_selector_by_ewma_guard,
    _choose_selector_by_mean_mae,
    _choose_selector_by_safe_switch,
    _matrix_alignment_error,
    _validated_training_matrices,
    _validated_training_metrics,
    _validate_training_results,
)
from barcarolle.selection.features import _ensure_feature_records_match_origin
from barcarolle.task_pool import TimeRange


def test_build_rolling_origin_separates_history_and_future_without_outcomes() -> None:
    origin = build_rolling_origin(
        _task_pool(("task-old", "task-future"), ("check-old", "check-future")),
        (
            _task("task-old", "check-old", available_at="2026-01-02T00:00:00Z"),
            _task("task-future", "check-future", available_at="2026-01-07T00:00:00Z"),
        ),
        {
            "check-old": _check(
                "check-old", "task-old", available_at="2026-01-02T00:00:00Z"
            ),
            "check-future": _check(
                "check-future", "task-future", available_at="2026-01-07T00:00:00Z"
            ),
        },
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        _rolling_policy(future_holdout_known=True),
    )

    assert origin.history_task_check_refs == (TaskCheckRef("task-old", "check-old"),)
    assert origin.future_holdout_task_check_refs == (
        TaskCheckRef("task-future", "check-future"),
    )
    assert origin.as_of_cutoff == "2026-01-05T00:00:00.000000Z"


def test_build_rolling_origin_requires_task_pool_member_records() -> None:
    task_pool = _task_pool(
        ("task-old", "task-future"),
        ("check-old", "check-future"),
    )
    tasks = (
        _task("task-old", "check-old", available_at="2026-01-02T00:00:00Z"),
        _task("task-future", "check-future", available_at="2026-01-07T00:00:00Z"),
    )
    checks = {
        "check-old": _check(
            "check-old", "task-old", available_at="2026-01-02T00:00:00Z"
        ),
        "check-future": _check(
            "check-future", "task-future", available_at="2026-01-07T00:00:00Z"
        ),
    }
    origin_time = datetime(2026, 1, 5, tzinfo=UTC)
    future_window = TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z")
    policy = _rolling_policy(future_holdout_known=True)

    with pytest.raises(ValueError, match="missing TaskPoolRecord task IDs"):
        build_rolling_origin(
            task_pool,
            tasks[:-1],
            checks,
            origin_time,
            future_window,
            policy,
        )

    with pytest.raises(ValueError, match="missing TaskPoolRecord check IDs"):
        build_rolling_origin(
            task_pool,
            tasks,
            {"check-old": checks["check-old"]},
            origin_time,
            future_window,
            policy,
        )

    wrong_owner = replace(checks["check-future"], task_id="task-old")
    with pytest.raises(ValueError, match="Task/Check linkage"):
        build_rolling_origin(
            task_pool,
            tasks,
            {**checks, "check-future": wrong_owner},
            origin_time,
            future_window,
            policy,
        )


def test_rolling_origin_separates_arrival_cohorts_from_label_maturity() -> None:
    task_pool = _task_pool(
        (
            "history-mature",
            "history-censored",
            "future-mature",
            "future-censored",
        ),
        (
            "history-mature-check",
            "history-censored-check",
            "future-mature-check",
            "future-censored-check",
        ),
    )
    tasks = (
        _task(
            "history-mature",
            "history-mature-check",
            available_at="2026-01-02T00:00:00Z",
        ),
        _task(
            "history-censored",
            "history-censored-check",
            available_at="2026-01-03T00:00:00Z",
        ),
        _task(
            "future-mature",
            "future-mature-check",
            available_at="2026-01-06T00:00:00Z",
        ),
        _task(
            "future-censored",
            "future-censored-check",
            available_at="2026-01-07T00:00:00Z",
        ),
    )
    checks = {
        "history-mature-check": _check(
            "history-mature-check",
            "history-mature",
            available_at="2026-01-04T00:00:00Z",
        ),
        "history-censored-check": _check(
            "history-censored-check",
            "history-censored",
            available_at="2026-01-07T00:00:00Z",
        ),
        "future-mature-check": _check(
            "future-mature-check",
            "future-mature",
            available_at="2026-01-11T00:00:00Z",
        ),
        "future-censored-check": _check(
            "future-censored-check",
            "future-censored",
            available_at="2026-01-13T00:00:00Z",
        ),
    }

    origin = build_rolling_origin(
        task_pool,
        tasks,
        checks,
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        RollingOriginPolicy(
            as_of_cutoff_rule="origin_time",
            eligibility_mode="counterfactual_replay",
            holdout_overlap_policy="allow_cluster_overlap",
            future_holdout_known=True,
            maturity_lag_seconds=2 * 24 * 60 * 60,
        ),
    )

    assert origin.history_task_check_refs == (
        TaskCheckRef("history-mature", "history-mature-check"),
    )
    assert origin.history_censored_task_check_refs == (
        TaskCheckRef("history-censored", "history-censored-check"),
    )
    assert origin.future_holdout_task_check_refs == (
        TaskCheckRef("future-mature", "future-mature-check"),
    )
    assert origin.future_censored_task_check_refs == (
        TaskCheckRef("future-censored", "future-censored-check"),
    )
    assert origin.future_cohort_time_basis == "task_material_available_at"
    assert origin.label_maturity_cutoff == "2026-01-12T00:00:00.000000Z"
    comparison = compare_arrival_and_label_time_cohorts(origin, tasks, checks)
    assert comparison["arrival_cohort_count"] == 2
    assert comparison["arrival_mature_count"] == 1
    assert comparison["arrival_censored_count"] == 1
    assert comparison["legacy_label_time_cohort_count"] == 1
    assert comparison["shared_cohort_count"] == 0
    assert comparison["arrival_only_count"] == 2
    assert comparison["label_time_only_count"] == 1


def test_build_rolling_origin_rejects_timezone_naive_origin() -> None:
    task_pool = _task_pool(("task",), ("check",))

    with pytest.raises(ValueError, match="timezone-aware"):
        build_rolling_origin(
            task_pool,
            (_task("task", "check", available_at="2026-01-02T00:00:00Z"),),
            {"check": _check("check", "task", available_at="2026-01-02T00:00:00Z")},
            datetime(2026, 1, 5),
            TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
            _rolling_policy(future_holdout_known=True),
        )


def test_build_rolling_origin_bounds_history_to_requested_window() -> None:
    task_pool = _task_pool(
        ("task-too-old", "task-history", "task-future"),
        ("check-too-old", "check-history", "check-future"),
    )
    origin = build_rolling_origin(
        task_pool,
        (
            _task("task-too-old", "check-too-old", available_at="2026-01-01T00:00:00Z"),
            _task("task-history", "check-history", available_at="2026-01-03T00:00:00Z"),
            _task("task-future", "check-future", available_at="2026-01-07T00:00:00Z"),
        ),
        {
            "check-too-old": _check(
                "check-too-old", "task-too-old", available_at="2026-01-01T00:00:00Z"
            ),
            "check-history": _check(
                "check-history", "task-history", available_at="2026-01-03T00:00:00Z"
            ),
            "check-future": _check(
                "check-future", "task-future", available_at="2026-01-07T00:00:00Z"
            ),
        },
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        _rolling_policy(future_holdout_known=True),
        history_window=TimeRange("2026-01-02T00:00:00Z", "2026-01-05T00:00:00Z"),
    )

    assert origin.history_task_check_refs == (
        TaskCheckRef("task-history", "check-history"),
    )
    assert origin.future_holdout_task_check_refs == (
        TaskCheckRef("task-future", "check-future"),
    )


def test_build_rolling_origin_preserves_fractional_second_boundary() -> None:
    task_pool = _task_pool(("history", "future"), ("history-check", "future-check"))
    origin = build_rolling_origin(
        task_pool,
        (
            _task(
                "history", "history-check", available_at="2026-01-05T00:00:00.250000Z"
            ),
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
    assert origin.future_holdout_task_check_refs == (
        TaskCheckRef("future", "future-check"),
    )


def test_build_rolling_origin_identity_changes_with_holdout() -> None:
    task_pool = _task_pool(("history", "future"), ("history-check", "future-check"))
    tasks = (
        _task("history", "history-check", available_at="2026-01-02T00:00:00Z"),
        _task("future", "future-check", available_at="2026-01-07T00:00:00Z"),
    )
    checks = {
        "history-check": _check(
            "history-check", "history", available_at="2026-01-02T00:00:00Z"
        ),
        "future-check": _check(
            "future-check", "future", available_at="2026-01-07T00:00:00Z"
        ),
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
    assert long_holdout.future_holdout_task_check_refs == (
        TaskCheckRef("future", "future-check"),
    )
    assert short_holdout.origin_id != shifted_empty_holdout.origin_id
    assert short_holdout.origin_id != long_holdout.origin_id


def test_rolling_origin_policy_digest_is_derived_from_behavior() -> None:
    policy = RollingOriginPolicy(
        as_of_cutoff_rule="origin_time",
        eligibility_mode="strict_prospective",
        holdout_overlap_policy="allow_cluster_overlap",
        future_holdout_known=False,
    )

    changed = replace(
        policy,
        allowed_dependency_cluster_ids=("dependency-cluster",),
    )

    assert (
        policy.policy_digest
        == RollingOriginPolicy(
            as_of_cutoff_rule="origin_time",
            eligibility_mode="strict_prospective",
            holdout_overlap_policy="allow_cluster_overlap",
            future_holdout_known=False,
        ).policy_digest
    )
    assert changed.policy_digest != policy.policy_digest


@pytest.mark.parametrize("value", (0, 1, "false", None))
def test_rolling_origin_policy_requires_exact_future_holdout_boolean(
    value: object,
) -> None:
    with pytest.raises(ValueError, match="future_holdout_known must be a boolean"):
        RollingOriginPolicy(
            as_of_cutoff_rule="origin_time",
            eligibility_mode="counterfactual_replay",
            holdout_overlap_policy="allow_cluster_overlap",
            future_holdout_known=value,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("value", ((1,), "allowed"))
def test_rolling_origin_policy_requires_typed_dependency_cluster_ids(
    value: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="allowed_dependency_cluster_ids must be a tuple of nonempty strings",
    ):
        RollingOriginPolicy(
            as_of_cutoff_rule="origin_time",
            eligibility_mode="counterfactual_replay",
            holdout_overlap_policy="allow_cluster_overlap",
            future_holdout_known=True,
            allowed_dependency_cluster_ids=value,  # type: ignore[arg-type]
        )


def test_selection_budget_digest_is_derived_from_limit() -> None:
    budget = SelectionBudget(2)

    assert budget.budget_digest == canonical_digest({"max_task_checks": 2})
    assert SelectionBudget(2).budget_digest == budget.budget_digest
    assert SelectionBudget(3).budget_digest != budget.budget_digest


@pytest.mark.parametrize("value", (0, -1, 1.5, True))
def test_selection_budget_rejects_nonpositive_or_noninteger_limit(
    value: object,
) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        SelectionBudget(value)  # type: ignore[arg-type]


def test_feature_and_leakage_digests_are_derived_from_behavior() -> None:
    config = FeatureConfig(("task_count",))
    same = FeatureConfig(("task_count",))
    changed_features = FeatureConfig(
        ("task_count", "task_stratum"),
    )
    policy = config.leakage_policy("2026-01-05T00:00:00Z")

    assert config.feature_config_digest == same.feature_config_digest
    assert config.feature_config_digest != changed_features.feature_config_digest
    assert (
        policy.leakage_policy_digest
        == LeakagePolicy(
            ("task_metadata",), "2026-01-05T00:00:00Z"
        ).leakage_policy_digest
    )
    assert (
        policy.leakage_policy_digest
        != config.leakage_policy("2026-01-06T00:00:00Z").leakage_policy_digest
    )


def test_feature_config_canonicalizes_names_and_derives_leakage_classes() -> None:
    config = FeatureConfig(("task_stratum", "task_count"))

    assert config.feature_names == ("task_count", "task_stratum")
    assert config.allowed_leakage_classes == ("task_metadata",)
    assert (
        config.feature_config_digest
        == FeatureConfig(("task_count", "task_stratum")).feature_config_digest
    )


@pytest.mark.parametrize(
    ("feature_names", "error"),
    (
        ((), "must not be empty"),
        (("task_count", "task_count"), "must be unique"),
        (("task_count", "unknown"), "unsupported feature"),
    ),
)
def test_feature_config_rejects_nonexecutable_feature_sets(
    feature_names: tuple[str, ...],
    error: str,
) -> None:
    with pytest.raises(ValueError, match=error):
        FeatureConfig(feature_names)


def test_strict_prospective_waits_for_frozen_task_pool_availability() -> None:
    task_pool = record_with_digest(
        replace(
            _task_pool(("task",), ("check",)),
            created_at="2026-01-06T00:00:00Z",
            task_pool_digest="",
        )
    )

    origin = build_rolling_origin(
        task_pool,
        (_task("task", "check", available_at="2026-01-02T00:00:00Z"),),
        {"check": _check("check", "task", available_at="2026-01-02T00:00:00Z")},
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-05T00:00:00Z", "2026-01-10T00:00:00Z"),
        RollingOriginPolicy(
            as_of_cutoff_rule="origin_time",
            eligibility_mode="strict_prospective",
            holdout_overlap_policy="allow_cluster_overlap",
            future_holdout_known=False,
        ),
    )

    assert origin.history_task_check_refs == ()
    assert origin.history_censored_task_check_refs == (TaskCheckRef("task", "check"),)
    assert origin.future_holdout_task_check_refs == ()


def test_prospective_future_cohort_accepts_incremental_pool_and_rejects_gap() -> None:
    history_task = _task(
        "history", "history-check", available_at="2026-01-02T00:00:00Z"
    )
    history_check = _check(
        "history-check", "history", available_at="2026-01-02T00:00:00Z"
    )
    selection_pool = record_with_digest(
        replace(
            _task_pool(("history",), ("history-check",)),
            created_at="2026-01-05T00:00:00Z",
            source_window_start="2026-01-01T00:00:00.000000Z",
            source_window_end="2026-01-05T00:00:00.000000Z",
            task_pool_digest="",
        )
    )
    origin = build_rolling_origin(
        selection_pool,
        (history_task,),
        {history_check.check_id: history_check},
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        RollingOriginPolicy(
            "origin_time",
            "strict_prospective",
            "allow_cluster_overlap",
            False,
        ),
    )
    selection = _selection(origin, selection_pool)
    future_task = _task("future", "future-check", available_at="2026-01-07T00:00:00Z")
    future_check = _check("future-check", "future", available_at="2026-01-07T00:00:00Z")
    future_pool = record_with_digest(
        replace(
            _task_pool(("future",), ("future-check",)),
            task_pool_id="future-pool",
            created_at="2026-01-11T00:00:00Z",
            source_window_start="2026-01-06T00:00:00.000000Z",
            source_window_end="2026-01-10T00:00:00.000000Z",
            task_pool_digest="",
        )
    )

    mature, censored = materialize_prospective_future_cohort(
        selection,
        origin,
        selection_pool,
        future_pool,
        (history_task,),
        {history_check.check_id: history_check},
        (future_task,),
        {future_check.check_id: future_check},
    )

    assert mature == (TaskCheckRef("future", "future-check"),)
    assert censored == ()

    gap_pool = record_with_digest(
        replace(
            future_pool,
            source_window_start="2026-01-07T00:00:00.000000Z",
            task_pool_digest="",
        )
    )
    with pytest.raises(ValueError, match="does not cover.*future window start"):
        materialize_prospective_future_cohort(
            selection,
            origin,
            selection_pool,
            gap_pool,
            (history_task,),
            {history_check.check_id: history_check},
            (future_task,),
            {future_check.check_id: future_check},
        )


def test_counterfactual_replay_uses_historical_material_availability() -> None:
    task_pool = record_with_digest(
        replace(
            _task_pool(("task",), ("check",)),
            created_at="2026-01-06T00:00:00Z",
            task_pool_digest="",
        )
    )

    origin = build_rolling_origin(
        task_pool,
        (_task("task", "check", available_at="2026-01-02T00:00:00Z"),),
        {"check": _check("check", "task", available_at="2026-01-02T00:00:00Z")},
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        RollingOriginPolicy(
            as_of_cutoff_rule="origin_time",
            eligibility_mode="counterfactual_replay",
            holdout_overlap_policy="allow_cluster_overlap",
            future_holdout_known=True,
        ),
    )

    assert origin.history_task_check_refs == (TaskCheckRef("task", "check"),)


def test_build_rolling_origin_rejects_disjoint_cluster_overlap() -> None:
    task_pool = _task_pool(("history", "future"), ("history-check", "future-check"))

    with pytest.raises(ValueError, match="history and future clusters overlap"):
        build_rolling_origin(
            task_pool,
            (
                _task(
                    "history",
                    "history-check",
                    available_at="2026-01-02T00:00:00Z",
                    dependency_cluster_id="shared",
                ),
                _task(
                    "future",
                    "future-check",
                    available_at="2026-01-07T00:00:00Z",
                    dependency_cluster_id="shared",
                ),
            ),
            {
                "history-check": _check(
                    "history-check", "history", available_at="2026-01-02T00:00:00Z"
                ),
                "future-check": _check(
                    "future-check", "future", available_at="2026-01-07T00:00:00Z"
                ),
            },
            datetime(2026, 1, 5, tzinfo=UTC),
            TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
            RollingOriginPolicy(
                as_of_cutoff_rule="origin_time",
                eligibility_mode="counterfactual_replay",
                holdout_overlap_policy="disjoint_clusters",
                future_holdout_known=True,
            ),
        )


def test_build_rolling_origin_explicitly_allows_cluster_overlap() -> None:
    task_pool = _task_pool(("history", "future"), ("history-check", "future-check"))
    origin = build_rolling_origin(
        task_pool,
        (
            _task(
                "history",
                "history-check",
                available_at="2026-01-02T00:00:00Z",
                dependency_cluster_id="shared",
            ),
            _task(
                "future",
                "future-check",
                available_at="2026-01-07T00:00:00Z",
                dependency_cluster_id="shared",
            ),
        ),
        {
            "history-check": _check(
                "history-check", "history", available_at="2026-01-02T00:00:00Z"
            ),
            "future-check": _check(
                "future-check", "future", available_at="2026-01-07T00:00:00Z"
            ),
        },
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        RollingOriginPolicy(
            as_of_cutoff_rule="origin_time",
            eligibility_mode="counterfactual_replay",
            holdout_overlap_policy="allow_cluster_overlap",
            future_holdout_known=True,
        ),
    )

    assert origin.future_holdout_task_check_refs == (
        TaskCheckRef("future", "future-check"),
    )
    assert validate_rolling_origin(origin).ok
    assert not validate_rolling_origin(
        replace(origin, future_window_end="2026-01-11T00:00:00Z")
    ).ok


def test_rolling_origin_validation_binds_cutoff_rule_and_future_window() -> None:
    origin = build_rolling_origin(
        _task_pool(("history", "future"), ("history-check", "future-check")),
        (
            _task("history", "history-check", available_at="2026-01-02T00:00:00Z"),
            _task("future", "future-check", available_at="2026-01-07T00:00:00Z"),
        ),
        {
            "history-check": _check(
                "history-check", "history", available_at="2026-01-02T00:00:00Z"
            ),
            "future-check": _check(
                "future-check", "future", available_at="2026-01-07T00:00:00Z"
            ),
        },
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        _rolling_policy(future_holdout_known=True),
    )

    def redigest(candidate: RollingOriginRecord) -> RollingOriginRecord:
        candidate = replace(candidate, origin_id="", origin_digest="")
        candidate = replace(candidate, origin_id=make_rolling_origin_id(candidate))
        return record_with_digest(candidate)

    cutoff_drift = redigest(replace(origin, as_of_cutoff="2026-01-04T00:00:00.000000Z"))
    cutoff_validation = validate_rolling_origin(cutoff_drift)
    assert not cutoff_validation.ok
    assert "as_of_cutoff does not match as_of_cutoff_rule" in cutoff_validation.errors

    overlapping_window = redigest(
        replace(origin, future_window_start="2026-01-04T00:00:00.000000Z")
    )
    window_validation = validate_rolling_origin(overlapping_window)
    assert not window_validation.ok
    assert (
        "timestamps must be ordered: as_of_cutoff, future_window_start, "
        "future_window_end"
    ) in window_validation.errors

    invalid_rule = replace(origin, as_of_cutoff_rule="not-a-timestamp")
    invalid_rule = replace(
        invalid_rule,
        policy_digest=make_rolling_origin_policy_digest(
            as_of_cutoff_rule=invalid_rule.as_of_cutoff_rule,
            eligibility_mode=invalid_rule.eligibility_mode,
            holdout_overlap_policy=invalid_rule.holdout_overlap_policy,
            future_holdout_known=invalid_rule.future_holdout_known,
            allowed_dependency_cluster_ids=invalid_rule.allowed_dependency_cluster_ids,
            maturity_lag_seconds=invalid_rule.maturity_lag_seconds,
        ),
    )
    rule_validation = validate_rolling_origin(redigest(invalid_rule))
    assert not rule_validation.ok
    assert (
        "as_of_cutoff_rule must be origin_time or a valid ISO datetime"
        in rule_validation.errors
    )


def test_rolling_origin_validation_rejects_nonboolean_future_holdout_state() -> None:
    origin = _origin(_task_pool(("task-old",), ("check-old",)))
    malformed = replace(
        origin,
        origin_id="",
        origin_digest="",
        future_holdout_known="false",  # type: ignore[arg-type]
        policy_digest=make_rolling_origin_policy_digest(
            as_of_cutoff_rule=origin.as_of_cutoff_rule,
            eligibility_mode=origin.eligibility_mode,
            holdout_overlap_policy=origin.holdout_overlap_policy,
            future_holdout_known="false",  # type: ignore[arg-type]
            allowed_dependency_cluster_ids=origin.allowed_dependency_cluster_ids,
            maturity_lag_seconds=origin.maturity_lag_seconds,
        ),
    )
    malformed = replace(malformed, origin_id=make_rolling_origin_id(malformed))
    malformed = record_with_digest(malformed)

    validation = validate_rolling_origin(malformed)

    assert not validation.ok
    assert (
        "RollingOriginRecord.future_holdout_known must be a boolean"
        in validation.errors
    )


def test_rolling_origin_validation_rejects_untyped_dependency_cluster_ids() -> None:
    origin = _origin(_task_pool(("task-old",), ("check-old",)))
    malformed = replace(
        origin,
        origin_id="",
        origin_digest="",
        allowed_dependency_cluster_ids=(1,),  # type: ignore[arg-type]
        policy_digest=make_rolling_origin_policy_digest(
            as_of_cutoff_rule=origin.as_of_cutoff_rule,
            eligibility_mode=origin.eligibility_mode,
            holdout_overlap_policy=origin.holdout_overlap_policy,
            future_holdout_known=origin.future_holdout_known,
            allowed_dependency_cluster_ids=(1,),  # type: ignore[arg-type]
            maturity_lag_seconds=origin.maturity_lag_seconds,
        ),
    )
    malformed = replace(malformed, origin_id=make_rolling_origin_id(malformed))
    malformed = record_with_digest(malformed)

    validation = validate_rolling_origin(malformed)

    assert not validation.ok
    assert (
        "RollingOriginRecord.allowed_dependency_cluster_ids[0] must be a string"
        in validation.errors
    )


def test_recency_selection_is_chronological_and_input_order_independent() -> None:
    task_pool = _task_pool(("task-new", "task-old"), ("check-new", "check-old"))
    task_new = _task("task-new", "check-new", available_at="2026-01-04T00:00:00Z")
    task_old = _task("task-old", "check-old", available_at="2026-01-02T00:00:00Z")
    checks = {
        "check-new": _check(
            "check-new", "task-new", available_at="2026-01-04T00:00:00Z"
        ),
        "check-old": _check(
            "check-old", "task-old", available_at="2026-01-02T00:00:00Z"
        ),
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

    expected_refs = (
        TaskCheckRef("task-old", "check-old"),
        TaskCheckRef("task-new", "check-new"),
    )
    assert origin_forward.history_task_check_refs == expected_refs
    assert origin_reversed.history_task_check_refs == expected_refs

    snapshot = build_feature_snapshot(
        origin_forward,
        task_pool,
        (task_new, task_old),
        checks,
        (),
        FeatureConfig(("task_count",)),
    )
    selector_input = build_selector_input(
        origin_forward,
        task_pool,
        snapshot,
        (),
        (_agent(),),
        SelectionBudget(1),
        LeakagePolicy(("task_metadata",), origin_forward.as_of_cutoff),
    )

    selection = select_with_selector(
        selector_input,
        snapshot,
        build_rule_selector("recency", allowed_feature_classes=("task_metadata",)),
    )

    assert selection.selected_task_check_refs == (
        TaskCheckRef("task-new", "check-new"),
    )


def test_build_rolling_origin_enforces_cluster_policy() -> None:
    task_pool = _task_pool(
        ("old", "recent", "wrong-cluster"), ("old-check", "recent-check", "wrong-check")
    )
    origin = build_rolling_origin(
        task_pool,
        (
            _task(
                "old",
                "old-check",
                available_at="2026-01-02T00:00:00Z",
                dependency_cluster_id="allowed",
            ),
            _task(
                "recent",
                "recent-check",
                available_at="2026-01-04T12:00:00Z",
                dependency_cluster_id="allowed",
            ),
            _task(
                "wrong-cluster",
                "wrong-check",
                available_at="2026-01-02T00:00:00Z",
                dependency_cluster_id="blocked",
            ),
        ),
        {
            "old-check": _check(
                "old-check", "old", available_at="2026-01-02T00:00:00Z"
            ),
            "recent-check": _check(
                "recent-check", "recent", available_at="2026-01-04T12:00:00Z"
            ),
            "wrong-check": _check(
                "wrong-check", "wrong-cluster", available_at="2026-01-02T00:00:00Z"
            ),
        },
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        _rolling_policy(allowed_dependency_cluster_ids=("allowed",)),
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
            _task(
                "after-origin", "after-check", available_at="2026-01-04T20:00:00-05:00"
            ),
        ),
        {
            "old-check": _check(
                "old-check", "old", available_at="2026-01-02T00:00:00Z"
            ),
            "after-check": _check(
                "after-check", "after-origin", available_at="2026-01-04T20:00:00-05:00"
            ),
        },
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-05T00:30:00Z", "2026-01-06T00:00:00Z"),
        _rolling_policy(future_holdout_known=True),
    )

    assert origin.history_task_check_refs == (TaskCheckRef("old", "old-check"),)
    assert origin.future_holdout_task_check_refs == (
        TaskCheckRef("after-origin", "after-check"),
    )


def test_build_selector_input_lints_features() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    feature_config = FeatureConfig(("task_count",))
    pre_origin_results = (_result(result_available_at="2026-01-04T00:00:00Z"),)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        pre_origin_results,
        feature_config,
    )

    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        pre_origin_results,
        (_agent(),),
        SelectionBudget(1),
        LeakagePolicy(("task_metadata",), origin.as_of_cutoff),
    )

    assert validate_selector_input(selector_input).ok
    assert selector_input.eligible_task_check_refs == origin.history_task_check_refs
    assert selector_input.feature_records_digest == snapshot.feature_records_digest
    assert selector_input.feature_snapshot_lint_status == "passed"

    def redigest(candidate: SelectorInput) -> SelectorInput:
        candidate = replace(
            candidate,
            selector_input_id=make_selector_input_id(candidate),
            selector_input_digest="",
        )
        return record_with_digest(candidate)

    duplicate_refs = (*selector_input.eligible_task_check_refs,) * 2
    invalid_inputs = (
        (
            redigest(replace(selector_input, selection_budget_limit=2)),
            "budget_digest does not match selection_budget_limit",
        ),
        (
            redigest(
                replace(
                    selector_input,
                    agent_ids=(*selector_input.agent_ids,) * 2,
                )
            ),
            "agent_ids must be unique",
        ),
        (
            redigest(
                replace(
                    selector_input,
                    eligible_task_check_refs=duplicate_refs,
                    origin_history_refs_digest=canonical_digest(duplicate_refs),
                )
            ),
            "eligible_task_check_refs must be unique",
        ),
        (
            redigest(replace(selector_input, origin_as_of_cutoff="not-a-timestamp")),
            "timestamps must be valid ISO datetimes: origin_as_of_cutoff",
        ),
    )
    for invalid_input, expected_error in invalid_inputs:
        assert expected_error in validate_selector_input(invalid_input).errors

def test_result_time_gates_strict_but_not_counterfactual_history() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    task = _task("task-old", "check-old")
    check = _check("check-old", "task-old")
    late_observed_result = _result(result_available_at="2026-01-06T00:00:00Z")
    feature_config = FeatureConfig(("pre_origin_result_count",))
    counterfactual_origin = _origin(task_pool)

    counterfactual_snapshot = build_feature_snapshot(
        counterfactual_origin,
        task_pool,
        (task,),
        {check.check_id: check},
        (late_observed_result,),
        feature_config,
    )
    counterfactual_input = build_selector_input(
        counterfactual_origin,
        task_pool,
        counterfactual_snapshot,
        (late_observed_result,),
        (_agent(),),
        SelectionBudget(1),
        feature_config.leakage_policy(counterfactual_origin.as_of_cutoff),
    )

    assert counterfactual_input.pre_origin_result_ids == (
        late_observed_result.result_id,
    )

    strict_origin = build_rolling_origin(
        task_pool,
        (task,),
        {check.check_id: check},
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        RollingOriginPolicy(
            as_of_cutoff_rule="origin_time",
            eligibility_mode="strict_prospective",
            holdout_overlap_policy="allow_cluster_overlap",
            future_holdout_known=False,
        ),
    )
    with pytest.raises(ValueError, match="after the origin cutoff"):
        build_feature_snapshot(
            strict_origin,
            task_pool,
            (task,),
            {check.check_id: check},
            (late_observed_result,),
            feature_config,
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
        FeatureConfig(("task_count",)),
    )

    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (),
        (_agent(),),
        SelectionBudget(1),
        LeakagePolicy(("task_metadata",), origin.as_of_cutoff),
    )

    assert validate_selector_input(selector_input).ok
    assert selector_input.pre_origin_result_ids == ()
    assert selector_input.pre_origin_result_digests == ()
    assert selector_input.feature_records_digest == snapshot.feature_records_digest


def test_feature_snapshot_task_metadata_requires_exact_frozen_sources() -> None:
    refs = (
        TaskCheckRef("task-old", "check-old"),
        TaskCheckRef("task-second", "check-second"),
    )
    tasks = (
        _task("task-old", "check-old", sampling_stratum="a"),
        _task("task-second", "check-second", sampling_stratum="b"),
    )
    task_pool = _task_pool(
        tuple(task.task_id for task in tasks),
        tuple(ref.check_id for ref in refs),
    )
    origin = _origin(task_pool, refs)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        tasks,
        {ref.check_id: _check(ref.check_id, ref.task_id) for ref in refs},
        (),
        FeatureConfig(
            ("task_count", "task_stratum"),
        ),
    )

    def redigest(
        records: tuple[FeatureRecord, ...],
    ) -> FeatureSnapshotRecord:
        updated = replace(
            snapshot,
            feature_snapshot_id="",
            feature_records=records,
            feature_records_digest=canonical_digest(records),
            feature_snapshot_digest="",
        )
        updated = replace(
            updated,
            feature_snapshot_id=make_feature_snapshot_id(updated),
        )
        return record_with_digest(updated)

    ensure_feature_snapshot_task_metadata_provenance(
        snapshot,
        origin,
        task_pool,
        tasks,
    )

    count_drift = redigest(
        tuple(
            replace(record, value=3) if record.feature_name == "task_count" else record
            for record in snapshot.feature_records
        )
    )
    with pytest.raises(ValueError, match="task_count.*frozen Task Pool"):
        ensure_feature_snapshot_task_metadata_provenance(
            count_drift,
            origin,
            task_pool,
            tasks,
        )

    stratum_drift = redigest(
        tuple(
            replace(record, source_artifact_digest="drifted-task")
            if record.feature_name == "task_stratum" and record.task_id == "task-old"
            else record
            for record in snapshot.feature_records
        )
    )
    with pytest.raises(ValueError, match="task_stratum.*frozen Task record"):
        ensure_feature_snapshot_task_metadata_provenance(
            stratum_drift,
            origin,
            task_pool,
            tasks,
        )

    origin_binding_drift = redigest(
        (
            replace(snapshot.feature_records[0], origin_snapshot_digest="drifted"),
            *snapshot.feature_records[1:],
        )
    )
    with pytest.raises(ValueError, match="Origin/config provenance"):
        ensure_feature_snapshot_task_metadata_provenance(
            origin_binding_drift,
            origin,
            task_pool,
            tasks,
        )

    unsupported = redigest(
        (
            replace(snapshot.feature_records[0], feature_name="unsupported"),
            *snapshot.feature_records[1:],
        )
    )
    with pytest.raises(ValueError, match="task_metadata provenance is unsupported"):
        ensure_feature_snapshot_task_metadata_provenance(
            unsupported,
            origin,
            task_pool,
            tasks,
        )


def test_selector_input_result_evidence_requires_exact_frozen_bindings() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    result = _result(result_available_at="2026-01-04T00:00:00Z")
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (result,),
        FeatureConfig(("pre_origin_result_count",)),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (result,),
        (_agent(),),
        SelectionBudget(1),
        LeakagePolicy(("pre_origin_result",), origin.as_of_cutoff),
    )

    ensure_selector_input_result_evidence(
        selector_input,
        origin,
        snapshot,
        (result,),
    )
    with pytest.raises(ValueError, match="missing from pre_origin_results"):
        ensure_selector_input_result_evidence(
            selector_input,
            origin,
            snapshot,
            (),
        )
    drifted_result = _redigest_result(
        result,
        cost={"total_cost": 1.0},
    )
    with pytest.raises(ValueError, match="Result digest does not match"):
        ensure_selector_input_result_evidence(
            selector_input,
            origin,
            snapshot,
            (drifted_result,),
        )
    with pytest.raises(ValueError, match="duplicate pre-origin Result record"):
        ensure_selector_input_result_evidence(
            selector_input,
            origin,
            snapshot,
            (result, result),
        )
    with pytest.raises(ValueError, match="does not match its origin"):
        ensure_selector_input_result_evidence(
            selector_input,
            replace(origin, origin_id="other-origin"),
            snapshot,
            (result,),
        )


def test_build_selector_input_rejects_timezone_offset_post_origin_result() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    task = _task("task-old", "check-old")
    check = _check("check-old", "task-old")
    origin = build_rolling_origin(
        task_pool,
        (task,),
        {check.check_id: check},
        datetime(2026, 1, 5, tzinfo=UTC),
        TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        RollingOriginPolicy(
            as_of_cutoff_rule="origin_time",
            eligibility_mode="strict_prospective",
            holdout_overlap_policy="allow_cluster_overlap",
            future_holdout_known=False,
        ),
    )
    feature_config = FeatureConfig(("task_count",))
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (task,),
        {check.check_id: check},
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
            SelectionBudget(1),
            LeakagePolicy(("task_metadata",), origin.as_of_cutoff),
        )


def test_build_feature_snapshot_rejects_result_finished_after_origin_as_instant() -> (
    None
):
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
            FeatureConfig(),
        )


def test_build_selector_input_rejects_off_history_or_wrong_agent_results() -> None:
    task_pool = _task_pool(("task-old", "task-other"), ("check-old", "check-other"))
    origin = _origin(task_pool)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"), _task("task-other", "check-other")),
        {
            "check-old": _check("check-old", "task-old"),
            "check-other": _check("check-other", "task-other"),
        },
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        FeatureConfig(("task_count",)),
    )

    with pytest.raises(ValueError, match="outside origin history"):
        build_selector_input(
            origin,
            task_pool,
            snapshot,
            (
                _result(
                    result_available_at="2026-01-04T00:00:00Z",
                    task_id="task-other",
                    check_id="check-other",
                ),
            ),
            (_agent(),),
            SelectionBudget(1),
            LeakagePolicy(("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
        )

    with pytest.raises(ValueError, match="outside candidate Agent"):
        build_selector_input(
            origin,
            task_pool,
            snapshot,
            (
                _result(
                    result_available_at="2026-01-04T00:00:00Z", agent_id="other-agent"
                ),
            ),
            (_agent(),),
            SelectionBudget(1),
            LeakagePolicy(("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
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
        FeatureConfig(("pre_origin_result_count",)),
    )

    with pytest.raises(ValueError, match="result provenance"):
        build_selector_input(
            origin,
            task_pool,
            snapshot,
            (_result(result_available_at="2026-01-04T00:00:00Z", agent_id="agent"),),
            (_agent("agent"),),
            SelectionBudget(1),
            LeakagePolicy(("pre_origin_result",), origin.as_of_cutoff),
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
            FeatureConfig(),
        )

    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (valid_result,),
        FeatureConfig(),
    )
    with pytest.raises(ValueError, match="invalid ResultRecord"):
        build_selector_input(
            origin,
            task_pool,
            snapshot,
            (_result_with_mismatched_identity(valid_result),),
            (_agent(),),
            SelectionBudget(1),
            LeakagePolicy(("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
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
            FeatureConfig(),
        )

    wrong_agent_result = _result_with_wrong_agent_identity(valid_result)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (wrong_agent_result,),
        FeatureConfig(),
    )
    with pytest.raises(ValueError, match="candidate Agent"):
        build_selector_input(
            origin,
            task_pool,
            snapshot,
            (wrong_agent_result,),
            (_agent(),),
            SelectionBudget(1),
            LeakagePolicy(("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
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
        FeatureConfig(("task_count",)),
    )

    result = lint_feature_snapshot(
        snapshot, LeakagePolicy(("pre_origin_result",), origin.as_of_cutoff)
    )

    assert not result.ok
    assert "feature leakage_class is not allowed" in result.errors
    assert snapshot.feature_records
    assert snapshot.leakage_lint_status == "passed"


def test_select_with_selector_freezes_common_refs_weights_and_task_pool_digest() -> (
    None
):
    task_pool = _task_pool(("task-old", "task-new"), ("check-old", "check-new"))
    origin = _origin(
        task_pool,
        refs=(
            TaskCheckRef("task-old", "check-old"),
            TaskCheckRef("task-new", "check-new"),
        ),
    )
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"), _task("task-new", "check-new")),
        {
            "check-old": _check("check-old", "task-old"),
            "check-new": _check("check-new", "task-new"),
        },
        (_result(result_available_at="2026-01-04T00:00:00Z", agent_id="agent-a"),),
        FeatureConfig(),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (_result(result_available_at="2026-01-04T00:00:00Z", agent_id="agent-a"),),
        (_agent("agent-a"), _agent("agent-b")),
        SelectionBudget(1),
        LeakagePolicy(("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
    )
    selector = _selector("selector-recency", "recency")

    selection = select_with_selector(selector_input, snapshot, selector)

    assert validate_benchmark_selection(selection).ok
    assert selection.task_pool_digest == task_pool.task_pool_digest
    assert selection.selector_id == selector.selector_id
    assert selection.feature_snapshot_id == snapshot.feature_snapshot_id
    assert selection.eligibility_mode == origin.eligibility_mode
    assert selection.selected_task_check_refs == (
        TaskCheckRef("task-new", "check-new"),
    )
    assert set(selection.selected_weights) == {
        canonical_digest(TaskCheckRef("task-new", "check-new"))
    }


def test_stratified_forecast_selector_uses_trailing_mix_and_capped_weights() -> None:
    refs = tuple(TaskCheckRef(f"task-{index}", f"check-{index}") for index in range(4))
    strata = ("a", "a", "b", "b")
    task_pool = _task_pool(
        tuple(ref.task_id for ref in refs),
        tuple(ref.check_id for ref in refs),
    )
    origin = _origin(task_pool, refs)
    tasks = tuple(
        _task(ref.task_id, ref.check_id, sampling_stratum=stratum)
        for ref, stratum in zip(refs, strata, strict=True)
    )
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        tasks,
        {ref.check_id: _check(ref.check_id, ref.task_id) for ref in refs},
        (),
        FeatureConfig(("task_stratum",)),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (),
        (_agent(),),
        SelectionBudget(3),
        LeakagePolicy(("task_metadata",), origin.as_of_cutoff),
    )
    selector = build_rule_selector(
        "stratified_forecast",
        {
            "dirichlet_alpha": 1.0,
            "trailing_ref_count": 2,
            "seed": 7,
            "weight_cap": 1.0,
        },
        allowed_feature_classes=("task_metadata",),
    )

    selection = select_with_selector(selector_input, snapshot, selector)

    stratum_by_task = {task.task_id: task.sampling_stratum for task in tasks}
    selected_strata = tuple(
        stratum_by_task[ref.task_id] for ref in selection.selected_task_check_refs
    )
    assert selected_strata.count("a") == 1
    assert selected_strata.count("b") == 2
    weights = tuple(selection.selected_weights.values())
    assert sorted(weights) == pytest.approx([0.75, 1.0, 1.0])


def test_stratified_forecast_selector_redistributes_capacity_overflow() -> None:
    refs = tuple(TaskCheckRef(f"task-{index}", f"check-{index}") for index in range(4))
    strata = ("b", "b", "b", "a")
    task_pool = _task_pool(
        tuple(ref.task_id for ref in refs),
        tuple(ref.check_id for ref in refs),
    )
    origin = _origin(task_pool, refs)
    tasks = tuple(
        _task(ref.task_id, ref.check_id, sampling_stratum=stratum)
        for ref, stratum in zip(refs, strata, strict=True)
    )
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        tasks,
        {ref.check_id: _check(ref.check_id, ref.task_id) for ref in refs},
        (),
        FeatureConfig(("task_stratum",)),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (),
        (_agent(),),
        SelectionBudget(4),
        LeakagePolicy(("task_metadata",), origin.as_of_cutoff),
    )
    selector = build_rule_selector(
        "stratified_forecast",
        {
            "dirichlet_alpha": 0.1,
            "trailing_ref_count": 1,
            "seed": 7,
            "weight_cap": None,
        },
        allowed_feature_classes=("task_metadata",),
    )

    selection = select_with_selector(selector_input, snapshot, selector)

    assert set(selection.selected_task_check_refs) == set(refs)
    assert set(selection.selected_weights.values()) == {1.0}


def test_stratified_forecast_selector_requires_exact_stratum_features() -> None:
    refs = (TaskCheckRef("task-old", "check-old"),)
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool, refs)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (),
        FeatureConfig(("task_count",)),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (),
        (_agent(),),
        SelectionBudget(1),
        LeakagePolicy(("task_metadata",), origin.as_of_cutoff),
    )
    selector = build_rule_selector(
        "stratified_forecast",
        {
            "dirichlet_alpha": 1.0,
            "trailing_ref_count": 10,
            "seed": 7,
            "weight_cap": 3.0,
        },
        allowed_feature_classes=("task_metadata",),
    )

    with pytest.raises(ValueError, match="exactly one task_stratum feature"):
        select_with_selector(selector_input, snapshot, selector)


@pytest.mark.parametrize(
    "parameters, message",
    (
        (
            {
                "dirichlet_alpha": 0.0,
                "trailing_ref_count": 10,
                "seed": 7,
                "weight_cap": 3.0,
            },
            "dirichlet_alpha",
        ),
        (
            {
                "dirichlet_alpha": 1.0,
                "trailing_ref_count": True,
                "seed": 7,
                "weight_cap": 3.0,
            },
            "trailing_ref_count",
        ),
        (
            {
                "dirichlet_alpha": 1.0,
                "trailing_ref_count": 10,
                "seed": False,
                "weight_cap": 3.0,
            },
            "seed",
        ),
        (
            {
                "dirichlet_alpha": 1.0,
                "trailing_ref_count": 10,
                "seed": 7,
                "weight_cap": float("nan"),
            },
            "weight_cap",
        ),
    ),
)
def test_stratified_forecast_selector_rejects_invalid_parameters(
    parameters: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        build_rule_selector("stratified_forecast", parameters)


def test_summarize_stratified_forecast_reports_composition_and_weight_diagnostics() -> (
    None
):
    history_refs = tuple(
        TaskCheckRef(f"task-{index}", f"check-{index}") for index in range(4)
    )
    future_refs = (
        TaskCheckRef("future-a", "future-check-a"),
        TaskCheckRef("future-b", "future-check-b"),
    )
    strata = ("a", "a", "b", "b")
    task_pool = _task_pool(
        tuple(ref.task_id for ref in history_refs),
        tuple(ref.check_id for ref in history_refs),
    )
    origin = record_with_digest(
        replace(
            _origin(task_pool, history_refs),
            future_holdout_task_check_refs=future_refs,
            origin_id="",
            origin_digest="",
        )
    )
    origin = record_with_digest(
        replace(origin, origin_id=make_rolling_origin_id(origin), origin_digest="")
    )
    tasks = tuple(
        _task(ref.task_id, ref.check_id, sampling_stratum=stratum)
        for ref, stratum in zip(history_refs, strata, strict=True)
    )
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        tasks,
        {ref.check_id: _check(ref.check_id, ref.task_id) for ref in history_refs},
        (),
        FeatureConfig(("task_stratum",)),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (),
        (_agent(),),
        SelectionBudget(3),
        LeakagePolicy(("task_metadata",), origin.as_of_cutoff),
    )
    selector = build_rule_selector(
        "stratified_forecast",
        {
            "dirichlet_alpha": 1.0,
            "trailing_ref_count": 2,
            "seed": 7,
            "weight_cap": 1.0,
        },
        allowed_feature_classes=("task_metadata",),
    )
    selection = select_with_selector(selector_input, snapshot, selector)

    summary = summarize_stratified_forecast(
        selector_input,
        snapshot,
        selector,
        selection,
        origin,
        {
            canonical_digest(future_refs[0]): "a",
            canonical_digest(future_refs[1]): "b",
        },
    )

    assert summary["forecast_proportions"] == {"a": 0.25, "b": 0.75}
    assert summary["future_proportions"] == {"a": 0.5, "b": 0.5}
    assert summary["forecast_proportion_tv_error"] == pytest.approx(0.25)
    assert summary["unweighted_selected_proportion_tv_error"] == pytest.approx(1 / 6)
    assert summary["post_stratified_proportion_tv_error"] == pytest.approx(2.5 / 11)
    assert summary["effective_sample_size"] == pytest.approx(121 / 41)
    assert summary["maximum_selected_weight"] == pytest.approx(1.0)
    assert summary["configured_weight_cap"] == pytest.approx(1.0)
    assert summary["capped_selected_fraction"] == pytest.approx(2 / 3)


def test_select_with_selector_rejects_feature_class_not_allowed_by_selector() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    result = _result(result_available_at="2026-01-04T00:00:00Z")
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (result,),
        FeatureConfig(),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (result,),
        (_agent(),),
        SelectionBudget(1),
        LeakagePolicy(("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
    )
    selector = replace(
        _selector("selector-recency", "recency"),
        allowed_feature_classes=("task_metadata",),
        selector_digest="",
    )
    selector = record_with_digest(selector)

    with pytest.raises(ValueError, match="not allowed by selector"):
        select_with_selector(selector_input, snapshot, selector)


def test_build_rule_selector_creates_an_executable_fixed_rule() -> None:
    selection_module = __import__(
        "barcarolle.selection", fromlist=["build_rule_selector"]
    )

    selector = selection_module.build_rule_selector(
        "random",
        {"seed": 11},
        allowed_feature_classes=("task_metadata",),
    )

    assert selector.selector_family == "random"
    assert selector.parameters == {"seed": 11}
    assert selector.training_source_digests == ()


def test_build_rule_selector_identity_includes_allowed_feature_classes() -> None:
    selection_module = __import__(
        "barcarolle.selection", fromlist=["build_rule_selector"]
    )

    metadata_only = selection_module.build_rule_selector(
        "recency", allowed_feature_classes=("task_metadata",)
    )
    results_only = selection_module.build_rule_selector(
        "recency", allowed_feature_classes=("pre_origin_result",)
    )

    assert metadata_only.selector_id != results_only.selector_id


def test_build_rule_selector_uses_record_semantic_id() -> None:
    selector = build_rule_selector(
        "random",
        {"seed": 11},
        allowed_feature_classes=("task_metadata",),
    )

    assert selector.selector_id == make_selector_id(selector)


def test_build_rule_selector_normalizes_allowed_feature_class_order() -> None:
    first = build_rule_selector(
        "recency",
        allowed_feature_classes=("task_metadata", "pre_origin_result"),
    )
    second = build_rule_selector(
        "recency",
        allowed_feature_classes=("pre_origin_result", "task_metadata", "task_metadata"),
    )

    assert first.selector_id == second.selector_id
    assert first.allowed_feature_classes == second.allowed_feature_classes


def test_build_rule_selector_normalizes_equivalent_numeric_parameters() -> None:
    integer_form = build_rule_selector(
        "stratified_forecast",
        {
            "dirichlet_alpha": 1,
            "trailing_ref_count": 10,
            "seed": 7,
            "weight_cap": 3,
        },
    )
    float_form = build_rule_selector(
        "stratified_forecast",
        {
            "dirichlet_alpha": 1.0,
            "trailing_ref_count": 10,
            "seed": 7,
            "weight_cap": 3.0,
        },
    )

    assert integer_form.parameters == float_form.parameters
    assert integer_form.config_digest == float_form.config_digest
    assert integer_form.selector_id == float_form.selector_id
    assert isinstance(integer_form.parameters["dirichlet_alpha"], float)
    assert isinstance(integer_form.parameters["weight_cap"], float)


def test_executable_selector_rejects_noncanonical_numeric_parameters() -> None:
    canonical = build_rule_selector(
        "stratified_forecast",
        {
            "dirichlet_alpha": 1.0,
            "trailing_ref_count": 10,
            "seed": 7,
            "weight_cap": 3.0,
        },
    )
    parameters = {
        "dirichlet_alpha": 1,
        "trailing_ref_count": 10,
        "seed": 7,
        "weight_cap": 3,
    }
    noncanonical = record_with_digest(
        replace(
            canonical,
            parameters=parameters,
            config_digest=canonical_digest(
                {
                    "selector_family": canonical.selector_family,
                    "parameters": parameters,
                }
            ),
            selector_digest="",
        )
    )

    assert validate_selector(noncanonical).ok
    with pytest.raises(ValueError, match="parameters must be canonical"):
        ensure_selector_executable(noncanonical)


@pytest.mark.parametrize(
    "expert_weights",
    (
        {"coverage": 2.0, "random": 0.0, "recency": 0.0},
        {"coverage": 1.0},
    ),
)
def test_executable_rule_mixture_rejects_redundant_weight_shapes(
    expert_weights: dict[str, float],
) -> None:
    selector = _rule_mixture_selector(
        {
            "expert_weights": expert_weights,
            "random_seed": 7,
            "group_by_ref_key": {},
        }
    )

    assert validate_selector(selector).ok
    with pytest.raises(ValueError, match="parameters must be canonical"):
        ensure_selector_executable(selector)


def test_executable_rule_mixture_collapses_signed_zero_identity() -> None:
    def selector(random_weight: float) -> SelectorRecord:
        return _rule_mixture_selector(
            {
                "expert_weights": {
                    "coverage": 1.0,
                    "random": random_weight,
                    "recency": 0.0,
                },
                "random_seed": 7,
                "group_by_ref_key": {},
            }
        )

    positive_zero = selector(0.0)
    negative_zero = selector(-0.0)

    assert negative_zero.selector_digest == positive_zero.selector_digest
    ensure_selector_executable(negative_zero)


def test_build_rule_selector_snapshots_nested_parameter_mappings() -> None:
    groups = {"task-a/check-a": "group-a"}
    selector = build_rule_selector(
        "coverage",
        {"group_by_ref_key": groups},
    )

    groups["task-a/check-a"] = "changed"

    assert selector.parameters == {"group_by_ref_key": {"task-a/check-a": "group-a"}}
    assert validate_selector(selector).ok


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
        FeatureConfig(("task_count",)),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (),
        (_agent(),),
        SelectionBudget(2),
        LeakagePolicy(("task_metadata",), origin.as_of_cutoff),
    )
    parameters = {
        "expert_weights": {"coverage": 1.0, "random": 0.0, "recency": 0.0},
        "random_seed": 7,
        "group_by_ref_key": {
            canonical_digest(refs[0]): "group-a",
            canonical_digest(refs[1]): "group-a",
            canonical_digest(refs[2]): "group-b",
        },
    }

    selection = select_with_selector(
        selector_input,
        snapshot,
        _rule_mixture_selector(parameters),
    )

    assert selection.selected_task_check_refs == (refs[0], refs[2])


def test_build_rule_mixture_grid_freezes_ten_executable_simplex_points() -> None:
    selectors = build_rule_mixture_grid(
        random_seed=7,
        group_by_ref_key={"ref-a": "group-a"},
    )

    weight_points = {
        tuple(
            selector.parameters["expert_weights"][family]  # type: ignore[index]
            for family in ("coverage", "random", "recency")
        )
        for selector in selectors
    }
    assert len(selectors) == 10
    assert len({selector.selector_id for selector in selectors}) == 10
    assert len({selector.training_source_digests for selector in selectors}) == 1
    assert (1 / 3, 1 / 3, 1 / 3) in weight_points
    assert {(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)} <= weight_points


def test_rule_mixture_one_se_prefers_equal_weights_within_best_uncertainty() -> None:
    selectors = build_rule_mixture_grid(random_seed=7, group_by_ref_key={})
    equal = _simplex_selector(selectors, (1 / 3, 1 / 3, 1 / 3))
    best = _simplex_selector(selectors, (1.0, 0.0, 0.0))
    rows = tuple(
        {
            selector.selector_id: (
                (0.1, 0.1, 0.5, 0.1)[origin_index]
                if selector == best
                else 0.3
                if selector == equal
                else 0.9
            )
            for selector in selectors
        }
        for origin_index in range(4)
    )

    chosen = _choose_rule_mixture_by_one_se(
        selectors,
        rows,
        SimplexChoiceConfig(minimum_origins=4),
    )

    assert chosen == equal


def test_rule_mixture_one_se_keeps_clear_best_and_falls_back_on_short_history() -> None:
    selectors = build_rule_mixture_grid(random_seed=7, group_by_ref_key={})
    equal = _simplex_selector(selectors, (1 / 3, 1 / 3, 1 / 3))
    best = _simplex_selector(selectors, (1.0, 0.0, 0.0))
    rows = tuple(
        {
            selector.selector_id: 0.1 if selector == best else 0.4
            for selector in selectors
        }
        for _ in range(4)
    )

    assert (
        _choose_rule_mixture_by_one_se(
            selectors,
            rows,
            SimplexChoiceConfig(minimum_origins=4),
        )
        == best
    )
    assert (
        _choose_rule_mixture_by_one_se(
            selectors,
            rows[:3],
            SimplexChoiceConfig(minimum_origins=4),
        )
        == equal
    )


def test_rule_mixture_one_se_rejects_incomplete_or_mixed_grid() -> None:
    selectors = build_rule_mixture_grid(random_seed=7, group_by_ref_key={})
    with pytest.raises(ValueError, match="complete ten-point simplex grid"):
        _choose_rule_mixture_by_one_se(
            selectors[:-1],
            tuple(
                {selector.selector_id: 0.2 for selector in selectors[:-1]}
                for _ in range(4)
            ),
            SimplexChoiceConfig(),
        )

    changed_parameters = {**selectors[-1].parameters, "random_seed": 11}
    changed_seed = record_with_digest(
        replace(
            selectors[-1],
            parameters=changed_parameters,
            config_digest=canonical_digest(
                {
                    "selector_family": "rule_mixture",
                    "parameters": changed_parameters,
                }
            ),
            selector_digest="",
        )
    )
    mixed = (*selectors[:-1], changed_seed)
    with pytest.raises(ValueError, match="same non-weight behavior"):
        _choose_rule_mixture_by_one_se(
            mixed,
            tuple({selector.selector_id: 0.2 for selector in mixed} for _ in range(4)),
            SimplexChoiceConfig(),
        )


def test_choose_rule_mixture_from_grid_uses_complete_paired_evidence() -> None:
    selectors = build_rule_mixture_grid(random_seed=7, group_by_ref_key={})
    equal = _simplex_selector(selectors, (1 / 3, 1 / 3, 1 / 3))
    selections = tuple(
        _selection_for_metric(origin_id, selector)
        for origin_id in ("origin-1", "origin-2", "origin-3", "origin-4")
        for selector in selectors
    )
    matrices = _future_matrices(selections)
    metrics = tuple(
        _mae_metric(
            selection,
            0.2 if selection.selector_id == equal.selector_id else 0.4,
            matrix,
        )
        for selection, matrix in zip(selections, matrices, strict=True)
    )

    chosen = choose_rule_mixture_from_grid(
        selectors,
        selections,
        metrics,
        matrices,
        config=SimplexChoiceConfig(minimum_origins=4),
    )

    assert chosen == equal


@pytest.mark.parametrize("minimum_origins", (True, 0, 1, 1.5))
def test_simplex_choice_config_rejects_invalid_history_gate(
    minimum_origins: object,
) -> None:
    with pytest.raises(ValueError, match="minimum_origins"):
        SimplexChoiceConfig(minimum_origins=minimum_origins)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("expert_weights", "error"),
    [
        ({"coverage": -1.0}, "finite nonnegative"),
        ({"coverage": float("inf")}, "not JSON compliant"),
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
        FeatureConfig(("task_count",)),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (),
        (_agent(),),
        SelectionBudget(1),
        LeakagePolicy(("task_metadata",), origin.as_of_cutoff),
    )

    with pytest.raises(ValueError, match=error):
        select_with_selector(
            selector_input,
            snapshot,
            _rule_mixture_selector(
                {
                    "expert_weights": expert_weights,
                    "random_seed": 7,
                    "group_by_ref_key": {},
                },
            ),
        )


def test_select_with_selector_replays_random_parameters_from_selector() -> None:
    refs = tuple(TaskCheckRef(f"task-{index}", f"check-{index}") for index in range(3))
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
        FeatureConfig(("task_count",)),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (),
        (_agent(),),
        SelectionBudget(2),
        LeakagePolicy(("task_metadata",), origin.as_of_cutoff),
    )
    selector = _selector("selector-random-v1", "random")

    first = select_with_selector(selector_input, snapshot, selector)
    second = select_with_selector(selector_input, snapshot, selector)
    mixture = select_with_selector(
        selector_input,
        snapshot,
        _rule_mixture_selector(
            {
                "expert_weights": {
                    "coverage": 0.0,
                    "random": 1.0,
                    "recency": 0.0,
                },
                "random_seed": 7,
                "group_by_ref_key": {},
            }
        ),
    )

    assert selector.parameters == {"seed": 7}
    assert first.selector_id == "selector-random-v1"
    assert first.selected_task_check_refs == second.selected_task_check_refs
    assert mixture.selected_task_check_refs == first.selected_task_check_refs


def test_select_with_selector_rejects_invalid_tampered_selector_input() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        FeatureConfig(),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        (_agent(),),
        SelectionBudget(1),
        LeakagePolicy(("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
    )
    tampered_input = record_with_digest(
        replace(
            selector_input,
            feature_snapshot_lint_status="failed",
            selector_input_digest="",
        )
    )

    with pytest.raises(ValueError, match="selector input is invalid"):
        select_with_selector(
            tampered_input,
            snapshot,
            _selector("selector-recency", "recency"),
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
        FeatureConfig(),
    )
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        (_agent(),),
        SelectionBudget(1),
        LeakagePolicy(("task_metadata", "pre_origin_result"), origin.as_of_cutoff),
    )
    selector = _selector("selector-unsupported", "unsupported")

    with pytest.raises(ValueError, match="unsupported selector family"):
        select_with_selector(
            selector_input,
            snapshot,
            selector,
        )


def test_train_selector_fits_replayable_rule_mixture_from_complete_evidence() -> None:
    evidence = _training_evidence()

    selector = _train_from_evidence(evidence)
    replayed = select_with_selector(
        evidence.selector_inputs[0], evidence.feature_snapshots[0], selector
    )

    assert selector.selector_family == "rule_mixture"
    assert len(selector.training_source_digests) == 10
    assert selector.parameters["random_seed"] == 7
    expert_weights = selector.parameters["expert_weights"]
    assert isinstance(expert_weights, dict)
    assert set(expert_weights) == {"coverage", "random", "recency"}
    assert all(isinstance(weight, float) for weight in expert_weights.values())
    assert sum(expert_weights.values()) == pytest.approx(1.0)
    assert validate_benchmark_selection(replayed).ok


def test_train_selector_accepts_cutoff_specific_leakage_policies_across_origins() -> (
    None
):
    evidence = _training_evidence(
        training_origin_times=(
            "2026-01-05T00:00:00Z",
            "2026-01-06T00:00:00Z",
        )
    )

    selector = _train_from_evidence(evidence)

    assert len({item.leakage_policy_digest for item in evidence.selector_inputs}) == 2
    assert selector.selector_family == "rule_mixture"


@pytest.mark.parametrize(
    ("drift_all_origins", "error"),
    (
        (False, "one Agent identity set"),
        (True, "training Results.*frozen Agent identities"),
    ),
)
def test_train_selector_binds_agent_identities_across_origins_and_results(
    drift_all_origins: bool,
    error: str,
) -> None:
    evidence = _training_evidence(
        training_origin_times=(
            "2026-01-05T00:00:00Z",
            "2026-01-06T00:00:00Z",
        )
    )
    drifted_agent_digest = canonical_digest(
        replace(_agent(), prompt_digest="drifted-prompt")
    )
    drifted_origin_ids = (
        {item.origin_id for item in evidence.selector_inputs}
        if drift_all_origins
        else {evidence.selector_inputs[1].origin_id}
    )
    drifted_evidence = _redigest_training_agent_inputs(
        evidence,
        drifted_origin_ids,
        drifted_agent_digest,
    )

    with pytest.raises(ValueError, match=error):
        _train_from_evidence(drifted_evidence)


def test_train_selector_binds_results_to_frozen_task_records() -> None:
    evidence = _training_evidence()
    drifted_evidence = _redigest_training_result_task_identities(evidence)

    with pytest.raises(ValueError, match="training Results.*Task/Check records"):
        _train_from_evidence(drifted_evidence)


def test_train_selector_requires_exact_pre_origin_feature_results() -> None:
    evidence = _training_evidence(include_pre_origin_result=True)

    assert _train_from_evidence(evidence).selector_family == "rule_mixture"
    with pytest.raises(ValueError, match="missing from pre_origin_results"):
        _train_from_evidence(replace(evidence, pre_origin_results=()))


def test_train_selector_rejects_nonlearned_family() -> None:
    evidence = _training_evidence()

    with pytest.raises(ValueError, match="only the rule_mixture"):
        _train_from_evidence(evidence, selector_family="recency")


def test_train_selector_rejects_selection_with_wrong_selector_digest() -> None:
    evidence = _training_evidence()
    tampered = record_with_digest(
        replace(
            evidence.selections[0],
            selector_digest="wrong-selector-digest",
            selection_digest="",
        )
    )

    with pytest.raises(ValueError, match="selector digest"):
        _train_from_evidence(
            replace(
                evidence,
                selections=(tampered, *evidence.selections[1:]),
            )
        )


def test_train_selector_rejects_selection_that_does_not_replay() -> None:
    evidence = _training_evidence()
    first = evidence.selections[0]
    alternate_ref = next(
        ref
        for ref in evidence.selector_inputs[0].eligible_task_check_refs
        if ref not in first.selected_task_check_refs
    )
    tampered = record_with_digest(
        replace(
            first,
            selected_task_check_refs=(alternate_ref,),
            selected_weights={canonical_digest(alternate_ref): 1.0},
            selection_digest="",
        )
    )

    with pytest.raises(ValueError, match="does not replay"):
        _train_from_evidence(
            replace(evidence, selections=(tampered, *evidence.selections[1:]))
        )


def test_train_selector_recomputes_mae_instead_of_trusting_metric() -> None:
    evidence = _training_evidence()
    first = evidence.metrics[0]
    tampered = record_with_digest(
        replace(
            first,
            metric_value=1.0 if first.metric_value == 0.0 else 0.0,
            metric_digest="",
        )
    )

    with pytest.raises(ValueError, match="does not recompute"):
        _train_from_evidence(
            replace(evidence, metrics=(tampered, *evidence.metrics[1:]))
        )


def test_training_matrix_validation_characterizes_paired_evidence() -> None:
    evidence = _training_evidence()
    origins_by_id = {origin.origin_id: origin for origin in evidence.training_origins}
    inputs_by_origin = {
        selector_input.origin_id: selector_input
        for selector_input in evidence.selector_inputs
    }
    selections_by_id = {
        selection.selection_id: selection for selection in evidence.selections
    }

    paired = _validated_training_matrices(
        origins_by_id,
        inputs_by_origin,
        selections_by_id,
        evidence.result_matrices,
    )
    assert set(paired) == set(selections_by_id)
    assert all(
        (selected.matrix_role, future.matrix_role) == ("selected", "future_holdout")
        for selected, future in paired.values()
    )

    with pytest.raises(ValueError, match="must have selected and future matrices"):
        _validated_training_matrices(
            origins_by_id,
            inputs_by_origin,
            selections_by_id,
            evidence.result_matrices[1:],
        )

    changed_policy = record_with_digest(
        replace(
            evidence.result_matrices[1],
            join_policy_digest="other-join-policy",
            matrix_digest="",
        )
    )
    with pytest.raises(ValueError, match="one join policy"):
        _validated_training_matrices(
            origins_by_id,
            inputs_by_origin,
            selections_by_id,
            (
                evidence.result_matrices[0],
                changed_policy,
                *evidence.result_matrices[2:],
            ),
        )

    second_future_index = next(
        index
        for index, matrix in enumerate(evidence.result_matrices)
        if matrix.matrix_role == "future_holdout"
        and matrix.selection_id == evidence.selections[1].selection_id
    )
    second_future = evidence.result_matrices[second_future_index]
    changed_cell = replace(second_future.cells[0], result_id="other-future-result")
    changed_evidence = record_with_digest(
        replace(second_future, cells=(changed_cell,), matrix_digest="")
    )
    matrices = list(evidence.result_matrices)
    matrices[second_future_index] = changed_evidence
    with pytest.raises(ValueError, match="same Result evidence"):
        _validated_training_matrices(
            origins_by_id,
            inputs_by_origin,
            selections_by_id,
            matrices,
        )


def test_training_metric_validation_characterizes_recomputed_contract() -> None:
    evidence = _training_evidence()
    selections_by_id = {
        selection.selection_id: selection for selection in evidence.selections
    }
    selections_by_origin: dict[str, dict[str, BenchmarkSelectionRecord]] = {}
    for selection in evidence.selections:
        selections_by_origin.setdefault(selection.origin_id, {})[
            selection.selector_id
        ] = selection
    matrices_by_selection = {
        selection.selection_id: (
            next(
                matrix
                for matrix in evidence.result_matrices
                if matrix.selection_id == selection.selection_id
                and matrix.matrix_role == "selected"
            ),
            next(
                matrix
                for matrix in evidence.result_matrices
                if matrix.selection_id == selection.selection_id
                and matrix.matrix_role == "future_holdout"
            ),
        )
        for selection in evidence.selections
    }

    rows = _validated_training_metrics(
        selections_by_id,
        selections_by_origin,
        matrices_by_selection,
        evidence.metrics,
    )
    assert rows == (
        {
            selection.selector_id: evidence.metrics[index].metric_value
            for index, selection in enumerate(evidence.selections)
        },
    )

    with pytest.raises(ValueError, match="exactly cover training selections"):
        _validated_training_metrics(
            selections_by_id,
            selections_by_origin,
            matrices_by_selection,
            evidence.metrics[1:],
        )

    changed_config = record_with_digest(
        replace(
            evidence.metrics[1],
            metric_config_digest="other-metric-config",
            metric_digest="",
        )
    )
    with pytest.raises(ValueError, match="unsupported metric protocol"):
        _validated_training_metrics(
            selections_by_id,
            selections_by_origin,
            matrices_by_selection,
            (evidence.metrics[0], changed_config, *evidence.metrics[2:]),
        )


def test_train_selector_rejects_an_unknown_metric_protocol() -> None:
    evidence = _training_evidence()
    changed_metrics = tuple(
        record_with_digest(
            replace(
                metric,
                metric_config_digest="unknown-metric-protocol",
                metric_digest="",
            )
        )
        for metric in evidence.metrics
    )

    with pytest.raises(ValueError, match="unsupported metric protocol"):
        _train_from_evidence(replace(evidence, metrics=changed_metrics))


def test_train_selector_requires_exact_result_bindings() -> None:
    evidence = _training_evidence()
    extra = _redigest_result(
        evidence.training_results[0],
        scoring_config_digest="extra-scoring",
    )

    with pytest.raises(ValueError, match="exactly match matrix bindings"):
        _train_from_evidence(
            replace(
                evidence,
                training_results=(*evidence.training_results, extra),
            )
        )


def test_train_selector_requires_results_bound_by_excluded_cells() -> None:
    evidence, excluded_result = _training_evidence_with_bound_exclusion()

    assert _train_from_evidence(evidence).selector_family == "rule_mixture"
    with pytest.raises(ValueError, match="missing from training_results"):
        _train_from_evidence(
            replace(
                evidence,
                training_results=tuple(
                    result
                    for result in evidence.training_results
                    if result.result_id != excluded_result.result_id
                ),
            )
        )


def test_train_selector_rejects_exclusion_without_invalid_result() -> None:
    evidence, _ = _training_evidence_with_bound_exclusion(justified=False)

    with pytest.raises(ValueError, match="does not follow Result evidence"):
        _train_from_evidence(evidence)


def test_training_result_validation_characterizes_matrix_bindings() -> None:
    evidence = _training_evidence()
    matrices_by_selection = {
        selection.selection_id: (
            next(
                matrix
                for matrix in evidence.result_matrices
                if matrix.selection_id == selection.selection_id
                and matrix.matrix_role == "selected"
            ),
            next(
                matrix
                for matrix in evidence.result_matrices
                if matrix.selection_id == selection.selection_id
                and matrix.matrix_role == "future_holdout"
            ),
        )
        for selection in evidence.selections
    }
    _validate_training_results(
        evidence.deployment_origin,
        matrices_by_selection,
        evidence.training_results,
    )

    with pytest.raises(ValueError, match="missing from training_results"):
        _validate_training_results(
            evidence.deployment_origin,
            matrices_by_selection,
            evidence.training_results[1:],
        )

    first_selection_id = evidence.selections[0].selection_id
    selected_matrix, future_matrix = matrices_by_selection[first_selection_id]
    drifted_cell = replace(selected_matrix.cells[0], agent_id="other-agent")
    drifted_matrix = replace(
        selected_matrix,
        cells=(drifted_cell, *selected_matrix.cells[1:]),
    )
    drifted_matrices = {
        **matrices_by_selection,
        first_selection_id: (drifted_matrix, future_matrix),
    }
    with pytest.raises(ValueError, match="does not match its matrix cell identity"):
        _validate_training_results(
            evidence.deployment_origin,
            drifted_matrices,
            evidence.training_results,
        )


def test_train_selector_rejects_future_window_after_deployment_cutoff() -> None:
    evidence = _training_evidence(deployment_time="2026-01-09T00:00:00Z")

    with pytest.raises(ValueError, match="label-maturity cutoffs"):
        _train_from_evidence(evidence)


def test_train_selector_waits_for_predeclared_label_maturity_cutoff() -> None:
    evidence = _training_evidence(deployment_time="2026-01-11T00:00:00Z")
    origin = evidence.training_origins[0]
    changed = replace(
        origin,
        policy_digest=make_rolling_origin_policy_digest(
            as_of_cutoff_rule=origin.as_of_cutoff_rule,
            eligibility_mode=origin.eligibility_mode,
            holdout_overlap_policy=origin.holdout_overlap_policy,
            future_holdout_known=origin.future_holdout_known,
            allowed_dependency_cluster_ids=origin.allowed_dependency_cluster_ids,
            maturity_lag_seconds=2 * 24 * 60 * 60,
        ),
        maturity_lag_seconds=2 * 24 * 60 * 60,
        label_maturity_cutoff="2026-01-12T00:00:00.000000Z",
        origin_id="",
        origin_digest="",
    )
    changed = replace(changed, origin_id=make_rolling_origin_id(changed))
    changed = record_with_digest(changed)

    with pytest.raises(ValueError, match="label-maturity cutoffs"):
        _train_from_evidence(replace(evidence, training_origins=(changed,)))


def test_train_selector_strict_prospective_requires_results_before_cutoff() -> None:
    evidence = _training_evidence(
        deployment_mode="strict_prospective",
        result_available_at="2026-01-11T00:00:00Z",
    )

    with pytest.raises(ValueError, match="strictly before deployment cutoff"):
        _train_from_evidence(evidence)


def test_train_selector_counterfactual_allows_later_evidence_collection() -> None:
    evidence = _training_evidence(
        deployment_mode="counterfactual_replay",
        result_available_at="2026-02-01T00:00:00Z",
    )

    assert _train_from_evidence(evidence).selector_family == "rule_mixture"


def test_choose_selector_by_mean_mae_averages_prepared_origin_rows() -> None:
    fallback = _selector("selector-fallback", "recency")
    selector_a = _selector("selector-a", "coverage")
    selector_b = _selector("selector-b", "random")
    rows = (
        {
            fallback.selector_id: 0.5,
            selector_a.selector_id: 0.2,
            selector_b.selector_id: 0.3,
        },
        {
            fallback.selector_id: 0.4,
            selector_a.selector_id: 0.4,
            selector_b.selector_id: 0.5,
        },
    )

    chosen = _choose_selector_by_mean_mae(
        (fallback, selector_a, selector_b),
        rows,
        fallback.selector_id,
    )

    assert chosen == selector_a


def test_choose_selector_by_mean_mae_uses_fallback_only_without_history() -> None:
    fallback = _selector("selector-fallback", "recency")
    candidate = _selector("selector-candidate", "random")

    chosen = _choose_selector_by_mean_mae(
        (fallback, candidate),
        (),
        fallback.selector_id,
    )

    assert chosen == fallback


def test_safe_switch_requires_stable_shrunk_improvement() -> None:
    fallback = _selector("selector-fallback", "recency")
    candidate = _selector("selector-candidate", "coverage")
    stable_rows = tuple(
        {fallback.selector_id: 0.5, candidate.selector_id: 0.2} for _ in range(4)
    )
    noisy_rows = tuple(
        {fallback.selector_id: 0.5, candidate.selector_id: value}
        for value in (0.0, 0.9, 0.0, 0.9)
    )

    assert (
        _choose_selector_by_safe_switch(
            (fallback, candidate),
            stable_rows,
            fallback.selector_id,
            SafeSwitchConfig(),
        )
        == candidate
    )
    assert (
        _choose_selector_by_safe_switch(
            (fallback, candidate),
            stable_rows,
            fallback.selector_id,
            SafeSwitchConfig(improvement_margin=0.21),
        )
        == fallback
    )
    assert (
        _choose_selector_by_safe_switch(
            (fallback, candidate),
            noisy_rows,
            fallback.selector_id,
            SafeSwitchConfig(),
        )
        == fallback
    )
    assert (
        _choose_selector_by_safe_switch(
            (fallback, candidate),
            noisy_rows,
            fallback.selector_id,
            SafeSwitchConfig(
                prior_strength=0.0,
                minimum_origins=2,
                uncertainty_multiplier=0.0,
            ),
        )
        == candidate
    )


def test_safe_switch_uses_fallback_below_minimum_history() -> None:
    fallback = _selector("selector-fallback", "recency")
    candidate = _selector("selector-candidate", "coverage")
    rows = tuple(
        {fallback.selector_id: 0.8, candidate.selector_id: 0.1} for _ in range(3)
    )

    chosen = _choose_selector_by_safe_switch(
        (fallback, candidate),
        rows,
        fallback.selector_id,
        SafeSwitchConfig(minimum_origins=4),
    )

    assert chosen == fallback


def test_safe_switch_config_rejects_invalid_gates() -> None:
    with pytest.raises(ValueError, match="prior_strength"):
        SafeSwitchConfig(prior_strength=-1.0)
    with pytest.raises(ValueError, match="prior_strength"):
        SafeSwitchConfig(prior_strength=10**1000)
    with pytest.raises(ValueError, match="minimum_origins"):
        SafeSwitchConfig(minimum_origins=1)
    with pytest.raises(ValueError, match="improvement_margin"):
        SafeSwitchConfig(improvement_margin=float("nan"))
    with pytest.raises(ValueError, match="uncertainty_multiplier"):
        SafeSwitchConfig(uncertainty_multiplier=True)  # type: ignore[arg-type]


def test_ewma_guard_prefers_recent_trend_over_lower_full_history_mean() -> None:
    fallback = _selector("selector-fallback", "recency")
    stale = _selector("selector-stale", "coverage")
    recent = _selector("selector-recent", "random")
    stale_losses = (0.0, 0.0, 0.0, 0.4, 0.7, 0.7)
    recent_losses = (0.8, 0.8, 0.8, 0.2, 0.1, 0.1)
    rows = tuple(
        {
            fallback.selector_id: 0.5,
            stale.selector_id: stale_losses[index],
            recent.selector_id: recent_losses[index],
        }
        for index in range(6)
    )

    assert (
        _choose_selector_by_mean_mae(
            (fallback, stale, recent), rows, fallback.selector_id
        )
        == stale
    )
    assert (
        _choose_selector_by_ewma_guard(
            (fallback, stale, recent),
            rows,
            fallback.selector_id,
            EWMASwitchConfig(
                half_life_origins=0.5,
                safe_switch=SafeSwitchConfig(
                    prior_strength=0.0,
                    minimum_origins=4,
                    uncertainty_multiplier=0.0,
                ),
            ),
        )
        == recent
    )


def test_ewma_guard_blocks_recent_candidate_without_full_history_improvement() -> None:
    fallback = _selector("selector-fallback", "recency")
    candidate = _selector("selector-candidate", "coverage")
    rows = tuple(
        {fallback.selector_id: 0.5, candidate.selector_id: loss}
        for loss in (0.9, 0.9, 0.9, 0.1, 0.1, 0.1)
    )

    chosen = _choose_selector_by_ewma_guard(
        (fallback, candidate),
        rows,
        fallback.selector_id,
        EWMASwitchConfig(
            half_life_origins=0.5,
            safe_switch=SafeSwitchConfig(
                prior_strength=0.0,
                minimum_origins=4,
                uncertainty_multiplier=0.0,
            ),
        ),
    )

    assert chosen == fallback


def test_choose_selector_with_ewma_guard_orders_rows_by_origin_cutoff() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origins = tuple(_chronological_origin(task_pool, day) for day in range(5, 11))
    fallback = _selector("selector-fallback", "recency")
    stale = _selector("selector-stale", "coverage")
    recent = _selector("selector-recent", "random")
    selectors = (fallback, stale, recent)
    stale_losses = (0.0, 0.0, 0.0, 0.4, 0.7, 0.7)
    recent_losses = (0.8, 0.8, 0.8, 0.2, 0.1, 0.1)
    loss_by_origin_selector = {
        (origin.origin_id, selector.selector_id): (
            0.5
            if selector == fallback
            else stale_losses[index]
            if selector == stale
            else recent_losses[index]
        )
        for index, origin in enumerate(origins)
        for selector in selectors
    }
    selections = tuple(
        _selection_for_metric(origin.origin_id, selector)
        for origin in reversed(origins)
        for selector in reversed(selectors)
    )
    matrices = _future_matrices(selections)
    metrics = tuple(
        _mae_metric(
            selection,
            loss_by_origin_selector[(selection.origin_id, selection.selector_id)],
            matrix,
        )
        for selection, matrix in zip(selections, matrices, strict=True)
    )

    chosen = choose_selector_with_ewma_guard(
        selectors,
        selections,
        metrics,
        matrices,
        tuple(reversed(origins)),
        _chronological_origin(task_pool, 12),
        fallback.selector_id,
        config=EWMASwitchConfig(
            half_life_origins=0.5,
            safe_switch=SafeSwitchConfig(
                prior_strength=0.0,
                minimum_origins=4,
                uncertainty_multiplier=0.0,
            ),
        ),
    )

    assert chosen == recent


def test_choose_selector_with_ewma_guard_requires_exact_origin_evidence() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _chronological_origin(task_pool, 5)
    selector = _selector("selector", "recency")
    selection = _selection_for_metric(origin.origin_id, selector)
    matrix = _future_matrix_for_metric(selection)

    with pytest.raises(ValueError, match="exactly cover paired MAE origins"):
        choose_selector_with_ewma_guard(
            (selector,),
            (selection,),
            (_mae_metric(selection, 0.2, matrix),),
            (matrix,),
            (),
            _chronological_origin(task_pool, 7),
            selector.selector_id,
        )


def test_choose_selector_with_ewma_guard_uses_fallback_without_history() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    fallback = _selector("selector-fallback", "recency")
    candidate = _selector("selector-candidate", "coverage")

    chosen = choose_selector_with_ewma_guard(
        (fallback, candidate),
        (),
        (),
        (),
        (),
        _chronological_origin(task_pool, 7),
        fallback.selector_id,
    )

    assert chosen == fallback


def test_choose_selector_with_ewma_guard_rejects_nonhistorical_origin() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    training_origin = _chronological_origin(task_pool, 5)
    selector = _selector("selector", "recency")
    selection = _selection_for_metric(training_origin.origin_id, selector)
    matrix = _future_matrix_for_metric(selection)

    with pytest.raises(ValueError, match="precede the deployment origin"):
        choose_selector_with_ewma_guard(
            (selector,),
            (selection,),
            (_mae_metric(selection, 0.2, matrix),),
            (matrix,),
            (training_origin,),
            _chronological_origin(task_pool, 5),
            selector.selector_id,
        )


@pytest.mark.parametrize("half_life", (True, 0.0, -1.0, float("nan"), 10**1000))
def test_ewma_switch_config_rejects_invalid_half_life(half_life: object) -> None:
    with pytest.raises(ValueError, match="half_life_origins"):
        EWMASwitchConfig(half_life_origins=half_life)  # type: ignore[arg-type]


def test_choose_selector_by_mean_mae_rejects_unpaired_rows() -> None:
    fallback = _selector("selector-fallback", "recency")
    candidate = _selector("selector-candidate", "coverage")

    with pytest.raises(ValueError, match="cover every registered selector"):
        _choose_selector_by_mean_mae(
            (fallback, candidate),
            ({candidate.selector_id: 0.1},),
            fallback.selector_id,
        )


@pytest.mark.parametrize("value", (float("nan"), float("inf"), -0.1, 1.1, True))
def test_choose_selector_by_mean_mae_rejects_invalid_values(value: float) -> None:
    selector = _selector("selector", "recency")

    with pytest.raises(ValueError, match="between 0 and 1"):
        _choose_selector_by_mean_mae(
            (selector,),
            ({selector.selector_id: value},),
            selector.selector_id,
        )


def test_choose_selector_by_mean_mae_rejects_invalid_registration() -> None:
    duplicate_a = _selector("duplicate", "recency")
    duplicate_b = _selector("duplicate", "random")

    with pytest.raises(ValueError, match="must be unique"):
        _choose_selector_by_mean_mae(
            (duplicate_a, duplicate_b), (), duplicate_a.selector_id
        )

    with pytest.raises(ValueError, match="fallback_selector_id is not registered"):
        _choose_selector_by_mean_mae((_selector("selector", "recency"),), (), "missing")

    with pytest.raises(ValueError, match="unsupported selector family"):
        _choose_selector_by_mean_mae(
            (_selector("selector-unsupported", "unsupported"),),
            (),
            "selector-unsupported",
        )

    invalid_random = record_with_digest(
        replace(
            _selector("selector-random", "random"),
            parameters={},
            config_digest=canonical_digest(
                {"selector_family": "random", "parameters": {}}
            ),
            selector_digest="",
        )
    )
    with pytest.raises(ValueError, match="seed"):
        _choose_selector_by_mean_mae(
            (invalid_random,),
            (),
            invalid_random.selector_id,
        )


def test_choose_selector_from_metrics_pairs_complete_origin_rows() -> None:
    selector_a = _selector("selector-a", "recency")
    selector_b = _selector("selector-b", "coverage")
    selections = (
        _selection_for_metric("origin-2", selector_b),
        _selection_for_metric("origin-1", selector_a),
        _selection_for_metric("origin-2", selector_a),
        _selection_for_metric("origin-1", selector_b),
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

    safe_chosen = choose_selector_with_safe_switch(
        (selector_b, selector_a),
        selections,
        metrics,
        _future_matrices(selections),
        selector_b.selector_id,
        config=SafeSwitchConfig(
            prior_strength=0.0,
            minimum_origins=2,
            uncertainty_multiplier=0.0,
        ),
    )

    assert safe_chosen == selector_a


def test_summarize_selector_mae_reports_macro_weighted_and_paired_losses() -> None:
    selector_a = _selector("selector-a", "recency")
    selector_b = _selector("selector-b", "coverage")
    selections = tuple(
        _selection_for_metric(origin_id, selector)
        for origin_id in ("origin-1", "origin-2")
        for selector in (selector_a, selector_b)
    )
    future_counts = {"origin-1": 1, "origin-2": 3}
    matrices = tuple(
        _future_matrix_for_metric(
            selection,
            task_count=future_counts[selection.origin_id],
        )
        for selection in selections
    )
    matrices_by_selection = {matrix.selection_id: matrix for matrix in matrices}
    losses = {
        ("origin-1", "selector-a"): 0.2,
        ("origin-2", "selector-a"): 0.8,
        ("origin-1", "selector-b"): 0.4,
        ("origin-2", "selector-b"): 0.4,
    }
    metrics = tuple(
        _mae_metric(
            selection,
            losses[(selection.origin_id, selection.selector_id)],
            matrices_by_selection[selection.selection_id],
        )
        for selection in selections
    )

    summary = summarize_selector_mae(
        (selector_b, selector_a),
        tuple(reversed(selections)),
        tuple(reversed(metrics)),
        tuple(reversed(matrices)),
    )

    selector_rows = {
        row["selector_id"]: row
        for row in summary["selectors"]  # type: ignore[index]
    }
    assert selector_rows["selector-a"]["macro_origin_mae"] == pytest.approx(0.5)
    assert selector_rows["selector-a"][
        "future_task_count_weighted_mae"
    ] == pytest.approx(0.65)
    assert selector_rows["selector-b"]["macro_origin_mae"] == pytest.approx(0.4)
    assert selector_rows["selector-b"][
        "future_task_count_weighted_mae"
    ] == pytest.approx(0.4)
    pair = summary["paired_differences"][0]  # type: ignore[index]
    assert pair["selector_a_id"] == "selector-a"
    assert pair["selector_b_id"] == "selector-b"
    assert pair["macro_origin_mae_difference"] == pytest.approx(0.1)
    assert pair["future_task_count_weighted_mae_difference"] == pytest.approx(0.25)
    assert pair["origin_block_interval_95"]["status"] == ("insufficient_origin_blocks")


def test_summarize_selector_mae_does_not_present_empty_evidence_as_zero_loss() -> None:
    selector = _selector("selector", "recency")

    with pytest.raises(ValueError, match="at least one origin"):
        summarize_selector_mae((selector,), (), (), ())


def test_summarize_selector_mae_weights_only_scoreable_future_refs() -> None:
    selector = _selector("selector", "recency")
    first = _selection_for_metric("origin-1", selector)
    second = _selection_for_metric("origin-2", selector)
    first_matrix = _future_matrix_for_metric(first)
    excluded_ref = TaskCheckRef("excluded-task", "excluded-check")
    first_matrix = record_with_digest(
        replace(
            first_matrix,
            task_check_refs=(*first_matrix.task_check_refs, excluded_ref),
            cells=(
                *first_matrix.cells,
                ResultCellRef(
                    "agent",
                    excluded_ref.task_id,
                    excluded_ref.check_id,
                    "excluded-identity",
                    None,
                    None,
                    "excluded",
                    "benchmark_invalid",
                    None,
                ),
            ),
            scoreable_state="complete_with_exclusions",
            matrix_digest="",
        )
    )
    second_matrix = _future_matrix_for_metric(second)
    first_metric = record_with_digest(
        replace(
            _mae_metric(first, 0.0, first_matrix),
            completeness_state="complete_with_exclusions",
            metric_digest="",
        )
    )

    summary = summarize_selector_mae(
        (selector,),
        (first, second),
        (first_metric, _mae_metric(second, 1.0, second_matrix)),
        (first_matrix, second_matrix),
    )

    selector_row = summary["selectors"][0]  # type: ignore[index]
    assert selector_row["future_task_count_weighted_mae"] == pytest.approx(0.5)
    assert summary["future_scoreable_task_check_count"] == 2


def test_summarize_selector_mae_rejects_non_scoreable_future_matrix() -> None:
    selector = _selector("selector", "recency")
    selection = _selection_for_metric("origin-1", selector)
    matrix = _future_matrix_for_metric(selection)
    missing_cell = replace(
        matrix.cells[0],
        result_id=None,
        result_digest=None,
        cell_state="missing",
        outcome=None,
    )
    matrix = record_with_digest(
        replace(
            matrix,
            cells=(missing_cell,),
            scoreable_state="incomplete",
            matrix_digest="",
        )
    )

    with pytest.raises(ValueError, match="future matrix is not scoreable"):
        summarize_selector_mae(
            (selector,),
            (selection,),
            (_mae_metric(selection, 0.0, matrix),),
            (matrix,),
        )


def test_summarize_selector_mae_reports_deterministic_origin_block_interval() -> None:
    selector = _selector("selector", "recency")
    selections = tuple(
        _selection_for_metric(f"origin-{index:02d}", selector) for index in range(8)
    )
    matrices = _future_matrices(selections)
    metrics = tuple(
        _mae_metric(selection, 0.25, matrix)
        for selection, matrix in zip(selections, matrices, strict=True)
    )

    first = summarize_selector_mae((selector,), selections, metrics, matrices)
    second = summarize_selector_mae((selector,), selections, metrics, matrices)

    assert first == second
    interval = first["selectors"][0]["origin_block_interval_95"]  # type: ignore[index]
    assert interval["status"] == "available"
    assert interval["lower"] == pytest.approx(0.25)
    assert interval["upper"] == pytest.approx(0.25)


@pytest.mark.parametrize("family", ("random", "stratified_forecast"))
def test_summarize_selector_mae_groups_exact_seed_variants(family: str) -> None:
    seed_seven = _selector(f"{family}-7", family)
    seed_eleven_parameters = {**seed_seven.parameters, "seed": 11}
    seed_eleven = record_with_digest(
        replace(
            _selector(f"{family}-11", family),
            parameters=seed_eleven_parameters,
            config_digest=canonical_digest(
                {
                    "selector_family": family,
                    "parameters": seed_eleven_parameters,
                }
            ),
            selector_digest="",
        )
    )
    selections = tuple(
        _selection_for_metric("origin-1", selector)
        for selector in (seed_seven, seed_eleven)
    )
    matrices = _future_matrices(selections)
    metrics = tuple(
        _mae_metric(selection, loss, matrix)
        for selection, loss, matrix in zip(
            selections,
            (0.2, 0.6),
            matrices,
            strict=True,
        )
    )

    summary = summarize_selector_mae(
        (seed_seven, seed_eleven),
        selections,
        metrics,
        matrices,
    )

    seed_bank = summary["seed_banks"][0]  # type: ignore[index]
    assert seed_bank["selector_ids"] == (f"{family}-7", f"{family}-11")
    assert seed_bank["seeds"] == (7, 11)
    assert seed_bank["macro_origin_mae_mean"] == pytest.approx(0.4)
    assert seed_bank["macro_origin_mae_population_stddev"] == pytest.approx(0.2)


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
    selection = _selection_for_metric("origin-1", selector)
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
    selection = _selection_for_metric("origin-1", selector_a)

    with pytest.raises(
        ValueError, match="origin-1 is missing registered selectors: selector-b"
    ):
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
    selection = _selection_for_metric("origin-1", selector)
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
    first = _selection_for_metric("origin-1", selector)
    second = _selection_for_metric("origin-2", selector)
    first_metric = _mae_metric(first, 0.2)
    second_metric = _mae_metric(second, 0.3)
    incompatible_cases = (
        (
            replace(second, budget_digest="other-budget", selection_digest=""),
            second_metric,
            "budget",
        ),
        (
            second,
            replace(second_metric, metric_name="other-metric", metric_digest=""),
            "future_pass_rate_mae",
        ),
        (
            second,
            replace(
                second_metric, metric_config_digest="other-config", metric_digest=""
            ),
            "metric protocol",
        ),
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


def test_choose_selector_from_metrics_requires_same_origin_input_and_task_pool() -> (
    None
):
    selector_a = _selector("selector-a", "recency")
    selector_b = _selector("selector-b", "coverage")
    first = _selection_for_metric("origin-1", selector_a)
    mismatched_input = record_with_digest(
        replace(
            _selection_for_metric("origin-1", selector_b),
            selection_input_digest="other-input",
            selection_digest="",
        )
    )
    with pytest.raises(
        ValueError, match="origin origin-1 must use one selection input"
    ):
        choose_selector_from_metrics(
            (selector_a, selector_b),
            (first, mismatched_input),
            (_mae_metric(first, 0.2), _mae_metric(mismatched_input, 0.3)),
            _future_matrices((first, mismatched_input)),
            selector_a.selector_id,
        )

    second_origin = record_with_digest(
        replace(
            _selection_for_metric("origin-2", selector_a),
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


def test_choose_selector_from_metrics_allows_completeness_to_differ_across_origins() -> (
    None
):
    selector = _selector("selector", "recency")
    first = _selection_for_metric("origin-1", selector)
    second = _selection_for_metric("origin-2", selector)
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


def test_choose_selector_from_metrics_requires_one_completeness_state_within_origin() -> (
    None
):
    selector_a = _selector("selector-a", "recency")
    selector_b = _selector("selector-b", "coverage")
    first = _selection_for_metric("origin-1", selector_a)
    second = _selection_for_metric("origin-1", selector_b)
    second_metric = record_with_digest(
        replace(
            _mae_metric(second, 0.3),
            completeness_state="complete_with_exclusions",
            metric_digest="",
        )
    )

    with pytest.raises(
        ValueError, match="origin origin-1 must have one completeness state"
    ):
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
    first = _selection_for_metric("origin-1", selector_a)
    second = _selection_for_metric("origin-1", selector_b)
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


def test_evaluate_selection_emits_invalid_metric_for_matrix_alignment_failure() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    selected_matrix = _matrix(origin, selection, cell_set, role="selected")
    future_matrix = _matrix(origin, selection, cell_set, role="selected")

    metrics = evaluate_selection(
        selection,
        origin,
        cell_set,
        selected_matrix,
        future_matrix,
    )

    assert len(metrics) == 1
    assert validate_metric(metrics[0]).ok
    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].abstention_reason == "matrix_role_mismatch"


def test_evaluate_selection_uses_implementation_owned_metric_protocol() -> None:
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
    )

    assert {metric.metric_config_digest for metric in metrics} == {
        evaluation_module.METRIC_CONFIG_DIGEST
    }


def test_evaluate_selection_rejects_selection_origin_eligibility_mode_drift() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    drifted_selection = record_with_digest(
        replace(
            selection,
            eligibility_mode="strict_prospective",
            selection_digest="",
        )
    )
    cell_set = _cell_set(origin, selection)
    selected_matrix = _matrix(origin, selection, cell_set, role="selected")
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")

    metrics = evaluate_selection(
        drifted_selection,
        origin,
        cell_set,
        selected_matrix,
        future_matrix,
    )

    assert len(metrics) == 1
    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].abstention_reason == "selection_eligibility_mode_mismatch"


def test_matrix_alignment_error_characterizes_every_fail_closed_boundary() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    selected = _matrix(origin, selection, cell_set, role="selected")
    future = _matrix(origin, selection, cell_set, role="future_holdout")
    other_refs = (TaskCheckRef("other-task", "other-check"),)

    cases = (
        (
            replace(selection, origin_id="other-origin"),
            cell_set,
            selected,
            future,
            "origin_mismatch",
        ),
        (
            replace(selection, eligibility_mode="strict_prospective"),
            cell_set,
            selected,
            future,
            "selection_eligibility_mode_mismatch",
        ),
        (
            selection,
            replace(cell_set, selection_id="other-selection"),
            selected,
            future,
            "evaluation_cell_selection_mismatch",
        ),
        (
            selection,
            cell_set,
            selected,
            replace(future, matrix_role="selected"),
            "matrix_role_mismatch",
        ),
        (
            selection,
            cell_set,
            replace(selected, origin_id="other-origin"),
            future,
            "matrix_origin_mismatch",
        ),
        (
            selection,
            cell_set,
            selected,
            replace(future, selection_id="other-selection"),
            "matrix_selection_mismatch",
        ),
        (
            selection,
            cell_set,
            selected,
            replace(future, agent_ids=("other-agent",)),
            "agent_set_mismatch",
        ),
        (
            selection,
            cell_set,
            selected,
            replace(future, join_policy_digest="other-join"),
            "join_policy_mismatch",
        ),
        (
            selection,
            cell_set,
            selected,
            replace(future, denominator_policy_digest="other-denominator"),
            "denominator_policy_mismatch",
        ),
        (
            selection,
            cell_set,
            replace(selected, task_check_refs=other_refs),
            future,
            "selected_denominator_mismatch",
        ),
        (
            selection,
            replace(cell_set, selected_task_check_refs=other_refs),
            selected,
            future,
            "evaluation_selected_denominator_mismatch",
        ),
        (
            selection,
            replace(cell_set, future_task_pool_id="other-task-pool"),
            selected,
            future,
            "evaluation_future_task_pool_mismatch",
        ),
        (
            selection,
            cell_set,
            selected,
            replace(future, task_check_refs=other_refs),
            "future_denominator_mismatch",
        ),
        (
            selection,
            replace(cell_set, future_task_check_refs=other_refs),
            selected,
            future,
            "evaluation_future_denominator_mismatch",
        ),
        (
            selection,
            replace(cell_set, future_censored_task_check_refs=other_refs),
            selected,
            future,
            "evaluation_future_censoring_mismatch",
        ),
        (
            selection,
            cell_set,
            replace(
                selected,
                cells=(
                    replace(
                        selected.cells[0],
                        required_identity_digest="other-identity",
                    ),
                ),
            ),
            future,
            "selected_matrix_cell_identity_mismatch",
        ),
        (
            selection,
            cell_set,
            selected,
            replace(
                future,
                cells=(
                    replace(
                        future.cells[0],
                        required_identity_digest="other-identity",
                    ),
                ),
            ),
            "future_matrix_cell_identity_mismatch",
        ),
    )

    for (
        candidate_selection,
        candidate_cells,
        candidate_selected,
        candidate_future,
        error,
    ) in cases:
        assert (
            _matrix_alignment_error(
                candidate_selection,
                origin,
                candidate_cells,
                candidate_selected,
                candidate_future,
            )
            == error
        )

    assert (
        _matrix_alignment_error(
            replace(selection, origin_id="other-origin"),
            origin,
            cell_set,
            selected,
            replace(future, matrix_role="selected"),
        )
        == "origin_mismatch"
    )

    strict_origin = replace(origin, eligibility_mode="strict_prospective")
    strict_selection = replace(selection, eligibility_mode="strict_prospective")
    assert (
        _matrix_alignment_error(
            strict_selection,
            strict_origin,
            cell_set,
            selected,
            future,
        )
        == "prospective_future_task_pool_mismatch"
    )


def test_evaluate_selection_applies_selected_weights_to_pass_rate_mae() -> None:
    selected_refs = (
        TaskCheckRef("task-a", "check-a"),
        TaskCheckRef("task-b", "check-b"),
    )
    future_refs = (TaskCheckRef("future-task", "future-check"),)
    task_pool = _task_pool(
        ("task-a", "task-b", "future-task"), ("check-a", "check-b", "future-check")
    )
    origin = _origin(task_pool, refs=selected_refs)
    selection = record_with_digest(
        BenchmarkSelectionRecord(
            selection_id="weighted-selection",
            task_pool_id=task_pool.task_pool_id,
            task_pool_digest=task_pool.task_pool_digest,
            origin_id=origin.origin_id,
            selector_id="selector",
            selector_digest="selector-digest",
            selected_task_check_refs=selected_refs,
            selected_weights={
                canonical_digest(selected_refs[0]): 0.9,
                canonical_digest(selected_refs[1]): 0.1,
            },
            budget_digest="budget",
            selection_input_digest="selector-input",
            feature_snapshot_id="feature-snapshot",
            eligibility_mode="counterfactual_replay",
            created_at="2026-01-05T00:00:00Z",
            selection_digest="",
        )
    )
    cells = (
        ResultCellRef(
            "agent",
            "task-a",
            "check-a",
            "identity-a",
            "result-a",
            "digest-a",
            "result",
            None,
            "fail",
        ),
        ResultCellRef(
            "agent",
            "task-b",
            "check-b",
            "identity-b",
            "result-b",
            "digest-b",
            "result",
            None,
            "pass",
        ),
        ResultCellRef(
            "agent",
            "future-task",
            "future-check",
            "future-identity",
            "future-result",
            "future-digest",
            "result",
            None,
            "pass",
        ),
    )
    cell_set = record_with_digest(
        EvaluationCellSet(
            cell_set_id="weighted-cells",
            origin_id=origin.origin_id,
            selection_id=selection.selection_id,
            selected_task_check_refs=selected_refs,
            future_task_check_refs=future_refs,
            future_censored_task_check_refs=(),
            future_task_pool_id=origin.task_pool_id,
            future_task_pool_digest=origin.task_pool_digest,
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

    metrics = evaluate_selection(
        selection,
        origin,
        cell_set,
        selected_matrix,
        future_matrix,
    )
    metrics_by_name = {metric.metric_name: metric.metric_value for metric in metrics}

    assert metrics[0].metric_name == "future_pass_rate_mae"
    assert metrics[0].metric_value == pytest.approx(0.9)
    assert metrics_by_name["pairwise_gap_mae"] == pytest.approx(0.0)
    assert metrics_by_name["rank_agreement"] == pytest.approx(1.0)
    assert metrics_by_name["recommendation_regret"] == pytest.approx(0.0)
    assert {metric.budget_digest for metric in metrics} == {selection.budget_digest}


def test_evaluate_selection_emits_pairwise_rank_and_recommendation_metrics() -> None:
    selected_refs = (
        TaskCheckRef("selected-a", "check-selected-a"),
        TaskCheckRef("selected-b", "check-selected-b"),
    )
    future_refs = (
        TaskCheckRef("future-a", "check-future-a"),
        TaskCheckRef("future-b", "check-future-b"),
    )
    task_pool = _task_pool(
        tuple(ref.task_id for ref in selected_refs + future_refs),
        tuple(ref.check_id for ref in selected_refs + future_refs),
    )
    origin = replace(
        _origin(task_pool, refs=selected_refs),
        future_holdout_task_check_refs=future_refs,
    )
    selection = record_with_digest(
        BenchmarkSelectionRecord(
            selection_id="selection-pairwise",
            task_pool_id=task_pool.task_pool_id,
            task_pool_digest=task_pool.task_pool_digest,
            origin_id=origin.origin_id,
            selector_id="selector",
            selector_digest="selector-digest",
            selected_task_check_refs=selected_refs,
            selected_weights={canonical_digest(ref): 1.0 for ref in selected_refs},
            budget_digest="budget",
            selection_input_digest="selector-input",
            feature_snapshot_id="feature-snapshot",
            eligibility_mode="counterfactual_replay",
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
            future_censored_task_check_refs=(),
            future_task_pool_id=origin.task_pool_id,
            future_task_pool_digest=origin.task_pool_digest,
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

    metrics = evaluate_selection(
        selection,
        origin,
        cell_set,
        selected_matrix,
        future_matrix,
    )
    metrics_by_name = {metric.metric_name: metric.metric_value for metric in metrics}

    assert metrics_by_name["future_pass_rate_mae"] == pytest.approx(0.75)
    assert metrics_by_name["pairwise_gap_mae"] == pytest.approx(1.5)
    assert metrics_by_name["rank_agreement"] == pytest.approx(0.0)
    assert metrics_by_name["recommendation_regret"] == pytest.approx(1.0)
    assert metrics_by_name["future_coverage"] == pytest.approx(1.0)
    assert metrics_by_name["future_invalid_rate"] == pytest.approx(0.0)


def test_evaluate_selection_rejects_wrong_task_pool_selection() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    selected_matrix = _matrix(origin, selection, cell_set, role="selected")
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")
    wrong_pool = record_with_digest(
        replace(selection, task_pool_digest="other-digest", selection_digest="")
    )
    metrics = evaluate_selection(
        wrong_pool,
        origin,
        cell_set,
        selected_matrix,
        future_matrix,
    )

    assert metrics[0].abstention_reason == "selection_task_pool_mismatch"


def test_build_selector_input_rejects_feature_snapshot_origin_or_feature_mismatch() -> (
    None
):
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (_task("task-old", "check-old"),),
        {"check-old": _check("check-old", "task-old")},
        (_result(result_available_at="2026-01-04T00:00:00Z"),),
        FeatureConfig(("task_stratum",)),
    )

    with pytest.raises(ValueError, match="origin_id"):
        build_selector_input(
            origin,
            task_pool,
            replace(snapshot, origin_id="other-origin"),
            (_result(result_available_at="2026-01-04T00:00:00Z"),),
            (_agent(),),
            SelectionBudget(1),
            LeakagePolicy(("task_metadata",), origin.as_of_cutoff),
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
            SelectionBudget(1),
            LeakagePolicy(("task_metadata",), origin.as_of_cutoff),
        )


def test_feature_result_records_bind_their_visible_result_identity() -> None:
    refs = (
        TaskCheckRef("task-old", "check-old"),
        TaskCheckRef("task-other", "check-other"),
    )
    task_pool = _task_pool(
        tuple(ref.task_id for ref in refs),
        tuple(ref.check_id for ref in refs),
    )
    origin = _origin(task_pool, refs)
    result = _result(result_available_at="2026-01-04T00:00:00Z")
    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        tuple(_task(ref.task_id, ref.check_id) for ref in refs),
        {ref.check_id: _check(ref.check_id, ref.task_id) for ref in refs},
        (result,),
        FeatureConfig(("pre_origin_result_count",)),
    )
    aggregate_record = snapshot.feature_records[0]
    result_record = replace(
        aggregate_record,
        feature_scope="result",
        task_id=result.task_id,
        check_id=result.check_id,
        agent_id=result.agent_id,
        result_id=result.result_id,
        result_cache_identity_digest=result.cache_identity.identity_digest,
        feature_name="result_outcome",
        value=result.outcome,
        source_artifact_digest=result.result_digest,
    )

    _ensure_feature_records_match_origin(
        replace(snapshot, feature_records=(result_record,)),
        origin,
        (result,),
    )

    wrong_ref_record = replace(
        result_record,
        task_id=refs[1].task_id,
        check_id=refs[1].check_id,
    )
    with pytest.raises(ValueError, match="result linkage does not match"):
        _ensure_feature_records_match_origin(
            replace(snapshot, feature_records=(wrong_ref_record,)),
            origin,
            (result,),
        )

    wrong_agent_record = replace(result_record, agent_id="other-agent")
    with pytest.raises(ValueError, match="result linkage does not match"):
        _ensure_feature_records_match_origin(
            replace(snapshot, feature_records=(wrong_agent_record,)),
            origin,
            (result,),
        )

    wrong_count_record = replace(aggregate_record, value=2)
    with pytest.raises(ValueError, match="result count does not match"):
        _ensure_feature_records_match_origin(
            replace(snapshot, feature_records=(wrong_count_record,)),
            origin,
            (result,),
        )


def test_build_feature_snapshot_exposes_stratum_not_dependency_cluster() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    task = _task(
        "task-old",
        "check-old",
        dependency_cluster_id="private-dependency-cluster",
        sampling_stratum="public-stratum",
    )

    snapshot = build_feature_snapshot(
        origin,
        task_pool,
        (task,),
        {"check-old": _check("check-old", "task-old")},
        (),
        FeatureConfig(("task_stratum",)),
    )

    assert snapshot.feature_records[0].value == "public-stratum"
    assert snapshot.feature_records[0].value != task.dependency_cluster_id


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

    metrics = evaluate_selection(
        selection,
        origin,
        cell_set,
        wrong_selected,
        future_matrix,
    )

    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].abstention_reason is not None
    assert metrics[0].abstention_reason.startswith("selected_matrix_invalid:")


def test_evaluate_selection_abstains_on_missing_cells() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection, selected_state="missing")
    selected_matrix = _matrix(
        origin,
        selection,
        cell_set,
        role="selected",
        abstention_reason="missing_required_results",
    )
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")

    metrics = evaluate_selection(
        selection,
        origin,
        cell_set,
        selected_matrix,
        future_matrix,
    )

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
        outcome=None,
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
    )

    assert len(metrics) == 1
    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].completeness_state == "abstained"
    assert metrics[0].abstention_reason == (f"{matrix_role}_empty_agent_denominator")


def test_evaluate_selection_abstains_on_partial_agent_exclusion() -> None:
    selection, origin, cell_set, selected_matrix, future_matrix = (
        _selection_evidence_with_task_exclusion(partial=True)
    )

    metrics = evaluate_selection(
        selection,
        origin,
        cell_set,
        selected_matrix,
        future_matrix,
    )

    assert len(metrics) == 1
    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].completeness_state == "abstained"
    assert metrics[0].abstention_reason == "agent_specific_invalid_exclusion"


def test_evaluate_selection_scores_common_task_check_exclusion() -> None:
    selection, origin, cell_set, selected_matrix, future_matrix = (
        _selection_evidence_with_task_exclusion(partial=False)
    )

    metrics = evaluate_selection(
        selection,
        origin,
        cell_set,
        selected_matrix,
        future_matrix,
    )

    assert {metric.metric_name for metric in metrics} == {
        "future_pass_rate_mae",
        "future_coverage",
        "future_invalid_rate",
        "pairwise_gap_mae",
        "rank_agreement",
        "recommendation_regret",
    }
    assert {metric.completeness_state for metric in metrics} == {
        "complete_with_exclusions"
    }
    assert all(metric.abstention_reason is None for metric in metrics)


def test_evaluate_selection_rejects_matrix_with_omitted_agent_denominator_cell() -> (
    None
):
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

    metrics = evaluate_selection(
        selection,
        origin,
        cell_set,
        selected_matrix,
        future_matrix,
    )

    assert len(metrics) == 1
    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].abstention_reason is not None
    assert metrics[0].abstention_reason.startswith("selected_matrix_invalid:")


def test_evaluate_selection_metric_id_changes_with_matrix_evidence() -> None:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    selected_matrix = _matrix(origin, selection, cell_set, role="selected")
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")
    changed_future = record_with_digest(
        replace(future_matrix, matrix_id="future-matrix-rescore", matrix_digest="")
    )

    first = evaluate_selection(
        selection,
        origin,
        cell_set,
        selected_matrix,
        future_matrix,
    )
    second = evaluate_selection(
        selection,
        origin,
        cell_set,
        selected_matrix,
        changed_future,
    )

    assert first[0].metric_name == "future_pass_rate_mae"
    assert second[0].metric_name == "future_pass_rate_mae"
    assert first[0].metric_id != second[0].metric_id


def test_evaluate_selection_rejects_matrix_cell_identity_mismatch_with_cell_set() -> (
    None
):
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    selected_matrix = _matrix(origin, selection, cell_set, role="selected")
    mismatched_cell = replace(
        selected_matrix.cells[0], required_identity_digest="different-identity"
    )
    mismatched_matrix = record_with_digest(
        replace(selected_matrix, cells=(mismatched_cell,), matrix_digest="")
    )
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")

    metrics = evaluate_selection(
        selection,
        origin,
        cell_set,
        mismatched_matrix,
        future_matrix,
    )

    assert len(metrics) == 1
    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].abstention_reason == "selected_matrix_cell_identity_mismatch"


def test_evaluate_selection_rejects_matrix_result_binding_mismatch_with_cell_set() -> (
    None
):
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = _origin(task_pool)
    selection = _selection(origin, task_pool)
    cell_set = _cell_set(origin, selection)
    selected_matrix = _matrix(origin, selection, cell_set, role="selected")
    mismatched_cell = replace(selected_matrix.cells[0], result_id="different-result")
    mismatched_matrix = record_with_digest(
        replace(selected_matrix, cells=(mismatched_cell,), matrix_digest="")
    )
    future_matrix = _matrix(origin, selection, cell_set, role="future_holdout")

    metrics = evaluate_selection(
        selection,
        origin,
        cell_set,
        mismatched_matrix,
        future_matrix,
    )

    assert len(metrics) == 1
    assert metrics[0].metric_name == "selection_evaluation_invalid"
    assert metrics[0].abstention_reason == "selected_matrix_cell_identity_mismatch"


def _origin(
    task_pool: TaskPoolRecord,
    refs: tuple[TaskCheckRef, ...] = (TaskCheckRef("task-old", "check-old"),),
):
    policy_digest = make_rolling_origin_policy_digest(
        as_of_cutoff_rule="origin_time",
        eligibility_mode="counterfactual_replay",
        holdout_overlap_policy="allow_cluster_overlap",
        future_holdout_known=True,
        allowed_dependency_cluster_ids=(),
        maturity_lag_seconds=0,
    )
    origin = __import__(
        "barcarolle.records", fromlist=["RollingOriginRecord"]
    ).RollingOriginRecord(
        origin_id="",
        task_pool_id=task_pool.task_pool_id,
        task_pool_digest=task_pool.task_pool_digest,
        origin_time="2026-01-05T00:00:00Z",
        policy_digest=policy_digest,
        history_task_check_refs=refs,
        history_censored_task_check_refs=(),
        future_holdout_task_check_refs=(TaskCheckRef("future-task", "future-check"),),
        future_censored_task_check_refs=(),
        as_of_cutoff="2026-01-05T00:00:00Z",
        eligibility_mode="counterfactual_replay",
        holdout_overlap_policy="allow_cluster_overlap",
        as_of_cutoff_rule="origin_time",
        history_window_start="2026-01-01T00:00:00Z",
        future_window_start="2026-01-05T00:00:00Z",
        future_window_end="2026-01-10T00:00:00Z",
        future_cohort_time_basis="task_material_available_at",
        maturity_lag_seconds=0,
        label_maturity_cutoff="2026-01-10T00:00:00.000000Z",
        future_holdout_known=True,
        allowed_dependency_cluster_ids=(),
        origin_digest="",
    )
    origin = replace(origin, origin_id=make_rolling_origin_id(origin))
    return record_with_digest(origin)


def _chronological_origin(
    task_pool: TaskPoolRecord,
    day: int,
) -> RollingOriginRecord:
    cutoff = f"2026-01-{day:02d}T00:00:00Z"
    future_end = f"2026-01-{day + 1:02d}T00:00:00Z"
    origin = replace(
        _origin(task_pool),
        origin_id="",
        origin_time=cutoff,
        as_of_cutoff=cutoff,
        future_window_start=cutoff,
        future_window_end=future_end,
        label_maturity_cutoff=f"2026-01-{day + 1:02d}T00:00:00.000000Z",
        origin_digest="",
    )
    origin = replace(origin, origin_id=make_rolling_origin_id(origin))
    return record_with_digest(origin)


def _selection(origin, task_pool: TaskPoolRecord):
    selection = __import__(
        "barcarolle.records", fromlist=["BenchmarkSelectionRecord"]
    ).BenchmarkSelectionRecord(
        selection_id="selection",
        task_pool_id=task_pool.task_pool_id,
        task_pool_digest=task_pool.task_pool_digest,
        origin_id=origin.origin_id,
        selector_id="selector",
        selector_digest="selector-digest",
        selected_task_check_refs=origin.history_task_check_refs,
        selected_weights={canonical_digest(origin.history_task_check_refs[0]): 1.0},
        budget_digest="budget",
        selection_input_digest="selector-input",
        feature_snapshot_id="feature-snapshot",
        eligibility_mode=origin.eligibility_mode,
        created_at="2026-01-05T00:00:00Z",
        selection_digest="",
    )
    return record_with_digest(selection)


def _selection_for_metric(
    origin_id: str,
    selector: SelectorRecord,
    *,
    budget_digest: str = "budget",
) -> BenchmarkSelectionRecord:
    task_pool = _task_pool(("task-old",), ("check-old",))
    origin = replace(_origin(task_pool), origin_id=origin_id)
    selection = replace(
        _selection(origin, task_pool),
        selection_id=f"selection-{origin_id}-{selector.selector_id}",
        selector_id=selector.selector_id,
        selector_digest=selector.selector_digest,
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
        metric_config_digest=evaluation_module.METRIC_CONFIG_DIGEST,
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
    task_count: int = 1,
) -> ResultMatrix:
    refs = tuple(
        TaskCheckRef(
            "future-task" if index == 0 else f"future-task-{index + 1}",
            "future-check" if index == 0 else f"future-check-{index + 1}",
        )
        for index in range(task_count)
    )
    matrix = ResultMatrix(
        matrix_id=f"future-{selection.selection_id}",
        matrix_role="future_holdout",
        origin_id=selection.origin_id,
        selection_id=selection.selection_id,
        agent_ids=("agent",),
        task_check_refs=refs,
        cells=tuple(
            ResultCellRef(
                "agent",
                ref.task_id,
                ref.check_id,
                "future-identity" if index == 0 else f"future-identity-{index + 1}",
                result_id if index == 0 else f"{result_id}-{index + 1}",
                result_digest if index == 0 else f"{result_digest}-{index + 1}",
                "result",
                None,
                "pass",
            )
            for index, ref in enumerate(refs)
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
        future_censored_task_check_refs=origin.future_censored_task_check_refs,
        future_task_pool_id=origin.task_pool_id,
        future_task_pool_digest=origin.task_pool_digest,
        cells=(
            ResultCellRef(
                "agent",
                "task-old",
                "check-old",
                "identity",
                "result" if selected_state == "result" else None,
                "digest" if selected_state == "result" else None,
                selected_state,
                None,
                "pass" if selected_state == "result" else None,
            ),
            ResultCellRef(
                "agent",
                "future-task",
                "future-check",
                "future-identity",
                "future-result",
                "future-digest",
                "result",
                None,
                "pass",
            ),
        ),
        abstention_reason=None,
        cell_set_digest="",
    )
    return record_with_digest(cell_set)


def _matrix(
    origin, selection, cell_set, role: str, abstention_reason: str | None = None
):
    refs = (
        origin.history_task_check_refs
        if role == "selected"
        else origin.future_holdout_task_check_refs
    )
    matrix = ResultMatrix(
        matrix_id=f"matrix-{role}",
        matrix_role=role,
        origin_id=origin.origin_id,
        selection_id=selection.selection_id,
        agent_ids=("agent",),
        task_check_refs=refs,
        cells=tuple(
            cell
            for cell in cell_set.cells
            if (cell.task_id, cell.check_id)
            in {(ref.task_id, ref.check_id) for ref in refs}
        ),
        join_policy_digest="join",
        denominator_policy_digest="denominator",
        abstention_reason=abstention_reason,
        scoreable_state="abstained" if abstention_reason else "complete",
        matrix_digest="",
    )
    return record_with_digest(matrix)


def _selection_evidence_with_task_exclusion(*, partial: bool):
    kept_ref = TaskCheckRef("task-old", "check-old")
    excluded_ref = TaskCheckRef("task-excluded", "check-excluded")
    future_ref = TaskCheckRef("future-task", "future-check")
    task_pool = _task_pool(
        (kept_ref.task_id, excluded_ref.task_id),
        (kept_ref.check_id, excluded_ref.check_id),
    )
    origin = _origin(task_pool, refs=(kept_ref, excluded_ref))
    selection = record_with_digest(
        replace(
            _selection(origin, task_pool),
            selected_weights={
                canonical_digest(kept_ref): 1.0,
                canonical_digest(excluded_ref): 1.0,
            },
            selection_digest="",
        )
    )
    agents = ("agent", "other-agent")
    cells: list[ResultCellRef] = []
    for agent_id in agents:
        cells.append(
            ResultCellRef(
                agent_id,
                kept_ref.task_id,
                kept_ref.check_id,
                f"{agent_id}-kept-identity",
                f"{agent_id}-kept-result",
                f"{agent_id}-kept-digest",
                "result",
                None,
                "pass",
            )
        )
        excluded_for_agent = not partial or agent_id == "agent"
        cells.append(
            ResultCellRef(
                agent_id,
                excluded_ref.task_id,
                excluded_ref.check_id,
                f"{agent_id}-excluded-identity",
                f"{agent_id}-excluded-result",
                f"{agent_id}-excluded-digest",
                "excluded" if excluded_for_agent else "result",
                "task_check_infrastructure_failure" if excluded_for_agent else None,
                "invalid" if excluded_for_agent else "pass",
            )
        )
        cells.append(
            ResultCellRef(
                agent_id,
                future_ref.task_id,
                future_ref.check_id,
                f"{agent_id}-future-identity",
                f"{agent_id}-future-result",
                f"{agent_id}-future-digest",
                "result",
                None,
                "pass",
            )
        )
    cell_set = record_with_digest(
        EvaluationCellSet(
            cell_set_id="cell-set-with-exclusion",
            origin_id=origin.origin_id,
            selection_id=selection.selection_id,
            selected_task_check_refs=(kept_ref, excluded_ref),
            future_task_check_refs=(future_ref,),
            future_censored_task_check_refs=(),
            future_task_pool_id=origin.task_pool_id,
            future_task_pool_digest=origin.task_pool_digest,
            cells=tuple(cells),
            abstention_reason=None,
            cell_set_digest="",
        )
    )
    selected_keys = {
        (kept_ref.task_id, kept_ref.check_id),
        (excluded_ref.task_id, excluded_ref.check_id),
    }
    selected_matrix = record_with_digest(
        ResultMatrix(
            matrix_id="matrix-selected-with-exclusion",
            matrix_role="selected",
            origin_id=origin.origin_id,
            selection_id=selection.selection_id,
            agent_ids=agents,
            task_check_refs=(kept_ref, excluded_ref),
            cells=tuple(
                cell for cell in cells if (cell.task_id, cell.check_id) in selected_keys
            ),
            join_policy_digest="join",
            denominator_policy_digest="denominator",
            abstention_reason=None,
            scoreable_state="complete_with_exclusions",
            matrix_digest="",
        )
    )
    future_matrix = record_with_digest(
        ResultMatrix(
            matrix_id="matrix-future-with-exclusion",
            matrix_role="future_holdout",
            origin_id=origin.origin_id,
            selection_id=selection.selection_id,
            agent_ids=agents,
            task_check_refs=(future_ref,),
            cells=tuple(
                cell
                for cell in cells
                if (cell.task_id, cell.check_id)
                == (future_ref.task_id, future_ref.check_id)
            ),
            join_policy_digest="join",
            denominator_policy_digest="denominator",
            abstention_reason=None,
            scoreable_state="complete",
            matrix_digest="",
        )
    )
    return selection, origin, cell_set, selected_matrix, future_matrix


@dataclass(frozen=True)
class _TrainingEvidence:
    deployment_origin: RollingOriginRecord
    task_pool: TaskPoolRecord
    tasks: tuple[TaskRecord, ...]
    checks: Mapping[str, CheckRecord]
    training_origins: tuple[RollingOriginRecord, ...]
    feature_snapshots: tuple[FeatureSnapshotRecord, ...]
    selector_inputs: tuple[SelectorInput, ...]
    expert_selectors: tuple[SelectorRecord, ...]
    selections: tuple[BenchmarkSelectionRecord, ...]
    result_matrices: tuple[ResultMatrix, ...]
    metrics: tuple[MetricRecord, ...]
    pre_origin_results: tuple[ResultRecord, ...]
    training_results: tuple[ResultRecord, ...]


def _train_from_evidence(
    evidence: _TrainingEvidence,
    *,
    selector_family: str = "rule_mixture",
) -> SelectorRecord:
    return train_selector(
        selector_family,
        deployment_origin=evidence.deployment_origin,
        task_pool=evidence.task_pool,
        tasks=evidence.tasks,
        checks=evidence.checks,
        training_origins=evidence.training_origins,
        feature_snapshots=evidence.feature_snapshots,
        selector_inputs=evidence.selector_inputs,
        expert_selectors=evidence.expert_selectors,
        selections=evidence.selections,
        result_matrices=evidence.result_matrices,
        metrics=evidence.metrics,
        pre_origin_results=evidence.pre_origin_results,
        training_results=evidence.training_results,
    )


def _redigest_training_agent_inputs(
    evidence: _TrainingEvidence,
    origin_ids: set[str],
    agent_record_digest: str,
) -> _TrainingEvidence:
    snapshot_by_origin = {
        snapshot.origin_id: snapshot for snapshot in evidence.feature_snapshots
    }
    input_by_origin: dict[str, SelectorInput] = {}
    updated_inputs: list[SelectorInput] = []
    for selector_input in evidence.selector_inputs:
        updated = selector_input
        if selector_input.origin_id in origin_ids:
            updated = replace(
                selector_input,
                selector_input_id="",
                agent_record_digests=(agent_record_digest,),
                selector_input_digest="",
            )
            updated = replace(
                updated,
                selector_input_id=make_selector_input_id(updated),
            )
            updated = record_with_digest(updated)
        input_by_origin[updated.origin_id] = updated
        updated_inputs.append(updated)

    expert_by_id = {expert.selector_id: expert for expert in evidence.expert_selectors}
    selection_by_old_id: dict[str, BenchmarkSelectionRecord] = {}
    updated_selections: list[BenchmarkSelectionRecord] = []
    for selection in evidence.selections:
        updated = selection
        if selection.origin_id in origin_ids:
            updated = select_with_selector(
                input_by_origin[selection.origin_id],
                snapshot_by_origin[selection.origin_id],
                expert_by_id[selection.selector_id],
            )
        selection_by_old_id[selection.selection_id] = updated
        updated_selections.append(updated)

    updated_matrices: list[ResultMatrix] = []
    matrices_by_selection: dict[str, dict[str, ResultMatrix]] = {}
    for matrix in evidence.result_matrices:
        updated_selection = selection_by_old_id[matrix.selection_id]
        updated = matrix
        if updated_selection.selection_id != matrix.selection_id:
            updated = record_with_digest(
                replace(
                    matrix,
                    matrix_id=(
                        f"matrix-{matrix.matrix_role}-{updated_selection.selection_id}"
                    ),
                    selection_id=updated_selection.selection_id,
                    matrix_digest="",
                )
            )
        updated_matrices.append(updated)
        matrices_by_selection.setdefault(updated.selection_id, {})[
            updated.matrix_role
        ] = updated

    updated_metrics: list[MetricRecord] = []
    for metric in evidence.metrics:
        updated_selection = selection_by_old_id[metric.selection_id]
        updated = metric
        if updated_selection.selection_id != metric.selection_id:
            matrices = matrices_by_selection[updated_selection.selection_id]
            updated = record_with_digest(
                replace(
                    metric,
                    metric_id=f"metric-{updated_selection.selection_id}",
                    selection_id=updated_selection.selection_id,
                    evaluation_cell_set_digest=(
                        f"cells-{updated_selection.selection_id}"
                    ),
                    selected_matrix_digest=matrices["selected"].matrix_digest,
                    future_matrix_digest=matrices["future_holdout"].matrix_digest,
                    metric_digest="",
                )
            )
        updated_metrics.append(updated)

    return replace(
        evidence,
        selector_inputs=tuple(updated_inputs),
        selections=tuple(updated_selections),
        result_matrices=tuple(updated_matrices),
        metrics=tuple(updated_metrics),
    )


def _redigest_training_result_task_identities(
    evidence: _TrainingEvidence,
) -> _TrainingEvidence:
    result_by_id: dict[str, ResultRecord] = {}
    for result in evidence.training_results:
        identity = record_with_digest(
            replace(
                result.cache_identity,
                base_commit="b" * 40,
                identity_digest="",
            )
        )
        result_by_id[result.result_id] = _redigest_result(
            result,
            cache_identity=identity,
        )

    matrices_by_selection: dict[str, dict[str, ResultMatrix]] = {}
    updated_matrices: list[ResultMatrix] = []
    for matrix in evidence.result_matrices:
        cells = tuple(
            replace(
                cell,
                result_id=result_by_id[cell.result_id or ""].result_id,
                required_identity_digest=result_by_id[
                    cell.result_id or ""
                ].cache_identity.identity_digest,
                result_digest=result_by_id[cell.result_id or ""].result_digest,
            )
            for cell in matrix.cells
        )
        updated = record_with_digest(
            replace(
                matrix,
                cells=cells,
                matrix_digest="",
            )
        )
        updated_matrices.append(updated)
        matrices_by_selection.setdefault(updated.selection_id, {})[
            updated.matrix_role
        ] = updated

    updated_metrics = tuple(
        record_with_digest(
            replace(
                metric,
                selected_matrix_digest=matrices_by_selection[metric.selection_id][
                    "selected"
                ].matrix_digest,
                future_matrix_digest=matrices_by_selection[metric.selection_id][
                    "future_holdout"
                ].matrix_digest,
                metric_digest="",
            )
        )
        for metric in evidence.metrics
    )
    return replace(
        evidence,
        result_matrices=tuple(updated_matrices),
        metrics=updated_metrics,
        training_results=tuple(result_by_id.values()),
    )


def _training_evidence(
    *,
    deployment_mode: str = "counterfactual_replay",
    deployment_time: str = "2026-01-11T00:00:00Z",
    result_available_at: str = "2026-01-09T00:00:00Z",
    training_origin_times: tuple[str, ...] = ("2026-01-05T00:00:00Z",),
    include_pre_origin_result: bool = False,
    selection_budget_limit: int = 1,
) -> _TrainingEvidence:
    join_config = ResultJoinConfig()
    history_refs = tuple(
        TaskCheckRef(f"task-old-{index}", f"check-old-{index}") for index in range(1, 4)
    )
    future_ref = TaskCheckRef("task-future", "check-future")
    refs = (*history_refs, future_ref)
    available_at = {
        history_refs[0]: "2026-01-02T00:00:00Z",
        history_refs[1]: "2026-01-03T00:00:00Z",
        history_refs[2]: "2026-01-04T00:00:00Z",
        future_ref: "2026-01-07T00:00:00Z",
    }
    tasks = tuple(
        _task(
            ref.task_id,
            ref.check_id,
            available_at=available_at[ref],
        )
        for ref in refs
    )
    checks = {
        ref.check_id: _check(
            ref.check_id,
            ref.task_id,
            available_at=available_at[ref],
        )
        for ref in refs
    }
    task_pool = _task_pool(
        tuple(ref.task_id for ref in refs),
        tuple(ref.check_id for ref in refs),
    )
    task_pool = record_with_digest(
        replace(
            task_pool,
            task_records_digest=canonical_digest(tasks),
            check_records_digest=canonical_digest(
                tuple(checks[check_id] for check_id in task_pool.check_ids)
            ),
            task_pool_digest="",
        )
    )
    training_origins = tuple(
        build_rolling_origin(
            task_pool,
            tasks,
            checks,
            parse_utc_timestamp(origin_time),
            TimeRange(origin_time, "2026-01-10T00:00:00Z"),
            RollingOriginPolicy(
                "origin_time",
                "counterfactual_replay",
                "allow_cluster_overlap",
                True,
            ),
        )
        for origin_time in training_origin_times
    )
    deployment_origin = build_rolling_origin(
        task_pool,
        tasks,
        checks,
        parse_utc_timestamp(deployment_time),
        TimeRange(deployment_time, "2026-01-20T00:00:00Z"),
        RollingOriginPolicy(
            "origin_time",
            deployment_mode,
            "allow_cluster_overlap",
            deployment_mode != "strict_prospective",
        ),
    )
    pre_origin_results: tuple[ResultRecord, ...] = ()
    allowed_feature_classes = ("task_metadata",)
    feature_names = ("task_count",)
    if include_pre_origin_result:
        pre_origin_result = _result(
            "2026-01-04T00:00:00Z",
            task_id=history_refs[0].task_id,
            check_id=history_refs[0].check_id,
        )
        pre_origin_results = (pre_origin_result,)
        allowed_feature_classes = ("task_metadata", "pre_origin_result")
        feature_names = ("task_count", "pre_origin_result_count")
    feature_config = FeatureConfig(feature_names)
    feature_snapshots = tuple(
        build_feature_snapshot(
            training_origin,
            task_pool,
            tasks,
            checks,
            pre_origin_results,
            feature_config,
        )
        for training_origin in training_origins
    )
    selector_inputs = tuple(
        build_selector_input(
            training_origin,
            task_pool,
            snapshot,
            pre_origin_results,
            (_agent(),),
            SelectionBudget(selection_budget_limit),
            LeakagePolicy(allowed_feature_classes, training_origin.as_of_cutoff),
        )
        for training_origin, snapshot in zip(
            training_origins, feature_snapshots, strict=True
        )
    )
    experts = (
        build_rule_selector(
            "coverage",
            {
                "group_by_ref_key": {
                    canonical_digest(ref): f"group-{index}"
                    for index, ref in enumerate(history_refs)
                }
            },
            allowed_feature_classes=allowed_feature_classes,
        ),
        build_rule_selector(
            "random",
            {"seed": 7},
            allowed_feature_classes=allowed_feature_classes,
        ),
        build_rule_selector(
            "recency",
            allowed_feature_classes=allowed_feature_classes,
        ),
    )
    selections = tuple(
        select_with_selector(selector_input, snapshot, expert)
        for selector_input, snapshot in zip(
            selector_inputs, feature_snapshots, strict=True
        )
        for expert in experts
    )
    result_refs = tuple(
        dict.fromkeys(
            (
                *(
                    ref
                    for selection in selections
                    for ref in selection.selected_task_check_refs
                ),
                *(
                    ref
                    for training_origin in training_origins
                    for ref in training_origin.future_holdout_task_check_refs
                ),
            )
        )
    )
    result_by_ref: dict[TaskCheckRef, ResultRecord] = {}
    for ref in result_refs:
        result = _result(
            result_available_at,
            task_id=ref.task_id,
            check_id=ref.check_id,
        )
        result_by_ref[ref] = result

    matrices: list[ResultMatrix] = []
    metrics: list[MetricRecord] = []
    origin_by_id = {origin.origin_id: origin for origin in training_origins}
    for selection in selections:
        training_origin = origin_by_id[selection.origin_id]
        selection_matrices = []
        for role, matrix_refs in (
            ("selected", selection.selected_task_check_refs),
            (
                "future_holdout",
                training_origin.future_holdout_task_check_refs,
            ),
        ):
            cells = tuple(
                ResultCellRef(
                    "agent",
                    ref.task_id,
                    ref.check_id,
                    result_by_ref[ref].cache_identity.identity_digest,
                    result_by_ref[ref].result_id,
                    result_by_ref[ref].result_digest,
                    "result",
                    None,
                    result_by_ref[ref].outcome,
                )
                for ref in matrix_refs
            )
            matrix = record_with_digest(
                ResultMatrix(
                    matrix_id=f"matrix-{role}-{selection.selection_id}",
                    matrix_role=role,
                    origin_id=training_origin.origin_id,
                    selection_id=selection.selection_id,
                    agent_ids=("agent",),
                    task_check_refs=matrix_refs,
                    cells=cells,
                    join_policy_digest=join_config.join_policy_digest,
                    denominator_policy_digest=join_config.denominator_policy_digest,
                    abstention_reason=None,
                    scoreable_state="complete",
                    matrix_digest="",
                )
            )
            matrices.append(matrix)
            selection_matrices.append(matrix)
        selected_matrix, future_matrix = selection_matrices
        metrics.append(
            record_with_digest(
                MetricRecord(
                    metric_id=f"metric-{selection.selection_id}",
                    origin_id=training_origin.origin_id,
                    selection_id=selection.selection_id,
                    evaluation_cell_set_digest=f"cells-{selection.selection_id}",
                    selected_matrix_digest=selected_matrix.matrix_digest,
                    future_matrix_digest=future_matrix.matrix_digest,
                    join_policy_digest=join_config.join_policy_digest,
                    metric_config_digest=evaluation_module.METRIC_CONFIG_DIGEST,
                    metric_scope="aggregate",
                    agent_id=None,
                    agent_pair=None,
                    aggregation_level="all_agents",
                    budget_digest=selection.budget_digest,
                    stratum_ref=None,
                    metric_name="future_pass_rate_mae",
                    metric_value=0.0,
                    denominator_policy_digest=join_config.denominator_policy_digest,
                    completeness_state="complete",
                    abstention_reason=None,
                    computed_at="2026-02-02T00:00:00Z",
                    metric_digest="",
                )
            )
        )
    return _TrainingEvidence(
        deployment_origin=deployment_origin,
        task_pool=task_pool,
        tasks=tasks,
        checks=checks,
        training_origins=training_origins,
        feature_snapshots=feature_snapshots,
        selector_inputs=selector_inputs,
        expert_selectors=experts,
        selections=selections,
        result_matrices=tuple(matrices),
        metrics=tuple(metrics),
        pre_origin_results=pre_origin_results,
        training_results=tuple(result_by_ref.values()),
    )


def _training_evidence_with_bound_exclusion(
    *,
    justified: bool = True,
) -> tuple[
    _TrainingEvidence,
    ResultRecord,
]:
    evidence = _training_evidence(selection_budget_limit=3)
    selected_matrix = next(
        matrix
        for matrix in evidence.result_matrices
        if matrix.matrix_role == "selected"
    )
    target_cell = selected_matrix.cells[0]
    source_result = next(
        result
        for result in evidence.training_results
        if result.result_id == target_cell.result_id
    )
    excluded_result = source_result
    if justified:
        excluded_result = _redigest_result(
            source_result,
            terminal_status="invalid",
            scoreable_state="benchmark_invalid",
            outcome="invalid",
            invalid_owner="benchmark",
            failure_label="check_failed",
        )
    exclusion_reason = (
        "task_check_infrastructure_failure:"
        f"check_failed:{excluded_result.result_digest}"
        if justified
        else "unjustified_exclusion"
    )
    matrices: list[ResultMatrix] = []
    for matrix in evidence.result_matrices:
        cells = tuple(
            replace(
                cell,
                result_id=excluded_result.result_id,
                result_digest=excluded_result.result_digest,
                cell_state="excluded",
                exclusion_reason=exclusion_reason,
                outcome=excluded_result.outcome,
            )
            if cell.result_id == source_result.result_id
            else cell
            for cell in matrix.cells
        )
        scoreable_state = (
            "complete_with_exclusions"
            if cells != matrix.cells
            else matrix.scoreable_state
        )
        matrices.append(
            record_with_digest(
                replace(
                    matrix,
                    cells=cells,
                    scoreable_state=scoreable_state,
                    matrix_digest="",
                )
            )
        )
    matrices_by_selection = {
        selection.selection_id: {
            matrix.matrix_role: matrix
            for matrix in matrices
            if matrix.selection_id == selection.selection_id
        }
        for selection in evidence.selections
    }
    metrics = tuple(
        record_with_digest(
            replace(
                metric,
                selected_matrix_digest=matrices_by_selection[metric.selection_id][
                    "selected"
                ].matrix_digest,
                future_matrix_digest=matrices_by_selection[metric.selection_id][
                    "future_holdout"
                ].matrix_digest,
                completeness_state=(
                    "complete_with_exclusions"
                    if "complete_with_exclusions"
                    in {
                        matrices_by_selection[metric.selection_id][
                            "selected"
                        ].scoreable_state,
                        matrices_by_selection[metric.selection_id][
                            "future_holdout"
                        ].scoreable_state,
                    }
                    else "complete"
                ),
                metric_digest="",
            )
        )
        for metric in evidence.metrics
    )
    return (
        replace(
            evidence,
            result_matrices=tuple(matrices),
            metrics=metrics,
            training_results=tuple(
                excluded_result
                if result.result_id == source_result.result_id
                else result
                for result in evidence.training_results
            ),
        ),
        excluded_result,
    )


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
        source_event_records_ref="source-events.jsonl",
        source_event_records_digest="source-events",
        rejected_candidate_ids=(),
        rejection_summary_digest="rejections",
        certification_evidence_digest="evidence",
        generation_provenance_ref="generation-provenance.jsonl",
        generation_provenance_digest="generation-provenance",
        generator_config_digest="generator",
        source_protocol_digest="source-protocol",
        certification_config_digest="certification",
        created_at="2026-01-01T00:00:00Z",
    )
    return record_with_digest(record)


def _task(
    task_id: str,
    check_id: str,
    available_at: str = "2026-01-02T00:00:00Z",
    dependency_cluster_id: str = "dependency-cluster",
    sampling_stratum: str = "stratum",
) -> TaskRecord:
    task_text = f"Task {task_id}"
    solver_material_refs = ("README.md",)
    return TaskRecord(
        task_id=task_id,
        repository_id="repo",
        base_commit="a" * 40,
        source_family="issue",
        source_ref=f"issue-{task_id}",
        source_resolved_at=available_at,
        task_material_available_at=available_at,
        task_text=task_text,
        solver_material_digest=make_solver_material_digest(
            task_text, solver_material_refs
        ),
        solver_material_refs=solver_material_refs,
        check_ids=(check_id,),
        dependency_cluster_id=dependency_cluster_id,
        sampling_stratum=sampling_stratum,
    )


def _check(
    check_id: str, task_id: str, available_at: str = "2026-01-02T00:00:00Z"
) -> CheckRecord:
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
        requested_model_id="model",
        model_snapshot_id="model",
        model_resolution_scope_id=None,
        model_resolution_scope_started_at=None,
        model_resolution_scope_ended_at=None,
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
        "stratified_forecast": {
            "dirichlet_alpha": 1.0,
            "trailing_ref_count": 10,
            "seed": 7,
            "weight_cap": 3.0,
        },
    }.get(family, {})
    return record_with_digest(
        SelectorRecord(
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
            selector_digest="",
        )
    )


def _simplex_selector(
    selectors: tuple[SelectorRecord, ...],
    weights: tuple[float, float, float],
) -> SelectorRecord:
    families = ("coverage", "random", "recency")
    for selector in selectors:
        expert_weights = selector.parameters["expert_weights"]
        if isinstance(expert_weights, dict) and tuple(
            expert_weights[family] for family in families
        ) == pytest.approx(weights):
            return selector
    raise AssertionError(f"simplex grid is missing weights {weights}")


def _rule_mixture_selector(parameters: dict[str, object]) -> SelectorRecord:
    selector = _selector("selector-rule-mixture", "rule_mixture")
    return record_with_digest(
        replace(
            selector,
            parameters=parameters,
            config_digest=canonical_digest(
                {"selector_family": "rule_mixture", "parameters": parameters}
            ),
            selector_digest="",
        )
    )


def _rolling_policy(
    future_holdout_known: bool = False,
    allowed_dependency_cluster_ids: tuple[str, ...] = (),
) -> RollingOriginPolicy:
    return RollingOriginPolicy(
        as_of_cutoff_rule="origin_time",
        eligibility_mode="counterfactual_replay",
        holdout_overlap_policy="allow_cluster_overlap",
        future_holdout_known=future_holdout_known,
        allowed_dependency_cluster_ids=allowed_dependency_cluster_ids,
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
        base_commit="a" * 40,
        submodule_state_digest="submodules",
        solver_material_digest=make_solver_material_digest(
            task_text, solver_material_refs
        ),
        check_digest=make_check_digest(_check(check_id, task_id)),
        agent_manifest_digest=f"manifest-{agent_id}",
        requested_model_id="model",
        model_snapshot_id="model",
        model_resolution_scope_id=None,
        model_resolution_scope_started_at=None,
        model_resolution_scope_ended_at=None,
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
        result_id="",
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
        evidence_source_kind="barcarolle_managed",
        evidence_source_manifest_digest=None,
        evidence_imported_at=None,
        source_result_available_at=result_available_at,
        availability_policy="managed_observation_v1",
        result_available_at=result_available_at,
    )
    return record_with_digest(replace(result, result_id=make_result_id(result)))


def _redigest_result(
    result: ResultRecord,
    **changes: object,
) -> ResultRecord:
    draft = replace(
        result,
        result_id="",
        result_digest="",
        **changes,
    )
    return record_with_digest(replace(draft, result_id=make_result_id(draft)))


def _result_with_mismatched_identity(result: ResultRecord) -> ResultRecord:
    cache_identity = record_with_digest(
        replace(
            result.cache_identity,
            task_id=f"{result.task_id}-different",
            identity_digest="",
        )
    )
    return _redigest_result(result, cache_identity=cache_identity)


def _result_with_stale_check_identity(result: ResultRecord) -> ResultRecord:
    cache_identity = record_with_digest(
        replace(
            result.cache_identity,
            check_digest="stale-check",
            identity_digest="",
        )
    )
    return _redigest_result(result, cache_identity=cache_identity)


def _result_with_wrong_agent_identity(result: ResultRecord) -> ResultRecord:
    cache_identity = record_with_digest(
        replace(
            result.cache_identity,
            agent_manifest_digest="manifest-other-agent-version",
            identity_digest="",
        )
    )
    return _redigest_result(result, cache_identity=cache_identity)
