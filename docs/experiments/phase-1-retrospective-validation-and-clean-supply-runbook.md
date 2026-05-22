# Phase 1 Retrospective Validation And Clean Supply Runbook

Status: implementation runbook, 2026-05-22.

This runbook is for one dedicated Codex CLI session. Its job is to continue
Phase 1 after the strict future-holdout gate blocked on clean supply. It adds a
lower-strength but useful validation track:

```text
outcome-seen retrospective locked validation
```

and keeps a separate track for replenishing strict clean future-holdout supply.

The central rule is:

```text
Already observed ACUT outcomes may be used for retrospective validation, but
they must not be claimed as clean future holdout evidence.
```

## Starting State

The expected starting state is:

```text
phase1_future_holdout_decision = future_holdout_supply_blocked
paid_acut_calls_made = false
recommended_next_runbook = mine_and_certify_fresh_outcome_unseen_tasks_for_future_holdout
```

Current clean supply:

```text
boltons: 16 certified, 7 benchmark-grade, 7 outcome-seen, 0 clean outcome-unseen
toolz:   6 certified, 6 benchmark-grade, 6 outcome-seen, 0 clean outcome-unseen
```

This block is valid for strict future holdout. It does not mean the current data
is useless. It means the current data must be labeled as retrospective,
outcome-seen evidence.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-1-retrospective-validation-and-clean-supply-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make cohesive commits after completing one or more related steps.

The strict future-holdout runbook blocked because all current validation-grade
Toolz and Boltons tasks already have observed workspace ACUT outcomes. This
runbook intentionally introduces a lower-strength evidence level:
outcome-seen retrospective locked validation. Use existing sanitized score
tables and manifests. Do not rerun already observed retrospective cells unless
the runbook explicitly reaches a clean-supply paid-validation gate.

Keep claim labels honest:
- outcome-seen retrospective validation can support estimator sanity checks,
  pilot error metrics, and baseline-comparison plumbing;
- it cannot support clean future-holdout predictive-validity claims;
- strict clean future holdout still requires outcome-unseen tasks.

All paid LLM or ACUT calls must use LLM_BASE_URL plus LLM_API_KEY. If either
variable is missing, source ~/.zshrc and check again. Do not use local
Codex/ChatGPT subscription auth, OPENAI_API_KEY, OpenRouter variables, or
provider-specific fallbacks.

Paid ACUT calls are disabled for the retrospective track. They are allowed only
if the clean-supply extension track promotes enough outcome-unseen tasks and the
runbook explicitly reaches the paid clean-validation gate. Run paid cells
sequentially.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts,
solver workspaces, verifier workspaces, cloned external repositories, .venv,
caches, raw GitHub API responses, or large raw outputs. Commit only small
sanitized configs, manifests, score tables, cost summaries, reports, and
decision files. Raw harness outputs must stay under ignored paths.

Do not push unless explicitly asked.
```

## Evidence Levels

Use these labels consistently:

```text
clean_future_holdout:
  Outcome-unseen tasks, selected before ACUT execution, opened only after
  predictor and metrics are frozen. This is the strongest validation evidence.

outcome_seen_retrospective_locked:
  Tasks with existing ACUT outcomes. Splits, predictors, metrics, and inclusion
  rules are frozen before analysis in this runbook, and all eligible tasks are
  used without cherry-picking. This is useful pilot evidence, not clean holdout.

diagnostic_dev:
  Evidence used to debug adapters, certification, policy gates, source quality,
  or failure modes. It can guide engineering, but not validation claims.
```

## Claim Boundary

Allowed claims:

```text
retrospective_locked_validation_complete
outcome_seen_retrospective_estimator_sanity_check
same_endpoint_model_different_cli_harnesses
existing_scorecard_baseline_comparison
strict_clean_future_holdout_still_blocked
clean_supply_extension_ready_for_paid_validation
insufficient_evidence_for_predictive_validation
observed_or_conservative_cost_accounting
```

Disallowed claims:

```text
predictive_validity_established
clean_future_holdout_validity_from_outcome_seen_tasks
production_benchmark_ranking
pure_harness_effect
contamination_proof_evaluation_if_model_snapshot_unknown
validation_grade_humanize_if_commit_fallback_only
```

Important interpretation:

- `B_real` and `W_real` are historical split labels. They are not themselves
  contamination labels.
- A task becomes outcome-seen when a workspace ACUT score table or Phase 1
  workspace scorecard contains a result for it.
- Outcome-seen tasks may be analyzed only under the retrospective evidence
  level.
- Clean future holdout remains blocked until enough outcome-unseen tasks are
  promoted.

## Primary Retrospective Dataset

Use these current result prefixes as the primary retrospective evidence:

```text
toolz:
  prefix: codex_kilo_workspace_followup
  tasks:
    B_real: toolz__hist__001, toolz__hist__002, toolz__hist__003
    W_real: toolz__hist__004, toolz__hist__010, toolz__hist__016

boltons:
  prefixes:
    phase1_validation_boltons_paid_smoke
    phase1_validation_boltons_paid_extension
  tasks:
    B_real: boltons__hist__007, boltons__hist__017, boltons__hist__019, boltons__hist__020
    W_real: boltons__hist__024, boltons__hist__026, boltons__hist__031
```

Diagnostic-only result prefixes:

```text
codex_kilo_workspace_stability
humanize_pre_phase1_workspace
phase1_validation_humanize_holdout_smoke
phase1_validation_humanize_holdout
phase1_validation_humanize_holdout_stability
click / generic comparator rows
```

Rules:

- Do not use Toolz stability repeats in the primary retrospective score because
  they duplicate task outcomes. Report them separately as stability diagnostics.
- Do not use Humanize as validation-grade because current Humanize source
  provenance remains commit-message fallback.
- Do not use Click as target-repo validation because it is a generic comparator.
- Include all primary eligible rows from the selected prefixes. Do not
  cherry-pick pass/fail outcomes.

## Clean Supply Candidates

Start with the current Boltons manual-review-required candidates, because they
are certified, outcome-unseen, and have not been used in paid ACUT cells:

```text
boltons__hist__011    B_real    iterutils
boltons__hist__014    B_real    fileutils,jsonutils
boltons__hist__022    W_real    iterutils
boltons__hist__023    W_real    tbutils
boltons__hist__027    W_real    cacheutils
```

These tasks must not be promoted mechanically. Review source quality, oracle
alignment, scope, and solution exposure. If at least two B_real and two W_real
tasks are promoted to benchmark-grade and remain outcome-unseen, strict clean
future-holdout validation can be reattempted.

## Budget And Parallelism

Retrospective track:

```text
paid_acut_calls: disabled
direct_paid_llm_calls: disabled
```

Clean-supply local hardening:

```text
paid_acut_calls: disabled
direct_paid_llm_calls: disabled
```

Optional paid clean validation, only if clean supply is promoted:

```text
minimum clean validation:
  2 B_eval tasks * 2 harnesses = 4 cells
  2 H_future tasks * 2 harnesses = 4 cells
  total = 8 cells

conservative estimate: USD 0.50 per workspace ACUT cell
incremental hard cap: USD 20.00
total observed-or-conservative stop cap: USD 80.00
paid concurrency: 1
```

Stop before any paid call if:

- `LLM_BASE_URL` or `LLM_API_KEY` is unavailable after sourcing `~/.zshrc`;
- either ACUT adapter cannot prove endpoint-backed operation;
- current observed-or-conservative total is already at or above `USD 80`;
- projected incremental cost would exceed `USD 20`;
- usage import is broken and cost cannot be bounded.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_retrospective_validation_and_clean_supply.yaml
  tools/
    phase1_retrospective_validation.py
  tests/
    test_phase1_retrospective_validation.py
  results/
    phase1_retrospective_validation_preflight.json
    phase1_retrospective_validation_plan.json
    phase1_retrospective_validation_metrics.json
    phase1_clean_supply_extension_review.json
    phase1_retrospective_validation_decision.json
    phase1_mvp_closeout.json
    phase1_workspace_scorecard.json
    phase1_cost_summary.json
  reports/
    phase1_retrospective_validation_process.md
    phase1_retrospective_validation_plan.md
    phase1_retrospective_validation_metrics.md
    phase1_clean_supply_extension_review.md
    phase1_retrospective_validation_decision.md
    phase1_mvp_closeout.md
    phase1_workspace_scorecard.md
    phase1_cost_summary.md
```

If optional paid clean validation runs, the workspace runner may add:

```text
experiments/phase0_headroom/results/
  phase1_clean_future_holdout_b_eval_*.json
  phase1_clean_future_holdout_b_eval_*.jsonl
  phase1_clean_future_holdout_b_eval_score_table.csv
  phase1_clean_future_holdout_h_future_*.json
  phase1_clean_future_holdout_h_future_*.jsonl
  phase1_clean_future_holdout_h_future_score_table.csv
  workspace_usage_ledger.jsonl
  workspace_cost_reconciliation.json
```

Raw outputs under `experiments/phase0_headroom/results/raw/` and workspaces
under `experiments/phase0_headroom/workspaces/` must remain ignored and
untracked.

## Step 0: Preflight

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, and current git
   status in:

```text
experiments/phase1_compiler/reports/phase1_retrospective_validation_process.md
```

2. Confirm the strict future-holdout blocker:

```bash
jq -r '.primary_decision_label' \
  experiments/phase1_compiler/results/phase1_future_holdout_decision.json

jq -r '.recommended_next_runbook' \
  experiments/phase1_compiler/results/phase1_future_holdout_decision.json

jq '.repo_summary' \
  experiments/phase1_compiler/results/phase1_future_holdout_clean_supply.json
```

Expected:

```text
future_holdout_supply_blocked
mine_and_certify_fresh_outcome_unseen_tasks_for_future_holdout
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
experiments/phase1_compiler/results/phase1_retrospective_validation_preflight.json
```

Include at least:

```json
{
  "schema_version": "barcarolle.phase1.retrospective_validation_preflight.v1",
  "strict_future_holdout_decision": "future_holdout_supply_blocked",
  "retrospective_evidence_level": "outcome_seen_retrospective_locked",
  "retrospective_paid_acut_calls_allowed": false,
  "clean_supply_paid_acut_calls_allowed_after_gate": true,
  "endpoint_env_required": ["LLM_BASE_URL", "LLM_API_KEY"],
  "predictive_validity_established": false
}
```

Acceptance:

- all baseline checks pass;
- endpoint env is present after sourcing `~/.zshrc`;
- current cost is bounded;
- raw/workspace/external repo paths are not tracked;
- no paid calls have run in this runbook.

Stop if:

- strict future-holdout decision is not available;
- baseline tests fail;
- endpoint env is missing and this runbook would need paid clean validation.

Commit if preflight artifacts were created:

```text
Record Phase 1 retrospective validation preflight
```

## Step 1: Write Config

Actions:

Create:

```text
experiments/phase1_compiler/configs/phase1_retrospective_validation_and_clean_supply.yaml
```

Use this minimum structure:

```yaml
schema_version: barcarolle.phase1_retrospective_validation_and_clean_supply.v1
status: configured
claim_scope: retrospective_locked_validation_not_clean_future_holdout
predictive_validity_established: false

evidence_levels:
  primary_retrospective: outcome_seen_retrospective_locked
  strict_holdout: clean_future_holdout

retrospective_track:
  paid_acut_calls: disabled
  inclusion_rule: use_all_primary_eligible_outcome_seen_rows
  split_source: historical_B_real_W_real
  primary_result_prefixes:
    toolz:
      - codex_kilo_workspace_followup
    boltons:
      - phase1_validation_boltons_paid_smoke
      - phase1_validation_boltons_paid_extension
  diagnostic_result_prefixes:
    - codex_kilo_workspace_stability
    - humanize_pre_phase1_workspace
    - phase1_validation_humanize_holdout_smoke
    - phase1_validation_humanize_holdout
    - phase1_validation_humanize_holdout_stability
  excluded_target_repos:
    - click
    - generic_comparators
  diagnostic_only_repos:
    - humanize
  duplicate_policy:
    toolz_stability_repeat: diagnostic_only
    same_task_same_adapter_primary_prefix_duplicate: keep_latest_by_prefix_order

clean_supply_track:
  paid_acut_calls: disabled_until_clean_supply_ready
  candidate_source: current_boltons_manual_review_required
  candidate_task_ids:
    - boltons__hist__011
    - boltons__hist__014
    - boltons__hist__022
    - boltons__hist__023
    - boltons__hist__027
  promotion_requires:
    - benchmark_grade_source_context
    - oracle_alignment
    - scope_clarity
    - no_solution_exposure
    - no_project_or_docs_only_work
    - outcome_unseen
  minimum_clean_split:
    b_eval_tasks: 2
    h_future_tasks: 2
  preferred_clean_split:
    b_eval_tasks: 3
    h_future_tasks: 3

endpoint_rule:
  required_env:
    - LLM_BASE_URL
    - LLM_API_KEY
  local_subscription_fallback: disabled
  openai_api_key_fallback: disabled
  provider_specific_fallback: disabled

adapters:
  config: experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
  ids:
    - codex_workspace
    - kilo_workspace

budget:
  conservative_cell_estimate_usd: 0.50
  optional_clean_validation_cells_min: 8
  incremental_hard_cap_usd: 20.00
  total_observed_or_conservative_stop_cap_usd: 80.00

result_prefixes:
  optional_clean_b_eval: phase1_clean_future_holdout_b_eval
  optional_clean_h_future: phase1_clean_future_holdout_h_future

source_artifacts:
  workspace_scorecard: experiments/phase1_compiler/results/phase1_workspace_scorecard.json
  hardening_overlay: experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json
  boltons_certified_tasks: experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl
  boltons_release: experiments/phase0_headroom/releases/boltons_phase0_pilot_release.json
  toolz_certified_tasks: experiments/phase0_headroom/certified_tasks/toolz_certified_tasks.jsonl
  toolz_release: experiments/phase0_headroom/releases/toolz_phase0_mini_release.json
  cost_reconciliation: experiments/phase0_headroom/results/workspace_cost_reconciliation.json

acceptance:
  retrospective_policy_violations_max: 3
  clean_validation_policy_violations_max: 0
  strict_predictive_validity_claim_allowed: false
```

Acceptance:

- retrospective track allows outcome-seen data but labels it as such;
- paid calls are disabled for retrospective scoring;
- clean supply track is separate and outcome-unseen;
- config preserves `predictive_validity_established=false`.

Commit:

```text
Configure Phase 1 retrospective validation and clean supply
```

## Step 2: Add Retrospective Validation Tooling

Add:

```text
experiments/phase1_compiler/tools/phase1_retrospective_validation.py
experiments/phase1_compiler/tests/test_phase1_retrospective_validation.py
```

Required commands:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_retrospective_validation.py \
  plan \
  --config experiments/phase1_compiler/configs/phase1_retrospective_validation_and_clean_supply.yaml

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_retrospective_validation.py \
  score \
  --config experiments/phase1_compiler/configs/phase1_retrospective_validation_and_clean_supply.yaml

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_retrospective_validation.py \
  review-clean-supply \
  --config experiments/phase1_compiler/configs/phase1_retrospective_validation_and_clean_supply.yaml

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_retrospective_validation.py \
  decide \
  --config experiments/phase1_compiler/configs/phase1_retrospective_validation_and_clean_supply.yaml
```

The tool may be implemented as a small standalone script. Reuse existing
helpers only when this keeps the change simple.

Required behavior:

1. Load primary score tables:

```text
experiments/phase0_headroom/results/codex_kilo_workspace_followup_score_table.csv
experiments/phase0_headroom/results/phase1_validation_boltons_paid_smoke_score_table.csv
experiments/phase0_headroom/results/phase1_validation_boltons_paid_extension_score_table.csv
```

2. Filter to primary target repos only:

```text
toolz
boltons
```

3. Exclude:

```text
click
generic_comparators
humanize primary validation rows
Toolz stability repeat from primary retrospective scoring
```

4. Use all primary eligible rows from selected prefixes. Do not select by
   outcome.

5. Treat `verified_pass` and `verified_fail` as scoreable. Treat
   `invalid_output`, `policy_violation`, `timeout`, `harness_error`, and
   `acut_harness_error` as non-scoreable.

6. Compute per repo and per adapter:

```text
B_real scoreable pass rate
W_real scoreable pass rate
absolute error = abs(B_real pass rate - W_real pass rate)
scoreable counts
non-scoreable counts
policy violation counts
```

7. Compute pooled MAE across adapter/repo cells where both B_real and W_real
   have scoreable data.

8. Emit a warning when sample size is underpowered.

9. Write:

```text
experiments/phase1_compiler/results/phase1_retrospective_validation_plan.json
experiments/phase1_compiler/reports/phase1_retrospective_validation_plan.md
experiments/phase1_compiler/results/phase1_retrospective_validation_metrics.json
experiments/phase1_compiler/reports/phase1_retrospective_validation_metrics.md
```

10. The metrics payload must include:

```json
{
  "evidence_level": "outcome_seen_retrospective_locked",
  "clean_future_holdout": false,
  "predictive_validity_established": false
}
```

Unit tests must cover:

- outcome-seen rows are allowed only under retrospective evidence level;
- Click and Humanize are excluded from primary target validation;
- Toolz stability repeat is diagnostic-only;
- B_real/W_real pass-rate error calculation;
- non-scoreable rows do not enter pass-rate denominators;
- no predictive-validity claim is emitted.

Acceptance:

- tests pass;
- plan lists exact included task ids and prefixes;
- metrics use all eligible rows and no outcome-based selection;
- no paid calls run.

Commit:

```text
Add Phase 1 retrospective validation tooling
```

## Step 3: Run Retrospective Locked Validation

Actions:

Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_retrospective_validation.py \
  plan \
  --config experiments/phase1_compiler/configs/phase1_retrospective_validation_and_clean_supply.yaml

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_retrospective_validation.py \
  score \
  --config experiments/phase1_compiler/configs/phase1_retrospective_validation_and_clean_supply.yaml
```

Inspect:

```bash
jq '{evidence_level, included_repos, included_task_count, primary_prefixes, clean_future_holdout, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_retrospective_validation_plan.json

jq '{evidence_level, pooled_mae, repo_adapter_errors, warnings, predictive_validity_established}' \
  experiments/phase1_compiler/results/phase1_retrospective_validation_metrics.json
```

Acceptance:

- included repos are `toolz` and `boltons`;
- included task ids match the primary retrospective dataset in this runbook;
- evidence level is `outcome_seen_retrospective_locked`;
- clean future holdout is `false`;
- predictive validity is `false`;
- metrics are present for Codex and Kilo where B/W scoreable cells exist.

Stop if:

- the tool includes Click or Humanize in primary validation;
- the tool selects or drops tasks based on pass/fail outcome;
- the report labels the result as clean holdout or predictive validity.

Commit:

```text
Run Phase 1 retrospective locked validation
```

## Step 4: Review Clean Supply Candidates

Actions:

Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_retrospective_validation.py \
  review-clean-supply \
  --config experiments/phase1_compiler/configs/phase1_retrospective_validation_and_clean_supply.yaml
```

The review must read:

```text
experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json
experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl
experiments/phase1_compiler/results/phase1_workspace_scorecard.json
```

It must produce:

```text
experiments/phase1_compiler/results/phase1_clean_supply_extension_review.json
experiments/phase1_compiler/reports/phase1_clean_supply_extension_review.md
```

For each candidate task, record:

```text
task_id
split
module_or_package
task_time
current_hardened_status
manual_review_reasons
outcome_seen
source_context_status
oracle_alignment_status
solution_exposure_risk
project_or_docs_only_risk
promotion_decision
promotion_blockers
```

Promotion decisions:

```text
promote_to_clean_benchmark_candidate
keep_manual_review_required
reject_for_clean_holdout
```

Default conservative rules:

- Reject if `outcome_seen=true`.
- Reject if source context is commit-message-only or source-diagnostic-only.
- Reject if task is project/config/docs-only rather than behavioral code.
- Reject if oracle alignment is rejected or execution gates failed.
- Keep manual review if evidence is insufficient.
- Promote only if the row has clean source context, aligned oracle, clear
  implementation scope, no solution exposure, and no ACUT outcome.

Acceptance:

- every candidate has a decision and reason;
- outcome-seen tasks are not promoted;
- promoted clean candidates are split into B_real/W_real;
- if at least 2 B_real and 2 W_real are promoted, the review marks
  `clean_supply_extension_ready=true`.

Branch:

- If clean supply extension is ready, continue to Step 5.
- If not ready, skip Steps 5-7 and continue to Step 8 with decision
  `retrospective_validation_complete_clean_supply_still_blocked`.

Commit:

```text
Review Phase 1 clean supply extension candidates
```

## Step 5: Re-run Strict Clean Future Holdout Design

Run this step only if Step 4 promotes at least two B_real and two W_real clean
outcome-unseen tasks.

Actions:

1. Extend `phase1_future_holdout.py` or add a small overlay reader so promoted
   clean candidates from Step 4 can count as benchmark-grade for strict
   future-holdout design without changing their original raw certification
   history.

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

- strict future-holdout clean supply is ready for at least one repo;
- all selected clean tasks are outcome-unseen before paid validation;
- cutoff uses repo task time and an embargo gap;
- preregistration is frozen before paid cells;
- predictive validity remains false.

Stop if:

- promoted tasks are not visible to the strict holdout design;
- selected task ids differ from the Step 4 promoted set without explanation;
- the strict holdout plan includes outcome-seen tasks.

Commit:

```text
Reopen strict clean future holdout design with promoted supply
```

## Step 6: Optional Paid Clean Validation Preflight

Run this step only if Step 5 passes and cost remains below caps.

Actions:

1. Check endpoint variables:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

2. Preflight Codex:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --result-prefix phase1_clean_future_holdout_codex_preflight'
```

3. Preflight Kilo:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; \
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --result-prefix phase1_clean_future_holdout_kilo_preflight'
```

4. Inspect both preflight JSONs for:

```text
status=ready
required_env_present=true
endpoint_proof_status eligible
fallback auth disabled
```

Acceptance:

- both adapters are ready;
- endpoint rule is satisfied;
- no paid solving cell has run yet;
- observed-or-conservative total is below `USD 80`.

Stop if adapter preflight fails.

Commit:

```text
Record Phase 1 clean future holdout adapter preflight
```

## Step 7: Optional Paid Clean Validation

Run this step only if Step 6 passes.

Use the frozen task ids from:

```text
experiments/phase1_compiler/results/phase1_future_holdout_preregistration.json
```

Actions:

1. Run `B_eval` cells for Codex and Kilo under:

```text
phase1_clean_future_holdout_b_eval
```

Use `workspace_acut_run.py run-matrix` with repeated `--task-id` values from
`.splits.b_eval`.

2. Import usage with all canonical prefixes plus:

```text
phase1_clean_future_holdout_b_eval
```

3. Summarize the prefix.

4. If `B_eval` acceptance passes, run `H_future` cells for Codex and Kilo under:

```text
phase1_clean_future_holdout_h_future
```

Use task ids from `.splits.h_future`.

5. Import usage again with both clean prefixes.

6. Summarize the holdout prefix.

Acceptance:

- all paid task ids match preregistration;
- paid cells are sequential;
- policy violations are `0`;
- scoreable cells meet the minimum from preregistration;
- observed-or-conservative total remains below `USD 80`;
- no predictor, task set, or metric rule is changed after `B_eval` results.

Stop if:

- any paid task id differs from preregistration;
- endpoint/cost cannot be bounded;
- policy violations occur;
- both adapters fail systemically.

Commit:

```text
Run Phase 1 optional clean future holdout validation
```

## Step 8: Decide

Actions:

Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_retrospective_validation.py \
  decide \
  --config experiments/phase1_compiler/configs/phase1_retrospective_validation_and_clean_supply.yaml
```

Write:

```text
experiments/phase1_compiler/results/phase1_retrospective_validation_decision.json
experiments/phase1_compiler/reports/phase1_retrospective_validation_decision.md
```

Decision labels:

```text
retrospective_validation_complete_clean_supply_still_blocked
retrospective_validation_complete_clean_supply_ready
retrospective_validation_complete_clean_holdout_paid_deferred
retrospective_validation_and_clean_holdout_smoke_complete
```

The decision must include:

```text
retrospective evidence level
included retrospective repos
included retrospective task ids
retrospective B->W error metrics
clean supply promoted task ids
whether optional paid clean validation ran
scoreable cells and policy violations, if paid validation ran
cost summary
predictive validity status
next recommended runbook
```

Allowed next runbooks:

```text
mine_additional_clean_outcome_unseen_supply
run_preregistered_clean_future_holdout_paid_validation
scale_retrospective_validation_to_additional_repos
scale_clean_future_holdout_validation
```

Do not emit `predictive_validity_established=true`.

Acceptance:

- decision explicitly separates retrospective evidence from clean holdout
  evidence;
- disallowed claims remain disallowed;
- next runbook is concrete;
- no raw artifacts are referenced as committed files.

Commit:

```text
Summarize Phase 1 retrospective validation and clean supply
```

## Step 9: Refresh Phase 1 Boundary

Actions:

1. Extend Phase 1 compiler closeout only as needed to import:

```text
experiments/phase1_compiler/results/phase1_retrospective_validation_decision.json
```

as sidecar evidence.

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

Acceptance:

- Phase 1 compiler validation returns `status=valid`;
- closeout labels retrospective evidence as retrospective, not clean holdout;
- strict future-holdout sidecar still records the previous blocker unless
  optional clean validation actually ran;
- `predictive_validity_established=false`;
- production ranking remains `not_produced`.

Commit:

```text
Refresh Phase 1 boundary after retrospective validation
```

## Step 10: Final Verification

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
- process report records each branch taken;
- final decision JSON and report are committed;
- no push is performed.

Final response from the worker should include:

- final decision label;
- retrospective included repos/tasks;
- retrospective B->W error summary;
- clean supply candidate decisions;
- whether optional paid clean validation ran;
- cost summary;
- whether predictive validity remains false;
- recommended next runbook.

## Expected Branches

### Retrospective Only, Clean Supply Still Blocked

Use this if retrospective scoring succeeds but fewer than two B_real and two
W_real outcome-unseen tasks are promoted.

Decision:

```text
retrospective_validation_complete_clean_supply_still_blocked
```

Next runbook:

```text
mine_additional_clean_outcome_unseen_supply
```

### Retrospective Complete, Clean Supply Ready

Use this if candidate review promotes enough clean tasks but paid clean
validation is not run in this session.

Decision:

```text
retrospective_validation_complete_clean_supply_ready
```

Next runbook:

```text
run_preregistered_clean_future_holdout_paid_validation
```

### Retrospective Plus Clean Holdout Smoke

Use this if enough clean tasks are promoted and optional paid clean validation
runs under the preregistered task ids.

Decision:

```text
retrospective_validation_and_clean_holdout_smoke_complete
```

Allowed claim:

```text
clean_future_holdout_protocol_executable
insufficient_sample_for_predictive_validity
```

Do not claim predictive validity unless a later scale-up satisfies a stronger
pre-registered threshold.
