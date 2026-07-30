# Multi-SWE Failure-Region Assessment

Date: 2026-07-30.

Status: frozen interpretation of the opened public development panel. This
assessment made no paid call, opened no sealed outcome, and changed no
algorithm.

## Decision

For the current rolling-origin pass-rate MAE claim, the combination of the
Multi-SWE research projection and its 36 public Agent configurations is an
observed failure region.

A failure region is an operating regime where the target claim cannot be
separated reliably from a trivial predictor or from the metric's discrete
support. Barcarolle does not require one Selector to perform well in every
regime. Algorithm research should target the practical main region and report
or abstain outside it instead of sacrificing main-region performance to rescue
an extreme panel.

This decision is conditional on the Task Pool, Agent panel, horizon, and
aggregation. It does not mean that Multi-SWE is corrupt, that every Agent panel
on Multi-SWE will fail, or that the source has no useful Tasks.

## Measured Evidence

The frozen source identities are:

- 1,632 Tasks in 39 repositories;
- 36 complete public Agent configurations;
- 58,752 Agent-Task cells;
- 2,913 positive cells, or `4.9581%`;
- projected GitHub pull-request `createdAt` Task time;
- standard minimum history 20 and Selection budget 10.

The standard H5 and H10 frames produce:

| Diagnostic | H5 | H10 |
| --- | ---: | ---: |
| Repositories | `13` | `11` |
| Origins | `221` | `107` |
| Agent-Origin future blocks | `7,956` | `3,852` |
| All-zero future blocks | `6,652` (`83.61%`) | `2,771` (`71.94%`) |
| Always-zero repository-macro MAE | `0.059870` | `0.060395` |
| Full-history repository-macro MAE | `0.067348` | `0.052807` |
| Always-zero minus full history | `-0.007477` | `+0.007589` |

An all-zero future block means that one Agent configuration fails every Task
in that Origin's future cohort. The always-zero row predicts pass rate `0` for
every Agent and Origin. It is an estimator diagnostic, not a deployable
Selector.

At H5, always predicting zero beats full history and also beats the retained
unseen-target ALG-016U point estimate of `0.064013`. At H10, full history beats
zero, so the panel is not devoid of temporal information. The high all-zero
share still makes absolute MAE small before an algorithm uses any Task
information, and no frozen unseen-target candidate is favorable against full
history at both horizons.

The exact budget-ten hindsight diagnostic reduced full-history loss by
`48.46%` at H5 and `48.51%` at H10. A better subset therefore exists after
future outcomes are opened. The failure is not lack of representational
capacity. The unresolved problem is identifying that subset from pre-Origin
evidence in a response regime where most future Agent-Origin blocks are zero.

The cached-target finite-horizon result does not change this interpretation.
It uses the exact target Agent's historical outcomes and exploits the feasible
pass-rate grid. Its strongest matched result is specific to the B10/H5 grid
mismatch and is not evidence of unseen-Agent Task-content prediction.

## Historical Comparison Correction

The five-Task report
[`boltons-paired-mae-mechanism.md`](../boltons-paired-mae-mechanism.md) is an
H1 mechanism check. It is not the historical Boltons H10 comparison.

The older branch `codex/agent-selection-demo-2026-06-12` contains the relevant
Boltons experiment:

- `experiments/agent_selection_demo/results/frozen_split.json` freezes 20
  visible Tasks and 10 later Tasks;
- `experiments/agent_selection_demo/reports/demo_agent_selection_evidence_zh.md`
  reports full-visible-history to H10 MAE `0.136111` using scoreable pass rates
  and `0.137500` using the scheduled denominator;
- `experiments/agent_selection_demo/reports/selector_baseline_eval_zh.md`
  reports equal-budget random k10 mean MAE from `0.151700` to `0.152775`.

The approximately `0.20` value in the same research period came from the
multi-repository retrospective layer. It reports candidate MAE `0.209011` and
best simple temporal baseline MAE `0.214900` over 18 mixed retrospective
slices. Those rows are not the single Boltons full-history H10 result. The
later SymPy H5 study reports full-history MAE `0.193290`.

These comparisons rule out future block size alone as the explanation for
Multi-SWE's low absolute MAE. H5 and H10 studies on other Task Pool and Agent
combinations produced materially larger errors.

## Research Consequences

Every future pass-rate MAE study must report, before interpreting a candidate:

1. positive outcome density by Agent and repository;
2. all-zero and all-one future-block shares at every declared horizon;
3. always-zero and cutoff-safe historical-climatology baselines;
4. the full eligible history baseline;
5. equal-budget random loss distribution;
6. continuous support and discrete hindsight oracle;
7. candidate improvement over both full history and the strongest trivial
   baseline;
8. the fraction of oracle headroom captured by the candidate when the
   denominator is positive.

One useful normalized diagnostic is:

`captured_headroom = (MAE_trivial - MAE_candidate) / (MAE_trivial - MAE_oracle)`.

It is undefined when the trivial and oracle losses are equal and must not
replace direct MAE. Random percentile remains a separate description of where
the candidate lies in the attainable sampling space.

No universal failure-region threshold is frozen from this opened panel.
Thresholds must follow the intended deployment regime and be declared before
candidate outcomes are inspected. Until that work is complete:

- use this Multi-SWE panel as a sparse-outcome stress test and capacity
  diagnostic;
- do not use it as the primary algorithm-nomination panel;
- do not rescue-tune closed candidates on its opened outcomes;
- do not claim a generally low prediction error from its absolute MAE;
- allow a different Multi-SWE Agent panel to undergo a fresh suitability
  assessment.

## Reproduction Boundary

The calculation reuses:

- Selector plan digest
  `6619ab258039d3f12cf865421faeba7c23248b302f72b06bb6f311b8f65bde05`;
- panel digest
  `f2658d12451bdab4108a71cfae5cd5044a5bd312633239c09425378b4b682deb`;
- resolved-outcome digest
  `b9a6d0d8e44d747d23789ec23eb4205178f2ae2d4f737c2446a5fcdf5abc116c`;
- Task-time projection digest
  `56eb7dda0d7fd9787b1e77c432572f212726b92abc189df18ab2a4fe6bb815e5`.

Origins are rebuilt with the committed complete, non-overlapping
`build_repository_origins` implementation. Always-zero MAE applies the same
configuration-within-Origin, Origin-within-repository, then equal-repository
aggregation used by the frozen studies.
