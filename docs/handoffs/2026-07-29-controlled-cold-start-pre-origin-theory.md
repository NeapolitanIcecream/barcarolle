# Handoff: Controlled Cold-Start Pre-Origin Theory

Date: 2026-07-29.

## Goal

Design the next theory-driven Selection candidate from first principles.
Investigate which information available before an Origin can predict the Agent
pass-rate distribution of that repository's future Tasks.

This session is for research and design. It may run outcome-free feasibility
checks and create a frozen empirical plan. It must not tune an existing
algorithm, develop a concrete Generator, or claim that a Selector is valid.

## Product Boundary

Runtime remains:

`one repository -> one local Task Pool -> one Selection`

Multiple repositories are offline research or training evidence units. Their
Tasks never enter the target repository's runtime candidate set.

Preserve these contracts:

- the tested Agent owns its model, harness, prompts, tools, retries, and budget;
- Barcarolle owns Task supply, isolation, hidden verification, Result storage,
  rolling-origin Selection, and evidence reporting;
- full eligible target-repository history is the primary baseline;
- equal-budget random Selection calibrates sampling advantage but does not
  replace full history;
- pass-rate MAE is the outcome gate whenever matching Agent outcomes exist;
- AUC, Brier loss, embedding loss, and Task-mix loss are diagnostics;
- repositories are aggregated equally after configuration and Origin
  aggregation within each repository;
- runtime uses an absolute Selection budget and an explicit future
  `TimeRange`; H5 and H10 Task blocks are research controls.

Prefer one direct example-layer study over a registry, trainer service,
Feature Store, scheduler, generic source adapter, or multi-repository Runner.

## Cold-Start Order

1. Read `AGENTS.md`, `PROCESS.md`, this handoff, the system design, Selection
   contract, and statistical protocol.
2. Survey external research before reading prior algorithm implementations or
   detailed experiment reports. Cover software-work arrival, repository
   evolution, temporal distribution shift, benchmark selection, forecasting,
   and prequential evaluation.
3. Propose at least three mechanisms that use materially different pre-Origin
   observables. For each, state:
   - the causal or statistical reason the observable should predict future
     Agent pass rates;
   - its exact availability time;
   - how a user can import or derive it;
   - its dependence on the Task Generator;
   - its likely source bias and leakage paths;
   - the smallest outcome-free falsification test;
   - the independent evidence needed for a pass-rate MAE decision.
4. Freeze the initial mechanism inventory before reading the research ledger,
   prior candidate code, or detailed result reports.
5. Run a collision audit against the ledger. Remove mechanisms that are
   equivalent to a closed route, use unavailable future information, or need
   infrastructure without a concrete experiment.
6. Select at most one mechanism for a frozen theory contract. If none survives,
   record a stop decision.

The session may learn from prior failures during the collision audit. It must
not modify a candidate or threshold in response to opened outcome values.

## Evidence Boundary

SWE-bench Verified and Multi-SWE Agent outcomes are opened development
evidence. The six SWE-bench holdout Agents remain unread.

During this session:

- do not replay a new candidate on opened Agent outcomes;
- do not read the sealed holdout;
- do not make paid benchmark, Agent, or LLM calls;
- do not treat projected Task times as native prospective evidence;
- do not use future Task identities, patches, outcomes, or derived labels in
  Selection;
- do not pool Tasks from several repositories into a runtime Task Pool.

Allowed work:

- external literature and source research;
- inspection of pre-Origin fields and their availability semantics;
- synthetic tests and negative controls;
- outcome-free source and Origin feasibility;
- a frozen implementation and evaluation plan;
- identification of an independent development or confirmation boundary.

Any later outcome replay requires a separate, precommitted plan that binds the
information set, code, source, Origin schedule, budget, horizons, controls,
random protocol, pass-rate MAE gates, and stop conditions.

## Required Decision Contract

For the selected mechanism, specify:

- estimand: future pass-rate MAE for a held-out Agent configuration;
- candidate information available at each Origin;
- full-history baseline and equal-budget random calibration;
- H5 and H10 behavior, plus realized calendar spans;
- wide and deep repository frames;
- repository-first aggregation and uncertainty interval;
- Agent, model, harness, provider, language, and temporal-null checks when
  applicable;
- ablations that separate observable quality, forecast quality, and subset
  materialization;
- minimum effect, direction, replication, and falsification requirements;
- evidence class: projected counterfactual, strict historical, or prospective;
- exact condition that permits an opened-outcome replay, independent source,
  sealed holdout, or paid campaign.

Do not choose thresholds from observed candidate performance.

## Deliverables

1. A cited research memo with the initial mechanism inventory and collision
   audit.
2. One frozen theory contract and minimum decisive empirical plan, or a
   justified stop decision.
3. A table separating:
   - evidence already available without Agent outcomes;
   - evidence requiring existing opened outcomes;
   - evidence requiring a new source, prospective collection, or paid runs.
4. A short recommendation covering expected information gain, implementation
   cost, and the next authorized action.
5. Updates to the research ledger and `PROCESS.md` only if the route or
   reopening boundary changes.

Do not create core abstractions, a concrete Generator, or the next execution
runbook unless the user separately authorizes it.

## Starting Files

- `AGENTS.md`
- `PROCESS.md`
- `docs/design/system-design.md`
- `docs/design/modules/selection.md`
- `docs/statistical-protocol.md`
- `docs/research-improvement-backlog.md`, only after the initial mechanism
  inventory is frozen

Prior reports and implementations are collision-audit evidence, not a starting
template or golden interpretation.
