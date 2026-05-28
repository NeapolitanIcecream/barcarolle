# Phase 1 Three-Repo Paid Validation Runbook

Status: paid execution runbook, 2026-05-28.

This runbook is for one dedicated Codex CLI session. Its job is to execute the
frozen three-repo paid-validation pilot package and write a bounded pilot
decision.

```text
Run the frozen attrs/boltons/click primary_pilot package through the configured
workspace ACUT adapters, import score/cost results, and evaluate the
preregistered repo_stratified pilot threshold.
```

Plain-language summary:

```text
The previous runbook prepared the package. This runbook is the paid run.

It may spend money, but only after local entry gates, endpoint checks, task
package inspection, and batch cost checks pass. It must not change the frozen
task list, split plan, baselines, thresholds, or primary design after seeing
paid outcomes.

Even if the pilot passes, this runbook should call the result pilot evidence,
not precision-target predictive validity.
```

## Paid Approval Boundary

This runbook may make paid ACUT solver calls only when the coordinating
user-facing session explicitly asks a worker to execute this paid runbook and
approves the selected paid batch option and budget cap.

Default approved option for execution, if the user asks to run this runbook:

```text
option: primary_pilot
planned unique tasks: 60
planned cells: 120
planned adapters: codex_workspace, kilo_workspace
estimated cost range: USD 37.21 lower / USD 60.00 conservative
hard cost cap: USD 75
```

If the worker cannot prove that this approval applies to the current execution,
stop before paid calls and write a blocker report. Do not infer paid approval
from this document merely existing.

Do not draft or create a follow-up runbook. Record recommended next action
categories only.

## Starting Point

The local packaging run ended with:

```text
decision: pilot_package_ready_but_precision_target_not_claimable
entry_gate_status: ready_for_paid_validation_runbook
paid_ready: true
predictive_validity_established: false

release eligible:
  attrs:   31
  boltons: 35
  click:   30

primary design: repo_stratified
primary score: unweighted_pass_rate_by_repo_split_then_pooled_summary
recommended paid batch: primary_pilot
primary_pilot: 60 tasks, 120 cells
```

Frozen split counts:

```text
attrs:   B_eval 16 / H_future 15
boltons: B_eval 18 / H_future 17
click:   B_eval 15 / H_future 15
```

The recommended paid batch is a subset of the 96-task package:

```text
attrs:   20 tasks
boltons: 20 tasks
click:   20 tasks
adapters: codex_workspace, kilo_workspace
cells: 60 tasks * 2 adapters = 120 cells
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-three-repo-paid-validation-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md first. Use uv for
repo-local Python tooling. Follow AGENTS.md step-level acceptance and commit
requirements: after each step, or after each small group of tightly related
steps, commit the changed files with an appropriately scoped commit.

Paid execution approval is granted for option=primary_pilot only if the
coordinating session explicitly provided that approval when launching this
worker. If approval is absent or ambiguous, stop before paid calls and write a
blocker. If approval is present, the hard cost cap is USD 75 unless the
coordinating session provides a lower cap.

Main goal: execute the frozen three-repo primary_pilot package from
phase1_three_repo_paid_readiness_packaging_20260528. The primary design is
repo_stratified. The old weighted design is diagnostic only. Do not change task
selection, split assignment, primary design, baselines, thresholds, or
non-scoreable handling after seeing outcomes.

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

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
Codex/Kilo logs, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, raw target diffs, raw test patches, raw GitHub API
responses, or large raw outputs. Commit only small sanitized configs, tools,
tests, score tables, metrics, cost summaries, reports, manifests, digests, and
decision files. Raw harness outputs must remain under ignored paths.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. Whether the next paid batch should continue or stop.

Do not draft or create the next runbook.
```

## Required Inputs

Use these committed inputs:

```text
AGENTS.md
docs/architecture/system-design.md
docs/experiments/phase-1-three-repo-paid-readiness-packaging-runbook.md

experiments/phase1_compiler/configs/phase1_three_repo_paid_readiness_packaging.yaml
experiments/phase1_compiler/configs/phase1_three_repo_paid_validation_thresholds.yaml
experiments/phase1_compiler/configs/phase1_three_repo_release_selection.yaml

experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_task_table.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_supply_snapshot.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_source_quality_audit.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_split_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_baseline_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_threshold_preregistration.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_power_cost_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_entry_gate.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_decision.json

experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
experiments/phase0_headroom/tools/workspace_acut_run.py
experiments/phase0_headroom/tools/workspace_usage_import.py
```

Use these source certification artifacts to build task packages, if the
packaging task table does not already contain all fields needed by workspace
ACUT tooling:

```text
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_attempts.json
experiments/phase1_compiler/results/phase1_attrs_source_repair_release_eligibility_overlay.json
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_certification_attempts.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_task_table.json
```

## Frozen Primary Pilot Task IDs

Run exactly these 60 unique tasks for `primary_pilot`, with both configured
workspace adapters:

```text
attrs__v2__207
attrs__v2__264
attrs__v2__187
attrs__v2__044
attrs__v2__253
attrs__v2__237
attrs__v2__250
attrs__v2__227
attrs__v2__048
attrs__v2__223
attrs__v2__261
attrs__v2__206
attrs__v2__196
attrs__v2__052
attrs__v2__056
attrs__v2__220
attrs__v2__215
attrs__v2__158
attrs__v2__202
attrs__v2__235
boltons__v2__135
boltons__v2__148
boltons__v2__229
boltons__v2__142
boltons__v2__068
boltons__v2__133
boltons__v2__147
boltons__v2__093
boltons__v2__007
boltons__v2__155
boltons__v2__141
boltons__v2__163
boltons__v2__170
boltons__v2__144
boltons__v2__091
boltons__v2__086
boltons__v2__006
boltons__v2__087
boltons__v2__164
boltons__v2__140
click__third__275
click__third__045
click__third__203
click__third__217
click__third__271
click__third__204
click__third__278
click__third__201
click__third__274
click__third__200
click__third__208
click__third__213
click__third__216
click__third__250
click__third__206
click__third__199
click__third__166
click__third__050
click__third__205
click__third__238
```

If any task id cannot be loaded from the frozen packaging artifacts, stop
before paid calls.

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

## Claim Boundary

Allowed claims after this runbook:

```text
three_repo_paid_validation_run
primary_pilot_paid_cells_completed
repo_stratified_primary_metrics_recorded
baseline_metrics_recorded
old_weighted_design_diagnostic_recorded
observed_or_conservative_cost_accounting_recorded
policy_violation_rate_recorded
scoreability_rate_recorded
pilot_threshold_met
pilot_threshold_not_met
pilot_result_insufficient_precision
paid_validation_blocked_with_precise_reason
```

Disallowed claims unless a later precision-target run supports them:

```text
precision_target_predictive_validity_established
production_benchmark_ranking
old_weighted_design_promoted_to_primary_after_outcomes
paid_precision_replication_completed
H_future_used_as_target_profile
hidden_oracle_informed_selection
post_hoc_release_changed_after_outcomes
old_paid_result_repaired
raw_oracle_exposed_to_solver
```

Interpretation rules:

- `verified_pass` and `verified_fail` are scoreable ACUT outcomes.
- `policy_violation`, `invalid_output`, `acut_harness_error`,
  `harness_error`, `timeout`, and endpoint/tooling failures are non-scoreable
  or boundary failures.
- Non-scoreable cells are excluded from pass-rate denominators, but they count
  against the 0.95 scoreability gate.
- Primary success requires the preregistered primary absolute gap `<= 0.15`.
- Even if success criteria pass, label the result pilot-grade unless a later
  precision-target design is preregistered and run.

## Frozen Thresholds

Use the packaging preregistration:

```text
policy_violations_max: 0
paid_endpoint_required: LLM_BASE_URL + LLM_API_KEY
raw_oracle_exposure_allowed: false
minimum_scoreability_rate: 0.95
cost_latency_accounting_required: true
primary_gap_threshold: 0.15
primary design: repo_stratified
old weighted design: diagnostic_only
```

Failure is any policy violation, raw oracle exposure, endpoint noncompliance,
scoreability below 0.95, incomplete cost/latency accounting, or primary gap
above 0.15.

## Budget And Batch Policy

Use the packaging estimate:

```text
primary_pilot planned cells: 120
expected cost range: USD 37.21 lower / USD 60.00 conservative
hard cost cap: USD 75
paid ACUT concurrency: 1
cross-harness paid parallelism: disabled
```

Run paid cells sequentially by small batch. Suggested batch schedule:

```text
Batch 0: no-paid tooling and dry package inspection
Batch 1: paid smoke, 3 tasks * 2 adapters = 6 cells
Batch 2: complete small_pilot remaining tasks, 15 tasks * 2 adapters = 30 cells
Batch 3: attrs primary_pilot remainder, 14 tasks * 2 adapters = 28 cells
Batch 4: boltons primary_pilot remainder, 14 tasks * 2 adapters = 28 cells
Batch 5: click primary_pilot remainder, 14 tasks * 2 adapters = 28 cells
```

The batch task lists must be generated from the frozen `primary_pilot` task ids
and split assignments. Do not add tasks after terminal outcomes are known.

Stop before the next paid batch if any of these fires:

```text
endpoint_proof_missing
projected_total_cost_exceeds_approved_cap
observed_or_conservative_cost_cannot_be_reconciled
scoreability_rate_below_0.95_after_batch
policy_violation_count_above_0
raw_oracle_exposure_detected
cost_latency_accounting_incomplete
frozen_package_integrity_check_failed
```

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_three_repo_paid_validation.yaml
  tools/
    phase1_three_repo_paid_validation.py
  tests/
    test_phase1_three_repo_paid_validation.py
  results/
    phase1_three_repo_paid_validation_preflight.json
    phase1_three_repo_paid_validation_tooling_check.json
    phase1_three_repo_paid_validation_entry_gate.json
    phase1_three_repo_paid_validation_batch_plan.json
    phase1_three_repo_paid_validation_batch_1_smoke.json
    phase1_three_repo_paid_validation_batch_2_small_pilot_complete.json
    phase1_three_repo_paid_validation_batch_3_attrs_remainder.json
    phase1_three_repo_paid_validation_batch_4_boltons_remainder.json
    phase1_three_repo_paid_validation_batch_5_click_remainder.json
    phase1_three_repo_paid_validation_cost_reconciliation.json
    phase1_three_repo_paid_validation_score_tables_manifest.json
    phase1_three_repo_paid_validation_metrics.json
    phase1_three_repo_paid_validation_baseline_comparison.json
    phase1_three_repo_paid_validation_decision.json
  reports/
    phase1_three_repo_paid_validation_process.md
    phase1_three_repo_paid_validation_preflight.md
    phase1_three_repo_paid_validation_tooling_check.md
    phase1_three_repo_paid_validation_entry_gate.md
    phase1_three_repo_paid_validation_batch_plan.md
    phase1_three_repo_paid_validation_batch_status.md
    phase1_three_repo_paid_validation_cost_reconciliation.md
    phase1_three_repo_paid_validation_metrics.md
    phase1_three_repo_paid_validation_baseline_comparison.md
    phase1_three_repo_paid_validation_decision.md

experiments/phase0_headroom/
  configs/
    phase1_three_repo_paid_validation_workspace_matrix.yaml
  results/
    phase1_three_repo_paid_validation_*_score_table.csv
    phase1_three_repo_paid_validation_*_matrix.json
    workspace_usage_ledger.jsonl
    workspace_cost_reconciliation.json
```

Raw outputs must stay under ignored paths:

```text
experiments/phase0_headroom/results/raw/
experiments/phase0_headroom/workspaces/
experiments/phase0_headroom/external_repos/
experiments/phase1_compiler/tmp/three_repo_paid_validation/
```

Do not commit raw ACUT logs, raw prompts, raw completions, solver workspaces,
verifier workspaces, target repo clones, caches, or secret-bearing artifacts.

## Step 0 - Preflight And Approval Record

Goal: prove the paid run starts from a frozen, approved state.

Actions:

1. Read `AGENTS.md`, this runbook, and all required packaging artifacts.
2. Record branch, HEAD, date, Python version, `uv --version`,
   `codex --version` if available, and `kilo --version` if available.
3. Record `git status --short --branch` and `git diff --check`.
4. Record explicit paid approval:
   - approved option;
   - approved cost cap;
   - planned adapters;
   - planned cells.
5. Verify endpoint variables without printing values.
6. Verify packaging entry gate is `ready_for_paid_validation_runbook`.
7. Write preflight result and report.

Acceptance:

- Paid approval is recorded for this execution.
- Endpoint variables are present.
- Entry gate is ready.
- No paid calls have run before preflight.
- Dirty/untracked files are classified.

Stop if:

- paid approval is absent or ambiguous;
- endpoint variables are missing;
- packaging entry gate is not ready;
- package artifacts are missing or modified unexpectedly.

Commit:

```text
Record three-repo paid validation preflight
```

## Step 1 - Tooling And Frozen Package Loader

Goal: prove the workspace ACUT runner can load the frozen three-repo package.

Actions:

1. Add or update a small paid-validation wrapper only if existing tooling
   cannot load the three-repo package directly.
2. Inspect all 60 `primary_pilot` task ids.
3. Verify for each package:
   - solver workspace starts at base commit;
   - solver-visible statement exists;
   - hidden oracle is not in solver-visible material;
   - editable and non-editable path policy is enforceable;
   - split label and repo id match frozen split plan;
   - adapter config requires `LLM_BASE_URL` and `LLM_API_KEY`.
4. Add focused tests for package loading and batch-plan generation.
5. Do not run paid ACUT cells in this step.

Expected outputs:

```text
phase1_three_repo_paid_validation_tooling_check.json
phase1_three_repo_paid_validation_tooling_check.md
```

Acceptance:

- All 60 task ids are loadable.
- Both adapters are resolvable.
- A no-paid dry inspection passes.
- Focused tests pass.

Commit:

```text
Add three-repo paid validation tooling check
```

## Step 2 - Entry Gate And Batch Plan

Goal: freeze execution batches before paid outcomes exist.

Actions:

1. Generate the exact paid matrix:
   - task id;
   - repo;
   - split;
   - adapter;
   - batch id;
   - result prefix.
2. Generate score-table prefixes for B_eval/H_future by repo and/or a unified
   manifest that downstream metrics can read without ambiguity.
3. Check all non-paid gates:
   - approval present;
   - endpoint variables present;
   - package integrity passes;
   - source-quality audit still passes;
   - thresholds frozen;
   - cost cap recorded;
   - no raw logs/workspaces staged.
4. Do not run paid cells.

Expected outputs:

```text
phase1_three_repo_paid_validation_entry_gate.json
phase1_three_repo_paid_validation_batch_plan.json
phase1_three_repo_paid_validation_entry_gate.md
phase1_three_repo_paid_validation_batch_plan.md
```

Acceptance:

- Planned cells equal 120.
- Batch plan is deterministic and complete.
- Entry gate status is `ready_for_paid_batches`.

Commit:

```text
Freeze three-repo paid validation batch plan
```

## Step 3 - Paid Batch 1 Smoke

Goal: spend a small amount first and validate operational health.

Actions:

1. Run exactly 3 tasks, one per repo, with both adapters: 6 cells.
2. Store raw outputs only under ignored paths.
3. Import score rows and usage/cost records.
4. Check:
   - endpoint compliance evidence;
   - policy violations;
   - scoreability;
   - raw oracle exposure;
   - cost accounting.
5. Stop before Batch 2 if any stop condition fires.

Expected outputs:

```text
phase1_three_repo_paid_validation_batch_1_smoke.json
phase1_three_repo_paid_validation_batch_status.md
```

Acceptance:

- 6 planned cells are accounted for as scoreable or preregistered
  non-scoreable.
- Cost/usage is reconciled or a blocker is written.
- Continue/stop decision is explicit.

Commit:

```text
Record three-repo paid validation smoke batch
```

## Step 4 - Paid Batch 2 Small Pilot Completion

Goal: complete the 18-task small pilot if smoke is clean.

Actions:

1. Run the remaining 15 small-pilot tasks with both adapters: 30 cells.
2. Import score rows and usage/cost records.
3. Recompute cumulative scoreability, policy, and cost gates.
4. Stop before Batch 3 if any stop condition fires.

Expected outputs:

```text
phase1_three_repo_paid_validation_batch_2_small_pilot_complete.json
phase1_three_repo_paid_validation_batch_status.md
```

Acceptance:

- 36 cumulative cells are accounted for.
- A preliminary small-pilot status is recorded as interim evidence only.
- No final predictive claim is made yet.

Commit:

```text
Record three-repo paid validation small pilot batch
```

## Step 5 - Paid Batches 3-5 Primary Pilot Remainder

Goal: complete the frozen 120-cell primary pilot if gates remain clean.

Run these batches sequentially, committing after each batch:

```text
Batch 3: attrs primary_pilot remainder, 28 cells
Batch 4: boltons primary_pilot remainder, 28 cells
Batch 5: click primary_pilot remainder, 28 cells
```

After every batch:

1. Import score rows and usage/cost records.
2. Recompute cumulative gates.
3. Check projected total cost against the approved cap.
4. Stop before the next batch if any stop condition fires.

Expected outputs:

```text
phase1_three_repo_paid_validation_batch_3_attrs_remainder.json
phase1_three_repo_paid_validation_batch_4_boltons_remainder.json
phase1_three_repo_paid_validation_batch_5_click_remainder.json
phase1_three_repo_paid_validation_batch_status.md
```

Acceptance:

- Every completed batch has a sanitized status artifact.
- If all batches complete, 120 planned cells are accounted for.
- If stopped early, the blocker is precise and no later batch is run.

Commits:

```text
Record three-repo paid validation attrs batch
Record three-repo paid validation boltons batch
Record three-repo paid validation click batch
```

## Step 6 - Cost Reconciliation And Score Table Manifest

Goal: make paid usage auditable before interpreting scores.

Actions:

1. Reconcile workspace usage ledger and cost summaries.
2. Record observed, conservative, and unresolved cost amounts.
3. Build a score-table manifest listing:
   - result prefixes;
   - repo/split/adapter coverage;
   - planned cells;
   - completed cells;
   - scoreable cells;
   - non-scoreable cells by taxonomy.
4. Verify raw logs remain ignored and uncommitted.

Expected outputs:

```text
phase1_three_repo_paid_validation_cost_reconciliation.json
phase1_three_repo_paid_validation_score_tables_manifest.json
phase1_three_repo_paid_validation_cost_reconciliation.md
```

Acceptance:

- Cost/latency accounting is complete or the result is blocked.
- Score-table manifest covers all attempted cells.

Commit:

```text
Reconcile three-repo paid validation cost and score tables
```

## Step 7 - Metrics And Baseline Comparison

Goal: evaluate exactly the preregistered metrics.

Actions:

1. Compute primary `repo_stratified` metrics:
   - per-repo B_eval pass rate;
   - per-repo H_future pass rate;
   - per-repo absolute gap;
   - pooled B_eval/H_future absolute gap;
   - scoreability rate;
   - policy violation count;
   - endpoint compliance status;
   - cost/latency accounting status.
2. Compute frozen baselines/diagnostics:
   - repo_unweighted_same_budget;
   - repo_stratified_same_budget;
   - temporal_recent_baseline;
   - block_randomized_stratified_candidate;
   - old_weighted_design diagnostic only.
3. Do not promote a secondary/diagnostic design to primary after seeing
   outcomes.
4. Label precision honestly:
   - pilot_threshold_met;
   - pilot_threshold_not_met;
   - pilot_result_insufficient_precision;
   - blocked.

Expected outputs:

```text
phase1_three_repo_paid_validation_metrics.json
phase1_three_repo_paid_validation_baseline_comparison.json
phase1_three_repo_paid_validation_metrics.md
phase1_three_repo_paid_validation_baseline_comparison.md
```

Acceptance:

- Metrics apply the frozen threshold rules.
- Non-scoreable handling follows preregistration.
- Old weighted design is diagnostic only.

Commit:

```text
Compute three-repo paid validation metrics
```

## Step 8 - Decision And Closeout

Goal: write a clear pilot result or blocker.

Actions:

1. Write final decision artifacts.
2. Answer these research questions:

```text
RQ1: Did all planned primary_pilot cells complete?
RQ2: What was the scoreability rate?
RQ3: Were endpoint, policy, raw-oracle, and cost-accounting gates clean?
RQ4: What are the per-repo and pooled primary gaps?
RQ5: Did the preregistered pilot threshold pass?
RQ6: How did baselines and diagnostics compare, without changing the primary?
RQ7: What did the run cost?
RQ8: Is predictive validity established, pilot-only, failed, or blocked?
```

3. Record completed steps, commits made during the run, tests run, and known
   blockers.
4. Do not draft a follow-up runbook.

Expected outputs:

```text
phase1_three_repo_paid_validation_decision.json
phase1_three_repo_paid_validation_decision.md
```

Decision labels:

```text
three_repo_paid_pilot_threshold_met
three_repo_paid_pilot_threshold_not_met
three_repo_paid_pilot_insufficient_precision
three_repo_paid_validation_blocked_before_paid_calls
three_repo_paid_validation_blocked_after_partial_run
```

Acceptance:

- The report states clearly whether paid cells ran.
- The report does not claim precision-target predictive validity.
- The report explains the result in simple language.

Commit:

```text
Close three-repo paid validation run
```

## Verification

At minimum, run:

```bash
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_three_repo_paid_validation.py -q
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q
git diff --check
git status --short --untracked-files=all
```

If the full test suite is too slow or blocked, run focused tests plus the
nearest related tests and record the reason.

## Final Reporting Template

The final worker summary should be short and in simple Chinese:

```text
这次 runbook 是 paid validation，使用冻结的 attrs/boltons/click primary_pilot。

结果：
- planned cells: N
- completed cells: N
- scoreable cells: N
- scoreability rate: X
- policy violations: N
- raw oracle exposure: yes/no
- endpoint compliance: pass/fail
- cost: $X observed/conservative
- primary design: repo_stratified
- primary gap: X
- threshold <= 0.15: pass/fail

解释：
- predictive validity 是否成立：不能/只能说 pilot evidence/blocked。
- old weighted design 只作为 diagnostic，不作为主结论。

没有提交 raw logs、raw prompts、raw completions、solver workspaces、verifier
workspaces 或 secrets。
```

