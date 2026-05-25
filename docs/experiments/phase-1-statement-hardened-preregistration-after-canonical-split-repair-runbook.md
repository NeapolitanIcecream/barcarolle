# Phase 1 Statement-Hardened Preregistration After Canonical Split Repair Runbook

Status: draft only, not executed.

Use this runbook after the canonical split repair has produced reviewed and deterministic-QA-passed statements for all 16 canonical tasks.

## Required Inputs

- `experiments/phase1_compiler/results/phase1_canonical_split_map.json`
- `experiments/phase1_compiler/results/phase1_canonical_selected_inventory.json`
- `experiments/phase1_compiler/results/phase1_canonical_statement_reviews.json`
- `experiments/phase1_compiler/results/phase1_canonical_statement_qa.json`
- `experiments/phase1_compiler/results/phase1_canonical_statement_screen.json`
- `experiments/phase1_compiler/results/phase1_canonical_split_repair_decision.json`

## Scope

- Freeze a new statement-hardened preregistration from the canonical split screen.
- Use canonical split labels only.
- Keep paid ACUT validation disabled until the user explicitly approves a paid run.
- Do not rerun old scoreable cells or rewrite historical score tables.

## Current Decision

- Primary decision: `canonical_split_repair_complete_retry_preregistration`.
- Selected counts by repo/split: `{'attrs/B_eval': 4, 'attrs/H_future': 4, 'boltons/B_eval': 4, 'boltons/H_future': 4}`.
- Next paid validation status: `requires_explicit_user_approval`.

## Disallowed Claims

- `predictive_validity_established`
- `paid_validation_completed`
- `old_paid_result_repaired`
