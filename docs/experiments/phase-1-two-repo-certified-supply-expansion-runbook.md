# Phase 1 Two-Repo Certified Supply Expansion Runbook

Status: implementation runbook, 2026-05-26.

This runbook is for one long-running Codex CLI session. Its job is to expand
the eligible certified task supply for the existing Phase 1 target repositories,
`attrs` and `boltons`, before any further paid replication.

The current blocker is not that we need more repositories immediately. The
blocker is that each current repository has too few eligible certified tasks to
make local split, weighting, and temporal validation evidence stable.

Do not draft or create a follow-up runbook. Record completed work, blockers,
decisions, and recommended next action categories in closeout reports only.

## Starting Point

The local algorithm bakeoff completed with this decision:

```text
final decision: not_ready_keep_stratified_mainline
mainline recommendation: keep_repo_stratified_as_mainline
smallest blocker: eligible certified task supply below 20-30 per target repo
```

Current local bakeoff paid-readiness supply counts:

```text
attrs:   10 eligible certified tasks
boltons: 12 eligible certified tasks
```

Minimum target for this runbook:

```text
attrs:   >= 30 eligible certified tasks
boltons: >= 30 eligible certified tasks
total:   >= 60 eligible certified tasks
```

Stretch target:

```text
attrs:   approximately 50 eligible certified tasks
boltons: approximately 50 eligible certified tasks
total:   approximately 100 eligible certified tasks
```

Expected mining scale:

```text
raw candidates per repo: 50-100 minimum, up to 160 if needed
new certified tasks per repo: 20-40 expected
paid ACUT cells: 0
paid task-solving calls: 0
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-two-repo-certified-supply-expansion-runbook.md.

Work in the repository root. Read AGENTS.md first. Use uv for repo-local Python
tooling. Make a cohesive git commit after every completed step that changes
files. Do not batch unrelated steps into one commit. If a step produces only a
small sanitized report or manifest, commit that report as the step commit. Do
not push unless the user explicitly asks.

Main goal: expand eligible certified task supply for attrs and boltons before
any further paid replication. Prefer mining more historical tasks from these two
repositories over adding new repositories. Reach at least 30 eligible certified
tasks per repo if local evidence allows; 50 per repo is the stretch target.

Do not run paid ACUT task-solving cells. Do not run paid replication. Do not
use hidden verifier material, raw ACUT transcripts, raw prompts, raw
completions, solver workspaces, or verifier workspaces for selection. Commit
only small sanitized configs, manifests, tools, tests, reports, summaries, and
digests.

All paid LLM calls, if a later statement-generation gate explicitly requires
them, must use LLM_BASE_URL and LLM_API_KEY as required by AGENTS.md. Do not use
local Codex/ChatGPT subscription auth or provider fallback unless AGENTS.md is
explicitly updated by the user. If you cannot prove the generation/review loop
uses the required endpoint variables, stop that branch and write a blocker
report instead of silently replacing it with deterministic rules.

Prefer mature modern software stacks over hand-rolled infrastructure when they
materially improve correctness or maintainability. Inspect existing
dependencies first. Keep the artifact format auditable: deterministic CLI,
JSON/CSV/Markdown outputs, digests, and tests.

Do not draft or create the next runbook. Record recommended next action
categories only.
```

## Required Inputs

Use these artifacts if present:

```text
AGENTS.md
docs/architecture/system-design.md
docs/experiments/phase-1-local-algorithm-bakeoff-runbook.md
experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_decision.json
experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_paid_readiness_gate.json
experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_task_audit.json
experiments/phase1_compiler/results/phase1_pre_paid_replication_candidate_inventory.json
experiments/phase1_compiler/results/phase1_pre_paid_replication_release_candidates.json
experiments/phase1_compiler/results/phase1_pre_paid_replication_target_profiles.json
experiments/phase1_compiler/results/phase1_weighted_design_paid_pilot_score_table.csv
experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py
experiments/phase1_compiler/tools/phase1_diff_assisted_codex_loop_statement_regeneration.py
experiments/phase1_compiler/tools/phase1_local_algorithm_bakeoff.py
experiments/phase1_compiler/tools/phase1_pre_paid_replication_compiler_readiness.py
experiments/phase0_headroom/tools/repo_history_pilot.py
experiments/phase0_headroom/tools/statement_quality.py
experiments/phase0_headroom/external_repos/attrs
experiments/phase0_headroom/external_repos/boltons
```

Also inventory existing `attrs` and `boltons` task/source artifacts under:

```text
experiments/phase0_headroom/candidate_sources/
experiments/phase0_headroom/certified_tasks/
experiments/phase0_headroom/releases/
experiments/phase0_headroom/results/
experiments/phase1_compiler/results/
```

If a required historical artifact has moved or is missing, record that in the
preflight report and continue with the available committed artifacts.

## Claim Boundary

Allowed claims:

```text
two_repo_supply_expansion_completed
existing_supply_inventory_completed
raw_candidate_mining_completed
source_context_enrichment_completed
local_certification_replay_completed
statement_generation_packets_prepared
endpoint_statement_generation_review_completed
statement_generation_blocked_by_endpoint_policy
expanded_certified_supply_created
expanded_supply_reaches_minimum
expanded_supply_below_minimum
local_bakeoff_rerun_completed
paid_replication_not_run
```

Disallowed claims:

```text
predictive_validity_established
paid_replication_completed
new_paid_acut_cells_run
H_future_used_as_target_profile
hidden_oracle_informed_selection
raw_transcript_informed_selection
local_subscription_llm_used_under_endpoint_rule
post_hoc_algorithm_claimed_as_preregistered_paid_design
followup_runbook_written_by_worker
```

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_two_repo_certified_supply_expansion.yaml
  tools/
    phase1_two_repo_certified_supply_expansion.py
    phase1_statement_generation_review_loop.py        # optional, only if needed
  tests/
    test_phase1_two_repo_certified_supply_expansion.py
    test_phase1_statement_generation_review_loop.py   # optional, only if used
  results/
    phase1_two_repo_supply_expansion_preflight.json
    phase1_two_repo_supply_expansion_existing_inventory.json
    phase1_two_repo_supply_expansion_duplicate_and_leakage_index.json
    phase1_two_repo_supply_expansion_mining_plan.json
    phase1_two_repo_supply_expansion_raw_candidates.json
    phase1_two_repo_supply_expansion_source_contexts.json
    phase1_two_repo_supply_expansion_certification_attempts.json
    phase1_two_repo_supply_expansion_statement_packets.json
    phase1_two_repo_supply_expansion_statement_generation_review.json
    phase1_two_repo_supply_expansion_eligibility_audit.json
    phase1_two_repo_supply_expansion_expanded_supply.json
    phase1_two_repo_supply_expansion_split_support.json
    phase1_two_repo_supply_expansion_local_bakeoff_rerun.json
    phase1_two_repo_supply_expansion_decision.json
  reports/
    phase1_two_repo_supply_expansion_process.md
    phase1_two_repo_supply_expansion_existing_inventory.md
    phase1_two_repo_supply_expansion_mining_plan.md
    phase1_two_repo_supply_expansion_raw_candidates.md
    phase1_two_repo_supply_expansion_source_contexts.md
    phase1_two_repo_supply_expansion_certification_attempts.md
    phase1_two_repo_supply_expansion_statement_generation_review.md
    phase1_two_repo_supply_expansion_eligibility_audit.md
    phase1_two_repo_supply_expansion_expanded_supply.md
    phase1_two_repo_supply_expansion_split_support.md
    phase1_two_repo_supply_expansion_local_bakeoff_rerun.md
    phase1_two_repo_supply_expansion_decision.md
```

If new Phase 0-style task artifacts are needed, write them under a new
versioned namespace. Do not overwrite canonical historical files:

```text
experiments/phase0_headroom/candidate_sources/
  attrs_supply_expansion_20260526_candidates.jsonl
  attrs_supply_expansion_20260526_source_context.jsonl
  boltons_supply_expansion_20260526_candidates.jsonl
  boltons_supply_expansion_20260526_source_context.jsonl
experiments/phase0_headroom/certified_tasks/
  attrs_supply_expansion_20260526_certified_tasks.jsonl
  attrs_supply_expansion_20260526_review_records.jsonl
  attrs_supply_expansion_20260526_task_statements.jsonl
  boltons_supply_expansion_20260526_certified_tasks.jsonl
  boltons_supply_expansion_20260526_review_records.jsonl
  boltons_supply_expansion_20260526_task_statements.jsonl
```

Do not commit raw cloned repositories, solver workspaces, verifier workspaces,
large raw diffs, raw GitHub API responses, raw prompts, raw completions, or raw
Codex CLI transcripts.

## Step 0: Preflight And Execution Ledger

Actions:

1. Read `AGENTS.md` and record the relevant boundary rules in the process
   report.
2. Record branch, HEAD, date, Python version, `uv --version`, current git
   status, and whether the working tree already contains unrelated changes.
3. Confirm the latest local bakeoff decision and supply blocker:

```bash
jq '{final_decision, mainline_recommendation, smallest_local_blocker}' \
  experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_decision.json
jq '{status, eligible_supply_by_repo, gates, candidate_algorithm_if_ready}' \
  experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_paid_readiness_gate.json
```

4. Create or update the config and preflight report.
5. Start `phase1_two_repo_supply_expansion_process.md` as an execution ledger.

Acceptance:

- Preflight records `paid_acut_calls: disabled`.
- Preflight records whether paid LLM statement generation is disabled, blocked,
  or later gated by endpoint variables.
- Starting supply counts match or explicitly explain differences from:

```text
attrs: 10
boltons: 12
```

Commit target:

```text
Record two-repo supply expansion preflight
```

## Step 1: Existing Supply Inventory

Actions:

1. Build a task-level inventory for `attrs` and `boltons` across all existing
   candidate, certified, release, preregistration, and score-table artifacts.
2. For each task, record sanitized fields only:

```text
repo_id
task_id
base_commit_present
target_commit_present
task_time
source_kind
source_context_status
statement_quality_gate
certification_gate_summary
release_split_eligibility
historical_paid_cells_present
outcome_seen_status
eligible_without_paid_outcome
changed_file_count
implementation_file_count
test_file_count
module_or_package
statement_digest
```

3. Produce a duplicate and leakage index:

```text
seen_task_ids
seen_target_commits
paid_outcome_seen_task_ids
paid_outcome_seen_target_commits
hidden_oracle_sensitive_artifacts_excluded
raw_transcripts_excluded
```

Acceptance:

- The inventory explains exactly why each existing task is or is not eligible.
- No raw prompts, completions, transcripts, hidden verifier content, or full raw
  diffs are committed.
- The duplicate/leakage index prevents reminting already outcome-seen tasks
  under new ids.

Commit target:

```text
Inventory existing attrs and boltons supply
```

## Step 2: Mining Plan And Stop Rules

Actions:

1. Define mining quotas:

```text
minimum_new_certified_needed:
  attrs: max(0, 30 - current_attrs_eligible)
  boltons: max(0, 30 - current_boltons_eligible)
stretch_new_certified_needed:
  attrs: max(0, 50 - current_attrs_eligible)
  boltons: max(0, 50 - current_boltons_eligible)
raw_candidate_floor_per_repo: 50
raw_candidate_soft_cap_per_repo: 160
local_certification_attempt_soft_cap_per_repo: 96
```

2. Define repository-history windows. Prefer broad chronological coverage over
   repeatedly mining the same module/time slice.
3. Define candidate priorities:

```text
prefer behavior/API bugfixes over refactors
prefer non-leaky issue or PR context
prefer target commits with local tests that expose behavior
prefer bounded implementation scope
prefer tasks not outcome-seen in any score table
avoid docs-only, project-config-heavy, formatting-only, dependency-only changes
avoid ambiguous project maintenance changes
avoid candidates whose public context states the exact solution patch
```

4. Define hard stop rules:

```text
stop a repo as supply-exhausted only after:
  - local history scan reaches the configured anchor cap, and
  - candidate source enrichment finds no additional non-leaky problem context,
    and
  - certification attempts reach the configured cap or all plausible candidates
    are exhausted, and
  - the report explains the dominant failure modes.
```

Acceptance:

- Mining plan targets both repos first.
- New repository selection is contingency-only and is not the main path.
- Stop rules prevent prematurely declaring the existing repos unusable.

Commit target:

```text
Define two-repo supply mining plan
```

## Step 3: Mine Raw Historical Candidates

Actions:

1. Use existing local repository-history tooling where possible. Extend it only
   when needed.
2. Mine `attrs` and `boltons` independently.
3. For each raw candidate, capture sanitized metadata:

```text
repo_id
candidate_id
target_commit
base_commit
task_time
changed_files
implementation_files
test_files
change_size_bucket
module_or_package
commit_subject_summary
candidate_source_refs
candidate_source_kind
public_context_available
diff_digest
diff_size_summary
```

4. If a full diff is useful for later statement generation, store the full diff
   only in ignored raw artifacts or regenerate it from the local repository when
   needed. Commit only digests, bounded summaries, and small sanitized packet
   excerpts.

Acceptance:

- At least 50 raw candidates per repo are mined unless supply depletion is
  proved and documented.
- Stretch toward 100-160 raw candidates per repo if early certification yield is
  low.
- Outcome-seen target commits are marked and excluded from promotion.

Commit target:

```text
Mine raw attrs and boltons supply-expansion candidates
```

## Step 4: Enrich Public Source Context

Actions:

1. Enrich each plausible raw candidate with public issue/PR context.
2. `gh api` or other GitHub metadata lookup is allowed if authenticated, but do
   not commit raw API responses.
3. Normalize context into sanitized records:

```text
source_ref
source_kind
title_or_summary
body_summary
linked_issue_refs
linked_pr_refs
problem_context_confidence
source_context_status
source_leakage_risks
source_context_digest
```

4. If source context is sparse but the repository diff clarifies the behavioral
   problem, keep the candidate in a separate `diff_assisted_statement_needed`
   queue. Do not reject it only because old PR context is short or empty.

Acceptance:

- Candidates are not penalized by an old hard 240-character truncation rule.
- A candidate may remain viable if it needs diff-assisted statement generation,
  but it must later pass independent leakage review.
- Source context failure modes are counted by repo and reason.

Commit target:

```text
Enrich public source context for supply candidates
```

## Step 5: Local Certification Replay

Actions:

1. Run local certification for prioritized candidates using the existing
   certification gates where possible.
2. Required gates:

```text
checkout
oracle_extractable
no_op_fail
reference_pass
known_bad_fail
flakiness_check
scope_clarity_review
cost_boundedness
taxonomy_labelability
solution_leakage_review
statement_quality_review
```

3. Keep certification local. Do not run paid ACUT cells.
4. Store raw local workspaces under ignored workspace/cache paths only.
5. Commit sanitized review records, gate summaries, and failure taxonomy.

Acceptance:

- Certification attempts are bounded and resumable.
- Each promoted task has all required gates passing or a documented reason why
  a gate is not applicable.
- Known near-misses are preserved as diagnostic records, not silently promoted.

Commit target:

```text
Replay local certification for supply candidates
```

## Step 6: Prepare Statement Generation Packets

Actions:

1. Prepare statement packets for candidates that pass local certification or are
   one clearly fixable statement-quality step away from eligibility.
2. Each packet may include:

```text
public issue/PR summary
linked public context summaries
base behavior summary
expected behavior summary inferred from repository history
bounded diff summary
changed file categories
implementation scope hints
test behavior summary
explicit leakage constraints
```

3. Do not include hidden verifier content, raw ACUT transcripts, raw prompts, or
   raw completions.
4. Do not hard-truncate the future solver statement. Use a soft target:

```text
preferred solver statement length: 800-1500 characters
maximum before manual review: 2200 characters
no hard truncation
no mid-sentence cuts
no unclosed code fences
```

5. Mark whether each packet requires endpoint LLM generation/review or can be
   accepted with existing human-authored/public context.

Acceptance:

- Packet count is sufficient to plausibly reach 30 eligible tasks per repo, or
  the deficit is explained.
- Packets separate generation-only diff context from solver-visible statement
  text.
- The report explicitly states that diff-assisted generation is allowed only if
  the final statement passes leakage review.

Commit target:

```text
Prepare diff-assisted statement generation packets
```

## Step 7: Optional Endpoint Statement Generation And Review Loop

Run this step only if Step 6 shows that statement generation/review is needed
to reach the minimum supply target.

Actions:

1. Source shell configuration if needed, then check:

```bash
test -n "$LLM_BASE_URL"
test -n "$LLM_API_KEY"
```

2. Prove that the intended Codex CLI or wrapper uses `LLM_BASE_URL` and
   `LLM_API_KEY`. If this cannot be proved, do not run the loop. Write:

```text
experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_statement_generation_blocker.md
```

3. If the endpoint rule is satisfied, run two independent sessions or roles:

```text
Generator:
  input: statement packet with public context plus bounded diff summary
  output: solver-visible statement candidate plus rationale digest
  constraints:
    - no target commit
    - no patch text
    - no exact solution algorithm unless public problem context already says it
    - no hidden oracle details
    - no test edits
    - soft length target, no hard truncation

Reviewer:
  input: statement packet plus generated statement
  output: pass/fail plus concrete leakage/clarity findings
  checks:
    - answer leakage
    - patch-shaped wording
    - missing API intent
    - impossible or underspecified reproduction
    - unclosed code blocks
    - overfit file/test hints
    - statement/source mismatch
```

4. Iterate generator and reviewer until review passes or a bounded retry limit
   is reached.
5. Commit only sanitized final statements, review summaries, digests, and cost
   summary. Do not commit raw prompts, raw completions, or session transcripts.

Acceptance:

- If the loop runs, the report proves endpoint compliance and records total
  paid LLM cost or conservative estimate.
- If the loop does not run, the blocker is explicit and no deterministic
  substitute is presented as if it were the requested generator/reviewer loop.
- Every generated statement that enters supply has an independent review pass.

Commit target:

```text
Run endpoint statement generation review loop
```

or, if blocked:

```text
Record statement generation endpoint blocker
```

## Step 8: Eligibility Audit And Expanded Supply Freeze

Actions:

1. Combine existing eligible tasks and newly certified tasks under a versioned
   expanded-supply manifest.
2. For each task, record:

```text
repo_id
task_id
task_time
source_ref
source_context_status
statement_digest
certification_gate_summary
leakage_review_status
outcome_seen_status
release_eligible
promotion_reason
```

3. Produce per-repo counts:

```text
existing_eligible
new_eligible
total_eligible
minimum_target_met
stretch_target_met
```

4. Do not mutate prior canonical releases. The expanded supply is a new
   versioned candidate inventory.

Acceptance:

- Minimum success requires `attrs >= 30` and `boltons >= 30` eligible tasks.
- If either repo remains below 30, the report explains whether the limit came
  from raw supply, public context, certification, statement quality, leakage,
  or time.
- No outcome-seen target commit is promoted as new supply.

Commit target:

```text
Freeze expanded two-repo certified supply
```

## Step 9: Split Support And Target-Profile Diagnostics

Actions:

1. Analyze whether expanded supply supports stable local validation:

```text
per-repo count
chronological coverage
module/package coverage
taxonomy coverage
source kind mix
certification failure mix
eligible B_eval/H_future-style chronological split options
pseudo-future window count
minimum per-window support
```

2. Recompute target-profile diagnostics without using paid outcomes as target
   features.
3. Keep `H_future` as a validation holdout concept, not as the target profile
   itself.

Acceptance:

- The split-support report says whether the expanded inventory is large enough
  to rerun local bakeoff meaningfully.
- If support is still too sparse, stop before local bakeoff rerun and write the
  exact blocker.

Commit target:

```text
Analyze expanded supply split support
```

## Step 10: Local Bakeoff Rerun On Expanded Supply

Run this step only if Step 9 says split support is adequate.

Actions:

1. Rerun or extend the local algorithm bakeoff using the expanded inventory.
2. Include at least these designs:

```text
repo_unweighted_same_budget
repo_stratified_by_target_profile
temporal_recent_baseline
seeded_random_same_budget
block_randomized_stratified
block_plus_shrinkage_weighted
old_weighted_target_profile as reference only
```

3. Use multiple seeds/windows where supply allows.
4. Evaluate:

```text
mean absolute B_eval/H_future gap
max gap
catastrophic miss rate
per-repo stability
per-window stability
seed stability
ESS and max-weight diagnostics for weighted designs
```

Acceptance:

- A new design can be promoted only if it beats the simple stratified baseline
  by at least 15% local MAE, avoids catastrophic misses, and is stable across
  repos/windows/seeds.
- If no design passes, keep simple stratified as the conservative mainline.
- This step still does not authorize paid replication.

Commit target:

```text
Rerun local bakeoff on expanded supply
```

## Step 11: New Repository Contingency Screen

Run this step only if at least one existing repo is supply-exhausted below 30
eligible tasks after the configured mining and certification effort.

Actions:

1. Do not deep-mine a new repo by default.
2. Create a lightweight new-repo contingency screen for 3-5 Python libraries.
3. Evaluate only public, local, non-paid feasibility signals:

```text
history depth
issue/PR quality
test suite stability
dependency/environment complexity
API/task diversity
likely non-leaky source availability
estimated certified supply
maintenance timeline coverage
```

4. Recommend whether the next coordinating session should choose a third repo.

Acceptance:

- This is a contingency memo, not a new benchmark expansion claim.
- No paid ACUT cells are run.
- No follow-up runbook is drafted.

Commit target:

```text
Screen contingency repositories after supply depletion
```

## Step 12: Final Decision And Closeout

Actions:

1. Write final decision JSON and Markdown.
2. Answer these directly:

```text
RQ1: Did attrs reach at least 30 eligible certified tasks?
RQ2: Did boltons reach at least 30 eligible certified tasks?
RQ3: If not, what exact gate depleted supply?
RQ4: Did diff-assisted statement generation/review run? If yes, was it endpoint
    compliant? If no, why not?
RQ5: Is expanded local supply sufficient to rerun stable local bakeoff?
RQ6: Did any rerun local design beat simple stratified baseline robustly?
RQ7: Is the project ready for a future paid replication preregistration, or
    should it keep mining/screening locally?
```

3. Record boundary checks:

```text
new_paid_acut_calls_made
new_paid_task_solving_calls_made
new_paid_llm_statement_calls_made
endpoint_rule_satisfied_if_paid_llm_used
raw_artifacts_committed
followup_runbook_written_by_worker
```

4. Run verification:

```bash
uv run pytest experiments/phase1_compiler/tests -q
git diff --check
```

If scoped tests are too broad or fail for unrelated existing reasons, run the
nearest relevant tests and document the exact failure.

Acceptance:

- Decision is one of:

```text
expanded_supply_ready_for_local_bakeoff
expanded_supply_and_local_bakeoff_ready_for_preregistration_planning
keep_stratified_mainline_more_local_supply_needed
existing_repos_supply_exhausted_screen_new_repo
blocked_with_precise_reason
```

- Final report is sufficient for the coordinating session to decide the next
  runbook.
- The worker does not write the next runbook.

Commit target:

```text
Record two-repo supply expansion decision
```

