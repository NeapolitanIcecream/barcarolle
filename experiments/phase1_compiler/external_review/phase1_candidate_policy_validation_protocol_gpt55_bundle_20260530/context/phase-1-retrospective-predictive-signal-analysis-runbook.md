# Phase 1 Retrospective Predictive-Signal Analysis Runbook

Status: no-paid analysis runbook, 2026-05-30.

This runbook is for one dedicated Codex CLI session. Its job is to use existing
committed paid outcomes to test whether any Barcarolle candidate design has
retrospective predictive signal beyond simple baselines.

```text
Run an outcome-blind retrospective / rolling-style replay over the repaired
three-repo Phase 1 supply, compare candidate benchmark designs against simple
baselines, and report adapter-stratified prediction error.
```

Plain-language summary:

```text
Barcarolle's final north-star claim is predictive validity: a compiled
repo-specific benchmark should better predict later target-repo work than a
simple random, unweighted, stratified, or temporal baseline.

We are not ready to claim that yet. But we do have enough paid outcome evidence
and cleaner three-repo source quality to run a no-paid retrospective signal
analysis. The worker should freeze candidate designs without looking at
outcomes, then join existing score tables only after selections are fixed, and
ask: did any Barcarolle-style design predict H_future outcomes better than
simple baselines?
```

## Execution Boundary

This runbook is no-paid. It must not make paid ACUT solver calls or paid LLM
calls.

Allowed work:

- read committed candidate inventories, repaired source-quality overlays,
  split plans, score tables, adapter metrics, manifests, and reports;
- reuse existing paid ACUT outcomes only after outcome-blind selections,
  cutoffs, windows, and candidate designs are frozen;
- implement deterministic local analysis tooling, tests, JSON/CSV outputs,
  Markdown reports, and a decision;
- compare multiple candidate designs and baselines using adapter-stratified
  prediction metrics;
- classify the result as traction evidence, negative evidence, underpowered
  evidence, or a blocker.

Disallowed work:

- running new paid ACUT solver cells;
- running paid LLM calls;
- rerunning failed, invalid, disagreeing, or high-gap cells;
- changing completed paid terminal outcomes, score tables, selected task IDs,
  split labels, source-eligibility artifacts, task statements, or completed
  decisions;
- using terminal outcomes, pass/fail labels, adapter outcomes, or H_future
  outcomes to select tasks, tune weights, choose cutoffs, choose seeds, or
  choose which candidate design is the primary claim;
- claiming formal preregistered predictive validity from already-inspected
  outcomes;
- collapsing Codex and Kilo into a model-only result;
- committing raw prompts, raw completions, raw ACUT transcripts, raw Codex/Kilo
  logs, solver workspaces, verifier workspaces, raw diffs, raw test patches,
  target repository clones, raw public API responses, secrets, `.venv`, caches,
  or large raw outputs;
- drafting or creating the next runbook.

If true rolling-origin support is too sparse, record that limitation and run a
clearly labeled `retrospective_pseudo_future_signal_analysis`. Do not inflate it
into a formal predictive-validity claim.

## Starting Point

Current process state:

```text
Phase 1 goal:
  traction evidence, narrative validation, and project/proposal support

predictive validity:
  not established

three-repo supply:
  attrs, boltons, click

click source-quality boundary:
  repaired; all 30 frozen click tasks now have reviewed public context

adapter fairness:
  fair enough to interpret Codex/Kilo differences as ACUT configuration results

paid ACUT cells:
  no more by default
```

Existing algorithm evidence:

```text
old weighted target-profile:
  failed paid pilot; keep as negative-control/reference only

repo_stratified / repo_unweighted:
  current conservative baselines

blocked / shrinkage / coverage / temporal variants:
  available as local research candidates, not promoted
```

This runbook should answer:

```text
Do existing paid outcomes contain retrospective evidence that a Barcarolle-style
candidate design predicts later or held-out repo outcomes better than simple
baselines?
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-retrospective-predictive-signal-analysis-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first.
Use uv for repo-local Python tooling. Follow AGENTS.md step-level acceptance and
commit requirements: after each step, or after a small group of tightly related
steps, commit the changed files with an appropriately scoped commit.

Main goal: run a no-paid retrospective predictive-signal analysis over the
repaired attrs/boltons/click Phase 1 supply. Freeze cutoffs, windows, baselines,
candidate designs, adapter policy, and metrics before loading score outcomes.
Then join committed paid score tables and compare prediction error.

Do not run paid ACUT cells or paid LLM calls. Do not rerun cells. Do not change
paid outcomes, score tables, selected task IDs, split labels, source
eligibility, task statements, or completed decisions. Do not use outcomes to
select tasks, tune weights, pick seeds, or choose a favorable cutoff.

Use adapter-stratified reporting first. Kilo and Codex differences are ACUT
configuration evidence if benchmark-side conditions remain clean enough. Pooled
results are secondary unless the analysis explicitly defines an equal-mix
pooled estimator before outcomes are joined.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. What action it suggests next.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
Codex/Kilo logs, solver workspaces, verifier workspaces, target repo clones,
raw public API responses, raw target diffs, raw test patches, .venv, caches, or
large raw outputs. Commit only small sanitized configs, tools, tests, tables,
reports, manifests, digests, and decision files.

Do not draft or create the next runbook. Record recommended next action
categories only.
```

## Required Inputs

Use these committed inputs when present:

```text
AGENTS.md
PROCESS.md
docs/architecture/system-design.md
docs/experiments/phase-1-local-algorithm-bakeoff-runbook.md
docs/experiments/phase-1-three-repo-paid-validation-runbook.md
docs/experiments/phase-1-blocked-split-missing-cell-supplement-paid-execution-runbook.md
docs/experiments/phase-1-blocked-split-supplement-fairness-and-gap-diagnostics-runbook.md
docs/experiments/phase-1-click-llm-assisted-source-context-repair-runbook.md

experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_candidate_designs.json
experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_validation_results.json
experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_ablation.json
experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_paid_readiness_gate.json

experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_task_table.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_split_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_baseline_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_source_quality_audit.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_metrics.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_score_tables_manifest.json

experiments/phase1_compiler/results/phase1_source_context_statement_hardening_split_feature_table.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_candidate_universe.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_candidate_splits.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_selected_split.json
experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_selected_split_plan.json
experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_adapter_stratified_metrics.json
experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_combined_score_tables_manifest.json
experiments/phase1_compiler/results/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.json

experiments/phase1_compiler/results/phase1_click_llm_source_context_repair_quality_overlay.json
experiments/phase1_compiler/results/phase1_click_llm_source_context_repair_claim_boundary.json
experiments/phase1_compiler/results/phase1_click_llm_source_context_repair_decision.json

experiments/phase0_headroom/results/phase1_three_repo_paid_validation_*_score_table.csv
experiments/phase0_headroom/results/phase1_blocked_split_missing_cell_supplement_paid_execution_*_score_table.csv
experiments/phase0_headroom/results/workspace_usage_ledger.jsonl
experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
```

Useful implementation references:

```text
experiments/phase1_compiler/tools/phase1_local_algorithm_bakeoff.py
experiments/phase1_compiler/tools/phase1_blocked_split_redesign.py
experiments/phase1_compiler/tools/phase1_blocked_split_missing_cell_supplement_paid_execution.py
experiments/phase1_compiler/tools/phase1_blocked_split_supplement_fairness_gap_diagnostics.py
experiments/phase1_compiler/tests/test_phase1_local_algorithm_bakeoff.py
experiments/phase1_compiler/tests/test_phase1_blocked_split_redesign.py
experiments/phase1_compiler/tests/test_phase1_blocked_split_supplement_fairness_gap_diagnostics.py
```

If an input is missing or has moved, record that in the preflight report and
continue with available committed artifacts.

## Output Layout

Create a new no-paid analysis run under this prefix:

```text
phase1_retrospective_predictive_signal
```

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_retrospective_predictive_signal.yaml
  tools/
    phase1_retrospective_predictive_signal.py
  tests/
    test_phase1_retrospective_predictive_signal.py
  results/
    phase1_retrospective_predictive_signal_preflight.json
    phase1_retrospective_predictive_signal_universe.json
    phase1_retrospective_predictive_signal_window_plan.json
    phase1_retrospective_predictive_signal_design_registry.json
    phase1_retrospective_predictive_signal_selection_freeze.json
    phase1_retrospective_predictive_signal_score_join_manifest.json
    phase1_retrospective_predictive_signal_adapter_metrics.json
    phase1_retrospective_predictive_signal_baseline_comparison.json
    phase1_retrospective_predictive_signal_uncertainty.json
    phase1_retrospective_predictive_signal_claim_boundary.json
    phase1_retrospective_predictive_signal_decision.json
  reports/
    phase1_retrospective_predictive_signal_process.md
    phase1_retrospective_predictive_signal_universe.md
    phase1_retrospective_predictive_signal_window_plan.md
    phase1_retrospective_predictive_signal_design_registry.md
    phase1_retrospective_predictive_signal_adapter_metrics.md
    phase1_retrospective_predictive_signal_baseline_comparison.md
    phase1_retrospective_predictive_signal_uncertainty.md
    phase1_retrospective_predictive_signal_decision.md
```

Optional small CSV outputs may be added if useful:

```text
experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_*.csv
```

Committed artifacts must contain only sanitized task IDs, metadata buckets,
score-table references, pass/fail counts, rates, metrics, confidence labels,
and report summaries.

## Definitions

Use these terms consistently:

```text
analysis_universe:
  Frozen set of candidate tasks eligible for retrospective analysis before
  outcomes are loaded.

selection_freeze:
  Design-by-window task selections produced without terminal outcomes.

B_eval:
  Tasks selected as the benchmark estimator at a cutoff/window.

H_future:
  Tasks treated as later or held-out target work for the same repo/adapter.

prediction_error:
  Absolute or squared difference between B_eval pass rate and H_future pass
  rate for the same repo, adapter, design, and window.

retrospective_pseudo_future:
  A historical replay that uses already-committed paid outcomes and therefore
  supports traction evidence, not formal predictive validity.

true_rolling_origin_support:
  A stronger replay in which task timestamps and outcome coverage allow multiple
  cutoff-before / cutoff-after windows without using post-cutoff data for
  selection.
```

## Candidate Designs

At minimum, register these designs before outcomes are joined:

```text
repo_unweighted_same_budget:
  simple same-budget unweighted baseline

repo_stratified_by_target_profile:
  conservative mainline baseline

temporal_recent_baseline:
  recent pre-cutoff tasks predict later tasks

seeded_random_same_budget:
  multi-seed random baseline

coverage_constrained_unweighted:
  coverage-oriented unweighted candidate

block_randomized_stratified:
  Barcarolle-style blocked candidate, no weights

block_plus_shrinkage_weighted:
  research candidate; must report ESS, max weight, fallback mode

old_weighted_target_profile:
  negative-control/reference only, not promotable

completed_blocked_split_supplement:
  diagnostic design from the selected blocked split; label as post-hoc
  exploratory if it depends on prior outcome-aware history
```

The worker may add other candidates only if they are outcome-blind and clearly
marked as exploratory. Do not drop an unfavorable registered design after seeing
outcomes.

## Primary Metrics

Compute metrics by adapter first:

```text
MAE:
  mean absolute error between B_eval pass rate and H_future pass rate

RMSE:
  root mean squared error

signed_error:
  B_eval pass rate minus H_future pass rate

absolute_gap:
  absolute B_eval/H_future pass-rate gap

catastrophic_miss_rate:
  share of repo/window/design cells with absolute_gap > 0.15

baseline_delta_MAE:
  design MAE minus repo_stratified MAE

coverage:
  scoreable cell counts and non-scoreable counts by repo/adapter/window/design
```

Optional secondary metrics:

```text
Wilson or beta-binomial interval labels
bootstrap intervals over task blocks if enough support exists
NLL / Brier only if the estimator produces calibrated probabilities and sample
support is sufficient
equal-mix pooled metrics if preregistered before outcome join
```

## Claim Boundary

Allowed claims:

```text
retrospective_predictive_signal_analysis_completed
selection_freeze_outcome_blind
adapter_stratified_metrics_computed
baseline_comparison_completed
barcarolle_candidate_has_traction_signal
barcarolle_candidate_no_signal_found
analysis_underpowered
true_rolling_origin_support_too_sparse
pseudo_future_signal_only
future_preregistered_validation_recommended
no_paid_acut_cells_run
no_paid_llm_calls_run
```

Disallowed claims:

```text
predictive_validity_established
formal_preregistration_completed
new_paid_validation_completed
new_paid_acut_cells_run
new_paid_llm_calls_run
post_hoc_design_promoted_as_primary
outcome_informed_selection
H_future_used_as_target_profile
adapter_difference_is_unfair_by_default
model_only_superiority
followup_runbook_written_by_worker
```

## Step 0 - Preflight And Scope Check

Goal: prove the analysis is no-paid and can run without changing historical
outcomes.

Actions:

1. Read `AGENTS.md`, `PROCESS.md`, this runbook, and the required input
   artifacts.
2. Record branch, HEAD, date, Python version, and `uv --version`.
3. Record `git status --short --untracked-files=all` and `git diff --check`.
4. Classify dirty/untracked files. The known external-review bundle may remain
   untracked unless the user explicitly asks to package or remove it.
5. Confirm no paid ACUT or LLM calls are needed.
6. Confirm existing score tables will be read only after selection freeze.
7. Write preflight result and process report.

Acceptance:

- Preflight records branch, HEAD, dirty-tree classification, no-paid boundary,
  and required input availability.
- No paid calls have run.
- The report says this is retrospective signal evidence, not formal predictive
  validity.

Suggested commit:

```text
Record retrospective predictive signal preflight
```

## Step 1 - Analysis Universe

Goal: build the outcome-blind task universe.

Actions:

1. Load repaired source-quality metadata for attrs, boltons, and click.
2. Load candidate task metadata, time buckets, task-family buckets, source
   reservoirs, editable scope, statement digests, and split-design features.
3. Exclude tasks with unresolved source-quality blockers or hidden-oracle risks.
4. Record whether each task has any committed paid outcome coverage, but do not
   load terminal status or pass/fail at this step. If outcome coverage itself
   could leak design quality, treat it as a coverage constraint only and report
   the limitation.
5. Write a universe table with no terminal outcome fields.

Expected outputs:

```text
phase1_retrospective_predictive_signal_universe.json
phase1_retrospective_predictive_signal_universe.md
```

Acceptance:

- The universe includes attrs, boltons, and repaired click where available.
- Outcome/pass/fail fields are absent.
- Coverage limitations are explicit.

Suggested commit:

```text
Build retrospective predictive signal universe
```

## Step 2 - Window And Cutoff Plan

Goal: decide whether true rolling-origin support exists and freeze the replay
windows before outcomes are loaded.

Actions:

1. Propose candidate cutoffs using task timestamps or time buckets only.
2. For each repo, compute pre-cutoff and post-cutoff task counts from metadata.
3. Require minimum support before accepting a true rolling-origin window:
   - at least 4 B_eval candidate tasks per repo/window;
   - at least 4 H_future candidate tasks per repo/window;
   - at least one scoreable outcome available per task/adapter after the later
     score join, if coverage metadata can be checked without terminal status.
4. If true rolling support is too sparse, freeze a pseudo-future plan based on
   existing B_eval/H_future split labels and task-time ordering, and label it
   `retrospective_pseudo_future`.
5. Do not inspect pass/fail outcomes while choosing windows.

Expected outputs:

```text
phase1_retrospective_predictive_signal_window_plan.json
phase1_retrospective_predictive_signal_window_plan.md
```

Acceptance:

- The plan states whether analysis mode is `true_rolling_origin`,
  `retrospective_pseudo_future`, or `mixed`.
- Cutoffs/windows are frozen before score tables are joined.
- Sparse support is reported, not hidden.

Suggested commit:

```text
Freeze retrospective predictive signal windows
```

## Step 3 - Design Registry And Selection Freeze

Goal: register all designs and freeze their task selections without outcomes.

Actions:

1. Register required baselines and candidate designs.
2. For each repo/window/design, produce B_eval and H_future selections using
   metadata only.
3. For seeded designs, preregister seeds before score join. Use multiple seeds
   where feasible and record every seed.
4. For weighted designs, compute weights, ESS, max weight, and fallback mode
   without terminal outcomes.
5. For post-hoc historical designs such as the completed blocked split
   supplement, label claim boundary as exploratory and do not let them become
   the primary formal claim.
6. Write the selection freeze artifact. After this step, do not change task
   selection, weights, seeds, cutoffs, or design inclusion because of outcomes.

Expected outputs:

```text
phase1_retrospective_predictive_signal_design_registry.json
phase1_retrospective_predictive_signal_selection_freeze.json
phase1_retrospective_predictive_signal_design_registry.md
```

Acceptance:

- Every design records inputs, seeds, fallback rules, weights, and whether it
  is baseline, candidate, or negative control.
- `outcome_fields_used_for_selection` is empty for every promoted design.
- Any post-hoc design is labeled as diagnostic only.

Suggested commit:

```text
Freeze retrospective predictive signal designs
```

## Step 4 - Score Join Manifest

Goal: join existing paid outcomes only after the selection freeze.

Actions:

1. Load score tables from the committed manifests.
2. Join terminal statuses, pass/fail outcomes, scoreability, adapter id, split
   labels, cost, and latency to the frozen selections.
3. Preserve non-scoreable cells explicitly. Do not coerce `invalid_output` into
   pass or fail unless a preregistered sensitivity analysis says so.
4. Record reused vs newly paid outcome provenance where available.
5. Confirm no paid outcomes, score tables, or completed decisions were changed.

Expected outputs:

```text
phase1_retrospective_predictive_signal_score_join_manifest.json
```

Acceptance:

- Every joined score row points to a committed score table or manifest.
- Non-scoreable denominators are explicit.
- The join happens after selection freeze, as recorded by timestamps or process
  report ordering.

Suggested commit:

```text
Join retrospective predictive signal score tables
```

## Step 5 - Adapter-Stratified Metrics

Goal: compute prediction errors by adapter first.

Actions:

1. For each adapter/repo/window/design, compute B_eval pass rate, H_future pass
   rate, signed error, absolute error, scoreable counts, and non-scoreable
   counts.
2. Compute MAE, RMSE, catastrophic miss rate, and coverage by adapter/design.
3. Keep Codex and Kilo separate. If pooled metrics are computed, mark them as
   secondary equal-mix diagnostics.
4. Include sensitivity labels for the known Codex `attrs__v2__157`
   `invalid_output` if it enters any selected denominator.
5. Do not describe adapter pass-rate differences as model-only superiority.

Expected outputs:

```text
phase1_retrospective_predictive_signal_adapter_metrics.json
phase1_retrospective_predictive_signal_adapter_metrics.md
```

Acceptance:

- Adapter-level metrics are the primary report.
- Pooled metrics, if any, are secondary and clearly labeled.
- Scoreability and non-scoreable cells are visible.

Suggested commit:

```text
Compute retrospective adapter prediction metrics
```

## Step 6 - Baseline Comparison And Uncertainty

Goal: decide whether any Barcarolle candidate has traction signal beyond simple
baselines.

Actions:

1. Compare each candidate against:
   - `repo_stratified_by_target_profile`;
   - `repo_unweighted_same_budget`;
   - `temporal_recent_baseline`;
   - `seeded_random_same_budget`, where available.
2. Compute:
   - candidate MAE minus baseline MAE;
   - candidate catastrophic miss rate minus baseline miss rate;
   - count of repo/window/adapter slices where candidate improves or worsens;
   - whether improvement is driven by one repo, one adapter, or one window.
3. Add simple uncertainty labels:
   - `too_sparse`;
   - `directional_only`;
   - `stable_across_repos`;
   - `single_repo_driven`;
   - `candidate_worse_than_baseline`.
4. If sample size is too small for meaningful intervals, say so directly.
5. Keep the result as traction evidence unless a future runbook explicitly
   preregisters formal validation.

Expected outputs:

```text
phase1_retrospective_predictive_signal_baseline_comparison.json
phase1_retrospective_predictive_signal_uncertainty.json
phase1_retrospective_predictive_signal_baseline_comparison.md
phase1_retrospective_predictive_signal_uncertainty.md
```

Acceptance:

- The report leads with whether any candidate beats simple baselines.
- It identifies if evidence is negative, positive, mixed, or underpowered.
- It does not overstate statistical certainty.

Suggested commit:

```text
Compare retrospective predictive signal baselines
```

## Step 7 - Claim Boundary And Decision

Goal: turn the analysis into a project-facing decision.

Actions:

1. Write a claim-boundary artifact with one label:

```text
retrospective_signal_positive_directional
retrospective_signal_mixed_underpowered
retrospective_signal_negative_against_baselines
retrospective_signal_blocked_by_coverage
retrospective_signal_protocol_bug_found
```

2. Write a decision with:
   - analysis mode;
   - repos included;
   - adapters included;
   - number of windows;
   - candidate designs evaluated;
   - best baseline;
   - best Barcarolle candidate;
   - whether any candidate beats baseline;
   - whether result supports traction narrative;
   - whether future paid ACUT remains blocked by default;
   - recommended next action categories.
3. Update `PROCESS.md` only if the run changes the active claim boundary, paid
   boundary, mainline design, or recommended next action category.
4. Run focused tests and `git diff --check`.

Expected outputs:

```text
phase1_retrospective_predictive_signal_claim_boundary.json
phase1_retrospective_predictive_signal_decision.json
phase1_retrospective_predictive_signal_decision.md
```

Acceptance:

- The decision states whether the result is positive, mixed, negative,
  underpowered, or blocked.
- Predictive validity remains false unless a future preregistered validation
  actually establishes it.
- No follow-up runbook is drafted or created by the worker.
- Verification commands and results are recorded.

Suggested commit:

```text
Close retrospective predictive signal analysis
```

## Final Report Template

Use this structure in the closeout report:

```text
# Retrospective Predictive-Signal Decision

Decision label: ...

What happened: ...
Why it matters: ...
Action suggested next: ...

- Analysis mode:
- Repos included:
- Adapters included:
- Windows:
- Designs evaluated:
- Best simple baseline:
- Best Barcarolle candidate:
- Candidate beats baseline:
- MAE summary:
- Catastrophic miss summary:
- Support level:
- Paid ACUT cells:
- Paid LLM calls:
- Predictive validity established:
- PROCESS.md updated:

## Boundary

...

## Verification

- focused tests:
- relevant suite:
- git diff --check:
```
