# Agent Tuning Demo preregistration

生成时间：`2026-06-17T15:20:31+00:00`。

## 冻结协议

| Item | Value |
| --- | --- |
| Primary repo | `mypy` |
| Origin | `origin_40` |
| Selected benchmark | `20` |
| Train feedback | `12` |
| Dev eval | `8` |
| Future holdout | `20` |
| Planned paid cells | `76` |
| Max concurrency | `2` |

本轮使用 corrected rolling-origin 形状：`history_pool_before_origin -> selected_benchmark_from_history -> future_holdout_after_origin`。
selected benchmark 只从 origin 前历史池选择；future holdout ID 在 artifact hash freeze 前只以 hash 形式记录，不进入反馈或候选 artifact。

## Agent 与 artifact

- Baseline: `Kilo + GPT low-cost` / `gpt-5.4-mini` / `kilo`。
- Tuned surface: repo-local `AGENTS.md` appendix, injected as `repo_AGENTS_md`。
- Tuner/proposer: train-only local rule proposer first; no LLM proposer unless later iterations need it and ledger records the call.

## Scheduler

- Entry point: `uv run --project experiments/phase1_compiler python experiments/agent_tuning_demo/tools/agent_tuning_demo_run.py run-stage`。
- Default concurrency: `2`, hard cap `4`。
- One selected-baseline paid cell is the scheduler smoke; the later selected-baseline batch skips it by stable row key.
- Raw prompts/completions/transcripts/workspaces are not committed; raw adapter artifacts stay under ignored phase0 paths.

## Endpoint proof

- `LLM_BASE_URL` present: `True`。
- `LLM_API_KEY` present: `True`。
- Endpoint host hash: `9952174049b2`。
- Key fingerprint: `1169c0fc`。
