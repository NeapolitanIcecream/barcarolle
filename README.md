# Barcarolle

Barcarolle's first principle is to provide reliable evaluation methods for
self-evolving agents. Repository-level coding agents are the first concrete
domain.

A self-evolving agent retains behavior-changing updates across tasks. Those
updates may change its model, harness, persistent prompts, memory, skills,
tools, or other persistent state, whether the change is made autonomously or by
an external agent optimizer. Evaluating this changing subject is the core
research context.
Making the evaluator evolve too is one optional method, not part of the
definition.

The default target is **operational behavior**: what an exact agent version will
actually do under a declared deployment-like harness and runtime policy.
Performance under a separate capability-elicitation protocol is a different
claim. Changing the persistent agent configuration or its generation, tool, or
runtime policy creates a new agent version; task inputs and temporary evaluation
cues allowed by a frozen policy are recorded as run contexts for the same version. The
research design requires evidence about frozen snapshots, parent-to-child
changes, and complete agent lineages rather than only the final winner; the
current implementation does not yet capture those lineages.

Reliability is always bounded by a declared task population, outcome
definition, agent lineage and optimizer, feedback interface, optimization
budget, threat model, time horizon, and decision. It requires valid independent
evidence, adequate accuracy, and continued accuracy while the evaluator is used
for optimization. It never means universal or permanent resistance to Goodhart
effects.

Within that mission, the three primary empirical objectives are:

1. minimize pass-rate mean absolute error (MAE) on future real-world tasks;
2. minimize pass-rate-difference MAE between agents on those tasks;
3. minimize the increase in both errors as the predeclared budget for repeated
   evaluator-guided optimization grows.

The first two are separate primary metrics, and the third evaluates their
retention under optimization. Evaluation and method selection proceed in four
stages, in order:

- **Evidence validity** asks whether the future tasks, outcomes, and information
  boundaries support the claim at all. Invalid or leaked prospective evidence,
  or evidence whose outcomes affected its own selection, invalidates the claim
  rather than merely worsening a metric.
- **Absolute error limits** ask whether both errors meet predeclared limits
  derived from deployment needs, with adequate coverage and resolved
  uncertainty.
- **Degradation under optimization** asks how both errors change from the same
  evaluation method's no-optimization baseline (`b=0`) as the budget grows.
- **Method comparison** chooses among methods. Give pass-rate-difference MAE
  decision priority only if, at every predeclared evaluation budget, the
  method's pass-rate MAE is no more than a predeclared margin worse than a named
  comparator.

A reliability claim must pass evidence validity and absolute error limits, plus
degradation under optimization when the claim covers evaluator-guided
optimization. Method comparison cannot upgrade an inaccurate method: a method
can be stable but inaccurate, or beat an inaccurate comparator.

The current research plan is
[`docs/research-program.md`](docs/research-program.md). The package is alpha;
the current implementation provides fresh-workspace execution for cooperative
agents, hidden-check verification, result provenance, and part of the static
time-based evaluation path. It does not yet provide persistent-state lineages,
a closed-loop repeated-optimization protocol, complete reliability-claim
evidence, or the complete task-generation and optional evaluator-coevolution
methods. Read the [implementation status](docs/implementation-status.md) before
using a run as benchmark or research evidence.

## What The Current Implementation Does

Barcarolle keeps evaluation data and verification outside the tested agent:

- imports repository tasks, including prepared output from external task
  generators, and checks that each task and test setup executes as declared;
- runs agents in clean solver workspaces;
- applies the resulting patch in a separate verifier workspace and runs hidden
  checks;
- records outcomes, evidence timestamps, cost, latency, and failure labels with
  content-based identifiers that support exact replay and safe cache reuse;
- selects benchmark tasks under rolling-origin evaluation, meaning repeated
  backtests across successive time cutoffs;
- computes pass-rate MAE and aggregate pass-rate-difference MAE on held-out
  future task blocks;
- writes human- and machine-readable reports that distinguish supported from
  unsupported claims.

The research scope is broader than the current executable modules. Candidate
methods include task generation, task sampling and weighting, statistical
outcome models, calibration and abstention, evaluator feedback policies,
evaluator updating, adversarial stress testing of evaluators and
metrics, and agent–evaluator coevolution. Meta-evaluation means evaluating
evaluators and their metrics. Every method must ultimately be tested on future
real-world tasks from the target repositories that were not visible while
optimizing the agent or choosing the evaluator.

The tested agent controls its model, harness, prompts, memory, skills, tools,
retrieval, edit loop, retry policy, public-test policy, persistent state, and
runtime budget. The current Barcarolle runtime controls task collection,
fresh-workspace execution, hidden-check verification, result storage, task
selection, and reporting. The broader research design must additionally record agent
lineage and evaluator feedback and keep prospective evidence independent from
both agent optimization and optional evaluator updates.

The default execution model assumes a cooperative agent. Fresh solver and
verifier workspaces protect the benchmark boundary and hidden checks. A
host-isolation adapter is an optional capability for cooperative runs, but is
mandatory when the experiment deliberately includes test/scorer/grader/host
attacks or otherwise treats same-host jobs as mutually untrusted.

## Run The Minimal Demo

The demo runs offline with deterministic fixture agents. It does not call an
LLM API and does not require credentials.

```bash
uv run python examples/minimal/run_demo.py
```

It writes:

- `examples/minimal/out/report.md`
- `examples/minimal/out/report.json`

The output directory is ignored by Git, so you can rerun the demo without
creating tracked generated files.

For a target repository run with a real agent harness, see
[`docs/real-target-walkthrough.md`](docs/real-target-walkthrough.md).
For a concrete shell harness example, see
[`examples/harnesses/codex-cli/`](examples/harnesses/codex-cli/).

Validate an existing immutable task-pool bundle without rerunning its task
generator, recertifying, or republishing it:

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
records. It does not run agents or make paid calls.

```bash
uv run barcarolle report path/to/report-config.json
```

The smallest valid config names the task-pool file and output directory:

```json
{
  "task_pool": "records/task_pool.jsonl",
  "output_dir": "report"
}
```

Paths are resolved relative to the config file. Add optional evidence files only
when they exist; missing evidence produces an explicit unsupported claim rather
than an inferred result. The command writes `report.md` and `report.json` under
`output_dir`. The [Runner design reference](docs/design/modules/runner.md#barcarolle-report)
lists the full config and evidence requirements.

## Python Interface

The Python API runs benchmark workflows. Start with these modules:

- `barcarolle.task_pool` validates prepared tasks and their checks, then builds
  immutable task pools.
- `barcarolle.workspace` creates solver and verifier workspaces.
- `barcarolle.result_store` stores reusable results, detects ambiguous
  executions, and builds result matrices.
- `barcarolle.selection` builds time-based backtests, task selections, and the
  current static pass-rate and pass-rate-difference metrics. It is one
  implemented mechanism, not the boundary of the research program.
- `barcarolle.reporting` writes human-readable and machine-readable reports.
- `barcarolle.runner` coordinates the modules for end-to-end workflows.

The tests in `tests/` are executable examples of the current contracts.

## Project Layout

- `src/barcarolle/`: Python package.
- `tests/`: executable examples and regression tests.
- `examples/minimal/`: offline demo with deterministic fixture agents.
- `examples/harnesses/codex-cli/`: optional Codex CLI harness example.
- `examples/multi_repository_study/`: offline studies comparing task-sampling
  methods across repositories.
- `docs/research-program.md`: first principle, reliability contract, objectives,
  threat model, candidate methods, and experiment sequence.
- `docs/literature-review.md`: annotated literature map, evidence limits, and
  research questions that remain open.
- `docs/statistical-protocol.md`: target quantities, time splits, weighting,
  pairing, repeated optimization, and uncertainty rules.
- `docs/implementation-status.md`: implemented capabilities and known gaps.
- `docs/research-improvement-backlog.md`: current research decisions, evidence
  limits, active plan, and the link to the archived historical ledger.
- `docs/experiments/`: dated evidence records. Their fixed goals and metrics
  describe the experiments that were run, not the current project roadmap.
- `docs/experiments/2026-07-28-multi-repository-public-study.md`: completed
  zero-paid-call task-sampling study that informs the next experiment.
- `docs/design/evidence-storage-and-recovery.md`: artifact roots, task-pool
  publication, exact result reuse, pricing views, and interruption recovery.
- `docs/design/`: detailed behavior and data-contract reference.
