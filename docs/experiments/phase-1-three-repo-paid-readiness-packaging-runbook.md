# Phase 1 Three-Repo Paid Readiness Packaging Runbook

Status: implementation runbook, 2026-05-28.

This runbook is for one dedicated Codex CLI session. Its job is narrow:

```text
Package the attrs/boltons/click release-eligible supply into a frozen,
auditable paid-validation entry package.
```

Plain-language summary:

```text
The supply blocker is now cleared. attrs, boltons, and click each have at least
30 release-eligible tasks.

That does not mean predictive validity is proven. It only means we finally have
enough clean local task supply to prepare the next paid validation design.

This runbook freezes the release candidate, audits the edge cases, chooses the
mainline split/baseline design, preregisters thresholds and cost bounds, and
stops before any paid ACUT run.
```

This is a packaging and preregistration runbook. Do not run paid ACUT solver
cells, paid task-solving calls, paid replication, benchmark scoring, paid LLM
statement generation, or paid LLM review.

## Starting Point

The latest third-repo release supply screen ended with:

```text
decision: third_repo_ready_paid_gate_ready_for_packaging
paid_ready: true

release eligible:
  attrs:   31
  boltons: 35
  click:   30

repos meeting 30:
  attrs
  boltons
  click
```

The important interpretation is:

```text
The local supply gate is satisfied.
The paid validation design is not yet frozen.
Predictive validity is still not established.
```

The latest algorithm evidence also matters:

```text
weighted paid pilot:
  threshold not met
  weighted design performed worse than simple baselines

local algorithm bakeoff:
  no stable promotion signal for shrinkage weighting
  mainline recommendation: keep repo_stratified as mainline
```

So the next paid package must not quietly return to the old naive weighted
design. It should freeze a conservative mainline, normally
`repo_stratified` or `block_randomized_stratified`, with unweighted and old
weighted designs retained only as baselines/diagnostics unless local evidence
in this runbook clearly justifies otherwise.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-three-repo-paid-readiness-packaging-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md first. Use uv for
repo-local Python tooling. Follow AGENTS.md step-level acceptance and commit
requirements: after each step, or after a small group of tightly related steps,
commit the changed files with an appropriately scoped commit.

Main goal: build a frozen paid-validation entry package from the current
attrs/boltons/click release-eligible task supply. Do not run paid ACUT cells.
Do not launch paid replication. Stop at a local-only entry decision.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. Whether paid validation is ready, blocked, or requires a narrower package.

The package must preserve the current research boundary:
- Barcarolle is a benchmark compiler, not a general task factory.
- Task supply is now an input to compiler validation.
- Predictive validity is not established until paid validation is actually run
  and analyzed.

Do not use the old naive weighted design as the primary claim unless this
runbook produces new preregistered local evidence. Use a conservative
repo-stratified or block-randomized stratified mainline by default. Keep
unweighted, stratified, and historical weighted designs as baselines or
diagnostics.

Do not run paid ACUT solver cells, paid task-solving calls, paid replication,
benchmark scoring, paid LLM statement generation, or paid LLM review. If the
entry package needs an endpoint proof for a later paid run, only check presence
of LLM_BASE_URL and LLM_API_KEY; never print or commit their values. If either
variable is missing, source ~/.zshrc and check again. Do not fall back to local
Codex/ChatGPT subscription auth, OPENAI_API_KEY, OpenRouter variables, or
provider-specific variables.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
Codex/Kilo logs, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, raw target diffs, raw test patches, raw GitHub API
responses, or large raw outputs. Commit only small sanitized configs, manifests,
task tables, statement/source review summaries, score-plan metadata, reports,
and decision files.

Do not draft or create the next runbook. Record recommended next action
categories only.
```

## Inputs

Read these files before making changes:

```text
AGENTS.md
docs/architecture/system-design.md
docs/experiments/phase-1-task-supply-v2-fresh-certification-runbook.md
docs/experiments/phase-1-attrs-source-repair-runbook.md
docs/experiments/phase-1-third-repo-release-supply-screen-runbook.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_decision.md
experiments/phase1_compiler/reports/phase1_attrs_source_repair_decision.md
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_decision.md
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_release_gate.md
experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md
experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md
```

Use these machine-readable inputs:

```text
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_attempts.json
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_paid_readiness_gate.json
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_source_review_queue.json
experiments/phase1_compiler/results/phase1_attrs_source_repair_release_eligibility_overlay.json
experiments/phase1_compiler/results/phase1_attrs_source_repair_paid_readiness_gate.json
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_certification_attempts.json
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_release_gate.json
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_decision.json
experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_decision.json
experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_decision.json
experiments/phase1_compiler/schemas/task_source_candidate_v2.schema.json
```

Useful implementation references:

```text
experiments/phase1_compiler/tools/phase1_task_supply_v2_fresh_certification.py
experiments/phase1_compiler/tools/phase1_attrs_source_repair.py
experiments/phase1_compiler/tools/phase1_third_repo_release_supply_screen.py
experiments/phase1_compiler/tools/phase1_pre_paid_replication_compiler_readiness.py
experiments/phase1_compiler/tests/test_phase1_task_supply_v2_fresh_certification.py
experiments/phase1_compiler/tests/test_phase1_attrs_source_repair.py
experiments/phase1_compiler/tests/test_phase1_third_repo_release_supply_screen.py
```

If older pre-paid replication files exist, treat them as historical references,
not as the current package. The current package must be based on the
three-repo `attrs/boltons/click` supply.

## Outputs

Create a new local-only run under this prefix:

```text
phase1_three_repo_paid_readiness_packaging
```

Expected committed outputs:

```text
experiments/phase1_compiler/configs/phase1_three_repo_paid_readiness_packaging.yaml
experiments/phase1_compiler/configs/phase1_three_repo_paid_validation_thresholds.yaml
experiments/phase1_compiler/configs/phase1_three_repo_release_selection.yaml
experiments/phase1_compiler/tools/phase1_three_repo_paid_readiness_packaging.py
experiments/phase1_compiler/tests/test_phase1_three_repo_paid_readiness_packaging.py

experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_preflight.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_supply_snapshot.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_source_quality_audit.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_task_table.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_split_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_baseline_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_threshold_preregistration.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_power_cost_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_entry_gate.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_decision.json

experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_process.md
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_supply_snapshot.md
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_source_quality_audit.md
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_task_table.md
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_split_plan.md
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_baseline_plan.md
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_threshold_preregistration.md
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_power_cost_plan.md
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_entry_gate.md
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_decision.md
```

Allowed ignored outputs:

```text
experiments/phase1_compiler/tmp/three_repo_paid_readiness_packaging/
experiments/phase0_headroom/workspaces/three_repo_paid_readiness_packaging/
experiments/phase0_headroom/cache/three_repo_paid_readiness_packaging/
```

Committed artifacts must contain only sanitized task metadata, task ids,
source-context classes, digests, split labels, thresholds, and cost estimates.

## Definitions

Use these terms consistently:

```text
technical_certified:
  A task passed the local no-op fail, reference pass, and reference repeat
  gates under an accepted environment profile.

release_eligible:
  A task is technical_certified and has accepted solver-visible source context
  or a reviewed statement repair overlay.

entry_package:
  The frozen task table, split plan, baseline plan, threshold preregistration,
  source-quality audit, cost plan, and endpoint/tooling gate needed before a
  later paid validation runbook can execute solver cells.

paid_ready:
  The entry package is locally complete and all non-paid gates pass. It does
  not mean paid validation has been run.
```

## Claim Boundary

Allowed claims:

```text
three_repo_paid_readiness_packaging_completed
three_repo_supply_snapshot_frozen
source_quality_audit_completed
release_candidate_frozen
split_plan_preregistered
baseline_plan_preregistered
thresholds_preregistered
power_cost_plan_completed
entry_gate_ready_for_paid_validation_runbook
blocked_before_paid_validation
paid_validation_not_run
```

Disallowed claims:

```text
predictive_validity_established
paid_validation_completed
production_benchmark_ranking
old_weighted_design_rehabilitated_without_new_evidence
H_future_outcomes_used_to_select_or_weight_tasks
hidden_oracle_informed_selection
raw_candidates_counted_as_release_eligible
technical_certifications_counted_without_source_quality
paid_acut_cells_run_by_this_packaging_runbook
followup_runbook_written_by_worker
```

## Step 0 - Preflight And Boundary Check

Goal: prove the run starts from a known local state.

Actions:

1. Run `git status --short --untracked-files=all`.
2. Record branch, HEAD, date, Python version, and `uv --version`.
3. Confirm the latest supply gate says paid-ready from a local supply
   perspective.
4. Confirm no paid ACUT or paid LLM calls are required for packaging.
5. Check whether `LLM_BASE_URL` and `LLM_API_KEY` are present for future paid
   use. Record only presence/absence, never values.
6. Classify dirty/untracked files as relevant, ignored artifact output, or
   unrelated.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_preflight.json
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_process.md
```

Acceptance:

- The report states the exact starting commit.
- The report says this runbook did not run paid validation.
- The report records whether the existing external-review bundle is unrelated
  and remains untracked.

Commit guidance:

- Commit preflight artifacts as one preflight commit.
- Do not stage unrelated external-review bundle files.

## Step 1 - Three-Repo Supply Snapshot

Goal: freeze the local release-eligible task inventory as input to packaging.

Actions:

1. Merge the relevant committed evidence:
   - attrs fresh certification plus source-repair overlay;
   - boltons fresh certification;
   - click third-repo certification wave.
2. Build one sanitized task table for all release-eligible tasks:
   - repo id;
   - candidate id;
   - base commit;
   - target commit;
   - task time;
   - implementation files;
   - test files;
   - source reservoir;
   - source context class;
   - technical certification profile;
   - release eligibility provenance;
   - digests, not raw diffs or raw tests.
3. Confirm counts:

```text
attrs >= 30
boltons >= 30
click >= 30
```

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_supply_snapshot.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_task_table.json
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_supply_snapshot.md
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_task_table.md
```

Acceptance:

- The task table contains only release-eligible tasks.
- Raw candidates and technical-only tasks are not counted.
- The report explains in simple language why this is sufficient for packaging.

Commit guidance:

- Commit supply snapshot and task-table artifacts together.

## Step 2 - Source Quality Audit

Goal: catch weak solver-facing statements before paying for solver cells.

Actions:

1. Audit all release-eligible tasks that will be eligible for the paid package.
2. Pay special attention to click because its 30 release-eligible tasks come
   from `pr_title_only_context`.
3. For every repo, report:
   - source context class counts;
   - statement provenance counts;
   - material leakage flags;
   - ambiguity flags;
   - tasks requiring exclusion or manual repair before paid validation.
4. For click's 30 release-eligible tasks, either:
   - accept all after audit; or
   - exclude weak tasks and replace them with audited alternatives from the
     click source-review queue, if available; or
   - mark packaging blocked if click drops below 30 release eligible.
5. Do not use paid LLM review in this runbook.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_source_quality_audit.json
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_source_quality_audit.md
```

Acceptance:

- Every selected release-eligible task has an audit status:
  `accepted_for_paid_package`, `exclude_before_paid`, or
  `needs_source_repair_before_paid`.
- No task with material leakage or unresolved ambiguity remains in the paid
  package.
- If click remains at exactly 30, the report calls out the thin margin.

Commit guidance:

- Commit source-quality audit artifacts separately.

## Step 3 - Release Candidate And Split Plan

Goal: freeze the benchmark release design before paid validation.

Actions:

1. Build a release candidate from audited tasks only.
2. Use a conservative mainline design:

```text
primary_design: repo_stratified_or_block_randomized_stratified
primary_score: unweighted pass rate by repo/split, then pooled summary
```

3. Do not use the old naive weighted design as primary.
4. Split tasks into `B_eval` and `H_future` or equivalent preregistered
   evaluation splits. The split plan must state:
   - repo;
   - split;
   - candidate id;
   - source context class;
   - task time bucket;
   - task family/module if available;
   - seed;
   - tie-breaking rule;
   - imbalance diagnostics.
5. Prefer block-randomized or stratified assignment where supply allows.
6. If the package is a small pilot, explicitly label it as pilot-grade and do
   not claim precision-target predictive validity.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_split_plan.json
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_split_plan.md
```

Acceptance:

- Split assignment is deterministic from a recorded seed and rules.
- H_future outcomes are not used to select, weight, or split tasks.
- The split plan includes all task ids needed for the later paid runbook.

Commit guidance:

- Commit release selection config and split-plan artifacts together.

## Step 4 - Baseline And Diagnostic Plan

Goal: freeze what the paid run will compare before seeing paid outcomes.

Actions:

1. Preregister these baselines unless a report explains why one is infeasible:
   - repo-unweighted same budget;
   - repo-stratified same budget;
   - temporal-recent baseline;
   - old weighted design as diagnostic only;
   - optional block-randomized stratified candidate.
2. Define which design is primary and which are secondary/diagnostic.
3. Define how scores will be aggregated:
   - per repo;
   - pooled;
   - B_eval-to-H_future predictive gap;
   - uncertainty intervals;
   - non-scoreable handling.
4. Record no post-hoc promotion rule. A secondary design can be informative,
   but it must not be reported as the primary result after seeing outcomes.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_baseline_plan.json
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_baseline_plan.md
```

Acceptance:

- Primary, baseline, and diagnostic designs are clearly separated.
- The old weighted design is not silently treated as the main claim.

Commit guidance:

- Commit baseline-plan artifacts as one scoped commit.

## Step 5 - Threshold Preregistration

Goal: make success and failure rules explicit before paid validation.

Actions:

1. Preregister primary metrics:
   - per-repo B_eval to H_future absolute gap;
   - pooled absolute gap;
   - scoreability rate;
   - policy violation count;
   - endpoint compliance;
   - cost/latency accounting completeness.
2. Preregister acceptable thresholds. At minimum include:

```text
policy_violations_max: 0
paid_endpoint_required: LLM_BASE_URL + LLM_API_KEY
raw_oracle_exposure_allowed: false
non_scoreable_cell_handling: preregistered
minimum_scoreability_rate: explicit value
primary_gap_threshold: explicit value or pilot-only no-claim label
precision_label_rules: explicit
```

3. If the selected package is underpowered, state that clearly and label the
   next paid run as a pilot, not a precision-target validation.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_threshold_preregistration.json
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_threshold_preregistration.md
```

Acceptance:

- The threshold report says exactly what would count as success, failure, or
  underpowered evidence.
- It does not claim predictive validity before paid cells run.

Commit guidance:

- Commit threshold artifacts as one scoped commit.

## Step 6 - Power, Cost, And Paid Batch Plan

Goal: make the paid cost and runtime risk visible before committing budget.

Actions:

1. Produce at least two paid batch options:

```text
small_pilot:
  smallest useful three-repo pilot
  lower cost
  weaker precision

primary_pilot:
  recommended next paid batch
  enough cells to compare primary design and baselines
  still not necessarily precision-target
```

2. For each option report:
   - repos;
   - task counts by repo/split;
   - ACUT adapters/harnesses;
   - total paid cells;
   - expected cost range;
   - expected runtime;
   - stop conditions after each batch;
   - scoreability and policy gates.
3. If cost estimates require historical observed cost, use committed cost
   summaries only. Do not inspect raw paid transcripts.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_power_cost_plan.json
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_power_cost_plan.md
```

Acceptance:

- The report recommends one batch option.
- The report explains what evidence that batch can and cannot support.
- The report defines stop-after-batch rules.

Commit guidance:

- Commit power/cost artifacts as one scoped commit.

## Step 7 - Entry Gate

Goal: decide whether a future paid validation runbook can safely execute.

Actions:

1. Check all non-paid gates:
   - three repos at 30 release eligible;
   - source-quality audit passed;
   - release candidate frozen;
   - split plan frozen;
   - baseline plan frozen;
   - thresholds frozen;
   - power/cost plan frozen;
   - endpoint variables present or blocker recorded;
   - no raw logs/workspaces committed;
   - tests pass.
2. Record every failed gate and exact blocker.
3. Do not run paid cells.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_entry_gate.json
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_entry_gate.md
```

Acceptance:

- The entry gate says one of:

```text
ready_for_paid_validation_runbook
blocked_source_quality
blocked_split_or_threshold_preregistration
blocked_endpoint_compliance
blocked_tests_or_artifact_hygiene
```

Commit guidance:

- Commit entry-gate artifacts as one scoped commit.

## Step 8 - Decision And Closeout

Goal: give the coordinating session a clear next decision.

Actions:

1. Write the final decision report.
2. Answer these research questions:

```text
RQ1: Which tasks and repos are frozen into the paid entry package?
RQ2: Did source-quality audit pass for attrs, boltons, and click?
RQ3: What is the primary design: repo-stratified, block-randomized stratified,
     unweighted, or something else?
RQ4: Which baselines and diagnostics are frozen?
RQ5: What thresholds and non-scoreable handling are preregistered?
RQ6: What paid batch option is recommended and what will it cost?
RQ7: Is the package ready for a paid validation runbook?
RQ8: Were any paid ACUT or paid LLM calls made?
```

3. Record completed steps, commits made during the run, tests run, and known
   blockers.
4. Do not draft a follow-up runbook.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_decision.json
experiments/phase1_compiler/reports/phase1_three_repo_paid_readiness_packaging_decision.md
```

Acceptance:

- The decision says one of:

```text
ready_for_paid_validation_runbook
blocked_before_paid_validation
pilot_package_ready_but_precision_target_not_claimable
```

- The report uses simple language and does not overclaim predictive validity.

Commit guidance:

- Commit closeout artifacts as the final runbook execution commit.

## Verification

At minimum, run:

```bash
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_three_repo_paid_readiness_packaging.py -q
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q
git diff --check
git status --short --untracked-files=all
```

If the full test suite is too slow or blocked, run focused tests plus the
nearest related tests and record the reason.

## Final Reporting Template

The final worker summary should be short and in simple Chinese:

```text
这次 runbook 做的是 paid-readiness packaging，没有运行 paid validation。

结果：
- 进入 package 的 repo：attrs、boltons、click。
- release-eligible 数量：attrs=N，boltons=N，click=N。
- source-quality audit：通过/未通过。
- 主设计：...
- baseline/diagnostic：...
- 推荐 paid batch：...
- entry gate：ready/blocked。

如果 blocked，原因是：
- source quality，或
- split/threshold 没冻结，或
- endpoint compliance，或
- 测试/artifact hygiene。

没有运行 paid ACUT solver cells、paid replication、paid LLM generation/review。
```

