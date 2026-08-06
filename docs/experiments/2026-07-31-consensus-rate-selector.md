# Consensus-Rate Selector Sprint

Date: 2026-07-31.

Status: the optimistic development contract passed. `consensus_rate_match` is
the first pre-Origin budget-ten candidate in the modern fixed-Harness panel to
beat Full history at both H5 and H10 on direct future pass-rate MAE. It is not
a production Selector: Origin-weighted aggregation reverses the result, and
two opened cross-system diagnostics fail.

## Decision

| Repository-equal development metric | H5 | H10 |
| --- | ---: | ---: |
| Full-history MAE | `0.179527` | `0.129700` |
| `consensus_rate_match` MAE | `0.173387` | `0.115927` |
| Candidate − Full | `-0.006140` | `-0.013774` |
| Relative MAE reduction | `3.42%` | `10.62%` |

The frozen success gate is met: the same horizon-independent method beats Full
at both horizons, target and future information audits pass, and two complete
runs are byte-identical.

The scientific conclusion is narrower. The experiment establishes an
outcome-open, same-Harness, repository-equal development candidate. It does not
establish that a typical Origin improves, that a new Harness transfers, or that
the raw selected-subset mean is an unbiased estimate of Full or future
performance.

## Frame and Search Provenance

The primary panel contains thirteen model configurations evaluated with the
same mini-SWE-agent v2.0.0 Harness on all 500 SWE-bench Verified Tasks. The
rolling frame has five repositories, 61 H5 Origins, and 30 H10 Origins. For
each target Agent, the other twelve Agents form the historical reference
panel. The target column is excluded before selection.

Direct future pass-rate MAE remains primary. Target Agents and Origins are
averaged inside each repository, then repositories receive equal weight. Full
eligible repository-local history is the no-Selection baseline. Random ten
Tasks calibrate the sampling space but are not a substitute for the Full gate.

The candidate was found after primary outcomes were open. The local META search
contained 72 experts and 68 distinct cross-horizon membership trajectories:

- 17 experts beat Full at H5;
- 24 beat Full at H10;
- 11 beat Full at both;
- the selected fixed expert ranked first at H5 and second at H10.

The 72 experts are not the global multiplicity. The sprint also ran separate
decomposition, distributional, MMD, semantic, IRT, and prequential routes.
Their grids overlap and produce different objects, so no false single
independent-trial count is reported. Formal reproduction does not remove this
outcome-open selection bias.

The original frozen plan was committed before formal candidate execution. An
independent audit later found underspecified tie and reporting rules. Commit
`78e2c4b2` clarified the already observed scratch behavior without changing the
algorithm or rereading a score. The operative plan is
[`consensus-rate-plan.json`](../../examples/modern_agent_panel/consensus-rate-plan.json),
digest
`4298d371d83bcd954932a34692ef2692384ce35e0e42989ff02093409a04fb6e`.

## Algorithm

At one repository and Origin, let:

- \(H\) be the \(n\) eligible historical Tasks;
- \(m\) be the number of reference Agents, fixed across Tasks;
- \(c_i\) be the number of reference Agents that pass historical Task \(i\);
- \(S\) be a subset of ten Tasks.

The Selector minimizes this exact lexicographic key:

\[
\left(
\left|n\sum_{i\in S}c_i-10\sum_{i\in H}c_i\right|,
\sum_{i\in S}c_i(m-c_i),
\operatorname{recent}(S)
\right).
\]

The first term matches the selected reference-panel pass rate to the Full
historical reference-panel pass rate without floating-point rounding. The
second term breaks exact rate ties toward Tasks on which the reference Agents
agree. Since \(c_i(m-c_i)\) counts pass/fail Agent pairs for Task \(i\), it is
zero when all references agree and largest near a half split. The final key
deterministically prefers the lexicographically most recent vector of canonical
history positions.

An exact dynamic program searches response-count compositions. The runtime
contract requires a complete binary Task-by-reference-Agent matrix, at least
two reference Agents, one fixed denominator within a Selection, and no missing
outcome imputation. The same rule is used at H5 and H10.

The selected benchmark score is still the target Agent's raw mean over the ten
Tasks. There is no IRT fit, missing-outcome prediction, importance weighting,
or cross-repository pooling.

## Why the Rule Can Work

If a new target Agent is conditionally exchangeable with the reference panel,
\(q_i=c_i/m\) is a natural estimate of its pass probability on Task \(i\).
Matching the Full pooled rate preserves one historical first moment. Among
exact matches,

\[
c_i(m-c_i)=m^2q_i(1-q_i)
\]

is a plug-in per-Task Bernoulli predictive-variance heuristic. Preferring
reference consensus can therefore reduce uncertainty about an unknown target
without changing the matched moment.

That argument is conditional, not a theorem about future MAE. It ignores
cross-Task covariance, temporal distribution shift, and Task-by-Agent
interactions. Consensus is panel-relative and is not intrinsic Task
difficulty. A different Harness or Agent population can violate
exchangeability even at a similar aggregate pass rate.

The method is best described as a target-hidden, rolling-origin,
model-centric moment-matching coreset. It is not IRT and does not inherit the
accuracy claims of static benchmark-compression work.

## Route Results

| Route | Outcome |
| --- | --- |
| Forecast/materialization/transfer decomposition | Exact subset materialization was already adequate; reference-to-target transfer dominated. |
| Histogram and nearest-analog response matching | Lost to Full at both horizons. |
| RBF MMD | A nominal H5 gain of `0.001332` was driven by a two-Origin repository and did not survive H10. Future-open MMD Oracles showed capacity, not a usable forecast. |
| Hashed and MiniLM Task semantics | Nominal gains were repository- or single-Origin-sensitive and did not pass both horizons. |
| Rasch/IRT family | No dual-horizon winner. The most balanced candidate was worse by `0.001121` at H5 and `0.001889` at H10. |
| Strict prequential META | Beat Full by `0.005951` at H5 and `0.008953` at H10, but the fixed consensus-rate expert was simpler and better at both horizons. |
| Fixed-expert audit | Selected `consensus_rate_match`; all 1,183 formal memberships exactly match the scratch expert. |

These results close the attempted families on this opened panel. They do not
prove that MMD, semantics, or IRT cannot work under a different theory or data
boundary.

## Primary Evidence

### Aggregate and directions

| Horizon | Candidate − Full | Repositories favorable | Agents favorable | Origins favorable |
| --- | ---: | ---: | ---: | ---: |
| H5 | `-0.006140` | 3/5 | 10/13 | 23/61 |
| H10 | `-0.013774` | 4/5 | 11/13 | 13/30 |

The candidate is better than `96.725%` of 20,000 random H5 selections and
`99.620%` of 20,000 random H10 selections. A random subset is as good as or
better than the candidate in `3.275%` and `0.380%` of draws, respectively.

### Repository directions

| Repository | H5 candidate − Full | H10 candidate − Full |
| --- | ---: | ---: |
| Django | `+0.008511` | `+0.006868` |
| Matplotlib | `-0.021430` | `-0.045513` |
| scikit-learn | `-0.007835` | `-0.020280` |
| Sphinx | `-0.010259` | `-0.009069` |
| SymPy | `+0.000311` | `-0.000875` |

Every leave-one-repository-out repository-equal result remains favorable:

- H5 delta range: `[-0.009803, -0.002318]`;
- H10 delta range: `[-0.018934, -0.005839]`.

This rules out a single repository as the sole explanation of the frozen
repository-equal result. It does not rule out Origin-count imbalance.

### Sensitivity that limits the claim

| Alternative estimand | H5 candidate − Full | H10 candidate − Full |
| --- | ---: | ---: |
| Origin-weighted | `+0.004284` | `+0.001864` |
| Only repositories with more than one Origin | `-0.006140` | `-0.001025` |

The Origin-weighted result reverses at both horizons, and most individual
Origins are unfavorable. At H10, Matplotlib and scikit-learn each contribute
only one Origin; removing single-Origin repositories leaves a small
`0.001025` improvement. Repository-equal prediction is the intended project
estimand, but the method must not be described as improving a typical Origin.

### Ablations and diagnostics

| Variant | H5 candidate − Full | H10 candidate − Full |
| --- | ---: | ---: |
| Rate match without consensus | `+0.001728` | `+0.000724` |
| Consensus first without rate preservation | `+0.013217` | `+0.019142` |

Both parts are necessary on this opened panel. The selected reference rate
differs from the Full reference rate by only `0.002051` at H5 and `0.002017` at
H10. Normalized mean disagreement falls from `0.067956` to `0.022353` at H5
and from `0.065231` to `0.022588` at H10.

These ablations support the proposed mechanism locally. Because the mechanism
was selected after outcome-open search, they are not independent causal
confirmation.

## Opened Transfer Diagnostics

The candidate was replayed unchanged after freeze on the already-open
three-system SWE-bench Full lane.

First, each complete system was targeted with the other two systems as
references over all 2,294 Tasks:

| Internal Full-system LOO | H5 | H10 |
| --- | ---: | ---: |
| Full-history MAE | `0.191961` | `0.150453` |
| Candidate MAE | `0.206920` | `0.174459` |
| Candidate − Full | `+0.014960` | `+0.024006` |
| Favorable repositories | 0/10 | 0/10 |
| Favorable Agents | 0/3 | 0/3 |

This changes both Harness population and reference count from twelve to two.
It is a strong failure but not a clean attribution.

Second, all thirteen primary Agents remained the reference panel, the three
complete systems were unseen targets, and evaluation was restricted to the
common 500 Verified Tasks:

| Primary references → external targets | H5 | H10 |
| --- | ---: | ---: |
| Full-history MAE | `0.179630` | `0.156896` |
| Candidate MAE | `0.197143` | `0.164603` |
| Candidate − Full | `+0.017513` | `+0.007707` |
| Favorable repositories | 1/5 | 3/5 |
| Favorable Agents | 0/3 | 1/3 |

The second diagnostic preserves the thirteen-Agent reference panel and common
Task denominator. Its failure is stronger evidence that a target-system or
Harness shift breaks the exchangeability premise. These outcomes were already
open and are not independent confirmation. The independently recomputed compact
record is
[`consensus-rate-transfer-diagnostic.json`](../../examples/modern_agent_panel/evidence/consensus-rate-transfer-diagnostic.json).

## Literature Position

Anchor Points and tinyBenchmarks also exploit historical model-by-item response
structure, but they cover response regions or fit latent/predictive models and
often use weighted estimators. The frozen method matches one pooled moment and
uses an unweighted raw target mean:

- [Anchor Points: Benchmarking Models with Much Fewer Examples](https://aclanthology.org/2024.eacl-long.95/);
- [tinyBenchmarks: evaluating LLMs with fewer examples](https://proceedings.mlr.press/v235/maia-polo24a.html);
- [Evaluation Examples are not Equally Informative](https://aclanthology.org/2021.acl-long.346/).

Active Testing explicitly treats directed test acquisition as a potential
source of estimator bias and uses weighting to recover unbiasedness:
[Active Testing: Sample-Efficient Model Evaluation](https://proceedings.mlr.press/v139/kossen21a.html).
Barcarolle's current raw selected-subset pass rate has no such guarantee.

The closest external warning is the 2025 NeurIPS study of eleven benchmark
prediction methods. It reports strong dependence on source-target model
similarity and weak extrapolation to stronger new models:
[How Benchmark Prediction from Fewer Data Misses the Mark](https://papers.nips.cc/paper_files/paper/2025/hash/c57bacb5ea621582235c54ce2a83136d-Abstract-Conference.html).
The opened Barcarolle transfer failure is consistent with that diagnosis.

SubLIME optimizes rank preservation using anchor models and intrinsic
features. That is a different estimand from Barcarolle's future pass-rate MAE:
[SubLIME](https://aclanthology.org/2025.acl-long.1477/).

## Reproduction and Resource Use

The formal implementation is
[`consensus_rate.py`](../../examples/modern_agent_panel/consensus_rate.py).
Targeted tests cover the exact integer objective, both levels of deterministic
ties, target-column exclusion, current-future exclusion, primary-only loading,
and the minimum reference-panel contract.

Two complete primary executions are byte-identical:

- result file SHA-256:
  `f7282fe8d2a4c6f1660097b3eebe845bc88c1df9c19cc48f9e6157175b709a13`;
- canonical result digest:
  `3816b067491e574d19fd315131cc7080f6da31b644b7f3a7fa4a8864d059f306`;
- compact summary file SHA-256:
  `ba75c0d15a4bc4b384e937c39bc00dd2eef05374f7df2cfb11780aa612cc68b5`;
- implementation SHA-256:
  `4a6f3a62cf9e203a71533f120b0d87decce8d56f6d87acb0685eb06913cd4237`.

The committed evidence is
[`consensus-rate-summary.json`](../../examples/modern_agent_panel/evidence/consensus-rate-summary.json).
Raw membership and score rows remain under ignored `outputs/`.

Resource use: zero paid API calls, zero new Agent runs, zero sealed holdout
reads, and no Generator or core-schema change.

## Next Boundary

Do not tune another constant or selector on the same five-repository primary
score. The next research question is reference-to-target population shift:

1. use existing public outcomes to map failure against reference-panel size,
   target ability, model family, and Harness change;
2. separate a zero-target-outcome cold-start mode from a warm-start mode that
   may use already cached target results;
3. freeze one mechanism that either detects an unsupported cold-start target or
   remains robust across target panels;
4. evaluate it on a new same-Harness target boundary before opening any sealed
   outcome or paying for new Agent runs.

Importance weighting or AIPW is a literature-backed lead, not an immediate
implementation decision. It changes the meaning of the reported benchmark
score and must first be reconciled with Barcarolle's raw pass-rate contract.

The six sealed legacy full-system Agents remain unread, but their population is
not a clean modern confirmation boundary. They should not be opened merely to
produce another score.
