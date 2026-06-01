# Phase 1 Proposal Report Reviewer-Ready Checklist

Status: V3 proposal-genre checklist, 2026-06-01.

Checked report:
`docs/research/phase-1-proposal-report-v3.md`.

## Checklist

| Area | Status | Evidence |
| --- | --- | --- |
| Reader-facing problem and ask | pass | V3 asks reviewers to approve Barcarolle as a repo-specific benchmark-compiler project and states why target-repo prediction matters. |
| V1 structure preservation | pass | V3 preserves the eleven-section proposal shape from V1: executive summary, problem, north star, boundary, design, validation, evidence, plan/resources, risks, deliverables, and appendices. |
| Internal vocabulary control | pass | The V3 main body avoids milestone/process vocabulary and does not require readers to know internal phase labels or execution artifacts. |
| Paid-evaluation framing | pass | V3 frames budgeted ACUT evaluation as a gated project resource after releases, baselines, score joins, and success criteria are frozen. |
| Evidence accuracy | pass | V3 preserves the key numbers: weighted gaps `0.3148` and `0.7481`, simple baselines `0.25` and `0.125`, `120/120` cells, `30/30` click repairs, candidate MAE `0.209`, best simple aggregate baseline `0.2149`, edge `0.0059`, random beats/ties share `93.4%`, and fallback `6/18` overall with boltons `6/6`. |
| Claim boundary | pass | V3 states that predictive validity is the north star and remains unproven; Phase 1 supplies traction evidence and a concrete validation path. |
| Back-half readability | pass | Validation, project plan, risks, deliverables, and appendices read as proposal sections rather than as a protocol packet. |
| Citation coverage | pass | Related-work and benchmark-validity claims use the public citations recorded in `experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_citation_matrix.md`. |
| Artifact hygiene | pass | V3 references committed sanitized reports and does not introduce raw prompts, raw completions, ACUT transcripts, workspaces, raw diffs, local planning-file paths, or hidden verifier material. |

## Audit Commands

Required V3 audit commands:

```text
rg -n "\bM[0-9]\b|runbook|roadmap|P0|P1|placeholder|no-paid|paid remains unauthorized|does not authorize paid|M6|user-owned" docs/research/phase-1-proposal-report-v3.md
rg -n "validated predictive benchmark compiler|proves predictive validity|established predictive validity|model-only superiority" docs/research/phase-1-proposal-report-v3.md
rg -n "/Users/chenmohan/Downloads" docs/research/phase-1-proposal-report-v3.md
git diff --check
```

Recorded result: all text checks returned no matches, and `git diff --check`
passed.

## Remaining Items

Remaining items are reviewer/coordinator decisions after V3 review:

- accept or revise `docs/research/phase-1-proposal-report-v3.md`;
- choose whether the approval artifact should be a report, short memo,
  presentation, executive summary, or combined packet;
- set project duration and staffing assumptions;
- set the budget ceiling and approval path for gated ACUT evaluation;
- assign reviewer-facing deliverable owner categories.
