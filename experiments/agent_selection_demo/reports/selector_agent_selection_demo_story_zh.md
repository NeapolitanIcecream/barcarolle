# Selector Agent-selection Demo Story

生成日期：2026-06-14

## 旧 demo 的缺口

旧 demo 已经证明 Barcarolle 能运行完整 Agent、捕获 diff、干净重放 verifier，也证明当前任务选择在 pass-rate MAE 上好于同预算随机抽样。

但它还不能直接支持“用户看 Selection 就选 Agent”的故事。原因很具体：原始 `20` 个 Selection tasks 上，`Codex + GPT mainline` 和 `Kilo + GPT mainline` 都是 `15/20`。Selection 没有给出干净质量推荐；后来 Holdout 支持 Kilo，只能说明旧 Selection 证据不足，而不是说明旧 selector 已经会选 Agent。

## 这次改了什么

本轮把 selector 和 decision 分开实现：

- selector 负责选出一个小而可审计的 benchmark；
- decision wrapper 负责判断该不该推荐、abstain，还是需要更多证据。

实现和评估了：

- 三个强随机基线：uniform random、quality-filtered random、source/recency-stratified random；
- RSQ：recency-stratified quota selector；
- HRD：hybrid representative + disagreement selector，含 `70/30`、`60/40`、`50/50` variants 和 ablations；
- 共享 decision wrapper：`recommend`、`abstain_indistinguishable`、`need_more_evidence`。

所有结果都来自 committed sanitized artifacts；没有新 paid cells。

## Frozen final selector

最终锁定：

- Selector：`hrd_70_30`
- Budget：`k=10`
- Representative/discriminative split：`70/30`
- Decision threshold：action margin `5pp`，minimum common valid selected tasks `8`

最终 Selection pass rates：

| Agent | Selection |
| --- | ---: |
| Codex + GPT mainline | `7/10` |
| Kilo + GPT mainline | `9/10` |
| Kilo + GPT low-cost | `7/10` |
| Kilo + Claude Sonnet | `7/10` |

Decision wrapper 输出：

> recommend `Kilo + GPT mainline`

它没有用成本破平，也没有在 tie 上硬推荐。推荐依据是 Kilo 在 selected benchmark 上领先 `20pp`，并且 paired small-sample fallback 没有 top-pair discordant loss。

## Later / Holdout validation

原始 Holdout pass rates：

| Agent | Holdout |
| --- | ---: |
| Codex + GPT mainline | `5/10` |
| Kilo + GPT mainline | `9/10` |
| Kilo + GPT low-cost | `6/10` |
| Kilo + Claude Sonnet | `8/10` |

Doubled-timeout top-2 repeat：

| Agent | Repeat |
| --- | ---: |
| Codex + GPT mainline | `6/10` |
| Kilo + GPT mainline | `9/10` |

所以这次 frozen story 是干净的：

> Selection 推荐 Kilo + GPT mainline；后来 Holdout 和 doubled-timeout top-2 repeat 也都支持 Kilo。

Recommendation regret 是 `0.0`。

## Strong random comparison

Final selector MAE：`0.100000`。

Strong random baseline 使用 `stratified_random__k10`：

- random MAE mean：`0.151700`
- absolute improvement：`0.051700`
- relative improvement：`34.0804%`
- selector beats/ties stratified-random MAE share：`1.0`

Decision metrics 也更好：

- selector recommendation regret：`0.0`
- stratified random mean regret when recommending：`0.152239`
- stratified random false-recommendation rate：`0.380597`
- selector top-pair direction agreement：`true`
- stratified random top-pair agreement rate：`0.619403`

## Claim boundary

现在可以 claim：

> 在 frozen `mahmoud/boltons` demo slice 上，HRD 70/30 selector 加 shared decision wrapper 能给出 Kilo + GPT mainline 推荐；later/Holdout 和 doubled-timeout top-2 repeat 验证了这个推荐，且 recommendation regret 为 `0`。该 selector 在本 slice 的 MAE 也明显优于 strong stratified-random baseline。

不能 claim：

- full predictive validity；
- 跨仓库 selector superiority；
- 全局 Agent 或模型排名；
- 未提交 future tasks 上的泛化结果；
- 成本赢家，因为旧 Selection usage coverage 不可比。
