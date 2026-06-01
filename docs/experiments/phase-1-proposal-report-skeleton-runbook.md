# Phase 1 Proposal Report Skeleton Runbook

Status: no-paid writing and planning runbook, 2026-05-30.

This runbook is for one dedicated Codex CLI session. Its job is to execute M1
from `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`:

```text
Write a proposal-report skeleton, argument map, and evidence/TODO matrix that
keep short-term proposal work aligned with the predictive-validity north star.
```

Plain-language summary:

```text
The immediate goal is not to prove predictive validity or run another
experiment. The immediate goal is to produce a report-shaped plan that says:
what the project is trying to prove eventually, what Phase 1 already supports,
what remains unproven, and which missing evidence actually matters for
proposal readiness.
```

## Execution Boundary

This runbook is no-paid. It must not make paid ACUT solver calls, paid LLM
calls, or external GPT-5.5-Pro calls.

Allowed work:

- read committed reports, runbooks, process notes, review packets, and local
  research planning files;
- synthesize the north-star claim, short-term proposal claim, argument map, and
  evidence gaps;
- write proposal-facing draft documents under `docs/research`;
- create a Markdown evidence/TODO matrix mapping each needed claim to existing
  evidence or a future milestone;
- label unsupported or not-yet-ready claims with `Draft` or `[NEEDS ...]`;
- update `PROCESS.md` if the handoff state changes.

Disallowed work:

- running paid ACUT cells;
- running paid or external LLM review calls;
- rerunning paid cells or changing paid outcomes;
- changing completed score tables, selected task IDs, split labels, source
  eligibility artifacts, task statements, or completed decisions;
- creating a paid-validation runbook;
- claiming predictive validity is established;
- treating GPT-5.5-Pro recommendations as mandatory scope expansion;
- committing raw prompts, raw completions, raw ACUT transcripts, solver
  workspaces, verifier workspaces, target repo clones, raw public API
  responses, raw target diffs, raw test patches, `.venv`, caches, secrets, or
  large raw outputs.

If the worker finds that a necessary number or table is missing, it must insert
a precise `[NEEDS ...]` placeholder and route it to a later milestone instead
of stopping to run unrelated experiments.

## Starting Point

Current direction:

```text
long-term north star:
  predictive validity for repo-specific benchmarks

short-term proposal goal:
  show that predictive validity is valuable, that Phase 1 produced traction
  evidence, and that there is a credible research path toward the north star

not the short-term goal:
  prove predictive validity before proposal
```

The M1 report skeleton should make clear:

```text
Phase 1 does not prove predictive validity.
Phase 1 does show that benchmark construction choices matter.
Naive weighted matching failed in a diagnosable way.
Adapter-stratified reporting, source-quality repair, and outcome-blind policy
freezing are concrete research governance wins.
Retrospective signal is weak and underpowered but useful for route finding.
The next phase is justified by a real, measurable problem and a tractable
algorithm/validation agenda.
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-proposal-report-skeleton-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first,
then read docs/research/phase-1-proposal-roadmap-and-claim-planning.md. Use uv
for repo-local Python tooling only if needed for lightweight checks. Follow
AGENTS.md step-level acceptance and commit requirements: after each step, or
after a small group of tightly related steps, commit the changed files with an
appropriately scoped commit.

Main goal: write a proposal-report skeleton, argument map, and evidence/TODO
matrix for Barcarolle Phase 1. Keep predictive validity as the long-term north
star. Keep the short-term proposal claim focused on traction evidence and a
credible path toward that north star. Do not downgrade the project to mere
auditable benchmark construction, but do not claim predictive validity has been
proved.

This runbook is no-paid. Do not run paid ACUT cells. Do not call paid LLMs. Do
not call GPT-5.5-Pro or any external reviewer. Do not rerun completed cells. Do
not change paid outcomes, score tables, selected task IDs, split labels, source
eligibility, task statements, or completed decisions.

Use the academic-paper-writing framing: reader questions, research problem,
main claim, reasons, evidence, warrants, objections, and remaining evidence
needs. Mark unsupported proposal content with Draft or [NEEDS ...] placeholders
instead of silently strengthening the claim.

Do not let GPT-5.5-Pro's review expand short-term scope by default. Classify its
recommendations as: accept now, consider for no-paid proposal evidence, defer,
or reject as short-term scope expansion.

Do not draft M2-M6 runbooks. Mention their intended roles only.
```

## Required Inputs

Read these coordination files first:

```text
AGENTS.md
PROCESS.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
docs/architecture/system-design.md
```

Read these local research plans and reviews:

```text
/Users/chenmohan/Downloads/barcarolle-research-0519.md
/Users/chenmohan/Downloads/barcarolle-research-0526.md
/Users/chenmohan/Downloads/barcarolle-research-0526-1.md
/Users/chenmohan/Downloads/barcarolle-research-0530.md
```

Use these canonical reports when present:

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
experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md
```

Use JSON artifacts only for exact values when needed. Prefer canonical Markdown
reports in the report skeleton unless exact fields or hashes are needed.

## Output Layout

Add or update:

```text
docs/research/
  phase-1-proposal-report-v0.md
  phase-1-proposal-argument-map.md
  phase-1-proposal-evidence-todo-matrix.md
  phase-1-proposal-claim-boundary.md

experiments/phase1_compiler/
  results/
    phase1_proposal_report_skeleton_preflight.json
    phase1_proposal_report_skeleton_evidence_todo_matrix.json
    phase1_proposal_report_skeleton_decision.json
  reports/
    phase1_proposal_report_skeleton_process.md
    phase1_proposal_report_skeleton_decision.md
```

The report skeleton should be useful even before all evidence gaps are filled.
It should contain placeholders instead of invented or overstrengthened claims.

## Step 0: Preflight And Reader Brief

Actions:

1. Record branch, HEAD, date, worktree status, and required-input availability.
2. Read `AGENTS.md`, `PROCESS.md`, and the proposal roadmap planning document.
3. Write a reader-role brief:
   - target readers;
   - what they likely know;
   - what they will object to;
   - what counts as credible evidence;
   - what the proposal must get them to accept.
4. Create or update:

```text
experiments/phase1_compiler/results/phase1_proposal_report_skeleton_preflight.json
experiments/phase1_compiler/reports/phase1_proposal_report_skeleton_process.md
```

Acceptance:

- no paid calls made;
- worktree state recorded;
- missing inputs recorded;
- reader-role brief is written in the process report or argument map.

Commit:

```text
Record proposal report skeleton preflight
```

## Step 1: Write The Argument Map

Actions:

1. Write the research problem:

```text
Public/general SWE benchmarks and scalable task generators do not directly
answer how to predict future work in one target repository.
```

2. Write the north-star question:

```text
Can a Barcarolle-compiled repo-specific benchmark predict future target-repo
ACUT performance?
```

3. Separate:
   - main long-term claim;
   - short-term proposal claim;
   - allowed Phase 1 claims;
   - prohibited claims.
4. Build reasons, evidence, warrants, objections, and responses.
5. Save:

```text
docs/research/phase-1-proposal-argument-map.md
```

Acceptance:

- predictive validity remains the north star;
- short-term claim is stronger than mere engineering artifact hygiene;
- no predictive-validity proof is claimed;
- GPT-5.5-Pro recommendations are classified by priority, not copied as scope.

Commit:

```text
Draft proposal argument map
```

## Step 2: Draft Proposal Report V0

Actions:

Write:

```text
docs/research/phase-1-proposal-report-v0.md
```

Use this structure unless the evidence clearly demands a better one:

1. Problem
2. North Star
3. Barcarolle Thesis
4. Phase 1 Evidence
5. What We Learned
6. Current Candidate Path
7. Validation Path
8. Research Plan
9. Risks And Boundaries
10. Milestones

Required style:

- write as a report draft, not as bullet-only notes;
- keep placeholders explicit;
- use `[NEEDS ...]` for missing tables, figures, numbers, decisions, or
  experiments;
- label tentative sections `Draft`;
- cite local evidence by relative path.

Acceptance:

- report can be read end-to-end as a proposal skeleton;
- every major claim has either evidence, a path to evidence, or a placeholder;
- Phase 1 evidence is not overstated;
- task-supply/generator work is framed as Layer 1 support, not the project core.

Commit:

```text
Draft phase 1 proposal report skeleton
```

## Step 3: Build Evidence/TODO Matrix

Actions:

Create:

```text
docs/research/phase-1-proposal-evidence-todo-matrix.md
experiments/phase1_compiler/results/phase1_proposal_report_skeleton_evidence_todo_matrix.json
```

Each row should include:

```text
claim_or_section
status: supported | traction | diagnostic | draft | needs_evidence | prohibited
current_evidence
missing_evidence
priority: P0 | P1 | P2 | deferred
recommended_milestone
notes
```

Required rows:

- predictive validity north star;
- short-term proposal claim;
- naive weighted failure;
- retrospective signal;
- adapter-stratified reporting;
- source-quality repair;
- candidate policy with labeled fallback;
- boltons fallback issue;
- pseudo-future versus predictive validity boundary;
- baseline strengthening;
- Task Supply v2 relevance;
- paid-validation readiness.

Acceptance:

- matrix drives later milestones;
- missing evidence is routed to M2-M6, not solved ad hoc;
- no prohibited claim is left as a draft claim.

Commit:

```text
Map proposal evidence gaps
```

## Step 4: Claim Boundary And Milestone Sync

Actions:

1. Write:

```text
docs/research/phase-1-proposal-claim-boundary.md
```

2. Confirm M2-M6 remain draft milestones, not new runbooks.
3. Identify which missing evidence must be filled before the proposal can be
   shown to reviewers.
4. Update `PROCESS.md` if the handoff state changes.

Acceptance:

- allowed, draft, and prohibited claims are explicit;
- M1 outputs point to the next milestone but do not draft M2;
- `PROCESS.md` points to M1 closeout if updated.

Commit:

```text
Record proposal claim boundary
```

## Step 5: Closeout

Actions:

1. Write final decision JSON and Markdown:

```text
experiments/phase1_compiler/results/phase1_proposal_report_skeleton_decision.json
experiments/phase1_compiler/reports/phase1_proposal_report_skeleton_decision.md
```

2. Run:

```bash
git diff --check
```

3. Optionally run a lightweight Markdown link/path sanity check if the worker
   has already added one locally. Do not add a large new dependency for this.

Stop with one label:

```text
proposal_report_skeleton_complete
blocked_missing_core_inputs
blocked_claim_boundary_unclear
blocked_evidence_matrix_incomplete
```

Decision must say:

- no paid calls were made;
- predictive validity is not established;
- report skeleton is ready or blocked;
- next recommended milestone is M2 review triage or M3 evidence consolidation.

Commit:

```text
Close proposal report skeleton
```

## Final Report Expectations

The closeout report should answer:

```text
What happened:
  proposal skeleton, argument map, evidence/TODO matrix, and claim boundary
  were written.

Why it matters:
  future work is now pulled by proposal evidence gaps instead of unrelated
  experimental branches.

What action it suggests next:
  execute the highest-priority next milestone from the evidence/TODO matrix.
```

Do not draft the next runbook unless the user explicitly asks after M1 is
interpreted.
