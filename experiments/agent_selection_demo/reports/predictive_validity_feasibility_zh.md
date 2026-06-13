# Predictive-validity Feasibility

生成日期：2026-06-13T13:36:11+00:00

本报告只读取 committed sanitized outcomes、score tables 和 metadata summaries；没有读取 raw prompts、raw completions、transcripts、solver workspaces、verifier workspaces 或 provider logs，也没有运行 paid calls。

## Summary

- Candidate repos: `3`.
- Windows inventoried: `5`.
- Metric slices available: `208`.
- Pass-rate prediction windows: `4`.
- Baseline-comparison windows: `3`.
- Raw artifacts needed: `False`.

## Repos

| Repo | Eligible | Any outcome | Both Agents | Time buckets |
| --- | --- | --- | --- | --- |
| attrs | 30 | 25 | 25 | legacy_2018_or_earlier:4, middle_2019_2022:26 |
| boltons | 35 | 30 | 30 | legacy_2018_or_earlier:24, middle_2019_2022:8, recent_2023_or_later:3 |
| click | 30 | 28 | 28 | middle_2019_2022:4, recent_2023_or_later:26 |

## Windows

| Window | Mode | Repos | Agents | Pass-rate | Rank/regret | Baselines | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| blocked_split_heldout | retrospective_pseudo_future | attrs, boltons, click | codex_workspace, kilo_workspace | True | True | True | accepted |
| original_three_repo_split_heldout | retrospective_pseudo_future | attrs, boltons, click | codex_workspace, kilo_workspace | True | True | True | accepted |
| repo_specific_earliest_time_bucket_cutoff | true_rolling_origin_diagnostic | attrs, boltons, click | codex_workspace, kilo_workspace | True | True | True | diagnostic_sparse |
| demo_boltons_selection_to_holdout | demo_fresh_holdout | boltons | codex_gpt_5_4, kilo_claude_sonnet_4_6, kilo_gpt_5_4, kilo_gpt_5_4_mini | True | True | False | accepted_for_demo_metric |
| demo_boltons_top2_repeat | demo_repeatability_blocker | boltons | codex_gpt_5_4, kilo_gpt_5_4 | False | False | False | blocked_infrastructure |

## Interpretation

至少一个 no-paid retrospective window 可以支持 pass-rate prediction 和 simple-baseline comparison。`attrs`、`boltons`、`click` 都有 committed sanitized outcomes；demo 自身的 `boltons` selection-to-holdout window 可以支持推荐反转和 regret 解释，但缺少同预算 simple baselines，因此不能单独作为 predictive-validity proof。

True rolling-origin support 仍偏 sparse；phase1 window plan 把 repo-specific earliest bucket cutoff 标为 diagnostic_sparse。Package 5 的分析必须把结果写成 retrospective/directional 或 negative/underpowered evidence。
