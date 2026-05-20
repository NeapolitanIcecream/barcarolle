# Phase 0 Headroom Matrix Follow-Up Runbook

Status: continuation runbook, 2026-05-20.

This runbook is written for one dedicated Codex CLI session continuing after the
Phase 0 source-adapter repair. Its job is to decide whether Phase 0 may continue
from `ready_for_headroom_matrix`, then run the smallest scoreable headroom
matrix if the entry gates pass.

This is still Phase 0. The goal is not to prove predictive validity. The goal is
to test whether the certified mini release can produce valid, budget-bounded
ACUT score cells. Because the current release has only six certified `toolz`
tasks, and four of them come from one `compose` issue thread, the result must be
reported as underpowered directional evidence.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-0-headroom-matrix-followup-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Continue from the existing Phase 0
source-adapter repair artifacts under experiments/phase0_headroom/.

Do not rerun the full Phase 0 pipeline. Do not expand task volume. First run the
"Can Continue Phase 0" entry gate in this runbook. If it fails, repair or stop
according to the gate result.

Use uv for repo-local Python tooling. Run tests with:

  uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools

Do not run broad repository-root pytest. It can collect archived workspaces and
fail for unrelated legacy artifacts.

Budget: keep this follow-up's projected ACUT/model-solving spend at or below
USD 60 unless the runbook explicitly reaches the optional second-ACUT gate and
the user approves a higher cap. Keep total Phase 0 LLM API spend below USD 200.
Write projected and actual costs to experiments/phase0_headroom/results/cost_ledger.jsonl
before and after each paid batch.

Default matrix: one cheap ACUT, three B_real tasks, three W_real tasks. Try the
four G_mini archived Click comparator tasks only after a same-protocol dry run
passes. If G_mini cannot be scored with the same protocol, mark it
not_scoreable_same_protocol and continue with same-repo diagnostics only.

Commit cohesive checkpoints. Do not commit .venv, cloned repositories, pytest
caches, raw model transcripts, raw ACUT workspaces, or large run outputs.
```

## Can Continue Phase 0

Run this gate before starting any paid model or ACUT task-solving call.

Phase 0 may continue only if all required conditions pass:

| Gate | Required condition | Evidence path |
|---|---|---|
| Source-adapter decision | Decision is `ready_for_headroom_matrix`. | `reports/phase0_source_adapter_followup_decision.md` |
| Matrix status | Status is `ready_not_run_after_source_adapter_repair`. | `results/headroom_matrix.json` |
| Certified count | At least six `toolz` tasks are `certified`; zero `near_certified` tasks count toward benchmark-grade release. | `certified_tasks/toolz_certification_funnel.csv` |
| Release status | Mini release is `benchmark_grade_candidate`. | `releases/toolz_phase0_mini_release.json` |
| Split minimum | `B_real` has at least three certified tasks and `W_real` has at least three certified tasks, with no duplicate task across those splits. | `releases/toolz_phase0_task_table.csv` |
| Statement status | Solver-facing task statements are reviewed, not left as draft-only records. | `certified_tasks/toolz_task_statements.jsonl` |
| Review consistency | Review records, certification CSV, certified JSONL, and release manifest agree on task status and first failing gate. | `certified_tasks/` and `releases/` |
| Leakage policy | Solver-facing statements do not contain target commit hashes, PR numbers, issue numbers, GitHub URLs, reference diff snippets, or copied hidden-test assertions. | `certified_tasks/toolz_task_statements.jsonl` |
| Mechanical gates | Reused no-op, reference, known-bad, and flakiness gates remain attached to each certified task. | `certified_tasks/toolz_certified_tasks.jsonl` |
| Budget | Current cumulative LLM API spend is known, and `current + projected <= 160` for the default matrix. Never proceed if it can exceed USD 200. | `results/cost_ledger.jsonl` |
| Tooling | Scoped Phase 0 tests pass. | `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` |
| Artifact hygiene | Raw workspaces, cloned repos, model transcripts, and caches are ignored and unstaged. | `git status --short --ignored` |

If any required condition fails, do not start the matrix. Use these outcomes:

- `repair_certification_hygiene`: status records disagree, statements remain
  draft-only, or manual review metadata is inconsistent;
- `repair_harness_protocol`: task metadata is valid, but the harness cannot dry
  run the release;
- `continue_without_g_mini`: same-repo tasks are scoreable but archived Click
  comparator tasks cannot use the same scoring protocol;
- `stop_phase0_matrix`: budget, leakage, or certification failures make paid
  runs unjustified.

## Entry Hygiene Checks

The source-adapter follow-up is expected to be mostly ready, but the next worker
must check and repair small consistency issues before ACUT runs:

1. `toolz_task_statements.jsonl` should not leave promoted statements at
   `statement_review_status: "draft"`. Use `reviewed` or another explicit final
   status after the review records pass.
2. `manual_review_minutes` in `toolz_certification_funnel.csv` should match the
   review record policy. Do not let repeated follow-up runs multiply review
   minutes unless new review time was actually spent.
3. `toolz_certified_tasks.jsonl` should not retain stale missing-source labels
   for fields that the source-adapter repair filled. If a legacy field is kept
   for provenance, add a clear follow-up metadata field showing the repaired
   source context.

These checks are not optional. They protect the credibility of the certification
claim before spending budget on model runs.

## Budget Rules

The original Phase 0 hard cap remains USD 200 total LLM API spend.

Default cap for this follow-up:

- USD 0-10: optional dry-run setup or protocol debugging with a model, only if
  deterministic debugging is not enough;
- USD 0-60: one cheap ACUT over the minimal matrix;
- USD 0: optional second ACUT until the first ACUT produces valid same-repo
  score cells and the user approves expanding the run;
- reserve: keep at least USD 40 below the original hard cap.

Stop rules:

- Do not start any paid batch without a projected-cost ledger entry.
- Stop before the batch if projected cumulative spend would exceed USD 160.
- Stop and ask before projected cumulative spend would exceed USD 180.
- Never exceed USD 200 total Phase 0 LLM API spend.
- Do not spawn parallel paid ACUT runs in this follow-up.
- Do not use LLM calls to repair CSV/JSON formatting, count rows, or compute
  metrics.

Every paid call must append or update:

```text
experiments/phase0_headroom/results/cost_ledger.jsonl
```

Ledger records must not contain raw prompts, raw completions, API keys, endpoint
URLs, or private transcripts.

## Output Layout

Create or update these files:

```text
experiments/phase0_headroom/
  configs/
    headroom_matrix.yaml
  results/
    headroom_entry_gate.json
    headroom_protocol_dry_run.json
    headroom_submissions.jsonl
    headroom_verifier_results.jsonl
    headroom_score_table.csv
    headroom_matrix.json
    headroom_metrics.json
    cost_ledger.jsonl
  reports/
    headroom_matrix_followup_process.md
    headroom_entry_gate.md
    headroom_protocol_dry_run.md
    headroom_analysis.md
    phase0_headroom_matrix_decision.md
```

If raw ACUT workspaces, transcripts, or verifier tails are needed, store them
under ignored raw paths and commit only a small manifest with paths, digests,
producer, and reproduction command.

## Step 0: Preflight

Actions:

1. Record branch, HEAD commit, date, `uv --version`, Python version, and current
   cumulative cost.
2. Confirm the current release and source-adapter decision are present.
3. Run:

```bash
git status --short --ignored experiments/phase0_headroom docs/experiments .gitignore
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
```

4. Create `reports/headroom_matrix_followup_process.md`.

Outputs:

- `reports/headroom_matrix_followup_process.md`

Acceptance:

- scoped tests pass;
- ignored raw paths are not staged;
- cumulative cost is known or conservatively treated as unknown with no paid
  calls allowed until clarified.

Stop if:

- the worker cannot identify the current Phase 0 release;
- unexplained local edits touch certification or release outputs.

## Step 1: Run The Entry Gate

Actions:

1. Evaluate every gate in `Can Continue Phase 0`.
2. Write a machine-readable gate record.
3. Write a short human-readable gate report.
4. If a gate fails, set the decision to the matching repair or stop outcome.

Outputs:

- `results/headroom_entry_gate.json`
- `reports/headroom_entry_gate.md`

Minimum JSON fields:

```json
{
  "schema_version": "barcarolle.phase0_headroom_entry_gate.v1",
  "generated_at": "",
  "can_continue_phase0": false,
  "gates": [],
  "decision": "",
  "blocking_reasons": []
}
```

Acceptance:

- every gate has `pass`, `fail`, or `not_applicable`;
- failures name exact files and task IDs where possible;
- no ACUT run starts until `can_continue_phase0` is `true`.

## Step 2: Repair Entry Hygiene If Needed

Run this step only for small consistency fixes. Do not use it to change task
meaning, oracle files, base commits, or source context.

Allowed repairs:

- mark reviewed task statements as reviewed after matching review records pass;
- correct manual review minute accumulation if reruns inflated it;
- add follow-up provenance fields that clarify source context repair;
- update reports to reflect the repaired metadata.

Disallowed repairs:

- promoting new tasks;
- changing oracle tests;
- changing solver-facing task scope;
- rewriting statements from implementation diffs;
- adding new repositories.

Outputs:

- updated certification/release metadata if needed;
- updated `reports/headroom_entry_gate.md`;
- a checkpoint commit if files changed.

Acceptance:

- the entry gate passes after repair;
- repairs are mechanical and auditable;
- scoped tests still pass.

Stop if:

- a hygiene issue changes task semantics or certification status. Return to the
  source-adapter follow-up instead.

## Step 3: Define The Minimal Matrix

Actions:

1. Create `configs/headroom_matrix.yaml`.
2. Use the release's exact task IDs:
   - `B_real`: three certified early same-repo tasks;
   - `W_real`: three certified later same-repo tasks;
   - `G_mini`: four archived Click comparator tasks, pending dry-run approval.
3. Select one cheap ACUT and record:
   - model or agent name;
   - command template;
   - per-task timeout;
   - projected cost per task and total projected cost;
   - output contract;
   - verifier command.
4. Set `allow_second_acut: false` by default.

Suggested config shape:

```yaml
schema_version: barcarolle.phase0_headroom_matrix_config.v1
release_id: toolz-phase0-mini-source-adapter-candidate
default_matrix:
  acuts:
    - id: cheap_acut_1
      max_projected_cost_usd: 60
  splits:
    B_real: []
    W_real: []
    G_mini: []
allow_second_acut: false
claim_scope: underpowered_directional_diagnostic
```

Outputs:

- `configs/headroom_matrix.yaml`

Acceptance:

- the config references certified same-repo task IDs from the release;
- projected cost keeps total spend below the stop threshold;
- the claim scope is explicitly `underpowered_directional_diagnostic`.

## Step 4: Protocol Dry Run

Actions:

1. Dry-run the harness without paid model calls.
2. For each `toolz` task, verify:
   - base checkout can be reconstructed;
   - solver-facing statement can be loaded without evaluator-private fields;
   - verifier command is available;
   - no-op/reference mechanical gate metadata is attached.
3. For each `G_mini` task, verify whether it can use the same ACUT invocation
   and scoring protocol as the `toolz` tasks.
4. Mark each task as:
   - `scoreable_same_protocol`;
   - `scoreable_different_protocol`;
   - `metadata_only`;
   - `not_scoreable`.

Outputs:

- `results/headroom_protocol_dry_run.json`
- `reports/headroom_protocol_dry_run.md`

Acceptance:

- all six `toolz` tasks are `scoreable_same_protocol`, or the matrix stops for
  `repair_harness_protocol`;
- `G_mini` tasks are included in paid runs only if they are
  `scoreable_same_protocol`;
- if `G_mini` is not scoreable, the report pre-declares same-repo-only
  diagnostics.

Stop if:

- any same-repo task cannot be scored with the current harness;
- solver-facing statements expose evaluator-private fields.

## Step 5: Ledger Gate Before Paid Runs

Actions:

1. Compute projected cost for the exact paid batch.
2. Append or update a ledger record with:
   - event: `projected_headroom_matrix_batch`;
   - task IDs;
   - ACUT ID;
   - projected max cost;
   - cumulative projected cost;
   - approval status.
3. Confirm the batch does not cross the stop thresholds.

Outputs:

- updated `results/cost_ledger.jsonl`
- process-log entry

Acceptance:

- projected cost is recorded before the batch starts;
- the batch covers only dry-run-approved tasks;
- no parallel paid ACUT workers are scheduled.

## Step 6: Run One Cheap ACUT

Actions:

1. Run the ACUT on the smallest approved batch:
   - three `B_real`;
   - three `W_real`;
   - four `G_mini` only if same-protocol dry run passed.
2. Capture raw transcripts and workspaces under ignored paths.
3. Commit only small metadata and result records.
4. Label every task attempt:
   - `submitted`;
   - `not_submitted`;
   - `invalid_output`;
   - `harness_error`;
   - `verified_pass`;
   - `verified_fail`;
   - `timeout`;
   - `cost_stopped`.

Outputs:

- `results/headroom_submissions.jsonl`
- raw ignored artifacts referenced by manifest

Acceptance:

- every scheduled cell has one terminal status;
- invalid outputs and harness errors are separated from verified failures;
- actual or estimated cost is recorded after the batch.

Stop if:

- more than one same-repo task fails because of harness or protocol errors;
- actual cost exceeds projection enough to threaten the stop thresholds.

## Step 7: Verify And Score

Actions:

1. Run verifiers for each submitted same-repo task.
2. Run `G_mini` verifiers only if the dry run established same protocol.
3. Produce a score table with one row per ACUT/task cell.
4. Compute only metrics justified by the sample:
   - pass rate by split;
   - scoreable-cell count;
   - invalid/harness-error count;
   - directional `B_real` vs `W_real` notes for the single ACUT.
5. Do not report MAE/RMSE, Brier score, or predictive residual improvement for a
   one-ACUT matrix. Mark them `not_applicable_underpowered`.

Outputs:

- `results/headroom_verifier_results.jsonl`
- `results/headroom_score_table.csv`
- `results/headroom_metrics.json`
- `reports/headroom_analysis.md`

Acceptance:

- score table distinguishes verified task outcomes from infrastructure
  failures;
- metrics do not claim predictive validity from one ACUT;
- `G_mini` comparison is reported only if same-protocol cells exist.

## Step 8: Decide Whether Phase 0 Continues

Write `reports/phase0_headroom_matrix_decision.md`.

Allowed decisions:

- `phase0_scoreable_continue_second_acut`: one ACUT produced valid same-repo
  cells, cost is still low, and a second ACUT would materially improve the
  diagnostic;
- `phase0_same_repo_diagnostic_complete`: same-repo matrix is scoreable, but
  evidence is too small for more spending in Phase 0;
- `repair_generic_comparator_protocol`: same-repo cells work, but `G_mini`
  cannot be scored under the same protocol;
- `repair_harness_protocol`: paid or dry-run cells are dominated by harness
  errors;
- `return_to_certification`: task statements, leakage, or oracle metadata fail
  under matrix use;
- `stop_phase0`: the matrix does not justify more Phase 0 work.

The decision memo must answer:

1. Did Phase 0 meet the entry conditions to continue?
2. How many cells were scoreable?
3. How many failures were agent failures rather than harness failures?
4. Was `G_mini` same-protocol scoreable?
5. How much budget was spent?
6. What claim is now supported, and what claim is still unsupported?
7. What is the next smallest useful action?

Acceptance:

- the decision follows from scoreable cells and cost, not from desired narrative;
- limitations name the small sample, one-ACUT design, and clustered `compose`
  tasks;
- any recommendation for a second ACUT includes projected cost and expected
  evidentiary value.

## Step 9: Commit Hygiene

Actions:

1. Run:

```bash
git status --short --ignored experiments/phase0_headroom docs/experiments .gitignore
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
```

2. Confirm raw artifacts are ignored and unstaged.
3. Stage only configs, scripts, small manifests, JSONL/CSV result records, and
   reports.
4. Commit cohesive checkpoints. Suggested boundaries:
   - entry gate and hygiene repair;
   - matrix config and protocol dry run;
   - ACUT run results and decision memo.

Acceptance:

- committed artifacts are small and reviewable;
- raw ACUT outputs, transcripts, cloned repositories, `.venv`, caches, and full
  workspaces remain out of Git;
- final status is clean except for intentionally ignored artifacts.

## Final Success Criteria

This follow-up succeeds when the repo contains:

- a passed or failed `Can Continue Phase 0` entry gate;
- repaired certification hygiene if needed;
- a minimal matrix config with explicit cost projection;
- a protocol dry-run result for same-repo and optional `G_mini` tasks;
- one cheap ACUT result set, if the entry and ledger gates passed;
- split-level scoreable-cell diagnostics;
- a decision memo with one of the allowed decisions;
- total Phase 0 LLM API spend below USD 200.

If the entry gate fails, the follow-up may still be successful if it stops before
paid runs and records a precise repair path. Do not spend ACUT budget to hide a
certification, leakage, harness, or comparator-protocol problem.
