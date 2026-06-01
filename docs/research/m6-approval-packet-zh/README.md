# Barcarolle M6 中文立项交付包

状态：中文补充包，2026-06-01。

## 编辑面

本目录是 M6 立项交付包的中文版本。中文补充包完成并通过审计后，后续面向评审者的修改应优先在本目录进行。

英文 M6 交付包保留为来源和审计基准：

```text
docs/research/m6-approval-packet/
```

V5 仍是长文论证基准和主参考文本：

```text
docs/research/barcarolle-proposal-report-v5.md
```

如果中文材料与英文 M6 包或 V5 的声明边界不一致，先按英文 M6 包和 V5 校正中文材料，不要扩大当前证据可以支持的结论。

## 文件

| 文件 | 用途 |
| --- | --- |
| `executive-summary-v1.zh.md` | 中文一页摘要，用于快速阅读和审批沟通。 |
| `approval-deck-outline-v1.zh.md` | 中文 PPTX 的逐页 claim spine 和证据边界。 |
| `appendix-evidence-index-v1.zh.md` | 中文证据附录，映射关键声明、数字和来源。 |
| `approval-packet-checklist-v1.zh.md` | 中文交付包检查清单和审计结果。 |
| `terminology-glossary-v1.zh.md` | 中文术语表，用于稳定后续改稿。 |
| `barcarolle-approval-deck-v1.zh.pptx` | 中文可编辑 PPTX，作为主要评审呈现材料。 |

## 声明边界

当前证据支持“有边界的牵引性证据”和“可信的验证路径”，但预测效度仍未建立。Barcarolle 的调优与回归反馈也仍是计划交付能力，尚无实证结果支持效果声明。

中文材料必须保留这些边界：

- 不声称已经建立正式预测效度；
- 不声称调优或回归反馈的效果已经完成实证验证；
- 不把 adapter 差异解释成单纯模型能力差异；
- 不授权无闸门、开放式的付费 ACUT 评测；
- 不替换或删除仍由用户决定的资源、预算、审批和负责人占位符。

## 占位符

这些用户自有值应在中文材料中保持可见，除非用户明确提供值并在 process report 中记录来源：

- `[待用户决定：项目人员配置]`
- `[待用户决定：项目周期]`
- `[待用户决定：有闸门 ACUT 评测的预算上限]`
- `[待用户决定：审批路径或审批负责人]`
- `[待用户决定：对外材料中的交付负责人类别]`

## 后续编辑顺序

1. 先改中文 PPTX 和中文一页摘要。
2. 再同步中文 outline、证据附录和检查清单。
3. 如果涉及声明、数字、证据边界或术语选择，回查英文 M6 包和 V5。
4. 不在中文材料中新增证据、改动 score 表、改动任务 ID、改动 split label、改动 source eligibility、改动任务陈述或 hidden-oracle 材料。
