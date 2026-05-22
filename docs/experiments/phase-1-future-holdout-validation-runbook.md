# Phase 1 Future Holdout Validation Runbook

Status: implementation runbook, 2026-05-22.

This runbook is for one dedicated Codex CLI session. Its job is to
pre-register a Phase 1 future-holdout validation design, select repo-time
cutoffs, audit whether there is enough outcome-unseen validation-grade task
supply, and run only the smallest paid ACUT validation batch if the frozen
design passes its entry gates.

This runbook may make paid ACUT calls only after the design-freeze gate passes.
All paid LLM or ACUT calls must use only the configured OpenAI-compatible
endpoint:

```text
LLM_BASE_URL
LLM_API_KEY
```

If either variable is missing in the worker shell, source `~/.zshrc` and check
again before any paid call. Do not use local Codex/ChatGPT subscription auth,
`OPENAI_API_KEY`, OpenRouter variables, or provider-specific fallbacks.

## Why This Runbook Exists

The completed Boltons paid smoke shows that the workspace ACUT protocol is
operational:

- `14` paid Boltons cells were run;
- `13` cells were scoreable;
- policy violations were `0`;
- observed-or-conservative cumulative cost was about `USD 37.65`;
- predictive validity was explicitly not established.

The next evidence gap is not another generic scale-up. The next evidence gap is
a clean future-holdout design:

```text
compiler-visible repo history  -> Barcarolle benchmark score
future holdout repo history     -> held-out target-repo outcome
```

This runbook makes the cutoff and split rules explicit before any new paid
validation cells are run.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-1-future-holdout-validation-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make cohesive commits after completing one or more related steps.

Your first job is to freeze the future-holdout validation design before any new
paid ACUT cells are run. The primary cutoff axis is target-repo task time. Model
release or snapshot date is only a contamination guard, not the main cutoff. If
the model release/snapshot date cannot be reliably established from committed
metadata or the endpoint model list, record it as unknown and do not claim
contamination-proof evaluation.

Do not treat any task with previously observed ACUT outcome as a clean future
holdout task. Existing Toolz, Humanize, and Boltons paid/smoke/stability results
may be used as sidecar evidence, feasibility evidence, or dev diagnostics, but
not as the final future-holdout validation target.

This runbook may make paid ACUT calls only after the design-freeze gate passes.
Every paid call must use LLM_BASE_URL plus LLM_API_KEY. If either variable is
missing, source ~/.zshrc and check again. Do not use local Codex/ChatGPT
subscription auth, OPENAI_API_KEY, OpenRouter variables, or provider-specific
fallbacks.

Run paid ACUT cells sequentially. Do not enable paid parallelism. Import usage
after each paid batch and stop if usage/cost cannot be bounded.

Keep Barcarolle on the benchmark/compiler side of the ACUT boundary. Do not
implement Codex, Kilo, or any other ACUT internals.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts,
solver workspaces, verifier workspaces, cloned external repositories, .venv,
caches, raw GitHub API responses, or large raw outputs. Commit only small
sanitized configs, manifests, score tables, cost summaries, reports, and
decision files. Raw harness outputs must stay under ignored paths.

Do not push unless explicitly asked.
```

## Claim Boundary

Allowed claims:

```text
future_holdout_design_preregistered
repo_time_cutoff_policy_defined
outcome_unseen_task_supply_audited
workspace_acut_future_holdout_smoke_run
same_endpoint_model_different_cli_harnesses
observed_or_conservative_cost_accounting
insufficient_evidence_for_predictive_validation
ready_for_phase1_predictive_validation_scaleup
future_holdout_supply_blocked
```

Disallowed claims:

```text
predictive_validity_established
production_benchmark_ranking
pure_harness_effect
contamination_proof_evaluation_if_model_snapshot_unknown
future_holdout_validity_if_holdout_used_for_tuning
validation_grade_humanize_if_commit_fallback_only
```

Important interpretation:

- `verified_pass` and `verified_fail` are both scoreable ACUT outcomes.
- `policy_violation`, `invalid_output`, `acut_harness_error`, `harness_error`,
  and `timeout` are non-scoreable/harness or benchmark-boundary problems.
- This runbook can establish that a clean future-holdout validation protocol is
  executable. It cannot establish predictive validity unless the pre-registered
  validation batch has enough independent holdout cells and the resulting error
  metrics meet the pre-registered thresholds.
- If the clean task supply is too small, stop with a supply blocker. Do not
  launder previously observed ACUT cells into a future holdout.

## Cutoff Policy

Use repo-time as the primary cutoff axis.

Definitions:

```text
T_compile_end:
  Last task_time allowed to inform target profile, task selection, weights,
  baseline choice, ACUT config, retry policy, and predictor design.

embargo_gap_days:
  Buffer between compiler-visible tasks and holdout tasks. Default: 14 days.

T_holdout_start:
  T_compile_end + embargo_gap_days.

B_eval:
  Outcome-unseen scoreable benchmark tasks selected from compiler-visible
  history. ACUT outcomes on B_eval create the Barcarolle predictor input.

H_future:
  Outcome-unseen tasks with task_time >= T_holdout_start. ACUT outcomes on
  H_future are used only as validation target W_r(a).
```

Model release or snapshot date policy:

```text
model_snapshot_boundary:
  If a reliable model release/snapshot date is available, record it and require
  H_future task_time to be later than that date.

unknown_model_snapshot:
  If the date is not reliable, record model_snapshot_status=unknown and do not
  claim contamination-proof evaluation. Continue with repo-time holdout only.
```

Do not choose `T_compile_end` by convenience alone. The cutoff must satisfy:

- enough compiler-visible tasks for `B_eval`;
- enough later tasks for `H_future`;
- no task overlap between `B_eval` and `H_future`;
- no previously observed ACUT outcomes in either clean validation split;
- `H_future` is later in repo task time than `B_eval`;
- `embargo_gap_days >= 14` unless the process report justifies a smaller pilot.

## Eligible Repos

Primary candidates:

```text
boltons
toolz
```

Diagnostic-only unless repaired:

```text
humanize
```

Excluded from target-repo future holdout:

```text
click
generic_comparators
```

Rules:

- Prefer `boltons` because it is the active third repo with local certification
  and successful paid workspace smoke.
- Use `toolz` only if outcome-unseen validation-grade tasks are available or
  can be locally certified without reusing prior paid outcomes.
- Do not use `humanize` as validation-grade until commit-message fallback
  source provenance is repaired to non-leaky problem context.
- Generic comparators can remain sidecar evidence but cannot be target-repo
  holdout tasks.

## Budget And Parallelism

Local design, supply audit, and artifact generation are unpaid.

Paid validation is allowed only after the design-freeze gate passes.

Default paid plan:

```text
minimum clean validation:
  2 B_eval tasks * 2 harnesses = 4 cells
  2 H_future tasks * 2 harnesses = 4 cells
  total = 8 cells

preferred clean validation:
  4 B_eval tasks * 2 harnesses = 8 cells
  4 H_future tasks * 2 harnesses = 8 cells
  total = 16 cells
```

Budget caps:

```text
Conservative estimate per workspace ACUT cell: USD 0.50
Minimum clean validation conservative increment: USD 4.00
Preferred clean validation conservative increment: USD 8.00
Incremental hard cap for this runbook: USD 20.00
Total observed-or-conservative stop cap: USD 80.00
```

Run paid ACUT cells sequentially.

Stop before paid validation if:

- current observed-or-conservative total is already at or above `USD 80`;
- projected incremental cost would exceed `USD 20`;
- usage import is broken and conservative fallback cannot bound the run;
- either adapter cannot prove endpoint-backed operation through
  `LLM_BASE_URL` and `LLM_API_KEY`;
- paid parallelism would be required.

## Result Prefixes

Use these result prefixes:

```text
phase1_future_holdout_design_codex_preflight
phase1_future_holdout_design_kilo_preflight
phase1_future_holdout_b_eval
phase1_future_holdout_h_future
```

Only create the paid result prefixes after the design-freeze gate passes.

When importing usage, include all prior canonical prefixes plus new prefixes
that exist:

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

Omit `phase1_future_holdout_b_eval` and `phase1_future_holdout_h_future` until
they exist.

## Output Layout

Add or update:

```text
docs/experiments/
  phase-1-future-holdout-validation-runbook.md

experiments/phase1_compiler/
  configs/
    phase1_future_holdout_validation.yaml
  results/
    phase1_future_holdout_preflight.json
    phase1_future_holdout_clean_supply.json
    phase1_future_holdout_cutoff_plan.json
    phase1_future_holdout_preregistration.json
    phase1_future_holdout_prediction_metrics.json
    phase1_future_holdout_decision.json
    phase1_mvp_closeout.json
    phase1_workspace_scorecard.json
    phase1_cost_summary.json
  reports/
    phase1_future_holdout_process.md
    phase1_future_holdout_clean_supply.md
    phase1_future_holdout_preregistration.md
    phase1_future_holdout_prediction_metrics.md
    phase1_future_holdout_decision.md
    phase1_mvp_closeout.md
    phase1_workspace_scorecard.md
    phase1_cost_summary.md
```

If new tooling is needed, add:

```text
experiments/phase1_compiler/tools/phase1_future_holdout.py
experiments/phase1_compiler/tests/test_phase1_future_holdout.py
```

The workspace ACUT runner may add or update sanitized Phase 0 result artifacts:

```text
experiments/phase0_headroom/results/
  phase1_future_holdout_b_eval_*.json
  phase1_future_holdout_b_eval_*.jsonl
  phase1_future_holdout_b_eval_score_table.csv
  phase1_future_holdout_h_future_*.json
  phase1_future_holdout_h_future_*.jsonl
  phase1_future_holdout_h_future_score_table.csv
  workspace_usage_ledger.jsonl
  workspace_cost_reconciliation.json
experiments/phase0_headroom/reports/
  phase1_future_holdout_design_codex_preflight.md
  phase1_future_holdout_design_kilo_preflight.md
  workspace_cost_usage_report.md
```

Raw outputs under `experiments/phase0_headroom/results/raw/` and workspaces
under `experiments/phase0_headroom/workspaces/` must remain ignored and
untracked.

## Step 0: Preflight

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, and current git
   status in:

```text
experiments/phase1_compiler/reports/phase1_future_holdout_process.md
```

2. Confirm the current boundary:

```bash
jq -r '.primary_decision_label' \
  experiments/phase1_compiler/results/phase1_boltons_paid_acut_smoke_decision.json

jq -r '.recommended_next_runbook' \
  experiments/phase1_compiler/results/phase1_boltons_paid_acut_smoke_decision.json

jq -r '.predictive_validity_established' \
  experiments/phase1_compiler/results/phase1_mvp_closeout.json
```

Expected:

```text
boltons_paid_smoke_complete_ready_for_phase1_validation_design
write_phase1_validation_design_and_future_holdout_runbook
false
```

3. Run local checks:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

4. Check endpoint variables without making paid calls:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

5. Check current cost:

```bash
jq '.totals' experiments/phase0_headroom/results/workspace_cost_reconciliation.json
```

6. Confirm raw paths are not tracked:

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

7. Write:

```text
experiments/phase1_compiler/results/phase1_future_holdout_preflight.json
```

Include at least:

```json
{
  "schema_version": "barcarolle.phase1.future_holdout_preflight.v1",
  "paid_acut_calls_allowed_after_design_freeze": true,
  "paid_acut_calls_made_in_preflight": false,
  "endpoint_env_required": ["LLM_BASE_URL", "LLM_API_KEY"],
  "cutoff_primary_axis": "repo_task_time",
  "model_release_date_policy": "contamination_guard_only",
  "embargo_gap_days_default": 14,
  "predictive_validity_established": false
}
```

Acceptance:

- all baseline checks pass;
- endpoint env is present after sourcing `~/.zshrc`;
- current observed-or-conservative total is below `USD 80`;
- raw/workspace/external repo paths are not tracked;
- process report records no paid calls yet.

Stop if:

- the Boltons paid smoke decision is missing or does not recommend future
  holdout validation design;
- endpoint env is missing;
- baseline tests fail;
- current cost cannot be bounded.

Commit if preflight artifacts were created:

```text
Record Phase 1 future holdout preflight
```

## Step 1: Write Future Holdout Config

Actions:

Create:

```text
experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml
```

Use this minimum structure:

```yaml
schema_version: barcarolle.phase1_future_holdout_validation.v1
status: configured
claim_scope: future_holdout_design_not_predictive_validity
predictive_validity_established: false

endpoint_rule:
  required_env:
    - LLM_BASE_URL
    - LLM_API_KEY
  local_subscription_fallback: disabled
  openai_api_key_fallback: disabled
  provider_specific_fallback: disabled

cutoff_policy:
  primary_axis: repo_task_time
  model_release_or_snapshot_date_role: contamination_guard_only
  model_snapshot_status: unknown_until_recorded
  embargo_gap_days: 14
  disallow_previous_acut_outcomes_in_clean_validation: true
  disallow_holdout_tuning: true
  disallow_generic_comparators_as_target_holdout: true

eligible_repos:
  primary:
    - boltons
    - toolz
  diagnostic_only:
    - humanize
  excluded_target_holdout:
    - click
    - generic_comparators

source_artifacts:
  boltons_certified_tasks: experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl
  boltons_release: experiments/phase0_headroom/releases/boltons_phase0_pilot_release.json
  toolz_certified_tasks: experiments/phase0_headroom/certified_tasks/toolz_certified_tasks.jsonl
  toolz_release: experiments/phase0_headroom/releases/toolz_phase0_mini_release.json
  hardening_overlay: experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json
  workspace_scorecard: experiments/phase1_compiler/results/phase1_workspace_scorecard.json
  cost_reconciliation: experiments/phase0_headroom/results/workspace_cost_reconciliation.json

clean_split_minimums:
  minimum_b_eval_tasks_per_repo: 2
  minimum_h_future_tasks_per_repo: 2
  preferred_b_eval_tasks_per_repo: 4
  preferred_h_future_tasks_per_repo: 4
  minimum_scoreable_cells_per_split: 3

adapters:
  config: experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
  ids:
    - codex_workspace
    - kilo_workspace

model_design:
  comparison_design: same_model_cross_harness
  preferred_model: gpt-5.4-mini
  model_snapshot_date: null
  model_snapshot_source: null

parallelism:
  paid_acut_concurrency: 1
  allow_cross_harness_paid_parallelism: false

budget:
  conservative_cell_estimate_usd: 0.50
  minimum_clean_validation_cells: 8
  preferred_clean_validation_cells: 16
  incremental_hard_cap_usd: 20.00
  total_observed_or_conservative_stop_cap_usd: 80.00

result_prefixes:
  b_eval: phase1_future_holdout_b_eval
  h_future: phase1_future_holdout_h_future

acceptance:
  policy_violations_max: 0
  usage_observed_rate_min: 0.85
  non_scoreable_cells_max_per_split: 2
  predictive_validity_claim_min_repos: 2
  predictive_validity_claim_min_holdout_scoreable_cells: 12
```

Acceptance:

- config states repo-time cutoff is primary;
- model date is only a contamination guard;
- paid concurrency is `1`;
- previous ACUT outcomes are explicitly disallowed for clean validation;
- Humanize is diagnostic-only unless source provenance is repaired;
- config does not claim predictive validity.

Commit:

```text
Configure Phase 1 future holdout validation
```

## Step 2: Implement Clean-Supply And Cutoff Tooling

If no existing tool fully supports this, add:

```text
experiments/phase1_compiler/tools/phase1_future_holdout.py
experiments/phase1_compiler/tests/test_phase1_future_holdout.py
```

Required commands:

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

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_future_holdout.py \
  score \
  --config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml
```

The `score` command may produce `not_run` if paid result prefixes do not exist.

Tooling requirements:

1. Load certified task rows from committed sanitized JSONL.

2. Parse `task_time` as an aware timestamp when present.

3. Read observed ACUT outcomes from:

```text
experiments/phase1_compiler/results/phase1_workspace_scorecard.json
experiments/phase0_headroom/results/*_score_table.csv
```

4. Mark a task as outcome-seen if any existing score table or workspace
   scorecard contains that task id for a paid or workspace ACUT result.

5. Exclude outcome-seen tasks from clean `B_eval` and clean `H_future`.

6. Exclude generic comparator rows and Humanize validation-grade use.

7. For each eligible repo, sort clean validation-grade tasks by `task_time`.

8. Try candidate cutoffs that satisfy:

```text
len(clean tasks with task_time <= T_compile_end) >= preferred_b_eval_tasks_per_repo
len(clean tasks with task_time >= T_compile_end + embargo_gap) >= preferred_h_future_tasks_per_repo
```

9. If preferred counts fail, try minimum counts.

10. If minimum counts fail, write a blocker decision instead of paid tasks.

11. Record why each task is ineligible:

```text
previous_acut_outcome_seen
missing_task_time
not_benchmark_grade_or_hardening_rejected
diagnostic_only_source_provenance
generic_comparator
outside_cutoff_window
```

12. Write:

```text
experiments/phase1_compiler/results/phase1_future_holdout_clean_supply.json
experiments/phase1_compiler/reports/phase1_future_holdout_clean_supply.md
experiments/phase1_compiler/results/phase1_future_holdout_cutoff_plan.json
```

The cutoff plan must include:

```json
{
  "schema_version": "barcarolle.phase1.future_holdout_cutoff_plan.v1",
  "cutoff_primary_axis": "repo_task_time",
  "embargo_gap_days": 14,
  "model_snapshot_status": "known|unknown",
  "selected_repos": [],
  "repo_plans": {
    "boltons": {
      "T_compile_end": "...",
      "T_holdout_start": "...",
      "b_eval_task_ids": [],
      "h_future_task_ids": [],
      "clean_validation_ready": false
    }
  },
  "predictive_validity_established": false
}
```

Unit tests must cover:

- repo-time sorting;
- embargo calculation;
- exclusion of previously observed ACUT outcomes;
- exclusion of Humanize validation-grade use;
- fallback from preferred to minimum counts;
- blocker output when clean supply is insufficient;
- model snapshot unknown does not block repo-time validation but does block
  contamination-proof claims.

Acceptance:

- tests pass;
- clean supply report lists eligible and excluded tasks by repo;
- cutoff plan is deterministic;
- no paid calls have run in this step.

Commit:

```text
Add Phase 1 future holdout cutoff tooling
```

## Step 3: Audit Clean Supply

Actions:

Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_future_holdout.py \
  audit-supply \
  --config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml
```

Inspect:

```bash
jq '{selected_repos, clean_supply_ready, repo_summary, blockers}' \
  experiments/phase1_compiler/results/phase1_future_holdout_clean_supply.json
```

The report must explicitly answer:

- How many certified tasks exist per repo?
- How many are validation-grade after current hardening rules?
- How many have previously observed ACUT outcomes?
- How many are still clean and outcome-unseen?
- Does any repo have enough clean tasks for both `B_eval` and `H_future`?

Expected risk:

The current Boltons hardened set may already have paid outcomes from the smoke
and extension run. If so, do not reuse those tasks as clean holdout. Report this
as a clean-supply blocker unless enough other validation-grade tasks remain.

Acceptance:

- all exclusions are explained by reason;
- clean-supply readiness is based on outcome-unseen tasks only;
- report does not count already observed Boltons paid smoke cells as clean
  future holdout.

Branch:

- If at least one repo meets minimum clean supply, continue to Step 4.
- If no repo meets minimum clean supply, skip paid validation, continue to Step
  9 with decision `future_holdout_supply_blocked`.

Commit:

```text
Audit Phase 1 clean future holdout supply
```

## Step 4: Select And Freeze Cutoff

Actions:

Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_future_holdout.py \
  design-cutoff \
  --config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml
```

Inspect:

```bash
jq '.' experiments/phase1_compiler/results/phase1_future_holdout_cutoff_plan.json
```

Selection rules:

1. Prefer the earliest `T_compile_end` that leaves the preferred number of clean
   `H_future` tasks.

2. If preferred counts fail, use the earliest `T_compile_end` that leaves the
   minimum number of clean `H_future` tasks.

3. `T_holdout_start` must be `T_compile_end + embargo_gap_days`.

4. `B_eval` tasks must have `task_time <= T_compile_end`.

5. `H_future` tasks must have `task_time >= T_holdout_start`.

6. If reliable `model_snapshot_date` is recorded, `H_future.task_time` must be
   after that date. If this removes too many tasks, stop with
   `future_holdout_model_date_supply_blocked`.

7. If `model_snapshot_status=unknown`, proceed only with the claim boundary
   `repo_time_holdout_not_contamination_proof`.

Acceptance:

- cutoff plan lists exact task ids for `B_eval` and `H_future`;
- no task appears in both splits;
- no selected task has previous ACUT outcome;
- split assignment is stable if the command is rerun;
- plan records whether this is minimum or preferred validation.

Stop if:

- no clean cutoff satisfies the minimum split counts;
- any selected task has previous ACUT outcome;
- model snapshot is known and all holdout tasks are earlier than it.

Commit:

```text
Freeze Phase 1 future holdout cutoff plan
```

## Step 5: Pre-register Predictor And Metrics

Actions:

Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_future_holdout.py \
  preregister \
  --config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml
```

Write:

```text
experiments/phase1_compiler/results/phase1_future_holdout_preregistration.json
experiments/phase1_compiler/reports/phase1_future_holdout_preregistration.md
```

The preregistration must freeze:

```text
selected repos
T_compile_end per repo
T_holdout_start per repo
B_eval task ids
H_future task ids
ACUT adapters
model name
endpoint rule
budget caps
retry policy
scoreability policy
baselines
metrics
claim thresholds
```

Minimum predictor:

```text
For each ACUT adapter:
  predicted_holdout_pass_rate = scoreable pass rate on B_eval

If B_eval has module/task_type strata with enough cells:
  weighted predictor = sum(target_profile_weight_s * observed_pass_rate_s)

If strata are underpowered:
  report weighted predictor as diagnostic only and use unweighted B_eval
  pass rate as the primary pilot predictor.
```

Baselines:

```text
Repo_unweighted:
  unweighted pass rate on B_eval.

Repo_stratified:
  stratified by module_or_package when at least two strata have scoreable cells.

Historical_sidecar:
  prior Toolz/Humanize/Boltons operational scorecards, diagnostic only.
```

Metrics:

```text
MAE between predicted pass rate and H_future pass rate
absolute error per adapter
binomial interval coverage, if enough cells
scoreable cell counts
policy violation counts
non-scoreable cell counts
cost and latency summaries
```

Predictive-validity claim threshold for this pilot:

```text
Do not claim predictive_validity_established unless:
  at least 2 target repos have clean validation,
  H_future has at least 12 total scoreable cells,
  policy violations are 0,
  and the pre-registered Barcarolle predictor beats the unweighted baseline.
```

If only one repo or fewer than 12 holdout scoreable cells are available, the
maximum allowed claim is:

```text
future_holdout_validation_smoke_complete
insufficient_sample_for_predictive_validity
```

Acceptance:

- preregistration exists before paid validation;
- it names exact task ids and metrics;
- it forbids retuning on holdout outcomes;
- it keeps predictive validity false unless thresholds are met.

Commit:

```text
Preregister Phase 1 future holdout validation
```

## Step 6: Adapter Preflight

Run this step only if Step 5 passed.

Actions:

1. Preflight Codex:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --result-prefix phase1_future_holdout_design_codex_preflight'
```

2. Preflight Kilo:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --result-prefix phase1_future_holdout_design_kilo_preflight'
```

3. Inspect:

```bash
jq '{status, adapter_id, endpoint_proof_status, required_env_present, local_subscription_fallback, openai_or_provider_fallback, blockers}' \
  experiments/phase0_headroom/results/phase1_future_holdout_design_codex_preflight_preflight.json

jq '{status, adapter_id, endpoint_proof_status, required_env_present, local_subscription_fallback, openai_or_provider_fallback, blockers}' \
  experiments/phase0_headroom/results/phase1_future_holdout_design_kilo_preflight_preflight.json
```

Acceptance:

- both adapter preflights have `status=ready`;
- `required_env_present=true`;
- endpoint proof is eligible for both adapters;
- local subscription and provider fallback are disabled;
- no paid task-solving cell has run yet in this runbook.

Stop if:

- either preflight is not ready;
- either adapter cannot prove endpoint-backed operation;
- either adapter would use local subscription auth or a fallback endpoint.

Commit:

```text
Record Phase 1 future holdout adapter preflight
```

## Step 7: Run B_eval Paid Cells

Run this step only after preregistration and adapter preflight pass.

Actions:

1. Extract `B_eval` task ids from:

```text
experiments/phase1_compiler/results/phase1_future_holdout_preregistration.json
```

2. Run Codex sequentially:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml \
  --result-prefix phase1_future_holdout_b_eval \
  $(jq -r ".splits.b_eval[] | \"--task-id \" + ." experiments/phase1_compiler/results/phase1_future_holdout_preregistration.json) \
  --timeout-seconds 900'
```

If shell substitution is awkward, manually repeat `--task-id` for each frozen
`B_eval` task id. Do not add task ids not present in the preregistration.

3. Run Kilo sequentially with the same frozen `B_eval` task ids:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml \
  --result-prefix phase1_future_holdout_b_eval \
  $(jq -r ".splits.b_eval[] | \"--task-id \" + ." experiments/phase1_compiler/results/phase1_future_holdout_preregistration.json) \
  --timeout-seconds 900'
```

4. Import usage:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_usage_import.py \
  --root . \
  --result-prefix codex_kilo_workspace \
  --result-prefix codex_kilo_workspace_followup_smoke \
  --result-prefix codex_kilo_workspace_followup \
  --result-prefix kilo_completion_probe \
  --result-prefix codex_kilo_workspace_stability \
  --result-prefix humanize_pre_phase1_workspace \
  --result-prefix phase1_validation_humanize_holdout_smoke \
  --result-prefix phase1_validation_humanize_holdout \
  --result-prefix phase1_validation_humanize_holdout_stability \
  --result-prefix phase1_validation_boltons_paid_smoke \
  --result-prefix phase1_validation_boltons_paid_extension \
  --result-prefix phase1_future_holdout_b_eval \
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --allow-missing-price-estimate
```

5. Summarize:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . summarize \
  --result-prefix phase1_future_holdout_b_eval
```

6. Inspect:

```bash
jq '{total_cells, scoreable_cell_count, terminal_status_counts, split_metrics, harness_metrics}' \
  experiments/phase0_headroom/results/phase1_future_holdout_b_eval_metrics.json

jq '.totals' experiments/phase0_headroom/results/workspace_cost_reconciliation.json
```

Acceptance:

- all submitted task ids match preregistration;
- scoreable cells are at least the preregistered minimum for `B_eval`;
- policy violations are `0`;
- non-scoreable cells do not exceed preregistered max;
- observed-or-conservative total remains below `USD 80`.

Stop if:

- task ids differ from preregistration;
- policy violations occur;
- both adapters have systemic non-scoreable failure;
- cost cannot be bounded.

Commit:

```text
Run Phase 1 future holdout B_eval cells
```

## Step 8: Run H_future Paid Cells

Run this step only if Step 7 passes. Do not change the predictor, task set,
weights, retry policy, or acceptance thresholds after seeing `B_eval` results.

Actions:

1. Extract `H_future` task ids from:

```text
experiments/phase1_compiler/results/phase1_future_holdout_preregistration.json
```

2. Run Codex sequentially:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml \
  --result-prefix phase1_future_holdout_h_future \
  $(jq -r ".splits.h_future[] | \"--task-id \" + ." experiments/phase1_compiler/results/phase1_future_holdout_preregistration.json) \
  --timeout-seconds 900'
```

3. Run Kilo sequentially:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml \
  --result-prefix phase1_future_holdout_h_future \
  $(jq -r ".splits.h_future[] | \"--task-id \" + ." experiments/phase1_compiler/results/phase1_future_holdout_preregistration.json) \
  --timeout-seconds 900'
```

4. Import usage:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_usage_import.py \
  --root . \
  --result-prefix codex_kilo_workspace \
  --result-prefix codex_kilo_workspace_followup_smoke \
  --result-prefix codex_kilo_workspace_followup \
  --result-prefix kilo_completion_probe \
  --result-prefix codex_kilo_workspace_stability \
  --result-prefix humanize_pre_phase1_workspace \
  --result-prefix phase1_validation_humanize_holdout_smoke \
  --result-prefix phase1_validation_humanize_holdout \
  --result-prefix phase1_validation_humanize_holdout_stability \
  --result-prefix phase1_validation_boltons_paid_smoke \
  --result-prefix phase1_validation_boltons_paid_extension \
  --result-prefix phase1_future_holdout_b_eval \
  --result-prefix phase1_future_holdout_h_future \
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --allow-missing-price-estimate
```

5. Summarize:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . summarize \
  --result-prefix phase1_future_holdout_h_future
```

Acceptance:

- all submitted task ids match preregistration;
- scoreable cells are at least the preregistered minimum for `H_future`;
- policy violations are `0`;
- observed-or-conservative total remains below `USD 80`;
- the process report states that no predictor rule was changed after `B_eval`.

Stop if:

- task ids differ from preregistration;
- policy violations occur;
- holdout cells are not scoreable enough for the preregistered metrics;
- cost cannot be bounded.

Commit:

```text
Run Phase 1 future holdout validation cells
```

## Step 9: Score And Decide

Actions:

Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_future_holdout.py \
  score \
  --config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml
```

Expected outputs:

```text
experiments/phase1_compiler/results/phase1_future_holdout_prediction_metrics.json
experiments/phase1_compiler/reports/phase1_future_holdout_prediction_metrics.md
experiments/phase1_compiler/results/phase1_future_holdout_decision.json
experiments/phase1_compiler/reports/phase1_future_holdout_decision.md
```

The metrics must include:

```text
B_eval scoreable cells
H_future scoreable cells
adapter-level predicted pass rate
adapter-level holdout pass rate
absolute error
MAE
baseline comparison if available
policy violation count
non-scoreable count
cost summary
claim boundary
```

Decision labels:

```text
future_holdout_supply_blocked
future_holdout_design_frozen_ready_for_paid_validation
future_holdout_validation_smoke_complete_insufficient_sample
future_holdout_validation_complete_predictive_validity_not_established
future_holdout_validation_complete_candidate_for_scaleup
```

Do not use `predictive_validity_established` unless all preregistered claim
thresholds pass.

Acceptance:

- decision report names the exact selected cutoff policy;
- if no paid validation ran, decision explains the clean-supply blocker;
- if paid validation ran, metrics are computed only from preregistered splits;
- disallowed claims remain disallowed unless thresholds pass;
- next recommended runbook is concrete.

Commit:

```text
Summarize Phase 1 future holdout validation
```

## Step 10: Refresh Phase 1 Boundary

Actions:

1. Extend the Phase 1 compiler boundary only as needed so current closeout and
   scorecard can import the future-holdout decision as sidecar evidence.

2. Rebuild:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  build-mvp \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

3. Validate:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

The refreshed closeout must preserve:

```text
predictive_validity_established=false
production_ranking_status=not_produced
```

unless the Step 9 decision legitimately meets all preregistered predictive
validity thresholds.

Acceptance:

- Phase 1 compiler validation returns `status=valid`;
- future-holdout evidence is labeled as preregistered design, blocker, smoke, or
  validation, not silently folded into old operational scorecards;
- existing Boltons paid smoke remains operational sidecar evidence;
- Humanize remains diagnostic-only unless separately repaired.

Commit:

```text
Refresh Phase 1 boundary after future holdout validation
```

## Step 11: Final Verification

Actions:

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
- process report records every branch taken;
- final decision JSON and report are committed;
- no push is performed.

Final response from the worker should include:

- final decision label;
- selected repos and cutoff dates, if any;
- `B_eval` and `H_future` task ids, if paid validation ran;
- scoreable cell counts and policy violations;
- observed-or-conservative total cost and incremental cost;
- whether predictive validity remains false;
- recommended next runbook.

## Expected Branches

### Clean-Supply Blocker

Likely if all current validation-grade Boltons tasks already have paid ACUT
outcomes, and Toolz has no clean outcome-unseen validation-grade tasks.

Required final decision:

```text
future_holdout_supply_blocked
```

Allowed next runbook:

```text
mine_and_certify_fresh_outcome_unseen_tasks_for_future_holdout
```

Do not run paid validation in this branch.

### Design Frozen, Paid Validation Deferred

Use this if clean supply exists and preregistration succeeds, but endpoint,
budget, adapter preflight, or user policy prevents paid cells.

Required final decision:

```text
future_holdout_design_frozen_ready_for_paid_validation
```

Allowed next runbook:

```text
run_preregistered_phase1_future_holdout_paid_validation
```

### Future Holdout Smoke Complete

Use this if a minimum clean validation batch runs but sample size is below the
predictive-validity claim threshold.

Required final decision:

```text
future_holdout_validation_smoke_complete_insufficient_sample
```

Allowed claim:

```text
future_holdout_protocol_executable
insufficient_sample_for_predictive_validity
```

### Candidate For Scale-Up

Use this if at least two repos and at least twelve holdout scoreable cells are
available, policy violations are zero, and the preregistered predictor is
computable.

Required final decision:

```text
future_holdout_validation_complete_candidate_for_scaleup
```

Allowed next runbook:

```text
scale_preregistered_phase1_predictive_validation
```

Do not claim predictive validity unless the preregistered baseline comparison
threshold is met.
