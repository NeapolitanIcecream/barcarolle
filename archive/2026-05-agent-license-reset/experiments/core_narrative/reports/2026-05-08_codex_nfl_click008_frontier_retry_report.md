# Barcarolle NFL Click008 Frontier Retry Report

Date: 2026-05-08 Asia/Shanghai
Branch: codex/nfl-click008-frontier-retry

## Why This Ran

PR #4 closed the first Click008 attempt 3 replay, but both frontier cells were still infra outcomes. I ran two bounded follow-ups without repeating the cheap cells:

- Attempt 4: `frontier-generic-swe` and `frontier-click-specialist`
- Attempt 5: only `frontier-click-specialist`, after attempt 4 hit provider HTTP 500

The goal was not to expand the experiment. The goal was to convert Click008 frontier infra failures into scoreable outcomes.

## Artifacts

- Attempt 4 approval: `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_frontier_retry_attempt4_approval_20260508.json`
- Attempt 4 budget gate: `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_frontier_retry_attempt4_budget_gate_20260508.json`
- Attempt 4 live summary: `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_frontier_retry_attempt4_live_20260508.json`
- Attempt 5 approval: `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_frontier_specialist_retry_attempt5_approval_20260508.json`
- Attempt 5 budget gate: `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_frontier_specialist_retry_attempt5_budget_gate_20260508.json`
- Attempt 5 live summary: `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_frontier_specialist_retry_attempt5_live_20260508.json`
- Canonical closure summary: `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_scoreable_closure_20260508.json`
- Ledger: `experiments/core_narrative/results/cost_ledger.jsonl`

## Result

Canonical latest Click008 result by ACUT:

| ACUT | Latest attempt | Status | Failure class | Outcome meaning |
| --- | ---: | --- | --- | --- |
| `cheap-generic-swe` | 3 | `failed` | verifier failure | Valid patch artifact, but hidden verifier failed. |
| `cheap-click-specialist` | 3 | `invalid_submission` | `search_replace_anchor_mismatch` | Model response could not satisfy anchored edit contract. |
| `frontier-generic-swe` | 4 | `invalid_submission` | `search_replace_old_occurrence_mismatch` | Provider returned; model output referenced old text that did not match current source. |
| `frontier-click-specialist` | 5 | `invalid_submission` | `search_replace_old_occurrence_mismatch` | Provider returned after one HTTP 500 retry; model output still failed source matching. |

Aggregate canonical result:

- Passed: 0 / 4
- Scoreable: 4 / 4
- Status counts: 1 `failed`, 3 `invalid_submission`
- Remaining infra failures in canonical set: 0

## Cost

Ledger state after attempt 5:

- Records: 79
- Cumulative estimated cost: $15.697699
- Increment after PR #4 merge: $3.597673
- Provider-reported usage in attempts 4-5: $0.597673
- Conservative projected provider-error estimate in attempt 4: $3.000000

The $3.000000 provider-error record came from the fixed timeout/provider-error ledger path and is conservative budget accounting, not invoice-confirmed provider cost.

## Interpretation

This is now a clean Click008 story: after removing frontier infra ambiguity, none of the four core ACUTs solved the task. The dominant failure mode is not the verifier setup anymore; it is model-output fidelity against the anchored search/replace contract.

For Barcarolle's NFL angle, this is useful because the scoreboard separates:

- one game-play failure after a patch reached verification,
- three rule/submission failures before verification,
- zero unresolved operations failures in the canonical Click008 set.

That makes Click008 a good example of why the experiment needs play-by-play outcome labels, not only pass/fail.

## Next Step

Do not retry Click008 again immediately. The local evidence says the next useful work is analysis/reporting over the completed Click004-008 and Click008 closure data: quantify how much of the failure mass is verifier failure, invalid submission, or infra, then decide whether the next intervention should be prompt/contract design or a new task slice.
