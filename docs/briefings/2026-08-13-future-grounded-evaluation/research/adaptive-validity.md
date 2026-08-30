# 从 pointwise validity 到 adaptive selection validity

> 本文把主叙事中的“反复优化会不会让评测失效”拆成可区分、可测量的机制。它不是对 Barcarolle 已有能力的描述，而是下一阶段的研究定义与实验协议。
>
> 2026-08-30 更新：当前共同核心指标是 level MAE 与两个 Agent 的 pass-rate
> gap MAE，第三项目标是二者在优化压力下的保持。top-1 regret、sign、ranking
> 和 policy regret 为决策诊断，不能替代这两个 cardinal errors。当前权威见
> [`../../../research-program.md`](../../../research-program.md)。

## 1. 先区分五种失败，不把它们都叫 Goodhart

| 失败 | 发生了什么 | 即使没有自适应优化也会发生吗 | 决定性检查 |
| --- | --- | --- | --- |
| 时间分布漂移 | 历史 Task mix 与 next-H 真实工作不同 | 会 | rolling-origin；按 repository、time、task family 分层 |
| oracle 错配 | 测试拒绝正确替代解，或放过错误实现 | 会 | 多解审计、hidden checks、人工复审、invalid-rate |
| 污染/直接暴露 | 题目、gold patch 或判分特征进入训练和开发过程 | 会 | cutoff/provenance、exposure ledger、held-out assurance set |
| Agent population shift | Selector 在 reference models 上学到的结构不适合新 Harness、工具或策略 | 会 | same-Harness 与 cross-Harness 分开；support diagnostics |
| 自适应选择偏差 | Optimizer 根据连续反馈主动找到 evaluator 的误差方向 | 不会；这是闭环新增项 | 固定 proposer/预算，只改变 evaluator，并密封 future block |

Barcarolle 目前已经直接观察到第四项：same-Harness development candidate 在完整 Agent system/Harness 上迁移失败。但这不是第五项的证据。只有让同一个 Optimizer 多轮查询 evaluator，并与密封 future workload 对账，才能声称测到了 adaptive degradation。

同样，重复优化并不必然造成严重过拟合。竞赛数据研究发现 public/private gap 有时很小，可能因为候选彼此高度相似，或 private set 的分布变化比自适应查询本身更重要。因此实验必须同时报告候选多样性、temporal shift 和 adaptive exposure，不能看到 public/future gap 就自动归因于 Goodhart。

## 2. 三层有效性

设 origin 为 `o`，Agent 为 `a`，在 origin 前编译的 evaluator 分数为 `S_o(a)`，origin 后密封的 next-H 真实工作结果为 `Y_o,H(a)`。

### 2.1 Pointwise predictive validity

问题：单个自然出现的 Agent，今天分数与后来表现是否接近？

```text
level_error(a) = |S_o(a) - Y_o,H(a)|
```

这对应 Barcarolle 现有 rolling-origin MAE 研究。它是必要地基，但不足以证明 evaluator 能选对下一版本。

### 2.2 Selection validity

问题：面对一批固定、且没有因本 evaluator 反馈而产生的候选，能否保留差值、方向和 winner？对候选 `a_i, a_j`：

```text
lift_error(i,j) = |[S(a_i)-S(a_j)] - [Y(a_i)-Y(a_j)]|
sign_accuracy   = 1{sign ΔS = sign ΔY}
selection_regret = max_a Y(a) - Y(argmax_a S(a))
```

平均 level MAE 低，仍可能把两个接近的候选排反；因此 selection regret 和 pairwise lift 是本项目比单点 MAE 更直接的指标。

### 2.3 Adaptive selection validity

问题：候选 `a_t` 是 Optimizer 根据先前的 evaluator 反馈产生的；随着查询次数、反馈粒度和 trace 暴露增加，selection validity 如何变化？

需要记录完整 trajectory：

- `agent_parent_id`、intervention、round、proposer identity；
- 该轮可见 task IDs、aggregate score、per-task result、failure trace；
- evaluator version、refresh epoch、query/cost budget；
- 在搜索完成前始终不可见的 future block identity。

`optimization horizon` 不是一个脱离协议的常数。它应定义为：在预先声明的候选生成器、反馈通道、任务预算和误差阈值下，regret/lift error 首次持续越界前可承受的查询数或轮数。阈值和“持续”规则必须在 future outcomes 打开前冻结。

### 2.4 统一决策口径：tie、replicate 与 abstention

- **Tie**：在 future outcome 上预注册 practical-indifference band `δ`；差值落在 `[-δ, δ]` 时记为 tie，不强行判方向。evaluator 的 top score 并列时，按预注册规则保留 incumbent；没有 incumbent 时再按稳定的 `agent_id` 排序。所有方法使用同一规则，不能在 future outcomes 打开后挑 winner。
- **Replicate**：每个 candidate × task 使用相同数量的独立完整 Agent runs。主估计按预注册方式跨 runs 汇总，同时报告 seed-level 分布和置信区间；不能把同一 origin/repository 下相关的 task cells 当作独立 replicate。
- **Abstention**：主协议的 fallback 预先设为保留 incumbent；candidate panel 因此应包含 incumbent。若某项实验没有 incumbent，必须在 outcomes 打开前指定一个固定 fallback candidate。support rule 拒绝排序时执行 fallback，而不是从分析中删掉该 decision cell。另设 Full-history-based fallback 只能作为提前冻结的敏感性分析。

冻结 operating point 后，同时报告 coverage、covered cases 的 conditional risk、完整 coverage–risk 曲线，以及包含 abstention 的 unconditional policy regret：

```text
policy_regret = mean_decisions[max_a Y(a) - Y(policy(a))]
policy(decision) = supported winner, if support; frozen fallback, if abstain
```

近零 coverage 下的低 conditional risk 不算成功；unconditional policy regret 才回答部署这套 support + fallback policy 是否少选错 future winner。

## 3. Goodhart 分类能解释风险，但不能代替实验

[Manheim 与 Garrabrant](https://arxiv.org/abs/1803.04585) 将 Goodhart 效应分为 regressional、extremal、causal 和 adversarial 四类。在这里可以作机制映射：

| 类型 | coding-agent 例子 | Barcarolle 可观测量 |
| --- | --- | --- |
| regressional | 从许多相近候选中选到“真实能力 + 测量噪声”最高者 | winner optimism、selection regret 随候选数变化 |
| extremal | 新 Harness/工具产生 reference panel 未覆盖的行为 | support distance、cross-Harness transfer、abstention coverage |
| causal | 优化一个代理特征破坏了它与真实工作的因果关系 | benchmark gain 与 future lift 脱钩；intervention 分层 |
| adversarial | Agent 从 tests/traces 反推出判分盲区 | exposure ledger、反馈消融、assurance set gap |

这个分类用于提出诊断，不授权“counter-Goodhart”结论。项目必须说明观测到哪一种行为、在哪个 exposure protocol 下、相对什么 baseline 改善。

## 4. Generator 的三层外部有效性

未来导向任务供应应拆成三个独立对象：

1. `Forecaster`：在 origin 时预测未来需求 family；
2. `Materializer`：把 family 具体化为 requirement、environment、Task 和 hidden Check；
3. `Response validator`：检查这些 executable tasks 在 Agent panel 上形成的差值/排序，是否迁移到 later real Tasks。

对应三种失败：方向没来、方向来了但题出偏了、题看似合理但 Agent response surface 与真实任务不同。SWE-Future 对第一层给出重要方法和回溯证据，但不能让第二、三层自动成立。

需要的实验单位不是“单个生成题看起来多真实”，而是 response vector：

```text
r(task) = [pass(a1), pass(a2), ..., pass(am)]
```

同一 family 做多次独立 materialization。如果合理的具体化经常翻转 `a_i-a_j` 的符号，说明 family-level forecast 不能稳定支撑版本选择。再做 cross-materializer，避免同一个 pipeline 同时定义问题、答案和成功标准。

Response calibration 属于 development：只能在更早 rolling origins 的 development blocks 上拟合 synthetic-to-real response mapping、阈值和 materializer 选择。所有配置必须在后续 sealed later-real block 打开前冻结；该 block 只做外部评估，不能再用于调参、选择 Materializer 或改变 admission rule。数据不足时按 origin 做 temporal cross-fitting，不能随机拆分，也不能让同一个 later-real block 同时承担 calibration 和 final evaluation。

用于评价的 Reality Generator 应保持 Agent-blind。可以另设查看失败 traces 的 Challenge Generator 来找训练难例，但两者必须分账：challenge usefulness 不等于 future representativeness。

## 5. 最小决定性实验：先固定候选，再开放自适应闭环

### Stage A：population-shift screen

先用现有公开 outcomes，不产生新付费 Agent runs：

- 将 target 按同 Harness/跨 Harness、model family、ability 和已有 target history 分层；
- 分开 cold start 与 warm start；
- 冻结 support/abstention rule、tie rule 与 fallback；
- 在没有参与规则选择的新 same-Harness target boundary 上验证。

首要目的不是立即赢过 Full，而是知道何时有资格给出排序。报告完整 coverage–risk 曲线、冻结阈值下的 covered-case risk，以及 fallback 后的 unconditional policy regret。

### Stage B：fixed candidate panel

在预先存在的候选 Agent panel 上比较：

- Full history；
- recent-N；
- random subset；
- human-curated regression suite；
- current Barcarolle；
- contrast-aware + support/abstention Barcarolle。

预注册共同主指标 `level MAE` 与 `pairwise pass-rate-gap MAE`；`top-1
selection regret`、sign/rank、以及包含 abstention/fallback 的
`unconditional policy regret` 作为决策诊断。candidate panel 不能由待测
evaluator 产生，因此这一阶段只测 fixed-candidate validity。tie、replicate
和 fallback 均按 2.4 节冻结。

### Stage C：adaptive pressure curve

固定相同 initial Agent、proposer、候选/成本预算、repository origins 和密封 future blocks。只改变 evaluator。每组至少有独立 seed/replicate，并限制 scorer 反馈通道。

沿 query count/round 报告：

- benchmark gain、future gain 与二者差值；
- best-so-far future performance；
- pairwise sign accuracy；
- top-1 regret 与 unconditional policy regret；
- 虚涨率：benchmark 改善但 future 回退的 accepted transitions 占比；
- coverage–risk 与 abstention/fallback 结果；
- cost 与 latency。

应包含两个关键消融：只给 aggregate score vs 给 per-task traces；evaluator frozen vs epoch refresh。这样才能把任务质量、反馈泄漏和 refresh 的作用分开。

### Stage D：prospective confirmation

冻结 Generator、response-calibration parameters、Selector、support/tie/fallback rule、metrics 和 analysis code，在新的 repository/time window 等待真实 Task 到来。只有此阶段才能支持 strict-prospective wording。任何在 future outcomes 打开后修改的规则都回到 development 状态。

## 6. 预期效果必须写成待检验假说

| 强度 | 预注册假说 | 失败时能学到什么 |
| --- | --- | --- |
| H1 固定候选 | 相对 Full/recent，少选错 future winner | 若失败，问题在 response/contrast preservation，不必先谈 adaptive safety |
| H2 population support | abstention 后 covered cases 的 regret 更低，且 fallback 后 unconditional policy regret 不劣于预注册 baseline | 若 coverage 近零或 unconditional regret 未改善，说明 support rule 没有改善实际决策 |
| H3 adaptive curve | query 增加时，Barcarolle regret 增长慢于 static eval | 若曲线相同，refresh/exposure protocol 没产生边际价值 |
| H4 closed loop | 同 proposer/预算下，最终 future gain 更大 | 若 benchmark 更好但 future 不变，评测没有改善版本决策 |
| H5 prospective | 冻结 pipeline 在新时间窗复现 H1–H4 的关键方向 | 若不复现，前序结果只能保留为 retrospective development evidence |

不应预先承诺数值。样本量和最小实际相关效应应根据 future task 数、Agent replicate variance 和 decision cost 做 power/simulation 设计，而不是从当前 0.006/0.014 的 MAE 差异外推。

## 7. 与相邻理论/系统的准确关系

- [Adaptive data analysis](https://arxiv.org/abs/1411.2664) 与 [Ladder](https://arxiv.org/abs/1502.04585)说明反复查询 holdout 和高粒度反馈为何会产生选择偏差，也提供限制信息泄漏的设计语言；它们不定义 repository 的未来真实 workload。
- [Darwin Gödel Machine](https://arxiv.org/abs/2505.22954)展示自动 Agent variant search 已经可行；它的 benchmark fitness 仍由外部给定，因此不能证明 benchmark gain 的 field transfer。
- [Red Queen Gödel Machine](https://arxiv.org/abs/2606.26294)对 evaluator-dependent slots 使用 fixed-within-epoch evaluator，并在 epoch 边界以 held-out ground-truth anchor 决定 evaluator promotion；writer/prover 等 task agents 仍由 epoch-local evaluator 排序。论文把当前实证称为 preliminary，也没有替 coding-agent 场景构造 delayed、changing、repo-specific 的 future anchor。
- [Skalse 等](https://arxiv.org/abs/2209.13085)形式化 reward hacking 和 unhackability；它提供 proxy 失真的机制语言，不提供 coding-agent 的 future-grounded 验证协议。
- [Gao 等](https://arxiv.org/abs/2210.10760)在 synthetic gold reward model 设定中测量 proxy optimization pressure 与 gold score 的关系；它支持压力曲线设计，但 fixed gold model 不等于 later-real workload。
- [Sequential algorithmic modification with test data reuse](https://proceedings.mlr.press/v180/feng22a.html)研究同一 holdout 上连续修改算法的统计代价；Barcarolle 增加了时间切点、可执行任务、完整 Agent identity 和 later-work replay。
- [Cawley 与 Talbot](https://www.jmlr.org/papers/v11/cawley10a.html)提醒模型选择本身会对性能估计过拟合；这里相应地把开发 Selector 与外部确认边界分开。
- [Roelofs 等](https://arxiv.org/abs/1902.10811)说明 benchmark overfitting 的实证大小不能从理论风险直接推出；因此本项目报告分布漂移、候选相似性与自适应压力的分解，而不假定退化必然发生。

## 8. 当前允许的结论

现有证据支持：“Barcarolle 有能力运行可审计的 rolling-origin benchmark selection；一个同 Harness development candidate 在窄口径上改善，但对 weighting 和 Agent population shift 敏感。”

尚不支持：“Barcarolle 能抵抗 Goodhart”“能安全驱动无限轮自我改进”“动态任务不会污染”“生成任务代表未来”“已有 optimization horizon 数值”。这些全部是由上述实验逐层判定的开放命题。
