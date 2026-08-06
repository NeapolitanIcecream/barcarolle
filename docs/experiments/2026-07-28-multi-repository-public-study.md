# Multi-Repository Public Selector Study

Date: 2026-07-28.

Status: completed initial no-paid-call development study. No Selector was
nominated for independent or paid validation. The later theory-driven,
sealed-Agent, cutoff-aware, and adaptive experiments are recorded in
[`2026-07-28-theory-driven-selector-sprint.md`](2026-07-28-theory-driven-selector-sprint.md).

## Question And Boundary

The study asks whether a budgeted Selection drawn from one repository's
eligible historical Tasks predicts the same repository's next Tasks better
than using all eligible history.

Multiple repositories increase the number and diversity of offline research
Origins. They are never combined at product runtime:

`one target repository -> one Task Pool -> one repository-local Selection`.

The primary contrast is candidate MAE minus full-history MAE. Negative values
favor Selection. Origins are averaged within repository before repositories
receive equal weight. This prevents Django's 43 Origins from replacing the
cross-repository claim.

## Inputs And Identity

- Task source: 500 Tasks from
  [SWE-bench Verified](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified/tree/main),
  revision `91aa3ed51b709be6457e12d00300a6a596d4c6a3`.
- Source SHA-256:
  `43ed5a3d1d98da36472c1ade65ddd2085d7b4ff694fcaf6a023a07c5c1f32f21`.
- Outcome source: three frozen submissions from the official
  [SWE-bench experiments repository](https://github.com/SWE-bench/experiments),
  commit `2f15350cd32becc4569e0d826361048555b605c0`.
- Panel: SWE-agent LM 32B, SWE-Fixer Qwen, and Skywork-SWE 32B.
- Origin rule: at least 15 historical Tasks, non-overlapping five-Task future
  blocks, and a ten-Task Selection budget.
- Portfolio: 12 inventoried repositories, seven wide-portfolio repositories,
  three deep-portfolio repositories, and 68 repository-local Origins.
- Lineage audit: all 12 repository slugs were public, non-archived, and
  non-forks when checked. This is not proof of statistical independence.
- Cost: zero paid API calls and zero coding-Agent calls. The semantic replay
  used an already-cached, pinned `all-MiniLM-L12-v2` snapshot on local CPU.

The Tasks use source `created_at`, while Check maturity is projected back to
Task arrival. The resulting evidence is counterfactual, not
strict-prospective. Raw parquet, public result files, and embedding vectors
remain ignored; committed plans, manifests, summaries, and digests make the
replay auditable.

## Results

The table reports the wide-portfolio macro-repository contrast against full
history. The interval resamples declared repository clusters. `Favorable`
counts repositories with a negative contrast.

| Route | Difference | 95% cluster interval | Favorable | Better than random | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Recency | `+0.0189` | `[-0.0040, +0.0400]` | 2/7 | 45.83% | Retire on this panel |
| Difficulty coverage | `+0.0398` | `[+0.0289, +0.0519]` | 0/7 | 8.28% | Retire on this panel |
| History match | `-0.0064` | `[-0.0178, +0.0041]` | 5/7 | 93.75% | Compression control only |
| Cross-repository drift match | `+0.0016` | `[-0.0060, +0.0093]` | 4/7 | 84.02% | Reject |
| Local trend match | `-0.0064` | `[-0.0178, +0.0041]` | 5/7 | 93.75% | Collapsed to history match |
| Semantic centroid | `+0.0015` | `[-0.0215, +0.0253]` | 4/7 | 84.15% | Retire ALG-007 on this source |
| Semantic facility location | `+0.0377` | `[+0.0118, +0.0618]` | 2/7 | 10.46% | Retire ALG-007 control |
| Hindsight support | `-0.1589` | `[-0.1992, -0.1114]` | 7/7 | Not applicable | Diagnostic oracle only |

The deep-portfolio direction is also unfavorable for recency
(`+0.0353`), difficulty coverage (`+0.0284`), and semantic centroid
(`+0.0168`). History match is nearly neutral (`-0.0014`). The locally fitted
trend rule chose alpha zero in every outer repository fold, so it added no
information to history match. Cross-repository mean drift did not improve that
control.

Equal-budget random Selection has mean wide contrast `+0.0175` with population
SD `0.0159`. The 20,000-draw Monte Carlo estimate has mean standard error
`0.000112`. History match occupies a useful part of the random landscape, but
its `-0.0064` effect misses the frozen development nomination threshold
`-0.01`, its interval crosses zero, and the deep effect is negligible.

The hindsight support endpoint shows that ten-Task subsets can represent future
Agent performance much better than full history. The failed outcome-safe
methods show that identifying those subsets before the future Origin is the
current bottleneck. Text similarity does not close that gap: full history has
lower selected-to-future centroid distance (`0.2468`) than either semantic
candidate (`0.2893` and `0.2910`).

## Decisions

1. Do not pay to validate any current candidate. None clears the opened-data
   nomination gate, so a paid run would test an already weak method.
2. Keep full history as the primary baseline and equal-budget random Selection
   as the dense sampling-landscape calibration.
3. Keep history match only as a compression control. It is evidence that the
   Agent response matrix contains some usable structure, not a validated
   temporal Selector.
4. Retire recency, difficulty coverage, cross-repository mean drift, local
   trend, and fixed ALG-007 on this source family and panel. Do not continue
   window, embedding-model, shrinkage, or mixture sweeps on these opened
   outcomes.
5. Do not widen core `train_selector`, add an embedding service, create a
   repository registry, or add multi-repository Runner behavior. The direct
   experiment layer already supplies the only proven callers.

## Gate Before The Next Paid Study

A new route must first have a mechanism not derived from further searches over
these opened outcomes. On the current development panel it must meet all of:

- wide macro-repository difference at most `-0.01`;
- negative direction in at least five of seven repositories;
- every leave-one-repository-out summary negative;
- negative deep-portfolio direction;
- better than at least 75% of equal-budget random draws;
- improvement over history match when it forecasts Agent outcomes.

Only then should the project freeze a new source or Agent panel and request
paid authority. Confirmatory validity still requires the stronger project gate:
at least `0.02` improvement over full history, a 95% interval below zero, no
leave-one-cluster-out sign reversal, and later-source or strict-prospective
confirmation.

Do not freeze a confirmatory repository count from this failed seven-repository
screen. Candidate-specific repository SDs vary enough that naive normal
approximations range from roughly 3 to 28 repositories for a `0.02` effect.
The next nominated route must supply its own blinded pilot variance,
repository dependence audit, missingness, and cost before sample size is fixed.

## Reproduction

The code and self-digested artifacts are under
[`examples/multi_repository_study/`](../../examples/multi_repository_study/).
The directory README lists the commands. Focused tests verify source-plan
binding, repository-local selection, deterministic ties, exact normalization,
repository-first aggregation, local embedding identity, and committed result
digests.
