# Multi-SWE Regime Assessment

Date: 2026-07-30.

Status: revised interpretation of the opened public development panel after
independent audit. This assessment made no paid call, opened no sealed outcome,
and changed no algorithm.

## Decision

The earlier combined `H5/H10 failure region` label was too broad.

Under the frozen end-aligned, equal-repository, scheduled-denominator,
shared-unseen-target estimator view, H5 is dominated by the always-zero
estimator: full history and every retained unseen-target candidate have higher
MAE. This blocks a nontrivial-prediction interpretation for that view.

H10 is not a frozen failure or success region. Full history has a lower point
estimate than zero under the primary aggregation, but the sign is sensitive to
repository weighting, Origin anchoring, and cohort construction. Those
post-result sensitivities require a bound experiment before they can become
gates.

The two rows use different repository and Origin frames. A candidate changing
sign across them fails its predeclared cross-frame robustness requirement; the
change cannot be attributed to horizon size alone.

This does not erase a separately measured Selection/compression result. A
budgeted candidate may improve full history even when it does not beat a
prevalence-only estimator. A strong predictive nomination needs both claims,
but they must be reported separately.

The finding is conditional on the Task Pool, Agent panel, Selection unit,
information contract, horizon frame, denominator, and aggregation. It does not
mean that Multi-SWE is corrupt, that every Agent panel on Multi-SWE will fail,
or that the source has no useful Tasks.

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
| Always-zero equal-repository MAE | `0.059870` | `0.060395` |
| Full-history equal-repository MAE | `0.067348` | `0.052807` |
| Always-zero minus full history | `-0.007477` | `+0.007589` |

An all-zero future block means that one Agent configuration fails every Task
in that Origin's future cohort. The always-zero row predicts pass rate `0` for
every Agent and Origin. It is an estimator diagnostic, not a deployable
Selector.

At H5, always predicting zero beats full history and also beats the retained
unseen-target ALG-016U point estimate of `0.064013`. At H10, full history beats
zero only as a primary-estimand point estimate. That difference is not by
itself proof of usable temporal information. The high all-zero share makes
absolute MAE small before an algorithm uses Task information, and no frozen
unseen-target candidate is favorable against full history in both frames.

The exact budget-ten hindsight diagnostic reduced full-history loss by
`48.46%` at H5 and `48.51%` at H10. A better subset therefore exists after
future outcomes are opened. The opened panel has representational capacity.
Whether the observed chronology contains candidate-independent pre-Origin
signal, and whether the current repository count can resolve it, remain
separate questions.

The cached-target finite-horizon result is a separate information contract. It
uses the exact target Agent's historical outcomes and exploits the feasible
pass-rate grid. It is a counterexample to labeling the whole frame
`trivial-dominated`, but it is not evidence of unseen-Agent Task-content
prediction.

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
3. always-zero and always-one baselines, plus a fully specified cutoff-safe
   climatology only when its target or reference outcomes are admitted by the
   candidate's information contract;
4. the full eligible history baseline;
5. equal-budget random loss distribution;
6. continuous support and discrete hindsight oracle;
7. the Selection/compression contrast against full history and position in the
   equal-budget random landscape;
8. the nontrivial-prediction contrast against a contract-matched trivial
   estimator;
9. full-history-to-oracle selection headroom and the fraction captured by a
   candidate when the denominator is positive.

The primary normalized Selection diagnostic is:

`selection_capture = (MAE_full - MAE_candidate) / (MAE_full - MAE_oracle)`.

A separate estimator diagnostic is:

`captured_headroom = (MAE_trivial - MAE_candidate) / (MAE_trivial - MAE_oracle)`.

Each ratio is undefined when its denominator is nonpositive or its rows do not
share the exact Task, Check, Agent, Origin, denominator, weighting, budget, and
oracle contract. Neither replaces direct MAE. Random percentile remains a
separate description of where the candidate lies in the attainable sampling
space.

No universal suitability threshold is frozen from this opened panel.
Thresholds must follow the intended deployment regime and be declared before
candidate outcomes are inspected. Until that work is complete:

- use H5 as an unseen-target estimator stress view and both rows as capacity
  diagnostics;
- do not use it as the primary algorithm-nomination panel;
- do not rescue-tune closed candidates on its opened outcomes;
- do not claim a generally low prediction error from its absolute MAE;
- allow a different Multi-SWE Agent panel to undergo a fresh suitability
  assessment.

The frozen next experiment is the candidate-free null-and-headroom audit in
[`suitability-audit-plan.json`](../../examples/multi_swe_research/suitability-audit-plan.json).
It separates prevalence support, selectable capacity, temporal alignment, and
repository-level resolution without testing another candidate.

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

The pooled-Origin, repository-omission, start-aligned, split-H10, and expanding
climatology values in the independent audit are post-result robustness
diagnostics. They motivate the new frozen audit; they are not silently promoted
to thresholds here.
