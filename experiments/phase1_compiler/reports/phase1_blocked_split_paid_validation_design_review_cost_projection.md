# Blocked Split Validation Cost Projection

Status: `complete`.

## What Happened

Projected cost and latency were computed from committed prior token-cost summaries and usage-ledger-derived baselines. No provider billing API was called.

## Why It Matters

The missing-cell supplement is cheaper than full rerun, but all cost numbers remain token-estimated rather than exact provider-billed cost.

## What Action It Suggests Next

If the coordinator authorizes paid work, use adapter-specific new-cell counts and keep provider-billed cost status explicit.

## Options

### Option A: `retrospective_only_no_new_paid_cells`

- New paid cells: `0`.
- Reused cells: `72`.
- Token-estimated new cost: `$0.0`.
- Token-estimated historical reused cost: `$30.760416`.
- Provider-billed exact cost available: `False`.

### Option B: `same_budget_missing_cell_supplement`

- New paid cells: `48`.
- Reused cells: `72`.
- Token-estimated new cost: `$20.506944`.
- Token-estimated historical reused cost: `$30.760416`.
- Provider-billed exact cost available: `False`.

### Option C: `same_budget_full_rerun`

- New paid cells: `120`.
- Reused cells: `0`.
- Token-estimated new cost: `$51.26736`.
- Token-estimated historical reused cost: `$0.0`.
- Provider-billed exact cost available: `False`.

### Option D: `expanded_full_rerun`

- New paid cells: `180`.
- Reused cells: `0`.
- Token-estimated new cost: `$76.90104`.
- Token-estimated historical reused cost: `$0.0`.
- Provider-billed exact cost available: `False`.

### Option E: `stop_for_source_repair_or_third_repo_replacement`

- New paid cells: `0`.
- Reused cells: `0`.
- Token-estimated new cost: `$0.0`.
- Token-estimated historical reused cost: `$0.0`.
- Provider-billed exact cost available: `False`.

## Reconciliation

- Same-budget full rerun difference from blocked projection: `$0.0`.
- Expanded full rerun difference from blocked projection: `$0.0`.
