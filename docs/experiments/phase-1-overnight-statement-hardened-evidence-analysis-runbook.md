# Phase 1 Overnight Statement-Hardened Evidence Analysis Runbook

Status: implementation runbook, 2026-05-25.

This runbook is for one long-running unattended Codex CLI session. Its job is
to analyze the completed statement-hardened paid validation, explain what the
evidence does and does not show, and produce a concrete local research decision
for the coordinating session.

This runbook should run long enough to exhaust the useful local analysis queue.
It should not stop after a shallow summary. If one analysis branch is blocked,
continue independent local branches and record the blocker precisely.

Do not draft or create a follow-up runbook. Record recommended next actions in
the final decision and closeout reports only.

## Starting Point

Latest paid validation result:

```text
release_id: statement_hardened_after_canonical_split_repair_20260525
paid validation decision: statement_hardened_paid_validation_complete_threshold_not_met
planned cells: 32
completed cells: 32
scoreable cells: 32
terminal statuses:
  verified_pass: 21
  verified_fail: 11
policy violations: 0
timeouts: 0
harness errors: 0
observed-or-conservative cost: USD 9.9235152
adapter disagreement rate: 0.0625
predictive_validity_established: false
```

Repo/split pass rates:

```text
attrs/B_eval: 6/8 = 0.75
attrs/H_future: 4/8 = 0.50
boltons/B_eval: 7/8 = 0.875
boltons/H_future: 4/8 = 0.50
```

Observed B_eval to H_future gaps:

```text
attrs: 0.25
boltons: 0.375
```

Key decision reason:

```text
No preregistered quantitative predictive-validity success threshold beyond
scoreability, policy, and cost gates was recorded for this paid runbook.
```

## Required Inputs

Use these committed artifacts:

```text
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_paid_decision.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_paid_metrics.json
experiments/phase1_compiler/reports/phase1_statement_hardened_after_canonical_repair_paid_process.md
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_release_manifest.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_preregistration.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_inventory.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_screen.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_release_preview.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_paid_tooling_check.json
experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_attrs_b_eval_score_table.csv
experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_attrs_h_future_score_table.csv
experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_boltons_b_eval_score_table.csv
experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_boltons_h_future_score_table.csv
experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_attrs_b_eval_metrics.json
experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_attrs_h_future_metrics.json
experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_boltons_b_eval_metrics.json
experiments/phase0_headroom/results/phase1_statement_hardened_after_canonical_repair_boltons_h_future_metrics.json
experiments/phase0_headroom/results/workspace_cost_reconciliation.json
experiments/phase0_headroom/results/workspace_usage_ledger.jsonl
```

Optional historical context:

```text
experiments/phase1_compiler/results/phase1_two_repo_task_outcome_matrix.json
experiments/phase1_compiler/results/phase1_two_repo_future_holdout_decision.json
experiments/phase1_compiler/results/phase1_attrs_h_future_evidence_status.json
experiments/phase1_compiler/results/phase1_canonical_split_repair_decision.json
experiments/phase1_compiler/results/phase1_canonical_statement_screen.json
barcarolle-research-0519.md
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-overnight-statement-hardened-evidence-analysis-runbook.md.

Work in the repository root. Use uv for repo-local Python tooling. Make a
cohesive git commit after every completed step that changes files. Do not batch
unrelated steps into one commit. If a step has no file changes, record that fact
in the process report and do not create an empty commit. Do not push unless the
user explicitly asks.

Main goal: deeply analyze the completed statement-hardened paid validation and
produce a local research decision. Explain whether the results mainly indicate
task difficulty, split design weakness, missing predictive-validity threshold,
insufficient sample size, statement quality residual risk, ACUT adapter
variance, or some combination.

Run long enough to complete the local analysis queue. If one branch is blocked,
continue other branches. Be autonomous: add small deterministic tools, tests,
tables, and reports when they help answer the research question.

Do not run new paid ACUT cells or paid LLM calls in this runbook. The previous
paid validation already produced 32 scoreable cells. If you conclude another
paid experiment is needed, record the exact recommendation and rationale in the
decision report; do not run it and do not write a follow-up runbook.

Do not use hidden verifier material to rewrite statements or change selection.
Do not rewrite old paid score tables. Do not treat generated task statements as
scoreable results. Do not claim predictive validity unless the final analysis
defines and justifies a threshold and shows the current evidence meets it.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
Codex/Kilo logs, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, raw target diffs, or large raw outputs. Commit only
small sanitized configs, tools, tests, tables, metrics, reports, summaries, and
decision files.

Do not draft or create the next runbook. Record recommended next actions and
suggested follow-up categories only.
```

## Research Questions

Answer these directly:

```text
RQ1: Did statement hardening turn the benchmark into clean scoreable evidence?
RQ2: Does B_eval predict H_future well enough under the current split?
RQ3: Is the H_future drop mainly task difficulty, task-family/time shift,
    statement quality, adapter variance, sample size, or an undefined threshold?
RQ4: What quantitative success threshold should future predictive-validity
    preregistrations use?
RQ5: What should Barcarolle do next as a benchmark compiler: reweight, resplit,
    enlarge local supply, add another repo, tune statement generation, or stop
    and report bounded negative evidence?
```

## Claim Boundary

Allowed claims:

```text
statement_hardened_paid_evidence_analyzed
scoreability_gate_passed
policy_gate_passed
cost_gate_passed
predictive_validity_threshold_missing
predictive_validity_not_established
task_difficulty_shift_evidence
adapter_disagreement_low
sample_size_underpowered
threshold_options_proposed
compiler_design_options_ranked
bounded_negative_or_inconclusive_evidence_reported
```

Disallowed claims:

```text
predictive_validity_established_without_threshold
production_benchmark_ranking
old_paid_result_repaired
attrs_policy_violation_repaired
hidden_oracle_informed_statement_rewrite
new_paid_validation_completed
followup_runbook_written_by_worker
```

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_overnight_statement_hardened_evidence_analysis.yaml
  tools/
    phase1_overnight_statement_hardened_evidence_analysis.py
  tests/
    test_phase1_overnight_statement_hardened_evidence_analysis.py
  results/
    phase1_overnight_statement_hardened_evidence_preflight.json
    phase1_overnight_statement_hardened_integrity_audit.json
    phase1_overnight_statement_hardened_task_outcome_matrix.json
    phase1_overnight_statement_hardened_failure_taxonomy.json
    phase1_overnight_statement_hardened_strata_analysis.json
    phase1_overnight_statement_hardened_threshold_analysis.json
    phase1_overnight_statement_hardened_power_analysis.json
    phase1_overnight_statement_hardened_calibration_options.json
    phase1_overnight_statement_hardened_next_action_decision.json
  reports/
    phase1_overnight_statement_hardened_evidence_process.md
    phase1_overnight_statement_hardened_integrity_audit.md
    phase1_overnight_statement_hardened_task_outcome_matrix.md
    phase1_overnight_statement_hardened_failure_taxonomy.md
    phase1_overnight_statement_hardened_strata_analysis.md
    phase1_overnight_statement_hardened_threshold_analysis.md
    phase1_overnight_statement_hardened_power_analysis.md
    phase1_overnight_statement_hardened_calibration_options.md
    phase1_overnight_statement_hardened_next_action_decision.md
```

Do not create:

```text
docs/experiments/*follow-up*.md
docs/experiments/*next*.md
docs/experiments/phase-1-*-paid-*.md
```

If a follow-up path is useful, record it only as a recommendation field.

## Step 0: Preflight And Work Queue

Actions:

1. Read `AGENTS.md`, this runbook, paid decision, paid metrics, and process
   report.
2. Record branch, HEAD, date, `uv --version`, Python version, and
   `git status --short --branch`.
3. Verify:

```text
paid decision == statement_hardened_paid_validation_complete_threshold_not_met
planned cells == 32
scoreable cells == 32
policy violation count == 0
old paid result repaired == false
followup_runbook_written_by_worker == false
```

4. Build a work queue JSON with all planned local analyses, status, blockers,
   and commit targets.
5. Write preflight JSON and initialize the process report.

Acceptance:

- All required input artifacts exist and have SHA256 digests recorded.
- The runbook records that no new paid calls are allowed.
- Work queue contains at least the analyses in Steps 1-9.

Commit:

```text
Record overnight statement-hardened analysis preflight
```

## Step 1: Result Integrity Audit

Actions:

1. Parse all four score tables and metrics files.
2. Cross-check against paid decision and process report:

```text
total cells == 32
scoreable cells == 32
verified_pass + verified_fail == 32
policy violations == 0
timeouts == 0
harness errors == 0
invalid outputs == 0
usage observed count == 32
observed-or-conservative cost == paid metrics value
```

3. Confirm score tables use only new statement-hardened result prefixes.
4. Confirm no old score table rows are merged.
5. Confirm raw artifacts are not committed.

Acceptance:

- Integrity audit status is `pass`, or exact mismatches are listed.
- If any mismatch exists, continue local analysis but mark final decision as
  blocked on integrity.

Commit:

```text
Audit statement-hardened paid result integrity
```

## Step 2: Build Task Outcome Matrix

Actions:

1. Build one row per task with both adapter outcomes:

```text
task_id
repo_id
canonical_split
repo_split
codex_terminal_status
kilo_terminal_status
both_pass
both_fail
adapter_disagreement
statement_source
source_kind
module_or_package
editable_paths
test_paths
task_time
statement_digest
```

2. Add derived fields:

```text
adapter_pass_count
repo_split_pass_count
task_family_label
implementation_file_count
test_file_count
statement_length_bucket
source_context_length_bucket
historical_old_policy_violation_flag
```

3. Produce Markdown tables sorted by:
   - both adapters failed;
   - adapter disagreement;
   - H_future failures;
   - B_eval failures.

Acceptance:

- The matrix accounts for exactly 16 unique tasks and 32 cells.
- It identifies the exact tasks where both adapters failed.
- It identifies the exact task where adapters disagreed.

Commit:

```text
Build statement-hardened task outcome matrix
```

## Step 3: Failure Taxonomy

Actions:

1. For each failed task, inspect only committed sanitized artifacts and
   score/verifier summaries. Do not inspect raw transcripts or hidden verifier
   material to rewrite statements.
2. Classify each failed task into one or more categories:

```text
api_semantics_complexity
edge_case_specification
multi_file_or_typing_surface
time_or_version_shift
statement_under_specification
statement_over_constraint
source_context_weakness
test_environment_or_dependency
adapter_specific_behavior
unknown_from_sanitized_artifacts
```

3. Compare failure categories against pass tasks in the same repo/split.
4. Identify whether failures are concentrated by module, source kind, statement
   source, task age, implementation path, or test path.

Acceptance:

- Every verified_fail cell has a task-level explanation category.
- Both-adapter failures are called out separately from adapter disagreement.
- The report clearly separates evidence from inference.

Commit:

```text
Classify statement-hardened paid failures
```

## Step 4: Strata And Split Analysis

Actions:

1. Analyze pass rates by strata:

```text
repo
split
adapter
task family/module
statement source: reused_codex_loop vs new_codex_loop
source kind: issue vs pull_request vs commit-derived
task time bucket
implementation path count
test path count
B_eval vs H_future
```

2. Quantify whether the H_future 50% result is plausibly a time-window shift,
   task-family shift, or general future-holdout hardness.
3. Compare canonical split labels with current inventory split and verify the
   repaired split did not reintroduce the old mapping bug.

Acceptance:

- The report names the strongest plausible explanation and the main uncertainty.
- It does not overclaim root cause from small-N evidence.
- It states whether attrs and boltons show the same direction of H_future drop.

Commit:

```text
Analyze statement-hardened result strata
```

## Step 5: Statistical Threshold And Power Analysis

Actions:

1. Compute uncertainty intervals for each repo/split pass rate.
2. Compute uncertainty for B_eval-to-H_future gaps.
3. Simulate or analytically estimate power for future validation designs:

```text
current design: 2 repos, 4 tasks/split, 2 adapters
expanded tasks: 2 repos, 8 tasks/split, 2 adapters
expanded repos: 3 repos, 4 tasks/split, 2 adapters
expanded repos and tasks: 3 repos, 8 tasks/split, 2 adapters
single-adapter sensitivity
adapter-averaged sensitivity
```

4. Propose at least three candidate predictive-validity thresholds, such as:

```text
absolute B_eval-H_future gap <= 0.15 with enough scoreable cells
rank/correlation threshold across repos or task families
calibration error threshold with confidence interval
holdout pass-rate lower bound conditional on B_eval
```

5. Explain which thresholds are compatible with the research proposal and which
are too weak or too easy to game.

Acceptance:

- The analysis explains why the current runbook could not establish predictive
  validity without a preregistered quantitative success rule.
- It recommends one primary threshold family for future preregistration.
- It estimates the sample size needed to make that threshold meaningful.

Commit:

```text
Analyze predictive threshold and power
```

## Step 6: Compiler Calibration And Weighting Options

Actions:

1. Treat Barcarolle as a benchmark compiler. Propose compiler-side options:

```text
time-stratified B_eval matching
module/task-family weighting
difficulty-balanced B_eval selection
per-repo calibration using local historical dry-run metadata
adapter-disagreement weighting
statement-quality confidence weighting
expanded holdout with minimum scoreable cells
negative-evidence reporting without further paid runs
```

2. For each option, record:

```text
expected benefit
cost
risk of overfitting
data needed
whether it respects ACUT boundary
whether it requires paid validation
```

3. Rank the options for the next research move.

Acceptance:

- Options are benchmark-compiler changes, not ACUT harness changes.
- No option relies on hidden verifier material or old paid pass/fail selection.
- The recommendation is specific enough for the coordinating session to write a
  future runbook if needed.

Commit:

```text
Rank compiler calibration options
```

## Step 7: Local Supply And Expansion Plan

Actions:

1. Inventory existing local candidate pools for possible future expansion:

```text
attrs clean outcome-unseen supply
boltons clean outcome-unseen supply
humanize/itsdangerous/toolz historical certified tasks
second-repo clean supply artifacts if present
third-repo decision artifacts if present
```

2. Do not mine new tasks unless it is cheap and local. If mining is needed,
   record the exact target repo and why.
3. Estimate how many additional local tasks are needed for each threshold option
   from Step 5.
4. Identify whether expansion should prefer:
   - more tasks per existing repo;
   - a third repo;
   - better B_eval matching for H_future;
   - a smaller but more defensible claim.

Acceptance:

- The plan distinguishes local task preparation from paid validation.
- It does not recommend spending before explaining the current negative result.
- It names the most promising local candidate reservoir, if any.

Commit:

```text
Assess local supply for statement-hardened expansion
```

## Step 8: Proposal Alignment Memo

Actions:

1. Re-read the proposal excerpt or local proposal file if available.
2. Write a short memo answering:

```text
Is the project still aligned with "target-repository benchmark compiler"?
Did the latest result weaken or strengthen the core claim?
What claim can be made now?
What claim must not be made?
What experiment would most directly improve the paper or prototype next?
```

3. Keep the memo plain and evidence-based. Avoid marketing language.

Acceptance:

- The memo explicitly says the current evidence is bounded and not predictive
  validity.
- It states whether the next work should be analysis/reporting, compiler design,
  local supply expansion, or paid scale-up.

Commit:

```text
Write proposal alignment memo for paid evidence
```

## Step 9: Final Decision

Actions:

1. Write final decision JSON and Markdown.
2. Choose exactly one primary decision:

```text
report_bounded_negative_statement_hardened_evidence:
  Use if current evidence is clean and useful but does not justify more paid
  validation without a new threshold/design.

design_new_predictive_threshold_before_more_paid_validation:
  Use if the main blocker is missing quantitative success criteria.

expand_local_supply_before_more_paid_validation:
  Use if small-N or poor strata matching is the main blocker.

run_bounded_paid_replication_after_new_preregistration:
  Use only as a recommendation, not an action, if local analysis shows a precise
  paid replication is worthwhile.

blocked_on_integrity_or_tooling:
  Use if result integrity or tooling problems invalidate the evidence.
```

3. Include:

```text
primary_decision
confidence level
main evidence
main uncertainty
recommended next action
suggested follow-up category
followup_runbook_written_by_worker: false
new_paid_calls_made: false
predictive_validity_established: false unless strongly justified
```

Acceptance:

- Decision answers all five research questions.
- Decision does not create a follow-up runbook.
- Decision does not claim predictive validity unless threshold and evidence
  support it.

Commit:

```text
Decide next action from statement-hardened evidence
```

## Step 10: Closeout

Actions:

1. Update the process report with:

```text
steps completed
commits created
tests run
new paid ACUT calls made: false
new paid LLM calls made: false
raw artifacts committed: false
integrity audit status
primary decision
recommended next action
follow-up runbook written by worker: false
```

2. Run:

```bash
git diff --check
uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_overnight_statement_hardened_evidence_analysis.py

uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_statement_hardened_after_canonical_repair_paid_validation.py \
  experiments/phase1_compiler/tests/test_phase1_statement_hardened_after_canonical_repair_preregistration.py \
  experiments/phase1_compiler/tests/test_phase1_canonical_split_statement_repair.py
```

3. If broader tools were touched, expand tests accordingly.
4. Commit closeout if files changed.

Acceptance:

- Final process report agrees with JSON decision artifacts.
- No raw workspaces, transcripts, completions, caches, or secrets are committed.
- No follow-up runbook is created by the worker.
- Worktree is clean or contains only pre-existing unrelated changes clearly
  recorded in the process report.

Commit:

```text
Record overnight statement-hardened analysis closeout
```

## Verification Commands

At minimum:

```bash
uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_overnight_statement_hardened_evidence_analysis.py

uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_statement_hardened_after_canonical_repair_paid_validation.py \
  experiments/phase1_compiler/tests/test_phase1_statement_hardened_after_canonical_repair_preregistration.py \
  experiments/phase1_compiler/tests/test_phase1_canonical_split_statement_repair.py \
  experiments/phase1_compiler/tests/test_phase1_diff_assisted_codex_loop_statement_regeneration.py

git diff --check
```

## Final Response Template

Use simple Chinese:

```text
这轮夜间分析完成后的结论：

1. 这轮 paid validation 的数据是否完整可信。
2. H_future 掉到 50% 更像是什么原因。
3. 当前证据能不能支持 predictive validity；如果不能，缺什么。
4. 下一步建议是什么；注意执行 agent 没有写下一份 runbook。
5. 是否建议继续 paid validation；如果建议，必须先有什么新 preregistration 或阈值。

不要说旧 paid 结果被修好了。
不要说 attrs__hist__027 的旧 policy violation 被修好了。
不要说 generated statement 本身是 scoreable result。
不要说 predictive validity 已经建立，除非最终 JSON 明确给出阈值和满足证据。
```
