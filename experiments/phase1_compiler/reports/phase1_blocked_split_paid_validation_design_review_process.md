# Phase 1 Blocked Split Paid Validation Design Review Process

## Step 0: Preflight And Dirty-Tree Audit

What happened: preflight passed for the no-paid design review. The current branch is `codex/restart-benchmark-compiler` at commit `f565a737bc3eb2d5b0162b75b2b246d4631773a6` (`Add blocked split paid design review runbook`).

Why it matters: this run can proceed using committed inputs only. It does not need ignored raw artifacts, new paid LLM calls, or new paid ACUT solver cells.

What action it suggests next: codify the exploratory claim policy, then compute exact overlap between the frozen blocked split and completed paid score tables.

## Dirty Tree

- Tracked changes present: `false`.
- Untracked files present: `true`.
- Untracked file count: `106`.
- Classification: the untracked paths are under `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/`, matching the known external-review bundle described by the runbook.
- Action: left unstaged.

## Input Availability

- Required committed path count checked: `26`.
- Missing required paths: `[]`.
- Completed paid score tables found: `10`.
- Completed paid cost summaries found: `10`.

## Boundary

This is an exploratory design review. Post-hoc blocked split design is acceptable for Phase 1 exploration only when labeled honestly. This run does not claim formal preregistration or predictive validity.

No paid calls are required or allowed for this run. Paid calls made by this run so far: `0`.

## Starting Point

- Blocked split decision label: `blocked_split_ready_with_click_minor_risk`.
- Blocked split paid calls made: `0`.
- Completed paid decision changed: `false`.
- Predictive validity established: `false`.

## Step 1: Codify Claim Policy

What happened: the claim policy was written in `experiments/phase1_compiler/configs/phase1_blocked_split_paid_validation_design_review.yaml`, `experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_claim_policy.json`, and `experiments/phase1_compiler/reports/phase1_blocked_split_paid_validation_design_review_claim_policy.md`.

Why it matters: this run now has a machine-readable guardrail that accepts post-hoc split design only for exploratory accounting and rejects formal preregistration or predictive-validity wording.

What action it suggests next: compute exact task/adapter overlap with completed score tables without imputing missing outcomes and without changing the selected split.
