# Research Ledger

Last reviewed: 2026-07-29.

Status: archived research record; superseded by `research-improvement-backlog.md`.

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
11. When complete Agent outcomes already exist, the Selection gate uses
    pass-rate MAE directly. AUC, Brier loss, embedding loss, and response-
    coordinate loss are mechanism diagnostics. They may order paid evidence
    acquisition when outcomes do not exist, but they do not replace or suppress
    an affordable outcome evaluation.
12. Evidence executors validate both source bytes and declared logical
    identities before Selection. A post-freeze correction is an additive,
    self-bound amendment that records prior evidence access; it does not rewrite
    the parent plan. Result terminal states use the plan's frozen vocabulary,
    while mechanism-specific labels remain diagnostics.
13. Cached-target compression and unseen-target Selection are different
    information contracts. A cached method may use only cutoff-safe Results
    from the exact Agent identity; it cannot support a claim about a new or
    changed Agent. If target pass-rate MAE depends only on selected success
    count, call the result scalar calibration or quantization, not Task-content
    prediction.
14. A known future cohort count may be an input to a finite-horizon
    cached-target estimator, but it must be declared before Selection. When the
    count is unknown, use an H-blind rule and report the realized count after
    evaluation. Runtime `TimeRange` remains the user-facing horizon contract;
    do not infer a privileged Task count from future arrivals.
15. Public same-configuration outcomes without native Result availability
    timestamps or a complete production Agent fingerprint can test a
    retrospective cached-result counterfactual only. They do not establish
    that a production cache was cutoff-safe or identity-complete.
16. A finite-H cached action is identified by Result identity and availability,
    Selection budget, declared future count, loss, and estimand. Treat the
    plug-in median as a grid-aware baseline, not Task prediction. Current
    evidence is `grid_dominant`; do not sweep more budgets, horizons, priors,
    ties, or smoothing values on the opened panel.

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
| ALG-012 Multi-SWE minimax semantic herding | H5 `-0.00027`, `[-0.00415, +0.00334]`; 8/13 favorable | 81.59th random percentile, but deep `+0.00080`, H10 `+0.00241`, harness 1/3 and language 3/7 favorable; semantic MMD² worsens in 13/13 repositories | Retire; gate failed. |
| Multi-SWE exact budget-ten hindsight support | H5 `-0.03264`; 13/13 favorable | 48.46% loss reduction; deep `-0.03423`; H10 `-0.02562`, 11/11 favorable; 328/328 MILPs certified optimal | Budget-ten capacity supported; pre-Origin identification remains the bottleneck. |
| ALG-013 Multi-SWE Response-Contrast Projection | Pass-rate MAE H5 `+0.001729`, 6/13 favorable; H10 `+0.005890`, 3/11 favorable | The earlier AUC and z-loss gates failed; direct outcome replay now shows the candidate also loses to full history. | Reject on primary MAE; no proxy false kill. |
| ALG-014 Multi-SWE Response-Composition Shrinkage | Pass-rate MAE H5 `+0.001992`, 4/13 favorable; H10 `+0.008170`, 1/11 favorable | Static AUC `0.9121`; proxy forecast differences `+0.000992`/`+0.001855`; direct MAE has the same harmful direction. | Reject on primary MAE; no proxy false kill. |
| THY-002S Brier Projection Coreset | Pass-rate MAE H5 `-0.002594`, 7/11 favorable; H10 `+0.002943`, 7/11 favorable | H5 misses the frozen `-0.005` effect and has bootstrap upper `+0.004724`; H10 reverses. | Fails the frozen outcome gate; no proxy false kill. |
| THY-003 Registry-Dated Dependency-Lag Nearest Regime | Continuous Brier H5/H10 `-0.000223`/`-0.000404`; budget-ten `+0.009057`/`+0.000879` | Source passed at 97.47% coverage; H5 continuous interval crosses zero, deep reverses, materialization fails, temporal null `0.9496` | `closed`; two byte-identical Stage-A runs, no Agent outcomes opened |
| ALG-015C cached prequential assembly | Pass-rate MAE H5 `-0.002235`; H10 `-0.000246` | H5 misses ALG-007 by `0.000019`; the adaptive forecast and final Selection both lose to the stationary cached control. | `bounded_inconclusive`; remove the adaptive layer from the cached KISS route. |
| ALG-015U unseen prequential assembly | Pass-rate MAE H5 `-0.000530`; H10 `+0.000854` | Continuous forecasts lose to full history; H10 reverses. | `bounded_inconclusive`; do not tune the expert family on this frame. |
| ALG-016U unseen shared-change-point assembly | Pass-rate MAE H5 `-0.003335`, 9/13 favorable, random midrank `0.9925`; H10 `+0.001105` | H5 is the best unseen-target point estimate and beats ALG-007 by `0.001081`, but that paired repository interval crosses zero and H10 reverses. | Preserve as an H5 development challenger; no numeric progress or nomination. |
| Cached-target stationary exact control | Pass-rate MAE H5 `-0.004365`, interval `[-0.005984, -0.002773]`; H10 `-0.003774`, `[-0.005533, -0.001932]` | 13/13 and 10/11 repositories favorable; gain is exact success-count quantization to `q/10`, not Task identity or recency. | Retain as the H-blind cached-target baseline. |
| ALG-018C Jeffreys finite-horizon median | Pass-rate MAE H5 `-0.014096`; H10 `-0.004094` | Versus the H-blind cached control: H5 `-0.009731`, interval `[-0.013081, -0.006442]`; H10 `-0.000320`, interval `[-0.002109, +0.001565]`. | Superseded by the matched grid audit; retain the family as a cached-result grid-aware baseline, not a general Selector. |
| Matched B-by-H finite-horizon audit | Plug-in minus H-blind: B5/H5 `-0.000248`; B5/H10 `+0.000467`; B10/H5 `-0.010171`; B10/H10 `-0.000684` | Only B10/H5 has an interval below zero, `[-0.015755, -0.004738]`. B5/H5 and B10/H5 plug-in selected rates are identical in all 3,852 rows; wrong-horizon actions worsen H5/H10 by `+0.005789`/`+0.001834`. | `grid_dominant`; ALG-018C-P is a contract-specific baseline. Close cached scalar/grid search on this panel. |

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

Multi-SWE provides a stronger capacity check. A separately frozen exact
response-pattern MILP reduced H5 loss by `48.46%` (`-0.03264`) with 13/13
repositories favorable and H10 loss by `48.51%` (`-0.02562`) with 11/11
favorable. All 328 Origin solves were certified optimal and every deep
repository was favorable. This rules out budget-ten response-representation
capacity as the current explanation on this opened estimand. It does not show
that the optimal subsets can be identified before future outcomes.

ALG-013 and ALG-014 then separated response representation from temporal
identification. Fixed embeddings did not acquire stable cross-repository
response contrast: future AUC was `0.5530` with a repository bootstrap lower
bound below chance, while a complete-history diagnostic was `0.5104` with
corrected negative-control rate `0.55`. In contrast, the leave-one-
configuration response-composition coordinate had static AUC `0.9121`, but its
prequential full/recent forecast plus one-Task cross-repository prior worsened
H5 loss by `+0.000992` and H10 by `+0.001855`. Thus the current bottleneck is
forecasting the target repository's next Task mix from observable pre-Origin
evidence, not budget-ten capacity or absence of same-Task response structure.

A post-decision methodology audit bypassed the surrogate stops without changing
the frozen algorithms. ALG-013 and ALG-014 both lose to full history on direct
H5 and H10 pass-rate MAE. THY-002S improves H5 by `0.002594`, reaches random
midrank `0.93485`, and has 24/36 favorable configurations, but misses its
required `0.005` effect, has a bootstrap interval crossing zero, and worsens
H10 by `0.002943`. The surrogate-gate order was wrong because the public
outcomes were already available; it did not change any candidate decision.
An adversarial audit found two miscopied logical digests, missing logical
binding checks, an inconsistent terminal label, and omitted control contrasts
in the committed summary. Amendment `1d25336e…1a833` fixes the evidence
contract without changing the scientific payload. The accepted raw runs are
byte-identical at `1eda7fe1…fc928`; the committed evidence digest is
`5f6098f3…fff39`. The plan, exact numbers, controls, and remaining Stage-C
specification gaps are in
[`experiments/2026-07-29-surrogate-gate-pass-rate-mae.md`](experiments/2026-07-29-surrogate-gate-pass-rate-mae.md).

A separately frozen prequential-response portfolio then evaluated
AdaNormalHedge and shared-run-length BOCPD before joining future outcomes.
ALG-016U is the best unseen-target H5 point estimate: MAE falls from
`0.067348` to `0.064013`, a `-0.003335` contrast and `0.9925` random midrank.
Every H5 leave-one-repository-out contrast to full history stays favorable,
but the repository interval crosses zero and H10 reverses to `+0.001105`.
ALG-015C improves both horizons by `-0.002235`/`-0.000246`, but its adaptive
layer loses to the simpler cached stationary control at both. No preregistered
candidate meets the combined numeric-progress rule.

The frozen `cached_full_target` control is the stronger finding. It maps the
same public target configuration's historical success rate to the nearest
feasible `q/10`.
H5/H10 differences are `-0.004365`/`-0.003774`; both repository-bootstrap
intervals exclude zero, every leave-one-repository-out aggregate is favorable,
and random midranks are `0.9986`/`0.99995`. The specific Task identities and
recency tie do not affect target pass-rate MAE after `q` is fixed. The result
is therefore cached-Agent scalar calibration under aligned Selection/future
grids, not evidence that Task content predicts the future. Plan
`f1517fd0…58c84b`, lock `f4dcec2e…1a91d`, byte-identical result
`04a2475d…186487`, corrected compact evidence `e6c766fe…4d2e9`, and the complete claim
boundary are in
[`experiments/2026-07-29-prequential-response-assembly.md`](experiments/2026-07-29-prequential-response-assembly.md).

A second theory-first plan froze `ALG-018C` after the H-blind result but before
materializing its memberships. It minimizes exact posterior-predictive
absolute loss for a declared future cohort size and projects that action onto
the feasible budget-ten success-count grid. H5 MAE is `0.053252`, improving
full history by `0.014096` (`20.93%`) and the H-blind control by `0.009731`
(`15.45%`). The latter paired repository interval excludes zero, 12/13
repositories are favorable, and every leave-one-repository-out aggregate is
favorable. H10 MAE is `0.048713`, improving full history by `0.004094` but the
H-blind control by only `0.000320`; that paired interval crosses zero and only
5/11 repositories are favorable.

The frozen plug-in Binomial ablation is within `0.000117` of Jeffreys at H5 and
`0.000015` at H10. The main mechanism is therefore finite-horizon L1/grid
alignment, not the prior. On this zero-heavy panel, H5 selected success count
is always 0, 2, or 4 while H10's incremental gain nearly vanishes. This is a
retrospective same-configuration cached-result finite-cohort counterfactual,
not evidence that real Result availability or a complete Agent fingerprint
was cutoff-safe, and not semantic or temporal Task prediction. Plan
`6602a349…264b7`, lock
`10e28322…be4b`, byte-identical result `63662482…e045`, and the full boundary
are in
[`experiments/2026-07-29-finite-horizon-cached-assembly.md`](experiments/2026-07-29-finite-horizon-cached-assembly.md).

The matched follow-up removes the H5/H10 frame confound by using the same 107
H10 Origins and the first five future Tasks for H5. Plug-in-minus-H-blind
contrasts are `-0.000248`, `+0.000467`, `-0.010171`, and `-0.000684` for
B5/H5, B5/H10, B10/H5, and B10/H10. Only B10/H5 has a repository-bootstrap
interval wholly below zero. B5/H5 and B10/H5 produce identical selected rates
row by row; B10 merely lets the H-blind control choose odd tenths that an H5
future rate cannot attain. Horizon-swap diagnostics also worsen H5/H10 by
`+0.005789`/`+0.001834`.

The frozen terminal state is therefore `grid_dominant`, not general
finite-horizon support. Amendment `80dd4596…618c` corrects one exact-zero
repository direction count with a `1e-15` tolerance; corrected lock
`03c2dbfb…fcaa5` and byte-identical result `d7d92c6d…b630` preserve every MAE,
interval, diagnostic, and terminal decision. Compact evidence is
`32c388c89…e909a`. Full evidence is in
[`experiments/2026-07-29-finite-horizon-grid-audit.md`](experiments/2026-07-29-finite-horizon-grid-audit.md).

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
The first frozen Multi-SWE mechanism, exact evidence identities, failed gates,
and random-landscape interpretation are in
[`experiments/2026-07-28-multi-swe-semantic-selector.md`](experiments/2026-07-28-multi-swe-semantic-selector.md).
The separately frozen exact capacity diagnostic and its leakage boundary are in
[`experiments/2026-07-28-multi-swe-budget-ten-capacity.md`](experiments/2026-07-28-multi-swe-budget-ten-capacity.md).
The frozen ALG-013/ALG-014 plans, corrected response-vector negative control,
independent audit limits, and current-source stop boundary are in
[`experiments/2026-07-28-pre-origin-signal-audit.md`](experiments/2026-07-28-pre-origin-signal-audit.md).
The independently specified `THY-001` information set, external evidence,
candidate comparison, source-alignment gate, and falsification plan are in
[`experiments/2026-07-28-pre-origin-observable-theory.md`](experiments/2026-07-28-pre-origin-observable-theory.md).

`THY-001R Fixed-Half-Life Module Commit Pressure` is `closed`. Its
outcome-free Multi-SWE and Full-minus-Verified test passed source admission and
byte reproduction but lost to full Task history on both H5 and H10. A
Git-vocabulary-only audit revision preserved the failure. Do not tune its
half-life, smoothing, path map, horizon, source, or repository frame.

`THY-002 Generator-Calibrated Module Exposure` passed its frozen Task-mix
gate. H5/H10 candidate-minus-full-history Brier contrasts are
`-0.006562`/`-0.006107`, with intervals below zero and 27/40 and 28/40
favorable repositories. Git-only and yield-only ablations also lose at both
horizons. Two raw runs are byte-identical at `449e10c1…6ac8`; compact digest is
`26233a42…aa31`. The 5,365-Task, 40-repository evidence remains a
projected-timeline association, not native causality or Agent-score evidence.
The contract, diagnostics, result, and claim boundary are in
[`experiments/2026-07-29-generator-calibrated-exposure.md`](experiments/2026-07-29-generator-calibrated-exposure.md).

`THY-002S Brier Projection Coreset` is `closed` on the frozen Multi-SWE
frame. Its deterministic budget-ten Selection improved full history by
`0.019114` at H5 and `0.015294` at H10, reached random midrank `1.0` at both
horizons, and differed from the continuous forecast by less than `0.0005`.
H10 passed, but the H5 forecast and Selection repository intervals had upper
bounds `+0.006686` and `+0.005761`; both H5 front gates therefore failed.
Two accepted runs were byte-identical at `8ec69bb2…a98e`, and compact digest
`8243d4cb…42a6` binds the zero-outcome resource ledger and outcome-free
result. A separate post-decision audit then reused the exact memberships and
the already-open public panel. H5 pass-rate MAE improved full history by
`0.002594`, below the frozen `0.005` requirement, with interval
`[-0.009243, +0.004724]`; H10 worsened by `0.002943`. The frozen outcome gate
therefore also fails. Retire this mapping without tuning the gate, source,
budget, horizon, or algorithm. Details are in
[`experiments/2026-07-29-generator-calibrated-selection.md`](experiments/2026-07-29-generator-calibrated-selection.md).

`THY-003 Registry-Dated Dependency-Lag Nearest Regime` is `closed`. Source
admission passed on the exact 9-repository/119-Origin frame: 82,279/84,418
state-package cells resolved (`97.47%`), every Origin was supported, and two
offline runs reproduced byte-identically. The continuous forecast had small
favorable wide H5/H10 directions (`-0.000223`/`-0.000404`) but H5 uncertainty
crossed zero and deep results reversed. Budget-ten materialization worsened
full history by `+0.009057`/`+0.000879`; temporal-null rate was `0.9496`.
Corrected result `68acfaa5…ccd9` and compact evidence `90456efc…1c17` retire
the route. The first execution was invalidated because its identity loader read
patches before membership freeze; the corrected raw-input reconstruction
preserves the same scientific payload. No opened outcome, sealed holdout, or
paid replay is authorized. Details are in
[`experiments/2026-07-29-controlled-cold-start-pre-origin-theory.md`](experiments/2026-07-29-controlled-cold-start-pre-origin-theory.md).

All studies recorded here made zero paid benchmark calls. The prior local
embedding run did not make an API call. The previous USD 300 authority remains
closed. There is no active Agent-outcome or paid study.

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
| MR-A: fixed outcome-free transfer | A simple semantic or structural rule transfers without fitting target outcomes. | Fixed recency, coverage, and ALG-007 failed on Verified. On Multi-SWE, ALG-012 reached H5 `-0.00027` and 81.59th random percentile but failed task-space, H10, deep, harness, and language gates; unchanged ALG-007 reached `-0.00225` and also failed. | `closed` on current opened panels; an independently motivated observable may advance theory, not authorize replay |
| MR-B: offline multi-repository training | Repository-local Origins from several research repositories teach one policy that still consumes only one repository at deployment. | ALG-013 and ALG-014 lose to full history on direct H5/H10 pass-rate MAE; their earlier surrogate failures did not hide a valid candidate. | `closed` for replay on current opened outcomes; an independent observable may advance theory only, while empirical nomination needs a new evidence boundary |
| MR-C: partial pooling | Repository-specific effects share useful structure without erasing heterogeneity. | ALG-014's equal-repository, one-Task prior worsened the frozen candidate; the local no-prior ablation was only `1.28%` better at H5 and reversed at H10. | `closed` for this bounded response-composition mechanism; do not tune prior mass |
| MR-D: fixed-universe compression | A small subset reconstructs full historical Agent scores across unseen Agents. | ALG-008 beats equal-budget random and coverage on held-out Agents, reported separately from future-Task MAE. | `ready` on the 36-vector Multi-SWE panel when prioritized |
| MR-E: source and field validity | Generator-conditional gains persist in natural future work. | Frozen later source, then prospective field evidence with an independently defined target frame. | `authority-gated` |
| MR-F: adaptive difficulty regime | Historical predictive score can choose between stationary and dynamic task-difficulty forecasts without future leakage. | Prequential adaptation produced wide `-0.00235`, deep `+0.00927`, and temporal-null rate `0.194`. | `closed` on the current pool |
| MR-G / THY-001R: module change pressure | Reachable Git change pressure predicts the module composition of the target repository's next work cohort. | The frozen Multi-SWE and Full-minus-Verified Task-mix test lost to full Task history at both horizons; the Git-only vocabulary audit preserved the result. | `closed`; no tuning or outcome replay |
| MR-H: parent work intent | Timestamped structural parent state predicts later Task-component mass before source-attested Task material becomes available. | Admit only a complete event archive with source-native parent/component mapping, versioned material, and native Task arrival; issue creation, linking, resolution, and merge times are not substitutes. | `data-gated` challenger; archive schema, event completeness, transform, and Task alignment unresolved |
| MR-I / THY-002: generator-calibrated exposure | Future generated Task mass follows current Git exposure multiplied by a module's historical Task-per-exposure propensity. | H5/H10 improve over full history by `0.006562`/`0.006107`; all full/Git/yield gates pass on 40 Rebench repositories. | `task-mix-pass`; retain as an observable, not a production Selector |
| MR-J / THY-002S: Brier projection coreset | A deterministic budget-ten subset that projects local historical Tasks onto the frozen THY-002 forecast preserves its future Task-mix advantage and then predicts future Agent response. | Outcome-free H5 mapping improved Brier by `0.019114`; direct pass-rate MAE improves only `0.002594`, its interval crosses zero, and H10 worsens `0.002943`. | `closed` on this frame; both the original front gate and the post-decision frozen outcome gate fail |
| MR-K / THY-003: registry-dated dependency lag | The direct npm dependency-lag regime at an Origin persists into the next Task cohort and identifies comparable historical Task regimes. | Frozen Stage A passed source admission but failed full-history, deep, materialization, LORO, and temporal-null gates. | `closed`; do not tune or open Agent outcomes |
| MR-L: forecast-to-budget-k materialization | A discrete subset can preserve explicitly frozen pre-Origin forecast moments better than nearest-Task ranking without using future labels. | THY-003 moved only `0.00572` continuously from full history but `0.06329` after budget-ten materialization; 95/119 H5 cohorts were all zero. This diagnoses a general discretization question, not a rescue result. | `theory-gated`; derive on a new evidence boundary before implementation |
| MR-M / ALG-018C/P: cached finite-horizon calibration | Complete same-configuration historical Results can be compressed for a declared finite future count by minimizing predictive pass-rate MAE on the feasible Selection grid. | Matched B5/B10 by H5/H10 audit finds stable incremental gain only at B10/H5; equal-grid cells do not support a general correction. Current source does not prove Result availability or full Agent identity. | `grid-baseline-retained`; close scalar/grid search and require a new evidence boundary for broader claims |

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
configurations, and 2,913 sparse positive outcomes. The ALG-012 study
full-byte verified all 39 source objects, projected 1,632 issue texts, bound
local embeddings, and recorded deterministic task-space and outcome replays.
Core Result, Task Pool, Selection, and Runner contracts did not change.

### Phase 3 — Multi-Repository Feasibility Pilot

State: `closed` for nomination-oriented search on current opened outcomes.

The public panel establishes portfolio geometry and route-dependent
between-repository variation. Naive normal approximations for a `0.02` effect
range from roughly 3 to 28 repositories across failed routes, so they are not a
confirmatory target. ALG-013 and ALG-014 completed the planned
representation/forecast factorization without nominating a Selector. An
independently specified observable may advance theory design but cannot reopen
these panels. Empirical nomination requires a source with native availability
time, an independent complete panel/source family, or a prospective campaign.
That blinded pilot must measure repository dependence, missingness, cost, and
wall time before the repository count is frozen. The old 44-Origin calculation
is not carried forward. Eleven development Agents now have complete 500-Task
public vectors, and six holdout Agents remain sealed. Multi-SWE supplies 36
complete public vectors on a separate 1,632-Task denominator. Its outcomes are
open; use it for development and reserve later-source or prospective evidence
for confirmation. ALG-012 used this source and failed its frozen task-space and
outcome gates.

### Phase 4 — Frozen Fixed-Selector Comparison

State: `closed` on the current source and Agent panel.

Full history, coverage, recency, equal-budget random, and both frozen ALG-007
rules were compared across wide and deep views. None earned nomination.

### Phase 5 — Offline Multi-Repository Training

State: `closed` for ALG-012 and current Verified-pool search; budget-ten
capacity is established, but no predictive mechanism is nominated.

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
36-vector allowlist are frozen. ALG-012 then failed: H5 outcome difference was
`-0.00027`, H10 was `+0.00241`, and the deep, harness, language, and semantic
task-space gates failed. The unchanged ALG-007 transfer control reached H5
`-0.00225` with 7/13 favorable repositories but reversed at H10. Do not tune
either route. The separately frozen exact hindsight diagnostic then reached
H5 `-0.03264` with 13/13 repositories favorable and H10 `-0.02562` with 11/11
favorable. All 328 solves were certified optimal. Budget ten is not the current
representational bottleneck; pre-Origin identification is. Do not train on the
hindsight memberships or use them to select the next mechanism.

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
Multi-SWE. Its first replay froze source-relative gates before outcomes:
effect at most `-0.01`; at least 10/13 H5 and 8/11 H10 repositories favorable;
negative leave-one-repository, deep, and H10 directions; at least 75th random
percentile; improvement over controls; temporal-null rate below `0.10`; and
explicit language, model, provider, harness, and configuration directions.
ALG-012 failed this gate. Preserve the gate principles for a genuinely new
mechanism, but derive exact counts from its frozen eligible cohort.

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
| Local semantic evidence | `code-confirmed` as 1,632 ignored vectors, committed identities, fixed memberships, and deterministic MMD²/outcome replays | ALG-007 and ALG-012 failed; add no core embedding service or representation search. |
| Pre-Origin response signal audit | `code-confirmed` complete-repository RCP holdout, leave-one-configuration response composition, prequential experts, shared-change-point forecasts, matched cached-target finite-horizon actions, direct pass-rate MAE, byte reproductions, controls, and compact evidence | Unseen-target ALG-016U remains an H5-only challenger. Plug-in finite-H is the cached grid-aware baseline; matched audit closes scalar/grid search. Surrogates remain diagnostics. |
| Pre-Origin repository-process theory | `THY-001R` is retired; `THY-002` passed Task mix but `THY-002S` failed outcomes; `THY-003` passed source admission but failed Stage-A prediction/materialization | Preserve the closed routes and direct example evidence; add no core service or opened-outcome replay. A new route needs an independent theory and evidence boundary. |
| External benchmark inventory | `code-confirmed` for Verified, Full, PolyBench, and Rebench with exact source bytes and Origin protocols | Preserve source-specific identities; do not introduce a registry. |
| Multi-SWE public Result normalization | `code-confirmed`: fixed 39-file contract, verified 1.60 GB source projection, 36-vector allowlist, 1,632 projected times, 2,913 sparse positive cells, and offline evidence validation | Use only in outcome-open research; this is still not a runnable Task Pool and needs no generic source layer. |

Infrastructure prerequisites for another paid selector study remain available,
but no mechanism is nominated. The cached finite-H baseline needs no new Result
Store or core service; runtime admission remains caller-gated. No
multi-repository product execution path or generic training service is needed.

## Active Work Ledger

| ID | Priority | State | Next decision or action |
| --- | --- | --- | --- |
| MR-001 | P1 | `closed` | Portfolio and lineage audit committed; repeat only for a new source revision. |
| MR-002 | P1 | `closed` | Repository-first aggregator, cluster interval, and leave-one-cluster-out tests committed. |
| MR-003 | P1 | `closed` | Fixed public plan, full-history contrast, random calibration, exclusions, and results committed. |
| MR-004 | P1 | `trigger-gated` | Multi-SWE supplies the data trigger, but paid sizing remains blocked until a mechanism passes its frozen outcome-open gate. |
| MR-005 / ALG-007 | P1 | `closed` | Unchanged Multi-SWE transfer reached H5 `-0.00225` with 7/13 favorable repositories and H10 `+0.00216`; do not tune it. |
| MR-006 / ALG-014 | P2 | `closed` | The direct response-composition partial-pooling mechanism found strong static structure but worsened H5/H10 future loss. Do not tune its prior mass or expert threshold on opened outcomes. |
| MR-007 / RI-188 | P1 | `data-gated` | The 11-development/6-holdout Agent split is frozen. Preserve the six unread blobs until every gate passes. |
| MR-008 | P1 | `data-gated` | A nominated route must exist before later-source or strict-prospective authority is requested. |
| MR-009 / ALG-009 | P1 | `closed` | Joint response Markov failed temporal-null, leave-one-Agent, and sealed eight-Agent replication. |
| MR-010 / ALG-010 | P1 | `closed` | Cutoff-aware difficulty Markov reached wide `-0.00888` but failed effect, repository, deep, and Agent-direction gates. |
| MR-011 / ALG-011 | P1 | `closed` | Prequential adaptation reached wide `-0.00235` and null `0.194`; stop current-pool temporal candidate invention. |
| MR-012 | P1 | `closed` | The frozen budget `5/10/15` by horizon `3/5/10` audit found no passing cell or stable region. Keep absolute budget and future `TimeRange` configurable; do not tune more scales on this opened panel. |
| MR-013 | P1 | `closed` | External-source audit selected Multi-SWE for outcome-open development, Full for depth, Rebench for supply, and deferred response-derived PolyBench work. |
| MR-014 | P1 | `closed` | Direct Multi-SWE response/time research import committed with the 39-file contract, projected-time sidecar, 36-vector allowlist, strict denominator checks, and no generic source registry. |
| MR-015 / ALG-012 | P1 | `closed` | Outcome-free minimax semantic herding beat most random subsets but failed full-history, H10, deep, harness, language, and ALG-007 control gates; no nomination. |
| MR-016 | P1 | `closed` | Exact hindsight reached H5 `-0.03264` and H10 `-0.02562`, every repository favorable, and 328/328 certified optimal solves. Capacity is supported; no Selector was nominated. |
| MR-017 / ALG-013 / ALG-014 | P1 | `closed` | Post-decision direct MAE replay gives ALG-013 H5/H10 `+0.001729`/`+0.005890` and ALG-014 `+0.001992`/`+0.008170`. Preserve the proxy diagnostics, but use primary MAE for future decisions. |
| MR-018 / THY-001R | P1 | `closed` | Original plan `10b4fcb2…8459` and two byte-identical runs retire the candidate: Multi H5/H10 vs full Task history `+0.17572`/`+0.21704`; Full-minus-Verified `+0.08751`/`+0.08807`. Audit revision `dd3e420d…2d44` removes the shared-vocabulary ambiguity and preserves failure. |
| MR-019 | P2 | `data-gated` | Parent-level work intent remains a planning-source challenger. Require complete timestamped planning-node history, versioned Task material, and a module/component label available before source-attested Task arrival; do not substitute issue creation, linking, resolution, merge, open leaf issues, or PRs. |
| MR-020 / THY-002 | P1 | `task-mix-pass` | Plan `0fe42fc1…1c69`; raw/reproduction `449e10c1…6ac8`; H5/H10 full-history contrasts `-0.006562`/`-0.006107`. Retain the mechanism under its projected-time claim boundary. |
| MR-021 / THY-002S | P1 | `closed` | Exact outcome audit: H5 `-0.002594`, bootstrap upper `+0.004724`; H10 `+0.002943`. Frozen outcome gate fails. Keep original `retire_mapping`; do not rescue-tune this frame. |
| MR-022 / THY-003 | P1 | `closed` | Source admission passed; continuous H5/H10 were `-0.000223`/`-0.000404`, budget-ten `+0.009057`/`+0.000879`, and temporal null `0.9496`. Preserve corrected result `68acfaa5…ccd9`; do not rescue-tune or open Agent outcomes. |
| MR-023 | P2 | `theory-gated` | Derive a general forecast-to-budget-k materialization rule with an explicit visible-attribute contract and independent evidence boundary. Do not tune against THY-003's opened future labels or add core infrastructure before nomination. |
| MR-024 / ALG-015C / ALG-015U | P1 | `closed` | Frozen AdaNormalHedge candidates do not beat their appropriate controls across H5/H10. Preserve the deterministic evidence; do not tune their expert menu on this panel. |
| MR-025 / ALG-016U | P1 | `development-retained` | Shared-run-length BOCPD is the best unseen-target H5 point estimate (`-0.003335`) but reverses at H10 (`+0.001105`). Reopen only with an independently specified mechanism or evidence boundary. |
| MR-026 / ALG-018C/P | P1 | `closed` | Matched plan `8388fc58…4b1d` terminates `grid_dominant`: only B10/H5 has stable incremental gain over H-blind. Keep plug-in as the KISS grid-aware baseline; do not sweep B/H, prior, tie, or smoothing on this panel. |
| RI-125 | P2 | `trigger-gated` | The exact 39 source objects and issue-text projection are full-byte verified. A runnable prepared Task Pool still needs solver/verifier material and source-specific certification when a concrete campaign requires it. |
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
| RI-125 | Multi-SWE now has an exact response/time/content research projection. A runnable source still needs one explicit prepared-package path and repository-local pools; do not generalize an adapter framework. |
| RI-126 | A synthetic overlay materializes the final solver state as a full commit plus lineage sidecar; add no core overlay abstraction without a concrete adapter. |
| RI-127 | Interactive episodes reopen only with a concrete source and treatment-conditional contract; require a held-out human branch-policy pilot before human-interaction claims. |
| RI-128 | A model-backed Generator owns its endpoint, authority, and provenance inside its adapter; add no generic model service. |
| RI-130 / RI-139 / RI-140 | Compare Generators only on a common frame and crossed design. Report strata separately; add mixture weights or field claims only with an outer calibration protocol. |
| RI-187 | Preserve the `0.02` full-history margin, paired uncertainty, robustness, random diagnostics, and later-source confirmation as separate gates. |
| RI-189 | Admit immutable embedding projections to core FeatureSnapshot only if ALG-007 first passes transfer gates; add no embedding service. |
| RI-190 / ALG-008 | The development panel now has 11 Agents, so fixed-universe IRT may be planned when that separate estimand becomes a priority. Develop on the 11 opened vectors and do not consume the six-Agent temporal holdout merely to improve reconstruction. |

Items not listed above are closed or superseded for current planning. Their
evidence and identifiers remain recoverable in the archived ledger.
