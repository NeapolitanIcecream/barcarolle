# 研究材料审计

> 审计对象：`briefing.md`、`discussion-synthesis.md` 与本地保存的 11 轮原始可见问答。本文记录材料覆盖与证据口径，不替代外部来源逐项核查，也不把拟建实验写成已完成工作。
>
> 本审计只覆盖 2026-08-13 briefing；当前研究合同见
> [`../../../research-program.md`](../../../research-program.md)。

## 1. 原始 11 轮覆盖

结构化归档记录 11 条 user 与 11 条 assistant final，共 22 条可见消息，轮次 1–11 严格交替。归档明确排除了 system、tool、reasoning 和 commentary 节点；因此准确说法是“完整保存 11 轮可见问答”，不是“保存全部内部会话状态”。

| 轮次 | 核心问题或修正 | 整理稿位置 |
| --- | --- | --- |
| 1 | 从绝对分数转向 lift、ranking、decision regret；追问 so what | `briefing.md` §§1、4、5；`discussion-synthesis.md` §1 |
| 2 | SWE-bench 的公共协调价值；公共榜单与 repo-specific eval 的采用逻辑不同 | `briefing.md` §§3.1、5；`discussion-synthesis.md` §2 |
| 3 | task pass/fail 与“优化项目”之间存在反事实缺口 | `briefing.md` §2；`discussion-synthesis.md` §3 |
| 4 | 区分工程师根据诊断改系统，与 Agent 自主发现并修改项目 | `briefing.md` §2；`discussion-synthesis.md` §3 |
| 5 | project intervention 使未来 workload treatment-dependent；项目价值没有统一二元标签 | `briefing.md` §2；`discussion-synthesis.md` §4 |
| 6 | workload 与 outcome 分开；后来真实 workload 保持外部锚；RSI 只放大需求 | `briefing.md` §§2、5、11；`discussion-synthesis.md` §§4、9 |
| 7 | gradient 类比修正为 Proposer/Evaluator/Selection；intervention 仅作校准 | `briefing.md` §§2、5；`discussion-synthesis.md` §5 |
| 8 | Generator/Selector 只构成地基；SWE-Future/INTERACT/Together/RQGM 各补一块 | `briefing.md` §§3、6、7；`discussion-synthesis.md` §§7、8 |
| 9 | Generator 拆成 forecast/materialization/response；Reality/Challenge 分流 | `briefing.md` §7；`discussion-synthesis.md` §8 |
| 10 | 管理评委需要先例子、少术语、少公式、中文首释 | `briefing.md` §§1–5；`discussion-synthesis.md` §9 |
| 11 | RSI 不是成立前提；区分 milestone/vision；保留外部 reality anchor | `briefing.md` §§9、11–13；`discussion-synthesis.md` §§9–11 |

## 2. 关键质疑的最终回答

### “能不能指导项目优化”有三种含义

1. **直接告诉人或 Agent 该改什么**：当前不能承诺。失败归因不是改动的因果效果；已知有限选项应直接做 ablation。
2. **在若干 Agent/system 版本中判断哪个值得 ship**：这是拟新增的核心研究问题。当前只有 pointwise development evidence，还没有 selection-validity 确认。
3. **让 Agent 自主修改项目并评价项目整体价值**：一般情形下 future workload 随干预改变，反事实不可同时观察，outcome 也不统一。因此不作为第一阶段一般性主张；外生 workload、明确 outcome 或可随机化的窄场景不被排除。

### Proposer、Evaluator 与 Selection 的边界

- Proposer 产生候选，可由工程师、配置搜索或外部 self-improver 实现。
- Barcarolle 主要提供 Evaluator/evidence boundary。
- Selection 根据冻结证据选择下一版本，证据不足时允许 abstain。
- Barcarolle 提供 selection pressure，不提供 gradient，不负责保证候选提出者找到好方向。

### workload 与 outcome 的边界

- workload 是外部软件工程需求流；后来真实工作是最终 reality anchor。
- Generator 预测需求方向并把需求具体化为可执行 Task，不生成“项目提高多少”的标签。
- outcome 是执行后测得的结果；第一阶段保持 pass/fail，time、cost、interaction、correction 等以后作为向量报告。

## 3. 事实、推断、假说与愿景

### 已核对事实

- 当前仓库有可审计运行和 hidden-oracle replay 边界。
- 当前 selector 结果来自 retrospective、outcome-open development search，不是 independent confirmation。
- `consensus_rate_match` 只在被报告的 same-Harness、repository-equal development estimand 上改善；换为 origin weighting 后反转，在被测的完整 system/Harness 场景没有保持优势。
- 原始 11 轮对话提出并最终撤回了“一般 project optimizer benchmark”作为近期主张。

### 支持性推断

- reference-to-target population shift 是当前优先故障假说；现有证据不能排除样本量、任务构成或 Agent–Task interaction。
- public benchmark 的 coordination value 与 repo-specific eval 的 local decision value不同。
- forecast family 的相关性不能替代 materialization validity 和 response validity。

### 待验证假说

- 搜索候选数、轮数或反馈粒度增加时，static evaluator 的 selection regret 会增加。
- contrast-aware selection、support/abstention 和 epoch refresh 能使 regret/lift error 随压力增长得更慢。
- repeated/cross materialization 与基于较早时间块的 response calibration 能改善 later-real-work contrast prediction。
- 同 proposer、同预算时，Barcarolle evaluator 组最终会在 sealed future workload 上取得更大真实增益。

### 愿景

- 为外部 self-improver 提供长期可信的 selection pressure。
- 愿景不等于已经存在的 production Selector、Generator、adaptive protocol 或 Optimization Horizon 测量。

## 4. 当前态与拟建态

| 层 | 当前态 | 拟建态 |
| --- | --- | --- |
| Benchmark boundary | Task/Check、Workspace、Verification、Result、Selection、Reporting、Runner 已有 | 保持边界小且可审计 |
| Selector evidence | outcome-open retrospective development candidate；迁移诊断未保持优势 | contrast-aware、support-aware、可 abstain，并在新边界确认 |
| Generator | 材料提出边界和验证框架；没有证明完整新 Generator 已实现 | Forecaster + Materializer；三层 validity；Reality/Challenge 分流 |
| Adaptive experiment | 尚未执行 | 候选池压力测试，再做闭环 proposer/evaluator 对照 |
| Prospective evidence | 尚无 | 冻结 pipeline 后等待新 repository/time window 的真实工作 |

## 5. 不可声称边界

- 当前结果不是 strict-prospective、independent 或 confirmatory evidence。
- 未证明 production Selector、field validity、跨 Harness/模型家族/仓库泛化。
- 未证明 repeated optimization 已在 Barcarolle 上造成 Goodhart 退化，也未证明 Barcarolle 能减缓它。
- 未测得 Optimization Horizon。
- 未证明 Generator 的任务代表未来真实工作，或 synthetic workload 可替代 later real workload。
- 未识别跨 system/Harness 失败的唯一因果机制。
- Barcarolle 不是 Proposer、trainer、通用 RSI 系统或通用项目价值函数。

## 6. 研究 gate 需要的机器检查

### Gate A：归档与输入完整性

- 校验原始 JSON 的 `expected_turns=11`、user/assistant final 各 11 条、轮次严格交替。
- 记录原始聊天和外部 source snapshot 的 SHA-256、抓取时间、URL 与文件大小。
- 检查研究材料中的本地链接、外部链接和 citation ID 是否可解析；链接失效不得静默删除来源记录。

### Gate B：时间与泄漏边界

- 对每个 Origin 断言 Selector、Generator、Proposer 只读取 cutoff 前材料。
- 对所有 task/result/feature 记录 availability，并拒绝未来时间戳、缺 provenance 或同一 future block 同时用于 calibration 与 evaluation。
- 自动检查 candidate selection、阈值、Materializer 配置和主指标的冻结时间早于 sealed block 打开时间。

### Gate C：身份、执行与预算等价

- 哈希完整 Agent identity：模型、Harness、prompt/skills、tools、retrieval、retry、预算和 runtime settings。
- 验证各 evaluator arm 使用同初始 Agent、同 Proposer 版本、同候选/轮数预算、同停止规则、同随机种子策略。
- 对 solver/verifier workspaces、hidden oracle 注入点和最终 diff replay 做 fail-closed 检查。

### Gate D：统计与选择复现

- byte-for-byte 重跑 Selection；用独立实现复算 membership、score、lift、ranking、top-1 regret 和 abstention。
- 同时报告 repository-equal 与 origin-weighted 结果，并预先指定 primary estimand；禁止事后切换权重挑结果。
- 候选池压力测试固定候选顺序/抽样种子，报告 K=2/5/10/20/50 的不确定性与多重比较策略。
- 对 cold/warm start、reference support、Harness shift 和 target ability 做预声明分层；小样本不得输出伪精确排名。

### Gate E：Generator 有效性

- 同一 family 多次独立 materialize，记录随机种子、Materializer identity、requirement、checks 和 oracle digest。
- 自动计算 synthesis sensitivity、pairwise contrast 翻转率和 cross-materializer transfer。
- Reality Generator 禁止读取当前 Agent failures/traces；Challenge Generator 的产物和分数必须使用不同 namespace，不得进入 external-validity claim。
- response calibration 使用早期 rolling-origin blocks；最终 sealed block 只评估一次。

### Gate F：Adaptive pressure 与外部确认

- exposure ledger 逐轮记录 optimizer 看过的 task、aggregate score、trace 和 check 粒度。
- epoch refresh 后验证旧 evidence 的 validity lifetime，并拒绝将 later-real outcomes 回流到 proposer。
- 自动生成 benchmark-gain 与 real-future-gain 轨迹、selection regret 曲线和预定义的 Optimization Horizon；阈值未满足时输出“未测得/不支持”，而不是外推。
- 最终 claim 必须通过新的 same-Harness sealed boundary；strict-prospective claim 还必须通过冻结 pipeline 后的新 repository/time window。

## 7. 收口结论

当前材料已覆盖 11 轮讨论的关键质疑与收敛路径。最重要的口径是：已有的是 outcome-open retrospective 工程与 development evidence；拟建的是以 later real workload 为外部锚的 selection-validity 研究。所有关于 adaptive Goodhart、Generator response validity、Optimization Horizon 和 closed-loop 增益的表述都属于待验证假说，必须通过上述机器 gate 后才能升级为结果。
