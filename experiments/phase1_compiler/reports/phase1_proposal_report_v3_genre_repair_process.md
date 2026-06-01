# Phase 1 Proposal Report V3 Genre Repair Process

Status: in progress, 2026-06-01.

This process report records execution evidence for
`docs/experiments/phase-1-proposal-report-v3-genre-repair-runbook.md`.

## Step 0: Preflight And Regression Diagnosis

Branch: `codex/restart-benchmark-compiler`.

HEAD at preflight:
`ac8531297b3fc59477deb8ea483f1bf6631373b7`.

Date: `2026-06-01`.

Starting worktree status:

```text
## codex/restart-benchmark-compiler...origin/codex/restart-benchmark-compiler
 M PROCESS.md
 M docs/research/phase-1-proposal-roadmap-and-claim-planning.md
?? docs/experiments/phase-1-proposal-report-v3-genre-repair-runbook.md
```

The preexisting `PROCESS.md` and roadmap edits already describe the user review
that found V2 evidence-safe but proposal-genre regressed. The untracked runbook
is the execution input for this run. These starting changes are treated as
user/coordinator context and are not reverted.

Input availability: all required repository inputs, support artifacts, and
local planning/review files named by the runbook were present at preflight.
Local planning files were checked for availability only; they should not be
cited as public literature support in V3.

Paid/external-call boundary:

- Paid ACUT solver cells run in this step: `0`.
- Paid LLM calls run in this step: `0`.
- External reviewer calls run in this step: `0`.
- Public browsing used in this step: `false`.
- Score tables, selected task IDs, split labels, source eligibility, task
  statements, and completed experiment decisions changed: `false`.

V2 genre regression diagnosis:

- Internal milestone/process vocabulary appears in reader-facing argument
  positions. Examples include `M3`, `M4`, `M5`, `M6`, `P0`, `no-paid`,
  `user-owned`, and report/process artifact references in the executive
  summary, validation section, risks, proposed next phase, deliverables, and
  appendix.
- The opening frames the requested decision as approval of a "no-paid research
  phase" and repeatedly says paid validation is not authorized. That is a
  correct execution guardrail for the writing work, but it makes the proposal
  sound as if the approved project itself is defined by not spending evaluation
  budget.
- The phrase "next phase" points to remaining pre-proposal/M6 packaging work in
  several places rather than to the project work that would begin after
  approval.
- Technical due-diligence detail dominates the back half. Study-mode tables,
  adapter-estimand wording, fallback caps, release-schema fields, support
  thresholds, and user decision tables should be translated into a readable
  validation plan, resource plan, risks, and appendices.
- Terminology is introduced before a proposal reader has a reason to care about
  it. V3 should name detailed policy objects only where they clarify evidence
  or traceability.

V3 execution decision:

- Use `docs/research/phase-1-proposal-report-v1.md` as the structural
  reference and preserve its eleven-section proposal shape.
- Use `docs/research/phase-1-proposal-report-v2.md` as the evidence, citation,
  figure, and conservative claim-boundary source.
- Reframe paid ACUT evaluation as a normal budgeted project activity that may
  occur only after candidate policies, validation protocols, baselines, and
  success criteria are frozen.
- Preserve the central claim boundary: predictive validity is the north star;
  Phase 1 does not establish it; Phase 1 supplies traction evidence and a
  concrete path for testing it.
