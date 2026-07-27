# Barcarolle Cross-Session Handoff

Last updated: 2026-07-27.

This file records current direction and reopening conditions. Intended behavior
lives in `docs/design/`; findings live in
`docs/research-improvement-backlog.md`.

## Stable boundaries

- Keep the eight modules: Records, Task Pool, Verification, Workspace, Result
  Store, Selection, Reporting, and Runner.
- Generators end at one strict prepared-candidate package. Barcarolle owns
  certification and immutable Task Pool publication. A user-maintained complete
  Task Pool opens read-only.
- Algorithm-visible Task/Check availability, dependency cluster, and sampling
  stratum may come from a user or adapter. Their derivation and evidence class
  must be explicit. A counterfactual scenario gets a new immutable Task Pool;
  it never overwrites or relabels its source pool.
- Task Pool and Result storage remain independent. Reuse is by exact
  Task/Check/Agent/Workspace/Runtime identity, not Task Pool ID.
- Strict-prospective Result inputs obey physical availability. Counterfactual
  inputs obey mature history membership plus exact identity. FeatureSnapshot
  and SelectorInput freeze the view before lazy testing.
- Preserve the rolling-origin, fitted Selector, lazy-fill, and prospective
  replay data flow. Use direct records and functions. Do not add a Generator
  registry, plugin host, Feature Store, workflow DAG, model service,
  distributed scheduler, or simulator platform without a concrete caller.

## Current evidence

The 75-Task SymPy model/Agent study supports Terra as its source-conditional
operational default and mini as a research challenger. Its paid authority is
closed.

The zero-call Selector study now has two evidence views:

- The published 2026 Check timestamps are the source-observation negative
  control. All 12 historical Origins are fully censored.
- The user-configured `label_at_task_arrival` scenario produces 12 public
  Origins, 72 Selections, 144 matrices, and 72 MAE metrics. All 150 base Results
  match exact Task/Check/Agent/cache identity and are reused without calls.
- Coverage MAE is `0.1833`, versus random seed 5 at `0.2250` and recency at
  `0.2042`. This supports selection within this counterfactual scenario.
- The predeclared weighted-stratified rule remains worse than coverage by
  `0.0536`. ALG-003 is seed-unstable; ALG-001 and ALG-004 retain coverage.
- Stable rule-mixture summation changes one benchmark membership and one MAE
  relative to the frozen transparent diagnostic. The disagreement is recorded.

No result establishes strict-prospective performance or promotes a Selector
into Runner defaults.

## Stop state and reopening work

Do not spend more money, tune against the same 75 outcomes, or add learned
Selector machinery. The current generic infrastructure is sufficient until a
concrete Task source, later Task Pool, or model API is available.

Highest-value reopening work:

1. Preregister coverage versus the frozen five-seed random-bank mean with at
   least 25 independent mature five-Task Origins, two frozen Agents,
   dependency/repository reporting, and a preselected repeat subset. The
   140-Task, 280-call estimates of `$86.47` median and `$187.21`
   sum-of-Agent-p90 are planning inputs, not authority or quotes.
2. Before another comparable certification run, add the single-writer
   candidate checkpoint from RI-160 and narrow the Pylint Generator behavior
   digest from RI-163.
3. Reopen learned Selectors only when enough mature Origins exist for a frozen
   outer evaluation. Reopen concrete Generator development only with its source
   and required API.
4. Reopen checkout caching when checkout plus cleanup exceeds 5% of scoreable
   cell time or p95 blocks throughput. Reopen bounded Agent parallelism only
   with exact per-call attribution, one Result writer, and explicit concurrency
   authority.

Before commits, run focused tests, the full suite, Ruff, Pyright, and
`git diff --check`. Keep credentials, raw prompts/completions, transcripts,
workspaces, verifier output, and provider payloads under ignored outputs.
