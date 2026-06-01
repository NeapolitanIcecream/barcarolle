# Phase 1 Proposal Report Reviewer-Ready Checklist

Status: V4 agent-tuning integration checklist, 2026-06-01.

Checked report:
`docs/research/phase-1-proposal-report-v4.md`.

## Checklist

| Area | Status | Evidence |
| --- | --- | --- |
| Reader-facing problem and ask | pass | V4 asks reviewers to approve Barcarolle as a repo-specific benchmark-compiler project and states why target-repo prediction matters. |
| V3 structure and claim-boundary preservation | pass | V4 preserves the eleven-section proposal shape from V3 and keeps predictive validity as the north star rather than an established result. |
| Agent-tuning product fit | pass | V4 integrates configuration selection, prompt/retrieval/skill/tool-policy tuning, runtime-budget decisions, regression monitoring, dev/eval/canary feedback, and optimizer-readable outputs as the product/application path. |
| Tuning proof boundary | pass | V4 treats tuning/regression interfaces as deliverables but does not claim that Barcarolle has already improved a tuning loop. |
| Later-extension scope | pass | V4 does not promote multi-ACUT residual predictive validity or formal tuning-loop validation into the main project scope. |
| Paid-evaluation framing | pass | V4 frames budgeted ACUT evaluation as a gated project resource after releases, baselines, score joins, and success criteria are frozen. |
| Evidence accuracy | pass | V4 preserves the key numbers: weighted gaps `0.3148` and `0.7481`, simple baselines `0.25` and `0.125`, `120/120` cells, `30/30` click repairs, candidate MAE `0.209`, best simple aggregate baseline `0.2149`, edge `0.0059`, random beats/ties share `93.4%`, and fallback `6/18` overall with boltons `6/6`. |
| Back-half readability | pass | Validation, project plan, risks, deliverables, and appendices read as proposal sections rather than as a protocol packet or tuning-validation execution plan. |
| Citation coverage | pass | Related-work and benchmark-validity claims use the public citations recorded in `experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_citation_matrix.md`. |
| Artifact hygiene | pass | V4 references committed sanitized reports and does not introduce raw prompts, raw completions, ACUT transcripts, workspaces, raw diffs, local planning-file paths, hidden verifier material, or new source/task/split artifacts. |

## Audit Commands

Required V4 audit commands:

```text
rg -n "Phase 3|Phase 2|multi-ACUT residual|tuning validation established|improves agent tuning|proves tuning|validated predictive benchmark compiler|established predictive validity" docs/research/phase-1-proposal-report-v4.md
rg -n "/Users/chenmohan/Downloads" docs/research/phase-1-proposal-report-v4.md
git diff --check
```

Recorded result: V4 text checks returned no matches during the integration
audit, and `git diff --check` passed.

## Remaining Items

Remaining items are reviewer/coordinator decisions after V4 review:

- accept or revise `docs/research/phase-1-proposal-report-v4.md`;
- choose whether the approval artifact should be a report, short memo,
  presentation, executive summary, or combined packet;
- set project duration and staffing assumptions;
- set the budget ceiling and approval path for gated ACUT evaluation;
- assign reviewer-facing deliverable owner categories.
