# Proposal Report V5 Phase-Label Cleanup Decision

Stop label: `proposal_report_v5_phase_label_cleanup_complete`.

## Decision

The V5 reader-facing phase-label cleanup is complete.

Active proposal report:
`docs/research/barcarolle-proposal-report-v5.md`.

V5 supersedes V4 for proposal use. V4 remains the agent-tuning integration
source draft and traceability artifact.

## What Changed

V5 removes internal phase framing from the reader-facing proposal while
preserving V4's structure, evidence, claim boundary, paid-evaluation framing,
and agent-tuning application path.

The proposal now describes the existing support as preliminary evidence,
completed pilot work, current evidence, and traction rather than as an
internal phase report. The appendix now presents readable evidence labels to
proposal reviewers, while path-level audit references are preserved in the
internal evidence manifest.

Internal evidence manifest:
`experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md`.

## Boundary Status

| Item | Status |
| --- | --- |
| V5 supersedes V4 as active proposal report | `true` |
| Reader-facing phase labels removed from V5 | `true` |
| V4 agent-tuning integration preserved | `true` |
| Raw path traceability moved to internal manifest | `true` |
| Predictive validity established | `false` |
| Tuning-loop improvement established | `false` |
| Multi-ACUT residual predictive validity established | `false` |
| Paid ACUT cells in this cleanup run | `0` |
| Paid LLM calls in this cleanup run | `0` |
| External reviewer calls in this cleanup run | `0` |
| Public browsing in this cleanup run | `false` |
| Score tables changed | `false` |
| Selected task IDs or split labels changed | `false` |
| Source eligibility changed | `false` |
| Task statements or hidden-oracle material changed | `false` |

## Audit

Passed:

```text
rg -n "Phase 1|Phase 2|Phase 3|phase 1|phase 2|phase 3|M[0-9]|phase1|phase-1" docs/research/barcarolle-proposal-report-v5.md
rg -n "validated predictive benchmark compiler|established predictive validity|tuning validation established|improves agent tuning|multi-ACUT residual validity established" docs/research/barcarolle-proposal-report-v5.md
rg -n "/Users/chenmohan/Downloads" docs/research/barcarolle-proposal-report-v5.md
git diff --check
```

The text checks returned no matches. `git diff --check` passed.

Manual audit answers were all yes:

- A proposal reader can understand V5 without knowing the internal phase
  system.
- V5 preserves predictive validity as the north star.
- V5 preserves agent tuning as the product/application path.
- The evidence remains preliminary rather than overclaimed.
- The appendix supports the argument instead of exposing internal process.

## Remaining Work

Before an approval artifact can start, the user/coordinator should review and
accept or revise V5, then decide:

- approval artifact format;
- project staffing and duration assumptions;
- budget ceiling and approval path for gated ACUT evaluation;
- reviewer-facing deliverable owner categories.

Do not treat V5 as establishing predictive validity, proving tuning-loop
improvement, or authorizing ungated paid ACUT evaluation. It supports approval
to build and validate Barcarolle under the stated claim boundary, with agent
tuning as the practical application path.
