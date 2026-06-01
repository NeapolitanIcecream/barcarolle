# Proposal Report V5 Reader-Facing Phase-Label Cleanup Runbook

Status: targeted proposal cleanup runbook, 2026-06-01.

## Goal

Create a reader-facing V5 proposal report that removes the internal "Phase 1"
framing from the proposal itself.

The intended output is:

```text
docs/research/barcarolle-proposal-report-v5.md
```

This is a narrow cleanup. V4 already has the right structure, claim boundary,
agent-tuning application path, and paid-evaluation framing. V5 should preserve
V4's substance while replacing internal phase language with reader-facing
proposal language.

Plain-language target:

```text
Reviewers should see a project proposal for Barcarolle, not a report about an
internal Phase 1. The evidence should be described as preliminary or
pre-proposal evidence, not as "Phase 1 evidence." Phase 2 and Phase 3 should
also remain out of the reader-facing framing except as plain-language future
extensions if needed.
```

## Diagnosis To Fix

V4 successfully integrates agent tuning as the product/application path, but it
still exposes internal phase framing in the proposal:

- title: `Barcarolle Phase 1 Proposal Report V4`;
- status note: "It presents Phase 1 as traction evidence";
- executive summary: "Phase 1 supports that request";
- claim boundary: "Phase 1 supplies traction evidence";
- evidence section: "Phase 1 evidence matters";
- appendix claim boundary: "Phase 1 shows...";
- appendix evidence paths expose `phase1_...` filenames.

After considering both the long-term scientific extension and product
application path, these phase labels no longer help the proposal reader. They
create a false question: "What are Phase 2 and Phase 3, and why am I only
approving Phase 1?" The proposal should instead ask for project approval around
the north star and application path.

## Boundary

Allowed:

- create a new V5 report from V4;
- use a reader-facing filename without `phase-1`;
- replace reader-facing "Phase 1" language with "preliminary evidence",
  "pre-proposal work", "completed pilot evidence", or "current evidence";
- keep V4's agent-tuning integration, project ask, evidence numbers, citations,
  and claim boundary;
- simplify the appendix evidence index so raw internal `phase1_...` paths do
  not dominate the reader-facing proposal;
- create a companion internal evidence manifest if raw paths are needed for
  auditability;
- update the checklist, roadmap, and `PROCESS.md` so V5 becomes the active
  proposal report if the cleanup passes;
- add process and decision closeout artifacts.

Not allowed:

- paid ACUT solver calls;
- paid LLM calls;
- external reviewer calls;
- changing score tables, selected task IDs, split labels, source eligibility,
  task statements, hidden-oracle material, or completed experiment decisions;
- weakening the claim boundary;
- claiming predictive validity, multi-ACUT residual validity, or tuning-loop
  improvement has been established;
- rewriting the report's argument or project plan beyond phase-label cleanup;
- drafting a deck, decision memo, or M6 approval artifact;
- deleting V1, V2, V3, or V4.

Public browsing is not expected.

## Required Inputs

Read first:

```text
AGENTS.md
PROCESS.md
docs/research/phase-1-proposal-report-v4.md
docs/research/phase-1-proposal-report-reviewer-ready-checklist.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
experiments/phase1_compiler/reports/phase1_proposal_report_v4_agent_tuning_integration_decision.md
```

Use V4 as the source draft. Do not return to earlier drafts unless a V4
sentence is ambiguous.

## Expected Outputs

Create:

```text
docs/research/barcarolle-proposal-report-v5.md

experiments/phase1_compiler/reports/proposal_report_v5_phase_label_cleanup_process.md
experiments/phase1_compiler/reports/proposal_report_v5_phase_label_cleanup_decision.md
experiments/phase1_compiler/results/proposal_report_v5_phase_label_cleanup_decision.json
```

Optional, if raw path traceability is moved out of the proposal:

```text
experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md
```

Update if V5 succeeds:

```text
docs/research/phase-1-proposal-report-reviewer-ready-checklist.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
PROCESS.md
```

Do not overwrite V4. V4 remains the agent-tuning integration source draft.

## V5 Report Contract

V5 should preserve V4's section structure:

```text
1. Executive Summary
2. Problem And Stakes
3. Research Question And North Star
4. Barcarolle Thesis And Boundary
5. Proposed Benchmark-Compiler Design
6. Validation Strategy For Predictive Validity
7. Preliminary Evidence And Feasibility
8. Project Plan, Decision Gates, And Resource Ask
9. Risks, Objections, And Mitigations
10. Expected Deliverables
11. Appendices And Evidence Index
```

V5 may rename the document title to:

```text
Barcarolle Proposal Report V5
```

or:

```text
Barcarolle Project Proposal V5
```

Do not use `Phase 1`, `Phase 2`, `Phase 3`, `M1`, `M2`, `M3`, `M4`, `M5`, or
`M6` in reader-facing title, status, headings, main body, or claim boundary.

### Reader-Facing Replacement Rules

Use these replacements:

| Internal phrase | Reader-facing phrase |
| --- | --- |
| Phase 1 evidence | preliminary evidence |
| Phase 1 supports this request | current evidence supports this request |
| Phase 1 shows | completed pilot work shows |
| Phase 1 supplies traction evidence | current evidence supplies traction and a validation path |
| Phase 2 | later multi-configuration scientific extension |
| Phase 3 | later tuning-loop product validation |
| M6 approval artifact | approval artifact |

In the proposal body, prefer:

```text
preliminary evidence
pre-proposal work
completed pilot evidence
current evidence
later scientific extension
later product-validation extension
```

### Evidence Index Rule

The reader-facing proposal should not look like a path manifest. If the current
appendix evidence table contains raw internal paths such as
`experiments/phase1_compiler/...`, replace the first column with readable
evidence labels:

```text
Weighted design pilot
Local algorithm bakeoff
Three-repo workspace execution pilot
Click source-context repair
Adapter fairness diagnostics
Random-baseline comparison
Baseline-envelope comparison
Fallback-share accounting
Validation-protocol hardening
```

If path-level traceability is still needed, move raw paths into the optional
internal evidence manifest and link it from the process report, not from the
proposal body. If a short appendix note is needed, keep it neutral:

```text
Path-level audit references are maintained in the internal evidence manifest.
```

Do not remove evidence traceability from the repository; just avoid making it
the reader-facing proposal's dominant form.

## Worker Prompt

Use this prompt to start the execution worker:

```text
You are executing docs/experiments/proposal-report-v5-reader-facing-phase-label-cleanup-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first.
Then read the runbook and follow it with step-level acceptance and scoped
commits.

Main goal: create docs/research/barcarolle-proposal-report-v5.md from
docs/research/phase-1-proposal-report-v4.md by removing reader-facing internal
phase labels. Preserve V4's structure, agent-tuning product path, evidence
numbers, citations, claim boundary, and paid-evaluation framing.

Do not rewrite the whole report. Do not run paid ACUT cells, paid LLM calls, or
external reviewer calls. Do not change score tables, selected task IDs, split
labels, source eligibility, task statements, or completed decisions. Do not
claim predictive validity, tuning-loop improvement, or multi-ACUT residual
validity has been established. Do not draft a deck or M6 approval packet.
```

## Step 0: Preflight And Reader Contract

Actions:

1. Record branch, HEAD, date, worktree status, and input availability in the
   process report.
2. Read V4 and search for phase labels:

```bash
rg -n "Phase 1|Phase 2|Phase 3|phase 1|phase 2|phase 3|M[0-9]|phase1|phase-1" docs/research/phase-1-proposal-report-v4.md
```

3. Record the reader contract:
   - V5 is the reader-facing proposal report;
   - phase labels are internal coordination vocabulary;
   - current evidence remains traction-only;
   - agent tuning remains application path, not proven outcome.

Acceptance:

- no paid/external calls made;
- process report lists V4 phase-label locations;
- no proposal text changed yet except process artifacts if needed.

Suggested commit:

```text
Record proposal v5 phase-label cleanup preflight
```

## Step 1: Create V5 And Remove Main-Body Phase Labels

Actions:

1. Copy V4 to `docs/research/barcarolle-proposal-report-v5.md`.
2. Rename the report title and status to remove `Phase 1`.
3. Replace every main-body "Phase 1" claim with reader-facing language.
4. Remove "Phase 2" and "Phase 3" from the main body if present.
5. Preserve all numbers and evidence limits.

Acceptance:

- V5 exists at the neutral report path;
- title/status/headings/main body contain no phase labels;
- current evidence remains traction-only;
- predictive validity remains unproven.

Suggested commit:

```text
Draft reader-facing proposal report v5
```

## Step 2: Clean The Claim Boundary And Evidence Appendix

Actions:

1. Rewrite Appendix A so it does not say "Phase 1 shows".
2. Replace the evidence index's raw path-first presentation with readable
   evidence labels.
3. Create `proposal_report_v5_evidence_manifest.md` if needed to preserve
   raw path traceability.
4. Keep the proposal appendix concise and reader-facing.

Acceptance:

- Appendix A has no phase labels;
- evidence index is readable to a proposal reviewer;
- raw internal paths are preserved somewhere if removed from the proposal;
- no evidence claim is strengthened.

Suggested commit:

```text
Clean proposal v5 evidence appendix
```

## Step 3: Update Checklist And Handoff Documents

Actions:

1. Update the reviewer-ready checklist to check:
   - V5 is reader-facing and phase-label-free;
   - V4's agent-tuning integration is preserved;
   - predictive validity and tuning-loop improvement remain unproven;
   - path-level traceability is preserved outside the proposal if moved;
   - paid evaluation remains budgeted and gated.
2. Update the roadmap to say V5 supersedes V4 as the active proposal report if
   V5 passes audit.
3. Update `PROCESS.md` with the new active report and stop label if V5 passes.

Acceptance:

- handoff docs point to V5 when appropriate;
- roadmap can keep internal phase/milestone terms because it is an internal
  planning file;
- M6 waits on V5 acceptance and user decisions.

Suggested commit:

```text
Align proposal v5 handoff documents
```

## Step 4: Audit

Run:

```bash
rg -n "Phase 1|Phase 2|Phase 3|phase 1|phase 2|phase 3|M[0-9]|phase1|phase-1" docs/research/barcarolle-proposal-report-v5.md
rg -n "validated predictive benchmark compiler|established predictive validity|tuning validation established|improves agent tuning|multi-ACUT residual validity established" docs/research/barcarolle-proposal-report-v5.md
rg -n "/Users/chenmohan/Downloads" docs/research/barcarolle-proposal-report-v5.md
git diff --check
```

Expected:

- no phase-label matches in V5;
- no prohibited claim matches;
- no local planning path matches;
- `git diff --check` passes.

If the only phase-label matches are unavoidable internal artifact titles, move
them out of V5 and into the internal evidence manifest unless there is a
compelling reason not to.

Manual review questions:

```text
Can a proposal reader understand the document without knowing our phase system?
Does V5 still preserve the predictive-validity north star?
Does V5 still preserve agent tuning as the product/application path?
Does the evidence remain preliminary rather than overclaimed?
Does the appendix support the argument instead of exposing internal process?
```

Acceptance:

- text checks pass;
- manual review answers are yes;
- `git diff --check` passes.

Suggested commit:

```text
Audit proposal report v5 phase-label cleanup
```

## Step 5: Closeout

Actions:

1. Write:

```text
experiments/phase1_compiler/reports/proposal_report_v5_phase_label_cleanup_process.md
experiments/phase1_compiler/reports/proposal_report_v5_phase_label_cleanup_decision.md
experiments/phase1_compiler/results/proposal_report_v5_phase_label_cleanup_decision.json
```

2. Stop with one label:

```text
proposal_report_v5_phase_label_cleanup_complete
blocked_v5_phase_labels_remain_in_reader_report
blocked_claim_boundary_unclear
blocked_traceability_policy_unclear
blocked_missing_core_inputs
```

Decision report must state:

- whether V5 supersedes V4 as the active proposal report;
- whether reader-facing phase labels were removed;
- whether V4's agent-tuning integration was preserved;
- whether raw path traceability was moved to an internal manifest;
- whether predictive validity and tuning-loop improvement remain unproven;
- what remains before the approval artifact can start.

Suggested commit:

```text
Close proposal report v5 phase-label cleanup
```

## Final Report Expectations

The closeout should say:

```text
What changed:
  V5 removes internal phase framing from the reader-facing proposal while
  preserving V4's argument, evidence, and agent-tuning application path.

Why it matters:
  reviewers now see a coherent project proposal instead of a report about an
  internal Phase 1.

What can happen next:
  after the user accepts V5, decide the approval artifact format, staffing and
  duration assumptions, evaluation budget path, and deliverable owner
  categories.
```

Do not draft the next runbook unless the user explicitly asks after reviewing
V5.
