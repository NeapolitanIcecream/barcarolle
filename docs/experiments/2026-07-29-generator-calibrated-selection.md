# THY-002S Generator-Calibrated Selection

Date: 2026-07-29.

## Decision Before Replay

Freeze a sequential study rather than building an outcome layer speculatively.
Stage A first tests the forecast-to-Selection mapping entirely in Task space.
Only a Stage A pass authorizes a narrow amendment that can reuse already-open
public Agent outcomes. No paid call or sealed holdout access is authorized.

The machine contract is
[`plan.json`](../../examples/generator_calibrated_selection/plan.json), digest
`c6edade7…d1b05`. It binds code, source bytes, Git heads, 1,337 Tasks, 107
nested Origins in 11 repositories, the upstream `THY-002` result, budget,
mapping, controls, random sampler, gates, and the downstream outcome contract.

This sequencing applies YAGNI at an expensive boundary: the outcome executor
has one known future caller and its complete contract is frozen, but it is not
implemented unless the outcome-free mapping proves useful.

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

Pending frozen Stage A replay.
