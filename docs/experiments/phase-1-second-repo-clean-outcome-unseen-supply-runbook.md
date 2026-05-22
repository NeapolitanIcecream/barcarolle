# Phase 1 Second-Repo Clean Outcome-Unseen Supply Runbook

Status: implementation runbook, 2026-05-22.

This runbook is for one dedicated Codex CLI session. Its job is to find and
certify clean outcome-unseen task supply for a second target repo, then freeze a
two-repo future-holdout validation design. It must not run second-repo paid
ACUT solving cells.

The current state is:

```text
Boltons clean future-holdout pilot:
  paid cells: 16
  scoreable cells: 16
  policy violations: 0
  predictive_validity_established: false

Remaining blockers:
  predictive_validity_min_target_repos_not_met
  predictive_validity_min_holdout_scoreable_cells_not_met
```

The shortest path to a stronger Phase 1 validation attempt is to add one clean
second repo. `attrs` is the preferred candidate because it was already named as
the backup repo in prior clean-supply configs and has not yet been screened in
this branch. `toolz` may be reconsidered only if it can provide clean
outcome-unseen tasks without reusing previous ACUT outcomes.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-1-second-repo-clean-outcome-unseen-supply-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make a cohesive git commit after every completed step that changes files. Do
not batch unrelated steps into one commit. Do not push unless explicitly asked.

Goal: mine and certify clean outcome-unseen supply for a second target repo,
preferably attrs, then freeze a two-repo future-holdout validation design that
combines the completed Boltons pilot with the second repo. Do not run paid
second-repo ACUT cells in this runbook.

Do not promote outcome-seen, target-commit-seen, solution-leaky,
project-heavy ambiguous, docs-only, config-only, or commit-message-only tasks.
Do not lower clean split minimums. Do not claim predictive validity.

All paid LLM or ACUT calls remain disabled. If a command would make a paid ACUT
task-solving call, stop and write a blocker. Local git mining, local repository
inspection, local certification replay, GitHub metadata lookup if already
authenticated, deterministic reports, tests, and small sanitized manifests are
allowed.

Keep Barcarolle on the benchmark/compiler side of the ACUT boundary. Do not
implement Codex, Kilo, or another ACUT harness. Do not mutate canonical
hardening results or canonical release files to make sidecar tasks look
canonically hardened.

Do not commit secrets, raw GitHub API responses, full raw prompts, raw
completions, raw ACUT transcripts, solver workspaces, verifier workspaces,
cloned external repositories, .venv, caches, or large raw outputs. Commit only
small sanitized configs, manifests, tools, tests, reports, summaries, and
digests. Raw and cloned artifacts must remain under ignored paths.
```

## Claim Boundary

Allowed claims:

```text
second_repo_clean_supply_mining_completed
second_repo_clean_supply_overlay_created
attrs_clean_supply_ready_for_two_repo_preregistration
toolz_clean_supply_ready_for_two_repo_preregistration
two_repo_future_holdout_design_preregistered
second_repo_clean_supply_blocked
insufficient_evidence_for_predictive_validation
```

Disallowed claims:

```text
predictive_validity_established
production_benchmark_ranking
pure_harness_effect
clean_second_repo_validated_without_paid_holdout_run
contamination_proof_evaluation_if_model_snapshot_unknown
validation_grade_humanize_if_commit_fallback_only
promotion_of_solution_leaky_or_project_heavy_tasks
```

## Success Criteria

Minimum success:

```text
second repo selected: attrs or toolz
B_eval clean tasks: >= 2
H_future clean tasks: >= 2
two-repo preregistration: frozen
paid second-repo ACUT calls: false
predictive_validity_established: false
```

Preferred success:

```text
second repo selected: attrs
B_eval clean tasks: >= 4
H_future clean tasks: >= 4
two-repo preregistration: frozen
paid second-repo ACUT calls: false
predictive_validity_established: false
```

Why the minimum is enough:

- Boltons already contributes `8` H_future scoreable cells from the paid pilot.
- A second repo with `2` H_future tasks across `2` adapters would add `4`
  planned holdout cells.
- That reaches the configured `12` holdout-scoreable-cell threshold if the
  later paid two-repo run is scoreable.

## Commit Discipline

The executing agent must commit after every completed step that changes files.
Use one commit per logical unit:

```text
preflight record
second-repo config
local candidate mining
local certification/review
clean supply overlay
two-repo preregistration
closeout decision
```

Before every commit:

```bash
git diff --check
git status --short
```

Use non-interactive git commands:

```bash
git add <paths>
git commit -m "<message>"
```

Do not commit ignored raw paths, cloned repos, workspaces, caches, or secrets.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_second_repo_clean_outcome_unseen_supply.yaml
    phase1_two_repo_future_holdout_validation.yaml
  tools/
    phase1_clean_outcome_unseen_supply_mining.py
    phase1_future_holdout.py
    phase1_compiler.py
  tests/
    test_phase1_clean_outcome_unseen_supply_mining.py
    test_phase1_future_holdout.py
    test_phase1_compiler.py
  results/
    phase1_second_repo_clean_supply_preflight.json
    phase1_second_repo_clean_supply_candidate_inventory.json
    phase1_second_repo_clean_supply_review.json
    phase1_second_repo_clean_supply_overlay.json
    phase1_two_repo_future_holdout_clean_supply.json
    phase1_two_repo_future_holdout_preregistration.json
    phase1_second_repo_clean_supply_decision.json
    phase1_mvp_closeout.json
  reports/
    phase1_second_repo_clean_supply_process.md
    phase1_second_repo_clean_supply_candidate_inventory.md
    phase1_second_repo_clean_supply_review.md
    phase1_second_repo_clean_supply_overlay.md
    phase1_two_repo_future_holdout_preregistration.md
    phase1_second_repo_clean_supply_decision.md
    phase1_mvp_closeout.md
```

If new local mining artifacts are needed, write them under repo-specific names:

```text
experiments/phase0_headroom/candidate_sources/
  attrs_clean_outcome_unseen_supply_*.jsonl
  toolz_clean_outcome_unseen_supply_*.jsonl
experiments/phase0_headroom/certified_tasks/
  attrs_clean_outcome_unseen_supply_*.jsonl
  toolz_clean_outcome_unseen_supply_*.jsonl
```

Raw or large artifacts must stay ignored:

```text
experiments/phase0_headroom/external_repos/
experiments/phase0_headroom/workspaces/
experiments/phase0_headroom/results/raw/
```

Do not overwrite:

```text
experiments/phase0_headroom/releases/boltons_phase0_pilot_release.json
experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl
experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json
experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_overlay.json
```

## Step 0: Preflight

Actions:

1. Record branch, HEAD, current date, Python version, and `uv --version`.
2. Confirm worktree state:

```bash
git status --short --branch
git log --oneline -10
git diff --check
```

3. Confirm Boltons pilot result:

```bash
jq '{primary_decision_label, selected_repos, b_eval_scoreable_cells, h_future_scoreable_cells, policy_violation_count, predictive_validity_established, blockers, recommended_next_runbook}' \
  experiments/phase1_compiler/results/phase1_future_holdout_decision.json
```

4. Confirm current closeout recommendation:

```bash
jq '{future_holdout_sidecar_evidence, clean_future_holdout_scale_up_decision, next_runbook_recommendation, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_mvp_closeout.json
```

5. Run baseline checks:

```bash
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

6. Write:

```text
experiments/phase1_compiler/results/phase1_second_repo_clean_supply_preflight.json
experiments/phase1_compiler/reports/phase1_second_repo_clean_supply_process.md
```

Acceptance:

- Boltons decision is `boltons_clean_future_holdout_pilot_complete_insufficient_sample`;
- Boltons has `8` B_eval scoreable cells and `8` H_future scoreable cells;
- policy violations are `0`;
- `predictive_validity_established` is `false`;
- current recommendation is `mine_second_repo_clean_outcome_unseen_supply_for_two_repo_validation`;
- tests and validation pass.

Stop if:

- Boltons paid pilot artifacts are missing or inconsistent;
- the worktree has conflicting uncommitted changes;
- baseline validation fails.

Commit:

```text
Record second repo clean supply preflight
```

## Step 1: Configure Second-Repo Mining

Actions:

1. Create:

```text
experiments/phase1_compiler/configs/phase1_second_repo_clean_outcome_unseen_supply.yaml
```

2. Include:

```text
primary_candidate_repo: attrs
fallback_candidate_repos:
  - toolz

minimum_clean_split:
  B_eval: 2
  H_future: 2

preferred_clean_split:
  B_eval: 4
  H_future: 4

paid_acut_calls: disabled
paid_llm_calls: disabled

prior_boltons_future_holdout_decision:
  experiments/phase1_compiler/results/phase1_future_holdout_decision.json

prior_boltons_clean_overlay:
  experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_overlay.json
```

3. Define source paths for `attrs`:

```text
repo_url: https://github.com/python-attrs/attrs.git
local_repo: experiments/phase0_headroom/external_repos/attrs
candidate_source_prefix: attrs_clean_outcome_unseen_supply
```

4. Define promotion policy:

```text
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
```

Acceptance:

- config names `attrs` as first candidate;
- fallback repos are explicit;
- paid calls are disabled;
- promotion rules do not weaken earlier clean-supply rules;
- output paths are separate from Boltons canonical artifacts.

Stop if:

- config would require paid calls;
- config would reuse existing ACUT outcomes as clean validation rows;
- config would mutate canonical Boltons artifacts.

Commit:

```text
Configure second repo clean supply mining
```

## Step 2: Prepare Local Repo And Candidate Anchors

Actions:

1. Confirm ignored clone path:

```bash
git check-ignore -v experiments/phase0_headroom/external_repos/attrs || true
```

2. Clone or fetch `attrs` into the ignored external repo path:

```bash
mkdir -p experiments/phase0_headroom/external_repos
test -d experiments/phase0_headroom/external_repos/attrs/.git || \
  git clone https://github.com/python-attrs/attrs.git \
    experiments/phase0_headroom/external_repos/attrs
git -C experiments/phase0_headroom/external_repos/attrs fetch --all --tags --prune
```

3. Mine up to `1000` local history anchors. Prefer commits linked to public
   issues or PRs with non-leaky problem context.
4. Write sanitized candidate-source files:

```text
experiments/phase0_headroom/candidate_sources/attrs_clean_outcome_unseen_supply_candidates.jsonl
experiments/phase0_headroom/candidate_sources/attrs_clean_outcome_unseen_supply_source_context.jsonl
```

Do not commit raw GitHub API responses.

Acceptance:

- local clone exists only under ignored external repo path;
- candidate file exists and is small enough to review;
- source context file contains sanitized summaries, not raw API payloads;
- candidate inventory records total anchors scanned and first filter counts.

Stop if:

- `attrs` cannot be cloned or fetched;
- there are fewer than `8` plausible behavior-change anchors;
- source context is mostly commit-message-only;
- raw API data would need to be committed.

Commit:

```text
Mine attrs clean outcome-unseen candidates
```

## Step 3: Certify And Review Candidates

Actions:

1. Run local certification for a bounded batch:

```text
attrs local certification attempts: up to 48 candidates
```

2. For each candidate, record gate outcomes:
   - checkout;
   - oracle extractable;
   - no-op fail;
   - reference pass;
   - known-bad fail;
   - flakiness check;
   - ambiguity review;
   - solution leakage review;
   - scope clarity review;
   - cost boundedness;
   - taxonomy labelability.
3. Reject candidates that are:
   - previous ACUT outcome-seen;
   - target-commit-seen in local score tables;
   - solution-leaky;
   - project-heavy ambiguous;
   - docs-only or config-only;
   - commit-message-only.
4. Write:

```text
experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_review_records.jsonl
experiments/phase1_compiler/results/phase1_second_repo_clean_supply_candidate_inventory.json
experiments/phase1_compiler/results/phase1_second_repo_clean_supply_review.json
experiments/phase1_compiler/reports/phase1_second_repo_clean_supply_candidate_inventory.md
experiments/phase1_compiler/reports/phase1_second_repo_clean_supply_review.md
```

Acceptance:

- promoted tasks have all required clean gates passing;
- promoted tasks have non-leaky public problem context;
- promoted tasks are outcome-unseen and target-commit-unseen;
- review report lists every rejected candidate and blocker;
- no paid ACUT calls were made.

Stop if:

- fewer than `2` clean B_eval and `2` clean H_future tasks can be promoted;
- all plausible tasks are source-leaky or project-heavy;
- local verification is flaky and cannot be bounded;
- certification would require exposing hidden oracle material to a solver
  workspace.

Commit:

```text
Review attrs clean outcome-unseen candidates
```

## Step 4: Build Second-Repo Clean Supply Overlay

Actions:

1. Build:

```text
experiments/phase1_compiler/results/phase1_second_repo_clean_supply_overlay.json
experiments/phase1_compiler/reports/phase1_second_repo_clean_supply_overlay.md
```

2. The overlay must record:
   - `evidence_level: clean_supply_overlay_sidecar`;
   - selected repo id;
   - promoted task ids;
   - selected B_eval and H_future task ids;
   - original local certification status;
   - promotion rationale;
   - source context refs;
   - target commits;
   - task times;
   - `predictive_validity_established: false`;
   - `paid_acut_calls_made: false`.
3. Check cutoff feasibility:
   - `T_compile_end`;
   - `T_holdout_start`;
   - embargo gap at least `14` days;
   - no overlap between B_eval and H_future;
   - H_future later than B_eval by repo task time.

Acceptance:

- overlay includes at least `2` B_eval and `2` H_future clean tasks;
- preferred path includes `4` and `4` if supply allows;
- provenance is sidecar, not canonical hardening;
- canonical release and hardening outputs are unchanged;
- predictive validity remains false.

Stop if:

- cutoff feasibility fails;
- only historical count thresholds pass but chronological future-holdout split
  fails;
- overlay would hide original rejection or diagnostic status.

Commit:

```text
Build second repo clean supply overlay
```

## Step 5: Freeze Two-Repo Future-Holdout Design

Actions:

1. Create:

```text
experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml
```

2. The two-repo design must include:

```text
repos:
  - boltons
  - attrs  # or toolz if attrs is blocked and toolz qualifies

existing_paid_evidence:
  boltons:
    b_eval_prefix: phase1_future_holdout_b_eval
    h_future_prefix: phase1_future_holdout_h_future

second_repo_planned_paid_prefixes:
  b_eval: phase1_two_repo_future_holdout_<repo_id>_b_eval
  h_future: phase1_two_repo_future_holdout_<repo_id>_h_future

acceptance:
  min_target_repos: 2
  min_holdout_scoreable_cells: 12
  policy_violations_max: 0
  non_scoreable_cells_max_per_split: 2
```

3. Run or extend `phase1_future_holdout.py` so it can read both:
   - Boltons paid sidecar evidence;
   - second-repo clean-supply overlay.
4. Write:

```text
experiments/phase1_compiler/results/phase1_two_repo_future_holdout_clean_supply.json
experiments/phase1_compiler/results/phase1_two_repo_future_holdout_preregistration.json
experiments/phase1_compiler/reports/phase1_two_repo_future_holdout_preregistration.md
```

Acceptance:

- selected repos include `boltons` and one clean second repo;
- Boltons paid evidence is imported as already-run sidecar evidence;
- second-repo cells are planned but not run;
- total planned H_future scoreable capacity reaches at least `12` cells if the
  second-repo paid run is scoreable;
- status is `frozen`;
- predictive validity remains false.

Stop if:

- only one repo can be selected;
- second-repo clean supply is below minimum;
- design would require tuning on holdout tasks;
- design would mix outcome-seen rows into clean validation.

Commit:

```text
Freeze two repo future holdout design
```

## Step 6: Decision And MVP Closeout Import

Actions:

1. Write:

```text
experiments/phase1_compiler/results/phase1_second_repo_clean_supply_decision.json
experiments/phase1_compiler/reports/phase1_second_repo_clean_supply_decision.md
```

2. Use one of these decision labels:

```text
attrs_clean_supply_ready_for_two_repo_preregistration
toolz_clean_supply_ready_for_two_repo_preregistration
two_repo_future_holdout_design_frozen_ready_for_paid_validation
second_repo_clean_supply_blocked
```

3. Rebuild MVP closeout:

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

4. Update closeout recommendation:

If successful:

```text
run_two_repo_preregistered_clean_future_holdout_paid_validation
```

If blocked:

```text
expand_clean_supply_sources_or_add_manual_canaries
```

Acceptance:

- decision file clearly states selected repo or blocker;
- if successful, two-repo preregistration is frozen;
- if blocked, blocker report says whether the problem is supply, source
  context, oracle, flakiness, ambiguity, or chronology;
- `predictive_validity_established` is false;
- no paid second-repo cells ran.

Stop if:

- closeout import would overstate validation evidence;
- decision tries to claim predictive validity before the two-repo paid run.

Commit:

```text
Decide second repo clean supply readiness
```

## Step 7: Final Validation And Hygiene

Actions:

1. Run:

```bash
git diff --check
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

2. Confirm no raw or ignored paths are staged:

```bash
git status --short
git diff --cached --name-only
git check-ignore -q experiments/phase0_headroom/external_repos/attrs || true
git check-ignore -q experiments/phase0_headroom/workspaces || true
git check-ignore -q experiments/phase0_headroom/results/raw || true
```

3. Add final process-report summary:
   - commits made by step;
   - candidate counts;
   - promoted task counts;
   - selected B_eval and H_future tasks;
   - blockers if any;
   - final next runbook;
   - confirmation that no paid second-repo ACUT calls ran.

Acceptance:

- final validation passes;
- working tree is clean after final commit;
- every changed step has a commit;
- no raw artifacts are committed;
- final report is understandable without reading raw logs.

Commit:

```text
Close second repo clean supply run
```

## Expected Outcomes

Successful outcome:

```text
primary_decision_label: two_repo_future_holdout_design_frozen_ready_for_paid_validation
selected_repos:
  - boltons
  - attrs
paid_second_repo_acut_calls_made: false
predictive_validity_established: false
recommended_next_runbook: run_two_repo_preregistered_clean_future_holdout_paid_validation
```

Blocked outcome:

```text
primary_decision_label: second_repo_clean_supply_blocked
selected_repos:
  - boltons
blockers:
  - insufficient_clean_outcome_unseen_supply
  - source_context_leaky_or_commit_message_only
  - local_certification_failed
  - chronological_cutoff_infeasible
paid_second_repo_acut_calls_made: false
predictive_validity_established: false
recommended_next_runbook: expand_clean_supply_sources_or_add_manual_canaries
```

