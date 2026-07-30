# SWE-bench Full direct-MAE development

Date: 2026-07-30.

Interpretation corrected after the
[estimand and reliability audit](2026-07-30-swe-bench-full-estimand-reliability-audit.md).
The frozen numbers are unchanged. The earlier random and Oracle interpretation
was too broad.

## Question

For each target Agent and repository, can a method use historical Task data and
the other ten Agents' historical outcomes to select ten Tasks whose target
Agent pass rate is closer than Full history to the next five or ten Tasks?

The score is direct future pass-rate MAE. Agents and Origins are averaged
inside each repository, then repositories are averaged equally. The target
Agent's entire outcome column is hidden from Selection. Result storage time is
not an algorithm input.

This is outcome-open development on SWE-bench Full, not independent
confirmation.

## Frozen comparison

The portfolio was committed before candidate scores were read:

- ordinary recency;
- stationary matching of the other Agents' historical response rates;
- ALG-010, a five-state difficulty Markov forecast;
- ALG-015U, an online combination of full, recent, recent-two-block, and
  linear response forecasts;
- ALG-016U, a shared change-point response forecast.

Full history is the no-Selection baseline. The frozen random policy samples
one ten-Task subset per Origin and shares it across target Agents. Its midrank
locates a method under that exact policy; it is not a p-value or a claim about
every random policy. The future-open Oracle is a capacity diagnostic.

Two complete executions produced identical memberships and results.

## Result

| Method | H5 MAE | H5 minus Full | H10 MAE | H10 minus Full |
| --- | ---: | ---: | ---: | ---: |
| Full history | `0.078554` | `0.000000` | `0.062579` | `0.000000` |
| Ordinary recency | `0.083039` | `+0.004485` | `0.069464` | `+0.006885` |
| Stationary response match | `0.081205` | `+0.002652` | `0.064299` | `+0.001719` |
| ALG-010 | `0.082618` | `+0.004065` | `0.069371` | `+0.006792` |
| ALG-015U | `0.078673` | `+0.000119` | `0.067178` | `+0.004599` |
| ALG-016U | `0.080082` | `+0.001528` | `0.065610` | `+0.003030` |

No candidate beat Full at either horizon. ALG-015U was nearly tied at H5;
stationary response matching was best among the candidates at H10.

The candidate random midranks ranged from `0.92435` to `0.99960` at H5 and
`0.88930` to `0.99675` at H10. Full itself had random midranks `0.99970` and
`0.99975`. These values show lower macro budget-ten sampling loss than most
draws from that frozen random policy. They do not establish future-predictive
structure or improvement for most Agent-by-repository cells.

A candidate was favorable in only two to four of ten repository marginals,
depending on method and horizon. The candidate memberships also did not
collapse: pairwise exact equality was generally `2%–24%`, with mean Jaccard
overlap `0.62–0.78`. The later joint-cell audit found that each candidate
improves the six-Agent RAG group mean and harms the five-Agent other-group mean
at both horizons.

## Failure localization

After the candidate result was frozen, a separate future-open diagnostic asked
two questions.

First, suppose Selection knows the other ten Agents' actual future response
rates but still cannot see the target Agent. Using the same exact response
matcher:

| Diagnostic | H5 MAE | H5 minus Full | H10 MAE | H10 minus Full |
| --- | ---: | ---: | ---: | ---: |
| Reference-future Oracle | `0.065864` | `-0.012690` | `0.052649` | `-0.009930` |
| Target-future Oracle | `0.004013` | `-0.074540` | `0.002395` | `-0.060184` |

The reference-future Oracle improved eight of ten repositories at both
horizons. Its repository-bootstrap interval for the difference was
`[-0.020721, -0.004580]` at H5 and `[-0.016253, -0.004128]` at H10. It helped
all eleven target Agents at H5 and ten of eleven at H10.

Those marginals hide joint-cell failures. The reference Oracle helps, harms,
and ties `71/17/22` Agent-by-repository cells at H5 and `68/20/22` at H10. Its
result is macro capacity, not a guarantee for one target Agent and repository.

This separates three possible explanations:

1. The ten-Task history pool has ample capacity: the target-future Oracle is
   near zero. H5 and H10 future rates lie on grids compatible with a ten-Task
   selected pass rate, so this is a feasibility result rather than evidence of
   a complex mechanism.
2. Other Agents' same-future response geometry contains contemporaneous macro
   signal: a target-hidden future-open reference vector beats Full on average.
3. The exact response matcher can turn perfect contemporaneous information into
   a lower macro loss, although local Agent-by-repository transport is
   unreliable.

Within the tested response-matching family, open problems include forecasting
the next reference-Agent residual, transferring that residual to a particular
target Agent and repository, and making a budget-ten action robust to forecast
error. The current coordinate-wise expert, shared change-point, and coarse
Markov forecasts do not solve this combined problem.

This conclusion has limits. The reference-future Oracle recovers about `17.0%`
of target-Oracle headroom at H5 and `16.5%` at H10. It proves that the current
response representation and exact matcher are sufficient at zero forecast
error to beat Full; it does not prove that equal-coordinate response means are
the best representation, that exact L1 is optimal under forecast uncertainty,
that realized future reference rates are predictable from history, or that
response forecasting is the project's only useful route.

## Decision

Do not nominate a Selector from this wave. The post-result audit found that
an exact descriptive decomposition assigns `50.89%` of H5 and `67.68%` of H10
realized variation to fitted Agent, repository, and interaction sample means,
while within-cell variance scales almost linearly with `1/H`. These are
in-sample descriptions, not population variance or reliability estimates. The
current aggregate result does not establish that Selection predicts temporal
deviations from Full.

Permit only one bounded response forecast replay:

1. compare only Full, stationary response matching, and ALG-015U;
2. report forecast error, materialization error, and final direct MAE;
3. retain every Agent-by-repository paired cell and repository leave-one-out
   direction;
4. report whether a gain is confined to the post-hoc RAG subgroup; that
   narrows the claim and blocks broad-Agent nomination without redefining the
   primary finite-panel result;
5. stop response-model work if no stable direct-MAE increment remains at H5 or
   H10, then open one frozen Task-content or repository-process route.

Forecast and materialization loss may guide diagnosis but must not replace
direct pass-rate MAE.
Here partial pooling means learning regularities from multiple research
repositories while every runtime Origin and Selection stays inside one target
repository.
No paid calls or new outcomes are needed for this next wave.

## Evidence

- frozen plan:
  `examples/swe_bench_full_development/plan.json`;
- result:
  `examples/swe_bench_full_development/evidence/summary.json`;
- diagnostic plan:
  `examples/swe_bench_full_development/diagnostic-plan.json`;
- diagnostic result:
  `examples/swe_bench_full_development/evidence/diagnostic-summary.json`;
- superseding interpretation audit:
  `examples/swe_bench_full_estimand_audit/evidence/summary.json`.

The frozen development plans bind their direct implementation and evidence
inputs but not every transitive imported module. The superseding estimand audit
corrects this by binding a canonical manifest of all repository Python
execution sources and dependency declarations; future evidence plans should
retain that complete-source and pinned-runtime rule.
