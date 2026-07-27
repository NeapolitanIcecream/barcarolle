# Selection Landscape and Learnability Study

Date: 2026-07-27.

Status: development evidence complete; no Selector promoted.

## Decision

The existing 75-Task SymPy counterfactual replay is useful for algorithm
development, but it does not yet establish Barcarolle's selection claim.

- The primary baseline is the complete eligible historical benchmark without
  Selection. Its macro-Origin future-pass-rate MAE is `0.1933`.
- Coverage selects ten Tasks and has MAE `0.1833`. The observed improvement is
  `0.0100`, below the frozen `0.02` practical threshold; its descriptive paired
  interval is `[-0.0363, +0.0152]`.
- Coverage is materially better than a typical equal-budget random Selection,
  but a random Selection is as good or better with probability `12.91%`.
- The history can represent the future outcome vector well: continuous support
  MAE is `0.0250`, and the hindsight discrete ten-Task oracle is `0.0375`.
  Present failure is primarily identification or learnability, not lack of
  support.
- Coverage's contrast with full history changes sign across reasonable future
  block sizes. Removing repeated dependency clusters raises its point gain to
  `0.0167`, but still clears neither promotion gate; repeat-result sensitivity
  has mean gain `0.0071` and no view reaches `0.02`.
- None of the fixed outcome-forecast, semantic-coreset, or mid-difficulty
  candidates clears the practical gate over full history.

The correct terminal state is
`selection_landscape_measured_but_no_candidate_clears_promotion_gate`.
Coverage remains a prospective candidate, not a Runner default.

## Question and claim boundary

For each of twelve rolling Origins, the development scenario exposes the
eligible historical Tasks and hides the next five Task outcomes. A Selector
chooses ten historical Tasks. The primary loss averages, across the two frozen
Agents, the absolute difference between selected-history and future pass rate,
then macro-averages across Origins.

This study opened the previously inspected outcomes and is explicitly
`post_outcome_development`. Its roles are to:

1. compare Selection with the no-Selection benchmark;
2. locate an algorithm inside the full equal-budget random search space;
3. separate Task Pool support from pre-origin identification;
4. retire unproductive mechanisms and nominate the next prospective work.

It cannot confirm strict-prospective performance, manufacture independent
Origins through resampling, or justify choosing a favorable hyperparameter.
Future outcomes are opened only for scoring, support bounds, and null controls,
never as a Selector input.

## Exact equal-budget random landscape

With two binary Agent outcomes, each historical Task belongs to one of four
joint outcome categories. For every Origin, the loss distribution of a
uniformly random ten-Task subset is therefore an exact multivariate
hypergeometric distribution. Convolving the twelve Origin distributions gives
the exact macro-Origin random landscape; no Monte Carlo seed is involved.

| Quantity | Macro-Origin MAE or probability |
| --- | ---: |
| full eligible history, no Selection | `0.1933` |
| coverage | `0.1833` |
| one random Selection, expectation | `0.2150` |
| one random Selection, median | `0.2125` |
| random strictly better than coverage | `9.73%` |
| random equal to coverage | `3.18%` |
| random as good as or better than coverage | `12.91%` |
| fraction of random mass coverage beats, midrank | `88.68%` |

The reciprocal as-good probability is `7.75`: on average, about one of every
7.75 independent random draws is at least as good as coverage. This is useful
calibration. The earlier contrast with random seed 5 is not an artifact of that
one seed, but coverage is also far from exhausting the Task Pool's selectable
signal.

The macro position is not a claim of uniform temporal superiority. Coverage's
Origin-level random midrank is above `50%` in 8 of 12 Origins, but below `50%`
for the four consecutive Origins 6–9. The range is `31.53%` to `97.81%`.
This local regime failure is consistent with the block-size sensitivity below
and is another reason not to promote the aggregate result.

The dense frontier reinforces that conclusion:

| Random-search diagnostic | Expected or conditional mean MAE |
| --- | ---: |
| best 10% of random mass | `0.1701` |
| best 5% | `0.1626` |
| best 1% | `0.1485` |
| expected best of 10 draws | `0.1755` |
| expected best of 100 draws | `0.1523` |
| expected best of 1,000 draws | `0.1358` |

These are hindsight search-space diagnostics, not deployable algorithms. They
provide the denser estimate requested between one random sample and an oracle.

The exact density also explains why the oracle alone is misleading. Its MAE is
`0.0375`, but its probability under uniform equal-budget Selection is only
`2.38e-21`. Probability mass within `+0.02`, `+0.05`, and `+0.10` MAE of the
oracle is approximately `2.13e-15`, `1.05e-8`, and `0.00110`. The Task Pool
contains excellent subsets, but the best endpoint is extremely sparse. Elite
means and best-of-draw curves are the actionable intermediate diagnostics.

The example's deployable random rule reinitializes one fixed seed at every
Origin, so its selections are not independent across Origins. A post-plan
adversarial sensitivity enumerated seeds `0` through `99,999` under that exact
policy. Its mean MAE is `0.21504`, `12.84%` of seeds are as good as or better
than coverage, and coverage's midrank position is `88.77%`. Relative to the
independent exact distribution, the mean changes by `+0.00005` and the as-good
fraction by `-0.00070`. Cross-Origin seed coupling therefore does not explain
the result.

## Support versus learnability

The continuous support calculation projects each future two-Agent pass-rate
vector onto the convex hull of historical joint outcomes. It has macro MAE
`0.0250` and zero loss at 11 of 12 Origins. The discrete hindsight oracle,
which must select exactly ten Tasks, has macro MAE `0.0375` and zero loss at 10
of 12 Origins.

Therefore, the ten-Task budget and observed Task Pool support do not explain
the `0.1833` coverage loss. Most of the gap is between what history can
represent and what pre-origin features can identify. Origin 1 is the principal
support exception; Origin 7 has continuous support but a discrete-budget loss
of `0.15`.

Three outcome-alignment null controls test whether coverage's observed
advantage could arise from accidental alignment:

| Null control | Contrast | One-sided probability |
| --- | --- | ---: |
| unrestricted outcome permutation | coverage minus full history | `0.1834` |
| unrestricted outcome permutation | coverage minus exact-random expectation | `0.1906` |
| sampling-stratum-preserving permutation | coverage minus full history | `0.0716` |
| sampling-stratum-preserving permutation | coverage minus exact-random expectation | `0.0730` |
| all 74 nonzero circular shifts | coverage minus full history | `0.0800` |
| all 74 nonzero circular shifts | coverage minus exact-random expectation | `0.0533` |

The stratum-preserving and circular controls are suggestive, but twelve
dependent development Origins are not enough for confirmation. The controls
do not create new evidence units. All finite randomization probabilities use
the conservative `(b + 1) / (B + 1)` rule that includes the observed
arrangement.

## Adversarial robustness

The primary contrast is not stable to the rolling-Origin aggregation choice:

| Future block size | Initial history | Origins | Coverage minus full-history MAE |
| ---: | ---: | ---: | ---: |
| 3 | 15 | 20 | `+0.0012` |
| 4 | 15 | 15 | `+0.0047` |
| 5 | 15 | 12 | `-0.0100` |
| 6 | 15 | 10 | `-0.0052` |
| 8 | 11 | 8 | `-0.0058` |

Positive values favor full history. No configuration has a `0.02` point gain
or an interval wholly below zero. These are post-plan sensitivity rows, not
five chances to choose the most favorable configuration; they reuse the
configurations frozen in the earlier offline-study sensitivity. A future study
must predeclare the horizon implied by its deployment question and may report
the others only as robustness checks.

The existing Task sequence also has dependency clusters spanning multiple
future blocks. Retaining only the earliest Task in each cluster leaves 54 Tasks
and eight five-Task Origins with no cluster recurrence. Coverage then scores
`0.1813` versus `0.1979` for full history, a gain of `0.0167` with interval
`[-0.0479, +0.0120]`. Cluster recurrence therefore does not explain away the
direction, but the independent view still misses both gates and has fewer
evidence units.

The source study also preselected 5,000 repeat-noise views over 22 Tasks and 44
Agent×Task cells with scoreable repeats. Recomputing the primary contrast gives
a mean coverage gain of `0.0071`, a conditional 2.5%–97.5% range
`[-0.0147, +0.0050]`, and favorable direction in `88.3%` of views. No view
reaches the `0.02` practical threshold. These views vary persisted Agent
outcomes on only the preselected repeat subset; they are sensitivity evidence,
not independent Origins or a confidence interval.

## Candidate mechanisms

### Outcome forecast matching

Each rule forecasts the next outcome vector using only historical two-Agent
outcomes, then chooses a feasible ten-Task joint-outcome composition nearest
that forecast.

Matching the complete historical mean ties coverage at `0.1833`. The best
exponential rules score `0.1917`; recent-window and linear-trend variants are
worse. More window tuning on these outcomes is stopped. Reopen only with a
new reference-Agent panel or a predeclared change-point mechanism.

### Semantic coresets

One endpoint call embedded the 75 frozen Task texts with
`text-embedding-3-small`. Centroid-nearest and facility-location variants used
only pre-origin Task text. The best fixed rules, both using a recent-15
reference frame, score `0.1917`: slightly better than full history, worse than
coverage, and short of the practical gate.

The mechanism diagnostic separates semantic representation from outcome
prediction. Mean selected-to-future embedding-centroid cosine distance is
`0.2296` for coverage. Centroid-recent-15 reduces it to `0.2074`, and
facility-recent-15 to `0.2133`, yet both worsen outcome MAE from `0.1833` to
`0.1917`. Full history has the lowest semantic distance, `0.1694`, but outcome
MAE `0.1933`. Better text-centroid alignment is therefore not a sufficient
proxy for the target outcome on this source.

This is a source-conditional negative result, not a general rejection of
semantic coresets. The approach is motivated by evaluation-unsupervised
facility-location results on much larger and more heterogeneous LLM benchmark
suites. Reopen it on a second Task source or with more independent Origins.

### Semantic-conditioned outcome forecast

A final post-plan mechanism probe tested whether semantic similarity becomes
useful after conditioning historical Agent outcomes. It used four recent
semantic windows, three nearest-neighbor counts, and four fixed softmax
temperatures, then matched the forecast to a feasible historical ten-Task
outcome composition.

The best three realized rules use softmax temperature `1` with windows 5, 10,
or 15 and score `0.1875`. They improve full history by only `0.0058`, lose to
coverage by `0.0042`, and tie coverage's `0.2125` on the last eight Origins.
Higher temperatures and nearest-neighbor variants are worse. This probe does
not justify more similarity-window or temperature tuning on the opened source.

### Mid-range historical difficulty

A 30–70% historical pass-rate filter scores `0.2708` and pairwise-gap MAE
`0.4083`. With only two reference Agents, task difficulty has only three
levels: `0`, `0.5`, and `1`. The filter therefore collapses to the disagreement
set and does not reproduce the information regime in the motivating work.
Reopen only with a larger reference-Agent panel.

### Decision metrics

Coverage and full history both have rank agreement `0.4167` and recommendation
regret `0.0833`. Coverage's level-MAE advantage does not presently transfer to
a ranking or recommendation claim. Recency has lower regret `0.0667` but worse
level MAE `0.2042`; selecting a metric after observing this tradeoff would be
post-outcome target switching.

### Agent-axis validity

The aggregate direction is not produced by one Agent reversing the other, but
the strength differs:

| Frozen Agent | Coverage MAE | Full-history MAE | Difference |
| --- | ---: | ---: | ---: |
| Terra-high | `0.1750` | `0.1832` | `-0.00817` |
| mini-high | `0.1917` | `0.2034` | `-0.01175` |

Terra's descriptive paired interval is `[-0.0603, +0.0424]`. Mini's is
`[-0.0192, -0.0047]`, but its point effect still misses `0.02` and the same
dependency limitations apply.

Coverage does not consume Agent outcomes at inference time, but it was
nominated after inspecting this two-Agent panel. An Agent meant to be tested
after Selection is a new generalization axis. Future confirmation must state
whether the estimand is this frozen portfolio or unseen Agents. For the latter,
reference/training Agents and evaluation Agents must be disjoint. Two Agents
cannot supply that split.

## Literature used to choose mechanisms

- [Efficient Benchmarking of AI Agents](https://arxiv.org/abs/2603.23749)
  motivates separating absolute score fidelity from rank fidelity and testing
  intermediate historical difficulty under scaffold and temporal shift. The
  present two-Agent panel is too coarse for that mechanism.
- [Coresets Before Score Sets](https://arxiv.org/abs/2607.09739) motivates
  evaluation-unsupervised facility location over inexpensive semantic
  embeddings. Its positive result comes from a much larger heterogeneous
  setting and is not assumed to transfer.
- [Model Assessment and Selection under Temporal Distribution Shift](https://proceedings.mlr.press/v235/han24b.html)
  motivates adaptive rolling windows when the environment changes. The current
  twelve-Block development trace is too small to support another tuned adaptive
  chooser; the existing conservative chooser results remain the applicable
  evidence.
- [tinyBenchmarks](https://arxiv.org/abs/2402.14992) shows that an Item
  Response Theory representation plus a curated subset can estimate scores on
  a fixed benchmark with far fewer evaluations. [Reliable and Efficient
  Amortized Model-based Evaluation](https://proceedings.mlr.press/v267/truong25c.html)
  extends this direction with content-predicted difficulty and adaptive
  questions over a large LM panel. These are relevant fixed-universe
  compression baselines, not evidence that historical Tasks predict later
  Tasks. Barcarolle should test such a baseline only after it has enough
  reference Agents to estimate item parameters and disjoint held-out Agents to
  measure transfer; rolling-origin future MAE remains the primary estimand.

## Validity scorecard and gap

The current algorithm-validity target is:

| Gate | Target | Current result | State |
| --- | --- | --- | --- |
| primary point improvement | at least `0.02` MAE over full history | `0.0100` | miss |
| paired uncertainty | 95% Origin-block interval below `0` | `[-0.0363, +0.0152]` | miss |
| random-space position | beat most equal-budget random mass | `88.68%` midrank | pass as development diagnostic |
| non-oracle density | materially better than a few random draws | reciprocal as-good rate `7.75` | weak |
| support | oracle/support gap leaves room for learning | `0.0250` continuous; `0.0375` discrete | pass |
| learnability control | robust to temporal/stratum nulls | best one-sided value `0.0533` | suggestive only |
| design robustness | stable across horizons, dependencies, and repeat views | block-size direction changes; cluster-deduplicated gain `0.0167`; repeat mean `0.0071` | miss |
| decision fidelity | improve rank or recommendation without target switching | no improvement | miss |
| external confirmation | later Task source and held-out Agents | none | miss |

Support and random-density headroom mean the Task Pool does not rule out the
algorithmic claim. The block-size reversal and failed mechanism screens mean
the current data cannot estimate whether a pre-origin rule will meet it.

For the primary coverage-minus-full-history contrast, the twelve Origin
differences have sample standard deviation `0.04735`. A normal approximation,
used only for planning, gives:

- `44` independent Origins for 80% power if the true improvement is the
  practical target `0.02`;
- `178` independent Origins for 80% power at the currently observed `0.00996`
  effect, which would still miss the practical-effect gate;
- `22` independent Origins for a 95% half-width of `0.02`.

These calculations assume independent identically distributed Origins and
condition on the frozen two-Agent panel. Current dependency recurrence violates
the first assumption, and unseen-Agent generalization adds another variance
axis. Forty-four five-Task Origins plus the initial 15 Tasks imply 235 unique
Tasks and 470 calls for two Agents. Reusing the completed study's cost
distribution gives rough planning values of `$145.15` at the median and
`$314.25` at the sum-of-Agent-p90 view. They are not authority or provider
quotes; a held-out Agent panel increases them.

## Next work

No more coding-Agent spend or same-source parameter search is justified now.

1. Preserve full history as the primary baseline, exact equal-budget random
   landscape as calibration, and support/oracle rows as diagnostics.
2. Obtain a new Task source or later immutable Task Pool with genuinely mature
   rolling Origins. Preregister the candidate, metrics, null controls, and
   dependency/repository aggregation before opening outcomes.
3. Expand and split the Agent panel before reopening difficulty or learned
   outcome models. Reference/training Agents may supply historical features;
   held-out Agents measure transfer. Existing cached Results enter
   exact-identity history; missing Agent×Task cells remain lazy. The present
   exact-random routine is intentionally two-Agent-specific. Before the new
   panel opens, freeze either a tractable sparse exact calculation or a
   fixed-seed Monte Carlo calibration with stated numerical precision.
4. On the second source, freeze ALG-007's `centroid_recent_15` as primary and
   `facility_recent_15` as mechanism control before opening outcomes. Do not
   carry over the 28-point hybrid grid. Embedding availability is independent
   of the temporarily unavailable coding-Agent endpoint. Keep this test
   offline; RI-189 permits core FeatureSnapshot admission only after it passes.
5. After expanding the Agent panel, fit ALG-008 only as an offline
   fixed-universe compression comparator. Fit item parameters only on reference
   Agents, then evaluate the frozen subset on disjoint held-out Agents and later
   Origins. Do not interpret fixed-pool score reconstruction as future-Task
   prediction.
6. Use nested or prequential model choice only after enough outer Origins
   exist. Do not turn the twelve current blocks into pseudo-replication.

The prior 25-Origin sizing applies to coverage versus a five-seed random-bank
mean, not to the primary full-history claim. Replace it with 44 independent
Origins as the current primary planning lower bound. Source, repository,
dependency, and Agent diversity may require more.

## Reproduction and resource record

Run:

```bash
uv run python examples/offline_selector_study/landscape.py
```

The self-digested result binds the frozen study plan and embedding artifact.
Amendment 1 corrects only an overstrong terminal-state label: the best point
loss does improve full history, but not by the required margin. The committed
snapshot binds that amendment and contains aggregate PMFs, diagnostics,
metrics, and selection-membership digests. Raw embeddings remain ignored.

The null audit requests 240,000 Origin PMFs but realizes only 27,172 distinct
four-category history/future states. A bounded exact-PMF cache reuses those
states `8.83×`; an authoritative local rerun took `21.91` seconds and retained
result digest
`c6c15e8a1ffc1ab9f7824ad878b72f3e095aceb8f6968ff6712057368ed884ed`.
Fresh runs with `PYTHONHASHSEED=1` and `777` were byte-identical, with file
SHA-256
`c1a7bc81643ecfc7bea2b807fef51e37ef7f9ba230865738d2265dd18d7fe3f4`.
This is analysis-tool timing, not Agent or Runner performance evidence.

The embedding artifact was retrieved at `07:11:38Z`, before the formal
landscape-plan freeze at `07:18:00Z`. That call generated fixed,
outcome-independent Task-text representations; no mechanism score was computed
before the plan freeze. This chronology is disclosed because the plan is a
development contract, not prospective preregistration.

New resource use in this follow-up:

- coding-Agent calls: `0`;
- embedding calls: `1`;
- embedded Task texts: `75`;
- input tokens: `22,935`;
- dimensions: `1,536`;
- embedding artifact SHA-256:
  `2f3feed69da0f3969f4a2f45372586707fede905bc36f78e1510cbd2f268d075`;
- sanitized landscape result digest:
  `c6c15e8a1ffc1ab9f7824ad878b72f3e095aceb8f6968ff6712057368ed884ed`;
- monetary cost: not exposed by the provider response and therefore not
  guessed.
