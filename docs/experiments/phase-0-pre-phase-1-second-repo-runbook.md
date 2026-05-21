# Phase 0 Pre-Phase 1 Second-Repo Pilot Runbook

Status: handoff runbook, 2026-05-21.

This runbook is for one dedicated Codex CLI session. Its job is to do the last
bounded Phase 0 work before starting Phase 1 MVP implementation:

1. add one small second-target-repository pilot;
2. keep the existing workspace ACUT protocol unchanged;
3. collect cost, scoreability, policy, and certification evidence;
4. write a Phase 1 readiness gate that says exactly what Phase 1 may and may
   not claim.

This runbook does not try to satisfy the full Phase 1 validation target. The
restart proposal's Phase 1 target is still larger: multiple repos, 20-50 eval
tasks per repo, at least two task sources, split generation, weighted scoring,
and uncertainty. This runbook only decides whether the project is ready to
start implementing that Phase 1 MVP from evidence that is no longer single-repo
only.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-0-pre-phase-1-second-repo-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make cohesive commits after completing one or more related steps.

Current Phase 0 decision is proceed_regression_benchmark. The Toolz workspace
ACUT protocol is operationally healthy enough for bounded follow-up work:
Codex/Kilo repaired matrix reached 19/20 scoreable cells, the stability repeat
reached 18/20 scoreable cells, Kilo strict-final no longer times out on the
current matrix, Click test-edit policy violations are gone, and observed-token
cost accounting is available.

Your task is not to rerun Toolz. Add a small second-repository pilot, preferably
humanize unless its entry gate fails. Certify a small set of second-repo
historical tasks, run the existing Codex/Kilo workspace ACUT protocol on a
bounded second-repo matrix, import observed usage, and write a Phase 1 readiness
gate.

All paid LLM and ACUT calls must use LLM_BASE_URL + LLM_API_KEY. If either is
missing, source ~/.zshrc and check again. Do not use local Codex/ChatGPT
subscription auth, OPENAI_API_KEY, OpenRouter variables, or provider-specific
keys unless the user's shell maps them into LLM_API_KEY.

Keep the ACUT boundary intact. Barcarolle prepares clean solver workspaces,
passes solver-visible statements and allowed context, invokes configured CLI
harnesses, captures git diff, applies benchmark-side policy, replays in a fresh
verifier workspace, injects hidden oracle material only there, and records
sanitized artifacts. Do not implement Codex, Kilo, or any other agent harness
inside Barcarolle.

Do not commit secrets, full prompts, raw completions, raw ACUT transcripts,
solver workspaces, verifier workspaces, cloned external repositories, .venv,
caches, or large logs. Commit only small sanitized manifests, summaries,
reports, and digests.
```

## Research Alignment

The restart proposal defines Barcarolle as a target-repository benchmark
compiler. The main Phase 0 gap is not another Toolz repeat. The gap is that the
current evidence is one primary target repository, a small recovered Click
generic comparator, and a clustered task sample.

This runbook should improve that situation without overclaiming:

- add a second target repository to test whether the certification and workspace
  ACUT boundary generalize beyond Toolz;
- preserve the same endpoint model and the same Codex/Kilo harness identities
  used in the repaired matrix;
- keep paid ACUT solving sequential;
- report `insufficient_evidence` wherever the original Phase 1 predictive
  target is not met.

Do not revive old agent-license, G0-G5 authorization, admission, public
leaderboard, or ranking-reversal narratives. License can remain future
productization only.

## Entry State

The worker should start from a branch that already contains:

```text
experiments/phase0_headroom/reports/phase0_decision_memo.md
experiments/phase0_headroom/reports/codex_kilo_workspace_stability_analysis.md
experiments/phase0_headroom/reports/workspace_cost_usage_report.md
experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
experiments/phase0_headroom/configs/model_pricing.yaml
experiments/phase0_headroom/configs/parallelism_policy.yaml
experiments/phase0_headroom/results/workspace_usage_ledger.jsonl
experiments/phase1_compiler/reports/compiler_skeleton_report.md
experiments/phase1_compiler/results/toolz_phase1_weighted_score.json
```

Expected current decision:

```text
proceed_regression_benchmark
```

Expected non-claim:

```text
predictive validity is not established
```

## Budget Rules

No new paid ACUT task-solving call is allowed before Steps 0 through 5 pass.

Incremental caps for this runbook:

- soft cap: `USD 20` observed-or-estimated;
- hard cap: `USD 45` observed-or-estimated;
- stop before any paid batch whose projected incremental spend exceeds
  `USD 12`;
- paid ACUT concurrency remains `1`;
- do not run Codex and Kilo in parallel against the same endpoint;
- local checkout, mining, certification, and verifier work may run in parallel
  only when workspaces and result writes are isolated.

Cost calculation order:

1. Use provider-billed dollars if the endpoint exposes them.
2. Otherwise import observed harness token usage with
   `experiments/phase0_headroom/tools/workspace_usage_import.py`.
3. If usage is missing, use the existing conservative per-cell fallback and do
   not scale beyond the current batch.

Default paid scale:

- smoke: `2` second-repo tasks x `2` harnesses = `4` cells;
- matrix: `4` second-repo tasks x `2` harnesses = `8` cells;
- optional extension: at most `6` second-repo tasks x `2` harnesses = `12`
  cells, only if usage is observed, smoke is healthy, and the projected
  incremental spend stays below the soft cap.

Do not run more than `16` paid second-repo cells in this runbook.

## Output Layout

Add or update only small committed artifacts:

```text
docs/experiments/
  phase-0-pre-phase-1-second-repo-runbook.md

experiments/phase0_headroom/
  configs/
    second_repo_pilot.yaml
    pre_phase1_gate.yaml
  candidate_sources/
    <repo_id>_history_anchors.jsonl
    <repo_id>_candidates.jsonl
    <repo_id>_source_context.jsonl
    <repo_id>_supply_funnel.csv
    <repo_id>_source_context_funnel.csv
  certified_tasks/
    <repo_id>_certification_funnel.csv
    <repo_id>_certified_tasks.jsonl
    <repo_id>_near_certified_tasks.jsonl
    <repo_id>_task_statements.jsonl
    <repo_id>_review_records.jsonl
  releases/
    <repo_id>_phase0_pilot_release.json
    <repo_id>_phase0_task_table.csv
  results/
    <repo_id>_pre_phase1_workspace_submissions.jsonl
    <repo_id>_pre_phase1_workspace_verifier_results.jsonl
    <repo_id>_pre_phase1_workspace_score_table.csv
    <repo_id>_pre_phase1_workspace_matrix.json
    <repo_id>_pre_phase1_workspace_metrics.json
    <repo_id>_pre_phase1_workspace_cost_ledger.jsonl
    <repo_id>_pre_phase1_workspace_cost_summary.json
    pre_phase1_gate.json
  reports/
    second_repo_selection.md
    <repo_id>_certification_funnel.md
    <repo_id>_mini_release.md
    <repo_id>_workspace_pilot_analysis.md
    phase1_readiness_gate.md
    phase0_decision_memo.md

experiments/phase1_compiler/
  reports/
    phase1_readiness_import.md
  results/
    phase1_readiness_snapshot.json
```

Raw artifacts must remain ignored:

```text
experiments/phase0_headroom/results/raw/
experiments/phase0_headroom/workspaces/
experiments/phase0_headroom/external_repos/
experiments/phase0_headroom/cache/
experiments/phase0_headroom/large_artifacts/
```

## Step 0: Preflight

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, `codex --version`,
   and `kilo --version`.
2. Verify endpoint variables without making a paid call:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

3. Verify current Phase 0 and Phase 1 artifacts exist:

```bash
test -f experiments/phase0_headroom/reports/phase0_decision_memo.md
test -f experiments/phase0_headroom/reports/codex_kilo_workspace_stability_analysis.md
test -f experiments/phase0_headroom/reports/workspace_cost_usage_report.md
test -f experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
test -f experiments/phase0_headroom/configs/model_pricing.yaml
test -f experiments/phase0_headroom/configs/parallelism_policy.yaml
test -f experiments/phase1_compiler/results/toolz_phase1_weighted_score.json
```

4. Run:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
git status --short --ignored experiments/phase0_headroom experiments/phase1_compiler docs/experiments AGENTS.md .gitignore
```

Acceptance:

- endpoint variables are present after sourcing `~/.zshrc`;
- Phase 0 and Phase 1 scoped tests pass;
- current decision memo still says predictive validity is not established;
- no raw workspace, raw log, cache, external repo, or `.venv` file is tracked.

Stop if:

- endpoint variables are missing;
- scoped tests fail;
- the current branch does not contain the repaired workspace ACUT evidence;
- there are unexplained uncommitted changes in experiment config, task, release,
  result, or report files.

Commit only if this step changes a preflight/process report:

```text
Record pre-Phase 1 pilot preflight
```

## Step 1: Choose One Second Target Repository

Preferred second repo: `humanize`.

Fallback order if `humanize` fails the entry gate:

```text
boltons
itsdangerous
```

Do not attempt more than one fallback repo in this runbook. If both `humanize`
and the first fallback fail, stop and write the blocker report.

Actions:

1. Read `experiments/phase0_headroom/configs/repositories.yaml`.
2. For the preferred repo, confirm or create an ignored local clone under:

```text
experiments/phase0_headroom/external_repos/<repo_id>
```

3. Record the selected repo's:
   - GitHub URL;
   - current local HEAD;
   - Python/package manager shape;
   - test command candidate;
   - candidate anchor estimate;
   - why it is selected.
4. Mine a quick deterministic entry sample without LLM calls:

```bash
git -C experiments/phase0_headroom/external_repos/<repo_id> log \
  --since=2020-01-01 \
  --reverse \
  --format='%H%x09%P%x09%ad%x09%s' \
  --date=iso-strict \
  --name-only
```

5. Reject commits that are only docs, CI, release metadata, formatting, lockfiles,
   dependency version bumps, translations, or test-only cleanup.
6. Prefer commits that touch both code and tests in the same target area.

Write:

```text
experiments/phase0_headroom/configs/second_repo_pilot.yaml
experiments/phase0_headroom/reports/second_repo_selection.md
```

Minimum config shape:

```yaml
schema_version: barcarolle.second_repo_pilot.v1
selected_repo_id: humanize
status: selected
repo_url: https://github.com/python-humanize/humanize.git
local_repo: experiments/phase0_headroom/external_repos/humanize
test_environment:
  pythonpath_mode: src_if_present_else_repo_root
  command_template: uv run --project experiments/phase0_headroom --with freezegun --with pytest python -m pytest -q {test_files}
preferred_task_count:
  certification_attempts: 16
  pilot_certified_min: 4
  benchmark_grade_min: 6
  paid_matrix_default_tasks: 4
  paid_matrix_optional_tasks_max: 6
acut:
  adapters_config: experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
  adapters:
    - codex_workspace
    - kilo_workspace
  result_prefix: humanize_pre_phase1_workspace
budget:
  soft_cap_usd: 20
  hard_cap_usd: 45
  stop_before_batch_projected_incremental_usd: 12
parallelism:
  paid_acut_concurrency: 1
  allow_cross_harness_paid_parallelism: false
claim_scope: second_repo_operational_pilot_not_predictive_validation
```

Acceptance:

- selected repo is locally available in an ignored path;
- report explains why the repo is selected and why fallback was not needed, or
  records the fallback reason;
- config names exact adapter IDs and result prefix;
- no paid ACUT call has been made.

Stop if:

- no candidate repo has at least `12` plausible code-plus-test historical
  anchors after the quick deterministic scan;
- the repo cannot be checked out locally;
- the repo requires external services or a test environment that cannot be made
  local and bounded.

Commit:

```text
Select second repo pilot target
```

## Step 2: Add Generic Repo-History Certification Support

The current Phase 0 tooling is Toolz-first. Extend it conservatively rather than
copying Toolz-specific code.

Actions:

1. Add or extend a repo-local tool for generic Python repo history pilots. A
   reasonable path is:

```text
experiments/phase0_headroom/tools/repo_history_pilot.py
```

2. Keep the existing Toolz and Click behavior unchanged.
3. The generic tool must read `configs/second_repo_pilot.yaml` and write the
   selected repo artifacts under the output layout above.
4. Give the tool stable subcommands:

```text
mine
source-context
certify
assemble-release
summarize
```

5. Candidate IDs must be stable:

```text
<repo_id>__hist__001
<repo_id>__hist__002
...
```

6. Use only structured Git data for mining:
   - commit hash;
   - parent hash;
   - commit time;
   - changed paths;
   - numstat;
   - code files;
   - test files.
7. For test execution, support both flat and `src/` layouts:
   - if `<workspace>/src` exists, put it on `PYTHONPATH`;
   - otherwise put `<workspace>` on `PYTHONPATH`;
   - allow `test_environment.command_template` from
     `second_repo_pilot.yaml` to add bounded test dependencies through `uv
     run --with`;
   - do not install dependencies into the target repo checkout.
8. For certification, support these gates:
   - checkout;
   - oracle extractable from changed test files;
   - no-op fail;
   - reference pass;
   - known-bad fail;
   - flakiness check;
   - ambiguity review;
   - solution leakage review;
   - scope clarity review;
   - cost boundedness;
   - taxonomy labelability.
9. If there is no separate known-bad patch, use the no-op baseline as the
   known-bad strategy and record:

```text
known_bad_strategy: no_op_baseline
```

10. Do not count commit-subject-only tasks as certified. They may be
   `near_certified` if mechanical gates pass but source context is too leaky or
   too thin.
11. Add tests that cover:
   - stable task ID generation;
   - code/test path classification for a `src/<package>` repo and a flat
     package repo;
   - first failing gate selection;
   - certified versus near-certified separation;
   - pilot release split generation;
   - no raw paths or full source text copied into committed JSON.

Useful commands:

```bash
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
```

Acceptance:

- generic pilot tool exists and has tests;
- existing `workspace_acut_run.py` tests still pass;
- no existing Toolz result, release, or certification artifact is rewritten in
  this step;
- all new outputs are parameterized by `<repo_id>`.

Stop if:

- implementing generic support requires broad refactoring of existing Phase 0
  tools;
- the tool would need to commit raw diffs, raw issue bodies, or target repo
  checkouts.

Commit:

```text
Add generic second-repo pilot tooling
```

## Step 3: Mine Candidate Supply For The Selected Repo

Actions:

1. Run the generic pilot tool in mining mode:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/second_repo_pilot.yaml \
  mine
```

2. Attempt up to `50` history anchors.
3. Select up to `16` certification candidates from those anchors.
4. Prefer a mix of:
   - code modules;
   - task types;
   - early and late dates;
   - small and medium patches;
   - changed tests that can be run directly.
5. Write deterministic supply artifacts:

```text
experiments/phase0_headroom/candidate_sources/<repo_id>_history_anchors.jsonl
experiments/phase0_headroom/candidate_sources/<repo_id>_candidates.jsonl
experiments/phase0_headroom/candidate_sources/<repo_id>_supply_funnel.csv
experiments/phase0_headroom/target_profiles/<repo_id>_target_profile.json
```

Minimum candidate fields:

```text
task_id
repo_id
repo_url
base_commit
target_commit
task_time
subject
changed_files
code_files
test_files
candidate_oracle_source
changed_lines_added
changed_lines_deleted
change_size_bucket
module_or_package
task_type_proxy
source_type
status
```

Acceptance:

- at least `12` executable candidates are selected, or the report gives a clear
  first failing reason for why fewer were possible;
- each selected candidate has at least one code file and one test file;
- target profile has explicit missing-data labels rather than silent blanks;
- no ACUT call has been made.

Stop if:

- fewer than `6` candidates have a runnable local test target;
- candidate tests depend on network, time-zone-global state that cannot be
  controlled, system services, or missing binary dependencies.

Commit:

```text
Mine second repo candidate supply
```

## Step 4: Build Non-Leaky Source Context And Solver Statements

Actions:

1. If `gh` is available and authenticated, use GitHub metadata to find linked
   PRs and issues. For commit-to-PR lookup, prefer:

```bash
gh api repos/<owner>/<repo>/commits/<sha>/pulls \
  -H 'Accept: application/vnd.github.groot-preview+json'
```

2. Run the source-context subcommand:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/second_repo_pilot.yaml \
  source-context
```

3. For each candidate, record compact source context rows under:

```text
experiments/phase0_headroom/candidate_sources/<repo_id>_source_context.jsonl
experiments/phase0_headroom/candidate_sources/<repo_id>_source_context_funnel.csv
```

4. Classify each source item:
   - `problem_context`: may be used to write solver statements;
   - `scope_context`: evaluator-side only unless it does not reveal solution;
   - `solution_revealing`: never solver-visible;
   - `unusable`: missing, too broad, or too ambiguous.
5. Exclude from solver-visible statements:
   - commit hashes;
   - PR numbers;
   - issue URLs;
   - raw patch text;
   - copied hidden-test assertions;
   - exact implementation checklist language;
   - maintainer comments that directly describe the patch.
6. Write solver statements and review records:

```text
experiments/phase0_headroom/certified_tasks/<repo_id>_task_statements.jsonl
experiments/phase0_headroom/certified_tasks/<repo_id>_review_records.jsonl
```

7. Statement rows must include:
   - `task_id`;
   - `base_commit`;
   - `solver_facing_statement`;
   - `scope_boundaries`;
   - `allowed_context_refs`;
   - `excluded_context_refs`;
   - `oracle_refs`;
   - `harness_test_command`;
   - `statement_review_status`.

Acceptance:

- every candidate that can become certified has a reviewed solver-facing
  statement;
- every certified statement has non-leaky problem context, not just a commit
  subject;
- rejected or near-certified tasks have first failing source-context reason;
- committed rows contain summaries and references, not raw full issue bodies.

Stop if:

- fewer than `4` candidates have non-leaky source context;
- source context mostly reveals implementation rather than problem framing;
- `gh` is unavailable and commit metadata is the only context for nearly all
  candidates.

Commit:

```text
Add second repo source context and statements
```

## Step 5: Certify Tasks And Assemble A Pilot Release

Actions:

1. Run mechanical certification for up to `16` candidates:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/second_repo_pilot.yaml \
  certify
```

2. For each candidate:
   - checkout base commit in an ignored worktree;
   - extract hidden oracle from changed test files;
   - apply test-only patch to base;
   - verify no-op fail;
   - checkout target commit or apply reference code patch;
   - verify reference pass twice;
   - record known-bad strategy and outcome;
   - record runtime and timeout;
   - remove or leave worktrees only under ignored paths.
3. Combine mechanical gates with source-context review gates.
4. Assemble the pilot release:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/second_repo_pilot.yaml \
  assemble-release
```

5. Write:

```text
experiments/phase0_headroom/certified_tasks/<repo_id>_certification_funnel.csv
experiments/phase0_headroom/certified_tasks/<repo_id>_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/<repo_id>_near_certified_tasks.jsonl
experiments/phase0_headroom/releases/<repo_id>_phase0_pilot_release.json
experiments/phase0_headroom/releases/<repo_id>_phase0_task_table.csv
experiments/phase0_headroom/reports/<repo_id>_certification_funnel.md
experiments/phase0_headroom/reports/<repo_id>_mini_release.md
```

Pilot release rules:

- `pilot_grade`: at least `4` certified tasks, with at least `2` early
  `B_real` tasks and at least `2` late `W_real` tasks;
- `benchmark_grade_candidate`: at least `6` certified tasks, with at least
  `3` `B_real` and `3` `W_real`;
- `diagnostic_only`: fewer than `4` certified tasks.

Release schema must include:

```text
schema_version
repo_id
release_id
release_status
benchmark_grade
pilot_grade
certified_task_count
splits
tasks
quality_gates
claim_scope
```

Acceptance:

- every attempted candidate has status and first failing gate;
- certified tasks pass all mechanical and semantic gates;
- `near_certified` tasks do not count toward pilot or benchmark grade;
- release has at least `4` certified tasks and a valid early/late split before
  any paid second-repo ACUT calls.

Stop if:

- release is `diagnostic_only`;
- hidden oracle cannot be injected without exposing tests to the solver;
- reference pass is flaky or cannot be bounded under the selected test command.

Commit:

```text
Certify second repo pilot release
```

## Step 6: Extend Workspace ACUT Loading For The Second Repo

The ACUT protocol must stay the same. Only task package loading should become
repo-generic.

Actions:

1. Extend `experiments/phase0_headroom/tools/workspace_acut_run.py` so it can
   load the selected second repo release in addition to Toolz and Click.
2. Read the selected repo from `configs/second_repo_pilot.yaml`.
3. Build `TaskPackage` rows from:

```text
certified_tasks/<repo_id>_certified_tasks.jsonl
certified_tasks/<repo_id>_task_statements.jsonl
releases/<repo_id>_phase0_pilot_release.json
```

4. Source repo must point to:

```text
experiments/phase0_headroom/external_repos/<repo_id>
```

5. Hidden oracle must be generated from:

```bash
git diff --binary <base_commit> <target_commit> -- <test_paths>
```

6. Allowed edits must be limited to `code_files` unless the certified task
   explicitly allows more paths.
7. Test edits must remain rejected.
8. Add tests for:
   - loading one synthetic second-repo task package;
   - hidden test patch generation from target commit;
   - path policy rejecting tests and out-of-scope edits;
   - Toolz and Click package loading still working.

Acceptance:

- Phase 0 tests pass;
- existing Toolz and Click result summaries can still be regenerated with
  `summarize`;
- no one-shot diff-only prompt path is introduced;
- second-repo tasks use the same workspace adapter and verifier replay path.

Stop if:

- adding second-repo loading would require changing ACUT harness behavior;
- hidden oracle injection would expose tests in solver workspaces.

Commit:

```text
Support second repo workspace ACUT packages
```

## Step 7: Run Second-Repo Workspace Smoke

No full matrix is allowed until smoke passes.

Actions:

1. Select `2` certified second-repo tasks:
   - one `B_real`;
   - one `W_real`.
2. Run adapter preflight for both harnesses:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase0_headroom/configs/second_repo_pilot.yaml \
  --result-prefix <repo_id>_pre_phase1_workspace

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase0_headroom/configs/second_repo_pilot.yaml \
  --result-prefix <repo_id>_pre_phase1_workspace
```

3. Record projected cost in the result cost ledger before the smoke batch.
4. Run Codex and Kilo sequentially:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  smoke \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase0_headroom/configs/second_repo_pilot.yaml \
  --result-prefix <repo_id>_pre_phase1_workspace \
  --task-id <b_real_task_id> \
  --task-id <w_real_task_id>

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  smoke \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase0_headroom/configs/second_repo_pilot.yaml \
  --result-prefix <repo_id>_pre_phase1_workspace \
  --task-id <b_real_task_id> \
  --task-id <w_real_task_id>
```

5. Import usage:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_usage_import.py \
  --root . \
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --result-prefix <repo_id>_pre_phase1_workspace
```

6. Summarize scoreability, usage, latency, and policy violations.

Acceptance:

- all `4` smoke cells have terminal status;
- at least `3/4` smoke cells are scoreable;
- Kilo has no timeout rows;
- there are zero test-edit policy violations;
- usage is observed for at least `3/4` cells, or conservative fallback is used
  and the run does not scale beyond the default matrix;
- observed-or-conservative smoke cost stays below `USD 12`.

Stop if:

- fewer than `3/4` smoke cells are scoreable;
- any solver workspace contains hidden oracle material;
- test-edit policy violations recur;
- Kilo non-interactive timeout behavior recurs;
- usage import fails and projected cost cannot be bounded.

Commit:

```text
Run second repo workspace smoke
```

## Step 8: Run The Bounded Second-Repo Matrix

Actions:

1. Select default matrix tasks:
   - `2` certified `B_real`;
   - `2` certified `W_real`.
2. If the release is `benchmark_grade_candidate`, smoke used observed usage,
   and projected incremental spend remains under `USD 12`, optionally use:
   - `3` certified `B_real`;
   - `3` certified `W_real`.
3. Do not include Toolz or Click cells in this matrix.
4. Reuse successful smoke rows as matrix cells. The `run-matrix` command should
   add only missing task IDs for each adapter when the smoke tasks are included
   in the selected matrix.
5. Run Codex and Kilo sequentially with the same result prefix:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase0_headroom/configs/second_repo_pilot.yaml \
  --result-prefix <repo_id>_pre_phase1_workspace \
  --task-id <task_1> \
  --task-id <task_2> \
  --task-id <task_3> \
  --task-id <task_4>

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase0_headroom/configs/second_repo_pilot.yaml \
  --result-prefix <repo_id>_pre_phase1_workspace \
  --task-id <task_1> \
  --task-id <task_2> \
  --task-id <task_3> \
  --task-id <task_4>
```

6. Re-import usage for all workspace prefixes:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_usage_import.py \
  --root . \
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --result-prefix codex_kilo_workspace \
  --result-prefix codex_kilo_workspace_followup_smoke \
  --result-prefix codex_kilo_workspace_followup \
  --result-prefix kilo_completion_probe \
  --result-prefix codex_kilo_workspace_stability \
  --result-prefix <repo_id>_pre_phase1_workspace
```

Acceptance:

- every scheduled matrix cell has terminal status;
- scoreable rate is at least `75%`;
- no hidden oracle leakage is detected;
- no test-edit policy violation occurs;
- observed-or-conservative incremental spend stays below `USD 20`;
- the result table includes `adapter_id`, `acut_id`, `harness_name`,
  `model_or_agent_name`, `task_id`, `split`, and `terminal_status`.

Stop if:

- scoreable rate drops below `75%`;
- policy violations are dominated by benchmark-side statement or path-scope
  errors rather than ACUT failures;
- cost exceeds the soft cap and the next action would require paid scale-up.

Commit:

```text
Run second repo bounded workspace matrix
```

## Step 9: Analyze The Second-Repo Pilot

Write:

```text
experiments/phase0_headroom/reports/<repo_id>_workspace_pilot_analysis.md
```

Required sections:

- selected repo and release status;
- certification yield;
- source-context yield;
- task split and module distribution;
- scheduled cells and scoreable cells;
- Codex versus Kilo terminal statuses;
- cost and usage;
- policy violations;
- recurring scope issues;
- whether this strengthens or weakens the case for entering Phase 1;
- what it still cannot prove.

Interpretation rules:

- If the second repo matrix is healthy, say it supports starting Phase 1 MVP
  implementation as a multi-repo compiler effort.
- Do not claim predictive validity.
- Do not claim pure harness effect; the correct label remains:

```text
same endpoint model, different CLI harnesses
```

- If the second repo fails, classify the blocker:
  - `second_repo_supply_blocker`;
  - `second_repo_source_context_blocker`;
  - `second_repo_oracle_blocker`;
  - `second_repo_workspace_acut_blocker`;
  - `second_repo_cost_observability_blocker`;
  - `second_repo_policy_blocker`.

Acceptance:

- report maps every failure to a concrete next action;
- report names which evidence can be reused by Phase 1;
- report does not upgrade Phase 0 to predictive validation.

Commit:

```text
Analyze second repo pilot
```

## Step 10: Refresh Phase 1 Readiness Artifacts

This is a readiness snapshot, not full Phase 1 compiler implementation.

Actions:

1. Add a machine-readable gate:

```text
experiments/phase0_headroom/configs/pre_phase1_gate.yaml
experiments/phase0_headroom/results/pre_phase1_gate.json
```

2. Add a human-readable gate:

```text
experiments/phase0_headroom/reports/phase1_readiness_gate.md
```

3. Add Phase 1 import snapshot:

```text
experiments/phase1_compiler/results/phase1_readiness_snapshot.json
experiments/phase1_compiler/reports/phase1_readiness_import.md
```

Gate statuses:

```text
ready_for_phase1_mvp
ready_for_phase1_infrastructure_only
stay_in_phase0_blocked
```

Use `ready_for_phase1_mvp` only if all conditions pass:

- Toolz evidence remains intact;
- second repo release is at least `pilot_grade`;
- second repo workspace matrix scoreable rate is at least `75%`;
- there are zero test-edit policy violations;
- hidden oracle isolation holds;
- usage/cost accounting is observed or conservatively bounded;
- Phase 1 readiness report keeps predictive-validity claims out of scope.

Use `ready_for_phase1_infrastructure_only` if:

- the second repo attempt produced useful compiler requirements and a precise
  blocker, but did not produce a healthy scoreable matrix;
- Phase 1 work should start with source-adapter, certification, schema, or
  split-generation infrastructure, not validation claims.

Use `stay_in_phase0_blocked` if:

- endpoint/auth, ACUT boundary, hidden oracle isolation, or artifact hygiene is
  unresolved.

Minimum JSON fields:

```json
{
  "schema_version": "barcarolle.pre_phase1_gate.v1",
  "generated_at": "...",
  "status": "ready_for_phase1_mvp",
  "phase0_decision": "proceed_regression_benchmark",
  "predictive_validity_established": false,
  "toolz_evidence": {},
  "second_repo_evidence": {},
  "cost_evidence": {},
  "open_blockers": [],
  "phase1_allowed_scope": [],
  "phase1_disallowed_claims": []
}
```

Acceptance:

- readiness gate has one of the three statuses above;
- Phase 1 allowed scope is explicit;
- Phase 1 disallowed claims include predictive validity unless the original
  Phase 1 evidence target is actually met;
- artifacts are small and sanitized.

Commit:

```text
Record Phase 1 readiness gate
```

## Step 11: Update The Phase 0 Decision Memo

Update:

```text
experiments/phase0_headroom/reports/phase0_decision_memo.md
```

Required changes:

- keep current Toolz evidence summary;
- add second repo pilot summary;
- add total workspace usage/cost including second repo;
- state the Phase 1 readiness gate status;
- state whether the next action is:
  - start Phase 1 MVP implementation;
  - start Phase 1 infrastructure only;
  - remain blocked in Phase 0;
- keep `MAE`, `RMSE`, and `Brier` marked `not_applicable_underpowered` unless
  the run genuinely produces enough predictive-validation cells.

Acceptance:

- decision memo no longer says "no second-repository pilot was run";
- decision memo does not claim predictive validity;
- next action is concrete and matches `pre_phase1_gate.json`.

Commit:

```text
Update Phase 0 decision for Phase 1 readiness
```

## Step 12: Final Verification And Hygiene

Actions:

1. Run:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
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

3. Review `git diff --stat`.
4. Commit any remaining cohesive documentation or summary updates.

Final report must include:

- selected second repo;
- certified task count;
- second repo scoreable cells;
- observed-or-conservative incremental spend;
- readiness gate status;
- test commands run;
- commit list created by the worker;
- next smallest useful Phase 1 runbook.

Acceptance:

- scoped tests pass;
- `git diff --check` passes;
- no raw or ignored artifacts are staged;
- branch is clean except ignored files after final commit;
- final report names exact files changed.

## Decision Outcomes

### `ready_for_phase1_mvp`

Start Phase 1 MVP implementation next. The first Phase 1 runbook should build:

- multi-repo release manifest import;
- split-generation policy;
- target profile normalization across repos;
- weighted score summary with uncertainty placeholders;
- explicit `insufficient_evidence` surfaces;
- Phase 1 reports that keep predictive validation out of scope until the
  original Phase 1 sample target is met.

### `ready_for_phase1_infrastructure_only`

Start Phase 1 only for infrastructure that addresses the blocker. Do not run
predictive-validation matrices. The first Phase 1 runbook should target the
failed layer, for example source adapters, certification automation, or generic
workspace package loading.

### `stay_in_phase0_blocked`

Do not enter Phase 1. Write a short blocker runbook that repairs the unresolved
Phase 0 issue before any new paid ACUT task-solving calls.
