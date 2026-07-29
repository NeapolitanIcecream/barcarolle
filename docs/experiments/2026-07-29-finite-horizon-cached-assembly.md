# Finite-Horizon Cached Assembly

Date: 2026-07-29.

## Result

`ALG-018C Jeffreys Finite-Horizon Median Assembly` passes its frozen
exploratory progress rule on the outcome-open Multi-SWE development panel.

| Horizon | ALG-018C MAE | Full MAE | Candidate − full | H-blind cached MAE | Candidate − H-blind |
| --- | ---: | ---: | ---: | ---: | ---: |
| H5 | `0.053252` | `0.067348` | `-0.014096` | `0.062983` | `-0.009731` |
| H10 | `0.048713` | `0.052807` | `-0.004094` | `0.049033` | `-0.000320` |

The relative MAE reduction versus full history is `20.93%` at H5 and `7.75%`
at H10. Compared with the stronger H-blind cached control, the reduction is
`15.45%` and `0.65%`.

The H5 gain is repository-robust. The paired candidate-minus-H-blind interval
is `[-0.013081, -0.006442]`, 12/13 repositories are favorable, every
leave-one-repository-out aggregate is negative, and all eight deep
repositories are favorable. Versus full history, 34/36 configurations, 12/12
models, 3/3 harnesses, and 7/7 languages are favorable.

The H10 point estimate passes the frozen strict-negative rule, but its paired
interval `[-0.002109, +0.001565]` crosses zero and only 5/11 repositories are
favorable. H10 supports retention of the mechanism, not a stable superiority
claim over the H-blind cached control.

The finite-horizon family has the best observed direct pass-rate MAE in the
sprint's cached-target information contract: the plug-in ablation is slightly
lower at H5 and ALG-018C is slightly lower at H10. It is not comparable to
unseen-target methods without stating the extra cached Result information.

## Why This Follow-Up Exists

The preceding frozen portfolio found that a simple cached-target control beat
AdaNormalHedge, BOCPD, ALG-007, recency, and full history on both horizons. The
control selects \(q\) historical successes so that \(q/10\) is nearest to the
same public target configuration's full-history pass rate.

An independent theory Agent, without reading the preceding membership or
result artifacts, identified the missing decision-theoretic step: Barcarolle's
loss compares the selected pass rate with a realized finite future cohort
rate, not a latent Bernoulli probability. Under absolute loss, the optimal
action is a predictive median projected onto the feasible Selection grid.

The second plan was frozen after observing the H-blind control result but before
materializing or scoring either new membership. It is explicitly post-result
exploration on the same opened panel, not independent confirmation.

## Frozen Information Contract

At one Origin:

- the exact target Agent identity has complete, cutoff-safe binary Results on
  all \(n\) eligible historical Tasks;
- \(s\) of those Results are successes;
- Selection budget \(B=10\);
- future cohort size \(H\) is declared as 5 or 10 before Selection.

The runtime contract requires Agent identity to include model, harness,
prompts, skills, tools, runtime budget, and stochastic-result policy. Missing,
stale, partial, or identity-mismatched Results make the method unavailable.
Another Agent cannot fill the missing column.

This evidence source does not prove that runtime contract. Its public outcome
rows identify model/harness configurations but have no native Result
availability time or complete production Agent fingerprint. The experiment
therefore assumes that all same-configuration historical outcomes were cached
at each cutoff. Projected Task history and future blocks are separated without
future-outcome access, but real historical Result availability is not
established. The result is a retrospective cached-result counterfactual.

No future Task identity, content, patch, attribute, or outcome enters
membership generation. The contract is cached-target calibration. It cannot
support lazy pre-execution Selection for an unseen Agent.

## ALG-018C

Use Jeffreys' Bernoulli posterior

\[
p\mid\text{history}\sim
\operatorname{Beta}\left(s+\tfrac12,n-s+\tfrac12\right).
\]

For future success count \(K\), the posterior predictive distribution is
Beta-Binomial with size \(H\). Let

\[
Q=\{\max(0,B-(n-s)),\ldots,\min(B,s)\}
\]

be the feasible selected success counts. Exact unnormalized predictive weights
are generated with `Fraction`:

\[
w_0=1,\qquad
w_{k+1}=w_k\,
\frac{H-k}{k+1}\,
\frac{s+\frac12+k}{n-s+\frac12+H-k-1}.
\]

For each \(q\in Q\), minimize

\[
A(q)=\sum_{k=0}^{H} w_k |Hq-Bk|.
\]

This differs from
\(\operatorname{E}|q/B-K/H|\) only by a common positive factor.
Exact primary ties choose the \(q\) nearest the Jeffreys predictive mean, then
the lower \(q\). Within the success and failure cells, the existing
cutoff-safe visible priority picks concrete Tasks.

The rule has no fitted parameter, numerical tolerance, or solver. Jeffreys'
prior follows his sampling-theory construction
([Jeffreys, 1946](https://www.cambridge.org/core/journals/mathematical-proceedings-of-the-cambridge-philosophical-society/article/abs/on-the-prior-probability-in-the-theory-of-sampling/BC1F87CE9625BB27B116B5484FBC6A8C));
binomial medians and their relation to rounded means are discussed by
[Kaas and Buhrman](https://onlinelibrary.wiley.com/doi/pdf/10.1111/j.1467-9574.1980.tb00681.x).

The frozen `ALG-018C-P` ablation replaces the Beta-Binomial distribution with
`Binomial(H, s/n)` and uses the same exact action and tie structure. It isolates
finite-horizon loss alignment from Jeffreys uncertainty integration.

## Results

### Direct MAE And Robustness

| Algorithm | Horizon | Candidate − full | Repositories favorable vs full | Deep difference vs full | Random midrank |
| --- | ---: | ---: | ---: | ---: | ---: |
| ALG-018C Jeffreys | H5 | `-0.014096` | 12/13 | `-0.015733` | `1.00000` |
| ALG-018C Jeffreys | H10 | `-0.004094` | 9/11 | `-0.006969` | `0.99995` |
| ALG-018C-P plug-in | H5 | `-0.014213` | 12/13 | `-0.015749` | `1.00000` |
| ALG-018C-P plug-in | H10 | `-0.004079` | 9/11 | `-0.007214` | `0.99995` |

ALG-018C also beats:

| Control | H5 | H10 |
| --- | ---: | ---: |
| H-blind cached quantized full | `-0.009731` | `-0.000320` |
| ALG-015C | `-0.011861` | `-0.003848` |
| ALG-007 | `-0.011842` | `-0.006251` |
| Ordinary recency | `-0.013912` | `-0.004305` |

All values are repository-first candidate-minus-control MAE. The H5 result is
favorable for 34/36 configurations, 12/12 models, 3/3 harnesses, and 7/7
languages. H10 is favorable versus full for 30/36 configurations, 12/12
models, 3/3 harnesses, and 6/7 languages.

The plug-in ablation is `0.000117` better than Jeffreys at H5; Jeffreys is
`0.000015` better at H10. The plan prohibits replacing the frozen candidate
after observing these values. Their near equality shows that finite-horizon
absolute-loss alignment explains the main gain; Jeffreys shrinkage is a small
secondary choice on this frame. Paired repository intervals for plug-in minus
Jeffreys are `[-0.000396, +0.000105]` at H5 and
`[-0.001163, +0.001411]` at H10, so this panel does not distinguish them.

### Why H5 Is Large

With H5, the future empirical pass rate can only be
\(0,0.2,0.4,\ldots,1\). A ten-Task Selection can express tenths. On this
panel, the exact absolute-loss action happens to select only points on the
future fifth-grid:

- \(q=0\): 7,546/7,956 cells;
- \(q=2\): 380/7,956;
- \(q=4\): 30/7,956.

No odd \(q\) is selected. ALG-018C changes the H-blind action in 2,444 cells
(`30.72%`). No action is changed by success/failure inventory constraints.
Future success count is zero in 6,652/7,956 cells. The large observed gain
therefore reflects the interaction of finite-H absolute loss, the B10/H5 grid,
and this opened panel's zero-heavy outcomes; grid alignment alone is not a
general theorem about the action.

With H10, future and Selection rates share the same tenth-grid. ALG-018C
changes only 460/3,852 cells (`11.94%`), always decreasing \(q\), and gains
only `0.000320` over the H-blind control. This H5/H10 contrast is the expected
pattern under finite-grid alignment and supplies no Task-content-prediction
evidence.

The standard H5 and H10 frames also differ: H5 contains 221 Origins in 13
repositories, while H10 contains 107 Origins in 11. The contrast is therefore
entangled with frame composition until a matched-cutoff B-by-H audit is run.

An independent reconstruction traced all 11,808 evaluated cells from projected
Origins through eligible history and future blocks, recomputed exact
`Fraction` risks and actions, rebuilt newest-within-cell memberships, and
recomputed repository-first MAE, paired bootstraps, random ranks, and action
diagnostics. It found zero mismatches. Among the 2,444 H5 cells whose action
changed, 1,766 had zero future successes; 1,747 cells improved and 697
worsened. This confirms the gain is the expected interaction between the
known H5 grid, absolute loss, and this panel's zero-heavy outcomes, rather than
future-outcome access or an implementation defect.

Configuration, model, harness, and language directions are post-selection
descriptions, not group-held-out validation. Random midrank describes location
among equal-budget random subsets and is not a p-value.

## Interpretation

This is a valid Bayes decision for the frozen estimand: realized pass rate on a
known-size future cohort under a stationary Bernoulli predictive model. It is
not metric gaming if that finite cohort pass rate is the quantity the user
actually wants to estimate.

It becomes the wrong estimand when the user wants:

- the latent success probability rather than a realized small-cohort rate;
- performance over an unknown or variable future Task count;
- transfer to a changed or unseen Agent;
- Task-level coverage, semantics, failure modes, or interaction quality;
- evidence of temporal Task-mixture prediction.

The specific Task identities inside the selected success/failure cells do not
affect target-Agent pass-rate MAE. This method is therefore a loss-aware cached
Result compressor, not evidence that its ten Tasks resemble future Tasks in
content.

The result also makes future horizon an algorithm contract, not merely an
evaluation setting. A runtime `TimeRange` with unknown realized count cannot
silently substitute for H5 or H10.

## Reproduction

Plan digest:
`6602a349d5c108fef96fb9e15d405bf268619b0fdd2721500f6a5c62ad9264b7`.
Execution lock:
`10e2832290b92f40c120b8a6e3a7e9a946ec778ee71bb4bf08f6fa697858be4b`.

Two complete membership runs are byte-identical:

- logical digest:
  `dc76659a301a87e15d0e9004936cc7b5383621d5291f35f7e15a0f4de8219319`;
- raw SHA-256:
  `961b99d53435e0acbf54b7fe5bd6934301914a357ef1d7d3a2c4c44c930b5162`;
- raw size: 24,737,911 bytes.

Two score runs are byte-identical:

- logical digest:
  `77c6ae2c893197ecf3c1361433994a41538558142e069d64483ef5e49052afb2`;
- raw SHA-256:
  `63662482080394eb94c6ce2ec416cbaa88172b037b466abfccaea29fcf9ae045`;
- raw size: 58,701 bytes.

Raw outputs remain ignored under
`outputs/research/2026-07-29-finite-horizon-cached-assembly/`. Compact evidence
is
[`examples/finite_horizon_cached_assembly/evidence/summary.json`](../../examples/finite_horizon_cached_assembly/evidence/summary.json).
Its self-excluding digest is
`ae4997f1c4042d3499b43a7a8eeced9ea6c52f4151277fa94826aabe98888735`.

The run used CPython 3.14.0, NumPy 2.5.1, and SciPy 1.16.3. It made no paid API
call, new Agent-outcome call, embedding call, or sealed holdout read, and added
no core schema or runtime service.

## Decision And Next Work

1. Retain ALG-018C as the frozen cached-target finite-horizon development
   candidate. Keep the plug-in rule as a nearly equivalent loss-aware
   baseline; do not choose between them from these opened values.
2. Keep `cached_quantized_full` as the H-blind fallback when the future Task
   count is unknown.
3. Do not use ALG-018C for unseen-target Selection or claim Task-content
   prediction.
4. The crossed budget/horizon study is complete in
   [`2026-07-29-finite-horizon-grid-audit.md`](2026-07-29-finite-horizon-grid-audit.md).
   It terminates `grid_dominant`: only B10/H5 has a stable incremental gain
   over same-budget H-blind. Treat plug-in as a contract-specific baseline,
   not a general Selector.
5. Treat the crossed study on Multi-SWE as mechanism characterization, not
   independent confirmation. A confirmation claim needs a new source,
   later-period panel, or prospective evidence.
6. Do not open sealed Agents or add core infrastructure. Runtime admission
   needs a concrete cached-result caller and an explicit future-count contract.
