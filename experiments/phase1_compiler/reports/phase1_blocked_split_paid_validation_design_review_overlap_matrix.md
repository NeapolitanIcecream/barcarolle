# Blocked Split Paid Outcome Overlap

Status: `complete`.

## What Happened

The frozen blocked split was compared against committed three-repo paid score tables at the task/adapter-cell level.

## Why It Matters

Known outcomes cover only part of the selected blocked split. Missing outcomes are not imputed, so any complete selected score table needs new paid cells or a full rerun.

## What Action It Suggests Next

Use the exact missing-cell manifest to compare retrospective-only, missing-cell supplement, and full-rerun protocols.

## Summary

### `same_budget_20_per_repo`

- Selected tasks: `60`.
- Selected cells: `120`.
- Known tasks with at least one paid outcome: `36`.
- Tasks with no completed paid outcome: `24`.
- Known cells by adapter: `{'codex_workspace': 36, 'kilo_workspace': 36}`.
- Missing cells by adapter: `{'codex_workspace': 24, 'kilo_workspace': 24}`.
- Reused score-table sources: `10`.

### `expanded_30_per_repo`

- Selected tasks: `90`.
- Selected cells: `180`.
- Known tasks with at least one paid outcome: `56`.
- Tasks with no completed paid outcome: `34`.
- Known cells by adapter: `{'codex_workspace': 56, 'kilo_workspace': 56}`.
- Missing cells by adapter: `{'codex_workspace': 34, 'kilo_workspace': 34}`.
- Reused score-table sources: `10`.

## Boundary

No paid calls were made. Existing outcomes are used only for exploratory overlap accounting and provenance, not to alter the selected split or claim predictive validity.
