# Selector Decision Eval

生成日期：2026-06-14

## Decision rule

决策层输出三种状态：`recommend`、`abstain_indistinguishable`、`need_more_evidence`。它不会在 Selection tie 上硬推荐；k=10 小样本下要求 top Agent 对每个 competitor 的 common-valid paired comparison 没有 discordant loss。

## Selector decisions

| Selector | k | State | Recommended | Selection margin | Later top | Later margin | MAE | Regret | Top-pair agree | Reason |
| --- | ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- |
| `rsq_recency_stratified_quota` | `10` | `abstain_indistinguishable` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.25` | `None` | `None` | `selected_top_margin_below_action_threshold_or_tied` |
| `rsq_recency_stratified_quota` | `20` | `abstain_indistinguishable` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.1375` | `None` | `None` | `selected_top_margin_below_action_threshold_or_tied` |
| `hrd_50_50` | `10` | `recommend` | `kilo_gpt_5_4` | `0.2` | `kilo_gpt_5_4` | `0.1` | `0.1` | `0.0` | `True` | `top_agent_margin_and_paired_small_sample_fallback_passed` |
| `hrd_50_50` | `20` | `abstain_indistinguishable` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.1375` | `None` | `None` | `selected_top_margin_below_action_threshold_or_tied` |
| `hrd_60_40` | `10` | `recommend` | `kilo_gpt_5_4` | `0.2` | `kilo_gpt_5_4` | `0.1` | `0.1` | `0.0` | `True` | `top_agent_margin_and_paired_small_sample_fallback_passed` |
| `hrd_60_40` | `20` | `abstain_indistinguishable` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.1375` | `None` | `None` | `selected_top_margin_below_action_threshold_or_tied` |
| `hrd_70_30` | `10` | `recommend` | `kilo_gpt_5_4` | `0.2` | `kilo_gpt_5_4` | `0.1` | `0.1` | `0.0` | `True` | `top_agent_margin_and_paired_small_sample_fallback_passed` |
| `hrd_70_30` | `20` | `abstain_indistinguishable` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.1375` | `None` | `None` | `selected_top_margin_below_action_threshold_or_tied` |
| `hrd_disagreement_only` | `10` | `recommend` | `kilo_gpt_5_4` | `0.2` | `kilo_gpt_5_4` | `0.1` | `0.1` | `0.0` | `True` | `top_agent_margin_and_paired_small_sample_fallback_passed` |
| `hrd_disagreement_only` | `20` | `abstain_indistinguishable` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.1375` | `None` | `None` | `selected_top_margin_below_action_threshold_or_tied` |
| `hrd_representative_only` | `10` | `abstain_indistinguishable` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.25` | `None` | `None` | `selected_top_margin_below_action_threshold_or_tied` |
| `hrd_representative_only` | `20` | `abstain_indistinguishable` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.1375` | `None` | `None` | `selected_top_margin_below_action_threshold_or_tied` |

## Summary

- Recommendation coverage: `0.333333`。
- False-recommendation rate: `0.0`。
- Mean recommendation regret: `0.0`；worst regret: `0.0`。
- Missed-opportunity rate: `0.666667`。
- Top-pair direction agreement among recommendations: `1.0`。

## Random decision baselines

| Baseline | k | Recommendation coverage | False recommend | Mean regret | Worst regret | Missed opportunity | Top-pair agree |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `uniform_random_same_budget` | `10` | `0.282` | `0.407801` | `0.163121` | `0.4` | `0.718` | `0.592199` |
| `quality_filtered_random` | `10` | `0.282` | `0.407801` | `0.163121` | `0.4` | `0.718` | `0.592199` |
| `stratified_random` | `10` | `0.268` | `0.380597` | `0.152239` | `0.4` | `0.732` | `0.619403` |
| `uniform_random_same_budget` | `20` | `0.0` | `0.0` | `None` | `None` | `1.0` | `None` |
| `quality_filtered_random` | `20` | `0.0` | `0.0` | `None` | `None` | `1.0` | `None` |
| `stratified_random` | `20` | `0.0` | `0.0` | `None` | `None` | `1.0` | `None` |
