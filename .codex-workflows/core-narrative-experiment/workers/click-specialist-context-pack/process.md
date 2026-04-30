# Process

status: working
updated: 2026-04-30T09:00:48+08:00

## Summary

Focused worker is starting to generate, wire, and smoke-check a task-agnostic
Click specialist context pack before any specialist ACUT execution. The goal is
to strengthen the 2x2 specialist treatment without changing model tier,
runtime budget, retry policy, task slice, or broad execution authorization.

No ACUT attempt, retry, second attempt, specialist ACUT run, broad execution, or
large model-call batch is authorized.

## Owned Paths

- `experiments/core_narrative/context_packs/click_specialist/**`
- `experiments/core_narrative/tools/**` only for context-pack generation,
  loading, and prompt-injection support
- `experiments/core_narrative/configs/acuts/frontier-click-specialist.yaml`
- `experiments/core_narrative/configs/acuts/cheap-click-specialist.yaml`
- `experiments/core_narrative/configs/core_subset_run_manifest.yaml` only for
  context-pack status/metadata
- `experiments/core_narrative/reports/click_specialist_context_pack.md`
- `experiments/core_narrative/results/normalized/click_specialist_context_pack*.json`
- `experiments/core_narrative/results/raw/click_specialist_context_pack*/**`
- `experiments/core_narrative/results/cost_ledger.jsonl` only if a live
  BARCAROLLE model-call smoke is performed and ledgered
- `.codex-workflows/core-narrative-experiment/workers/click-specialist-context-pack/**`

## Branch / Worktree

- Branch: `codex/core-exp-click-specialist-context-pack`
- Worktree: `/Users/chenmohan/gits/barcarolle-wt-click-specialist-context-pack`

## Current Blockers

None recorded at worker start.

## Activity Log

- 2026-04-30T09:00:48+08:00: Worker scaffold created by coordinator. Start by
  reading the coordinator, active specialist ACUT manifests, reviewed Codex CLI
  harness adapter process/review summaries, and current context-pack-related
  run-manifest entries. Do not inspect any `cli.log` file.

## Changed Files

- pending

## Inspected Files

- pending

## Checks Run

- pending

## Live Call And Ledger

- live BARCAROLLE model call occurred: pending
- main experiment cost ledger appended: pending

## Handoff

When delivered, set `status: delivered` and record:

- generated context-pack artifact paths and hashes;
- evidence that artifacts are task-agnostic and generated before specialist
  ACUT execution;
- no-model prompt/context injection evidence proving Click-specialist ACUTs get
  the context pack and generic ACUTs do not;
- whether any live BARCAROLLE smoke occurred and, if so, the ledger run IDs and
  cumulative estimated cost without secrets, full URLs, hostnames, or IPs;
- checks run, changed files, and a concise reviewer handoff.
