# Phase 1 Preregistered Clean Future-Holdout Paid Validation Runbook

Status: implementation runbook, 2026-05-22.

This runbook is for one dedicated Codex CLI session. Its job is to execute the
already frozen clean future-holdout design, import the paid results, and leave
Phase 1 with either a bounded clean future-holdout pilot result or a precise
blocker for predictive-validation scale-up.

The current frozen design is Boltons-only:

```text
B_eval:
  boltons__clean_ext__001
  boltons__clean_ext__008
  boltons__clean_ext__010
  boltons__hist__011

H_future:
  boltons__clean_ext__017
  boltons__hist__022
  boltons__hist__023
  boltons__hist__027
```

This runbook may make paid ACUT task-solving calls only after the local entry
gates pass. Every paid LLM or ACUT call must use:

```text
LLM_BASE_URL
LLM_API_KEY
```

If either variable is missing in the worker shell, source `~/.zshrc` and check
again before any paid call. Do not use local Codex/ChatGPT subscription auth,
`OPENAI_API_KEY`, OpenRouter variables, or provider-specific fallbacks.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-1-preregistered-clean-future-holdout-paid-validation-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make a cohesive git commit after every completed step that changes files. Do
not batch unrelated steps into one commit. If a step only records state, commit
the small sanitized report/result update for that step. Do not push unless the
user explicitly asks.

The frozen clean future-holdout design is in:
experiments/phase1_compiler/results/phase1_future_holdout_preregistration.json

Run paid ACUT cells only after the entry gates pass. Every paid call must use
LLM_BASE_URL plus LLM_API_KEY. If either variable is missing, source ~/.zshrc
and check again. Do not use local Codex/ChatGPT subscription auth, OPENAI_API_KEY,
OpenRouter variables, or provider-specific fallback variables.

Keep Barcarolle on the benchmark/compiler side of the ACUT boundary. Do not
implement Codex, Kilo, or another ACUT harness. Barcarolle may prepare solver
workspaces, invoke the configured ACUT harnesses, capture git diffs, replay the
diff in a fresh verifier workspace, inject private oracle material only in the
verifier workspace, and record sanitized results.

The current clean supply is sidecar evidence. Do not silently mutate canonical
hardening results or canonical Boltons release files to make clean_ext tasks
look canonically hardened. If workspace ACUT tooling needs clean_ext tasks,
load them from the explicit clean-supply overlay and certified sidecar records,
and preserve the evidence_level=clean_supply_overlay_sidecar provenance.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts,
solver workspaces, verifier workspaces, cloned external repositories, .venv,
caches, raw GitHub API responses, or large raw outputs. Commit only small
sanitized configs, manifests, tools, tests, score tables, cost summaries,
reports, and decision files. Raw harness outputs must remain under ignored paths.

Run paid cells sequentially. Import or summarize usage after every paid batch.
Stop before the next paid batch if scoreability, policy, endpoint, or cost
accounting is blocked.
```

## Claim Boundary

Allowed claims:

```text
preregistered_clean_future_holdout_paid_validation_run
boltons_clean_future_holdout_pilot_complete
workspace_acut_future_holdout_cells_scoreable
same_endpoint_model_different_cli_harnesses
observed_or_conservative_cost_accounting
insufficient_evidence_for_predictive_validation
ready_for_second_repo_clean_supply_scaleup
second_repo_clean_supply_blocked
ready_for_phase1_predictive_validation_scaleup
```

Disallowed claims:

```text
predictive_validity_established_without_acceptance_thresholds
production_benchmark_ranking
pure_harness_effect
contamination_proof_evaluation_if_model_snapshot_unknown
clean_future_holdout_validated_without_paid_holdout_run
validation_grade_humanize_if_commit_fallback_only
promotion_of_solution_leaky_or_project_heavy_tasks
```

Important interpretation:

- `verified_pass` and `verified_fail` are scoreable ACUT outcomes.
- `policy_violation`, `invalid_output`, `acut_harness_error`,
  `harness_error`, and `timeout` are non-scoreable or boundary failures.
- A Boltons-only paid run can establish an executable clean future-holdout pilot.
  It does not establish the stronger Phase 1 predictive-validity claim because
  the frozen acceptance threshold requires at least `2` target repos and at
  least `12` holdout scoreable cells.
- If only Boltons is run, the final decision must keep
  `predictive_validity_established=false`.

## Commit Discipline

The executing agent must commit after every completed step that changes files.
Each commit should contain one logical unit:

```text
preflight record
tooling support
local dry-run artifacts
paid B_eval batch
paid H_future batch
metrics and decision import
optional second-repo supply work
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

Do not commit ignored raw directories, workspaces, cloned repos, caches, or
secrets. If a step has no file changes, record that in the process report of
the next step; do not create an empty commit unless the user explicitly asks.

## Current Entry Evidence

The expected starting point is:

```text
experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_decision.json
  primary_decision_label: boltons_clean_supply_ready_for_preregistered_validation
  clean_supply_ready: true
  predictive_validity_established: false

experiments/phase1_compiler/results/phase1_future_holdout_preregistration.json
  status: frozen
  selected_repos: [boltons]
  B_eval task count: 4
  H_future task count: 4

experiments/phase1_compiler/results/phase1_future_holdout_decision.json
  primary_decision_label: future_holdout_design_frozen_ready_for_paid_validation
  b_eval_scoreable_cells: 0
  h_future_scoreable_cells: 0
  paid_acut_calls_made: false
```

The configured acceptance thresholds are:

```text
policy_violations_max: 0
usage_observed_rate_min: 0.85
non_scoreable_cells_max_per_split: 2
predictive_validity_claim_min_repos: 2
predictive_validity_claim_min_holdout_scoreable_cells: 12
```

## Output Layout

Add or update these Phase 1 files:

```text
experiments/phase1_compiler/
  configs/
    phase1_preregistered_clean_future_holdout_paid_validation.yaml
  results/
    phase1_preregistered_clean_future_holdout_preflight.json
    phase1_preregistered_clean_future_holdout_tooling_check.json
    phase1_future_holdout_prediction_metrics.json
    phase1_future_holdout_decision.json
    phase1_mvp_closeout.json
  reports/
    phase1_preregistered_clean_future_holdout_process.md
    phase1_preregistered_clean_future_holdout_preflight.md
    phase1_preregistered_clean_future_holdout_tooling_check.md
    phase1_future_holdout_prediction_metrics.md
    phase1_future_holdout_decision.md
    phase1_mvp_closeout.md
```

Add or update these Phase 0 workspace ACUT artifacts:

```text
experiments/phase0_headroom/
  configs/
    phase1_preregistered_clean_future_holdout_workspace_matrix.yaml
  results/
    phase1_future_holdout_b_eval_*.json*
    phase1_future_holdout_b_eval_score_table.csv
    phase1_future_holdout_h_future_*.json*
    phase1_future_holdout_h_future_score_table.csv
    workspace_usage_ledger.jsonl
    workspace_cost_reconciliation.json
  reports/
    phase1_future_holdout_b_eval_codex_preflight_preflight.md
    phase1_future_holdout_b_eval_kilo_preflight_preflight.md
    phase1_future_holdout_h_future_codex_preflight_preflight.md
    phase1_future_holdout_h_future_kilo_preflight_preflight.md
    workspace_cost_usage_report.md
```

Raw outputs must stay under ignored paths:

```text
experiments/phase0_headroom/results/raw/
experiments/phase0_headroom/workspaces/
experiments/phase0_headroom/external_repos/
```

Do not overwrite canonical release or hardening files:

```text
experiments/phase0_headroom/releases/boltons_phase0_pilot_release.json
experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl
experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json
```

## Step 0: Preflight And State Record

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`,
   `codex --version` if available, and `kilo --version` if available.
2. Confirm the worktree starts clean or record unrelated existing changes:

```bash
git status --short --branch
git log --oneline -8
git diff --check
```

3. Confirm endpoint variables without printing secret values:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

4. Confirm the frozen design:

```bash
jq '{primary_decision_label, clean_supply_ready, recommended_next_runbook, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_decision.json

jq '{status, selected_repos, splits, claim_thresholds, budget, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_future_holdout_preregistration.json

jq '{primary_decision_label, paid_acut_calls_made, b_eval_scoreable_cells, h_future_scoreable_cells, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_future_holdout_decision.json
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
experiments/phase1_compiler/results/phase1_preregistered_clean_future_holdout_preflight.json
experiments/phase1_compiler/reports/phase1_preregistered_clean_future_holdout_preflight.md
experiments/phase1_compiler/reports/phase1_preregistered_clean_future_holdout_process.md
```

Acceptance:

- clean supply decision is `boltons_clean_supply_ready_for_preregistered_validation`;
- preregistration status is `frozen`;
- selected repo is exactly `boltons`;
- paid ACUT calls for the future-holdout prefixes have not run yet;
- endpoint variables are present before any paid work;
- Phase 1 tests pass;
- Phase 1 compiler validation returns `status=valid`;
- `predictive_validity_established` remains `false`.

Stop if:

- the preregistration is missing or not frozen;
- endpoint variables are missing after sourcing `~/.zshrc`;
- baseline tests or validation fail for reasons unrelated to the current runbook;
- existing uncommitted changes conflict with this runbook.

Commit:

```text
Record preregistered clean future holdout preflight
```

## Step 1: Add Clean-Overlay Workspace Task Loading

Current tooling can load canonical Phase 0 release tasks, but the frozen split
contains `boltons__clean_ext__001`, `boltons__clean_ext__008`,
`boltons__clean_ext__010`, and `boltons__clean_ext__017`. These are sidecar
clean-supply tasks, not canonical Boltons release tasks. The paid runner must
load them without mutating the canonical release or hardening overlay.

Actions:

1. Add a small config for this run:

```text
experiments/phase1_compiler/configs/phase1_preregistered_clean_future_holdout_paid_validation.yaml
experiments/phase0_headroom/configs/phase1_preregistered_clean_future_holdout_workspace_matrix.yaml
```

The config must name:

```text
clean_supply_overlay:
  experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_overlay.json

clean_ext_certified_tasks:
  experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_certified_tasks.jsonl

canonical_boltons_certified_tasks:
  experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl

canonical_boltons_release:
  experiments/phase0_headroom/releases/boltons_phase0_pilot_release.json

result_prefixes:
  b_eval: phase1_future_holdout_b_eval
  h_future: phase1_future_holdout_h_future
```

2. Extend workspace ACUT package loading so it can construct `TaskPackage`
   rows for clean-overlay tasks. Preserve these fields in the package or
   associated metadata:
   - `task_id`;
   - `repo_id`;
   - `split`;
   - `base_commit`;
   - `target_commit`;
   - `task_time`;
   - `test_files`;
   - `changed_files`;
   - `sanitized_context`;
   - `evidence_level=clean_supply_overlay_sidecar`;
   - original hardening status and promotion rationale.
3. Build the solver-visible statement only from non-leaky `sanitized_context`,
   allowed context refs, changed code-file scope, and test command metadata.
   Do not read or summarize the solution patch for the statement.
4. Add or update focused tests. At minimum, test that:
   - clean-overlay task ids can be selected by `--task-id`;
   - canonical release files are not rewritten;
   - the statement for a clean-ext task contains public problem context but no
     target diff;
   - B_eval and H_future prefixes keep separate score tables;
   - provenance is recorded as sidecar evidence.

Suggested validation commands:

```bash
uv run --project experiments/phase0_headroom pytest -q \
  experiments/phase0_headroom/tools/test_workspace_acut_run.py

uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_future_holdout.py
```

Write:

```text
experiments/phase1_compiler/results/phase1_preregistered_clean_future_holdout_tooling_check.json
experiments/phase1_compiler/reports/phase1_preregistered_clean_future_holdout_tooling_check.md
```

Acceptance:

- clean-ext task ids can be selected by the workspace runner;
- canonical Boltons release and hardening overlay are unchanged;
- tests cover the sidecar loader and pass;
- process report records the exact files changed;
- no paid ACUT task-solving cell has run in this step.

Stop if:

- clean-ext tasks cannot be represented without reading solution patches;
- supporting them requires changing ACUT harness behavior;
- hidden oracle material would be exposed in solver workspaces;
- canonical release mutation appears necessary.

Commit:

```text
Support clean overlay tasks in workspace ACUT runner
```

## Step 2: Local Dry-Run And Paid Entry Gate

Actions:

1. Run workspace ACUT preflight for both adapters and both result prefixes:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_preregistered_clean_future_holdout_workspace_matrix.yaml \
  --result-prefix phase1_future_holdout_b_eval_codex_preflight

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_preregistered_clean_future_holdout_workspace_matrix.yaml \
  --result-prefix phase1_future_holdout_b_eval_kilo_preflight

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_preregistered_clean_future_holdout_workspace_matrix.yaml \
  --result-prefix phase1_future_holdout_h_future_codex_preflight

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_preregistered_clean_future_holdout_workspace_matrix.yaml \
  --result-prefix phase1_future_holdout_h_future_kilo_preflight
```

2. Run local package-selection checks without paid ACUT solving. If the runner
   does not have a dry-run mode, add a small non-paid inspection command or test
   that verifies the selected task ids and statement paths.
3. Summarize existing future-holdout prefixes if any files already exist:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  summarize \
  --result-prefix phase1_future_holdout_b_eval

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  summarize \
  --result-prefix phase1_future_holdout_h_future
```

4. Record projected cost before paid work:

```text
preferred batch:
  4 B_eval tasks * 2 adapters = 8 cells
  4 H_future tasks * 2 adapters = 8 cells
  total = 16 cells
  conservative incremental estimate = USD 8.00
```

Acceptance:

- every preflight status is `ready`;
- endpoint proof status is acceptable for both adapters;
- required endpoint env is present;
- selected task ids match the frozen preregistration exactly;
- no future-holdout score table contains previous paid rows unless they are
  explicitly from this runbook and already committed by an earlier step;
- projected incremental spend is below `USD 20`;
- observed-or-conservative cumulative spend is below `USD 80`;
- paid parallelism remains disabled.

Stop if:

- any preflight is not `ready`;
- selected task ids do not match the frozen preregistration;
- usage/cost cannot be bounded;
- any existing future-holdout rows indicate the split was already run outside
  this runbook.

Commit:

```text
Record clean future holdout paid entry gate
```

## Step 3: Run The Paid B_eval Batch

Actions:

1. Run Codex and Kilo sequentially on the frozen B_eval task ids:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_preregistered_clean_future_holdout_workspace_matrix.yaml \
  --result-prefix phase1_future_holdout_b_eval \
  --task-id boltons__clean_ext__001 \
  --task-id boltons__clean_ext__008 \
  --task-id boltons__clean_ext__010 \
  --task-id boltons__hist__011

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_preregistered_clean_future_holdout_workspace_matrix.yaml \
  --result-prefix phase1_future_holdout_b_eval \
  --task-id boltons__clean_ext__001 \
  --task-id boltons__clean_ext__008 \
  --task-id boltons__clean_ext__010 \
  --task-id boltons__hist__011
```

2. Import usage or refresh conservative usage accounting for the B_eval prefix:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_usage_import.py \
  --root . \
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --result-prefix phase1_future_holdout_b_eval
```

3. Summarize the prefix:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  summarize \
  --result-prefix phase1_future_holdout_b_eval
```

4. Update the process report with:
   - scheduled cells;
   - terminal status counts;
   - scoreable cell count;
   - policy violation count;
   - observed-or-conservative incremental cost;
   - usage observed rate;
   - whether H_future may proceed.

Acceptance:

- all `8` B_eval cells have terminal status;
- at least `6/8` B_eval cells are scoreable;
- non-scoreable B_eval cells are at most `2`;
- policy violations are `0`;
- no solver workspace contains hidden oracle files;
- usage observed rate remains at least `0.85`, or conservative fallback is
  explicitly recorded and the projected run stays under the hard caps;
- observed-or-conservative incremental cost remains below `USD 20`.

Stop if:

- fewer than `6/8` B_eval cells are scoreable;
- any policy violation occurs;
- hidden oracle leakage is detected;
- endpoint proof or required env becomes invalid;
- usage/cost cannot be bounded.

Commit:

```text
Run clean future holdout B_eval batch
```

## Step 4: Run The Paid H_future Batch

Actions:

1. Run Codex and Kilo sequentially on the frozen H_future task ids:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_preregistered_clean_future_holdout_workspace_matrix.yaml \
  --result-prefix phase1_future_holdout_h_future \
  --task-id boltons__clean_ext__017 \
  --task-id boltons__hist__022 \
  --task-id boltons__hist__023 \
  --task-id boltons__hist__027

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_preregistered_clean_future_holdout_workspace_matrix.yaml \
  --result-prefix phase1_future_holdout_h_future \
  --task-id boltons__clean_ext__017 \
  --task-id boltons__hist__022 \
  --task-id boltons__hist__023 \
  --task-id boltons__hist__027
```

2. Import usage or refresh conservative usage accounting for the H_future
   prefix:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_usage_import.py \
  --root . \
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --result-prefix phase1_future_holdout_h_future
```

3. Summarize the prefix:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  summarize \
  --result-prefix phase1_future_holdout_h_future
```

4. Re-import or reconcile cumulative workspace usage across all canonical
   prefixes used by Phase 1, including:

```text
codex_kilo_workspace
codex_kilo_workspace_followup_smoke
codex_kilo_workspace_followup
kilo_completion_probe
codex_kilo_workspace_stability
humanize_pre_phase1_workspace
phase1_validation_humanize_holdout_smoke
phase1_validation_humanize_holdout
phase1_validation_humanize_holdout_stability
phase1_validation_boltons_paid_smoke
phase1_validation_boltons_paid_extension
phase1_future_holdout_b_eval
phase1_future_holdout_h_future
```

Acceptance:

- all `8` H_future cells have terminal status;
- at least `6/8` H_future cells are scoreable;
- non-scoreable H_future cells are at most `2`;
- policy violations are `0`;
- no solver workspace contains hidden oracle files;
- usage observed rate remains at least `0.85`, or conservative fallback is
  explicitly recorded and the run stays under the hard caps;
- cumulative observed-or-conservative spend remains below `USD 80`.

Stop if:

- fewer than `6/8` H_future cells are scoreable;
- any policy violation occurs;
- hidden oracle leakage is detected;
- usage/cost cannot be bounded.

Commit:

```text
Run clean future holdout H_future batch
```

## Step 5: Compute Metrics And Decision

Actions:

1. Run future-holdout scoring:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_future_holdout.py \
  score \
  --config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml
```

2. Inspect:

```bash
jq '{status, b_eval, h_future, absolute_error_per_adapter, mae, policy_violation_count, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_future_holdout_prediction_metrics.json

jq '{primary_decision_label, selected_repos, b_eval_scoreable_cells, h_future_scoreable_cells, policy_violation_count, predictive_validity_established, recommended_next_runbook}' \
  experiments/phase1_compiler/results/phase1_future_holdout_decision.json
```

3. Rebuild and validate the Phase 1 MVP closeout so the new future-holdout
   evidence is imported as sidecar evidence:

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

4. Run tests:

```bash
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
git diff --check
```

Acceptance:

- prediction metrics are computed from the B_eval and H_future score tables;
- decision file records paid ACUT calls made;
- policy violation count is `0`;
- `predictive_validity_established` remains `false` unless all pre-registered
  acceptance thresholds are met;
- if only Boltons was run, the decision label must not claim Phase 1 predictive
  validity;
- Phase 1 MVP validation returns `status=valid`;
- scoped tests pass.

Decision labels:

Use `boltons_clean_future_holdout_pilot_complete_insufficient_sample` if:

- Boltons B_eval and H_future are scoreable enough for a pilot;
- policy violations are `0`;
- the run has only one target repo or fewer than `12` holdout scoreable cells.

Use `future_holdout_validation_blocked_non_scoreable_cells` if:

- paid cells ran but scoreability falls below the acceptance gate.

Use `future_holdout_validation_blocked_policy_or_cost` if:

- policy violations occur or cost cannot be bounded.

Use `ready_for_phase1_predictive_validation_scaleup` only if:

- at least `2` target repos are included;
- at least `12` H_future cells are scoreable;
- policy violations are `0`;
- the metrics beat the pre-registered baseline threshold.

Commit:

```text
Compute clean future holdout metrics and decision
```

## Step 6: Decide Whether To Scale To A Second Repo

This step is mandatory as an analysis and decision step. It may be local-only.
Do not run new paid second-repo cells until clean supply is frozen and a second
repo preregistration is written.

Actions:

1. Inspect the final Boltons decision and acceptance thresholds.
2. If the goal is only to complete the preregistered Boltons pilot, write a
   precise closeout that says:

```text
Boltons clean future-holdout pilot complete.
Predictive validity remains unestablished because the acceptance threshold
requires at least two target repos and at least 12 holdout scoreable cells.
```

3. If the goal is a stronger Phase 1 predictive-validity claim, continue with
   second-repo clean supply work. Prefer `attrs` as the backup repo already
   named by the clean-supply mining config. `toolz` can be reconsidered only if
   clean outcome-unseen tasks can be found without reusing previous ACUT
   outcomes.
4. For second-repo supply, write a new runbook or extend a follow-up runbook
   before paid work. It must include:
   - local candidate mining;
   - non-leaky problem-context review;
   - local certification;
   - clean overlay sidecar;
   - frozen repo-time cutoff;
   - B_eval and H_future split;
   - paid entry gates;
   - claim thresholds.

Acceptance:

- final closeout explicitly states whether the next path is stop, mine second
  repo supply, or run a separately preregistered two-repo validation;
- no second-repo paid work runs without a frozen second-repo design;
- all claims stay within the claim boundary.

Commit:

```text
Record clean future holdout scale-up decision
```

## Step 7: Final Repository Hygiene

Actions:

1. Confirm no raw artifacts are staged:

```bash
git status --short
git diff --cached --name-only
```

2. Confirm ignored raw paths remain ignored:

```bash
git check-ignore -q experiments/phase0_headroom/results/raw || true
git check-ignore -q experiments/phase0_headroom/workspaces || true
git check-ignore -q experiments/phase0_headroom/external_repos || true
```

3. Run final validation:

```bash
git diff --check
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

4. Write the final process-report summary with:
   - commits made by step;
   - paid cell counts by prefix;
   - scoreable counts by prefix;
   - policy violation count;
   - observed-or-conservative spend;
   - final decision label;
   - next recommended runbook.

Acceptance:

- working tree is clean after the final commit;
- every step with file changes has a corresponding commit;
- no raw workspaces, raw transcripts, caches, or secrets are committed;
- final validation passes;
- final report does not claim predictive validity unless the configured
  thresholds are actually satisfied.

Commit:

```text
Close preregistered clean future holdout validation run
```

## Expected Outcomes

Preferred pilot outcome:

```text
primary_decision_label: boltons_clean_future_holdout_pilot_complete_insufficient_sample
paid_acut_calls_made: true
selected_repos: [boltons]
b_eval_scoreable_cells: >= 6
h_future_scoreable_cells: >= 6
policy_violation_count: 0
predictive_validity_established: false
recommended_next_runbook: mine_second_repo_clean_outcome_unseen_supply_for_two_repo_validation
```

Blocked outcome:

```text
primary_decision_label: future_holdout_validation_blocked_non_scoreable_cells
or: future_holdout_validation_blocked_policy_or_cost
predictive_validity_established: false
recommended_next_runbook: repair_workspace_acut_scoreability_or_cost_accounting
```

Scale-up outcome:

```text
primary_decision_label: ready_for_phase1_predictive_validation_scaleup
predictive_validity_established: false unless the two-repo acceptance gate has
  already been run and passed
recommended_next_runbook: preregister_second_repo_clean_future_holdout_validation
```
