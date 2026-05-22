# Phase 1 Clean Outcome-Unseen Supply Mining Runbook

Status: implementation runbook, 2026-05-22.

This runbook is for one dedicated Codex CLI session. Its job is to continue
clean outcome-unseen task mining after the `B_real` extension runbook blocked,
and to leave Phase 1 either ready for a preregistered paid clean future-holdout
runbook or blocked with a precise supply-depletion report.

This is still a local-only runbook. It must not run paid ACUT solving cells and
must not make experiment LLM calls.

## Starting State

The immediately preceding runbook ended with:

```text
primary_decision_label: clean_supply_breal_extension_still_blocked
recommended_next_runbook: continue_mining_clean_outcome_unseen_supply
clean_supply_ready: false
newly_promoted_task_ids: []
paid_llm_calls_made: false
paid_acut_calls_made: false
predictive_validity_established: false
```

Current clean-supply sidecar evidence for `boltons`:

```text
B_real:
  boltons__hist__011

W_real:
  boltons__hist__022
  boltons__hist__023
  boltons__hist__027
```

The strict minimum remains:

```text
B_real >= 2
W_real >= 2
```

The missing piece is at least one additional clean outcome-unseen `boltons`
task early enough to support a future-holdout cutoff with two `B_eval` tasks
and two later `H_future` tasks. If `boltons` cannot produce this locally, the
worker may screen `attrs` as a backup repo, but it must keep the claim limited
to readiness for a future paid validation run.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-1-clean-outcome-unseen-supply-mining-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make cohesive commits after completing one or more related steps.

Your goal is to continue mining clean outcome-unseen task supply after
phase1_clean_supply_breal_extension_still_blocked. First try to add enough
Boltons clean supply to make strict future-holdout preregistration possible.
If Boltons supply is exhausted under the non-leakage rules, locally screen attrs
as a backup repo.

Do not run paid ACUT task-solving cells. Do not make experiment LLM calls.
GitHub metadata lookup, local repository-history mining, local verifier replay,
deterministic reports, tests, and small sanitized manifests are allowed.

Do not promote outcome-seen, solution-leaky, project-heavy ambiguous, or
commit-message-only tasks just to satisfy split counts. Do not lower the clean
split minimum. Do not claim predictive validity.

If you extend future-holdout tooling, make it consume a clean-supply overlay as
explicit sidecar evidence. Do not silently mutate canonical hardening results.

Do not commit secrets, raw GitHub API responses, full raw prompts, raw
completions, raw ACUT transcripts, solver workspaces, verifier workspaces,
cloned external repositories, .venv, caches, or large raw outputs. Commit only
small sanitized configs, manifests, tools, tests, reports, summaries, and
digests.

Do not push unless explicitly asked.
```

## Claim Boundary

Allowed claims:

```text
clean_outcome_unseen_supply_mining_completed
clean_supply_overlay_created
boltons_clean_supply_ready_for_preregistered_validation
backup_repo_clean_supply_ready_for_preregistered_validation
strict_future_holdout_design_preregistered
strict_clean_future_holdout_still_blocked
insufficient_evidence_for_predictive_validity
```

Disallowed claims:

```text
predictive_validity_established
clean_future_holdout_validated_without_paid_holdout_run
production_benchmark_ranking
pure_harness_effect
validation_grade_humanize_if_commit_fallback_only
promotion_of_solution_leaky_or_project_heavy_tasks
contamination_proof_evaluation_if_model_snapshot_unknown
```

## Important Design Constraint

The previous clean-supply extension output is a sidecar overlay, not a rewrite
of the canonical hardening overlay. This runbook may update
`phase1_future_holdout.py` so that future-holdout supply design can consume
explicit clean-supply overlay files, but the output must keep provenance clear:

```text
evidence_level: clean_supply_overlay_sidecar
predictive_validity_established: false
```

Do not make a task look like it passed the original hardening overlay if it was
manually promoted only by the clean-supply overlay review. Instead, record both
the original hardening status and the clean overlay promotion reason.

## Promotion Rules

A task may enter clean supply only if all are true:

- the task id and target commit are absent from current ACUT scorecards and all
  local score tables;
- the task has non-leaky public problem context from an issue, PR, issue
  comment, PR comment, or equivalent sanitized source;
- the solver-visible statement can be written from that non-leaky context
  without reading the solution patch;
- local certification shows hidden oracle extractable, no-op fail, reference
  pass, known-bad fail, flakiness check pass, ambiguity review pass, solution
  leakage review pass, scope clarity pass, cost boundedness pass, and taxonomy
  labelability pass;
- project/config/docs changes are absent or clearly ancillary to a behavior
  change;
- solution exposure risk is absent;
- the task is not Humanize commit-message fallback and not a generic
  comparator;
- adding the task can support a chronological future-holdout cutoff, not merely
  a historical `B_real`/`W_real` count.

Do not promote `boltons__hist__014`, `boltons__hist__006`, or
`boltons__hist__013` unless the prior blocker is genuinely disproved with new
non-leaky evidence. The expected path is to find new supply, not to relabel
known bad candidates.

## Budget And Runtime Rules

Default:

```text
paid_acut_calls: disabled
direct_paid_llm_calls: disabled
```

Allowed:

```text
local git inspection
local gh metadata lookup if authenticated
local repository clone or fetch into ignored external_repos paths
local candidate mining
local certification replay
local pytest and validation
deterministic artifact generation
```

The worker may run for multiple hours locally. It should prefer bounded batches:

```text
boltons history scan: up to 1000 anchors
boltons local certification attempts: up to 48 new candidates
attrs backup history scan: up to 1000 anchors if Boltons exhausts
attrs backup local certification attempts: up to 48 candidates
paid provider cost: 0
```

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_clean_outcome_unseen_supply_mining.yaml
  tools/
    phase1_clean_outcome_unseen_supply_mining.py
    phase1_future_holdout.py
    phase1_compiler.py
  tests/
    test_phase1_clean_outcome_unseen_supply_mining.py
    test_phase1_future_holdout.py
    test_phase1_compiler.py
  results/
    phase1_clean_outcome_unseen_supply_preflight.json
    phase1_clean_outcome_unseen_supply_candidate_inventory.json
    phase1_clean_outcome_unseen_supply_review.json
    phase1_clean_outcome_unseen_supply_overlay.json
    phase1_clean_outcome_unseen_supply_decision.json
    phase1_future_holdout_clean_supply.json
    phase1_future_holdout_cutoff_plan.json
    phase1_future_holdout_preregistration.json
    phase1_future_holdout_prediction_metrics.json
    phase1_future_holdout_decision.json
    phase1_mvp_closeout.json
  reports/
    phase1_clean_outcome_unseen_supply_process.md
    phase1_clean_outcome_unseen_supply_candidate_inventory.md
    phase1_clean_outcome_unseen_supply_review.md
    phase1_clean_outcome_unseen_supply_overlay.md
    phase1_clean_outcome_unseen_supply_decision.md
    phase1_future_holdout_clean_supply.md
    phase1_future_holdout_cutoff_plan.md
    phase1_future_holdout_preregistration.md
    phase1_future_holdout_prediction_metrics.md
    phase1_future_holdout_decision.md
    phase1_mvp_closeout.md
```

If new local mining artifacts are needed, write them under a separate namespace:

```text
experiments/phase0_headroom/candidate_sources/
  boltons_clean_outcome_unseen_supply_*.jsonl
  attrs_clean_outcome_unseen_supply_*.jsonl
experiments/phase0_headroom/certified_tasks/
  boltons_clean_outcome_unseen_supply_*.jsonl
  attrs_clean_outcome_unseen_supply_*.jsonl
```

Do not overwrite canonical release files such as:

```text
experiments/phase0_headroom/releases/boltons_phase0_pilot_release.json
experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl
experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json
```

## Step 0: Preflight

Actions:

1. Confirm the current branch and blocker:

```bash
git status --short --branch
git log --oneline -5
jq '{primary_decision_label, clean_supply_ready, recommended_next_runbook, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_decision.json
jq '{clean_supply_ready, promoted_by_split, minimum_clean_split, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_overlay.json
```

2. Record the stale future-holdout supply state for comparison:

```bash
jq '{clean_supply_ready, selected_repos, repo_summary, blockers}' \
  experiments/phase1_compiler/results/phase1_future_holdout_clean_supply.json
```

3. Run baseline checks:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

4. Write:

```text
experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_preflight.json
experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_process.md
```

Acceptance:

- previous decision is `clean_supply_breal_extension_still_blocked`;
- previous clean overlay has `B_real=1`, `W_real>=2`;
- no paid calls have been made;
- baseline checks pass or any failure is recorded as a pre-existing blocker.

Commit:

```bash
git add experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_preflight.json \
  experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_process.md
git commit -m "Record Phase 1 clean outcome-unseen supply preflight"
```

## Step 1: Configure Continued Mining

Create:

```text
experiments/phase1_compiler/configs/phase1_clean_outcome_unseen_supply_mining.yaml
```

Minimum schema:

```yaml
schema_version: barcarolle.phase1_clean_outcome_unseen_supply_mining.v1
status: configured
claim_scope: clean_supply_mining_not_predictive_validation
predictive_validity_established: false
paid_acut_calls: disabled
paid_llm_calls: disabled

target:
  primary_repo: boltons
  backup_repos:
    - attrs
  minimum_clean_split:
    B_real: 2
    W_real: 2
  required_future_holdout_minimum:
    b_eval_tasks_per_repo: 2
    h_future_tasks_per_repo: 2
  prior_clean_supply_overlay: experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_overlay.json
  first_choice_missing_supply:
    repo_id: boltons
    split: B_real
    count: 1

mining:
  extension_namespace: clean_outcome_unseen_supply
  boltons_max_history_anchors: 1000
  boltons_max_certification_attempts: 48
  backup_max_history_anchors: 1000
  backup_max_certification_attempts: 48
  prefer_candidates_before_task_time: "2023-04-02T15:11:27-04:00"
  require_cutoff_feasibility: true

source_artifacts:
  current_breal_extension_decision: experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_decision.json
  current_breal_extension_overlay: experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_overlay.json
  current_breal_candidate_audit: experiments/phase1_compiler/results/phase1_clean_supply_breal_candidate_audit.json
  future_holdout_config: experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml
  future_holdout_clean_supply: experiments/phase1_compiler/results/phase1_future_holdout_clean_supply.json
  hardening_overlay: experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json
  workspace_scorecard: experiments/phase1_compiler/results/phase1_workspace_scorecard.json
  boltons_local_repo: experiments/phase0_headroom/external_repos/boltons
  attrs_local_repo: experiments/phase0_headroom/external_repos/attrs

promotion_policy:
  require_outcome_unseen: true
  require_target_commit_unseen: true
  require_non_leaky_problem_context: true
  reject_commit_message_only_source: true
  reject_solution_exposure_risk: true
  reject_project_heavy_ambiguous_context: true
  reject_project_or_docs_only: true
  require_oracle_alignment: true
  require_local_certification_gates: true
  require_future_holdout_cutoff_feasibility: true

future_holdout_overlay_integration:
  enabled: true
  evidence_level: clean_supply_overlay_sidecar
  mutate_hardening_overlay: false
```

Acceptance:

- config disables paid LLM and paid ACUT calls;
- config names the prior blocker and overlay;
- config requires cutoff feasibility, not only `B_real` count;
- config preserves `predictive_validity_established: false`.

Commit:

```bash
git add experiments/phase1_compiler/configs/phase1_clean_outcome_unseen_supply_mining.yaml
git commit -m "Configure Phase 1 clean outcome-unseen supply mining"
```

## Step 2: Add Continued-Mining Tooling

Add:

```text
experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py
experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py
```

The tool should expose these commands:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py \
  audit-state

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py \
  mine-boltons

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py \
  review-candidates

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py \
  mine-backup

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py \
  build-overlay

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py \
  decide
```

Implementation requirements:

- reuse existing deterministic helpers where practical, but do not overwrite
  canonical `boltons_*` release or certification files;
- assign new extension task ids with no collision, for example
  `boltons__clean_ext__001` or `attrs__clean_ext__001`;
- keep `repo_id` as the actual target repo, for example `boltons`, even if the
  task id uses an extension namespace;
- skip any task id or target commit that appears in `phase1_workspace_scorecard`
  or any `experiments/phase0_headroom/results/*_score_table.csv`;
- skip known rejected target commits unless the new review supplies genuinely
  new non-leaky context;
- collect sanitized PR/issue context summaries only, not raw API responses;
- write command-result hashes or summaries, not raw stdout/stderr logs;
- compute whether the combined clean supply can satisfy the future-holdout
  cutoff with `B_eval>=2`, `H_future>=2`, and the configured embargo gap.

Test requirements:

- outcome-seen task ids are never promoted;
- outcome-seen target commits are never promoted under a renamed task id;
- solution-exposure rows are rejected;
- project-heavy ambiguous rows remain manual/rejected;
- commit-message-only rows are diagnostic-only;
- extension ids do not collide with existing `boltons__hist__*` ids;
- overlay preserves prior promoted clean tasks;
- overlay readiness requires both clean split counts and chronological
  future-holdout feasibility;
- predictive validity always remains false.

Run:

```bash
uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py
```

Acceptance:

- new tests pass;
- no paid-call path exists in the new tool;
- artifact paths are small, sanitized, and under committed result/report paths
  or ignored raw/workspace paths as appropriate.

Commit:

```bash
git add experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py \
  experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py
git commit -m "Add Phase 1 clean outcome-unseen supply mining tooling"
```

## Step 3: Mine Additional Boltons Supply

Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py \
  audit-state

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py \
  mine-boltons

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py \
  review-candidates
```

Expected outputs:

```text
experiments/phase0_headroom/candidate_sources/boltons_clean_outcome_unseen_supply_candidates.jsonl
experiments/phase0_headroom/candidate_sources/boltons_clean_outcome_unseen_supply_source_context.jsonl
experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_review_records.jsonl
experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_candidate_inventory.json
experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_review.json
experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_candidate_inventory.md
experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_review.md
```

Review the result:

```bash
jq '{repo_summary, recommended_path, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_candidate_inventory.json
jq '{promoted_by_repo, rejected_counts, cutoff_feasibility, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_review.json
```

Acceptance:

- every promoted candidate has sanitized non-leaky source context;
- every promoted candidate has local certification gates recorded;
- every promoted candidate is outcome-unseen by task id and target commit;
- at least one promoted `boltons` candidate is early enough to support two
  `B_eval` and two `H_future` clean tasks, or the report explains why Boltons
  supply is exhausted.

Commit:

```bash
git add experiments/phase0_headroom/candidate_sources/boltons_clean_outcome_unseen_supply_*.jsonl \
  experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_*.jsonl \
  experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_candidate_inventory.json \
  experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_review.json \
  experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_candidate_inventory.md \
  experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_review.md \
  experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_process.md
git commit -m "Mine Boltons clean outcome-unseen supply"
```

If Boltons is ready, skip Step 4 and continue to Step 5. If not, continue to
Step 4.

## Step 4: Screen Attrs As Backup If Boltons Is Exhausted

Run this step only if Step 3 cannot produce a Boltons-ready clean overlay.

Actions:

1. Ensure `attrs` exists under the ignored external repo path, or clone it:

```bash
test -d experiments/phase0_headroom/external_repos/attrs/.git || \
  git clone https://github.com/python-attrs/attrs.git \
  experiments/phase0_headroom/external_repos/attrs
```

2. Run backup mining:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py \
  mine-backup

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py \
  review-candidates
```

Expected outputs:

```text
experiments/phase0_headroom/candidate_sources/attrs_clean_outcome_unseen_supply_candidates.jsonl
experiments/phase0_headroom/candidate_sources/attrs_clean_outcome_unseen_supply_source_context.jsonl
experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_review_records.jsonl
```

Acceptance:

- backup repo reaches at least two clean early tasks and two clean later tasks
  under the configured embargo, or the report names the exact blocker;
- backup repo tasks pass the same non-leakage and certification rules as
  Boltons;
- `attrs` is added to future-holdout primary eligibility only if local clean
  supply is ready;
- predictive validity remains false.

Commit:

```bash
git add experiments/phase0_headroom/candidate_sources/attrs_clean_outcome_unseen_supply_*.jsonl \
  experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_*.jsonl \
  experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_candidate_inventory.json \
  experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_review.json \
  experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_candidate_inventory.md \
  experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_review.md \
  experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_process.md
git commit -m "Screen attrs backup clean outcome-unseen supply"
```

## Step 5: Build Clean-Supply Overlay

Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py \
  build-overlay

jq '{clean_supply_ready, promoted_by_repo, promoted_by_split, cutoff_feasibility, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_overlay.json
```

The overlay must include:

- prior clean Boltons tasks from
  `phase1_clean_supply_breal_extension_overlay.json`;
- newly promoted Boltons extension tasks, if any;
- newly promoted backup repo tasks, if Step 4 ran;
- original hardening status for each task when available;
- clean overlay promotion decision and promotion rationale;
- future-holdout cutoff feasibility.

Acceptance:

- `clean_supply_ready=true` only if at least one repo can satisfy the
  future-holdout minimum with clean outcome-unseen tasks;
- `predictive_validity_established=false`;
- no outcome-seen, solution-leaky, or project-heavy ambiguous task appears in
  the promoted set.

Commit:

```bash
git add experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_overlay.json \
  experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_overlay.md \
  experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_process.md
git commit -m "Build Phase 1 clean outcome-unseen supply overlay"
```

## Step 6: Integrate Overlay With Future-Holdout Design

Extend:

```text
experiments/phase1_compiler/tools/phase1_future_holdout.py
experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml
experiments/phase1_compiler/tests/test_phase1_future_holdout.py
```

Required behavior:

- config can name one or more clean-supply overlay files;
- `audit-supply` includes clean overlay promoted tasks as eligible supply when
  their `repo_id` is primary eligible;
- output records that these tasks came from `clean_supply_overlay_sidecar`;
- original hardening overlay remains unchanged;
- diagnostic-only repos remain excluded unless the config explicitly promotes a
  locally ready backup repo to primary eligibility;
- predictive validity remains false.

Run:

```bash
uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_future_holdout.py

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_future_holdout.py \
  audit-supply \
  --config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_future_holdout.py \
  design-cutoff \
  --config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_future_holdout.py \
  preregister \
  --config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_future_holdout.py \
  score \
  --config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml
```

Inspect:

```bash
jq '{clean_supply_ready, selected_repos, repo_summary, blockers, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_future_holdout_clean_supply.json
jq '{status, selected_repos, splits, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_future_holdout_preregistration.json
jq '{primary_decision_label, recommended_next_runbook, b_eval_task_ids, h_future_task_ids, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_future_holdout_decision.json
```

Acceptance:

- if the overlay is ready, preregistration status is `frozen`;
- if paid score tables do not exist, decision is not a validation result and
  recommends a paid preregistered clean future-holdout runbook;
- if the overlay is not ready, decision stays `future_holdout_supply_blocked`;
- no predictive-validity claim is introduced.

Commit:

```bash
git add experiments/phase1_compiler/tools/phase1_future_holdout.py \
  experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml \
  experiments/phase1_compiler/tests/test_phase1_future_holdout.py \
  experiments/phase1_compiler/results/phase1_future_holdout_clean_supply.json \
  experiments/phase1_compiler/results/phase1_future_holdout_cutoff_plan.json \
  experiments/phase1_compiler/results/phase1_future_holdout_preregistration.json \
  experiments/phase1_compiler/results/phase1_future_holdout_prediction_metrics.json \
  experiments/phase1_compiler/results/phase1_future_holdout_decision.json \
  experiments/phase1_compiler/reports/phase1_future_holdout_clean_supply.md \
  experiments/phase1_compiler/reports/phase1_future_holdout_cutoff_plan.md \
  experiments/phase1_compiler/reports/phase1_future_holdout_preregistration.md \
  experiments/phase1_compiler/reports/phase1_future_holdout_prediction_metrics.md \
  experiments/phase1_compiler/reports/phase1_future_holdout_decision.md
git commit -m "Integrate clean supply overlay with future holdout design"
```

## Step 7: Decide

Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py \
  decide
```

Write:

```text
experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_decision.json
experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_decision.md
```

Allowed primary decisions:

```text
boltons_clean_supply_ready_for_preregistered_validation
backup_repo_clean_supply_ready_for_preregistered_validation
clean_supply_continued_mining_still_blocked
clean_supply_mining_tooling_blocked
```

Decision rules:

- Use `boltons_clean_supply_ready_for_preregistered_validation` only if Boltons
  overlay supply is clean, outcome-unseen, cutoff-feasible, and future-holdout
  preregistration is frozen.
- Use `backup_repo_clean_supply_ready_for_preregistered_validation` only if a
  backup repo is clean, outcome-unseen, cutoff-feasible, primary-eligible in
  the future-holdout config, and preregistration is frozen.
- Use `clean_supply_continued_mining_still_blocked` if neither repo can reach
  clean supply under the promotion rules.
- Use `clean_supply_mining_tooling_blocked` only for a local tooling or test
  problem that prevents a trustworthy supply decision.

Recommended next runbooks:

```text
run_preregistered_clean_future_holdout_paid_validation
continue_mining_clean_outcome_unseen_supply_with_additional_backup_repo
repair_clean_supply_mining_tooling
```

Acceptance:

- final decision names exact promoted task ids and rejected blocker counts;
- final decision says whether preregistration is frozen;
- final decision says `predictive_validity_established=false`;
- no paid calls were made.

Commit:

```bash
git add experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_decision.json \
  experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_decision.md \
  experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_process.md
git commit -m "Decide Phase 1 clean outcome-unseen supply mining"
```

## Step 8: Refresh Phase 1 Boundary

Update the Phase 1 MVP closeout to import the new supply decision as sidecar
evidence. Extend tests if necessary.

Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  build-mvp \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

Acceptance:

- closeout imports `phase1_clean_outcome_unseen_supply_decision.json`;
- closeout records whether clean future-holdout preregistration is ready;
- closeout keeps `predictive_validity_established=false`;
- production ranking remains `not_produced`.

Commit:

```bash
git status --short
git add experiments/phase1_compiler/tools/phase1_compiler.py \
  experiments/phase1_compiler/tests/test_phase1_compiler.py \
  experiments/phase1_compiler/results/phase1_mvp_closeout.json \
  experiments/phase1_compiler/reports/phase1_mvp_closeout.md
git commit -m "Refresh Phase 1 boundary after clean supply mining"
```

If `build-mvp` deterministically refreshes additional Phase 1 compiler summary
artifacts, inspect them with `git diff` and stage only those sanitized
result/report files. Do not stage raw outputs or workspace paths.

## Step 9: Final Verification

Run:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
git status --short
```

Check artifact hygiene:

```bash
git ls-files \
  experiments/phase0_headroom/results/raw \
  experiments/phase0_headroom/workspaces \
  experiments/phase0_headroom/external_repos \
  experiments/phase0_headroom/.venv \
  experiments/phase1_compiler/.venv \
  experiments/phase0_headroom/tools/__pycache__ \
  experiments/phase1_compiler/tools/__pycache__ \
  experiments/phase1_compiler/tests/__pycache__
```

Acceptance:

- final tests pass;
- `git diff --check` passes;
- no raw/workspace/external repo/venv/cache path is tracked;
- final decision JSON and report are committed;
- no paid LLM or paid ACUT calls were made;
- no push is performed.

Final worker response should include:

- final primary decision label;
- promoted clean task ids by repo and split;
- whether Boltons became ready;
- whether a backup repo was used;
- selected future-holdout repos, if any;
- preregistration status;
- predictive validity status;
- recommended next runbook;
- final test results.

## Expected Branches

### Boltons Ready

Expected decision:

```text
boltons_clean_supply_ready_for_preregistered_validation
```

Next runbook:

```text
run_preregistered_clean_future_holdout_paid_validation
```

### Backup Repo Ready

Expected decision:

```text
backup_repo_clean_supply_ready_for_preregistered_validation
```

Next runbook:

```text
run_preregistered_clean_future_holdout_paid_validation
```

### Still Blocked

Expected decision:

```text
clean_supply_continued_mining_still_blocked
```

Next runbook:

```text
continue_mining_clean_outcome_unseen_supply_with_additional_backup_repo
```

Do not lower the clean split minimum and do not relabel known leaky or ambiguous
tasks to avoid this blocker.
