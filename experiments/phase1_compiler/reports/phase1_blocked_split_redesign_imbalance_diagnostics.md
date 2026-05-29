# Phase 1 Blocked Split Imbalance Diagnostics

## What Happened

`phase1_blocked_split_redesign_20260529__same_budget_20_per_repo__seed_2026052902` has feature imbalance score `74.0`, gate status `True`, and is fairer than the previous frozen paid split on the visible-feature score.
`phase1_blocked_split_redesign_20260529__expanded_30_per_repo__seed_2026052904` has feature imbalance score `100.0`, gate status `True`, and is fairer than the previous frozen paid split on the visible-feature score.
Previous frozen paid split visible-feature score: `174.0`.
No threshold relaxation was used; selected candidates passed the configured rare/unknown, editable-scope, time-bucket, task-family, statement-specificity, source-quality, and source-context gates.

## Why It Matters

B_eval and H_future are checked by repo on visible features only. This keeps attrs, boltons, and click from masking each other in a pooled average.

Click remains title-only minor risk: it is balanced within click, but it still has a weaker source-context claim boundary than attrs or boltons.

## What Action It Suggests Next

Use these diagnostics as the feature-balance gate for any later preregistration decision. Do not treat this as predictive validity evidence.
