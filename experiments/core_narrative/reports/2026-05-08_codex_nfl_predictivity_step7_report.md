# Barcarolle Click G/R/W Predictivity Step 7 Report

Generated: 2026-05-08T17:50:48.147731Z

## Scope

This report compares the Click RBench canonical evidence against the held-out Click RWork slice for the four core ACUTs. It also records G_score status from the pinned SWE-Bench Pro configuration.

## Method

- R_score is the canonical-latest fixed-denominator pass percentage from the 4 ACUT x 8 Click RBench matrix.
- W_score is the canonical-latest fixed-denominator pass percentage from the 4 ACUT x 6 Click RWork matrix.
- Canonical latest chooses the highest scoreable attempt for each ACUT/task cell. Provider/infra retries are retained as artifacts but do not replace scoreable evidence.
- G_score uses only direct SWE-Bench Pro execution when feasible; this run did not substitute public, external, or proxy scores.

## Result

- R_score vs W_score error status: `computed`.
- G_score vs W_score error status: `not_computable`.
- G_score basis: `direct_gscore_blocked`; direct G_score used: `False`.
- Ranking reversal claim: `not_supported`.

## Scores

| ACUT | R_score | W_score | G_score basis |
| --- | ---: | ---: | --- |
| `cheap-click-specialist` | 62.5 | 33.3 | unavailable |
| `cheap-generic-swe` | 62.5 | 16.7 | unavailable |
| `frontier-click-specialist` | 62.5 | 16.7 | unavailable |
| `frontier-generic-swe` | 75.0 | 16.7 | unavailable |

## Confidence

| ACUT | R passed/total | R Wilson 95% | W passed/total | W Wilson 95% |
| --- | ---: | ---: | ---: | ---: |
| `cheap-click-specialist` | 5/8 | 30.6-86.3 | 2/6 | 9.7-70.0 |
| `cheap-generic-swe` | 5/8 | 30.6-86.3 | 1/6 | 3.0-56.4 |
| `frontier-click-specialist` | 5/8 | 30.6-86.3 | 1/6 | 3.0-56.4 |
| `frontier-generic-swe` | 6/8 | 40.9-92.9 | 1/6 | 3.0-56.4 |

## Rank And Error

- R rank order: 1. frontier-generic-swe (75.0), 2. cheap-click-specialist (62.5), 3. cheap-generic-swe (62.5), 4. frontier-click-specialist (62.5).
- W rank order: 1. cheap-click-specialist (33.3), 2. cheap-generic-swe (16.7), 3. frontier-click-specialist (16.7), 4. frontier-generic-swe (16.7).
- R->W MAE: 44.79 percentage points.
- R->W RMSE: 45.98 percentage points.
- R->W mean signed error: 44.79 percentage points.

## Distributions

- RBench canonical status counts: failed=7, invalid_submission=4, passed=21.
- RBench canonical failure labels: failed=7, invalid_submission:search_replace_anchor_mismatch=1, invalid_submission:search_replace_old_occurrence_mismatch=3, passed=21.
- RBench future-contract metadata gaps: direct_runner_budget_gate=17, direct_runner_cost_ledger_append=17.
- RWork canonical status counts: failed=3, invalid_submission=16, passed=5.
- RWork canonical failure labels: failed=3, invalid_submission:search_replace_anchor_mismatch=1, invalid_submission:search_replace_old_occurrence_mismatch=14, invalid_submission:unsupported_patch_response=1, passed=5.
- RWork future-contract metadata gaps: {}.

## G Score

- Status: `direct_gscore_blocked`.
- Basis: `direct_run_unavailable`.
- Direct G_score values are unavailable and are not treated as zero.
- Blocker: `dataset_cache_missing`.
- Blocker: `evaluation_harness_checkout_missing`.

## Interpretation

No ranking reversal conclusion is supported: W_score has a bounded held-out Click slice, but direct G_score is unavailable and the R/W sample is too small for stable reversal claims.

R_score/W_score comparisons are based on small Click-only samples, so the numbers are diagnostic rather than proof of a stable ranking law. Missing direct G_score prevents any supported claim that repository-specific RBench is more predictive than a general benchmark under matched conditions.

This run does show a Click-only mismatch: R_score overestimated W_score for all four ACUTs, and the R rank leader (`frontier-generic-swe`) tied for last by W_score. That is a warning signal, not a ranking-reversal proof.

## Reproduction

1. Run `codex_nfl_canonical_matrix.py --split rbench` against the normalized result root.
2. Run `codex_nfl_canonical_matrix.py --split rwork` against the same normalized result root.
3. Run `codex_nfl_gscore_basis.py` to record direct G_score feasibility from `general_benchmark.yaml`.
4. Run `codex_nfl_predictivity_analysis.py` with the RBench matrix, RWork matrix, and G_score basis JSON artifacts.
