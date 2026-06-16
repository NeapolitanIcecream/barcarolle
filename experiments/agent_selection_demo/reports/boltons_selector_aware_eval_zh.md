# Boltons selector-aware eval

生成时间：`2026-06-16T03:16:06+00:00`。

主结果使用 fail-inclusive pass rate：timeout、harness error、invalid output、no meaningful change 都计为失败。

## Primary k=10 rolling-origin summary

| Selector | MAE | Regret | Top tier | Top pair | Recommend |
| --- | --- | --- | --- | --- | --- |
| cod_lite | 0.411111 | 0.022222 | 0.666667 | 1.0 | 0.666667 |
| flc | 0.394444 | 0.0 | 1.0 | 1.0 | 0.333333 |
| hrd_v3_50_50 | 0.202778 | 0.022222 | 0.666667 | 0.0 | 0.666667 |
| hrd_v3_60_40 | 0.202778 | 0.0 | 1.0 | 0.0 | 0.666667 |
| hrd_v3_70_30 | 0.194444 | 0.0 | 1.0 | 0.0 | 0.666667 |
| hrd_v3_70_30_flc_rep | 0.352778 | 0.022222 | 0.666667 | 0.333333 | 0.666667 |
| hrd_v3_70_30_no_caps | 0.211111 | 0.0 | 1.0 | 0.333333 | 0.333333 |
| hrd_v3_70_30_no_recency | 0.311111 | 0.0 | 1.0 | 0.333333 | 1.0 |
| informativeness_only | 0.311111 | 0.0 | 1.0 | 0.333333 | 1.0 |
| representative_only | 0.144444 | 0.016667 | 1.0 | 0.0 | 0.666667 |
| ro_lsp | 0.286111 | 0.038889 | 1.0 | 0.0 | 0.666667 |
| rsq_v2 | 0.144444 | 0.016667 | 1.0 | 0.0 | 0.666667 |
| rsq_v2_no_caps | 0.144444 | 0.016667 | 1.0 | 0.0 | 0.666667 |
| rsq_v2_no_recency | 0.327778 | 0.022222 | 0.666667 | 0.0 | 1.0 |
| saes_lite | 0.444444 | 0.022222 | 1.0 | 0.666667 | 0.333333 |

## Latest origin k=10

| Selector | Decision | Forced | Future top | Regret | MAE | Random |
| --- | --- | --- | --- | --- | --- | --- |
| rsq_v2 | recommend | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.15 | source_recency_stratified_random |
| rsq_v2_no_recency | recommend | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.3 | source_recency_stratified_random |
| rsq_v2_no_caps | recommend | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.15 | source_recency_stratified_random |
| flc | top_tier | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.5 | source_recency_stratified_random |
| representative_only | recommend | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.15 | source_recency_stratified_random |
| informativeness_only | recommend | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.325 | source_recency_stratified_random |
| hrd_v3_70_30 | recommend | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.225 | source_recency_stratified_random |
| hrd_v3_60_40 | recommend | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.2 | source_recency_stratified_random |
| hrd_v3_50_50 | recommend | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.2 | source_recency_stratified_random |
| hrd_v3_70_30_no_recency | recommend | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.325 | source_recency_stratified_random |
| hrd_v3_70_30_no_caps | top_tier | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.225 | source_recency_stratified_random |
| hrd_v3_70_30_flc_rep | top_tier | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.425 | source_recency_stratified_random |
| cod_lite | top_tier | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.55 | source_recency_stratified_random |
| ro_lsp | recommend | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.275 | source_recency_stratified_random |
| saes_lite | top_tier | kilo_claude_sonnet_4_6 | kilo_claude_sonnet_4_6 | 0.0 | 0.5 | source_recency_stratified_random |

本表是 selector-aware：Selection rates 来自 selector 选出的 task IDs，而不是 origin 之前的全部历史任务。
