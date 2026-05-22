# Phase 1 Boltons Paid ACUT Smoke Runbook

Status: implementation runbook, 2026-05-22.

This runbook is for one dedicated Codex CLI session. Its job is to run a small
paid workspace-ACUT smoke on the selected replacement third repo, `boltons`,
using the existing Codex and Kilo CLI harness adapters.

This runbook may make paid ACUT calls. It must use only the configured
OpenAI-compatible endpoint:

```text
LLM_BASE_URL
LLM_API_KEY
```

If either variable is missing in the worker shell, source `~/.zshrc` and check
again before any paid call. Do not use local Codex/ChatGPT subscription auth,
`OPENAI_API_KEY`, OpenRouter variables, or provider-specific fallbacks.

## Why This Runbook Exists

The replacement-selection runbook selected `boltons` as the active third repo:

- `boltons` candidate count after filter: `32`
- reviewed non-leaky source statements: `22`
- locally certified tasks: `16`
- B/W split: `8` B_real and `8` W_real
- hardened benchmark-grade candidates: `7`
- final decision: `ready_for_paid_third_repo_acut_smoke_runbook`

The next useful step is a small paid smoke that tests whether the real
Codex/Kilo ACUT harnesses can produce scoreable workspace diffs on those
hardened Boltons tasks. This is operational validation only. It is not
predictive validity and not a production benchmark ranking.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-1-boltons-paid-acut-smoke-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make cohesive commits after completing one or more related steps.

This runbook is allowed to make a small number of paid ACUT calls, but every
paid call must use LLM_BASE_URL plus LLM_API_KEY. If either variable is missing,
source ~/.zshrc and check again. Do not use local Codex/ChatGPT subscription
auth, OPENAI_API_KEY, OpenRouter variables, or provider-specific fallbacks.

Run paid ACUT cells sequentially. Do not enable paid parallelism. Import usage
after each paid batch and stop if usage/cost cannot be bounded.

Keep Barcarolle on the benchmark/compiler side of the ACUT boundary. Do not
implement Codex, Kilo, or any other ACUT internals.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts,
solver workspaces, verifier workspaces, cloned external repositories, .venv,
caches, or large raw outputs. Commit only small sanitized configs, manifests,
score tables, cost summaries, reports, and decision files. Raw harness outputs
must stay under ignored paths.

Do not push unless explicitly asked.
```

## Claim Boundary

Allowed claims:

```text
boltons_paid_acut_smoke_run
workspace_acut_scoreability_smoke
same_endpoint_model_different_cli_harnesses
observed_or_conservative_cost_accounting
ready_for_boltons_paid_extension
ready_for_phase1_validation_design_after_paid_smoke
insufficient_evidence_for_predictive_validation
```

Disallowed claims:

```text
predictive_validity_established
future_holdout_predictive_validity
production_benchmark_ranking
pure_harness_effect
paid_acut_validation_completed
```

Important interpretation:

- `verified_pass` and `verified_fail` are both scoreable ACUT outcomes.
- `policy_violation`, `invalid_output`, `acut_harness_error`, `harness_error`,
  and `timeout` are non-scoreable/harness or benchmark-boundary problems.
- This smoke tests whether Boltons tasks and workspace harnesses are operational
  enough to continue. It does not establish predictive validity.
- The same model is compared across Codex and Kilo harnesses; this does not
  isolate pure harness effects.

## Selected Tasks

Use only hardened Boltons benchmark-grade candidates.

Canary task:

```text
boltons__hist__007    B_real    socketutils
```

Balanced smoke tasks:

```text
boltons__hist__007    B_real    socketutils
boltons__hist__017    B_real    urlutils
boltons__hist__024    W_real    dictutils
boltons__hist__026    W_real    dictutils
```

Optional extension tasks:

```text
boltons__hist__019    B_real    ioutils
boltons__hist__020    B_real    timeutils
boltons__hist__031    W_real    iterutils
```

Do not use Boltons tasks outside this hardened set unless a later runbook
explicitly expands the benchmark.

## Budget And Parallelism

Run paid ACUT cells sequentially.

Budget assumptions:

```text
Conservative estimate per workspace ACUT cell: USD 0.50
Canary: 1 task * 2 harnesses = 2 cells = USD 1.00 conservative
Balanced smoke: 4 tasks * 2 harnesses = 8 cells = USD 4.00 conservative
Optional extension: 3 tasks * 2 harnesses = 6 cells = USD 3.00 conservative
Maximum planned incremental cells: 14
Maximum planned conservative increment: USD 7.00
Incremental hard cap for this runbook: USD 20.00
Total observed-or-conservative stop cap: USD 60.00
```

Before paid calls, read the current cost reconciliation:

```bash
jq '.totals' experiments/phase0_headroom/results/workspace_cost_reconciliation.json
```

Expected current observed-or-conservative cost is around `USD 31.03`. If the
current value is already at or above `USD 60`, stop before paid calls.

Stop immediately if:

- `LLM_BASE_URL` or `LLM_API_KEY` is unavailable after sourcing `~/.zshrc`;
- either ACUT adapter cannot prove endpoint-backed operation;
- either adapter falls back to local subscription auth;
- paid parallelism would be required;
- usage import stops working and conservative cost would exceed the caps above.

## Result Prefixes

Use these result prefixes:

```text
phase1_validation_boltons_paid_smoke_codex_preflight
phase1_validation_boltons_paid_smoke_kilo_preflight
phase1_validation_boltons_paid_smoke
phase1_validation_boltons_paid_extension
```

The first two are preflight-only prefixes. The paid smoke uses
`phase1_validation_boltons_paid_smoke`. The optional extension uses
`phase1_validation_boltons_paid_extension`.

When importing usage, include all prior canonical prefixes plus new Boltons
prefixes so `workspace_usage_ledger.jsonl` and
`workspace_cost_reconciliation.json` do not accidentally drop prior evidence:

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
```

Omit the extension prefix from usage import only until the extension actually
exists.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_boltons_paid_acut_smoke.yaml
  results/
    phase1_boltons_paid_acut_smoke_preflight.json
    phase1_boltons_paid_acut_smoke_decision.json
    phase1_mvp_closeout.json
    phase1_cost_summary.json
    phase1_workspace_scorecard.json
  reports/
    phase1_boltons_paid_acut_smoke_process.md
    phase1_boltons_paid_acut_smoke_decision.md
    phase1_mvp_closeout.md
    phase1_cost_summary.md
    phase1_workspace_scorecard.md
```

The workspace ACUT runner will add or update sanitized Phase 0 result artifacts:

```text
experiments/phase0_headroom/results/
  phase1_validation_boltons_paid_smoke_*.json
  phase1_validation_boltons_paid_smoke_*.jsonl
  phase1_validation_boltons_paid_smoke_score_table.csv
  phase1_validation_boltons_paid_extension_*.json
  phase1_validation_boltons_paid_extension_*.jsonl
  phase1_validation_boltons_paid_extension_score_table.csv
  workspace_usage_ledger.jsonl
  workspace_cost_reconciliation.json
experiments/phase0_headroom/reports/
  phase1_validation_boltons_paid_smoke_preflight.md
  phase1_validation_boltons_paid_extension_preflight.md
  workspace_cost_usage_report.md
```

Raw outputs under `experiments/phase0_headroom/results/raw/` and workspaces
under `experiments/phase0_headroom/workspaces/` must remain ignored and
untracked.

## Step 0: Preflight

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, and current git
   status.

2. Confirm replacement decision:

```bash
jq -r '.primary_decision_label' \
  experiments/phase1_compiler/results/phase1_third_repo_replacement_selection_decision.json

jq -r '.selected_repo_id' \
  experiments/phase1_compiler/results/phase1_third_repo_replacement_selection_decision.json

jq -r '.ready_for_paid_smoke' \
  experiments/phase1_compiler/results/phase1_third_repo_replacement_selection_decision.json

jq -r '.hardened_benchmark_candidate_count' \
  experiments/phase1_compiler/results/phase1_third_repo_replacement_selection_decision.json
```

Expected:

```text
ready_for_paid_third_repo_acut_smoke_runbook
boltons
true
7
```

3. Confirm selected task IDs are still hardened benchmark candidates:

```bash
jq -r '.tasks[] | select(.repo_id=="boltons" and .hardened_status=="benchmark_grade_candidate") | .task_id' \
  experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json
```

The output must include:

```text
boltons__hist__007
boltons__hist__017
boltons__hist__019
boltons__hist__020
boltons__hist__024
boltons__hist__026
boltons__hist__031
```

4. Run baseline checks:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

5. Check endpoint variables:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

6. Check current cost:

```bash
jq '.totals' experiments/phase0_headroom/results/workspace_cost_reconciliation.json
```

7. Confirm raw paths are not tracked:

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

8. Create:

```text
experiments/phase1_compiler/results/phase1_boltons_paid_acut_smoke_preflight.json
experiments/phase1_compiler/reports/phase1_boltons_paid_acut_smoke_process.md
```

The preflight JSON should include:

```json
{
  "schema_version": "barcarolle.phase1.boltons_paid_acut_smoke_preflight.v1",
  "paid_acut_calls_allowed": true,
  "direct_paid_llm_calls_allowed": false,
  "endpoint_env_required": ["LLM_BASE_URL", "LLM_API_KEY"],
  "selected_repo_id": "boltons",
  "hardened_benchmark_candidate_count": 7,
  "planned_smoke_cell_count": 8,
  "planned_extension_cell_count": 6,
  "incremental_hard_cap_usd": 20.0,
  "total_observed_or_conservative_stop_cap_usd": 60.0,
  "predictive_validity_established": false
}
```

Acceptance:

- all baseline checks pass;
- endpoint env is present after sourcing `~/.zshrc`;
- current observed-or-conservative total is below `USD 60`;
- raw/workspace/external repo paths are not tracked;
- process report records no paid calls yet.

Stop if:

- replacement decision is not ready for paid smoke;
- endpoint env is missing;
- baseline tests fail;
- current cost cannot be bounded.

Commit if preflight artifacts were created:

```text
Record Phase 1 Boltons paid smoke preflight
```

## Step 1: Write Smoke Config

Actions:

1. Create:

```text
experiments/phase1_compiler/configs/phase1_boltons_paid_acut_smoke.yaml
```

2. Include:

```yaml
schema_version: barcarolle.phase1_boltons_paid_acut_smoke.v1
status: configured
claim_scope: workspace_acut_scoreability_smoke_not_predictive_validation
predictive_validity_established: false
paid_acut_calls: enabled_small_smoke
paid_llm_calls: disabled_except_acut_harness_internal_calls
endpoint_rule:
  required_env:
    - LLM_BASE_URL
    - LLM_API_KEY
  local_subscription_fallback: disabled
  openai_api_key_fallback: disabled
selected_repo:
  repo_id: boltons
  source_release: experiments/phase0_headroom/releases/boltons_phase0_pilot_release.json
  hardening_overlay: experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json
adapters:
  config: experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
  ids:
    - codex_workspace
    - kilo_workspace
model_design:
  comparison_design: same_model_cross_harness
  preferred_model: gpt-5.4-mini
parallelism:
  paid_acut_concurrency: 1
  allow_cross_harness_paid_parallelism: false
budget:
  conservative_cell_estimate_usd: 0.50
  canary_cells: 2
  smoke_cells: 8
  optional_extension_cells: 6
  planned_conservative_increment_usd: 7.00
  incremental_hard_cap_usd: 20.00
  total_observed_or_conservative_stop_cap_usd: 60.00
result_prefixes:
  smoke: phase1_validation_boltons_paid_smoke
  extension: phase1_validation_boltons_paid_extension
tasks:
  canary:
    - boltons__hist__007
  smoke:
    - boltons__hist__007
    - boltons__hist__017
    - boltons__hist__024
    - boltons__hist__026
  optional_extension:
    - boltons__hist__019
    - boltons__hist__020
    - boltons__hist__031
acceptance:
  smoke_scoreable_cells_min: 6
  smoke_policy_violations_max: 0
  smoke_harness_error_cells_max: 2
  usage_observed_rate_min: 0.85
  extension_requires_smoke_acceptance: true
```

Acceptance:

- config names only hardened Boltons benchmark-grade candidates;
- paid ACUT concurrency is `1`;
- budget caps are explicit;
- config does not claim predictive validity.

Commit:

```text
Configure Phase 1 Boltons paid smoke
```

## Step 2: Adapter Preflight

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
  --result-prefix phase1_validation_boltons_paid_smoke_codex_preflight'
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
  --result-prefix phase1_validation_boltons_paid_smoke_kilo_preflight'
```

3. Inspect:

```bash
jq '{status, adapter_id, endpoint_proof_status, required_env_present, local_subscription_fallback, openai_or_provider_fallback, blockers}' \
  experiments/phase0_headroom/results/phase1_validation_boltons_paid_smoke_codex_preflight_preflight.json

jq '{status, adapter_id, endpoint_proof_status, required_env_present, local_subscription_fallback, openai_or_provider_fallback, blockers}' \
  experiments/phase0_headroom/results/phase1_validation_boltons_paid_smoke_kilo_preflight_preflight.json
```

Acceptance:

- both adapter preflights have `status=ready`;
- `required_env_present=true`;
- endpoint proof is eligible for both adapters;
- local subscription and provider fallback are disabled;
- no paid task-solving cell has run yet.

Stop if:

- either preflight is not ready;
- either adapter cannot prove endpoint-backed operation;
- either adapter would use local subscription auth or a fallback endpoint.

Commit:

```text
Record Boltons paid smoke adapter preflight
```

## Step 3: Paid Canary

This is the first paid batch: one task, both harnesses, sequential.

Task:

```text
boltons__hist__007
```

Projected conservative cost:

```text
2 cells * USD 0.50 = USD 1.00
```

Actions:

1. Run Codex:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_boltons_paid_acut_smoke.yaml \
  --result-prefix phase1_validation_boltons_paid_smoke \
  --task-id boltons__hist__007 \
  --timeout-seconds 900'
```

2. Run Kilo:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_boltons_paid_acut_smoke.yaml \
  --result-prefix phase1_validation_boltons_paid_smoke \
  --task-id boltons__hist__007 \
  --timeout-seconds 900'
```

3. Import usage for existing canonical prefixes plus the new smoke prefix:

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
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --allow-missing-price-estimate
```

4. Summarize:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . summarize \
  --result-prefix phase1_validation_boltons_paid_smoke
```

5. Inspect:

```bash
jq '{total_cells, scoreable_cell_count, terminal_status_counts, harness_metrics, cost_per_scoreable_cell_usd}' \
  experiments/phase0_headroom/results/phase1_validation_boltons_paid_smoke_metrics.json

jq '.totals' experiments/phase0_headroom/results/workspace_cost_reconciliation.json
```

Acceptance:

- exactly `2` canary cells are present;
- at least `1` canary cell is scoreable;
- `policy_violation` count is `0`;
- usage is observed for both cells, or observed-or-conservative total remains
  below `USD 60`;
- no adapter has systemic harness failure on the canary.

Branch:

- If accepted, continue to Step 4.
- If one harness fails due to a clear adapter/output issue but the other is
  scoreable, stop before more paid cells and write the final decision as
  `boltons_paid_canary_partial_harness_blocker`.
- If both harnesses fail or usage/cost cannot be bounded, stop and write
  `boltons_paid_canary_blocked`.

Commit:

```text
Run Boltons paid ACUT canary
```

## Step 4: Balanced Paid Smoke

Run the remaining balanced smoke tasks. The existing canary row for
`boltons__hist__007` should be reused by `run-matrix`; do not rerun it
unnecessarily under a different result prefix.

Additional tasks:

```text
boltons__hist__017
boltons__hist__024
boltons__hist__026
```

Final smoke task set:

```text
boltons__hist__007
boltons__hist__017
boltons__hist__024
boltons__hist__026
```

Projected total smoke cost:

```text
8 cells * USD 0.50 = USD 4.00 conservative
```

Actions:

1. Run Codex for the full smoke task set:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_boltons_paid_acut_smoke.yaml \
  --result-prefix phase1_validation_boltons_paid_smoke \
  --task-id boltons__hist__007 \
  --task-id boltons__hist__017 \
  --task-id boltons__hist__024 \
  --task-id boltons__hist__026 \
  --timeout-seconds 900'
```

2. Run Kilo for the full smoke task set:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_boltons_paid_acut_smoke.yaml \
  --result-prefix phase1_validation_boltons_paid_smoke \
  --task-id boltons__hist__007 \
  --task-id boltons__hist__017 \
  --task-id boltons__hist__024 \
  --task-id boltons__hist__026 \
  --timeout-seconds 900'
```

3. Import usage again:

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
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --allow-missing-price-estimate
```

4. Summarize:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . summarize \
  --result-prefix phase1_validation_boltons_paid_smoke
```

5. Inspect:

```bash
jq '{total_cells, scoreable_cell_count, terminal_status_counts, split_metrics, harness_metrics, cost_per_scoreable_cell_usd}' \
  experiments/phase0_headroom/results/phase1_validation_boltons_paid_smoke_metrics.json

cat experiments/phase0_headroom/results/phase1_validation_boltons_paid_smoke_score_table.csv

jq '.totals' experiments/phase0_headroom/results/workspace_cost_reconciliation.json
```

Acceptance:

- `total_cells` is `8`;
- scoreable cells are at least `6`;
- `policy_violation` terminal count is `0`;
- non-scoreable harness/timeout/invalid-output cells are at most `2`;
- both B_real and W_real have at least `2` scoreable cells combined across
  harnesses;
- usage observed rate remains at least `0.85`, or observed-or-conservative
  total remains below `USD 60`;
- result is labeled operational smoke, not predictive validation.

Branch:

- If accepted and cost remains below caps, Step 5 optional extension may run.
- If accepted but usage/cost is marginal, skip extension and continue to Step 6.
- If not accepted, skip extension and continue to Step 7 with a blocker
  decision.

Commit:

```text
Run Boltons paid ACUT smoke
```

## Step 5: Optional Hardened-Task Extension

Run this only if Step 4 is accepted and observed-or-conservative total is safely
below `USD 60`.

This extension tests the remaining hardened Boltons candidates. It is still
small and not predictive validation.

Tasks:

```text
boltons__hist__019
boltons__hist__020
boltons__hist__031
```

Projected extension cost:

```text
6 cells * USD 0.50 = USD 3.00 conservative
```

Actions:

1. Run Codex:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_boltons_paid_acut_smoke.yaml \
  --result-prefix phase1_validation_boltons_paid_extension \
  --task-id boltons__hist__019 \
  --task-id boltons__hist__020 \
  --task-id boltons__hist__031 \
  --timeout-seconds 900'
```

2. Run Kilo:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_boltons_paid_acut_smoke.yaml \
  --result-prefix phase1_validation_boltons_paid_extension \
  --task-id boltons__hist__019 \
  --task-id boltons__hist__020 \
  --task-id boltons__hist__031 \
  --timeout-seconds 900'
```

3. Import usage with both Boltons prefixes:

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
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --allow-missing-price-estimate
```

4. Summarize extension:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . summarize \
  --result-prefix phase1_validation_boltons_paid_extension
```

Acceptance:

- extension total cells are `6`;
- extension scoreable cells are at least `4`;
- policy violations are `0`;
- combined smoke plus extension has at least `10` scoreable cells out of `14`;
- observed-or-conservative total remains below `USD 60`.

Commit:

```text
Run Boltons paid ACUT extension
```

## Step 6: Import Into Phase 1 Boundary

Purpose:

Make Phase 1 artifacts aware of the Boltons paid smoke without claiming
predictive validity.

Actions:

1. If needed, extend:

```text
experiments/phase1_compiler/configs/phase1_mvp.yaml
experiments/phase1_compiler/tools/phase1_compiler.py
experiments/phase1_compiler/tests/
```

so the MVP scorecard can import Boltons paid smoke score tables as sidecar or
Phase 1 operational validation evidence.

Minimum expected source artifacts:

```yaml
boltons_paid_smoke_score_table: experiments/phase0_headroom/results/phase1_validation_boltons_paid_smoke_score_table.csv
boltons_paid_extension_score_table: experiments/phase0_headroom/results/phase1_validation_boltons_paid_extension_score_table.csv
```

If the extension did not run, the compiler must not require the extension score
table.

2. Run:

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

3. Inspect:

```bash
jq '{
  release_status,
  predictive_validity_established,
  production_ranking_status,
  hardening_sidecar_evidence,
  next_runbook_recommendation
}' experiments/phase1_compiler/results/phase1_mvp_closeout.json

jq '.summary.by_result_prefix' experiments/phase1_compiler/results/phase1_workspace_scorecard.json

jq '{call_count, usage_observed_rate, observed_or_conservative_estimated_cost_usd}' \
  experiments/phase1_compiler/results/phase1_cost_summary.json
```

Acceptance:

- Phase 1 compiler validate passes;
- predictive-validity fields remain `false`;
- production ranking remains `not_produced`;
- Boltons paid smoke is labeled operational smoke evidence;
- older scorecards are not silently reinterpreted as predictive evidence;
- cost summary includes new paid smoke usage/cost.

Commit if compiler config/code/results changed:

```text
Import Boltons paid smoke into Phase 1 boundary
```

## Step 7: Write Final Smoke Decision

Actions:

1. Create:

```text
experiments/phase1_compiler/results/phase1_boltons_paid_acut_smoke_decision.json
experiments/phase1_compiler/reports/phase1_boltons_paid_acut_smoke_decision.md
```

2. Use exactly one primary decision label:

```text
boltons_paid_smoke_complete_ready_for_phase1_validation_design
boltons_paid_smoke_complete_extension_recommended
boltons_paid_smoke_scoreability_blocked
boltons_paid_canary_partial_harness_blocker
boltons_paid_canary_blocked
boltons_paid_smoke_usage_cost_blocked
```

3. The JSON must include:

```json
{
  "schema_version": "barcarolle.phase1.boltons_paid_acut_smoke_decision.v1",
  "starting_head": "",
  "final_head": "",
  "paid_acut_calls_made": true,
  "direct_paid_llm_calls_made": false,
  "endpoint_env_used": ["LLM_BASE_URL", "LLM_API_KEY"],
  "selected_repo_id": "boltons",
  "result_prefixes": [],
  "smoke_task_ids": [],
  "extension_task_ids": [],
  "smoke_total_cells": 0,
  "smoke_scoreable_cells": 0,
  "smoke_terminal_status_counts": {},
  "extension_total_cells": 0,
  "extension_scoreable_cells": 0,
  "combined_total_cells": 0,
  "combined_scoreable_cells": 0,
  "policy_violation_count": 0,
  "usage_observed_rate": null,
  "observed_or_conservative_estimated_cost_usd": null,
  "incremental_observed_or_conservative_estimated_cost_usd": null,
  "predictive_validity_established": false,
  "production_ranking_status": "not_produced",
  "primary_decision_label": "",
  "recommended_next_runbook": "",
  "allowed_claims": [],
  "disallowed_claims": []
}
```

4. The Markdown report should answer:

- Did both adapters pass preflight?
- Which Boltons tasks were run?
- How many paid cells ran?
- How many cells were scoreable?
- Were there any policy violations?
- What was usage observed rate?
- What was observed-or-conservative cost?
- Did the optional extension run?
- May the next runbook move to Phase 1 validation design?
- Which claims remain prohibited?

5. Recommended next runbook:

- If balanced smoke is accepted and extension either passed or was skipped for
  cost prudence:

```text
write_phase1_validation_design_and_future_holdout_runbook
```

- If smoke is accepted but extension did not run and more operational evidence
  is desired:

```text
run_boltons_paid_hardened_extension
```

- If smoke is blocked:

```text
repair_boltons_paid_smoke_scoreability_or_adapter_boundary
```

Acceptance:

- final decision follows from observed scoreability and cost;
- no unsupported predictive-validity claim is made;
- raw artifacts remain ignored;
- paid calls are explicitly acknowledged and bounded.

Commit:

```text
Summarize Boltons paid ACUT smoke
```

## Step 8: Final Verification

Actions:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml

git status --short --ignored \
  experiments/phase0_headroom \
  experiments/phase1_compiler \
  docs/experiments \
  AGENTS.md \
  .gitignore

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

- all scoped tests pass;
- Phase 1 compiler validate passes;
- branch is clean except ignored raw/cache/workspace/external-repo files;
- raw artifacts are not tracked;
- final smoke decision is committed;
- process report records paid calls and cost boundary.

Do not push unless the user explicitly asked this worker to push.

## Stop Conditions

Stop and write:

```text
experiments/phase1_compiler/reports/phase1_boltons_paid_acut_smoke_blocker.md
```

if any of these occur:

- endpoint env is missing after sourcing `~/.zshrc`;
- adapter preflight is not ready;
- local subscription or fallback auth would be used;
- current observed-or-conservative cost is already at or above `USD 60`;
- canary has zero scoreable cells;
- balanced smoke has fewer than `6` scoreable cells out of `8`;
- any policy violation occurs;
- usage/cost cannot be observed or conservatively bounded;
- raw prompts/completions/transcripts/workspaces would need to be committed;
- final artifacts would imply predictive validity.

The blocker report must include:

```text
last completed step
blocking condition
affected result prefix
affected adapter or task IDs
why the worker stopped
smallest next repair
whether paid calls were made
observed-or-conservative cost at stop
```

## Expected End States

Strong outcome:

```text
boltons_paid_smoke_complete_ready_for_phase1_validation_design
```

The balanced Boltons smoke is scoreable, policy-clean, and cost-bounded. The next
runbook can design Phase 1 validation and future holdout without pretending this
smoke established predictive validity.

Useful extension outcome:

```text
boltons_paid_smoke_complete_extension_recommended
```

The balanced smoke is healthy, but the optional extension was skipped. A short
follow-up may run the remaining three hardened Boltons tasks before moving to
validation design.

Blocked outcome:

```text
boltons_paid_smoke_scoreability_blocked
```

The selected tasks were locally benchmark-grade, but real ACUT harnesses did not
produce enough scoreable cells. The next runbook should repair the workspace
adapter boundary, task statement policy, or harness invocation before further
paid expansion.

Never claim predictive validity from this runbook.
