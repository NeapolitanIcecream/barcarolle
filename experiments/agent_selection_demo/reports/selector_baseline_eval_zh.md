# Selector Baseline Eval

生成日期：2026-06-14

## Scope

本 package 只使用 committed sanitized score tables，没有新 paid cells。所有 selector 在固定 task IDs 后才 join Selection 和 Holdout outcomes。

## Random baselines

| Baseline | k | Seeds | Unique samples | MAE mean | Pairwise mean | Top-1 forced | Regret mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `uniform_random_same_budget` | `10` | `1000` | `995` | `0.152775` | `0.365667` | `0.33` | `0.268` |
| `quality_filtered_random` | `10` | `1000` | `995` | `0.152775` | `0.365667` | `0.33` | `0.268` |
| `stratified_random` | `10` | `1000` | `966` | `0.1517` | `0.361667` | `0.315` | `0.274` |
| `uniform_random_same_budget` | `20` | `1000` | `1` | `0.1375` | `0.333333` | `0.0` | `0.4` |
| `quality_filtered_random` | `20` | `1000` | `1` | `0.1375` | `0.333333` | `0.0` | `0.4` |
| `stratified_random` | `20` | `1000` | `1` | `0.1375` | `0.333333` | `0.0` | `0.4` |

## RSQ

| Selector | k | Selected tasks | MAE | Pairwise agreement | Forced top | Later top | Forced regret | MAE percentile vs stratified random |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| `rsq_recency_stratified_quota` | `10` | `10` | `0.25` | `0.5` | `kilo_gpt_5_4` | `kilo_gpt_5_4` | `0.0` | `0.012` |
| `rsq_recency_stratified_quota` | `20` | `20` | `0.1375` | `0.333333` | `codex_gpt_5_4` | `kilo_gpt_5_4` | `0.4` | `1.0` |

## Interpretation

最佳 RSQ slice 是 `rsq_recency_stratified_quota__k20`，MAE `0.1375`。它把 source/recency quota 固定在 metadata 层，并在每个 quota 内偏好较新的任务和 module cap。

Package 3 的 forced top/regret 只是诊断口径；真正的 recommend/abstain/need-more-evidence 由 Package 5 的 shared decision wrapper 统一处理，避免在 selection tie 上硬推荐。
