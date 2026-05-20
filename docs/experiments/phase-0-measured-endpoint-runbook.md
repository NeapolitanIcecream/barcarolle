# Phase 0 Measured Endpoint Runbook

Status: operating runbook, 2026-05-20.

This runbook replaces the earlier ad hoc Codex-subscription ACUT path for future
Phase 0 execution. Its job is to finish Phase 0 with measured cost data and a
clear scale-up decision.

All LLM and ACUT calls in this runbook must use the OpenAI-compatible endpoint
configured by:

```text
LLM_BASE_URL
LLM_API_KEY
```

If those variables are missing in the worker shell, source `~/.zshrc` before
running any LLM command. Do not fall back to the local Codex/ChatGPT subscription,
`OPENAI_API_KEY`, OpenRouter variables, or any project-specific API variable
unless the user explicitly changes this rule.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-0-measured-endpoint-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.

All LLM and ACUT calls must use LLM_BASE_URL + LLM_API_KEY. If either variable is
missing, source ~/.zshrc and check again. Do not use the local Codex/ChatGPT
subscription path. Do not use OPENAI_API_KEY or other provider-specific
environment variables unless this runbook is updated by the user.

First discover the models supported by LLM_BASE_URL, then select ACUT models only
from that discovered model set. Record token usage, cached input tokens if
reported, output tokens, latency, status, and estimated cost for every LLM call.

Run Phase 0 to a defensible closeout under the USD 200 hard cap. Use the current
Phase 0 artifacts when valid, but rerun or repair any stage whose evidence is
stale, incompatible with the measured endpoint, or missing generic-comparator
protocol support.

Before spending on larger matrices, run a small calibration batch and use the
measured cost per scoreable cell to decide whether to scale task count, ACUT
count, or stop.

Commit cohesive checkpoints. Do not commit API keys, full prompts, raw model
responses, raw transcripts, cloned repositories, .venv, caches, or full
workspaces.
```

## Relationship To Earlier Phase 0 Work

The previous Phase 0 run proved that Barcarolle can create a small certified
`toolz` regression slice and score six same-repo ACUT cells. It did not provide
reliable dollar cost measurement because the ACUT path used local Codex CLI
authentication. It also did not score `G_mini` under the same protocol.

This runbook keeps the useful Phase 0 evidence chain:

- target-profile mismatch;
- task supply and certification;
- mini release assembly;
- same-repo and generic-comparator protocol checks;
- budgeted ACUT scoring;
- canonical decision memo.

It changes the execution contract:

- ACUTs must run through `LLM_BASE_URL + LLM_API_KEY`;
- model choices must come from the endpoint's discovered model list;
- token and cost measurements must be first-class artifacts;
- scale-up decisions must be based on observed cost per scoreable cell.

## Hard Rules

1. Never print or commit `LLM_API_KEY`.
2. Never record full raw prompts or raw completions in committed artifacts.
3. Do not use `codex exec` as the ACUT unless it is configured to call the
   required endpoint through `LLM_BASE_URL + LLM_API_KEY` and the run records
   endpoint token usage.
4. Do not use `OPENAI_API_KEY` as a fallback.
5. Do not use `OPENROUTER_API_KEY`, `BARCAROLLE_LLM_API_KEY`,
   `KIPERINA_LLM_API_KEY`, or similar variables unless they are explicitly
   copied into `LLM_API_KEY` by the user's shell configuration.
6. All model names used in ACUT runs must appear in the endpoint model discovery
   output or in a user-approved endpoint model override.
7. Do not scale beyond the calibration batch until measured cost is recorded.

## Budget Rules

Hard cap: USD 200 total measured or estimated LLM spend for this Phase 0 run.

Budget bands:

- USD 0-10: endpoint discovery, smoke tests, and model probes;
- USD 0-30: optional statement cleanup or review help, only if needed;
- USD 0-40: generic-comparator protocol repair probes;
- USD 0-120: measured ACUT matrix runs;
- USD 40 reserve: reruns, failed calls, or cost-model error.

Stop rules:

- Stop before any batch whose projected cumulative cost exceeds USD 160.
- Stop and ask before projected cumulative cost exceeds USD 180.
- Never exceed USD 200.
- Do not run parallel paid ACUT batches.
- Do not use LLM calls for deterministic extraction, CSV/JSON formatting, row
  counting, or metrics computation.

If the endpoint does not report usage tokens, mark `usage_observed: false`,
estimate conservatively from prompt/output byte counts, and do not scale beyond
the calibration batch without user approval.

## Output Layout

Create or update these artifacts:

```text
experiments/phase0_headroom/
  configs/
    endpoint.yaml
    model_selection.yaml
    measured_budget.yaml
    headroom_matrix.yaml
  results/
    endpoint_models.json
    endpoint_smoke_tests.jsonl
    measured_cost_ledger.jsonl
    measured_cost_summary.json
    cost_realignment.json
    generic_comparator_protocol.json
    headroom_score_table.csv
    headroom_metrics.json
    headroom_matrix.json
  reports/
    endpoint_preflight.md
    model_selection.md
    measured_cost_report.md
    generic_comparator_protocol.md
    headroom_analysis.md
    phase0_decision_memo.md
```

The existing `results/cost_ledger.jsonl` may be preserved for historical
continuity, but the measured endpoint run must write
`results/measured_cost_ledger.jsonl`.

## Step 0: Endpoint Preflight

Actions:

1. Start a zsh shell and source `~/.zshrc` if needed:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

2. Verify `LLM_BASE_URL` and `LLM_API_KEY` are present.
3. Record only safe endpoint metadata:
   - whether `LLM_BASE_URL` is present;
   - redacted host or host hash;
   - whether the key is present;
   - key fingerprint as a short hash, never the key;
   - timestamp and shell.
4. Create `configs/endpoint.yaml`.
5. Confirm no ACUT path uses local Codex/ChatGPT auth by default.

Outputs:

- `configs/endpoint.yaml`
- `reports/endpoint_preflight.md`

Acceptance:

- `LLM_BASE_URL` and `LLM_API_KEY` are present after sourcing shell config;
- no secret value is written to disk;
- the report states that local Codex subscription fallback is disabled.

Stop if:

- either variable is missing after sourcing `~/.zshrc`;
- the only available route is local Codex/ChatGPT auth;
- the worker cannot prevent secrets from being logged.

## Step 1: Discover Endpoint Models

Actions:

1. Query the endpoint's model list. For an OpenAI-compatible endpoint, try:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
curl -sS "$LLM_BASE_URL/models" \
  -H "Authorization: Bearer $LLM_API_KEY"'
```

If `LLM_BASE_URL` already includes `/v1` and `/models` fails, try the endpoint's
documented equivalent. Record which path worked.

2. Save a sanitized model list to `results/endpoint_models.json`.
3. Run a cheap smoke request for candidate models that look suitable for code
   editing. Record:
   - model id;
   - API path used;
   - success/failure;
   - latency;
   - context-window hints if available;
   - whether token usage is reported;
   - whether tool calls or JSON mode are supported if needed.
4. Select one primary cheap ACUT model and, optionally, one stronger comparison
   model. Selection must be from discovered models unless the user approves an
   override.

Outputs:

- `results/endpoint_models.json`
- `results/endpoint_smoke_tests.jsonl`
- `configs/model_selection.yaml`
- `reports/model_selection.md`

Acceptance:

- selected ACUT model ids appear in the discovered endpoint model list or a
  user-approved override;
- at least one selected model can complete a simple code-edit smoke prompt;
- token usage reporting is known for each selected model.

Stop if:

- no endpoint model can run a code-edit smoke prompt;
- the endpoint does not expose enough model information to choose safely and the
  user has not supplied an override.

## Step 2: Install Cost Measurement

Actions:

1. Implement or update a small measurement utility under
   `experiments/phase0_headroom/tools/` that can parse endpoint responses and
   write records to `results/measured_cost_ledger.jsonl`.
2. Record these fields for every LLM call:

```json
{
  "schema_version": "barcarolle.measured_cost.v1",
  "run_id": "",
  "timestamp": "",
  "phase": "",
  "event": "",
  "endpoint_host_hash": "",
  "model": "",
  "request_api": "",
  "status": "",
  "latency_seconds": 0.0,
  "input_tokens": null,
  "cached_input_tokens": null,
  "output_tokens": null,
  "reasoning_output_tokens": null,
  "usage_observed": false,
  "pricing_source": "",
  "input_rate_per_1m_usd": null,
  "cached_input_rate_per_1m_usd": null,
  "output_rate_per_1m_usd": null,
  "estimated_cost_usd": null,
  "actual_cost_usd": null,
  "artifact_ref": "",
  "notes": ""
}
```

3. Create `configs/measured_budget.yaml` with rate assumptions. If endpoint
   pricing is unknown, set `pricing_source: user_estimate_required` and use
   conservative estimates until the user fills rates.
4. Add tests for token aggregation and cost computation.

Outputs:

- `tools/<measurement utility>`
- `configs/measured_budget.yaml`
- `results/measured_cost_ledger.jsonl`
- `results/measured_cost_summary.json`
- tests under `experiments/phase0_headroom/tools`

Acceptance:

- scoped tests pass;
- one endpoint smoke call produces a measured ledger row;
- cost summary reports both token totals and dollar estimates;
- missing usage tokens are handled explicitly.

## Step 3: Reuse Or Repair Phase 0 Inputs

Actions:

1. Reuse current target profile, supply funnel, certified `toolz` tasks, and
   mini release if they still pass certification and hygiene checks.
2. Re-run deterministic certification checks only if artifacts are stale or
   missing.
3. Keep the current certified task count unless the measured cost model shows
   enough room to expand.
4. Preserve the current `toolz` split as the baseline:
   - `3` `B_real`;
   - `3` `W_real`;
   - `4` `G_mini` comparator records, pending protocol repair.

Outputs:

- updated gate report if needed;
- no changed files if all inputs remain valid.

Acceptance:

- six `toolz` same-repo tasks remain `certified`;
- solver-facing statements and review records pass leakage checks;
- mini release is still `benchmark_grade_candidate`.

Stop if:

- certification regresses;
- solver-facing task statements expose evaluator-private details.

## Step 4: Repair Generic Comparator Protocol

Actions:

1. Materialize or adapt `G_mini` tasks so they use the same ACUT invocation and
   verifier protocol as `toolz`.
2. Use archived Click metadata only as source material. The active `G_mini`
   package must include:
   - solver-facing statement;
   - base checkout or task workspace;
   - oracle/verifier command;
   - certification or provenance status;
   - leakage and scope notes.
3. Dry-run same-protocol scoring without paid LLM calls.
4. Mark each comparator task as:
   - `scoreable_same_protocol`;
   - `scoreable_different_protocol`;
   - `metadata_only`;
   - `not_scoreable`.

Outputs:

- `results/generic_comparator_protocol.json`
- `reports/generic_comparator_protocol.md`
- any small active comparator manifests needed for scoring

Acceptance:

- at least three `G_mini` tasks are `scoreable_same_protocol`, or the report
  explains why the generic comparator remains blocked;
- no paid ACUT call starts for comparator tasks until dry-run scoreability
  passes.

Stop if:

- active comparator materialization would require reviving old core-narrative
  semantics rather than producing Phase 0-compatible tasks.

## Step 5: Calibration Batch

Actions:

1. Run the smallest measured batch through the selected endpoint model:
   - `1` or `2` `B_real` tasks;
   - `1` or `2` `W_real` tasks;
   - `1` `G_mini` task only if generic comparator protocol passed.
2. Record token usage and cost for every call.
3. Verify every submission.
4. Compute:
   - cost per submitted cell;
   - cost per scoreable cell;
   - pass/fail/harness-error counts;
   - median latency;
   - usage-observed rate.

Outputs:

- `results/measured_cost_ledger.jsonl`
- `results/measured_cost_summary.json`
- `results/cost_realignment.json`
- `reports/measured_cost_report.md`

Acceptance:

- at least two same-repo cells are scoreable;
- measured cost per scoreable same-repo cell is available, or usage reporting is
  explicitly blocked;
- no scale-up decision is made without this report.

Stop if:

- endpoint usage reporting is absent and cost cannot be bounded conservatively;
- harness errors dominate the calibration cells.

## Step 6: Cost Realignment And Scale Decision

Use measured cost to choose one path.

Allowed decisions:

- `scale_tasks_same_acut`: cost is low enough to add more certified tasks for
  the same ACUT;
- `scale_acuts_current_tasks`: cost is low enough to add a second endpoint model
  on the current task set;
- `repair_generic_comparator_first`: same-repo is scoreable but `G_mini` is not;
- `stay_diagnostic`: cost, protocol, or task supply supports only the current
  diagnostic scale;
- `stop_phase0`: cost or protocol risk makes further Phase 0 spending
  unjustified.

Default thresholds:

- If measured cost per scoreable cell is below USD 2 and `G_mini` works, scale
  to at least `6` same-repo cells plus `3-4` `G_mini` cells for one ACUT.
- If measured cost per scoreable cell is below USD 1 and certification supply is
  available, consider adding a second endpoint model.
- If `G_mini` is blocked, do not run a second ACUT unless the user explicitly
  waives the generic-comparator requirement.
- If usage is not observed, do not scale beyond the calibration batch without
  user approval.

Outputs:

- `results/cost_realignment.json`
- `reports/measured_cost_report.md`

Acceptance:

- the decision uses observed token/cost data;
- projected cumulative spend stays below USD 160 before any scale-up batch;
- the report says what evidence the scale-up will add.

## Step 7: Run The Approved Matrix

Run only the matrix approved in Step 6.

Actions:

1. Write or update `configs/headroom_matrix.yaml`.
2. Append a projected-cost row before each paid batch.
3. Run endpoint ACUT calls through the measured runner.
4. Store raw responses under ignored paths; commit only sanitized summaries.
5. Verify each submission and write score rows.
6. Append completed-cost rows with observed token usage and estimated dollar
   cost.

Outputs:

- `results/headroom_score_table.csv`
- `results/headroom_matrix.json`
- `results/headroom_metrics.json`
- `results/measured_cost_ledger.jsonl`
- `results/measured_cost_summary.json`
- `reports/headroom_analysis.md`

Acceptance:

- every scheduled cell has a terminal status;
- `verified_fail`, `harness_error`, `invalid_output`, and `timeout` are
  separated;
- `G_mini` comparisons are reported only for same-protocol scoreable cells;
- MAE/RMSE/Brier metrics are reported only when sample size and predictor setup
  justify them. Otherwise mark them `not_applicable_underpowered`.

## Step 8: Final Decision Memo

Update:

```text
experiments/phase0_headroom/reports/phase0_decision_memo.md
```

Use one of the original Phase 0 decisions:

- `proceed_predictive`;
- `proceed_tuning_feedback`;
- `proceed_regression_benchmark`;
- `repair_source_adapter`;
- `stop`.

Decision guidance:

- Use `proceed_predictive` only if same-protocol `G_mini`, `B_real`, and
  `W_real` cells support a real headroom comparison.
- Use `proceed_regression_benchmark` if certification and same-repo scoring work
  but generic comparison or predictive metrics remain underpowered.
- Use `proceed_tuning_feedback` if the benchmark is more useful as optimizer
  feedback than as a regression pack.
- Use `repair_source_adapter` only if certification regresses.
- Use `stop` if cost or protocol risk invalidates further work.

The memo must include:

- endpoint model selection;
- measured token totals;
- estimated and actual cost fields;
- scale decision and rationale;
- headroom result or blocker;
- threats to validity;
- next smallest useful experiment.

## Step 9: Commit Hygiene

Actions:

1. Run:

```bash
git status --short --ignored experiments/phase0_headroom docs/experiments .gitignore
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
```

2. Confirm raw responses, prompts, completions, cloned repos, `.venv`, caches,
   and workspaces are ignored and unstaged.
3. Stage only configs, scripts, sanitized JSONL/JSON/CSV summaries, and reports.
4. Commit cohesive checkpoints:
   - endpoint/model discovery and measurement tooling;
   - generic comparator protocol repair;
   - calibration batch and cost realignment;
   - approved matrix and final decision memo.

Acceptance:

- committed artifacts are small and reviewable;
- no secrets or raw model content are committed;
- measured cost artifacts are present;
- final status is clean except intentionally ignored artifacts.

## Final Success Criteria

Phase 0 is complete under this measured endpoint runbook when the repo contains:

- endpoint preflight and sanitized model discovery;
- selected ACUT model ids from the endpoint's supported model list;
- measured token usage for every LLM call;
- a cost summary and scale decision based on observed data;
- certified same-repo task evidence;
- generic comparator protocol status;
- a budgeted matrix result or precise blocker;
- a canonical Phase 0 decision memo;
- total measured or conservatively estimated spend below USD 200.

If measured cost is much lower than the previous USD 60 conservative estimate,
use that fact to justify a controlled scale-up only after the calibration batch
and only when the next batch answers a specific research question.
