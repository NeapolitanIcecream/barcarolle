# Surrogate-Gate Pass-Rate MAE Audit

Date: 2026-07-29.

## Result

The earlier use of AUC, response-coordinate loss, and Brier loss as hard stops
was a methodology error once complete public Agent outcomes were already
available. Those metrics can diagnose a mechanism. They should not prevent the
direct pass-rate MAE evaluation that represents Barcarolle's claim.

The error did not change the decision for the three audited candidates:

| Candidate | H5 candidate − full | H10 candidate − full | Outcome decision |
| --- | ---: | ---: | --- |
| ALG-013 Response-Contrast Projection | `+0.001729` | `+0.005890` | Reject on primary MAE. |
| ALG-014 Response-Composition Shrinkage | `+0.001992` | `+0.008170` | Reject on primary MAE. |
| THY-002S Brier Projection Coreset | `-0.002594` | `+0.002943` | Fails its frozen outcome gate. |

Negative differences favor Selection. ALG-013 and ALG-014 are worse than full
history at both horizons. THY-002S helps at H5, but misses its required
`-0.005` effect and its repository bootstrap interval crosses zero. It reverses
at H10.

No Selector is nominated. The original ALG-013, ALG-014, and THY-002S
decisions remain recorded.

## Why This Audit Exists

`future_pass_rate_mae` remained the project outcome in early experiments.
ALG-013 and ALG-014 later introduced cascades that stopped before Stage C when
AUC or response-coordinate forecasting failed. THY-002S stopped before its
already-written outcome contract when its Brier front gate failed.

That order is justified only when Agent outcomes must still be purchased. The
Multi-SWE panel already contained 36 complete public outcome vectors, so the
MAE join required local compute only.

This audit asks one question: did the surrogate stop falsely retire a candidate
that would have passed the direct outcome evaluation?

## Contract

For configuration \(a\), Origin \(o\), horizon \(h\), and Selection \(S\):

\[
L_{a,o,h}(S)=
\left|
\operatorname{mean}_{t\in S} y_{a,t}
-
\operatorname{mean}_{t\in F_{o,h}} y_{a,t}
\right|.
\]

The primary contrast is candidate loss minus loss on all eligible target-
repository history. Configurations and Origins are averaged within each
repository, then repositories are weighted equally.

The replay preserves:

- the exact 1,632-Task Multi-SWE projection and 36 complete configurations;
- the frozen H5 wide/deep and H10 common/deep repository frames;
- minimum history 20, Selection budget 10, and projected Task ordering;
- each parent algorithm, parameters, controls, and primary MAE thresholds;
- zero paid calls and zero sealed-holdout reads.

The work is a post-decision reproducibility audit, not a blinded experiment.
Independent audit workers reported preliminary MAE values before the executor
plan was committed. The three parent algorithms and their primary Stage-C
requirements predate those values. The audit plan prohibits any result-driven
change.

## ALG-013

For every Origin and held-out configuration, ALG-013 uses response-contrast
directions from the other configurations, forecasts the next block's projected
centroid, and applies the existing greedy mean-match plus at most 20 improving
swaps. Only the held-out configuration scores the resulting Selection.

| Horizon | Candidate MAE | Full MAE | Difference | Favorable repositories | Deep difference | Random midrank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H5 | `0.069076` | `0.067348` | `+0.001729` | 6/13 | `-0.000579` | `0.5032` |
| H10 | `0.058697` | `0.052807` | `+0.005890` | 3/11 | `+0.001757` | `0.3693` |

H5 bootstrap interval: `[-0.002264, +0.005995]`. H10:
`[-0.000989, +0.015173]`.

Candidate-minus-control contrasts are:

| Control | H5 | H10 |
| --- | ---: | ---: |
| ALG-007 | `+0.003983` | `+0.003733` |
| Ordinary recency | `+0.001912` | `+0.005680` |
| Raw-embedding OLS | `+0.001417` | `+0.001079` |
| RCP full centroid | `-0.000212` | `-0.001404` |
| RCP recent centroid | `+0.001979` | `+0.000378` |

The candidate fails the first primary conditions. Random, group-refit, or
temporal-null diagnostics cannot make its positive full-history contrast pass.

## ALG-014

For held-out configuration \(a\), each Task receives the integer count solved
by the other 35 configurations. The earlier-Origin full/recent expert, one-
Task cross-repository prior, and exact bounded composition matcher remain
unchanged. Selection materialization has no current-future argument.

| Horizon | Candidate MAE | Full MAE | Difference | Favorable repositories | Deep difference | Random midrank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H5 | `0.069340` | `0.067348` | `+0.001992` | 4/13 | `+0.001296` | `0.45645` |
| H10 | `0.060977` | `0.052807` | `+0.008170` | 1/11 | `+0.005753` | `0.11745` |

Its Stage-B response-coordinate differences reproduce the earlier
`+0.000992` and `+0.001855`. The primary MAE agrees with that direction and
rejects the candidate directly.

Candidate-minus-control contrasts are:

| Control | H5 | H10 |
| --- | ---: | ---: |
| ALG-007 | `+0.004246` | `+0.006013` |
| Ordinary recency | `+0.002176` | `+0.007959` |
| Static response composition | `+0.001354` | `+0.002016` |

## THY-002S

THY-002S reuses all 107 frozen candidate, stationary, recency, history, H5
future, and H10 future memberships. The executor regenerates the original
20,000 random subsets with NumPy 2.5.1, seed `2026072902`, chunk 500, and one
RNG stream. The regenerated membership digest matches
`ddafa132…24db9`.

| Horizon | Candidate MAE | Full MAE | Difference | Favorable repositories | Favorable configurations | Random midrank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H5 | `0.062839` | `0.065433` | `-0.002594` | 7/11 | 24/36 | `0.93485` |
| H10 | `0.055750` | `0.052807` | `+0.002943` | 7/11 | 14/36 | `0.78260` |

H5 also passes every leave-one-repository-out view, beats the stationary
coreset, and has 8/12 favorable models and 3/3 favorable harnesses. It fails:

- required effect `candidate − full <= -0.005`;
- bootstrap upper bound below zero; observed interval
  `[-0.009243, +0.004724]`.

H10 fails the negative-direction and 19/36 configuration requirements.
Therefore `would_pass_frozen_outcome_gate` is false.

Candidate-minus-control contrasts are:

| Control | H5 | H10 |
| --- | ---: | ---: |
| Ordinary recency | `-0.001001` | `+0.002733` |
| Stationary coreset | `-0.003783` | `-0.003374` |

## Specification Limits Found

ALG-013 and ALG-014 did not fully specify:

- whether random subsets are shared across held-out configurations;
- exact group-holdout rematerialization for model, harness, language, and
  model-by-harness views;
- exact Selection temporal-null construction.

The audit records shared-subset random results as implementation-specific
diagnostics and group values as post-Selection directions. It does not claim a
unique complete replay of either original Stage C. These gaps do not affect
their primary rejection.

THY-002S's outcome contract is complete enough for a full gate decision. Its
declared provider count has no frozen provider mapping, so provider is omitted;
it is not a gate.

## Reproduction And Artifacts

Plan digest: `7df62c16…7c181`. The first invocation stopped before Selection
because the compact panel key is `configurations`, not
`configuration_metadata`. Amendment `9ee6e8d7…98f49` binds that input-only fix
and states that no scientific field changed.

An adversarial review of the first two completed runs then found two transcribed
logical digests, no executor check for the plan's logical bindings, one
terminal label outside the frozen vocabulary, and missing control values in the
committed summary. Amendment `1d25336e…1a833` records that post-replay evidence
access, corrects only the two identities, validates all twelve logical bindings
before Selection, and maps unchanged gate booleans to the frozen terminal
states. The first two runs remain as superseded audit evidence at raw SHA-256
`0b932023…5037d` and result digest `e9bbd44e…f403c`.

The two accepted post-amendment runs are byte-identical:

- raw SHA-256: `1eda7fe1…fc928`;
- raw logical result digest: `1a105781…0599`;
- compact SHA-256: `3df11e3a…ba853`;
- committed evidence digest: `5f6098f3…fff39`.

After removing amendment provenance and normalizing the renamed terminal
diagnostic, the accepted scientific payload equals the superseded runs. Every
membership, loss, control, interval, random result, gate boolean, and
scientific conclusion is unchanged. The normalized old/new canonical digest is
`4ca4f15d…d4192`; the committed summary records the exact normalization rule.

The raw runs remain under ignored `outputs/research`. The compact evidence is
in
[`examples/surrogate_gate_audit/evidence/summary.json`](../../examples/surrogate_gate_audit/evidence/summary.json).

Tests cover the amendment chain, every logical binding, frozen terminal-state
projection, the ALG-013 optimizer and held-out-fit semantics, ALG-014 exact DP
and tie rules, a future-free composition materializer, evidence identity, and
repository-first aggregation.

## Decision Rule Going Forward

When matching Agent outcomes already exist, candidate promotion or rejection
must use pass-rate MAE directly. A proxy may:

- explain why a candidate behaves as observed;
- reject an outcome-independent representation before Agent outcomes exist;
- order paid evidence acquisition under a separately frozen cost policy.

A proxy may not suppress an affordable outcome evaluation or be reported as
the candidate's predictive validity.

The next algorithm route still needs a new pre-Origin mechanism. Do not tune
ALG-013, ALG-014, or THY-002S on this opened panel. Preserve the six unread
SWE-bench Verified holdout Agents until a new candidate passes its complete
development outcome gate.
