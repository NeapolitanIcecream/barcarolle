# Zero-Call Offline Selector Study

Date: 2026-07-27.

Status: complete. No network request, model call, or paid call was made.

## Decision

The existing paid data materially advanced the project, but it did not establish
the project's rolling-origin research claim.

It produced four decisions:

1. Do not backdate the 2026 certified Checks or Results. They cannot form valid
   2016–2023 core rolling-origin evidence.
2. Reject the current duration-stratum instantiation of ALG-002 for this source.
   Parameter search does not rescue it.
3. Keep ALG-001 and ALG-004 as conservative analysis rules. In all eight
   eligible outer blocks they retained the coverage fallback and avoided the
   losses incurred by raw choice and ALG-003.
4. Nominate the boring coverage rule against a frozen random seed bank for a
   new strict-prospective study. This is a future hypothesis, not a default or a
   claim from the current data.

## Frozen question

The preregistered question was whether a ten-Task benchmark selected from
history predicted the next five chronological Tasks better than fixed
baselines. The loss was `future_pass_rate_mae`: for each of the two frozen
Agents, take the absolute difference between selected-history and future pass
rate, then average across Agents.

The source was fixed before outcome inspection:

- one certified 75-Task SymPy SWE-bench Verified slice;
- 54 patch-path dependency clusters;
- base replicate zero for Terra-high and mini-high;
- 15 initial historical Tasks;
- twelve disjoint five-Task future blocks;
- a ten-Task selection budget;
- coverage, random seed 5, recency, unweighted and weighted stratified
  forecast, and equal rank mixture;
- ALG-001, ALG-003, and ALG-004 evaluated only on the last eight blocks after
  four prior blocks existed;
- 10,000 Origin-block bootstrap resamples with seed `20260722`;
- 5,000 repeat-noise views with seed `20260727`.

The primary contrast was weighted stratified minus coverage. Support required
at least `0.02` lower macro-Origin MAE and a paired interval wholly below zero.

## Contract failure before outcomes

The source-contract check found that all 75 `CheckRecord` values have
`check_material_available_at=2026-07-25T14:00:00Z`, while Task source times run
from 2016-09-15 through 2023-02-05.

The ordinary `build_rolling_origin` path was run for all twelve planned
historical cutoffs. Every Origin had:

- zero mature historical Task/Check refs;
- 15 through 70 censored historical refs;
- zero mature future refs;
- five censored future refs.

Rewriting Check, Result, Feature, or Origin timestamps would manufacture the
availability claim that the core contract correctly withholds. Amendment 1
therefore downgraded the remaining work to a historical Task-order diagnostic.
Amendment 2 corrected a one-character Task Pool SHA-256 transcription error;
all scientific choices remained unchanged and per-Task outcomes were still
unopened.

Consequently, no number below is a `RollingOriginRecord`, `MetricRecord`, or
strict-prospective result. The valid terminal state for the original question
is `invalid_or_insufficient_evidence`.

## Historical Task-order diagnostic

Lower is better.

| Fixed rule | Macro-Origin MAE |
| --- | ---: |
| coverage | 0.1833 |
| recency | 0.2042 |
| equal rank mixture | 0.2167 |
| random seed 5 | 0.2250 |
| weighted stratified forecast | 0.2369 |
| unweighted stratified forecast | 0.2417 |

The preregistered weighted-stratified contrast failed:

- weighted stratified minus coverage: `+0.0536`;
- paired Origin-block interval: `[-0.0605, +0.1628]`;
- weighted stratified was better in 3 blocks, tied in 2, and worse in 7.

The direction was unfavorable for each Agent:

| Agent | Coverage MAE | Weighted-stratified MAE |
| --- | ---: | ---: |
| Terra-high | 0.1750 | 0.2209 |
| mini-high | 0.1917 | 0.2529 |

This is a source-conditional rejection of the current configuration, not a
proof that stratification can never work.

## Adaptive rules

The adaptive rules had eight eligible outer blocks.

| Rule | Outer-block MAE | Behavior |
| --- | ---: | --- |
| coverage fallback | 0.2125 | fixed baseline |
| ALG-001 | 0.2125 | retained coverage 8/8 |
| ALG-004 | 0.2125 | retained coverage 8/8 |
| ALG-003 | 0.2375 | worse than coverage by 0.0250 |
| raw mean choice | 0.2500 | switched once and paid 0.3000 extra loss |
| hindsight fixed-candidate oracle | 0.0875 | non-deployable diagnostic |

ALG-001 and ALG-004 did not demonstrate an improvement, but their safety gate
worked: neither promoted a noisy candidate. This is useful negative evidence
for keeping the gate and against deploying a raw empirical winner.

ALG-003 was not stable. Across mixture seeds 5, 17, and 29, its one-standard-
error outer difference from coverage ranged from `-0.04375` to `+0.0250`.
One favorable seed is therefore not a usable gain.

## Why the stratified mechanism failed

The duration strata were associated with outcome difficulty in this slice:

| Declared duration stratum | Tasks | Terra pass rate | mini pass rate |
| --- | ---: | ---: | ---: |
| 1–4 hours | 6 | 0.167 | 0.000 |
| 15 minutes–1 hour | 43 | 0.698 | 0.605 |
| under 15 minutes | 25 | 0.840 | 0.800 |
| over 4 hours | 1 | 1.000 | 0.000 |

That association did not make future stratum mix a sufficient prediction
mechanism:

- mean selected-versus-future composition TV was `0.4167` for coverage but
  `0.3000` for stratified selection;
- post-stratification weighting reduced TV from `0.3000` to `0.2886`;
- weighting retained mean effective sample size `9.83/10`;
- the maximum mean selected weight was only `1.10`;
- the cap never activated.

Coverage had worse composition fidelity yet lower outcome MAE. The weighted
rule improved composition slightly but not outcome prediction. Within-stratum
Task choice and unmodeled temporal/outcome structure dominated the proposed
mix correction.

The 36-point stratified sensitivity grid produced only 18 distinct realized
behaviors because caps 2, 3, and 4 were all inactive. Its best macro MAE was the
primary configuration's `0.2369`; no grid point beat coverage. Further tuning
of alpha, trailing window, cap, or seed on these outcomes would be
outcome-driven overfitting.

## Adversarial checks

### Run-level noise

The 22 preselected repeated Tasks generated 5,000 diagnostic outcome views by
drawing one available scoreable replicate for each Agent×Task.

- weighted stratified minus coverage was always positive; its 2.5–97.5%
  sensitivity range was `[+0.0220, +0.0588]`;
- coverage minus the five-seed random-bank mean was always negative; its range
  was `[-0.0475, -0.0233]`;
- ALG-001 retained coverage in every view.

These ranges condition on the repeated subset and are not sampling confidence
intervals.

### Dependency

The primary future blocks were disjoint in Tasks, not dependency clusters:

- 45 distinct clusters appeared in the 60 future Tasks;
- 7 clusters spanned multiple future blocks;
- 19 future Tasks had a cluster already present in history;
- one cluster appeared in five future blocks.

The ordinary Origin-block interval is therefore descriptive, not a clean
independent-cluster inference.

The preregistered first-Task-per-cluster sensitivity retained 54 Tasks and
eight disjoint future blocks. Coverage MAE was `0.1813`; weighted stratified
was `0.2952`, a difference of `+0.1140` for the weighted rule. Removing cluster
recurrence strengthens the unfavorable direction.

### Block size

After the primary result, an adversarial diagnostic used every previously
identified viable future-block size: 3, 4, 5, 6, and 8 Tasks. Coverage beat
random seed 5 and weighted stratification at every size. Coverage beat recency
at four sizes and lost at size 4. This supports coverage as a candidate, not a
universal winner.

## What useful signal remains

Coverage was the preregistered fallback, not the primary candidate. Its
post-primary comparisons are exploratory:

- coverage minus random seed 5: `-0.0417`, interval
  `[-0.0917, +0.0083]`;
- coverage minus the mean of seeds 5, 17, 29, 43, and 71: `-0.0383`, interval
  `[-0.0767, -0.0042]`;
- all five individual random macro MAEs were worse than coverage;
- coverage beat the random-bank mean in every repeat-noise view.

The seed-bank comparison is the best next prospective hypothesis because it
does not depend on one lucky random draw. It remains post-primary,
source-conditional, and affected by cluster recurrence.

There is also substantial theoretical headroom:

| Diagnostic | Macro-Origin MAE |
| --- | ---: |
| all historical Tasks, no budget | 0.1933 |
| coverage | 0.1833 |
| hindsight best registered fixed rule per block | 0.0917 |
| hindsight ten-Task joint-outcome subset oracle | 0.0375 |

The oracle rows use future outcomes and are not deployable. They show that the
ten-Task budget is not the main mathematical limit; current pre-origin
features and decision rules fail to identify much of the available subset.

## Prospective campaign sizing

Using the exploratory coverage-versus-random-bank effect:

- normal approximation: 25 independent Origin blocks for 80% power;
- empirical resampling: 21 blocks;
- conservative planning count: 25;
- five new mature Tasks per block;
- two frozen Agents;
- the first coverage-plus-five-random union covers all 15 initial Tasks;
- later Task Results are reusable after each future block matures.

This implies 140 unique Tasks and 280 Agent calls. Reusing the exact cost
distribution from the completed model study gives:

- median planning estimate: `$86.47`;
- sum-of-Agent-p90 planning estimate: `$187.21`.

These values are neither authorization nor a provider quote. They assume the
same harness, model pricing, task-length profile, cache behavior, and no
additional operational failures. More Origins may be required when dependency,
repository, and source heterogeneity are modeled honestly.

## Next research decision

Do not spend more money or tune the same algorithms on these 75 outcomes.

When new Task supply and API authority exist, preregister a strict-prospective
campaign with:

- coverage as candidate;
- the frozen five-seed random-bank mean as primary fallback contrast;
- at least 25 non-overlapping mature five-Task Origins;
- dependency-cluster blocking and per-repository/source reporting;
- Terra and mini retained as the two-Agent treatment panel unless a new
  calibration replaces them before the campaign;
- a preselected 20–30% repeat subset;
- a later immutable Task Pool snapshot at each future window;
- no hyperparameter choice from current or outer-future outcomes.

If collecting 25 independent Origins is infeasible, the honest result is that
the claim remains unresolved. Overlapping windows or retrospective timestamp
projection must not be substituted for missing prospective evidence.

## Reproduction and artifact policy

Committed artifacts:

- `examples/offline_selector_study/study-plan.json`;
- `examples/offline_selector_study/study-amendment-1.json`;
- `examples/offline_selector_study/study-amendment-2.json`;
- `examples/offline_selector_study/study.py`;
- `examples/offline_selector_study/study-results.json`.

The result snapshot is self-digested and stores aggregate Origin losses,
diagnostics, source digests, and audit counts. It stores no per-Task outcome,
prompt, completion, transcript, solver workspace, verifier workspace, hidden
material, or credential.

The ignored Task Pool, Agent, schedule, and Result sources are bound by exact
SHA-256. The implementation freezes every diagnostic Selection before opening
the Result file, independently recomputes all 972 Selector–Origin metric
calculations, and checks history membership and future-block uniqueness.
