# Phase 1 Task Supply v2 Generator Bakeoff Runbook

Status: implementation runbook, 2026-05-27.

This runbook is for one dedicated Codex CLI session. Its job is to move Phase 1
from "which repo should we try next?" to a clearer question:

```text
Can Barcarolle's task supply layer produce enough certified, clear,
source-diverse, auditable tasks for target-repo benchmark compilation?
```

Plain-language summary:

```text
The current generator is too thin. It mostly mines commits that changed both
code and tests, then tries to certify them. That is useful, but it is not
enough to prove a repo has or lacks task supply.

This runbook builds and measures Task Supply v2. It keeps Barcarolle's own
certification and benchmark-compiler boundary, broadens local repo-history
mining, integrates historical environment subgates, and runs a local-only
generator bakeoff before any paid validation.
```

This is a local-only supply and tooling runbook. Do not run paid ACUT cells,
paid replication, paid task-solving calls, or paid LLM statement generation.

## Starting Point

Recent evidence points to a task-supply bottleneck:

```text
two-repo supply expansion:
  attrs total eligible after expansion:   20
  boltons total eligible after expansion: 27
  target: at least 30 per repo

historical environment synthesis:
  known reference-pass failures sampled: 36
  recovered reference_pass: 8
  confirmed recovered eligible:
    attrs:   +2, projected total 22
    boltons: +4, projected total 31

third-repo quick screen using existing local artifacts:
  toolz:    16 candidates, 6 certified
  humanize: 16 candidates, 12 certified
```

Important interpretation:

```text
The quick toolz/humanize screen does not prove those repos lack supply.
It proves the existing local artifacts are too narrow.

The reference-pass audits do not prove local validation code is broadly wrong.
They show old environment failures were being hidden behind a coarse
reference_pass label.
```

An external GPT-5.5-Pro review in
`/Users/chenmohan/Downloads/barcarolle-research-0526-1.md` recommended a
hybrid path:

```text
stronger internal repo-history / PR / issue generator
+ external source adapters as feasibility trials and future reservoirs
+ Barcarolle-owned certification, source mixing, and benchmark compilation
+ local generator bakeoff before paid ACUT validation
```

This runbook implements the next local step. It does not try to solve every
future task-generation idea at once.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-task-supply-v2-generator-bakeoff-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md first. Use uv for
repo-local Python tooling. Make a cohesive git commit after every completed
step that changes files. Do not batch unrelated steps into one commit. Do not
push unless the user explicitly asks.

Main goal: implement and run a local-only Task Supply v2 generator bakeoff.
Compare the current repo-history adapter against a broader repo-history v2
path, historical-environment-aware certification, and small external-source
feasibility checks. Decide which repo/source paths are viable for the next
benchmark compiler step.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. Whether it argues for broader internal mining, external-source feasibility,
   repo replacement, or future work.

Do not run paid ACUT cells, paid replication, paid task-solving calls, or paid
LLM statement generation. Do not use hidden verifier material, raw ACUT
transcripts, raw prompts, raw completions, solver workspaces, or verifier
workspaces.

Do not implement ACUT internals. Barcarolle may normalize task candidates,
build workspaces, infer local environments, run certification checks, classify
benchmark-side failures, and record sanitized artifacts.

Do not treat SWE-Bench++, SWE-smith, SWE-bench-Live, SWE-Gym, or R2E-Gym as
trusted task sources. External candidates, if any are inspected, are untrusted
inputs and must pass Barcarolle-side schema, provenance, license, and local QA
checks before they can count as future supply.

Do not commit secrets, raw stdout/stderr logs, full raw prompts, raw
completions, raw ACUT transcripts, solver workspaces, verifier workspaces,
target repo clones, .venv, uv caches, Docker layers, or large raw outputs.
Commit only small sanitized configs, schemas, tools, tests, JSON/CSV summaries,
reports, manifests, and digests.

Raw logs, temporary workspaces, external repo clones, downloaded datasets, and
package caches must stay under ignored local paths.

If you find a production certification-code change is needed, first add a
focused regression test that captures the expected behavior. Then make the
smallest fix and rerun the focused test plus the relevant suite.

Do not draft or create a follow-up runbook. Instead, record completed work,
blockers, decisions, and future-direction candidates in the closeout report.
```

## Required Inputs

Use these artifacts if present:

```text
AGENTS.md
docs/architecture/system-design.md
docs/restart/2026-05-20-restart-consensus.md
docs/experiments/phase-1-two-repo-certified-supply-expansion-runbook.md
docs/experiments/phase-1-reference-pass-failure-audit-runbook.md
docs/experiments/phase-1-historical-environment-synthesis-and-third-repo-gate-runbook.md
/Users/chenmohan/Downloads/barcarolle-research-0519.md
/Users/chenmohan/Downloads/barcarolle-research-0526.md
/Users/chenmohan/Downloads/barcarolle-research-0526-1.md

experiments/phase0_headroom/configs/repositories.yaml
experiments/phase0_headroom/tools/repo_history_pilot.py
experiments/phase0_headroom/tools/statement_quality.py
experiments/phase0_headroom/tools/test_repo_history_pilot.py
experiments/phase0_headroom/external_repos/attrs
experiments/phase0_headroom/external_repos/boltons
experiments/phase0_headroom/external_repos/toolz
experiments/phase0_headroom/external_repos/humanize

experiments/phase1_compiler/tools/phase1_two_repo_certified_supply_expansion.py
experiments/phase1_compiler/tools/phase1_reference_pass_failure_audit.py
experiments/phase1_compiler/tools/phase1_historical_environment_synthesis_gate.py
experiments/phase1_compiler/tests/test_phase1_reference_pass_failure_audit.py
experiments/phase1_compiler/tests/test_phase1_historical_environment_synthesis_gate.py

experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_decision.json
experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_raw_candidates.json
experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_source_contexts.json
experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_certification_attempts.json
experiments/phase1_compiler/results/phase1_reference_pass_failure_audit_decision.json
experiments/phase1_compiler/results/phase1_historical_environment_synthesis_decision.json
experiments/phase1_compiler/results/phase1_third_repo_environment_gate_screen.json

experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/README_FOR_EXTERNAL_GPT55_PRO.md
experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/TASK_GENERATOR_PROBLEM_BRIEF.md
```

If an input has moved or is missing, record that in the preflight report and
continue with available committed artifacts.

## Budget And Runtime Rules

This runbook is local-only.

```text
paid ACUT calls: disabled
paid task-solving calls: disabled
paid replication: disabled
paid LLM statement generation: disabled
provider cost change: 0
```

Network access is allowed only for public metadata, public repo refreshes,
public package resolution, and external-source feasibility inspection. Do not
make paid API calls.

Use these caps unless a blocker report explains why they are impossible:

```text
target repos:
  attrs
  boltons
  toolz
  humanize

history scan cap per repo:
  all commits since 2010 or first 2,000 commits, whichever is smaller

raw candidate cap per repo per source arm:
  300

local certification attempt cap per repo for repo_history_v2:
  120

local certification attempt cap per repo for external feasibility:
  60

environment profiles per task:
  baseline + inferred profile + at most 2 fallbacks

single command timeout:
  120 seconds

single task total certification timeout:
  10 minutes
```

If the worker cannot keep the run inside these caps, stop the affected arm,
write a cost/cap blocker, and continue other arms.

## Claim Boundary

Allowed claims:

```text
task_supply_v2_preflight_completed
task_source_candidate_schema_defined
repo_history_v1_reproduction_completed
repo_history_v2_broad_mining_completed
source_context_inventory_completed
historical_environment_subgate_integration_completed
oracle_extraction_inventory_completed
local_certification_bakeoff_completed
external_source_feasibility_completed
source_mixing_policy_drafted
task_supply_future_directions_recorded
paid_readiness_gate_completed
no_paid_acut_calls_made
no_paid_llm_statement_generation_made
```

Disallowed claims:

```text
predictive_validity_established
paid_replication_completed
new_paid_acut_cells_run
new_paid_llm_statement_generation_run
SWE_Bench_plus_plus_adopted_as_default_generator
SWE_smith_adopted_as_default_generator
synthetic_tasks_validated_as_future_work_proxy
generated_oracle_tasks_promoted_to_eval_pool
benchmark_release_frozen
third_repo_paid_smoke_ready_without_supply_gate
hidden_oracle_informed_generation
raw_transcript_informed_generation
raw_prompt_or_completion_informed_generation
ACUT_harness_reimplemented
followup_runbook_written_by_worker
```

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_task_supply_v2_generator_bakeoff.yaml
  tools/
    phase1_task_supply_v2_generator_bakeoff.py
  tests/
    test_phase1_task_supply_v2_generator_bakeoff.py
    # also update existing tests if shared certification code changes
  results/
    phase1_task_supply_v2_preflight.json
    phase1_task_supply_v2_schema.json
    phase1_task_supply_v2_current_supply_reproduction.json
    phase1_task_supply_v2_repo_inventory.json
    phase1_task_supply_v2_raw_anchor_inventory.json
    phase1_task_supply_v2_source_context_inventory.json
    phase1_task_supply_v2_environment_profile_matrix.json
    phase1_task_supply_v2_oracle_extraction_matrix.json
    phase1_task_supply_v2_certification_attempts.json
    phase1_task_supply_v2_external_feasibility.json
    phase1_task_supply_v2_source_bakeoff_decision.json
    phase1_task_supply_v2_future_directions.json
    phase1_task_supply_v2_paid_readiness_gate.json
  reports/
    phase1_task_supply_v2_process.md
    phase1_task_supply_v2_schema.md
    phase1_task_supply_v2_current_supply_reproduction.md
    phase1_task_supply_v2_repo_inventory.md
    phase1_task_supply_v2_raw_anchor_inventory.md
    phase1_task_supply_v2_source_context_inventory.md
    phase1_task_supply_v2_environment_profile_matrix.md
    phase1_task_supply_v2_oracle_extraction_matrix.md
    phase1_task_supply_v2_certification_attempts.md
    phase1_task_supply_v2_external_feasibility.md
    phase1_task_supply_v2_source_bakeoff_decision.md
    phase1_task_supply_v2_future_directions.md
    phase1_task_supply_v2_paid_readiness_gate.md
```

Optional small schemas may be added under:

```text
experiments/phase1_compiler/schemas/
  task_source_candidate_v2.schema.json
  task_supply_bakeoff_result_v1.schema.json
```

Raw local artifacts must stay under ignored paths such as:

```text
experiments/phase1_compiler/tmp/task_supply_v2_generator_bakeoff/
experiments/phase0_headroom/workspaces/task_supply_v2_generator_bakeoff/
experiments/phase0_headroom/cache/task_supply_v2_generator_bakeoff/
experiments/phase0_headroom/external_repos/
```

Do not commit those raw paths.

## Research Questions

Answer these in the final decision report:

```text
RQ1: Is the current repo-history v1 supply path reproducibly too narrow for
     Phase 1 paid validation?

RQ2: Does repo-history v2 broad mining materially improve candidate yield,
     public-context quality, environment reconstruction, or certification
     yield on attrs, boltons, toolz, and humanize?

RQ3: Which failure modes dominate after historical-environment-aware subgate
     classification: source context, statement quality, environment,
     oracle extraction, no-op behavior, reference behavior, or cost?

RQ4: Do any repos reach at least 30 locally certified candidates under local
     gates, and do they have at least two usable source reservoirs?

RQ5: Are any external sources feasible enough to justify a real adapter later,
     without treating them as trusted or default supply now?

RQ6: Which ideas are explicitly not implemented in this run, and how should
     they be tracked as future evolution rather than silent rejection?

RQ7: What is the next coordinating decision: continue internal generator v2,
     broaden repo screening, run external-source feasibility, or prepare a
     benchmark assembly runbook?
```

## Task Supply v2 Design

### Candidate Schema

Define and test a normalized candidate schema. It may be JSON Schema or a small
validated Python model, but it must serialize to JSON/JSONL.

Minimum fields:

```yaml
schema_version: barcarolle.task_source_candidate.v2
candidate_id:
repo_id:
repo_url:
language:
source_system:
source_system_version:
source_reservoir:
source_license:
upstream_task_id:
base_commit:
target_commit_optional:
task_time:
source_time:
problem_statement:
problem_statement_provenance:
public_context_refs:
oracle:
  fail_to_pass:
  pass_to_pass:
  oracle_source:
environment:
  kind:
  profile_id:
  command_shape:
  dependency_time_policy:
changed_files:
implementation_files:
test_files:
reference_patch_digest_optional:
gold_patch_available_to_barcarolle:
gold_patch_exposed_to_solver: false
leakage_flags:
ambiguity_flags:
candidate_labels:
source_confidence:
raw_artifact_paths_uncommitted:
```

Required source reservoirs:

```text
repo_history_v1_commit_with_tests
repo_history_v2_pr_issue_with_tests
repo_history_v2_commit_with_tests
repo_history_v2_issue_without_changed_tests
external_swe_bench_plus_plus_feasibility
external_swe_smith_feasibility
external_swe_bench_live_feasibility
manual_or_customer_future_direction
synthetic_or_generated_oracle_future_direction
```

The last two may appear only in future-direction reports unless actually
implemented under local-only constraints.

### Source Arms

Compare these source arms:

```text
Arm A: repo_history_v1_baseline
  current thin adapter, current filters, current artifacts reproduced.

Arm B: repo_history_v2_real
  broader Git/PR/issue mining, source_reservoir labels, public context
  enrichment, historical environment profiles, reference subgates.

Arm C: repo_history_v2_oracle_inventory
  inventory issue/PR candidates without changed tests and estimate oracle
  recoverability. Do not promote generated oracle tasks to eval.

Arm D: external_source_feasibility
  inspect SWE-Bench++/SWE-smith/SWE-bench-Live/R2E-style source feasibility:
  license, schema mapping, repo overlap, environment cost, oracle type.
  Do not count external tasks as certified supply unless they pass local
  Barcarolle certification.

Arm E: hybrid_pool_diagnostic
  combine certified local candidates and feasible external candidate summaries
  only for source-mix diagnostics. Do not freeze a benchmark release.
```

## Explicit Non-Goals And Future Directions

This section is intentionally part of the runbook. The worker must update the
future-directions report with evidence for each item.

### Not Doing In This Run

Do not do these in this run:

```text
1. No paid ACUT validation.
2. No paid LLM statement generation.
3. No benchmark release freeze.
4. No predictive validity claim.
5. No default adoption of SWE-Bench++ as Barcarolle's generator.
6. No default adoption of SWE-smith as Barcarolle's generator.
7. No production use of generated oracle tasks in eval pools.
8. No broad multi-language generator implementation.
9. No full Docker image factory unless needed for a bounded feasibility check.
10. No ACUT harness reimplementation.
11. No raw prompt, raw completion, raw transcript, hidden oracle, or solver
    trace use in candidate generation or statement writing.
12. No manual cherry-picking of tasks based on paid outcomes.
```

### Future Direction Ledger

Record these as explicit future directions, not as rejected ideas:

```text
external_swe_bench_plus_plus_adapter:
  future question: Can public or licensed SWE-Bench++ artifacts be mapped into
  Barcarolle candidate schema and recertified locally?

external_swe_smith_adapter:
  future question: Can SWE-smith provide synthetic/test-breaking supply that
  improves target-repo predictive value when source-capped?

external_swe_bench_live_adapter:
  future question: Can live issue freshness provide target-repo or nearby-repo
  supply without contamination?

generated_oracle_pipeline:
  future question: Can generated tests support issue/PR candidates without
  changed tests while staying separate from real changed-test tasks?

endpoint_statement_generator_reviewer:
  future question: Can LLM_BASE_URL/LLM_API_KEY backed statement generation
  improve clarity without leakage, with raw prompts/completions kept out of git?

docker_or_nix_environment_factory:
  future question: When uv historical profiles are insufficient, can container
  environment synthesis recover tasks at acceptable cost?

manual_or_customer_regression_source:
  future question: How should customer-provided or expert-authored tasks enter
  the same candidate schema and certification gates?

multi_language_supply:
  future question: What changes are needed beyond Python after Phase 1?
```

For each future direction, the closeout must include:

```text
status: deferred | feasible_spike_completed | blocked
why_not_now
minimum_next_artifact
main_risk
suggested_owner_or_tooling
```

## Step 0: Preflight And Ledger

Actions:

1. Read `AGENTS.md`.
2. Record branch, HEAD, date, Python version, `uv --version`, and git status.
3. Record whether `gh` is authenticated if GitHub metadata will be used.
4. Record which target repos are locally available.
5. Confirm ignored scratch paths.
6. Confirm paid calls are disabled.
7. Create the config and process ledger.

Acceptance:

- Preflight records `paid_acut_calls: disabled`.
- Preflight records `paid_llm_calls: disabled`.
- Preflight records `raw_artifacts_committed: false`.
- Process report says in simple language that this is a supply-layer bakeoff,
  not a benchmark validation run.

## Step 1: Define TaskSourceCandidate v2

Actions:

1. Add a compact schema or validated Python model for normalized candidates.
2. Add conversion functions from current repo-history v1 candidates to v2.
3. Add validation for:

```text
required ids
base commit
source_reservoir
oracle source
environment profile shape
gold_patch_exposed_to_solver == false
raw artifact paths marked uncommitted
```

4. Add unit tests for valid and invalid candidates.

Acceptance:

- Existing attrs/boltons/toolz/humanize candidate rows can be mapped into v2.
- Invalid rows fail loudly with useful errors.
- Schema report explains the fields in simple language.

## Step 2: Reproduce Current Supply Baseline

Actions:

1. Reproduce current repo-history v1 counts for attrs, boltons, toolz, and
   humanize from committed artifacts.
2. Summarize:

```text
raw candidates
source contexts
certified tasks
near-certified tasks
first failing gate counts
commit-message-only count
public PR/issue context count
reference/environment failures
```

3. This is a baseline, not a new mining result.

Acceptance:

- The report states clearly what current artifacts prove and do not prove.
- The report warns that toolz/humanize old 16-candidate screens are not broad
  repo-supply conclusions.

## Step 3: Repo Inventory For Broad Mining

Actions:

For each target repo:

```text
attrs
boltons
toolz
humanize
```

Collect local metadata:

```text
default branch
HEAD
commit count since 2010
commit count with implementation changes
commit count with test changes
commit count with both implementation and test changes
visible issue/PR linkability signal
test framework hints
package manager hints
known external-service risk
```

Use existing repositories under ignored `external_repos/`. If a repo is missing,
clone or refresh it only under the ignored path.

Acceptance:

- Inventory identifies which repos are worth broad mining first.
- If a repo is missing or cannot be refreshed, the blocker is recorded but
  other repos continue.

## Step 4: Broad Repo-History v2 Mining

Actions:

1. Implement broader mining without replacing the old adapter yet.
2. Candidate reservoirs should include:

```text
merged PR or issue with changed tests
commit with implementation and changed tests
issue/PR with implementation change but no changed tests
commit/PR with source context but weak oracle
```

3. Mine up to the configured raw candidate cap per repo.
4. Keep full raw GitHub responses out of git. Commit only summaries and refs.
5. Add dedup keys:

```text
repo_id
base_commit
target_commit_optional
problem_context_ref
implementation path set digest
oracle path set digest
```

Acceptance:

- Each repo has a raw anchor inventory and normalized v2 candidate summary.
- The report separates "candidate found" from "candidate has usable oracle".
- No raw API payloads are committed.

## Step 5: Source Context Inventory

Actions:

For each v2 candidate, classify public context:

```text
non_leaky_issue_or_pr_context
pr_title_only_context
commit_message_only_context
diff_assisted_statement_needed
no_usable_public_context
material_leakage_risk
material_ambiguity_risk
```

Use deterministic rules first. If manual review is needed, write review packets
but do not use paid LLM calls.

Acceptance:

- The report shows source-context quality by repo and source reservoir.
- Commit-message-only supply is counted separately and not allowed to silently
  count as high-quality issue-like supply.

## Step 6: Environment Profile And Subgate Integration

Actions:

1. Reuse the historical environment synthesis mechanism where possible.
2. Add environment profile inference to the certification path:

```text
current profile
inferred historical uv profile
at most two bounded fallback profiles
```

3. Record subgate labels:

```text
checkout_failed
install_failed
import_failed
collect_failed
noop_assert_failed
reference_assert_failed
reference_pass
flaky_reference
timeout
environment_unavailable
unknown_failed
```

4. Add regression tests for classification and command construction.

Acceptance:

- Certification attempts no longer collapse install/import/collection failures
  into a single `reference_pass` failure.
- Environment command shape is sanitized and recorded.
- Raw stdout/stderr stays under ignored tmp paths.

## Step 7: Oracle Extraction Inventory

Actions:

1. For changed-test candidates, run the current fail-to-pass extraction.
2. Add a report-only inventory for issue/PR candidates without changed tests:

```text
oracle_missing
oracle_recoverable_from_existing_tests
oracle_requires_generated_tests
oracle_requires_manual_regression
oracle_out_of_scope_for_this_run
```

3. Do not promote generated oracle tasks to certified eval supply in this run.
4. If a simple existing-test recovery is possible without generation, record it
   as `recovered_existing_test_oracle`.

Acceptance:

- Real changed-test supply and missing-oracle supply are separated.
- The future-directions report records generated oracle as deferred unless a
  bounded feasibility spike was actually completed.

## Step 8: Local Certification Bakeoff

Actions:

Run certification under the configured caps for each repo/source arm.

For each repo × arm, report:

```text
attempt_count
certified_count
near_certified_count
first_failing_gate_counts
subgate_counts
median_seconds_per_attempt
wall_clock_per_certified
source_context_quality_counts
oracle_source_counts
source_reservoir_mix
module coverage
time bucket coverage
```

Stop early for an arm if:

```text
after 60 attempts:
  certified_count < 6
  and recoverable_env_fail_rate < 20%

or install/import/collect failures remain above 60% after one profile expansion

or leakage/material statement risk exceeds 25%

or median certification time exceeds 10 minutes
```

Acceptance:

- The bakeoff report can say which repo/source arms are actually worth
  continuing.
- No repo is rejected merely because an old 16-candidate artifact was small.

## Step 9: External Source Feasibility

Actions:

Run small feasibility checks for external sources as design inputs, not as
trusted supply:

```text
SWE-Bench++:
  license availability
  public artifact availability
  schema mapping
  repo overlap with target repos or nearby repos
  environment/oracle fields available

SWE-smith:
  install/runtime feasibility
  license
  target repo support
  generated task schema
  Docker/Ubuntu requirement
  local cost estimate

SWE-bench-Live / R2E-Gym:
  artifact availability
  license
  schema mapping
  freshness or synthetic-oracle relevance
```

Allowed output:

```text
feasible_for_future_adapter
feasible_only_as_design_reference
blocked_by_license
blocked_by_runtime_cost
blocked_by_missing_artifacts
blocked_by_target_repo_mismatch
```

Acceptance:

- External systems are compared concretely.
- No external source is called "adopted" or counted as certified default supply
  unless it has passed local Barcarolle certification under this run.

## Step 10: Source Mixing Policy

Actions:

Draft a source mixing policy for future benchmark release candidates:

```text
per repo certified candidates >= 30 before paid validation
at least 2 source reservoirs represented when possible
no single source reservoir > 70% of eval pool unless waived
commit-message-only tasks <= 20% unless manually reviewed
synthetic/generated oracle tasks <= 25% until predictive evidence supports more
all external tasks must be recertified locally
```

This policy can be a report section or a small JSON artifact. It should not
freeze an actual release.

Acceptance:

- The policy distinguishes local supply readiness from paid validation
  readiness.
- Any waiver is explicit and justified.

## Step 11: Future Direction Ledger

Actions:

Write the future-directions JSON and report. Include every non-goal listed
above.

For each item, record:

```text
direction_id
status
why_not_now
evidence_from_this_run
minimum_next_artifact
main_risk
recommended_priority: now | next | later | park
```

Acceptance:

- Deferred work is visible and organized.
- The report prevents readers from interpreting "not implemented in this run"
  as "rejected permanently."

## Step 12: Paid Readiness Gate

Actions:

Evaluate whether any path is ready for paid ACUT validation.

Minimum paid-readiness gate:

```text
at least 3 repos with >= 30 certified candidates, or a documented narrower
  Phase 1 scope approved by the coordinating session

per selected repo:
  certified candidates >= 30
  issue/PR or otherwise strong public context sufficient for statements
  reference pass reproducible twice
  subgate labels present for every failure
  flakiness sample failure <= 5%
  raw logs/workspaces not committed

source quality:
  at least 2 source reservoirs where feasible
  no unreviewed material leakage risk
  no hidden oracle or raw ACUT trace influence

algorithm readiness:
  local compiler/bakeoff gate still favors a simple stratified or better
  design before paid validation
```

Acceptance:

- The gate may say "not ready." That is a valid result.
- The report says exactly what is missing.
- No paid runbook is drafted by the worker.

## Step 13: Decision And Closeout

The final decision report must include:

```text
primary_decision_label
plain_language_summary
repos_screened
source_arms_compared
certified_count_by_repo_and_arm
best_source_arm_by_repo
dominant_failure_modes
external_source_feasibility_summary
future_directions_summary
paid_readiness_status
recommended_next_action_category
verification
```

Allowed `primary_decision_label` values:

```text
task_supply_v2_ready_for_benchmark_assembly
continue_internal_repo_history_v2
broaden_third_repo_screening
external_source_adapter_feasibility_needed
hybrid_supply_promising_but_not_paid_ready
task_supply_v2_blocked
insufficient_local_evidence
```

Recommended next action categories:

```text
assemble_local_benchmark_candidate_without_paid_validation
continue_internal_generator_v2_on_selected_repos
run_external_adapter_spike
screen_more_repos_before_paid_validation
repair_environment_or_oracle_pipeline
repair_statement_generation_pipeline
```

Acceptance:

- Decision report answers all research questions.
- Reports use simple language.
- Future directions are explicitly documented.
- Raw logs, target clones, caches, and workspaces are not committed.

## Verification

Run focused tests:

```bash
uv run --project experiments/phase1_compiler pytest \
  experiments/phase1_compiler/tests/test_phase1_task_supply_v2_generator_bakeoff.py \
  -q
```

If historical environment code changed:

```bash
uv run --project experiments/phase1_compiler pytest \
  experiments/phase1_compiler/tests/test_phase1_historical_environment_synthesis_gate.py \
  experiments/phase1_compiler/tests/test_phase1_reference_pass_failure_audit.py \
  -q
```

If repo-history tooling changed:

```bash
uv run --project experiments/phase0_headroom pytest \
  experiments/phase0_headroom/tools/test_repo_history_pilot.py \
  -q
```

If shared Phase 1 compiler behavior changed broadly:

```bash
uv run --project experiments/phase1_compiler pytest \
  experiments/phase1_compiler/tests \
  -q
```

Always run:

```bash
git diff --check
```

Record every command and result in the final decision report.
