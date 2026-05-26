# Phase 1 Local Algorithm Bakeoff Runbook

Status: implementation runbook, 2026-05-26.

This runbook is for one long-running Codex CLI session. Its job is to complete
the local algorithm work recommended after the weighted paid pilot failure. It
must not run paid ACUT cells or paid LLM calls. It should produce a clear
decision about whether any new benchmark compiler algorithm is locally strong
enough to justify a future paid replication.

Do not draft or create a follow-up runbook. Record completed work, blockers,
decisions, and recommended next action categories in closeout reports only.

## Starting Point

The weighted paid pilot completed cleanly as an experiment but failed as a
compiler design:

```text
paid pilot cells: 44 planned / 44 completed / 44 scoreable
policy violations: 0
observed-or-conservative cost: USD 22.0
final decision: weighted_pilot_complete_threshold_not_met

barcarolle_weighted_time_family_matched:
  attrs gap:   0.3148
  boltons gap: 0.7481
  max gap:     0.7481

repo_unweighted_same_budget:
  attrs gap:   0.25
  boltons gap: 0.125
  max gap:     0.25

repo_stratified_by_target_profile:
  attrs gap:   0.25
  boltons gap: 0.125
  max gap:     0.25
```

The external review recommendation is:

```text
Stop paid iteration on the current naive weighted target-profile method.
Promote simple stratified/unweighted methods as conservative baselines.
Develop and locally test block-randomized stratified and shrinkage-weighted
compiler variants before any more paid replication.
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-local-algorithm-bakeoff-runbook.md.

Work in the repository root. Read AGENTS.md first. Use uv for repo-local Python
tooling. Make a cohesive git commit after every completed step that changes
files. Do not batch unrelated steps into one commit. If a step only records
state, commit the small sanitized report/result update for that step. Do not
push unless the user explicitly asks.

Main goal: complete a local-only algorithm bakeoff after the weighted paid pilot
failure. Reproduce the pilot metrics, diagnose underidentification in the old
metadata objective, implement block-randomized stratified and capped
shrinkage-weighted compiler variants, run rolling-origin or pseudo-future local
validation, compare against baselines, and decide whether any algorithm is
ready for future paid replication.

Do not run paid ACUT cells. Do not run paid LLM calls. If a branch would require
paid task solving or paid LLM judgment, stop that branch and record a blocker.
No local Codex/ChatGPT subscription auth, provider fallback, or endpoint-paid
call should be used in this runbook.

Prefer mature modern software stacks over hand-rolled infrastructure. Inspect
available dependencies first. If adding a dependency would materially improve
correctness or maintainability, choose a well-maintained package, update the
appropriate pyproject/uv.lock, and record the reason. Keep the artifact format
auditable: deterministic CLI, JSON/CSV/Markdown outputs, digests, and tests.

Do not use hidden verifier material, raw ACUT transcripts, raw prompts, raw
completions, solver workspaces, or verifier workspaces for algorithm selection.
Use sanitized score tables, candidate metadata, release manifests, and reports.
Do not commit secrets, raw transcripts, workspaces, cloned external repos,
.venv, caches, or large raw outputs.

Do not draft or create the next runbook. Record recommended next action
categories only.
```

## Required Inputs

Use these committed or locally available artifacts:

```text
AGENTS.md
docs/architecture/system-design.md
experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_decision.json
experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_metrics.json
experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_baseline_comparison.json
experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_integrity_audit.json
experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_score_table.csv
experiments/phase1_compiler/results/phase1_pre_paid_replication_candidate_inventory.json
experiments/phase1_compiler/results/phase1_pre_paid_replication_target_profiles.json
experiments/phase1_compiler/results/phase1_pre_paid_replication_strata_matching.json
experiments/phase1_compiler/results/phase1_pre_paid_replication_release_candidates.json
experiments/phase1_compiler/results/phase1_pre_paid_replication_threshold_preregistration.json
experiments/phase1_compiler/results/phase1_overnight_statement_hardened_task_outcome_matrix.json
experiments/phase1_compiler/results/phase1_overnight_statement_hardened_failure_taxonomy.json
experiments/phase1_compiler/results/phase1_overnight_statement_hardened_strata_analysis.json
experiments/phase1_compiler/results/phase1_overnight_statement_hardened_next_action_decision.json
```

Optional context, if present:

```text
experiments/phase1_compiler/external_review/phase1_weighted_pilot_direction_review_20260526/README_FOR_EXTERNAL_GPT55_PRO.md
experiments/phase1_compiler/external_review/phase1_weighted_pilot_direction_review_20260526.zip
experiments/phase1_compiler/tools/phase1_pre_paid_replication_compiler_readiness.py
experiments/phase1_compiler/tools/phase1_weighted_design_paid_pilot.py
```

Do not include local absolute paths in committed artifacts. If an optional file
is missing, record it as missing and continue with the required committed
artifacts.

## Research Questions

Answer these directly:

```text
RQ1: Can the current weighted pilot metrics be reproduced exactly from committed
    score tables and release candidates?
RQ2: Is the old metadata objective underidentified, meaning many equivalent or
    near-equivalent metadata splits have very different observed outcome gaps?
RQ3: Does a coarser block-randomized stratified compiler reduce catastrophic
    B_eval/H_future gaps compared with unweighted, simple stratified, and the
    old weighted method in local validation?
RQ4: Do capped shrinkage weights improve prediction after blocking, or do they
    fail ESS/max-weight/uncertainty gates and fall back to uniform weights?
RQ5: Is there enough local supply and retrospective evidence to justify another
    paid replication? If not, what mainline candidate should be retained?
```

## Claim Boundary

Allowed claims:

```text
local_algorithm_bakeoff_completed
weighted_pilot_metrics_reproduced
metadata_objective_underidentification_measured
block_randomized_stratified_candidate_evaluated
shrinkage_weighted_candidate_evaluated
rolling_origin_or_pseudo_future_validation_completed
baseline_comparison_completed
paid_readiness_gate_passed
paid_readiness_gate_not_met
stratified_mainline_recommended
local_algorithm_work_blocked_with_precise_reason
```

Disallowed claims:

```text
predictive_validity_established
paid_replication_completed
new_paid_acut_cells_run
new_paid_llm_calls_made
H_future_used_as_target_profile
hidden_oracle_informed_selection
raw_transcript_informed_algorithm
post_hoc_algorithm_claimed_as_preregistered_paid_design
followup_runbook_written_by_worker
```

## Modern Stack Preference

Prefer mature packages when they materially improve correctness or clarity:

```text
pydantic: schemas and artifact validation
duckdb: local JSON/CSV analysis over candidate inventories and score tables
scipy: optimization, entropy balancing, MILP if available
statsmodels: intervals and basic statistical diagnostics
scikit-learn: simple classifiers, clustering, calibration diagnostics
ortools or cvxpy: optional only if split constraints need them and install cost
  is justified
```

Do not add heavy dependencies just because they are fashionable. If the existing
environment cannot support a package cleanly, implement the smallest auditable
fallback and record the tradeoff. Any dependency addition must be a separate
commit with a short reason in the process report.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_local_algorithm_bakeoff.yaml
    phase1_local_algorithm_bakeoff_candidates.yaml
  tools/
    phase1_local_algorithm_bakeoff.py
  tests/
    test_phase1_local_algorithm_bakeoff.py
  results/
    phase1_local_algorithm_bakeoff_preflight.json
    phase1_local_algorithm_bakeoff_reproduction.json
    phase1_local_algorithm_bakeoff_task_audit.json
    phase1_local_algorithm_bakeoff_underidentification.json
    phase1_local_algorithm_bakeoff_feature_schema.json
    phase1_local_algorithm_bakeoff_target_profile_prototype.json
    phase1_local_algorithm_bakeoff_candidate_designs.json
    phase1_local_algorithm_bakeoff_shrinkage_weights.json
    phase1_local_algorithm_bakeoff_validation_results.json
    phase1_local_algorithm_bakeoff_ablation.json
    phase1_local_algorithm_bakeoff_paid_readiness_gate.json
    phase1_local_algorithm_bakeoff_decision.json
  reports/
    phase1_local_algorithm_bakeoff_process.md
    phase1_local_algorithm_bakeoff_reproduction.md
    phase1_local_algorithm_bakeoff_task_audit.md
    phase1_local_algorithm_bakeoff_underidentification.md
    phase1_local_algorithm_bakeoff_feature_schema.md
    phase1_local_algorithm_bakeoff_target_profile_prototype.md
    phase1_local_algorithm_bakeoff_candidate_designs.md
    phase1_local_algorithm_bakeoff_shrinkage_weights.md
    phase1_local_algorithm_bakeoff_validation_results.md
    phase1_local_algorithm_bakeoff_ablation.md
    phase1_local_algorithm_bakeoff_paid_readiness_gate.md
    phase1_local_algorithm_bakeoff_decision.md
```

Optional small tables may be added under:

```text
experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_*.csv
```

Do not create:

```text
docs/experiments/*paid*.md
docs/experiments/*next*.md
docs/experiments/*follow-up*.md
raw ACUT/LLM transcript artifacts
solver or verifier workspaces
new paid score tables
```

## Commit Discipline

Every step below has a commit target. After a step produces or modifies files:

```text
git status --short
git diff --check
run the scoped tests for that step
git add only intended small sanitized files
git commit -m "<commit target>"
```

If a step only reads files and confirms no changes are needed, record that fact
in the process report and do not create an empty commit.

## Step 0: Preflight, Dependency Audit, And Work Queue

Commit target:

```text
Record local algorithm bakeoff preflight
```

Actions:

1. Read `AGENTS.md`, this runbook, system design, weighted pilot decision,
   metrics, baseline comparison, and pre-paid release candidates.
2. Record branch, HEAD, date, Python version, `uv --version`, and
   `git status --short --branch`.
3. Record SHA256 digests for all Required Inputs that exist.
4. Inspect `experiments/phase1_compiler/pyproject.toml` and current importable
   packages. Decide whether to add dependencies or stay with standard library.
5. If adding dependencies, prefer a minimal set and commit the dependency update
   separately before algorithm work. Record why each dependency is needed.
6. Initialize the process report and work queue.
7. Verify:

```text
new_paid_acut_calls_made == false for this runbook
new_paid_llm_calls_made == false for this runbook
weighted pilot completed == true
weighted pilot threshold met == false
historical reference was not rerun
```

Acceptance:

- Preflight JSON and process report exist.
- Work queue covers every step in this runbook.
- Dependency decision is recorded.
- No paid calls were made.

Verification:

```text
uv run --project experiments/phase1_compiler pytest -q
git diff --check
```

## Step 1: Reproduce Paid Pilot Metrics And Build Task Audit

Commit target:

```text
Reproduce weighted pilot metrics for bakeoff
```

Actions:

1. Implement or extend deterministic tooling to load:

```text
phase1_weighted_design_paid_pilot_score_table.csv
phase1_pre_paid_replication_release_candidates.json
phase1_pre_paid_replication_candidate_inventory.json
```

2. Recompute exactly:

```text
weighted design per-repo gaps
unweighted baseline per-repo gaps
stratified baseline per-repo gaps
task-level adapter-averaged outcomes
adapter disagreement rate
terminal status counts
scoreable cell counts
```

3. Build a per-task audit table with:

```text
task_id
repo_id
task_time_bucket
module_or_package
task_family_label
source_kind
statement_source
statement_quality_status
implementation/test file count buckets
candidate membership flags
adapter outcomes
task-level outcome
```

4. The audit must not include raw statements, raw prompts, raw completions, raw
   transcripts, hidden verifier material, or local absolute paths.

Acceptance:

- Reproduced metrics match the committed pilot metrics exactly or mismatches
  are explained.
- Task audit has one row per paid pilot task and is machine-readable.
- Tests cover at least one weighted and one unweighted recomputation.

Verification:

```text
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_local_algorithm_bakeoff.py reproduce
uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_local_algorithm_bakeoff.py
git diff --check
```

## Step 2: Quantify Metadata Objective Underidentification

Commit target:

```text
Measure weighted objective underidentification
```

Actions:

1. Reimplement the old weighted split objective from the pre-paid readiness
   tool as a local analysis function.
2. For each repo, enumerate all feasible `4 B_eval + 4 H_future` splits from
   the eligible unpaid candidate pool when enumeration is tractable. If not
   tractable for future larger pools, implement seeded sampling with a recorded
   sample size.
3. For each feasible split, compute:

```text
old metadata objective score
B_eval distance to target profile
H_future distance to target profile
B/H metadata gap
observed outcome gap when outcomes are available
max per-repo gap
```

4. Analyze:

```text
correlation between metadata objective and observed gap
gap distribution among top 1%, 5%, and 10% objective splits
best metadata split gap
best observed split gap, as oracle diagnostic only
worst near-optimal split gap
current selected weighted split percentile
```

5. Include oracle diagnostics only as upper/lower-bound analysis. Do not treat
   them as deployable algorithms.

Acceptance:

- The report answers whether metadata matching was underidentified.
- Near-optimal metadata splits have outcome-gap variance quantified.
- The report states whether deterministic tie-breaks are unsafe.

Verification:

```text
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_local_algorithm_bakeoff.py underidentification
uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_local_algorithm_bakeoff.py
git diff --check
```

## Step 3: Define Coarse Features And Target Profile Prototype

Commit target:

```text
Define local bakeoff features and target profile prototype
```

Actions:

1. Define a low-dimensional task feature schema. Start with:

```text
repo_id
work_cluster
difficulty_band
source_quality
locality
time_recency
source_kind_group
statement_quality_group
```

2. Map existing metadata into coarse features:

```text
work_cluster: merged module/task-family cluster
difficulty_band: unknown by default, or prior-only model prediction
source_quality: clean / minor_risk / risky
locality: single_file / multi_file
time_recency: older / recent / unknown, computed within repo
source_kind_group: issue / pull_request / other
```

3. Merge sparse strata:

```text
min_support_per_stratum: 3 by default
rare/unknown bucket required
do not keep high-cardinality raw task_family_label as a primary matching stratum
```

4. Build a target profile prototype. Prefer independent pre-cutoff public event
   metadata if it exists in committed artifacts. If it does not exist, build a
   clearly labeled surrogate profile from sanitized pre-outcome metadata and
   record:

```text
target_profile_independence_status: independent | surrogate_candidate_metadata | blocked_no_event_stream
```

5. H_future outcomes must not enter target profile computation.
6. Report:

```text
covered target mass
uncovered target mass
stratum support counts
confidence labels
profile uncertainty or support warnings
```

Acceptance:

- Feature schema is explicit and tested.
- Sparse raw strata are coarsened or marked rare/unknown.
- Target profile status honestly distinguishes independent profile from
  candidate-metadata surrogate.
- H_future outcomes used for profile computation is false.

Verification:

```text
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_local_algorithm_bakeoff.py features
uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_local_algorithm_bakeoff.py
git diff --check
```

## Step 4: Implement Candidate Compiler Designs

Commit target:

```text
Build local bakeoff compiler candidates
```

Actions:

Implement these deterministic local candidate designs:

```text
repo_unweighted_same_budget
repo_stratified_by_target_profile
seeded_random_same_budget
temporal_recent_baseline
coverage_constrained_unweighted
block_randomized_stratified
old_weighted_target_profile
block_plus_shrinkage_weighted
optional_block_plus_prior_difficulty
```

Rules:

1. `block_randomized_stratified` must:

```text
build matched blocks using coarse features
split within blocks using preregistered seeds
run multiple seeds for bakeoff diagnostics
report split imbalance and seed variance
```

2. `coverage_constrained_unweighted` must maximize coarse stratum coverage
   without using paid outcomes.
3. `temporal_recent_baseline` must use only time/order metadata.
4. `optional_block_plus_prior_difficulty` may be implemented only if the
   difficulty prior is trained on previous evidence and evaluated with leakage-
   safe rolling or nested validation. Otherwise mark it skipped.
5. Every design must state:

```text
selection_inputs
outcome_fields_used_for_selection
hidden_oracle_material_used
random_seed_policy
fallback_rule
```

Acceptance:

- Candidate design JSON contains task sets, split assignments, weights or
  weight mode, feature diagnostics, and seed information.
- Old weighted design is included only as a baseline/reference.
- Tests verify no candidate uses outcome fields for selection except explicitly
  labeled oracle diagnostics.

Verification:

```text
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_local_algorithm_bakeoff.py candidate-designs
uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_local_algorithm_bakeoff.py
git diff --check
```

## Step 5: Implement Capped Shrinkage Weights

Commit target:

```text
Evaluate capped shrinkage weights
```

Actions:

1. Implement capped shrinkage weighting for selected tasks:

```text
target: match coarse target profile moments where feasible
default closeness-to-uniform objective
max_weight <= 2 / n_selected
ESS >= 0.7 * n_selected
sum(weights) == 1
```

2. Prefer a mature optimization library if available and justified. If not,
   implement an auditable fallback:

```text
coarsen strata
attempt simple raking or constrained least squares
shrink toward uniform
fallback to uniform when infeasible
```

3. For each weighted candidate, record:

```text
weight_status: optimized | shrunk | uniform_fallback | infeasible
ESS
ESS ratio
max_weight
max_weight_allowed
target imbalance before/after weighting
reason for fallback, if any
```

4. Do not allow weights to override sparse support warnings. If supply is too
   small, the correct result is fallback plus a warning.

Acceptance:

- Weights are normalized and satisfy caps, or fallback is explicit.
- Any optimization dependency is documented and tested.
- The report says whether weighting adds useful signal or mostly increases
  variance.

Verification:

```text
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_local_algorithm_bakeoff.py shrinkage-weights
uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_local_algorithm_bakeoff.py
git diff --check
```

## Step 6: Rolling-Origin Or Pseudo-Future Local Validation

Commit target:

```text
Run local bakeoff validation
```

Actions:

1. Build local validation windows from available sanitized outcome evidence.
   Prefer true rolling-origin windows:

```text
profile/selection evidence before cutoff t
validate on later observed tasks after cutoff t
```

2. If true rolling-origin support is too small, run clearly labeled
   pseudo-future validation:

```text
time-ordered holdout
leave-window-out
seeded block split resampling
```

3. For every candidate design and seed/window, compute:

```text
MAE
RMSE
max absolute gap
catastrophic miss rate, where candidate gap > baseline gap + 0.15
threshold pass rate under 0.15
coverage interval or bootstrap interval when possible
effective sample size
covered/uncovered target mass
```

4. Compare against:

```text
repo_unweighted_same_budget
repo_stratified_by_target_profile
block_randomized_stratified
old_weighted_target_profile
block_plus_shrinkage_weighted
```

5. Use bootstrap over tasks or blocks where support allows. If support is too
   small, mark uncertainty as insufficient instead of overclaiming.

Acceptance:

- Validation result distinguishes true rolling-origin from pseudo-future.
- Results include per-repo/window/seed metrics and aggregate summaries.
- Catastrophic miss rate is reported.
- No design is promoted based on one favorable seed or one repo only.

Verification:

```text
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_local_algorithm_bakeoff.py validate
uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_local_algorithm_bakeoff.py
git diff --check
```

## Step 7: Ablation Study And Mainline Recommendation

Commit target:

```text
Compare local bakeoff ablations
```

Actions:

1. Run or summarize ablations:

```text
unweighted only
simple stratified
seeded random
coverage constrained
blocked only
blocked + shrinkage weights
blocked + prior difficulty, if safely available
old weighted method
```

2. Answer:

```text
Does blocking alone help?
Do shrinkage weights help after blocking?
Does weighting fail ESS or max-weight gates?
Does any algorithm beat stratified by at least 15-25% MAE locally?
Is improvement stable across repos/windows/seeds?
Does any algorithm avoid catastrophic misses?
```

3. Choose one mainline recommendation:

```text
keep_repo_stratified_as_mainline
promote_block_randomized_stratified
promote_block_plus_shrinkage_research_candidate
continue_local_algorithm_work
stop_predictive_compiler_claim_for_now
```

Acceptance:

- Ablation report is clear enough for a coordinating session to decide next
  direction.
- The mainline recommendation is conservative and evidence-bounded.
- Weighted methods are not promoted unless they pass local gates.

Verification:

```text
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_local_algorithm_bakeoff.py ablation
uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_local_algorithm_bakeoff.py
git diff --check
```

## Step 8: Paid-Readiness Gate

Commit target:

```text
Evaluate local bakeoff paid readiness
```

Actions:

Evaluate whether another paid replication is justified. Use these gates:

```text
local MAE improvement:
  candidate improves over simple stratified baseline by at least 15-25% and
  improvement is not driven by a single repo/window.

catastrophic miss:
  candidate does not frequently produce gaps worse than baseline + 0.15.

weight diagnostics:
  ESS >= 0.7 * n when weights are used.
  max_weight <= 2 / n when weights are used.
  fallback to uniform is automatic when infeasible.

supply diagnostics:
  each target repo has at least 20-30 eligible certified tasks for a precision
  run, or the decision is explicitly pilot-only.
  each coarse stratum has support >= 3 or is merged into rare/unknown.

split stability:
  multi-seed prediction variance is low enough for a paid pilot.
  result does not depend on lexicographic tie-break.

preregistration readiness:
  features, target profile, weights, split seed, fallback rules, and primary
  metrics can be frozen before paid calls.
```

Output one of:

```text
ready_to_preregister_paid_pilot
ready_to_preregister_precision_target_after_supply_expansion
not_ready_continue_local_algorithm_work
not_ready_keep_stratified_mainline
stop_and_report_bounded_negative_algorithm_evidence
```

Acceptance:

- Paid-readiness JSON is machine-readable and conservative.
- If ready, it specifies exact candidate algorithm and preregistration fields.
- If not ready, it states the smallest local blocker.
- No paid runbook is written by the worker.

Verification:

```text
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_local_algorithm_bakeoff.py paid-readiness
uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_local_algorithm_bakeoff.py
git diff --check
```

## Step 9: Final Decision And Closeout

Commit target:

```text
Record local algorithm bakeoff decision
```

Actions:

1. Write final decision JSON and Markdown.
2. Answer all Research Questions.
3. Record:

```text
new_paid_acut_calls_made
new_paid_llm_calls_made
raw_artifacts_committed
followup_runbook_written_by_worker
weighted_pilot_metrics_reproduced
underidentification_status
best_local_candidate
mainline_recommendation
paid_readiness_status
smallest_blocker
modern_stack_changes
```

4. Update the process report with step status, commit hashes, verification
   commands, blockers, and closeout.
5. Run final checks.

Acceptance:

- Final decision does not claim predictive validity.
- Final decision does not include or create a follow-up runbook.
- If no algorithm is paid-ready, the report says so directly.
- If stratified remains mainline, the report explains why in simple terms.

Verification:

```text
uv run --project experiments/phase1_compiler pytest -q
git diff --check
git status --short
```

## Final Response Requirements For The Worker

The worker's final response to the coordinating session should be short and
plain. It should include:

```text
1. whether the local bakeoff completed
2. whether current weighted metrics reproduced
3. whether metadata-objective underidentification was confirmed
4. best local candidate and mainline recommendation
5. whether any algorithm is ready for paid replication
6. smallest blocker or next action category
7. confirmation that no paid calls and no follow-up runbook were created
8. commit range created by the worker
```

Do not paste long reports into the final response. Point to committed reports
and decision files instead.
