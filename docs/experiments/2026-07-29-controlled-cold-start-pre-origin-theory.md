# Controlled Cold-Start Pre-Origin Theory

Date: 2026-07-29.

Status: inventory and plan were frozen before execution; `THY-003` Stage A is
now reproducibly retired. This memo contains no Agent-outcome replay and makes
no Selector-validity claim.

## Research Contract

### Target decision

Decide whether at most one new, theory-driven mechanism deserves a frozen
empirical contract for predicting the future Agent pass-rate distribution of
Tasks in one target repository. The mechanism must use only information
available by each Origin and must eventually support an absolute-budget local
Selection, not a cross-repository runtime pool.

Success in this research-and-design session requires:

1. a source-backed inventory of materially distinct pre-Origin mechanisms;
2. an inventory freeze before detailed prior-route inspection;
3. a collision and leakage audit against the research ledger;
4. either one frozen theory contract with a minimum decisive empirical plan or
   a justified stop decision; and
5. a requirement-by-requirement adversarial audit.

### Definitions and invariants

- An **observable** is usable at Origin `o` only if its value and its provenance
  were available no later than `o` under the declared evidence mode.
- A **mechanism** must connect a pre-Origin observable to future Task
  composition or difficulty and then to the Agent pass-rate estimand. A
  correlation with Git activity alone is not enough.
- The runtime candidate set remains the target repository's eligible historical
  Tasks. Cross-repository data may support offline development or
  confirmation, never runtime pooling.
- Full eligible history is the primary baseline. Equal-budget random Selection
  is sampling calibration.
- The outcome gate is future pass-rate MAE for held-out Agent configurations.
  Task-mix, AUC, Brier, embedding, CI, or forecast losses are diagnostics or
  outcome-free gates, not substitutes.
- Repository aggregation is repository first. H5 and H10 are fixed research
  controls whose realized calendar spans must be reported; runtime uses an
  explicit future `TimeRange`.

### Insufficient outcomes

The following do not count as a successful theory:

- forecasting commit, issue, PR, release, or package counts without a
  precommitted bridge to Selection and pass-rate MAE;
- selecting future-like Tasks with future identities, patches, outcomes, or
  labels;
- reconstructing historical Agent scores without predicting a later cohort;
- improving a task-mix diagnostic while failing the pass-rate gate;
- a historical-source replay presented as prospective evidence;
- a platform-specific signal presented as portable without source and language
  checks; or
- an implementation plan whose missing data source is as difficult as the
  target experiment.

### Epistemic stance and terminal states

Established repository requirements are the invariants above and the evidence
boundary in the controlling handoff. The literature below establishes that
software work and repositories evolve, that useful pre-Origin covariates can
exist, and that selected evaluation samples create bias. It does not establish
that any inventory mechanism predicts coding-Agent pass rates.

Working hypotheses are stated per mechanism. The main unknowns are source
availability at historical Origins, whether a signal forecasts Generator Tasks
rather than its source proxy, whether a forecast can be materialized as a
budgeted historical subset, and whether any resulting gain transfers across
Agents and repositories.

Allowed terminal states are:

- **frozen candidate**: one mechanism survives collision and feasibility audit
  and receives an independently testable outcome contract;
- **refutation/stop**: every mechanism is collided, leaked, unavailable, or
  lacks an outcome-strength bridge;
- **bounded inconclusive**: a named external source boundary prevents the
  decisive feasibility test; or
- **external blocker**: the required source cannot be accessed without new
  authority.

### Boundaries

This session may use public literature, repository-local inspection, synthetic
tests, and outcome-free source/Origin checks. It must not read the six sealed
SWE-bench holdout Agents, replay a candidate on opened Agent outcomes, make paid
benchmark or LLM calls, tune an existing algorithm, create a concrete
Generator, add core abstractions, or create an execution runbook.

External sources are used for background and source semantics. Material ideas
are attributed below. Prior candidate implementations and detailed reports are
excluded until the marked inventory is frozen.

## External Research Synthesis

### Software-work arrival and forecasting

Repository work is not safely modeled as homogeneous traffic. Jahanshahi,
Cevik, and Başar compare time-series forecasts of Mozilla bug-report counts and
find that release dates can add short-horizon information
([paper](https://arxiv.org/abs/2104.12001)). Constantinou and Mens forecast a
contributor's next commit with survival analysis over prior and recent activity
across thousands of repositories
([paper](https://doi.org/10.1016/j.jss.2020.110573)). These results motivate
release-state and contributor-state observables, but their targets are work
arrival, not Task difficulty or Agent outcomes.

### Repository evolution

Neamtiu, Xie, and Chen find continuing change and continuing growth across nine
long-running open-source systems, while other proposed evolution laws depend on
their operational definition
([paper](https://doi.org/10.1002/smr.564)). Bird et al. find that file/component
ownership measures are associated with pre-release faults and post-release
failures in two Microsoft systems
([paper](https://www.microsoft.com/en-us/research/publication/dont-touch-my-code-examining-the-effects-of-ownership-on-software-quality/)).
The useful implication is local and conditional: evolving code and contributor
state may forecast where difficult work appears, but a universal repository
law cannot be assumed.

### Temporal distribution shift

Han, Huang, and Wang study assessment under unknown temporal shift and derive an
adaptive rolling-window comparison rather than assuming historical epochs are
exchangeable
([paper](https://proceedings.mlr.press/v235/han24b.html)). Barcarolle's fixed
H5/H10 sensitivities and full-history baseline therefore test distinct
questions: whether a proposed observable adds forward information, and whether
that information is robust to horizon and history depth.

### Benchmark selection

Kossen et al. formalize active testing as estimating a fixed model's evaluation
statistic from selectively labeled test points
([paper](https://proceedings.mlr.press/v139/kossen21a.html)). They emphasize
that informative acquisition creates sample-selection bias and use weighting
to recover an unbiased estimator. This does not directly solve Barcarolle's
future-cohort problem: the future Task identities are absent at Selection time,
and historical Tasks rather than future points must be materialized. It does
establish that subset quality and estimator validity must be audited
separately.

### Prequential and rolling-origin evaluation

Dawid's prequential formulation judges a forecasting system through its
sequential predictions for later observations
([paper](https://rss.onlinelibrary.wiley.com/doi/10.2307/2981683)). Tashman
shows why rolling origins and multiple test periods improve out-of-sample
forecast evaluation and why their implementation choices must be explicit
([paper](https://doi.org/10.1016/S0169-2070(00)00065-0)). These are the basis
for freezing every Origin information set before later evidence is opened.

### Source bias

Kalliamvakou et al. document that GitHub fields can misrepresent development
events—for example, some merged PRs appear unmerged—and that platform samples
contain many inactive or non-software repositories
([paper](https://gousios.org/pub/promises-perils-github.pdf)). Issue-label
practice is also heterogeneous even though labels are common
([paper](https://arxiv.org/abs/2110.01328)). Every platform-derived mechanism
below therefore requires event-time reconstruction, repository inclusion
rules, missingness reporting, and a non-GitHub portability boundary.

## Frozen Initial Mechanism Inventory

The content between the inventory markers was frozen before opening the current
research ledger or any detailed prior candidate report. Its digest is recorded
immediately after the closing marker.

<!-- INITIAL-MECHANISM-INVENTORY-BEGIN -->

### M1 — Release-cycle state

**Thesis.** Scheduled releases, milestones, branch phase, and time since the
last release change the mix of regression fixes, stabilization work, and
feature work. A forecast of the next cohort's release phase could favor
historical Tasks from comparable phases.

- **Reason to predict pass rates:** release phase can change Task type, affected
  subsystem, urgency, and test surface; those mediators can change Agent
  success. The direct evidence currently predicts bug-report volume, not Agent
  outcomes.
- **Exact availability:** signed/annotated tags and commits exist when they
  enter the repository; forge release and milestone values exist only from
  their event timestamps. A release calendar visible at Origin may be used
  prospectively. A calendar retrieved later cannot be projected backward
  without an archive proving its historical value.
- **Import/derivation:** derive prior tags and branch state from a local clone;
  import milestone/release event histories or a user-supplied, timestamped
  release calendar. Persist source query time, event time, and missing-history
  state.
- **Generator dependence:** medium to high. The source protocol must produce
  Tasks whose arrivals follow the repository's issue/PR/release process. A
  synthetic Generator that samples commits independently can erase the
  mechanism.
- **Bias and leakage:** rewritten milestone due dates, backfilled releases,
  branch-name conventions, irregular hotfixes, and hindsight reconstruction of
  planned dates. Future tags and later milestone edits are forbidden.
- **Smallest outcome-free falsification:** using only calendar values archived
  before each Origin, compare a frozen phase forecast against seasonality and
  full-history phase proportions for next-H Task source type/module mix. Report
  missing calendars as failures, not zero signal.
- **Independent pass-rate evidence:** a later frozen replay on development
  Agents followed, if every gate passes, by a source-observed prospective
  schedule; compare full history and equal-budget random at H5/H10.

### M2 — Contributor and ownership transition

**Thesis.** Changes in module ownership concentration, recent-owner departure
risk, and newcomer share alter which subsystems receive work and the amount of
latent repository knowledge represented by that work. Select historical Tasks
from modules and ownership states matching the forecast future state.

- **Reason to predict pass rates:** ownership and expertise measures have been
  associated with software failures, and recent contribution histories can
  predict future contributor activity. Agent difficulty may shift when work
  moves into low-ownership or transition-heavy components.
- **Exact availability:** commits, authorship, and file contents reachable from
  the mainline at Origin. Identity aliases may be resolved only with mappings
  available at Origin; later identity merges are a weaker retrospective view.
- **Import/derivation:** a local clone supplies commit authorship and
  path-level contribution counts. Derive recent owner share, ownership entropy,
  newcomer share, and contributor survival summaries with pseudonymous stable
  identities.
- **Generator dependence:** medium. Historical and future Task source records
  need a sanitized module mapping; a Generator that hides or changes the
  work-to-module relation weakens the bridge.
- **Bias and leakage:** squash merges, bots, shared accounts, private
  contributions, author aliases, monorepo team boundaries, and future alias
  resolution. Do not use the future Task patch to assign its pre-Origin state
  in Selection.
- **Smallest outcome-free falsification:** freeze ownership-state forecasts and
  test whether they improve next-H module/work-type distribution over module
  churn and full-history controls. Alias perturbation and bot removal are
  negative/sensitivity controls.
- **Independent pass-rate evidence:** a frozen cross-repository development
  replay with repository-first intervals, then held-out-Agent and prospective
  confirmation if the mechanism and materialization ablations pass.

### M3 — External dependency-shock exposure

**Thesis.** Upstream package releases, security advisories, runtime/toolchain
deprecations, and the target repository's lag behind them create exogenous
compatibility shocks. The Origin-time dependency graph and only already
published upstream events can forecast which maintenance strata will appear
next. Selection would represent the forecast shock regime using eligible
historical Tasks from comparable dependency/toolchain strata.

- **Reason to predict pass rates:** dependency breaking changes can propagate
  into clients, including through non-major and transitive releases. Venturini
  et al. report affected client packages and frequent non-major breaks
  ([paper](https://arxiv.org/abs/2301.04563)); He et al. show dependency-update
  bots induce real maintenance work but have sparse compatibility evidence
  ([paper](https://arxiv.org/abs/2206.07230)). Compatibility and toolchain work
  can change environment reconstruction, API migration breadth, and test
  failures, all plausible Agent-difficulty mediators.
- **Exact availability:** the target manifest/lockfile at Origin; upstream
  releases with registry publication times no later than Origin; advisories
  with published times no later than Origin; and toolchain notices archived by
  Origin. Later corrections, yanks, advisory modifications, and rebuilt
  dependency graphs must retain their observation-time semantics.
- **Import/derivation:** read manifests and lockfiles from the Origin commit;
  import timestamped package-registry release metadata and advisory snapshots;
  resolve the dependency graph in a pinned disposable environment or accept a
  user-supplied signed dependency inventory. Bind ecosystem, resolver,
  platform, source response digest, and query time.
- **Generator dependence:** medium. The Task source must preserve a sanitized
  dependency/toolchain stratum or module relation. The forecast is useless when
  the Generator excludes dependency and compatibility work.
- **Bias and leakage:** ecosystem coverage, mutable/yanked releases, missing
  historical advisories, unobserved private registries, environment-specific
  resolution, transitive-version ambiguity, bot-generated PR overcount, and
  retrospective use of an advisory's later text. Future package events are
  forbidden.
- **Smallest outcome-free falsification:** at frozen historical Origins, test
  whether past-only shock exposure improves next-H dependency/toolchain Task
  mix or source-event incidence over (a) full-history mix, (b) repository-only
  release/activity controls, (c) time-shifted upstream events, and (d)
  unrelated-package shocks. This opens no Agent outcomes.
- **Independent pass-rate evidence:** only after source feasibility and
  task-mix gates pass, freeze the mapper and subset materialization for
  repository-first H5/H10 pass-rate MAE on opened development Agents. Require
  held-out Agent/model/harness/provider/language checks and a new source or
  prospective confirmation before a validity claim.

### M4 — Event-sourced work-queue composition

**Thesis.** The open issue/PR/milestone queue at Origin represents unresolved
user demand and planned work. Aggregate queue composition and aging may forecast
the type and module distribution of newly materialized future Tasks.

- **Reason to predict pass rates:** issue labels encode feature, development,
  and defect categories, while queue age and triage state may separate routine
  work from ambiguous or blocked work. Those categories can mediate Agent
  difficulty.
- **Exact availability:** issue/PR fields and every label, assignment,
  milestone, close/reopen, and edit event no later than Origin. A current API
  snapshot without event history is not a historical snapshot.
- **Import/derivation:** import an event-sourced issue-tracker export, forge
  timeline API, or user audit log. Derive only aggregate counts, age
  distributions, and taxonomy mappings frozen before the Origin.
- **Generator dependence:** high. If Task text is the pre-existing issue, its
  material-arrival time is issue creation and it belongs in history rather than
  the future cohort. The mechanism is coherent only when the source protocol
  defines a later, distinct Task materialization event.
- **Bias and leakage:** the queue can expose exact future Task identities,
  edited issue text, later labels, private planning boards, duplicated issues,
  and platform-specific triage practice. Removing future-linked queue items
  using hindsight would itself leak.
- **Smallest outcome-free falsification:** first audit Task material-arrival
  semantics. If coherent, forecast only aggregate next-H source categories from
  queue aggregates and compare with historical arrival-rate and label-mix
  controls. Stop if exact future identities cannot be excluded without
  hindsight.
- **Independent pass-rate evidence:** a source-observed prospective tracker
  snapshot plus a frozen aggregation and mapping contract; development replay
  is insufficient if historical event snapshots cannot be reconstructed.

### M5 — CI-health regime

**Thesis.** Recent mainline build/test failure classes, recovery time, flake
rate, and workflow changes reveal an unstable subsystem or environment regime.
That regime may forecast future repair Tasks and their verification difficulty.

- **Reason to predict pass rates:** empirical CI studies find recent build
  history among the strongest predictors of later build failures
  ([paper](https://doi.org/10.34726/hss.2016.37419)). Persistent dependency,
  environment, test, or code failures may change both future Task mix and the
  likelihood that an Agent can produce a verified patch.
- **Exact availability:** completed check/run status, configuration, timing,
  and retained log or failure category observed no later than Origin. Reruns,
  deleted logs, and later classifications require their own timestamps.
- **Import/derivation:** import forge check-run/action metadata or a user CI
  export; derive a small declared failure taxonomy, rolling failure rate,
  recovery time, workflow-change indicators, and missing-log fraction.
- **Generator dependence:** medium to high. The Generator and certification
  Check must sample work related to the observed CI surface; otherwise CI health
  predicts a different process.
- **Bias and leakage:** short retention, cancelled runs, branch protection,
  retry policy, infrastructure outages, flaky tests, private checks, and
  workflow migrations. A red run is not automatically a code defect or a hard
  Task.
- **Smallest outcome-free falsification:** forecast next-H source failure
  categories, certification-invalid rate, or Task module mix from pre-Origin
  CI state, with shuffled-status, infrastructure-only, and retention-complete
  controls. Separate source failure from Agent verification failure.
- **Independent pass-rate evidence:** a frozen development replay crossed by
  Agent/harness/provider and CI platform, followed by prospective CI capture if
  pass-rate gates clear.

### Initial portfolio decision

No mechanism is nominated at the inventory stage. M3 has the clearest
exogenous timing argument; M2 has the strongest repository-local availability;
M1 is cheap but historically hard to timestamp; M4 has the highest identity
leakage risk; and M5 has the highest retention and Check-confounding risk. These
are search priors only. Collision and feasibility evidence may retire all five.

<!-- INITIAL-MECHANISM-INVENTORY-END -->

Inventory SHA-256:
`8a8612450bd5ecdd6918f2fb262fd20045cb15da6d9be5ed985811d495c263a5`.

## Approach Registry At Freeze

| Family | Decisive next test | Evidence at freeze | Exact gap | Status | Reopen condition |
| --- | --- | --- | --- | --- | --- |
| M1 release-cycle | archived-calendar coverage and task-mix forecast | literature plausibility | historical schedule values | open | source snapshot with event-time proof |
| M2 ownership transition | module-traffic gain beyond churn | literature plausibility; local Git availability | Task-module and Agent-MAE bridge | open | stable sanitized module mapping |
| M3 dependency shock | past-only shock/source feasibility and negative controls | ecosystem propagation evidence | task incidence and subset mapping | open | sufficient manifests and registry history |
| M4 work queue | material-arrival semantic audit | common but heterogeneous issue labels | exact-identity leakage | open/high risk | event-sourced aggregate that cannot identify future Tasks |
| M5 CI regime | retention-complete temporal source audit | recent CI history predicts later CI failure | source retention and Check confounding | open/high risk | complete run history with failure provenance |

## Collision Audit

The audit opened the research ledger and detailed prior reports only after the
inventory and its digest were committed. It compared information paths, not
names: a new feature does not define a new route when its causal bridge and
subset materialization repeat a closed experiment.

| Mechanism | Collision or boundary | Decision |
| --- | --- | --- |
| M1 release-cycle state | The prior cold-start audit already deprioritized release-calendar phase because it overlaps the closed temporal family. Recency, duration strata, and adaptive temporal routes have also failed their frozen transfer or robustness gates. | Remove. A historically archived calendar could support a different source-specific study, but another phase proxy is not a new route. |
| M2 ownership transition | Git authorship is available and varied, but the proposed bridge remains Git state → future module mix → historical module-matched subset. `THY-001R` falsified raw Git pressure and `THY-002S` falsified the current Task-mix-to-subset bridge. Adding owner entropy inside that information path would be tuning on opened route knowledge unless an independent ownership-native Task source first supplies a distinct target. | Do not nominate. Preserve as a source-gated hypothesis, not a reopened Git/module candidate. |
| M3 dependency shock | Broad advisory counts were previously rejected, but the exact Origin lock graph crossed with already-published upstream release times is exposure-specific, exogenous to target-repository Git activity, and not used by `THY-001R`, `THY-002`, or `THY-002S`. | Retain only as registry-dated direct npm dependency lag. Exclude advisories, CI, transitive resolution, dist-tags, and deprecation from version one. |
| M4 work queue | Open leaf issues expose existing Task identity under the current material-availability contract. Parent-level work intent is already `MR-H`, whose complete event archive and native Task-arrival mapping are unresolved. Aggregate queue aging does not solve that semantic boundary. | Remove. Keep the existing `MR-H` data gate; do not create a second queue route. |
| M5 CI regime | Broad CI state collides with the prior rejected raw-CI family; the exposure-specific survivor is already the differential upstream-nightly-CI challenger. Historical run retention and Check/source-failure confounding remain unresolved. | Remove. Do not substitute a generic red-build score for the already specified source gate. |

This audit does not refute ownership, planning, or CI effects in software
engineering. It says they do not presently supply an independent, executable
Barcarolle theory route under the handoff's no-tuning and information-availability
rules.

## Outcome-Free Feasibility

All checks used the ignored SWE-rebench repository/source artifacts already
bound by `THY-002`. They opened no Agent outcomes, no sealed holdout, and made
no paid or LLM call. The compact record is
[`source-feasibility.json`](../../examples/dependency_lag_theory/source-feasibility.json).

### Repository and Task support

Across the complete 40-repository, 436-Origin frame, 396 Origins in 39
repositories contain a recognized dependency declaration. The fixed narrow
frame is nine Node repositories whose 119 frozen Origins all contain a root
`package.json` and a committed npm, pnpm, or Yarn lockfile. Those repositories
contain 1,420 Tasks. Five repositories have at least ten Origins, fixing a
source-derived deep frame before candidate performance exists.

The scoring-only reference-patch label “touches a root Node manifest or
lockfile” is sparse but measurable: 103/1,420 Tasks are positive. Twenty-seven
of 119 H5 Origins and 40/119 H10 Origins have at least one positive future Task;
eight of nine repositories contribute a positive future Origin at both
horizons. The between-repository rate is highly heterogeneous, so pooled Task
weighting would be misleading and repository-first aggregation is mandatory.
This label never enters Selection.

Python was not chosen as a parallel version-one frame. Eleven repositories and
103 Origins have root Python declarations, but none has a committed exact lock
at every frozen Origin. A requirements range retrieved later would not prove
the resolved Origin state.

### Registry support and variation

npm's full package metadata includes per-version publication times, while its
registry API is a current response rather than an immutable historical
snapshot
([package metadata](https://github.com/npm/registry/blob/master/docs/responses/package-metadata.md),
[registry API](https://github.com/npm/registry/blob/main/docs/REGISTRY-API.md)).
Moreover, npm permits package/version removal under declared conditions, so a
packument fetched today can differ from what an Origin-time client saw
([unpublish policy](https://docs.npmjs.com/policies/unpublish)).

A bounded current-source check queried four deterministically sampled direct
dependencies in each of five package-lock repositories at their first and last
frozen Origins. All 20 requests succeeded. Nine of 20 lag classifications
changed, spanning four of five repositories; classification projection digest
is `20ae8bf1…897a`. This establishes source accessibility and temporal
variation, not historical visibility or predictive value. Raw responses were
not retained, so the result is exploratory. The frozen study must retain and
digest every full packument before it can produce accepted counterfactual
evidence.

## Frozen Theory Contract

### THY-003 — Registry-Dated Dependency-Lag Nearest Regime

The selected hypothesis is deliberately narrower than M3:

> The distribution of direct production and development dependencies that are
> current, patch-lagged, minor-lagged, major-lagged, or unknown at an Origin
> persists over a short future window and changes the incidence and
> verification difficulty of compatibility, update, and toolchain Tasks.
> Historical Tasks observed under the closest pre-Task lag regimes should
> therefore estimate the future Agent pass rate better than all history.

The complete frozen design is
[`plan.json`](../../examples/dependency_lag_theory/plan.json), digest
`0126c44a4b3c4878637fef969fdf29a5ff5477fa487c967710667c3154853d5d`.
At design freeze there was intentionally no runner.

At each cutoff, the candidate reads only the root `package.json`, the first
supported committed lockfile, and npm versions with publication time no later
than the cutoff. It ignores current dist-tags, advisories, deprecation,
downloads, maintainers, transitive packages, prereleases, non-SemVer versions,
CI, and every future Task field. Exact stable versions are mechanically
classified under the frozen strict `x.y.z` rule; this operationalization should
not be confused with a claim that every package follows semantic-versioning
intent ([SemVer specification](https://semver.org/)).

The state is ten joint proportions: production/development crossed with five
lag categories. Distance is half the L1 distance. Each historical Task receives
the state observable at its declared Task time; absence of a supported
historical state is a visible missing-state marker at distance one. Selection
is the ten eligible historical Tasks with smallest distance to the Origin
state, with a SHA-256 tie-break. It is local, absolute-budget, deterministic,
and outcome-free.

The mechanism bridge has three independently falsifiable links:

1. **Observable:** registry publication timing adds information beyond the
   manifest/lock alone and survives circular time-shift nulls.
2. **Forecast:** a fixed inverse-distance historical weighting predicts future
   root dependency-touch incidence better than full history and trailing-H.
3. **Materialization:** the deterministic ten-Task nearest-regime subset
   preserves the continuous forecast closely enough to justify opening the
   Agent-outcome estimand.

Failure at any link retires `THY-003` on this frame. No category, package scope,
distance, weighting, budget, horizon, label, repository, or threshold may be
changed in response.

## Minimum Decisive Empirical Plan

### Stage A — authorized outcome-free falsification

The fixed wide frame is the nine repositories in the plan; the deep frame is
the five with at least ten Origins. The study reuses the bound 119
non-overlapping rolling Origins, with H5 primary and H10 sensitivity, and
reports realized calendar spans. It must first admit every Origin, retain and
reload-digest the raw registry bytes, resolve at least 70% of declared direct
dependencies, observe at least three distinct Origin states in six of nine
repositories, and reproduce byte-identically twice.

The primary diagnostic is future-Task Brier loss for the scoring-only binary
root dependency-touch label. Tasks aggregate to Origins, Origins to
repositories, and repositories equally. A deterministic 20,000-draw
repository bootstrap supplies the paired interval; every
leave-one-repository-out result is reported.

The candidate must pass all of the following:

- continuous and budget-ten forecasts beat full history at H5, with paired
  repository interval upper bounds below zero and at least 6/9 repositories
  favorable;
- both remain negative against full history at H10 with at least 6/9
  favorable, and both deep-frame contrasts are negative at H5 and H10;
- every H5 leave-one-repository-out materialized contrast is negative;
- the budget-ten loss is no more than `0.005` above its continuous forecast;
- the budget-ten candidate beats trailing-H and the lock-only ablation at both
  horizons; and
- its 20,000-draw circular-state temporal-null as-good-or-better rate is below
  `0.10`.

There is no practical-effect claim on this diagnostic scale; the value is the
conjunction of direction, uncertainty, breadth, robustness, ablation, null,
and reproduction evidence. A failure stops the route without Agent replay.

### Stage-A execution result

An independent pre-execution audit found several mechanical ambiguities in the
scientific plan. The
[`execution-addendum.json`](../../examples/dependency_lag_theory/execution-addendum.json),
digest `f920d134…c739`, closed them before any membership or result existed. It
fixed the state-cell coverage denominator, lockfile parsers, scalar binary
Brier definition, exact rational distance, lock-only comparison, bootstrap,
temporal null, and terminal states without changing the candidate or a gate.
The accepted execution lock `4774fbfe…df673` binds corrected runner commit
`8531d9a4`, Python `3.14.0`, DuckDB `1.5.5`, all nine repository heads, and
595 raw packuments before scoring labels load.

An independent audit invalidated the first execution lock `e9be3d28…1dc9`.
Its source loader read reference patches while constructing Task identities,
before the declared scoring-label barrier, and its Origin-variation count used
unreduced count/denominator pairs. The candidate never consumed the patch
projection, and independently normalized variation counts were unchanged in
all nine repositories, but the run was still an execution-contract violation.
The accepted loader selects only repository, identity, base commit, source
time, language, and PR URL; a regression test rejects any `patch` projection.
The corrected discovery file is byte-identical to the invalid run's discovery,
including all Task, Origin, state-point, and package digests.
An independent post-correction audit found no remaining blocker and confirmed
that every scientific payload field is unchanged.

Source admission passed:

- all 1,420 Tasks and 119 Origins reproduced; all Origins had a supported
  nonempty state and seven historical Tasks used the declared missing marker;
- 82,279/84,418 state-package cells (`97.47%`) had an exact lock resolution
  with an eligible publication timestamp;
- every repository had at least five distinct Origin state vectors;
- 595/595 full packument responses returned HTTP 200, totaling 641,582,736
  ignored raw bytes; and
- two corrected offline runs were byte-identical at SHA-256
  `02c18c81…01a7`.

The scientific gate failed. Negative candidate-minus-control values favor the
candidate:

| Diagnostic | H5 | H10 |
| --- | ---: | ---: |
| Continuous minus full history | `-0.000223`, 95% `[-0.000846, +0.000240]`, 6/9 favorable | `-0.000404`, 6/9 favorable |
| Budget-ten minus full history | `+0.009057`, 95% `[+0.003355, +0.015569]`, 1/9 favorable | `+0.000879`, 4/9 favorable |
| Budget-ten minus continuous | `+0.009280` | `+0.001283` |
| Budget-ten minus trailing-H | `-0.003947` | `-0.001499` |
| Budget-ten minus lock-only budget-ten | `-0.002014` | `-0.008823` |

The continuous forecast had the favorable wide direction at both horizons,
but H5 uncertainty crossed zero and the deep-frame contrasts reversed to
`+0.000079`/`+0.000042`. Hard materialization caused most of the failure:
deep H5/H10 contrasts were `+0.009566`/`+0.007206`, the H5
materialized-versus-continuous gap exceeded `0.005`, and not every H5
leave-one-repository-out contrast was negative. The candidate did beat the two
budgeted controls, so registry timing affected ranking; it did not beat the
primary full-history estimator.

The H5 circular-state null as-good-or-better rate was `0.9496`, against the
required `<0.10`. Thus the observed budget-ten ranking was not distinguished
from temporally shifted Origin states. Result digest is `68acfaa5…ccd9`;
committed evidence digest is `90456efc…1c17`. The strengthened verifier
reconstructed the complete result from the frozen repository, registry, and
label inputs; it did not only replay internal row summaries.

A post-decision descriptive diagnostic helps localize the failure without
reopening the gate. The future label was all zero at 95/119 H5 Origins and
80/119 H10 Origins; mean positive rates were `5.88%` and `6.64%`. A ten-Task
subset can express its rate only in increments of `0.1`. The candidate's mean
absolute movement from full history was `0.06329` after materialization versus
`0.00572` for the continuous forecast. This does not rescue the weak
continuous signal; it shows that sparse labels and coarse subset
discretization amplified it.

`THY-003` is `retired_stage_a` unchanged. Stage B, Agent outcomes, the six
sealed Agents, and paid calls remain unopened. Do not tune peer handling,
categories, distance, weighting, budget, horizon, repositories, label, or
gate on this frame.

### Stage B — separately authorized Agent-outcome decision

Stage B was conditional on every Stage-A gate and is not authorized. A passing
route would have required an additive plan binding the accepted code and
registry bytes, the exact nine/five repository frames, Origin schedule,
unopened Agent configuration
digests, budget, H5/H10, calendar spans, controls, 20,000-draw equal-budget
random protocol, MAE gates, and stop rules before outcomes open.

For each held-out Agent configuration, the estimand is the absolute difference
between pass rate on the ten selected historical Tasks and the next-H future
Tasks. Candidate-minus-full-history repository-first MAE must be at most
`-0.02` at H5, have a paired 95% repository-cluster interval wholly below zero,
be favorable in at least 6/9 wide and 4/5 deep repositories, remain negative
in every leave-one-cluster-out view and at H10, and beat at least 95% of
equal-budget random draws. Agent, model, harness, provider, JavaScript versus
TypeScript, package-manager, and temporal-null directions are frozen in the
plan.

Even a Stage-B pass is panel-conditional development evidence. The same
algorithm must replicate on a later independent npm source or a strict
prospective collection before a predictive-validity claim.

## Evidence Portfolio

| Evidence class | Available now | Required decision use |
| --- | --- | --- |
| Without Agent outcomes | Complete 9-repository/119-Origin Stage A; 97.47% state-cell coverage; byte-identical result `68acfaa5…ccd9` | Retires `THY-003`; continuous direction is weak and budget-ten, deep, null, and robustness gates fail |
| Existing opened outcomes | Multi-SWE and SWE-bench development Results exist, but no current panel covers the exact frozen npm wide/deep frame | None may be opened for retired `THY-003` |
| New source or prospective | 595 responses are frozen for this closed replay; live Origin-time registry snapshots remain unavailable | A different route needs its own source contract; strict registry evidence still requires prospective capture |
| Sealed holdout | Six SWE-bench Agents remain unread on a Python-heavy frame | Not applicable confirmation for this npm-specific route; keep sealed |
| Paid evidence | No active authority or plan | Not authorized for retired `THY-003` |

## Adversarial Requirement Audit

| Requirement | Audit result |
| --- | --- |
| Pre-Origin availability | Candidate filters repository and package events at each cutoff. Current registry retrieval remains explicitly retrospective; strict evidence requires Origin-time byte capture. |
| No future Task leakage | Selection consumes Task ID only for deterministic tie-breaking plus each historical Task's pre-Task state. Future identities, text, patches, labels, and outcomes are forbidden. Reference patches score Stage A only. |
| Local runtime boundary | Every ranking is inside one repository's eligible historical Task Pool. Cross-repository data appears only in offline aggregation. |
| Generator dependence | Root dependency-touch is Generator-conditional and sparse. Stage A tests this bridge directly and failure stops; no natural-traffic claim follows. |
| Baselines and calibration | Full history is primary; trailing-H and lock-only are mechanism controls; equal-budget random is downstream calibration only. |
| H5/H10 and TimeRange | Both task-count controls and calendar spans are required. Runtime remains an explicit future `TimeRange`. |
| Wide/deep and uncertainty | Nine/five frames are frozen from source availability, not performance. Repository-first bootstrap and leave-one-repository-out checks are mandatory. |
| Observable/forecast/subset separation | Registry timing, continuous weighting, and ten-Task materialization have separate ablations and gates. |
| Minimum effect and falsification | Stage A has no surrogate effect claim but requires every robustness gate. Stage B retains the protocol-wide `-0.02` MAE effect and interval gate. Any failure retires the route. |
| Portability | Version one is npm/Node only. JavaScript/TypeScript and package-manager checks are required; no Python or ecosystem-wide claim is permitted. |
| Reproduction and source mutation | 595 raw responses are retained and reload-verified; two offline executions are byte-identical. Evidence remains registry-retrospective, not strict historical. |
| Holdout and paid boundaries | Six sealed Agents stay unread. No paid or benchmark-producing call occurred or is currently authorized. |
| Infrastructure proportionality | The frozen deliverable is one direct example-layer plan. No core schema, registry service, source adapter, Generator, or Runner was added. |

## Decision And Recommendation

`THY-003` is reproducibly retired at Stage A. npm publication time was
available and varied, and it improved the budgeted ranking over trailing-H and
lock-only controls, but neither the smooth forecast nor its ten-Task
materialization met the full-history, deep, robustness, and temporal-null
contract. The failure is scientific rather than a source or implementation
blocker.

No Agent replay, holdout access, Generator, core registry service, or paid
authority follows. A later candidate must introduce an independently motivated
mechanism or materialization theory and freeze it on a new evidence boundary;
changing this route's parser, state, distance, budget, horizon, repository
frame, or gates would be rescue tuning.

One research direction remains theory-gated: treat forecast-to-budget-k
materialization as its own algorithmic problem and preserve explicit
pre-Origin target moments rather than selecting the nearest individual Tasks.
It is not `THY-003.1`. Before implementation, a new plan must derive the rule
without this frame's future labels, state which historical Task attributes are
visible, and choose independent development evidence. No core abstraction is
warranted until such a plan nominates a caller.

## Approach Registry After Audit

| Family | Evidence gained | Status | Reopen or advance condition |
| --- | --- | --- | --- |
| M1 release-cycle | collision with closed temporal family | removed | historically archived schedule plus a source-native, non-temporal target |
| M2 ownership transition | 436/436 Origins have recent non-bot Git activity; signal availability is not the missing evidence | source-gated, not nominated | ownership-native Task target that avoids the closed Git/module bridge |
| M3 / THY-003 registry-dated lag | complete Stage A; continuous H5/H10 `-0.000223`/`-0.000404`; materialized `+0.009057`/`+0.000879`; null `0.9496` | retired | do not tune or open Agent outcomes |
| M4 work queue | exact leaf identity leak; parent intent already `MR-H` | removed | existing `MR-H` complete event archive and native Task materialization |
| M5 CI regime | broad form collides; differential nightly CI already specified | removed | retained, timestamp-complete differential upstream-CI episodes with Task alignment |
