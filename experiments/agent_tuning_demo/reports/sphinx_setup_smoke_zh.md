# Sphinx target profile and setup smoke

生成时间：`2026-06-17T10:32:21+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

当前 Sphinx checkout 的小型 targeted smoke 为 `2/2` 通过，targeted verifier 时间等级为 `ideal_under_60s`。

## Checkout

- repo: `sphinx`
- path: `experiments/phase0_headroom/external_repos/sphinx`
- HEAD: `581c0860dfed` / `2026-06-15T08:51:10+02:00`
- subject: `Document 'graphviz' requirement for 'sphinx.ext.graphviz' (#14487)`

## Smoke 结果

| Shard | Status | Seconds | RC | Profile |
| --- | --- | --- | --- | --- |
| sphinx_util | passed | 0.309 | 0 | py314_current_editable |
| sphinx_config | passed | 0.641 | 0 | py314_current_editable |

## 记录边界

命令记录只保留 command shape、duration、return code、行数和尾部 hash；未提交 raw stdout/stderr、solver workspace、verifier workspace、prompt、completion 或 transcript。
