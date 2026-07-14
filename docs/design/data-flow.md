# Barcarolle Data Flow

Status: draft, 2026-07-14.

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

Task Pool + Agent Results + origin + budget
  -> Benchmark Selection
  -> RollingOrigin metrics
  -> Report
```

## Flow 1: Build A Task Pool

Input:

- target repository reference;
- task generator or user import;
- check construction method;
- task-validation config.

Steps:

1. Task Pool calls a generator or importer.
2. Generator emits candidate `Task + Check`.
3. Execution-based task validation confirms that the task check fails at the
   base commit and, when a reference patch exists, passes after that patch. It
   repeats checks when repeatability needs to be measured.
4. Task Pool freezes accepted `Task + Check` records and rejection summaries.

Output:

- frozen `Task Pool`.
- accepted Task/Check record references, rejection summaries, task-validation
  evidence, and source-event inventory digests.

Runner entrypoint:

- `build_task_pool`

Downstream:

- Workspace receives Task and Check records to run Agents.
- Selection receives Task metadata and task-validation metadata.
- Reporting receives accepted and rejected counts.

## Flow 2: Run Agents And Store Results

Input:

- `Task`;
- `Check`;
- Agent config;
- workspace config;
- runtime config.

Steps:

1. Workspace creates solver workspace at the task base commit.
2. Workspace writes solver-visible task material.
3. Workspace invokes the configured Agent.
4. Workspace captures the final diff.
5. Workspace creates verifier workspace.
6. Workspace applies the diff.
7. Verification injects hidden material and executes the Check.
8. Result Store computes cache identity and writes a normalized `Result`.

Output:

- reusable `Result` with complete `ResultCacheIdentity`.

Runner entrypoint:

- `run_agents`

Downstream:

- Selection joins results with Task Pool records.
- Reporting summarizes outcome, cost, latency, and failure labels.

## Flow 3: Train A Selector

Input:

- historical window;
- historical `Task Pool` subset allowed by the protocol;
- historical `Agent Results` allowed by the protocol;
- candidate Agent set;
- selector config.

Steps:

1. Runner builds the rolling-origin history boundary at the end of the window
   and loads only matching historical results from Result Store.
2. Selection validates the Task, Check, Agent, and time bindings and records
   the training-source digests.
3. Selection validates a supplied executable rule Selector or creates one from
   its persisted rule parameters. A learned method will define its own training
   data and fitted parameters with its concrete algorithm.

Output:

- `Selector`.

Runner entrypoint:

- `train_selector`

Downstream:

- Runner can use the Selector for production benchmark selection.
- Reporting can summarize training sources and selector version.

## Flow 4: Evaluate A Selector

Input:

- specified `Selector`;
- historical window;
- historical `Task Pool` subset allowed by the protocol;
- historical `Agent Results` allowed by the protocol;
- candidate Agent set;
- evaluation config.

Steps:

1. Runner loads historical results from Result Store.
2. Selection builds the origins required by the evaluation config and
   rolling-origin policy.
3. Selection builds leakage-safe feature snapshots.
4. Selection freezes `Benchmark Selection` records for those origins and does
   not score them.
5. Runner opens the needed result sets only after selections are frozen.
6. Runner prepares evaluation cells for the selected benchmark and future
   holdout under the same identity and denominator policy.
7. Runner returns metrics for those frozen selections.

Output:

- frozen `Benchmark Selection` records;
- rolling-origin metrics.

Runner entrypoint:

- `evaluate_selector`

Downstream:

- Maintainers use metrics to compare selector versions.
- Reporting can summarize Selector performance.

## Flow 5: Select A Benchmark

Input:

- frozen origin time;
- pre-origin `Task Pool` subset;
- pre-origin `Agent Results` allowed by the selected protocol;
- candidate Agent set;
- budget and constraints;
- selector version.
- selection config.

Steps:

1. Runner loads pre-origin results from Result Store.
2. Selection builds the history pool from a `RollingOriginPolicy`.
3. Selection builds and lints a feature snapshot.
4. Selection builds leakage-safe Selector input.
5. Selector chooses common `Task + Check` refs and optional weights.
6. Selection records a frozen `Benchmark Selection`.

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

- `Task Pool`;
- `Agent Results`;
- `Benchmark Selection`;
- future holdout window.

Steps:

1. Runner prepares selected-benchmark Agent-task-check cells and
   future-holdout Agent-task-check cells under the same result identity and
   denominator policy.
2. Result Store builds cell-level mappings from Agent-task-check cells to
   required identities, results, exclusions, or missing states.
3. Result Store builds one selected-benchmark matrix and one future-holdout
   matrix with explicit matrix roles.
4. Compute selected-benchmark pass-rate estimates per Agent.
5. Compute future holdout pass rates per Agent.
6. Compute MAE as the primary prediction metric, plus pairwise gap MAE, rank
   agreement, recommendation regret, invalid rate, and coverage.
7. Store metrics keyed by origin, selector version, cell-set digest,
   selected/future matrix digests, join policy, and denominator policy.

Output:

- evaluation cell set;
- selected-benchmark and future-holdout result matrices;
- rolling-origin metrics.

Runner entrypoint:

- `score_selection`

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
