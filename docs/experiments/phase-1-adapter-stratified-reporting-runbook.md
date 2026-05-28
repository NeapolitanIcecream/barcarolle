# Phase 1 Adapter-Stratified Reporting Runbook

Status: no-paid implementation runbook, 2026-05-28.

This runbook is for one dedicated Codex CLI session. Its job is to turn the
three-repo paid result diagnostics into a stable reporting rule: adapter
behavior must be visible whenever Barcarolle reports cross-harness paid results.

```text
Add no-paid adapter-stratified reporting for the completed three-repo paid
pilot, codify future reporting rules, and write a bounded decision on whether
the adapter-reporting blocker is cleared.
```

Plain-language summary:

```text
The last diagnostic found that Kilo and Codex behaved differently even though
they used the same model. That means a single pooled score can hide an important
harness effect.

This runbook should make the adapter dimension first-class in reports. It
should not run new paid cells, should not change the completed paid pilot
decision, and should not treat two adapters as interchangeable evidence.
```

## Execution Boundary

This runbook is no-paid. It must not make new LLM or ACUT calls.

Allowed work:

- read committed paid score tables, diagnostics, usage summaries, and metadata;
- define adapter-aware reporting policy and schemas;
- compute adapter-stratified pass, gap, disagreement, latency, and estimated
  cost summaries from existing artifacts;
- write sanitized reports and machine-readable result files;
- update future paid-run reporting guidance so adapter-specific evidence is
  shown before any pooled headline.

Disallowed work:

- running any new paid ACUT solver cell;
- changing the frozen three-repo paid pilot task list, split assignment, or
  terminal outcomes;
- changing the completed paid decision label;
- promoting a post-hoc diagnostic metric to the primary result for the
  completed paid pilot;
- changing Task Generator behavior in this runbook;
- redesigning the split algorithm in this runbook;
- committing raw prompts, completions, ACUT transcripts, solver workspaces,
  verifier workspaces, raw diffs, raw test patches, target repository clones,
  secrets, `.venv`, caches, or large raw outputs;
- drafting or creating the next runbook.

If the worker discovers that adapter reporting cannot be completed without new
paid calls, stop and write a blocker. Do not make those calls.

## Starting Point

The paid result diagnostic ended with:

```text
primary decision: three_repo_paid_diagnostics_adapter_stratification_needed
new paid cells run by diagnostic: 0
completed paid decision changed: false
predictive validity established: false
recommended next action: stratify_or_separate_adapter_reporting
secondary actions: harden_task_generator_or_source_context,
                   redesign_split_with_block_randomization
```

The main evidence:

```text
codex_workspace pass rate: 22/60 = 0.3667
kilo_workspace pass rate:  32/60 = 0.5333
kilo minus codex:          0.1666
adapter disagreements:     22/60 = 0.3667
paired outcomes:
  both_fail:       22
  both_pass:       16
  codex_only_pass:  6
  kilo_only_pass:  16
```

Cost evidence from observed token estimates:

```text
codex_workspace: 60 cells, USD 32.22309, USD 0.53705/cell
kilo_workspace:  60 cells, USD 19.044243, USD 0.31740/cell
actual provider billed cost: unavailable
```

The previous paid pilot result remains pilot evidence only. This runbook must
not claim precision-target predictive validity.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-adapter-stratified-reporting-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md first. Use uv for
repo-local Python tooling. Follow AGENTS.md step-level acceptance and commit
requirements: after each step, or after each small group of tightly related
steps, commit the changed files with an appropriately scoped commit.

This runbook is no-paid. Do not make new LLM or ACUT calls. Do not change the
completed three-repo paid pilot decision, task list, split assignment, primary
design, thresholds, or terminal outcomes.

Main goal: make adapter-stratified reporting first-class. The completed
three-repo paid pilot may keep its original primary decision, but future reports
must not hide Codex/Kilo differences behind a single pooled adapter headline.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. What action it suggests next.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
Codex/Kilo logs, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, raw target diffs, raw test patches, raw GitHub API
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
docs/experiments/phase-1-three-repo-paid-validation-runbook.md
docs/experiments/phase-1-three-repo-paid-result-diagnostics-runbook.md

experiments/phase1_compiler/results/phase1_three_repo_paid_validation_metrics.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_decision.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_score_tables_manifest.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_cost_reconciliation.json

experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_result_cube.json
experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_adapter_effects.json
experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_uncertainty.json
experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_split_balance.json
experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_action_matrix.json
experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_decision.json

experiments/phase0_headroom/results/phase1_three_repo_paid_validation_*_score_table.csv
experiments/phase0_headroom/results/phase1_three_repo_paid_validation_*_cost_summary.json
experiments/phase0_headroom/results/workspace_usage_ledger.jsonl
experiments/phase0_headroom/configs/model_pricing.yaml
```

Do not require ignored raw artifacts for this runbook.

## Reporting Rules To Codify

The worker should turn these rules into committed config/report artifacts:

1. A cross-harness paid run must report adapter-level results before pooled
   adapter summaries.
2. A pooled adapter result may be shown only as a diagnostic or preregistered
   aggregate, and must not be the only headline.
3. For each adapter, report:
   - cell count;
   - scoreable count;
   - pass rate;
   - per-repo and per-split pass rates;
   - B_eval/H_future gap where applicable;
   - policy violations;
   - observed token estimated cost;
   - cost per cell;
   - usage observed rate;
   - median latency.
4. For paired cross-harness tasks, report:
   - both pass;
   - both fail;
   - adapter A only pass;
   - adapter B only pass;
   - disagreement rate.
5. If adapters differ materially, future paid runbooks must either:
   - choose one ACUT/adapter as the scoreable target before outcomes; or
   - preregister adapter as a blocking/reporting factor; or
   - report each adapter as a separate ACUT result, with pooled summaries
     clearly marked as secondary.
6. Estimated cost must say whether it is token-estimated or provider-billed.
   If `actual_provider_billed_cost_usd` is null, do not call it exact bill.
7. Existing paid pilot conclusions must keep their historical claim boundary:
   pilot evidence only, predictive validity not established.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_adapter_stratified_reporting.yaml
  tools/
    phase1_adapter_stratified_reporting.py
  tests/
    test_phase1_adapter_stratified_reporting.py
  results/
    phase1_adapter_stratified_reporting_preflight.json
    phase1_adapter_stratified_reporting_policy.json
    phase1_adapter_stratified_reporting_three_repo_summary.json
    phase1_adapter_stratified_reporting_three_repo_summary.csv
    phase1_adapter_stratified_reporting_pairwise_summary.json
    phase1_adapter_stratified_reporting_cost_latency_summary.json
    phase1_adapter_stratified_reporting_future_gates.json
    phase1_adapter_stratified_reporting_decision.json
  reports/
    phase1_adapter_stratified_reporting_process.md
    phase1_adapter_stratified_reporting_preflight.md
    phase1_adapter_stratified_reporting_policy.md
    phase1_adapter_stratified_reporting_three_repo_summary.md
    phase1_adapter_stratified_reporting_cost_latency_summary.md
    phase1_adapter_stratified_reporting_future_gates.md
    phase1_adapter_stratified_reporting_decision.md
```

If an artifact already exists under a better established local name, reuse that
name and explain the mapping in the process report.

## Step 0 - Preflight And No-Paid Boundary

Goal: prove this run starts from committed diagnostics and will not spend money.

Actions:

1. Read `AGENTS.md`, this runbook, and the diagnostics decision.
2. Record branch, HEAD, date, Python version, and `uv --version`.
3. Record `git status --short --branch` and `git diff --check`.
4. Confirm the diagnostics primary decision is
   `three_repo_paid_diagnostics_adapter_stratification_needed`.
5. Confirm new paid LLM/ACUT calls are disallowed.
6. Confirm the completed paid decision will not be changed.
7. Classify dirty/untracked paths as relevant, ignored raw/runtime, or
   unrelated.

Expected outputs:

```text
phase1_adapter_stratified_reporting_preflight.json
phase1_adapter_stratified_reporting_preflight.md
phase1_adapter_stratified_reporting_process.md
```

Acceptance:

- The diagnostic decision is available and points to adapter stratification.
- No new paid calls are planned or made.
- Dirty/untracked files are classified.
- The report states that this work does not change the completed paid pilot.

Commit:

```text
Record adapter stratified reporting preflight
```

## Step 1 - Reporting Policy And Schema

Goal: define what adapter-aware reporting means before generating summaries.

Actions:

1. Add a config file for adapter-stratified reporting.
2. Encode:
   - required adapter-level metrics;
   - required paired-task metrics;
   - required cost/latency fields;
   - claim-boundary language for pooled summaries;
   - provider-bill vs token-estimate cost language;
   - future paid gate requirements.
3. Add focused tests for config loading and policy validation.
4. Keep policy generic enough for future cross-harness paid runs, not just this
   three-repo pilot.

Expected outputs:

```text
phase1_adapter_stratified_reporting.yaml
phase1_adapter_stratified_reporting_policy.json
phase1_adapter_stratified_reporting_policy.md
```

Acceptance:

- Policy requires adapter-level reporting before pooled reporting.
- Policy prevents a single pooled adapter headline from being the only
  cross-harness result.
- Policy states that estimated token cost is not provider-billed cost.
- Focused tests pass.

Commit:

```text
Define adapter stratified reporting policy
```

## Step 2 - Adapter Summary Tooling

Goal: compute reusable adapter-aware summaries from existing sanitized results.

Actions:

1. Add or update a small tool that reads the diagnostics result cube and paid
   cost summaries.
2. Compute, for each adapter:
   - total cells;
   - scoreable cells;
   - pass rate;
   - pass rate by repo;
   - pass rate by split;
   - pass rate by repo and split;
   - B_eval/H_future gap by repo and pooled;
   - policy violation count;
   - non-scoreable count;
   - estimated token cost;
   - conservative cost;
   - provider-billed cost if available;
   - cost per cell;
   - median latency.
3. Compute paired task outcomes:
   - both pass;
   - both fail;
   - per-adapter-only pass counts;
   - disagreement rate;
   - paired sign-test or a simple exact count summary.
4. The tool should avoid raw artifacts and use committed score/cost files only.

Expected outputs:

```text
phase1_adapter_stratified_reporting_three_repo_summary.json
phase1_adapter_stratified_reporting_three_repo_summary.csv
phase1_adapter_stratified_reporting_pairwise_summary.json
phase1_adapter_stratified_reporting_cost_latency_summary.json
```

Acceptance:

- The adapter pass rates reproduce Codex `22/60` and Kilo `32/60`.
- The paired disagreement counts reproduce both_fail `22`, both_pass `16`,
  codex_only_pass `6`, and kilo_only_pass `16`.
- The cost summary reproduces the observed token estimates for Codex and Kilo.
- Tests cover the summary calculations.

Commit:

```text
Add adapter stratified reporting summaries
```

## Step 3 - Three-Repo Reporting Supplement

Goal: write the human-readable supplement for the completed paid pilot.

Actions:

1. Write a short report that explains:
   - what the original paid pilot concluded;
   - why the adapter supplement is needed;
   - Codex vs Kilo pass rates;
   - paired disagreement;
   - per-repo/per-split adapter gaps;
   - token-estimated cost and latency differences;
   - why provider-billed exact cost remains unavailable.
2. State plainly that the completed paid decision is unchanged.
3. Mark pooled adapter summaries as retrospective diagnostic evidence only.
4. Do not claim predictive validity.

Expected outputs:

```text
phase1_adapter_stratified_reporting_three_repo_summary.md
phase1_adapter_stratified_reporting_cost_latency_summary.md
```

Acceptance:

- The report is understandable without reading raw JSON.
- The report separates score, cost, and latency.
- The report states the difference between token-estimated cost and provider
  bill.
- The report does not rewrite the completed paid pilot result.

Commit:

```text
Report adapter stratified three-repo pilot summary
```

## Step 4 - Future Paid Gate Updates

Goal: make sure the next paid run cannot repeat the same reporting ambiguity.

Actions:

1. Write future gates for paid validation runbooks:
   - adapter reporting policy loaded;
   - adapter-level result table required;
   - paired-disagreement table required for shared tasks;
   - cost estimate/bill status required;
   - pooled adapter headline must be marked primary only if preregistered;
   - otherwise pooled headline is secondary/diagnostic.
2. Identify which existing future runbooks or templates should reference these
   gates. Prefer a small report over broad doc churn unless a direct reference
   is necessary.
3. If updating the next paid-validation runbook template is clearly local and
   safe, do so. If not, record the required future update in the gate report.
4. Do not create a precision paid runbook.

Expected outputs:

```text
phase1_adapter_stratified_reporting_future_gates.json
phase1_adapter_stratified_reporting_future_gates.md
```

Acceptance:

- Future paid runs have explicit adapter-reporting gates.
- The gates distinguish single-ACUT evaluation from cross-harness comparison.
- The gates say when pooled adapter reporting is allowed.
- No future runbook is drafted.

Commit:

```text
Codify future adapter reporting gates
```

## Step 5 - Decision And Closeout

Goal: decide whether the adapter-reporting blocker is cleared.

Actions:

1. Write final decision artifacts.
2. Answer these research questions:

```text
RQ1: Did this run make any new paid calls?
RQ2: Does the adapter-stratified summary reproduce the diagnostics numbers?
RQ3: Are adapter-level score, cost, and latency now reportable from committed artifacts?
RQ4: Does the reporting policy prevent a pooled-only cross-harness headline?
RQ5: What still blocks a precision-target paid replication?
RQ6: What is the recommended next action category?
```

3. Choose exactly one primary decision label:

```text
adapter_reporting_policy_ready
adapter_reporting_policy_ready_but_source_context_next
adapter_reporting_policy_ready_but_split_redesign_next
adapter_reporting_policy_blocked_missing_artifacts
adapter_reporting_policy_blocked_metric_mismatch
```

4. Secondary labels may be recorded for source-context hardening and split
   redesign, but the primary label should say whether adapter reporting itself
   is ready.
5. Record completed steps, commits made during the run, tests run, and known
   blockers.
6. Do not draft or create the next runbook.

Expected outputs:

```text
phase1_adapter_stratified_reporting_decision.json
phase1_adapter_stratified_reporting_decision.md
```

Acceptance:

- The decision states that no new paid cells ran.
- The decision states whether adapter reporting is ready for future paid runs.
- The decision does not claim precision-target predictive validity.
- The decision explains the next action in simple language.

Commit:

```text
Close adapter stratified reporting run
```

## Verification

At minimum, run:

```bash
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_adapter_stratified_reporting.py -q
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_three_repo_paid_result_diagnostics.py -q
git diff --check
git status --short --untracked-files=all
```

If the full Phase 1 compiler test suite is feasible, also run:

```bash
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q
```

If a verification command is too slow or blocked, record the exact reason in
the decision report.

## Final Reporting Template

The final worker summary should be short and in simple Chinese:

```text
这次 runbook 是 adapter-stratified reporting，没有跑新的 paid cells。

结果：
- adapter reporting policy ready: yes/no
- paid calls made: 0
- completed paid pilot decision changed: yes/no
- Codex pass/cost summary: X
- Kilo pass/cost summary: X
- paired disagreement summary: X
- provider-billed exact cost available: yes/no
- primary decision label: X
- recommended next action category: X

解释：
- 以后不能只用一个 pooled adapter headline 汇报 cross-harness paid run。
- 上一轮 paid pilot 结论没有被改写。
- 没有提交 raw logs、raw prompts、raw completions、solver workspaces、verifier
  workspaces 或 secrets。
```
