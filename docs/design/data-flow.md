# Barcarolle Data Flow

Status: draft, 2026-06-27.

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
- certification config.

Steps:

1. Task Pool calls a generator or importer.
2. Generator emits candidate `Task + Check`.
3. Certification validates checkout, check executability, oracle stability,
   solver-visible boundary, and metadata.
4. Task Pool freezes accepted `Task + Check` records and rejection summaries.

Output:

- frozen `Task Pool`.

Runner entrypoint:

- `build_task_pool`

Downstream:

- Workspace receives Task and Check records to run Agents.
- Selection receives Task metadata and certification metadata.
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
8. Results computes cache identity and writes a normalized `Result`.

Output:

- reusable `Result`.

Runner entrypoint:

- `run_agents`

Downstream:

- Selection joins Results with Task Pool records.
- Reporting summarizes outcome, cost, latency, and failure labels.

## Flow 3: Train A Selector

Input:

- historical window;
- historical `Task Pool` subset allowed by the protocol;
- historical `Agent Results` allowed by the protocol;
- candidate Agent set;
- selector config.

Steps:

1. Runner loads historical results from Results.
2. Selection builds the origins required by the training config.
3. Selection trains or chooses a persistent `Selector`.

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

1. Runner loads historical results from Results.
2. Selection builds the origins required by the evaluation config.
3. Selection applies the specified Selector at each origin.
4. Selection returns metrics for those origins.

Output:

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

Steps:

1. Runner loads pre-origin results from Results.
2. Selection builds the history pool.
3. Selection builds leakage-safe Selector input.
4. Selector chooses common task IDs and optional weights.
5. Selection records a `Benchmark Selection`.

Output:

- `Benchmark Selection`.

Runner entrypoint:

- `select_benchmark`

Downstream:

- Runner can ask Results which selected Agent-task runs are missing.
- Reporting shows why tasks were selected.
- RollingOrigin evaluation joins selected results with future results.

## Flow 6: Score A Selection

Input:

- `Task Pool`;
- `Agent Results`;
- `Benchmark Selection`;
- future holdout window.

Steps:

1. Compute selected-benchmark pass-rate estimates per Agent.
2. Compute future holdout pass rates per Agent.
3. Compute prediction error, rank agreement, regret, invalid rate, cost, and
   coverage.
4. Store metrics keyed by origin, selector version, and result cache state.

Output:

- rolling-origin metrics.

Runner entrypoint:

- `score_selection`

Downstream:

- Selection uses metrics to evaluate or update Selectors.
- Reporting distinguishes evidence from claim.

## Flow 7: Update A Selector

Input:

- `Selector`;
- `Benchmark Selection`;
- metrics;
- feedback config.

Steps:

1. Runner passes recorded metrics to Selection.
2. Selection updates the persistent Selector or its trust metadata.

Output:

- updated `Selector`.

Runner entrypoint:

- `update_selector`

Downstream:

- Runner can use the updated Selector for later benchmark selection.

## Source Alignment Check

Aligned with the architecture:

- Supports result cache reuse and lazy Agent execution.
- Treats paid Agent results as reusable assets.
- Ensures selectors consume tables, not raw workspaces or transcripts.
- Preserves separation between solving and verification.
