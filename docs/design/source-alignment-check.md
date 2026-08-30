# Design Consistency Check

Status: current implementation consistency check, 2026-08-30.

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

These terms are the implemented module and record vocabulary used across the
package. Research prose additionally uses evaluator, task generator, agent
version, evaluator feedback policy, optimization round, and meta-evaluation as
ordinary domain terms. They are not implemented core records or modules.

The first principle is to provide reliable evaluation methods for
self-evolving agents. Repository-level coding agents are the first concrete
domain. In public prose, a self-evolving agent means an agent that retains
behavior-changing model, harness, prompt, memory, skill, tool, or other
persistent-state updates across tasks. Subject evolution is the core context;
evaluator coevolution is an optional method.

## System Boundary

Barcarolle develops reliable evaluation methods for self-evolving agents. It
does not become an agent harness, public leaderboard, or general workflow
runtime. The external agent optimizer remains outside its execution ownership,
while its version, parent links, behavior-changing persistent state, candidate
archive, budget, and evaluator feedback must enter Barcarolle's evidence
boundary for repeated-optimization claims.

The tested agent owns its model, harness, prompts, memory, skills, tools,
retrieval, edit loop, retry policy, public-test policy, persistent state, and
runtime budget. The current Barcarolle runtime owns task validation, fresh
solver/verifier workspace separation, hidden-check verification, normalized
result storage, rolling-origin selection, and report traceability. The built-in
Workspace path assumes a cooperative agent and does not claim host-level
resource isolation.

## Research Information Boundaries

The design keeps three research flows distinct:

1. agent optimization receives only the declared evaluator feedback and emits
   versioned agent candidates, lineage, persistent-state changes, and budget
   evidence;
2. optional evaluator updating receives only permitted development evidence,
   consumed prospective cohorts, and red-team evidence and follows a frozen
   update rule;
3. independent prospective evaluation freezes the complete evaluation method,
   applicable agent and evaluator versions, budget, and predictions before
   opening future real-world tasks and outcomes from an independent outcome
   authority.

Prospective evidence does not enter either of the first two flows until the
corresponding scoring decision is complete. Once an opened cohort affects agent
optimization, evaluator updating, attack design, threshold choice, or method
selection, it becomes development evidence and cannot remain an independent
test.

Reports keep four evaluation and method-selection stages separate and apply
them in order:

- evidence validity is a hard prerequisite;
- absolute error limits require both primary errors, coverage, and uncertainty to
  meet predeclared deployment requirements;
- degradation under optimization measures both errors relative to the same evaluation
  policy's `b=0` baseline;
- method comparison chooses among methods under matched conditions.

A reliability claim must pass the first two stages and the third when it covers
evaluator-guided optimization. The fourth stage cannot repair an earlier
failure.
Neither a stable but inaccurate method nor a method that only beats an
inaccurate comparator supports a reliability claim.

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
  fixed across `RollingOrigin` records, validates the common `Task Pool`,
  `RollingOrigin`, and `FeatureSnapshot` records,
  and binds every pre-origin and outcome Result cache projection to the frozen
  Agent/Task/Check records;
- one Records-owned ResultCell binding contract across Result Store, Runner,
  Selection, and Reporting, including exact Result ID/digest and outcome;
- one Result Store-owned Matrix state derivation: only benchmark-invalid and
  agent-invalid Result evidence can justify exclusions, and the complete Matrix
  must replay under one declared join/denominator policy, including abstention
  and scoreability;
- current pass-rate-mean-MAE Selector choice over complete, comparable metrics from
  earlier rolling origins; this is an implementation limitation, not the
  research metric hierarchy. Pass-rate-difference MAE must become an equally
  prominent claim and
  fitting input before the static two-objective path is complete.

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

The current static metric chain does not implement complete reliability-claim evidence
or an agent-optimization trajectory. New closed-loop evidence must bind agent
lineage and persistent state, optimizer and feedback identity, budget
checkpoints, evaluator versions, prospective-cohort status, and outcome
authority without weakening the existing exact Result and Matrix bindings.

Rolling-origin evaluation freezes `Task + Check` refs before future outcomes
are opened. Historical `known_at` uses only source, task-material, and
check-material availability. Certification evidence is stored separately and
does not move that historical availability time.

## Reporting Boundary

Reports summarize existing evidence. They do not create new evidence, inspect
hidden oracle material, or reinterpret missing, invalid, excluded, or abstained
cells after scoring. Selector-performance claims require the exact `Agent`,
`Result`, `RollingOrigin`, `FeatureSnapshot`, `SelectorInput`,
`BenchmarkSelection`, `EvaluationCellSet`, `ResultMatrix`, and `Metric`
bindings; reports use mode-specific claim names so counterfactual replay is not
presented as prospective evidence.

For self-evolving-agent claims, reports must additionally distinguish evidence
validity, absolute error limits, degradation under optimization, and method
comparison, and must state the tested lineage, optimizer, feedback, budget,
threat model, prospective cohort, coverage, uncertainty, and reference
standard. An integrity violation invalidates the capability result rather than
becoming an ordinary low score.

## Paid Execution Boundary

Runner validates the complete missing-cell plan before the first Agent call.
Workspace then revalidates repository and Check material, positive timeouts,
harness command and content, and the `OPENAI_BASE_URL`/`OPENAI_API_KEY` endpoint
proof immediately before execution. Offline Agents use the literal `offline`
network policy. Credentials and raw endpoint URLs are not stored in evidence
records, and cache-only or repricing operations do not require them.
