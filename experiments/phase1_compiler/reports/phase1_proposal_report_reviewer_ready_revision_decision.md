# Phase 1 Proposal Report Reviewer-Ready Revision Decision

Stop label: `proposal_report_reviewer_ready_for_technical_review`.

## Decision

M5 reviewer-ready proposal revision is complete.

Active reviewer-facing technical proposal report:
`docs/research/phase-1-proposal-report-v2.md`.

V2 is ready for technical proposal review under the bounded Phase 1 claim:
Barcarolle has traction evidence and a credible validation path for
repo-specific benchmark compilation. It does not claim predictive validity, and
it does not authorize paid validation.

## Boundary Status

| Item | Status |
| --- | --- |
| Predictive validity established | `false` |
| Paid validation authorized | `false` |
| Paid ACUT cells in M5 | `0` |
| Paid LLM calls in M5 | `0` |
| External reviewer calls in M5 | `0` |
| Public citation browsing | `related_work_only` |
| Score tables changed | `false` |
| Selected task IDs or split labels changed | `false` |

## Outputs

- `docs/research/phase-1-proposal-report-v2.md`
- `docs/research/phase-1-proposal-report-reviewer-ready-checklist.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_process.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_citation_matrix.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_risk_register.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_decision.md`
- `experiments/phase1_compiler/results/phase1_proposal_report_reviewer_ready_revision_decision.json`

## Citations Added

- `SWE-bench-2024`
- `SWE-bench-Verified-2024`
- `SWE-bench-Verified-2026`
- `SWE-bench-Live-2025`
- `SWE-smith-2025`
- `R2E-Gym-2025`
- `Validity-Challenges-2022`

Citation details are recorded in
`experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_citation_matrix.md`.

## Placeholder Status

V2 has no unresolved `[NEEDS ...]` markers. Remaining open items are user
decisions for M6 or later budget-bearing discussion:

- M6 approval artifact format.
- No-paid staffing and duration.
- Reviewer-facing deliverable owner categories.
- Conditional paid-validation budget ceiling.
- Any future paid-validation authorization.

## M6 Status

M6 can proceed only after the user or coordinator chooses the approval artifact
format and resolves the user-owned resource and owner-category decisions. M5
does not draft the M6 runbook and does not set budget, staffing, duration, or
owner categories.

## Checks

Passed:

```text
rg -n "\[NEEDS" docs/research/phase-1-proposal-report-v2.md
rg -n "validated predictive benchmark compiler|proves predictive validity|established predictive validity|paid validation authorized|model-only superiority" docs/research/phase-1-proposal-report-v2.md
rg -n "/Users/chenmohan/Downloads" docs/research/phase-1-proposal-report-v2.md
python3 -m json.tool experiments/phase1_compiler/results/phase1_proposal_report_reviewer_ready_revision_decision.json
git diff --check
```

Failed: none.
