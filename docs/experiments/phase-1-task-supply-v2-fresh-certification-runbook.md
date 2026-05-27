# Phase 1 Task Supply v2 Fresh Certification Runbook

Status: implementation runbook, 2026-05-27.

This runbook is for one dedicated Codex CLI session. Its job is to turn the
Task Supply v2 inventory into real local certification evidence.

```text
Do the 829 repo-history v2 candidates actually produce enough locally
certified, source-auditable tasks for Phase 1 paid validation?
```

Plain-language summary:

```text
The previous run found many possible task anchors. It did not prove those
anchors are usable tasks.

This runbook puts every v2 candidate into a fresh certification funnel. Some
candidates will stop early because they have no changed-test oracle or weak
source context. Candidates with a usable oracle should be run through the local
reference/no-op certification gates under current and historical environment
profiles.

At the end, count only tasks that really passed the gates and are safe enough
for a future release candidate. Do not count raw inventory as supply.
```

This is a local-only certification runbook. Do not run paid ACUT cells, paid
task-solving calls, paid replication, paid LLM statement generation, or any
other paid model call.

## Starting Point

The previous Task Supply v2 bakeoff ended with this decision:

```text
primary_decision_label: continue_internal_repo_history_v2
paid_ready: false
recommended_next_action: continue_internal_generator_v2_on_selected_repos
```

The important result was:

```text
raw v2 candidates: 829

attrs:    300 candidates
boltons:  233 candidates
toolz:    204 candidates
humanize:  92 candidates
```

The previous run also warned:

```text
Broad local mining found more candidate anchors, but certified supply is still
not paid-ready. The next useful move is to certify the v2 pool and repair weak
source-context/oracle paths.
```

The current paid-readiness projection is conservative:

```text
attrs:    22
boltons:  31
toolz:     6
humanize: 12
```

That projection does not include fresh certification of the 829 v2 candidates.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-task-supply-v2-fresh-certification-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md first. Use uv for
repo-local Python tooling. Follow AGENTS.md step-level acceptance and commit
requirements: after each step, or each small group of tightly related steps,
commit the changed files with an appropriately scoped commit.

Main goal: run a fresh local certification funnel for the 829 Task Supply v2
repo-history candidates. Every candidate must receive a terminal classification.
Only candidates with a usable changed-test oracle should be executed through
the local reference/no-op certification runner. Count release eligibility
separately from technical certification.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. Whether it argues for paid readiness, more internal mining, source-context
   repair, environment repair, or external-source work.

Do not run paid ACUT cells, paid task-solving calls, paid replication, paid
LLM statement generation, or any provider call that is not explicitly local.
Do not commit raw prompts, raw completions, raw command logs, workspaces,
external repository clones, caches, .venv directories, or large raw outputs.
```

## Inputs

Read these files before making changes:

```text
AGENTS.md
docs/experiments/phase-1-task-supply-v2-generator-bakeoff-runbook.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_raw_anchor_inventory.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_source_context_inventory.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_oracle_extraction_matrix.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_environment_profile_matrix.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_paid_readiness_gate.md
experiments/phase1_compiler/reports/phase1_historical_environment_recovered_supply_projection.md
```

Use these machine-readable inputs:

```text
experiments/phase1_compiler/results/phase1_task_supply_v2_raw_anchor_inventory.json
experiments/phase1_compiler/results/phase1_task_supply_v2_source_context_inventory.json
experiments/phase1_compiler/results/phase1_task_supply_v2_oracle_extraction_matrix.json
experiments/phase1_compiler/results/phase1_task_supply_v2_environment_profile_matrix.json
experiments/phase1_compiler/results/phase1_task_supply_v2_current_supply_reproduction.json
experiments/phase1_compiler/results/phase1_historical_environment_synthesis_decision.json
experiments/phase1_compiler/results/phase1_historical_environment_recovered_supply_projection.json
experiments/phase1_compiler/schemas/task_source_candidate_v2.schema.json
experiments/phase1_compiler/configs/phase1_task_supply_v2_generator_bakeoff.yaml
```

Useful existing implementation references:

```text
experiments/phase1_compiler/tools/phase1_task_supply_v2_generator_bakeoff.py
experiments/phase1_compiler/tools/phase1_historical_environment_synthesis_gate.py
experiments/phase0_headroom/tools/repo_history_pilot.py
experiments/phase1_compiler/tests/test_phase1_task_supply_v2_generator_bakeoff.py
```

## Outputs

Create a new local-only run under this prefix:

```text
phase1_task_supply_v2_fresh_certification
```

Expected committed outputs:

```text
experiments/phase1_compiler/configs/phase1_task_supply_v2_fresh_certification.yaml
experiments/phase1_compiler/tools/phase1_task_supply_v2_fresh_certification.py
experiments/phase1_compiler/tests/test_phase1_task_supply_v2_fresh_certification.py
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_preflight.json
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_candidate_funnel.json
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_attempts.json
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_subgate_summary.json
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_source_review_queue.json
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_paid_readiness_gate.json
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_decision.json
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_process.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_candidate_funnel.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_attempts.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_subgate_summary.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_paid_readiness_gate.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_decision.md
```

Allowed ignored outputs:

```text
experiments/phase1_compiler/tmp/task_supply_v2_fresh_certification/
experiments/phase0_headroom/workspaces/task_supply_v2_fresh_certification/
experiments/phase0_headroom/cache/task_supply_v2_fresh_certification/
```

Raw stdout/stderr logs may be written under ignored tmp paths, but committed
JSON and Markdown must contain only sanitized command metadata, return codes,
durations, subgate labels, and short hashes.

## Definitions

Use these terms consistently:

```text
raw_candidate:
  A row from phase1_task_supply_v2_raw_anchor_inventory.json.

oracle_usable:
  The candidate has changed tests that can be extracted as a private verifier
  oracle. Issue-only candidates without changed tests are inventory only.

technical_certified:
  The candidate passed checkout, oracle extraction, no-op fail, reference pass,
  flakiness, cost, scope, and leakage checks under one accepted environment
  profile.

release_eligible:
  The candidate is technical_certified and also passes source-context policy for
  a future release candidate. In this run, source-context policy means either
  non-leaky issue/PR context exists or the candidate is explicitly put in a
  manual/endpoint-compliant review queue and not counted yet.

paid_ready:
  At least three repos have 30 or more release_eligible candidates, raw logs and
  workspaces are not committed, subgate labels are present for failures, and
  unreviewed material leakage risk is not silently accepted.
```

This distinction matters. A repo can have many technical_certified tasks but
still be below paid readiness if the solver-facing source context is weak.

## Step 0 - Preflight And Dirty-Tree Audit

Goal: prove the run starts from a known local state.

Actions:

1. Run `git status --short --untracked-files=all`.
2. Confirm the current branch and latest commit.
3. Confirm no paid endpoint call is needed for this run.
4. Confirm the v2 raw anchor inventory exists and has 829 rows.
5. Confirm external repo paths exist or record which ones are missing.
6. Confirm ignored workspace/tmp/cache paths are not staged.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_preflight.json
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_process.md
```

Acceptance:

- The report states the exact starting commit.
- The report lists dirty/untracked files and classifies them as either relevant,
  ignored artifact output, or unrelated.
- The report says no paid ACUT or paid LLM calls were made.

Commit guidance:

- If this step creates only preflight artifacts, commit them as one preflight
  commit.
- If the dirty tree contains unrelated user changes, do not stage them.

## Step 1 - Configure The Fresh Certification Run

Goal: create a clear config before implementing the runner.

Create:

```text
experiments/phase1_compiler/configs/phase1_task_supply_v2_fresh_certification.yaml
```

The config should include:

```text
run_id: phase1_task_supply_v2_fresh_certification_20260527
input_raw_anchor_inventory
input_task_source_candidate_schema
target_repos
repo local paths and repo URLs
candidate_funnel_policy
environment_profile_policy
certification caps
timeouts
source_context_policy
paid_readiness_policy
output paths
ignored scratch paths
```

Recommended candidate execution policy:

```text
All 829 raw candidates must enter the funnel.
All candidates without usable changed-test oracle get terminal status
oracle_missing_inventory_only.
For oracle-usable candidates, execute certification in repo waves.
Preferred repo order: attrs, humanize, toolz, boltons.
Within each repo, prioritize non-leaky issue/PR context, then PR-title-only,
then commit-message-only.
Do not infer no supply from candidates that were not executed because of a cap.
```

Recommended caps:

```text
single_command_timeout_seconds: 120
single_candidate_total_timeout_seconds: 600
environment_profiles_per_candidate: 5
first_wave_attempt_cap_by_repo:
  attrs: 160
  humanize: 92
  toolz: 160
  boltons: 80
stretch_goal:
  continue until all oracle-usable candidates are attempted if runtime remains
  reasonable and the worker can keep committing sanitized evidence by step.
```

Acceptance:

- Config is deterministic and local-only.
- Config clearly separates first-wave cap from stretch goal.
- Config does not say unattempted candidates are failures.

Commit guidance:

- Commit config and any tiny documentation adjustment together.

## Step 2 - Build Candidate Funnel And Terminal Classifications

Goal: every raw candidate gets a terminal pre-certification classification.

Implement or extend:

```text
experiments/phase1_compiler/tools/phase1_task_supply_v2_fresh_certification.py
```

The candidate funnel must read the 829 rows and emit one row per candidate with
at least these fields:

```text
candidate_id
repo_id
source_reservoir
base_commit
target_commit_optional
has_usable_oracle
test_files
implementation_files
source_context_class
source_context_quality
leakage_risk
execution_priority
pre_certification_status
pre_certification_subgate
selected_for_execution
selection_reason
not_selected_reason
```

Required terminal pre-certification subgates:

```text
selected_for_certification
oracle_missing_inventory_only
duplicate_candidate
base_or_target_commit_missing
changed_test_oracle_missing
implementation_scope_missing
material_leakage_risk
source_context_weak_needs_review
candidate_outside_scope
not_attempted_cap_deferred
```

Important rules:

- Issue-only candidates without changed tests are not discarded. They are
  recorded as inventory-only and not counted as certified.
- Commit-message-only candidates may be technically certified, but they are not
  release_eligible unless the run adds a manual or endpoint-compliant review
  artifact. This run should not call a paid endpoint, so most such candidates
  should enter the source review queue.
- Deduplicate by a stable key derived from repo, base commit, target commit,
  implementation files, and test files.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_candidate_funnel.json
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_candidate_funnel.md
```

Acceptance:

- The candidate funnel accounts for all 829 raw rows.
- The report shows counts by repo, reservoir, oracle availability, source
  context class, selected/deferred status, and first terminal subgate.
- The report explains in simple language why raw supply differs from certified
  supply.

Commit guidance:

- Commit the candidate funnel implementation, tests, and generated sanitized
  funnel artifacts together.

## Step 3 - Add Focused Tests Before Full Execution

Goal: make the certification accounting hard to accidentally inflate.

Add tests covering:

```text
829 input rows must all be classified.
oracle_missing candidates are inventory-only and not executed.
technical_certified and release_eligible are separate counts.
commit-message-only technical passes are not release_eligible without review.
unattempted candidates caused by a cap are not counted as failures.
subgate labels are present for every non-certified row.
raw stdout/stderr text is not written into committed JSON.
paid_ready requires at least three repos with >=30 release_eligible tasks.
```

Expected command:

```text
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_task_supply_v2_fresh_certification.py -q
```

Acceptance:

- Focused tests pass.
- Tests do not require external network or paid model calls.

Commit guidance:

- If Step 2 did not already include tests, commit this as a focused test commit.

## Step 4 - Implement Fresh Local Certification Runner

Goal: actually run local reference/no-op certification for selected v2
candidates.

Implementation requirements:

1. Reuse existing helpers where possible from:

```text
experiments/phase0_headroom/tools/repo_history_pilot.py
experiments/phase1_compiler/tools/phase1_historical_environment_synthesis_gate.py
```

2. For each selected candidate, build clean base and target workspaces from git
   commits.

3. Extract the changed test patch from base to target. Treat empty or
   non-applicable patches as oracle failures, not as reference failures.

4. Run no-op behavior:

```text
base workspace + changed test oracle should fail
```

5. Run reference behavior twice:

```text
target workspace + changed test oracle should pass twice
```

6. Try the current profile first, then bounded historical profiles. Record the
   winning profile if one exists.

7. Classify every failure with a precise subgate. Do not store all setup/import
   failures as `reference_pass`.

Required execution subgates:

```text
checkout_failed
oracle_patch_empty
oracle_patch_apply_failed
environment_unavailable
install_failed
import_failed
collect_failed
noop_assert_failed
reference_assert_failed
flaky_reference
timeout
unknown_failed
technical_certified
```

Required sanitized command metadata:

```text
role
profile_id
returncode
duration_seconds
timed_out
stdout_tail_hash
stderr_tail_hash
subgate_label
```

Do not commit raw stdout, raw stderr, full workspace paths, solver workspaces,
verifier workspaces, cloned external repositories, or dependency caches.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_attempts.json
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_attempts.md
```

Acceptance:

- Every selected candidate has exactly one terminal execution status.
- The attempts report separates attempted, technical_certified, failed,
  deferred, and not-selected counts.
- The report shows median and total runtime by repo.
- Failure subgates are more specific than the old coarse `reference_pass`
  label.

Commit guidance:

- Commit runner code and tests before committing large generated result files.
- After each completed repo wave, commit sanitized results and reports for that
  wave if they are stable.

## Step 5 - Execute Certification Waves

Goal: get useful evidence without turning runtime into an uncontrolled batch.

Run waves in this order:

```text
1. attrs first wave
2. humanize full or capped wave
3. toolz first wave
4. boltons calibration wave
5. stretch continuation for any repo that is close to 30 release_eligible tasks
```

Why this order:

```text
attrs is closest to 30 under the conservative paid gate and has more issue/PR
context than toolz or humanize.

humanize had a strong old 16-candidate yield, so it is worth checking whether
that yield holds beyond the narrow old artifact.

toolz has many raw candidates but weak source context, so it needs evidence
before we treat it as a paid-ready repo.

boltons already reached 31 under the conservative projection, so it is useful
as calibration but should not consume the first runtime budget.
```

Stop conditions:

```text
Continue a repo until one of these is true:
- all oracle-usable selected candidates for that repo have been attempted;
- the configured first-wave cap is reached;
- the repo reaches at least 35 technical_certified and at least 30
  release_eligible tasks;
- repeated environment failures show a clear blocker and the report records
  the blocker with enough evidence to continue later;
- the runbook-level local runtime cap is reached.
```

Important:

```text
If a cap stops execution, record deferred candidates as not_attempted_cap_deferred.
Do not mark them failed.
Do not claim the repo lacks supply based on unattempted candidates.
```

Acceptance:

- At least attrs, humanize, and toolz receive fresh execution evidence unless
  preflight finds a concrete blocker.
- Boltons is either run as a calibration wave or explicitly deferred with a
  reason.
- Each completed wave has a process note and a commit.

## Step 6 - Build Source Review Queue

Goal: avoid counting weak statements as release-ready supply.

Create:

```text
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_source_review_queue.json
```

The queue should include technical_certified tasks that are not release_eligible
because of source-context quality.

Required fields:

```text
candidate_id
repo_id
technical_certified
source_context_class
allowed_context_refs
why_not_release_eligible
minimum_review_needed
suggested_review_mode
```

Allowed suggested review modes:

```text
manual_review
endpoint_compliant_statement_review_future
public_issue_pr_enrichment
drop_from_release_candidate
```

This run should not perform endpoint statement review. It should only create
the queue and say how many tasks might become release_eligible if reviewed.

Acceptance:

- The queue clearly separates "technically works" from "safe to release".
- The report states how many additional release_eligible tasks each repo could
  gain through source-context repair.

Commit guidance:

- Commit this queue and its report separately if it changes the paid-readiness
  interpretation.

## Step 7 - Recompute Paid Readiness

Goal: answer the main decision question with the new evidence.

Create:

```text
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_paid_readiness_gate.json
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_paid_readiness_gate.md
```

The gate must report:

```text
release_eligible_count_by_repo
technical_certified_count_by_repo
source_review_queue_count_by_repo
oracle_missing_inventory_only_count_by_repo
not_attempted_cap_deferred_count_by_repo
repos_meeting_30_release_eligible
paid_ready
blocking_reasons
paid_acut_calls_made: false
paid_llm_calls_made: false
```

Minimum paid-ready requirements:

```text
at_least_3_repos_with_30_release_eligible: true
subgate_labels_present_for_failures: true
raw_logs_workspaces_not_committed: true
no_unreviewed_material_leakage_risk: true
source_reservoir_mix_policy_checked: true
no_paid_acut_calls_made: true
no_paid_llm_statement_generation_made: true
```

Acceptance:

- Paid readiness is based on release_eligible counts, not raw candidates and not
  technical certification alone.
- The report lists exactly which repos meet 30 and which do not.
- The report explains the next bottleneck in simple language.

Commit guidance:

- Commit paid-readiness outputs with the final decision outputs if they are
  generated together.

## Step 8 - Write Decision And Closeout

Goal: make the result easy for the coordinating session to interpret.

Create:

```text
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_decision.json
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_decision.md
```

The decision must choose one primary label:

```text
paid_validation_gate_met
continue_source_context_repair
continue_environment_repair
continue_repo_history_v2_certification
screen_additional_repo
external_source_adapter_spike
blocked
```

Answer these research questions:

```text
RQ1. How many of the 829 raw v2 candidates reached each terminal funnel state?
RQ2. How many candidates were technically certified by repo?
RQ3. How many candidates were release_eligible by repo?
RQ4. Did at least three repos reach 30 release_eligible tasks?
RQ5. If not, what is the dominant blocker: oracle, source context,
     environment, no-op/reference behavior, scope/leakage, or runtime cap?
RQ6. Did broad v2 mining change the earlier conclusion about toolz or
     humanize?
RQ7. What should the next coordinating runbook do?
```

The closeout must include:

```text
completed steps
commits made during the run
tests run and results
files changed
raw artifact hygiene statement
paid-call statement
known blockers
recommended next actions
```

Acceptance:

- The report is understandable without reading raw JSON.
- It does not draft the next runbook unless the user explicitly asked the
  worker to do so.
- It does not claim predictive validity or paid ACUT readiness unless the gate
  actually passed.

Commit guidance:

- Commit the final decision, closeout, and any stable generated summaries as
  the final runbook commit.

## Verification

Before the final commit, run:

```text
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_task_supply_v2_fresh_certification.py -q
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q
git diff --check
git status --short --untracked-files=all
```

If full tests are too slow or fail for an unrelated reason, record that clearly
in the closeout report with the exact command and failure summary. Do not hide
test failures.

## Expected Interpretations

Use these interpretation rules:

```text
If three repos have >=30 release_eligible tasks:
  The next coordinating step can design a paid validation entry gate.

If three repos have >=30 technical_certified tasks but fewer release_eligible
tasks:
  The next bottleneck is source-context repair, not environment or raw supply.

If raw supply is high but technical certification is low:
  The next bottleneck is certification mechanics, oracle quality, or historical
  environment support.

If attrs remains below 30 but humanize or toolz rises above 30:
  Phase 1 should consider replacing attrs or using a broader repo mix.

If most failures are not_attempted_cap_deferred:
  The run was a partial certification wave. Do not call it a negative result.

If most failures are oracle_missing_inventory_only:
  v2 mining found useful issue inventory, but Barcarolle still lacks an
  acceptable oracle path for those tasks.
```

## Non-Goals

This runbook does not:

- run paid ACUT validation;
- run paid task solving;
- run paid statement generation or review;
- promote generated oracle tasks into evaluation supply;
- adopt SWE-Bench++, SWE-smith, SWE-bench-Live, or R2E-style tasks as default
  supply;
- build a Docker or Nix environment factory;
- freeze a benchmark release;
- claim predictive validity;
- reimplement the ACUT harness.

These remain future directions unless a later coordinating session explicitly
chooses them.
