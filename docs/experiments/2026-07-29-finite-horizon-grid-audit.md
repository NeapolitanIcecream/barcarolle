# Matched Finite-Horizon Grid Audit

Date: 2026-07-29.

## Result

The frozen matched audit terminates as `grid_dominant`.

| Cell | Plug-in MAE | Full MAE | Plug-in − full | H-blind MAE | Plug-in − H-blind | Paired repository 95% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B5/H5 | `0.051289` | `0.065433` | `-0.014144` | `0.051537` | `-0.000248` | `[-0.003337, +0.003425]` |
| B5/H10 | `0.050577` | `0.052807` | `-0.002230` | `0.050110` | `+0.000467` | `[-0.001122, +0.002842]` |
| B10/H5 | `0.051289` | `0.065433` | `-0.014144` | `0.061460` | `-0.010171` | `[-0.015755, -0.004738]` |
| B10/H10 | `0.048728` | `0.052807` | `-0.004079` | `0.049412` | `-0.000684` | `[-0.002681, +0.001591]` |

Only B10/H5 has a stable advantage over the same-budget H-blind control.
Its absolute contrast is more than twice every other cell, while the two
equal-grid cells B5/H5 and B10/H10 do not both have negative interval upper
bounds. This satisfies the plan's frozen `grid_dominant` definition and
rejects `general_support`.

The finite-horizon plug-in rule remains a useful grid-aware cached-result
baseline and contract-specific score/action adapter, but the evidence does not
support a generally better Selector. The large H5 result is principally a
B10/H5 evaluation-grid effect on this zero-heavy panel, not improved
prediction of future Task content or temporal regimes.

## Why This Audit Was Needed

The preceding study compared standard H5 and H10 frames with different
repositories and Origins. Two independent audits found no implementation
error, but identified finite-grid geometry as the leading explanation for the
large H5 gain.

This plan was frozen after that observation and before reading any crossed-cell
score. It uses the standard H10 frame for every cell:

- 107 repository-local Origins in 11 repositories;
- 36 public model/harness configurations;
- 3,852 configuration-Origin rows per cell;
- minimum history 20;
- H5 is exactly the first five Tasks of the same Origin's ten-Task future
  block.

The matched frame removes the previous repository/Origin composition
confound. All outcomes remain opened, so this is mechanism characterization,
not independent confirmation.

## Methods And Contract

For history size \(n\), successes \(s\), budget \(B\), future count \(H\), and
future success count \(K\):

- H-blind chooses feasible \(q\) nearest to \(s/n\);
- `ALG-018C-P` chooses feasible \(q\) minimizing exact
  \(\operatorname{E}|q/B-K/H|\) under
  \(K\sim\operatorname{Binomial}(H,s/n)\);
- `ALG-018C` replaces the plug-in distribution with the Jeffreys
  Beta-Binomial posterior predictive distribution.

The plug-in rule is primary because it is the KISS isolation of finite-H/grid
geometry. Jeffreys is a fixed sensitivity. Both use exact integer arithmetic
and the same newest-within-success/failure-cell materializer. No parameter,
prior, method, budget, horizon, or tie was selected from the crossed scores.

The frozen H-blind control breaks exact rate-distance ties toward lower \(q\).
The preceding implementation instead breaks such ties using visible Task
priority. A post-score sensitivity using that older tie rule preserves the
scientific conclusion:

| Cell | Plug-in − visible-priority H-blind | Paired repository 95% |
| --- | ---: | ---: |
| B10/H5 | `-0.009792` | `[-0.015591, -0.004151]` |
| B10/H10 | `-0.000305` | `[-0.002553, +0.002161]` |

B5 memberships are unchanged by this tie sensitivity. The sensitivity is not
part of the frozen terminal decision.

## Mechanism Evidence

### Crossed Cells

B5/H5 and B10/H5 produce exactly the same plug-in selected rates and MAE. Their
selected success counts are scaled representations of the same fifth-grid:

- B5/H5 plug-in \(q\): 0 in 3,669 cells, 1 in 171, 2 in 12;
- B10/H5 plug-in \(q\): 0 in 3,669 cells, 2 in 171, 4 in 12.

The B10 success count is exactly twice the B5 count in all 3,852 rows, so B10
provides no additional prediction in this comparison. In general the common
score support is governed by \(\gcd(B,H)\). When \(B>H\) and \(H\) divides
\(B\), the Selection grid contains values that a realized H-Task future rate
cannot take; B10/H5 is exactly this case.

The difference is the H-blind action. B5/H5 already lives on the future
fifth-grid, so the plug-in improvement over H-blind is only `-0.000248` and
its interval crosses zero. B10/H5 lets H-blind express intervening tenths;
the finite-H action changes 1,173/3,852 cells and improves by `-0.010171`,
with 10/11 repositories favorable and every leave-one-repository-out
aggregate favorable.

B5/H10 is the reverse mismatch: the Selection fifth-grid is coarser than the
future tenth-grid. The plug-in point estimate is `+0.000467` worse than
H-blind, with only 3/11 repositories favorable. B10/H10 has aligned tenth
grids and only a weak `-0.000684` point estimate whose interval crosses zero.

No cell's theoretical action is changed by success/failure inventory.
Jeffreys and plug-in differ in only 12, 30, 12, and 36 of 3,852 cells for
B5/H5, B5/H10, B10/H5, and B10/H10. Their MAEs remain practically
indistinguishable; the evidence is about the finite-H action family, not the
Jeffreys prior.

### Horizon Swap

At B10, using an action built for the wrong declared horizon is harmful:

| Evaluated future | Wrong action | Wrong − matched action MAE |
| --- | --- | ---: |
| H5 | H10 action | `+0.005789` |
| H10 | H5 action | `+0.001834` |

For H5, only 1/11 repositories favors the wrong action; for H10, 4/11 do.
This establishes that declared future count changes the loss-optimal cached
action on this panel. It does not establish prediction of the count itself.

### Random Landscape

Plug-in random midrank is `1.0` in the first three cells and `0.9999` in
B10/H10. H-blind is also at `1.0`, `1.0`, `0.9818`, and `0.9997`. These values
show that both deterministic cached-result compressors occupy an extreme part
of the equal-budget random landscape. They are not p-values and do not replace
the paired H-blind comparison.

## Independent Audit

The final independent audit passed. It rebuilt the 107-Origin matched frame,
verified every H5 prefix and history-only membership, replayed corrected
memberships, recomputed scores, bootstraps, random calibration, LOO,
horizon-swap diagnostics, and the terminal decision, and found zero mismatch.
It also confirmed that old and corrected scientific payloads differ only in
the four exact-zero favorable-repository counts recorded by the amendment.
All 28 parent-plus-grid directed tests passed.

## Claim Boundary

The valid claim is:

> Given complete same-configuration historical binary outcomes and a
> predeclared finite future Task count, exact loss/grid-aware compression can
> reduce realized future pass-rate MAE relative to full history; on this panel,
> its stable incremental advantage over an H-blind compressor is confined to
> the B10/H5 grid-mismatch cell.

The method contract is the tuple of cached Result identity and availability
policy, \(B\), declared \(H\), absolute-error loss, and the realized
\(K/H\) estimand. Changing any element requires a new action; memberships are
not interchangeable across horizons.

The public source has no native Result availability timestamp and does not
prove the complete production Agent fingerprint. The experiment assumes
same-configuration history was cached by each projected Task cutoff. It
therefore does not establish:

- real cutoff-safe Result availability or exact production Agent identity;
- behavior with partial, stale, or missing-not-at-random caches;
- unseen-Agent or changed-Agent Selection;
- latent capability estimation;
- Task-content, temporal-regime, or causal prediction;
- prospective validity, Task Pool certification, or a production default.

If the estimand is latent pass probability rather than the realized rate of a
known-size future cohort, H should not enter the action. In that setting this
method optimizes the evaluation grid rather than the desired quantity.

## Reproduction

Plan digest:
`8388fc583f7acf68a27c1864b673de91d87e895e2384366461ba87c00f2c4b1d`.
Direction-classification amendment:
`80dd4596ef3bbff45b859245960fb98bc352432f839e992d6c29703b29bf618c`.
Execution lock:
`03c2dbfb526b50d4a2b010cdb132ccd6087eca43fa2e20790c330c1c8b8fcaa5`.

The amendment records that an exact-zero B5/H5 repository difference was
represented near `-6.17e-20`. It freezes a `1e-15` zero tolerance for direction
counts only. Corrected replay changes four B5/H5 favorable-repository counts
by one; memberships, MAE, intervals, LOO directions, random results, horizon
swap, and `grid_dominant` are unchanged.

Two complete membership runs are byte-identical:

- logical digest:
  `9427c9a0ad57910ad1cb757b04eac60c9ca3f7d05e4553c0025f69bae9052631`;
- raw SHA-256:
  `1d770a2051ab45a7263bbb78dc3fdaa5f8bad77524d3c197a04a83c044fe8a47`;
- raw size: 18,102,822 bytes.

Two complete score runs are byte-identical:

- logical digest:
  `f841611418a2d7cb1485f77e0b76270f47aff538071e9c3d32f22bfeeee2e30a`;
- raw SHA-256:
  `d7d92c6df7552b32a17eb002918279f9a4dc51852d1e36139f4a49b055c6b630`;
- raw size: 100,347 bytes.

Raw outputs remain ignored under
`outputs/research/2026-07-29-finite-horizon-grid-audit/`. The run used CPython
3.14.0, NumPy 2.5.1, and SciPy 1.16.3. It made no paid API call, new
Agent-outcome call, embedding call, or sealed holdout read, and added no core
schema or runtime service.

Committed compact evidence is
[`examples/finite_horizon_grid_audit/evidence/summary.json`](../../examples/finite_horizon_grid_audit/evidence/summary.json);
its self-excluding digest is
`32c388c8931840a0a9c87b6fd94898858a7c4d0dfbbf25986d227f04216e909a`.

## Decision

1. Retain the plug-in finite-H median as the canonical grid-aware
   cached-result research baseline. Keep Jeffreys only as a fixed sensitivity;
   do not ensemble or tune the prior.
2. Do not promote the family as a general Selector. Its stable incremental
   gain is specific to B10/H5 on this opened panel.
3. Keep H-blind quantized history when future count is unknown. Require an
   explicit known count before using a finite-H action.
4. Preserve `ALG-016U` separately as the best unseen-target H5 point estimate;
   the cached family supplies no evidence for that information contract.
5. Close cached scalar/grid search on these opened outcomes; do not sweep more
   budgets, horizons, priors, ties, or smoothing values. A
   broader cached-result claim needs a new source with Result availability and
   complete Agent identity, or prospective evidence. A broader unseen-target
   claim needs an independently motivated mechanism and evidence boundary.
