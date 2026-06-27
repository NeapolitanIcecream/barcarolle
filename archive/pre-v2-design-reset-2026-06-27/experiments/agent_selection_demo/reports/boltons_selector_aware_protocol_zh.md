# Boltons selector-aware protocol

生成时间：`2026-06-16T03:16:03+00:00`。

## Audit

旧图表的问题是把固定历史窗口直接当成 Selection 证据；这只能说明历史窗口与未来窗口的 pass-rate drift，不能说明某个 selector 会在当时从历史池里挑出哪些任务。

本次协议冻结为：每个 origin 先只给 selector 历史 task metadata，selector 选出预算内 benchmark task IDs，之后才 join 已提交 outcome matrix 计算 Selection-vs-Future。

## Origins and budgets

| Origin | History | Future | Budgets |
| --- | --- | --- | --- |
| origin_20 | 20 | 30 | 10 |
| origin_30 | 30 | 20 | 10,15 |
| origin_40 | 40 | 10 | 10,15,20 |

## Selectors

| Selector | Family | Algorithm |
| --- | --- | --- |
| rsq_v2 | rsq_v2 | rsq_v2 |
| rsq_v2_no_recency | rsq_v2 | rsq_v2 |
| rsq_v2_no_caps | rsq_v2 | rsq_v2 |
| flc | flc | flc |
| representative_only | ablation | representative_only |
| informativeness_only | ablation | informativeness_only |
| hrd_v3_70_30 | hrd_v3 | hrd_v3_70_30 |
| hrd_v3_60_40 | hrd_v3 | hrd_v3_60_40 |
| hrd_v3_50_50 | hrd_v3 | hrd_v3_50_50 |
| hrd_v3_70_30_no_recency | hrd_v3 | hrd_v3_70_30 |
| hrd_v3_70_30_no_caps | hrd_v3 | hrd_v3_70_30 |
| hrd_v3_70_30_flc_rep | hrd_v3 | hrd_v3_70_30 |
| cod_lite | cod_lite | cod_lite |
| ro_lsp | ro_lsp | ro_lsp |
| saes_lite | saes_lite | saes_lite |

## Random baselines

- Baselines: `uniform_random_same_budget, quality_filtered_random, source_recency_stratified_random, module_stratified_random`。
- Seeds: `0..999`。

## Main scoring policy

`timeout`、`acut_harness_error`、`invalid_output` 和 `no meaningful change` 都进入 denominator 并计为失败；scoreable-only 只能作为 sensitivity note，不进入主图。

## Leakage boundary

selector 不得看到 future task IDs、future outcomes，也不得为了选择而读取未选 candidate 的 outcomes。`saes_lite` 只允许按 seed batch -> 观察 seed outcomes -> second batch 的顺序离线 replay。

Paid Agent cells used by this protocol freeze: `0`。
