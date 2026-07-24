# Barcarolle Internal Process Notes

Last updated: 2026-07-23.

This file records the active research direction, paid-call boundary, claim
boundary, and cross-session handoff. Intended behavior lives in `docs/design/`;
completed findings and historical evidence live in
`docs/research-improvement-backlog.md`.

## Current State

The active direction is predictive validity.

- Research Stages 0 through 2 are implemented: evidence integrity, runtime and
  storage reliability, and the final-form Selector boundary.
- Stage 3's offline contracts are implemented: arrival versus label maturity,
  censored SourceEvents, dependency evidence, repeated-cell scheduling,
  strict-prospective replay, paired metrics, and uncertainty rules.
- The Pylint replicate campaign has a concrete entry point. It loads frozen
  Agent, Runtime, schedule, Task Pool, and adapter evidence, then exposes only
  `authorize`, `preflight`, and one-cell `run-next` actions.
- The repository quality workflow performs a frozen install, Ruff, Pyright in
  standard mode over `src`, `examples`, and `scripts`, and the full suite.
  Target-repository hidden-check fixtures are excluded. Recursive JSON values
  and finite execution states now have static types; preparation failures
  carry stable labels rather than relying on message parsing.
- No campaign authority ledger or paid call was created during the current
  maintenance work.

Core infrastructure has reached its stop line. Do not add another validation
framework, experiment framework, model service, Feature Store, workflow engine,
plugin host, distributed scheduler, or generic Task Generator.

## Active Decisions

1. Wait for the model server and API before the next evidence-producing run.
2. Defer Task Pool expansion until one concrete Task Generator is selected.
   Some generators may be LLM-driven; deterministic importers have different
   source and certification requirements. Reuse the existing candidate,
   certification, SourceEvent, and immutable publication boundaries.
3. Keep ALG-001 through ALG-004 as offline analysis rules until outer-origin
   evidence compares them. Do not implement ALG-005 without a measured resource
   problem and a predeclared resource estimand. ALG-006 requires substantially
   more independent clusters and repeated cells.
4. Continue RI-034 refactoring only for a reproduced boundary failure or a
   measured maintenance bottleneck. Static hotspot counts alone do not justify
   another abstraction.
5. Use Cremona only as routing evidence. Its default scope is executable code
   under `src/barcarolle`, `examples`, and `scripts`; tests require a concrete
   test-maintenance question. Use 180 days of history, at least two shared
   commits, and ignore commits touching more than 25 in-scope files for
   coupling. That cutoff separates the two 28/35-file integration PRs from the
   15-file package/Selection migration. Do not create a baseline or CI gate
   until the repository has a stable comparison window and an agreed
   regression policy.

## Next Campaign

The concrete procedure is documented in
`docs/pylint-swe-bench-reasoning-pilot.md`.

Required frozen inputs under one ignored campaign directory:

- `records/agents.jsonl`;
- `records/runtime-config.jsonl`;
- `records/replicate-schedule.jsonl`;
- the prepared Pylint Task Pool and its local repository, Check, dependency,
  and verifier-image inputs.

Execution order:

1. Freeze Agent and Runtime records for the actual endpoint, model identity,
   campaign window, harness, and enforced runtime budget.
2. Freeze the replicate schedule before opening Result evidence.
3. Invoke the campaign CLI's `authorize` action with explicit approval time,
   scope, total budget, per-call limit, and pricing sources.
4. Inspect `preflight` output. It makes no Agent call and validates the pinned
   verifier images plus every remaining Runtime slot.
5. Invoke `run-next` once. Re-run `preflight` before each later cell. Do not add
   an automatic paid loop.

If the endpoint, authority, schedule, Result evidence, pricing, model window,
or runtime budget cannot be proven, stop before the Agent call.

## Paid-Call Boundary

Benchmark and evidence-producing calls must use only:

```text
OPENAI_BASE_URL
OPENAI_API_KEY
```

If either is missing, source `~/.zshrc` and check again. Do not use subscription
authentication, `LLM_BASE_URL`, `LLM_API_KEY`, OpenRouter variables, or
provider-specific credentials unless the user changes this rule. Repository
maintenance and PR review sessions use local Codex authentication instead.

Every paid Agent binding must prove the exact endpoint, command, each declared
harness path-to-content binding, requested model, immutable snapshot or bounded
campaign scope, and runtime identity. Raw URLs and credentials are not
persisted.

Every replicate campaign authority must bind:

- the frozen schedule, Task Pool, Agent set, Workspace and Runtime configs;
- endpoint digest and model identity;
- total estimated-cost budget and one conservative per-call limit;
- the schedule-derived call cap;
- pricing version, rates, sources, and accounting basis.

The remaining total must cover one full per-call limit before reservation. A
stopped reservation, a reservation without an exact Result, or a Result above a
declared limit forbids automatic retry. The ledger limits Barcarolle's authority;
the Agent harness or provider must enforce the actual per-call runtime budget.

The existing project authorization note allows up to USD 300 for the paired
rolling-origin work. Known priced spend is USD 2.95516590 across the Boltons
mechanism run and the two Pylint attempts; one interrupted Pylint cell retains
unknown cost. A new campaign still requires its own immutable authority ledger.

## Claim Boundary

- The Boltons run proves the paired-MAE mechanism on controlled tasks. It is not
  real-target predictive evidence.
- The ten-task Pylint pilot proves executable task certification and one
  observed low/high disagreement. One run per cell cannot separate treatment
  effect from run noise and cannot support a learned controller.
- ALG-001 through ALG-004 have executable offline rules but no outer-origin
  empirical win claim.
- Strict-prospective claims require the original frozen Selection plus a later
  immutable Task Pool covering the planned future window. Never rewrite the
  original Origin.
- Reports support claims only after replaying exact Task, Check, Agent, Result,
  Selection, matrix, metric, source, and timing evidence. Missing evidence must
  produce an unsupported claim, not an inferred value.

## Storage And Schema

Core readers accept only the latest schema. Preserve valuable older paid
Results with a small, non-destructive one-off migration; do not add runtime
compatibility branches. A migrated Result is not exact-cache reusable unless
its execution identity is still proven.

Task Pools publish immutable bundles. Result Store owns durable append, locking,
exact reuse, repricing views, and conservative tail recovery. Raw prompts,
completions, transcripts, workspaces, credentials, and large outputs stay below
ignored paths.

## Deferred Scale Work

- RI-021 checkout caching: reopen only after warm/cold small, medium, and large
  repository measurements show checkout plus cleanup above 5 percent of total
  scoreable-cell wall time or p95 blocks target throughput.
- RI-033 bounded parallelism: reopen when a planned serial run exceeds one hour
  or the API has explicit controlled concurrency. Use a standard-library worker
  pool, one Result writer, and `max_concurrency=1` by default.

## Handoff

After the quality workflow first succeeds on `main`, configure the repository
rule to require its `quality` check; that setting cannot be proven before the
workflow exists on the default branch. Before the endpoint arrives, further
development should start only after selecting a concrete Task Generator,
reproducing a new evidence-chain defect, or measuring a maintenance bottleneck.
When the endpoint arrives, prepare the frozen campaign inputs, create explicit
authority, run no-call preflight, and advance one cell at a time.
