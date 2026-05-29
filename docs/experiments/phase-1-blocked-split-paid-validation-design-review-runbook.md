# Phase 1 Blocked Split Paid Validation Design Review Runbook

Status: no-paid design-review runbook, 2026-05-29.

This runbook is for one dedicated Codex CLI session. Its job is to decide how
Barcarolle should validate the blocked split redesign in the current exploratory
Phase 1 setting.

```text
Review whether the blocked split should be validated by reusing existing paid
outcomes, supplementing only missing cells, fully rerunning the selected split,
or stopping for more source repair. Keep the result clearly labeled as
exploratory unless a later runbook executes a fresh frozen protocol.
```

Plain-language summary:

```text
The blocked split was designed after earlier paid results existed. That is
acceptable for Phase 1 exploration, but it changes what we can claim.

This runbook should not pretend the design was a formal preregistered study.
Instead, it should choose an honest validation protocol: how much old paid data
can be reused, what missing cells would need to be run, what it would cost, and
what claim boundary would remain.
```

## Execution Boundary

This runbook is no-paid. It must not make new paid LLM or ACUT calls.

Allowed work:

- read committed blocked split, source-hardening, paid-validation,
  adapter-reporting, cost, and usage artifacts;
- classify the blocked split validation mode as exploratory, preregistration-like
  design freeze, missing-cell supplement, full rerun, or blocked;
- compute exact overlap between the selected blocked split and completed paid
  score tables;
- compute known cells, missing cells, missing tasks, adapter coverage, and
  score-table reuse eligibility;
- compare validation protocol options:
  - no new paid cells, retrospective-only;
  - missing-cell supplement;
  - full rerun of the selected blocked split;
  - expanded-budget rerun;
  - stop for more source repair or third-repo replacement;
- project cost and latency for each option using committed prior cost summaries
  and usage ledger;
- write a frozen exploratory validation design package, if the review says one
  is ready;
- write small sanitized configs, tools, tests, result files, reports, and a
  decision.

Disallowed work:

- running any new paid ACUT solver cell;
- invoking paid LLM APIs for task solving, statement generation, statement
  review, split choice, or scoring;
- changing the completed three-repo paid pilot decision, task list, split
  assignment, primary design, thresholds, or terminal outcomes;
- changing the blocked split redesign selected task IDs, seed, or split labels;
- changing source-context release eligibility or repairing statements;
- using paid outcomes to alter the selected blocked split;
- claiming formal preregistration for work that was designed after earlier paid
  outcomes existed;
- claiming predictive validity from retrospective overlap or missing-cell
  accounting alone;
- committing raw prompts, completions, ACUT transcripts, solver workspaces,
  verifier workspaces, raw diffs, raw test patches, target repository clones,
  raw public API responses, secrets, `.venv`, caches, or large raw outputs;
- drafting or creating the next runbook.

If the worker concludes that a paid execution runbook is needed, it should
record the recommended action category and exact protocol inputs. It must not
write the paid execution runbook unless the user separately asks.

## Starting Point

The blocked split redesign ended with:

```text
decision_label: blocked_split_ready_with_click_minor_risk
ready_for_preregistered_paid_validation_runbook: true
primary selected split:
  phase1_blocked_split_redesign_20260529__same_budget_20_per_repo__seed_2026052902
primary budget:
  same_budget_20_per_repo
secondary selected split:
  phase1_blocked_split_redesign_20260529__expanded_30_per_repo__seed_2026052904
smallest remaining blocker:
  click_title_only_minor_risk
paid calls made by blocked split run: 0
completed paid decision changed: false
predictive validity established: false
```

Retrospective outcome coverage already recorded:

```text
same_budget_20_per_repo:
  36/60 selected tasks have at least one completed paid outcome
  24/60 selected tasks have no completed paid outcome

expanded_30_per_repo:
  56/90 selected tasks have at least one completed paid outcome
  34/90 selected tasks have no completed paid outcome
```

Projected full-run costs already recorded:

```text
same_budget_20_per_repo:
  120 planned scoreable cells
  token-estimated cost: USD 51.26736

expanded_30_per_repo:
  180 planned scoreable cells
  token-estimated cost: USD 76.90104
```

The key interpretation point for this run:

```text
Post-hoc design is acceptable in the current exploratory project phase, but the
claim must stay exploratory. It cannot be reported as a formal preregistered
predictive-validity experiment.
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-blocked-split-paid-validation-design-review-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md first. Use uv for
repo-local Python tooling. Follow AGENTS.md step-level acceptance and commit
requirements: after each step, or after each small group of tightly related
steps, commit the changed files with an appropriately scoped commit.

This runbook is no-paid. Do not make paid LLM calls or paid ACUT solver calls.
Do not change completed paid pilot results, blocked split task IDs, split
labels, source eligibility, or task statements.

Main goal: decide the honest validation protocol for the blocked split redesign.
Because this is still Phase 1 exploration, post-hoc split design is allowed if
it is labeled honestly. The report must distinguish exploratory evidence from
formal preregistered predictive-validity evidence.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. What action it suggests next.

Compare at least these protocol options:
1. Retrospective-only, no new paid cells.
2. Missing-cell supplement for same_budget_20_per_repo.
3. Full rerun for same_budget_20_per_repo.
4. Expanded full rerun for expanded_30_per_repo.
5. Stop for click source repair or third-repo replacement.

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
docs/experiments/phase-1-blocked-split-redesign-runbook.md
docs/experiments/phase-1-three-repo-paid-validation-runbook.md
docs/experiments/phase-1-adapter-stratified-reporting-runbook.md

experiments/phase1_compiler/results/phase1_blocked_split_redesign_decision.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_readiness_gate.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_selected_split.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_selection_audit.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_candidate_universe.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_imbalance_diagnostics.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_retrospective_outcome_diagnostics.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_cost_power_projection.json

experiments/phase1_compiler/results/phase1_source_context_statement_hardening_decision.json
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_split_feature_table.json

experiments/phase1_compiler/results/phase1_three_repo_paid_validation_decision.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_metrics.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_score_tables_manifest.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_cost_reconciliation.json

experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_decision.json
experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_three_repo_summary.json
experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_cost_latency_summary.json
experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_future_gates.json

experiments/phase0_headroom/results/phase1_three_repo_paid_validation_*_score_table.csv
experiments/phase0_headroom/results/phase1_three_repo_paid_validation_*_cost_summary.json
experiments/phase0_headroom/results/workspace_usage_ledger.jsonl
experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
experiments/phase0_headroom/configs/model_pricing.yaml
```

Do not require ignored raw artifacts for this runbook.

## Claim Boundary Policy

The worker should codify this policy in config and reports:

1. Phase 1 status is exploratory.
2. Post-hoc blocked split design is acceptable for exploration if it is labeled
   as post-hoc/exploratory.
3. Existing paid outcomes may be reused for exploratory accounting and cost
   reduction.
4. Reused outcomes cannot by themselves make the blocked split a formal
   preregistered validation.
5. Missing-cell supplement can produce useful exploratory evidence, but the
   design still remains post-hoc unless a future clean protocol is run from
   scratch on a frozen split.
6. Full rerun of the selected blocked split after this design review is cleaner
   than missing-cell supplement, but it still inherits the fact that the split
   was designed after earlier paid results existed.
7. A future formal predictive-validity claim would need a cleaner design such
   as a new time cutoff, new future tasks, third-repo replacement/repair, or a
   fresh pre-outcome protocol.
8. Click title-only minor risk must be visible in every option and decision.
9. Adapter-level reporting must come before pooled summaries.
10. Provider-billed exact cost must not be claimed unless
    `actual_provider_billed_cost_usd` is present.

## Protocol Options To Compare

The worker must compare these options:

### Option A: Retrospective Only

```text
new paid cells: 0
uses completed paid outcomes only where selected blocked split overlaps
claim: retrospective sanity check only
pros: free, fast
cons: incomplete outcome coverage; not new validation evidence
```

### Option B: Same-Budget Missing-Cell Supplement

```text
target split: same_budget_20_per_repo
new paid cells: only selected task/adapter cells missing from completed score
tables
claim: exploratory supplemental validation for blocked split
pros: cheaper than full rerun; fills the selected score table
cons: mixed old and new outcomes; still post-hoc/exploratory
```

Expected starting point:

```text
selected tasks: 60
known tasks from completed paid run: 36
missing tasks: 24
adapters: codex_workspace, kilo_workspace
likely missing cells if both adapters are needed: 48
```

The worker must compute the exact missing cells rather than relying on this
expected count.

### Option C: Same-Budget Full Rerun

```text
target split: same_budget_20_per_repo
new paid cells: all 60 tasks x 2 adapters = 120 cells
claim: cleaner exploratory validation after blocked split freeze
pros: one uniform run after design review
cons: costs about USD 51 token-estimated; still not formal pre-outcome design
```

### Option D: Expanded Full Rerun

```text
target split: expanded_30_per_repo
new paid cells: all 90 tasks x 2 adapters = 180 cells
claim: higher-coverage exploratory validation after blocked split freeze
pros: more tasks and better mechanical precision
cons: costs about USD 76.9 token-estimated; click risk remains; more spend
```

### Option E: Stop For Source Repair Or Third-Repo Replacement

```text
new paid cells: 0
claim: no paid validation until click risk is reduced or another repo replaces it
pros: cleaner source-quality basis
cons: delays validation and may require more local mining/repair
```

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_blocked_split_paid_validation_design_review.yaml
  tools/
    phase1_blocked_split_paid_validation_design_review.py
  tests/
    test_phase1_blocked_split_paid_validation_design_review.py
  results/
    phase1_blocked_split_paid_validation_design_review_preflight.json
    phase1_blocked_split_paid_validation_design_review_claim_policy.json
    phase1_blocked_split_paid_validation_design_review_overlap_matrix.json
    phase1_blocked_split_paid_validation_design_review_missing_cells.json
    phase1_blocked_split_paid_validation_design_review_protocol_options.json
    phase1_blocked_split_paid_validation_design_review_cost_projection.json
    phase1_blocked_split_paid_validation_design_review_reuse_policy.json
    phase1_blocked_split_paid_validation_design_review_ready_package.json
    phase1_blocked_split_paid_validation_design_review_decision.json
  reports/
    phase1_blocked_split_paid_validation_design_review_process.md
    phase1_blocked_split_paid_validation_design_review_claim_policy.md
    phase1_blocked_split_paid_validation_design_review_overlap_matrix.md
    phase1_blocked_split_paid_validation_design_review_protocol_options.md
    phase1_blocked_split_paid_validation_design_review_cost_projection.md
    phase1_blocked_split_paid_validation_design_review_decision.md
```

Optional small CSV outputs may be added if useful:

```text
experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_*.csv
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
5. Confirm blocked split decision is
   `blocked_split_ready_with_click_minor_risk`.
6. Write:

```text
experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_preflight.json
experiments/phase1_compiler/reports/phase1_blocked_split_paid_validation_design_review_process.md
```

Acceptance:

- preflight records branch, latest commit, dirty-tree classification, no-paid
  boundary, and required input availability;
- report states that this is an exploratory design review;
- report states that post-hoc design is acceptable for exploration but must be
  labeled honestly;
- no unrelated untracked file is staged.

Suggested commit:

```text
Record blocked split paid design review preflight
```

## Step 1: Codify Claim Policy

Write the claim-boundary policy in machine-readable and human-readable form.

Required fields:

```text
phase_status: exploratory
post_hoc_design_allowed_for_exploration: true
formal_preregistration_claim_allowed: false
predictive_validity_established: false
existing_outcomes_reusable_for_exploratory_accounting: true
existing_outcomes_reusable_for_formal_preregistration: false
click_minor_risk_must_be_reported: true
adapter_stratified_reporting_required: true
```

Write:

```text
experiments/phase1_compiler/configs/phase1_blocked_split_paid_validation_design_review.yaml
experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_claim_policy.json
experiments/phase1_compiler/reports/phase1_blocked_split_paid_validation_design_review_claim_policy.md
```

Acceptance:

- policy explicitly accepts post-hoc design only as exploratory;
- policy explicitly forbids formal preregistration wording for this design;
- policy keeps click title-only risk visible;
- no paid outcomes are used to alter the split.

Suggested commit:

```text
Codify exploratory blocked split claim policy
```

## Step 2: Compute Overlap And Missing Cells

Compute exact overlap between selected blocked split task/adapter cells and
completed paid score tables.

Do this for:

```text
same_budget_20_per_repo primary split
expanded_30_per_repo secondary split
```

For each option, record:

```text
selected_tasks
selected_cells_by_adapter
known_cells_by_adapter
missing_cells_by_adapter
known_tasks
missing_tasks
known_cells_by_repo_split_adapter
missing_cells_by_repo_split_adapter
cells_safe_to_reuse
cells_requiring_new_paid_run
reused_cell_score_table_sources
missing_cell_manifest
```

Write:

```text
experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_overlap_matrix.json
experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_missing_cells.json
experiments/phase1_compiler/reports/phase1_blocked_split_paid_validation_design_review_overlap_matrix.md
```

Acceptance:

- missing-cell counts are exact and adapter-specific;
- no missing outcomes are imputed;
- cells with known outcomes are traceable to committed score-table paths;
- cells requiring new paid work are listed by task ID, repo, split, and adapter;
- report explains why known pass/fail is incomplete for the selected split.

Suggested commit:

```text
Compute blocked split paid outcome overlap
```

## Step 3: Compare Protocol Options

Use overlap data and claim policy to compare Options A-E.

Each option must record:

```text
option_id
protocol_name
new_paid_cell_count
reused_cell_count
total_scoreable_cell_count_after_protocol
adapter_reporting_mode
claim_boundary
pros
cons
click_minor_risk_status
provider_bill_status
recommendation_status
```

Allowed recommendation statuses:

```text
recommended
acceptable_secondary
not_recommended
blocked
```

Write:

```text
experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_protocol_options.json
experiments/phase1_compiler/reports/phase1_blocked_split_paid_validation_design_review_protocol_options.md
```

Acceptance:

- options include retrospective-only, missing-cell supplement, same-budget full
  rerun, expanded full rerun, and stop/repair;
- each option has a clear claim boundary;
- no option claims predictive validity;
- no option hides click title-only minor risk.

Suggested commit:

```text
Compare blocked split validation protocols
```

## Step 4: Project Cost And Latency

Project cost and latency for each protocol option using committed cost summaries
and usage ledger.

Required outputs:

```text
new_paid_cell_count by adapter
reused_cell_count by adapter
token-estimated new cost by adapter
token-estimated total historical+new cost by adapter when relevant
median latency by adapter
provider-billed exact cost availability
cost basis
```

Do not call provider billing APIs. If exact bill is unavailable, say so.

Write:

```text
experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_cost_projection.json
experiments/phase1_compiler/reports/phase1_blocked_split_paid_validation_design_review_cost_projection.md
```

Acceptance:

- cost is adapter-stratified before any total;
- token-estimated cost is not called exact provider bill;
- missing-cell supplement cost is computed from exact missing cells;
- full rerun costs reproduce or explain differences from blocked split cost
  projection.

Suggested commit:

```text
Project blocked split validation protocol cost
```

## Step 5: Define Reuse Policy And Ready Package

If any option is recommended or acceptable, write a ready package describing the
protocol inputs a later paid execution runbook would need.

The package should include:

```text
selected_protocol_option
selected_split_id
selected_budget_id
selected_task_ids
split labels
adapters
known reusable cells
missing paid cells to run
endpoint requirement: LLM_BASE_URL + LLM_API_KEY
adapter reporting policy
claim boundary
click minor-risk caveat
stop conditions
```

If no option is recommended, write a blocker package instead.

Write:

```text
experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_reuse_policy.json
experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_ready_package.json
```

Acceptance:

- ready package does not execute paid cells;
- package separates reusable cells from missing cells;
- package states whether old cells are accepted only for exploratory evidence;
- package states whether a full rerun is cleaner but more expensive;
- package does not draft the paid execution runbook.

Suggested commit:

```text
Package blocked split validation design review
```

## Step 6: Tests And Consistency Checks

Add focused tests for the design review tool and policy.

Minimum test coverage:

- claim policy permits post-hoc design only under exploratory status;
- formal preregistration claim is false;
- missing-cell counts are adapter-specific and deterministic;
- no missing outcomes are imputed;
- known cells have committed score-table provenance;
- protocol options do not claim predictive validity;
- click minor-risk caveat is required for every non-stop option;
- cost projections are adapter-stratified;
- provider-billed exact cost is unavailable unless explicitly present;
- ready package contains no raw prompts, completions, transcripts, workspaces,
  raw diffs, raw test patches, or secrets.

Run:

```bash
uv run --project experiments/phase1_compiler pytest \
  experiments/phase1_compiler/tests/test_phase1_blocked_split_paid_validation_design_review.py -q

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
Test blocked split paid design review
```

## Step 7: Decision And Closeout

Write a decision that answers:

```text
RQ1: Why are paid pass/fail results incomplete for the selected blocked split?
RQ2: Is post-hoc design acceptable in this project phase?
RQ3: What claim boundary should be used?
RQ4: Which protocol option is recommended?
RQ5: How many cells can be reused and how many new cells would be needed?
RQ6: What is the estimated new paid cost by adapter and total?
RQ7: Does click title-only minor risk remain a blocker or accepted caveat?
RQ8: Did this run make paid calls?
RQ9: Did this run change completed paid decisions or selected split labels?
RQ10: What action category should the coordinator consider next?
```

Allowed decision labels:

```text
recommend_missing_cell_supplement_exploratory
recommend_same_budget_full_rerun_exploratory
recommend_expanded_full_rerun_exploratory
recommend_retrospective_only_no_paid
recommend_source_repair_or_third_repo_replacement
blocked_by_overlap_or_cost_uncertainty
blocked_by_policy_or_hygiene_issue
```

Readiness for a later paid execution runbook is true only if:

```text
claim policy is written and exploratory status is explicit
selected blocked split remains unchanged
overlap and missing-cell manifests are exact
recommended option has clear reusable/missing cell handling
adapter-level reporting is required
click minor-risk caveat is explicit
cost projection is adapter-stratified and token-estimated
paid calls made by this run = 0
completed paid decision changed = false
predictive validity established = false
tests and git diff --check passed
```

Write:

```text
experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_decision.json
experiments/phase1_compiler/reports/phase1_blocked_split_paid_validation_design_review_decision.md
```

Acceptance:

- decision uses one allowed label;
- report states whether post-hoc design is accepted as exploratory;
- report names the exact recommended option;
- report states the number of reusable and missing cells;
- report states estimated new paid cost;
- no next runbook is drafted or created.

Suggested commit:

```text
Close blocked split paid design review
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
- whether selected blocked split changed;
- whether predictive validity is still not established;
- recommended protocol option;
- known reusable cells and missing new cells;
- projected new paid cost;
- click minor-risk status;
- decision label;
- recommended next action category.

Do not create a follow-up runbook unless the user explicitly asks for one after
this run is complete.
