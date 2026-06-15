# Boltons strict chronological rolling-origin diagnostics

生成时间：`2026-06-15T14:33:58+00:00`。

本诊断只用 expanded boltons final matrix，并按真实 `task_time` 形成 origin；没有把普通 Selection/Holdout label 混入 rolling-origin claim。

- Origins: `4`。
- Selection window size per origin: `10` tasks。
- Overall MAE mean: `0.213418`。
- Top-rank agreement rate: `0.5`。
- Mean recommendation regret: `0.033742`；max regret `0.094737`。
- Gap-direction agreement rate: `0.75`。
- Same-budget random mean MAE: `0.238985`。

## Origins

| Origin | Time | Future tasks | MAE | Top agree | Regret | Gap agree | Random MAE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| origin_10_2016-08-03 | 2016-08-03T02:11:02-07:00 | 40 | 0.101763 | True | 0.0 | True | 0.101763 |
| origin_20_2018-06-27 | 2018-06-27T16:51:35-05:00 | 30 | 0.370402 | False | 0.04023 | True | 0.265259 |
| origin_30_2019-02-12 | 2019-02-12T15:15:17-05:00 | 20 | 0.270395 | False | 0.094737 | False | 0.299472 |
| origin_40_2021-02-21 | 2021-02-21T22:35:25-08:00 | 10 | 0.111111 | True | 0.0 | True | 0.289446 |

这些结果是 historical pseudo-future diagnostics，只能作为 directional evidence；不能单独证明 predictive validity 或 selector optimality。
