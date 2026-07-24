# Barcarolle Internal Process Notes

Last updated: 2026-07-24.

This file records the active research direction, paid-call boundary, claim
boundary, and cross-session handoff. Intended behavior lives in `docs/design/`;
completed findings and historical evidence live in
`docs/research-improvement-backlog.md`.

## Current State

The active direction is predictive validity plus the Task-supply,
Result-admission, and Generator-validity boundaries needed to extend it.

- Stages 0–2 and Stage 3's offline contracts are implemented: evidence/runtime/
  storage reliability, final-form Selection, arrival and maturity, censored
  events, dependency evidence, repeated schedules, prospective replay, paired
  metrics, and uncertainty.
- The Pylint campaign has frozen-input `authorize`, no-call `preflight`, and
  one-cell `run-next`; no authority ledger or paid call was created in the
  current research. The required `main-quality` status runs locked install,
  Ruff, Pyright standard mode, and the full suite.
- Built-in or user Generators emit one strict prepared-candidate package for
  Barcarolle certification/publication. User-maintained Task Pools instead open
  read-only and validate in place. External Results remain separate and are
  normalized into the local Result Store for exact-identity reuse.
- Current SourceEvents prove complete processing of the events supplied to one
  Task Pool build, not complete observation of a real-work population.
  `future_pass_rate_mae` is Generator-conditional later-Task/Check prediction
  error, not an end-to-end benchmark-quality score.

Selector/campaign infrastructure is at its stop line. Next implement only the
narrow supply/admission and Generator/frame evidence contracts. Do not add a
validation or experiment framework, model service, Feature Store, workflow
engine, plugin host/registry, simulator platform, or distributed scheduler.

## Active Decisions

1. Wait for the model server and API before the next evidence-producing run.
2. Downstream modules consume a complete `TaskPoolBundle`, never Generator
   objects/plugins. Preserve separate `build` and read-only `open` operations.
   Keep Task Pool and Result storage independent; import external Results with
   authority/effective availability, freeze and replay Selection from one
   cutoff-safe snapshot, then query the full cache and execute selected misses.
3. A Task-Pool-bound generation manifest independently digests Generator
   behavior, stable source protocol, exact observed frame, run authority, and
   outputs. A frame records scope/query or dataset revision, window,
   sampling/deduplication, event inventory, receipts, and blind spots; every
   frame event receives a Generator disposition. This proves only the declared
   observable frame, never all real work.
4. Use the claim ladder `bundle integrity -> generated-pool prospective
   prediction -> same-frame Generator bridge -> prospective field calibration`.
   Each rung requires separate evidence. Rename/narrow `task_pool_coverage` to
   bundle integrity and keep MAE conditional on the Generator/Check process.
5. Implement explicit built-in adapters: static SWE-bench first, then
   SWE-smith; state whether each imports a dataset, wraps official code, or
   reimplements a paradigm. Keep one repository per pool. Compare native
   Generators with same-frame classic baselines at both task and upstream-event
   level. Managed LLM generation stays behind paid-call authority; external
   Generators hand over data, not executable trust.
6. SWE-Together/SWE-Interact need a different episode boundary, but one logged
   path does not identify user responses to a new Agent. Require a held-out
   human branch-policy pilot against deterministic disclosure and generic role
   play before adding a narrow episode contract. Unsupported interactive shapes
   fail rather than degrade to static tasks.
7. Report Generators separately by default. Mixing needs common event identity,
   overlap/positivity, target event weights, semantic/Check calibration, and a
   prospective outer holdout. Field outcomes stay an external vector unless
   stakeholder weights are predeclared.
8. Keep ALG-001–004 offline until outer-origin comparison; ALG-005 needs a
   measured resource estimand and ALG-006 more independent clusters/replicates.
   Continue RI-034 only for reproduced failures or measured maintenance cost.
   Cremona remains calibrated routing evidence, not a baseline or CI gate.

## Next Campaign

The concrete procedure is in `docs/pylint-swe-bench-reasoning-pilot.md`. Keep
Agent, Runtime, schedule, Task Pool, repository, Check, dependency, and
verifier-image inputs frozen under one ignored campaign directory. Freeze the
schedule before opening Results; then use explicit `authorize`, no-call
`preflight`, and one `run-next`. Re-run preflight before every later cell and
never add an automatic paid loop. Stop if endpoint, authority, schedule,
pricing, model window, evidence, or runtime budget cannot be proven.

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

Every paid Agent or managed-generator binding must prove the exact endpoint,
command/implementation content, requested model, immutable snapshot or bounded
campaign scope, and runtime identity. Its authority binds the frozen schedule
or generation plan, Task Pool or source inputs, relevant configs, endpoint and
model identity, total and per-call cost limits, call cap, and pricing basis.
Raw URLs and credentials are not persisted.

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
- The current `task_pool_coverage` claim proves supplied-bundle integrity only.
  It does not prove source-adapter capture, observed-frame representativeness,
  or real-work external validity.
- Generated-pool MAE, certification yield, behavioral similarity, greater
  interaction difficulty, and cross-simulator agreement cannot establish a
  real-work claim. Interactive simulators are benchmark-side treatments, not
  neutral measurement devices.
- Strict-prospective claims require the original frozen Selection plus a later
  immutable Task Pool covering the planned future window. Never rewrite the
  original Origin.
- Imported Results prove external producer attestation, not Barcarolle-managed
  execution. They become historical Selector evidence only under their recorded
  effective-availability policy.
- Reports support claims only after replaying exact Task, Check, Agent, Result,
  Selection, matrix, metric, source, and timing evidence. Missing evidence must
  produce an unsupported claim, not an inferred value.

## Storage And Schema

Core readers accept only the latest schema. Preserve valuable older paid
Results with a small, non-destructive one-off migration; do not add runtime
compatibility branches. A migrated Result is not exact-cache reusable unless
its execution identity is still proven.

Task Pools publish immutable bundles. Result Store owns durable append, locking,
exact reuse, repricing views, conservative tail recovery, and normalized
external-Result admission. An imported source stays read-only; conflicting
executions under one exact cache identity are not auto-reused. Raw prompts,
completions, trajectories, field observations, workspaces, credentials, and
large outputs stay below ignored paths. A small Task-Pool-bound generation
manifest separately digests Generator behavior, source protocol, exact observed
frame, run authority, and outputs; adapter-specific details stay in sidecars.

## Deferred Scale Work

- RI-021 checkout caching: reopen only after warm/cold small, medium, and large
  repository measurements show checkout plus cleanup above 5 percent of total
  scoreable-cell wall time or p95 blocks target throughput.
- RI-033 bounded parallelism: reopen when a planned serial run exceeds one hour
  or the API has explicit controlled concurrency. Use a standard-library worker
  pool, one Result writer, and `max_concurrency=1` by default.

## Handoff

Before the endpoint arrives, implement the Task-supply work in this order:
complete-bundle preflight for every evidence-producing Runner path; read-only
Task Pool open/use; external Result provenance/import/conflict handling and the
Selection-before-cache phase contract; strict prepared-candidate package plus
local material bindings; Generator behavior/source protocol/observed-frame
provenance and the bundle-integrity claim correction; then one static SWE-bench
built-in with full funnel and derivation evidence. Use SWE-smith as the second
contract test before extracting shared adapter machinery. Defer LLM execution
and large-pool certification until their concrete adapter and authority exist.
Defer interactive episode execution until both a concrete adapter and the human
branch-policy gate exist; field calibration remains a separate prospective
study.

When the endpoint arrives, prepare the frozen Pylint campaign inputs, create
explicit authority, run no-call preflight, and advance one cell at a time.
