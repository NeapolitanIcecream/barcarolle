# Phase 1 Targeted Statement-Hardened Replacement Supply Runbook

Status: follow-up runbook, 2026-05-25.

This runbook follows `docs/experiments/phase-1-diff-assisted-statement-regeneration-runbook.md`.
Diff-assisted regeneration partially recovered the old pool, but targeted replacement supply is still needed.

## Starting Point

- Review-passed regenerated statements: `19`.
- Deterministic QA-passed regenerated statements: `19`.
- Eligible before regeneration: `4`.
- Eligible after regeneration: `19`.
- Selected counts by repo/split: `{'attrs/B_eval': 4, 'attrs/H_future': 4, 'boltons/B_eval': 4, 'boltons/H_future': 0}`.
- Remaining missing supply: `{'boltons/H_future': ['needed 4, found 0 eligible regenerated statements without using paid outcomes']}`.

## Goal

Mine targeted replacement candidates only for the remaining missing repo/split supply, prioritizing `boltons/H_future`.
Do not discard the regenerated statements that already passed review and deterministic QA.

## Boundaries

- Paid ACUT calls remain disabled.
- Do not rerun old scoreable cells.
- Do not rewrite historical score tables.
- Do not use historical paid outcomes for candidate selection.
- Keep generated statements and review verdicts as sidecar artifacts until a later preregistration freezes a release.
- Do not claim predictive validity or paid validation from this runbook.

## Required Output

Add or update targeted replacement-supply configs, tooling, results, and reports under `experiments/phase1_compiler/`.
The final decision should say whether the remaining `boltons/H_future` hole is filled enough to run a new statement-hardened preregistration after regeneration.

## Verification

Run the scoped Phase 1 compiler tests for statement quality, clean supply mining, and preregistration screening, then run `git diff --check`.
