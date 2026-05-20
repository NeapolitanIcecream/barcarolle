# Phase 0 Headroom Runbook

Status: operating runbook, 2026-05-20.

This runbook is written for one dedicated Codex CLI session. Its job is to run
Phase 0 far enough to make a defensible restart decision under a hard LLM API
budget of USD 200.

The goal is not task volume. The goal is a complete evidence chain:

1. target-repo work differs from a generic task mix;
2. same-repo tasks can be sourced and certified;
3. a small same-repo benchmark signal can be compared with a generic benchmark
   signal;
4. the final decision says whether to continue toward predictive validity,
   tuning feedback, regression coverage, or stop.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-0-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Do not spend more than USD 200 in
LLM API calls. Treat USD 160 as the soft stop and USD 180 as the stop-and-ask
threshold. Prefer deterministic scripts and local checks. Keep a process log in
experiments/phase0_headroom/reports/process.md. Commit small manifests, configs,
reports, and scripts only. Do not commit large raw artifacts.

At each runbook step, update the process log with status, outputs, budget used,
and the next acceptance gate. If an acceptance gate fails, stop expanding scope
and write the blocker into the decision memo.
```

## Budget Rules

Hard cap: USD 200 total LLM API spend.

Count every external model call started by the worker: paid agent/task-solving
runs, optional LLM review calls, and any Codex CLI subcommand whose usage is
reported by the runtime. If the worker cannot observe session-level cost, keep
projected experiment calls at or below USD 120 and leave the rest as buffer for
unreported session overhead.

Use these internal limits:

- USD 0-20: optional LLM help for summarizing repository history or drafting
  reports. Avoid it unless it saves substantial manual time.
- USD 0-40: task-statement cleanup or ambiguity review, only after deterministic
  extraction has produced candidates.
- USD 0-120: paid agent/task-solving runs for the mini headroom matrix.
- USD 20 reserve: reruns, failed calls, or one follow-up comparison.

Stop rules:

- Stop all paid calls at USD 160 unless the next batch is essential to complete
  the evidence chain.
- Stop and ask the user at USD 180.
- Never start a paid batch whose projected cumulative spend can exceed USD 200.
- If actual cost is unavailable, use a conservative estimate and keep at least
  USD 40 unspent.
- Do not spawn parallel LLM workers or reviewer agents for Phase 0.
- Do not use LLMs for mining commits, cloning repositories, running tests,
  computing features, counting yield, or formatting JSON/CSV.

Every paid model call must append or update a ledger record under:

```text
experiments/phase0_headroom/results/cost_ledger.jsonl
```

Minimum ledger fields:

```json
{
  "timestamp": "",
  "phase": "",
  "event": "",
  "provider": "",
  "model": "",
  "input_tokens": null,
  "output_tokens": null,
  "estimated_cost_usd": 0.0,
  "actual_cost_usd": null,
  "cumulative_estimated_cost_usd": 0.0,
  "artifact_ref": "",
  "command": "",
  "notes": ""
}
```

Acceptance gate: before any paid batch, the ledger exists, the current cumulative
cost is known, and the projected batch keeps cumulative estimated spend below
the applicable stop threshold.

## Scope Defaults

Use the smallest scope that preserves the logic chain:

- one smoke repository: archived Click material, used only to check reuse and
  packaging assumptions;
- one primary target repository selected by deterministic buildability and task
  supply;
- one optional secondary target repository only if Step 4 fails for the primary
  or if total spend is still below USD 80 after Step 6.

Default target counts:

- 30-60 candidate anchors for the primary repo;
- 12-20 executable candidates;
- 6-12 certified tasks;
- 4-6 early same-repo tasks for `B_real`;
- 4-6 late same-repo tasks for `W_real`;
- 4-6 generic benchmark tasks for `G_mini`, reusing existing public or archived
  artifacts when possible.

Paid agent/task-solving runs are optional until Step 7. If paid runs are needed,
start with one cheap ACUT and only add a second ACUT if the first matrix is
scoreable and total projected spend stays below USD 160.

## Directory Layout

Create these directories as needed:

```text
experiments/phase0_headroom/
  configs/
  candidate_sources/
  target_profiles/
  certified_tasks/
  releases/
  results/
  reports/
```

Do not commit cloned repositories, virtual environments, installed dependency
caches, full workspaces, model transcripts, or large raw run outputs. Store
large raw outputs outside Git and reference them by manifest path and digest.

## Step 0: Preflight

Input:

- clean or understood working tree;
- this runbook;
- `docs/experiments/phase-0-headroom-plan.md`;
- `docs/architecture/system-design.md`;
- archived core-narrative material under
  `archive/2026-05-agent-license-reset/`.

Actions:

1. Record branch, HEAD commit, date, shell, Python version, and available disk.
2. Create `experiments/phase0_headroom/reports/process.md`.
3. Create `experiments/phase0_headroom/results/cost_ledger.jsonl` if absent.
4. Check that `.gitignore` excludes large workspaces, caches, and raw artifacts.
5. List reusable archive assets and do not copy them into active paths unless
   the runbook step requires a small manifest or script.

Outputs:

- `experiments/phase0_headroom/reports/process.md`
- `experiments/phase0_headroom/results/cost_ledger.jsonl`
- `experiments/phase0_headroom/reports/preflight.md`

Acceptance:

- process log exists;
- budget ledger exists;
- no paid model call has been made;
- active `experiments/core_narrative` remains absent from tracked files.

Stop if:

- the worker cannot identify the current branch or repo state;
- ignored local raw artifacts would be accidentally committed.

## Step 1: Budget And Execution Config

Actions:

1. Create `experiments/phase0_headroom/configs/budget.yaml`.
2. Set `max_total_usd: 200`, `soft_stop_usd: 160`,
   `stop_and_ask_usd: 180`, and `reserve_usd: 20`.
3. Create `experiments/phase0_headroom/configs/execution.yaml` with local
   workspace roots, raw artifact roots, timeout defaults, and no-model defaults.
4. Add a short `reports/budget_plan.md` explaining how cost is measured.

Suggested `budget.yaml`:

```yaml
max_total_usd: 200
soft_stop_usd: 160
stop_and_ask_usd: 180
reserve_usd: 20
paid_agent_runs_max_usd: 120
optional_llm_review_max_usd: 40
reporting_llm_max_usd: 20
require_ledger_before_paid_call: true
allow_parallel_paid_workers: false
```

Outputs:

- `configs/budget.yaml`
- `configs/execution.yaml`
- `reports/budget_plan.md`

Acceptance:

- a new worker can read the configs and know when to stop;
- no command can be described as "approved" unless it names the ledger path and
  projected cost.

## Step 2: Repository Selection

Actions:

1. Build a shortlist of 5-8 candidate repositories.
2. Exclude repos with non-deterministic external service dependencies, long
   install time, private dependency requirements, or unclear tests.
3. Pick:
   - one smoke repo, normally Click from the archive;
   - one primary target repo;
   - one optional backup repo.
4. Record the choice and rejected candidates.

Selection fields:

```yaml
repo_id:
url:
language:
package_manager:
default_test_command:
install_command:
median_test_runtime_estimate_seconds:
external_service_risk:
candidate_anchor_estimate:
why_selected_or_rejected:
```

Outputs:

- `configs/repositories.yaml`
- `reports/repository_selection.md`

Acceptance:

- at least one primary target repo has deterministic local install and test
  commands;
- selection uses task supply, buildability, and low external-service risk, not
  popularity alone;
- no LLM call is needed.

Stop if:

- no repository can be built locally in a bounded time;
- all plausible repos require private services or credentials.

## Step 3: Target-Profile And Distribution Mismatch

Actions:

1. For the primary repo, collect historical commits, PRs, issues, or changelog
   anchors around the chosen cutoff.
2. Split history into early and late windows.
3. Extract deterministic features:
   - module or package;
   - task type proxy;
   - changed files and changed lines;
   - test-file involvement;
   - dependency radius proxy;
   - issue or PR text length and labels where available;
   - API surface touched;
   - runtime or platform constraints.
4. Compare the primary repo profile with a generic task profile from available
   public or archived benchmark metadata.
5. Produce a divergence table and a low-dimensional target profile.

Outputs:

- `candidate_sources/<repo_id>_history_anchors.jsonl`
- `target_profiles/<repo_id>_target_profile.json`
- `results/<repo_id>_distribution_mismatch.csv`
- `reports/distribution_mismatch.md`

Acceptance:

- the target profile has explicit feature definitions and missing-data labels;
- at least one feature family has an interpretable mismatch, or the report says
  there is no measurable mismatch at this scope;
- no task generation or paid model run is required.

Stop if:

- the repo history cannot be split into early and late windows;
- extracted features are too sparse to compare.

## Step 4: Candidate Task Supply

Actions:

1. Mine candidate anchors from commits, PRs, issues, and test changes.
2. Start with deterministic extraction. Use LLM cleanup only if it is within the
   optional review budget and recorded in the ledger.
3. For each candidate, create a manifest with:
   - base commit;
   - task time;
   - changed files;
   - source text pointers;
   - candidate oracle source;
   - leakage risks;
   - taxonomy draft.
4. Reconstruct the base checkout in an ignored workspace.
5. Try environment setup and oracle extraction.

Outputs:

- `candidate_sources/<repo_id>_candidates.jsonl`
- `candidate_sources/<repo_id>_supply_funnel.csv`
- ignored raw workspaces referenced by manifest

Acceptance:

- at least 12 executable candidates or a clear rejection table explaining why
  supply is insufficient;
- each rejected candidate has a first failing gate;
- large raw checkouts are outside Git.

Stop if:

- fewer than 6 candidates can reach `executable`;
- the next source adapter needed is obvious and cannot be built under the
  remaining budget.

## Step 5: Certification Gates

Actions:

Run certification gates for each executable candidate:

1. no-op fail;
2. reference pass;
3. known-bad fail, using the original failing change, a reverted reference
   patch, or a small negative-control mutation where available;
4. repeated-run flakiness check;
5. ambiguity review;
6. solution-leakage review across issue text, PR comments, docs, tests, and
   generated statement;
7. scope-clarity review;
8. cost boundedness for setup, agent run, and verifier runtime;
9. feature-taxonomy labelability.

Use these statuses:

- `candidate`: sourced but not replayed;
- `executable`: checkout, build, and oracle are available;
- `oracle_valid`: no-op, reference, and known-bad checks pass;
- `certified`: all required gates pass;
- `near_certified`: one or more review gates are missing, weak, or manual-only;
- `rejected`: a required gate fails.

Outputs:

- `certified_tasks/<repo_id>_certification_funnel.csv`
- `certified_tasks/<repo_id>_certified_tasks.jsonl`
- `certified_tasks/<repo_id>_near_certified_tasks.jsonl`
- `reports/certification_funnel.md`

Acceptance:

- certified and near-certified tasks are separated;
- every candidate has a status and rejection reason;
- only `certified` tasks can count toward the MVP release target;
- the report includes manual review minutes and runtime/cost estimates.

Stop if:

- no candidate reaches `oracle_valid`;
- leakage or ambiguity blocks most candidates and needs a new source adapter.

## Step 6: Mini Release Assembly

Actions:

1. Assemble a minimal release from certified tasks.
2. If certified yield is low, assemble a diagnostic release and label it as not
   benchmark-grade.
3. Split tasks into:
   - early same-repo tasks, `B_real`;
   - late same-repo tasks, `W_real`;
   - optional canary or dev split;
   - generic comparator tasks, `G_mini`, if available.
4. Record task weights. Start unweighted, then add a simple stratified weighting
   column if target-profile strata are clear.

Outputs:

- `releases/<repo_id>_phase0_mini_release.json`
- `releases/<repo_id>_phase0_task_table.csv`
- `reports/mini_release.md`

Acceptance:

- release manifest names exact task IDs, splits, weights, and certification
  status;
- a release with fewer than 6 certified tasks is labeled diagnostic only;
- no `near_certified` task is counted as benchmark-grade.

## Step 7: Budgeted Headroom Matrix

Run this step only after Steps 3-6 pass. Keep it small.

Default matrix:

- one cheap or low-cost ACUT;
- one stronger ACUT only if the first matrix is scoreable and projected spend
  remains below USD 160;
- 4-6 `B_real` tasks;
- 4-6 `W_real` tasks;
- 4-6 `G_mini` tasks.

Actions:

1. Dry-run the harness without model calls.
2. Record projected cost for each paid batch.
3. Run the smallest batch that can produce a scoreable comparison.
4. Compute:
   - `G_mini -> W_real`;
   - `B_real -> W_real`;
   - `G_mini + B_real -> W_real`, only if there are enough ACUT/task cells;
   - residual notes by stratum.
5. Report MAE/RMSE only when the sample is large enough to avoid meaningless
   precision. Otherwise report directional diagnostics and mark as
   underpowered.

Outputs:

- `results/headroom_matrix.json`
- `results/headroom_metrics.json`
- `reports/headroom_analysis.md`
- updated `results/cost_ledger.jsonl`

Acceptance:

- no paid run starts without a budget gate;
- failed or invalid submissions are labeled separately from verified failures;
- the analysis does not claim predictive validity from an underpowered matrix;
- if budget blocks the matrix, the report says exactly which comparison is
  missing.

Stop if:

- cumulative estimated spend reaches USD 160 and the evidence chain is still
  incomplete;
- paid runs are unscoreable because of harness, oracle, or output-contract
  failure.

## Step 8: Decision Memo

Actions:

Write `reports/phase0_decision_memo.md` with:

1. repo selection and scope;
2. total LLM API spend and ledger path;
3. distribution mismatch result;
4. supply and certification yield;
5. mini release status;
6. headroom matrix result or blocker;
7. threats to validity;
8. decision.

Allowed decisions:

- `proceed_predictive`: enough signal and supply to justify Phase 1 predictive
  validation;
- `proceed_tuning_feedback`: certification works, but predictive headroom is
  weak or underpowered;
- `proceed_regression_benchmark`: task supply is useful, but predictive framing
  is not yet supported;
- `repair_source_adapter`: task supply or oracle extraction is the main blocker;
- `stop`: evidence does not justify continuing the restart in this form.

Acceptance:

- the decision follows from the evidence, not from the desired narrative;
- all unsupported claims are labeled as open questions;
- the memo can be read without inspecting raw artifacts;
- the memo names the next smallest useful experiment.

## Step 9: Commit Hygiene

Actions:

1. Run `git status --short --ignored`.
2. Confirm ignored raw artifacts are not staged.
3. Run `git diff --check`.
4. Stage only configs, scripts, small manifests, tables, and reports.
5. Commit with a message that names the completed step.

Acceptance:

- committed artifacts are small and reviewable;
- `experiments/phase0_headroom/results/cost_ledger.jsonl` is committed only if
  it contains no secrets, endpoints, raw prompts, or private responses;
- raw model responses and full workspaces remain out of Git;
- final status is clean except for intentionally ignored artifacts.

## Final Success Criteria

Phase 0 is complete when the repo contains:

- a target-profile draft with a mismatch result;
- a gate-level certification funnel;
- a mini release manifest or a diagnostic release label;
- a budgeted headroom analysis or a precise blocker;
- a decision memo with one of the allowed decisions;
- total LLM API spend below USD 200.

Phase 0 should stop early if it can already make a defensible negative or pivot
decision. Do not spend budget to make the result look larger.
