# Phase 1 Pre-Paid Replication Compiler Readiness Runbook

Status: implementation runbook, 2026-05-26.

This runbook is for one long-running Codex CLI session. Its job is to complete
the local compiler work required before the next paid replication. It must stop
at a paid replication entry package. It must not launch paid ACUT validation
cells.

The purpose is to move from "the tasks are cleanly scoreable" to "there is a
preregistered, target-profile-aware, weighted benchmark release design ready for
paid replication."

Do not draft or create a follow-up runbook. Record completed work, blockers,
decisions, and recommended next actions in closeout reports only.

## Starting Point

Latest completed paid evidence:

```text
release_id: statement_hardened_after_canonical_split_repair_20260525
planned cells: 32
completed cells: 32
scoreable cells: 32
terminal statuses:
  verified_pass: 21
  verified_fail: 11
policy violations: 0
timeouts: 0
harness errors: 0
invalid outputs: 0
adapter disagreement tasks: 1 of 16
predictive_validity_established: false
```

Latest analysis decision:

```text
primary_decision: design_new_predictive_threshold_before_more_paid_validation
recommended_next_action:
  Do not run more paid validation until a quantitative predictive-validity
  threshold and a better matched local design are preregistered.
```

Observed paid pass rates from the prior release:

```text
attrs/B_eval:    6/8 = 0.75
attrs/H_future:  4/8 = 0.50
boltons/B_eval:  7/8 = 0.875
boltons/H_future: 4/8 = 0.50
```

Observed B_eval to H_future gaps:

```text
attrs:   0.25
boltons: 0.375
pooled:  0.3125
```

These outcomes are previous evidence. They may be used to motivate the next
compiler design, but the next paid replication must be preregistered before it
is run and must not be presented as if the design were chosen without seeing
the previous result.

## Required Inputs

Use these committed inputs:

```text
AGENTS.md
docs/architecture/system-design.md
docs/experiments/phase-1-overnight-statement-hardened-evidence-analysis-runbook.md
experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_evidence_process.md
experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_next_action_decision.md
experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_threshold_analysis.md
experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_power_analysis.md
experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_calibration_options.md
experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_local_supply_analysis.md
experiments/phase1_compiler/results/phase1_overnight_statement_hardened_next_action_decision.json
experiments/phase1_compiler/results/phase1_overnight_statement_hardened_threshold_analysis.json
experiments/phase1_compiler/results/phase1_overnight_statement_hardened_power_analysis.json
experiments/phase1_compiler/results/phase1_overnight_statement_hardened_calibration_options.json
experiments/phase1_compiler/results/phase1_overnight_statement_hardened_local_supply_analysis.json
experiments/phase1_compiler/results/phase1_overnight_statement_hardened_task_outcome_matrix.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_release_manifest.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_inventory.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_preregistration.json
experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/humanize_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/itsdangerous_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/toolz_certified_tasks.jsonl
```

Optional context:

```text
barcarolle-research-0519.md
experiments/phase1_compiler/reports/phase1_statement_hardened_after_canonical_repair_paid_process.md
experiments/phase1_compiler/reports/phase1_statement_hardened_after_canonical_repair_preregistration.md
experiments/phase1_compiler/reports/phase1_statement_hardened_after_canonical_repair_release_manifest.md
```

If the original proposal file is not present in the repository, do not copy a
local absolute path into committed artifacts. Record only `proposal_available:
false` or use a repo-relative committed design document.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-pre-paid-replication-compiler-readiness-runbook.md.

Work in the repository root. Read AGENTS.md first. Use uv for repo-local Python
tooling. Make a cohesive git commit after every completed step that changes
files. Do not batch unrelated steps into one commit. If a step has no file
changes, record that fact in the process report and do not create an empty
commit. Do not push unless the user explicitly asks.

Main goal: complete all local compiler-readiness work before the next paid
replication. This includes a preregistered predictive-validity threshold, target
profiles, enriched candidate inventory, time/task-family/source matching,
weighted release candidates, baseline comparison design, statement/source
quality gates, sample-size and cost planning, and a final paid replication entry
package.

Stop before paid ACUT validation. Do not launch paid replication cells. Do not
run solver ACUTs against the release. If paid replication is ready, write the
exact entry package and mark the gate `ready_for_paid_replication`; if not,
write `blocked_before_paid_replication` with precise blockers.

No paid calls are expected for this runbook. If a task statement must be
regenerated or reviewed by an LLM to reach replication readiness, obey AGENTS.md:
paid LLM calls must use LLM_BASE_URL and LLM_API_KEY. Source ~/.zshrc and check
again if either variable is missing. Do not use local Codex/ChatGPT subscription
auth, OPENAI_API_KEY, OpenRouter variables, or provider-specific variables. If
you cannot prove the call uses LLM_BASE_URL plus LLM_API_KEY, stop that branch
and record a blocker. Do not run paid ACUT task-solving calls under any
circumstance in this runbook.

Be autonomous and keep moving. If one analysis branch is blocked, continue
independent local branches. Add deterministic tools, tests, schemas, reports,
and manifests where useful. Keep artifacts small and sanitized.

Do not use hidden verifier material to select, rewrite, or weight tasks. Do not
commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw Codex or
Kilo logs, solver workspaces, verifier workspaces, cloned external repositories,
.venv, caches, raw target diffs, or large raw outputs. Commit only small
sanitized configs, tools, tests, tables, metrics, reports, summaries, and
decision files.

Do not draft or create the next runbook. Record recommended next actions and
suggested follow-up categories only.
```

## Research Questions

Answer these directly:

```text
RQ1: What quantitative predictive-validity threshold will the next replication
    use, and what minimum sample/precision gates must it satisfy?
RQ2: What target profile is being estimated for each repo without treating
    H_future itself as the target profile?
RQ3: Which task strata explain the prior B_eval/H_future mismatch, and how
    will the next release match or weight them before paid replication?
RQ4: Which local candidate reservoirs are ready, which need statement/source
    hardening, and which are excluded from the paid replication candidate pool?
RQ5: What benchmark release candidates and baselines are frozen for the next
    paid replication?
RQ6: Is the final state ready for paid replication? If not, what exact blocker
    remains?
```

## Claim Boundary

Allowed claims:

```text
pre_paid_replication_readiness_completed
predictive_validity_threshold_preregistered
target_profile_estimated_from_pre_holdout_metadata
candidate_inventory_enriched
time_task_family_source_matching_completed
weighted_release_candidate_frozen
baseline_release_candidates_frozen
statement_quality_gate_completed
paid_replication_entry_package_ready
blocked_before_paid_replication
no_paid_acut_replication_run
```

Disallowed claims:

```text
predictive_validity_established
paid_replication_completed
production_benchmark_ranking
H_future_used_as_target_profile
hidden_oracle_informed_selection
post_hoc_release_claimed_as_preregistered
local_codex_subscription_used_for_paid_llm_calls
followup_runbook_written_by_worker
```

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_pre_paid_replication_compiler_readiness.yaml
    phase1_pre_paid_replication_thresholds.yaml
    phase1_pre_paid_replication_release_selection.yaml
  tools/
    phase1_pre_paid_replication_compiler_readiness.py
  tests/
    test_phase1_pre_paid_replication_compiler_readiness.py
  results/
    phase1_pre_paid_replication_preflight.json
    phase1_pre_paid_replication_threshold_preregistration.json
    phase1_pre_paid_replication_candidate_inventory.json
    phase1_pre_paid_replication_target_profiles.json
    phase1_pre_paid_replication_strata_matching.json
    phase1_pre_paid_replication_statement_quality_gate.json
    phase1_pre_paid_replication_release_candidates.json
    phase1_pre_paid_replication_baseline_plan.json
    phase1_pre_paid_replication_power_and_cost_plan.json
    phase1_pre_paid_replication_entry_gate.json
    phase1_pre_paid_replication_decision.json
  reports/
    phase1_pre_paid_replication_process.md
    phase1_pre_paid_replication_threshold_preregistration.md
    phase1_pre_paid_replication_candidate_inventory.md
    phase1_pre_paid_replication_target_profiles.md
    phase1_pre_paid_replication_strata_matching.md
    phase1_pre_paid_replication_statement_quality_gate.md
    phase1_pre_paid_replication_release_candidates.md
    phase1_pre_paid_replication_baseline_plan.md
    phase1_pre_paid_replication_power_and_cost_plan.md
    phase1_pre_paid_replication_entry_gate.md
    phase1_pre_paid_replication_decision.md
```

Do not create:

```text
docs/experiments/*follow-up*.md
docs/experiments/*next*.md
experiments/phase0_headroom/results/*paid_replication*_score_table.csv
experiments/phase0_headroom/results/*paid_replication*_metrics.json
raw ACUT/LLM transcript artifacts
solver or verifier workspaces
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

## Step 0: Preflight And Boundary Check

Commit target:

```text
Record pre-paid replication readiness preflight
```

Actions:

1. Read `AGENTS.md`, this runbook, system design, and the overnight analysis
   decision.
2. Record branch, HEAD, date, `uv --version`, Python version, and
   `git status --short --branch`.
3. Record SHA256 digests for all required inputs that exist.
4. Verify and record:

```text
previous paid scoreable cells == 32
previous policy violations == 0
previous predictive_validity_established == false
followup_runbook_written_by_worker == false
new paid ACUT replication allowed in this runbook == false
```

5. Initialize `phase1_pre_paid_replication_process.md` with a work queue for all
   steps in this runbook.
6. Create the main config file with run id, input paths, output paths, and
   no-paid-ACUT boundary.

Acceptance:

- Preflight JSON exists and contains input digests, environment, branch, HEAD,
  and no-paid boundary.
- Process report exists and shows every step as pending except Step 0.
- No paid ACUT or paid LLM calls have been made.

Verification:

```text
uv run python -m pytest experiments/phase1_compiler/tests -q
git diff --check
```

## Step 1: Freeze Predictive-Validity Thresholds

Commit target:

```text
Preregister pre-paid replication predictive thresholds
```

Actions:

1. Write a preregistered threshold file before designing the new release.
2. Use the overnight recommendation as the default primary rule:

```text
primary rule:
  For each preregistered repo or repo-family stratum,
  abs(B_eval_predicted_pass_rate - H_future_observed_pass_rate) <= 0.15.

minimum scoreability rule:
  100% planned cells must complete or every missing cell must have a
  preregistered non-scoreable handling rule.

policy rule:
  policy violations, hidden-oracle access, prohibited test edits, harness errors,
  and invalid outputs must be zero for primary validity claims.

precision rule:
  report Wilson or beta-binomial intervals for each stratum and mark strata
  insufficient when the half-width target is not met.
```

3. Add secondary diagnostic metrics:

```text
MAE between B_eval-predicted and H_future observed pass rates
RMSE between B_eval-predicted and H_future observed pass rates
binomial negative log likelihood if enough strata exist
Brier score if enough strata exist
calibration interval coverage
adapter disagreement rate
```

4. Explicitly decide how previous paid evidence may and may not be used:

```text
allowed:
  motivate thresholds, sample-size planning, and local compiler redesign
not allowed:
  claim the next design was chosen without seeing previous outcomes
  count previous H_future outcomes as validation for a post-hoc redesigned release
```

5. Write both JSON and Markdown threshold preregistration artifacts.

Acceptance:

- Thresholds are frozen before new release selection artifacts are written.
- The file clearly distinguishes primary gates from diagnostics.
- The file states that H_future is validation data, not the target profile.

Verification:

```text
uv run python -m pytest experiments/phase1_compiler/tests/test_phase1_pre_paid_replication_compiler_readiness.py -q
git diff --check
```

## Step 2: Build The Enriched Candidate Inventory

Commit target:

```text
Build pre-paid replication candidate inventory
```

Actions:

1. Load all local certified-task reservoirs listed in Required Inputs.
2. Normalize candidates into one inventory schema:

```yaml
task_id:
repo_id:
source_reservoir:
source_kind:
source_ref:
task_time:
canonical_split_current:
base_commit:
statement_digest:
statement_source:
statement_length:
statement_quality_status:
editable_paths:
test_paths:
implementation_file_count:
test_file_count:
module_or_package_list:
task_family_label:
source_context_length_bucket:
historical_paid_outcome_available:
historical_paid_outcome_summary:
eligible_for_next_release:
exclusion_reasons:
```

3. Enrich missing metadata deterministically when possible from committed
   manifests, inventories, certified tasks, and sanitized reports.
4. Do not inspect raw hidden verifier material.
5. Mark a candidate ineligible if required metadata is missing and cannot be
   recovered locally.
6. Keep previous paid terminal outcomes in a separate nested field. Do not let
   outcome fields drive target profile estimation.

Acceptance:

- Every local certified candidate appears exactly once or has a documented
  duplicate-resolution rule.
- Every candidate has repo, time, source, statement, module/family, file-count,
  and eligibility fields.
- Exclusions are explicit and machine-readable.

Verification:

```text
uv run python experiments/phase1_compiler/tools/phase1_pre_paid_replication_compiler_readiness.py inventory
uv run python -m pytest experiments/phase1_compiler/tests/test_phase1_pre_paid_replication_compiler_readiness.py -q
git diff --check
```

## Step 3: Estimate Target Profiles Without Using H_future As The Profile

Commit target:

```text
Estimate pre-paid replication target profiles
```

Actions:

1. Build target profiles for each repo included in the next release.
2. Use only pre-holdout metadata and source-visible task metadata:

```text
allowed profile inputs:
  task_time
  module/package
  source kind
  implementation/test file counts
  task family
  statement/source-context surface features
  historical repository task frequencies
  candidate-pool metadata

disallowed profile inputs:
  H_future terminal pass/fail outcomes as profile weights
  hidden verifier material
  reference patch internals beyond sanitized metadata
  raw solver transcripts
```

3. For each repo, estimate weights over at least:

```text
task_family_label
module_or_package
task_time_bucket
source_kind
implementation_file_count bucket
test_file_count bucket
statement_quality_status
```

4. Include confidence labels:

```text
high: enough candidate support and stable distribution
medium: enough support but shifted or sparse in one split
low: sparse, single-task, or source-confounded
insufficient: cannot support weighted scoring yet
```

5. Write a plain-language report explaining why target profile is not the same
   thing as H_future.

Acceptance:

- Target profiles are explicit weight tables, not just prose.
- H_future outcome fields are absent from the profile computation inputs.
- Sparse strata are marked `insufficient` instead of being silently assigned
  overconfident weights.

Verification:

```text
uv run python experiments/phase1_compiler/tools/phase1_pre_paid_replication_compiler_readiness.py target-profiles
uv run python -m pytest experiments/phase1_compiler/tests/test_phase1_pre_paid_replication_compiler_readiness.py -q
git diff --check
```

## Step 4: Diagnose And Repair Split Matching Locally

Commit target:

```text
Design pre-paid replication split matching
```

Actions:

1. Compare candidate B_eval and H_future pools by target-profile strata:

```text
time bucket
task family
module/package
source kind
statement source
statement quality
implementation/test file count
```

2. Measure mismatch using simple auditable metrics:

```text
absolute weight gap by stratum
L1 distance between B_eval and target profile
L1 distance between H_future and target profile
coverage count per stratum
single-task stratum flags
```

3. Produce at least three local selection designs:

```text
repo_unweighted_same_budget
repo_stratified_by_target_profile
barcarolle_weighted_time_family_matched
```

4. Prefer designs that reduce known confounds from the prior run:

```text
attrs:
  avoid letting attr._next_gen/on_setattr concentration dominate one split
boltons:
  avoid H_future being much later in time and different in task family without
  explicit weights or insufficient-evidence labels
both:
  avoid one split having mostly reused statements and the other mostly new
  generated statements unless this is explicitly modeled
```

5. Do not select tasks solely because previous paid outcomes were pass or fail.
   If previous outcomes influence a design choice indirectly, label the design
   `post_hoc_calibrated` and do not present it as clean validation until a new
   preregistered replication is run.

Acceptance:

- Mismatch tables exist for every proposed design.
- The recommended design has lower or equal mismatch than the prior release on
  primary strata, or the report explains why no local repair is possible.
- The report clearly separates pre-outcome metadata matching from post-hoc
  learning from previous paid outcomes.

Verification:

```text
uv run python experiments/phase1_compiler/tools/phase1_pre_paid_replication_compiler_readiness.py match-splits
uv run python -m pytest experiments/phase1_compiler/tests/test_phase1_pre_paid_replication_compiler_readiness.py -q
git diff --check
```

## Step 5: Audit Statement And Source Quality Gates

Commit target:

```text
Audit pre-paid replication statement quality gates
```

Actions:

1. Audit every candidate in the recommended release and all baselines for:

```text
statement exists
statement length within soft target range
no hard truncation
closed code fences and reproduction blocks
clear API intent
clear expected behavior
clear editable scope
no direct solution leakage
no hidden oracle leakage
source context not empty unless statement has enough independent detail
diff-derived detail does not reveal exact implementation patch
```

2. Classify each statement:

```text
pass
pass_with_minor_risk
needs_regeneration
exclude_before_paid_replication
```

3. If all selected statements pass or pass with minor risk, continue.
4. If a selected statement needs regeneration:
   - First try deterministic repair from allowed source-visible metadata.
   - If LLM regeneration/review is necessary, use only `LLM_BASE_URL` and
     `LLM_API_KEY` as required by `AGENTS.md`.
   - Run a generator/reviewer loop only for statement preparation, not for ACUT
     solving.
   - Record sanitized statement digests and review verdicts only.
   - Do not commit raw prompts, raw completions, or transcripts.
   - If the required endpoint cannot be proven, mark the candidate blocked or
     exclude it; do not use local Codex subscription auth.

5. Recompute release eligibility after statement quality decisions.

Acceptance:

- Every selected candidate has a statement quality verdict.
- No selected candidate has hard truncation, broken code fences, or known direct
  answer leakage.
- Any LLM statement-prep call, if made, has endpoint/cost/provenance recorded
  in sanitized form and complies with `AGENTS.md`.
- If no LLM calls are made, the report states `new_paid_llm_calls_made: false`.

Verification:

```text
uv run python experiments/phase1_compiler/tools/phase1_pre_paid_replication_compiler_readiness.py statement-quality
uv run python -m pytest experiments/phase1_compiler/tests/test_phase1_pre_paid_replication_compiler_readiness.py -q
git diff --check
```

## Step 6: Freeze Release Candidates And Baselines

Commit target:

```text
Freeze pre-paid replication release candidates
```

Actions:

1. Freeze a recommended Barcarolle release candidate:

```text
barcarolle_weighted_time_family_matched
```

2. Freeze baseline candidates for the next paid replication:

```text
repo_unweighted_same_budget
repo_stratified_by_target_profile
prior_statement_hardened_release_as_historical_reference
```

3. For each candidate, write:

```yaml
release_candidate_id:
design_kind:
repo_ids:
task_ids:
split_assignment:
weights:
target_profile_version:
selection_inputs:
selection_exclusions:
statement_quality_summary:
known_confounds:
insufficient_evidence_strata:
score_aggregation_rule:
uncertainty_rule:
primary_threshold_file:
```

4. If there is not enough local supply to freeze a valid release, freeze the
   best blocked design and write `blocked_before_paid_replication` with exact
   missing strata or candidates.

Acceptance:

- Release candidate JSON is deterministic and stable across reruns.
- Baselines are frozen with the same budget and comparable task eligibility
  rules where possible.
- The recommended release has a score aggregation rule that uses target-profile
  weights and reports uncertainty.

Verification:

```text
uv run python experiments/phase1_compiler/tools/phase1_pre_paid_replication_compiler_readiness.py freeze-releases
uv run python -m pytest experiments/phase1_compiler/tests/test_phase1_pre_paid_replication_compiler_readiness.py -q
git diff --check
```

## Step 7: Write The Baseline Comparison Plan

Commit target:

```text
Plan pre-paid replication baseline comparisons
```

Actions:

1. Define how paid replication will compare:

```text
primary:
  Barcarolle weighted predictor vs H_future observed pass rate

baselines:
  repo_unweighted_same_budget
  repo_stratified_by_target_profile
  prior_statement_hardened_release historical reference

diagnostics:
  per-repo gap
  per-task-family gap
  adapter disagreement
  source-kind gap
  statement-quality gap
```

2. Define exact scoring formulas in code or config:

```text
unweighted pass rate
target-profile weighted pass rate
Wilson or beta-binomial interval by stratum
MAE and RMSE across preregistered strata
insufficient-evidence labels
```

3. Decide how to handle multiple adapters:

```text
primary: average task-level outcome across preregistered adapters
secondary: per-adapter report
disagreement: diagnostic, not automatic exclusion unless preregistered
```

4. Decide how to handle missing or non-scoreable cells:

```text
scoreability failure policy
replacement policy before launch
no post-hoc replacement after terminal outcomes are known
```

Acceptance:

- Baseline plan can be executed without changing the selection after paid
  outcomes are seen.
- Metrics match the threshold preregistration from Step 1.
- The plan states exactly what would count as success, failure, and
  insufficient evidence.

Verification:

```text
uv run python experiments/phase1_compiler/tools/phase1_pre_paid_replication_compiler_readiness.py baseline-plan
uv run python -m pytest experiments/phase1_compiler/tests/test_phase1_pre_paid_replication_compiler_readiness.py -q
git diff --check
```

## Step 8: Update Power, Sample-Size, And Cost Planning

Commit target:

```text
Plan pre-paid replication power and cost
```

Actions:

1. Recompute sample-size needs for the frozen release design.
2. Use the prior cost observation as a conservative cost baseline:

```text
previous 32-cell observed-or-conservative cost: USD 9.9235152
```

3. Estimate cost for:

```text
minimum viable replication
recommended replication
precision-target replication
```

4. Include expected cells by:

```text
repo
split
adapter
release candidate
baseline
```

5. Mark whether the planned design reaches:

```text
primary scoreability gate
primary 0.15 gap threshold
precision half-width target
minimum task-level units per split
```

6. If local supply cannot support the recommended sample size, write the exact
   tradeoff:

```text
run smaller replication as pilot
mine/harden more tasks first
add third repo after source/provenance hardening
stop and report insufficient evidence
```

Acceptance:

- Cost and sample-size estimates are explicit and tied to prior observed cost.
- The report distinguishes "ready for pilot paid replication" from "ready for
  precision-target paid replication."
- No paid ACUT cells are run.

Verification:

```text
uv run python experiments/phase1_compiler/tools/phase1_pre_paid_replication_compiler_readiness.py power-cost
uv run python -m pytest experiments/phase1_compiler/tests/test_phase1_pre_paid_replication_compiler_readiness.py -q
git diff --check
```

## Step 9: Build The Paid Replication Entry Package Without Running It

Commit target:

```text
Build pre-paid replication entry package
```

Actions:

1. Create a paid replication entry gate JSON and report.
2. Include:

```yaml
entry_status: ready_for_paid_replication | blocked_before_paid_replication
release_candidate_id:
baseline_candidate_ids:
threshold_preregistration:
target_profile_version:
candidate_inventory_digest:
statement_quality_gate_status:
sample_size_plan:
cost_estimate:
required_env:
  LLM_BASE_URL: required
  LLM_API_KEY: required
paid_acut_calls_already_run_for_this_release: false
commands_to_run_later: documented_but_not_executed
stop_reason:
```

3. If ready, document the exact later paid-run command plan in sanitized form.
   Do not include secrets.
4. If blocked, write the smallest set of local tasks that would unblock paid
   replication. Do not write a new runbook.
5. Verify the entry package does not include local absolute paths or sensitive
   values.

Acceptance:

- Entry package is sufficient for a future coordinating session to decide
  whether to approve paid replication.
- It contains commands or config references, but no paid replication was run.
- It states whether paid replication is pilot-grade or precision-target-grade.

Verification:

```text
uv run python experiments/phase1_compiler/tools/phase1_pre_paid_replication_compiler_readiness.py entry-gate
uv run python -m pytest experiments/phase1_compiler/tests/test_phase1_pre_paid_replication_compiler_readiness.py -q
git diff --check
```

## Step 10: Final Decision And Closeout

Commit target:

```text
Record pre-paid replication readiness decision
```

Actions:

1. Write final decision JSON and Markdown.
2. Answer all Research Questions.
3. Record:

```text
new_paid_acut_calls_made
new_paid_llm_calls_made
followup_runbook_written_by_worker
raw_artifacts_committed
ready_for_paid_replication
blocked_before_paid_replication
primary_release_candidate_id
baseline_candidate_ids
primary_threshold
sample_size_status
cost_status
statement_quality_status
```

4. Update the process report with each step status, commit hashes, verification
   commands, and blockers.
5. Run final checks.

Acceptance:

- Final decision is one of:

```text
ready_for_pilot_paid_replication
ready_for_precision_target_paid_replication
blocked_before_paid_replication
stop_and_report_insufficient_local_supply
```

- The decision does not claim predictive validity.
- The decision does not include or create a next runbook.
- The process report contains a concise closeout for the coordinating session.

Verification:

```text
uv run python -m pytest experiments/phase1_compiler/tests -q
git diff --check
git status --short
```

## Final Response Requirements For The Worker

The worker's final response to the coordinating session should be short and
plain. It should include:

```text
1. whether the runbook completed
2. whether paid replication is ready, blocked, or only pilot-grade ready
3. the frozen release candidate and baselines
4. the most important blocker or risk, if any
5. confirmation that no paid ACUT replication was run
6. the commit range created by the worker
```

Do not paste long reports into the final response. Point to committed reports
and decision files instead.
