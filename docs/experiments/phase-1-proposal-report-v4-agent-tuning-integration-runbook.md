# Phase 1 Proposal Report V4 Agent-Tuning Integration Runbook

Status: proposal-report targeted revision runbook, 2026-06-01.

## Goal

Revise the active proposal report from V3 to V4 by integrating the product
landing path around agent tuning, configuration selection, and regression
feedback.

The intended output is:

```text
docs/research/phase-1-proposal-report-v4.md
```

This is a targeted revision, not a full rewrite. V3 already has the right
report genre, claim boundary, and structure. V4 should preserve that structure
unless a small local section adjustment is clearly necessary.

Plain-language target:

```text
Keep predictive validity as the north star. Make clear why that north star
matters in practice: a repo-specific benchmark compiler becomes valuable when
it helps teams choose, tune, and regression-test agent configurations for their
own repositories.
```

## Revision Thesis

The user wants Phase 3's product value integrated into the proposal, but not as
a new short-term proof burden.

Use this framing:

```text
Agent tuning is the main product pull and application path.
Predictive validity remains the research north star.
The approved project should produce outputs that are useful for tuning and
regression feedback, but it does not need to prove full tuning-loop
improvement before project approval.
```

Do not make the report say:

```text
This project must complete Phase 3 tuning validation before it is successful.
Barcarolle has already shown that its benchmark improves agent tuning.
Tuning-loop validation replaces predictive-validity validation.
```

Preferred proposal wording:

```text
The same release machinery that supports predictive validation also supports
practical tuning workflows: dev/eval/canary splits, adapter-stratified
scorecards, failure taxonomies, regression reports, and optimizer-readable
feedback for prompts, retrieval, skills, tool policies, and runtime budgets.
These interfaces are product-facing deliverables, while formal evidence that
Barcarolle improves tuning outcomes remains a later validation target.
```

## Phase 2 Boundary

Phase 2, as originally described in the 0519 plan, is multi-ACUT residual
predictive validity: testing whether Barcarolle adds predictive signal beyond
general benchmark scores across multiple paired ACUT configurations.

It is valuable as a stronger scientific extension, but it should not become
the main body of this proposal. The proposal may mention it briefly as a later
extension, for example:

```text
A later extension can test whether Barcarolle adds predictive signal beyond
general benchmark scores across multiple paired ACUT configurations.
```

Do not turn V4 into a multi-ACUT residual-validity study plan. The current
proposal should stay focused on building and validating the repo-specific
benchmark compiler, with agent tuning as the practical application path.

## Boundary

This runbook is writing, synthesis, and handoff cleanup only.

Allowed:

- create `docs/research/phase-1-proposal-report-v4.md` from V3;
- preserve V3's evidence, citation, claim boundary, and section order;
- add or revise concise agent-tuning language in the main body;
- add a small product/application subsection only if it improves readability;
- update the reviewer-readiness checklist so it includes agent-tuning fit;
- update the roadmap and `PROCESS.md` to record that V4 is the active proposal
  report if the revision succeeds;
- add process and decision closeout artifacts.

Not allowed:

- paid ACUT solver calls;
- paid LLM calls;
- external reviewer calls;
- changing score tables, selected task IDs, split labels, source eligibility,
  task statements, hidden-oracle material, or completed experiment decisions;
- claiming predictive validity has been established;
- claiming agent tuning value has been empirically proven;
- turning the report into a Phase 2 or Phase 3 execution plan;
- drafting a slide deck, decision memo, or M6 approval artifact;
- setting final staffing, duration, or budget numbers without user input;
- deleting V1, V2, or V3.

Public browsing is not expected. If a citation must be corrected, use primary
public sources and record the reason in the process report.

## Required Inputs

Read first:

```text
AGENTS.md
PROCESS.md
docs/research/phase-1-proposal-report-v3.md
docs/research/phase-1-proposal-report-reviewer-ready-checklist.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
docs/research/phase-1-proposal-claim-boundary.md
docs/experiments/phase-1-proposal-report-v3-genre-repair-runbook.md
experiments/phase1_compiler/reports/phase1_proposal_report_v3_genre_repair_decision.md
```

Read the original product/tuning context from the 0519 plan:

```text
/Users/chenmohan/Downloads/barcarolle-research-0519.md
```

Relevant 0519 sections include:

- Phase 2: multi-ACUT residual predictive validity;
- Phase 3: agent tuning validation;
- product value for agent developers and repo owners;
- tuning interfaces for DSPy-style and SkVM-style optimizers;
- milestone 5: tuning integrations;
- risk: tuning overfits benchmark.

Use these only as source material. Do not cite local planning files as public
literature support in the proposal.

Use current evidence reports as needed, but do not add new evidence claims:

```text
experiments/phase1_compiler/reports/phase1_proposal_report_v3_genre_repair_decision.md
experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md
experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md
experiments/phase1_compiler/reports/phase1_proposal_evidence_package_fallback_share.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md
```

## Expected Outputs

Create:

```text
docs/research/phase-1-proposal-report-v4.md

experiments/phase1_compiler/reports/phase1_proposal_report_v4_agent_tuning_integration_process.md
experiments/phase1_compiler/reports/phase1_proposal_report_v4_agent_tuning_integration_decision.md
experiments/phase1_compiler/results/phase1_proposal_report_v4_agent_tuning_integration_decision.json
```

Update if V4 succeeds:

```text
docs/research/phase-1-proposal-report-reviewer-ready-checklist.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
PROCESS.md
```

Optional only if useful:

```text
experiments/phase1_compiler/reports/phase1_proposal_report_v4_agent_tuning_section_map.md
experiments/phase1_compiler/results/phase1_proposal_report_v4_agent_tuning_audit.json
```

Do not overwrite V3. V3 remains the genre-repaired baseline and source draft.

## V4 Report Contract

Preserve V3's eleven-section proposal shape:

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

The expected V4 change is emphasis, not architecture.

### Where To Integrate Agent Tuning

Use these insertion points by default:

1. **Executive Summary**
   Add one or two sentences explaining that the practical value of a
   predictive repo-specific benchmark is agent configuration selection,
   tuning, and regression monitoring. Do not make tuning validation a current
   result.

2. **Problem And Stakes**
   Expand the "evaluation, tuning, governance" paragraph with concrete reader
   questions:
   - Did a repo-docs retriever help this repo?
   - Did a test-running policy justify its cost?
   - Did a prompt, skill, or retrieval change improve future repo work rather
     than overfit the dev set?
   - Did a model or harness upgrade regress on critical task families?

3. **Barcarolle Thesis And Boundary**
   Clarify that Barcarolle can emit tuning feedback without owning the ACUT
   optimization loop. It supplies benchmark releases, splits, scorecards,
   failure labels, and regression signals; the ACUT or optimizer owns how to
   change prompts, skills, tools, retrieval, or budgets.

4. **Proposed Benchmark-Compiler Design**
   Expand the existing "Tuning and evaluation interfaces" layer. Mention
   dev/eval/canary splits, optimizer-readable scorecards, failure taxonomy,
   source-quality limits, cost/latency accounting, and regression labels.

5. **Validation Strategy**
   Add one paragraph explaining that tuning workflows need holdout and canary
   protection because optimizer loops can overfit benchmark dev tasks. Keep
   predictive validation as the formal north-star test.

6. **Project Plan**
   Add or revise one work package for "Tuning and regression feedback
   interfaces." The output should be schema/templates, not a claim that tuning
   improvement is already proven.

7. **Risks**
   Add or strengthen an objection about tuning overfitting the benchmark.
   Mitigation should use dev/eval/canary separation, frozen holdouts,
   source/task-family reporting, and refresh governance.

8. **Expected Deliverables**
   Add deliverables such as:
   - optimizer-readable scorecard schema;
   - dev/eval/canary split manager;
   - tuning/regression report template;
   - failure taxonomy for prompts, retrieval, tools, skills, public-test
     policy, and runtime budget;
   - canary/holdout rules for preventing overfitting.

9. **Appendices**
   Optionally add a short future-extension note:
   - Phase 2/multi-ACUT residual predictive validity is a later scientific
     strengthening path;
   - agent tuning validation is a later product-validation path.

### Style Rules

Use reader-facing language. Avoid making readers learn our phase labels.

Do not use `Phase 3` in the main body unless a brief appendix explicitly
explains historical roadmap terminology. Prefer:

```text
agent-tuning application path
tuning and regression feedback
optimizer-readable outputs
configuration-selection workflow
future tuning-loop validation
```

Do not overuse specific framework names. DSPy and SkVM may appear in an
appendix or as examples if already cited, but the main body should describe the
generic workflow: prompts, retrieval, skills, tools, public-test policy,
runtime budget, and harness settings.

## Worker Prompt

Use this prompt to start the execution worker:

```text
You are executing docs/experiments/phase-1-proposal-report-v4-agent-tuning-integration-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first.
Then read the runbook and follow it with step-level acceptance and scoped
commits.

Main goal: create docs/research/phase-1-proposal-report-v4.md by making a
targeted revision to V3. Preserve V3's report structure, evidence, citations,
and claim boundary. Integrate agent tuning as the product/application path:
configuration selection, prompt/retrieval/skill/tool-policy tuning, regression
monitoring, dev/eval/canary splits, optimizer-readable scorecards, and failure
taxonomy.

Do not rewrite the whole report. Do not turn V4 into a Phase 2 multi-ACUT
residual-validity study plan or a Phase 3 tuning-validation plan. Do not claim
predictive validity or tuning improvement has already been established.

Do not run paid ACUT cells, paid LLM calls, or external reviewer calls. Do not
change score tables, selected task IDs, split labels, source eligibility, task
statements, or completed decisions. Do not draft a deck or M6 approval packet.
```

## Step 0: Preflight And Intent Check

Actions:

1. Record branch, HEAD, date, worktree status, and input availability in the
   process report.
2. Read V3 and the 0519 Phase 2/Phase 3/product-value sections.
3. Record the revision intent:
   - V3 is structurally accepted;
   - V4 is a targeted application-path integration;
   - agent tuning is product pull, not current proof;
   - Phase 2 is a later scientific extension, not this proposal's main
     deliverable.

Acceptance:

- no paid/external calls made;
- process report records the distinction between Phase 2 and agent-tuning
  product path;
- no report text changed yet except process artifacts if needed.

Suggested commit:

```text
Record proposal v4 agent tuning preflight
```

## Step 1: Map Existing V3 Tuning Content

Actions:

1. Search V3 for tuning-related terms:

```bash
rg -n "tuning|optimizer|scorecard|failure|regression|canary|dev/eval|configuration" docs/research/phase-1-proposal-report-v3.md
```

2. Write a compact map of:
   - useful V3 tuning content to preserve;
   - places where one or two sentences are enough;
   - places where a bullet or deliverable should be added;
   - places where Phase 2 should stay absent or appendix-only.

Acceptance:

- the map shows V4 can be a targeted revision;
- no section is marked for full rewrite unless justified;
- no new evidence requirement is introduced.

Suggested commit:

```text
Map proposal v4 tuning integration points
```

## Step 2: Draft V4 From V3

Actions:

1. Copy V3 into `docs/research/phase-1-proposal-report-v4.md`.
2. Update title/status to V4.
3. Apply only targeted edits from the section map.
4. Preserve all numerical evidence and citations unless a local sentence needs
   rewording.

Acceptance:

- V4 exists;
- V4 preserves V3's section order;
- V4 does not read as a new report genre;
- predictive validity remains unproven.

Suggested commit:

```text
Draft proposal report v4 from v3
```

## Step 3: Strengthen Product Pull In The Opening And Stakes

Actions:

1. Add practical tuning value to the executive summary without increasing the
   current evidence claim.
2. Expand the stakes paragraph with concrete agent developer and repo owner
   questions.
3. Keep the central problem as target-repository prediction, not generic
   tuning tooling.

Acceptance:

- a reviewer can see why Barcarolle matters beyond evaluation reporting;
- the opening still asks for benchmark-compiler project approval;
- no claim says Barcarolle has already improved a tuning loop.

Suggested commit:

```text
Integrate tuning product pull in proposal opening
```

## Step 4: Integrate Tuning Interfaces Into Design And Deliverables

Actions:

1. Expand the existing "Tuning and evaluation interfaces" layer.
2. Add tuning/regression output expectations to deliverables:
   - optimizer-readable scorecard schema;
   - dev/eval/canary split manager;
   - configuration comparison templates;
   - regression and canary reports;
   - failure taxonomy tied to prompts, retrieval, skills, tools, test policy,
     and budget.
3. Clarify that Barcarolle provides these outputs but does not own the ACUT
   optimizer or harness internals.

Acceptance:

- design section explains what product-facing tuning artifacts Barcarolle
  emits;
- deliverables include tuning feedback artifacts;
- the ACUT boundary remains intact.

Suggested commit:

```text
Add proposal v4 tuning interface deliverables
```

## Step 5: Add Tuning-Overfit Guardrails

Actions:

1. Add or revise validation language explaining that tuning workflows must
   preserve dev/eval/canary or holdout separation.
2. Add a risk/objection about benchmark overfitting during agent tuning.
3. Mitigate with:
   - frozen evaluation releases;
   - canary or future holdout tasks;
   - source/task-family slice reporting;
   - refresh governance;
   - clear separation between tuning feedback and formal validation claims.

Acceptance:

- V4 makes tuning useful but not loose;
- readers can see how tuning value avoids undermining predictive validity;
- no tuning-loop result is invented.

Suggested commit:

```text
Add tuning overfit guardrails to proposal v4
```

## Step 6: Keep Phase 2 As A Future Extension

Actions:

1. Decide whether V4 needs a one-sentence appendix note about Phase 2.
2. If included, describe it without phase jargon in the main body:

```text
A later extension can test whether Barcarolle adds predictive signal beyond
general benchmark scores across multiple paired ACUT configurations.
```

3. Do not add multi-ACUT residual predictive validity to the project work
   packages unless the user explicitly changes the project scope.

Acceptance:

- Phase 2 is not a main deliverable;
- V4 does not imply multi-ACUT residual validation is required for this
  project approval;
- any future-extension note is short and scoped.

Suggested commit:

```text
Scope multi acut residual validation as future extension
```

## Step 7: Update Checklist And Handoff Documents

Actions:

1. Update `docs/research/phase-1-proposal-report-reviewer-ready-checklist.md`
   to check:
   - V4 preserves V3 structure and claim boundary;
   - agent tuning is integrated as product/application path;
   - tuning-loop improvement is not claimed as established;
   - Phase 2 is not promoted into the main project scope;
   - paid evaluation remains budgeted and gated;
   - artifact hygiene is unchanged.
2. Update the roadmap to say V4 supersedes V3 as the active proposal report if
   V4 passes audit.
3. Update `PROCESS.md` with the new active report and stop label if V4 passes.

Acceptance:

- handoff docs point to V4 when appropriate;
- M6 waits on V4 acceptance and user decisions;
- process notes stay concise.

Suggested commit:

```text
Align proposal v4 handoff documents
```

## Step 8: Audit

Run these checks:

```bash
rg -n "Phase 3|Phase 2|multi-ACUT residual|tuning validation established|improves agent tuning|proves tuning|validated predictive benchmark compiler|established predictive validity" docs/research/phase-1-proposal-report-v4.md
rg -n "/Users/chenmohan/Downloads" docs/research/phase-1-proposal-report-v4.md
git diff --check
```

Interpretation:

- `Phase 3` should not appear in the main body. If it appears in an appendix or
  local artifact title, explain why in the process report.
- `Phase 2` and `multi-ACUT residual` should be absent from the main body or
  appear only as a clearly deferred future extension.
- no prohibited validity or tuning-improvement claim should appear;
- no local planning path should appear in V4;
- `git diff --check` must pass.

Manual review questions:

```text
Does V4 make the product value clearer than V3?
Does it avoid turning the proposal into a Phase 3 tuning-validation plan?
Does it preserve predictive validity as the north star?
Does it make tuning outputs useful while keeping the ACUT boundary intact?
Does it avoid adding new evidence burdens before approval?
```

Acceptance:

- text checks pass or every acceptable match is explained;
- manual review answers are yes;
- `git diff --check` passes.

Suggested commit:

```text
Audit proposal report v4 tuning integration
```

## Step 9: Closeout

Actions:

1. Write:

```text
experiments/phase1_compiler/reports/phase1_proposal_report_v4_agent_tuning_integration_process.md
experiments/phase1_compiler/reports/phase1_proposal_report_v4_agent_tuning_integration_decision.md
experiments/phase1_compiler/results/phase1_proposal_report_v4_agent_tuning_integration_decision.json
```

2. Stop with one label:

```text
proposal_report_v4_agent_tuning_integration_complete
blocked_v4_turns_into_tuning_validation_plan
blocked_phase2_scope_unclear
blocked_claim_boundary_unclear
blocked_missing_core_inputs
```

Decision report must state:

- whether V4 supersedes V3 as the active proposal report;
- whether V3's structure and claim boundary were preserved;
- how agent tuning was integrated;
- whether tuning-loop improvement is still unproven;
- whether Phase 2 remains a future extension;
- what remains before M6 or another approval artifact can start.

Suggested commit:

```text
Close proposal report v4 tuning integration
```

## Final Report Expectations

The closeout should say, in plain terms:

```text
What changed:
  V4 clarifies the product/application value of Barcarolle for agent tuning,
  configuration comparison, and regression feedback while preserving V3's
  proposal structure.

Why it matters:
  the proposal now connects predictive validity to the practical reason teams
  would use Barcarolle: choosing and improving agent configurations for their
  own repositories.

What can happen next:
  the user/coordinator can review V4 as the proposal report. Only after V4 is
  accepted should the team decide whether to create a deck, decision memo, or
  other approval artifact.
```

Do not draft the next runbook unless the user explicitly asks after reviewing
V4.
