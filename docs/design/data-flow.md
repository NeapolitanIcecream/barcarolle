# Barcarolle Data Flow

Status: current, 2026-07-23.

## Overview

The system is organized around durable records. `Task Pool`, `Benchmark
Selection`, and `Agent Results` are independent assets that can be joined by
stable identifiers.

Runner owns the cross-module command flow. The other modules own the records
and computations named below.

```text
target repository + task source
  -> Task Pool
  -> Workspace execution
  -> Agent Results

Task Pool + pre-origin Agent Results + origin + budget + Selector
  -> RollingOrigin -> FeatureSnapshot -> SelectorInput
  -> frozen Benchmark Selection
  -> Evaluation Cell Set -> Result Matrices -> Metrics
  -> Report
```

## Flow 1: Build A Task Pool

Input:

- stable target `repository_id` and local `repository_path`;
- task generator or user import;
- per-candidate check command, hidden material path, and reference patch;
- Workspace, Runtime, and certification config.

Steps:

1. Task Pool filters sanitized source events or imports candidates.
2. The filter/importer emits a `CandidateBatch` with `TaskCandidate` records
   and any pre-certification excluded SourceEvents.
3. Runner binds the local repository and each candidate's check command and
   hidden material.
4. Execution-based task validation runs `repeat_count` fresh base/patched
   pairs, requiring every base Check to fail and every reference-patched Check
   to pass.
5. Task Pool joins the batch with all certification decisions into the
   sanitized SourceEvent frame and constructs the frozen pool record without
   writing files.
6. Runner publishes the exact SourceEvent, accepted Task, accepted Check, and
   ordered sanitized certification sequences referenced and digested by that
   pool record.

Output:

- frozen `Task Pool`.
- accepted Task/Check record references and digests, rejection summaries,
  certification evidence ref/digest, and source-event record ref/digest.

Runner entrypoint:

- `build_task_pool`

Downstream:

- Workspace receives Task and Check records to run Agents.
- Selection receives Task and Check metadata, not certification outcomes or
  raw validation artifacts.
- Reporting receives accepted and rejected counts.

## Flow 2: Run Agents And Store Results

Input:

- `Task`;
- `Check`;
- Agent config;
- workspace config;
- runtime config.

Steps:

1. Runner computes and validates every requested exact cell identity.
2. Workspace preflights all repository, Check, timeout, harness, and paid
   endpoint bindings for the batch before the first Agent invocation.
3. Workspace creates a solver workspace at the task base commit and writes
   solver-visible task material.
4. Workspace revalidates the Agent harness and endpoint proof immediately
   before invocation, then captures bounded output and the final diff.
5. Workspace creates a verifier workspace and applies the diff.
6. Verification injects hidden material and executes the Check with bounded
   output and process-tree timeout cleanup.
7. Result Store writes a normalized `Result`.

Output:

- reusable `Result` with complete `ResultCacheIdentity`.

Runner entrypoint:

- `run_agents`

Downstream:

- Selection joins results with Task Pool records.
- Reporting summarizes outcome, cost, latency, and failure labels.

## Flow 3: Train A Selector

Input:

- deployment `RollingOrigin`;
- the common frozen `Task Pool` and its validated Task/Check records;
- exact prior training Origins, FeatureSnapshots, SelectorInputs, expert
  Selectors, frozen Selections, matrices, metrics, and bound Results;
- one concrete fitted family.

Steps:

1. Runner starts from explicit training Selection IDs and loads their exact
   persisted provenance and Result bindings plus the common validated Task Pool
   bundle; it does not discover a dataset.
2. Selection validates and replays every expert Selection, verifies pre-origin
   feature Results and selected/future matrices, requires one ordered full Agent
   identity binding across Origins, projects every training Result back to that
   binding, replays all Origins, Snapshot Task metadata, and Result Task/Check
   cache identities against the frozen pool, requires each bound Matrix cell's
   Result ID/digest, Agent/Task/Check, required identity, and outcome to match,
  including bound excluded cells, and recomputes MAE. Only genuinely unbound
  excluded or missing cells omit Result evidence. Matrix exclusion states must
  also derive from benchmark-invalid or agent-invalid Results, and one complete
  Matrix must match its declared join/denominator policy, including abstention
  and scoreability. The current fitter ranks expert evidence rather than
  consuming Task metadata values, but the evidence path is ready for a later
  feature-consuming model.
3. Selection requires training origins and future windows before the deployment
   cutoff. Strict prospective deployment also requires bound outcome Results to
   have been available strictly before that cutoff.
4. Selection fits the existing rule-mixture weights and returns one compact,
   directly executable `SelectorRecord`. Fixed rules use
   `build_rule_selector`; choosing evaluated Selectors is separate.

Output:

- `Selector`.

Runner entrypoint:

- `train_selector`

Downstream:

- Runner can use the Selector for production benchmark selection.
- Reporting can summarize training sources and selector version.

## Flow 4: Evaluate Selectors

Input:

- one or more specified `Selector` records;
- historical window;
- historical `Task Pool` subset allowed by the protocol;
- historical `Agent Results` allowed by the protocol;
- candidate Agent set;
- evaluation config containing ISO `origin_times` and a selection budget, plus
  a rolling-origin policy.

Steps:

0. The current Runner path accepts only `counterfactual_replay` with a
   predeclared future holdout. A strict-prospective Selection can be frozen by
   `select_benchmark`, but its later traffic must come from separately linked
   post-origin Task Pool or source-frame evidence. The evaluator fails before
   writes or Agent calls until that linkage exists.
1. Runner loads historical results from Result Store.
2. Runner parses the strictly increasing UTC instants in
   `evaluation_config.origin_times` and asks Selection to build a
   `RollingOriginRecord` for each timestamp under the rolling-origin policy.
   Each future arrival window ends at the next origin; the last ends at the
   historical window boundary. Task-material arrival determines cohort
   membership. Label availability determines mature versus censored refs at the
   as-of cutoff or fixed maturity-lag cutoff. Refs arriving before the
   historical window start are not included in that origin's history.
3. Selection builds and lints leakage-safe feature snapshots, replays their
   Task Pool-backed `task_count` and `task_stratum` provenance, then builds
   Selector inputs that bind the complete pre-origin Result view.
4. Runner computes every Selector/origin Selection and persists all Selectors,
   Origins, FeatureSnapshots, SelectorInputs, and frozen Selections before
   future resolution.
5. Runner validates every Result bound by a reusable CellSet in one batch read,
   then deduplicates the first-occurrence union of all pending selected and
   mature future exact cells and resolves, executes, and reprices that union
   once. Censored refs remain provenance only.
6. Runner reconstructs each CellSet in its own requested ref order and scores
   separate matrices and metrics. Partial execution preserves appended Results;
   valid persisted CellSets are reused on resume.

Output:

- persisted Selector, RollingOrigin, FeatureSnapshot, and SelectorInput
  provenance;
- frozen `Benchmark Selection` records;
- evaluation cell sets and selected/future Result matrices;
- rolling-origin metrics.

Runner entrypoint:

- `evaluate_selectors` (`evaluate_selector` is its singleton wrapper)

Downstream:

- Maintainers use metrics to compare selector versions.
- Reporting validates and recomputes the complete chain, then derives the
  predeclared paired MAE summary and interval status. Invalid provenance yields
  no aggregate summary.

## Flow 5: Select A Benchmark

Input:

- frozen origin time;
- pre-origin `Task Pool` subset;
- pre-origin `Agent Results` allowed by the selected protocol;
- candidate Agent set;
- budget and constraints;
- selector version.

Steps:

1. Runner loads pre-origin results from Result Store.
2. Selection builds the history pool from a `RollingOriginPolicy`.
3. Selection builds and lints a feature snapshot and replays Task metadata
   values, observation times, and source digests against the frozen Origin and
   Task Pool records.
4. Selection builds leakage-safe Selector input.
5. Selector chooses common `Task + Check` refs and optional weights.
6. Selection records a frozen `Benchmark Selection`.

For strict-prospective use, the Origin also freezes a future window while
keeping future refs empty. A later Task Pool is a separate immutable snapshot;
it never extends or replaces the Selection pool.

Output:

- `Benchmark Selection`.

Runner entrypoint:

- `select_benchmark`

Downstream:

- Runner can ask Result Store which selected Agent-task-check cells are missing.
- Reporting shows why tasks were selected.
- RollingOrigin evaluation joins selected results with future results.
- Future outcomes must remain unopened until the `Benchmark Selection` has been
  frozen.

## Flow 6: Score A Selection

Input:

- the Selection `Task Pool` and, for strict-prospective evaluation, one later
  `Task Pool`;
- `Agent Results`;
- `Benchmark Selection`;
- future holdout window.

Steps:

1. For strict-prospective evidence, Runner reloads Selector, Origin,
   FeatureSnapshot, SelectorInput, and Selection and proves deterministic
   inference reproduces the frozen Selection. It then resolves every
   pre-origin Result ID/digest frozen by SelectorInput and replays Origin scope
   plus Feature provenance and the cache-identity Agent projection before
   reading either Task Pool.
2. Runner validates the selection-time pool, replays the Origin, and checks
   every pre-origin Result's Task/Check cache identity. Selection then replays
   exact `task_count` and `task_stratum` provenance from the validated
   TaskRecords. Only then does Runner validate that the later pool keeps the
   same source behavior and
   certification config, covers the planned source window, postdates Selection,
   and reaches the label-maturity cutoff. It replays mature and censored future
   refs without changing the Origin.
3. Runner prepares selected-benchmark Agent-task-check cells and
   future-holdout Agent-task-check cells under the same result identity and
   denominator policy.
4. Result Store builds cell-level mappings from Agent-task-check cells to
   required identities, results, exclusions, or missing states.
5. Result Store builds one selected-benchmark matrix and one future-holdout
   matrix with explicit matrix roles.
6. Compute selected-benchmark pass-rate estimates per Agent.
7. Compute future holdout pass rates per Agent.
8. Compute MAE as the primary prediction metric, plus pairwise gap MAE, rank
   agreement, recommendation regret, invalid rate, and coverage.
9. Store metrics keyed by origin, selector version, cell-set digest,
   selected/future matrix digests, join policy, and denominator policy.

Output:

- evaluation cell set;
- selected-benchmark and future-holdout result matrices;
- rolling-origin metrics.

Runner entrypoint:

- `score_selection` for a predeclared counterfactual cohort;
- `evaluate_prospective_selection` for a persisted Selection plus later pool.

Downstream:

- Maintainers use metrics to evaluate Selector algorithms and decide what to
  develop next.
- Reporting distinguishes evidence from claim.

## Design Consistency Check

- Supports result cache reuse and lazy Agent execution.
- Treats paid Agent results as reusable assets.
- Ensures selectors consume result tables, not workspaces or unsanitized Agent
  logs.
- Preserves separation between solving and verification.
- Makes supported Selector claims replayable from the full persisted evidence
  chain and labels strict-prospective and counterfactual-replay claims
  separately.
