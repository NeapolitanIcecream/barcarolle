# Phase 0 Workspace ACUT Adapter Runbook

Status: implementation runbook, 2026-05-21.

This runbook replaces the scoreable use of one-shot diff generation in Phase 0.
Its job is to implement a thin workspace adapter, then rerun the Phase 0 matrix
so Barcarolle evaluates an ACUT harness rather than pretending to be one.

## Current Problem

The measured endpoint Matrix A repaired `G_mini` scoreability but failed at the
ACUT output boundary:

- `10` task-solving cells;
- `2` scoreable cells;
- `8` `invalid_output` or harness-error cells;
- all `4` `G_mini` matrix cells failed before verification because the
  generated patch did not apply.

The immediate cause was corrupt unified diff text from a one-shot chat prompt.
That is not a useful Barcarolle research signal. The next run must let the ACUT
harness edit a real workspace, then let Barcarolle capture `git diff`.

## Core Constraint

Barcarolle must not implement the ACUT agent harness.

Barcarolle owns:

- task package assembly;
- clean solver workspace creation;
- solver-visible statement and context boundary;
- ACUT harness invocation;
- final `git diff --binary` capture;
- changed-path and policy checks;
- fresh verifier workspace replay;
- hidden oracle injection and verification;
- score, cost, latency, and sanitized report artifacts.

The ACUT harness owns:

- file search and reading;
- file editing;
- multi-turn reasoning;
- optional public-test execution;
- retry behavior;
- model calls;
- tool-use internals and traces.

If no endpoint-backed ACUT harness can be configured, implement the adapter and
tests, then stop before paid task-solving calls. Do not fall back to the old
diff-only prompt path except as a clearly labeled non-scoreable baseline.

## Handoff Prompt

Use this prompt to start the implementation session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-0-workspace-acut-adapter-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.

Implement a thin Phase 0 workspace ACUT adapter. Barcarolle must provide a clean
solver workspace and invoke a configured ACUT harness; it must not implement the
ACUT agent loop itself. The ACUT harness is responsible for reading, editing,
testing, retrying, and using tools. Barcarolle captures the final git diff and
verifies it in a fresh workspace with hidden oracle material.

All paid LLM and ACUT calls must use LLM_BASE_URL + LLM_API_KEY. If either is
missing, source ~/.zshrc and check again. Do not use local Codex/ChatGPT
subscription auth. Do not use OPENAI_API_KEY, OpenRouter variables, or
provider-specific variables unless the user's shell maps them into LLM_API_KEY.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts,
workspaces, cloned repositories, .venv, caches, or full raw run outputs.

Implement the adapter and tests first. Then rerun Phase 0 through the workspace
adapter only if an endpoint-backed ACUT harness command is configured and passes
preflight. End with a committed report that states the matrix outcome, cost,
scoreable-cell count, and whether Phase 0 can move beyond
proceed_regression_benchmark.
```

## Required ACUT Harness Contract

The adapter is command-template based. The real ACUT harness is supplied by
configuration, not hard-coded in Barcarolle.

Create:

```text
experiments/phase0_headroom/configs/acut_workspace_adapter.yaml
```

Minimum schema:

```yaml
schema_version: barcarolle.acut_workspace_adapter_config.v1
adapter_id: endpoint_workspace_acut
acut_id: ""
model_or_agent_name: ""
command_template: ""
timeout_seconds: 900
requires_env:
  - LLM_BASE_URL
  - LLM_API_KEY
workspace_arg_style: template
statement_delivery: file
usage_observation:
  mode: harness_report_optional
  report_path: null
allowed_network: acut_harness_defined
raw_log_policy: ignored_path_only
```

`command_template` may use these placeholders:

```text
{workspace}
{statement_file}
{task_id}
{run_id}
{raw_dir}
{timeout_seconds}
```

Example shape, not a committed default:

```text
<acut command> --workspace {workspace} --task-file {statement_file} --run-id {run_id}
```

The command must mutate files inside `{workspace}`. It may write its own raw logs
under `{raw_dir}`. It should exit non-zero only for harness/runtime failure; a
legitimate failed solution should still leave a workspace diff and allow
Barcarolle verification to classify it as `verified_fail`.

## Budget Rules

Use the measured endpoint budget discipline:

- hard cap for this rerun: `USD 25` estimated or observed incremental spend;
- stop before any batch whose projected incremental spend exceeds `USD 15`;
- stop if the ACUT harness cannot report or conservatively bound cost;
- do not run parallel paid ACUT batches;
- record projected and observed cost rows around every paid batch.

If usage reporting is unavailable but the ACUT harness is confirmed to use
`LLM_BASE_URL + LLM_API_KEY`, run only the smoke subset and stop unless the user
has explicitly approved conservative scale-up.

## Output Layout

Add or update these files:

```text
experiments/phase0_headroom/
  configs/
    acut_workspace_adapter.yaml
    workspace_acut_matrix.yaml
  tools/
    workspace_acut_run.py
    test_workspace_acut_run.py
  results/
    workspace_acut_submissions.jsonl
    workspace_acut_verifier_results.jsonl
    workspace_acut_score_table.csv
    workspace_acut_matrix.json
    workspace_acut_metrics.json
    workspace_acut_cost_ledger.jsonl
    workspace_acut_cost_summary.json
    workspace_acut_preflight.json
  reports/
    workspace_acut_preflight.md
    workspace_acut_process.md
    workspace_acut_analysis.md
    phase0_decision_memo.md
```

Raw ACUT logs and solver/verifier workspaces must be ignored under:

```text
experiments/phase0_headroom/results/raw/workspace_acut/
experiments/phase0_headroom/workspaces/workspace_acut/
```

## Step 0: Preflight

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, and current
   working-tree status.
2. Confirm `AGENTS.md` and this runbook are present.
3. Confirm the current Phase 0 evidence exists:
   - `reports/overnight_research_report.md`
   - `results/generic_comparator_protocol.json`
   - `results/headroom_matrix.json`
   - `reports/phase0_decision_memo.md`
4. Source shell config if needed and confirm:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

5. Run:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
test ! -d experiments/phase1_compiler || uv run --project experiments/phase1_compiler pytest -q
```

Acceptance:

- tests pass;
- tracked worktree is understood;
- endpoint variables are available;
- no raw artifacts are tracked.

Stop if:

- endpoint variables are absent;
- there are unexplained local edits touching Phase 0 results;
- generic comparator protocol has regressed below `3` same-protocol tasks.

## Step 1: Implement The Adapter Contract

Actions:

1. Create `configs/acut_workspace_adapter.yaml`.
2. Implement `tools/workspace_acut_run.py` with subcommands or flags for:
   - `preflight`
   - `smoke`
   - `run-matrix`
   - `summarize`
3. The implementation must:
   - load certified `toolz` task packages;
   - load active `G_mini` comparator packages;
   - create a solver workspace at the base commit;
   - write a solver-visible statement file outside hidden/private material;
   - invoke the configured ACUT command template;
   - capture `git diff --binary` from the solver workspace;
   - classify empty diff as `invalid_output`;
   - classify ACUT command failure separately as `acut_harness_error`;
   - check changed paths before verification;
   - create a fresh verifier workspace;
   - apply the captured patch to the verifier workspace;
   - inject the hidden oracle only in the verifier workspace;
   - run the verifier;
   - write sanitized JSONL/CSV summaries.
4. Add tests with fake ACUT harness commands that:
   - modify an allowed code file and produce a captured patch;
   - produce no diff;
   - edit a prohibited test file;
   - exit non-zero;
   - produce a diff that applies in the verifier workspace;
   - preserve hidden material outside the solver workspace.

Acceptance:

- all adapter tests pass;
- fake ACUT tests prove Barcarolle is not relying on model-emitted diff text;
- solver workspace contains no hidden verifier files;
- verifier uses a fresh checkout, not the mutated solver workspace.

Commit:

```text
Add Phase 0 workspace ACUT adapter
```

## Step 2: ACUT Harness Preflight

Actions:

1. Resolve the real ACUT command from `configs/acut_workspace_adapter.yaml` or
   a documented environment variable such as `ACUT_WORKSPACE_COMMAND`.
2. Confirm the command exists and can run a no-op workspace smoke without a paid
   model call if supported.
3. Confirm the command receives `LLM_BASE_URL` and `LLM_API_KEY`.
4. Confirm the command is not using local Codex/ChatGPT subscription auth unless
   the user has explicitly changed the endpoint rule.
5. Write:
   - `results/workspace_acut_preflight.json`
   - `reports/workspace_acut_preflight.md`

Acceptance:

- ACUT command is configured;
- endpoint path is explicit;
- a dry no-op command path works or a precise blocker is recorded;
- the report states whether cost usage will be observed directly, imported from
  ACUT metadata, or conservatively estimated.

Stop if:

- no ACUT harness command is configured;
- the worker cannot prove endpoint-backed execution;
- the ACUT requires secrets beyond `LLM_BASE_URL + LLM_API_KEY` that are not
  explicitly approved;
- the only runnable option is the old diff-only prompt.

If stopped here, commit:

```text
Document workspace ACUT harness preflight blocker
```

## Step 3: Build The Phase 0 Workspace Matrix

Actions:

1. Write `configs/workspace_acut_matrix.yaml`.
2. Include the current Phase 0 tasks:
   - `B_real`: `toolz__hist__001`, `toolz__hist__002`,
     `toolz__hist__003`;
   - `W_real`: `toolz__hist__004`, `toolz__hist__010`,
     `toolz__hist__016`;
   - `G_mini`: `click__rbench__001`, `click__rbench__002`,
     `click__rbench__003`, `click__rbench__004`.
3. Mark the old measured diff-only Matrix A as historical baseline.
4. Project cost for:
   - smoke subset;
   - full 10-cell matrix;
   - optional rerun or second ACUT, disabled by default.

Acceptance:

- the matrix has `10` scheduled cells;
- every scheduled task has a base checkout and verifier;
- no `G_mini` task is included unless `same_protocol_scoreable`;
- projected cost stays below the hard cap.

Commit if only config/report files changed:

```text
Configure Phase 0 workspace ACUT matrix
```

## Step 4: Run A No-Paid Or Minimal-Paid Smoke

Actions:

1. Run fake-harness tests first.
2. If the real ACUT supports no-paid dry-run mode, run one no-paid smoke cell.
3. Otherwise run a paid smoke subset of `2` to `4` cells:
   - at least one `toolz` task;
   - at least one `G_mini` task;
   - prefer cells that failed as corrupt patch in Matrix A.
4. Record projected cost before the batch.
5. Record terminal status after each cell.

Acceptance:

- every smoke cell reaches a terminal status;
- captured patch source is `git_diff_after_workspace_run`;
- no corrupt-patch class appears unless Git-generated diff replay somehow fails;
- hidden verifier material is absent from solver workspace;
- changed-path policy is enforced.

Stop before full matrix if:

- fewer than half of smoke cells are scoreable;
- any solver workspace contains hidden oracle material;
- ACUT edits prohibited tests in more than one smoke cell;
- ACUT harness fails before modifying the workspace for more than one cell;
- usage/cost cannot be observed or bounded.

Commit:

```text
Run workspace ACUT smoke matrix
```

or:

```text
Document workspace ACUT smoke blocker
```

## Step 5: Run The Full Phase 0 Workspace Matrix

Take this step only if Step 4 passes.

Actions:

1. Run the `10`-cell matrix, reusing smoke cells only if the run protocol is
   identical and the artifacts are complete.
2. Run cells sequentially; do not run parallel paid ACUT calls.
3. After each cell:
   - capture patch with `git diff --binary`;
   - write submission row;
   - run policy checks;
   - verify in a fresh workspace;
   - append cost and status rows.
4. Separate terminal statuses:
   - `verified_pass`
   - `verified_fail`
   - `invalid_output`
   - `acut_harness_error`
   - `policy_violation`
   - `harness_error`
   - `timeout`

Acceptance:

- every scheduled cell has terminal status;
- corrupt model patch is no longer a terminal category for scoreable cells;
- scoreable-cell count is high enough to judge whether `G_mini -> W_real` is
  available;
- failures caused by the ACUT are separated from Barcarolle harness failures.

Stop if:

- projected incremental spend would exceed `USD 15`;
- hidden verifier setup regresses;
- verifier replay fails for Git-captured patches because of Barcarolle-side
  workspace bugs.

Commit:

```text
Run Phase 0 workspace ACUT matrix
```

## Step 6: Analyze Phase 0

Actions:

1. Write:
   - `results/workspace_acut_score_table.csv`
   - `results/workspace_acut_matrix.json`
   - `results/workspace_acut_metrics.json`
   - `reports/workspace_acut_analysis.md`
2. Compute:
   - total cells;
   - scoreable cells;
   - pass/fail counts;
   - invalid/policy/harness counts;
   - `B_real`, `W_real`, and `G_mini` split summaries;
   - cost per submitted cell;
   - cost per scoreable cell;
   - median latency;
   - whether `G_mini -> W_real` is available;
   - whether `G_mini + B_real -> W_real` is available.
3. Keep MAE/RMSE/Brier marked `not_applicable_underpowered` unless the sample
   size and predictor setup truly justify them.

Acceptance:

- the report can be read without raw logs;
- it clearly compares workspace-adapter results to the old diff-only Matrix A;
- it states whether the prior invalid-output blocker is resolved.

## Step 7: Update The Canonical Phase 0 Decision

Update:

```text
experiments/phase0_headroom/reports/phase0_decision_memo.md
```

Allowed decisions remain:

- `proceed_predictive`;
- `proceed_tuning_feedback`;
- `proceed_regression_benchmark`;
- `repair_source_adapter`;
- `stop`.

Decision guidance:

- Use `proceed_predictive` only if same-protocol `G_mini`, `B_real`, and
  `W_real` have enough scoreable cells to support a real comparison.
- Use `proceed_regression_benchmark` if task packaging and workspace execution
  work but predictive evidence remains underpowered.
- Use `proceed_tuning_feedback` if workspace execution is useful mainly as an
  optimizer feedback substrate.
- Use `stop` if the adapter shows the current release cannot be evaluated
  without unacceptable harness ambiguity.

Acceptance:

- the memo names the workspace adapter as the active scoreable ACUT protocol;
- old diff-only Matrix A is described as historical diagnostic evidence;
- next smallest experiment is concrete.

Commit:

```text
Update Phase 0 decision after workspace ACUT run
```

## Step 8: Optional Phase 1 Refresh

Run only if the full matrix completed.

Actions:

1. Import workspace-adapter score rows into the Phase 1 compiler skeleton.
2. Regenerate:
   - `experiments/phase1_compiler/results/toolz_phase1_draft_release.json`
   - `experiments/phase1_compiler/results/toolz_phase1_weighted_score.json`
3. Keep `insufficient_evidence` labels where strata have no compatible cells.
4. Run:

```bash
uv run --project experiments/phase1_compiler pytest -q
```

Acceptance:

- Phase 1 artifacts reflect the workspace-adapter run, not the old diff-only
  Matrix A;
- the compiler still refuses to fabricate weighted scores for empty strata.

Commit:

```text
Refresh Phase 1 compiler artifacts from workspace ACUT run
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

2. Confirm no raw prompts, completions, ACUT transcripts, solver workspaces,
   verifier workspaces, cloned repos, `.venv`, caches, or full logs are staged.
3. Write or update:

```text
experiments/phase0_headroom/reports/workspace_acut_process.md
```

4. Ensure there is a final commit if Step 9 changed reports.

Final commit:

```text
Summarize Phase 0 workspace ACUT adapter rerun
```

Do not push unless the user explicitly asks.

## Success Criteria

Best case:

- workspace adapter implemented and tested;
- endpoint-backed ACUT harness preflight passes;
- 10-cell Phase 0 matrix completes;
- scoreable-cell count is materially higher than old Matrix A;
- `G_mini` cells are scoreable;
- Phase 0 decision memo is updated.

Good fallback:

- adapter implemented and tested;
- ACUT harness preflight blocker is precise;
- no paid calls are made through the wrong endpoint;
- runbook leaves the exact command/config missing for the next worker.

Unacceptable outcomes:

- returning to one-shot diff-only prompt as the scoreable protocol;
- using local Codex/ChatGPT subscription auth for ACUT task-solving;
- exposing hidden verifier material in the solver workspace;
- committing raw ACUT transcripts, workspaces, or secrets;
- claiming predictive validity from underpowered or harness-dominated cells.
