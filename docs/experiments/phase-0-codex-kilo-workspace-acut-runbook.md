# Phase 0 Codex vs Kilo Workspace ACUT Runbook

Status: implementation and experiment runbook, 2026-05-21.

This runbook continues after
`docs/experiments/phase-0-workspace-acut-adapter-runbook.md` reached the good
fallback state:

- workspace ACUT adapter implemented;
- fake ACUT tests pass;
- no real endpoint-backed ACUT command configured;
- no paid workspace ACUT task-solving calls made.

The goal here is to configure and compare two realistic CLI agent harnesses:

```text
ACUT-Codex: Codex CLI workspace harness
ACUT-Kilo:  Kilo CLI workspace harness
```

This is a realistic harness-level ACUT comparison, not a single-variable
ablation. Prefer the same endpoint model for both harnesses. If that is not
possible, label the run as a bundled ACUT comparison where harness, model,
tooling policy, and implementation details may all differ.

## Research Question

Can Barcarolle's Phase 0 release and workspace adapter produce scoreable,
same-protocol evidence for two real CLI agent harnesses, and does the resulting
`G_mini`, `B_real`, and `W_real` pattern justify continuing toward predictive or
tuning-feedback validation?

The immediate blocker to remove is not model intelligence. It is the absence of
a configured endpoint-backed workspace ACUT harness.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-0-codex-kilo-workspace-acut-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.

Configure Codex CLI and Kilo CLI as two realistic workspace ACUT harnesses for
the existing Phase 0 workspace adapter. Barcarolle must not implement either
agent harness. It prepares clean solver workspaces, invokes each configured CLI
harness, captures git diff, and verifies patches in fresh hidden-oracle
workspaces.

All paid LLM and ACUT calls must use LLM_BASE_URL + LLM_API_KEY. If either is
missing, source ~/.zshrc and check again. Do not use local Codex/ChatGPT
subscription auth. Do not use OPENAI_API_KEY, OpenRouter variables, or other
provider-specific variables unless the user's shell maps them into LLM_API_KEY.

Do not run scoreable task-solving calls for a harness until its endpoint-backed
execution is proven or a precise blocker is recorded. Do not fall back to the
old diff-only prompt path.

Implement multi-ACUT config and result isolation first. Then run per-harness
preflight. If both harnesses pass, run a 2-cell smoke per harness. If smoke
passes, run the 20-cell Codex-vs-Kilo matrix. Commit cohesive checkpoints.
```

## Required Interpretation

Use these labels in reports:

```text
same_model_cross_harness
bundled_acut_cross_harness
codex_eligible
codex_blocked_endpoint_proof
kilo_eligible
kilo_blocked_endpoint_proof
```

Preferred claim if both harnesses can run the same endpoint model:

```text
Same endpoint model, different CLI harnesses.
```

Fallback claim if model identity cannot be matched:

```text
Bundled ACUT comparison: Codex CLI configuration versus Kilo CLI configuration.
The result is realistic but does not identify a pure harness effect.
```

Do not claim that differences are caused by harness alone unless the model,
budget, endpoint, solver-visible statement, workspace, and task set are matched.

## Budget Rules

Incremental cap for this run:

- soft cap: `USD 10`;
- hard cap: `USD 25`;
- stop before any batch whose projected incremental spend exceeds `USD 15`;
- do not run parallel paid ACUT task-solving calls;
- run Codex and Kilo cells sequentially;
- do not start the 20-cell matrix until smoke results are scoreable enough.

Stop if cost is not observable and cannot be conservatively estimated. If a
harness cannot export usage, record elapsed time and available harness stats,
then use a conservative per-cell estimate in the cost ledger before any scale-up.

## Output Layout

Add or update:

```text
experiments/phase0_headroom/
  configs/
    acut_workspace_adapters.yaml
    codex_kilo_workspace_matrix.yaml
  results/
    codex_kilo_workspace_preflight.json
    codex_kilo_workspace_submissions.jsonl
    codex_kilo_workspace_verifier_results.jsonl
    codex_kilo_workspace_score_table.csv
    codex_kilo_workspace_matrix.json
    codex_kilo_workspace_metrics.json
    codex_kilo_workspace_cost_ledger.jsonl
    codex_kilo_workspace_cost_summary.json
  reports/
    codex_kilo_workspace_preflight.md
    codex_kilo_workspace_process.md
    codex_kilo_workspace_analysis.md
    phase0_decision_memo.md
```

Raw logs and workspaces must remain ignored:

```text
experiments/phase0_headroom/results/raw/workspace_acut/
experiments/phase0_headroom/workspaces/workspace_acut/
```

Do not overwrite the single-ACUT good-fallback artifacts unless a report clearly
states they were superseded.

## Step 0: Preflight

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, `codex --version`,
   and `kilo --version`.
2. Confirm command availability:

```bash
command -v codex
command -v kilo
codex exec --help
kilo run --help
```

3. Source shell config if needed and verify endpoint variables:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

4. Confirm current Phase 0 evidence exists:
   - `reports/workspace_acut_preflight.md`
   - `reports/overnight_research_report.md`
   - `results/generic_comparator_protocol.json`
   - `reports/phase0_decision_memo.md`
5. Run:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
```

Acceptance:

- `codex` and `kilo` commands are present;
- endpoint variables are present;
- existing tests pass;
- current worktree state is understood;
- no raw workspace/log paths are tracked.

Stop if:

- either CLI is missing;
- endpoint variables are missing;
- the workspace adapter tests fail;
- generic comparator same-protocol count is below `3`.

## Step 1: Extend Adapter To Multi-ACUT Config

Current `workspace_acut_run.py` was implemented for a single configured ACUT.
Extend it without breaking the existing single-ACUT commands.

Actions:

1. Add support for:
   - `--adapter-config`
   - `--adapter-id`
   - `--matrix-config`
   - `--result-prefix`
2. Create `configs/acut_workspace_adapters.yaml` with an `adapters` list.
3. Preserve compatibility with `configs/acut_workspace_adapter.yaml`.
4. Ensure result rows include:
   - `adapter_id`;
   - `acut_id`;
   - `harness_name`;
   - `model_or_agent_name`;
   - `command_template_source`;
   - `endpoint_proof_status`.
5. Ensure Codex and Kilo runs cannot overwrite each other's raw logs or
   workspaces.
6. Add tests proving:
   - two fake adapters can run the same task and produce distinct run IDs;
   - result prefixes isolate outputs;
   - missing adapter id is a preflight error;
   - old single-adapter behavior still works.

Acceptance:

- Phase 0 tests pass;
- existing single-ACUT good-fallback artifacts remain readable;
- multi-ACUT result files can be written without clobbering prior results.

Commit:

```text
Support multi-ACUT workspace adapter configs
```

## Step 2: Configure Codex And Kilo As Candidate ACUTs

Create:

```text
experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
```

Minimum shape:

```yaml
schema_version: barcarolle.acut_workspace_adapters_config.v1
preferred_model: gpt-5.4-mini
comparison_design: same_model_cross_harness
adapters:
  - adapter_id: codex_workspace
    harness_name: codex
    acut_id: codex_workspace_gpt_5_4_mini
    model_or_agent_name: gpt-5.4-mini
    command_template: ""
    timeout_seconds: 900
    requires_env:
      - LLM_BASE_URL
      - LLM_API_KEY
    endpoint_proof:
      required: true
      isolated_auth_required: true
      status: pending
  - adapter_id: kilo_workspace
    harness_name: kilo
    acut_id: kilo_workspace_gpt_5_4_mini
    model_or_agent_name: gpt-5.4-mini
    command_template: ""
    timeout_seconds: 900
    requires_env:
      - LLM_BASE_URL
      - LLM_API_KEY
    endpoint_proof:
      required: true
      isolated_auth_required: true
      status: pending
```

Candidate command shapes may look like this, but must be verified locally:

```text
codex exec --json --ephemeral --ask-for-approval never --sandbox workspace-write --cd {workspace} --model gpt-5.4-mini "Read {statement_file}, inspect the repository, modify code only, do not edit tests, and stop when done."
```

```text
kilo run --dir {workspace} --auto --format json --model <provider>/gpt-5.4-mini --file {statement_file} "Inspect the repository, modify code only, do not edit tests, and stop when done."
```

These examples are not accepted until endpoint proof passes. Adjust flags to the
actual installed CLI behavior.

Acceptance:

- both command templates are syntactically valid for the installed CLI;
- both templates mutate `{workspace}` rather than emitting a patch to stdout;
- both templates deliver the task through `{statement_file}`;
- both templates write raw logs only under ignored paths or CLI-managed ignored
  session stores;
- model identity is either matched or explicitly labeled as a bundled ACUT
  comparison.

Commit:

```text
Configure Codex and Kilo workspace ACUT candidates
```

## Step 3: Endpoint-Backed Eligibility Proof

This is the most important gate. Do not run scoreable task-solving calls until
both harnesses either pass or are recorded as blocked.

For each harness:

1. Run a no-task connectivity probe if the CLI supports it.
2. Prefer isolated auth/config homes where practical:
   - for Codex, use an isolated `CODEX_HOME` if endpoint config can be supplied
     without local ChatGPT auth;
   - for Kilo, use an isolated Kilo config/cache location if supported or a
     documented provider config that relies only on `LLM_BASE_URL` and
     `LLM_API_KEY`.
3. Confirm the harness can run without local Codex/ChatGPT subscription auth.
4. Confirm the harness sees `LLM_BASE_URL` and `LLM_API_KEY`.
5. Confirm selected model is available from
   `results/endpoint_models.json` or document an explicit endpoint model
   override.
6. Record whether usage/cost is:
   - directly reported by the harness;
   - available from endpoint logs;
   - conservatively estimated.

Write:

```text
results/codex_kilo_workspace_preflight.json
reports/codex_kilo_workspace_preflight.md
```

Required statuses:

```text
codex_eligible
codex_blocked_endpoint_proof
kilo_eligible
kilo_blocked_endpoint_proof
```

Acceptance for a harness:

- command exists;
- command template renders;
- endpoint variables are present;
- selected model is known;
- no local subscription fallback is needed;
- no scoreable calls are made before this status is written.

Stop or partially proceed:

- If both harnesses are blocked, stop and write a blocker report.
- If one harness is eligible and the other is blocked, run at most that
  harness's smoke subset and mark the comparison incomplete.
- If both are eligible, continue to Step 4.

Commit:

```text
Record Codex Kilo workspace ACUT eligibility
```

## Step 4: Build The Codex/Kilo Matrix

Create:

```text
experiments/phase0_headroom/configs/codex_kilo_workspace_matrix.yaml
```

Matrix:

```text
ACUTs:
  - codex_workspace
  - kilo_workspace

Tasks:
  B_real:
    - toolz__hist__001
    - toolz__hist__002
    - toolz__hist__003
  W_real:
    - toolz__hist__004
    - toolz__hist__010
    - toolz__hist__016
  G_mini:
    - click__rbench__001
    - click__rbench__002
    - click__rbench__003
    - click__rbench__004
```

Planned cells:

```text
smoke: 2 cells per harness, 4 total
full matrix: 10 cells per harness, 20 total
```

Recommended smoke cells:

```text
toolz__hist__002
click__rbench__001
```

These both failed as invalid/corrupt-patch under the old diff-only protocol, so
they directly test whether workspace editing removes the old blocker.

Acceptance:

- every scheduled task has base checkout and verifier metadata;
- every `G_mini` task remains `scoreable_same_protocol`;
- projected smoke and full-matrix costs are recorded;
- full matrix remains disabled until smoke passes.

Commit:

```text
Configure Codex Kilo workspace matrix
```

## Step 5: Smoke Run

Run smoke sequentially:

```text
codex_workspace x toolz__hist__002
codex_workspace x click__rbench__001
kilo_workspace  x toolz__hist__002
kilo_workspace  x click__rbench__001
```

Actions:

1. Append projected-cost rows before the batch.
2. Run one cell at a time through the workspace adapter.
3. For each cell, verify:
   - solver workspace has no hidden material;
   - ACUT mutated the workspace or produced a classified no-diff result;
   - patch source is `git_diff_after_workspace_run`;
   - changed-path policy runs before hidden verification;
   - verifier workspace is fresh;
   - terminal status is recorded.
4. Write smoke results to the Codex/Kilo result files.

Acceptance:

- each eligible harness reaches terminal status for both smoke cells;
- at least one cell per eligible harness is scoreable;
- no corrupt model-emitted patch category appears;
- no hidden verifier material appears in solver workspaces;
- costs are recorded or conservatively estimated.

Stop before full matrix if:

- either eligible harness has `0` scoreable smoke cells;
- either harness edits prohibited tests in both smoke cells;
- endpoint usage/cost cannot be observed or bounded;
- workspace replay fails because of Barcarolle adapter bugs.

Commit:

```text
Run Codex Kilo workspace smoke
```

or:

```text
Document Codex Kilo workspace smoke blocker
```

## Step 6: Full 20-Cell Matrix

Run only if Step 5 passes.

Actions:

1. Run all `2 x 10` cells sequentially.
2. Do not parallelize paid task-solving calls.
3. Reuse smoke cells only if the command template, adapter code, and task
   package are unchanged.
4. For each cell, write:
   - submission row;
   - verifier row;
   - cost row;
   - raw artifact references under ignored paths;
   - terminal status.
5. Preserve terminal status taxonomy:
   - `verified_pass`
   - `verified_fail`
   - `invalid_output`
   - `acut_harness_error`
   - `policy_violation`
   - `harness_error`
   - `timeout`

Acceptance:

- every scheduled cell has terminal status;
- scoreable-cell rate is reported separately for Codex and Kilo;
- `G_mini` has enough scoreable cells per harness to say whether
  `G_mini -> W_real` is available;
- failures are not dominated by Barcarolle-side harness errors.

Stop if:

- projected incremental spend would exceed `USD 15`;
- one harness becomes ineligible during the run;
- Barcarolle exposes hidden verifier material to solver workspaces;
- fresh verifier replay fails for Git-captured patches because of adapter bugs.

Commit:

```text
Run Codex Kilo workspace Phase 0 matrix
```

## Step 7: Analysis

Write:

```text
reports/codex_kilo_workspace_analysis.md
results/codex_kilo_workspace_metrics.json
results/codex_kilo_workspace_cost_summary.json
```

Required analysis:

1. Eligibility:
   - Codex endpoint proof;
   - Kilo endpoint proof;
   - same-model or bundled-ACUT label.
2. Scoreability:
   - submitted cells;
   - scoreable cells;
   - scoreable rate by harness and split;
   - invalid/policy/harness/timeout counts.
3. Performance:
   - verified pass/fail by harness and split;
   - `B_real`, `W_real`, `G_mini` split summaries;
   - whether `G_mini -> W_real` is available;
   - whether `G_mini + B_real -> W_real` is available.
4. Cost:
   - estimated and actual cost fields;
   - cost per submitted cell;
   - cost per scoreable cell;
   - median latency.
5. Validity:
   - underpowered sample warning;
   - model mismatch if any;
   - harness/tooling differences;
   - task clustering;
   - recovered Click comparator caveat.

Do not report MAE, RMSE, Brier, or ordering accuracy as meaningful unless the
sample size and predictor setup justify them. Otherwise mark:

```text
not_applicable_underpowered
```

Acceptance:

- the report can be read without raw logs;
- old diff-only Matrix A is treated as historical diagnostic evidence;
- the analysis states whether the workspace adapter resolved the corrupt patch
  failure mode;
- the analysis does not overclaim pure harness causality if model/configs differ.

## Step 8: Update Phase 0 Decision

Update:

```text
experiments/phase0_headroom/reports/phase0_decision_memo.md
```

Allowed decisions:

- `proceed_predictive`;
- `proceed_tuning_feedback`;
- `proceed_regression_benchmark`;
- `repair_source_adapter`;
- `stop`.

Decision guidance:

- Use `proceed_predictive` only if both harnesses produce enough same-protocol
  `B_real`, `W_real`, and `G_mini` scoreable cells to support the next
  predictive-validity experiment.
- Use `proceed_tuning_feedback` if the two-harness run is most useful as a
  repo-specific optimizer/harness-selection substrate.
- Use `proceed_regression_benchmark` if workspace execution is scoreable but
  too underpowered for predictive claims.
- Use `stop` only if realistic workspace harness evaluation remains dominated
  by infrastructure ambiguity.

Acceptance:

- the memo says whether Codex/Kilo were both eligible;
- the memo names the active scoreable protocol as workspace ACUT adapter;
- the next smallest useful experiment is concrete.

Commit:

```text
Update Phase 0 decision after Codex Kilo workspace run
```

## Step 9: Optional Phase 1 Refresh

Run only if the matrix completed.

Actions:

1. Import Codex/Kilo score rows into the Phase 1 compiler skeleton.
2. Regenerate:
   - `experiments/phase1_compiler/results/toolz_phase1_draft_release.json`
   - `experiments/phase1_compiler/results/toolz_phase1_weighted_score.json`
3. Preserve `insufficient_evidence` labels for empty strata.
4. Run:

```bash
uv run --project experiments/phase1_compiler pytest -q
```

Acceptance:

- Phase 1 artifacts clearly identify Codex/Kilo ACUTs;
- weighted score is computed only where evidence is compatible;
- no predictive-validity claim is silently introduced.

Commit:

```text
Refresh Phase 1 compiler artifacts from Codex Kilo matrix
```

## Step 10: Final Hygiene

Actions:

1. Run:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
test ! -d experiments/phase1_compiler || uv run --project experiments/phase1_compiler pytest -q
git status --short --ignored experiments/phase0_headroom experiments/phase1_compiler docs/experiments AGENTS.md .gitignore
```

2. Confirm no raw prompts, completions, ACUT transcripts, solver workspaces,
   verifier workspaces, cloned repositories, `.venv`, caches, or full logs are
   staged.
3. Ensure `reports/codex_kilo_workspace_process.md` records:
   - branch and commits;
   - eligibility decisions;
   - smoke decision;
   - full matrix decision;
   - cost;
   - next smallest useful runbook.

Final commit:

```text
Summarize Codex Kilo workspace ACUT experiment
```

Do not push unless the user explicitly asks.

## Success Criteria

Best case:

- Codex and Kilo both prove endpoint-backed workspace execution;
- both smoke subsets pass;
- 20-cell matrix completes;
- scoreable-cell rate is materially better than old diff-only Matrix A;
- `G_mini` cells become scoreable for both harnesses;
- Phase 0 decision can move to `proceed_tuning_feedback` or a well-scoped
  predictive follow-up.

Good fallback:

- one or both harnesses are blocked by endpoint proof or CLI configuration;
- no wrong-endpoint paid calls are made;
- adapter remains tested;
- blocker report says exactly which command/config/proof is missing.

Unacceptable outcomes:

- using local Codex/ChatGPT subscription auth as scoreable evidence;
- using the old one-shot diff-only prompt as the scoreable protocol;
- exposing hidden verifier material in solver workspaces;
- treating a bundled ACUT comparison as a pure harness effect;
- claiming predictive validity from harness-dominated or underpowered cells.
