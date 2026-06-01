# Phase 1 Proposal Report V3 Genre Repair Decision

Stop label: `proposal_report_v3_genre_repair_complete`.

## Decision

The V3 genre repair is complete.

Active proposal report:
`docs/research/phase-1-proposal-report-v3.md`.

V3 supersedes V2 for proposal use. V2 remains an evidence-safe source draft and
traceability artifact, but V3 is the report to review as the proposal-facing
document.

## What Changed

V3 repairs V2's proposal-genre regression while preserving V2's evidence and
claim safety.

The report now:

- preserves the V1 eleven-section proposal structure;
- asks for approval of Barcarolle as a repo-specific benchmark-compiler
  project;
- explains target-repository predictive validity as the north star;
- presents Phase 1 evidence as traction and feasibility, not as proof;
- frames budgeted ACUT evaluation as a gated project resource after protocols,
  baselines, score joins, and success criteria are frozen;
- moves detailed protocol machinery into appendices and supporting references.

## Boundary Status

| Item | Status |
| --- | --- |
| V3 supersedes V2 as active proposal report | `true` |
| V1 structure preserved | `true` |
| Predictive validity established | `false` |
| Paid ACUT cells in this repair run | `0` |
| Paid LLM calls in this repair run | `0` |
| External reviewer calls in this repair run | `0` |
| Public browsing in this repair run | `false` |
| Score tables changed | `false` |
| Selected task IDs or split labels changed | `false` |
| Task statements or hidden-oracle material changed | `false` |

## Paid Evaluation Framing

V3 does not describe the approved project as a project defined by avoiding
evaluation spend. It says budgeted ACUT evaluation may be needed after the
benchmark release, task-selection rule, baseline suite, score-join procedure,
and success criteria are frozen. This keeps the writing-run execution guardrail
separate from the proposal-facing resource plan.

## Internal Vocabulary Status

Required text checks found no flagged internal/process terms in
`docs/research/phase-1-proposal-report-v3.md`.

Appendices retain committed report paths and protocol artifact names only for
traceability. They do not require the reader to understand internal milestone
or execution vocabulary to follow the proposal argument.

## Checks

Passed:

```text
rg -n "\bM[0-9]\b|runbook|roadmap|P0|P1|placeholder|no-paid|paid remains unauthorized|does not authorize paid|M6|user-owned" docs/research/phase-1-proposal-report-v3.md
rg -n "validated predictive benchmark compiler|proves predictive validity|established predictive validity|model-only superiority" docs/research/phase-1-proposal-report-v3.md
rg -n "/Users/chenmohan/Downloads" docs/research/phase-1-proposal-report-v3.md
git diff --check
```

Failed: none.

## Remaining Work

Before an approval artifact can start, the user/coordinator should review and
accept or revise V3. After V3 is accepted, remaining decisions are:

- approval artifact format;
- project staffing and duration assumptions;
- budget ceiling and approval path for gated ACUT evaluation;
- reviewer-facing deliverable owner categories.

Do not treat V3 as establishing predictive validity. It supports approval to
build and validate Barcarolle under the stated claim boundary.
