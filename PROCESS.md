# Barcarolle Cross-Session Handoff

Last updated: 2026-07-27. Design lives in `docs/design/`; findings live in
`docs/research-improvement-backlog.md`.

## Stable boundaries

- Keep Records, Task Pool, Verification, Workspace, Result Store, Selection,
  Reporting, and Runner.
- Generators end at one prepared package. Barcarolle certifies and publishes
  immutable Task Pools; user-maintained pools open read-only.
- Task Pool and Results stay independent. Reuse requires exact
  Task/Check/Agent/Workspace/Runtime identity.
- User- or adapter-derived availability, dependency cluster, and sampling
  stratum require explicit lineage and evidence class. A counterfactual is a
  new pool, never a relabeled source pool.
- Strict-prospective inputs obey physical availability. Counterfactual inputs
  obey mature history plus exact identity. FeatureSnapshot and SelectorInput
  freeze the pre-selection view before lazy testing.
- Preserve rolling-origin evaluation, fitted Selector provenance, lazy fill,
  and prospective replay with direct records/functions. Add no registry,
  Feature Store, workflow DAG, model service, distributed scheduler, or
  simulator platform without a concrete caller.

## Current evidence

The closed 75-Task SymPy study supports Terra as a source-conditional
operational default and mini as a challenger. The `label_at_task_arrival`
counterfactual reuses 150 exact Results across twelve Origins; the
source-observed Check view remains a censored negative control.

Current Selector decision:

- full eligible history is the no-Selection baseline at MAE `0.1933`;
- coverage scores `0.1833`; its `0.0100` gain and interval
  `[-0.0363, +0.0152]` miss promotion gates;
- exact-random expectation is `0.2150`; coverage beats `88.68%` by midrank,
  while `12.91%` is as good or better; Origins 6–9 fall below random midrank;
- support/oracle MAE is `0.0250`/`0.0375`, but exact-oracle random mass is only
  `2.38e-21`, so sparse pre-origin identification is the observed gap;
- the full-history contrast changes sign across future block sizes; removing
  repeated clusters gives a `0.0167` gain but still misses both gates;
- repeat views average a `0.0071` gain and never reach `0.02`; null controls
  remain suggestive and no fixed mechanism clears the gate;
- both Agents favor coverage by less than `0.02`; unseen-Agent transfer is
  untested.

No Selector is a Runner default and no result is strict-prospective evidence.

## Resource boundary

The USD 300 Agent-study authority is closed. This follow-up made zero
coding-Agent calls and one allowed required-endpoint embedding call
(`text-embedding-3-small`, 75 Tasks, 22,935 input tokens). Cost was not exposed
and is not imputed; raw embeddings remain ignored.

Coding-Agent availability is an external blocker, not an architectural signal.
Future evidence calls need new authority and `OPENAI_BASE_URL` plus
`OPENAI_API_KEY`.

## Reopening work

Do not spend more money or tune the same 75 outcomes.

1. Bring a later pool or second source with mature Origins. Preregister the
   candidate, full-history baseline, exact-random calibration, support/nulls,
   and dependency/repository aggregation before opening outcomes.
2. Plan at least 44 independent five-Task Origins for the primary `0.02`
   full-history effect; the earlier 25 applies only versus the random bank.
   This is conditional on the current panel.
3. On the second source, freeze ALG-007's `centroid_recent_15` primary and
   `facility_recent_15` control. Keep it offline; RI-189 gates core admission.
4. Split expanded reference/training and held-out Agent panels before unseen-
   Agent, difficulty, or learned-model claims. After that gate, ALG-008 may
   compare fixed-universe IRT compression offline, but it does not replace
   later-Origin future-Task evidence. Freeze RI-191's sparse-exact or
   precision-bounded random calibration after the panel size is concrete.
5. Before comparable certification, implement RI-160's checkpoint and narrow
   RI-163's Pylint Generator behavior digest.
6. Reopen checkout caching above its 5% threshold. Reopen Agent parallelism
   only with exact attribution, one writer, and authority.

Before commits, run focused/full tests, Ruff, Pyright, and `git diff --check`.
Keep secrets and raw model/workspace artifacts ignored.
