# Barcarolle 项目展示 Deck V4 读者反馈审计

状态：V4 reader-review audit，2026-06-03。

审计对象：

```text
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v4.zh.md
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v4.zh.pptx
```

## Result

结论：通过。V4 针对读者复核提出的图形、论证和术语问题做了局部修复，未扩大证据声明。

| Review item | V4 answer | Evidence slide(s) | Pass/fail | If fail, repair |
| --- | --- | --- | --- | --- |
| Slide 1 right diagram looks wrong | 右侧图改为 `目标仓库 -> 仓库级评测 release -> ACUT 运行与结果`，删除 V3 端点圆点和斜向残留感。 | Slide 1；visual QA full-size review | pass | n/a |
| Slide 2 gap/consequence visual relation unclear | `预测缺口` 改成桥接带，并通过 shared rail 连接部署选择、配置调优、治理决策。 | Slide 2；visual QA full-size review | pass | n/a |
| Slide 5 bottom shapes/process text unclear | 删除 V3 的底部小形状行和过程句；替换为一条 readable `认证 checklist`。 | Slide 5；PPTX text residue check | pass | n/a |
| Slide 7 layout problem | 第 7 页重画为四段主流程加五个规则卡，layout check 没有 error。 | Slide 7；layout QA | pass | n/a |
| Slide 7 weak bad-algorithm argument | 主论证改成有限预算估计器和任务选择器问题；旧 weighted 只保留为历史诊断。 | Slide 7；`argument-repair-v4.zh.md` | pass | n/a |
| Slide 8 weak bad-algorithm/process-evidence argument | 第 8 页按四个读者问题组织协议、source repair、selector traction 和 claim boundary；不再用旧 weighted failure 作为主证据。 | Slide 8；evidence audit | pass | n/a |
| Slide 9 left graphic alignment | 左侧算法演进 loop 对齐到 2x2 网格，节点统一宽高，connector 位置清楚。 | Slide 9；visual QA full-size review | pass | n/a |
| Slide 10 layout problem | 移除 detached bottom output strip，主流程节点直接承载治理输出，底部仅保留无框支撑句。 | Slide 10；visual QA full-size review | pass | n/a |
| Slide 11 graphic looks wrong | 重画为单一路径 `配置变更 -> dev feedback -> eval release -> canary release -> 回归信号`；未来验证材料独立隔离。 | Slide 11；visual QA full-size review | pass | n/a |
| Overall terminology burden | 建立 V4 术语替换表；表头中文化，主要节点改用中文，必要英文术语在 `text-style-audit-v4.zh.md` 中列明原因。 | Slides 1-11；`terminology-reduction-v4.zh.md` | pass | n/a |

## Residual Risk

V4 仍保留 ACUT、release、harness、MAE、future holdout、rolling-origin、dev/eval/canary 等必要技术术语。它们在上下文中有解释或属于产品/验证路线名称，属于 accepted residual terminology rather than a reader-review failure.
