# Phase 1 Clean Supply B_real Extension Runbook

Status: implementation runbook, 2026-05-22.

This runbook is for one dedicated Codex CLI session. Its job is to unblock the
strict clean future-holdout path by adding at least one more clean
outcome-unseen `B_real` task, preferably for `boltons`.

This runbook is local-only by default. It must not run paid ACUT solving cells.
Its main output is a clean-supply overlay that a later preregistered paid
validation runbook can consume.

## Starting State

The previous runbook completed the retrospective track but left clean supply
blocked:

```text
primary_decision_label: retrospective_validation_complete_clean_supply_still_blocked
recommended_next_runbook: mine_additional_clean_outcome_unseen_supply
predictive_validity_established: false
```

Current promoted clean outcome-unseen Boltons supply:

```text
B_real:
  boltons__hist__011

W_real:
  boltons__hist__022
  boltons__hist__023
  boltons__hist__027
```

Minimum strict clean split requirement:

```text
B_real >= 2
W_real >= 2
```

The missing piece is one additional clean `B_real` task. The first candidate is:

```text
boltons__hist__014
```

It is currently `manual_review_required` because of:

```text
scope_context_project_heavy_or_ambiguous
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-1-clean-supply-breal-extension-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make cohesive commits after completing one or more related steps.

Your goal is to add at least one clean outcome-unseen B_real task for strict
future-holdout validation. Prefer repairing/reviewing boltons__hist__014. If it
cannot be safely promoted, mine additional local Boltons candidates without
overwriting prior Phase 0/Phase 1 artifacts.

This runbook is local-only by default. Do not run paid ACUT solving cells. Do
not use LLM calls for source review, candidate mining, or certification. If a
later branch unexpectedly needs paid ACUT calls, stop and write a decision
asking for a dedicated paid-validation runbook.

Keep claim labels honest:
- promoted clean supply can unblock a future paid validation runbook;
- it does not itself establish predictive validity;
- retrospective outcome-seen data remains retrospective only.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts,
solver workspaces, verifier workspaces, cloned external repositories, .venv,
caches, raw GitHub API responses, or large raw outputs. Commit only small
sanitized configs, manifests, overlays, reports, and decision files.

Do not push unless explicitly asked.
```

## Claim Boundary

Allowed claims:

```text
clean_supply_breal_extension_audited
clean_supply_overlay_created
clean_supply_ready_for_preregistered_validation
strict_future_holdout_unblocked_for_design
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
```

## Evidence Rules

A task may be promoted into the clean-supply overlay only if all are true:

- it is outcome-unseen in current workspace scorecards and score tables;
- it has non-leaky problem context, preferably PR or issue context, not only a
  commit subject;
- hidden oracle alignment is intact;
- no-op fails and reference passes remain true in existing local certification
  evidence, or are rechecked locally without paid ACUT calls;
- implementation scope is clear enough for a solver-visible task statement;
- project/config/docs changes are either absent or clearly ancillary to a
  behavior-code change;
- solution exposure risk is not present;
- it is not a generic comparator and not Humanize commit-message fallback.

Do not promote a task simply because the split count needs it.

## Candidate Priority

Use this order:

1. Deep-review `boltons__hist__014`.
2. If still blocked, reassess other outcome-unseen Boltons `B_real` rows that
   were rejected only if the original blocker can be repaired without leakage.
3. If still blocked, locally mine additional outcome-unseen Boltons candidates
   into a separate extension namespace.
4. If Boltons cannot provide an additional clean `B_real`, screen a backup repo
   locally, but do not start paid validation in this runbook.

Do not use previously observed ACUT tasks as clean supply.

## Budget And Parallelism

Default:

```text
paid_acut_calls: disabled
direct_paid_llm_calls: disabled
```

Allowed:

```text
local git inspection
local gh metadata lookup if authenticated
local certification checks
local pytest/oracle replay
local artifact generation
```

No paid parallelism is needed.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_clean_supply_breal_extension.yaml
  tools/
    phase1_clean_supply_breal_extension.py
  tests/
    test_phase1_clean_supply_breal_extension.py
  results/
    phase1_clean_supply_breal_extension_preflight.json
    phase1_clean_supply_breal_candidate_audit.json
    phase1_clean_supply_boltons_014_review.json
    phase1_clean_supply_breal_extension_overlay.json
    phase1_clean_supply_breal_extension_decision.json
    phase1_future_holdout_clean_supply.json
    phase1_future_holdout_cutoff_plan.json
    phase1_future_holdout_preregistration.json
    phase1_mvp_closeout.json
  reports/
    phase1_clean_supply_breal_extension_process.md
    phase1_clean_supply_breal_candidate_audit.md
    phase1_clean_supply_boltons_014_review.md
    phase1_clean_supply_breal_extension_overlay.md
    phase1_clean_supply_breal_extension_decision.md
    phase1_mvp_closeout.md
```

If local mining is needed, write extension artifacts under a separate namespace:

```text
experiments/phase0_headroom/candidate_sources/
  boltons_clean_supply_breal_extension_*.jsonl
experiments/phase0_headroom/certified_tasks/
  boltons_clean_supply_breal_extension_*.jsonl
```

Do not overwrite the existing canonical Boltons release, certified task table,
or hardening overlay. Use an overlay.

## Step 0: Preflight

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, and git status in:

```text
experiments/phase1_compiler/reports/phase1_clean_supply_breal_extension_process.md
```

2. Confirm the current blocker:

```bash
jq -r '.primary_decision_label' \
  experiments/phase1_compiler/results/phase1_retrospective_validation_decision.json

jq -r '.recommended_next_runbook' \
  experiments/phase1_compiler/results/phase1_retrospective_validation_decision.json

jq '.clean_supply_promoted_by_split' \
  experiments/phase1_compiler/results/phase1_retrospective_validation_decision.json
```

Expected:

```text
retrospective_validation_complete_clean_supply_still_blocked
mine_additional_clean_outcome_unseen_supply
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

4. Confirm raw paths are not tracked:

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

5. Write:

```text
experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_preflight.json
```

Include:

```json
{
  "schema_version": "barcarolle.phase1.clean_supply_breal_extension_preflight.v1",
  "paid_acut_calls_allowed": false,
  "direct_paid_llm_calls_allowed": false,
  "starting_decision": "retrospective_validation_complete_clean_supply_still_blocked",
  "required_missing_split": "B_real",
  "minimum_clean_split": {"B_real": 2, "W_real": 2},
  "existing_promoted_clean_supply": {
    "B_real": ["boltons__hist__011"],
    "W_real": ["boltons__hist__022", "boltons__hist__023", "boltons__hist__027"]
  },
  "predictive_validity_established": false
}
```

Acceptance:

- baseline checks pass;
- no paid calls run;
- current blocker and split deficit are recorded;
- raw/workspace/external repo paths are not tracked.

Stop if:

- the retrospective decision is missing;
- tests fail;
- git state contains unrelated uncommitted changes that would make the output
  ambiguous.

Commit:

```text
Record Phase 1 clean supply B_real extension preflight
```

## Step 1: Write Config

Create:

```text
experiments/phase1_compiler/configs/phase1_clean_supply_breal_extension.yaml
```

Use this minimum structure:

```yaml
schema_version: barcarolle.phase1_clean_supply_breal_extension.v1
status: configured
claim_scope: clean_supply_extension_not_predictive_validation
predictive_validity_established: false
paid_acut_calls: disabled
paid_llm_calls: disabled

target:
  repo_id: boltons
  missing_split: B_real
  minimum_clean_split:
    B_real: 2
    W_real: 2
  existing_promoted_clean_supply:
    B_real:
      - boltons__hist__011
    W_real:
      - boltons__hist__022
      - boltons__hist__023
      - boltons__hist__027

primary_candidate:
  task_id: boltons__hist__014
  current_status: manual_review_required
  current_blocker: scope_context_project_heavy_or_ambiguous

candidate_priority:
  deep_review_first:
    - boltons__hist__014
  repair_only_if_non_leaky:
    - boltons__hist__006
    - boltons__hist__013
  mine_extension_if_needed: true

source_artifacts:
  retrospective_decision: experiments/phase1_compiler/results/phase1_retrospective_validation_decision.json
  clean_supply_review: experiments/phase1_compiler/results/phase1_clean_supply_extension_review.json
  hardening_overlay: experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json
  workspace_scorecard: experiments/phase1_compiler/results/phase1_workspace_scorecard.json
  boltons_certified_tasks: experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl
  boltons_task_statements: experiments/phase0_headroom/certified_tasks/boltons_task_statements.jsonl
  boltons_review_records: experiments/phase0_headroom/certified_tasks/boltons_review_records.jsonl
  boltons_release: experiments/phase0_headroom/releases/boltons_phase0_pilot_release.json
  boltons_local_repo: experiments/phase0_headroom/external_repos/boltons

promotion_policy:
  require_outcome_unseen: true
  require_non_leaky_problem_context: true
  require_oracle_alignment: true
  require_scope_clarity: true
  reject_project_or_docs_only: true
  reject_solution_exposure_risk: true
  reject_commit_message_only_source: true

overlay:
  output: experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_overlay.json
  evidence_level: clean_supply_candidate_overlay
```

Acceptance:

- config is local-only;
- config names `boltons__hist__014` as first candidate;
- config forbids predictive-validity claims;
- config uses overlay output rather than mutating canonical releases.

Commit:

```text
Configure Phase 1 clean supply B_real extension
```

## Step 2: Add Clean-Supply Extension Tooling

Add:

```text
experiments/phase1_compiler/tools/phase1_clean_supply_breal_extension.py
experiments/phase1_compiler/tests/test_phase1_clean_supply_breal_extension.py
```

Required commands:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_supply_breal_extension.py \
  audit-candidates \
  --config experiments/phase1_compiler/configs/phase1_clean_supply_breal_extension.yaml

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_supply_breal_extension.py \
  review-014 \
  --config experiments/phase1_compiler/configs/phase1_clean_supply_breal_extension.yaml

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_supply_breal_extension.py \
  build-overlay \
  --config experiments/phase1_compiler/configs/phase1_clean_supply_breal_extension.yaml

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_supply_breal_extension.py \
  decide \
  --config experiments/phase1_compiler/configs/phase1_clean_supply_breal_extension.yaml
```

If `review-014` cannot promote enough supply, add a fifth command:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_supply_breal_extension.py \
  mine-extension \
  --config experiments/phase1_compiler/configs/phase1_clean_supply_breal_extension.yaml
```

Tooling requirements:

1. Load current promoted clean supply from:

```text
experiments/phase1_compiler/results/phase1_clean_supply_extension_review.json
```

2. Load outcome-seen task ids from:

```text
experiments/phase1_compiler/results/phase1_workspace_scorecard.json
experiments/phase0_headroom/results/*_score_table.csv
```

3. Load Boltons task rows, statements, review records, and hardening status.

4. `audit-candidates` writes:

```text
experiments/phase1_compiler/results/phase1_clean_supply_breal_candidate_audit.json
experiments/phase1_compiler/reports/phase1_clean_supply_breal_candidate_audit.md
```

It must show:

```text
current promoted B_real count
current promoted W_real count
candidate B_real rows
outcome_seen status
hardening status
blocker reasons
recommended next action per candidate
```

5. `review-014` writes:

```text
experiments/phase1_compiler/results/phase1_clean_supply_boltons_014_review.json
experiments/phase1_compiler/reports/phase1_clean_supply_boltons_014_review.md
```

It must determine whether `boltons__hist__014` is:

```text
promote_to_clean_benchmark_candidate
keep_manual_review_required
reject_for_clean_holdout
```

6. `build-overlay` writes:

```text
experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_overlay.json
experiments/phase1_compiler/reports/phase1_clean_supply_breal_extension_overlay.md
```

The overlay must include all prior promoted clean tasks plus any newly promoted
task:

```json
{
  "schema_version": "barcarolle.phase1.clean_supply_breal_extension_overlay.v1",
  "evidence_level": "clean_supply_candidate_overlay",
  "repo_id": "boltons",
  "promoted_by_split": {
    "B_real": [],
    "W_real": []
  },
  "clean_supply_ready": false,
  "predictive_validity_established": false
}
```

7. `decide` writes:

```text
experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_decision.json
experiments/phase1_compiler/reports/phase1_clean_supply_breal_extension_decision.md
```

Decision labels:

```text
clean_supply_ready_for_preregistered_validation
clean_supply_breal_extension_still_blocked
clean_supply_needs_extension_mining
```

Unit tests must cover:

- outcome-seen tasks cannot be promoted;
- `boltons__hist__014` can be promoted only if project/config-heavy ambiguity is
  resolved;
- solution-exposure-risk rows are not promoted;
- overlay combines prior promoted supply with new promoted supply;
- clean supply readiness requires at least `2 B_real` and `2 W_real`;
- predictive validity remains false.

Acceptance:

- tests pass;
- tooling produces deterministic JSON and markdown;
- no paid calls run.

Commit:

```text
Add Phase 1 clean supply B_real extension tooling
```

## Step 3: Audit B_real Candidates

Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_supply_breal_extension.py \
  audit-candidates \
  --config experiments/phase1_compiler/configs/phase1_clean_supply_breal_extension.yaml
```

Inspect:

```bash
jq '{current_promoted_by_split, candidate_summary, recommended_path, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_clean_supply_breal_candidate_audit.json
```

Acceptance:

- audit confirms current clean supply is `1 B_real + 3 W_real`;
- `boltons__hist__014` is outcome-unseen;
- all B_real candidates have explicit action labels;
- no task with previous ACUT outcome is recommended for clean promotion.

Commit:

```text
Audit Phase 1 clean supply B_real candidates
```

## Step 4: Deep Review `boltons__hist__014`

Actions:

1. Read sanitized committed metadata:

```bash
jq -r 'select(.task_id=="boltons__hist__014")' \
  experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl

jq -r 'select(.task_id=="boltons__hist__014")' \
  experiments/phase0_headroom/certified_tasks/boltons_task_statements.jsonl

jq -r '.tasks[] | select(.task_id=="boltons__hist__014")' \
  experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json
```

2. If local Boltons repo is present, inspect changed files and diff stats only.
Do not commit raw diffs:

```bash
git -C experiments/phase0_headroom/external_repos/boltons show --stat --oneline <target_commit>
git -C experiments/phase0_headroom/external_repos/boltons diff --name-only <base_commit> <target_commit>
```

3. If GitHub auth is available, fetch sanitized PR metadata only for the allowed
context ref. Do not commit raw responses:

```bash
gh api repos/mahmoud/boltons/pulls/286 \
  --jq '{number,title,body: (.body // "" | .[:500]), labels: [.labels[].name], merged_at, changed_files, additions, deletions}'
```

4. Run the review command:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_supply_breal_extension.py \
  review-014 \
  --config experiments/phase1_compiler/configs/phase1_clean_supply_breal_extension.yaml
```

Promotion rule for `boltons__hist__014`:

- Promote only if the tool/report can narrow the task to the behavior-code
  change in `fileutils/jsonutils`, with docs/config changes treated as
  ancillary and excluded from solver scope.
- Keep manual review if the PR/context is mainly infrastructure, tox/CI,
  project configuration, or ambiguous across unrelated behavior.
- Reject if the only usable statement would leak the solution or require
  project/config changes.

Acceptance:

- review report records exact reason;
- no raw GitHub response is committed;
- `outcome_seen=false`;
- decision is one of the allowed labels;
- if promoted, solver-facing scope excludes project/config/docs changes.

Branch:

- If promoted, continue to Step 6.
- If kept or rejected, continue to Step 5.

Commit:

```text
Review Boltons 014 for clean B_real promotion
```

## Step 5: Mine Additional Clean B_real Supply If Needed

Run this step only if `boltons__hist__014` is not promoted.

Actions:

1. Prefer extending Boltons locally. Do not overwrite canonical files:

```text
experiments/phase0_headroom/candidate_sources/boltons_clean_supply_breal_extension_*.jsonl
experiments/phase0_headroom/certified_tasks/boltons_clean_supply_breal_extension_*.jsonl
```

2. If reusing logic from `repo_history_pilot.py`, copy or wrap it so extension
task ids use a separate namespace, for example:

```text
boltons__breal_ext__001
boltons__breal_ext__002
```

Do not reuse `boltons__hist__NNN` ids for new mined extension rows.

3. Search for candidate anchors that are:

- outcome-unseen;
- earlier than the current W_real promoted tasks if possible;
- code-plus-test changes;
- not project/config/docs-only;
- not solution-leaky by statement;
- locally replayable with no-op fail and reference pass.

4. Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_supply_breal_extension.py \
  mine-extension \
  --config experiments/phase1_compiler/configs/phase1_clean_supply_breal_extension.yaml
```

If this command is not implemented because `boltons__hist__014` promoted, skip
this step.

5. If Boltons cannot produce a B_real candidate, add a local-only backup repo
screen. Recommended order:

```text
attrs
requests
rich
```

Use backup repos only for clean supply. Do not mix them into the current Boltons
strict holdout without a new split plan.

Acceptance:

- extension artifacts do not overwrite canonical Boltons release/certified
  files;
- at least one new candidate is either promoted or the report explains why not;
- all promoted extension tasks are outcome-unseen;
- no paid calls run.

Stop if:

- local mining requires changing the core ACUT harness;
- only solution-leaky or project-heavy tasks are available;
- artifacts would overwrite prior committed candidate/certified files.

Commit:

```text
Mine additional Phase 1 clean B_real supply
```

## Step 6: Build Clean-Supply Overlay

Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_supply_breal_extension.py \
  build-overlay \
  --config experiments/phase1_compiler/configs/phase1_clean_supply_breal_extension.yaml
```

Inspect:

```bash
jq '{repo_id, promoted_by_split, clean_supply_ready, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_overlay.json
```

Acceptance:

- overlay includes prior promoted tasks:

```text
boltons__hist__011
boltons__hist__022
boltons__hist__023
boltons__hist__027
```

- overlay includes any newly promoted B_real task;
- `clean_supply_ready=true` only if promoted supply reaches at least
  `2 B_real + 2 W_real`;
- overlay is clearly labeled as clean-supply candidate evidence, not validation
  evidence;
- predictive validity remains false.

Commit:

```text
Build Phase 1 clean supply B_real overlay
```

## Step 7: Re-run Strict Future-Holdout Supply Design

Run this step only if the overlay has `clean_supply_ready=true`.

Actions:

1. Extend `phase1_future_holdout.py` and its tests if needed so it can read:

```text
experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_overlay.json
```

as an additional benchmark-grade clean-supply source.

2. Re-run:

```bash
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
```

3. Inspect:

```bash
jq '{selected_repos, clean_supply_ready, repo_summary, blockers}' \
  experiments/phase1_compiler/results/phase1_future_holdout_clean_supply.json

jq '{selected_repos, repo_plans, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_future_holdout_cutoff_plan.json

jq '{status, selected_repos, splits, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_future_holdout_preregistration.json
```

Acceptance:

- strict clean supply is ready for Boltons;
- selected tasks are outcome-unseen;
- B_eval and H_future are disjoint;
- cutoff uses repo task time and embargo;
- preregistration is frozen for a later paid validation run;
- no paid cells run in this runbook.

Commit:

```text
Reopen Phase 1 strict future holdout with clean B_real supply
```

## Step 8: Decide

Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_clean_supply_breal_extension.py \
  decide \
  --config experiments/phase1_compiler/configs/phase1_clean_supply_breal_extension.yaml
```

Expected outputs:

```text
experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_decision.json
experiments/phase1_compiler/reports/phase1_clean_supply_breal_extension_decision.md
```

Decision labels:

```text
clean_supply_ready_for_preregistered_validation
clean_supply_breal_extension_still_blocked
clean_supply_needs_extension_mining
```

Decision must include:

```text
candidate decisions
newly promoted B_real tasks
promoted supply by split
strict future-holdout supply status
whether preregistration was refreshed
whether paid calls were made
predictive validity status
next recommended runbook
```

Recommended next runbook:

```text
run_preregistered_clean_future_holdout_paid_validation
```

only if strict preregistration exists and clean supply is ready.

Otherwise:

```text
continue_mining_clean_outcome_unseen_supply
```

Acceptance:

- decision does not claim predictive validity;
- decision does not claim paid holdout validation ran;
- next runbook is concrete;
- no raw artifacts are committed.

Commit:

```text
Summarize Phase 1 clean supply B_real extension
```

## Step 9: Refresh Phase 1 Boundary

Actions:

1. Extend Phase 1 compiler closeout only as needed to import:

```text
experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_decision.json
```

as sidecar evidence.

2. Rebuild and validate:

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

- Phase 1 compiler validation returns `status=valid`;
- closeout labels clean-supply overlay as supply evidence, not validation
  evidence;
- `predictive_validity_established=false`;
- production ranking remains `not_produced`;
- next runbook recommendation matches the Step 8 decision.

Commit:

```text
Refresh Phase 1 boundary after clean supply extension
```

## Step 10: Final Verification

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
- no raw/workspace/external repo/venv/cache paths are tracked;
- final decision JSON and report are committed;
- no paid ACUT cells were run;
- no push is performed.

Final response from the worker should include:

- final decision label;
- whether `boltons__hist__014` was promoted;
- any additional mined B_real task ids;
- final promoted clean supply by split;
- whether strict future-holdout preregistration is ready;
- predictive validity status;
- recommended next runbook.

## Expected Branches

### `boltons__hist__014` Promoted

Expected decision:

```text
clean_supply_ready_for_preregistered_validation
```

Next runbook:

```text
run_preregistered_clean_future_holdout_paid_validation
```

### Extension Mining Finds Another B_real

Expected decision:

```text
clean_supply_ready_for_preregistered_validation
```

Next runbook:

```text
run_preregistered_clean_future_holdout_paid_validation
```

### Still Blocked

Expected decision:

```text
clean_supply_breal_extension_still_blocked
```

Next runbook:

```text
continue_mining_clean_outcome_unseen_supply
```

Do not lower the clean split minimum just to proceed.
