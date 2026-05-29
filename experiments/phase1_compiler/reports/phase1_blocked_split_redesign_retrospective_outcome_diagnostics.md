# Phase 1 Blocked Split Retrospective Outcome Diagnostics

## What Happened

After the selected split was frozen, existing completed paid score tables were joined where task IDs overlapped. Missing outcome cells were not imputed.

`phase1_blocked_split_redesign_20260529__same_budget_20_per_repo__seed_2026052902` coverage: 36/60 tasks have at least one completed paid outcome.
`phase1_blocked_split_redesign_20260529__expanded_30_per_repo__seed_2026052904` coverage: 56/90 tasks have at least one completed paid outcome.

## Why It Matters

These diagnostics did not choose or tune the split. Adapter-level results remain separate, pooled diagnostics are secondary, and predictive validity remains false.

## What Action It Suggests Next

Use this only as a retrospective sanity check. Any new evidence for the redesigned split would require a later preregistered paid validation runbook.
