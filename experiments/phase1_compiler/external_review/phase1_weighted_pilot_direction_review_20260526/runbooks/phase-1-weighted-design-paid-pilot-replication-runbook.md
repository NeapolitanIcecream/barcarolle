# Phase 1 Weighted Design Paid Pilot Replication Runbook

Status: implementation runbook, 2026-05-26.

This runbook is for one dedicated Codex CLI session. Its job is to execute the
frozen pilot-grade paid replication package produced by the pre-paid
replication readiness work, import the paid results, compare the weighted
Barcarolle design against local baselines, and write a bounded pilot decision.

Paid pilot approval is granted by the coordinating session for this runbook.
The worker does not need to ask for another user confirmation before paid
cells, but it must pass the local entry gates, endpoint checks, package
inspection, cost caps, and scoreability gates before and between paid batches.

Do not draft or create a follow-up runbook. Record recommended next actions in
the final decision and closeout reports only.

## Starting Point

Previous local readiness decision:

```text
run_id: phase1_pre_paid_replication_20260526
entry_status: ready_for_paid_replication
replication_grade: pilot_grade_ready_not_precision_target
primary_release_candidate_id: barcarolle_weighted_time_family_matched
recommended_with_baselines_cells: 44
precision_target_cells: 156
```

Primary threshold:

```text
primary rule:
  For each preregistered repo or repo-family stratum,
  abs(B_eval_predicted_pass_rate - H_future_observed_pass_rate) <= 0.15.

scoreability gate:
  100% planned cells complete, or every missing cell follows the preregistered
  non-scoreable handling rule.

policy gate:
  hidden-oracle access, prohibited test edits, policy violations, harness
  errors, and invalid outputs must all be zero for primary validity claims.
```

This runbook can produce a pilot result. It must not claim precision-target
predictive validity because the frozen package is underpowered for the
precision half-width target.

## Frozen Paid Pilot Package

Run the union of the primary release and the two new local baselines. Do not
rerun the historical reference release.

Primary release:

```text
barcarolle_weighted_time_family_matched
```

Local baselines:

```text
repo_unweighted_same_budget
repo_stratified_by_target_profile
```

Historical reference, not rerun:

```text
prior_statement_hardened_release_as_historical_reference
```

Unique paid task set for this pilot:

```text
attrs__hist__009
attrs__hist__010
attrs__hist__032
attrs__hist__033
attrs__hist__035
attrs__hist__036
attrs__hist__039
attrs__hist__041
attrs__hist__045
attrs__hist__047
boltons__hist__006
boltons__hist__007
boltons__hist__013
boltons__hist__014
boltons__hist__017
boltons__hist__019
boltons__hist__020
boltons__hist__024
boltons__hist__025
boltons__hist__026
boltons__hist__028
boltons__hist__031
```

Planned adapters:

```text
codex_workspace
kilo_workspace
```

Planned cells:

```text
22 tasks * 2 adapters = 44 cells
```

## Required Inputs

Use these committed inputs:

```text
AGENTS.md
docs/architecture/system-design.md
experiments/phase1_compiler/configs/phase1_pre_paid_replication_release_selection.yaml
experiments/phase1_compiler/results/phase1_pre_paid_replication_decision.json
experiments/phase1_compiler/results/phase1_pre_paid_replication_entry_gate.json
experiments/phase1_compiler/results/phase1_pre_paid_replication_release_candidates.json
experiments/phase1_compiler/results/phase1_pre_paid_replication_baseline_plan.json
experiments/phase1_compiler/results/phase1_pre_paid_replication_threshold_preregistration.json
experiments/phase1_compiler/results/phase1_pre_paid_replication_target_profiles.json
experiments/phase1_compiler/results/phase1_pre_paid_replication_statement_quality_gate.json
experiments/phase1_compiler/results/phase1_pre_paid_replication_candidate_inventory.json
experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_certified_tasks.jsonl
experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
experiments/phase0_headroom/tools/workspace_acut_run.py
experiments/phase0_headroom/tools/workspace_usage_import.py
```

Historical reference inputs:

```text
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_paid_metrics.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_paid_decision.json
experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_attrs_b_eval_score_table.csv
experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_attrs_h_future_score_table.csv
experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_boltons_b_eval_score_table.csv
experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_boltons_h_future_score_table.csv
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-weighted-design-paid-pilot-replication-runbook.md.

Work in the repository root. Read AGENTS.md first. Use uv for repo-local Python
tooling. Make a cohesive git commit after every completed step that changes
files. Do not batch unrelated steps into one commit. If a step only records
state, commit the small sanitized report/result update for that step. Do not
push unless the user explicitly asks.

Paid pilot approval has been granted by the coordinating session for this
runbook. You may run the frozen paid pilot cells only after all local entry
gates pass. Every paid LLM or ACUT call must use LLM_BASE_URL plus LLM_API_KEY.
If either variable is missing in the worker shell, source ~/.zshrc and check
again before making any paid call. Do not fall back to local Codex/ChatGPT
subscription auth, OPENAI_API_KEY, OpenRouter variables, or provider-specific
fallback variables.

Run only the frozen pilot package from
experiments/phase1_compiler/results/phase1_pre_paid_replication_release_candidates.json
and experiments/phase1_compiler/configs/phase1_pre_paid_replication_release_selection.yaml.
The paid task set is the union of barcarolle_weighted_time_family_matched,
repo_unweighted_same_budget, and repo_stratified_by_target_profile. Do not
rerun the prior_statement_hardened_release_as_historical_reference cells. Do
not change frozen task selection, split assignment, weights, thresholds, or
baseline definitions after terminal outcomes are known.

Keep Barcarolle on the benchmark/compiler side of the ACUT boundary. Barcarolle
may prepare clean solver workspaces, invoke configured ACUT workspace adapters,
capture final git diffs, replay those diffs in fresh verifier workspaces,
inject private oracle material only in verifier workspaces, and record sanitized
results. Do not implement Codex, Kilo, or another ACUT harness.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
Codex/Kilo logs, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, raw GitHub API responses, raw target diffs, or
large raw outputs. Commit only small sanitized configs, tools, tests, score
tables, cost summaries, reports, manifests, digests, and decision files. Raw
harness outputs must remain under ignored paths.

Run paid cells sequentially by small batch. Import or summarize usage after
every paid batch. Stop before the next paid batch if scoreability, policy,
endpoint, package inspection, or cost accounting is blocked.

Do not draft or create the next runbook. Record recommended next actions and
suggested follow-up categories only.
```

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
weighted_design_paid_pilot_run
weighted_design_paid_pilot_cells_completed
weighted_design_score_table_imported
weighted_vs_unweighted_baseline_metrics_recorded
weighted_vs_stratified_baseline_metrics_recorded
historical_reference_compared_without_rerun
observed_or_conservative_cost_accounting_recorded
policy_violation_rate_recorded
pilot_threshold_met
pilot_threshold_not_met
pilot_result_insufficient_precision
paid_pilot_blocked_with_precise_reason
```

Disallowed claims unless explicitly supported and scoped:

```text
precision_target_predictive_validity_established
production_benchmark_ranking
paid_precision_replication_completed
historical_reference_rerun_as_new_validation
H_future_used_as_target_profile
hidden_oracle_informed_selection
post_hoc_release_changed_after_outcomes
old_paid_result_repaired
generated_statement_is_scoreable_result
```

Interpretation rules:

- `verified_pass` and `verified_fail` are scoreable ACUT outcomes.
- `policy_violation`, `invalid_output`, `acut_harness_error`,
  `harness_error`, and `timeout` are non-scoreable or boundary failures.
- Historical reference results may be summarized, but they must not be merged
  into new pilot score tables.
- If the 0.15 gap threshold is met, state this as pilot evidence only.
- If precision half-width remains too wide, report `pilot_result_insufficient_precision`.

## Budget And Batch Policy

Use the pre-paid readiness estimate:

```text
previous cost per 32 cells: USD 9.9235152
estimated cost per cell: USD 0.31010985
recommended pilot with baselines: 44 cells, about USD 13.644833
precision target: 156 cells, about USD 48.377137
```

Paid cells must run sequentially:

```text
total planned cells: 44
incremental hard cap for this runbook: USD 25
stop-before-next-batch projected total cap: USD 20
single batch projected cap: USD 6
paid ACUT concurrency: 1
cross-harness paid parallelism: disabled
```

Suggested batch order:

```text
Batch 1: smoke, 2 tasks * 2 adapters = 4 cells
Batch 2: remaining attrs primary/baseline-union tasks
Batch 3: first boltons primary/baseline-union tasks
Batch 4: remaining boltons primary/baseline-union tasks
```

The exact batch task lists may be generated deterministically from the frozen
pilot matrix. Do not add tasks after terminal outcomes are known.

Stop before the next paid batch if observed-or-conservative cost cannot be
bounded, if projected total cost exceeds the cap, or if scoreability/policy
gates fail.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_weighted_design_paid_pilot.yaml
  tools/
    phase1_weighted_design_paid_pilot.py
  tests/
    test_phase1_weighted_design_paid_pilot.py
  results/
    phase1_weighted_design_paid_pilot_preflight.json
    phase1_weighted_design_paid_pilot_tooling_check.json
    phase1_weighted_design_paid_pilot_entry_gate.json
    phase1_weighted_design_paid_pilot_batch_plan.json
    phase1_weighted_design_paid_pilot_integrity_audit.json
    phase1_weighted_design_paid_pilot_metrics.json
    phase1_weighted_design_paid_pilot_baseline_comparison.json
    phase1_weighted_design_paid_pilot_decision.json
  reports/
    phase1_weighted_design_paid_pilot_process.md
    phase1_weighted_design_paid_pilot_preflight.md
    phase1_weighted_design_paid_pilot_tooling_check.md
    phase1_weighted_design_paid_pilot_entry_gate.md
    phase1_weighted_design_paid_pilot_batch_plan.md
    phase1_weighted_design_paid_pilot_integrity_audit.md
    phase1_weighted_design_paid_pilot_metrics.md
    phase1_weighted_design_paid_pilot_baseline_comparison.md
    phase1_weighted_design_paid_pilot_decision.md
```

Add or update Phase 0 workspace ACUT artifacts:

```text
experiments/phase0_headroom/
  configs/
    phase1_weighted_design_paid_pilot_workspace_matrix.yaml
  results/
    phase1_weighted_design_paid_pilot_package_inspection.json
    phase1_weighted_design_paid_pilot_preflight.json
    phase1_weighted_design_paid_pilot_matrix.json
    phase1_weighted_design_paid_pilot_score_table.csv
    phase1_weighted_design_paid_pilot_metrics.json
    phase1_weighted_design_paid_pilot_cost_summary.json
    phase1_weighted_design_paid_pilot_cost_ledger.jsonl
    workspace_usage_ledger.jsonl
    workspace_cost_reconciliation.json
  reports/
    phase1_weighted_design_paid_pilot_package_inspection.md
    phase1_weighted_design_paid_pilot_preflight.md
    workspace_cost_usage_report.md
```

Raw outputs must stay under ignored paths:

```text
experiments/phase0_headroom/results/raw/
experiments/phase0_headroom/workspaces/
experiments/phase0_headroom/external_repos/
```

Do not overwrite prior paid validation artifacts:

```text
experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_*_score_table.csv
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_paid_*.json
```

## Required Commit Discipline

Every step below has a commit target. After a step produces or modifies files:

```text
git status --short
git diff --check
run the relevant scoped tests for the step
git add only the intended small sanitized files
git commit -m "<commit target>"
```

If a step only reads files and confirms no changes are needed, update the
process report in the next step that changes files. Do not create empty commits.

If the worktree already contains unrelated user changes, leave them untouched.
Do not revert unrelated files.

## Step 0: Preflight And Approval Record

Commit target:

```text
Record weighted design paid pilot preflight
```

Actions:

1. Read `AGENTS.md`, this runbook, the pre-paid replication decision, entry
   gate, release candidates, baseline plan, thresholds, target profiles,
   statement quality gate, and release selection config.
2. Record branch, HEAD, date, Python version, `uv --version`,
   `codex --version` if available, and `kilo --version` if available.
3. Record `git status --short --branch`, `git log --oneline -12`, and
   `git diff --check`.
4. Record SHA256 digests for all Required Inputs.
5. Verify:

```text
entry_status == ready_for_paid_replication
replication_grade == pilot_grade_ready_not_precision_target
primary_release_candidate_id == barcarolle_weighted_time_family_matched
baseline candidates include repo_unweighted_same_budget and repo_stratified_by_target_profile
historical reference is not rerun
planned unique task count == 22
planned adapter count == 2
planned cells == 44
selection_frozen_before_paid_replication == true
historical_paid_outcomes_used_for_selection == false
new paid ACUT cells for this release have not already run
followup_runbook_written_by_worker == false
```

6. Initialize `phase1_weighted_design_paid_pilot_process.md` with a work queue
   for all steps in this runbook.

Acceptance:

- Preflight JSON and report exist.
- Work queue lists every step and commit target.
- No paid ACUT cells have been run yet.
- The runbook records paid approval and the endpoint rule.

Verification:

```text
uv run python -m pytest experiments/phase1_compiler/tests -q
git diff --check
```

## Step 1: Build Frozen Pilot Matrix And Package Inspection

Commit target:

```text
Build weighted design paid pilot matrix
```

Actions:

1. Add or update deterministic tooling/config that converts frozen release
   candidates into `phase1_weighted_design_paid_pilot_workspace_matrix.yaml`.
2. The matrix must include exactly the 22 unique task ids from the union of:

```text
barcarolle_weighted_time_family_matched
repo_unweighted_same_budget
repo_stratified_by_target_profile
```

3. Do not include any tasks that appear only in:

```text
prior_statement_hardened_release_as_historical_reference
```

4. Run package inspection with the workspace ACUT runner without paid calls.
5. Verify every selected task package exists and that solver-facing statement
   digests match the frozen candidate inventory when such digests are present.
6. Verify no selected candidate is blocked by statement quality gate.

Acceptance:

- Matrix config exists and is deterministic.
- Package inspection status is `ready`.
- Selected task count is 22 and missing task count is 0.
- Historical reference tasks are excluded unless they also appear in a new local
  baseline, in which case their prior paid cells are still not reused as new
  scoreable outcomes.

Verification:

```text
uv run python experiments/phase0_headroom/tools/workspace_acut_run.py --root . inspect-packages --matrix-config experiments/phase0_headroom/configs/phase1_weighted_design_paid_pilot_workspace_matrix.yaml --result-prefix phase1_weighted_design_paid_pilot
uv run python -m pytest experiments/phase0_headroom/tools/test_workspace_acut_run.py experiments/phase1_compiler/tests/test_phase1_weighted_design_paid_pilot.py -q
git diff --check
```

## Step 2: Tooling, Endpoint, And Entry Gate

Commit target:

```text
Record weighted design paid pilot entry gate
```

Actions:

1. Check `LLM_BASE_URL` and `LLM_API_KEY` without printing values. Source
   `~/.zshrc` and check again if needed.
2. Confirm adapter config requires `LLM_BASE_URL` and `LLM_API_KEY` and has
   local subscription fallback disabled.
3. Run workspace ACUT preflight for both adapters:

```text
codex_workspace
kilo_workspace
```

4. Confirm command templates exist, required env is present, package inspection
   is ready, and no paid call has been made by preflight.
5. Record cost cap, planned cells, batch plan, and stop conditions.
6. If any adapter fails preflight, stop before paid calls and write
   `paid_pilot_blocked_before_paid_cells`.

Acceptance:

- Entry gate status is `ready_for_paid_pilot` or
  `blocked_before_paid_cells`.
- Endpoint proof is recorded without secrets.
- Both adapters are ready before paid calls begin.
- No paid cells have run before this step commits.

Verification:

```text
uv run python experiments/phase0_headroom/tools/workspace_acut_run.py --root . preflight --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml --adapter-id codex_workspace --matrix-config experiments/phase0_headroom/configs/phase1_weighted_design_paid_pilot_workspace_matrix.yaml --result-prefix phase1_weighted_design_paid_pilot
uv run python experiments/phase0_headroom/tools/workspace_acut_run.py --root . preflight --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml --adapter-id kilo_workspace --matrix-config experiments/phase0_headroom/configs/phase1_weighted_design_paid_pilot_workspace_matrix.yaml --result-prefix phase1_weighted_design_paid_pilot
uv run python -m pytest experiments/phase1_compiler/tests/test_phase1_weighted_design_paid_pilot.py -q
git diff --check
```

## Step 3: Run Paid Smoke Batch

Commit target:

```text
Run weighted design paid pilot smoke batch
```

Actions:

1. Select two preregistered tasks for smoke, one attrs and one boltons, from
   the frozen union matrix.
2. Run each smoke task with both adapters, 4 cells total.
3. Use the workspace ACUT runner with the frozen matrix config and result
   prefix `phase1_weighted_design_paid_pilot`.
4. Import or summarize usage and cost immediately after the batch.
5. Rebuild the score table and metrics from sanitized submissions/verifier
   results.
6. Stop before further paid work if:

```text
endpoint proof is missing
any raw output would need to be committed
cost cannot be bounded
policy gate fails
package/workspace setup fails
both smoke tasks are non-scoreable for infrastructure reasons
```

Acceptance:

- Exactly 4 smoke cells are scheduled unless a blocker is recorded.
- Score table and cost summary include the smoke cells.
- Raw outputs remain in ignored paths only.
- Process report records observed terminal statuses and cost after smoke.

Verification:

```text
uv run python experiments/phase0_headroom/tools/workspace_acut_run.py --root . run-matrix --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml --adapter-id codex_workspace --matrix-config experiments/phase0_headroom/configs/phase1_weighted_design_paid_pilot_workspace_matrix.yaml --result-prefix phase1_weighted_design_paid_pilot --task-id <attrs_smoke_task_id> --task-id <boltons_smoke_task_id>
uv run python experiments/phase0_headroom/tools/workspace_acut_run.py --root . run-matrix --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml --adapter-id kilo_workspace --matrix-config experiments/phase0_headroom/configs/phase1_weighted_design_paid_pilot_workspace_matrix.yaml --result-prefix phase1_weighted_design_paid_pilot --task-id <attrs_smoke_task_id> --task-id <boltons_smoke_task_id>
uv run python experiments/phase0_headroom/tools/workspace_acut_run.py --root . summarize --result-prefix phase1_weighted_design_paid_pilot
git diff --check
```

Replace `<attrs_smoke_task_id>` and `<boltons_smoke_task_id>` with task ids
written in the batch plan before running the commands.

## Step 4: Run Remaining Attrs Paid Cells

Commit target:

```text
Run weighted design paid pilot attrs cells
```

Actions:

1. Run all remaining attrs tasks in the frozen union matrix for both adapters.
2. Do not rerun smoke cells if the runner can reuse already completed
   submissions.
3. Import or summarize usage and cost after the batch.
4. Rebuild the score table and metrics.
5. Stop before boltons cells if cost or scoreability gates are blocked.

Acceptance:

- All planned attrs cells are complete or a preregistered blocker is recorded.
- No task outside the frozen union matrix was run.
- Cost summary and process report are updated.

Verification:

```text
uv run python experiments/phase0_headroom/tools/workspace_acut_run.py --root . run-matrix --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml --adapter-id codex_workspace --matrix-config experiments/phase0_headroom/configs/phase1_weighted_design_paid_pilot_workspace_matrix.yaml --result-prefix phase1_weighted_design_paid_pilot --task-id <remaining_attrs_task_id> ...
uv run python experiments/phase0_headroom/tools/workspace_acut_run.py --root . run-matrix --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml --adapter-id kilo_workspace --matrix-config experiments/phase0_headroom/configs/phase1_weighted_design_paid_pilot_workspace_matrix.yaml --result-prefix phase1_weighted_design_paid_pilot --task-id <remaining_attrs_task_id> ...
uv run python experiments/phase0_headroom/tools/workspace_acut_run.py --root . summarize --result-prefix phase1_weighted_design_paid_pilot
git diff --check
```

## Step 5: Run Remaining Boltons Paid Cells

Commit target:

```text
Run weighted design paid pilot boltons cells
```

Actions:

1. Run all remaining boltons tasks in the frozen union matrix for both adapters.
2. Do not rerun smoke cells if the runner can reuse already completed
   submissions.
3. Import or summarize usage and cost after the batch.
4. Rebuild the score table and metrics.
5. Stop and record a partial-run decision if cost, endpoint, scoreability, or
   policy gates fail.

Acceptance:

- All 44 planned cells are complete, or every missing/non-scoreable cell has a
  preregistered handling record.
- No task outside the frozen union matrix was run.
- Cost summary and process report are updated.

Verification:

```text
uv run python experiments/phase0_headroom/tools/workspace_acut_run.py --root . run-matrix --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml --adapter-id codex_workspace --matrix-config experiments/phase0_headroom/configs/phase1_weighted_design_paid_pilot_workspace_matrix.yaml --result-prefix phase1_weighted_design_paid_pilot --task-id <remaining_boltons_task_id> ...
uv run python experiments/phase0_headroom/tools/workspace_acut_run.py --root . run-matrix --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml --adapter-id kilo_workspace --matrix-config experiments/phase0_headroom/configs/phase1_weighted_design_paid_pilot_workspace_matrix.yaml --result-prefix phase1_weighted_design_paid_pilot --task-id <remaining_boltons_task_id> ...
uv run python experiments/phase0_headroom/tools/workspace_acut_run.py --root . summarize --result-prefix phase1_weighted_design_paid_pilot
git diff --check
```

## Step 6: Integrity Audit And Score Import

Commit target:

```text
Audit weighted design paid pilot score tables
```

Actions:

1. Validate that the score table contains exactly the planned task/adapter
   cells or a preregistered partial-run status.
2. Check:

```text
planned cells
completed cells
scoreable cells
terminal status counts
adapter ids
task ids
no prohibited test edits
no hidden-oracle access
no raw transcript paths committed
cost summary present
usage ledger or conservative cost accounting present
```

3. Verify historical reference score tables were not overwritten.
4. Verify old paid score tables were not merged into the new pilot score table.
5. Write integrity audit JSON and Markdown.

Acceptance:

- Integrity audit status is `pass`, `partial_paid_pilot`, or
  `blocked_with_precise_reason`.
- Any mismatch is machine-readable.
- The audit can reproduce task and cell counts from committed score tables.

Verification:

```text
uv run python experiments/phase1_compiler/tools/phase1_weighted_design_paid_pilot.py integrity-audit
uv run python -m pytest experiments/phase1_compiler/tests/test_phase1_weighted_design_paid_pilot.py -q
git diff --check
```

## Step 7: Compute Weighted And Baseline Metrics

Commit target:

```text
Compute weighted design paid pilot metrics
```

Actions:

1. Project the score table onto each frozen release candidate:

```text
barcarolle_weighted_time_family_matched
repo_unweighted_same_budget
repo_stratified_by_target_profile
```

2. For each candidate, compute:

```text
B_eval predicted pass rate
H_future observed pass rate
absolute B_eval/H_future gap
per-repo gaps
weighted pass rate when candidate weights are non-uniform
unweighted diagnostic pass rate
Wilson intervals by repo/split
adapter disagreement rate
terminal status counts
scoreable cell count
observed-or-conservative cost
```

3. Compare against the historical reference without rerunning it.
4. Apply the preregistered threshold:

```text
gap <= 0.15
scoreability gate
policy gate
precision label
```

5. Label precision honestly:

```text
pilot_threshold_met_but_precision_underpowered
pilot_threshold_not_met
pilot_result_insufficient_precision
paid_pilot_non_scoreable
```

Acceptance:

- Metrics JSON includes all primary and baseline candidates.
- Weighted and unweighted formulas are explicit.
- The report states whether weighted design improves over unweighted and
  stratified baselines on the pilot metrics.
- The report does not claim precision-target validity.

Verification:

```text
uv run python experiments/phase1_compiler/tools/phase1_weighted_design_paid_pilot.py metrics
uv run python -m pytest experiments/phase1_compiler/tests/test_phase1_weighted_design_paid_pilot.py -q
git diff --check
```

## Step 8: Baseline Comparison And Error Analysis

Commit target:

```text
Compare weighted design paid pilot baselines
```

Actions:

1. Write a baseline comparison report focused on:

```text
weighted design gap
unweighted baseline gap
stratified baseline gap
historical reference gap
which design best predicted H_future in the pilot
where each design failed by repo, task family, source kind, and adapter
```

2. Classify failures using sanitized score/verifier summaries only. Do not read
   raw ACUT transcripts or hidden verifier material.
3. Explain whether failures look like:

```text
task difficulty
remaining split mismatch
statement/source quality
adapter-specific behavior
small-N noise
policy/harness issue
```

4. Record whether the pilot result supports moving toward more local supply,
   more repos, precision-target replication, or bounded negative reporting.
   Do not write a new runbook.

Acceptance:

- Baseline comparison is readable and grounded in committed metrics.
- Failure classification does not use hidden-oracle or raw transcript material.
- Recommended next actions are recorded only as fields or prose in the report.

Verification:

```text
uv run python experiments/phase1_compiler/tools/phase1_weighted_design_paid_pilot.py baseline-comparison
uv run python -m pytest experiments/phase1_compiler/tests/test_phase1_weighted_design_paid_pilot.py -q
git diff --check
```

## Step 9: Final Decision And Closeout

Commit target:

```text
Record weighted design paid pilot decision
```

Actions:

1. Write final decision JSON and Markdown.
2. Answer:

```text
Did all 44 planned cells complete?
Did policy, harness, hidden-oracle, and invalid-output gates pass?
Did weighted design meet the 0.15 pilot threshold?
Did weighted design beat unweighted and stratified baselines?
Did historical reference remain historical-only?
Was precision still underpowered?
What is the smallest next local or paid action recommended?
```

3. Record:

```text
new_paid_acut_calls_made
new_paid_llm_calls_made
paid_cells_planned
paid_cells_completed
scoreable_cells
observed_or_conservative_cost_usd
primary_release_candidate_id
baseline_candidate_ids
primary_threshold_result
precision_status
policy_status
scoreability_status
followup_runbook_written_by_worker
raw_artifacts_committed
```

4. Update the process report with step status, commit hashes, verification
   commands, and blockers.
5. Run final checks.

Acceptance:

- Final decision is one of:

```text
weighted_pilot_complete_threshold_met_precision_underpowered
weighted_pilot_complete_threshold_not_met
weighted_pilot_complete_insufficient_scoreability
weighted_pilot_blocked_before_paid_cells
weighted_pilot_blocked_after_partial_paid_cells
```

- The decision does not claim precision-target predictive validity.
- The decision does not include or create a next runbook.
- The process report contains a concise closeout for the coordinating session.

Verification:

```text
uv run python -m pytest experiments/phase0_headroom/tools/test_workspace_acut_run.py experiments/phase1_compiler/tests -q
git diff --check
git status --short
```

## Final Response Requirements For The Worker

The worker's final response to the coordinating session should be short and
plain. It should include:

```text
1. whether the paid pilot completed or where it blocked
2. number of planned/completed/scoreable cells
3. weighted design gap and baseline gaps
4. whether the pilot 0.15 threshold was met
5. cost summary
6. the strongest remaining risk
7. confirmation that no follow-up runbook was written
8. commit range created by the worker
```

Do not paste long reports into the final response. Point to committed reports
and decision files instead.
