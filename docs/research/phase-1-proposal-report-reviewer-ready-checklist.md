# Barcarolle Proposal Report V5 Reviewer-Ready Checklist

Status: V5 reader-facing phase-label cleanup checklist, 2026-06-01.

Checked report:
`docs/research/barcarolle-proposal-report-v5.md`.

## Checklist

| Area | Status | Evidence |
| --- | --- | --- |
| Reader-facing proposal framing | pass | V5 asks reviewers to approve Barcarolle as a repo-specific benchmark-compiler project and no longer frames the proposal around internal phase labels. |
| Phase-label cleanup | pass | V5 title, status, headings, main body, claim boundary, and appendices have no matches for the runbook's phase-label audit pattern. |
| V4 structure and substance preservation | pass | V5 preserves V4's eleven-section proposal shape, project ask, evidence numbers, citations, and predictive-validity north star. |
| Agent-tuning product fit | pass | V5 preserves V4's configuration-selection, prompt/retrieval/skill/tool-policy tuning, runtime-budget, regression-monitoring, dev/eval/canary, and optimizer-readable output path. |
| Tuning proof boundary | pass | V5 treats tuning/regression interfaces as deliverables but does not claim that Barcarolle has already improved a tuning loop. |
| Predictive-validity boundary | pass | V5 states that predictive validity remains unproven and treats current evidence as traction, feasibility, and validation-path support. |
| Path-level traceability | pass | V5 uses readable evidence labels in the proposal appendix while preserving raw path traceability in `experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md`. |
| Paid-evaluation framing | pass | V5 frames budgeted ACUT evaluation as a gated project resource after releases, baselines, score joins, and success criteria are frozen. |
| Evidence accuracy | pass | V5 preserves the key numbers: weighted gaps `0.3148` and `0.7481`, simple baselines `0.25` and `0.125`, `120/120` cells, `30/30` click repairs, candidate MAE `0.209`, best simple aggregate baseline `0.2149`, edge `0.0059`, random beats/ties share `93.4%`, and fallback `6/18` overall with boltons `6/6`. |
| Artifact hygiene | pass | V5 references committed sanitized evidence, does not include raw prompts, raw completions, ACUT transcripts, workspaces, raw diffs, local planning-file paths, hidden verifier material, or new source/task/split artifacts, and keeps raw evidence paths out of the reader-facing report. |
| Approval packet status | pass | The combined approval packet now exists under `docs/research/m6-approval-packet/`, with PPTX deck, one-page summary, deck outline, evidence appendix, and packet checklist. |

## Audit Commands

Required V5 audit commands:

```text
rg -n "Phase 1|Phase 2|Phase 3|phase 1|phase 2|phase 3|M[0-9]|phase1|phase-1" docs/research/barcarolle-proposal-report-v5.md
rg -n "validated predictive benchmark compiler|established predictive validity|tuning validation established|improves agent tuning|multi-ACUT residual validity established" docs/research/barcarolle-proposal-report-v5.md
rg -n "/Users/chenmohan/Downloads" docs/research/barcarolle-proposal-report-v5.md
git diff --check
```

Recorded result: V5 text checks returned no matches during cleanup audit, and
`git diff --check` passed.

## Remaining Items

Remaining items are reviewer/coordinator decisions before sending the approval
packet:

- accept or revise `docs/research/barcarolle-proposal-report-v5.md`;
- review the completed approval packet under `docs/research/m6-approval-packet/`;
- set project duration and staffing assumptions;
- set the budget ceiling and approval path for gated ACUT evaluation;
- assign reviewer-facing deliverable owner categories.
