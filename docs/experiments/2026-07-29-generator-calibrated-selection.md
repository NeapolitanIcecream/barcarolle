# THY-002S Generator-Calibrated Selection

Date: 2026-07-29.

## Decision Before Replay

Freeze a sequential study rather than building an outcome layer speculatively.
Stage A first tests the forecast-to-Selection mapping entirely in Task space.
Only a Stage A pass authorizes a narrow amendment that can reuse already-open
public Agent outcomes. No paid call or sealed holdout access is authorized.

The machine contract is
[`plan.json`](../../examples/generator_calibrated_selection/plan.json), digest
`cb83d866…b1b9a`. It binds code, source bytes, Git heads, 1,337 Tasks, 107
nested Origins in 11 repositories, the upstream `THY-002` result, budget,
mapping, controls, random sampler, gates, and the downstream outcome contract.

This sequencing applies YAGNI at an expensive boundary: the outcome executor
has one known future caller and its complete contract is frozen, but it is not
implemented unless the outcome-free mapping proves useful.

### Verifier-only amendment A1

The parent freeze was committed as `9a5e0c43`, plan digest
`c6edade7…d1b05`. Its two raw replays were byte-identical at
`81752a8c…9fc5` and returned `retire_mapping`, with result digest
`8b494ae4…db367`, Origin-row digest `8467942c…8d9d7`, and membership
digest `e1cdae62…82fe6`.

Compact verification then exposed a generic parser defect: the valid empty
`admission_failures` sequence was rejected because mapping sequences default
to nonempty. Amendment `THY-002S-A1` permits emptiness only at the two
admission-failure verifier call sites and adds a regression test. It changes
no source, forecast, Selection, membership, metric, random draw, aggregation,
gate, decision, resource counter, or outcome-access path. No outcome was
opened. The amended plan was frozen before an accepted replay and requires the
same scientific contrasts and decision.

## Estimand And Mapping

For each repository-Origin, `THY-002` predicts a module distribution \(p\)
from full historical Task mass, cutoff-safe historical Git exposure, and
recent Git exposure. For historical Task \(i\), \(x_i\) is its fractional
module-mass vector. With fixed budget \(k=10\), `THY-002S` minimizes:

\[
\left\|\frac{1}{k}\sum_{i\in S}x_i-p\right\|_2^2.
\]

The direct algorithm greedily adds the Task that best approaches \(kp\), then
performs deterministic strict-improvement one-swaps until reaching a local
optimum. Hash ties depend only on the frozen domain, repository, and Task
identity. No outcome, future Task, or time-based tie enters Selection.

Forecast mass on a module absent from historical Task support is not hidden by
renormalization or pseudo-Tasks. The runner reports cold-support mass, module
count, and its Brier lower bound. It rejects an Origin only when all forecast
mass is unrepresentable.

This is intentionally a small direct algorithm. A global integer optimizer,
learned mapper, registry, trainer service, or generic source adapter would add
machinery without a demonstrated caller.

## Source And Evidence Boundary

Stage A uses the common H10 frame of Multi-SWE:

- 1,337 Tasks and 107 Origins across 11 repository-local pools;
- H5 is the first half of each same H10 block, so it is not independent
  replication;
- full-byte source files, projected times, source revision, repository heads,
  and per-repository Task/Origin counts are frozen;
- Origins use only local eligible history and equal-repository aggregation.

Task time is the already-declared GitHub pull-request `createdAt` projection.
Task module attributes come from retrospective reference-fix patches. They are
valid for a source-time-safe counterfactual development study, not native
arrival or a causal claim.

Stage A cannot read the committed Multi-SWE outcome panel even though its
future file identities and decision contract are recorded. Its resource
budget requires zero Agent outcomes, embeddings, paid calls, and sealed
holdout reads.

## Front Gate

Full historical Task distribution is the primary baseline. Equal-budget
random subsets locate the deterministic candidate in the sampling landscape;
they do not replace the baseline. The stationary control uses the identical
Brier coreset mapper targeting full historical Task distribution, which
separates forecast value from compression. Recency is descriptive.

Candidate-minus-control differences are negative when the candidate helps.
All Stage A conditions must pass:

1. all 11 repositories and all 107 Origins are admitted;
2. unchanged `THY-002` forecast beats full history and its Git-only and
   yield-only components at H5 and H10, with H5 interval and repository gates;
3. the mapped Selection beats full history and the stationary coreset at H5
   and H10;
4. H5 has a repository-bootstrap upper bound below zero, at least 7/11
   favorable repositories, every leave-one-repository-out contrast below
   zero, and at least 90th random percentile;
5. H10 is negative in at least 6/11 repositories and reaches at least the
   random median.

The random calibration freezes NumPy 2.5.1, one seed, 20,000 global draw
indices, and 500-draw chunks. One draw index combines one independently
uniform ten-Task subset per Origin, then aggregates repository first.

Failure retires the mapping without outcome replay or rescue tuning. It does
not refute the upstream `THY-002` Task-mix result.

## Frozen Downstream Contract

If and only if Stage A passes, a focused amendment may join the exact frozen
memberships to the 36 complete public Multi-SWE Agent configurations. Per
Agent, the loss is the absolute difference between selected-history pass rate
and future-cohort pass rate. Aggregation is Agent, Origin, repository, then
equal-repository macro-average.

H5 is the sole primary inferential contrast. It must improve full history by
at least `0.005`, have a repository-bootstrap upper bound below zero, favor at
least 7/11 repositories, remain negative under every leave-one-repository-out
view, beat the stationary coreset, reach the 90th random percentile, and have
favorable directions for at least 24/36 configurations, 8/12 models, and 2/3
harnesses. H10 requires a negative macro contrast, at least 6/11 repositories,
the random median, and 19/36 configurations.

The outcome files were opened in earlier research. Passing these gates would
nominate the mechanism on development evidence only. It would not confirm
external validity, authorize the six sealed SWE-bench Verified Agents, or make
the Selector a Runner default.

## Result

Decision: **retire this frozen mapping without Agent-outcome replay**.

The accepted A1 runs were byte-identical:

- raw file SHA-256:
  `8ec69bb21243954323ffd75fd13fbde44bbf5595a8a09431eb73e2011f76a98e`;
- result digest:
  `1980c887a6e9a30ae51389382900b98c505cd1fb74b5d3335d196d1d25d70197`;
- Origin-row digest:
  `8467942c309c4d9e5c67903b9a225d696316e9ce5a527a5cbcc2a9b84828d9d7`;
- membership digest:
  `e1cdae6262504e73159e758d3c4ef092446454a40bf9ef8c6c6ec57b33a82fe6`;
- compact summary digest:
  `8243d4cb689090688d62f7537d0778da7b9916744ca11d5a59eeba190f0f42a6`;
- committed summary file SHA-256:
  `a3eb18abf2de59bdc29a452f7893d39d1fc6e4ee0687a47f29ac5f4d20e66207`.

All 11 repositories and 107 Origins were admitted. Both accepted raw runs
preserved the parent freeze's Origin-row and membership digests exactly. Paid
calls, embeddings, Agent outcomes, and sealed holdout reads were all zero.

Negative differences favor the candidate:

| Horizon and contrast | Macro repository difference | Repository interval | Favorable repositories | Random midrank | Gate |
| --- | ---: | --- | ---: | ---: | --- |
| H5 forecast minus full | `-0.018640` | `[-0.044943, +0.006686]` | 8/11 | n/a | fail |
| H5 Selection minus full | `-0.019114` | `[-0.044455, +0.005761]` | 7/11 | `1.0000` | fail |
| H5 Selection minus stationary | `-0.022645` | `[-0.050094, +0.005967]` | 8/11 | n/a | directional control passes |
| H5 Selection minus recency | `+0.014093` | `[-0.019779, +0.045215]` | 3/11 | n/a | descriptive only |
| H10 forecast minus full | `-0.014866` | `[-0.042076, +0.012627]` | 7/11 | n/a | pass |
| H10 Selection minus full | `-0.015294` | `[-0.041029, +0.011362]` | 7/11 | `1.0000` | pass |
| H10 Selection minus stationary | `-0.015550` | `[-0.044081, +0.014978]` | 7/11 | n/a | directional control passes |
| H10 Selection minus recency | `+0.008836` | `[-0.018247, +0.033442]` | 4/11 | n/a | descriptive only |

The two H5 gates each failed only their predeclared repository-bootstrap upper
bound. Their point estimates, repository counts, Git/yield ablations,
stationary control, random threshold, and every leave-one-repository-out
direction passed. Four repositories had harmful Selection directions at both
horizons: `clap-rs/clap`, `elastic/logstash`, `iamkun/dayjs`, and
`sveltejs/svelte`. No single omitted repository reverses the macro direction,
but repository heterogeneity is large enough that resampling 11
repository-level units still includes zero. Recency has a better point
estimate than the candidate at both horizons, but both descriptive intervals
cross zero and recency was not a frozen gate.

The mapping itself is not the measured loss bottleneck. Selection minus the
continuous forecast is `-0.000473` at H5 and `-0.000429` at H10. Relative to
full-history Brier loss, the discrete subset improves by `5.11%` and `4.04%`.
No one of 20,000 equal-budget random global draws is as good as the candidate
at either horizon. The mean final projection objective is `0.002631`; one-swap
polishing averages `0.52` swaps. Every Origin has some cold-support forecast
mass, but its Origin-weighted mean is `3.15%` and maximum is `18.74%`.

These diagnostics support a narrow mechanism conclusion: Brier projection is
capable of preserving the THY-002 Task-mix forecast in a budget-ten subset.
They do not override the frozen cross-repository uncertainty gate. The
outcome executor remains unauthorized and unimplemented. Do not lower the
gate, tune the mapper, change the budget or horizon, append the two omitted H5
repositories, or open outcomes to rescue this result.

A future route needs a new pre-outcome theory or an independently frozen,
wider source frame whose repository count is justified before replay. It may
reuse the general lesson that the discrete mapping was not the observed
bottleneck; it may not treat these memberships as a nominated Selector.
