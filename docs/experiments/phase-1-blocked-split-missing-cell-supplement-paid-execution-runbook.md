# Phase 1 Blocked Split Missing-Cell Supplement Paid Execution Runbook

Status: paid execution runbook, 2026-05-29.

This runbook is for one dedicated Codex CLI session. Its job is to execute the
recommended exploratory missing-cell supplement for the blocked split redesign.

```text
Reuse the 72 already completed paid task/adapter cells that overlap the selected
blocked split, run only the 48 missing selected task/adapter cells, then report
the completed same_budget_20_per_repo blocked split as exploratory evidence.
```

Plain-language summary:

```text
We redesigned the split after earlier paid results existed. That is acceptable
for this Phase 1 exploration, but it limits what we can claim.

This runbook should not rerun everything. It should keep the 72 old cells that
already match the selected task/adapter pairs, pay only for the 48 missing
cells, and then explain the result as an exploratory check, not a formal
preregistered validation.
```

## Paid Approval Boundary

This runbook may make paid ACUT solver calls only when the coordinating
user-facing session explicitly asks a worker to execute this paid runbook and
approves the selected paid batch option and budget cap.

Default approved option for execution, if the user asks to run this runbook:

```text
option: same_budget_missing_cell_supplement
selected split:
  phase1_blocked_split_redesign_20260529__same_budget_20_per_repo__seed_2026052902
planned unique selected tasks: 60
known reusable cells: 72
new paid cells to run: 48
planned adapters: codex_workspace, kilo_workspace
token-estimated new paid cost: USD 20.506944
hard cost cap: USD 30 unless the coordinating session gives a lower cap
```

If the worker cannot prove that this approval applies to the current execution,
stop before paid calls and write a blocker report. Do not infer paid approval
from this document merely existing.

The smoke batch is not extra work. It is the first 6 cells from the frozen
48-cell missing-cell manifest.

Do not draft or create a follow-up runbook. Record recommended next action
categories only.

## Execution Boundary

Allowed work:

- read committed blocked split, design-review, source-hardening,
  adapter-reporting, paid-validation, cost, and usage artifacts;
- verify that the selected split, selected task IDs, missing-cell manifest, and
  ready package are unchanged;
- import the 72 reusable cells from committed prior score tables without
  changing their terminal outcomes;
- assign reusable cells to the selected blocked split labels for this new
  exploratory combined table;
- run exactly the 48 missing selected task/adapter cells, in the batch order
  frozen by this runbook;
- capture final solver diffs through the configured workspace ACUT adapters and
  verify them in fresh verifier workspaces;
- import score rows, usage, latency, and token-estimated cost after every paid
  batch;
- write small sanitized configs, tools, tests, score tables, manifests, result
  files, reports, and a decision.

Disallowed work:

- running any paid task/adapter cell outside the 48-cell missing manifest;
- rerunning the 72 reusable cells unless the run stops and records a blocker
  explaining why reuse provenance cannot be trusted;
- changing the selected blocked split, selected task IDs, seed, budget, or split
  labels;
- changing the completed three-repo paid pilot decision, old score tables,
  terminal outcomes, thresholds, or historical cost records;
- repairing task statements, source eligibility, source context, or Task
  Generator behavior in this runbook;
- using newly observed outcomes to add tasks, drop tasks, reorder future
  non-smoke batches, or revise the claim boundary;
- claiming formal preregistration or predictive validity from this mixed old/new
  supplement;
- using paid LLM calls for statement generation, statement review, split choice,
  or analysis outside the configured ACUT solver cells;
- committing raw prompts, completions, ACUT transcripts, solver workspaces,
  verifier workspaces, raw diffs, raw test patches, target repository clones,
  raw public API responses, secrets, `.venv`, caches, or large raw outputs.

Raw harness outputs must remain under ignored paths. Commit only small
sanitized artifacts.

## Starting Point

The previous design review ended with:

```text
decision_label: recommend_missing_cell_supplement_exploratory
selected protocol option: B
selected protocol name: same_budget_missing_cell_supplement
selected split:
  phase1_blocked_split_redesign_20260529__same_budget_20_per_repo__seed_2026052902
selected budget:
  same_budget_20_per_repo
known reusable cells: 72
missing paid cells to run: 48
paid calls made by design review: 0
completed paid decision changed: false
selected blocked split changed: false
predictive validity established: false
```

Cost projection:

```text
new codex_workspace cells: 24
new codex token-estimated cost: USD 12.889248

new kilo_workspace cells: 24
new kilo token-estimated cost: USD 7.617696

new total paid cells: 48
new total token-estimated cost: USD 20.506944
provider-billed exact cost available: false
```

The completed table after this run should contain:

```text
selected tasks: 60
selected cells: 120
reused cells from earlier paid run: 72
new paid cells from this supplement: 48
```

Important interpretation point:

```text
The selected blocked split was designed after earlier paid outcomes existed.
This supplement is useful exploratory evidence, but it is not a clean
pre-outcome, formally preregistered predictive-validity experiment.
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-blocked-split-missing-cell-supplement-paid-execution-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md first. Use uv for
repo-local Python tooling. Follow AGENTS.md step-level acceptance and commit
requirements: after each step, or after each small group of tightly related
steps, commit the changed files with an appropriately scoped commit.

Paid execution approval is granted for option=same_budget_missing_cell_supplement
only if the coordinating session explicitly provided that approval when
launching this worker. If approval is absent or ambiguous, stop before paid
calls and write a blocker. If approval is present, the hard cost cap is USD 30
unless the coordinating session provides a lower cap.

Main goal: execute the frozen missing-cell supplement from
phase1_blocked_split_paid_validation_design_review_20260529. Reuse exactly the
72 committed prior cells listed in the ready package and run exactly the 48
missing cells listed there. Do not change the selected split, selected task IDs,
source eligibility, old paid outcomes, or claim boundary after seeing outcomes.

Every paid ACUT call must use LLM_BASE_URL and LLM_API_KEY. If either variable
is missing, source ~/.zshrc and check again before any paid call. Do not fall
back to local Codex/ChatGPT subscription auth, OPENAI_API_KEY, OpenRouter
variables, or provider-specific fallback variables.

Keep Barcarolle on the benchmark/compiler side of the ACUT boundary. Barcarolle
may prepare clean solver workspaces, invoke configured ACUT workspace adapters,
capture final git diffs, replay those diffs in fresh verifier workspaces,
inject private oracle material only in verifier workspaces, run hidden
verifiers there, and record sanitized results. Do not implement Codex, Kilo, or
another ACUT harness.

Run paid cells in small batches. After every paid batch, import/summarize usage
and cost, recompute scoreability and policy gates, and stop before the next
batch if any stop condition fires.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. Whether the next paid batch should continue or stop.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
Codex/Kilo logs, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, raw target diffs, raw test patches, raw public API
responses, or large raw outputs. Commit only small sanitized configs, tools,
tests, score tables, metrics, cost summaries, reports, manifests, digests, and
decision files. Raw harness outputs must remain under ignored paths.

Do not draft or create the next runbook.
```

## Required Inputs

Use these committed inputs:

```text
AGENTS.md
docs/architecture/system-design.md
docs/experiments/phase-1-blocked-split-redesign-runbook.md
docs/experiments/phase-1-blocked-split-paid-validation-design-review-runbook.md
docs/experiments/phase-1-three-repo-paid-validation-runbook.md
docs/experiments/phase-1-adapter-stratified-reporting-runbook.md

experiments/phase1_compiler/results/phase1_blocked_split_redesign_decision.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_selected_split.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_selection_audit.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_retrospective_outcome_diagnostics.json

experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_decision.json
experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_ready_package.json
experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_missing_cells.json
experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_overlap_matrix.json
experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_cost_projection.json

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
experiments/phase0_headroom/tools/workspace_acut_run.py
experiments/phase0_headroom/tools/workspace_usage_import.py
```

Use source certification artifacts only if the workspace ACUT tooling needs
task package fields that are not already present in the ready package or split
artifacts.

Do not require ignored raw artifacts for preflight or reuse verification.

## Endpoint Rule

Every paid call must use:

```text
LLM_BASE_URL
LLM_API_KEY
```

Before paid work, check without printing values:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

Stop before paid work if either variable is missing after sourcing `~/.zshrc`.
Do not use subscription auth, `OPENAI_API_KEY`, OpenRouter variables, or any
provider-specific fallback for paid ACUT cells.

## Frozen Missing-Cell Manifest

Run exactly these 24 missing tasks with both adapters:

```text
attrs / B_eval:
  attrs__v2__157
  attrs__v2__231
  attrs__v2__271

attrs / H_future:
  attrs__v2__210
  attrs__v2__218
  attrs__v2__244

boltons / B_eval:
  boltons__v2__008
  boltons__v2__009
  boltons__v2__076
  boltons__v2__103
  boltons__v2__128
  boltons__v2__154
  boltons__v2__231

boltons / H_future:
  boltons__v2__122
  boltons__v2__132
  boltons__v2__232

click / B_eval:
  click__third__091
  click__third__202
  click__third__220

click / H_future:
  click__third__109
  click__third__198
  click__third__214
  click__third__234
  click__third__288
```

For every task above, run:

```text
codex_workspace
kilo_workspace
```

Expected count:

```text
24 tasks * 2 adapters = 48 new paid cells
```

If any task/adaptor cell in this section differs from
`phase1_blocked_split_paid_validation_design_review_ready_package.json`, stop
before paid calls and write a blocker.

## Claim Boundary

Allowed claims after this runbook:

```text
blocked_split_missing_cell_supplement_executed
selected_same_budget_blocked_split_completed
reused_prior_cells_recorded
new_missing_cells_recorded
adapter_stratified_exploratory_metrics_recorded
token_estimated_cost_recorded
policy_violation_rate_recorded
scoreability_rate_recorded
exploratory_threshold_diagnostic_recorded
```

Disallowed claims:

```text
formal_preregistration_completed
predictive_validity_established
clean_pre_outcome_validation
production_benchmark_ranking
old_paid_decision_changed
post_hoc_result_promoted_to_primary_preregistered_evidence
raw_oracle_exposed_to_solver
provider_exact_bill_recorded_without_bill_artifact
```

Interpretation rules:

- `verified_pass` and `verified_fail` are scoreable ACUT outcomes.
- `policy_violation`, `invalid_output`, `acut_harness_error`,
  `harness_error`, `timeout`, and endpoint/tooling failures are non-scoreable
  or boundary failures.
- Non-scoreable cells are excluded from pass-rate denominators, but they count
  against the scoreability gate.
- Use adapter-stratified reporting first. Pooled summaries may be included only
  after adapter-level results.
- Any gap threshold is exploratory/diagnostic in this runbook. Do not describe
  it as a preregistered predictive-validity threshold.
- The click title-only minor risk must be visible in the final decision.

## Budget And Batch Policy

Use the design-review estimate:

```text
new paid cells: 48
token-estimated new paid cost: USD 20.506944
approved hard cap default: USD 30
paid ACUT concurrency: 1
cross-harness paid parallelism: disabled
```

Run paid cells sequentially by small batch. Freeze this batch schedule before
the first paid call:

```text
Batch 0: no-paid preflight, ready-package integrity, reuse import, batch plan
Batch 1: paid smoke, 3 tasks * 2 adapters = 6 cells
  attrs__v2__157
  boltons__v2__008
  click__third__091
Batch 2: attrs missing-cell remainder, 5 tasks * 2 adapters = 10 cells
  attrs__v2__210
  attrs__v2__218
  attrs__v2__231
  attrs__v2__244
  attrs__v2__271
Batch 3: boltons missing-cell remainder, 9 tasks * 2 adapters = 18 cells
  boltons__v2__009
  boltons__v2__076
  boltons__v2__103
  boltons__v2__122
  boltons__v2__128
  boltons__v2__132
  boltons__v2__154
  boltons__v2__231
  boltons__v2__232
Batch 4: click missing-cell remainder, 7 tasks * 2 adapters = 14 cells
  click__third__109
  click__third__198
  click__third__202
  click__third__214
  click__third__220
  click__third__234
  click__third__288
```

The total is:

```text
6 + 10 + 18 + 14 = 48 cells
```

Stop before the next paid batch if any of these fires:

```text
paid_approval_absent_or_ambiguous
endpoint_proof_missing
selected_split_or_task_manifest_mismatch
reusable_cell_provenance_unverifiable
planned_paid_cells_not_exactly_48
paid_cell_outside_missing_manifest
projected_total_new_cost_exceeds_approved_cap
observed_or_token_estimated_cost_cannot_be_reconciled
scoreability_below_gate_or_cannot_recover_to_gate
policy_violation_count_above_0
raw_oracle_exposure_detected
cost_latency_accounting_incomplete
raw_or_secret_artifact_would_be_committed
```

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_blocked_split_missing_cell_supplement_paid_execution.yaml
  tools/
    phase1_blocked_split_missing_cell_supplement_paid_execution.py
  tests/
    test_phase1_blocked_split_missing_cell_supplement_paid_execution.py
  results/
    phase1_blocked_split_missing_cell_supplement_paid_execution_preflight.json
    phase1_blocked_split_missing_cell_supplement_paid_execution_ready_package_integrity.json
    phase1_blocked_split_missing_cell_supplement_paid_execution_reuse_manifest.json
    phase1_blocked_split_missing_cell_supplement_paid_execution_entry_gate.json
    phase1_blocked_split_missing_cell_supplement_paid_execution_batch_plan.json
    phase1_blocked_split_missing_cell_supplement_paid_execution_batch_1_smoke.json
    phase1_blocked_split_missing_cell_supplement_paid_execution_batch_2_attrs_remainder.json
    phase1_blocked_split_missing_cell_supplement_paid_execution_batch_3_boltons_remainder.json
    phase1_blocked_split_missing_cell_supplement_paid_execution_batch_4_click_remainder.json
    phase1_blocked_split_missing_cell_supplement_paid_execution_cost_reconciliation.json
    phase1_blocked_split_missing_cell_supplement_paid_execution_combined_score_tables_manifest.json
    phase1_blocked_split_missing_cell_supplement_paid_execution_adapter_stratified_metrics.json
    phase1_blocked_split_missing_cell_supplement_paid_execution_decision.json
  reports/
    phase1_blocked_split_missing_cell_supplement_paid_execution_process.md
    phase1_blocked_split_missing_cell_supplement_paid_execution_preflight.md
    phase1_blocked_split_missing_cell_supplement_paid_execution_ready_package_integrity.md
    phase1_blocked_split_missing_cell_supplement_paid_execution_reuse_manifest.md
    phase1_blocked_split_missing_cell_supplement_paid_execution_batch_plan.md
    phase1_blocked_split_missing_cell_supplement_paid_execution_batch_status.md
    phase1_blocked_split_missing_cell_supplement_paid_execution_cost_reconciliation.md
    phase1_blocked_split_missing_cell_supplement_paid_execution_adapter_stratified_metrics.md
    phase1_blocked_split_missing_cell_supplement_paid_execution_decision.md

experiments/phase0_headroom/
  results/
    phase1_blocked_split_missing_cell_supplement_paid_execution_*_score_table.csv
    phase1_blocked_split_missing_cell_supplement_paid_execution_*_cost_summary.json
    phase1_blocked_split_missing_cell_supplement_paid_execution_*_matrix.json
    workspace_usage_ledger.jsonl
```

Raw outputs must stay under ignored paths:

```text
experiments/phase0_headroom/results/raw/
experiments/phase0_headroom/workspaces/
experiments/phase0_headroom/external_repos/
experiments/phase1_compiler/tmp/blocked_split_missing_cell_supplement_paid_execution/
```

Do not commit raw ACUT logs, raw prompts, raw completions, solver workspaces,
verifier workspaces, target repo clones, caches, or secret-bearing artifacts.

## Step 0 - Preflight And Approval Record

Goal: prove the paid supplement starts from a frozen, approved state.

Actions:

1. Read `AGENTS.md`, this runbook, and all required input artifacts.
2. Record branch, HEAD, date, Python version, `uv --version`,
   `codex --version` if available, and `kilo --version` if available.
3. Record `git status --short --untracked-files=all` and `git diff --check`.
4. Classify dirty/untracked files. The known external-review bundle may remain
   untracked unless the user explicitly asks to package or remove it.
5. Record explicit paid approval:
   - approved option;
   - approved cost cap;
   - planned adapters;
   - planned new paid cells.
6. Verify endpoint variables without printing values.
7. Confirm ready package status is `ready`.
8. Write preflight result and process report.

Acceptance:

- Paid approval is recorded for this execution.
- Endpoint variables are present.
- Ready package status is `ready`.
- Selected protocol is `same_budget_missing_cell_supplement`.
- No paid calls have run before preflight.
- Dirty/untracked files are classified.

Stop if:

- paid approval is absent or ambiguous;
- endpoint variables are missing;
- ready package is missing or not ready;
- selected protocol is not option B;
- selected split differs from the value in this runbook.

Commit:

```text
Record blocked split missing-cell supplement preflight
```

## Step 1 - Ready Package Integrity And Tooling Check

Goal: prove the frozen ready package can drive the workspace ACUT runner.

Actions:

1. Load the ready package and selected split artifacts.
2. Verify:
   - selected split ID matches this runbook;
   - selected budget is `same_budget_20_per_repo`;
   - selected task count is 60;
   - known reusable cells count is 72;
   - missing paid cells count is 48;
   - adapters are exactly `codex_workspace` and `kilo_workspace`;
   - endpoint requirement is `LLM_BASE_URL` plus `LLM_API_KEY`;
   - click minor risk caveat is still present.
3. Add or update a small paid-execution wrapper only if existing tooling cannot
   load the ready package directly.
4. For every missing task, verify:
   - solver workspace can start at the task base commit;
   - solver-visible statement exists;
   - hidden oracle material is not solver-visible;
   - editable and non-editable path policy is enforceable;
   - split label matches the selected split;
   - adapter config uses the required endpoint variables.
5. Add focused tests for ready-package loading, manifest validation, and batch
   plan generation.
6. Do not run paid ACUT cells in this step.

Expected outputs:

```text
phase1_blocked_split_missing_cell_supplement_paid_execution_ready_package_integrity.json
phase1_blocked_split_missing_cell_supplement_paid_execution_ready_package_integrity.md
```

Acceptance:

- Ready-package integrity passes.
- All 48 missing task/adapter cells are loadable.
- Both adapters are resolvable.
- A no-paid dry inspection passes.
- Focused tests pass.

Commit:

```text
Check blocked split supplement ready package
```

## Step 2 - Reuse Import, Entry Gate, And Batch Plan

Goal: freeze the combined accounting plan before paid outcomes from this run
exist.

Actions:

1. Import the 72 reusable cells listed by the ready package from committed prior
   score tables.
2. Verify each reusable cell has:
   - task ID;
   - repo;
   - adapter;
   - old score-table source path;
   - old terminal status;
   - old scoreability label;
   - selected blocked split label for the new combined table.
3. Build the exact 48-cell paid batch plan from the frozen manifest.
4. Verify the batch plan contains no cells outside the ready package.
5. Verify the old completed paid decision is not modified.
6. Write the reuse manifest, entry gate, and batch plan.

Expected outputs:

```text
phase1_blocked_split_missing_cell_supplement_paid_execution_reuse_manifest.json
phase1_blocked_split_missing_cell_supplement_paid_execution_entry_gate.json
phase1_blocked_split_missing_cell_supplement_paid_execution_batch_plan.json
phase1_blocked_split_missing_cell_supplement_paid_execution_reuse_manifest.md
phase1_blocked_split_missing_cell_supplement_paid_execution_batch_plan.md
```

Acceptance:

- Reused cells equal 72.
- Planned new paid cells equal 48.
- Combined planned cells equal 120.
- Batch plan is deterministic and complete.
- Entry gate status is `ready_for_paid_batches`.
- No paid cells have run yet.

Commit:

```text
Freeze blocked split supplement batch plan
```

## Step 3 - Paid Batch 1 Smoke

Goal: spend a small amount first and validate operational health.

Actions:

1. Run exactly these 3 tasks with both adapters: 6 cells.

```text
attrs__v2__157
boltons__v2__008
click__third__091
```

2. Store raw outputs only under ignored paths.
3. Import score rows and usage/cost records.
4. Check:
   - endpoint compliance evidence;
   - policy violations;
   - scoreability;
   - raw oracle exposure;
   - cost accounting;
   - no unapproved raw artifacts are staged.
5. Stop before Batch 2 if any stop condition fires.

Expected outputs:

```text
phase1_blocked_split_missing_cell_supplement_paid_execution_batch_1_smoke.json
phase1_blocked_split_missing_cell_supplement_paid_execution_batch_status.md
```

Acceptance:

- 6 planned smoke cells are accounted for as scoreable or preregistered
  non-scoreable.
- Cost/usage is reconciled or a blocker is written.
- Continue/stop decision is explicit.

Commit:

```text
Record blocked split supplement smoke batch
```

## Step 4 - Paid Batch 2 Attrs Remainder

Goal: finish the attrs missing cells if the smoke batch is clean.

Actions:

1. Run exactly these 5 attrs tasks with both adapters: 10 cells.

```text
attrs__v2__210
attrs__v2__218
attrs__v2__231
attrs__v2__244
attrs__v2__271
```

2. Import score rows and usage/cost records.
3. Recompute cumulative scoreability, policy, raw-oracle, endpoint, and cost
   gates.
4. Stop before Batch 3 if any stop condition fires.

Expected outputs:

```text
phase1_blocked_split_missing_cell_supplement_paid_execution_batch_2_attrs_remainder.json
phase1_blocked_split_missing_cell_supplement_paid_execution_batch_status.md
```

Acceptance:

- 16 cumulative new paid cells are accounted for.
- The combined table still has exactly 72 reused cells plus completed new cells.
- Continue/stop decision is explicit.

Commit:

```text
Record blocked split supplement attrs batch
```

## Step 5 - Paid Batch 3 Boltons Remainder

Goal: finish the boltons missing cells if gates remain clean.

Actions:

1. Run exactly these 9 boltons tasks with both adapters: 18 cells.

```text
boltons__v2__009
boltons__v2__076
boltons__v2__103
boltons__v2__122
boltons__v2__128
boltons__v2__132
boltons__v2__154
boltons__v2__231
boltons__v2__232
```

2. Import score rows and usage/cost records.
3. Recompute cumulative scoreability, policy, raw-oracle, endpoint, and cost
   gates.
4. Stop before Batch 4 if any stop condition fires.

Expected outputs:

```text
phase1_blocked_split_missing_cell_supplement_paid_execution_batch_3_boltons_remainder.json
phase1_blocked_split_missing_cell_supplement_paid_execution_batch_status.md
```

Acceptance:

- 34 cumulative new paid cells are accounted for.
- Cost projection remains under the approved cap.
- Continue/stop decision is explicit.

Commit:

```text
Record blocked split supplement boltons batch
```

## Step 6 - Paid Batch 4 Click Remainder

Goal: finish the click missing cells if gates remain clean.

Actions:

1. Run exactly these 7 click tasks with both adapters: 14 cells.

```text
click__third__109
click__third__198
click__third__202
click__third__214
click__third__220
click__third__234
click__third__288
```

2. Import score rows and usage/cost records.
3. Recompute cumulative scoreability, policy, raw-oracle, endpoint, and cost
   gates.
4. Keep the click title-only minor risk visible in the batch status.

Expected outputs:

```text
phase1_blocked_split_missing_cell_supplement_paid_execution_batch_4_click_remainder.json
phase1_blocked_split_missing_cell_supplement_paid_execution_batch_status.md
```

Acceptance:

- 48 cumulative new paid cells are accounted for.
- 120 combined planned cells are either reusable or newly completed.
- Cost/usage records are ready for reconciliation.
- The click caveat is still explicit.

Commit:

```text
Record blocked split supplement click batch
```

## Step 7 - Cost Reconciliation And Combined Score Tables

Goal: make reuse, new spend, and score-table coverage auditable before
interpreting scores.

Actions:

1. Reconcile workspace usage ledger and cost summaries for the 48 new cells.
2. Record:
   - token-estimated new cost;
   - historical reused token-estimated cost;
   - total token-estimated historical-plus-new cost;
   - exact provider-billed cost only if an actual bill artifact exists.
3. Build a combined score-table manifest listing:
   - reused result prefixes and source score tables;
   - new result prefixes and score tables;
   - repo/split/adapter coverage;
   - planned cells;
   - completed cells;
   - scoreable cells;
   - non-scoreable cells by taxonomy.
4. Verify raw logs remain ignored and uncommitted.

Expected outputs:

```text
phase1_blocked_split_missing_cell_supplement_paid_execution_cost_reconciliation.json
phase1_blocked_split_missing_cell_supplement_paid_execution_combined_score_tables_manifest.json
phase1_blocked_split_missing_cell_supplement_paid_execution_cost_reconciliation.md
```

Acceptance:

- Cost/latency accounting is complete or the result is blocked.
- Provider-billed exact cost is not claimed unless directly supported.
- Combined score-table manifest covers all 120 selected cells or records the
  exact incomplete state.

Commit:

```text
Reconcile blocked split supplement cost and score tables
```

## Step 8 - Adapter-Stratified Metrics And Interpretation

Goal: evaluate the selected blocked split without hiding adapter behavior.

Actions:

1. Compute metrics first by adapter:
   - selected cells;
   - reused cells;
   - new cells;
   - completed cells;
   - scoreable cells;
   - pass rate;
   - B_eval pass rate;
   - H_future pass rate;
   - B_eval/H_future absolute gap;
   - per-repo pass rates and gaps;
   - policy violations;
   - raw-oracle status;
   - endpoint compliance;
   - token-estimated cost;
   - latency summaries.
2. Compute paired adapter disagreement for shared selected tasks.
3. Compute pooled summaries only after adapter-level results.
4. Compare the observed gap to the old `<= 0.15` threshold only as an
   exploratory diagnostic.
5. Keep click title-only minor risk visible.
6. Do not change selected split or task list after seeing metrics.

Expected outputs:

```text
phase1_blocked_split_missing_cell_supplement_paid_execution_adapter_stratified_metrics.json
phase1_blocked_split_missing_cell_supplement_paid_execution_adapter_stratified_metrics.md
```

Acceptance:

- Adapter-stratified results appear before pooled summaries.
- Metrics distinguish reused and newly paid cells.
- No metric is described as formal preregistered predictive validity.
- Click title-only risk is present in the interpretation.

Commit:

```text
Compute blocked split supplement metrics
```

## Step 9 - Decision And Closeout

Goal: write a clear exploratory result or blocker.

Actions:

1. Write final decision artifacts.
2. Answer these research questions:

```text
RQ1: Did all 48 missing cells run?
RQ2: Were all 72 reusable cells traceable to committed prior score tables?
RQ3: What was the combined selected-cell scoreability rate?
RQ4: Were endpoint, policy, raw-oracle, and cost-accounting gates clean?
RQ5: What did the new supplement cost, token-estimated?
RQ6: What are the adapter-stratified B_eval/H_future results?
RQ7: How much do Codex and Kilo disagree on the selected tasks?
RQ8: Does the exploratory diagnostic look healthier than the previous split?
RQ9: What claim is allowed, and what claim is still not allowed?
```

3. Record completed steps, commits made during the run, tests run, and known
   blockers.
4. Do not draft a follow-up runbook.

Expected outputs:

```text
phase1_blocked_split_missing_cell_supplement_paid_execution_decision.json
phase1_blocked_split_missing_cell_supplement_paid_execution_decision.md
```

Decision labels:

```text
blocked_split_missing_cell_supplement_completed_exploratory
blocked_split_missing_cell_supplement_completed_with_non_scoreable_cells
blocked_split_missing_cell_supplement_blocked_before_paid_calls
blocked_split_missing_cell_supplement_blocked_after_partial_run
```

Acceptance:

- The report states clearly whether paid cells ran.
- The report says this is exploratory evidence.
- The report does not claim formal preregistration or predictive validity.
- The old completed paid decision remains unchanged.
- The selected blocked split remains unchanged.
- The report explains the result in simple language.

Commit:

```text
Close blocked split missing-cell supplement run
```

## Verification

At minimum, run:

```bash
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_blocked_split_missing_cell_supplement_paid_execution.py -q
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q
git diff --check
git status --short --untracked-files=all
```

If the full test suite is too slow or blocked, run focused tests plus the
nearest related tests and record the reason.

## Final Reporting Template

The final worker summary should be short and in simple Chinese:

```text
这次 runbook 是 paid execution，但不是全量重跑。

我们做了什么：
- 复用了旧 paid run 里已经存在的 72 个 cell。
- 只补跑 selected blocked split 缺的 48 个 cell。
- 最后把 72 + 48 合成同一个 120-cell exploratory 结果表。

结果：
- planned new cells: 48
- completed new cells: N
- reused cells: 72
- combined selected cells: N / 120
- scoreable cells: N
- scoreability rate: X
- policy violations: N
- raw oracle exposure: yes/no
- endpoint compliance: pass/fail
- new token-estimated cost: $X
- exact provider bill: available/unavailable

解释：
- 这能告诉我们 blocked split 在现有三仓上看起来是否更合理。
- 但因为 split 是在旧 paid 结果存在之后设计的，所以它还是探索性证据。
- 它不能被说成正式 preregistered predictive-validity 实验。
- Codex 和 Kilo 的结果要分开看，不能只看一个 pooled 平均数。
- click 的 title-only source risk 仍然要作为 caveat。

没有提交 raw logs、raw prompts、raw completions、solver workspaces、verifier
workspaces 或 secrets。
```
