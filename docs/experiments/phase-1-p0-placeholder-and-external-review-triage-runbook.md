# Phase 1 P0 Placeholder And External Review Triage Runbook

Status: no-paid proposal triage runbook, 2026-06-01.

This runbook is for one dedicated Codex CLI session. Its job is to triage the
active proposal report's P0 placeholders together with GPT-5.5-Pro review
findings and the 0526-1 task-supply plan. It should decide what must be filled
before reviewer readiness, what routes to M3 or M4, what is only report
revision work, what is deferred, and what is rejected as short-term scope
expansion.

```text
Create a clear routing table from proposal-report gaps to later milestones.
Do not fill the gaps yet.
```

Plain-language summary:

```text
Proposal report v1 is now the active final-shape draft. M2 should keep the
remaining work from drifting: every P0 placeholder and important external
review recommendation should be assigned to a route, priority, owner category,
and claim impact before any evidence package or validation-protocol work
starts.
```

## Execution Boundary

This runbook is no-paid triage and documentation work. It must not make paid
ACUT solver calls, paid LLM calls, external GPT-5.5-Pro calls, or new external
review calls.

Allowed work:

- read local proposal documents, roadmap, claim boundary, evidence matrix,
  completed runbooks, committed reports, and local review files;
- inventory P0 and P1 placeholders from
  `docs/research/phase-1-proposal-report-v1.md`;
- inventory relevant GPT-5.5-Pro 0530 recommendations and 0526-1 task-supply
  guidance from local files;
- create a triage document and machine-readable decision artifact;
- update roadmap, claim boundary, evidence/TODO matrix, or `PROCESS.md` only
  to align with the triage;
- update the proposal report appendix only if route labels are needed for
  clarity;
- run lightweight text checks, JSON validation, and `git diff --check`.

Disallowed work:

- running paid ACUT cells;
- running paid LLM calls;
- calling GPT-5.5-Pro or another external reviewer;
- browsing or public-literature hunting to fill citation placeholders;
- filling baseline results, ablations, power notes, figures, pseudocode, or
  release schema placeholders;
- drafting M3, M4, M5, or M6 runbooks;
- creating a new roadmap file;
- moving roadmap duties out of
  `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`;
- changing paid outcomes, score tables, selected task IDs, split labels, source
  eligibility artifacts, task statements, or completed decisions;
- claiming predictive validity is established;
- authorizing paid validation;
- committing raw prompts, raw completions, raw ACUT transcripts, solver
  workspaces, verifier workspaces, target repo clones, raw public API
  responses, raw target diffs, raw test patches, `.venv`, caches, secrets, or
  large raw outputs.

If a placeholder looks fillable during M2, still route it to a later milestone
unless it is purely a wording or claim-boundary alignment fix. M2 is a triage
gate, not an evidence-production milestone.

## Starting Point

The active proposal report is:

```text
docs/research/phase-1-proposal-report-v1.md
```

The active roadmap has already been realigned around v1 placeholders:

```text
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
```

M2 should convert this state:

```text
many P0 placeholders and several external review recommendations
```

into this state:

```text
each placeholder and recommendation has a route, priority, rationale, and
claim-boundary impact.
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-p0-placeholder-and-external-review-triage-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first.
Then read docs/research/phase-1-proposal-roadmap-and-claim-planning.md,
docs/research/phase-1-proposal-report-v1.md,
docs/research/phase-1-proposal-claim-boundary.md, and
docs/research/phase-1-proposal-evidence-todo-matrix.md. Follow AGENTS.md
step-level acceptance and commit requirements.

Main goal: triage every proposal-report v1 P0 placeholder and relevant external
review recommendation into a route: M3 evidence package, M4 validation/candidate
policy hardening, M5 reviewer-ready report revision, M6 approval artifact,
defer, or reject as short-term scope expansion. Do not fill the placeholders.

Read the local review files /Users/chenmohan/Downloads/barcarolle-research-0530.md
and /Users/chenmohan/Downloads/barcarolle-research-0526-1.md. Treat GPT-5.5-Pro
as strategy input, not controlling scope. Keep predictive validity as the north
star, but do not claim it is established.

Do not run paid ACUT cells. Do not call paid LLMs. Do not call GPT-5.5-Pro or
any external reviewer. Do not browse for citations. Do not rerun completed
cells. Do not change paid outcomes, score tables, selected task IDs, split
labels, source eligibility, task statements, or completed decisions. Do not
draft M3, M4, M5, or M6 runbooks.
```

## Required Inputs

Read these coordination files first:

```text
AGENTS.md
PROCESS.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
docs/research/phase-1-proposal-report-v1.md
docs/research/phase-1-proposal-claim-boundary.md
docs/research/phase-1-proposal-evidence-todo-matrix.md
docs/research/phase-1-proposal-argument-map.md
experiments/phase1_compiler/reports/phase1_proposal_report_final_shape_rewrite_decision.md
```

Read these local research plans and reviews:

```text
/Users/chenmohan/Downloads/barcarolle-research-0519.md
/Users/chenmohan/Downloads/barcarolle-research-0526.md
/Users/chenmohan/Downloads/barcarolle-research-0526-1.md
/Users/chenmohan/Downloads/barcarolle-research-0530.md
```

Use these reports for context only when needed to understand a placeholder or
review finding:

```text
experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md
experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md
experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md
experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_success_criteria.md
experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_validation_protocol.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md
```

## Output Layout

Add:

```text
docs/research/phase-1-proposal-p0-placeholder-triage.md
```

Optionally update:

```text
docs/research/phase-1-proposal-report-v1.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
docs/research/phase-1-proposal-claim-boundary.md
docs/research/phase-1-proposal-evidence-todo-matrix.md
PROCESS.md
```

Add closeout artifacts:

```text
experiments/phase1_compiler/
  results/
    phase1_p0_placeholder_external_review_triage_preflight.json
    phase1_p0_placeholder_external_review_triage_decision.json
  reports/
    phase1_p0_placeholder_external_review_triage_process.md
    phase1_p0_placeholder_external_review_triage_decision.md
```

Do not add M3, M4, M5, or M6 runbooks.

## Triage Categories

Use these route values consistently:

```text
M2_boundary_or_wording
M3_evidence_package
M4_validation_or_candidate_hardening
M5_reviewer_ready_report_revision
M6_approval_artifact
defer_post_proposal
reject_short_term_scope_expansion
already_satisfied_or_appendix_only
needs_user_decision
```

Use these priority values:

```text
P0_blocker
P1_before_final_publication_or_broader_review
P2_deferred
```

Use these recommendation classes for external review items:

```text
accept_now
route_to_M3
route_to_M4
route_to_M5
defer
reject_scope_expansion
needs_user_decision
```

## Required Triage Document Shape

`docs/research/phase-1-proposal-p0-placeholder-triage.md` should include:

```text
1. Executive Decision
2. Scope And Non-Scope
3. P0 Placeholder Routing Table
4. P1 Placeholder Routing Table
5. External Review Recommendation Triage
6. 0526-1 Task-Supply Guidance Triage
7. Claim Boundary Updates Needed
8. Milestone Routing Summary
9. No-Paid / No-Validation Boundary
10. Open User Decisions
```

Every P0 placeholder from proposal report v1 Appendix D must appear exactly
once in the P0 routing table, unless it is merged with another placeholder and
the merge is explicitly explained.

For each row, include at least:

```text
placeholder or recommendation
source
route
priority
claim function
why this route
expected output
whether it can affect paid-validation readiness
```

## Step 0: Preflight And Inventory

Actions:

1. Record branch, HEAD, date, worktree status, and required-input availability.
2. Confirm the active report is
   `docs/research/phase-1-proposal-report-v1.md`.
3. Extract or manually inventory all P0 and P1 placeholders from Appendix D.
4. Record the inventory in:

```text
experiments/phase1_compiler/results/phase1_p0_placeholder_external_review_triage_preflight.json
experiments/phase1_compiler/reports/phase1_p0_placeholder_external_review_triage_process.md
```

Acceptance:

- no paid calls made;
- no external reviewer calls made;
- all P0 placeholders from v1 Appendix D are inventoried;
- missing inputs, if any, are recorded;
- no later runbook is drafted.

Commit:

```text
Record M2 placeholder triage preflight
```

## Step 1: Build The P0/P1 Placeholder Routing Table

Actions:

1. Create `docs/research/phase-1-proposal-p0-placeholder-triage.md`.
2. Route every P0 placeholder to exactly one primary route.
3. Route P1 placeholders separately.
4. For placeholders that could belong to both M3 and M4, pick the route that
   should own the first concrete output and note the secondary dependency.
5. Mark any item that would require user approval or external-state change as
   `needs_user_decision`.

Acceptance:

- every v1 P0 placeholder appears exactly once or is explicitly merged;
- each row has route, priority, claim function, rationale, and expected output;
- evidence-producing work is not performed during triage;
- paid validation remains unauthorized.

Commit:

```text
Draft P0 placeholder routing table
```

## Step 2: Triage External Review And Task-Supply Guidance

Actions:

1. Read `/Users/chenmohan/Downloads/barcarolle-research-0530.md`.
2. Extract only findings that affect the proposal report, validation protocol,
   candidate policy, baseline suite, fallback handling, adapter claim, or paid
   readiness.
3. Classify each finding with the external review recommendation classes.
4. Read `/Users/chenmohan/Downloads/barcarolle-research-0526-1.md`.
5. Classify task-supply guidance as:
   - needed for proposal P0;
   - relevant but M3/M4 scoped;
   - deferred infrastructure;
   - rejected as short-term scope expansion.

Acceptance:

- GPT-5.5-Pro advice is classified as input, not controlling scope;
- task-supply guidance stays inside the source-adapter/supply layer;
- no broad task-generator expansion is promoted to core proposal scope;
- paid validation remains unauthorized.

Commit:

```text
Triage external review and task-supply guidance
```

## Step 3: Align Claim Boundary And Milestone Map

Actions:

1. Update `docs/research/phase-1-proposal-claim-boundary.md` only if M2 changes
   a guardrail, draft claim, prohibited claim, or milestone role.
2. Update `docs/research/phase-1-proposal-evidence-todo-matrix.md` only if M2
   changes the recommended milestone route for a claim.
3. Update `docs/research/phase-1-proposal-roadmap-and-claim-planning.md` only
   if M2 changes the M3/M4/M5/M6 scope.
4. Update the v1 report appendix only if route labels or placeholder wording
   need to be synchronized.
5. Update `PROCESS.md` if the active handoff state changes.

Acceptance:

- roadmap ownership remains in
  `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`;
- no new roadmap file exists;
- supporting docs agree about which milestone owns each major P0 group;
- no later runbook is drafted.

Commit:

```text
Align M2 triage supporting documents
```

## Step 4: Triage Quality Gate

Actions:

1. Verify completeness:

```bash
rg -n "NEEDS " docs/research/phase-1-proposal-report-v1.md
rg -n "P0_blocker|M3_evidence_package|M4_validation_or_candidate_hardening|M5_reviewer_ready_report_revision|defer_post_proposal|reject_short_term_scope_expansion|needs_user_decision" docs/research/phase-1-proposal-p0-placeholder-triage.md
```

2. Check that no prohibited claim has been introduced:

```bash
rg -n "proves predictive validity|established predictive validity|authorizes paid|validated predictive benchmark compiler|model-only superiority" docs/research/phase-1-proposal-p0-placeholder-triage.md docs/research/phase-1-proposal-claim-boundary.md docs/research/phase-1-proposal-evidence-todo-matrix.md docs/research/phase-1-proposal-roadmap-and-claim-planning.md
```

3. Run:

```bash
python3 -m json.tool experiments/phase1_compiler/results/phase1_p0_placeholder_external_review_triage_preflight.json
git diff --check
```

Use judgment for `rg` checks. If a prohibited phrase appears only as a
prohibited-claim example, record that in the process report.

Acceptance:

- all P0 placeholders are routed;
- all relevant review recommendations are classified;
- no paid validation is authorized;
- `git diff --check` passes;
- JSON preflight validates.

Commit:

```text
Audit M2 triage completeness
```

## Step 5: Closeout

Actions:

1. Write:

```text
experiments/phase1_compiler/reports/phase1_p0_placeholder_external_review_triage_decision.md
experiments/phase1_compiler/results/phase1_p0_placeholder_external_review_triage_decision.json
```

2. Validate JSON:

```bash
python3 -m json.tool experiments/phase1_compiler/results/phase1_p0_placeholder_external_review_triage_decision.json
```

3. Stop with one label:

```text
p0_placeholder_external_review_triage_complete
blocked_p0_inventory_incomplete
blocked_external_review_inputs_missing
blocked_claim_boundary_unclear
blocked_milestone_routes_conflict
```

Decision must say:

- no paid calls were made;
- no external reviewer calls were made;
- predictive validity remains unestablished;
- paid validation remains unauthorized;
- whether every P0 placeholder has a route;
- which route owns the next work category;
- whether user decisions are needed before writing the next runbook.

Commit:

```text
Close M2 placeholder and review triage
```

## Final Report Expectations

The closeout should say:

```text
What happened:
  proposal report v1 placeholders and external review recommendations were
  routed into concrete milestone categories.

Why it matters:
  remaining pre-proposal work now has an explicit priority map, so M3 and M4
  can be written narrowly instead of absorbing every useful-but-noncritical
  idea.

What action it suggests next:
  write the next runbook only for the highest-priority route identified by M2,
  unless user decisions are needed first.
```

Do not draft the next runbook unless the user explicitly asks after reviewing
the M2 result.
