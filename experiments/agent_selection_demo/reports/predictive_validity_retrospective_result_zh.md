# Predictive-validity Retrospective Result

生成日期：2026-06-13

## 执行状态

本 package 使用 frozen protocol 和 Package 3 window inventory，运行了 no-paid rolling-origin/pseudo-future evaluation。

命令：

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler python experiments/agent_selection_demo/tools/agent_selection_demo.py rolling-origin-eval --protocol experiments/agent_selection_demo/results/predictive_validity_protocol.json --window-inventory experiments/agent_selection_demo/results/predictive_validity_window_inventory.json --output experiments/agent_selection_demo/reports/rolling_origin_eval_zh.md
```

新增 paid calls：`0`。

Raw artifacts needed：`false`。

## 分析了哪些 windows

| Window | Mode | 用途 | Baseline comparison |
| --- | --- | --- | --- |
| `blocked_split_heldout` | retrospective pseudo-future | phase1 三仓库 held-out split | yes |
| `original_three_repo_split_heldout` | retrospective pseudo-future | phase1 原三仓库 split | yes |
| `repo_specific_earliest_time_bucket_cutoff` | true rolling-origin diagnostic | repo-specific earliest bucket cutoff | yes, but sparse |
| `demo_boltons_selection_to_holdout` | demo fresh holdout | boltons selection-to-holdout contradiction and regret | no simple same-budget baselines |
| `demo_boltons_top2_repeat` | repeatability blocker | Kilo repeat timeout diagnosis | no metric slice |

Repos covered by retrospective/baseline windows：`attrs`、`boltons`、`click`。

Agents/adapters covered：`codex_workspace`、`kilo_workspace`。Demo-only window additionally covers `codex_gpt_5_4`、`kilo_gpt_5_4`、`kilo_gpt_5_4_mini`、`kilo_claude_sonnet_4_6`。

## 数据来源

The outcomes are existing committed sanitized artifacts:

- phase1 paid score tables and score joins, reused no-paid in this package;
- phase1 retrospective predictive-signal metric rows;
- agent-selection demo selection/holdout score tables and metrics;
- top-2 repeat metrics only as blocker context.

Package 5 did not read raw prompts, raw completions, transcripts, solver workspaces, verifier workspaces, provider logs, or secrets.

## Numeric results

Primary comparison:

| Design | Role | MAE | RMSE | Signed error | Catastrophic miss | Slices |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `temporal_recent_baseline` | best simple baseline | `0.214900` | `0.257954` | `-0.061789` | `0.555556` | `18` |
| `coverage_constrained_unweighted` | best Barcarolle candidate | `0.209011` | `0.258881` | `-0.043267` | `0.555556` | `18` |
| `completed_blocked_split_supplement` | diagnostic only | `0.140733` | `0.168746` | `0.107400` | `0.333333` | `6` |

Candidate minus best simple MAE：

```text
-0.005889
```

Rank/regret diagnostics over groups with at least two Agents:

- Rank groups evaluated：`64`
- Top-rank agreement rate：`0.8125`
- Regret groups evaluated：`64`
- Mean recommendation regret：`0.041552`
- Max recommendation regret：`0.4`

Demo-only boltons selection-to-holdout metric:

- `demo_selection_set` MAE：`0.136111`
- Slices：`4`
- Catastrophic miss rate：`0.5`
- This window has no simple same-budget baselines, so it is motivation and regret evidence, not proof.

## Baseline comparison result

The best promotable Barcarolle candidate, `coverage_constrained_unweighted`, beats the best simple baseline, `temporal_recent_baseline`, by `0.005889` MAE on the no-paid retrospective evaluation.

This meets the frozen protocol's directional retrospective traction rule:

- candidate MAE is lower than best simple baseline MAE;
- candidate slice count is `18`, above the `12` slice support threshold;
- comparison uses committed sanitized outcomes;
- diagnostic-only `completed_blocked_split_supplement` is not promoted.

It does not establish predictive validity because the analysis is retrospective/pseudo-future and partly diagnostic_sparse. The effect size is small, catastrophic miss rate is unchanged against the best simple baseline (`0.555556` for both), and future-preregistered validation has not passed.

## Demo story implication

The completed boltons Agent-selection demo showed a selection recommendation contradicted by fresh holdout. This Package 5 result adds the missing predictive-validity layer:

- Barcarolle can now express the problem as pass-rate prediction from selection tasks to later target-repo tasks;
- it can compare candidate selectors to simple same-budget baselines;
- current no-paid evidence gives directional retrospective traction, not proof;
- if future results are negative or underpowered, that still supports the project thesis: optimizing predictive validity is the hard part, not merely running pass/fail dashboards.

## Package 5 acceptance

- Numeric predictive metrics were produced from the frozen protocol.
- Baseline comparison says candidate beats best simple baseline by a small MAE margin.
- The report explicitly keeps the claim at directional retrospective traction.
- No raw artifacts and no new paid cells were required.
