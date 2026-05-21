# Phase 0 Kilo Completion And Policy Follow-Up Runbook

Status: follow-up implementation and experiment runbook, 2026-05-21.

This runbook continues after
`docs/experiments/phase-0-codex-kilo-workspace-acut-runbook.md` completed the
Codex/Kilo workspace ACUT matrix.

Current Phase 0 decision remains:

```text
proceed_regression_benchmark
```

The matrix proved the intended workspace ACUT boundary, but it is not ready to
scale. The next step is to remove two validity blockers:

- Kilo frequently edits the workspace and then does not exit before the adapter
  timeout.
- Several tasks are rejected by benchmark-side policy, especially because
  solver-visible scope text can mention regression test files even though test
  edits are prohibited.

This runbook is deliberately smaller than another overnight run. It should
produce either a repaired small matrix or a precise blocker report.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-0-kilo-completion-policy-followup-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make cohesive commits after completing one or more related steps.

The previous Codex/Kilo workspace ACUT matrix completed, but only 9/20 cells
were scoreable. Kilo had 6 acut_harness_error rows caused by non-interactive
completion/exit behavior, and 5 total cells were rejected by benchmark policy.

Your goal is not to implement an ACUT agent harness inside Barcarolle. Keep the
ACUT boundary intact: Barcarolle prepares workspaces, invokes configured CLI
harnesses, captures git diff, enforces policy, and verifies in fresh verifier
workspaces.

All paid LLM and ACUT calls must use LLM_BASE_URL + LLM_API_KEY. If either is
missing, source ~/.zshrc and check again. Do not use local Codex/ChatGPT
subscription auth, OPENAI_API_KEY, OpenRouter variables, or provider-specific
keys unless the user's shell maps them into LLM_API_KEY.

First diagnose existing raw artifacts without paid calls. Then fix statement
policy rendering. Then run only bounded Kilo completion probes and a small
policy smoke. Run a repaired full matrix only if the explicit continuation
conditions in this runbook are satisfied.
```

## Relation To The Original Phase 0 Plan

The original Phase 0 objective is still to establish whether Barcarolle can
compile target-repository benchmark tasks and evaluate realistic ACUTs under a
clean solver/verifier boundary.

This follow-up does not change that objective. It repairs the current Phase 0
execution protocol so that a future scale-up is not dominated by wrapper
timeouts or self-inflicted policy violations. If the follow-up succeeds, return
to the remaining Phase 0 work through a repaired Codex/Kilo workspace matrix.
If it fails, Phase 0 should stay in regression-benchmark mode with a specific
Kilo or statement-policy blocker.

## Budget Rules

Incremental cap for this follow-up:

- soft cap: `USD 8`;
- hard cap: `USD 20`;
- do not run parallel paid ACUT task-solving calls;
- do not run a repaired 20-cell matrix unless the continuation conditions in
  Step 5 pass;
- if usage is still not exported by the harnesses, continue using conservative
  `USD 0.50` per paid ACUT cell and record latency for every cell;
- stop before any batch whose projected incremental spend exceeds `USD 8`.

Most early steps are local diagnosis or tests and should not make paid calls.

## Output Layout

Add new follow-up artifacts instead of overwriting the completed Codex/Kilo
matrix:

```text
experiments/phase0_headroom/
  configs/
    codex_kilo_workspace_followup_matrix.yaml
  results/
    kilo_completion_policy_diagnosis.json
    kilo_completion_probe_results.jsonl
    codex_kilo_workspace_followup_submissions.jsonl
    codex_kilo_workspace_followup_verifier_results.jsonl
    codex_kilo_workspace_followup_score_table.csv
    codex_kilo_workspace_followup_matrix.json
    codex_kilo_workspace_followup_metrics.json
    codex_kilo_workspace_followup_cost_ledger.jsonl
    codex_kilo_workspace_followup_cost_summary.json
  reports/
    kilo_completion_policy_diagnosis.md
    codex_kilo_workspace_followup_process.md
    codex_kilo_workspace_followup_analysis.md
    phase0_decision_memo.md
```

Raw logs and workspaces must remain ignored:

```text
experiments/phase0_headroom/results/raw/workspace_acut/
experiments/phase0_headroom/workspaces/workspace_acut/
```

## Step 0: Preflight

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`,
   `codex --version`, and `kilo --version`.
2. Verify endpoint variables without using them yet:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

3. Confirm the current completed matrix artifacts exist:

```text
experiments/phase0_headroom/results/codex_kilo_workspace_score_table.csv
experiments/phase0_headroom/results/codex_kilo_workspace_verifier_results.jsonl
experiments/phase0_headroom/results/codex_kilo_workspace_cost_summary.json
experiments/phase0_headroom/reports/codex_kilo_workspace_analysis.md
experiments/phase0_headroom/reports/phase0_decision_memo.md
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
- existing tests pass;
- current tracked worktree state is understood;
- only ignored raw logs, workspaces, caches, or virtualenvs appear as ignored
  untracked artifacts.

Stop if:

- endpoint variables are missing after sourcing `~/.zshrc`;
- Phase 0 workspace adapter tests fail;
- the completed Codex/Kilo matrix artifacts are missing.

## Step 1: Diagnose Existing Kilo And Policy Failures

This step must not make paid LLM calls.

Actions:

1. Parse:

```text
experiments/phase0_headroom/results/codex_kilo_workspace_score_table.csv
experiments/phase0_headroom/results/codex_kilo_workspace_submissions.jsonl
experiments/phase0_headroom/results/codex_kilo_workspace_verifier_results.jsonl
experiments/phase0_headroom/results/codex_kilo_workspace_cost_ledger.jsonl
```

2. For each Kilo `acut_harness_error` row, inspect only ignored raw logs and
   generated workspaces. Record sanitized facts:
   - task id and split;
   - adapter timeout or non-timeout exit code;
   - whether `submission.patch` is non-empty;
   - changed paths from the solver workspace if available;
   - last 10 JSON event `type` values from Kilo stdout;
   - whether events include `suggestion.shown`, `session.idle`, or an obvious
     final-response event;
   - elapsed seconds from the cost ledger.
3. For every `policy_violation`, record:
   - task id and split;
   - harness;
   - `harness_error`;
   - rejected paths;
   - whether the solver-visible statement mentioned rejected test paths or
     other non-editable paths.
4. Write:

```text
experiments/phase0_headroom/results/kilo_completion_policy_diagnosis.json
experiments/phase0_headroom/reports/kilo_completion_policy_diagnosis.md
```

Acceptance:

- the report distinguishes endpoint failure, adapter timeout, empty diff,
  non-empty diff plus non-exit, and policy rejection;
- no raw prompts, full transcripts, raw completions, or raw patches are
  committed;
- the report identifies whether current solver-visible statements can mention
  test files while policy rejects test edits.

Commit:

```text
Diagnose Kilo completion and policy failures
```

## Step 2: Repair Solver-Visible Statement Policy

This step fixes Barcarolle's benchmark-side statement rendering. It must not
relax hidden verifier isolation and must not allow test edits.

Current issue to check:

```text
click__rbench__002 and click__rbench__003 can expose tests/test_*.py as
"regression coverage" inside Scope Boundary, while policy_violation rejects
any tests/** edit.
```

Actions:

1. Update the workspace statement renderer so solver-visible statements have
   explicit edit policy:

```text
## Editable Paths
<implementation files only, from allowed_code_paths or prompt_code_files>

## Non-Editable Paths
Do not edit tests, hidden verifier files, generated caches, lockfiles, or files
outside the listed editable paths.
```

2. When task metadata contains expected touched areas that mention tests or
   regression coverage, do not list those test paths as editable scope. Either
   omit them from the solver-visible `Scope Boundary` or move them into a
   clearly non-editable verifier-only note.
3. Preserve the current policy gate:
   - any `tests/**` edit is still `submission_edited_tests`;
   - any path outside `allowed_code_paths` is still
     `submission_edited_out_of_scope_paths`.
4. Add or update tests proving:
   - Click generic task statements list `click/testing.py`, `click/core.py`, or
     `click/termui.py` as editable implementation paths as appropriate;
   - generated statements do not present `tests/test_testing.py` or
     `tests/test_termui.py` as editable;
   - policy still rejects a test edit;
   - existing Toolz task statements still render useful scope boundaries.
5. Run:

```bash
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
git diff --check
```

Acceptance:

- policy text and policy enforcement agree;
- no hidden verifier material becomes solver-visible;
- tests pass.

Commit:

```text
Clarify workspace ACUT editable path policy
```

## Step 3: Run Bounded Kilo Completion Probes

This step may make paid ACUT calls, but only bounded diagnostic calls.

Preferred repair:

- keep using `kilo run --auto`;
- keep the same endpoint model and provider configuration;
- make the wrapper prompt stricter about finalizing and exiting;
- do not implement a replacement agent loop inside Barcarolle.

Allowed wrapper changes:

1. Add a Kilo completion prompt mode, for example:

```text
--completion-mode current
--completion-mode strict-final
```

2. `strict-final` should tell Kilo:
   - make the required code edits in the workspace;
   - do not edit tests or files outside editable paths;
   - do not ask follow-up questions;
   - do not show suggestions after editing;
   - after edits are complete, provide one brief final answer and terminate.
3. Keep isolated Kilo config and `LLM_BASE_URL + LLM_API_KEY` use unchanged.
4. Add wrapper unit tests or command-construction tests for the new mode.

Run probes sequentially with a short diagnostic timeout, such as `300` seconds.
Use the previous 20-cell matrix as the baseline for the current prompt; do not
spend money re-running the current prompt unless the diagnosis makes that
necessary.

Probe set:

```text
kilo_workspace strict-final x toolz__hist__002
kilo_workspace strict-final x toolz__hist__001
kilo_workspace strict-final x click__rbench__004
```

These are known Kilo timeout cases from the completed matrix. Use a new result
prefix such as:

```text
kilo_completion_probe
```

Write:

```text
experiments/phase0_headroom/results/kilo_completion_probe_results.jsonl
experiments/phase0_headroom/reports/codex_kilo_workspace_followup_process.md
```

Acceptance:

- at least `2/3` known-timeout Kilo probes terminate without adapter timeout;
- every non-timeout probe has a captured `git diff` or a classified no-diff
  result;
- no probe exposes hidden verifier material to the solver workspace;
- cost rows are recorded or conservatively estimated;
- if the strict prompt does not improve timeout behavior, stop and write a
  Kilo completion blocker report.

Optional fallback only if `strict-final` fails:

- Implement an experimental `event-idle-capture` mode only as a diagnostic
  adapter mode, not as the default scoreable protocol.
- It may terminate the child process only when:
  - Kilo JSON events show a clear idle or final state;
  - no tool call is active;
  - the workspace diff is non-empty and stable for at least 30 seconds;
  - the raw event stream is preserved under ignored paths;
  - the terminal status is labeled separately, for example
    `adapter_idle_capture`, until validated.
- Do not count `event-idle-capture` as scoreable evidence until a later smoke
  proves it agrees with normal verifier outcomes.

Commit:

```text
Probe Kilo completion behavior
```

or:

```text
Document Kilo completion blocker
```

## Step 4: Run A Small Policy Smoke

Run this step only if Step 2 passes and Step 3 does not stop with a blocker.

Purpose:

- verify that repaired statements reduce test-edit and out-of-scope policy
  violations;
- verify Kilo can produce terminal outcomes on more than one real task;
- keep cost small before another full matrix.

Smoke cells:

```text
codex_workspace x click__rbench__002
codex_workspace x click__rbench__003
codex_workspace x toolz__hist__010
kilo_workspace  x click__rbench__002
kilo_workspace  x click__rbench__003
kilo_workspace  x toolz__hist__010
```

Use a new result prefix:

```text
codex_kilo_workspace_followup_smoke
```

Actions:

1. Run cells sequentially.
2. Keep the same endpoint model `gpt-5.4-mini` for both harnesses.
3. Record submissions, verifier rows, cost rows, changed paths, and terminal
   statuses.
4. Verify solver workspaces contain no tracked hidden verifier material.
5. Compare policy violation counts against the previous matrix.

Acceptance:

- all 6 cells have terminal status;
- test-edit policy violations on the two Click tasks are `0/4`;
- Kilo has at least `2/3` non-timeout terminal outcomes;
- no hidden verifier material appears in solver workspaces;
- projected follow-up full matrix cost remains within the hard cap.

Stop if:

- any Click task still exposes test files as editable scope;
- policy violations remain dominated by test edits;
- Kilo still times out on most smoke cells;
- cost cannot be observed or conservatively bounded.

Commit:

```text
Run Codex Kilo follow-up policy smoke
```

or:

```text
Document Codex Kilo follow-up smoke blocker
```

## Step 5: Continue Or Stop Conditions

Continue to a repaired 20-cell matrix only if all conditions hold:

- Step 2 statement-policy tests pass;
- Step 3 Kilo completion probes have at least `2/3` non-timeout outcomes;
- Step 4 policy smoke has `0` test-edit violations on Click tasks;
- Step 4 Kilo smoke has at least `2/3` non-timeout terminal outcomes;
- no hidden verifier material is exposed to solver workspaces;
- projected incremental cost for the repaired matrix is at or below `USD 10`.

If any condition fails, stop and update:

```text
experiments/phase0_headroom/reports/codex_kilo_workspace_followup_analysis.md
experiments/phase0_headroom/reports/phase0_decision_memo.md
```

Use decision:

```text
proceed_regression_benchmark
```

and name the concrete blocker.

## Step 6: Repaired 20-Cell Matrix

Run only if Step 5 allows continuing.

Use the same task set as the completed matrix:

```text
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

Run:

```text
codex_workspace x 10 tasks
kilo_workspace  x 10 tasks
```

Use result prefix:

```text
codex_kilo_workspace_followup
```

Acceptance:

- every scheduled cell has terminal status;
- total scoreable cells are at least `12/20`;
- each harness has at least `5/10` scoreable cells;
- `G_mini` has at least `4/8` scoreable cells;
- policy violations are not dominated by test edits;
- Kilo timeout rows are below `3/10`;
- MAE, RMSE, Brier, and ordering accuracy remain
  `not_applicable_underpowered` unless a later analysis explicitly justifies
  them.

Interpretation:

- If the thresholds pass, Phase 0 can continue as a stronger
  regression-benchmark compiler and can refresh Phase 1 draft artifacts.
- If the thresholds fail, Phase 0 remains a useful workspace ACUT prototype but
  should not scale or claim predictive validity.

Commit:

```text
Run repaired Codex Kilo workspace matrix
```

## Step 7: Optional Phase 1 Refresh

Run only if Step 6 completes and the repaired matrix has enough compatible
evidence to avoid silently importing harness errors as scores.

Actions:

1. Import the repaired Codex/Kilo score rows into the Phase 1 compiler
   skeleton.
2. Regenerate:

```text
experiments/phase1_compiler/results/toolz_phase1_draft_release.json
experiments/phase1_compiler/results/toolz_phase1_weighted_score.json
```

3. Preserve `insufficient_evidence` for empty or incompatible strata.
4. Run:

```bash
uv run --project experiments/phase1_compiler pytest -q
```

Acceptance:

- Phase 1 artifacts identify the Codex/Kilo ACUT source rows;
- incompatible cells are not counted as passing or failing evidence;
- no predictive-validity claim is introduced.

Commit:

```text
Refresh Phase 1 artifacts from follow-up matrix
```

## Step 8: Final Hygiene

Actions:

1. Run:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
test ! -d experiments/phase1_compiler || uv run --project experiments/phase1_compiler pytest -q
git status --short --ignored experiments/phase0_headroom experiments/phase1_compiler docs/experiments AGENTS.md .gitignore
```

2. Confirm no raw prompts, full completions, ACUT transcripts, solver
   workspaces, verifier workspaces, cloned repositories, `.venv`, caches, or
   full logs are staged.
3. Update:

```text
experiments/phase0_headroom/reports/codex_kilo_workspace_followup_analysis.md
experiments/phase0_headroom/reports/phase0_decision_memo.md
```

4. The final analysis must state:
   - whether Kilo completion was repaired;
   - whether statement-policy rendering was repaired;
   - whether the repaired smoke or matrix is scoreable enough to scale;
   - whether Phase 1 artifacts were refreshed;
   - the next smallest useful experiment.

Final commit:

```text
Summarize Kilo completion and policy follow-up
```

Do not push unless the user explicitly asks.

## Success Criteria

Best case:

- solver-visible statements no longer invite test edits;
- Kilo strict completion mode exits on known timeout tasks;
- follow-up smoke has no Click test-edit policy violations;
- repaired 20-cell matrix reaches at least `12/20` scoreable cells;
- Phase 1 artifacts can be refreshed without overclaiming.

Good fallback:

- statement-policy rendering is repaired and tested;
- Kilo remains blocked by CLI completion behavior;
- no additional large paid matrix is run;
- reports name the exact Kilo blocker and preserve current
  `proceed_regression_benchmark` decision.

Unacceptable outcomes:

- using local Codex/ChatGPT subscription auth as scoreable evidence;
- reverting to one-shot diff generation as the scoreable protocol;
- exposing hidden verifier material in solver workspaces;
- relaxing benchmark policy to allow tests edits merely to improve scoreability;
- treating event-idle capture as scoreable without a separate validation gate;
- claiming predictive validity from underpowered or harness-dominated cells.
