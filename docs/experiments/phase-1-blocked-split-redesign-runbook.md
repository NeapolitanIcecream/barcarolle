# Phase 1 Blocked Split Redesign Runbook

Status: no-paid split-design runbook, 2026-05-29.

This runbook is for one dedicated Codex CLI session. Its job is to redesign the
B_eval/H_future split for the current attrs/boltons/click Phase 1 task pool
using the source-context and statement-quality feature table produced by the
previous hardening run.

```text
Build an outcome-blind, block-randomized, feature-balanced split design for the
attrs/boltons/click pool. Keep click title-only source risk explicit. Decide
whether the resulting split design is ready for a later preregistered paid
validation runbook.
```

Plain-language summary:

```text
The last runbook checked which tasks can be used and what quality risks they
carry. This runbook should decide how to divide those tasks fairly into B_eval
and H_future.

The key rule is simple: choose the split by visible task features only. Do not
use pass/fail outcomes to pick a nicer split. Outcomes may be joined only after
the split is frozen, and only as a retrospective diagnostic.
```

## Execution Boundary

This runbook is no-paid. It must not make new paid LLM or ACUT calls.

Allowed work:

- read committed source-hardening, paid-package, paid-validation, diagnostics,
  adapter-reporting, and local-bakeoff artifacts;
- build a split-design candidate universe from tasks marked
  `release_eligible_for_split_design=true`;
- define coarse blocking features and balance constraints;
- generate many seeded block-randomized candidate splits without loading paid
  outcomes;
- select one or more candidate split designs using feature balance only;
- freeze selected candidate design IDs, seeds, task IDs, split labels, and
  imbalance diagnostics;
- after freeze, join existing completed paid outcomes only for retrospective
  diagnostics, and only where such outcomes already exist;
- project future paid cost from committed usage/cost summaries without making
  calls;
- write small sanitized configs, tools, tests, JSON/CSV outputs, reports, and
  decision files.

Disallowed work:

- running any new paid ACUT solver cell;
- invoking paid LLM APIs for task solving, statement generation, statement
  review, split choice, or scoring;
- changing the completed three-repo paid pilot decision, task list, split
  assignment, primary design, thresholds, or terminal outcomes;
- changing source-context release eligibility in this runbook;
- repairing task statements in this runbook;
- using B_eval/H_future pass rates, adapter pass/fail labels, failure labels, or
  any paid outcome field to select, rank, or tune the new split;
- promoting retrospective diagnostics to preregistered paid evidence;
- implementing a new external Task Generator or SWE-Bench++/SWE-Smith adapter;
- committing raw prompts, completions, ACUT transcripts, solver workspaces,
  verifier workspaces, raw diffs, raw test patches, target repository clones,
  raw public API responses, secrets, `.venv`, caches, or large raw outputs;
- drafting or creating the next runbook.

If the worker cannot prove that split selection was outcome-blind, stop and
write a blocker. Do not try to repair the evidence after looking at outcomes.

## Starting Point

The previous run ended with:

```text
decision_label: source_context_ready_with_minor_risk
ready_for_blocked_split_design: true
paid calls made: 0
completed paid result changed: false
predictive validity established: false
recommended next action category: blocked_split_redesign
smallest remaining blocker: click_title_only_minor_risk
```

The split-design feature table has:

```text
feature rows: 153
eligible for split design: 95
eligible counts:
  attrs:   30
  boltons: 35
  click:   30
```

Important source-quality fact:

```text
attrs eligible tasks:   clean issue/PR context
boltons eligible tasks: clean issue/PR context
click eligible tasks:   title-only, minor-risk context
```

This means click can participate in the next design, but click is not a clean
source-quality repo. The new split must keep that caveat visible.

The completed three-repo paid pilot remains:

```text
decision_label: three_repo_paid_pilot_threshold_met
primary_design: repo_stratified
planned/completed/scoreable cells: 120/120/120
primary pooled gap: 0.1
predictive_validity_established: false
```

This runbook must not rewrite that result.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-blocked-split-redesign-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md first. Use uv for
repo-local Python tooling. Follow AGENTS.md step-level acceptance and commit
requirements: after each step, or after each small group of tightly related
steps, commit the changed files with an appropriately scoped commit.

This runbook is no-paid. Do not make paid LLM calls or paid ACUT solver calls.
Do not change the completed three-repo paid pilot decision, task list, split
assignment, primary design, thresholds, or terminal outcomes. Do not repair task
statements or source eligibility in this runbook.

Main goal: use the source-context hardening feature table to build an
outcome-blind, block-randomized, feature-balanced B_eval/H_future split design
for attrs, boltons, and click. Keep click's title-only minor-risk source context
visible in every report and gate.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. What action it suggests next.

Selection must be outcome-blind. Do not load or join completed paid outcomes
until after the candidate split design is frozen and written. If you later join
outcomes for retrospective diagnostics, state clearly that those diagnostics did
not choose the split.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
Codex/Kilo logs, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, raw target diffs, raw test patches, raw public API
responses, or large raw outputs. Commit only small sanitized configs, tools,
tests, tables, reports, manifests, digests, and decision files.

Do not draft or create the next runbook. Record recommended next action
categories only.
```

## Required Inputs

Use these committed inputs:

```text
AGENTS.md
docs/architecture/system-design.md
docs/experiments/phase-1-source-context-statement-hardening-runbook.md
docs/experiments/phase-1-local-algorithm-bakeoff-runbook.md
docs/experiments/phase-1-three-repo-paid-readiness-packaging-runbook.md
docs/experiments/phase-1-three-repo-paid-validation-runbook.md
docs/experiments/phase-1-three-repo-paid-result-diagnostics-runbook.md
docs/experiments/phase-1-adapter-stratified-reporting-runbook.md

experiments/phase1_compiler/results/phase1_source_context_statement_hardening_decision.json
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_readiness_gate.json
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_split_feature_table.json
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_overlay.json

experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_decision.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_task_table.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_split_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_baseline_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_power_cost_plan.json

experiments/phase1_compiler/results/phase1_three_repo_paid_validation_decision.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_metrics.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_score_tables_manifest.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_cost_reconciliation.json

experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_result_cube.json
experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_split_balance.json
experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_uncertainty.json
experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_action_matrix.json

experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_decision.json
experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_three_repo_summary.json
experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_future_gates.json

experiments/phase0_headroom/results/phase1_three_repo_paid_validation_*_score_table.csv
experiments/phase0_headroom/results/phase1_three_repo_paid_validation_*_cost_summary.json
experiments/phase0_headroom/results/workspace_usage_ledger.jsonl
```

Do not require ignored raw artifacts for this runbook.

## Split Design Rules

The worker should codify these rules in config, code, tests, and reports.

1. Candidate universe:
   - include only rows where `release_eligible_for_split_design=true`;
   - keep `repo` as a hard stratum;
   - do not silently include blocked, diagnostic-only, or missing-public-context
     rows.
2. Primary budgets to evaluate locally:
   - `same_budget_20_per_repo`: 20 tasks per repo, 10 B_eval and 10 H_future;
   - `expanded_30_per_repo`: 30 tasks per repo, 15 B_eval and 15 H_future, if
     feasible without hiding click minor risk.
3. Blocking should be within repo first. Cross-repo balancing is useful for
   reporting, but attrs, boltons, and click have different source-quality
   shapes, so a cross-repo average must not hide click.
4. Use only coarse visible features:
   - source context type bucket;
   - source quality bucket;
   - statement specificity bucket;
   - context length bucket;
   - editable scope bucket;
   - ambiguity risk bucket;
   - leakage risk bucket;
   - certification risk bucket;
   - coarse task family;
   - time bucket;
   - rare or unknown feature flag.
5. Do not use:
   - pass/fail outcomes;
   - adapter outcomes;
   - hidden verifier labels;
   - raw solver traces;
   - raw prompts or completions;
   - target reference diffs;
   - post-hoc manual preferences after looking at outcomes.
6. Build matched blocks when possible:
   - default block size is 2 tasks, one assigned to B_eval and one to H_future;
   - block within repo;
   - prefer same or nearest source quality, source context type, task family,
     time bucket, and editable scope;
   - when perfect matches are impossible, record the nearest-match reason.
7. Use seeded randomization:
   - generate many candidate seeds;
   - score each seed by feature imbalance only;
   - select by the preregistered feature-imbalance objective;
   - record candidate seeds and the selected seed.
8. Freeze before diagnostics:
   - write the selected split assignment and selection audit before loading paid
     outcomes;
   - only after freeze may the worker join completed paid outcomes for
     retrospective diagnostics.

## Feature Imbalance Objective

Implement a simple, auditable objective before considering any retrospective
outcome diagnostics.

Recommended components:

```text
hard failures:
  repo B/H count mismatch
  duplicate task IDs
  non-eligible task selected
  blocked source-quality task selected
  missing selected seed or unstable deterministic order

soft penalties:
  per-repo task-family count difference
  per-repo time-bucket count difference
  per-repo editable-scope count difference
  per-repo statement-specificity count difference
  per-repo rare/unknown flag count difference
  cross-repo source-quality caveat not surfaced
```

Recommended gate thresholds:

```text
repo_count_balance: exact
split_count_per_repo: exact
source_quality_balance_within_repo: exact or constant-by-repo
source_context_type_balance_within_repo: exact or constant-by-repo
rare_or_unknown_abs_diff_per_repo: <= 1
editable_scope_abs_diff_per_repo: <= 2
time_bucket_abs_diff_per_repo: <= 2
coarse_family_abs_diff_per_repo: <= 2, unless support is too sparse
blocked_source_quality_selected: 0
outcome_fields_loaded_before_freeze: false
```

If a threshold is infeasible, do not silently relax it. Record which supply
constraint caused the relaxation and whether the final design remains usable.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_blocked_split_redesign.yaml
  tools/
    phase1_blocked_split_redesign.py
  tests/
    test_phase1_blocked_split_redesign.py
  results/
    phase1_blocked_split_redesign_preflight.json
    phase1_blocked_split_redesign_candidate_universe.json
    phase1_blocked_split_redesign_block_schema.json
    phase1_blocked_split_redesign_candidate_splits.json
    phase1_blocked_split_redesign_selected_split.json
    phase1_blocked_split_redesign_selection_audit.json
    phase1_blocked_split_redesign_imbalance_diagnostics.json
    phase1_blocked_split_redesign_retrospective_outcome_diagnostics.json
    phase1_blocked_split_redesign_cost_power_projection.json
    phase1_blocked_split_redesign_readiness_gate.json
    phase1_blocked_split_redesign_decision.json
  reports/
    phase1_blocked_split_redesign_process.md
    phase1_blocked_split_redesign_candidate_universe.md
    phase1_blocked_split_redesign_block_schema.md
    phase1_blocked_split_redesign_candidate_splits.md
    phase1_blocked_split_redesign_imbalance_diagnostics.md
    phase1_blocked_split_redesign_retrospective_outcome_diagnostics.md
    phase1_blocked_split_redesign_cost_power_projection.md
    phase1_blocked_split_redesign_readiness_gate.md
    phase1_blocked_split_redesign_decision.md
```

Optional small CSV outputs may be added if useful:

```text
experiments/phase1_compiler/results/phase1_blocked_split_redesign_*.csv
```

## Step 0: Preflight And Dirty-Tree Audit

1. Read `AGENTS.md`.
2. Confirm branch, latest commit, and dirty tree:

```bash
git status --short --untracked-files=all
git log --oneline -5
```

3. Classify untracked files. The known external-review bundle may remain
   untracked unless the user explicitly asks to package or remove it.
4. Confirm no paid calls are needed.
5. Confirm the source hardening decision is
   `source_context_ready_with_minor_risk`.
6. Write:

```text
experiments/phase1_compiler/results/phase1_blocked_split_redesign_preflight.json
experiments/phase1_compiler/reports/phase1_blocked_split_redesign_process.md
```

Acceptance:

- preflight records branch, latest commit, dirty-tree classification, no-paid
  boundary, and required input availability;
- report states that click minor-risk source context must remain visible;
- no unrelated untracked file is staged.

Suggested commit:

```text
Record blocked split redesign preflight
```

## Step 1: Build Candidate Universe

Load the source-hardening split feature table and build the candidate universe.

Required checks:

```text
all selected-universe rows have release_eligible_for_split_design=true
no blocked or diagnostic-only rows in candidate universe
repo counts are attrs=30, boltons=35, click=30 unless source artifacts changed
click source_quality_bucket remains minor_risk for all eligible click tasks
raw_text_fields_committed=false
```

Write:

```text
experiments/phase1_compiler/results/phase1_blocked_split_redesign_candidate_universe.json
experiments/phase1_compiler/reports/phase1_blocked_split_redesign_candidate_universe.md
```

Acceptance:

- universe counts are reported by repo, source quality, context type, time
  bucket, task family, scope, and rare/unknown flag;
- excluded rows are counted by exclusion reason;
- click title-only minor-risk caveat is explicit;
- no outcomes are loaded in this step.

Suggested commit:

```text
Build blocked split candidate universe
```

## Step 2: Define Block Schema And Balance Constraints

Create the split-design config and block schema.

The config should include:

```text
run_id
candidate_universe_path
budgets_to_evaluate
random_seed_family
candidate_seed_count
hard_constraints
soft_penalty_weights
allowed_feature_buckets
outcome_blind_selection_required
click_minor_risk_caveat_required
```

Write:

```text
experiments/phase1_compiler/configs/phase1_blocked_split_redesign.yaml
experiments/phase1_compiler/results/phase1_blocked_split_redesign_block_schema.json
experiments/phase1_compiler/reports/phase1_blocked_split_redesign_block_schema.md
```

Acceptance:

- hard constraints and soft penalties are written before candidate outcomes are
  loaded;
- selection objective mentions only visible features;
- click source-quality caveat is a required reporting field;
- the block schema is deterministic and testable.

Suggested commit:

```text
Define blocked split schema
```

## Step 3: Generate Outcome-Blind Candidate Splits

Generate candidate splits for the configured budgets.

Minimum candidates:

```text
same_budget_20_per_repo:
  at least 100 deterministic candidate seeds, if feasible

expanded_30_per_repo:
  at least 100 deterministic candidate seeds, if feasible
```

For each candidate, record:

```text
design_id
budget_id
seed
selected_task_ids
block assignments
B_eval task IDs
H_future task IDs
hard constraint failures
feature imbalance score
per-feature imbalance summary
selection_inputs_used
outcome_fields_used_for_selection=false
```

Write:

```text
experiments/phase1_compiler/results/phase1_blocked_split_redesign_candidate_splits.json
experiments/phase1_compiler/reports/phase1_blocked_split_redesign_candidate_splits.md
```

Acceptance:

- no candidate split includes duplicate task IDs;
- no candidate split includes a blocked or non-eligible row;
- B_eval/H_future counts are exact for each repo;
- every candidate records `outcome_fields_used_for_selection=false`;
- if a budget is infeasible, the report gives the exact reason.

Suggested commit:

```text
Generate outcome blind blocked split candidates
```

## Step 4: Select And Freeze Split Design

Select the best candidate by the feature-imbalance objective only.

The worker should normally freeze:

```text
primary_candidate: best feasible same_budget_20_per_repo
secondary_candidate: best feasible expanded_30_per_repo, if feasible
```

Do not use retrospective outcomes to choose between candidates. If expanded
budget is cheaper or more expensive only in future paid cost terms, record that
in the cost projection step, not as an outcome-based selection.

Write:

```text
experiments/phase1_compiler/results/phase1_blocked_split_redesign_selected_split.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_selection_audit.json
```

Acceptance:

- selected split is written before retrospective outcome diagnostics;
- selection audit lists all loaded input paths and confirms no paid outcome file
  was loaded before freeze;
- selected candidate has stable design ID, seed, task IDs, block IDs, and split
  labels;
- completed paid pilot files remain unchanged.

Suggested commit:

```text
Freeze blocked split redesign candidate
```

## Step 5: Feature Imbalance Diagnostics

Compute readable imbalance diagnostics for the frozen candidate or candidates.

Required summaries:

```text
per repo B/H counts
per repo source quality B/H counts
per repo source context type B/H counts
per repo statement specificity B/H counts
per repo task family B/H counts
per repo time bucket B/H counts
per repo editable scope B/H counts
rare/unknown B/H counts
hard constraint pass/fail table
soft imbalance score table
```

Write:

```text
experiments/phase1_compiler/results/phase1_blocked_split_redesign_imbalance_diagnostics.json
experiments/phase1_compiler/reports/phase1_blocked_split_redesign_imbalance_diagnostics.md
```

Acceptance:

- report explains in simple language whether B_eval and H_future look fairer
  than the previous split on visible features;
- click title-only minor-risk remains visible;
- any threshold relaxation is named and justified;
- no paid outcomes are needed for this step.

Suggested commit:

```text
Report blocked split feature balance
```

## Step 6: Retrospective Outcome Diagnostics After Freeze

Only after the split is frozen, join existing completed paid outcomes where
available.

This step is diagnostic only. It must say:

```text
retrospective outcomes did not choose the split
missing outcome cells are not imputed
adapter-level diagnostics remain separate
pooled diagnostics are secondary
predictive validity remains false
```

Compute, where outcome coverage allows:

```text
overlap with completed paid score tables
outcome coverage by budget/design/repo/split/adapter
adapter-level B_eval/H_future pass rates
adapter-level gaps
paired disagreement, if both adapters exist
comparison with previous frozen paid split, clearly marked retrospective
```

Write:

```text
experiments/phase1_compiler/results/phase1_blocked_split_redesign_retrospective_outcome_diagnostics.json
experiments/phase1_compiler/reports/phase1_blocked_split_redesign_retrospective_outcome_diagnostics.md
```

Acceptance:

- diagnostics are skipped or marked incomplete when outcome coverage is missing;
- no missing outcomes are inferred;
- no selected split is changed after this step;
- report states that this is not paid evidence for the new design.

Suggested commit:

```text
Record retrospective blocked split diagnostics
```

## Step 7: Cost, Power, And Paid-Readiness Projection

Project the cost and precision tradeoff for any future paid validation runbook.
Do not make calls.

Use committed prior cost summaries and usage ledger to estimate:

```text
tasks per repo
total tasks
adapters
scoreable cell count
token-estimated cost range
cost per cell by adapter
provider-billed exact cost availability
estimated latency by adapter
expected precision caveat
```

Report separately for:

```text
same_budget_20_per_repo
expanded_30_per_repo
```

Write:

```text
experiments/phase1_compiler/results/phase1_blocked_split_redesign_cost_power_projection.json
experiments/phase1_compiler/reports/phase1_blocked_split_redesign_cost_power_projection.md
```

Acceptance:

- cost is labeled token-estimated unless provider-billed cost is available;
- adapter costs are shown separately before any pooled cost;
- projection does not claim paid readiness by itself;
- report states whether expanded budget is worth considering or should remain
  secondary.

Suggested commit:

```text
Project blocked split paid validation cost
```

## Step 8: Tests And Consistency Checks

Add focused tests for the split tool and policy.

Minimum test coverage:

- candidate universe excludes non-eligible rows;
- blocked and diagnostic-only rows cannot be selected;
- B_eval/H_future counts are exact by repo;
- selected split has no duplicate task IDs;
- outcome fields cannot be used before freeze;
- feature imbalance objective ignores pass/fail columns;
- click minor-risk caveat is required when click is included;
- selection audit fails if an outcome input is loaded before freeze;
- retrospective diagnostics cannot mutate the selected split;
- cost projection labels token-estimated vs provider-billed status.

Run:

```bash
uv run --project experiments/phase1_compiler pytest \
  experiments/phase1_compiler/tests/test_phase1_blocked_split_redesign.py -q

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
Test blocked split redesign policy
```

## Step 9: Readiness Gate And Decision

Write the readiness gate and final decision.

Research questions:

```text
RQ1: Did the selected split use only visible pre-outcome features?
RQ2: Which budget/design was selected as primary and why?
RQ3: Are B_eval and H_future balanced enough on source quality, task family,
     time bucket, scope, and rare/unknown flags?
RQ4: How does click title-only minor risk affect the claim boundary?
RQ5: What did retrospective outcome diagnostics show, if coverage exists?
RQ6: What would a future paid run cost, by adapter and budget?
RQ7: Did this run make paid calls or change completed paid decisions?
RQ8: What is the smallest remaining blocker?
RQ9: What action category should the coordinator consider next?
```

Allowed decision labels:

```text
blocked_split_ready_for_preregistration
blocked_split_ready_with_click_minor_risk
blocked_split_needs_more_source_repair
blocked_split_needs_third_repo_replacement
blocked_split_blocked_by_selection_audit
blocked_split_blocked_by_feature_imbalance
blocked_split_blocked_by_insufficient_supply
```

Readiness is true only if:

```text
candidate universe uses source-hardening eligible rows only
selection audit proves outcome-blind selection
primary selected split has exact repo and split counts
blocked/diagnostic-only tasks selected = 0
feature imbalance gates pass or every relaxation is explicit and acceptable
click title-only minor risk is visible in reports and decision
retrospective outcomes, if joined, did not change the selected split
paid calls made by this run = 0
completed paid decision changed = false
predictive validity established = false
tests and git diff --check passed
```

Write:

```text
experiments/phase1_compiler/results/phase1_blocked_split_redesign_readiness_gate.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_decision.json
experiments/phase1_compiler/reports/phase1_blocked_split_redesign_readiness_gate.md
experiments/phase1_compiler/reports/phase1_blocked_split_redesign_decision.md
```

Acceptance:

- decision uses one allowed label;
- report states what the selected split is, what risk remains, and what the
  coordinator should consider next;
- predictive validity remains `false`;
- completed paid pilot decision remains unchanged;
- no next runbook is drafted or created.

Suggested commit:

```text
Close blocked split redesign run
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
- selected split design ID and budget;
- click minor-risk status;
- decision label;
- smallest remaining blocker;
- recommended next action category.

Do not create a follow-up runbook unless the user explicitly asks for one after
this run is complete.
