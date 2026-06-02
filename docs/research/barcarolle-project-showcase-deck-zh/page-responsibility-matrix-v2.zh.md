# Barcarolle 项目展示 Deck 页面职责矩阵 V2

状态：V2 页面职责审计，2026-06-02。

用途：在编辑 V2 PPTX 前审计 V1 全部页面的独立读者职责，决定保留、合并或删除。本文是内部执行依据，不作为投影片正文。

## Pruning Decision

目标页数：`14` 页。

核心裁剪：

- 删除 V1 Slide 5 `项目位置`。
- 将 Slide 5 中仍有价值的 positioning 内容并入 Slide 4 `相关工作` 和 Slide 7 `方法`。
- Slide 7 作为唯一完整 compiler workflow 页面。
- Slide 6 聚焦预测目标和 MAE，不再承担流程图职责。
- Slide 13 聚焦未来验证协议，不再重复 compiler workflow 或算法环境。
- Slides 14 和 15 都保留，原因是二者服务不同产品化接口：deployment governance 和 tuning feedback。两页必须使用不同视觉结构，不能共享同一套 feedback/process 图式。

## Matrix

| V1 slide | Title label | Unique reader question | What disappears if removed | Repetition found | Decision | Merge destination | Preserve | Remove or rewrite |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 项目定位 | Barcarolle 到底是什么对象？它连接哪些实体？ | 读者会缺少项目一句话定义、目标仓库、ACUT、冻结 release 三者关系。 | 与 Slide 5 都在定位 Barcarolle；与 Slide 7 都提 release 输出。 | keep | n/a | 一句话定义；目标仓库 / ACUT / 冻结 release 三元关系；ACUT 不归 Barcarolle 控制的边界。 | 删除二分式句法；避免把 release formula 写成和 Slide 7 同样的完整流程。 |
| 2 | 问题 | 现有分数和目标仓库未来工作之间的决策缺口是什么？ | 读者会看不到为什么 target-repo future work 需要单独估计。 | 与 Slide 6 都讲未来表现；与 Slide 3 都讲部署决策。 | keep | n/a | 通用分数到目标仓库未来工作的 gap；目标问题句。 | 删除“通用 benchmark 无用”式对照；改成通用分数提供广义信号、仓库未来估计需单独建模。 |
| 3 | 代价 | 预测缺口为什么会影响实际部署、调优和治理？ | 读者会缺少项目 stakes，只看到抽象研究问题。 | 与 Slide 14/15 都提治理和调优；这里应只讲问题造成的后果。 | keep | n/a | 部署选择、配置调优、治理判断三类 consequence。 | 避免提前展开 productization solution；治理和调优方案留到 Slides 14/15。 |
| 4 | 相关工作 | 相邻系统已经解决了哪些层，Barcarolle 还要回答哪一层？ | 读者可能误以为项目重复 public benchmark、Verified、Live、SWE-smith 或 R2E-Gym。 | 与 Slide 5 都讲 Barcarolle 的层级位置。 | keep | absorbs part of Slide 5 | 相关工作矩阵；相邻贡献层；Barcarolle 的 release compilation 问题。 | 将 Slide 5 的“任务供应越强，越需要 compiler”压缩到本页底部收束句；不再另设定位页。 |
| 5 | 项目位置 | 原本问题：Barcarolle 位于哪一层？ | 删除后不会丢失独立论证步骤，因为 Slide 1 已定义对象，Slide 4 已定位相关工作之后的层，Slide 7 会给出完整 compiler workflow。 | 与 Slide 1 重复项目定位；与 Slide 4 重复相邻层定位；与 Slides 6/7/13 重复 release/freeze/validation 流程。 | delete / merge | Slide 4 and Slide 7 | “candidate supply -> certification -> assembly/release”这一层级逻辑；Barcarolle 不等于 task generator、ACUT harness、leaderboard 的边界含义。 | 删除本页；不保留完整 process strip；不保留二分式定位文案。 |
| 6 | 研究目标 | 长期要预测什么，MAE 如何解释？ | 读者会缺少 north-star estimand 和评价方向。 | 与 Slide 13 都讲 freeze/future/baseline；与 Slide 11 都提 MAE。 | keep | n/a | `W_r(a)` estimand；MAE 是平均预测误差；当前只定义目标，不宣称完成。 | 去掉 validation gate strip；把流程职责交给 Slide 13；避免与 Slide 7 的 release workflow 相似。 |
| 7 | 方法 | Barcarolle 怎样把候选任务编译成 release？ | 读者会缺少唯一完整方法流程，无法理解 compiler 具体产物。 | 与 Slide 5 和 Slide 13 都有多阶段流程；与 Slide 1 都提 release 输出。 | keep | absorbs part of Slide 5 | 唯一完整 workflow：candidate supply、certification、target-work profile、assembly rule、release、score/refresh；认证维度。 | 删除“不是抽题”句法；避免在 Slide 6/13 再画同款完整流程。 |
| 8 | 执行边界 | Barcarolle 和 ACUT harness 的边界在哪里？ | 读者会误读 Barcarolle 为 agent harness 或 model runner。 | 与 Slide 1 都提 ACUT；与 Slide 13 都提 named ACUT。 | keep | n/a | solver workspace / captured diff / verifier workspace；hidden oracle 只在 verifier 侧出现；adapter 差异按 named configuration 报告。 | 删除二分式 model-only 表述；正文改成直接边界声明。 |
| 9 | 算法问题 | 为什么 selection/support/fallback 本身是研究问题？ | 读者会缺少旧 weighted design 失败带来的负面诊断。 | 与 Slide 10 都讲 selector；与 Slide 12 都讲 fallback/support。 | keep | n/a | attrs/boltons weighted gaps 与 simple baselines；负面诊断。 | 标题可保留；正文删去“随机抽题”和“不是成功结果”二分句；改为 construction choices materially affect estimates。 |
| 10 | 算法环境 | 现在有什么算法比较环境可继续演进 selector？ | 读者会缺少“项目已具备 algorithm lab”的可执行性证据。 | 与 Slide 13 都提 baselines；与 Slide 12 都提 fallback/accounting。 | keep | n/a | candidate features、selection policy、baseline suite、random envelope、adapter/repo/window diagnostics。 | 只讲现有算法评估环境；不要提前画未来验证路线；减少 baseline/future wording 与 Slide 13 的重复。 |
| 11 | 当前效果 | 当前证据支持继续优化到什么程度？ | 读者会缺少 traction evidence 的量化摘要。 | 与 Slide 12 都提 MAE edge、fallback/support；与 Slide 9 都提 weighted failure。 | keep | n/a | `120/120`、scoreability `1.0`、click `30/30`、MAE `0.209` vs `0.2149`、edge `0.0059`、random beats/ties `93.4%`。 | 删除“traction evidence / predictive-validity result”二分句；本页只呈现 traction，不承担 repair plan。 |
| 12 | 限制 | 当前哪些弱点必须转成下一步 repair/validation gates？ | 读者会缺少 claim boundary、fallback、adapter 和 support 风险。 | 与 Slide 11 都提 MAE/fallback；与 Slide 13 都讲下一阶段动作。 | keep | n/a | fallback `6/18` and boltons `6/6`；Codex/Kilo named configuration reporting；small edge needs margin/stability。 | 本页用 weakness -> required action bridge；不要重复 Slide 11 的 traction proof cards；不要展开完整 future validation roadmap。 |
| 13 | 研究路线 | 下一阶段如何获得 outcome-unseen validation evidence？ | 读者会缺少从当前 traction 走向更强声明的验证路径。 | 与 Slides 5/6/7 都重复 release/freeze/validation；与 Slide 10 都提 baselines。 | keep | n/a | pre-outcome freeze、named ACUT configurations、outcome-unseen score join、baseline envelope、scoped result；future holdout / rolling-origin boundary。 | 不重复 candidate supply/certification/assembly workflow；不重复 algorithm lab map；视觉上必须像 validation protocol，不像 compiler process strip。 |
| 14 | 产品化方向 | Agent License / deployment governance 怎样使用仓库级证据层？ | 读者会缺少 governance 产品路径。 | 与 Slide 3 都讲治理；与 Slide 15 都是产品化方向。 | keep | n/a | 仓库/任务类别、风险等级、ACUT 配置、evidence status、scoped use decision。 | 直接说明 Barcarolle 支持 evidence layer；不使用“本身不是 license 产品”的二分句；视觉上采用 governance decision matrix。 |
| 15 | 产品化方向 | Agent Tuning 怎样使用受保护的反馈材料？ | 读者会缺少调优产品路径和 eval/canary 隔离边界。 | 与 Slide 3 都讲调优风险；与 Slide 14 都是产品化方向；与 Slide 13 都提 protected future/eval material。 | keep | n/a | dev/eval/canary release、failure taxonomy、scorecard、regression signal；prompt/retrieval/skills/tool policy/runtime budget configuration comparison。 | 保留为独立 tuning slide；视觉上采用 protected feedback loop，不采用 Slide 14 的治理矩阵；不声称 tuning-loop improvement 已经验证。 |

## Required Overlap Decisions

| Suspect overlap | Decision |
| --- | --- |
| Slide 1 `项目定位` vs Slide 5 `项目位置` | Slide 1 retained for object definition; Slide 5 deleted. Slide 5's layer-positioning sentence is compressed into Slide 4 and Slide 7. |
| Slides 5, 6, 7, and 13 around release/freeze/validation workflow | Slide 7 becomes the only complete compiler workflow. Slide 6 defines estimand/MAE. Slide 13 defines future validation protocol. Slide 5 deleted. |
| Slide 10 `算法环境` vs Slide 13 `研究路线` | Slide 10 remains current algorithm-evaluation environment. Slide 13 remains future validation protocol. Baseline vocabulary is separated by role: comparison environment vs validation gate. |
| Slide 11 `当前效果` vs Slide 12 `限制` | Slide 11 remains traction evidence only. Slide 12 maps support/fallback/adapter weaknesses to required repair or validation actions. |
| Slides 14 and 15 around productization direction | Both retained because governance evidence and tuning feedback answer different product questions. The two pages must use distinct visual grammars and avoid a repeated process-strip layout. |

## Title Preservation

All retained V1 slides keep their top-level title labels:

```text
项目定位
问题
代价
相关工作
研究目标
方法
执行边界
算法问题
算法环境
当前效果
限制
研究路线
产品化方向
产品化方向
```

Only V1 Slide 5 `项目位置` is deleted. Renumbering is allowed after deletion.
