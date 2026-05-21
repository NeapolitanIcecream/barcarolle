# Phase 0 Cost Usage And Stability Follow-Up Runbook

Status: follow-up implementation and experiment runbook, 2026-05-21.

This runbook continues after
`docs/experiments/phase-0-kilo-completion-policy-followup-runbook.md`
completed successfully.

Current Phase 0 decision remains:

```text
proceed_regression_benchmark
```

The repaired Codex/Kilo workspace matrix is operationally healthy enough to
continue, but two infrastructure questions must be settled before scaling:

- cost accounting should import observed harness usage instead of relying on
  conservative per-cell estimates;
- stability and scope behavior should be measured before making predictive or
  tuning-feedback claims.

This runbook first repairs usage/cost accounting, then records an explicit
parallelism policy, then reviews the remaining `toolz__hist__010` scope
violation, and only then allows a bounded stability run.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-0-cost-usage-stability-followup-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make cohesive commits after completing one or more related steps.

The previous follow-up repaired Kilo completion and statement-policy rendering:
the repaired Codex/Kilo workspace matrix reached 19/20 scoreable cells, Kilo
had 0/10 timeout rows, and Click test-edit policy violations were eliminated.

Your first goal is cost accounting. Do not run new paid ACUT task-solving calls
until the existing raw Codex/Kilo JSON artifacts are parsed into observed usage
and priced through a repo-local price table. Codex emits turn.completed.usage.
Kilo emits step_finish.part.tokens and part.cost currently reports 0 for the
openai-compatible provider, so price those tokens locally.

All paid LLM and ACUT calls must use LLM_BASE_URL + LLM_API_KEY. If either is
missing, source ~/.zshrc and check again. Do not use local Codex/ChatGPT
subscription auth, OPENAI_API_KEY, OpenRouter variables, or provider-specific
keys unless the user's shell maps them into LLM_API_KEY.

Keep the ACUT boundary intact. Barcarolle prepares workspaces, invokes
configured CLI harnesses, captures git diff, enforces benchmark-side policy,
and verifies in fresh verifier workspaces. Do not implement an agent harness
inside Barcarolle.
```

## Relation To Phase 0

The repaired matrix established that the workspace ACUT protocol is viable for
regression-benchmark work. This follow-up is about measurement quality and
scale control:

- cost/usage accounting determines whether the next batch can be responsibly
  scaled;
- parallelism policy prevents accidental paid-concurrency and shared-result
  races;
- stability repeat or second-repo pilot determines whether the repaired result
  is robust enough to justify the next research phase.

This runbook does not authorize predictive-validity claims by itself.

## Budget Rules

No new paid ACUT calls are allowed until Steps 1 through 3 pass.

Incremental cap after cost accounting is repaired:

- soft cap: `USD 12` observed-or-estimated;
- hard cap: `USD 25` observed-or-estimated;
- stop before any paid batch whose projected incremental spend exceeds
  `USD 8`;
- default paid ACUT concurrency remains `1`;
- do not use parallel paid ACUT calls in this runbook unless the user
  explicitly approves a later update.

Cost calculation order:

1. Use provider-billed dollars if the endpoint or harness exposes them.
2. Otherwise import observed token usage from harness raw JSON and multiply by
   the repo-local price table.
3. Only if usage is missing, estimate with a tokenizer or calibrated fallback.

## Output Layout

Add or update:

```text
experiments/phase0_headroom/
  configs/
    model_pricing.yaml
    parallelism_policy.yaml
    stability_followup_matrix.yaml
  results/
    workspace_usage_ledger.jsonl
    workspace_cost_reconciliation.json
    codex_kilo_workspace_followup_cost_ledger.jsonl
    codex_kilo_workspace_followup_cost_summary.json
    codex_kilo_workspace_stability_submissions.jsonl
    codex_kilo_workspace_stability_verifier_results.jsonl
    codex_kilo_workspace_stability_score_table.csv
    codex_kilo_workspace_stability_cost_ledger.jsonl
    codex_kilo_workspace_stability_cost_summary.json
    codex_kilo_workspace_stability_metrics.json
  reports/
    workspace_cost_usage_report.md
    parallelism_policy.md
    toolz_hist_010_scope_review.md
    codex_kilo_workspace_stability_analysis.md
    phase0_decision_memo.md
```

Raw logs and workspaces must remain ignored:

```text
experiments/phase0_headroom/results/raw/
experiments/phase0_headroom/workspaces/
```

Do not commit raw prompts, full completions, ACUT transcripts, raw patches,
solver workspaces, verifier workspaces, cloned repositories, `.venv`, caches,
or full logs.

## Step 0: Preflight

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`,
   `codex --version`, and `kilo --version`.
2. Verify endpoint variables without using them yet:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

3. Confirm the repaired follow-up artifacts exist:

```text
experiments/phase0_headroom/results/codex_kilo_workspace_followup_score_table.csv
experiments/phase0_headroom/results/codex_kilo_workspace_followup_submissions.jsonl
experiments/phase0_headroom/results/codex_kilo_workspace_followup_verifier_results.jsonl
experiments/phase0_headroom/results/codex_kilo_workspace_followup_cost_summary.json
experiments/phase0_headroom/reports/codex_kilo_workspace_followup_analysis.md
experiments/phase1_compiler/results/toolz_phase1_weighted_score.json
```

4. Run:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
git status --short --ignored experiments/phase0_headroom experiments/phase1_compiler docs/experiments AGENTS.md .gitignore
```

Acceptance:

- endpoint variables are present;
- current tests pass;
- repaired matrix artifacts are present;
- only ignored raw/workspace/cache/venv artifacts appear as ignored untracked
  files.

Stop if:

- endpoint variables are missing after sourcing `~/.zshrc`;
- Phase 0 or Phase 1 tests fail;
- repaired follow-up artifacts are missing.

## Step 1: Add Model Pricing Table

Create:

```text
experiments/phase0_headroom/configs/model_pricing.yaml
```

Minimum schema:

```yaml
schema_version: barcarolle.model_pricing.v1
default_currency: USD
prices:
  - endpoint_host_hash: "9952174049b2"
    model: gpt-5.4-mini
    pricing_source: user_estimate_required_conservative_default
    input_rate_per_1m_usd: 3.0
    cached_input_rate_per_1m_usd: 0.3
    output_rate_per_1m_usd: 15.0
    reasoning_output_policy: included_in_output_tokens
    notes: >
      Local estimate used for budgeting and reconciliation when provider-billed
      dollars are unavailable. Does not model volume discounts or tiered
      pricing.
```

Rules:

- `endpoint_host_hash + model` is the lookup key.
- If the model is unknown, the cost tool must fail closed unless explicitly
  passed `--allow-missing-price-estimate`.
- `reasoning_output_policy` must be explicit. Prefer
  `included_in_output_tokens` unless endpoint documentation or raw response
  schema proves reasoning tokens must be billed separately.
- Keep prices editable and reviewable in YAML rather than hard-coded inside a
  script.

Add tests for:

- price lookup by host hash and model;
- missing model failure;
- cost calculation with uncached input, cached input, output, and optional
  reasoning policy.

Acceptance:

- pricing table exists;
- tests pass;
- no paid calls are made.

Commit:

```text
Add workspace model pricing table
```

## Step 2: Import Codex And Kilo Usage From Raw JSON

Create a repo-local tool, for example:

```text
experiments/phase0_headroom/tools/workspace_usage_import.py
```

The tool should read committed result rows plus ignored raw stdout files and
write a sanitized usage ledger.

Inputs:

```text
--result-prefix codex_kilo_workspace
--result-prefix codex_kilo_workspace_followup_smoke
--result-prefix codex_kilo_workspace_followup
--result-prefix kilo_completion_probe
--pricing-config experiments/phase0_headroom/configs/model_pricing.yaml
```

Codex parser:

- parse JSONL stdout rows where `type == "turn.completed"`;
- read `usage.input_tokens`;
- read `usage.cached_input_tokens`;
- read `usage.output_tokens`;
- read `usage.reasoning_output_tokens`;
- associate usage to `run_id` from the raw artifact path or submission row.

Kilo parser:

- parse JSONL stdout rows where `type == "step_finish"`;
- sum `part.tokens.input`;
- sum `part.tokens.output`;
- sum `part.tokens.reasoning`;
- sum `part.tokens.cache.read`;
- sum `part.tokens.cache.write`;
- record `part.cost` separately, but do not trust `0` as billed cost for
  openai-compatible provider;
- associate usage to `run_id` from the raw artifact path or submission row.

Output row schema:

```json
{
  "schema_version": "barcarolle.workspace_usage.v1",
  "run_id": "",
  "result_prefix": "",
  "adapter_id": "",
  "harness_name": "",
  "model_or_agent_name": "",
  "usage_source": "codex_turn_completed|kilo_step_finish|missing",
  "usage_observed": true,
  "input_tokens": 0,
  "cached_input_tokens": 0,
  "uncached_input_tokens": 0,
  "output_tokens": 0,
  "reasoning_output_tokens": 0,
  "reported_cost_usd": null,
  "estimated_cost_usd": 0.0,
  "pricing_source": "",
  "raw_artifact_ref": "sanitized relative path only"
}
```

Write:

```text
experiments/phase0_headroom/results/workspace_usage_ledger.jsonl
experiments/phase0_headroom/results/workspace_cost_reconciliation.json
experiments/phase0_headroom/reports/workspace_cost_usage_report.md
```

Tests:

- parse a Codex `turn.completed` fixture;
- parse a Kilo `step_finish` fixture;
- sum multiple Kilo steps for one run;
- ignore non-JSON or unrelated JSON rows safely;
- fail closed for missing price unless explicitly allowed;
- do not include raw stdout content in committed ledger.

Acceptance:

- repaired follow-up matrix usage observation rate is greater than `0.8`;
- Codex and Kilo usage are both imported;
- `workspace_cost_usage_report.md` compares old conservative estimates against
  observed-token estimates;
- no raw prompts, completions, transcripts, or patches are committed.

Commit:

```text
Import workspace ACUT usage from harness logs
```

## Step 3: Reconcile Existing Cost Summaries

Use the usage importer to update or add measured summaries for existing
workspace ACUT runs.

Required reconciliations:

```text
codex_kilo_workspace
kilo_completion_probe
codex_kilo_workspace_followup_smoke
codex_kilo_workspace_followup
```

For each prefix, write:

- observed-token cost estimate;
- previous conservative estimate;
- usage observed rate;
- number of missing-usage cells;
- per-harness cost;
- per-split cost;
- median latency.

Update existing `*_cost_summary.json` files only if their schema preserves both
the previous conservative estimate and the observed-token estimate. Otherwise
write `workspace_cost_reconciliation.json` and leave the old files untouched.

Recommended summary fields:

```json
{
  "schema_version": "barcarolle.workspace_acut_cost_summary.v2",
  "result_prefix": "",
  "call_count": 0,
  "usage_observed_count": 0,
  "usage_observed_rate": 0.0,
  "conservative_estimated_cost_usd": 0.0,
  "observed_token_estimated_cost_usd": 0.0,
  "actual_provider_billed_cost_usd": null,
  "pricing_source": "",
  "missing_usage_run_ids": [],
  "median_latency_seconds": 0.0
}
```

Acceptance:

- repaired follow-up spend is no longer reported only as `USD 14.50`;
- reports clearly state that provider-billed dollars remain unknown;
- cost estimates distinguish observed-token estimate from conservative
  fallback;
- Phase 0 decision memo points to the new canonical cost report.

Commit:

```text
Reconcile workspace ACUT cost summaries
```

## Step 4: Record Parallelism Policy

Create:

```text
experiments/phase0_headroom/configs/parallelism_policy.yaml
experiments/phase0_headroom/reports/parallelism_policy.md
```

Minimum policy:

```yaml
schema_version: barcarolle.parallelism_policy.v1
max_paid_acut_concurrency: 1
max_local_checkout_concurrency: 4
max_local_verify_concurrency: 4
allow_cross_harness_paid_parallelism: false
require_usage_import_before_paid_parallelism: true
require_file_lock_for_shared_results: true
shared_result_write_mode: single_writer
```

Document the rationale:

- local checkout, oracle extraction, no-op/reference, and verifier replay may
  eventually parallelize because they do not call paid LLM endpoints;
- paid ACUT task solving remains sequential until usage import, rate limiting,
  and shared-result file locking are implemented;
- Codex and Kilo should not be run in paid parallel against the same endpoint
  yet because endpoint rate limits, cache behavior, cost spikes, and Kilo
  completion behavior would be confounded.

Acceptance:

- the policy is explicit and machine-readable;
- current runbooks do not accidentally authorize paid parallelism;
- no new paid calls are made.

Commit:

```text
Record Phase 0 parallelism policy
```

## Step 5: Review `toolz__hist__010` Scope Violation

The only repaired-matrix policy violation was:

```text
kilo_workspace x toolz__hist__010
submission_edited_out_of_scope_paths:
  - toolz/__init__.py
  - toolz/curried/__init__.py
```

Review whether package export files should be allowed for this task.

Actions:

1. Inspect the solver-facing statement, reference commit diff, hidden verifier,
   and previous Kilo/Codex diffs.
2. Decide whether updating package exports is:
   - necessary public API behavior for `pipeline`;
   - optional but acceptable implementation scope;
   - out-of-scope and correctly rejected.
3. If package exports are allowed, update task metadata and policy tests so
   the allowed paths are explicit:

```text
toolz/functoolz.py
toolz/__init__.py
toolz/curried/__init__.py
```

4. If package exports are not allowed, keep the policy violation and document
   why.
5. Do not weaken the global test-edit policy.

Write:

```text
experiments/phase0_headroom/reports/toolz_hist_010_scope_review.md
```

Acceptance:

- the review gives a clear allow/reject decision;
- any metadata change is covered by tests;
- no hidden verifier material becomes solver-visible;
- test-edit rejection remains unchanged.

Commit one of:

```text
Review toolz hist 010 export scope
```

```text
Allow toolz hist 010 package export paths
```

## Step 6: Decide Stability Run Shape

Choose exactly one path after Steps 1 through 5 pass.

Preferred path A: repaired matrix repeat.

Use this if:

- cost usage import is working;
- estimated repeat cost is within the soft cap;
- `toolz__hist__010` scope decision is recorded;
- the goal is run-to-run stability for the same task set.

Path B: second target-repository pilot.

Use this if:

- a small second repo task package already exists or can be prepared without
  large task-generator work;
- the goal is reducing Toolz task clustering;
- the worker can keep the pilot smaller than the cost cap.

Do not do both paths in this runbook unless the user explicitly approves.

Write:

```text
experiments/phase0_headroom/configs/stability_followup_matrix.yaml
```

Required fields:

```yaml
schema_version: barcarolle.stability_followup_matrix.v1
selected_path: repaired_matrix_repeat|second_repo_pilot|stop
reason: ""
budget:
  projected_observed_token_cost_usd: 0.0
  conservative_fallback_cost_usd: 0.0
  hard_cap_usd: 25
parallelism:
  paid_acut_concurrency: 1
```

Acceptance:

- the selected path is justified by observed cost and current validity needs;
- projected cost is recorded from the new cost accounting path;
- paid ACUT concurrency remains `1`.

Commit:

```text
Configure Phase 0 stability follow-up
```

## Step 7A: Repaired Matrix Repeat

Run only if Step 6 selected `repaired_matrix_repeat`.

Repeat the repaired Codex/Kilo 20-cell matrix with:

```text
result_prefix: codex_kilo_workspace_stability
```

Use the current repaired protocol:

- Codex workspace adapter;
- Kilo workspace adapter with `strict-final`;
- same endpoint model `gpt-5.4-mini`;
- same task set as `codex_kilo_workspace_followup`;
- paid ACUT concurrency `1`;
- observed usage import after the run.

Acceptance:

- every scheduled cell has terminal status;
- scoreable cells are at least `18/20`;
- Kilo timeout rows remain `0/10` or at most `1/10`;
- Click test-edit policy violations remain `0`;
- if `toolz__hist__010` exports were allowed, the Kilo cell is no longer a
  policy violation for package export edits;
- cost summary uses observed-token estimate where available.

Write:

```text
experiments/phase0_headroom/results/codex_kilo_workspace_stability_submissions.jsonl
experiments/phase0_headroom/results/codex_kilo_workspace_stability_verifier_results.jsonl
experiments/phase0_headroom/results/codex_kilo_workspace_stability_score_table.csv
experiments/phase0_headroom/results/codex_kilo_workspace_stability_cost_ledger.jsonl
experiments/phase0_headroom/results/codex_kilo_workspace_stability_cost_summary.json
experiments/phase0_headroom/results/codex_kilo_workspace_stability_metrics.json
experiments/phase0_headroom/reports/codex_kilo_workspace_stability_analysis.md
```

Commit:

```text
Run Codex Kilo workspace stability repeat
```

## Step 7B: Second Target-Repository Pilot

Run only if Step 6 selected `second_repo_pilot`.

The pilot should be small and should not turn Barcarolle into a general task
factory. Use the existing task certification methodology and stop if suitable
source material is not already available.

Minimum shape:

- `3` to `6` certified same-repo tasks from one second repository;
- no more than `2` generic comparator tasks unless already available;
- Codex and Kilo workspace ACUT cells only after task certification passes;
- paid ACUT concurrency `1`;
- observed usage import after the run.

Acceptance:

- task certification includes checkout, oracle extract, no-op/reference,
  known-bad fail, flakiness, ambiguity, leakage, scope clarity, cost
  boundedness, and taxonomy gates;
- scoreable protocol is workspace ACUT adapter, not diff-only prompting;
- no predictive-validity claim is made from the pilot alone;
- report explains whether the second repo reduces clustering enough to justify
  a larger Phase 1 plan.

Commit:

```text
Run second repository workspace ACUT pilot
```

## Step 8: Update Phase 0 Decision

Update:

```text
experiments/phase0_headroom/reports/phase0_decision_memo.md
```

Allowed decisions:

- `proceed_regression_benchmark`;
- `proceed_tuning_feedback`;
- `proceed_predictive`;
- `repair_cost_accounting`;
- `repair_scope_policy`;
- `stop`.

Decision guidance:

- Use `repair_cost_accounting` if usage import cannot reliably parse Codex and
  Kilo raw JSON.
- Use `repair_scope_policy` if `toolz__hist__010` exposes a broader
  allowed-path ambiguity that affects many tasks.
- Keep `proceed_regression_benchmark` if cost accounting and stability improve
  but evidence remains small or clustered.
- Use `proceed_tuning_feedback` only if the stability repeat or second repo
  pilot supports harness-selection or repo-specific optimization claims.
- Use `proceed_predictive` only if the evidence base is substantially larger
  and no longer dominated by a single target repository or recovered comparator
  set.

Acceptance:

- memo names the canonical cost report;
- memo states whether stability was repeated or second repo pilot was run;
- memo does not overclaim predictive validity.

Commit:

```text
Update Phase 0 decision after cost and stability follow-up
```

## Step 9: Final Hygiene

Actions:

1. Run:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
test ! -d experiments/phase1_compiler || uv run --project experiments/phase1_compiler pytest -q
git status --short --ignored experiments/phase0_headroom experiments/phase1_compiler docs/experiments AGENTS.md .gitignore
```

2. Confirm no raw prompts, full completions, ACUT transcripts, raw patches,
   solver workspaces, verifier workspaces, cloned repositories, `.venv`,
   caches, or full logs are staged.
3. Ensure the final report states:
   - observed-token cost for existing workspace ACUT runs;
   - conservative-vs-observed cost delta;
   - parallelism policy;
   - `toolz__hist__010` scope decision;
   - whether a stability repeat or second-repo pilot was run;
   - next smallest useful experiment.

Final commit:

```text
Summarize Phase 0 cost and stability follow-up
```

Do not push unless the user explicitly asks.

## Success Criteria

Best case:

- Codex and Kilo usage are imported from raw harness JSON;
- existing follow-up cost is reconciled with observed-token estimates;
- paid parallelism remains controlled by a machine-readable policy;
- `toolz__hist__010` scope is clarified;
- a repaired matrix repeat or second repo pilot strengthens stability evidence.

Good fallback:

- usage importer works and cost summaries are repaired;
- stability run is deferred because scope or budget gates fail;
- Phase 0 remains `proceed_regression_benchmark` with clearer measurement.

Unacceptable outcomes:

- making new paid ACUT calls before usage/cost accounting is repaired;
- relying only on tokenizer estimates when harness usage is available;
- using local Codex/ChatGPT subscription auth as scoreable evidence;
- relaxing test-edit policy to improve scoreability;
- enabling paid parallel ACUT calls without usage import, file locking, and
  explicit user approval;
- claiming predictive validity from a single repeated Toolz matrix.
