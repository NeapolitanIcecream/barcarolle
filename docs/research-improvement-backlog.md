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
   but their Tasks are not candidates in the target benchmark. A rolling-origin
   fit may use only records available by the target Origin's calendar cutoff;
   using complete other-repository histories must be labeled retrospective
   transfer.
7. Full eligible local history is the primary no-Selection baseline.
   Equal-budget random Selection is a dense calibration of where an algorithm
   lies in the attainable sampling landscape, not a replacement baseline.
8. Fixed-universe score reconstruction, temporal future-Task prediction,
   held-out-repository transfer, and held-out-Agent transfer are different
   claims and must be reported separately.
9. Keep `SelectionBudget.max_task_checks` as an absolute positive integer. It
   matches execution cost. Research reports also show budget-to-history
   fraction; no percentage-budget policy is justified by current evidence.
10. Runtime future cohorts use an explicit `TimeRange`. Task-count blocks are a
    research device for controlling target sample size and must report realized
    calendar span. Use `source-time-cutoff-safe counterfactual`, `strict
    historical replay`, or `strict prospective` instead of the ambiguous
    phrase “calendar-valid”.

## Current Evidence And Claim Boundary

The completed public multi-repository development program contains 500
SWE-bench Verified Tasks, seven wide-portfolio repositories, three
deep-portfolio repositories, and 68 repository-local Origins. The initial
screen used three frozen public Agent result vectors. An outcome-independent
metadata rule later added eight development Agents and preserved six sealed
holdout Agents. Full eligible local history is the primary baseline.
Candidate-minus-full-history differences are negative when Selection helps.

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

The theory-driven extension reached the following decisions:

| Route | Wide macro difference and interval | Decisive evidence | Decision |
| --- | --- | --- | --- |
| Joint response Markov, original 3 Agents | `-0.01911`, `[-0.04715, +0.00442]`; 5/7 favorable | Temporal-null rate `0.100`; leave-one-Agent macro `-0.00043`, only 1/3 favorable | Retire after adversarial audit. |
| Joint response Markov, sealed 8-Agent replication | `+0.00031`, `[-0.01037, +0.01225]`; 4/7 favorable | Deep `+0.00626`; exact original memberships | Retire confirmed; no Agent-panel transfer. |
| Cutoff-aware Agent-invariant difficulty Markov | `-0.00888`, `[-0.03215, +0.01432]`; 3/7 favorable | Better than 97.78% of random; null `0.066`; deep `+0.00920`; leave-one-Agent 6/11 favorable | Retire; gate failed. |
| Adaptive prequential difficulty | `-0.00235`, `[-0.02208, +0.01680]`; 3/7 favorable | Better than 90.28% of random; null `0.194`; deep `+0.00927`; leave-one-Agent 6/11 favorable | Retire and close current-pool temporal search. |
| Difficulty Markov budget–horizon audit | Best of nine cells `-0.00379` at budget 5, horizon 10; 2/5 favorable | 99.97th random percentile, but deep `+0.02550`; leave-one-Agent `+0.01553`, 3/11 favorable; no stable region | Scale tuning does not reopen the candidate. |

The original Joint Markov was temporally retrospective: 9,467 of 19,985
cross-repository training Task uses (`47.37%`) occurred after the target
Origin cutoff, affecting 68/68 Origins. The difficulty experiments enforce
source-time Task cutoffs. They project public Agent labels to Task arrival and
therefore remain counterfactual rather than strict historical replay. A
post-result, outcome-free supply audit found a median of 11 completed
other-repository training Origins from a median of two repositories; four
target Origins have none and 35/68 have fewer than three training
repositories. The self-digested audit is part of
`adaptive-difficulty-results.json`. This is too thin for a credible learned
adaptive gate.

The fixed-budget concern was tested on one common 56-Origin cohort at budgets
5, 10, and 15 and task-count horizons 3, 5, and 10. None of the nine cells
passed the frozen effect, repository, deep, random, control, and Agent-transfer
gate. The only negative wide cell was budget 5, horizon 10 at `-0.00379`; its
deep effect was `+0.02550` and only 3/11 leave-one-Agent directions were
favorable. The fixed ten-Task budget did not cause the route failure.

Task-count horizons also encode different calendar periods. Median spans are
25.7, 39.5, and 75.6 days for 3, 5, and 10 Tasks; the ten-Task maximum is 1,336
days. The runtime already uses an explicit future `TimeRange`. Preserve it and
report realized future Task count and calendar span. Do not add a separate
count-or-duration policy hierarchy.

The six-Agent holdout remains unread. It is reserved for a future mechanism
specified independently of the opened results; it is not permission to keep
searching the current development panel.

In the initial three-Agent screen, equal-budget random Selection has mean wide
difference `+0.0175`, population SD `0.0159`, and mean Monte Carlo standard
error `0.000112` from 20,000 draws. The deep portfolio does not rescue a
candidate: history match is `-0.0014`, semantic centroid is `+0.0168`, and the
fixed recency and coverage rules are also harmful. Full history is
semantically closer to future Tasks than either ALG-007 subset.

The earlier 75-Task, two-Agent SymPy replay remains a precursor, not a second
independent confirmation. Its coverage gain was `0.0100` with interval
`[-0.0363, +0.0152]`. The new portfolio shows why its direction must not be
generalized from one repository.

No Selector is a Runner default. All current results are counterfactual and
panel-conditional; Check maturity is projected to Task arrival and the
Python-heavy source cannot establish language or source-family portability.
The Joint Markov received an outcome-independently allocated eight-Agent
replication and failed. Later mechanisms use all eleven opened development
Agents; six remain sealed. The completed studies and exact identities are
recorded in
[`experiments/2026-07-28-multi-repository-public-study.md`](experiments/2026-07-28-multi-repository-public-study.md)
and
[`experiments/2026-07-28-theory-driven-selector-sprint.md`](experiments/2026-07-28-theory-driven-selector-sprint.md).
The budget and horizon audit is recorded in
[`experiments/2026-07-28-budget-horizon-sensitivity.md`](experiments/2026-07-28-budget-horizon-sensitivity.md).

The external-source audit then measured exact public Task supply and official
Agent-result coverage:

| Source | Repository-local supply | Result decision |
| --- | --- | --- |
| Multi-SWE-bench | 1,632 Tasks; H5 221 Origins/13 repositories; H10 107/11 | Adopt as the primary outcome-open development source; 36 complete public vectors. |
| SWE-bench Full | 2,294 Tasks; legacy H5 419 Origins/11 repositories | Adopt as a secondary depth source; 22 clean vectors, but no independent repository or source-family confirmation. |
| SWE-rebench V2 | 32,079 Tasks; research H5 1,534 Origins/235 raw repositories | Adopt for Task supply and outcome-free research; no complete public result matrix. |
| SWE-PolyBench Full | 2,110 Tasks; research H5 355 Origins/11 repositories | Defer response-derived work; published Full vectors are language-partial. |

The committed inventory digest is
`f4436fd642f6a229cfbf5dfd0a20e4d5175def8dfaa9a46cd830a41d0e335df8`.
Multi-SWE Task time is a GitHub PR-time projection, not native source evidence.
Its import contract digest is
`1e104613012a95fc534dba23d4adac1b7d6a6c10e70537c732f16da3e6f83307`;
the normalized panel digest is
`f2658d12451bdab4108a71cfae5cd5044a5bd312633239c09425378b4b682deb`.
Multi-SWE and Full outcomes were inspected during source choice and are
development data, not sealed confirmation. Detailed identities, overlap,
licenses, timestamp limits, and result coverage are in
[`experiments/2026-07-28-external-benchmark-source-audit.md`](experiments/2026-07-28-external-benchmark-source-audit.md).

All studies recorded here made zero paid benchmark calls. The prior local
embedding run did not make an API call. The previous USD 300 authority remains
closed; the next development study needs no paid authority.

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
| MR-A: fixed outcome-free transfer | A simple semantic or structural rule transfers without fitting target outcomes. | Fixed recency, coverage, and ALG-007 failed the Verified screen. Multi-SWE satisfies the recorded new-source/new-panel trigger; include at most one unchanged ALG-007 transfer replay as a control, not a new parameter search. | `ready` on Multi-SWE; Verified route closed |
| MR-B: offline multi-repository training | Repository-local Origins from several research repositories teach one policy that still consumes only one repository at deployment. | Existing response and difficulty mechanisms failed. Multi-SWE supplies H5 221 Origins/13 repositories and 36 vectors; nominate a mechanism under repository, language, model, harness, and time audits. | `ready` for outcome-open development |
| MR-C: partial pooling | Repository-specific effects share useful structure without erasing heterogeneity. | A newly predeclared mechanism improves held-out-repository loss and calibration over macro averaging and the safe-switch baseline on the new source. | `ready`; keep the implementation direct until a candidate passes |
| MR-D: fixed-universe compression | A small subset reconstructs full historical Agent scores across unseen Agents. | ALG-008 beats equal-budget random and coverage on held-out Agents, reported separately from future-Task MAE. | `ready` on the 36-vector Multi-SWE panel when prioritized |
| MR-E: source and field validity | Generator-conditional gains persist in natural future work. | Frozen later source, then prospective field evidence with an independently defined target frame. | `authority-gated` |
| MR-F: adaptive difficulty regime | Historical predictive score can choose between stationary and dynamic task-difficulty forecasts without future leakage. | Prequential adaptation produced wide `-0.00235`, deep `+0.00927`, and temporal-null rate `0.194`. | `closed` on the current pool |

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
uses repository-first aggregation. The later external audit pinned Full,
PolyBench, Multi-SWE, and SWE-rebench identities and measured their Task,
Origin, timestamp, overlap, license, and outcome limits. Multi-SWE is the next
development source; SWE-rebench is supply-only until an outcome matrix exists.

### Phase 2 — Offline Protocol And Tooling

State: `closed`; completed with zero paid calls.

The direct experiment layer now provides source/plan binding, repository-local
Origin construction, repository-first contrasts, cluster bootstrap intervals,
leave-one-cluster-out sensitivity, wide/deep views, 20,000-draw random
calibration, and compact self-digested outputs. Tests cover the evidence
boundary. The external inventory adds full-byte source verification, resumable
ignored projections, four Origin protocols, and cross-source overlap checks.
The direct Multi-SWE import fixes 39 source paths, 1,632 Task/time rows, 36
configurations, and 2,913 sparse positive outcomes; its evidence validates
offline. Core Result, Task Pool, Selection, and Runner contracts did not
change.

### Phase 3 — Multi-Repository Feasibility Pilot

State: `ready` on an outcome-open external development source.

The public panel establishes portfolio geometry and route-dependent
between-repository variation. Naive normal approximations for a `0.02` effect
range from roughly 3 to 28 repositories across failed routes, so they are not a
confirmatory target. After a new route passes the development gate, its blinded
pilot must measure repository dependence, missingness, cost, and wall time
before the repository count is frozen. The old 44-Origin calculation is not
carried forward. Eleven development Agents now have complete 500-Task public
vectors, and six holdout Agents remain sealed. Multi-SWE now supplies 36
complete public vectors on a separate 1,632-Task denominator. Its outcomes are
open; use it for development and reserve later-source or prospective evidence
for confirmation.

### Phase 4 — Frozen Fixed-Selector Comparison

State: `closed` on the current source and Agent panel.

Full history, coverage, recency, equal-budget random, and both frozen ALG-007
rules were compared across wide and deep views. None earned nomination.

### Phase 5 — Offline Multi-Repository Training

State: `ready` on Multi-SWE; current Verified-pool search remains closed.

Outer repository folds were exercised directly in the experiment layer.
History match improved full history by only `0.0064`; every trend fold chose
zero adjustment, and mean cross-repository drift was harmful. Joint response
Markov failed temporal-null and Agent-transfer audits. Cutoff-aware scalar
difficulty Markov and prequential adaptation also failed the repository,
deep-history, and Agent-direction gates. A common-cohort audit over budgets 5,
10, and 15 and task-count horizons 3, 5, and 10 found no passing cell or stable
region. Add no core training seam until one concrete family first passes the
opened-data nomination gate. Multi-SWE now satisfies the recorded
source-and-panel trigger. Use unchanged ALG-007 once as a transfer control, not
as another parameter search; the primary candidate must be a mechanism derived
independently of the opened Verified results. Do not introduce a meta-pool,
model registry, trainer service, or generic cross-validation framework. The
39-file Multi-SWE Task universe, projected-time sidecar, H5/H10 schedules, and
36-vector allowlist are now frozen. Freeze the source-relative nomination gate
and language/model/harness audit definitions before the next outcome replay.

### Phase 6 — Orthogonal Confirmation

State: `trigger-gated`, then `authority-gated`.

There is no successful route to confirm. The disjoint Agent split is already
frozen: eleven opened development Agents and six sealed holdout Agents. Open
the holdout once only after a candidate passes every development gate, then
require a later source or strict-prospective campaign. Request paid authority
only for the resulting fixed cells. A route that passes repository transfer
but fails Agent transfer is repository-portable and panel-conditional, not
generally valid.

## Entry Gate For The Next Paid Study

There is no active paid plan. Before requesting one, a new mechanism must be
specified without another search over the opened target outcomes and pass the
development gate. The exact counts below apply to the frozen SWE-bench
Verified development panel:

1. wide macro-repository difference at most `-0.01`;
2. at least five of seven repository directions negative;
3. every leave-one-repository-out difference negative;
4. deep macro-repository direction negative;
5. better than at least 75% of equal-budget random draws;
6. improvement over relevant frozen controls;
7. temporal-null as-good-or-better rate below `0.10`;
8. leave-one-Agent macro negative and at least 8/11 Agents favorable.

Do not copy the Verified-specific `5/7` repository or `8/11` Agent counts to
Multi-SWE. Before its first outcome replay, freeze source-relative gates that
retain the same principles: effect at most `-0.01`, favorable direction in at
least 70% of eligible repositories and Agents, negative leave-one-repository
macro effects, negative deep direction, better than 75% of equal-budget random
draws, temporal-null rate below `0.10`, and explicit leave-one-language,
leave-one-model-family, and leave-one-harness-family audits.

After the applicable gate, freeze candidate code and parameters, source and
revision, Origin schedule, budget, missing-cell policy, endpoint identity, and
exclusions before opening an independent holdout. The current six-Agent
SWE-bench split is already frozen; do not reallocate it from observed results.
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
| User-configured time/stratum scenarios | `code-confirmed`; future windows are explicit `TimeRange` values | Preserve explicit lineage and counterfactual labeling. Report realized future Task count and span instead of adding a horizon-policy hierarchy. |
| Multi-repository research report | `code-confirmed` in `examples/multi_repository_study` | Preserve the direct repository-first aggregator; it combines effects, not Tasks. |
| Offline multi-repository fitting | Outer repository folds and target-Origin source-time cutoffs are `code-confirmed` in the experiment layer; projected labels mean the current evidence is counterfactual. Core `train_selector` remains single-pool. | Add a narrow core seam only after a nominated concrete learned family needs it. |
| Repository/fork independence metadata | `code-confirmed` in the study manifest; no core registry | Repeat the source-specific audit for a new portfolio. |
| Repository-cluster uncertainty | `code-confirmed` in the experiment layer | Preserve cluster bootstrap and leave-one-cluster-out summaries. |
| Random calibration | `code-confirmed` at 20,000 deterministic draws | Reuse until a candidate changes the state space; exact enumeration is not needed at current precision. |
| Agent development/holdout allocation | `code-confirmed`: 11 opened development Agents and six project-sealed holdout Agents, allocated from metadata before outcomes | Preserve the six blobs; open once only after every candidate gate passes. |
| Official Result schema normalization | Current three-field schema plus one exact legacy schema amendment for three exact blobs | Do not add permissive field handling; bind any future schema exception to exact identities and unchanged endpoints. |
| Agent-transfer audit | `code-confirmed` leave-one-Agent rematerialization; an evaluated Agent is never a Selector input | Preserve for response-derived Selectors. |
| Local semantic evidence | `code-confirmed` as ignored vectors plus committed identities | ALG-007 failed; add no core embedding service. |
| External benchmark inventory | `code-confirmed` for Verified, Full, PolyBench, and Rebench with exact source bytes and Origin protocols | Preserve source-specific identities; do not introduce a registry. |
| Multi-SWE public Result normalization | `code-confirmed`: fixed 39-file contract, 36-vector allowlist, 1,632 projected times, 2,913 sparse positive cells, and offline evidence validation | Use only in outcome-open research; add no generic source layer. |

Infrastructure prerequisites for another paid selector study are ready. The
external-source audit removes the immediate Origin and Agent-cell supply
blocker for zero-paid development. The remaining blocker is a scientifically
nominated mechanism. No multi-repository product execution path or generic
training service is needed.

## Active Work Ledger

| ID | Priority | State | Next decision or action |
| --- | --- | --- | --- |
| MR-001 | P1 | `closed` | Portfolio and lineage audit committed; repeat only for a new source revision. |
| MR-002 | P1 | `closed` | Repository-first aggregator, cluster interval, and leave-one-cluster-out tests committed. |
| MR-003 | P1 | `closed` | Fixed public plan, full-history contrast, random calibration, exclusions, and results committed. |
| MR-004 | P1 | `trigger-gated` | Multi-SWE supplies the data trigger, but paid sizing remains blocked until a mechanism passes its frozen outcome-open gate. |
| MR-005 / ALG-007 | P1 | `ready` | Run the unchanged rule once on Multi-SWE as a transfer control. Do not tune it or treat it as the primary candidate. |
| MR-006 | P2 | `ready` | ALG-006 remains retired. Give a new ID to one independently motivated partial-pooling mechanism on Multi-SWE; preserve repository-local deployment and source-time cutoffs. |
| MR-007 / RI-188 | P1 | `data-gated` | The 11-development/6-holdout Agent split is frozen. Preserve the six unread blobs until every gate passes. |
| MR-008 | P1 | `data-gated` | A nominated route must exist before later-source or strict-prospective authority is requested. |
| MR-009 / ALG-009 | P1 | `closed` | Joint response Markov failed temporal-null, leave-one-Agent, and sealed eight-Agent replication. |
| MR-010 / ALG-010 | P1 | `closed` | Cutoff-aware difficulty Markov reached wide `-0.00888` but failed effect, repository, deep, and Agent-direction gates. |
| MR-011 / ALG-011 | P1 | `closed` | Prequential adaptation reached wide `-0.00235` and null `0.194`; stop current-pool temporal candidate invention. |
| MR-012 | P1 | `closed` | The frozen budget `5/10/15` by horizon `3/5/10` audit found no passing cell or stable region. Keep absolute budget and future `TimeRange` configurable; do not tune more scales on this opened panel. |
| MR-013 | P1 | `closed` | External-source audit selected Multi-SWE for outcome-open development, Full for depth, Rebench for supply, and deferred response-derived PolyBench work. |
| MR-014 | P1 | `closed` | Direct Multi-SWE response/time research import committed with the 39-file contract, projected-time sidecar, 36-vector allowlist, strict denominator checks, and no generic source registry. |
| RI-125 | P2 | `trigger-gated` | The research import is not a prepared Task Pool. Download, full-byte verify, and certify the 39 source files only when a concrete mechanism needs Task content or a runnable Multi-SWE pool. |
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
| RI-125 | Multi-SWE triggered the response/time import only. A runnable source still needs one explicit prepared-package path and repository-local pools; do not generalize an adapter framework. |
| RI-126 | A synthetic overlay materializes the final solver state as a full commit plus lineage sidecar; add no core overlay abstraction without a concrete adapter. |
| RI-127 | Interactive episodes reopen only with a concrete source and treatment-conditional contract; require a held-out human branch-policy pilot before human-interaction claims. |
| RI-128 | A model-backed Generator owns its endpoint, authority, and provenance inside its adapter; add no generic model service. |
| RI-130 / RI-139 / RI-140 | Compare Generators only on a common frame and crossed design. Report strata separately; add mixture weights or field claims only with an outer calibration protocol. |
| RI-187 | Preserve the `0.02` full-history margin, paired uncertainty, robustness, random diagnostics, and later-source confirmation as separate gates. |
| RI-189 | Admit immutable embedding projections to core FeatureSnapshot only if ALG-007 first passes transfer gates; add no embedding service. |
| RI-190 / ALG-008 | The development panel now has 11 Agents, so fixed-universe IRT may be planned when that separate estimand becomes a priority. Develop on the 11 opened vectors and do not consume the six-Agent temporal holdout merely to improve reconstruction. |

Items not listed above are closed or superseded for current planning. Their
evidence and identifiers remain recoverable in the archived ledger.
