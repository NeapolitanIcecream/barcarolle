"""Public Selection API."""

from .algorithms import (
    CoverageConfig,
    SelectionConfig,
    select_coverage,
    select_random,
    select_recency,
    select_rule_mixture,
    select_with_selector,
)
from .core import (
    SelectorEvaluationConfig,
    SelectorTrainingConfig,
    freeze_evaluation_selections,
    select_benchmark,
    train_selector,
)
from .evaluation import (
    MetricConfig,
    choose_selector_by_mean_mae,
    choose_selector_from_metrics,
    evaluate_selection,
    fit_rule_mixture_from_metrics,
)
from .features import FeatureConfig, LeakagePolicy, build_feature_snapshot, lint_feature_snapshot
from .inputs import SelectionBudget, build_selector_input
from .origin import RollingOriginPolicy, build_rolling_origin

__all__ = [
    "CoverageConfig",
    "FeatureConfig",
    "LeakagePolicy",
    "MetricConfig",
    "RollingOriginPolicy",
    "SelectionBudget",
    "SelectionConfig",
    "SelectorEvaluationConfig",
    "SelectorTrainingConfig",
    "build_feature_snapshot",
    "build_rolling_origin",
    "build_selector_input",
    "choose_selector_by_mean_mae",
    "choose_selector_from_metrics",
    "evaluate_selection",
    "fit_rule_mixture_from_metrics",
    "freeze_evaluation_selections",
    "lint_feature_snapshot",
    "select_benchmark",
    "select_coverage",
    "select_random",
    "select_recency",
    "select_rule_mixture",
    "select_with_selector",
    "train_selector",
]
