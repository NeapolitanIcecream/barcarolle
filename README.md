# Barcarolle

Barcarolle is a repo-specific benchmark compiler for predictive coding-agent evaluation.

It helps you build auditable, time-split benchmarks around a target repository
so you can evaluate coding agents on repository-specific work.

The package is alpha. Read the
[implementation status](docs/implementation-status.md) before using a run as
benchmark or research evidence.

## What It Does

Barcarolle keeps the benchmark boundary outside the tested Agent:

- builds or imports a `Task + Check` pool with execution-based task validation;
- runs Agents in fresh solver workspaces;
- replays captured diffs in verifier workspaces with private check material;
- stores normalized `Result` records with exact cache identity;
- selects benchmark tasks under rolling-origin splits;
- writes reports from frozen records and result matrices.

The tested Agent owns its model, harness, prompts, tools, retrieval, edit loop,
retry policy, public-test policy, and runtime budget. Barcarolle owns the task
pool, workspace boundary, verification boundary, result storage, selection, and
reporting contracts.

The default execution model assumes a cooperative Agent. Fresh solver and
verifier workspaces protect the benchmark boundary and hidden checks; stronger
host isolation is an optional adapter for adversarial or shared-host runs.

## Run The Minimal Demo

The demo runs offline with deterministic fixture Agents. It does not call an
LLM API and does not require credentials.

```bash
uv run python examples/minimal/run_demo.py
```

It writes:

- `examples/minimal/out/report.md`
- `examples/minimal/out/report.json`

The output directory is ignored by Git, so you can rerun the demo without
creating tracked generated files.

For a target repository run with a real Agent harness, see
[`docs/real-target-walkthrough.md`](docs/real-target-walkthrough.md).
For a concrete shell harness example, see
[`examples/harnesses/codex-cli/`](examples/harnesses/codex-cli/).

## Install And Test

Barcarolle uses Python 3.11+ and `uv`.

```bash
uv sync
uv run pytest
uv run ruff check src tests examples scripts
uv run pyright
```

Run a focused test file while working in one area:

```bash
uv run pytest tests/test_runner.py
uv run pytest tests/test_result_store.py
```

## Python Interface

Barcarolle is currently a Python library. Start with these modules:

- `barcarolle.task_pool` builds and freezes candidate `Task + Check` pools.
- `barcarolle.workspace` creates solver and verifier workspaces.
- `barcarolle.result_store` stores reusable `Result` records and builds
  result matrices.
- `barcarolle.selection` builds rolling origins, selector inputs, benchmark
  selections, and metrics.
- `barcarolle.reporting` writes human-readable and machine-readable reports.
- `barcarolle.runner` coordinates the modules for end-to-end workflows.

The tests in `tests/` are executable examples of the current contracts.

## Project Layout

- `src/barcarolle/`: Python package.
- `tests/`: executable examples and regression tests.
- `examples/minimal/`: offline demo with deterministic fixture Agents.
- `examples/harnesses/codex-cli/`: optional Codex CLI harness example.
- `docs/design/`: detailed behavior and data-contract reference.
