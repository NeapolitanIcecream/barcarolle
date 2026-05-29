# Phase 1 Blocked Split Candidate Splits

## What Happened

Generated 200 deterministic candidate splits using seeded block randomization.
Budget summary: `{'same_budget_20_per_repo': {'candidate_count': 100, 'feasible_candidate_count': 100, 'minimum_feature_imbalance_score': 74.0, 'maximum_feature_imbalance_score': 164.0, 'infeasible_reason': None}, 'expanded_30_per_repo': {'candidate_count': 100, 'feasible_candidate_count': 100, 'minimum_feature_imbalance_score': 100.0, 'maximum_feature_imbalance_score': 170.0, 'infeasible_reason': None}}`.

Every candidate records selected task IDs, block assignments, B_eval/H_future task IDs, hard failures, feature imbalance score, and `outcome_fields_used_for_selection=false`.

## Why It Matters

The candidate set gives the selector many reproducible options without looking at pass/fail outcomes. Counts are exact by repo because every within-repo block contributes one task to each split.

## What Action It Suggests Next

Freeze the lowest feature-imbalance feasible candidate for the same-budget design as primary, and freeze the best expanded-budget candidate as secondary if feasible. Retrospective outcome diagnostics must wait until after that freeze.
