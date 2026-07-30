# SWE-bench Full direct-MAE development

Date: 2026-07-30.

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

The candidates were not random-quality selections. Their random midranks
ranged from `0.92435` to `0.99960` at H5 and `0.88930` to `0.99675` at H10.
Full itself had random midranks `0.99970` and `0.99975`. Selection therefore
used real structure but did not recover enough future shift to offset the
sampling variance introduced by reducing Full history to ten Tasks.

The negative result is not a single-repository artifact. A candidate was
favorable in only two to four of ten repositories, depending on method and
horizon. The candidate memberships also did not collapse: pairwise exact
equality was generally `2%–24%`, with mean Jaccard overlap `0.62–0.78`.

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

This separates three possible explanations:

1. The ten-Task history pool has ample capacity: the target-future Oracle is
   near zero. H5 and H10 future rates lie on grids compatible with a ten-Task
   selected pass rate, so this is a feasibility result rather than evidence of
   a complex mechanism.
2. Other Agents' response geometry contains transferable signal: a target-
   hidden perfect reference forecast beats Full.
3. The exact response matcher can turn that signal into a better Selection.

Within the tested response-matching family, the main missing component is
therefore a sufficiently accurate forecast of the next reference-Agent
response regime and a budget-ten action that is robust to forecast error. The
current coordinate-wise expert, shared change-point, and coarse Markov
forecasts do not provide it.

This conclusion has limits. The reference-future Oracle recovers about `17.0%`
of target-Oracle headroom at H5 and `16.5%` at H10. It proves that the current
response representation and exact matcher are sufficient at zero forecast
error to beat Full; it does not prove that equal-coordinate response means are
the best representation, that exact L1 is optimal under forecast uncertainty,
that realized future reference rates are predictable from history, or that
response forecasting is the project's only useful route.

## Decision

Do not nominate a Selector from this wave. Do not reopen source suitability,
Result timestamps, Agent identity separation, or Task Pool capacity as the
primary explanation for this result. Keep forecast uncertainty and discrete
materialization coupled until the next decomposition measures them separately.

The next algorithm wave should first localize the response-family error:

1. report forecast-to-future response L1, selected-to-forecast L1,
   selected-to-future response L1, reference-Oracle regret, and final
   target-Agent direct MAE;
2. report the same repository-first H5/H10 and per-Agent directions, so a
   better surrogate cannot hide a worse Selection;
3. measure a predeclared noise-to-regret curve around the reference Oracle to
   learn how accurate a forecast must be before Selection beats Full;
4. if the decomposition supports more response work, freeze at most three
   distinct mechanisms: repository-aware empirical-Bayes shrinkage, a
   rank-one shared-difficulty forecast, and a reliability-shrunk or minimax
   action;
5. if historical responses have no stable predictable increment, stop adding
   response models and run one frozen task-only semantic or repository-process
   route;
6. use Full for development and seek a separate boundary only after a
   candidate exists.

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
  `examples/swe_bench_full_development/evidence/diagnostic-summary.json`.

The frozen plans bind their direct implementation and evidence inputs but not
every transitive imported module. The two byte-identical runs and Git commits
make this result auditable; the next plan should bind the complete execution
commit or tree instead of enumerating only selected files.
