# Barcarolle

Barcarolle helps you build target-repository benchmarks for coding-agent
evaluation. It keeps the benchmark boundary auditable: the Agent works in a
solver workspace, hidden checks run in a separate verifier workspace, results
are stored with exact cache identity, and reports are built from frozen
evidence.

Use it when you need to ask whether a benchmark selection predicts later Agent
performance on the same repository.

## What Barcarolle Does

1. Builds or imports a `Task + Check` pool for a target repository.
2. Runs configured Agents in clean solver workspaces and captures their final
   diffs.
3. Replays each diff in a verifier workspace with private oracle material.
4. Stores normalized `Result` records and reuses cached results only when the
   task, check, Agent, workspace, runtime, and scoring identity all match.
5. Selects and evaluates benchmarks under rolling-origin splits so selectors
   cannot use future results or future-derived features.
6. Writes reports from frozen selections, result matrices, metrics, and result
   records.

Barcarolle does not choose the Agent model, prompts, tools, edit loop, retry
policy, or runtime budget. Those stay inside the Agent harness you configure.

## Install and Test

Barcarolle uses Python 3.11+ and `uv`.

```bash
uv sync
uv run pytest
```

Run a focused test file while reading an area:

```bash
uv run pytest tests/test_runner.py
uv run pytest tests/test_result_store.py
```

## Current Interface

Barcarolle is currently a Python library. It does not expose a CLI yet.

Start from `barcarolle.runner` for end-to-end orchestration:

- `build_task_pool(...)` creates a frozen task pool.
- `fill_results(...)` runs missing Agent/task/check cells and stores results.
- `select_benchmark(...)` freezes a benchmark selection for an origin time.
- `evaluate_selector(...)` evaluates selections across rolling-origin splits.
- `write_report(...)` writes report artifacts from existing records.

The tests in `tests/test_runner.py` provide executable examples of these entry
points.

## Project Layout

- `barcarolle/`: Python package.
- `tests/`: executable examples and regression tests.
- `docs/design/`: detailed behavior and data contracts.
- `archive/`: historical material; skip it for normal use.
