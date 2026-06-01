# Phase 1 P0 Placeholder And External Review Triage Decision

Decision label: `p0_placeholder_external_review_triage_complete`.

What happened: proposal report v1 P0/P1 placeholders, 0530 external-review
recommendations, and 0526-1 task-supply guidance were routed into milestone
categories without filling the placeholders.

Why it matters: remaining pre-proposal work now has an explicit priority map,
so M3 and M4 can stay narrow instead of absorbing every useful but noncritical
idea.

Action suggested next: write the next runbook only for the M3 proposal evidence
package, unless the user first chooses to prioritize M4 protocol hardening.

## Boundary

- Paid ACUT solver calls made: `0`.
- Paid LLM calls made: `0`.
- External reviewer calls made: `0`.
- Public citation browsing made: `false`.
- Predictive validity established: `false`.
- Paid validation authorized: `false`.
- Later runbook drafted: `false`.

## Triage Result

Every P0 placeholder from proposal report v1 Appendix D has exactly one route
in `docs/research/phase-1-proposal-p0-placeholder-triage.md`.

P0 route counts:

- `M3_evidence_package`: `4`.
- `M4_validation_or_candidate_hardening`: `8`.
- `M5_reviewer_ready_report_revision`: `2`.
- `needs_user_decision`: `3`.

P1 route counts:

- `M2_boundary_or_wording`: `1`.
- `M3_evidence_package`: `1`.
- `M5_reviewer_ready_report_revision`: `1`.
- `needs_user_decision`: `1`.

External review recommendations were classified as strategy input, not
controlling scope. Task-supply guidance was kept in the source-adapter/supply
layer; broad task-generator expansion was deferred or rejected as short-term
scope expansion.

## Next Work Category

The next work category is `M3_evidence_package`.

M3 should produce the proposal-critical no-paid evidence package:

- one-page preliminary evidence summary;
- many-seed random baseline distribution and candidate percentile;
- baseline-envelope comparison;
- coverage-objective ablation;
- fallback-share accounting;
- concise source-supply status;
- report evidence index.

M4 remains required before any paid-validation discussion: it owns candidate
pseudocode, release schema, fallback threshold, adapter estimand, invalid-cell
rules, joint success gate, support thresholds, and power/budget note.

## User Decisions

User decisions are not required before an M3 evidence-package runbook. They are
required before M6 approval artifact work and before any budget-bearing paid
validation discussion:

- no-paid staffing and duration;
- conditional paid-validation budget ceiling;
- reviewer-facing owner categories;
- approval artifact format.

## Verification

```text
python3 -m json.tool experiments/phase1_compiler/results/phase1_p0_placeholder_external_review_triage_preflight.json
  passed

python3 -m json.tool experiments/phase1_compiler/results/phase1_p0_placeholder_external_review_triage_decision.json
  passed

git diff --check
  passed
```
