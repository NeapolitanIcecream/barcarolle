# THY-002 Generator-Calibrated Module Exposure

Date: 2026-07-29.

## Decision Before Replay

Freeze one outcome-free test of `THY-002`. Do not tune it after future
Task-module replay.

The exact machine contract is
[`plan.json`](../../examples/generator_calibrated_exposure/plan.json), digest
`0fe42fc1…1c69`. It binds the implementation, source bytes, canonical
repository lineage, Git refs and heads, Task identities, formula, nested
Origins, metric, aggregation, gates, and forbidden changes.

No Agent outcome, sealed holdout, paid call, or embedding may enter this study.

The source-loader audit parsed reference patches before this freeze to verify
deduplication, path handling, and exact frame identities. It did not construct
Origins, calculate losses, inspect a candidate contrast, or search any
algorithm parameter. This is therefore a pre-metric freeze, not a claim that
source labels were cryptographically unread before implementation.

## Why This Is A New Theory

`THY-001R` treated recent Git activity as the future Task distribution. It beat
short Task history and simpler Git controls but lost consistently to full Task
history. Its missing variable is not another half-life: an automated Generator
does not turn every code touch into an admitted Task at the same rate.

For one repository, module \(m\), and Origin \(O\), define:

- \(T_m(O)\): full historical admitted-Task mass;
- \(E_m(O)\): eligible Git touch exposure since the repository's fixed source
  observation start;
- \(G_m(O)\): the same exposure with the frozen 365.25-day age kernel.

The mechanism hypothesis is:

\[
\text{future admitted Task intensity}_m
\propto
\text{current exposure}_m
\times
\text{Generator admission yield}_m.
\]

This remains conditional on a fixed Generator and admission policy. It tests
an association on the explicit source-time projection; it does not claim
native event-time causality or that admitted benchmark Tasks exhaust real
software work.

## Frozen Estimator

A raw \(T_m/E_m\) ratio is undefined for cold-start modules. Adding the same
constant to Tasks, historical exposure, and current exposure would be
dimensionally invalid. The frozen estimator instead uses one repository-scale
empirical rate shrinkage:

\[
\rho(O)=\frac{\sum_m T_m(O)}{\sum_m E_m(O)},\qquad
\beta(O)=\frac{1/2}{\rho(O)},
\]

\[
\widehat q_m(O)=
\frac{T_m(O)+1/2}{E_m(O)+\beta(O)},
\qquad
p_m(O)=
\frac{G_m(O)\widehat q_m(O)}
{\sum_jG_j(O)\widehat q_j(O)}.
\]

The regularizer has the repository-global Task-per-touch mean and exactly
one-half Task of mass. Its denominator is measured in touches. It is fixed,
not fit across repositories or selected from observed future scores. This
form is motivated by Gamma-Poisson rate shrinkage, but Tasks and commits split
mass across modules, so it is not claimed as an exact conjugate posterior.

No mass is added to \(G_m\). A module with zero recent exposure gets zero
candidate mass. A repository-Origin with no historical or recent exposure is
a source failure rather than a fallback forecast.

If a module has historical Task mass but zero observed historical Git
exposure, the fixed shrinkage estimate remains finite. The runner reports the
count and Task mass of those cases rather than dropping them or pretending
that a literal Poisson likelihood generated the fractional observations.

The two mechanistic controls are:

- \(p_m\propto G_m\), which removes Generator calibration;
- \(p_m\propto\widehat q_m\), which removes current exposure.

Full Task history remains the primary baseline. Recent Task history and
uniform mass are descriptive controls.

Git exposure walks the complete reachable non-merge DAG with
`--since-as-filter`, then reapplies timestamp bounds after commit projection.
This prevents an old-timestamp ancestor from pruning a deeper in-window commit
when repository clocks are not monotone.

Git `--name-only` paths are already repository-relative, so real top-level
directories named `a` or `b` are preserved. Diff headers remove exactly one
synthetic side prefix before using the same module map. Git names use NUL
delimiters so whitespace and non-ASCII paths are not changed by display
quoting.

## Why Brier Score Is Primary

Structural zero recent exposure is part of the hypothesis. Cross-entropy would
require an arbitrary epsilon chosen only to make zero probabilities finite.
The primary loss is therefore multiclass Brier score, a proper score that
accepts zeros. Multi-module Tasks split their target mass uniformly. Total
variation is descriptive only.

Each Origin is averaged within its canonical repository; all 40 repositories
then receive equal weight. H5 is the first half of the same non-overlapping H10
block and is not an independent replication.

For both H5 and H10, the candidate must:

1. beat full Task history in macro-repository loss;
2. have a repository-bootstrap upper bound below zero;
3. beat full Task history in at least 24/40 repositories; and
4. beat both current Git exposure alone and Generator yield alone, with each
   ablation contrast's repository-bootstrap upper bound below zero.

All conditions must pass. A failure retires the theory without changing the
prior, half-life, exposure window, module map, source threshold, repository
membership, timestamp policy, metric, horizon, or gate.

## Independent Source And Lineage

SWE-rebench V2 is an automated Generator family separate from Multi-SWE and
SWE-bench Full. Its paper describes a funnel that mines public GitHub activity,
requires issue-linked merged PRs with tests, synthesizes repository setup,
executes pre/post-fix tests, filters issue clarity, and retains stable results
across three validation runs. The release contains 32,079 Tasks from 3,617
repositories across 20 languages
([paper](https://arxiv.org/html/2602.23866v2),
[pinned dataset](https://huggingface.co/datasets/nebius/SWE-rebench-V2/tree/475dd5e8703bb5fb22dd3c60b5d038b019eba1e0)).

The local parquet is pinned by SHA-256
`0e0bf935…d3ad`. Before patch replay, a metadata-only audit selected every
source repository with at least 75 rows, then resolved exact GitHub lineage:

- `analysis-dev/diktat` and `cqfn/diKTat` collapse to
  `saveourtool/diktat`;
- `argoproj/argo` resolves to `argoproj/argo-workflows`;
- `Qiskit/qiskit-terra` resolves to `Qiskit/qiskit`;
- `rust-analyzer/rust-analyzer` resolves to `rust-lang/rust-analyzer`.

The two Diktat aliases contain 83 duplicate PRs. Exact canonical PR identity
deduplication yields 5,365 Tasks in 40 repositories. No repository is selected
by a score, replaced after failure, or mixed with another repository at
runtime. Multiple repositories are only equal-weight offline evidence units.
The frozen loader recomputes the raw `>=75` census and requires its 41 aliases
to equal the plan, then checks the 40 canonical-repository count. A named
branch records freeze-time provenance; its pinned commit object, not the later
live position of that branch, is authoritative during replay.

All source `created_at` values are timezone-naive. The frozen projection
assumes UTC for counterfactual development and does not call this native
calendar evidence. Reference patches supply historical candidate attributes
and future scoring labels. Their lineage is explicit; a later strict campaign
would need arrival-native attributes.

The projected Task clock and Git clock are not the same event clock:
`created_at` orders Tasks while commit timestamps define exposure. A reference
patch can also mature after the projected Task time. This is allowed by the
counterfactual-development contract, but it limits the result to a
projected-timeline association rather than a native causal thinning claim.

The runner records whether each declared `base_commit` exists in the pinned
Git object graph and binds that diagnostic to the repository manifest. Missing
objects do not reject a Task: this Task-mix experiment never checks out a Task
base and its frozen inputs are source time, reference-patch modules, and
cutoff-safe Git exposure. Making object presence an admission gate would add a
strict provenance condition unrelated to the tested mechanism.

Before aggregation, the verifier rejects unknown repositories, horizons other
than H5/H10, missing or extra numbered Origins derived from the frozen Task
counts, duplicate repository-Origin-horizon rows, and an Origin missing either
member of its H5/H10 pair. It also verifies the study identity and all four
zero-use counters for paid calls, embeddings, Agent outcomes, and the sealed
holdout before replaying summaries and the decision.

## Stop Boundary

A Task-mix pass would support the generator-calibrated exposure mechanism on a
new Generator family. It would not establish Agent-score prediction,
benchmark validity, a production Selector, or strict prospective validity.

Only after a pass may another plan specify how the predicted module mix becomes
an absolute-budget Selection and how it compares with the unselected benchmark
and equal-budget random sampling on Agent outcomes. The current study never
opens those outcomes.

## Frozen Result

Decision: **pass the Task-mix gate; retain THY-002 for a separately frozen
Selection study**.

`task-mix-results.json` and `task-mix-results-reproduction.json` were
byte-identical:

- raw file SHA-256:
  `449e10c195f07e98e89644ce9957bfbaab23fd9d03c320fe10ac3b7efe9d6ac8`;
- result digest:
  `d0666c4e70f4195eb4c81fa1d143a947cbcf8e3fe718136193f82459d0e3ff94`;
- Origin-row digest:
  `68cf05b816e06dd37b9c839223df3af7763da0afe894a4105847d502182f7775`;
- compact-summary digest:
  `26233a425ecea7794df236ea991139eaa673b1569fc88262ddd2b31b9f8eaa31`.
  Its committed file SHA-256 is
  `7b97318cf617dcd1e324774a69de628cef5f69288dd11e7826ba1c61436f470a`.

All 40 repositories and all 436 planned Origins were admitted. Negative
contrasts favor THY-002:

| Horizon | Candidate Brier | Full history | Candidate − full | 95% repository bootstrap | Favorable repositories |
| --- | ---: | ---: | ---: | ---: | ---: |
| H5 | 0.369901 | 0.376463 | -0.006562 | [-0.010743, -0.002855] | 27/40 |
| H10 | 0.381399 | 0.387505 | -0.006107 | [-0.009734, -0.002796] | 28/40 |

The relative loss reductions against full Task history are 1.74% at H5 and
1.58% at H10. The effect is modest, but its sign is stable across both nested
horizons and clears the frozen repository-bootstrap and 24/40 breadth gates.
Deleting any one repository keeps the macro contrast negative: H5 ranges from
`-0.007095` to `-0.005745`, and H10 from `-0.006580` to `-0.005328`.
However, the median per-repository gains are only `0.00125` and `0.00249`;
13/40 and 12/40 repositories worsen. The mechanism is stable but heterogeneous.
H5 and H10 repository contrasts correlate at `0.963`, and H5 is nested inside
H10, so the two passes are horizon stability evidence rather than independent
replications.

The two mechanism ablations fail more clearly:

| Horizon | Candidate − recent Git | 95% interval | Candidate − yield only | 95% interval |
| --- | ---: | ---: | ---: | ---: |
| H5 | -0.068670 | [-0.096032, -0.044543] | -0.215530 | [-0.280333, -0.157310] |
| H10 | -0.062451 | [-0.089843, -0.038698] | -0.208163 | [-0.270839, -0.149657] |

This supports the multiplicative mechanism: neither current exposure nor
historical Generator yield alone explains the result. Candidate mean loss also
beats trailing-H Task history at both horizons, although the H10
candidate-minus-trailing interval crosses zero; trailing history was a
descriptive control, not a frozen gate.

## Diagnostics And Interpretation

- The realized H5 and H10 future spans average 56.7 and 118.8 days after
  repository-first aggregation. Across Origins, medians are 23.5 and 54.0
  days, while maxima reach 1,207.0 and 1,376.3 days. Task-count horizons
  therefore represent variable calendar ranges, not fixed short-term
  forecasts.
- Future `OTHER` mass is 3.51% at H5 and 4.01% at H10. The gain is not an
  artifact of a vocabulary that absorbs most future work.
- All 5,034 unique declared base-commit objects checked by repository
  manifests are present; no Origin contains a reachable commit dated after its
  cutoff.
- 100/436 Origins contain at least one historical Task module with zero
  observed historical Git exposure; 122 module-Origin cases carry 117.24
  units of Task mass. This confirms that the empirical-shrinkage interpretation
  is necessary. It does not invalidate the fixed score, but a literal Poisson
  posterior claim would have failed on the actual data.
- Paid calls, embedding calls, Agent outcomes, and sealed-holdout reads are all
  zero.

The result resolves the immediate theory question: a fixed Generator's
historical Task-per-exposure association adds a small but reproducible
pre-Origin signal beyond the unselected full Task history on a new Generator
family. It does **not** yet show that a ten-Task benchmark compiled from that
forecast predicts future Agent performance better than the full benchmark.

The next admissible experiment must freeze, before reading its evaluation
contrasts:

1. one deterministic absolute-budget mapping from the forecast distribution to
   historical Tasks;
2. full-history and equal-budget random Selection baselines;
3. repository-first future Agent-response loss, random-landscape position,
   Agent breadth, and H5/H10 gates; and
4. exact reuse boundaries for already-open public Agent results.

No production Selector or Agent-outcome replay is authorized by this result
alone.
