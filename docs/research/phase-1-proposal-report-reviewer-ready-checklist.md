# Phase 1 Proposal Report Reviewer-Ready Checklist

Status: M5 reviewer-readiness checklist, 2026-06-01.

Checked report:
`docs/research/phase-1-proposal-report-v2.md`.

## Checklist

| Area | Status | Evidence |
| --- | --- | --- |
| Claim boundary | pass | V2 states that predictive validity is the north star, current evidence is traction plus a credible validation path, and paid validation remains unauthorized. |
| Evidence support | pass | M3 evidence is tied to canonical reports: candidate MAE `0.209`, best simple aggregate baseline MAE `0.2149`, `0.0059` edge, and `93.4%` random beats/ties share. |
| Citation coverage | pass | Related-work and benchmark-validity claims use public citations recorded in `experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_citation_matrix.md`. |
| Related-work distinction | pass | SWE-bench, SWE-bench Verified, SWE-bench-Live, SWE-smith, and R2E-Gym are described as benchmark, quality, live-maintenance, task-generation, or agent-environment references rather than Barcarolle replacements. |
| M3 integration | pass | V2 separates random-baseline traction from the small best-simple-baseline edge and includes fallback and adapter caveats. |
| M4 validation-path integration | pass | V2 includes study modes, per-named-ACUT estimand, mandatory baselines, fallback caps, support thresholds, joint gate, release schema pointer, and no-paid power/budget boundary. |
| Prohibited claims | pass | V2 does not use the prohibited current-claim phrases checked by the runbook grep command. |
| Remaining user decisions | pass | Staffing, duration, owner categories, approval format, budget ceiling, and paid authorization are isolated as user-owned decision points. |
| Artifact hygiene | pass | V2 and M5 artifacts reference sanitized report paths and do not introduce raw prompts, raw completions, ACUT transcripts, workspaces, raw diffs, or hidden verifier material. |
| Paid/no-paid boundary | pass | M5 records zero paid ACUT cells, zero paid LLM calls, and zero external reviewer calls; public browsing was limited to citation verification. |
| Readability and structure | pass | V2 uses the expected report shape, moves detailed evidence into appendices, and no longer reads as a placeholder register or process log. |

## Audit Commands

Required M5 audit commands:

```text
rg -n "\[NEEDS" docs/research/phase-1-proposal-report-v2.md
rg -n "validated predictive benchmark compiler|proves predictive validity|established predictive validity|paid validation authorized|model-only superiority" docs/research/phase-1-proposal-report-v2.md
rg -n "/Users/chenmohan/Downloads" docs/research/phase-1-proposal-report-v2.md
```

Recorded result: all three commands returned no matches.

## Remaining Items

The remaining items are user decisions for M6 or later budget-bearing
discussion, not unresolved evidence placeholders:

- M6 approval artifact format.
- No-paid staffing and duration.
- Reviewer-facing deliverable owner categories.
- Conditional paid-validation budget ceiling.
- Any future paid-validation authorization.
