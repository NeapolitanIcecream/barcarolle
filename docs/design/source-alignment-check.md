# Design Consistency Check

Status: draft, 2026-07-14.

## Vocabulary

The design uses the active core terms:

- `Task`
- `Check`
- `Workspace`
- `Result`
- `Selector`
- `RollingOrigin`
- `Task Pool`
- `Benchmark Selection`
- `Agent Results`

These terms are the module and record vocabulary used across the package.

## System Boundary

Barcarolle is a target-repository benchmark compiler. It does not become an
Agent harness, public leaderboard, tuning framework, or general workflow
runtime.

The tested Agent owns its model, harness, prompts, tools, retrieval, edit loop,
retry policy, public-test policy, and runtime budget. Barcarolle owns task
validation, fresh solver/verifier workspace separation, hidden-oracle verification,
normalized result storage, rolling-origin selection, and report traceability.

## Asset Decoupling

The design keeps these assets independent:

- `Task Pool`
- `Benchmark Selection`
- `Agent Results`

Cached Agent-task-check results can be reused only when the exact
`ResultCacheIdentity` matches. Selectors consume result tables and feature
snapshots, not solver workspaces, verifier workspaces, hidden check material, or
unsanitized Agent run logs.

## Selector Boundary

The Selection module keeps these constraints:

- one selected `Task + Check` set and optional weight vector for all Agents in
  a comparison;
- metadata-only and pre-origin-result features with recorded `observed_at`
  timestamps and leakage classes;
- selector inputs that bind origin, task pool, feature snapshot, Agent set,
  budget, and pre-origin result view;
- rolling-origin policy with as-of cutoff, cluster constraints,
  eligibility mode, and holdout overlap rules;
- benchmark selections frozen before future outcomes are opened;
- a mean-MAE meta-controller over complete, comparable rows from earlier
  rolling origins; result availability is enforced when those rows are built,
  not reconsidered by the controller.

## Cache And Scoring Boundary

Result reuse depends on exact `ResultCacheIdentity`, not broad runtime names.
Pricing is stored on `Result` and excluded from execution identity, so a price
change cannot trigger another Agent run.
Result matrices carry cell-level Agent/Task/Check mappings, completeness,
exclusion, abstention, join policy, and denominator metadata so Agent
comparisons cannot silently reuse stale or partial cells.

Metrics must reference the evaluation cell set, selected-benchmark matrix,
future-holdout matrix, metric config, join policy, and denominator policy.
Frozen selector inputs, selections, cell sets, matrices, and metrics reference
Result records by ID and digest. Evidence-bearing records are append-only.

Rolling-origin evaluation freezes `Task + Check` refs before future outcomes
are opened, and records source, task material, check material, certification,
and result availability timestamps separately.

## Reporting Boundary

Reports summarize existing evidence. They do not create new evidence, inspect
hidden oracle material, or reinterpret missing, invalid, excluded, or abstained
cells after scoring.
