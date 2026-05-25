# Phase 1 Diff-Assisted Recovery Decision

Generated: `2026-05-25T02:52:58Z`.

## Decision

- Primary decision: `partial_recovery_mine_targeted_replacement_supply`.
- Old candidate pool recovered: `partial`.
- Replacement supply still needed: `True`.
- Next runbook: `docs/experiments/phase-1-targeted-statement-hardened-replacement-supply-runbook.md`.

## Basis

- Candidate count: `22`.
- Review pass/reject: `19` / `3`.
- Deterministic QA pass: `19`.
- Eligible before regeneration: `4`.
- Eligible after regeneration: `19`.
- Selected counts by repo/split: `{'attrs/B_eval': 4, 'attrs/H_future': 4, 'boltons/B_eval': 4, 'boltons/H_future': 0}`.
- Remaining missing supply: `{'boltons/H_future': ['needed 4, found 0 eligible regenerated statements without using paid outcomes']}`.

## Boundary

The decision is based on regenerated statement review and deterministic QA, not old truncation flags alone. It does not claim predictive validity, paid validation, repaired historical paid results, or scoreable results from generated statements. Future paid validation requires a new preregistration after targeted replacement supply closes the remaining repo/split hole.
