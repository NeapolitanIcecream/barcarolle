# Phase 1 Proposal Report Final-Shape Rewrite Runbook

Status: no-paid proposal-writing correction runbook, 2026-05-30.

This runbook is for one dedicated Codex CLI session. Its job is to write the
proposal report as a final-shape proposal-approval document with explicit
placeholders, not as a current-state report, internal roadmap, experiment
ledger, or evidence inventory.

```text
Create docs/research/phase-1-proposal-report-v1.md as the report that should
exist when pre-proposal work is complete, leaving [NEEDS ...] placeholders for
missing numbers, figures, pseudocode, citations, and result-dependent
paragraphs.
```

Plain-language summary:

```text
The previous v0 report collected useful material but still wrote from the
current research state. This runbook writes from the desired proposal endpoint:
if all remaining pre-proposal evidence were filled in, the report structure
should already be final.
```

## Execution Boundary

This runbook is no-paid writing and synthesis work. It must not make paid ACUT
solver calls, paid LLM calls, or external GPT-5.5-Pro calls.

Allowed work:

- read local planning files, completed runbooks, committed reports, and local
  review files;
- use `docs/research/phase-1-proposal-report-v0.md` as source material, not as
  the structure to preserve;
- create `docs/research/phase-1-proposal-report-v1.md`;
- optionally add a short supersession note to
  `docs/research/phase-1-proposal-report-v0.md`;
- update supporting proposal documents only when needed to point at v1 and keep
  roles clear;
- update `PROCESS.md` if the handoff state changes;
- run lightweight text checks and `git diff --check`.

Disallowed work:

- running paid ACUT cells;
- running paid or external LLM review calls;
- calling GPT-5.5-Pro or another external reviewer;
- rerunning paid cells or changing completed outcomes;
- changing score tables, selected task IDs, split labels, source eligibility
  artifacts, task statements, or completed experiment decisions;
- creating a new roadmap file;
- moving roadmap duties out of
  `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`;
- drafting later milestone runbooks;
- claiming predictive validity is established;
- inventing future experimental results;
- committing raw prompts, raw completions, raw ACUT transcripts, solver
  workspaces, verifier workspaces, target repo clones, raw public API
  responses, raw target diffs, raw test patches, `.venv`, caches, secrets, or
  large raw outputs.

## Starting Point

The current document roles are:

```text
docs/research/phase-1-proposal-report-v0.md:
  useful source material, but still too close to a current-state research
  report and process/evidence ledger.

docs/research/phase-1-proposal-roadmap-and-claim-planning.md:
  internal roadmap owner. Keep it that way.

docs/research/phase-1-proposal-argument-map.md:
  internal claim/warrant scaffolding.

docs/research/phase-1-proposal-evidence-todo-matrix.md:
  internal tracker for what evidence exists and what remains.

docs/research/phase-1-proposal-claim-boundary.md:
  guardrail for allowed, draft, and prohibited claims.
```

The correction is not "polish v0." The correction is:

```text
Write v1 as the proposal report that will be handed to reviewers once the
remaining pre-proposal blanks are filled.
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-proposal-report-final-shape-rewrite-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first.
Then read docs/research/phase-1-proposal-report-v0.md,
docs/research/phase-1-proposal-roadmap-and-claim-planning.md,
docs/research/phase-1-proposal-argument-map.md,
docs/research/phase-1-proposal-evidence-todo-matrix.md, and
docs/research/phase-1-proposal-claim-boundary.md. Follow AGENTS.md step-level
acceptance and commit requirements.

Main goal: create docs/research/phase-1-proposal-report-v1.md as a
final-shape proposal report with placeholders. The report should read as the
endpoint of pre-proposal work and the starting document for the actual project,
not as a snapshot of current progress. Use academic-paper-writing discipline:
reader problem, research question, contribution, method/source plan,
feasibility, risks, objections, responses, and scoped next-phase ask.

Write from the final report shape. Do not preserve v0's organization if it
keeps the report in current-state/reporting mode. Use v0 as material only.
Leave precise [NEEDS ...] placeholders for missing numbers, tables, figures,
pseudocode, citations, and result-dependent paragraphs. Do not invent future
results.

Keep predictive validity as the north star. Keep Phase 1 evidence only where
it supports the proposal argument: the problem is real, the work is technically
tractable, and the next phase is justified. Do not write a chronological
"Phase 1 evidence" ledger in the main body.

Do not create a new roadmap file. The existing
docs/research/phase-1-proposal-roadmap-and-claim-planning.md remains the
roadmap. Do not draft later runbooks.

Do not run paid ACUT cells. Do not call paid LLMs. Do not call GPT-5.5-Pro or
any external reviewer. Do not rerun completed cells. Do not change paid
outcomes, score tables, selected task IDs, split labels, source eligibility,
task statements, or completed decisions.
```

## Required Inputs

Read these coordination and proposal files:

```text
AGENTS.md
PROCESS.md
docs/research/phase-1-proposal-report-v0.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
docs/research/phase-1-proposal-argument-map.md
docs/research/phase-1-proposal-evidence-todo-matrix.md
docs/research/phase-1-proposal-claim-boundary.md
docs/architecture/system-design.md
```

Read these local research plans and reviews as needed:

```text
/Users/chenmohan/Downloads/barcarolle-research-0519.md
/Users/chenmohan/Downloads/barcarolle-research-0526.md
/Users/chenmohan/Downloads/barcarolle-research-0526-1.md
/Users/chenmohan/Downloads/barcarolle-research-0530.md
```

Use these canonical reports for evidence, but do not reproduce them as a lab
diary:

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

Add:

```text
docs/research/phase-1-proposal-report-v1.md
```

Optionally update:

```text
docs/research/phase-1-proposal-report-v0.md
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
    phase1_proposal_report_final_shape_rewrite_decision.json
  reports/
    phase1_proposal_report_final_shape_rewrite_process.md
    phase1_proposal_report_final_shape_rewrite_decision.md
```

## V1 Report Contract

`phase-1-proposal-report-v1.md` should be a final-shape proposal report, not a
current-state memo. Suggested structure:

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

Section functions:

- Executive Summary: state the problem, Barcarolle's contribution, north star,
  current readiness, and ask in proposal language.
- Problem And Stakes: explain why repo-specific future-performance prediction
  matters to readers.
- Research Question And North Star: define predictive validity as the long-term
  success criterion without claiming it is already proved.
- Barcarolle Thesis And Boundary: distinguish benchmark compilation from task
  generation, ACUT harnessing, and leaderboard work.
- Proposed Benchmark-Compiler Design: describe the intended system/algorithmic
  object at the level the final proposal needs, with placeholders for diagrams
  and pseudocode.
- Validation Strategy: define estimand, ACUT scope, baselines, metrics, adapter
  reporting, future holdout or rolling-origin design, success gates, and
  invalid-cell handling, using placeholders where exact values remain missing.
- Preliminary Evidence And Feasibility: use Phase 1 evidence only to show that
  the problem is real, measurable, and tractable.
- Project Plan: describe work packages and decision gates at proposal level,
  not internal runbook steps.
- Risks: present strongest objections and concrete mitigations.
- Expected Deliverables: list what the funded/approved project will produce.
- Appendices: point to evidence, current artifacts, claim boundaries, and
  technical details that would distract from the main argument.

## Placeholder Rules

Use placeholders as contracts, not vague TODOs. Preferred forms:

```text
[NEEDS RESULT: many-seed random baseline percentile for current candidate]
[NEEDS TABLE: Phase 1 evidence summary with claim strength and limitation]
[NEEDS FIGURE: predictive-validity validation design]
[NEEDS PSEUDOCODE: candidate benchmark assembly policy]
[NEEDS CITATION: concise comparison to SWE-bench-family and generated-task systems]
[NEEDS DECISION: fallback threshold for composite selector claim]
[DRAFT CLAIM pending M4 validation-protocol hardening: ...]
```

Every placeholder must specify what is missing clearly enough that a later
milestone can fill it. Do not use placeholders to hide an unsupported claim.
Do not write future results as if they already happened.

## Preliminary Evidence Rule

Phase 1 evidence belongs in v1 only when it answers one of these reader
questions:

```text
Is the problem real?
Is the work technically tractable?
Is there enough traction to justify the next phase?
```

The main body should not walk through Phase 1 chronology. If detailed evidence
is useful, route it to an appendix or evidence index. A concise preliminary
evidence section or table is acceptable; an experiment-by-experiment ledger is
not.

## Step 0: Preflight And Failure Diagnosis

Actions:

1. Record branch, HEAD, date, worktree status, and required-input availability
   in the process report.
2. Diagnose why v0 is insufficient:
   - where it describes current state instead of final proposal state;
   - where it exposes process details the proposal reader does not need;
   - where Phase 1 evidence lacks a clear argumentative function.
3. Confirm that the new target is v1 final-shape report with placeholders.

Acceptance:

- no paid calls made;
- v0 failure mode is recorded;
- v1 target contract is recorded;
- no new roadmap file created.

Commit:

```text
Record proposal final-shape rewrite preflight
```

## Step 1: Define The Final-Shape Report Contract

Actions:

1. Write a concise reader brief in the process report:
   - target readers;
   - what they already know;
   - what they doubt;
   - what would justify approval;
   - what the report must not overclaim.
2. Map each v1 section to one reader question.
3. Decide which content belongs in the main body and which belongs in an
   appendix or supporting document.

Acceptance:

- each planned v1 section has a reader-facing job;
- Phase 1 evidence has a limited argumentative role;
- internal roadmap details are excluded from the main body.

Commit:

```text
Define proposal report v1 contract
```

## Step 2: Write Proposal Report V1 From The Contract

Actions:

1. Create `docs/research/phase-1-proposal-report-v1.md`.
2. Write v1 from the section contract, not by lightly editing v0.
3. Keep the north star as predictive validity.
4. State the current short-term claim as traction and path, not validation.
5. Describe the proposed technical approach and validation strategy at the
   level needed for a final proposal, with placeholders where results,
   figures, exact algorithms, or gates remain missing.
6. Compress Phase 1 evidence into preliminary evidence and feasibility.
7. Move detailed process evidence to appendices or links.

Acceptance:

- v1 reads as a final-shape proposal report with placeholders;
- v1 does not read as a current-state report;
- v1 does not read as an internal roadmap;
- v1 does not contain an experiment-by-experiment Phase 1 ledger in the main
  body;
- every missing value or result-dependent paragraph is marked with a precise
  placeholder;
- no future result is invented;
- predictive validity is not claimed as established.

Commit:

```text
Write proposal report v1 final-shape draft
```

## Step 3: Align Supporting Documents

Actions:

1. Add a supersession note to v0 if useful.
2. Update the argument map only if v1 changes the claim, warrant, or objection
   structure.
3. Update the evidence/TODO matrix only if v1 changes which missing evidence
   matters.
4. Update the claim boundary only if v1 needs a new guardrail.
5. Update the roadmap planning document only if it needs to say that v1
   supersedes the old report draft.
6. Update `PROCESS.md` with the new handoff state if needed.

Acceptance:

- roadmap ownership remains in
  `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`;
- supporting docs point to v1 cleanly;
- no duplicate roadmap file exists;
- no later runbook is drafted.

Commit:

```text
Align proposal report v1 supporting documents
```

## Step 4: Self-Review Against The Final-Shape Standard

Actions:

1. Review v1 against these questions:

```text
If all [NEEDS ...] placeholders were filled, would this be close to the final
proposal-approval report?

Can a proposal reader understand the project without reading internal runbooks?

Does every Phase 1 evidence paragraph support a reader-facing claim?

Are algorithm, validation, and risk sections shaped as proposal content rather
than process notes?

Are unsupported or result-dependent claims explicitly marked?
```

2. Run lightweight text checks, for example:

```bash
rg -n "M[0-9]|runbook|roadmap|current state|completed cells|score table" docs/research/phase-1-proposal-report-v1.md
rg -n "proves predictive validity|established predictive validity|authorizes paid" docs/research/phase-1-proposal-report-v1.md
git diff --check
```

Use judgment: these searches are diagnostics, not automatic failures. If a
term appears for a legitimate reason, explain it in the process report.

Acceptance:

- v1 passes the final-shape review or the run stops with a blocker label;
- `git diff --check` passes;
- no paid calls made.

Commit:

```text
Audit proposal report v1 final-shape standard
```

## Step 5: Closeout

Actions:

1. Write:

```text
experiments/phase1_compiler/reports/phase1_proposal_report_final_shape_rewrite_process.md
experiments/phase1_compiler/reports/phase1_proposal_report_final_shape_rewrite_decision.md
experiments/phase1_compiler/results/phase1_proposal_report_final_shape_rewrite_decision.json
```

2. Stop with one label:

```text
proposal_report_final_shape_rewrite_complete
blocked_final_shape_report_not_reached
blocked_claim_boundary_unclear
blocked_missing_core_inputs
blocked_v1_still_reads_as_process_report
```

Decision must say:

- no paid calls were made;
- whether v1 now functions as the final-shape proposal report;
- whether v0 was superseded or left as source material;
- which placeholders remain P0 before the report can be filled;
- which next milestone category is recommended, without drafting the next
  runbook.

Commit:

```text
Close proposal report final-shape rewrite
```

## Final Report Expectations

The closeout should say:

```text
What happened:
  proposal report v1 was created as a final-shape proposal document with
  explicit placeholders.

Why it matters:
  remaining experiments can now be pulled by report blanks rather than by
  process drift or local curiosity.

What action it suggests next:
  fill the highest-priority placeholders that block reviewer readiness, while
  keeping paid validation unauthorized until the protocol and evidence gates
  are hardened.
```

Do not draft the next runbook unless the user explicitly asks after reviewing
v1.
