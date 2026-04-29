# Process

status: working
updated: 2026-04-29T12:59:00+08:00

## Summary

First bounded pilot execution worker is starting after the coordinator recorded
an explicit execution-start decision for exactly one ACUT/task primary attempt:
`cheap-generic-swe` on `click__rbench__001`, attempt 1.

This worker is authorized to run only this single patch-generation attempt
through the reviewed `acut_patch_adapter.py` plus custom
`barcarolle_patch_command.py` path. Broad ACUT execution and any second
model-call attempt remain disallowed.

## Owned Paths

- `experiments/core_narrative/results/cost_ledger.jsonl`
- `experiments/core_narrative/results/raw/pilot_001__cheap-generic-swe__click__rbench__001__attempt1/**`
- `experiments/core_narrative/results/normalized/pilot_001__cheap-generic-swe__click__rbench__001__attempt1.json`
- `.codex-workflows/core-narrative-experiment/workers/first-execution-pilot/**`

## Branch / Worktree

- Branch: `codex/core-exp-first-execution-pilot`
- Worktree: `/Users/chenmohan/gits/barcarolle-wt-first-execution-pilot`

## Attempt Scope

- run_id: `pilot_001__cheap-generic-swe__click__rbench__001__attempt1`
- acut_id: `cheap-generic-swe`
- task_id: `click__rbench__001`
- split: `rbench`
- attempt: `1`
- projected_cost_usd: `3.00`
- broad_execution: false

## Current Blockers

None. Execution is in progress for the single authorized attempt.

## Handoff

Coordinator should read this `process.md` on the next heartbeat. Do not inspect
`cli.log`. Do not start a second attempt or broad execution until this worker
delivers and a focused result review passes.
