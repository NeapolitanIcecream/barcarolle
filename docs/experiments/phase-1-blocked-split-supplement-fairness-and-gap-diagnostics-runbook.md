# Phase 1 Blocked Split Supplement Fairness And Gap Diagnostics Runbook

Status: no-paid diagnostics runbook, 2026-05-29.

This runbook is for one dedicated Codex CLI session. Its job is to diagnose the
completed blocked split missing-cell supplement without running new paid cells.

```text
Check that Codex/Kilo calls were made through the intended endpoint and under
fair-enough benchmark conditions, then analyze repo-level B_eval/H_future gaps,
adapter disagreement, and the one invalid_output cell.
```

Plain-language summary:

```text
The last run finished the 72 reused + 48 newly paid cell table. The result is
usable exploratory evidence, but it raised a few small follow-up questions.

The adapter difference itself is not automatically a problem. It may simply
mean Kilo + gpt-5.4-mini is stronger than Codex + gpt-5.4-mini under the
current ACUT setup. This runbook should only treat the adapter difference as a
problem if the calls, task inputs, workspace setup, verifier setup, or accounting
were unfair or wrong.

At the same time, this runbook should do the practical analysis we still need:
which repos drive the B_eval/H_future gaps, where Codex and Kilo disagree, and
whether the attrs invalid_output points to an adapter bug, task issue, or import
classification issue.
```

## Execution Boundary

This runbook is no-paid. It must not make new paid LLM or ACUT solver calls.

Allowed work:

- read committed score tables, metrics, manifests, cost summaries, batch status,
  usage ledger entries, adapter configs, and sanitized reports;
- audit endpoint/model/config evidence from committed artifacts and sanitized
  usage records;
- compare solver-visible task inputs, split labels, base commits, path policies,
  verifier setup, timeout/accounting policy, and score-table import policy for
  `codex_workspace` and `kilo_workspace`;
- compute repo-level B_eval/H_future pass rates and gaps by adapter;
- compute repo-level Codex/Kilo disagreement and pass-rate deltas;
- compare new blocked split diagnostics with the previous three-repo paid split
  where the committed artifacts support that comparison;
- classify the single `invalid_output` cell and decide whether it points to an
  adapter bug, task statement issue, verifier/import bug, or acceptable
  non-scoreable ACUT output;
- write small sanitized configs, tools, tests, JSON/CSV outputs, reports, and a
  decision.

Disallowed work:

- running new paid ACUT cells;
- rerunning failed, invalid, or disagreeing cells;
- changing any paid terminal outcome, score table, selected task ID, split
  assignment, source eligibility, task statement, or completed decision;
- changing Codex/Kilo adapter behavior in this runbook;
- treating Kilo/Codex pass-rate difference as a blocker merely because the
  results differ;
- claiming model-only superiority unless adapter/harness/tooling differences
  have been ruled out;
- claiming formal preregistration or predictive validity from the supplement;
- committing raw prompts, raw completions, raw ACUT transcripts, solver
  workspaces, verifier workspaces, raw diffs, raw test patches, target
  repository clones, raw public API responses, secrets, `.venv`, caches, or
  large raw outputs;
- drafting or creating the next runbook.

If exact evidence is missing because raw artifacts are intentionally ignored,
record the missing evidence as a limitation. Do not recover it by reading or
committing raw sensitive artifacts unless the existing repo policy already
allows a sanitized digest.

## Starting Point

The blocked split supplement ended with:

```text
decision_label: blocked_split_missing_cell_supplement_completed_with_non_scoreable_cells
planned new cells: 48
completed new cells: 48
reused cells: 72
combined selected cells: 120 / 120
scoreable cells: 119
scoreability rate: 0.9917
policy violations: 0
raw oracle exposure: false
endpoint compliance: pass
new token-estimated cost: USD 26.3480964
exact provider bill: unavailable
predictive validity established: false
```

Adapter-level results:

```text
codex_workspace:
  cells: 60
  scoreable: 59
  pass rate: 0.2881
  B_eval pass rate: 0.3448
  H_future pass rate: 0.2333
  gap: 0.1115

kilo_workspace:
  cells: 60
  scoreable: 60
  pass rate: 0.5833
  B_eval pass rate: 0.6333
  H_future pass rate: 0.5333
  gap: 0.1000
```

Known repo-level gaps from the supplement:

```text
codex_workspace:
  attrs gap:   0.1444
  boltons gap: 0.1000
  click gap:   0.3000

kilo_workspace:
  attrs gap:   0.0000
  boltons gap: 0.2000
  click gap:   0.1000
```

Paired adapter disagreement:

```text
paired task count: 59
disagreement rate: 0.4068
both_fail: 21
both_pass: 14
codex_only_pass: 3
kilo_only_pass: 21
```

The only non-scoreable cell:

```text
adapter: codex_workspace
task_id: attrs__v2__157
split: B_eval
terminal_status: invalid_output
scoreable_cell: false
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-blocked-split-supplement-fairness-and-gap-diagnostics-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md first. Use uv for
repo-local Python tooling. Follow AGENTS.md step-level acceptance and commit
requirements: after each step, or after each small group of tightly related
steps, commit the changed files with an appropriately scoped commit.

This runbook is no-paid. Do not make paid LLM calls or paid ACUT solver calls.
Do not rerun cells. Do not change paid outcomes, score tables, selected task
IDs, split labels, source eligibility, task statements, or completed decisions.

Main goal: decide whether the completed supplement is fair-enough to interpret,
then explain what the repo-level gaps and Codex/Kilo disagreements mean. Adapter
difference is not a blocker by itself. Treat it as a valid ACUT configuration
difference if endpoint, model, task input, workspace, verifier, policy, and
accounting evidence are clean enough.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. What action it suggests next.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
Codex/Kilo logs, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, raw target diffs, raw test patches, raw public API
responses, or large raw outputs. Commit only small sanitized configs, tools,
tests, tables, reports, manifests, digests, and decision files.

Do not draft or create the next runbook. Record recommended next action
categories only.
```

## Required Inputs

Use these committed inputs:

```text
AGENTS.md
docs/architecture/system-design.md
docs/experiments/phase-1-blocked-split-missing-cell-supplement-paid-execution-runbook.md
docs/experiments/phase-1-adapter-stratified-reporting-runbook.md
docs/experiments/phase-1-three-repo-paid-validation-runbook.md

experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_decision.json
experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_adapter_stratified_metrics.json
experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_combined_score_tables_manifest.json
experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_cost_reconciliation.json
experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_batch_plan.json
experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_reuse_manifest.json
experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_ready_package_integrity.json
experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_batch_1_smoke.json
experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_batch_2_attrs_remainder.json
experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_batch_3_boltons_remainder.json
experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_batch_4_click_remainder.json

experiments/phase1_compiler/results/phase1_three_repo_paid_validation_decision.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_metrics.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_score_tables_manifest.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_cost_reconciliation.json

experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_decision.json
experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_three_repo_summary.json
experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_cost_latency_summary.json

experiments/phase0_headroom/results/phase1_blocked_split_missing_cell_supplement_paid_execution_*_score_table.csv
experiments/phase0_headroom/results/phase1_blocked_split_missing_cell_supplement_paid_execution_*_cost_summary.json
experiments/phase0_headroom/results/phase1_three_repo_paid_validation_*_score_table.csv
experiments/phase0_headroom/results/phase1_three_repo_paid_validation_*_cost_summary.json
experiments/phase0_headroom/results/workspace_usage_ledger.jsonl
experiments/phase0_headroom/results/workspace_cost_reconciliation.json
experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
experiments/phase0_headroom/configs/model_pricing.yaml
```

Do not require ignored raw artifacts for this runbook. If raw artifacts would
be needed to answer a question exactly, write a sanitized limitation and a
future action category instead.

## Diagnostic Policy

The worker should codify this policy in the outputs:

1. Adapter difference is expected benchmark evidence, not automatically a bug.
2. The required fairness question is whether the two ACUT configurations were
   called correctly and tested under comparable benchmark rules.
3. If endpoint/model/task/workspace/verifier/accounting checks pass, report the
   Kilo/Codex gap as an ACUT configuration difference.
4. If any check fails, classify whether it threatens:
   - all supplement conclusions;
   - only adapter comparison;
   - only a repo-specific slice;
   - only cost/latency interpretation.
5. Do not collapse Codex and Kilo into a model-only conclusion unless adapter
   and harness differences are explicitly out of scope and named.
6. Repo-level gaps should guide next local analysis, not trigger paid reruns by
   default.
7. The single invalid_output should be triaged, but one non-scoreable cell with
   combined scoreability 0.9917 is not automatically a paid-run blocker.
8. The click title-only minor risk remains visible in any interpretation that
   uses click repo results.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_blocked_split_supplement_fairness_gap_diagnostics.yaml
  tools/
    phase1_blocked_split_supplement_fairness_gap_diagnostics.py
  tests/
    test_phase1_blocked_split_supplement_fairness_gap_diagnostics.py
  results/
    phase1_blocked_split_supplement_fairness_gap_diagnostics_preflight.json
    phase1_blocked_split_supplement_fairness_gap_diagnostics_adapter_fairness_audit.json
    phase1_blocked_split_supplement_fairness_gap_diagnostics_repo_gap_matrix.json
    phase1_blocked_split_supplement_fairness_gap_diagnostics_adapter_disagreement_by_repo.json
    phase1_blocked_split_supplement_fairness_gap_diagnostics_invalid_output_triage.json
    phase1_blocked_split_supplement_fairness_gap_diagnostics_previous_split_comparison.json
    phase1_blocked_split_supplement_fairness_gap_diagnostics_action_matrix.json
    phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.json
  reports/
    phase1_blocked_split_supplement_fairness_gap_diagnostics_process.md
    phase1_blocked_split_supplement_fairness_gap_diagnostics_adapter_fairness_audit.md
    phase1_blocked_split_supplement_fairness_gap_diagnostics_repo_gap_matrix.md
    phase1_blocked_split_supplement_fairness_gap_diagnostics_adapter_disagreement_by_repo.md
    phase1_blocked_split_supplement_fairness_gap_diagnostics_invalid_output_triage.md
    phase1_blocked_split_supplement_fairness_gap_diagnostics_previous_split_comparison.md
    phase1_blocked_split_supplement_fairness_gap_diagnostics_action_matrix.md
    phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md
```

Optional small CSV outputs may be added if useful:

```text
experiments/phase1_compiler/results/phase1_blocked_split_supplement_fairness_gap_diagnostics_*.csv
```

## Step 0 - Preflight And Scope Check

Goal: prove this is a no-paid diagnostic over completed committed artifacts.

Actions:

1. Read `AGENTS.md`, this runbook, and the required input artifacts.
2. Record branch, HEAD, date, Python version, and `uv --version`.
3. Record `git status --short --untracked-files=all` and `git diff --check`.
4. Classify dirty/untracked files. The known external-review bundle may remain
   untracked unless the user explicitly asks to package or remove it.
5. Confirm no paid calls are needed.
6. Confirm the supplement decision is
   `blocked_split_missing_cell_supplement_completed_with_non_scoreable_cells`.
7. Write preflight result and process report.

Acceptance:

- Preflight records branch, HEAD, dirty-tree classification, no-paid boundary,
  and required input availability.
- No paid calls have run.
- Completed supplement artifacts are present and unchanged.
- The report states that adapter difference is not automatically a blocker.

Suggested commit:

```text
Record blocked split supplement diagnostics preflight
```

## Step 1 - Adapter Fairness And Endpoint Audit

Goal: decide whether Codex/Kilo differences can be interpreted as ACUT
configuration differences rather than benchmark setup mistakes.

Actions:

1. Audit both adapters for:
   - required endpoint variables;
   - model identifier or configured model family, where recorded;
   - pricing/accounting source;
   - solver-visible task statement source;
   - base commit and workspace construction policy;
   - allowed edit paths and prohibited test/oracle paths;
   - verifier replay policy;
   - hidden oracle injection only in verifier workspace;
   - timeout/concurrency/retry policy;
   - score-table import rules;
   - usage/cost record completeness.
2. For each dimension, classify:
   - `clean`;
   - `documented_acut_difference`;
   - `missing_evidence`;
   - `fairness_risk`;
   - `benchmark_blocker`.
3. If raw artifacts would be required to prove a point, do not read or commit
   them. Record a limitation and whether it affects interpretation.
4. Write a fairness conclusion:
   - `fair_enough_to_interpret_as_acut_difference`;
   - `adapter_comparison_limited_but_score_tables_usable`;
   - `adapter_comparison_blocked`;
   - `supplement_interpretation_blocked`.

Expected outputs:

```text
phase1_blocked_split_supplement_fairness_gap_diagnostics_adapter_fairness_audit.json
phase1_blocked_split_supplement_fairness_gap_diagnostics_adapter_fairness_audit.md
```

Acceptance:

- Endpoint evidence is explicitly checked.
- Model/config evidence is explicitly checked or marked as missing.
- Differences in harness/tooling are treated as ACUT configuration details, not
  hidden errors, unless a benchmark rule was violated.
- The conclusion says whether adapter differences can be reported.

Suggested commit:

```text
Audit blocked split supplement adapter fairness
```

## Step 2 - Repo-Level Gap Matrix

Goal: show which repos drive B_eval/H_future gaps.

Actions:

1. Build a matrix by:
   - adapter;
   - repo;
   - split;
   - reused vs newly paid origin;
   - terminal status;
   - scoreability.
2. Compute for each adapter/repo:
   - B_eval cell count;
   - H_future cell count;
   - scoreable counts;
   - verified pass/fail counts;
   - pass rates;
   - absolute B_eval/H_future gap;
   - non-scoreable count and status.
3. Compute repo-level pooled secondary diagnostics after adapter-level metrics.
4. Flag gap drivers using simple labels, for example:
   - `low_gap`;
   - `moderate_gap`;
   - `high_gap`;
   - `non_scoreable_sensitive`;
   - `click_source_caveat_applies`.
5. Do not change any outcome or denominator after seeing the matrix.

Expected outputs:

```text
phase1_blocked_split_supplement_fairness_gap_diagnostics_repo_gap_matrix.json
phase1_blocked_split_supplement_fairness_gap_diagnostics_repo_gap_matrix.md
```

Acceptance:

- Repo-level results are shown separately for Codex and Kilo.
- Pooled repo summaries are secondary.
- The report explains in simple language which repos are driving the gap:
  Codex click, Kilo boltons, Codex attrs/non-scoreable sensitivity, or another
  observed driver.
- Click title-only source caveat is visible where click is interpreted.

Suggested commit:

```text
Compute blocked split supplement repo gap matrix
```

## Step 3 - Adapter Disagreement By Repo

Goal: explain where Codex and Kilo differ most without treating difference as
wrong by default.

Actions:

1. Pair scoreable task outcomes by task ID and repo.
2. Exclude or explicitly label the non-scoreable Codex `attrs__v2__157` cell so
   denominators are clear.
3. Compute by repo:
   - paired task count;
   - both pass;
   - both fail;
   - Codex-only pass;
   - Kilo-only pass;
   - disagreement rate;
   - Kilo minus Codex pass-rate delta.
4. Compute the same disagreement by split where useful.
5. Identify whether disagreement is broad across repos or concentrated.
6. State that a higher Kilo pass rate is a valid ACUT result if Step 1 fairness
   is clean enough.

Expected outputs:

```text
phase1_blocked_split_supplement_fairness_gap_diagnostics_adapter_disagreement_by_repo.json
phase1_blocked_split_supplement_fairness_gap_diagnostics_adapter_disagreement_by_repo.md
```

Acceptance:

- Overall disagreement rate is reconciled with the known `0.4068`.
- Repo-level disagreement is reported.
- Kilo/Codex difference is not mislabeled as a model-only effect.
- Any missing or non-scoreable pair is accounted for.

Suggested commit:

```text
Compute blocked split supplement adapter disagreement
```

## Step 4 - Invalid Output Triage

Goal: decide what the single non-scoreable cell means.

Actions:

1. Locate the sanitized score-table row for:

```text
adapter: codex_workspace
task_id: attrs__v2__157
split: B_eval
terminal_status: invalid_output
```

2. Inspect committed sanitized fields only. Do not commit raw solver output or
   raw transcript.
3. Classify the likely cause:
   - `adapter_output_contract_violation`;
   - `solver_no_diff_or_unparseable_diff`;
   - `verifier_import_or_score_table_bug`;
   - `task_statement_or_workspace_issue`;
   - `insufficient_sanitized_evidence`.
4. Check whether Kilo completed the same task and what its outcome was.
5. Check whether other Codex cells had similar near-fail or invalid patterns,
   using committed sanitized data only.
6. Decide whether this should trigger:
   - no action beyond reporting;
   - no-paid adapter import hardening;
   - no-paid sanitized logging improvement;
   - future rerun only if a concrete benchmark bug is found.

Expected outputs:

```text
phase1_blocked_split_supplement_fairness_gap_diagnostics_invalid_output_triage.json
phase1_blocked_split_supplement_fairness_gap_diagnostics_invalid_output_triage.md
```

Acceptance:

- The invalid cell is traced to a specific committed score table.
- The report says whether it threatens the supplement conclusion.
- The report does not rerun the cell.
- Any recommended action is no-paid unless a concrete bug justifies a future
  paid rerun proposal.

Suggested commit:

```text
Triage blocked split supplement invalid output
```

## Step 5 - Previous Split Comparison

Goal: compare the new blocked split supplement against the previous paid split
without overstating the claim.

Actions:

1. Use committed old paid-validation and adapter-reporting artifacts.
2. Compare, where available:
   - scoreability;
   - policy violations;
   - adapter pass rates;
   - adapter B_eval/H_future gaps;
   - repo-level gaps;
   - pooled secondary gap;
   - adapter disagreement.
3. Distinguish:
   - old paid split;
   - new blocked split supplement;
   - reused cells;
   - newly paid supplement cells.
4. State whether the blocked split looks:
   - cleaner;
   - about the same;
   - worse;
   - inconclusive.
5. Keep the claim boundary exploratory.

Expected outputs:

```text
phase1_blocked_split_supplement_fairness_gap_diagnostics_previous_split_comparison.json
phase1_blocked_split_supplement_fairness_gap_diagnostics_previous_split_comparison.md
```

Acceptance:

- The comparison includes the known pooled gap comparison:
  old `0.1000` vs supplement `0.1079`.
- The report does not claim the new split is better if the evidence says it is
  only similar or slightly worse.
- The report explains why this comparison is diagnostic, not formal validation.

Suggested commit:

```text
Compare blocked split supplement with previous split
```

## Step 6 - Action Matrix And Decision

Goal: turn the diagnostics into a next-action recommendation.

Actions:

1. Build an action matrix with at least these possible actions:
   - `accept_adapter_difference_as_acut_result`;
   - `fix_adapter_endpoint_or_model_config`;
   - `improve_sanitized_invalid_output_logging`;
   - `investigate_codex_attrs_invalid_output_contract`;
   - `repo_level_gap_deep_dive_no_paid`;
   - `proceed_to_next_repo_or_supply_expansion`;
   - `do_not_run_more_paid_cells_yet`;
   - `paid_rerun_only_if_benchmark_bug_confirmed`.
2. Assign each action:
   - recommendation status;
   - evidence;
   - cost;
   - whether it is blocking.
3. Write a final decision.

Decision labels:

```text
supplement_fair_enough_repo_gap_diagnostics_complete
supplement_fair_enough_with_minor_logging_action
adapter_comparison_limited_but_supplement_usable
adapter_fairness_blocker_found
supplement_diagnostics_blocked
```

Expected outputs:

```text
phase1_blocked_split_supplement_fairness_gap_diagnostics_action_matrix.json
phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.json
phase1_blocked_split_supplement_fairness_gap_diagnostics_action_matrix.md
phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md
```

Acceptance:

- The decision says whether adapter difference is acceptable as ACUT evidence.
- The decision says which repo-level gaps matter most.
- The decision says what to do about `invalid_output`.
- The decision says whether more paid cells are recommended now.
- The decision keeps predictive validity false.
- The worker does not draft the next runbook.

Suggested commit:

```text
Close blocked split supplement diagnostics
```

## Verification

At minimum, run:

```bash
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_blocked_split_supplement_fairness_gap_diagnostics.py -q
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q
git diff --check
git status --short --untracked-files=all
```

If the full test suite is too slow or blocked, run focused tests plus the
nearest related tests and record the reason.

## Final Reporting Template

The final worker summary should be short and in simple Chinese:

```text
这次 runbook 没有跑新的 paid cells，只分析已有结果。

结果：
- adapter fairness: pass/limited/blocker
- endpoint/model/config evidence: clean/missing/risk
- adapter difference 是否可作为 ACUT 差异解释：yes/no/limited
- repo-level gap 最大的地方：...
- Codex/Kilo disagreement 主要集中在：...
- invalid_output 原因：...
- 是否影响 supplement 结论：yes/no/limited
- 是否建议现在继续 paid run：yes/no

解释：
- 如果公平性检查干净，Kilo 明显强于 Codex 可以被报告为 ACUT 配置差异。
- repo-level gap 用来指导后续 no-paid 分析或选仓，不自动触发 paid rerun。
- 这仍然是 Phase 1 exploratory evidence，不是正式 predictive validity。

没有提交 raw logs、raw prompts、raw completions、solver workspaces、verifier
workspaces 或 secrets。
```
