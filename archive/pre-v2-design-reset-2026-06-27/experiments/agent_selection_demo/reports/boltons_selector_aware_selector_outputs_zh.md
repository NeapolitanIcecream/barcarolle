# Boltons selector-aware selector outputs

生成时间：`2026-06-16T03:16:06+00:00`。

## Selector runs

| Selector | Runs | Eligible |
| --- | --- | --- |
| cod_lite | 6 | 6 |
| flc | 6 | 6 |
| hrd_v3_50_50 | 6 | 6 |
| hrd_v3_60_40 | 6 | 6 |
| hrd_v3_70_30 | 6 | 6 |
| hrd_v3_70_30_flc_rep | 6 | 6 |
| hrd_v3_70_30_no_caps | 6 | 6 |
| hrd_v3_70_30_no_recency | 6 | 6 |
| informativeness_only | 6 | 6 |
| representative_only | 6 | 6 |
| ro_lsp | 6 | 6 |
| rsq_v2 | 6 | 6 |
| rsq_v2_no_caps | 6 | 6 |
| rsq_v2_no_recency | 6 | 6 |
| saes_lite | 6 | 6 |

## Random baselines

| Baseline | Cases | Seeds/case |
| --- | --- | --- |
| uniform_random_same_budget | 6 | 1000 |
| quality_filtered_random | 6 | 1000 |
| source_recency_stratified_random | 6 | 1000 |
| module_stratified_random | 6 | 1000 |

- Diagnostic-only exclusions: `0`。
- 所有 deterministic selectors 只收到 origin 之前的 history metadata。
- `saes_lite` 只在 seed batch 已选任务上读取 history outcomes；没有读取 future task IDs 或 future outcomes。
