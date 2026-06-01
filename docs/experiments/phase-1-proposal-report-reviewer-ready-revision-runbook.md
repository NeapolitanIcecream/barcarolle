# Phase 1 Proposal Report Reviewer-Ready Revision Runbook

Status: no-paid proposal-report revision runbook, 2026-06-01.

## Goal

Revise the final-shape proposal draft into a reviewer-ready technical proposal
report for project approval.

M5 should integrate M3 evidence and M4 protocol hardening into a coherent
reader-facing argument:

```text
Predictive validity is the long-term north star.
Phase 1 does not prove predictive validity.
Phase 1 does show that the metric is meaningful, benchmark selection affects
that metric, a current candidate beats most same-budget random selections, and
the remaining weaknesses are concrete optimization and validation work.
```

The report should make the case for starting the next project phase. It should
not treat the M4 future success gate as something that must already be passed
before the proposal can be approved.

## Boundary

M5 is report integration and reviewer-facing argument work.

Allowed:

- revise the proposal report;
- replace resolved `[NEEDS ...]` placeholders with M3/M4 evidence and explicit
  deferrals;
- browse public sources for reviewer-facing citations and related-work
  references;
- create compact figures, tables, and appendices in Markdown;
- add a reviewer-readiness checklist, citation matrix, and decision report;
- update `PROCESS.md`, the roadmap, and the evidence/TODO matrix with M5
  handoff state.

Not allowed:

- paid ACUT cells;
- paid LLM calls;
- external reviewer calls;
- changing score tables;
- changing selected task IDs or split labels;
- authorizing paid validation;
- claiming predictive validity has been established;
- converting M5 into M6 deck/memo production;
- setting user-owned staffing, duration, approval format, owner categories, or
  paid budget ceiling;
- drafting the M6 runbook.

Public browsing is allowed only for citation and related-work verification.
Prefer primary sources: official benchmark pages, official project pages,
papers, arXiv/OpenReview/ACM/IEEE pages, GitHub repos, or project docs. Do not
cite local planning files as reviewer-facing literature support.

## Interpretation To Preserve

Use M4 correctly.

M4's `0.02` MAE margin, fallback caps, adapter gates, and support thresholds
are future optimization and validation standards. They are not a reason to
kill the proposal before the project starts.

The proposal-facing interpretation is:

- MAE is meaningful because it measures average prediction error for future
  repo performance.
- M3 shows the metric can move with benchmark selection.
- The current candidate beats or ties `93.4%` of 1000 same-budget random
  selections, which is strong traction evidence that selection is not pure
  noise.
- The current candidate's edge over the best simple aggregate baseline is
  small (`0.0059` MAE), and Codex/fallback/repo diagnostics are fragile.
- Therefore the next phase should optimize and validate the compiler, not claim
  that it is already validated.

Do not write the report as:

```text
The current candidate failed the M4 gate, so the proposal is weak.
```

Write it as:

```text
M4 defines the project-stage success standard. The current evidence is not
enough to claim success, but it is enough to justify the next phase because the
metric is meaningful, selection has signal, and the remaining failure modes are
known and tractable.
```

## Inputs

Read these first:

- `AGENTS.md`
- `PROCESS.md`
- `docs/research/phase-1-proposal-report-v1.md`
- `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`
- `docs/research/phase-1-proposal-evidence-todo-matrix.md`
- `docs/research/phase-1-proposal-p0-placeholder-triage.md`
- `docs/research/phase-1-proposal-claim-boundary.md`
- `docs/research/phase-1-proposal-evidence-package.md`
- `docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md`
- `docs/experiments/phase-1-proposal-report-reviewer-ready-revision-runbook.md`

Evidence reports:

- `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`
- `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md`
- `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md`
- `experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md`
- `experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md`
- `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md`
- `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`
- `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md`
- `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_coverage_ablation.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_fallback_share.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_claim_modes.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_candidate_policy.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_adapter_estimand.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_success_gate.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_support_thresholds.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_power_budget_note.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md`

Structured results:

- `experiments/phase1_compiler/results/phase1_proposal_evidence_package_decision.json`
- `experiments/phase1_compiler/results/phase1_proposal_evidence_package_random_baseline_distribution.json`
- `experiments/phase1_compiler/results/phase1_proposal_evidence_package_baseline_envelope.json`
- `experiments/phase1_compiler/results/phase1_proposal_evidence_package_fallback_share.json`
- `experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_decision.json`
- `experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_success_gate.json`
- `experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_support_thresholds.json`
- `experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_release_schema.json`

Local planning and review inputs:

- `/Users/chenmohan/Downloads/barcarolle-research-0519.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0526.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0526-1.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0530.md`

Use local planning files to preserve intent and boundary. Replace them with
public citations where the report makes a literature or related-work claim.

## Expected Outputs

Create these outputs unless a stop condition prevents completion:

```text
docs/research/phase-1-proposal-report-v2.md
docs/research/phase-1-proposal-report-reviewer-ready-checklist.md

experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_process.md
experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_citation_matrix.md
experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_risk_register.md
experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_decision.md

experiments/phase1_compiler/results/phase1_proposal_report_reviewer_ready_revision_decision.json
```

Optional, only if useful:

```text
experiments/phase1_compiler/results/phase1_proposal_report_reviewer_ready_revision_citation_matrix.json
experiments/phase1_compiler/results/phase1_proposal_report_reviewer_ready_revision_placeholder_audit.json
```

Do not overwrite `docs/research/phase-1-proposal-report-v1.md`. Treat v1 as the
source draft and v2 as the reviewer-ready technical proposal report.

## Worker Prompt

Use this prompt for the execution worker:

```text
You are executing docs/experiments/phase-1-proposal-report-reviewer-ready-revision-runbook.md.

Read AGENTS.md and PROCESS.md first. Then read the runbook and follow it with
step-level acceptance and scoped commits.

This is M5 reviewer-ready proposal report revision. Do not run paid ACUT cells,
paid LLM calls, or external reviewer calls. Public citation browsing is allowed
only for related-work and reviewer-facing citation verification. Do not change
score tables, selected task IDs, or split labels. Do not draft M6 or set
user-owned staffing, duration, owner categories, approval format, or paid budget
ceiling.

Revise docs/research/phase-1-proposal-report-v1.md into
docs/research/phase-1-proposal-report-v2.md. The report should argue for
project approval, not prove predictive validity. Use M3 random-baseline
evidence to show the metric is meaningful and optimizable. Use M4 gates as
future project-stage standards, not as a pre-proposal failure condition. Keep
paid validation unauthorized and predictive validity unestablished.
```

## Step 0: Preflight And Reader Contract

1. Confirm M4 stop label is
   `validation_protocol_hardened_candidate_not_paid_ready`.
2. Confirm paid/external calls are disallowed and citation browsing is allowed
   only for public related-work sources.
3. Record the current Git commit and input artifact paths.
4. Define the reader contract for v2:
   - target reader: project/proposal reviewer;
   - decision requested: approve the next no-paid research phase;
   - current claim: traction plus credible path;
   - explicit non-claim: predictive validity is not established.

Acceptance evidence:

- process report records boundary flags and reader contract;
- v1 remains unchanged at this step;
- no paid/external calls are made.

Suggested commit:

```text
Record M5 proposal revision preflight
```

Stop if:

- M4 decision artifacts are missing;
- the report cannot be revised without user-owned approval values;
- the worker cannot keep public citation browsing separate from paid/external
  model calls.

## Step 1: Build The Argument Map

Before rewriting prose, write a compact argument map in the process report.

Required structure:

```text
Claim: approve the next research phase for Barcarolle as a repo-specific
benchmark compiler.

Reason 1: The target-repo prediction problem is real and consequential.
Evidence: problem framing, failed naive weighting, pilot gaps.

Reason 2: The benchmark-side protocol is technically tractable.
Evidence: completed workspace ACUT pilot, source repair, artifact hygiene,
endpoint/accounting boundaries.

Reason 3: The optimization target is meaningful and shows signal.
Evidence: MAE as prediction error; 1000-seed random baseline; small but
directional best-simple-baseline edge.

Reason 4: The path to predictive validity is concrete.
Evidence: M4 claim modes, future gates, support thresholds, release schema.

Limits: current evidence is retrospective, underpowered, adapter-fragile, and
fallback-composite; paid validation remains unauthorized.
```

Acceptance evidence:

- process report includes the argument map;
- the map does not use M4 gate failure as a reason against project approval;
- random-baseline evidence is assigned to "optimizable metric" rather than
  "validated predictor."

Suggested commit:

```text
Map reviewer-facing proposal argument
```

## Step 2: Citation And Related-Work Matrix

Fill the related-work citation gap with public sources.

At minimum, find reviewer-facing references for:

- SWE-bench-family or SWE-bench;
- SWE-bench Verified or other quality-improved SWE-bench variant if relevant;
- SWE-bench Live or live/contamination-aware benchmark maintenance if
  relevant;
- SWE-smith or generated task systems if relevant;
- R2E-Gym or agent-training/evaluation environments if relevant;
- at least one source for benchmark evaluation validity, predictive validity,
  or construct validity if a suitable public source is found.

For each source, record:

- citation label;
- URL;
- publication/project date when available;
- what claim it supports;
- what claim it must not be used for;
- where it appears in v2.

Do not over-browse. The goal is a concise related-work paragraph, not a
literature review.

Acceptance evidence:

- citation matrix exists;
- every public-source claim in v2 has a citation or is clearly internal
  evidence;
- local research plans are not used as reviewer-facing literature citations.

Suggested commit:

```text
Build proposal citation matrix
```

## Step 3: Draft V2 Report Skeleton

Create `docs/research/phase-1-proposal-report-v2.md` from v1.

Expected v2 shape:

1. Executive Summary
2. Problem And Stakes
3. Barcarolle Thesis And Boundary
4. Proposed Compiler Design
5. Evidence For Project Approval
6. Validation Path And Success Standards
7. Risks, Limits, And Mitigations
8. Proposed Next Phase
9. Deliverables And Decision Points
10. Appendices

Do not keep Appendix D as a placeholder register. V2 should have resolved
prose, tables, figures, or explicit user-decision callouts. If a value remains
user-owned, label it as a decision point, not an unresolved evidence gap.

Acceptance evidence:

- v2 exists with the expected report shape;
- v2 no longer reads like a roadmap or lab notebook;
- v2 keeps a concise main body and pushes details into appendices.

Suggested commit:

```text
Draft reviewer-ready proposal report structure
```

## Step 4: Rewrite Executive Summary And Main Claim

Rewrite the opening so the approval ask is clear.

Required wording content:

- Barcarolle is a benchmark compiler for repo-specific agent evaluation, not an
  ACUT harness, task factory, or leaderboard.
- The north star is predictive validity.
- The current report asks for approval to pursue that north star; it does not
  claim the north star has been reached.
- Current traction: the metric is meaningful, the old weighted design failed
  informatively, clean ACUT execution is feasible, and the current candidate
  beats/ties `93.4%` of 1000 same-budget random selections.
- Current limit: the best-simple-baseline edge is only `0.0059` MAE and the
  candidate is adapter-fragile and fallback-composite.
- M4 gates are next-phase standards, not pre-proposal proof requirements.

Avoid:

- "validated predictive benchmark compiler";
- "paid-ready";
- "proven predictive validity";
- implying that Kilo/Codex differences are model-only.

Acceptance evidence:

- executive summary can stand alone for a reviewer;
- current claim and non-claim are explicit;
- M4 is framed as future governance, not a failed current deliverable.

Suggested commit:

```text
Rewrite proposal executive claim
```

## Step 5: Integrate M3 Evidence As Approval Traction

Revise the evidence section around three approval questions:

```text
Is the problem real?
Is the work technically feasible?
Is there enough signal to justify optimization and validation work?
```

For the third question, make the random-baseline evidence prominent:

- current candidate MAE: `0.209`;
- best simple aggregate baseline MAE: `0.2149`;
- best-simple-baseline edge: `0.0059`;
- 1000-seed same-budget random comparison: candidate beats/ties `93.4%`;
- explain that random comparison shows selection has signal, while the
  best-simple-baseline comparison shows the current candidate is not yet
  strong enough for validation claims.

Include the fallback and adapter caveats:

- `6/18` selected benchmark slots use fallback;
- `6/6` boltons slots use fallback;
- Codex fails while Kilo passes under current adapter diagnostics.

Acceptance evidence:

- evidence section uses M3 outputs directly;
- MAE is explained in reader-friendly terms;
- random baseline and simple baseline play different argumentative roles;
- current candidate is not described as paid-ready.

Suggested commit:

```text
Integrate M3 proposal evidence
```

## Step 6: Integrate M4 As The Validation Path

Revise the validation strategy and success-gates sections using M4.

Required content:

- study-mode table: true future holdout, preregistered rolling-origin,
  pseudo-future replay;
- adapter estimand: primary claims are per named ACUT configuration;
- fallback governance: caps and consequence for composite selectors;
- mandatory baselines;
- joint success gate;
- support thresholds;
- release artifact schema;
- no-paid power/budget scenario note.

Interpretation rule:

```text
M4 defines how the next phase will know it is succeeding. It does not prove
current success, and it does not authorize paid validation.
```

Acceptance evidence:

- all M4-owned placeholders from v1 are replaced or explicitly narrowed;
- M4 gates appear as future validation standards;
- v2 says current M3 evidence does not pass those standards but remains
  useful traction.

Suggested commit:

```text
Integrate M4 validation path
```

## Step 7: Add Figures And Tables

Add compact Markdown tables or Mermaid diagrams where they improve readability.

Required:

- north-star validation design figure;
- compiler architecture figure;
- release artifact schema table or appendix pointer;
- one-page evidence summary;
- report evidence index;
- risk register.

Mermaid is acceptable for figures. Keep diagrams simple and text-light.

Do not create decorative figures. Every figure or table should answer a
reviewer question.

Acceptance evidence:

- required figures/tables exist in v2 or its appendices;
- figures do not introduce new claims;
- v2 no longer contains unresolved figure/table placeholders except user-owned
  M6 decision points.

Suggested commit:

```text
Add proposal figures and appendix tables
```

## Step 8: Risks, Objections, And Scope Control

Revise the objections section so it reads like mature proposal risk handling.

Must cover:

- failed weighted design;
- random evidence versus simple-baseline edge;
- current candidate not paid-ready;
- fallback/composite policy;
- adapter-specific support;
- task-generator scope drift;
- source quality and release schema;
- post-hoc validation risk;
- budget and paid-validation boundary.

For each risk, state:

- what the risk is;
- why it does not invalidate the proposal;
- what the next phase does about it;
- what claim remains prohibited until resolved.

Acceptance evidence:

- risk register exists;
- risk prose is not defensive;
- no risk response turns a limitation into a stronger finding than the evidence
  supports.

Suggested commit:

```text
Write reviewer-facing risk register
```

## Step 9: Deliverables And Decision Points

Replace user-owned placeholders with decision points.

Do not invent:

- no-paid staffing;
- duration;
- paid budget ceiling;
- owner categories;
- approval artifact format.

Instead, create a clean decision table:

| Decision | Owner | Needed before | Current default |
| --- | --- | --- | --- |

Use defaults only when they are non-binding. For example:

- "M5 technical report can proceed without this";
- "M6 must choose deck/memo/report format";
- "paid budget ceiling remains unset and non-authorized."

Acceptance evidence:

- v2 contains no fake budget/staffing numbers;
- M6 decisions are clearly separated from M5 technical readiness;
- paid validation remains blocked until a later user decision.

Suggested commit:

```text
Record proposal decision points
```

## Step 10: Reviewer-Readiness Audit

Create:

```text
docs/research/phase-1-proposal-report-reviewer-ready-checklist.md
```

The checklist must cover:

- claim boundary;
- evidence support;
- citation coverage;
- related-work distinction;
- M3 evidence integration;
- M4 validation-path integration;
- prohibited claims;
- remaining user decisions;
- artifact hygiene;
- paid/no-paid boundary;
- readability and structure.

Run these checks:

```text
rg -n "\[NEEDS" docs/research/phase-1-proposal-report-v2.md
rg -n "validated predictive benchmark compiler|proves predictive validity|established predictive validity|paid validation authorized|model-only superiority" docs/research/phase-1-proposal-report-v2.md
rg -n "/Users/chenmohan/Downloads" docs/research/phase-1-proposal-report-v2.md
```

Expected:

- no unresolved `[NEEDS ...]` markers in v2;
- prohibited-claim grep returns no matches, except if a checklist explicitly
  quotes prohibited claims as prohibited;
- local Downloads paths do not appear in the reviewer-facing main report.

Acceptance evidence:

- checklist exists;
- audit results are recorded in the process report;
- remaining unresolved items are user decisions, not evidence placeholders.

Suggested commit:

```text
Audit reviewer-ready proposal report
```

## Step 11: Synchronize Handoff Documents

Update:

- `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`
- `docs/research/phase-1-proposal-evidence-todo-matrix.md`
- `PROCESS.md`

Record:

- M5 status;
- v2 report path;
- whether M6 can proceed;
- remaining user decisions before M6;
- paid validation remains unauthorized;
- predictive validity remains future work.

Do not compress `PROCESS.md` unless it becomes hard to scan. If it is close to
the size target, replace stale proposal-process details with links instead of
adding long new paragraphs.

Acceptance evidence:

- handoff docs point to v2 and M5 closeout artifacts;
- roadmap says M6 is next only after user decisions;
- PROCESS does not become a duplicate lab notebook.

Suggested commit:

```text
Synchronize M5 proposal handoff
```

## Step 12: Closeout

Write:

```text
experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_decision.md
experiments/phase1_compiler/results/phase1_proposal_report_reviewer_ready_revision_decision.json
```

Closeout must state:

- stop label;
- v2 report path;
- whether v2 is reviewer-ready for technical proposal review;
- whether predictive validity is established;
- whether paid validation is authorized;
- whether M6 can proceed;
- what user decisions remain before M6;
- what citations were added;
- what placeholders remain, if any;
- what checks passed or failed.

Suggested stop labels:

- `proposal_report_reviewer_ready_for_technical_review`
- `proposal_report_ready_except_user_decisions`
- `blocked_related_work_citations`
- `blocked_claim_boundary_conflict`
- `blocked_m3_m4_integration`
- `blocked_user_decision_needed_for_report`
- `blocked_unresolved_placeholders`

Run:

```text
python3 -m json.tool experiments/phase1_compiler/results/phase1_proposal_report_reviewer_ready_revision_decision.json
git diff --check
```

If a script or generated checker was added, run its focused tests.

Suggested commit:

```text
Close M5 reviewer-ready proposal revision
```

## Completion Criteria

M5 is complete when:

- `docs/research/phase-1-proposal-report-v2.md` exists;
- v2 reads as a proposal report, not a roadmap or process log;
- v2 argues for project approval using the bounded Phase 1 claim;
- M3 random-baseline evidence is used to show signal and optimizability;
- best-simple-baseline, adapter, and fallback weaknesses are explicit limits;
- M4 gates are future project-stage standards, not current proof requirements;
- no unresolved evidence placeholders remain in v2;
- local planning files are replaced by public citations where needed;
- remaining user-owned decisions are explicit and isolated;
- paid validation remains unauthorized;
- predictive validity remains unestablished;
- handoff docs are synchronized;
- verification passes.

## Expected Interpretation

The expected M5 outcome is not:

```text
We have validated Barcarolle.
```

It is:

```text
We have a proposal-ready argument for why Barcarolle should be funded or
approved as a research project: the problem is real, the metric is meaningful,
the compiler choice has measurable signal, the current candidate exposes the
right next optimization targets, and the validation standard is now explicit.
```
