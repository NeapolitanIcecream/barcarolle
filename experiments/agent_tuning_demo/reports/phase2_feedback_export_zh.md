# Agent Tuning Phase 2 feedback export

生成日期：2026-06-15T02:21:43+00:00

- Target Agent: `kilo_gpt_5_4_mini`
- Exported Selection-train rows: `16`
- Holdout task IDs/logs/prompts/completions/transcripts: not exported.
- Raw workspaces and raw verifier material: not exported.

## Failure labels

| Label | Count |
| --- | --- |
| timeout_or_context_exhaustion | 2 |
| verified_pass | 13 |
| wrong_api_semantics | 1 |

Every label is derived from committed sanitized score rows plus sanitized tool summaries from ignored raw stdout. Raw transcript text is not committed.
