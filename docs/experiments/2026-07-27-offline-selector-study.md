# Zero-Call Offline Selector Study and Public Replay

Date: 2026-07-27.

Status: complete. No network request, model call, or paid call was made.

## Decision

The existing paid data supports a bounded counterfactual rolling-origin result.
It does not establish a strict-prospective result.

1. Keep the published 2026 Check and Result timestamps unchanged. Under that
   source-observation view, all twelve historical Origins are fully censored.
2. Permit user- or adapter-configured Task attributes, including Task and Check
   material times, to affect algorithms. Freeze them in a new Task Pool
   scenario with explicit lineage and evidence class.
3. Under the `label_at_task_arrival` counterfactual scenario, the public
   Selection, Result Matrix, and Metric APIs produce twelve scoreable Origins
   and reuse all 150 base Agent Results by exact cache identity.
4. Reject the current duration-stratum ALG-002 configuration for this source.
   Its predeclared MAE is worse than coverage by `0.0536`.
5. Keep coverage as a source-conditional prospective candidate. It is not a
   Runner default.

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

## Source-observation negative control

The source-contract check found that all 75 `CheckRecord` values have
`check_material_available_at=2026-07-25T14:00:00Z`, while Task source times run
from 2016-09-15 through 2023-02-05.

The ordinary `build_rolling_origin` path was run for all twelve planned
historical cutoffs. Every Origin had:

- zero mature historical Task/Check refs;
- 15 through 70 censored historical refs;
- zero mature future refs;
- five censored future refs.

Overwriting those published records or calling projected times source-attested
would make a false provenance claim. Amendment 1 therefore retained this view
as an invalid core path and allowed only a transparent Task-order diagnostic.
Amendment 2 corrected a one-character Task Pool SHA-256 transcription error.

The user then clarified that imported Task attributes must be allowed to affect
algorithms. Amendment 3 froze a zero-call correction before the public replay:

- retain the published Task Pool and Results byte-for-byte;
- keep the source-observation view as a negative control;
- derive a new `label_at_task_arrival` scenario where each Check material time
  equals its bound Task material time;
- label that scenario `user_configured_counterfactual`, not source-attested or
  strict-prospective;
- run ordinary public RollingOrigin, FeatureSnapshot, SelectorInput, Selection,
  Result Matrix, and Metric APIs;
- retain every disagreement with the earlier diagnostic.

This distinction is the contract: algorithm-visible time is configurable;
evidence strength comes from its lineage and eligibility mode.

## Public counterfactual replay

The scenario changed Check maturity, not Task arrival order. The
source-observation view had zero scoreable Origins; the configured scenario had
twelve. All twelve public history and future cohorts matched the frozen
diagnostic exactly.

Every one of the 150 base Agent×Task Results:

- retained its original Result ID and digest;
- matched the scenario Task, Check, Agent, and execution cache identity;
- was physically observed after the historical Task arrival;
- entered only selected or future matrices after the Selection was frozen.

Lower is better.

| Public fixed rule | Macro-Origin MAE |
| --- | ---: |
| coverage | 0.1833 |
| recency | 0.2042 |
| equal rank mixture | 0.2125 |
| random seed 5 | 0.2250 |
| weighted stratified forecast | 0.2369 |
| unweighted stratified forecast | 0.2417 |

For coverage, random, recency, and both stratified rules, all 60
Selector×Origin memberships and MAEs matched the transparent diagnostic. The
equal rank mixture exposed one numerical defect in the public implementation:
left-to-right binary64 addition could perturb a mathematical tie before the
Task ID tie-break. The public implementation now uses `math.fsum`.

Compared with the frozen diagnostic, stable summation changed mixture order at
four Origins, membership at one Origin, and MAE at one Origin by `-0.05`.
Mixture macro MAE changed from `0.2167` to `0.2125`. The disagreement was
retained; the diagnostic was not edited.

The public replay establishes that, within this configured SymPy scenario,
selection policy affects how closely a ten-Task benchmark approximates the
next five Tasks. Coverage had lower observed MAE than random seed 5 and recency.
It does not establish that the projected times are historical facts, that
coverage is universally best, or that any rule will win on a later
strict-prospective Task Pool.

## Historical Task-order diagnostic

The original diagnostic remains frozen. Its equal-mixture row uses the earlier
left-to-right sum and is retained for audit.

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

If collecting 25 independent Origins is infeasible, the strict-prospective
claim remains unresolved. A labeled counterfactual scenario remains valid for
algorithm development, but it cannot be relabeled as prospective evidence.

## Reproduction and artifact policy

Committed artifacts:

- `examples/offline_selector_study/study-plan.json`;
- `examples/offline_selector_study/study-amendment-1.json`;
- `examples/offline_selector_study/study-amendment-2.json`;
- `examples/offline_selector_study/study-amendment-3.json`;
- `examples/offline_selector_study/study.py`;
- `examples/offline_selector_study/study-results.json`;
- `examples/offline_selector_study/public_replay.py`;
- `examples/offline_selector_study/public-replay-results.json`.

Both result snapshots are self-digested. The public snapshot stores scenario
lineage, cohort and selection membership digests, public aggregate losses,
exact Result-reuse counts, and every diagnostic disagreement. Neither snapshot
stores per-Task outcomes, prompts, completions, transcripts, workspaces, hidden
material, or credentials.

The ignored Task Pool, Agent, schedule, and Result sources are bound by exact
SHA-256. The diagnostic independently recomputes its 972 Selector–Origin metric
calculations. The public replay separately constructs 12 Origins, 72
Selections, 144 matrices, and 72 MAE metrics. Two complete public replays
produced byte-identical sanitized results.
