# Phase 1 Proposal Report V4 Agent-Tuning Integration Decision

Stop label: `proposal_report_v4_agent_tuning_integration_complete`.

## Decision

The V4 agent-tuning integration is complete.

Active proposal report:
`docs/research/phase-1-proposal-report-v4.md`.

V4 supersedes V3 for proposal use. V3 remains the genre-repaired baseline and
source draft, but V4 is the report to review as the active proposal-facing
document.

## What Changed

V4 preserves V3's proposal structure, evidence, citations, and claim boundary
while clarifying the product/application value of Barcarolle.

The report now explains that a repo-specific predictive benchmark becomes
practically useful when it helps teams:

- compare agent configurations;
- tune prompts, retrieval, skills, tools, public-test policy, and runtime
  budgets;
- monitor regressions on critical repository task families;
- consume dev/eval/canary splits, optimizer-readable scorecards, failure
  labels, configuration-comparison templates, and tuning/regression reports.

## Boundary Status

| Item | Status |
| --- | --- |
| V4 supersedes V3 as active proposal report | `true` |
| V3 eleven-section structure preserved | `true` |
| Predictive validity established | `false` |
| Tuning-loop improvement established | `false` |
| Agent tuning integrated as product/application path | `true` |
| Later residual predictive-validity extension promoted into main scope | `false` |
| Formal tuning-loop validation promoted into main scope | `false` |
| Paid ACUT cells in this repair run | `0` |
| Paid LLM calls in this repair run | `0` |
| External reviewer calls in this repair run | `0` |
| Public browsing in this repair run | `false` |
| Score tables changed | `false` |
| Selected task IDs or split labels changed | `false` |
| Source eligibility changed | `false` |
| Task statements or hidden-oracle material changed | `false` |

## Phase 2 And Tuning Scope

The 0519 plan's multi-configuration residual predictive-validity idea remains a
later scientific extension. V4 mentions the idea only as a deferred extension
and does not make it a project-approval deliverable.

The 0519 plan's agent-tuning validation idea remains a later product-validation
target. V4 makes tuning and regression interfaces product-facing deliverables,
but it does not claim that Barcarolle has already improved tuning outcomes.

## Audit

Passed:

```text
rg -n "Phase 3|Phase 2|multi-ACUT residual|tuning validation established|improves agent tuning|proves tuning|validated predictive benchmark compiler|established predictive validity" docs/research/phase-1-proposal-report-v4.md
rg -n "/Users/chenmohan/Downloads" docs/research/phase-1-proposal-report-v4.md
git diff --check
```

The prohibited-scope and local-path checks returned no matches. `git diff
--check` passed.

Manual audit answers were all yes:

- V4 makes the product value clearer than V3.
- V4 avoids turning the proposal into a tuning-validation plan.
- V4 preserves predictive validity as the north star.
- V4 makes tuning outputs useful while keeping the ACUT boundary intact.
- V4 avoids adding new evidence burdens before approval.

## Remaining Work

Before an approval artifact can start, the user/coordinator should review and
accept or revise V4. After V4 is accepted, remaining decisions are:

- approval artifact format;
- project staffing and duration assumptions;
- budget ceiling and approval path for gated ACUT evaluation;
- reviewer-facing deliverable owner categories.

Do not treat V4 as establishing predictive validity or proving tuning-loop
improvement. It supports approval to build and validate Barcarolle under the
stated claim boundary, with agent tuning as the practical application path.
