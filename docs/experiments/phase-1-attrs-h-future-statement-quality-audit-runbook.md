# Phase 1 Attrs H_future Statement-Quality Audit Runbook

Status: implementation runbook, 2026-05-25.

This runbook is for one dedicated Codex CLI session. Its job is to test the
strongest task-design confound found after the `attrs` H_future collapse:
solver-visible statements for the four `attrs` H_future tasks appear to be
truncated or under-specified.

The goal is not to rescue the current paid result. The goal is to decide how
much of the `attrs` H_future failure should be treated as benchmark/compiler
evidence, and how much should be treated as statement-quality confounding before
spending on more validation.

## Starting Point

Current committed Phase 1 evidence:

```text
two-repo pilot:
  repos: boltons, attrs
  B_eval scoreable cells: 16
  H_future scoreable cells: 15
  policy violations: 1
  predictive_validity_established: false
  decision: report_two_repo_negative_or_underpowered_pilot

attrs asymmetry:
  B_eval: 7/8 scoreable pass
  H_future: 1/7 scoreable pass
  H_future policy violations: 1
```

Manual audit before this runbook found these task-design risks:

```text
attrs__hist__012:
  source: issue:680
  outcome: codex fail, kilo fail
  audit signal: probably valid, but target patch is moderately large and
    Problem details appear truncated mid reproduction.

attrs__hist__013:
  source: pr:687
  outcome: codex fail, kilo fail
  audit signal: highest concern; PR-context source, subtle next-gen frozen
    subclass behavior, and Problem details appear truncated mid sentence.

attrs__hist__023:
  source: issue:593
  outcome: codex fail, kilo pass
  audit signal: probably valid, but generated-init/type-hints behavior is
    subtle and Problem details appear truncated in the expected result.

attrs__hist__027:
  source: issue:766
  outcome: codex fail, kilo policy_violation
  audit signal: target patch is small and scope metadata matches the target
    commit, but the statement may under-specify the needed
    resolve_types(..., attribs=...) API behavior.
```

The research proposal in `barcarolle-research-0519.md`
sets the governing direction:

```text
Barcarolle is a repo-specific benchmark compiler. Its central question is
whether the compiled benchmark predicts held-out future target-repo work.
Task production is not the main contribution; task selection, calibration,
quality control, and predictive validity are.
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing <repo>/docs/experiments/phase-1-attrs-h-future-statement-quality-audit-runbook.md.

Work in <repo>. Use uv for repo-local Python tooling.
Make a cohesive git commit after every completed step that changes files. Do
not batch unrelated steps into one commit. If a step has no file changes, record
that fact in the process report and do not create an empty commit. Do not push
unless the user explicitly asks.

Main goal: audit whether the attrs H_future collapse is confounded by task
statement quality, quantify the sensitivity of the two-repo conclusion to that
confound, and harden future statement generation/checking locally. Keep the
current paid outcomes immutable: do not rewrite, rescore, rerun, or relabel
existing paid cells except by adding explicit sidecar audit/sensitivity
artifacts.

Do not run paid ACUT cells or paid LLM calls. Do not rerun existing scoreable
cells. Do not rerun the confirmed attrs__hist__027 policy violation. Do not
modify Codex, Kilo, or any ACUT internals. If future paid validation appears
necessary, stop after writing a precise next-runbook recommendation.

Keep Barcarolle on the benchmark/compiler side of the ACUT boundary. Barcarolle
may inspect sanitized score artifacts, public source-context metadata, certified
task metadata, local target-repo history, statement files, package manifests,
and local certification records. Barcarolle must not use hidden verifier
material to tune task statements or weaken scope policy.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
GitHub API responses, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, raw patch bodies, full public issue/PR bodies, or
large raw outputs. Commit only small sanitized configs, tools, tests, manifests,
sidecar audits, summaries, reports, digests, and short excerpts.

The final user-facing summary should be simple Chinese: say clearly whether the
attrs H_future evidence still looks clean, partly confounded, or unusable as a
clean holdout signal.
```

## Claim Boundary

Allowed claims:

```text
attrs_h_future_statement_quality_audited
attrs_h_future_task_design_confound_identified
two_repo_conclusion_sensitivity_quantified
statement_quality_gate_added
statement_preview_generated_without_paid_rerun
current_paid_result_preserved_as_original_observation
future_validation_requires_new_preregistration
insufficient_clean_evidence_for_predictive_validity
```

Disallowed claims:

```text
predictive_validity_established
production_benchmark_ranking
attrs_h_future_paid_result_repaired
attrs_policy_violation_repaired
rerun_equivalent_score_from_statement_preview
hidden_oracle_informed_statement_rewrite
task_generator_yield_as_main_contribution
```

Interpretation rules:

- The original two-repo paid result remains the original observation.
- Statement-quality sidecars may weaken or qualify that observation, but must
  not overwrite the paid score table.
- A regenerated statement preview is not a new scoreable result.
- If every `attrs` H_future task has material statement-quality risk, say so
  plainly and do not pretend the holdout is clean.
- Do not broaden editable paths based on ACUT behavior. Scope is justified by
  target commit and public task evidence, not by where a failed agent edited.

## Commit Discipline

Every step that changes files must be committed before moving on. Use one or
more commits per step when the step naturally contains separate units.

Suggested commit messages:

```text
Record attrs H_future statement audit preflight
Add attrs H_future statement quality audit
Quantify attrs H_future statement-risk sensitivity
Harden clean supply statement quality checks
Generate attrs H_future statement preview sidecars
Decide attrs H_future evidence status
Record attrs statement-quality audit closeout
```

Before every commit:

```bash
git diff --check
git status --short
```

Use non-interactive git commands:

```bash
git add <paths>
git commit -m "<message>"
```

Do not commit ignored raw paths, workspaces, external repos, caches, or secrets.

## Budget And Runtime Rules

This runbook is local-only by default.

```text
paid ACUT calls: disabled
paid LLM calls: disabled
provider cost change: USD 0
```

Allowed external lookup:

```text
Non-paid GitHub metadata lookup is allowed only for public issue/PR pages that
are already referenced by sanitized task metadata. Commit only short sanitized
excerpts, source refs, lengths, and digests. Do not commit raw API responses or
full issue/PR bodies.
```

Stop before any paid work and write a blocker if:

- the next step requires a paid ACUT rerun;
- the next step requires a paid LLM call;
- the worker cannot separate hidden verifier material from public context;
- the worker would need to modify ACUT internals;
- the worker would need to change historical score tables instead of adding
  sidecar artifacts.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_attrs_h_future_statement_quality_audit.yaml
  tools/
    phase1_attrs_statement_quality_audit.py
  tests/
    test_phase1_attrs_statement_quality_audit.py
  results/
    phase1_attrs_h_future_statement_audit_preflight.json
    phase1_attrs_h_future_task_design_audit.json
    phase1_attrs_h_future_statement_sensitivity.json
    phase1_attrs_h_future_statement_preview.json
    phase1_attrs_h_future_evidence_status.json
  reports/
    phase1_attrs_h_future_statement_audit_process.md
    phase1_attrs_h_future_task_design_audit.md
    phase1_attrs_h_future_statement_sensitivity.md
    phase1_attrs_h_future_statement_preview.md
    phase1_attrs_h_future_evidence_status.md
```

Optional future-runbook draft if the evidence status requires it:

```text
docs/experiments/phase-1-statement-hardened-holdout-preregistration-runbook.md
```

Do not write generated previews into existing solver workspaces. Do not update
original paid result prefixes.

## Step 0: Preflight And Evidence Lock

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, and git status.
2. Record existing untracked paths without touching unrelated files.
3. Read and cite the local proposal file:

```text
barcarolle-research-0519.md
```

4. Read the current Phase 1 evidence:

```text
experiments/phase1_compiler/results/phase1_two_repo_task_outcome_matrix.json
experiments/phase1_compiler/results/phase1_attrs_h_future_failure_taxonomy.json
experiments/phase1_compiler/results/phase1_two_repo_negative_or_underpowered_pilot.json
experiments/phase1_compiler/results/phase1_next_research_decision.json
```

5. Write:

```text
experiments/phase1_compiler/configs/phase1_attrs_h_future_statement_quality_audit.yaml
experiments/phase1_compiler/results/phase1_attrs_h_future_statement_audit_preflight.json
experiments/phase1_compiler/reports/phase1_attrs_h_future_statement_audit_process.md
```

Acceptance:

- The preflight says no paid calls were made.
- The process report says the current paid score tables are immutable inputs.
- The report names the four task IDs under audit:

```text
attrs__hist__012
attrs__hist__013
attrs__hist__023
attrs__hist__027
```

Commit:

```text
Record attrs H_future statement audit preflight
```

## Step 1: Build Durable Task-Design Audit Tool

Actions:

1. Add a local-only tool:

```text
experiments/phase1_compiler/tools/phase1_attrs_statement_quality_audit.py
```

2. The tool must load only sanitized and committed artifacts:

```text
experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl
experiments/phase0_headroom/candidate_sources/attrs_clean_outcome_unseen_supply_source_context.jsonl
experiments/phase1_compiler/results/phase1_two_repo_task_outcome_matrix.json
```

3. If public GitHub metadata is available, the tool may add short sanitized
   excerpt metadata for the already referenced public refs:

```text
issue:680
pr:687
issue:593
issue:766
```

4. The tool must not commit raw API responses or full bodies. Store only:

```text
source_ref
source_kind
title
body_digest
body_length
short_public_excerpt
lookup_status
```

5. For each audited task, compute at least:

```text
task_id
source_ref
source_kind
adapter_outcomes
scoreable_pass_count
scoreable_fail_count
policy_violation_count
changed_file_count
implementation_file_count
test_file_count
module_or_package
certification_gate_summary
solver_statement_excerpt
body_summary_length
body_summary_hit_old_cap
statement_probably_truncated
statement_ends_mid_code_fence
statement_ends_mid_sentence
statement_underspecified_risk
pr_context_risk
scope_metadata_matches_target_non_test_files
manual_audit_label
manual_audit_rationale
```

6. Add tests for the detection logic. The tests must cover:

- a 240-character body summary that ends mid-code or mid-sentence;
- a short complete issue body summary that should not be flagged;
- a PR-context task that gets a `pr_context_risk`;
- a task with a policy violation that is still not treated as a scoreable fail.

Acceptance:

- `uv run pytest experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py`
  passes.
- The tool emits deterministic JSON and Markdown.
- No raw public body, prompt, transcript, workspace, or verifier material is
  committed.

Commit:

```text
Add attrs H_future statement quality audit
```

## Step 2: Generate Manual-Audit Sidecar

Actions:

1. Run the audit tool.
2. Write:

```text
experiments/phase1_compiler/results/phase1_attrs_h_future_task_design_audit.json
experiments/phase1_compiler/reports/phase1_attrs_h_future_task_design_audit.md
```

3. Use these initial labels unless the evidence contradicts them:

```text
attrs__hist__012:
  label: valid_but_statement_quality_risk

attrs__hist__013:
  label: questionable_pr_context_and_statement_quality_risk

attrs__hist__023:
  label: mostly_valid_but_statement_quality_risk

attrs__hist__027:
  label: valid_scope_but_under_specified_statement_risk
```

4. Keep the report simple. It should answer:

- Is the verifier/oracle machinery obviously broken?
- Is the task scope obviously wrong?
- Is the solver-facing statement likely incomplete?
- Could that incompleteness plausibly explain failure?

Acceptance:

- The report distinguishes mechanism validity from statement quality.
- The report does not use hidden verifier material.
- The report does not overwrite previous failure-taxonomy artifacts.
- The report states whether each task is safe to use as clean predictive
  evidence, questionable, or should be excluded in a sensitivity view.

Commit:

```text
Generate attrs H_future task design audit
```

## Step 3: Quantify Sensitivity To Statement Risk

Actions:

1. Add sensitivity computation to the audit tool or a small companion function.
2. Compute at least these views:

```text
original_attrs_h_future:
  include all scoreable attrs H_future cells

exclude_policy_violation_only:
  same scoreable denominator as current metric, policy cell remains non-scoreable

exclude_highest_risk_task_013:
  remove both adapter cells for attrs__hist__013

exclude_highest_risk_tasks_013_027:
  remove attrs__hist__013 and attrs__hist__027

strict_clean_statement_only:
  include only tasks without material statement-quality risk

all_statement_risk_excluded:
  diagnostic view showing whether any attrs H_future clean evidence remains
```

3. For each view, report:

```text
included_tasks
excluded_tasks
scoreable_cells
verified_pass
verified_fail
policy_violations
pass_rate
comparison_to_attrs_b_eval
interpretation
```

4. Write:

```text
experiments/phase1_compiler/results/phase1_attrs_h_future_statement_sensitivity.json
experiments/phase1_compiler/reports/phase1_attrs_h_future_statement_sensitivity.md
```

Acceptance:

- The original metric remains `1/7` scoreable pass.
- Excluding questionable tasks must be presented as sensitivity analysis, not
  as a corrected score.
- If the strict clean statement view has too little evidence, say
  `insufficient_clean_attrs_h_future_evidence`.

Commit:

```text
Quantify attrs H_future statement-risk sensitivity
```

## Step 4: Harden Future Statement Quality Checks

Actions:

1. Locate the statement/context generation paths that produced the truncation
   risk. At runbook creation time, the likely paths were:

```text
experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py
experiments/phase0_headroom/tools/repo_history_pilot.py
experiments/phase0_headroom/tools/workspace_acut_run.py
```

2. Add a reusable statement-quality helper rather than one-off string checks.
   The helper should detect:

```text
truncation at the old 240-character cap
unclosed fenced code block
trailing incomplete sentence
empty or nearly empty body summary
PR-context source with no linked issue
statement missing the public problem summary
statement missing editable implementation scope
```

3. Add tests in the most local existing test module or in the new audit test
   module. Tests must show that future clean-supply candidates with severe
   statement truncation cannot silently pass as clean without a risk flag.

4. Do not retroactively mutate committed paid packages or score tables. The
   hardening is for future mining, statement previews, and preregistration.

Acceptance:

- The new helper is covered by tests.
- Existing relevant tests still pass:

```bash
uv run pytest \
  experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py \
  experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py \
  experiments/phase0_headroom/tools/test_workspace_acut_run.py
```

- The change does not expose target diffs or hidden verifier content in solver
  statements.

Commit:

```text
Harden clean supply statement quality checks
```

## Step 5: Generate Statement Preview Sidecars

Actions:

1. Generate sidecar statement previews for the four `attrs` H_future tasks.
   These previews are diagnostic only and must not be used as scoreable paid
   results.
2. The preview should use fuller sanitized public context when available, but
   must remain small and non-raw:

```text
source ref
problem summary
short public excerpt
editable implementation scope
known non-editable test paths
verifier command metadata
statement quality flags
```

3. Write:

```text
experiments/phase1_compiler/results/phase1_attrs_h_future_statement_preview.json
experiments/phase1_compiler/reports/phase1_attrs_h_future_statement_preview.md
```

4. The report must explicitly say:

```text
These previews do not change previous paid outcomes and are not a rerun.
Any future paid validation using improved statements requires a new frozen
release or preregistration.
```

Acceptance:

- No solver workspace is modified.
- No paid result prefix is modified.
- Preview statements are visibly not cut mid-code or mid-sentence.
- Preview statements list only implementation files as editable paths.

Commit:

```text
Generate attrs H_future statement preview sidecars
```

## Step 6: Decide Evidence Status And Next Branch

Actions:

1. Write a final decision artifact:

```text
experiments/phase1_compiler/results/phase1_attrs_h_future_evidence_status.json
experiments/phase1_compiler/reports/phase1_attrs_h_future_evidence_status.md
```

2. Choose exactly one primary status:

```text
clean_negative_holdout_signal:
  Use only if the audit finds statement quality was not materially risky.

negative_but_statement_quality_confounded:
  Use if the attrs H_future result remains directionally bad but task
  statements materially weaken causal interpretation.

not_clean_enough_for_predictive_validity_claim:
  Use if most or all attrs H_future evidence is statement-quality-risky enough
  that the clean holdout signal is not reliable.
```

3. Choose exactly one next branch:

```text
report_pilot_with_statement_quality_caveat:
  Use if local evidence is enough to close Phase 1 as negative/underpowered
  with an explicit statement-quality caveat.

prepare_statement_hardened_preregistration:
  Use if improved statement rendering is ready and a future paid rerun should
  be considered only under a new preregistered release.

mine_replacement_clean_holdout_supply:
  Use if attrs H_future is too confounded and should be replaced locally before
  any more paid validation.

build_weighted_stratified_compiler_analysis:
  Use if statement quality is only one confound and task strata/time-window
  mismatch still need local analysis before any paid decision.
```

4. If a future runbook is needed, draft it but do not run it.

Acceptance:

- The decision is understandable in simple terms.
- It does not claim predictive validity.
- It does not claim a repaired paid result.
- It says whether the current `attrs` H_future collapse should be treated as:

```text
clean evidence
directional but confounded evidence
or not clean enough for the proposal's predictive-validity claim
```

Commit:

```text
Decide attrs H_future evidence status
```

## Step 7: Closeout

Actions:

1. Update the process report with:

```text
steps completed
commits created
tests run
paid calls made: false
raw artifacts committed: false
current evidence status
recommended next runbook or stop condition
```

2. Run:

```bash
git diff --check
git status --short
```

3. If there are changed files from this runbook, commit the closeout update.

Acceptance:

- Worktree status contains only intentional changes or pre-existing unrelated
  untracked files.
- The final message to the user is in simple Chinese.
- The final message includes the commit list and the evidence status.

Commit:

```text
Record attrs statement-quality audit closeout
```

## Final Response Template

Use simple Chinese:

```text
这轮 runbook 完成后，我会把结论分成三句话：

1. attrs H_future 原始结果是什么。
2. 人工/工具审计后，这个结果是否被题面质量混杂。
3. 下一步应该报告、重做 preregistration、还是先补本地 clean supply。

不要把 improved statement preview 说成 repaired score。
不要说 predictive validity 已经建立。
```
