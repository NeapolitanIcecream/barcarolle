# Phase 1 Attrs Source Repair Runbook

Status: implementation runbook, 2026-05-28.

This runbook is for one dedicated Codex CLI session. Its job is narrow:

```text
Turn the remaining technical-certified attrs tasks into release-eligible tasks
by repairing solver-visible source context and statement provenance.
```

Plain-language summary:

```text
attrs is not blocked by local test certification anymore. It has 31 tasks that
passed the technical gates, but only 28 are release eligible.

The missing 3 tasks already pass the base/reference test checks. They are held
back because their solver-facing source context is only a commit subject. This
runbook tries to repair that weak source context without turning Barcarolle
into a general task generator.

First, look for non-leaky public PR, issue, changelog, or commit-body context.
Only if that is not enough, build a tightly controlled diff-assisted statement
repair path. Any generated or rewritten statement must pass a separate
leakage and ambiguity review before it can count.
```

This is a local supply-repair runbook. Do not run paid ACUT solver cells, paid
task-solving calls, paid replication, or benchmark scoring. Any paid LLM
statement-generation or review call must use only `LLM_BASE_URL` and
`LLM_API_KEY` as required by `AGENTS.md`. If endpoint-compliant generation or
review cannot be proven, stop before those calls and write a blocker report.

## Starting Point

The fresh certification run ended with:

```text
attrs technical certified: 31
attrs release eligible:    28
attrs source review queue:  3

boltons technical certified: 47
boltons release eligible:    35

paid ready: false
blocking reason: at least 3 repos with 30 release-eligible tasks
```

The 3 attrs tasks in the source-review queue are:

```text
attrs__v2__218
attrs__v2__231
attrs__v2__237
```

All three have:

```text
technical_certified: true
release_eligible: false
source_context_quality: commit_message_only_context
suggested_review_mode: manual_review
```

They are not failed tasks. They are tasks with a weak solver-facing statement
source.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-attrs-source-repair-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md first. Use uv for
repo-local Python tooling. Follow AGENTS.md step-level acceptance and commit
requirements: after each step, or after each small group of tightly related
steps, commit the changed files with an appropriately scoped commit.

Main goal: repair the source context and solver-visible statements for the
three attrs technical-certified but not release-eligible tasks:

  attrs__v2__218
  attrs__v2__231
  attrs__v2__237

Do not change their technical certification result unless the committed
metadata is inconsistent. Do not weaken release eligibility by silently
accepting commit-message-only statements. A task may become release eligible
only if it has either non-leaky public context or a reviewed diff-assisted
statement with recorded provenance and review evidence.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. Whether attrs now reaches 30 release-eligible tasks.

Do not run paid ACUT solver cells, paid task-solving calls, paid replication,
or benchmark scoring. Any paid LLM statement generation or review must use only
LLM_BASE_URL and LLM_API_KEY. If either variable is missing, source ~/.zshrc
and check again. If endpoint-compliant calls still cannot be proven, stop
before generation/review and write a blocker. Do not fall back to local Codex
subscription auth, OPENAI_API_KEY, OpenRouter variables, or provider-specific
variables.

Do not commit secrets, raw prompts, raw completions, raw transcripts, raw
GitHub API responses, raw target diffs, solver workspaces, verifier workspaces,
cloned external repositories, .venv, caches, raw stdout/stderr logs, or large
raw outputs. Commit only small sanitized configs, packets, review records,
digests, summaries, reports, and tests.
```

## Inputs

Read these files before making changes:

```text
AGENTS.md
docs/experiments/phase-1-task-supply-v2-fresh-certification-runbook.md
docs/experiments/phase-1-task-supply-v2-generator-bakeoff-runbook.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_decision.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_paid_readiness_gate.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_source_context_inventory.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_raw_anchor_inventory.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_future_directions.md
```

Use these machine-readable inputs:

```text
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_source_review_queue.json
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_attempts.json
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_paid_readiness_gate.json
experiments/phase1_compiler/results/phase1_task_supply_v2_raw_anchor_inventory.json
experiments/phase1_compiler/results/phase1_task_supply_v2_source_context_inventory.json
experiments/phase1_compiler/results/phase1_task_supply_v2_oracle_extraction_matrix.json
```

Useful implementation references:

```text
experiments/phase1_compiler/tools/phase1_task_supply_v2_fresh_certification.py
experiments/phase1_compiler/tools/phase1_task_supply_v2_generator_bakeoff.py
experiments/phase1_compiler/tools/phase1_diff_assisted_codex_loop_statement_regeneration.py
experiments/phase1_compiler/tools/statement_quality.py
experiments/phase1_compiler/tests/test_phase1_task_supply_v2_fresh_certification.py
```

## Outputs

Create a new local-only run under this prefix:

```text
phase1_attrs_source_repair
```

Expected committed outputs:

```text
experiments/phase1_compiler/configs/phase1_attrs_source_repair.yaml
experiments/phase1_compiler/tools/phase1_attrs_source_repair.py
experiments/phase1_compiler/tests/test_phase1_attrs_source_repair.py
experiments/phase1_compiler/results/phase1_attrs_source_repair_preflight.json
experiments/phase1_compiler/results/phase1_attrs_source_repair_candidate_packets.json
experiments/phase1_compiler/results/phase1_attrs_source_repair_public_context_review.json
experiments/phase1_compiler/results/phase1_attrs_source_repair_statement_packets.json
experiments/phase1_compiler/results/phase1_attrs_source_repair_review_records.json
experiments/phase1_compiler/results/phase1_attrs_source_repair_release_eligibility_overlay.json
experiments/phase1_compiler/results/phase1_attrs_source_repair_paid_readiness_gate.json
experiments/phase1_compiler/results/phase1_attrs_source_repair_decision.json
experiments/phase1_compiler/reports/phase1_attrs_source_repair_process.md
experiments/phase1_compiler/reports/phase1_attrs_source_repair_candidate_packets.md
experiments/phase1_compiler/reports/phase1_attrs_source_repair_public_context_review.md
experiments/phase1_compiler/reports/phase1_attrs_source_repair_statement_review.md
experiments/phase1_compiler/reports/phase1_attrs_source_repair_paid_readiness_gate.md
experiments/phase1_compiler/reports/phase1_attrs_source_repair_decision.md
```

Allowed ignored outputs:

```text
experiments/phase1_compiler/tmp/attrs_source_repair/
experiments/phase0_headroom/workspaces/attrs_source_repair/
experiments/phase0_headroom/cache/attrs_source_repair/
```

Committed JSON and Markdown must contain only sanitized metadata, short
summaries, hashes, provenance classes, review verdicts, and task ids.

## Definitions

Use these terms consistently:

```text
technical_certified:
  The task has already passed the local no-op fail, reference pass, and
  reference repeat gates under an accepted environment profile.

release_eligible:
  The task is technical_certified and has a solver-visible statement/source
  context that passed leakage, ambiguity, provenance, and scope checks.

public_context_repaired:
  The task moved from commit-message-only context to a non-leaky public issue,
  PR, changelog, release note, or commit-body context that is sufficient for a
  solver-visible statement.

reviewed_diff_assisted_statement:
  The task still lacks enough public natural-language context, but a
  solver-visible statement was generated or rewritten from a sanitized packet
  and then passed independent review.

statement_ready:
  The task has an accepted statement from either public_context_repaired or
  reviewed_diff_assisted_statement.
```

## Claim Boundary

Allowed claims:

```text
attrs_source_repair_completed
attrs_public_context_repaired
attrs_reviewed_diff_assisted_statement_passed
attrs_release_eligible_count_recomputed
attrs_reached_30_release_eligible
attrs_still_below_30_release_eligible
third_repo_still_needed
paid_validation_not_run
```

Disallowed claims:

```text
predictive_validity_established
production_benchmark_ranking
paid_acut_validation_completed
solver_performance_improved
task_generator_is_barcarolle_core_contribution
commit_message_only_context_is_release_eligible_without_review
generated_statement_is_release_eligible_without_review
hidden_oracle_informed_statement
third_repo_gate_satisfied_unless_three_repos_reach_30_release_eligible
```

## Step 0 - Preflight And Dirty-Tree Audit

Goal: prove the run starts from a known local state.

Actions:

1. Run `git status --short --untracked-files=all`.
2. Record branch and starting commit.
3. Confirm the three attrs source-review tasks exist in the source-review
   queue.
4. Confirm each task is technical certified and release ineligible only because
   of source context quality.
5. Confirm no paid ACUT or paid task-solving call is needed.
6. If LLM generation/review may be needed later, check whether
   `LLM_BASE_URL` and `LLM_API_KEY` are present. If missing, source
   `~/.zshrc` and check again. Record only presence/absence, never values.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_attrs_source_repair_preflight.json
experiments/phase1_compiler/reports/phase1_attrs_source_repair_process.md
```

Acceptance:

- The report lists the exact three attrs candidate ids.
- The report states each task's current technical and release status.
- The report classifies dirty/untracked files as relevant, ignored artifact
  output, or unrelated.
- The report says no paid ACUT or solver calls were made.

Commit guidance:

- Commit preflight artifacts as one preflight commit.
- Do not stage unrelated untracked external-review bundle files.

## Step 1 - Build Sanitized Candidate Packets

Goal: create auditable packets for the three attrs tasks.

Actions:

1. Read raw anchor, source context, oracle, and fresh certification artifacts.
2. For each task, write a sanitized candidate packet with:
   - candidate id;
   - repo id;
   - base commit;
   - target commit;
   - task time;
   - implementation file paths;
   - test file paths;
   - existing public context refs;
   - technical certification profile;
   - source context class;
   - short digests of changed tests and implementation diff, not raw diffs;
   - reason it is not release eligible today.
3. Do not include raw target diffs, raw test patches, raw prompts, or raw
   completions.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_attrs_source_repair_candidate_packets.json
experiments/phase1_compiler/reports/phase1_attrs_source_repair_candidate_packets.md
```

Acceptance:

- Exactly three packets are present.
- Packets contain enough provenance to audit the repair path.
- Packets do not include raw patch bodies or hidden oracle material.

Commit guidance:

- Commit the packet builder, config, tests, and packet/report outputs together
  if they are tightly related.

## Step 2 - Public Context Search And Review

Goal: repair source context from public, non-leaky material before using any
statement generator.

Actions:

1. For each target commit, inspect local git metadata first:
   - commit subject;
   - commit body;
   - associated tags or nearby release notes if already present locally.
2. If network access is used, query only public upstream repository pages or
   APIs for PR, issue, release note, and changelog context linked to the target
   commit.
3. Save only sanitized context metadata:
   - public URL or ref id;
   - context type;
   - short summary;
   - leakage flags;
   - ambiguity flags;
   - whether it is sufficient to write a solver-visible statement.
4. Do not commit raw GitHub API responses or full issue/PR bodies.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_attrs_source_repair_public_context_review.json
experiments/phase1_compiler/reports/phase1_attrs_source_repair_public_context_review.md
```

Acceptance:

- Every task receives a public-context verdict:
  `accepted_public_context`, `insufficient_public_context`, or
  `rejected_leaky_public_context`.
- If at least two tasks receive accepted public context, attrs should be able
  to reach 30 release eligible after Step 5.
- If fewer than two tasks receive accepted public context, continue to Step 3.

Commit guidance:

- Commit public-context review artifacts separately from later generated
  statement artifacts.

## Step 3 - Endpoint-Compliant Diff-Assisted Statement Repair

Goal: repair only the tasks that still lack sufficient public context.

This step is conditional. Run it only if Step 2 leaves fewer than two newly
release-eligible attrs tasks.

Actions:

1. Confirm `LLM_BASE_URL` and `LLM_API_KEY` are present in the worker shell.
   If either is missing, source `~/.zshrc` and check again.
2. If endpoint compliance cannot be proven, do not call a model. Write a
   blocker record and skip to Step 6.
3. Build a sanitized statement packet for each remaining task. Allowed inputs:
   - candidate id;
   - repo name;
   - public context summary when available;
   - commit subject/body summary;
   - implementation file paths;
   - test file paths;
   - behavior-level summary of changed tests;
   - behavior-level summary of touched APIs;
   - short diff/test digests.
4. Disallowed inputs:
   - raw target patch;
   - raw hidden test patch;
   - exact added assertions copied into the statement;
   - target commit hash in the solver statement;
   - direct implementation recipe;
   - raw prompt/completion transcripts in committed files.
5. Use an endpoint-compliant wrapper or script that records:
   - endpoint variables were present;
   - model/config id without secrets;
   - prompt template digest;
   - completion digest;
   - generated statement id;
   - raw prompt/completion storage path under ignored tmp, if retained.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_attrs_source_repair_statement_packets.json
experiments/phase1_compiler/reports/phase1_attrs_source_repair_statement_review.md
```

Acceptance:

- No model call occurs unless endpoint compliance is proven.
- Every generated statement has provenance and digests.
- Raw prompts and raw completions are not committed.

Commit guidance:

- If this step runs, commit endpoint wrapper/config/tests and sanitized
  statement-packet artifacts as one scoped commit.
- If this step blocks before model calls, commit the blocker report.

## Step 4 - Independent Leakage And Ambiguity Review

Goal: do not count generated or repaired statements until they pass review.

Actions:

1. Review every accepted public-context statement and every diff-assisted
   statement.
2. The review must classify:
   - leakage status;
   - ambiguity status;
   - scope clarity;
   - whether the statement contains implementation instructions;
   - whether it exposes target commit, patch, raw tests, or hidden oracle text;
   - final release-eligibility recommendation.
3. Prefer an independent endpoint-compliant reviewer for diff-assisted
   statements. If no endpoint-compliant reviewer is available, use deterministic
   checks plus manual blocker status, but do not promote the generated
   statement to release eligible.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_attrs_source_repair_review_records.json
experiments/phase1_compiler/reports/phase1_attrs_source_repair_statement_review.md
```

Acceptance:

- Every promoted task has a review record.
- A generated statement without independent endpoint-compliant review is not
  counted as release eligible.
- Review records explain rejected tasks in simple language.

Commit guidance:

- Commit review records and report updates separately from raw generation
  artifacts.

## Step 5 - Release Eligibility Overlay And Gate Recompute

Goal: recompute attrs release eligibility without rewriting historical fresh
certification outputs.

Actions:

1. Create an overlay that marks only the repaired attrs tasks as newly
   statement-ready.
2. Preserve the original fresh certification outputs as historical evidence.
3. Recompute:
   - attrs technical certified count;
   - attrs release eligible count before overlay;
   - attrs release eligible count after overlay;
   - boltons release eligible count;
   - repos meeting 30 release-eligible tasks;
   - whether three repos now meet the paid gate.
4. Do not count humanize/toolz repairs unless this runbook explicitly repaired
   them, which it should not.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_attrs_source_repair_release_eligibility_overlay.json
experiments/phase1_compiler/results/phase1_attrs_source_repair_paid_readiness_gate.json
experiments/phase1_compiler/reports/phase1_attrs_source_repair_paid_readiness_gate.md
```

Acceptance:

- The overlay is additive and traceable.
- If at least two attrs tasks are promoted, attrs should reach at least 30
  release eligible.
- Paid readiness remains false unless at least three repos have 30
  release-eligible tasks.

Commit guidance:

- Commit overlay and gate artifacts as one scoped commit.

## Step 6 - Decision And Closeout

Goal: give the coordinating session a clear next decision.

Actions:

1. Write the final decision report.
2. Answer these research questions:

```text
RQ1: How many attrs source-review tasks were repaired through public context?
RQ2: How many were repaired through reviewed diff-assisted statements?
RQ3: Did attrs reach 30 release-eligible tasks?
RQ4: Did any repaired statement fail leakage or ambiguity review?
RQ5: Were any paid LLM calls made, and if so did they use only
     LLM_BASE_URL and LLM_API_KEY?
RQ6: Are at least three repos now at 30 release-eligible tasks?
RQ7: What is the next blocker: third repo supply, endpoint statement review,
     environment repair, or paid validation readiness?
```

3. Record completed steps, commits made during the run, tests run, and known
   blockers.
4. Do not draft the next runbook unless the user explicitly asks in the worker
   task.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_attrs_source_repair_decision.json
experiments/phase1_compiler/reports/phase1_attrs_source_repair_decision.md
```

Acceptance:

- The decision says one of:

```text
attrs_reached_30_third_repo_still_needed
attrs_still_below_30_source_repair_blocked
attrs_source_repair_completed_paid_gate_still_not_ready
blocked_endpoint_compliant_statement_review_missing
```

- The report uses simple language and does not overclaim predictive validity.

Commit guidance:

- Commit closeout artifacts as the final runbook execution commit.

## Verification

At minimum, run:

```bash
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_attrs_source_repair.py -q
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q
git diff --check
git status --short --untracked-files=all
```

If the full test suite is too slow or blocked, run the focused tests plus the
nearest related tests and record the reason.

## Final Reporting Template

The final worker summary should be short and in simple Chinese:

```text
这次 runbook 修的是 attrs 的题面来源，不是重新验证测试。

结果：
- attrs 原来 release eligible 是 28。
- 本次新增通过 review 的任务是 N 个。
- attrs 现在 release eligible 是 M。
- paid gate 是否通过：是/否。

如果 paid gate 还没通过，原因是：
- 第三个仓库仍然没有 30 个 release-eligible tasks，或
- attrs 仍然没有到 30，或
- endpoint-compliant statement review 被阻塞。

没有运行 paid ACUT solver cells。LLM 调用情况：无/有，且 endpoint 合规情况如下。
```

