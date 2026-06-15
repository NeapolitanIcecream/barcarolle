# Agent Tuning Phase 2 protocol freeze

生成日期：2026-06-15T02:20:27+00:00

## 冻结路线

- Agent: `Kilo + GPT low-cost` (`kilo_gpt_5_4_mini`)
- Surface: Kilo repo `AGENTS.md` appendix
- Target repo: `mahmoud/boltons`
- Optimizer path: GEPA standalone `optimize_anything` with a repo-local custom proposer; no reflection LM is used.

## Headroom

选择 `kilo_gpt_5_4_mini` 是因为它在现有 sanitized Selection table 中为 `13/20`，Holdout 为 `6/10`，比 Kilo GPT mainline 更有可调空间，同时仍是 Kilo workspace Agent。

## Split

| Split | Count | Visibility |
| --- | --- | --- |
| selection_train | 16 | optimizer-visible |
| selection_dev | 4 | evaluation-only |
| holdout | 6 | withheld until artifact hash freeze |

Holdout task ids are not written into optimizer input. The protocol stores only the Holdout subset count and SHA-256 digest until the chosen artifact hash is frozen.

## Stop conditions

- Stop before optimizer rollout if action-level preflight does not pass.
- Stop before Holdout if Selection-dev paired net wins are negative or tuned invalid runs exceed baseline invalid runs.
- Stop if paid-cell caps would be exceeded.
- Stop on missing LLM_BASE_URL or LLM_API_KEY before any paid Agent cell.
- Stop if artifact hash is not frozen before Holdout.
