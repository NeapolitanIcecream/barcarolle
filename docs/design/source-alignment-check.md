# Design Consistency Check

Status: current, 2026-07-23.

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
The built-in Workspace path assumes a cooperative Agent and does not claim
host-level resource isolation.

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
- a FeatureConfig whose non-empty unique supported names are normalized to
  builder order and whose leakage classes are derived by Selection rather than
  declared independently by callers;
- selector inputs that bind origin, task pool, feature snapshot, ordered Agent
  IDs and full-record digests, a positive selection limit and its derived
  budget digest, and the pre-origin result view;
- rolling-origin policy with arrival cohorts, label-maturity/censoring rules,
  dependency-cluster constraints, exact
  `strict_prospective` or `counterfactual_replay` eligibility semantics, and
  enforced holdout overlap rules;
- benchmark selections frozen before future outcomes are opened;
- strict-prospective CellSets that bind a separately frozen later Task Pool,
  while counterfactual CellSets bind the Origin pool; Reporting replays the
  later source window, maturity, censoring, and dependency policy;
- a persisted, self-digested
  Selector→RollingOrigin→FeatureSnapshot→SelectorInput→Benchmark Selection
  chain that can be deterministically replayed;
- ordered resolution of every pre-origin Result ID/digest frozen by
  SelectorInput, with Origin Agent/history/cutoff scope and Feature provenance
  replayed before strict-prospective supply reads;
- exact replay of Task Pool-backed FeatureRecords: `task_count` binds the
  Origin and pool, while `task_stratum` binds complete history coverage, Task
  value, known-at time, and canonical Task digest before future-pool reads;
- Records-owned replay of Result cache identity against the frozen Agent before
  supply reads and against the validated selection-time Task/Check records
  before future-pool reads or Agent execution;
- learned-Selector training that holds the ordered full AgentRecord identity
  fixed across Origins, validates the common Task Pool/Origin/Snapshot records,
  and binds every pre-origin and outcome Result cache projection to the frozen
  Agent/Task/Check records;
- one Records-owned ResultCell binding contract across Result Store, Runner,
  Selection, and Reporting, including exact Result ID/digest and outcome;
- one Result Store-owned Matrix state derivation: only benchmark-invalid and
  agent-invalid Result evidence can justify exclusions, and the complete Matrix
  must replay under one declared join/denominator policy, including abstention
  and scoreability;
- mean-MAE Selector choice over complete, comparable metrics from earlier
  rolling origins; the choice does not reinterpret whether a recorded MAE is
  available.

## Cache And Scoring Boundary

Result reuse depends on exact `ResultCacheIdentity`, not broad runtime names.
The identity binds the requested model plus either a proven snapshot or one
bounded campaign scope, so a moving alias cannot cross campaigns unchanged.
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
are opened. Historical `known_at` uses only source, task-material, and
check-material availability. Certification evidence is stored separately and
does not move that historical availability time.

## Reporting Boundary

Reports summarize existing evidence. They do not create new evidence, inspect
hidden oracle material, or reinterpret missing, invalid, excluded, or abstained
cells after scoring. Selector-performance claims require the exact Agent,
Result, origin, snapshot, input, selection, cell-set, matrix, and metric
bindings; reports use mode-specific claim names so counterfactual replay is not
presented as prospective evidence.

## Paid Execution Boundary

Runner validates the complete missing-cell plan before the first Agent call.
Workspace then revalidates repository and Check material, positive timeouts,
harness command and content, and the `OPENAI_BASE_URL`/`OPENAI_API_KEY` endpoint
proof immediately before execution. Offline Agents use the literal `offline`
network policy. Credentials and raw endpoint URLs are not stored in evidence
records, and cache-only or repricing operations do not require them.
