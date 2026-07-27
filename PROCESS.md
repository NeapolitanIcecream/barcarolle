# Barcarolle Cross-Session Handoff

Last updated: 2026-07-27.

This file records only current direction and stop conditions. Intended behavior
lives in `docs/design/`; findings and future work live in
`docs/research-improvement-backlog.md`.

## Stable boundaries

- Keep the eight-module graph: Records, Task Pool, Verification, Workspace,
  Result Store, Selection, Reporting, and Runner.
- Generators end at one strict prepared-candidate package. Barcarolle owns
  certification and immutable Task Pool publication. A user-maintained complete
  Task Pool opens read-only.
- Task Pool and Result storage remain independent. Reuse is by exact
  Task/Check/Agent/Workspace/Runtime identity, not Task Pool ID.
- Scoreable execution uses a clean solver workspace, captures its diff, and
  replays it in a fresh verifier workspace where private oracle material is
  first introduced.
- Preserve rolling-origin, FeatureSnapshot, SelectorInput, fitted Selector,
  lazy-fill, and prospective replay contracts. YAGNI applies to machinery, not
  to this known final data flow.
- Prefer direct records and functions. Do not add a Generator registry, plugin
  host, model service, workflow DAG, Feature Store, distributed scheduler, or
  simulator platform without a concrete implementation that requires it.

## Current evidence

The completed model/Agent study is documented at
`docs/experiments/2026-07-25-model-agent-study.md`. Its 75-Task SymPy panel
supports Terra as the source-conditional operational default and mini as a
research challenger. No more paid calls are authorized by that contract.

The zero-call Selector follow-up is documented at
`docs/experiments/2026-07-27-offline-selector-study.md`.

- Historical Task source times do not backdate the Checks certified in 2026.
  All twelve planned historical core Origins have zero mature history and
  future refs. The existing Results do not establish counterfactual or
  strict-prospective rolling-origin error.
- A separately labeled historical Task-order diagnostic rejected the current
  duration-stratum ALG-002 configuration. Do not tune it on the same outcomes.
- ALG-001 and ALG-004 retained coverage in every eligible outer block. ALG-003
  was seed-unstable. None is a Runner default.
- Coverage is a future hypothesis only. Its exploratory difference from the
  five-seed random-bank mean was `-0.0383`; repeat, dependency, and block-size
  diagnostics justify prospective testing, not deployment.

## Next reopening point

Do not spend more money or add learned Selector machinery against the current
75 outcomes. The next decisive Selector study requires real later Task Pool
snapshots and mature Results.

Preregister coverage versus the frozen five-seed random-bank mean with at least
25 independent, non-overlapping five-Task Origins, two frozen Agents,
dependency/repository reporting, and a preselected repeat subset. The current
planning estimate is 140 unique Tasks, 280 Agent calls, `$86.47` median and
`$187.21` sum-of-Agent-p90 cost. These numbers are neither authorization nor a
provider quote.

Before another certification run of comparable size, add the already-justified
single-writer candidate checkpoint keyed by exact package, candidate,
Workspace, Runtime, Check, mode, and normalized outcome. Narrow the Pylint
Generator behavior digest before its next campaign. Concrete Generator
development remains deferred until a source and any required API are available.

Reopen checkout caching only when checkout plus cleanup exceeds 5% of scoreable
cell wall time or p95 blocks target throughput. Reopen bounded Agent parallelism
only with unambiguous per-call attribution, one Result writer, and explicit
concurrency authority.

Before commits, run focused tests, the full suite, Ruff, Pyright, and
`git diff --check`. Keep credentials, prompts, completions, transcripts,
workspaces, verifier output, and provider payloads under ignored outputs.
