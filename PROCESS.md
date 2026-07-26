# Barcarolle Cross-Session Handoff

Last updated: 2026-07-25.

This file records current direction and stop conditions only. Intended behavior
lives in `docs/design/`; findings and future work live in
`docs/research-improvement-backlog.md`.

## Stable boundaries

- Keep the eight-module graph: Records, Task Pool, Verification, Workspace,
  Result Store, Selection, Reporting, and Runner.
- Generators end at one strict prepared-candidate package. Barcarolle owns
  certification and immutable Task Pool publication; downstream modules consume
  a validated `TaskPoolBundle`, never a Generator object.
- User-maintained complete Task Pools open read-only. Opening does not generate,
  copy, recertify, or republish them.
- Task Pool and Result storage remain independent. Reuse is by exact
  Task/Check/Agent/Workspace/Runtime identity, not Task Pool ID.
- Scoreable execution uses a clean solver workspace, captures its diff, and
  applies that diff in a fresh verifier workspace where private oracle material
  is first introduced.
- Imported Results require an immutable source manifest and receipt.
  Producer-attested history stays explicit and cannot silently become
  Barcarolle-managed evidence.
- Preserve final-form rolling-origin, FeatureSnapshot, SelectorInput, fitted
  Selector, lazy-fill, and prospective replay contracts. Learned algorithms
  wait for prospective evidence; their infrastructure is not removed.
- Prefer direct records and functions. Do not add a Generator registry, plugin
  host, model service, workflow DAG, Feature Store, distributed scheduler, or
  simulator platform without a concrete implementation that needs it.

## Completed model/Agent study

The bounded USD 300 study is complete. Its frozen contract, five append-only
amendments, implementation, sanitized result snapshot, and report are under
`examples/model_agent_study/` and
`docs/experiments/2026-07-25-model-agent-study.md`.

- The main population is one certified 75-Task, 54-dependency-cluster SymPy
  SWE-bench Verified pool. The fixed harness is Codex CLI.
- Main executed all 238 frozen cells: 150 base cells and 88 repeat cells.
  There are 237 scoreable Results and one retained Terra availability failure
  on a preselected repeat-2 cell. No cell was retried or replaced.
- Terra-high passed 53/75 base Tasks; mini-high passed 46/75. The paired
  difference is +9.33 percentage points for Terra, with exact McNemar
  `p=0.0923` and dependency-cluster bootstrap 95% interval `[0, 18.18]`
  percentage points.
- Terra is the operational default for this source and harness: USD 25.036084
  for 119 calls and 87 end-to-end successes, versus mini's USD 71.414206 and
  73 successes. Mini remains a research challenger for future prospective
  routing work, not a default second execution.
- The observed run-level flip rate is 18/130 = 13.85%, with an
  Agent×Task-cluster bootstrap 95% interval `[6.15%, 21.88%]`. It crosses
  neither predeclared gate. Keep repeats in the experiment layer; do not change
  the core Result/controller schema or mandate replicate-aware execution yet.
- Sol matched Terra's 5/10 calibration outcomes at higher cost and is retired
  for this source. DeepSeek V4 Pro, Gemini 3.1 Pro, and Claude Sonnet 4.6 were
  incompatible with the fixed Codex Responses protocol; this is not a
  capability ranking.

The whole sprint made 291 benchmark calls. Exact attributed gateway cost was
USD 114.406752; conservative global balance movement was USD 117.795124; the
sum of conservative call estimates was USD 216.113623. No more paid calls are
authorized by this completed contract. Unused budget is intentional: there
were no remaining frozen cells, and outcome-driven expansion would weaken the
evidence.

## Claim boundary

- Results are retrospective and conditional on the frozen SymPy source,
  certified checks, Codex CLI harness, model configurations, and observed
  endpoint period. They are not a universal model leaderboard.
- Newly observed Results cannot be backdated into historical rolling origins
  and do not establish prospective Selector error.
- Task Pool consistency proves artifact/link consistency, not source-population
  coverage. Generator behavior, observed source frame, Check quality,
  generated-pool prediction, and field calibration remain separate evidence
  axes.
- A theoretical two-Agent oracle is not a deployable Selector. Do not claim
  routing benefit without a prospective policy and held-out origins.

## Next work and reopening triggers

1. Before certifying another pool of comparable size, add one single-writer
   certification checkpoint keyed by exact package, candidate, Workspace,
   Runtime, Check, mode, and normalized outcome. Replay every checkpoint before
   reuse; do not add a workflow engine.
2. Narrow the Pylint Generator behavior identity from the whole pilot file to
   an explicit behavior/version payload plus directly executed helper digests.
3. For model generalization, preregister a second repository/source replication.
   For Selector evidence, run a future authorized prospective rolling campaign.
4. Compare another coding-agent harness only after it has identity, isolation,
   oracle, and artifact parity with the Codex adapter.
5. Reopen checkout caching when checkout plus cleanup exceeds 5% of scoreable
   cell wall time or p95 blocks target throughput. Reopen bounded Agent
   parallelism only with unambiguous per-call attribution, one Result writer,
   and explicit concurrency authority.
6. Concrete Generator development remains outside the completed sprint.

Before commits, run scoped tests, Ruff, Pyright, and `git diff --check`. Raw
credentials, prompts, completions, transcripts, workspaces, verifier output,
and provider payloads remain under ignored outputs and must not be committed.
