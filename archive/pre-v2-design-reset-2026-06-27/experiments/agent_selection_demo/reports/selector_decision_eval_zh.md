# Selector Decision Eval

生成日期：2026-06-14

## Decision rule

决策层输出三种用户可读状态：`recommend`、`top_tier`、`insufficient_data`。报告先给 Agent 排名，再给选择建议和证据表；paired/LCB 指标只作为证据，不再因为单个 discordant task 或统计显著性不足直接拒绝推荐。

## Selector decisions

| Selector | k | State | Recommended | Selection margin | Later top | Later margin | MAE | Regret | Top-pair agree | Reason |
| --- | ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- |
| `rsq_recency_stratified_quota` | `10` | `top_tier` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.25` | `None` | `None` | `top_agents_within_tie_epsilon` |
| `rsq_recency_stratified_quota` | `20` | `top_tier` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.1375` | `None` | `None` | `top_agents_within_tie_epsilon` |
| `hrd_50_50` | `10` | `recommend` | `kilo_gpt_5_4` | `0.2` | `kilo_gpt_5_4` | `0.1` | `0.1` | `0.0` | `True` | `top_agent_pass_rate_advantage` |
| `hrd_50_50` | `20` | `top_tier` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.1375` | `None` | `None` | `top_agents_within_tie_epsilon` |
| `hrd_60_40` | `10` | `recommend` | `kilo_gpt_5_4` | `0.2` | `kilo_gpt_5_4` | `0.1` | `0.1` | `0.0` | `True` | `top_agent_pass_rate_advantage` |
| `hrd_60_40` | `20` | `top_tier` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.1375` | `None` | `None` | `top_agents_within_tie_epsilon` |
| `hrd_70_30` | `10` | `recommend` | `kilo_gpt_5_4` | `0.2` | `kilo_gpt_5_4` | `0.1` | `0.1` | `0.0` | `True` | `top_agent_pass_rate_advantage` |
| `hrd_70_30` | `20` | `top_tier` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.1375` | `None` | `None` | `top_agents_within_tie_epsilon` |
| `hrd_disagreement_only` | `10` | `recommend` | `kilo_gpt_5_4` | `0.2` | `kilo_gpt_5_4` | `0.1` | `0.1` | `0.0` | `True` | `top_agent_pass_rate_advantage` |
| `hrd_disagreement_only` | `20` | `top_tier` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.1375` | `None` | `None` | `top_agents_within_tie_epsilon` |
| `hrd_representative_only` | `10` | `top_tier` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.25` | `None` | `None` | `top_agents_within_tie_epsilon` |
| `hrd_representative_only` | `20` | `top_tier` | `None` | `0.0` | `kilo_gpt_5_4` | `0.1` | `0.1375` | `None` | `None` | `top_agents_within_tie_epsilon` |

## Summary

- Recommendation coverage: `0.333333`。
- Top-tier rate: `0.666667`；insufficient-data rate: `0.0`。
- False-recommendation rate: `0.0`。
- Mean recommendation regret: `0.0`；worst regret: `0.0`。
- Missed-opportunity rate: `0.666667`。
- Top-pair direction agreement among recommendations: `1.0`。

## Random decision baselines

| Baseline | k | Recommendation coverage | False recommend | Mean regret | Worst regret | Missed opportunity | Top-pair agree |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `uniform_random_same_budget` | `10` | `0.546` | `0.452381` | `0.180952` | `0.4` | `0.454` | `0.547619` |
| `quality_filtered_random` | `10` | `0.546` | `0.452381` | `0.180952` | `0.4` | `0.454` | `0.547619` |
| `stratified_random` | `10` | `0.518` | `0.455598` | `0.182239` | `0.4` | `0.482` | `0.544402` |
| `uniform_random_same_budget` | `20` | `0.0` | `0.0` | `None` | `None` | `1.0` | `None` |
| `quality_filtered_random` | `20` | `0.0` | `0.0` | `None` | `None` | `1.0` | `None` |
| `stratified_random` | `20` | `0.0` | `0.0` | `None` | `None` | `1.0` | `None` |
