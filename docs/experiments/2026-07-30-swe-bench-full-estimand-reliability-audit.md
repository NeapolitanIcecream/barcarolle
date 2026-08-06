# SWE-bench Full estimand and reliability audit

Date: 2026-07-30.

Verdict: **revise the interpretation; keep direct pass-rate MAE**.

## Question

The preceding development wave reported one repository-equal MAE for eleven
Agents and ten repositories. This audit asks whether that number demonstrates
within-repository future Selection, or mainly reflects fitted
Agent-by-repository means and finite next-H block variation.

This is outcome-open diagnosis, not independent confirmation. An initial
contract was committed after the concern was identified. Before final
interpretation, adversarial review exposed a wrong permutation null and
incomplete reproduction binding. The v2 contract records those post-output
amendments and treats the corrected permutation result as post-hoc. The audit
ran no new Selector and used no paid, new, or sealed Agent outcome.

## The aggregation implementation is not the bug

For method \(m\), the implementation computes

\[
L_m(r,o,a)=
\left|
  p_{\mathrm{selected},m}(r,o,a)
  -p_{\mathrm{future}}(r,o,a)
\right|
\]

before averaging Agents and Origins inside each repository and then averaging
repositories equally. Opposite signed errors therefore cannot cancel.

The resulting scalar is a valid average loss for this finite development
panel. It is not the pass-rate estimate or expected loss for a particular
Agent and repository, and it does not imply a direction for every
Agent-by-repository cell.

## Fixed-denominator heterogeneity

Across the ten rolling-frame repositories and eleven Agents:

- 70 of 110 Agent-by-repository pass rates are below `0.10`;
- the median cell pass rate is `0.03646`;
- the range is `0.0` to `0.54545`;
- all 60 cells belonging to the six source-labeled RAG submissions are below
  `0.10`;
- the other five submissions have mean cell prevalence `0.20777`.

This recovers the kind of repository-specific variation that a cross-repository
benchmark aggregate hides. SWE-Bench Pro independently reports repository
resolve rates below 10% and, for some model-repository pairs, above 50%
([paper](https://arxiv.org/abs/2509.16941)).

## Future-block landscape

H20 and H40 are reliability diagnostics only. Existing candidates were not
reranked on them.

| Horizon | Repositories | Origins | Zero future blocks | Full MAE | Zero MAE | Previous-block MAE | Previous coverage |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H5 | 10 | 408 | `68.19%` | `0.078554` | `0.098671` | `0.085434` | `4488/4488` |
| H10 | 10 | 201 | `57.81%` | `0.062579` | `0.099916` | `0.069464` | `2211/2211` |
| H20 | 10 | 98 | `46.94%` | `0.050606` | `0.101378` | `0.055299` | `1078/1078` |
| H40 | 8 | 47 | `37.94%` | `0.040636` | `0.098553` | `0.044676` | `451/517` |

Full is not merely an always-zero predictor: it beats zero and the target
Agent's previous-block rate at every horizon on matched rows. At H40, Full MAE
is `0.037527` on the 451 rows where a previous block exists; `0.040636` uses
all 517 rows. Full's advantage is consistent with useful local prevalence; it
does not by itself show prediction of a changing future regime.

The primary target remains the realized next-H pass rate. If the intended
target were instead a latent long-run pass probability, it would be a different
estimand and would require a measurement model. Under absolute loss, a point
forecast unconstrained to a feasible Task subset targets a conditional median,
not a conditional mean; Selection has the additional subset-feasibility
constraint
([Gneiting 2011](https://doi.org/10.1198/jasa.2011.r10138)).

## Exact descriptive finite-panel decomposition

For realized future-block rate \(z_{rba}\), the audit decomposes repository-
equal sums of squares into Agent, repository, Agent-by-repository, common
repository block, and remaining Agent-by-block components. The components add
exactly on this realized frame.

| H | Agent | Repository | Agent × repository | Common block | Agent × block residual | Fitted Agent/repository mean total |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H5 | `44.18%` | `2.29%` | `4.42%` | `13.17%` | `35.95%` | `50.89%` |
| H10 | `59.36%` | `2.77%` | `5.55%` | `9.51%` | `22.81%` | `67.68%` |
| H20 | `73.88%` | `3.41%` | `7.67%` | `4.85%` | `10.19%` | `84.96%` |
| H40 | `79.17%` | `3.30%` | `7.29%` | `4.15%` | `6.09%` | `89.76%` |

On the eight repositories eligible at all four horizons, within-cell block
variance is almost linear in \(1/H\):

```text
variance = -0.0001446 + 0.0714169 / H
R² = 0.99886
```

This is descriptive evidence that finite-block averaging is a major contributor
to the apparent within-cell variation. It is not proof that Tasks are IID
Bernoulli draws. The four horizons are nested coarsenings, H20/H40 contain few
blocks in some cells, and the residual component may still contain Task
composition and real temporal change.

These are in-sample components whose cell means are re-estimated from the
opened future frame. Their percentages are not population variance estimates,
causal shares, reliability coefficients, or proof of stable prevalence. The
facet separation is motivated by generalizability theory, but this audit is
not a formal G-study
([Cronbach, Rajaratnam, and Gleser 1963](https://doi.org/10.1111/j.2044-8317.1963.tb00206.x)).

## Timing separates Oracle capacity from forecasting

Define each target Agent's signed Full residual as:

```text
next-block pass rate - expanding Full-history pass rate
```

| Signal | H5 correlation | H10 correlation |
| --- | ---: | ---: |
| Target Agent's previous residual → its next residual | `0.167` | `0.131` |
| Other Agents' previous residual → target's next residual | `0.176` | `0.177` |
| Other Agents' same-future residual → target's residual | `0.392` | `0.437` |

The same-future association is consistent with, and helps localize, the
future-open reference Oracle's capacity. Lagged association is one
timing-valid diagnostic, not an exhaustive forecast. The corrected
repository-shared multivariate block permutation gives:

| Horizon | Adjacent covariance | As-large-or-larger rate |
| ---: | ---: | ---: |
| H5 | `+0.000670` | `0.001499` |
| H10 | `-0.000926` | `0.211894` |
| H20 | `-0.000269` | `0.099450` |
| H40 | `-0.000816` | `0.457271` |

The null shuffles one common block order per repository, preserving same-block
cross-Agent dependence. It was corrected after initial output was visible, so
these rates are exploratory rather than pre-registered evidence. H5 leaves a
bounded forecasting hypothesis open; the other horizons do not establish an
implementable gain.

## Candidate gains concentrate in the low-prevalence/RAG region

Each frozen candidate improves the six-Agent RAG group mean and harms the
five-Agent other-group mean at both horizons:

| Candidate | H5 RAG / other ΔMAE | H10 RAG / other ΔMAE |
| --- | ---: | ---: |
| Recency | `-0.001662 / +0.011861` | `-0.001493 / +0.016938` |
| Stationary response | `-0.001839 / +0.008041` | `-0.001624 / +0.005732` |
| ALG-010 | `-0.000821 / +0.009928` | `-0.000463 / +0.015497` |
| ALG-015U | `-0.004112 / +0.005197` | `-0.001983 / +0.012497` |
| ALG-016U | `-0.001819 / +0.005545` | `-0.002840 / +0.010075` |

This split was inspected after the aggregate result. It localizes failure and
must not be used to rerank candidates. It is confounded with prevalence,
submission date, harness, model, and mechanism; individual Agents and cells
also reverse direction. All candidates harm the `>=0.10` prevalence-cell mean
at H5 and H10, while the `<0.10` stratum is not uniformly favorable at H10.
The former “better than most random subsets” interpretation therefore did not
establish useful future-predictive structure.

## Marginals hide observed joint-cell reversals

The earlier reference-future Oracle improved the macro H5 and H10 scores, eight
of ten repository marginals, and nearly every Agent marginal. The recovered
joint cells are:

| Reference Oracle | Favorable cells | Harmful cells | Ties |
| --- | ---: | ---: | ---: |
| H5 | 71 | 17 | 22 |
| H10 | 68 | 20 | 22 |

At H10, `psf/requests × sweagent-claude37sonnet-20250227` worsens from Full
MAE `0.135539` to `0.25`, although both its repository marginal and Agent
marginal are favorable. The Oracle therefore establishes macro contemporaneous
capacity on this finite panel, not uniformly favorable observed cells, much
less future deployment cells.

ALG-015U provides the same kind of counterexample. Its H5 random midrank is
`0.99960`, but only 42 of 110 cells are favorable, 46 are harmful, and 22 tie.
Random midrank locates one macro score under one frozen random policy. It is
not a p-value or evidence that most target Agent-by-repository cases improve.

## Corrected claim boundary

The evidence supports these statements:

1. A cross-repository benchmark aggregate is not a pass-rate estimate for an
   arbitrary single repository.
2. The current headline is a realized finite-panel average loss, not an
   expected deployment effect.
3. On the panel average, Full beats zero and previous-block controls. This is
   consistent with useful local prevalence but does not imply a uniform cell
   advantage.
4. Existing candidates do not beat Full. Their group-average direction
   reversal is correlated with prevalence and does not identify a cause.
5. Same-future cross-Agent capacity exists, but usable history-to-future signal
   is weak and not yet converted into lower direct MAE.

The evidence does not prove that every SWE-bench score converges to one global
constant. Under a stable Task distribution, each Agent-by-repository pass rate
converges to its own expected value; a cross-repository total converges to a
weighted mixture of those values. The current experiment has not yet shown that
Selection predicts deviations from the local value.

## Decision

Do not develop another broad response-model portfolio. Permit one bounded
forecast replay because H5 retains weak pre-Origin order and lag evidence:

1. forecast the next other-Agent residual using history only;
2. compare only Full, stationary response matching, and ALG-015U;
3. keep H5 and H10 direct pass-rate MAE primary;
4. retain every Agent-by-repository paired cell and report repository
   leave-one-out directions;
5. report whether a gain is confined to the post-hoc RAG subgroup; such
   confinement narrows the claim and blocks broad-Agent nomination, but does
   not erase a separately reported primary finite-panel improvement;
6. separate forecast error, budget-ten materialization error, and final MAE.

If the forecast improves its diagnostic target but not direct MAE, uncertainty
and budget-ten action are the remaining response-route problem. If it does not
produce a stable forecast increment, retire additional response forecasting and
open one frozen Task-content or repository-process route.

No paid calls, new outcomes, Generator work, or core-schema change is needed.

## Evidence and reproduction

- contract: `examples/swe_bench_full_estimand_audit/plan.json`;
- implementation: `examples/swe_bench_full_estimand_audit/audit.py`;
- committed evidence:
  `examples/swe_bench_full_estimand_audit/evidence/summary.json`;
- summary digest:
  `9e3ba1c5bdf22ac48e8bfc628b2c049a4f16dc0ef3b3b50238ca7e89bcda8630`.

Two complete runs were byte-identical with file SHA-256
`f114bf2fd8aaf77e57410f25c7c2962bb9082635b94d675deefb02cffc02a69a`.
The v2 plan binds Python `3.14.0`, NumPy `2.5.1`, SciPy `1.16.3`,
PyArrow `25.0.0`, and a canonical manifest of all repository Python execution
sources plus dependency declarations.
