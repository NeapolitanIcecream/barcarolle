# Statistical Protocol

Status: current offline contract, 2026-07-27. Empirical thresholds and model
claims remain pending until a larger authorized paired history exists.

This document fixes the statistical meanings used by rolling-origin evaluation.
It does not authorize paid execution and does not turn fixture results into
predictive evidence.

## Time And Cohorts

- Task arrival is `TaskRecord.task_material_available_at`.
- Label maturity is the later of task and Check material availability, subject
  to strict-prospective Task Pool availability.
- An origin's history cohort contains arrivals at or before its as-of cutoff.
  Its future cohort contains arrivals after that cutoff and inside the frozen
  future window.
- A fixed nonnegative maturity lag sets the future label cutoff to
  `future_window.end + maturity_lag_seconds`.
- Arrived refs without a mature label remain right-censored. They stay in the
  Origin and source-event evidence but do not enter training, Agent execution,
  denominators, or MAE.

`strict_prospective` uses what the live system could have known at the origin.
`counterfactual_replay` reconstructs historical material availability and may
predeclare the future cohort, but Runner still freezes every Selection before
opening future Result evidence. Reports must name the mode; the two are not
interchangeable claims.

The batch `evaluate_selectors` Runner supports counterfactual replay with a
predeclared future cohort. Strict-prospective evaluation is two-phase:
`select_benchmark` freezes an Origin with a declared future window but no future
refs, then `evaluate_prospective_selection` links a later immutable Task Pool to
the CellSet. Before supply reads, it reloads Selector, Origin, FeatureSnapshot,
SelectorInput, and Selection, replays deterministic inference, resolves every
frozen pre-origin Result ID/digest, and verifies its Agent/history/cutoff scope
and Feature provenance. It also proves the Result cache identity projects to
the frozen Agent before supply reads. After validating the selection-time pool
and replaying Origin, it verifies Task/Check cache identity and exact
`task_count`/`task_stratum` Feature provenance before opening the later pool.
That pool must preserve the bound repository, stable Generator behavior, source
protocol, and certification configuration; cover the complete declared future
interval; postdate the Selection; and be observed through the label-maturity
cutoff. It may contain only the later increment or a cumulative history.
Overlapping same-ID Task/Check records must remain unchanged. Run identity,
observed frame, and output inventory may change without changing Generator
behavior.
Reporting reloads both pools and recomputes mature and censored refs before
supporting a prospective claim. The original Origin and Task Pool are never
rewritten.

Result availability is also evidence. Barcarolle-managed Results use the
recorded local observation time. Imported Results default to an import-time
floor, preventing late evidence from entering an earlier Origin. An explicit
`producer_attested_historical_v1` policy may preserve the producer's source
timestamp, but reports label that history as producer-attested; it does not
become a Barcarolle observation-time claim.

## Evidence Claim Lattice

Claim strength is a product of independent evidence axes, not one ladder:

- supplied Task Pool bundle and cross-record consistency;
- observed source-frame identity and authority;
- Generator behavior and source-protocol continuity;
- executable Check certification and hidden-oracle binding;
- Agent/Task/Check/Workspace/Runtime Result identity;
- Result-source and availability provenance;
- rolling-origin chronology, maturity, censoring, and leakage replay;
- downstream field or tuning outcomes.

The machine claim `task_pool_bundle_internal_consistency` proves only the first
axis. A frame-free user pool remains usable, but cannot support a source-frame
or population-coverage claim. A producer-attested frame requires the declared
blind spots and authority; source-authoritative frames additionally require
their authority receipt. An observed frame is an inventory of what was seen,
not proof that the underlying population is complete.

Prediction-error estimates from a generated or user-supplied pool are
conditional on the exact frozen pool and whatever source-frame/protocol
evidence is present. Generalization to natural future traffic additionally
requires a defensible source protocol, prospective behavior continuity, and
enough future Origin blocks. Reporting must not infer those axes from internal
bundle validity.

## Dependence And Stratification

`dependency_cluster_id` is protocol-only metadata for filtering and blocked
history/future evaluation. It is never a Selector feature. A cluster must be
derived from sanitized, reproducible source relations by a concrete adapter;
caller labels without relation evidence are not proof of cluster correctness.

`sampling_stratum` is a separate visible label for coverage, task difficulty,
or future-composition analysis. It may enter a FeatureSnapshot as
`task_stratum`. Every frozen value must replay against its TaskRecord, known-at
time, and Task digest before it can support execution or a report. A stratum is
not evidence of statistical independence.

The fixed Pylint adapter implements the first concrete dependency protocol as
`pylint_trusted_patch_path_components_v1`. It reads trusted certification-side
reference patches, persists only each SourceEvent's patch digest and exact
repository-relative changed paths, creates an undirected edge for exact path
overlap, and assigns deterministic connected-component IDs. The evidence is a
self-digested adapter artifact at `records/adapter-evidence.jsonl`. Generation
provenance binds its ref and digest as run-specific sidecar evidence while
keeping stable behavior inventory-independent. Loading validates the complete
Task Pool bundle, re-derives the artifact from local patches, and checks every
persisted SourceEvent cluster before any paid stage.

Exact path overlap is a conservative, coarse relation: overlap is evidence of
dependence, while no overlap is not proof of independence. Issue/PR links,
reverts, and cherry-picks should be added by a concrete adapter only when its
source data actually supplies those relations. Neither patch text, relation
paths, nor cluster IDs enter Selector features or solver-visible task material.

The two target estimands are:

1. realistic traffic, where dependency clusters may recur but uncertainty is
   blocked by an appropriate independent unit;
2. unseen-cluster generalization, where future dependency clusters are absent
   from history.

## Comparable Selector Evidence

Aggregate comparisons accept only `future_pass_rate_mae` records that:

- aggregate all Agents;
- are `complete` or `complete_with_exclusions`;
- bind the same Task Pool, budget, metric config, join policy, and denominator
  policy;
- include every registered Selector at every included Origin;
- bind exactly the same future Result evidence for all Selectors at one Origin.

Learned-Selector fitting additionally requires one ordered full AgentRecord
digest binding across all training Origins. Every Result used for the fitted
loss must project from its cache identity to that frozen Agent binding; matching
an `agent_id` string alone does not define a stable treatment. The trainer also
loads the common frozen Task Pool, validates every Origin and Snapshot against
its Task/Check records, and requires each Result cache identity to project to
those records before the loss can affect fitted parameters.

An unseen-Agent claim has another evidence boundary. Reference or training
Agents that supply Selector features must be disjoint from evaluation Agents.
An outcome-free Selector may be evaluated on a frozen Agent panel, but
nominating it after inspecting that panel still does not establish transfer to
a new Agent. Report panel-conditional and held-out-Agent claims separately.

An Origin's future weight is the number of distinct mature Task/Check refs with
Result cells after common benchmark-owned exclusions. Planned refs with no
scoreable Result do not increase the weight.

For Selector `s` with Origin losses `L(s, o)` and future weights `n(o)`, report:

- macro-Origin MAE: `mean_o L(s, o)`;
- future-task-count-weighted MAE:
  `sum_o n(o) * L(s, o) / sum_o n(o)`;
- for every canonical Selector pair `(a, b)`, paired differences using
  `L(a, o) - L(b, o)` under both weightings. Negative favors `a`.

The pairwise table lets a report identify a predeclared fallback without adding
fallback identity to Result or Metric records. Choosing a fallback after
looking at the table is exploratory, not confirmatory.

## Primary Baseline And Landscape Diagnostics

For the current future-pass-rate fidelity claim, the primary baseline is every
eligible historical Task/Check ref without Selection. Its benchmark may be
larger and more expensive than the selected benchmark; that is the compression
comparison.

An equal-budget random Selection is calibration, not the primary baseline.
Report its loss distribution or a predeclared seed bank and locate the
candidate within it. State whether Origins draw independently or share a
reproducible seed. When a finite outcome-category model permits an exact
distribution, report its expectation, quantiles, candidate percentile,
as-good-or-better mass, elite means, and expected best-of-draw frontier. A
fixed-seed sensitivity checks whether cross-Origin coupling changes the
conclusion.

Continuous historical support and a discrete hindsight budget oracle are
endpoints. They may open future outcomes to measure representability and search
density, but cannot enter Selection or be reported as learnable algorithms.
Low support loss does not establish that pre-origin features can identify the
corresponding subset.

A response-matrix or Item Response Theory subset is first a fixed-universe
compression comparator. Fit item parameters only from reference-Agent Results
available before the evaluation boundary, then freeze the subset before
opening disjoint held-out-Agent or later-Origin outcomes. Report held-out
reconstruction of the complete historical benchmark separately from
later-Origin future MAE. Accurate historical score reconstruction cannot by
itself clear the temporal promotion gate.

The current algorithm-promotion gate requires at least `0.02` lower
macro-Origin MAE than full history and a paired 95% Origin-block interval wholly
below zero. Random-space position, support, null controls, rank agreement, and
recommendation regret remain separately labeled diagnostics. Changing the
primary metric or practical margin after outcomes open is exploratory.

Predeclare the future-block horizon from the deployment question. When more
than one reasonable horizon exists, report a fixed block-size sensitivity and
dependency-deduplicated view without selecting the most favorable result.
Changing sign across those views is a robustness failure even if one point
estimate is favorable.

## Shrinkage Safe Switch

ALG-001 uses the same complete paired Origin rows. For candidate `s`, fallback
`f`, and `n` prior Origins, define improvement `d_o = L(f,o) - L(s,o)` so
positive values favor the candidate. With prior strength `p`, the shrunk mean is
`sum_o d_o / (n + p)`. The conservative score subtracts
`uncertainty_multiplier * sample_standard_error(d)`.

The current default is `p=2`, at least four Origins, zero improvement margin,
and uncertainty multiplier one. A candidate is eligible only when its
conservative score strictly exceeds the margin; the largest score wins, with
Selector ID as the deterministic final tie-break. No prior history, fewer than
the minimum Origins, or no eligible candidate returns the predeclared fallback.

This gate is a deterministic decision heuristic, not a calibrated confidence
interval. Prior strength, minimum history, margin, and uncertainty multiplier
must be chosen within nested rolling-origin history. Outer Origins compare the
frozen safe switch against fixed experts, raw mean choice, no-shrink, no-gate,
and hindsight-oracle diagnostics.

`future_coverage` and `future_invalid_rate` remain holdout-evidence diagnostics.
They are not Selector prediction losses.

## Drift-Aware EWMA Guard

ALG-004 uses the same complete paired MAE rows and requires their exact training
`RollingOriginRecord` set plus an explicit deployment Origin. All records must
validate and bind the same Task Pool. Each training origin time and cutoff must
strictly precede deployment, its label-maturity cutoff must not exceed the
deployment cutoff, and the training set must use one comparable policy and
distinct materialized `as_of_cutoff` instants. Rows are ordered by those
instants rather than caller order or Origin ID.

For half-life `h > 0`, give the newest prior Origin age zero and an Origin `a`
steps older weight `2^(-a/h)`. Rank every registered Selector by its normalized
weighted mean MAE. If the fallback ranks first, keep it. Otherwise compare only
the ranked candidate and fallback with ALG-001's ordinary unweighted,
full-history safe-switch rule. A candidate that captures a recent trend but
does not clear that gate cannot be deployed.

The implementation does not attach a confidence interpretation to decayed
weights. The default half-life is two Origins. Nested rolling-origin comparison
predeclares half-lives 0.5, 1, 2, and 4 plus the non-decayed history baseline;
the safe-switch parameters are tuned only inside the same prior history. Outer
Origins compare the frozen choice against fixed experts, non-decayed safe
choice, and raw mean choice. Reject the method if its paired outer-origin MAE
does not improve or if the selected half-life is unstable across adjacent
training windows.

## Stratified Forecast And Weighting

ALG-002 operates on Task/Check refs because that is the Selection and primary
MAE denominator. At an Origin, let `c_s` be the count for stratum `s` among the
last `w` eligible refs, let `S` be all strata present in the eligible history,
and let `alpha > 0` be symmetric. The forecast is

`p_s = (c_s + alpha) / (sum_j c_j + alpha * |S|)`.

For budget `B`, start from `floor(B * p_s)`, capped by the number of eligible
refs in each stratum. Assign remaining seats to the available stratum with the
largest current deficit `B * p_s - quota_s`; forecast proportion and stratum
name break ties deterministically. This is ordinary largest remainder when no
capacity binds and deterministic overflow redistribution otherwise. A seeded
digest rank chooses refs within each stratum.

With selected share `q_s > 0`, the raw post-stratification weight is `p_s/q_s`.
The executable weighted variant stores `min(weight_cap, p_s/q_s)` on every
selected ref in stratum `s`; `weight_cap` must be at least one. The exact
unweighted baseline sets `weight_cap=null` and stores weight one. Existing
selection metrics normalize by the total selected weight.

For each outer Origin, report the total-variation distance between future
stratum proportions and (a) the forecast, (b) the unweighted selected mix, and
(c) the capped weighted selected mix. Also report maximum selected weight, cap
activation fraction, and effective sample size
`(sum_i weight_i)^2 / sum_i weight_i^2`. Alpha, trailing-window length, cap,
and seed are hyperparameters selected only inside nested rolling origins. The
required comparison set is random, recency, coverage, and unweighted
stratified selection. No current synthetic test or implementation status is an
empirical accuracy claim.

## Rank-Mixture Simplex Choice

ALG-003 predeclares the ten coverage/random/recency weight triples whose
components are nonnegative thirds summing to one. This grid includes the three
individual experts, the equal-weight point, and all two-expert thirds mixtures.
All points share the same random seed, coverage mapping, feature classes, and
grid-protocol digest. Each point must produce its own frozen Selection and
paired future MAE through the ordinary evaluation path. Individual expert
losses are not a valid substitute for observing the blended rank Selection.

At deployment with `n` prior Origins, use equal weights when `n` is below the
declared minimum (currently four). Otherwise let `m_j` be each grid point's
mean paired MAE. For the lowest-mean point `j*`, compute the sample standard
error of its Origin losses and set `limit = m_j* + SE_j*`. Among points with
`m_j <= limit`, choose the one minimizing squared Euclidean distance to
`(1/3, 1/3, 1/3)`; then prefer lower mean and Selector ID. This is the discrete
one-standard-error rule, not a confidence interval or proof that equal weights
are optimal.

The outer rolling-origin comparison includes equal weights, each expert, the
current inverse-MAE fitted mixture, and the frozen one-SE choice. Reject the
method if gains disappear out of sample or if seed-bank variation dominates
the paired improvement. The grid and four-Origin gate are predeclared starting
points, not empirically calibrated defaults.

## Stochastic Selectors

Random-seed variants form a seed bank only when Selector family, version,
training sources, allowed feature classes, and every non-seed parameter are
identical. The current recognized seed fields are `seed` for `random` and
`stratified_forecast`, and `random_seed` for `rule_mixture`.

For a bank with at least two variants, report the mean and population standard
deviation of each variant's macro-Origin MAE. Do not pool unrelated fitted
weights or feature contracts merely because their family names match.

A small seed bank is not a dense estimate of the random search space. Use an
exact distribution when the outcome structure permits it; otherwise predeclare
enough seeds or simulation draws for the desired tail resolution and report
Monte Carlo uncertainty.

## Uncertainty

The current offline summary treats each non-overlapping rolling Origin future
window as one time block. With fewer than eight complete blocks, report
`insufficient_origin_blocks` and no interval.

With at least eight blocks, use protocol
`paired_origin_block_percentile_bootstrap_v1`:

- 10,000 deterministic resamples;
- seed `20260722`;
- sample Origin indices with replacement and preserve pairing across all
  Selectors;
- report the linear-interpolated 2.5th and 97.5th percentiles for macro-Origin
  MAE and paired macro loss differences.

This interval describes variation across the included Origin blocks. It is not
cluster-robust when dependency clusters cross blocks, and it does not quantify
run-level Agent variation without explicit replicate evidence.

## Replicates And Nested Fitting

The next paid paired history should randomize Agent-configuration order within
Task and repeat a predeclared stratified 20–30 percent of Tasks two or three
times. Replicates must be explicit experiment evidence; exact-cache lookup must
not silently choose a latest or best duplicate. A stable core replicate identity
will be added only when the first concrete repeated-run workflow establishes
how those records are reused.

The Pylint experiment layer now freezes that first workflow with
`replicate_schedule.py`. Before any Result evidence is opened, it binds the
exact Task Pool members, two Agent records, base Runtime config, campaign ID,
seed, realized stratified subset, total repeat count, Runtime slot identities,
and every cell's serial order in one self-digested schedule. The subset count
must realize 20–30 percent exactly; largest-remainder allocation preserves the
observed sampling-stratum mix, and digest-ranked choices make the declared seed
replayable without depending on input order. Each Task/replicate block contains
both Agents in a seeded order. The two Agent records must describe distinct
execution configurations after ignoring only `agent_id`; duplicate treatments
are rejected before schedule construction.

Selected Tasks have two or three total observations; all other Tasks have one.
Each replicate index derives a campaign-scoped Runtime config by replacing only
`runtime_config_id` and `stochastic_settings_digest`. That existing exact-cache
dimension names the intended stochastic observation slot: resuming the same
slot reuses it, while a new observation requires another slot or campaign. The
schedule does not add a core replicate record, alter Result selection, or
estimate run-level variance by itself.

The experiment-layer resolver first replays the complete schedule, then joins
each cell to the Result Store with that cell's Runtime config and preserves the
frozen serial order. Resume selects only the first exact missing slot; it does
not choose a latest or best observation. The separate campaign executor requires
a self-digested authority ledger that binds the schedule, Task Pool, Agent set,
Workspace and Runtime configs, endpoint digest, budget, schedule-derived call cap,
one campaign-wide maximum estimated cost per call, and ScoringConfig. Before a
call, the remaining total budget must cover that per-call limit. A returned
Result must not exceed either the per-call limit or the cumulative budget. The
executor preflights all remaining cells but executes at most the first missing
slot per invocation. A durable Result can repair an interrupted completion
event; a stopped cell or result-less reservation cannot retry automatically.
The initializer records authority supplied for a new campaign; it does not
derive authority from the completed pilot. Malformed timestamp, endpoint,
scope, accounting, or pricing-source shapes fail before either ledger file is
created. This reservation guard constrains Barcarolle's estimated-cost
authority; preventing a provider call itself from exceeding the declared
per-call limit still depends on the Agent runtime budget. The call cap is
derived from the frozen schedule rather than supplied again.

At deployment Origin `t`, fitting, algorithm choice, hyperparameters, seed-bank
selection, and uncertainty gates may consume only training Origins whose label-
maturity cutoffs precede `t`. Any tuning within that history uses another
rolling-origin split. Outer-Origin future evidence is opened only after the
deployed Selection is frozen.

Every frozen SelectorInput binds one positive selection limit to the canonical
budget digest derived from that limit. Agent and eligible-ref identities are
unique, and the materialized cutoff is canonical UTC; a self-digested record
that violates any of those intrinsic bindings is not admissible evidence.

ALG-005 remains behind an estimand gate. Existing evidence can reconstruct
usage, a declared pricing view, workspace latency, and exact selected cells, but
the protocol has not chosen among per-Cell p90, whole-Selection total resource,
or bounded-concurrency critical-path time. These targets are not interchangeable.
No resource-constrained choice may claim a hard cap until one target, Agent and
Runtime comparability rule, no-feasible action, nested tuning plan, and
unconstrained Pareto baseline are predeclared.

## Current Claim Boundary

The repository can execute and validate the cohort, censoring, pairing, and
aggregate-summary contracts offline. It cannot yet support a claim that one
Selector predicts better, that a reasoning-effort effect is stable, or that the
bootstrap interval is calibrated for the target repository. Those require a
larger authorized real-task history with enough independent blocks and explicit
replicates.

The 2026-07-27 follow-ups do not relax this boundary. The source-observed SymPy
view remains fully censored. A separate `label_at_task_arrival`
counterfactual replay is valid for development and reuses exact Results, but it
is not source-attested or strict-prospective.

On that opened development scenario, coverage MAE is `0.1833` versus `0.1933`
for full history. The `0.0100` point gain and paired interval
`[-0.0363, +0.0152]` miss the promotion gate. Exact random and support
diagnostics show headroom, while null controls, decision metrics, fixed
candidate screens, and the two-Agent panel do not establish learnability or
transfer.

Normal planning from the panel-conditional primary contrast requires about 44
independent Origins for 80% power at a true `0.02` effect. The earlier
25-Origin calculation applies only to coverage versus a five-seed random-bank
mean. Both counts omit some dependency and Agent-generalization variance, are
planning inputs rather than guarantees, and authorize no campaign.
