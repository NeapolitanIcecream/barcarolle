# Barcarolle

Barcarolle is a repo-specific benchmark compiler for predictive coding-agent evaluation.

It helps you build auditable, time-split benchmarks around a target repository
so you can evaluate coding agents on repository-specific work.

The package is alpha. Read the
[implementation status](docs/implementation-status.md) before using a run as
benchmark or research evidence.

## What It Does

Barcarolle keeps the benchmark boundary outside the tested Agent:

- accepts direct candidates, a prepared package from an arbitrary Generator, or
  an existing user-maintained `Task + Check` pool, with execution-based task
  validation where Barcarolle builds the pool;
- runs Agents in fresh solver workspaces;
- replays captured diffs in verifier workspaces with private check material;
- stores managed or explicitly admitted external `Result` records with exact
  cache identity and availability provenance;
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
The Pylint replicate campaign's explicit `authorize`, `preflight`, and
single-cell execution commands are documented in
[`docs/pylint-swe-bench-reasoning-pilot.md`](docs/pylint-swe-bench-reasoning-pilot.md).
The rolling-origin estimands, censoring, weighting, pairing, and uncertainty
rules are fixed in [`docs/statistical-protocol.md`](docs/statistical-protocol.md).

Validate an existing immutable Task Pool bundle without running its Generator,
recertifying, or republishing it:

```bash
uv run barcarolle task-pool validate path/to/task-pool.jsonl
```

## Install And Test

Barcarolle uses Python 3.11+, `uv`, and `zsh` for the Codex harness contract
tests.

```bash
uv sync
uv run pytest
uv run ruff check src tests examples scripts
uv run pyright
```

Pull requests and pushes to `main` run the locked install, Ruff, Pyright in
standard mode over `src`, `examples`, and `scripts`, and the full test suite in
the `quality` workflow. Target-repository hidden-check fixtures are excluded
from static analysis. Formatting is not yet a repository-wide gate because the
current tree has pre-existing format drift.

Run a focused test file while working in one area:

```bash
uv run pytest tests/test_runner.py
uv run pytest tests/test_result_store.py
```

## Offline Report Command

`barcarolle report` rebuilds a report from existing latest-schema JSONL
records. It does not run Agents or make paid calls.

```bash
uv run barcarolle report path/to/report-config.json
```

Paths are resolved relative to the config file:

```json
{
  "task_pool": "records/task_pool.jsonl",
  "future_task_pools": "records/future-task-pools.jsonl",
  "agents": "records/agents.jsonl",
  "selectors": "records/selectors.jsonl",
  "origins": "records/origins.jsonl",
  "feature_snapshots": "records/feature-snapshots.jsonl",
  "selector_inputs": "records/selector-inputs.jsonl",
  "selections": "records/selections.jsonl",
  "results": "records/results.jsonl",
  "evaluation_cell_sets": "records/evaluation_cell_sets.jsonl",
  "result_matrices": "records/result_matrices.jsonl",
  "metrics": "records/metrics.jsonl",
  "artifact_root": ".",
  "output_dir": "report"
}
```

The task-pool file must contain one `TaskPoolRecord`. The optional
`future_task_pools` file may contain zero or more later snapshots used by
strict-prospective CellSets. `task_pool` and `output_dir` are required; omit a
record file when that evidence is absent.
Included record files contain zero or more records of the type named by the
key. Task Pool artifact refs resolve under `artifact_root`, which defaults to
the config-file directory. Bundle internal consistency is unsupported when
referenced Task, SourceEvent, Check, or certification-evidence files are
missing or do not match their stored digests; this claim does not imply source
or population coverage. The command writes `report.md` and `report.json` under
`output_dir`. A supported Selector-performance claim additionally requires the
Selector, Origin, FeatureSnapshot, SelectorInput, Agent, Result, Selection,
cell-set, matrix, and metric files shown above; omitting them produces an
explicit unsupported claim rather than inferring missing provenance.

## Python Interface

The Python API runs benchmark workflows. Start with these modules:

- `barcarolle.task_pool` validates prepared candidates and complete bundles,
  then builds and freezes candidate `Task + Check` pools.
- `barcarolle.workspace` creates solver and verifier workspaces.
- `barcarolle.result_store` stores reusable managed/external `Result` records,
  detects ambiguous executions, and builds result matrices.
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
- `docs/research-improvement-backlog.md`: living research findings, priorities,
  validation criteria, and deferred algorithm ideas.
- `docs/design/evidence-storage-and-recovery.md`: artifact roots, Task Pool
  publication, exact Result reuse, pricing views, and interruption recovery.
- `docs/design/`: detailed behavior and data-contract reference.
