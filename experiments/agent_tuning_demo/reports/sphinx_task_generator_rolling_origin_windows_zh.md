# sphinx Task Generator corrected rolling-origin windows

生成时间：`2026-06-17T14:49:26+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

certified task count `100` supports `3` corrected windows；state: `preferred_policy_supported`。

每个 origin 的 selected benchmark 只能从 `history_pool_before_origin` 选择；`future_holdout_after_origin` 的 IDs/outcomes 不是 selector inputs。

| Origin | History pool | Selected size | Future holdout | First future | Last future |
| --- | --- | --- | --- | --- | --- |
| origin_40 | 40 | 20 | 20 | sphinx__taskgen__0127 | sphinx__taskgen__0181 |
| origin_60 | 60 | 20 | 20 | sphinx__taskgen__0183 | sphinx__taskgen__0345 |
| origin_80 | 80 | 20 | 20 | sphinx__taskgen__0349 | sphinx__taskgen__0471 |
