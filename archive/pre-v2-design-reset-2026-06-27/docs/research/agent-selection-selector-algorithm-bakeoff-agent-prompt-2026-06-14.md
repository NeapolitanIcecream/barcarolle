# Prompt For Selector Algorithm Bakeoff Agent

Please execute this runbook end to end:

```text
/Users/chenmohan/gits/barcarolle/docs/research/agent-selection-selector-algorithm-bakeoff-runbook-2026-06-14.md
```

Goal: explore the full selector algorithm space quickly and honestly. Implement
RSQ v2, FLC, HRD v3, COD-lite, RO-LSP, SAES-lite, strong random baselines, and a
less conservative demo-appropriate decision wrapper. Run ablations and compare
selectors on Agent-selection decision quality first: whether Selection
recommends an Agent and later/Holdout validates that choice. Report MAE and
relative MAE improvement as auxiliary evidence, not as a hard veto.

Do not stop after a diagnostic. Build the algorithms, run the bakeoff, freeze a
final candidate, and run the strongest available final replay or fresh paid
validation allowed by the runbook. Do not retune on final outcomes. Paid calls,
if needed, must use `LLM_BASE_URL` plus `LLM_API_KEY` and stay inside the
70-cell cap.

Make focused commits after each package. Final closeout must list implemented
algorithms, ablations, selected decision rule, final Selection and
later/Holdout pass rates, recommendation regret, random-baseline comparison,
MAE/relative MAE improvement, paid cells/cost, tests, and the exact demo claim
now supported.

