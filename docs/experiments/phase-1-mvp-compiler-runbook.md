# Phase 1 MVP Compiler Runbook

Status: implementation runbook, 2026-05-21.

This runbook is for one dedicated Codex CLI session. Its job is to implement the
Phase 1 MVP compiler from the completed Phase 0 readiness gate.

The expected starting gate is:

```text
experiments/phase0_headroom/results/pre_phase1_gate.json
status: ready_for_phase1_mvp
predictive_validity_established: false
```

Phase 1 MVP means compiler infrastructure, not predictive validation. The worker
should produce a multi-repo benchmark-release draft, normalized certification
records, workspace ACUT score imports, cost summaries, and readiness reports
that keep unsupported claims out of scope.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-1-mvp-compiler-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make cohesive commits after completing one or more related steps.

Current state: Phase 0 is proceed_regression_benchmark, and the Phase 1
readiness gate is ready_for_phase1_mvp. Toolz has a certified mini release and
healthy repaired workspace ACUT evidence. Humanize has a bounded second-repo
pilot with 12 certified tasks and an 8/8 scoreable Codex/Kilo matrix. The
current evidence still does not establish predictive validity.

Implement the Phase 1 MVP compiler. Do not run new paid ACUT task-solving calls
unless the runbook explicitly reaches a blocker that cannot be resolved from
existing committed artifacts, and stop before making any such call. This runbook
should be completed from existing Phase 0 artifacts.

All paid LLM or ACUT calls, if any are explicitly approved later, must use
LLM_BASE_URL + LLM_API_KEY. If either is missing, source ~/.zshrc and check
again. Do not use local Codex/ChatGPT subscription auth, OPENAI_API_KEY,
OpenRouter variables, or provider-specific keys unless the user's shell maps
them into LLM_API_KEY.

Keep Barcarolle on the benchmark/compiler side of the boundary. Barcarolle may
import task manifests, certification gates, score tables, usage ledgers, and
sanitized reports. It must not implement Codex, Kilo, or any other ACUT harness
internals.

Do not commit secrets, full raw prompts, raw completions, raw ACUT transcripts,
solver workspaces, verifier workspaces, cloned external repositories, .venv,
caches, or large logs. Commit only small sanitized manifests, schemas, tools,
tests, reports, and digests.
```

## Required Interpretation

Allowed Phase 1 scope:

```text
multi_repo_compiler_mvp
source_adapter_and_certification_infrastructure
workspace_acut_import_and_score_tables
readiness_and_artifact_hygiene_reports
```

Disallowed claims:

```text
predictive_validity_established
pure_harness_effect
production_benchmark_ranking
```

Use these claim labels in artifacts:

```text
phase1_mvp_compiler_infrastructure
insufficient_evidence_for_predictive_validation
same_endpoint_model_different_cli_harnesses
source_provenance_issue_derived
source_provenance_commit_message_fallback
generic_comparator_archived_click_r0
```

## Starting Artifacts

The worker should confirm these artifacts exist before implementation:

```text
experiments/phase0_headroom/results/pre_phase1_gate.json
experiments/phase0_headroom/reports/phase1_readiness_gate.md
experiments/phase0_headroom/releases/toolz_phase0_mini_release.json
experiments/phase0_headroom/releases/humanize_phase0_pilot_release.json
experiments/phase0_headroom/results/codex_kilo_workspace_followup_score_table.csv
experiments/phase0_headroom/results/codex_kilo_workspace_stability_score_table.csv
experiments/phase0_headroom/results/humanize_pre_phase1_workspace_score_table.csv
experiments/phase0_headroom/results/workspace_cost_reconciliation.json
experiments/phase0_headroom/results/workspace_usage_ledger.jsonl
experiments/phase1_compiler/tools/phase1_compiler.py
experiments/phase1_compiler/tests/test_phase1_compiler.py
```

## Budget Rules

This runbook should not require new paid model calls.

- New paid ACUT calls: `disabled_by_default`.
- New LLM calls for writing, summarizing, or formatting artifacts:
  `disabled_by_default`.
- Local tests, local JSON/CSV transforms, and local report generation: allowed.
- If a future worker believes a paid call is needed, stop and write a blocker
  report before making the call.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_mvp.yaml
  schemas/
    phase1_release.schema.json
    phase1_scorecard.schema.json
    phase1_certification_rollup.schema.json
  tools/
    phase1_compiler.py
  tests/
    test_phase1_compiler.py
  results/
    phase1_input_inventory.json
    phase1_certification_rollup.json
    phase1_mvp_release.json
    phase1_split_plan.json
    phase1_workspace_scorecard.json
    phase1_cost_summary.json
    phase1_weighted_score.json
    phase1_uncertainty_summary.json
    phase1_mvp_closeout.json
  reports/
    phase1_input_inventory.md
    phase1_certification_rollup.md
    phase1_split_plan.md
    phase1_workspace_scorecard.md
    phase1_cost_summary.md
    phase1_weighted_score.md
    phase1_uncertainty_summary.md
    phase1_mvp_closeout.md
```

Do not write raw prompts, completions, stdout logs, workspaces, external repos,
or `.venv` content into `experiments/phase1_compiler/`.

## Step 0: Preflight

Actions:

1. Record branch, HEAD, date, Python version, and `uv --version`.
2. Confirm Phase 1 readiness:

```bash
jq -r '.status' experiments/phase0_headroom/results/pre_phase1_gate.json
jq -r '.predictive_validity_established' experiments/phase0_headroom/results/pre_phase1_gate.json
```

Expected:

```text
ready_for_phase1_mvp
false
```

3. Confirm current tests and hygiene:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
git status --short --ignored experiments/phase0_headroom experiments/phase1_compiler docs/experiments AGENTS.md .gitignore
```

4. Confirm no ignored raw paths are tracked:

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

- readiness gate is `ready_for_phase1_mvp`;
- predictive validity is `false`;
- scoped tests pass;
- only ignored cache, raw, workspace, external repo, and venv paths appear as
  ignored files;
- no paid call is made.

Stop if:

- readiness gate is not `ready_for_phase1_mvp`;
- existing tests fail;
- raw or external-repo artifacts are tracked.

Commit only if this step writes a preflight report:

```text
Record Phase 1 MVP preflight
```

## Step 1: Create The Phase 1 MVP Config

Actions:

1. Create:

```text
experiments/phase1_compiler/configs/phase1_mvp.yaml
```

2. Import the allowed scope and disallowed claims from:

```text
experiments/phase0_headroom/results/pre_phase1_gate.json
```

3. Name all source artifacts explicitly.

Minimum shape:

```yaml
schema_version: barcarolle.phase1_mvp_config.v1
status: configured
claim_scope: phase1_mvp_compiler_infrastructure
predictive_validity_established: false
source_artifacts:
  readiness_gate: experiments/phase0_headroom/results/pre_phase1_gate.json
  toolz_release: experiments/phase0_headroom/releases/toolz_phase0_mini_release.json
  humanize_release: experiments/phase0_headroom/releases/humanize_phase0_pilot_release.json
  toolz_score_table: experiments/phase0_headroom/results/codex_kilo_workspace_followup_score_table.csv
  toolz_stability_score_table: experiments/phase0_headroom/results/codex_kilo_workspace_stability_score_table.csv
  humanize_score_table: experiments/phase0_headroom/results/humanize_pre_phase1_workspace_score_table.csv
  workspace_cost_reconciliation: experiments/phase0_headroom/results/workspace_cost_reconciliation.json
  workspace_usage_ledger: experiments/phase0_headroom/results/workspace_usage_ledger.jsonl
repos:
  - repo_id: toolz
    role: primary_target_repo
    source_provenance: source_provenance_issue_derived
  - repo_id: humanize
    role: second_target_repo
    source_provenance: source_provenance_commit_message_fallback
comparators:
  - repo_id: click
    role: generic_comparator
    source_provenance: generic_comparator_archived_click_r0
allowed_scope:
  - multi_repo_compiler_mvp
  - source_adapter_and_certification_infrastructure
  - workspace_acut_import_and_score_tables
  - readiness_and_artifact_hygiene_reports
disallowed_claims:
  - predictive_validity_established
  - pure_harness_effect
  - production_benchmark_ranking
```

Acceptance:

- config exists and references exact committed artifacts;
- config says predictive validity is `false`;
- config labels humanize provenance as `source_provenance_commit_message_fallback`;
- no existing Phase 0 artifact is rewritten.

Commit:

```text
Configure Phase 1 MVP compiler inputs
```

## Step 2: Add Input Inventory

Actions:

1. Extend `experiments/phase1_compiler/tools/phase1_compiler.py` with a command:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  inventory \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

2. The command should read only committed sanitized artifacts.
3. It should write:

```text
experiments/phase1_compiler/results/phase1_input_inventory.json
experiments/phase1_compiler/reports/phase1_input_inventory.md
```

Inventory fields:

```text
schema_version
generated_at
source_artifacts
repo_count
target_repos
generic_comparators
task_counts_by_repo
certified_task_counts_by_repo
score_table_counts
cost_summary_present
usage_ledger_call_count
known_limitations
```

Acceptance:

- inventory reports Toolz and humanize as target repos;
- inventory reports Click only as generic comparator;
- inventory records `predictive_validity_established=false`;
- tests cover missing artifact failure and normal inventory generation.

Stop if:

- required source artifacts are missing;
- the tool needs raw logs or ignored workspaces to build the inventory.

Commit:

```text
Add Phase 1 input inventory
```

## Step 3: Normalize Phase 1 Schemas

Actions:

1. Update or add schemas:

```text
experiments/phase1_compiler/schemas/phase1_release.schema.json
experiments/phase1_compiler/schemas/phase1_scorecard.schema.json
experiments/phase1_compiler/schemas/phase1_certification_rollup.schema.json
```

2. Keep schemas small but explicit. They must represent:
   - multiple repos;
   - repo roles;
   - source provenance strength;
   - release status;
   - task certification gates;
   - scorecard cells;
   - cost summary references;
   - claim scope;
   - disallowed claims.
3. Normalize release statuses:

```text
diagnostic_only
pilot_grade
benchmark_grade_candidate
validation_grade
```

4. Treat old booleans like `benchmark_grade=true` as legacy fields. The MVP
   release status should use the normalized enum above.
5. Add tests for:
   - valid multi-repo release;
   - invalid predictive-validity claim;
   - invalid repo role;
   - legacy humanize `benchmark_grade=true` not overriding
     `release_status=pilot_grade`.

Acceptance:

- schema tests pass;
- schema does not require Phase 1 predictive-validation fields that current
  evidence cannot supply;
- schema can represent weaker humanize provenance without hiding it.

Commit:

```text
Normalize Phase 1 MVP schemas
```

## Step 4: Import Multi-Repo Releases

Actions:

1. Add a command:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  build-release \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

2. It should import:
   - Toolz release as `primary_target_repo`;
   - humanize release as `second_target_repo`;
   - Click `G_mini` tasks as `generic_comparator` only.
3. It should write:

```text
experiments/phase1_compiler/results/phase1_mvp_release.json
```

4. The release must include:
   - `schema_version`;
   - `release_id`;
   - `status`;
   - `claim_scope`;
   - `predictive_validity_established=false`;
   - `repos`;
   - `tasks`;
   - `splits`;
   - `source_provenance`;
   - `certification_summary`;
   - `disallowed_claims`.
5. Preserve task IDs exactly. Do not rename Phase 0 task IDs.
6. Preserve source weakness:
   - Toolz: issue-derived or repaired source-adapter context;
   - humanize: commit-message fallback context;
   - Click: archived generic comparator.

Acceptance:

- release imports at least `6` Toolz certified tasks and `12` humanize
  certified tasks;
- release does not count Click tasks as target-repo eval tasks;
- release status is `pilot_grade` or `mvp_draft`, not `validation_grade`;
- release carries disallowed claims.

Stop if:

- importing humanize requires rewriting Phase 0 release files;
- Click comparator tasks are accidentally merged into target-repo task counts.

Commit:

```text
Import multi-repo Phase 1 release
```

## Step 5: Build Certification Rollup

Actions:

1. Add a command:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  certification-rollup \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

2. Read:
   - `toolz_certification_funnel.csv`;
   - `humanize_certification_funnel.csv`;
   - certified task JSONL files;
   - review records and statement records.
3. Write:

```text
experiments/phase1_compiler/results/phase1_certification_rollup.json
experiments/phase1_compiler/reports/phase1_certification_rollup.md
```

4. Roll up gates:

```text
checkout
oracle_extractable
no_op_fail
reference_pass
known_bad_fail
flakiness_check
ambiguity_review
solution_leakage_review
scope_clarity_review
cost_boundedness
taxonomy_labelability
```

5. Mark known source weaknesses:
   - humanize source context is commit-message fallback;
   - provider-billed cost remains unavailable;
   - no Phase 1 held-out future validation has been run.

Acceptance:

- rollup reports certified, near-certified, and rejected counts by repo;
- first failing gate counts are present;
- humanize provenance weakness is explicit;
- no raw issue bodies, raw diffs, or hidden tests are copied.

Commit:

```text
Add Phase 1 certification rollup
```

## Step 6: Add Split Plan

Actions:

1. Add a command:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  split-plan \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

2. Preserve existing historical Phase 0 splits:
   - `B_real`;
   - `W_real`;
   - `G_mini`.
3. Add Phase 1 split placeholders:
   - `dev`;
   - `eval`;
   - `canary`;
   - `future_holdout`.
4. Because no true future holdout exists yet, mark:

```text
future_holdout_status: unavailable_in_current_evidence
```

5. Write:

```text
experiments/phase1_compiler/results/phase1_split_plan.json
experiments/phase1_compiler/reports/phase1_split_plan.md
```

6. Include split constraints:
   - no task appears in more than one target-repo evaluation split unless the
     split plan labels it as a historical diagnostic reuse;
   - generic comparators cannot be canary or target-repo holdout tasks;
   - humanize tasks with commit-message fallback provenance remain allowed for
     MVP infrastructure but not for high-confidence validation claims.

Acceptance:

- split plan includes Toolz and humanize separately;
- Click remains comparator-only;
- future holdout is explicitly unavailable;
- report says Phase 1 validation is still future work.

Commit:

```text
Add Phase 1 split plan
```

## Step 7: Import Workspace ACUT Scorecards

Actions:

1. Add a command:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  import-scorecards \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

2. Import score tables:
   - repaired Toolz/Click matrix;
   - Toolz/Click stability matrix;
   - humanize pre-Phase1 matrix.
3. Normalize each cell to include:
   - `source_result_prefix`;
   - `repo_id`;
   - `task_id`;
   - `split`;
   - `adapter_id`;
   - `acut_id`;
   - `harness_name`;
   - `model_or_agent_name`;
   - `terminal_status`;
   - `scoreable_cell`;
   - `policy_violation`;
   - `agent_failure`;
   - `score`;
4. Map repo IDs:
   - `toolz__*` -> `toolz`;
   - `humanize__*` -> `humanize`;
   - `click__*` -> `click`.
5. Write:

```text
experiments/phase1_compiler/results/phase1_workspace_scorecard.json
experiments/phase1_compiler/reports/phase1_workspace_scorecard.md
```

Acceptance:

- scorecard imports all expected humanize cells: `8`;
- scorecard imports repaired Toolz/Click cells and the stability repeat as
  separate result prefixes, not as duplicate independent validation samples;
- scorecard labels the comparison as `same_endpoint_model_different_cli_harnesses`;
- policy violations remain visible and are not converted into verified failures.

Stop if:

- a score table lacks required columns;
- duplicate cells are merged without preserving source result prefix.

Commit:

```text
Import Phase 1 workspace scorecards
```

## Step 8: Import Cost And Usage Summary

Actions:

1. Add a command:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  cost-summary \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

2. Read:

```text
experiments/phase0_headroom/results/workspace_cost_reconciliation.json
experiments/phase0_headroom/results/workspace_usage_ledger.jsonl
experiments/phase0_headroom/reports/workspace_cost_usage_report.md
```

3. Write:

```text
experiments/phase1_compiler/results/phase1_cost_summary.json
experiments/phase1_compiler/reports/phase1_cost_summary.md
```

4. Include:
   - call count;
   - usage observed rate;
   - provider-billed cost status;
   - observed-token estimate;
   - observed-or-conservative estimate;
   - per-result-prefix cost;
   - per-harness cost when available;
   - pricing source.

Acceptance:

- report states provider-billed dollars are unavailable;
- report uses observed-token estimates from the local price table;
- cost is not used as a predictive-validity metric.

Commit:

```text
Import Phase 1 cost summary
```

## Step 9: Compute MVP Weighted Scores And Evidence Status

Actions:

1. Replace the current Toolz-only weighted score path with a multi-repo-aware
   command:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  weighted-score \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

2. Compute only scores supported by current evidence:
   - per-repo, per-split observed pass rates;
   - per-repo, per-module observed pass rates where coverage exists;
   - combined diagnostic score only if explicitly labeled `diagnostic`;
   - null predictive score.
3. Preserve `insufficient_evidence` when:
   - a target-profile stratum has no compatible cells;
   - cells are policy violations;
   - source provenance is too weak for validation-grade use;
   - no future holdout exists.
4. Write:

```text
experiments/phase1_compiler/results/phase1_weighted_score.json
experiments/phase1_compiler/reports/phase1_weighted_score.md
```

Minimum fields:

```text
schema_version
generated_at
claim_scope
predictive_validity_established
diagnostic_scores
stratum_scores
repo_scores
insufficient_evidence
disallowed_claims
```

Acceptance:

- `predictive_validity_established=false`;
- MAE, RMSE, Brier, NLL, and residual-improvement metrics remain
  `not_applicable_underpowered`;
- weighted score does not silently ignore missing strata;
- humanize provenance weakness is represented in evidence status.

Commit:

```text
Compute Phase 1 MVP weighted scores
```

## Step 10: Add Uncertainty Summary

Actions:

1. Add a command:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  uncertainty-summary \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

2. For current MVP evidence, use conservative descriptive intervals only:
   - binomial proportion interval for scoreable pass rates, if implemented
     locally without new dependencies;
   - otherwise explicit placeholder status.
3. Do not estimate predictive uncertainty over future work yet.
4. Write:

```text
experiments/phase1_compiler/results/phase1_uncertainty_summary.json
experiments/phase1_compiler/reports/phase1_uncertainty_summary.md
```

Acceptance:

- uncertainty report distinguishes observed score uncertainty from predictive
  validity;
- no interval is shown for unavailable future holdout prediction;
- report names required future data for MAE/RMSE/Brier.

Commit:

```text
Add Phase 1 uncertainty summary
```

## Step 11: Add CLI Orchestration

Actions:

1. Add a `build-mvp` command that runs the local Phase 1 commands in order:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  build-mvp \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

2. Expected command order:
   - `inventory`;
   - `build-release`;
   - `certification-rollup`;
   - `split-plan`;
   - `import-scorecards`;
   - `cost-summary`;
   - `weighted-score`;
   - `uncertainty-summary`;
   - `closeout`.
3. Each command should be idempotent and should overwrite only its own Phase 1
   result/report outputs.
4. Add `validate` command if useful:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

Acceptance:

- `build-mvp` produces the full output layout from a clean checkout with
  existing Phase 0 artifacts;
- tests cover command orchestration without making paid calls;
- commands fail closed on missing input artifacts.

Commit:

```text
Add Phase 1 MVP build command
```

## Step 12: Write MVP Closeout

Actions:

1. Add command:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  closeout \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

2. Write:

```text
experiments/phase1_compiler/results/phase1_mvp_closeout.json
experiments/phase1_compiler/reports/phase1_mvp_closeout.md
```

Closeout must include:

- release ID and status;
- repos imported;
- task counts by repo and source;
- certification counts by repo;
- scorecard cells by result prefix;
- cost summary;
- evidence status;
- allowed claims;
- disallowed claims;
- next runbook recommendation.

Recommended next runbook depends on result:

- If MVP build is healthy: write Phase 1 validation-design runbook.
- If source provenance is the main weakness: write source-adapter hardening
  runbook.
- If schema/import fragility is the main weakness: write compiler-hardening
  runbook.

Acceptance:

- closeout says `predictive_validity_established=false`;
- closeout does not present a production ranking;
- closeout states that `ready_for_phase1_mvp` has been consumed into an MVP
  compiler artifact.

Commit:

```text
Summarize Phase 1 MVP compiler
```

## Step 13: Update README And Documentation Links

Actions:

1. Update:

```text
experiments/phase1_compiler/README.md
```

2. Document:
   - how to run tests;
   - how to run `build-mvp`;
   - where outputs are written;
   - current evidence boundary;
   - which claims are disallowed.
3. If useful, add a short pointer from:

```text
experiments/phase0_headroom/README.md
```

Acceptance:

- README commands are copyable;
- README does not say Phase 1 predictive validation is complete;
- README names the MVP closeout report.

Commit:

```text
Document Phase 1 MVP compiler workflow
```

## Step 14: Final Verification

Actions:

1. Run:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  build-mvp \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
git diff --check
git status --short --ignored experiments/phase0_headroom experiments/phase1_compiler docs/experiments AGENTS.md .gitignore
```

2. Verify ignored raw paths are not tracked:

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

3. Commit any regenerated Phase 1 MVP artifacts that are small, sanitized, and
   intentionally part of the MVP output.

Acceptance:

- all scoped tests pass;
- `build-mvp` succeeds;
- branch is clean except ignored files after final commit;
- raw artifacts are not tracked;
- final answer lists commits created and next recommended runbook.

## Stop Conditions

Stop and write a blocker report if any of these occur:

- Phase 1 readiness gate is not `ready_for_phase1_mvp`;
- implementing the MVP requires new paid ACUT task-solving calls;
- raw logs, hidden tests, solver workspaces, or verifier workspaces would need
  to be committed;
- source artifacts are missing or inconsistent enough that imports would be
  misleading;
- schema changes would force predictive-validation claims.

## Expected End State

Successful completion should leave:

```text
experiments/phase1_compiler/results/phase1_mvp_release.json
experiments/phase1_compiler/results/phase1_workspace_scorecard.json
experiments/phase1_compiler/results/phase1_weighted_score.json
experiments/phase1_compiler/results/phase1_mvp_closeout.json
experiments/phase1_compiler/reports/phase1_mvp_closeout.md
```

Expected final decision:

```text
Phase 1 MVP compiler implemented.
Predictive validation not established.
Next step: Phase 1 validation-design runbook or source-adapter hardening,
depending on closeout limitations.
```
