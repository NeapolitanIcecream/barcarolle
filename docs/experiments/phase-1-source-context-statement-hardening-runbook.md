# Phase 1 Source-Context And Statement Hardening Runbook

Status: no-paid implementation runbook, 2026-05-28.

This runbook is for one dedicated Codex CLI session. Its job is to harden the
source context and solver-facing task statements used by the current Phase 1
three-repo pilot package before Barcarolle redesigns the split or buys more
paid replication cells.

```text
Audit and repair source context, task statement quality, leakage risk, and
split-design feature coverage for the attrs/boltons/click Phase 1 task supply.
Produce a clean no-paid decision on whether the task pool is ready for blocked
split redesign.
```

Plain-language summary:

```text
The paid pilot was clean, but some task statements and source context are still
thin. In particular, title-only or commit-message-only context can make a task
look certified while still giving the solver a weak problem description.

This runbook should make that weakness visible and repair what can be repaired
from public, non-leaky context. It should not change the completed paid result,
should not run new paid cells, and should not use outcomes to hand-pick a better
split after the fact.
```

## Execution Boundary

This runbook is no-paid. It must not make new paid LLM or ACUT calls.

Allowed work:

- read committed release, certification, source-context, statement, diagnostic,
  and adapter-reporting artifacts;
- inspect public repository metadata, issues, pull requests, commits, and
  release notes when needed to repair source context;
- write small sanitized public-context summaries, statement packets, review
  records, feature tables, manifests, configs, tests, and reports;
- use completed paid outcomes only as diagnostic labels when explaining the
  already-completed pilot;
- define future split-design feature inputs such as source-quality bucket,
  statement-specificity bucket, context-length bucket, scope bucket, and
  leakage-risk bucket.

Disallowed work:

- running any new paid ACUT solver cell;
- invoking paid LLM APIs for statement generation, statement review, task
  solving, or task scoring;
- changing the frozen three-repo paid pilot task list, split assignment,
  primary design, thresholds, or terminal outcomes;
- changing the completed paid decision label;
- promoting a repaired post-hoc package into a completed paid result;
- using H_future outcomes, adapter outcomes, or failure labels to choose a
  better future split in this runbook;
- implementing the blocked split compiler itself;
- implementing a new external Task Generator or SWE-Bench++/SWE-Smith adapter;
- committing raw prompts, completions, ACUT transcripts, solver workspaces,
  verifier workspaces, raw diffs, raw test patches, target repository clones,
  raw GitHub API responses, secrets, `.venv`, caches, or large raw outputs;
- drafting or creating the next runbook.

If source repair cannot be completed without paid LLM calls or hidden oracle
content, stop that repair item and record a blocker. Do not make the call and
do not expose the oracle.

## Starting Point

The current route is:

```text
Barcarolle remains a repo-specific benchmark compiler.
Mainline compiler design: repo_stratified for now.
Old weighted target-profile design: diagnostic only.
Predictive validity: not established.
Next blocker: source-context/task-statement hardening, then split redesign.
```

The relevant completed decisions are:

```text
phase1_three_repo_paid_validation:
  decision_label: three_repo_paid_pilot_threshold_met
  planned/completed/scoreable cells: 120/120/120
  policy violations: 0
  raw oracle exposure: false
  primary pooled gap: 0.1
  predictive validity established: false

phase1_three_repo_paid_result_diagnostics:
  primary decision: three_repo_paid_diagnostics_adapter_stratification_needed
  bookkeeping error: not supported
  source context thinness: partially supported
  task statement quality: inconclusive
  split imbalance: partially supported
  adapter behavior: supported

phase1_adapter_stratified_reporting:
  primary decision: adapter_reporting_policy_ready_but_source_context_next
  adapter reporting policy ready: true
  recommended next action:
    source_context_hardening_then_split_redesign_before_precision_paid_replication
```

The three-repo paid package used release-eligible counts:

```text
attrs:   31
boltons: 35
click:   30
```

This runbook should not try to prove predictive validity. It should answer a
smaller question:

```text
Are the task statements and source-context quality now clean enough to support
the next no-paid blocked split redesign run?
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-source-context-statement-hardening-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md first. Use uv for
repo-local Python tooling. Follow AGENTS.md step-level acceptance and commit
requirements: after each step, or after each small group of tightly related
steps, commit the changed files with an appropriately scoped commit.

This runbook is no-paid. Do not make paid LLM calls or paid ACUT solver calls.
Do not change the completed three-repo paid pilot decision, task list, split
assignment, primary design, thresholds, or terminal outcomes.

Main goal: audit and harden source context and solver-facing task statements for
the current attrs/boltons/click Phase 1 supply. Use public, non-leaky context
where available. Produce a clear decision on whether the pool is ready for a
later blocked split redesign.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. What action it suggests next.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
Codex/Kilo logs, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, raw target diffs, raw test patches, raw GitHub API
responses, or large raw outputs. Commit only small sanitized configs, tools,
tests, tables, reports, manifests, digests, review records, and decision files.

Do not draft or create the next runbook. Record recommended next action
categories only.
```

## Required Inputs

Use these committed inputs when present:

```text
AGENTS.md
docs/architecture/system-design.md
docs/experiments/phase-1-three-repo-paid-readiness-packaging-runbook.md
docs/experiments/phase-1-three-repo-paid-validation-runbook.md
docs/experiments/phase-1-three-repo-paid-result-diagnostics-runbook.md
docs/experiments/phase-1-adapter-stratified-reporting-runbook.md

experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_decision.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_task_table.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_split_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_source_quality_audit.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_baseline_plan.json

experiments/phase1_compiler/results/phase1_three_repo_paid_validation_decision.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_metrics.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_score_tables_manifest.json

experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_split_balance.json
experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_failure_taxonomy.json
experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_action_matrix.json
experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_decision.json

experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_decision.json
experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_three_repo_summary.json
experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_future_gates.json

experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_attempts.json
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_source_review_queue.json
experiments/phase1_compiler/results/phase1_attrs_source_repair_decision.json

experiments/phase0_headroom/certified_tasks/*_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/*_near_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/*_task_statements.jsonl
experiments/phase0_headroom/certified_tasks/*_review_records.jsonl
experiments/phase0_headroom/certified_tasks/*_source_context*.jsonl
```

Optional local-only inputs, if present and ignored:

```text
experiments/phase1_compiler/tmp/
experiments/phase0_headroom/results/raw/
```

Raw local-only inputs may be read only to assign sanitized labels or hashes. Do
not copy raw text into committed artifacts.

## Quality Policy To Codify

The worker should turn these rules into committed config/report artifacts:

1. `release_eligible` must remain separate from `technical_certified`.
2. A task with only commit-message context is not release-eligible unless a
   separate review record explicitly promotes a sanitized, non-leaky problem
   statement.
3. A task with only a PR or issue title is at least `minor_risk` unless the
   title itself contains a complete problem statement and a review record says
   so.
4. Public issue/PR context may be summarized, but the committed summary must
   avoid target commit hashes, raw reference diff text, hidden tests, direct
   solution instructions, and copied oracle assertions.
5. Diff-assisted statement repair is allowed only when public problem context is
   insufficient and only if the final solver-visible statement is reviewed for
   leakage, ambiguity, and scope.
6. Outcome labels from completed paid runs may explain risk, but must not decide
   whether a candidate is promoted for future primary split design.
7. Future split design should use coarse, auditable features rather than raw
   high-cardinality text:
   - source context type;
   - source quality bucket;
   - statement specificity bucket;
   - context length bucket;
   - editable scope bucket;
   - leakage risk bucket;
   - ambiguity risk bucket;
   - environment/certification risk bucket;
   - repo and coarse task family.
8. Any task excluded from future split-design input must have a clear exclusion
   reason such as `missing_public_problem_context`, `solution_exposure_risk`,
   `ambiguous_scope`, `statement_too_thin`, or `certification_inconsistent`.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_source_context_statement_hardening.yaml
  tools/
    phase1_source_context_statement_hardening.py
  tests/
    test_phase1_source_context_statement_hardening.py
  results/
    phase1_source_context_statement_hardening_preflight.json
    phase1_source_context_statement_hardening_inventory.json
    phase1_source_context_statement_hardening_repair_queue.json
    phase1_source_context_statement_hardening_statement_packets.json
    phase1_source_context_statement_hardening_review_records.json
    phase1_source_context_statement_hardening_overlay.json
    phase1_source_context_statement_hardening_split_feature_table.json
    phase1_source_context_statement_hardening_readiness_gate.json
    phase1_source_context_statement_hardening_decision.json
  reports/
    phase1_source_context_statement_hardening_process.md
    phase1_source_context_statement_hardening_inventory.md
    phase1_source_context_statement_hardening_repair_review.md
    phase1_source_context_statement_hardening_split_features.md
    phase1_source_context_statement_hardening_readiness_gate.md
    phase1_source_context_statement_hardening_decision.md
```

If an exact file does not make sense after reading the current repo, use the
nearest existing local pattern, but keep the same information content.

## Step 0: Preflight And Dirty-Tree Audit

1. Read `AGENTS.md`.
2. Confirm branch, latest commit, and dirty tree:

```bash
git status --short --untracked-files=all
git log --oneline -5
```

3. Classify any existing untracked files. Do not stage unrelated files. The
   known external-review bundle may remain untracked unless the user explicitly
   asks to package or remove it.
4. Confirm no paid calls are needed.
5. Write:

```text
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_preflight.json
experiments/phase1_compiler/reports/phase1_source_context_statement_hardening_process.md
```

Acceptance:

- preflight records branch, latest commit, dirty-tree classification, no-paid
  boundary, and required input availability;
- no unrelated untracked file is staged;
- report says in simple language what is being hardened and why.

Suggested commit:

```text
Record source context hardening preflight
```

## Step 1: Inventory Current Source And Statement Quality

Build a task-level inventory for the current attrs/boltons/click supply used or
eligible for the three-repo pilot.

For each task, record sanitized fields such as:

```text
task_id
repo
source_reservoir
split_label if already assigned
release_eligible before this run
technical_certified
statement_source
source_context_type
source_context_quality
title_only_context
commit_message_only_context
public_issue_or_pr_context
material_leakage_risk
statement_specificity_bucket
statement_length_bucket
editable_scope_bucket
ambiguity_risk_bucket
leakage_risk_bucket
certification_risk_bucket
```

If completed paid outcomes are joined for diagnostic display, put them in a
separate diagnostic section and make clear they were not used for promotion.

Write:

```text
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_inventory.json
experiments/phase1_compiler/reports/phase1_source_context_statement_hardening_inventory.md
```

Acceptance:

- inventory covers the frozen three-repo paid package and any directly relevant
  release-eligible or source-review queue rows;
- counts by repo and source-quality bucket are reported;
- title-only and commit-message-only counts are explicit;
- no hidden oracle material or raw raw API payload is committed.

Suggested commit:

```text
Inventory source context and statement quality
```

## Step 2: Define Repair Queue And Review Rules

Create a repair queue from the inventory. Prioritize tasks that are otherwise
technically certified or release-relevant but have weak source context.

Include these queue labels:

```text
needs_public_context_repair
needs_statement_specificity_review
needs_leakage_review
needs_scope_review
needs_diff_assisted_statement_review
no_repair_needed
not_repairable_without_hidden_oracle
```

The queue should not be outcome-selected. If paid outcome information is useful
for diagnostics, record it separately from repair priority.

Write:

```text
experiments/phase1_compiler/configs/phase1_source_context_statement_hardening.yaml
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_repair_queue.json
```

Acceptance:

- repair queue has deterministic ordering and stable reasons;
- queue policy states that H_future outcomes and adapter pass/fail labels cannot
  promote or demote future primary split candidates;
- the config records thresholds for title-only, commit-message-only, leakage,
  ambiguity, and scope review.

Suggested commit:

```text
Define source context hardening repair queue
```

## Step 3: Repair Public Context And Statement Packets

For queued tasks, search only public, non-hidden context:

```text
public issue text or issue summary
public pull request title/body or discussion summary
public changelog or release-note summary
public commit message summary
public documentation page summary
```

Do not commit raw public API responses. Commit only short sanitized summaries,
source references, stable IDs where safe, and hashes/digests if useful.

Use diff-assisted statement repair only when public context is too thin and the
repair can be reviewed as a problem statement rather than a solution leak. The
committed packet must clearly distinguish:

```text
solver_visible_problem_summary
allowed_public_context_summary
editable_scope_summary
non_solver_visible_review_notes
source_references_or_digests
leakage_review_required
```

Write:

```text
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_statement_packets.json
```

Acceptance:

- packets contain sanitized problem context, not solution instructions;
- every packet records whether it came from public context or diff-assisted
  repair;
- tasks that cannot be repaired without hidden oracle content are explicitly
  blocked rather than guessed.

Suggested commit:

```text
Add sanitized source context repair packets
```

## Step 4: Review Leakage, Ambiguity, And Scope

Review each repaired packet. Produce machine-readable review records with:

```text
task_id
review_verdict
release_eligible_after_overlay
source_quality_after_overlay
statement_specificity_after_overlay
leakage_risk_after_overlay
ambiguity_risk_after_overlay
scope_clarity_after_overlay
review_reasons
```

Allowed verdicts:

```text
promote_release_eligible
keep_release_eligible
keep_diagnostic_only
reject_solution_exposure_risk
reject_ambiguous_scope
reject_missing_public_problem_context
reject_certification_inconsistent
```

Write:

```text
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_review_records.json
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_overlay.json
experiments/phase1_compiler/reports/phase1_source_context_statement_hardening_repair_review.md
```

Acceptance:

- every repaired packet has a review record;
- every promotion has a non-leaky, solver-visible reason;
- every rejection has a concrete reason;
- release-eligible counts before and after overlay are reported by repo.

Suggested commit:

```text
Review source context hardening overlays
```

## Step 5: Build Split-Design Feature Table

Build the sanitized low-dimensional feature table that a later blocked split
runbook can consume. Do not implement the split algorithm here.

Required columns:

```text
task_id
repo
release_eligible_for_split_design
source_context_type_bucket
source_quality_bucket
statement_specificity_bucket
context_length_bucket
editable_scope_bucket
ambiguity_risk_bucket
leakage_risk_bucket
certification_risk_bucket
coarse_task_family
time_bucket if already available
rare_or_unknown_feature_flag
exclusion_reason if not eligible
```

Recommended coarse buckets:

```text
source_context_type_bucket:
  issue_or_pr
  public_docs_or_changelog
  reviewed_diff_assisted
  commit_message_only
  title_only
  unknown

source_quality_bucket:
  clean
  minor_risk
  diagnostic_only
  blocked

statement_specificity_bucket:
  specific
  acceptable
  thin
  missing

editable_scope_bucket:
  single_module
  multi_module
  project_wide
  unknown
```

Write:

```text
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_split_feature_table.json
experiments/phase1_compiler/reports/phase1_source_context_statement_hardening_split_features.md
```

Acceptance:

- no raw task text, raw diff, or hidden oracle content appears in the feature
  table;
- feature buckets are coarse enough for small-N split design;
- rare/unknown coverage is explicit;
- the report says which fields are ready for blocked split design and which are
  still weak.

Suggested commit:

```text
Build source quality split feature table
```

## Step 6: Tests And Consistency Checks

Add focused tests for the new tool and policy.

Minimum test coverage:

- `technical_certified` and `release_eligible` are counted separately;
- commit-message-only tasks are not silently promoted;
- title-only tasks are flagged unless explicitly reviewed;
- outcome fields cannot affect promotion or split-design eligibility;
- overlay counts are deterministic;
- feature buckets contain only allowed values;
- raw sensitive fields are absent from committed JSON outputs.

Run:

```bash
uv run --project experiments/phase1_compiler pytest \
  experiments/phase1_compiler/tests/test_phase1_source_context_statement_hardening.py -q

uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q

git diff --check
```

Acceptance:

- focused tests pass;
- full Phase 1 compiler tests pass, or any failure is clearly unrelated and
  recorded with evidence;
- `git diff --check` passes.

Suggested commit:

```text
Test source context hardening policy
```

## Step 7: Readiness Gate And Decision

Write a decision that answers:

```text
RQ1: How many tasks changed source-quality or release-eligibility status?
RQ2: Which repos still have thin source context or statement risk?
RQ3: Are attrs/boltons/click ready as input to a no-paid blocked split redesign?
RQ4: Did this run make paid LLM or paid ACUT calls?
RQ5: Did this run change any completed paid result?
RQ6: What is the smallest remaining blocker?
RQ7: What action category should the coordinator consider next?
```

Allowed decision labels:

```text
source_context_ready_for_blocked_split_design
source_context_ready_with_minor_risk
needs_more_public_context_repair_before_split_design
blocked_missing_public_context_or_review
blocked_policy_or_hygiene_issue
```

Recommended readiness gate:

```text
ready_for_blocked_split_design is true only if:
  - no repaired task has unresolved solution exposure risk;
  - release-eligible and technical-certified counts are separate;
  - every split-design-eligible task has source_quality_bucket not blocked;
  - title-only and commit-message-only tasks are either reviewed/promoted or
    excluded from split-design eligibility;
  - feature table covers attrs, boltons, and click with deterministic buckets;
  - paid calls made by this run = 0;
  - completed paid decision changed = false.
```

Write:

```text
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_readiness_gate.json
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_decision.json
experiments/phase1_compiler/reports/phase1_source_context_statement_hardening_readiness_gate.md
experiments/phase1_compiler/reports/phase1_source_context_statement_hardening_decision.md
```

Acceptance:

- decision uses one allowed label;
- predictive validity remains `false`;
- completed paid pilot decision remains unchanged;
- no next runbook is drafted or created;
- next action is recorded only as a category, such as
  `blocked_split_redesign`, `additional_public_context_repair`, or
  `third_repo_or_more_repo_supply_screen`.

Suggested commit:

```text
Close source context statement hardening run
```

## Final Hygiene Check

Before stopping:

```bash
git status --short --untracked-files=all
git diff --check
```

Final report must mention:

- commits made during the run;
- tests run and their result;
- whether any paid calls were made;
- whether any completed paid decision changed;
- whether predictive validity is still not established;
- the decision label;
- the smallest remaining blocker;
- the recommended next action category.

Do not create a follow-up runbook unless the user explicitly asks for one after
this run is complete.
