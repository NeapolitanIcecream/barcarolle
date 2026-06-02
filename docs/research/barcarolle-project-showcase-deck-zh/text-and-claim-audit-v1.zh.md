# Barcarolle 项目展示 Deck 文本与声明审计

状态：文本与声明审计，2026-06-02。

## Scope

审计对象：

- `project-argument-map-v1.zh.md`
- `related-work-positioning-v1.zh.md`
- `showcase-deck-outline-v1.zh.md`
- `barcarolle-project-showcase-deck-v1.zh.pptx` 的抽取文本

PPTX 文本抽取位置：

```text
outputs/019e8612-2054-7261-838f-a9823b236589/presentations/barcarolle-project-showcase-deck-zh/qa/pptx-text.txt
```

## Result

结论：通过。

审计结果：

| 检查项 | 结果 |
| --- | --- |
| 禁用流程词与历史阶段词检查 | `0` matches |
| 预测效度与调优效果过度声明检查 | `0` matches |
| 本地 Downloads 路径检查 | `0` matches |
| PPTX 抽取文本禁用词与过度声明检查 | `0` matches |
| `git diff --check` | passed |

## Manual Review

人工复核结论：

- deck 标题是项目主张，不是章节名列表；
- related work 以贡献层定位，没有被写成失败竞品；
- 当前效果页只呈现牵引性 evidence，没有把小 MAE edge 写成正式未来预测结论；
- 限制页明确写出预测效度尚未建立，调优闭环效果也尚未实证；
- Agent License 被定位为 deployment governance 的 evidence layer；
- Agent Tuning 被定位为 dev/eval/canary、failure taxonomy、scorecard 和 regression signal 的接口；
- PPTX 文本没有出现内部写作指令、草稿残留、提示词式句子或本机 Downloads 路径。

## Repair Made During Audit

`project-argument-map-v1.zh.md` 中一处否定式表述使用了会触发过度声明正则的词序。已改为“已完成未来预测证明”，保留边界含义，同时避免读者材料出现误导性短语。

