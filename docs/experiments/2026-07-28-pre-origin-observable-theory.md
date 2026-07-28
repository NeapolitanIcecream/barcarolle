# Pre-Origin Observable Theory Sprint

Date: 2026-07-28.

## Decision

Freeze `THY-001 Fixed-Half-Life Module Change Pressure` as a data-gated theory.
It defines a forecast of a repository's next module composition from Git
history available at the Origin. It is not a Selector and has not been
empirically supported.

The strongest challenger is structural parent-planning state frozen by the
Origin that forecasts Tasks whose source-attested
`task_material_available_at` falls after the cutoff. Leaf creation or link time
is not a substitute for Task arrival, and the parent snapshot must not contain
the future Task's solver-visible material. Differential upstream nightly-CI
failure is retained only as a source-specific challenger for repositories that
exercise unreleased dependencies.

Do not replay any route on the opened Multi-SWE or SWE-bench Verified outcomes.
No opened outcome, hindsight membership, sealed holdout, paid call, embedding
call, Generator change, or new runtime service was used in this sprint.

## Research Contract

The question is whether an observable process outside the current Task and
Agent-result histories can forecast the target repository's next Task mix
before the Origin.

Success in this sprint means:

1. at least three mechanisms with distinct causal stories;
2. an exact, falsifiable information set and transform for one mechanism;
3. a source-admission rule that prevents solved patches, later issue state, and
   future Git reachability from entering the forecast;
4. an independent test plan that can retire the theory without another search
   over opened benchmark outcomes.

This sprint does not require a favorable score. It stops at a theory and source
gate because no admissible independent Task-plus-Result panel is currently
available. The first empirical stage may test an organic repository-process
proxy, but that evidence cannot be relabeled as benchmark Task-mix or Selection
evidence.

## Why Another Observable Is Necessary

The previous audit established three different facts:

- exact hindsight subsets can represent future Agent responses;
- other Agents strongly describe same-Task difficulty;
- fixed embeddings and full-versus-recent response composition do not forecast
  the next Task cohort.

The missing variable is the repository's future work composition. A useful new
route must therefore observe a process that can change before new Task material
exists. Reweighting past Tasks by age, semantic similarity, response trend, or
recent arrival would rename a tested family rather than introduce a new
information path.

`THY-001` instead observes code-change pressure. Parent-level work intent
observes maintainer commitments. Differential nightly CI observes ecosystem
compatibility pressure. These mechanisms can move before a future benchmark
Task is available.

## External Evidence And Its Limit

Change-history research supports a forward association between past change
activity and later faults or code changes:

- Graves et al. used information available by 1994-03-31 to predict faults from
  1994-04-01 through 1996-03-31. Change history predicted the later module
  fault distribution better than size alone in their system
  ([paper](https://cs.uwaterloo.ca/~m2nagapp/courses/CS846/1171/papers/graves_tse98.pdf),
  [DOI](https://doi.org/10.1109/32.859533)).
- Catolino et al. evaluated change prediction in sequential three-month
  windows across 20 systems. Evolution-history features were useful, while
  developer features added signal and restructuring weakened the
  evolution-history model
  ([paper](https://fpalomba.github.io/pdf/Journals/J12.pdf),
  [DOI](https://doi.org/10.1016/j.jss.2018.05.003)).
- Ostrand et al. predicted next-release fault-prone files from prior releases,
  reporting that the top 20% of files contained 71% to 92% of faults in the
  studied systems ([DOI](https://doi.org/10.1109/TSE.2005.49)).

These papers motivate the direction. They do not validate a one-year half-life,
the transform below, a generated benchmark's Task supply, or future Agent
responses. Organic commits and faults are not Barcarolle Tasks.

Branch treatment is not interchangeable. Kovalenko et al. found consistent,
project-dependent differences between first-parent and full file histories,
with modest downstream performance differences in their studied techniques
([paper](https://research.tudelft.nl/en/publications/mining-file-histories-should-we-consider-branches/),
[DOI](https://doi.org/10.1145/3238147.3238169)). The v1 graph-difference
estimand below is therefore explicit.

Change-coupling studies show that files changed together in the past can
suggest related changes
([Zimmermann et al.](https://www.st.cs.uni-saarland.de/papers/icse2004/icse.pdf);
[Ying et al.](https://www.cs.ubc.ca/~murphy/papers/hipikat/predicting-changes-tse.pdf)).
Their main use is conditional on knowing at least one current file. That seed
is unavailable when forecasting an unconditional future Task mix, so
co-change is not promoted as a standalone route.

## Candidate Decision Table

| Mechanism | Pre-Origin observable | Predictive reason | Importer and Generator boundary | Main leakage or failure | Smallest admissible test | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| Fixed-half-life module change pressure | Non-merge ancestors reachable from the Origin commit, frozen path-to-module map, and per-module diff mass | Recently changing modules may accumulate adaptation and defect pressure | High feasibility from local Git; feature extraction is Generator-free, but alignment with a generated Task population is Generator-specific | Refactors, vendored code, squash/cherry-pick history, new modules, merge-conflict changes, branch reachability, and commit-to-Task mismatch | Four-block organic-process falsification only; Task-mix testing remains unready until a source-specific horizon, Origin schedule, minimum Task count, label rule, and gate are frozen | **Freeze as `THY-001`; data-gated** |
| Parent-level work-intent graph | Timestamped structural state of Epic, parent, milestone, or planning nodes before future Task material becomes available | Maintainer commitments may precede a later cluster of Tasks | Feasibility unresolved; requires a complete event archive and source-native parent/component mapping; Task alignment is Generator-specific | Backfilled links, edited current state, incomplete archives, inconsistent link use, and parent text that contains future Task material | Not test-ready: audit archive schema and completeness, then freeze the transform, horizon, no-parent and historical-component baselines, Origins, and gate | Retain as strongest challenger |
| Differential upstream nightly CI | Repeated unreleased-dependency failures while ordinary stable-dependency jobs pass | An upstream-development-only failure may precede compatibility work | Prospectively feasible only after pinning the repository, workflow revision, attempt policy, job taxonomy, and local metadata archive; Task alignment is Generator-specific | Flakes, reruns against one upstream artifact, workflow edits, limited retained history, and strong source specificity | Feasibility screen only: freeze an episode key, eligible attempts, Task classifier, 14-day horizon, calendar-matched green controls, power minimum, and episode-clustered statistic | Retain only for eligible sources |
| Release-calendar phase | Public release calendar, tags, and pre-Origin beta/RC phase | Scheduled transitions can concentrate compatibility and release work | High, but only for projects coupled to a declared cadence; Task alignment remains Generator-specific | Pure seasonality, slips, sparse cycles, and post-release annotation | Predeclare at least five cycles and compare post-phase component mass with full-history and same-season controls | Deprioritize; overlaps the closed temporal family |
| Unconditional co-change pressure | Historical module-pair graph without a known future seed | Coupled modules may recur together | High from Git; feature extraction is Generator-free, but Task alignment is Generator-specific | Published evidence is mainly conditional on a known changed file; dense hubs and refactors dominate | Forecast future pair mass and beat independent marginal, full-history, and recent-history controls in every block | Retire as standalone; allow only as a later ablation of `THY-001` |
| Open leaf issue queue | Issue state, assignee, labels, and links after issue creation | Commitments predict which existing issues will resolve | High for Jira/GitHub; Task status depends on source protocol | When a leaf issue's Task material is already available by the Origin, later resolution predicts status rather than future cohort membership | None for a resolution-time cohort under the current `task_material_available_at` contract | Reject for Task-mix prediction |
| Open pull-request queue | Open PR metadata and review state | Review progress predicts near-term merge | High | The PR normally contains both Task-adjacent text and a candidate solution patch | None without a different estimand and solver-visibility contract | Reject |
| Raw CI failure or advisory count | Any recent red job or dependency advisory | Failures and advisories may trigger work | Medium; Task alignment is Generator-specific | Flakes, irrelevant failures, missing exposure, and advisories that never become Tasks | Must first isolate an exposure-specific contrast | Reject broad form |

The parent-intent distinction is material. A leaf issue may or may not be a
Task at creation; cohort membership is determined only by the source-attested
`task_material_available_at`. A parent planning node can be useful only when
its frozen structural state predates future Task arrival and does not expose
the future Task's solver-visible material. Issue creation, linking, resolution,
and merge times are not substitutes for Task arrival.

## Prior-Family Comparison

| Prior family | Existing result | Relation to `THY-001` |
| --- | --- | --- |
| Fixed recency and local trend | Failed or selected zero adjustment on the opened Verified panel | `THY-001` does not use Task age or Task-arrival rate. Its input is repository change mass. The trailing-90-day Git baseline tests whether the theory collapses to recency. |
| Fixed semantic representation | ALG-007, ALG-012, and ALG-013 failed transfer or outcome gates | No embedding, issue text, or semantic distance enters `THY-001`. |
| Response regime and partial pooling | Joint Markov, difficulty Markov, adaptation, and ALG-014 failed temporal or transfer gates | No Agent outcome enters the forecast. Future Result use begins only after the Task-mix gate passes on an independent source. |
| Hindsight response support | Strong on Multi-SWE but leaked by construction | No hindsight membership or future response vector is used. |
| Pure seasonality | Previously audited and not independently nominated | Release phase remains a challenger, not a renamed primary route. |
| Co-change | Useful when a current seed file is known | The unconditional pair graph is retired unless marginal module pressure first passes and co-change is frozen as an ablation. |

The route is new at the information-set level, not proven at the estimand
level. Code-change pressure can predict organic commits while failing to
predict imported or generated Tasks. The source-alignment gate below is
therefore mandatory.

## Frozen Theory Contract: THY-001 v1

### Prediction

At an Origin with repository base commit \(O\), the decayed Git distribution
below predicts the next Task-module distribution better than each frozen
control. Stage A tests only the analogous organic-change proxy.

The half-life is fixed at 365.25 days. It is a round, independently chosen v1
parameter, not an estimate from the target source and not a claim about the
parameter fitted by Graves et al. No half-life search is permitted in v1.

### Source-visible inputs

The forecast may use only:

1. the Git object graph reachable from \(O\);
2. parent diffs for reachable non-merge commits;
3. committer timestamps on those commits;
4. a finite path-to-module function fixed from repository documentation and
   the tree at \(O\);
5. a frozen exclusion list for generated, vendored, lock, and fixture paths.

The module map must include `OTHER`, assign every non-excluded path to exactly
one label, and have a recorded digest. For Stage A, construct one map and
vocabulary using only documentation and the tree reachable from the earliest
pseudo-Origin \(B_0\). Record its digest before inspecting a later graph
difference, then apply it unchanged at all four Origins and to every target
commit. Later or unrecognized paths map to `OTHER`; later trees and target
paths cannot create or rename labels. `OTHER` does not count toward the
five-module admission requirement.

Module labels and exclusions may differ by source, but they must be frozen
before target blocks or Task outcomes are read. The final repository must
never be timestamp-filtered to reconstruct an Origin; reachability from the
actual Origin commit defines visibility.

An Origin is inadmissible if a reachable eligible ancestor has a committer
timestamp later than \(O\)'s committer timestamp. This strict rule exposes
clock or history anomalies rather than clipping negative ages.

### Transform

Let \(C_e(O)\) be the set of non-root, non-merge commits reachable from \(O\)
whose parent diff contains at least one non-excluded path. Only \(C_e(O)\)
enters the transform.

For each \(c\), the importer runs the equivalent of
`git diff-tree --no-commit-id --numstat -r --no-renames c^ c`, records the Git
version, and treats the reported path as the module-map input. Rename and copy
detection is disabled. A numeric numstat record has
\(w_{cf}=\max(1,a_{cf}+d_{cf})\); a binary record has \(w_{cf}=1\).
For commit \(c\) and module \(m\), define

\[
\Delta_{cm} =
\sum_{f \in F_{cm}} w_{cf},
\]

where \(F_{cm}\) is the set of eligible paths in module \(m\) touched by the
parent diff of \(c\), and let \(M_c=\{m:\Delta_{cm}>0\}\). Let

\[
u_{cm} =
\frac{\log(1+\Delta_{cm})}
{\sum_j \log(1+\Delta_{cj})}
\]

for touched modules and zero otherwise. Each commit therefore contributes one
unit divided across its touched modules, with large diffs compressed.

The decayed pressure and forecast are

\[
H_m(O) =
\sum_{c \in C_e(O)}
2^{-(t_O-t_c)/(365.25\text{ days})} u_{cm},
\]

\[
p_m(O) =
\frac{H_m(O)+1/2}
{\sum_j H_j(O)+|\mathcal M(O)|/2}.
\]

The \(1/2\) term is fixed Jeffreys-style smoothing over the frozen module
vocabulary \(\mathcal M(O)\), including `OTHER`.

For an organic future commit \(d\), the evaluation target is

\[
y_{dm} =
\frac{\mathbf 1[m\text{ is touched by }d]}
{|\{j:j\text{ is touched by }d\}|}.
\]

For a future Task, the analogous vector may be one-hot or split uniformly
across source-native module labels. Its labels must be available when the Task
material arrives. Reference-patch paths, hidden tests, verifier material, and
post-resolution metadata are prohibited.

### Intended output and non-output

`THY-001` outputs the probability vector \(p(O)\). It does not yet choose
Tasks. If Task-mix prediction passes, a separate plan must freeze the
budget-to-stratum allocation and within-stratum choice before any Agent
outcomes are opened. That later algorithm would still select only from the
target repository's eligible local history.

## Independent Test Plan

### Stage 0: source admission

Before computing any future graph difference, publish an ordered
candidate-source list with repository URL, default ref, head SHA, retrieval
time, nominal cutoffs, module-map digest, and exclusion digest. Apply admission
to every listed source, report all failures, and do not replace a failed
repository or block.

For each listed repository:

1. take the latest four complete, consecutive 90-day blocks ending at the
   pinned branch head;
2. walk the pinned first-parent chain and take the first commit encountered
   with committer time at or before each calendar cutoff;
3. define the future commit set by graph difference:
   `ancestors(end) - ancestors(origin)`;
4. require the earliest Origin to have at least 365.25 days and 20 commits of
   eligible reachable history, and require at least 20 eligible future
   non-merge commits and five non-`OTHER` frozen modules with future mass in
   every block;
5. report every exclusion and do not replace a failed block.

Block membership is newly default-branch-reachable Git objects, not commit
timestamp. A side-branch commit first merged after the Origin is a target
observation even if its timestamp predates the Origin. Stage A therefore
forecasts newly mainline-visible change, not work authored during the nominal
90-day interval. Every boundary, including the terminal head, must satisfy the
timestamp-anomaly rule. Seven-day diagnostic clusters are graph differences
formed with the same first-parent boundary rule.

Barcarolle itself fails this source gate. At audited commit
`26b4c41ccefee6027c8b13b0491d71e4a31616ce`, it had 360 reachable commits
(311 first-parent commits) spanning 2026-04-17T15:49:42+08:00 through
2026-07-28T22:08:06+08:00. That span cannot provide four non-overlapping
90-day blocks. No shorter schedule was substituted.

### Stage A: organic repository-process falsification

For each admitted repository and Origin, let
\(D=C_e(\operatorname{end})\setminus C_e(O)\) under the frozen map and
exclusions. Compute `THY-001` once and score every \(d\in D\) with

\[
L = -\frac{1}{|D|}\sum_{d \in D}\sum_m y_{dm}\log p_m(O).
\]

Freeze these baselines:

- uniform module mass;
- current eligible LOC share;
- all-history module-touch share;
- trailing-90-day module-touch share;
- no-decay log-churn share.

Every baseline uses the same frozen vocabulary, exclusions, and \(1/2\)
pseudo-count. Full-history touch is proportional to
\(1/2+\sum_{c\in C_e(O)}\mathbf1[m\in M_c]/|M_c|\); trailing-90-day touch
restricts that sum to committer times in the previous 90 days. LOC is the
physical newline count in eligible nonbinary blobs at the Origin. The no-decay
ablation is proportional to
\(1/2+\sum_{c\in C_e(O)}u_{cm}\), which isolates the fixed half-life from the
within-commit transform.

For every admitted repository, Stage A v1 survives its source-specific
falsification screen only if its loss is lower than every baseline in all four
blocks. Report paired resampling of the fixed seven-day graph-difference
clusters only as a conditional target-event diagnostic. Four dependent
temporal blocks do not support a 95% population-generalization claim. A failed
inequality retires v1 for that source; it does not authorize half-life,
module-map, or exclusion tuning.

Surviving Stage A establishes only that the transform forecasts organic module
change under the admitted source screen. It is a required screen, not a
benchmark claim.

### Stage B: generator-conditional Task-mix test with native arrival times

Proceed only with a new source or prospective campaign that supplies:

- source-attested, versioned solver-material snapshots and a
  `task_material_available_at` derivation bound into source-protocol and
  Generator provenance; latest issue state, import time, close time, and merge
  time are inadmissible substitutes;
- a module/component label visible at Task arrival without a solved patch;
- an attested repository commit visible at the Origin cutoff, never a future
  `TaskRecord.base_commit`, resolution commit, or reference-patch commit;
- enough local Origins for a frozen repository-first comparison;
- historical Result availability and an independent complete Agent panel, or a
  strict prospective Result campaign, for any later Selection test.

The later pool must cover the complete frozen future source frame and preserve
Generator behavior, source protocol, and certification configuration. A Jira
leaf-arrival test without certified `TaskRecord`s is only a source-process
proxy.

Persist \(p(O)\), its input digest, and the Origin before opening the later
Task Pool or any future label. Score each Task once. History contains only
Tasks with `task_material_available_at <= as_of_cutoff`; future contains only
Tasks with `task_material_available_at > as_of_cutoff` inside the frozen
`TimeRange`. Construct every history control from that same cutoff-safe cohort.

At each Origin, compare \(p(O)\) with the later Task-module distribution.
Primary controls are full-history Task-module share, trailing Task-module
share, current LOC share, and uniform mass. Use cross-entropy as the primary
composition metric and total variation as a descriptive metric.

Stage B cannot pass or trigger Stage C until an outcome-free, source-specific
preregistration freezes its `TimeRange`, Origins, minimum future-Task count,
module-label rule, baseline formulas and smoothing, and an explicit
all-baseline temporal pass/retire gate. Freeze the source, module map, Origin
schedule, exclusions, controls, and gates before opening future Task labels.

If a Task can be mapped to a module only from its reference patch or verifier
material, the source fails. Hidden Checks and tests, resolved commits or diffs,
and post-resolution metadata are also prohibited. If the Generator's filter
makes its Task supply independent of organic module pressure, the mechanism
fails for that Generator even if Stage A passed.

### Stage C: Selection evidence

Only a passing Stage B can trigger a separate frozen Selection plan. That plan
must:

1. allocate the absolute Task budget across module strata from \(p(O)\);
2. state the deterministic within-stratum rule and undersupply
   redistribution;
3. compare future Agent-score error with full eligible history as the primary
   baseline and equal-budget random Selection as calibration;
4. preserve repository-first, Agent-transfer, horizon, temporal-null, and
   source-family gates;
5. derive exact pass counts from a blinded source-relative pilot rather than
   copying the Verified or Multi-SWE counts.

Opened Multi-SWE and Verified outcomes, the six sealed holdout Agents, and paid
calls remain prohibited until the independent Task-mix and development gates
pass.

## Challenger Feasibility Audit

The Public Jira Dataset establishes that a large issue-change/link archive
exists. Its paper describes 2.7 million issues, 32 million changes, 9 million
comments, and 1 million links across 16 Jira installations and 1,822 projects
([paper](https://arxiv.org/abs/2201.08368),
[dataset concept DOI](https://doi.org/10.5281/zenodo.5882881)).
The 2025-06-23 archive is CC BY 4.0 and exposes a 5,813,135,238-byte ZIP in the
[Zenodo record](https://zenodo.org/api/records/15719919), with reported MD5
`02f85309d966092ea130ca0797aea795`. The archive was not downloaded, so its
schema and the availability and completeness of time-versioned parent
mutations remain unverified.

A point audit during the 2026-07-28T14:24Z minute observed Apache Jira Epic
`HDDS-16000` and five timestamped `Epic Child` mutations
([API endpoint](https://issues.apache.org/jira/rest/api/2/issue/HDDS-16000?fields=key,issuetype,project,components,status,created,updated,fixVersions,issuelinks&expand=changelog)).
Follow-up issue reads gave:

| Child | Child created | Link mutation |
| --- | --- | --- |
| `HDDS-12365` | 2025-02-18T11:36:45.609+0000 | 2026-07-27T20:29:24.146+0000 |
| `HDDS-15944` | 2026-07-22T22:21:58.148+0000 | 2026-07-27T20:29:44.531+0000 |
| `HDDS-12671` | 2025-03-23T07:57:33.276+0000 | 2026-07-27T20:30:02.035+0000 |
| `HDDS-16002` | 2026-07-27T20:44:41.612+0000 | 2026-07-27T20:45:11.107+0000 |
| `HDDS-16001` | 2026-07-27T20:38:19.329+0000 | 2026-07-27T20:46:13.433+0000 |

The Epic was created at 2026-07-27T20:28:41.553+0000. The compact, sorted-key
JSON projection has top-level keys `epic_created`, `epic_key`, and `links`;
each link has `child_created`, `child_key`, and `link_created`, in table order.
It has SHA-256
`2bfdcc57e616afd7d6cba4ce4907db9499f1c40a1e283246658a1733ca84a5ca`.
Every child existed before its link mutation; three also predated the Epic.
The Epic predated two child creations, but their structural relation was not
recorded until after each child existed. This proves a timestamped event shape,
not linked parent state before `task_material_available_at`, corpus
completeness, or prediction.

Issue-link use is heterogeneous: a multi-project Jira study reported average
link coverage of 36%, with wide project variation. Its role analysis suggests
that Epic and Subtask links are likely created deliberately by stakeholders in
planning roles
([study](https://link.springer.com/article/10.1007/s00766-023-00406-x)).
Any parent-intent importer must therefore audit event completeness and link
semantics per source.

Adjacent industrial evidence shows that project and test progress can forecast
weekly defect inflow in another project
([study](https://www.sciencedirect.com/science/article/abs/pii/S0950584907001085),
[DOI](https://doi.org/10.1016/j.infsof.2007.10.001)). It does not validate a
Jira parent graph or a benchmark Task-mix mechanism.

GitHub exposes issue events and event types
([API](https://docs.github.com/en/rest/issues/events?apiVersion=2022-11-28),
[event types](https://docs.github.com/en/rest/using-the-rest-api/issue-event-types)),
but current API state is not a complete historical archive. Mining research
documents deletion, rename, and current-state hazards
([Kalliamvakou et al.](https://etc.leif.me/papers/Kalliamvakou2015a.pdf)).
[GH Archive](https://www.gharchive.org/) retains public event payloads from
2011, but a source-specific completeness audit would still be required.

Differential nightly CI has a documented ecosystem mechanism. Scientific
Python SPEC 4 recommends testing downstream packages against development
versions of dependencies
([SPEC 4](https://scientific-python.org/specs/spec-0004/)); NumPy gives
downstream guidance for development-version CI
([guide](https://numpy.org/devdocs/dev/depending_on_numpy.html)). The proposed
contrast deliberately requires ordinary stable jobs to pass so it does not
collapse to raw CI failure count. Neither source connects such failures to
future benchmark Tasks. GitHub build logs and artifacts default to 90-day
retention
([documentation](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/remove-workflow-artifacts));
retrospective job history, attempt identity, and external archival therefore
remain source gates.

## Approach Registry

| Route | Evidence gathered | Status |
| --- | --- | --- |
| Module change pressure | Strict-forward change/fault evidence, exact Git transform, branch and source-alignment audit | Selected as `THY-001 v1`; untested and data-gated |
| Parent-level work intent | Public Jira archive metadata, one live event-shape counterexample to pre-link ordering, link-coverage evidence | Retained challenger; archive schema, completeness, transform, and Task alignment unresolved |
| Differential upstream nightly CI | Ecosystem development-version testing contract; no Task-incidence evidence | Retained source-specific challenger; episode definition and historical source not pinned |
| Release phase and seasonality | Public schedules can be observed, but the mechanism overlaps a closed temporal family | Deprioritized |
| Unconditional co-change | Strong conditional literature, missing unconditional seed | Retired as standalone |
| Leaf issues and open PRs | Observable but already Task- or solution-adjacent | Rejected under the current Task boundary |
| Raw CI, crash, advisory, and dependency counts | Broad signals lack an exposure-specific causal contrast or complete source | Rejected in broad form |

## Claim Boundary And Next Action

This sprint mechanically specifies a distinct Git-derived hypothesis and an
organic-process falsification screen. Importability and Task-mix falsifiability
remain source-gated. Two challenger mechanisms remain researchable but are not
test-ready. No result establishes predictive value, Task-source alignment,
Agent-score improvement, portability, or a product requirement.

The next authorized action is outcome-free source admission for Stage A and a
search for an independent Task source with versioned material, source-attested
arrival, and a module label available at that arrival. Do not implement a core
FeatureSnapshot field, source adapter, trainer, registry, or Selector until a
concrete source passes its gate.
