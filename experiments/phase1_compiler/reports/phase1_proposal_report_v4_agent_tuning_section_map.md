# Phase 1 Proposal Report V4 Agent-Tuning Section Map

Status: complete, 2026-06-01.

This map records where V4 should integrate agent tuning into
`docs/research/phase-1-proposal-report-v3.md`. The conclusion is that V4 can
be a targeted revision: V3 already has the proposal genre, eleven-section
shape, evidence boundary, validation path, and ACUT boundary.

## Required V3 Search

Command:

```text
rg -n "tuning|optimizer|scorecard|failure|regression|canary|dev/eval|configuration" docs/research/phase-1-proposal-report-v3.md
```

Useful matches:

- Executive summary already names the ACUT configuration question and the
  stronger-validation path, but it does not yet explain that the practical
  application is configuration selection, tuning, and regression monitoring.
- Problem and stakes already says the stakes are "evaluation, tuning, and
  governance"; it needs concrete reader questions for agent developers and
  repo owners.
- Barcarolle thesis and boundary already separates Barcarolle from the ACUT
  harness; it should clarify that Barcarolle can emit tuning feedback while the
  ACUT or optimizer owns prompt, retrieval, skill, tool, test-policy, and
  budget changes.
- Proposed design already includes `tuning or evaluation objective O` and a
  "Tuning and evaluation interfaces" layer; this is the main local expansion
  point.
- Validation strategy already separates retrospective replay from future
  validity evidence; it needs one guardrail paragraph explaining why tuning
  workflows require dev/eval/canary or holdout protection.
- Project plan already has reporting and governance outputs; it should add a
  work package for tuning and regression feedback interfaces.
- Risks already cover post-hoc validation and budget readiness; they should add
  a distinct objection that optimizer loops can overfit benchmark dev tasks.
- Expected deliverables already include adapter-stratified scorecards; it
  should add optimizer-readable scorecard schemas, split management,
  tuning/regression templates, failure taxonomy, and canary/holdout rules.
- Appendices can carry one short future-extension note: multi-ACUT residual
  predictive validity and formal tuning-loop validation remain later work.

## Targeted Edit Plan

| V3 section | V4 action | Claim guardrail |
| --- | --- | --- |
| 1. Executive Summary | Add one short paragraph after the release-construction paragraph connecting predictive benchmarks to configuration selection, tuning, and regression monitoring. | Do not claim tuning improvement has been shown. |
| 2. Problem And Stakes | Expand the existing stakes paragraph with concrete questions about retrievers, test-running policy, prompt/skill/retrieval changes, model upgrades, and critical task-family regressions. | Keep target-repository prediction as the central problem. |
| 4. Barcarolle Thesis And Boundary | Add a boundary paragraph that Barcarolle supplies splits, scorecards, labels, and regression signals, but the ACUT or optimizer owns the loop that changes the agent. | Do not reimplement ACUT internals. |
| 5. Proposed Benchmark-Compiler Design | Expand the "Tuning and evaluation interfaces" layer and release description to include dev/eval/canary splits, optimizer-readable outputs, cost/latency, source-quality limits, failure taxonomy, and regression labels. | Keep this as interface design, not evidence of product success. |
| 6. Validation Strategy For Predictive Validity | Add one paragraph on tuning overfit protection and explain that tuning feedback is useful only if holdouts remain protected. | Predictive validation remains the formal north-star test. |
| 8. Project Plan, Decision Gates, And Resource Ask | Add a work package for tuning and regression feedback interfaces with schemas/templates as outputs. | Do not turn the work package into Phase 3 tuning validation. |
| 9. Risks, Objections, And Mitigations | Add an objection and mitigation for optimizer overfitting to benchmark dev tasks. | Keep tuning-loop improvement unproven. |
| 10. Expected Deliverables | Add product-facing tuning and regression artifacts to the deliverable list. | Deliverables are interfaces and reports, not established tuning outcomes. |
| 11. Appendices And Evidence Index | Add a concise future-extension note in Appendix C. | Multi-ACUT residual validity and formal tuning-loop validation remain later extensions. |

## Full-Rewrite Avoidance

No V3 section needs a full rewrite. The numerical evidence, citations, table
values, selected task IDs, split labels, source eligibility, and completed
experiment decisions should remain unchanged.

## Phase 2 Scope Decision

The 0519 Phase 2 plan for multi-ACUT residual predictive validity is valuable
scientific follow-up, but it should not become a main deliverable in V4. V4
may mention it only as a later extension, for example in Appendix C.

## Agent-Tuning Proof Boundary

The 0519 Phase 3 tuning-validation idea is useful product context, not a
current proof requirement. V4 should state that tuning/regression interfaces
are product-facing deliverables while evidence that Barcarolle improves tuning
outcomes remains a later validation target.
