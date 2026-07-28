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

The current counterfactual study contains one 75-Task SymPy pool, twelve
Origins, and two Agents.

| Axis | Recorded evidence | Decision |
| --- | --- | --- |
| Primary baseline | Full-history MAE is `0.1933`; coverage MAE is `0.1833`. | The `0.0100` gain is below the `0.02` practical gate. |
| Uncertainty | Coverage-minus-full paired interval is `[-0.0363, +0.0152]`. | The interval crosses zero; no promotion. |
| Random landscape | Exact random expectation is `0.2150`, SD is `0.0262`, coverage midrank is `0.8868`, and random as-good-or-better mass is `0.1291`. | Coverage uses meaningful pool signal, but random position does not establish superiority to full history. |
| Support | Continuous support MAE is `0.0250`; discrete hindsight oracle MAE is `0.0375`. | The pool can represent much better subsets; pre-Origin identification remains unsolved. |
| Robustness | Horizon direction changes. Dependency deduplication yields a `0.0167` gain. Repeat views average `0.0071`; none reaches `0.02`. | Recurrence does not explain the whole direction, but no robust effect clears the gate. |
| Semantic route | `centroid_recent_15` and `facility_recent_15` score `0.1917`, versus `0.1933` full history and `0.1833` coverage. | ALG-007 is a frozen cross-source candidate, not positive evidence. |
| Agent axis | Both Agents favor coverage by less than `0.02`; no Agent was held out from nomination. | Evidence is panel-conditional. |
| Fixed-universe route | The current two-Agent matrix has only three empirical difficulty levels. | ALG-008 IRT remains data-gated and cannot substitute for temporal evidence. |

No Selector is a Runner default. These results are counterfactual, not
strict-prospective. The earlier estimate of 44 independent Origins is only an
i.i.d. lower-bound calculation for the present panel; it is not a valid
multi-repository power target because Origins within a repository are
correlated.

The previous USD 300 authority is closed. The last follow-up made zero
coding-Agent calls and one required-endpoint embedding call over 75 Tasks and
22,935 input tokens; the endpoint exposed no cost. No current work item
authorizes paid evidence calls.

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
| MR-A: fixed outcome-free transfer | A simple semantic or structural rule transfers without fitting target outcomes. | Freeze ALG-007, apply it repository-locally, and pass the full-history, cluster-interval, random-landscape, and robustness gates. | `data-gated` |
| MR-B: offline multi-repository training | Repository-local Origins from several research repositories teach one policy that still consumes only one repository at deployment. | Nested leave-one-repository-out evaluation against full history and fixed rules; target future Results never enter fitting. | `data-gated` |
| MR-C: partial pooling | Repository-specific effects share useful structure without erasing heterogeneity. | ALG-006 improves held-out-repository loss and calibration over macro averaging and the safe-switch baseline after enough independent repositories exist. | `data-gated` |
| MR-D: fixed-universe compression | A small subset reconstructs full historical Agent scores across unseen Agents. | ALG-008 beats equal-budget random and coverage on held-out Agents, reported separately from future-Task MAE. | `data-gated` |
| MR-E: source and field validity | Generator-conditional gains persist in natural future work. | Frozen later source, then prospective field evidence with an independently defined target frame. | `authority-gated` |

ALG-001's shrinkage switch and ALG-004's EWMA guard remain offline safeguards,
not positive algorithms. ALG-002 is closed for the current duration-stratum
mechanism. ALG-003 is closed for the current seed-sensitive simplex search.
ALG-005 reopens only with a concrete cost or resource estimand.

## Phased Work Plan

### Phase 1 — Blinded Portfolio And Lineage Audit

State: `ready`; no paid calls.

1. Inventory candidate repositories without opening new Agent outcomes.
2. Prefer one static source/import paradigm and one certification policy.
3. Record repository ID, upstream/fork family, source revision, time coverage,
   eligible Task count, mature Origin count, dependency evidence, verifier
   availability, architecture constraints, and known missingness.
4. Form separate wide and deep candidate portfolios.
5. Verify that every algorithm-relevant time or stratum attribute is imported
   with explicit source or user lineage. Keep strict and counterfactual
   scenarios distinct.

Output: one sanitized portfolio manifest, exclusion log, and feasibility
report. A finding that no defensible portfolio exists is a valid terminal
result.

### Phase 2 — Offline Protocol And Tooling

State: `ready`; no paid calls.

1. Add an experiment-layer aggregator over repository-local reports. Start with
   a per-repository table, macro mean, repository-cluster resampling, and
   leave-one-cluster-out sensitivity.
2. Exercise it with fixtures, null simulations, and the existing SymPy report.
3. Specify sparse exact versus precision-bounded Monte Carlo random calibration
   after the Agent-panel state space is known.
4. Freeze a self-digested preregistration manifest before any new outer
   outcomes.

Do not change core Result, Task Pool, or Selection records for aggregation.

### Phase 3 — Multi-Repository Feasibility Pilot

State: `authority-gated` for missing Agent cells.

1. Certify repository-local pools under the fixed source and policy.
2. Reuse exact cached cells; lazily execute only missing Agent × Task cells
   after Selection when the protocol permits.
3. Estimate feasible Origin counts, between-repository variance,
   within-repository correlation, missingness, cost, and wall time.
4. Fix confirmatory repository and Origin counts from the pilot without using
   it as confirmatory evidence.

The old 44-Origin calculation is not carried forward as the target.

### Phase 4 — Frozen Fixed-Selector Comparison

State: `data-gated`.

Compare full history, coverage, recency, equal-budget random, and the frozen
ALG-007 primary/control across the wide and deep portfolios. This phase can
support a fixed-policy portability result without a cross-repository trainer.

### Phase 5 — Offline Multi-Repository Training

State: `data-gated`.

Only after the portfolio supports nested outer folds and one concrete learned
family exists, widen Selection's training input from one frozen Task Pool to a
sequence of independently validated repository-local evidence groups. Reuse
the existing `SelectorRecord`; bind every training pool, Origin, Agent
treatment, Result, and fitting protocol in `training_source_digests`.
This is an offline research/training entry point. Normal Runner input and
inference remain the existing single-pool, repository-local
`select_with_selector` path.

Do not introduce a meta-pool, model registry, trainer service, or generic
cross-validation framework.

### Phase 6 — Orthogonal Confirmation

State: `authority-gated`.

Cross the successful repository protocol with disjoint reference/training and
held-out Agent panels. Then run a later frozen source or strict-prospective
campaign. A route that passes repository transfer but fails Agent transfer is
reported as repository-portable and panel-conditional.

## Current Infrastructure Assessment

| Capability | Current state | Minimal evolution |
| --- | --- | --- |
| Repository-local Task Pools and Origins | `code-confirmed` | Preserve; never mix repositories in one pool. |
| Fixed Selector inference on a local pool | `code-confirmed` | Run once per repository; aggregate outside core. |
| Imported and lazy Result reuse | `code-confirmed` | Preserve exact identity, availability, and conflict rules. |
| User-configured time/stratum scenarios | `code-confirmed` | Preserve explicit lineage and counterfactual labeling. |
| Multi-repository research report | Missing | Add one experiment-layer aggregator in Phase 2; it aggregates effects, not Tasks. |
| Offline multi-repository fitting | Current `train_selector` requires one deployment Task Pool for every training Origin. | Widen the training evidence input only in Phase 5; keep product inference single-repository. |
| Repository/fork independence metadata | No core registry | Put declared clusters and evidence in the study manifest. |
| Repository-cluster uncertainty | Missing | Implement offline after the portfolio shape is known. |

This is enough infrastructure to begin Phases 1–2 and test fixed policies
across repositories one local run at a time. It is not enough to fit a policy
offline from several repositories. No multi-repository product execution path
is needed.

## Active Work Ledger

| ID | Priority | State | Next decision or action |
| --- | --- | --- | --- |
| MR-001 | P1 | `ready` | Complete the blinded repository portfolio and lineage audit. |
| MR-002 | P1 | `ready` | Implement and test the offline macro-repository/cluster aggregator. |
| MR-003 | P1 | `ready` | Freeze the study manifest, full-history contrast, random calibration, horizons, and exclusions. |
| MR-004 | P1 | `authority-gated` | Run the feasibility pilot and replace nominal Origin power with measured repository-cluster planning. |
| MR-005 / ALG-007 | P1 | `data-gated` | Transfer-test `centroid_recent_15`; keep `facility_recent_15` as the mechanism control. |
| MR-006 / ALG-006 | P2 | `data-gated` | Add the narrow multi-repository fitting seam only after a concrete learned family and enough outer folds exist. |
| MR-007 / RI-188 | P1 | `data-gated` | Split reference/training and held-out Agent panels before unseen-Agent claims. |
| MR-008 | P1 | `authority-gated` | Confirm a successful route on a later frozen source or strict-prospective campaign. |
| RI-129 / RI-160 | P2 | `trigger-gated` | Add a single-writer exact certification checkpoint before the next comparable pool; replay retained entries before reuse. |
| RI-163 | P2 | `trigger-gated` | Before another Pylint campaign, replace whole-file behavior identity with an explicit version payload and direct-helper digests. |
| RI-191 | P2 | `data-gated` | Choose sparse exact or precision-bounded Monte Carlo random calibration after the expanded Agent panel is concrete. |

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
