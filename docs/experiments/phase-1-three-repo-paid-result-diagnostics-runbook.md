# Phase 1 Three-Repo Paid Result Diagnostics Runbook

Status: diagnostic runbook, 2026-05-28.

This runbook is for one dedicated Codex CLI session. Its job is to explain the
three-repo paid pilot result, especially the large per-repo gaps and adapter
differences, before Barcarolle spends more money or changes the benchmark
design.

```text
Analyze the completed attrs/boltons/click primary_pilot paid results with
sanitized artifacts only. Explain whether the observed gaps are most consistent
with bookkeeping error, small-sample noise, split imbalance, task statement
quality, verifier/environment issues, or adapter behavior. Recommend the next
action category, but do not write the next runbook.
```

Plain-language summary:

```text
The paid pilot passed the frozen pooled threshold, but the per-repo numbers are
not stable. This runbook should explain why.

Do not rerun paid ACUT cells. Do not change the previous paid decision. Use the
existing score tables and committed package metadata to learn what likely caused
the gap. If raw ignored logs are inspected, record only short sanitized labels
and evidence hashes, never raw prompts, completions, transcripts, patches, or
workspace files.
```

## Execution Boundary

This runbook is diagnostic-only. It must not make new paid LLM or ACUT calls.

Allowed work:

- recompute metrics from committed score tables;
- build sanitized task-level result cubes;
- compare repo, split, task-family, time-bucket, source-context, adapter, and
  difficulty-proxy slices;
- run bootstrap, permutation, or exact small-sample uncertainty checks;
- inspect ignored raw artifacts only to assign bounded failure labels, if raw
  artifacts are locally available;
- write sanitized reports, manifests, and small JSON/CSV summaries.

Disallowed work:

- running any new paid ACUT solver cell;
- changing the frozen primary_pilot task list or split labels;
- changing the previous decision label after seeing diagnostics;
- promoting a diagnostic baseline to primary for the completed paid pilot;
- committing raw prompts, completions, ACUT transcripts, solver workspaces,
  verifier workspaces, raw diffs, raw test patches, target repository clones,
  secrets, or large raw outputs;
- drafting or creating the next runbook.

If a worker believes new paid calls are necessary, it must stop and write that
as a recommendation in the decision report, not execute those calls.

## Starting Point

The previous paid validation run ended with:

```text
decision: three_repo_paid_pilot_threshold_met
planned cells: 120
completed cells: 120
scoreable cells: 120
scoreability rate: 1.0
policy violations: 0
raw oracle exposure: false
endpoint compliance: pass
observed/conservative cost: USD 51.267333
primary design: repo_stratified
primary pooled absolute gap: 0.10
threshold <= 0.15: pass
predictive validity established: false
```

The main puzzle:

```text
Pooled gap passed, but per-repo gaps were large:

attrs:   B_eval 0.70 / H_future 0.35 / abs gap 0.35
boltons: B_eval 0.15 / H_future 0.40 / abs gap 0.25
click:   B_eval 0.35 / H_future 0.75 / abs gap 0.40

Adapter-level pass rates also differed:

codex_workspace: 22/60 = 0.367
kilo_workspace:  32/60 = 0.533
```

The result is pilot evidence only. This runbook must not claim
precision-target predictive validity.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-three-repo-paid-result-diagnostics-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md first. Use uv for
repo-local Python tooling. Follow AGENTS.md step-level acceptance and commit
requirements: after each step, or after each small group of tightly related
steps, commit the changed files with an appropriately scoped commit.

This runbook is diagnostic-only. Do not make new paid LLM or ACUT calls. Do not
change the completed three-repo paid pilot decision. Do not change the frozen
task list, split assignment, primary design, thresholds, or non-scoreable
handling after seeing outcomes.

Main goal: explain why the paid pilot had pooled gap 0.10 but large per-repo
gaps and visible adapter differences. Test these explanations: bookkeeping
error, small-sample noise, split imbalance, task statement quality, verifier or
environment issue, and adapter behavior.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. What action it suggests next.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
Codex/Kilo logs, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, raw target diffs, raw test patches, raw GitHub API
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
docs/experiments/phase-1-three-repo-paid-validation-runbook.md

experiments/phase1_compiler/configs/phase1_three_repo_paid_validation.yaml
experiments/phase1_compiler/configs/phase1_three_repo_paid_validation_thresholds.yaml

experiments/phase1_compiler/results/phase1_three_repo_paid_validation_batch_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_score_tables_manifest.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_metrics.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_decision.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_baseline_comparison.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_cost_reconciliation.json

experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_task_table.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_split_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_source_quality_audit.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_baseline_plan.json

experiments/phase0_headroom/results/phase1_three_repo_paid_validation_*_score_table.csv
experiments/phase0_headroom/results/phase1_three_repo_paid_validation_*_matrix.json
experiments/phase0_headroom/results/workspace_usage_ledger.jsonl
experiments/phase0_headroom/results/workspace_cost_reconciliation.json
```

Optional local-only inputs, if present and ignored:

```text
experiments/phase0_headroom/results/raw/
experiments/phase0_headroom/workspaces/
experiments/phase1_compiler/tmp/three_repo_paid_validation/
```

Raw local-only inputs may be read only to assign sanitized failure labels. Do
not copy raw text into committed artifacts.

## Explanation Targets

The final report should classify each explanation as `supported`,
`partially_supported`, `not_supported`, or `inconclusive`.

```text
bookkeeping_or_metric_error
small_sample_noise
split_imbalance
task_statement_quality
source_context_thinness
verifier_or_environment_issue
adapter_behavior_difference
outlier_task_or_task_family
```

Use these plain meanings:

- Bookkeeping error: the reported result is wrong because data was joined,
  counted, or aggregated incorrectly.
- Small-sample noise: the data is too small to tell whether a gap is real.
- Split imbalance: B_eval and H_future were not comparable in task type,
  source context, time bucket, or difficulty proxy.
- Task statement quality: the solver likely failed because the problem
  statement was unclear, missing necessary public context, or overcompressed.
- Source context thinness: title-only or similarly weak source context made
  tasks less informative.
- Verifier or environment issue: the solver may have been right, but replay,
  dependency, hidden test, or environment behavior caused failure.
- Adapter behavior difference: Codex and Kilo systematically behaved
  differently on the same task set.
- Outlier task or family: a small number of tasks or families drove most of the
  gap.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_three_repo_paid_result_diagnostics.yaml
  tools/
    phase1_three_repo_paid_result_diagnostics.py
  tests/
    test_phase1_three_repo_paid_result_diagnostics.py
  results/
    phase1_three_repo_paid_result_diagnostics_preflight.json
    phase1_three_repo_paid_result_diagnostics_result_cube.json
    phase1_three_repo_paid_result_diagnostics_result_cube.csv
    phase1_three_repo_paid_result_diagnostics_metric_reproduction.json
    phase1_three_repo_paid_result_diagnostics_uncertainty.json
    phase1_three_repo_paid_result_diagnostics_split_balance.json
    phase1_three_repo_paid_result_diagnostics_adapter_effects.json
    phase1_three_repo_paid_result_diagnostics_failure_taxonomy.json
    phase1_three_repo_paid_result_diagnostics_action_matrix.json
    phase1_three_repo_paid_result_diagnostics_decision.json
  reports/
    phase1_three_repo_paid_result_diagnostics_process.md
    phase1_three_repo_paid_result_diagnostics_preflight.md
    phase1_three_repo_paid_result_diagnostics_metric_reproduction.md
    phase1_three_repo_paid_result_diagnostics_uncertainty.md
    phase1_three_repo_paid_result_diagnostics_split_balance.md
    phase1_three_repo_paid_result_diagnostics_adapter_effects.md
    phase1_three_repo_paid_result_diagnostics_failure_taxonomy.md
    phase1_three_repo_paid_result_diagnostics_action_matrix.md
    phase1_three_repo_paid_result_diagnostics_decision.md
```

If a step is blocked, write the corresponding partial report and decision
instead of inventing missing evidence.

## Step 0 - Preflight And No-Paid Boundary

Goal: prove the diagnostic starts from the committed paid result and will not
make new paid calls.

Actions:

1. Read `AGENTS.md`, this runbook, and the paid validation decision artifacts.
2. Record branch, HEAD, date, Python version, and `uv --version`.
3. Record `git status --short --branch` and `git diff --check`.
4. Confirm the paid decision is `three_repo_paid_pilot_threshold_met`.
5. Confirm completed cells are 120, scoreable cells are 120, and policy
   violations are 0.
6. Record that new paid LLM/ACUT calls are disallowed.
7. Classify dirty/untracked paths as relevant, ignored raw/runtime, or
   unrelated.

Expected outputs:

```text
phase1_three_repo_paid_result_diagnostics_preflight.json
phase1_three_repo_paid_result_diagnostics_preflight.md
phase1_three_repo_paid_result_diagnostics_process.md
```

Acceptance:

- The previous paid result is available.
- No new paid calls are planned or made.
- Dirty/untracked files are classified.
- The report states the diagnostic does not change the paid decision.

Commit:

```text
Record three-repo paid result diagnostics preflight
```

## Step 1 - Result Cube And Metric Reproduction

Goal: rule out simple counting or aggregation mistakes.

Actions:

1. Load all score tables from the paid validation score-table manifest.
2. Build one row per attempted cell with:
   - task id;
   - repo id;
   - split;
   - adapter;
   - terminal status;
   - scoreable flag;
   - pass/fail flag;
   - result prefix;
   - batch id.
3. Join package metadata from the frozen task table and split plan:
   - task family;
   - task time bucket;
   - source context class;
   - source quality markers available in committed artifacts;
   - statement or context length if already present in committed sanitized
     artifacts.
4. Recompute:
   - total pass rate;
   - pass rate by repo;
   - pass rate by split;
   - pass rate by repo and split;
   - pass rate by adapter;
   - pass rate by adapter, repo, and split;
   - pooled primary gap.
5. Compare recomputed metrics against
   `phase1_three_repo_paid_validation_metrics.json`.
6. Stop with a blocker if the recomputed primary result does not match.

Expected outputs:

```text
phase1_three_repo_paid_result_diagnostics_result_cube.json
phase1_three_repo_paid_result_diagnostics_result_cube.csv
phase1_three_repo_paid_result_diagnostics_metric_reproduction.json
phase1_three_repo_paid_result_diagnostics_metric_reproduction.md
```

Acceptance:

- Every one of the 120 paid cells appears exactly once.
- Every task has exactly two adapter rows.
- The primary pooled gap reproduces the committed `0.10` result, or a precise
  bookkeeping bug is reported.
- The output is sanitized and does not include raw prompts, completions, or
  workspace diffs.

Commit:

```text
Reproduce three-repo paid result metrics
```

## Step 2 - Adapter And Task-Level Diagnostics

Goal: explain whether the solver harness choice is a major driver.

Actions:

1. Compute pass rates by adapter overall, by repo, and by split.
2. Compute paired task outcomes:
   - both adapters pass;
   - one adapter passes;
   - both adapters fail.
3. Compute adapter disagreement rates by repo, split, task family, source
   context class, and time bucket.
4. Identify tasks where adapters disagree, especially tasks that determine the
   sign or size of the B_eval/H_future gap.
5. If useful and dependency-free, compute a simple paired test such as McNemar
   or exact binomial sign test for adapter disagreement. If not, report raw
   counts and avoid overclaiming.

Expected outputs:

```text
phase1_three_repo_paid_result_diagnostics_adapter_effects.json
phase1_three_repo_paid_result_diagnostics_adapter_effects.md
```

Acceptance:

- Adapter differences are quantified at overall, repo, split, and paired-task
  levels.
- The report says whether adapter behavior difference is supported,
  partially supported, not supported, or inconclusive.
- The report states whether future runs should stratify by adapter, report
  adapters separately, or keep pooled adapter reporting.

Commit:

```text
Analyze three-repo paid adapter effects
```

## Step 3 - Split Balance And Difficulty Proxy Audit

Goal: test whether B_eval and H_future were comparable.

Actions:

1. Compare B_eval and H_future distributions by repo for:
   - task family;
   - task time bucket;
   - source context class;
   - statement or context length;
   - certification source class;
   - any available patch-size, file-count, test-count, or changed-path proxy in
     committed sanitized artifacts.
2. Compute simple imbalance summaries:
   - count differences;
   - absolute standardized differences when numeric proxies exist;
   - largest stratum imbalances.
3. Identify strata that align with large observed gaps.
4. Check whether click's title-only or thin-context tasks are concentrated in
   one split or in high-failure rows.
5. Do not use H_future outcomes to propose changing this completed split. Any
   split recommendation is for future preregistration only.

Expected outputs:

```text
phase1_three_repo_paid_result_diagnostics_split_balance.json
phase1_three_repo_paid_result_diagnostics_split_balance.md
```

Acceptance:

- The report identifies which split-balance factors are measured and which are
  unavailable.
- Each repo has a short split-balance explanation.
- The report states whether split imbalance is supported, partially supported,
  not supported, or inconclusive.

Commit:

```text
Audit three-repo paid split balance
```

## Step 4 - Small-Sample Uncertainty And Outlier Analysis

Goal: estimate how much of the gap could be noise.

Actions:

1. Use the result cube to compute uncertainty for:
   - pooled B_eval/H_future gap;
   - per-repo B_eval/H_future gaps;
   - adapter-level pass rates;
   - paired task-level pass-count differences.
2. Prefer transparent methods:
   - exact or Wilson intervals for simple pass rates;
   - bootstrap over tasks within repo/split;
   - permutation of split labels within allowed strata, if enough support
     exists;
   - leave-one-task-out and leave-one-family-out sensitivity.
3. Avoid overfitting. If a method is underpowered because each repo/split has
   only 20 cells, say that plainly.
4. Identify whether one or two tasks/families can materially change the
   primary pooled gap or the per-repo gaps.

Expected outputs:

```text
phase1_three_repo_paid_result_diagnostics_uncertainty.json
phase1_three_repo_paid_result_diagnostics_uncertainty.md
```

Acceptance:

- The report states whether small-sample noise is supported, partially
  supported, not supported, or inconclusive.
- The report identifies any influential tasks or task families.
- The report clearly says what cannot be inferred from 120 cells.

Commit:

```text
Quantify three-repo paid result uncertainty
```

## Step 5 - Bounded Failure Taxonomy

Goal: explain failures without leaking raw solver or oracle material.

Actions:

1. Build a bounded review queue from sanitized result rows:
   - all tasks where both adapters fail;
   - all adapter-disagreement tasks;
   - tasks in strata that drive the largest split gaps;
   - a small matched sample of both-pass tasks for contrast.
2. If ignored raw artifacts are locally available, inspect only enough to assign
   labels. Do not commit raw text or long excerpts.
3. Assign one or more labels from this taxonomy:
   - `likely_agent_solution_failure`;
   - `statement_missing_public_context`;
   - `statement_ambiguous_or_overcompressed`;
   - `source_context_too_thin`;
   - `verifier_or_environment_suspect`;
   - `adapter_specific_behavior`;
   - `task_intrinsically_hard`;
   - `classification_inconclusive`.
4. Record short sanitized evidence, such as:
   - score row reference;
   - committed source-context class;
   - task family;
   - failure label;
   - optional hash or local artifact path basename, not raw content.
5. Separately count labels by repo, split, and adapter.

Expected outputs:

```text
phase1_three_repo_paid_result_diagnostics_failure_taxonomy.json
phase1_three_repo_paid_result_diagnostics_failure_taxonomy.md
```

Acceptance:

- The report explains how many tasks were reviewed and how they were selected.
- No raw prompts, completions, transcripts, patches, workspaces, or secrets are
  committed.
- The report states whether task statement quality, source context thinness,
  verifier/environment issues, and outlier task/family effects are supported,
  partially supported, not supported, or inconclusive.

Commit:

```text
Classify three-repo paid result failures
```

## Step 6 - Action Matrix

Goal: map explanations to concrete next actions.

Actions:

1. Build an action matrix with one row per explanation target.
2. For each row, record:
   - status: supported, partially_supported, not_supported, inconclusive;
   - main evidence;
   - confidence: high, medium, low;
   - recommended next action;
   - whether action is no-paid or paid;
   - whether a future runbook is required.
3. Use these next-action categories:

```text
fix_metric_or_join_bug
repair_verifier_or_environment
harden_task_generator_or_source_context
redesign_split_with_block_randomization
stratify_or_separate_adapter_reporting
expand_precision_target_paid_replication
add_more_repos_before_precision_run
no_design_change_needed_yet
blocked_pending_missing_artifacts
```

4. Be explicit about tradeoffs:
   - If split imbalance is supported, future paid work should use a new
     preregistered blocked split, not reinterpret this split.
   - If task statement/source-context weakness is supported, harden Task
     Generator before buying more paid cells.
   - If adapter difference is supported, avoid single pooled adapter reporting
     as the only headline.
   - If uncertainty dominates and no design flaw is found, a precision-target
     replication is the clean next paid step.

Expected outputs:

```text
phase1_three_repo_paid_result_diagnostics_action_matrix.json
phase1_three_repo_paid_result_diagnostics_action_matrix.md
```

Acceptance:

- Every explanation target has a status and action.
- The action matrix does not recommend changing the completed paid decision.
- Paid recommendations are clearly separated from no-paid recommendations.

Commit:

```text
Map three-repo paid diagnostics to actions
```

## Step 7 - Decision And Closeout

Goal: write a clear diagnostic decision for the coordinating session.

Actions:

1. Write final decision artifacts.
2. Answer these research questions:

```text
RQ1: Did the diagnostic reproduce the paid pilot metrics?
RQ2: Are the large per-repo gaps likely a bookkeeping error?
RQ3: How much does adapter behavior explain?
RQ4: Are B_eval and H_future visibly imbalanced?
RQ5: How much uncertainty remains because the sample is small?
RQ6: Are statement quality or source context weaknesses likely drivers?
RQ7: Are verifier or environment issues likely drivers?
RQ8: What should be done next, and should it be no-paid or paid?
```

3. Choose exactly one primary decision label:

```text
three_repo_paid_diagnostics_metric_bug_found
three_repo_paid_diagnostics_split_redesign_needed
three_repo_paid_diagnostics_task_generator_hardening_needed
three_repo_paid_diagnostics_adapter_stratification_needed
three_repo_paid_diagnostics_precision_replication_ready
three_repo_paid_diagnostics_more_clean_supply_needed
three_repo_paid_diagnostics_blocked_missing_artifacts
```

4. Secondary labels may be recorded, but the primary label should identify the
   next bottleneck.
5. Record completed steps, commits made during the run, tests run, and known
   blockers.
6. Do not draft or create the next runbook.

Expected outputs:

```text
phase1_three_repo_paid_result_diagnostics_decision.json
phase1_three_repo_paid_result_diagnostics_decision.md
```

Acceptance:

- The report states that no new paid cells ran.
- The report does not claim precision-target predictive validity.
- The report explains the result in simple language.
- The report gives a next-action category, not a new runbook.

Commit:

```text
Close three-repo paid result diagnostics
```

## Verification

At minimum, run:

```bash
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_three_repo_paid_result_diagnostics.py -q
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_three_repo_paid_validation.py -q
git diff --check
git status --short --untracked-files=all
```

If the full Phase 1 compiler test suite is feasible, also run:

```bash
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q
```

If a verification command is too slow or blocked, record the exact reason in
the decision report.

## Final Reporting Template

The final worker summary should be short and in simple Chinese:

```text
这次 runbook 是 paid result diagnostics，没有跑新的 paid cells。

结果：
- paid pilot metrics reproduced: yes/no
- metric/bookkeeping bug: supported/partially_supported/not_supported/inconclusive
- adapter behavior difference: supported/partially_supported/not_supported/inconclusive
- split imbalance: supported/partially_supported/not_supported/inconclusive
- small-sample noise: supported/partially_supported/not_supported/inconclusive
- task statement/source context issue: supported/partially_supported/not_supported/inconclusive
- verifier/environment issue: supported/partially_supported/not_supported/inconclusive
- primary decision label: X
- recommended next action category: X

解释：
- 上一轮 paid pilot 结论没有被改写。
- 这次只是在解释为什么 pooled gap 过线但 per-repo gap 很大。
- 没有提交 raw logs、raw prompts、raw completions、solver workspaces、verifier
  workspaces 或 secrets。
```
