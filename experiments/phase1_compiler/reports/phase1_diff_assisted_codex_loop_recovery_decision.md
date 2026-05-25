# Phase 1 Diff-Assisted Codex Loop Recovery Decision

Generated: `2026-05-25T05:10:11Z`.

## Decision

- Primary decision: `partial_recovery_mine_targeted_replacement_supply`.
- Real Codex generator/reviewer loop completed: `True`.
- Generator/reviewer used local Codex Subscription: `True`.
- LLM API endpoint used for generator/reviewer: `False`.
- Old candidate pool recovered: `partial`.
- Replacement supply still needed: `True`.
- Next runbook: `docs/experiments/phase-1-targeted-statement-hardened-replacement-supply-runbook.md`.

## Basis

- Candidate count: `22`.
- Real reviewer counts: `{'pass': 22}`.
- Deterministic QA counts: `{'pass': 22}`.
- Eligible before regeneration: `4`.
- Eligible after Codex loop regeneration: `22`.
- Selected counts by repo/split: `{'attrs/B_eval': 4, 'attrs/H_future': 4, 'boltons/B_eval': 4, 'boltons/H_future': 0}`.
- Remaining missing supply: `{'boltons/H_future': ['needed 4, found 0 eligible Codex-reviewed regenerated statements without using paid outcomes']}`.

## Boundary

This decision is based on a real external Codex CLI generator/reviewer loop plus deterministic QA guardrails. It does not claim predictive validity, paid validation, repaired historical paid results, or scoreable results from generated statements.
