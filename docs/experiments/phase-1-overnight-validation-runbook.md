# Phase 1 Overnight Validation Runbook

Status: overnight handoff runbook, 2026-05-21.

This runbook is for one unattended Codex CLI session. Its job is to push beyond
the Phase 1 MVP compiler as far as the current evidence, endpoint, cost, and
artifact hygiene allow.

The goal is not to spend the budget. The goal is to turn the overnight window
into one of these outcomes:

- a healthy Phase 1 operational validation pilot with new scoreable cells;
- a stronger multi-repo validation candidate with a third target repo;
- a precise blocker report that says which layer prevents validation-grade
  claims.

## Current Starting Point

The expected starting state is the completed Phase 1 MVP compiler:

```text
experiments/phase1_compiler/reports/phase1_mvp_closeout.md
status: pilot_grade
predictive_validity_established: false
evidence_status: mvp_compiler_artifacts_built_insufficient_for_predictive_validation
```

Known evidence:

- Toolz: `6` certified target tasks, already used in Codex/Kilo workspace
  matrices.
- Humanize: `12` certified target tasks, but only `4` tasks have been used in
  the Codex/Kilo workspace pilot.
- Click: generic comparator only, not a target repo.
- Current workspace cost summary: `77` calls, usage observed rate about `0.92`,
  observed-or-conservative estimated spend about `USD 22.56`, provider-billed
  cost unavailable.
- Current disallowed claims remain:
  `predictive_validity_established`, `pure_harness_effect`, and
  `production_benchmark_ranking`.

The most useful unattended path is therefore:

1. harden or at least audit source provenance, especially Humanize;
2. run new workspace ACUT cells on Humanize tasks that were certified but not
   previously solved by either harness;
3. if the run is healthy and cheap, add a stability repeat or a third target repo
   pilot;
4. rebuild Phase 1 summaries without overstating predictive validity.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-1-overnight-validation-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make cohesive commits after completing one or more related steps.

Current state: Phase 1 MVP compiler is complete and pilot_grade. It does not
establish predictive validity. The next job is an overnight Phase 1 validation
pilot: source-provenance audit/hardening, new Humanize held-out workspace ACUT
cells, optional stability repeat, and optional third-repo pilot if the early
branches are healthy and cheap.

All paid LLM or ACUT calls must use LLM_BASE_URL + LLM_API_KEY. If either
variable is missing, source ~/.zshrc and check again. Do not use local
Codex/ChatGPT subscription auth, OPENAI_API_KEY, OpenRouter variables, or
provider-specific variables unless the user's shell explicitly maps them into
LLM_API_KEY.

Keep Barcarolle on the benchmark/compiler side of the boundary. Use the existing
workspace ACUT adapter. Do not implement Codex, Kilo, or any other ACUT harness
internals. Barcarolle should prepare workspaces, invoke configured harnesses,
capture git diffs, verify in fresh verifier workspaces, and record sanitized
results.

Do not commit secrets, full raw prompts, raw completions, raw ACUT transcripts,
solver workspaces, verifier workspaces, cloned external repositories, .venv,
caches, or large raw outputs. Commit only small sanitized configs, manifests,
tools, tests, reports, summaries, and digests.

Run paid ACUT work sequentially. After every paid batch, import usage, update
cost summaries, run scoped tests, and commit the sanitized checkpoint before
starting the next paid batch.
```

## Claim Boundary

Allowed claims for this overnight run:

```text
phase1_operational_validation_pilot
phase1_internal_unseen_acut_holdout
same_endpoint_model_different_cli_harnesses
source_provenance_audited
cost_bounded_workspace_acut_run
third_repo_pilot_candidate
insufficient_evidence_for_predictive_validation
```

Disallowed claims:

```text
predictive_validity_established
future_holdout_predictive_validity
pure_harness_effect
production_benchmark_ranking
general_swe_task_factory
agent_license_product
```

Important wording:

- Humanize tasks not previously solved by Codex/Kilo may be called
  `internal_unseen_acut_holdout`.
- Do not call them `future_holdout`, because they were already certified before
  this overnight run.
- A stability repeat is reliability evidence, not independent validation
  evidence.
- A third repo pilot can improve external validity, but it still needs a later
  pre-registered validation design before predictive-validity claims.

## Budget And Runtime Rules

Use the measured budget file as the absolute project boundary:

```text
experiments/phase0_headroom/configs/measured_budget.yaml
hard_cap_usd: 200
soft_stop_usd: 160
stop_and_ask_usd: 180
```

Overnight incremental caps:

- soft cap: `USD 80` observed-or-conservative incremental spend;
- hard cap: `USD 120` observed-or-conservative incremental spend;
- absolute unattended stop: projected cumulative spend reaches `USD 160`;
- stop before any batch whose projected cumulative spend reaches `USD 140`;
- stop if usage observed rate drops below `0.85` after a paid batch;
- stop if provider-billed cost becomes available and contradicts local estimates
  by more than `2x`.

Batch rules:

- Paid ACUT concurrency is `1`.
- Local checkout, certification, summarization, and verifier replay may use
  parallelism only when outputs are isolated.
- Record projected cost before each paid batch in the process report.
- Import usage immediately after each paid batch.
- Do not start the next paid batch if the previous batch has unresolved
  scoreability, policy, endpoint, or cost-accounting blockers.
- Prefer new task coverage over repeating old cells. Run stability repeats only
  after new held-out cells are healthy.

Conservative cost planning:

- The current runner uses `USD 0.50` conservative estimate per workspace cell
  when usage is missing.
- The first smoke batch is `4` cells, projected at `USD 2.00` conservative.
- The main Humanize holdout batch is `12` cells, projected at `USD 6.00`
  conservative.
- The optional Humanize stability repeat is `16` cells, projected at
  `USD 8.00` conservative.
- The optional third-repo pilot should not exceed `16` paid cells unless the
  cumulative observed-or-conservative spend remains below `USD 80`.

## Output Layout

Use these committed output files for sanitized overnight state:

```text
experiments/phase1_compiler/
  configs/
    phase1_validation_overnight.yaml
  results/
    phase1_validation_overnight_plan.json
    phase1_source_provenance_audit.json
    phase1_validation_overnight_decision.json
  reports/
    phase1_validation_overnight_process.md
    phase1_source_provenance_audit.md
    phase1_validation_overnight_report.md
```

Use existing Phase 0 workspace ACUT result locations for score tables and usage:

```text
experiments/phase0_headroom/results/
  phase1_validation_humanize_holdout_smoke_*.json*
  phase1_validation_humanize_holdout_*.json*
  phase1_validation_humanize_holdout_stability_*.json*
  phase1_validation_third_repo_<repo_id>_*.json*
```

Raw harness output, workspaces, and cloned repos must remain under ignored paths:

```text
experiments/phase0_headroom/results/raw/
experiments/phase0_headroom/workspaces/
experiments/phase0_headroom/external_repos/
```

## Step 0: Preflight

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`,
   `codex --version` if available, and `kilo --version` if available.
2. Confirm endpoint variables:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

3. Confirm Phase 1 MVP state:

```bash
jq -r '.predictive_validity_established' experiments/phase1_compiler/results/phase1_mvp_closeout.json
jq -r '.evidence_status' experiments/phase1_compiler/results/phase1_mvp_closeout.json
jq -r '.status' experiments/phase1_compiler/results/phase1_mvp_release.json
```

Expected:

```text
false
mvp_compiler_artifacts_built_insufficient_for_predictive_validation
pilot_grade
```

4. Run hygiene checks:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
git status --short --ignored experiments/phase0_headroom experiments/phase1_compiler docs/experiments AGENTS.md .gitignore
```

5. Confirm ignored raw paths are not tracked:

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

6. Create or update:

```text
experiments/phase1_compiler/reports/phase1_validation_overnight_process.md
```

Acceptance:

- endpoint variables exist after sourcing `~/.zshrc`;
- scoped tests pass;
- Phase 1 MVP validates;
- no raw artifacts are tracked;
- the process report names the starting HEAD and current cost summary.

Stop if:

- endpoint variables are missing;
- Phase 1 MVP artifacts are absent or invalid;
- existing tests fail;
- raw workspaces, raw transcripts, external repos, or caches are tracked.

Commit if the process report was created:

```text
Record Phase 1 overnight validation preflight
```

## Step 1: Write The Overnight Validation Plan

Actions:

1. Create:

```text
experiments/phase1_compiler/configs/phase1_validation_overnight.yaml
experiments/phase1_compiler/results/phase1_validation_overnight_plan.json
```

2. The YAML config should name:

```yaml
schema_version: barcarolle.phase1_validation_overnight_config.v1
status: configured
claim_scope: phase1_operational_validation_pilot
predictive_validity_established: false
adapter_config: experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
adapters:
  - codex_workspace
  - kilo_workspace
result_prefixes:
  smoke: phase1_validation_humanize_holdout_smoke
  main: phase1_validation_humanize_holdout
  stability: phase1_validation_humanize_holdout_stability
humanize_internal_unseen_acut_holdout:
  smoke_task_ids:
    - humanize__hist__002
    - humanize__hist__010
  main_task_ids:
    - humanize__hist__003
    - humanize__hist__004
    - humanize__hist__007
    - humanize__hist__008
    - humanize__hist__012
    - humanize__hist__015
  already_solved_task_ids:
    - humanize__hist__005
    - humanize__hist__006
    - humanize__hist__013
    - humanize__hist__014
budget:
  incremental_soft_cap_usd: 80
  incremental_hard_cap_usd: 120
  cumulative_unattended_stop_usd: 160
  conservative_cell_estimate_usd: 0.50
parallelism:
  paid_acut_concurrency: 1
  local_verify_concurrency: 4
claim_boundary:
  heldout_label: internal_unseen_acut_holdout_not_future_holdout
  predictive_validity_established: false
```

3. The JSON plan should include the same task IDs plus:
   - current cost baseline;
   - projected smoke/main/stability cell counts;
   - continue/stop thresholds;
   - explicit statement that this plan does not establish predictive validity.

Acceptance:

- plan excludes the four Humanize tasks already solved in
  `humanize_pre_phase1_workspace_score_table.csv`;
- plan includes both `B_real` and `W_real` tasks;
- projected costs are below the overnight hard cap;
- no paid call has been made.

Commit:

```text
Plan Phase 1 overnight validation pilot
```

## Step 2: Audit And Harden Source Provenance

This step is local or GitHub-metadata-only. It should not make paid LLM calls.

Actions:

1. Add or update a small deterministic provenance audit. It may be a new command
   in `experiments/phase1_compiler/tools/phase1_compiler.py` or a small helper
   under `experiments/phase1_compiler/tools/`.
2. Read:

```text
experiments/phase0_headroom/candidate_sources/toolz_source_context.jsonl
experiments/phase0_headroom/candidate_sources/humanize_source_context.jsonl
experiments/phase0_headroom/certified_tasks/toolz_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/humanize_certified_tasks.jsonl
```

3. Produce:

```text
experiments/phase1_compiler/results/phase1_source_provenance_audit.json
experiments/phase1_compiler/reports/phase1_source_provenance_audit.md
```

4. The audit must count, per repo:
   - certified task count;
   - tasks with issue-derived or PR-derived source context;
   - tasks with commit-message fallback only;
   - tasks with missing source context;
   - tasks whose solver-facing statement appears to expose the solution.
5. If `gh` is authenticated and network is available, try to improve Humanize
   provenance by querying PR metadata for the 12 certified Humanize target
   commits:

```bash
gh auth status
```

For each target commit, use sanitized metadata only:

```bash
gh api repos/python-humanize/humanize/commits/<target_commit>/pulls \
  -H 'Accept: application/vnd.github.groot-preview+json'
```

6. Do not commit raw API responses. Store only compact sanitized fields:
   PR number, title, body digest or short summary, source kind, classification,
   and task ID.

Acceptance:

- audit report states whether Humanize remains
  `source_provenance_commit_message_fallback`;
- if at least `6` Humanize certified tasks have non-fallback PR/issue context,
  mark `humanize_source_provenance_hardened`;
- otherwise mark `humanize_source_provenance_fallback_confirmed`;
- no raw GitHub response is committed;
- no paid LLM call is made.

Commit:

```text
Audit Phase 1 source provenance
```

## Step 3: Reconfirm Adapter And Cost Gates

Actions:

1. Preflight both adapters:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --result-prefix phase1_validation_humanize_holdout_smoke

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --result-prefix phase1_validation_humanize_holdout_smoke
```

2. Record projected smoke cost:

```text
4 cells * USD 0.50 conservative = USD 2.00
```

3. Append the projection and current cumulative cost to
   `phase1_validation_overnight_process.md`.

Acceptance:

- adapter preflights pass for both Codex and Kilo;
- endpoint proof remains eligible for both adapters;
- projected cumulative cost remains below `USD 140`;
- no paid task-solving call starts until this step passes.

Stop if:

- either adapter cannot prove it uses `LLM_BASE_URL` plus `LLM_API_KEY`;
- either adapter would fall back to local subscription auth;
- current cumulative spend cannot be bounded.

Commit if preflight artifacts or reports changed:

```text
Record Phase 1 validation adapter preflight
```

## Step 4: Run Humanize Holdout Smoke

This is the first paid batch. It uses one B task and one W task that were not in
the earlier Humanize workspace pilot.

Task IDs:

```text
humanize__hist__002
humanize__hist__010
```

Actions:

1. Run Codex sequentially:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_validation_overnight.yaml \
  --result-prefix phase1_validation_humanize_holdout_smoke \
  --task-id humanize__hist__002 \
  --task-id humanize__hist__010 \
  --timeout-seconds 900
```

2. Run Kilo sequentially:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_validation_overnight.yaml \
  --result-prefix phase1_validation_humanize_holdout_smoke \
  --task-id humanize__hist__002 \
  --task-id humanize__hist__010 \
  --timeout-seconds 900
```

3. Import usage:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_usage_import.py \
  --root . \
  --result-prefix phase1_validation_humanize_holdout_smoke \
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --allow-missing-price-estimate
```

4. Summarize:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  summarize \
  --result-prefix phase1_validation_humanize_holdout_smoke
```

Acceptance:

- `phase1_validation_humanize_holdout_smoke_score_table.csv` exists;
- at least `3` of `4` cells are scoreable;
- policy violation count is `0`;
- usage observed rate is at least `0.85`, or the observed-or-conservative
  estimate remains below the smoke hard cap;
- no solver workspace contains hidden oracle material.

Branch:

- If smoke passes, continue to Step 5.
- If smoke has adapter or endpoint errors, skip paid work and go to Step 9.
- If smoke has many verified failures but cells are scoreable, continue to
  Step 5; failures are valid experimental signal.
- If smoke has policy violations, stop paid work and write a blocker report.

Commit:

```text
Run Phase 1 Humanize holdout smoke
```

## Step 5: Run The Main Humanize Holdout Batch

This is the second paid batch. It runs the remaining six Humanize certified tasks
that have not been solved by either Codex or Kilo.

Task IDs:

```text
humanize__hist__003
humanize__hist__004
humanize__hist__007
humanize__hist__008
humanize__hist__012
humanize__hist__015
```

Projected conservative cost:

```text
12 cells * USD 0.50 = USD 6.00
```

Actions:

1. Recheck cost before starting:

```bash
jq '.observed_or_conservative_estimated_cost_usd // .totals.observed_or_conservative_estimated_cost_usd' \
  experiments/phase0_headroom/results/workspace_cost_reconciliation.json
```

2. Run Codex:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_validation_overnight.yaml \
  --result-prefix phase1_validation_humanize_holdout \
  --task-id humanize__hist__003 \
  --task-id humanize__hist__004 \
  --task-id humanize__hist__007 \
  --task-id humanize__hist__008 \
  --task-id humanize__hist__012 \
  --task-id humanize__hist__015 \
  --timeout-seconds 900
```

3. Run Kilo:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_validation_overnight.yaml \
  --result-prefix phase1_validation_humanize_holdout \
  --task-id humanize__hist__003 \
  --task-id humanize__hist__004 \
  --task-id humanize__hist__007 \
  --task-id humanize__hist__008 \
  --task-id humanize__hist__012 \
  --task-id humanize__hist__015 \
  --timeout-seconds 900
```

4. Import usage for all current validation prefixes:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_usage_import.py \
  --root . \
  --result-prefix phase1_validation_humanize_holdout_smoke \
  --result-prefix phase1_validation_humanize_holdout \
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --allow-missing-price-estimate
```

5. Summarize both prefixes:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . summarize \
  --result-prefix phase1_validation_humanize_holdout_smoke

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . summarize \
  --result-prefix phase1_validation_humanize_holdout
```

Acceptance:

- `phase1_validation_humanize_holdout_score_table.csv` exists;
- combined smoke plus main Humanize holdout has at least `12` scoreable cells
  out of `16`;
- policy violation count is `0`;
- usage observed rate remains at least `0.85`, or observed-or-conservative spend
  remains below the hard cap;
- results are clearly labeled
  `internal_unseen_acut_holdout_not_future_holdout`.

Branch:

- If accepted and cumulative observed-or-conservative spend is below `USD 80`,
  continue to Step 6 or Step 7.
- If accepted but source provenance remains fallback-only, prefer Step 6
  stability over third-repo paid work.
- If accepted and source provenance has been hardened, prefer Step 7 third repo
  before Step 6 stability.
- If not accepted, skip further paid ACUT work and go to Step 9.

Commit:

```text
Run Phase 1 Humanize holdout matrix
```

## Step 6: Optional Humanize Stability Repeat

Run this only if Steps 4 and 5 are healthy and the worker needs more overnight
runtime before attempting a third repo.

This repeat is not independent validation. It tests whether the Humanize
holdout result is stable under a repeated same-protocol run.

Task IDs:

```text
humanize__hist__002
humanize__hist__003
humanize__hist__004
humanize__hist__007
humanize__hist__008
humanize__hist__010
humanize__hist__012
humanize__hist__015
```

Projected conservative cost:

```text
16 cells * USD 0.50 = USD 8.00
```

Actions:

1. Run Codex and Kilo sequentially with result prefix:

```text
phase1_validation_humanize_holdout_stability
```

Use the same `workspace_acut_run.py run-matrix` command shape as Step 5, but
include all eight task IDs above.

2. Import usage:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_usage_import.py \
  --root . \
  --result-prefix phase1_validation_humanize_holdout_smoke \
  --result-prefix phase1_validation_humanize_holdout \
  --result-prefix phase1_validation_humanize_holdout_stability \
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --allow-missing-price-estimate
```

3. Summarize the stability prefix.

Acceptance:

- at least `12` of `16` stability cells are scoreable;
- policy violation count is `0`;
- stability report says this is repeat evidence, not independent validation;
- cumulative observed-or-conservative spend remains below `USD 120`
  incremental and `USD 160` total.

Commit:

```text
Run Phase 1 Humanize holdout stability repeat
```

## Step 7: Optional Third Target Repo Pilot

Run this only if the Humanize holdout smoke and main batch passed, usage/cost is
healthy, and the worker still has substantial unattended time.

Recommended first third repo: `itsdangerous`.

Rationale:

- small Python package;
- local test surface is usually lightweight;
- listed as a previous candidate in `configs/repositories.yaml`;
- different enough from Toolz and Humanize to exercise multi-repo compiler
  behavior.

Actions:

1. Clone or update the repo under an ignored path:

```bash
mkdir -p experiments/phase0_headroom/external_repos
test -d experiments/phase0_headroom/external_repos/itsdangerous/.git || \
  git clone https://github.com/pallets/itsdangerous.git \
    experiments/phase0_headroom/external_repos/itsdangerous
git -C experiments/phase0_headroom/external_repos/itsdangerous fetch --all --tags
```

2. Create:

```text
experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous.yaml
```

Suggested config:

```yaml
schema_version: barcarolle.second_repo_pilot.v1
selected_repo_id: itsdangerous
status: selected
repo_url: https://github.com/pallets/itsdangerous.git
local_repo: experiments/phase0_headroom/external_repos/itsdangerous
test_environment:
  pythonpath_mode: src_if_present_else_repo_root
  command_template: uv run --project experiments/phase0_headroom --with "pytest>=9" --with "setuptools<81" python -m pytest -q {test_files}
preferred_task_count:
  certification_attempts: 24
  pilot_certified_min: 4
  benchmark_grade_min: 6
  paid_matrix_default_tasks: 4
  paid_matrix_optional_tasks_max: 8
acut:
  adapters_config: experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
  adapters:
    - codex_workspace
    - kilo_workspace
  result_prefix: phase1_validation_third_repo_itsdangerous
budget:
  soft_cap_usd: 20
  hard_cap_usd: 45
  stop_before_batch_projected_incremental_usd: 12
parallelism:
  paid_acut_concurrency: 1
  allow_cross_harness_paid_parallelism: false
claim_scope: third_repo_operational_pilot_not_predictive_validation
```

3. Run local-only mining and certification:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous.yaml \
  mine

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous.yaml \
  source-context

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous.yaml \
  certify

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous.yaml \
  assemble-release

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous.yaml \
  summarize
```

4. Continue to paid ACUT only if:
   - release status is `pilot_grade`;
   - at least `6` tasks are certified;
   - B/W split contains at least `3` tasks each;
   - certification report shows no systemic checkout/build/oracle blocker;
   - cumulative projected spend remains below `USD 140`.

5. Select up to `8` certified tasks, balanced across `B_real` and `W_real`.
   Run a 2-task smoke first, then a 6-task main batch if smoke passes.

Use result prefix:

```text
phase1_validation_third_repo_itsdangerous
```

Use the same `workspace_acut_run.py run-matrix` command shape as Steps 4 and 5,
with `--task-id` set to the selected `itsdangerous__hist__...` task IDs.

6. Import usage with all validation prefixes:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_usage_import.py \
  --root . \
  --result-prefix phase1_validation_humanize_holdout_smoke \
  --result-prefix phase1_validation_humanize_holdout \
  --result-prefix phase1_validation_humanize_holdout_stability \
  --result-prefix phase1_validation_third_repo_itsdangerous \
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --allow-missing-price-estimate
```

Acceptance:

- third repo certification artifacts are committed only as small sanitized
  files;
- external clone remains ignored and untracked;
- third repo score table exists if paid work ran;
- scoreable rate is at least `75%` for paid third-repo cells;
- status is `third_repo_pilot_candidate`, not validation-grade.

Stop if:

- certification fails below pilot threshold;
- test environment needs broad dependency engineering;
- source context is fallback-only and would make paid cells hard to interpret;
- projected cost exceeds the overnight caps.

Commit after local certification:

```text
Certify Phase 1 third repo pilot candidate
```

Commit after paid cells, if run:

```text
Run Phase 1 third repo validation pilot
```

## Step 8: Rebuild Phase 1 MVP Artifacts

After every accepted paid branch, rebuild the current Phase 1 MVP artifact set
so the compiler stays healthy.

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

Acceptance:

- MVP build still succeeds;
- closeout still says `predictive_validity_established=false`;
- new validation artifacts do not mutate historical MVP claims unless the tool
  was intentionally extended to import them.

Commit if generated MVP summaries changed:

```text
Refresh Phase 1 MVP compiler artifacts after validation pilot
```

## Step 9: Write The Overnight Validation Report

Actions:

1. Create:

```text
experiments/phase1_compiler/results/phase1_validation_overnight_decision.json
experiments/phase1_compiler/reports/phase1_validation_overnight_report.md
```

2. The JSON decision must include:
   - starting HEAD and final HEAD;
   - prefixes run;
   - repos covered;
   - task IDs;
   - cell counts;
   - scoreable counts;
   - terminal status counts;
   - policy violation counts;
   - cost summary;
   - usage observed rate;
   - source provenance status;
   - whether third repo certification or paid pilot ran;
   - allowed claims;
   - disallowed claims;
   - recommended next runbook.

3. The Markdown report must answer:
   - What new evidence did the night produce?
   - Did Humanize internal holdout cells run?
   - Was source provenance hardened or only audited?
   - Did a stability repeat run?
   - Did a third repo pilot run?
   - What remains before validation-grade claims?

Decision labels:

```text
phase1_operational_validation_pilot_complete
phase1_validation_candidate_needs_future_holdout
phase1_source_provenance_blocker
phase1_acut_scoreability_blocker
phase1_cost_observability_blocker
phase1_third_repo_certification_blocker
```

Use the strongest label supported by evidence. If multiple blockers exist, list
all of them but choose the blocker that stops the next paid batch as the primary
decision.

Acceptance:

- report does not claim predictive validity;
- report distinguishes internal unseen holdout from future holdout;
- report lists exact next recommended runbook;
- report includes enough detail for the main session to decide whether to scale,
  harden source adapters, or add a true future holdout.

Commit:

```text
Summarize Phase 1 overnight validation pilot
```

## Step 10: Final Verification

Actions:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
git status --short --ignored experiments/phase0_headroom experiments/phase1_compiler docs/experiments AGENTS.md .gitignore
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
- Phase 1 compiler validation passes;
- branch is clean except ignored raw/cache/workspace/external-repo files;
- raw artifacts are not tracked;
- final report and decision JSON are committed.

Do not push unless the user explicitly asked this worker to push.

## Stop Conditions

Stop paid work and write the overnight report if any condition occurs:

- `LLM_BASE_URL` or `LLM_API_KEY` is unavailable after sourcing `~/.zshrc`;
- an ACUT adapter cannot prove endpoint-backed execution;
- a solver workspace contains hidden oracle material;
- a paid batch creates policy violations;
- scoreable rate drops below `75%` for a smoke or main batch;
- usage observed rate drops below `0.85` and conservative cost no longer stays
  comfortably under cap;
- projected cumulative spend reaches `USD 140`;
- actual or observed-or-conservative cumulative spend reaches `USD 160`;
- source artifacts are inconsistent enough that new score tables would be
  misleading;
- local tests fail after a change and cannot be repaired quickly.

When stopping, do not leave a vague failure. Write:

```text
experiments/phase1_compiler/reports/phase1_validation_overnight_report.md
experiments/phase1_compiler/results/phase1_validation_overnight_decision.json
```

with the exact blocker, last successful step, cost spent, and smallest next
repair.

## Expected End States

Best likely outcome:

```text
phase1_operational_validation_pilot_complete
Humanize internal unseen ACUT holdout ran across Codex and Kilo.
Source provenance was audited, possibly hardened.
Cost and usage were recorded.
Predictive validity remains false pending true future holdout.
```

Strongest possible overnight outcome:

```text
phase1_validation_candidate_needs_future_holdout
Humanize holdout is healthy.
Source provenance has at least partial non-fallback repair.
A third repo pilot is certified and maybe has scoreable ACUT cells.
Next runbook should pre-register a true future holdout validation design.
```

Acceptable blocker outcome:

```text
phase1_<specific_layer>_blocker
No unsupported claims were made.
The blocker report identifies the failed layer and the next bounded repair.
```
