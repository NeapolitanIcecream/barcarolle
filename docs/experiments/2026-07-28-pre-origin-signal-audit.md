# Multi-SWE Pre-Origin Signal Audit

Date: 2026-07-28.

## Decision

Stop inventing Selectors on the currently opened Multi-SWE and SWE-bench
Verified development panels.

The evidence now separates three questions:

1. A ten-Task subset can represent the future response vector: the exact
   hindsight diagnostic reduced Multi-SWE H5 loss by `48.46%`.
2. Tasks contain response structure: the outcome-derived, leave-one-
   configuration difficulty coordinate reached repository-macro AUC `0.9121`.
3. The observable target history predicts the next cohort: the frozen
   prequential forecast failed, worsening H5 loss by `+0.000992` and H10 loss by
   `+0.001855`.

The current bottleneck is therefore pre-Origin prediction of the target
repository's next Task mix. It is not the ten-Task budget, and it is not an
absence of static cross-Agent response structure.

No Selector was materialized or nominated. No paid API, embedding API, or
sealed holdout was used.

## Frozen Contract

Both routes were frozen before their new outcome replay:

- ALG-013 Response-Contrast Projection (RCP), plan digest
  `6e3374c6a2d1ce866ad614198ae1911fdec2fc13a58d5cf32cd94ee66e1b249c`;
- ALG-014 Prequential Response-Composition Shrinkage (PRCS), plan digest
  `b703a9fd1484e2bd96376320ad58a2e1495a5f2252f009d2b9bdb49a1cf57fb0`.

RCP learns repository-centered embedding/outcome covariance directions only
from other repositories whose projected Task times are no later than the
target Origin. It never trains on target-repository outcomes or hindsight
memberships.

PRCS evaluates each configuration with a difficulty coordinate computed from
the other 35 configurations. At every Origin it chooses between full-history
and latest-h difficulty means using only earlier completed Origins from the
same target repository, then applies an equal-repository global prior with the
mass of one Task.

H5 is primary. H10 is a sensitivity cohort, not an independent replication.
Repositories are the independent aggregation unit. Multi-SWE Result
availability remains projected to Task arrival, so the evidence is
source-time-safe counterfactual rather than strict historical replay.

## Route 1: Response-Contrast Projection

RCP tested whether fixed Task embeddings could acquire response relevance from
other repositories.

| Diagnostic | Macro AUC | 95% repository bootstrap | Favorable repositories | Decision |
| --- | ---: | --- | ---: | --- |
| H5 future-block AUC | `0.5530` | `[0.4579, 0.6572]` | 10/13 | Frozen gate failed |
| Complete-history precision diagnostic | `0.5104` | `[0.4689, 0.5500]` | 8/13 | RCP family closed |

Only 166/221 five-Task Origins contained both terminal classes for at least one
configuration. A separately frozen post-rejection diagnostic therefore
evaluated complete target histories without changing the ALG-013 decision. Its
19 deterministic within-training-repository response-vector shifts produced a
corrected as-good-or-better rate of `0.55`. A small-future-block explanation
was not supported: the complete-history test also failed to distinguish the
learned semantic directions from the negative control.

Stage B forecasting and Stage C Selection were not reached.

## Route 2: Response Composition

PRCS removed Task text from the mechanism and used the solved fraction of the
other 35 configurations.

### Static response relevance

| Metric | Result |
| --- | ---: |
| Repository-macro history AUC | `0.9121` |
| Repository bootstrap interval | `[0.8828, 0.9365]` |
| Favorable repositories | 13/13 |
| 19-permutation corrected rate | `0.05` |

This establishes a strong static cross-Agent response coordinate on this
opened panel. It does not establish temporal prediction.

### Target future increment

Candidate-minus-full-history differences are positive when PRCS is worse.

| Cohort | Candidate loss | Full-history loss | Difference | Favorable repositories | Deep difference |
| --- | ---: | ---: | ---: | ---: | ---: |
| H5 | `0.036742` | `0.035750` | `+0.000992` | 2/13 | `+0.000106`, 1/8 |
| H10 | `0.033459` | `0.031604` | `+0.001855` | 5/11 | `+0.000262`, 3/5 |

The H5 short- and long-calendar-span differences were both positive:
`+0.004716` and `+0.000520`. The recent expert selection rate was `0.3296`, so
the failure was not caused by always selecting one expert.

The no-prior local prequential ablation was slightly favorable at H5:
`-0.000458`, a `1.28%` loss reduction. It reversed at H10 to `+0.000830`.
This is far below the frozen `10%` signal gate and cannot be promoted as a
post-hoc candidate. The one-Task cross-repository prior was harmful, and the
global-only control was much worse.

Because Stage B failed before its temporal-null decision point, the frozen
order correctly stopped without implementing the exact budgeted Selection.

## Independent Audit

Three independent reviews found no implementation error that changes a
headline effect or decision. They did find two evidence-quality defects and
two interpretation limits:

- The first RCP history diagnostic shifted each configuration separately,
  destroying the within-Task response vector. That artifact had logical digest
  `74cdfd2f0068a7b051a14f41daaecc37e33cd3ddcfce423e3bffc1e85b372847`
  and raw SHA-256
  `2f8e0902a9cb0533fef98cb723b338308fe582d7eed27a5d5ff4f8aaa8aab039`.
  It is retained only under the ignored `pre-audit-invalid-null` filename.
  The corrected diagnostic shifts complete response rows. Its AUC, interval,
  favorable count, corrected rate (`0.55`), and rejection decision are
  unchanged. ALG-013's original future-AUC gate had already failed before any
  permutation was run.
- The frozen RCP v1 audit field `active_configuration_ids` contains panel
  column indices, not configuration identifiers. The name is retained to keep
  the rejected raw result byte-reproducible; the source now states the field's
  semantics. Panel identity, column order, and projection digests still make
  every row traceable.
- Both 19-shift controls are deterministic diagnostics, not exact
  randomization p-values. PRCS Stage A observed AUC `0.9121`, versus maximum
  null AUC `0.5447`, so this limitation cannot reverse the static-signal
  conclusion.
- The H5 calendar split is Origin-weighted: the short-span side covers five
  repositories and the long-span side thirteen. It is not a pure
  within-repository calendar sensitivity. Both directions are harmful, so it
  cannot rescue PRCS.

Tests now cover complete-response-vector preservation, target-repository
exclusion, source-time cutoff, repository-equal pooling, one-Task prior mass,
and earlier-only expert inputs.

## What The Result Establishes

- The fixed sentence embedding does not carry stable cross-repository response
  contrast under the tested RCP construction.
- Other Agent outcomes provide a strong, configuration-held-out static
  difficulty signal.
- A full-versus-recent prequential forecast plus bounded cross-repository
  shrinkage does not predict the next cohort better than full history.
- Hindsight headroom and static response prediction can coexist with no usable
  pre-Origin next-cohort signal. This is the strongest current explanation for
  the repeated pattern of high random percentile but negligible or reversed
  improvement over full history.

## What It Does Not Establish

- It does not prove that every possible observable pre-Origin signal is
  impossible.
- It does not test native historical Result availability or strict prospective
  operation.
- It does not establish portability beyond the Multi-SWE source frame.
- It does not authorize opening the six sealed SWE-bench Agents or making paid
  validation calls.
- It does not justify a Runner default or a core Selector abstraction.

## Stop And Reopen Boundary

The current opened panels remain useful for implementation regression,
capacity diagnostics, and reproduction. They are closed for further candidate
discovery and nomination replay. A new observable mechanism proposed
independently of their outcomes may advance theory design, but it does not
authorize another replay on these panels.

Reopen empirical nomination research only at a new evidence boundary:

1. a source with native Task time, historical Result availability, and denser
   repository-local Origins;
2. an independent complete Agent panel or source family;
3. a strict prospective target-repository campaign.

Do not reopen by changing an embedding, horizon, budget, prior mass, expert
threshold, or gate.

## Reproduction

The ignored raw results and independent reproductions are byte-identical:

| Artifact pair | SHA-256 |
| --- | --- |
| RCP Stage A | `1cadce24535af40d25cb040732eb2c60a09d4b775401e0921cc456f046543812` |
| Corrected RCP history diagnostic | `eb13ea8d79c5340361577f1c1b80b2dad4076053f8c19b2040669d261f534539` |
| PRCS signal cascade | `4c76a98b482d34f5a785d4ab9875336a6edb30f21a7489960ffa46e1d54b9fd2` |

The committed summary is mechanically rebuilt from all six raw artifacts. Its
digest is
`3f4a370084167b37bb20e0e5ab7a5989fdc71e85b500c3fdcc9c8c1c3b0f045e`.
