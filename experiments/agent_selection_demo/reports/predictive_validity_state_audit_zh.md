# Predictive-validity State Audit

生成日期：2026-06-13

## 结论

现有 demo 证据能支持一个重要但有限的结论：目标仓库 Agent 选型不能只看一次选择集结果，因为 `mahmoud/boltons` 的冻结推荐在 fresh holdout 上被反转。这说明 predictive validity 是 Barcarolle 必须解决的核心问题。

现有证据还不能证明 predictive validity。已经提交的 phase1 和 demo artifacts 包含可复现的 sanitized outcomes、retrospective pseudo-future 指标、一次 boltons future-holdout pilot、一次 two-repo future-holdout pilot，以及本 demo 的 selection/holdout/repeat 结果；但这些结果要么样本太小，要么 retrospective/post-hoc，要么有 policy violation 或 adapter timeout blocker。

因此，当前状态是：

- 可以说 Barcarolle 已经有完整 Agent 运行、diff 捕获、干净验证、sanitized score table 和 rolling-origin/pseudo-future 分析基础；
- 可以说现有 evidence 解释了为什么 predictive-validity optimization 是项目主线；
- 不能说 Barcarolle 已经证明 repo-specific benchmark 能稳定预测未来 Agent pass rate；
- 不能说 coverage-constrained selector、Codex、Kilo、GPT 或 Claude 有跨仓库稳定优势。

## Evidence ledger

机器可读 ledger：

```text
experiments/agent_selection_demo/results/predictive_validity_evidence_ledger.json
```

Ledger 只引用 committed sanitized reports/results。它不需要 raw prompts、raw completions、raw transcripts、solver workspaces、verifier workspaces、provider logs 或 secrets。

## 可用 evidence 摘要

| Evidence | Repos | Agents/adapters | Counts | 支持什么 | 不能支持什么 |
| --- | --- | --- | ---: | --- | --- |
| Agent-selection demo selection | boltons | 4 demo Agents | 80 scheduled, 76 scoreable | selection set 可运行，top-2 quality tie 可审计 | future prediction proof |
| Agent-selection demo holdout | boltons | 4 demo Agents | 40 scheduled, 40 scoreable | frozen recommendation 被 fresh holdout contradicted | selector predictive validity |
| Top-2 repeatability | boltons | Codex GPT, Kilo GPT | 20 scheduled, 13 completed, 10 scoreable | Codex repeat 完成，Kilo repeat blocked | Kilo lead stability |
| Phase1 boltons future holdout | boltons | codex_workspace, kilo_workspace | 8 B_eval + 8 H_future scoreable | small future-holdout MAE `0.25` | production ranking 或 predictive-validity claim |
| Phase1 two-repo future holdout | boltons, attrs | codex_workspace, kilo_workspace | 16 B_eval scoreable, 15 H_future scoreable | two-repo pilot exposed policy violation and high MAE | validated two-repo prediction |
| Phase1 retrospective signal | attrs, boltons, click | codex_workspace, kilo_workspace | 95 eligible tasks, 3 windows, 3832/4234 joined scoreable rows | no-paid retrospective traction against best simple baseline | formal future proof |
| Phase1 three-repo paid validation | attrs, boltons, click | codex_workspace, kilo_workspace | 120/120 scoreable | workspace Agent protocol and conservative validation feasibility | future prediction |

## Claim boundary by artifact

`final_agent_selection_demo_package_zh.md` 和 `demo_completion_closeout_zh.md` 已经把 demo 收束为 target-repo Agent selection story：选择集推荐被 holdout 反转，Kilo repeat 被 timeout 阻断，成本 usage 口径不可比。这些内容是 predictive-validity story 的起点，不是终点。

`phase1_future_holdout_*` 和 `phase1_two_repo_future_holdout_*` 是更接近 predictive-validity 的 evidence，但两者都明确标记 predictive validity not established。boltons-only future holdout repo 数和 holdout scoreable cells 不够；two-repo future holdout 有 `policy_violation_count_exceeds_acceptance_gate`。

`phase1_retrospective_predictive_signal_*` 是当前最有用的 no-paid rolling-origin/pseudo-future evidence。它比较了 simple baselines 与 coverage-constrained candidate，得到 best simple baseline `temporal_recent_baseline` MAE `0.2149`，best Barcarolle candidate `coverage_constrained_unweighted` MAE `0.209`。这只支持 directional retrospective traction，不能被表述为 predictive validity proof。

## Package 1 acceptance

- 当前 demo evidence 支持 predictive validity 的重要性，但不证明 predictive validity。
- Ledger 已识别现有可用 outcomes，优先使用 committed sanitized artifacts。
- 本 package 没有运行 paid calls。
