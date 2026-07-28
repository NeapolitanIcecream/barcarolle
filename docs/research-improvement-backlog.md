# Research Ledger

Last reviewed: 2026-07-28.

Status: current decisions, evidence limits, and executable research plan.

This ledger contains only information that can change a future action. Design
documents define intended system behavior; code and tests show current
enforcement; `PROCESS.md` is the short cross-session handoff.

## Archive Lineage

The previous ledger is frozen at
[`research-improvement-backlog-2026-07-27.md`](research-improvement-backlog-2026-07-27.md).

- source commit: `a4c3ed265abedd123922ae0c5c6014f00fbf704c`;
- SHA-256:
  `41753a38c93fb72bac681550401dff897391833f4c6abf3f8b2a1b1ed341f9f3`;
- archive policy: do not amend the snapshot; record corrections and superseding
  decisions here with an explicit reference to the archived ID.

Resolved implementation history, repeated rationale, superseded sprint plans,
and dated narratives remain in the archive. This ledger migrates only stable
boundaries, current evidence, open claim gates, and work with a concrete
reopening condition.

## Maintenance Rules

Evidence labels:

- `measured`: produced by a recorded experiment or audit;
- `code-confirmed`: established by current implementation and tests;
- `planned`: a falsifiable route whose evidence has not been collected;
- `preserve`: a boundary that needs contrary evidence before removal.

Work states:

- `ready`: prerequisites exist and the next action is authorized;
- `data-gated`: wait for the stated independent data;
- `authority-gated`: wait for explicit paid-call authority or an external
  resource;
- `trigger-gated`: act only after the recorded measurement or caller appears;
- `closed`: no action remains under the current claim.

Every new algorithm entry must name its estimand, information available at
selection time, primary baseline, random calibration, ablations, and rejection
condition. Close completed work instead of copying its implementation diary
forward.

## Stable Decisions

1. Keep Records, Task Pool, Verification, Workspace, Result Store, Selection,
   Reporting, and Runner as direct modules. Add no registry, Feature Store,
   workflow DAG, generic model service, distributed scheduler, or simulator
   platform without a measured caller.
2. Each Task Pool belongs to one repository. A multi-repository study is a
   collection of repository-local pools, Origins, Selections, and Results; it
   is not a mixed meta-pool.
3. Generators end at a prepared candidate package. User-maintained Task Pools
   open read-only. Runner, Selection, Reporting, and Workspace do not depend on
   a Generator type.
4. Task Pool and Agent Results remain independent. Imported and lazily produced
   Results reuse only under exact Task, Check, Agent, Workspace, and Runtime
   identity, and never rewrite the source bundle.
5. User- or adapter-supplied availability time, dependency cluster, and
   sampling stratum may affect algorithms. They require explicit lineage and
   evidence class. Historical projection creates a counterfactual pool or
   scenario; it never relabels strict-prospective evidence.
6. Selection uses only the target repository's eligible local history at the
   deployment Origin. A learned policy may be fitted on other repositories,
   but their Tasks are not candidates in the target benchmark.
7. Full eligible local history is the primary no-Selection baseline.
   Equal-budget random Selection is a dense calibration of where an algorithm
   lies in the attainable sampling landscape, not a replacement baseline.
8. Fixed-universe score reconstruction, temporal future-Task prediction,
   held-out-repository transfer, and held-out-Agent transfer are different
   claims and must be reported separately.

## Current Evidence And Claim Boundary

The completed public multi-repository development study contains 500
SWE-bench Verified Tasks, three frozen public Agent result vectors, seven
wide-portfolio repositories, three deep-portfolio repositories, and 68
repository-local Origins. It uses full eligible local history as the primary
baseline. Candidate-minus-full-history differences are negative when Selection
helps.

| Route | Wide macro difference and interval | Decision |
| --- | --- | --- |
| Recency | `+0.0189`, `[-0.0040, +0.0400]`; 2/7 repositories favorable | Retire on this panel. |
| Difficulty coverage | `+0.0398`, `[+0.0289, +0.0519]`; 0/7 favorable | Retire on this panel. |
| History match | `-0.0064`, `[-0.0178, +0.0041]`; 5/7 favorable; better than 93.75% of random draws | Keep only as a response-matrix compression control; it misses the `-0.01` development nomination gate. |
| Cross-repository drift match | `+0.0016`, `[-0.0060, +0.0093]`; 4/7 favorable | Reject the mean-drift mechanism. |
| Local trend match | Equal to history match; every outer fold chose alpha zero | Reject the added trend term. |
| ALG-007 centroid | `+0.0015`, `[-0.0215, +0.0253]`; 4/7 favorable | Retire the fixed semantic route on this source family. |
| ALG-007 facility control | `+0.0377`, `[+0.0118, +0.0618]`; 2/7 favorable | Retire. |
| Hindsight support | `-0.1589`, `[-0.1992, -0.1114]`; 7/7 favorable | Strong representability; pre-Origin identification remains the bottleneck. |

Equal-budget random Selection has mean wide difference `+0.0175`, population
SD `0.0159`, and mean Monte Carlo standard error `0.000112` from 20,000 draws.
The deep portfolio does not rescue a candidate: history match is `-0.0014`,
semantic centroid is `+0.0168`, and the fixed recency and coverage rules are
also harmful. Full history is semantically closer to future Tasks than either
ALG-007 subset.

The earlier 75-Task, two-Agent SymPy replay remains a precursor, not a second
independent confirmation. Its coverage gain was `0.0100` with interval
`[-0.0363, +0.0152]`. The new portfolio shows why its direction must not be
generalized from one repository.

No Selector is a Runner default. All current results are counterfactual and
panel-conditional; Check maturity is projected to Task arrival, outer Agent
treatments were not held out, and the Python-heavy source cannot establish
language or source-family portability. The completed study and exact identities
are recorded in
[`experiments/2026-07-28-multi-repository-public-study.md`](experiments/2026-07-28-multi-repository-public-study.md).

This sprint made zero paid API calls and zero coding-Agent calls. One pinned
embedding model already present on disk ran on local CPU. The previous USD 300
authority remains closed, and no current candidate warrants or authorizes paid
validation.

## Multi-Repository Research Contract

### Target

Test whether a frozen, outcome-safe policy can compile a budgeted benchmark
from a target repository's past Tasks whose Agent performance is closer to that
repository's later Tasks than performance on all eligible past Tasks.

The product execution contract remains single-repository:

`one user repository -> one local Task Pool and history -> one Selection`.

Multiple repositories are used only offline to obtain more Origin observations
and repository variation for algorithm research, fitting, and validation. The
learned research form is:

1. fit one global policy using other repositories and only their mature past
   Origins;
2. freeze the policy before opening the target repository's outer outcomes;
3. apply it only to eligible local history in the target repository;
4. evaluate against later Tasks from that same target repository.

Holding out the complete target repository is the validation method used to
show the policy did not overfit its research repositories. It is not a
multi-repository Runner mode. A user repository with no eligible local history
is a separate cold-start estimand and is out of scope.

### Definitions And Scope

- A repository-local Origin is the atomic chronological replay boundary.
- A repository is the primary independent generalization unit.
- Cross-repository training addresses the shortage of Origins in any one
  project; it does not change the single-repository deployment input.
- Forks, mirrors, shared task lineages, or mechanically derived repositories
  belong to one declared repository cluster unless independence is justified.
- A `wide` portfolio contains many independent repositories with few mature
  Origins and tests portability.
- A `deep` portfolio contains fewer repositories with longer histories and
  tests drift, horizon sensitivity, and within-repository learnability.
- The two portfolios are reported separately. Their Origin rows are never
  flattened into one nominal sample count.
- The first multi-repository study holds the importer or Generator paradigm,
  certification policy, Agent panel, metric, and budget policy fixed. It does
  not vary repository, Generator, and Agent treatment simultaneously.

### Estimand

For Selector `s`, repository `r`, and Origin `o`, define

`D(r,o) = L(s,r,o) - L(full_history,r,o)`.

Negative values favor Selection. First aggregate within a repository:

`D(r) = mean_o D(r,o)`.

The primary multi-repository estimand is the macro-repository mean:

`D(macro) = mean_r D(r)`.

Future-task-count-weighted and deployment-volume-weighted summaries are
secondary. They must not let one large repository replace the portability
claim. Equal-budget random distributions, support, and hindsight oracles are
per-repository diagnostics and are aggregated only after their local meanings
are preserved.

For a learned policy in outer fold `r`, fit

`theta(-r) = fit(all eligible training repositories except r)`

using inner rolling-origin evidence only. Apply `theta(-r)` to repository
`r`'s local history and open `r`'s future outcomes only after the policy and
Selection are frozen. The default fitting objective gives every training
repository equal total weight and its Origins equal weight within that
repository. Deployment-volume or task weighting is a secondary alternative
chosen only inside the training folds.

### Required Evidence

A multi-repository algorithm-validity claim requires all of the following:

1. repository eligibility, lineage clusters, Origin construction, future
   horizon, budget, Agent panel, candidate, full-history baseline, random
   calibration, and exclusion rules are frozen before outer outcomes;
2. outer leave-one-repository-out evaluation, with method choice and
   hyperparameters confined to training repositories and their inner earlier
   Origins;
3. a per-repository paired table, direction count, upper-quartile effect
   because positive `D` is harm,
   macro-repository effect, repository-cluster interval,
   leave-one-repository-out sensitivity, and wide/deep breakdown;
4. at least `0.02` lower primary MAE than full history, a paired 95% interval
   wholly below zero, no sign reversal when any one independent repository
   cluster is removed, and stable direction under predeclared horizon and
   dependency views;
5. random percentile, as-good-or-better mass, and best-of-draw frontier to show
   how much of the Task Pool's attainable signal the algorithm captured;
6. a later frozen source or strict-prospective campaign before making an
   external predictive-validity claim.

The pilot must estimate between-repository variance and within-repository
correlation before a confirmatory sample size is fixed. Repository-cluster
uncertainty is primary; an Origin-block interval may be reported only as a
within-repository diagnostic.

### Insufficient Outcomes

None of the following establishes the target claim:

- pooling all Origins as independent observations;
- a favorable random percentile without improving full history;
- a pooled gain driven by one repository or one fork family;
- tuning on the held-out repository's future Results;
- selecting the best horizon, budget, or dependency view after outcomes open;
- a low support or oracle loss without an outcome-safe identification rule;
- fixed-pool score reconstruction without later-Task prediction;
- changing Generator, repository mix, and Agent panel in the same first study;
- importing projected timestamps and calling the result strict-prospective.

### Epistemic Stance And Exit Gates

The stance is hypothesis testing with a practical promotion margin. The sprint
does not assume that cross-repository transfer exists.

- `promote`: every required-evidence gate passes on frozen outer evidence;
- `retain exploratory`: point estimates are useful but uncertainty,
  robustness, or external confirmation fails;
- `refute route`: the frozen candidate fails full history across the planned
  portfolio or its direction depends on one repository cluster;
- `block`: the blinded inventory cannot supply the required local histories,
  repository independence, Agent cells, authority, or endpoint;
- `redirect`: the wide portfolio shows portability but the deep portfolio
  shows no temporal signal, or vice versa; narrow the claim rather than pooling
  away the conflict.

### Boundaries And Resources

- No paid call is authorized by this plan. Future evidence-producing calls
  require explicit authority and `OPENAI_BASE_URL` plus `OPENAI_API_KEY`.
- Existing cached Results may be reused under exact identity.
- This phase may select and import a static source, audit metadata, build
  manifests, implement offline aggregation, and use fixtures or synthetic null
  data. It does not develop a concrete Generator.
- Do not build a mixed Task Pool, repository registry, training service,
  distributed scheduler, or hierarchical model framework.
- Raw prompts, completions, workspaces, embeddings, and external repositories
  stay ignored. Commit only small sanitized manifests, summaries, digests, and
  reports.

### Failure Model

The plan must actively test or bound:

- temporal drift within repositories;
- between-repository treatment heterogeneity;
- fork, dependency, and repeated-task leakage;
- source-frame and Generator bias shared by every repository;
- Agent-panel treatment heterogeneity;
- informative missing, censored, or failed Result cells;
- repository-size domination under pooled weighting;
- post-outcome candidate, horizon, or hyperparameter selection;
- representability without pre-Origin learnability;
- current infrastructure accidentally fitting on the target repository.

## Route Registry

Routes remain separate until evidence supports a combination.

| Route | Thesis | Decisive test | State |
| --- | --- | --- | --- |
| MR-A: fixed outcome-free transfer | A simple semantic or structural rule transfers without fitting target outcomes. | Fixed recency, coverage, and ALG-007 all failed the current seven-repository screen. Reopen ALG-007 only with both a new Task source and new Agent panel; otherwise require a new prespecified mechanism. | `closed` on the current source and panel |
| MR-B: offline multi-repository training | Repository-local Origins from several research repositories teach one policy that still consumes only one repository at deployment. | History match has a small signal, but local trend and mean cross-repository drift add none. Reopen for one theory-grounded family that can be specified without another outcome-driven parameter sweep. | `data-gated` |
| MR-C: partial pooling | Repository-specific effects share useful structure without erasing heterogeneity. | ALG-006 improves held-out-repository loss and calibration over macro averaging and the safe-switch baseline after enough independent repositories exist. | `data-gated` |
| MR-D: fixed-universe compression | A small subset reconstructs full historical Agent scores across unseen Agents. | ALG-008 beats equal-budget random and coverage on held-out Agents, reported separately from future-Task MAE. | `data-gated` |
| MR-E: source and field validity | Generator-conditional gains persist in natural future work. | Frozen later source, then prospective field evidence with an independently defined target frame. | `authority-gated` |

ALG-001's shrinkage switch and ALG-004's EWMA guard remain offline safeguards,
not positive algorithms. ALG-002 is closed for the current duration-stratum
mechanism. ALG-003 is closed for the current seed-sensitive simplex search.
ALG-005 reopens only with a concrete cost or resource estimand.

## Phased Work Plan

### Phase 1 — Blinded Portfolio And Lineage Audit

State: `closed`; completed with zero paid calls.

The pinned 500-Task source yielded 12 repository rows, seven wide repositories,
three deep repositories, and 68 potential Origins. The manifest records exact
source identity, chronological span, current fork metadata, exclusions, and the
counterfactual time contract. Django supplies 63.2% of Origins, so the study
uses repository-first aggregation.

### Phase 2 — Offline Protocol And Tooling

State: `closed`; completed with zero paid calls.

The direct experiment layer now provides source/plan binding, repository-local
Origin construction, repository-first contrasts, cluster bootstrap intervals,
leave-one-cluster-out sensitivity, wide/deep views, 20,000-draw random
calibration, and compact self-digested outputs. Tests cover the evidence
boundary. Core Result, Task Pool, Selection, and Runner contracts did not
change.

### Phase 3 — Multi-Repository Feasibility Pilot

State: `data-gated`; the public zero-cost feasibility portion is complete, but
no candidate warrants missing Agent cells.

The public panel establishes portfolio geometry and route-dependent
between-repository variation. Naive normal approximations for a `0.02` effect
range from roughly 3 to 28 repositories across failed routes, so they are not a
confirmatory target. After a new route passes the development gate, its blinded
pilot must measure repository dependence, missingness, cost, and wall time
before the repository count is frozen. The old 44-Origin calculation is not
carried forward.

### Phase 4 — Frozen Fixed-Selector Comparison

State: `closed` on the current source and Agent panel.

Full history, coverage, recency, equal-budget random, and both frozen ALG-007
rules were compared across wide and deep views. None earned nomination.

### Phase 5 — Offline Multi-Repository Training

State: `data-gated`.

Outer repository folds were exercised directly in the experiment layer.
History match improved full history by only `0.0064`; every trend fold chose
zero adjustment, and mean cross-repository drift was harmful. Add no core
training seam until one concrete family first passes the opened-data
nomination gate. If that happens, bind its repository-local training evidence
with existing digests and keep normal inference on the existing
single-repository path. Do not introduce a meta-pool, model registry, trainer
service, or generic cross-validation framework.

### Phase 6 — Orthogonal Confirmation

State: `data-gated`, then `authority-gated`.

There is no successful route to confirm. After nomination, freeze disjoint
reference/training and held-out Agent panels, then a later source or
strict-prospective campaign. Request paid authority only for the resulting
fixed cells. A route that passes repository transfer but fails Agent transfer
is repository-portable and panel-conditional, not generally valid.

## Entry Gate For The Next Paid Study

There is no active paid plan. Before requesting one, a new mechanism must be
specified without another search over the opened target outcomes and pass the
development gate:

1. wide macro-repository difference at most `-0.01`;
2. at least five of seven repository directions negative;
3. every leave-one-repository-out difference negative;
4. deep macro-repository direction negative;
5. better than at least 75% of equal-budget random draws;
6. if it forecasts Agent outcomes, improvement over history match.

After that gate, freeze candidate code and parameters, source and revision,
reference and held-out Agent panels, Origin schedule, budget, missing-cell
policy, endpoint identity, and exclusions before opening independent outcomes.
Use the candidate-specific blinded pilot to choose the repository count. Add
RI-160's certification checkpoint only when the new pool is actually built,
and RI-163 only for another Pylint campaign. This ordering leaves no currently
useful infrastructure project hidden behind the data gate.

## Current Infrastructure Assessment

| Capability | Current state | Minimal evolution |
| --- | --- | --- |
| Repository-local Task Pools and Origins | `code-confirmed` | Preserve; never mix repositories in one pool. |
| Fixed Selector inference on a local pool | `code-confirmed` | Run once per repository; aggregate outside core. |
| Imported and lazy Result reuse | `code-confirmed` | Preserve exact identity, availability, and conflict rules. |
| User-configured time/stratum scenarios | `code-confirmed` | Preserve explicit lineage and counterfactual labeling. |
| Multi-repository research report | `code-confirmed` in `examples/multi_repository_study` | Preserve the direct repository-first aggregator; it combines effects, not Tasks. |
| Offline multi-repository fitting | Outer repository folds are `code-confirmed` in one experiment script; core `train_selector` remains single-pool. | Add a narrow core seam only after a nominated concrete learned family needs it. |
| Repository/fork independence metadata | `code-confirmed` in the study manifest; no core registry | Repeat the source-specific audit for a new portfolio. |
| Repository-cluster uncertainty | `code-confirmed` in the experiment layer | Preserve cluster bootstrap and leave-one-cluster-out summaries. |
| Random calibration | `code-confirmed` at 20,000 deterministic draws | Reuse until a candidate changes the state space; exact enumeration is not needed at current precision. |
| Local semantic evidence | `code-confirmed` as ignored vectors plus committed identities | ALG-007 failed; add no core embedding service. |

The infrastructure needed before another paid selector study is ready. The
remaining blocker is scientific nomination, not a missing platform. No
multi-repository product execution path or generic training service is needed.

## Active Work Ledger

| ID | Priority | State | Next decision or action |
| --- | --- | --- | --- |
| MR-001 | P1 | `closed` | Portfolio and lineage audit committed; repeat only for a new source revision. |
| MR-002 | P1 | `closed` | Repository-first aggregator, cluster interval, and leave-one-cluster-out tests committed. |
| MR-003 | P1 | `closed` | Fixed public plan, full-history contrast, random calibration, exclusions, and results committed. |
| MR-004 | P1 | `data-gated` | After nomination, use route-specific blinded pilot variance and cost to fix the next study; do not pay before then. |
| MR-005 / ALG-007 | P1 | `closed` | Retired on this source family and panel. Reopen only with both a new Task source and new Agent panel. |
| MR-006 / ALG-006 | P2 | `data-gated` | Require a theory-grounded family to pass the development gate before changing core training input. |
| MR-007 / RI-188 | P1 | `data-gated` | Split reference/training and held-out Agent panels only after a route is nominated. |
| MR-008 | P1 | `data-gated` | A nominated route must exist before later-source or strict-prospective authority is requested. |
| RI-129 / RI-160 | P2 | `trigger-gated` | Add a single-writer exact certification checkpoint before the next comparable pool; replay retained entries before reuse. |
| RI-163 | P2 | `trigger-gated` | Before another Pylint campaign, replace whole-file behavior identity with an explicit version payload and direct-helper digests. |
| RI-191 | P2 | `closed` | 20,000 draws give wide mean Monte Carlo SE `0.000112`; reopen only if the candidate state space changes materially. |

## Migrated Reopening Triggers

| Archived ID | Trigger retained in the new ledger |
| --- | --- |
| RI-021 | Reopen checkout caching only when measured checkout plus cleanup exceeds 5% of campaign wall time. The recorded overhead factor `1.009` did not justify it. |
| RI-031 | Measure certification acceptance, flake, and exclusion rates on a larger real pool; keep them observational until the denominator is defensible. |
| RI-033 | Reopen bounded Agent parallelism only for a measured campaign need, with exact cost attribution, one Result writer, and default concurrency one. |
| RI-034 / RI-119 | Use structural audit signals only after reproducing a boundary or maintenance problem; do not create broad refactor gates or split modules from a score alone. |
| RI-125 | The first additional static source gets one explicit adapter/import path, pinned revision, fidelity name, fixtures, and prepared package. Partition a multi-repository corpus into repository-local pools. |
| RI-126 | A synthetic overlay materializes the final solver state as a full commit plus lineage sidecar; add no core overlay abstraction without a concrete adapter. |
| RI-127 | Interactive episodes reopen only with a concrete source and treatment-conditional contract; require a held-out human branch-policy pilot before human-interaction claims. |
| RI-128 | A model-backed Generator owns its endpoint, authority, and provenance inside its adapter; add no generic model service. |
| RI-130 / RI-139 / RI-140 | Compare Generators only on a common frame and crossed design. Report strata separately; add mixture weights or field claims only with an outer calibration protocol. |
| RI-187 | Preserve the `0.02` full-history margin, paired uncertainty, robustness, random diagnostics, and later-source confirmation as separate gates. |
| RI-189 | Admit immutable embedding projections to core FeatureSnapshot only if ALG-007 first passes transfer gates; add no embedding service. |
| RI-190 / ALG-008 | Reopen IRT only after the Agent panel expands; keep fixed-universe reconstruction separate from temporal validity. |

Items not listed above are closed or superseded for current planning. Their
evidence and identifiers remain recoverable in the archived ledger.
