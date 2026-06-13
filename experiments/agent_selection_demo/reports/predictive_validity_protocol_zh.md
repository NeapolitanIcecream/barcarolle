# Predictive-validity Protocol

生成日期：2026-06-13

状态：frozen before Package 5 no-paid retrospective analysis and before any Package 6 paid-pilot decision.

## 1. Agent unit

本 protocol 的 Agent unit 是完整 Agent：

```text
model + harness + prompt/tools/runtime policy
```

在本 demo 中，`codex_gpt_5_4`、`kilo_gpt_5_4`、`kilo_gpt_5_4_mini`、`kilo_claude_sonnet_4_6` 都是完整 Agent 配置；在 phase1 retrospective artifacts 中，`codex_workspace` 和 `kilo_workspace` 也是完整 Agent/adapter boundary，不解释成纯模型差异。

## 2. Primary estimand

Primary estimand:

> 在目标仓库的历史 origin `T`，只使用 `T` 之前或当时可见的任务与元数据编译 benchmark selection，预测同一完整 Agent 在 `T` 之后目标仓库任务上的 verified pass rate 的准确度。

Plain-language version:

> 一个 repo-specific benchmark 选出来的任务，能不能比简单替代方案更准确地估计同一 Agent 之后在这个仓库真实任务上的通过率？

## 3. Primary metric

Primary metric 是 pass-rate MAE：

```text
mean(abs(selection_pass_rate - future_pass_rate))
```

平均单位是 preregistered `(repo, origin/window, Agent)` slices。只有 selection side 和 future side 都至少有一个 scoreable cell 的 slice 才进入 MAE。missing 或 non-scoreable cell 不被强行算作 pass/fail，而是计入 missing/non-scoreable 诊断。

## 4. Secondary metrics

- Signed error: `selection_pass_rate - future_pass_rate`，用来判断系统性高估或低估。
- RMSE: 对大错误更敏感。
- Rank agreement: 同一 `(repo, origin/window)` 至少有两个 Agent 可评分时，比较 selection rank 与 future rank 是否一致。
- Recommendation regret: selection 推荐的 Agent 在 future pass rate 上比 future-best Agent 低多少。
- Catastrophic miss rate: `abs(error) > 0.15` 的 slice 占比。

`0.15` threshold 沿用 phase1 retrospective predictive-signal tooling 中的 catastrophic-gap threshold。

## 5. Baselines

每个结果必须和 simple baselines 比较。Protocol 冻结的 baselines 是：

| Baseline | Role |
| --- | --- |
| `temporal_recent_baseline` | 同预算最近任务 baseline |
| `seeded_random_same_budget` | 多 seed 同预算随机 baseline |
| `repo_unweighted_same_budget` | 同 repo 不加权 baseline |
| `repo_stratified_by_target_profile` | repo-stratified/simple same-budget baseline |
| `best_simple_baseline_envelope` | 上述 simple baselines 中 MAE 最低者 |

Candidate selector:

| Candidate | Role |
| --- | --- |
| `coverage_constrained_unweighted` | Barcarolle-style candidate when available |
| `block_randomized_stratified` | research candidate |
| `block_plus_shrinkage_weighted` | research candidate |

`completed_blocked_split_supplement` 只能作为 diagnostic candidate，不作为 promotable winner。

## 6. Reporting policy

- 不能只报告 best run；必须报告 simple baseline distribution 或 envelope。
- 不把 adapter instability pooling 掉；报告 Agent/adapter-stratified结果。
- Retrospective result 只能叫 retrospective traction 或 negative/underpowered evidence。
- Future proof 需要 strict preregistered rolling-origin 或 true future holdout。
- Kilo timeout blocker 不得被解释成模型质量失败；它是 adapter/CLI infrastructure blocker。

## 7. Directional traction versus no signal

Directional retrospective traction 需要同时满足：

- promotable Barcarolle candidate 的 primary MAE 低于 best simple baseline envelope；
- 至少 `12` 个 scoreable `(repo, origin/window, Agent)` slices；
- comparison 使用 frozen protocol 和 committed sanitized outcomes；
- 没有把 diagnostic-only candidate 当成 promotable result；
- 报告仍明确写成 retrospective/underpowered，而不是 predictive-validity proof。

No signal 或 negative result 包括：

- best promotable Barcarolle candidate MAE 高于或等于 best simple baseline；
- support 太少，slice count 低于 `12`；
- policy violation、non-scoreable rate 或 adapter timeout 让结果不能解释；
- result 只来自 post-hoc diagnostic candidate。

## 8. Future predictive-validity claim gate

未来要 claim predictive validity，至少需要：

- 在 outcome join 前冻结 repos、origins/cutoffs、task IDs、Agent configs、selectors、baselines、seeds、invalid-cell policy、success threshold；
- 使用 true future holdout 或 strict rolling-origin，而不是事后 retrospective design；
- 每个 primary claim 至少覆盖两个目标仓库和两个 stable Agent paths，或明确缩窄到单仓库 claim；
- candidate selector 在 primary MAE 上 beat best simple baseline envelope，并在 rank/regret metrics 上不出现反向信号；
- scoreability、policy violation、endpoint compliance、artifact hygiene 和 cost accounting gates 全部通过；
- 报告 uncertainty 或 seed distribution。

## 9. Frozen command surface

Feasibility command:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler python experiments/agent_selection_demo/tools/agent_selection_demo.py predictive-validity-feasibility --output experiments/agent_selection_demo/reports/predictive_validity_feasibility_zh.md
```

Evaluation command:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler python experiments/agent_selection_demo/tools/agent_selection_demo.py rolling-origin-eval --protocol experiments/agent_selection_demo/results/predictive_validity_protocol.json --window-inventory experiments/agent_selection_demo/results/predictive_validity_window_inventory.json --output experiments/agent_selection_demo/reports/rolling_origin_eval_zh.md
```

## Acceptance

- Estimand, metrics, baselines, and claim boundary are frozen before Package 5 analysis.
- Protocol says what would count as directional traction versus no signal.
- Protocol says what future evidence would be required for a predictive-validity claim.
