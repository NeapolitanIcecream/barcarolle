# Controlled Cold-Start Pre-Origin Theory

Date: 2026-07-29.

Status: initial mechanism inventory frozen before collision audit. This memo
contains no Agent-outcome replay and makes no Selector-validity claim.

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
