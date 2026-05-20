# Phase 0 Closeout Follow-Up Runbook

Status: continuation runbook, 2026-05-20.

This runbook is written for one dedicated Codex CLI session after the
source-adapter and headroom-matrix follow-ups have completed. Its job is to
return to the original Phase 0 runbook and close out Step 8 and Step 9 with a
single canonical Phase 0 decision memo.

Do not run more ACUTs in this closeout. Do not add tasks, repositories, or
source adapters. The work here is synthesis, consistency checking, and commit
hygiene.

## Relationship To The Original Phase 0 Plan

The original Phase 0 runbook had three evidence-building parts and one closeout
part:

- Step 0-4: preflight, budget, repository selection, target profile, and
  candidate supply;
- Step 5-6: certification gates and mini release assembly;
- Step 7: budgeted headroom matrix;
- Step 8-9: final decision memo and commit hygiene.

The first Phase 0 run reached a real blocker at Step 5: six `toolz` tasks were
oracle-valid but only `near_certified`, so Step 7 could not be justified. The
source-adapter follow-up repaired that blocker by adding non-leaky issue-derived
task statements and promoting six tasks to `certified`.

The headroom-matrix follow-up then ran the smallest allowed Step 7 continuation:
one cheap ACUT over six certified same-repo tasks. It produced scoreable
same-repo cells, but it did not produce same-protocol `G_mini` comparator cells.

That means the remaining original Phase 0 work is only:

1. update `experiments/phase0_headroom/reports/phase0_decision_memo.md` so it
   reflects the final state rather than the earlier `repair_source_adapter`
   blocker;
2. choose one of the original runbook's allowed final decisions;
3. record the next smallest useful experiment;
4. run Step 9 commit hygiene.

The closeout should not change the evidentiary record. It should make the final
claim match the evidence.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-0-closeout-followup-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Do not rerun Phase 0, do not run more
ACUTs, do not add tasks, and do not fetch new source context. This is a closeout
pass that returns to the original Phase 0 runbook Step 8 and Step 9.

Use the current artifacts under experiments/phase0_headroom/ as the evidence
record. Update the canonical decision memo:

  experiments/phase0_headroom/reports/phase0_decision_memo.md

The final decision should use one of the original Phase 0 allowed decisions. If
the current evidence is unchanged, prefer `proceed_regression_benchmark`: task
supply, certification, release assembly, and same-repo scoring work, but
predictive validity is not supported because `G_mini` is not same-protocol
scoreable.

Run:

  git diff --check
  uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools

Commit only small docs/reports/metadata changes. Do not commit raw workspaces,
.venv, pytest caches, model transcripts, or raw ACUT outputs.
```

## Inputs

Use these artifacts as the evidence source:

- `docs/experiments/phase-0-runbook.md`
- `experiments/phase0_headroom/reports/phase0_decision_memo.md`
- `experiments/phase0_headroom/reports/distribution_mismatch.md`
- `experiments/phase0_headroom/reports/certification_funnel.md`
- `experiments/phase0_headroom/reports/mini_release.md`
- `experiments/phase0_headroom/reports/phase0_source_adapter_followup_decision.md`
- `experiments/phase0_headroom/reports/phase0_headroom_matrix_decision.md`
- `experiments/phase0_headroom/reports/headroom_analysis.md`
- `experiments/phase0_headroom/results/headroom_metrics.json`
- `experiments/phase0_headroom/results/headroom_matrix.json`
- `experiments/phase0_headroom/results/cost_ledger.jsonl`
- `experiments/phase0_headroom/releases/toolz_phase0_mini_release.json`
- `experiments/phase0_headroom/certified_tasks/toolz_certification_funnel.csv`

Do not use raw ACUT transcripts or raw GitHub API responses unless a committed
summary is inconsistent and needs audit.

## Step 0: Preflight

Actions:

1. Record branch, HEAD commit, and current working-tree status.
2. Confirm the current headroom-matrix decision exists.
3. Confirm `phase0_decision_memo.md` is stale or incomplete relative to the
   follow-up evidence.
4. Run:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
```

Acceptance:

- tests pass;
- no unexplained local edits touch Phase 0 reports or results;
- the worker can identify the final matrix decision.

Stop if:

- the matrix follow-up artifacts are missing;
- the working tree contains unexplained uncommitted experimental results.

## Step 1: Build The Evidence Summary

Actions:

Create a concise evidence summary for the final memo:

1. repo selection and scope;
2. distribution mismatch;
3. candidate supply funnel;
4. certification after source-adapter repair;
5. mini release status;
6. matrix entry gate and protocol dry run;
7. scoreable same-repo cell results;
8. `G_mini` comparator blocker;
9. total estimated LLM/API spend;
10. threats to validity.

Use exact numbers from committed artifacts. Do not infer new metrics from raw
files.

Expected facts if the current artifacts are unchanged:

- primary target repo: `toolz`;
- generic comparator: archived Click metadata;
- distribution mismatch rows with absolute gap >= 0.15: `12`;
- candidate anchors attempted: `16`;
- executable candidates: `16`;
- certified tasks after source-adapter repair: `6`;
- near-certified tasks after repair: `0`;
- release status: `benchmark_grade_candidate`;
- entry gate passed: `true`;
- same-repo scoreable cells: `6`;
- same-repo pass/fail: `2` pass, `4` fail;
- `G_mini` same-protocol scoreable: `false`;
- estimated LLM/API spend: `USD 60.00`, with exact Codex CLI cost not
  observable.

Acceptance:

- each number can be traced to a committed artifact;
- unsupported claims are labeled as open questions or limitations.

## Step 2: Choose The Final Phase 0 Decision

Use only the original runbook's allowed decisions:

- `proceed_predictive`;
- `proceed_tuning_feedback`;
- `proceed_regression_benchmark`;
- `repair_source_adapter`;
- `stop`.

Decision guidance:

- Use `proceed_predictive` only if there is a same-protocol comparison involving
  `G_mini`, `B_real`, and `W_real` with enough scoreable cells to support a
  predictive-validity next phase. The current evidence should not meet this bar.
- Use `proceed_tuning_feedback` if certification and scoring work, but the next
  contribution should be optimizer feedback rather than benchmark packaging.
- Use `proceed_regression_benchmark` if certified task supply and same-repo
  scoring work, but generic-comparator and predictive framing are not yet
  supported. This is the expected decision for the current artifacts.
- Use `repair_source_adapter` only if certification is still blocked. The
  current source-adapter follow-up should have resolved this.
- Use `stop` only if the follow-up evidence shows the restart is not worth
  continuing in any form.

Acceptance:

- the memo's decision is one of the allowed decisions;
- the decision matches the evidence, not the preferred narrative;
- any non-chosen decision with a plausible case is addressed in limitations.

## Step 3: Rewrite The Canonical Decision Memo

Update:

```text
experiments/phase0_headroom/reports/phase0_decision_memo.md
```

Required structure:

```markdown
# Phase 0 Decision Memo

Decision: `<allowed_decision>`.

## Scope
...

## Evidence Summary
...

## What Phase 0 Supports
...

## What Phase 0 Does Not Support
...

## Threats To Validity
...

## Next Smallest Useful Experiment
...
```

The memo should be readable without inspecting raw artifacts. It should name the
follow-up reports as supporting artifacts when useful, but it should not require
the reader to reconstruct the decision from them.

For the current artifacts, the recommended next smallest useful experiment is:

```text
repair_generic_comparator_protocol
```

This means materializing or adapting the archived Click `G_mini` tasks, or
choosing another generic comparator, so that the same ACUT invocation and scoring
protocol can produce `G_mini -> W_real` and `G_mini + B_real -> W_real`
comparisons. Do not spend on a second ACUT until comparator scoreability is
fixed or explicitly waived.

Acceptance:

- old `repair_source_adapter` text is removed or recast as a resolved blocker;
- source-adapter repair and matrix follow-up are summarized in the evidence;
- final decision does not claim predictive validity;
- next action is concrete and smaller than a new broad experiment.

## Step 4: Optional Status Report

If useful, add a short closeout note:

```text
experiments/phase0_headroom/reports/phase0_closeout.md
```

This file is optional. Use it only if the final decision memo would become too
long with process details.

Suggested contents:

- original blocker;
- follow-up sequence;
- final state;
- why Phase 0 should not continue with more ACUT spend yet.

Acceptance:

- the canonical decision memo remains the source of truth;
- any optional closeout note points back to `phase0_decision_memo.md`.

## Step 5: Commit Hygiene

Actions:

1. Run:

```bash
git status --short --ignored experiments/phase0_headroom docs/experiments .gitignore
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
```

2. Confirm raw artifacts are ignored and unstaged.
3. Stage only docs, small reports, or small metadata files changed by this
   closeout.
4. Commit with a message such as:

```text
Close out phase 0 decision memo
```

Acceptance:

- committed artifacts are small and reviewable;
- no raw ACUT output, transcript, cloned repository, `.venv`, cache, or full
  workspace is staged;
- final status is clean except intentionally ignored artifacts.

## Final Success Criteria

This closeout succeeds when:

- the canonical `phase0_decision_memo.md` reflects the final evidence state;
- the final decision is one of the original Phase 0 allowed decisions;
- the memo explains why Phase 0 does or does not continue;
- the memo names the next smallest useful experiment;
- tests and diff checks pass;
- the closeout is committed separately.

After this closeout, do not return to the earliest Phase 0 runbook for more
experimental work. The original runbook is complete. Future work should start
from the final decision: either repair the generic comparator protocol, plan a
regression-benchmark phase, or draft a new Phase 1 plan.
