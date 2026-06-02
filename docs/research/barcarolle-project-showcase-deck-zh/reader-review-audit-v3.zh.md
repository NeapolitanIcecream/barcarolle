# Barcarolle 项目展示 Deck V3 读者反馈审计

状态：V3 reader-review audit，2026-06-02。

审计对象：

```text
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v3.zh.pptx
```

## Result

结论：通过。逐页反馈中的 `10` 个内部复核问题均已在 V3 中处理。

| Review item | V3 answer | Evidence slide(s) | Pass/fail | If fail, repair |
| --- | --- | --- | --- | --- |
| 第一页是否解释了 ACUT，并且没有出现旧重复说法？ | Slide 1 副标题直接定义 `ACUT = Agent Configuration Under Test，一次被评估的 agent 配置。`，后续使用 `ACUT` 或 `agent 配置`。 | Slide 1；PPTX text residue check | pass | n/a |
| 问题页是否把通用 benchmark 分数和目标仓库未来工作之间的缺口讲具体？ | Slide 2 合并问题和代价，明确 general score、target-repo future work、prediction gap，以及 deployment/tuning/governance 后果。 | Slide 2 | pass | n/a |
| 相关工作页是否写全名称，并用直观语言说明每类工作留下的问题？ | Slide 3 写全 SWE-bench、SWE-bench Verified、SWE-bench-Live、SWE-Bench++、SWE-smith、R2E-Gym，并按 real tasks/quality、freshness/scale、environments/verifiers 三层说明 gap。 | Slide 3；`related-work-source-sanity-v3.zh.md` | pass | n/a |
| 研究目标页是否让非内部读者理解 predictive validity 和 MAE？ | Slide 4 用公式块定义 `W_r(a)`，用中文解释 MAE 是预测值与未来真实表现的平均距离，并保留未建立预测效度的边界。 | Slide 4 | pass | n/a |
| 方法页是否只保留必要术语，并去掉意义不明的底部矩形和过程文本？ | Slide 5 只保留 compiler workflow 与认证维度；没有底部残留矩形或生成过程说明。 | Slide 5 | pass | n/a |
| 执行边界和算法环境页是否改成中文、可读、低术语密度？ | Slide 6 把 solver/diff/verifier 边界改成中文说明；Slide 7 将 algorithm lab 吸收到 selection/support/fallback 问题中。 | Slides 6-7 | pass | n/a |
| 当前证据是否回答问题真实、方法可推进、路线可演进，而不是堆过程数据？ | Slide 8 按 reader question 组织 evidence：weighted failure、120/120、scoreability 1.0、click 30/30、MAE 和 random control。 | Slide 8 | pass | n/a |
| 研究路线是否把核心算法演进放回中心？ | Slide 9 以 selector evolution loop 为中心，把 freeze/release/baseline/success criteria 放在 validation gates 中。 | Slide 9 | pass | n/a |
| Agent License 和 Agent Tuning 页是否用正面表述说明用途？ | Slides 10-11 说明 governance evidence status 与 protected feedback loop，没有使用产品负面边界表述。 | Slides 10-11；PPTX text residue check | pass | n/a |
| 所有图是否没有孤立矩形、错误连接、不可解释标签或明显生成痕迹？ | full-size render review 检查了 Slides 1-11；explicit diagram sanity checks for Slides 1、5、6、10、11 passed。 | `visual-qa-report-v3.zh.md` | pass | n/a |

## Residual Risk

Formula slide 使用 editable text math block 而非 PowerPoint native equation。
渲染结果清晰，QA 中记录为 accepted implementation limitation。
