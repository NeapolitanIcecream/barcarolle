# 图表资产

> 本页以下内容是第一版技术证据图。新版战略汇报优先使用 [`story/README.md`](story/README.md) 中的七张内容型示意图。

本目录包含三组 16:9 图表。每组同时输出 2400×1350 PNG 和可编辑 SVG；
白底、统一字体和色盲友好配色适合直接裁切到 PPT。

## 资产与证据状态

| Stem | 状态 | 内容与数据来源 |
| --- | --- | --- |
| `observed-selector-boundaries` | `OBSERVED` | 对比 repository-equal、Origin-weighted、modern Full internal LOO 和 13 references→external targets 的 H5/H10 `Candidate − Full MAE`。脚本动态读取 `examples/modern_agent_panel/evidence/consensus-rate-summary.json` 和 `consensus-rate-transfer-diagnostic.json`。 |
| `observed-repository-heterogeneity` | `OBSERVED` | repository × horizon 热图；脚本动态读取 summary JSON 的 `horizons.{5,10}.repository_rows[].candidate_minus_full.consensus_rate_match`，并验证两 horizon 的 repository 集合一致。 |
| `hypothetical-optimization-pressure` | `HYPOTHETICAL — NOT MEASURED` | 固定 benchmark 重复使用与 future-grounded adaptive protocol 的机制示意。CSV 中数字只控制曲线版面位置，没有单位，不是效果量、预测值或实际 optimization round。 |

Observed 图中的负值表示 Selector 的 MAE 低于 Full history，即较好；正值表示
较差。Transfer 结果是 opened post-freeze diagnostics，不是独立确认。

## 复现

从仓库根目录运行：

```bash
uv run --with matplotlib python \
  docs/briefings/2026-08-13-future-grounded-evaluation/scripts/make_figures.py
```

脚本在 observed JSON 字段缺失、数值非有限、repository 集合不一致或
hypothetical CSV 未显式标记 `hypothetical` 时失败，不会用默认值掩盖证据
漂移。

## Hypothetical 数据口径

[`data/hypothetical-optimization-pressure.csv`](data/hypothetical-optimization-pressure.csv)
只保存绘图布局坐标。第三图隐藏数值刻度，并在画面中央及图注明确标记
`HYPOTHETICAL — NOT MEASURED`。它表达待检验机制，不应与前两张 observed
图合并计算、添加误差条或解释为预期收益。
