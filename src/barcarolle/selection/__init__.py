"""Public Selection API."""

from .algorithms import (
    build_rule_mixture_grid,
    build_rule_selector,
    ensure_selector_executable,
    ensure_selection_replay,
    select_with_selector,
    summarize_stratified_forecast,
)
from .core import (
    SelectorEvaluationConfig,
)
from .evaluation import (
    EWMASwitchConfig,
    SafeSwitchConfig,
    SimplexChoiceConfig,
    choose_rule_mixture_from_grid,
    choose_selector_from_metrics,
    choose_selector_with_ewma_guard,
    choose_selector_with_safe_switch,
    evaluate_selection,
    summarize_selector_mae,
    train_selector,
)
from .features import (
    FeatureConfig,
    LeakagePolicy,
    build_feature_snapshot,
    ensure_feature_snapshot_task_metadata_provenance,
    lint_feature_snapshot,
)
from .inputs import (
    SelectionBudget,
    build_selector_input,
    ensure_selector_input_result_evidence,
)
from .origin import (
    RollingOriginPolicy,
    build_rolling_origin,
    materialize_prospective_future_cohort,
    compare_arrival_and_label_time_cohorts,
    validate_rolling_origin_against_records,
)

__all__ = [
    "EWMASwitchConfig",
    "FeatureConfig",
    "LeakagePolicy",
    "RollingOriginPolicy",
    "SafeSwitchConfig",
    "SelectionBudget",
    "SimplexChoiceConfig",
    "SelectorEvaluationConfig",
    "build_rule_selector",
    "build_rule_mixture_grid",
    "build_feature_snapshot",
    "build_rolling_origin",
    "materialize_prospective_future_cohort",
    "build_selector_input",
    "choose_selector_from_metrics",
    "choose_selector_with_ewma_guard",
    "choose_selector_with_safe_switch",
    "choose_rule_mixture_from_grid",
    "compare_arrival_and_label_time_cohorts",
    "evaluate_selection",
    "ensure_selector_executable",
    "ensure_selection_replay",
    "ensure_feature_snapshot_task_metadata_provenance",
    "ensure_selector_input_result_evidence",
    "lint_feature_snapshot",
    "select_with_selector",
    "summarize_stratified_forecast",
    "summarize_selector_mae",
    "train_selector",
    "validate_rolling_origin_against_records",
]
