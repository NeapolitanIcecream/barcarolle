# Phase 1 Proposal Report V3 Genre Repair Runbook

Status: proposal-report genre-repair runbook, 2026-06-01.

## Goal

Rewrite the active proposal report so it reads like the final project proposal,
not like an internal milestone summary, runbook closeout, or budget-safety
memo.

The intended output is:

```text
docs/research/phase-1-proposal-report-v3.md
```

V3 should preserve the M1 final-shape structure unless there is a clear
reader-facing reason to change it. Use V2 as a source of evidence, citations,
figures, and claim-boundary material, but do not preserve V2's organization
where it exposes internal milestones or process controls.

Plain-language target:

```text
Write the proposal as the document that would be handed to project approvers at
the end of pre-proposal work. It should say why Barcarolle is worth doing, what
the approved project will do, what preliminary evidence supports the bet, how
success will be tested, what resources are needed, and what claims remain out
of scope.
```

## Diagnosis To Fix

V2 improved evidence safety but regressed as a proposal report. It contains
several classes of reader-facing problems:

- internal milestone leakage: `M3`, `M4`, `M6`, `P0`, roadmap, runbook, and
  closeout vocabulary appear in the proposal argument;
- execution-boundary leakage: no-paid and paid-authorization safeguards that
  belong in runbooks and `PROCESS.md` appear as if they were project premises;
- phase confusion: "next phase" sometimes means remaining pre-proposal or M6
  packaging work, not the project work that starts after approval;
- technical overloading: validation gates, fallback caps, release schema fields,
  adapter estimands, and support thresholds dominate the main body instead of
  supporting a readable validation plan;
- terminology drift: locally coined labels are used before the reader has a
  reason to care about them;
- back-half readability decay: later sections read like a technical due
  diligence packet rather than a coherent proposal.

The repair should keep V2's conservative claim boundary:

```text
Predictive validity is the north star.
Phase 1 does not prove predictive validity.
Phase 1 supplies traction evidence and a concrete path toward testing it.
```

The repair should not keep V2's mistaken framing that the proposed project is a
no-paid project. The internal rule is:

```text
Do not trigger paid evaluations during this writing runbook.
```

The proposal-facing rule is:

```text
The approved project may require budgeted ACUT evaluation after candidate
policies, validation protocols, baselines, and success criteria are frozen.
```

## Boundary

This runbook is writing, synthesis, and artifact cleanup. It must not run ACUT
solver cells or change completed experimental outcomes.

Allowed:

- revise the proposal report into V3;
- reuse V1's section shape and V2's resolved evidence, citations, and figures;
- move technical details from the main body into appendices or supporting
  protocol references;
- revise the reviewer-readiness checklist so it checks reader fit, genre, and
  argument quality, not only prohibited claims;
- update the roadmap and `PROCESS.md` only to record that V2 needs genre repair
  and that V3 becomes the active proposal report if the repair succeeds;
- add closeout process and decision artifacts.

Not allowed:

- paid ACUT solver calls;
- paid LLM calls;
- external reviewer calls;
- changing score tables, selected task IDs, split labels, hidden-oracle
  material, task statements, or completed experiment decisions;
- inventing future results or pretending predictive validity has been shown;
- turning the report into a slide deck, decision memo, or M6 approval packet;
- setting final staffing, duration, or budget numbers without user input;
- deleting V1 or V2.

Public browsing is not expected. If a citation must be corrected, use primary
public sources and record the reason in the process report.

## Required Inputs

Read first:

```text
AGENTS.md
PROCESS.md
docs/research/phase-1-proposal-report-v1.md
docs/research/phase-1-proposal-report-v2.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
docs/research/phase-1-proposal-claim-boundary.md
docs/research/phase-1-proposal-evidence-package.md
docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md
docs/research/phase-1-proposal-report-reviewer-ready-checklist.md
docs/experiments/phase-1-proposal-report-final-shape-rewrite-runbook.md
docs/experiments/phase-1-proposal-report-reviewer-ready-revision-runbook.md
```

Use these evidence and support artifacts as needed:

```text
experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_citation_matrix.md
experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_risk_register.md
experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_decision.md
experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md
experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md
experiments/phase1_compiler/reports/phase1_proposal_evidence_package_fallback_share.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_claim_modes.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_candidate_policy.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_adapter_estimand.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_success_gate.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_support_thresholds.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_release_schema.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_power_budget_note.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md
```

Use local planning and review inputs only to preserve intent:

```text
/Users/chenmohan/Downloads/barcarolle-research-0519.md
/Users/chenmohan/Downloads/barcarolle-research-0526.md
/Users/chenmohan/Downloads/barcarolle-research-0526-1.md
/Users/chenmohan/Downloads/barcarolle-research-0530.md
```

Do not cite local planning files as public literature support in the proposal.

## Expected Outputs

Create:

```text
docs/research/phase-1-proposal-report-v3.md

experiments/phase1_compiler/reports/phase1_proposal_report_v3_genre_repair_process.md
experiments/phase1_compiler/reports/phase1_proposal_report_v3_genre_repair_decision.md
experiments/phase1_compiler/results/phase1_proposal_report_v3_genre_repair_decision.json
```

Update if the repair succeeds:

```text
docs/research/phase-1-proposal-report-reviewer-ready-checklist.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
PROCESS.md
```

Optional only if needed:

```text
experiments/phase1_compiler/reports/phase1_proposal_report_v3_genre_repair_section_map.md
experiments/phase1_compiler/results/phase1_proposal_report_v3_genre_repair_audit.json
```

Do not overwrite V1 or V2. V1 remains the final-shape structural reference.
V2 remains the evidence-safe but genre-regressed source draft.

## V3 Report Contract

Default to the M1/V1 section structure:

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

Change this structure only if the process report explains the reader-facing
reason. Do not change it merely because V2 used a different outline.

### Reader Contract

Target readers:

- project/proposal reviewers deciding whether Barcarolle should be approved or
  funded;
- coding-agent evaluation researchers who are skeptical of benchmark
  overclaiming;
- engineering leaders who need to understand what they would receive from the
  project.

The report must answer:

- What decision is being requested?
- Why is repo-specific predictive validity important?
- Why is Barcarolle a benchmark compiler rather than a task generator, ACUT
  harness, or leaderboard?
- What preliminary evidence shows the project is worth pursuing?
- What will the approved project do?
- How will predictive validity eventually be tested?
- What budgeted evaluation and other resources may be needed?
- What claims are explicitly not being made yet?

### Main-Body Style Rules

The main body should use reader-facing language.

Avoid these terms in the proposal main body unless there is a compelling reason
and a plain-English explanation:

```text
M1
M2
M3
M4
M5
M6
runbook
roadmap
P0
P1
placeholder
no-paid
paid remains unauthorized
does not authorize paid validation
user-owned
candidate policy hardening
adapter estimand
fallback governance
baseline registry
release schema
joint success gate
```

Acceptable replacements:

```text
recent retrospective analysis
preliminary evidence
planned validation protocol
budgeted ACUT evaluation
future-work validation
named ACUT configuration
task-selection rule
fallback-labeled selection
mandatory baselines
success criteria
release manifest
```

Internal terms may appear in appendices or evidence indexes when they are file
names, artifact titles, or necessary traceability labels.

### Paid Evaluation Reframing

Do not describe the project as a no-paid project. Do not repeatedly say paid
validation is unauthorized in the proposal body.

Use this framing instead:

```text
The project should spend evaluation budget only after the benchmark release,
candidate policy, baseline suite, success criteria, and score-join procedure
are frozen. Before that point, retrospective replay and local diagnostics are
used to reduce waste and prevent post-hoc validation.
```

Resource section expectations:

- acknowledge that real project operation may require budgeted ACUT evaluation;
- separate exploratory local analysis from formal paid evaluation;
- leave exact budget, staffing, and duration as bracketed decisions if they are
  not known;
- avoid making "no paid work" a premise of the project.

### Evidence Framing

Use Phase 1 evidence only for these proposal functions:

```text
The problem is real.
The work is technically feasible.
The metric is meaningful.
Benchmark selection has early signal.
The path to stronger validation is concrete.
```

Do not write an experiment chronology in the main body.

Use the current numbers carefully:

- old weighted design failed materially against simple same-budget baselines;
- workspace ACUT execution completed `120/120` exploratory cells with
  scoreability `1.0`;
- click source context was repaired for `30/30` tasks;
- current candidate MAE is `0.209`;
- best simple aggregate baseline MAE is `0.2149`;
- aggregate MAE edge is `0.0059`;
- current candidate beats/ties `93.4%` of 1000 same-budget random selections;
- `6/18` selected slots use fallback and `6/6` boltons slots use fallback;
- current evidence is weaker for Codex than for Kilo under the existing named
  ACUT configurations.

Explain MAE in plain English: average prediction error. Lower MAE means the
benchmark's estimate is closer to observed future-work performance.

### Validation Framing

In the main body, explain the future validation strategy without dumping the
technical protocol:

- freeze the benchmark before seeing future outcomes;
- compare its predictions against simple baselines;
- use rolling-origin or future holdout evidence;
- report results by named ACUT configuration;
- handle invalid cells and task-source problems with predefined rules;
- require a practically meaningful improvement before claiming predictive
  validity.

Detailed thresholds, fallback caps, support thresholds, release-manifest fields,
and schema names belong in an appendix or a linked protocol summary unless they
are essential to the main argument.

## Worker Prompt

Use this prompt to start the execution worker:

```text
You are executing docs/experiments/phase-1-proposal-report-v3-genre-repair-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first.
Then read the runbook and follow it with step-level acceptance and scoped
commits.

Main goal: create docs/research/phase-1-proposal-report-v3.md by repairing the
proposal-report genre regression in V2. Preserve the M1/V1 section structure
unless a clear reader-facing reason requires a change. Use V2 for evidence,
citations, and conservative claim boundaries, but remove internal milestone
language, no-paid/paid-authorization process language, and pre-proposal
packaging work from the proposal argument.

The final report should read as the project proposal endpoint of pre-proposal
work and the starting document for the approved project. It should ask for
approval to build and validate Barcarolle, explain why predictive validity is
the north star, summarize preliminary evidence, describe the approved project's
work, and state that budgeted ACUT evaluation may be needed after protocols and
success criteria are frozen.

Do not run paid ACUT cells, paid LLM calls, or external reviewer calls. Do not
change score tables, selected task IDs, split labels, source eligibility, task
statements, or completed decisions. Do not draft a deck or M6 approval packet.
Do not claim predictive validity has been established.
```

## Step 0: Preflight And Regression Diagnosis

Actions:

1. Record branch, HEAD, date, worktree status, and input availability in the
   process report.
2. Read V1 and V2 side by side.
3. Record a short diagnosis of V2's genre regression:
   - where it leaks milestone/process vocabulary;
   - where it treats an internal paid-run guardrail as a proposal premise;
   - where "next phase" means pre-proposal or packaging work instead of the
     approved project;
   - where technical detail should move out of the main body.
4. Confirm that V3 will use V1 as the structural reference and V2 as evidence
   source material.

Acceptance:

- process report contains the diagnosis;
- no paid/external calls made;
- no report text changed yet except process artifacts if needed.

Suggested commit:

```text
Record proposal v3 genre repair preflight
```

## Step 1: Build The V1-to-V3 Section Map

Actions:

1. Create a section map in the process report or optional section-map artifact.
2. For each V1 section, state:
   - reader question it answers;
   - V2 material to keep;
   - V2 material to remove, translate, or move to appendix;
   - evidence or citation source.
3. Explicitly map V2 sections 6-9 into V1 sections 6-11 so the back half no
   longer reads like an internal protocol packet.

Acceptance:

- every V3 section has a reader-facing job;
- M1/V1 structure is preserved unless a documented exception is made;
- paid evaluation is mapped to resource planning, not to a repeated prohibition.

Suggested commit:

```text
Map proposal v3 section repair
```

## Step 2: Draft V3 From The M1 Structure

Actions:

1. Create `docs/research/phase-1-proposal-report-v3.md`.
2. Start from the V1 section structure.
3. Pull in V2's public citations and resolved evidence only where they serve
   the section's reader-facing purpose.
4. Keep the report self-contained enough that a reviewer can understand it
   without reading runbooks or the roadmap.

Acceptance:

- V3 exists;
- headings are close to V1's headings;
- V3 does not read as a current-state report, internal roadmap, or M6 setup
  memo;
- predictive validity is not claimed as established.

Suggested commit:

```text
Draft proposal report v3 from M1 structure
```

## Step 3: Rewrite The Opening And Ask

Actions:

1. Rewrite the status note and executive summary.
2. Remove "no-paid research project" and "paid validation remains
   unauthorized" from the proposal ask.
3. State the approval ask in project terms:
   - approve Barcarolle as a repo-specific benchmark-compiler project;
   - build and optimize benchmark-selection algorithms;
   - validate predictive value through preregistered future-work designs;
   - budget evaluation only after protocols and success standards are frozen.
4. Keep the current evidence boundary:
   - traction and credible path, not formal predictive validity.

Acceptance:

- executive summary can stand alone for a reviewer;
- project ask is positive and concrete;
- paid evaluation appears, if at all, as planned budgeted evaluation under
  conditions, not as something repeatedly forbidden.

Suggested commit:

```text
Repair proposal v3 opening and project ask
```

## Step 4: Rewrite Evidence As Proposal Traction

Actions:

1. Rewrite the preliminary-evidence section around reader questions:
   - Is the problem real?
   - Is the work feasible?
   - Is there enough signal to justify project work?
2. Explain MAE and the random-baseline result in plain language.
3. Keep the small simple-baseline edge visible without making it the whole
   story.
4. State adapter and fallback caveats as reasons for project work, not as
   internal milestone failure labels.
5. Move detailed evidence tables to appendices if they interrupt the argument.

Acceptance:

- evidence section is not chronological;
- no section heading or paragraph requires knowing M3/M4/M5;
- numbers are preserved accurately;
- current evidence remains traction-only.

Suggested commit:

```text
Rewrite proposal v3 evidence narrative
```

## Step 5: Rewrite Validation And Project Plan

Actions:

1. Rewrite validation strategy in plain language.
2. Keep true future holdout, rolling-origin, and pseudo-future replay, but
   explain them as validation designs rather than internal study modes.
3. Move detailed thresholds and schema fields to an appendix or linked
   protocol summary.
4. Rewrite the project plan as work after approval:
   - improve and compare benchmark-selection algorithms;
   - strengthen task supply and certification only where it supports the
     compiler claim;
   - freeze benchmark releases and baselines before score joins;
   - run budgeted ACUT evaluation when the protocol is ready;
   - publish release manifests, reports, and validation results.
5. Remove M6 packaging work from the proposal body.

Acceptance:

- "next phase" means the approved project phase;
- validation is understandable without internal protocol vocabulary;
- paid evaluation is handled as an ordinary budget/resource item;
- no detailed threshold table dominates the main body.

Suggested commit:

```text
Rewrite proposal v3 validation and project plan
```

## Step 6: Repair Risks, Deliverables, And Appendices

Actions:

1. Shorten risk handling to mature proposal risks:
   - preliminary evidence may not generalize;
   - task supply may be thin or biased;
   - adapter-specific results may not generalize across ACUT configurations;
   - benchmark selection algorithms may fail to beat simple baselines;
   - future validation could become post-hoc without freezing;
   - evaluation budget may be spent before evidence is ready.
2. For each risk, state mitigation in project terms.
3. Rewrite deliverables as outputs of the approved project, not artifacts
   already produced by milestones.
4. Keep appendices for evidence index, citations, and technical protocol
   details.

Acceptance:

- risks are intelligible to a proposal reader;
- deliverables do not list internal runbook artifacts as if they were project
  deliverables;
- appendices support the main argument without taking over it.

Suggested commit:

```text
Repair proposal v3 risks and deliverables
```

## Step 7: Update Checklist And Handoff Documents

Actions:

1. Revise `docs/research/phase-1-proposal-report-reviewer-ready-checklist.md`
   so it checks:
   - reader-facing problem and ask;
   - M1/V1 structure preservation;
   - absence of internal milestone vocabulary from the main body;
   - correct paid-evaluation framing;
   - evidence accuracy and claim boundary;
   - back-half readability;
   - citation and artifact hygiene.
2. Update the roadmap only to say V3 supersedes V2 for proposal use and that
   M6 should wait until V3 is accepted.
3. Update `PROCESS.md` only to record the active proposal report and the new
   stop label.

Acceptance:

- support docs point to V3 if V3 passes review;
- roadmap duties remain in
  `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`;
- process notes stay concise.

Suggested commit:

```text
Align proposal v3 handoff documents
```

## Step 8: Audit

Run these checks:

```bash
rg -n "\bM[0-9]\b|runbook|roadmap|P0|P1|placeholder|no-paid|paid remains unauthorized|does not authorize paid|M6|user-owned" docs/research/phase-1-proposal-report-v3.md
rg -n "validated predictive benchmark compiler|proves predictive validity|established predictive validity|model-only superiority" docs/research/phase-1-proposal-report-v3.md
rg -n "/Users/chenmohan/Downloads" docs/research/phase-1-proposal-report-v3.md
git diff --check
```

Interpretation:

- the first command should return no main-body matches except legitimate
  appendix file names or quoted artifact paths that the process report
  explains;
- the second command should return no matches;
- the third command should return no matches;
- `git diff --check` must pass.

Manual review questions:

```text
If a reviewer never reads PROCESS.md or any runbook, can they still understand
the project?

Does the report ask for approval of the actual project, not the remaining
pre-proposal work?

Does the report present budgeted evaluation as a normal project requirement
rather than a prohibited activity?

Does the back half still read like a proposal, not a protocol dump?

Did the rewrite preserve all numerical evidence without strengthening it?
```

Acceptance:

- text checks pass or every acceptable match is explained;
- manual review answers are yes;
- `git diff --check` passes.

Suggested commit:

```text
Audit proposal report v3 genre repair
```

## Step 9: Closeout

Actions:

1. Write:

```text
experiments/phase1_compiler/reports/phase1_proposal_report_v3_genre_repair_process.md
experiments/phase1_compiler/reports/phase1_proposal_report_v3_genre_repair_decision.md
experiments/phase1_compiler/results/phase1_proposal_report_v3_genre_repair_decision.json
```

2. Stop with one label:

```text
proposal_report_v3_genre_repair_complete
blocked_v3_still_reads_as_process_report
blocked_paid_evaluation_framing_unclear
blocked_claim_boundary_unclear
blocked_missing_user_resource_decisions
blocked_missing_core_inputs
```

Decision report must state:

- whether V3 supersedes V2 as the active proposal report;
- whether V3 preserves the M1 structure or why it changed;
- how paid evaluation is framed in the proposal;
- which internal/process terms remain, if any, and why;
- whether predictive validity remains unproven;
- what remains before M6 or another approval artifact can start.

Suggested commit:

```text
Close proposal report v3 genre repair
```

## Final Report Expectations

The closeout should say, in plain terms:

```text
What changed:
  V3 repairs V2's proposal-genre regression while preserving V2's evidence and
  claim safety.

Why it matters:
  the active report now argues for the actual project rather than narrating
  internal pre-proposal milestones or execution safeguards.

What can happen next:
  the user/coordinator can review V3 as the proposal report. Only after V3 is
  accepted should the team decide whether to create a deck, decision memo, or
  other approval artifact.
```

Do not draft the next runbook unless the user explicitly asks after reviewing
V3.
