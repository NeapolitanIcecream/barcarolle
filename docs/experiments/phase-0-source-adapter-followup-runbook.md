# Phase 0 Source Adapter Follow-Up Runbook

Status: continuation runbook, 2026-05-20.

This runbook is written for one dedicated Codex CLI session continuing from the
current Phase 0 checkpoint. Its job is to repair the source-adapter and review
layer that blocked Phase 0 at `repair_source_adapter`.

Do not rerun the full Phase 0 pipeline. The current evidence says checkout,
replay, oracle extraction, no-op/reference checks, known-bad checks, flakiness,
and cost bounds are viable for six `toolz` anchors. The blocker is that these
anchors are only `near_certified` because their task statements are derived from
commit subjects and public Git diffs, which leaves solution-leakage review weak.

The goal is to produce benchmark-grade task statements and review records for
the existing oracle-valid anchors. If that cannot be done, the run should explain
which source text is missing and whether the next repair is a better adapter, a
different repository, or a smaller benchmark claim.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-0-source-adapter-followup-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Continue from the existing Phase 0
artifacts under experiments/phase0_headroom/. Do not rerun the full Phase 0
pipeline unless this runbook explicitly says to rerun a narrow check.

Use uv for repo-local Python tooling. Run tests with:

  uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools

Do not run a broad repository-root pytest command; it can collect archived
workspaces and fail for unrelated legacy artifacts.

Do not start ACUT task-solving runs. Do not spend more than USD 60 on optional
LLM help for this follow-up, and keep total Phase 0 LLM API spend below the
existing USD 200 cap. Prefer deterministic source fetching, local scripts, and
manual review. Update experiments/phase0_headroom/results/cost_ledger.jsonl for
any paid model call whose cost is observable.

Goal: for the six existing oracle-valid near-certified toolz anchors, fetch or
reconstruct non-leaky source context, draft solver-facing task statements, run
ambiguity/leakage/scope reviews, and update the certification funnel. At least
six tasks should become certified, or the report must explain exactly why fewer
can be certified.

Commit cohesive checkpoints. Do not commit cloned repositories, .venv,
pytest caches, raw transcripts, raw model responses, or large run outputs.
```

## Starting Point

Use the committed Phase 0 state as input:

- `experiments/phase0_headroom/certified_tasks/toolz_near_certified_tasks.jsonl`
- `experiments/phase0_headroom/certified_tasks/toolz_certification_funnel.csv`
- `experiments/phase0_headroom/candidate_sources/toolz_candidates.jsonl`
- `experiments/phase0_headroom/releases/toolz_phase0_task_table.csv`
- `experiments/phase0_headroom/reports/phase0_decision_memo.md`
- `experiments/phase0_headroom/reports/certification_funnel.md`
- `experiments/phase0_headroom/reports/headroom_analysis.md`
- `experiments/phase0_headroom/results/raw_artifact_manifest.json`

The expected initial state is:

- repository: `toolz`;
- near-certified tasks: `6`;
- certified tasks: `0`;
- paid model calls: `0`;
- current decision: `repair_source_adapter`;
- mini release status: `diagnostic_only`;
- headroom matrix status: `blocked_underpowered`.

If the local artifacts differ, record the difference in
`experiments/phase0_headroom/reports/source_adapter_followup_process.md` and use
the local committed artifacts as the source of truth.

## Budget Rules

The original Phase 0 hard cap remains USD 200 total LLM API spend. This
follow-up has a narrower internal cap:

- USD 0-20: optional help summarizing issue or PR discussions;
- USD 0-30: optional task-statement cleanup or second-pass leakage review;
- USD 10 reserve: failed calls or one small comparison review;
- USD 0: ACUT task-solving runs in this follow-up.

Stop rules:

- Do not start any paid ACUT/model-solving run.
- Stop optional LLM review at USD 50 unless the next call is needed to complete
  a specific review record.
- Stop and ask the user before this follow-up can exceed USD 60.
- Never exceed the original Phase 0 total cap of USD 200.
- If the worker cannot observe session-level cost, record projected external
  calls only and keep this follow-up's extra projected spend at USD 0.

Every observable paid model call must be recorded in:

```text
experiments/phase0_headroom/results/cost_ledger.jsonl
```

Do not put raw prompts, private responses, tokens, API keys, or endpoints into
committed artifacts. The ledger should contain cost metadata and an artifact
reference only.

## Artifact Policy

Separate evaluator-private source metadata from solver-facing task text.

Evaluator-private artifacts may include commit hashes, PR numbers, issue
numbers, source URLs, source timestamps, and review notes. Solver-facing task
artifacts must not include:

- target commit hashes;
- PR or issue numbers that trivially identify the patch;
- GitHub commit URLs;
- public diff URLs;
- reference patch snippets;
- changed test assertions copied as the task statement;
- implementation-level commit subjects such as `implement Compose.__repr__`;
- review comments written after the solution was proposed if they reveal the
  patch.

Allowed solver-facing material:

- a concise problem statement derived from non-leaky issue, PR, changelog, or
  pre-solution discussion text;
- affected public API or module, if naming it does not reveal the patch;
- reproduction behavior or expected user-visible behavior, stated without
  exposing hidden tests;
- setup and test command metadata needed by the harness;
- explicit scope boundaries.

If only solution-revealing text exists, reject the task or keep it
`near_certified`. Do not promote it by rewriting the commit diff into a polished
task statement.

## Output Layout

Create or update these files:

```text
experiments/phase0_headroom/
  candidate_sources/
    toolz_source_context.jsonl
    toolz_source_context_funnel.csv
  certified_tasks/
    toolz_task_statements.jsonl
    toolz_review_records.jsonl
    toolz_certification_funnel.csv
    toolz_certified_tasks.jsonl
    toolz_near_certified_tasks.jsonl
  releases/
    toolz_phase0_mini_release.json
    toolz_phase0_task_table.csv
  reports/
    source_adapter_followup_process.md
    source_adapter_repair.md
    source_context_funnel.md
    certification_funnel.md
    phase0_source_adapter_followup_decision.md
```

Use JSONL for per-task records. Keep each record self-contained and
machine-readable.

## Step 0: Preflight

Actions:

1. Record branch, HEAD commit, date, `uv --version`, Python version, and `gh`
   authentication status if `gh` is available.
2. Confirm the working tree is clean or only contains understood local changes.
3. Confirm the six near-certified task IDs from
   `certified_tasks/toolz_near_certified_tasks.jsonl`.
4. Read the current cumulative cost from `results/cost_ledger.jsonl`.
5. Create `reports/source_adapter_followup_process.md`.
6. Run the scoped Phase 0 tooling tests:

```bash
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
```

Outputs:

- `reports/source_adapter_followup_process.md`

Acceptance:

- the six target task IDs are listed;
- the scoped test command passes, or a tool-only blocker is recorded;
- no ACUT/model-solving run has started;
- cumulative cost is known or conservatively treated as unknown with no
  additional external model calls.

Stop if:

- the worker cannot identify the current Phase 0 artifacts;
- the working tree contains unexplained edits to certification outputs.

## Step 1: Lock The Repair Target Set

Actions:

1. Build a table from the existing six near-certified records.
2. For each task, record:
   - `task_id`;
   - anchor commit;
   - base commit;
   - changed files;
   - oracle files;
   - current first failing gate;
   - current leakage risk;
   - current split membership if present.
3. Do not add new anchors in this follow-up unless fewer than six current
   anchors can be reviewed because source data is unavailable.

Outputs:

- `candidate_sources/toolz_source_context_funnel.csv`
- an initial section in `reports/source_context_funnel.md`

Acceptance:

- the repair target set is exactly the six oracle-valid near-certified tasks,
  or the report explains every substitution;
- no task is promoted before source context is fetched and reviewed.

## Step 2: Fetch Source Context

Actions:

1. For each target commit, find linked PRs and issues using deterministic
   sources. Prefer GitHub API or `gh`; fall back to local Git metadata and public
   URLs if needed.
2. Fetch only source metadata and discussion text needed for certification:
   - PR title and body;
   - linked issue title and body;
   - pre-merge comments that describe the problem or expected behavior;
   - labels and timestamps;
   - release or changelog text, if it provides non-leaky problem context.
3. Mark each source item by leakage class:
   - `problem_context`: can inform solver-facing statement;
   - `scope_context`: useful for boundaries but not task text;
   - `solution_revealing`: evaluator-private only;
   - `unusable`: irrelevant, missing, deleted, or too ambiguous.
4. Store raw long responses outside Git if they are large. Commit only compact
   source metadata, short summaries, hashes, and URLs.

Suggested commands:

```bash
gh api /repos/pytoolz/toolz/commits/<sha>/pulls \
  -H "Accept: application/vnd.github+json"

gh api /repos/pytoolz/toolz/issues/<number>

gh api /repos/pytoolz/toolz/issues/<number>/comments
```

If `gh` is unavailable or unauthenticated, use unauthenticated GitHub API calls
sparingly and record rate-limit failures as source-context blockers.

Outputs:

- `candidate_sources/toolz_source_context.jsonl`
- `candidate_sources/toolz_source_context_funnel.csv`
- `reports/source_context_funnel.md`

Acceptance:

- each target task has a source-context status:
  `non_leaky_context_found`, `only_solution_revealing_context`,
  `missing_context`, or `ambiguous_context`;
- every committed source record names its URL, timestamp if available, leakage
  class, and whether it may be used in solver-facing text;
- no solver-facing task statement has been drafted from a reference diff.

Stop if:

- fewer than three target tasks have any non-leaky source context and no
  obvious fallback source exists.

## Step 3: Draft Solver-Facing Task Statements

Actions:

1. For each task with `non_leaky_context_found`, write a solver-facing task
   statement.
2. Keep the statement short and operational:
   - problem or behavior to address;
   - affected API/module if safe;
   - constraints and non-goals;
   - test command or harness metadata outside the natural-language prompt.
3. Do not include target commit hashes, PR numbers, issue numbers, commit
   subjects, diff snippets, or changed test assertions in solver-facing text.
4. For each statement, record the source items used and the source items
   excluded for leakage.
5. If a task needs a small amount of LLM cleanup, record the estimated or actual
   cost in the ledger and keep the raw prompt/response out of Git.

Outputs:

- `certified_tasks/toolz_task_statements.jsonl`

Minimum record fields:

```json
{
  "task_id": "",
  "repo_id": "toolz",
  "base_commit": "",
  "solver_facing_statement": "",
  "allowed_context_refs": [],
  "excluded_context_refs": [],
  "oracle_refs": [],
  "harness_test_command": "",
  "statement_author": "codex_cli_followup",
  "statement_review_status": "draft"
}
```

Acceptance:

- every drafted statement can be read without inspecting the reference patch;
- each statement has at least one non-leaky allowed source reference;
- tasks without enough non-leaky context remain `near_certified` or become
  `rejected`, not `certified`.

## Step 4: Run Review Gates

Actions:

Review each drafted task against the semantic certification gates:

1. ambiguity review;
2. solution-leakage review;
3. scope-clarity review;
4. cost boundedness;
5. taxonomy labelability.

For this follow-up, do not rerun no-op/reference/known-bad/flakiness checks
unless the source adapter changes the task's oracle or base checkout. Reuse the
existing mechanical gate results and record that reuse in the review record.

Review rubric:

- `pass`: enough evidence for benchmark-grade release;
- `weak`: usable for diagnosis but not benchmark-grade;
- `fail`: should be rejected or needs a different source adapter.

Outputs:

- `certified_tasks/toolz_review_records.jsonl`
- updated `certified_tasks/toolz_certification_funnel.csv`
- updated `certified_tasks/toolz_certified_tasks.jsonl`
- updated `certified_tasks/toolz_near_certified_tasks.jsonl`
- `reports/certification_funnel.md`

Minimum review record fields:

```json
{
  "task_id": "",
  "mechanical_gates_reused_from": "phase0_initial",
  "ambiguity_review": "",
  "solution_leakage_review": "",
  "scope_clarity_review": "",
  "cost_boundedness": "",
  "taxonomy_labelability": "",
  "status_after_review": "",
  "first_failing_gate": "",
  "review_minutes": 0,
  "review_notes": ""
}
```

Acceptance:

- `certified` tasks have all required mechanical and semantic gates at `pass`;
- `near_certified` tasks clearly name the weak or missing gate;
- `rejected` tasks name the first failing gate;
- review records preserve enough detail for an external reviewer to audit the
  promotion decision without raw transcripts.

Stop if:

- fewer than six tasks can pass semantic review and the missing source context is
  not repairable within this follow-up.

## Step 5: Refresh The Mini Release

Run this step only if at least one task changes status.

Actions:

1. Update `releases/toolz_phase0_mini_release.json`.
2. Update `releases/toolz_phase0_task_table.csv`.
3. If at least six tasks are certified, set release status to
   `benchmark_grade_candidate`.
4. If fewer than six tasks are certified, keep release status
   `diagnostic_only`.
5. Keep `near_certified` tasks visible but excluded from benchmark-grade counts.
6. Do not run ACUTs in this follow-up.

Outputs:

- `releases/toolz_phase0_mini_release.json`
- `releases/toolz_phase0_task_table.csv`
- `reports/source_adapter_repair.md`

Acceptance:

- release counts match the certification funnel;
- benchmark-grade counts include only `certified` tasks;
- the report says whether the next run may proceed to a budgeted headroom
  matrix.

## Step 6: Decision Memo

Write `reports/phase0_source_adapter_followup_decision.md`.

Required sections:

1. starting blocker;
2. source-context coverage;
3. task-statement and review method;
4. certification result;
5. release status after repair;
6. remaining leakage or ambiguity risks;
7. budget used;
8. decision.

Allowed decisions:

- `ready_for_headroom_matrix`: at least six tasks are certified and the mini
  release is a benchmark-grade candidate;
- `continue_source_adapter_repair`: some tasks improved, but fewer than six are
  certified and the next repair is concrete;
- `switch_target_repo`: `toolz` lacks enough non-leaky source context for this
  method;
- `narrow_to_diagnostic_benchmark`: certification remains too weak for
  predictive claims, but the diagnostic release is still useful;
- `stop_phase0`: source-context and certification evidence do not justify
  spending more Phase 0 effort.

Acceptance:

- the decision follows from gate-level evidence;
- unsupported claims are marked as open questions;
- if the decision is `ready_for_headroom_matrix`, the memo names the exact
  smallest next matrix and projected maximum cost;
- if the decision is not `ready_for_headroom_matrix`, the memo names the next
  smallest useful repair or pivot.

## Step 7: Commit Hygiene

Actions:

1. Run:

```bash
git status --short --ignored experiments/phase0_headroom docs/experiments .gitignore
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
```

2. Confirm ignored raw artifacts are not staged.
3. Stage only docs, scripts, small manifests, JSONL review records, CSV tables,
   and reports.
4. Commit in cohesive checkpoints. Suggested commit boundaries:
   - source-context adapter and manifests;
   - task statements and review records;
   - refreshed release and decision memo.

Acceptance:

- committed artifacts are small and reviewable;
- raw GitHub responses, model transcripts, cloned repositories, `.venv`, caches,
  and full workspaces remain out of Git;
- the scoped `uv` test command passes;
- final status is clean except for intentionally ignored artifacts.

## Final Success Criteria

This follow-up succeeds when the repo contains:

- a source-context funnel for the six existing oracle-valid `toolz` anchors;
- solver-facing task statements for every task that can use non-leaky context;
- review records for ambiguity, leakage, scope, cost, and taxonomy gates;
- an updated certification funnel separating `certified`, `near_certified`, and
  `rejected`;
- an updated mini release labeled either `benchmark_grade_candidate` or
  `diagnostic_only`;
- a decision memo with one of the allowed decisions;
- total Phase 0 LLM API spend still below USD 200.

The follow-up should stop early if it can make a defensible negative or pivot
decision. Do not spend budget or add new repositories merely to avoid a
diagnostic-only outcome.
