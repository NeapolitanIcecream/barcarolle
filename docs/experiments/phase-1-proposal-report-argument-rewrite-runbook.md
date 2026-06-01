# Phase 1 Proposal Report Argument Rewrite Runbook

Status: no-paid writing revision runbook, 2026-05-30.

This runbook is for one dedicated Codex CLI session. Its job is to revise the
M1 proposal report so it becomes a reader-facing research proposal argument,
not a roadmap, evidence ledger, or milestone plan.

```text
Rewrite docs/research/phase-1-proposal-report-v0.md using the
academic-paper-writing argument structure: problem, question, claim, reasons,
evidence, warrants, objections, response, and scoped next phase.
```

Plain-language summary:

```text
The M1 skeleton collected the right materials, but it mixed proposal writing
with internal roadmap management. This runbook keeps the existing roadmap file
as the internal planning document and rewrites the proposal report itself as an
argument for why Barcarolle should be funded or continued.
```

## Execution Boundary

This runbook is no-paid writing and revision work. It must not make paid ACUT
solver calls, paid LLM calls, or external GPT-5.5-Pro calls.

Allowed work:

- read M1 outputs, the proposal roadmap planning document, local research
  plans, external review, and canonical experiment reports;
- rewrite `docs/research/phase-1-proposal-report-v0.md` into a
  proposal-facing research argument;
- update `docs/research/phase-1-proposal-argument-map.md` only if the rewrite
  exposes a better claim, warrant, or objection structure;
- update `docs/research/phase-1-proposal-evidence-todo-matrix.md` only to
  align evidence gaps with the rewritten report;
- update `docs/research/phase-1-proposal-claim-boundary.md` only if wording
  changes require it;
- update `PROCESS.md` only if the handoff state changes.

Disallowed work:

- creating a new roadmap file;
- duplicating `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`;
- turning the proposal report into an M2-M6 task list;
- drafting M2-M6 runbooks;
- running paid ACUT cells or paid LLM calls;
- rerunning paid cells or changing paid outcomes;
- changing completed score tables, selected task IDs, split labels, source
  eligibility artifacts, task statements, or completed decisions;
- claiming predictive validity is established;
- treating GPT-5.5-Pro recommendations as mandatory scope expansion;
- committing raw prompts, raw completions, raw ACUT transcripts, solver
  workspaces, verifier workspaces, target repo clones, raw public API
  responses, raw target diffs, raw test patches, `.venv`, caches, secrets, or
  large raw outputs.

If the report needs an internal roadmap detail, link to
`docs/research/phase-1-proposal-roadmap-and-claim-planning.md` or use one short
paragraph. Do not reproduce milestone management in the report body.

## Starting Point

The current M1 outputs are useful but imperfect:

```text
docs/research/phase-1-proposal-report-v0.md:
  contains useful proposal material, but mixes report argument with roadmap,
  evidence TODOs, and milestone management.

docs/research/phase-1-proposal-roadmap-and-claim-planning.md:
  already owns internal roadmap and claim-planning duties.

docs/research/phase-1-proposal-argument-map.md:
  is closer to the right argument structure and should drive the rewrite.

docs/research/phase-1-proposal-evidence-todo-matrix.md:
  should remain an internal evidence tracker or appendix, not the report body.
```

Correct document roles after this run:

```text
Proposal report:
  reader-facing argument for project value and next-phase research.

Roadmap and claim planning:
  internal plan for M1-M6, GPT-5.5-Pro prioritization, and milestone order.

Evidence/TODO matrix:
  internal tracker or appendix for what evidence exists and what remains.

Claim boundary:
  writing guardrail and possible appendix.
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-proposal-report-argument-rewrite-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first,
then read docs/research/phase-1-proposal-roadmap-and-claim-planning.md,
docs/research/phase-1-proposal-argument-map.md, and
docs/research/phase-1-proposal-report-v0.md. Use uv only if needed for
lightweight checks. Follow AGENTS.md step-level acceptance and commit
requirements.

Main goal: rewrite the proposal report as a research argument, not a roadmap.
Use the academic-paper-writing structure: reader problem, research question,
claim, reasons, evidence, warrants, objections, responses, limitations, and a
scoped next phase. Keep predictive validity as the north star. Keep the
short-term proposal claim focused on why predictive validity is valuable and
why Phase 1 gives enough traction to justify exploring it further.

Do not create a new roadmap file. The existing
docs/research/phase-1-proposal-roadmap-and-claim-planning.md remains the
roadmap. If it needs minor alignment, update it there, but do not duplicate it.

Do not run paid ACUT cells. Do not call paid LLMs. Do not call GPT-5.5-Pro or
any external reviewer. Do not rerun completed cells. Do not change paid
outcomes, score tables, selected task IDs, split labels, source eligibility,
task statements, or completed decisions.

Do not claim predictive validity is proved. Use [NEEDS ...] placeholders only
where a missing table, citation, figure, or number is necessary for the
proposal argument. Keep internal task lists out of the report body.
```

## Required Inputs

Read these coordination files:

```text
AGENTS.md
PROCESS.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
docs/research/phase-1-proposal-argument-map.md
docs/research/phase-1-proposal-evidence-todo-matrix.md
docs/research/phase-1-proposal-claim-boundary.md
docs/research/phase-1-proposal-report-v0.md
docs/architecture/system-design.md
```

Read these local research plans and reviews as needed:

```text
/Users/chenmohan/Downloads/barcarolle-research-0519.md
/Users/chenmohan/Downloads/barcarolle-research-0526.md
/Users/chenmohan/Downloads/barcarolle-research-0526-1.md
/Users/chenmohan/Downloads/barcarolle-research-0530.md
```

Use these canonical reports for evidence:

```text
experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md
experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md
experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md
experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md
experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md
experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md
experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md
experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md
experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_validation_protocol.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md
```

## Output Layout

Update:

```text
docs/research/phase-1-proposal-report-v0.md
```

Optionally update, only when necessary:

```text
docs/research/phase-1-proposal-argument-map.md
docs/research/phase-1-proposal-evidence-todo-matrix.md
docs/research/phase-1-proposal-claim-boundary.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
PROCESS.md
```

Add closeout artifacts:

```text
experiments/phase1_compiler/
  results/
    phase1_proposal_report_argument_rewrite_decision.json
  reports/
    phase1_proposal_report_argument_rewrite_process.md
    phase1_proposal_report_argument_rewrite_decision.md
```

Do not add a new roadmap document.

## Report Shape

The rewritten report should read like a proposal, not a roadmap. Suggested
structure:

```text
1. Executive Thesis
2. The Research Problem
3. Why Existing Benchmarks And Task Generators Do Not Solve It
4. Barcarolle's Approach
5. Phase 1 Evidence
6. Interpretation: What This Evidence Shows And Does Not Show
7. Research Agenda Toward Predictive Validity
8. Risks, Objections, And Responses
9. Proposal Ask / Next Phase
```

The report may mention next-phase work, but it should not list internal M2-M6
milestones. Put internal milestone logic in the roadmap file.

## Writing Requirements

Use the academic-paper-writing discipline:

- start from reader-facing cost, not internal chronology;
- make the main claim clear and qualified;
- connect each reason to evidence with an explicit warrant;
- include objections before readers have to raise them;
- keep limitations near the claims they qualify;
- preserve source meaning and do not strengthen evidence beyond what reports
  support;
- quote or cite local files by path when needed;
- mark missing support with `[NEEDS ...]`;
- avoid turning all evidence into a chronological lab diary.

Required argument moves:

```text
Problem:
  General SWE benchmarks and task generators do not directly estimate future
  target-repo performance.

North star:
  Predictive validity for repo-specific benchmarks.

Short-term claim:
  Phase 1 does not prove predictive validity, but it shows that the problem is
  real, measurable, and technically tractable.

Evidence:
  weighted failure, local bakeoff, paid exploratory runs, source repair,
  adapter-stratified reporting, retrospective signal, candidate policy freeze.

Limit:
  no future holdout result; weak and adapter-fragile signal; boltons fallback;
  baseline and success criteria need hardening.

Next phase:
  algorithm and validation work aimed at the north star, not a generic task
  generator expansion.
```

## Step 0: Preflight And Diagnosis

Actions:

1. Record branch, HEAD, date, and worktree status in the process report.
2. Diagnose the current report's failure mode:
   - where it reads like a report argument;
   - where it reads like roadmap management;
   - which sections should be rewritten, compressed, or moved by reference.
3. Confirm that `phase-1-proposal-roadmap-and-claim-planning.md` remains the
   roadmap owner.

Acceptance:

- no paid calls made;
- report/roadmap role distinction is written down;
- no new roadmap file created.

Commit:

```text
Record proposal report rewrite diagnosis
```

## Step 1: Rewrite The Report As An Argument

Actions:

1. Rewrite `docs/research/phase-1-proposal-report-v0.md` using the report
   shape above.
2. Remove internal milestone lists from the report body.
3. Keep evidence and limitations close to each claim.
4. Preserve useful `[NEEDS ...]` placeholders, but only when they serve the
   proposal argument.
5. Replace "M2/M3/M4" language with proposal-facing next-phase language.

Acceptance:

- report no longer reads as a roadmap;
- report contains a clear thesis, reasons, evidence, objections, and response;
- predictive validity remains the north star;
- current evidence is not overstated;
- no new roadmap file created.

Commit:

```text
Rewrite proposal report as research argument
```

## Step 2: Align Supporting Documents

Actions:

1. Update the argument map only if the rewritten report changes the claim or
   warrant structure.
2. Update the evidence/TODO matrix only if the rewritten report changes which
   missing evidence matters.
3. Update claim boundary only if wording changes need a guardrail.
4. Update the existing roadmap planning document only if it needs a small
   clarification that it owns roadmap duties.

Acceptance:

- no duplicate roadmap document exists;
- supporting docs point to the rewritten report roles cleanly;
- roadmap and report are not merged back together.

Commit:

```text
Align proposal report supporting documents
```

## Step 3: Closeout

Actions:

1. Write:

```text
experiments/phase1_compiler/reports/phase1_proposal_report_argument_rewrite_process.md
experiments/phase1_compiler/reports/phase1_proposal_report_argument_rewrite_decision.md
experiments/phase1_compiler/results/phase1_proposal_report_argument_rewrite_decision.json
```

2. Run:

```bash
git diff --check
```

3. Stop with one label:

```text
proposal_report_argument_rewrite_complete
blocked_report_still_reads_as_roadmap
blocked_claim_boundary_unclear
blocked_missing_core_inputs
```

Decision must say:

- no paid calls were made;
- no new roadmap file was created;
- whether the report now reads as a proposal argument;
- which next milestone is recommended.

Commit:

```text
Close proposal report argument rewrite
```

## Final Report Expectations

The closeout should say:

```text
What happened:
  proposal report was rewritten as an argument; roadmap remains in the existing
  planning document.

Why it matters:
  the report now answers the reviewer-facing proposal question instead of
  exposing the internal execution plan.

What action it suggests next:
  proceed to the highest-priority evidence or review-triage milestone named by
  the rewritten report and evidence matrix.
```

Do not draft the next runbook unless the user explicitly asks after reviewing
the rewritten report.
