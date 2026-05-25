# Phase 1 Autonomous Overnight Two-Repo Research Runbook

Status: overnight autonomous runbook, 2026-05-22.

This runbook is for one unattended Codex CLI session. Its job is to use the
overnight window to push Phase 1 as far as the evidence, endpoint, cost, and
artifact hygiene allow.

Unlike the narrow step-by-step runbooks, this one gives the worker a decision
tree. The worker should make conservative research judgments, choose the most
valuable safe branch, commit each checkpoint, and keep going until one of these
terminal outcomes is reached:

- the preregistered two-repo paid validation has run and been scored;
- paid validation is blocked, but local blockers are repaired or precisely
  reported;
- the evidence shows the next meaningful step needs user input or a new paid
  budget decision.

## Current Starting Point

The expected starting state is:

```text
Boltons paid clean future-holdout pilot:
  B_eval scoreable cells: 8
  H_future scoreable cells: 8
  policy violations: 0
  predictive_validity_established: false

Attrs second-repo clean supply:
  promoted clean tasks: 18
  selected B_eval tasks: 4
  selected H_future tasks: 4
  paid second-repo ACUT calls: false

Two-repo preregistration:
  status: frozen
  selected repos: boltons, attrs
  planned attrs B_eval cells: 8
  planned attrs H_future cells: 8
  total H_future capacity if attrs is scoreable: 16
  recommended next runbook: run_two_repo_preregistered_clean_future_holdout_paid_validation
```

The important boundary is simple:

```text
The design is ready for a paid two-repo validation attempt.
It has not yet produced predictive-validation evidence, because attrs has not
run paid ACUT cells.
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing <repo>/docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md.

Work in <repo>. Use uv for repo-local Python tooling.
Make a cohesive git commit after every completed checkpoint that changes files.
Do not batch unrelated checkpoints into one commit. Do not push unless explicitly
asked.

Your main goal is to make as much safe overnight progress as possible toward a
Phase 1 two-repo predictive-validation result. Think and decide as you work:
prefer the highest-value valid branch, but do not overclaim. If a paid branch is
blocked, switch to local repair, supply, metrics, or blocker-report work instead
of stopping early.

Primary path: run the frozen two-repo paid validation for attrs using the
existing Codex/Kilo workspace ACUT adapters, then score the combined Boltons +
attrs evidence.

All paid LLM or ACUT calls must use LLM_BASE_URL plus LLM_API_KEY. If either is
missing, source ~/.zshrc and check again. Do not use local Codex/ChatGPT
subscription auth, OPENAI_API_KEY, OpenRouter variables, or provider-specific
fallback variables.

Run paid ACUT cells sequentially. Import usage after every paid batch. Stop
before the next paid batch if scoreability, policy, endpoint, or cost accounting
is blocked. Do not rerun scoreable cells. Rerun non-scoreable cells only if a
clear harness or infrastructure issue has been fixed and the rerun is recorded
as a bounded repair attempt.

Keep Barcarolle on the benchmark/compiler side of the ACUT boundary. Do not
implement Codex, Kilo, or another ACUT harness. Barcarolle may prepare
workspaces, invoke configured harnesses, capture diffs, replay diffs in fresh
verifier workspaces, inject private oracle material only in verifier
workspaces, and record sanitized results.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
GitHub API responses, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, or large raw outputs. Commit only small sanitized
configs, manifests, tools, tests, score tables, summaries, reports, and
decisions. Raw artifacts must remain under ignored paths.
```

## Autonomy Rules

The worker should not wait for the user unless all safe branches are exhausted.
Use this order of preference:

1. Preserve correctness and benchmark boundaries.
2. Preserve cost and endpoint rules.
3. Complete the frozen two-repo validation if gates allow it.
4. If paid validation is blocked, fix local tooling or metadata blockers.
5. If validation runs but evidence is underpowered or noisy, add local analysis,
   confidence intervals, failure taxonomy, and a precise next-runbook plan.
6. If all validation paths are blocked, mine or prepare additional clean supply
   only without paid calls.

The worker may make small implementation changes when they are needed to finish
the runbook, but should not redesign the benchmark protocol during the night.
Protocol changes must be recorded as sidecar evidence and tested.

## Claim Boundary

Allowed claims:

```text
two_repo_preregistered_paid_validation_run
attrs_paid_future_holdout_cells_scoreable
two_repo_future_holdout_metrics_computed
same_endpoint_model_different_cli_harnesses
observed_or_conservative_cost_accounting
phase1_predictive_validation_pilot_complete
insufficient_evidence_for_predictive_validation
paid_validation_blocked_with_precise_reason
local_repair_or_supply_work_completed
```

Disallowed claims:

```text
production_benchmark_ranking
pure_harness_effect
contamination_proof_evaluation_if_model_snapshot_unknown
predictive_validity_established_without_two_repo_thresholds
predictive_validity_established_with_policy_violations
predictive_validity_established_if_holdout_was_used_for_tuning
validation_grade_humanize_if_commit_fallback_only
```

The worker may set `predictive_validity_established=true` only if all are true:

- selected target repos are at least `2`;
- H_future scoreable cells are at least `12`;
- policy violations are `0`;
- holdout tuning did not occur;
- B_eval and H_future metrics are computed from the frozen design;
- the pre-registered decision logic says the validation threshold passed.

If the tooling does not yet implement the final threshold check, do not set
`predictive_validity_established=true`; instead record
`phase1_predictive_validation_pilot_complete` or
`insufficient_evidence_for_predictive_validation`.

## Budget And Runtime Rules

Use these unattended caps unless a committed config is stricter:

```text
current cumulative observed-or-conservative spend: about USD 46.99
overnight incremental soft cap: USD 20
overnight incremental hard cap: USD 35
absolute unattended stop cap: USD 80 cumulative observed-or-conservative
conservative estimate per workspace ACUT cell: USD 0.50
planned attrs paid cells: 16
planned conservative attrs increment: USD 8.00
```

Stop before paid work if:

- `LLM_BASE_URL` or `LLM_API_KEY` is missing after sourcing `~/.zshrc`;
- projected cumulative observed-or-conservative spend reaches `USD 80`;
- projected overnight increment reaches `USD 35`;
- usage import is broken and conservative fallback cannot bound the run;
- adapter preflight is not `ready`;
- the frozen two-repo preregistration is missing or not frozen.

Stop after a paid batch if:

- usage observed rate drops below `0.85` and conservative fallback would exceed
  a cap;
- any policy violation occurs;
- hidden oracle material appears in a solver workspace;
- more than `2` cells in the current split are non-scoreable;
- an adapter repeatedly fails due to harness errors rather than task outcomes.

## Decision Tree

Use this tree during the night.

### Branch A: Preflight Fails

Do not run paid cells. Fix what is local and safe:

- stale or inconsistent JSON/report fields;
- missing package-inspection support for attrs;
- missing score import for planned prefixes;
- tests that need updating after the last committed changes.

Then rebuild reports and close with a blocker if paid gates still fail.

### Branch B: Paid Gates Pass

Run the paid attrs batches:

```text
phase1_two_repo_future_holdout_attrs_b_eval
phase1_two_repo_future_holdout_attrs_h_future
```

Run Codex and Kilo sequentially. Import usage after each split. Commit after
each paid split.

### Branch C: B_eval Runs, H_future Blocked

Do not continue blindly. Analyze whether the blocker is:

- endpoint/cost;
- policy violation;
- hidden oracle leak;
- package construction;
- verifier failure;
- adapter timeout or invalid output.

Fix only benchmark-side issues. Do not modify ACUT internals. Commit the partial
paid results and blocker report.

### Branch D: Both Paid Splits Run

Compute combined metrics across:

- existing Boltons paid B_eval/H_future;
- new attrs paid B_eval/H_future.

Update Phase 1 closeout. If thresholds are not met, explain why in simple
terms. If thresholds are met and the code supports the claim, record the narrow
pilot claim without creating a production ranking.

### Branch E: Metrics Underpowered Or Ambiguous

Use remaining local time for analysis, not extra unplanned paid runs:

- adapter-level error table;
- repo-level error table;
- task-level pass/fail table;
- confidence interval or binomial uncertainty summary;
- failure taxonomy;
- next-runbook recommendation.

### Branch F: Everything Is Healthy And Cheap

Only after the frozen attrs validation is complete and scored, the worker may
do local-only preparation for the next day:

- draft a follow-up scale-up runbook;
- inspect reserve attrs tasks for future use;
- identify whether reserve tasks would improve uncertainty;
- do not run extra paid reserve cells unless a committed preregistration already
  permits them.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_autonomous_overnight_two_repo_research.yaml
  results/
    phase1_autonomous_overnight_two_repo_preflight.json
    phase1_two_repo_future_holdout_prediction_metrics.json
    phase1_two_repo_future_holdout_decision.json
    phase1_autonomous_overnight_two_repo_decision.json
    phase1_mvp_closeout.json
  reports/
    phase1_autonomous_overnight_two_repo_process.md
    phase1_two_repo_future_holdout_prediction_metrics.md
    phase1_two_repo_future_holdout_decision.md
    phase1_autonomous_overnight_two_repo_decision.md
    phase1_mvp_closeout.md
```

Use Phase 0 workspace ACUT result prefixes:

```text
experiments/phase0_headroom/results/
  phase1_two_repo_future_holdout_attrs_b_eval_*.json*
  phase1_two_repo_future_holdout_attrs_b_eval_score_table.csv
  phase1_two_repo_future_holdout_attrs_h_future_*.json*
  phase1_two_repo_future_holdout_attrs_h_future_score_table.csv
  workspace_usage_ledger.jsonl
  workspace_cost_reconciliation.json
```

Raw artifacts remain ignored:

```text
experiments/phase0_headroom/results/raw/
experiments/phase0_headroom/workspaces/
experiments/phase0_headroom/external_repos/
```

## Step 0: Preflight And Plan

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`,
   `codex --version` if available, and `kilo --version` if available.
2. Check endpoint variables without printing values:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

3. Confirm the frozen two-repo design:

```bash
jq '{primary_decision_label, selected_repos, selected_repo_id, two_repo_preregistration_status, paid_second_repo_acut_calls_made, predictive_validity_established, recommended_next_runbook}' \
  experiments/phase1_compiler/results/phase1_second_repo_clean_supply_decision.json

jq '{status, selected_repos, planned_second_repo_tasks, planned_second_repo_cells, existing_paid_evidence, acceptance, recommended_next_runbook}' \
  experiments/phase1_compiler/results/phase1_two_repo_future_holdout_preregistration.json
```

4. Run baseline validation:

```bash
git diff --check
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

5. Write:

```text
experiments/phase1_compiler/configs/phase1_autonomous_overnight_two_repo_research.yaml
experiments/phase1_compiler/results/phase1_autonomous_overnight_two_repo_preflight.json
experiments/phase1_compiler/reports/phase1_autonomous_overnight_two_repo_process.md
```

Acceptance:

- two-repo preregistration is `frozen`;
- selected repos are `boltons` and `attrs`;
- no second-repo paid cells have already run;
- endpoint variables are present before paid work;
- tests and validation pass;
- the process report states which branch the worker selected first.

Commit:

```text
Record autonomous overnight two repo preflight
```

## Step 1: Repair Local Metadata If Needed

This step is intentionally flexible. It exists so the worker can fix small local
issues before spending money.

Known issue to check:

```text
phase1_second_repo_clean_supply_process.md says attrs scanned 388 anchors, but
phase1_second_repo_clean_supply_candidate_inventory.json may show
anchors_scanned: 0 after later certification rewrites.
```

Actions:

1. Check whether sanitized reports and JSON agree on candidate counts.
2. If counts disagree, fix the deterministic tool/report logic and regenerate
   the affected artifacts.
3. Add a focused regression test if the bug is in tooling.
4. Do not change promoted task decisions unless the underlying evidence is
   wrong.

Acceptance:

- candidate count, certification count, and promoted count agree across JSON
  and Markdown reports;
- no paid cells run in this step;
- tests covering the changed logic pass.

Commit:

```text
Repair second repo clean supply metadata
```

If no repair is needed, record `metadata_repair_not_needed` in the process
report and continue without an empty commit.

## Step 2: Paid Entry Gate For Attrs

Actions:

1. Run workspace ACUT preflight for both attrs prefixes and both adapters. Use
   separate preflight result prefixes so the preflight artifacts do not
   overwrite each other:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml \
  --result-prefix phase1_two_repo_future_holdout_attrs_b_eval_codex_preflight

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml \
  --result-prefix phase1_two_repo_future_holdout_attrs_b_eval_kilo_preflight

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml \
  --result-prefix phase1_two_repo_future_holdout_attrs_h_future_codex_preflight

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml \
  --result-prefix phase1_two_repo_future_holdout_attrs_h_future_kilo_preflight
```

2. Inspect package selection for attrs B_eval and H_future. If the workspace
   runner cannot load attrs clean-overlay tasks yet, add package-loading support
   using sidecar evidence. Do not mutate canonical release files.
3. Check that target task ids match the frozen preregistration exactly.
4. Check that target prefixes have no prior paid rows.
5. Record projected cost:

```text
attrs B_eval: 4 tasks * 2 adapters = 8 cells
attrs H_future: 4 tasks * 2 adapters = 8 cells
planned total: 16 cells
conservative planned increment: USD 8.00
```

Acceptance:

- all adapter preflights are `ready`;
- attrs packages can be selected by task id;
- score tables for planned attrs prefixes have no previous paid rows;
- projected cumulative spend remains below the unattended cap;
- paid parallelism is disabled.

Commit:

```text
Record attrs paid validation entry gate
```

## Step 3: Run Paid Attrs B_eval

Actions:

Run Codex and Kilo sequentially:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml \
  --result-prefix phase1_two_repo_future_holdout_attrs_b_eval \
  --task-id attrs__hist__001 \
  --task-id attrs__hist__003 \
  --task-id attrs__hist__004 \
  --task-id attrs__hist__008

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml \
  --result-prefix phase1_two_repo_future_holdout_attrs_b_eval \
  --task-id attrs__hist__001 \
  --task-id attrs__hist__003 \
  --task-id attrs__hist__004 \
  --task-id attrs__hist__008
```

Then import usage and summarize:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_usage_import.py \
  --root . \
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --result-prefix phase1_two_repo_future_holdout_attrs_b_eval

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  summarize \
  --result-prefix phase1_two_repo_future_holdout_attrs_b_eval
```

Acceptance:

- all `8` B_eval cells have terminal status;
- at least `6/8` are scoreable;
- policy violations are `0`;
- usage/cost is observed or conservatively bounded;
- no hidden oracle leak is detected in solver workspaces.

Commit:

```text
Run attrs B_eval paid batch
```

## Step 4: Decide Whether H_future May Run

Actions:

Inspect the B_eval result:

- if scoreability and policy gates pass, continue to Step 5;
- if not, stop paid work and write a blocker;
- if the issue is local package/verifier construction and can be fixed without
  ACUT internals, fix it and rerun only non-scoreable cells if policy permits.

Acceptance:

- the decision to continue or stop is written in the process report;
- no H_future paid cell runs after a failed B_eval gate.

Commit:

```text
Record attrs H_future continuation decision
```

If the decision is simply "continue" and no files changed beyond the process
report already committed in Step 3, continue without an empty commit.

## Step 5: Run Paid Attrs H_future

Actions:

Run Codex and Kilo sequentially:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml \
  --result-prefix phase1_two_repo_future_holdout_attrs_h_future \
  --task-id attrs__hist__012 \
  --task-id attrs__hist__013 \
  --task-id attrs__hist__023 \
  --task-id attrs__hist__027

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml \
  --result-prefix phase1_two_repo_future_holdout_attrs_h_future \
  --task-id attrs__hist__012 \
  --task-id attrs__hist__013 \
  --task-id attrs__hist__023 \
  --task-id attrs__hist__027
```

Then import usage and summarize:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_usage_import.py \
  --root . \
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --result-prefix phase1_two_repo_future_holdout_attrs_h_future

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  summarize \
  --result-prefix phase1_two_repo_future_holdout_attrs_h_future
```

Acceptance:

- all `8` H_future cells have terminal status;
- at least `6/8` are scoreable;
- policy violations are `0`;
- usage/cost is observed or conservatively bounded;
- no hidden oracle leak is detected in solver workspaces.

Commit:

```text
Run attrs H_future paid batch
```

## Step 6: Compute Two-Repo Metrics

Actions:

1. Extend or run the existing future-holdout scorer so it consumes:
   - Boltons paid prefixes:
     - `phase1_future_holdout_b_eval`
     - `phase1_future_holdout_h_future`
   - attrs paid prefixes:
     - `phase1_two_repo_future_holdout_attrs_b_eval`
     - `phase1_two_repo_future_holdout_attrs_h_future`
2. Compute:
   - scoreable cell counts by repo, split, and adapter;
   - pass rates by repo, split, and adapter;
   - absolute error per repo/adapter;
   - pooled MAE;
   - policy violation count;
   - non-scoreable count;
   - cost summary.
3. Write:

```text
experiments/phase1_compiler/results/phase1_two_repo_future_holdout_prediction_metrics.json
experiments/phase1_compiler/reports/phase1_two_repo_future_holdout_prediction_metrics.md
experiments/phase1_compiler/results/phase1_two_repo_future_holdout_decision.json
experiments/phase1_compiler/reports/phase1_two_repo_future_holdout_decision.md
```

Acceptance:

- metrics include both repos;
- total H_future scoreable cells are recorded;
- policy violations are recorded;
- decision does not claim predictive validity unless the threshold logic is
  implemented and passes.

Commit:

```text
Compute two repo future holdout metrics
```

## Step 7: Rebuild Phase 1 Closeout

Actions:

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

Update closeout so it explains the result in plain terms:

- what ran;
- how many cells were scoreable;
- whether thresholds were met;
- whether predictive validity is established;
- what should happen next.

Acceptance:

- closeout imports two-repo paid evidence as sidecar evidence;
- `predictive_validity_established` is correct;
- production ranking remains `not_produced`;
- validation returns `status=valid`.

Commit:

```text
Import two repo future holdout evidence
```

## Step 8: Optional Local Analysis

Run this step only if paid validation is complete or blocked and there is still
time.

Allowed local work:

- failure taxonomy for failed cells;
- task-level result table;
- adapter-level comparison;
- repo-level comparison;
- uncertainty summary;
- draft next runbook;
- reserve-task audit for future scale-up.

Do not run extra paid cells in this optional step unless a committed
preregistration already allows them.

Commit:

```text
Add overnight two repo analysis
```

## Step 9: Final Decision And Hygiene

Actions:

1. Write:

```text
experiments/phase1_compiler/results/phase1_autonomous_overnight_two_repo_decision.json
experiments/phase1_compiler/reports/phase1_autonomous_overnight_two_repo_decision.md
```

2. Use one of these final labels:

```text
two_repo_paid_validation_complete_predictive_threshold_met
two_repo_paid_validation_complete_insufficient_evidence
two_repo_paid_validation_blocked_before_paid_calls
two_repo_paid_validation_blocked_after_partial_run
local_repair_completed_paid_validation_deferred
```

3. Run final checks:

```bash
git diff --check
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
git status --short
```

4. Confirm raw paths are not staged:

```bash
git diff --cached --name-only
git check-ignore -q experiments/phase0_headroom/results/raw || true
git check-ignore -q experiments/phase0_headroom/workspaces || true
git check-ignore -q experiments/phase0_headroom/external_repos || true
```

Acceptance:

- final decision is clear;
- tests pass unless a precise blocker explains why not;
- no raw artifacts are committed;
- every major checkpoint with file changes has a commit;
- no push was performed.

Commit:

```text
Close autonomous overnight two repo research run
```

## Simple Completion Analysis Template

At the end, write the completion analysis in simple Chinese using this shape:

```text
这次完成了什么：
...

结果好不好：
...

有没有达到主目标：
...

还卡在哪里：
...

下一步：
...
```
