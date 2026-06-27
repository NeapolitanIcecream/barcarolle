# Barcarolle Data Flow

Status: draft, 2026-06-27.

## Overview

The system is organized around durable records. `Task Pool`, `Benchmark
Selection`, and `Agent Results` are independent assets that can be joined by
stable identifiers.

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

Downstream:

- Workspace receives Tasks and Checks to run Agents.
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
7. Checks inject hidden material and execute the Check.
8. Results computes cache identity and writes a normalized `Result`.

Output:

- reusable `Result`.

Downstream:

- Selection joins Results with Task Pool records.
- Reporting summarizes outcome, cost, latency, and failure labels.

## Flow 3: Select A Benchmark

Input:

- frozen origin time;
- pre-origin `Task Pool` subset;
- pre-origin `Agent Results` allowed by the selected protocol;
- candidate Agent set;
- budget and constraints;
- selector version.

Steps:

1. Selection builds the history pool.
2. Selection builds leakage-safe feature tables.
3. Selector chooses common task IDs and optional weights.
4. Selection records a `Benchmark Selection`.

Output:

- `Benchmark Selection`.

Downstream:

- Results identifies missing selected Agent-task runs.
- Reporting shows why tasks were selected.
- RollingOrigin evaluation joins selected results with future results.

## Flow 4: Evaluate With Rolling Origin

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

Downstream:

- Selection uses prior-origin metrics to compare selectors.
- Reporting distinguishes evidence from claim.

## Source Alignment Check

Aligned with the architecture:

- Supports result cache reuse and lazy Agent execution.
- Treats paid Agent results as reusable assets.
- Ensures selectors consume tables, not raw workspaces or transcripts.
- Preserves separation between solving and verification.
